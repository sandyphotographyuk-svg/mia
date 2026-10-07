"""Chat routes — Phase 2: MiaAgent + sandboxes + DB persistence."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents.mia_agent import MiaAgent
from core.database import ChatMessage, get_db
from services.code_sandbox import run_python
from services.sql_sandbox import run_query

router = APIRouter()
agent = MiaAgent()


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str = "default"
    mode: str = "auto"


class RunCodeIn(BaseModel):
    source: str = Field(min_length=1, max_length=8000)
    timeout_seconds: float = 5.0


class RunSqlIn(BaseModel):
    sql: str = Field(min_length=1, max_length=6000)
    params: dict = {}
    allow_writes: bool = False


@router.post("/")
def chat(body: ChatIn, db: Session = Depends(get_db)):
    db.add(ChatMessage(role="user", content=body.message))
    db.commit()
    result = agent.reply(body.message, session_id=body.session_id, mode=body.mode)
    db.add(ChatMessage(role="assistant", content=result["reply"][:8000]))
    db.commit()
    return result


@router.get("/history/{session_id}")
def history(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .order_by(ChatMessage.id.desc())
        .limit(50)
        .all()
    )
    msgs = [{"role": r.role, "content": r.content} for r in reversed(rows)]
    return {"session_id": session_id, "messages": msgs}


@router.post("/run-code")
def run_code(body: RunCodeIn):
    return run_python(body.source, timeout_seconds=body.timeout_seconds)


@router.post("/run-sql")
def run_sql(body: RunSqlIn):
    return run_query(body.sql, params=body.params, allow_writes=body.allow_writes)

