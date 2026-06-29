#!/usr/bin/env python3
"""Audit quality-backed mixed-int8 energy frontier options."""

from __future__ import annotations

import argparse
import csv
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


def _read_first_ok_metrics(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise RuntimeError(f"metrics CSV has no rows: {path}")
    ok_rows = [row for row in rows if str(row.get("status", "")).lower() == "ok"]
    row = ok_rows[0] if ok_rows else rows[0]
    return {
        "path": str(path),
        "design": row.get("design"),
        "status": row.get("status"),
        "critical_path_ns": _as_float(row.get("critical_path_ns")),
        "die_area_um2": _as_float(row.get("die_area")),
        "total_power_mw": _as_float(row.get("total_power_mw")),
        "instance_area_um2": _as_float(row.get("instance_area_um2")),
        "stdcell_area_um2": _as_float(row.get("stdcell_area_um2")),
        "stdcell_count": _as_float(row.get("stdcell_count")),
    }


def _candidate_summaries(payload: JsonDict) -> list[JsonDict]:
    rows = payload.get("candidate_summaries")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _is_pass(row: JsonDict) -> bool:
    status = str(row.get("decision_status") or (row.get("decision") or {}).get("status") or "")
    return status.endswith("_pass")


def _quality_candidate(row: JsonDict | None) -> JsonDict | None:
    if row is None:
        return None
    return {
        "candidate_id": row.get("candidate_id"),
        "decision_status": row.get("decision_status") or (row.get("decision") or {}).get("status"),
        "q_bits": row.get("q_bits"),
        "k_bits": row.get("k_bits"),
        "v_bits": row.get("v_bits"),
        "score_bits": row.get("score_bits"),
        "weight_bits": row.get("weight_bits"),
        "softmax_mode": row.get("softmax_mode"),
        "comparison_count": row.get("comparison_count"),
        "top1_match_rate": row.get("top1_match_rate"),
        "topk_contains_rate": row.get("topk_contains_rate"),
        "mean_logit_cosine": row.get("mean_logit_cosine"),
        "mean_probability_kl": row.get("mean_probability_kl"),
        "max_abs_logit_delta_max": row.get("max_abs_logit_delta_max"),
    }


def _recovery_candidate(payload: JsonDict, candidate_id: str) -> JsonDict | None:
    for row in _candidate_summaries(payload):
        if str(row.get("candidate_id")) == candidate_id:
            return _quality_candidate(row)
    return None


def _recost_summary(payload: JsonDict, *, label: str) -> JsonDict:
    diagnosis = dict(payload.get("diagnosis") or {})
    best = dict(payload.get("best_feasible") or payload.get("best_requested") or {})
    return {
        "label": label,
        "decision": diagnosis.get("decision") or payload.get("decision"),
        "precision_profile": best.get("precision_profile") or diagnosis.get("precision_profile"),
        "best_feasible_latency_us": diagnosis.get("best_feasible_latency_us"),
        "replica_recost_latency_us": best.get("replica_recost_latency_us"),
        "replica_recost_area_fit_replica_count": best.get("replica_recost_area_fit_replica_count"),
        "replica_recost_macs_per_cycle": best.get("replica_recost_macs_per_cycle"),
        "replica_recost_compute_area_um2": best.get("replica_recost_compute_area_um2"),
        "replica_recost_compute_power_mw": best.get("replica_recost_compute_power_mw"),
        "substituted_compute_arch": (
            best.get("substituted_compute_arch")
            or best.get("compute_arch_name")
            or diagnosis.get("best_requested_substituted_compute_arch")
        ),
        "quality_backed": False,
        "quality_blocker": "score32 fixed-point/PWL candidates did not pass broad native attention-shadow gate",
    }


def build_payload(args: argparse.Namespace) -> JsonDict:
    quality_frontier = _load_json(args.quality_backed_frontier_json)
    score_recovery = _load_json(args.score_precision_recovery_json)
    exact_div = _load_json(args.exact_div_recost_json)
    exact_div_split2 = _load_json(args.exact_div_split2_recost_json)
    fp16_nm1 = _read_first_ok_metrics(args.fp16_softmax_nm1_metrics)
    fp16_nm2 = _read_first_ok_metrics(args.fp16_softmax_nm2_metrics)

    qbf_diag = dict(quality_frontier.get("diagnosis") or {})
    qkv8_quality_pass = "qkv8_float_exact" in {
        str(item) for item in qbf_diag.get("quality_passing_candidate_ids", [])
    }
    qkv8_quality = {
        "candidate_id": qbf_diag.get("quality_best_candidate_id"),
        "top1_match_rate": qbf_diag.get("quality_best_top1_match_rate"),
        "mean_probability_kl": qbf_diag.get("quality_best_mean_probability_kl"),
        "quality_backed": qkv8_quality_pass,
    }

    score32 = _recovery_candidate(score_recovery, "score32_float")
    q24_pwl = _recovery_candidate(score_recovery, "qkv8_q24_pwl_recip_q24_bucket8")
    measured_non_quality_backed = [
        _recost_summary(exact_div, label="score32_w16_exact_div"),
        _recost_summary(exact_div_split2, label="score32_w16_exact_div_split2"),
    ]

    fp16_proxy_candidates = [
        {
            "candidate_id": "qkv8_float_exact_fp16_softmax_nm1_proxy",
            "quality_source": "qkv8_float_exact",
            "softmax_metrics": fp16_nm1,
            "quality_backed": qkv8_quality_pass,
            "composition_status": "measured_softmax_only_not_composed_attention_wrapper",
        },
        {
            "candidate_id": "qkv8_float_exact_fp16_softmax_nm2_proxy",
            "quality_source": "qkv8_float_exact",
            "softmax_metrics": fp16_nm2,
            "quality_backed": qkv8_quality_pass,
            "composition_status": "measured_softmax_only_not_composed_attention_wrapper",
        },
    ]

    best_proxy = min(
        fp16_proxy_candidates,
        key=lambda row: (
            _as_float(row["softmax_metrics"].get("critical_path_ns"), 1e9),
            _as_float(row["softmax_metrics"].get("die_area_um2"), 1e18),
        ),
    )

    decision = "mixed_int8_quality_energy_frontier_composed_measurement_required"
    recommended_next_step = (
        "Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics "
        "and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL "
        "rows as quality-backed frontier points."
    )

    payload: JsonDict = {
        "version": 1,
        "model": "llm_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1",
        "decision": decision,
        "quality_gate": {
            "qkv8_float_exact": qkv8_quality,
            "score32_float": score32,
            "qkv8_q24_pwl_recip_q24_bucket8": q24_pwl,
        },
        "fp16_softmax_proxy_candidates": fp16_proxy_candidates,
        "best_fp16_softmax_proxy_candidate": best_proxy,
        "measured_non_quality_backed_recosts": measured_non_quality_backed,
        "diagnosis": {
            "decision": decision,
            "quality_best_candidate_id": qkv8_quality.get("candidate_id"),
            "quality_best_top1_match_rate": qkv8_quality.get("top1_match_rate"),
            "score32_top1_match_rate": (score32 or {}).get("top1_match_rate"),
            "q24_pwl_top1_match_rate": (q24_pwl or {}).get("top1_match_rate"),
            "best_fp16_softmax_proxy_candidate_id": best_proxy.get("candidate_id"),
            "best_fp16_softmax_proxy_critical_path_ns": best_proxy["softmax_metrics"].get("critical_path_ns"),
            "best_fp16_softmax_proxy_die_area_um2": best_proxy["softmax_metrics"].get("die_area_um2"),
            "best_fp16_softmax_proxy_total_power_mw": best_proxy["softmax_metrics"].get("total_power_mw"),
            "non_quality_backed_measured_recost_count": len(measured_non_quality_backed),
            "recommended_next_step": recommended_next_step,
        },
        "inputs": {
            "quality_backed_frontier_json": str(args.quality_backed_frontier_json),
            "score_precision_recovery_json": str(args.score_precision_recovery_json),
            "exact_div_recost_json": str(args.exact_div_recost_json),
            "exact_div_split2_recost_json": str(args.exact_div_split2_recost_json),
            "fp16_softmax_nm1_metrics": str(args.fp16_softmax_nm1_metrics),
            "fp16_softmax_nm2_metrics": str(args.fp16_softmax_nm2_metrics),
        },
        "assumptions": [
            "qkv8_float_exact is the only broad native attention-shadow passing mixed/int8 candidate.",
            "FP16 softmax metrics are measured hardware rows but not yet a composed q8/k8/v8 attention wrapper.",
            "Score32 exact-div and PWL recosts are retained as measured diagnostic rows but are not quality-backed.",
        ],
    }
    return payload


def write_report(payload: JsonDict, path: Path) -> None:
    diag = dict(payload.get("diagnosis") or {})
    lines = [
        "# Mixed-Int8 Quality/Energy Frontier Audit",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- quality_best_candidate_id: `{diag.get('quality_best_candidate_id')}`",
        f"- quality_best_top1_match_rate: `{diag.get('quality_best_top1_match_rate')}`",
        f"- score32_top1_match_rate: `{diag.get('score32_top1_match_rate')}`",
        f"- q24_pwl_top1_match_rate: `{diag.get('q24_pwl_top1_match_rate')}`",
        f"- best_fp16_softmax_proxy_candidate_id: `{diag.get('best_fp16_softmax_proxy_candidate_id')}`",
        f"- best_fp16_softmax_proxy_critical_path_ns: `{diag.get('best_fp16_softmax_proxy_critical_path_ns')}`",
        f"- best_fp16_softmax_proxy_die_area_um2: `{diag.get('best_fp16_softmax_proxy_die_area_um2')}`",
        f"- best_fp16_softmax_proxy_total_power_mw: `{diag.get('best_fp16_softmax_proxy_total_power_mw')}`",
        "",
        "## Recommendation",
        "",
        str(diag.get("recommended_next_step")),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-backed-frontier-json", type=Path, required=True)
    parser.add_argument("--score-precision-recovery-json", type=Path, required=True)
    parser.add_argument("--exact-div-recost-json", type=Path, required=True)
    parser.add_argument("--exact-div-split2-recost-json", type=Path, required=True)
    parser.add_argument("--fp16-softmax-nm1-metrics", type=Path, required=True)
    parser.add_argument("--fp16-softmax-nm2-metrics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
