"""Multi-channel notifier: Telegram bot, generic webhook, desktop log.

Each channel degrades gracefully (returns delivered=False + reason)
so a missing token/URL never crashes reminder dispatch.
"""
from __future__ import annotations

import httpx

from core.config import settings


def send_telegram(title: str, body: str) -> dict:
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return {"ok": False, "channel": "telegram", "reason": "TELEGRAM_BOT_TOKEN/CHAT_ID not set"}
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"*{title}*\n{body}", "parse_mode": "Markdown"},
            timeout=15.0,
        )
        r.raise_for_status()
        return {"ok": True, "channel": "telegram"}
    except Exception as exc:
        return {"ok": False, "channel": "telegram", "reason": str(exc)}


def send_webhook(title: str, body: str) -> dict:
    url = settings.GENERIC_WEBHOOK_URL
    if not url:
        return {"ok": False, "channel": "webhook", "reason": "GENERIC_WEBHOOK_URL not set"}
    try:
        r = httpx.post(url, json={"title": title, "body": body, "source": "mia"}, timeout=15.0)
        r.raise_for_status()
        return {"ok": True, "channel": "webhook"}
    except Exception as exc:
        return {"ok": False, "channel": "webhook", "reason": str(exc)}


def send_desktop(title: str, body: str) -> dict:
    if not settings.DESKTOP_NOTIFY_ENABLED:
        return {"ok": False, "channel": "desktop", "reason": "disabled"}
    import sys

    print(f"[Mia desktop] {title}: {body}", file=sys.stderr)
    return {"ok": True, "channel": "desktop"}


def dispatch(title: str, body: str = "", channel: str = "webhook") -> dict:
    """Route to one channel ('telegram'|'webhook'|'desktop'|'all')."""
    channel = (channel or "webhook").lower()
    if channel == "all":
        results = [dispatch(title, body, c) for c in ("telegram", "webhook", "desktop")]
        return {"ok": any(r["ok"] for r in results), "channel": "all", "results": results}
    sender = {"telegram": send_telegram, "webhook": send_webhook, "desktop": send_desktop}.get(channel)
    if sender is None:
        return {"ok": False, "channel": channel, "reason": f"unknown channel '{channel}'"}
    return sender(title, body)
