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
    "decoder_attention_score32_local_reducer_measured_recost__"
    "l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1_r1.json"
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
    if cadence.get("model") != "llm_decoder_attention_score32_local_reducer_measured_recost_v1":
        raise ValueError("unexpected cadence recost model")

    baseline = norm.get("baseline")
    scope = norm.get("attention_scope_proof")
    schedule = cadence.get("schedule_recost")
    summary = cadence.get("summary")
    if not all(isinstance(value, dict) for value in (baseline, scope, schedule, summary)):
        raise ValueError("missing baseline, scope, or cadence evidence")
    if scope.get("status") != "verified_attention_only_excludes_transformer_rmsnorm":
        raise ValueError("RMSNorm attention scope is not verified")
    source_contract = schedule.get("source_exact_reduction_contract")
    if not isinstance(source_contract, dict):
        raise ValueError("missing superseded source contract")

    terms = scope.get("layer_cycle_terms")
    if not isinstance(terms, dict):
        raise ValueError("missing layer cycle terms")
    old_tile_cycles = int(terms["tile_service_cycles"])
    tile_waves = int(terms["tile_waves"])
    if old_tile_cycles != int(source_contract["replica_recost_tile_service_cycles"]):
        raise ValueError("frontier and cadence reports do not share the superseded reference")
    old_attention_cycles = old_tile_cycles * tile_waves
    recorded_layer_cycles = int(scope["recorded_layer_cycles"])
    layers = int(scope["layers"])
    recorded_total_cycles = int(scope["recorded_total_cycles"])
    if recorded_total_cycles != recorded_layer_cycles * layers:
        raise ValueError("recorded cycle accounting is inconsistent")
    recorded_latency_us = float(baseline["latency_us"])
    clock_period_ns = recorded_latency_us * 1000.0 / recorded_total_cycles

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
    norm_deltas_us = [float(row["composed_latency_us"]) - recorded_latency_us for row in serialized]
    competitor_latency_us = float(competitor["latency_us"])
    single = schedule["single_clock_full_layer_bound"]
    dual = schedule["dual_clock_component_rate_bound"]
    single_low = float(single["conditional_overlap_latency_lower_bound_us"])
    single_high = float(single["strict_no_overlap_latency_upper_bound_us"])
    dual_low = float(dual["conditional_overlap_latency_lower_bound_us"])
    dual_high = float(dual["strict_no_overlap_latency_upper_bound_us"])
    ppa = cadence["routed_component_ppa"]
    local_area_low = float(ppa["synthesis_area_lower_bound_scaled_16_clusters"]["total_hierarchy_area_mm2"])
    local_area_high = float(ppa["macro_only_sum_scaled_16_clusters"]["die_area_mm2"])
    score32_area = float(score32["compute_area_mm2"])
    competitor_area = float(competitor["compute_area_mm2"])

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
        "measured_local_reducer_recost": {
            "clock_period_ns_reconstructed": clock_period_ns,
            "single_clock_latency_interval_us": [single_low, single_high],
            "single_clock_serialized_rmsnorm_interval_us": [single_low + min(norm_deltas_us), single_high + max(norm_deltas_us)],
            "single_clock_latency_lead_preserved": single_high < competitor_latency_us,
            "dual_clock_latency_interval_us": [dual_low, dual_high],
            "dual_clock_serialized_rmsnorm_interval_us": [dual_low + min(norm_deltas_us), dual_high + max(norm_deltas_us)],
            "dual_clock_latency_lead_preserved_across_serialized_rmsnorm_envelope": dual_high + max(norm_deltas_us) < competitor_latency_us,
            "dual_clock_requires_unmeasured_cdc_scheduler": bool(dual["cdc_handshake_required"]),
            "nearest_credible_competitor_id": str(competitor["candidate_id"]),
            "nearest_credible_competitor_latency_us": competitor_latency_us,
            "local_reducer_area_interval_mm2": [local_area_low, local_area_high],
            "score32_component_plus_local_reducer_area_interval_mm2": [score32_area + local_area_low, score32_area + local_area_high],
            "remaining_area_headroom_to_fp16_interval_mm2": [competitor_area - score32_area - local_area_high, competitor_area - score32_area - local_area_low],
            "claim_scope": "measured reducer service and component-area bounds; no routed composed top, CDC closure, or activity-backed energy",
        },
        "pareto_status": {
            "recorded_two_point_set_physically_credible": False,
            "score32_membership": "unproven_pending_cadence_integrated_energy_area_recost",
            "exact_fp16_membership": "retained_as_current_measured_reference",
        },
        "blockers": [
            "the integrated frontier still consumes the superseded 986-cycle tile-service term",
            "the routed 53/54-way composed top is absent despite functional reducer and routed submacro evidence",
            "the latency-leading dual-clock interval requires unmeasured CDC and scheduler composition",
            "score32 energy has not been recomputed for the measured reducer schedule or closed with activity",
        ],
    }


def render_markdown(report: JsonDict) -> str:
    old = report["superseded_contract"]
    new = report["measured_local_reducer_recost"]
    lines = [
        "# Llama7B Score32 Cadence/Frontier Consistency Audit",
        "",
        f"- decision: `{report['decision']}`",
        f"- recorded two-point Pareto set physically credible: `{report['pareto_status']['recorded_two_point_set_physically_credible']}`",
        f"- superseded Score32 latency: `{old['recorded_latency_us']:.3f} us`",
        f"- single-clock interval before RMSNorm: `{new['single_clock_latency_interval_us'][0]:.3f}--{new['single_clock_latency_interval_us'][1]:.3f} us`",
        f"- dual-clock interval before RMSNorm: `{new['dual_clock_latency_interval_us'][0]:.3f}--{new['dual_clock_latency_interval_us'][1]:.3f} us`",
        f"- dual-clock interval with serialized RMSNorm: `{new['dual_clock_serialized_rmsnorm_interval_us'][0]:.3f}--{new['dual_clock_serialized_rmsnorm_interval_us'][1]:.3f} us`",
        f"- nearest measured reference latency: `{new['nearest_credible_competitor_latency_us']:.3f} us`",
        f"- dual-clock latency lead preserved: `{new['dual_clock_latency_lead_preserved_across_serialized_rmsnorm_envelope']}`",
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
