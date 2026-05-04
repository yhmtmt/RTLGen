#!/usr/bin/env python3
"""Estimate whether bf16/PWL score-tie recovery is hardware-plausible."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

DEFAULT_BF16_RECIP_PPA = Path("control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json")
DEFAULT_BF16_TIE_RANK_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json"
)
DEFAULT_RECOVERY = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
)
METRIC_KEYS = ("critical_path_ns", "die_area", "total_power_mw")

COST_MODEL = {
    "name": "decoder_bf16_pwl_score_tie_rank_frontier_v1",
    "unit": "nangate45_row8_component_metrics",
    "source": "merged_rtlgen_openroad_bf16_reciprocal_and_score_tie_rank_datapath_metrics",
    "component_model": "conservative_additive_datapath_components",
    "ppa_balance": (
        "The recovered bf16/PWL row is priced as the measured row-8 bf16 reciprocal-normalization "
        "datapath plus the measured row-8 score/logit tie-rank datapath. The rank key is critical "
        "path, then area, then power. This is comparable only within the current Nangate45 row-8 "
        "datapath framing; it is not a full-array routed macro or application-level throughput model."
    ),
}


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _best_ppa_row(path: Path) -> JsonDict:
    payload = _load_json(path)
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        raise SystemExit(f"PPA artifact must contain a proposals list: {path}")
    rows: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metrics_ref = proposal.get("metrics_ref")
        metric_summary = proposal.get("metric_summary")
        if not isinstance(metrics_ref, dict) or not isinstance(metric_summary, dict):
            continue
        if str(metrics_ref.get("status") or "") != "ok":
            continue
        metrics = {key: _as_float(metric_summary.get(key), default=None) for key in METRIC_KEYS}
        if any(metrics[key] is None for key in METRIC_KEYS):
            continue
        rows.append(
            {
                "metrics": metrics,
                "metrics_ref": metrics_ref,
                "selection_reason": proposal.get("selection_reason", ""),
            }
        )
    if not rows:
        raise SystemExit(f"no accepted physical metrics in PPA artifact: {path}")
    rows.sort(key=lambda row: tuple(_as_float(row["metrics"][key]) for key in METRIC_KEYS))
    return rows[0]


def _combine_metrics(*components: JsonDict) -> JsonDict:
    return {key: round(sum(_as_float(component.get(key)) for component in components), 6) for key in METRIC_KEYS}


def _quality(row: JsonDict) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_matches = _as_int(row.get("next_token_matches"))
    topk_matches = _as_int(row.get("topk_matches"))
    return {
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_match_rate": next_matches / sample_count if sample_count else 0.0,
        "topk_match_rate": topk_matches / sample_count if sample_count else 0.0,
        "next_token_mismatch_sample_ids": row.get("next_token_mismatch_sample_ids") or [],
        "topk_miss_sample_ids": row.get("topk_miss_sample_ids") or [],
        "exact_safe": sample_count > 0 and next_matches == sample_count and topk_matches == sample_count,
    }


def _ratio_delta(*, numerator: float, denominator: float) -> JsonDict:
    delta = numerator - denominator
    return {
        "absolute": round(delta, 6),
        "relative": round(delta / denominator, 6) if denominator else None,
        "relative_percent": round(100.0 * delta / denominator, 3) if denominator else None,
    }


def build_report(*, recovery_path: Path, bf16_recip_ppa_path: Path, bf16_tie_rank_ppa_path: Path) -> JsonDict:
    recovery_payload = _load_json(recovery_path)
    baseline = recovery_payload.get("baseline")
    recovery = recovery_payload.get("recovery")
    diagnosis = recovery_payload.get("diagnosis")
    if not isinstance(baseline, dict) or not isinstance(recovery, dict):
        raise SystemExit(f"recovery summary must contain baseline and recovery objects: {recovery_path}")
    if not isinstance(diagnosis, dict):
        diagnosis = {}

    recip_ppa = _best_ppa_row(bf16_recip_ppa_path)
    tie_rank_ppa = _best_ppa_row(bf16_tie_rank_ppa_path)
    baseline_metrics = recip_ppa["metrics"]
    recovered_metrics = _combine_metrics(recip_ppa["metrics"], tie_rank_ppa["metrics"])
    baseline_quality = _quality(baseline)
    recovery_quality = _quality(recovery)
    regressions = recovery_payload.get("regression_sample_ids") or []
    recovered_samples = recovery_payload.get("recovered_sample_ids") or []

    exact_after_recovery = bool(diagnosis.get("exact_safe_after_recovery")) and recovery_quality["exact_safe"]
    no_regressions = len(regressions) == 0
    ppa_available = bool(recip_ppa and tie_rank_ppa)
    if exact_after_recovery and no_regressions and ppa_available:
        decision = "hardware_recovery_plausible"
        reason = (
            "The GPT-2 prompt-stress misses are recovered by logit tie-rank, no regressions are present, "
            "and both bf16 reciprocal normalization and score tie-rank have merged Nangate45 physical metrics."
        )
    elif not recovery_quality["exact_safe"]:
        decision = "blocked_quality"
        reason = "The recovered row is not exact-safe on the source recovery summary."
    elif not no_regressions:
        decision = "blocked_regression"
        reason = "The recovered row introduces regression samples."
    else:
        decision = "blocked_ppa"
        reason = "The required measured component PPA artifacts are not available."

    return {
        "version": 0.1,
        "source_recovery": str(recovery_path),
        "source_sweep": recovery_payload.get("source_sweep", ""),
        "source_artifacts": {
            "bf16_reciprocal_datapath_ppa": str(bf16_recip_ppa_path),
            "bf16_score_tie_rank_datapath_ppa": str(bf16_tie_rank_ppa_path),
        },
        "cost_model": COST_MODEL,
        "quality": {
            "baseline": baseline_quality,
            "recovery": recovery_quality,
            "recovered_sample_ids": recovered_samples,
            "regression_sample_ids": regressions,
        },
        "components": {
            "bf16_reciprocal": recip_ppa,
            "score_tie_rank": tie_rank_ppa,
            "recovered_path": {
                "metrics": recovered_metrics,
                "component_model": COST_MODEL["component_model"],
                "rank_key": [recovered_metrics[key] for key in METRIC_KEYS],
                "incremental_vs_bf16_reciprocal": {
                    key: _ratio_delta(
                        numerator=_as_float(recovered_metrics[key]),
                        denominator=_as_float(baseline_metrics[key]),
                    )
                    for key in METRIC_KEYS
                },
            },
        },
        "decision": {
            "decision": decision,
            "reason": reason,
            "selected_candidate": recovery.get("template", ""),
            "baseline_candidate": baseline.get("template", ""),
            "exact_safe_after_recovery": exact_after_recovery,
            "no_regressions": no_regressions,
        },
        "next_step": [
            "Use this as a hardware-plausibility gate for bf16/PWL score-tie recovery, not as full-array proof.",
            "If larger-model or larger-array prompt stress breaks this gate, move to QAT or richer calibration.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    decision = payload["decision"]
    quality = payload["quality"]
    recovered_metrics = payload["components"]["recovered_path"]["metrics"]
    inc = payload["components"]["recovered_path"]["incremental_vs_bf16_reciprocal"]
    lines = [
        "# Decoder bf16/PWL Tie-Rank Frontier",
        "",
        f"- source_recovery: `{payload['source_recovery']}`",
        f"- decision: `{decision['decision']}`",
        f"- selected_candidate: `{decision['selected_candidate']}`",
        f"- reason: {decision['reason']}",
        "",
        "## Quality Gate",
        "",
        (
            f"- baseline: {quality['baseline']['next_token_matches']}/{quality['baseline']['sample_count']} "
            f"next-token, {quality['baseline']['topk_matches']}/{quality['baseline']['sample_count']} top-k"
        ),
        (
            f"- recovery: {quality['recovery']['next_token_matches']}/{quality['recovery']['sample_count']} "
            f"next-token, {quality['recovery']['topk_matches']}/{quality['recovery']['sample_count']} top-k"
        ),
        f"- recovered_sample_ids: `{', '.join(quality['recovered_sample_ids']) or 'none'}`",
        f"- regression_sample_ids: `{', '.join(quality['regression_sample_ids']) or 'none'}`",
        "",
        "## Component PPA",
        "",
        "| path | critical_path_ns | die_area | total_power_mw |",
        "|---|---:|---:|---:|",
        (
            f"| recovered bf16 reciprocal + score tie-rank | {recovered_metrics['critical_path_ns']} | "
            f"{recovered_metrics['die_area']} | {recovered_metrics['total_power_mw']} |"
        ),
        "",
        "## Incremental Cost Versus bf16 Reciprocal",
        "",
        "| metric | absolute | relative % |",
        "|---|---:|---:|",
    ]
    for key in METRIC_KEYS:
        lines.append(f"| {key} | {inc[key]['absolute']} | {inc[key]['relative_percent']} |")
    lines.extend(["", "## Next Step", ""])
    for item in payload["next_step"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Estimate bf16/PWL score-tie recovery quality/PPA frontier")
    ap.add_argument("--recovery", default=str(DEFAULT_RECOVERY), help="bf16/PWL recovery summary JSON")
    ap.add_argument("--bf16-recip-ppa", default=str(DEFAULT_BF16_RECIP_PPA), help="merged bf16 reciprocal PPA JSON")
    ap.add_argument("--bf16-tie-rank-ppa", default=str(DEFAULT_BF16_TIE_RANK_PPA), help="merged score tie-rank PPA JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown path")
    args = ap.parse_args()
    report = build_report(
        recovery_path=Path(args.recovery),
        bf16_recip_ppa_path=Path(args.bf16_recip_ppa),
        bf16_tie_rank_ppa_path=Path(args.bf16_tie_rank_ppa),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
