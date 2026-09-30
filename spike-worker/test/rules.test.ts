import { describe, expect, it } from "vitest";
import {
  EARLY_RULE, evaluateSpike, formatAlert, formatEarlyAlert, formatMicroAlert, gradePath, levels, liquidityLabel, positionSize, scoreboard, tradeCost, type Candle,
} from "../src/rules";
import {
  mergeUniverse, parseCoinbaseCandles, parseCoinbasePage, parseKrakenOhlc, parseKrakenPairs, parseKrakenTicker,
  parseKrakenTickerAll,
} from "../src/exchanges";

const NOW = Date.UTC(2026, 8, 28, 12, 0);
const MIN = 60_000;

/** 31 one-minute candles ending at NOW, price rising linearly from `from` to `to`, `vol` per bar. */
function ramp(from: number, to: number, vol: number): Candle[] {
  return Array.from({ length: 31 }, (_, i) => {
    const p = from + (to - from) * (i / 30);
    return { t: NOW - (30 - i) * MIN, open: p, high: p * 1.001, low: p * 0.999, close: p, volume: vol };
  });
}

describe("evaluateSpike", () => {
  // Baseline 4,800/day -> 100 per 30 min; 31 bars × 20 = 620 -> 6.2×.
  it("fires when all three conditions hold", () => {
    const r = evaluateSpike(ramp(100, 120, 20), 120, 4800, NOW);
    expect(r.ok).toBe(true);
    expect(r.move).toBeCloseTo(0.2, 3);
    expect(r.volMultiple).toBeGreaterThanOrEqual(5);
  });
  it("rejects a move under 15%", () => {
    const r = evaluateSpike(ramp(100, 110, 20), 110, 4800, NOW);
    expect(r.ok).toBe(false);
    expect(r.reasons[0]).toMatch(/^move/);
  });
  it("rejects volume under 5× the 30-min baseline", () => {
    expect(evaluateSpike(ramp(100, 120, 10), 120, 4800, NOW).reasons).toEqual([expect.stringMatching(/^vol/)]);
  });
  it("rejects a price already off the 30-min high", () => {
    const c = ramp(100, 120, 20);
    c[25].high = 130;                                   // spiked to 130, now 120 = 7.7% below
    expect(evaluateSpike(c, 120, 4800, NOW).reasons).toEqual([expect.stringMatching(/^off high/)]);
  });
  it("needs a baseline", () => {
    expect(evaluateSpike(ramp(100, 120, 20), 120, 0, NOW).ok).toBe(false);
  });
});

describe("evaluateSpike, early rule (15 min)", () => {
  // Baseline 4,800/day -> 50 per 15 min; 16 bars × 20 = 320 -> 6.4×.
  it("fires on +8% in 15 minutes, below the 30-minute spike threshold", () => {
    const c = ramp(100, 112, 20);                        // +12% in 30 min: no spike
    expect(evaluateSpike(c, 112, 4800, NOW).ok).toBe(false);
    const r = evaluateSpike(c, 112, 4800, NOW, EARLY_RULE);   // 15 min ago: 106 -> +5.7%
    expect(r.reasons).toEqual([expect.stringMatching(/^move/)]);
    const fast = ramp(100, 120, 20);                     // 15 min ago: 110 -> +9.1%
    const f = evaluateSpike(fast, 120, 4800, NOW, EARLY_RULE);
    expect(f.ok).toBe(true);
    expect(f.priceAgo).toBeCloseTo(110, 6);
    expect(f.volMultiple).toBeCloseTo(6.4, 6);
  });
  it("measures volume against the 15-minute share of the daily baseline", () => {
    expect(evaluateSpike(ramp(100, 120, 10), 120, 4800, NOW, EARLY_RULE).reasons).toEqual([expect.stringMatching(/^vol 3\.2x/)]);
  });
  it("rejects a window that starts more than 3 minutes late", () => {
    const c = ramp(100, 120, 20).filter(x => x.t >= NOW - 11 * MIN);
    expect(evaluateSpike(c, 120, 4800, NOW, EARLY_RULE).reasons).toEqual(["window starts late"]);
  });
});

describe("levels and sizing", () => {
  it("stop is the nearer of the pre-spike price and −13%", () => {
    expect(levels(120, 100).stop).toBeCloseTo(104.4, 6);       // 120 × 0.87 > 100
    expect(levels(120, 110).stop).toBe(110);                   // pre-spike price is nearer
    const lv = levels(120, 110);
    expect(lv.takeProfit).toBeCloseTo(135, 6);                 // 120 + 1.5 × 10
  });
  it("matches scanner/strategy.py position_size", () => {
    expect(positionSize(100, 90, 1000, 5, 50)).toBe(500);      // $50 risk / 10% = $500, at the cap
    expect(positionSize(100, 80, 1000, 5, 50)).toBe(250);
    expect(positionSize(100, 100, 1000, 5, 50)).toBe(0);
  });
  it("labels liquidity", () => {
    expect([liquidityLabel(4e5), liquidityLabel(1.5e6), liquidityLabel(5e6), liquidityLabel(3e7)])
      .toEqual(["micro", "thin", "ok", "liquid"]);
  });
  it("estimates round-trip cost from the spread and taker fees", () => {
    // POND on Kraken, 2026-09-29: bid 0.002076 / ask 0.002112 -> 1.72% spread + 2 × 0.40%
    const k = tradeCost(0.002076, 0.002112, "kraken");
    expect(k.spreadPct).toBeCloseTo(1.719, 2);
    expect(k.costPct).toBeCloseTo(2.519, 2);
    expect(tradeCost(100, 100.1, "coinbase").costPct).toBeCloseTo(2.5, 2);   // 0.1% + 2 × 1.20%
    expect(tradeCost(NaN, NaN, "coinbase")).toEqual({ spreadPct: null, costPct: 1.5 });   // no book -> flat cost
    expect(tradeCost(101, 100, "kraken").spreadPct).toBeNull();                          // crossed book
  });
});

describe("formatAlert", () => {
  it("renders the spec's seven lines", () => {
    const text = formatAlert({
      symbol: "QNT", exchange: "kraken", move30: 0.2034, volMultiple: 6.21, price: 120.5, high: 121.3,
      chg24h: 31.2, chg7d: -4.5, liquidity: "ok", vol24h: 12_300_000, headline: null,
      reddit: { m24: 14, avg7d: 3.5 }, prior: { n: 2, avgRet60: -1.25 }, size: 461.2, lv: levels(120.5, 100),
    });
    expect(text.split("\n")).toEqual([
      "SPIKE — QNT   Kraken",
      "+20.3% in 30 min · vol 6.2× · now 120.5 (30m high 121.3)",
      "24h +31.2% · 7d −4.5% · liquidity ok ($12.3M/24h)",
      "News 6h: none",
      "Reddit: 14 vs baseline 3.5 (4.0×)",
      "Prior spikes 90d: 2 · avg +60min −1.3%",
      "Size $461 · stop 104.8 (−13.0%) · TP 144 (+19.5%)",
    ]);
  });
  it("says n/a when Reddit is off and there are no prior spikes", () => {
    const text = formatAlert({
      symbol: "X", exchange: "coinbase", move30: 0.15, volMultiple: 5, price: 1, high: 1, chg24h: null, chg7d: null,
      liquidity: "thin", vol24h: 1.2e6, headline: "Listed on Y", reddit: null, prior: { n: 0, avgRet60: null }, size: 100,
      lv: levels(1, 0.9),
    });
    expect(text).toContain("Reddit: n/a");
    expect(text).toContain("Prior spikes 90d: 0 · avg +60min n/a");
    expect(text).toContain("24h n/a% · 7d n/a%");
  });
});

describe("formatMicroAlert", () => {
  it("flags the coin as micro and shows the round-trip cost", () => {
    const text = formatMicroAlert({
      symbol: "DIMO", exchange: "coinbase", move30: 0.17792, volMultiple: 16.6, price: 0.017, high: 0.0172,
      vol24h: 870_892, costPct: 2.712, size: 250, lv: levels(0.017, 0.01443),
    });
    expect(text.split("\n")).toEqual([
      "SPIKE (MICRO) — DIMO   Coinbase",
      "+17.8% in 30 min · vol 16.6× · now 0.017 (30m high 0.0172)",
      "liquidity micro ($871k/24h) · round-trip cost ~2.7% + slippage",
      "Size $250 · stop 0.01479 (−13.0%) · TP 0.02031 (+19.5%)",
    ]);
  });
});

describe("formatEarlyAlert", () => {
  it("flags the alert as early and unconfirmed", () => {
    const text = formatEarlyAlert({
      symbol: "AVT", exchange: "coinbase", move15: 0.087, volMultiple: 6.2, price: 0.3056, high: 0.3327,
      liquidity: "thin", vol24h: 1_642_857, costPct: 2.9, size: 250, lv: levels(0.3056, 0.2811),
    });
    expect(text.split("\n")).toEqual([
      "EARLY — AVT   Coinbase",
      "+8.7% in 15 min · vol 6.2× · now 0.3056 (15m high 0.3327)",
      "liquidity thin ($1.6M/24h) · round-trip cost ~2.9%",
      "Not yet a confirmed spike (+15% in 30 min). Early alerts are scored separately.",
      "Size $250 · stop 0.2811 (−8.0%) · TP 0.3423 (+12.0%)",
    ]);
  });
});

describe("gradePath", () => {
  const fired = NOW;
  const bars = (closes: number[], hi = 0, lo = 0): Candle[] =>
    closes.map((c, i) => ({ t: fired + i * MIN, open: c, high: c + hi, low: c - lo, close: c, volume: 1 }));

  it("fills horizons that have elapsed and leaves the rest", () => {
    const p = gradePath({ firedAt: fired, price: 100, stop: 90, takeProfit: 115, costPct: 2.5 }, bars(Array(61).fill(101)), fired + 61 * MIN);
    expect(p.ret_15).toBeCloseTo(1, 6);
    expect(p.ret_60).toBeCloseTo(1, 6);
    expect(p.net_60).toBeCloseTo(-0.5, 6);
    expect(p.net_60_real).toBeCloseTo(-1.5, 6);
    expect(p.ret_240).toBeUndefined();
    expect(p.graded_complete).toBe(false);
    expect(p.hit_tp_first).toBeUndefined();              // undecided until a level is hit or 240 min pass
  });
  it("records which level was touched first", () => {
    const closes = [...Array(10).fill(105), 116, ...Array(229).fill(95)];
    const p = gradePath({ firedAt: fired, price: 100, stop: 90, takeProfit: 115 }, bars(closes), fired + 241 * MIN);
    expect([p.hit_tp_first, p.hit_stop_first, p.graded_complete]).toEqual([true, false, true]);
    expect(p.mfe_240).toBeCloseTo(16, 6);
    expect(p.mae_240).toBeCloseTo(-5, 6);
  });
  it("counts the stop first when one bar touches both", () => {
    const p = gradePath({ firedAt: fired, price: 100, stop: 90, takeProfit: 115 }, bars([100], 20, 20), fired + 2 * MIN);
    expect([p.hit_tp_first, p.hit_stop_first]).toEqual([false, true]);
  });
  it("marks neither when nothing is hit in 240 min", () => {
    const p = gradePath({ firedAt: fired, price: 100, stop: 90, takeProfit: 115 }, bars(Array(240).fill(100)), fired + 241 * MIN);
    expect([p.hit_tp_first, p.hit_stop_first, p.graded_complete]).toEqual([false, false, true]);
  });
});

describe("scoreboard", () => {
  it("splits by liquidity and news", () => {
    const row = (liquidity_label: any, has_news: boolean | null, ret_60: number, tp: boolean) => ({
      liquidity_label, has_news, ret_15: 1, ret_30: 1, ret_60, ret_240: 1, net_60: ret_60 - 1.5, hit_tp_first: tp, hit_stop_first: !tp,
    });
    const shadowRow = { ...row("micro", null, 9, true), shadow: true, net_60_real: 6 };
    const s = scoreboard("2026-09-28", [row("thin", true, 4, true), row("liquid", false, -2, false), row("liquid", null, 0, false), shadowRow]);
    const by = Object.fromEntries(s.map(r => [r.segment, r]));
    expect(by.overall.n).toBe(3);
    expect(by.overall.median_ret_60).toBe(0);
    expect(by.overall.pct_tp_first).toBeCloseTo(33.3, 1);
    expect(by["liquidity:liquid"].n).toBe(2);
    expect(by["liquidity:ok"].n).toBe(0);
    expect([by["news:yes"].n, by["news:no"].n, by["news:unknown"].n]).toEqual([1, 1, 1]);   // shadow excluded
    expect(by["liquidity:micro"].n).toBe(1);
    expect(by["liquidity:micro"].mean_net_60_real).toBe(6);
  });
  it("keeps early alerts out of the spike segments", () => {
    const row = (kind: "spike" | "early" | undefined, ret_60: number) => ({
      kind, liquidity_label: "ok" as const, has_news: false, ret_15: 1, ret_30: 1, ret_60, ret_240: 1, net_60: ret_60 - 1.5,
      hit_tp_first: false, hit_stop_first: false,
    });
    const by = Object.fromEntries(scoreboard("2026-09-30", [row(undefined, 2), row("spike", 4), row("early", -3), row("early", 5)])
      .map(r => [r.segment, r]));
    expect([by.overall.n, by["liquidity:ok"].n, by["news:no"].n, by["liquidity:micro"].n]).toEqual([2, 2, 2, 0]);
    expect(by.early.n).toBe(2);
    expect(by.early.mean_ret_60).toBe(1);
  });
});

describe("exchange parsers", () => {
  it("maps Kraken pairs to bases and skips non-USD / stablecoins", () => {
    const pairs = parseKrakenPairs({ result: {
      XXBTZUSD: { wsname: "XBT/USD", quote: "ZUSD", status: "online" },
      XDGUSD: { wsname: "XDG/USD", quote: "ZUSD", status: "online" },
      XBTPYUSD: { wsname: "XBT/PYUSD", quote: "PYUSD", status: "online" },
      USDTZUSD: { wsname: "USDT/USD", quote: "ZUSD", status: "online" },
      "XXBTZUSD.d": { wsname: "XBT/USD", quote: "ZUSD", status: "online" },
      QNTUSD: { wsname: "QNT/USD", quote: "ZUSD", status: "cancel_only" },
    } });
    expect(pairs).toEqual({ XXBTZUSD: "BTC", XDGUSD: "DOGE" });
    const t = { result: { XXBTZUSD: { c: ["100", "1"], v: ["1", "10"], p: ["99", "100"], b: ["99.9", "1", "1"], a: ["100.1", "1", "1"] } } };
    expect(parseKrakenTickerAll(t, pairs)).toEqual([{ base: "BTC", exchange: "kraken", id: "XXBTZUSD", qvol24: 1000 }]);
    expect(parseKrakenTicker(t, pairs)).toEqual({ BTC: { price: 100, qvol24: 1000, bid: 99.9, ask: 100.1 } });
  });
  it("keeps only BASE-USD Coinbase spot books", () => {
    const p = (id: string, extra = {}) => ({ product_id: id, product_type: "SPOT", status: "online", base_display_symbol: id.split("-")[0],
                                             approximate_quote_24h_volume: "5000000", ...extra });
    const out = parseCoinbasePage({ products: [p("BTC-USDC"), p("QNT-USD"), p("USDT-USD"), p("OLD-USD", { trading_disabled: true })] });
    expect(out.map(e => e.id)).toEqual(["QNT-USD"]);
  });
  it("dedupes by base keeping the busier exchange, then ranks by volume", () => {
    const k = [{ base: "BTC", exchange: "kraken" as const, id: "XXBTZUSD", qvol24: 90 },
               { base: "POND", exchange: "kraken" as const, id: "PONDUSD", qvol24: 0.3 },
               { base: "ETH", exchange: "kraken" as const, id: "XETHZUSD", qvol24: 10 }];
    const c = [{ base: "BTC", exchange: "coinbase" as const, id: "BTC-USD", qvol24: 50 },
               { base: "POND", exchange: "coinbase" as const, id: "POND-USD", qvol24: 1.2 },
               { base: "ETH", exchange: "coinbase" as const, id: "ETH-USD", qvol24: 10 },
               { base: "QNT", exchange: "coinbase" as const, id: "QNT-USD", qvol24: 7 }];
    expect(mergeUniverse(k, c, 300).map(e => `${e.exchange}:${e.base}`))
      .toEqual(["kraken:BTC", "kraken:ETH", "coinbase:QNT", "coinbase:POND"]);   // ETH tie -> Kraken
    expect(mergeUniverse(k, c, 1)).toHaveLength(1);
  });
  it("parses candles from both exchanges into the same shape", () => {
    const kr = parseKrakenOhlc({ result: { QNTUSD: [[1790621700, "1", "2", "0.5", "1.5", "1.2", "10", 3]], last: 1 } });
    const cb = parseCoinbaseCandles({ candles: [
      { start: "1790621760", open: "1", high: "2", low: "0.5", close: "1.5", volume: "10" },
      { start: "1790621700", open: "1", high: "2", low: "0.5", close: "1.5", volume: "10" }] });
    expect(kr[0]).toEqual({ t: 1790621700000, open: 1, high: 2, low: 0.5, close: 1.5, volume: 10 });
    expect(cb.map(c => c.t)).toEqual([1790621700000, 1790621760000]);
  });
});
