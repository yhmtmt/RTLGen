#!/usr/bin/env python3
"""Extract the physically credible Pareto set without promoting incomplete energy evidence."""

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
OBJECTIVES = ("latency_us", "energy_mj_per_token", "component_area_mm2")


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


def _dominates(left: JsonDict, right: JsonDict) -> bool:
    left_values = tuple(float(left[key]) for key in OBJECTIVES)
    right_values = tuple(float(right[key]) for key in OBJECTIVES)
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )


def build_report(
    frontier: JsonDict,
    *,
    frontier_path: Path,
    norm: JsonDict,
    norm_path: Path,
) -> JsonDict:
    if frontier.get("model") != "llm_decoder_attention_score32_integrated_frontier_ranking_v1":
        raise ValueError("unexpected integrated-frontier model")
    rows = frontier.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("integrated frontier has no rows")

    eligible: list[JsonDict] = []
    excluded: list[JsonDict] = []
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("frontier row must be an object")
        candidate_id = str(raw.get("candidate_id") or "")
        metrics = {
            "latency_us": float(raw.get("latency_us") or 0.0),
            "energy_mj_per_token": float(raw.get("energy_mj_per_token") or 0.0),
            "component_area_mm2": float(raw.get("compute_area_mm2") or 0.0),
        }
        if not candidate_id or metrics["latency_us"] <= 0.0 or metrics["energy_mj_per_token"] <= 0.0:
            raise ValueError(f"candidate has missing/non-positive latency or energy: {candidate_id}")
        record = {
            "candidate_id": candidate_id,
            **metrics,
            "die_area_envelope_mm2": float(raw.get("die_area_mm2") or 0.0),
            "token_throughput_per_s": float(raw.get("token_throughput_per_s") or 0.0),
            "family": raw.get("family"),
            "precision_status": raw.get("precision_status"),
            "abstraction_status": raw.get("abstraction_status"),
            "remaining_abstractions": list(raw.get("remaining_abstractions") or []),
        }
        if bool(raw.get("promotable")) and bool(raw.get("quality_backed")):
            if metrics["component_area_mm2"] <= 0.0:
                raise ValueError(f"eligible candidate has missing/non-positive component area: {candidate_id}")
            eligible.append(record)
        else:
            reasons = []
            if not bool(raw.get("promotable")):
                reasons.append("not_promotable")
            if not bool(raw.get("quality_backed")):
                reasons.append("not_quality_backed")
            excluded.append({**record, "exclusion_reasons": reasons})

    if not eligible:
        raise ValueError("no quality-backed promotable candidates")
    pareto = [row for row in eligible if not any(_dominates(other, row) for other in eligible if other is not row)]
    dominated = [row for row in eligible if row not in pareto]

    if norm.get("model") != "llama7b_rmsnorm_macro_banked_latency_composition_v2":
        raise ValueError("unexpected RMSNorm composition model")
    scope = norm.get("attention_scope_proof")
    if not isinstance(scope, dict) or scope.get("status") != "verified_attention_only_excludes_transformer_rmsnorm":
        raise ValueError("RMSNorm scope exclusion is not proven")
    norm_candidates = norm.get("rmsnorm_candidates")
    if not isinstance(norm_candidates, list) or not norm_candidates:
        raise ValueError("RMSNorm composition has no candidates")
    norm_baseline = norm.get("baseline")
    if not isinstance(norm_baseline, dict):
        raise ValueError("RMSNorm composition has no baseline")
    norm_baseline_id = str(norm_baseline.get("candidate_id") or "")
    score32_point = next((row for row in pareto if row["candidate_id"] == norm_baseline_id), None)
    if score32_point is None:
        raise ValueError("RMSNorm baseline is not a credible Pareto point")
    if float(norm_baseline.get("latency_us") or 0.0) != score32_point["latency_us"]:
        raise ValueError("RMSNorm and Pareto baseline latencies differ")
    norm_rows = norm.get("rows")
    if not isinstance(norm_rows, list):
        raise ValueError("RMSNorm composition rows are missing")
    serialized_rows = [row for row in norm_rows if float(row.get("hidden_fraction", -1.0)) == 0.0]
    expected_serialized_rows = len(norm_candidates) * 3
    if len(serialized_rows) != expected_serialized_rows:
        raise ValueError(
            f"expected {expected_serialized_rows} serialized RMSNorm sensitivity rows, "
            f"got {len(serialized_rows)}"
        )
    serialized_envelope = sorted(
        (
            {
                "rmsnorm_candidate_id": str(row["rmsnorm_candidate_id"]),
                "clock_period_ns": float(row["clock_period_ns"]),
                "composed_latency_us": float(row["composed_latency_us"]),
                "composed_token_throughput_per_s": float(row["composed_token_throughput_per_s"]),
            }
            for row in serialized_rows
        ),
        key=lambda row: row["composed_latency_us"],
    )
    competing_latencies = [
        row["latency_us"] for row in pareto if row["candidate_id"] != score32_point["candidate_id"]
    ]
    latency_anchor_robust = bool(competing_latencies) and serialized_envelope[-1][
        "composed_latency_us"
    ] < min(competing_latencies)
    energy_reference = min(
        (row for row in pareto if row["candidate_id"] != score32_point["candidate_id"]),
        key=lambda row: row["energy_mj_per_token"],
        default=None,
    )
    if energy_reference is None:
        raise ValueError("credible Pareto set has no energy-reference competitor")
    recorded_energy_ratio = score32_point["energy_mj_per_token"] / energy_reference[
        "energy_mj_per_token"
    ]
    score32_multiplier_to_tie = 1.0 / recorded_energy_ratio

    area_reference = min(
        (row for row in pareto if row["candidate_id"] != score32_point["candidate_id"]),
        key=lambda row: row["component_area_mm2"],
        default=None,
    )
    if area_reference is None:
        raise ValueError("credible Pareto set has no area-reference competitor")
    score32_missing_area_budget_to_tie_mm2 = (
        area_reference["component_area_mm2"] - score32_point["component_area_mm2"]
    )
    if score32_missing_area_budget_to_tie_mm2 <= 0.0:
        raise ValueError("score32 point is not the current component-area anchor")
    reference_latency_reduction_to_tie_recorded_pct = 100.0 * (
        1.0 - score32_point["latency_us"] / area_reference["latency_us"]
    )
    reference_latency_reduction_to_tie_worst_serialized_norm_pct = 100.0 * (
        1.0 - serialized_envelope[-1]["composed_latency_us"] / area_reference["latency_us"]
    )
    reference_area_reduction_to_tie_recorded_pct = 100.0 * (
        1.0 - score32_point["component_area_mm2"] / area_reference["component_area_mm2"]
    )
    if min(
        reference_latency_reduction_to_tie_recorded_pct,
        reference_latency_reduction_to_tie_worst_serialized_norm_pct,
        reference_area_reduction_to_tie_recorded_pct,
    ) <= 0.0:
        raise ValueError("reference does not trail score32 on the recorded latency/area axes")

    score32_activity_input = (frontier.get("inputs") or {}).get("score32_activity_power_json")
    activity_backed = bool(score32_activity_input)
    return {
        "version": 1,
        "model": "llama7b_physically_credible_pareto_audit_v1",
        "decision": "two_provisional_quality_backed_component_composed_pareto_points",
        "source": {
            "frontier_path": _portable(frontier_path),
            "frontier_sha256": _sha256(frontier_path),
            "norm_path": _portable(norm_path),
            "norm_sha256": _sha256(norm_path),
        },
        "objective_definition": {
            "minimize": list(OBJECTIVES),
            "eligibility": ["promotable", "quality_backed", "all objectives finite and positive"],
            "dominance_pool": "eligible candidates only",
        },
        "pareto_points": pareto,
        "eligible_dominated": dominated,
        "excluded_points": excluded,
        "objective_evidence": {
            "latency": "component-composed attention-centered estimate",
            "area": (
                "component-composed compute/controller area is the dominance objective; die area is retained only "
                "as a capacity envelope, and RMSNorm area is not yet included"
            ),
            "energy": (
                "activity-backed score32 input"
                if activity_backed
                else "not activity-backed in this frontier; schedule-wrapper activity input is absent"
            ),
        },
        "scope_guard": {
            "status": "attention_centered_not_full_model",
            "excluded_from_frontier_latency": list(scope["excluded_terms"]),
            "rmsnorm_rows_per_token": int(norm["rmsnorm_scope"]["rows_per_token"]),
            "rmsnorm_candidate_cycles": {
                str(row["candidate_id"]): int(row["row_cycles"]) for row in norm_candidates
            },
            "norm_promotion_gate_pass": bool(norm.get("promotion_gate_pass")),
        },
        "rmsnorm_serialized_latency_robustness": {
            "candidate_id": score32_point["candidate_id"],
            "baseline_excludes_rmsnorm": True,
            "sensitivity_rows": serialized_envelope,
            "best_case": serialized_envelope[0],
            "worst_case": serialized_envelope[-1],
            "nearest_other_pareto_latency_us": min(competing_latencies)
            if competing_latencies
            else None,
            "latency_anchor_robust_across_envelope": latency_anchor_robust,
            "claim_scope": "serialized latency only; no norm area or energy promotion",
        },
        "area_axis_uncertainty": {
            "status": "rmsnorm_area_unmeasured_break_even_only",
            "score32_candidate_id": score32_point["candidate_id"],
            "area_reference_candidate_id": area_reference["candidate_id"],
            "score32_recorded_component_area_mm2": score32_point["component_area_mm2"],
            "area_reference_recorded_component_area_mm2": area_reference["component_area_mm2"],
            "score32_aggregate_missing_area_budget_to_tie_mm2": round(
                score32_missing_area_budget_to_tie_mm2, 9
            ),
            "score32_aggregate_missing_area_budget_to_tie_pct_of_recorded_area": round(
                100.0
                * score32_missing_area_budget_to_tie_mm2
                / score32_point["component_area_mm2"],
                9,
            ),
            "strict_area_lead_condition": (
                "aggregate score32-only area absent from the current objective is less than the tie budget, "
                "with the reference area unchanged"
            ),
            "rmsnorm_area_closed": False,
            "reason": (
                "The routed RMSNorm area and its architecture-level replication are not measured. The budget is "
                "an aggregate break-even sensitivity, not an estimated RMSNorm area or a physical closure claim."
            ),
        },
        "pairwise_dominance_sensitivity": {
            "status": "conditional_break_even_not_physical_closure",
            "score32_candidate_id": score32_point["candidate_id"],
            "reference_candidate_id": area_reference["candidate_id"],
            "score32_dominates_reference_if": {
                "latency_condition": (
                    "already strict across the complete exact serialized RMSNorm envelope"
                ),
                "energy_mj_per_token_at_most": energy_reference["energy_mj_per_token"],
                "aggregate_missing_area_mm2_at_most": round(
                    score32_missing_area_budget_to_tie_mm2, 9
                ),
                "assumptions": [
                    "reference objectives remain unchanged",
                    "score32 activity-backed energy includes the same system boundary as the reference",
                    "all score32-only area absent from the current objective is counted in aggregate",
                ],
            },
            "reference_dominates_score32_recorded_axes_only_if": {
                "latency_reduction_to_tie_recorded_score32_pct": round(
                    reference_latency_reduction_to_tie_recorded_pct, 9
                ),
                "latency_reduction_to_tie_worst_serialized_norm_score32_pct": round(
                    reference_latency_reduction_to_tie_worst_serialized_norm_pct, 9
                ),
                "component_area_reduction_to_tie_recorded_score32_pct": round(
                    reference_area_reduction_to_tie_recorded_pct, 9
                ),
                "requirements_are_simultaneous": True,
                "energy_condition": "already strict on the recorded, non-activity-closed energy axis",
                "assumptions": [
                    "score32 recorded component area is used before adding unmeasured area",
                    "each comparison holds the opposing candidate objective fixed",
                ],
            },
            "reason": (
                "These thresholds identify which missing measurements can change pairwise dominance. They do not "
                "predict achievable improvements or replace matched physical and activity measurements."
            ),
        },
        "energy_axis_uncertainty": {
            "status": "recorded_energy_tradeoff_not_activity_closed",
            "score32_candidate_id": score32_point["candidate_id"],
            "energy_reference_candidate_id": energy_reference["candidate_id"],
            "score32_recorded_energy_mj_per_token": score32_point["energy_mj_per_token"],
            "energy_reference_recorded_mj_per_token": energy_reference["energy_mj_per_token"],
            "score32_to_reference_recorded_ratio": round(recorded_energy_ratio, 9),
            "score32_energy_multiplier_to_tie_if_reference_unchanged": round(
                score32_multiplier_to_tie, 9
            ),
            "score32_energy_reduction_to_tie_pct_if_reference_unchanged": round(
                100.0 * (1.0 - score32_multiplier_to_tie), 9
            ),
            "activity_closed_pareto_status": "unproven",
            "reason": (
                "The selected frontier has no score32_activity_power_json input. Its recorded energy ratio is a "
                "break-even sensitivity, not an activity-backed dominance claim."
            ),
        },
        "promotion_gate_pass": False,
        "blockers": [
            "the frontier energy objective does not consume schedule-wrapper post-route activity power",
            "transformer RMSNorm latency is excluded and its routed area/activity/overlap are open",
            "NoC and selected SRAM hierarchy lack matched workload-backed routed activity power",
            "the architecture is component-composed rather than a full-chip routed implementation",
        ],
        "interpretation": (
            "Among quality-backed promotable rows, score32 is the latency/area point and measured exact FP16 is "
            "the energy point; neither dominates the other. These are provisional component-composed Pareto "
            "anchors, not final full-model PPA points. Non-promotable abstract or quality-invalid rows are never "
            "allowed to dominate the credible set."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    lines = [
        "# Llama7B Physically Credible Pareto Audit",
        "",
        f"- decision: `{report['decision']}`",
        f"- scope: `{report['scope_guard']['status']}`",
        f"- promotion gate: `{report['promotion_gate_pass']}`",
        "",
        "| credible Pareto point | family | latency us | token/s | energy mJ/token | component area mm2 | die envelope mm2 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["pareto_points"]:
        lines.append(
            "| `{candidate_id}` | `{family}` | {latency_us:.3f} | {token_throughput_per_s:.3f} | "
            "{energy_mj_per_token:.3f} | {component_area_mm2:.3f} | "
            "{die_area_envelope_mm2:.3f} |".format(**row)
        )
    robustness = report["rmsnorm_serialized_latency_robustness"]
    lines.extend(
        [
            "",
            "## RMSNorm Serialized-Latency Robustness",
            "",
            f"- score32 remains latency anchor across envelope: "
            f"`{robustness['latency_anchor_robust_across_envelope']}`",
            f"- best adjusted latency: `{robustness['best_case']['composed_latency_us']:.3f} us`",
            f"- worst adjusted latency: `{robustness['worst_case']['composed_latency_us']:.3f} us`",
            f"- nearest other Pareto latency: `{robustness['nearest_other_pareto_latency_us']:.3f} us`",
            f"- claim scope: {robustness['claim_scope']}",
        ]
    )
    area = report["area_axis_uncertainty"]
    lines.extend(
        [
            "",
            "## Area-Axis Uncertainty",
            "",
            f"- status: `{area['status']}`",
            f"- score32 aggregate missing-area budget to tie reference: "
            f"`{area['score32_aggregate_missing_area_budget_to_tie_mm2']:.3f} mm2`",
            f"- budget relative to recorded score32 component area: "
            f"`{area['score32_aggregate_missing_area_budget_to_tie_pct_of_recorded_area']:.3f}%`",
            f"- strict area-lead condition: {area['strict_area_lead_condition']}",
            f"- reason: {area['reason']}",
        ]
    )
    pairwise = report["pairwise_dominance_sensitivity"]
    score32_condition = pairwise["score32_dominates_reference_if"]
    reference_condition = pairwise["reference_dominates_score32_recorded_axes_only_if"]
    lines.extend(
        [
            "",
            "## Pairwise Dominance Sensitivity",
            "",
            f"- status: `{pairwise['status']}`",
            f"- score32 dominance boundary: energy at most "
            f"`{score32_condition['energy_mj_per_token_at_most']:.3f} mJ/token` and aggregate "
            f"missing area at most `{score32_condition['aggregate_missing_area_mm2_at_most']:.3f} mm2`; "
            f"latency is {score32_condition['latency_condition']}",
            f"- reference latency reduction to tie recorded score32: "
            f"`{reference_condition['latency_reduction_to_tie_recorded_score32_pct']:.3f}%`",
            f"- reference latency reduction to tie worst serialized-norm score32: "
            f"`{reference_condition['latency_reduction_to_tie_worst_serialized_norm_score32_pct']:.3f}%`",
            f"- reference component-area reduction to tie recorded score32: "
            f"`{reference_condition['component_area_reduction_to_tie_recorded_score32_pct']:.3f}%`",
            f"- reference latency and area requirements are simultaneous: "
            f"`{reference_condition['requirements_are_simultaneous']}`",
            f"- reason: {pairwise['reason']}",
        ]
    )
    energy = report["energy_axis_uncertainty"]
    lines.extend(
        [
            "",
            "## Energy-Axis Uncertainty",
            "",
            f"- status: `{energy['status']}`",
            f"- recorded score32/reference ratio: `{energy['score32_to_reference_recorded_ratio']:.3f}x`",
            f"- score32 reduction required to tie if reference is unchanged: "
            f"`{energy['score32_energy_reduction_to_tie_pct_if_reference_unchanged']:.3f}%`",
            f"- activity-closed Pareto status: `{energy['activity_closed_pareto_status']}`",
            f"- reason: {energy['reason']}",
        ]
    )
    lines.extend(["", "## Excluded Points", "", "| candidate | reasons |", "| --- | --- |"])
    for row in report["excluded_points"]:
        lines.append(f"| `{row['candidate_id']}` | {', '.join(row['exclusion_reasons'])} |")
    lines.extend(["", "## Evidence Limits", ""])
    lines.extend(f"- {key}: {value}" for key, value in report["objective_evidence"].items())
    lines.extend(["", "## Promotion Blockers", ""])
    lines.extend(f"- {item}" for item in report["blockers"])
    lines.extend(["", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier", type=Path, default=DEFAULT_FRONTIER)
    parser.add_argument("--norm", type=Path, default=DEFAULT_NORM)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    report = build_report(
        _load(args.frontier),
        frontier_path=args.frontier,
        norm=_load(args.norm),
        norm_path=args.norm,
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
