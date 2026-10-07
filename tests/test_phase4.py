"""Phase 4 integration tests: reminders CRUD + dispatch, signalling, briefing."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import main as app_module
from services import notifier
from services.briefing import build_briefing
from services.signalling import SignallingHub


@pytest.fixture()
def api():
    with TestClient(app_module.app) as t:
        yield t


def test_reminder_crud(api):
    r = api.post("/api/reminders/", json={"title": "Call mum", "body": "evening", "channel": "desktop"})
    assert r.status_code == 200
    rid = r.json()["reminder"]["id"]
    assert r.json()["reminder"]["delivered"] is False

    r = api.get("/api/reminders/")
    assert any(x["id"] == rid for x in r.json()["reminders"])

    r = api.get(f"/api/reminders/{rid}")
    assert r.json()["reminder"]["title"] == "Call mum"

    r = api.delete(f"/api/reminders/{rid}")
    assert r.json() == {"ok": True, "deleted": rid}
    assert api.get(f"/api/reminders/{rid}").status_code == 404


def test_dispatch_desktop_marks_delivered(api, capsys):
    r = api.post("/api/reminders/", json={"title": "ping", "channel": "desktop"})
    rid = r.json()["reminder"]["id"]
    r = api.post(f"/api/reminders/{rid}/dispatch")
    body = r.json()
    assert body["delivered"] is True
    assert body["dispatch"]["ok"] is True
    assert "ping" in capsys.readouterr().err


def test_dispatch_unconfigured_channel_stays_undelivered(api):
    r = api.post("/api/reminders/", json={"title": "webhook me", "channel": "webhook"})
    rid = r.json()["reminder"]["id"]
    r = api.post(f"/api/reminders/{rid}/dispatch")
    body = r.json()
    assert body["delivered"] is False
    assert body["dispatch"]["ok"] is False


def test_poll_due_only_picks_overdue(monkeypatch, api):
    monkeypatch.setattr(notifier.settings, "DESKTOP_NOTIFY_ENABLED", True)
    past = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    future = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    api.post("/api/reminders/", json={"title": "overdue", "due_at": past, "channel": "desktop"})
    api.post("/api/reminders/", json={"title": "later", "due_at": future, "channel": "desktop"})
    r = api.post("/api/reminders/poll-due")
    body = r.json()
    assert body["checked"] == 1
    assert body["results"][0]["dispatch"]["ok"] is True


def test_notifier_unknown_channel():
    res = notifier.dispatch("t", "b", channel="pigeon")
    assert res["ok"] is False


def test_telegram_missing_creds(monkeypatch):
    monkeypatch.setattr(notifier.settings, "TELEGRAM_BOT_TOKEN", "")
    assert notifier.send_telegram("t", "b")["ok"] is False


def test_webhook_success(monkeypatch):
    import services.notifier as n

    class Resp:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(n.httpx, "post", lambda *a, **k: Resp())
    monkeypatch.setattr(n.settings, "GENERIC_WEBHOOK_URL", "http://hook")
    assert n.send_webhook("t", "b")["ok"] is True


def test_signalling_hub_flow():
    h = SignallingHub()
    assert h.join("s1", "alice")["peers"] == ["alice"]
    res = h.push_signal("s1", "alice", "offer", {"sdp": "x"})
    assert res["ok"] is True
    assert h.history("s1")["events"][0]["kind"] == "offer"
    assert h.push_signal("s1", "alice", "bogus", {})["ok"] is False
    assert h.leave("s1", "alice")["peers"] == []


def test_signal_routes(api):
    r = api.post("/api/video/signal", json={"session_id": "room1", "peer_id": "bob", "kind": "offer", "payload": {"sdp": "1"}})
    assert r.json()["ok"] is True
    r = api.get("/api/video/history/room1")
    assert r.json()["events"][0]["kind"] == "offer"
    assert api.post("/api/video/signal", json={"kind": "nope"}) .status_code == 422
    assert api.post("/api/video/join?session_id=room1&peer_id=bob").status_code == 200


def test_briefing_shape():
    b = build_briefing(focus="sprint", reminders=[{"title": "Standup", "body": "9:30"}])
    assert "Standup" in b["script"]
    assert set(b) >= {"script", "talking_points", "voice", "video", "date"}


def test_daily_briefing_route_includes_preview(api):
    api.post("/api/reminders/", json={"title": "Standup", "body": "9:30", "channel": "desktop"})
    r = api.post("/api/video/daily-briefing", json={"focus": "day overview"})
    body = r.json()
    assert "Standup" in body["script"]
    assert body["preview"]["ok"] is True
    assert body["preview"]["url"].startswith("/outputs/")


def test_celery_beat_schedule():
    from core.celery_app import celery_app

    sched = celery_app.conf.beat_schedule
    assert "mia.dispatch_due_reminders" in str(sched)
    assert "mia.daily_briefing" in str(sched)
