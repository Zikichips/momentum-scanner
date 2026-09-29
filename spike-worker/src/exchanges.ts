// Kraken and Coinbase public market data (no keys). Parsers are pure and exported for tests.
import { EXCLUDE_BASES } from "./config";
import type { Candle, Exchange } from "./rules";

const KRAKEN = "https://api.kraken.com/0/public";
const COINBASE = "https://api.coinbase.com/api/v3/brokerage/market";
const TIMEOUT = 8000;

async function getJson(url: string): Promise<any> {
  const r = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT), headers: { "User-Agent": "spike-detector" } });
  if (!r.ok) throw new Error(`${r.status} ${url.slice(0, 120)}`);
  return r.json();
}

// Kraken's legacy asset codes -> common tickers.
const KRAKEN_ALIASES: Record<string, string> = { XBT: "BTC", XDG: "DOGE" };
export const normBase = (b: string) => KRAKEN_ALIASES[b] ?? b;

export interface Quote { price: number; qvol24: number; bid: number; ask: number }
export interface UniverseEntry { base: string; exchange: Exchange; id: string; qvol24: number }

// ------------------------------------------------------------------ universe (daily, one payload per step)
/** AssetPairs -> {tickerKey: base} for online USD-quoted spot pairs. */
export function parseKrakenPairs(json: any): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, v] of Object.entries<any>(json.result ?? {})) {
    if (v.status !== "online" || !(v.quote === "ZUSD" || v.quote === "USD") || !v.wsname || key.includes(".")) continue;
    const base = normBase(String(v.wsname).split("/")[0]);
    if (!EXCLUDE_BASES.has(base)) out[key] = base;
  }
  return out;
}

/** Ticker (all pairs) -> entries for the pairs we kept, with 24h quote volume = 24h base volume × 24h VWAP. */
export function parseKrakenTickerAll(json: any, pairs: Record<string, string>): UniverseEntry[] {
  const out: UniverseEntry[] = [];
  for (const [key, t] of Object.entries<any>(json.result ?? {})) {
    const base = pairs[key];
    if (!base) continue;
    out.push({ base, exchange: "kraken", id: key, qvol24: parseFloat(t.v[1]) * parseFloat(t.p[1]) });
  }
  return out;
}

/** One page of Coinbase products -> USD spot entries. BASE-USDC books are skipped (Coinbase shows them as USD too). */
export function parseCoinbasePage(json: any): UniverseEntry[] {
  const out: UniverseEntry[] = [];
  for (const p of json.products ?? []) {
    if (!String(p.product_id).endsWith("-USD") || p.product_type !== "SPOT" || p.status !== "online"
        || p.trading_disabled || p.is_disabled || p.view_only) continue;
    const base = String(p.base_display_symbol || p.product_id.split("-")[0]).toUpperCase();
    if (EXCLUDE_BASES.has(base)) continue;
    out.push({ base, exchange: "coinbase", id: p.product_id, qvol24: parseFloat(p.approximate_quote_24h_volume || "0") });
  }
  return out;
}

/** Dedupe by base, keeping the pair with the higher 24h quote volume (the busier exchange
 *  gives the truer price, candles and liquidity check; Kraken wins ties). Rank by that
 *  volume and keep the top n. */
export function mergeUniverse(kraken: UniverseEntry[], coinbase: UniverseEntry[], n: number): UniverseEntry[] {
  const byBase = new Map<string, UniverseEntry>();
  for (const e of [...kraken, ...coinbase]) {
    const prev = byBase.get(e.base);
    if (!prev || e.qvol24 > prev.qvol24) byBase.set(e.base, e);
  }
  return [...byBase.values()].sort((a, b) => b.qvol24 - a.qvol24).slice(0, n);
}

export const fetchKrakenPairs = async () => parseKrakenPairs(await getJson(`${KRAKEN}/AssetPairs`));
export const fetchKrakenTickerAll = async (pairs: Record<string, string>) => parseKrakenTickerAll(await getJson(`${KRAKEN}/Ticker`), pairs);
export const COINBASE_PAGE = 250;
export const fetchCoinbasePage = async (offset: number) => {
  const json = await getJson(`${COINBASE}/products?product_type=SPOT&limit=${COINBASE_PAGE}&offset=${offset}`);
  return { entries: parseCoinbasePage(json), last: (json.products ?? []).length < COINBASE_PAGE };
};

// ------------------------------------------------------------------ per-minute quotes (universe only)
export function parseKrakenTicker(json: any, keyToBase: Record<string, string>): Record<string, Quote> {
  const out: Record<string, Quote> = {};
  for (const [key, t] of Object.entries<any>(json.result ?? {})) {
    const base = keyToBase[key];
    if (base) out[base] = { price: parseFloat(t.c[0]), qvol24: parseFloat(t.v[1]) * parseFloat(t.p[1]),
                            bid: parseFloat(t.b[0]), ask: parseFloat(t.a[0]) };
  }
  return out;
}

export function parseCoinbaseProducts(json: any): Record<string, Quote> {
  const out: Record<string, Quote> = {};
  for (const p of json.products ?? []) {
    const base = String(p.product_id).split("-")[0];
    out[base] = { price: parseFloat(p.price), qvol24: parseFloat(p.approximate_quote_24h_volume || "0"),
                  bid: parseFloat(p.best_bid_price || "NaN"), ask: parseFloat(p.best_ask_price || "NaN") };
  }
  return out;
}

/** Current price + 24h quote volume for every universe entry: one Kraken call, one Coinbase call. */
export async function fetchQuotes(universe: UniverseEntry[]): Promise<Record<string, Quote>> {
  const kr = universe.filter(e => e.exchange === "kraken");
  const cb = universe.filter(e => e.exchange === "coinbase");
  const [k, c] = await Promise.allSettled([
    kr.length ? getJson(`${KRAKEN}/Ticker?pair=${kr.map(e => e.id).join(",")}`) : Promise.resolve({ result: {} }),
    cb.length ? getJson(`${COINBASE}/products?limit=${cb.length}&${cb.map(e => `product_ids=${e.id}`).join("&")}`) : Promise.resolve({ products: [] }),
  ]);
  const out: Record<string, Quote> = {};
  if (k.status === "fulfilled") Object.assign(out, parseKrakenTicker(k.value, Object.fromEntries(kr.map(e => [e.id, e.base]))));
  else console.log("kraken ticker failed:", String(k.reason));
  if (c.status === "fulfilled") {
    const want = new Set(cb.map(e => e.base));
    for (const [b, q] of Object.entries(parseCoinbaseProducts(c.value))) if (want.has(b)) out[b] = q;
  } else console.log("coinbase products failed:", String(c.reason));
  return out;
}

// ------------------------------------------------------------------ candles
export function parseKrakenOhlc(json: any): Candle[] {
  const key = Object.keys(json.result ?? {}).find(k => k !== "last");
  return (key ? json.result[key] : []).map((r: any[]) => ({
    t: Number(r[0]) * 1000, open: +r[1], high: +r[2], low: +r[3], close: +r[4], volume: +r[6],
  }));
}

export function parseCoinbaseCandles(json: any): Candle[] {
  return (json.candles ?? []).map((c: any) => ({
    t: Number(c.start) * 1000, open: +c.open, high: +c.high, low: +c.low, close: +c.close, volume: +c.volume,
  })).sort((a: Candle, b: Candle) => a.t - b.t);
}

const KRAKEN_INTERVAL = { 1: 1, 60: 60, 1440: 1440 } as const;
const COINBASE_GRANULARITY = { 1: "ONE_MINUTE", 60: "ONE_HOUR", 1440: "ONE_DAY" } as const;

/** Candles of `minutes` size from `since` (ms) to now. Coinbase returns at most 350 per call. */
export async function fetchCandles(e: { exchange: Exchange; id: string }, minutes: 1 | 60 | 1440, since: number): Promise<Candle[]> {
  if (e.exchange === "kraken") {
    const json = await getJson(`${KRAKEN}/OHLC?pair=${e.id}&interval=${KRAKEN_INTERVAL[minutes]}&since=${Math.floor(since / 1000)}`);
    if (json.error?.length) throw new Error(json.error.join(","));
    return parseKrakenOhlc(json).filter(c => c.t >= since);
  }
  const start = Math.floor(since / 1000);
  const end = Math.min(Math.floor(Date.now() / 1000), start + 349 * minutes * 60);
  return parseCoinbaseCandles(await getJson(
    `${COINBASE}/products/${e.id}/candles?granularity=${COINBASE_GRANULARITY[minutes]}&start=${start}&end=${end}`));
}
