"""Notebook-side completion processing coverage."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ArtifactStorageMode
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.completion_service import (
    CompletionProcessRequest,
    CompletionProcessingError,
    process_completed_items,
)
from control_plane.services.operator_submission import OperatorSubmissionError


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
            assert results[0].work_item_state == "artifact_sync"
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


def test_process_completed_items_submit_blocks_shadow_only_item_without_force() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id = _seed_l1_artifact_sync(session, repo_root)
            try:
                process_completed_items(
                    session,
                    CompletionProcessRequest(
                        repo_root=str(repo_root),
                        item_id=item_id,
                        submit=True,
                        repo="yhmtmt/RTLGen",
                    ),
                )
            except CompletionProcessingError as exc:
                assert "missing canonical runs evidence outputs" in str(exc)
            else:
                raise AssertionError("expected CompletionProcessingError")


def test_process_completed_items_materializes_expected_output_artifacts_for_canonical_l1() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        metrics_rel = "runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/metrics.csv"
        index_rel = "runs/index.csv"
        metrics_text = (
            "platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'nangate45,ok,fast0001,tag_fast,12.0,30000,0.18,{"CLOCK_PERIOD": 6.0, "CORE_UTILIZATION": 30},'
            "runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/work/fast0001/result.json\n"
        )
        index_text = (
            "circuit_type,design,platform,status,critical_path_ns,die_area,total_power_mw,config_hash,param_hash,tag,result_path,params_json,metrics_path,design_path,sram_area_um2,sram_read_energy_pj,sram_write_energy_pj,sram_max_access_time_ns\n"
            "activations,softmax_rowwise_int8_r4_acc20_wrapper,nangate45,ok,12.0,30000,0.18,cfg123,fast0001,tag_fast,runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/work/fast0001/result.json,\"{\\\"CLOCK_PERIOD\\\": 6.0}\",runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/metrics.csv,runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper,,,\n"
        )
        with Session(engine) as session:
            payload = {
                "item_id": "completion_l1_canonical_demo",
                "title": "completion canonical demo",
                "layer": "layer1",
                "flow": "openroad",
                "handoff": {
                    "branch": "eval/completion_l1_canonical_demo/<session_id>",
                    "pr_title": "eval: completion canonical demo",
                    "pr_body_fields": {
                        "evaluator_id": "control_plane",
                        "session_id": "<session_id>",
                        "host": "<host>",
                        "queue_item_id": "completion_l1_canonical_demo",
                    },
                    "checklist": ["demo"],
                },
            }
            task = TaskRequest(
                request_key="completion:l1_canonical",
                source="test",
                requested_by="@tester",
                title="completion canonical demo",
                description="completion service canonical materialization test",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload=payload,
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="completion:l1_canonical",
                task_request_id=task.id,
                item_id="completion_l1_canonical_demo",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[metrics_rel, index_rel],
                acceptance_rules=[],
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="completion_l1_canonical_demo_run_1",
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
            session.flush()
            session.add_all(
                [
                    Artifact(
                        run_id=run.id,
                        kind="expected_output",
                        storage_mode=ArtifactStorageMode.REPO,
                        path=metrics_rel,
                        sha256=None,
                        metadata_={"inline_utf8": metrics_text},
                    ),
                    Artifact(
                        run_id=run.id,
                        kind="expected_output",
                        storage_mode=ArtifactStorageMode.REPO,
                        path=index_rel,
                        sha256=None,
                        metadata_={"inline_utf8": index_text},
                    ),
                ]
            )
            session.commit()

            results = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )
            assert len(results) == 1
            assert results[0].consumed is True
            assert results[0].work_item_state == "artifact_sync"

        assert (repo_root / metrics_rel).read_text(encoding="utf-8") == metrics_text
        assert (repo_root / index_rel).read_text(encoding="utf-8") == index_text


def test_process_completed_items_submission_failure_keeps_artifact_sync() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id = _seed_l1_artifact_sync(session, repo_root)
            with patch(
                "control_plane.services.completion_service.operate_submission",
                side_effect=OperatorSubmissionError("gh pr create failed"),
            ):
                try:
                    process_completed_items(
                        session,
                        CompletionProcessRequest(
                            repo_root=str(repo_root),
                            item_id=item_id,
                            submit=True,
                            repo="yhmtmt/RTLGen",
                            force=True,
                        ),
                    )
                except CompletionProcessingError as exc:
                    assert "gh pr create failed" in str(exc)
                else:
                    raise AssertionError("expected CompletionProcessingError")

            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            assert work_item.state == WorkItemState.ARTIFACT_SYNC


def test_process_completed_items_materializes_supporting_output_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        metrics_rel = "runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/metrics.csv"
        schedule_rel = (
            "runs/campaigns/npu/demo_supporting/artifacts/mapper/"
            "fp16_nm2_softmax_r4/logistic_regression/schedule.yml"
        )
        metrics_text = (
            "platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'nangate45,ok,fast0001,tag_fast,12.0,30000,0.18,{"CLOCK_PERIOD": 6.0},'
            "runs/designs/activations/softmax_rowwise_int8_r4_acc20_wrapper/work/fast0001/result.json\n"
        )
        schedule_text = "steps:\n- softmax\n"
        with Session(engine) as session:
            payload = {
                "item_id": "completion_supporting_demo",
                "title": "completion supporting demo",
                "layer": "layer1",
                "flow": "openroad",
                "handoff": {
                    "branch": "eval/completion_supporting_demo/<session_id>",
                    "pr_title": "eval: completion supporting demo",
                    "pr_body_fields": {
                        "evaluator_id": "control_plane",
                        "session_id": "<session_id>",
                        "host": "<host>",
                        "queue_item_id": "completion_supporting_demo",
                    },
                    "checklist": ["demo"],
                },
            }
            task = TaskRequest(
                request_key="completion:supporting",
                source="test",
                requested_by="@tester",
                title="completion supporting demo",
                description="completion service supporting artifact materialization test",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload=payload,
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="completion:supporting",
                task_request_id=task.id,
                item_id="completion_supporting_demo",
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
                run_key="completion_supporting_demo_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                result_summary="1/1 commands succeeded",
                result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"], "notes": []}},
            )
            session.add(run)
            session.flush()
            session.add_all(
                [
                    Artifact(
                        run_id=run.id,
                        kind="expected_output",
                        storage_mode=ArtifactStorageMode.REPO,
                        path=metrics_rel,
                        sha256=None,
                        metadata_={"inline_utf8": metrics_text},
                    ),
                    Artifact(
                        run_id=run.id,
                        kind="supporting_output",
                        storage_mode=ArtifactStorageMode.REPO,
                        path=schedule_rel,
                        sha256=None,
                        metadata_={"inline_utf8": schedule_text, "transport_policy": "inline_text_supporting"},
                    ),
                ]
            )
            session.commit()

            results = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )
            assert len(results) == 1
            assert results[0].consumed is True

        assert (repo_root / metrics_rel).read_text(encoding="utf-8") == metrics_text
        assert (repo_root / schedule_rel).read_text(encoding="utf-8") == schedule_text


def test_process_completed_items_skips_non_transportable_expected_output_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        shadow_rel = "control_plane/shadow_exports/tmp/ignored.txt"
        with Session(engine) as session:
            payload = {
                "item_id": "completion_skip_shadow_demo",
                "title": "completion skip shadow demo",
                "layer": "layer1",
                "flow": "openroad",
                "handoff": {
                    "branch": "eval/completion_skip_shadow_demo/<session_id>",
                    "pr_title": "eval: completion skip shadow demo",
                    "pr_body_fields": {
                        "evaluator_id": "control_plane",
                        "session_id": "<session_id>",
                        "host": "<host>",
                        "queue_item_id": "completion_skip_shadow_demo",
                    },
                    "checklist": ["demo"],
                },
            }
            task = TaskRequest(
                request_key="completion:skip_shadow",
                source="test",
                requested_by="@tester",
                title="completion skip shadow demo",
                description="completion service transport policy test",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                priority=1,
                request_payload=payload,
            )
            session.add(task)
            session.flush()
            work_item = WorkItem(
                work_item_key="completion:skip_shadow",
                task_request_id=task.id,
                item_id="completion_skip_shadow_demo",
                layer=LayerName.LAYER1,
                flow=FlowName.OPENROAD,
                platform="nangate45",
                task_type="l1_sweep",
                state=WorkItemState.ARTIFACT_SYNC,
                priority=1,
                source_mode="config",
                input_manifest={},
                command_manifest=[],
                expected_outputs=[shadow_rel],
                acceptance_rules=[],
            )
            session.add(work_item)
            session.flush()
            run = Run(
                run_key="completion_skip_shadow_demo_run_1",
                work_item_id=work_item.id,
                attempt=1,
                executor_type=ExecutorType.INTERNAL_WORKER,
                status=RunStatus.SUCCEEDED,
                started_at=utcnow(),
                completed_at=utcnow(),
                result_summary="1/1 commands succeeded",
                result_payload={"queue_result": {"status": "ok", "metrics_rows": [], "notes": []}},
            )
            session.add(run)
            session.flush()
            session.add(
                Artifact(
                    run_id=run.id,
                    kind="expected_output",
                    storage_mode=ArtifactStorageMode.REPO,
                    path=shadow_rel,
                    sha256=None,
                    metadata_={"inline_utf8": "ignore me\n", "transport_policy": "inline_text_evidence"},
                )
            )
            session.commit()

            result = process_completed_items(
                session,
                CompletionProcessRequest(
                    repo_root=str(repo_root),
                    item_id=work_item.item_id,
                ),
            )
            assert len(result) == 1

        assert not (repo_root / shadow_rel).exists()
