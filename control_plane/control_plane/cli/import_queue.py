"""Queue import CLI for cp-003."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.queue_importer import QueueImportRequest, import_queue_item


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a queue item into the RTLGen control-plane DB")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--queue-path", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--mode", default="upsert")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = import_queue_item(
            session,
            QueueImportRequest(
                repo_root=args.repo_root,
                queue_path=args.queue_path,
                source_commit=args.source_commit,
                mode=args.mode,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
