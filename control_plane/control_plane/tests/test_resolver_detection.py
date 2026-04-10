"""Tests for resolver detection rules."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, LeaseStatus, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.resolver_detection import detect_orphaned_running_items


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def test_detect_orphaned_running_item() -> None:
    now = utcnow()
    with make_session() as session:
        task = TaskRequest(
            request_key="queue:test-orphan",
            source="test",
            requested_by="tester",
            title="test orphan",
            description="detect stuck run",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            priority=1,
            request_payload={"item_id": "orphan-item"},
        )
        session.add(task)
        session.flush()
        work_item = WorkItem(
            work_item_key="queue:test-orphan",
            task_request_id=task.id,
            item_id="orphan-item",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            platform="nangate45",
            task_type="l1_sweep",
            state=WorkItemState.RUNNING,
            priority=1,
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
            source_commit="deadbeef",
        )
        session.add(work_item)
        machine = WorkerMachine(
            machine_key="eval-1",
            hostname="eval-host",
            executor_kind="local_process",
            capabilities={},
            last_seen_at=now - timedelta(hours=1),
        )
        session.add(machine)
        session.flush()
        lease = WorkerLease(
            work_item_id=work_item.id,
            machine_id=machine.id,
            lease_token="lease-1",
            status=LeaseStatus.ACTIVE,
            leased_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=30),
            last_heartbeat_at=now - timedelta(minutes=35),
        )
        session.add(lease)
        session.flush()
        run = Run(
            run_key="run-1",
            work_item_id=work_item.id,
            lease_id=lease.id,
            attempt=1,
            executor_type=ExecutorType.INTERNAL_WORKER,
            machine_id=machine.id,
            status=RunStatus.RUNNING,
            started_at=now - timedelta(hours=1),
            result_payload={},
        )
        session.add(run)
        session.flush()
        session.add(
            RunEvent(
                run_id=run.id,
                event_time=now - timedelta(minutes=31),
                event_type="command_progress",
                event_payload={"command": "run_sweep"},
            )
        )
        session.commit()

        detections = detect_orphaned_running_items(session, repo_root="/repo")

    assert len(detections) == 1
    detection = detections[0]
    assert detection.fingerprint == "orphaned_running_item:command_progress"
    assert detection.owner == "eval"
    assert detection.item_id == "orphan-item"
    assert detection.run_key == "run-1"
    assert detection.machine_key == "eval-1"
    assert detection.evidence["lease_token"] == "lease-1"
    assert detection.evidence["repo_root"] == "/repo"


def test_skip_orphan_detector_for_terminal_latest_event() -> None:
    now = utcnow()
    with make_session() as session:
        task = TaskRequest(
            request_key="queue:test-terminal",
            source="test",
            requested_by="tester",
            title="test terminal",
            description="terminal event should not trigger",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            priority=1,
            request_payload={"item_id": "done-item"},
        )
        session.add(task)
        session.flush()
        work_item = WorkItem(
            work_item_key="queue:test-terminal",
            task_request_id=task.id,
            item_id="done-item",
            layer=LayerName.LAYER1,
            flow=FlowName.OPENROAD,
            platform="nangate45",
            task_type="l1_sweep",
            state=WorkItemState.RUNNING,
            priority=1,
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
        )
        session.add(work_item)
        machine = WorkerMachine(
            machine_key="eval-1",
            hostname="eval-host",
            executor_kind="local_process",
            capabilities={},
        )
        session.add(machine)
        session.flush()
        lease = WorkerLease(
            work_item_id=work_item.id,
            machine_id=machine.id,
            lease_token="lease-2",
            status=LeaseStatus.ACTIVE,
            leased_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=30),
            last_heartbeat_at=now - timedelta(minutes=35),
        )
        session.add(lease)
        session.flush()
        run = Run(
            run_key="run-2",
            work_item_id=work_item.id,
            lease_id=lease.id,
            attempt=1,
            executor_type=ExecutorType.INTERNAL_WORKER,
            machine_id=machine.id,
            status=RunStatus.RUNNING,
            started_at=now - timedelta(hours=1),
            result_payload={},
        )
        session.add(run)
        session.flush()
        session.add(
            RunEvent(
                run_id=run.id,
                event_time=now - timedelta(minutes=29),
                event_type="run_completed",
                event_payload={"status": "succeeded"},
            )
        )
        session.commit()

        detections = detect_orphaned_running_items(session, repo_root="/repo")

    assert detections == []
