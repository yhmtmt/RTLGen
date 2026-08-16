from __future__ import annotations

import argparse
import copy
from pathlib import Path

import pytest

from npu.eval import recost_llm_decoder_attention_score32_noc_phase2_finite_endpoint_composed as recost
from npu.eval.recost_llm_decoder_attention_score32_noc_phase2_finite_endpoint_composed import (
    _build_physical_recost,
    _validate_endpoint_equivalence,
)


def _baseline() -> dict:
    return {
        "simulation": {
            "scheduled_packet_count": 10,
            "scheduled_flit_count": 80,
            "cycles_to_drain": 123,
        }
    }


def _endpoint() -> dict:
    counters = {
        "packets": 10,
        "flits": 80,
        "cycles": 140,
        "contention": 7,
        "input_stalls": 9,
        "max_occupancy": 4,
    }
    return {
        "version": 1,
        "profile": "decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence",
        "coverage": "workload_complete",
        "source_schedule": {
            "packet_count": 10,
            "flit_count": 80,
            "logical_release_queue_cycles_to_drain": 123,
        },
        "rtl_replay": counters,
        "endpoint_aware_performance_replay": dict(counters),
        "equivalence": {
            "all_packets_completed": True,
            "all_flits_written": True,
            "rx_descriptor_precedes_tx_enforced": True,
            "cycle_and_router_counter_match": True,
            "wire_tag_width_bits": 8,
        },
    }


def test_validate_endpoint_equivalence_rejects_counter_mismatch() -> None:
    payload = _endpoint()
    payload["rtl_replay"]["cycles"] += 1

    with pytest.raises(ValueError, match="counters differ"):
        _validate_endpoint_equivalence(payload, baseline=_baseline())


def test_validate_endpoint_equivalence_rejects_source_schedule_mismatch() -> None:
    payload = _endpoint()
    payload["source_schedule"]["flit_count"] += 1

    with pytest.raises(ValueError, match="source schedule mismatch"):
        _validate_endpoint_equivalence(payload, baseline=_baseline())


def test_physical_recost_replaces_prior_primitives_without_double_counting() -> None:
    source = {
        "best_requested": {
            "cluster_count": 2,
            "noc_router_per_cluster": 1,
            "noc_router_area_um2": 10,
            "noc_router_power_mw": 1,
            "noc_fifo_per_cluster": 1,
            "noc_fifo_area_um2": 20,
            "noc_fifo_power_mw": 2,
            "onchip_endpoint_per_cluster": 1,
            "onchip_endpoint_area_um2": 30,
            "onchip_endpoint_power_mw": 3,
            "logic_area_used_um2": 1000,
            "replica_recost_compute_power_mw": 100,
            "measured_l1_overhead_power_mw": 20,
            "die_area_mm2": 0.002,
            "measured_shared_sram_used_area_um2": 100,
            "measured_tile_local_sram_area_um2": 200,
            "reserved_area_fraction": 0.1,
        }
    }
    composed = {"footprint_um2": 150, "vectorless_power_mw": 15}

    result = _build_physical_recost(
        source_recost=copy.deepcopy(source), composed=composed, token_time_ns=1_000_000
    )

    assert result["source_replaced_components"]["area_um2"] == 120
    assert result["source_replaced_components"]["power_mw"] == 12
    assert result["recost_logic_area_um2"] == 1030
    assert result["recost_logic_vectorless_power_mw"] == 123
    assert result["total_embodied_area_um2"] == 1530
    assert result["recost_logic_vectorless_energy_per_token_mj"] == pytest.approx(0.123)
    assert result["area_fit"] is True


def test_build_report_joins_finite_timing_physical_and_precision_contracts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    baseline = {
        "source_contract": {"noc_clock_ns": 1.0},
        "simulation": {
            "scheduled_packet_count": 10,
            "scheduled_flit_count": 80,
            "cycles_to_drain": 123,
        },
    }
    source = {
        "corrected_contract": {"layers": 32, "token_throughput_per_s": 100.0},
        "best_requested": {
            "cluster_count": 2,
            "noc_router_per_cluster": 1,
            "noc_router_area_um2": 10,
            "noc_router_power_mw": 1,
            "noc_fifo_per_cluster": 1,
            "noc_fifo_area_um2": 20,
            "noc_fifo_power_mw": 2,
            "onchip_endpoint_per_cluster": 1,
            "onchip_endpoint_area_um2": 30,
            "onchip_endpoint_power_mw": 3,
            "logic_area_used_um2": 1000,
            "replica_recost_compute_power_mw": 100,
            "measured_l1_overhead_power_mw": 20,
            "die_area_mm2": 0.002,
            "measured_shared_sram_used_area_um2": 100,
            "measured_tile_local_sram_area_um2": 200,
            "reserved_area_fraction": 0.1,
            "precision_profile": "exact-profile",
            "measured_dual_stream_composed_semantic_profile": "exact-semantics",
        },
    }
    endpoint = _endpoint()
    composed = {"critical_path_ns": 2.0, "footprint_um2": 150, "vectorless_power_mw": 15}

    def fake_load(path: Path) -> dict:
        name = path.name
        if "endpoint" in name:
            return endpoint
        if "promotion" in name:
            return composed
        if "source" in name:
            return source
        return baseline

    monkeypatch.setattr(recost, "_load_json", fake_load)
    monkeypatch.setattr(recost, "_validate_phase2_schedule", lambda payload, source_path: payload)
    monkeypatch.setattr(recost, "_validate_composed_promotion", lambda payload: payload)
    monkeypatch.setattr(
        recost.phase2_schedule,
        "build_report",
        lambda args, packet_spec_output: {
            "version": 2,
            "profile": "decoder_attention_score32_noc_phase2_schedule",
            "source_contract": {
                "coverage": "workload_complete",
                "declared_tile_waves": 8,
                "simulated_wave_count": 8,
                "noc_clock_ns": 2.0,
                "compute_clock_ns": 1.0,
                "compute_layer_time_ns": 500.0,
            },
            "traffic_quantities": {"tile_count": 128, "simulated_tiles": 128},
            "simulation": {
                "cycles_to_drain": 200,
                "drain_time_ns": 400.0,
                "drain_within_source_compute_layer_envelope": True,
                "drain_minus_compute_layer_time_ns": -100.0,
                "scheduled_packet_count": 10,
                "scheduled_flit_count": 80,
                "delivered_flit_count": 80,
                "router_contention_cycles": 7,
                "endpoint_input_stall_cycles_total": 9,
            },
            "schedule_parameters": {
                "wave_start_noc_cycles": [0],
                "reduction_release_noc_cycles": [1],
                "release_conversion": "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)",
            },
        },
    )
    monkeypatch.setattr(recost, "descriptors_from_packet_specs", lambda specs: [])
    monkeypatch.setattr(
        recost,
        "run_performance_replay",
        lambda packets, max_cycles: {
            "packets": 10,
            "flits": 80,
            "cycles": 300,
            "contention": 8,
            "input_stalls": 11,
            "max_occupancy": 5,
        },
    )
    args = argparse.Namespace(
        repo_root=tmp_path,
        source_json=Path("source.json"),
        measured_l1_costs=Path("costs.json"),
        baseline_schedule_json=Path("baseline.json"),
        endpoint_equivalence_json=Path("endpoint.json"),
        composed_promotion_json=Path("promotion.json"),
        max_cycles=1000,
        out=tmp_path / "out.json",
        report=tmp_path / "out.md",
    )

    result = recost.build_report(args)

    assert result["clock_contract"]["effective_noc_clock_ns"] == 2.0
    assert result["finite_endpoint_schedule"]["drain_time_ns"] == 600.0
    assert result["throughput"]["bottleneck"] == "finite_endpoint_noc"
    assert result["throughput"]["token_throughput_per_s"] == pytest.approx(52083.333333333336)
    assert result["physical_recost"]["recost_logic_area_um2"] == 1030
    assert result["precision_contract"]["precision_profile"] == "exact-profile"
    assert result["precision_contract"]["arithmetic_changed_by_this_recost"] is False
