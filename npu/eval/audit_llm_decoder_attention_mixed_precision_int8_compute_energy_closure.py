#!/usr/bin/env python3
"""Compose bounded Llama7B energy closure from mixed-int8 compute feasibility rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import sys

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
    die_area_mm2 = _as_float(row.get("die_area_mm2"))
    compute_arch = row.get("substituted_compute_arch", row.get("substituted_compute_variant_label", "compute"))
    replicas = int(_as_float(row.get("substituted_compute_replica_count"), 1))
    return (
        f"die{die_area_mm2:g}_"
        f"{compute_arch}_"
        f"rep{replicas}_"
        f"lat{_effective_latency_us(row):g}_"
        f"hbm{_as_float(row.get('hbm_byte_share')):.6f}_"
        f"tt{int(_as_float(row.get('tile_tokens'), 0.0))}"
    )


def _effective_latency_us(row: JsonDict) -> float:
    adjusted = row.get("adjusted_latency_us_if_feasible")
    if adjusted is not None:
        adjusted_us = _as_float(adjusted)
        if adjusted_us > 0.0:
            return adjusted_us
    return _as_float(row.get("latency_us"))


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


def _compute_candidate_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    rows: list[JsonDict] = []
    if isinstance(payload.get("rows"), list):
        rows.extend(row for row in payload["rows"] if isinstance(row, dict))
    for key in ("best_requested", "best_feasible", "best_area_fit"):
        candidate = payload.get(key)
        if isinstance(candidate, dict):
            rows.append(candidate)

    filtered: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        latency = _effective_latency_us(row)
        if latency <= 0.0:
            continue
        if _as_float(row.get("substituted_compute_power_mw")) <= 0.0:
            continue
        if not row.get("substituted_compute_arch"):
            continue
        row = dict(row)
        row["candidate_id"] = _candidate_id(row)
        if row["candidate_id"] in seen:
            continue
        seen.add(row["candidate_id"])
        filtered.append(row)

    filtered.sort(
        key=lambda row: (
            _effective_latency_us(row),
            _as_float(row.get("die_area_mm2")),
            _as_float(row.get("substituted_compute_power_mw")),
            str(row.get("substituted_compute_arch")),
        )
    )
    return filtered[:limit]


def _compute_area_mm2(row: JsonDict) -> float:
    required_um2 = _as_float(row.get("compute_area_required_um2"))
    if required_um2 > 0.0:
        return required_um2 / 1_000_000.0
    block_area_um2 = _as_float(row.get("substituted_compute_area_um2"))
    replicas = _as_float(row.get("substituted_compute_replica_count"), 1.0)
    if block_area_um2 <= 0.0:
        return 0.0
    if replicas > 1.0:
        return block_area_um2 * replicas / 1_000_000.0
    return block_area_um2 / 1_000_000.0


def _energy_row(row: JsonDict, command_calibrated: JsonDict, sram_profile: JsonDict) -> JsonDict:
    latency_us = _effective_latency_us(row)
    traffic = _traffic(row)

    hbm_pj_per_byte = _hbm_energy_pj_per_byte(command_calibrated)
    hbm_read_bytes = _as_float(traffic.get("hbm_read_bytes"))
    kv_write_bytes = _as_float(traffic.get("kv_write_bytes"))
    hbm_energy_pj = (hbm_read_bytes + kv_write_bytes) * hbm_pj_per_byte

    sram = _sram_energy_terms(sram_profile, traffic)
    noc_hops = _as_float(row.get("noc_hops"), 1.0)
    noc_payload_bytes = _as_float(traffic.get("estimated_noc_payload_bytes"))
    noc_energy_pj = noc_payload_bytes * noc_hops * 0.02

    substituted_compute_power_mw = _as_float(row.get("substituted_compute_power_mw"))
    measured_l1_overhead_power_mw = _as_float(row.get("measured_l1_overhead_power_mw"))
    compute_power_mw = substituted_compute_power_mw + measured_l1_overhead_power_mw
    if compute_power_mw <= 0.0:
        compute_power_mw = substituted_compute_power_mw
    compute_energy_mj = _energy_mj_from_power(compute_power_mw, latency_us)

    components = {
        "compute": {
            "status": "substituted_int8_compute_power_from_physical_feasibility",
            "energy_mj": compute_energy_mj,
            "power_mw": compute_power_mw,
            "substituted_compute_power_mw": substituted_compute_power_mw,
            "measured_l1_overhead_power_mw_included": measured_l1_overhead_power_mw,
            "power_area_mm2": _compute_area_mm2(row),
            "replica_count": int(_as_float(row.get("substituted_compute_replica_count"), 1)),
            "latency_us": latency_us,
            "compute_arch": row.get("substituted_compute_arch"),
            "block_area_um2": _as_float(row.get("substituted_compute_area_um2")),
        },
        "hbm": {
            "status": "source_backed_aggregate_hbm_energy",
            "energy_mj": _energy_mj_from_pj(hbm_energy_pj),
            "energy_pj": hbm_energy_pj,
            "energy_pj_per_byte": hbm_pj_per_byte,
            "read_bytes": hbm_read_bytes,
            "write_bytes": kv_write_bytes,
        },
        "sram": sram,
        "noc": {
            "status": "profile_payload_byte_hop",
            "energy_mj": _energy_mj_from_pj(noc_energy_pj),
            "energy_pj": noc_energy_pj,
            "payload_bytes": noc_payload_bytes,
            "hops": noc_hops,
            "energy_pj_per_byte_hop": 0.02,
        },
    }
    total_energy_mj = sum(_as_float(component.get("energy_mj")) for component in components.values() if component.get("energy_mj") is not None)
    dominant = max(
        (
            (name, _as_float(component.get("energy_mj")))
            for name, component in components.items()
            if isinstance(component, dict)
        ),
        key=lambda item: item[1],
    )[0].replace("_", " ")

    substituted_compute_arch = row.get("substituted_compute_arch")
    substituted_compute_replica_count = int(_as_float(row.get("substituted_compute_replica_count"), 1))
    substituted_compute_area_um2 = _as_float(row.get("substituted_compute_area_um2"))

    return {
        **row,
        "candidate_id": _candidate_id(row),
        "arch_id": "mixed_precision_int8_compute_energy_closure_frontier",
        "latency_us": latency_us,
        "base_latency_us": _as_float(row.get("latency_us")),
        "token_throughput_per_s": _tokens_per_s(latency_us),
        "die_area_mm2": _as_float(row.get("die_area_mm2")),
        "compute_arch": substituted_compute_arch,
        "compute_power_mw": compute_power_mw,
        "compute_replica_count": substituted_compute_replica_count,
        "metrics_csv": row.get("substituted_compute_metrics_csv") or row.get("metrics_csv"),
        "compute_area_um2": _compute_area_mm2(row) * 1_000_000.0,
        "compute_area_mm2": _compute_area_mm2(row),
        "substituted_compute_arch": substituted_compute_arch,
        "substituted_compute_replica_count": substituted_compute_replica_count,
        "substituted_compute_power_mw": compute_power_mw,
        "substituted_compute_power_mw_only": substituted_compute_power_mw,
        "measured_l1_overhead_power_mw_included": measured_l1_overhead_power_mw,
        "substituted_compute_area_um2": substituted_compute_area_um2,
        "compute_energy_mj": compute_energy_mj,
        "hbm_energy_mj": _energy_mj_from_pj(hbm_energy_pj),
        "sram_energy_mj": _as_float(sram.get("energy_mj")),
        "noc_energy_mj": _energy_mj_from_pj(noc_energy_pj),
        "energy_mj": total_energy_mj,
        "energy_status": "mixed_precision_int8_compute_power_and_measured_hbm_sram_service",
        "dominant_energy_component": dominant,
        "energy_components": components,
    }


def _baseline_summary(path: Path | None) -> JsonDict | None:
    if path is None:
        return None
    payload = _load_json(path)
    best = payload.get("best") if isinstance(payload.get("best"), dict) else {}
    latency_best = payload.get("latency_best") if isinstance(payload.get("latency_best"), dict) else {}
    return {
        "model": payload.get("model"),
        "decision": payload.get("decision"),
        "energy_best_candidate_id": best.get("candidate_id"),
        "energy_best_latency_us": best.get("latency_us"),
        "energy_best_throughput_tok_s": best.get("token_throughput_per_s"),
        "energy_best_energy_mj": best.get("energy_mj"),
        "energy_best_area_mm2": best.get("die_area_mm2"),
        "latency_best_candidate_id": latency_best.get("candidate_id"),
        "latency_best_latency_us": latency_best.get("latency_us"),
        "latency_best_energy_mj": latency_best.get("energy_mj"),
        "latency_best_area_mm2": latency_best.get("die_area_mm2"),
    }


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
    feasibility = _load_json(args.mixed_precision_int8_compute_physical_feasibility_json)
    sram_profile = _load_json(args.sram_profile_json)

    source_rows = _compute_candidate_rows(feasibility, limit=args.row_limit)
    if not source_rows:
        raise RuntimeError("no substituted-compute feasibility rows found")

    modeled_rows = [_energy_row(row, command_calibrated, sram_profile) for row in source_rows]
    latency_best = min(modeled_rows, key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"])))
    energy_best = min(modeled_rows, key=lambda row: (_as_float(row["energy_mj"]), _as_float(row["latency_us"])))
    pareto_rows = _pareto(modeled_rows)
    baseline_closure_json = getattr(args, "baseline_closure_json", None)
    baseline = _baseline_summary(baseline_closure_json)

    best_requested = feasibility.get("best_requested")
    best_requested = best_requested if isinstance(best_requested, dict) else {}
    feasibility_diag = feasibility.get("diagnosis") if isinstance(feasibility.get("diagnosis"), dict) else {}
    decision = "mixed_precision_int8_compute_energy_closure_recorded"
    recommended_next_step = "promote mixed-precision dual-stream candidate into measured RTL/PPA wrapper"
    if not bool(feasibility_diag.get("physical_feasible_rows")):
        decision = "mixed_precision_int8_compute_energy_closure_recorded_source_latency_fallback"
        recommended_next_step = "inspect feasibility inputs; next run should include adjusted latency from measured dual-stream feasibility"
    baseline_energy = _as_float((baseline or {}).get("energy_best_energy_mj"))
    baseline_latency = _as_float((baseline or {}).get("energy_best_latency_us"))
    if baseline_energy > 0.0 and _as_float(energy_best.get("energy_mj")) < baseline_energy:
        decision = "mixed_precision_int8_compute_replaces_fp16_v3_energy_frontier"
        recommended_next_step = "prioritize checkpoint-quality validation for the mixed/int8 frontier before promotion"
    elif baseline_latency > 0.0 and _as_float(latency_best.get("latency_us")) < baseline_latency:
        decision = "mixed_precision_int8_compute_improves_latency_not_energy"
        recommended_next_step = (
            "keep exact-FP16 V3 as the energy baseline and use mixed/int8 as the latency frontier "
            "pending real-checkpoint quality validation"
        )

    return {
        "version": 1,
        "model": "llm_decoder_attention_mixed_precision_int8_compute_energy_closure_llama7b_v1",
        "decision": decision,
        "source_model": feasibility.get("source_model"),
        "inputs": {
            "hbm_command_calibrated_service_json": str(args.hbm_command_calibrated_service_json),
            "mixed_precision_int8_compute_physical_feasibility_json": str(args.mixed_precision_int8_compute_physical_feasibility_json),
            "sram_profile_json": str(args.sram_profile_json),
        },
        "diagnosis": {
            "decision": decision,
            "source_rows_used": len(source_rows),
            "feasibility_rows": feasibility_diag.get("source_rows_used"),
            "physical_feasible_rows": feasibility_diag.get("physical_feasible_rows", 0),
            "best_requested_mode": best_requested.get("compute_mode"),
            "best_requested_latency_us": best_requested.get("latency_us"),
            "best_requested_adjusted_latency_us_if_feasible": best_requested.get("adjusted_latency_us_if_feasible"),
            "best_requested_substituted_compute_arch": best_requested.get("substituted_compute_arch"),
            "best_requested_substituted_compute_replica_count": best_requested.get("substituted_compute_replica_count"),
            "best_requested_substituted_compute_area_um2": best_requested.get("substituted_compute_area_um2"),
            "best_requested_substituted_compute_power_mw": best_requested.get("substituted_compute_power_mw"),
            "baseline_fp16_v3": baseline,
            "recommended_next_step": recommended_next_step,
        },
        "input_row_count": len(source_rows),
        "best": {
            **energy_best,
            "arch_id": "mixed_precision_int8_compute_energy_closure_best",
        },
        "latency_best": latency_best,
        "pareto_rows": pareto_rows[: args.pareto_row_limit],
        "source_artifacts": {
            "hbm_command_calibrated_service_model": command_calibrated.get("model"),
            "sram_profile_model": sram_profile.get("model"),
            "baseline_closure_json": str(baseline_closure_json) if baseline_closure_json else None,
        },
        "remaining_abstractions": [
            "HBM and SRAM energy are sourced from existing aggregate campaign helpers; NoC still uses the payload-byte-hop model.",
            "Compute energy is from substituted_compute_power_mw plus measured local L1 overhead power carried by mixed-precision feasibility rows, not from a fresh end-to-end measured compute rerun.",
            "adjusted_latency_us_if_feasible is used when present and source latency is used as a fallback.",
            "Mixed/int8 quality remains proxy-backed, not real Llama7B checkpoint perplexity or task accuracy.",
        ],
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    diag = payload["diagnosis"]
    lines = [
        "# Llama7B Mixed-Precision Int8 Compute Energy Closure",
        "",
        f"- decision: `{diag['decision']}`",
        f"- source rows used: `{diag['source_rows_used']}`",
        f"- physical feasible rows: `{diag['physical_feasible_rows']}`",
        f"- best requested mode: `{diag['best_requested_mode']}`",
        f"- best requested adjusted latency us: `{diag['best_requested_adjusted_latency_us_if_feasible']}`",
        f"- best requested substituted compute arch: `{diag['best_requested_substituted_compute_arch']}`",
        f"- best requested substituted compute area um2: `{diag['best_requested_substituted_compute_area_um2']}`",
        f"- best requested substituted compute power mw: `{diag['best_requested_substituted_compute_power_mw']}`",
        f"- baseline fp16 v3 energy mJ: `{(diag.get('baseline_fp16_v3') or {}).get('energy_best_energy_mj')}`",
        f"- baseline fp16 v3 latency us: `{(diag.get('baseline_fp16_v3') or {}).get('energy_best_latency_us')}`",
        f"- recommended next step: `{diag['recommended_next_step']}`",
        "",
        "## Best Measured Point",
        "",
        "| candidate | latency us | throughput tok/s | energy mJ | area mm2 | compute mJ | HBM mJ | sram mJ | dominant |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {compute_energy_mj} | {hbm_energy_mj} | {sram_energy_mj} | {dominant_energy_component} |".format(
            **best
        ),
        "",
        "## Pareto Rows",
        "",
        "| candidate | latency us | energy mJ | area mm2 | compute arch | compute replicas | dominant |",
        "|---|---:|---:|---:|---|---:|---|",
    ]
    for row in payload["pareto_rows"]:
        lines.append(
            "| {candidate_id} | {latency_us} | {energy_mj} | {die_area_mm2} | {substituted_compute_arch} | {substituted_compute_replica_count} | {dominant_energy_component} |".format(
                **row
            )
        )

    lines.extend(["", "## Remaining Abstractions", ""])
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hbm-command-calibrated-service-json", type=Path, required=True)
    parser.add_argument("--mixed-precision-int8-compute-physical-feasibility-json", type=Path, required=True)
    parser.add_argument("--sram-profile-json", type=Path, required=True)
    parser.add_argument("--baseline-closure-json", type=Path)
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
