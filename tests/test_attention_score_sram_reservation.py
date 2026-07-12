import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_exp_lut_sram_hierarchy_envelope import (
    _build_row,
    _macro_library,
    _score_buffer_profile,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "runs" / "datasets" / "llm_decoder_eval_gpt2_prompt_stress_v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_measured_score_sram_reservation_matches_llama7b_stream() -> None:
    profile = _score_buffer_profile(
        metrics_path=ROOT / "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics.json",
        macro_name="kv_tile_read_buffer",
        score_buffer_bytes=16 * 1024 * 1024,
        attention_heads=32,
        score_block_bytes=32,
    )

    assert profile["macro_width_bits"] == 256
    assert profile["macros_per_head"] == 1
    assert profile["macro_count"] == 32
    assert profile["allocated_capacity_bytes"] == 16 * 1024 * 1024
    assert profile["macro_area_um2"] == 66_636_897.2928
    assert profile["access_time_ns"] == 1.4124
    assert profile["read_accesses_per_token"] == 32 * 16384
    assert profile["write_accesses_per_token"] == 32 * 16384
    assert profile["total_energy_mj_per_token"] == 0.277849571328


def test_score_sram_is_reserved_before_nominal_kv_packing() -> None:
    local_capacity = _load(
        DATASET
        / "decoder_attention_local_sram_capacity__l2_decoder_attention_local_sram_capacity_llama7b_v1.json"
    )
    measured_sram = _load(
        DATASET
        / "decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json"
    )
    composition = _load(
        DATASET
        / "decoder_attention_kv_endpoint_router_sram_composition__l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json"
    )
    service_closure = _load(
        DATASET
        / "decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json"
    )
    score_buffer = _score_buffer_profile(
        metrics_path=ROOT / "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics.json",
        macro_name="kv_tile_read_buffer",
        score_buffer_bytes=16 * 1024 * 1024,
        attention_heads=32,
        score_block_bytes=32,
    )

    row = _build_row(
        efficiency=0.75,
        placement_overhead_fraction=0.05,
        score32_row=service_closure["selected_score32_row"],
        measured_sram_row=measured_sram["best"],
        composition_quantities=composition["composition_quantities"],
        local_capacity_payload=local_capacity,
        macros=_macro_library(local_capacity),
        score_buffer=score_buffer,
        clock_period_ns=10.0,
    )

    assert row["score_buffer_fits_macro_budget"] is True
    assert row["score_buffer_meets_clock"] is True
    assert row["shared_sram_capacity_mib"] == 29.015625
    assert row["hbm_byte_share"] == 0.992916107
    assert row["projected_latency_us_hbm_share_scaled"] == 12640.508864

    baseline = _build_row(
        efficiency=0.75,
        placement_overhead_fraction=0.05,
        score32_row=service_closure["selected_score32_row"],
        measured_sram_row=measured_sram["best"],
        composition_quantities=composition["composition_quantities"],
        local_capacity_payload=local_capacity,
        macros=_macro_library(local_capacity),
    )
    assert baseline["shared_sram_capacity_mib"] == 47.8125
    assert baseline["hbm_byte_share"] == 0.988327026
