"""Mia FastAPI entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import init_db
from api.routes_chat import router as chat_router
from api.routes_reminders import router as reminders_router
from api.routes_video import router as video_router
from api.routes_avatar import router as avatar_router
from api.routes_render import router as render_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mia API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(reminders_router, prefix="/api/reminders", tags=["reminders"])
app.include_router(video_router, prefix="/api/video", tags=["video"])
app.include_router(avatar_router, prefix="/api/avatar", tags=["avatar"])
app.include_router(render_router, prefix="/api/render", tags=["render"])

try:
    from pathlib import Path

    _out = Path(__file__).resolve().parent / settings.MIA_OUTPUTS_DIR
    _out.mkdir(parents=True, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=str(_out)), name="outputs")
except Exception:
    pass

try:
    import socketio as _socketio

    from services.signalling import get_socket_server as _get_sio

    _sio = _get_sio()
    app.mount("/ws", _socketio.ASGIApp(_sio), name="signalling")
except Exception:
    pass


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.MIA_ENV, "model": settings.OLLAMA_MODEL}
