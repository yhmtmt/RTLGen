"""CLI for operator submission eligibility status."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.models.work_items import WorkItem
from control_plane.services.operator_submission import assess_submission_eligibility


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List operator submission eligibility for work items")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--eligible-only", action="store_true")
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
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
