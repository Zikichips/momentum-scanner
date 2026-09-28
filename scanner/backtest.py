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
from .outcomes import grade, scoreboard, SKIPPED
from .strategy import position_size


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


def apply_portfolio(results: list[dict], capital: float, max_concurrent: int | None,
                    max_position_pct: float, fees_pct: float) -> tuple[list[dict], dict]:
    """Replay graded setups in time order as one account. A setup is skipped
    (outcome skipped_concurrent) when max_concurrent trades are open, open meaning
    fired_at <= t < outcome_at. Taken trades are sized with position_size() and charged
    fees_pct on entry and on exit notional. Drawdown is on realised P&L (closed trades)."""
    ts = lambda v: pd.Timestamp(v).tz_convert("UTC") if pd.Timestamp(v).tzinfo else pd.Timestamp(v).tz_localize("UTC")
    rows = sorted((dict(r) for r in results if r.get("outcome") not in (None, "open")), key=lambda r: ts(r["fired_at"]))
    taken, peak_deployed = [], 0.0
    for r in rows:
        t = ts(r["fired_at"])
        live = [x for x in taken if x["_open"] <= t < x["_close"]]
        if max_concurrent is not None and len(live) >= max_concurrent:
            r["outcome"] = SKIPPED
            r["position_usd"] = r["pnl_usd"] = None
            continue
        size = position_size(r["entry"], r["stop"], capital, max_position_pct)
        fees = size * fees_pct / 100 * (1 + (1 + r["rule_return"] / 100))
        r.update(position_usd=size, pnl_usd=round(size * r["rule_return"] / 100 - fees, 2),
                 _open=t, _close=ts(r["outcome_at"]))
        peak_deployed = max(peak_deployed, size + sum(x["position_usd"] for x in live))
        taken.append(r)

    equity = peak = max_dd = 0.0
    for r in sorted(taken, key=lambda r: r["_close"]):
        equity += r["pnl_usd"]
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    for r in rows:
        r.pop("_open", None); r.pop("_close", None)
    pnls = [r["pnl_usd"] for r in taken]
    rs = [r["r_multiple"] for r in taken if r.get("r_multiple") is not None]
    stats = {
        "taken": len(taken), "skipped": len(rows) - len(taken),
        "win_rate": round(sum(r > 0 for r in rs) / len(rs), 3) if rs else None,
        "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
        "pnl_usd": round(sum(pnls), 2), "max_dd_usd": round(max_dd, 2),
        "worst_loss_usd": round(min([p for p in pnls if p < 0], default=0.0), 2),
        "peak_deployed_usd": round(peak_deployed, 2),
        "pnl_per_dd": round(sum(pnls) / max_dd, 2) if max_dd else None,
    }
    return rows, stats


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
    ap.add_argument("--top", type=int, default=30, help="Kraken top-N pairs by volume when no --symbols (live scans 150)")
    ap.add_argument("--capital", type=float, help="override account.capital_usd")
    ap.add_argument("--max-position", type=float, help="override account.max_position_pct")
    ap.add_argument("--max-concurrent", type=int, help="override account.max_concurrent_trades (0 = no limit)")
    ap.add_argument("--grid", action="store_true",
                    help="replay the same setups for capital {200,1000} x concurrent {2,3,none} x cap {50,75}")
    args = ap.parse_args()
    acct = CFG["account"]
    capital = args.capital or acct["capital_usd"]
    max_position = args.max_position or acct["max_position_pct"]
    max_concurrent = acct.get("max_concurrent_trades") if args.max_concurrent is None else (args.max_concurrent or None)
    fees = acct.get("fees_pct", 0.0)
    entries = [args.entry] if args.entry else entries_enabled()
    b = CFG["breakout"]
    warm_days = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 3
    start = pd.Timestamp.now(tz="UTC") - timedelta(days=args.days)

    all_results = []
    if args.csv:
        df = data.load_csv(args.csv)
        all_results += run_symbol(args.csv.split("/")[-1].replace(".csv", ""), args.asset_class, df, entries)
    else:
        syms = args.symbols or (data.crypto_universe()[:args.top] if args.asset_class == "crypto" else data.stock_universe())
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
    if args.grid:
        _grid(all_results, fees)
    all_results, pf = apply_portfolio(all_results, capital, max_concurrent, max_position, fees)
    out = pd.DataFrame(all_results)
    cols = ["entry_type", "symbol", "fired_at", "entry", "stop", "target1", "target2", "reward_risk", "outcome", "rule_return", "r_multiple", "hold_7d_return", "mfe_7d", "mae_7d"]
    print(out[[c for c in cols if c in out.columns]].to_string(index=False))
    sb = scoreboard(all_results)
    for t in entries:
        _print_summary(t, sb[t])
    _print_summary("combined", sb["overall"])
    print(f"\n[account] capital ${capital:,.0f}, max_concurrent {max_concurrent or 'none'}, "
          f"max_position {max_position:g}%, fees {fees}%/side -> {pf}")
    path = ROOT / "data" / f"backtest_{datetime.now():%Y%m%d_%H%M%S}.csv"
    out.to_csv(path, index=False); print("saved", path)


def _grid(results: list[dict], fees: float) -> None:
    cols = ["capital", "max_concurrent", "max_position_pct", "taken", "skipped", "win_rate", "avg_r",
            "pnl_usd", "max_dd_usd", "pnl_per_dd", "worst_loss_usd", "peak_deployed_usd"]
    print("\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
    for cap in (200, 1000):
        for mc in (2, 3, None):
            for mp in (50, 75):
                _, st = apply_portfolio(results, cap, mc, mp, fees)
                cell = {"capital": cap, "max_concurrent": mc or "none", "max_position_pct": mp, **st}
                print("| " + " | ".join(str(cell[c]) for c in cols) + " |")
    print()


if __name__ == "__main__":
    main()
