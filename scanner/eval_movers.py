"""Measure Stage A against Coinbase's daily top movers. Measurement only: no thresholds change.

  python -m scanner.eval_movers              # last 90 days
  python -m scanner.eval_movers --days 60

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

Writes data/movers_eval.md.
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


def _alerts(sym: str, daily: pd.DataFrame) -> tuple[list, set]:
    """(alerts the live scanner would send, days on which Stage A's conditions held at all)."""
    expiry = timedelta(days=CFG["breakout"]["in_play_expiry_days"])
    alerts, raw, in_play = [], set(), None
    for i in range(len(daily)):
        day = daily.index[i]
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
            "rule_return": patch["rule_return"], "r_multiple": patch["r_multiple"]}


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
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args()

    import ccxt
    ex = ccxt.coinbase({"enableRateLimit": True})
    ex.load_markets()
    syms = _universe(ex)
    b, e = CFG["breakout"], CFG["breakout_entry"]
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

    # --- movers
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
        alerts[s], raw[s] = _alerts(s, d)
    need_grade = {s: [a for a in al if a[0] >= start - LOOKBACK * DAY] for s, al in alerts.items()}
    need_grade = {s: al for s, al in need_grade.items() if al}
    print(f"grading {sum(map(len, need_grade.values()))} alerts on hourly bars ({len(need_grade)} pairs)...")
    graded = {}
    for s, al in need_grade.items():
        try:
            days_back = (pd.Timestamp.now(tz="UTC") - min(a[0] for a in al)).days + 2
            hourly = data.crypto_history(s, "1h", days_back, ex)
        except Exception as ex_:
            print(f"  {s}: {ex_}"); hourly = pd.DataFrame()
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
            if prev.empty or prev[["prior_high", "vol_mult", "gain_3d"]].isna().any(axis=None):
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
                **graded[(s, day)],
            })

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
        f"Window {start:%Y-%m-%d} to {last_day:%Y-%m-%d} ({args.days} days), {len(daily)} Coinbase USD pairs. "
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
        f"- Avg R — became mover: **{_avg([p['r_multiple'] for p in yes])}**; did not: **{_avg([p['r_multiple'] for p in no])}**.",
        f"- Alerts that did not become movers (R known for {len(no_r)}): "
        f"≤ −1R: {sum(r <= -1 for r in no_r)}, −1R to 0: {sum(-1 < r <= 0 for r in no_r)}, > 0: {sum(r > 0 for r in no_r)}; "
        f"median {pd.Series(no_r).median() if no_r else float('nan'):.2f}R, worst {min(no_r) if no_r else float('nan'):.2f}R.",
        "",
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
                  ["alert_day", "symbol", "impulse_pct", "alert_day_was_mover", "became_mover", "days_to_mover",
                   "entry", "trade", "rule_return", "r_multiple"]),
        "",
    ]
    report = "\n".join(lines)
    (ROOT / "data" / "movers_eval.md").write_text(report)
    print(report.split("## Caught movers")[0])
    print("written data/movers_eval.md")


if __name__ == "__main__":
    main()
