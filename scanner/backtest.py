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
from .strategy import detect_breakout, detect_pullback, update_impulse_high
from .outcomes import grade, scoreboard


def resample_daily(intraday: pd.DataFrame) -> pd.DataFrame:
    return intraday.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()


def run_symbol(symbol: str, asset_class: str, intraday: pd.DataFrame) -> list[dict]:
    daily = resample_daily(intraday)
    b = CFG["breakout"]
    expiry = timedelta(days=b["in_play_expiry_days"])
    results, in_play = [], None
    warm = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 2

    for i in range(warm, len(daily)):
        day_end = daily.index[i]
        # Stage A on daily bars up to and including this day
        if in_play is None:
            bo = detect_breakout(daily.iloc[: i + 1], symbol, asset_class)
            if bo:
                in_play = bo
                continue
        else:
            # Expiry / failure
            if day_end - pd.Timestamp(in_play.breakout_date) > expiry:
                in_play = None; continue
            if float(daily["close"].iloc[i]) < in_play.breakout_level:
                in_play = None; continue
            in_play = update_impulse_high(in_play, daily.iloc[: i + 1])
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=[])
    ap.add_argument("--asset-class", default="crypto")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--csv", help="offline: single-symbol intraday CSV")
    args = ap.parse_args()

    all_results = []
    if args.csv:
        df = data.load_csv(args.csv)
        all_results += run_symbol(args.csv.split("/")[-1].replace(".csv", ""), args.asset_class, df)
    else:
        ex = data._exchange() if args.asset_class == "crypto" else None
        syms = args.symbols or (data.crypto_universe(ex)[:30] if args.asset_class == "crypto" else data.stock_universe())
        bars_needed = args.days * 24
        for s in syms:
            try:
                # ccxt limits per call; page backwards
                frames, since = [], int((datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp() * 1000)
                while True:
                    raw = ex.fetch_ohlcv(s, timeframe="1h", since=since, limit=720)
                    if not raw:
                        break
                    frames += raw
                    since = raw[-1][0] + 1
                    if len(frames) >= bars_needed or len(raw) < 2:
                        break
                df = pd.DataFrame(frames, columns=["ts", *data.COLS])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                df = df.drop_duplicates("ts").set_index("ts")
                r = run_symbol(s, args.asset_class, df)
                print(f"{s}: {len(r)} setups")
                all_results += r
            except Exception as e:
                print(f"{s}: {e}")

    if not all_results:
        print("No setups found."); return
    out = pd.DataFrame(all_results)
    cols = ["symbol", "fired_at", "entry", "stop", "target1", "target2", "reward_risk", "outcome", "rule_return", "r_multiple", "hold_7d_return", "mfe_7d", "mae_7d"]
    print(out[[c for c in cols if c in out.columns]].to_string(index=False))
    print("\nSUMMARY:", scoreboard(all_results))
    path = ROOT / "data" / f"backtest_{datetime.now():%Y%m%d_%H%M}.csv"
    out.to_csv(path, index=False); print("saved", path)


if __name__ == "__main__":
    main()
