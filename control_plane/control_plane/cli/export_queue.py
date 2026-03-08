"""Queue export CLI for cp-006."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.queue_exporter import QueueExportRequest, export_queue_item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a control-plane work item into queue JSON")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--target-state", required=True, choices=["queued", "evaluated"])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--target-path")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = export_queue_item(
            session,
            QueueExportRequest(
                repo_root=args.repo_root,
                item_id=args.item_id,
                target_state=args.target_state,
                target_path=args.target_path,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
