"""Module 1 — exchange-listing watcher. Run every 5 minutes from the scan workflow.

  python -m scanner.listings                    # poll, store, notify, put fresh listings in play
  python -m scanner.listings --dry-run --days 7 # what it would have caught (no writes, no Telegram)

Sources (each skipped on failure, so one blocked site never stops the others):
  upbit     api-manager.upbit.com announcements, "trade" category. Listing titles say
            "신규 거래지원" (new trading support) or "디지털 자산 추가" (digital asset added);
            "거래지원 종료" (delisting) and "유의" (warning) notices are ignored.
  bithumb   api.bithumb.com/v1/notices, titles with "마켓 추가" / "신규 거래지원".
  binance   CMS "New Cryptocurrency Listing" catalog: "Will List X (TICKER)" spot listings and
            single-coin "XXXUSDT Perpetual" launches. Stocks/TradFi/collateral/Earn notices skipped.
  coinbase  Advanced Trade products' `new_at` (when a product went live). @CoinbaseAssets on X
            needs a paid API and the blog is behind a bot check, so this is the stand-in.

Each announcement and ticker becomes one catalysts row (event_type "listing") with the price
just before the announcement and at +1h/+24h, from Coinbase (else Kraken). A fresh one
(announced within listings.max_age_hours) on a coin tradeable on Coinbase Advanced also gets
a one-line Telegram notice and an in_play row (source "listing", Coinbase prices), so Stage B
watches it for a pullback entry under the normal rules. The same exchange announcing the same
coin again within listings.dedupe_days is ignored.
"""
from __future__ import annotations
import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import requests
from .config import CFG
from . import data
from .db import Store
from . import alerts as notify

L = CFG["listings"]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36",
      "Accept": "application/json"}
MARKETS = {"KRW", "BTC", "USDT", "USDC", "USD", "ETH"}   # quote markets named in titles, not listed coins
NAMES = {"upbit": "Upbit", "bithumb": "Bithumb", "binance": "Binance", "coinbase": "Coinbase"}
_primary = None


def _ex(ex_id: str):
    """ccxt exchange by id, created once per run (the configured exchange included)."""
    global _primary
    if ex_id != CFG["universe"]["crypto"]["exchange"]:
        return data.exchange_for(ex_id)
    if _primary is None:
        _primary = data._exchange()
    return _primary


@dataclass
class Announcement:
    source: str
    source_id: str
    title: str
    tickers: list[str]
    announced_at: pd.Timestamp
    url: str


# ------------------------------------------------------------------ parsing (pure)
def _paren_tickers(title: str) -> list[str]:
    """Tickers in parentheses: "뉴메레르(NMR)", "(BICO, BMT, NIL, GWEI)". Quote markets dropped."""
    out = []
    for group in re.findall(r"\(([^()]*)\)", title):
        for tok in (t.strip() for t in group.split(",")):
            if re.fullmatch(r"[A-Z0-9]{2,15}", tok) and tok not in MARKETS and tok not in out:
                out.append(tok)
    return out


def is_listing(source: str, title: str) -> bool:
    if source == "upbit":
        return ("신규 거래지원" in title or "디지털 자산 추가" in title) and "종료" not in title
    if source == "bithumb":
        return ("마켓 추가" in title or "신규 거래지원" in title) and "종료" not in title and "유의" not in title
    if source == "binance":
        if re.search(r"bStocks|TradFi|Pre-IPO|Quanto|Collateral|Stocks|Multiple|Margin Will Add|on Earn", title):
            return False
        return "Will List" in title or bool(re.search(r"Perpetual Contract", title))
    return True


def parse_tickers(source: str, title: str) -> list[str]:
    if not is_listing(source, title):
        return []
    if source == "binance" and "Will List" not in title:
        m = re.findall(r"\b([A-Z0-9]{2,15})USDT\b", title)
        return list(dict.fromkeys(m))
    return _paren_tickers(title)


# ------------------------------------------------------------------ sources
def fetch_upbit(pages: int = 1) -> list[Announcement]:
    out = []
    for page in range(1, pages + 1):
        r = requests.get("https://api-manager.upbit.com/api/v1/announcements",
                         params={"os": "web", "page": page, "per_page": 20, "category": "trade"}, headers=UA, timeout=15)
        r.raise_for_status()
        for n in r.json()["data"]["notices"]:
            out.append(Announcement("upbit", str(n["id"]), n["title"], parse_tickers("upbit", n["title"]),
                                    pd.Timestamp(n.get("first_listed_at") or n["listed_at"]).tz_convert("UTC"),
                                    f"https://upbit.com/service_center/notice?id={n['id']}"))
    return out


def fetch_bithumb(pages: int = 1) -> list[Announcement]:
    r = requests.get("https://api.bithumb.com/v1/notices", params={"count": 20 * pages}, headers=UA, timeout=15)
    r.raise_for_status()
    body = r.json()
    items = body if isinstance(body, list) else body.get("data") or []
    out = []
    for n in items:
        title = n.get("title") or ""
        ts = n.get("published_at") or n.get("created_at") or n.get("modified_at")
        if not ts:
            continue
        t = pd.Timestamp(ts)
        t = t.tz_localize("Asia/Seoul") if t.tzinfo is None else t
        url = n.get("pc_url") or n.get("url") or "https://feed.bithumb.com/notice"
        out.append(Announcement("bithumb", str(n.get("id") or url), title, parse_tickers("bithumb", title),
                                t.tz_convert("UTC"), url))
    return out


def fetch_binance(pages: int = 1) -> list[Announcement]:
    out = []
    for page in range(1, pages + 1):
        r = requests.get("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
                         params={"type": 1, "catalogId": 48, "pageNo": page, "pageSize": 20}, headers=UA, timeout=15)
        r.raise_for_status()
        for a in r.json()["data"]["catalogs"][0]["articles"]:
            out.append(Announcement("binance", a["code"], a["title"], parse_tickers("binance", a["title"]),
                                    pd.Timestamp(a["releaseDate"], unit="ms", tz="UTC"),
                                    f"https://www.binance.com/en/support/announcement/{a['code']}"))
    return out


def fetch_coinbase(pages: int = 1) -> list[Announcement]:
    r = requests.get("https://api.coinbase.com/api/v3/brokerage/market/products",
                     params={"product_type": "SPOT"}, headers=UA, timeout=20)
    r.raise_for_status()
    seen, out = set(), []
    for p in r.json()["products"]:
        base, new_at = p.get("base_currency_id"), p.get("new_at")
        if not new_at or p.get("quote_currency_id") not in ("USD", "USDC") or base in seen:
            continue
        seen.add(base)
        out.append(Announcement("coinbase", f"{base}-{new_at}", f"{p.get('base_name') or base} ({base}) live on Coinbase Advanced",
                                [base], pd.Timestamp(new_at).tz_convert("UTC"),
                                f"https://www.coinbase.com/advanced-trade/spot/{base}-USD"))
    return out


FETCHERS = {"upbit": fetch_upbit, "bithumb": fetch_bithumb, "binance": fetch_binance, "coinbase": fetch_coinbase}


def trading_open(source: str, ticker: str, title: str = "") -> bool | None:
    """Has trading started on the announcing exchange? None = couldn't tell."""
    try:
        if source == "binance" and "Perpetual" in title:   # futures listing: the spot book may not exist
            r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
            return any(x["symbol"] == f"{ticker}USDT" and x["status"] == "TRADING" for x in r.json()["symbols"])
        if source == "upbit":
            r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": f"KRW-{ticker}"}, timeout=10)
            if r.status_code != 200:   # no KRW market (yet): try the USDT/BTC books
                r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": f"USDT-{ticker}"}, timeout=10)
            return r.status_code == 200 and (r.json()[0].get("acc_trade_volume_24h") or 0) > 0
        if source == "bithumb":
            r = requests.get(f"https://api.bithumb.com/public/ticker/{ticker}_KRW", timeout=10).json()
            return r.get("status") == "0000" and float(r["data"].get("units_traded_24H") or 0) > 0
        if source == "binance":
            r = requests.get("https://data-api.binance.vision/api/v3/exchangeInfo", params={"symbol": f"{ticker}USDT"}, timeout=10)
            return r.status_code == 200 and r.json()["symbols"][0]["status"] == "TRADING"
        if source == "coinbase":
            p = _ex("coinbase").markets[f"{ticker}/USD"]["info"]
            return p.get("status") == "online" and not (p.get("trading_disabled") or p.get("auction_mode") or p.get("cancel_only"))
    except Exception as e:
        print(f"[listings] {source} {ticker} open check: {e}")
    return None


# ------------------------------------------------------------------ prices
def price_source(ticker: str):
    """(exchange id, ccxt exchange, symbol) for USD prices: Coinbase first, else Kraken, else None."""
    for ex_id in ("coinbase", CFG["universe"]["crypto"]["exchange"]):
        try:
            ex = _ex(ex_id)
            if f"{ticker}/USD" in ex.markets:
                return ex_id, ex, f"{ticker}/USD"
        except Exception as e:
            print(f"[listings] {ex_id} markets: {e}")
    return None


def price_before(ex, symbol: str, ts: pd.Timestamp) -> float | None:
    """Close of the last 1m bar that closed at or before ts (hourly bars as a fallback)."""
    for tf, back in (("1m", 240), ("1h", 48)):
        step = pd.to_timedelta(tf)
        raw = ex.fetch_ohlcv(symbol, timeframe=tf, since=int((ts - back * step).timestamp() * 1000), limit=300)
        done = [b for b in raw if pd.Timestamp(b[0], unit="ms", tz="UTC") + step <= ts]
        if done:
            return float(done[-1][4])
    return None


def high_since(ex, symbol: str, ts: pd.Timestamp) -> float | None:
    raw = ex.fetch_ohlcv(symbol, timeframe="1h", since=int(ts.floor("h").timestamp() * 1000), limit=300)
    return max((float(b[2]) for b in raw), default=None)


# ------------------------------------------------------------------ run
def _fmt_time(ts: pd.Timestamp) -> str:
    return ts.tz_convert(ZoneInfo(CFG["alerts"]["timezone"])).strftime("%-d %b %H:%M %Z")


def format_listing(row: dict, is_open: bool | None) -> str:
    pre, now = row.get("price_pre"), row.get("price_detect")
    px = f"price at announcement ${pre:.4g}" if pre else "price at announcement –"
    if pre and now:
        px += f", now ${now:.4g} ({(now / pre - 1) * 100:+.0f}%)"
    opened = {True: "yes", False: "not yet", None: "unknown"}[is_open]
    src = NAMES[row["source"]]
    return (f"*LISTING — {row['symbol'].split('/')[0]}* on {src} · announced {_fmt_time(pd.Timestamp(row['announced_at']))} · "
            f"{px} · trading open on {src}: {opened}. Watching for a pullback.")


def _recent(store: Store, days: int, now: pd.Timestamp) -> set[tuple[str, str]]:
    cut = now - pd.Timedelta(days=days)
    return {(r["source"], r["symbol"]) for r in store.select("catalysts", event_type="listing")
            if r.get("announced_at") and pd.Timestamp(r["announced_at"]) >= cut}


def record(store: Store | None, a: Announcement, ticker: str, now: pd.Timestamp, fresh: bool,
           notify_fresh: bool = True) -> dict:
    """Build (and unless store is None, save) the catalysts row for one listing; for a fresh
    one on a Coinbase-tradeable coin, also notify and put it in play."""
    row = {"symbol": f"{ticker}/USD", "asset_class": "crypto", "event_date": a.announced_at.strftime("%Y-%m-%d"),
           "event_type": "listing", "lean": "bullish", "title": a.title[:300], "source": a.source,
           "source_url": a.url, "source_id": a.source_id, "announced_at": a.announced_at.isoformat(),
           "detected_at": now.isoformat(), "coinbase_tradeable": f"{ticker}/USD" in _ex("coinbase").markets,
           "price_source": None, "price_pre": None, "price_detect": None, "notified": False}
    ps = price_source(ticker)
    if ps:
        ex_id, ex, sym = ps
        row["price_source"] = ex_id
        try:
            row["price_pre"] = price_before(ex, sym, a.announced_at)
            row["price_detect"] = float(ex.fetch_ticker(sym)["last"])
        except Exception as e:
            print(f"[listings] {sym} price: {e}")
    act = fresh and row["coinbase_tradeable"]
    is_open = trading_open(a.source, ticker, a.title) if act else None
    if store is None:
        return {**row, "trading_open": is_open}
    row["trading_open"] = is_open
    if act and notify_fresh:
        notify.send(format_listing(row, is_open))
        row["notified"] = True
    store.upsert("catalysts", row, on_conflict="symbol,event_date,event_type,source")
    if act and row["price_pre"]:
        _put_in_play(store, row)
    return row


def _put_in_play(store: Store, row: dict) -> None:
    """in_play for the normal Stage B rules: the "breakout level" and impulse low are the
    pre-announcement price, the impulse high is the high since the announcement."""
    sym, day = row["symbol"], row["event_date"]
    if any(r["symbol"] == sym for r in store.watching()) or store.select("in_play", symbol=sym, breakout_date=day):
        print(f"[listings] {sym} already in play, not added")
        return
    cb = _ex("coinbase")
    t0 = pd.Timestamp(row["announced_at"])
    hi = max(x for x in (high_since(cb, sym, t0), row["price_detect"], row["price_pre"]) if x)
    store.upsert("in_play", {
        "symbol": sym, "asset_class": "crypto", "breakout_date": day,
        "breakout_level": row["price_pre"], "impulse_low": row["price_pre"], "impulse_high": hi,
        "impulse_volume": 0.0, "status": "watching", "late": False, "exchange": "coinbase", "source": "listing",
    }, on_conflict="symbol,breakout_date")


def fill_followups(store: Store, now: pd.Timestamp) -> int:
    """price_1h / price_24h for stored listings once those times have passed."""
    n = 0
    for r in store.select("catalysts", event_type="listing"):
        if not r.get("price_source") or not r.get("announced_at"):
            continue
        t0 = pd.Timestamp(r["announced_at"])
        patch = {}
        for col, h in (("price_1h", 1), ("price_24h", 24)):
            if r.get(col) is None and now >= t0 + pd.Timedelta(hours=h, minutes=2):
                try:
                    ex = _ex(r["price_source"])
                    patch[col] = price_before(ex, r["symbol"], t0 + pd.Timedelta(hours=h))
                except Exception as e:
                    print(f"[listings] {r['symbol']} {col}: {e}")
        if any(v is not None for v in patch.values()):
            store.update("catalysts", r["id"], {k: v for k, v in patch.items() if v is not None}); n += 1
    return n


def poll(pages: int = 1) -> list[Announcement]:
    out = []
    for src in L["sources"]:
        try:
            got = FETCHERS[src](pages)
            print(f"[listings] {src}: {len(got)} notices, {sum(bool(a.tickers) for a in got)} listings")
            out += got
        except Exception as e:   # blocked / changed site: the other sources still run
            print(f"[listings] {src}: {e}")
    return out


def run(store: Store, now: pd.Timestamp | None = None) -> int:
    now = now or pd.Timestamp.now(tz="UTC")
    seen = _recent(store, L["dedupe_days"], now)
    excl = set(CFG["universe"]["crypto"]["exclude"]) | set(L["exclude"])
    new = 0
    for a in sorted(poll(), key=lambda a: a.announced_at):
        if now - a.announced_at > pd.Timedelta(days=L["dedupe_days"]):
            continue
        for t in a.tickers:
            if t in excl or (a.source, f"{t}/USD") in seen:
                continue
            fresh = now - a.announced_at <= pd.Timedelta(hours=L["max_age_hours"])
            try:
                record(store, a, t, now, fresh)
                seen.add((a.source, f"{t}/USD")); new += 1
            except Exception as e:
                print(f"[listings] {a.source} {t}: {e}")
    filled = fill_followups(store, now)
    print(f"listings: {new} new, {filled} follow-up prices filled")
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print what would be caught; no writes, no Telegram")
    ap.add_argument("--days", type=int, default=7, help="dry run: look back this many days")
    args = ap.parse_args()
    if not args.dry_run:
        run(Store()); return
    now = pd.Timestamp.now(tz="UTC")
    excl = set(CFG["universe"]["crypto"]["exclude"]) | set(L["exclude"])
    seen = set()
    for a in sorted(poll(pages=3), key=lambda a: a.announced_at):
        if now - a.announced_at > pd.Timedelta(days=args.days):
            continue
        for t in a.tickers:
            if t in excl or (a.source, t) in seen:
                continue
            seen.add((a.source, t))
            r = record(None, a, t, now, fresh=True)
            ps = r["price_source"]
            ex = _ex(ps) if ps else None
            p1 = price_before(ex, r["symbol"], a.announced_at + pd.Timedelta(hours=1)) if ex and now > a.announced_at + pd.Timedelta(hours=1) else None
            p24 = price_before(ex, r["symbol"], a.announced_at + pd.Timedelta(hours=24)) if ex and now > a.announced_at + pd.Timedelta(hours=24) else None
            pct = lambda p: f"{(p / r['price_pre'] - 1) * 100:+.1f}%" if p and r["price_pre"] else "–"
            print(f"{a.announced_at:%Y-%m-%d %H:%M}Z  {NAMES[a.source]:<8} {t:<8} coinbase={'Y' if r['coinbase_tradeable'] else 'n'} "
                  f"open={r['trading_open']}  pre={r['price_pre']} ({ps})  +1h {pct(p1)}  +24h {pct(p24)}  | {a.title[:80]}")


if __name__ == "__main__":
    main()
