"""Caller memory for Aarogya Saathi (Day 4).

A tiny SQLite-backed store so the voice agent can remember a caller between
calls and continue from last time instead of making them repeat themselves.

Design notes for the Health Access track:
- Callers are keyed by their SPOKEN NAME (normalized), NOT by the LiveKit
  participant identity. The frontend assigns a fresh random identity/room on
  every connect (``voice_assistant_user_<random>``), so that value is useless
  as a durable key. The name the caller says is the only stable handle we have.
- We deliberately store the MINIMUM: name, language preference, a rough age
  band, a few short condition labels, and a one-line triage outcome. We never
  store Aadhaar, bank, phone or any ID number, and never detailed medical
  notes — the task's hard rule for Health Access, and our existing guardrail.
- The DB file lives outside git (see .gitignore) because it holds personal
  data. Being a plain file, it survives an agent restart — a Day 4 criterion.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

# One row per caller. IF NOT EXISTS keeps this safe to run on every connect.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS callers (
    caller_id   TEXT PRIMARY KEY,   -- normalized name (lowercase, single-spaced)
    name        TEXT NOT NULL,      -- display name, as the caller said it
    language    TEXT NOT NULL DEFAULT '',  -- e.g. "Hindi", "Hinglish"
    age_band    TEXT NOT NULL DEFAULT '',  -- rough band only, e.g. "30s", "senior"
    conditions  TEXT NOT NULL DEFAULT '[]', -- JSON array of short labels e.g. ["BP","sugar"]
    last_triage TEXT NOT NULL DEFAULT '',  -- one short line on what was advised
    updated_at  TEXT NOT NULL       -- ISO-8601 UTC timestamp of last write
)
"""

_ENV_DB_PATH = "AAROGYA_DB_PATH"
_WHITESPACE = re.compile(r"\s+")


def default_db_path() -> str:
    """Resolve the DB file path: ``$AAROGYA_DB_PATH`` or ``backend/aarogya_memory.db``."""
    env = os.environ.get(_ENV_DB_PATH)
    if env:
        return os.path.abspath(env)
    # src/memory.py -> backend/aarogya_memory.db
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(backend_dir, "aarogya_memory.db")


def normalize_name(name: str) -> str:
    """Turn a spoken name into a stable lookup key.

    Lowercase, trim, and collapse internal whitespace so "  Sita  Devi " and
    "sita devi" resolve to the same caller. Returns "" for an empty/blank name.
    """
    if not name:
        return ""
    return _WHITESPACE.sub(" ", name.strip()).lower()


@dataclass(frozen=True)
class CallerProfile:
    """An immutable snapshot of what we remember about one caller."""

    caller_id: str
    name: str
    language: str = ""
    age_band: str = ""
    conditions: tuple[str, ...] = field(default_factory=tuple)
    last_triage: str = ""
    updated_at: str = ""

    def merged(self, **changes: object) -> CallerProfile:
        """Return a copy with the given fields replaced (immutable update)."""
        return replace(self, **changes)

    def as_recall_summary(self) -> str:
        """A compact, model-facing description used to brief the LLM on recall.

        This is instructions for the agent (English), not something to read out
        loud — the agent rephrases it warmly in Hinglish.
        """
        parts = [f"name={self.name}"]
        if self.language:
            parts.append(f"language={self.language}")
        if self.age_band:
            parts.append(f"age_band={self.age_band}")
        if self.conditions:
            parts.append("conditions=" + ", ".join(self.conditions))
        if self.last_triage:
            parts.append(f"last_triage={self.last_triage}")
        return (
            "Returning caller — you have spoken before. "
            + "; ".join(parts)
            + ". Greet them back BY NAME, briefly refer to last time, then ask how they are now."
        )


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection and guarantee the schema exists (idempotent)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def init_db(db_path: str | None = None) -> str:
    """Create the DB file and table if missing. Returns the resolved path."""
    path = db_path or default_db_path()
    with _connect(path) as conn:
        conn.commit()
    return path


def _row_to_profile(row: sqlite3.Row) -> CallerProfile:
    try:
        conditions = tuple(json.loads(row["conditions"]) or ())
    except (json.JSONDecodeError, TypeError):
        conditions = ()
    return CallerProfile(
        caller_id=row["caller_id"],
        name=row["name"],
        language=row["language"],
        age_band=row["age_band"],
        conditions=conditions,
        last_triage=row["last_triage"],
        updated_at=row["updated_at"],
    )


def get_caller(caller_id: str, db_path: str | None = None) -> CallerProfile | None:
    """Return the stored profile for ``caller_id``, or None if never seen.

    The id is normalized here too, so lookups are robust to casing/spacing even
    if a caller passes a raw name.
    """
    key = normalize_name(caller_id)
    if not key:
        return None
    path = db_path or default_db_path()
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT * FROM callers WHERE caller_id = ?", (key,)
        ).fetchone()
    return _row_to_profile(row) if row else None


def upsert_caller(profile: CallerProfile, db_path: str | None = None) -> CallerProfile:
    """Insert or update a caller, stamping ``updated_at`` at write time.

    Returns the stored profile (with the fresh timestamp) so callers don't have
    to re-read it.
    """
    key = normalize_name(profile.caller_id)
    if not key:
        raise ValueError("caller_id is required to save a caller profile")
    stamped = profile.merged(
        caller_id=key,
        updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    path = db_path or default_db_path()
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO callers
                (caller_id, name, language, age_band, conditions, last_triage, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(caller_id) DO UPDATE SET
                name        = excluded.name,
                language    = excluded.language,
                age_band    = excluded.age_band,
                conditions  = excluded.conditions,
                last_triage = excluded.last_triage,
                updated_at  = excluded.updated_at
            """,
            (
                stamped.caller_id,
                stamped.name,
                stamped.language,
                stamped.age_band,
                json.dumps(list(stamped.conditions), ensure_ascii=False),
                stamped.last_triage,
                stamped.updated_at,
            ),
        )
        conn.commit()
    return stamped


def forget_caller(caller_id: str, db_path: str | None = None) -> bool:
    """Delete a caller's record (a 'forget me' request). True if a row was removed."""
    key = normalize_name(caller_id)
    if not key:
        return False
    path = db_path or default_db_path()
    with _connect(path) as conn:
        cur = conn.execute("DELETE FROM callers WHERE caller_id = ?", (key,))
        conn.commit()
        return cur.rowcount > 0
