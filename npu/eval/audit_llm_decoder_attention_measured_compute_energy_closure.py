#!/usr/bin/env python3
"""Re-rank Llama7B attention with measured dense-compute capacity and calibrated HBM energy."""

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

from npu.eval.audit_llm_decoder_attention_integrated_energy_closure import (  # noqa: E402
    _as_float,
    _energy_mj_from_pj,
    _energy_mj_from_power,
    _load_json,
    _sram_energy_terms,
    _tokens_per_s,
    _traffic,
)

JsonDict = dict[str, Any]


def _candidate_id(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}_"
        f"{row.get('compute_arch', 'compute')}_"
        f"mac{int(_as_float(row.get('macs_per_cycle')))}_"
        f"lat{_as_float(row.get('latency_us')):g}_"
        f"hbm{_as_float(row.get('hbm_byte_share')):.6f}_"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def _frontier_family(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}:"
        f"kv{int(_as_float(row.get('kv_bits')))}:"
        f"{row.get('kv_sharing', 'kv')}:"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def _measured_rows(measured_compute: JsonDict, limit: int) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for key in ("best", "top_rows", "best_by_die", "best_by_die_sram_logic", "best_by_compute_arch"):
        value = measured_compute.get(key)
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    deduped: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        if _as_float(row.get("latency_us")) <= 0.0:
            continue
        if _as_float(row.get("macs_per_cycle")) <= 0.0:
            continue
        cid = _candidate_id(row)
        if cid in seen:
            continue
        seen.add(cid)
        deduped.append(row)
    deduped.sort(
        key=lambda row: (
            _as_float(row.get("latency_us")),
            _as_float(row.get("die_area_mm2")),
            -_as_float(row.get("macs_per_cycle")),
        )
    )
    return deduped[:limit]


def _compute_candidates(measured_compute: JsonDict) -> list[JsonDict]:
    candidates: list[JsonDict] = []
    for row in measured_compute.get("compute_candidates", []):
        if not isinstance(row, dict):
            continue
        macs = _as_float(row.get("block_macs_per_cycle"))
        area = _as_float(row.get("block_area_um2"))
        power = _as_float(row.get("block_power_mw"))
        if macs <= 0.0 or area <= 0.0 or power <= 0.0:
            continue
        out = dict(row)
        out["macs_per_mm2"] = macs / (area / 1_000_000.0)
        out["mw_per_mac_per_cycle"] = power / macs
        candidates.append(out)
    return candidates


def _best_density_candidate(candidates: list[JsonDict]) -> JsonDict:
    if not candidates:
        raise RuntimeError("no measured compute candidates found")
    return max(candidates, key=lambda row: (_as_float(row.get("macs_per_mm2")), -_as_float(row.get("block_clock_ns"))))


def _abstract_compute_feasibility(command_calibrated: JsonDict, measured_compute: JsonDict) -> JsonDict:
    best = command_calibrated.get("best") if isinstance(command_calibrated.get("best"), dict) else {}
    target_macs = _as_float(best.get("macs_per_cycle"))
    die_area_mm2 = _as_float(best.get("die_area_mm2"))
    candidates = _compute_candidates(measured_compute)
    density_best = _best_density_candidate(candidates)
    block_macs = _as_float(density_best.get("block_macs_per_cycle"))
    block_area_um2 = _as_float(density_best.get("block_area_um2"))
    block_power_mw = _as_float(density_best.get("block_power_mw"))
    replicas_required = math.ceil(target_macs / max(1.0, block_macs)) if target_macs > 0.0 else 0
    required_area_mm2 = replicas_required * block_area_um2 / 1_000_000.0
    required_power_mw = replicas_required * block_power_mw
    return {
        "abstract_candidate_id": best.get("candidate_id") or best.get("source_candidate_id"),
        "target_macs_per_cycle": target_macs,
        "die_area_mm2": die_area_mm2,
        "best_measured_compute_arch": density_best.get("compute_arch"),
        "best_measured_block_macs_per_cycle": block_macs,
        "best_measured_block_area_um2": block_area_um2,
        "best_measured_block_power_mw": block_power_mw,
        "best_measured_macs_per_mm2": density_best.get("macs_per_mm2"),
        "replicas_required": replicas_required,
        "required_compute_area_mm2": required_area_mm2,
        "required_compute_power_mw": required_power_mw,
        "required_compute_area_over_die": required_area_mm2 / die_area_mm2 if die_area_mm2 > 0.0 else None,
        "fits_selected_die_if_compute_only": required_area_mm2 <= die_area_mm2,
        "status": (
            "abstract_compute_target_exceeds_measured_dense_tile_area"
            if required_area_mm2 > die_area_mm2
            else "abstract_compute_target_fits_measured_dense_tile_area"
        ),
    }


def _controller_defaults(command_calibrated: JsonDict) -> JsonDict:
    best = command_calibrated.get("best") if isinstance(command_calibrated.get("best"), dict) else {}
    service = best.get("hbm_dram_service") if isinstance(best.get("hbm_dram_service"), dict) else {}
    return {
        "row_hit_rate": _as_float(service.get("row_hit_rate"), 0.9),
        "request_overhead_cycles": _as_float(service.get("request_overhead_cycles"), 4.0),
        "row_miss_penalty_cycles": _as_float(service.get("row_miss_penalty_cycles"), 16.0),
        "scheduler_efficiency": _as_float(service.get("scheduler_efficiency"), 0.9),
        "arbitration_efficiency": _as_float(service.get("arbitration_efficiency"), 0.85),
        "burst_bytes": _as_float(service.get("burst_bytes"), 1024.0),
        "hbm_outstanding": _as_float(service.get("hbm_outstanding"), 8.0),
    }


def _raw_hbm_bytes_per_cycle(row: JsonDict) -> float:
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


def _service_adjusted_latency(row: JsonDict, controller: JsonDict) -> JsonDict:
    base_latency_us = _as_float(row.get("latency_us"))
    raw = max(1e-12, _raw_hbm_bytes_per_cycle(row))
    original_effective = _as_float(row.get("effective_hbm_bytes_per_cycle"), _as_float(row.get("hbm_effective_bytes_per_cycle")))
    if original_effective <= 0.0:
        original_effective = raw * max(1e-12, _as_float(row.get("hbm_efficiency"), 1.0))
    burst_bytes = max(1.0, _as_float(controller["burst_bytes"]))
    sustained = raw * max(1e-12, _as_float(controller["scheduler_efficiency"])) * max(
        1e-12,
        _as_float(controller["arbitration_efficiency"]),
    )
    payload_cycles = burst_bytes / max(1e-12, sustained)
    row_hit_rate = min(1.0, max(0.0, _as_float(controller["row_hit_rate"])))
    hidden_cycles = (
        _as_float(controller["request_overhead_cycles"])
        + (1.0 - row_hit_rate) * _as_float(controller["row_miss_penalty_cycles"])
    ) / math.sqrt(max(1.0, _as_float(controller["hbm_outstanding"])))
    modeled_effective = burst_bytes / max(1e-12, payload_cycles + hidden_cycles)
    service_scale = original_effective / max(1e-12, modeled_effective)
    if str(row.get("dominant_tile_resource", "")) == "hbm":
        hbm_latency_weight = min(0.95, max(0.35, _as_float(row.get("hbm_byte_share"), 0.5)))
    else:
        hbm_latency_weight = min(0.65, max(0.1, _as_float(row.get("hbm_byte_share"), 0.25)))
    latency_us = base_latency_us * ((1.0 - hbm_latency_weight) + hbm_latency_weight * service_scale)
    return {
        "base_latency_us": base_latency_us,
        "latency_us": latency_us,
        "service_latency_scale": service_scale,
        "hbm_latency_weight": hbm_latency_weight,
        "modeled_effective_hbm_bytes_per_cycle": modeled_effective,
        "original_effective_hbm_bytes_per_cycle": original_effective,
        "payload_cycles_per_burst": payload_cycles,
        "hidden_command_cycles_per_burst": hidden_cycles,
    }


def _hbm_energy_pj_per_byte(command_calibrated: JsonDict) -> float:
    calibration = command_calibrated.get("command_energy_calibration")
    if isinstance(calibration, dict):
        value = _as_float(calibration.get("source_hbm_energy_pj_per_byte"))
        if value > 0.0:
            return value
    best = command_calibrated.get("best") if isinstance(command_calibrated.get("best"), dict) else {}
    hbm = best.get("hbm_command_calibrated_energy") if isinstance(best.get("hbm_command_calibrated_energy"), dict) else {}
    read_bytes = _as_float(hbm.get("read_bytes")) + _as_float(hbm.get("write_bytes"))
    if read_bytes > 0.0:
        return _as_float(hbm.get("energy_pj")) / read_bytes
    return 31.76


def _energy_row(row: JsonDict, command_calibrated: JsonDict, sram_profile: JsonDict, controller: JsonDict) -> JsonDict:
    latency = _service_adjusted_latency(row, controller)
    traffic = _traffic(row)
    hbm_pj_per_byte = _hbm_energy_pj_per_byte(command_calibrated)
    hbm_energy_pj = (
        _as_float(traffic.get("hbm_read_bytes")) + _as_float(traffic.get("kv_write_bytes"))
    ) * hbm_pj_per_byte
    sram = _sram_energy_terms(sram_profile, traffic)
    noc_hops = _as_float(row.get("noc_hops"), 1.0)
    noc_bytes = _as_float(traffic.get("estimated_noc_payload_bytes"))
    noc_energy_pj = noc_bytes * noc_hops * 0.02
    compute_power_mw = _as_float(row.get("compute_power_mw"))
    compute_active_latency_us = _as_float(row.get("latency_us"))
    compute_energy_mj = _energy_mj_from_power(compute_power_mw, compute_active_latency_us)
    compute_wall_time_energy_mj = _energy_mj_from_power(compute_power_mw, latency["latency_us"])
    components = {
        "compute_mj": compute_energy_mj,
        "hbm_mj": _energy_mj_from_pj(hbm_energy_pj),
        "noc_mj": _energy_mj_from_pj(noc_energy_pj),
        "sram_mj": _as_float(sram.get("energy_mj")),
    }
    total = sum(_as_float(value) for value in components.values())
    dominant = max(components.items(), key=lambda item: _as_float(item[1]))[0].replace("_mj", "")
    out = {
        **row,
        "candidate_id": _candidate_id(row),
        "arch_id": "measured_compute_hbm_calibrated_frontier",
        "latency_us": latency["latency_us"],
        "token_throughput_per_s": _tokens_per_s(latency["latency_us"]),
        "base_latency_us": latency["base_latency_us"],
        "energy_mj": total,
        "energy_status": "measured_dense_tile_compute_power_clock_gated_with_source_hbm_energy",
        "dominant_energy_component": dominant,
        "energy_components": components,
        "measured_compute_energy": {
            "status": "measured_dense_tile_power_replicated_to_row_capacity",
            "compute_power_mw": compute_power_mw,
            "compute_active_latency_us": compute_active_latency_us,
            "wall_latency_us": latency["latency_us"],
            "energy_mj": compute_energy_mj,
            "wall_time_power_energy_upper_bound_mj": compute_wall_time_energy_mj,
            "compute_arch": row.get("compute_arch"),
            "compute_replica_count": row.get("compute_replica_count"),
            "macs_per_cycle": row.get("macs_per_cycle"),
            "compute_area_um2": row.get("compute_area_um2"),
            "metrics_csv": row.get("metrics_csv"),
            "metrics_tag": row.get("metrics_tag"),
            "metrics_param_hash": row.get("metrics_param_hash"),
        },
        "hbm_energy": {
            "status": "source_backed_aggregate_hbm_energy",
            "energy_pj_per_byte": hbm_pj_per_byte,
            "read_bytes": traffic.get("hbm_read_bytes"),
            "write_bytes": traffic.get("kv_write_bytes"),
            "energy_mj": _energy_mj_from_pj(hbm_energy_pj),
        },
        "hbm_service": latency,
        "sram_energy": sram,
        "noc_energy": {
            "status": "profile_payload_byte_hop",
            "payload_bytes": noc_bytes,
            "hops": noc_hops,
            "energy_pj_per_byte_hop": 0.02,
            "energy_mj": _energy_mj_from_pj(noc_energy_pj),
        },
    }
    return out


def _pareto(rows: list[JsonDict]) -> list[JsonDict]:
    frontier: list[JsonDict] = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            no_worse = (
                _as_float(other.get("latency_us")) <= _as_float(row.get("latency_us"))
                and _as_float(other.get("energy_mj")) <= _as_float(row.get("energy_mj"))
                and _as_float(other.get("die_area_mm2")) <= _as_float(row.get("die_area_mm2"))
            )
            better = (
                _as_float(other.get("latency_us")) < _as_float(row.get("latency_us"))
                or _as_float(other.get("energy_mj")) < _as_float(row.get("energy_mj"))
                or _as_float(other.get("die_area_mm2")) < _as_float(row.get("die_area_mm2"))
            )
            if no_worse and better:
                dominated = True
                break
        if not dominated:
            frontier.append(row)
    return sorted(frontier, key=lambda item: (_as_float(item.get("latency_us")), _as_float(item.get("energy_mj"))))


def build_payload(args: argparse.Namespace) -> JsonDict:
    command_calibrated = _load_json(args.hbm_command_calibrated_service_json)
    measured_compute = _load_json(args.measured_compute_json)
    sram_profile = _load_json(args.sram_profile_json)
    source_rows = _measured_rows(measured_compute, args.row_limit)
    if not source_rows:
        raise RuntimeError("no measured compute rows found")
    controller = _controller_defaults(command_calibrated)
    modeled_rows = [_energy_row(row, command_calibrated, sram_profile, controller) for row in source_rows]
    latency_best = min(modeled_rows, key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"])))
    energy_best = min(modeled_rows, key=lambda row: (_as_float(row["energy_mj"]), _as_float(row["latency_us"])))
    pareto_rows = _pareto(modeled_rows)
    previous_best = command_calibrated.get("best") if isinstance(command_calibrated.get("best"), dict) else {}
    previous_family = _frontier_family(previous_best)
    measured_family = _frontier_family(energy_best)
    feasibility = _abstract_compute_feasibility(command_calibrated, measured_compute)
    frontier_changed = previous_family != measured_family
    abstract_infeasible = not bool(feasibility.get("fits_selected_die_if_compute_only"))
    decision = (
        "measured_compute_constraints_replace_abstract_frontier"
        if abstract_infeasible or frontier_changed
        else "measured_compute_constraints_preserve_frontier"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_measured_compute_energy_closure_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "previous_hbm_command_calibrated_best": previous_best.get("candidate_id") or previous_best.get("source_candidate_id"),
            "measured_compute_energy_best": energy_best["candidate_id"],
            "previous_energy_family": previous_family,
            "measured_energy_family": measured_family,
            "energy_family_changed_vs_hbm_command_calibrated": frontier_changed,
            "abstract_compute_target_infeasible_at_measured_tile_density": abstract_infeasible,
            "recommended_next_step": (
                "Use the measured-compute-constrained frontier for the next architecture decision; "
                "then either measure a larger integrated compute macro or explore denser/lower-precision compute."
            ),
        },
        "best": {
            **energy_best,
            "arch_id": "measured_compute_energy_closure_best",
        },
        "latency_best": latency_best,
        "pareto_rows": pareto_rows[: args.pareto_row_limit],
        "input_row_count": len(source_rows),
        "abstract_compute_feasibility": feasibility,
        "controller_defaults": controller,
        "remaining_abstractions": [
            "Compute power is measured per dense tile and replicated to measured-compute capacity rows, not measured as one full integrated 400-1200 mm2 macro.",
            "Compute energy ranking assumes compute lanes can be clock gated during added HBM command-service stalls; wall-time compute-power energy is reported as an upper bound.",
            "HBM energy uses source-backed aggregate pJ/byte and the existing command-service latency model, not vendor stack-current signoff.",
            "NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.",
            "Quality remains native-GQA KV8 backed; KV4/MQA remain excluded until recovery evidence is sufficient.",
        ],
        "source_artifacts": {
            "hbm_command_calibrated_service_model": command_calibrated.get("model"),
            "measured_compute_model": measured_compute.get("model"),
            "sram_profile_model": sram_profile.get("model"),
        },
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    feasibility = payload["abstract_compute_feasibility"]
    lines = [
        "# Llama7B Measured Compute Energy Closure",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- abstract_compute_target_infeasible: `{payload['diagnosis']['abstract_compute_target_infeasible_at_measured_tile_density']}`",
        f"- previous_energy_family: `{payload['diagnosis']['previous_energy_family']}`",
        f"- measured_energy_family: `{payload['diagnosis']['measured_energy_family']}`",
        "",
        "## Abstract Compute Feasibility",
        "",
        f"- target_macs_per_cycle: `{feasibility['target_macs_per_cycle']}`",
        f"- required_compute_area_mm2: `{feasibility['required_compute_area_mm2']}`",
        f"- selected_die_area_mm2: `{feasibility['die_area_mm2']}`",
        f"- required_compute_area_over_die: `{feasibility['required_compute_area_over_die']}`",
        "",
        "## Best Measured-Compute-Constrained Point",
        "",
        "| candidate | latency us | throughput tok/s | energy mJ | area mm2 | MAC/cyc | compute mJ | HBM mJ | dominant |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {macs_per_cycle} | {compute_mj} | {hbm_mj} | {dominant_energy_component} |".format(
            candidate_id=best["candidate_id"],
            latency_us=best["latency_us"],
            token_throughput_per_s=best["token_throughput_per_s"],
            energy_mj=best["energy_mj"],
            die_area_mm2=best["die_area_mm2"],
            macs_per_cycle=best["macs_per_cycle"],
            compute_mj=best["energy_components"]["compute_mj"],
            hbm_mj=best["energy_components"]["hbm_mj"],
            dominant_energy_component=best["dominant_energy_component"],
        ),
        "",
        "## Pareto Rows",
        "",
        "| candidate | latency us | energy mJ | area mm2 | MAC/cyc | dominant |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["pareto_rows"]:
        lines.append(
            "| {candidate_id} | {latency_us} | {energy_mj} | {die_area_mm2} | {macs_per_cycle} | {dominant_energy_component} |".format(
                **row
            )
        )
    lines.extend(["", "## Remaining Abstractions"])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hbm-command-calibrated-service-json", type=Path, required=True)
    parser.add_argument("--measured-compute-json", type=Path, required=True)
    parser.add_argument("--sram-profile-json", type=Path, required=True)
    parser.add_argument("--row-limit", type=int, default=256)
    parser.add_argument("--pareto-row-limit", type=int, default=24)
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
