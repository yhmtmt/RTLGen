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
            assert result.work_item_state == "awaiting_review"

            proposal_path = repo_root / "control_plane" / "shadow_exports" / "l1_promotions" / f"{item_id}.json"
            payload = json.loads(proposal_path.read_text(encoding="utf-8"))
            assert payload["proposal_count"] == 2
            assert payload["proposals"][0]["metrics_ref"]["param_hash"] == "fast0001"
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
