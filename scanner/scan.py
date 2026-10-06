"""Live scan entry point. Run every 15 minutes by GitHub Actions.

  python -m scanner.scan            # full scan (Stage A daily + Stage B intraday + exits)
  python -m scanner.scan --stage a  # breakouts only (cheaper; fine hourly)
  python -m scanner.scan --stage b  # pullbacks + exits only
"""
from __future__ import annotations
import argparse
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
from .config import CFG
from . import data
from .strategy import detect_breakout, detect_pullback, breakout_entry, entries_enabled, update_impulse_high, Breakout
from .db import Store
from . import alerts as notify


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


def _insert_alert(store: Store, setup, in_play_id, exchange: str | None = None) -> bool:
    """Store a new alert. At account.max_concurrent_trades open (taken) alerts it is stored
    with taken=False: graded like any alert, but not traded. Returns True if taken."""
    limit = CFG["account"].get("max_concurrent_trades")
    taken = limit is None or len(store.open_alerts()) < limit
    row = setup.to_row(); row.pop("pullback_low")
    row.update({"in_play_id": in_play_id, "outcome": "open", "taken": taken,
                "fired_at": datetime.now(timezone.utc)})
    store.insert("alerts", _with_exchange(row, exchange))
    return taken


# ------------------------------------------------------------------ Stage A
def stage_a(store: Store) -> int:
    found = 0
    already = {(r["symbol"], str(r["breakout_date"])[:10]) for r in store.select("in_play")}
    watching = {r["symbol"] for r in store.watching()}
    ex = data._exchange() if CFG["universe"]["crypto"]["enabled"] else None
    for sym, cls, src in universe():
        if sym in watching:   # same as the backtester: no new Stage A while already in play
            continue
        try:
            daily = data.ohlcv(sym, cls, CFG["timeframes"]["daily"], limit=120, ex=data.exchange_for(src, ex))
            bo = detect_breakout(daily, sym, cls)
            if bo and (sym, bo.breakout_date.strftime("%Y-%m-%d")) not in already:
                # The in_play row is created even when the breakout entry fires, so the
                # pullback entry can still trigger later. The two are graded separately.
                ip = store.upsert("in_play", _with_exchange({
                    "symbol": sym, "asset_class": cls,
                    "breakout_date": bo.breakout_date.strftime("%Y-%m-%d"),
                    "breakout_level": bo.breakout_level, "impulse_low": bo.impulse_low,
                    "impulse_high": bo.impulse_high, "impulse_volume": bo.impulse_volume,
                    "status": "watching",
                }, src), on_conflict="symbol,breakout_date")
                msg = notify.format_breakout(bo, src)
                setup = breakout_entry(bo, float(daily["close"].iloc[-1])) if "breakout" in entries_enabled() else None
                if setup:
                    taken = _insert_alert(store, setup, ip.get("id"), src)
                    msg += "\n\n" + (notify.format_setup(setup) if taken else notify.format_skipped(setup))
                notify.send(msg)
                found += 1
        except Exception as e:  # one bad symbol must not kill the run
            print(f"[stage_a] {sym}: {e}")
        time.sleep(0.05)
    return found


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
            # A close below breakout level = failed breakout.
            if float(daily["close"].iloc[-1]) < bo.breakout_level:
                store.update("in_play", r["id"], {"status": "failed", "updated_at": datetime.now(timezone.utc)})
                continue
            store.update("in_play", r["id"], {"impulse_high": bo.impulse_high, "updated_at": datetime.now(timezone.utc)})
            if "pullback" not in entries_enabled():
                continue   # row stays "watching" until expiry, so Stage A won't re-fire meanwhile
            intraday = data.ohlcv(bo.symbol, bo.asset_class, CFG["timeframes"]["intraday"], limit=300, ex=rex)
            setup = detect_pullback(intraday, bo)
            if setup:
                taken = _insert_alert(store, setup, r["id"], r.get("exchange"))
                store.update("in_play", r["id"], {"status": "triggered"})
                notify.send(notify.format_setup(setup) if taken else notify.format_skipped(setup))
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
    ap.add_argument("--stage", choices=["a", "b", "all"], default="all")
    args = ap.parse_args()
    store = Store()
    t0 = time.time()
    if args.stage in ("a", "all"):
        print(f"stage A: {stage_a(store)} new breakouts")
    if args.stage in ("b", "all"):
        print(f"stage B: {stage_b(store)} setups fired")
        print(f"exits:   {manage_exits(store)} notices")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
