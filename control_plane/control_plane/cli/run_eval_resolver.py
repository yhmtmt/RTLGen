"""Run the eval-side resolver daemon."""

from __future__ import annotations

import argparse

from control_plane.db import build_engine, build_session_factory
from control_plane.services.resolver_eval_daemon import ResolverEvalDaemonConfig, run_eval_resolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rtlgen-control-plane run-eval-resolver")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--machine-key")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-polls", type=int)
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    session_factory = build_session_factory(engine)
    run_eval_resolver(
        session_factory,
        ResolverEvalDaemonConfig(
            repo=args.repo,
            machine_key=args.machine_key,
            poll_seconds=args.poll_seconds,
            max_polls=args.max_polls,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
