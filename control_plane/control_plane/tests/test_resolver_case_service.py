"""Tests for resolver case persistence helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.resolver_cases import ResolverCase
from control_plane.services.resolver_case_service import upsert_case_from_detection
from control_plane.services.resolver_detection import ResolverDetection


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _detection(*, item_id: str, latest_event_type: str, latest_event_time: str = "2026-04-09T23:58:00+00:00") -> ResolverDetection:
    evidence = {
        "item_id": item_id,
        "run_key": f"{item_id}-run",
        "machine_key": "eval-1",
        "lease_token": f"{item_id}-lease",
        "lease_expires_at": "2026-04-10T00:00:00+00:00",
        "last_heartbeat_at": "2026-04-09T23:59:00+00:00",
        "latest_event_type": latest_event_type,
        "latest_event_time": latest_event_time,
        "work_item_state": "running",
        "repo_root": "/repo",
        "source_commit": "deadbeef",
    }
    return ResolverDetection(
        fingerprint=f"orphaned_running_item:{latest_event_type}",
        failure_class="orphaned_running_item",
        owner="eval",
        severity="high",
        summary=f"{item_id} stale",
        item_id=item_id,
        run_key=f"{item_id}-run",
        machine_key="eval-1",
        source_commit="deadbeef",
        repo_root="/repo",
        evidence=evidence,
    )


def test_upsert_case_from_detection_creates_case() -> None:
    with make_session() as session:
        result = upsert_case_from_detection(session, _detection(item_id="item-1", latest_event_type="command_progress"))

        assert result.created is True
        assert result.evidence_changed is True
        case = session.query(ResolverCase).one()
        assert case.first_item_id == "item-1"
        assert case.latest_item_id == "item-1"
        assert case.fingerprint == "orphaned_running_item:command_progress"


def test_upsert_case_from_detection_updates_existing_case_for_same_item() -> None:
    with make_session() as session:
        first = upsert_case_from_detection(session, _detection(item_id="item-1", latest_event_type="command_progress"))
        second = upsert_case_from_detection(session, _detection(item_id="item-1", latest_event_type="command_progress", latest_event_time="2026-04-10T00:01:00+00:00"))

        assert first.case.id == second.case.id
        assert second.created is False
        assert second.evidence_changed is True
        case = session.query(ResolverCase).one()
        assert case.first_item_id == "item-1"
        assert case.latest_item_id == "item-1"
        assert case.fingerprint == "orphaned_running_item:command_progress"
        assert case.evidence_json["latest_event_type"] == "command_progress"
        assert case.evidence_json["latest_event_time"] == "2026-04-10T00:01:00+00:00"


def test_upsert_case_from_detection_creates_new_case_for_different_item_same_fingerprint() -> None:
    with make_session() as session:
        first = upsert_case_from_detection(session, _detection(item_id="item-1", latest_event_type="command_progress"))
        second = upsert_case_from_detection(session, _detection(item_id="item-2", latest_event_type="command_progress"))

        assert first.case.id != second.case.id
        assert second.created is True
        cases = session.query(ResolverCase).order_by(ResolverCase.created_at.asc()).all()
        assert len(cases) == 2
        assert cases[0].first_item_id == "item-1"
        assert cases[1].first_item_id == "item-2"
