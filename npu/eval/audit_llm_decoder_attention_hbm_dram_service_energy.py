#!/usr/bin/env python3
"""Apply a lightweight HBM/DRAM command-service energy model to Llama7B attention rows."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_hbm_energy_sensitivity import (  # noqa: E402
    _candidate_id,
    _energy_row,
    _frontier_rows,
    _pareto,
    _with_score,
)
from npu.eval.audit_llm_decoder_attention_integrated_energy_closure import (  # noqa: E402
    _as_float,
    _energy_mj_from_pj,
    _load_json,
    _tokens_per_s,
    _traffic,
)


JsonDict = dict[str, Any]


def _best(payload: JsonDict) -> JsonDict:
    best = payload.get("best")
    return best if isinstance(best, dict) else {}


def _frontier_family_key(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}:"
        f"kv{int(_as_float(row.get('kv_bits')))}:"
        f"{row.get('kv_sharing', 'kv')}:"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def _controller_defaults(controller_payload: JsonDict) -> JsonDict:
    best = _best(controller_payload)
    return {
        "row_hit_rate": _as_float(best.get("row_hit_rate"), 0.9),
        "request_overhead_cycles": _as_float(best.get("request_overhead_cycles"), 4.0),
        "row_miss_penalty_cycles": _as_float(best.get("row_miss_penalty_cycles"), 16.0),
        "scheduler_efficiency": _as_float(best.get("scheduler_efficiency"), 0.9),
        "arbitration_efficiency": _as_float(best.get("arbitration_efficiency"), 0.85),
        "burst_bytes": _as_float(best.get("burst_bytes"), 1024.0),
        "hbm_outstanding": _as_float(best.get("hbm_outstanding"), 8.0),
    }


def _row_raw_hbm_bytes_per_cycle(row: JsonDict) -> float:
    raw = _as_float(row.get("raw_hbm_bytes_per_cycle"))
    if raw > 0.0:
        return raw
    effective = _as_float(row.get("effective_hbm_bytes_per_cycle"), _as_float(row.get("hbm_effective_bytes_per_cycle")))
    efficiency = _as_float(row.get("hbm_efficiency"))
    if effective > 0.0 and efficiency > 0.0:
        return effective / efficiency
    stack_count = max(1.0, _as_float(row.get("stack_count"), 8.0))
    pseudo_channels = max(1.0, _as_float(row.get("pseudo_channels_per_stack"), 16.0))
    pseudo_width_bits = max(1.0, _as_float(row.get("pseudo_channel_width_bits"), 64.0))
    data_rate_mtps = max(1.0, _as_float(row.get("data_rate_mtps"), 6400.0))
    clock_mhz = 1000.0 / max(1e-12, _as_float(row.get("clock_ns"), 1.0))
    return stack_count * pseudo_channels * (pseudo_width_bits / 8.0) * data_rate_mtps / clock_mhz


def _modeled_hbm_service(row: JsonDict, controller: JsonDict) -> JsonDict:
    row_hit_rate = min(1.0, max(0.0, _as_float(row.get("row_hit_rate"), controller["row_hit_rate"])))
    scheduler_efficiency = min(1.0, max(0.0, _as_float(row.get("scheduler_efficiency"), controller["scheduler_efficiency"])))
    arbitration_efficiency = min(1.0, max(0.0, _as_float(row.get("arbitration_efficiency"), controller["arbitration_efficiency"])))
    burst_bytes = max(1.0, _as_float(row.get("burst_bytes"), controller["burst_bytes"]))
    outstanding = max(1.0, _as_float(row.get("hbm_outstanding"), controller["hbm_outstanding"]))
    request_overhead_cycles = max(0.0, _as_float(row.get("request_overhead_cycles"), controller["request_overhead_cycles"]))
    row_miss_penalty_cycles = max(0.0, _as_float(row.get("row_miss_penalty_cycles"), controller["row_miss_penalty_cycles"]))
    raw_bytes_per_cycle = max(1e-12, _row_raw_hbm_bytes_per_cycle(row))
    sustained_bytes_per_cycle = raw_bytes_per_cycle * scheduler_efficiency * arbitration_efficiency
    payload_cycles = burst_bytes / max(1e-12, sustained_bytes_per_cycle)
    hidden_command_cycles = (request_overhead_cycles + (1.0 - row_hit_rate) * row_miss_penalty_cycles) / math.sqrt(outstanding)
    service_cycles_per_burst = payload_cycles + hidden_command_cycles
    modeled_effective_bytes_per_cycle = burst_bytes / max(1e-12, service_cycles_per_burst)
    modeled_hbm_efficiency = modeled_effective_bytes_per_cycle / raw_bytes_per_cycle
    original_effective = _as_float(row.get("effective_hbm_bytes_per_cycle"), _as_float(row.get("hbm_effective_bytes_per_cycle")))
    if original_effective <= 0.0:
        original_effective = raw_bytes_per_cycle * max(1e-12, _as_float(row.get("hbm_efficiency"), 1.0))
    return {
        "raw_hbm_bytes_per_cycle": raw_bytes_per_cycle,
        "modeled_effective_hbm_bytes_per_cycle": modeled_effective_bytes_per_cycle,
        "original_effective_hbm_bytes_per_cycle": original_effective,
        "modeled_hbm_efficiency": modeled_hbm_efficiency,
        "original_hbm_efficiency": _as_float(row.get("hbm_efficiency")),
        "row_hit_rate": row_hit_rate,
        "scheduler_efficiency": scheduler_efficiency,
        "arbitration_efficiency": arbitration_efficiency,
        "burst_bytes": burst_bytes,
        "hbm_outstanding": outstanding,
        "request_overhead_cycles": request_overhead_cycles,
        "row_miss_penalty_cycles": row_miss_penalty_cycles,
        "payload_cycles_per_burst": payload_cycles,
        "hidden_command_cycles_per_burst": hidden_command_cycles,
        "service_cycles_per_burst": service_cycles_per_burst,
    }


def _dram_energy_terms(
    *,
    row: JsonDict,
    service: JsonDict,
    read_hit_pj_per_byte: float,
    read_miss_pj_per_byte: float,
    write_pj_per_byte: float,
    activate_precharge_pj_per_row: float,
    command_pj_per_burst: float,
) -> JsonDict:
    traffic = _traffic(row)
    read_bytes = _as_float(traffic["hbm_read_bytes"])
    write_bytes = _as_float(traffic["kv_write_bytes"])
    row_hit_rate = _as_float(service["row_hit_rate"])
    hit_read_bytes = read_bytes * row_hit_rate
    miss_read_bytes = read_bytes - hit_read_bytes
    burst_bytes = max(1.0, _as_float(service["burst_bytes"]))
    row_bytes = burst_bytes
    burst_count = math.ceil((read_bytes + write_bytes) / burst_bytes)
    miss_row_count = math.ceil(miss_read_bytes / row_bytes)
    read_hit_pj = hit_read_bytes * read_hit_pj_per_byte
    read_miss_pj = miss_read_bytes * read_miss_pj_per_byte
    write_pj = write_bytes * write_pj_per_byte
    activate_precharge_pj = miss_row_count * activate_precharge_pj_per_row
    command_pj = burst_count * command_pj_per_burst
    total_pj = read_hit_pj + read_miss_pj + write_pj + activate_precharge_pj + command_pj
    return {
        "status": "hbm_dram_command_class_energy_model_not_signoff",
        "energy_mj": _energy_mj_from_pj(total_pj),
        "energy_pj": total_pj,
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
        "row_hit_read_bytes": hit_read_bytes,
        "row_miss_read_bytes": miss_read_bytes,
        "burst_count": burst_count,
        "miss_row_count": miss_row_count,
        "read_hit_pj": read_hit_pj,
        "read_miss_pj": read_miss_pj,
        "write_pj": write_pj,
        "activate_precharge_pj": activate_precharge_pj,
        "command_pj": command_pj,
        "read_hit_pj_per_byte": read_hit_pj_per_byte,
        "read_miss_pj_per_byte": read_miss_pj_per_byte,
        "write_pj_per_byte": write_pj_per_byte,
        "activate_precharge_pj_per_row": activate_precharge_pj_per_row,
        "command_pj_per_burst": command_pj_per_burst,
    }


def _service_adjusted_latency(row: JsonDict, service: JsonDict) -> JsonDict:
    latency_us = _as_float(row.get("latency_us"))
    if latency_us <= 0.0:
        return {"latency_us": latency_us, "service_latency_scale": 1.0, "hbm_latency_weight": 0.0}
    original = max(1e-12, _as_float(service["original_effective_hbm_bytes_per_cycle"]))
    modeled = max(1e-12, _as_float(service["modeled_effective_hbm_bytes_per_cycle"]))
    service_scale = original / modeled
    if str(row.get("dominant_tile_resource", "")) == "hbm":
        hbm_latency_weight = min(0.95, max(0.35, _as_float(row.get("hbm_byte_share"), 0.5)))
    else:
        hbm_latency_weight = min(0.65, max(0.1, _as_float(row.get("hbm_byte_share"), 0.25)))
    adjusted_latency_us = latency_us * ((1.0 - hbm_latency_weight) + hbm_latency_weight * service_scale)
    return {
        "latency_us": adjusted_latency_us,
        "base_latency_us": latency_us,
        "service_latency_scale": service_scale,
        "hbm_latency_weight": hbm_latency_weight,
    }


def _dram_modeled_row(
    *,
    row: JsonDict,
    integrated_energy: JsonDict,
    measured_compute: JsonDict,
    sram_profile: JsonDict,
    controller: JsonDict,
    args: argparse.Namespace,
) -> JsonDict:
    base = _energy_row(
        row=row,
        integrated_energy=integrated_energy,
        measured_compute=measured_compute,
        sram_profile=sram_profile,
        hbm_energy_pj_per_byte=0.0,
        noc_energy_pj_per_byte_hop=args.noc_energy_pj_per_byte_hop,
    )
    service = _modeled_hbm_service(row, controller)
    dram = _dram_energy_terms(
        row=row,
        service=service,
        read_hit_pj_per_byte=args.read_hit_pj_per_byte,
        read_miss_pj_per_byte=args.read_miss_pj_per_byte,
        write_pj_per_byte=args.write_pj_per_byte,
        activate_precharge_pj_per_row=args.activate_precharge_pj_per_row,
        command_pj_per_burst=args.command_pj_per_burst,
    )
    latency = _service_adjusted_latency(row, service)
    components = dict(base["energy_components"])
    components["hbm_mj"] = _as_float(dram["energy_mj"])
    total_energy_mj = sum(_as_float(value) for value in components.values())
    dominant_energy_component = max(components.items(), key=lambda item: _as_float(item[1]))[0].replace("_mj", "")
    out = {
        **base,
        "arch_id": "hbm_dram_service_energy_frontier",
        "latency_us": latency["latency_us"],
        "token_throughput_per_s": _tokens_per_s(latency["latency_us"]),
        "base_latency_us": latency["base_latency_us"],
        "service_latency_scale": latency["service_latency_scale"],
        "hbm_latency_weight": latency["hbm_latency_weight"],
        "energy_mj": total_energy_mj,
        "energy_status": "hbm_dram_command_service_energy_model_not_signoff",
        "dominant_energy_component": dominant_energy_component,
        "energy_components": components,
        "hbm_dram_service": service,
        "hbm_dram_energy": dram,
        "remaining_energy_abstractions": [
            "HBM service uses burst/row-hit/outstanding-request accounting, not a cycle-accurate DRAM controller RTL simulation.",
            "HBM energy is split by command class, but pJ values are explicit model parameters rather than vendor signoff currents.",
            "Compute energy is still scaled from the nearest measured dense compute reference.",
            "NoC/SRAM energy uses profile-scaled accounting from the integrated energy closure.",
        ],
    }
    return out


def build_payload(args: argparse.Namespace) -> JsonDict:
    integrated_energy = _load_json(args.integrated_energy_json)
    hbm_sensitivity = _load_json(args.hbm_energy_sensitivity_json)
    hbm_quality_backed = _load_json(args.hbm_quality_backed_json)
    measured_compute = _load_json(args.measured_compute_json)
    sram_profile = _load_json(args.sram_profile_json)
    hbm_controller = _load_json(args.hbm_controller_json)
    rows = _frontier_rows(hbm_quality_backed, args.frontier_row_limit)
    if not rows:
        raise RuntimeError("no retained HBM frontier rows found")
    controller = _controller_defaults(hbm_controller)
    modeled_rows = [
        _dram_modeled_row(
            row=row,
            integrated_energy=integrated_energy,
            measured_compute=measured_compute,
            sram_profile=sram_profile,
            controller=controller,
            args=args,
        )
        for row in rows
    ]
    latency_best = min(modeled_rows, key=lambda item: (_as_float(item["latency_us"]), _as_float(item["energy_mj"])))
    energy_best = min(modeled_rows, key=lambda item: (_as_float(item["energy_mj"]), _as_float(item["latency_us"])))
    balanced_best = min(
        _with_score(modeled_rows, latency_best),
        key=lambda item: (
            _as_float(item["unit_weight_latency_energy_area_score"]),
            _as_float(item["latency_us"]),
        ),
    )
    pareto_rows = _pareto(modeled_rows)[: args.pareto_row_limit]
    previous_best = _best(hbm_sensitivity)
    previous_candidate_id = str(previous_best.get("candidate_id", ""))
    energy_candidate_id = str(energy_best.get("candidate_id", ""))
    previous_family = _frontier_family_key(previous_best)
    energy_family = _frontier_family_key(energy_best)
    energy_frontier_changed = previous_family != energy_family
    energy_variant_changed = bool(previous_candidate_id and previous_candidate_id != energy_candidate_id)
    service_slowdown_vs_sensitivity = _as_float(latency_best["latency_us"]) / max(
        1e-12,
        _as_float((hbm_sensitivity.get("latency_best_at_nominal") or {}).get("latency_us")),
    )
    decision = (
        "hbm_dram_service_energy_changes_energy_frontier"
        if energy_frontier_changed
        else "hbm_dram_service_energy_preserves_energy_frontier"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_hbm_dram_service_energy_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "previous_hbm_sensitivity_energy_best": previous_candidate_id,
            "hbm_dram_energy_best": energy_candidate_id,
            "previous_hbm_sensitivity_energy_family": previous_family,
            "hbm_dram_energy_family": energy_family,
            "energy_frontier_changed_vs_hbm_sensitivity": energy_frontier_changed,
            "energy_variant_changed_vs_hbm_sensitivity": energy_variant_changed,
            "service_slowdown_vs_hbm_sensitivity_latency_best": service_slowdown_vs_sensitivity,
            "recommended_next_step": (
                "directly measure the selected compute service point and replace DRAM pJ parameters with sourced HBM stack currents"
            ),
        },
        "best": {
            **energy_best,
            "arch_id": "hbm_dram_service_energy_best",
        },
        "latency_best_under_dram_model": latency_best,
        "balanced_best_under_dram_model": balanced_best,
        "pareto_rows": pareto_rows,
        "input_row_count": len(rows),
        "dram_model_parameters": {
            "read_hit_pj_per_byte": args.read_hit_pj_per_byte,
            "read_miss_pj_per_byte": args.read_miss_pj_per_byte,
            "write_pj_per_byte": args.write_pj_per_byte,
            "activate_precharge_pj_per_row": args.activate_precharge_pj_per_row,
            "command_pj_per_burst": args.command_pj_per_burst,
            "noc_energy_pj_per_byte_hop": args.noc_energy_pj_per_byte_hop,
            "controller_defaults": controller,
        },
        "remaining_abstractions": [
            "HBM/DRAM service is now command-class and row-hit aware, but still not a cycle-accurate controller simulation.",
            "HBM/DRAM energy parameters are explicit pJ values; they need source-backed stack-current calibration before final energy claims.",
            "Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.",
            "NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.",
        ],
        "source_artifacts": {
            "integrated_energy_model": integrated_energy.get("model"),
            "hbm_energy_sensitivity_model": hbm_sensitivity.get("model"),
            "hbm_quality_backed_model": hbm_quality_backed.get("model"),
            "hbm_controller_model": hbm_controller.get("model"),
            "measured_compute_model": measured_compute.get("model"),
            "sram_profile_model": sram_profile.get("model"),
        },
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    latency_best = payload["latency_best_under_dram_model"]
    balanced_best = payload["balanced_best_under_dram_model"]
    lines = [
        "# Llama7B HBM/DRAM Service Energy",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- previous_hbm_sensitivity_energy_best: `{payload['diagnosis']['previous_hbm_sensitivity_energy_best']}`",
        f"- hbm_dram_energy_best: `{payload['diagnosis']['hbm_dram_energy_best']}`",
        f"- service_slowdown_vs_hbm_sensitivity_latency_best: `{payload['diagnosis']['service_slowdown_vs_hbm_sensitivity_latency_best']}`",
        "",
        "## Best Points",
        "",
        "| role | candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for role, row in (("latency", latency_best), ("energy", best), ("balanced", balanced_best)):
        lines.append(
            "| {role} | {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {dominant_energy_component} |".format(
                role=role,
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## DRAM Model Parameters",
            "",
            "| parameter | value |",
            "|---|---:|",
        ]
    )
    for key, value in payload["dram_model_parameters"].items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Pareto Rows", "", "| candidate | latency us | energy mJ | area mm2 | service scale |", "|---|---:|---:|---:|---:|"])
    for row in payload["pareto_rows"]:
        lines.append(
            "| {candidate_id} | {latency_us} | {energy_mj} | {die_area_mm2} | {service_latency_scale} |".format(
                **row
            )
        )
    lines.extend(["", "## Remaining Abstractions"])
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrated-energy-json", type=Path, required=True)
    parser.add_argument("--hbm-energy-sensitivity-json", type=Path, required=True)
    parser.add_argument("--hbm-quality-backed-json", type=Path, required=True)
    parser.add_argument("--hbm-controller-json", type=Path, required=True)
    parser.add_argument("--measured-compute-json", type=Path, required=True)
    parser.add_argument("--sram-profile-json", type=Path, required=True)
    parser.add_argument("--read-hit-pj-per-byte", type=float, default=4.0)
    parser.add_argument("--read-miss-pj-per-byte", type=float, default=10.0)
    parser.add_argument("--write-pj-per-byte", type=float, default=6.0)
    parser.add_argument("--activate-precharge-pj-per-row", type=float, default=3000.0)
    parser.add_argument("--command-pj-per-burst", type=float, default=5.0)
    parser.add_argument("--noc-energy-pj-per-byte-hop", type=float, default=0.02)
    parser.add_argument("--frontier-row-limit", type=int, default=96)
    parser.add_argument("--pareto-row-limit", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
