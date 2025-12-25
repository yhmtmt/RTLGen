#!/usr/bin/env python3
"""
Compare ILP Booth multipliers vs Yosys Booth (and lowpower) by normalizing ILP metrics to Yosys baseline per matching config (platform, width, signed, CPA where applicable).
For Yosys lowpower (signed-only), compare against ILP signed designs.
Outputs plots under analysis/ comparing area/delay/power.
"""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

ILP_ROOT = Path('runs/campaigns/multipliers/ppg_cpa_widths_4_32')
YOSYS_ROOT = Path('runs/campaigns/multipliers/yosys_booth_widths_4_32')
OUT_DIR = Path('analysis')
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTHS = [4,8,16,32]
CPAS = ["ripple","brentkung","koggestone","sklansky"]

# Map ILP design name -> (width,signed,ppg,cpa)
def parse_ilp_name(name:str):
    base = name.replace('mult','')
    parts = base.split('_')
    width_signed = parts[0]
    ppg = parts[1]
    cpa = parts[2]
    width = int(width_signed[:-1])
    signed = width_signed[-1]
    return width, signed, ppg, cpa

# Map Yosys design -> (width,signed,booth_kind)
def parse_yosys_name(name:str):
    # yosys_mult16s_booth_wrapper
    base = name.replace('yosys_mult','').replace('_wrapper','')
    parts = base.split('_')
    width_signed = parts[0]
    booth = parts[1]
    width = int(width_signed[:-1])
    signed = width_signed[-1]
    return width, signed, booth.lower()


def load_best(path:Path, metric_field:str):
    rows = []
    with path.open() as f:
        r=csv.DictReader(f)
        for row in r:
            try:
                val=float(row[metric_field])
            except Exception:
                continue
            rows.append(row | {metric_field: val})
    return rows

# Load ILP bests
ilp_best = load_best(ILP_ROOT/'best_area_highutil.csv','die_area')
ilp_delay = { (r['design'],r['platform']):float(r['critical_path_ns']) for r in load_best(ILP_ROOT/'best_delay_all.csv','critical_path_ns') }
ilp_power = { (r['design'],r['platform']):float(r['total_power_mw']) for r in load_best(ILP_ROOT/'best_power_all.csv','total_power_mw') }

# Load Yosys bests
ys_best = load_best(YOSYS_ROOT/'best_area_highutil.csv','die_area')
ys_delay = { (r['design'],r['platform']):float(r['critical_path_ns']) for r in load_best(YOSYS_ROOT/'best_delay_all.csv','critical_path_ns') }
ys_power = { (r['design'],r['platform']):float(r['total_power_mw']) for r in load_best(YOSYS_ROOT/'best_power_all.csv','total_power_mw') }

def match_pairs():
    pairs = []
    ys_map = {}
    for r in ys_best:
        width, signed, booth_kind = parse_yosys_name(r['design'])
        ys_map[(width,signed,r['platform'],booth_kind)] = r
    for r in ilp_best:
        width,signed,ppg,cpa = parse_ilp_name(r['design'])
        if ppg != 'booth4':
            continue
        key = (width,signed,r['platform'],'booth')
        ys_row = ys_map.get(key)
        if ys_row:
            pairs.append((r, ys_row, cpa, 'booth'))
    # lowpower comparison (signed only)
    for r in ilp_best:
        width,signed,ppg,cpa = parse_ilp_name(r['design'])
        if ppg != 'booth4' or signed != 's':
            continue
        key_lp = (width,signed,r['platform'],'lowpowerbooth')
        ys_row = ys_map.get(key_lp)
        if ys_row:
            pairs.append((r, ys_row, cpa, 'lowpowerbooth'))
    return pairs

pairs = match_pairs()

metrics = defaultdict(lambda: defaultdict(list))
for ilp_row, ys_row, cpa, booth_kind in pairs:
    plat = ilp_row['platform']
    width, signed, _, _ = parse_ilp_name(ilp_row['design'])
    sign_lbl = 'signed' if signed=='s' else 'unsigned'
    base_key = (plat, sign_lbl, booth_kind)
    # area
    a_ilp = float(ilp_row['die_area'])
    a_ys = float(ys_row['die_area'])
    if a_ys>0:
        metrics['area'][base_key].append((width, cpa, a_ilp/a_ys))
    # delay
    d_ilp = ilp_delay.get((ilp_row['design'], plat))
    d_ys = ys_delay.get((ys_row['design'], plat))
    if d_ilp and d_ys:
        metrics['delay'][base_key].append((width, cpa, d_ilp/d_ys))
    # power
    p_ilp = ilp_power.get((ilp_row['design'], plat))
    p_ys = ys_power.get((ys_row['design'], plat))
    if p_ilp and p_ys:
        metrics['power'][base_key].append((width, cpa, p_ilp/p_ys))


for metric_name, data in metrics.items():
    for (plat, sign_lbl, booth_kind), pts in data.items():
        fig, ax = plt.subplots(figsize=(7,4))
        for cpa in CPAS:
            sub = [(w,v) for (w,c,v) in pts if c==cpa]
            if not sub:
                continue
            sub = sorted(sub, key=lambda x:x[0])
            xs, ys = zip(*sub)
            ax.plot(xs, ys, marker='o', label=f"{cpa}")
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, label='Yosys baseline')
        ax.set_title(f"ILP Booth / Yosys {booth_kind} ({plat}, {sign_lbl}) — {metric_name}")
        ax.set_xlabel("Bit width")
        ax.set_ylabel(f"Normalized {metric_name} (ILP / Yosys)")
        ax.set_xticks(WIDTHS)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize='small', ncol=2)
        out_path = OUT_DIR / f"ilp_over_yosys_{metric_name}_{plat}_{sign_lbl}_{booth_kind}.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=200)
        plt.close(fig)

print("done")
