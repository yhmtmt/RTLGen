"""Dispatcher assignment coverage."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.dispatcher_service import AutoDispatchItemResult, DispatchReadyRequest, auto_dispatch_item, dispatch_ready_items
from control_plane.services.lease_service import upsert_worker_machine


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _seed_ready_item(session: Session, *, item_id: str, platform: str, priority: int = 1) -> None:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=item_id,
        description=item_id,
        layer="layer2",
        flow="openroad",
        priority=priority,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()
    session.add(
        WorkItem(
            work_item_key=f"queue:{item_id}",
            task_request_id=task.id,
            item_id=item_id,
            layer="layer2",
            flow="openroad",
            platform=platform,
            task_type="l2_campaign",
            state=WorkItemState.DISPATCH_PENDING,
            priority=priority,
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
        )
    )
    session.commit()


def test_dispatch_ready_items_assigns_matching_unassigned_work() -> None:
    with make_session() as session:
        upsert_worker_machine(
            session,
            machine_key="eval-a",
            hostname="eval-a",
            role="evaluator",
            slot_capacity=2,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        _seed_ready_item(session, item_id="item_a", platform="nangate45", priority=5)
        _seed_ready_item(session, item_id="item_b", platform="nangate45", priority=1)

        results = dispatch_ready_items(session, DispatchReadyRequest())

        assert [row.item_id for row in results] == ["item_a", "item_b"]
        items = session.query(WorkItem).order_by(WorkItem.item_id.asc()).all()
        assert all(item.assigned_machine_key == "eval-a" for item in items)
        assert all(item.state == WorkItemState.READY for item in items)


def test_dispatch_ready_items_respects_slot_capacity_and_existing_assignment() -> None:
    with make_session() as session:
        upsert_worker_machine(
            session,
            machine_key="eval-a",
            hostname="eval-a",
            role="evaluator",
            slot_capacity=1,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        upsert_worker_machine(
            session,
            machine_key="eval-b",
            hostname="eval-b",
            role="evaluator",
            slot_capacity=1,
            capabilities={"platform": "sky130hd", "flow": "openroad"},
        )
        _seed_ready_item(session, item_id="item_a", platform="nangate45", priority=5)
        _seed_ready_item(session, item_id="item_b", platform="nangate45", priority=4)
        _seed_ready_item(session, item_id="item_c", platform="sky130hd", priority=3)

        results = dispatch_ready_items(session, DispatchReadyRequest())

        assert {(row.item_id, row.machine_key) for row in results} == {
            ("item_a", "eval-a"),
            ("item_c", "eval-b"),
        }
        item_b = session.query(WorkItem).filter_by(item_id="item_b").one()
        assert item_b.assigned_machine_key is None
        assert item_b.state == WorkItemState.DISPATCH_PENDING


def test_auto_dispatch_item_assigns_single_matching_machine() -> None:
    with make_session() as session:
        upsert_worker_machine(
            session,
            machine_key="eval-a",
            hostname="eval-a",
            role="evaluator",
            slot_capacity=1,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        _seed_ready_item(session, item_id="item_a", platform="nangate45", priority=5)

        result = auto_dispatch_item(session, item_id="item_a")

        assert result == AutoDispatchItemResult(
            item_id="item_a",
            status="assigned",
            machine_key="eval-a",
            reason="ready",
        )
        item = session.query(WorkItem).filter_by(item_id="item_a").one()
        assert item.assigned_machine_key == "eval-a"
        assert item.state == WorkItemState.READY


def test_auto_dispatch_item_skips_when_multiple_eligible_machines() -> None:
    with make_session() as session:
        upsert_worker_machine(
            session,
            machine_key="eval-a",
            hostname="eval-a",
            role="evaluator",
            slot_capacity=1,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        upsert_worker_machine(
            session,
            machine_key="eval-b",
            hostname="eval-b",
            role="evaluator",
            slot_capacity=1,
            capabilities={"platform": "nangate45", "flow": "openroad"},
        )
        _seed_ready_item(session, item_id="item_a", platform="nangate45", priority=5)

        result = auto_dispatch_item(session, item_id="item_a")

        assert result == AutoDispatchItemResult(
            item_id="item_a",
            status="skipped",
            machine_key=None,
            reason="multiple_eligible_machines",
        )
        item = session.query(WorkItem).filter_by(item_id="item_a").one()
        assert item.assigned_machine_key is None
        assert item.state == WorkItemState.DISPATCH_PENDING
