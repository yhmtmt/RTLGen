"""CLI for direct Layer 2 campaign task generation."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.l2_task_generator import Layer2CampaignGenerateRequest, generate_l2_campaign_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Layer 2 campaign work item directly into the control-plane DB")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--campaign-path", required=True)
    parser.add_argument("--platform")
    parser.add_argument("--requested-by", default="control_plane")
    parser.add_argument("--priority", type=int, default=1)
    parser.add_argument("--item-id")
    parser.add_argument("--title")
    parser.add_argument("--objective")
    parser.add_argument("--source-commit")
    parser.add_argument("--mode", default="upsert")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--batch-id")
    parser.add_argument("--objective-profiles-json")
    parser.add_argument("--no-run-physical", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = generate_l2_campaign_task(
            session,
            Layer2CampaignGenerateRequest(
                repo_root=args.repo_root,
                campaign_path=args.campaign_path,
                platform=args.platform,
                requested_by=args.requested_by,
                priority=args.priority,
                item_id=args.item_id,
                title=args.title,
                objective=args.objective,
                source_commit=args.source_commit,
                mode=args.mode,
                run_physical=not args.no_run_physical,
                jobs=args.jobs,
                batch_id=args.batch_id,
                objective_profiles_json=args.objective_profiles_json,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
