#!/usr/bin/env python3
"""Recost the separated score32 Llama7B row with measured two-pass service."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _arg_value(args: argparse.Namespace, primary: str, legacy: str) -> Any:
    value = getattr(args, primary, None)
    if value is not None:
        return value
    return getattr(args, legacy)


def _dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _require_positive(value: Any, label: str) -> float:
    result = _float(value)
    if result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _quality_evidence(payload: JsonDict) -> JsonDict:
    decision = _dict(payload.get("decision"))
    best = _dict(payload.get("best_candidate"))
    status = str(decision.get("status") or best.get("decision_status") or "unknown")
    quality_backed = status.endswith("_pass")
    return {
        "status": status,
        "candidate_id": best.get("candidate_id"),
        "teacher_forced_nll_delta_mean": best.get("teacher_forced_nll_delta_mean"),
        "free_running_match_rate": best.get("free_running_match_rate"),
        "candidate_probability_assigned_to_reference_token_mean": best.get(
            "candidate_probability_assigned_to_reference_token_mean"
        ),
        "precision": _dict(payload.get("precision")),
        "quality_backed": quality_backed,
        "precision_aligned": quality_backed,
    }


def _metrics_csv_row(metrics_csv: str, ppa_path: Path) -> JsonDict:
    relative = Path(metrics_csv)
    candidates = [relative] if relative.is_absolute() else [Path.cwd() / relative]
    if not relative.is_absolute():
        candidates.extend(parent / relative for parent in ppa_path.resolve().parents)
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle) if str(row.get("status") or "").strip() == "ok"]
    if not rows:
        return {}
    return min(
        rows,
        key=lambda row: (
            _float(row.get("critical_path_ns"), 1.0e99),
            _float(row.get("instance_area_um2"), 1.0e99),
        ),
    )


def _iterdiv_metrics(payload: JsonDict, ppa_path: Path) -> JsonDict:
    candidates: list[JsonDict] = []
    for proposal in payload.get("proposals", []):
        proposal_dict = _dict(proposal)
        metrics_ref = _dict(proposal_dict.get("metrics_ref"))
        summary = _dict(proposal_dict.get("metric_summary"))
        if str(metrics_ref.get("status") or "") != "ok" or not summary:
            continue
        metrics_csv = str(metrics_ref.get("metrics_csv") or "")
        csv_row = _metrics_csv_row(metrics_csv, ppa_path) if metrics_csv else {}
        candidates.append(
            {
                "critical_path_ns": _require_positive(summary.get("critical_path_ns"), "iterdiv critical_path_ns"),
                "area_um2": _require_positive(
                    csv_row.get("instance_area_um2", summary.get("die_area")),
                    "iterdiv instance_area_um2",
                ),
                "area_metric": "instance_area_um2" if csv_row else "die_area_fallback",
                "power_mw": _require_positive(summary.get("total_power_mw"), "iterdiv total_power_mw"),
                "metrics_csv": metrics_csv,
            }
        )
    if not candidates:
        raise ValueError("iterative-divider PPA has no successful proposal metrics")
    return min(candidates, key=lambda row: (row["critical_path_ns"], row["area_um2"]))


def _component_map(source_candidate: JsonDict) -> JsonDict:
    components = [
        _dict(component)
        for component in source_candidate.get("components", [])
        if isinstance(component, dict)
    ]
    indexed = {str(component.get("component")): component for component in components}
    controller = next(
        (component for component in components if str(component.get("component", "")).startswith("hbm_replay_controller")),
        None,
    )
    required = {
        "dense_int8_gemm_fabric": indexed.get("dense_int8_gemm_fabric"),
        "shared_score32_vector_softmax_overhead": indexed.get("shared_score32_vector_softmax_overhead"),
        "command_dispatch_control": indexed.get("command_dispatch_control"),
        "hbm_replay_controller": controller,
    }
    missing = [name for name, component in required.items() if component is None]
    if missing:
        raise ValueError(f"source separated recost is missing components: {', '.join(sorted(missing))}")
    return required


def _select_scenarios(payload: JsonDict) -> list[JsonDict]:
    rows = [_dict(row) for row in payload.get("rows", []) if isinstance(row, dict)]
    if not rows:
        raise ValueError("frontier input must contain rows")

    if any("score_sram_latency_delta_us" in row for row in rows):
        by_name: dict[str, JsonDict] = {}
        for row in rows:
            name = str(row.get("placement_scenario") or "")
            if name in ("nominal", "conservative") and name not in by_name:
                score_source_latency_us = _require_positive(
                    row.get("score_sram_source_latency_us"),
                    f"{name} integrated frontier score_sram_source_latency_us",
                )
                score_latency_delta_us = _float(row.get("score_sram_latency_delta_us"))
                projected_latency_us = score_source_latency_us + score_latency_delta_us
                by_name[name] = {
                    "name": name,
                    "placement_efficiency": _float(row.get("placement_efficiency")),
                    "shared_sram_capacity_mib": _float(row.get("shared_sram_capacity_mib")),
                    "hbm_byte_share": _float(row.get("hbm_byte_share")),
                    "hbm_share_scale": projected_latency_us / score_source_latency_us,
                    "source_score32_latency_us": score_source_latency_us,
                    "projected_latency_us_hbm_share_scaled": projected_latency_us,
                    "score_sram_energy_mj_per_token": _float(row.get("score_sram_energy_mj_per_token")),
                    "score_sram_macro_area_mm2": _float(row.get("score_sram_macro_area_mm2")),
                    "score_sram_envelope_area_mm2": _float(row.get("score_sram_envelope_area_mm2")),
                }
        missing = [name for name in ("nominal", "conservative") if name not in by_name]
        if missing:
            raise ValueError(f"integrated frontier is missing scenarios: {', '.join(missing)}")
        return [by_name["nominal"], by_name["conservative"]]

    diagnosis = _dict(payload.get("diagnosis"))
    wanted = {0.75: "nominal", 0.55: "conservative"}
    selected: list[JsonDict] = []
    for efficiency, name in wanted.items():
        row = next(
            (candidate for candidate in rows if abs(_float(candidate.get("placement_efficiency")) - efficiency) < 1.0e-9),
            None,
        )
        if row is None:
            raise ValueError(f"score-SRAM recost is missing placement efficiency {efficiency}")
        source_score32_latency_us = _require_positive(
            row.get("source_score32_latency_us"),
            f"{name} score-SRAM source_score32_latency_us",
        )
        projected_latency_us = _require_positive(
            row.get("projected_latency_us_hbm_share_scaled"),
            f"{name} score-SRAM projected_latency_us_hbm_share_scaled",
        )
        selected.append(
            {
                "name": name,
                "placement_efficiency": efficiency,
                "shared_sram_capacity_mib": _float(row.get("shared_sram_capacity_mib")),
                "hbm_byte_share": _float(row.get("hbm_byte_share")),
                "hbm_share_scale": _float(
                    row.get("hbm_share_scale_vs_measured_sram"),
                    projected_latency_us / source_score32_latency_us,
                ),
                "source_score32_latency_us": source_score32_latency_us,
                "projected_latency_us_hbm_share_scaled": projected_latency_us,
                "score_sram_energy_mj_per_token": _float(
                    row.get("score_buffer_energy_mj_per_token"),
                    diagnosis.get("score_buffer_energy_mj_per_token"),
                ),
                "score_sram_macro_area_mm2": _float(
                    diagnosis.get("score_buffer_area_mm2"),
                    _float(row.get("score_buffer_macro_area_um2")) / 1.0e6,
                ),
                "score_sram_envelope_area_mm2": _float(row.get("score_buffer_envelope_area_um2")) / 1.0e6,
            }
        )
    return selected


def _source_remaining_abstractions(source_candidate: JsonDict) -> list[str]:
    filtered: list[str] = []
    for item in source_candidate.get("remaining_abstractions", []):
        text = str(item)
        lower = text.lower()
        if "precision-aligned" in lower or "precision aligned" in lower:
            continue
        filtered.append(text)
    return filtered


def build_report(args: argparse.Namespace) -> JsonDict:
    separated_compute_recost_json = _arg_value(
        args,
        "separated_compute_recost_json",
        "score32_separated_compute_recost_json",
    )
    score_sram_recost_json = _arg_value(
        args,
        "score_sram_recost_json",
        "two_pass_frontier_or_score_sram_json",
    )
    source_payload = _load(separated_compute_recost_json)
    frontier_payload = _load(score_sram_recost_json)
    quality_payload = _load(args.zero_tail_quality_json)
    iterdiv_payload = _load(args.iterdiv_ppa_json)

    source_candidate = _dict(source_payload.get("candidate"))
    if not source_candidate:
        raise ValueError("source separated recost must provide candidate")
    components = _component_map(source_candidate)
    scenarios = _select_scenarios(frontier_payload)
    quality = _quality_evidence(quality_payload)
    iterdiv = _iterdiv_metrics(iterdiv_payload, args.iterdiv_ppa_json)

    source_latency_us = _require_positive(source_candidate.get("latency_us"), "source candidate latency_us")
    source_hbm_energy_mj = _require_positive(
        source_candidate.get("hbm_energy_mj_per_token"),
        "source candidate hbm_energy_mj_per_token",
    )
    source_noc_energy_mj = _require_positive(
        source_candidate.get("noc_energy_mj_per_token"),
        "source candidate noc_energy_mj_per_token",
    )
    source_sram_energy_mj = _require_positive(
        source_candidate.get("sram_energy_mj_per_token"),
        "source candidate sram_energy_mj_per_token",
    )
    source_schedule_clock_ns = _require_positive(
        source_candidate.get("schedule_clock_ns", args.clock_ns),
        "source candidate schedule_clock_ns",
    )
    source_logic_area_mm2 = _require_positive(source_candidate.get("logic_area_mm2"), "source candidate logic_area_mm2")
    source_compute_control_energy_mj = _require_positive(
        source_candidate.get("compute_control_energy_mj_per_token"),
        "source candidate compute_control_energy_mj_per_token",
    )

    dense = components["dense_int8_gemm_fabric"]
    old_shared = components["shared_score32_vector_softmax_overhead"]
    dispatch = components["command_dispatch_control"]
    controller = components["hbm_replay_controller"]
    retained_components = [dense, dispatch, controller]
    retained_logic_area_mm2 = round(
        sum(_require_positive(component.get("area_um2"), f"{component.get('component')} area_um2") for component in retained_components)
        / 1.0e6,
        12,
    )
    retained_logic_power_mw = round(
        sum(_require_positive(component.get("power_mw"), f"{component.get('component')} power_mw") for component in retained_components),
        12,
    )
    removed_shared_energy_mj = round(
        _require_positive(old_shared.get("power_mw"), "shared score32 power_mw") * source_latency_us * 1.0e-6,
        12,
    )
    retained_logic_energy_mj = round(source_compute_control_energy_mj - removed_shared_energy_mj, 12)
    if retained_logic_energy_mj <= 0.0:
        raise ValueError("replacing the shared score32 overhead produced non-positive retained logic energy")

    clock_ns = _float(args.clock_ns)
    divide_cycles_per_head = int(args.divide_cycles_per_head)
    head_count = int(args.head_count)
    per_head_divider_latency_us = divide_cycles_per_head * clock_ns / 1000.0
    divider_energy_total_mj = round(iterdiv["power_mw"] * per_head_divider_latency_us * head_count * 1.0e-6, 12)
    deployments = (
        ("per_head", head_count, 1),
        ("shared", 1, head_count),
    )

    source_remaining_abstractions = _source_remaining_abstractions(source_candidate)
    rows: list[JsonDict] = []
    for scenario in scenarios:
        score_sram_energy_mj = _require_positive(
            scenario.get("score_sram_energy_mj_per_token"),
            f"{scenario['name']} score SRAM energy",
        )
        score_sram_macro_area_mm2 = _require_positive(
            scenario.get("score_sram_macro_area_mm2"),
            f"{scenario['name']} score SRAM macro area",
        )
        score_sram_envelope_area_mm2 = _require_positive(
            scenario.get("score_sram_envelope_area_mm2"),
            f"{scenario['name']} score SRAM envelope area",
        )
        hbm_share_scale = _require_positive(scenario.get("hbm_share_scale"), f"{scenario['name']} hbm share scale")
        projected_latency_us = round(source_latency_us * hbm_share_scale, 12)
        scaled_hbm_energy_mj = round(source_hbm_energy_mj * hbm_share_scale, 12)

        for deployment, instances, serial_head_groups in deployments:
            divider_latency_us = round(per_head_divider_latency_us * serial_head_groups, 12)
            divider_area_mm2 = round(iterdiv["area_um2"] * instances / 1.0e6, 12)
            logic_plus_service_area_mm2 = round(retained_logic_area_mm2 + divider_area_mm2, 12)
            active_power_mw = round(retained_logic_power_mw + iterdiv["power_mw"] * instances, 12)
            compute_control_service_energy_mj = round(retained_logic_energy_mj + divider_energy_total_mj, 12)
            total_energy_mj = round(
                compute_control_service_energy_mj
                + scaled_hbm_energy_mj
                + source_noc_energy_mj
                + source_sram_energy_mj
                + score_sram_energy_mj,
                12,
            )
            component_rows = []
            for component in retained_components:
                component_rows.append(
                    {
                        "component": component.get("component"),
                        "area_um2": _float(component.get("area_um2")),
                        "power_mw": _float(component.get("power_mw")),
                        "critical_path_ns": _float(component.get("critical_path_ns")),
                        "clock_ok": bool(component.get("clock_ok", True)),
                        "source": component.get("source"),
                        "energy_mj_per_token": round(_float(component.get("power_mw")) * source_latency_us * 1.0e-6, 12),
                    }
                )
            component_rows.append(
                {
                    "component": f"two_pass_iterdiv_service_{deployment}",
                    "area_um2": round(iterdiv["area_um2"] * instances, 6),
                    "power_mw": round(iterdiv["power_mw"] * instances, 12),
                    "critical_path_ns": iterdiv["critical_path_ns"],
                    "clock_ok": iterdiv["critical_path_ns"] <= clock_ns,
                    "source": iterdiv.get("metrics_csv"),
                    "energy_mj_per_token": divider_energy_total_mj,
                    "deployment": deployment,
                    "instances": instances,
                    "serial_head_groups": serial_head_groups,
                }
            )
            row_remaining_abstractions = sorted(
                set(
                    source_remaining_abstractions
                    + [
                        "Schedule latency is inherited from the separated compute recost and scaled only by the score-SRAM HBM-share ratio.",
                        "HBM/DRAM service latency and energy are inherited from the separated compute recost and scaled only by the score-SRAM HBM-share ratio.",
                        "sram_macro_floorplan_pnr",
                    ]
                )
            )
            timing_ok = all(bool(component["clock_ok"]) for component in component_rows)
            total_latency_us = round(projected_latency_us + divider_latency_us, 12)
            rows.append(
                {
                    "candidate_id": f"score32_separated_zero_tail_two_pass_{scenario['name']}_{deployment}_iterdiv",
                    "family": "score32_separated_zero_tail_two_pass_iterdiv",
                    "placement_scenario": scenario["name"],
                    "placement_efficiency": scenario["placement_efficiency"],
                    "divider_deployment": deployment,
                    "divider_instances": instances,
                    "serial_head_groups": serial_head_groups,
                    "head_count": head_count,
                    "source_candidate_id": source_candidate.get("candidate_id"),
                    "precision_profile": source_candidate.get("precision_profile"),
                    "precision_aligned": quality["precision_aligned"],
                    "quality_status": quality["status"],
                    "quality_backed": quality["quality_backed"],
                    "free_running_match_rate": quality.get("free_running_match_rate"),
                    "teacher_forced_nll_delta_mean": quality.get("teacher_forced_nll_delta_mean"),
                    "candidate_probability_assigned_to_reference_token_mean": quality.get(
                        "candidate_probability_assigned_to_reference_token_mean"
                    ),
                    "latency_us": total_latency_us,
                    "token_throughput_per_s": round(1_000_000.0 / total_latency_us, 12),
                    "source_logic_area_mm2": source_logic_area_mm2,
                    "baseline_source_latency_us": source_latency_us,
                    "baseline_source_score32_latency_us": scenario["source_score32_latency_us"],
                    "hbm_share_scaled_latency_us": projected_latency_us,
                    "hbm_share_scale": round(hbm_share_scale, 12),
                    "divider_latency_us": divider_latency_us,
                    "divider_critical_path_ns": iterdiv["critical_path_ns"],
                    "divider_schedule_clock_ns": clock_ns,
                    "divider_meets_clock": iterdiv["critical_path_ns"] <= clock_ns,
                    "source_schedule_clock_ns": source_schedule_clock_ns,
                    "source_timing_ok": bool(source_candidate.get("timing_ok", True)),
                    "timing_ok": timing_ok,
                    "energy_mj_per_token": total_energy_mj,
                    "compute_control_service_energy_mj_per_token": compute_control_service_energy_mj,
                    "retained_logic_energy_mj_per_token": retained_logic_energy_mj,
                    "removed_shared_score32_energy_mj_per_token": removed_shared_energy_mj,
                    "divider_energy_mj_per_token": divider_energy_total_mj,
                    "hbm_energy_mj_per_token": scaled_hbm_energy_mj,
                    "noc_energy_mj_per_token": source_noc_energy_mj,
                    "base_sram_energy_mj_per_token": source_sram_energy_mj,
                    "score_sram_energy_mj_per_token": score_sram_energy_mj,
                    "logic_plus_service_area_mm2": logic_plus_service_area_mm2,
                    "retained_logic_area_mm2": retained_logic_area_mm2,
                    "removed_shared_score32_area_mm2": round(_float(old_shared.get("area_um2")) / 1.0e6, 12),
                    "divider_area_mm2": divider_area_mm2,
                    "score_sram_macro_area_mm2": score_sram_macro_area_mm2,
                    "score_sram_envelope_area_mm2": score_sram_envelope_area_mm2,
                    "embodied_logic_plus_score_macro_area_mm2": round(
                        logic_plus_service_area_mm2 + score_sram_macro_area_mm2,
                        12,
                    ),
                    "die_area_mm2": _float(source_candidate.get("die_area_mm2")),
                    "shared_sram_capacity_mib": scenario["shared_sram_capacity_mib"],
                    "hbm_byte_share": scenario["hbm_byte_share"],
                    "active_power_mw": active_power_mw,
                    "active_power_accounting_note": (
                        "Instantaneous active power reports retained logic plus deployed divider instances; "
                        "token energy preserves identical divider work across deployments."
                    ),
                    "components": component_rows,
                    "remaining_abstractions": row_remaining_abstractions,
                    "inherited_schedule_abstraction": {
                        "source_candidate_id": source_candidate.get("candidate_id"),
                        "baseline_latency_us": source_latency_us,
                        "source_score_sram_latency_us": scenario["source_score32_latency_us"],
                        "hbm_share_scale": round(hbm_share_scale, 12),
                        "scaled_latency_us_before_divider": projected_latency_us,
                    },
                    "inherited_hbm_service_abstraction": {
                        "source_hbm_energy_mj_per_token": source_hbm_energy_mj,
                        "scaled_hbm_energy_mj_per_token": scaled_hbm_energy_mj,
                        "hbm_share_scale": round(hbm_share_scale, 12),
                        "hbm_byte_share": scenario["hbm_byte_share"],
                    },
                }
            )

    latency_rank = sorted(rows, key=lambda row: (row["latency_us"], row["embodied_logic_plus_score_macro_area_mm2"]))
    area_rank = sorted(rows, key=lambda row: (row["embodied_logic_plus_score_macro_area_mm2"], row["latency_us"]))
    recommended = latency_rank[0]
    return {
        "version": 1,
        "model": "llm_decoder_attention_separated_two_pass_frontier_v1",
        "decision": "score32_separated_two_pass_frontier_ranked",
        "inputs": {
            "separated_compute_recost_json": str(separated_compute_recost_json),
            "score_sram_recost_json": str(score_sram_recost_json),
            "zero_tail_quality_json": str(args.zero_tail_quality_json),
            "iterdiv_ppa_json": str(args.iterdiv_ppa_json),
        },
        "iterdiv_metrics": iterdiv,
        "schedule": {
            "source_schedule_clock_ns": source_schedule_clock_ns,
            "divider_schedule_clock_ns": clock_ns,
            "divide_cycles_per_head": divide_cycles_per_head,
            "head_count": head_count,
            "per_head_divider_latency_us": per_head_divider_latency_us,
            "shared_divider_latency_us": per_head_divider_latency_us * head_count,
            "note": "Separated candidate latency is inherited as the baseline; divider service is a measured 10ns two-pass abstraction.",
        },
        "rows": rows,
        "latency_rank": latency_rank,
        "area_rank": area_rank,
        "diagnosis": {
            "recommended_candidate": recommended["candidate_id"],
            "recommended_latency_us": recommended["latency_us"],
            "recommended_token_throughput_per_s": recommended["token_throughput_per_s"],
            "recommended_total_energy_mj_per_token": recommended["energy_mj_per_token"],
            "recommended_embodied_area_mm2": recommended["embodied_logic_plus_score_macro_area_mm2"],
            "minimum_area_candidate": area_rank[0]["candidate_id"],
            "shared_divider_latency_penalty_us": round(per_head_divider_latency_us * (head_count - 1), 12),
            "per_head_divider_area_premium_mm2": round(iterdiv["area_um2"] * (head_count - 1) / 1.0e6, 12),
            "quality_status": quality["status"],
            "precision_status": quality["status"],
            "precision_aligned": quality["precision_aligned"],
            "inherited_schedule_abstraction": "score32_separated_compute_recost_scaled_by_hbm_share_ratio",
            "inherited_hbm_service_abstraction": "score32_separated_compute_recost_scaled_by_hbm_share_ratio",
            "remaining_abstractions": [
                "score32_separated_compute_schedule_inheritance",
                "hbm_dram_service",
                "sram_macro_floorplan_pnr",
            ],
        },
        "assumptions": [
            "The separated score32 recost supplies the baseline dense producer, dispatch, controller, NoC, and tile-SRAM costs.",
            "Score-SRAM integration transfers only the HBM-share scale ratio onto inherited latency and HBM energy; it does not reuse the slow wrapper's absolute latency.",
            "The old shared_score32_vector_softmax_overhead component is replaced by measured iterative two-pass service rather than stacked on top of it.",
            "Divider total active work energy is identical across per-head and shared deployments; only area, instantaneous power, and serialized latency change.",
            "Score SRAM raw macro area is reported separately from its placement envelope so the envelope is not double-counted as embodied silicon.",
            "Zero-tail quality pass is treated as the precision-aligned quality witness for the two-pass recost.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Separated Two-Pass Frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- recommended candidate: `{diagnosis['recommended_candidate']}`",
        f"- recommended latency us: `{diagnosis['recommended_latency_us']}`",
        f"- minimum-area candidate: `{diagnosis['minimum_area_candidate']}`",
        f"- quality status: `{diagnosis['quality_status']}`",
        "",
        "| candidate | latency us | token/s | energy mJ/token | embodied logic + score macro mm2 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["latency_rank"]:
        lines.append(
            f"| {row['candidate_id']} | {row['latency_us']} | {row['token_throughput_per_s']} | "
            f"{row['energy_mj_per_token']} | {row['embodied_logic_plus_score_macro_area_mm2']} |"
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--separated-compute-recost-json",
        "--score32-separated-compute-recost-json",
        dest="separated_compute_recost_json",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--score-sram-recost-json",
        "--two-pass-frontier-or-score-sram-json",
        dest="score_sram_recost_json",
        type=Path,
        required=True,
    )
    parser.add_argument("--zero-tail-quality-json", type=Path, required=True)
    parser.add_argument("--iterdiv-ppa-json", type=Path, required=True)
    parser.add_argument("--head-count", type=int, default=32)
    parser.add_argument("--divide-cycles-per-head", type=int, default=480)
    parser.add_argument("--clock-ns", type=float, default=10.0)
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
