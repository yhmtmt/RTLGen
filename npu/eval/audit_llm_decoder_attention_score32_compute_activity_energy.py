#!/usr/bin/env python3
"""Bound score32 exp-LUT compute energy by explicit active-cycle accounting."""

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


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_ratio(num: float, den: float) -> float:
    return num / den if den else 0.0


def _measured_fp16_energy_reference(integrated_ranking: JsonDict) -> JsonDict:
    for row in integrated_ranking.get("promotable_energy_rank") or []:
        if isinstance(row, dict) and row.get("family") == "measured_exact_fp16_gqa8_kv8":
            return dict(row)
    for row in integrated_ranking.get("rows") or []:
        if isinstance(row, dict) and row.get("family") == "measured_exact_fp16_gqa8_kv8":
            return dict(row)
    return {}


def build_report(args: argparse.Namespace) -> JsonDict:
    score32_hbm = _load_json(args.score32_hbm_dram_service_json)
    measured_command = _load_json(args.score32_measured_command_control_json)
    integrated_ranking = _load_json(args.score32_integrated_frontier_ranking_json)

    score32 = _as_dict(score32_hbm.get("best_latency"))
    command_row = _as_dict(measured_command.get("best_requested"))
    fp16_ref = _measured_fp16_energy_reference(integrated_ranking)

    tile_service_cycles = _as_int(
        command_row.get("replica_recost_tile_service_cycles") or command_row.get("tile_service_cycles"), 1
    )
    layer_cycles = _as_int(command_row.get("replica_recost_layer_cycles") or command_row.get("layer_cycles"), 1)
    tile_waves = _as_int(command_row.get("tile_waves"), 1)
    layers = _as_int(command_row.get("layers"), 32)
    active_cycles_per_layer = tile_service_cycles * tile_waves
    active_cycles_total = active_cycles_per_layer * layers
    layer_cycles_total = layer_cycles * layers
    compute_active_duty = min(1.0, _safe_ratio(active_cycles_per_layer, layer_cycles))

    wall_latency_us = _as_float(score32.get("latency_us"))
    compute_power_mw = _as_float(score32.get("compute_power_mw"))
    wall_compute_energy_mj = _as_float(score32.get("compute_energy_mj_per_token"))
    hbm_energy_mj = _as_float(score32.get("hbm_energy_mj_per_token"))
    active_compute_energy_mj = wall_compute_energy_mj * compute_active_duty
    idle_compute_energy_mj = max(0.0, wall_compute_energy_mj - active_compute_energy_mj)

    rows: list[JsonDict] = []
    for idle_power_fraction in args.idle_power_fraction:
        idle_energy_mj = idle_compute_energy_mj * idle_power_fraction
        compute_energy_mj = active_compute_energy_mj + idle_energy_mj
        total_energy_mj = compute_energy_mj + hbm_energy_mj
        rows.append(
            {
                "scenario": f"idle_power_fraction_{idle_power_fraction:g}",
                "idle_power_fraction": idle_power_fraction,
                "latency_us": wall_latency_us,
                "token_throughput_per_s": _as_float(score32.get("token_throughput_per_s")),
                "compute_power_mw": compute_power_mw,
                "compute_active_duty": round(compute_active_duty, 9),
                "active_cycles_per_layer": active_cycles_per_layer,
                "layer_cycles": layer_cycles,
                "active_cycles_total": active_cycles_total,
                "layer_cycles_total": layer_cycles_total,
                "wall_compute_energy_mj_per_token": round(wall_compute_energy_mj, 9),
                "active_compute_energy_mj_per_token": round(active_compute_energy_mj, 9),
                "idle_compute_energy_mj_per_token": round(idle_energy_mj, 9),
                "clock_gated_compute_energy_mj_per_token": round(compute_energy_mj, 9),
                "hbm_energy_mj_per_token": round(hbm_energy_mj, 9),
                "total_energy_mj_per_token": round(total_energy_mj, 9),
                "energy_reduction_vs_wall_time": round(wall_compute_energy_mj + hbm_energy_mj - total_energy_mj, 9),
                "energy_reduction_fraction_vs_wall_time": round(
                    _safe_ratio(wall_compute_energy_mj + hbm_energy_mj - total_energy_mj, wall_compute_energy_mj + hbm_energy_mj),
                    9,
                ),
            }
        )

    best_clock_gated = min(rows, key=lambda row: _as_float(row["total_energy_mj_per_token"]))
    fp16_energy = _as_float(fp16_ref.get("energy_mj_per_token"))
    fp16_throughput = _as_float(fp16_ref.get("token_throughput_per_s"))
    still_energy_worse = bool(fp16_energy and best_clock_gated["total_energy_mj_per_token"] > fp16_energy)
    decision = (
        "score32_compute_activity_energy_still_energy_worse"
        if still_energy_worse
        else "score32_compute_activity_energy_can_match_energy_reference"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_compute_activity_energy_v1",
        "decision": decision,
        "inputs": {
            "score32_hbm_dram_service_json": str(args.score32_hbm_dram_service_json),
            "score32_measured_command_control_json": str(args.score32_measured_command_control_json),
            "score32_integrated_frontier_ranking_json": str(args.score32_integrated_frontier_ranking_json),
        },
        "diagnosis": {
            "decision": decision,
            "compute_active_duty": round(compute_active_duty, 9),
            "active_cycles_per_layer": active_cycles_per_layer,
            "layer_cycles": layer_cycles,
            "wall_time_compute_energy_mj_per_token": round(wall_compute_energy_mj, 9),
            "best_clock_gated_compute_energy_mj_per_token": best_clock_gated["clock_gated_compute_energy_mj_per_token"],
            "best_clock_gated_total_energy_mj_per_token": best_clock_gated["total_energy_mj_per_token"],
            "wall_time_total_energy_mj_per_token": round(wall_compute_energy_mj + hbm_energy_mj, 9),
            "energy_reduction_fraction_vs_wall_time": best_clock_gated["energy_reduction_fraction_vs_wall_time"],
            "score32_latency_us": wall_latency_us,
            "score32_token_throughput_per_s": _as_float(score32.get("token_throughput_per_s")),
            "measured_fp16_energy_reference_mj_per_token": fp16_energy,
            "measured_fp16_token_throughput_per_s": fp16_throughput,
            "clock_gated_score32_vs_measured_fp16_energy_ratio": round(
                _safe_ratio(best_clock_gated["total_energy_mj_per_token"], fp16_energy), 9
            ),
            "clock_gated_score32_vs_measured_fp16_throughput_ratio": round(
                _safe_ratio(_as_float(score32.get("token_throughput_per_s")), fp16_throughput), 9
            ),
            "recommended_next_step": (
                "Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax "
                "datapath variants or quality-close a lower-energy mixed/int8 path."
                if still_energy_worse
                else "Clock-gated score32 can match the measured-FP16 energy reference; carry this energy model into ranking."
            ),
            "remaining_abstractions": [
                "compute active duty is derived from L2 cycle accounting, not RTL toggle activity",
                "idle power fractions are analytic clock-gating scenarios, not gate-level power simulation",
            ],
        },
        "best_clock_gated": best_clock_gated,
        "rows": rows,
        "measured_fp16_energy_reference": fp16_ref,
        "assumptions": [
            "Score32 compute power is inherited from measured dual-stream composed PPA and measured command-control recost.",
            "Active compute cycles use replica_recost_tile_service_cycles * tile_waves per layer.",
            "Idle energy is swept as a fraction of the non-active wall-time compute-energy remainder.",
            "HBM energy is unchanged from the score32 HBM/DRAM service closure.",
        ],
        "next_step": {
            "recommended_next_step": (
                "Explore score32 datapath energy reduction and lower-power quality-backed mixed/int8 variants; "
                "clock gating alone is a small correction because the active duty is high."
            ),
            "requires_score32_datapath_energy_optimization": still_energy_worse,
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    d = payload["diagnosis"]
    lines = [
        "# Score32 Compute Activity Energy",
        "",
        f"- decision: `{payload['decision']}`",
        f"- compute active duty: `{d['compute_active_duty']}`",
        f"- wall-time compute energy mJ/token: `{d['wall_time_compute_energy_mj_per_token']}`",
        f"- best clock-gated compute energy mJ/token: `{d['best_clock_gated_compute_energy_mj_per_token']}`",
        f"- best clock-gated total energy mJ/token: `{d['best_clock_gated_total_energy_mj_per_token']}`",
        f"- measured-FP16 energy reference mJ/token: `{d['measured_fp16_energy_reference_mj_per_token']}`",
        f"- clock-gated score32 / measured-FP16 energy ratio: `{d['clock_gated_score32_vs_measured_fp16_energy_ratio']}`",
        "",
        "## Scenarios",
        "",
        "| idle power fraction | compute mJ | total mJ | reduction vs wall |",
        "|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {idle_power_fraction} | {clock_gated_compute_energy_mj_per_token} | "
            "{total_energy_mj_per_token} | {energy_reduction_fraction_vs_wall_time} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _idle_power_fractions(value: str) -> list[float]:
    fractions = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not fractions or any(item < 0.0 or item > 1.0 for item in fractions):
        raise argparse.ArgumentTypeError("expected comma-separated fractions in [0,1]")
    return fractions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score32-hbm-dram-service-json", type=Path, required=True)
    parser.add_argument("--score32-measured-command-control-json", type=Path, required=True)
    parser.add_argument("--score32-integrated-frontier-ranking-json", type=Path, required=True)
    parser.add_argument("--idle-power-fraction", type=_idle_power_fractions, default=[0.0, 0.05, 0.1, 0.25, 1.0])
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
