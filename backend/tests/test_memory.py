"""Tests for Day 4 caller memory: the SQLite store and the agent's memory tools.

The store is keyed by the caller's normalized spoken name (the LiveKit identity
is random per call, so it can't be a durable key). These tests cover the
persistence layer and the three function tools — especially the Health Access
HARD RULE that nothing is saved without the caller's explicit consent.
"""

import os

import pytest

import memory
from agent import Assistant, _parse_conditions

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path) -> str:
    """A throwaway DB file for a single test."""
    return str(tmp_path / "callers.db")


@pytest.fixture
def isolated_db(tmp_path, monkeypatch) -> str:
    """Point the DEFAULT db path at a temp file so the agent tools (which don't
    take an explicit path) write somewhere isolated."""
    path = str(tmp_path / "default.db")
    monkeypatch.setenv("AAROGYA_DB_PATH", path)
    return path


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_normalize_name_collapses_case_and_space() -> None:
    assert memory.normalize_name("  Sita   Devi ") == "sita devi"
    assert memory.normalize_name("SITA DEVI") == memory.normalize_name("sita devi")


def test_normalize_name_blank_is_empty() -> None:
    assert memory.normalize_name("") == ""
    assert memory.normalize_name("   ") == ""


def test_parse_conditions_splits_on_commas_and_hindi_joiners() -> None:
    assert _parse_conditions("BP, sugar और bukhar") == ("BP", "sugar", "bukhar")
    assert _parse_conditions("") == ()


# ---------------------------------------------------------------------------
# Repository roundtrip / persistence
# ---------------------------------------------------------------------------


def test_upsert_then_get_roundtrip(db_path: str) -> None:
    profile = memory.CallerProfile(
        caller_id="Sita Devi",
        name="Sita Devi",
        language="Hindi",
        age_band="50s",
        conditions=("BP", "sugar"),
        last_triage="rest; PHC if fever > 3 days",
    )
    memory.upsert_caller(profile, db_path)

    # lookup is robust to casing/spacing
    got = memory.get_caller("  SITA  devi ", db_path)
    assert got is not None
    assert got.caller_id == "sita devi"
    assert got.name == "Sita Devi"
    assert got.conditions == ("BP", "sugar")
    assert got.updated_at  # stamped at write time


def test_get_missing_returns_none(db_path: str) -> None:
    memory.init_db(db_path)
    assert memory.get_caller("nobody", db_path) is None


def test_upsert_updates_existing_row(db_path: str) -> None:
    memory.upsert_caller(
        memory.CallerProfile(caller_id="ram", name="Ram", conditions=("cough",)), db_path
    )
    memory.upsert_caller(
        memory.CallerProfile(
            caller_id="ram", name="Ram", conditions=("cough", "fever"), last_triage="rest"
        ),
        db_path,
    )
    got = memory.get_caller("ram", db_path)
    assert got is not None
    assert got.conditions == ("cough", "fever")
    assert got.last_triage == "rest"


def test_devanagari_conditions_survive_json_roundtrip(db_path: str) -> None:
    memory.upsert_caller(
        memory.CallerProfile(caller_id="geeta", name="Geeta", conditions=("बुखार", "खांसी")),
        db_path,
    )
    got = memory.get_caller("geeta", db_path)
    assert got is not None
    assert got.conditions == ("बुखार", "खांसी")


def test_data_survives_a_fresh_connection(db_path: str) -> None:
    """Each repo call opens a new connection, so a successful read after a write
    proves the row is on disk — i.e. it survives an agent restart."""
    memory.upsert_caller(memory.CallerProfile(caller_id="mohan", name="Mohan"), db_path)
    assert os.path.exists(db_path)
    # simulate "next call after restart": brand-new read path
    assert memory.get_caller("mohan", db_path) is not None


def test_forget_removes_row(db_path: str) -> None:
    memory.upsert_caller(memory.CallerProfile(caller_id="asha", name="Asha"), db_path)
    assert memory.forget_caller("ASHA", db_path) is True
    assert memory.get_caller("asha", db_path) is None
    # deleting again is a no-op
    assert memory.forget_caller("asha", db_path) is False


def test_upsert_requires_a_name(db_path: str) -> None:
    with pytest.raises(ValueError):
        memory.upsert_caller(memory.CallerProfile(caller_id="   ", name="x"), db_path)


# ---------------------------------------------------------------------------
# Agent memory tools (called directly; `context` is unused in the tool bodies)
# ---------------------------------------------------------------------------


async def test_recall_new_caller_reports_new(isolated_db: str) -> None:
    agent = Assistant()
    result = await agent.recall_caller(None, name="Kavita")
    assert "NEW caller" in result
    assert agent._caller_id == "kavita"
    assert agent._profile is None


async def test_remember_requires_consent(isolated_db: str) -> None:
    agent = Assistant()
    await agent.recall_caller(None, name="Kavita")
    result = await agent.remember_caller(None, consent_given=False, conditions="BP")
    assert "not" in result.lower()  # refused
    assert memory.get_caller("kavita", isolated_db) is None  # nothing written


async def test_remember_needs_a_name_first(isolated_db: str) -> None:
    agent = Assistant()  # no recall_caller yet
    result = await agent.remember_caller(None, consent_given=True, conditions="BP")
    assert "name" in result.lower()


async def test_full_two_call_flow(isolated_db: str) -> None:
    # --- Call 1: new caller consents, we remember them ---
    call1 = Assistant()
    assert "NEW caller" in await call1.recall_caller(None, name="Sunita")
    await call1.remember_caller(
        None,
        consent_given=True,
        language="Hindi",
        age_band="40s",
        conditions="BP, sugar",
        triage_outcome="rest, review sugar",
    )

    # --- Call 2: a fresh Assistant (fresh call) recognizes her ---
    call2 = Assistant()
    summary = await call2.recall_caller(None, name="  sunita ")
    assert "Returning caller" in summary
    assert "Sunita" in summary
    assert "BP" in summary
    assert call2._profile is not None
    assert call2._profile.age_band == "40s"


async def test_remember_merges_with_previous(isolated_db: str) -> None:
    first = Assistant()
    await first.recall_caller(None, name="Ramesh")
    await first.remember_caller(
        None, consent_given=True, age_band="60s", conditions="BP"
    )

    # next call adds a triage outcome but omits age_band -> must be preserved
    second = Assistant()
    await second.recall_caller(None, name="Ramesh")
    await second.remember_caller(
        None, consent_given=True, triage_outcome="advised PHC visit"
    )

    got = memory.get_caller("ramesh", isolated_db)
    assert got is not None
    assert got.age_band == "60s"  # preserved from first call
    assert got.conditions == ("BP",)  # preserved
    assert got.last_triage == "advised PHC visit"  # updated


async def test_forget_tool_deletes(isolated_db: str) -> None:
    agent = Assistant()
    await agent.recall_caller(None, name="Farida")
    await agent.remember_caller(None, consent_given=True, conditions="cough")
    assert memory.get_caller("farida", isolated_db) is not None

    result = await agent.forget_caller(None)
    assert "eleted" in result or "forgot" in result.lower()
    assert memory.get_caller("farida", isolated_db) is None
