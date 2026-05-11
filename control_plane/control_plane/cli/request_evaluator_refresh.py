"""CLI for requesting remote evaluator source refresh and daemon restart."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from control_plane.services.evaluator_refresh_request import (
    EvaluatorRefreshRequest,
    request_evaluator_refresh,
)


def _current_commit(repo_root: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(Path(repo_root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Request evaluator source refresh and daemon restart")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--target-commit")
    parser.add_argument("--reason", default="control-plane source changed")
    parser.add_argument("--evaluator", default="remote evaluator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    target_commit = args.target_commit or _current_commit(args.repo_root)
    result = request_evaluator_refresh(
        EvaluatorRefreshRequest(
            repo=args.repo,
            target_commit=target_commit,
            reason=args.reason,
            evaluator=args.evaluator,
            dry_run=args.dry_run,
        )
    )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
