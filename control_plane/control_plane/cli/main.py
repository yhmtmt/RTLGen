"""CLI entrypoint for the control-plane scaffold."""

from __future__ import annotations

import argparse
import json

from control_plane.api.app import main as serve_api_main
from control_plane.cli.consume_l1_result import main as consume_l1_result_main
from control_plane.cli.consume_l2_result import main as consume_l2_result_main
from control_plane.cli.execute_submission import main as execute_submission_main
from control_plane.cli.export_queue import main as export_queue_main
from control_plane.cli.generate_l1_sweep import main as generate_l1_sweep_main
from control_plane.cli.generate_l2_campaign import main as generate_l2_campaign_main
from control_plane.cli.import_queue import main as import_queue_main
from control_plane.cli.operate_submission import main as operate_submission_main
from control_plane.cli.process_completions import main as process_completions_main
from control_plane.cli.prepare_submission import main as prepare_submission_main
from control_plane.cli.publish_review import main as publish_review_main
from control_plane.cli.reconcile_github import main as reconcile_github_main
from control_plane.cli.run_scheduler import main as run_scheduler_main
from control_plane.cli.run_worker_daemon import main as run_worker_daemon_main
from control_plane.cli.run_worker import main as run_worker_main
from control_plane.cli.submission_status import main as submission_status_main
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

    consume_l1_parser = subparsers.add_parser(
        "consume-l1-result",
        help="Consume a completed Layer 1 sweep result and emit a promotion proposal",
    )
    consume_l1_parser.add_argument("--database-url", required=True)
    consume_l1_parser.add_argument("--repo-root", required=True)
    consume_l1_parser.add_argument("--item-id")
    consume_l1_parser.add_argument("--run-key")
    consume_l1_parser.add_argument("--target-path")

    consume_l2_parser = subparsers.add_parser(
        "consume-l2-result",
        help="Consume a completed Layer 2 campaign result and emit a decision proposal",
    )
    consume_l2_parser.add_argument("--database-url", required=True)
    consume_l2_parser.add_argument("--repo-root", required=True)
    consume_l2_parser.add_argument("--item-id")
    consume_l2_parser.add_argument("--run-key")
    consume_l2_parser.add_argument("--target-path")

    generate_l2_parser = subparsers.add_parser(
        "generate-l2-campaign",
        help="Generate a Layer 2 campaign work item directly into the control-plane DB",
    )
    generate_l2_parser.add_argument("--database-url", required=True)
    generate_l2_parser.add_argument("--repo-root", required=True)
    generate_l2_parser.add_argument("--campaign-path", required=True)
    generate_l2_parser.add_argument("--platform")
    generate_l2_parser.add_argument("--requested-by", default="control_plane")
    generate_l2_parser.add_argument("--priority", type=int, default=1)
    generate_l2_parser.add_argument("--item-id")
    generate_l2_parser.add_argument("--title")
    generate_l2_parser.add_argument("--objective")
    generate_l2_parser.add_argument("--source-commit")
    generate_l2_parser.add_argument("--mode", default="upsert")
    generate_l2_parser.add_argument("--jobs", type=int, default=2)
    generate_l2_parser.add_argument("--batch-id")
    generate_l2_parser.add_argument("--objective-profiles-json")
    generate_l2_parser.add_argument("--no-run-physical", action="store_true")

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
    worker_parser.add_argument("--max-retry-attempts", type=int, default=2)
    worker_parser.add_argument("--enforce-source-commit", action="store_true")
    worker_parser.add_argument("--log-root")
    worker_parser.add_argument("--max-items", type=int, default=1)

    worker_daemon_parser = subparsers.add_parser("run-worker-daemon", help="Run the internal worker as a polling daemon")
    worker_daemon_parser.add_argument("--database-url", required=True)
    worker_daemon_parser.add_argument("--repo-root", required=True)
    worker_daemon_parser.add_argument("--machine-key", required=True)
    worker_daemon_parser.add_argument("--hostname")
    worker_daemon_parser.add_argument("--executor-kind", default="local_process")
    worker_daemon_parser.add_argument("--capabilities-json")
    worker_daemon_parser.add_argument("--capability-filter-json")
    worker_daemon_parser.add_argument("--lease-seconds", type=int, default=1800)
    worker_daemon_parser.add_argument("--heartbeat-seconds", type=int, default=30)
    worker_daemon_parser.add_argument("--command-timeout-seconds", type=int)
    worker_daemon_parser.add_argument("--max-retry-attempts", type=int, default=2)
    worker_daemon_parser.add_argument("--enforce-source-commit", action="store_true")
    worker_daemon_parser.add_argument("--log-root")
    worker_daemon_parser.add_argument("--poll-seconds", type=int, default=15)
    worker_daemon_parser.add_argument("--max-items-per-poll", type=int, default=1)
    worker_daemon_parser.add_argument("--max-polls", type=int)
    worker_daemon_parser.add_argument("--stop-on-no-work", action="store_true")
    worker_daemon_parser.add_argument("--no-scheduler-maintenance", action="store_true")

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

    process_parser = subparsers.add_parser(
        "process-completions",
        help="Consume completed items in artifact_sync and optionally submit them",
    )
    process_parser.add_argument("--database-url", required=True)
    process_parser.add_argument("--repo-root", required=True)
    process_parser.add_argument("--repo")
    process_parser.add_argument("--item-id")
    process_parser.add_argument("--submit", action="store_true")
    process_parser.add_argument("--evaluator-id", default="control_plane")
    process_parser.add_argument("--session-id")
    process_parser.add_argument("--host")
    process_parser.add_argument("--executor", default="@control_plane")
    process_parser.add_argument("--branch-name")
    process_parser.add_argument("--snapshot-target-path")
    process_parser.add_argument("--package-target-path")
    process_parser.add_argument("--worktree-root")
    process_parser.add_argument("--commit-message")
    process_parser.add_argument("--pr-base", default="master")
    process_parser.add_argument("--force", action="store_true")

    review_parser = subparsers.add_parser(
        "publish-review",
        help="Publish a review-ready queue snapshot and PR payload package from a completed run",
    )
    review_parser.add_argument("--database-url", required=True)
    review_parser.add_argument("--repo-root", required=True)
    review_parser.add_argument("--item-id")
    review_parser.add_argument("--run-key")
    review_parser.add_argument("--evaluator-id", default="control_plane")
    review_parser.add_argument("--session-id")
    review_parser.add_argument("--host")
    review_parser.add_argument("--executor", default="@control_plane")
    review_parser.add_argument("--branch-name")
    review_parser.add_argument("--snapshot-target-path")
    review_parser.add_argument("--package-target-path")

    submission_parser = subparsers.add_parser(
        "prepare-submission",
        help="Prepare a bot-owned branch/worktree from a published review package",
    )
    submission_parser.add_argument("--database-url", required=True)
    submission_parser.add_argument("--repo-root", required=True)
    submission_parser.add_argument("--item-id")
    submission_parser.add_argument("--run-key")
    submission_parser.add_argument("--evaluator-id", default="control_plane")
    submission_parser.add_argument("--session-id")
    submission_parser.add_argument("--host")
    submission_parser.add_argument("--executor", default="@control_plane")
    submission_parser.add_argument("--branch-name")
    submission_parser.add_argument("--snapshot-target-path")
    submission_parser.add_argument("--package-target-path")
    submission_parser.add_argument("--worktree-root")
    submission_parser.add_argument("--commit-message")
    submission_parser.add_argument("--pr-base", default="master")

    execute_parser = subparsers.add_parser(
        "execute-submission",
        help="Push a prepared submission branch and open a draft PR",
    )
    execute_parser.add_argument("--database-url", required=True)
    execute_parser.add_argument("--repo-root", required=True)
    execute_parser.add_argument("--repo", required=True)
    execute_parser.add_argument("--item-id")
    execute_parser.add_argument("--run-key")
    execute_parser.add_argument("--evaluator-id", default="control_plane")
    execute_parser.add_argument("--session-id")
    execute_parser.add_argument("--host")
    execute_parser.add_argument("--executor", default="@control_plane")
    execute_parser.add_argument("--branch-name")
    execute_parser.add_argument("--snapshot-target-path")
    execute_parser.add_argument("--package-target-path")
    execute_parser.add_argument("--worktree-root")
    execute_parser.add_argument("--commit-message")
    execute_parser.add_argument("--pr-base", default="master")
    execute_parser.add_argument("--manifest-path")

    operate_parser = subparsers.add_parser(
        "operate-submission",
        help="Publish review outputs, prepare a submission branch, and open the draft PR in one command",
    )
    operate_parser.add_argument("--database-url", required=True)
    operate_parser.add_argument("--repo-root", required=True)
    operate_parser.add_argument("--repo", required=True)
    operate_parser.add_argument("--item-id")
    operate_parser.add_argument("--run-key")
    operate_parser.add_argument("--evaluator-id", default="control_plane")
    operate_parser.add_argument("--session-id")
    operate_parser.add_argument("--host")
    operate_parser.add_argument("--executor", default="@control_plane")
    operate_parser.add_argument("--branch-name")
    operate_parser.add_argument("--snapshot-target-path")
    operate_parser.add_argument("--package-target-path")
    operate_parser.add_argument("--worktree-root")
    operate_parser.add_argument("--commit-message")
    operate_parser.add_argument("--pr-base", default="master")
    operate_parser.add_argument("--force", action="store_true")

    submission_status_parser = subparsers.add_parser(
        "submission-status",
        help="List operator submission eligibility for work items",
    )
    submission_status_parser.add_argument("--database-url", required=True)
    submission_status_parser.add_argument("--item-id")
    submission_status_parser.add_argument("--eligible-only", action="store_true")
    submission_status_parser.add_argument("--format", choices=["json", "table"], default="json")
    submission_status_parser.add_argument("--jsonl", action="store_true")

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
    if args.command == "consume-l1-result":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--target-path", args.target_path),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return consume_l1_result_main(argv2)
    if args.command == "consume-l2-result":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--target-path", args.target_path),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return consume_l2_result_main(argv2)
    if args.command == "generate-l2-campaign":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--campaign-path",
            args.campaign_path,
            "--requested-by",
            args.requested_by,
            "--priority",
            str(args.priority),
            "--mode",
            args.mode,
            "--jobs",
            str(args.jobs),
        ]
        for key, value in [
            ("--platform", args.platform),
            ("--item-id", args.item_id),
            ("--title", args.title),
            ("--objective", args.objective),
            ("--source-commit", args.source_commit),
            ("--batch-id", args.batch_id),
            ("--objective-profiles-json", args.objective_profiles_json),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        if args.no_run_physical:
            argv2.append("--no-run-physical")
        return generate_l2_campaign_main(argv2)
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
            "--max-retry-attempts",
            str(args.max_retry_attempts),
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
    if args.command == "run-worker-daemon":
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
            "--max-retry-attempts",
            str(args.max_retry_attempts),
            "--poll-seconds",
            str(args.poll_seconds),
            "--max-items-per-poll",
            str(args.max_items_per_poll),
        ]
        for key, value in [
            ("--hostname", args.hostname),
            ("--capabilities-json", args.capabilities_json),
            ("--capability-filter-json", args.capability_filter_json),
            ("--command-timeout-seconds", args.command_timeout_seconds),
            ("--log-root", args.log_root),
            ("--max-polls", args.max_polls),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        if args.enforce_source_commit:
            argv2.append("--enforce-source-commit")
        if args.stop_on_no_work:
            argv2.append("--stop-on-no-work")
        if args.no_scheduler_maintenance:
            argv2.append("--no-scheduler-maintenance")
        return run_worker_daemon_main(argv2)
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
    if args.command == "process-completions":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--evaluator-id",
            args.evaluator_id,
            "--executor",
            args.executor,
            "--pr-base",
            args.pr_base,
        ]
        for key, value in [
            ("--repo", args.repo),
            ("--item-id", args.item_id),
            ("--session-id", args.session_id),
            ("--host", args.host),
            ("--branch-name", args.branch_name),
            ("--snapshot-target-path", args.snapshot_target_path),
            ("--package-target-path", args.package_target_path),
            ("--worktree-root", args.worktree_root),
            ("--commit-message", args.commit_message),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        if args.submit:
            argv2.append("--submit")
        if args.force:
            argv2.append("--force")
        return process_completions_main(argv2)
    if args.command == "publish-review":
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
            ("--snapshot-target-path", args.snapshot_target_path),
            ("--package-target-path", args.package_target_path),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return publish_review_main(argv2)
    if args.command == "prepare-submission":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--evaluator-id",
            args.evaluator_id,
            "--executor",
            args.executor,
            "--pr-base",
            args.pr_base,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--session-id", args.session_id),
            ("--host", args.host),
            ("--branch-name", args.branch_name),
            ("--snapshot-target-path", args.snapshot_target_path),
            ("--package-target-path", args.package_target_path),
            ("--worktree-root", args.worktree_root),
            ("--commit-message", args.commit_message),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return prepare_submission_main(argv2)
    if args.command == "execute-submission":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--repo",
            args.repo,
            "--evaluator-id",
            args.evaluator_id,
            "--executor",
            args.executor,
            "--pr-base",
            args.pr_base,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--session-id", args.session_id),
            ("--host", args.host),
            ("--branch-name", args.branch_name),
            ("--snapshot-target-path", args.snapshot_target_path),
            ("--package-target-path", args.package_target_path),
            ("--worktree-root", args.worktree_root),
            ("--commit-message", args.commit_message),
            ("--manifest-path", args.manifest_path),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        return execute_submission_main(argv2)
    if args.command == "operate-submission":
        argv2 = [
            "--database-url",
            args.database_url,
            "--repo-root",
            args.repo_root,
            "--repo",
            args.repo,
            "--evaluator-id",
            args.evaluator_id,
            "--executor",
            args.executor,
            "--pr-base",
            args.pr_base,
        ]
        for key, value in [
            ("--item-id", args.item_id),
            ("--run-key", args.run_key),
            ("--session-id", args.session_id),
            ("--host", args.host),
            ("--branch-name", args.branch_name),
            ("--snapshot-target-path", args.snapshot_target_path),
            ("--package-target-path", args.package_target_path),
            ("--worktree-root", args.worktree_root),
            ("--commit-message", args.commit_message),
        ]:
            if value is not None:
                argv2.extend([key, str(value)])
        if args.force:
            argv2.append("--force")
        return operate_submission_main(argv2)
    if args.command == "submission-status":
        argv2 = ["--database-url", args.database_url]
        if args.item_id is not None:
            argv2.extend(["--item-id", str(args.item_id)])
        if args.eligible_only:
            argv2.append("--eligible-only")
        if args.format is not None:
            argv2.extend(["--format", str(args.format)])
        if args.jsonl:
            argv2.append("--jsonl")
        return submission_status_main(argv2)
    if args.command == "show-config":
        print(json.dumps(Settings.from_env().__dict__, indent=2, sort_keys=True))
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
