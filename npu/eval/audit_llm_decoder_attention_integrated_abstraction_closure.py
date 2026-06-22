#!/usr/bin/env python3
"""Audit the current Llama7B attention frontier after recent abstraction closures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _maybe_load_json(path: Path | None) -> JsonDict | None:
    if path is None or not path.exists():
        return None
    return _load_json(path)


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


def _latency_to_tokens_per_s(latency_us: float) -> float | None:
    if latency_us <= 0.0:
        return None
    return 1_000_000.0 / latency_us


def _kv4_quality(native_quality: JsonDict) -> JsonDict | None:
    best = native_quality.get("best_kv4_candidate")
    if isinstance(best, dict):
        return best
    candidates = native_quality.get("candidate_summary")
    if not isinstance(candidates, list):
        return None
    kv4 = [row for row in candidates if isinstance(row, dict) and _as_int(row.get("kv_bits"), -1) == 4]
    if not kv4:
        return None
    return max(
        kv4,
        key=lambda row: (
            _as_float(row.get("top1_match_rate")),
            _as_float(row.get("topk_contains_rate")),
            _as_float(row.get("mean_logit_cosine")),
            -_as_float(row.get("mean_probability_kl")),
        ),
    )


def _kv8_quality(native_quality: JsonDict) -> JsonDict | None:
    candidates = native_quality.get("candidate_summary")
    if isinstance(candidates, dict):
        kv8_rows = candidates.get("kv8")
        if isinstance(kv8_rows, list) and kv8_rows:
            return kv8_rows[0] if isinstance(kv8_rows[0], dict) else None
    if not isinstance(candidates, list):
        return None
    kv8 = [row for row in candidates if isinstance(row, dict) and _as_int(row.get("kv_bits"), -1) == 8]
    return kv8[0] if kv8 else None


def _precision_summary(native_quality: JsonDict, hbm_best: JsonDict) -> JsonDict:
    decision = native_quality.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    kv4 = _kv4_quality(native_quality)
    kv8 = _kv8_quality(native_quality)
    kv4_cosine = _as_float((kv4 or {}).get("mean_logit_cosine"))
    kv4_kl = _as_float((kv4 or {}).get("mean_probability_kl"))
    kv4_top1 = _as_float((kv4 or {}).get("top1_match_rate"))
    kv4_topk = _as_float((kv4 or {}).get("topk_contains_rate"))
    return {
        "selected_frontier_kv_bits": _as_int(hbm_best.get("kv_bits")),
        "selected_frontier_kv_sharing": str(hbm_best.get("kv_sharing", "")),
        "native_quality_status": str(decision.get("status", "")),
        "native_quality_cautions": list(decision.get("cautions") or []),
        "kv8_candidate": kv8,
        "kv4_candidate": kv4,
        "kv4_promotable_without_recovery": bool(
            kv4
            and kv4_top1 >= 0.98
            and kv4_topk >= 0.995
            and kv4_cosine >= 0.999
            and kv4_kl <= 0.01
        ),
    }


def _subcampaign_summary(best_point: JsonDict | None) -> JsonDict | None:
    if not best_point:
        return None
    best = best_point.get("best")
    if not isinstance(best, dict):
        return None
    return {
        "arch_id": best.get("arch_id"),
        "macro_mode": best.get("macro_mode"),
        "latency_ms_mean": best.get("latency_ms_mean"),
        "throughput_infer_per_s_mean": best.get("throughput_infer_per_s_mean"),
        "energy_mj_mean": best.get("energy_mj_mean"),
        "die_area_um2_mean": best.get("die_area_um2_mean"),
        "total_power_mw_mean": best.get("total_power_mw_mean"),
        "critical_path_ns_mean": best.get("critical_path_ns_mean"),
        "scope": "subcampaign_not_full_llama7b_integrated_energy",
    }


def _build_payload(
    *,
    composed_datapath: JsonDict,
    hbm_quality_backed: JsonDict,
    native_quality: JsonDict,
    q12_frontier_best: JsonDict | None,
    hbm_campaign_best: JsonDict | None,
) -> JsonDict:
    hbm_best = hbm_quality_backed.get("best")
    if not isinstance(hbm_best, dict):
        raise SystemExit("hbm-quality-backed-json is missing object field 'best'")
    composed_diagnosis = composed_datapath.get("diagnosis")
    composed_diagnosis = composed_diagnosis if isinstance(composed_diagnosis, dict) else {}
    best_requested = composed_datapath.get("best_requested")
    best_requested = best_requested if isinstance(best_requested, dict) else {}

    hbm_latency_us = _as_float(hbm_best.get("latency_us"))
    precision = _precision_summary(native_quality, hbm_best)
    q12_promotable = str(composed_diagnosis.get("decision")) not in {
        "",
        "dual_stream_area_blocked",
    } and bool(composed_datapath.get("best_feasible"))
    q12_clock_ok = bool(composed_diagnosis.get("best_requested_compute_clock_ok"))
    q12_area_fit = bool(composed_diagnosis.get("best_requested_area_fit"))
    full_energy_available = False

    remaining_abstractions = [
        "HBM/DRAM service is still an aggregate bandwidth/efficiency model, not cycle-accurate DRAM timing.",
        "NoC/SRAM contention in the selected HBM frontier is still a compact service model.",
        "Full Llama7B integrated energy is not yet composed from measured compute, SRAM, NoC, and HBM energy.",
    ]
    if not q12_promotable:
        remaining_abstractions.append(
            "Measured q12/PWL dual-stream composed datapath is available, but the current dual-stream frontier is blocked by area or clock and cannot be promoted."
        )
    if not precision["kv4_promotable_without_recovery"]:
        remaining_abstractions.append(
            "KV4 remains precision-risky without QAT, scale-granularity recovery, or a larger 7B-class confirmation."
        )

    best = {
        "arch_id": "physical_hbm_gqa8_kv8_service_frontier",
        "latency_us": hbm_latency_us,
        "token_throughput_per_s": _latency_to_tokens_per_s(hbm_latency_us),
        "die_area_mm2": hbm_best.get("die_area_mm2"),
        "kv_bits": hbm_best.get("kv_bits"),
        "kv_sharing": hbm_best.get("kv_sharing"),
        "macs_per_cycle": hbm_best.get("macs_per_cycle"),
        "vector_ops_per_cycle": hbm_best.get("vector_ops_per_cycle"),
        "dominant_resource": hbm_best.get("dominant_tile_resource"),
        "energy_mj": None,
        "energy_status": "full_integrated_energy_missing",
        "precision_status": precision["native_quality_status"],
    }

    decision = "integrated_closure_recorded_q12_blocked_hbm_service_frontier"
    return {
        "version": 1,
        "model": "llm_decoder_attention_integrated_abstraction_closure_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "recommended_next_step": "close integrated energy and HBM/NoC/SRAM service details before promoting a final Llama7B point",
            "selected_frontier": "physical_hbm_gqa8_kv8_service_frontier",
            "q12_pwl_datapath": str(composed_diagnosis.get("decision", "")),
            "precision_status": precision["native_quality_status"],
        },
        "best": best,
        "ranked_candidates": [
            {
                "name": "quality_backed_hbm_gqa8_kv8",
                "status": "current_selected_service_frontier",
                "token_throughput_per_s": best["token_throughput_per_s"],
                "latency_us": best["latency_us"],
                "area_mm2": best["die_area_mm2"],
                "energy_mj": None,
                "precision": {
                    "kv_bits": best["kv_bits"],
                    "kv_sharing": best["kv_sharing"],
                    "status": precision["native_quality_status"],
                },
                "dominant_resource": best["dominant_resource"],
            },
            {
                "name": "q12_pwl_dual_stream_composed_datapath",
                "status": "blocked_not_promotable" if not q12_promotable else "promotable",
                "latency_us_if_feasible": composed_diagnosis.get("best_requested_latency_us"),
                "area_fit": q12_area_fit,
                "clock_ok": q12_clock_ok,
                "logic_slack_um2": composed_diagnosis.get("best_requested_logic_slack_um2"),
                "required_compute_density_gain": composed_diagnosis.get(
                    "best_requested_required_compute_density_gain"
                ),
                "compute_mode": best_requested.get("compute_mode"),
            },
        ],
        "precision": precision,
        "subcampaign_energy_refs": {
            "q12_pwl_tail_stress": _subcampaign_summary(q12_frontier_best),
            "hbm_quality_backed_mlp_smoke": _subcampaign_summary(hbm_campaign_best),
        },
        "closure_flags": {
            "q12_pwl_composed_datapath_measured": True,
            "q12_pwl_dual_stream_promotable": q12_promotable,
            "native_7b_quality_available": bool(native_quality),
            "conservative_kv8_quality_backed": _as_int(hbm_best.get("kv_bits")) == 8,
            "kv4_promotable_without_recovery": precision["kv4_promotable_without_recovery"],
            "hbm_model_cycle_accurate": False,
            "integrated_energy_model_available": full_energy_available,
        },
        "closure_diagnosis": {
            "selected_frontier": "Use conservative GQA8/KV8 physical-HBM service frontier until the remaining service and energy abstractions are closed.",
            "q12_pwl_datapath": str(composed_diagnosis.get("decision", "")),
            "q12_pwl_next_step": str(composed_diagnosis.get("recommended_next_step", "")),
            "precision_next_step": str((native_quality.get("decision") or {}).get("next_step", "")),
        },
        "recommended_next_l1_points": [
            {
                "primitive": "denser_or_lower_replica_q12_pwl_dual_stream_datapath",
                "reason": "The measured q12/PWL wrapper blocks the dual-stream frontier on area/clock before it can improve throughput.",
            },
        ],
        "recommended_next_l2_jobs": [
            {
                "job": "integrated_energy_closure",
                "reason": "Token throughput and area are bounded, but full Llama7B energy is still not comparable across candidates.",
            },
            {
                "job": "hbm_noc_sram_service_detail",
                "reason": "The selected frontier is still HBM-service dominated and uses aggregate NoC/SRAM service assumptions.",
            },
            {
                "job": "kv4_recovery_or_larger_quality_confirmation",
                "reason": "KV4 has top-k stability but misses the cosine/KL caution line.",
            },
        ],
        "remaining_abstractions": remaining_abstractions,
        "source_artifacts": {
            "composed_datapath_model": composed_datapath.get("model"),
            "hbm_quality_backed_model": hbm_quality_backed.get("model"),
            "native_quality_model": (native_quality.get("model") or {}).get("model_id"),
        },
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Integrated Abstraction Closure",
        "",
        "## Selected Frontier",
        f"- arch_id: `{best['arch_id']}`",
        f"- latency_us: `{best['latency_us']}`",
        f"- token_throughput_per_s: `{best['token_throughput_per_s']}`",
        f"- die_area_mm2: `{best['die_area_mm2']}`",
        f"- kv: `{best['kv_sharing']} / {best['kv_bits']}b`",
        f"- dominant_resource: `{best['dominant_resource']}`",
        f"- energy_status: `{best['energy_status']}`",
        "",
        "## Closure Flags",
    ]
    for key, value in payload["closure_flags"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Ranked Candidates"])
    for row in payload["ranked_candidates"]:
        lines.append(f"- `{row['name']}`: `{row['status']}`")
    lines.extend(["", "## Remaining Abstractions"])
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Jobs"])
    for item in payload["recommended_next_l2_jobs"]:
        lines.append(f"- `{item['job']}`: {item['reason']}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--composed-datapath-json", type=Path, required=True)
    parser.add_argument("--hbm-quality-backed-json", type=Path, required=True)
    parser.add_argument("--native-quality-json", type=Path, required=True)
    parser.add_argument("--q12-frontier-best-json", type=Path)
    parser.add_argument("--hbm-campaign-best-json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = _build_payload(
        composed_datapath=_load_json(args.composed_datapath_json),
        hbm_quality_backed=_load_json(args.hbm_quality_backed_json),
        native_quality=_load_json(args.native_quality_json),
        q12_frontier_best=_maybe_load_json(args.q12_frontier_best_json),
        hbm_campaign_best=_maybe_load_json(args.hbm_campaign_best_json),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
