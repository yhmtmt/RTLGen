"""Proposal finalization coverage."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
import control_plane.services.proposal_finalizer as proposal_finalizer
from control_plane.services.proposal_finalizer import ProposalFinalizeRequest, finalize_after_merge


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _seed_repo_files(repo_root: Path, proposal_id: str, requested_items: list[dict[str, object]]) -> Path:
    proposal_dir = repo_root / "docs" / "developer_loop" / proposal_id
    _write(
        proposal_dir / "proposal.json",
        json.dumps({"proposal_id": proposal_id, "title": proposal_id}, indent=2) + "\n",
    )
    _write(
        proposal_dir / "evaluation_requests.json",
        json.dumps({"proposal_id": proposal_id, "source_commit": "pending", "requested_items": requested_items}, indent=2)
        + "\n",
    )
    _write(
        proposal_dir / "promotion_decision.json",
        json.dumps(
            {
                "proposal_id": proposal_id,
                "candidate_id": "pending",
                "decision": "pending",
                "reason": "pending",
                "evidence_refs": [],
                "next_action": "pending",
                "requires_human_approval": True,
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        proposal_dir / "promotion_result.json",
        json.dumps(
            {
                "proposal_id": proposal_id,
                "decision": "pending",
                "pr_number": None,
                "merge_commit": None,
                "merged_utc": None,
            },
            indent=2,
        )
        + "\n",
    )
    _write(proposal_dir / "analysis_report.md", "# Analysis Report\n\n## Candidate\n- pending\n")
    return proposal_dir


def test_finalize_accepts_directory_style_proposal_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_dir_style_v1"
        proposal_dir = _seed_repo_files(
            repo_root,
            proposal_id,
            [
                {
                    "item_id": "dir_style_r1",
                    "task_type": "l1_sweep",
                    "objective": "dir_style_metrics",
                    "status": "pending",
                }
            ],
        )
        payload_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / "dir_style_r1.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "dir_style_r1",
                    "run_key": "dir_style_r1_run_1",
                    "source_commit": "abc123",
                    "proposals": [
                        {
                            "metrics_ref": {"metrics_csv": "runs/designs/demo/metrics.csv", "platform": "nangate45", "status": "ok"},
                            "metric_summary": {"critical_path_ns": 1.0, "die_area": 100.0, "total_power_mw": 0.01},
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
            task = TaskRequest(
                request_key="l1:dir_style_r1",
                source="test",
                requested_by="tester",
                title="dir style l1",
                description="dir style objective",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "developer_loop": {
                        "proposal_id": proposal_id,
                        "proposal_path": str(proposal_dir.relative_to(repo_root)),
                    }
                },
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1:dir_style_r1",
                task_request_id=task.id,
                item_id="dir_style_r1",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/designs/demo/metrics.csv"],
                acceptance_rules=[],
                source_commit="abc123",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="dir_style_r1_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="abc123",
                result_summary="ok",
                result_payload={"queue_result": {"status": "ok"}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="promotion_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="x",
                    metadata_={},
                )
            )
            session.commit()

            result = finalize_after_merge(
                session,
                ProposalFinalizeRequest(
                    repo_root=str(repo_root),
                    item_id="dir_style_r1",
                    pr_number=99,
                    merge_commit="facefeed",
                    merged_utc="2026-03-25T03:00:00Z",
                    git_publish=False,
                ),
            )

        assert result.skipped is False
        assert result.decision == "promote"
        promotion_result = json.loads((proposal_dir / "promotion_result.json").read_text())
        assert promotion_result["merge_commit"] == "facefeed"


def test_finalize_l1_merge_promotes_and_releases_next_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_l1_demo_v1"
        proposal_path = _seed_repo_files(
            repo_root,
            proposal_id,
            [
                {
                    "item_id": "l1_demo_r1",
                    "task_type": "l1_sweep",
                    "objective": "demo_metrics",
                    "status": "pending",
                },
                {
                    "item_id": "l1_demo_followon_r1",
                    "task_type": "l2_campaign",
                    "objective": "followon",
                    "depends_on_item_ids": ["l1_demo_r1"],
                    "status": "blocked_on_prerequisite",
                },
            ],
        )
        payload_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / "l1_demo_r1.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "l1_demo_r1",
                    "run_key": "l1_demo_r1_run_1",
                    "source_commit": "abc123",
                    "proposals": [
                        {
                            "metrics_ref": {"metrics_csv": "runs/designs/demo/metrics.csv", "platform": "nangate45", "status": "ok"},
                            "metric_summary": {"critical_path_ns": 1.23, "die_area": 20000.0, "total_power_mw": 0.1},
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
            task = TaskRequest(
                request_key="l1:l1_demo_r1",
                source="test",
                requested_by="tester",
                title="demo l1",
                description="demo l1 objective",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "developer_loop": {
                        "proposal_id": proposal_id,
                        "proposal_path": str((proposal_path / "proposal.json").relative_to(repo_root)),
                    }
                },
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1:l1_demo_r1",
                task_request_id=task.id,
                item_id="l1_demo_r1",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/designs/demo/metrics.csv"],
                acceptance_rules=[],
                source_commit="abc123",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="l1_demo_r1_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="abc123",
                result_summary="ok",
                result_payload={"queue_result": {"status": "ok"}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="promotion_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="x",
                    metadata_={},
                )
            )
            session.commit()

            result = finalize_after_merge(
                session,
                ProposalFinalizeRequest(
                    repo_root=str(repo_root),
                    item_id="l1_demo_r1",
                    pr_number=80,
                    merge_commit="deadbeef",
                    merged_utc="2026-03-24T00:00:00Z",
                    git_publish=False,
                ),
            )

        assert result.skipped is False
        assert result.decision == "promote"
        assert result.next_item_id == "l1_demo_followon_r1"
        evaluation_requests = json.loads((proposal_path / "evaluation_requests.json").read_text())
        current = evaluation_requests["requested_items"][0]
        followon = evaluation_requests["requested_items"][1]
        assert current["status"] == "merged"
        assert current["merged_pr_number"] == 80
        assert followon["status"] == "ready_to_queue"
        promotion_decision = json.loads((proposal_path / "promotion_decision.json").read_text())
        assert promotion_decision["decision"] == "promote"
        assert promotion_decision["requires_human_approval"] is False
        promotion_result = json.loads((proposal_path / "promotion_result.json").read_text())
        assert promotion_result["merge_commit"] == "deadbeef"
        analysis_report = (proposal_path / "analysis_report.md").read_text()
        assert "`candidate_id`: `l1_demo_r1`" in analysis_report
        assert "- `promote`" in analysis_report


def test_finalize_l2_candidate_merge_promotes_after_iterate_baseline() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_l2_demo_v1"
        proposal_path = _seed_repo_files(
            repo_root,
            proposal_id,
            [
                {
                    "item_id": "l2_demo_measurement_r1",
                    "task_type": "l2_campaign",
                    "evaluation_mode": "measurement_only",
                    "status": "merged",
                },
                {
                    "item_id": "l2_demo_fused_r1",
                    "task_type": "l2_campaign",
                    "evaluation_mode": "paired_comparison",
                    "paired_baseline_item_id": "l2_demo_measurement_r1",
                    "depends_on_item_ids": ["l2_demo_measurement_r1"],
                    "status": "ready_to_queue",
                },
            ],
        )
        promotion_result_path = proposal_path / "promotion_result.json"
        promotion_result = json.loads(promotion_result_path.read_text())
        promotion_result["decision"] = "iterate"
        promotion_result["pr_number"] = 82
        promotion_result["merge_commit"] = "cafebabe"
        promotion_result["merged_utc"] = "2026-03-24T01:00:00Z"
        promotion_result_path.write_text(json.dumps(promotion_result, indent=2) + "\n", encoding="utf-8")

        payload_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / "l2_demo_fused_r1.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "l2_demo_fused_r1",
                    "run_key": "l2_demo_fused_r1_run_1",
                    "source_commit": "fedcba",
                    "evaluation_record": {"summary": "Focused comparison improved latency and/or energy without regressing matched rows."},
                    "proposal_assessment": {
                        "outcome": "improved",
                        "summary": "Focused comparison improved latency and/or energy without regressing matched rows.",
                    },
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
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
                        "proposal_id": proposal_id,
                        "proposal_path": str((proposal_path / "proposal.json").relative_to(repo_root)),
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
                state=WorkItemState.MERGED,
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
                Artifact(
                    run_id=run.id,
                    kind="decision_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="z",
                    metadata_={},
                )
            )
            session.commit()

            result = finalize_after_merge(
                session,
                ProposalFinalizeRequest(
                    repo_root=str(repo_root),
                    item_id="l2_demo_fused_r1",
                    pr_number=85,
                    merge_commit="deadbeef",
                    merged_utc="2026-03-24T02:00:00Z",
                    git_publish=False,
                ),
            )

        assert result.skipped is False
        assert result.decision == "promote"
        assert result.next_item_id is None
        evaluation_requests = json.loads((proposal_path / "evaluation_requests.json").read_text())
        fused = evaluation_requests["requested_items"][1]
        assert fused["status"] == "merged"
        promotion_decision = json.loads((proposal_path / "promotion_decision.json").read_text())
        assert promotion_decision["decision"] == "promote"
        promotion_result = json.loads((proposal_path / "promotion_result.json").read_text())
        assert promotion_result["decision"] == "promote"
        assert promotion_result["pr_number"] == 85


def test_finalize_l2_measurement_merge_iterates_and_unblocks_candidate() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_l2_demo_v1"
        proposal_path = _seed_repo_files(
            repo_root,
            proposal_id,
            [
                {
                    "item_id": "l2_demo_measurement_r1",
                    "task_type": "l2_campaign",
                    "evaluation_mode": "measurement_only",
                    "status": "pending",
                },
                {
                    "item_id": "l2_demo_fused_r1",
                    "task_type": "l2_campaign",
                    "evaluation_mode": "paired_comparison",
                    "paired_baseline_item_id": "l2_demo_measurement_r1",
                    "depends_on_item_ids": ["l2_demo_measurement_r1"],
                    "status": "blocked_on_baseline",
                },
            ],
        )
        payload_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / "l2_demo_measurement_r1.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "l2_demo_measurement_r1",
                    "run_key": "l2_demo_measurement_r1_run_1",
                    "source_commit": "def456",
                    "evaluation_record": {"summary": "This item records metrics for the requested architecture point and does not emit a proposal judgment."},
                    "proposal_assessment": None,
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
            task = TaskRequest(
                request_key="l2:l2_demo_measurement_r1",
                source="test",
                requested_by="tester",
                title="demo l2",
                description="demo l2 objective",
                layer=LayerName.LAYER2,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "developer_loop": {
                        "proposal_id": proposal_id,
                        "proposal_path": str((proposal_path / "proposal.json").relative_to(repo_root)),
                        "evaluation": {"mode": "measurement_only"},
                    }
                },
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="l2:l2_demo_measurement_r1",
                task_request_id=task.id,
                item_id="l2_demo_measurement_r1",
                layer=LayerName.LAYER2,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l2_campaign",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/campaigns/demo/report.md"],
                acceptance_rules=[],
                source_commit="def456",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="l2_demo_measurement_r1_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="def456",
                result_summary="ok",
                result_payload={"queue_result": {"status": "ok"}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="decision_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="y",
                    metadata_={},
                )
            )
            session.commit()

            result = finalize_after_merge(
                session,
                ProposalFinalizeRequest(
                    repo_root=str(repo_root),
                    item_id="l2_demo_measurement_r1",
                    pr_number=82,
                    merge_commit="cafebabe",
                    merged_utc="2026-03-24T01:00:00Z",
                    git_publish=False,
                ),
            )

        assert result.skipped is False
        assert result.decision == "iterate"
        assert result.next_item_id == "l2_demo_fused_r1"
        evaluation_requests = json.loads((proposal_path / "evaluation_requests.json").read_text())
        current = evaluation_requests["requested_items"][0]
        fused = evaluation_requests["requested_items"][1]
        assert current["status"] == "merged"
        assert fused["status"] == "ready_to_queue"
        promotion_decision = json.loads((proposal_path / "promotion_decision.json").read_text())
        assert promotion_decision["decision"] == "iterate"
        assert promotion_decision["next_action"] == "queue l2_demo_fused_r1"


def test_finalize_refreshes_repo_before_loading_proposal_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_l1_refresh_demo_v1"
        proposal_path = repo_root / "docs" / "developer_loop" / proposal_id
        payload_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / "l1_refresh_demo_r1.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "l1_refresh_demo_r1",
                    "run_key": "l1_refresh_demo_r1_run_1",
                    "source_commit": "abc123",
                    "proposals": [
                        {
                            "metrics_ref": {"metrics_csv": "runs/designs/demo/metrics.csv", "platform": "nangate45", "status": "ok"},
                            "metric_summary": {"critical_path_ns": 1.0, "die_area": 10.0, "total_power_mw": 0.1},
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
            task = TaskRequest(
                request_key="l1:l1_refresh_demo_r1",
                source="test",
                requested_by="tester",
                title="refresh l1",
                description="refresh l1 objective",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "developer_loop": {
                        "proposal_id": proposal_id,
                        "proposal_path": str((proposal_path / "proposal.json").relative_to(repo_root)),
                    }
                },
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1:l1_refresh_demo_r1",
                task_request_id=task.id,
                item_id="l1_refresh_demo_r1",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/designs/demo/metrics.csv"],
                acceptance_rules=[],
                source_commit="abc123",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="l1_refresh_demo_r1_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="abc123",
                result_summary="ok",
                result_payload={"queue_result": {"status": "ok"}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="promotion_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="x",
                    metadata_={},
                )
            )
            session.commit()

            original_prepare = proposal_finalizer._prepare_repo
            original_git_dirty = proposal_finalizer._git_dirty
            original_run_git = proposal_finalizer._run_git
            try:
                def fake_prepare(root: Path) -> str:
                    _seed_repo_files(
                        root,
                        proposal_id,
                        [
                            {
                                "item_id": "l1_refresh_demo_r1",
                                "task_type": "l1_sweep",
                                "objective": "demo_metrics",
                                "status": "pending",
                            }
                        ],
                    )
                    return "merge123"

                proposal_finalizer._prepare_repo = fake_prepare
                proposal_finalizer._git_dirty = lambda _root: True

                def fake_run_git(_root: Path, *args: str, env=None) -> str:
                    if args[:1] == ("rev-parse",):
                        return "finalize123"
                    return ""

                proposal_finalizer._run_git = fake_run_git

                result = finalize_after_merge(
                    session,
                    ProposalFinalizeRequest(
                        repo_root=str(repo_root),
                        item_id="l1_refresh_demo_r1",
                        pr_number=86,
                        git_publish=True,
                    ),
                )
            finally:
                proposal_finalizer._prepare_repo = original_prepare
                proposal_finalizer._git_dirty = original_git_dirty
                proposal_finalizer._run_git = original_run_git

        assert result.skipped is False
        assert result.decision == "promote"
        assert result.commit_sha == "finalize123"
        promotion_result = json.loads((proposal_path / "promotion_result.json").read_text())
        assert promotion_result["merge_commit"] == "merge123"


def test_prepare_repo_resets_detached_worktree_to_origin_master() -> None:
    calls: list[tuple[str, ...]] = []
    original_run_git = proposal_finalizer._run_git
    try:
        def fake_run_git(_root: Path, *args: str, env=None) -> str:
            calls.append(args)
            if args[:1] == ("rev-parse",):
                return "finalize123"
            return ""

        proposal_finalizer._run_git = fake_run_git
        commit_sha = proposal_finalizer._prepare_repo(Path('/tmp/repo'))
    finally:
        proposal_finalizer._run_git = original_run_git

    assert commit_sha == "finalize123"
    assert calls == [
        ("fetch", "origin"),
        ("reset", "--hard", "refs/remotes/origin/master"),
        ("rev-parse", "HEAD"),
    ]

def test_finalize_l1_retry_item_rebinds_requested_entry() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        proposal_id = "prop_l1_retry_demo_v1"
        proposal_path = _seed_repo_files(
            repo_root,
            proposal_id,
            [
                {
                    "item_id": "l1_retry_demo_r1",
                    "task_type": "l1_sweep",
                    "objective": "demo_metrics",
                    "evaluation_mode": "measurement_only",
                    "status": "pending",
                }
            ],
        )
        payload_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / "l1_retry_demo_r2.json"
        _write(
            payload_path,
            json.dumps(
                {
                    "item_id": "l1_retry_demo_r2",
                    "run_key": "l1_retry_demo_r2_run_1",
                    "source_commit": "abc123",
                    "objective": "demo_metrics",
                    "proposals": [
                        {
                            "metrics_ref": {"metrics_csv": "runs/designs/demo/metrics.csv", "platform": "nangate45", "status": "ok"},
                            "metric_summary": {"critical_path_ns": 1.11, "die_area": 123.0, "total_power_mw": 0.2},
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
        )

        with _session() as session:
            task = TaskRequest(
                request_key="l1:l1_retry_demo_r2",
                source="test",
                requested_by="tester",
                title="retry l1",
                description="demo_metrics",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "developer_loop": {
                        "proposal_id": proposal_id,
                        "proposal_path": str((proposal_path / "proposal.json").relative_to(repo_root)),
                    },
                    "task": {
                        "objective": "demo_metrics",
                    },
                },
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1:l1_retry_demo_r2",
                task_request_id=task.id,
                item_id="l1_retry_demo_r2",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.MERGED,
                priority=1,
                input_manifest={},
                command_manifest=[],
                expected_outputs=["runs/designs/demo/metrics.csv"],
                acceptance_rules=[],
                source_commit="abc123",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="l1_retry_demo_r2_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="abc123",
                result_summary="ok",
                result_payload={"queue_result": {"status": "ok"}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="promotion_proposal",
                    storage_mode="repo",
                    path=str(payload_path.relative_to(repo_root)),
                    sha256="x",
                    metadata_={},
                )
            )
            session.commit()

            result = finalize_after_merge(
                session,
                ProposalFinalizeRequest(
                    repo_root=str(repo_root),
                    item_id="l1_retry_demo_r2",
                    pr_number=89,
                    merge_commit="beadfeed",
                    merged_utc="2026-03-25T01:43:24Z",
                    git_publish=False,
                ),
            )

        assert result.skipped is False
        assert result.decision == "promote"
        evaluation_requests = json.loads((proposal_path / "evaluation_requests.json").read_text())
        current = evaluation_requests["requested_items"][0]
        assert current["item_id"] == "l1_retry_demo_r2"
        assert current["prior_item_ids"] == ["l1_retry_demo_r1"]
        assert current["status"] == "merged"
        assert current["merged_pr_number"] == 89
