#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.evaluate_llm_decoder_model_native_mixed_int8_generation_quality import (
    DEFAULT_CANDIDATE_SPEC,
    _decision,
    _resolve_candidates,
    _summarize_free_running_rows,
    _summarize_teacher_forced_rows,
)
from npu.eval import evaluate_llm_decoder_model_native_mixed_int8_attention as attention_eval


def test_summarize_teacher_and_free_running_rows_record_divergence_and_nll() -> None:
    teacher_rows = [
        {
            "reference_nll": 2.0,
            "candidate_nll": 2.2,
            "nll_delta": 0.2,
            "teacher_forced_top1_match": 1.0,
            "candidate_probability_assigned_to_reference_token": 0.4,
        },
        {
            "reference_nll": 3.0,
            "candidate_nll": 3.3,
            "nll_delta": 0.3,
            "teacher_forced_top1_match": 0.0,
            "candidate_probability_assigned_to_reference_token": 0.2,
        },
    ]
    generation_rows = [
        {"prompt_index": 0, "step": 0, "match": 1.0},
        {"prompt_index": 0, "step": 1, "match": 0.0},
        {"prompt_index": 1, "step": 0, "match": 1.0},
        {"prompt_index": 1, "step": 1, "match": 1.0},
        {"prompt_index": 1, "step": 2, "match": 1.0},
    ]

    teacher_summary = _summarize_teacher_forced_rows(teacher_rows)
    generation_summary = _summarize_free_running_rows(
        generation_rows, generation_steps=3, prompt_count=2
    )

    assert teacher_summary["teacher_forced_reference_nll_mean"] == pytest.approx(2.5)
    assert teacher_summary["teacher_forced_candidate_nll_mean"] == pytest.approx(2.75)
    assert teacher_summary["teacher_forced_nll_delta_mean"] == pytest.approx(0.25)
    assert teacher_summary["reference_probability_of_top1_mean"] == pytest.approx(0.0)
    assert teacher_summary["candidate_probability_assigned_to_reference_token_mean"] == pytest.approx(0.3)
    assert generation_summary["free_running_match_rate"] == 0.8
    assert generation_summary["free_running_first_divergence_step_mean"] == 2.0
    assert generation_summary["free_running_prompt_diverged_count"] == 1


def test_generation_decision_pass_and_hold_thresholds() -> None:
    clean = {
        "teacher_forced_nll_delta_mean": 0.2,
        "candidate_probability_assigned_to_reference_token_mean": 0.35,
        "candidate_probability_assigned_to_reference_token_min": 0.01,
        "free_running_match_rate": 0.9,
    }
    poor = {
        "teacher_forced_nll_delta_mean": 0.8,
        "candidate_probability_assigned_to_reference_token_mean": 0.05,
        "free_running_match_rate": 0.5,
    }

    clean_decision = _decision(clean, expected_gqa_group_size=4, actual_gqa_group_size=4.0)
    assert clean_decision["status"] == "mixed_int8_generation_quality_pass"
    assert clean_decision["thresholds"] == {
        "teacher_forced_mean_nll_delta_max": 0.4,
        "teacher_forced_candidate_reference_token_prob_mean_min": 0.1,
        "free_running_match_rate_min": 0.75,
        "expected_gqa_group_size": 4,
    }
    hold = _decision(poor, expected_gqa_group_size=4, actual_gqa_group_size=4.0)
    assert hold["status"] == "mixed_int8_generation_quality_hold"
    assert hold["blockers"]


def test_default_candidates_resolves_score32_float() -> None:
    args = argparse.Namespace(
        candidate=[],
        candidate_list=[],
    )
    candidates = _resolve_candidates(args)

    assert len(candidates) == 1
    assert candidates[0].candidate_id == attention_eval._parse_candidate_spec(DEFAULT_CANDIDATE_SPEC).candidate_id
    assert candidates[0].score_bits == 32
    assert candidates[0].q_bits == 8
