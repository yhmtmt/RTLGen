"""CLI for reporting terminal failed runs as GitHub issues."""

from __future__ import annotations

import argparse
import json

from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.services.failure_issue_reporter import FailureIssueReportRequest, report_failure_issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Report terminal failed runs as GitHub issues')
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--max-items', type=int)
    args = parser.parse_args(argv)

    engine = build_engine(args.database_url)
    create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as session:
        result = report_failure_issues(
            session,
            FailureIssueReportRequest(
                repo=args.repo,
                max_items=args.max_items,
            ),
        )
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    return 0 if not result.errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
