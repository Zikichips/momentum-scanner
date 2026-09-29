// CPU-cost check on LIVE payloads (npm run bench). Measures the parse + compute work each
// invocation does, in V8 on this machine; the Workers Free limit is 10 ms CPU per invocation.
// Network time does not count toward CPU time, so fetches are done outside the timed section.
import { describe, expect, it } from "vitest";
import {
  mergeUniverse, parseCoinbasePage, parseCoinbaseProducts, parseKrakenPairs, parseKrakenTicker, parseKrakenTickerAll,
} from "../src/exchanges";

const run = process.env.BENCH ? describe : describe.skip;

function time(label: string, f: () => unknown, n = 30): number {
  for (let i = 0; i < 5; i++) f();
  const t = performance.now();
  for (let i = 0; i < n; i++) f();
  const ms = (performance.now() - t) / n;
  console.log(`${label.padEnd(52)} ${ms.toFixed(2)} ms`);
  return ms;
}

run("CPU per invocation (live payloads)", () => {
  it("stays well under 10 ms per step", async () => {
    const get = (u: string) => fetch(u).then(r => r.text());
    const pairsTxt = await get("https://api.kraken.com/0/public/AssetPairs");
    const tickerTxt = await get("https://api.kraken.com/0/public/Ticker");
    const pages: string[] = [];
    for (let off = 0; ; off += 250) {
      const t = await get(`https://api.coinbase.com/api/v3/brokerage/market/products?product_type=SPOT&limit=250&offset=${off}`);
      pages.push(t);
      if (JSON.parse(t).products.length < 250) break;
    }
    const pairs = parseKrakenPairs(JSON.parse(pairsTxt));
    const kraken = parseKrakenTickerAll(JSON.parse(tickerTxt), pairs);
    const universe = mergeUniverse(kraken, pages.flatMap(p => parseCoinbasePage(JSON.parse(p))), 300);
    const kr = universe.filter(e => e.exchange === "kraken"), cb = universe.filter(e => e.exchange === "coinbase");
    console.log(`universe ${universe.length}: kraken ${kr.length}, coinbase ${cb.length}; coinbase pages ${pages.length}`);

    // The per-minute payloads, as the scan fetches them.
    const scanKr = await get(`https://api.kraken.com/0/public/Ticker?pair=${kr.map(e => e.id).join(",")}`);
    const scanCb = await get(`https://api.coinbase.com/api/v3/brokerage/market/products?limit=${cb.length}&${cb.map(e => `product_ids=${e.id}`).join("&")}`);
    console.log(`scan payloads: kraken ${(scanKr.length / 1024).toFixed(0)} KB, coinbase ${(scanCb.length / 1024).toFixed(0)} KB`);
    const keyToBase = Object.fromEntries(kr.map(e => [e.id, e.base]));
    const snapshot = JSON.stringify(Object.fromEntries(universe.map(e => [e.base, 1.2345])));

    const results = {
      scan: time("scan: parse both tickers + snapshot (de)serialise", () => {
        const q = { ...parseKrakenTicker(JSON.parse(scanKr), keyToBase), ...parseCoinbaseProducts(JSON.parse(scanCb)) };
        JSON.parse(snapshot); JSON.stringify(q);
      }),
      pairs: time("daily step: Kraken AssetPairs", () => parseKrakenPairs(JSON.parse(pairsTxt))),
      ticker: time("daily step: Kraken Ticker (all pairs)", () => parseKrakenTickerAll(JSON.parse(tickerTxt), pairs)),
      cbPage: time("daily step: one Coinbase products page", () => parseCoinbasePage(JSON.parse(pages[0]))),
    };
    expect(Object.keys(JSON.parse(scanCb).products).length).toBe(cb.length);   // product_ids filter returned them all
    for (const ms of Object.values(results)) expect(ms).toBeLessThan(5);        // 2× margin for slower Workers hardware
  }, 120_000);
});
