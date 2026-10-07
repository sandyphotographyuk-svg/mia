"""Tests for code + SQL sandboxes."""
from services.code_sandbox import run_python
from services.sql_sandbox import run_query


def test_python_ok():
    r = run_python("result = sum([1, 2, 3])")
    assert r["ok"] is True
    assert "6" in r["result"]


def test_python_blocked_import():
    r = run_python("import os\nresult = 1")
    assert r["ok"] is False
    assert "import" in r["error"].lower() or "validation" in r["error"].lower()


def test_python_blocked_open():
    r = run_python("result = open('/etc/passwd').read()")
    assert r["ok"] is False


def test_python_timeout():
    r = run_python("result = 1\nwhile True:\n    pass", timeout_seconds=1.0)
    assert r["ok"] is False
    assert "timeout" in r["error"].lower()


def test_sql_select_ok():
    r = run_query("SELECT name FROM users ORDER BY name")
    assert r["ok"] is True
    assert r["columns"] == ["name"]
    assert [x["name"] for x in r["rows"]] == ["Ava", "Ben", "Cara"]


def test_sql_params():
    r = run_query("SELECT name FROM users WHERE name = :n", params={"n": "Ben"})
    assert r["ok"] is True
    assert r["rows"] == [{"name": "Ben"}]


def test_sql_blocked_drop():
    r = run_query("DROP TABLE users")
    assert r["ok"] is False


def test_sql_blocked_multi():
    r = run_query("SELECT 1; SELECT 2")
    assert r["ok"] is False


def test_sql_join():
    r = run_query("SELECT u.name, o.total FROM users u JOIN orders o ON o.user_id = u.id ORDER BY o.total")
    assert r["ok"] is True
    assert len(r["rows"]) == 3
