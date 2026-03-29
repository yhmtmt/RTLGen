"""Polling worker-daemon coverage."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_service import CompletionProcessResult, CompletionProcessingError
from control_plane.services.lease_service import upsert_worker_machine
from control_plane.services.worker_daemon import WorkerDaemonConfig, run_worker_daemon
from control_plane.workers.executor import WorkerConfig


def _seed_ready_work_item(session: Session, *, item_id: str, repo_root: Path) -> None:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=f"{item_id} title",
        description="worker daemon test",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()

    report_dir = repo_root / "runs" / "campaigns" / item_id
    metrics_path = report_dir / "metrics.csv"
    report_path = report_dir / "report.md"
    work_item = WorkItem(
        work_item_key=f"queue:{item_id}",
        task_request_id=task.id,
        item_id=item_id,
        layer="layer2",
        flow="openroad",
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.READY,
        priority=1,
        input_manifest={},
        command_manifest=[
            {
                "name": "write_metrics",
                "run": (
                    "python3 -c \"from pathlib import Path; "
                    f"p=Path('{metrics_path.relative_to(repo_root)}'); "
                    "p.parent.mkdir(parents=True, exist_ok=True); "
                    "p.write_text('metric,value\\nlatency,1\\n', encoding='utf-8')\""
                ),
            },
            {
                "name": "write_report",
                "run": (
                    "python3 -c \"from pathlib import Path; "
                    f"p=Path('{report_path.relative_to(repo_root)}'); "
                    "p.write_text('# report\\n', encoding='utf-8')\""
                ),
            },
        ],
        expected_outputs=[
            str(metrics_path.relative_to(repo_root)),
            str(report_path.relative_to(repo_root)),
        ],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.commit()


def test_worker_daemon_executes_item_then_stops_on_no_work() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_success", repo_root=repo_root)

        session_factory = build_session_factory(engine)
        result = run_worker_daemon(
            session_factory,
            config=WorkerDaemonConfig(
                worker=WorkerConfig(
                    repo_root=str(repo_root),
                    machine_key="daemon-worker-1",
                    capabilities={"platform": "nangate45", "flow": "openroad"},
                    capability_filter={"platform": "nangate45", "flow": "openroad"},
                    heartbeat_seconds=1,
                ),
                poll_seconds=0,
                max_polls=2,
                stop_on_no_work=True,
            ),
        )

        assert result.executed_items == 1
        assert result.no_work_polls == 1
        assert result.poll_count == 2
        assert [row.status for row in result.results] == ["succeeded", "no_work"]


def test_worker_daemon_emits_positive_poll_logs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_log", repo_root=repo_root)

        messages: list[str] = []
        session_factory = build_session_factory(engine)
        result = run_worker_daemon(
            session_factory,
            config=WorkerDaemonConfig(
                worker=WorkerConfig(
                    repo_root=str(repo_root),
                    machine_key="daemon-worker-log",
                    hostname="daemon-host",
                    capabilities={"platform": "nangate45", "flow": "openroad"},
                    capability_filter={"platform": "nangate45", "flow": "openroad"},
                    heartbeat_seconds=1,
                ),
                poll_seconds=0,
                max_polls=2,
                stop_on_no_work=True,
            ),
            log_fn=messages.append,
        )

        assert result.executed_items == 1
        assert any("worker-daemon start" in entry for entry in messages)
        assert any("poll=1" in entry and "succeeded" in entry for entry in messages)
        assert any("poll=2" in entry and "no_work" in entry for entry in messages)
        assert any("worker-daemon exit" in entry for entry in messages)


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "tester@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Tester"], check=True)
    (repo_root / "README.md").write_text("worker daemon test\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "README.md"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "init"], check=True, capture_output=True, text=True)


def test_worker_daemon_executes_two_items_with_concurrency() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(
            f"sqlite+pysqlite:///{db_path}",
            future=True,
            connect_args={"check_same_thread": False},
        )
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_parallel_a", repo_root=repo_root)
            _seed_ready_work_item(session, item_id="daemon_item_parallel_b", repo_root=repo_root)
            upsert_worker_machine(
                session,
                machine_key="daemon-worker-parallel",
                hostname="daemon-worker-parallel",
                executor_kind="local_process",
                capabilities={"platform": "nangate45", "flow": "openroad"},
            )
            session.commit()

        session_factory = build_session_factory(engine)
        result = run_worker_daemon(
            session_factory,
            config=WorkerDaemonConfig(
                worker=WorkerConfig(
                    repo_root=str(repo_root),
                    machine_key="daemon-worker-parallel",
                    capabilities={"platform": "nangate45", "flow": "openroad"},
                    capability_filter={"platform": "nangate45", "flow": "openroad"},
                    heartbeat_seconds=1,
                ),
                poll_seconds=0,
                max_polls=1,
                max_items_per_poll=2,
                concurrency=2,
            ),
        )

        assert result.executed_items == 2
        assert sorted(row.item_id for row in result.results if row.item_id) == [
            "daemon_item_parallel_a",
            "daemon_item_parallel_b",
        ]


def test_worker_daemon_immediately_processes_completion_for_supported_items() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_immediate_completion", repo_root=repo_root)

        session_factory = build_session_factory(engine)
        with patch("control_plane.workers.executor.process_completed_items") as process_completed:
            process_completed.return_value = [
                CompletionProcessResult(
                    item_id="daemon_item_immediate_completion",
                    run_key="synthetic",
                    task_type="l2_campaign",
                    consumed=True,
                    submitted=True,
                    work_item_state="awaiting_review",
                    target_path="control_plane/shadow_exports/review/demo/evaluated.json",
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/999",
                    submission_error=None,
                )
            ]
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-immediate",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        heartbeat_seconds=1,
                        auto_process_completions=True,
                        completion_submit=True,
                        completion_repo="yhmtmt/RTLGen",
                    ),
                    poll_seconds=0,
                    max_polls=1,
                ),
            )

        assert result.executed_items == 1
        assert process_completed.call_count == 1
        request = process_completed.call_args.args[1]
        assert request.item_id == "daemon_item_immediate_completion"
        assert request.submit is True
        assert request.repo == "yhmtmt/RTLGen"
        with Session(engine) as session:
            event = (
                session.query(RunEvent)
                .filter(RunEvent.event_type == "completion_processed")
                .one()
            )
            assert event.event_payload["submitted"] is True
            assert event.event_payload["pr_url"] == "https://github.com/yhmtmt/RTLGen/pull/999"


def test_worker_daemon_records_immediate_completion_failure_without_poisoning_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_completion_failure", repo_root=repo_root)

        session_factory = build_session_factory(engine)
        with patch(
            "control_plane.workers.executor.process_completed_items",
            side_effect=CompletionProcessingError("boom"),
        ):
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-immediate-fail",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        heartbeat_seconds=1,
                        auto_process_completions=True,
                        completion_repo="yhmtmt/RTLGen",
                    ),
                    poll_seconds=0,
                    max_polls=1,
                ),
            )

        assert result.executed_items == 1
        with Session(engine) as session:
            work_item = (
                session.query(WorkItem)
                .filter(WorkItem.item_id == "daemon_item_completion_failure")
                .one()
            )
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            event = (
                session.query(RunEvent)
                .filter(RunEvent.event_type == "completion_processing_failed")
                .one()
            )
            assert event.event_payload["error"] == "boom"
