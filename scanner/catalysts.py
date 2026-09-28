"""Module 1 — catalyst calendar. Pulls scheduled events for the next N days and stores them.

Sources (all optional; each one is skipped if its key or endpoint is unavailable):
  - CoinMarketCal API   (crypto events; needs COINMARKETCAL_KEY)
  - DefiLlama unlocks   (public JSON; token unlocks -> bearish lean)
  - yfinance            (stock earnings dates -> binary)
Extend by adding a fetch_* function that returns rows in the common shape.
"""
from __future__ import annotations
from datetime import date, timedelta
import requests
from .config import CFG, env
from . import data
from .db import Store

LOOKAHEAD = CFG["catalysts"]["lookahead_days"]


def _window():
    today = date.today()
    return today, today + timedelta(days=LOOKAHEAD)


def fetch_coinmarketcal() -> list[dict]:
    key = env("COINMARKETCAL_KEY")
    if not key:
        return []
    start, end = _window()
    r = requests.get(
        "https://developers.coinmarketcal.com/v1/events",
        headers={"x-api-key": key, "Accept": "application/json"},
        params={"dateRangeStart": start.isoformat(), "dateRangeEnd": end.isoformat(), "max": 75, "sortBy": "hot_events"},
        timeout=20,
    )
    r.raise_for_status()
    rows = []
    for ev in r.json().get("body", []):
        for coin in ev.get("coins", []):
            title = (ev.get("title") or {}).get("en", "")
            cats = [c.get("name", "").lower() for c in ev.get("categories", [])]
            etype = "listing" if "exchange" in " ".join(cats) else "mainnet" if "release" in " ".join(cats) else "other"
            rows.append({
                "symbol": f"{coin.get('symbol')}/USD", "asset_class": "crypto",
                "event_date": (ev.get("date_event") or "")[:10], "event_type": etype,
                "lean": "bullish" if etype in ("listing", "mainnet") else "binary",
                "title": title, "source": "coinmarketcal", "source_url": ev.get("source"),
            })
    return rows


def fetch_defillama_unlocks() -> list[dict]:
    try:
        r = requests.get("https://api.llama.fi/emissions", timeout=20)
        r.raise_for_status()
    except Exception:
        return []
    start, end = _window()
    rows = []
    for p in r.json() if isinstance(r.json(), list) else []:
        for ev in p.get("events", []) or []:
            ts = ev.get("timestamp")
            if not ts:
                continue
            d = date.fromtimestamp(ts)
            if start <= d <= end and (ev.get("noOfTokens") or [0])[0] > 0:
                rows.append({
                    "symbol": f"{(p.get('token') or p.get('name') or '').upper()}/USD", "asset_class": "crypto",
                    "event_date": d.isoformat(), "event_type": "unlock", "lean": "bearish",
                    "title": f"Token unlock: {ev.get('description') or ''}".strip(),
                    "source": "defillama", "source_url": "https://defillama.com/unlocks",
                })
    return rows


def fetch_stock_earnings() -> list[dict]:
    if not CFG["universe"]["stocks"]["enabled"]:
        return []
    import yfinance as yf
    start, end = _window()
    rows = []
    for t in data.stock_universe():
        try:
            cal = yf.Ticker(t).calendar
            d = cal.get("Earnings Date") if isinstance(cal, dict) else None
            d = d[0] if isinstance(d, (list, tuple)) and d else d
            if d and start <= d <= end:
                rows.append({"symbol": t, "asset_class": "stock", "event_date": d.isoformat(),
                             "event_type": "earnings", "lean": "binary", "title": f"{t} earnings",
                             "source": "yfinance", "source_url": f"https://finance.yahoo.com/quote/{t}"})
        except Exception:
            pass
    return rows


def main():
    store = Store()
    rows = fetch_coinmarketcal() + fetch_defillama_unlocks() + fetch_stock_earnings()
    for r in rows:
        if r.get("event_date"):
            store.upsert("catalysts", r, on_conflict="symbol,event_date,event_type")
    print(f"catalysts: {len(rows)} rows")
    return rows


if __name__ == "__main__":
    main()
