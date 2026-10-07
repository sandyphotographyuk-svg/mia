"""Daily briefing builder: compiles Mia's summary script + voice/video params.

Avoids text-typing fatigue by pre-compiling structured talking points
the frontend video-call UI can speak/animate directly.
"""
from __future__ import annotations

from datetime import datetime, timezone

VOICE_DEFAULTS = {"voice": "mia-warm", "rate": 1.0, "pitch": 1.0}
VIDEO_DEFAULTS = {"avatar_style": "portrait", "frames": 12, "fps": 6}


def build_briefing(
    focus: str = "day overview",
    reminders: list[dict] | None = None,
    date: datetime | None = None,
) -> dict:
    day = (date or datetime.now(timezone.utc)).strftime("%A, %d %B %Y")
    reminders = reminders or []
    points = [f"Good morning — here's your {focus} for {day}."]
    for r in reminders[:5]:
        points.append(f"• {r.get('title', 'Reminder')}: {r.get('body', '')}".strip())
    if not reminders:
        points.append("• No open reminders — a clear runway. Want me to plan something?")
    points.append("Anything you'd like to dive into first?")
    script = "\n".join(points)
    return {
        "date": day,
        "focus": focus,
        "script": script,
        "talking_points": points,
        "voice": dict(VOICE_DEFAULTS),
        "video": dict(VIDEO_DEFAULTS),
    }
