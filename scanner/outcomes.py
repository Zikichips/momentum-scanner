"""Daily grader. For every alert, looks at what price did afterwards and records:
  - outcome: stop | t1 | t2 | open | expired  (which was hit first, on intraday bars)
  - MFE/MAE at 1/3/7/14 days (max favourable / adverse excursion, %)
  - hold_7d / hold_14d returns (if you'd just held)
  - rule_return and r_multiple (if you'd followed the rules: half off at T1, stop to entry, rest at T2/stop)
Then writes a daily scoreboard row. Runs once a day via GitHub Actions.

Pure function grade(alert, df) is reused by the backtester.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import pandas as pd
from .config import CFG
from . import data
from .db import Store

HORIZONS = (1, 3, 7, 14)


def grade(alert: dict, df: pd.DataFrame, max_days: int = 14, close_at_end: bool = False) -> dict:
    """df: intraday bars starting at/after fired_at. Returns a patch dict.
    close_at_end=True (backtests) marks an unresolved trade closed at the last bar."""
    entry, stop, t1, t2 = alert["entry"], alert["stop"], alert["target1"], alert["target2"]
    fired = pd.Timestamp(alert["fired_at"])
    if fired.tzinfo is None:
        fired = fired.tz_localize("UTC")
    df = df[df.index > fired]
    if df.empty:
        return {}

    patch: dict = {}
    # --- excursions
    for h in HORIZONS:
        w = df[df.index <= fired + timedelta(days=h)]
        if w.empty:
            continue
        patch[f"mfe_{h}d"] = round((w["high"].max() / entry - 1) * 100, 3)
        patch[f"mae_{h}d"] = round((w["low"].min() / entry - 1) * 100, 3)
    for h in (7, 14):
        w = df[df.index <= fired + timedelta(days=h)]
        if not w.empty:
            patch[f"hold_{h}d_return"] = round((float(w["close"].iloc[-1]) / entry - 1) * 100, 3)

    # --- rule-following simulation, bar by bar
    risk = entry - stop
    half_taken = False
    cur_stop = stop
    realised = 0.0     # in % of entry, weighted by fraction of position
    outcome = "open"
    outcome_at = None
    for ts, bar in df.iterrows():
        if ts > fired + timedelta(days=max_days):
            outcome = "expired"; outcome_at = ts
            realised += (0.5 if half_taken else 1.0) * (float(bar["close"]) / entry - 1) * 100
            break
        lo, hi, close = float(bar["low"]), float(bar["high"]), float(bar["close"])
        # Stop check uses close (rule: exit on close below stop) but a gap through is honoured at the low.
        if close < cur_stop:
            px = min(close, cur_stop) if lo < cur_stop else close
            realised += (0.5 if half_taken else 1.0) * (px / entry - 1) * 100
            outcome = "t1" if half_taken else "stop"; outcome_at = ts
            break
        if not half_taken and hi >= t1:
            realised += 0.5 * (t1 / entry - 1) * 100
            half_taken = True
            cur_stop = entry
            if hi >= t2:
                realised += 0.5 * (t2 / entry - 1) * 100
                outcome = "t2"; outcome_at = ts
                break
            continue
        if half_taken and hi >= t2:
            realised += 0.5 * (t2 / entry - 1) * 100
            outcome = "t2"; outcome_at = ts
            break

    if outcome == "open":
        if close_at_end:
            last = df.iloc[-1]
            realised += (0.5 if half_taken else 1.0) * (float(last["close"]) / entry - 1) * 100
            outcome, outcome_at = ("t1" if half_taken else "expired"), df.index[-1]
        else:
            return patch   # not resolved yet; leave outcome fields alone
    patch["outcome"] = outcome
    patch["outcome_at"] = outcome_at.isoformat() if outcome_at is not None else None
    patch["rule_return"] = round(realised, 3)
    patch["r_multiple"] = round(realised / ((risk / entry) * 100), 3) if risk > 0 else None
    return patch


def scoreboard(alerts: list[dict]) -> dict:
    graded = [a for a in alerts if a.get("outcome") not in (None, "open")]
    wins = [a for a in graded if (a.get("r_multiple") or 0) > 0]
    losses = [a for a in graded if (a.get("r_multiple") or 0) <= 0]
    rs = [a["r_multiple"] for a in graded if a.get("r_multiple") is not None]
    holds = [a["hold_7d_return"] for a in graded if a.get("hold_7d_return") is not None]
    rules = [a["rule_return"] for a in graded if a.get("rule_return") is not None]
    return {
        "day": datetime.now(timezone.utc).date().isoformat(),
        "alerts_total": len(alerts),
        "alerts_graded": len(graded),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(graded), 3) if graded else None,
        "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
        "expectancy_r": round(sum(rs) / len(rs), 3) if rs else None,
        "vs_hold_7d": round(sum(rules) / len(rules) - sum(holds) / len(holds), 3) if rules and holds else None,
    }


def main():
    store = Store()
    ex = data._exchange() if CFG["universe"]["crypto"]["enabled"] else None
    alerts = store.select("alerts")
    for a in alerts:
        # Re-grade anything open or graded within the last 14 days (excursions keep growing).
        fired = pd.Timestamp(a["fired_at"])
        if fired.tzinfo is None:
            fired = fired.tz_localize("UTC")
        if a.get("outcome") not in (None, "open") and datetime.now(timezone.utc) - fired > timedelta(days=15):
            continue
        try:
            df = data.ohlcv(a["symbol"], a["asset_class"], CFG["timeframes"]["intraday"], limit=400, ex=ex)
            patch = grade(a, df)
            if patch:
                store.update("alerts", a["id"], patch)
                a.update(patch)
        except Exception as e:
            print(f"[outcomes] {a['symbol']}: {e}")
    sb = scoreboard(store.select("alerts"))
    store.upsert("scoreboard_daily", sb, on_conflict="day")
    print(sb)


if __name__ == "__main__":
    main()
