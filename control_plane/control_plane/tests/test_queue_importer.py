"""Queue importer coverage for cp-003."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.queue_reconciliations import QueueReconciliation
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.queue_importer import QueueImportConflict, QueueImportError, QueueImportRequest, import_queue_item

REPO_ROOT = Path("/workspaces/RTLGen")
REAL_QUEUE_ITEM = REPO_ROOT / "runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json"


def _make_queue_import_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    origin_root = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin_root)], check=True, capture_output=True, text=True)
    queue_dir = repo_root / "runs" / "eval_queue" / "openroad" / "queued"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / REAL_QUEUE_ITEM.name
    queue_file.write_text(REAL_QUEUE_ITEM.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "init"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "tester@example.com"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Tester"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "test repo"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "remote", "add", "origin", str(origin_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "-u", "origin", "HEAD:master"], check=True, capture_output=True, text=True)
    head = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return repo_root, queue_file, head


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    return Session(engine)


def test_import_real_queue_item(tmp_path: Path) -> None:
    repo_root, queue_file, source_commit = _make_queue_import_repo(tmp_path)
    with make_session() as session:
        result = import_queue_item(
            session,
            QueueImportRequest(
                repo_root=str(repo_root),
                queue_path=str(queue_file),
                source_commit=source_commit,
            ),
        )
        work_item = session.query(WorkItem).filter_by(item_id="l2_e2e_softmax_macro_tail_v1").one()
        task_request = session.query(TaskRequest).filter_by(request_key="queue:l2_e2e_softmax_macro_tail_v1").one()
        reconciliation = session.query(QueueReconciliation).filter_by(id=result.reconciliation_id).one()
        assert result.status == "applied"
        assert work_item.platform == "nangate45"
        assert work_item.task_type == "l2_campaign"
        assert task_request.source_commit == source_commit
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

    repo_root, queue_file, source_commit = _make_queue_import_repo(tmp_path)
    db_file = tmp_path / "cp.db"
    payload = {
        "repo_root": str(repo_root),
        "queue_path": str(queue_file),
        "source_commit": source_commit,
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


def test_import_rejects_invalid_source_commit() -> None:
    with make_session() as session:
        try:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(REPO_ROOT),
                    queue_path=str(REAL_QUEUE_ITEM),
                    source_commit="badbadbad",
                ),
            )
        except QueueImportError as exc:
            assert "provided source_commit does not resolve to a commit" in str(exc)
        else:
            raise AssertionError("expected QueueImportError")


def test_import_rejects_source_commit_not_pushed_to_origin(tmp_path: Path) -> None:
    repo_root, queue_file, _ = _make_queue_import_repo(tmp_path)
    extra = repo_root / "LOCAL_ONLY.txt"
    extra.write_text("local only\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "LOCAL_ONLY.txt"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "local only"], check=True, capture_output=True, text=True)
    local_only_commit = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    with make_session() as session:
        try:
            import_queue_item(
                session,
                QueueImportRequest(
                    repo_root=str(repo_root),
                    queue_path=str(queue_file),
                    source_commit=local_only_commit,
                ),
            )
        except QueueImportError as exc:
            assert "not reachable from origin" in str(exc)
        else:
            raise AssertionError("expected QueueImportError")
