#!/usr/bin/env python3
"""Bound Llama7B attention/KV estimates by physically plausible compute density envelopes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


def _registry_records(path: str) -> list[JsonDict]:
    records: list[JsonDict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _best_hbm_floor_by_die(compute_sensitivity: JsonDict) -> dict[float, JsonDict]:
    floors: dict[float, JsonDict] = {}
    for row in compute_sensitivity.get("best_by_compute", []):
        if str(row.get("dominant_tile_resource")) != "hbm":
            continue
        die = float(row["die_area_mm2"])
        current = floors.get(die)
        key = (
            int(row["macs_per_cycle"]),
            int(row["vector_ops_per_cycle"]),
            float(row["latency_us"]),
        )
        if current is None:
            floors[die] = row
            continue
        current_key = (
            int(current["macs_per_cycle"]),
            int(current["vector_ops_per_cycle"]),
            float(current["latency_us"]),
        )
        if key < current_key:
            floors[die] = row
    return floors


def _best_rows_by_die(compute_sensitivity: JsonDict) -> dict[float, list[JsonDict]]:
    rows_by_die: dict[float, list[JsonDict]] = {}
    for row in compute_sensitivity.get("best_by_compute", []):
        die = float(row["die_area_mm2"])
        rows_by_die.setdefault(die, []).append(row)
    for rows in rows_by_die.values():
        rows.sort(key=lambda row: (float(row["latency_us"]), -int(row["macs_per_cycle"])))
    return rows_by_die


def _best_density(measured_compute: JsonDict) -> JsonDict:
    best: JsonDict | None = None
    for candidate in measured_compute.get("compute_candidates", []):
        area_mm2 = float(candidate["block_area_um2"]) / 1_000_000.0
        macs = int(candidate["block_macs_per_cycle"])
        clock_ns = float(candidate["block_clock_ns"])
        if area_mm2 <= 0.0 or clock_ns <= 0.0:
            continue
        row = {
            "source": "rtlgen_measured",
            "label": candidate["compute_arch"],
            "macs_per_cycle_per_mm2": macs / area_mm2,
            "macs_per_second_per_mm2": macs / (clock_ns * 1e-9) / area_mm2,
            "block_macs_per_cycle": macs,
            "block_area_mm2": area_mm2,
            "block_clock_ns": clock_ns,
            "block_power_mw": float(candidate["block_power_mw"]),
            "metrics_csv": candidate.get("metrics_csv", ""),
            "metrics_tag": candidate.get("metrics_tag", ""),
            "metrics_param_hash": candidate.get("metrics_param_hash", ""),
        }
        if best is None or (
            float(row["macs_per_cycle_per_mm2"]),
            -float(row["block_clock_ns"]),
            str(row["label"]),
        ) > (
            float(best["macs_per_cycle_per_mm2"]),
            -float(best["block_clock_ns"]),
            str(best["label"]),
        ):
            best = row
    if best is None:
        raise RuntimeError("no measured compute candidates found")
    return best


def _external_density_rows(external_measurements: list[JsonDict]) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for record in external_measurements:
        derived = record.get("derived", {})
        density = derived.get("ideal_scaled_mac_per_cycle_per_mm2_to_45nm")
        if density is None:
            density = derived.get("ideal_scaled_mac_equiv_per_cycle_per_mm2_to_45nm")
        if density is None:
            density = derived.get("ideal_scaled_mac_per_cycle_per_mm2_to_45nm_lower_bound")
        if density is None:
            continue
        rows.append(
            {
                "source": "external_reference",
                "measurement_id": record["measurement_id"],
                "external_design_id": record["external_design_id"],
                "macs_per_cycle_per_mm2_to_45nm": float(density),
                "comparability_class": record["comparability"]["class"],
                "comparability_reason": record["comparability"]["reason"],
                "normalization": record.get("normalization", {}),
            }
        )
    return sorted(rows, key=lambda row: -float(row["macs_per_cycle_per_mm2_to_45nm"]))


def _select_best_under_ceiling(rows: list[JsonDict], ceiling_macs: int) -> JsonDict | None:
    eligible = [row for row in rows if int(row["macs_per_cycle"]) <= ceiling_macs]
    if not eligible:
        return None
    return min(eligible, key=lambda row: (float(row["latency_us"]), -int(row["macs_per_cycle"])))


def build_report(
    *,
    compute_sensitivity: JsonDict,
    measured_compute: JsonDict,
    internal_measurements: list[JsonDict],
    external_measurements: list[JsonDict],
    comparison_claims: list[JsonDict],
    density_envelope_list: list[float],
    die_area_mm2_list: list[float],
    logic_area_fraction_list: list[float],
    vector_ops_per_mac: float,
) -> JsonDict:
    floors_by_die = _best_hbm_floor_by_die(compute_sensitivity)
    rows_by_die = _best_rows_by_die(compute_sensitivity)
    measured_best = _best_density(measured_compute)
    external_density = _external_density_rows(external_measurements)
    required_internal_measurements = {
        "rtlgen_npu_fp16_nm64_flat_cmp33_nangate45",
        "rtlgen_llama7b_attention_kv_compute_floor_gap_v1",
    }
    required_comparison_claims = {
        "rtlgen_llama7b_compute_density_gap_vs_external_refs_v1",
    }
    found_internal_measurements = {
        record["measurement_id"]
        for record in internal_measurements
        if record.get("measurement_id") in required_internal_measurements
    }
    found_comparison_claims = {
        record["claim_id"]
        for record in comparison_claims
        if record.get("claim_id") in required_comparison_claims
    }
    missing_internal = sorted(required_internal_measurements - found_internal_measurements)
    missing_claims = sorted(required_comparison_claims - found_comparison_claims)
    if missing_internal:
        raise RuntimeError(f"missing required internal registry measurements: {missing_internal}")
    if missing_claims:
        raise RuntimeError(f"missing required registry comparison claims: {missing_claims}")
    if not external_density:
        raise RuntimeError("no external density references found in registry")

    envelope_sources: list[JsonDict] = [
        {
            "label": "rtlgen_measured_best",
            "macs_per_cycle_per_mm2": measured_best["macs_per_cycle_per_mm2"],
            "source_measurement_id": "rtlgen_npu_fp16_nm64_flat_cmp33_nangate45",
            "comparability_class": "direct_comparable",
        }
    ]
    for density in density_envelope_list:
        envelope_sources.append(
            {
                "label": f"density_{density:g}_mac_per_cycle_per_mm2",
                "macs_per_cycle_per_mm2": density,
                "source_measurement_id": "",
                "comparability_class": "analytic_envelope",
            }
        )

    frontier_rows: list[JsonDict] = []
    for die in die_area_mm2_list:
        die_rows = rows_by_die.get(die, [])
        floor = floors_by_die.get(die)
        floor_macs = int(floor["macs_per_cycle"]) if floor else 0
        for logic_fraction in logic_area_fraction_list:
            logic_area_mm2 = die * logic_fraction
            for envelope in envelope_sources:
                density = float(envelope["macs_per_cycle_per_mm2"])
                ceiling_macs = max(1, int(math.floor(logic_area_mm2 * density)))
                vector_ceiling = max(1, int(math.floor(ceiling_macs * vector_ops_per_mac)))
                selected = _select_best_under_ceiling(die_rows, ceiling_macs)
                frontier_rows.append(
                    {
                        "die_area_mm2": die,
                        "logic_area_fraction": logic_fraction,
                        "logic_area_mm2": logic_area_mm2,
                        "density_label": envelope["label"],
                        "density_source_measurement_id": envelope["source_measurement_id"],
                        "density_comparability_class": envelope["comparability_class"],
                        "macs_per_cycle_per_mm2": density,
                        "compute_ceiling_macs_per_cycle": ceiling_macs,
                        "compute_ceiling_vector_ops_per_cycle": vector_ceiling,
                        "hbm_floor_macs_per_cycle": floor_macs,
                        "reaches_hbm_floor": bool(floor_macs and ceiling_macs >= floor_macs),
                        "selected_sensitivity_row_found": selected is not None,
                        "selected_macs_per_cycle": int(selected["macs_per_cycle"]) if selected else None,
                        "selected_vector_ops_per_cycle": int(selected["vector_ops_per_cycle"]) if selected else None,
                        "selected_latency_us": float(selected["latency_us"]) if selected else None,
                        "selected_dominant_resource": selected.get("dominant_tile_resource") if selected else "",
                        "selected_hbm_byte_share": float(selected["hbm_byte_share"]) if selected else None,
                    }
                )

    reachable = [row for row in frontier_rows if row["reaches_hbm_floor"]]
    best_rows = [row for row in frontier_rows if row["selected_sensitivity_row_found"]]
    best_latency = min(best_rows, key=lambda row: float(row["selected_latency_us"])) if best_rows else None
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_compute_ceiling_envelope_v1",
        "inputs": {
            "density_envelope_macs_per_cycle_per_mm2_list": density_envelope_list,
            "die_area_mm2_list": die_area_mm2_list,
            "logic_area_fraction_list": logic_area_fraction_list,
            "vector_ops_per_mac": vector_ops_per_mac,
        },
        "registry_evidence": {
            "required_internal_measurements": sorted(required_internal_measurements),
            "external_reference_measurements": [
                row["measurement_id"] for row in external_density
            ],
            "comparison_claims": sorted(required_comparison_claims),
            "internal_measurement_records_found": sorted(found_internal_measurements),
            "comparison_claim_records_found": sorted(found_comparison_claims),
        },
        "measured_best_density": measured_best,
        "external_density_references": external_density,
        "hbm_floor_by_die": [floors_by_die[die] for die in sorted(floors_by_die)],
        "frontier_rows": frontier_rows,
        "summary": {
            "measured_best_density_macs_per_cycle_per_mm2": measured_best["macs_per_cycle_per_mm2"],
            "measured_best_density_label": measured_best["label"],
            "hbm_floor_reachable_row_count": len(reachable),
            "best_latency_under_any_envelope_us": (
                float(best_latency["selected_latency_us"]) if best_latency else None
            ),
            "best_latency_density_label": best_latency["density_label"] if best_latency else "",
            "best_latency_die_area_mm2": best_latency["die_area_mm2"] if best_latency else None,
            "best_latency_logic_area_fraction": best_latency["logic_area_fraction"] if best_latency else None,
        },
        "assumptions": [
            "Compute ceilings are calculated as die_area_mm2 * logic_area_fraction * density_envelope.",
            "The selected latency is taken from the merged compute-sensitivity sweep row whose MAC/cycle does not exceed the ceiling.",
            "External density rows are calibration references, not direct ranking baselines.",
            "Ideal node scaling is optimistic and does not include routing, voltage, SRAM, timing, or workload-utilization effects.",
        ],
    }


def _fmt(value: float | int | None) -> str:
    if value is None:
        return ""
    return f"{float(value):.6g}"


def _write_markdown(path: Path, payload: JsonDict) -> None:
    summary = payload["summary"]
    evidence = payload["registry_evidence"]
    lines = [
        "# Decoder Attention/KV Compute Ceiling Envelope",
        "",
        f"- model: `{payload['model']}`",
        f"- measured_best_density: `{_fmt(summary['measured_best_density_macs_per_cycle_per_mm2'])}` MAC/cycle/mm2",
        f"- measured_best_density_label: `{summary['measured_best_density_label']}`",
        f"- hbm_floor_reachable_row_count: `{summary['hbm_floor_reachable_row_count']}`",
        f"- best_latency_under_any_envelope_us: `{_fmt(summary['best_latency_under_any_envelope_us'])}`",
        "",
        "## Registry Evidence",
        "",
        "Internal measurements:",
    ]
    lines.extend(f"- `{item}`" for item in evidence["required_internal_measurements"])
    lines.append("")
    lines.append("External references:")
    lines.extend(f"- `{item}`" for item in evidence["external_reference_measurements"])
    lines.append("")
    lines.append("Comparison claims:")
    lines.extend(f"- `{item}`" for item in evidence["comparison_claims"])

    lines.extend(
        [
            "",
            "## Envelope Frontier",
            "",
            "| die | logic frac | density label | ceiling MAC/cyc | HBM floor MAC/cyc | reaches HBM | selected MAC/cyc | latency us | resource |",
            "|---:|---:|---|---:|---:|---|---:|---:|---|",
        ]
    )
    for row in payload["frontier_rows"]:
        lines.append(
            "| {die} | {logic} | {label} | {ceiling} | {floor} | {reaches} | {sel} | {lat} | {res} |".format(
                die=_fmt(row["die_area_mm2"]),
                logic=_fmt(row["logic_area_fraction"]),
                label=row["density_label"],
                ceiling=row["compute_ceiling_macs_per_cycle"],
                floor=row["hbm_floor_macs_per_cycle"],
                reaches=row["reaches_hbm_floor"],
                sel=row["selected_macs_per_cycle"] or "",
                lat=_fmt(row["selected_latency_us"]),
                res=row["selected_dominant_resource"],
            )
        )

    lines.extend(
        [
            "",
            "## External Density References",
            "",
            "| measurement | 45nm-scaled MAC/cyc/mm2 | comparability |",
            "|---|---:|---|",
        ]
    )
    for row in payload["external_density_references"]:
        lines.append(
            "| `{measurement}` | {density} | {klass} |".format(
                measurement=row["measurement_id"],
                density=_fmt(row["macs_per_cycle_per_mm2_to_45nm"]),
                klass=row["comparability_class"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compute-sensitivity", required=True)
    parser.add_argument("--measured-compute", required=True)
    parser.add_argument("--internal-measurements", required=True)
    parser.add_argument("--external-measurements", required=True)
    parser.add_argument("--comparison-claims", required=True)
    parser.add_argument("--density-envelope-macs-per-cycle-per-mm2-list", type=_float_list, default=[150, 300])
    parser.add_argument("--die-area-mm2-list", type=_float_list, default=[400, 800, 1200])
    parser.add_argument("--logic-area-fraction-list", type=_float_list, default=[0.2, 0.4, 0.6])
    parser.add_argument("--vector-ops-per-mac", type=float, default=0.125)
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    if args.vector_ops_per_mac <= 0.0:
        parser.error("--vector-ops-per-mac must be positive")

    payload = build_report(
        compute_sensitivity=_load_json(args.compute_sensitivity),
        measured_compute=_load_json(args.measured_compute),
        internal_measurements=_registry_records(args.internal_measurements),
        external_measurements=_registry_records(args.external_measurements),
        comparison_claims=_registry_records(args.comparison_claims),
        density_envelope_list=args.density_envelope_macs_per_cycle_per_mm2_list,
        die_area_mm2_list=args.die_area_mm2_list,
        logic_area_fraction_list=args.logic_area_fraction_list,
        vector_ops_per_mac=args.vector_ops_per_mac,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
