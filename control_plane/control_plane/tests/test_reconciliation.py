"""GitHub linkage reconciliation coverage for cp-007."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.api.app import create_app
from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import LeaseStatus, WorkItemState
from control_plane.models.artifacts import Artifact
from control_plane.models.github_links import GitHubLink
from control_plane.models.run_events import RunEvent
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_leases import WorkerLease
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services.github_bridge import GitHubReconcileRequest, reconcile_github_link
from control_plane.services.proposal_finalizer import ProposalFinalizationError


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def seed_reviewable_run(session: Session) -> Run:
    task = TaskRequest(
        request_key="queue:item_review",
        source="test",
        requested_by="tester",
        title="item review",
        description="review objective",
        layer="layer2",
        flow="openroad",
        priority=1,
        request_payload={"item_id": "item_review"},
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key="queue:item_review",
        task_request_id=task.id,
        item_id="item_review",
        layer="layer2",
        flow="openroad",
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
    )
    session.add(work_item)
    machine = WorkerMachine(
        machine_key="machine-review",
        hostname="machine-review",
        executor_kind="docker",
        capabilities={"platform": "nangate45"},
    )
    session.add(machine)
    session.flush()
    lease = WorkerLease(
        work_item_id=work_item.id,
        machine_id=machine.id,
        lease_token="lease-review",
        status=LeaseStatus.RELEASED,
        leased_at=utcnow(),
        expires_at=utcnow(),
        last_heartbeat_at=utcnow(),
    )
    session.add(lease)
    run = Run(
        run_key="run-review-1",
        work_item_id=work_item.id,
        lease_id=lease.id,
        attempt=1,
        executor_type="internal_worker",
        machine_id=machine.id,
        branch_name="eval/item_review/s20260308t000000z",
        status="succeeded",
        started_at=utcnow(),
        completed_at=utcnow(),
        result_summary="review ok",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [{"metrics_csv": "runs/x.csv", "platform": "nangate45", "tag": "t", "status": "ok"}]}}
    )
    session.add(run)
    session.commit()
    return run


def test_reconcile_merge_triggers_proposal_finalizer_when_repo_root_is_present() -> None:
    with make_session() as session:
        run = seed_reviewable_run(session)
        with patch("control_plane.services.github_bridge.finalize_after_merge") as finalize_mock:
            from control_plane.services.proposal_finalizer import ProposalFinalizeResult

            finalize_mock.return_value = ProposalFinalizeResult(
                item_id="item_review",
                proposal_id="prop_demo_v1",
                decision="iterate",
                next_item_id="item_followon",
                commit_sha="feedface",
                skipped=False,
                skip_reason=None,
            )
            result = reconcile_github_link(
                session,
                GitHubReconcileRequest(
                    repo="yhmtmt/RTLGen",
                    item_id="item_review",
                    branch_name="eval/item_review/s20260308t000000z",
                    pr_number=42,
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                    state="pr_merged",
                    run_key=run.run_key,
                    repo_root="/tmp/repo",
                ),
            )
        assert result.finalized_proposal_id == "prop_demo_v1"
        assert result.finalization_commit == "feedface"
        assert result.finalization_error is None
        link = session.query(GitHubLink).filter_by(pr_number=42).one()
        assert link.metadata_["finalized_proposal_id"] == "prop_demo_v1"
        assert link.metadata_["finalization_commit"] == "feedface"
        assert link.metadata_["finalization_error"] is None
        finalize_mock.assert_called_once()


def test_reconcile_merge_persists_finalization_error_for_retry() -> None:
    with make_session() as session:
        run = seed_reviewable_run(session)
        with patch("control_plane.services.github_bridge.finalize_after_merge") as finalize_mock:
            finalize_mock.side_effect = ProposalFinalizationError("proposal files missing")
            result = reconcile_github_link(
                session,
                GitHubReconcileRequest(
                    repo="yhmtmt/RTLGen",
                    item_id="item_review",
                    branch_name="eval/item_review/s20260308t000000z",
                    pr_number=43,
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/43",
                    state="pr_merged",
                    run_key=run.run_key,
                    repo_root="/tmp/repo",
                ),
            )
        assert result.finalization_commit is None
        assert result.finalization_error == "proposal files missing"
        link = session.query(GitHubLink).filter_by(pr_number=43).one()
        assert link.metadata_["finalization_commit"] is None
        assert link.metadata_["finalization_error"] == "proposal files missing"
        assert link.metadata_["finalization_skipped"] is False


def test_reconcile_github_link_open_and_merge() -> None:
    with make_session() as session:
        run = seed_reviewable_run(session)
        result = reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo="yhmtmt/RTLGen",
                item_id="item_review",
                branch_name="eval/item_review/s20260308t000000z",
                pr_number=42,
                pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                state="pr_open",
                run_key=run.run_key,
                metadata={"source": "test"},
            ),
        )
        link = session.query(GitHubLink).filter_by(pr_number=42).one()
        work_item = session.query(WorkItem).filter_by(item_id="item_review").one()
        assert result.state == "pr_open"
        assert work_item.state == WorkItemState.AWAITING_REVIEW
        assert link.branch_name == "eval/item_review/s20260308t000000z"

        result = reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo="yhmtmt/RTLGen",
                item_id="item_review",
                branch_name="eval/item_review/s20260308t000000z",
                pr_number=42,
                pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                state="pr_merged",
                run_key=run.run_key,
            ),
        )
        session.refresh(work_item)
        assert result.state == "pr_merged"
        assert work_item.state == WorkItemState.MERGED
        assert session.query(RunEvent).filter_by(run_id=run.id).count() == 2


def test_reconcile_can_infer_item_id_from_branch_name() -> None:
    with make_session() as session:
        seed_reviewable_run(session)
        result = reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo="yhmtmt/RTLGen",
                branch_name="eval/item_review/s20260308t000000z",
                state="branch_created",
            ),
        )
        assert result.item_id == "item_review"
        assert result.branch_name == "eval/item_review/s20260308t000000z"


def test_github_route_works_in_process() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            run = seed_reviewable_run(session)
            run_key = run.run_key

        old = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status, headers, body = app.handle(
                "POST",
                "/api/v1/github/reconcile",
                json.dumps(
                    {
                        "repo": "yhmtmt/RTLGen",
                        "item_id": "item_review",
                        "branch_name": "eval/item_review/s20260308t000000z",
                        "pr_number": 43,
                        "state": "pr_open",
                        "run_key": run_key,
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            assert headers["Content-Type"] == "application/json"
            response = json.loads(body.decode("utf-8"))
            assert response["item_id"] == "item_review"
            assert response["state"] == "pr_open"
        finally:
            if old is None:
                del os.environ["RTLCP_DATABASE_URL"]
            else:
                os.environ["RTLCP_DATABASE_URL"] = old


def test_reconcile_merge_releases_blocked_dependent_when_materialized() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        summary_rel = "runs/campaigns/baseline_run/summary.csv"
        report_rel = "runs/campaigns/baseline_run/report.md"
        queue_rel = "control_plane/shadow_exports/review/item_review/evaluated.json"
        decision_rel = "control_plane/shadow_exports/l2_decisions/item_review.json"
        review_rel = "control_plane/shadow_exports/review/item_review/review_package.json"
        for rel in (summary_rel, report_rel, queue_rel, decision_rel, review_rel):
            path = repo_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok\n", encoding="utf-8")

        with make_session() as session:
            run = seed_reviewable_run(session)
            for kind, rel in (
                ("expected_output", summary_rel),
                ("expected_output", report_rel),
                ("queue_snapshot", queue_rel),
                ("decision_proposal", decision_rel),
                ("review_package", review_rel),
            ):
                session.add(Artifact(run_id=run.id, kind=kind, storage_mode="repo", path=rel, sha256="x", metadata_={}))

            dep_task = TaskRequest(
                request_key="queue:item_dependent",
                source="test",
                requested_by="tester",
                title="dependent",
                description="dependent objective",
                layer="layer2",
                flow="openroad",
                priority=1,
                request_payload={
                    "developer_loop": {
                        "dependencies": {
                            "item_ids": ["item_review"],
                            "requires_merged_inputs": True,
                            "requires_materialized_refs": True,
                        }
                    }
                },
            )
            session.add(dep_task)
            session.flush()
            dependent = WorkItem(
                work_item_key="queue:item_dependent",
                task_request_id=dep_task.id,
                item_id="item_dependent",
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
            session.add(dependent)
            session.commit()

            reconcile_github_link(
                session,
                GitHubReconcileRequest(
                    repo="yhmtmt/RTLGen",
                    item_id="item_review",
                    branch_name="eval/item_review/s20260308t000000z",
                    pr_number=42,
                    pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                    state="pr_merged",
                    run_key=run.run_key,
                    repo_root=str(repo_root),
                ),
            )
            session.refresh(dependent)
            assert dependent.state == WorkItemState.READY


def test_reconcile_github_link_closed_supersedes_item() -> None:
    with make_session() as session:
        run = seed_reviewable_run(session)
        reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo="yhmtmt/RTLGen",
                item_id="item_review",
                branch_name="eval/item_review/s20260308t000000z",
                pr_number=42,
                pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                state="pr_open",
                run_key=run.run_key,
                metadata={"source": "test"},
            ),
        )
        result = reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo="yhmtmt/RTLGen",
                item_id="item_review",
                branch_name="eval/item_review/s20260308t000000z",
                pr_number=42,
                pr_url="https://github.com/yhmtmt/RTLGen/pull/42",
                state="pr_closed",
                run_key=run.run_key,
            ),
        )
        link = session.query(GitHubLink).filter_by(pr_number=42).one()
        work_item = session.query(WorkItem).filter_by(item_id="item_review").one()
        assert result.state == "pr_closed"
        assert work_item.state == WorkItemState.SUPERSEDED
        assert link.state.value == "pr_closed"
        event_types = [row.event_type for row in session.query(RunEvent).filter_by(run_id=run.id).all()]
        assert "pr_closed" in event_types
        assert "work_item_superseded" in event_types
