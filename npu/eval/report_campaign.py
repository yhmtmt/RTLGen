#!/usr/bin/env python3
"""
Generate campaign-level summary report from merged results CSV.

Outputs:
  - Markdown report (default: campaign.outputs.report_md)
  - Optional summary CSV with per-(arch,mode,model) and aggregate rows
"""

import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from validate import load_json, validate_campaign


REPO_ROOT = Path(__file__).resolve().parents[2]


def log(msg: str) -> None:
    print(f"[report_campaign] {msg}")


def abs_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path.resolve())


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        txt = str(value).strip()
        if txt == "":
            return None
        return float(txt)
    except Exception:
        return None


def mean(values: Iterable[float]) -> Optional[float]:
    vals = list(values)
    if not vals:
        return None
    return sum(vals) / float(len(vals))


def stddev(values: Iterable[float]) -> Optional[float]:
    vals = list(values)
    if not vals:
        return None
    if len(vals) < 2:
        return 0.0
    mu = sum(vals) / float(len(vals))
    var = sum((x - mu) ** 2 for x in vals) / float(len(vals) - 1)
    return math.sqrt(var)


def fmt(value: Optional[float], digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def load_results_rows(results_csv: Path) -> List[Dict[str, str]]:
    if not results_csv.exists():
        return []
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def group_ok_rows(rows: List[Dict[str, str]]) -> Dict[Tuple[str, str, str], List[Dict[str, str]]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        if str(row.get("status", "")).strip() != "ok":
            continue
        key = (
            str(row.get("arch_id", "")).strip(),
            str(row.get("macro_mode", "")).strip(),
            str(row.get("model_id", "")).strip(),
        )
        groups[key].append(row)
    return groups


def summarize_group(rows: List[Dict[str, str]]) -> Dict[str, Optional[float]]:
    metrics = {
        "latency_ms": [],
        "throughput_infer_per_s": [],
        "energy_mj": [],
        "cycles": [],
        "critical_path_ns": [],
        "die_area_um2": [],
        "total_power_mw": [],
        "flow_elapsed_s": [],
        "place_gp_elapsed_s": [],
    }
    for row in rows:
        metrics["latency_ms"].append(safe_float(row.get("performance_latency_ms")))
        metrics["throughput_infer_per_s"].append(safe_float(row.get("performance_throughput_infer_per_s")))
        metrics["energy_mj"].append(safe_float(row.get("performance_energy_mj")))
        metrics["cycles"].append(safe_float(row.get("performance_cycles")))
        metrics["critical_path_ns"].append(safe_float(row.get("physical_critical_path_ns")))
        metrics["die_area_um2"].append(safe_float(row.get("physical_die_area_um2")))
        metrics["total_power_mw"].append(safe_float(row.get("physical_total_power_mw")))
        metrics["flow_elapsed_s"].append(safe_float(row.get("physical_flow_elapsed_s")))
        metrics["place_gp_elapsed_s"].append(safe_float(row.get("physical_place_gp_elapsed_s")))

    def keep(values: List[Optional[float]]) -> List[float]:
        return [v for v in values if v is not None]

    out: Dict[str, Optional[float]] = {}
    for k, vals in metrics.items():
        vv = keep(vals)
        out[f"{k}_mean"] = mean(vv)
        out[f"{k}_std"] = stddev(vv)
    out["n"] = float(len(rows))
    return out


def rank_key(item: Dict[str, Any]) -> Tuple[float, float, float, float]:
    latency = item.get("latency_ms_mean")
    energy = item.get("energy_mj_mean")
    flow = item.get("flow_elapsed_s_mean")
    cp = item.get("critical_path_ns_mean")
    return (
        float("inf") if latency is None else float(latency),
        float("inf") if energy is None else float(energy),
        float("inf") if flow is None else float(flow),
        float("inf") if cp is None else float(cp),
    )


def write_summary_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in header:
                header.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate campaign summary report")
    ap.add_argument("--campaign", required=True, help="Campaign manifest JSON")
    ap.add_argument("--results_csv", help="Optional override for merged results CSV")
    ap.add_argument("--out_md", help="Optional override for markdown report path")
    ap.add_argument("--out_csv", help="Optional summary CSV path")
    args = ap.parse_args()

    os.chdir(REPO_ROOT)
    campaign_path = abs_path(args.campaign)
    campaign = load_json(campaign_path)
    validate_campaign(campaign, check_paths=True)

    results_csv = abs_path(args.results_csv) if args.results_csv else abs_path(str(campaign["outputs"]["results_csv"]))
    out_md = abs_path(args.out_md) if args.out_md else abs_path(str(campaign["outputs"].get("report_md", "")))
    if not str(out_md):
        out_md = results_csv.parent / "report.md"
    out_csv = abs_path(args.out_csv) if args.out_csv else (results_csv.parent / "summary.csv")

    rows = load_results_rows(results_csv)
    if not rows:
        raise SystemExit(f"report_campaign: no rows found: {results_csv}")

    grouped = group_ok_rows(rows)
    total_rows = len(rows)
    ok_rows = sum(1 for r in rows if str(r.get("status", "")).strip() == "ok")
    fail_rows = total_rows - ok_rows

    per_model: List[Dict[str, Any]] = []
    for (arch_id, macro_mode, model_id), g_rows in sorted(grouped.items()):
        s = summarize_group(g_rows)
        row = {
            "scope": "model",
            "arch_id": arch_id,
            "macro_mode": macro_mode,
            "model_id": model_id,
            "n": int(s.get("n") or 0),
            "latency_ms_mean": s.get("latency_ms_mean"),
            "latency_ms_std": s.get("latency_ms_std"),
            "throughput_infer_per_s_mean": s.get("throughput_infer_per_s_mean"),
            "throughput_infer_per_s_std": s.get("throughput_infer_per_s_std"),
            "energy_mj_mean": s.get("energy_mj_mean"),
            "energy_mj_std": s.get("energy_mj_std"),
            "critical_path_ns_mean": s.get("critical_path_ns_mean"),
            "die_area_um2_mean": s.get("die_area_um2_mean"),
            "total_power_mw_mean": s.get("total_power_mw_mean"),
            "flow_elapsed_s_mean": s.get("flow_elapsed_s_mean"),
            "place_gp_elapsed_s_mean": s.get("place_gp_elapsed_s_mean"),
        }
        per_model.append(row)

    by_arch_mode: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in per_model:
        by_arch_mode[(str(row["arch_id"]), str(row["macro_mode"]))].append(row)

    aggregate: List[Dict[str, Any]] = []
    for (arch_id, macro_mode), model_rows in sorted(by_arch_mode.items()):
        agg = {
            "scope": "aggregate",
            "arch_id": arch_id,
            "macro_mode": macro_mode,
            "model_count": len(model_rows),
            "latency_ms_mean": mean(
                [float(x["latency_ms_mean"]) for x in model_rows if x["latency_ms_mean"] is not None]
            ),
            "throughput_infer_per_s_mean": mean(
                [
                    float(x["throughput_infer_per_s_mean"])
                    for x in model_rows
                    if x["throughput_infer_per_s_mean"] is not None
                ]
            ),
            "energy_mj_mean": mean(
                [float(x["energy_mj_mean"]) for x in model_rows if x["energy_mj_mean"] is not None]
            ),
            "critical_path_ns_mean": mean(
                [float(x["critical_path_ns_mean"]) for x in model_rows if x["critical_path_ns_mean"] is not None]
            ),
            "die_area_um2_mean": mean(
                [float(x["die_area_um2_mean"]) for x in model_rows if x["die_area_um2_mean"] is not None]
            ),
            "total_power_mw_mean": mean(
                [float(x["total_power_mw_mean"]) for x in model_rows if x["total_power_mw_mean"] is not None]
            ),
            "flow_elapsed_s_mean": mean(
                [float(x["flow_elapsed_s_mean"]) for x in model_rows if x["flow_elapsed_s_mean"] is not None]
            ),
            "place_gp_elapsed_s_mean": mean(
                [float(x["place_gp_elapsed_s_mean"]) for x in model_rows if x["place_gp_elapsed_s_mean"] is not None]
            ),
        }
        aggregate.append(agg)

    ranked = sorted(aggregate, key=rank_key)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i

    summary_rows: List[Dict[str, Any]] = []
    summary_rows.extend(per_model)
    summary_rows.extend(ranked)
    write_summary_csv(out_csv, summary_rows)

    lines: List[str] = []
    lines.append(f"# Campaign Report: {campaign['campaign_id']}")
    lines.append("")
    lines.append(f"- generated_utc: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`")
    lines.append(f"- results_csv: `{rel_to_repo(results_csv)}`")
    lines.append(f"- summary_csv: `{rel_to_repo(out_csv)}`")
    lines.append(f"- total_rows: `{total_rows}`")
    lines.append(f"- ok_rows: `{ok_rows}`")
    lines.append(f"- non_ok_rows: `{fail_rows}`")
    lines.append("")

    lines.append("## Aggregate Ranking (lower latency, lower energy)")
    lines.append("")
    lines.append(
        "| rank | arch_id | macro_mode | model_count | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |"
    )
    lines.append(
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for row in ranked:
        lines.append(
            "| {rank} | {arch} | {mode} | {mc} | {lat} | {thr} | {eng} | {cp} | {area} | {pwr} | {flow} | {gp} |".format(
                rank=row.get("rank", ""),
                arch=row["arch_id"],
                mode=row["macro_mode"],
                mc=row["model_count"],
                lat=fmt(row.get("latency_ms_mean")),
                thr=fmt(row.get("throughput_infer_per_s_mean")),
                eng=fmt(row.get("energy_mj_mean"), digits=8),
                cp=fmt(row.get("critical_path_ns_mean")),
                area=fmt(row.get("die_area_um2_mean")),
                pwr=fmt(row.get("total_power_mw_mean"), digits=6),
                flow=fmt(row.get("flow_elapsed_s_mean")),
                gp=fmt(row.get("place_gp_elapsed_s_mean")),
            )
        )
    lines.append("")

    lines.append("## Per-Model Summary")
    lines.append("")
    lines.append(
        "| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |"
    )
    lines.append(
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for row in sorted(per_model, key=lambda x: (x["model_id"], x["arch_id"], x["macro_mode"])):
        lines.append(
            "| {arch} | {mode} | {model} | {n} | {lat_m} | {lat_s} | {thr} | {eng} | {cp} | {area} | {pwr} | {flow} | {gp} |".format(
                arch=row["arch_id"],
                mode=row["macro_mode"],
                model=row["model_id"],
                n=row["n"],
                lat_m=fmt(row.get("latency_ms_mean")),
                lat_s=fmt(row.get("latency_ms_std")),
                thr=fmt(row.get("throughput_infer_per_s_mean")),
                eng=fmt(row.get("energy_mj_mean"), digits=8),
                cp=fmt(row.get("critical_path_ns_mean")),
                area=fmt(row.get("die_area_um2_mean")),
                pwr=fmt(row.get("total_power_mw_mean"), digits=6),
                flow=fmt(row.get("flow_elapsed_s_mean")),
                gp=fmt(row.get("place_gp_elapsed_s_mean")),
            )
        )
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote report: {rel_to_repo(out_md)}")
    log(f"wrote summary: {rel_to_repo(out_csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
