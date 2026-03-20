"""Request cancellation of an active run."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.models.enums import RunStatus
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.run_service import request_run_cancel


def _resolve_run_key(session, *, run_key: str | None, item_id: str | None) -> str:
    if run_key:
        return run_key
    if not item_id:
        raise SystemExit("provide --run-key or --item-id")
    run = (
        session.query(Run)
        .join(WorkItem, WorkItem.id == Run.work_item_id)
        .filter(WorkItem.item_id == item_id)
        .filter(Run.status == RunStatus.RUNNING)
        .order_by(Run.created_at.desc())
        .first()
    )
    if run is None:
        raise SystemExit(f"no active run found for item_id={item_id}")
    return run.run_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Request cancellation of an active run")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--run-key")
    parser.add_argument("--item-id")
    parser.add_argument("--requested-by", default="developer_agent")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        resolved_run_key = _resolve_run_key(session, run_key=args.run_key, item_id=args.item_id)
        result = request_run_cancel(
            session,
            run_key=resolved_run_key,
            requested_by=args.requested_by,
            reason=args.reason,
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
