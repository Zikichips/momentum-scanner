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
scan.universe = lambda: [("QNT/USD", "crypto", None)]

# Stage A must run on the breakout day, so first run at the breakout bar's close.
BO_CUT = pd.Timestamp("2026-08-30 23:00:00+00:00")
hist = full[full.index <= BO_CUT]
# "Now" is 1h after the daily bar closed, at the closing price: an on-time breakout.
NOW = BO_CUT + pd.Timedelta(hours=2)
scan._now = lambda: NOW
price = {"px": None}
data.last_price = lambda symbol, asset_class, ex=None: price["px"] if price["px"] is not None else float(hist["close"].iloc[-1])
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

# Exit notices are sent once, not every 15-minute scan (STOP / T1 / T2).
CFG["account"]["max_concurrent_trades"] = None
last = hist.iloc[-1]
sent = []
scan.notify.send = sent.append
for sym, stop, t1, t2 in (("STOPX/USD", last["close"] * 2, last["close"] * 3, last["close"] * 4),
                          ("T1X/USD", last["close"] * 0.5, last["high"] * 0.99, last["high"] * 10),
                          ("T2X/USD", last["close"] * 0.5, last["high"] * 0.8, last["high"] * 0.9)):
    scan._insert_alert(store, Setup(symbol=sym, asset_class="crypto", entry=float(last["close"]), stop=float(stop),
                                    target1=float(t1), target2=float(t2), reward_risk=2.0, position_usd=100.0,
                                    retrace_pct=0.0, ema_value=None, pullback_low=None, entry_type="breakout"), None)
scan.manage_exits(store)
first = [m for m in sent if any(k in m for k in ("STOPX", "T1X", "T2X"))]
assert len(first) == 3, first
sent.clear()
scan.manage_exits(store)
assert not [m for m in sent if any(k in m for k in ("STOPX", "T1X", "T2X"))], sent
print("Exit notices OK -> one each, no repeats")

# Late breakouts: first seen > max_alert_delay_hours after the close, or price > max_chase_pct
# above the close -> in_play marked late, one heads-up, no breakout-entry alert.
hist = full[full.index <= BO_CUT]
close = float(hist["close"].iloc[-1])
n_alerts = len(store.select("alerts"))
cases = (("LATE/USD", BO_CUT + pd.Timedelta(hours=6), None),               # 5h after the close
         ("CHASE/USD", NOW, close * 1.06),                                   # on time, but +6%
         ("EDGE/USD", BO_CUT + pd.Timedelta(hours=5), close * 1.05))       # exactly 4h, exactly +5%: on time
for sym, now, px in cases:
    scan._now, price["px"] = (lambda now=now: now), px
    scan.universe = lambda sym=sym: [(sym, "crypto", None)]
    sent.clear()
    assert scan.stage_a(store) == 1
    ip = [r for r in store.select("in_play") if r["symbol"] == sym][0]
    new = [x for x in store.select("alerts") if x["symbol"] == sym]
    if sym == "EDGE/USD":
        assert ip["late"] is False and len(new) == 1, (ip, new)
    else:
        assert ip["late"] is True and ip["status"] == "watching" and not new, (ip, new)
        assert len(sent) == 1 and "LATE BREAKOUT" in sent[0] and "\n" not in sent[0], sent
print("Late breakouts OK ->", sent[0] if sent else "")
# Stage B still tracks a late breakout and can fire a pullback entry on it.
hist = full[full.index <= CUT]
for r in store.watching():
    if r["symbol"] not in ("LATE/USD",):
        store.update("in_play", r["id"], {"status": "expired"})
assert scan.stage_b(store) == 1
assert [x["entry_type"] for x in store.select("alerts") if x["symbol"] == "LATE/USD"] == ["pullback"]
print("Late breakout -> Stage B pullback OK")

# Listing alerts: Stage B on a listing in_play row tags the alert source="listing", and the
# scoreboard scores it as its own group, not with Stage A pullbacks.
lst = Setup(symbol="LST/USD", asset_class="crypto", entry=10.0, stop=9.0, target1=12.0, target2=14.0, reward_risk=4.0,
            position_usd=100.0, retrace_pct=30.0, ema_value=9.5, pullback_low=9.1)
scan._insert_alert(store, lst, None, "coinbase", "listing")
la = [x for x in store.select("alerts") if x["symbol"] == "LST/USD"][0]
assert la["source"] == "listing" and la["exchange"] == "coinbase" and la["entry_type"] == "pullback"
store.update("alerts", la["id"], {"outcome": "t2", "r_multiple": 4.0, "rule_return": 40.0, "hold_7d_return": 20.0})
sbl = outcomes.scoreboard(store.select("alerts"))
assert sbl["listing"]["alerts_graded"] == 1 and sbl["listing"]["avg_r"] == 4.0
assert all(outcomes.group_of(x) != "pullback" for x in store.select("alerts") if x["symbol"] == "LST/USD")
assert outcomes.scoreboard_row(sbl)["listing_n_graded"] == 1
print("Listing alerts scored apart OK")

# Stale alerts: kept, but not a position and not scored.
CFG["account"]["max_concurrent_trades"] = 2
before = outcomes.scoreboard(store.select("alerts"))["overall"]["alerts_total"]
st = [x for x in store.select("alerts") if x["symbol"] == "EDGE/USD"][0]
assert any(x["id"] == st["id"] for x in store.open_alerts())
store.update("alerts", st["id"], {"stale": True})
assert all(x["id"] != st["id"] for x in store.open_alerts())
assert outcomes.scoreboard(store.select("alerts"))["overall"]["alerts_total"] == before - 1
assert any(x["id"] == st["id"] for x in store.select("alerts"))   # still on record
print("Stale alerts OK")

# Listing watcher: title parsing.
from scanner import listings as li
assert li.parse_tickers("upbit", "뉴메레르(NMR) KRW, USDT 마켓 디지털 자산 추가") == ["NMR"]
assert li.parse_tickers("upbit", "돌핀(POD) 신규 거래지원 안내 (KRW, BTC, USDT 마켓)") == ["POD"]
assert li.parse_tickers("upbit", "BTC, USDT 마켓 신규 거래지원 안내 (BICO, BMT, NIL, GWEI) (BICO, BMT, NIL, GWEI 거래지원 개시 시점 추가 변경 안내)") == ["BICO", "BMT", "NIL", "GWEI"]
assert li.parse_tickers("upbit", "아이콘(ICX) 거래지원 종료 안내 (10/19 15:00)") == []          # delisting
assert li.parse_tickers("upbit", "블라스트(BLAST) 거래 유의 종목 지정 안내") == []                # warning
assert li.parse_tickers("bithumb", "[마켓 추가] 뉴메레르(NMR) 원화 마켓 추가") == ["NMR"]
assert li.parse_tickers("binance", "Binance Will List Hyperliquid (HYPE) with Seed Tag Applied") == ["HYPE"]
assert li.parse_tickers("binance", "Binance Futures Will Launch USDⓈ-Margined CTUSDT Perpetual Contract (2026-10-01)") == ["CT"]
for t in ("Binance Will Add Hyperliquid (HYPE) on Earn, Buy Crypto, Convert, VIP Loan & Margin",
          "Binance Exchange Adds GoPro (GPROB) and Reddit (RDDTB) bStocks Trading Pairs on Binance Spot/Convert - 2026-09-16",
          "Binance Futures Will Launch Multiple TradFi USDⓈ-Margined Perpetual Contracts (2026-10-06)",
          "Binance Margin Will Add New Pairs - 2026-09-23"):
    assert li.parse_tickers("binance", t) == [], t
print("Listing parsing OK")

# Listing watcher: a fresh Upbit listing on a Coinbase-tradeable coin -> one Telegram line (no "buy"),
# a catalysts row, an in_play row (source listing); a repeat poll doesn't fire again; an old one is
# stored only; a coin not on Coinbase is stored, not notified, not put in play.
T0 = pd.Timestamp("2026-09-01 10:00", tz="UTC")
class FakeCB:
    markets = {"NEWC/USD": {"info": {}}, "OLDC/USD": {"info": {}}}
    def fetch_ticker(self, sym): return {"last": 13.0}
    def fetch_ohlcv(self, sym, timeframe="1m", since=None, limit=300):
        step = 60_000 if timeframe == "1m" else 3_600_000
        return [[since + i * step, 10, 14 if timeframe == "1h" else 10, 9.5, 10, 1] for i in range(5)]
li._ex = lambda ex_id: FakeCB()
li.trading_open = lambda source, ticker, title="": True
anns = [li.Announcement("upbit", "1", "뉴코인(NEWC) KRW 마켓 디지털 자산 추가", ["NEWC"], T0, "u1"),
        li.Announcement("upbit", "2", "올드코인(OLDC) KRW 마켓 디지털 자산 추가", ["OLDC"], T0 - pd.Timedelta(hours=8), "u2"),
        li.Announcement("upbit", "3", "엑스(NOTCB) KRW 마켓 디지털 자산 추가", ["NOTCB"], T0, "u3")]
li._poll = li.poll
li.poll = lambda pages=1, store=None, now=None: anns
li.notify.send = sent.append
sent.clear()
assert li.run(store, now=T0 + pd.Timedelta(minutes=5)) == 3
assert len(sent) == 1 and "NEWC" in sent[0] and "Upbit" in sent[0] and "\n" not in sent[0] and "buy" not in sent[0].lower(), sent
cats = {r["symbol"]: r for r in store.select("catalysts", event_type="listing")}
assert cats["NEWC/USD"]["notified"] and cats["NEWC/USD"]["price_pre"] == 10 and cats["NEWC/USD"]["price_detect"] == 13
assert not cats["OLDC/USD"]["notified"] and not cats["NOTCB/USD"]["coinbase_tradeable"] and not cats["NOTCB/USD"]["notified"]
ip = [r for r in store.select("in_play") if r.get("source") == "listing"]
assert [r["symbol"] for r in ip] == ["NEWC/USD"] and ip[0]["exchange"] == "coinbase" and ip[0]["breakout_level"] == 10 and ip[0]["impulse_high"] == 14
sent.clear()
assert li.run(store, now=T0 + pd.Timedelta(minutes=10)) == 0 and not sent        # dedupe
# +1h / +24h prices filled once those times pass
li.run(store, now=T0 + pd.Timedelta(hours=25))
c = [r for r in store.select("catalysts", event_type="listing") if r["symbol"] == "NEWC/USD"][0]
assert c["price_1h"] == 10 and c["price_24h"] == 10, c
print("Listing watcher OK ->", sent or "(no repeat)")

# Source health: "down" once after 3 failed runs in a row, nothing on the 4th, "recovered" once.
def broken(pages=1): raise ConnectionError("403 Forbidden")
ok_fetchers = dict(li.FETCHERS)
li.FETCHERS = {k: (broken if k == "upbit" else (lambda pages=1: [anns[0]])) for k in ok_fetchers}
health = []
for i in range(5):
    sent.clear(); li._poll(store=store, now=T0); health.append(list(sent))
assert health[:2] == [[], []] and len(health[2]) == 1 and "DOWN" in health[2][0] and "Upbit" in health[2][0], health
assert health[3] == [] and health[4] == [], health
li.FETCHERS["upbit"] = lambda pages=1: [anns[0]]
sent.clear(); li._poll(store=store, now=T0)
assert len(sent) == 1 and "RECOVERED" in sent[0] and "Upbit" in sent[0], sent
sent.clear(); li._poll(store=store, now=T0); assert not sent
li.FETCHERS["binance"] = lambda pages=1: []          # empty = failure too
for i in range(3): sent.clear(); li._poll(store=store, now=T0)
assert len(sent) == 1 and "Binance" in sent[0], sent
print("Source health OK ->", health[2][0])
print("ALL OK")
