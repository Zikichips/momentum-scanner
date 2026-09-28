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
bo_alerts = [x for x in store.open_alerts() if x["entry_type"] == "breakout"]
assert len(bo_alerts) == 1, f"expected 1 breakout-entry alert, got {len(bo_alerts)}"
ba = bo_alerts[0]
assert ba["stop"] < ba["entry"] < ba["target1"] < ba["target2"] and ba["reward_risk"] >= 2
print(f"Breakout entry OK -> entry {ba['entry']:.2f} stop {ba['stop']:.2f} t1 {ba['target1']:.2f} t2 {ba['target2']:.2f} size ${ba['position_usd']}")

# Advance to pullback base and run Stage B.
hist = full[full.index <= CUT]
import scanner.scan as s
s.datetime = outcomes.datetime  # same class; ensure expiry uses real now (breakout is old, so patch expiry)
from scanner.config import CFG
CFG["breakout"]["in_play_expiry_days"] = 10_000
n_b = scan.stage_b(store)
assert n_b == 1, f"expected 1 setup, got {n_b}"
pb_alerts = [x for x in store.open_alerts() if x["entry_type"] == "pullback"]
assert len(pb_alerts) == 1
a = pb_alerts[0]
print(f"Stage B OK -> entry {a['entry']:.2f} stop {a['stop']:.2f} t1 {a['target1']:.2f} t2 {a['target2']:.2f} size ${a['position_usd']}")

# Advance to end and grade (fired_at is "now" in live; pin it to the cut for the sample).
hist = full
a["fired_at"] = CUT.isoformat()
store.update("alerts", a["id"], outcomes.grade(a, hist, close_at_end=True))
ba["fired_at"] = BO_CUT.isoformat()
store.update("alerts", ba["id"], outcomes.grade(ba, hist, close_at_end=True))
sb = outcomes.scoreboard(store.select("alerts"))
assert sb["pullback"]["alerts_graded"] == 1 and sb["pullback"]["wins"] == 1
assert sb["breakout"]["alerts_graded"] == 1 and sb["overall"]["alerts_graded"] == 2
row = outcomes.scoreboard_row(sb)
assert row["pullback_n_graded"] == 1 and row["breakout_n_graded"] == 1
print("Outcomes OK ->", sb)

# Concurrency limit, live: with the limit at the number of open alerts, a new setup is
# stored with taken=False. Once graded it counts for the tool, not the trader.
from scanner.strategy import Setup
CFG["account"]["max_concurrent_trades"] = len(store.open_alerts())
extra = Setup(symbol="TEST/USD", asset_class="crypto", entry=10.0, stop=9.0, target1=12.0, target2=14.0,
              reward_risk=4.0, position_usd=100.0, retrace_pct=0.0, ema_value=None, pullback_low=None,
              entry_type="breakout")
assert scan._insert_alert(store, extra, None) is False
skipped = [x for x in store.select("alerts") if x["symbol"] == "TEST/USD"]
assert len(skipped) == 1 and skipped[0]["taken"] is False and skipped[0]["outcome"] == "open"
assert all(x["symbol"] != "TEST/USD" for x in store.open_alerts())   # not a position
x = skipped[0]
x["fired_at"] = BO_CUT.isoformat()
store.update("alerts", x["id"], outcomes.grade({**x, "entry": ba["entry"], "stop": ba["stop"],
                                                "target1": ba["target1"], "target2": ba["target2"]}, hist, close_at_end=True))
sb2 = outcomes.scoreboard(store.select("alerts"))
assert sb2["overall"]["alerts_graded"] == 3 and sb2["overall"]["skipped"] == 1
assert sb2["trader"]["alerts_graded"] == 2 and sb2["trader"]["skipped"] == 0
assert outcomes.scoreboard_row(sb2)["trader_n_graded"] == 2

# Concurrency limit, backtest: three overlapping trades with a limit of 2 -> third skipped.
from scanner.backtest import apply_portfolio
t0 = pd.Timestamp("2026-01-01", tz="UTC")
fake = [{"entry": 10.0, "stop": 9.0, "rule_return": 10.0, "r_multiple": 1.0, "outcome": "t2",
         "fired_at": t0 + pd.Timedelta(hours=h), "outcome_at": (t0 + pd.Timedelta(days=3)).isoformat()} for h in (0, 1, 2)]
rows, st = apply_portfolio(fake, 1000, 2, 50, 0.3)
assert st["taken"] == 2 and st["skipped"] == 1 and rows[2]["taken"] is False and rows[2]["outcome"] == "t2"
_, st = apply_portfolio(fake, 1000, None, 50, 0.3)
assert st["taken"] == 3 and st["skipped"] == 0
print("Concurrency OK ->", st)
print("ALL OK")
