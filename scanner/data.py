"""Market data access. Crypto via ccxt (public endpoints, no key), stocks via yfinance.

Every function returns a pandas DataFrame indexed by UTC timestamp with columns
open, high, low, close, volume. Nothing else in the project touches an API directly.
"""
from __future__ import annotations
import time
from pathlib import Path
import pandas as pd
from .config import CFG, ROOT

COLS = ["open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------- crypto
def _exchange():
    import ccxt
    ex_id = CFG["universe"]["crypto"]["exchange"]
    ex = getattr(ccxt, ex_id)({"enableRateLimit": True})
    ex.load_markets()
    return ex


def crypto_universe(ex=None) -> list[str]:
    """Top-N spot pairs by 24h quote volume, quoted in the configured currency."""
    return [s for s, _ in crypto_universe_with_volume(ex)]


def crypto_universe_with_volume(ex=None) -> list[tuple[str, float]]:
    """crypto_universe() with each pair's 24h quote volume, busiest first."""
    ex = ex or _exchange()
    u = CFG["universe"]["crypto"]
    quote, excl, n = u["quote"], set(u["exclude"]), u["top_n_by_volume"]
    tickers = ex.fetch_tickers()
    rows = []
    for sym, t in tickers.items():
        if not sym.endswith(f"/{quote}"):
            continue
        base = sym.split("/")[0]
        if base in excl:
            continue
        qv = t.get("quoteVolume") or 0
        rows.append((sym, qv))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:n]


def closed_bars(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Drop the still-forming last bar. Exchanges return it, but the strategy must only
    see completed bars (an hour-old daily bar has a fraction of a day's volume)."""
    if df.empty:
        return df
    now = pd.Timestamp.now(tz="UTC")
    return df[df.index + pd.to_timedelta(timeframe) <= now]


def crypto_ohlcv(symbol: str, timeframe: str, limit: int = 400, ex=None) -> pd.DataFrame:
    ex = ex or _exchange()
    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["ts", *COLS])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return closed_bars(df.set_index("ts"), timeframe)


def crypto_history(symbol: str, timeframe: str, days: int, ex=None) -> pd.DataFrame:
    """Paged history for backtests. Kraken's OHLC endpoint only returns the latest 720
    bars whatever `since` says, so this uses backtest.history_exchange (Coinbase by default)."""
    import ccxt
    ex = ex or getattr(ccxt, CFG["backtest"]["history_exchange"])({"enableRateLimit": True})
    step = int(pd.to_timedelta(timeframe).total_seconds() * 1000)
    now = int(pd.Timestamp.now(tz="UTC").timestamp() * 1000)
    since, frames = now - days * 86_400_000, []
    while since < now:
        raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=300)
        # Empty page = symbol not listed yet at `since`; skip ahead rather than stop.
        since = raw[-1][0] + step if raw else since + 300 * step
        frames += raw
    df = pd.DataFrame(frames, columns=["ts", *COLS])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return closed_bars(df.drop_duplicates("ts").set_index("ts").sort_index(), timeframe)


# ---------------------------------------------------------------- stocks
def stock_universe() -> list[str]:
    p = ROOT / CFG["universe"]["stocks"]["tickers_file"]
    if not p.exists():
        return []
    return [l.strip().upper() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]


def stock_ohlcv(symbol: str, timeframe: str, limit: int = 400) -> pd.DataFrame:
    import yfinance as yf
    period = "2y" if timeframe == "1d" else "60d"   # yfinance caps intraday history
    df = yf.download(symbol, period=period, interval=timeframe, progress=False, auto_adjust=True)
    if df.empty:
        return pd.DataFrame(columns=COLS)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[COLS]
    df.index = pd.to_datetime(df.index, utc=True)
    return closed_bars(df, timeframe).tail(limit)


# ---------------------------------------------------------------- unified
def ohlcv(symbol: str, asset_class: str, timeframe: str, limit: int = 400, ex=None) -> pd.DataFrame:
    if asset_class == "crypto":
        return crypto_ohlcv(symbol, timeframe, limit, ex)
    return stock_ohlcv(symbol, timeframe, limit)


def load_csv(path: str | Path) -> pd.DataFrame:
    """For backtests and tests: CSV with ts,open,high,low,close,volume."""
    df = pd.read_csv(path, parse_dates=["ts"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df.set_index("ts")[COLS]
