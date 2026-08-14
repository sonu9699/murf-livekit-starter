import json
import os
import sqlite3

import pytest

import calls


@pytest.fixture
def db_path(tmp_path) -> str:
    """A temp SQLite DB file for testing."""
    return str(tmp_path / "test_calls.db")


@pytest.fixture
def isolated_db(tmp_path, monkeypatch) -> str:
    """Isolate the default database path to a temp file."""
    path = str(tmp_path / "default_test.db")
    monkeypatch.setenv("AAROGYA_DB_PATH", path)
    return path


def test_calls_init_db(db_path: str) -> None:
    # Initialize DB
    calls.init_db(db_path)

    # Check if table exists
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "calls"
    conn.close()


@pytest.mark.asyncio
async def test_save_call(db_path: str) -> None:
    calls.init_db(db_path)

    room_name = "test_room_123"
    calls.save_call(
        call_id=room_name,
        caller_name="Ramesh Kumar",
        status="success",
        reason="Triage performed",
        duration=45,
        db_path=db_path,
    )

    # Read from DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM calls WHERE id = ?", (room_name,)).fetchone()
    conn.close()

    assert row is not None
    assert row["caller_name"] == "Ramesh Kumar"
    assert row["status"] == "success"
    assert row["reason"] == "Triage performed"
    assert row["duration"] == 45
    assert row["created_at"]


@pytest.mark.asyncio
async def test_sync_to_json(db_path: str) -> None:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(backend_dir, "calls.json")

    # Remove existing JSON if any
    if os.path.exists(json_path):
        try:
            os.remove(json_path)
        except OSError:
            pass

    calls.init_db(db_path)

    room_name = "test_room_sync"
    calls.save_call(
        call_id=room_name,
        caller_name="Sita Devi",
        status="failed",
        reason="Caller was silent / did not engage",
        duration=12,
        db_path=db_path,
    )

    # Verify JSON was created
    assert os.path.exists(json_path)
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["id"] == room_name
    assert data[0]["caller_name"] == "Sita Devi"
    assert data[0]["status"] == "failed"
    assert data[0]["duration"] == 12
