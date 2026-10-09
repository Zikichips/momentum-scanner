"""Replay Stage A (daily + intraday) and Stage B hour by hour over the last N days, through the
live code path (scan.stage_a / scan.stage_b) on Kraken bars, against a throwaway local store.
Nothing is sent and nothing touches Supabase.

  python -m scanner.replay_intraday                     # last 7 days
  python -m scanner.replay_intraday --days 7 --add STRK/USD

Universe each hour: the Kraken top-N USD pairs by trailing 24h quote volume (sum of close x
volume over the last 24 closed 1h bars), i.e. roughly what crypto_universe() returned then.
Only pairs whose current 24h volume is >= 20% of today's #N are ranked (the rest can't
plausibly have been in the top-N this week). --add scans a symbol every hour even when it's
outside the top-N (shown as "forced"). Coinbase movers are not replayed.

Runs twice, intraday Stage A off (what the live scanner did) and on, and reports what the
intraday check adds. Every alert counts (no slot limit). Pullback alerts are graded on the hourly
bars after them; "open" = unresolved by the last bar. Writes data/intraday_replay.md.
"""
from __future__ import annotations
import os
for _k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    os.environ[_k] = ""   # blank, not unset: load_dotenv never overrides, so .env can't leak in
import argparse
import tempfile
import time
import types
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from .config import CFG, ROOT
from . import data, db, scan
from .outcomes import grade

HOUR = pd.Timedelta(hours=1)


def _fetch(ex, symbols: list[str]) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    out = {}
    for s in symbols:
        try:
            out[s] = (data.crypto_ohlcv(s, "1h", limit=720, ex=ex), data.crypto_ohlcv(s, "1d", limit=200, ex=ex))
        except Exception as e:
            print(f"  {s}: {e}")
        time.sleep(0.05)
    return out


def _top_n(bars: dict, now: pd.Timestamp, n: int) -> list[str]:
    vol = {}
    for s, (h, _) in bars.items():
        w = h[(h.index + HOUR <= now) & (h.index + HOUR > now - pd.Timedelta(hours=24))]
        vol[s] = float((w["close"] * w["volume"]).sum())
    return sorted(vol, key=vol.get, reverse=True)[:n]


class _Clock(datetime):
    now_ts: pd.Timestamp

    @classmethod
    def now(cls, tz=None):
        return cls.now_ts.to_pydatetime()


def replay(bars: dict, hours: list[pd.Timestamp], add: list[str], intraday: bool) -> tuple[list, list, list]:
    """Returns (in_play rows, alerts, Telegram messages with their hour)."""
    CFG["intraday_breakout"]["enabled"] = intraday
    CFG["account"]["max_concurrent_trades"] = None
    db._LOCAL = Path(tempfile.mkstemp(suffix=".json")[1]); db._LOCAL.unlink()
    store = db.Store()
    n = CFG["universe"]["crypto"]["top_n_by_volume"]
    clock = {"now": hours[0]}

    def ohlcv(symbol, asset_class, timeframe, limit=400, ex=None):
        h, d = bars[symbol]
        df, step = (d, pd.Timedelta(days=1)) if timeframe == "1d" else (h, HOUR)
        return df[df.index + step <= clock["now"]].tail(limit)

    def last_price(symbol, asset_class, ex=None):
        h = bars[symbol][0]
        return float(h[h.index + HOUR <= clock["now"]]["close"].iloc[-1])

    sent = []
    saved = (data.ohlcv, data.last_price, data._exchange, data.exchange_for, scan.universe, scan._now,
             scan.datetime, scan.notify.send, scan.time)
    scan.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)   # no API calls to pace
    data.ohlcv, data.last_price, data._exchange = ohlcv, last_price, (lambda: None)
    data.exchange_for = lambda ex_id, default=None: default
    scan.datetime = _Clock
    scan.notify.send = lambda m: sent.append((clock["now"], m))
    try:
        for now in hours:
            clock["now"] = _Clock.now_ts = now
            uni = _top_n(bars, now, n)
            uni += [s for s in add if s in bars and s not in uni]
            scan.universe = lambda uni=uni: [(s, "crypto", None) for s in uni]
            scan._now = lambda now=now: now
            scan.stage_a(store)   # the hourly run: Stage A, then Stage B in the same run
            scan.stage_b(store)
    finally:
        (data.ohlcv, data.last_price, data._exchange, data.exchange_for, scan.universe, scan._now,
         scan.datetime, scan.notify.send, scan.time) = saved
    return store.select("in_play"), store.select("alerts"), sent


def _in_universe(bars: dict, sym: str, at: pd.Timestamp, n: int) -> bool:
    return sym in _top_n(bars, at, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--add", nargs="*", default=[], help="symbols scanned every hour even outside the top-N")
    args = ap.parse_args()

    ex = data._exchange()
    n = CFG["universe"]["crypto"]["top_n_by_volume"]
    rows = data.crypto_universe_with_volume(ex)
    cut = rows[n - 1][1] if len(rows) >= n else 0
    u = CFG["universe"]["crypto"]
    excl = set(u["exclude"])
    cands = sorted({s for s, t in ex.fetch_tickers().items()
                    if s.endswith(f"/{u['quote']}") and s.split("/")[0] not in excl
                    and (t.get("quoteVolume") or 0) >= 0.2 * cut} | set(args.add))
    print(f"fetching 1h + 1d bars for {len(cands)} Kraken pairs...")
    bars = _fetch(ex, cands)

    last = max(h.index[-1] for h, _ in bars.values()) + HOUR       # close of the latest closed 1h bar
    hours = list(pd.date_range(last - pd.Timedelta(days=args.days) + HOUR, last, freq="1h"))
    print(f"replaying {len(hours)} hourly runs, {hours[0]:%d %b %H:%M} -> {hours[-1]:%d %b %H:%M} UTC")

    base_ip, base_al, _ = replay(bars, hours, args.add, intraday=False)
    ip, al, sent = replay(bars, hours, args.add, intraday=True)
    CFG["intraday_breakout"]["enabled"] = True

    def graded(a):
        h = bars[a["symbol"]][0]
        g = grade(a, h[h.index + HOUR <= last])
        return {**a, **g}

    lines = [f"# Intraday Stage A replay — {hours[0]:%d %b %H:%M} to {hours[-1]:%d %b %H:%M} UTC", "",
             f"Kraken bars; rolling top-{n} universe by trailing 24h volume"
             + (f", plus forced: {', '.join(args.add)}" if args.add else "") + ". "
             f"Rule: 1h close > prior {CFG['intraday_breakout']['lookback_high_hours']}h high, volume >= "
             f"{CFG['intraday_breakout']['volume_multiple']}x prior {CFG['intraday_breakout']['volume_avg_hours']}h average, "
             f"+{CFG['intraday_breakout']['min_gain_pct']}% over {CFG['intraday_breakout']['gain_window_hours']}h. "
             "Every alert counts (no slot limit).", "",
             "## Coins the intraday check put in play", ""]
    adds = [m for m in sent if "IN PLAY (intraday)" in m[1]]
    if not adds:
        lines.append("None.")
    lines += ["| first seen (run, UTC) | symbol | in top-N then | 3-day high | 24h gain | what happened |",
              "|---|---|---|---|---|---|"] if adds else []
    for t, m in adds:
        sym = m.split("— ")[1].split("*")[0]
        row = next(r for r in ip if r["symbol"] == sym and str(r["breakout_date"])[:10] == f"{t - HOUR:%Y-%m-%d}")
        a = [x for x in al if x["symbol"] == sym and x.get("source") == "intraday"]
        what = (f"pullback entry {pd.Timestamp(a[0]['fired_at']):%d %b %H:%M}" if a
                else "taken over by a daily breakout" if row.get("source") is None else row["status"])
        gain = m.split("+")[1].split("%")[0]
        lines.append(f"| {t:%d %b %H:%M} | {sym} | {'yes' if _in_universe(bars, sym, t, n) else 'no (forced)'} | "
                     f"{row['breakout_level']:.4g} | +{gain}% | {what} |")

    def alert_table(alerts, title):
        out = [f"## {title}", ""]
        if not alerts:
            return out + ["None.", ""]
        out += ["| fired (run, UTC) | symbol | type | entry | stop | T1 | T2 | outcome | R |", "|---|---|---|---|---|---|---|---|---|"]
        for a in sorted((graded(x) for x in alerts), key=lambda x: x["fired_at"]):
            typ = "intraday pullback" if a.get("source") == "intraday" else a["entry_type"]
            r = a.get("r_multiple")
            out.append(f"| {pd.Timestamp(a['fired_at']):%d %b %H:%M} | {a['symbol']} | {typ} | {a['entry']:.4g} | {a['stop']:.4g} | "
                       f"{a['target1']:.4g} | {a['target2']:.4g} | {a.get('outcome', 'open')} | {'' if r is None else f'{r:+.2f}'} |")
        return out + [""]

    key = lambda a: (a["symbol"], a["entry_type"], round(a["entry"], 10))
    base_keys = {key(a) for a in base_al}
    lines += [""] + alert_table([a for a in al if key(a) not in base_keys], "Alerts only the intraday check produces")
    lines += alert_table([a for a in base_al if key(a) not in {key(x) for x in al}], "Daily-only alerts lost with intraday on")
    lines += alert_table(base_al, "All alerts, daily-only (what the live scanner did)")
    lines += [f"_Run {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC._"]
    out = ROOT / "data" / "intraday_replay.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
