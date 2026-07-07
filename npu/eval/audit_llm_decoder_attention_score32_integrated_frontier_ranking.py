#!/usr/bin/env python3
"""Rank the closed score32 Llama7B attention row against prior frontier evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _quality_status(score32_quality: JsonDict) -> JsonDict:
    decision = score32_quality.get("decision")
    decision_dict = _as_dict(decision)
    best = _as_dict(score32_quality.get("best_candidate"))
    status = str(decision_dict.get("status") or best.get("decision_status") or "unknown")
    return {
        "status": status,
        "candidate_id": best.get("candidate_id"),
        "teacher_forced_nll_delta_mean": best.get("teacher_forced_nll_delta_mean"),
        "free_running_match_rate": best.get("free_running_match_rate"),
        "candidate_probability_assigned_to_reference_token_mean": best.get(
            "candidate_probability_assigned_to_reference_token_mean"
        ),
        "quality_backed": status.endswith("_pass"),
    }


def _score32_row(
    score32_hbm: JsonDict,
    measured_command: JsonDict,
    score32_quality: JsonDict,
    score32_physical: JsonDict | None = None,
) -> JsonDict:
    best = _as_dict(score32_hbm.get("best_latency"))
    measured_source = score32_physical if score32_physical is not None else measured_command
    measured = _as_dict(measured_source.get("best_requested"))
    quality = _quality_status(score32_quality)
    uses_physical_recost = score32_physical is not None
    latency_us = _as_float(best.get("latency_us"))
    token_throughput_per_s = _as_float(best.get("token_throughput_per_s"))
    compute_energy_mj_per_token = _as_float(best.get("compute_energy_mj_per_token"))
    hbm_energy_mj_per_token = _as_float(best.get("hbm_energy_mj_per_token"))
    total_energy_mj_per_token = _as_float(best.get("total_energy_mj_per_token"))
    source_artifact = "score32_hbm_dram_service_closure"
    candidate_id = "score32_exp_lut_hbm_dram_service_closure_best"
    abstraction_status = "measured_wrapper_command_control_sram_envelope_hbm_command_service"
    remaining_abstractions = list(best.get("remaining_abstractions") or [])

    if uses_physical_recost:
        latency_us = _as_float(
            measured.get("replica_recost_latency_us") or measured.get("adjusted_latency_us_if_feasible"),
            latency_us,
        )
        if latency_us > 0:
            token_throughput_per_s = 1_000_000.0 / latency_us
        compute_power_mw = _as_float(
            measured.get("substituted_compute_plus_control_power_mw")
            or measured.get("logic_power_mw")
            or measured.get("compute_power_mw")
            or best.get("compute_power_mw")
        )
        if compute_power_mw > 0 and latency_us > 0:
            compute_energy_mj_per_token = compute_power_mw * latency_us * 1.0e-6
            total_energy_mj_per_token = compute_energy_mj_per_token + hbm_energy_mj_per_token
        source_artifact = "score32_schedule_wrapper_recost_with_hbm_service"
        candidate_id = "score32_exp_lut_schedule_wrapper_hbm_service_best"
        abstraction_status = "measured_schedule_wrapper_recost_sram_envelope_hbm_command_service"
        remaining_abstractions = sorted(
            {
                *remaining_abstractions,
                *list(score32_physical.get("remaining_abstractions") or []),
                "HBM/DRAM service and energy are reused from the score32 HBM closure because the wrapper recost does not change token memory traffic.",
            }
        )

    return {
        "candidate_id": candidate_id,
        "family": "score32_exp_lut_div",
        "source_artifact": source_artifact,
        "latency_us": latency_us,
        "token_throughput_per_s": token_throughput_per_s,
        "energy_mj_per_token": total_energy_mj_per_token,
        "compute_energy_mj_per_token": compute_energy_mj_per_token,
        "hbm_energy_mj_per_token": hbm_energy_mj_per_token,
        "die_area_mm2": _as_float(measured.get("die_area_mm2")),
        "compute_area_mm2": _as_float(
            measured.get("replica_recost_compute_area_um2") or measured.get("compute_area_um2")
        )
        / 1.0e6,
        "macs_per_cycle": _as_float(measured.get("replica_recost_macs_per_cycle") or best.get("macs_per_cycle")),
        "precision_status": quality["status"],
        "quality_backed": quality["quality_backed"],
        "quality": quality,
        "abstraction_status": abstraction_status,
        "remaining_abstractions": remaining_abstractions,
        "promotable": bool(quality["quality_backed"]),
    }


def _best_row(source: JsonDict) -> JsonDict:
    return _as_dict(source.get("best"))


def _prior_row(
    *,
    candidate_id: str,
    family: str,
    source_artifact: str,
    row: JsonDict,
    precision_status: str,
    quality_backed: bool,
    abstraction_status: str,
    promotable: bool,
    remaining_abstractions: list[str],
) -> JsonDict:
    return {
        "candidate_id": candidate_id,
        "family": family,
        "source_artifact": source_artifact,
        "latency_us": _as_float(row.get("latency_us")),
        "token_throughput_per_s": _as_float(row.get("token_throughput_per_s")),
        "energy_mj_per_token": _as_float(row.get("energy_mj")),
        "compute_energy_mj_per_token": _as_float(_as_dict(row.get("energy_components")).get("compute_mj")),
        "hbm_energy_mj_per_token": _as_float(_as_dict(row.get("energy_components")).get("hbm_mj")),
        "die_area_mm2": _as_float(row.get("die_area_mm2")),
        "compute_area_mm2": _as_float(row.get("compute_area_um2")) / 1.0e6,
        "macs_per_cycle": _as_float(row.get("macs_per_cycle")),
        "precision_status": precision_status,
        "quality_backed": quality_backed,
        "abstraction_status": abstraction_status,
        "remaining_abstractions": remaining_abstractions,
        "promotable": promotable,
    }


def _abstract_integrated_row(integrated_energy: JsonDict) -> JsonDict:
    row = _best_row(integrated_energy)
    return {
        "candidate_id": str(row.get("candidate_id") or row.get("arch_id") or "abstract_integrated_energy_best"),
        "family": "abstract_integrated_gqa8_kv8",
        "source_artifact": "integrated_energy_closure_r2",
        "latency_us": _as_float(row.get("latency_us")),
        "token_throughput_per_s": _as_float(row.get("token_throughput_per_s")),
        "energy_mj_per_token": _as_float(row.get("energy_mj")),
        "compute_energy_mj_per_token": _as_float(_as_dict(row.get("energy_components")).get("compute_mj")),
        "hbm_energy_mj_per_token": _as_float(_as_dict(row.get("energy_components")).get("hbm_mj")),
        "die_area_mm2": _as_float(row.get("die_area_mm2")),
        "compute_area_mm2": 0.0,
        "macs_per_cycle": _as_float(row.get("macs_per_cycle")),
        "precision_status": "planning_only_native_gqa8_kv8",
        "quality_backed": False,
        "abstraction_status": "abstract_compute_target_infeasible_after_measured_compute_closure",
        "remaining_abstractions": [
            "abstract_compute_capacity",
            "parameterized_energy",
        ],
        "promotable": False,
    }


def _rank_rows(rows: list[JsonDict], *, promotable_only: bool = False) -> list[JsonDict]:
    candidates = [row for row in rows if (row.get("promotable") or not promotable_only)]
    return sorted(
        candidates,
        key=lambda row: (
            _as_float(row.get("latency_us"), 1.0e99),
            _as_float(row.get("energy_mj_per_token"), 1.0e99),
            _as_float(row.get("die_area_mm2"), 1.0e99),
        ),
    )


def _energy_rank(rows: list[JsonDict], *, promotable_only: bool = False) -> list[JsonDict]:
    candidates = [row for row in rows if (row.get("promotable") or not promotable_only)]
    return sorted(
        candidates,
        key=lambda row: (
            _as_float(row.get("energy_mj_per_token"), 1.0e99),
            _as_float(row.get("latency_us"), 1.0e99),
            _as_float(row.get("die_area_mm2"), 1.0e99),
        ),
    )


def build_report(args: argparse.Namespace) -> JsonDict:
    score32_hbm = _load_json(args.score32_hbm_dram_service_json)
    measured_command = _load_json(args.score32_measured_command_control_json)
    score32_physical = _load_json(args.score32_physical_feasibility_json) if args.score32_physical_feasibility_json else None
    score32_quality = _load_json(args.score32_quality_json)
    measured_compute = _load_json(args.measured_compute_energy_json)
    mixed_int8 = _load_json(args.mixed_int8_energy_json)
    integrated = _load_json(args.integrated_energy_json)

    rows = [
        _score32_row(score32_hbm, measured_command, score32_quality, score32_physical),
        _prior_row(
            candidate_id=str(_best_row(measured_compute).get("candidate_id") or "measured_fp16_compute_energy_best"),
            family="measured_exact_fp16_gqa8_kv8",
            source_artifact="measured_compute_energy_closure",
            row=_best_row(measured_compute),
            precision_status="conservative_native_gqa8_kv8",
            quality_backed=True,
            abstraction_status="measured_compute_with_source_backed_hbm_energy",
            promotable=True,
            remaining_abstractions=[
                "source_backed_aggregate_hbm_energy_not_vendor_current_signoff",
                "profile_scaled_noc_sram_energy",
            ],
        ),
        _prior_row(
            candidate_id=str(_best_row(mixed_int8).get("candidate_id") or "mixed_int8_energy_best"),
            family="mixed_int8_compute",
            source_artifact="mixed_int8_energy_closure_r2",
            row=_best_row(mixed_int8),
            precision_status="latency_candidate_pending_real_checkpoint_quality",
            quality_backed=False,
            abstraction_status="measured_int8_compute_with_source_backed_hbm_energy",
            promotable=False,
            remaining_abstractions=[
                "real_checkpoint_quality_not_promoted_for_this_compute_path",
                "source_backed_aggregate_hbm_energy_not_vendor_current_signoff",
            ],
        ),
        _abstract_integrated_row(integrated),
    ]

    latency_rank = _rank_rows(rows)
    energy_rank = _energy_rank(rows)
    promotable_latency_rank = _rank_rows(rows, promotable_only=True)
    promotable_energy_rank = _energy_rank(rows, promotable_only=True)
    best_precision_safe = promotable_latency_rank[0]
    best_energy_safe = promotable_energy_rank[0]
    score32 = rows[0]
    decision = (
        "score32_integrated_frontier_best_precision_safe_throughput"
        if best_precision_safe["candidate_id"] == score32["candidate_id"]
        else "score32_integrated_frontier_ranking_recorded"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
        "decision": decision,
        "inputs": {
            "score32_hbm_dram_service_json": str(args.score32_hbm_dram_service_json),
            "score32_measured_command_control_json": str(args.score32_measured_command_control_json),
            "score32_physical_feasibility_json": str(args.score32_physical_feasibility_json)
            if args.score32_physical_feasibility_json
            else None,
            "score32_quality_json": str(args.score32_quality_json),
            "measured_compute_energy_json": str(args.measured_compute_energy_json),
            "mixed_int8_energy_json": str(args.mixed_int8_energy_json),
            "integrated_energy_json": str(args.integrated_energy_json),
        },
        "diagnosis": {
            "decision": decision,
            "best_latency_candidate": latency_rank[0]["candidate_id"],
            "best_energy_candidate": energy_rank[0]["candidate_id"],
            "best_precision_safe_candidate": best_precision_safe["candidate_id"],
            "best_precision_safe_energy_candidate": best_energy_safe["candidate_id"],
            "current_recommended_candidate": best_precision_safe["candidate_id"],
            "score32_latency_us": score32["latency_us"],
            "score32_token_throughput_per_s": score32["token_throughput_per_s"],
            "score32_total_energy_mj_per_token": score32["energy_mj_per_token"],
            "score32_die_area_mm2": score32["die_area_mm2"],
            "score32_quality_status": score32["precision_status"],
            "score32_vs_measured_fp16_energy_ratio": round(
                score32["energy_mj_per_token"] / max(1.0e-12, best_energy_safe["energy_mj_per_token"]), 9
            ),
            "score32_vs_measured_fp16_throughput_ratio": round(
                score32["token_throughput_per_s"] / max(1.0e-12, best_energy_safe["token_throughput_per_s"]), 9
            ),
            "excluded_fastest_candidate": latency_rank[0]["candidate_id"]
            if not latency_rank[0].get("promotable")
            else None,
            "remaining_abstractions": sorted(
                {
                    item
                    for row in rows
                    if row.get("promotable")
                    for item in list(row.get("remaining_abstractions") or [])
                }
            ),
        },
        "rows": rows,
        "latency_rank": latency_rank,
        "energy_rank": energy_rank,
        "promotable_latency_rank": promotable_latency_rank,
        "promotable_energy_rank": promotable_energy_rank,
        "assumptions": [
            "Rows are ranked by explicit metrics from merged evidence; no new PPA is synthesized in this audit.",
            "The score32 row is quality-backed by the bounded generation-quality gate and measured through wrapper, command-control, SRAM-envelope, and HBM/DRAM service closure.",
            "The mixed-int8 energy row is retained as a fast non-promotable latency candidate because its precision path is not promoted by the current real-checkpoint evidence.",
            "The older integrated-energy row is retained as planning-only because measured-compute closure made its abstract compute target infeasible.",
        ],
        "next_step": {
            "recommended_next_step": (
                "Use score32 as the current precision-safe throughput frontier and measured exact-FP16 as the "
                "energy reference; next reduce score32 compute energy or validate a lower-energy mixed/int8 path."
            ),
            "score32_energy_reduction_required_for_energy_best": True,
            "mixed_int8_requires_quality_closure": True,
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    d = payload["diagnosis"]
    lines = [
        "# Score32 Integrated Frontier Ranking",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best latency candidate: `{d['best_latency_candidate']}`",
        f"- best energy candidate: `{d['best_energy_candidate']}`",
        f"- best precision-safe throughput candidate: `{d['best_precision_safe_candidate']}`",
        f"- current recommended candidate: `{d['current_recommended_candidate']}`",
        f"- score32 latency us: `{d['score32_latency_us']}`",
        f"- score32 total energy mJ/token: `{d['score32_total_energy_mj_per_token']}`",
        f"- score32 die area mm2: `{d['score32_die_area_mm2']}`",
        f"- score32 quality status: `{d['score32_quality_status']}`",
        "",
        "## Promotable Latency Rank",
        "",
        "| candidate | latency us | token/s | energy mJ/token | area mm2 | precision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["promotable_latency_rank"]:
        lines.append(
            "| {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj_per_token} | "
            "{die_area_mm2} | {precision_status} |".format(**row)
        )
    lines.extend(["", "## All Rows", "", "| candidate | promotable | latency us | energy mJ/token | status |", "|---|---:|---:|---:|---|"])
    for row in payload["latency_rank"]:
        lines.append(
            "| {candidate_id} | {promotable} | {latency_us} | {energy_mj_per_token} | "
            "{abstraction_status} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score32-hbm-dram-service-json", type=Path, required=True)
    parser.add_argument("--score32-measured-command-control-json", type=Path, required=True)
    parser.add_argument("--score32-physical-feasibility-json", type=Path)
    parser.add_argument("--score32-quality-json", type=Path, required=True)
    parser.add_argument("--measured-compute-energy-json", type=Path, required=True)
    parser.add_argument("--mixed-int8-energy-json", type=Path, required=True)
    parser.add_argument("--integrated-energy-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
