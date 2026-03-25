"""GitHub merge polling coverage."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, GitHubLinkState, LayerName, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.github_poller import GitHubPollRequest, poll_github_links


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _seed_link(session: Session, *, pr_state: GitHubLinkState = GitHubLinkState.PR_OPEN) -> tuple[WorkItem, Run]:
    task = TaskRequest(
        request_key="l2:l2_demo_fused_r1",
        source="test",
        requested_by="tester",
        title="demo l2 fused",
        description="demo l2 candidate",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={
            "developer_loop": {
                "proposal_id": "prop_l2_demo_v1",
                "proposal_path": "docs/developer_loop/prop_l2_demo_v1/proposal.json",
                "evaluation": {"mode": "paired_comparison"},
                "comparison": {"role": "candidate", "paired_baseline_item_id": "l2_demo_measurement_r1"},
            }
        },
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key="l2:l2_demo_fused_r1",
        task_request_id=task.id,
        item_id="l2_demo_fused_r1",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.AWAITING_REVIEW,
        priority=1,
        input_manifest={},
        command_manifest=[],
        expected_outputs=["runs/campaigns/demo/report.md"],
        acceptance_rules=[],
        source_commit="fedcba",
    )
    session.add(work_item)
    session.flush()
    run = Run(
        run_key="l2_demo_fused_r1_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="fedcba",
        result_summary="ok",
        result_payload={"queue_result": {"status": "ok"}},
    )
    session.add(run)
    session.flush()
    session.add(
        GitHubLink(
            work_item_id=work_item.id,
            run_id=run.id,
            repo="yhmtmt/RTLGen",
            branch_name="eval/l2_demo_fused_r1/s20260325t000000z",
            pr_number=85,
            pr_url="https://github.com/yhmtmt/RTLGen/pull/85",
            head_sha="oldhead",
            base_branch="master",
            state=pr_state,
            metadata_={},
        )
    )
    session.commit()
    return work_item, run


def test_poll_github_links_reconciles_merged_pr() -> None:
    with _session() as session:
        work_item, run = _seed_link(session)
        merged_payload = {
            "merged_at": "2026-03-25T00:00:00Z",
            "merge_commit_sha": "deadbeef",
            "html_url": "https://github.com/yhmtmt/RTLGen/pull/85",
            "head": {"ref": "eval/l2_demo_fused_r1/s20260325t000000z"},
            "base": {"ref": "master"},
        }
        with patch("control_plane.services.github_poller.subprocess.run") as run_mock, patch(
            "control_plane.services.github_poller.reconcile_github_link"
        ) as reconcile_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=["gh", "api"],
                returncode=0,
                stdout=json.dumps(merged_payload),
                stderr="",
            )
            result = poll_github_links(session, GitHubPollRequest(repo_root="/tmp/repo"))

        assert result.checked_count == 1
        assert result.merged_count == 1
        assert result.skipped_count == 0
        assert result.errors == []
        reconcile_mock.assert_called_once()
        request = reconcile_mock.call_args.args[1]
        assert request.repo == "yhmtmt/RTLGen"
        assert request.item_id == work_item.item_id
        assert request.run_key == run.run_key
        assert request.state == "pr_merged"
        assert request.pr_number == 85
        assert request.head_sha == "deadbeef"
        assert request.repo_root == "/tmp/repo"


def test_poll_github_links_skips_open_pr() -> None:
    with _session() as session:
        _seed_link(session)
        open_payload = {
            "merged_at": None,
            "merge_commit_sha": None,
            "html_url": "https://github.com/yhmtmt/RTLGen/pull/85",
            "head": {"ref": "eval/l2_demo_fused_r1/s20260325t000000z"},
            "base": {"ref": "master"},
        }
        with patch("control_plane.services.github_poller.subprocess.run") as run_mock, patch(
            "control_plane.services.github_poller.reconcile_github_link"
        ) as reconcile_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=["gh", "api"],
                returncode=0,
                stdout=json.dumps(open_payload),
                stderr="",
            )
            result = poll_github_links(session, GitHubPollRequest(repo_root="/tmp/repo"))

        assert result.checked_count == 1
        assert result.merged_count == 0
        assert result.skipped_count == 1
        assert result.errors == []
        reconcile_mock.assert_not_called()
