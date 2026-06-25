#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_mixed_int8_score_margin import (  # noqa: E402
    DECISION_NARROW_HOLD,
    DECISION_PASS,
    DECISION_SYSTEMATIC_HOLD,
    build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        score_precision_recovery_json=tmp_path / "score_precision_recovery.json",
        out=tmp_path / "out.json",
        out_md=tmp_path / "out.md",
    )


def test_audit_classifies_narrow_and_systematic_by_margin_bucket(tmp_path: Path) -> None:
    payload = {
        "candidate_summaries": [
            {
                "candidate_id": "candidate_narrow",
                "q_bits": 8,
                "k_bits": 8,
                "v_bits": 8,
                "score_bits": 8,
                "weight_bits": 8,
                "softmax_mode": "float_quantized",
                "top1_match_rate": 0.5,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.999,
                "mean_probability_kl": 0.01,
                "max_abs_logit_delta": 0.2,
            },
            {
                "candidate_id": "candidate_systematic",
                "q_bits": 8,
                "k_bits": 8,
                "v_bits": 8,
                "score_bits": 16,
                "weight_bits": 12,
                "softmax_mode": "pwl_recip_lut_q16_bucket8",
                "top1_match_rate": 0.0,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.99,
                "mean_probability_kl": 0.09,
                "max_abs_logit_delta": 1.7,
            },
            {
                "candidate_id": "candidate_pass",
                "q_bits": 8,
                "k_bits": 8,
                "v_bits": 8,
                "score_bits": 32,
                "weight_bits": 16,
                "softmax_mode": "float_quantized",
                "top1_match_rate": 1.0,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.9999,
                "mean_probability_kl": 0.001,
                "max_abs_logit_delta": 0.1,
            },
        ],
        "candidate_rows": [
            {"candidate_id": "candidate_narrow", "top1_match": 1.0, "topk_contains": 1.0, "reference_margin": 0.2, "logit_cosine": 0.999, "probability_kl": 0.001, "max_abs_logit_delta": 0.2},
            {"candidate_id": "candidate_narrow", "top1_match": 0.0, "topk_contains": 1.0, "reference_margin": 0.2, "logit_cosine": 0.998, "probability_kl": 0.002, "max_abs_logit_delta": 0.3},
            {"candidate_id": "candidate_narrow", "top1_match": 0.0, "topk_contains": 1.0, "reference_margin": 0.9, "logit_cosine": 0.998, "probability_kl": 0.003, "max_abs_logit_delta": 0.25},
            {"candidate_id": "candidate_narrow", "top1_match": 1.0, "topk_contains": 1.0, "reference_margin": 1.8, "logit_cosine": 0.999, "probability_kl": 0.001, "max_abs_logit_delta": 0.22},
            {"candidate_id": "candidate_systematic", "top1_match": 1.0, "topk_contains": 1.0, "reference_margin": 0.3, "logit_cosine": 0.996, "probability_kl": 0.002, "max_abs_logit_delta": 0.21},
            {"candidate_id": "candidate_systematic", "top1_match": 0.0, "topk_contains": 1.0, "reference_margin": 5.2, "logit_cosine": 0.992, "probability_kl": 0.019, "max_abs_logit_delta": 1.9},
            {"candidate_id": "candidate_pass", "top1_match": 1.0, "topk_contains": 1.0, "reference_margin": 0.1, "logit_cosine": 0.9997, "probability_kl": 0.001, "max_abs_logit_delta": 0.08},
            {"candidate_id": "candidate_pass", "top1_match": 1.0, "topk_contains": 1.0, "reference_margin": 0.4, "logit_cosine": 0.9996, "probability_kl": 0.0008, "max_abs_logit_delta": 0.06},
        ],
    }
    args = _args(tmp_path)
    _write_json(args.score_precision_recovery_json, payload)

    output = build_payload(args)
    by_id = {row["candidate_id"]: row for row in output["candidates"]}

    assert output["decision"]["status"] == DECISION_SYSTEMATIC_HOLD
    assert by_id["candidate_narrow"]["audit_status"] == DECISION_NARROW_HOLD
    assert by_id["candidate_narrow"]["top1_miss_by_reference_margin"]["0_0.5"] == 1
    assert by_id["candidate_narrow"]["top1_miss_by_reference_margin"]["0_5_1.0"] == 1
    assert by_id["candidate_narrow"]["top1_miss_count"] == 2
    assert by_id["candidate_narrow"]["miss_topk_contains_rate"] == 1.0
    assert by_id["candidate_narrow"]["miss_mean_reference_margin"] == 0.55
    assert by_id["candidate_narrow"]["miss_mean_probability_kl"] == 0.0025
    assert by_id["candidate_systematic"]["audit_status"] == DECISION_SYSTEMATIC_HOLD
    assert by_id["candidate_systematic"]["top1_miss_by_reference_margin"][">=4.0"] == 1
    assert by_id["candidate_systematic"]["miss_max_abs_logit_delta"] == 1.9
    assert by_id["candidate_pass"]["audit_status"] == DECISION_PASS


def test_audit_falls_back_to_candidate_summaries_when_rows_missing(tmp_path: Path) -> None:
    payload = {
        "candidate_summaries": [
            {
                "candidate_id": "score32_float",
                "top1_match_rate": 1.0,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.9999,
                "mean_probability_kl": 0.0001,
                "max_abs_logit_delta": 0.2,
                "comparison_count": 12,
            },
            {
                "candidate_id": "score16_float",
                "top1_match_rate": 0.5,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.997,
                "mean_probability_kl": 0.2,
                "max_abs_logit_delta": 0.9,
                "comparison_count": 12,
            },
        ],
    }
    args = _args(tmp_path)
    _write_json(args.score_precision_recovery_json, payload)

    output = build_payload(args)
    by_id = {row["candidate_id"]: row for row in output["candidates"]}

    assert by_id["score32_float"]["audit_status"] == DECISION_PASS
    assert by_id["score16_float"]["audit_status"] == DECISION_SYSTEMATIC_HOLD
    assert by_id["score16_float"]["top1_miss_count"] == 6
    assert output["decision"]["status"] == DECISION_SYSTEMATIC_HOLD
