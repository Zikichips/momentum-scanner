# Intraday Stage A replay — 02 Oct 04:00 to 09 Oct 03:00 UTC

Kraken bars; rolling top-30 universe by trailing 24h volume, plus forced: STRK/USD. Rule: 1h close > prior 72h high, volume >= 3.0x prior 72h average, +15% over 24h. Every alert counts (no slot limit).

## Coins the intraday check put in play

| first seen (run, UTC) | symbol | in top-N then | 3-day high | 24h gain | what happened |
|---|---|---|---|---|---|
| 02 Oct 15:00 | ZRO/USD | yes | 1.946 | +18% | failed |
| 03 Oct 18:00 | STRK/USD | no (forced) | 0.05092 | +19% | taken over by a daily breakout |
| 05 Oct 09:00 | FET/USD | yes | 0.2653 | +20% | failed |
| 08 Oct 10:00 | ALGO/USD | yes | 0.1314 | +17% | failed |
| 08 Oct 12:00 | STRK/USD | no (forced) | 0.05794 | +21% | failed |

## Alerts only the intraday check produces

None.

## Daily-only alerts lost with intraday on

None.

## All alerts, daily-only (what the live scanner did)

| fired (run, UTC) | symbol | type | entry | stop | T1 | T2 | outcome | R |
|---|---|---|---|---|---|---|---|---|
| 03 Oct 00:00 | NIGHT/USD | breakout | 0.04886 | 0.04656 | 0.07025 | 0.09164 | stop | -1.17 |
| 03 Oct 00:00 | SAND/USD | breakout | 0.0693 | 0.04617 | 0.0969 | 0.1245 | open |  |
| 04 Oct 00:00 | STRK/USD | breakout | 0.05434 | 0.04939 | 0.06795 | 0.08156 | stop | -1.15 |
| 04 Oct 01:00 | SAND/USD | pullback | 0.0751 | 0.07019 | 0.084 | 0.1052 | stop | -1.14 |
| 04 Oct 02:00 | SAND/USD | breakout | 0.075 | 0.07139 | 0.1075 | 0.14 | stop | -1.52 |

_Run 2026-10-09 03:55 UTC._
