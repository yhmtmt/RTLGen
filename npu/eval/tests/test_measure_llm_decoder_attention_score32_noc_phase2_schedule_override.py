from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as schedule


def _args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "source_json": Path("missing_source.json"),
        "measured_l1_costs": Path("measured_costs.json"),
        "wave_limit": None,
        "packet_payload_bytes": 256,
        "cluster_endpoints": [0, 1],
        "root_endpoint": 1,
        "shared_vc": 0,
        "reduction_vc": 1,
        "compute_clock_ns": None,
        "noc_clock_ns": 1.25,
        "max_cycles": 1000,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _source_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "active_clusters": 2,
        "cluster_count": 2,
        "sequence_length": 10,
        "tile_tokens": 5,
        "tile_waves": 1,
        "hidden_size": 16,
        "attention_heads": 4,
        "kv_heads": 3,
        "kv_bits": 8,
        "shared_byte_share": 0.25,
        "partial_reduction_payload_bytes": 7,
        "cross_tile_reduction_payload_bytes": 14,
        "tile_attention_cycles": 13,
        "qkv_cycles": 11,
        "layer_cycles": 29,
        "measured_dual_stream_composed_clock_ns": 2.5,
        "noc_hops": 1,
        "measured_l1_profile": "override-profile",
        "cross_tile_reduction_cycles": 4,
        "topology": "mesh4x4",
        "scheduler_policy": "phase2-static",
        "reduction_strategy": "root",
    }
    row.update(overrides)
    return row


def test_build_report_source_row_override_skips_source_json_and_controls_quantities(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    costs_path = tmp_path / "measured_costs.json"
    args = _args(tmp_path)
    load_calls: list[Path] = []

    def fake_load(path: Path) -> dict[str, object]:
        load_calls.append(path)
        if path == costs_path:
            return {
                "profiles": [
                    {
                        "name": "override-profile",
                        "latency_cycles": 99,
                        "area_um2": 123.0,
                    }
                ]
            }
        raise AssertionError(f"unexpected JSON load: {path}")

    monkeypatch.setattr(schedule, "_load_json", fake_load)

    report = schedule.build_report(
        args,
        source_row_override=_source_row(),
        source_artifact_override="inline://score32-override",
    )

    assert load_calls == [costs_path]
    assert report["source_artifacts"]["score32_recost_json"] == "inline://score32-override"
    assert report["source_artifacts"]["measured_l1_profile"] == "override-profile"
    assert report["source_contract"]["kv_heads"] == 3
    assert report["traffic_quantities"]["full_tile_bytes"] == 120
    assert report["traffic_quantities"]["shared_tile_payload_bytes"] == 30
    assert report["traffic_quantities"]["local_tile_payload_bytes"] == 90
    assert report["flow_summary"]["remote_shared_bytes"] == 60
    assert report["flow_summary"]["local_only_shared_bytes"] == 0
    assert report["flow_summary"]["remote_reduction_bytes"] == 7
    assert report["flow_summary"]["local_only_reduction_bytes"] == 7
    assert report["schedule_parameters"]["compute_qkv_cycles_before_wave0"] == 11
    assert report["schedule_parameters"]["compute_tile_attention_cycles_per_wave"] == 13
    assert report["schedule_parameters"]["wave_start_compute_cycles"] == [11]
    assert report["schedule_parameters"]["wave_start_noc_cycles"] == [22]
    assert report["schedule_parameters"]["reduction_release_compute_cycles"] == [24]
    assert report["schedule_parameters"]["reduction_release_noc_cycles"] == [48]
    assert report["source_contract"]["compute_layer_cycles"] == 29
    assert report["source_contract"]["compute_clock_ns"] == pytest.approx(2.5)
    assert report["source_contract"]["compute_layer_time_ns"] == pytest.approx(72.5)


def test_build_report_source_row_override_can_fall_back_to_args_source_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    costs_path = tmp_path / "measured_costs.json"
    args = _args(tmp_path, source_json=Path("kept_source_provenance.json"))

    def fake_load(path: Path) -> dict[str, object]:
        if path == costs_path:
            return {"profiles": [{"name": "override-profile"}]}
        raise AssertionError(f"unexpected JSON load: {path}")

    monkeypatch.setattr(schedule, "_load_json", fake_load)

    report = schedule.build_report(args, source_row_override=_source_row(kv_heads=1, shared_byte_share=0.5))

    assert report["source_artifacts"]["score32_recost_json"] == "kept_source_provenance.json"
    assert report["source_contract"]["kv_heads"] == 1
    assert report["traffic_quantities"]["shared_tile_payload_bytes"] == 20
    assert report["flow_summary"]["remote_shared_bytes"] == 40
