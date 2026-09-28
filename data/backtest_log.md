# Backtest log

History: Coinbase 1h bars (Kraken only serves the latest 720). No fees/slippage modelled yet.

| Date | Universe | Days | Config change | Setups | Win rate | Avg R | vs hold 7d | Notes |
|---|---|---|---|---|---|---|---|---|
| 2026-09-28 | BTC ETH SOL XRP ADA LINK AVAX DOT QNT | 365 | baseline (config.yaml as shipped) | 4 | 0% | -1.15 | +0.65pp | All 4 stopped out. Too few setups to judge (<20); rules too strict for majors. QNT: Stage A fired 24 Sep, no Stage B (retrace hit 57.5% > 55% cap). |

## 2026-09-28 — two entry types (pullback + breakout)

Config used (config.yaml as committed with this entry):
- Stage A: 20-day high, volume ≥ 3.0× 30-day avg, ≥ 25% over 3 days (crypto), in play 5 days
- Pullback entry: retrace 0.25–0.55, EMA 20 rising + reclaimed, pullback vol ratio ≤ 0.8, R:R ≥ 2.0, stop 1% under pullback low, T1 = impulse high, T2 = high + 0.5× range
- Breakout entry: entry = breakout-day close, stop = breakout level × 0.97, T1 = entry + 1.0× (entry − impulse low), T2 = entry + 2.0×, R:R ≥ 2.0
- Sizing 5% risk / 50% cap. Grader: half off at T1, stop to entry, 14-day max hold. **No fees in these numbers** (0.3%/side shown separately).
- History: Coinbase 1h. `--days` is the evaluation window; indicator warm-up is fetched on top.

**Top-30 Kraken pairs, 365 days** (`backtest_20260928_100240.csv`; JUP, XMR not on Coinbase → 28 symbols)

| Entry | Setups | Win rate | Avg R | Avg R after fees | Avg winner | Avg loser | Winner/loser | vs hold 7d | Avg R without best trade |
|---|---|---|---|---|---|---|---|---|---|
| pullback | 28 | 39% | +0.15 | +0.02 | +2.36R | −1.28R | 1.84× | −7.2pp | −0.08 |
| breakout | 44 graded (+1 open) | 43% | +0.46 | +0.41 | +2.28R | −0.92R | 2.47× | −3.0pp | +0.22 (+0.08 without best 3) |
| combined | 72 | 42% | +0.34 | – | +2.31R | −1.07R | 2.16× | −4.7pp | – |

Timing: 59 of 72 trades fell in the last six months (Mar–Sep 2026). Breakout: first half 8 trades at +0.10R, second half 37 at +0.54R.

**QNT/USD, 30 days** (`backtest_20260928_095934.csv`): breakout entry 24 Sep at 90.08, stop 74.13, T2 141.90 hit → +43.1%, +2.44R (hold 7d: +155.7%). Pullback: no setup (retrace 57.5% > 0.55 cap, correct for a blow-off).

Verdict: pullback shows no edge. Breakout clears the handoff's thin-edge bar (win 35–45%, avg R > 0.3) but misses the 3× winner/loser bar and leans on three trades. Not yet proven. Next single test: `breakout_entry.t2_multiple` 2.0 → 3.0.

## 2026-09-28 — account grid: concurrency × position cap × capital (breakout entry only)

Command: `python -m scanner.backtest --entry breakout --top 150 --days 365 --grid` (`backtest_20260928_120859.csv`).
Universe: Kraken top 150 by volume today; 109 also on Coinbase (history source), 41 skipped. Entry/exit thresholds unchanged.
One account per cell: setups replayed in time order; a setup is skipped when `max_concurrent` trades are open (fired → outcome).
Sizing via position_size (5% risk, cap as shown). **Fees 0.3% each way included in $ P&L** (entry + exit notional incl. the T1 half); win rate / avg R are before fees.
Max drawdown is peak-to-trough of realised P&L (closed trades); open-trade swings not modelled. Peak deployed > capital means the cell needs money you don't have.

| capital | max_concurrent | max_position_pct | taken | skipped | win_rate | avg_r | pnl_usd | max_dd_usd | pnl_per_dd | worst_loss_usd | peak_deployed_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 200 | 2 | 50 | 59 | 109 | 0.305 | -0.018 | -44.3 | 228.27 | -0.19 | -15.18 | 200.0 |
| 200 | 2 | 75 | 59 | 109 | 0.305 | -0.018 | -47.21 | 261.68 | -0.18 | -17.5 | 261.42 |
| 200 | 3 | 50 | 78 | 90 | 0.295 | -0.049 | -76.52 | 339.48 | -0.23 | -15.18 | 284.84 |
| 200 | 3 | 75 | 78 | 90 | 0.295 | -0.049 | -81.51 | 374.97 | -0.22 | -17.5 | 346.26 |
| 200 | none | 50 | 168 | 0 | 0.28 | -0.092 | -289.08 | 588.04 | -0.49 | -15.18 | 3152.09 |
| 200 | none | 75 | 168 | 0 | 0.28 | -0.092 | -296.9 | 662.0 | -0.45 | -17.5 | 3407.1 |
| 1000 | 2 | 50 | 59 | 109 | 0.305 | -0.018 | -221.43 | 1141.26 | -0.19 | -75.88 | 1000.0 |
| 1000 | 2 | 75 | 59 | 109 | 0.305 | -0.018 | -235.96 | 1308.29 | -0.18 | -87.49 | 1307.1 |
| 1000 | 3 | 50 | 78 | 90 | 0.295 | -0.049 | -382.59 | 1697.33 | -0.23 | -75.88 | 1424.2 |
| 1000 | 3 | 75 | 78 | 90 | 0.295 | -0.049 | -407.5 | 1874.74 | -0.22 | -87.49 | 1731.3 |
| 1000 | none | 50 | 168 | 0 | 0.28 | -0.092 | -1445.57 | 2940.18 | -0.49 | -75.88 | 15760.47 |
| 1000 | none | 75 | 168 | 0 | 0.28 | -0.092 | -1484.41 | 3309.77 | -0.45 | -87.49 | 17035.53 |

Why it's negative when the top-30 run was positive: the 41 trades on the earlier top-30 coins average +0.54R; the other 127 (less liquid coins) average −0.30R. By quarter: Q4-25 +0.40R (26), Q1-26 −0.61R (26), Q2-26 −0.66R (35), Q3-26 +0.18R (80).
For reference, earlier top-30 coins only, $1,000/50% cap: max 2 concurrent → 19 taken, +$431, DD $275; unlimited → 41 taken, +$572, DD $340 (that subset is picked with hindsight — today's volume ranking).

Verdict: no concurrency/cap setting makes the breakout entry profitable on the full live universe. Least-bad: max_concurrent 2, cap 50% (config default). The cap barely matters (same trades; 75% only enlarges size and drawdown).

## 2026-09-28 — rolling universe (no hindsight) vs fixed top-30 vs full 109

Command: `python -m scanner.backtest --entry breakout --rolling-top 30 --days 365 --capital 1000 --max-concurrent 2 --max-position 50` (`backtest_20260928_125403.csv`).
Rolling universe: each calendar month, top 30 Kraken USD pairs by the previous month's Kraken quote volume (close × volume), among the 289 Kraken USD pairs Coinbase also lists; Stage A only checked while a coin is in that month's list. 63 distinct pairs over 13 months. Only pairs listed on Kraken today could be ranked (survivorship). Thresholds unchanged. All three rows use the same replay: $1,000, max 2 concurrent, 50% cap, fees 0.3% each way. "Tool" = every setup; "trader" = setups actually taken.

| universe | setups | tool avg R | taken | trader avg R | P&L | max DD | P&L ÷ DD | H2-2025 setups / avg R / taken $ | H1-2026 | H2-2026 (Jul–Sep) |
|---|---|---|---|---|---|---|---|---|---|---|
| fixed top-30 (hindsight) | 41 | +0.54 | 19 | +0.55 | +$431 | $275 | 1.57 | 7 / +0.27 / −$31 | 10 / −0.06 / +$35 | 24 / +0.87 / +$427 |
| full 109 (live universe today) | 168 | −0.09 | 59 | −0.02 | −$221 | $1,141 | −0.19 | 27 / +0.34 / +$399 | 61 / −0.64 / −$929 | 80 / +0.18 / +$309 |
| rolling top-30 (no hindsight) | 32 | +0.34 | 15 | +1.00 | +$430 | $161 | 2.68 | 3 / +3.35 / +$220 | 8 / −0.09 / −$14 | 21 / +0.07 / +$224 |

Concentration (rolling): DASH/USD 1 Nov 2025 = +12.1R, +$329 of the $430. Without it: tool avg R −0.04, median setup −0.28R, P&L +$101. Trader avg R (+1.00) beats tool (+0.34) only because the concurrency limit happened to keep DASH and skip losers — order luck, not skill.
Note: the rolling list includes PAXG (gold token) and USD1 (stablecoin), which aren't in `universe.crypto.exclude`; they never fired.

Verdict: liquid-only is clearly less bad than the full universe (smaller losses, much smaller drawdown), but without hindsight the positive result rests on one trade. No demonstrated edge.
