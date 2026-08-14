import json
import logging
import os
import random
import sqlite3
from datetime import datetime, timezone

import aiohttp

import memory

logger = logging.getLogger("escalation")

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


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(ESCALATION_SCHEMA)
    return conn


def init_db(db_path: str | None = None) -> str:
    path = db_path or memory.default_db_path()
    with _connect(path) as conn:
        conn.commit()
    logger.info("Escalations database initialized at %s", path)
    return path


def _sync_to_json(db_path: str) -> None:
    """Read all escalations from DB and write them to backend/escalations.json."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(backend_dir, "escalations.json")

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM escalations ORDER BY created_at DESC"
            ).fetchall()

        escalations_list = []
        for row in rows:
            escalations_list.append(
                {
                    "id": row["id"],
                    "caller_name": row["caller_name"],
                    "language": row["language"],
                    "symptoms": row["symptoms"],
                    "urgency": row["urgency"],
                    "followup_method": row["followup_method"],
                    "summary": row["summary"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(escalations_list, f, ensure_ascii=False, indent=2)

        logger.info("Synced %d escalations to %s", len(escalations_list), json_path)
    except Exception as e:
        logger.error("Failed to sync escalations to JSON: %s", e)


async def send_discord_webhook(
    webhook_url: str,
    ref_id: str,
    caller_name: str,
    language: str,
    symptoms: str,
    urgency: str,
    followup_method: str,
    summary: str,
    created_at: str,
) -> None:
    urgency_lower = urgency.lower()
    if "emergency" in urgency_lower or "high" in urgency_lower:
        color = 15548997  # Red
    elif "medium" in urgency_lower:
        color = 16705372  # Orange/Yellow
    else:
        color = 5763719  # Green

    payload = {
        "content": "🚨 **New Aarogya Saathi Human Help Escalation** 🚨",
        "embeds": [
            {
                "title": f"Escalation Details - {ref_id}",
                "color": color,
                "fields": [
                    {"name": "Caller Name", "value": caller_name, "inline": True},
                    {"name": "Language", "value": language, "inline": True},
                    {"name": "Urgency Level", "value": urgency, "inline": True},
                    {"name": "Symptoms", "value": symptoms, "inline": False},
                    {"name": "Agent Summary", "value": summary, "inline": False},
                    {
                        "name": "Preferred Follow-up",
                        "value": followup_method,
                        "inline": True,
                    },
                ],
                "timestamp": created_at,
            }
        ],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in (200, 204):
                    logger.error("Discord Webhook returned status %s", response.status)
                else:
                    logger.info("Successfully sent Discord Webhook for %s", ref_id)
    except Exception as e:
        logger.error("Failed to send Discord Webhook: %s", e)


async def save_escalation(
    caller_name: str,
    language: str,
    symptoms: str,
    urgency: str,
    followup_method: str,
    summary: str,
    db_path: str | None = None,
) -> str:
    path = db_path or memory.default_db_path()
    ref_id = f"ESC-{random.randint(1000, 9999)}"
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO escalations (id, caller_name, language, symptoms, urgency, followup_method, summary, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                ref_id,
                caller_name,
                language,
                symptoms,
                urgency,
                followup_method,
                summary,
                created_at,
            ),
        )
        conn.commit()

    logger.info("Saved escalation %s to DB", ref_id)
    _sync_to_json(path)

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if webhook_url:
        await send_discord_webhook(
            webhook_url,
            ref_id,
            caller_name,
            language,
            symptoms,
            urgency,
            followup_method,
            summary,
            created_at,
        )

    return ref_id


def update_status(ref_id: str, status: str, db_path: str | None = None) -> bool:
    path = db_path or memory.default_db_path()
    with _connect(path) as conn:
        cur = conn.execute(
            "UPDATE escalations SET status = ? WHERE id = ?", (status, ref_id)
        )
        conn.commit()
        updated = cur.rowcount > 0
    if updated:
        _sync_to_json(path)
    return updated


def get_escalations(db_path: str | None = None) -> list[dict]:
    path = db_path or memory.default_db_path()
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT * FROM escalations ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]
