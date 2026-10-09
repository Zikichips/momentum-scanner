"""Live scan entry point. Run every 15 minutes by GitHub Actions.

  python -m scanner.scan            # full scan (Stage A daily + Stage B intraday + exits)
  python -m scanner.scan --stage a  # breakouts only: daily, plus intraday on the last 1h bar (run hourly)
  python -m scanner.scan --stage b  # pullbacks + exits only
  python -m scanner.scan --stage l  # exchange-listing watcher only (scanner/listings.py)
  python -m scanner.scan --stage a,l  # any comma-separated mix
"""
from __future__ import annotations
import argparse
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
from .config import CFG
from . import data
from .strategy import (detect_breakout, detect_intraday_breakout, detect_pullback, breakout_entry, entries_enabled,
                       update_impulse_high, late_breakout, Breakout)
from .db import Store
from . import alerts as notify


def _now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


def _bo_from_row(r: dict) -> Breakout:
    return Breakout(
        symbol=r["symbol"], asset_class=r["asset_class"],
        breakout_date=pd.Timestamp(r["breakout_date"]).tz_localize("UTC") if pd.Timestamp(r["breakout_date"]).tzinfo is None else pd.Timestamp(r["breakout_date"]),
        breakout_level=r["breakout_level"], impulse_low=r["impulse_low"],
        impulse_high=r["impulse_high"], impulse_volume=r["impulse_volume"],
        impulse_pct=(r["impulse_high"] / r["impulse_low"] - 1) * 100 if r.get("impulse_low") else 0.0,
    )


def universe() -> list[tuple[str, str, str | None]]:
    """(symbol, asset_class, exchange): exchange None = the configured exchange."""
    out = []
    u = CFG["universe"]["crypto"]
    if u["enabled"]:
        rows = data.crypto_universe_with_volume()
        print(f"universe: {len(rows)} crypto pairs (24h quote volume)")
        for i, (s, qv) in enumerate(rows, 1):
            print(f"  {i:>3}. {s:<12} ${qv:>15,.0f}")
        out += [(s, "crypto", None) for s, _ in rows]
        if u.get("coinbase_movers", {}).get("enabled"):
            try:
                movers = data.coinbase_movers(skip={s for s, _ in rows})
            except Exception as e:   # the Kraken universe still gets scanned
                print(f"[universe] coinbase movers: {e}"); movers = []
            print(f"universe: +{len(movers)} Coinbase movers")
            for s, qv, gain in movers:
                print(f"    + {s:<12} ${qv:>15,.0f}  +{gain:.0f}%")
            out += [(s, "crypto", "coinbase") for s, _, _ in movers]
    if CFG["universe"]["stocks"]["enabled"]:
        out += [(s, "stock", None) for s in data.stock_universe()]
    return out


def _with_exchange(row: dict, exchange: str | None) -> dict:
    """Record a non-default price source on the row; default rows are left as they were."""
    return {**row, "exchange": exchange} if exchange else row


def _is_shadow(exchange: str | None, source: str | None) -> bool:
    """A Coinbase mover (Stage A coin from outside the Kraken top-N, daily or intraday breakout,
    not a listing) while universe.crypto.coinbase_movers.shadow is on."""
    return (exchange == "coinbase" and source != "listing"
            and bool(CFG["universe"]["crypto"].get("coinbase_movers", {}).get("shadow")))


def _alert_message(setup, taken: bool, exchange: str | None, source: str | None) -> str:
    if taken:
        return notify.format_setup(setup)
    return notify.format_shadow(setup) if _is_shadow(exchange, source) else notify.format_skipped(setup)


def _insert_alert(store: Store, setup, in_play_id, exchange: str | None = None, source: str | None = None) -> bool:
    """Store a new alert. At account.max_concurrent_trades open (taken) alerts it is stored
    with taken=False: graded like any alert, but not traded. A shadow alert (_is_shadow) is
    always stored with taken=False and "shadow" in its notes. Returns True if taken."""
    limit = CFG["account"].get("max_concurrent_trades")
    shadow = _is_shadow(exchange, source)
    taken = not shadow and (limit is None or len(store.open_alerts()) < limit)
    row = setup.to_row(); row.pop("pullback_low")
    if shadow:
        row["notes"] = f"{row.get('notes') or ''} | shadow (Coinbase mover)".lstrip(" |")
    row.update({"in_play_id": in_play_id, "outcome": "open", "taken": taken,
                "fired_at": datetime.now(timezone.utc)})
    if source:   # e.g. "listing": scored as its own group, not with Stage A pullbacks
        row["source"] = source
    store.insert("alerts", _with_exchange(row, exchange))
    return taken


# ------------------------------------------------------------------ Stage A
def stage_a(store: Store) -> int:
    """Daily breakouts, then (hourly run) intraday breakouts on the coins without one.
    An intraday row (source "intraday") is a precursor: it doesn't stop the daily check, and a
    daily breakout on the same coin takes it over (_take_over_intraday)."""
    found = 0
    rows = store.select("in_play")
    already = {(r["symbol"], str(r["breakout_date"])[:10]) for r in rows if r.get("source") != "intraday"}
    any_day = {(r["symbol"], str(r["breakout_date"])[:10]) for r in rows}
    watching = {r["symbol"]: r for r in store.watching()}
    ex = data._exchange() if CFG["universe"]["crypto"]["enabled"] else None
    for sym, cls, src in universe():
        w = watching.get(sym)
        if w and w.get("source") != "intraday":   # same as the backtester: no new Stage A while already in play
            continue
        try:
            rex = data.exchange_for(src, ex)
            daily = data.ohlcv(sym, cls, CFG["timeframes"]["daily"], limit=120, ex=rex)
            bo = detect_breakout(daily, sym, cls)
            if bo and (sym, bo.breakout_date.strftime("%Y-%m-%d")) not in already:
                day = bo.breakout_date.strftime("%Y-%m-%d")
                close = float(daily["close"].iloc[-1])
                try:
                    price = data.last_price(sym, cls, rex)
                except Exception as e:   # time check still applies
                    print(f"[stage_a] {sym} price: {e}"); price = None
                late = late_breakout(bo, close, price, _now())
                # The in_play row is created even when the breakout entry fires, so the
                # pullback entry can still trigger later. The two are graded separately.
                ip = store.upsert("in_play", _with_exchange({
                    "symbol": sym, "asset_class": cls,
                    "breakout_date": day,
                    "breakout_level": bo.breakout_level, "impulse_low": bo.impulse_low,
                    "impulse_high": bo.impulse_high, "impulse_volume": bo.impulse_volume,
                    "status": _take_over_intraday(store, rows, sym, day), "late": bool(late), "source": None,
                }, src), on_conflict="symbol,breakout_date")
                found += 1
                if late:   # no buy at a price that's gone; Stage B still watches for a pullback
                    notify.send(notify.format_late(bo, late, src))
                    continue
                msg = notify.format_breakout(bo, src)
                setup = breakout_entry(bo, close) if "breakout" in entries_enabled() else None
                if setup:
                    taken = _insert_alert(store, setup, ip.get("id"), src)
                    msg += "\n\n" + _alert_message(setup, taken, src, None)
                notify.send(msg)
            elif not w and CFG.get("intraday_breakout", {}).get("enabled"):
                found += _intraday_breakout(store, sym, cls, src, rex, any_day)
        except Exception as e:  # one bad symbol must not kill the run
            print(f"[stage_a] {sym}: {e}")
        time.sleep(0.05)
    return found


def _take_over_intraday(store: Store, rows: list[dict], sym: str, day: str) -> str:
    """A daily breakout on a coin the intraday check put in play replaces the intraday row:
    the same day's row is overwritten by the upsert (keeping its status, so a pullback that
    already fired doesn't fire again on the same move); an earlier day's watching row is closed.
    Returns the status for the daily row."""
    status = "watching"
    for r in rows:
        if r["symbol"] != sym or r.get("source") != "intraday":
            continue
        if str(r["breakout_date"])[:10] == day:
            status = r["status"]
        elif r["status"] == "watching":
            store.update("in_play", r["id"], {"status": "expired", "updated_at": datetime.now(timezone.utc)})
    return status


def _intraday_breakout(store: Store, sym: str, cls: str, src: str | None, rex, any_day: set) -> int:
    """Intraday Stage A on the last closed 1h bar. No buy alert: the coin goes in play
    (source "intraday") and Stage B watches it for a pullback. Returns 1 if added."""
    hourly = data.ohlcv(sym, cls, CFG["timeframes"]["intraday"], limit=120, ex=rex)
    bo = detect_intraday_breakout(hourly, sym, cls)
    if not bo or (sym, bo.breakout_date.strftime("%Y-%m-%d")) in any_day:
        return 0
    store.upsert("in_play", _with_exchange({
        "symbol": sym, "asset_class": cls,
        "breakout_date": bo.breakout_date.strftime("%Y-%m-%d"),
        "breakout_level": bo.breakout_level, "impulse_low": bo.impulse_low,
        "impulse_high": bo.impulse_high, "impulse_volume": bo.impulse_volume,
        "status": "watching", "late": False, "source": "intraday",
    }, src), on_conflict="symbol,breakout_date")
    notify.send(notify.format_intraday(bo, src))
    return 1


# ------------------------------------------------------------------ Stage B
def stage_b(store: Store) -> int:
    fired = 0
    expiry = timedelta(days=CFG["breakout"]["in_play_expiry_days"])
    ex = data._exchange() if CFG["universe"]["crypto"]["enabled"] else None
    for r in store.watching():
        bo = _bo_from_row(r)
        rex = data.exchange_for(r.get("exchange"), ex)
        try:
            if datetime.now(timezone.utc) - bo.breakout_date > expiry:
                store.update("in_play", r["id"], {"status": "expired", "updated_at": datetime.now(timezone.utc)})
                continue
            daily = data.ohlcv(bo.symbol, bo.asset_class, CFG["timeframes"]["daily"], limit=60, ex=rex)
            bo = update_impulse_high(bo, daily)
            # A close below breakout level = failed breakout. Only daily bars from the breakout
            # day on count: a listing goes in play mid-day, when the last closed bar predates it.
            if daily.index[-1] >= pd.Timestamp(bo.breakout_date) and float(daily["close"].iloc[-1]) < bo.breakout_level:
                store.update("in_play", r["id"], {"status": "failed", "updated_at": datetime.now(timezone.utc)})
                continue
            store.update("in_play", r["id"], {"impulse_high": bo.impulse_high, "updated_at": datetime.now(timezone.utc)})
            if "pullback" not in entries_enabled():
                continue   # row stays "watching" until expiry, so Stage A won't re-fire meanwhile
            intraday = data.ohlcv(bo.symbol, bo.asset_class, CFG["timeframes"]["intraday"], limit=300, ex=rex)
            if r.get("source") in ("listing", "intraday"):   # day 0 has no closed daily bar yet: track the high on hourly bars
                bo = update_impulse_high(bo, intraday)
                store.update("in_play", r["id"], {"impulse_high": bo.impulse_high})
            setup = detect_pullback(intraday, bo)
            if setup:
                taken = _insert_alert(store, setup, r["id"], r.get("exchange"), r.get("source"))
                store.update("in_play", r["id"], {"status": "triggered"})
                notify.send(_alert_message(setup, taken, r.get("exchange"), r.get("source")))
                fired += 1
        except Exception as e:
            print(f"[stage_b] {bo.symbol}: {e}")
        time.sleep(0.05)
    return fired


# ------------------------------------------------------------------ Exits
def manage_exits(store: Store) -> int:
    """Alert when an open setup hits stop / T1 / T2 on a closed bar. Each notice is sent once:
    a marker goes into the alert's notes (the outcome itself is only set by the daily grader)."""
    n = 0
    ex = data._exchange() if CFG["universe"]["crypto"]["enabled"] else None
    for a in store.open_alerts():
        notes = a.get("notes") or ""
        if "STOP notified" in notes or "T2 notified" in notes:   # exit already sent; wait for the grader
            continue
        try:
            df = data.ohlcv(a["symbol"], a["asset_class"], CFG["timeframes"]["intraday"], limit=50,
                            ex=data.exchange_for(a.get("exchange"), ex))
            last = df.iloc[-1]
            hi, lo, close = float(last["high"]), float(last["low"]), float(last["close"])
            if close < a["stop"]:
                notify.send(notify.format_exit(a, "STOP hit — exit", close))
                store.update("alerts", a["id"], {"notes": notes + " | STOP notified"}); n += 1
            elif hi >= a["target2"]:
                notify.send(notify.format_exit(a, "T2 reached — exit remainder", hi))
                store.update("alerts", a["id"], {"notes": notes + " | T2 notified"}); n += 1
            elif hi >= a["target1"] and "T1 notified" not in notes and "T1 hit" not in notes:
                notify.send(notify.format_exit(a, "T1 reached — take half, stop to entry", hi))
                store.update("alerts", a["id"], {"notes": notes + " | T1 notified"}); n += 1
        except Exception as e:
            print(f"[exits] {a['symbol']}: {e}")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", help="all, or a comma-separated mix of a, b, l")
    args = ap.parse_args()
    stages = {"a", "b", "l"} if args.stage == "all" else set(args.stage.split(","))
    if not stages <= {"a", "b", "l"}:
        ap.error(f"unknown stage in {args.stage!r}")
    store = Store()
    t0 = time.time()
    if "l" in stages:   # first: a fresh listing put in play here gets Stage B in the same run
        from . import listings
        print(f"listings: {listings.run(store)} new")
    if "a" in stages:
        print(f"stage A: {stage_a(store)} new breakouts")
    if "b" in stages:
        print(f"stage B: {stage_b(store)} setups fired")
        print(f"exits:   {manage_exits(store)} notices")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
