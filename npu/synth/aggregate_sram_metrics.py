#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def summarize_metrics(metrics_path: Path):
    data = json.loads(metrics_path.read_text())
    instances = data.get("instances", [])

    total_area_um2 = 0.0
    total_read_energy_pj = 0.0
    total_write_energy_pj = 0.0
    max_access_time_ns = 0.0
    missing = []

    for entry in instances:
        if not entry.get("estimated"):
            missing.append(entry.get("instance", {}).get("name", "unknown"))
            continue
        metrics = entry.get("metrics", {})
        area = metrics.get("area_um2")
        read_energy = metrics.get("read_energy_pj")
        write_energy = metrics.get("write_energy_pj")
        access_time = metrics.get("access_time_ns")
        if area is not None:
            total_area_um2 += float(area)
        if read_energy is not None:
            total_read_energy_pj += float(read_energy)
        if write_energy is not None:
            total_write_energy_pj += float(write_energy)
        if access_time is not None:
            max_access_time_ns = max(max_access_time_ns, float(access_time))

    summary = {
        "total_area_um2": total_area_um2,
        "total_read_energy_pj": total_read_energy_pj,
        "total_write_energy_pj": total_write_energy_pj,
        "max_access_time_ns": max_access_time_ns,
        "missing_instances": missing,
        "instance_count": len(instances),
        "estimated_count": len(instances) - len(missing),
    }
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate SRAM metrics into a single summary."
    )
    parser.add_argument(
        "--id",
        required=True,
        help="Design ID (used under runs/designs/sram/<id>).",
    )
    parser.add_argument(
        "--root",
        default="runs/designs/sram",
        help="Root path for SRAM metrics.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    design_dir = root / args.id
    metrics_path = design_dir / "sram_metrics.json"
    if not metrics_path.exists():
        raise SystemExit(f"Missing SRAM metrics: {metrics_path}")

    summary = summarize_metrics(metrics_path)
    summary_path = design_dir / "sram_metrics_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote SRAM summary: {summary_path}")


if __name__ == "__main__":
    main()
