import tempfile
from pathlib import Path

from control_plane.models.artifacts import Artifact
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.dependency_gate import refresh_all_blocked_items
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.clock import utcnow


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def test_refresh_all_blocked_items_releases_satisfied_dependent() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        decision_rel = "control_plane/shadow_exports/l2_decisions/baseline.json"
        review_rel = "control_plane/shadow_exports/review/baseline/review_package.json"
        queue_rel = "control_plane/shadow_exports/review/baseline/evaluated.json"
        summary_rel = "runs/campaigns/baseline/summary.csv"
        for rel in (decision_rel, review_rel, queue_rel, summary_rel):
            path = repo_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok\n", encoding="utf-8")

        with make_session() as session:
            dep_task = TaskRequest(
                request_key="queue:baseline",
                source="test",
                requested_by="tester",
                title="baseline",
                description="baseline",
                layer="layer2",
                flow="openroad",
                priority=1,
                request_payload={},
            )
            session.add(dep_task)
            session.flush()
            dependency = WorkItem(
                work_item_key="queue:baseline",
                task_request_id=dep_task.id,
                item_id="baseline_item",
                layer="layer2",
                flow="openroad",
                platform="nangate45",
                task_type="l2_campaign",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
            )
            session.add(dependency)
            session.flush()
            run = Run(
                run_key="baseline_run",
                work_item_id=dependency.id,
                attempt=1,
                executor_type="internal_worker",
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="ok",
                result_payload={},
            )
            session.add(run)
            session.flush()
            for kind, rel in (("decision_proposal", decision_rel), ("review_package", review_rel), ("queue_snapshot", queue_rel), ("expected_output", summary_rel)):
                session.add(Artifact(run_id=run.id, kind=kind, storage_mode="repo", path=rel, sha256="x", metadata_={}))

            blocked_task = TaskRequest(
                request_key="queue:blocked",
                source="test",
                requested_by="tester",
                title="blocked",
                description="blocked",
                layer="layer2",
                flow="openroad",
                priority=1,
                request_payload={
                    "developer_loop": {
                        "dependencies": {
                            "item_ids": ["baseline_item"],
                            "requires_merged_inputs": True,
                            "requires_materialized_refs": True,
                        }
                    }
                },
            )
            session.add(blocked_task)
            session.flush()
            blocked = WorkItem(
                work_item_key="queue:blocked",
                task_request_id=blocked_task.id,
                item_id="blocked_item",
                layer="layer2",
                flow="openroad",
                platform="nangate45",
                task_type="l2_campaign",
                state=WorkItemState.BLOCKED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=[],
                acceptance_rules=[],
            )
            session.add(blocked)
            session.commit()

            released = refresh_all_blocked_items(session, repo_root=repo_root)
            session.commit()
            session.refresh(blocked)

        assert released == ["blocked_item"]
        assert blocked.state == WorkItemState.READY
