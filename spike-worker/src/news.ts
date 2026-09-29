// "News 6h" from free RSS feeds. Fetched once per scan invocation, only when an alert fires,
// and shared across that minute's alerts. Matching is by coin name or ticker in the headline:
// cheaper and less precise than a tagged news API, so the rules below lean towards missing a
// headline rather than attaching a wrong one.

export const FEEDS = [
  { source: "CoinDesk", url: "https://www.coindesk.com/arc/outboundfeeds/rss/" },
  { source: "Cointelegraph", url: "https://cointelegraph.com/rss" },
  { source: "Decrypt", url: "https://decrypt.co/feed" },
  { source: "The Block", url: "https://www.theblock.co/rss.xml" },
];

export interface NewsItem { title: string; published: number; source: string }
export interface Feeds { items: NewsItem[]; ok: number; failed: string[] }

const ENTITIES: Record<string, string> = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
const decode = (s: string) => s
  .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
  .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
  .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
  .replace(/&([a-z]+);/gi, (m, n) => ENTITIES[n.toLowerCase()] ?? m)
  .replace(/\s+/g, " ").trim();

/** Titles and publish times from an RSS 2.0 feed (regex; Workers have no DOM parser). */
export function parseRss(xml: string, source: string): NewsItem[] {
  const out: NewsItem[] = [];
  for (const m of xml.matchAll(/<item[\s>][\s\S]*?<\/item>/g)) {
    const title = /<title[^>]*>([\s\S]*?)<\/title>/.exec(m[0])?.[1];
    const date = /<pubDate>([\s\S]*?)<\/pubDate>/.exec(m[0])?.[1] ?? /<dc:date>([\s\S]*?)<\/dc:date>/.exec(m[0])?.[1];
    const published = date ? Date.parse(decode(date)) : NaN;
    if (title && isFinite(published)) out.push({ title: decode(title), published, source });
  }
  return out;
}

export async function fetchFeeds(): Promise<Feeds> {
  const res = await Promise.allSettled(FEEDS.map(async f => {
    const r = await fetch(f.url, { signal: AbortSignal.timeout(4000), headers: { "User-Agent": "spike-detector/1.0 (+rss)" } });
    if (!r.ok) throw new Error(`${r.status}`);
    return parseRss(await r.text(), f.source);
  }));
  const feeds: Feeds = { items: [], ok: 0, failed: [] };
  res.forEach((r, i) => {
    if (r.status === "fulfilled") { feeds.items.push(...r.value); feeds.ok++; }
    else feeds.failed.push(`${FEEDS[i].source}: ${String(r.reason)}`);
  });
  return feeds;
}

// Names are matched ignoring case, so coin names that are ordinary words would hit unrelated
// headlines ("Trump", "Dash", "Near"). Those names are skipped; the ticker can still match.
const WORD_NAMES = new Set([
  "one", "gas", "near", "flow", "sand", "band", "magic", "render", "mask", "origin", "status", "graph", "maker",
  "compound", "super", "safe", "move", "just", "people", "blur", "ace", "ark", "bat", "cat", "cow", "dog", "ever",
  "fun", "hot", "key", "life", "max", "meme", "moon", "new", "now", "open", "pay", "pepe", "pro", "real", "sun",
  "time", "trump", "true", "win", "wild", "world", "zero", "act", "big", "bond", "core", "dash", "dent", "edge",
  "gold", "hard", "home", "ice", "jet", "kind", "loom", "mint", "power", "prime", "pump", "quick", "ray", "rare",
  "rose", "shell", "sign", "star", "sync", "wave", "coin", "token", "bitcoin cash", "useless", "official trump",
]);
// Tickers are matched only in capitals, so the risk is capitalised acronyms and words in headlines.
const WORD_TICKERS = new Set([
  "ONE", "NEW", "NOW", "THE", "API", "NFT", "ETF", "SEC", "CEO", "DAO", "DEX", "CEX", "TVL", "FED", "CPI", "GDP",
  "USA", "IPO", "ATH", "OTC", "KYC", "AML", "APY", "APR", "RWA", "CZ", "BIG", "WIN", "SUN", "HOT", "KEY", "MAX",
  "TRUE", "ALL", "FOR", "AND", "WHY", "HOW", "WHO", "BUY", "SELL", "GAS", "ACE", "CAT", "DOG", "PAY", "PRO", "ICE",
]);

const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Does this headline mention the coin? */
export function mentions(title: string, base: string, name?: string): boolean {
  const t = base.toUpperCase();
  // Unmistakable forms, any ticker length: $POND, (POND)
  if (new RegExp(`\\$${esc(t)}\\b|\\(${esc(t)}\\)`).test(title)) return true;
  // Ticker as a capitalised whole word, 3+ letters, not an acronym/word
  if (t.length >= 3 && !WORD_TICKERS.has(t) && new RegExp(`(^|[^A-Za-z0-9])${esc(t)}([^A-Za-z0-9]|$)`).test(title)) return true;
  // Coin name as a whole word/phrase, case-insensitive, 4+ letters, not a common word
  if (name && name.length >= 4 && !WORD_NAMES.has(name.toLowerCase())
      && new RegExp(`(^|[^A-Za-z0-9])${esc(name)}([^A-Za-z0-9]|$)`, "i").test(title)) return true;
  return false;
}

/** Newest headline in the last 6h that mentions the coin. */
export function findHeadline(items: NewsItem[], base: string, name: string | undefined, now: number): NewsItem | null {
  return items
    .filter(i => now - i.published <= 6 * 3600_000 && i.published <= now + 5 * 60_000)
    .sort((a, b) => b.published - a.published)
    .find(i => mentions(i.title, base, name)) ?? null;
}
