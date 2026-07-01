"""Lease acquisition, heartbeat, and expiry coverage for cp-005."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.api.app import create_app
from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.lease_service import acquire_next_lease, expire_stale_leases, heartbeat_lease
from control_plane.services.scheduler import assign_work_item


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def seed_ready_items(session: Session) -> tuple[WorkItem, WorkItem]:
    task1 = TaskRequest(
        request_key="queue:item_a",
        source="test",
        requested_by="tester",
        title="item a",
        description="objective a",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": "item_a"},
    )
    task2 = TaskRequest(
        request_key="queue:item_b",
        source="test",
        requested_by="tester",
        title="item b",
        description="objective b",
        layer="layer2",
        flow="openroad",
        priority=5,
        request_payload={"item_id": "item_b"},
    )
    session.add_all([task1, task2])
    session.flush()
    item_a = WorkItem(
        work_item_key="queue:item_a",
        task_request_id=task1.id,
        item_id="item_a",
        layer="layer2",
        flow="openroad",
        platform="sky130hd",
        task_type="l2_campaign",
        state=WorkItemState.DISPATCH_PENDING,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    item_b = WorkItem(
        work_item_key="queue:item_b",
        task_request_id=task2.id,
        item_id="item_b",
        layer="layer2",
        flow="openroad",
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.DISPATCH_PENDING,
        priority=5,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add_all([item_a, item_b])
    session.commit()
    return item_a, item_b


def test_acquire_next_lease_selects_matching_highest_priority_item() -> None:
    with make_session() as session:
        item_a, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine
        upsert_worker_machine(session, machine_key="machine-1")
        assign_work_item(session, item_id=item_b.item_id, machine_key="machine-1")
        result = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=900,
        )
        session.refresh(item_b)
        assert result.item_id == item_b.item_id
        assert item_b.state == WorkItemState.LEASED
        lease = session.query(WorkerLease).filter_by(lease_token=result.lease_token).one()
        assert lease.status == LeaseStatus.ACTIVE


def test_acquire_next_lease_persists_capability_filter() -> None:
    with make_session() as session:
        _, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine

        upsert_worker_machine(session, machine_key="machine-1")
        assign_work_item(session, item_id=item_b.item_id, machine_key="machine-1")

        result = acquire_next_lease(
            session,
            machine_key="machine-1",
            capability_filter={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=900,
        )

        machine = session.query(WorkerMachine).filter_by(machine_key="machine-1").one()
        assert result.item_id == item_b.item_id
        assert machine.capabilities["platform"] == "nangate45"
        assert machine.capabilities["flow"] == "openroad"


def test_heartbeat_updates_expiry_and_machine_progress() -> None:
    with make_session() as session:
        _, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine
        upsert_worker_machine(session, machine_key="machine-1")
        assign_work_item(session, item_id=item_b.item_id, machine_key="machine-1")
        acquired = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=60,
        )
        first_expiry = acquired.expires_at
        result = heartbeat_lease(
            session,
            lease_token=acquired.lease_token,
            extend_seconds=600,
            progress={"phase": "run_campaign", "message": "still running"},
        )
        lease = session.query(WorkerLease).filter_by(lease_token=acquired.lease_token).one()
        assert result.status == "active"
        assert result.expires_at != first_expiry
        assert lease.machine.capabilities["last_progress"]["phase"] == "run_campaign"


def test_upsert_worker_machine_does_not_clear_progress_with_empty_capabilities() -> None:
    with make_session() as session:
        from control_plane.services.lease_service import upsert_worker_machine

        machine = upsert_worker_machine(
            session,
            machine_key="machine-1",
            capabilities={
                "platform": "nangate45",
                "flow": "openroad",
                "last_progress": {"phase": "worker_poll", "status": "no_work"},
            },
        )
        session.commit()

        upsert_worker_machine(session, machine_key=machine.machine_key, capabilities={})
        session.commit()
        session.refresh(machine)

        assert machine.capabilities["platform"] == "nangate45"
        assert machine.capabilities["flow"] == "openroad"
        assert machine.capabilities["last_progress"] == {"phase": "worker_poll", "status": "no_work"}


def test_expire_stale_leases_requeues_assigned_nonterminal_work_as_ready() -> None:
    with make_session() as session:
        _, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine
        upsert_worker_machine(session, machine_key="machine-1")
        assign_work_item(session, item_id=item_b.item_id, machine_key="machine-1")
        acquired = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=1,
        )
        lease = session.query(WorkerLease).filter_by(lease_token=acquired.lease_token).one()
        run = Run(
            run_key="item_b_run_1",
            work_item_id=item_b.id,
            lease_id=lease.id,
            attempt=1,
            executor_type="internal_worker",
            status=RunStatus.RUNNING,
            started_at=utcnow(),
        )
        session.add(run)
        lease.machine.capabilities = {
            **(lease.machine.capabilities or {}),
            "last_progress": {
                "phase": "command_running",
                "item_id": item_b.item_id,
                "command_name": "run_sweep",
            },
        }
        lease.expires_at = utcnow().replace(year=2020)
        item_b.state = WorkItemState.RUNNING
        session.commit()
        result = expire_stale_leases(session)
        session.refresh(item_b)
        session.refresh(lease)
        session.refresh(run)
        assert result.expired_count == 1
        assert result.requeued_count == 1
        assert result.cleaned_run_count == 1
        assert lease.status == LeaseStatus.EXPIRED
        assert item_b.state == WorkItemState.READY
        assert run.status == RunStatus.CANCELED
        assert "last_progress" not in lease.machine.capabilities
        assert run.completed_at is not None
        assert run.failure_category == "lease_expired"

        reacquired = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=1,
        )
        new_lease = session.query(WorkerLease).filter_by(lease_token=reacquired.lease_token).one()
        session.refresh(run)
        session.refresh(lease)

        assert new_lease.id != lease.id
        assert new_lease.status == LeaseStatus.ACTIVE
        assert lease.status == LeaseStatus.EXPIRED
        assert run.lease_id == lease.id


def test_lease_routes_work_in_process() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        old = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            with Session(engine) as session:
                from control_plane.services.lease_service import upsert_worker_machine
                item_a, item_b = seed_ready_items(session)
                upsert_worker_machine(session, machine_key="machine-1")
                assign_work_item(session, item_id=item_b.item_id, machine_key="machine-1")

            status, _, body = app.handle(
                "POST",
                "/api/v1/leases/acquire-next",
                json.dumps(
                    {
                        "machine_key": "machine-1",
                        "capabilities": {"platform": "nangate45", "flow": "openroad"},
                        "lease_seconds": 120,
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            acquire_response = json.loads(body.decode("utf-8"))
            assert acquire_response["item_id"] == "item_b"

            status, _, body = app.handle(
                "POST",
                f"/api/v1/leases/{acquire_response['lease_token']}/heartbeat",
                json.dumps(
                    {
                        "extend_seconds": 300,
                        "progress": {"phase": "validate"},
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            heartbeat_response = json.loads(body.decode("utf-8"))
            assert heartbeat_response["status"] == "active"
        finally:
            if old is None:
                del os.environ["RTLCP_DATABASE_URL"]
            else:
                os.environ["RTLCP_DATABASE_URL"] = old


def test_acquire_next_lease_prefers_item_assigned_to_machine() -> None:
    with make_session() as session:
        item_a, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine
        upsert_worker_machine(session, machine_key="machine-1")
        assign_work_item(session, item_id=item_a.item_id, machine_key="machine-1")
        result = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"flow": "openroad"},
            lease_seconds=900,
        )
        assert result.item_id == item_a.item_id


def test_acquire_next_lease_does_not_take_item_assigned_to_other_machine() -> None:
    with make_session() as session:
        item_a, item_b = seed_ready_items(session)
        from control_plane.services.lease_service import upsert_worker_machine
        upsert_worker_machine(session, machine_key="machine-1")
        upsert_worker_machine(session, machine_key="machine-2")
        assign_work_item(session, item_id=item_a.item_id, machine_key="machine-1")
        assign_work_item(session, item_id=item_b.item_id, machine_key="machine-2")
        result = acquire_next_lease(
            session,
            machine_key="machine-1",
            capabilities={"platform": "sky130hd", "flow": "openroad"},
            lease_seconds=900,
        )
        assert result.item_id == item_a.item_id


def test_acquire_next_lease_requires_assignment_for_machine() -> None:
    with make_session() as session:
        seed_ready_items(session)
        try:
            acquire_next_lease(
                session,
                machine_key="machine-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=900,
            )
        except Exception as exc:
            assert exc.__class__.__name__ == "NoEligibleWorkItem"
        else:
            raise AssertionError("expected NoEligibleWorkItem")
