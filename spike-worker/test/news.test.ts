import { describe, expect, it } from "vitest";
import { findHeadline, mentions, parseRss } from "../src/news";
import { mergeUniverse, parseCoinbasePage } from "../src/exchanges";

const RSS = `<?xml version="1.0"?><rss><channel><title>Feed</title>
<item><title><![CDATA[Marlin (POND) jumps 40% as &quot;restaking&quot; narrative returns]]></title>
  <pubDate>Tue, 29 Sep 2026 11:00:00 +0000</pubDate></item>
<item><title>Ethereum&#8217;s gas fees fall &amp; ETH steadies</title><pubDate>Tue, 29 Sep 2026 09:00:00 +0000</pubDate></item>
<item><title>No date here</title></item>
</channel></rss>`;
const NOW = Date.parse("2026-09-29T12:00:00Z");

describe("parseRss", () => {
  it("reads titles (CDATA, entities) and dates, skipping undated items", () => {
    const items = parseRss(RSS, "Test");
    expect(items.map(i => i.title)).toEqual([
      'Marlin (POND) jumps 40% as "restaking" narrative returns',
      "Ethereum’s gas fees fall & ETH steadies",
    ]);
    expect(items[0].published).toBe(Date.parse("2026-09-29T11:00:00Z"));
  });
});

describe("mentions", () => {
  it("matches the name, the capitalised ticker, $TICKER and (TICKER)", () => {
    expect(mentions("Marlin jumps 40%", "POND", "Marlin")).toBe(true);
    expect(mentions("POND jumps 40%", "POND")).toBe(true);
    expect(mentions("Traders pile into $OP", "OP")).toBe(true);           // short ticker only in $ form
    expect(mentions("Optimism (OP) rallies", "OP")).toBe(true);
    expect(mentions("Chainlink expands CCIP", "LINK", "Chainlink")).toBe(true);
  });
  it("avoids the obvious false hits", () => {
    expect(mentions("Ethena launches new vault", "ETH", "Ethereum")).toBe(false);   // whole words only
    expect(mentions("One of the biggest weeks for DeFi", "ONE", "Harmony")).toBe(false);
    expect(mentions("SEC delays ETF decision", "SEC")).toBe(false);                 // acronym list
    expect(mentions("Trump signs crypto order", "TRUMP", "Official Trump")).toBe(false);
    expect(mentions("TRUMP memecoin unlock looms", "TRUMP", "Official Trump")).toBe(true);
    expect(mentions("Near-term outlook dims", "NEAR", "Near")).toBe(false);
    expect(mentions("the pond is frozen", "POND")).toBe(false);                     // ticker must be capitalised
    expect(mentions("OP ed: markets", "OP")).toBe(false);                           // 2-letter bare ticker ignored
  });
});

describe("findHeadline", () => {
  it("returns the newest match within 6 hours", () => {
    const items = parseRss(RSS, "Test");
    expect(findHeadline(items, "POND", "Marlin", NOW)?.title).toMatch(/^Marlin/);
    expect(findHeadline(items, "ETH", "Ethereum", NOW)?.title).toMatch(/^Ethereum/);
    expect(findHeadline(items, "POND", "Marlin", NOW + 6 * 3600_000)).toBeNull();   // 11:00 is > 6h before 18:00
  });
});

describe("coin names", () => {
  it("come from Coinbase and survive when the Kraken pair is chosen", () => {
    const cb = parseCoinbasePage({ products: [
      { product_id: "POND-USD", product_type: "SPOT", status: "online", base_display_symbol: "POND", base_name: "Marlin", approximate_quote_24h_volume: "1" },
    ] });
    const merged = mergeUniverse([{ base: "POND", exchange: "kraken", id: "PONDUSD", qvol24: 5 }], cb, 10);
    expect(merged[0]).toEqual({ base: "POND", exchange: "kraken", id: "PONDUSD", qvol24: 5, name: "Marlin" });
  });
});
