"""WebRTC signalling hub (python-socketio ASGI + in-memory session store).

Keeps peer exchange server-light: the hub relays offers/answers/ICE,
tracks presence per session, and stores a short signal history for
reconnects. No media flows through the server (peer-to-peer).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

SESSION_TTL_SECONDS = 4 * 3600
MAX_HISTORY = 50


@dataclass
class SignalSession:
    session_id: str
    peers: set[str] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)


class SignallingHub:
    def __init__(self) -> None:
        self._sessions: dict[str, SignalSession] = {}

    def _get(self, session_id: str) -> SignalSession:
        sess = self._sessions.get(session_id)
        if sess is None:
            sess = SignalSession(session_id=session_id)
            self._sessions[session_id] = sess
        sess.last_active = time.time()
        return sess

    def join(self, session_id: str, peer_id: str) -> dict:
        sess = self._get(session_id)
        sess.peers.add(peer_id)
        return {"session_id": session_id, "peers": sorted(sess.peers)}

    def leave(self, session_id: str, peer_id: str) -> dict:
        sess = self._get(session_id)
        sess.peers.discard(peer_id)
        return {"session_id": session_id, "peers": sorted(sess.peers)}

    def push_signal(self, session_id: str, peer_id: str, kind: str, payload: dict) -> dict:
        if kind not in ("offer", "answer", "ice", "join", "leave", "briefing"):
            return {"ok": False, "error": f"unknown signal kind '{kind}'"}
        sess = self._get(session_id)
        sess.peers.add(peer_id)
        event = {"session_id": session_id, "from": peer_id, "kind": kind,
                 "payload": payload or {}, "ts": time.time()}
        sess.history.append(event)
        sess.history = sess.history[-MAX_HISTORY:]
        return {"ok": True, "event": event, "peers": sorted(sess.peers)}

    def history(self, session_id: str, limit: int = 20) -> dict:
        sess = self._get(session_id)
        return {"session_id": session_id, "peers": sorted(sess.peers),
                "events": sess.history[-max(1, min(limit, MAX_HISTORY)):]}

    def prune(self) -> int:
        now = time.time()
        stale = [k for k, s in self._sessions.items() if now - s.last_active > SESSION_TTL_SECONDS]
        for k in stale:
            del self._sessions[k]
        return len(stale)


hub = SignallingHub()


def get_socket_server():
    """Build the python-socketio AsyncServer (import lazily so tests stay light)."""
    import socketio

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

    @sio.event
    async def connect(sid, environ):
        await sio.emit("mia:hello", {"sid": sid}, to=sid)

    @sio.event
    async def disconnect(sid):
        pass

    @sio.on("mia:join")
    async def on_join(sid, data):
        res = hub.join(data.get("session_id", "default"), data.get("peer_id", sid))
        await sio.emit("mia:presence", res, to=sid)
        return res

    @sio.on("mia:signal")
    async def on_signal(sid, data):
        res = hub.push_signal(
            data.get("session_id", "default"), data.get("peer_id", sid),
            data.get("kind", ""), data.get("payload", {}),
        )
        await sio.emit("mia:signal", res.get("event", res), skip_sid=sid)
        return res

    return sio
