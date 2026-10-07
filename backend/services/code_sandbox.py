"""Safe Python code-interpreter sandbox.

- Blocks dangerous imports/attributes (os, sys, subprocess, socket, open, exec...).
- Runs untrusted code in a separate process with a wall-clock timeout.
- Exposes only a small safe-builtin set + math.
"""
from __future__ import annotations

import ast
import multiprocessing as mp

BLOCKED_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "input",
    "os", "sys", "subprocess", "socket", "shutil", "pathlib",
    "pty", "signal", "threading", "multiprocessing", "ctypes",
}
BLOCKED_ATTRS = {"__dict__", "__class__", "__bases__", "__subclasses__", "gi_frame", "f_globals"}

ALLOWED_BUILTINS = {
    "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
    "range": range, "enumerate": enumerate, "zip": zip, "sorted": sorted,
    "round": round, "print": print,
}


def validate_source(source: str) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("imports are not allowed in the sandbox")
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            raise ValueError(f"blocked name: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRS:
            raise ValueError(f"blocked attribute: {node.attr}")


def _worker(source: str, queue: mp.Queue) -> None:
    try:
        validate_source(source)
        import math as _math

        safe_globals = {"__builtins__": dict(ALLOWED_BUILTINS), "math": _math}
        buf: dict = {}
        exec(compile(source, "<mia-sandbox>", "exec"), safe_globals, buf)
        result = buf.get("result", None)
        queue.put({"ok": True, "result": repr(result)[:2000]})
    except Exception as exc:  # noqa: BLE001 — sandbox must report, not raise
        queue.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def run_python(source: str, timeout_seconds: float = 5.0) -> dict:
    """Execute source in a subprocess. Returns {ok, result} or {ok, error}."""
    if len(source) > 8000:
        return {"ok": False, "error": "source too long (max 8000 chars)"}
    try:
        validate_source(source)
    except Exception as exc:
        return {"ok": False, "error": f"ValidationError: {exc}"}
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(source, queue))
    proc.start()
    proc.join(timeout_seconds)
    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        return {"ok": False, "error": f"timeout after {timeout_seconds}s"}
    if queue.empty():
        return {"ok": False, "error": "no result (crashed?)"}
    return queue.get()
