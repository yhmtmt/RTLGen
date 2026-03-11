"""Artifact-sync round-trip coverage for cp-009."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import build_session_factory, create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.queue_importer import QueueImportRequest, import_queue_item
from control_plane.services.reconciliation_service import (
    ArtifactSyncRequest,
    _normalize_metrics_csv_refs,
    sync_run_artifacts,
)
from control_plane.services.worker_service import run_worker
from control_plane.workers.executor import WorkerConfig


def _write_queue_item(repo_root: Path) -> Path:
    queue_path = repo_root / "runs" / "eval_queue" / "openroad" / "queued" / "cp009_item.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path = "runs/designs/demo_block/metrics.csv"
    report_path = "runs/campaigns/demo/report.md"
    item = {
        "version": 0.1,
        "item_id": "cp009_item",
        "title": "cp009 roundtrip test",
        "layer": "layer2",
        "flow": "openroad",
        "state": "queued",
        "priority": 1,
        "created_utc": "2026-03-08T00:00:00Z",
        "requested_by": "@tester",
        "platform": "nangate45",
        "task": {
            "objective": "prove artifact sync roundtrip",
            "source_mode": "src_verilog",
            "inputs": {
                "design_dirs": ["runs/designs/demo_block"],
                "configs": [],
                "sweeps": [],
                "macro_manifests": [],
                "candidate_manifests": [],
            },
            "commands": [
                {
                    "name": "write_metrics",
                    "run": (
                        "python3 -c \"from pathlib import Path; "
                        f"p=Path('{metrics_path}'); "
                        "p.parent.mkdir(parents=True, exist_ok=True); "
                        "p.write_text("
                        "'platform,status,param_hash,tag,result_path,work_result_json\\n"
                        "nangate45,ok,deadbeef,demo_tag,/orfs/flow/logs/demo/3_3_place_gp.json,runs/designs/demo_block/work/deadbeef/result.json\\n', "
                        "encoding='utf-8')\""
                    ),
                },
                {
                    "name": "write_report",
                    "run": (
                        "python3 -c \"from pathlib import Path; "
                        f"p=Path('{report_path}'); "
                        "p.parent.mkdir(parents=True, exist_ok=True); "
                        "p.write_text('# demo report\\n', encoding='utf-8')\""
                    ),
                },
            ],
            "expected_outputs": [
                metrics_path,
                report_path,
            ],
            "acceptance": [
                "write metrics and report outputs",
            ],
        },
        "handoff": {
            "branch": "eval/cp009_item/<session_id>",
            "pr_title": "eval: cp009 roundtrip test",
            "identity_block_format": "[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]",
            "pr_body_fields": {
                "evaluator_id": "tester",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "cp009_item",
            },
            "checklist": [
                "roundtrip export",
            ],
        },
        "result": None,
    }
    queue_path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    return queue_path


def test_sync_run_artifacts_roundtrips_internal_worker_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )
        assert worker_results[0].status == "succeeded"

        with Session(engine) as session:
            sync_result = sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t120000z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )
            assert sync_result.item_id == "cp009_item"
            assert sync_result.metrics_row_count == 1

        evaluated_path = repo_root / "runs" / "eval_queue" / "openroad" / "evaluated" / "cp009_item.json"
        payload = json.loads(evaluated_path.read_text(encoding="utf-8"))
        assert payload["state"] == "evaluated"
        assert payload["result"]["branch"] == "eval/cp009_item/s20260308t120000z"
        assert payload["result"]["executor"] == "@control_plane"
        assert payload["result"]["evaluator_id"] == "cpbot"
        assert payload["result"]["session_id"] == "s20260308t120000z"
        assert payload["result"]["host"] == "cp-host"
        assert payload["result"]["metrics_rows"][0]["metrics_csv"] == "runs/designs/demo_block/metrics.csv"
        assert payload["result"]["metrics_rows"][0]["param_hash"] == "deadbeef"
        assert payload["result"]["metrics_rows"][0]["tag"] == "demo_tag"
        assert payload["result"]["metrics_rows"][0]["result_path"] == "runs/designs/demo_block/work/deadbeef/result.json"
        assert payload["handoff"]["branch"] == "eval/cp009_item/s20260308t120000z"
        assert payload["handoff"]["pr_body_fields"]["evaluator_id"] == "cpbot"
        assert payload["handoff"]["pr_body_fields"]["session_id"] == "s20260308t120000z"
        assert payload["handoff"]["pr_body_fields"]["host"] == "cp-host"
        assert "notes" not in payload["result"]

        with Session(engine) as session:
            work_item = session.query(WorkItem).filter_by(item_id="cp009_item").one()
            run = session.query(Run).filter_by(run_key=worker_results[0].run_key).one()
            queue_snapshot = (
                session.query(Artifact)
                .filter(Artifact.run_id == run.id, Artifact.kind == "queue_snapshot")
                .one()
            )
            assert work_item.state == WorkItemState.AWAITING_REVIEW
            assert run.status == RunStatus.SUCCEEDED
            assert queue_snapshot.path == "runs/eval_queue/openroad/evaluated/cp009_item.json"


def test_sync_run_artifacts_allows_failed_terminal_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
                command_timeout_seconds=0,
            ),
            max_items=1,
        )

        assert worker_results[0].status == "failed"

        with Session(engine) as session:
            result = sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t120500z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )
            assert result.work_item_state == "awaiting_review"

        payload = json.loads(
            (repo_root / "runs" / "eval_queue" / "openroad" / "evaluated" / "cp009_item.json").read_text(encoding="utf-8")
        )
        assert payload["result"]["status"] == "fail"
        assert payload["result"]["queue_item_id"] == "cp009_item"


def test_sync_run_artifacts_recovers_portable_result_path_on_resync() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )
        assert worker_results[0].status == "succeeded"

        with Session(engine) as session:
            sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t120700z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )
            run = session.query(Run).filter_by(run_key=worker_results[0].run_key).one()
            payload = dict(run.result_payload or {})
            queue_result = dict(payload.get("queue_result") or {})
            metrics_rows = [dict(row) for row in queue_result.get("metrics_rows") or []]
            metrics_rows[0]["result_path"] = "/orfs/flow/logs/demo/3_3_place_gp.json"
            queue_result["metrics_rows"] = metrics_rows
            payload["queue_result"] = queue_result
            run.result_payload = payload
            session.commit()

        with Session(engine) as session:
            sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t120701z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )

        payload = json.loads(
            (repo_root / "runs" / "eval_queue" / "openroad" / "evaluated" / "cp009_item.json").read_text(encoding="utf-8")
        )
        assert payload["result"]["metrics_rows"][0]["result_path"] == "runs/designs/demo_block/work/deadbeef/result.json"


def test_sync_run_artifacts_recovers_from_non_path_stale_result_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )
        assert worker_results[0].status == "succeeded"

        with Session(engine) as session:
            sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t121000z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )
            run = session.query(Run).filter_by(run_key=worker_results[0].run_key).one()
            payload = dict(run.result_payload or {})
            queue_result = dict(payload.get("queue_result") or {})
            metrics_rows = [dict(row) for row in queue_result.get("metrics_rows") or []]
            metrics_rows[0]["result_path"] = '"CORE_UTILIZATION": 30'
            queue_result["metrics_rows"] = metrics_rows
            payload["queue_result"] = queue_result
            run.result_payload = payload
            session.commit()

        with Session(engine) as session:
            sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t121001z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="runs/eval_queue/openroad/evaluated/cp009_item.json",
                ),
            )

        payload = json.loads(
            (repo_root / "runs" / "eval_queue" / "openroad" / "evaluated" / "cp009_item.json").read_text(encoding="utf-8")
        )
        assert payload["result"]["metrics_rows"][0]["result_path"] == "runs/designs/demo_block/work/deadbeef/result.json"


def test_normalize_metrics_csv_refs_supports_modern_npu_metrics_shape() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        metrics_path = repo_root / "runs" / "designs" / "npu_blocks" / "demo_block" / "metrics.csv"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(
            (
                "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,"
                "flow_elapsed_seconds,stage_elapsed_seconds,params_json,result_path,work_result_json,synth_script_path,synth_script_sha1\n"
                'demo_block,nangate45,abc123,deadbeef,demo_tag,ok,5.0,100.0,0.2,10.0,4.0,'
                '"{""CLOCK_PERIOD"": 10.0, ""TAG"": ""demo_tag""}",'
                "/orfs/flow/logs/demo/3_3_place_gp.json,"
                "runs/designs/npu_blocks/demo_block/work/deadbeef/result.json,,\n"
            ),
            encoding="utf-8",
        )

        rows = _normalize_metrics_csv_refs(
            repo_root=repo_root,
            metrics_csv="runs/designs/npu_blocks/demo_block/metrics.csv",
            allow_missing=False,
        )
        assert len(rows) == 1
        assert rows[0]["platform"] == "nangate45"
        assert rows[0]["param_hash"] == "deadbeef"
        assert rows[0]["tag"] == "demo_tag"
        assert rows[0]["result_path"] == "runs/designs/npu_blocks/demo_block/work/deadbeef/result.json"


def test_sync_run_artifacts_defaults_to_shadow_export_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )
        assert worker_results[0].status == "succeeded"

        with Session(engine) as session:
            result = sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260308t120900z",
                    host="cp-host",
                    executor="@control_plane",
                ),
            )

        assert result.target_path.endswith("control_plane/shadow_exports/evaluated/cp009_item.json")
        assert not (repo_root / "runs" / "eval_queue" / "openroad" / "evaluated" / "cp009_item.json").exists()
        assert (repo_root / "control_plane" / "shadow_exports" / "evaluated" / "cp009_item.json").exists()


def test_sync_run_artifacts_reuses_branch_session_identity_when_session_not_provided() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        queue_path = _write_queue_item(repo_root)
        db_path = Path(td) / "cp.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_path.relative_to(repo_root)),
                ),
            )

        session_factory = build_session_factory(engine)
        worker_results = run_worker(
            session_factory,
            config=WorkerConfig(
                repo_root=str(repo_root),
                machine_key="cp009-worker",
                capabilities={"platform": "nangate45", "flow": "openroad"},
                capability_filter={"platform": "nangate45", "flow": "openroad"},
                lease_seconds=60,
                heartbeat_seconds=1,
            ),
            max_items=1,
        )
        assert worker_results[0].status == "succeeded"

        with Session(engine) as session:
            first = sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    session_id="s20260311t120000z",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="control_plane/shadow_exports/evaluated/cp009_item.json",
                ),
            )
            assert first.item_id == "cp009_item"

        with Session(engine) as session:
            second = sync_run_artifacts(
                session,
                ArtifactSyncRequest(
                    repo_root=str(repo_root),
                    item_id="cp009_item",
                    evaluator_id="cpbot",
                    host="cp-host",
                    executor="@control_plane",
                    target_path="control_plane/shadow_exports/evaluated/cp009_item.json",
                ),
            )
            assert second.item_id == "cp009_item"

        payload = json.loads(
            (repo_root / "control_plane" / "shadow_exports" / "evaluated" / "cp009_item.json").read_text(encoding="utf-8")
        )
        assert payload["result"]["branch"] == "eval/cp009_item/s20260311t120000z"
        assert payload["result"]["session_id"] == "s20260311t120000z"
        assert payload["handoff"]["branch"] == "eval/cp009_item/s20260311t120000z"
        assert payload["handoff"]["pr_body_fields"]["session_id"] == "s20260311t120000z"
