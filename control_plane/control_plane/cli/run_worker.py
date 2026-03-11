"""Worker CLI for cp-008."""

from __future__ import annotations

import argparse
import json
import socket

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.worker_service import render_worker_results, run_worker
from control_plane.workers.executor import WorkerConfig


def _parse_json_flag(raw: str | None) -> dict[str, object] | None:
    if raw is None:
        return None
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal RTLGen control-plane worker loop")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--machine-key", required=True)
    parser.add_argument("--hostname", default=socket.gethostname())
    parser.add_argument("--executor-kind", default="local_process")
    parser.add_argument("--capabilities-json")
    parser.add_argument("--capability-filter-json")
    parser.add_argument("--lease-seconds", type=int, default=1800)
    parser.add_argument("--heartbeat-seconds", type=int, default=30)
    parser.add_argument("--command-timeout-seconds", type=int)
    parser.add_argument("--max-retry-attempts", type=int, default=2)
    parser.add_argument("--enforce-source-commit", action="store_true")
    parser.add_argument("--log-root")
    parser.add_argument("--max-items", type=int, default=1)
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    config = WorkerConfig(
        repo_root=args.repo_root,
        machine_key=args.machine_key,
        hostname=args.hostname,
        executor_kind=args.executor_kind,
        capabilities=_parse_json_flag(args.capabilities_json),
        capability_filter=_parse_json_flag(args.capability_filter_json),
        lease_seconds=args.lease_seconds,
        heartbeat_seconds=args.heartbeat_seconds,
        command_timeout_seconds=args.command_timeout_seconds,
        max_retry_attempts=args.max_retry_attempts,
        enforce_source_commit=args.enforce_source_commit,
        log_root=args.log_root,
    )
    results = run_worker(session_factory, config=config, max_items=args.max_items)
    print(json.dumps(render_worker_results(results), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
