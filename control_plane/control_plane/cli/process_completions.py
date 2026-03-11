"""CLI for notebook-side completion processing."""

from __future__ import annotations

import argparse
import json
import socket

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.completion_service import CompletionProcessRequest, process_completed_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consume completed work items and optionally submit them")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--repo")
    parser.add_argument("--item-id")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--evaluator-id", default="control_plane")
    parser.add_argument("--session-id")
    parser.add_argument("--host", default=socket.gethostname())
    parser.add_argument("--executor", default="@control_plane")
    parser.add_argument("--branch-name")
    parser.add_argument("--snapshot-target-path")
    parser.add_argument("--package-target-path")
    parser.add_argument("--worktree-root")
    parser.add_argument("--commit-message")
    parser.add_argument("--pr-base", default="master")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        results = process_completed_items(
            session,
            CompletionProcessRequest(
                repo_root=args.repo_root,
                repo=args.repo,
                item_id=args.item_id,
                submit=args.submit,
                evaluator_id=args.evaluator_id,
                session_id=args.session_id,
                host=args.host,
                executor=args.executor,
                branch_name=args.branch_name,
                snapshot_target_path=args.snapshot_target_path,
                package_target_path=args.package_target_path,
                worktree_root=args.worktree_root,
                commit_message=args.commit_message,
                pr_base=args.pr_base,
                force=args.force,
            ),
        )
    print(json.dumps([result.__dict__ for result in results], indent=2, sort_keys=True))
    return 0
