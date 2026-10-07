"""Reminder routes — DB persistence + Celery dispatch (Phase 4)."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import Reminder, get_db
from services.notifier import dispatch

router = APIRouter()


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = ""
    due_at: datetime | None = None
    channel: str = "webhook"


def _shape(r: Reminder) -> dict:
    return {"id": r.id, "title": r.title, "body": r.body,
            "due_at": r.due_at.isoformat() if r.due_at else None,
            "channel": r.channel, "delivered": r.delivered}


@router.post("/")
def create_reminder(body: ReminderIn, db: Session = Depends(get_db)):
    r = Reminder(title=body.title, body=body.body, due_at=body.due_at, channel=body.channel)
    db.add(r)
    db.commit()
    db.refresh(r)
    task = None
    try:
        from core.celery_app import send_reminder_now

        if body.due_at is None:
            task = send_reminder_now.delay(r.id)
    except Exception:
        task = None
    return {"reminder": _shape(r), "task_id": getattr(task, "id", None)}


@router.get("/")
def list_reminders(db: Session = Depends(get_db)):
    rows = db.query(Reminder).order_by(Reminder.id.desc()).limit(100).all()
    return {"reminders": [_shape(r) for r in rows]}


@router.get("/{reminder_id}")
def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if r is None:
        raise HTTPException(404, "reminder not found")
    return {"reminder": _shape(r)}


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if r is None:
        raise HTTPException(404, "reminder not found")
    db.delete(r)
    db.commit()
    return {"ok": True, "deleted": reminder_id}


@router.post("/{reminder_id}/dispatch")
def dispatch_now(reminder_id: int, db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if r is None:
        raise HTTPException(404, "reminder not found")
    res = dispatch(r.title, r.body or "", r.channel)
    if res.get("ok"):
        r.delivered = True
        db.commit()
    return {"id": r.id, "dispatch": res, "delivered": r.delivered}


@router.post("/poll-due")
def poll_due(db: Session = Depends(get_db)):
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

