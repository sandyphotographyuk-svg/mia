"""Ollama connection wrapper for local Qwen models.

Uses httpx against Ollama's /api/chat + /api/generate endpoints so tests
can mock HTTP without a live server. Falls back gracefully when offline.
"""
from __future__ import annotations

import httpx

from core.config import settings


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[dict], system: str | None = None) -> str:
        """Send chat messages; returns assistant text (or offline stub)."""
        payload_messages = list(messages)
        if system:
            payload_messages = [{"role": "system", "content": system}] + payload_messages
        try:
            r = httpx.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": payload_messages, "stream": False},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "")
        except Exception as exc:
            return f"[Mia offline — Ollama unreachable: {exc}]"

    def generate(self, prompt: str, system: str | None = None) -> str:
        try:
            r = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "system": system or "", "stream": False},
                timeout=self.timeout,
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as exc:
            return f"[Mia offline — Ollama unreachable: {exc}]"


_default_client: OllamaClient | None = None


def get_client() -> OllamaClient:
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client
