"""Outbound notifications. Telegram by default; prints to stdout if not configured."""
from __future__ import annotations
import requests
from .config import env, CFG
from .strategy import Setup


def send(text: str) -> None:
    channel = CFG["alerts"]["channel"]
    token, chat = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHAT_ID")
    if channel == "telegram" and token and chat:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True},
            timeout=15,
        )
    else:
        print("\n" + text + "\n")


def format_setup(s: Setup) -> str:
    risk_pct = (s.entry - s.stop) / s.entry * 100
    return (
        f"*MOMENTUM SETUP — {s.symbol}* ({s.asset_class})\n"
        f"Entry  `{s.entry:.4g}`\n"
        f"Stop   `{s.stop:.4g}`  (−{risk_pct:.1f}%)\n"
        f"T1     `{s.target1:.4g}`  (take half)\n"
        f"T2     `{s.target2:.4g}`\n"
        f"R:R    `{s.reward_risk:.1f}`   Size `${s.position_usd:,.0f}`\n"
        f"_{s.notes}_\n"
        f"Rules: exit on close below stop. After T1, move stop to entry."
    )


def format_breakout(bo) -> str:
    return (
        f"*IN PLAY — {bo.symbol}* broke {bo.breakout_level:.4g} on volume, "
        f"+{bo.impulse_pct:.0f}% in {CFG['breakout']['impulse_window_days']}d. Watching for pullback."
    )


def format_exit(alert: dict, reason: str, price: float) -> str:
    return f"*EXIT — {alert['symbol']}*  {reason} at `{price:.4g}` (entry {alert['entry']:.4g})"
