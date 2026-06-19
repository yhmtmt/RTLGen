"""CLI for requesting remote evaluator source refresh and daemon restart."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from control_plane.db import build_engine, build_session_factory
from control_plane.models.enums import WorkItemState
from control_plane.models.work_items import WorkItem
from control_plane.services.evaluator_refresh_request import (
    EvaluatorRefreshRequest,
    request_evaluator_refresh,
)
from control_plane.services.operator_status import OperatorStatusRequest, load_operator_status


def _current_commit(repo_root: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(Path(repo_root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _operator_status_details(
    *,
    database_url: str,
    repo_root: str,
    machine_key: str | None,
    recent_limit: int,
) -> tuple[str, ...]:
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)
    details: list[str] = []
    with session_factory() as session:
        status = load_operator_status(
            session,
            OperatorStatusRequest(recent_limit=recent_limit, repo_root=repo_root),
        )
        details.append(f"operator health: {status.health_summary['message']}")
        for machine in status.evaluator_machines:
            if machine_key and machine.get("machine_key") != machine_key:
                continue
            details.append(
                "machine "
                f"{machine.get('machine_key')}: assigned_ready={machine.get('assigned_ready')}, "
                f"active_slots={machine.get('active_slots')}, "
                f"heartbeat_age_seconds={machine.get('heartbeat_age_seconds')}, "
                f"worker_attention={machine.get('worker_attention')}, "
                f"capabilities={machine.get('capabilities')}, "
                f"last_progress={machine.get('last_progress')}"
            )
        ready_query = session.query(WorkItem).filter(WorkItem.state == WorkItemState.READY)
        if machine_key:
            ready_query = ready_query.filter(WorkItem.assigned_machine_key == machine_key)
        ready_items = (
            ready_query.order_by(WorkItem.priority.desc(), WorkItem.created_at.asc(), WorkItem.item_id.asc())
            .limit(recent_limit)
            .all()
        )
        for item in ready_items:
            details.append(
                f"ready item {item.item_id}: assigned_machine_key={item.assigned_machine_key}, "
                f"source_commit={item.source_commit}, task_type={item.task_type}"
            )
        for row in status.blocked_items[:recent_limit]:
            details.append(
                f"blocked item {row['item_id']}: {row.get('dependency_reason')}; "
                f"dependencies={row.get('dependency_item_ids')}"
            )
    return tuple(details)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Request evaluator source refresh and daemon restart")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--target-commit")
    parser.add_argument("--reason", default="control-plane source changed")
    parser.add_argument("--evaluator", default="remote evaluator")
    parser.add_argument("--database-url")
    parser.add_argument("--include-operator-status", action="store_true")
    parser.add_argument("--machine-key")
    parser.add_argument("--recent-limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    target_commit = args.target_commit or _current_commit(args.repo_root)
    details: tuple[str, ...] = ()
    if args.include_operator_status:
        if not args.database_url:
            parser.error("--include-operator-status requires --database-url")
        details = _operator_status_details(
            database_url=args.database_url,
            repo_root=args.repo_root,
            machine_key=args.machine_key,
            recent_limit=args.recent_limit,
        )
    result = request_evaluator_refresh(
        EvaluatorRefreshRequest(
            repo=args.repo,
            target_commit=target_commit,
            reason=args.reason,
            evaluator=args.evaluator,
            dry_run=args.dry_run,
            details=details,
        )
    )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
