"""Source reconciliation recovery coverage."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.models.worker_machines import WorkerMachine
from control_plane.services import source_reconciler
from control_plane.services.source_reconciler import (
    SourceReconciliationError,
    next_source_required_item,
    reconcile_service_repo_source,
)


def _run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def _init_repo_with_stale_head(repo_root: Path) -> tuple[str, str]:
    origin_root = repo_root.parent / "origin.git"
    _run("git", "init", "--bare", str(origin_root))
    _run("git", "init", str(repo_root))
    _run("git", "-C", str(repo_root), "config", "user.email", "tester@example.com")
    _run("git", "-C", str(repo_root), "config", "user.name", "Tester")
    (repo_root / "README.md").write_text("initial\n", encoding="utf-8")
    _run("git", "-C", str(repo_root), "add", "README.md")
    _run("git", "-C", str(repo_root), "commit", "-m", "initial")
    _run("git", "-C", str(repo_root), "remote", "add", "origin", str(origin_root))
    _run("git", "-C", str(repo_root), "push", "-u", "origin", "HEAD:master")
    first = _run("git", "-C", str(repo_root), "rev-parse", "HEAD")

    (repo_root / "SOURCE.txt").write_text("source update\n", encoding="utf-8")
    _run("git", "-C", str(repo_root), "add", "SOURCE.txt")
    _run("git", "-C", str(repo_root), "commit", "-m", "source update")
    _run("git", "-C", str(repo_root), "push", "origin", "HEAD:master")
    second = _run("git", "-C", str(repo_root), "rev-parse", "HEAD")
    _run("git", "-C", str(repo_root), "checkout", "--detach", first)
    return first, second


def test_next_source_required_item_persists_capability_filter() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        task = TaskRequest(
            request_key="queue:source_item",
            source="test",
            requested_by="tester",
            title="source item",
            description="requires source",
            layer="layer2",
            flow="openroad",
            priority=1,
            request_payload={"item_id": "source_item"},
        )
        session.add(task)
        session.flush()
        item = WorkItem(
            work_item_key="queue:source_item",
            task_request_id=task.id,
            item_id="source_item",
            layer="layer2",
            flow="openroad",
            platform="nangate45",
            task_type="l2_campaign",
            state=WorkItemState.READY,
            priority=1,
            source_commit="0" * 40,
            assigned_machine_key="machine-1",
            input_manifest={},
            command_manifest=[],
            expected_outputs=[],
            acceptance_rules=[],
        )
        session.add(item)
        session.commit()

        selected = next_source_required_item(
            session,
            machine_key="machine-1",
            hostname=None,
            executor_kind="docker",
            machine_role="evaluator",
            slot_capacity=1,
            capabilities=None,
            capability_filter={"platform": "nangate45", "flow": "openroad"},
        )

        machine = session.query(WorkerMachine).filter_by(machine_key="machine-1").one()
        assert selected is not None
        assert selected.item_id == "source_item"
        assert machine.capabilities["platform"] == "nangate45"
        assert machine.capabilities["flow"] == "openroad"


def test_reconcile_service_repo_recovers_stale_git_index_lock(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    first, required = _init_repo_with_stale_head(repo_root)
    index_lock = repo_root / ".git" / "index.lock"
    index_lock.write_text("stale lock\n", encoding="utf-8")

    result = reconcile_service_repo_source(
        repo_root=str(repo_root),
        required_sha=required,
        update_ref="origin/master",
        allow_update=True,
    )

    assert result.status == "updated"
    assert result.required_sha == required
    assert result.source_commit_relation in {"exact", "descendant"}
    assert _run("git", "-C", str(repo_root), "rev-parse", "HEAD") == required
    assert first != required
    assert not index_lock.exists()


def test_reconcile_service_repo_keeps_index_lock_when_git_process_appears_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _, required = _init_repo_with_stale_head(repo_root)
    index_lock = repo_root / ".git" / "index.lock"
    index_lock.write_text("owned lock\n", encoding="utf-8")
    monkeypatch.setattr(source_reconciler, "_git_process_active_for_repo", lambda repo: True)

    with pytest.raises(SourceReconciliationError, match="git index lock is present"):
        reconcile_service_repo_source(
            repo_root=str(repo_root),
            required_sha=required,
            update_ref="origin/master",
            allow_update=True,
        )

    assert index_lock.exists()


def test_reconcile_service_repo_quarantines_untracked_checkout_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    first, _second = _init_repo_with_stale_head(repo_root)
    blocker_rel = Path("runs/designs/activations/demo_wrapper/metrics.csv")
    _run("git", "-C", str(repo_root), "checkout", "master")
    tracked_blocker = repo_root / blocker_rel
    tracked_blocker.parent.mkdir(parents=True, exist_ok=True)
    tracked_blocker.write_text("tracked,new\n", encoding="utf-8")
    _run("git", "-C", str(repo_root), "add", str(blocker_rel))
    _run("git", "-C", str(repo_root), "commit", "-m", "track generated metric")
    _run("git", "-C", str(repo_root), "push", "origin", "HEAD:master")
    required = _run("git", "-C", str(repo_root), "rev-parse", "HEAD")
    _run("git", "-C", str(repo_root), "checkout", "--detach", first)
    blocker = repo_root / blocker_rel
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("generated,old\n", encoding="utf-8")
    monkeypatch.setenv("RTLCP_SOURCE_QUARANTINE_ROOT", str(tmp_path / "quarantine"))

    result = reconcile_service_repo_source(
        repo_root=str(repo_root),
        required_sha=required,
        update_ref="origin/master",
        allow_update=True,
    )

    assert result.status == "updated"
    assert result.required_sha == required
    assert _run("git", "-C", str(repo_root), "rev-parse", "HEAD") == required
    assert first != required
    assert blocker.exists()
    assert blocker.read_text(encoding="utf-8") != "generated,old\n"
    assert len(result.quarantine_paths) == 1
    quarantine_dir = Path(result.quarantine_paths[0])
    assert quarantine_dir.is_dir()
    assert (quarantine_dir / blocker_rel).read_text(encoding="utf-8") == "generated,old\n"
    assert (quarantine_dir / "manifest.json").exists()
    assert "quarantined untracked checkout blockers" in (result.message or "")
