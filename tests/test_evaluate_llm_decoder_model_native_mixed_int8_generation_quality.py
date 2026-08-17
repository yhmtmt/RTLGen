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
    _build_requested_model_contract,
    _build_structural_contract,
    _decision,
    _enforce_contract,
    _resolve_candidates,
    _resolve_model_structure,
    _summarize_free_running_rows,
    _summarize_teacher_forced_rows,
    _write_report_md,
)
from npu.eval import evaluate_llm_decoder_model_native_mixed_int8_attention as attention_eval


class _FakeConfig:
    def __init__(
        self,
        *,
        attention_heads: int,
        kv_heads: int,
        hidden_size: int,
        name_or_path: str = "",
    ) -> None:
        self.num_attention_heads = attention_heads
        self.num_key_value_heads = kv_heads
        self.hidden_size = hidden_size
        self._name_or_path = name_or_path


class _FakeModel:
    def __init__(self, config: _FakeConfig) -> None:
        self.config = config


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


def test_report_and_hold_message_use_primary_candidate_label() -> None:
    summary = {
        "candidate_id": "score24_w16_rtl_exact",
        "score_bits": 24,
        "weight_bits": 16,
        "softmax_mode": "rtl_exact",
        "teacher_forced_nll_delta_mean": 0.8,
        "candidate_probability_assigned_to_reference_token_mean": 0.2,
        "candidate_probability_assigned_to_reference_token_min": 0.01,
        "free_running_match_rate": 0.5,
        "decision_status": "mixed_int8_generation_quality_hold",
        "free_running_first_divergence_step_mean": 0.5,
    }
    decision = _decision(summary, expected_gqa_group_size=4, actual_gqa_group_size=4.0)
    summary["decision"] = decision
    payload = {
        "model": {"model_id": "test/model"},
        "decision": decision,
        "summary": summary,
        "candidate_summaries": [summary],
        "prompt_records": [
            {
                "candidate_id": "score24_w16_rtl_exact",
                "prompt_index": 0,
                "free_run_first_divergence_step": 0,
                "free_run_match_count": 0,
                "free_run_steps": 8,
            }
        ],
    }

    report = _write_report_md(payload)

    assert "Hold this score24 w16 rtl exact mixed/int8 generation candidate" in decision["next_step"]
    assert "# Native-Checkpoint Mixed/Int8 Score24 W16 RTL Exact Generation Quality" in report
    assert "score32" not in report


def test_requested_model_contract_accepts_exact_expected_identity() -> None:
    args = argparse.Namespace(expected_model_id="meta-llama/Llama-2-7b-hf")

    contract = _build_requested_model_contract(args, "meta-llama/Llama-2-7b-hf")

    assert contract == {
        "status": "pass",
        "blockers": [],
        "resolved_model_id": "meta-llama/Llama-2-7b-hf",
        "expected_model_id": "meta-llama/Llama-2-7b-hf",
    }


def test_requested_model_contract_rejects_mismatched_identity() -> None:
    args = argparse.Namespace(expected_model_id="meta-llama/Llama-2-7b-hf")
    contract = _build_requested_model_contract(args, "mistralai/Mistral-7B-v0.1")

    assert contract["status"] == "fail"
    assert contract["blockers"] == [
        "resolved model_id 'mistralai/Mistral-7B-v0.1' does not match expected 'meta-llama/Llama-2-7b-hf'"
    ]
    with pytest.raises(SystemExit, match="requested model identity contract failed"):
        _enforce_contract(contract, label="requested model identity contract")


def test_resolve_model_structure_reports_exact_llama2_dimensions() -> None:
    model = _FakeModel(
        _FakeConfig(
            attention_heads=32,
            kv_heads=32,
            hidden_size=4096,
            name_or_path="meta-llama/Llama-2-7b-hf",
        )
    )

    structure = _resolve_model_structure(model.config)

    assert structure == {
        "attention_head_count": 32,
        "kv_head_count": 32,
        "hidden_size": 4096,
        "gqa_group_size": 1.0,
        "loaded_model_id": "meta-llama/Llama-2-7b-hf",
    }


def test_structural_contract_accepts_exact_llama2_requirements() -> None:
    args = argparse.Namespace(
        expected_attention_head_count=32,
        expected_kv_head_count=32,
        expected_hidden_size=4096,
        expected_gqa_group_size=1,
    )
    model = _FakeModel(
        _FakeConfig(
            attention_heads=32,
            kv_heads=32,
            hidden_size=4096,
            name_or_path="meta-llama/Llama-2-7b-hf",
        )
    )

    contract = _build_structural_contract(
        args,
        model,
        resolved_model_id="meta-llama/Llama-2-7b-hf",
    )

    assert contract["status"] == "pass"
    assert contract["blockers"] == []
    assert contract["expected"] == {
        "attention_head_count": 32,
        "kv_head_count": 32,
        "hidden_size": 4096,
        "gqa_group_size": 1,
    }
    assert contract["actual"] == {
        "attention_head_count": 32,
        "kv_head_count": 32,
        "hidden_size": 4096,
        "gqa_group_size": 1.0,
        "loaded_model_id": "meta-llama/Llama-2-7b-hf",
    }
    assert contract["gqa_group_size_matches_expectation"] is True


def test_structural_contract_rejects_dimension_mismatch_without_loading_models() -> None:
    args = argparse.Namespace(
        expected_attention_head_count=32,
        expected_kv_head_count=32,
        expected_hidden_size=4096,
        expected_gqa_group_size=1,
    )
    model = _FakeModel(
        _FakeConfig(
            attention_heads=32,
            kv_heads=8,
            hidden_size=4096,
            name_or_path="other/model",
        )
    )

    contract = _build_structural_contract(args, model, resolved_model_id="other/model")

    assert contract["status"] == "fail"
    assert contract["blockers"] == [
        "KV head count 8 does not match expected 32",
        "GQA group size 4.0 does not match expected 1",
    ]
    assert contract["gqa_group_size_matches_expectation"] is False
    with pytest.raises(SystemExit, match="model structural contract failed"):
        _enforce_contract(contract, label="model structural contract")
