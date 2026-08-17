#!/usr/bin/env python3
"""Build the exact Llama-2-7B score32 final frontier without collapsing to one scalar winner."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

JsonDict = dict[str, Any]

_BASE = Path("runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1")
DEFAULT_RECOST = _BASE / (
    "decoder_attention_score32_global_hbm_exact_llama2_mha_recost__"
    "l2_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1.json"
)
DEFAULT_GENERATION_QUALITY = _BASE / (
    "decoder_attention_score32_exact_llama2_mha_generation_quality__"
    "l2_decoder_attention_score32_exact_llama2_mha_generation_quality_v1.json"
)
DEFAULT_QUALITY_FRONTIER = _BASE / (
    "decoder_attention_score32_integrated_frontier_ranking__"
    "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_frontier_"
    "llama7b_v1.json"
)

_MODEL_ID = "llama2_7b_score32_exact_mha_final_frontier_v1"
_RECOST_MODEL = "llm_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1"
_QUALITY_GATE = "mixed_int8_generation_quality"
_QUALITY_PASS = "mixed_int8_generation_quality_pass"
_QUALITY_HOLD = "mixed_int8_generation_quality_hold"
_DECISION_PASS = "exact_llama2_mha_quality_backed_frontier_available"
_DECISION_HOLD = "exact_llama2_mha_score32_quality_hold"
_QUALITY_FRONTIER_MODEL = "llm_decoder_attention_score32_integrated_frontier_ranking_v1"
_EXACT_MODEL_ID = "meta-llama/Llama-2-7b-hf"
_SCORE32_PRECISION = {
    "candidate_id": "score32_exp_lut_div",
    "q_bits": 8,
    "k_bits": 8,
    "v_bits": 8,
    "score_bits": 32,
    "weight_bits": 16,
    "softmax_mode": "exp_lut_div_bucket20",
}
_GQA8_CANDIDATE_ID = "score32_gqa8_global_hbm_finite_endpoint"
_LONG_CONTEXT_MHA_CANDIDATE_ID = "score32_llama2_7b_mha_131k_extrapolation_global_hbm_finite_endpoint"
_EXACT_MHA_CANDIDATE_ID = "score32_exact_llama2_7b_mha_global_hbm_finite_endpoint"


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _positive(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be positive")
    return number


def _string(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _exact_number(value: Any, expected: float, label: str) -> float:
    observed = _positive(value, label)
    if observed != expected:
        raise ValueError(f"{label} mismatch: expected {expected}, observed {observed}")
    return observed


def _validate_recost(payload: JsonDict) -> tuple[JsonDict, JsonDict, JsonDict]:
    if payload.get("version") != 1 or payload.get("model") != _RECOST_MODEL:
        raise ValueError("exact MHA recost model/version mismatch")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("exact MHA recost rows are missing")

    gqa8_row: JsonDict | None = None
    long_context_mha_row: JsonDict | None = None
    native_mha_row: JsonDict | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        contract = row.get("model_contract")
        throughput = row.get("throughput")
        physical = row.get("physical")
        energy = row.get("energy")
        if not all(isinstance(section, dict) for section in (contract, throughput, physical, energy)):
            raise ValueError("exact MHA recost row is missing required sections")
        kv_heads = int(_positive(contract.get("kv_heads"), "recost kv_heads"))
        attention_heads = int(_positive(contract.get("attention_heads"), "recost attention_heads"))
        gqa_group_size = _positive(contract.get("gqa_group_size"), "recost gqa_group_size")
        hidden_size = int(_positive(contract.get("hidden_size"), "recost hidden_size"))
        if hidden_size != 4096 or attention_heads != 32:
            raise ValueError("exact MHA recost rows must remain on the 4096-wide 32-head model")
        candidate_id = row.get("candidate_id")
        if kv_heads == 4 and gqa_group_size == 8 and candidate_id == _GQA8_CANDIDATE_ID:
            if contract.get("kv_sharing") != "gqa8" or int(contract.get("sequence_length", 0)) != 131072:
                raise ValueError("corrected GQA8 row kv_sharing mismatch")
            gqa8_row = dict(row)
        elif kv_heads == 32 and gqa_group_size == 1 and candidate_id == _LONG_CONTEXT_MHA_CANDIDATE_ID:
            if contract.get("kv_sharing") != "mha" or int(contract.get("sequence_length", 0)) != 131072:
                raise ValueError("long-context MHA row contract mismatch")
            long_context_mha_row = dict(row)
        elif kv_heads == 32 and gqa_group_size == 1 and candidate_id == _EXACT_MHA_CANDIDATE_ID:
            if (
                contract.get("kv_sharing") != "mha"
                or contract.get("contract_scope") != "exact_llama2_7b_mha_structure"
                or int(contract.get("sequence_length", 0)) != 4096
                or contract.get("native_context_match") is not True
            ):
                raise ValueError("exact MHA row structural contract mismatch")
            native_mha_row = dict(row)

    if gqa8_row is None or long_context_mha_row is None or native_mha_row is None:
        raise ValueError("exact MHA recost must contain corrected GQA8, 131k MHA, and native-context MHA rows")
    return gqa8_row, long_context_mha_row, native_mha_row


def _quality_model_field(model: JsonDict, field: str) -> Any:
    if field in model:
        return model.get(field)
    contract = model.get("structural_contract")
    if isinstance(contract, dict):
        loaded = contract.get("loaded_model_structure")
        if isinstance(loaded, dict):
            actual = loaded.get("actual")
            if isinstance(actual, dict) and field in actual:
                return actual.get(field)
    return None


def _validate_generation_quality(payload: JsonDict) -> JsonDict:
    if float(payload.get("version", 0.0)) != 1.0:
        raise ValueError("generation quality version mismatch")
    if payload.get("quality_gate") != _QUALITY_GATE:
        raise ValueError("generation quality gate mismatch")
    model = payload.get("model")
    precision = payload.get("precision")
    decision = payload.get("decision")
    if not all(isinstance(section, dict) for section in (model, precision, decision)):
        raise ValueError("generation quality payload is missing required sections")

    observed_model_id = _string(
        model.get("resolved_model_id") or model.get("model_id"),
        "generation quality model_id",
    )
    if observed_model_id != _EXACT_MODEL_ID:
        raise ValueError(
            f"generation quality model_id mismatch: expected {_EXACT_MODEL_ID!r}, observed {observed_model_id!r}"
        )
    if model.get("expected_model_id") != _EXACT_MODEL_ID:
        raise ValueError("generation quality expected_model_id does not lock the official checkpoint")

    hidden_size = int(_exact_number(_quality_model_field(model, "hidden_size"), 4096, "quality hidden_size"))
    attention_heads = int(
        _exact_number(
            _quality_model_field(model, "attention_head_count"),
            32,
            "quality attention_head_count",
        )
    )
    kv_heads = int(
        _exact_number(
            _quality_model_field(model, "kv_head_count"),
            32,
            "quality kv_head_count",
        )
    )
    gqa_group_size = _exact_number(_quality_model_field(model, "gqa_group_size"), 1, "quality gqa_group_size")
    structural_status = _string(
        model.get("structural_contract_status")
        or model.get("structural_contract", {}).get("loaded_model_structure", {}).get("status"),
        "generation quality structural_contract_status",
    )
    if structural_status != "pass":
        raise ValueError("generation quality structural contract did not pass")

    mismatches = {
        key: {"expected": expected, "observed": precision.get(key)}
        for key, expected in _SCORE32_PRECISION.items()
        if precision.get(key) != expected
    }
    if mismatches:
        raise ValueError(f"generation quality precision mismatch: {mismatches}")

    decision_status = _string(decision.get("status"), "generation quality decision status")
    if decision_status not in {_QUALITY_PASS, _QUALITY_HOLD}:
        raise ValueError(f"generation quality decision status is unsupported: {decision_status}")

    summary = payload.get("summary")
    prompt_count = None
    if isinstance(summary, dict) and summary.get("prompt_count") not in (None, ""):
        prompt_count = int(_positive(summary.get("prompt_count"), "quality prompt_count"))

    return {
        "model_id": observed_model_id,
        "hidden_size": hidden_size,
        "attention_head_count": attention_heads,
        "kv_head_count": kv_heads,
        "gqa_group_size": gqa_group_size,
        "structural_contract_status": structural_status,
        "decision_status": decision_status,
        "prompt_count": prompt_count,
        "generation_steps": model.get("generation_steps"),
        "precision": dict(precision),
    }


def _validate_quality_frontier(payload: JsonDict) -> tuple[JsonDict, list[JsonDict]]:
    if payload.get("version") != 1 or payload.get("model") != _QUALITY_FRONTIER_MODEL:
        raise ValueError("quality-aware frontier model/version mismatch")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("quality-aware frontier rows are missing")

    fp16_row: JsonDict | None = None
    excluded: list[JsonDict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("family") == "measured_exact_fp16_gqa8_kv8":
            if fp16_row is not None:
                raise ValueError("quality-aware frontier must contain exactly one measured exact-FP16 GQA8 row")
            fp16_row = dict(row)
            continue
        if row.get("promotable") is not True or row.get("quality_backed") is not True:
            excluded.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "family": row.get("family"),
                    "reason": row.get("precision_status") or row.get("abstraction_status") or "nonpromotable_history",
                }
            )
    if fp16_row is None:
        raise ValueError("quality-aware frontier is missing the measured exact-FP16 GQA8 engineering reference")
    return fp16_row, excluded


def _embodied_area_mm2(row: JsonDict, *, source_label: str) -> float:
    if "total_embodied_area_mm2" in row and row.get("total_embodied_area_mm2") not in (None, ""):
        return _positive(row.get("total_embodied_area_mm2"), f"{source_label} total_embodied_area_mm2")
    if "total_embodied_area_um2" in row and row.get("total_embodied_area_um2") not in (None, ""):
        return _positive(row.get("total_embodied_area_um2"), f"{source_label} total_embodied_area_um2") / 1.0e6
    if "die_area_mm2" in row and row.get("die_area_mm2") not in (None, ""):
        return _positive(row.get("die_area_mm2"), f"{source_label} die_area_mm2")
    raise ValueError(f"{source_label} is missing an embodied-area metric")


def _recost_engineering_row(
    row: JsonDict,
    *,
    promotable: bool,
    quality_backed: bool,
    structural_quality_backed: bool,
    arithmetic_quality_backed: bool,
    precision_level: int,
    precision_dimension_label: str,
    precision_dimension_rank: int,
    promotion_blocker: str | None,
    structural_mismatch: JsonDict | None,
    quality_meta: JsonDict,
    workload_id: str,
) -> JsonDict:
    contract = dict(row["model_contract"])
    throughput = dict(row["throughput"])
    physical = dict(row["physical"])
    energy = dict(row["energy"])
    return {
        "candidate_id": row["candidate_id"],
        "workload_id": workload_id,
        "source_model_contract": contract,
        "promotable": promotable,
        "quality_backed": quality_backed,
        "structural_quality_backed": structural_quality_backed,
        "arithmetic_quality_backed": arithmetic_quality_backed,
        "precision_level": precision_level,
        "precision_dimension_label": precision_dimension_label,
        "precision_dimension_rank": precision_dimension_rank,
        "token_throughput_per_s": _positive(throughput.get("token_throughput_per_s"), "token throughput"),
        "token_latency_us": _positive(throughput.get("token_latency_us"), "token latency"),
        "embodied_area_mm2": _embodied_area_mm2(physical, source_label=str(row["candidate_id"])),
        "energy_mj_per_token": _positive(
            energy.get("total_proxy_energy_mj_per_token"),
            f"{row['candidate_id']} total_proxy_energy_mj_per_token",
        ),
        "remaining_abstractions": [str(item) for item in row.get("remaining_abstractions", [])],
        "promotion_blocker": promotion_blocker,
        "structural_mismatch": structural_mismatch,
        "quality_validation": quality_meta,
    }


def _fp16_row(source: JsonDict) -> JsonDict:
    return {
        "candidate_id": source["candidate_id"],
        "workload_id": "legacy_llama7b_gqa8_131k_accounting",
        "source_model_contract": {
            "contract_scope": "measured_exact_fp16_gqa8_engineering_reference",
            "attention_heads": 32,
            "kv_heads": 4,
            "gqa_group_size": 8,
            "kv_sharing": "gqa8",
        },
        "promotable": False,
        "quality_backed": False,
        "structural_quality_backed": False,
        "arithmetic_quality_backed": True,
        "precision_level": 2,
        "precision_dimension_label": "exact_fp16_gqa8_reference",
        "precision_dimension_rank": 2,
        "token_throughput_per_s": _positive(source.get("token_throughput_per_s"), "fp16 throughput"),
        "token_latency_us": _positive(source.get("latency_us"), "fp16 latency"),
        "embodied_area_mm2": None,
        "compute_area_mm2": _positive(source.get("compute_area_mm2"), "fp16 compute area"),
        "die_envelope_mm2": _positive(source.get("die_area_mm2"), "fp16 die envelope"),
        "area_metric_status": "compute_only_not_total_embodied_noncomparable",
        "energy_mj_per_token": _positive(source.get("energy_mj_per_token"), "fp16 energy"),
        "remaining_abstractions": [
            *[str(item) for item in source.get("remaining_abstractions", [])],
            "Exact FP16 MHA has not been physically recosted on the same accounting boundary.",
        ],
        "promotion_blocker": "The measured exact-FP16 reference remains GQA8 rather than exact Llama-2-7B MHA.",
        "structural_mismatch": {
            "hardware_kv_sharing": "gqa8",
            "exact_llama2_kv_sharing": "mha",
            "reason": "The measured FP16 engineering reference is structurally mismatched to exact Llama-2-7B.",
        },
        "quality_validation": {
            "decision_status": None,
            "model_id": None,
        },
    }


def _precision_rank(row: JsonDict) -> int:
    return int(row["precision_dimension_rank"])


def _dominates(left: JsonDict, right: JsonDict) -> bool:
    comparisons = (
        float(left["token_throughput_per_s"]) >= float(right["token_throughput_per_s"]),
        float(left["embodied_area_mm2"]) <= float(right["embodied_area_mm2"]),
        float(left["energy_mj_per_token"]) <= float(right["energy_mj_per_token"]),
        _precision_rank(left) >= _precision_rank(right),
    )
    strict = (
        float(left["token_throughput_per_s"]) > float(right["token_throughput_per_s"]),
        float(left["embodied_area_mm2"]) < float(right["embodied_area_mm2"]),
        float(left["energy_mj_per_token"]) < float(right["energy_mj_per_token"]),
        _precision_rank(left) > _precision_rank(right),
    )
    return all(comparisons) and any(strict)


def _pareto_rows(rows: list[JsonDict]) -> list[JsonDict]:
    frontier: list[JsonDict] = []
    for row in rows:
        dominators = [other["candidate_id"] for other in rows if other is not row and _dominates(other, row)]
        if not dominators:
            frontier.append({**row, "pareto_reason": "not dominated across throughput, embodied area, energy, and precision"})
    return frontier


def _winner(rows: list[JsonDict], key: str, *, maximize: bool) -> str | list[str]:
    values = [float(row[key]) for row in rows]
    target = max(values) if maximize else min(values)
    winners = [str(row["candidate_id"]) for row, value in zip(rows, values) if value == target]
    return winners[0] if len(winners) == 1 else winners


def _precision_winner(rows: list[JsonDict]) -> str | list[str]:
    values = [_precision_rank(row) for row in rows]
    target = max(values)
    winners = [str(row["candidate_id"]) for row, value in zip(rows, values) if value == target]
    return winners[0] if len(winners) == 1 else winners


def build_report(*, recost: JsonDict, generation_quality: JsonDict, quality_frontier: JsonDict) -> JsonDict:
    corrected_gqa8, long_context_mha, exact_mha = _validate_recost(recost)
    quality = _validate_generation_quality(generation_quality)
    fp16_reference, excluded_history = _validate_quality_frontier(quality_frontier)

    gqa8_row = _recost_engineering_row(
        corrected_gqa8,
        promotable=False,
        quality_backed=False,
        structural_quality_backed=False,
        arithmetic_quality_backed=False,
        precision_level=1,
        precision_dimension_label="score32_exp_lut_div",
        precision_dimension_rank=1,
        promotion_blocker="Corrected GQA8 score32 remains structurally mismatched to exact Llama-2-7B MHA.",
        structural_mismatch={
            "hardware_kv_sharing": "gqa8",
            "exact_llama2_kv_sharing": "mha",
            "reason": "Corrected GQA8 score32 does not match the exact 32-KV-head Llama-2-7B structure.",
        },
        quality_meta=quality,
        workload_id="long_context_131072_extrapolation",
    )

    long_context_mha_row = _recost_engineering_row(
        long_context_mha,
        promotable=False,
        quality_backed=False,
        structural_quality_backed=True,
        arithmetic_quality_backed=False,
        precision_level=1,
        precision_dimension_label="score32_exp_lut_div",
        precision_dimension_rank=1,
        promotion_blocker=(
            "The 131k MHA extrapolation exceeds the official checkpoint context and lacks matching long-context quality evidence."
        ),
        structural_mismatch={
            "hardware_kv_sharing": "mha",
            "sequence_length": 131072,
            "official_native_context_length": 4096,
            "reason": "MHA dimensions match, but the workload context does not match the official checkpoint contract.",
        },
        quality_meta=quality,
        workload_id="long_context_131072_extrapolation",
    )

    exact_quality_pass = quality["decision_status"] == _QUALITY_PASS
    exact_mha_row = _recost_engineering_row(
        exact_mha,
        promotable=exact_quality_pass,
        quality_backed=exact_quality_pass,
        structural_quality_backed=True,
        arithmetic_quality_backed=exact_quality_pass,
        precision_level=1,
        precision_dimension_label="score32_exp_lut_div",
        precision_dimension_rank=1,
        promotion_blocker=None if exact_quality_pass else "Exact score32 MHA lacks a passing native Llama-2-7B generation-quality gate.",
        structural_mismatch=None,
        quality_meta=quality,
        workload_id="official_llama2_7b_native_context_4096",
    )
    fp16_row = _fp16_row(fp16_reference)

    long_context_rows = [gqa8_row, long_context_mha_row]
    native_context_rows = [exact_mha_row]
    all_rows = [*long_context_rows, *native_context_rows, fp16_row]
    engineering_pareto_by_workload = {
        "long_context_131072_extrapolation": _pareto_rows(long_context_rows),
        "official_llama2_7b_native_context_4096": _pareto_rows(native_context_rows),
    }
    promotable_rows = [row for row in native_context_rows if row["promotable"] and row["quality_backed"]]
    promotable_pareto = _pareto_rows(promotable_rows)

    dimension_winners_by_workload = {
        "long_context_131072_extrapolation": {
            "throughput": _winner(long_context_rows, "token_throughput_per_s", maximize=True),
            "embodied_area": _winner(long_context_rows, "embodied_area_mm2", maximize=False),
            "energy": _winner(long_context_rows, "energy_mj_per_token", maximize=False),
            "precision": _precision_winner(long_context_rows),
        },
        "official_llama2_7b_native_context_4096": {
            "throughput": exact_mha_row["candidate_id"],
            "embodied_area": exact_mha_row["candidate_id"],
            "energy": exact_mha_row["candidate_id"],
            "precision": exact_mha_row["candidate_id"],
        },
    }
    noncomparable_reference_winners = {
        "higher_precision_noncomparable_reference": fp16_row["candidate_id"],
    }

    remaining_abstractions = sorted(
        {
            *[item for row in all_rows for item in row["remaining_abstractions"]],
            *[str(item) for item in recost.get("remaining_abstractions", [])],
            "HBM controller service remains deterministic global replay rather than controller RTL or vendor timing signoff.",
            "Logic energy remains a vectorless activity proxy rather than workload-toggle-complete power.",
            "Fixed shared-SRAM residency is recosted but not reoptimized for exact MHA.",
            "Native exact Llama-2-7B quality is bounded to a limited prompt sample rather than a full benchmark suite.",
            "The 131072-token stress workload is a long-context extrapolation beyond the official Llama-2-7B 4096-token context and is not quality-backed.",
            "Exact FP16 MHA has not been physically recosted on the same accounting boundary.",
        }
    )

    decision = _DECISION_PASS if exact_quality_pass else _DECISION_HOLD
    return {
        "version": 1,
        "model": _MODEL_ID,
        "decision": decision,
        "source_items": {
            "global_hbm_exact_mha_recost": "l2_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1",
            "exact_native_generation_quality": "l2_decoder_attention_score32_exact_llama2_mha_generation_quality_v1",
            "quality_aware_frontier_reference": (
                "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_frontier_llama7b_v1"
            ),
        },
        "dimension_winners_by_workload": dimension_winners_by_workload,
        "dimension_winner_scope": "rows are compared only within identical sequence-length and total-embodied-area boundaries",
        "noncomparable_reference_winners": noncomparable_reference_winners,
        "scalar_universal_winner": None,
        "conditional_recommendation": {
            "universal_winner": None,
            "promotable_frontier_available": bool(promotable_pareto),
            "reason": (
                "Exact score32 MHA has a passing native Llama-2-7B quality contract."
                if exact_quality_pass
                else "Exact score32 MHA is still held behind the native Llama-2-7B quality gate."
            ),
        },
        "precision_contract": {
            "candidate_id": _SCORE32_PRECISION["candidate_id"],
            "q_bits": _SCORE32_PRECISION["q_bits"],
            "k_bits": _SCORE32_PRECISION["k_bits"],
            "v_bits": _SCORE32_PRECISION["v_bits"],
            "score_bits": _SCORE32_PRECISION["score_bits"],
            "weight_bits": _SCORE32_PRECISION["weight_bits"],
            "softmax_mode": _SCORE32_PRECISION["softmax_mode"],
        },
        "quality_contract": quality,
        "engineering_pareto_frontiers_by_workload": engineering_pareto_by_workload,
        "promotable_pareto_frontier": promotable_pareto,
        "noncomparable_reference_rows": [fp16_row],
        "all_rows": all_rows,
        "excluded_nonpromotable_history": excluded_history,
        "remaining_abstractions": remaining_abstractions,
        "next_measurements": [
            "Recost exact FP16 MHA on the same embodied-area and energy accounting boundary.",
            "Optimize fixed shared-SRAM residency for the exact MHA point rather than inheriting the GQA8 policy.",
            "Expand native exact Llama-2-7B quality beyond the bounded prompt sample.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    engineering_by_workload = payload["engineering_pareto_frontiers_by_workload"]
    promotable = payload["promotable_pareto_frontier"]
    lines = [
        "# Exact Llama-2-7B Score32 Final Frontier",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']}`",
        "- scalar universal winner: `None`",
        "",
        "## Dimension Winners By Workload",
        "",
    ]
    for workload_id, winners in payload["dimension_winners_by_workload"].items():
        lines.append(f"- `{workload_id}`: `{winners}`")
    lines.append(
        f"- higher-precision noncomparable reference: `{payload['noncomparable_reference_winners']['higher_precision_noncomparable_reference']}`"
    )
    for workload_id, engineering in engineering_by_workload.items():
        lines.extend(
            [
                "",
                f"## Engineering Pareto: {workload_id}",
                "",
                "| Candidate | Throughput token/s | Embodied area mm2 | Energy mJ/token | Precision | Promotable |",
                "|---|---:|---:|---:|---|---|",
            ]
        )
        for row in engineering:
            lines.append(
                "| {candidate_id} | {token_throughput_per_s} | {embodied_area_mm2} | {energy_mj_per_token} | {precision_dimension_label} | {promotable} |".format(
                    **row
                )
            )
    lines.extend(["", "## Promotable Pareto", ""])
    if promotable:
        lines.extend(
            [
                "| Candidate | Throughput token/s | Embodied area mm2 | Energy mJ/token |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in promotable:
            lines.append(
                "| {candidate_id} | {token_throughput_per_s} | {embodied_area_mm2} | {energy_mj_per_token} |".format(
                    **row
                )
            )
    else:
        lines.append("- No promotable frontier row is currently available.")
    lines.extend(["", "## Noncomparable References", ""])
    for row in payload["noncomparable_reference_rows"]:
        lines.append(
            f"- `{row['candidate_id']}`: {row['area_metric_status']}; excluded from cross-objective Pareto ranking."
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--exact-mha-recost-json", type=Path, default=DEFAULT_RECOST)
    parser.add_argument("--exact-generation-quality-json", type=Path, default=DEFAULT_GENERATION_QUALITY)
    parser.add_argument("--prior-quality-frontier-json", type=Path, default=DEFAULT_QUALITY_FRONTIER)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    payload = build_report(
        recost=_load_json(root / args.exact_mha_recost_json),
        generation_quality=_load_json(root / args.exact_generation_quality_json),
        quality_frontier=_load_json(root / args.prior_quality_frontier_json),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
