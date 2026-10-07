"""Tests for OllamaClient (mocked HTTP) and persona prompts."""
from agents.ollama_client import OllamaClient
from agents.persona import build_system_prompt


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


def test_chat_success(monkeypatch):
    import agents.ollama_client as oc

    def fake_post(url, json=None, timeout=None):
        assert "/api/chat" in url
        return FakeResp({"message": {"content": "hello from qwen"}})

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    c = OllamaClient(base_url="http://x", model="m", timeout_seconds=5)
    assert c.chat([{"role": "user", "content": "hi"}]) == "hello from qwen"


def test_chat_offline_stub(monkeypatch):
    import agents.ollama_client as oc

    def boom(url, json=None, timeout=None):
        raise ConnectionError("down")

    monkeypatch.setattr(oc.httpx, "post", boom)
    c = OllamaClient(base_url="http://x", model="m", timeout_seconds=5)
    out = c.chat([{"role": "user", "content": "hi"}])
    assert "offline" in out.lower()


def test_health_false(monkeypatch):
    import agents.ollama_client as oc

    def boom(url, timeout=None):
        raise ConnectionError("down")

    monkeypatch.setattr(oc.httpx, "get", boom)
    assert OllamaClient(base_url="http://x").health() is False


def test_persona_modes():
    assert "Mermaid" in build_system_prompt("diagram")
    assert "matplotlib" in build_system_prompt("chart")
    assert "parametrized" in build_system_prompt("sql")
    assert "JSON" in build_system_prompt("ui")
    assert "Mia" in build_system_prompt("general")
