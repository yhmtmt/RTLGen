#!/usr/bin/env python3
"""
Generate normalized PPA plots comparing Booth4 vs Normal partial-product generators
across CPAs and platforms. Metrics are normalized per width/signedness to the
Normal + Ripple baseline for that platform.

Inputs (already in the repo):
- runs/multipliers/ppg_cpa_widths_4_32/best_area_highutil.csv
- runs/multipliers/ppg_cpa_widths_4_32/best_delay_all.csv
- runs/multipliers/ppg_cpa_widths_4_32/best_power_all.csv

Outputs (written next to this script):
- area_normalized_<platform>.png
- delay_normalized_<platform>.png
- power_normalized_<platform>.png
"""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1] / "multipliers" / "ppg_cpa_widths_4_32"
OUT_DIR = Path(__file__).resolve().parent

AREA_FILE = ROOT / "best_area_highutil.csv"
DELAY_FILE = ROOT / "best_delay_all.csv"
POWER_FILE = ROOT / "best_power_all.csv"

WIDTHS = [4, 8, 16, 32]
CPAS = ["ripple", "brentkung", "koggestone", "sklansky"]
PPGS = ["normal", "booth4"]


def parse_design(design: str):
    # mult16s_normal_ripple_wrapper -> (16, 's', 'normal', 'ripple')
    base = design.replace("mult", "")
    parts = base.split("_")
    if len(parts) < 3:
        raise ValueError(f"Unexpected design name: {design}")
    width_signed = parts[0]
    ppg = parts[1]
    cpa = parts[2]
    width = int(width_signed[:-1])
    signed = width_signed[-1]
    return width, signed, ppg, cpa


def load_metric(path: Path, metric_field: str):
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            design = row["design"]
            platform = row["platform"]
            try:
                width, signed, ppg, cpa = parse_design(design)
            except Exception:
                continue
            try:
                value = float(row[metric_field])
            except Exception:
                continue
            rows.append(
                {
                    "platform": platform,
                    "width": width,
                    "signed": signed,
                    "ppg": ppg,
                    "cpa": cpa,
                    "value": value,
                }
            )
    return rows


def normalize(rows):
    # baseline per (platform, width, signed, cpa): normal PPG with same CPA
    baseline = {}
    for r in rows:
        if r["ppg"] == "normal":
            baseline[(r["platform"], r["width"], r["signed"], r["cpa"])] = r["value"]
    norm_rows = []
    for r in rows:
        key = (r["platform"], r["width"], r["signed"], r["cpa"])
        base = baseline.get(key)
        if base is None or base == 0:
            continue
        norm_rows.append({**r, "norm": r["value"] / base})
    return norm_rows


def plot_metric(norm_rows, metric_name: str):
    # Group by platform and signedness
    by_platform_signed = defaultdict(list)
    for r in norm_rows:
        by_platform_signed[(r["platform"], r["signed"])].append(r)

    for (platform, signed), rows in by_platform_signed.items():
        fig, ax = plt.subplots(figsize=(7, 4))
        for cpa in CPAS:
            pts = []
            for width in WIDTHS:
                vals = [
                    r["norm"]
                    for r in rows
                    if r["ppg"] == "booth4" and r["cpa"] == cpa and r["width"] == width
                ]
                if vals:
                    pts.append((width, sum(vals) / len(vals)))
            if not pts:
                continue
            pts = sorted(pts, key=lambda x: x[0])
            xs, ys = zip(*pts)
            label = f"booth4-{cpa}"
            ax.plot(xs, ys, marker="o", label=label)
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="baseline (normal same CPA)")
        sign_lbl = "signed" if signed == "s" else "unsigned"
        ax.set_title(f"{metric_name} normalized to normal (same CPA) ({platform}, {sign_lbl})")
        ax.set_xlabel("Bit width")
        ax.set_ylabel("Normalized " + metric_name)
        ax.set_xticks(WIDTHS)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(fontsize="small", ncol=2)
        out_path = OUT_DIR / f"{metric_name.lower()}_normalized_{platform}_{sign_lbl}.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=200)
        plt.close(fig)


def main():
    area_rows = normalize(load_metric(AREA_FILE, "die_area"))
    delay_rows = normalize(load_metric(DELAY_FILE, "critical_path_ns"))
    power_rows = normalize(load_metric(POWER_FILE, "total_power_mw"))

    plot_metric(area_rows, "Area")
    plot_metric(delay_rows, "Delay")
    plot_metric(power_rows, "Power")


if __name__ == "__main__":
    main()
