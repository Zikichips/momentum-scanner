# Momentum Scanner

A rules-based scanner for the *second leg* of a breakout: it finds assets that have already broken out on volume (Stage A), waits for a controlled pullback that holds (Stage B), then alerts with a precomputed entry, stop, two targets and position size (Stage C). Every alert is graded afterwards so the tool is judged on evidence, not vibes.

It does **not** place trades. It does **not** predict news. It gives you a watchlist, a disciplined setup, and a scoreboard.

```
Kraken/yfinance ────► Stage A (daily)  ──► in_play ──► Stage B (hourly) ──► alerts ──► Telegram
                                                                                  │
                                                       outcomes.py (daily) ◄──────┘  grades every alert
                                                                                  │
                                                                     scoreboard_daily ──► Next.js dashboard (Vercel)
```

## Layout

```
scanner/            Python package (the engine)
  config.py         loads config.yaml + .env
  data.py           ccxt (crypto) / yfinance (stocks) -> OHLCV DataFrames
  indicators.py     ema, rolling high, volume avg
  strategy.py       PURE logic: detect_breakout, detect_pullback, position_size
  scan.py           live entry point: Stage A, Stage B, exit notices
  outcomes.py       grades alerts (stop/t1/t2, MFE/MAE, hold vs rules), writes scoreboard
  backtest.py       replays strategy+grader over history
  catalysts.py      module 1: event calendar (CoinMarketCal, DefiLlama unlocks, earnings)
  footprints.py     module 2: unusual volume / OI with no news
  digest.py         7am Telegram digest
  alerts.py         Telegram formatting + send
  db.py             Supabase client; falls back to data/local_store.json when no creds
supabase/schema.sql tables + RLS policies
.github/workflows/  scan.yml (every 15 min), daily.yml (07:00 Edmonton)
dashboard/          Next.js 15 app: /alerts, /scoreboard, /journal
tests/              make_sample.py (synthetic QNT-like series), test_offline.py (end-to-end smoke)
config.yaml         every threshold, in one place
```

## Run locally (no cloud accounts needed)

```bash
pip install -r requirements.txt
python tests/make_sample.py                       # synthetic data
python -m tests.test_offline                      # Stage A -> B -> grade, expects "ALL OK"
python -m scanner.backtest --csv data/sample_QNT.csv
```

With network access:

```bash
cp .env.example .env                              # leave Supabase blank to use the JSON store
python -m scanner.scan --stage a                  # breakouts across the top-150 Kraken pairs
python -m scanner.backtest --symbols BTC/USD ETH/USD SOL/USD --days 365
python -m scanner.digest
```

## Strategy rules (config.yaml)

**Stage A — breakout (daily bars).** Close > 20-day high, volume ≥ 3× 30-day avg, ≥ 25% (crypto) / 12% (stocks) gain over 3 days. Asset goes "in play" for 5 days.

**Stage B — pullback (hourly bars).** Retrace 25–55% of the impulse, holding above the breakout level, 20-EMA rising and price has closed back above it after touching, pullback volume < 80% of impulse volume, R:R to T2 ≥ 2.

**Stage C — the alert.** Stop 1% below pullback low. T1 = impulse high (take half). T2 = high + 50% of impulse range. Size so a stop-out costs 5% of capital, capped at 50% of capital.

**Exits.** Close below stop → out. T1 → half off, stop to entry. T2 → out.

## Honest expectations

Breakout-pullback systems in the literature run 35–45% win rates at ~2:1 reward/risk — a thin edge before fees and slippage. The scoreboard exists to tell you whether *this* configuration has one. Don't trade real money until the backtest and 30+ forward-graded alerts agree it does.

See `HANDOFF.md` for deployment and next steps.
