from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from npu.eval import recost_llm_decoder_attention_score32_global_hbm_exact_llama2_mha as recost


def _source_row() -> dict:
    return {
        "active_clusters": 16,
        "cluster_count": 16,
        "sequence_length": 131072,
        "tile_tokens": 1024,
        "tile_count": 128,
        "tile_waves": 8,
        "hidden_size": 4096,
        "attention_heads": 32,
        "kv_heads": 4,
        "kv_bits": 8,
        "kv_sharing": "gqa8",
        "shared_byte_share": 17408 / 1048576,
        "partial_reduction_payload_bytes": 8320,
        "cross_tile_reduction_payload_bytes": 133120,
        "cross_tile_reduction_cycles": 574,
        "tile_attention_cycles": 986,
        "qkv_cycles": 192,
        "kv_write_cycles": 10,
        "layer_cycles": 8664,
        "layers": 32,
        "measured_dual_stream_composed_clock_ns": 48.6509,
        "clock_ns": 5.9811,
        "replica_recost_macs_per_cycle": 109568,
        "measured_l1_profile": "test-profile",
        "noc_hops": 6,
        "topology": "mesh2d",
        "scheduler_policy": "locality_aware",
        "reduction_strategy": "cluster_tree",
        "onchip_shared_bytes_per_cluster": 17408,
    }


def _finite() -> dict:
    return {
        "version": 1,
        "profile": "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost",
        "model_contract": {
            "hidden_size": 4096,
            "layers": 32,
            "attention_heads": 32,
            "kv_heads": 4,
            "gqa_group_size": 8,
            "kv_sharing": "gqa8",
            "sequence_length": 131072,
        },
        "throughput": {"token_throughput_per_s": 74.0},
        "physical_recost": {
            "area_fit": True,
            "die_area_um2": 800_000_000.0,
            "total_embodied_area_um2": 760_000_000.0,
            "recost_logic_vectorless_power_mw": 26000.0,
        },
        "clock_contract": {"effective_noc_clock_ns": 1.0},
        "logical_schedule": {},
        "precision_contract": {"precision_profile": "score32-exp-lut"},
    }


def _controller() -> dict:
    return {
        "channel_count": 4,
        "channel_bandwidth_bytes_per_cycle": 1024.0,
        "burst_bytes": 1024,
        "row_span_bursts": 16,
        "row_hit_rate": 0.95,
        "request_overhead_cycles": 2,
        "row_miss_penalty_cycles": 8,
        "hbm_outstanding": 4,
        "scheduler_gap_cycles": 0,
        "scheduler_efficiency": 0.75,
    }


def _energy_params() -> dict:
    return {
        "read_hit_pj_per_byte": 2.0,
        "read_miss_pj_per_byte": 4.0,
        "write_pj_per_byte": 3.0,
        "activate_precharge_pj_per_row": 5.0,
        "command_pj_per_burst": 1.0,
        "source": "test",
    }


def _controller_ppa() -> dict:
    return {
        "artifact_item_id": "l1_hbm_controller",
        "area_mm2": 0.03,
        "power_mw": 0.1,
        "critical_path_ns": 2.0,
        "metrics_csv": "runs/designs/hbm/metrics.csv",
    }


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=tmp_path,
        source_recost_json=Path("source.json"),
        quality_frontier_json=Path("quality.json"),
        measured_l1_costs=Path("costs.json"),
        out=tmp_path / "out.json",
        report=tmp_path / "out.md",
        max_cycles=20_000_000,
    )


def test_projection_recomputes_mha_instead_of_scaling_qkv_by_eight() -> None:
    gqa8 = recost._projection_cycles(row=_source_row(), kv_heads=4)
    mha = recost._projection_cycles(row=_source_row(), kv_heads=32)

    assert gqa8["source_macs"] == 20_971_520
    assert gqa8["target_cycles"] == 192
    assert mha["target_macs"] == 50_331_648
    assert mha["target_cycles"] == 460
    assert mha["target_macs"] / gqa8["target_macs"] == 2.4


def test_global_hbm_service_replays_all_cluster_tiles_in_each_wave() -> None:
    service = recost._global_hbm_service(
        tile_hbm_bytes=1_000_000,
        active_clusters=16,
        controller=_controller(),
        hbm_clock_ns=5.0,
    )

    assert service["scope"] == "one_global_controller_shared_by_all_active_clusters"
    assert service["aggregate_wave_hbm_bytes"] == 16_000_000
    assert service["burst_count"] == 15625
    assert service["service_cycles"] > 1000
    assert service["service_time_ns"] == service["service_cycles"] * 5.0


def test_exact_mha_candidate_rebuilds_memory_compute_and_finite_release_schedule(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen_rows: list[dict] = []

    def fake_phase2(_args, *, packet_spec_output, source_row_override, source_artifact_override):
        seen_rows.append(dict(source_row_override))
        packet_spec_output.extend([object(), object()])
        return {"source_artifact_override": source_artifact_override}

    monkeypatch.setattr(recost.phase2_schedule, "build_report", fake_phase2)
    monkeypatch.setattr(
        recost,
        "_compact_schedule",
        lambda _payload, **_kwargs: {
            "scheduled_packet_count": 2,
            "scheduled_flit_count": 16,
        },
    )
    monkeypatch.setattr(recost, "descriptors_from_packet_specs", lambda _specs: [])
    monkeypatch.setattr(
        recost,
        "run_performance_replay",
        lambda _descriptors, max_cycles: {
            "packets": 2,
            "flits": 16,
            "cycles": 1000,
            "contention": 7,
        },
    )

    result = recost._candidate(
        args=_args(tmp_path),
        candidate_id="exact-mha",
        kv_heads=32,
        exact_llama2_structure=True,
        sequence_length=4096,
        native_context_match=True,
        finite=_finite(),
        source_row=_source_row(),
        controller=_controller(),
        controller_ppa=_controller_ppa(),
        energy_params=_energy_params(),
        fixed_shared_tile_bytes=17408,
    )

    schedule_row = seen_rows[0]
    assert schedule_row["kv_heads"] == 32
    assert schedule_row["kv_sharing"] == "mha"
    assert schedule_row["qkv_cycles"] == 460
    assert schedule_row["kv_write_cycles"] == 80
    assert schedule_row["sequence_length"] == 4096
    assert schedule_row["tile_count"] == 4
    assert schedule_row["active_clusters"] == 4
    assert schedule_row["tile_waves"] == 1
    assert schedule_row["kv_cache_mib"] == 1024.0
    assert result["memory"]["full_tile_bytes"] == 8_388_608
    assert result["memory"]["fixed_shared_tile_bytes"] == 17_408
    assert result["memory"]["tile_hbm_bytes"] == 8_371_200
    assert result["memory"]["tile_count"] == 4
    assert result["memory"]["read_bytes_per_token"] == 1_071_513_600
    assert result["memory"]["write_bytes_per_token"] == 262_144
    assert result["global_hbm_service"]["aggregate_wave_hbm_bytes"] == 33_484_800
    assert result["schedule"]["scheduled_packets"] == 2
    assert result["schedule"]["scheduled_flits"] == 16
    assert result["quality_contract"]["structural_model_match"] is True
    assert result["quality_contract"]["native_context_match"] is True
    assert result["quality_contract"]["promotable"] is False
    assert result["physical"]["hbm_controller_area_um2"] == 30_000.0
    assert result["physical"]["total_embodied_area_um2"] == 760_030_000.0
    assert result["energy"]["hbm_controller_vectorless_energy_mj_per_token"] > 0.0
    assert result["energy"]["total_proxy_energy_mj_per_token"] > result["energy"]["hbm_energy_mj_per_token"]


def test_controller_ppa_requires_the_measured_score32_row() -> None:
    payload = {
        "version": 1,
        "model": recost._QUALITY_FRONTIER_MODEL,
        "rows": [
            {
                "family": "score32_exp_lut_div",
                "score32_hbm_controller_replay_ppa": {
                    "artifact_item_id": "l1_hbm_controller",
                    "controller_area_mm2": 0.03,
                    "controller_power_mw": 0.1,
                    "critical_path_ns_best": 2.0,
                    "metrics_csv": "runs/designs/hbm/metrics.csv",
                },
            }
        ],
    }

    assert recost._controller_ppa(payload) == _controller_ppa()


def test_validation_rejects_structurally_mismatched_finite_source() -> None:
    finite = _finite()
    finite["model_contract"]["kv_heads"] = 8

    with pytest.raises(ValueError, match="32-head/4-KV-head"):
        recost._validate_inputs(
            finite=finite,
            source={"version": 1, "model": recost._SOURCE_MODEL, "best_requested": _source_row()},
            hbm_replay={"version": 1, "model": recost._HBM_REPLAY_MODEL, "best_latency": _controller()},
            hbm_energy={"version": 1, "model": recost._HBM_ENERGY_MODEL, "energy_params": _energy_params()},
        )
