"""Top-level CLI coverage for evaluator refresh requests."""

from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.cli.request_evaluator_refresh import _operator_status_details
from control_plane.cli.main import main
from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import FlowName, LayerName, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.worker_machines import WorkerMachine
from control_plane.models.work_items import WorkItem


def test_top_level_request_evaluator_refresh_forwards_operator_status_flags() -> None:
    with patch("control_plane.cli.main.request_evaluator_refresh_main", return_value=0) as request_refresh:
        result = main(
            [
                "request-evaluator-refresh",
                "--repo",
                "yhmtmt/RTLGen",
                "--repo-root",
                "/repo",
                "--target-commit",
                "abcdef",
                "--database-url",
                "postgresql+psycopg://rtlgen:rtlgen@localhost/rtlgen_control_plane",
                "--include-operator-status",
                "--machine-key",
                "eval-daemon",
                "--recent-limit",
                "5",
                "--dry-run",
            ]
        )

    assert result == 0
    forwarded = request_refresh.call_args.args[0]
    assert forwarded[forwarded.index("--repo") + 1] == "yhmtmt/RTLGen"
    assert forwarded[forwarded.index("--repo-root") + 1] == "/repo"
    assert forwarded[forwarded.index("--target-commit") + 1] == "abcdef"
    assert forwarded[forwarded.index("--database-url") + 1].startswith("postgresql+psycopg://")
    assert forwarded[forwarded.index("--machine-key") + 1] == "eval-daemon"
    assert forwarded[forwarded.index("--recent-limit") + 1] == "5"
    assert "--include-operator-status" in forwarded
    assert "--dry-run" in forwarded


def test_operator_status_details_include_source_requirements() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            machine = WorkerMachine(
                machine_key="eval-daemon",
                hostname="eval-daemon",
                executor_kind="local_process",
                role="evaluator",
                slot_capacity=4,
                capabilities={
                    "flow": "openroad",
                    "platform": "nangate45",
                    "worker_source": {
                        "head": "a" * 40,
                        "repo_root": "/workspaces/rtlgen-eval-clean",
                    },
                },
                last_seen_at=utcnow(),
            )
            session.add(machine)
            task = TaskRequest(
                request_key="queue:needs_source",
                source="test",
                requested_by="tester",
                title="needs source",
                description="needs source",
                layer=LayerName.LAYER2,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={"item_id": "needs_source"},
            )
            session.add(task)
            session.flush()
            session.add(
                WorkItem(
                    work_item_key="queue:needs_source",
                    task_request_id=task.id,
                    item_id="needs_source",
                    layer=LayerName.LAYER2,
                    flow=FlowName.OPENROAD,
                    platform="nangate45",
                    task_type="l2_campaign",
                    state=WorkItemState.READY,
                    priority=1,
                    source_commit="b" * 40,
                    assigned_machine_key=machine.machine_key,
                    input_manifest={},
                    command_manifest=[],
                    expected_outputs=[],
                    acceptance_rules=[],
                )
            )
            session.commit()

        details = _operator_status_details(
            database_url=f"sqlite+pysqlite:///{db_path}",
            repo_root=td,
            machine_key="eval-daemon",
            recent_limit=5,
        )

    machine_detail = next(row for row in details if row.startswith("machine eval-daemon:"))
    assert "worker_attention=assigned_ready_requires_newer_source" in machine_detail
    assert "source_requirements=[" in machine_detail
    assert "needs_source" in machine_detail
    assert "'required_sha': '" + ("b" * 40) + "'" in machine_detail
    assert "'worker_head': '" + ("a" * 40) + "'" in machine_detail
