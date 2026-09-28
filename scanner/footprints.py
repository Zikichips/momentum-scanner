"""Module 2 — footprint screener. Flags assets with unusual activity and no obvious news.

Signal 1: volume >= N x 30-day average while |24h move| < X%  (quiet accumulation)
Signal 2: (crypto futures) open interest up >= Y% while price flat        (positioning)
Each flag is checked against CryptoPanic / NewsAPI; unexplained flags score higher.
"""
from __future__ import annotations
from datetime import datetime, timezone
import requests
from .config import CFG, env
from . import data
from .indicators import volume_avg
from .db import Store

F = CFG["footprints"]


def has_news(symbol: str) -> tuple[bool, str | None]:
    base = symbol.split("/")[0]
    tok = env("CRYPTOPANIC_TOKEN")
    if tok:
        try:
            r = requests.get("https://cryptopanic.com/api/v1/posts/",
                             params={"auth_token": tok, "currencies": base, "filter": "hot"}, timeout=15)
            posts = r.json().get("results", [])
            if posts:
                return True, posts[0].get("title")
        except Exception:
            pass
    key = env("NEWSAPI_KEY")
    if key:
        try:
            r = requests.get("https://newsapi.org/v2/everything",
                             params={"q": base, "sortBy": "publishedAt", "pageSize": 1, "apiKey": key}, timeout=15)
            arts = r.json().get("articles", [])
            if arts:
                return True, arts[0].get("title")
        except Exception:
            pass
    return False, None


def open_interest_change(symbol: str) -> float | None:
    """Binance USDT-perp OI change over 24h, % (best-effort; None if unavailable)."""
    base = symbol.split("/")[0]
    try:
        r = requests.get("https://fapi.binance.com/futures/data/openInterestHist",
                         params={"symbol": f"{base}USDT", "period": "1d", "limit": 2}, timeout=15)
        d = r.json()
        if len(d) == 2:
            a, b = float(d[0]["sumOpenInterestValue"]), float(d[1]["sumOpenInterestValue"])
            return round((b / a - 1) * 100, 2) if a else None
    except Exception:
        return None
    return None


def screen() -> list[dict]:
    store = Store()
    rows = []
    ex = data._exchange()
    for sym in data.crypto_universe(ex):
        try:
            daily = data.crypto_ohlcv(sym, "1d", limit=40, ex=ex)
            if len(daily) < 32:
                continue
            last = daily.iloc[-1]
            vavg = float(volume_avg(daily["volume"], 30).iloc[-1])
            vmult = float(last["volume"]) / vavg if vavg else 0
            move = (float(last["close"]) / float(daily["close"].iloc[-2]) - 1) * 100
            oi = open_interest_change(sym)
            quiet_vol = vmult >= F["volume_multiple"] and abs(move) < F["max_abs_move_pct"]
            quiet_oi = oi is not None and oi >= F["oi_change_pct_min"] and abs(move) < F["max_abs_move_pct"]
            if not (quiet_vol or quiet_oi):
                continue
            news, headline = has_news(sym)
            score = (vmult if quiet_vol else 0) + ((oi or 0) / 10 if quiet_oi else 0)
            if not news:
                score *= 1.5
            row = {"symbol": sym, "asset_class": "crypto", "observed_at": datetime.now(timezone.utc),
                   "volume_multiple": round(vmult, 2), "move_pct": round(move, 2), "oi_change_pct": oi,
                   "has_news": news, "news_headline": headline, "score": round(score, 2)}
            store.insert("footprints", row)
            rows.append(row)
        except Exception as e:
            print(f"[footprints] {sym}: {e}")
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:10]


if __name__ == "__main__":
    for r in screen():
        print(r)
