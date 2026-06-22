#!/usr/bin/env python3
"""Compose an explicit energy account for the current Llama7B attention frontier."""

from __future__ import annotations

import argparse
import json
import math
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
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(parsed) or math.isinf(parsed):
        return default
    return parsed


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _energy_mj_from_pj(energy_pj: float) -> float:
    return energy_pj * 1e-9


def _energy_mj_from_power(power_mw: float, latency_us: float) -> float:
    return power_mw * latency_us * 1e-6


def _tokens_per_s(latency_us: float) -> float | None:
    if latency_us <= 0.0:
        return None
    return 1_000_000.0 / latency_us


def _best(payload: JsonDict | None) -> JsonDict:
    if not payload:
        return {}
    best = payload.get("best")
    return best if isinstance(best, dict) else {}


def _select_compute_reference(measured_compute: JsonDict | None, target_macs_per_cycle: float) -> JsonDict | None:
    rows: list[JsonDict] = []
    if measured_compute:
        top_rows = measured_compute.get("top_rows")
        if isinstance(top_rows, list):
            rows.extend(row for row in top_rows if isinstance(row, dict))
        best = measured_compute.get("best")
        if isinstance(best, dict):
            rows.append(best)
    usable = [
        row
        for row in rows
        if _as_float(row.get("macs_per_cycle")) > 0.0 and _as_float(row.get("compute_power_mw")) > 0.0
    ]
    if not usable:
        return None
    return min(
        usable,
        key=lambda row: (
            abs(_as_float(row.get("macs_per_cycle")) - target_macs_per_cycle),
            -_as_float(row.get("macs_per_cycle")),
        ),
    )


def _traffic(best: JsonDict) -> JsonDict:
    layers = _as_int(best.get("layers"), 32)
    hidden_size = _as_int(best.get("hidden_size"), 4096)
    attention_heads = max(1, _as_int(best.get("attention_heads"), 32))
    kv_heads = max(1, _as_int(best.get("kv_heads"), 4))
    head_dim = hidden_size // attention_heads
    tile_tokens = _as_int(best.get("tile_tokens"), 512)
    sequence_length = _as_int(best.get("sequence_length"), 32768)
    tile_count = _as_int(best.get("tile_count"), math.ceil(sequence_length / max(1, tile_tokens)))
    kv_bits = _as_float(best.get("kv_bits"), 8.0)
    kv_width = kv_heads * head_dim
    full_tile_kv_bytes = 2.0 * tile_tokens * kv_width * kv_bits / 8.0
    total_tile_kv_read_bytes = full_tile_kv_bytes * tile_count * layers
    hbm_share = _as_float(best.get("hbm_byte_share"), 1.0)
    hbm_read_bytes = total_tile_kv_read_bytes * hbm_share
    shared_read_bytes = total_tile_kv_read_bytes * max(0.0, 1.0 - hbm_share)
    kv_write_bytes = 2.0 * kv_width * kv_bits / 8.0 * layers
    reduction_scalar_bytes = 2.0
    partial_reduction_payload_bytes = attention_heads * 2.0 * reduction_scalar_bytes + hidden_size * reduction_scalar_bytes
    active_clusters = max(1, _as_int(best.get("active_clusters"), best.get("cluster_count", 1)))
    cross_tile_reduction_bytes = active_clusters * partial_reduction_payload_bytes * tile_count * layers
    return {
        "layers": layers,
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "kv_heads": kv_heads,
        "tile_tokens": tile_tokens,
        "tile_count": tile_count,
        "sequence_length": sequence_length,
        "full_tile_kv_bytes": full_tile_kv_bytes,
        "total_tile_kv_read_bytes": total_tile_kv_read_bytes,
        "hbm_read_bytes": hbm_read_bytes,
        "shared_read_bytes": shared_read_bytes,
        "kv_write_bytes": kv_write_bytes,
        "cross_tile_reduction_bytes": cross_tile_reduction_bytes,
        "estimated_noc_payload_bytes": shared_read_bytes + kv_write_bytes + cross_tile_reduction_bytes,
    }


def _sram_energy_terms(sram_profile: JsonDict | None, traffic: JsonDict) -> JsonDict:
    if not sram_profile:
        return {
            "status": "missing_sram_profile",
            "energy_mj": None,
        }
    totals = sram_profile.get("totals")
    totals = totals if isinstance(totals, dict) else {}
    summary = sram_profile.get("sram_metrics_summary")
    summary = summary if isinstance(summary, dict) else {}
    allocated = _as_float(totals.get("allocated_sram_bytes"))
    read_pj = _as_float(summary.get("total_read_energy_pj"))
    write_pj = _as_float(summary.get("total_write_energy_pj"))
    if allocated <= 0.0 or read_pj <= 0.0:
        return {
            "status": "incomplete_sram_profile",
            "energy_mj": None,
            "sram_metrics_summary": summary,
        }
    read_pj_per_byte = read_pj / allocated
    write_pj_per_byte = write_pj / allocated if write_pj > 0.0 else read_pj_per_byte
    sram_read_bytes = _as_float(traffic.get("shared_read_bytes"))
    sram_write_bytes = _as_float(traffic.get("kv_write_bytes"))
    energy_pj = sram_read_bytes * read_pj_per_byte + sram_write_bytes * write_pj_per_byte
    return {
        "status": "profile_scaled_from_measured_cacti_sram_buffers",
        "energy_mj": _energy_mj_from_pj(energy_pj),
        "energy_pj": energy_pj,
        "read_pj_per_byte": read_pj_per_byte,
        "write_pj_per_byte": write_pj_per_byte,
        "read_bytes": sram_read_bytes,
        "write_bytes": sram_write_bytes,
        "missing_instances": summary.get("missing_instances", []),
    }


def _compute_energy_terms(
    *,
    selected: JsonDict,
    measured_compute: JsonDict | None,
    latency_us: float,
    target_macs_per_cycle: float,
) -> JsonDict:
    ref = _select_compute_reference(measured_compute, target_macs_per_cycle)
    if ref is None:
        return {
            "status": "missing_measured_compute_reference",
            "energy_mj": None,
        }
    ref_macs = _as_float(ref.get("macs_per_cycle"))
    ref_power = _as_float(ref.get("compute_power_mw"))
    scaled_power = ref_power * target_macs_per_cycle / ref_macs if ref_macs > 0.0 else 0.0
    return {
        "status": "parameterized_from_nearest_measured_compute_density",
        "energy_mj": _energy_mj_from_power(scaled_power, latency_us),
        "scaled_power_mw": scaled_power,
        "target_macs_per_cycle": target_macs_per_cycle,
        "reference_macs_per_cycle": ref_macs,
        "reference_compute_power_mw": ref_power,
        "reference_latency_us": ref.get("latency_us"),
        "reference_die_area_mm2": ref.get("die_area_mm2"),
        "source_metrics_csv": ref.get("metrics_csv"),
        "note": (
            "The selected service frontier does not have measured compute PPA at its target "
            "MAC/cycle; this term scales the nearest measured dense compute reference."
        ),
    }


def _build_payload(
    *,
    integrated_closure: JsonDict,
    hbm_quality_backed: JsonDict,
    measured_compute: JsonDict | None,
    sram_profile: JsonDict | None,
    noc_profile: JsonDict | None,
    hbm_energy_pj_per_byte: float,
    noc_energy_pj_per_byte_hop: float,
) -> JsonDict:
    closure_best = _best(integrated_closure)
    hbm_best = _best(hbm_quality_backed)
    selected = hbm_best or closure_best
    if not selected:
        raise SystemExit("integrated or HBM frontier evidence is missing a best object")
    arch_id = str(closure_best.get("arch_id") or "physical_hbm_gqa8_kv8_service_frontier")
    latency_us = _as_float(closure_best.get("latency_us"), _as_float(selected.get("latency_us")))
    macs_per_cycle = _as_float(closure_best.get("macs_per_cycle"), _as_float(selected.get("macs_per_cycle")))
    traffic = _traffic(selected)

    hbm_energy_pj = _as_float(traffic["hbm_read_bytes"]) * hbm_energy_pj_per_byte
    noc_hops = _as_float(selected.get("noc_hops"), 1.0)
    noc_bytes = _as_float(traffic["estimated_noc_payload_bytes"])
    noc_energy_pj = noc_bytes * noc_hops * noc_energy_pj_per_byte_hop
    sram = _sram_energy_terms(sram_profile, traffic)
    compute = _compute_energy_terms(
        selected=selected,
        measured_compute=measured_compute,
        latency_us=latency_us,
        target_macs_per_cycle=macs_per_cycle,
    )

    components = {
        "compute": compute,
        "hbm": {
            "status": "parameterized_hbm_energy_per_byte",
            "energy_mj": _energy_mj_from_pj(hbm_energy_pj),
            "energy_pj": hbm_energy_pj,
            "energy_pj_per_byte": hbm_energy_pj_per_byte,
            "read_bytes": traffic["hbm_read_bytes"],
        },
        "sram": sram,
        "noc": {
            "status": "parameterized_payload_byte_hop_energy",
            "energy_mj": _energy_mj_from_pj(noc_energy_pj),
            "energy_pj": noc_energy_pj,
            "energy_pj_per_byte_hop": noc_energy_pj_per_byte_hop,
            "payload_bytes": noc_bytes,
            "hops": noc_hops,
        },
    }
    known_energy_mj = [
        _as_float(component.get("energy_mj"), -1.0)
        for component in components.values()
        if isinstance(component, dict) and component.get("energy_mj") is not None
    ]
    total_energy_mj = sum(value for value in known_energy_mj if value >= 0.0)
    dominant_energy_component = max(
        (
            (name, _as_float(component.get("energy_mj")))
            for name, component in components.items()
            if isinstance(component, dict)
        ),
        key=lambda item: item[1],
    )[0]

    remaining_abstractions = [
        "HBM energy uses an explicit pJ/byte sensitivity parameter, not a cycle-accurate DRAM timing/power model.",
        "NoC energy uses payload byte-hop accounting, not routed wire/switching simulation.",
        "SRAM energy scales CACTI macro access estimates by traffic bytes; it is not a placed SRAM compiler energy signoff.",
        "Selected 524288 MAC/cycle compute energy is scaled from the nearest measured dense compute reference, not directly measured at that service point.",
    ]
    if not measured_compute:
        remaining_abstractions.append("Measured compute reference artifact was not present; compute energy is incomplete.")
    if not sram_profile:
        remaining_abstractions.append("SRAM profile artifact was not present; SRAM energy is incomplete.")
    if not noc_profile:
        remaining_abstractions.append("NoC profile artifact was not present; NoC topology evidence is incomplete.")

    decision = "integrated_energy_closure_parameterized_frontier_recorded"
    return {
        "version": 1,
        "model": "llm_decoder_attention_integrated_energy_closure_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "selected_frontier": arch_id,
            "dominant_latency_resource": selected.get("dominant_tile_resource") or closure_best.get("dominant_resource"),
            "dominant_energy_component": dominant_energy_component,
            "recommended_next_step": (
                "measure or bound the selected compute service point directly, then refine HBM/NoC/SRAM energy from "
                "parameterized service accounting toward physical models"
            ),
        },
        "best": {
            "arch_id": arch_id,
            "latency_us": latency_us,
            "token_throughput_per_s": _tokens_per_s(latency_us),
            "die_area_mm2": closure_best.get("die_area_mm2", selected.get("die_area_mm2")),
            "kv_bits": selected.get("kv_bits"),
            "kv_sharing": selected.get("kv_sharing"),
            "macs_per_cycle": macs_per_cycle,
            "vector_ops_per_cycle": closure_best.get("vector_ops_per_cycle", selected.get("vector_ops_per_cycle")),
            "dominant_resource": selected.get("dominant_tile_resource") or closure_best.get("dominant_resource"),
            "energy_mj": total_energy_mj,
            "energy_status": "parameterized_integrated_energy_not_full_measurement",
            "dominant_energy_component": dominant_energy_component,
        },
        "energy_components": components,
        "traffic": traffic,
        "energy_parameters": {
            "hbm_energy_pj_per_byte": hbm_energy_pj_per_byte,
            "noc_energy_pj_per_byte_hop": noc_energy_pj_per_byte_hop,
        },
        "ranked_candidates": [
            {
                "name": "quality_backed_hbm_gqa8_kv8",
                "status": "current_selected_energy_accounted_frontier",
                "latency_us": latency_us,
                "token_throughput_per_s": _tokens_per_s(latency_us),
                "area_mm2": closure_best.get("die_area_mm2", selected.get("die_area_mm2")),
                "energy_mj": total_energy_mj,
                "energy_status": "parameterized_integrated_energy_not_full_measurement",
                "dominant_energy_component": dominant_energy_component,
            }
        ],
        "closure_flags": {
            "integrated_energy_accounting_available": True,
            "full_measured_energy_available": False,
            "compute_energy_directly_measured_at_selected_point": False,
            "hbm_energy_parameterized": True,
            "noc_energy_parameterized": True,
            "sram_energy_profile_scaled": sram.get("energy_mj") is not None,
        },
        "remaining_abstractions": remaining_abstractions,
        "source_artifacts": {
            "integrated_closure_model": integrated_closure.get("model"),
            "hbm_quality_backed_model": hbm_quality_backed.get("model"),
            "measured_compute_model": (measured_compute or {}).get("model"),
            "sram_profile_model": (sram_profile or {}).get("model"),
            "noc_profile_model": (noc_profile or {}).get("model"),
        },
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B Integrated Energy Closure",
        "",
        "## Selected Frontier",
        f"- arch_id: `{best['arch_id']}`",
        f"- latency_us: `{best['latency_us']}`",
        f"- token_throughput_per_s: `{best['token_throughput_per_s']}`",
        f"- die_area_mm2: `{best['die_area_mm2']}`",
        f"- energy_mj: `{best['energy_mj']}`",
        f"- energy_status: `{best['energy_status']}`",
        f"- dominant_energy_component: `{best['dominant_energy_component']}`",
        "",
        "## Energy Components",
        "",
        "| component | status | energy_mj |",
        "|---|---|---:|",
    ]
    for name, component in payload["energy_components"].items():
        lines.append(f"| {name} | {component.get('status')} | {component.get('energy_mj')} |")
    lines.extend(["", "## Closure Flags"])
    for key, value in payload["closure_flags"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Remaining Abstractions"])
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrated-closure-json", type=Path, required=True)
    parser.add_argument("--hbm-quality-backed-json", type=Path, required=True)
    parser.add_argument("--measured-compute-json", type=Path)
    parser.add_argument("--sram-profile-json", type=Path)
    parser.add_argument("--noc-profile-json", type=Path)
    parser.add_argument("--hbm-energy-pj-per-byte", type=float, default=8.0)
    parser.add_argument("--noc-energy-pj-per-byte-hop", type=float, default=0.02)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = _build_payload(
        integrated_closure=_load_json(args.integrated_closure_json),
        hbm_quality_backed=_load_json(args.hbm_quality_backed_json),
        measured_compute=_maybe_load_json(args.measured_compute_json),
        sram_profile=_maybe_load_json(args.sram_profile_json),
        noc_profile=_maybe_load_json(args.noc_profile_json),
        hbm_energy_pj_per_byte=args.hbm_energy_pj_per_byte,
        noc_energy_pj_per_byte_hop=args.noc_energy_pj_per_byte_hop,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
