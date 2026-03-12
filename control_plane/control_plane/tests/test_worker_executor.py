"""Worker-loop coverage for cp-008."""

from __future__ import annotations
from pathlib import Path
import tempfile
import subprocess
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.services.worker_service import run_worker
from control_plane.workers.checkout import prepare_checkout
from control_plane.workers.executor import WorkerConfig


def seed_ready_work_item(session: Session, *, item_id: str, repo_root: Path, failing: bool) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=f"{item_id} title",
        description="worker test",
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
    commands = [
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
    ]
    if failing:
        commands.append(
            {
                "name": "fail_step",
                "run": "python3 -c \"import sys; sys.exit(3)\"",
            }
        )

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
        command_manifest=commands,
        expected_outputs=[
            str(metrics_path.relative_to(repo_root)),
            str(report_path.relative_to(repo_root)),
        ],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.commit()
    return work_item


def seed_timeout_work_item(session: Session, *, item_id: str) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=f"{item_id} title",
        description="worker timeout test",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()

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
                "name": "slow_step",
                "run": "python3 -c \"import time; time.sleep(2)\"",
            }
        ],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    session.commit()
    return work_item


def seed_source_commit_work_item(
    session: Session,
    *,
    item_id: str,
    source_commit: str,
) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=f"{item_id} title",
        description="worker source commit test",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": item_id},
        source_commit=source_commit,
    )
    session.add(task)
    session.flush()

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
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
        source_commit=source_commit,
    )
    session.add(work_item)
    session.commit()
    return work_item


def init_git_repo(repo_root: Path) -> tuple[str, str]:
    subprocess.run(["git", "-C", str(repo_root), "init"], check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
        text=True,
    )
    marker = repo_root / "marker.txt"
    marker.write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "marker.txt"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "one"], check=True, capture_output=True, text=True)
    commit1 = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    marker.write_text("two\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "commit", "-am", "two"], check=True, capture_output=True, text=True)
    commit2 = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return commit1, commit2


def test_worker_executes_ready_item_and_stages_outputs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_ready_work_item(session, item_id="item_success", repo_root=repo_root, failing=False)

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "succeeded"
        assert results[0].item_id == seeded.item_id

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            lease = session.query(WorkerLease).filter_by(work_item_id=work_item.id).one()
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            assert run.status == RunStatus.SUCCEEDED
            assert lease.status == LeaseStatus.RELEASED
            assert run.result_payload["queue_result"]["status"] == "ok"
            assert run.result_payload["queue_result"]["metrics_rows"] == [
                f"runs/campaigns/{seeded.item_id}/metrics.csv:2"
            ]
            artifact_paths = sorted(artifact.path for artifact in run.artifacts)
            assert f"runs/campaigns/{seeded.item_id}/metrics.csv" in artifact_paths
            assert f"runs/campaigns/{seeded.item_id}/report.md" in artifact_paths
            expected_artifacts = {artifact.path: artifact for artifact in run.artifacts if artifact.kind == "expected_output"}
            assert "metric,value\nlatency,1\n" in expected_artifacts[f"runs/campaigns/{seeded.item_id}/metrics.csv"].metadata_["inline_utf8"]
            assert "# report\n" == expected_artifacts[f"runs/campaigns/{seeded.item_id}/report.md"].metadata_["inline_utf8"]
            assert expected_artifacts[f"runs/campaigns/{seeded.item_id}/metrics.csv"].metadata_["transport_policy"] == "inline_text_evidence"
            assert expected_artifacts[f"runs/campaigns/{seeded.item_id}/report.md"].metadata_["transport_policy"] == "inline_text_evidence"


def test_worker_skips_non_transportable_expected_outputs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        shadow_rel = "control_plane/shadow_exports/tmp/ignored.txt"
        shadow_path = repo_root / shadow_rel
        shadow_path.parent.mkdir(parents=True, exist_ok=True)
        shadow_path.write_text("ignore me\n", encoding="utf-8")
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_ready_work_item(session, item_id="item_transport_policy", repo_root=repo_root, failing=False)
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            work_item.expected_outputs.append(shadow_rel)
            session.commit()

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "succeeded"

        with Session(engine) as session:
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            artifact_paths = {artifact.path for artifact in run.artifacts if artifact.kind == "expected_output"}
            assert shadow_rel not in artifact_paths


def test_worker_marks_failed_run_when_command_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_ready_work_item(session, item_id="item_fail", repo_root=repo_root, failing=True)

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "failed"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            lease = session.query(WorkerLease).filter_by(work_item_id=work_item.id).one()
            assert work_item.state == WorkItemState.FAILED
            assert run.status == RunStatus.FAILED
            assert lease.status == LeaseStatus.RELEASED
            assert run.result_payload["queue_result"]["status"] == "fail"
            assert "failure_command=fail_step" in run.result_payload["queue_result"]["notes"]
            assert run.result_payload["failure_classification"]["category"] == "command_failure"
            assert run.result_payload["retry_decision"]["requeue"] is False


def test_worker_requeues_retryable_timeout_once() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_timeout_work_item(session, item_id="item_timeout")

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
                command_timeout_seconds=1,
                max_retry_attempts=2,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "failed"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            lease = session.query(WorkerLease).filter_by(work_item_id=work_item.id).one()
            assert work_item.state == WorkItemState.READY
            assert run.status == RunStatus.FAILED
            assert lease.status == LeaseStatus.RELEASED
            assert run.result_payload["failure_classification"]["category"] == "command_timeout"
            assert run.result_payload["retry_decision"]["requeue"] is True


def test_worker_stops_retrying_after_max_attempts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_timeout_work_item(session, item_id="item_timeout_exhausted")

        session_factory = build_session_factory(engine)
        config = WorkerConfig(
            repo_root=str(repo_root),
            machine_key="worker-1",
            capabilities={"platform": "nangate45", "flow": "openroad"},
            capability_filter={"platform": "nangate45", "flow": "openroad"},
            lease_seconds=60,
            heartbeat_seconds=1,
            command_timeout_seconds=1,
            max_retry_attempts=2,
        )
        first = run_worker(session_factory, config=config, max_items=1)
        second = run_worker(session_factory, config=config, max_items=1)

        assert first[0].status == "failed"
        assert second[0].status == "failed"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            runs = session.query(Run).filter_by(work_item_id=work_item.id).order_by(Run.attempt.asc()).all()
            assert len(runs) == 2
            assert work_item.state == WorkItemState.FAILED
            assert runs[0].result_payload["retry_decision"]["requeue"] is True
            assert runs[1].result_payload["retry_decision"]["requeue"] is False


def test_worker_blocks_stale_checkout_by_default() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        old_commit, new_commit = init_git_repo(repo_root)
        subprocess.run(
            ["git", "-C", str(repo_root), "checkout", old_commit],
            check=True,
            capture_output=True,
            text=True,
        )
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_source_commit_work_item(
                session,
                item_id="item_stale_checkout",
                source_commit=new_commit,
            )

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "failed"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            assert work_item.state == WorkItemState.READY
            assert run.status == RunStatus.FAILED
            assert run.result_payload["failure_classification"]["category"] == "checkout_error"
            assert run.result_payload["retry_decision"]["requeue"] is True
            assert "at-or-ahead-of" in run.result_summary


def test_worker_allows_checkout_ahead_of_source_commit() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        old_commit, _new_commit = init_git_repo(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_source_commit_work_item(
                session,
                item_id="item_descendant_checkout",
                source_commit=old_commit,
            )

        session_factory = build_session_factory(engine)
        results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="worker-1",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )

        assert len(results) == 1
        assert results[0].status == "succeeded"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            assert run.status == RunStatus.SUCCEEDED
            assert run.result_payload["checkout"]["source_commit_relation"] == "descendant"


def test_prepare_checkout_materializes_missing_submodules_only() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        (repo_root / ".gitmodules").write_text(
            (
                '[submodule "cacti"]\n'
                "\tpath = third_party/cacti\n"
                '\n[submodule "flopoco"]\n'
                "\tpath = third_party/flopoco\n"
            ),
            encoding="utf-8",
        )
        (repo_root / "third_party" / "flopoco").mkdir(parents=True)
        (repo_root / "third_party" / "flopoco" / "README").write_text("present\n", encoding="utf-8")

        calls: list[list[str]] = []

        def fake_run(args, check, capture_output, text):
            calls.append(list(args))
            if args[-2:] == ["rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, stdout="deadbeef\n", stderr="")
            if args[-3:] == ["status", "--porcelain", "--untracked-files=no"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if "submodule" in args:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected subprocess args: {args}")

        with mock.patch("control_plane.workers.checkout.subprocess.run", side_effect=fake_run):
            info = prepare_checkout(
                repo_root=str(repo_root),
                required_submodules=["third_party/cacti"],
            )

        assert info.materialized_submodules == ("third_party/cacti",)
        submodule_calls = [args for args in calls if "submodule" in args]
        assert len(submodule_calls) == 1
        assert "--recursive" not in submodule_calls[0]
        assert submodule_calls[0][-1] == "third_party/cacti"
