# Stage A vs Coinbase top movers

Window 2026-06-30 to 2026-09-27 (90 days), live scanner universe: Kraken top 150 by volume today, 110 of them listed on Coinbase, 110 with data. Mover = top 10 by UTC close-to-close gain that day, gain ≥ 20%. Thresholds as in config.yaml: close > 20-day high, volume ≥ 3.0× 30-day avg, 3-day gain ≥ 25%. Breakout entry: stop 3.0% under level, T1/T2 = 1.0×/2.0× leg.

## Recall — did Stage A alert in the 5 days before a mover day?

- Mover days: **72**. Caught: **13 (18%)**. Missed: 59.
- Lead time on caught movers (days before the mover day): 1d: 3, 2d: 2, 3d: 4, 4d: 3, 5d: 1
- Caught movers' breakout entries: avg R 2.875, avg rule return 47.671%.
- Of the misses, Stage A fired **on the mover day itself** (i.e. after the move) for 35 (59%).
- Misses by failed condition on the D−1 bar:

| why | count | share |
|---|---|---|
| prior-high + volume + 3d-gain | 41 | 69% |
| volume + 3d-gain | 5 | 8% |
| 3d-gain | 4 | 7% |
| prior-high + volume | 2 | 3% |
| volume | 2 | 3% |
| prior-high + 3d-gain | 2 | 3% |
| prior-high | 2 | 3% |
| suppressed (already in play) | 1 | 2% |

Median on D−1 for diagnosable misses: close vs 20-day high -8.1%, volume 1.37×, 3-day gain +8.5%.

## Precision — did alerts become movers within 5 days?

- Alerts in window: **79** (5 too recent to judge).
- Became a mover on A+1..A+5: **8 of 74 (11%)**.
- Alert day itself was already a mover: 34 of 74.
- Avg R per alert, all judged alerts: **0.212** (R known for 74 of 74).
- Avg R — became mover: **3.319**; did not: **-0.164**.
- Alerts that did not become movers (R known for 66): ≤ −1R: 29, −1R to 0: 17, > 0: 20; median -0.62R, worst -1.42R.

## Confusion matrix — every (coin, day) in the window

| | Alert in prior 5 days | No alert |
|---|---|---|
| **Mover that day** | 13 | 59 |
| **Not a mover** | 366 | 9405 |

Recall 18%. Precision per coin-day 3% (differs from per-alert precision above: one alert covers 5 coin-days).

## Caught movers

| day | symbol | gain_pct | alert_day | lead_days | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|
| 2026-07-29 | COTI/USD | 59.63 | 2026-07-27 | 2 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-07-31 | COTI/USD | 20.74 | 2026-07-27 | 4 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-08-21 | ENA/USD | 21.87 | 2026-08-20 | 1 | 0.12 | t2 | 45.09 | 2.46 |
| 2026-08-22 | TRUMP/USD | 27.65 | 2026-08-19 | 3 | 1.79 | t2 | 35.32 | 2.12 |
| 2026-08-30 | HNT/USD | 79.73 | 2026-08-29 | 1 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-01 | USELESS/USD | 24.55 | 2026-08-31 | 1 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | USELESS/USD | 68.66 | 2026-08-31 | 3 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | HNT/USD | 37.58 | 2026-08-29 | 5 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-04 | USELESS/USD | 27.66 | 2026-08-31 | 4 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-05 | ARB/USD | 34.23 | 2026-09-01 | 4 | 0.11 | t2 | 36.94 | 10.63 |
| 2026-09-19 | DRV/USD | 51.35 | 2026-09-16 | 3 | 0.24 | t2 | 67.02 | 3.26 |
| 2026-09-26 | QNT/USD | 53.47 | 2026-09-24 | 2 | 90.08 | t2 | 43.15 | 2.44 |
| 2026-09-27 | QNT/USD | 88.99 | 2026-09-24 | 3 | 90.08 | t2 | 43.15 | 2.44 |

## Missed movers

| day | symbol | gain_pct | why | close_vs_high_pct | vol_mult | gain_3d | fired_on_day |
|---|---|---|---|---|---|---|---|
| 2026-07-12 | BILL/USD | 21.50 | prior-high + volume + 3d-gain | -35.55 | 0.61 | 8.41 | no |
| 2026-07-13 | BILL/USD | 20.74 | prior-high + volume | -21.70 | 2.48 | 30.94 | yes |
| 2026-07-14 | DRV/USD | 32.49 | prior-high + volume + 3d-gain | -11.22 | 1.17 | -1.32 | no |
| 2026-07-19 | PUMP/USD | 20.22 | prior-high + volume + 3d-gain | -6.79 | 0.27 | -1.60 | no |
| 2026-07-23 | BILL/USD | 26.22 | prior-high + volume + 3d-gain | -63.54 | 1.46 | -1.19 | no |
| 2026-07-27 | COTI/USD | 48.65 | prior-high + volume + 3d-gain | -14.94 | 0.67 | 1.37 | yes |
| 2026-07-30 | CAP/USD | 31.30 | prior-high + volume + 3d-gain | -7.87 | 1.29 | 16.84 | no |
| 2026-07-31 | DRV/USD | 24.09 | prior-high + volume + 3d-gain | -50.86 | 0.31 | -10.45 | no |
| 2026-08-12 | COTI/USD | 25.00 | prior-high + volume + 3d-gain | -51.46 | 0.58 | -19.35 | no |
| 2026-08-19 | TRUMP/USD | 27.26 | prior-high + volume + 3d-gain | -8.56 | 1.43 | -0.13 | yes |
| 2026-08-20 | PUMP/USD | 27.71 | prior-high + volume + 3d-gain | -4.09 | 1.31 | 12.68 | no |
| 2026-08-20 | ENA/USD | 25.07 | prior-high + volume + 3d-gain | -4.99 | 1.84 | 13.32 | yes |
| 2026-08-21 | USELESS/USD | 32.11 | prior-high + volume + 3d-gain | -7.74 | 2.80 | 16.09 | yes |
| 2026-08-21 | STX/USD | 29.73 | volume + 3d-gain | 2.81 | 2.27 | 21.01 | yes |
| 2026-08-21 | BCH/USD | 29.12 | 3d-gain | 1.95 | 3.62 | 8.64 | yes |
| 2026-08-21 | ZEC/USD | 29.06 | prior-high + volume + 3d-gain | -1.91 | 2.64 | 10.80 | yes |
| 2026-08-21 | PEPE/USD | 28.04 | 3d-gain | 7.72 | 5.65 | 24.42 | yes |
| 2026-08-21 | PENGU/USD | 24.34 | 3d-gain | 4.03 | 3.91 | 19.30 | yes |
| 2026-08-21 | AAVE/USD | 23.68 | prior-high + volume + 3d-gain | -2.24 | 2.06 | 11.09 | yes |
| 2026-08-21 | WIF/USD | 21.22 | 3d-gain | 10.79 | 11.91 | 19.13 | yes |
| 2026-08-21 | CRV/USD | 20.35 | prior-high + volume + 3d-gain | -0.24 | 2.72 | 18.22 | yes |
| 2026-08-22 | PUMP/USD | 22.35 | volume | 3.26 | 2.60 | 30.99 | yes |
| 2026-08-23 | MORPHO/USD | 25.63 | prior-high + 3d-gain | -8.39 | 3.35 | 4.52 | yes |
| 2026-08-24 | DRV/USD | 25.01 | volume | 3.22 | 2.01 | 32.45 | yes |
| 2026-08-26 | RLS/USD | 26.50 | prior-high + volume + 3d-gain | -22.22 | 0.56 | -2.67 | no |
| 2026-08-26 | CVX/USD | 21.78 | prior-high + volume + 3d-gain | -9.12 | 1.09 | -3.51 | no |
| 2026-08-27 | SKR/USD | 21.71 | prior-high + volume + 3d-gain | -1.37 | 1.10 | 5.38 | no |
| 2026-08-29 | HNT/USD | 68.58 | volume + 3d-gain | 4.22 | 2.63 | 24.78 | yes |
| 2026-08-30 | SKR/USD | 127.49 | prior-high | -12.83 | 3.37 | 30.22 | yes |
| 2026-08-31 | USELESS/USD | 31.57 | prior-high + volume + 3d-gain | -9.06 | 0.88 | -1.39 | yes |
| 2026-08-31 | ARB/USD | 29.44 | prior-high + volume + 3d-gain | -23.08 | 0.83 | -8.38 | no |
| 2026-09-03 | CHIP/USD | 31.09 | prior-high + volume + 3d-gain | -10.35 | 1.19 | 11.16 | no |
| 2026-09-04 | DASH/USD | 31.77 | prior-high + volume + 3d-gain | -4.52 | 1.27 | 5.74 | yes |
| 2026-09-04 | XCN/USD | 21.33 | prior-high + volume + 3d-gain | -14.64 | 2.13 | 5.03 | yes |
| 2026-09-05 | SUSHI/USD | 33.81 | prior-high + volume + 3d-gain | -13.41 | 1.51 | -4.70 | yes |
| 2026-09-06 | RAY/USD | 41.50 | volume + 3d-gain | 6.41 | 2.37 | 13.90 | yes |
| 2026-09-08 | VVV/USD | 40.23 | prior-high + volume + 3d-gain | -1.07 | 1.14 | 1.83 | yes |
| 2026-09-08 | USELESS/USD | 23.75 | suppressed (already in play) | -27.24 | 1.50 | -13.04 | no |
| 2026-09-14 | CAP/USD | 36.27 | prior-high + volume + 3d-gain | -38.06 | 0.26 | 3.63 | no |
| 2026-09-16 | DRV/USD | 77.98 | prior-high + volume + 3d-gain | -31.38 | 1.06 | -8.69 | yes |
| 2026-09-16 | ZEC/USD | 20.57 | prior-high + volume + 3d-gain | -14.55 | 0.96 | -1.24 | no |
| 2026-09-17 | COTI/USD | 46.94 | prior-high + volume + 3d-gain | -21.57 | 1.26 | 8.13 | yes |
| 2026-09-18 | STRK/USD | 53.94 | prior-high + volume + 3d-gain | -15.59 | 0.34 | 0.35 | yes |
| 2026-09-18 | ARB/USD | 24.86 | prior-high + volume | -14.05 | 1.81 | 32.52 | no |
| 2026-09-18 | APT/USD | 22.42 | prior-high + volume + 3d-gain | -13.68 | 0.69 | 1.36 | no |
| 2026-09-19 | ZAMA/USD | 37.27 | prior-high | -5.91 | 3.43 | 28.59 | yes |
| 2026-09-19 | XTZ/USD | 24.09 | prior-high + volume + 3d-gain | -3.21 | 0.99 | 18.39 | yes |
| 2026-09-19 | AVAX/USD | 23.05 | volume + 3d-gain | 0.10 | 2.18 | 12.95 | yes |
| 2026-09-19 | ENA/USD | 21.27 | prior-high + volume + 3d-gain | -10.90 | 0.65 | 20.57 | no |
| 2026-09-21 | TAO/USD | 22.05 | prior-high + volume + 3d-gain | -5.55 | 1.48 | 12.75 | yes |
| 2026-09-21 | WIF/USD | 21.04 | prior-high + volume + 3d-gain | -10.05 | 0.38 | 8.68 | no |
| 2026-09-22 | BCH/USD | 29.15 | prior-high + 3d-gain | -0.92 | 3.03 | 4.58 | yes |
| 2026-09-22 | USELESS/USD | 23.76 | prior-high + volume + 3d-gain | -16.92 | 0.94 | -4.12 | no |
| 2026-09-22 | MINA/USD | 21.57 | volume + 3d-gain | 5.77 | 1.47 | 20.68 | yes |
| 2026-09-24 | QNT/USD | 27.45 | prior-high + volume + 3d-gain | -5.82 | 1.46 | 9.97 | yes |
| 2026-09-24 | ONDO/USD | 26.65 | prior-high + volume + 3d-gain | -11.11 | 1.47 | -4.80 | no |
| 2026-09-24 | XPL/USD | 23.17 | prior-high + volume + 3d-gain | -14.16 | 1.11 | 0.82 | no |
| 2026-09-25 | AERO/USD | 22.06 | prior-high + volume + 3d-gain | -6.83 | 1.00 | -0.46 | no |
| 2026-09-27 | GRT/USD | 30.07 | prior-high + volume + 3d-gain | -4.56 | 1.30 | 10.94 | yes |

## Alerts

| alert_day | symbol | impulse_pct | alert_day_was_mover | became_mover | days_to_mover | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|---|
| 2026-07-13 | BILL/USD | 51.92 | yes | no | – | 0.06 | stop | -8.93 | -1.42 |
| 2026-07-22 | ZAMA/USD | 34.53 | no | no | – | 0.05 | t1 | 14.15 | 0.90 |
| 2026-07-26 | SHIB/USD | 28.33 | no | no | – | 0.00 | stop | -6.60 | -1.27 |
| 2026-07-27 | COTI/USD | 52.78 | yes | yes | 2 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-08-19 | TRUMP/USD | 28.00 | yes | yes | 3 | 1.79 | t2 | 35.32 | 2.12 |
| 2026-08-20 | XRP/USD | 26.49 | no | no | – | 1.27 | expired | 17.92 | 1.37 |
| 2026-08-20 | ENA/USD | 40.29 | yes | yes | 1 | 0.12 | t2 | 45.09 | 2.46 |
| 2026-08-21 | ETH/USD | 31.26 | no | no | – | 2515.80 | expired | -2.52 | -0.28 |
| 2026-08-21 | ZEC/USD | 44.39 | yes | no | – | 734.47 | expired | 35.29 | 1.65 |
| 2026-08-21 | SUI/USD | 29.55 | no | no | – | 0.84 | stop | -15.68 | -1.17 |
| 2026-08-21 | LINK/USD | 25.70 | no | no | – | 11.99 | expired | -3.04 | -0.26 |
| 2026-08-21 | HYPE/USD | 29.11 | no | no | – | 75.54 | expired | 11.62 | 3.15 |
| 2026-08-21 | XLM/USD | 30.38 | no | no | – | 0.20 | stop | -8.67 | -1.12 |
| 2026-08-21 | DOGE/USD | 30.36 | no | no | – | 0.09 | stop | -11.88 | -1.03 |
| 2026-08-21 | ADA/USD | 31.32 | no | no | – | 0.23 | stop | -10.60 | -1.01 |
| 2026-08-21 | ARB/USD | 30.51 | no | no | – | 0.10 | stop | -9.99 | -1.04 |
| 2026-08-21 | PENGU/USD | 47.08 | yes | no | – | 0.01 | expired | -6.95 | -0.34 |
| 2026-08-21 | USELESS/USD | 73.28 | yes | no | – | 0.06 | t2 | 67.38 | 3.28 |
| 2026-08-21 | BCH/USD | 41.44 | yes | no | – | 287.88 | expired | -14.75 | -0.62 |
| 2026-08-21 | PEPE/USD | 59.30 | yes | no | – | 0.00 | expired | -15.09 | -0.66 |
| 2026-08-21 | GRT/USD | 31.29 | no | no | – | 0.02 | expired | -2.76 | -0.18 |
| 2026-08-21 | CRV/USD | 42.40 | yes | no | – | 0.34 | expired | 1.34 | 0.07 |
| 2026-08-21 | MON/USD | 34.97 | no | no | – | 0.03 | stop | -8.40 | -1.13 |
| 2026-08-21 | DOT/USD | 25.16 | no | no | – | 0.94 | stop | -10.27 | -1.00 |
| 2026-08-21 | DASH/USD | 30.12 | no | no | – | 38.75 | t1 | 11.41 | 0.72 |
| 2026-08-21 | FARTCOIN/USD | 39.39 | no | no | – | 0.20 | stop | -14.98 | -1.00 |
| 2026-08-21 | AAVE/USD | 40.12 | yes | no | – | 122.63 | expired | 6.79 | 0.32 |
| 2026-08-21 | VIRTUAL/USD | 26.50 | no | no | – | 0.73 | expired | -8.48 | -0.71 |
| 2026-08-21 | XPL/USD | 33.70 | no | no | – | 0.10 | stop | -15.85 | -1.17 |
| 2026-08-21 | ZRO/USD | 26.46 | no | no | – | 1.00 | t1 | 11.65 | 1.09 |
| 2026-08-21 | BONK/USD | 34.63 | no | no | – | 0.00 | stop | -10.29 | -1.19 |
| 2026-08-21 | FIL/USD | 28.24 | no | no | – | 0.81 | stop | -8.04 | -1.06 |
| 2026-08-21 | LIGHTER/USD | 32.65 | no | no | – | 3.13 | t2 | 41.29 | 5.23 |
| 2026-08-21 | SHIB/USD | 34.24 | no | no | – | 0.00 | stop | -16.55 | -1.07 |
| 2026-08-21 | SPX/USD | 45.34 | no | no | – | 0.46 | expired | 30.27 | 1.84 |
| 2026-08-21 | OP/USD | 30.69 | no | no | – | 0.11 | stop | -12.88 | -1.17 |
| 2026-08-21 | EIGEN/USD | 30.38 | no | no | – | 0.22 | stop | -12.43 | -1.00 |
| 2026-08-21 | STX/USD | 58.17 | yes | no | – | 0.19 | expired | 38.83 | 1.58 |
| 2026-08-21 | TIA/USD | 32.08 | no | no | – | 0.39 | stop | -15.17 | -1.01 |
| 2026-08-21 | WIF/USD | 46.14 | yes | no | – | 0.20 | expired | 2.22 | 0.12 |
| 2026-08-21 | ETC/USD | 37.36 | no | no | – | 8.35 | expired | -10.92 | -0.58 |
| 2026-08-21 | XCN/USD | 36.96 | no | no | – | 0.00 | stop | -13.42 | -1.01 |
| 2026-08-21 | FLR/USD | 29.21 | no | no | – | 0.01 | stop | -10.33 | -1.05 |
| 2026-08-21 | JASMY/USD | 32.47 | no | no | – | 0.00 | stop | -7.59 | -1.23 |
| 2026-08-21 | POPCAT/USD | 29.02 | no | no | – | 0.05 | t1 | 11.53 | 0.92 |
| 2026-08-21 | SYRUP/USD | 31.19 | no | no | – | 0.21 | stop | -13.12 | -1.00 |
| 2026-08-22 | PUMP/USD | 65.33 | yes | no | – | 0.00 | stop | -17.16 | -1.02 |
| 2026-08-22 | POL/USD | 31.10 | no | no | – | 0.11 | stop | -13.40 | -1.01 |
| 2026-08-23 | MORPHO/USD | 25.29 | yes | no | – | 2.90 | stop | -15.72 | -1.00 |
| 2026-08-24 | DRV/USD | 38.04 | yes | no | – | 0.16 | expired | -3.08 | -0.15 |
| 2026-08-27 | VET/USD | 26.27 | no | no | – | 0.01 | stop | -7.42 | -1.04 |
| 2026-08-29 | HNT/USD | 84.15 | yes | yes | 1 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-08-30 | SKR/USD | 143.40 | yes | no | – | 0.03 | expired | -31.19 | -0.61 |
| 2026-08-31 | USELESS/USD | 49.06 | yes | yes | 1 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-01 | ARB/USD | 26.12 | no | yes | 4 | 0.11 | t2 | 36.94 | 10.63 |
| 2026-09-04 | DASH/USD | 42.44 | yes | no | – | 62.59 | t1 | 16.80 | 0.73 |
| 2026-09-04 | XCN/USD | 30.45 | yes | no | – | 0.00 | stop | -6.44 | -1.02 |
| 2026-09-05 | SUSHI/USD | 31.46 | yes | no | – | 0.25 | stop | -16.36 | -1.00 |
| 2026-09-06 | RAY/USD | 54.44 | yes | no | – | 1.29 | expired | 36.30 | 1.19 |
| 2026-09-07 | INJ/USD | 28.31 | no | no | – | 6.17 | stop | -5.25 | -1.14 |
| 2026-09-08 | VVV/USD | 49.68 | yes | no | – | 25.85 | expired | 26.03 | 0.90 |
| 2026-09-16 | DRV/USD | 69.99 | yes | yes | 3 | 0.24 | t2 | 67.02 | 3.26 |
| 2026-09-17 | COTI/USD | 51.55 | yes | no | – | 0.03 | stop | -16.68 | -1.05 |
| 2026-09-18 | NEAR/USD | 61.09 | no | no | – | 3.76 | t1 (open, marked at last bar) | 35.25 | 2.01 |
| 2026-09-18 | STRK/USD | 67.22 | yes | no | – | 0.04 | expired (open, marked at last bar) | -8.50 | -0.34 |
| 2026-09-19 | AVAX/USD | 35.14 | yes | no | – | 10.10 | expired (open, marked at last bar) | 3.47 | 0.17 |
| 2026-09-19 | INJ/USD | 46.74 | no | no | – | 7.93 | expired (open, marked at last bar) | -7.26 | -0.49 |
| 2026-09-19 | ZAMA/USD | 71.08 | yes | no | – | 0.08 | expired (open, marked at last bar) | -3.65 | -0.15 |
| 2026-09-19 | XTZ/USD | 44.83 | yes | no | – | 0.37 | expired (open, marked at last bar) | -14.89 | -0.77 |
| 2026-09-21 | SUI/USD | 28.09 | no | no | – | 1.04 | expired (open, marked at last bar) | 11.63 | 0.81 |
| 2026-09-21 | TAO/USD | 27.57 | yes | no | – | 319.37 | expired (open, marked at last bar) | -5.14 | -0.33 |
| 2026-09-22 | BCH/USD | 35.45 | yes | no | – | 345.00 | expired (open, marked at last bar) | -10.12 | -0.43 |
| 2026-09-22 | MINA/USD | 48.10 | yes | no | – | 0.16 | expired (open, marked at last bar) | -8.46 | -0.54 |
| 2026-09-23 | ZRO/USD | 27.44 | no | pending | – | 1.50 | expired (open, marked at last bar) | 2.29 | 0.33 |
| 2026-09-23 | XCN/USD | 27.70 | no | pending | – | 0.01 | expired (open, marked at last bar) | -8.07 | -0.79 |
| 2026-09-24 | QNT/USD | 34.81 | yes | yes | 2 | 90.08 | t2 | 43.15 | 2.44 |
| 2026-09-26 | WLD/USD | 28.52 | no | pending | – | 0.52 | stop | -6.83 | -1.10 |
| 2026-09-27 | GRT/USD | 36.79 | yes | pending | – | 0.04 | expired (open, marked at last bar) | -13.17 | -0.60 |
| 2026-09-27 | W/USD | 32.42 | no | pending | – | 0.02 | expired (open, marked at last bar) | -11.55 | -0.66 |
