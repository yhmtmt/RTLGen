#!/usr/bin/env python3
"""Tests for quality-gate wiring in the physical HBM frontier estimator."""

import json
from pathlib import Path

import npu.eval.estimate_llm_decoder_attention_kv_physical_hbm_frontier as estimator


def _write_quality_payload(path: Path) -> None:
    payload = {
        "version": 0.2,
        "model": {
            "model_id": "mock/7b",
            "attention_heads": 32,
            "kv_heads": 4,
            "gqa_group_size": 8.0,
            "device": "cpu",
            "dtype": "float16",
            "requested_dtype": "auto",
        },
        "decision": {
            "status": "native_checkpoint_kv4_promising",
            "blockers": ["minor concern"],
            "cautions": ["check top-k sensitivity"],
            "next_step": "validate at larger scale",
        },
        "candidate_summary": [
            {
                "kv_bits": 4,
                "kv_granularity": "tensor",
                "comparison_count": 128,
                "top1_match_rate": 0.992,
                "topk_contains_rate": 0.999,
                "mean_logit_cosine": 0.9992,
                "mean_probability_kl": 0.0015,
                "min_reference_margin": 0.11,
                "max_abs_logit_delta_max": 0.009,
            },
            {
                "kv_bits": 8,
                "kv_granularity": "token_vector",
                "comparison_count": 128,
                "top1_match_rate": 0.999,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.9999,
                "mean_probability_kl": 0.0005,
                "min_reference_margin": 0.21,
                "max_abs_logit_delta_max": 0.003,
            },
        ],
        "best_kv4_candidate": {
            "kv_bits": 4,
            "kv_granularity": "tensor",
            "comparison_count": 128,
            "top1_match_rate": 0.992,
            "topk_contains_rate": 0.999,
            "mean_logit_cosine": 0.9992,
            "mean_probability_kl": 0.0015,
            "min_reference_margin": 0.11,
            "max_abs_logit_delta_max": 0.009,
        },
    }
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _build_payload_with_quality(quality_path: Path) -> estimator.JsonDict:
    quality_gate = estimator._load_quality_gate_json(str(quality_path))
    return estimator.build_report(
        label="llama7b_proxy",
        sequence_length_list=[4096],
        die_area_mm2_list=[100.0],
        kv_sharing_list=["gqa8"],
        kv_bits_list=[8],
        stack_count_list=[1],
        pseudo_channels_per_stack_list=[8],
        pseudo_channel_width_bits_list=[64],
        data_rate_mtps_list=[3200],
        hbm_efficiency_list=[0.6],
        tile_tokens_list=[512],
        prefetch_distance_tiles_list=[4],
        hbm_outstanding_list=[8],
        arbitration_efficiency_list=[0.9],
        virtual_channel_list=[4],
        prefetch_start_list=["during_qkv"],
        sram_area_fraction_list=[0.6],
        usable_sram_fraction_list=[0.7],
        bitcell_area_um2_per_bit_list=[0.02],
        local_sram_fraction_list=[0.25],
        bank_count_list=[16],
        bank_bandwidth_bytes_per_cycle_list=[1024.0],
        bank_interleave_tokens_list=[16],
        bank_conflict_efficiency_list=[0.75],
        noc_bandwidth_bytes_per_cycle_list=[16384.0],
        noc_hops_list=[1],
        router_latency_cycles_per_hop_list=[2],
        macs_per_cycle_list=[524288],
        vector_ops_per_cycle_list=[65536],
        clock_ns=1.0,
        quality_gate=quality_gate,
    )


def test_load_quality_gate_json_returns_compact_summary(tmp_path: Path) -> None:
    quality_path = tmp_path / "quality.json"
    _write_quality_payload(quality_path)

    summary = estimator._load_quality_gate_json(str(quality_path))

    assert summary["model"]["model_id"] == "mock/7b"
    assert summary["decision"]["status"] == "native_checkpoint_kv4_promising"
    assert summary["candidate_summary"]["kv4"][0]["kv_bits"] == 4
    assert summary["candidate_summary"]["kv8"][0]["kv_bits"] == 8
    assert summary["best_kv4_candidate"]["kv_bits"] == 4


def test_build_report_and_markdown_include_quality_gate_summary(tmp_path: Path) -> None:
    quality_path = tmp_path / "quality.json"
    _write_quality_payload(quality_path)
    out_md = tmp_path / "out.md"

    payload = _build_payload_with_quality(quality_path)
    assert payload["quality_gate"]["decision"]["status"] == "native_checkpoint_kv4_promising"
    assert payload["quality_gate"]["candidate_summary"]["kv4"][0]["kv_bits"] == 4

    estimator._write_markdown(out_md, payload)
    markdown = out_md.read_text(encoding="utf-8")
    assert "## Native KV Quality Gate Summary" in markdown
    assert "- status: `native_checkpoint_kv4_promising`" in markdown
    assert "### KV4 summary" in markdown
    assert "### best KV4 candidate" in markdown
