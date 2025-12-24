#!/usr/bin/env python3
"""
Compare ILP Normal multipliers vs Yosys LowpowerBooth (signed only) by
normalizing ILP metrics to the Yosys lowpower baseline per matching config
(platform, width). Outputs plots under runs/analysis/.
"""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

ILP_ROOT = Path('runs/multipliers/ppg_cpa_widths_4_32')
YOSYS_ROOT = Path('runs/multipliers/yosys_booth_widths_4_32')
OUT_DIR = Path('runs/analysis')
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTHS = [4, 8, 16, 32]
CPAS = ["ripple", "brentkung", "koggestone", "sklansky"]


def parse_ilp_name(name: str):
    base = name.replace('mult', '')
    parts = base.split('_')
    width_signed = parts[0]
    ppg = parts[1]
    cpa = parts[2]
    width = int(width_signed[:-1])
    signed = width_signed[-1]
    return width, signed, ppg, cpa


def parse_yosys_name(name: str):
    base = name.replace('yosys_mult', '').replace('_wrapper', '')
    parts = base.split('_')
    width_signed = parts[0]
    booth = parts[1]
    width = int(width_signed[:-1])
    signed = width_signed[-1]
    return width, signed, booth.lower()


def load_best(path: Path, metric_field: str):
    rows = []
    with path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                val = float(row[metric_field])
            except Exception:
                continue
            rows.append(row | {metric_field: val})
    return rows


# Load ILP bests (Normal PPG only)
ilp_best = load_best(ILP_ROOT / 'best_area_highutil.csv', 'die_area')
ilp_delay = {
    (r['design'], r['platform']): float(r['critical_path_ns'])
    for r in load_best(ILP_ROOT / 'best_delay_all.csv', 'critical_path_ns')
}
ilp_power = {
    (r['design'], r['platform']): float(r['total_power_mw'])
    for r in load_best(ILP_ROOT / 'best_power_all.csv', 'total_power_mw')
}

# Load Yosys lowpower bests
ys_best = load_best(YOSYS_ROOT / 'best_area_highutil.csv', 'die_area')
ys_delay = {
    (r['design'], r['platform']): float(r['critical_path_ns'])
    for r in load_best(YOSYS_ROOT / 'best_delay_all.csv', 'critical_path_ns')
}
ys_power = {
    (r['design'], r['platform']): float(r['total_power_mw'])
    for r in load_best(YOSYS_ROOT / 'best_power_all.csv', 'total_power_mw')
}


def match_pairs():
    pairs = []
    ys_map = {}
    for r in ys_best:
        width, signed, booth_kind = parse_yosys_name(r['design'])
        if booth_kind == 'lowpowerbooth' and signed == 's':
            ys_map[(width, r['platform'])] = r
    for r in ilp_best:
        width, signed, ppg, cpa = parse_ilp_name(r['design'])
        if ppg != 'normal' or signed != 's':
            continue
        ys_row = ys_map.get((width, r['platform']))
        if ys_row:
            pairs.append((r, ys_row, cpa))
    return pairs


pairs = match_pairs()

metrics = defaultdict(lambda: defaultdict(list))
for ilp_row, ys_row, cpa in pairs:
    plat = ilp_row['platform']
    width, _, _, _ = parse_ilp_name(ilp_row['design'])
    base_key = (plat, 'signed')
    # area
    a_ilp = float(ilp_row['die_area'])
    a_ys = float(ys_row['die_area'])
    if a_ys > 0:
        metrics['area'][base_key].append((width, cpa, a_ilp / a_ys))
    # delay
    d_ilp = ilp_delay.get((ilp_row['design'], plat))
    d_ys = ys_delay.get((ys_row['design'], plat))
    if d_ilp and d_ys:
        metrics['delay'][base_key].append((width, cpa, d_ilp / d_ys))
    # power
    p_ilp = ilp_power.get((ilp_row['design'], plat))
    p_ys = ys_power.get((ys_row['design'], plat))
    if p_ilp and p_ys:
        metrics['power'][base_key].append((width, cpa, p_ilp / p_ys))


for metric_name, data in metrics.items():
    for (plat, sign_lbl), pts in data.items():
        fig, ax = plt.subplots(figsize=(7, 4))
        for cpa in CPAS:
            sub = [(w, v) for (w, c, v) in pts if c == cpa]
            if not sub:
                continue
            sub = sorted(sub, key=lambda x: x[0])
            xs, ys = zip(*sub)
            ax.plot(xs, ys, marker='o', label=f"{cpa}")
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, label='Yosys baseline')
        ax.set_title(f"ILP Normal / Yosys LowpowerBooth ({plat}, {sign_lbl}) — {metric_name}")
        ax.set_xlabel("Bit width")
        ax.set_ylabel(f"Normalized {metric_name} (ILP / Yosys)")
        ax.set_xticks(WIDTHS)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize='small', ncol=2)
        out_path = OUT_DIR / f"ilp_normal_over_yosys_lowpower_{metric_name}_{plat}_{sign_lbl}.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=200)
        plt.close(fig)

print("done")
