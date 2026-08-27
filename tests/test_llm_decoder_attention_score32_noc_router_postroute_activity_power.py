from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from npu.eval import (
    audit_llm_decoder_attention_score32_noc_router_postroute_activity_power as audit,
)


def _write_metrics(path: Path, *, effective_flow_variant: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "design",
                "platform",
                "param_hash",
                "effective_flow_variant",
                "status",
                "critical_path_ns",
                "die_area",
                "instance_area_um2",
                "total_power_mw",
                "params_json",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": "noc_segmented_mesh_router_node5_bare",
                "platform": "nangate45",
                "param_hash": "abc12345",
                "effective_flow_variant": effective_flow_variant,
                "status": "ok",
                "critical_path_ns": "1.75",
                "die_area": "500000",
                "instance_area_um2": "230000",
                "total_power_mw": "0.3",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 1.8,
                        "CORE_UTILIZATION": 50,
                        "PLACE_DENSITY": 0.52,
                        "FLOW_VARIANT": "router_node5_bare_v1",
                    }
                ),
            }
        )


def test_physical_rows_require_unique_isolated_flow_variant(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, effective_flow_variant="router_node5_bare_v1__abc12345")

    rows = audit._physical_rows(metrics)

    assert len(rows) == 1
    assert rows[0]["timing_feasible"] is True
    assert rows[0]["effective_flow_variant"] == "router_node5_bare_v1__abc12345"


def test_physical_rows_reject_shared_flow_variant(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, effective_flow_variant="router_node5_bare_v1")

    with pytest.raises(ValueError, match="isolated effective_flow_variant"):
        audit._physical_rows(metrics)


def test_measure_point_enforces_activity_gates_and_separates_clocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_power_report(**kwargs):
        assert kwargs["flow_variant"] == "router_node5_bare_v1__abc12345"
        assert kwargs["min_sequential_register_activity_coverage"] == 0.95
        return {
            "promotion_gate_pass": True,
            "phases": [
                {
                    "annotation_gate_pass": True,
                    "sequential_register_activity_gate_pass": True,
                    "clock_period_gate_pass": True,
                    "power_numeric_gate_pass": True,
                    "structural_macro_activity_gate_pass": True,
                    "phase_gate_pass": True,
                    "macro_activity_assignment_count": 0,
                    "measured_cycles": 100,
                    "full_context_cycles": 100,
                    "power": {
                        "internal_w": 0.10,
                        "switching_w": 0.20,
                        "leakage_w": 0.01,
                        "total_w": 0.31,
                    },
                }
            ],
        }

    monkeypatch.setattr(audit, "build_power_report", fake_power_report)
    physical = {
        "param_hash": "abc12345",
        "effective_flow_variant": "router_node5_bare_v1__abc12345",
        "target_clock_ns": 1.8,
        "core_utilization_pct": 50.0,
        "place_density": 0.52,
        "critical_path_ns": 1.75,
        "timing_feasible": True,
        "die_area_um2": 500000.0,
        "instance_area_um2": 230000.0,
        "vectorless_power_mw": 0.3,
    }

    row = audit._measure_point(
        physical=physical,
        activity_manifest={"clock_period_ns": 1.8},
        activity_manifest_path=tmp_path / "activity.json",
        orfs_design_config=tmp_path / "config.mk",
    )

    assert row["annotation_clock_ns"] == 1.8
    assert row["promotion_clock_ns"] == 1.8
    assert row["replay_energy_j"]["dynamic"] == pytest.approx(5.4e-8)
    assert row["replay_energy_j"]["leakage"] == pytest.approx(1.8e-9)
