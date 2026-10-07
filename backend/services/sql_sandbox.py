"""Safe parametrized SQL sandbox (read-only by default).

- Only SELECT / WITH / EXPLAIN allowed unless allow_writes=True.
- Multi-statement and comment tricks rejected.
- Runs against an in-memory SQLite demo DB seeded with sample tables.
"""
from __future__ import annotations

import re
import sqlite3

WRITE_RE = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|VACUUM)\b", re.I)


def validate_sql(sql: str, allow_writes: bool = False) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise ValueError("empty query")
    if cleaned.count(";") > 0:
        raise ValueError("only a single statement is allowed")
    if "--" in cleaned or "/*" in cleaned:
        raise ValueError("SQL comments are not allowed")
    first = cleaned.split(None, 1)[0].upper()
    if first not in ("SELECT", "WITH", "EXPLAIN"):
        if not (allow_writes and first in ("INSERT", "UPDATE", "DELETE")):
            raise ValueError(f"statement type '{first}' is not allowed (read-only sandbox)")
    if not allow_writes and WRITE_RE.search(cleaned):
        raise ValueError("write keywords are not allowed in read-only mode")
    return cleaned


def seed_demo_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
        DELETE FROM users;
        INSERT INTO users (name, email) VALUES
          ('Ava','ava@example.com'),('Ben','ben@example.com'),('Cara','cara@example.com');
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL);
        DELETE FROM orders;
        INSERT INTO orders (user_id, total) VALUES (1, 42.5),(2, 19.99),(1, 7.0);
        """
    )
    conn.commit()


def run_query(sql: str, params: dict | tuple | None = None, allow_writes: bool = False) -> dict:
    """Execute a validated query against the demo DB. Returns {ok, columns, rows} or {ok, error}."""
    if len(sql) > 6000:
        return {"ok": False, "error": "query too long (max 6000 chars)"}
    try:
        cleaned = validate_sql(sql, allow_writes=allow_writes)
    except ValueError as exc:
        return {"ok": False, "error": f"ValidationError: {exc}"}
    try:
        conn = sqlite3.connect(":memory:")
        seed_demo_db(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(cleaned, params or {})
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = [dict(r) for r in cur.fetchmany(100)]
            return {"ok": True, "columns": cols, "rows": rows}
        conn.commit()
        return {"ok": True, "columns": [], "rows": [], "rowcount": cur.rowcount}
    except Exception as exc:  # noqa: BLE001 — report DB errors to caller
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        try:
            conn.close()
        except Exception:
            pass
