#!/usr/bin/env python3
"""Sweep HBM pJ/byte energy for retained Llama7B attention frontier rows."""

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
    _compute_energy_terms,
    _energy_mj_from_pj,
    _load_json,
    _sram_energy_terms,
    _tokens_per_s,
    _traffic,
)


JsonDict = dict[str, Any]


def _float_list(text: str) -> list[float]:
    values = [float(part.strip()) for part in text.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("list must contain at least one value")
    if any(value < 0.0 for value in values):
        raise argparse.ArgumentTypeError("energy values must be non-negative")
    return values


def _candidate_id(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}_kv{int(_as_float(row.get('kv_bits')))}_"
        f"{row.get('kv_sharing', 'kv')}_lat{_as_float(row.get('latency_us')):g}_"
        f"hbm{_as_float(row.get('hbm_byte_share')):.6f}_"
        f"dt{int(_as_float(row.get('data_rate_mtps')))}_eff{_as_float(row.get('hbm_efficiency')):g}_"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def _precision_status(row: JsonDict, integrated_energy: JsonDict) -> str:
    kv_bits = _as_float(row.get("kv_bits"))
    if kv_bits >= 8.0:
        return "quality_backed_conservative"
    precision = integrated_energy.get("precision")
    if isinstance(precision, dict) and precision.get("kv4_promotable_without_recovery"):
        return "kv4_promotable_with_existing_evidence"
    return "precision_risky_requires_recovery"


def _frontier_rows(hbm_quality_backed: JsonDict, limit: int) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for key in ("best", "top_rows", "best_by_memory_noc", "best_by_hbm_physical"):
        value = hbm_quality_backed.get(key)
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    seen: set[str] = set()
    deduped: list[JsonDict] = []
    for row in rows:
        if _as_float(row.get("latency_us")) <= 0.0 or _as_float(row.get("die_area_mm2")) <= 0.0:
            continue
        candidate_id = _candidate_id(row)
        if candidate_id in seen:
            continue
        seen.add(candidate_id)
        deduped.append(row)
    deduped.sort(
        key=lambda row: (
            _as_float(row.get("latency_us")),
            _as_float(row.get("die_area_mm2")),
            _as_float(row.get("hbm_byte_share")),
        )
    )
    return deduped[:limit]


def _energy_row(
    *,
    row: JsonDict,
    integrated_energy: JsonDict,
    measured_compute: JsonDict,
    sram_profile: JsonDict,
    hbm_energy_pj_per_byte: float,
    noc_energy_pj_per_byte_hop: float,
) -> JsonDict:
    latency_us = _as_float(row.get("latency_us"))
    macs_per_cycle = _as_float(row.get("macs_per_cycle"))
    traffic = _traffic(row)
    compute = _compute_energy_terms(
        selected=row,
        measured_compute=measured_compute,
        latency_us=latency_us,
        target_macs_per_cycle=macs_per_cycle,
    )
    sram = _sram_energy_terms(sram_profile, traffic)
    hbm_energy_pj = _as_float(traffic["hbm_read_bytes"]) * hbm_energy_pj_per_byte
    noc_hops = _as_float(row.get("noc_hops"), 1.0)
    noc_bytes = _as_float(traffic["estimated_noc_payload_bytes"])
    noc_energy_pj = noc_bytes * noc_hops * noc_energy_pj_per_byte_hop
    components = {
        "compute_mj": _as_float(compute.get("energy_mj")),
        "hbm_mj": _energy_mj_from_pj(hbm_energy_pj),
        "sram_mj": _as_float(sram.get("energy_mj")),
        "noc_mj": _energy_mj_from_pj(noc_energy_pj),
    }
    total_energy_mj = sum(components.values())
    dominant_energy_component = max(components.items(), key=lambda item: item[1])[0].replace("_mj", "")
    return {
        "candidate_id": _candidate_id(row),
        "arch_id": "physical_hbm_gqa8_kv8_service_frontier",
        "latency_us": latency_us,
        "token_throughput_per_s": _tokens_per_s(latency_us),
        "die_area_mm2": _as_float(row.get("die_area_mm2")),
        "kv_bits": row.get("kv_bits"),
        "kv_sharing": row.get("kv_sharing"),
        "precision_status": _precision_status(row, integrated_energy),
        "macs_per_cycle": macs_per_cycle,
        "vector_ops_per_cycle": row.get("vector_ops_per_cycle"),
        "hbm_energy_pj_per_byte": hbm_energy_pj_per_byte,
        "hbm_byte_share": row.get("hbm_byte_share"),
        "hbm_read_bytes": traffic["hbm_read_bytes"],
        "total_tile_kv_read_bytes": traffic["total_tile_kv_read_bytes"],
        "energy_mj": total_energy_mj,
        "dominant_energy_component": dominant_energy_component,
        "energy_components": components,
        "source_latency_resource": row.get("dominant_tile_resource"),
        "data_rate_mtps": row.get("data_rate_mtps"),
        "hbm_efficiency": row.get("hbm_efficiency"),
        "tile_tokens": row.get("tile_tokens"),
        "total_sram_mib": row.get("total_sram_mib"),
        "remaining_energy_abstractions": [
            "HBM energy is swept by pJ/byte rather than modeled with cycle-accurate DRAM command power.",
            "Compute energy is still scaled from the nearest measured dense compute reference.",
            "NoC/SRAM energy uses the same profile-scaled accounting as the integrated energy closure.",
        ],
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


def _with_score(rows: list[JsonDict], baseline: JsonDict) -> list[JsonDict]:
    baseline_latency = max(1e-12, _as_float(baseline.get("latency_us")))
    baseline_energy = max(1e-12, _as_float(baseline.get("energy_mj")))
    baseline_area = max(1e-12, _as_float(baseline.get("die_area_mm2")))
    scored: list[JsonDict] = []
    for row in rows:
        out = dict(row)
        out["unit_weight_latency_energy_area_score"] = (
            _as_float(row.get("latency_us")) / baseline_latency
            + _as_float(row.get("energy_mj")) / baseline_energy
            + _as_float(row.get("die_area_mm2")) / baseline_area
        )
        scored.append(out)
    return scored


def build_payload(args: argparse.Namespace) -> JsonDict:
    integrated_energy = _load_json(args.integrated_energy_json)
    hbm_quality_backed = _load_json(args.hbm_quality_backed_json)
    measured_compute = _load_json(args.measured_compute_json)
    sram_profile = _load_json(args.sram_profile_json)
    rows = _frontier_rows(hbm_quality_backed, args.frontier_row_limit)
    if not rows:
        raise RuntimeError("no retained HBM frontier rows found")

    nominal_hbm = _as_float((integrated_energy.get("energy_parameters") or {}).get("hbm_energy_pj_per_byte"), 8.0)
    sweeps: list[JsonDict] = []
    nominal_selected: JsonDict | None = None
    for hbm_energy in args.hbm_energy_pj_per_byte_list:
        energy_rows = [
            _energy_row(
                row=row,
                integrated_energy=integrated_energy,
                measured_compute=measured_compute,
                sram_profile=sram_profile,
                hbm_energy_pj_per_byte=hbm_energy,
                noc_energy_pj_per_byte_hop=args.noc_energy_pj_per_byte_hop,
            )
            for row in rows
        ]
        latency_best = min(energy_rows, key=lambda item: (_as_float(item["latency_us"]), _as_float(item["energy_mj"])))
        energy_best = min(energy_rows, key=lambda item: (_as_float(item["energy_mj"]), _as_float(item["latency_us"])))
        scored_rows = _with_score(energy_rows, latency_best)
        balanced_best = min(
            scored_rows,
            key=lambda item: (
                _as_float(item["unit_weight_latency_energy_area_score"]),
                _as_float(item["latency_us"]),
            ),
        )
        pareto_rows = _pareto(energy_rows)
        if abs(hbm_energy - nominal_hbm) < 1e-9:
            nominal_selected = {
                "hbm_energy_pj_per_byte": hbm_energy,
                "latency_best": latency_best,
                "energy_best": energy_best,
                "balanced_best": balanced_best,
                "pareto_rows": pareto_rows[: args.pareto_row_limit],
            }
        sweeps.append(
            {
                "hbm_energy_pj_per_byte": hbm_energy,
                "latency_best": latency_best,
                "energy_best": energy_best,
                "balanced_best": balanced_best,
                "pareto_row_count": len(pareto_rows),
                "pareto_rows": pareto_rows[: args.pareto_row_limit],
            }
        )

    if nominal_selected is None:
        nominal_selected = min(sweeps, key=lambda sweep: abs(sweep["hbm_energy_pj_per_byte"] - nominal_hbm))

    latency_candidate = nominal_selected["latency_best"]
    energy_candidate = nominal_selected["energy_best"]
    energy_changes_frontier = latency_candidate["candidate_id"] != energy_candidate["candidate_id"]
    decision = (
        "hbm_energy_sensitivity_changes_energy_optimum"
        if energy_changes_frontier
        else "hbm_energy_sensitivity_keeps_latency_energy_optimum"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_hbm_energy_sensitivity_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "nominal_hbm_energy_pj_per_byte": nominal_selected["hbm_energy_pj_per_byte"],
            "latency_best_candidate_id": latency_candidate["candidate_id"],
            "energy_best_candidate_id": energy_candidate["candidate_id"],
            "energy_changes_frontier": energy_changes_frontier,
            "recommended_next_step": (
                "close HBM/DRAM energy and service modeling before claiming an energy-optimal Llama7B point"
                if energy_changes_frontier
                else "directly measure the selected compute service point and refine HBM service timing"
            ),
        },
        "best": {
            **energy_candidate,
            "arch_id": "hbm_energy_sensitivity_energy_best",
            "energy_status": "hbm_energy_parameter_swept_not_dram_signoff",
        },
        "latency_best_at_nominal": latency_candidate,
        "balanced_best_at_nominal": nominal_selected["balanced_best"],
        "nominal_pareto_rows": nominal_selected["pareto_rows"],
        "sweeps": sweeps,
        "input_row_count": len(rows),
        "energy_parameters": {
            "hbm_energy_pj_per_byte_list": args.hbm_energy_pj_per_byte_list,
            "nominal_hbm_energy_pj_per_byte": nominal_hbm,
            "noc_energy_pj_per_byte_hop": args.noc_energy_pj_per_byte_hop,
        },
        "remaining_abstractions": [
            "HBM energy remains a pJ/byte sensitivity sweep rather than a DRAM command/current model.",
            "HBM timing still comes from the merged physical-HBM service frontier, not a cycle-accurate memory controller.",
            "Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.",
            "NoC and SRAM energy remain profile-scaled as in the integrated energy closure.",
        ],
        "source_artifacts": {
            "integrated_energy_model": integrated_energy.get("model"),
            "hbm_quality_backed_model": hbm_quality_backed.get("model"),
            "measured_compute_model": measured_compute.get("model"),
            "sram_profile_model": sram_profile.get("model"),
        },
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    latency_best = payload["latency_best_at_nominal"]
    lines = [
        "# Llama7B HBM Energy Sensitivity",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- nominal_hbm_energy_pj_per_byte: `{payload['diagnosis']['nominal_hbm_energy_pj_per_byte']}`",
        f"- energy_changes_frontier: `{payload['diagnosis']['energy_changes_frontier']}`",
        "",
        "## Nominal Bests",
        "",
        "| role | candidate | latency us | throughput tok/s | energy mJ | area mm2 | hbm share | dominant energy |",
        "|---|---|---:|---:|---:|---:|---:|---|",
        "| latency | {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {hbm_byte_share} | {dominant_energy_component} |".format(
            **latency_best
        ),
        "| energy | {candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {hbm_byte_share} | {dominant_energy_component} |".format(
            **best
        ),
        "",
        "## Sweep Summary",
        "",
        "| hbm pJ/B | latency best | energy best | energy best mJ | energy best area | pareto rows |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for sweep in payload["sweeps"]:
        energy_best = sweep["energy_best"]
        lines.append(
            "| {hbm} | {lat} | {eng} | {energy} | {area} | {pareto} |".format(
                hbm=sweep["hbm_energy_pj_per_byte"],
                lat=sweep["latency_best"]["candidate_id"],
                eng=energy_best["candidate_id"],
                energy=energy_best["energy_mj"],
                area=energy_best["die_area_mm2"],
                pareto=sweep["pareto_row_count"],
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
    parser.add_argument("--hbm-quality-backed-json", type=Path, required=True)
    parser.add_argument("--measured-compute-json", type=Path, required=True)
    parser.add_argument("--sram-profile-json", type=Path, required=True)
    parser.add_argument("--hbm-energy-pj-per-byte-list", type=_float_list, default=[1.0, 2.0, 4.0, 8.0, 16.0, 32.0])
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
