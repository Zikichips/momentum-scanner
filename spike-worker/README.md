# Spike detector (Cloudflare Worker)

Watches the 300 most liquid USD crypto pairs on Kraken and Coinbase every minute. It sends a Telegram alert when a coin jumps ≥ 15% in 30 minutes on ≥ 5× normal volume while still near its high. Then it grades every alert on what price did next. **Detection and measurement only: it never places orders.** Size, stop and take-profit in the alert are suggestions that the grader measures against.

Runs on the Workers **Free** plan. No VPS, and no dependency on GitHub Actions.

| Cron | Job |
|---|---|
| `* * * * *` | **scan**: fetch quotes for the universe (1 Kraken + 1 Coinbase call), store the minute's prices in the Durable Object, check spikes, alert |
| `*/10 * * * *` | **grade**: fill `ret_15/30/60/240`, `mfe_240`/`mae_240`, TP-or-stop-first, `net_60` for alerts until 240 min have passed |
| `0 4 * * *` | **baseline**: start the daily universe + 30-day volume baseline rebuild; write `spike_scoreboard` |

Storage: **Durable Object (SQLite)** for the rolling window, cooldowns and rebuild state · **KV** for the published universe and baseline (one write each per day) · **Supabase** for `spike_alerts` and `spike_scoreboard`, which the dashboard's Spikes tab reads.

## Rules

- **Universe:** top 300 USD spot pairs by 24h quote volume, Kraken ∪ Coinbase, deduplicated by base symbol: when both exchanges list a coin, the one with the higher 24h quote volume is used for prices, candles, grading and the liquidity check (Kraken on a tie), and the coin is ranked by that volume. Excludes stablecoins and fiat bases (USDT, USDC, DAI, TUSD, PYUSD, EUR, GBP, CAD, plus USD1, USDS, USDE, FDUSD, USDG, RLUSD, USDQ, EURC, EURQ, USDD). Coinbase `BASE-USDC` books are skipped because Coinbase shows them as USD. Rebuilt daily.
- **Minimum liquidity:** 24h quote volume ≥ $1M, else skipped.
- **Spike:** all of
  - `price_now / price_30min_ago − 1 ≥ 0.15`
  - `volume_last_30min ≥ 5 × (30-day average daily volume / 48)`
  - `price_now ≥ 0.97 × high_last_30min`
- **Cooldown:** one alert per base symbol per 4 hours.
- **Liquidity label:** thin < $2M · ok $2–20M · liquid > $20M (24h quote volume).
- **Suggested levels:** size = `position_size()` from the Python scanner (5% of `CAPITAL_USD` at risk, capped at 50%); stop = `max(price_30min_ago, price_now × 0.87)`; TP = `price_now + 1.5 × (price_now − stop)`.
- **Grading:** close-to-alert returns at +15/30/60/240 min; MFE/MAE within 240 min; which level was touched first (if one 1-minute bar touches both, the stop counts first); `net_60 = ret_60 − 1.5`.
- **Scoreboard (daily):** count, mean and median of each return and `net_60`, % TP first, % stop first. Given overall, by liquidity label, and by news (`yes` / `no` / `unknown` when CryptoPanic isn't configured).

All thresholds live in `src/config.ts`.

### How the pieces are measured

- **Price 30 minutes ago** comes from the minute snapshots. They're a cheap prefilter at +13%, so the Worker doesn't fetch candles for every coin every minute.
- **Final check:** coins that pass the prefilter (at most 8 per minute) are confirmed on **1-minute candles**. Those give the exact 30-minute volume, the 30-minute high and the price at the start of the window. A 24h ticker volume can't be differenced into a 30-minute volume, because volume also rolls out of the 24h window.
- **Candle gaps:** the window must start within 5 minutes of the 30-minute mark. Illiquid pairs have gaps in their candles.
- **Baseline:** the average of the last 30 complete daily candles, in base units, like the candle volume. Pairs with fewer than 20 days of history have no baseline and can't alert (6 of 300 on 2026-09-28).

## Request budget (per minute) and free-plan limits

These are the Workers Free limits as understood at build time. Check them against Cloudflare's current pricing page.

| Resource | This Worker | Free limit |
|---|---|---|
| Worker invocations | 1/min scan + 0.1/min grade + 1/day ≈ **1,585/day** | 100,000/day |
| External subrequests, scan (steady state) | **2** (Kraken Ticker + Coinbase products) | 50 per invocation |
| External subrequests, scan (worst case) | 2 + 8 candidate candle fetches + 3 alerts × 8 (hourly candles, CryptoPanic, Reddit ×3, prior spikes, Supabase insert, Telegram) + 6 baseline fetches (04:00–05:00 only) = **40** | 50 per invocation |
| External subrequests, grade | 1 + 20 × (candles + update) = **≤ 41** | 50 per invocation |
| Exchange APIs | Kraken 1–15 calls/min, Coinbase 1–15 calls/min | Kraken public ≈ 1/s; Coinbase public 10/s |
| KV | 2 reads/min (**2,880/day**); **2 writes/day** | 100,000 reads, 1,000 writes/day |
| Durable Object requests | ~2/min (**~2,900/day**) | 100,000/day |
| DO SQLite rows written | 1 snapshot + 1 delete per minute + rebuild state ≈ **3,000/day** | 100,000/day |
| Cron triggers | 3 | 5 per account |
| **CPU per invocation** | scan **1.3 ms**; largest daily step **2.7 ms** (see below) | 10 ms |

**CPU, measured** (`npm run bench`, live payloads, V8 in Node on an Apple-silicon Mac, 2026-09-28):

| Step | Payload | CPU |
|---|---|---|
| Scan: parse both tickers + snapshot | Kraken 62 KB + Coinbase 96 KB (`product_ids` filter, 77 products) | 1.28 ms |
| Daily: Kraken AssetPairs | 675 KB | 2.32 ms |
| Daily: Kraken Ticker, all pairs | 417 KB | 2.69 ms |
| Daily: one Coinbase products page | 318 KB (250 products; 4 pages) | 0.66 ms |

Each daily step parses at most one of these payloads per invocation. The rebuild therefore runs as a job across the scan ticks after 04:00 UTC: 1 step for AssetPairs, 1 for the ticker, 4 Coinbase pages, 50 steps of 6 daily-candle fetches (one at a time; symbols that fail, e.g. Coinbase 429s on Cloudflare's shared IPs, get one retry pass), then publish. Publishing sends a short Telegram heartbeat. That's about 56 minutes, and the previous universe keeps scanning in the meantime. Cloudflare's servers may be slower than this Mac. After deploying, confirm the real numbers under **Workers → spike-detector → Metrics → CPU time** (look at p99). The bench fails if any step exceeds 5 ms, which leaves 2× headroom.

## Setup

```bash
cd spike-worker
npm install
npx wrangler login
npx wrangler kv namespace create SPIKE_KV      # paste the id into wrangler.jsonc
```

Run `supabase/schema.sql` in the Supabase SQL editor (the spike tables are at the bottom). Then set the secrets:

| Secret | Needed for |
|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | storing alerts, grading, scoreboard, prior-spike counts. Without them alerts are only logged, and nothing is graded |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | alerts. Without them the message is logged |
| `CRYPTOPANIC_TOKEN` | "News 6h" line and `has_news` (optional; `unknown` without it) |
| `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Reddit line (optional). Create a "script" app at reddit.com/prefs/apps. The Worker uses Reddit's OAuth API directly, since praw is Python-only |

```bash
npx wrangler secret put SUPABASE_URL            # repeat for each secret above
npx wrangler deploy
curl https://spike-detector.<your-subdomain>.workers.dev/status   # universe/baseline/rebuild progress
npx wrangler tail                                                 # live logs: one "scan …" line per minute
npx wrangler kv key put rebuild now --binding SPIKE_KV --remote   # rebuild universe + baseline now (scanning continues)
```

The first universe build starts on the first scan tick after deploy and takes about an hour. Scanning starts when it publishes, and spikes can fire 30 minutes after that, once the rolling window is full.

Non-secret settings live in `wrangler.jsonc → vars`: `CAPITAL_USD`, `RISK_PCT`, `MAX_POSITION_PCT` (keep them in step with the Python `config.yaml`), and `CRYPTOPANIC_URL`.

## Local development

```bash
cp .dev.vars.example .dev.vars          # optional secrets for local runs
npm run dev                             # wrangler dev --test-scheduled
curl "http://localhost:8787/cdn-cgi/handler/scheduled?cron=0+4+*+*+*"      # start the rebuild
curl "http://localhost:8787/cdn-cgi/handler/scheduled?cron=*+*+*+*+*"      # one scan tick (repeat to step the rebuild)
curl "http://localhost:8787/cdn-cgi/handler/scheduled?cron=*+*+*+*+*&time=<epoch ms>"   # tick at a chosen time
curl http://localhost:8787/status
npm test                                # rules, grading, scoreboard, parsers
npm run bench                           # CPU per step on live payloads
```
