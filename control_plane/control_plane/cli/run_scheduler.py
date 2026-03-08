"""Scheduler CLI for cp-005."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.lease_service import expire_stale_leases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run control-plane scheduler maintenance tasks")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("command", choices=["expire-stale-leases"])
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        if args.command == "expire-stale-leases":
            result = expire_stale_leases(session)
            print(json.dumps(result.__dict__, indent=2, sort_keys=True))
            return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
