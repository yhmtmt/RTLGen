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
