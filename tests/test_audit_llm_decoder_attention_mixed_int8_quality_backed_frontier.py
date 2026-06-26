#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_mixed_int8_quality_backed_frontier import (  # noqa: E402
    build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        mixed_int8_energy_closure_json=tmp_path / "energy.json",
        mixed_int8_broad_native_quality_json=tmp_path / "quality.json",
        mixed_int8_generation_quality_json=None,
        out=tmp_path / "out.json",
        out_md=tmp_path / "out.md",
    )


def _quality_payload() -> dict:
    return {
        "candidate_summaries": [
            {
                "candidate_id": "qkv8_float_exact",
                "comparison_count": 4,
                "decision_status": "mixed_int8_native_attention_shadow_pass",
                "q_bits": 8,
                "k_bits": 8,
                "v_bits": 8,
                "score_bits": 24,
                "weight_bits": 16,
                "softmax_mode": "float_exact",
                "top1_match_rate": 1.0,
                "topk_contains_rate": 1.0,
                "mean_probability_kl": 0.001,
                "mean_logit_cosine": 0.999,
            }
        ]
    }


def _energy_payload() -> dict:
    return {
        "best": {
            "candidate_id": "candidate_1",
            "precision_profile": "q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute",
            "latency_us": 10.0,
            "token_throughput_per_s": 100.0,
            "energy_mj": 5.0,
        },
        "pareto_rows": [
            {
                "candidate_id": "candidate_1",
                "precision_profile": "q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute",
                "latency_us": 10.0,
                "token_throughput_per_s": 100.0,
                "energy_mj": 5.0,
            }
        ],
    }


def test_quality_backed_frontier_without_generation_quality_remains_deterministic(tmp_path: Path) -> None:
    args = _args(tmp_path)
    _write_json(args.mixed_int8_energy_closure_json, _energy_payload())
    _write_json(args.mixed_int8_broad_native_quality_json, _quality_payload())

    output = build_payload(args)

    assert output["quality_backed_direction"]["status"] == "quality_pass_requires_energy_recost"
    assert output["diagnosis"]["score32_generation_quality_summary"] is None
    assert output["diagnosis"]["score32_generation_quality_pass"] is False
    assert output["diagnosis"]["invalidated_energy_candidate_count"] == 1
    assert "Recompute the Llama7B energy frontier" in output["diagnosis"]["recommended_next_step"]
    assert "mixed_int8_generation_quality_json" not in output["inputs"]


def test_quality_backed_frontier_with_score32_generation_quality_pass_drives_recost_text(tmp_path: Path) -> None:
    args = _args(tmp_path)
    generation = tmp_path / "generation_quality.json"
    args.mixed_int8_generation_quality_json = generation

    _write_json(args.mixed_int8_energy_closure_json, _energy_payload())
    _write_json(args.mixed_int8_broad_native_quality_json, _quality_payload())
    _write_json(
        generation,
        {
            "candidate_summaries": [
                {
                    "candidate_id": "score32_float",
                    "decision_status": "mixed_int8_generation_quality_pass",
                    "free_run_exact_match_rate": 0.75,
                    "free_run_token_match_rate": 0.84375,
                    "teacher_forced_mean_nll_delta": 0.00233,
                    "teacher_forced_candidate_reference_token_prob_mean": 0.4489,
                },
                {
                    "candidate_id": "other",
                    "decision_status": "mixed_int8_generation_quality_hold",
                },
            ]
        },
    )

    output = build_payload(args)

    assert output["decision"] == "mixed_int8_quality_backed_frontier_recost_required"
    assert output["diagnosis"]["score32_generation_quality_pass"] is True
    assert output["diagnosis"]["score32_generation_quality_summary"]["candidate_id"] == "score32_float"
    assert output["diagnosis"]["score32_generation_quality_summary"]["free_run_token_match_rate"] == 0.84375
    assert output["quality_backed_direction"]["status"] == "quality_pass_requires_energy_recost"
    assert output["quality_backed_direction"]["rankable_for_energy_frontier"] is False
    assert "score32_float" in output["quality_backed_direction"]["recost_requirement"]
    assert "generation/NLL evidence is passing for candidate score32_float" in output["diagnosis"]["recommended_next_step"]
    assert "mixed_int8_generation_quality_json" in output["inputs"]
