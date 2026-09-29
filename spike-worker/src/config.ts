// Spike detector rules. Detection and measurement only: nothing here places orders.
// Mirrors the spec in README.md; change a number here and the README together.

export const RULES = {
  universeSize: 300,              // top N USD spot pairs by 24h quote volume (Kraken ∪ Coinbase, dedup by base -> busier exchange)
  minQuoteVolume24h: 1_000_000,   // below this 24h quote volume (USD): "micro" -> shadow alerts only (graded, not sent)
  windowMin: 30,                  // rolling window
  minMove: 0.15,                  // price_now / price_30min_ago − 1
  prefilterMove: 0.13,            // cheap check on minute snapshots before fetching candles
  volumeMultiple: 5,              // volume_last_30min ≥ this × (30-day avg daily volume / 48)
  nearHigh: 0.97,                 // price_now ≥ this × high_last_30min
  cooldownMs: 4 * 3600_000,       // one alert per base symbol per 4 hours
  stopFloor: 0.87,                // stop = max(price_30min_ago, price_now × this)
  tpMultiple: 1.5,                // take_profit = price_now + this × (price_now − stop)
  costsPct: 1.5,                  // net_60 = ret_60 − this (percentage points)
  gradeHorizonsMin: [15, 30, 60, 240] as const,
  liquidity: { thin: 2_000_000, liquid: 20_000_000 },   // micro < $1M (shadow), thin < $2M, ok $2–20M, liquid > $20M
  baselineDays: 30,
  minBaselineDays: 20,            // fewer complete daily bars than this (new listing) -> no baseline, no alert
};

// Stablecoins and fiat bases never belong in the universe.
export const EXCLUDE_BASES = new Set([
  "USDT", "USDC", "DAI", "TUSD", "PYUSD", "EUR", "GBP", "CAD",
  // other USD stablecoins that would otherwise take universe slots
  "USD1", "USDS", "USDE", "FDUSD", "USDG", "RLUSD", "USDQ", "EURC", "EURQ", "USDD",
]);

// Round-trip cost estimate per alert: spread at alert time + 2 × taker fee. Lowest-tier taker
// fees as understood at build time; check the exchanges' current fee schedules.
export const TAKER_FEE_PCT: Record<"kraken" | "coinbase", number> = { kraken: 0.40, coinbase: 1.20 };

// Per-invocation budgets, sized to stay under the Workers Free limit of 50 external subrequests.
export const BUDGET = {
  maxCandidatesPerScan: 8,        // 1-min candle fetches to confirm a spike (coins >= $1M; checked first)
  maxAlertsPerScan: 3,            // each alert costs up to 8 subrequests (enrichment + store + Telegram)
  maxMicroCandidatesPerScan: 4,   // extra candle fetches for micro coins (shadow mode)
  maxShadowPerScan: 3,            // each shadow alert costs 1 subrequest (store only)
  baselineFetchesPerTick: 5,      // daily-candle fetches per scan tick while the baseline job runs
  maxGradesPerRun: 20,            // each grade = 1 candle fetch + 1 Supabase update
};

export interface Env {
  SPIKE_KV: KVNamespace;
  SPIKE_STATE: DurableObjectNamespace<import("./state").SpikeState>;
  CAPITAL_USD: string;
  RISK_PCT: string;
  MAX_POSITION_PCT: string;
  CRYPTOPANIC_URL: string;
  SUPABASE_URL?: string;
  SUPABASE_SERVICE_ROLE_KEY?: string;
  TELEGRAM_BOT_TOKEN?: string;
  TELEGRAM_CHAT_ID?: string;
  CRYPTOPANIC_TOKEN?: string;
  REDDIT_CLIENT_ID?: string;
  REDDIT_CLIENT_SECRET?: string;
}
