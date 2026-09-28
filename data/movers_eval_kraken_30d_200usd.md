# Stage A vs Coinbase top movers

Window 2026-08-29 to 2026-09-27 (30 days), live scanner universe: Kraken top 150 by volume today, 110 of them listed on Coinbase, 110 with data. Mover = top 10 by UTC close-to-close gain that day, gain ≥ 20%. Thresholds as in config.yaml: close > 20-day high, volume ≥ 3.0× 30-day avg, 3-day gain ≥ 25%. Breakout entry: stop 3.0% under level, T1/T2 = 1.0×/2.0× leg.

## Recall — did Stage A alert in the 5 days before a mover day?

- Mover days: **41**. Caught: **9 (22%)**. Missed: 32.
- Lead time on caught movers (days before the mover day): 1d: 2, 2d: 1, 3d: 3, 4d: 2, 5d: 1
- Caught movers' breakout entries: avg R 3.484, avg rule return 56.186%.
- Of the misses, Stage A fired **on the mover day itself** (i.e. after the move) for 19 (59%).
- Misses by failed condition on the D−1 bar:

| why | count | share |
|---|---|---|
| prior-high + volume + 3d-gain | 23 | 72% |
| volume + 3d-gain | 4 | 12% |
| prior-high | 2 | 6% |
| suppressed (already in play) | 1 | 3% |
| prior-high + volume | 1 | 3% |
| prior-high + 3d-gain | 1 | 3% |

Median on D−1 for diagnosable misses: close vs 20-day high -10.3%, volume 1.26×, 3-day gain +5.7%.

## Precision — did alerts become movers within 5 days?

- Alerts in window: **29** (6 too recent to judge).
- Became a mover on A+1..A+5: **5 of 23 (22%)**.
- Alert day itself was already a mover: 18 of 23.
- Avg R per alert, all judged alerts: **0.835** (R known for 23 of 23).
- Dollars at $200 capital (5% risk, 50% cap), no fees: total **$132.53** over 23 trades, avg $5.762/alert; became mover $143.19, did not $-10.66. Each alert is traded independently, so overlapping positions can exceed capital.
- Avg R — became mover: **4.251**; did not: **-0.114**.
- Alerts that did not become movers (R known for 18): ≤ −1R: 4, −1R to 0: 8, > 0: 6; median -0.39R, worst -1.14R.

## Confusion matrix — every (coin, day) in the window

| | Alert in prior 5 days | No alert |
|---|---|---|
| **Mover that day** | 9 | 32 |
| **Not a mover** | 122 | 3137 |

Recall 22%. Precision per coin-day 7% (differs from per-alert precision above: one alert covers 5 coin-days).

## Caught movers

| day | symbol | gain_pct | alert_day | lead_days | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|
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

| alert_day | symbol | impulse_pct | alert_day_was_mover | became_mover | days_to_mover | entry | trade | rule_return | r_multiple | position_usd | pnl_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-29 | HNT/USD | 84.15 | yes | yes | 1 | 0.43 | t2 | 80.02 | 2.20 | 27.44 | 21.96 |
| 2026-08-30 | SKR/USD | 143.40 | yes | no | – | 0.03 | expired | -31.19 | -0.61 | 19.57 | -6.10 |
| 2026-08-31 | USELESS/USD | 49.06 | yes | yes | 1 | 0.09 | t2 | 51.80 | 2.74 | 52.82 | 27.36 |
| 2026-09-01 | ARB/USD | 26.12 | no | yes | 4 | 0.11 | t2 | 36.94 | 10.63 | 100.00 | 36.94 |
| 2026-09-04 | DASH/USD | 42.44 | yes | no | – | 62.59 | t1 | 16.80 | 0.73 | 43.67 | 7.34 |
| 2026-09-04 | XCN/USD | 30.45 | yes | no | – | 0.00 | stop | -6.44 | -1.02 | 100.00 | -6.44 |
| 2026-09-05 | SUSHI/USD | 31.46 | yes | no | – | 0.25 | stop | -16.36 | -1.00 | 61.42 | -10.05 |
| 2026-09-06 | RAY/USD | 54.44 | yes | no | – | 1.29 | expired | 36.30 | 1.19 | 32.72 | 11.88 |
| 2026-09-07 | INJ/USD | 28.31 | no | no | – | 6.17 | stop | -5.25 | -1.14 | 100.00 | -5.25 |
| 2026-09-08 | VVV/USD | 49.68 | yes | no | – | 25.85 | expired | 26.03 | 0.90 | 34.61 | 9.01 |
| 2026-09-16 | DRV/USD | 69.99 | yes | yes | 3 | 0.24 | t2 | 67.02 | 3.26 | 48.59 | 32.57 |
| 2026-09-17 | COTI/USD | 51.55 | yes | no | – | 0.03 | stop | -16.68 | -1.05 | 63.19 | -10.54 |
| 2026-09-18 | NEAR/USD | 61.09 | no | no | – | 3.76 | t1 (open, marked at last bar) | 35.25 | 2.01 | 57.10 | 20.13 |
| 2026-09-18 | STRK/USD | 67.22 | yes | no | – | 0.04 | expired (open, marked at last bar) | -8.50 | -0.34 | 39.45 | -3.35 |
| 2026-09-19 | AVAX/USD | 35.14 | yes | no | – | 10.10 | expired (open, marked at last bar) | 3.47 | 0.17 | 50.28 | 1.74 |
| 2026-09-19 | INJ/USD | 46.74 | no | no | – | 7.93 | expired (open, marked at last bar) | -7.26 | -0.49 | 68.11 | -4.95 |
| 2026-09-19 | ZAMA/USD | 71.08 | yes | no | – | 0.08 | expired (open, marked at last bar) | -3.65 | -0.15 | 40.16 | -1.47 |
| 2026-09-19 | XTZ/USD | 44.83 | yes | no | – | 0.37 | expired (open, marked at last bar) | -14.89 | -0.77 | 51.97 | -7.74 |
| 2026-09-21 | SUI/USD | 28.09 | no | no | – | 1.04 | expired (open, marked at last bar) | 11.63 | 0.81 | 70.09 | 8.15 |
| 2026-09-21 | TAO/USD | 27.57 | yes | no | – | 319.37 | expired (open, marked at last bar) | -5.14 | -0.33 | 63.09 | -3.25 |
| 2026-09-22 | BCH/USD | 35.45 | yes | no | – | 345.00 | expired (open, marked at last bar) | -10.12 | -0.43 | 42.96 | -4.35 |
| 2026-09-22 | MINA/USD | 48.10 | yes | no | – | 0.16 | expired (open, marked at last bar) | -8.46 | -0.54 | 64.04 | -5.42 |
| 2026-09-23 | ZRO/USD | 27.44 | no | pending | – | 1.50 | expired (open, marked at last bar) | 2.29 | 0.33 | 100.00 | 2.29 |
| 2026-09-23 | XCN/USD | 27.70 | no | pending | – | 0.01 | expired (open, marked at last bar) | -8.07 | -0.79 | 97.31 | -7.85 |
| 2026-09-23 | SUPER/USD | 25.37 | no | pending | – | 0.18 | expired (open, marked at last bar) | 8.81 | 1.21 | 100.00 | 8.81 |
| 2026-09-24 | QNT/USD | 34.81 | yes | yes | 2 | 90.08 | t2 | 43.15 | 2.44 | 56.47 | 24.36 |
| 2026-09-26 | WLD/USD | 28.52 | no | pending | – | 0.52 | stop | -6.83 | -1.10 | 100.00 | -6.83 |
| 2026-09-27 | GRT/USD | 36.79 | yes | pending | – | 0.04 | expired (open, marked at last bar) | -13.17 | -0.60 | 45.74 | -6.02 |
| 2026-09-27 | W/USD | 32.42 | no | pending | – | 0.02 | expired (open, marked at last bar) | -11.55 | -0.66 | 57.07 | -6.59 |
