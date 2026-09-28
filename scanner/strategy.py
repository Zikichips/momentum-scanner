"""Pure strategy logic. No I/O. Used by the live scanner and the backtester alike.

Stage A  detect_breakout(daily_df)       -> Breakout | None
Stage B  detect_pullback(intraday_df, bo) -> Setup | None
Stage C  build_setup(...)                 -> targets, stop, sizing
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
from .config import CFG
from .indicators import ema, rolling_high, volume_avg, pct_change_over


@dataclass
class Breakout:
    symbol: str
    asset_class: str
    breakout_date: datetime          # date of the bar that broke the high
    breakout_level: float            # the prior 20-day high
    impulse_low: float               # low at start of impulse window
    impulse_high: float              # highest high since breakout (updated)
    impulse_volume: float            # avg volume across impulse window
    impulse_pct: float               # % gain over impulse window at breakout

    @property
    def impulse_range(self) -> float:
        return self.impulse_high - self.impulse_low


@dataclass
class Setup:
    symbol: str
    asset_class: str
    entry: float
    stop: float
    target1: float
    target2: float
    reward_risk: float
    position_usd: float
    retrace_pct: float
    ema_value: float
    pullback_low: float
    notes: str = ""

    def to_row(self) -> dict:
        return asdict(self)


# ------------------------------------------------------------------ Stage A
def detect_breakout(daily: pd.DataFrame, symbol: str, asset_class: str) -> Breakout | None:
    """Return a Breakout if the LAST completed daily bar qualifies."""
    b = CFG["breakout"]
    need = max(b["lookback_high_days"], b["volume_avg_days"]) + b["impulse_window_days"] + 2
    if len(daily) < need:
        return None

    df = daily.copy()
    df["prior_high"] = rolling_high(df["high"], b["lookback_high_days"])
    df["vol_avg"] = volume_avg(df["volume"], b["volume_avg_days"])
    df["impulse"] = pct_change_over(df["close"], b["impulse_window_days"])

    last = df.iloc[-1]
    min_imp = b["min_impulse_pct"][asset_class if asset_class in b["min_impulse_pct"] else "crypto"]

    cond_high = last["close"] > last["prior_high"]
    cond_vol = last["volume"] >= b["volume_multiple"] * last["vol_avg"]
    cond_imp = last["impulse"] >= min_imp
    if not (cond_high and cond_vol and cond_imp):
        return None

    window = df.iloc[-(b["impulse_window_days"] + 1):]
    # Impulse starts at the low of the bar BEFORE the impulse window began (the base).
    base_low = float(df["low"].iloc[-(b["impulse_window_days"] + 1)])
    return Breakout(
        symbol=symbol,
        asset_class=asset_class,
        breakout_date=df.index[-1].to_pydatetime(),
        breakout_level=float(last["prior_high"]),
        impulse_low=min(base_low, float(window["low"].min())),
        impulse_high=float(window["high"].max()),
        impulse_volume=float(window["volume"].mean()),
        impulse_pct=float(last["impulse"]),
    )


def update_impulse_high(bo: Breakout, daily: pd.DataFrame) -> Breakout:
    """While in play, the impulse high is the highest high since breakout."""
    since = daily[daily.index >= pd.Timestamp(bo.breakout_date)]
    if not since.empty:
        bo.impulse_high = max(bo.impulse_high, float(since["high"].max()))
    return bo


# ------------------------------------------------------------------ Stage B
def detect_pullback(intraday: pd.DataFrame, bo: Breakout) -> Setup | None:
    """Return a Setup if the LAST completed intraday bar qualifies as a tradeable pullback."""
    p, t, acct = CFG["pullback"], CFG["targets"], CFG["account"]
    if len(intraday) < p["ema_period"] * 3 or bo.impulse_range <= 0:
        return None

    df = intraday.copy()
    df["ema"] = ema(df["close"], p["ema_period"])
    last, prev = df.iloc[-1], df.iloc[-2]

    # Only bars since the impulse high count as the pullback.
    since_high = df[df.index >= _ts_of_high(df, bo)]
    if since_high.empty or len(since_high) < 2:
        return None
    pullback_low = float(since_high["low"].min())

    retrace = (bo.impulse_high - pullback_low) / bo.impulse_range
    if not (p["min_retrace"] <= retrace <= p["max_retrace"]):
        return None

    # Must hold above the original breakout level.
    if pullback_low < bo.breakout_level:
        return None

    # EMA rising and price reclaimed it after touching.
    if p["require_ema_rising"] and not (last["ema"] > prev["ema"]):
        return None
    touched = (since_high["low"] <= since_high["ema"]).any()
    if p["require_close_above_ema"] and not (touched and last["close"] > last["ema"]):
        return None

    # Sellers tired: pullback volume well below impulse volume (both per-bar averages,
    # scaled to the same bar size by comparing intraday to intraday where possible).
    impulse_bars = df[(df.index >= pd.Timestamp(bo.breakout_date)) & (df.index < _ts_of_high(df, bo))]
    if not impulse_bars.empty:
        ratio = since_high["volume"].mean() / max(impulse_bars["volume"].mean(), 1e-9)
        if ratio > p["pullback_volume_ratio_max"]:
            return None

    entry = float(last["close"])
    stop = pullback_low * (1 - t["stop_buffer_pct"] / 100)
    target1 = bo.impulse_high
    target2 = bo.impulse_high + t["t2_extension"] * bo.impulse_range
    risk = entry - stop
    if risk <= 0:
        return None
    rr = (target2 - entry) / risk
    if rr < p["min_reward_risk"]:
        return None

    return Setup(
        symbol=bo.symbol,
        asset_class=bo.asset_class,
        entry=entry,
        stop=float(stop),
        target1=float(target1),
        target2=float(target2),
        reward_risk=float(rr),
        position_usd=position_size(entry, stop),
        retrace_pct=float(retrace * 100),
        ema_value=float(last["ema"]),
        pullback_low=pullback_low,
        notes=f"retrace {retrace:.0%}, impulse +{bo.impulse_pct:.0f}%",
    )


def _ts_of_high(df: pd.DataFrame, bo: Breakout) -> pd.Timestamp:
    since = df[df.index >= pd.Timestamp(bo.breakout_date)]
    if since.empty:
        return df.index[-1]
    return since["high"].idxmax()


# ------------------------------------------------------------------ Stage C
def position_size(entry: float, stop: float) -> float:
    """Dollars to deploy so a stop-out costs risk_per_trade_pct of capital."""
    a = CFG["account"]
    risk_usd = a["capital_usd"] * a["risk_per_trade_pct"] / 100
    per_unit_risk = (entry - stop) / entry
    if per_unit_risk <= 0:
        return 0.0
    size = risk_usd / per_unit_risk
    cap = a["capital_usd"] * a["max_position_pct"] / 100
    return float(round(min(size, cap), 2))
