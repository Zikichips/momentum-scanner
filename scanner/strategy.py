"""Pure strategy logic. No I/O. Used by the live scanner and the backtester alike.

Stage A  detect_breakout(daily_df)       -> Breakout | None
         detect_intraday_breakout(1h_df) -> Breakout | None   (no entry; goes in play only)
         breakout_entry(bo, close)       -> Setup | None   (entry type "breakout")
Stage B  detect_pullback(intraday_df, bo) -> Setup | None   (entry type "pullback")
Stage C  targets, stop, sizing live inside each entry function
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
    ema_value: float | None
    pullback_low: float | None
    notes: str = ""
    entry_type: str = "pullback"

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


def detect_intraday_breakout(hourly: pd.DataFrame, symbol: str, asset_class: str) -> Breakout | None:
    """Return a Breakout if the LAST completed 1h bar closed above the prior 3-day high on
    volume >= 3x the prior 3-day hourly average, up >= 15% over 24h (intraday_breakout config).
    breakout_date is the hour bar's timestamp; the impulse is the gain window."""
    b = CFG["intraday_breakout"]
    w = b["gain_window_hours"]
    need = max(b["lookback_high_hours"], b["volume_avg_hours"], w) + 2
    if len(hourly) < need:
        return None

    df = hourly.copy()
    df["prior_high"] = rolling_high(df["high"], b["lookback_high_hours"])
    df["vol_avg"] = volume_avg(df["volume"], b["volume_avg_hours"])
    df["gain"] = pct_change_over(df["close"], w)

    last = df.iloc[-1]
    if not (last["close"] > last["prior_high"]
            and last["volume"] >= b["volume_multiple"] * last["vol_avg"]
            and last["gain"] >= b["min_gain_pct"]):
        return None

    window = df.iloc[-(w + 1):]   # the bar before the window (the base) plus the window
    return Breakout(
        symbol=symbol,
        asset_class=asset_class,
        breakout_date=df.index[-1].to_pydatetime(),
        breakout_level=float(last["prior_high"]),
        impulse_low=float(window["low"].min()),
        impulse_high=float(window["high"].max()),
        impulse_volume=float(window["volume"].iloc[1:].mean()),
        impulse_pct=float(last["gain"]),
    )


def update_impulse_high(bo: Breakout, daily: pd.DataFrame) -> Breakout:
    """While in play, the impulse high is the highest high since breakout."""
    since = daily[daily.index >= pd.Timestamp(bo.breakout_date)]
    if not since.empty:
        bo.impulse_high = max(bo.impulse_high, float(since["high"].max()))
    return bo


def breakout_entry(bo: Breakout, close: float) -> Setup | None:
    """Entry type "breakout": buy the close of the breakout day, no pullback wait.
    Stop under the broken level; targets are multiples of the impulse so far."""
    e = CFG["breakout_entry"]
    entry = float(close)
    stop = bo.breakout_level * (1 - e["stop_buffer_pct"] / 100)
    leg = entry - bo.impulse_low
    target1 = entry + e["t1_multiple"] * leg
    target2 = entry + e["t2_multiple"] * leg
    risk = entry - stop
    if risk <= 0 or leg <= 0:
        return None
    rr = (target2 - entry) / risk
    if rr < e["min_reward_risk"]:
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
        retrace_pct=0.0,
        ema_value=None,
        pullback_low=None,
        notes=f"breakout over {bo.breakout_level:.4g}, impulse +{bo.impulse_pct:.0f}%",
        entry_type="breakout",
    )


def late_breakout(bo: Breakout, close: float, price: float | None, now: pd.Timestamp) -> str | None:
    """Why the breakout entry (buy the breakout close) is no longer on offer, or None.
    Late = first seen more than max_alert_delay_hours after the breakout bar closed, or the
    current price is more than max_chase_pct above that close. price None = time check only."""
    e = CFG["breakout_entry"]
    hours = (now - (pd.Timestamp(bo.breakout_date) + pd.Timedelta(days=1))).total_seconds() / 3600
    if hours > e["max_alert_delay_hours"]:
        return f"seen {hours:.0f}h after the breakout close"
    if price is not None and price > close * (1 + e["max_chase_pct"] / 100):
        return f"price {price:.4g} is {(price / close - 1) * 100:.0f}% above the breakout close {close:.4g}"
    return None


def entries_enabled() -> list[str]:
    return CFG.get("entries", ["pullback"])


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
def position_size(entry: float, stop: float, capital: float | None = None,
                  max_position_pct: float | None = None) -> float:
    """Dollars to deploy so a stop-out costs risk_per_trade_pct of capital.
    capital / max_position_pct default to config (overrides are for backtest grids)."""
    a = CFG["account"]
    capital = a["capital_usd"] if capital is None else capital
    max_position_pct = a["max_position_pct"] if max_position_pct is None else max_position_pct
    risk_usd = capital * a["risk_per_trade_pct"] / 100
    per_unit_risk = (entry - stop) / entry
    if per_unit_risk <= 0:
        return 0.0
    size = risk_usd / per_unit_risk
    cap = capital * max_position_pct / 100
    return float(round(min(size, cap), 2))
