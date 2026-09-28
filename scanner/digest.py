"""Daily 7am digest: upcoming catalysts, top footprints, in-play assets, scoreboard."""
from __future__ import annotations
from datetime import date, timedelta
from .db import Store
from . import alerts as notify
from .catalysts import main as refresh_catalysts
from .footprints import screen
from .outcomes import scoreboard


def build() -> str:
    store = Store()
    refresh_catalysts()
    fps = screen()
    cats = [c for c in store.select("catalysts") if date.fromisoformat(str(c["event_date"])[:10]) <= date.today() + timedelta(days=14)]
    cats.sort(key=lambda c: c["event_date"])
    watching = store.watching()
    sb = scoreboard(store.select("alerts"))

    lines = [f"*DAILY DIGEST — {date.today():%a %d %b}*", ""]
    lines.append("*Upcoming catalysts (14d)*")
    lines += [f"• {c['event_date']} {c['symbol']} — {c['event_type']} ({c['lean']}) {c.get('title') or ''}"[:120] for c in cats[:12]] or ["• none"]
    lines += ["", "*Footprints (unusual activity)*"]
    lines += [f"• {f['symbol']} vol×{f['volume_multiple']} move {f['move_pct']:+.1f}% OI {f['oi_change_pct'] or '–'}% {'news' if f['has_news'] else 'NO NEWS'}" for f in fps[:8]] or ["• none"]
    lines += ["", "*In play (watching for pullback)*"]
    lines += [f"• {w['symbol']} broke {w['breakout_level']:.4g} on {w['breakout_date']}" for w in watching] or ["• none"]
    lines += ["", "*Scoreboard*"]
    for label in ("overall", "pullback", "breakout"):
        st = sb[label]
        if st["alerts_graded"]:
            vs = f"{st['vs_hold_7d']:+.1f}pp" if st["vs_hold_7d"] is not None else "–"
            lines.append(f"• {label}: {st['alerts_graded']} graded · win {st['win_rate']:.0%} · avg R {st['avg_r']} · vs hold-7d {vs}")
        else:
            lines.append(f"• {label}: no graded alerts yet")
    return "\n".join(lines)


if __name__ == "__main__":
    notify.send(build())
