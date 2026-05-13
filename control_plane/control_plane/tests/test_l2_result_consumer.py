"""Layer 2 result consumer coverage."""

from __future__ import annotations

import copy
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


def _seed_multimodel_measurement_campaign(session: Session, repo_root: Path) -> tuple[str, str]:
    campaign_dir = repo_root / "runs" / "campaigns" / "npu" / "demo_multimodel_campaign"
    schedule_linear_rel = (
        "runs/campaigns/npu/demo_multimodel_campaign/artifacts/mapper/fp16_nm1_demo/linear_tail/schedule.yml"
    )
    schedule_relu_rel = (
        "runs/campaigns/npu/demo_multimodel_campaign/artifacts/mapper/fp16_nm1_demo/relu_tail/schedule.yml"
    )
    trace_linear_rel = "runs/campaigns/npu/demo_multimodel_campaign/artifacts/perf/fp16_nm1_demo/linear_tail/trace.json"
    trace_relu_rel = "runs/campaigns/npu/demo_multimodel_campaign/artifacts/perf/fp16_nm1_demo/relu_tail/trace.json"
    _write(repo_root / schedule_linear_rel, "schedule: linear\n")
    _write(repo_root / schedule_relu_rel, "schedule: relu\n")
    _write(repo_root / trace_linear_rel, "{\"trace\":\"linear\"}\n")
    _write(repo_root / trace_relu_rel, "{\"trace\":\"relu\"}\n")
    _write(
        campaign_dir / "best_point.json",
        json.dumps(
            {
                "campaign_id": "demo_multimodel_campaign",
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
            "scope,arch_id,macro_mode,model_id,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,die_area_um2_mean,total_power_mw_mean,flow_elapsed_s_mean\n"
            "aggregate,fp16_nm1_demo,flat_nomacro,,1,0.5,0.2,5.5,2250000,0.18,1000\n"
            "model,fp16_nm1_demo,flat_nomacro,linear_tail,1,0.5,0.2,5.5,2250000,0.18,1000\n"
            "model,fp16_nm1_demo,flat_nomacro,relu_tail,2,0.6,0.21,5.5,2250000,0.18,1000\n"
        ),
    )
    _write(
        campaign_dir / "results.csv",
        (
            "version,campaign_id,arch_id,macro_mode,model_id,status,artifact_schedule_yml,artifact_perf_trace_json\n"
            f"0.1,demo_multimodel_campaign,fp16_nm1_demo,flat_nomacro,linear_tail,ok,{schedule_linear_rel},{trace_linear_rel}\n"
            f"0.1,demo_multimodel_campaign,fp16_nm1_demo,flat_nomacro,relu_tail,ok,{schedule_relu_rel},{trace_relu_rel}\n"
        ),
    )
    _write(campaign_dir / "report.md", "# demo multimodel report\n")

    task_request = TaskRequest(
        request_key="l2_campaign:test_multimodel_measurement",
        source="test",
        requested_by="@tester",
        title="Layer2 multimodel measurement campaign",
        description="test multimodel measurement evidence export",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={
            "item_id": "l2_test_multimodel_measurement",
            "layer": "layer2",
            "flow": "openroad",
            "developer_loop": {
                "evaluation": {
                    "mode": "measurement_only",
                }
            },
        },
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_test_multimodel_measurement",
        task_request_id=task_request.id,
        item_id="l2_test_multimodel_measurement",
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
            "runs/campaigns/npu/demo_multimodel_campaign/results.csv",
            "runs/campaigns/npu/demo_multimodel_campaign/summary.csv",
            "runs/campaigns/npu/demo_multimodel_campaign/report.md",
            "runs/campaigns/npu/demo_multimodel_campaign/best_point.json",
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l2_test_multimodel_measurement_run_1",
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
                "abstraction": {"layer": "full_architecture"},
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


def _seed_campaign_work_item(
    session: Session,
    repo_root: Path,
    *,
    item_id: str,
    campaign_dir_rel: str,
    summary_rows: str,
    proposal_path: str,
    comparison: dict[str, str] | None = None,
) -> str:
    campaign_dir = repo_root / campaign_dir_rel
    schedule_rel = f"{campaign_dir_rel}/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml"
    descriptors_rel = f"{campaign_dir_rel}/artifacts/mapper/fp16_nm1_demo/demo_model/descriptors.bin"
    _write(repo_root / schedule_rel, "schedule: demo\n")
    _write(repo_root / descriptors_rel, "bin\n")
    _write(
        campaign_dir / "best_point.json",
        json.dumps(
            {
                "campaign_id": item_id,
                "best": {
                    "arch_id": "fp16_nm1_demo",
                    "macro_mode": "flat_nomacro",
                    "objective_rank": 1,
                    "objective_score": 0.0,
                    "latency_ms_mean": 0.4,
                    "energy_mj_mean": 0.15,
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
    _write(campaign_dir / "summary.csv", summary_rows)
    _write(
        campaign_dir / "results.csv",
        (
            "version,campaign_id,arch_id,macro_mode,status,artifact_schedule_yml,artifact_descriptors_bin\n"
            f"0.1,{item_id},fp16_nm1_demo,flat_nomacro,ok,{schedule_rel},{descriptors_rel}\n"
        ),
    )
    _write(campaign_dir / "report.md", "# demo report\n")

    request_payload: dict[str, object] = {
        "item_id": item_id,
        "layer": "layer2",
        "flow": "openroad",
        "developer_loop": {
            "proposal_id": "prop_l2_demo_v1",
            "proposal_path": proposal_path,
        },
    }
    if comparison:
        request_payload["developer_loop"]["comparison"] = comparison

    task_request = TaskRequest(
        request_key=f"l2_campaign:{item_id}",
        source="test",
        requested_by="@tester",
        title=f"Layer2 {item_id}",
        description="focused comparison",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=request_payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key=f"l2_campaign:{item_id}",
        task_request_id=task_request.id,
        item_id=item_id,
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
            f"{campaign_dir_rel}/results.csv",
            f"{campaign_dir_rel}/summary.csv",
            f"{campaign_dir_rel}/report.md",
            f"{campaign_dir_rel}/best_point.json",
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key=f"{item_id}_run_1",
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
    return item_id


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
            assert result.work_item_state == "artifact_sync"

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["recommendation"]["arch_id"] == "fp16_nm1_demo"
            assert payload["recommendation"]["macro_mode"] == "flat_nomacro"
            assert len(payload["objective_profiles"]) == 2
            assert payload["source_commit"] == "deadbeef"
            assert payload["review_metadata_source_commit"] == "deadbeef"
            assert payload["source_refs"]["focused_candidate_schedule_yml"] == "runs/campaigns/npu/demo_campaign/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml"
            assert payload["source_refs"]["focused_candidate_descriptors_bin"] == "runs/campaigns/npu/demo_campaign/artifacts/mapper/fp16_nm1_demo/demo_model/descriptors.bin"

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
            evaluation_record = payload["evaluation_record"]
            assert assessment["proposal_id"] == "prop_l2_demo_v1"
            assert assessment["outcome"] == "no_measurable_change"
            assert evaluation_record["evaluation_mode"] == "paired_comparison"
            assert evaluation_record["abstraction_layer"] == "full_architecture"
            assert evaluation_record["expectation_status"] == "unspecified"
            assert assessment["matched_row_count"] == 1
            assert assessment["matched_rows"][0]["arch_id"] == "fp16_nm1_demo"
            assert payload["source_refs"]["baseline_summary_csv"] == "runs/campaigns/npu/baseline_campaign/summary.csv"
            assert payload["source_refs"]["baseline_report_md"] == "runs/campaigns/npu/baseline_campaign/report.md"


def test_consume_l2_result_measurement_only_omits_proposal_assessment() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_demo_v1",
                        "kind": "architecture",
                        "title": "Demo measurement-only",
                        "direct_comparison": {
                            "primary_question": "Record the metric for this architecture point.",
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_measurement_only",
                campaign_dir_rel="runs/campaigns/npu/measurement_only_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "measurement_only"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "measurement_only",
                "expected_direction": "unknown",
                "expected_reason": "This item only records the metric reference point.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "full_architecture",
            }
            work_item.task_request.request_payload = payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assert decision_payload["proposal_assessment"] is None
            assert decision_payload["evaluation_record"]["evaluation_mode"] == "measurement_only"
            assert decision_payload["evaluation_record"]["abstraction_layer"] == "full_architecture"
            assert decision_payload["evaluation_record"]["expectation_status"] == "not_applicable"


def test_consume_l2_result_broad_ranking_does_not_require_baseline_refs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_demo_v1",
                        "kind": "architecture",
                        "title": "Demo broad ranking",
                        "direct_comparison": {
                            "primary_question": "Which current architecture point ranks best?",
                        },
                        "baseline_refs": [],
                    },
                    indent=2,
                )
                + "\n",
            )
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_broad_ranking",
                campaign_dir_rel="runs/campaigns/npu/broad_ranking_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "ranking"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "broad_ranking",
                "expected_direction": "unknown",
                "expected_reason": "This item ranks current architecture points without a paired baseline.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "full_architecture",
            }
            work_item.task_request.request_payload = payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            evaluation_record = decision_payload["evaluation_record"]
            assert assessment["evaluation_mode"] == "broad_ranking"
            assert assessment["comparison_role"] == "ranking"
            assert assessment["outcome"] == "ranking_recorded"
            assert assessment["baseline_ref"] is None
            assert evaluation_record["evaluation_mode"] == "broad_ranking"
            assert evaluation_record["comparison_role"] == "ranking"
            assert evaluation_record["abstraction_layer"] == "full_architecture"
            assert "baseline comparison is not required" in evaluation_record["summary"]


def test_consume_l2_result_frontier_ranking_does_not_require_baseline_refs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_demo_v1",
                        "kind": "architecture",
                        "title": "Demo frontier ranking",
                        "prior_art": ["docs/proposals/older/analysis_report.md"],
                    },
                    indent=2,
                )
                + "\n",
            )
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_frontier_ranking",
                campaign_dir_rel="runs/campaigns/npu/frontier_ranking_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "ranking"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "frontier_detail",
                "expected_direction": "iterate",
                "expected_reason": "This item records frontier details without a paired baseline.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "llm_practical_scale",
            }
            work_item.task_request.request_payload = payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            assert assessment["evaluation_mode"] == "frontier_detail"
            assert assessment["comparison_role"] == "ranking"
            assert assessment["outcome"] == "ranking_recorded"
            assert "baseline comparison is not required" in assessment["summary"]


def test_consume_l2_result_frontier_decoder_quality_uses_decoder_json_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_decoder_quality_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_decoder_quality_v1",
                        "kind": "architecture",
                        "title": "Decoder trained quality",
                        "direct_comparison": {
                            "primary_question": "Does the decoder recovery remain exact-safe?"
                        },
                        "baseline_refs": [
                            "runs/datasets/llm_decoder_eval_tiny_v1/decoder_bf16_pwl_recovery.json"
                        ],
                    },
                    indent=2,
                )
                + "\n",
            )
            evidence_rel = "runs/datasets/llm_decoder_eval_trained_tiny_v1/decoder_trained_tiny_quality__l2_decoder_quality.json"
            report_rel = "runs/datasets/llm_decoder_eval_trained_tiny_v1/decoder_trained_tiny_quality__l2_decoder_quality.md"
            _write(
                repo_root / evidence_rel,
                json.dumps(
                    {
                        "version": 0.1,
                        "baseline": {
                            "template": "grid_approx_pwl_bf16_path",
                            "next_token_matches": 23,
                            "sample_count": 24,
                            "next_token_mismatch_sample_ids": ["trained_color_sky"],
                        },
                        "recovery": {
                            "template": "grid_approx_pwl_bf16_path_logit_tiebreak",
                            "next_token_matches": 24,
                            "sample_count": 24,
                            "next_token_mismatch_sample_ids": [],
                        },
                        "diagnosis": {
                            "decision": "tie_break_recovery_sufficient",
                            "exact_safe_after_recovery": True,
                            "recovered_count": 1,
                            "regression_count": 0,
                            "recommended_next_step": "scale to a larger trained checkpoint",
                        },
                        "recovered_sample_ids": ["trained_color_sky"],
                        "regression_sample_ids": [],
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(repo_root / report_rel, "# decoder quality\n")
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_decoder_quality",
                campaign_dir_rel="runs/campaigns/npu/decoder_quality_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_decoder_quality_v1",
                comparison={"role": "ranking"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "frontier_detail",
                "expected_direction": "iterate",
                "expected_reason": "Use decoder quality before a larger trained checkpoint.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "decoder_trained_tiny_quality",
            }
            work_item.task_request.request_payload = payload
            work_item.input_manifest = {
                "decoder_contract": {
                    "dataset_manifest": "runs/datasets/llm_decoder_eval_trained_tiny_v1/manifest.json",
                    "quality_out": "runs/datasets/llm_decoder_eval_trained_tiny_v1/decoder_quality_compare__l2_decoder_quality.json",
                    "candidate_sweep_out": "runs/datasets/llm_decoder_eval_trained_tiny_v1/decoder_quality_sweep__l2_decoder_quality.json",
                    "trained_quality_out": evidence_rel,
                    "trained_quality_report": report_rel,
                }
            }
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            evaluation_record = decision_payload["evaluation_record"]
            assert assessment["evaluation_mode"] == "frontier_detail"
            assert assessment["comparison_role"] == "ranking"
            assert assessment["outcome"] == "tie_break_recovery_sufficient"
            assert assessment["decoder_evidence_ref"] == evidence_rel
            assert assessment["decoder_quality"]["diagnosis"]["exact_safe_after_recovery"] is True
            assert assessment["decoder_quality"]["recovery"]["next_token_matches"] == 24
            assert assessment["baseline_ref"] is None
            assert "Focused comparison baseline" not in assessment["summary"]
            assert evaluation_record["outcome"] == "tie_break_recovery_sufficient"
            assert decision_payload["source_refs"]["decoder_trained_quality_out"] == evidence_rel
            assert decision_payload["source_refs"]["decoder_trained_quality_report"] == report_rel
            assert "baseline_summary_csv" not in decision_payload["source_refs"]


def test_consume_l2_result_frontier_attention_kv_uses_decoder_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_attention_kv_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_attention_kv_v1",
                        "kind": "architecture",
                        "title": "Attention KV memory bottleneck",
                        "direct_comparison": {
                            "primary_question": "Which decoder attention substage dominates?"
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            evidence_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.json"
            )
            report_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.md"
            )
            _write(
                repo_root / evidence_rel,
                json.dumps(
                    {
                        "version": 0.1,
                        "diagnosis": {
                            "decision": "attention_kv_bottleneck_recorded",
                            "recommended_next_step": "measure KV memory hierarchy",
                        },
                        "sweep_summary": {
                            "generated_rows": 7200,
                            "compact_rows": 240,
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(repo_root / report_rel, "# attention kv\n")
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_attention_kv",
                campaign_dir_rel="runs/campaigns/npu/attention_kv_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_attention_kv_v1",
                comparison={"role": "ranking"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "frontier_detail",
                "expected_direction": "iterate",
                "expected_reason": "Use attention/KV bottleneck evidence for next architecture selection.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "decoder_attention_kv_memory",
            }
            work_item.task_request.request_payload = payload
            work_item.input_manifest = {
                "decoder_contract": {
                    "attention_kv_memory_out": evidence_rel,
                    "attention_kv_memory_report": report_rel,
                }
            }
            work_item.expected_outputs = [*(work_item.expected_outputs or []), evidence_rel, report_rel]
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            assert assessment["outcome"] == "attention_kv_bottleneck_recorded"
            assert assessment["decoder_evidence_ref"] == evidence_rel
            assert decision_payload["evaluation_record"]["abstraction_layer"] == "decoder_attention_kv_memory"
            assert decision_payload["source_refs"]["decoder_attention_kv_memory_out"] == evidence_rel
            assert decision_payload["source_refs"]["decoder_attention_kv_memory_report"] == report_rel


def test_consume_l2_result_frontier_synthesis_prefers_synthesis_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "proposals" / "prop_l2_decoder_frontier_synthesis_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_decoder_frontier_synthesis_v1",
                        "kind": "architecture",
                        "title": "Decoder frontier synthesis",
                        "direct_comparison": {
                            "primary_question": "Which measured decoder components dominate the frontier?"
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            synthesis_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_frontier_synthesis__l2_decoder_frontier_synthesis_v1.json"
            )
            synthesis_report_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_frontier_synthesis__l2_decoder_frontier_synthesis_v1.md"
            )
            attention_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_memory__l2_decoder_frontier_synthesis_v1.json"
            )
            attention_report_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_memory__l2_decoder_frontier_synthesis_v1.md"
            )
            _write(
                repo_root / synthesis_rel,
                json.dumps(
                    {
                        "version": 0.1,
                        "model": "llm_decoder_frontier_synthesis_v1",
                        "diagnosis": {
                            "decision": "decoder_frontier_synthesis_recorded",
                            "recommended_next_step": "measure producer/ranker RTL",
                        },
                        "dominant_component_counts": {
                            "output_projection_producer_ranker": 8,
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(repo_root / synthesis_report_rel, "# decoder frontier synthesis\n")
            _write(
                repo_root / attention_rel,
                json.dumps(
                    {
                        "version": 0.1,
                        "diagnosis": {
                            "decision": "attention_kv_bottleneck_recorded",
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(repo_root / attention_report_rel, "# attention kv\n")
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_decoder_frontier_synthesis_v1",
                campaign_dir_rel="runs/campaigns/npu/decoder_frontier_synthesis_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/proposals/prop_l2_decoder_frontier_synthesis_v1",
                comparison={"role": "ranking"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "frontier_detail",
                "expected_direction": "iterate",
                "expected_reason": "Use measured decoder frontier synthesis evidence for next architecture selection.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "decoder_frontier_synthesis",
            }
            work_item.task_request.request_payload = payload
            work_item.input_manifest = {
                "decoder_contract": {
                    "decoder_frontier_synthesis_out": synthesis_rel,
                    "decoder_frontier_synthesis_report": synthesis_report_rel,
                    "attention_kv_memory_out": attention_rel,
                    "attention_kv_memory_report": attention_report_rel,
                }
            }
            work_item.expected_outputs = [
                *(work_item.expected_outputs or []),
                synthesis_rel,
                synthesis_report_rel,
                attention_rel,
                attention_report_rel,
            ]
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            assert assessment["outcome"] == "decoder_frontier_synthesis_recorded"
            assert assessment["decoder_evidence_ref"] == synthesis_rel
            assert decision_payload["evaluation_record"]["abstraction_layer"] == "decoder_frontier_synthesis"
            assert decision_payload["source_refs"]["decoder_frontier_synthesis_out"] == synthesis_rel
            assert decision_payload["source_refs"]["decoder_frontier_synthesis_report"] == synthesis_report_rel
            assert decision_payload["source_refs"].get("decoder_attention_kv_memory_out") is None


def test_consume_l2_result_prefers_producer_synth_boundary_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            proposal_dir = (
                repo_root
                / "docs"
                / "proposals"
                / "prop_l2_decoder_output_projection_producer_synth_boundary_v1"
            )
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_decoder_output_projection_producer_synth_boundary_v1",
                        "kind": "architecture",
                        "title": "Decoder producer synthesis boundary",
                        "direct_comparison": {
                            "primary_question": "Where does producer synthesis become nonviable?"
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
            evidence_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_synth_boundary__"
                "l2_decoder_output_projection_producer_synth_boundary_v1.json"
            )
            report_rel = (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_synth_boundary__"
                "l2_decoder_output_projection_producer_synth_boundary_v1.md"
            )
            _write(
                repo_root / evidence_rel,
                json.dumps(
                    {
                        "version": 0.1,
                        "model": "decoder_output_projection_producer_synth_boundary_v1",
                        "diagnosis": {
                            "decision": "producer_synth_boundary_recorded",
                            "feasible_max_num_modules": 3,
                            "first_nonviable_num_modules": 4,
                            "recommended_next_step": "split the producer before full PnR",
                        },
                        "probe_rows": [
                            {"num_modules": 3, "status": "ok"},
                            {"num_modules": 4, "status": "stall_timeout"},
                        ],
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(repo_root / report_rel, "# decoder producer synthesis boundary\n")
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_decoder_output_projection_producer_synth_boundary_v1",
                campaign_dir_rel="runs/campaigns/npu/decoder_producer_synth_boundary_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,"
                    "critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,"
                    "throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm3_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_v1",
                comparison={"role": "producer_synth_boundary"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "frontier_detail",
                "expected_direction": "iterate",
                "expected_reason": "Record bounded producer synthesis frontier before deeper RTL jobs.",
            }
            payload["developer_loop"]["abstraction"] = {
                "layer": "decoder_output_projection_producer_synth_boundary",
            }
            work_item.task_request.request_payload = payload
            work_item.input_manifest = {
                "decoder_contract": {
                    "producer_synth_boundary_out": evidence_rel,
                    "producer_synth_boundary_report": report_rel,
                }
            }
            work_item.expected_outputs = [
                *(work_item.expected_outputs or []),
                evidence_rel,
                report_rel,
            ]
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = decision_payload["proposal_assessment"]
            assert assessment["outcome"] == "producer_synth_boundary_recorded"
            assert assessment["decoder_evidence_ref"] == evidence_rel
            assert decision_payload["evaluation_record"]["abstraction_layer"] == (
                "decoder_output_projection_producer_synth_boundary"
            )
            assert decision_payload["source_refs"]["decoder_producer_synth_boundary_out"] == evidence_rel
            assert decision_payload["source_refs"]["decoder_producer_synth_boundary_report"] == report_rel


def test_consume_l2_result_resolves_prior_art_report_as_baseline() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            baseline_dir = repo_root / "runs" / "campaigns" / "npu" / "prior_art_baseline"
            _write(
                baseline_dir / "summary.csv",
                (
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.50,0.20,5.5,0.18,1000,1.0\n"
                ),
            )
            _write(baseline_dir / "report.md", "# prior-art baseline\n")
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            _write(
                proposal_dir / "proposal.json",
                json.dumps(
                    {
                        "proposal_id": "prop_l2_demo_v1",
                        "kind": "architecture",
                        "title": "Demo focused comparison",
                        "direct_comparison": {
                            "primary_question": "Does the candidate improve the prior-art baseline?"
                        },
                        "prior_art": ["runs/campaigns/npu/prior_art_baseline/report.md"],
                    },
                    indent=2,
                )
                + "\n",
            )
            item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_prior_art_candidate",
                campaign_dir_rel="runs/campaigns/npu/prior_art_candidate",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.40,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
            )

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = payload["proposal_assessment"]
            assert assessment["baseline_ref"] == "runs/campaigns/npu/prior_art_baseline"
            assert assessment["outcome"] == "improved"
            assert payload["source_refs"]["baseline_summary_csv"] == "runs/campaigns/npu/prior_art_baseline/summary.csv"


def test_consume_l2_result_multimodel_measurement_exports_model_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, _run_key = _seed_multimodel_measurement_campaign(session, repo_root)

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=item_id))

            decision_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            focused_models = decision_payload["source_refs"]["focused_model_artifacts"]
            assert [entry["model_id"] for entry in focused_models] == ["linear_tail", "relu_tail"]
            assert focused_models[0]["schedule_yml"].endswith("/linear_tail/schedule.yml")
            assert focused_models[1]["schedule_yml"].endswith("/relu_tail/schedule.yml")
            assert focused_models[0]["perf_trace_json"].endswith("/linear_tail/trace.json")
            assert focused_models[1]["perf_trace_json"].endswith("/relu_tail/trace.json")


def test_consume_l2_result_marks_refreshed_baseline_without_proposal_judgment() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
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
                        "baseline_refs": ["runs/campaigns/npu/historical_baseline"],
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(
                repo_root / "runs" / "campaigns" / "npu" / "historical_baseline" / "summary.csv",
                (
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.3,0.1,5.5,0.18,1000,1.0\n"
                ),
            )
            baseline_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_refreshed_baseline",
                campaign_dir_rel="runs/campaigns/npu/refreshed_baseline_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.5,0.2,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "refreshed_baseline"},
            )
            work_item = session.query(WorkItem).filter_by(item_id=baseline_item_id).one()
            payload = copy.deepcopy(work_item.task_request.request_payload or {})
            payload["developer_loop"]["evaluation"] = {
                "mode": "baseline_refresh",
                "expected_direction": "worse_than_historical",
                "expected_reason": "The corrected contract should expose previously hidden terminal DMA cost.",
            }
            work_item.task_request.request_payload = payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=baseline_item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{baseline_item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = payload["proposal_assessment"]
            evaluation_record = payload["evaluation_record"]
            assert assessment["comparison_role"] == "refreshed_baseline"
            assert assessment["evaluation_mode"] == "baseline_refresh"
            assert assessment["outcome"] == "baseline_refreshed"
            assert "deferred until the paired candidate run is reviewed" in assessment["summary"]
            assert evaluation_record["expected_direction"] == "worse_than_historical"
            assert evaluation_record["expectation_status"] == "as_expected"
            assert payload["source_refs"]["baseline_summary_csv"] == "runs/campaigns/npu/historical_baseline/summary.csv"


def test_consume_l2_result_compares_candidate_against_paired_baseline_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
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
                        "baseline_refs": ["runs/campaigns/npu/historical_baseline"],
                    },
                    indent=2,
                )
                + "\n",
            )
            _write(
                repo_root / "runs" / "campaigns" / "npu" / "historical_baseline" / "summary.csv",
                (
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.3,0.1,5.5,0.18,1000,1.0\n"
                ),
            )
            baseline_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_refreshed_baseline",
                campaign_dir_rel="runs/campaigns/npu/refreshed_baseline_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.5,0.2,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "refreshed_baseline"},
            )
            baseline_work_item = session.query(WorkItem).filter_by(item_id=baseline_item_id).one()
            baseline_payload = copy.deepcopy(baseline_work_item.task_request.request_payload or {})
            baseline_payload["developer_loop"]["evaluation"] = {
                "mode": "baseline_refresh",
                "expected_direction": "worse_than_historical",
                "expected_reason": "The corrected contract should expose previously hidden terminal DMA cost.",
            }
            baseline_work_item.task_request.request_payload = baseline_payload
            session.commit()
            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=baseline_item_id))

            candidate_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_candidate",
                campaign_dir_rel="runs/campaigns/npu/candidate_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "candidate", "paired_baseline_item_id": baseline_item_id},
            )
            candidate_work_item = session.query(WorkItem).filter_by(item_id=candidate_item_id).one()
            candidate_payload = copy.deepcopy(candidate_work_item.task_request.request_payload or {})
            candidate_payload["developer_loop"]["evaluation"] = {
                "mode": "paired_comparison",
                "expected_direction": "better_than_historical",
                "expected_reason": "The candidate should beat the refreshed baseline.",
            }
            candidate_work_item.task_request.request_payload = candidate_payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=candidate_item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{candidate_item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = payload["proposal_assessment"]
            evaluation_record = payload["evaluation_record"]
            assert assessment["comparison_role"] == "candidate"
            assert assessment["evaluation_mode"] == "paired_comparison"
            assert assessment["baseline_item_id"] == baseline_item_id
            assert assessment["baseline_ref"] == "runs/campaigns/npu/refreshed_baseline_campaign"
            assert assessment["outcome"] == "improved"
            assert evaluation_record["expectation_status"] == "as_expected"
            assert assessment["matched_rows"][0]["model_id"] is None
            assert assessment["matched_rows"][0]["metrics"]["latency_ms_mean"]["baseline"] == 0.5
            assert assessment["matched_rows"][0]["metrics"]["latency_ms_mean"]["candidate"] == 0.4
            assert payload["source_refs"]["baseline_summary_csv"] == "runs/campaigns/npu/refreshed_baseline_campaign/summary.csv"


def test_consume_l2_result_candidate_falls_back_to_developer_loop_when_proposal_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            baseline_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_missing_proposal_baseline",
                campaign_dir_rel="runs/campaigns/npu/missing_proposal_baseline_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.5,0.2,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_missing_v1/proposal.json",
                comparison={"role": "measurement_only"},
            )
            baseline_work_item = session.query(WorkItem).filter_by(item_id=baseline_item_id).one()
            baseline_payload = copy.deepcopy(baseline_work_item.task_request.request_payload or {})
            baseline_payload["developer_loop"]["evaluation"] = {
                "mode": "measurement_only",
                "expected_direction": "unknown",
                "expected_reason": "Baseline metric capture only.",
            }
            baseline_work_item.task_request.request_payload = baseline_payload
            session.commit()

            candidate_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_missing_proposal_candidate",
                campaign_dir_rel="runs/campaigns/npu/missing_proposal_candidate_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_missing_v1/proposal.json",
                comparison={"role": "candidate", "paired_baseline_item_id": baseline_item_id},
            )
            candidate_work_item = session.query(WorkItem).filter_by(item_id=candidate_item_id).one()
            candidate_payload = copy.deepcopy(candidate_work_item.task_request.request_payload or {})
            candidate_payload["developer_loop"]["evaluation"] = {
                "mode": "paired_comparison",
                "expected_direction": "better_than_historical",
                "expected_reason": "The candidate should beat the persisted baseline even if proposal.json is unavailable.",
            }
            candidate_payload["developer_loop"]["abstraction"] = {
                "layer": "full_architecture",
            }
            candidate_work_item.task_request.request_payload = candidate_payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=candidate_item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{candidate_item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assessment = payload["proposal_assessment"]
            evaluation_record = payload["evaluation_record"]
            assert assessment["proposal_id"] == "prop_l2_missing_v1"
            assert assessment["baseline_item_id"] == baseline_item_id
            assert assessment["outcome"] == "improved"
            assert evaluation_record["proposal_id"] == "prop_l2_missing_v1"
            assert evaluation_record["evaluation_mode"] == "paired_comparison"
            assert evaluation_record["comparison_role"] == "candidate"
            assert evaluation_record["abstraction_layer"] == "full_architecture"
            assert evaluation_record["expectation_status"] == "as_expected"
            assert payload["source_refs"]["baseline_summary_csv"] == (
                "runs/campaigns/npu/missing_proposal_baseline_campaign/summary.csv"
            )


def test_consume_l2_result_paired_comparison_recovers_baseline_and_abstraction_from_evaluation_requests() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
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
                },
                indent=2,
            )
            + "\n",
        )
        _write(
            proposal_dir / "evaluation_requests.json",
            json.dumps(
                {
                    "proposal_id": "prop_l2_demo_v1",
                    "requested_items": [
                        {
                            "item_id": "l2_demo_measurement_r1",
                            "task_type": "l2_campaign",
                            "evaluation_mode": "measurement_only",
                            "abstraction_layer": "full_architecture",
                            "status": "merged",
                        },
                        {
                            "item_id": "l2_demo_fused_r1",
                            "task_type": "l2_campaign",
                            "evaluation_mode": "paired_comparison",
                            "abstraction_layer": "full_architecture",
                            "paired_baseline_item_id": "l2_demo_measurement_r1",
                            "status": "not_queued",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
        )

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            baseline_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_demo_measurement_r1",
                campaign_dir_rel="runs/campaigns/npu/demo_baseline_refresh",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.50,0.20,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
            )
            baseline_work_item = session.query(WorkItem).filter_by(item_id=baseline_item_id).one()
            baseline_work_item.state = WorkItemState.MERGED
            session.commit()
            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=baseline_item_id))
            session.query(Run).filter(Run.work_item_id == baseline_work_item.id).delete()
            session.delete(baseline_work_item)
            session.commit()

            candidate_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_demo_fused_r1",
                campaign_dir_rel="runs/campaigns/npu/demo_candidate_refresh",
                summary_rows=(
                    "scope,arch_id,macro_mode,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "aggregate,fp16_nm1_demo,flat_nomacro,1,0.40,0.15,5.5,0.18,950,1.1\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
            )
            candidate_work_item = session.query(WorkItem).filter_by(item_id=candidate_item_id).one()
            candidate_work_item.task_request.request_payload["developer_loop"] = {
                "proposal_id": "prop_l2_demo_v1",
                "proposal_path": "docs/developer_loop/prop_l2_demo_v1",
            }
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=candidate_item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{candidate_item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assert payload["proposal_assessment"]["baseline_item_id"] == baseline_item_id
            assert payload["proposal_assessment"]["outcome"] == "improved"
            assert payload["evaluation_record"]["abstraction_layer"] == "full_architecture"
            assert payload["evaluation_record"]["comparison_role"] == "candidate"


def test_consume_l2_result_paired_comparison_matches_model_rows_by_model_id() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            proposal_dir.mkdir(parents=True, exist_ok=True)
            (proposal_dir / "proposal.json").write_text(
                json.dumps(
                    {
                        "proposal_id": "prop_l2_demo_v1",
                        "title": "Layer2 review demo",
                        "kind": "architecture",
                        "direct_comparison": {
                            "primary_question": "Does the candidate improve the per-model baseline?"
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            baseline_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_model_baseline",
                campaign_dir_rel="runs/campaigns/npu/model_baseline_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,model_id,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "model,fp16_nm1_demo,flat_nomacro,model_a,1,0.5,0.20,5.5,0.18,1000,1.0\n"
                    "model,fp16_nm1_demo,flat_nomacro,model_b,1,0.8,0.30,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "measurement_only"},
            )
            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=baseline_item_id))

            candidate_item_id = _seed_campaign_work_item(
                session,
                repo_root,
                item_id="l2_model_candidate",
                campaign_dir_rel="runs/campaigns/npu/model_candidate_campaign",
                summary_rows=(
                    "scope,arch_id,macro_mode,model_id,objective_rank,latency_ms_mean,energy_mj_mean,critical_path_ns_mean,total_power_mw_mean,flow_elapsed_s_mean,throughput_infer_per_s_mean\n"
                    "model,fp16_nm1_demo,flat_nomacro,model_a,1,0.4,0.15,5.5,0.18,1000,1.0\n"
                    "model,fp16_nm1_demo,flat_nomacro,model_b,1,0.7,0.25,5.5,0.18,1000,1.0\n"
                ),
                proposal_path="docs/developer_loop/prop_l2_demo_v1",
                comparison={"role": "candidate", "paired_baseline_item_id": baseline_item_id},
            )
            candidate_work_item = session.query(WorkItem).filter_by(item_id=candidate_item_id).one()
            candidate_payload = copy.deepcopy(candidate_work_item.task_request.request_payload or {})
            candidate_payload["developer_loop"]["evaluation"] = {
                "mode": "paired_comparison",
                "expected_direction": "better_than_historical",
                "expected_reason": "The candidate should improve both model rows.",
            }
            candidate_work_item.task_request.request_payload = candidate_payload
            session.commit()

            consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=candidate_item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l2_decisions" / f"{candidate_item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            matched_rows = payload["proposal_assessment"]["matched_rows"]
            assert len(matched_rows) == 2
            assert matched_rows[0]["model_id"] == "model_a"
            assert matched_rows[0]["metrics"]["latency_ms_mean"]["baseline"] == 0.5
            assert matched_rows[0]["metrics"]["latency_ms_mean"]["candidate"] == 0.4
            assert matched_rows[1]["model_id"] == "model_b"
            assert matched_rows[1]["metrics"]["latency_ms_mean"]["baseline"] == 0.8
            assert matched_rows[1]["metrics"]["latency_ms_mean"]["candidate"] == 0.7
