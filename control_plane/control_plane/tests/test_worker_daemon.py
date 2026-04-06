"""Polling worker-daemon coverage."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.clock import utcnow
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_service import CompletionProcessResult, CompletionProcessingError
from control_plane.services.lease_service import upsert_worker_machine
from control_plane.services.scheduler import assign_work_item
from control_plane.services.worker_daemon import WorkerDaemonConfig, run_worker_daemon
from control_plane.workers.checkout import CheckoutInfo
from control_plane.workers.executor import WorkerConfig, _active_command_manifest, _active_expected_outputs


def _seed_ready_work_item(session: Session, *, item_id: str, repo_root: Path, assigned_machine_key: str | None = None) -> None:
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
        state=WorkItemState.READY if assigned_machine_key else WorkItemState.DISPATCH_PENDING,
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
    if assigned_machine_key:
        upsert_worker_machine(session, machine_key=assigned_machine_key, capabilities={"platform": "nangate45", "flow": "openroad"})
        assign_work_item(session, item_id=item_id, machine_key=assigned_machine_key)


def test_worker_daemon_executes_item_then_stops_on_no_work() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_success", repo_root=repo_root, assigned_machine_key="daemon-worker-1")

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


def test_active_command_manifest_injects_flow_random_seed_for_multi_trial_sweep() -> None:
    work_item = WorkItem(
        item_id="seeded_item",
        task_type="l1_sweep",
        input_manifest={"out_root": "runs/designs/activations/demo_wrapper"},
        command_manifest=[
            {
                "name": "run_sweep",
                "run": (
                    "export PATH=/oss-cad-suite/bin:$PATH && "
                    "python3 scripts/run_sweep.py --configs runs/designs/demo/config.json "
                    "--platform nangate45 --sweep runs/designs/demo/sweep.json "
                    "--out_root runs/designs/activations/demo_wrapper --skip_existing"
                ),
            }
        ],
        trial_policy_json={"trial_count": 3, "seed_start": 100, "stop_after_failures": 3},
    )

    commands = _active_command_manifest(work_item, 2)

    assert commands[0]["run"].startswith("export PATH=/oss-cad-suite/bin:$PATH && FLOW_RANDOM_SEED=101 python3")
    assert "--out_root runs/designs/activations/demo_wrapper/trials/trial_002" in commands[0]["run"]


def test_active_expected_outputs_keeps_trial_scoped_outputs_for_multi_trial_sweep() -> None:
    work_item = WorkItem(
        item_id="seeded_item",
        task_type="l1_sweep",
        input_manifest={"out_root": "runs/designs/activations/demo_wrapper"},
        expected_outputs=[
            "runs/designs/activations/demo_wrapper/trials/trial_001/demo_wrapper/metrics.csv",
            "runs/designs/activations/demo_wrapper/trials/trial_002/demo_wrapper/metrics.csv",
            "runs/designs/activations/demo_wrapper/trials/trial_003/demo_wrapper/metrics.csv",
        ],
        trial_policy_json={"trial_count": 3, "seed_start": 100, "stop_after_failures": 3},
    )

    assert _active_expected_outputs(work_item, 2) == [
        "runs/designs/activations/demo_wrapper/trials/trial_001/demo_wrapper/metrics.csv",
        "runs/designs/activations/demo_wrapper/trials/trial_002/demo_wrapper/metrics.csv",
        "runs/designs/activations/demo_wrapper/trials/trial_003/demo_wrapper/metrics.csv",
    ]


def test_worker_daemon_emits_positive_poll_logs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_log", repo_root=repo_root, assigned_machine_key="daemon-worker-log")

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
            _seed_ready_work_item(session, item_id="daemon_item_parallel_a", repo_root=repo_root, assigned_machine_key="daemon-worker-parallel")
            _seed_ready_work_item(session, item_id="daemon_item_parallel_b", repo_root=repo_root, assigned_machine_key="daemon-worker-parallel")
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


def test_worker_daemon_syncs_expected_outputs_before_immediate_completion() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_sync_before_completion", repo_root=repo_root, assigned_machine_key="daemon-worker-sync-before-completion")

        session_factory = build_session_factory(engine)

        def _assert_synced(session, request):
            metrics_path = repo_root / "runs" / "campaigns" / "daemon_item_sync_before_completion" / "metrics.csv"
            report_path = repo_root / "runs" / "campaigns" / "daemon_item_sync_before_completion" / "report.md"
            assert metrics_path.exists(), metrics_path
            assert report_path.exists(), report_path
            assert Path(request.repo_root).resolve() != repo_root.resolve()

            review_path = Path(request.repo_root) / "control_plane" / "shadow_exports" / "review" / "daemon_item_sync_before_completion" / "evaluated.json"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text('{\"ok\": true}\n', encoding='utf-8')

            frozen_path = Path(request.repo_root) / "control_plane" / "shadow_exports" / "frozen_review" / "daemon_item_sync_before_completion" / "run_001" / "evidence.json"
            frozen_path.parent.mkdir(parents=True, exist_ok=True)
            frozen_path.write_text('{\"frozen\": true}\n', encoding='utf-8')

            return [
                CompletionProcessResult(
                    item_id="daemon_item_sync_before_completion",
                    run_key="synthetic",
                    task_type="l2_campaign",
                    consumed=True,
                    submitted=False,
                    work_item_state="artifact_sync",
                    target_path="control_plane/shadow_exports/review/daemon_item_sync_before_completion/evaluated.json",
                    pr_url=None,
                    submission_error=None,
                )
            ]

        with patch("control_plane.workers.executor.process_completed_items", side_effect=_assert_synced) as process_completed:
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-sync-before-completion",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        heartbeat_seconds=1,
                        auto_process_completions=True,
                    ),
                    poll_seconds=0,
                    max_polls=1,
                ),
            )

        assert result.executed_items == 1
        assert process_completed.call_count == 1
        assert (repo_root / "control_plane" / "shadow_exports" / "review" / "daemon_item_sync_before_completion" / "evaluated.json").exists()
        assert (repo_root / "control_plane" / "shadow_exports" / "frozen_review" / "daemon_item_sync_before_completion" / "run_001" / "evidence.json").exists()


def test_worker_daemon_immediately_processes_completion_for_supported_items() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_immediate_completion", repo_root=repo_root, assigned_machine_key="daemon-worker-immediate")

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
            _seed_ready_work_item(session, item_id="daemon_item_completion_failure", repo_root=repo_root, assigned_machine_key="daemon-worker-immediate-fail")

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


def test_worker_daemon_records_unexpected_immediate_completion_failure_without_poisoning_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_completion_runtime_failure", repo_root=repo_root, assigned_machine_key="daemon-worker-immediate-runtime-fail")

        session_factory = build_session_factory(engine)
        with patch(
            "control_plane.workers.executor.process_completed_items",
            side_effect=RuntimeError("unexpected boom"),
        ):
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-immediate-runtime-fail",
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
                .filter(WorkItem.item_id == "daemon_item_completion_runtime_failure")
                .one()
            )
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            event = (
                session.query(RunEvent)
                .filter(RunEvent.event_type == "completion_processing_failed")
                .one()
            )
            assert event.event_payload["error"] == "unexpected boom"




def test_worker_daemon_skips_same_file_completion_artifact_sync() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_same_file_sync", repo_root=repo_root, assigned_machine_key="daemon-worker-same-file-sync")

        session_factory = build_session_factory(engine)

        def _produce_review_file(session, request):
            review_path = Path(request.repo_root) / "control_plane" / "shadow_exports" / "review" / "daemon_item_same_file_sync" / "evaluated.json"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text('{"ok": true}\n', encoding="utf-8")
            return [
                CompletionProcessResult(
                    item_id="daemon_item_same_file_sync",
                    run_key="synthetic",
                    task_type="l2_campaign",
                    consumed=True,
                    submitted=False,
                    work_item_state="artifact_sync",
                    target_path=str(review_path.relative_to(Path(request.repo_root))),
                    pr_url=None,
                    submission_error=None,
                )
            ]

        with patch("control_plane.workers.executor.process_completed_items", side_effect=_produce_review_file):
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-same-file-sync",
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
            event = (
                session.query(RunEvent)
                .filter(RunEvent.event_type == "completion_processed")
                .one()
            )
            assert event.event_payload["item_id"] == "daemon_item_same_file_sync"


def test_worker_daemon_records_completion_artifact_sync_failure_without_poisoning_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_ready_work_item(session, item_id="daemon_item_artifact_sync_failure", repo_root=repo_root, assigned_machine_key="daemon-worker-artifact-sync-fail")

        session_factory = build_session_factory(engine)
        with patch("control_plane.workers.executor.process_completed_items") as process_completed, patch(
            "control_plane.workers.executor._sync_completion_artifacts_to_repo",
            side_effect=RuntimeError("artifact sync boom"),
        ):
            process_completed.return_value = [
                CompletionProcessResult(
                    item_id="daemon_item_artifact_sync_failure",
                    run_key="synthetic",
                    task_type="l2_campaign",
                    consumed=True,
                    submitted=False,
                    work_item_state="artifact_sync",
                    target_path="control_plane/shadow_exports/review/daemon_item_artifact_sync_failure/evaluated.json",
                    pr_url=None,
                    submission_error=None,
                )
            ]
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-artifact-sync-fail",
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
                .filter(WorkItem.item_id == "daemon_item_artifact_sync_failure")
                .one()
            )
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            event = (
                session.query(RunEvent)
                .filter(RunEvent.event_type == "completion_processing_failed")
                .one()
            )
            assert event.event_payload["error"] == "artifact sync boom"
            assert event.event_payload["phase"] == "artifact_sync"

def test_worker_daemon_registers_machine_slot_capacity() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        session_factory = build_session_factory(engine)

        run_worker_daemon(
            session_factory,
            config=WorkerDaemonConfig(
                worker=WorkerConfig(
                    repo_root=str(repo_root),
                    machine_key="daemon-worker-capacity",
                    machine_role="evaluator",
                    slot_capacity=3,
                    capabilities={"platform": "nangate45", "flow": "openroad"},
                    capability_filter={"platform": "nangate45", "flow": "openroad"},
                    heartbeat_seconds=1,
                ),
                poll_seconds=0,
                max_polls=1,
                stop_on_no_work=True,
                concurrency=3,
            ),
        )

        with Session(engine) as session:
            from control_plane.models.worker_machines import WorkerMachine
            machine = session.query(WorkerMachine).filter_by(machine_key="daemon-worker-capacity").one()
            assert machine.role == "evaluator"
            assert machine.slot_capacity == 3


def test_worker_daemon_runs_all_l1_trials_before_immediate_completion() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)

        with Session(engine) as session:
            task = TaskRequest(
                request_key="queue:daemon_item_l1_trials",
                source="test",
                requested_by="tester",
                title="daemon_item_l1_trials title",
                description="worker daemon l1 trial test",
                layer="layer1",
                flow="openroad",
                priority=1,
                request_payload={"item_id": "daemon_item_l1_trials"},
            )
            session.add(task)
            session.flush()

            out_root = "runs/designs/activations/trial_demo"
            work_item = WorkItem(
                work_item_key="queue:daemon_item_l1_trials",
                task_request_id=task.id,
                item_id="daemon_item_l1_trials",
                layer="layer1",
                flow="openroad",
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.READY,
                priority=1,
                source_mode="config",
                input_manifest={"out_root": out_root},
                command_manifest=[
                    {"name": "build_generator", "run": "python3 -c \"print(\'build\')\""},
                    {
                        "name": "run_sweep",
                        "run": (
                            "python3 -c \"from pathlib import Path; import sys; args=sys.argv; "
                            "out=Path(args[args.index('--out_root')+1]); "
                            "p=out/'trial_wrapper'/'metrics.csv'; "
                            "p.parent.mkdir(parents=True, exist_ok=True); "
                            "p.write_text('platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,result_path\\n' "
                            "'nangate45,ok,trialhash,trialtag,1.0,2.0,3.0,runs/demo/result.json\\n', encoding='utf-8')\" "
                            f"--out_root {out_root} --skip_existing"
                        ),
                    },
                    {
                        "name": "build_runs_index",
                        "run": "python3 -c \"from pathlib import Path; p=Path('runs/index.csv'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text('item_id,status\\n', encoding='utf-8')\"",
                    },
                ],
                expected_outputs=[
                    f"{out_root}/trial_wrapper/metrics.csv",
                    "runs/index.csv",
                ],
                acceptance_rules=[],
                trial_policy_json={"trial_count": 2, "seed_start": 7, "stop_after_failures": 2},
            )
            session.add(work_item)
            session.commit()
            upsert_worker_machine(session, machine_key="daemon-worker-l1-trials", capabilities={"platform": "nangate45", "flow": "openroad"})
            assign_work_item(session, item_id="daemon_item_l1_trials", machine_key="daemon-worker-l1-trials")

        session_factory = build_session_factory(engine)
        checkout_info = CheckoutInfo(
            repo_root=str(repo_root),
            work_dir=str(repo_root),
            head_sha=None,
            git_dirty=False,
            source_commit=None,
            source_commit_matches=None,
            source_commit_relation=None,
            materialized_submodules=(),
            checkout_mode="inplace",
            cleanup_path=None,
        )
        with patch("control_plane.workers.executor.process_completed_items") as process_completed, patch(
            "control_plane.workers.executor.prepare_checkout", return_value=checkout_info
        ), patch("control_plane.workers.executor.cleanup_checkout"):
            process_completed.return_value = [
                CompletionProcessResult(
                    item_id="daemon_item_l1_trials",
                    run_key="synthetic",
                    task_type="l1_sweep",
                    consumed=True,
                    submitted=False,
                    work_item_state="artifact_sync",
                    target_path="control_plane/shadow_exports/l1_promotions/daemon_item_l1_trials.json",
                    pr_url=None,
                    submission_error=None,
                )
            ]
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="daemon-worker-l1-trials",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        heartbeat_seconds=1,
                        auto_process_completions=True,
                    ),
                    poll_seconds=0,
                    max_polls=3,
                    stop_on_no_work=True,
                ),
            )

        assert result.executed_items == 2
        assert [row.status for row in result.results] == ["succeeded", "succeeded", "no_work"]
        assert process_completed.call_count == 1

        with Session(engine) as session:
            runs = session.query(Run).filter(Run.work_item_id == work_item.id).order_by(Run.attempt.asc()).all()
            assert [run.trial_index for run in runs] == [1, 2]
            assert [run.seed for run in runs] == [7, 8]
            work_item = session.query(WorkItem).filter(WorkItem.item_id == "daemon_item_l1_trials").one()
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            assert session.query(RunEvent).filter(RunEvent.event_type == "trial_scheduled").count() == 1
            assert session.query(RunEvent).filter(RunEvent.event_type == "trial_set_completed").count() == 1


def test_worker_daemon_processes_requested_submission_retry() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        now = utcnow()
        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="queue:retry_item",
                source="test",
                requested_by="tester",
                title="retry item",
                description="retry item",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={"item_id": "retry_item"},
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()
            work_item = WorkItem(
                work_item_key="queue:retry_item",
                task_request_id=task_request.id,
                item_id="retry_item",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/index.csv"],
                acceptance_rules=[],
                assigned_machine_key="retry-worker",
            )
            session.add(work_item)
            session.flush()
            upsert_worker_machine(session, machine_key="retry-worker", capabilities={"platform": "nangate45", "flow": "openroad"})
            run = Run(
                run_key="retry_item_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=2),
                completed_at=now - timedelta(minutes=1),
                result_summary="completed",
                result_payload={},
            )
            session.add(run)
            session.flush()
            session.add(
                RunEvent(
                    run_id=run.id,
                    event_time=now,
                    event_type="submission_retry_requested",
                    event_payload={"request_id": "resume_123", "target_machine_key": "retry-worker", "force": False},
                )
            )
            session.commit()

        session_factory = build_session_factory(engine)
        with patch("control_plane.workers.executor.process_completed_items") as process_completed:
            process_completed.return_value = [
                CompletionProcessResult(
                    item_id="retry_item",
                    run_key="retry_item_run_1",
                    task_type="l1_sweep",
                    consumed=True,
                    submitted=True,
                    work_item_state="awaiting_review",
                    target_path="control_plane/shadow_exports/l1_promotions/retry_item.json",
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/999",
                    submission_error=None,
                )
            ]
            result = run_worker_daemon(
                session_factory,
                config=WorkerDaemonConfig(
                    worker=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="retry-worker",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        auto_process_completions=True,
                        completion_submit=True,
                        completion_repo="yhmtmt/RTLGen",
                    ),
                    poll_seconds=0,
                    max_polls=2,
                    stop_on_no_work=True,
                ),
            )

        assert [row.status for row in result.results] == ["resumed", "no_work"]
        assert process_completed.call_count == 1
        with Session(engine) as session:
            started = session.query(RunEvent).filter(RunEvent.event_type == "submission_retry_started").count()
            processed = session.query(RunEvent).filter(RunEvent.event_type == "submission_retry_processed").count()
            assert started == 1
            assert processed == 1
