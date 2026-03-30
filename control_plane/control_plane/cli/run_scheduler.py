"""Scheduler CLI for cp-005."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.lease_service import expire_stale_leases
from control_plane.services.scheduler import assign_work_item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run control-plane scheduler maintenance tasks")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("command", choices=["expire-stale-leases", "assign-item", "clear-assignment"])
    parser.add_argument("--item-id")
    parser.add_argument("--machine-key")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        if args.command == "expire-stale-leases":
            result = expire_stale_leases(session)
            print(json.dumps(result.__dict__, indent=2, sort_keys=True))
            return 0
        if args.command == "assign-item":
            if not args.item_id or not args.machine_key:
                raise SystemExit("assign-item requires --item-id and --machine-key")
            result = assign_work_item(session, item_id=args.item_id, machine_key=args.machine_key)
            print(json.dumps(result.__dict__, indent=2, sort_keys=True))
            return 0
        if args.command == "clear-assignment":
            if not args.item_id:
                raise SystemExit("clear-assignment requires --item-id")
            result = assign_work_item(session, item_id=args.item_id, machine_key=None)
            print(json.dumps(result.__dict__, indent=2, sort_keys=True))
            return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
