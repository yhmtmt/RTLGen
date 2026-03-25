"""CLI for polling GitHub PR state and reconciling merged review PRs."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.github_poller import GitHubPollRequest, poll_github_links


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poll GitHub for merged review PRs and reconcile them into the DB")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--repo")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = poll_github_links(
            session,
            GitHubPollRequest(
                repo_root=args.repo_root,
                repo=args.repo,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
