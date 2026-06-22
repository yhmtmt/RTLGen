#!/usr/bin/env python3
"""Calibrate HBM command-class service energy to source-backed aggregate HBM energy."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _float_list(text: str) -> list[float]:
    values = [float(part.strip()) for part in text.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("list must contain at least one value")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("row-hit rates must be in [0, 1]")
    return values


def _tokens_per_s(latency_us: float) -> float:
    return 1_000_000.0 / latency_us if latency_us > 0.0 else 0.0


def _candidate_id(row: JsonDict) -> str:
    return str(row.get("candidate_id") or row.get("source_candidate_id") or row.get("arch_id") or "unknown")


def _frontier_family(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}:"
        f"kv{int(_as_float(row.get('kv_bits')))}:"
        f"{row.get('kv_sharing', 'kv')}:"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def _source_rows(hbm_dram_service: JsonDict) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for key in ("best", "latency_best_under_dram_model", "balanced_best_under_dram_model"):
        value = hbm_dram_service.get(key)
        if isinstance(value, dict):
            rows.append(value)
    for value in hbm_dram_service.get("pareto_rows", []):
        if isinstance(value, dict):
            rows.append(value)
    deduped: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        candidate = _candidate_id(row)
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(row)
    return deduped


def _primary_ref(hbm_energy_calibration: JsonDict, measurement_id: str) -> JsonDict:
    refs = hbm_energy_calibration.get("source_backed_hbm_energy_refs", [])
    for ref in refs:
        if isinstance(ref, dict) and ref.get("measurement_id") == measurement_id:
            return ref
    for ref in refs:
        if isinstance(ref, dict):
            return ref
    best = hbm_energy_calibration.get("best", {})
    calibration = best.get("hbm_energy_calibration", {}) if isinstance(best, dict) else {}
    if calibration:
        return calibration
    raise RuntimeError("no HBM calibration reference found")


def _hbm_dram_energy(row: JsonDict) -> JsonDict:
    value = row.get("hbm_dram_energy")
    if not isinstance(value, dict):
        raise RuntimeError(f"row {_candidate_id(row)} has no hbm_dram_energy block")
    return value


def _hbm_service(row: JsonDict) -> JsonDict:
    value = row.get("hbm_dram_service")
    if isinstance(value, dict):
        return value
    return {}


def _base_hbm_bytes(row: JsonDict) -> float:
    dram = _hbm_dram_energy(row)
    return _as_float(dram.get("read_bytes")) + _as_float(dram.get("write_bytes"))


def _calibration_scale(anchor_row: JsonDict, ref: JsonDict) -> JsonDict:
    dram = _hbm_dram_energy(anchor_row)
    model_pj = _as_float(dram.get("energy_pj"))
    target_pj = _base_hbm_bytes(anchor_row) * _as_float(ref["hbm_energy_pj_per_byte"])
    if model_pj <= 0.0 or target_pj <= 0.0:
        raise RuntimeError("cannot calibrate HBM command energy with non-positive model or target energy")
    return {
        "anchor_candidate_id": _candidate_id(anchor_row),
        "measurement_id": ref["measurement_id"],
        "external_design_id": ref.get("external_design_id"),
        "source_hbm_energy_pj_per_bit": _as_float(ref["hbm_energy_pj_per_bit"]),
        "source_hbm_energy_pj_per_byte": _as_float(ref["hbm_energy_pj_per_byte"]),
        "anchor_model_hbm_energy_pj": model_pj,
        "anchor_target_hbm_energy_pj": target_pj,
        "command_energy_scale": target_pj / model_pj,
    }


def _scaled_params(row: JsonDict, scale: float) -> JsonDict:
    dram = _hbm_dram_energy(row)
    return {
        "read_hit_pj_per_byte": _as_float(dram.get("read_hit_pj_per_byte")) * scale,
        "read_miss_pj_per_byte": _as_float(dram.get("read_miss_pj_per_byte")) * scale,
        "write_pj_per_byte": _as_float(dram.get("write_pj_per_byte")) * scale,
        "activate_precharge_pj_per_row": _as_float(dram.get("activate_precharge_pj_per_row")) * scale,
        "command_pj_per_burst": _as_float(dram.get("command_pj_per_burst")) * scale,
    }


def _dram_terms(row: JsonDict, row_hit_rate: float, scale: float) -> JsonDict:
    dram = _hbm_dram_energy(row)
    params = _scaled_params(row, scale)
    read_bytes = _as_float(dram.get("read_bytes"))
    write_bytes = _as_float(dram.get("write_bytes"))
    hit_read_bytes = read_bytes * row_hit_rate
    miss_read_bytes = read_bytes - hit_read_bytes
    burst_bytes = max(1.0, _as_float(dram.get("burst_bytes"), _as_float(_hbm_service(row).get("burst_bytes"), 1024.0)))
    burst_count = math.ceil((read_bytes + write_bytes) / burst_bytes)
    miss_row_count = math.ceil(miss_read_bytes / burst_bytes)
    read_hit_pj = hit_read_bytes * params["read_hit_pj_per_byte"]
    read_miss_pj = miss_read_bytes * params["read_miss_pj_per_byte"]
    write_pj = write_bytes * params["write_pj_per_byte"]
    activate_precharge_pj = miss_row_count * params["activate_precharge_pj_per_row"]
    command_pj = burst_count * params["command_pj_per_burst"]
    total_pj = read_hit_pj + read_miss_pj + write_pj + activate_precharge_pj + command_pj
    return {
        "status": "hbm_command_class_energy_scaled_to_source_aggregate_not_stack_current_signoff",
        "row_hit_rate": row_hit_rate,
        "energy_pj": total_pj,
        "energy_mj": total_pj / 1_000_000_000.0,
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
        **params,
    }


def _service_latency(row: JsonDict, row_hit_rate: float) -> JsonDict:
    service = _hbm_service(row)
    base_latency_us = _as_float(row.get("base_latency_us"), _as_float(row.get("latency_us")))
    original_effective = max(1e-12, _as_float(service.get("original_effective_hbm_bytes_per_cycle")))
    raw_bytes_per_cycle = max(1e-12, _as_float(service.get("raw_hbm_bytes_per_cycle")))
    scheduler_efficiency = max(1e-12, _as_float(service.get("scheduler_efficiency"), 1.0))
    arbitration_efficiency = max(1e-12, _as_float(service.get("arbitration_efficiency"), 1.0))
    burst_bytes = max(1.0, _as_float(service.get("burst_bytes"), _as_float(_hbm_dram_energy(row).get("burst_bytes"), 1024.0)))
    request_overhead_cycles = max(0.0, _as_float(service.get("request_overhead_cycles")))
    row_miss_penalty_cycles = max(0.0, _as_float(service.get("row_miss_penalty_cycles")))
    outstanding = max(1.0, _as_float(service.get("hbm_outstanding"), 1.0))
    sustained_bytes_per_cycle = raw_bytes_per_cycle * scheduler_efficiency * arbitration_efficiency
    payload_cycles = burst_bytes / max(1e-12, sustained_bytes_per_cycle)
    hidden_cycles = (request_overhead_cycles + (1.0 - row_hit_rate) * row_miss_penalty_cycles) / math.sqrt(outstanding)
    modeled_effective = burst_bytes / max(1e-12, payload_cycles + hidden_cycles)
    service_scale = original_effective / max(1e-12, modeled_effective)
    hbm_latency_weight = _as_float(row.get("hbm_latency_weight"), 0.5)
    latency_us = base_latency_us * ((1.0 - hbm_latency_weight) + hbm_latency_weight * service_scale)
    return {
        "latency_us": latency_us,
        "base_latency_us": base_latency_us,
        "token_throughput_per_s": _tokens_per_s(latency_us),
        "service_latency_scale": service_scale,
        "hbm_latency_weight": hbm_latency_weight,
        "modeled_effective_hbm_bytes_per_cycle": modeled_effective,
        "row_hit_rate": row_hit_rate,
        "payload_cycles_per_burst": payload_cycles,
        "hidden_command_cycles_per_burst": hidden_cycles,
    }


def _modeled_row(row: JsonDict, row_hit_rate: float, scale: float) -> JsonDict:
    dram = _dram_terms(row, row_hit_rate, scale)
    latency = _service_latency(row, row_hit_rate)
    components = dict(row.get("energy_components") or {})
    components["hbm_mj"] = dram["energy_mj"]
    total_energy_mj = sum(_as_float(value) for value in components.values())
    dominant = max(components.items(), key=lambda item: _as_float(item[1]))[0].replace("_mj", "")
    out = dict(row)
    out.update(
        {
            "arch_id": "hbm_command_calibrated_service_frontier",
            "source_candidate_id": _candidate_id(row),
            "latency_us": latency["latency_us"],
            "token_throughput_per_s": latency["token_throughput_per_s"],
            "energy_mj": total_energy_mj,
            "energy_status": "hbm_command_class_scaled_to_source_aggregate_not_stack_current_signoff",
            "dominant_energy_component": dominant,
            "energy_components": components,
            "hbm_command_calibrated_energy": dram,
            "hbm_command_calibrated_service": latency,
        }
    )
    return out


def _scenario(rows: list[JsonDict], row_hit_rate: float, scale: float) -> JsonDict:
    modeled = [_modeled_row(row, row_hit_rate, scale) for row in rows]
    energy_best = min(modeled, key=lambda row: (_as_float(row["energy_mj"]), _as_float(row["latency_us"])))
    latency_best = min(modeled, key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"])))
    return {
        "row_hit_rate": row_hit_rate,
        "energy_best": energy_best,
        "latency_best": latency_best,
        "rows": sorted(modeled, key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"]))),
    }


def build_payload(args: argparse.Namespace) -> JsonDict:
    hbm_dram_service = _load_json(args.hbm_dram_service_energy_json)
    hbm_energy_calibration = _load_json(args.hbm_energy_calibration_json)
    rows = _source_rows(hbm_dram_service)
    if not rows:
        raise RuntimeError("no HBM/DRAM service rows found")
    previous_best = hbm_energy_calibration.get("best")
    if not isinstance(previous_best, dict):
        raise RuntimeError("HBM energy calibration input has no best row")
    ref = _primary_ref(hbm_energy_calibration, args.primary_measurement_id)
    anchor_candidate = str(previous_best.get("source_candidate_id") or previous_best.get("candidate_id"))
    anchor_row = next((row for row in rows if _candidate_id(row) == anchor_candidate), rows[0])
    scale = _calibration_scale(anchor_row, ref)
    base_row_hit = _as_float(_hbm_service(anchor_row).get("row_hit_rate"), 0.9)
    row_hit_rates = sorted(set([base_row_hit, *args.row_hit_rate_list]))
    scenarios = [_scenario(rows, row_hit_rate, _as_float(scale["command_energy_scale"])) for row_hit_rate in row_hit_rates]
    primary = min(scenarios, key=lambda scenario: abs(_as_float(scenario["row_hit_rate"]) - base_row_hit))
    best = dict(primary["energy_best"])
    best["arch_id"] = "hbm_command_calibrated_service_best"
    previous_family = _frontier_family(previous_best)
    calibrated_family = _frontier_family(best)
    frontier_changed = previous_family != calibrated_family
    row_hit_changed = any(_frontier_family(scenario["energy_best"]) != previous_family for scenario in scenarios)
    decision = (
        "hbm_command_calibrated_service_changes_frontier"
        if frontier_changed
        else "hbm_command_calibrated_service_preserves_frontier"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "previous_hbm_energy_calibration_best": _candidate_id(previous_best),
            "command_calibrated_energy_best": _candidate_id(best),
            "previous_energy_family": previous_family,
            "command_calibrated_energy_family": calibrated_family,
            "energy_frontier_changed_vs_hbm_energy_calibration": frontier_changed,
            "any_row_hit_scenario_changes_energy_family": row_hit_changed,
            "recommended_next_step": (
                "Use the command-calibrated HBM service result to decide whether to invest next in "
                "cycle-accurate HBM controller/current modeling or in direct compute-energy measurement."
            ),
        },
        "best": best,
        "primary_scenario": primary,
        "row_hit_scenarios": scenarios,
        "command_energy_calibration": scale,
        "remaining_abstractions": [
            "HBM command-class terms are globally scaled to an aggregate source pJ/bit anchor; this is not vendor stack-current signoff.",
            "Row-hit service sensitivity is analytic and reuses the existing HBM controller service model, not a cycle-accurate RTL controller.",
            "Compute energy remains scaled from the nearest measured dense compute reference.",
            "NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.",
        ],
        "source_artifacts": {
            "hbm_dram_service_energy_model": hbm_dram_service.get("model"),
            "hbm_energy_calibration_model": hbm_energy_calibration.get("model"),
        },
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B HBM Command-Calibrated Service",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- command_energy_scale: `{payload['command_energy_calibration']['command_energy_scale']}`",
        f"- previous_energy_family: `{payload['diagnosis']['previous_energy_family']}`",
        f"- command_calibrated_energy_family: `{payload['diagnosis']['command_calibrated_energy_family']}`",
        f"- any_row_hit_scenario_changes_energy_family: `{payload['diagnosis']['any_row_hit_scenario_changes_energy_family']}`",
        "",
        "## Best Point",
        "",
        "| candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy | row hit |",
        "|---|---:|---:|---:|---:|---|---:|",
        "| {source_candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {dominant_energy_component} | {row_hit_rate} |".format(
            row_hit_rate=best["hbm_command_calibrated_energy"]["row_hit_rate"],
            **best,
        ),
        "",
        "## Row-Hit Scenarios",
        "",
        "| row hit | latency best | energy best | energy mJ | dominant energy |",
        "|---:|---|---|---:|---|",
    ]
    for scenario in payload["row_hit_scenarios"]:
        energy_best = scenario["energy_best"]
        latency_best = scenario["latency_best"]
        lines.append(
            "| {row_hit_rate} | {latency_candidate} | {energy_candidate} | {energy_mj} | {dominant} |".format(
                row_hit_rate=scenario["row_hit_rate"],
                latency_candidate=latency_best["source_candidate_id"],
                energy_candidate=energy_best["source_candidate_id"],
                energy_mj=energy_best["energy_mj"],
                dominant=energy_best["dominant_energy_component"],
            )
        )
    lines.extend(["", "## Remaining Abstractions"])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hbm-dram-service-energy-json", type=Path, required=True)
    parser.add_argument("--hbm-energy-calibration-json", type=Path, required=True)
    parser.add_argument("--primary-measurement-id", default="hbm2_fgdram_micro2017_access_energy")
    parser.add_argument("--row-hit-rate-list", type=_float_list, default=[0.5, 0.7, 0.9, 0.95])
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
