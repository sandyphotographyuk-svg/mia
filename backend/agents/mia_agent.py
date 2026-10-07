"""Mia agent orchestrator: persona + Ollama + multimodal router."""
from __future__ import annotations

from agents.ollama_client import OllamaClient, get_client
from agents.persona import build_system_prompt
from services.multimodal import detect_mode, render


class MiaAgent:
    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or get_client()

    def reply(self, message: str, session_id: str = "default", mode: str = "auto") -> dict:
        effective_mode = detect_mode(message) if mode == "auto" else mode
        system = build_system_prompt(effective_mode)
        text = self.client.chat(
            [{"role": "user", "content": message}],
            system=system,
        )
        artifact = render(effective_mode, message, text)
        return {"reply": text, "mode": effective_mode, "artifact": artifact, "session_id": session_id}
