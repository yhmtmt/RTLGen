"""CLI entrypoint for the control-plane scaffold."""

from __future__ import annotations

import argparse
import json

from control_plane.api.app import main as serve_api_main
from control_plane.cli.export_queue import main as export_queue_main
from control_plane.cli.generate_l1_sweep import main as generate_l1_sweep_main
from control_plane.cli.import_queue import main as import_queue_main
from control_plane.cli.reconcile_github import main as reconcile_github_main
from control_plane.cli.run_scheduler import main as run_scheduler_main
from control_plane.cli.run_worker import main as run_worker_main
from control_plane.cli.sync_artifacts import main as sync_artifacts_main
from control_plane.config import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rtlgen-control-plane")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_api_parser = subparsers.add_parser("serve-api", help="Run the minimal HTTP API")
    settings = Settings.from_env()
    serve_api_parser.add_argument("--host", default=settings.host)
    serve_api_parser.add_argument("--port", default=settings.port, type=int)

    import_parser = subparsers.add_parser("import-queue", help="Import a queue item into the control-plane DB")
    import_parser.add_argument("--repo-root", required=True)
    import_parser.add_argument("--queue-path", required=True)
    import_parser.add_argument("--database-url", required=True)
    import_parser.add_argument("--source-commit")
    import_parser.add_argument("--mode", default="upsert")

    export_parser = subparsers.add_parser("export-queue", help="Export a control-plane work item to queue JSON")
    export_parser.add_argument("--repo-root", required=True)
    export_parser.add_argument("--item-id", required=True)
    export_parser.add_argument("--target-state", required=True, choices=["queued", "evaluated"])
    export_parser.add_argument("--database-url", required=True)
    export_parser.add_argument("--target-path")

    generate_l1_parser = subparsers.add_parser(
        "generate-l1-sweep",
        help="Generate a Layer 1 sweep work item directly into the control-plane DB",
    )
    generate_l1_parser.add_argument("--database-url", required=True)
    generate_l1_parser.add_argument("--repo-root", required=True)
    generate_l1_parser.add_argument("--sweep-path", required=True)
    generate_l1_parser.add_argument("--configs", nargs="+", required=True)
    generate_l1_parser.add_argument("--platform", required=True)
    generate_l1_parser.add_argument("--out-root", required=True)
    generate_l1_parser.add_argument("--requested-by", default="control_plane")
    generate_l1_parser.add_argument("--priority", type=int, default=1)
    generate_l1_parser.add_argument("--item-id")
    generate_l1_parser.add_argument("--title")
    generate_l1_parser.add_argument("--objective")
    generate_l1_parser.add_argument("--source-commit")
    generate_l1_parser.add_argument("--mode", default="upsert")

    github_parser = subparsers.add_parser("reconcile-github", help="Reconcile GitHub branch/PR metadata into the DB")
    github_parser.add_argument("--database-url", required=True)
    github_parser.add_argument("--repo", required=True)
    github_parser.add_argument("--item-id")
    github_parser.add_argument("--branch-name")
    github_parser.add_argument("--pr-number", type=int)
    github_parser.add_argument("--pr-url")
    github_parser.add_argument("--head-sha")
    github_parser.add_argument("--base-branch")
    github_parser.add_argument("--state", required=True)
    github_parser.add_argument("--run-key")
    github_parser.add_argument("--metadata-json")

    scheduler_parser = subparsers.add_parser("scheduler", help="Run scheduler maintenance commands")
    scheduler_parser.add_argument("--database-url", required=True)
    scheduler_parser.add_argument("scheduler_command", choices=["expire-stale-leases"])

    worker_parser = subparsers.add_parser("run-worker", help="Run the internal worker loop")
    worker_parser.add_argument("--database-url", required=True)
    worker_parser.add_argument("--repo-root", required=True)
    worker_parser.add_argument("--machine-key", required=True)
    worker_parser.add_argument("--hostname")
    worker_parser.add_argument("--executor-kind", default="local_process")
    worker_parser.add_argument("--capabilities-json")
    worker_parser.add_argument("--capability-filter-json")
    worker_parser.add_argument("--lease-seconds", type=int, default=1800)
    worker_parser.add_argument("--heartbeat-seconds", type=int, default=30)
    worker_parser.add_argument("--command-timeout-seconds", type=int)
    worker_parser.add_argument("--enforce-source-commit", action="store_true")
    worker_parser.add_argument("--log-root")
    worker_parser.add_argument("--max-items", type=int, default=1)

    sync_parser = subparsers.add_parser("sync-artifacts", help="Sync a completed run into an evaluated queue snapshot")
    sync_parser.add_argument("--database-url", required=True)
    sync_parser.add_argument("--repo-root", required=True)
    sync_parser.add_argument("--item-id")
    sync_parser.add_argument("--run-key")
    sync_parser.add_argument("--evaluator-id", default="control_plane")
    sync_parser.add_argument("--session-id")
    sync_parser.add_argument("--host")
    sync_parser.add_argument("--executor", default="@control_plane")
    sync_parser.add_argument("--branch-name")
    sync_parser.add_argument("--target-path")

    subparsers.add_parser("show-config", help="Print resolved scaffold configuration")

    args = parser.parse_args(argv)
    if args.command == "serve-api":
        return serve_api_main(["--host", args.host, "--port", str(args.port)])
    if args.command == "import-queue":
        return import_queue_main(
            [
                "--repo-root",
                args.repo_root,
                "--queue-path",
                args.queue_path,
                "--database-url",
                args.database_url,
                *(["--source-commit", args.source_commit] if args.source_commit else []),
                "--mode",
                args.mode,
            ]
        )
    if args.command == "export-queue":
        return export_queue_main(
            [
                "--repo-root",
                args.repo_root,
                "--item-id",
                args.item_id,
                "--target-state",
                args.target_state,
                "--database-url",
                args.database_url,
                *(["--target-path", args.target_path] if args.target_path else []),
            ]
        )
    if args.command == "generate-l1-sweep":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--sweep-path",
            args.sweep_path,
            "--platform",
            args.platform,
            "--out-root",
            args.out_root,
            "--requested-by",
            args.requested_by,
            "--priority",
            str(args.priority),
            "--mode",
            args.mode,
            "--configs",
            *args.configs,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--title", args.title),
            ("--objective", args.objective),
            ("--source-commit", args.source_commit),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return generate_l1_sweep_main(argv2)
    if args.command == "reconcile-github":
        argv2 = ["--database-url", args.database_url, "--repo", args.repo, "--state", args.state]
        for key, value in [
            ("--item-id", args.item_id),
            ("--branch-name", args.branch_name),
            ("--pr-number", args.pr_number),
            ("--pr-url", args.pr_url),
            ("--head-sha", args.head_sha),
            ("--base-branch", args.base_branch),
            ("--run-key", args.run_key),
            ("--metadata-json", args.metadata_json),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return reconcile_github_main(argv2)
    if args.command == "scheduler":
        return run_scheduler_main(
            [
                "--database-url",
                args.database_url,
                args.scheduler_command,
            ]
        )
    if args.command == "run-worker":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--machine-key",
            args.machine_key,
            "--executor-kind",
            args.executor_kind,
            "--lease-seconds",
            str(args.lease_seconds),
            "--heartbeat-seconds",
            str(args.heartbeat_seconds),
            "--max-items",
            str(args.max_items),
        ]
        for key, value in [
            ("--hostname", args.hostname),
            ("--capabilities-json", args.capabilities_json),
            ("--capability-filter-json", args.capability_filter_json),
            ("--command-timeout-seconds", args.command_timeout_seconds),
            ("--log-root", args.log_root),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        if args.enforce_source_commit:
            argv2.append("--enforce-source-commit")
        return run_worker_main(argv2)
    if args.command == "sync-artifacts":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--evaluator-id",
            args.evaluator_id,
            "--executor",
            args.executor,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--session-id", args.session_id),
            ("--host", args.host),
            ("--branch-name", args.branch_name),
            ("--target-path", args.target_path),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return sync_artifacts_main(argv2)
    if args.command == "show-config":
        print(json.dumps(Settings.from_env().__dict__, indent=2, sort_keys=True))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
