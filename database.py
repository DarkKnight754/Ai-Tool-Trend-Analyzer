"""
database.py - SQLite storage for AI tools data
Simple, zero-setup, production-ready for small/medium datasets
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "ai_tools.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # dict-like rows
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tools (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            description     TEXT,
            category        TEXT,
            summary         TEXT,
            best_for_tasks  TEXT,  -- JSON array
            audience_fit    TEXT,  -- JSON object
            tags            TEXT,  -- JSON array
            pricing_hint    TEXT,
            classification_method TEXT,
            keyword_confidence REAL,
            source          TEXT,
            scraped_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at      TEXT,
            tools_found INTEGER,
            status      TEXT
        );
    """)
    conn.commit()
    conn.close()
    print("[DB] Initialized database")


def save_tool(tool: Dict):
    """Insert or update a tool record."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO tools (
            name, description, category, summary,
            best_for_tasks, audience_fit, tags, pricing_hint,
            classification_method, keyword_confidence, source, scraped_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        tool.get("name"),
        tool.get("description"),
        tool.get("category"),
        tool.get("summary"),
        json.dumps(tool.get("best_for_tasks", [])),
        json.dumps(tool.get("audience_fit", {})),
        json.dumps(tool.get("tags", [])),
        tool.get("pricing_hint"),
        tool.get("classification_method"),
        tool.get("keyword_confidence"),
        tool.get("source"),
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def get_all_tools(category: str = None, search: str = None) -> List[Dict]:
    """Fetch tools with optional filters."""
    conn = get_conn()
    query = "SELECT * FROM tools WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (name LIKE ? OR summary LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY scraped_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    tools = []
    for row in rows:
        t = dict(row)
        t["best_for_tasks"] = json.loads(t.get("best_for_tasks") or "[]")
        t["audience_fit"] = json.loads(t.get("audience_fit") or "{}")
        t["tags"] = json.loads(t.get("tags") or "[]")
        tools.append(t)

    return tools


def get_category_stats() -> Dict:
    """Return count per category for charts."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM tools GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return {row["category"]: row["count"] for row in rows}


def clear_tools():
    """Clear all tool records (for fresh pipeline run)."""
    conn = get_conn()
    conn.execute("DELETE FROM tools")
    conn.commit()
    conn.close()


def log_run(tools_found: int, status: str = "success"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO pipeline_runs (run_at, tools_found, status) VALUES (?,?,?)",
        (datetime.now().isoformat(), tools_found, status)
    )
    conn.commit()
    conn.close()


def get_tool_count() -> int:
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    init_db()
    print(f"Tools in DB: {get_tool_count()}")
