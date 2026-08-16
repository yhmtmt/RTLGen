#!/usr/bin/env python3
"""Build the final multidimensional Llama7B frontier after finite-endpoint recost."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

_BASE = Path("runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1")
DEFAULT_FINITE_RECOST = _BASE / (
    "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost__"
    "l2_decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost_llama7b_v1.json"
)
DEFAULT_QUALITY_FRONTIER = _BASE / (
    "decoder_attention_score32_integrated_frontier_ranking__"
    "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_frontier_"
    "llama7b_v1.json"
)
DEFAULT_GENERATION_QUALITY = _BASE / (
    "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
    "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
)

_RECOST_PROFILE = "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost"
_FRONTIER_MODEL = "llm_decoder_attention_score32_integrated_frontier_ranking_v1"
_SCORE32_FAMILY = "score32_exp_lut_div"
_FP16_FAMILY = "measured_exact_fp16_gqa8_kv8"


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


def _validate_finite_recost(payload: JsonDict) -> JsonDict:
    if payload.get("version") != 1 or payload.get("model") != "llama7b_proxy":
        raise ValueError("finite recost model/version mismatch")
    if payload.get("profile") != _RECOST_PROFILE:
        raise ValueError("finite recost profile mismatch")
    if payload.get("decision") != "score32_noc_phase2_finite_endpoint_composed_recost_recorded":
        raise ValueError("finite recost decision mismatch")
    closure = payload.get("closure_flags")
    throughput = payload.get("throughput")
    physical = payload.get("physical_recost")
    precision = payload.get("precision_contract")
    model_contract = payload.get("model_contract")
    if not all(
        isinstance(section, dict)
        for section in (closure, throughput, physical, precision, model_contract)
    ):
        raise ValueError("finite recost is missing required sections")
    required_flags = (
        "finite_endpoint_and_mesh_cycle_equivalence_consumed",
        "aggregate_endpoint_mesh_ppa_consumed",
        "prior_primitive_area_power_replaced_not_added",
    )
    if not all(closure.get(flag) is True for flag in required_flags):
        raise ValueError("finite recost does not close every required communication flag")
    if physical.get("area_fit") is not True:
        raise ValueError("finite recost does not fit its die envelope")
    if precision.get("arithmetic_changed_by_this_recost") is not False:
        raise ValueError("finite recost must preserve arithmetic semantics")
    if model_contract.get("contract_scope") != "llama7b_shaped_gqa8_proxy_not_exact_llama2_7b":
        raise ValueError("finite recost model contract scope mismatch")
    if model_contract.get("attention_heads") != 32 or model_contract.get("kv_heads") != 4:
        raise ValueError("finite recost must expose the exact 32-head/4-KV-head structure")
    if model_contract.get("gqa_group_size") != 8 or model_contract.get("kv_sharing") != "gqa8":
        raise ValueError("finite recost must expose the exact GQA8 structure")
    return payload


def _validate_generation_quality(payload: JsonDict) -> JsonDict:
    if float(payload.get("version", 0.0)) != 1.0:
        raise ValueError("generation quality version mismatch")
    if payload.get("quality_gate") != "mixed_int8_generation_quality":
        raise ValueError("generation quality gate mismatch")
    model = payload.get("model")
    precision = payload.get("precision")
    decision = payload.get("decision")
    if not all(isinstance(section, dict) for section in (model, precision, decision)):
        raise ValueError("generation quality is missing required sections")
    expected_precision = {
        "candidate_id": "score32_exp_lut_div",
        "q_bits": 8,
        "k_bits": 8,
        "v_bits": 8,
        "score_bits": 32,
        "weight_bits": 16,
        "softmax_mode": "exp_lut_div_bucket20",
    }
    mismatches = {
        key: {"expected": expected, "observed": precision.get(key)}
        for key, expected in expected_precision.items()
        if precision.get(key) != expected
    }
    if mismatches:
        raise ValueError(f"generation quality precision mismatch: {mismatches}")
    if decision.get("status") != "mixed_int8_generation_quality_pass":
        raise ValueError("generation quality decision is not passing")
    return {
        "model_id": model.get("model_id"),
        "gqa_group_size": _positive(model.get("gqa_group_size"), "quality GQA group size"),
        "prompt_count": payload.get("summary", {}).get("prompt_count"),
        "generation_steps": model.get("generation_steps"),
        "decision_status": decision.get("status"),
        "precision": precision,
    }


def _frontier_rows(payload: JsonDict) -> tuple[JsonDict, JsonDict, list[JsonDict]]:
    if payload.get("version") != 1 or payload.get("model") != _FRONTIER_MODEL:
        raise ValueError("quality frontier model/version mismatch")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("quality frontier rows are missing")
    valid_rows = [dict(row) for row in rows if isinstance(row, dict)]

    def unique_family(family: str) -> JsonDict:
        matches = [row for row in valid_rows if row.get("family") == family]
        if len(matches) != 1:
            raise ValueError(f"quality frontier must contain exactly one {family} row")
        row = matches[0]
        if row.get("promotable") is not True or row.get("quality_backed") is not True:
            raise ValueError(f"{family} row must be promotable and quality-backed")
        return row

    return unique_family(_SCORE32_FAMILY), unique_family(_FP16_FAMILY), valid_rows


def _score32_row(recost: JsonDict, source: JsonDict, generation_quality: JsonDict) -> JsonDict:
    throughput = dict(recost["throughput"])
    physical = dict(recost["physical_recost"])
    precision = dict(recost["precision_contract"])
    model_contract = dict(recost["model_contract"])
    controller = dict(source.get("score32_hbm_controller_replay_ppa") or {})
    token_latency_us = _positive(throughput.get("token_latency_us"), "score32 token latency")
    logic_energy_mj = _positive(
        physical.get("recost_logic_vectorless_energy_per_token_mj"),
        "score32 recost logic energy",
    )
    hbm_energy_mj = _positive(source.get("hbm_energy_mj_per_token"), "score32 HBM energy")
    controller_power_mw = _positive(controller.get("controller_power_mw"), "controller power")
    controller_area_mm2 = _positive(controller.get("controller_area_mm2"), "controller area")
    controller_energy_mj = controller_power_mw * token_latency_us * 1.0e-6
    total_energy_mj = logic_energy_mj + hbm_energy_mj + controller_energy_mj
    recost_embodied_area_mm2 = _positive(
        physical.get("total_embodied_area_um2"), "score32 embodied area"
    ) / 1.0e6
    total_embodied_area_mm2 = recost_embodied_area_mm2 + controller_area_mm2
    die_area_mm2 = _positive(physical.get("die_area_um2"), "score32 die area") / 1.0e6
    if total_embodied_area_mm2 > die_area_mm2:
        raise ValueError("score32 recost plus HBM replay controller exceeds the die envelope")
    quality = dict(source.get("quality") or {})
    if quality.get("quality_backed") is not True or not str(quality.get("status", "")).endswith("_pass"):
        raise ValueError("score32 quality evidence is not passing")
    architecture_gqa = _positive(model_contract.get("gqa_group_size"), "architecture GQA group size")
    measured_gqa = _positive(generation_quality.get("gqa_group_size"), "measured GQA group size")
    structural_quality_backed = architecture_gqa == measured_gqa
    return {
        "candidate_id": "score32_finite_endpoint_composed_quality_backed",
        "family": _SCORE32_FAMILY,
        "promotable": structural_quality_backed,
        "quality_backed": structural_quality_backed,
        "arithmetic_quality_backed": True,
        "structural_quality_backed": structural_quality_backed,
        "architecture_model_contract": model_contract,
        "generation_quality_contract": generation_quality,
        "structural_quality_mismatch": (
            None
            if structural_quality_backed
            else {
                "architecture_gqa_group_size": architecture_gqa,
                "measured_checkpoint_gqa_group_size": measured_gqa,
                "reason": "Mistral-7B GQA4 arithmetic evidence does not validate the GQA8 hardware structure.",
            }
        ),
        "precision_class": "approximate_q8_k8_v8_score32_weight16_exp_lut_div",
        "precision_profile": precision.get("precision_profile"),
        "semantic_profile": precision.get("semantic_profile"),
        "quality": quality,
        "token_throughput_per_s": _positive(
            throughput.get("token_throughput_per_s"), "score32 throughput"
        ),
        "token_latency_us": token_latency_us,
        "bottleneck": throughput.get("bottleneck"),
        "die_envelope_mm2": die_area_mm2,
        "finite_recost_embodied_area_mm2": recost_embodied_area_mm2,
        "hbm_controller_area_mm2": controller_area_mm2,
        "total_embodied_area_mm2": total_embodied_area_mm2,
        "area_status": "placed_logic_plus_measured_sram_area_plus_reserved_die_fraction",
        "logic_vectorless_energy_mj_per_token": logic_energy_mj,
        "hbm_source_backed_energy_mj_per_token": hbm_energy_mj,
        "hbm_controller_vectorless_energy_mj_per_token": controller_energy_mj,
        "energy_mj_per_token": total_energy_mj,
        "energy_status": "vectorless_onchip_logic_plus_source_backed_hbm_and_measured_controller",
        "source_candidate_id": source.get("candidate_id"),
        "remaining_abstractions": sorted(
            {
                *[str(item) for item in recost.get("remaining_abstractions", [])],
                *[str(item) for item in source.get("remaining_abstractions", [])],
                "The combined score32 energy is not workload-toggle-complete for the composed NoC and SRAM macros.",
                "The GQA8 structural transformation lacks trained-checkpoint or QAT quality evidence.",
            }
        ),
    }


def _fp16_row(source: JsonDict) -> JsonDict:
    return {
        "candidate_id": source.get("candidate_id"),
        "family": _FP16_FAMILY,
        "promotable": False,
        "quality_backed": False,
        "arithmetic_quality_backed": True,
        "structural_quality_backed": False,
        "structural_quality_mismatch": {
            "hardware_kv_sharing": "gqa8",
            "exact_llama2_7b_kv_sharing": "mha",
            "reason": "The measured FP16 row also uses GQA8 and lacks exact Llama-2-7B MHA physical recost.",
        },
        "precision_class": "measured_exact_fp16_with_native_gqa8_kv8",
        "precision_profile": source.get("precision_status"),
        "token_throughput_per_s": _positive(source.get("token_throughput_per_s"), "FP16 throughput"),
        "token_latency_us": _positive(source.get("latency_us"), "FP16 latency"),
        "die_envelope_mm2": _positive(source.get("die_area_mm2"), "FP16 die area"),
        "total_embodied_area_mm2": None,
        "area_status": "die_envelope_only_total_embodied_area_not_materialized",
        "energy_mj_per_token": _positive(source.get("energy_mj_per_token"), "FP16 energy"),
        "energy_status": source.get("abstraction_status"),
        "remaining_abstractions": [
            *list(source.get("remaining_abstractions") or []),
            "Exact Llama-2-7B MHA (32 KV heads) has not been carried through the physical frontier.",
        ],
    }


def _precision_level(row: JsonDict) -> int:
    return 2 if row.get("family") == _FP16_FAMILY else 1


def _winner(rows: list[JsonDict], key: str, *, maximize: bool) -> str | list[str]:
    values = [float(row[key]) for row in rows]
    target = max(values) if maximize else min(values)
    winners = [str(row["candidate_id"]) for row, value in zip(rows, values) if value == target]
    return winners[0] if len(winners) == 1 else winners


def _dominates(left: JsonDict, right: JsonDict) -> bool:
    comparisons = (
        float(left["token_throughput_per_s"]) >= float(right["token_throughput_per_s"]),
        float(left["die_envelope_mm2"]) <= float(right["die_envelope_mm2"]),
        float(left["energy_mj_per_token"]) <= float(right["energy_mj_per_token"]),
        _precision_level(left) >= _precision_level(right),
    )
    strict = (
        float(left["token_throughput_per_s"]) > float(right["token_throughput_per_s"]),
        float(left["die_envelope_mm2"]) < float(right["die_envelope_mm2"]),
        float(left["energy_mj_per_token"]) < float(right["energy_mj_per_token"]),
        _precision_level(left) > _precision_level(right),
    )
    return all(comparisons) and any(strict)


def _pareto_rows(rows: list[JsonDict]) -> list[JsonDict]:
    result: list[JsonDict] = []
    for row in rows:
        dominators = [other["candidate_id"] for other in rows if other is not row and _dominates(other, row)]
        if not dominators:
            result.append({**row, "pareto_reason": "not dominated across all four objectives"})
    return result


def build_report(
    *, finite_recost: JsonDict, quality_frontier: JsonDict, generation_quality: JsonDict
) -> JsonDict:
    recost = _validate_finite_recost(finite_recost)
    generation = _validate_generation_quality(generation_quality)
    prior_score32, prior_fp16, all_prior_rows = _frontier_rows(quality_frontier)
    score32 = _score32_row(recost, prior_score32, generation)
    fp16 = _fp16_row(prior_fp16)
    candidates = [score32, fp16]
    engineering_pareto = _pareto_rows(candidates)
    promotable_candidates = [row for row in candidates if row["promotable"] and row["quality_backed"]]
    promotable_pareto = _pareto_rows(promotable_candidates)
    dimension_winners = {
        "token_throughput": _winner(candidates, "token_throughput_per_s", maximize=True),
        "die_envelope_area": _winner(candidates, "die_envelope_mm2", maximize=False),
        "energy_per_token": _winner(candidates, "energy_mj_per_token", maximize=False),
        "arithmetic_precision": fp16["candidate_id"],
    }
    excluded = [
        {
            "candidate_id": row.get("candidate_id"),
            "family": row.get("family"),
            "reason": row.get("precision_status") or row.get("abstraction_status"),
        }
        for row in all_prior_rows
        if row.get("promotable") is not True or row.get("quality_backed") is not True
    ]
    return {
        "version": 1,
        "model": "llama7b_score32_finite_endpoint_final_frontier_v1",
        "decision": (
            "no_structurally_quality_backed_exact_llama7b_point"
            if not promotable_pareto
            else "structurally_quality_backed_frontier_available"
        ),
        "source_items": {
            "finite_endpoint_composed_recost": (
                "l2_decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost_llama7b_v1"
            ),
            "quality_aware_frontier": (
                "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_"
                "rtl_ppa_recost_frontier_llama7b_v1"
            ),
            "generation_quality": (
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_"
                "generation_quality_llama7b_v1"
            ),
        },
        "dimension_winners": dimension_winners,
        "dimension_winner_scope": "engineering_metrics_before_structural_quality_promotion",
        "conditional_recommendation": {
            "provisional_throughput_under_800mm2": score32["candidate_id"],
            "energy_first": dimension_winners["energy_per_token"],
            "precision_first": dimension_winners["arithmetic_precision"],
            "unconditional_best": None,
            "reason": "No physical row matches an exact Llama-2-7B structural quality contract.",
        },
        "pareto_frontier": promotable_pareto,
        "engineering_pareto_frontier": engineering_pareto,
        "excluded_nonpromotable_history": excluded,
        "comparison_limits": [
            "Score32 has total embodied area; the FP16 reference currently exposes only its die envelope and compute area.",
            "Score32 energy uses vectorless composed-logic power plus source-backed HBM energy, not workload-complete NoC/SRAM activity.",
            "The bounded Mistral-7B quality gate is evidence for the Llama7B-class arithmetic profile, not a full Llama-2-7B benchmark suite.",
            "The physical rows use GQA8 while Mistral-7B quality uses GQA4 and exact Llama-2-7B uses MHA.",
        ],
        "remaining_abstractions": sorted(
            {
                *score32["remaining_abstractions"],
                *[str(item) for item in fp16["remaining_abstractions"]],
                "FP16 total embodied SRAM/NoC area is not materialized on the same accounting boundary.",
            }
        ),
        "next_measurements": [
            "Capture workload activity for the composed score32 endpoint/mesh and SRAM macro ports.",
            "Materialize FP16 total embodied area on the same die/SRAM/NoC accounting boundary.",
            "Expand native 7B generation quality beyond the bounded eight-prompt gate.",
            "Recost the exact Llama-2-7B MHA structure with 32 KV heads, or provide trained GQA8/QAT weights.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    rows = payload["engineering_pareto_frontier"]
    lines = [
        "# Llama7B Finite-Endpoint Final Frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- unconditional best: `{payload['conditional_recommendation']['unconditional_best']}`",
        "- table scope: engineering metrics; structural promotion is reported explicitly",
        "",
        "| Candidate | Throughput token/s | Die envelope mm2 | Embodied area mm2 | Energy mJ/token | Precision | Structural quality | Promotable |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {token_throughput_per_s} | {die_envelope_mm2} | {area} | "
            "{energy_mj_per_token} | {precision_class} | {structural_quality_backed} | {promotable} |".format(
                **row,
                area=row.get("total_embodied_area_mm2"),
            )
        )
    lines.extend(["", "## Dimension Winners", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in payload["dimension_winners"].items())
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--finite-recost-json", type=Path, default=DEFAULT_FINITE_RECOST)
    parser.add_argument("--quality-frontier-json", type=Path, default=DEFAULT_QUALITY_FRONTIER)
    parser.add_argument("--generation-quality-json", type=Path, default=DEFAULT_GENERATION_QUALITY)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    payload = build_report(
        finite_recost=_load_json(root / args.finite_recost_json),
        quality_frontier=_load_json(root / args.quality_frontier_json),
        generation_quality=_load_json(root / args.generation_quality_json),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
