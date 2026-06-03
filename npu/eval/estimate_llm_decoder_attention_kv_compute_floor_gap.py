#!/usr/bin/env python3
"""Compare Llama7B HBM-bound compute floors with measured compute PPA."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


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


def _best_measured_by_die(measured_partition: JsonDict) -> dict[float, JsonDict]:
    best: dict[float, JsonDict] = {}
    for row in measured_partition.get("best_by_die", []):
        die = float(row["die_area_mm2"])
        current = best.get(die)
        if current is None or float(row["latency_us"]) < float(current["latency_us"]):
            best[die] = row
    return best


def _candidate_density_rows(measured_compute: JsonDict) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for candidate in measured_compute.get("compute_candidates", []):
        area_mm2 = float(candidate["block_area_um2"]) / 1_000_000.0
        macs = int(candidate["block_macs_per_cycle"])
        clock_ns = float(candidate["block_clock_ns"])
        if area_mm2 <= 0.0 or clock_ns <= 0.0:
            continue
        rows.append(
            {
                "compute_arch": candidate["compute_arch"],
                "block_macs_per_cycle": macs,
                "block_area_mm2": area_mm2,
                "block_clock_ns": clock_ns,
                "block_power_mw": float(candidate["block_power_mw"]),
                "macs_per_cycle_per_mm2": macs / area_mm2,
                "macs_per_second_per_mm2": macs / (clock_ns * 1e-9) / area_mm2,
                "metrics_csv": candidate.get("metrics_csv", ""),
                "metrics_tag": candidate.get("metrics_tag", ""),
                "metrics_param_hash": candidate.get("metrics_param_hash", ""),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["macs_per_cycle_per_mm2"]),
            float(row["block_clock_ns"]),
            str(row["compute_arch"]),
        ),
    )


def _target_rows(
    *,
    target_macs_list: list[int],
    die_area_mm2_list: list[float],
    logic_area_fraction_list: list[float],
    best_density: JsonDict,
) -> list[JsonDict]:
    density = float(best_density["macs_per_cycle_per_mm2"])
    rows: list[JsonDict] = []
    for die in die_area_mm2_list:
        for logic_fraction in logic_area_fraction_list:
            logic_area_mm2 = die * logic_fraction
            for target_macs in target_macs_list:
                required_area_mm2 = target_macs / density
                rows.append(
                    {
                        "die_area_mm2": die,
                        "logic_area_fraction": logic_fraction,
                        "logic_area_mm2": logic_area_mm2,
                        "target_macs_per_cycle": target_macs,
                        "required_macs_per_cycle_per_mm2": target_macs / logic_area_mm2,
                        "best_measured_macs_per_cycle_per_mm2": density,
                        "required_density_multiplier": (target_macs / logic_area_mm2) / density,
                        "required_compute_area_mm2_at_best_measured_density": required_area_mm2,
                        "required_compute_area_fraction_at_best_measured_density": required_area_mm2 / die,
                        "fits_best_measured_density": required_area_mm2 <= logic_area_mm2,
                    }
                )
    return rows


def build_report(
    *,
    compute_sensitivity: JsonDict,
    measured_compute: JsonDict,
    measured_partition: JsonDict,
    target_macs_list: list[int],
    die_area_mm2_list: list[float],
    logic_area_fraction_list: list[float],
) -> JsonDict:
    floors_by_die = _best_hbm_floor_by_die(compute_sensitivity)
    measured_by_die = _best_measured_by_die(measured_partition)
    density_rows = _candidate_density_rows(measured_compute)
    if not density_rows:
        raise RuntimeError("no measured compute density rows found")
    best_density = density_rows[0]
    gap_rows: list[JsonDict] = []
    for die in sorted(set(floors_by_die) & set(measured_by_die)):
        floor = floors_by_die[die]
        measured = measured_by_die[die]
        target_macs = int(floor["macs_per_cycle"])
        measured_macs = int(measured["macs_per_cycle"])
        measured_area_mm2 = float(measured["compute_area_um2"]) / 1_000_000.0
        measured_density = measured_macs / measured_area_mm2 if measured_area_mm2 else 0.0
        target_area_at_measured_density = target_macs / measured_density if measured_density else math.inf
        gap_rows.append(
            {
                "die_area_mm2": die,
                "hbm_floor_macs_per_cycle": target_macs,
                "hbm_floor_vector_ops_per_cycle": int(floor["vector_ops_per_cycle"]),
                "hbm_floor_latency_us": float(floor["latency_us"]),
                "hbm_floor_resource": floor["dominant_tile_resource"],
                "measured_best_arch": measured["compute_arch"],
                "measured_best_replicas": int(measured["compute_replica_count"]),
                "measured_best_clusters": int(measured.get("cluster_count", 1)),
                "measured_best_macs_per_cycle": measured_macs,
                "measured_best_latency_us": float(measured["latency_us"]),
                "measured_best_resource": measured["dominant_tile_resource"],
                "macs_per_cycle_gap": target_macs - measured_macs,
                "throughput_multiplier_to_floor": target_macs / measured_macs if measured_macs else math.inf,
                "measured_compute_area_mm2": measured_area_mm2,
                "measured_macs_per_cycle_per_mm2": measured_density,
                "target_compute_area_mm2_at_measured_density": target_area_at_measured_density,
                "target_compute_area_fraction_at_measured_density": target_area_at_measured_density / die,
            }
        )
    target_sizing = _target_rows(
        target_macs_list=target_macs_list,
        die_area_mm2_list=die_area_mm2_list,
        logic_area_fraction_list=logic_area_fraction_list,
        best_density=best_density,
    )
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_compute_floor_gap_v1",
        "inputs": {
            "target_macs_per_cycle_list": target_macs_list,
            "die_area_mm2_list": die_area_mm2_list,
            "logic_area_fraction_list": logic_area_fraction_list,
        },
        "hbm_floor_by_die": [floors_by_die[die] for die in sorted(floors_by_die)],
        "measured_best_by_die": [measured_by_die[die] for die in sorted(measured_by_die)],
        "compute_density_rows": density_rows,
        "gap_by_die": gap_rows,
        "target_sizing_at_best_measured_density": target_sizing,
        "summary": {
            "best_measured_density_arch": best_density["compute_arch"],
            "best_measured_macs_per_cycle_per_mm2": best_density["macs_per_cycle_per_mm2"],
            "max_measured_macs_per_cycle": max(int(row["macs_per_cycle"]) for row in measured_by_die.values()),
            "min_hbm_floor_macs_per_cycle": min((int(row["macs_per_cycle"]) for row in floors_by_die.values()), default=0),
            "all_measured_points_below_hbm_floor": all(
                int(measured_by_die[die]["macs_per_cycle"]) < int(floors_by_die[die]["macs_per_cycle"])
                for die in set(floors_by_die) & set(measured_by_die)
            ),
        },
        "assumptions": [
            "The HBM floor comes from the merged physical HBM compute-sensitivity planning model.",
            "Measured compute rows come from merged NPU compute PPA and measured-compute partition reports.",
            "Density is reported as MAC/cycle per mm2 of measured compute block area; it is not a replacement for routed large-array timing closure.",
            "A target that fails at best measured density should be treated as a compute-architecture gap before requesting detailed global NoC simulation.",
        ],
    }


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _write_markdown(path: Path, payload: JsonDict) -> None:
    summary = payload["summary"]
    lines = [
        "# Decoder Attention/KV Compute Floor Gap",
        "",
        f"- model: `{payload['model']}`",
        f"- best_measured_density_arch: `{summary['best_measured_density_arch']}`",
        f"- best_measured_macs_per_cycle_per_mm2: `{_fmt(summary['best_measured_macs_per_cycle_per_mm2'])}`",
        f"- max_measured_macs_per_cycle: `{summary['max_measured_macs_per_cycle']}`",
        f"- min_hbm_floor_macs_per_cycle: `{summary['min_hbm_floor_macs_per_cycle']}`",
        f"- all_measured_points_below_hbm_floor: `{summary['all_measured_points_below_hbm_floor']}`",
        "",
        "## Gap By Die",
        "",
        "| die | HBM floor MAC/cyc | measured MAC/cyc | measured arch | clusters | multiplier | target area frac @ measured density | measured resource |",
        "|---:|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in payload["gap_by_die"]:
        lines.append(
            "| {die} | {floor} | {measured} | {arch} | {clusters} | {mult} | {frac} | {res} |".format(
                die=_fmt(float(row["die_area_mm2"])),
                floor=row["hbm_floor_macs_per_cycle"],
                measured=row["measured_best_macs_per_cycle"],
                arch=row["measured_best_arch"],
                clusters=row["measured_best_clusters"],
                mult=_fmt(float(row["throughput_multiplier_to_floor"])),
                frac=_fmt(float(row["target_compute_area_fraction_at_measured_density"])),
                res=row["measured_best_resource"],
            )
        )
    lines.extend(
        [
            "",
            "## Target Sizing At Best Measured Density",
            "",
            "| die | logic frac | target MAC/cyc | required density x | required compute area frac | fits |",
            "|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["target_sizing_at_best_measured_density"]:
        lines.append(
            "| {die} | {logic} | {target} | {mult} | {frac} | {fits} |".format(
                die=_fmt(float(row["die_area_mm2"])),
                logic=_fmt(float(row["logic_area_fraction"])),
                target=row["target_macs_per_cycle"],
                mult=_fmt(float(row["required_density_multiplier"])),
                frac=_fmt(float(row["required_compute_area_fraction_at_best_measured_density"])),
                fits=row["fits_best_measured_density"],
            )
        )
    lines.extend(
        [
            "",
            "## Top Measured Compute Density Rows",
            "",
            "| arch | MAC/cyc | area mm2 | clock ns | MAC/cyc/mm2 | metrics |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["compute_density_rows"][:10]:
        lines.append(
            "| {arch} | {macs} | {area} | {clock} | {density} | `{metrics}` |".format(
                arch=row["compute_arch"],
                macs=row["block_macs_per_cycle"],
                area=_fmt(float(row["block_area_mm2"])),
                clock=_fmt(float(row["block_clock_ns"])),
                density=_fmt(float(row["macs_per_cycle_per_mm2"])),
                metrics=row["metrics_csv"],
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
    parser.add_argument("--measured-partition", required=True)
    parser.add_argument("--target-macs-per-cycle-list", type=_int_list, default=[131072, 262144, 524288])
    parser.add_argument("--die-area-mm2-list", type=_float_list, default=[400, 800, 1200])
    parser.add_argument("--logic-area-fraction-list", type=_float_list, default=[0.2, 0.4, 0.6])
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    payload = build_report(
        compute_sensitivity=_load_json(args.compute_sensitivity),
        measured_compute=_load_json(args.measured_compute),
        measured_partition=_load_json(args.measured_partition),
        target_macs_list=args.target_macs_per_cycle_list,
        die_area_mm2_list=args.die_area_mm2_list,
        logic_area_fraction_list=args.logic_area_fraction_list,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
