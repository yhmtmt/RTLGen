import argparse
import json
from pathlib import Path

import pytest

from npu.eval import reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock as reroute


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _baseline() -> dict:
    return {
        "version": 2,
        "profile": "decoder_attention_score32_noc_phase2_schedule",
        "source_contract": {
            "coverage": "workload_complete",
            "active_clusters": 8,
            "cluster_count": 16,
            "declared_tile_waves": 8,
            "simulated_wave_count": 8,
            "compute_clock_ns": 48.6509,
            "noc_clock_ns": 1.0,
            "compute_layer_time_ns": 421511.3976,
        },
        "mapping": {"cluster_endpoints": list(range(8)), "root_endpoint": 15},
        "traffic_quantities": {
            "tile_count": 128,
            "simulated_tiles": 128,
            "shared_tile_payload_bytes": 8192,
            "partial_reduction_payload_bytes": 1024,
        },
        "schedule_parameters": {
            "wave_start_compute_cycles": [192] * 8,
            "wave_start_noc_cycles": [9341] * 8,
            "reduction_release_compute_cycles": [1178] * 8,
            "reduction_release_noc_cycles": [57311] * 8,
            "compute_to_noc_clock_ratio": 48.6509,
            "release_conversion": "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)",
        },
        "simulation": {
            "cycles_to_drain": 397004,
            "drain_time_ns": 397004.0,
            "drain_within_source_compute_layer_envelope": True,
            "drain_minus_compute_layer_time_ns": -24507.3976,
            "scheduled_packet_count": 512,
            "scheduled_flit_count": 92128,
            "delivered_flit_count": 92128,
            "router_contention_cycles": 36747,
            "endpoint_input_stall_cycles_total": 319772,
        },
    }


def _router(critical_path_ns: float) -> dict:
    return {
        "item_id": "l1_segmented_xy_mesh_noc_phase1_v1_r6",
        "task_type": "l1_sweep",
        "evaluation_record": {"physical_metrics_present": True, "timing_feasible": True},
        "proposals": [
            {
                "metrics_ref": {
                    "metrics_csv": "runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/metrics.csv"
                },
                "metric_summary": {
                    "critical_path_ns": critical_path_ns,
                    "die_area": 12000.0,
                    "total_power_mw": 0.4,
                },
            }
        ],
    }


def _rerouted(clock_ns: float) -> dict:
    cycles = int(round(397004.0 / clock_ns))
    drain_ns = cycles * clock_ns
    return {
        "version": 2,
        "profile": "decoder_attention_score32_noc_phase2_schedule",
        "source_contract": {
            "coverage": "workload_complete",
            "declared_tile_waves": 8,
            "simulated_wave_count": 8,
            "compute_clock_ns": 48.6509,
            "noc_clock_ns": clock_ns,
            "compute_layer_time_ns": 421511.3976,
        },
        "traffic_quantities": {"tile_count": 128, "simulated_tiles": 128},
        "schedule_parameters": {
            "wave_start_noc_cycles": [1] * 8,
            "reduction_release_noc_cycles": [2] * 8,
            "release_conversion": "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)",
        },
        "simulation": {
            "cycles_to_drain": cycles,
            "drain_time_ns": drain_ns,
            "drain_within_source_compute_layer_envelope": drain_ns <= 421511.3976,
            "drain_minus_compute_layer_time_ns": drain_ns - 421511.3976,
            "scheduled_packet_count": 512,
            "scheduled_flit_count": 92128,
            "delivered_flit_count": 92128,
            "router_contention_cycles": 100,
            "endpoint_input_stall_cycles_total": 200,
        },
    }


def _args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=root,
        source_json=Path("source.json"),
        measured_l1_costs=Path("costs.json"),
        baseline_schedule_json=reroute.DEFAULT_BASELINE_SCHEDULE,
        router_promotion_json=reroute.DEFAULT_ROUTER_PROMOTION,
        max_cycles=1000000,
        out=root / "out.json",
        report=root / "out.md",
    )


def test_reroute_records_raw_and_conservative_clocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    _write(tmp_path / reroute.DEFAULT_ROUTER_PROMOTION, _router(0.8))
    called: list[float] = []

    def fake_build(args: argparse.Namespace) -> dict:
        called.append(args.noc_clock_ns)
        return _rerouted(args.noc_clock_ns)

    monkeypatch.setattr(reroute.phase2_schedule, "build_report", fake_build)
    report = reroute.build_report(_args(tmp_path))

    assert called == [0.8, 1.0]
    assert report["clock_contract"]["absolute_1ns_cycle_timeline_reused"] is False
    assert report["cases"][0]["promotion_status"] == "diagnostic_primitive_clock_not_aggregate_mesh_closure"
    assert report["cases"][1]["promotion_status"] == "conservative_schedule_bound"
    assert report["cases"][1]["schedule"]["noc_clock_ns"] == pytest.approx(1.0)


def test_reroute_deduplicates_equal_slow_clock_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / reroute.DEFAULT_BASELINE_SCHEDULE, _baseline())
    _write(tmp_path / reroute.DEFAULT_ROUTER_PROMOTION, _router(1.4))
    called: list[float] = []

    def fake_build(args: argparse.Namespace) -> dict:
        called.append(args.noc_clock_ns)
        return _rerouted(args.noc_clock_ns)

    monkeypatch.setattr(reroute.phase2_schedule, "build_report", fake_build)
    report = reroute.build_report(_args(tmp_path))

    assert called == [1.4]
    assert all(case["schedule"]["noc_clock_ns"] == pytest.approx(1.4) for case in report["cases"])
    assert all(case["promotion_status"] == "conservative_schedule_bound" for case in report["cases"])


def test_reroute_rejects_noncanonical_baseline_item(tmp_path: Path) -> None:
    args = _args(tmp_path)
    args.baseline_schedule_json = Path("wrong.json")
    _write(tmp_path / args.baseline_schedule_json, _baseline())
    _write(tmp_path / reroute.DEFAULT_ROUTER_PROMOTION, _router(1.0))

    with pytest.raises(ValueError, match="phase2 item_id"):
        reroute.build_report(args)


def test_compact_schedule_accepts_an_explicit_workload_complete_shape() -> None:
    payload = _rerouted(1.0)
    payload["source_contract"]["declared_tile_waves"] = 1
    payload["source_contract"]["simulated_wave_count"] = 1
    payload["traffic_quantities"]["tile_count"] = 4
    payload["traffic_quantities"]["simulated_tiles"] = 4
    payload["schedule_parameters"]["wave_start_noc_cycles"] = [1]
    payload["schedule_parameters"]["reduction_release_noc_cycles"] = [2]

    compact = reroute._compact_schedule(
        payload,
        expected_wave_count=1,
        expected_tile_count=4,
    )

    assert compact["scheduled_flit_count"] == compact["delivered_flit_count"]
    assert compact["wave_start_noc_cycles"] == [1]
