"""Run the dev-side resolver daemon."""

from __future__ import annotations

import argparse

from control_plane.db import build_engine, build_session_factory
from control_plane.services.resolver_dev_daemon import ResolverDevDaemonConfig, run_dev_resolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rtlgen-control-plane run-dev-resolver")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-polls", type=int)
    parser.add_argument("--orphaned-stale-grace-seconds", type=int, default=600)
    parser.add_argument("--blocked-submission-stale-grace-seconds", type=int, default=120)
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    session_factory = build_session_factory(engine)
    run_dev_resolver(
        session_factory,
        ResolverDevDaemonConfig(
            repo=args.repo,
            repo_root=args.repo_root,
            poll_seconds=args.poll_seconds,
            max_polls=args.max_polls,
            orphaned_stale_grace_seconds=args.orphaned_stale_grace_seconds,
            blocked_submission_stale_grace_seconds=args.blocked_submission_stale_grace_seconds,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
