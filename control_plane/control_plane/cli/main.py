"""CLI entrypoint for the control-plane scaffold."""

from __future__ import annotations

import argparse
import json

from control_plane.api.app import main as serve_api_main
from control_plane.cli.export_queue import main as export_queue_main
from control_plane.cli.import_queue import main as import_queue_main
from control_plane.cli.reconcile_github import main as reconcile_github_main
from control_plane.cli.run_scheduler import main as run_scheduler_main
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
    if args.command == "show-config":
        print(json.dumps(Settings.from_env().__dict__, indent=2, sort_keys=True))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
