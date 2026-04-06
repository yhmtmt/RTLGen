"""Tests for run-index query and comparative analytics."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.run_index_rows import RunIndexRow
from control_plane.services.run_index_query import (
    RunIndexQueryRequest,
    comparative_run_index,
    query_run_index,
)


def _seed_rows(session: Session) -> None:
    session.add_all(
        [
            RunIndexRow(
                index_order=1,
                circuit_type="terminal",
                design="sigmoid_fast",
                platform="nangate45",
                status="ok",
                critical_path_ns="1.10",
                die_area="90.0",
                total_power_mw="0.40",
                metrics_path="runs/designs/activations/sigmoid_fast/metrics.csv",
            ),
            RunIndexRow(
                index_order=2,
                circuit_type="terminal",
                design="sigmoid_backup",
                platform="nangate45",
                status="ok",
                critical_path_ns="1.30",
                die_area="95.0",
                total_power_mw="0.45",
                metrics_path="runs/designs/activations/sigmoid_backup/metrics.csv",
            ),
            RunIndexRow(
                index_order=3,
                circuit_type="terminal",
                design="tanh_fragile",
                platform="asap7",
                status="route_failed",
                critical_path_ns="",
                die_area="130.0",
                total_power_mw="",
                metrics_path="runs/designs/activations/tanh_fragile/metrics.csv",
            ),
            RunIndexRow(
                index_order=4,
                circuit_type="reduction",
                design="softmax_rowwise",
                platform="nangate45",
                status="ok",
                critical_path_ns="2.50",
                die_area="200.0",
                total_power_mw="0.80",
                metrics_path="runs/designs/reductions/softmax_rowwise/metrics.csv",
            ),
            RunIndexRow(
                index_order=5,
                circuit_type="npu_macros",
                design="comb_only_macro",
                platform="nangate45",
                status="ok",
                critical_path_ns="-1.0",
                die_area="62500.0",
                total_power_mw="0.00119",
                metrics_path="runs/designs/npu_macros/comb_only_macro/metrics.csv",
            ),
            RunIndexRow(
                index_order=6,
                circuit_type="reduction",
                design="softmax_rowwise",
                platform="nangate45",
                status="ok",
                critical_path_ns="2.80",
                die_area="210.0",
                total_power_mw="0.82",
                metrics_path="runs/designs/reductions/softmax_rowwise/metrics.csv",
            ),
        ]
    )
    session.commit()


def test_query_run_index_filters_and_sorts() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        _seed_rows(session)
        result = query_run_index(
            session,
            RunIndexQueryRequest(
                circuit_type="terminal",
                status="ok",
                design_query="sigmoid",
                sort_by="critical_path_ns",
                descending=False,
                limit=10,
            ),
        )

    assert result.total_count == 6
    assert result.filtered_count == 2
    assert result.available_filters["circuit_types"] == ["npu_macros", "reduction", "terminal"]
    assert [row["design"] for row in result.rows] == ["sigmoid_fast", "sigmoid_backup"]
    assert result.rows[0]["critical_path_ns"] == 1.10


def test_comparative_run_index_reports_leaders_and_failure_rates() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        _seed_rows(session)
        result = comparative_run_index(session, limit=10)

    assert result.summary["row_count"] == 6
    assert result.summary["ok_row_count"] == 5
    assert result.summary["platform_count"] == 2
    assert result.families[0]["circuit_type"] == "terminal"
    assert all(row["design"] != "comb_only_macro" for row in result.best_designs)
    assert all(row["design"] != "comb_only_macro" for row in result.family_leaders)
    assert result.best_designs[0]["design"] == "sigmoid_fast"
    assert any(row["circuit_type"] == "terminal" and row["design"] == "sigmoid_fast" for row in result.family_leaders)
    terminal_failure = next(row for row in result.failure_rates if row["circuit_type"] == "terminal")
    assert terminal_failure["fail_row_count"] == 1
    assert terminal_failure["row_count"] == 3
    variance = next(row for row in result.design_variance if row["design"] == "softmax_rowwise")
    assert variance["comparable_ok_count"] == 2
    assert round(float(variance["critical_path_mean_ns"]), 2) == 2.65
    assert round(float(variance["critical_path_range_ns"]), 2) == 0.30
    assert round(float(variance["critical_path_stddev_ns"]), 3) == 0.212
    hotspot = next(row for row in result.failure_hotspots if row["design"] == "tanh_fragile")
    assert hotspot["fail_row_count"] == 1
    assert hotspot["status_breakdown"] == {"route_failed": 1}
