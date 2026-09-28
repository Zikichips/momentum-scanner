"""Generate a synthetic hourly series that mimics the QNT pattern:
60 days ranging 60-80 -> breakout day on 5x volume -> 3-day impulse to ~190
-> 2-day pullback to ~135 (≈45% retrace) -> second leg to ~250.
Writes data/sample_QNT.csv.
"""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(7)
hours = []
price = 70.0
vol_base = 1_000_000

def bar(p_open, p_close, vol, noise=0.004):
    hi = max(p_open, p_close) * (1 + abs(rng.normal(0, noise)))
    lo = min(p_open, p_close) * (1 - abs(rng.normal(0, noise)))
    return [p_open, hi, lo, p_close, vol]

# 60 days of range
for h in range(60 * 24):
    nxt = float(np.clip(price * (1 + rng.normal(0, 0.006)), 60, 80))
    hours.append(bar(price, nxt, vol_base * rng.uniform(0.6, 1.4)))
    price = nxt

# breakout + impulse: 3 days from ~78 to ~190 on 5x volume
target = 190
steps = 3 * 24
for i in range(steps):
    nxt = price * (target / price) ** (1 / (steps - i)) * (1 + rng.normal(0, 0.01))
    hours.append(bar(price, nxt, vol_base * rng.uniform(4, 6)))
    price = nxt

# pullback: 2 days to ~135 on fading volume (retrace ≈ (190-135)/(190-78) ≈ 49%)
target = 135
steps = 2 * 24
for i in range(steps):
    nxt = price * (target / price) ** (1 / (steps - i)) * (1 + rng.normal(0, 0.008))
    hours.append(bar(price, nxt, vol_base * rng.uniform(1.2, 2.0)))
    price = nxt

# base + reclaim: 1 day hovering 135-145 then second leg to 250 over 3 days
for i in range(24):
    nxt = float(np.clip(price * (1 + rng.normal(0.002, 0.006)), 133, 148))
    hours.append(bar(price, nxt, vol_base * rng.uniform(1.0, 1.6)))
    price = nxt
target = 250
steps = 3 * 24
for i in range(steps):
    nxt = price * (target / price) ** (1 / (steps - i)) * (1 + rng.normal(0, 0.01))
    hours.append(bar(price, nxt, vol_base * rng.uniform(2.5, 4)))
    price = nxt
# 10 more days drifting so the grader has a 14-day window
for h in range(10 * 24):
    nxt = price * (1 + rng.normal(0, 0.006))
    hours.append(bar(price, nxt, vol_base * rng.uniform(0.8, 1.5)))
    price = nxt

idx = pd.date_range("2026-07-01", periods=len(hours), freq="h", tz="UTC")
df = pd.DataFrame(hours, columns=["open", "high", "low", "close", "volume"], index=idx)
df.index.name = "ts"
out = Path(__file__).resolve().parent.parent / "data" / "sample_QNT.csv"
df.to_csv(out)
print("wrote", out, len(df), "bars")
