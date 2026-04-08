"""Layer 1 result consumer coverage."""

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
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result


def _write_metrics(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "platform",
        "status",
        "param_hash",
        "tag",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "result_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(headers) + "\n")
        for row in rows:
            handle.write(",".join(row.get(key, "") for key in headers) + "\n")


def _seed_succeeded_l1_sweep(session: Session, repo_root: Path) -> tuple[str, str]:
    metrics_a = "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv"
    metrics_b = "runs/designs/activations/softmax_rowwise_int8_r8_acc20_wrapper/metrics.csv"
    _write_metrics(
        repo_root / metrics_a,
        [
            {
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "slow0001",
                "tag": "tag_slow",
                "critical_path_ns": "14.2",
                "die_area": "41000",
                "total_power_mw": "0.25",
                "result_path": "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/slow0001/result.json",
            },
            {
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "fast0001",
                "tag": "tag_fast",
                "critical_path_ns": "12.0",
                "die_area": "30000",
                "total_power_mw": "0.18",
                "result_path": "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json",
            },
        ],
    )
    _write_metrics(
        repo_root / metrics_b,
        [
            {
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "acc20001",
                "tag": "tag_acc20",
                "critical_path_ns": "17.1",
                "die_area": "80000",
                "total_power_mw": "0.81",
                "result_path": "runs/designs/activations/softmax_rowwise_int8_r8_acc20_wrapper/work/acc20001/result.json",
            }
        ],
    )

    task_request = TaskRequest(
        request_key="l1_sweep:test_softmax",
        source="test",
        requested_by="@tester",
        title="Layer1 softmax test",
        description="test l1 result consumer",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={
            "item_id": "l1_test_softmax",
            "layer": "layer1",
            "flow": "openroad",
        },
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_test_softmax",
        task_request_id=task_request.id,
        item_id="l1_test_softmax",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="config",
        input_manifest={
            "configs": [
                "examples/config_softmax_rowwise_int8.json",
                "examples/config_softmax_rowwise_int8_r8_acc20.json",
            ],
            "sweeps": ["runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json"],
        },
        command_manifest=[],
        expected_outputs=[metrics_a, metrics_b, "runs/index.csv"],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l1_test_softmax_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="2/2 commands succeeded",
        result_payload={"queue_result": {"status": "ok"}},
    )
    session.add(run)
    session.commit()
    return work_item.item_id, run.run_key


def test_consume_l1_result_writes_promotion_proposal() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, run_key = _seed_succeeded_l1_sweep(session, repo_root)
            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                ),
            )

            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.proposal_count == 2
            assert result.work_item_state == "artifact_sync"

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 2
            assert payload["evaluation_record"]["evaluation_mode"] == "measurement_only"
            assert payload["evaluation_record"]["physical_metrics_present"] is True
            assert payload["evaluation_record"]["abstraction_layer"] == "circuit_block"
            assert payload["source_refs"]["summary_stats_json"].endswith(f"/{item_id}/summary_stats.json")
            assert payload["source_refs"]["trial_table_csv"].endswith(f"/{item_id}/trial_table.csv")
            assert payload["proposals"][0]["metrics_ref"]["param_hash"] == "fast0001"
            assert (
                payload["proposals"][0]["metrics_ref"]["result_path"]
                == "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json"
            )
            assert payload["proposals"][1]["metrics_ref"]["param_hash"] == "acc20001"

            artifact = session.query(Artifact).filter_by(kind="promotion_proposal").one()
            assert artifact.path == f"control_plane/shadow_exports/l1_promotions/{item_id}.json"


def test_consume_l1_result_allows_explicit_target_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, _run_key = _seed_succeeded_l1_sweep(session, repo_root)
            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    target_path="runs/proposals/l1_test_softmax.json",
                ),
            )
            assert result.target_path.endswith("runs/proposals/l1_test_softmax.json")
            assert (repo_root / "runs" / "proposals" / "l1_test_softmax.json").exists()


def test_consume_l1_result_falls_back_to_proposal_abstraction_layer() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l1_npu_nm1_relu6_vec_enable_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.json").write_text(
            json.dumps({"proposal_id": "prop_l1_npu_nm1_relu6_vec_enable_v1", "abstraction_layer": "architecture_block"}, indent=2) + "\n",
            encoding="utf-8",
        )

        with Session(engine) as session:
            item_id, _run_key = _seed_succeeded_l1_sweep(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = dict(work_item.task_request.request_payload or {})
            payload["developer_loop"] = {
                "proposal_id": "prop_l1_npu_nm1_relu6_vec_enable_v1",
                "proposal_path": "docs/developer_loop/prop_l1_npu_nm1_relu6_vec_enable_v1",
                "evaluation": {"mode": "measurement_only"},
            }
            work_item.task_request.request_payload = payload
            session.flush()

            consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                ),
            )

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{item_id}.json"
            rendered = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert rendered["evaluation_record"]["abstraction_layer"] == "architecture_block"




def test_consume_l1_result_accepts_synth_only_metrics_row() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_path = "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/metrics.csv"
        metrics_file = repo_root / metrics_path
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(
            "\n".join(
                [
                    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,flow_elapsed_seconds,stage_elapsed_seconds,params_json,result_path,work_result_json,synth_script_path,synth_script_sha1",
                    'npu_fp16_cpp_nm1_sigmoidcmp,nangate45,bbc47ba9eb29,6f70a40e,npu_fp16_nm1_sigmoidcmp_hier_firstpass,ok,,,,0.52,0.52,"{""CLOCK_PERIOD"": 12.0, ""TAG"": ""npu_fp16_nm1_sigmoidcmp_hier_firstpass""}",/orfs/flow/results/nangate45/npu_fp16_cpp_nm1_sigmoidcmp/nm1_sigmoidcmp_hier_firstpass/1_1_yosys_canonicalize.rtlil,runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/work/6f70a40e/result.json,,',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_sigmoid_prefilter",
                source="test",
                requested_by="@tester",
                title="Layer1 sigmoid prefilter test",
                description="test synth-only l1 result consumer",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_sigmoid_prefilter",
                    "layer": "layer1",
                    "flow": "openroad",
                    "developer_loop": {"evaluation": {"mode": "synth_prefilter"}},
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_sigmoid_prefilter",
                task_request_id=task_request.id,
                item_id="l1_test_sigmoid_prefilter",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={
                    "configs": [
                        "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/config_nm1_sigmoid.json",
                    ],
                    "sweeps": [
                        "runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/sweep_hier_firstpass.json",
                    ],
                },
                command_manifest=[],
                expected_outputs=[metrics_path, "runs/index.csv"],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            run = Run(
                run_key="l1_test_sigmoid_prefilter_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="5/5 commands succeeded",
                result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_path}:2"]}},
            )
            session.add(run)
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )

            assert result.item_id == work_item.item_id
            assert result.proposal_count == 1

            proposal_path = (
                repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            )
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 1
            assert payload["evaluation_record"]["evaluation_mode"] == "synth_prefilter"
            assert payload["evaluation_record"]["physical_metrics_present"] is False
            assert payload["proposals"][0]["metrics_ref"]["param_hash"] == "6f70a40e"
            assert payload["proposals"][0]["metrics_ref"]["result_kind"] == "synth_prefilter"
            assert payload["proposals"][0]["selection_reason"] == "first status=ok synth-stage prefilter row; no physical metrics are recorded yet"
            assert "metric_summary" not in payload["proposals"][0]


def test_consume_l1_result_writes_trial_aggregate_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_trial_1 = "runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper/metrics.csv"
        metrics_trial_2 = "runs/designs/activations/trials/trial_002/softmax_rowwise_int8_r4_wrapper/metrics.csv"
        _write_metrics(
            repo_root / metrics_trial_1,
            [{
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "trial1",
                "tag": "trial_1",
                "critical_path_ns": "12.0",
                "die_area": "30000",
                "total_power_mw": "0.18",
                "result_path": "runs/trials/trial_001/result.json",
            }],
        )
        _write_metrics(
            repo_root / metrics_trial_2,
            [{
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "trial2",
                "tag": "trial_2",
                "critical_path_ns": "11.0",
                "die_area": "29000",
                "total_power_mw": "0.17",
                "result_path": "runs/trials/trial_002/result.json",
            }],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_trial_aggregate",
                source="test",
                requested_by="@tester",
                title="Layer1 trial aggregate test",
                description="test l1 trial aggregation",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_trial_aggregate",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_trial_aggregate",
                task_request_id=task_request.id,
                item_id="l1_test_trial_aggregate",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_trial_1, metrics_trial_2, "runs/index.csv"],
                acceptance_rules=[],
                source_commit="deadbeef",
                trial_policy_json={"trial_count": 3, "seed_start": 3, "stop_after_failures": 3},
            )
            session.add(work_item)
            session.flush()

            run_1 = Run(
                run_key="l1_test_trial_aggregate_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=3,
                result_summary="trial 1 succeeded",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 3},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_1}:2"]},
                },
            )
            run_2 = Run(
                run_key="l1_test_trial_aggregate_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=4,
                result_summary="trial 2 succeeded",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 4},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_2}:2"]},
                },
            )
            run_3 = Run(
                run_key="l1_test_trial_aggregate_run_3",
                work_item_id=work_item.id,
                attempt=3,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=3,
                seed=5,
                result_summary="trial 3 failed",
                result_payload={
                    "trial": {"trial_index": 3, "seed": 5},
                    "failure_classification": {"category": "timing_unmet", "stage": "route", "signature": "slack<0"},
                },
                failure_category="timing_unmet",
                failure_stage="route",
                failure_signature="slack<0",
            )
            session.add_all([run_1, run_2, run_3])
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )

            assert result.item_id == work_item.item_id
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["trial_summary"]["completed_trials"] == 3
            assert payload["trial_summary"]["success_count"] == 2
            assert payload["trial_summary"]["failure_count"] == 1
            assert payload["trial_summary"]["metrics"]["critical_path_ns"]["best"] == 11.0
            assert payload["evaluation_record"]["abstraction_layer"] == "circuit_block"
            assert payload["source_refs"]["trial_metrics_csvs"] == [metrics_trial_1, metrics_trial_2]
            assert payload["source_refs"]["summary_stats_json"].endswith(f"/{work_item.item_id}/summary_stats.json")

            summary_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "summary_stats.json"
            failure_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "failure_stats.json"
            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            failure_stats = json.loads(failure_path.read_text(encoding="utf-8"))
            trial_table = trial_table_path.read_text(encoding="utf-8")
            assert summary["success_rate"] == 2 / 3
            assert failure_stats["by_category"] == {"timing_unmet": 1}
            assert failure_stats["by_stage"] == {"route": 1}
            assert "trial_index,seed,status" in trial_table
            assert "l1_test_trial_aggregate_run_3" in trial_table

            artifact_kinds = {artifact.kind for artifact in session.query(Artifact).all()}
            assert {"promotion_proposal", "summary_stats", "failure_stats", "trial_table"} <= artifact_kinds


def test_consume_l1_result_counts_requeued_failures_in_trial_history() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_trial_1 = "runs/designs/activations/terminal_hardswish_int8_pwl_seedvariance_wrapper/trials/trial_001/terminal_hardswish_int8_pwl_seedvariance_wrapper/metrics.csv"
        metrics_trial_2 = "runs/designs/activations/terminal_hardswish_int8_pwl_seedvariance_wrapper/trials/trial_002/terminal_hardswish_int8_pwl_seedvariance_wrapper/metrics.csv"
        for metrics_path, cp in ((metrics_trial_1, 0.1940), (metrics_trial_2, 0.1943)):
            target = repo_root / metrics_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "\n".join([
                    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path",
                    f'terminal_hardswish_int8_pwl_seedvariance_wrapper,nangate45,cfgseed,p{cp},tag_{cp},ok,{cp},25600.0,0.000325,"{{""CLOCK_PERIOD"": 4.0, ""FLOW_RANDOM_SEED"": 10, ""PLACE_DENSITY"": 0.35, ""TAG"": ""tag_{cp}""}}",runs/result_{cp}.json',
                ]) + "\n",
                encoding="utf-8",
            )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_requeued_failure_history",
                source="test",
                requested_by="@tester",
                title="Layer1 requeued failure history test",
                description="measure_seed_variance",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={"item_id": "l1_test_requeued_failure_history", "layer": "layer1", "flow": "openroad", "objective": "measure_seed_variance"},
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_requeued_failure_history",
                task_request_id=task_request.id,
                item_id="l1_test_requeued_failure_history",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_trial_1, metrics_trial_2],
                acceptance_rules=[],
                source_commit="deadbeef",
                trial_policy_json={"trial_count": 2, "seed_start": 101, "stop_after_failures": 2},
            )
            session.add(work_item)
            session.flush()

            run_1 = Run(
                run_key="l1_test_requeued_failure_history_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=101,
                result_summary="checkout failed",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 101},
                    "retry_decision": {"requeue": True},
                    "failure_classification": {"category": "checkout_error", "stage": "checkout", "signature": "git fetch origin"},
                },
                failure_category="checkout_error",
                failure_stage="checkout",
                failure_signature="git fetch origin",
            )
            run_2 = Run(
                run_key="l1_test_requeued_failure_history_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=101,
                result_summary="trial 1 succeeded",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 101},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_1}:2"]},
                },
            )
            run_3 = Run(
                run_key="l1_test_requeued_failure_history_run_3",
                work_item_id=work_item.id,
                attempt=3,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=102,
                result_summary="trial 2 succeeded",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 102},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_2}:2"]},
                },
            )
            session.add_all([run_1, run_2, run_3])
            session.commit()

            consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["trial_summary"]["completed_trials"] == 3
            assert payload["trial_summary"]["success_count"] == 2
            assert payload["trial_summary"]["failure_count"] == 1

            failure_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "failure_stats.json"
            failure_stats = json.loads(failure_path.read_text(encoding="utf-8"))
            assert failure_stats["by_category"] == {"checkout_error": 1}
            assert failure_stats["by_stage"] == {"checkout": 1}

            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            trial_table = trial_table_path.read_text(encoding="utf-8")
            assert "l1_test_requeued_failure_history_run_1,1,1,101,failed" in trial_table
            assert "checkout_error,checkout,git fetch origin" in trial_table
            assert metrics_trial_1 in trial_table
            assert metrics_trial_2 in trial_table


def test_consume_l1_result_groups_seed_variance_by_non_seed_params() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_trial_1 = "runs/designs/activations/terminal_sigmoid_int8_pwl_seedvariance2_wrapper/trials/trial_001/terminal_sigmoid_int8_pwl_seedvariance2_wrapper/metrics.csv"
        metrics_trial_2 = "runs/designs/activations/terminal_sigmoid_int8_pwl_seedvariance2_wrapper/trials/trial_002/terminal_sigmoid_int8_pwl_seedvariance2_wrapper/metrics.csv"
        trial_rows = {
            metrics_trial_1: [
                'design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path',
                'terminal_sigmoid_int8_pwl_seedvariance2_wrapper,nangate45,cfgseed,seed101a,tag_seed101a,ok,0.1906,25600.0,8.47e-05,"{""CLOCK_PERIOD"": 4.0, ""CORE_AREA"": ""20 20 140 140"", ""DIE_AREA"": ""0 0 160 160"", ""FLOW_RANDOM_SEED"": 101, ""PLACE_DENSITY"": 0.35, ""TAG"": ""tag_seed101a""}",runs/trial_001_a/result.json',
                'terminal_sigmoid_int8_pwl_seedvariance2_wrapper,nangate45,cfgseed,seed101b,tag_seed101b,ok,0.1910,25600.0,8.46e-05,"{""CLOCK_PERIOD"": 4.0, ""CORE_AREA"": ""20 20 140 140"", ""DIE_AREA"": ""0 0 160 160"", ""FLOW_RANDOM_SEED"": 101, ""PLACE_DENSITY"": 0.45, ""TAG"": ""tag_seed101b""}",runs/trial_001_b/result.json',
            ],
            metrics_trial_2: [
                'design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path',
                'terminal_sigmoid_int8_pwl_seedvariance2_wrapper,nangate45,cfgseed,seed102a,tag_seed102a,ok,0.1898,25600.0,8.45e-05,"{""CLOCK_PERIOD"": 4.0, ""CORE_AREA"": ""20 20 140 140"", ""DIE_AREA"": ""0 0 160 160"", ""FLOW_RANDOM_SEED"": 102, ""PLACE_DENSITY"": 0.35, ""TAG"": ""tag_seed102a""}",runs/trial_002_a/result.json',
                'terminal_sigmoid_int8_pwl_seedvariance2_wrapper,nangate45,cfgseed,seed102b,tag_seed102b,ok,0.1914,25600.0,8.46e-05,"{""CLOCK_PERIOD"": 4.0, ""CORE_AREA"": ""20 20 140 140"", ""DIE_AREA"": ""0 0 160 160"", ""FLOW_RANDOM_SEED"": 102, ""PLACE_DENSITY"": 0.45, ""TAG"": ""tag_seed102b""}",runs/trial_002_b/result.json',
            ],
        }
        for metrics_path, lines in trial_rows.items():
            target = repo_root / metrics_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_seed_variance",
                source="test",
                requested_by="@tester",
                title="Layer1 seed variance test",
                description="measure_seed_variance",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_seed_variance",
                    "layer": "layer1",
                    "flow": "openroad",
                    "objective": "measure_seed_variance",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_seed_variance",
                task_request_id=task_request.id,
                item_id="l1_test_seed_variance",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_trial_1, metrics_trial_2],
                acceptance_rules=[],
                source_commit="deadbeef",
                trial_policy_json={"trial_count": 2, "seed_start": 101, "stop_after_failures": 2},
            )
            session.add(work_item)
            session.flush()

            run_1 = Run(
                run_key="l1_test_seed_variance_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=101,
                result_summary="trial 1 succeeded",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 101},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_1}:2"]},
                },
            )
            run_2 = Run(
                run_key="l1_test_seed_variance_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=102,
                result_summary="trial 2 succeeded",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 102},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_trial_2}:2"]},
                },
            )
            session.add_all([run_1, run_2])
            session.commit()

            consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 1
            assert payload["trial_summary"]["completed_trials"] == 2
            assert payload["trial_summary"]["success_count"] == 2
            assert payload["trial_summary"]["failure_count"] == 0
            assert payload["trial_summary"]["comparison_mode"] == "same_non_seed_flow_params"
            assert payload["trial_summary"]["comparison_params"]["PLACE_DENSITY"] == 0.35
            assert payload["trial_summary"]["metrics"]["critical_path_ns"]["best"] == 0.1898
            assert payload["trial_summary"]["metrics"]["critical_path_ns"]["max"] == 0.1906
            assert abs(payload["trial_summary"]["metrics"]["critical_path_ns"]["range"] - 0.0008) < 1e-12
            assert payload["trial_summary"]["metrics"]["critical_path_ns"]["stddev"] > 0.0
            assert payload["proposals"][0]["metrics_ref"]["metrics_csv"] == metrics_trial_2

            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            trial_table = trial_table_path.read_text(encoding="utf-8")
            assert ",101,succeeded," in trial_table
            assert metrics_trial_1 in trial_table
            assert metrics_trial_2 in trial_table


def test_consume_l1_result_uses_run_trial_path_when_metrics_rows_are_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_trial_1 = "runs/designs/activations/terminal_hardswish_int8_pwl_seedvariance_wrapper/trials/trial_001/terminal_hardswish_int8_pwl_seedvariance_wrapper/metrics.csv"
        metrics_trial_2 = "runs/designs/activations/terminal_hardswish_int8_pwl_seedvariance_wrapper/trials/trial_002/terminal_hardswish_int8_pwl_seedvariance_wrapper/metrics.csv"
        for metrics_path, seed, cp in ((metrics_trial_1, 101, 0.1940), (metrics_trial_2, 102, 0.1943)):
            target = repo_root / metrics_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "\n".join([
                    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path",
                    f'terminal_hardswish_int8_pwl_seedvariance_wrapper,nangate45,cfgseed,p{seed},tag_{seed},ok,{cp},25600.0,0.000325,"{{""CLOCK_PERIOD"": 4.0, ""FLOW_RANDOM_SEED"": {seed}, ""PLACE_DENSITY"": 0.35, ""TAG"": ""tag_{seed}""}}",runs/result_{seed}.json',
                ]) + "\n",
                encoding="utf-8",
            )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_run_trial_path_fallback",
                source="test",
                requested_by="@tester",
                title="Layer1 run trial path fallback test",
                description="measure_seed_variance",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_run_trial_path_fallback",
                    "layer": "layer1",
                    "flow": "openroad",
                    "objective": "measure_seed_variance",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_run_trial_path_fallback",
                task_request_id=task_request.id,
                item_id="l1_test_run_trial_path_fallback",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_trial_1, metrics_trial_2],
                acceptance_rules=[],
                source_commit="deadbeef",
                trial_policy_json={"trial_count": 2, "seed_start": 101, "stop_after_failures": 2},
            )
            session.add(work_item)
            session.flush()

            run_1 = Run(
                run_key="l1_test_run_trial_path_fallback_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=101,
                result_summary="trial 1 succeeded",
                result_payload={"trial": {"trial_index": 1, "seed": 101}, "queue_result": {"status": "ok"}},
            )
            run_2 = Run(
                run_key="l1_test_run_trial_path_fallback_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=102,
                result_summary="trial 2 succeeded",
                result_payload={"trial": {"trial_index": 2, "seed": 102}, "queue_result": {"status": "ok"}},
            )
            session.add_all([run_1, run_2])
            session.commit()

            consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))

            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            trial_table_lines = trial_table_path.read_text(encoding="utf-8").strip().splitlines()
            assert metrics_trial_1 in trial_table_lines[1]
            assert metrics_trial_2 in trial_table_lines[2]
