"""Worker-loop coverage for cp-008."""

from __future__ import annotations
import json
from pathlib import Path
import tempfile
import subprocess
import threading
import time
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import LeaseStatus, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.services.run_service import request_run_cancel
from control_plane.services.worker_service import run_worker
from control_plane.workers.checkout import cleanup_checkout, prepare_checkout
from control_plane.workers.executor import WorkerConfig, _materialize_generated_inputs


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


def seed_results_artifact_work_item(session: Session, *, item_id: str, repo_root: Path) -> WorkItem:
    task = TaskRequest(
        request_key=f"queue:{item_id}",
        source="test",
        requested_by="tester",
        title=f"{item_id} title",
        description="worker supporting artifact test",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": item_id},
    )
    session.add(task)
    session.flush()

    campaign_dir = repo_root / "runs" / "campaigns" / item_id
    results_path = campaign_dir / "results.csv"
    report_path = campaign_dir / "report.md"
    schedule_path = campaign_dir / "artifacts" / "mapper" / "fp16_nm2_softmax_r4" / "logistic_regression" / "schedule.yml"
    trace_path = campaign_dir / "artifacts" / "perf" / "fp16_nm2_softmax_r4" / "logistic_regression" / "trace.json"
    commands = [
        {
            "name": "write_supporting_artifacts",
            "run": (
                "python3 -c \"from pathlib import Path; "
                f"schedule=Path('{schedule_path.relative_to(repo_root)}'); "
                f"trace=Path('{trace_path.relative_to(repo_root)}'); "
                f"results=Path('{results_path.relative_to(repo_root)}'); "
                f"report=Path('{report_path.relative_to(repo_root)}'); "
                "schedule.parent.mkdir(parents=True, exist_ok=True); "
                "trace.parent.mkdir(parents=True, exist_ok=True); "
                "results.parent.mkdir(parents=True, exist_ok=True); "
                "schedule.write_text('steps:\\n- gemm\\n', encoding='utf-8'); "
                "trace.write_text('{\\\"latency_ns\\\": 621}\\n', encoding='utf-8'); "
                "results.write_text("
                "'version,campaign_id,arch_id,macro_mode,status,artifact_schedule_yml,artifact_perf_trace_json\\n"
                f"0.1,{item_id},fp16_nm2_softmax_r4,flat_nomacro,ok,{schedule_path.relative_to(repo_root)},{trace_path.relative_to(repo_root)}\\n', "
                "encoding='utf-8'); "
                "report.write_text('# report\\n', encoding='utf-8')\""
            ),
        }
    ]

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
            str(results_path.relative_to(repo_root)),
            str(report_path.relative_to(repo_root)),
        ],
        acceptance_rules=[],
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


def test_worker_stages_linked_results_supporting_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_results_artifact_work_item(session, item_id="item_supporting", repo_root=repo_root)

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
            supporting = {artifact.path: artifact for artifact in run.artifacts if artifact.kind == "supporting_output"}
            schedule_rel = (
                f"runs/campaigns/{seeded.item_id}/artifacts/mapper/"
                "fp16_nm2_softmax_r4/logistic_regression/schedule.yml"
            )
            trace_rel = (
                f"runs/campaigns/{seeded.item_id}/artifacts/perf/"
                "fp16_nm2_softmax_r4/logistic_regression/trace.json"
            )
            assert schedule_rel in supporting
            assert trace_rel in supporting
            assert supporting[schedule_rel].metadata_["inline_utf8"] == "steps:\n- gemm\n"
            assert '"latency_ns"' in supporting[trace_rel].metadata_["inline_utf8"]
            assert supporting[schedule_rel].metadata_["transport_policy"] == "inline_text_supporting"


def test_materialize_generated_inputs_preserves_physical_source_campaign() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        base_campaign_path = repo_root / "runs" / "campaigns" / "npu" / "demo" / "campaign.json"
        target_campaign_path = repo_root / "runs" / "campaigns" / "npu" / "demo" / "campaign__item.json"
        base_campaign_path.parent.mkdir(parents=True, exist_ok=True)
        base_campaign_path.write_text(
            json.dumps(
                {
                    "campaign_id": "demo",
                    "platform": "nangate45",
                    "models": [],
                    "architecture_points": [],
                    "outputs": {
                        "campaign_dir": "runs/campaigns/npu/demo",
                        "results_csv": "runs/campaigns/npu/demo/results.csv",
                        "report_md": "runs/campaigns/npu/demo/report.md",
                    },
                    "physical_source_campaign": "runs/campaigns/npu/old/campaign.json",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        work_item = WorkItem(
            item_id="item",
            input_manifest={
                "generated_campaign": {
                    "base_campaign_path": "runs/campaigns/npu/demo/campaign.json",
                    "path": "runs/campaigns/npu/demo/campaign__item.json",
                    "outputs": {
                        "campaign_dir": "runs/campaigns/npu/demo__item",
                        "results_csv": "runs/campaigns/npu/demo__item/results.csv",
                        "report_md": "runs/campaigns/npu/demo__item/report.md",
                    },
                }
            },
        )

        _materialize_generated_inputs(checkout_root=str(repo_root), work_item=work_item)

        generated = json.loads(target_campaign_path.read_text(encoding="utf-8"))
        assert generated["outputs"]["campaign_dir"] == "runs/campaigns/npu/demo__item"
        assert generated["physical_source_campaign"] == "runs/campaigns/npu/old/campaign.json"


def test_materialize_generated_inputs_cleans_existing_l2_campaign_outputs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        base_campaign_path = repo_root / "runs" / "campaigns" / "npu" / "demo" / "campaign.json"
        target_campaign_path = repo_root / "runs" / "campaigns" / "npu" / "demo" / "campaign__item.json"
        output_dir = repo_root / "runs" / "campaigns" / "npu" / "demo__item"
        stale_results = output_dir / "results.csv"
        base_campaign_path.parent.mkdir(parents=True, exist_ok=True)
        base_campaign_path.write_text(
            json.dumps(
                {
                    "campaign_id": "demo",
                    "platform": "nangate45",
                    "models": [],
                    "architecture_points": [],
                    "outputs": {
                        "campaign_dir": "runs/campaigns/npu/demo",
                        "results_csv": "runs/campaigns/npu/demo/results.csv",
                        "report_md": "runs/campaigns/npu/demo/report.md",
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        stale_results.write_text("stale\n", encoding="utf-8")

        work_item = WorkItem(
            item_id="item",
            task_type="l2_campaign",
            input_manifest={
                "generated_campaign": {
                    "base_campaign_path": "runs/campaigns/npu/demo/campaign.json",
                    "path": "runs/campaigns/npu/demo/campaign__item.json",
                    "outputs": {
                        "campaign_dir": "runs/campaigns/npu/demo__item",
                        "results_csv": "runs/campaigns/npu/demo__item/results.csv",
                        "report_md": "runs/campaigns/npu/demo__item/report.md",
                    },
                }
            },
        )

        _materialize_generated_inputs(checkout_root=str(repo_root), work_item=work_item)

        assert not stale_results.exists()
        generated = json.loads(target_campaign_path.read_text(encoding="utf-8"))
        assert generated["outputs"]["campaign_dir"] == "runs/campaigns/npu/demo__item"


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


def test_worker_marks_command_timeout_terminal() -> None:
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
            assert work_item.state == WorkItemState.FAILED
            assert run.status == RunStatus.TIMED_OUT
            assert lease.status == LeaseStatus.RELEASED
            assert run.result_payload["failure_classification"]["category"] == "command_timeout"
            assert run.result_payload["retry_decision"]["requeue"] is False


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
        assert second[0].status == "no_work"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            runs = session.query(Run).filter_by(work_item_id=work_item.id).order_by(Run.attempt.asc()).all()
            assert len(runs) == 1
            assert work_item.state == WorkItemState.FAILED
            assert runs[0].result_payload["retry_decision"]["requeue"] is False


def test_worker_honors_cancel_requested_during_command() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_timeout_work_item(session, item_id="item_cancel")

        session_factory = build_session_factory(engine)
        results_box: list[list] = []

        def _run_worker() -> None:
            results_box.append(
                run_worker(
                    session_factory,
                    config=WorkerConfig(
                        repo_root=str(repo_root),
                        machine_key="worker-1",
                        capabilities={"platform": "nangate45", "flow": "openroad"},
                        capability_filter={"platform": "nangate45", "flow": "openroad"},
                        lease_seconds=60,
                        heartbeat_seconds=1,
                        command_progress_seconds=1,
                    ),
                    max_items=1,
                )
            )

        worker_thread = threading.Thread(target=_run_worker)
        worker_thread.start()

        run_key = None
        deadline = time.time() + 5
        while time.time() < deadline and run_key is None:
            with Session(engine) as session:
                run = session.query(Run).join(WorkItem).filter(WorkItem.item_id == seeded.item_id).first()
                if run is not None:
                    run_key = run.run_key
                    request_run_cancel(session, run_key=run_key, requested_by="tester", reason="stop test")
                    break
            time.sleep(0.1)

        worker_thread.join(timeout=10)
        assert run_key is not None
        assert results_box
        assert results_box[0][0].status == "canceled"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=run_key).one()
            assert work_item.state == WorkItemState.FAILED
            assert run.status == RunStatus.CANCELED
            assert run.result_payload["failure_classification"]["category"] == "command_canceled"


def test_worker_marks_stalled_command_as_timed_out() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            seeded = seed_timeout_work_item(session, item_id="item_stall")

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
                command_stall_timeout_seconds=1,
                command_progress_seconds=1,
            ),
            max_items=1,
        )

        assert results[0].status == "timed_out"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            assert work_item.state == WorkItemState.FAILED
            assert run.status == RunStatus.TIMED_OUT
            assert run.result_payload["failure_classification"]["category"] == "command_stall"


def test_worker_fetches_source_commit_into_clean_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        bare_remote = Path(td) / "remote.git"
        bare_remote.mkdir()
        subprocess.run(["git", "init", "--bare", str(bare_remote)], check=True, capture_output=True, text=True)

        seed_repo = Path(td) / "seed"
        seed_repo.mkdir()
        old_commit, new_commit = init_git_repo(seed_repo)
        subprocess.run(
            ["git", "-C", str(seed_repo), "remote", "add", "origin", str(bare_remote)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(["git", "-C", str(seed_repo), "push", "origin", "HEAD"], check=True, capture_output=True, text=True)

        repo_root = Path(td) / "repo"
        subprocess.run(
            ["git", "clone", "--quiet", str(bare_remote), str(repo_root)],
            check=True,
            capture_output=True,
            text=True,
        )
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
                item_id="item_fetch_checkout",
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
        assert results[0].status == "succeeded"

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id=seeded.item_id).one()
            run = session.query(Run).filter_by(run_key=results[0].run_key).one()
            assert work_item.state == WorkItemState.ARTIFACT_SYNC
            assert run.status == RunStatus.SUCCEEDED
            assert run.result_payload["checkout"]["source_commit_relation"] == "exact"
            assert run.result_payload["checkout"]["head_sha"] == new_commit


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
            assert run.result_payload["checkout"]["source_commit_relation"] == "exact"


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

        def fake_run(args, check=None, capture_output=None, text=None):
            calls.append(list(args))
            if "worktree" in args and "add" in args:
                checkout_root = Path(args[-2])
                checkout_root.mkdir(parents=True, exist_ok=True)
                (checkout_root / ".gitmodules").write_text((repo_root / ".gitmodules").read_text(encoding="utf-8"), encoding="utf-8")
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-3:] == ["cat-file", "-e", "HEAD^{commit}"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
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
                source_commit="HEAD",
                required_submodules=["third_party/cacti"],
            )

        assert info.materialized_submodules == ("third_party/cacti",)
        assert info.checkout_mode == "worktree"
        assert info.work_dir != str(repo_root)
        submodule_calls = [args for args in calls if "submodule" in args]
        assert len(submodule_calls) == 1
        assert "--recursive" not in submodule_calls[0]
        assert submodule_calls[0][-1] == "third_party/cacti"


def test_prepare_checkout_skips_submodules_when_not_requested() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        (repo_root / ".gitmodules").write_text(
            (
                '[submodule "cacti"]\n'
                "\tpath = third_party/cacti\n"
            ),
            encoding="utf-8",
        )

        calls: list[list[str]] = []

        def fake_run(args, check=None, capture_output=None, text=None):
            calls.append(list(args))
            if "worktree" in args and "add" in args:
                checkout_root = Path(args[-2])
                checkout_root.mkdir(parents=True, exist_ok=True)
                (checkout_root / ".gitmodules").write_text(
                    (repo_root / ".gitmodules").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-3:] == ["cat-file", "-e", "HEAD^{commit}"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-2:] == ["rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, stdout="deadbeef\n", stderr="")
            if args[-3:] == ["status", "--porcelain", "--untracked-files=no"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected subprocess args: {args}")

        with mock.patch("control_plane.workers.checkout.subprocess.run", side_effect=fake_run):
            info = prepare_checkout(
                repo_root=str(repo_root),
                source_commit="HEAD",
            )

        assert info.materialized_submodules == ()
        submodule_calls = [args for args in calls if "submodule" in args]
        assert submodule_calls == []


def test_prepare_checkout_creates_and_cleans_worktree() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        commit1, _commit2 = init_git_repo(repo_root)

        info = prepare_checkout(repo_root=str(repo_root), source_commit=commit1)
        checkout_root = Path(info.work_dir)
        assert checkout_root.exists()
        assert checkout_root != repo_root
        assert info.checkout_mode == "worktree"

        cleanup_checkout(info)
        assert not checkout_root.exists()


def test_prepare_checkout_refreshes_remote_refs_not_raw_sha() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()

        calls: list[list[str]] = []
        cat_file_checks: list[str] = []

        def fake_run(args, check=None, capture_output=None, text=None):
            calls.append(list(args))
            if args[-3:] == ["fetch", "--quiet", "origin"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if "worktree" in args and "add" in args:
                checkout_root = Path(args[-2])
                checkout_root.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-2:] == ["rev-parse", "9adb961"]:
                return subprocess.CompletedProcess(args, 0, stdout="9adb961000000000000000000000000000000000\n", stderr="")
            if args[-2:] == ["rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, stdout="9adb961000000000000000000000000000000000\n", stderr="")
            if args[-3:] == ["status", "--porcelain", "--untracked-files=no"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-4:] == ["merge-base", "--is-ancestor", "9adb961000000000000000000000000000000000", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected subprocess args: {args}")

        def fake_git_success(_repo_root, *args):
            joined = " ".join(args)
            cat_file_checks.append(joined)
            if joined == "cat-file -e 9adb961^{commit}":
                return len(cat_file_checks) >= 2
            return False

        with mock.patch("control_plane.workers.checkout.subprocess.run", side_effect=fake_run):
            with mock.patch("control_plane.workers.checkout._git_success", side_effect=fake_git_success):
                info = prepare_checkout(repo_root=str(repo_root), source_commit="9adb961")

        assert info.head_sha == "9adb961000000000000000000000000000000000"
        assert info.source_commit == "9adb961000000000000000000000000000000000"
        fetch_calls = [args for args in calls if args[-3:] == ["fetch", "--quiet", "origin"]]
        assert len(fetch_calls) == 1
        assert not any(args[-1] == "9adb961" for args in calls if "fetch" in args)


def test_prepare_checkout_accepts_short_source_commit_when_head_matches_resolved_sha() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()

        calls: list[list[str]] = []

        def fake_run(args, check=None, capture_output=None, text=None):
            calls.append(list(args))
            if "worktree" in args and "add" in args:
                checkout_root = Path(args[-2])
                checkout_root.mkdir(parents=True, exist_ok=True)
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[-2:] == ["rev-parse", "81a0705"]:
                return subprocess.CompletedProcess(args, 0, stdout="81a07051896adcdb9649dd445f93c550b62dd135\n", stderr="")
            if args[-2:] == ["rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, stdout="81a07051896adcdb9649dd445f93c550b62dd135\n", stderr="")
            if args[-3:] == ["status", "--porcelain", "--untracked-files=no"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected subprocess args: {args}")

        def fake_git_success(_repo_root, *args):
            return " ".join(args) == "cat-file -e 81a0705^{commit}"

        with mock.patch("control_plane.workers.checkout.subprocess.run", side_effect=fake_run):
            with mock.patch("control_plane.workers.checkout._git_success", side_effect=fake_git_success):
                info = prepare_checkout(
                    repo_root=str(repo_root),
                    source_commit="81a0705",
                    enforce_source_commit=True,
                )

        assert info.source_commit == "81a07051896adcdb9649dd445f93c550b62dd135"
        assert info.head_sha == "81a07051896adcdb9649dd445f93c550b62dd135"
        assert info.source_commit_relation == "exact"
