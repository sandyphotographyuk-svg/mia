"""Multi-modal generation router.

Detects intent (coding/sql/diagram/chart/ui/general), asks Ollama via
MiaAgent persona, and attaches a structured artifact:

- diagram -> {mermaid} extracted from ```mermaid fence or scaffolded
- chart   -> {python} runnable matplotlib script extracted or scaffolded
- ui      -> {schema} JSON with layout/components/style/interactions
- coding/sql -> raw text passthrough (+ optional sandbox execution lives in routes)
"""
from __future__ import annotations

import json
import re

MERMAID_RE = re.compile(r"```mermaid\s*(.*?)```", re.S | re.I)
PY_RE = re.compile(r"```python\s*(.*?)```", re.S | re.I)
JSON_RE = re.compile(r"```json\s*(.*?)```", re.S | re.I)

UI_SCHEMA_KEYS = ("layout", "components", "style", "interactions")


def detect_mode(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ("mermaid", "diagram", "architecture", "flowchart", "sequence diagram", "er diagram")):
        return "diagram"
    if any(k in m for k in ("chart", "graph", "plot", "matplotlib", "plotly", "visualise", "visualize", "bar chart", "line chart")):
        return "chart"
    if any(k in m for k in ("select ", "sql", "query", "database", "postgres", "where ", "join ")):
        return "sql"
    if any(k in m for k in ("ui design", "wireframe", "mockup", "component", "tailwind", "react component", "user scenario")):
        return "ui"
    if any(k in m for k in ("def ", "function", "code", "python", "typescript", "refactor", "debug", "implement")):
        return "coding"
    return "general"


def extract_mermaid(text: str) -> str | None:
    m = MERMAID_RE.search(text or "")
    return m.group(1).strip() if m else None


def extract_python(text: str) -> str | None:
    m = PY_RE.search(text or "")
    return m.group(1).strip() if m else None


def extract_json(text: str) -> dict | None:
    m = JSON_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def scaffold_mermaid(topic: str) -> str:
    return f"graph TD\n    U[User: {topic[:40]}] --> M[Mia Agent]\n    M --> O[Ollama / Qwen]\n    M --> R[Response]"


def scaffold_chart() -> str:
    return (
        "import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n\n"
        "labels = ['A', 'B', 'C']\nvalues = [3, 7, 5]\n"
        "plt.figure()\nplt.bar(labels, values)\nplt.title('Sample chart')\nplt.tight_layout()\n"
        "plt.savefig('/tmp/mia_chart.png')\nprint('saved /tmp/mia_chart.png')"
    )


def scaffold_ui(topic: str) -> dict:
    return {
        "layout": "single-column dashboard",
        "components": [{"type": "card", "title": topic[:60], "body": "Describe the scenario here."}],
        "style": {"theme": "dark", "accent": "#38bdf8"},
        "interactions": ["click card to expand", "filter list"],
    }


def coerce_ui_schema(data: object, topic: str) -> dict:
    if isinstance(data, dict) and all(k in data for k in UI_SCHEMA_KEYS):
        return {k: data[k] for k in UI_SCHEMA_KEYS}
    return scaffold_ui(topic)


def render(mode: str, topic: str, llm_text: str) -> dict | None:
    if mode == "diagram":
        return {"mermaid": extract_mermaid(llm_text) or scaffold_mermaid(topic)}
    if mode == "chart":
        return {"python": extract_python(llm_text) or scaffold_chart()}
    if mode == "ui":
        return {"schema": coerce_ui_schema(extract_json(llm_text), topic)}
    return None
