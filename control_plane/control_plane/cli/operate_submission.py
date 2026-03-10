"""CLI for one-shot review publication and draft PR submission."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.operator_submission import OperatorSubmissionRequest, operate_submission


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the full review publication and draft PR submission chain")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--run-key")
    parser.add_argument("--evaluator-id", default="control_plane")
    parser.add_argument("--session-id")
    parser.add_argument("--host")
    parser.add_argument("--executor", default="@control_plane")
    parser.add_argument("--branch-name")
    parser.add_argument("--snapshot-target-path")
    parser.add_argument("--package-target-path")
    parser.add_argument("--worktree-root")
    parser.add_argument("--commit-message")
    parser.add_argument("--pr-base", default="master")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = operate_submission(
            session,
            OperatorSubmissionRequest(
                repo_root=args.repo_root,
                repo=args.repo,
                item_id=args.item_id,
                run_key=args.run_key,
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
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
