#!/usr/bin/env python3
"""Reconcile mixed-int8 energy closure with broad native attention quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object at {path}")
    return payload


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _candidate_summaries(quality: JsonDict) -> list[JsonDict]:
    rows = quality.get("candidate_summaries")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _is_pass(row: JsonDict) -> bool:
    status = str(row.get("decision_status") or (row.get("decision") or {}).get("status") or "")
    return status.endswith("_pass")


def _quality_precision(row: JsonDict) -> JsonDict:
    return {
        "candidate_id": row.get("candidate_id"),
        "q_bits": row.get("q_bits"),
        "k_bits": row.get("k_bits"),
        "v_bits": row.get("v_bits"),
        "score_bits": row.get("score_bits"),
        "weight_bits": row.get("weight_bits"),
        "softmax_mode": row.get("softmax_mode"),
    }


def _energy_precision(row: JsonDict) -> JsonDict:
    return {
        "precision_profile": row.get("precision_profile"),
        "measured_softmax_weight_metrics_csv": row.get("measured_softmax_weight_metrics_csv"),
        "softmax_weight_generator_metrics_csv": row.get("softmax_weight_generator_metrics_csv"),
        "compute_arch": row.get("compute_arch") or row.get("substituted_compute_arch"),
        "compute_replica_count": row.get("compute_replica_count") or row.get("substituted_compute_replica_count"),
    }


def _energy_summary(row: JsonDict | None) -> JsonDict | None:
    if not isinstance(row, dict):
        return None
    return {
        "candidate_id": row.get("candidate_id"),
        "precision": _energy_precision(row),
        "latency_us": row.get("latency_us"),
        "token_throughput_per_s": row.get("token_throughput_per_s"),
        "energy_mj": row.get("energy_mj"),
        "die_area_mm2": row.get("die_area_mm2"),
        "compute_energy_mj": row.get("compute_energy_mj"),
        "hbm_energy_mj": row.get("hbm_energy_mj"),
        "sram_energy_mj": row.get("sram_energy_mj"),
        "noc_energy_mj": row.get("noc_energy_mj"),
        "dominant_energy_component": row.get("dominant_energy_component"),
    }


def _quality_summary(row: JsonDict) -> JsonDict:
    return {
        "candidate_id": row.get("candidate_id"),
        "decision_status": row.get("decision_status") or (row.get("decision") or {}).get("status"),
        "precision": _quality_precision(row),
        "comparison_count": row.get("comparison_count"),
        "top1_match_rate": row.get("top1_match_rate"),
        "topk_contains_rate": row.get("topk_contains_rate"),
        "mean_logit_cosine": row.get("mean_logit_cosine"),
        "mean_probability_kl": row.get("mean_probability_kl"),
        "max_abs_logit_delta_max": row.get("max_abs_logit_delta_max"),
    }


def _score_softmax_quantized(row: JsonDict) -> bool:
    precision = str(row.get("precision_profile") or "")
    softmax_paths = " ".join(
        str(row.get(key) or "")
        for key in ("measured_softmax_weight_metrics_csv", "softmax_weight_generator_metrics_csv")
    )
    return (
        "_s8_" in precision
        or "_w8_" in precision
        or "recip_lut" in precision
        or "int8" in softmax_paths
        or "recip_q" in softmax_paths
    )


def build_payload(args: argparse.Namespace) -> JsonDict:
    energy = _load_json(args.mixed_int8_energy_closure_json)
    quality = _load_json(args.mixed_int8_broad_native_quality_json)
    quality_rows = _candidate_summaries(quality)
    if not quality_rows:
        raise RuntimeError("broad native quality artifact contains no candidate_summaries")

    passing = [_quality_summary(row) for row in quality_rows if _is_pass(row)]
    held = [_quality_summary(row) for row in quality_rows if not _is_pass(row)]
    qkv8_float_exact = next(
        (row for row in quality_rows if str(row.get("candidate_id")) == "qkv8_float_exact"),
        None,
    )
    qkv8_pass = qkv8_float_exact is not None and _is_pass(qkv8_float_exact)

    energy_best = energy.get("best") if isinstance(energy.get("best"), dict) else {}
    latency_best = energy.get("latency_best") if isinstance(energy.get("latency_best"), dict) else {}
    energy_rows = [row for row in [energy_best, latency_best, *energy.get("pareto_rows", [])] if isinstance(row, dict)]
    invalidated_rows: list[JsonDict] = []
    seen: set[str] = set()
    for row in energy_rows:
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id in seen:
            continue
        seen.add(candidate_id)
        if _score_softmax_quantized(row):
            invalidated_rows.append(
                {
                    **(_energy_summary(row) or {}),
                    "quality_frontier_status": "invalid_for_quality_backed_ranking",
                    "reason": (
                        "energy row uses score/softmax quantization or reciprocal-LUT softmax evidence, "
                        "while broad native quality only passed qkv8_float_exact"
                    ),
                }
            )

    decision = "mixed_int8_quality_backed_frontier_recost_required"
    recommended_next_step = (
        "Recompute the Llama7B energy frontier for q8/k8/v8 projection quantization with "
        "high-precision or exact score/softmax PPA; do not rank the old s8/w8 reciprocal-LUT energy row."
    )
    if not qkv8_pass:
        decision = "mixed_int8_quality_backed_frontier_no_passing_candidate"
        recommended_next_step = "No mixed-int8 attention candidate passed the broad native quality gate; return to precision search."
    elif not invalidated_rows:
        decision = "mixed_int8_quality_backed_frontier_recorded"
        recommended_next_step = "Inspect whether the energy closure already matches the passing qkv8_float_exact precision path."

    best_quality = _quality_summary(qkv8_float_exact) if isinstance(qkv8_float_exact, dict) else None
    old_best = _energy_summary(energy_best)
    latency_floor = _as_float((old_best or {}).get("latency_us"))
    old_throughput = _as_float((old_best or {}).get("token_throughput_per_s"))

    return {
        "version": 1,
        "model": "llm_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
        "decision": decision,
        "quality_gate_status": (quality.get("decision") or {}).get("status") if isinstance(quality.get("decision"), dict) else None,
        "inputs": {
            "mixed_int8_energy_closure_json": str(args.mixed_int8_energy_closure_json),
            "mixed_int8_broad_native_quality_json": str(args.mixed_int8_broad_native_quality_json),
        },
        "diagnosis": {
            "decision": decision,
            "quality_candidate_count": len(quality_rows),
            "quality_passing_candidate_count": len(passing),
            "quality_passing_candidate_ids": [row.get("candidate_id") for row in passing],
            "quality_best_candidate_id": (best_quality or {}).get("candidate_id"),
            "quality_best_top1_match_rate": (best_quality or {}).get("top1_match_rate"),
            "quality_best_mean_probability_kl": (best_quality or {}).get("mean_probability_kl"),
            "invalidated_energy_candidate_count": len(invalidated_rows),
            "old_energy_best_candidate_id": (old_best or {}).get("candidate_id"),
            "old_energy_best_latency_us": (old_best or {}).get("latency_us"),
            "old_energy_best_token_throughput_per_s": (old_best or {}).get("token_throughput_per_s"),
            "old_energy_best_energy_mj": (old_best or {}).get("energy_mj"),
            "old_energy_best_precision_profile": ((old_best or {}).get("precision") or {}).get("precision_profile"),
            "quality_backed_latency_floor_us_unranked": latency_floor if invalidated_rows else None,
            "quality_backed_throughput_floor_tok_s_unranked": old_throughput if invalidated_rows else None,
            "recommended_next_step": recommended_next_step,
        },
        "quality_backed_direction": {
            "status": "quality_pass_requires_energy_recost" if qkv8_pass else "no_quality_pass",
            "candidate": best_quality,
            "rankable_for_energy_frontier": False if invalidated_rows else qkv8_pass,
            "recost_requirement": (
                "Substitute or measure high-precision/exact score-softmax PPA for the passing qkv8_float_exact path "
                "before comparing throughput, energy, or area against FP16/dense baselines."
            ),
        },
        "invalidated_energy_candidates": invalidated_rows,
        "quality_candidates": {
            "passing": passing,
            "held_or_failed": held,
        },
        "old_energy_best": old_best,
        "old_latency_best": _energy_summary(latency_best),
        "remaining_abstractions": [
            "The quality-passing qkv8_float_exact path has not yet been recosted with matching high-precision/exact score-softmax PPA.",
            "The previous mixed/int8 energy closure remains useful as a latency/traffic floor only; its s8/w8 reciprocal-LUT score-softmax precision is invalid for quality-backed ranking.",
            "This audit is an evidence reconciliation step and does not rerun OpenROAD or the native model quality gate.",
            "HBM/SRAM/NoC abstractions from the source energy closure remain unchanged until the recosted precision path is generated.",
        ],
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    diag = payload["diagnosis"]
    direction = payload["quality_backed_direction"]
    best = direction.get("candidate") or {}
    old_best = payload.get("old_energy_best") or {}
    lines = [
        "# Llama7B Mixed-Int8 Quality-Backed Frontier Audit",
        "",
        f"- decision: `{diag['decision']}`",
        f"- quality passing candidates: `{diag['quality_passing_candidate_ids']}`",
        f"- invalidated energy candidates: `{diag['invalidated_energy_candidate_count']}`",
        f"- recommended next step: `{diag['recommended_next_step']}`",
        "",
        "## Quality-Backed Direction",
        "",
        "| candidate | status | top1 | top-k | KL | rankable for energy frontier |",
        "|---|---|---:|---:|---:|---|",
        "| {candidate_id} | {decision_status} | {top1_match_rate} | {topk_contains_rate} | {mean_probability_kl} | {rankable} |".format(
            candidate_id=best.get("candidate_id"),
            decision_status=best.get("decision_status"),
            top1_match_rate=best.get("top1_match_rate"),
            topk_contains_rate=best.get("topk_contains_rate"),
            mean_probability_kl=best.get("mean_probability_kl"),
            rankable=direction.get("rankable_for_energy_frontier"),
        ),
        "",
        "## Previous Energy Best",
        "",
        "| candidate | precision profile | latency us | throughput tok/s | energy mJ | dominant | status |",
        "|---|---|---:|---:|---:|---|---|",
        "| {candidate_id} | {precision_profile} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {dominant_energy_component} | invalidated for quality-backed ranking |".format(
            candidate_id=old_best.get("candidate_id"),
            precision_profile=(old_best.get("precision") or {}).get("precision_profile"),
            latency_us=old_best.get("latency_us"),
            token_throughput_per_s=old_best.get("token_throughput_per_s"),
            energy_mj=old_best.get("energy_mj"),
            dominant_energy_component=old_best.get("dominant_energy_component"),
        ),
        "",
        "## Remaining Abstractions",
        "",
    ]
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mixed-int8-energy-closure-json", type=Path, required=True)
    parser.add_argument("--mixed-int8-broad-native-quality-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
