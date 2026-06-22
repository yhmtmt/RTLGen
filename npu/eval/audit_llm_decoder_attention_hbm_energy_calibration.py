#!/usr/bin/env python3
"""Calibrate Llama7B HBM energy against source-backed HBM pJ/bit references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_records(path: Path) -> list[JsonDict]:
    records: list[JsonDict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _tokens_per_s(latency_us: float) -> float:
    return 1_000_000.0 / latency_us if latency_us > 0.0 else 0.0


def _candidate_id(row: JsonDict) -> str:
    return str(row.get("candidate_id") or row.get("arch_id") or "unknown")


def _energy_refs(external_measurements: list[JsonDict]) -> list[JsonDict]:
    refs: list[JsonDict] = []
    for record in external_measurements:
        derived = record.get("derived", {})
        pj_per_byte = derived.get("hbm_energy_pj_per_byte")
        if pj_per_byte is None:
            pj_per_bit = derived.get("hbm_energy_pj_per_bit")
            pj_per_byte = _as_float(pj_per_bit) * 8.0 if pj_per_bit is not None else None
        if pj_per_byte is None:
            continue
        pj_per_byte = _as_float(pj_per_byte)
        if pj_per_byte <= 0.0:
            continue
        refs.append(
            {
                "measurement_id": record["measurement_id"],
                "external_design_id": record["external_design_id"],
                "hbm_energy_pj_per_byte": pj_per_byte,
                "hbm_energy_pj_per_bit": pj_per_byte / 8.0,
                "comparability_class": record["comparability"]["class"],
                "comparability_reason": record["comparability"]["reason"],
                "published": record.get("published", {}),
                "normalization": record.get("normalization", {}),
            }
        )
    refs.sort(key=lambda row: _as_float(row["hbm_energy_pj_per_byte"]))
    return refs


def _require_claim(comparison_claims: list[JsonDict]) -> JsonDict:
    claim_id = "rtlgen_llama7b_hbm_energy_calibration_vs_external_refs_v1"
    for record in comparison_claims:
        if record.get("claim_id") == claim_id and record.get("status") == "active":
            return record
    raise RuntimeError(f"missing active comparison claim: {claim_id}")


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


def _hbm_bytes(row: JsonDict) -> float:
    dram = row.get("hbm_dram_energy") if isinstance(row.get("hbm_dram_energy"), dict) else {}
    read_bytes = _as_float(dram.get("read_bytes"), _as_float(row.get("hbm_read_bytes")))
    write_bytes = _as_float(dram.get("write_bytes"))
    return read_bytes + write_bytes


def _non_hbm_energy_mj(row: JsonDict) -> float:
    components = row.get("energy_components") if isinstance(row.get("energy_components"), dict) else {}
    if components:
        return sum(_as_float(value) for key, value in components.items() if key != "hbm_mj")
    return max(0.0, _as_float(row.get("energy_mj")) - _as_float(row.get("hbm_dram_energy", {}).get("energy_mj")))


def _calibrated_row(row: JsonDict, ref: JsonDict) -> JsonDict:
    hbm_bytes = _hbm_bytes(row)
    hbm_energy_pj = hbm_bytes * _as_float(ref["hbm_energy_pj_per_byte"])
    hbm_energy_mj = hbm_energy_pj / 1_000_000_000.0
    components = dict(row.get("energy_components") or {})
    components["hbm_mj"] = hbm_energy_mj
    if not components:
        components = {
            "compute_mj": _non_hbm_energy_mj(row),
            "hbm_mj": hbm_energy_mj,
        }
    total_energy_mj = sum(_as_float(value) for value in components.values())
    dominant = max(components.items(), key=lambda item: _as_float(item[1]))[0].replace("_mj", "")
    out = dict(row)
    out.update(
        {
            "arch_id": "hbm_energy_calibrated_frontier",
            "source_candidate_id": _candidate_id(row),
            "latency_us": _as_float(row.get("latency_us")),
            "token_throughput_per_s": _tokens_per_s(_as_float(row.get("latency_us"))),
            "energy_mj": total_energy_mj,
            "energy_status": "source_backed_aggregate_hbm_energy_not_stack_current_signoff",
            "dominant_energy_component": dominant,
            "energy_components": components,
            "hbm_energy_calibration": {
                "measurement_id": ref["measurement_id"],
                "external_design_id": ref["external_design_id"],
                "hbm_energy_pj_per_byte": ref["hbm_energy_pj_per_byte"],
                "hbm_energy_pj_per_bit": ref["hbm_energy_pj_per_bit"],
                "hbm_bytes": hbm_bytes,
                "hbm_energy_mj": hbm_energy_mj,
            },
        }
    )
    return out


def _frontier_family(row: JsonDict) -> str:
    return (
        f"die{_as_float(row.get('die_area_mm2')):g}:"
        f"kv{int(_as_float(row.get('kv_bits')))}:"
        f"{row.get('kv_sharing', 'kv')}:"
        f"tt{int(_as_float(row.get('tile_tokens')))}"
    )


def build_payload(args: argparse.Namespace) -> JsonDict:
    hbm_dram_service = _load_json(args.hbm_dram_service_energy_json)
    external_measurements = _registry_records(args.external_measurements)
    comparison_claims = _registry_records(args.comparison_claims)
    claim = _require_claim(comparison_claims)
    refs = _energy_refs(external_measurements)
    if not refs:
        raise RuntimeError("no HBM energy pJ/byte external references found")
    rows = _source_rows(hbm_dram_service)
    if not rows:
        raise RuntimeError("no HBM/DRAM service rows found")

    sweeps: list[JsonDict] = []
    for ref in refs:
        calibrated = [_calibrated_row(row, ref) for row in rows]
        energy_best = min(calibrated, key=lambda row: (_as_float(row["energy_mj"]), _as_float(row["latency_us"])))
        latency_best = min(calibrated, key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"])))
        sweeps.append(
            {
                "measurement_id": ref["measurement_id"],
                "hbm_energy_pj_per_bit": ref["hbm_energy_pj_per_bit"],
                "hbm_energy_pj_per_byte": ref["hbm_energy_pj_per_byte"],
                "latency_best": latency_best,
                "energy_best": energy_best,
                "dominant_energy_component_at_energy_best": energy_best["dominant_energy_component"],
                "calibrated_rows": sorted(
                    calibrated,
                    key=lambda row: (_as_float(row["latency_us"]), _as_float(row["energy_mj"])),
                ),
            }
        )

    primary = next(
        (sweep for sweep in sweeps if sweep["measurement_id"] == args.primary_measurement_id),
        min(sweeps, key=lambda sweep: abs(_as_float(sweep["hbm_energy_pj_per_bit"]) - 3.97)),
    )
    best = dict(primary["energy_best"])
    best["arch_id"] = "hbm_energy_calibrated_best"
    previous_best = hbm_dram_service.get("best") if isinstance(hbm_dram_service.get("best"), dict) else {}
    previous_family = _frontier_family(previous_best)
    calibrated_family = _frontier_family(best)
    frontier_changed = previous_family != calibrated_family
    dominant_changed = str(previous_best.get("dominant_energy_component")) != str(best.get("dominant_energy_component"))
    decision = (
        "hbm_energy_calibration_changes_energy_frontier"
        if frontier_changed
        else "hbm_energy_calibration_preserves_energy_frontier"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_hbm_energy_calibration_llama7b_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "primary_measurement_id": primary["measurement_id"],
            "previous_hbm_dram_service_energy_best": _candidate_id(previous_best),
            "calibrated_energy_best": _candidate_id(best),
            "previous_energy_family": previous_family,
            "calibrated_energy_family": calibrated_family,
            "energy_frontier_changed_vs_hbm_dram_service": frontier_changed,
            "dominant_energy_component_changed": dominant_changed,
            "recommended_next_step": (
                "If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with "
                "a stack-current/controller-calibrated HBM model before final energy ranking."
            ),
        },
        "best": best,
        "primary_sweep": primary,
        "calibration_sweeps": sweeps,
        "source_backed_hbm_energy_refs": refs,
        "comparison_claim": {
            "claim_id": claim["claim_id"],
            "confidence": claim["confidence"],
            "conclusion": claim["conclusion"],
        },
        "remaining_abstractions": [
            "HBM energy is calibrated from aggregate source pJ/bit references, not matched stack-current tables.",
            "The calibration preserves the HBM/DRAM service latency model but does not simulate a cycle-accurate controller.",
            "Compute energy remains scaled from the nearest measured dense compute reference until the selected MAC/cycle point is measured.",
            "NoC/SRAM energy remains profile-scaled rather than routed switching or SRAM compiler signoff.",
        ],
        "source_artifacts": {
            "hbm_dram_service_energy_model": hbm_dram_service.get("model"),
            "external_measurements": str(args.external_measurements),
            "comparison_claims": str(args.comparison_claims),
        },
    }


def write_markdown(payload: JsonDict, report: Path) -> None:
    best = payload["best"]
    lines = [
        "# Llama7B HBM Energy Calibration",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- primary_measurement_id: `{payload['diagnosis']['primary_measurement_id']}`",
        f"- previous_energy_family: `{payload['diagnosis']['previous_energy_family']}`",
        f"- calibrated_energy_family: `{payload['diagnosis']['calibrated_energy_family']}`",
        f"- dominant_energy_component_changed: `{payload['diagnosis']['dominant_energy_component_changed']}`",
        "",
        "## Best Point",
        "",
        "| candidate | latency us | throughput tok/s | energy mJ | area mm2 | dominant energy | HBM pJ/bit |",
        "|---|---:|---:|---:|---:|---|---:|",
        "| {source_candidate_id} | {latency_us} | {token_throughput_per_s} | {energy_mj} | {die_area_mm2} | {dominant_energy_component} | {hbm_energy_pj_per_bit} |".format(
            hbm_energy_pj_per_bit=best["hbm_energy_calibration"]["hbm_energy_pj_per_bit"],
            **best,
        ),
        "",
        "## Calibration Sweeps",
        "",
        "| measurement | HBM pJ/bit | energy best | energy mJ | dominant energy |",
        "|---|---:|---|---:|---|",
    ]
    for sweep in payload["calibration_sweeps"]:
        energy_best = sweep["energy_best"]
        lines.append(
            "| {measurement_id} | {hbm_energy_pj_per_bit} | {candidate} | {energy_mj} | {dominant} |".format(
                measurement_id=sweep["measurement_id"],
                hbm_energy_pj_per_bit=sweep["hbm_energy_pj_per_bit"],
                candidate=energy_best["source_candidate_id"],
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
    parser.add_argument("--external-measurements", type=Path, required=True)
    parser.add_argument("--comparison-claims", type=Path, required=True)
    parser.add_argument("--primary-measurement-id", default="hbm2_fgdram_micro2017_access_energy")
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
