"""Video-call signalling + daily briefing endpoints (Phase 4)."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services.briefing import build_briefing
from services.signalling import hub
from services.video_render import render_gif

router = APIRouter()


class SignalIn(BaseModel):
    session_id: str = "default"
    peer_id: str = "anon"
    kind: str = Field(pattern="^(offer|answer|ice|join|leave|briefing)$")
    payload: dict = {}


class BriefingIn(BaseModel):
    focus: str = "day overview"


@router.post("/signal")
def signal(body: SignalIn):
    return hub.push_signal(body.session_id, body.peer_id, body.kind, body.payload)


@router.post("/join")
def join(session_id: str = "default", peer_id: str = "anon"):
    return hub.join(session_id, peer_id)


@router.post("/leave")
def leave(session_id: str = "default", peer_id: str = "anon"):
    return hub.leave(session_id, peer_id)


@router.get("/history/{session_id}")
def signal_history(session_id: str, limit: int = Query(default=20, ge=1, le=50)):
    return hub.history(session_id, limit=limit)


@router.post("/daily-briefing")
def daily_briefing(body: BriefingIn):
    from core.database import Reminder, SessionLocal

    db = SessionLocal()
    try:
        items = db.query(Reminder).filter(Reminder.delivered.is_(False)).limit(10).all()
        payload = [{"title": r.title, "body": r.body} for r in items]
    finally:
        db.close()
    briefing = build_briefing(focus=body.focus, reminders=payload)
    preview = render_gif(label="daily-briefing", prompt=briefing["script"][:120])
    return {**briefing, "preview": preview}

