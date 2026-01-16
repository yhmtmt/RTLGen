#!/usr/bin/env python3
"""
Build a global runs/index.csv by aggregating metrics.csv under runs/designs/.
"""

import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_ROOT = REPO_ROOT / "runs" / "designs"
OUT_PATH = REPO_ROOT / "runs" / "index.csv"


def iter_metrics_files(root: Path):
    for path in root.rglob("metrics.csv"):
        if path.is_file():
            yield path


def normalize_repo_path(path_str: str):
    if not path_str:
        return ""
    path = Path(path_str)
    if path.is_absolute():
        try:
            return path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            parts = path.parts
            if "runs" in parts:
                idx = parts.index("runs")
                return Path(*parts[idx:]).as_posix()
            return path_str
    parts = path.parts
    if "runs" in parts:
        idx = parts.index("runs")
        return Path(*parts[idx:]).as_posix()
    return path.as_posix()


def parse_design_info(metrics_path: Path):
    rel = metrics_path.relative_to(DESIGNS_ROOT)
    parts = rel.parts
    if len(parts) < 2:
        return "unknown", "unknown"
    return parts[0], parts[1]


def load_metrics(metrics_path: Path):
    text = metrics_path.read_text()
    text = re.sub(r"result\\.json(?=[A-Za-z0-9_])", "result.json\\n", text)
    lines = text.splitlines()
    if not lines:
        return []
    header = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        front = parts[:9]
        rest = parts[9]
        if "," in rest:
            params_json, result_path = rest.rsplit(",", 1)
        else:
            params_json, result_path = rest, ""
        values = front + [params_json, result_path]
        if len(values) != len(header):
            continue
        row = dict(zip(header, values))
        rows.append(row)
    return rows


def main():
    rows = []
    for metrics_path in iter_metrics_files(DESIGNS_ROOT):
        circuit_type, design = parse_design_info(metrics_path)
        for row in load_metrics(metrics_path):
            params_json = row.get("params_json", "")
            try:
                params = json.loads(params_json) if params_json else {}
            except json.JSONDecodeError:
                params = {}
            rows.append(
                {
                    "circuit_type": circuit_type,
                    "design": design,
                    "platform": row.get("platform", ""),
                    "status": row.get("status", ""),
                    "critical_path_ns": row.get("critical_path_ns", ""),
                    "die_area": row.get("die_area", ""),
                    "total_power_mw": row.get("total_power_mw", ""),
                    "config_hash": row.get("config_hash", ""),
                    "param_hash": row.get("param_hash", ""),
                    "tag": row.get("tag", ""),
                    "result_path": normalize_repo_path(row.get("result_path", "")),
                    "params_json": json.dumps(params, sort_keys=True),
                    "metrics_path": normalize_repo_path(str(metrics_path)),
                    "design_path": normalize_repo_path(str(metrics_path.parent)),
                }
            )

    rows.sort(key=lambda r: (r["circuit_type"], r["design"], r["platform"], r["param_hash"]))

    fieldnames = [
        "circuit_type",
        "design",
        "platform",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "config_hash",
        "param_hash",
        "tag",
        "result_path",
        "params_json",
        "metrics_path",
        "design_path",
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
