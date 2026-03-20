"""CLI for long-running worker supervision."""

from __future__ import annotations

import argparse
import json
import socket

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.worker_daemon import WorkerDaemonConfig, run_worker_daemon
from control_plane.workers.executor import WorkerConfig


def _parse_json_flag(raw: str | None):
    if raw is None:
        return None
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the internal worker as a polling daemon")
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
    parser.add_argument("--command-stall-timeout-seconds", type=int)
    parser.add_argument("--command-progress-seconds", type=int, default=60)
    parser.add_argument("--max-retry-attempts", type=int, default=2)
    parser.add_argument("--allow-stale-checkout", action="store_true")
    parser.add_argument("--log-root")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--max-items-per-poll", type=int, default=1)
    parser.add_argument("--max-polls", type=int)
    parser.add_argument("--stop-on-no-work", action="store_true")
    parser.add_argument("--no-scheduler-maintenance", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    result = run_worker_daemon(
        session_factory,
        config=WorkerDaemonConfig(
            worker=WorkerConfig(
                repo_root=args.repo_root,
                machine_key=args.machine_key,
                hostname=args.hostname,
                executor_kind=args.executor_kind,
                capabilities=_parse_json_flag(args.capabilities_json),
                capability_filter=_parse_json_flag(args.capability_filter_json),
                lease_seconds=args.lease_seconds,
                heartbeat_seconds=args.heartbeat_seconds,
                command_timeout_seconds=args.command_timeout_seconds,
                command_stall_timeout_seconds=args.command_stall_timeout_seconds,
                command_progress_seconds=args.command_progress_seconds,
                max_retry_attempts=args.max_retry_attempts,
                enforce_source_commit=not args.allow_stale_checkout,
                log_root=args.log_root,
            ),
            poll_seconds=args.poll_seconds,
            max_items_per_poll=args.max_items_per_poll,
            max_polls=args.max_polls,
            stop_on_no_work=args.stop_on_no_work,
            run_scheduler_maintenance=not args.no_scheduler_maintenance,
        ),
    )
    print(
        json.dumps(
            {
                "poll_count": result.poll_count,
                "executed_items": result.executed_items,
                "no_work_polls": result.no_work_polls,
                "results": [row.__dict__ for row in result.results],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0
