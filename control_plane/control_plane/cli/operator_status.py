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


def _render_table(payload: dict[str, object]) -> str:
    sections = [
        _render_state_counts(dict(payload["state_counts"])),
        _render_rows(
            "Active Runs",
            list(payload["active_runs"]),
            ["item_id", "task_type", "worker_host", "started_at", "last_heartbeat_at", "run_key"],
        ),
        _render_rows(
            "Stale Leases",
            list(payload["stale_leases"]),
            ["item_id", "hostname", "expires_at", "last_heartbeat_at", "lease_token"],
        ),
        _render_rows(
            "Recent Failures",
            list(payload["recent_failures"]),
            ["item_id", "failure_category", "summary", "retry_requeue", "worker_host", "run_key"],
        ),
        _render_rows(
            "Recent Submissions",
            list(payload["recent_submissions"]),
            ["item_id", "pr_number", "state", "branch_name", "updated_at"],
        ),
    ]
    return "\n\n".join(sections)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show operator-facing live status for the control plane")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--recent-limit", type=int, default=10)
    parser.add_argument("--format", choices=["json", "table"], default="table")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        status = load_operator_status(session, OperatorStatusRequest(recent_limit=args.recent_limit))
    payload = {
        "state_counts": status.state_counts,
        "active_runs": status.active_runs,
        "stale_leases": status.stale_leases,
        "recent_failures": status.recent_failures,
        "recent_submissions": status.recent_submissions,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_table(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
