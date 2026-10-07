# Stage A vs Coinbase top movers

Window 2026-07-09 to 2026-10-06 (90 days), Kraken top 30 by each day's volume (rolling, no hindsight), on Coinbase data, 399 with data. Mover = top 10 by UTC close-to-close gain that day, gain ≥ 20%. Thresholds as in config.yaml: close > 20-day high, volume ≥ 3.0× 30-day avg, 3-day gain ≥ 25%. Breakout entry: stop 3.0% under level, T1/T2 = 1.0×/2.0× leg.

## Recall — did Stage A alert in the 5 days before a mover day?

- Mover days: **328**. Caught: **16 (5%)**. Missed: 312.
- Lead time on caught movers (days before the mover day): 1d: 5, 2d: 3, 3d: 4, 4d: 3, 5d: 1
- Caught movers' breakout entries: avg R 3.081, avg rule return 38.975%.
- Of the misses, Stage A fired **on the mover day itself** (i.e. after the move) for 31 (10%).
- Misses by failed condition on the D−1 bar:

| why | count | share |
|---|---|---|
| not in universe on D−5..D−1 | 292 | 94% |
| prior-high + volume + 3d-gain | 13 | 4% |
| prior-high + volume | 2 | 1% |
| 3d-gain | 1 | 0% |
| volume | 1 | 0% |
| suppressed (already in play) | 1 | 0% |
| volume + 3d-gain | 1 | 0% |
| prior-high + 3d-gain | 1 | 0% |

Median on D−1 for diagnosable misses: close vs 20-day high -5.6%, volume 1.47×, 3-day gain +10.8%.

## Precision — did alerts become movers within 5 days?

- Alerts in window: **56** (1 too recent to judge).
- Became a mover on A+1..A+5: **11 of 55 (20%)**.
- Alert day itself was already a mover: 30 of 55.
- Avg R per alert, all judged alerts: **0.372** (R known for 55 of 55).
- Dollars at $300 capital (5% risk, 50% cap), no fees: total **$237.92** over 55 trades, avg $4.326/alert; became mover $347.18, did not $-109.26. Each alert is traded independently, so overlapping positions can exceed capital.
- Avg R — became mover: **2.718**; did not: **-0.215**.
- Alerts that did not become movers (R known for 44): ≤ −1R: 18, −1R to 0: 13, > 0: 13; median -0.62R, worst -1.42R.

## Account replay — $300, max 2 open, 50% cap, 0.3%/side fees

Every graded breakout entry in the window replayed as one account (trades still open are marked at the last bar). Taken 19, skipped at the limit 37; win rate 0.526, avg R 0.97; **P&L $276.87**, max drawdown $48.07, worst trade $-16.87.

## Confusion matrix — every (coin, day) in the window

| | Alert in prior 5 days | No alert |
|---|---|---|
| **Mover that day** | 16 | 312 |
| **Not a mover** | 266 | 34906 |

Recall 5%. Precision per coin-day 6% (differs from per-alert precision above: one alert covers 5 coin-days).

## Caught movers

| day | symbol | gain_pct | alert_day | lead_days | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|
| 2026-07-20 | OXT/USD | 23.93 | 2026-07-17 | 3 | 0.02 | expired | -28.74 | -0.64 |
| 2026-07-31 | COTI/USD | 20.74 | 2026-07-29 | 2 | 0.02 | stop | -20.11 | -1.15 |
| 2026-08-05 | HFT/USD | 56.03 | 2026-08-04 | 1 | 0.01 | t2 | 63.36 | 6.54 |
| 2026-08-06 | HFT/USD | 66.85 | 2026-08-04 | 2 | 0.01 | t2 | 63.36 | 6.54 |
| 2026-08-07 | BICO/USD | 39.62 | 2026-08-06 | 1 | 0.04 | t2 | 95.44 | 3.50 |
| 2026-08-10 | GWEI/USD | 24.39 | 2026-08-07 | 3 | 0.03 | stop | -7.63 | -1.33 |
| 2026-08-16 | APR/USD | 22.14 | 2026-08-12 | 4 | 0.58 | stop | -61.55 | -1.02 |
| 2026-08-30 | HNT/USD | 79.73 | 2026-08-29 | 1 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-01 | USELESS/USD | 24.55 | 2026-08-31 | 1 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | USELESS/USD | 68.66 | 2026-08-31 | 3 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | HNT/USD | 37.58 | 2026-08-29 | 5 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-04 | USELESS/USD | 27.66 | 2026-08-31 | 4 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-05 | ARB/USD | 34.23 | 2026-09-01 | 4 | 0.11 | t2 | 36.94 | 10.63 |
| 2026-09-19 | DRV/USD | 51.35 | 2026-09-16 | 3 | 0.24 | t2 | 67.02 | 3.26 |
| 2026-09-26 | QNT/USD | 53.47 | 2026-09-25 | 1 | 98.68 | t2 | 50.04 | 5.19 |
| 2026-09-27 | QNT/USD | 88.99 | 2026-09-25 | 2 | 98.68 | t2 | 50.04 | 5.19 |

## Missed movers

| day | symbol | gain_pct | why | close_vs_high_pct | vol_mult | gain_3d | fired_on_day |
|---|---|---|---|---|---|---|---|
| 2026-07-09 | BASED1/USD | 27.78 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-09 | SENT/USD | 23.30 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-09 | SKL/USD | 22.86 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-10 | PYR/USD | 46.46 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-11 | T/USD | 39.47 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-11 | SXT/USD | 33.80 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-12 | BLAST/USD | 35.71 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-12 | BILL/USD | 21.50 | prior-high + volume + 3d-gain | -35.55 | 0.61 | 8.41 | no |
| 2026-07-13 | ALLO/USD | 26.91 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-13 | BILL/USD | 20.74 | prior-high + volume | -21.70 | 2.48 | 30.94 | yes |
| 2026-07-14 | DRV/USD | 32.49 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-14 | B3/USD | 31.80 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-15 | HOME/USD | 32.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-16 | OXT/USD | 86.84 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-16 | BOBBOB/USD | 32.65 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-17 | OXT/USD | 135.21 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-07-17 | NKN/USD | 126.00 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-17 | SUKU/USD | 40.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-18 | HONEY/USD | 43.56 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-19 | GHST/USD | 22.34 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-19 | PUMP/USD | 20.22 | prior-high + volume + 3d-gain | -6.79 | 0.27 | -1.60 | no |
| 2026-07-20 | 00/USD | 55.00 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-20 | POND/USD | 28.38 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-21 | ERA/USD | 44.39 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-21 | 00/USD | 37.10 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-21 | BAL/USD | 27.06 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-21 | IMU/USD | 24.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-21 | HIGH/USD | 21.36 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-22 | GST/USD | 23.12 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-22 | RE/USD | 20.12 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-23 | ELA/USD | 29.88 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-23 | BILL/USD | 26.22 | prior-high + volume + 3d-gain | -63.54 | 1.46 | -1.19 | no |
| 2026-07-24 | GWEI/USD | 30.43 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-24 | OXT/USD | 20.93 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-25 | EUL/USD | 78.82 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-07-25 | QI/USD | 37.51 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-25 | REQ/USD | 26.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | ESP/USD | 46.91 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | TROLL/USD | 38.91 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | KAIO/USD | 31.60 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | THQ/USD | 29.34 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | DIA/USD | 28.11 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-26 | SAFE/USD | 25.88 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-27 | BOBBOB/USD | 52.43 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-27 | COTI/USD | 48.65 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-27 | 00/USD | 22.89 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-29 | COTI/USD | 59.63 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-07-29 | META/USD | 22.87 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-30 | FORTH/USD | 82.42 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-30 | CAP/USD | 31.30 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-30 | ROBO/USD | 26.75 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-31 | WMTX/USD | 113.31 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-31 | GODS/USD | 45.67 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-07-31 | DRV/USD | 24.09 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-01 | META/USD | 46.61 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-01 | BLZ/USD | 37.64 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-02 | BICO/USD | 37.61 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-02 | FORTH/USD | 23.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-03 | 00/USD | 24.42 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-04 | BICO/USD | 25.98 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-04 | HFT/USD | 24.73 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-04 | META/USD | 20.45 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-05 | BICO/USD | 29.06 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-06 | PYR/USD | 46.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-06 | BICO/USD | 43.22 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-06 | CTSI/USD | 42.13 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-06 | STG/USD | 28.71 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-06 | GWEI/USD | 25.92 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-06 | COOKIE/USD | 25.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-07 | GWEI/USD | 55.80 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-07 | C98/USD | 21.90 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-08 | IMU/USD | 235.34 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-08 | COOKIE/USD | 39.96 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-08 | DIMO/USD | 35.49 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-08 | 00/USD | 22.62 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-09 | XAN/USD | 53.97 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-10 | RAD/USD | 30.33 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-10 | SQD/USD | 23.55 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-11 | NOICE/USD | 39.81 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-11 | GODS/USD | 23.79 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-12 | APR/USD | 179.34 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-12 | COTI/USD | 25.00 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-13 | IMU/USD | 44.55 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-14 | ALICE/USD | 41.38 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-15 | FUN1/USD | 49.11 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-15 | COW/USD | 38.17 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-17 | 00/USD | 41.53 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-18 | PRCL/USD | 120.00 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-19 | RE/USD | 35.13 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-19 | OCEAN/USD | 29.37 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-19 | TRUMP/USD | 27.26 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-19 | MOG/USD | 22.22 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-20 | SHDW/USD | 47.39 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-20 | OSMO/USD | 41.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-20 | SHPING/USD | 29.05 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-20 | PUMP/USD | 27.71 | prior-high + volume + 3d-gain | -4.09 | 1.31 | 12.68 | no |
| 2026-08-20 | ENA/USD | 25.07 | prior-high + volume + 3d-gain | -4.99 | 1.84 | 13.32 | yes |
| 2026-08-21 | LMTS/USD | 49.13 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | LCX/USD | 32.19 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | USELESS/USD | 32.11 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | ENS/USD | 30.75 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | STX/USD | 29.73 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | BCH/USD | 29.12 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-21 | ZEC/USD | 29.06 | prior-high + volume + 3d-gain | -1.91 | 2.64 | 10.80 | yes |
| 2026-08-21 | PEPE/USD | 28.04 | 3d-gain | 7.72 | 5.65 | 24.42 | yes |
| 2026-08-21 | KEYCAT/USD | 25.45 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-21 | ZORA/USD | 25.02 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-22 | AERGO/USD | 75.67 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-22 | LCX/USD | 66.32 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-22 | TRUMP/USD | 27.65 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-22 | PUMP/USD | 22.35 | volume | 3.26 | 2.60 | 30.99 | yes |
| 2026-08-23 | KEYCAT/USD | 30.18 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-23 | BLZ/USD | 29.82 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-23 | SPK/USD | 29.68 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-23 | MORPHO/USD | 25.63 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-23 | TRAC/USD | 22.60 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-24 | MDT/USD | 76.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-24 | KEYCAT/USD | 33.44 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-24 | DRV/USD | 25.01 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | MDT/USD | 180.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | FORTH/USD | 46.31 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | HONEY/USD | 42.26 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | PERP/USD | 37.43 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | 00/USD | 36.11 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | GROVE/USD | 26.10 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | ELA/USD | 23.66 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-25 | META/USD | 23.49 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | NCT/USD | 286.12 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | DNT/USD | 45.76 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | HONEY/USD | 29.36 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | RLS/USD | 26.50 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | BICO/USD | 25.23 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | BOBBOB/USD | 24.17 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-26 | CVX/USD | 21.78 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | DRB/USD | 63.79 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | 00/USD | 44.20 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | BLZ/USD | 26.38 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | BEAM/USD | 24.45 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | SKR/USD | 21.71 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-27 | PYR/USD | 20.31 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-28 | GHST/USD | 144.42 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-28 | HONEY/USD | 31.30 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-28 | MDT/USD | 27.74 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-29 | HNT/USD | 68.58 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-29 | HIGH/USD | 37.25 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-29 | SWELL/USD | 22.86 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-29 | 00/USD | 20.38 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-29 | NKN/USD | 20.13 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-30 | SKR/USD | 127.49 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-30 | BASECAT/USD | 85.33 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-30 | ZKC/USD | 51.76 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-30 | AST/USD | 29.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-30 | ZORA/USD | 27.64 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-30 | POND/USD | 23.06 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-31 | USELESS/USD | 31.57 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-08-31 | ARB/USD | 29.44 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-31 | KTA/USD | 24.64 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-31 | HONEY/USD | 22.95 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-08-31 | FLOCK/USD | 21.75 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-01 | MLN/USD | 37.06 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-02 | T/USD | 47.96 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-02 | EGLD/USD | 32.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | BASECAT/USD | 62.30 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | EDGEX/USD | 36.20 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | APR/USD | 31.76 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | CHIP/USD | 31.09 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | TROLL/USD | 29.39 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-03 | AERGO/USD | 26.70 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | BLZ/USD | 63.83 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | TROLL/USD | 43.31 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | FLOCK/USD | 32.83 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | TRIA/USD | 32.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | DASH/USD | 31.77 | prior-high + volume + 3d-gain | -4.52 | 1.27 | 5.74 | yes |
| 2026-09-04 | BASECAT/USD | 24.32 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-04 | XCN/USD | 21.33 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-05 | RNBW/USD | 37.89 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-05 | BASECAT/USD | 34.61 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-05 | SUSHI/USD | 33.81 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-05 | FLOCK/USD | 22.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-05 | XAN/USD | 22.26 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-06 | PYR/USD | 52.41 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-06 | RAY/USD | 41.50 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-06 | RNBW/USD | 32.72 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-06 | DOOD/USD | 30.62 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-06 | JUPITER/USD | 25.22 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-06 | METIS/USD | 22.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-07 | VOXEL/USD | 35.62 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-07 | DRB/USD | 28.32 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-08 | VVV/USD | 40.23 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-08 | DIEM/USD | 34.25 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-08 | USELESS/USD | 23.75 | suppressed (already in play) | -27.24 | 1.50 | -13.04 | no |
| 2026-09-09 | OXT/USD | 72.50 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-09 | KAT/USD | 33.86 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-10 | SYND/USD | 127.34 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-10 | UP/USD | 29.04 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-10 | VTHO/USD | 24.57 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-11 | FARM/USD | 20.95 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-12 | FLOCK/USD | 29.91 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-12 | REZ/USD | 23.36 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-12 | ILV/USD | 22.01 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-13 | FORTH/USD | 62.63 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-13 | SYND/USD | 42.32 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-13 | CVC/USD | 38.57 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-13 | B3/USD | 30.88 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-13 | MEZO/USD | 21.34 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-14 | CAP/USD | 36.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-15 | ALIGN/USD | 33.90 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-16 | DRV/USD | 77.98 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-16 | ZEC/USD | 20.57 | prior-high + volume + 3d-gain | -14.55 | 0.96 | -1.24 | no |
| 2026-09-17 | COTI/USD | 46.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-17 | DRIFT/USD | 29.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | G/USD | 55.51 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | STRK/USD | 53.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | AURORA/USD | 37.74 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | BASECAT/USD | 32.04 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | ARB/USD | 24.86 | prior-high + volume | -14.05 | 1.81 | 32.52 | no |
| 2026-09-18 | APT/USD | 22.42 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-18 | ZK/USD | 22.14 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-19 | CELR/USD | 45.81 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-19 | G/USD | 39.48 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-19 | ZAMA/USD | 37.27 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-19 | EDGE/USD | 25.47 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-19 | XTZ/USD | 24.09 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-09-19 | AVAX/USD | 23.05 | volume + 3d-gain | 0.10 | 2.18 | 12.95 | yes |
| 2026-09-19 | META/USD | 22.49 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-19 | ENA/USD | 21.27 | prior-high + volume + 3d-gain | -10.90 | 0.65 | 20.57 | no |
| 2026-09-20 | RARI/USD | 65.54 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | AURORA/USD | 181.71 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | AIOZ/USD | 55.17 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | ZETA/USD | 42.01 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | ZETACHAIN/USD | 40.35 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | SWELL/USD | 35.21 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | VARA/USD | 34.86 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | BNKR/USD | 24.90 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-21 | TAO/USD | 22.05 | prior-high + volume + 3d-gain | -5.55 | 1.48 | 12.75 | yes |
| 2026-09-21 | WIF/USD | 21.04 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | SHDW/USD | 132.61 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | AURORA/USD | 67.65 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | ALCX/USD | 55.56 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | MPLX/USD | 45.40 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | A8/USD | 36.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | DRIFT/USD | 35.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | BCH/USD | 29.15 | prior-high + 3d-gain | -0.92 | 3.03 | 4.58 | yes |
| 2026-09-22 | KERNEL/USD | 28.51 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-22 | USELESS/USD | 23.76 | prior-high + volume + 3d-gain | -16.92 | 0.94 | -4.12 | no |
| 2026-09-22 | MINA/USD | 21.57 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-23 | NEON/USD | 322.84 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-23 | GFI/USD | 115.69 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-23 | ALEO/USD | 48.73 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-23 | DBR/USD | 21.30 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | ALEO/USD | 78.21 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | NEON/USD | 47.33 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | QNT/USD | 27.45 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | AURORA/USD | 27.04 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | ONDO/USD | 26.65 | prior-high + volume + 3d-gain | -11.11 | 1.47 | -4.80 | no |
| 2026-09-24 | DBR/USD | 25.79 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-24 | XPL/USD | 23.17 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | QI/USD | 139.58 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | POND/USD | 102.85 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | FARM/USD | 38.53 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | VARA/USD | 34.36 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | CTX/USD | 27.54 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | PNG/USD | 25.86 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | RARE/USD | 22.62 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | AERO/USD | 22.06 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-25 | MPLX/USD | 21.40 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | AMP/USD | 62.66 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | EDGE/USD | 43.75 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | RARE/USD | 34.18 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | KARRAT/USD | 31.98 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | MNDE/USD | 28.14 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-26 | 2Z/USD | 23.15 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-27 | INX/USD | 31.16 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-27 | GRT/USD | 30.07 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-27 | ABT/USD | 21.21 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-28 | KAIO/USD | 121.59 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-28 | AVT/USD | 59.39 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-28 | NMR/USD | 35.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-28 | HBAR/USD | 27.28 | prior-high + volume + 3d-gain | -5.43 | 1.26 | 3.04 | yes |
| 2026-09-29 | AST/USD | 40.41 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-29 | DIMO/USD | 27.95 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-29 | GRASS/USD | 27.84 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-29 | POND/USD | 26.89 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-29 | KARRAT/USD | 23.02 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-30 | DIMO/USD | 43.35 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-30 | LCX/USD | 32.19 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-30 | SUP/USD | 26.13 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-09-30 | ALEO/USD | 24.26 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-01 | GTC/USD | 53.24 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-01 | ALICE/USD | 25.45 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-01 | CT/USD | 20.52 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-01 | MEGA/USD | 20.15 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-02 | SAND/USD | 53.56 | not in universe on D−5..D−1 | – | – | – | yes |
| 2026-10-02 | MDT/USD | 20.64 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-03 | HFT/USD | 33.28 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-03 | STRK/USD | 26.19 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-03 | BASECAT/USD | 20.57 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | HONEY/USD | 65.39 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | GTC/USD | 52.35 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | RARI/USD | 34.02 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | BLAST/USD | 31.03 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | EDGE/USD | 24.70 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-04 | DIMO/USD | 23.21 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | RLC/USD | 98.68 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | DIMO/USD | 63.27 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | MNDE/USD | 43.93 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | RAD/USD | 31.94 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | KAIO/USD | 31.58 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-05 | ORCA/USD | 20.47 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-06 | FORT/USD | 46.67 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-06 | NMR/USD | 34.19 | not in universe on D−5..D−1 | – | – | – | no |
| 2026-10-06 | ORCA/USD | 32.40 | not in universe on D−5..D−1 | – | – | – | no |

## Alerts

| alert_day | symbol | via | impulse_pct | alert_day_was_mover | became_mover | days_to_mover | entry | trade | rule_return | r_multiple | position_usd | pnl_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-13 | BILL/USD | kraken | 51.92 | yes | no | – | 0.06 | stop | -8.93 | -1.42 | 150.00 | -13.40 |
| 2026-07-17 | OXT/USD | kraken | 339.47 | yes | yes | 3 | 0.02 | expired | -28.74 | -0.64 | 33.47 | -9.62 |
| 2026-07-23 | ZAMA/USD | kraken | 33.12 | no | no | – | 0.05 | expired | -0.24 | -0.02 | 117.17 | -0.29 |
| 2026-07-25 | EUL/USD | kraken | 98.16 | yes | no | – | 1.94 | expired | -39.39 | -0.87 | 33.00 | -13.00 |
| 2026-07-26 | SHIB/USD | kraken | 28.33 | no | no | – | 0.00 | stop | -6.60 | -1.27 | 150.00 | -9.91 |
| 2026-07-29 | COTI/USD | kraken | 135.14 | yes | yes | 2 | 0.02 | stop | -20.11 | -1.15 | 85.74 | -17.25 |
| 2026-08-04 | HFT/USD | kraken | 33.33 | yes | yes | 1 | 0.01 | t2 | 63.36 | 6.54 | 150.00 | 95.04 |
| 2026-08-06 | BICO/USD | kraken | 132.87 | yes | yes | 1 | 0.04 | t2 | 95.44 | 3.50 | 55.01 | 52.50 |
| 2026-08-07 | GWEI/USD | kraken | 83.01 | yes | yes | 3 | 0.03 | stop | -7.63 | -1.33 | 150.00 | -11.44 |
| 2026-08-09 | XAN/USD | kraken | 59.48 | yes | no | – | 0.02 | stop | -38.87 | -1.11 | 42.86 | -16.66 |
| 2026-08-12 | APR/USD | kraken | 189.74 | yes | yes | 4 | 0.58 | stop | -61.55 | -1.02 | 24.91 | -15.33 |
| 2026-08-18 | PRCL/USD | kraken | 115.22 | yes | no | – | 0.01 | stop | -23.23 | -1.03 | 66.38 | -15.42 |
| 2026-08-20 | ENA/USD | kraken | 40.29 | yes | no | – | 0.12 | t2 | 45.09 | 2.46 | 81.66 | 36.82 |
| 2026-08-20 | XRP/USD | kraken | 26.49 | no | no | – | 1.27 | expired | 17.92 | 1.37 | 114.70 | 20.55 |
| 2026-08-21 | AAVE/USD | kraken | 40.12 | no | no | – | 122.63 | expired | 6.79 | 0.32 | 70.20 | 4.76 |
| 2026-08-21 | ADA/USD | kraken | 31.32 | no | no | – | 0.23 | stop | -10.60 | -1.01 | 143.61 | -15.22 |
| 2026-08-21 | BCH/USD | kraken | 41.44 | yes | no | – | 287.88 | expired | -14.75 | -0.62 | 63.41 | -9.35 |
| 2026-08-21 | CRV/USD | kraken | 42.40 | no | no | – | 0.34 | expired | 1.34 | 0.07 | 80.96 | 1.08 |
| 2026-08-21 | DOGE/USD | kraken | 30.36 | no | no | – | 0.09 | stop | -11.88 | -1.03 | 130.69 | -15.52 |
| 2026-08-21 | ETH/USD | kraken | 31.26 | no | no | – | 2515.80 | expired | -2.52 | -0.28 | 150.00 | -3.78 |
| 2026-08-21 | FARTCOIN/USD | kraken | 39.39 | no | no | – | 0.20 | stop | -14.98 | -1.00 | 100.23 | -15.01 |
| 2026-08-21 | HYPE/USD | kraken | 29.11 | no | no | – | 75.54 | expired | 11.62 | 3.15 | 150.00 | 17.43 |
| 2026-08-21 | LINK/USD | kraken | 25.70 | no | no | – | 11.99 | expired | -3.04 | -0.26 | 126.29 | -3.85 |
| 2026-08-21 | MON/USD | kraken | 34.97 | no | no | – | 0.03 | stop | -8.40 | -1.13 | 150.00 | -12.60 |
| 2026-08-21 | PENGU/USD | kraken | 47.08 | no | no | – | 0.01 | expired | -6.95 | -0.34 | 74.20 | -5.15 |
| 2026-08-21 | PEPE/USD | kraken | 59.30 | yes | no | – | 0.00 | expired | -15.09 | -0.66 | 65.72 | -9.91 |
| 2026-08-21 | SUI/USD | kraken | 29.55 | no | no | – | 0.84 | stop | -15.68 | -1.17 | 111.63 | -17.50 |
| 2026-08-21 | XLM/USD | kraken | 30.38 | no | no | – | 0.20 | stop | -8.67 | -1.12 | 150.00 | -13.01 |
| 2026-08-21 | ZEC/USD | kraken | 44.39 | yes | no | – | 734.47 | expired | 35.29 | 1.65 | 70.25 | 24.79 |
| 2026-08-22 | DASH/USD | kraken | 29.49 | no | no | – | 41.14 | stop | -6.64 | -1.01 | 150.00 | -9.95 |
| 2026-08-22 | POL/USD | kraken | 31.10 | no | no | – | 0.11 | stop | -13.40 | -1.01 | 113.62 | -15.23 |
| 2026-08-22 | PUMP/USD | kraken | 65.33 | yes | no | – | 0.00 | stop | -17.16 | -1.02 | 89.43 | -15.35 |
| 2026-08-22 | TRUMP/USD | kraken | 32.97 | yes | no | – | 2.38 | expired | 0.01 | 0.00 | 75.67 | 0.01 |
| 2026-08-29 | HNT/USD | kraken | 84.15 | yes | yes | 1 | 0.43 | t2 | 80.02 | 2.20 | 41.16 | 32.94 |
| 2026-08-30 | SKR/USD | kraken | 143.40 | yes | no | – | 0.03 | expired | -31.19 | -0.61 | 29.36 | -9.16 |
| 2026-08-31 | USELESS/USD | kraken | 49.06 | yes | yes | 1 | 0.09 | t2 | 51.80 | 2.74 | 79.24 | 41.04 |
| 2026-08-31 | ZORA/USD | kraken | 45.41 | no | no | – | 0.01 | stop | -4.31 | -1.11 | 150.00 | -6.46 |
| 2026-09-01 | ARB/USD | kraken | 26.12 | no | yes | 4 | 0.11 | t2 | 36.94 | 10.63 | 150.00 | 55.40 |
| 2026-09-04 | DASH/USD | kraken | 42.44 | yes | no | – | 62.59 | t1 | 16.80 | 0.73 | 65.50 | 11.00 |
| 2026-09-04 | XCN/USD | kraken | 30.45 | yes | no | – | 0.00 | stop | -6.44 | -1.02 | 150.00 | -9.65 |
| 2026-09-06 | RAY/USD | kraken | 54.44 | yes | no | – | 1.29 | expired | 36.30 | 1.19 | 49.07 | 17.81 |
| 2026-09-07 | INJ/USD | kraken | 28.31 | no | no | – | 6.17 | stop | -5.25 | -1.14 | 150.00 | -7.88 |
| 2026-09-08 | VVV/USD | kraken | 49.68 | yes | no | – | 25.85 | expired | 26.03 | 0.90 | 51.92 | 13.52 |
| 2026-09-16 | DRV/USD | kraken | 69.99 | yes | yes | 3 | 0.24 | t2 | 67.02 | 3.26 | 72.88 | 48.84 |
| 2026-09-18 | NEAR/USD | kraken | 61.09 | no | no | – | 3.76 | expired | 32.07 | 1.83 | 85.65 | 27.47 |
| 2026-09-19 | AVAX/USD | kraken | 35.14 | yes | no | – | 10.10 | expired | 9.83 | 0.49 | 75.41 | 7.41 |
| 2026-09-19 | INJ/USD | kraken | 46.74 | no | no | – | 7.93 | expired | -3.51 | -0.24 | 102.17 | -3.58 |
| 2026-09-19 | XTZ/USD | kraken | 44.83 | yes | no | – | 0.37 | expired | -12.54 | -0.65 | 77.96 | -9.78 |
| 2026-09-19 | ZAMA/USD | kraken | 71.08 | yes | no | – | 0.08 | expired | 6.99 | 0.28 | 60.23 | 4.21 |
| 2026-09-21 | SUI/USD | kraken | 28.09 | no | no | – | 1.04 | expired | 15.81 | 1.11 | 105.13 | 16.62 |
| 2026-09-21 | TAO/USD | kraken | 27.57 | yes | no | – | 319.37 | expired | -4.57 | -0.29 | 94.63 | -4.32 |
| 2026-09-22 | BCH/USD | kraken | 35.45 | yes | no | – | 345.00 | expired | -9.63 | -0.41 | 64.44 | -6.21 |
| 2026-09-25 | QNT/USD | kraken | 33.71 | no | yes | 1 | 98.68 | t2 | 50.04 | 5.19 | 150.00 | 75.06 |
| 2026-09-26 | WLD/USD | kraken | 28.52 | no | no | – | 0.52 | stop | -6.83 | -1.10 | 150.00 | -10.24 |
| 2026-09-28 | HBAR/USD | kraken | 27.54 | yes | no | – | 0.12 | stop | -19.87 | -1.02 | 77.25 | -15.35 |
| 2026-10-02 | SAND/USD | kraken | 58.12 | yes | pending | – | 0.07 | t1 (open, marked at last bar) | 18.45 | 0.56 | 45.40 | 8.38 |
