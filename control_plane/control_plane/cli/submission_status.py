"""CLI for operator submission eligibility status."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.models.work_items import WorkItem
from control_plane.services.operator_submission import assess_submission_eligibility


def _render_table(rows: list[dict[str, object]]) -> str:
    headers = ["item_id", "task_type", "work_item_state", "eligible", "reason", "run_key"]
    widths: dict[str, int] = {header: len(header) for header in headers}
    for row in rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row.get(header, ""))))

    def fmt_row(values: dict[str, object]) -> str:
        return "  ".join(str(values.get(header, "")).ljust(widths[header]) for header in headers)

    lines = [fmt_row({header: header for header in headers}), fmt_row({header: "-" * widths[header] for header in headers})]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List operator submission eligibility for work items")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--eligible-only", action="store_true")
    parser.add_argument("--format", choices=["json", "table"], default="json")
    parser.add_argument("--jsonl", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        query = session.query(WorkItem).order_by(WorkItem.created_at.asc(), WorkItem.item_id.asc())
        if args.item_id:
            query = query.filter(WorkItem.item_id == args.item_id)
        rows = []
        for work_item in query.all():
            status = assess_submission_eligibility(session, work_item=work_item)
            if args.eligible_only and not status.eligible:
                continue
            rows.append(status.__dict__)
    if args.jsonl:
        for row in rows:
            print(json.dumps(row, sort_keys=True))
    elif args.format == "table":
        print(_render_table(rows))
    else:
        print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
