"""Review package publishing coverage."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result
from control_plane.services.review_publisher import ReviewPublishRequest, publish_review_package


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_l1_reviewable(session: Session, repo_root: Path) -> tuple[str, str]:
    metrics_rel = "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv"
    _write(
        repo_root / metrics_rel,
        (
            "platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'nangate45,ok,fast0001,tag_fast,12.0,30000,0.18,{"CLOCK_PERIOD": 6.0, "CORE_UTILIZATION": 30},'
            "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json\n"
        ),
    )

    payload = {
        "item_id": "l1_review_demo",
        "title": "Layer1 review demo",
        "layer": "layer1",
        "flow": "openroad",
        "developer_loop": {
            "proposal_id": "prop_l1_review_demo_v1",
            "proposal_path": "docs/developer_loop/prop_l1_review_demo_v1",
        },
        "handoff": {
            "branch": "eval/l1_review_demo/<session_id>",
            "pr_title": "eval: run layer1 review demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_review_demo",
            },
            "checklist": [
                "Commit lightweight outputs only",
                "Keep result_path repo-portable",
            ],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_review_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 review demo",
        description="test l1 review publish",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_review_demo",
        task_request_id=task_request.id,
        item_id="l1_review_demo",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="config",
        input_manifest={"configs": ["examples/config_softmax_rowwise_int8.json"]},
        command_manifest=[],
        expected_outputs=[metrics_rel, "runs/index.csv"],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l1_review_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="4/4 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()

    consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))
    return work_item.item_id, run.run_key


def _seed_l2_reviewable(session: Session, repo_root: Path) -> tuple[str, str]:
    campaign_dir = repo_root / "control_plane" / "shadow_exports" / "campaigns" / "demo_l2"
    design_metrics_rel = "control_plane/shadow_exports/designs/demo_nm1/metrics.csv"
    _write(
        repo_root / design_metrics_rel,
        (
            "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'demo_nm1,nangate45,cfg0001,p1,tag1,ok,5.5,2250000,0.18,"{""CLOCK_PERIOD"": 10.0}",'
            "control_plane/shadow_exports/designs/demo_nm1/work/p1/result.json\n"
        ),
    )
    _write(
        campaign_dir / "best_point.json",
        json.dumps(
            {
                "campaign_id": "demo_l2",
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
            "scope,arch_id,macro_mode,model_id,n,sample_count,latency_ms_mean,latency_ms_std,throughput_infer_per_s_mean,throughput_infer_per_s_std,energy_mj_mean,energy_mj_std,critical_path_ns_mean,die_area_um2_mean,total_power_mw_mean,flow_elapsed_s_mean,place_gp_elapsed_s_mean,model_count,rank,latency_norm,energy_norm,area_norm,power_norm,runtime_norm,objective_score,objective_rank\n"
            "aggregate,fp16_nm1_demo,flat_nomacro,,,1,0.5,,1.0,,0.2,,5.5,2250000,0.18,1000,500,1,1,0,0,0,0,0,0,1\n"
            "aggregate,fp16_nm1_demo,hier_macro,,,1,0.5,,1.0,,0.25,,5.6,2250000,0.20,1100,520,1,2,0,1,0,1,1,1,2\n"
        ),
    )
    _write(campaign_dir / "results.csv", "version,campaign_id,arch_id,macro_mode,status\n0.1,demo_l2,fp16_nm1_demo,flat_nomacro,ok\n")
    _write(campaign_dir / "report.md", "# demo report\n")
    _write(
        campaign_dir / "objective_sweep.csv",
        (
            "profile,w_latency,w_energy,w_area,w_power,w_runtime,best_arch_id,best_macro_mode,objective_score,latency_ms_mean,energy_mj_mean,flow_elapsed_s_mean,best_json,report_md,pareto_csv\n"
            "balanced,1,1,0,0,0,fp16_nm1_demo,flat_nomacro,0.0,0.5,0.2,1000,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/best_point.json,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/report.md,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/pareto.csv\n"
        ),
    )
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
    proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_review_demo_v1"
    _write(
        proposal_dir / "proposal.json",
        json.dumps(
            {
                "proposal_id": "prop_l2_review_demo_v1",
                "kind": "architecture",
                "title": "Layer2 review demo",
                "direct_comparison": {
                    "primary_question": "Does the focused candidate improve the fixed baseline?",
                },
                "baseline_refs": ["runs/campaigns/npu/baseline_campaign"],
            },
            indent=2,
        )
        + "\n",
    )

    payload = {
        "item_id": "l2_review_demo",
        "title": "Layer2 review demo",
        "layer": "layer2",
        "flow": "openroad",
        "developer_loop": {
            "proposal_id": "prop_l2_review_demo_v1",
            "proposal_path": "docs/developer_loop/prop_l2_review_demo_v1",
        },
        "handoff": {
            "branch": "eval/l2_review_demo/<session_id>",
            "pr_title": "eval: run layer2 review demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l2_review_demo",
            },
            "checklist": [
                "Commit lightweight campaign outputs only",
                "Keep committed result_path fields repo-portable",
            ],
        },
    }
    task_request = TaskRequest(
        request_key="l2_campaign:l2_review_demo",
        source="test",
        requested_by="@tester",
        title="Layer2 review demo",
        description="test l2 review publish",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_review_demo",
        task_request_id=task_request.id,
        item_id="l2_review_demo",
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
            "control_plane/shadow_exports/campaigns/demo_l2/results.csv",
            "control_plane/shadow_exports/campaigns/demo_l2/summary.csv",
            "control_plane/shadow_exports/campaigns/demo_l2/report.md",
            "control_plane/shadow_exports/campaigns/demo_l2/best_point.json",
            "control_plane/shadow_exports/campaigns/demo_l2/objective_sweep.csv",
            design_metrics_rel,
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l2_review_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="5/5 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{design_metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()

    consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))
    return work_item.item_id, run.run_key


def test_publish_review_package_for_l1() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            result = publish_review_package(
                session,
                ReviewPublishRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t070000z",
                    host="cp-host",
                ),
            )
            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.review_artifact_kind == "promotion_proposal"

            package_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "review_package.json"
            snapshot_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "evaluated.json"
            assert package_path.exists()
            assert snapshot_path.exists()

            payload = json.loads(package_path.read_text(encoding="utf-8"))
            assert payload["pr_payload"]["branch"] == "eval/l1_review_demo/s20260310t070000z"
            assert payload["pr_payload"]["body_fields"]["session_id"] == "s20260310t070000z"
            assert payload["pr_payload"]["body_fields"]["host"] == "cp-host"
            assert payload["review_artifact"]["kind"] == "promotion_proposal"
            assert payload["developer_loop"]["proposal_id"] == "prop_l1_review_demo_v1"
            assert payload["developer_loop"]["proposal_path"] == "docs/developer_loop/prop_l1_review_demo_v1"
            assert payload["queue_snapshot"]["result"]["status"] == "ok"
            assert len(payload["queue_snapshot"]["result"]["metrics_rows"]) == 1
            assert (
                payload["queue_snapshot"]["result"]["metrics_rows"][0]["result_path"]
                == "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json"
            )
            assert "proposal_id: `prop_l1_review_demo_v1`" in payload["pr_payload"]["body_md"]


def test_publish_review_package_for_l2() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            result = publish_review_package(
                session,
                ReviewPublishRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t071500z",
                    host="cp-host",
                ),
            )
            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.review_artifact_kind == "decision_proposal"

            package_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "review_package.json"
            payload = json.loads(package_path.read_text(encoding="utf-8"))
            assert payload["pr_payload"]["branch"] == "eval/l2_review_demo/s20260310t071500z"
            assert payload["review_artifact"]["kind"] == "decision_proposal"
            assert payload["review_artifact"]["payload"]["recommendation"]["arch_id"] == "fp16_nm1_demo"
            assert payload["review_artifact"]["payload"]["proposal_assessment"]["outcome"] == "no_measurable_change"
            assert payload["developer_loop"]["proposal_id"] == "prop_l2_review_demo_v1"
            assert payload["developer_loop"]["proposal_path"] == "docs/developer_loop/prop_l2_review_demo_v1"
            assert payload["queue_snapshot"]["result"]["status"] == "ok"
            assert "reviewer_first_read: `docs/developer_loop/prop_l2_review_demo_v1` plus `docs/developer_agent_review.md`" in payload["pr_payload"]["body_md"]
            assert "proposal_outcome: `no_measurable_change`" in payload["pr_payload"]["body_md"]
            assert "baseline_ref: `runs/campaigns/npu/baseline_campaign`" in payload["pr_payload"]["body_md"]
