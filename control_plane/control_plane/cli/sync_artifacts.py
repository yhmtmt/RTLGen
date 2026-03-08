"""Artifact-sync CLI for cp-009."""

from __future__ import annotations

import argparse
import json
import socket

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.reconciliation_service import ArtifactSyncRequest, sync_run_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync completed internal runs into repo-tracked evaluated queue snapshots")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--run-key")
    parser.add_argument("--evaluator-id", default="control_plane")
    parser.add_argument("--session-id")
    parser.add_argument("--host", default=socket.gethostname())
    parser.add_argument("--executor", default="@control_plane")
    parser.add_argument("--branch-name")
    parser.add_argument("--target-path")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = sync_run_artifacts(
            session,
            ArtifactSyncRequest(
                repo_root=args.repo_root,
                item_id=args.item_id,
                run_key=args.run_key,
                evaluator_id=args.evaluator_id,
                session_id=args.session_id,
                host=args.host,
                executor=args.executor,
                branch_name=args.branch_name,
                target_path=args.target_path,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
