"""Small, dependency-free indicator helpers on OHLCV DataFrames."""
from __future__ import annotations
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rolling_high(series: pd.Series, window: int) -> pd.Series:
    """Highest high of the PREVIOUS `window` bars (excludes current bar)."""
    return series.shift(1).rolling(window).max()


def volume_avg(series: pd.Series, window: int) -> pd.Series:
    return series.shift(1).rolling(window).mean()


def pct_change_over(series: pd.Series, bars: int) -> pd.Series:
    return (series / series.shift(bars) - 1.0) * 100.0
