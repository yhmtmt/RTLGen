#!/usr/bin/env python3
"""Evaluate model-level mixed-int8 score precision quality via generation behavior."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention as attention_eval

JsonDict = dict[str, Any]

DECISION_PASS = "mixed_int8_generation_quality_pass"
DECISION_HOLD = "mixed_int8_generation_quality_hold"

DEFAULT_CANDIDATE_SPEC = "score32_float:q8,k8,v8,s32,w16,float_quantized"
NLL_EPSILON = 1e-12
DIVISIBILITY_EPSILON = 1e-6


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_probability(probability: float, default: float = 0.0) -> float:
    if not isinstance(probability, (int, float)):
        return float(default)
    if probability < 0.0 or probability > 1.0:
        return float(default)
    return float(probability)


def _nll_from_probability(probability: float) -> float:
    return -math.log(max(NLL_EPSILON, _safe_probability(probability, default=0.0)))


def _parse_positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected positive integer")
    return parsed


def _resolve_model_id(args: argparse.Namespace) -> str:
    return (
        args.model_id
        or os.environ.get("RTLGEN_MODEL_NATIVE_MIXED_INT8_MODEL_ID")
        or os.environ.get("RTLGEN_MODEL_NATIVE_7B_MODEL_ID")
        or os.environ.get("RTLGEN_MODEL_NATIVE_GQA_MODEL_ID")
        or "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    )


def _resolve_candidates(args: argparse.Namespace) -> list[attention_eval.CandidateConfig]:
    candidates: list[attention_eval.CandidateConfig] = []
    if args.candidate:
        candidates.extend(args.candidate)
    for candidate_list in args.candidate_list:
        candidates.extend(candidate_list)

    if not candidates:
        candidates.append(attention_eval._parse_candidate_spec(DEFAULT_CANDIDATE_SPEC))

    return candidates


def _model_gqa_group_size(model: Any) -> float:
    config = model.config
    attention_heads = int(getattr(config, "num_attention_heads", 0) or getattr(config, "n_head", 0) or 0)
    kv_heads = int(getattr(config, "num_key_value_heads", 0) or attention_heads)
    if attention_heads <= 0 or kv_heads <= 0:
        raise SystemExit("model config does not expose attention and KV head counts")
    if attention_heads % kv_heads != 0:
        raise SystemExit("model uses non-integer GQA group size; expected divisible attention and KV heads")
    return attention_heads / kv_heads


def _collect_teacher_forced_rows(
    reference_model: Any,
    candidate_model: Any,
    tokenizer: Any,
    prompts: list[str],
    *,
    candidate: attention_eval.CandidateConfig,
    generation_steps: int,
    device: str,
    torch_module: Any,
) -> tuple[list[JsonDict], list[JsonDict]]:
    softmax_ctx = attention_eval._softmax_patch(
        score_bits=candidate.score_bits,
        weight_bits=candidate.weight_bits,
        softmax_mode=candidate.softmax_mode,
    )
    patches = attention_eval._install_attention_wrappers(
        candidate_model,
        q_bits=candidate.q_bits,
        k_bits=candidate.k_bits,
        v_bits=candidate.v_bits,
    )
    rows: list[JsonDict] = []
    prompt_records: list[JsonDict] = []

    try:
        for prompt_index, prompt in enumerate(prompts):
            encoded = tokenizer(prompt, return_tensors="pt")
            reference_input_ids = encoded["input_ids"].to(device)
            with torch_module.no_grad():
                ref_past, ref_logits, ref_probs, ref_order = attention_eval._run_single_inference(
                    reference_model,
                    input_ids=reference_input_ids,
                    past_key_values=None,
                    topk=2,
                )
            if not ref_logits:
                raise SystemExit("reference model did not return logits for initial prompt")

            ref_next_token = int(ref_order[0]) if ref_order else 0
            ref_prob = _safe_probability(ref_probs[ref_next_token], default=0.0) if len(ref_probs) > ref_next_token else 0.0
            ref_nll = _nll_from_probability(ref_prob)

            with torch_module.no_grad():
                with softmax_ctx():
                    cand_past, cand_logits, cand_probs, cand_order = attention_eval._run_single_inference(
                        candidate_model,
                        input_ids=reference_input_ids,
                        past_key_values=None,
                        topk=2,
                    )
            if not cand_logits:
                raise SystemExit("candidate model did not return logits for initial prompt")

            cand_next_token = int(cand_order[0]) if cand_order else 0
            cand_prob = _safe_probability(cand_probs[ref_next_token], default=0.0) if len(cand_probs) > ref_next_token else 0.0
            cand_nll = _nll_from_probability(cand_prob)
            rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "prompt_index": prompt_index,
                    "step": 0,
                    "phase": "teacher_forced",
                    "reference_next_token": ref_next_token,
                    "candidate_next_token": cand_next_token,
                    "teacher_forced_top1_match": 1.0 if cand_next_token == ref_next_token else 0.0,
                    "reference_nll": ref_nll,
                    "candidate_nll": cand_nll,
                    "nll_delta": cand_nll - ref_nll,
                    "candidate_probability_assigned_to_reference_token": cand_prob,
                    "reference_probability_of_top1": ref_prob,
                }
            )

            current_reference_token = ref_next_token
            if prompt_index < len(prompts):
                prompt_records.append(
                    {
                        "prompt_index": prompt_index,
                        "prompt": prompt,
                        "prefill_reference_next_token": ref_next_token,
                    }
                )

            for step in range(1, generation_steps):
                ref_input = torch_module.tensor([[current_reference_token]], dtype=torch_module.long, device=device)
                cand_input = torch_module.tensor([[current_reference_token]], dtype=torch_module.long, device=device)
                with torch_module.no_grad():
                    ref_past, ref_logits, ref_probs, ref_order = attention_eval._run_single_inference(
                        reference_model,
                        input_ids=ref_input,
                        past_key_values=ref_past,
                        topk=2,
                    )
                ref_next_token = int(ref_order[0]) if ref_order else 0
                ref_prob = _safe_probability(ref_probs[ref_next_token], default=0.0) if len(ref_probs) > ref_next_token else 0.0
                ref_nll = _nll_from_probability(ref_prob)

                with torch_module.no_grad():
                    with softmax_ctx():
                        cand_past, cand_logits, cand_probs, cand_order = attention_eval._run_single_inference(
                            candidate_model,
                            input_ids=cand_input,
                            past_key_values=cand_past,
                            topk=2,
                        )

                if not cand_logits:
                    raise SystemExit("candidate model did not return logits during teacher-forced rollout")
                cand_next_token = int(cand_order[0]) if cand_order else 0
                cand_prob = _safe_probability(cand_probs[ref_next_token], default=0.0) if len(cand_probs) > ref_next_token else 0.0
                cand_nll = _nll_from_probability(cand_prob)
                rows.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "prompt_index": prompt_index,
                        "step": step,
                        "phase": "teacher_forced",
                        "reference_next_token": ref_next_token,
                        "candidate_next_token": cand_next_token,
                        "teacher_forced_top1_match": 1.0 if cand_next_token == ref_next_token else 0.0,
                        "reference_nll": ref_nll,
                        "candidate_nll": cand_nll,
                        "nll_delta": cand_nll - ref_nll,
                        "candidate_probability_assigned_to_reference_token": cand_prob,
                        "reference_probability_of_top1": ref_prob,
                    }
                )
                current_reference_token = ref_next_token

    finally:
        attention_eval._restore_attention_wrappers(patches)

    return rows, prompt_records


def _collect_free_running_rows(
    reference_model: Any,
    candidate_model: Any,
    tokenizer: Any,
    prompts: list[str],
    *,
    candidate: attention_eval.CandidateConfig,
    generation_steps: int,
    device: str,
    torch_module: Any,
) -> tuple[list[JsonDict], list[JsonDict]]:
    softmax_ctx = attention_eval._softmax_patch(
        score_bits=candidate.score_bits,
        weight_bits=candidate.weight_bits,
        softmax_mode=candidate.softmax_mode,
    )
    patches = attention_eval._install_attention_wrappers(
        candidate_model,
        q_bits=candidate.q_bits,
        k_bits=candidate.k_bits,
        v_bits=candidate.v_bits,
    )
    rows: list[JsonDict] = []
    prompt_records: list[JsonDict] = []

    try:
        for prompt_index, prompt in enumerate(prompts):
            encoded = tokenizer(prompt, return_tensors="pt")
            ref_input = encoded["input_ids"].to(device)
            cand_input = encoded["input_ids"].to(device)
            ref_past = None
            cand_past = None
            prompt_match_count = 0
            first_divergence: int | None = None

            for step in range(generation_steps):
                with torch_module.no_grad():
                    ref_past, _, ref_probs, ref_order = attention_eval._run_single_inference(
                        reference_model,
                        input_ids=ref_input,
                        past_key_values=ref_past,
                        topk=2,
                    )
                ref_next_token = int(ref_order[0]) if ref_order else 0

                with torch_module.no_grad():
                    with softmax_ctx():
                        cand_past, _, cand_probs, cand_order = attention_eval._run_single_inference(
                            candidate_model,
                            input_ids=cand_input,
                            past_key_values=cand_past,
                            topk=2,
                        )
                cand_next_token = int(cand_order[0]) if cand_order else 0
                match = 1.0 if cand_next_token == ref_next_token else 0.0
                if match:
                    prompt_match_count += 1
                elif first_divergence is None:
                    first_divergence = step

                rows.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "prompt_index": prompt_index,
                        "step": step,
                        "phase": "free_running",
                        "reference_next_token": ref_next_token,
                        "candidate_next_token": cand_next_token,
                        "match": match,
                    }
                )

                ref_input = torch_module.tensor([[ref_next_token]], dtype=torch_module.long, device=device)
                cand_input = torch_module.tensor([[cand_next_token]], dtype=torch_module.long, device=device)

            if first_divergence is None:
                first_divergence = generation_steps

            prompt_records.append(
                {
                    "prompt_index": prompt_index,
                    "prompt": prompt,
                    "free_run_first_divergence_step": first_divergence,
                    "free_run_match_count": prompt_match_count,
                    "free_run_steps": generation_steps,
                    "free_run_match_rate": float(prompt_match_count) / float(generation_steps),
                }
            )

    finally:
        attention_eval._restore_attention_wrappers(patches)

    return rows, prompt_records


def _summarize_teacher_forced_rows(rows: list[JsonDict]) -> JsonDict:
    if not rows:
        return {
            "teacher_forced_comparison_count": 0,
            "teacher_forced_top1_match_rate": 0.0,
            "teacher_forced_reference_nll_mean": 0.0,
            "teacher_forced_candidate_nll_mean": 0.0,
            "teacher_forced_nll_delta_mean": 0.0,
            "teacher_forced_nll_delta_max": 0.0,
            "reference_probability_of_top1_mean": 0.0,
            "candidate_probability_assigned_to_reference_token_mean": 0.0,
            "candidate_probability_assigned_to_reference_token_min": 0.0,
            "candidate_probability_assigned_to_reference_token_max": 0.0,
        }

    reference_nll = [_float(row.get("reference_nll")) for row in rows]
    candidate_nll = [_float(row.get("candidate_nll")) for row in rows]
    deltas = [_float(row.get("nll_delta")) for row in rows]
    matches = [_float(row.get("teacher_forced_top1_match")) for row in rows]
    reference_probs = [_safe_probability(row.get("reference_probability_of_top1"), default=0.0) for row in rows]
    probs = [_safe_probability(row.get("candidate_probability_assigned_to_reference_token"), default=0.0) for row in rows]

    return {
        "teacher_forced_comparison_count": len(rows),
        "teacher_forced_top1_match_rate": _mean(matches),
        "teacher_forced_reference_nll_mean": _mean(reference_nll),
        "teacher_forced_candidate_nll_mean": _mean(candidate_nll),
        "teacher_forced_nll_delta_mean": _mean(deltas),
        "teacher_forced_nll_delta_max": max(deltas),
        "reference_probability_of_top1_mean": _mean(reference_probs),
        "candidate_probability_assigned_to_reference_token_mean": _mean(probs),
        "candidate_probability_assigned_to_reference_token_min": min(probs),
        "candidate_probability_assigned_to_reference_token_max": max(probs),
    }


def _summarize_free_running_rows(rows: list[JsonDict], *, generation_steps: int, prompt_count: int) -> JsonDict:
    if not rows:
        return {
            "free_running_comparison_count": 0,
            "free_running_match_count": 0,
            "free_running_match_rate": 0.0,
            "free_running_first_divergence_step_mean": 0.0,
            "free_running_first_divergence_step_max": 0,
            "free_running_prompt_diverged_count": 0,
            "free_running_prompt_divergence_rate": 0.0,
        }

    matches = [_float(row.get("match")) for row in rows]
    comparisons = len(rows)
    diverged_by_prompt: dict[int, int] = {}

    for row in rows:
        prompt_index = int(row["prompt_index"])
        step = int(row["step"])
        match = _float(row.get("match"))
        if match < 1.0 and prompt_index not in diverged_by_prompt:
            diverged_by_prompt[prompt_index] = step

    for index in range(prompt_count):
        if index not in diverged_by_prompt:
            diverged_by_prompt[index] = generation_steps

    first_divergence_steps = [diverged_by_prompt.get(index, generation_steps) for index in sorted(diverged_by_prompt)]
    prompt_diverged_count = sum(1 for step in first_divergence_steps if step < generation_steps)
    match_count = sum(1 for value in matches if value >= 1.0)
    return {
        "free_running_comparison_count": comparisons,
        "free_running_match_count": match_count,
        "free_running_match_rate": _mean(matches),
        "free_running_first_divergence_step_mean": _mean([_float(value) for value in first_divergence_steps]),
        "free_running_first_divergence_step_max": max(first_divergence_steps),
        "free_running_prompt_diverged_count": prompt_diverged_count,
        "free_running_prompt_divergence_rate": _float(prompt_diverged_count) / float(max(prompt_count, 1)),
    }


def _candidate_label(summary: JsonDict) -> str:
    candidate_id = str(summary.get("candidate_id") or "").strip()
    if candidate_id:
        return candidate_id.replace("_", " ")
    score_bits = summary.get("score_bits")
    weight_bits = summary.get("weight_bits")
    softmax_mode = str(summary.get("softmax_mode") or "").strip()
    parts: list[str] = []
    if score_bits is not None:
        parts.append(f"score{score_bits}")
    if weight_bits is not None:
        parts.append(f"w{weight_bits}")
    if softmax_mode:
        parts.append(softmax_mode.replace("_", " "))
    return " ".join(parts) or "candidate"


def _candidate_title_label(summary: JsonDict) -> str:
    words: list[str] = []
    for word in _candidate_label(summary).split():
        lower = word.lower()
        if lower in {"rtl", "pwl", "lut", "qkv"}:
            words.append(lower.upper())
        elif lower.startswith("q") and lower[1:].isdigit():
            words.append(lower.upper())
        elif lower.startswith("w") and lower[1:].isdigit():
            words.append(lower.upper())
        elif lower.startswith("score") and lower[5:].isdigit():
            words.append("Score" + lower[5:])
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _decision(summary: JsonDict, *, expected_gqa_group_size: int, actual_gqa_group_size: float) -> JsonDict:
    blockers: list[str] = []
    if expected_gqa_group_size > 0 and abs(actual_gqa_group_size - expected_gqa_group_size) > DIVISIBILITY_EPSILON:
        blockers.append(
            f"model_gqa_group_size {actual_gqa_group_size:g} does not match expected {expected_gqa_group_size}"
        )

    nll_delta = _float(summary.get("teacher_forced_nll_delta_mean"))
    candidate_prob = _float(summary.get("candidate_probability_assigned_to_reference_token_mean"))
    match_rate = _float(summary.get("free_running_match_rate"))
    if nll_delta > 0.4:
        blockers.append("teacher-forced mean NLL delta exceeded tolerance")
    if candidate_prob < 0.1:
        blockers.append("candidate assigned too little probability to reference tokens under teacher forcing")
    if match_rate < 0.75:
        blockers.append("free-running generation diverged too far from reference")

    if blockers:
        status = DECISION_HOLD
        label = _candidate_label(summary)
        next_step = (
            f"Hold this {label} mixed/int8 generation candidate until a narrower score-precision boundary "
            "demonstrates better free-running agreement."
        )
    else:
        status = DECISION_PASS
        next_step = (
            "Candidate passed the bounded generation-quality gate; route this score configuration into "
            "the native-checkpoint quality evidence stream."
        )

    return {
        "status": status,
        "blockers": blockers,
        "next_step": next_step,
        "thresholds": {
            "teacher_forced_mean_nll_delta_max": 0.4,
            "teacher_forced_candidate_reference_token_prob_mean_min": 0.1,
            "free_running_match_rate_min": 0.75,
            "expected_gqa_group_size": expected_gqa_group_size,
        },
    }


def _candidate_rank(candidate_summary: JsonDict) -> tuple[float, float, float, str]:
    status_weight = 1.0 if candidate_summary.get("decision_status") == DECISION_PASS else 0.0
    return (
        status_weight,
        _float(candidate_summary.get("free_running_match_rate")),
        -abs(_float(candidate_summary.get("teacher_forced_nll_delta_mean"))),
        candidate_summary.get("candidate_id", ""),
    )


def _candidate_precision(candidate: attention_eval.CandidateConfig) -> JsonDict:
    return {
        "candidate_id": candidate.candidate_id,
        "q_bits": candidate.q_bits,
        "k_bits": candidate.k_bits,
        "v_bits": candidate.v_bits,
        "score_bits": candidate.score_bits,
        "weight_bits": candidate.weight_bits,
        "softmax_mode": candidate.softmax_mode,
    }


def _run_model_eval(args: argparse.Namespace) -> JsonDict:
    torch_module, AutoModelForCausalLM, AutoTokenizer = attention_eval._load_runtime_modules()
    model_id = _resolve_model_id(args)
    device = args.device
    if device == "auto":
        device = "cuda" if torch_module.cuda.is_available() else "cpu"
    dtype = attention_eval._resolve_torch_dtype(torch_module, device=device, dtype_name=args.dtype)

    def load_model() -> Any:
        try:
            return AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=dtype,
                attn_implementation="eager",
            )
        except TypeError:
            return AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    reference_model = load_model().to(device)
    candidate_model = load_model().to(device)
    reference_model.eval()
    candidate_model.eval()

    if not attention_eval._supports_attention_quantization(candidate_model):
        raise SystemExit("candidate model does not expose q/k/v projection modules for mixed-int8 generation quality")

    actual_gqa_group_size = _model_gqa_group_size(reference_model)
    prompts = attention_eval._load_prompts(args.prompt_file)[: args.max_prompts]
    if not prompts:
        raise SystemExit("no prompts to evaluate")

    candidates = _resolve_candidates(args)
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise SystemExit(f"candidate ids must be unique: {candidate_ids}")

    candidate_rows: list[JsonDict] = []
    generation_rows: list[JsonDict] = []
    prompt_records: list[JsonDict] = []
    candidate_summaries: list[JsonDict] = []
    for candidate in candidates:
        teacher_rows, prompt_records_forced = _collect_teacher_forced_rows(
            reference_model,
            candidate_model,
            tokenizer,
            prompts,
            candidate=candidate,
            generation_steps=args.generation_steps,
            device=device,
            torch_module=torch_module,
        )
        running_rows, prompt_records_running = _collect_free_running_rows(
            reference_model,
            candidate_model,
            tokenizer,
            prompts,
            candidate=candidate,
            generation_steps=args.generation_steps,
            device=device,
            torch_module=torch_module,
        )

        teacher_summary = _summarize_teacher_forced_rows(teacher_rows)
        generation_summary = _summarize_free_running_rows(
            running_rows,
            generation_steps=args.generation_steps,
            prompt_count=len(prompts),
        )
        candidate_summary = {
            **_candidate_precision(candidate),
            **teacher_summary,
            **generation_summary,
            "candidate_id": candidate.candidate_id,
            "prompt_count": len(prompts),
            "generation_steps": args.generation_steps,
        }
        candidate_summary.update(
            {
                "free_run_exact_match_rate": 1.0
                - _float(candidate_summary.get("free_running_prompt_divergence_rate")),
                "free_run_token_match_rate": _float(candidate_summary.get("free_running_match_rate")),
                "diverged_prompt_count": int(candidate_summary.get("free_running_prompt_diverged_count", 0)),
                "mean_first_divergence_step": _float(
                    candidate_summary.get("free_running_first_divergence_step_mean")
                ),
                "teacher_forced_mean_reference_nll": _float(
                    candidate_summary.get("teacher_forced_reference_nll_mean")
                ),
                "teacher_forced_mean_candidate_nll": _float(
                    candidate_summary.get("teacher_forced_candidate_nll_mean")
                ),
                "teacher_forced_mean_nll_delta": _float(candidate_summary.get("teacher_forced_nll_delta_mean")),
                "teacher_forced_reference_token_prob_mean": _float(
                    candidate_summary.get("reference_probability_of_top1_mean")
                ),
                "teacher_forced_candidate_reference_token_prob_mean": _float(
                    candidate_summary.get("candidate_probability_assigned_to_reference_token_mean")
                ),
            }
        )
        decision = _decision(candidate_summary, expected_gqa_group_size=args.expected_gqa_group_size, actual_gqa_group_size=actual_gqa_group_size)
        candidate_summary["decision_status"] = decision["status"]
        candidate_summary["decision"] = decision
        for row in teacher_rows:
            row["candidate_id"] = candidate.candidate_id
        for row in running_rows:
            row["candidate_id"] = candidate.candidate_id
        for row in prompt_records_forced:
            row["candidate_id"] = candidate.candidate_id
        for row in prompt_records_running:
            row["candidate_id"] = candidate.candidate_id
            merged = prompt_records_forced[row["prompt_index"]].copy()
            merged.update(row)
            prompt_records.append(merged)

        candidate_rows.extend(teacher_rows)
        generation_rows.extend(running_rows)
        candidate_summaries.append(candidate_summary)

    if not candidate_summaries:
        raise SystemExit("no candidates were configured")

    best_candidate = max(candidate_summaries, key=_candidate_rank)
    primary_summary = best_candidate
    for candidate in candidate_summaries:
        if candidate.get("candidate_id") == args.primary_candidate_id:
            primary_summary = candidate
            break
    if args.primary_candidate_id and primary_summary.get("candidate_id") != args.primary_candidate_id:
        raise SystemExit(f"primary candidate id not found: {args.primary_candidate_id}")

    return {
        "version": 1.0,
        "quality_gate": "mixed_int8_generation_quality",
        "model": {
            "model_id": model_id,
            "gqa_group_size": actual_gqa_group_size,
            "device": device,
            "dtype": attention_eval._dtype_label(dtype),
            "requested_dtype": args.dtype,
            "generation_steps": args.generation_steps,
            "max_prompts": args.max_prompts,
        },
        "inputs": {
            "score_margin_audit_json": str(args.score_margin_audit_json) if args.score_margin_audit_json else "",
        },
        "candidate_rows": candidate_rows,
        "free_running_rows": generation_rows,
        "prompt_records": prompt_records,
        "candidate_summaries": candidate_summaries,
        "candidate_summary": primary_summary,
        "summary": primary_summary,
        "best_candidate": {
            "candidate_id": best_candidate["candidate_id"],
            "decision_status": best_candidate["decision_status"],
            "teacher_forced_nll_delta_mean": best_candidate["teacher_forced_nll_delta_mean"],
            "free_running_match_rate": best_candidate["free_running_match_rate"],
            "candidate_probability_assigned_to_reference_token_mean": best_candidate[
                "candidate_probability_assigned_to_reference_token_mean"
            ],
        },
        "precision": _candidate_precision(next(candidate for candidate in candidates if candidate.candidate_id == primary_summary["candidate_id"])),
        "decision": primary_summary["decision"],
    }


def build_payload(args: argparse.Namespace) -> JsonDict:
    return _run_model_eval(args)


def _write_report_md(payload: JsonDict) -> str:
    primary_summary = payload["summary"]
    label = _candidate_title_label(primary_summary)
    lines = [
        f"# Native-Checkpoint Mixed/Int8 {label} Generation Quality",
        "",
        f"- model_id: `{payload['model']['model_id']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Candidate Summaries",
        "",
        "| candidate_id | status | teacher_forced_nll_delta_mean | cand_ref_prob | free_run_match | first_div_step_mean |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["candidate_summaries"]:
        lines.append(
            "| {candidate_id} | {decision_status} | {teacher_forced_nll_delta_mean:.6f} | {candidate_probability_assigned_to_reference_token_mean:.6f} | {free_running_match_rate:.6f} | {free_running_first_divergence_step_mean:.6f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Prompt Divergence",
            "",
        ]
    )
    lines.extend(
        [
            "| candidate_id | prompt_index | first_divergence_step | match_count | steps |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in payload["prompt_records"]:
        lines.append(
            "| {candidate_id} | {prompt_index} | {free_run_first_divergence_step} | {free_run_match_count} | {free_run_steps} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Assumptions",
            "",
            "- Teacher-forced rows compare against a non-quantized reference model.",
            "- Candidate applies LLaMA-style q/k/v projection quantization plus softmax approximation.",
            f"- Decision thresholds are conservative for {label}-vs-reference drift in a bounded prompt sample.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-id", default="")
    ap.add_argument("--prompt-file", default="")
    ap.add_argument("--max-prompts", type=_parse_positive_int, default=2)
    ap.add_argument("--generation-steps", type=_parse_positive_int, default=4)
    ap.add_argument("--expected-gqa-group-size", type=int, default=8)
    ap.add_argument("--candidate", action="append", type=attention_eval._parse_candidate_spec, default=[])
    ap.add_argument("--candidate-list", action="append", type=attention_eval._parse_candidate_list, default=[])
    ap.add_argument("--primary-candidate-id", default="")
    ap.add_argument("--score-margin-audit-json", default="")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--dtype", default="auto", choices=["auto", "float32", "float16", "bfloat16"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_payload(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _write_report_md(payload)
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
