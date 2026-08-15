import argparse
import json
from pathlib import Path

import pytest

from npu.eval import reroute_llm_decoder_attention_score32_noc_phase2_composed_mesh as reroute
from tests.test_reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock import (
    _baseline,
    _rerouted,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _composed(
    *,
    critical_path_ns: float = 1.4,
    design: str = "l1_noc_sram_packet_mesh4x4_composed_ppa_harness_wrapper",
) -> dict:
    return {
        "item_id": "l1_noc_sram_packet_mesh4x4_composed_ppa_v1",
        "task_type": "l1_sweep",
        "evaluation_record": {"physical_metrics_present": True, "timing_feasible": True},
        "proposals": [
            {
                "metrics_ref": {
                    "design": design,
                    "metrics_csv": f"runs/designs/noc/{design}/metrics.csv",
                    "param_hash": "abcd1234",
                },
                "metric_summary": {
                    "critical_path_ns": critical_path_ns,
                    "die_area": 10_240_000.0,
                    "total_power_mw": 12.5,
                },
            }
        ],
    }


def _args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=root,
        source_json=Path("source.json"),
        measured_l1_costs=Path("costs.json"),
        baseline_schedule_json=reroute.DEFAULT_BASELINE_SCHEDULE,
        composed_promotion_json=reroute.DEFAULT_COMPOSED_PROMOTION,
        max_cycles=1_000_000,
        out=root / "out.json",
        report=root / "out.md",
    )


def test_composed_mesh_reroutes_full_schedule_and_accounts_aggregate_ppa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    _write(tmp_path / reroute.DEFAULT_COMPOSED_PROMOTION, _composed(critical_path_ns=1.4))
    called: list[float] = []

    def fake_build(args: argparse.Namespace) -> dict:
        called.append(args.noc_clock_ns)
        return _rerouted(args.noc_clock_ns)

    monkeypatch.setattr(reroute.phase2_schedule, "build_report", fake_build)
    report = reroute.build_report(_args(tmp_path))

    assert called == [1.4]
    assert report["profile"] == "decoder_attention_score32_noc_phase2_composed_mesh_reroute"
    assert report["schedule"]["scheduled_flit_count"] == report["schedule"]["delivered_flit_count"]
    assert report["physical_accounting"]["footprint_um2"] == pytest.approx(10_240_000.0)
    assert report["physical_accounting"]["vectorless_drain_energy_mj"] == pytest.approx(
        12.5 * report["schedule"]["drain_time_ns"] / 1.0e9
    )
    assert report["closure_flags"]["aggregate_wiring_and_congestion_included"] is True
    assert report["closure_flags"]["sram_bitcells_included"] is False


def test_composed_mesh_keeps_source_clock_floor_when_logic_is_faster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    _write(tmp_path / reroute.DEFAULT_COMPOSED_PROMOTION, _composed(critical_path_ns=0.7))
    called: list[float] = []

    def fake_build(args: argparse.Namespace) -> dict:
        called.append(args.noc_clock_ns)
        return _rerouted(args.noc_clock_ns)

    monkeypatch.setattr(reroute.phase2_schedule, "build_report", fake_build)
    report = reroute.build_report(_args(tmp_path))

    assert called == [1.0]
    assert report["clock_contract"]["effective_noc_clock_ns"] == pytest.approx(1.0)


def test_composed_mesh_rejects_wrong_physical_design(tmp_path: Path) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    _write(tmp_path / reroute.DEFAULT_COMPOSED_PROMOTION, _composed(design="unrelated_router"))

    with pytest.raises(ValueError, match="expected endpoint/mesh design"):
        reroute.build_report(_args(tmp_path))


def test_composed_mesh_rejects_noncanonical_promotion_item(tmp_path: Path) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    promotion = _composed()
    promotion["item_id"] = "wrong"
    _write(tmp_path / reroute.DEFAULT_COMPOSED_PROMOTION, promotion)

    with pytest.raises(ValueError, match="item_id mismatch"):
        reroute.build_report(_args(tmp_path))
