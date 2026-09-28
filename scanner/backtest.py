"""Walk-forward backtest of Stage A -> Stage B -> outcome rules over historical bars.

  python -m scanner.backtest --symbols BTC/USD ETH/USD SOL/USD --days 365
  python -m scanner.backtest --csv data/sample_QNT.csv          # offline / tests

Prints a per-setup table and summary stats (win rate, avg R, expectancy) and writes
data/backtest_<timestamp>.csv. This is the same code path as live: detect_breakout on
each daily bar, then detect_pullback on each subsequent intraday bar, then grade().
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import pandas as pd
from .config import CFG, ROOT
from . import data
from .strategy import detect_breakout, detect_pullback, breakout_entry, entries_enabled, update_impulse_high
from .outcomes import grade, scoreboard


def resample_daily(intraday: pd.DataFrame) -> pd.DataFrame:
    return intraday.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()


def run_symbol(symbol: str, asset_class: str, intraday: pd.DataFrame,
               entries: list[str] | None = None, start: pd.Timestamp | None = None) -> list[dict]:
    """entries: which entry types to trade (default: config). start: only breakouts on or
    after this day count; earlier bars are warm-up for the indicators."""
    entries = entries or entries_enabled()
    daily = resample_daily(intraday)
    b = CFG["breakout"]
    expiry = timedelta(days=b["in_play_expiry_days"])
    results, in_play = [], None
    warm = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 2

    for i in range(warm, len(daily)):
        day_end = daily.index[i]
        # Stage A on daily bars up to and including this day
        if in_play is None:
            if start is not None and day_end < start.normalize():
                continue
            bo = detect_breakout(daily.iloc[: i + 1], symbol, asset_class)
            if bo:
                in_play = bo
                if "breakout" in entries:
                    setup = breakout_entry(bo, float(daily["close"].iloc[i]))
                    if setup:
                        # Filled at the daily close: label it with the day's last intraday
                        # bar so grading starts with the next day's first bar.
                        day_bars = intraday[(intraday.index >= day_end) & (intraday.index < day_end + timedelta(days=1))]
                        if not day_bars.empty:
                            alert = {**setup.to_row(), "fired_at": day_bars.index[-1]}
                            results.append({**alert, **grade(alert, intraday, close_at_end=True)})
                continue
        else:
            # Expiry / failure
            if day_end - pd.Timestamp(in_play.breakout_date) > expiry:
                in_play = None; continue
            if float(daily["close"].iloc[i]) < in_play.breakout_level:
                in_play = None; continue
            in_play = update_impulse_high(in_play, daily.iloc[: i + 1])
            if "pullback" not in entries:
                continue
            # Stage B on each intraday bar within this day
            day_bars = intraday[(intraday.index > daily.index[i - 1]) & (intraday.index <= day_end + timedelta(days=1))]
            for ts in day_bars.index:
                hist = intraday[intraday.index <= ts]
                setup = detect_pullback(hist.tail(400), in_play)
                if setup:
                    alert = {**setup.to_row(), "fired_at": ts}
                    patch = grade(alert, intraday[intraday.index > ts], close_at_end=True)
                    results.append({**alert, **patch})
                    in_play = None
                    break
    return results


def _print_summary(label: str, stats: dict) -> None:
    w, l = stats["avg_win_r"], stats["avg_loss_r"]
    ratio = f"{w / abs(l):.2f}x" if w is not None and l else "–"
    print(f"\n[{label}] n={stats['alerts_graded']} win_rate={stats['win_rate']} avg_r={stats['avg_r']} "
          f"avg_win_r={w} avg_loss_r={l} win/loss={ratio} vs_hold_7d={stats['vs_hold_7d']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=[])
    ap.add_argument("--asset-class", default="crypto")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--csv", help="offline: single-symbol intraday CSV")
    ap.add_argument("--entry", choices=["pullback", "breakout"], help="run only this entry type")
    args = ap.parse_args()
    entries = [args.entry] if args.entry else entries_enabled()
    b = CFG["breakout"]
    warm_days = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 3
    start = pd.Timestamp.now(tz="UTC") - timedelta(days=args.days)

    all_results = []
    if args.csv:
        df = data.load_csv(args.csv)
        all_results += run_symbol(args.csv.split("/")[-1].replace(".csv", ""), args.asset_class, df, entries)
    else:
        syms = args.symbols or (data.crypto_universe()[:30] if args.asset_class == "crypto" else data.stock_universe())
        hist_ex = None
        if args.asset_class == "crypto":
            import ccxt
            hist_ex = getattr(ccxt, CFG["backtest"]["history_exchange"])({"enableRateLimit": True})
            hist_ex.load_markets()
        for s in syms:
            try:
                if hist_ex is not None and s not in hist_ex.markets:
                    print(f"{s}: not listed on {hist_ex.id}, skipped"); continue
                df = data.crypto_history(s, "1h", args.days + warm_days, hist_ex)
                r = run_symbol(s, args.asset_class, df, entries, start)
                print(f"{s}: {len(r)} setups " + " ".join(f"{t}={sum(x['entry_type'] == t for x in r)}" for t in entries))
                all_results += r
            except Exception as e:
                print(f"{s}: {e}")

    if not all_results:
        print("No setups found."); return
    out = pd.DataFrame(all_results)
    cols = ["entry_type", "symbol", "fired_at", "entry", "stop", "target1", "target2", "reward_risk", "outcome", "rule_return", "r_multiple", "hold_7d_return", "mfe_7d", "mae_7d"]
    print(out[[c for c in cols if c in out.columns]].to_string(index=False))
    sb = scoreboard(all_results)
    for t in entries:
        _print_summary(t, sb[t])
    _print_summary("combined", sb["overall"])
    path = ROOT / "data" / f"backtest_{datetime.now():%Y%m%d_%H%M%S}.csv"
    out.to_csv(path, index=False); print("saved", path)


if __name__ == "__main__":
    main()
