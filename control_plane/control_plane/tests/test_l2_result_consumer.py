"""Layer 2 result consumer coverage."""

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
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_succeeded_l2_campaign(session: Session, repo_root: Path) -> tuple[str, str]:
    campaign_dir = repo_root / "runs" / "campaigns" / "npu" / "demo_campaign"
    schedule_rel = "runs/campaigns/npu/demo_campaign/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml"
    descriptors_rel = "runs/campaigns/npu/demo_campaign/artifacts/mapper/fp16_nm1_demo/demo_model/descriptors.bin"
    _write(repo_root / schedule_rel, "schedule: demo\n")
    _write(repo_root / descriptors_rel, "bin\n")
    _write(
        campaign_dir / "best_point.json",
        json.dumps(
            {
                "campaign_id": "demo_campaign",
                "best": {
                    "arch_id": "fp16_nm1_demo",
                    "macro_mode": "flat_nomacro",
                    "objective_rank": 1,
                    "objective_score": 0.0,
                    "latency_ms_mean": 0.5,
                    "energy_mj_mean": 0.2,
                    "critical_path_ns_mean": 5.5,
                    "die_area_um2_mean": 2250000.0,
                    "total_power_mw_mean": 0.18,
                    "flow_elapsed_s_mean": 1000.0,
                },
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        campaign_dir / "summary.csv",
        (
            "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,die_area_um2_mean,total_power_mw_mean,flow_elapsed_s_mean\n"
            "aggregate,fp16_nm1_demo,flat_nomacro,1,0.5,0.2,5.5,2250000,0.18,1000\n"
            "aggregate,fp16_nm2_demo,hier_macro,2,0.7,0.3,5.8,2250000,0.20,1100\n"
        ),
    )
    _write(
        campaign_dir / "results.csv",
        (
            "version,campaign_id,arch_id,macro_mode,status,artifact_schedule_yml,artifact_descriptors_bin\n"
            f"0.1,demo_campaign,fp16_nm1_demo,flat_nomacro,ok,{schedule_rel},{descriptors_rel}\n"
        ),
    )
    _write(campaign_dir / "report.md", "# demo report\n")
    _write(
        campaign_dir / "objective_sweep.csv",
        (
            "profile,w_latency,w_energy,w_area,w_power,w_runtime,best_arch_id,best_macro_mode,objective_score,latency_ms_mean,energy_mj_mean,flow_elapsed_s_mean,best_json,report_md,pareto_csv\n"
            "balanced,1,1,0,0,0,fp16_nm1_demo,flat_nomacro,0.0,0.5,0.2,1000,runs/campaigns/npu/demo_campaign/objective_profiles/balanced/best_point.json,runs/campaigns/npu/demo_campaign/objective_profiles/balanced/report.md,runs/campaigns/npu/demo_campaign/objective_profiles/balanced/pareto.csv\n"
            "latency,1,0,0,0,0,fp16_nm1_demo,flat_nomacro,0.0,0.5,0.2,1000,runs/campaigns/npu/demo_campaign/objective_profiles/latency/best_point.json,runs/campaigns/npu/demo_campaign/objective_profiles/latency/report.md,runs/campaigns/npu/demo_campaign/objective_profiles/latency/pareto.csv\n"
        ),
    )

    task_request = TaskRequest(
        request_key="l2_campaign:test_demo",
        source="test",
        requested_by="@tester",
        title="Layer2 demo campaign",
        description="test l2 result consumer",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={"item_id": "l2_test_demo", "layer": "layer2", "flow": "openroad"},
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_test_demo",
        task_request_id=task_request.id,
        item_id="l2_test_demo",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="src_verilog",
        input_manifest={},
        command_manifest=[],
        expected_outputs=[
            "runs/campaigns/npu/demo_campaign/results.csv",
            "runs/campaigns/npu/demo_campaign/summary.csv",
            "runs/campaigns/npu/demo_campaign/report.md",
            "runs/campaigns/npu/demo_campaign/best_point.json",
            "runs/campaigns/npu/demo_campaign/objective_sweep.csv",
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l2_test_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="5/5 commands succeeded",
        result_payload={"queue_result": {"status": "ok"}},
    )
    session.add(run)
    session.commit()
    return work_item.item_id, run.run_key


def _seed_focused_l2_campaign_with_baseline(session: Session, repo_root: Path) -> str:
    baseline_dir = repo_root / "runs" / "campaigns" / "npu" / "baseline_campaign"
    _write(
        baseline_dir / "summary.csv",
        (
            "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
            "aggregate,fp16_nm1_demo,flat_nomacro,1,0.5,0.2,5.5,0.18,1000,1.0\n"
            "aggregate,fp16_nm1_demo,hier_macro,2,0.5,0.25,5.6,0.20,1100,1.0\n"
        ),
    )
    _write(baseline_dir / "report.md", "# baseline report\n")
    proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
    _write(
        proposal_dir / "proposal.json",
        json.dumps(
            {
                "proposal_id": "prop_l2_demo_v1",
                "kind": "architecture",
                "title": "Demo focused comparison",
                "direct_comparison": {
                    "primary_question": "Does the focused candidate improve the fixed baseline?",
                },
                "baseline_refs": ["runs/campaigns/npu/baseline_campaign"],
            },
            indent=2,
        )
        + "\n",
    )

    task_request = TaskRequest(
        request_key="l2_campaign:l2_test_focused",
        source="test",
        requested_by="@tester",
        title="Layer2 focused demo campaign",
        description="focused comparison",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={
            "item_id": "l2_test_focused",
            "layer": "layer2",
            "flow": "openroad",
            "developer_loop": {
                "proposal_id": "prop_l2_demo_v1",
                "proposal_path": "docs/developer_loop/prop_l2_demo_v1",
            },
        },
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_test_focused",
        task_request_id=task_request.id,
        item_id="l2_test_focused",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="src_verilog",
        input_manifest={},
        command_manifest=[],
        expected_outputs=[
            "runs/campaigns/npu/demo_campaign/results.csv",
            "runs/campaigns/npu/demo_campaign/summary.csv",
            "runs/campaigns/npu/demo_campaign/report.md",
            "runs/campaigns/npu/demo_campaign/best_point.json",
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l2_test_focused_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="4/4 commands succeeded",
        result_payload={"queue_result": {"status": "ok"}},
    )
    session.add(run)
    session.commit()
    return work_item.item_id


def test_consume_l2_result_writes_decision_proposal() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, run_key = _seed_succeeded_l2_campaign(session, repo_root)
            result = consume_l2_result(
                session,
                Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id),
            )
            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.recommended_arch_id == "fp16_nm1_demo"
            assert result.recommended_macro_mode == "flat_nomacro"
            assert result.profile_count == 2
            assert result.work_item_state == "awaiting_review"

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["recommendation"]["arch_id"] == "fp16_nm1_demo"
            assert payload["recommendation"]["macro_mode"] == "flat_nomacro"
            assert len(payload["objective_profiles"]) == 2
            assert payload["source_refs"]["focused_candidate_schedule_yml"] == schedule_rel
            assert payload["source_refs"]["focused_candidate_descriptors_bin"] == descriptors_rel

            artifact = session.query(Artifact).filter_by(kind="decision_proposal").one()
            assert artifact.path == f"control_plane/shadow_exports/l2_decisions/{item_id}.json"


def test_consume_l2_result_allows_explicit_target_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, _run_key = _seed_succeeded_l2_campaign(session, repo_root)
            result = consume_l2_result(
                session,
                Layer2ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    target_path="runs/proposals/l2_test_demo.json",
                ),
            )
            assert result.target_path.endswith("runs/proposals/l2_test_demo.json")
            assert (repo_root / "runs" / "proposals" / "l2_test_demo.json").exists()


def test_consume_l2_result_allows_missing_objective_sweep() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, _run_key = _seed_succeeded_l2_campaign(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            work_item.expected_outputs = [
                path
                for path in (work_item.expected_outputs or [])
                if not str(path).endswith("/objective_sweep.csv")
            ]
            session.commit()

            result = consume_l2_result(
                session,
                Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id),
            )
            assert result.profile_count == 0

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["objective_profiles"] == []
            assert "objective_sweep_csv" not in payload["source_refs"]


def test_consume_l2_result_writes_proposal_assessment_for_focused_comparison() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            _item_id, _run_key = _seed_succeeded_l2_campaign(session, repo_root)
            focused_item_id = _seed_focused_l2_campaign_with_baseline(session, repo_root)

            consume_l2_result(
                session,
                Layer2ConsumeRequest(repo_root=str(repo_root), item_id=focused_item_id),
            )

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{focused_item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assessment = payload["proposal_assessment"]
            assert assessment["proposal_id"] == "prop_l2_demo_v1"
            assert assessment["outcome"] == "no_measurable_change"
            assert assessment["matched_row_count"] == 2
            assert assessment["matched_rows"][0]["arch_id"] == "fp16_nm1_demo"
            assert payload["source_refs"]["baseline_summary_csv"] == "runs/campaigns/npu/baseline_campaign/summary.csv"
            assert payload["source_refs"]["baseline_report_md"] == "runs/campaigns/npu/baseline_campaign/report.md"
