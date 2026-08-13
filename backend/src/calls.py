import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
import memory

logger = logging.getLogger("calls")

CALL_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id          TEXT PRIMARY KEY,
    caller_name TEXT,
    status      TEXT NOT NULL,
    reason      TEXT,
    duration    INTEGER,
    created_at  TEXT NOT NULL
)
"""

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(CALL_SCHEMA)
    return conn

def init_db(db_path: str | None = None) -> str:
    path = db_path or memory.default_db_path()
    with _connect(path) as conn:
        conn.commit()
    logger.info("Calls database initialized at %s", path)
    return path

def _sync_to_json(db_path: str) -> None:
    """Read all calls from DB and write them to backend/calls.json."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(backend_dir, "calls.json")
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM calls ORDER BY created_at DESC").fetchall()
            
        calls_list = []
        for row in rows:
            calls_list.append({
                "id": row["id"],
                "caller_name": row["caller_name"],
                "status": row["status"],
                "reason": row["reason"],
                "duration": row["duration"],
                "created_at": row["created_at"]
            })
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(calls_list, f, ensure_ascii=False, indent=2)
            
        logger.info("Synced %d calls to %s", len(calls_list), json_path)
    except Exception as e:
        logger.error("Failed to sync calls to JSON: %s", e)

def save_call(
    call_id: str,
    caller_name: str | None,
    status: str,
    reason: str,
    duration: int,
    db_path: str | None = None
) -> None:
    path = db_path or memory.default_db_path()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO calls (id, caller_name, status, reason, duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                caller_name = excluded.caller_name,
                status      = excluded.status,
                reason      = excluded.reason,
                duration    = excluded.duration,
                created_at  = excluded.created_at
            """,
            (call_id, caller_name, status, reason, duration, created_at)
        )
        conn.commit()
        
    logger.info("Saved call %s (status: %s) to DB", call_id, status)
    _sync_to_json(path)

def get_calls(db_path: str | None = None) -> list[dict]:
    path = db_path or memory.default_db_path()
    with _connect(path) as conn:
        rows = conn.execute("SELECT * FROM calls ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]
