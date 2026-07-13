#!/usr/bin/env python3
"""Recost the Llama7B score32 frontier with the measured two-pass service."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _metrics_csv_row(metrics_csv: str, ppa_path: Path) -> JsonDict:
    relative = Path(metrics_csv)
    candidates = [relative] if relative.is_absolute() else [Path.cwd() / relative]
    if not relative.is_absolute():
        candidates.extend(parent / relative for parent in ppa_path.resolve().parents)
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        return {}
    return min(rows, key=lambda row: (_float(row.get("critical_path_ns"), 1.0e99), _float(row.get("instance_area_um2"), 1.0e99)))


def _iterdiv_metrics(payload: JsonDict, ppa_path: Path) -> JsonDict:
    candidates: list[JsonDict] = []
    for proposal in payload.get("proposals", []):
        if not isinstance(proposal, dict):
            continue
        metrics_ref = _dict(proposal.get("metrics_ref"))
        summary = _dict(proposal.get("metric_summary"))
        if metrics_ref.get("status") != "ok" or not summary:
            continue
        metrics_csv = str(metrics_ref.get("metrics_csv") or "")
        csv_row = _metrics_csv_row(metrics_csv, ppa_path) if metrics_csv else {}
        candidates.append(
            {
                "critical_path_ns": _float(summary.get("critical_path_ns")),
                "area_um2": _float(csv_row.get("instance_area_um2"), _float(summary.get("die_area"))),
                "area_metric": "instance_area_um2" if csv_row else "die_area_fallback",
                "power_mw": _float(summary.get("total_power_mw")),
                "metrics_csv": metrics_csv,
            }
        )
    if not candidates:
        raise ValueError("iterative-divider PPA has no successful proposal metrics")
    return min(candidates, key=lambda row: (row["critical_path_ns"], row["area_um2"]))


def _source_frontier_row(payload: JsonDict) -> JsonDict:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    for row in rows:
        if str(row.get("candidate_id", "")).startswith("score32_"):
            return dict(row)
    raise ValueError("source ranking has no score32 frontier row")


def _sram_scenarios(payload: JsonDict) -> list[JsonDict]:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    wanted = {0.75: "nominal", 0.55: "conservative"}
    selected = []
    for efficiency, name in wanted.items():
        match = next(
            (row for row in rows if abs(_float(row.get("placement_efficiency")) - efficiency) < 1e-9),
            None,
        )
        if match is None:
            raise ValueError(f"score-SRAM recost is missing placement efficiency {efficiency}")
        selected.append({"name": name, **match})
    return selected


def build_report(args: argparse.Namespace) -> JsonDict:
    source_payload = _load(args.source_frontier_ranking_json)
    sram_payload = _load(args.score_sram_recost_json)
    quality_payload = _load(args.zero_tail_quality_json)
    iterdiv_payload = _load(args.iterdiv_ppa_json)

    source = _source_frontier_row(source_payload)
    sram_diagnosis = _dict(sram_payload.get("diagnosis"))
    quality = _dict(quality_payload.get("best_candidate"))
    quality_decision = _dict(quality_payload.get("decision"))
    iterdiv = _iterdiv_metrics(iterdiv_payload, args.iterdiv_ppa_json)
    clock_ns = _float(args.clock_ns)
    divide_cycles_per_head = int(args.divide_cycles_per_head)
    head_count = int(args.head_count)
    per_head_latency_us = divide_cycles_per_head * clock_ns / 1000.0
    divider_energy_per_head_mj = iterdiv["power_mw"] * per_head_latency_us * 1.0e-6
    score_sram_energy_mj = _float(sram_diagnosis.get("score_buffer_energy_mj_per_token"))
    score_sram_macro_area_mm2 = _float(sram_diagnosis.get("score_buffer_area_mm2"))
    source_frontier_latency_us = _float(source.get("latency_us"))

    rows: list[JsonDict] = []
    deployments = (
        ("per_head", head_count, 1),
        ("shared", 1, head_count),
    )
    for scenario in _sram_scenarios(sram_payload):
        for deployment, instances, serial_head_groups in deployments:
            divider_latency_us = per_head_latency_us * serial_head_groups
            sram_source_latency_us = _float(scenario.get("source_score32_latency_us"))
            sram_latency_delta_us = (
                _float(scenario.get("projected_latency_us_hbm_share_scaled")) - sram_source_latency_us
            )
            latency_us = source_frontier_latency_us + sram_latency_delta_us + divider_latency_us
            divider_area_mm2 = iterdiv["area_um2"] * instances / 1.0e6
            divider_energy_mj = divider_energy_per_head_mj * head_count
            total_energy_mj = _float(source.get("energy_mj_per_token")) + score_sram_energy_mj + divider_energy_mj
            logic_area_mm2 = _float(source.get("compute_area_mm2")) + divider_area_mm2
            rows.append(
                {
                    "candidate_id": f"score32_zero_tail_two_pass_{scenario['name']}_{deployment}_iterdiv",
                    "family": "score32_zero_tail_two_pass_iterdiv",
                    "placement_scenario": scenario["name"],
                    "placement_efficiency": _float(scenario.get("placement_efficiency")),
                    "divider_deployment": deployment,
                    "divider_instances": instances,
                    "serial_head_groups": serial_head_groups,
                    "head_count": head_count,
                    "latency_us": round(latency_us, 12),
                    "source_frontier_latency_us": source_frontier_latency_us,
                    "score_sram_source_latency_us": sram_source_latency_us,
                    "score_sram_latency_delta_us": round(sram_latency_delta_us, 12),
                    "token_throughput_per_s": round(1_000_000.0 / latency_us, 12),
                    "energy_mj_per_token": round(total_energy_mj, 12),
                    "base_energy_mj_per_token": _float(source.get("energy_mj_per_token")),
                    "score_sram_energy_mj_per_token": score_sram_energy_mj,
                    "divider_energy_mj_per_token": round(divider_energy_mj, 12),
                    "compute_plus_service_logic_area_mm2": round(logic_area_mm2, 12),
                    "score_sram_macro_area_mm2": score_sram_macro_area_mm2,
                    "score_sram_envelope_area_mm2": round(
                        _float(scenario.get("score_buffer_envelope_area_um2")) / 1.0e6, 12
                    ),
                    "embodied_logic_plus_score_macro_area_mm2": round(
                        logic_area_mm2 + score_sram_macro_area_mm2, 12
                    ),
                    "die_area_mm2": _float(source.get("die_area_mm2")),
                    "shared_sram_capacity_mib": _float(scenario.get("shared_sram_capacity_mib")),
                    "hbm_byte_share": _float(scenario.get("hbm_byte_share")),
                    "divider_latency_us": round(divider_latency_us, 12),
                    "divider_critical_path_ns": iterdiv["critical_path_ns"],
                    "divider_meets_clock": iterdiv["critical_path_ns"] <= clock_ns,
                    "quality_status": quality_decision.get("status"),
                    "free_running_match_rate": quality.get("free_running_match_rate"),
                    "teacher_forced_nll_delta_mean": quality.get("teacher_forced_nll_delta_mean"),
                    "quality_backed": str(quality_decision.get("status", "")).endswith("_pass"),
                    "remaining_abstractions": ["hbm_dram_service", "sram_macro_floorplan_pnr"],
                }
            )

    latency_rank = sorted(rows, key=lambda row: (row["latency_us"], row["embodied_logic_plus_score_macro_area_mm2"]))
    area_rank = sorted(rows, key=lambda row: (row["embodied_logic_plus_score_macro_area_mm2"], row["latency_us"]))
    recommended = latency_rank[0]
    return {
        "version": 1,
        "model": "llm_decoder_attention_two_pass_integrated_frontier_ranking_v1",
        "decision": "two_pass_measured_components_integrated_frontier_ranked",
        "inputs": {
            "source_frontier_ranking_json": str(args.source_frontier_ranking_json),
            "score_sram_recost_json": str(args.score_sram_recost_json),
            "zero_tail_quality_json": str(args.zero_tail_quality_json),
            "iterdiv_ppa_json": str(args.iterdiv_ppa_json),
        },
        "iterdiv_metrics": iterdiv,
        "schedule": {
            "head_count": head_count,
            "divide_cycles_per_head": divide_cycles_per_head,
            "clock_ns": clock_ns,
            "per_head_divide_latency_us": per_head_latency_us,
            "note": "Each measured block normalizes one attention head with eight value lanes.",
        },
        "rows": rows,
        "latency_rank": latency_rank,
        "area_rank": area_rank,
        "diagnosis": {
            "recommended_candidate": recommended["candidate_id"],
            "recommended_latency_us": recommended["latency_us"],
            "recommended_token_throughput_per_s": recommended["token_throughput_per_s"],
            "minimum_area_candidate": area_rank[0]["candidate_id"],
            "shared_divider_latency_penalty_us": round(per_head_latency_us * (head_count - 1), 12),
            "per_head_divider_area_premium_mm2": round(
                iterdiv["area_um2"] * (head_count - 1) / 1.0e6, 12
            ),
            "quality_status": quality_decision.get("status"),
            "remaining_abstractions": ["hbm_dram_service", "sram_macro_floorplan_pnr"],
        },
        "assumptions": [
            "The source compute/controller row remains measured evidence; the two-pass service is added rather than silently replacing unseparated logic area.",
            "Only the score-SRAM recost latency delta is transferred onto the current controller-replay frontier, preserving measured controller overhead.",
            "Divider active energy is charged once per head, so sharing changes latency and area but not total divider work energy.",
            "The score SRAM macro area is reported separately from its placement envelope to avoid double counting the fixed die budget.",
            "HBM service and score-SRAM floorplan PNR remain explicit abstractions.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    d = payload["diagnosis"]
    lines = [
        "# Two-Pass Integrated Frontier Ranking",
        "",
        f"- decision: `{payload['decision']}`",
        f"- recommended candidate: `{d['recommended_candidate']}`",
        f"- recommended latency us: `{d['recommended_latency_us']}`",
        f"- minimum-area candidate: `{d['minimum_area_candidate']}`",
        f"- quality status: `{d['quality_status']}`",
        "",
        "| candidate | latency us | token/s | energy mJ/token | logic + score macro mm2 |",
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
    parser.add_argument("--source-frontier-ranking-json", type=Path, required=True)
    parser.add_argument("--score-sram-recost-json", type=Path, required=True)
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
