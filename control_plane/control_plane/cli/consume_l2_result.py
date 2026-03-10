"""CLI for Layer 2 result consumption."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consume a completed Layer 2 campaign result and emit a decision proposal")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--item-id")
    parser.add_argument("--run-key")
    parser.add_argument("--target-path")
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = consume_l2_result(
            session,
            Layer2ConsumeRequest(
                repo_root=args.repo_root,
                item_id=args.item_id,
                run_key=args.run_key,
                target_path=args.target_path,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
