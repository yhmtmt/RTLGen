"""CLI for direct Layer 1 sweep task generation."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.l1_task_generator import Layer1SweepGenerateRequest, generate_l1_sweep_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Layer 1 sweep work item directly into the control-plane DB")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--sweep-path", required=True)
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--requested-by", default="control_plane")
    parser.add_argument("--priority", type=int, default=1)
    parser.add_argument("--item-id")
    parser.add_argument("--title")
    parser.add_argument("--objective")
    parser.add_argument("--source-commit")
    parser.add_argument("--mode", default="upsert")
    parser.add_argument("--proposal-id")
    parser.add_argument("--proposal-path")
    parser.add_argument("--make-target")
    parser.add_argument("--evaluation-mode")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = generate_l1_sweep_task(
            session,
            Layer1SweepGenerateRequest(
                repo_root=args.repo_root,
                sweep_path=args.sweep_path,
                config_paths=list(args.configs),
                platform=args.platform,
                out_root=args.out_root,
                requested_by=args.requested_by,
                priority=args.priority,
                item_id=args.item_id,
                title=args.title,
                objective=args.objective,
                source_commit=args.source_commit,
                mode=args.mode,
                proposal_id=args.proposal_id,
                proposal_path=args.proposal_path,
                make_target=args.make_target,
                evaluation_mode=args.evaluation_mode,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
