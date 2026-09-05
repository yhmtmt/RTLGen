from __future__ import annotations

from unittest.mock import patch

from control_plane.cli.main import main
from control_plane.cli.operator_status import _render_section, _render_table


def _payload() -> dict[str, object]:
    return {
        "health_summary": {"message": "healthy", "status": "healthy"},
        "state_counts": {"ready": 0, "running": 0},
        "evaluator_machines": [
            {
                "machine_key": "eval-1",
                "hostname": "eval-host",
                "active": True,
                "active_slots": 0,
                "slot_capacity": 16,
                "assigned_ready": 0,
                "heartbeat_age_seconds": 4.5,
                "worker_attention": None,
            }
        ],
        "active_runs": [],
        "stale_leases": [],
        "recent_failures": [],
        "recent_submissions": [],
        "recent_resolver_cases": [],
    }


def test_operator_status_table_renders_live_evaluator_capacity() -> None:
    rendered = _render_table(_payload())
    assert "Evaluator Machines" in rendered
    assert "eval-1" in rendered
    assert "eval-host" in rendered
    assert "slot_capacity" in rendered
    assert "16" in rendered


def test_operator_status_evaluator_only_section() -> None:
    sections = _render_section(_payload(), "evaluator-machines")
    assert len(sections) == 1
    assert "Evaluator Machines" in sections[0]
    assert "eval-1" in sections[0]


def test_top_level_operator_status_forwards_evaluator_only_filter() -> None:
    with patch("control_plane.cli.main.operator_status_main", return_value=0) as status_main:
        result = main(
            [
                "operator-status",
                "--database-url",
                "sqlite+pysqlite:///:memory:",
                "--format",
                "json",
                "--only",
                "evaluator-machines",
            ]
        )
    assert result == 0
    forwarded = status_main.call_args.args[0]
    assert forwarded[forwarded.index("--only") + 1] == "evaluator-machines"
