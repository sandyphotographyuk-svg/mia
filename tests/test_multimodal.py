"""Tests for multimodal router + MiaAgent orchestration."""
from agents.mia_agent import MiaAgent
from agents.ollama_client import OllamaClient
from services import multimodal as mm


def test_detect_mode():
    assert mm.detect_mode("draw a mermaid architecture diagram") == "diagram"
    assert mm.detect_mode("plot a bar chart with matplotlib") == "chart"
    assert mm.detect_mode("SELECT * FROM users WHERE id=1") == "sql"
    assert mm.detect_mode("design a UI mockup component") == "ui"
    assert mm.detect_mode("write python code to sort a list") == "coding"
    assert mm.detect_mode("how are you today?") == "general"


def test_render_diagram_extract():
    text = "here:\n```mermaid\ngraph TD\n A-->B\n```"
    out = mm.render("diagram", "topic", text)
    assert out == {"mermaid": "graph TD\n A-->B"}


def test_render_diagram_scaffold():
    out = mm.render("diagram", "orders", "no fence here")
    assert "graph TD" in out["mermaid"]


def test_render_chart_scaffold():
    out = mm.render("chart", "sales", "plain text")
    assert "matplotlib" in out["python"]


def test_render_ui_coerce():
    out = mm.render("ui", "dashboard", "no json")
    assert set(out["schema"].keys()) == {"layout", "components", "style", "interactions"}
    good = '```json\n{"layout":"x","components":[],"style":{},"interactions":[]}\n```'
    out2 = mm.render("ui", "dashboard", good)
    assert out2["schema"]["layout"] == "x"


class StubClient(OllamaClient):
    def __init__(self):
        super().__init__(base_url="http://stub", model="stub", timeout_seconds=5)

    def chat(self, messages, system=None):
        return "```mermaid\ngraph TD\n A-->B\n```"


def test_agent_diagram_path():
    agent = MiaAgent(client=StubClient())
    res = agent.reply("make me a mermaid diagram of login flow")
    assert res["mode"] == "diagram"
    assert res["artifact"]["mermaid"].startswith("graph TD")
    assert res["session_id"] == "default"
