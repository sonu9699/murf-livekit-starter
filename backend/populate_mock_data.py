import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

# Resolve paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, "aarogya_memory.db")
calls_json_path = os.path.join(backend_dir, "calls.json")
escalations_json_path = os.path.join(backend_dir, "escalations.json")

# Schemas
CALLER_SCHEMA = """
CREATE TABLE IF NOT EXISTS callers (
    caller_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    language    TEXT NOT NULL DEFAULT '',
    age_band    TEXT NOT NULL DEFAULT '',
    conditions  TEXT NOT NULL DEFAULT '[]',
    last_triage TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL
)
"""

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

ESCALATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS escalations (
    id              TEXT PRIMARY KEY,
    caller_name     TEXT NOT NULL,
    language        TEXT NOT NULL,
    symptoms        TEXT NOT NULL,
    urgency         TEXT NOT NULL,
    followup_method TEXT NOT NULL,
    summary         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open',
    created_at      TEXT NOT NULL
)
"""


def populate():
    # Connect and create tables
    conn = sqlite3.connect(db_path)
    conn.execute(CALLER_SCHEMA)
    conn.execute(CALL_SCHEMA)
    conn.execute(ESCALATION_SCHEMA)

    # Clear existing to prevent duplicates
    conn.execute("DELETE FROM callers")
    conn.execute("DELETE FROM calls")
    conn.execute("DELETE FROM escalations")

    now = datetime.now(timezone.utc)

    # --- 1. Populate Callers (Patient Memory Directory) ---
    callers_data = [
        (
            "sunita sharma",
            "Sunita Sharma",
            "Hinglish",
            "40s",
            json.dumps(["BP"]),
            "Advised rest, warm fluids, and paracetamol for mild seasonal fever. BP parameters stable.",
            (now - timedelta(hours=2)).isoformat(),
        ),
        (
            "ramesh patel",
            "Ramesh Patel",
            "Hindi",
            "60s",
            json.dumps(["Diabetes"]),
            "EMERGENCY: Advised immediate transfer to hospital due to chest tightness and sweating.",
            (now - timedelta(hours=4)).isoformat(),
        ),
        (
            "karan singh",
            "Karan Singh",
            "Hinglish",
            "3 months",
            json.dumps([]),
            "Confirmed Pentavalent-2 shot schedule for next Tuesday. Reminder set.",
            (now - timedelta(hours=6)).isoformat(),
        ),
        (
            "meera devi",
            "Meera Devi",
            "Hinglish",
            "50s",
            json.dumps(["High BP"]),
            "BP stable at 135/85. Reminded to take Amlodipine daily and reduce salt.",
            (now - timedelta(hours=10)).isoformat(),
        ),
        (
            "rahul verma",
            "Rahul Verma",
            "English",
            "20s",
            json.dumps(["Asthma"]),
            "Advised dry inhaler usage checks. Referred to local clinic for follow-up.",
            (now - timedelta(hours=12)).isoformat(),
        ),
    ]

    conn.executemany(
        """
        INSERT INTO callers (caller_id, name, language, age_band, conditions, last_triage, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        callers_data,
    )

    # --- 2. Populate Calls (Call Analytics logs) ---
    calls_data = [
        (
            "call_session_101",
            "Sunita Sharma",
            "success",
            "Completed: Mild fever consultation and home care PCM advice provided.",
            95,
            (now - timedelta(hours=2)).isoformat(),
        ),
        (
            "call_session_102",
            "Ramesh Patel",
            "success",
            "Emergency: Chest pain triage. Automated doctor referral generated.",
            145,
            (now - timedelta(hours=4)).isoformat(),
        ),
        (
            "call_session_103",
            None,
            "failed",
            "Caller was silent / did not engage on connection.",
            7,
            (now - timedelta(hours=5)).isoformat(),
        ),
        (
            "call_session_104",
            "Karan Singh",
            "success",
            "Completed: Outbound vaccination reminder campaign check-in.",
            65,
            (now - timedelta(hours=6)).isoformat(),
        ),
        (
            "call_session_105",
            "Meera Devi",
            "success",
            "Completed: High BP check-in. Medication compliance confirmed.",
            110,
            (now - timedelta(hours=10)).isoformat(),
        ),
        (
            "call_session_106",
            "Rahul Verma",
            "success",
            "Completed: Mild wheezing query. Inhaler dosage guide given.",
            80,
            (now - timedelta(hours=12)).isoformat(),
        ),
        (
            "call_session_107",
            None,
            "failed",
            "Call dropped early by user before welcome greeting.",
            12,
            (now - timedelta(hours=15)).isoformat(),
        ),
    ]

    conn.executemany(
        """
        INSERT INTO calls (id, caller_name, status, reason, duration, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        calls_data,
    )

    # --- 3. Populate Escalations ---
    escalations_data = [
        (
            "ESC_001",
            "Ramesh Patel",
            "Hindi",
            "Chest pain radiating to left arm, sweating, shortness of breath",
            "Emergency",
            "Phone Call",
            "Suspected cardiovascular event. Patient directed to emergency room immediately.",
            "open",
            (now - timedelta(hours=4)).isoformat(),
        ),
        (
            "ESC_002",
            "Rahul Verma",
            "English",
            "Mild wheezing and chest congestion, asthma history",
            "High",
            "WhatsApp / SMS",
            "Asthma exacerbation under control, referred to physician for prescription renewal.",
            "resolved",
            (now - timedelta(hours=12)).isoformat(),
        ),
    ]

    conn.executemany(
        """
        INSERT INTO escalations (id, caller_name, language, symptoms, urgency, followup_method, summary, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        escalations_data,
    )

    conn.commit()
    conn.close()
    print("Database populated successfully.")

    # --- 4. Sync to calls.json ---
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM calls ORDER BY created_at DESC").fetchall()
    calls_list = [dict(r) for r in rows]
    with open(calls_json_path, "w", encoding="utf-8") as f:
        json.dump(calls_list, f, ensure_ascii=False, indent=2)
    print(f"Synced {len(calls_list)} calls to calls.json.")

    # --- 5. Sync to escalations.json ---
    rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
    escalations_list = [dict(r) for r in rows]
    with open(escalations_json_path, "w", encoding="utf-8") as f:
        json.dump(escalations_list, f, ensure_ascii=False, indent=2)
    print(f"Synced {len(escalations_list)} escalations to escalations.json.")
    conn.close()


if __name__ == "__main__":
    populate()
