"""CLI for backfilling stale awaiting_review items without PRs."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.review_state_backfill import ReviewStateBackfillRequest, backfill_review_states


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill stale awaiting_review items that have no PR")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--item-id")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        rows = backfill_review_states(session, ReviewStateBackfillRequest(item_id=args.item_id))
    print(json.dumps([row.__dict__ for row in rows], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
