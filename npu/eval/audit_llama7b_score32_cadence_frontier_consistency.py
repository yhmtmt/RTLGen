#!/usr/bin/env python3
"""Audit whether the published Score32 frontier consumes current cadence evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRONTIER = REPO_ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_integrated_frontier_ranking__"
    "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_"
    "frontier_llama7b_v1.json"
)
DEFAULT_NORM = REPO_ROOT / "npu/docs/generated/llama7b_rmsnorm_macro_banked_latency_composition.json"
DEFAULT_CADENCE = REPO_ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_folded_global_exact_reduction_recost__"
    "l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json"
)


def _load(path: Path) -> JsonDict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def build_report(
    frontier: JsonDict,
    *,
    frontier_path: Path,
    norm: JsonDict,
    norm_path: Path,
    cadence: JsonDict,
    cadence_path: Path,
) -> JsonDict:
    if frontier.get("model") != "llm_decoder_attention_score32_integrated_frontier_ranking_v1":
        raise ValueError("unexpected integrated-frontier model")
    if norm.get("model") != "llama7b_rmsnorm_macro_banked_latency_composition_v2":
        raise ValueError("unexpected RMSNorm composition model")
    if cadence.get("model") != "llm_decoder_attention_score32_folded_global_exact_reduction_recost_v2":
        raise ValueError("unexpected cadence recost model")

    baseline = norm.get("baseline")
    scope = norm.get("attention_scope_proof")
    bounded = cadence.get("bounded_schedule_analysis")
    cadence_evidence = cadence.get("cadence_evidence")
    if not all(isinstance(value, dict) for value in (baseline, scope, bounded, cadence_evidence)):
        raise ValueError("missing baseline, scope, or cadence evidence")
    if scope.get("status") != "verified_attention_only_excludes_transformer_rmsnorm":
        raise ValueError("RMSNorm attention scope is not verified")
    if cadence_evidence.get("reference_986_cycles_sustained") is not False:
        raise ValueError("cadence evidence does not explicitly retract 986 cycles")

    terms = scope.get("layer_cycle_terms")
    if not isinstance(terms, dict):
        raise ValueError("missing layer cycle terms")
    old_tile_cycles = int(terms["tile_service_cycles"])
    tile_waves = int(terms["tile_waves"])
    if old_tile_cycles != int(cadence["summary"]["old_arithmetic_reference_cycles"]):
        raise ValueError("frontier and cadence reports do not share the superseded reference")
    old_attention_cycles = old_tile_cycles * tile_waves
    replacement_attention_cycles = int(bounded["strict_serialized_bound_all_4_groups_cycles"])
    recorded_layer_cycles = int(scope["recorded_layer_cycles"])
    corrected_layer_cycles = recorded_layer_cycles - old_attention_cycles + replacement_attention_cycles
    layers = int(scope["layers"])
    recorded_total_cycles = int(scope["recorded_total_cycles"])
    if recorded_total_cycles != recorded_layer_cycles * layers:
        raise ValueError("recorded cycle accounting is inconsistent")
    recorded_latency_us = float(baseline["latency_us"])
    clock_period_ns = recorded_latency_us * 1000.0 / recorded_total_cycles
    corrected_latency_us = corrected_layer_cycles * layers * clock_period_ns / 1000.0

    rows = frontier.get("rows")
    if not isinstance(rows, list):
        raise ValueError("frontier rows are missing")
    score32_id = str(baseline["candidate_id"])
    score32 = next((row for row in rows if row.get("candidate_id") == score32_id), None)
    competitors = [
        row for row in rows
        if row.get("candidate_id") != score32_id and row.get("promotable") and row.get("quality_backed")
    ]
    if not isinstance(score32, dict) or not competitors:
        raise ValueError("score32 baseline or credible competitor is missing")
    competitor = min(competitors, key=lambda row: float(row["latency_us"]))

    serialized = [
        row for row in norm.get("rows", [])
        if isinstance(row, dict) and float(row.get("hidden_fraction", -1.0)) == 0.0
    ]
    if not serialized:
        raise ValueError("serialized RMSNorm envelope is missing")
    correction_delta_us = corrected_latency_us - recorded_latency_us
    corrected_norm_latencies = [float(row["composed_latency_us"]) + correction_delta_us for row in serialized]
    competitor_latency_us = float(competitor["latency_us"])

    return {
        "version": 1,
        "model": "llama7b_score32_cadence_frontier_consistency_v1",
        "decision": "recorded_score32_latency_retracted_pending_cadence_integrated_recost",
        "sources": {
            "frontier": {"path": _portable(frontier_path), "sha256": _sha256(frontier_path)},
            "norm": {"path": _portable(norm_path), "sha256": _sha256(norm_path)},
            "cadence": {"path": _portable(cadence_path), "sha256": _sha256(cadence_path)},
        },
        "superseded_contract": {
            "tile_service_cycles": old_tile_cycles,
            "tile_waves": tile_waves,
            "attention_cycles_per_layer": old_attention_cycles,
            "recorded_layer_cycles": recorded_layer_cycles,
            "recorded_latency_us": recorded_latency_us,
            "physically_credible_latency_anchor": False,
        },
        "strict_serialized_sensitivity": {
            "replacement_attention_cycles_per_layer": replacement_attention_cycles,
            "corrected_layer_cycles": corrected_layer_cycles,
            "clock_period_ns_reconstructed": clock_period_ns,
            "latency_us_before_rmsnorm": corrected_latency_us,
            "token_throughput_per_s_before_rmsnorm": 1.0e6 / corrected_latency_us,
            "serialized_rmsnorm_latency_min_us": min(corrected_norm_latencies),
            "serialized_rmsnorm_latency_max_us": max(corrected_norm_latencies),
            "nearest_credible_competitor_id": str(competitor["candidate_id"]),
            "nearest_credible_competitor_latency_us": competitor_latency_us,
            "latency_lead_preserved_before_rmsnorm": corrected_latency_us < competitor_latency_us,
            "latency_lead_preserved_across_serialized_rmsnorm_envelope": max(corrected_norm_latencies) < competitor_latency_us,
            "claim_scope": "conservative timing sensitivity only; energy and area are not recost",
        },
        "pareto_status": {
            "recorded_two_point_set_physically_credible": False,
            "score32_membership": "unproven_pending_cadence_integrated_energy_area_recost",
            "exact_fp16_membership": "retained_as_current_measured_reference",
        },
        "blockers": [
            "the integrated frontier still consumes the superseded 986-cycle tile-service term",
            "the local 53/54-way persistent reducer and safe group overlap scheduler remain unresolved",
            "score32 energy has not been recomputed for the corrected service time or closed with activity",
        ],
    }


def render_markdown(report: JsonDict) -> str:
    old = report["superseded_contract"]
    new = report["strict_serialized_sensitivity"]
    lines = [
        "# Llama7B Score32 Cadence/Frontier Consistency Audit",
        "",
        f"- decision: `{report['decision']}`",
        f"- recorded two-point Pareto set physically credible: `{report['pareto_status']['recorded_two_point_set_physically_credible']}`",
        f"- superseded Score32 latency: `{old['recorded_latency_us']:.3f} us`",
        f"- strict serialized sensitivity before RMSNorm: `{new['latency_us_before_rmsnorm']:.3f} us`",
        f"- strict serialized sensitivity with RMSNorm: `{new['serialized_rmsnorm_latency_min_us']:.3f}--{new['serialized_rmsnorm_latency_max_us']:.3f} us`",
        f"- nearest measured reference latency: `{new['nearest_credible_competitor_latency_us']:.3f} us`",
        f"- conservative latency lead preserved: `{new['latency_lead_preserved_across_serialized_rmsnorm_envelope']}`",
        f"- claim scope: {new['claim_scope']}",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in report["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier", type=Path, default=DEFAULT_FRONTIER)
    parser.add_argument("--norm", type=Path, default=DEFAULT_NORM)
    parser.add_argument("--cadence", type=Path, default=DEFAULT_CADENCE)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    report = build_report(
        _load(args.frontier), frontier_path=args.frontier,
        norm=_load(args.norm), norm_path=args.norm,
        cadence=_load(args.cadence), cadence_path=args.cadence,
    )
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report), encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
