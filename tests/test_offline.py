"""Offline smoke test: monkeypatches data access to the sample CSV and runs the
live scan path (Stage A -> Stage B -> exits -> outcomes) against the local JSON store.

  python -m tests.test_offline
"""
import os, shutil, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
store_path = ROOT / "data" / "test_store.json"
os.environ["LOCAL_STORE_PATH"] = str(store_path)
# Blank (not unset) so load_dotenv, which never overrides, can't point the test at
# real Supabase or Telegram once .env is filled in.
for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    os.environ[k] = ""
if store_path.exists():
    store_path.unlink()

from scanner import data, scan, outcomes, db
from scanner.backtest import resample_daily

full = data.load_csv(ROOT / "data" / "sample_QNT.csv")
# Freeze "now" at the pullback base so Stage B can fire.
CUT = pd.Timestamp("2026-09-05 00:00:00+00:00")
hist = full[full.index <= CUT]

def fake_ohlcv(symbol, asset_class, timeframe, limit=400, ex=None):
    df = resample_daily(hist) if timeframe == "1d" else hist
    return df.tail(limit)

data.ohlcv = fake_ohlcv
data._exchange = lambda: None
scan.universe = lambda: [("QNT/USD", "crypto")]

# Stage A must run on the breakout day, so first run at the breakout bar's close.
BO_CUT = pd.Timestamp("2026-08-30 23:00:00+00:00")
hist = full[full.index <= BO_CUT]
store = db.Store()
n_a = scan.stage_a(store)
assert n_a == 1, f"expected 1 breakout, got {n_a}"
print("Stage A OK ->", store.watching()[0]["symbol"])

# Advance to pullback base and run Stage B.
hist = full[full.index <= CUT]
import scanner.scan as s
s.datetime = outcomes.datetime  # same class; ensure expiry uses real now (breakout is old, so patch expiry)
from scanner.config import CFG
CFG["breakout"]["in_play_expiry_days"] = 10_000
n_b = scan.stage_b(store)
assert n_b == 1, f"expected 1 setup, got {n_b}"
a = store.open_alerts()[0]
print(f"Stage B OK -> entry {a['entry']:.2f} stop {a['stop']:.2f} t1 {a['target1']:.2f} t2 {a['target2']:.2f} size ${a['position_usd']}")

# Advance to end and grade (fired_at is "now" in live; pin it to the cut for the sample).
hist = full
a["fired_at"] = CUT.isoformat()
patch = outcomes.grade(a, hist, close_at_end=True)
store.update("alerts", a["id"], patch)
sb = outcomes.scoreboard(store.select("alerts"))
assert sb["alerts_graded"] == 1 and sb["wins"] == 1
print("Outcomes OK ->", sb)
print("ALL OK")
