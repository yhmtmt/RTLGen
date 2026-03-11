"""Polling worker-daemon coverage."""

from __future__ import annotations

from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
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
