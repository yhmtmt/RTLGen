"""Layer 1 result consumer coverage."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import (
    Layer1ConsumeRequest,
    _terminal_run_has_metrics,
    consume_l1_result,
)


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
        "params_json",
        "result_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def test_terminal_run_metrics_require_captured_inline_artifact() -> None:
    run = SimpleNamespace(
        status=RunStatus.CANCELED,
        result_payload={"queue_result": {"metrics_rows": ["runs/designs/demo/metrics.csv:2"]}},
        artifacts=[],
    )

    assert _terminal_run_has_metrics(run) is False


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


def test_consume_l1_result_records_completed_timing_misses_as_boundary_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            item_id, _run_key = _seed_succeeded_l1_sweep(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            request_payload = dict(work_item.task_request.request_payload or {})
            request_payload["developer_loop"] = {"evaluation": {"mode": "frontier_followup"}}
            work_item.task_request.request_payload = request_payload
            session.flush()
            metrics_paths = [Path(path) for path in work_item.expected_outputs if str(path).endswith("metrics.csv")]
            for index, metrics_path in enumerate(metrics_paths):
                _write_metrics(
                    repo_root / metrics_path,
                    [{
                        "platform": "nangate45",
                        "status": "ok",
                        "param_hash": f"timingmiss{index}",
                        "tag": f"tag_timing_miss_{index}",
                        "critical_path_ns": str(42.0 + index),
                        "die_area": str(100000 + index),
                        "total_power_mw": str(7.0 + index),
                        "params_json": json.dumps({"CLOCK_PERIOD": 10}),
                        "result_path": f"runs/timing_miss_{index}/result.json",
                    }],
                )

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(repo_root=str(repo_root), item_id=item_id),
            )

            assert result.proposal_count == 0
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_assessment"]["outcome"] == "boundary_no_feasible_points"
            assert payload["evaluation_record"]["evaluation_mode"] == "frontier_followup"
            assert payload["evaluation_record"]["timing_feasible"] is False
            assert payload["evaluation_record"]["physical_metrics_present"] is True
            assert payload["evaluation_record"]["boundary_status_counts"] == {"timing_infeasible": 2}
            assert payload["boundary_evidence"]["row_count"] == 2
            first = payload["boundary_evidence"]["rows"][0]
            assert first["status"] == "timing_infeasible"
            assert first["flow_status"] == "ok"
            assert first["clock_period_ns"] == 10.0
            assert first["timing_slack_ns"] == -32.0


def test_consume_l1_result_records_failure_only_boundary_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_a = "runs/designs/activations/attention_kv_reducer_tree_p8_l16_v16_s16_a24_wrapper/metrics.csv"
        metrics_b = "runs/designs/activations/attention_kv_reducer_tree_p16_l16_v16_s16_a24_wrapper/metrics.csv"
        _write_metrics(
            repo_root / metrics_a,
            [
                {
                    "platform": "nangate45",
                    "status": "failed",
                    "param_hash": "d64a0205",
                    "tag": "attention_kv_reducer_tree_nangate45_macro_frontier_175641b8",
                    "result_path": "runs/designs/activations/attention_kv_reducer_tree_p8_l16_v16_s16_a24_wrapper/work/d64a0205/result.json",
                },
                {
                    "platform": "nangate45",
                    "status": "failed",
                    "param_hash": "63079636",
                    "tag": "attention_kv_reducer_tree_nangate45_macro_frontier_e0c384c0",
                    "result_path": "runs/designs/activations/attention_kv_reducer_tree_p8_l16_v16_s16_a24_wrapper/work/63079636/result.json",
                },
            ],
        )
        _write_metrics(
            repo_root / metrics_b,
            [
                {
                    "platform": "nangate45",
                    "status": "failed",
                    "param_hash": "d64a0205",
                    "tag": "attention_kv_reducer_tree_nangate45_macro_frontier_175641b8",
                    "result_path": "runs/designs/activations/attention_kv_reducer_tree_p16_l16_v16_s16_a24_wrapper/work/d64a0205/result.json",
                },
                {
                    "platform": "nangate45",
                    "status": "failed",
                    "param_hash": "63079636",
                    "tag": "attention_kv_reducer_tree_nangate45_macro_frontier_e0c384c0",
                    "result_path": "runs/designs/activations/attention_kv_reducer_tree_p16_l16_v16_s16_a24_wrapper/work/63079636/result.json",
                },
            ],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_boundary_failure_only",
                source="test",
                requested_by="@tester",
                title="Layer1 boundary failure-only test",
                description="boundary failure-only test",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_boundary_failure_only",
                    "layer": "layer1",
                    "flow": "openroad",
                    "abstraction_layer": "circuit_block",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_boundary_failure_only",
                task_request_id=task_request.id,
                item_id="l1_test_boundary_failure_only",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[metrics_a, metrics_b],
                acceptance_rules=[
                    "Each generated wrapper metrics.csv contains recorded rows with a status column; allow non-ok metrics such as flow_failed when the row is boundary evidence",
                ],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            run = Run(
                run_key="l1_test_boundary_failure_only_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="4/4 commands succeeded",
                result_payload={"queue_result": {"metrics_rows": [metrics_a, metrics_b]}},
            )
            session.add(run)
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id),
            )

            assert result.proposal_count == 0
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 0
            assert payload["proposals"] == []
            assert payload["proposal_assessment"]["outcome"] == "boundary_no_feasible_points"
            assert payload["evaluation_record"]["result_kind"] == "boundary_evidence"
            assert payload["evaluation_record"]["boundary_status_counts"] == {"failed": 4}
            assert payload["boundary_evidence"]["row_count"] == 4
            assert {row["metrics_csv"] for row in payload["boundary_evidence"]["rows"]} == {metrics_a, metrics_b}
            assert {row["param_hash"] for row in payload["boundary_evidence"]["rows"]} == {"d64a0205", "63079636"}

            artifact = session.query(Artifact).filter_by(kind="promotion_proposal").one()
            assert artifact.metadata_["proposal_count"] == 0


def test_consume_l1_result_accepts_failed_acceptance_run_with_mixed_metrics() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_ok = "runs/designs/noc/l1_endpoint_w1024_wrapper/metrics.csv"
        metrics_failed = "runs/designs/noc/l1_router_w2048_wrapper/metrics.csv"
        _write_metrics(
            repo_root / metrics_ok,
            [
                {
                    "platform": "nangate45",
                    "status": "ok",
                    "param_hash": "ok0001",
                    "tag": "wide_noc_frontier_a",
                    "critical_path_ns": "0.8028",
                    "die_area": "53031.18",
                    "total_power_mw": "0.0282",
                    "result_path": "runs/designs/noc/l1_endpoint_w1024_wrapper/work/ok0001/result.json",
                }
            ],
        )
        _write_metrics(
            repo_root / metrics_failed,
            [
                {
                    "platform": "nangate45",
                    "status": "failed",
                    "param_hash": "fail0001",
                    "tag": "wide_noc_frontier_a",
                    "result_path": "runs/designs/noc/l1_router_w2048_wrapper/work/fail0001/result.json",
                }
            ],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_mixed_acceptance_failed",
                source="test",
                requested_by="@tester",
                title="Layer1 mixed acceptance failed test",
                description="test failed acceptance run consumption",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_mixed_acceptance_failed",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_mixed_acceptance_failed",
                task_request_id=task_request.id,
                item_id="l1_test_mixed_acceptance_failed",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.FAILED,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[metrics_ok, metrics_failed],
                acceptance_rules=[
                    "Each generated wrapper metrics.csv contains at least one status=ok row for the queued sweep",
                ],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            run = Run(
                run_key="l1_test_mixed_acceptance_failed_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="4/4 commands succeeded",
                result_payload={
                    "queue_result": {
                        "status": "fail",
                        "metrics_rows": [metrics_ok, metrics_failed],
                    },
                    "failure_classification": {
                        "category": "validation_error",
                        "failed_command_name": "acceptance",
                    },
                },
            )
            session.add(run)
            session.flush()
            session.add_all(
                [
                    Artifact(
                        run_id=run.id,
                        kind="expected_output",
                        storage_mode="repo",
                        path=metrics_path,
                        metadata_={
                            "transport_policy": "inline_text_evidence",
                            "inline_utf8": (repo_root / metrics_path).read_text(encoding="utf-8"),
                        },
                    )
                    for metrics_path in (metrics_ok, metrics_failed)
                ]
            )
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(repo_root=str(repo_root), run_key=run.run_key),
            )

            assert result.proposal_count == 1
            proposal_path = (
                repo_root
                / "control_plane"
                / "shadow_exports"
                / "l1_promotions"
                / f"{work_item.item_id}.json"
            )
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 1
            assert payload["proposals"][0]["metrics_ref"]["metrics_csv"] == metrics_ok
            assert payload["boundary_evidence"]["row_count"] == 1
            assert payload["boundary_evidence"]["rows"][0]["metrics_csv"] == metrics_failed
            assert payload["boundary_evidence"]["rows"][0]["status"] == "failed"
            assert session.query(Artifact).filter_by(kind="promotion_proposal").one().metadata_["proposal_count"] == 1


@pytest.mark.parametrize("run_status", [RunStatus.FAILED, RunStatus.CANCELED])
def test_consume_l1_result_retains_partial_metrics_from_terminal_sweep(run_status: RunStatus) -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_rel = "runs/designs/npu_blocks/partial_cluster/metrics.csv"
        _write_metrics(
            repo_root / metrics_rel,
            [
                {
                    "platform": "nangate45",
                    "status": "ok",
                    "param_hash": "measured1",
                    "tag": "partial_cluster_proxy_die_2500",
                    "critical_path_ns": "7.2189",
                    "die_area": "6250000",
                    "total_power_mw": "0.3",
                    "result_path": "runs/designs/npu_blocks/partial_cluster/work/measured1/result.json",
                }
            ],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_partial_failed_sweep",
                source="test",
                requested_by="@tester",
                title="Partial failed sweep",
                description="retain measured rows from a terminal physical sweep",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_partial_failed_sweep",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1_sweep:test_partial_failed_sweep",
                task_request_id=task_request.id,
                item_id="l1_test_partial_failed_sweep",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.FAILED,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[metrics_rel],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="l1_test_partial_failed_sweep_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=run_status,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                failure_stage="worker",
                failure_category="worker_error",
                failure_signature="heartbeat connection timeout",
                result_summary="heartbeat connection timeout",
                result_payload={
                    "queue_result": {
                        "status": "fail",
                        "metrics_rows": [f"{metrics_rel}:2"],
                    },
                    "failure_classification": {
                        "stage": "worker",
                        "category": "worker_error",
                        "signature": "heartbeat connection timeout",
                    },
                },
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="expected_output",
                    storage_mode="repo",
                    path=metrics_rel,
                    metadata_={
                        "transport_policy": "inline_text_evidence",
                        "inline_utf8": (repo_root / metrics_rel).read_text(encoding="utf-8"),
                    },
                )
            )
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(repo_root=str(repo_root), run_key=run.run_key),
            )

            assert result.proposal_count == 1
            proposal_path = (
                repo_root
                / "control_plane"
                / "shadow_exports"
                / "l1_promotions"
                / f"{work_item.item_id}.json"
            )
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_assessment"]["outcome"] == "partial_sweep_measured_points"
            assert payload["proposal_assessment"]["sweep_complete"] is False
            assert payload["trial_summary"]["success_count"] == 0
            assert payload["trial_summary"]["failure_count"] == 1
            assert payload["trial_summary"]["partial_metrics_count"] == 1
            assert payload["partial_run_evidence"] == {
                "run_status": run_status.value,
                "failure_stage": "worker",
                "failure_category": "worker_error",
                "failure_signature": "heartbeat connection timeout",
                "captured_metrics_rows": [f"{metrics_rel}:2"],
                "sweep_complete": False,
                "promotion_scope": "captured_metrics_rows_only",
            }
            assert payload["proposals"][0]["metrics_ref"]["param_hash"] == "measured1"


def test_consume_l1_result_keeps_single_trial_metrics_without_trials_subdir() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_rel = "runs/designs/activations/terminal_hardsigmoid_int8_pwl_retrysubmission_wrapper/metrics.csv"
        _write_metrics(
            repo_root / metrics_rel,
            [
                {
                    "platform": "nangate45",
                    "status": "ok",
                    "param_hash": "fast0001",
                    "tag": "tag_fast",
                    "critical_path_ns": "0.1908",
                    "die_area": "25600",
                    "total_power_mw": "8.76e-05",
                    "result_path": "runs/designs/activations/terminal_hardsigmoid_int8_pwl_retrysubmission_wrapper/work/fast0001/result.json",
                }
            ],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_single_trial_plain_metrics",
                source="test",
                requested_by="@tester",
                title="single trial plain metrics",
                description="single-trial metrics without trials subdir",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_single_trial_plain_metrics",
                    "layer": "layer1",
                    "flow": "openroad",
                    "objective": "terminal_hardsigmoid_retrysubmission_physical_metrics",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_single_trial_plain_metrics",
                task_request_id=task_request.id,
                item_id="l1_test_single_trial_plain_metrics",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_rel],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            canceled_run = Run(
                run_key="l1_test_single_trial_plain_metrics_run_1",
                work_item_id=work_item.id,
                attempt=1,
                trial_index=1,
                seed=0,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.CANCELED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="operator canceled before execution",
                result_payload={"trial": {"trial_index": 1, "seed": 0}},
            )
            run = Run(
                run_key="l1_test_single_trial_plain_metrics_run_2",
                work_item_id=work_item.id,
                attempt=2,
                trial_index=1,
                seed=0,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="1/1 commands succeeded",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 0},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"]},
                },
            )
            session.add_all([canceled_run, run])
            session.flush()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )

            assert result.proposal_count == 1
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposals"][0]["metrics_ref"]["metrics_csv"] == metrics_rel
            assert payload["trial_summary"]["completed_trials"] == 1
            assert payload["trial_summary"]["success_count"] == 1
            assert payload["trial_summary"]["failure_count"] == 0

            trial_table_path = (
                repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            )
            assert "l1_test_single_trial_plain_metrics_run_1" not in trial_table_path.read_text(encoding="utf-8")


def test_consume_l1_result_filters_historical_rows_by_current_sweep_tag_prefix() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_rel = "runs/designs/npu_blocks/demo_block/metrics.csv"
        sweep_rel = "runs/campaigns/npu/demo/sweeps/current.json"
        sweep_path = repo_root / sweep_rel
        sweep_path.parent.mkdir(parents=True, exist_ok=True)
        sweep_path.write_text(json.dumps({"tag_prefix": "current_sweep"}) + "\n", encoding="utf-8")
        _write_metrics(
            repo_root / metrics_rel,
            [
                {
                    "platform": "nangate45",
                    "status": "ok",
                    "param_hash": "oldfast",
                    "tag": "old_sweep_flat",
                    "critical_path_ns": "1.0",
                    "die_area": "100",
                    "total_power_mw": "0.1",
                    "result_path": "runs/designs/npu_blocks/demo_block/work/oldfast/result.json",
                },
                {
                    "platform": "nangate45",
                    "status": "ok",
                    "param_hash": "current",
                    "tag": "current_sweep_flat",
                    "critical_path_ns": "5.0",
                    "die_area": "500",
                    "total_power_mw": "0.5",
                    "result_path": "runs/designs/npu_blocks/demo_block/work/current/result.json",
                },
            ],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_current_scope",
                source="test",
                requested_by="@tester",
                title="current scope",
                description="current-sweep scope",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={"item_id": "l1_test_current_scope", "objective": "current-sweep scope"},
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()
            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_current_scope",
                task_request_id=task_request.id,
                item_id="l1_test_current_scope",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={"sweeps": [sweep_rel]},
                command_manifest=[],
                expected_outputs=[metrics_rel],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()
            session.add(Run(
                run_key="l1_test_current_scope_run_1",
                work_item_id=work_item.id,
                attempt=1,
                trial_index=1,
                seed=0,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                result_summary="ok",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 0},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"]},
                },
            ))
            session.flush()

            consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))

            payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            assert payload["proposals"][0]["metrics_ref"]["param_hash"] == "current"
            assert payload["trial_summary"]["metrics"]["critical_path_ns"]["best"] == 5.0


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
            assert "\r" not in trial_table
            assert "trial_index,seed,status" in trial_table
            assert "l1_test_trial_aggregate_run_3" in trial_table

            artifact_kinds = {artifact.kind for artifact in session.query(Artifact).all()}
            assert {"promotion_proposal", "summary_stats", "failure_stats", "trial_table"} <= artifact_kinds


def test_trial_aggregate_filters_other_checkout_attempts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        success_metrics = "runs/designs/activations/filter_checkout_diff/source_checkout_success/metrics.csv"
        failed_metrics = "runs/designs/activations/filter_checkout_diff/source_checkout_failed/metrics.csv"
        _write_metrics(
            repo_root / success_metrics,
            [{
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "ok-source",
                "tag": "source-checkout",
                "critical_path_ns": "11.0",
                "die_area": "60000",
                "total_power_mw": "0.18",
                "result_path": "runs/designs/activations/filter_checkout_diff/source_checkout_success/work/ok/result.json",
            }],
        )
        _write_metrics(
            repo_root / failed_metrics,
            [{
                "platform": "nangate45",
                "status": "failed",
                "param_hash": "fail-source",
                "tag": "other-checkout",
                "result_path": "runs/designs/activations/filter_checkout_diff/source_checkout_failed/work/fail/result.json",
            }],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_trial_source_checkout_filter",
                source="test",
                requested_by="@tester",
                title="source checkout filter test",
                description="l1 checkout-aware trial aggregation",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_trial_source_checkout_filter",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_trial_source_checkout_filter",
                task_request_id=task_request.id,
                item_id="l1_test_trial_source_checkout_filter",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[success_metrics, failed_metrics],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            success_run = Run(
                run_key="l1_test_trial_source_checkout_filter_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=1,
                result_summary="source checkout success",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 1},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{success_metrics}:2"]},
                },
            )
            failed_run = Run(
                run_key="l1_test_trial_source_checkout_filter_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="feedface",
                trial_index=2,
                seed=2,
                result_summary="source checkout failed",
                failure_category="timing_unmet",
                failure_stage="route",
                failure_signature="timing violation",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 2},
                    "queue_result": {"status": "fail", "metrics_rows": [f"{failed_metrics}:2"]},
                    "failure_classification": {
                        "category": "timing_unmet",
                        "stage": "route",
                        "signature": "timing violation",
                    },
                },
            )
            session.add_all([success_run, failed_run])
            session.flush()
            session.add(
                Artifact(
                    run_id=failed_run.id,
                    kind="expected_output",
                    storage_mode="repo",
                    path=failed_metrics,
                    metadata_={
                        "transport_policy": "inline_text_evidence",
                        "inline_utf8": (repo_root / failed_metrics).read_text(encoding="utf-8"),
                    },
                )
            )
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    run_key=success_run.run_key,
                ),
            )

            assert result.item_id == work_item.item_id
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 1
            assert payload["trial_summary"]["completed_trials"] == 1
            assert payload["trial_summary"]["success_count"] == 1
            assert payload["trial_summary"]["failure_count"] == 0
            assert payload["trial_summary"]["aggregation_scope"] == "current_run_checkout_commit"
            assert payload["trial_summary"]["aggregation_source_commit"] == "deadbeef"
            assert payload["trial_summary"]["aggregation_included_attempts"] == 1
            assert payload["trial_summary"]["aggregation_excluded_attempts"] == 1
            assert payload["trial_summary"]["aggregation_excluded_source_commits"] == {"feedface": 1}
            assert payload["trial_summary"]["aggregation_excluded_attempt_run_keys"] == [failed_run.run_key]
            assert payload["trial_summary"]["aggregation_excluded_attempt_run_keys_truncated"] is False

            failure_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "failure_stats.json").read_text(
                    encoding="utf-8"
                )
            )
            assert failure_payload["aggregation_scope"] == "current_run_checkout_commit"
            assert failure_payload["aggregation_excluded_attempts"] == 1
            assert "timing_unmet" not in failure_payload["by_category"]
            trial_table = (repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv").read_text(
                encoding="utf-8"
            )
            assert success_run.run_key in trial_table
            assert failed_run.run_key not in trial_table


def test_trial_aggregation_counts_same_checkout_failure() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        success_metrics = "runs/designs/activations/filter_checkout_same/source_checkout_success/metrics.csv"
        failed_metrics = "runs/designs/activations/filter_checkout_same/source_checkout_failed/metrics.csv"
        _write_metrics(
            repo_root / success_metrics,
            [{
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "ok-source",
                "tag": "same-checkout",
                "critical_path_ns": "11.2",
                "die_area": "61000",
                "total_power_mw": "0.19",
                "result_path": "runs/designs/activations/filter_checkout_same/source_checkout_success/work/ok/result.json",
            }],
        )
        _write_metrics(
            repo_root / failed_metrics,
            [{
                "platform": "nangate45",
                "status": "failed",
                "param_hash": "fail-source",
                "tag": "same-checkout",
                "result_path": "runs/designs/activations/filter_checkout_same/source_checkout_failed/work/fail/result.json",
            }],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_trial_source_checkout_same_filter",
                source="test",
                requested_by="@tester",
                title="source checkout same filter test",
                description="l1 checkout-aware trial aggregation same commit",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_trial_source_checkout_same_filter",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_trial_source_checkout_same_filter",
                task_request_id=task_request.id,
                item_id="l1_test_trial_source_checkout_same_filter",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[success_metrics, failed_metrics],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            success_run = Run(
                run_key="l1_test_trial_source_checkout_same_filter_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=1,
                seed=1,
                result_summary="source checkout success",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 1},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{success_metrics}:2"]},
                },
            )
            failed_run = Run(
                run_key="l1_test_trial_source_checkout_same_filter_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=2,
                result_summary="source checkout failed",
                failure_category="timing_unmet",
                failure_stage="route",
                failure_signature="timing violation",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 2},
                    "queue_result": {"status": "fail", "metrics_rows": [f"{failed_metrics}:2"]},
                    "failure_classification": {
                        "category": "timing_unmet",
                        "stage": "route",
                        "signature": "timing violation",
                    },
                },
            )
            session.add_all([success_run, failed_run])
            session.flush()
            session.add(
                Artifact(
                    run_id=failed_run.id,
                    kind="expected_output",
                    storage_mode="repo",
                    path=failed_metrics,
                    metadata_={
                        "transport_policy": "inline_text_evidence",
                        "inline_utf8": (repo_root / failed_metrics).read_text(encoding="utf-8"),
                    },
                )
            )
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    run_key=success_run.run_key,
                ),
            )

            assert result.item_id == work_item.item_id
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["trial_summary"]["completed_trials"] == 2
            assert payload["trial_summary"]["success_count"] == 1
            assert payload["trial_summary"]["failure_count"] == 1
            assert payload["trial_summary"]["aggregation_scope"] == "current_run_checkout_commit"
            assert payload["trial_summary"]["aggregation_excluded_attempts"] == 0
            assert payload["trial_summary"]["aggregation_excluded_source_commits"] == {}
            assert payload["trial_summary"]["aggregation_excluded_attempt_run_keys"] == []
            assert payload["trial_summary"]["aggregation_excluded_attempt_run_keys_truncated"] is False

            failure_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "failure_stats.json").read_text(
                    encoding="utf-8"
                )
            )
            assert failure_payload["by_category"] == {"timing_unmet": 1}
            assert failure_payload["aggregation_excluded_attempts"] == 0


def test_trial_aggregation_legacy_checkout_falls_back_to_all_attempts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        success_metrics = "runs/designs/activations/filter_checkout_legacy/source_checkout_success/metrics.csv"
        failed_metrics = "runs/designs/activations/filter_checkout_legacy/source_checkout_failed/metrics.csv"
        _write_metrics(
            repo_root / success_metrics,
            [{
                "platform": "nangate45",
                "status": "ok",
                "param_hash": "ok-source",
                "tag": "legacy-checkout",
                "critical_path_ns": "11.4",
                "die_area": "62000",
                "total_power_mw": "0.20",
                "result_path": "runs/designs/activations/filter_checkout_legacy/source_checkout_success/work/ok/result.json",
            }],
        )
        _write_metrics(
            repo_root / failed_metrics,
            [{
                "platform": "nangate45",
                "status": "failed",
                "param_hash": "fail-source",
                "tag": "legacy-checkout",
                "result_path": "runs/designs/activations/filter_checkout_legacy/source_checkout_failed/work/fail/result.json",
            }],
        )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_trial_source_checkout_legacy",
                source="test",
                requested_by="@tester",
                title="source checkout legacy fallback test",
                description="l1 checkout-aware trial aggregation legacy fallback",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_trial_source_checkout_legacy",
                    "layer": "layer1",
                    "flow": "openroad",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_trial_source_checkout_legacy",
                task_request_id=task_request.id,
                item_id="l1_test_trial_source_checkout_legacy",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={"configs": [], "sweeps": []},
                command_manifest=[],
                expected_outputs=[success_metrics, failed_metrics],
                acceptance_rules=[],
                source_commit="deadbeef",
            )
            session.add(work_item)
            session.flush()

            legacy_run = Run(
                run_key="l1_test_trial_source_checkout_legacy_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.FAILED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="",
                trial_index=1,
                seed=1,
                result_summary="legacy checkout failed",
                failure_category="worker",
                failure_stage="lease",
                failure_signature="legacy lease expired",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 1},
                    "queue_result": {"status": "fail", "metrics_rows": [f"{failed_metrics}:2"]},
                    "failure_classification": {
                        "category": "worker",
                        "stage": "lease",
                        "signature": "legacy lease expired",
                    },
                },
            )
            success_run = Run(
                run_key="l1_test_trial_source_checkout_legacy_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=2,
                seed=2,
                result_summary="legacy checkout success",
                result_payload={
                    "trial": {"trial_index": 2, "seed": 2},
                    "queue_result": {"status": "ok", "metrics_rows": [f"{success_metrics}:2"]},
                },
            )
            session.add_all([legacy_run, success_run])
            session.flush()
            session.add(
                Artifact(
                    run_id=legacy_run.id,
                    kind="expected_output",
                    storage_mode="repo",
                    path=failed_metrics,
                    metadata_={
                        "transport_policy": "inline_text_evidence",
                        "inline_utf8": (repo_root / failed_metrics).read_text(encoding="utf-8"),
                    },
                )
            )
            session.commit()

            result = consume_l1_result(
                session,
                Layer1ConsumeRequest(
                    repo_root=str(repo_root),
                    run_key=legacy_run.run_key,
                ),
            )

            assert result.item_id == work_item.item_id
            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{work_item.item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["trial_summary"]["completed_trials"] == 2
            assert payload["trial_summary"]["success_count"] == 1
            assert payload["trial_summary"]["failure_count"] == 1
            assert payload["trial_summary"]["aggregation_scope"] == "legacy_missing_checkout"
            assert payload["trial_summary"]["aggregation_included_attempts"] == 2
            assert payload["trial_summary"]["aggregation_excluded_attempts"] == 0
            assert payload["trial_summary"]["aggregation_excluded_source_commits"] == {}
            assert payload["trial_summary"]["aggregation_excluded_attempt_run_keys"] == []

            failure_payload = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "failure_stats.json").read_text(
                    encoding="utf-8"
                )
            )
            assert failure_payload["aggregation_scope"] == "legacy_missing_checkout"
            assert failure_payload.get("aggregation_excluded_attempt_run_keys_truncated", False) is False


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
                result_summary="acceptance failed before retry",
                result_payload={
                    "trial": {"trial_index": 1, "seed": 101},
                    "retry_decision": {"requeue": True},
                    "queue_result": {"status": "fail", "metrics_rows": [f"{metrics_trial_1}:2"]},
                    "failure_classification": {
                        "category": "validation_error",
                        "stage": "acceptance",
                        "failed_command_name": "acceptance",
                        "signature": "no accepted rows",
                    },
                },
                failure_category="validation_error",
                failure_stage="acceptance",
                failure_signature="no accepted rows",
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
            assert failure_stats["by_category"] == {"validation_error": 1}
            assert failure_stats["by_stage"] == {"acceptance": 1}

            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            trial_table = trial_table_path.read_text(encoding="utf-8")
            assert "l1_test_requeued_failure_history_run_1,1,1,101,failed" in trial_table
            assert "validation_error,acceptance,no accepted rows" in trial_table
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


def test_consume_l1_result_does_not_bind_missing_trial_to_another_trial_metrics() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        metrics_trial_1 = "runs/designs/activations/softmax_seedvariance_wrapper/trials/trial_001/softmax_seedvariance_wrapper/metrics.csv"
        metrics_trial_2 = "runs/designs/activations/softmax_seedvariance_wrapper/trials/trial_002/softmax_seedvariance_wrapper/metrics.csv"
        for metrics_path, seed, cp in ((metrics_trial_1, 101, 20.2), (metrics_trial_2, 102, 20.3)):
            target = repo_root / metrics_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "\n".join([
                    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path",
                    f'softmax_seedvariance_wrapper,nangate45,cfgseed,p{seed},tag_{seed},ok,{cp},176005.0,1.1,"{{""CLOCK_PERIOD"": 6.0, ""FLOW_RANDOM_SEED"": {seed}, ""PLACE_DENSITY"": 0.6, ""TAG"": ""tag_{seed}""}}",runs/result_{seed}.json',
                ]) + "\n",
                encoding="utf-8",
            )

        with Session(engine) as session:
            task_request = TaskRequest(
                request_key="l1_sweep:test_missing_trial_binding",
                source="test",
                requested_by="@tester",
                title="Layer1 missing trial binding test",
                description="measure_seed_variance",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload={
                    "item_id": "l1_test_missing_trial_binding",
                    "layer": "layer1",
                    "flow": "openroad",
                    "objective": "measure_seed_variance",
                },
                source_commit="deadbeef",
            )
            session.add(task_request)
            session.flush()

            work_item = WorkItem(
                work_item_key="l1_sweep:l1_test_missing_trial_binding",
                task_request_id=task_request.id,
                item_id="l1_test_missing_trial_binding",
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
                trial_policy_json={"trial_count": 5, "seed_start": 101, "stop_after_failures": 5},
            )
            session.add(work_item)
            session.flush()

            run_1 = Run(
                run_key="l1_test_missing_trial_binding_run_1",
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
                run_key="l1_test_missing_trial_binding_run_2",
                work_item_id=work_item.id,
                attempt=2,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                checkout_commit="deadbeef",
                trial_index=6,
                seed=106,
                result_summary="retry succeeded but no trial_006 artifact exists",
                result_payload={"trial": {"trial_index": 6, "seed": 106}, "queue_result": {"status": "ok"}},
            )
            session.add_all([run_1, run_2])
            session.commit()

            consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))

            trial_table_path = repo_root / "control_plane" / "shadow_exports" / "l1_trials" / work_item.item_id / "trial_table.csv"
            trial_table_lines = trial_table_path.read_text(encoding="utf-8").strip().splitlines()
            assert metrics_trial_1 in trial_table_lines[1]
            assert ",6,106,succeeded,," in trial_table_lines[2]
