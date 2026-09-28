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
