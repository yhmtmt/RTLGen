"""Finalize a proposal after its evidence PR has merged."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.proposal_finalizer import ProposalFinalizeRequest, finalize_after_merge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize a proposal after an evaluation PR merge")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--run-key")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--pr-url")
    parser.add_argument("--merge-commit")
    parser.add_argument("--merged-utc")
    parser.add_argument("--no-git-publish", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = finalize_after_merge(
            session,
            ProposalFinalizeRequest(
                repo_root=args.repo_root,
                item_id=args.item_id,
                run_key=args.run_key,
                pr_number=args.pr_number,
                pr_url=args.pr_url,
                merge_commit=args.merge_commit,
                merged_utc=args.merged_utc,
                git_publish=not args.no_git_publish,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
