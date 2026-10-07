# HANDOFF — Momentum Scanner

**For:** Claude Code, continuing this project on Ivy's machine.
**From:** the planning/build session in Claude (chat), 28 Sep 2026.
**Owner:** Ivy (Edmonton, America/Edmonton). Stack she knows: Next.js, Supabase, JavaScript, Python (some), R.

Read this file top to bottom before doing anything. Then read `README.md` and `config.yaml`.

---

## 1. What this is, in one paragraph

Ivy wants to trade a small, separate $1,000 bankroll on short-term momentum in crypto (stocks later), with rules that remove judgment, and she wants proof over time that the tool actually picks winners. The plan agreed in chat was three modules — (1) catalyst calendar, (2) unusual-activity "footprints", (3) **momentum-continuation scanner** (the main one) — plus an automatic outcome tracker and a dashboard. All of that is now written and smoke-tested offline. Nothing has been deployed or run against live data. That's your job.

**Non-negotiables from the conversation**
- This is *not* connected to her long-term portfolio. Never suggest moving that money here.
- The tool alerts; it never auto-trades.
- Every alert is graded automatically so the scanner is judged on evidence. Keep that pipeline intact whatever else changes.
- Free tier everywhere: GitHub Actions (scheduler), Supabase (db), Vercel (dashboard), Telegram (alerts). Vercel Hobby can't run the 15-min cron — that's why scanning lives in Actions.

## 2. Current state (what exists and what's verified)

| Piece | File(s) | Status |
|---|---|---|
| Config | `config.yaml`, `scanner/config.py` | done |
| Data access | `scanner/data.py` | written; **not tested against live Kraken/yfinance** (build env had no market-data network) |
| Strategy (Stage A/B/C) | `scanner/strategy.py` | done, verified on synthetic data |
| Live scan loop | `scanner/scan.py` | done, verified via `tests/test_offline.py` with data monkeypatched |
| Outcome grader + scoreboard | `scanner/outcomes.py` | done, verified |
| Backtester | `scanner/backtest.py` | done for `--csv`; the ccxt paging path for `--symbols` is **untested live** |
| Module 1 catalysts | `scanner/catalysts.py` | written, untested (needs keys / network) |
| Module 2 footprints | `scanner/footprints.py` | written, untested (Binance OI endpoint may be geo-blocked from some runners; handle gracefully — it already returns None on failure) |
| Digest | `scanner/digest.py` | written, untested |
| Supabase schema | `supabase/schema.sql` | written, not applied |
| Actions workflows | `.github/workflows/scan.yml`, `daily.yml` | written, not run |
| Dashboard | `dashboard/` | scaffolded (3 pages), `npm install` never run, never built |
| Local store fallback | `scanner/db.py` | works; used by tests |

Run `python -m tests.test_offline` first. It must print `ALL OK`. If it doesn't, something in the environment differs — fix that before touching anything else.

## 3. Setup steps, in order

Do these with Ivy present; several need her logins.

### 3.1 Repo
```bash
cd momentum-scanner
git init && git add -A && git commit -m "Momentum scanner: initial build from planning session"
gh repo create momentum-scanner --private --source=. --push   # or public for unlimited Actions minutes
```
Private repo = 2,000 Actions minutes/month. The scan job is ~1–2 min × 96 runs/day ≈ 100–190 min/day, which **exceeds the private quota in ~12 days**. Either make the repo public, or change `scan.yml` cron to `*/30` (halves it), or move Stage B to hourly and accept slower pullback detection. Discuss with Ivy; recommend public (no secrets are in the code — they're all in Actions secrets).

### 3.2 Supabase
1. Create a project (free tier). Region: `us-west` or `ca-central` if offered.
2. SQL editor → paste `supabase/schema.sql` → run.
3. Settings → API: copy `URL`, `anon` key, `service_role` key.
4. Local `.env`: fill `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. Dashboard `.env.local`: `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

### 3.3 Telegram
1. Message `@BotFather` → `/newbot` → copy the token.
2. Message the new bot once (any text), then message `@userinfobot` to get the chat id. Or: `curl https://api.telegram.org/bot<TOKEN>/getUpdates` after messaging the bot and read `chat.id`.
3. `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Test: `python -c "from scanner import alerts; alerts.send('hello from scanner')"`.

### 3.4 First live run (local, before Actions)
```bash
pip install -r requirements.txt
python -m scanner.scan --stage a        # expect a list of symbols scanned; maybe 0–3 breakouts
python -m scanner.scan --stage b
python -m scanner.outcomes
python -m scanner.digest
```
Things likely to need fixing here (do them, don't ask):
- `data.crypto_universe()` filters on `symbol.endswith("/USD")`. Kraken uses `/USD`; if the exchange is changed to Binance, quote is `USDT` — update `config.yaml → universe.crypto.quote`.
- Kraken rate limits: `enableRateLimit=True` is set. If you see 429s, add `time.sleep` in the loops (there's already 0.05s).
- yfinance intraday: only 60 days of 1h history. Stocks are disabled by default; leave them off until crypto is stable.
- Timezone handling: everything is UTC internally; `scan._bo_from_row` normalises `breakout_date`. If Supabase returns dates as strings vs datetimes differently from the local store, fix it there.

### 3.5 GitHub Actions secrets
Repo → Settings → Secrets → Actions: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Optional: `CRYPTOPANIC_TOKEN`, `NEWSAPI_KEY`, `COINMARKETCAL_KEY` (each has a free tier; skip until modules 1–2 are wanted).
Then Actions tab → `scan` → Run workflow (stage `all`) and check the log. Then `daily`.

Scheduling: GitHub's cron for this repo ran hours late, so the spike worker (`spike-worker/src/dispatch.ts`, cron `1-59/5`) starts `scan.yml` every 5 minutes (stage `all` at minute 1 of each hour, `b,l` every 15 min, `l` otherwise) and `daily.yml` at 07:00 Edmonton, via workflow_dispatch with the `GH_DISPATCH_TOKEN` worker secret. `scan.yml` keeps its cron as a backup; `daily.yml` has none.

### 3.6 Dashboard on Vercel
```bash
cd dashboard && npm install && npm run build   # fix any type errors first
vercel                                          # link to Ivy's Vercel account, framework: Next.js
```
Set env vars in Vercel project settings: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Redeploy.
The journal page writes via the anon key (RLS allows insert/update on `journal` only). That's fine for a private URL; if Ivy shares the dashboard, add Supabase Auth and tighten the policy.

## 4. Backtest — do this before any real money

```bash
python -m scanner.backtest --symbols BTC/USD ETH/USD SOL/USD XRP/USD ADA/USD LINK/USD AVAX/USD DOT/USD QNT/USD --days 365
python -m scanner.backtest --days 365     # top-30 by volume; slow (Kraken paging), run once
```
Read `SUMMARY`. What the numbers mean:
- **win_rate** 0.35–0.45 with **avg_r** > 0.3 → consistent with a real (thin) edge. Proceed to forward testing.
- **avg_r** ≤ 0 → no edge at these thresholds. Tune `config.yaml → pullback` (try `min_retrace 0.30`, `max_retrace 0.50`, `pullback_volume_ratio_max 0.7`) and `breakout.volume_multiple` (try 2.5 and 4). Re-run. Keep a table of results in `data/backtest_log.md`.
- Fewer than ~20 setups over a year across 30 symbols → too strict; loosen `min_impulse_pct` first.
- **vs_hold_7d** negative on average is expected in a strong trend (rules take half off at T1). It's there to keep the question honest, not to be maximised.

Known limitation: the backtester is single-symbol sequential and doesn't model fees/slippage. Add `fees_pct: 0.3` to config and subtract 2× from `rule_return` in `outcomes.grade` when you get to it.

## 5. Next tasks, in priority order

1. **Live smoke** (3.4) and fix whatever breaks in `data.py`.
2. **Backtest** (4). Record results. Tune once, at most twice — don't overfit to one year.
3. **Deploy** Actions (3.5) and dashboard (3.6). Confirm a Telegram alert arrives from a real Stage A hit.
4. **Fees/slippage** in the grader.
5. **Stocks**: create `data/stock_universe.txt` (S&P 500 + the watchlist tickers in `data/stock_universe.txt`), set `universe.stocks.enabled: true`, run Stage A on daily bars only (yfinance 1h history is too short for reliable Stage B; consider Stage B on 1d bars for stocks or a paid data source).
6. **Module 1 & 2 keys** (CoinMarketCal, CryptoPanic) once the core is stable.
7. **Dashboard polish**: scoreboard chart over time (win rate + cumulative R), alert detail page, link journal rows to alerts.
8. **Journal discipline**: after 20 logged trades, add a "you vs the scanner" panel comparing Ivy's realised P&L with rule_return on the same alerts.

## 6. Design decisions already made (don't relitigate without reason)

- **Kraken, not Binance**, for public data: Canada-friendly, no key, no geo issues. Binance is only used for the futures OI endpoint in footprints, best-effort.
- **Daily bars for Stage A, hourly for Stage B.** 15-minute cron is scan frequency, not bar size.
- **`strategy.py` is pure** (no I/O) so the backtester and live scanner share one code path. Keep it that way.
- **Grader is the source of truth** for tool quality, independent of what Ivy actually trades. Journal is separate.
- **Local JSON store** when Supabase creds are absent — keeps tests and casual runs zero-config. Don't remove.
- **Position sizing** = 5% of capital at risk per trade, cap 50% of capital. Ivy's numbers; in `config.yaml`.

## 7. Things to tell Ivy when you get there

- The first backtest result, in plain words: does it have an edge or not, and what you changed.
- The Actions-minutes issue (3.1) and which option she picked.
- That the first 30 forward alerts are paper: log them in the journal as "followed rules" with size but no real trade, and compare to the scoreboard before funding.
- QNT (the trigger for this whole project) would have fired Stage A on 24 Sep and Stage B near $100 and again near $150, per the synthetic replay. A real replay on Kraken `QNT/USD` hourly data is a good first sanity check of the live backtester: `python -m scanner.backtest --symbols QNT/USD --days 30`.

## 8. Reference

Personal context from the planning chat is kept out of the repo (see the gitignored `HANDOFF.private.md` on Ivy's machine, if present). What matters here: she's not a professional trader, so explain results in plain language and always show the "vs hold" comparison.
