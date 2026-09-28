# Stage A vs Coinbase top movers

Window 2026-06-30 to 2026-09-27 (90 days), 401 Coinbase USD pairs. Mover = top 10 by UTC close-to-close gain that day, gain ≥ 20%. Thresholds as in config.yaml: close > 20-day high, volume ≥ 3.0× 30-day avg, 3-day gain ≥ 25%. Breakout entry: stop 3.0% under level, T1/T2 = 1.0×/2.0× leg.

## Recall — did Stage A alert in the 5 days before a mover day?

- Mover days: **323**. Caught: **53 (16%)**. Missed: 270.
- Lead time on caught movers (days before the mover day): 1d: 15, 2d: 9, 3d: 13, 4d: 11, 5d: 5
- Caught movers' breakout entries: avg R 1.84, avg rule return 26.719%.
- Of the misses, Stage A fired **on the mover day itself** (i.e. after the move) for 144 (53%).
- Misses by failed condition on the D−1 bar:

| why | count | share |
|---|---|---|
| prior-high + volume + 3d-gain | 213 | 79% |
| prior-high + 3d-gain | 17 | 6% |
| volume + 3d-gain | 10 | 4% |
| not enough history | 8 | 3% |
| 3d-gain | 7 | 3% |
| prior-high + volume | 6 | 2% |
| prior-high | 4 | 1% |
| suppressed (already in play) | 3 | 1% |
| volume | 2 | 1% |

Median on D−1 for diagnosable misses: close vs 20-day high -16.9%, volume 1.00×, 3-day gain +1.7%.

## Precision — did alerts become movers within 5 days?

- Alerts in window: **237** (18 too recent to judge).
- Became a mover on A+1..A+5: **39 of 219 (18%)**.
- Alert day itself was already a mover: 137 of 219.
- Avg R — became mover: **1.86**; did not: **-0.414**.
- Alerts that did not become movers (R known for 180): ≤ −1R: 96, −1R to 0: 43, > 0: 41; median -1.00R, worst -3.04R.

## Confusion matrix — every (coin, day) in the window

| | Alert in prior 5 days | No alert |
|---|---|---|
| **Mover that day** | 53 | 270 |
| **Not a mover** | 1082 | 34289 |

Recall 16%. Precision per coin-day 5% (differs from per-alert precision above: one alert covers 5 coin-days).

## Caught movers

| day | symbol | gain_pct | alert_day | lead_days | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|
| 2026-07-03 | NOM/USD | 29.48 | 2026-07-01 | 2 | 0.00 | stop | -10.20 | -1.21 |
| 2026-07-04 | MPLX/USD | 37.14 | 2026-07-03 | 1 | 0.04 | t1 | 24.27 | 0.53 |
| 2026-07-04 | RPL/USD | 29.94 | 2026-07-02 | 2 | 2.07 | stop | -22.22 | -1.17 |
| 2026-07-17 | OXT/USD | 135.21 | 2026-07-16 | 1 | 0.01 | t2 | 73.94 | 4.83 |
| 2026-07-20 | OXT/USD | 23.93 | 2026-07-16 | 4 | 0.01 | t2 | 73.94 | 4.83 |
| 2026-07-21 | 00/USD | 37.10 | 2026-07-20 | 1 | 0.01 | t2 | 58.06 | 1.62 |
| 2026-07-29 | COTI/USD | 59.63 | 2026-07-27 | 2 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-07-31 | COTI/USD | 20.74 | 2026-07-27 | 4 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-08-01 | META/USD | 46.61 | 2026-07-29 | 3 | 5.17 | stop | -7.05 | -1.45 |
| 2026-08-02 | FORTH/USD | 23.94 | 2026-07-30 | 3 | 0.31 | stop | -35.80 | -1.05 |
| 2026-08-04 | BICO/USD | 25.98 | 2026-08-02 | 2 | 0.02 | t2 | 45.65 | 3.61 |
| 2026-08-05 | HFT/USD | 56.03 | 2026-08-04 | 1 | 0.01 | t2 | 63.36 | 6.54 |
| 2026-08-05 | BICO/USD | 29.06 | 2026-08-02 | 3 | 0.02 | t2 | 45.65 | 3.61 |
| 2026-08-06 | HFT/USD | 66.85 | 2026-08-04 | 2 | 0.01 | t2 | 63.36 | 6.54 |
| 2026-08-06 | BICO/USD | 43.22 | 2026-08-02 | 4 | 0.02 | t2 | 45.65 | 3.61 |
| 2026-08-07 | BICO/USD | 39.62 | 2026-08-02 | 5 | 0.02 | t2 | 45.65 | 3.61 |
| 2026-08-08 | COOKIE/USD | 39.96 | 2026-08-06 | 2 | 0.01 | stop | -11.34 | -1.08 |
| 2026-08-10 | GWEI/USD | 24.39 | 2026-08-07 | 3 | 0.03 | stop | -7.63 | -1.33 |
| 2026-08-13 | IMU/USD | 44.55 | 2026-08-08 | 5 | 0.00 | stop | -51.93 | -1.00 |
| 2026-08-16 | APR/USD | 22.14 | 2026-08-12 | 4 | 0.58 | stop | -61.55 | -1.02 |
| 2026-08-22 | TRUMP/USD | 27.65 | 2026-08-19 | 3 | 1.79 | t2 | 35.32 | 2.12 |
| 2026-08-23 | KEYCAT/USD | 30.18 | 2026-08-21 | 2 | 0.00 | stop | -9.25 | -1.04 |
| 2026-08-23 | SPK/USD | 29.68 | 2026-08-21 | 2 | 0.02 | expired | 19.99 | 2.03 |
| 2026-08-24 | KEYCAT/USD | 33.44 | 2026-08-21 | 3 | 0.00 | stop | -9.25 | -1.04 |
| 2026-08-25 | MDT/USD | 180.07 | 2026-08-24 | 1 | 0.01 | t2 | 70.67 | 2.19 |
| 2026-08-26 | HONEY/USD | 29.36 | 2026-08-25 | 1 | 0.00 | t2 | 49.30 | 3.07 |
| 2026-08-27 | BLZ/USD | 26.38 | 2026-08-23 | 4 | 0.01 | t2 | 42.25 | 3.15 |
| 2026-08-28 | HONEY/USD | 31.30 | 2026-08-25 | 3 | 0.00 | t2 | 49.30 | 3.07 |
| 2026-08-28 | MDT/USD | 27.74 | 2026-08-24 | 4 | 0.01 | t2 | 70.67 | 2.19 |
| 2026-08-30 | HNT/USD | 79.73 | 2026-08-29 | 1 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-01 | USELESS/USD | 24.55 | 2026-08-31 | 1 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | USELESS/USD | 68.66 | 2026-08-31 | 3 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-03 | HNT/USD | 37.58 | 2026-08-29 | 5 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-09-03 | EDGEX/USD | 36.20 | 2026-09-02 | 1 | 0.45 | t2 | 33.22 | 3.17 |
| 2026-09-04 | FLOCK/USD | 32.83 | 2026-08-31 | 4 | 0.04 | stop | -13.78 | -1.19 |
| 2026-09-04 | USELESS/USD | 27.66 | 2026-08-31 | 4 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-09-05 | ARB/USD | 34.23 | 2026-09-01 | 4 | 0.11 | t2 | 36.94 | 10.63 |
| 2026-09-05 | FLOCK/USD | 22.94 | 2026-08-31 | 5 | 0.04 | stop | -13.78 | -1.19 |
| 2026-09-06 | RNBW/USD | 32.72 | 2026-09-05 | 1 | 0.02 | t1 | 21.63 | 0.84 |
| 2026-09-13 | SYND/USD | 42.32 | 2026-09-10 | 3 | 0.01 | stop | -38.93 | -1.01 |
| 2026-09-19 | DRV/USD | 51.35 | 2026-09-16 | 3 | 0.24 | t2 | 67.02 | 3.26 |
| 2026-09-19 | G/USD | 39.48 | 2026-09-18 | 1 | 0.01 | t2 | 73.68 | 2.51 |
| 2026-09-21 | AURORA/USD | 181.71 | 2026-09-18 | 3 | 0.02 | stop | -16.41 | -1.01 |
| 2026-09-22 | AURORA/USD | 67.65 | 2026-09-18 | 4 | 0.02 | stop | -16.41 | -1.01 |
| 2026-09-22 | DRIFT/USD | 35.07 | 2026-09-17 | 5 | 0.02 | t2 | 41.38 | 2.52 |
| 2026-09-24 | ALEO/USD | 78.21 | 2026-09-23 | 1 | 0.02 | t2 | 56.02 | 1.91 |
| 2026-09-24 | NEON/USD | 47.33 | 2026-09-23 | 1 | 0.06 | t1 (open, marked at last bar) | 38.85 | 0.52 |
| 2026-09-24 | DBR/USD | 25.79 | 2026-09-23 | 1 | 0.02 | t1 (open, marked at last bar) | 12.47 | 0.65 |
| 2026-09-25 | VARA/USD | 34.36 | 2026-09-21 | 4 | 0.00 | t1 (open, marked at last bar) | 12.87 | 0.67 |
| 2026-09-25 | CTX/USD | 27.54 | 2026-09-24 | 1 | 0.54 | t2 | 38.26 | 11.65 |
| 2026-09-25 | MPLX/USD | 21.40 | 2026-09-22 | 3 | 0.06 | expired (open, marked at last bar) | -3.09 | -0.10 |
| 2026-09-26 | QNT/USD | 53.47 | 2026-09-24 | 2 | 90.08 | t2 | 43.15 | 2.44 |
| 2026-09-27 | QNT/USD | 88.99 | 2026-09-24 | 3 | 90.08 | t2 | 43.15 | 2.44 |

## Missed movers

| day | symbol | gain_pct | why | close_vs_high_pct | vol_mult | gain_3d | fired_on_day |
|---|---|---|---|---|---|---|---|
| 2026-06-30 | CHECK/USD | 49.12 | prior-high + volume + 3d-gain | -64.19 | 0.69 | -9.55 | no |
| 2026-06-30 | BASED1/USD | 23.80 | prior-high + volume + 3d-gain | -26.27 | 0.87 | 21.23 | no |
| 2026-07-01 | POND/USD | 68.09 | prior-high + volume + 3d-gain | -49.73 | 0.28 | -6.93 | no |
| 2026-07-01 | ELA/USD | 53.11 | prior-high + volume + 3d-gain | -19.31 | 2.38 | -9.23 | yes |
| 2026-07-01 | MEZO/USD | 48.99 | prior-high + volume + 3d-gain | -29.19 | 1.05 | -9.95 | no |
| 2026-07-01 | NOM/USD | 47.37 | prior-high + volume + 3d-gain | -28.11 | 0.38 | -4.32 | yes |
| 2026-07-01 | ALCX/USD | 35.45 | prior-high + volume + 3d-gain | -43.88 | 1.70 | -15.06 | no |
| 2026-07-01 | BASED1/USD | 30.18 | prior-high + volume | -8.73 | 1.93 | 33.87 | yes |
| 2026-07-01 | FLUID/USD | 27.48 | prior-high + volume + 3d-gain | -34.24 | 1.93 | -9.03 | no |
| 2026-07-01 | HFT/USD | 25.64 | prior-high + volume + 3d-gain | -33.33 | 2.99 | -7.14 | no |
| 2026-07-02 | BIRB/USD | 67.64 | prior-high + volume + 3d-gain | -36.32 | 0.57 | -11.20 | yes |
| 2026-07-02 | ALLO/USD | 49.74 | prior-high + volume + 3d-gain | -52.18 | 0.14 | -24.06 | no |
| 2026-07-02 | RPL/USD | 39.86 | prior-high + volume + 3d-gain | -14.45 | 1.35 | 5.71 | yes |
| 2026-07-02 | BREV/USD | 24.93 | prior-high + volume + 3d-gain | -26.39 | 0.30 | -1.38 | no |
| 2026-07-03 | MPLX/USD | 80.38 | volume + 3d-gain | 1.46 | 0.48 | 6.09 | yes |
| 2026-07-03 | NEX/USD | 52.97 | prior-high + volume + 3d-gain | -44.78 | 0.11 | -1.60 | no |
| 2026-07-03 | ZKP/USD | 32.28 | prior-high + volume + 3d-gain | -31.45 | 1.87 | 0.65 | no |
| 2026-07-03 | ARPA/USD | 28.75 | prior-high + volume + 3d-gain | -16.67 | 0.88 | 1.27 | yes |
| 2026-07-03 | L3/USD | 23.61 | prior-high + 3d-gain | -30.58 | 7.80 | -10.63 | no |
| 2026-07-05 | SYND/USD | 30.40 | prior-high + volume + 3d-gain | -67.87 | 0.29 | -11.97 | no |
| 2026-07-06 | YFI/USD | 43.88 | prior-high + volume + 3d-gain | -12.11 | 0.36 | 5.54 | yes |
| 2026-07-06 | BLUR/USD | 40.13 | prior-high + volume + 3d-gain | -20.83 | 0.52 | 1.33 | yes |
| 2026-07-06 | TRIA/USD | 35.56 | prior-high + volume + 3d-gain | -28.94 | 0.87 | 19.54 | no |
| 2026-07-06 | EDGEX/USD | 29.83 | prior-high + volume + 3d-gain | -43.94 | 0.72 | -10.34 | no |
| 2026-07-07 | EDGEX/USD | 25.85 | prior-high + 3d-gain | -27.22 | 3.08 | 19.56 | no |
| 2026-07-07 | SPELL/USD | 21.12 | prior-high + volume + 3d-gain | -43.17 | 1.02 | -2.31 | no |
| 2026-07-08 | PERP/USD | 23.12 | prior-high + volume + 3d-gain | -16.22 | 0.55 | -2.11 | no |
| 2026-07-09 | BASED1/USD | 27.78 | prior-high + volume + 3d-gain | -36.75 | 0.79 | -5.63 | no |
| 2026-07-09 | SENT/USD | 23.30 | prior-high + volume + 3d-gain | -21.29 | 0.13 | -4.87 | no |
| 2026-07-09 | SKL/USD | 22.86 | prior-high + volume + 3d-gain | -18.60 | 0.13 | -5.41 | no |
| 2026-07-10 | PYR/USD | 46.46 | prior-high + volume + 3d-gain | -36.50 | 1.45 | -20.13 | no |
| 2026-07-11 | T/USD | 39.47 | prior-high + volume + 3d-gain | -15.56 | 0.84 | -0.29 | yes |
| 2026-07-11 | SXT/USD | 33.80 | prior-high + volume + 3d-gain | -13.41 | 0.54 | 7.58 | yes |
| 2026-07-12 | BLAST/USD | 35.71 | prior-high + volume + 3d-gain | -24.32 | 0.19 | 3.70 | yes |
| 2026-07-12 | BILL/USD | 21.50 | prior-high + volume + 3d-gain | -35.55 | 0.61 | 8.41 | no |
| 2026-07-13 | ALLO/USD | 26.91 | prior-high + volume + 3d-gain | -20.39 | 0.54 | -14.70 | no |
| 2026-07-13 | BILL/USD | 20.74 | prior-high + volume | -21.70 | 2.48 | 30.94 | yes |
| 2026-07-14 | DRV/USD | 32.49 | prior-high + volume + 3d-gain | -11.22 | 1.17 | -1.32 | no |
| 2026-07-14 | B3/USD | 31.80 | prior-high + volume + 3d-gain | -24.24 | 0.62 | 1.01 | no |
| 2026-07-15 | HOME/USD | 32.48 | prior-high + volume + 3d-gain | -38.29 | 0.56 | -6.23 | no |
| 2026-07-16 | OXT/USD | 86.84 | prior-high + volume + 3d-gain | -39.68 | 0.11 | 0.00 | yes |
| 2026-07-16 | BOBBOB/USD | 32.65 | prior-high + volume + 3d-gain | -25.62 | 0.77 | -17.41 | no |
| 2026-07-17 | NKN/USD | 126.00 | prior-high + volume + 3d-gain | -20.63 | 0.27 | -3.85 | yes |
| 2026-07-17 | SUKU/USD | 40.48 | prior-high + volume + 3d-gain | -30.00 | 0.70 | -2.33 | no |
| 2026-07-18 | HONEY/USD | 43.56 | prior-high + 3d-gain | -41.28 | 3.68 | -16.53 | no |
| 2026-07-19 | GHST/USD | 22.34 | prior-high + 3d-gain | -22.65 | 3.22 | -11.00 | no |
| 2026-07-19 | PUMP/USD | 20.22 | prior-high + volume + 3d-gain | -6.79 | 0.27 | -1.60 | no |
| 2026-07-20 | 00/USD | 55.00 | prior-high + volume + 3d-gain | -2.44 | 0.43 | 5.26 | yes |
| 2026-07-20 | POND/USD | 28.38 | prior-high + volume + 3d-gain | -73.48 | 0.26 | -2.63 | no |
| 2026-07-21 | ERA/USD | 44.39 | prior-high + volume + 3d-gain | -32.01 | 2.54 | -9.70 | no |
| 2026-07-21 | BAL/USD | 27.06 | prior-high + volume + 3d-gain | -27.41 | 1.36 | -0.98 | no |
| 2026-07-21 | IMU/USD | 24.07 | prior-high + volume + 3d-gain | -30.77 | 0.49 | 0.93 | no |
| 2026-07-21 | HIGH/USD | 21.36 | prior-high + 3d-gain | -44.05 | 3.61 | 1.78 | no |
| 2026-07-22 | GST/USD | 23.12 | prior-high + volume + 3d-gain | -13.17 | 1.94 | 1.81 | yes |
| 2026-07-22 | RE/USD | 20.12 | prior-high + volume + 3d-gain | -47.63 | 0.41 | 0.15 | no |
| 2026-07-23 | ELA/USD | 29.88 | prior-high + volume + 3d-gain | -49.19 | 0.35 | -8.39 | no |
| 2026-07-23 | BILL/USD | 26.22 | prior-high + volume + 3d-gain | -63.54 | 1.46 | -1.19 | no |
| 2026-07-24 | GWEI/USD | 30.43 | prior-high + volume + 3d-gain | -87.04 | 2.50 | -28.63 | no |
| 2026-07-24 | OXT/USD | 20.93 | prior-high + volume + 3d-gain | -65.78 | 0.60 | -11.03 | no |
| 2026-07-25 | EUL/USD | 78.82 | volume + 3d-gain | 0.74 | 2.44 | 7.10 | yes |
| 2026-07-25 | QI/USD | 37.51 | prior-high + volume + 3d-gain | -27.28 | 0.42 | -9.38 | yes |
| 2026-07-25 | REQ/USD | 26.27 | prior-high + volume + 3d-gain | -17.62 | 0.45 | -3.35 | no |
| 2026-07-26 | ESP/USD | 46.91 | prior-high + volume + 3d-gain | -3.20 | 1.39 | 2.06 | yes |
| 2026-07-26 | TROLL/USD | 38.91 | prior-high + volume + 3d-gain | -41.52 | 1.07 | -4.97 | no |
| 2026-07-26 | KAIO/USD | 31.60 | prior-high + volume + 3d-gain | -54.73 | 1.12 | 0.08 | no |
| 2026-07-26 | THQ/USD | 29.34 | prior-high + volume + 3d-gain | -35.69 | 0.19 | -4.81 | no |
| 2026-07-26 | DIA/USD | 28.11 | prior-high + 3d-gain | -3.36 | 12.58 | 5.65 | yes |
| 2026-07-26 | SAFE/USD | 25.88 | prior-high + volume + 3d-gain | -31.37 | 0.20 | -6.45 | no |
| 2026-07-27 | BOBBOB/USD | 52.43 | prior-high + volume + 3d-gain | -32.73 | 1.67 | -6.33 | yes |
| 2026-07-27 | COTI/USD | 48.65 | prior-high + volume + 3d-gain | -14.94 | 0.67 | 1.37 | yes |
| 2026-07-27 | 00/USD | 22.89 | prior-high + volume + 3d-gain | -31.97 | 0.55 | 9.21 | no |
| 2026-07-29 | META/USD | 22.87 | prior-high + volume + 3d-gain | -17.02 | 0.32 | -3.73 | yes |
| 2026-07-30 | FORTH/USD | 82.42 | prior-high + volume + 3d-gain | -19.33 | 0.26 | 1.33 | yes |
| 2026-07-30 | CAP/USD | 31.30 | prior-high + volume + 3d-gain | -7.87 | 1.29 | 16.84 | no |
| 2026-07-30 | ROBO/USD | 26.75 | prior-high + volume + 3d-gain | -18.19 | 1.43 | -3.75 | yes |
| 2026-07-31 | WMTX/USD | 113.31 | prior-high + volume + 3d-gain | -25.70 | 1.62 | -2.60 | yes |
| 2026-07-31 | GODS/USD | 45.67 | prior-high + volume + 3d-gain | -24.37 | 0.25 | -6.52 | yes |
| 2026-07-31 | DRV/USD | 24.09 | prior-high + volume + 3d-gain | -50.86 | 0.31 | -10.45 | no |
| 2026-08-01 | BLZ/USD | 37.64 | prior-high + volume + 3d-gain | -22.07 | 0.33 | 2.00 | yes |
| 2026-08-02 | BICO/USD | 37.61 | prior-high + volume + 3d-gain | -19.31 | 0.23 | 1.74 | yes |
| 2026-08-03 | 00/USD | 24.42 | prior-high + volume + 3d-gain | -37.23 | 0.22 | -18.87 | no |
| 2026-08-04 | HFT/USD | 24.73 | prior-high + 3d-gain | -13.89 | 10.51 | 6.90 | yes |
| 2026-08-04 | META/USD | 20.45 | prior-high + volume + 3d-gain | -35.27 | 1.00 | 13.02 | no |
| 2026-08-06 | PYR/USD | 46.27 | prior-high + volume + 3d-gain | -54.11 | 1.56 | -5.63 | no |
| 2026-08-06 | CTSI/USD | 42.13 | prior-high + volume + 3d-gain | -13.60 | 0.32 | 1.89 | yes |
| 2026-08-06 | STG/USD | 28.71 | prior-high + volume + 3d-gain | -19.36 | 0.28 | 2.36 | yes |
| 2026-08-06 | GWEI/USD | 25.92 | prior-high + volume + 3d-gain | -61.09 | 0.54 | 2.40 | no |
| 2026-08-06 | COOKIE/USD | 25.48 | prior-high + volume + 3d-gain | -13.64 | 1.53 | 7.73 | yes |
| 2026-08-07 | GWEI/USD | 55.80 | prior-high + volume | -43.28 | 1.55 | 32.88 | yes |
| 2026-08-07 | C98/USD | 21.90 | prior-high + volume + 3d-gain | -1.44 | 1.80 | 8.73 | yes |
| 2026-08-08 | IMU/USD | 235.34 | prior-high + volume + 3d-gain | -39.90 | 0.43 | -10.77 | yes |
| 2026-08-08 | DIMO/USD | 35.49 | prior-high + volume + 3d-gain | -4.93 | 1.01 | 1.48 | yes |
| 2026-08-08 | 00/USD | 22.62 | prior-high + volume + 3d-gain | -38.69 | 0.41 | -23.64 | no |
| 2026-08-09 | XAN/USD | 53.97 | prior-high + volume + 3d-gain | -3.08 | 0.79 | 5.08 | yes |
| 2026-08-10 | RAD/USD | 30.33 | prior-high + volume + 3d-gain | -2.76 | 2.16 | 1.93 | yes |
| 2026-08-10 | SQD/USD | 23.55 | volume + 3d-gain | 0.28 | 0.20 | 6.49 | yes |
| 2026-08-11 | NOICE/USD | 39.81 | prior-high + volume + 3d-gain | -23.70 | 0.23 | 4.04 | yes |
| 2026-08-11 | GODS/USD | 23.79 | prior-high + volume + 3d-gain | -47.85 | 0.48 | -0.48 | no |
| 2026-08-12 | APR/USD | 179.34 | prior-high + volume + 3d-gain | -12.70 | 0.30 | 0.19 | yes |
| 2026-08-12 | COTI/USD | 25.00 | prior-high + volume + 3d-gain | -51.46 | 0.58 | -19.35 | no |
| 2026-08-14 | ALICE/USD | 41.38 | prior-high + volume + 3d-gain | -12.12 | 0.11 | -4.92 | yes |
| 2026-08-15 | FUN1/USD | 49.11 | prior-high + volume + 3d-gain | -10.69 | 1.83 | -1.19 | yes |
| 2026-08-15 | COW/USD | 38.17 | prior-high + volume + 3d-gain | -26.32 | 0.48 | -2.49 | yes |
| 2026-08-17 | 00/USD | 41.53 | prior-high + volume + 3d-gain | -13.87 | 0.44 | 19.19 | no |
| 2026-08-18 | PRCL/USD | 120.00 | prior-high + volume + 3d-gain | -43.04 | 1.36 | 0.00 | yes |
| 2026-08-19 | RE/USD | 35.13 | prior-high + volume + 3d-gain | -25.10 | 0.21 | -13.69 | no |
| 2026-08-19 | OCEAN/USD | 29.37 | prior-high + 3d-gain | -6.36 | 21.45 | 7.29 | no |
| 2026-08-19 | TRUMP/USD | 27.26 | prior-high + volume + 3d-gain | -8.56 | 1.43 | -0.13 | yes |
| 2026-08-19 | MOG/USD | 22.22 | prior-high + volume + 3d-gain | -18.18 | 0.31 | -10.00 | no |
| 2026-08-20 | SHDW/USD | 47.39 | prior-high + volume + 3d-gain | -11.62 | 0.62 | 8.33 | yes |
| 2026-08-20 | OSMO/USD | 41.48 | prior-high + volume + 3d-gain | -6.33 | 0.82 | 4.71 | yes |
| 2026-08-20 | SHPING/USD | 29.05 | prior-high + volume + 3d-gain | -16.67 | 2.37 | -0.63 | yes |
| 2026-08-20 | PUMP/USD | 27.71 | prior-high + volume + 3d-gain | -4.09 | 1.31 | 12.68 | no |
| 2026-08-20 | ENA/USD | 25.07 | prior-high + volume + 3d-gain | -4.99 | 1.84 | 13.32 | yes |
| 2026-08-21 | LMTS/USD | 49.13 | prior-high + volume + 3d-gain | -6.92 | 0.31 | 3.88 | yes |
| 2026-08-21 | LCX/USD | 32.19 | prior-high + volume + 3d-gain | -34.23 | 1.58 | -0.68 | no |
| 2026-08-21 | USELESS/USD | 32.11 | prior-high + volume + 3d-gain | -7.74 | 2.80 | 16.09 | yes |
| 2026-08-21 | ENS/USD | 30.75 | 3d-gain | 3.67 | 4.27 | 15.90 | yes |
| 2026-08-21 | STX/USD | 29.73 | volume + 3d-gain | 2.81 | 2.27 | 21.01 | yes |
| 2026-08-21 | BCH/USD | 29.12 | 3d-gain | 1.95 | 3.62 | 8.64 | yes |
| 2026-08-21 | ZEC/USD | 29.06 | prior-high + volume + 3d-gain | -1.91 | 2.64 | 10.80 | yes |
| 2026-08-21 | PEPE/USD | 28.04 | 3d-gain | 7.72 | 5.65 | 24.42 | yes |
| 2026-08-21 | KEYCAT/USD | 25.45 | prior-high + volume + 3d-gain | -15.15 | 1.70 | 11.72 | yes |
| 2026-08-21 | ZORA/USD | 25.02 | prior-high + volume + 3d-gain | -9.12 | 2.18 | 14.34 | yes |
| 2026-08-22 | AERGO/USD | 75.67 | prior-high + volume + 3d-gain | -37.36 | 1.06 | 13.86 | yes |
| 2026-08-22 | LCX/USD | 66.32 | prior-high | -13.06 | 4.75 | 36.88 | yes |
| 2026-08-22 | PUMP/USD | 22.35 | volume | 3.26 | 2.60 | 30.99 | yes |
| 2026-08-23 | BLZ/USD | 29.82 | prior-high + volume + 3d-gain | -18.28 | 1.65 | 7.24 | yes |
| 2026-08-23 | MORPHO/USD | 25.63 | prior-high + 3d-gain | -8.39 | 3.35 | 4.52 | yes |
| 2026-08-23 | TRAC/USD | 22.60 | prior-high + volume + 3d-gain | -5.66 | 1.88 | 13.35 | yes |
| 2026-08-24 | MDT/USD | 76.07 | prior-high + volume + 3d-gain | -18.67 | 0.30 | 5.90 | yes |
| 2026-08-24 | STORJ/USD | 28.30 | prior-high + volume + 3d-gain | -29.32 | 2.88 | 11.87 | no |
| 2026-08-24 | DRV/USD | 25.01 | volume | 3.22 | 2.01 | 32.45 | yes |
| 2026-08-25 | FORTH/USD | 46.31 | prior-high + volume + 3d-gain | -17.39 | 0.55 | 9.82 | yes |
| 2026-08-25 | HONEY/USD | 42.26 | prior-high + volume + 3d-gain | -38.04 | 1.09 | -2.44 | yes |
| 2026-08-25 | PERP/USD | 37.43 | prior-high + volume + 3d-gain | -15.38 | 0.51 | 1.08 | yes |
| 2026-08-25 | 00/USD | 36.11 | prior-high + volume + 3d-gain | -36.50 | 0.68 | -9.76 | no |
| 2026-08-25 | GROVE/USD | 26.10 | prior-high + volume + 3d-gain | -28.20 | 0.20 | -1.36 | no |
| 2026-08-25 | ELA/USD | 23.66 | prior-high + volume + 3d-gain | -12.81 | 0.27 | 0.72 | yes |
| 2026-08-25 | META/USD | 23.49 | prior-high + volume + 3d-gain | -24.03 | 0.80 | -5.56 | no |
| 2026-08-26 | NCT/USD | 286.12 | prior-high + volume + 3d-gain | -22.83 | 2.15 | 4.70 | yes |
| 2026-08-26 | DNT/USD | 45.76 | prior-high + 3d-gain | -4.84 | 10.85 | 0.00 | yes |
| 2026-08-26 | RLS/USD | 26.50 | prior-high + volume + 3d-gain | -22.22 | 0.56 | -2.67 | no |
| 2026-08-26 | BICO/USD | 25.23 | prior-high + volume + 3d-gain | -78.02 | 1.21 | 0.44 | no |
| 2026-08-26 | BOBBOB/USD | 24.17 | prior-high + volume + 3d-gain | -5.17 | 0.54 | 5.50 | yes |
| 2026-08-26 | CVX/USD | 21.78 | prior-high + volume + 3d-gain | -9.12 | 1.09 | -3.51 | no |
| 2026-08-27 | DRB/USD | 63.79 | not enough history | – | – | – | no |
| 2026-08-27 | 00/USD | 44.20 | prior-high + volume | -14.66 | 0.29 | 48.18 | no |
| 2026-08-27 | BEAM/USD | 24.45 | prior-high + volume + 3d-gain | -14.17 | 0.89 | -5.36 | no |
| 2026-08-27 | SKR/USD | 21.71 | prior-high + volume + 3d-gain | -1.37 | 1.10 | 5.38 | no |
| 2026-08-27 | PYR/USD | 20.31 | prior-high + 3d-gain | -61.91 | 5.01 | 7.56 | no |
| 2026-08-28 | GHST/USD | 144.42 | prior-high + volume + 3d-gain | -24.21 | 0.28 | -5.38 | yes |
| 2026-08-29 | HNT/USD | 68.58 | volume + 3d-gain | 4.22 | 2.63 | 24.78 | yes |
| 2026-08-29 | HIGH/USD | 37.25 | prior-high + volume + 3d-gain | -26.32 | 1.25 | 11.70 | yes |
| 2026-08-29 | SWELL/USD | 22.86 | prior-high + 3d-gain | -51.72 | 4.12 | 7.69 | no |
| 2026-08-29 | 00/USD | 20.38 | prior-high | -19.15 | 3.39 | 26.36 | no |
| 2026-08-29 | NKN/USD | 20.13 | prior-high + volume + 3d-gain | -20.41 | 0.38 | 0.39 | no |
| 2026-08-30 | SKR/USD | 127.49 | prior-high | -12.83 | 3.37 | 30.22 | yes |
| 2026-08-30 | BASECAT/USD | 85.33 | not enough history | – | – | – | no |
| 2026-08-30 | ZKC/USD | 51.76 | prior-high + volume + 3d-gain | -12.33 | 2.68 | -1.00 | yes |
| 2026-08-30 | AST/USD | 29.94 | prior-high + volume + 3d-gain | -5.21 | 0.40 | 7.88 | yes |
| 2026-08-30 | ZORA/USD | 27.64 | prior-high + volume + 3d-gain | -20.08 | 0.69 | -3.80 | no |
| 2026-08-30 | POND/USD | 23.06 | prior-high + volume + 3d-gain | -19.53 | 1.07 | 8.67 | no |
| 2026-08-31 | USELESS/USD | 31.57 | prior-high + volume + 3d-gain | -9.06 | 0.88 | -1.39 | yes |
| 2026-08-31 | ARB/USD | 29.44 | prior-high + volume + 3d-gain | -23.08 | 0.83 | -8.38 | no |
| 2026-08-31 | KTA/USD | 24.64 | prior-high + volume + 3d-gain | -31.47 | 0.54 | -8.78 | no |
| 2026-08-31 | HONEY/USD | 22.95 | suppressed (already in play) | -49.17 | 0.70 | 14.66 | no |
| 2026-08-31 | FLOCK/USD | 21.75 | prior-high + 3d-gain | -7.75 | 7.74 | 1.57 | yes |
| 2026-09-01 | MLN/USD | 37.06 | prior-high + volume + 3d-gain | -17.88 | 0.47 | -5.34 | yes |
| 2026-09-02 | T/USD | 47.96 | prior-high + volume + 3d-gain | -13.06 | 0.46 | -1.38 | yes |
| 2026-09-02 | EGLD/USD | 32.27 | prior-high + volume + 3d-gain | -0.99 | 0.80 | 10.77 | yes |
| 2026-09-03 | BASECAT/USD | 62.30 | not enough history | – | – | – | no |
| 2026-09-03 | APR/USD | 31.76 | prior-high + volume + 3d-gain | -67.32 | 0.18 | 6.22 | no |
| 2026-09-03 | CHIP/USD | 31.09 | prior-high + volume + 3d-gain | -10.35 | 1.19 | 11.16 | no |
| 2026-09-03 | TROLL/USD | 29.39 | prior-high + volume + 3d-gain | -35.95 | 0.81 | -11.61 | no |
| 2026-09-03 | AERGO/USD | 26.70 | prior-high + volume + 3d-gain | -49.31 | 0.32 | -18.47 | no |
| 2026-09-04 | BLZ/USD | 63.83 | prior-high + volume + 3d-gain | -36.83 | 0.47 | -6.09 | no |
| 2026-09-04 | TROLL/USD | 43.31 | prior-high + volume + 3d-gain | -17.13 | 2.73 | 20.57 | yes |
| 2026-09-04 | TRIA/USD | 32.48 | prior-high + volume + 3d-gain | -64.84 | 0.79 | -20.86 | no |
| 2026-09-04 | DASH/USD | 31.77 | prior-high + volume + 3d-gain | -4.52 | 1.27 | 5.74 | yes |
| 2026-09-04 | BASECAT/USD | 24.32 | not enough history | – | – | – | no |
| 2026-09-04 | XCN/USD | 21.33 | prior-high + volume + 3d-gain | -14.64 | 2.13 | 5.03 | yes |
| 2026-09-05 | RNBW/USD | 37.89 | prior-high + volume + 3d-gain | -4.62 | 1.83 | 19.92 | yes |
| 2026-09-05 | BASECAT/USD | 34.61 | not enough history | – | – | – | no |
| 2026-09-05 | SUSHI/USD | 33.81 | prior-high + volume + 3d-gain | -13.41 | 1.51 | -4.70 | yes |
| 2026-09-05 | XAN/USD | 22.26 | prior-high + volume + 3d-gain | -5.52 | 0.62 | 4.50 | no |
| 2026-09-06 | PYR/USD | 52.41 | prior-high + volume + 3d-gain | -37.89 | 1.30 | -7.49 | no |
| 2026-09-06 | RAY/USD | 41.50 | volume + 3d-gain | 6.41 | 2.37 | 13.90 | yes |
| 2026-09-06 | DOOD/USD | 30.62 | prior-high + volume + 3d-gain | -5.31 | 0.95 | 10.75 | yes |
| 2026-09-06 | JUPITER/USD | 25.22 | prior-high + volume + 3d-gain | -15.15 | 0.61 | -1.92 | no |
| 2026-09-06 | METIS/USD | 22.07 | prior-high + volume + 3d-gain | -3.86 | 2.00 | 9.76 | yes |
| 2026-09-07 | VOXEL/USD | 35.62 | prior-high + volume + 3d-gain | -27.49 | 0.13 | 2.45 | no |
| 2026-09-07 | DRB/USD | 28.32 | not enough history | – | – | – | no |
| 2026-09-08 | VVV/USD | 40.23 | prior-high + volume + 3d-gain | -1.07 | 1.14 | 1.83 | yes |
| 2026-09-08 | DIEM/USD | 34.25 | prior-high + volume + 3d-gain | -2.16 | 1.26 | 0.48 | yes |
| 2026-09-08 | USELESS/USD | 23.75 | suppressed (already in play) | -27.24 | 1.50 | -13.04 | no |
| 2026-09-09 | OXT/USD | 72.50 | prior-high + volume + 3d-gain | -21.88 | 0.13 | 0.13 | yes |
| 2026-09-09 | KAT/USD | 33.86 | prior-high + volume + 3d-gain | -5.16 | 0.92 | 2.74 | yes |
| 2026-09-10 | SYND/USD | 127.34 | prior-high + volume + 3d-gain | -30.51 | 0.30 | -3.72 | yes |
| 2026-09-10 | UP/USD | 29.04 | prior-high + 3d-gain | -3.64 | 8.37 | 5.96 | yes |
| 2026-09-10 | VTHO/USD | 24.57 | volume + 3d-gain | 1.67 | 1.74 | 9.86 | yes |
| 2026-09-11 | STORJ/USD | 123.81 | prior-high + volume + 3d-gain | -57.49 | 0.39 | -8.07 | no |
| 2026-09-11 | FARM/USD | 20.95 | prior-high + volume + 3d-gain | -40.39 | 0.25 | -6.74 | no |
| 2026-09-12 | FLOCK/USD | 29.91 | prior-high + volume + 3d-gain | -26.77 | 0.64 | -7.36 | no |
| 2026-09-12 | REZ/USD | 23.36 | prior-high + volume + 3d-gain | -16.88 | 2.10 | 5.08 | yes |
| 2026-09-12 | ILV/USD | 22.01 | prior-high + volume + 3d-gain | -14.90 | 1.18 | -5.00 | no |
| 2026-09-13 | FORTH/USD | 62.63 | prior-high + volume + 3d-gain | -32.41 | 1.34 | 6.44 | yes |
| 2026-09-13 | CVC/USD | 38.57 | prior-high + volume + 3d-gain | -1.30 | 0.86 | 4.84 | yes |
| 2026-09-13 | B3/USD | 30.88 | prior-high + volume + 3d-gain | -9.55 | 1.13 | 23.27 | yes |
| 2026-09-13 | MEZO/USD | 21.34 | prior-high + volume + 3d-gain | -38.00 | 2.01 | -13.37 | no |
| 2026-09-14 | CAP/USD | 36.27 | prior-high + volume + 3d-gain | -38.06 | 0.26 | 3.63 | no |
| 2026-09-15 | ALIGN/USD | 33.90 | not enough history | – | – | – | no |
| 2026-09-16 | DRV/USD | 77.98 | prior-high + volume + 3d-gain | -31.38 | 1.06 | -8.69 | yes |
| 2026-09-16 | ZEC/USD | 20.57 | prior-high + volume + 3d-gain | -14.55 | 0.96 | -1.24 | no |
| 2026-09-17 | COTI/USD | 46.94 | prior-high + volume + 3d-gain | -21.57 | 1.26 | 8.13 | yes |
| 2026-09-17 | DRIFT/USD | 29.94 | prior-high + volume + 3d-gain | -10.70 | 2.36 | 2.81 | yes |
| 2026-09-18 | G/USD | 55.51 | 3d-gain | 0.92 | 6.65 | 24.52 | yes |
| 2026-09-18 | STRK/USD | 53.94 | prior-high + volume + 3d-gain | -15.59 | 0.34 | 0.35 | yes |
| 2026-09-18 | AURORA/USD | 37.74 | prior-high + volume + 3d-gain | -15.94 | 1.26 | 8.16 | yes |
| 2026-09-18 | BASECAT/USD | 32.04 | not enough history | – | – | – | no |
| 2026-09-18 | ARB/USD | 24.86 | prior-high + volume | -14.05 | 1.81 | 32.52 | no |
| 2026-09-18 | APT/USD | 22.42 | prior-high + volume + 3d-gain | -13.68 | 0.69 | 1.36 | no |
| 2026-09-18 | ZK/USD | 22.14 | prior-high + volume + 3d-gain | -19.65 | 0.84 | -4.30 | no |
| 2026-09-19 | CELR/USD | 45.81 | prior-high + volume + 3d-gain | -9.78 | 2.22 | 13.77 | yes |
| 2026-09-19 | ZAMA/USD | 37.27 | prior-high | -5.91 | 3.43 | 28.59 | yes |
| 2026-09-19 | EDGE/USD | 25.47 | prior-high + volume + 3d-gain | -8.34 | 0.80 | 5.03 | yes |
| 2026-09-19 | XTZ/USD | 24.09 | prior-high + volume + 3d-gain | -3.21 | 0.99 | 18.39 | yes |
| 2026-09-19 | AVAX/USD | 23.05 | volume + 3d-gain | 0.10 | 2.18 | 12.95 | yes |
| 2026-09-19 | META/USD | 22.49 | prior-high + volume + 3d-gain | -25.82 | 1.06 | 5.35 | no |
| 2026-09-19 | ENA/USD | 21.27 | prior-high + volume + 3d-gain | -10.90 | 0.65 | 20.57 | no |
| 2026-09-20 | RARI/USD | 65.54 | prior-high + volume + 3d-gain | -9.51 | 0.45 | 1.14 | yes |
| 2026-09-21 | AIOZ/USD | 55.17 | prior-high + volume | -5.62 | 1.07 | 29.90 | yes |
| 2026-09-21 | ZETA/USD | 42.01 | prior-high + volume + 3d-gain | -1.15 | 1.96 | 16.75 | yes |
| 2026-09-21 | ZETACHAIN/USD | 40.35 | prior-high + volume + 3d-gain | -1.48 | 1.57 | 16.67 | yes |
| 2026-09-21 | SWELL/USD | 35.21 | prior-high + volume + 3d-gain | -22.35 | 0.28 | 3.98 | no |
| 2026-09-21 | VARA/USD | 34.86 | prior-high + volume + 3d-gain | -10.86 | 0.57 | 2.42 | yes |
| 2026-09-21 | BNKR/USD | 24.90 | prior-high + volume + 3d-gain | -14.53 | 0.57 | 4.44 | no |
| 2026-09-21 | TAO/USD | 22.05 | prior-high + volume + 3d-gain | -5.55 | 1.48 | 12.75 | yes |
| 2026-09-21 | WIF/USD | 21.04 | prior-high + volume + 3d-gain | -10.05 | 0.38 | 8.68 | no |
| 2026-09-22 | SHDW/USD | 132.61 | prior-high + volume + 3d-gain | -7.82 | 1.04 | 8.57 | yes |
| 2026-09-22 | ALCX/USD | 55.56 | prior-high + volume + 3d-gain | -3.57 | 0.98 | 2.86 | yes |
| 2026-09-22 | MPLX/USD | 45.40 | volume + 3d-gain | 7.07 | 1.16 | 8.75 | yes |
| 2026-09-22 | A8/USD | 36.27 | prior-high + volume + 3d-gain | -2.39 | 0.87 | 0.78 | yes |
| 2026-09-22 | BCH/USD | 29.15 | prior-high + 3d-gain | -0.92 | 3.03 | 4.58 | yes |
| 2026-09-22 | KERNEL/USD | 28.51 | 3d-gain | 8.01 | 7.71 | 11.35 | yes |
| 2026-09-22 | USELESS/USD | 23.76 | prior-high + volume + 3d-gain | -16.92 | 0.94 | -4.12 | no |
| 2026-09-22 | MINA/USD | 21.57 | volume + 3d-gain | 5.77 | 1.47 | 20.68 | yes |
| 2026-09-23 | NEON/USD | 322.84 | prior-high + volume + 3d-gain | -9.79 | 1.76 | 11.41 | yes |
| 2026-09-23 | GFI/USD | 115.69 | prior-high + volume + 3d-gain | -14.29 | 0.68 | 4.08 | yes |
| 2026-09-23 | ALEO/USD | 48.73 | prior-high + volume + 3d-gain | -9.90 | 2.21 | 4.36 | yes |
| 2026-09-23 | DBR/USD | 21.30 | prior-high + volume + 3d-gain | -1.19 | 0.48 | 3.75 | yes |
| 2026-09-24 | QNT/USD | 27.45 | prior-high + volume + 3d-gain | -5.82 | 1.46 | 9.97 | yes |
| 2026-09-24 | AURORA/USD | 27.04 | suppressed (already in play) | -48.21 | 5.70 | 247.08 | no |
| 2026-09-24 | ONDO/USD | 26.65 | prior-high + volume + 3d-gain | -11.11 | 1.47 | -4.80 | no |
| 2026-09-24 | XPL/USD | 23.17 | prior-high + volume + 3d-gain | -14.16 | 1.11 | 0.82 | no |
| 2026-09-25 | QI/USD | 139.58 | prior-high + volume + 3d-gain | -20.56 | 0.47 | 6.12 | yes |
| 2026-09-25 | POND/USD | 102.85 | prior-high + volume + 3d-gain | -24.49 | 1.58 | -3.62 | no |
| 2026-09-25 | FARM/USD | 38.53 | prior-high + volume + 3d-gain | -21.43 | 0.41 | -3.38 | yes |
| 2026-09-25 | PNG/USD | 25.86 | prior-high + volume + 3d-gain | -16.76 | 0.39 | -8.34 | no |
| 2026-09-25 | RARE/USD | 22.62 | prior-high + volume + 3d-gain | -6.66 | 1.25 | -1.52 | no |
| 2026-09-25 | AERO/USD | 22.06 | prior-high + volume + 3d-gain | -6.83 | 1.00 | -0.46 | no |
| 2026-09-26 | AMP/USD | 62.66 | prior-high + volume + 3d-gain | -1.76 | 0.68 | 3.22 | yes |
| 2026-09-26 | EDGE/USD | 43.75 | prior-high + 3d-gain | -19.23 | 6.55 | 18.35 | yes |
| 2026-09-26 | RARE/USD | 34.18 | 3d-gain | 14.45 | 11.92 | 16.98 | yes |
| 2026-09-26 | KARRAT/USD | 31.98 | prior-high + volume + 3d-gain | -10.83 | 1.07 | -2.76 | yes |
| 2026-09-26 | MNDE/USD | 28.14 | 3d-gain | 8.00 | 8.00 | 15.21 | yes |
| 2026-09-26 | 2Z/USD | 23.15 | prior-high + 3d-gain | -5.79 | 3.41 | 9.09 | yes |
| 2026-09-27 | INX/USD | 31.16 | prior-high + volume + 3d-gain | -18.40 | 0.92 | -0.49 | no |
| 2026-09-27 | GRT/USD | 30.07 | prior-high + volume + 3d-gain | -4.56 | 1.30 | 10.94 | yes |
| 2026-09-27 | ABT/USD | 21.21 | prior-high + volume + 3d-gain | -24.66 | 1.28 | 9.24 | no |

## Alerts

| alert_day | symbol | impulse_pct | alert_day_was_mover | became_mover | days_to_mover | entry | trade | rule_return | r_multiple |
|---|---|---|---|---|---|---|---|---|---|
| 2026-06-30 | AI/USD | 61.76 | no | no | – | 0.04 | stop | -14.42 | -1.05 |
| 2026-07-01 | BASED1/USD | 62.36 | yes | no | – | 0.13 | stop | -24.25 | -1.32 |
| 2026-07-01 | ELA/USD | 41.09 | yes | no | – | 0.47 | stop | -23.77 | -1.11 |
| 2026-07-01 | NOM/USD | 41.01 | yes | yes | 2 | 0.00 | stop | -10.20 | -1.21 |
| 2026-07-02 | BIRB/USD | 56.22 | yes | no | – | 0.09 | stop | -11.78 | -1.29 |
| 2026-07-02 | RPL/USD | 51.09 | yes | yes | 2 | 2.07 | stop | -22.22 | -1.17 |
| 2026-07-03 | ARPA/USD | 35.53 | yes | no | – | 0.01 | stop | -11.65 | -1.22 |
| 2026-07-03 | MPLX/USD | 93.33 | yes | yes | 1 | 0.04 | t1 | 24.27 | 0.53 |
| 2026-07-04 | ETHFI/USD | 28.44 | no | no | – | 0.41 | stop | -7.06 | -1.04 |
| 2026-07-05 | TRB/USD | 32.30 | no | no | – | 18.43 | stop | -13.19 | -1.09 |
| 2026-07-06 | BLUR/USD | 36.54 | yes | no | – | 0.02 | stop | -14.55 | -1.01 |
| 2026-07-06 | YFI/USD | 46.79 | yes | no | – | 2691.56 | expired | -21.12 | -0.82 |
| 2026-07-10 | SKL/USD | 37.14 | no | no | – | 0.00 | stop | -12.50 | -1.13 |
| 2026-07-11 | SXT/USD | 33.80 | yes | no | – | 0.01 | stop | -17.89 | -1.10 |
| 2026-07-11 | T/USD | 39.88 | yes | no | – | 0.00 | t1 | 14.78 | 0.84 |
| 2026-07-12 | BLAST/USD | 31.03 | yes | no | – | 0.00 | stop | -7.89 | -1.42 |
| 2026-07-13 | BILL/USD | 51.92 | yes | no | – | 0.06 | stop | -8.93 | -1.42 |
| 2026-07-16 | OXT/USD | 86.84 | yes | yes | 1 | 0.01 | t2 | 73.94 | 4.83 |
| 2026-07-17 | NKN/USD | 121.57 | yes | no | – | 0.01 | stop | -46.02 | -1.00 |
| 2026-07-20 | 00/USD | 58.97 | yes | yes | 1 | 0.01 | t2 | 58.06 | 1.62 |
| 2026-07-22 | GST/USD | 26.83 | yes | no | – | 0.00 | stop | -9.43 | -1.02 |
| 2026-07-22 | ZAMA/USD | 34.53 | no | no | – | 0.05 | t1 | 14.15 | 0.90 |
| 2026-07-25 | EUL/USD | 98.16 | yes | no | – | 1.94 | expired | -39.39 | -0.87 |
| 2026-07-25 | QI/USD | 25.04 | yes | no | – | 0.00 | stop | -5.18 | -1.19 |
| 2026-07-26 | DIA/USD | 38.29 | yes | no | – | 0.14 | t1 | 12.41 | 0.86 |
| 2026-07-26 | ESP/USD | 53.31 | yes | no | – | 0.11 | stop | -28.96 | -1.02 |
| 2026-07-26 | SHIB/USD | 28.33 | no | no | – | 0.00 | stop | -6.60 | -1.27 |
| 2026-07-27 | BOBBOB/USD | 50.40 | yes | no | – | 0.01 | stop | -11.88 | -2.20 |
| 2026-07-27 | COTI/USD | 52.78 | yes | yes | 2 | 0.01 | t1 | 16.82 | 0.72 |
| 2026-07-29 | META/USD | 26.75 | yes | yes | 3 | 5.17 | stop | -7.05 | -1.45 |
| 2026-07-30 | FORTH/USD | 83.95 | yes | yes | 3 | 0.31 | stop | -35.80 | -1.05 |
| 2026-07-30 | ROBO/USD | 29.50 | yes | no | – | 0.01 | stop | -8.88 | -1.37 |
| 2026-07-31 | GODS/USD | 45.08 | yes | no | – | 0.03 | stop | -14.68 | -1.08 |
| 2026-07-31 | WMTX/USD | 117.55 | yes | no | – | 0.05 | stop | -41.18 | -1.02 |
| 2026-08-01 | BLZ/USD | 37.64 | yes | no | – | 0.01 | stop | -9.75 | -1.02 |
| 2026-08-02 | BICO/USD | 36.44 | yes | yes | 2 | 0.02 | t2 | 45.65 | 3.61 |
| 2026-08-04 | HFT/USD | 33.33 | yes | yes | 1 | 0.01 | t2 | 63.36 | 6.54 |
| 2026-08-06 | COOKIE/USD | 35.88 | yes | yes | 2 | 0.01 | stop | -11.34 | -1.08 |
| 2026-08-06 | CTSI/USD | 43.46 | yes | no | – | 0.03 | stop | -21.17 | -1.01 |
| 2026-08-06 | STG/USD | 30.65 | yes | no | – | 0.16 | stop | -7.56 | -1.16 |
| 2026-08-07 | C98/USD | 35.77 | yes | no | – | 0.02 | expired | -0.60 | -0.03 |
| 2026-08-07 | GWEI/USD | 83.01 | yes | yes | 3 | 0.03 | stop | -7.63 | -1.33 |
| 2026-08-08 | COOKIE/USD | 56.70 | yes | no | – | 0.01 | stop | -10.46 | -2.03 |
| 2026-08-08 | DIMO/USD | 33.76 | yes | no | – | 0.01 | t1 | 13.34 | 0.54 |
| 2026-08-08 | IMU/USD | 232.48 | yes | yes | 5 | 0.00 | stop | -51.93 | -1.00 |
| 2026-08-09 | XAN/USD | 59.48 | yes | no | – | 0.02 | stop | -38.87 | -1.11 |
| 2026-08-10 | RAD/USD | 30.95 | yes | no | – | 0.28 | expired | -14.18 | -0.60 |
| 2026-08-10 | SQD/USD | 28.53 | yes | no | – | 0.04 | stop | -23.77 | -1.17 |
| 2026-08-11 | NOICE/USD | 44.00 | yes | no | – | 0.00 | stop | -11.11 | -1.23 |
| 2026-08-12 | APR/USD | 189.74 | yes | yes | 4 | 0.58 | stop | -61.55 | -1.02 |
| 2026-08-14 | ALICE/USD | 38.98 | yes | no | – | 0.16 | stop | -23.17 | -1.06 |
| 2026-08-15 | COW/USD | 38.31 | yes | no | – | 0.14 | stop | -11.58 | -2.45 |
| 2026-08-15 | FUN1/USD | 47.33 | yes | no | – | 0.03 | stop | -27.18 | -1.00 |
| 2026-08-16 | DOGINME/USD | 31.12 | no | no | – | 0.00 | stop | -6.89 | -1.00 |
| 2026-08-18 | PRCL/USD | 115.22 | yes | no | – | 0.01 | stop | -23.23 | -1.03 |
| 2026-08-19 | TRUMP/USD | 28.00 | yes | yes | 3 | 1.79 | t2 | 35.32 | 2.12 |
| 2026-08-20 | BIO/USD | 27.25 | no | no | – | 0.03 | stop | -8.32 | -1.02 |
| 2026-08-20 | ENA/USD | 40.29 | yes | no | – | 0.12 | t2 | 45.09 | 2.46 |
| 2026-08-20 | MET/USD | 29.26 | no | no | – | 0.21 | stop | -7.28 | -1.07 |
| 2026-08-20 | OSMO/USD | 45.70 | yes | no | – | 0.04 | expired | -22.01 | -0.82 |
| 2026-08-20 | PNUT/USD | 27.18 | no | no | – | 0.05 | expired | -5.50 | -0.37 |
| 2026-08-20 | SHDW/USD | 40.62 | yes | no | – | 0.03 | expired | -15.22 | -0.60 |
| 2026-08-20 | SHPING/USD | 27.71 | yes | no | – | 0.00 | stop | -12.89 | -1.31 |
| 2026-08-20 | XRP/USD | 26.49 | no | no | – | 1.27 | expired | 17.92 | 1.37 |
| 2026-08-21 | AAVE/USD | 40.12 | no | no | – | 122.63 | expired | 6.79 | 0.32 |
| 2026-08-21 | ADA/USD | 31.32 | no | no | – | 0.23 | stop | -10.60 | -1.01 |
| 2026-08-21 | ARB/USD | 30.51 | no | no | – | 0.10 | stop | -9.99 | -1.04 |
| 2026-08-21 | AXS/USD | 27.48 | no | no | – | 1.07 | stop | -12.93 | -1.05 |
| 2026-08-21 | BCH/USD | 41.44 | yes | no | – | 287.88 | expired | -14.75 | -0.62 |
| 2026-08-21 | BERA/USD | 30.88 | no | no | – | 0.20 | stop | -15.99 | -1.04 |
| 2026-08-21 | BONK/USD | 34.63 | no | no | – | 0.00 | stop | -10.29 | -1.19 |
| 2026-08-21 | CRV/USD | 42.40 | no | no | – | 0.34 | expired | 1.34 | 0.07 |
| 2026-08-21 | DASH/USD | 30.12 | no | no | – | 38.75 | t1 | 11.41 | 0.72 |
| 2026-08-21 | DOGE/USD | 30.36 | no | no | – | 0.09 | stop | -11.88 | -1.03 |
| 2026-08-21 | DOGINME/USD | 33.05 | no | no | – | 0.00 | stop | -11.81 | -1.02 |
| 2026-08-21 | DOT/USD | 25.16 | no | no | – | 0.94 | stop | -10.27 | -1.00 |
| 2026-08-21 | EIGEN/USD | 30.38 | no | no | – | 0.22 | stop | -12.43 | -1.00 |
| 2026-08-21 | ENS/USD | 53.91 | yes | no | – | 5.91 | expired | -2.62 | -0.11 |
| 2026-08-21 | ETC/USD | 37.36 | no | no | – | 8.35 | expired | -10.92 | -0.58 |
| 2026-08-21 | ETH/USD | 31.26 | no | no | – | 2515.80 | expired | -2.52 | -0.28 |
| 2026-08-21 | FARTCOIN/USD | 39.39 | no | no | – | 0.20 | stop | -14.98 | -1.00 |
| 2026-08-21 | FIL/USD | 28.24 | no | no | – | 0.81 | stop | -8.04 | -1.06 |
| 2026-08-21 | FLOKI/USD | 46.23 | no | no | – | 0.00 | expired | -13.47 | -0.63 |
| 2026-08-21 | FLR/USD | 29.21 | no | no | – | 0.01 | stop | -10.33 | -1.05 |
| 2026-08-21 | GIGA/USD | 31.10 | no | no | – | 0.00 | stop | -8.97 | -1.02 |
| 2026-08-21 | GRT/USD | 31.29 | no | no | – | 0.02 | expired | -2.76 | -0.18 |
| 2026-08-21 | HYPE/USD | 29.11 | no | no | – | 75.54 | expired | 11.62 | 3.15 |
| 2026-08-21 | JASMY/USD | 32.47 | no | no | – | 0.00 | stop | -7.59 | -1.23 |
| 2026-08-21 | KEYCAT/USD | 31.92 | yes | yes | 2 | 0.00 | stop | -9.25 | -1.04 |
| 2026-08-21 | KMNO/USD | 42.79 | no | no | – | 0.03 | expired | -4.70 | -0.34 |
| 2026-08-21 | LIGHTER/USD | 32.65 | no | no | – | 3.13 | t2 | 41.29 | 5.23 |
| 2026-08-21 | LINK/USD | 25.70 | no | no | – | 11.99 | expired | -3.04 | -0.26 |
| 2026-08-21 | LMTS/USD | 55.47 | yes | no | – | 0.10 | expired | -24.68 | -0.82 |
| 2026-08-21 | MAMO/USD | 25.82 | no | no | – | 0.01 | stop | -14.94 | -1.24 |
| 2026-08-21 | MASK/USD | 25.71 | no | no | – | 0.44 | expired | 0.17 | 0.01 |
| 2026-08-21 | MON/USD | 34.97 | no | no | – | 0.03 | stop | -8.40 | -1.13 |
| 2026-08-21 | MOODENG/USD | 38.87 | no | no | – | 0.05 | stop | -10.98 | -1.02 |
| 2026-08-21 | OP/USD | 30.69 | no | no | – | 0.11 | stop | -12.88 | -1.17 |
| 2026-08-21 | PENGU/USD | 47.08 | no | no | – | 0.01 | expired | -6.95 | -0.34 |
| 2026-08-21 | PEPE/USD | 59.30 | yes | no | – | 0.00 | expired | -15.09 | -0.66 |
| 2026-08-21 | POPCAT/USD | 29.02 | no | no | – | 0.05 | t1 | 11.53 | 0.92 |
| 2026-08-21 | RED/USD | 35.06 | no | no | – | 0.13 | stop | -9.03 | -1.67 |
| 2026-08-21 | S/USD | 33.61 | no | no | – | 0.03 | expired | 3.40 | 0.24 |
| 2026-08-21 | SAND/USD | 28.39 | no | no | – | 0.05 | stop | -14.40 | -1.06 |
| 2026-08-21 | SHIB/USD | 34.24 | no | no | – | 0.00 | stop | -16.55 | -1.07 |
| 2026-08-21 | SPK/USD | 32.40 | no | yes | 2 | 0.02 | expired | 19.99 | 2.03 |
| 2026-08-21 | SPX/USD | 45.34 | no | no | – | 0.46 | expired | 30.27 | 1.84 |
| 2026-08-21 | STX/USD | 58.17 | yes | no | – | 0.19 | expired | 38.83 | 1.58 |
| 2026-08-21 | SUI/USD | 29.55 | no | no | – | 0.84 | stop | -15.68 | -1.17 |
| 2026-08-21 | SYRUP/USD | 31.19 | no | no | – | 0.21 | stop | -13.12 | -1.00 |
| 2026-08-21 | TIA/USD | 32.08 | no | no | – | 0.39 | stop | -15.17 | -1.01 |
| 2026-08-21 | TOSHI/USD | 31.81 | no | no | – | 0.00 | expired | -8.01 | -0.57 |
| 2026-08-21 | TRB/USD | 38.46 | no | no | – | 18.11 | expired | -4.03 | -0.21 |
| 2026-08-21 | TURBO/USD | 36.74 | no | no | – | 0.00 | stop | -11.30 | -1.02 |
| 2026-08-21 | USELESS/USD | 73.28 | yes | no | – | 0.06 | t2 | 67.38 | 3.28 |
| 2026-08-21 | VIRTUAL/USD | 26.50 | no | no | – | 0.73 | expired | -8.48 | -0.71 |
| 2026-08-21 | WELL/USD | 35.32 | no | no | – | 0.00 | stop | -6.60 | -1.14 |
| 2026-08-21 | WIF/USD | 46.14 | no | no | – | 0.20 | expired | 2.22 | 0.12 |
| 2026-08-21 | XCN/USD | 36.96 | no | no | – | 0.00 | stop | -13.42 | -1.01 |
| 2026-08-21 | XLM/USD | 30.38 | no | no | – | 0.20 | stop | -8.67 | -1.12 |
| 2026-08-21 | XPL/USD | 33.70 | no | no | – | 0.10 | stop | -15.85 | -1.17 |
| 2026-08-21 | ZEC/USD | 44.39 | yes | no | – | 734.47 | expired | 35.29 | 1.65 |
| 2026-08-21 | ZEN/USD | 37.18 | no | no | – | 5.24 | expired | 31.65 | 1.87 |
| 2026-08-21 | ZORA/USD | 43.34 | yes | no | – | 0.01 | t2 | 47.67 | 3.26 |
| 2026-08-21 | ZRO/USD | 26.46 | no | no | – | 1.00 | t1 | 11.65 | 1.09 |
| 2026-08-21 | ZRX/USD | 28.35 | no | no | – | 0.10 | expired | 7.78 | 0.67 |
| 2026-08-22 | AERGO/USD | 86.61 | yes | no | – | 0.01 | stop | -18.76 | -1.49 |
| 2026-08-22 | LCX/USD | 126.06 | yes | no | – | 0.03 | expired | -20.87 | -0.63 |
| 2026-08-22 | POL/USD | 31.10 | no | no | – | 0.11 | stop | -13.40 | -1.01 |
| 2026-08-22 | PUMP/USD | 65.33 | yes | no | – | 0.00 | stop | -17.16 | -1.02 |
| 2026-08-23 | BLZ/USD | 33.38 | yes | yes | 4 | 0.01 | t2 | 42.25 | 3.15 |
| 2026-08-23 | MORPHO/USD | 25.29 | yes | no | – | 2.90 | stop | -15.72 | -1.00 |
| 2026-08-23 | TRAC/USD | 38.40 | yes | no | – | 0.38 | stop | -15.56 | -1.05 |
| 2026-08-24 | DRV/USD | 38.04 | yes | no | – | 0.16 | expired | -3.08 | -0.15 |
| 2026-08-24 | KEYCAT/USD | 50.53 | yes | no | – | 0.00 | stop | -16.31 | -1.00 |
| 2026-08-24 | MDT/USD | 77.81 | yes | yes | 1 | 0.01 | t2 | 70.67 | 2.19 |
| 2026-08-25 | ELA/USD | 27.31 | yes | no | – | 0.34 | t1 | 7.83 | 0.44 |
| 2026-08-25 | FORTH/USD | 60.77 | yes | no | – | 0.28 | stop | -26.74 | -1.00 |
| 2026-08-25 | HONEY/USD | 44.18 | yes | yes | 1 | 0.00 | t2 | 49.30 | 3.07 |
| 2026-08-25 | PERP/USD | 36.70 | yes | no | – | 0.03 | stop | -25.29 | -1.18 |
| 2026-08-26 | A8/USD | 27.05 | no | no | – | 0.01 | t1 | 11.65 | 1.60 |
| 2026-08-26 | BOBBOB/USD | 31.33 | yes | no | – | 0.01 | t1 | 12.69 | 0.70 |
| 2026-08-26 | DNT/USD | 50.88 | yes | no | – | 0.01 | stop | -19.77 | -1.12 |
| 2026-08-26 | NCT/USD | 306.01 | yes | no | – | 0.02 | expired | -45.45 | -0.67 |
| 2026-08-27 | VET/USD | 26.27 | no | no | – | 0.01 | stop | -7.42 | -1.04 |
| 2026-08-28 | GHST/USD | 143.89 | yes | no | – | 0.11 | expired | -42.70 | -0.90 |
| 2026-08-29 | HIGH/USD | 36.72 | yes | no | – | 0.04 | stop | -9.60 | -2.35 |
| 2026-08-29 | HNT/USD | 84.15 | yes | yes | 1 | 0.43 | t2 | 80.02 | 2.20 |
| 2026-08-30 | AST/USD | 31.19 | yes | no | – | 0.01 | t2 | 44.07 | 2.07 |
| 2026-08-30 | SKR/USD | 143.40 | yes | no | – | 0.03 | expired | -31.19 | -0.61 |
| 2026-08-30 | ZKC/USD | 48.40 | yes | no | – | 0.06 | expired | -23.01 | -0.85 |
| 2026-08-31 | FLOCK/USD | 27.36 | yes | yes | 4 | 0.04 | stop | -13.78 | -1.19 |
| 2026-08-31 | USELESS/USD | 49.06 | yes | yes | 1 | 0.09 | t2 | 51.80 | 2.74 |
| 2026-08-31 | ZORA/USD | 45.41 | no | no | – | 0.01 | stop | -4.31 | -1.11 |
| 2026-09-01 | ARB/USD | 26.12 | no | yes | 4 | 0.11 | t2 | 36.94 | 10.63 |
| 2026-09-01 | MLN/USD | 33.83 | yes | no | – | 1.70 | stop | -14.41 | -1.04 |
| 2026-09-02 | EDGEX/USD | 26.81 | no | yes | 1 | 0.45 | t2 | 33.22 | 3.17 |
| 2026-09-02 | EGLD/USD | 40.32 | yes | no | – | 5.30 | stop | -26.52 | -1.02 |
| 2026-09-02 | T/USD | 47.94 | yes | no | – | 0.01 | expired | -14.95 | -0.61 |
| 2026-09-04 | DASH/USD | 42.44 | yes | no | – | 62.59 | t1 | 16.80 | 0.73 |
| 2026-09-04 | FLOCK/USD | 50.10 | yes | yes | 1 | 0.05 | t2 | 52.73 | 10.10 |
| 2026-09-04 | TROLL/USD | 78.50 | yes | no | – | 0.08 | stop | -21.08 | -1.15 |
| 2026-09-04 | XCN/USD | 30.45 | yes | no | – | 0.00 | stop | -6.44 | -1.02 |
| 2026-09-04 | ZEN/USD | 29.66 | no | no | – | 7.12 | expired | 15.43 | 0.89 |
| 2026-09-05 | RNBW/USD | 73.34 | yes | yes | 1 | 0.02 | t1 | 21.63 | 0.84 |
| 2026-09-05 | SUSHI/USD | 31.46 | yes | no | – | 0.25 | stop | -16.36 | -1.00 |
| 2026-09-06 | DOOD/USD | 41.24 | yes | no | – | 0.00 | expired | -5.81 | -0.27 |
| 2026-09-06 | METIS/USD | 28.95 | yes | no | – | 3.58 | stop | -17.88 | -1.03 |
| 2026-09-06 | RAY/USD | 54.44 | yes | no | – | 1.29 | expired | 36.30 | 1.19 |
| 2026-09-06 | XAN/USD | 56.22 | no | no | – | 0.02 | stop | -26.82 | -1.72 |
| 2026-09-07 | INJ/USD | 28.31 | no | no | – | 6.17 | stop | -5.25 | -1.14 |
| 2026-09-08 | AIOZ/USD | 28.12 | no | no | – | 0.07 | t2 | 37.38 | 2.57 |
| 2026-09-08 | DIEM/USD | 41.17 | yes | no | – | 2322.93 | stop | -25.11 | -1.00 |
| 2026-09-08 | VVV/USD | 49.68 | yes | no | – | 25.85 | expired | 26.03 | 0.90 |
| 2026-09-09 | KAT/USD | 35.50 | yes | no | – | 0.01 | stop | -23.91 | -1.01 |
| 2026-09-09 | OXT/USD | 71.41 | yes | no | – | 0.01 | stop | -29.10 | -1.04 |
| 2026-09-10 | SYND/USD | 123.30 | yes | yes | 3 | 0.01 | stop | -38.93 | -1.01 |
| 2026-09-10 | UP/USD | 37.57 | yes | no | – | 0.07 | stop | -12.47 | -1.00 |
| 2026-09-10 | VTHO/USD | 38.84 | yes | no | – | 0.00 | t2 | 42.85 | 1.94 |
| 2026-09-12 | REZ/USD | 31.33 | yes | no | – | 0.00 | stop | -7.98 | -1.48 |
| 2026-09-13 | B3/USD | 38.02 | yes | no | – | 0.00 | stop | -18.82 | -1.04 |
| 2026-09-13 | CVC/USD | 48.79 | yes | no | – | 0.03 | t1 | 17.42 | 0.60 |
| 2026-09-13 | FORTH/USD | 83.40 | yes | no | – | 0.42 | stop | -35.67 | -3.04 |
| 2026-09-16 | DRV/USD | 69.99 | yes | yes | 3 | 0.24 | t2 | 67.02 | 3.26 |
| 2026-09-17 | COTI/USD | 51.55 | yes | no | – | 0.03 | stop | -16.68 | -1.05 |
| 2026-09-17 | DRIFT/USD | 34.54 | yes | yes | 5 | 0.02 | t2 | 41.38 | 2.52 |
| 2026-09-18 | AURORA/USD | 51.63 | yes | yes | 3 | 0.02 | stop | -16.41 | -1.01 |
| 2026-09-18 | G/USD | 72.30 | yes | yes | 1 | 0.01 | t2 | 73.68 | 2.51 |
| 2026-09-18 | NEAR/USD | 61.09 | no | no | – | 3.76 | t1 (open, marked at last bar) | 35.25 | 2.01 |
| 2026-09-18 | S/USD | 26.97 | no | no | – | 0.03 | t2 | 35.10 | 5.47 |
| 2026-09-18 | STRK/USD | 67.22 | yes | no | – | 0.04 | expired (open, marked at last bar) | -8.50 | -0.34 |
| 2026-09-19 | AVAX/USD | 35.14 | yes | no | – | 10.10 | expired (open, marked at last bar) | 3.47 | 0.17 |
| 2026-09-19 | CELR/USD | 63.86 | yes | no | – | 0.00 | t1 (open, marked at last bar) | 18.92 | 0.66 |
| 2026-09-19 | COSMOSDYDX/USD | 26.11 | no | no | – | 0.13 | stop | -3.60 | -1.15 |
| 2026-09-19 | EDGE/USD | 29.61 | yes | no | – | 0.09 | t2 | 37.68 | 2.41 |
| 2026-09-19 | INJ/USD | 46.74 | no | no | – | 7.93 | expired (open, marked at last bar) | -7.26 | -0.49 |
| 2026-09-19 | SKL/USD | 30.07 | no | no | – | 0.00 | expired (open, marked at last bar) | -2.18 | -0.14 |
| 2026-09-19 | XTZ/USD | 44.83 | yes | no | – | 0.37 | expired (open, marked at last bar) | -14.89 | -0.77 |
| 2026-09-19 | ZAMA/USD | 71.08 | yes | no | – | 0.08 | expired (open, marked at last bar) | -3.65 | -0.15 |
| 2026-09-20 | RARI/USD | 67.24 | yes | no | – | 0.15 | expired (open, marked at last bar) | -12.29 | -0.35 |
| 2026-09-21 | AIOZ/USD | 74.63 | yes | no | – | 0.14 | expired (open, marked at last bar) | -15.85 | -0.47 |
| 2026-09-21 | SUI/USD | 28.09 | no | no | – | 1.04 | expired (open, marked at last bar) | 11.63 | 0.81 |
| 2026-09-21 | TAO/USD | 27.57 | yes | no | – | 319.37 | expired (open, marked at last bar) | -5.14 | -0.33 |
| 2026-09-21 | VARA/USD | 34.86 | yes | yes | 4 | 0.00 | t1 (open, marked at last bar) | 12.87 | 0.67 |
| 2026-09-21 | ZETA/USD | 50.32 | yes | no | – | 0.06 | expired (open, marked at last bar) | -8.21 | -0.27 |
| 2026-09-21 | ZETACHAIN/USD | 49.73 | yes | no | – | 0.06 | expired (open, marked at last bar) | -7.14 | -0.24 |
| 2026-09-22 | A8/USD | 41.15 | yes | no | – | 0.01 | stop | -26.18 | -1.04 |
| 2026-09-22 | ALCX/USD | 61.54 | yes | no | – | 3.36 | expired (open, marked at last bar) | -19.05 | -0.54 |
| 2026-09-22 | BCH/USD | 35.45 | yes | no | – | 345.00 | expired (open, marked at last bar) | -10.12 | -0.43 |
| 2026-09-22 | BNKR/USD | 55.31 | no | no | – | 0.00 | t1 (open, marked at last bar) | 25.56 | 1.30 |
| 2026-09-22 | KERNEL/USD | 40.23 | yes | no | – | 0.06 | stop | -16.18 | -1.04 |
| 2026-09-22 | MINA/USD | 48.10 | yes | no | – | 0.16 | expired (open, marked at last bar) | -8.46 | -0.54 |
| 2026-09-22 | MPLX/USD | 60.37 | yes | yes | 3 | 0.06 | expired (open, marked at last bar) | -3.09 | -0.10 |
| 2026-09-22 | SHDW/USD | 149.27 | yes | no | – | 0.05 | expired (open, marked at last bar) | -31.08 | -0.57 |
| 2026-09-23 | ALEO/USD | 56.63 | yes | yes | 1 | 0.02 | t2 | 56.02 | 1.91 |
| 2026-09-23 | BLAST/USD | 26.74 | no | pending | – | 0.00 | stop | -11.76 | -1.47 |
| 2026-09-23 | DBR/USD | 26.71 | yes | yes | 1 | 0.02 | t1 (open, marked at last bar) | 12.47 | 0.65 |
| 2026-09-23 | GFI/USD | 119.27 | yes | pending | – | 0.07 | expired (open, marked at last bar) | -36.82 | -0.78 |
| 2026-09-23 | MET/USD | 34.09 | no | pending | – | 0.34 | stop | -6.97 | -1.21 |
| 2026-09-23 | NEON/USD | 376.46 | yes | yes | 1 | 0.06 | t1 (open, marked at last bar) | 38.85 | 0.52 |
| 2026-09-23 | SUPER/USD | 25.37 | no | pending | – | 0.18 | expired (open, marked at last bar) | 8.81 | 1.21 |
| 2026-09-23 | XCN/USD | 27.70 | no | pending | – | 0.01 | expired (open, marked at last bar) | -8.07 | -0.79 |
| 2026-09-23 | ZRO/USD | 27.44 | no | pending | – | 1.50 | expired (open, marked at last bar) | 2.29 | 0.33 |
| 2026-09-24 | CTX/USD | 25.31 | no | yes | 1 | 0.54 | t2 | 38.26 | 11.65 |
| 2026-09-24 | QNT/USD | 34.81 | yes | yes | 2 | 90.08 | t2 | 43.15 | 2.44 |
| 2026-09-24 | SPA/USD | 30.92 | no | pending | – | 0.00 | stop | -5.40 | -1.48 |
| 2026-09-25 | FARM/USD | 38.07 | yes | pending | – | 9.47 | stop | -11.76 | -1.08 |
| 2026-09-25 | QI/USD | 140.68 | yes | pending | – | 0.00 | expired (open, marked at last bar) | -13.32 | -0.27 |
| 2026-09-26 | 2Z/USD | 40.97 | yes | pending | – | 0.07 | expired (open, marked at last bar) | -8.98 | -0.55 |
| 2026-09-26 | AMP/USD | 70.01 | yes | pending | – | 0.00 | expired (open, marked at last bar) | -23.22 | -0.59 |
| 2026-09-26 | EDGE/USD | 71.78 | yes | pending | – | 0.14 | stop | -17.29 | -1.05 |
| 2026-09-26 | KARRAT/USD | 35.27 | yes | pending | – | 0.00 | expired (open, marked at last bar) | -12.58 | -0.71 |
| 2026-09-26 | MNDE/USD | 39.60 | yes | pending | – | 0.03 | expired (open, marked at last bar) | -11.24 | -0.68 |
| 2026-09-26 | RARE/USD | 69.07 | yes | pending | – | 0.02 | expired (open, marked at last bar) | -16.07 | -0.97 |
| 2026-09-26 | WLD/USD | 28.52 | no | pending | – | 0.52 | stop | -6.83 | -1.10 |
| 2026-09-27 | GRT/USD | 36.79 | yes | pending | – | 0.04 | expired (open, marked at last bar) | -13.17 | -0.60 |
| 2026-09-27 | W/USD | 32.42 | no | pending | – | 0.02 | expired (open, marked at last bar) | -11.55 | -0.66 |
