"""GitHub reconciliation CLI for cp-007."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.github_bridge import GitHubReconcileRequest, reconcile_github_link


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile evaluator branch/PR metadata into the control-plane DB")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--branch-name")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--pr-url")
    parser.add_argument("--head-sha")
    parser.add_argument("--base-branch")
    parser.add_argument("--state", required=True)
    parser.add_argument("--run-key")
    parser.add_argument("--metadata-json")
    args = parser.parse_args(argv)

    metadata = json.loads(args.metadata_json) if args.metadata_json else None
    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = reconcile_github_link(
            session,
            GitHubReconcileRequest(
                repo=args.repo,
                item_id=args.item_id,
                branch_name=args.branch_name,
                pr_number=args.pr_number,
                pr_url=args.pr_url,
                head_sha=args.head_sha,
                base_branch=args.base_branch,
                state=args.state,
                run_key=args.run_key,
                metadata=metadata,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
