"""Top-level CLI coverage for evaluator refresh requests."""

from __future__ import annotations

from unittest.mock import patch

from control_plane.cli.main import main


def test_top_level_request_evaluator_refresh_forwards_operator_status_flags() -> None:
    with patch("control_plane.cli.main.request_evaluator_refresh_main", return_value=0) as request_refresh:
        result = main(
            [
                "request-evaluator-refresh",
                "--repo",
                "yhmtmt/RTLGen",
                "--repo-root",
                "/repo",
                "--target-commit",
                "abcdef",
                "--database-url",
                "postgresql+psycopg://rtlgen:rtlgen@localhost/rtlgen_control_plane",
                "--include-operator-status",
                "--machine-key",
                "eval-daemon",
                "--recent-limit",
                "5",
                "--dry-run",
            ]
        )

    assert result == 0
    forwarded = request_refresh.call_args.args[0]
    assert forwarded[forwarded.index("--repo") + 1] == "yhmtmt/RTLGen"
    assert forwarded[forwarded.index("--repo-root") + 1] == "/repo"
    assert forwarded[forwarded.index("--target-commit") + 1] == "abcdef"
    assert forwarded[forwarded.index("--database-url") + 1].startswith("postgresql+psycopg://")
    assert forwarded[forwarded.index("--machine-key") + 1] == "eval-daemon"
    assert forwarded[forwarded.index("--recent-limit") + 1] == "5"
    assert "--include-operator-status" in forwarded
    assert "--dry-run" in forwarded
