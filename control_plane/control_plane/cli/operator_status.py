"""CLI for operator-facing control-plane status."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.operator_status import OperatorStatusRequest, load_operator_status


def _render_state_counts(state_counts: dict[str, int]) -> str:
    ordered = sorted(state_counts.items(), key=lambda row: row[0])
    lines = ["State Counts", "------------"]
    lines.extend(f"{name}: {count}" for name, count in ordered)
    return "\n".join(lines)


def _render_rows(title: str, rows: list[dict[str, object]], columns: list[str]) -> str:
    lines = [title, "-" * len(title)]
    if not rows:
        lines.append("(none)")
        return "\n".join(lines)

    widths = {column: len(column) for column in columns}
    for row in rows:
        for column in columns:
            widths[column] = max(widths[column], len(str(row.get(column, ""))))

    def fmt_row(values: dict[str, object]) -> str:
        return "  ".join(str(values.get(column, "")).ljust(widths[column]) for column in columns)

    lines.append(fmt_row({column: column for column in columns}))
    lines.append(fmt_row({column: "-" * widths[column] for column in columns}))
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)


def _render_health_summary(summary: dict[str, object]) -> str:
    return "\n".join(["Health", "------", str(summary["message"])])


def _render_table(payload: dict[str, object]) -> str:
    sections = [
        _render_health_summary(dict(payload["health_summary"])),
        _render_state_counts(dict(payload["state_counts"])),
    ]
    sections.extend(_render_section(payload, "all"))
    return "\n\n".join(sections)


def _render_section(payload: dict[str, object], only: str) -> list[str]:
    sections = []
    if only in ("all", "active-runs"):
        sections.append(
            _render_rows(
                "Active Runs",
                list(payload["active_runs"]),
                ["item_id", "task_type", "worker_host", "started_at", "last_heartbeat_at", "run_key"],
            )
        )
    if only in ("all", "stale-leases"):
        sections.append(
            _render_rows(
                "Stale Leases",
                list(payload["stale_leases"]),
                ["item_id", "hostname", "expires_at", "last_heartbeat_at", "lease_token"],
            )
        )
    if only in ("all", "failures"):
        sections.append(
            _render_rows(
                "Recent Failures",
                list(payload["recent_failures"]),
                ["item_id", "failure_category", "failure_issue_status", "failure_issue_number", "summary", "retry_requeue", "worker_host", "run_key"],
            )
        )
    if only in ("all", "submissions"):
        sections.append(
            _render_rows(
                "Recent Submissions",
                list(payload["recent_submissions"]),
                ["item_id", "pr_number", "state", "branch_name", "updated_at"],
            )
        )
    if only in ("all", "resolver-cases"):
        sections.append(
            _render_rows(
                "Resolver Cases",
                list(payload["recent_resolver_cases"]),
                ["item_id", "failure_class", "owner", "status", "issue_number", "attempt_count", "updated_at"],
            )
        )
    return sections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show operator-facing live status for the control plane")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--recent-limit", type=int, default=10)
    parser.add_argument("--format", choices=["json", "table"], default="table")
    parser.add_argument(
        "--only",
        choices=["all", "health", "state-counts", "active-runs", "stale-leases", "failures", "submissions", "resolver-cases"],
        default="all",
    )
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        status = load_operator_status(session, OperatorStatusRequest(recent_limit=args.recent_limit))
    payload = {
        "health_summary": status.health_summary,
        "state_counts": status.state_counts,
        "active_runs": status.active_runs,
        "stale_leases": status.stale_leases,
        "recent_failures": status.recent_failures,
        "recent_submissions": status.recent_submissions,
        "recent_resolver_cases": status.recent_resolver_cases,
    }
    if args.format == "json":
        if args.only == "all":
            out = payload
        elif args.only == "health":
            out = {"health_summary": payload["health_summary"]}
        elif args.only == "state-counts":
            out = {"state_counts": payload["state_counts"]}
        elif args.only == "active-runs":
            out = {"active_runs": payload["active_runs"]}
        elif args.only == "stale-leases":
            out = {"stale_leases": payload["stale_leases"]}
        elif args.only == "failures":
            out = {"recent_failures": payload["recent_failures"]}
        elif args.only == "resolver-cases":
            out = {"recent_resolver_cases": payload["recent_resolver_cases"]}
        else:
            out = {"recent_submissions": payload["recent_submissions"]}
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        if args.only == "all":
            print(_render_table(payload))
        elif args.only == "health":
            print(_render_health_summary(dict(payload["health_summary"])))
        elif args.only == "state-counts":
            print(_render_state_counts(dict(payload["state_counts"])))
        else:
            print("\n\n".join(_render_section(payload, args.only)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
