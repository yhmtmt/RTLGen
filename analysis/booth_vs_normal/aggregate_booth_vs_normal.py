import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "runs" / "campaigns" / "multipliers" / "ppg_cpa_widths_4_32"
PLATFORMS = ["nangate45", "sky130hd", "asap7"]


def load_platform(plat: str) -> pd.DataFrame:
    df = pd.read_csv(BASE / f"{plat}_summary.csv")
    df["signed"] = df["signed"].astype(str).map({"True": True, "False": False})
    return df


def compute_delta_by_width(df: pd.DataFrame, plat: str) -> pd.DataFrame:
    # Average Booth4-Normal deltas over CPA and signedness for each width.
    pivot = df.pivot_table(index=["width", "signed", "cpa"], columns="ppg", values=["critical_path_ns", "die_area", "total_power_mw"])
    delta = pivot.xs("booth4", level=1, axis=1) - pivot.xs("normal", level=1, axis=1)
    agg = delta.groupby("width").mean().reset_index()
    agg.insert(0, "platform", plat)
    return agg


def main():
    out_dir = Path(__file__).parent
    records = []
    for plat in PLATFORMS:
        df = load_platform(plat)
        records.append(compute_delta_by_width(df, plat))
    combined = pd.concat(records, ignore_index=True)
    combined.to_csv(out_dir / "delta_by_width.csv", index=False)

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 8.0), sharex=True)
    metrics = [("critical_path_ns", "Δ critical path (ns)"), ("die_area", "Δ die area (µm²)"), ("total_power_mw", "Δ total power (mW)")]
    colors = {"nangate45": "#1f77b4", "sky130hd": "#ff7f0e", "asap7": "#2ca02c"}
    for ax, (col, label) in zip(axes, metrics):
        for plat in PLATFORMS:
            subset = combined[combined["platform"] == plat]
            ax.plot(subset["width"], subset[col], marker="o", label=plat, color=colors[plat])
        ax.axhline(0.0, color="gray", linestyle="--", linewidth=0.8)
        ax.set_ylabel(label)
        ax.grid(True, linestyle="--", alpha=0.4)
    axes[-1].set_xlabel("width (bits)")
    axes[0].legend(ncol=len(PLATFORMS), fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / "delta_metrics_by_width.png", dpi=150)


if __name__ == "__main__":
    main()
