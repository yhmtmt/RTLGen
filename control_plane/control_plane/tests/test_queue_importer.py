"""Queue importer coverage for cp-003."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.queue_reconciliations import QueueReconciliation
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.queue_importer import QueueImportConflict, QueueImportRequest, import_queue_item

REPO_ROOT = Path("/workspaces/RTLGen")
REAL_QUEUE_ITEM = REPO_ROOT / "runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json"


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def test_import_real_queue_item() -> None:
    with make_session() as session:
        result = import_queue_item(
            session,
            QueueImportRequest(
                repo_root=str(REPO_ROOT),
                queue_path=str(REAL_QUEUE_ITEM),
                source_commit="abc1234",
            ),
        )
        work_item = session.query(WorkItem).filter_by(item_id="l2_e2e_softmax_macro_tail_v1").one()
        task_request = session.query(TaskRequest).filter_by(request_key="queue:l2_e2e_softmax_macro_tail_v1").one()
        reconciliation = session.query(QueueReconciliation).filter_by(id=result.reconciliation_id).one()
        assert result.status == "applied"
        assert work_item.platform == "nangate45"
        assert work_item.task_type == "l2_campaign"
        assert task_request.source_commit == "abc1234"
        assert reconciliation.status.value == "applied"


def test_import_same_item_is_idempotent() -> None:
    with make_session() as session:
        first = import_queue_item(
            session,
            QueueImportRequest(repo_root=str(REPO_ROOT), queue_path=str(REAL_QUEUE_ITEM)),
        )
        second = import_queue_item(
            session,
            QueueImportRequest(repo_root=str(REPO_ROOT), queue_path=str(REAL_QUEUE_ITEM)),
        )
        assert first.status == "applied"
        assert second.status == "skipped"
        assert session.query(WorkItem).count() == 1
        assert session.query(TaskRequest).count() == 1
        assert session.query(QueueReconciliation).count() == 2


def test_import_conflict_for_semantic_change(tmp_path: Path) -> None:
    payload = json.loads(REAL_QUEUE_ITEM.read_text(encoding="utf-8"))
    queue_file = tmp_path / "item.json"
    queue_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with make_session() as session:
        import_queue_item(
            session,
            QueueImportRequest(repo_root=str(tmp_path), queue_path="item.json"),
        )
        payload["task"]["objective"] = "semantically different task"
        queue_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            import_queue_item(
                session,
                QueueImportRequest(repo_root=str(tmp_path), queue_path="item.json"),
            )
            raise AssertionError("expected QueueImportConflict")
        except QueueImportConflict:
            pass


def test_import_route_accepts_post_with_sqlite_file(tmp_path: Path) -> None:
    from control_plane.api.app import create_app

    db_file = tmp_path / "cp.db"
    payload = {
        "repo_root": str(REPO_ROOT),
        "queue_path": str(REAL_QUEUE_ITEM),
        "source_commit": "feedbeef",
    }

    import os
    old = os.environ.get("RTLCP_DATABASE_URL")
    os.environ["RTLCP_DATABASE_URL"] = f"sqlite+pysqlite:///{db_file}"
    try:
        app = create_app()
        status, headers, body = app.handle(
            "POST",
            "/api/v1/queue/import",
            json.dumps(payload).encode("utf-8"),
        )
        assert status == 200
        assert headers["Content-Type"] == "application/json"
        response = json.loads(body.decode("utf-8"))
        assert response["item_id"] == "l2_e2e_softmax_macro_tail_v1"
        assert response["status"] == "applied"
    finally:
        if old is None:
            del os.environ["RTLCP_DATABASE_URL"]
        else:
            os.environ["RTLCP_DATABASE_URL"] = old
