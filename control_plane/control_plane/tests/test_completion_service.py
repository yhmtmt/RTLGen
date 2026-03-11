"""Notebook-side completion processing coverage."""

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
from control_plane.services.completion_service import (
    CompletionProcessRequest,
    CompletionProcessingError,
    process_completed_items,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_l1_artifact_sync(session: Session, repo_root: Path) -> str:
    metrics_rel = "control_plane/shadow_exports/designs/complete_l1/softmax_rowwise_int8_r4_shift5_wrapper/metrics.csv"
    _write(
        repo_root / metrics_rel,
        (
            "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'softmax_rowwise_int8_r4_shift5_wrapper,nangate45,cfg123,ph123,tag123,ok,12.5,54093.4,0.739,"{""CLOCK_PERIOD"": 4.0}",'
            "control_plane/shadow_exports/designs/complete_l1/softmax_rowwise_int8_r4_shift5_wrapper/work/ph123/result.json\n"
        ),
    )

    payload = {
        "item_id": "completion_l1_demo",
        "title": "completion demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/completion_l1_demo/<session_id>",
            "pr_title": "eval: completion demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "completion_l1_demo",
            },
            "checklist": ["demo"],
        },
    }
    task = TaskRequest(
        request_key="completion:l1",
        source="test",
        requested_by="@tester",
        title="completion demo",
        description="completion service test",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key="completion:l1",
        task_request_id=task.id,
        item_id="completion_l1_demo",
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
    )
    session.add(work_item)
    session.flush()
    run = Run(
        run_key="completion_l1_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        result_summary="4/4 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()
    return work_item.item_id


def test_process_completed_items_consumes_l1_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id = _seed_l1_artifact_sync(session, repo_root)
            results = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                ),
            )
            assert len(results) == 1
            assert results[0].item_id == item_id
            assert results[0].consumed is True
            assert results[0].submitted is False
            assert results[0].work_item_state == "awaiting_review"
            assert results[0].target_path


def test_process_completed_items_rejects_wrong_state() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id = _seed_l1_artifact_sync(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            work_item.state = WorkItemState.RUNNING
            session.commit()
            try:
                process_completed_items(
                    session,
                    CompletionProcessRequest(
                        repo_root=str(repo_root),
                        item_id=item_id,
                    ),
                )
            except CompletionProcessingError as exc:
                assert "not ready for completion processing" in str(exc)
            else:
                raise AssertionError("expected CompletionProcessingError")
