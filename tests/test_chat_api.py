"""API-level tests for chat + sandbox routes (FastAPI TestClient)."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_roundtrip(monkeypatch):
    import api.routes_chat as rc

    def fake_reply(self, message, session_id="default", mode="auto"):
        return {"reply": f"echo:{message}", "mode": "general", "artifact": None, "session_id": session_id}

    monkeypatch.setattr(rc.MiaAgent, "reply", fake_reply)
    r = client.post("/api/chat/", json={"message": "hello mia"})
    assert r.status_code == 200
    assert r.json()["reply"] == "echo:hello mia"


def test_run_code_route():
    r = client.post("/api/chat/run-code", json={"source": "result = 2 + 3"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_run_sql_route():
    r = client.post("/api/chat/run-sql", json={"sql": "SELECT COUNT(*) AS n FROM users"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["rows"][0]["n"] == 3


def test_history_route():
    r = client.get("/api/chat/history/default")
    assert r.status_code == 200
    assert "messages" in r.json()
