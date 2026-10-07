"""Celery app + scheduled tasks for reminders and daily briefing."""
from celery import Celery
from celery.schedules import crontab

from .config import settings

celery_app = Celery(
    "mia",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "poll-due-reminders": {
            "task": "mia.dispatch_due_reminders",
            "schedule": 60.0,
        },
        "daily-briefing": {
            "task": "mia.daily_briefing",
            "schedule": crontab(hour=7, minute=0),
        },
    },
)


@celery_app.task(name="mia.dispatch_due_reminders")
def dispatch_due_reminders() -> dict:
    from datetime import datetime, timezone

    from .database import Reminder, SessionLocal
    from services.notifier import dispatch

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        due = db.query(Reminder).filter(
            Reminder.delivered.is_(False),
            Reminder.due_at.is_not(None),
            Reminder.due_at <= now,
        ).all()
        results = []
        for r in due:
            res = dispatch(r.title, r.body or "", r.channel)
            if res.get("ok"):
                r.delivered = True
            results.append({"id": r.id, "dispatch": res})
        db.commit()
        return {"checked": len(due), "results": results}
    finally:
        db.close()


@celery_app.task(name="mia.send_reminder_now")
def send_reminder_now(reminder_id: int) -> dict:
    from .database import Reminder, SessionLocal
    from services.notifier import dispatch

    db = SessionLocal()
    try:
        r = db.get(Reminder, reminder_id)
        if r is None:
            return {"ok": False, "error": f"reminder {reminder_id} not found"}
        res = dispatch(r.title, r.body or "", r.channel)
        if res.get("ok"):
            r.delivered = True
            db.commit()
        return {"ok": res.get("ok", False), "id": r.id, "dispatch": res}
    finally:
        db.close()


@celery_app.task(name="mia.daily_briefing")
def daily_briefing_task(focus: str = "day overview") -> dict:
    from .database import Reminder, SessionLocal
    from services.briefing import build_briefing

    db = SessionLocal()
    try:
        open_items = db.query(Reminder).filter(Reminder.delivered.is_(False)).limit(10).all()
        payload = [{"title": r.title, "body": r.body} for r in open_items]
        return build_briefing(focus=focus, reminders=payload)
    finally:
        db.close()

