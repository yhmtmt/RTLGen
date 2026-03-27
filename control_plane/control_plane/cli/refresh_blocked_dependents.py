"""CLI for refreshing blocked work items whose dependencies are now satisfied."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.dependency_gate import refresh_all_blocked_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh blocked items whose dependency gates are now satisfied")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        released = refresh_all_blocked_items(session, repo_root=args.repo_root)
        session.commit()
    print(json.dumps({"released_items": released, "released_count": len(released)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
