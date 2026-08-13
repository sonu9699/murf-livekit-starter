import os
import json
import pytest
import sqlite3
import escalation
from agent import Assistant

@pytest.fixture
def db_path(tmp_path) -> str:
    """A temp SQLite DB file for testing."""
    return str(tmp_path / "test_escalations.db")

@pytest.fixture
def isolated_db(tmp_path, monkeypatch) -> str:
    """Isolate the default database path to a temp file."""
    path = str(tmp_path / "default_test.db")
    monkeypatch.setenv("AAROGYA_DB_PATH", path)
    return path

def test_escalation_init_db(db_path: str) -> None:
    # Initialize DB
    escalation.init_db(db_path)
    
    # Check if table exists
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='escalations'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "escalations"
    conn.close()

@pytest.mark.asyncio
async def test_save_escalation(db_path: str) -> None:
    escalation.init_db(db_path)
    
    ref_id = await escalation.save_escalation(
        caller_name="Ramesh",
        language="Hinglish",
        symptoms="severe chest pain",
        urgency="Emergency",
        followup_method="phone call",
        summary="Chest pain triage RED. Needs human help.",
        db_path=db_path
    )
    
    assert ref_id.startswith("ESC-")
    
    # Read from DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM escalations WHERE id = ?", (ref_id,)).fetchone()
    conn.close()
    
    assert row is not None
    assert row["caller_name"] == "Ramesh"
    assert row["urgency"] == "Emergency"
    assert row["status"] == "open"
    assert row["created_at"]

@pytest.mark.asyncio
async def test_sync_to_json_and_update_status(db_path: str, monkeypatch) -> None:
    # Set the path of escalations.json relative to the module
    # We mock _sync_to_json behavior or let it write to the test directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(backend_dir, "escalations.json")
    
    # Remove existing JSON if any
    if os.path.exists(json_path):
        try:
            os.remove(json_path)
        except OSError:
            pass
            
    escalation.init_db(db_path)
    
    ref_id = await escalation.save_escalation(
        caller_name="Sita Devi",
        language="Hindi",
        symptoms="high fever for 4 days",
        urgency="High",
        followup_method="visit",
        summary="High fever yellow triage.",
        db_path=db_path
    )
    
    # Verify JSON was created
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) == 1
    assert data[0]["id"] == ref_id
    assert data[0]["caller_name"] == "Sita Devi"
    assert data[0]["status"] == "open"
    
    # Test update status
    updated = escalation.update_status(ref_id, "resolved", db_path)
    assert updated is True
    
    # Verify status changed in JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data_updated = json.load(f)
    assert data_updated[0]["status"] == "resolved"

@pytest.mark.asyncio
async def test_agent_tool_create_escalation(isolated_db: str) -> None:
    escalation.init_db(isolated_db)
    agent = Assistant()
    
    # Call the tool directly
    res = await agent.create_escalation(
        context=None,
        caller_name="Mohan",
        language="Hinglish",
        symptoms="severe coughing with blood",
        urgency="Emergency",
        followup_method="phone call",
        summary="Coughing blood triage RED."
    )
    
    assert "Successfully created" in res
    assert "ESC-" in res
    
    # Check that it exists in the database
    requests = escalation.get_escalations(isolated_db)
    assert len(requests) == 1
    assert requests[0]["caller_name"] == "Mohan"
    assert requests[0]["urgency"] == "Emergency"
