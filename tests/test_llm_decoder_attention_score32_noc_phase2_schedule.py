import argparse
import json
from pathlib import Path

import pytest

from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (
    DEFAULT_MEASURED_L1_COSTS,
    DEFAULT_SOURCE_JSON,
    build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "repo_root": REPO_ROOT,
        "source_json": DEFAULT_SOURCE_JSON,
        "measured_l1_costs": DEFAULT_MEASURED_L1_COSTS,
        "wave_limit": None,
        "packet_payload_bytes": 256,
        "cluster_endpoints": None,
        "root_endpoint": 15,
        "shared_vc": 0,
        "reduction_vc": 1,
        "compute_clock_ns": None,
        "noc_clock_ns": 1.0,
        "max_cycles": 1000000,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_score32_noc_phase2_default_report_covers_full_declared_workload() -> None:
    report = build_report(_args())

    assert report["profile"] == "decoder_attention_score32_noc_phase2_schedule"
    assert report["version"] == 2
    assert report["source_contract"]["coverage"] == "workload_complete"
    assert report["source_contract"]["simulated_wave_count"] == report["source_contract"]["declared_tile_waves"]
    assert report["traffic_quantities"]["simulated_tiles"] == report["traffic_quantities"]["tile_count"]
    assert report["flow_summary"]["remote_shared_flow_count"] > 0
    assert report["flow_summary"]["remote_reduction_flow_count"] > 0
    assert report["simulation"]["delivered_flit_count"] == report["simulation"]["scheduled_flit_count"]
    assert report["source_contract"]["compute_clock_ns"] == pytest.approx(48.6509)
    assert report["source_contract"]["noc_clock_ns"] == pytest.approx(1.0)
    assert report["schedule_parameters"]["wave_start_compute_cycles"][0] == 192
    assert report["schedule_parameters"]["wave_start_noc_cycles"][0] == 9341
    assert report["schedule_parameters"]["wave_start_noc_cycles"][1] == 57311
    assert report["simulation"]["drain_time_ns"] == pytest.approx(
        report["simulation"]["cycles_to_drain"]
    )
    assert report["source_contract"]["compute_layer_time_ns"] == pytest.approx(8664 * 48.6509)
    assert report["simulation"]["drain_within_source_compute_layer_envelope"] is True
    assert report["simulation"]["drain_minus_compute_layer_time_ns"] < 0.0
    assert report["simulation"]["router_contention_cycles"] > 0
    assert report["tag_semantics"]["collision_free_reuse_proven"] is True
    assert report["tag_semantics"]["concrete_wire_tags_simulated"] is True
    assert report["tag_semantics"]["schedule_order_is_independent_of_wire_tag"] is True
    assert report["tag_semantics"]["ordered_tuple_stream_proven"] is True
    assert report["tag_semantics"]["max_packets_per_tuple"] > 256
    assert any(
        summary["tag_reuse_count"] > 0
        for summary in report["tag_semantics"]["tuple_summaries"]
    )
    assert any(
        summary["overlap_checked_count"] > 0
        for summary in report["tag_semantics"]["tuple_summaries"]
    )
    assert all(
        summary["min_nonoverlap_gap_cycles"] is None or summary["min_nonoverlap_gap_cycles"] > 0
        for summary in report["tag_semantics"]["tuple_summaries"]
    )
    assert any(
        "HBM/DRAM timing is intentionally excluded" in item
        for item in report["explicit_assumptions"]
    )


def test_score32_noc_phase2_explicit_wave_limit_is_bounded() -> None:
    packet_specs = []
    report = build_report(_args(wave_limit=1), packet_spec_output=packet_specs)

    assert report["source_contract"]["coverage"] == "bounded"
    assert report["source_contract"]["simulated_wave_count"] == 1
    assert report["traffic_quantities"]["simulated_tiles"] == report["source_contract"]["active_clusters"]
    assert report["schedule_parameters"]["requested_wave_limit"] == 1
    assert len(packet_specs) == report["simulation"]["scheduled_packet_count"]


def test_score32_noc_phase2_converts_absolute_release_times_between_clock_domains() -> None:
    report = build_report(_args(wave_limit=1, compute_clock_ns=10.0, noc_clock_ns=4.0))

    schedule = report["schedule_parameters"]
    assert schedule["compute_to_noc_clock_ratio"] == pytest.approx(2.5)
    assert schedule["wave_start_compute_cycles"] == [192]
    assert schedule["wave_start_noc_cycles"] == [480]
    assert schedule["reduction_release_compute_cycles"] == [1178]
    assert schedule["reduction_release_noc_cycles"] == [2945]
    assert schedule["release_conversion"] == "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)"


def test_score32_noc_phase2_proves_nonoverlapping_8bit_tag_reuse() -> None:
    report = build_report(_args(wave_limit=1))

    assert report["tag_semantics"]["tag_width_bits"] == 8
    assert report["tag_semantics"]["collision_free_reuse_proven"] is True
    assert report["tag_semantics"]["tuple_summaries"]
    assert report["tag_semantics"]["ordered_tuple_stream_proven"] is True
    assert all(
        summary["tag_reuse_count"] == 0
        for summary in report["tag_semantics"]["tuple_summaries"]
    )
    assert all(
        summary["overlap_checked_count"] == 0
        for summary in report["tag_semantics"]["tuple_summaries"]
    )


def test_score32_noc_phase2_rejects_missing_quantity(tmp_path: Path) -> None:
    source = json.loads((REPO_ROOT / DEFAULT_SOURCE_JSON).read_text(encoding="utf-8"))
    del source["best_requested"]["tile_waves"]
    broken = tmp_path / "broken_source.json"
    broken.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="tile_waves"):
        build_report(_args(source_json=broken))
