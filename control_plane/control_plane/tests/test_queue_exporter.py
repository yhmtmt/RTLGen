"""Queue exporter coverage for cp-006."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.api.app import create_app
from control_plane.db import create_all
from control_plane.models.queue_reconciliations import QueueReconciliation
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.queue_exporter import QueueExportRequest, export_queue_item
from control_plane.services.queue_importer import QueueImportRequest, import_queue_item

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_QUEUE_ITEM = REPO_ROOT / "runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json"


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def _seed_evaluated_result(session: Session, item_id: str) -> None:
    work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
    from control_plane.clock import utcnow
    from control_plane.models.enums import LeaseStatus, WorkItemState
    from control_plane.models.runs import Run
    from control_plane.models.worker_leases import WorkerLease
    from control_plane.models.worker_machines import WorkerMachine

    machine = WorkerMachine(
        machine_key="machine-export",
        hostname="machine-export",
        executor_kind="docker",
        capabilities={"platform": work_item.platform},
    )
    session.add(machine)
    session.flush()
    lease = WorkerLease(
        work_item_id=work_item.id,
        machine_id=machine.id,
        lease_token="lease-export",
        status=LeaseStatus.RELEASED,
        leased_at=utcnow(),
        expires_at=utcnow(),
        last_heartbeat_at=utcnow(),
    )
    session.add(lease)
    run = Run(
        run_key="run-export-1",
        work_item_id=work_item.id,
        lease_id=lease.id,
        attempt=1,
        executor_type="internal_worker",
        machine_id=machine.id,
        branch_name="eval/l2_e2e_softmax_macro_tail_v1/s20260308t000000z",
        status="succeeded",
        started_at=utcnow(),
        completed_at=utcnow(),
        result_summary="export smoke ok",
        result_payload={
            "queue_result": {
                "evaluator_id": "yhmtmt",
                "session_id": "s20260308t000000z",
                "host": "cp-host",
                "identity_block": "[role:evaluator][account:yhmtmt][session:s20260308t000000z][host:cp-host][item:l2_e2e_softmax_macro_tail_v1]",
                "notes": [
                    "validate_campaign: exit_code=0, duration_s=0.023",
                ],
                "metrics_rows": [
                    {
                        "metrics_csv": "runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/metrics.csv",
                        "platform": "nangate45",
                        "param_hash": "deadbeef",
                        "tag": "export_smoke",
                        "status": "ok",
                        "result_path": "runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/work/deadbeef/result.json",
                    }
                ],
            }
        },
    )
    session.add(run)
    work_item.state = WorkItemState.ARTIFACT_SYNC
    session.commit()


def test_export_queued_snapshot() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "queued.json"
        with make_session() as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(REPO_ROOT),
                    queue_path=str(REAL_QUEUE_ITEM.relative_to(REPO_ROOT)),
                ),
            )
            result = export_queue_item(
                session,
                QueueExportRequest(
                    repo_root=td,
                    item_id="l2_e2e_softmax_macro_tail_v1",
                    target_state="queued",
                    target_path=str(out),
                ),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            assert result.target_state == "queued"
            assert payload["state"] == "queued"
            assert payload["result"] is None
            assert payload["item_id"] == "l2_e2e_softmax_macro_tail_v1"
            assert session.query(QueueReconciliation).count() == 2


def test_export_evaluated_snapshot() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "evaluated.json"
        with make_session() as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(REPO_ROOT),
                    queue_path=str(REAL_QUEUE_ITEM.relative_to(REPO_ROOT)),
                ),
            )
            _seed_evaluated_result(session, "l2_e2e_softmax_macro_tail_v1")
            result = export_queue_item(
                session,
                QueueExportRequest(
                    repo_root=td,
                    item_id="l2_e2e_softmax_macro_tail_v1",
                    target_state="evaluated",
                    target_path=str(out),
                ),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            assert result.target_state == "evaluated"
            assert payload["state"] == "evaluated"
            assert payload["result"]["status"] == "ok"
            assert payload["result"]["queue_item_id"] == "l2_e2e_softmax_macro_tail_v1"
            assert payload["result"]["metrics_rows"][0]["tag"] == "export_smoke"
            assert "notes" not in payload["result"]


def test_export_route_works_in_process() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "cp.db"
        out = Path(td) / "evaluated.json"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
        create_all(engine)
        with Session(engine) as session:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(REPO_ROOT),
                    queue_path=str(REAL_QUEUE_ITEM.relative_to(REPO_ROOT)),
                ),
            )
            _seed_evaluated_result(session, "l2_e2e_softmax_macro_tail_v1")

        old = os.environ.get("RTLCP_DATABASE_URL")
        os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        try:
            app = create_app()
            status, headers, body = app.handle(
                "POST",
                "/api/v1/queue/export/l2_e2e_softmax_macro_tail_v1",
                json.dumps(
                    {
                        "repo_root": td,
                        "target_state": "evaluated",
                        "target_path": str(out),
                    }
                ).encode("utf-8"),
            )
            assert status == 200
            assert headers["Content-Type"] == "application/json"
            response = json.loads(body.decode("utf-8"))
            assert response["item_id"] == "l2_e2e_softmax_macro_tail_v1"
            assert json.loads(out.read_text(encoding="utf-8"))["state"] == "evaluated"
        finally:
            if old is None:
                del os.environ["RTLCP_DATABASE_URL"]
            else:
                os.environ["RTLCP_DATABASE_URL"] = old
