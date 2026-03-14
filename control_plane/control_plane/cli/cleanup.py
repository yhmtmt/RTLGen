"""CLI for control-plane cleanup and retention operations."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.cleanup_service import CleanupRequest, run_cleanup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean up control-plane runtime files and stale DB state")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--runtime-dir")
    parser.add_argument("--log-root")
    parser.add_argument("--max-age-days", type=int, default=7)
    parser.add_argument("--runtime-max-age-days", type=int)
    parser.add_argument("--log-max-age-days", type=int)
    parser.add_argument("--db-max-age-days", type=int)
    parser.add_argument("--no-runtime-files", action="store_true")
    parser.add_argument("--no-worker-logs", action="store_true")
    parser.add_argument("--no-db-leases", action="store_true")
    parser.add_argument("--no-db-transient-artifacts", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = run_cleanup(
            session,
            CleanupRequest(
                repo_root=args.repo_root,
                runtime_dir=args.runtime_dir,
                log_root=args.log_root,
                max_age_days=args.max_age_days,
                runtime_max_age_days=args.runtime_max_age_days,
                log_max_age_days=args.log_max_age_days,
                db_max_age_days=args.db_max_age_days,
                prune_runtime_files=not args.no_runtime_files,
                prune_worker_logs=not args.no_worker_logs,
                prune_db_leases=not args.no_db_leases,
                prune_db_transient_artifacts=not args.no_db_transient_artifacts,
                dry_run=not args.apply,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
