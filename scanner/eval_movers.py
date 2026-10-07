"""Measure Stage A against Coinbase's daily top movers. Measurement only: no thresholds change.

  python -m scanner.eval_movers              # last 90 days
  python -m scanner.eval_movers --days 60
  python -m scanner.eval_movers --universe kraken   # only the live scanner's Kraken top-N pairs

Movers: for each UTC day, the 10 Coinbase-listed USD pairs with the largest close-to-close
gain, keeping only gains >= 20%. (Coinbase's own list is a rolling 24h; UTC daily closes are
the closest reproducible version. Only pairs listed today are covered, so coins delisted in
the window are missing.)

Alerts are what the live scanner would send: detect_breakout on each closed daily bar,
suppressed while the coin is already in play (5-day expiry, or a close below the breakout
level), as in backtest.run_symbol. The pullback trigger, which also ends in_play, is not
modelled here (it needs hourly bars for every coin). Each alert is graded as a breakout entry
on hourly bars, exactly as the backtester does.

Recall:    for each (coin, mover day D), was there an alert on D-5..D-1?
Precision: for each alert on day A, was the coin a mover on A+1..A+5?
Matrix:    every (coin, day D) in the window: mover on D x alert on D-5..D-1.

--universe kraken30 / widened compare the live universes day by day on one movers list (every
Coinbase USD pair): kraken30 = that day's Kraken top-N by quote volume (no hindsight); widened =
kraken30 plus that day's Coinbase movers (universe.crypto.coinbase_movers: 3-day gain in range,
volume floor). Both can be given in one run (shared downloads) and add an account replay at the
configured capital / max concurrent / fees, as backtest.apply_portfolio does.

--universe kraken restricts everything (movers list included) to data.crypto_universe(),
i.e. the pairs the live scanner scans, keeping those Coinbase also lists (history source).
That list is today's top-N by volume, so it favours coins that moved recently.

Writes data/movers_eval.md (or data/movers_eval_kraken.md).
"""
from __future__ import annotations
import argparse
from datetime import timedelta
import pandas as pd
from .config import CFG, ROOT
from . import data
from .indicators import rolling_high, volume_avg, pct_change_over
from .strategy import detect_breakout, breakout_entry
from .outcomes import grade

TOP_N = 10
MIN_GAIN = 20.0
LOOKBACK = 5          # recall: alert on D-5..D-1; precision: mover on A+1..A+5
DAY = timedelta(days=1)


# ------------------------------------------------------------------ data
def _universe(ex) -> list[str]:
    excl = set(CFG["universe"]["crypto"]["exclude"])
    return sorted(s for s, m in ex.markets.items()
                  if m.get("spot") and m.get("quote") == "USD" and m.get("active") is not False
                  and m.get("base") not in excl)


def _conditions(daily: pd.DataFrame) -> pd.DataFrame:
    """The three Stage A inputs per bar, computed with the same helpers as detect_breakout."""
    b = CFG["breakout"]
    df = daily.copy()
    df["prior_high"] = rolling_high(df["high"], b["lookback_high_days"])
    df["vol_mult"] = df["volume"] / volume_avg(df["volume"], b["volume_avg_days"])
    df["gain_3d"] = pct_change_over(df["close"], b["impulse_window_days"])
    df["day_gain"] = pct_change_over(df["close"], 1)
    return df


def _alerts(sym: str, daily: pd.DataFrame, active=None) -> tuple[list, set]:
    """(alerts the live scanner would send, days on which Stage A's conditions held at all).
    active(day) -> bool: whether the coin was in the scanned universe that day (None = always)."""
    expiry = timedelta(days=CFG["breakout"]["in_play_expiry_days"])
    alerts, raw, in_play = [], set(), None
    for i in range(len(daily)):
        day = daily.index[i]
        if active is not None and not active(day):
            bo = None
        else:
            bo = detect_breakout(daily.iloc[: i + 1], sym, "crypto")
        if bo:
            raw.add(day)
        if in_play is not None:
            if day - pd.Timestamp(in_play.breakout_date) > expiry or float(daily["close"].iloc[i]) < in_play.breakout_level:
                in_play = None
            continue
        if bo:
            in_play = bo
            alerts.append((day, bo, float(daily["close"].iloc[i])))
    return alerts, raw


def _grade_alert(bo, close: float, day: pd.Timestamp, hourly: pd.DataFrame) -> dict:
    setup = breakout_entry(bo, close)
    if setup is None:
        return {"entry": close, "trade": "no entry (R:R < min)", "rule_return": None, "r_multiple": None}
    day_bars = hourly[(hourly.index >= day) & (hourly.index < day + DAY)]
    if day_bars.empty:
        return {"entry": setup.entry, "trade": "no hourly data", "rule_return": None, "r_multiple": None}
    fired = day_bars.index[-1]
    patch = grade({**setup.to_row(), "fired_at": fired}, hourly, close_at_end=True)
    if not patch:
        return {"entry": setup.entry, "trade": "no bars yet", "rule_return": None, "r_multiple": None}
    still_open = fired + timedelta(days=14) > hourly.index[-1] and patch["outcome"] in ("expired", "t1")
    return {"entry": setup.entry, "trade": patch["outcome"] + (" (open, marked at last bar)" if still_open else ""),
            "rule_return": patch["rule_return"], "r_multiple": patch["r_multiple"],
            "stop": setup.stop, "outcome": patch["outcome"], "fired_at": fired, "outcome_at": patch["outcome_at"],
            "position_usd": setup.position_usd, "pnl_usd": round(setup.position_usd * patch["rule_return"] / 100, 2)}


# ------------------------------------------------------------------ report helpers
def _md_table(rows: list[dict], cols: list[str]) -> str:
    def fmt(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "–"
        if isinstance(v, float):
            return f"{v:.2f}"
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return str(v)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _pct(a, b):
    return f"{a / b:.0%}" if b else "–"


# ------------------------------------------------------------------ main
def _kraken_top(days: pd.DatetimeIndex, top: int, cb_markets) -> dict:
    """{day: set of symbols}: the Kraken top-N USD pairs by that day's quote volume (close x
    volume of the daily bar), among pairs Coinbase also lists (the history source here). The
    live scanner ranks by rolling 24h volume; at its first run after 00:00 UTC that is ~day D."""
    import time
    kr = data._exchange()
    excl = set(CFG["universe"]["crypto"]["exclude"])
    syms = [s for s, m in kr.markets.items() if m.get("spot") and m.get("quote") == "USD" and m.get("base") not in excl]
    print(f"ranking {len(syms)} Kraken USD pairs by daily volume...")
    vols = {}
    for s in syms:
        try:
            d = data.crypto_ohlcv(s, "1d", limit=720, ex=kr)
            vols[s] = d["close"] * d["volume"]
        except Exception as e:
            print(f"  {s}: {e}")
        time.sleep(0.05)
    vol = pd.DataFrame(vols).fillna(0.0)
    return {D: {s for s in vol.loc[D].nlargest(top).index if s in cb_markets} if D in vol.index else set() for D in days}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--universe", nargs="+", choices=["coinbase", "kraken", "kraken30", "widened"], default=["coinbase"])
    ap.add_argument("--capital", type=float, help="override account.capital_usd for this run (sizing / $ P&L only)")
    args = ap.parse_args()
    if args.capital:
        CFG["account"]["capital_usd"] = args.capital

    import ccxt
    ex = ccxt.coinbase({"enableRateLimit": True})
    ex.load_markets()
    syms = _universe(ex)
    if args.universe == ["kraken"]:
        kraken = data.crypto_universe()
        syms = [s for s in kraken if s in ex.markets]
    b = CFG["breakout"]
    warm = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 3

    print(f"fetching daily bars for {len(syms)} Coinbase USD pairs...")
    daily, cond = {}, {}
    for s in syms:
        try:
            d = data.crypto_history(s, "1d", args.days + warm + LOOKBACK, ex)
            if len(d) >= 2:
                daily[s], cond[s] = d, _conditions(d)
        except Exception as ex_:
            print(f"  {s}: {ex_}")
    last_day = max(d.index[-1] for d in daily.values())
    start = last_day - timedelta(days=args.days - 1)
    print(f"window {start:%Y-%m-%d} .. {last_day:%Y-%m-%d}, {len(daily)} pairs with data")

    ktop = None
    if {"kraken30", "widened"} & set(args.universe):
        all_days = pd.DatetimeIndex(sorted({D for d in daily.values() for D in d.index}))
        ktop = _kraken_top(all_days, CFG["universe"]["crypto"]["top_n_by_volume"], ex.markets)
    hourly_cache: dict = {}
    for mode in args.universe:
        _report(mode, args, ex, daily, cond, start, last_day, ktop, hourly_cache)


def _membership(mode: str, daily: dict, ktop: dict | None):
    """(active(sym) -> active(day) | None, via(sym, day) -> 'kraken' | 'coinbase mover' | None, note)."""
    top_n = CFG["universe"]["crypto"]["top_n_by_volume"]
    if mode == "kraken30":
        return (lambda s: (lambda D: s in ktop.get(D, ()))), (lambda s, D: "kraken"), \
            f"Kraken top {top_n} by each day's volume (rolling, no hindsight), on Coinbase data"
    if mode == "widened":
        m = CFG["universe"]["crypto"]["coinbase_movers"]
        w = m["gain_window_days"]
        gain = {s: (d["close"] / d["close"].shift(w) - 1) * 100 for s, d in daily.items()}
        qvol = {s: d["close"] * d["volume"] for s, d in daily.items()}
        def mover(s, D):
            g, v = gain[s].get(D), qvol[s].get(D)
            return g is not None and v is not None and m["min_gain_pct"] <= g <= m["max_gain_pct"] and v >= m["min_volume_usd"]
        via = lambda s, D: "kraken" if s in ktop.get(D, ()) else "coinbase mover" if mover(s, D) else None
        return (lambda s: (lambda D: via(s, D) is not None)), via, \
            (f"Kraken top {top_n} by each day's volume plus that day's Coinbase movers ({m['min_gain_pct']}–"
             f"{m['max_gain_pct']}% over {w}d, ≥ ${m['min_volume_usd'] / 1e6:.0f}M volume)")
    return (lambda s: None), (lambda s, D: None), None


def _report(mode, args, ex, daily, cond, start, last_day, ktop, hourly_cache):
    b, e = CFG["breakout"], CFG["breakout_entry"]
    active_for, via, note = _membership(mode, daily, ktop)
    universe_note = note or f"{len(daily)} Coinbase USD pairs"
    if mode == "kraken":
        universe_note = f"live scanner universe: Kraken top-N by volume today, {len(daily)} of them listed on Coinbase"
    print(f"\n=== {mode}: {universe_note}")

    # --- movers (always over every pair loaded: the same list for every universe)
    rows = []
    for s, c in cond.items():
        w = c[(c.index >= start) & (c["day_gain"] >= MIN_GAIN)]
        rows += [(day, s, float(g)) for day, g in w["day_gain"].items()]
    mv = pd.DataFrame(rows, columns=["day", "symbol", "gain"])
    mv = mv.sort_values(["day", "gain"], ascending=[True, False]).groupby("day").head(TOP_N)
    mover_set = set(zip(mv["symbol"], mv["day"]))

    # --- alerts
    alerts, raw = {}, {}
    for s, d in daily.items():
        alerts[s], raw[s] = _alerts(s, d, active_for(s))
    need_grade = {s: [a for a in al if a[0] >= start - LOOKBACK * DAY] for s, al in alerts.items()}
    need_grade = {s: al for s, al in need_grade.items() if al}
    print(f"grading {sum(map(len, need_grade.values()))} alerts on hourly bars ({len(need_grade)} pairs)...")
    graded = {}
    for s, al in need_grade.items():
        days_back = (pd.Timestamp.now(tz="UTC") - min(a[0] for a in al)).days + 2
        if s not in hourly_cache or hourly_cache[s][0] < days_back:
            try:
                hourly_cache[s] = (days_back, data.crypto_history(s, "1h", days_back, ex))
            except Exception as ex_:
                print(f"  {s}: {ex_}"); hourly_cache[s] = (days_back, pd.DataFrame())
        hourly = hourly_cache[s][1]
        for day, bo, close in al:
            graded[(s, day)] = _grade_alert(bo, close, day, hourly) if not hourly.empty else \
                {"entry": close, "trade": "no hourly data", "rule_return": None, "r_multiple": None}

    # --- recall
    recall = []
    for _, m in mv.iterrows():
        s, D = m["symbol"], m["day"]
        hits = [a for a in alerts[s] if D - LOOKBACK * DAY <= a[0] <= D - DAY]
        r = {"day": D, "symbol": s, "gain_pct": m["gain"]}
        if hits:
            day = hits[0][0]
            g = graded[(s, day)]
            r.update({"caught": "yes", "alert_day": day, "lead_days": (D - day).days, **g})
        else:
            c = cond[s]
            prev = c[c.index == D - DAY]
            r["caught"] = "no"
            act = active_for(s)
            if act is not None and not any(act(x) for x in pd.date_range(D - LOOKBACK * DAY, D - DAY, tz="UTC")):
                r["why"] = "not in universe on D−5..D−1"
            elif prev.empty or prev[["prior_high", "vol_mult", "gain_3d"]].isna().any(axis=None):
                r["why"] = "not enough history"
            else:
                p = prev.iloc[0]
                fails = []
                if not p["close"] > p["prior_high"]:
                    fails.append("prior-high")
                if not p["vol_mult"] >= b["volume_multiple"]:
                    fails.append("volume")
                if not p["gain_3d"] >= b["min_impulse_pct"]["crypto"]:
                    fails.append("3d-gain")
                if any(D - LOOKBACK * DAY <= x <= D - DAY for x in raw[s]):
                    fails = ["suppressed (already in play)"]
                r.update({"why": " + ".join(fails) or "?", "close_vs_high_pct": (p["close"] / p["prior_high"] - 1) * 100,
                          "vol_mult": p["vol_mult"], "gain_3d": p["gain_3d"]})
            r["fired_on_day"] = "yes" if D in raw[s] else "no"
        recall.append(r)

    # --- precision
    precision = []
    for s, al in alerts.items():
        for day, bo, close in al:
            if day < start:
                continue
            ahead = [x for x in mv[mv["symbol"] == s]["day"] if day + DAY <= x <= day + LOOKBACK * DAY]
            complete = day + LOOKBACK * DAY <= last_day
            precision.append({
                "alert_day": day, "symbol": s, "impulse_pct": bo.impulse_pct,
                "became_mover": "yes" if ahead else ("no" if complete else "pending"),
                "days_to_mover": (min(ahead) - day).days if ahead else None,
                "alert_day_was_mover": "yes" if (s, day) in mover_set else "no",
                "via": via(s, day),
                **graded[(s, day)],
            })

    # --- account replay: the same alerts as one account at the configured capital, max
    # concurrent trades and fees (same-day ties: Kraken top-N first, as the live scan order)
    from .backtest import apply_portfolio
    acct = CFG["account"]
    tradable = sorted((p for p in precision if p.get("outcome") and p.get("fired_at") is not None),
                      key=lambda p: (p["alert_day"], p.get("via") != "kraken"))
    acct_rows, acct_stats = apply_portfolio(tradable, acct["capital_usd"], acct.get("max_concurrent_trades"),
                                            acct["max_position_pct"], acct.get("fees_pct", 0.0))
    by_via = {}
    for v in sorted({p.get("via") for p in precision if p.get("via")}):
        sub = [p for p in precision if p.get("via") == v and p["became_mover"] != "pending"]
        tk = [r for r in acct_rows if r.get("via") == v and r.get("taken")]
        by_via[v] = {"via": v, "alerts": len([p for p in precision if p.get("via") == v]), "judged": len(sub),
                     "became_mover": sum(p["became_mover"] == "yes" for p in sub), "avg_r": _avg([p["r_multiple"] for p in sub]),
                     "taken": len(tk), "account_pnl_usd": round(sum(r["pnl_usd"] for r in tk), 2)}

    # --- confusion matrix over every (coin, day) in the window
    tp = fn = fp = tn = 0
    for s, d in daily.items():
        adays = [a[0] for a in alerts[s]]
        for D in d.index[d.index >= start]:
            alerted = any(D - LOOKBACK * DAY <= x <= D - DAY for x in adays)
            mover = (s, D) in mover_set
            tp += mover and alerted; fn += mover and not alerted
            fp += alerted and not mover; tn += not mover and not alerted

    # --- summaries
    n_mv = len(recall)
    caught = [r for r in recall if r["caught"] == "yes"]
    missed = [r for r in recall if r["caught"] == "no"]
    why = pd.Series([r["why"] for r in missed]).value_counts() if missed else pd.Series(dtype=int)
    late = sum(r["fired_on_day"] == "yes" for r in missed)
    leads = pd.Series([r["lead_days"] for r in caught]).value_counts().sort_index() if caught else pd.Series(dtype=int)
    judged = [p for p in precision if p["became_mover"] != "pending"]
    yes = [p for p in judged if p["became_mover"] == "yes"]
    no = [p for p in judged if p["became_mover"] == "no"]
    no_r = [p["r_multiple"] for p in no if p["r_multiple"] is not None]
    miss_diag = [r for r in missed if "vol_mult" in r and r["why"] != "suppressed (already in play)"]
    med = lambda k: float(pd.Series([r[k] for r in miss_diag]).median()) if miss_diag else float("nan")

    lines = [
        f"# Stage A vs Coinbase top movers",
        "",
        f"Window {start:%Y-%m-%d} to {last_day:%Y-%m-%d} ({args.days} days), {universe_note}, {len(daily)} with data. "
        f"Mover = top {TOP_N} by UTC close-to-close gain that day, gain ≥ {MIN_GAIN:.0f}%. "
        f"Thresholds as in config.yaml: close > {b['lookback_high_days']}-day high, volume ≥ {b['volume_multiple']}× "
        f"{b['volume_avg_days']}-day avg, 3-day gain ≥ {b['min_impulse_pct']['crypto']}%. "
        f"Breakout entry: stop {e['stop_buffer_pct']}% under level, T1/T2 = {e['t1_multiple']}×/{e['t2_multiple']}× leg.",
        "",
        "## Recall — did Stage A alert in the 5 days before a mover day?",
        "",
        f"- Mover days: **{n_mv}**. Caught: **{len(caught)} ({_pct(len(caught), n_mv)})**. Missed: {len(missed)}.",
        f"- Lead time on caught movers (days before the mover day): " + (", ".join(f"{k}d: {v}" for k, v in leads.items()) or "–"),
        f"- Caught movers' breakout entries: avg R {_avg([r.get('r_multiple') for r in caught])}, "
        f"avg rule return {_avg([r.get('rule_return') for r in caught])}%.",
        f"- Of the misses, Stage A fired **on the mover day itself** (i.e. after the move) for {late} ({_pct(late, len(missed))}).",
        f"- Misses by failed condition on the D−1 bar:",
        "",
        _md_table([{"why": k, "count": v, "share": _pct(v, len(missed))} for k, v in why.items()], ["why", "count", "share"]),
        "",
        f"Median on D−1 for diagnosable misses: close vs 20-day high {med('close_vs_high_pct'):+.1f}%, "
        f"volume {med('vol_mult'):.2f}×, 3-day gain {med('gain_3d'):+.1f}%.",
        "",
        "## Precision — did alerts become movers within 5 days?",
        "",
        f"- Alerts in window: **{len(precision)}** ({len(precision) - len(judged)} too recent to judge).",
        f"- Became a mover on A+1..A+5: **{len(yes)} of {len(judged)} ({_pct(len(yes), len(judged))})**.",
        f"- Alert day itself was already a mover: {sum(p['alert_day_was_mover'] == 'yes' for p in judged)} of {len(judged)}.",
        f"- Avg R per alert, all judged alerts: **{_avg([p['r_multiple'] for p in judged])}** "
        f"(R known for {sum(p['r_multiple'] is not None for p in judged)} of {len(judged)}).",
        f"- Dollars at ${CFG['account']['capital_usd']:,.0f} capital ({CFG['account']['risk_per_trade_pct']}% risk, "
        f"{CFG['account']['max_position_pct']}% cap), no fees: total **${sum(p.get('pnl_usd') or 0 for p in judged):,.2f}** "
        f"over {sum(p.get('pnl_usd') is not None for p in judged)} trades, avg ${_avg([p.get('pnl_usd') for p in judged])}/alert; "
        f"became mover ${sum(p.get('pnl_usd') or 0 for p in yes):,.2f}, did not ${sum(p.get('pnl_usd') or 0 for p in no):,.2f}. "
        f"Each alert is traded independently, so overlapping positions can exceed capital.",
        f"- Avg R — became mover: **{_avg([p['r_multiple'] for p in yes])}**; did not: **{_avg([p['r_multiple'] for p in no])}**.",
        f"- Alerts that did not become movers (R known for {len(no_r)}): "
        f"≤ −1R: {sum(r <= -1 for r in no_r)}, −1R to 0: {sum(-1 < r <= 0 for r in no_r)}, > 0: {sum(r > 0 for r in no_r)}; "
        f"median {pd.Series(no_r).median() if no_r else float('nan'):.2f}R, worst {min(no_r) if no_r else float('nan'):.2f}R.",
        "",
        f"## Account replay — ${acct['capital_usd']:,.0f}, max {acct.get('max_concurrent_trades') or 'no limit'} open, "
        f"{acct['max_position_pct']}% cap, {acct.get('fees_pct', 0)}%/side fees",
        "",
        f"Every graded breakout entry in the window replayed as one account (trades still open are marked at the last bar). "
        f"Taken {acct_stats['taken']}, skipped at the limit {acct_stats['skipped']}; win rate {acct_stats['win_rate']}, "
        f"avg R {acct_stats['avg_r']}; **P&L ${acct_stats['pnl_usd']:,.2f}**, max drawdown ${acct_stats['max_dd_usd']:,.2f}, "
        f"worst trade ${acct_stats['worst_loss_usd']:,.2f}.",
        "",
        *([_md_table(list(by_via.values()), ["via", "alerts", "judged", "became_mover", "avg_r", "taken", "account_pnl_usd"]), ""]
          if len(by_via) > 1 else []),
        "## Confusion matrix — every (coin, day) in the window",
        "",
        "| | Alert in prior 5 days | No alert |",
        "|---|---|---|",
        f"| **Mover that day** | {tp} | {fn} |",
        f"| **Not a mover** | {fp} | {tn} |",
        "",
        f"Recall {_pct(tp, tp + fn)}. Precision per coin-day {_pct(tp, tp + fp)} (differs from per-alert precision above: "
        f"one alert covers 5 coin-days).",
        "",
        "## Caught movers",
        "",
        _md_table(caught, ["day", "symbol", "gain_pct", "alert_day", "lead_days", "entry", "trade", "rule_return", "r_multiple"]),
        "",
        "## Missed movers",
        "",
        _md_table(missed, ["day", "symbol", "gain_pct", "why", "close_vs_high_pct", "vol_mult", "gain_3d", "fired_on_day"]),
        "",
        "## Alerts",
        "",
        _md_table(sorted(precision, key=lambda p: p["alert_day"]),
                  ["alert_day", "symbol", *(["via"] if by_via else []), "impulse_pct", "alert_day_was_mover", "became_mover",
                   "days_to_mover", "entry", "trade", "rule_return", "r_multiple", "position_usd", "pnl_usd"]),
        "",
    ]
    report = "\n".join(lines)
    suffix = ("" if mode == "coinbase" else f"_{mode}") + ("" if args.days == 90 else f"_{args.days}d") \
        + (f"_{args.capital:g}usd" if args.capital else "")
    out = ROOT / "data" / f"movers_eval{suffix}.md"
    out.write_text(report)
    print(report.split("## Confusion matrix")[0])
    print("written", out)


if __name__ == "__main__":
    main()
