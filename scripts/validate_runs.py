#!/usr/bin/env python3
"""Validate runs/designs metrics.csv files and the global runs/index.csv."""

import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_ROOT = REPO_ROOT / "runs" / "designs"
INDEX_PATH = REPO_ROOT / "runs" / "index.csv"

REQUIRED_METRICS_FIELDS = {
    "design",
    "platform",
    "config_hash",
    "param_hash",
    "tag",
    "status",
    "critical_path_ns",
    "die_area",
    "total_power_mw",
    "params_json",
    "result_path",
}

REQUIRED_INDEX_FIELDS = {
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
}


def read_csv(path: Path):
    with path.open() as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def read_metrics_csv(path: Path):
    text = path.read_text()
    text = re.sub(r"result\\.json(?=[A-Za-z0-9_])", "result.json\\n", text)
    lines = text.splitlines()
    if not lines:
        return [], []
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
        rows.append(dict(zip(header, values)))
    return header, rows


def validate_metrics():
    errors = []
    seen = set()
    for metrics_path in DESIGNS_ROOT.rglob("metrics.csv"):
        fields, rows = read_metrics_csv(metrics_path)
        missing = REQUIRED_METRICS_FIELDS - set(fields)
        if missing:
            errors.append(f"{metrics_path}: missing fields {sorted(missing)}")
        for row in rows:
            key = (row.get("design"), row.get("platform"), row.get("param_hash"))
            if key in seen:
                errors.append(f"duplicate run: {key} in {metrics_path}")
            else:
                seen.add(key)
            params_json = row.get("params_json", "").strip()
            if params_json and not (params_json.startswith("{") and params_json.endswith("}")):
                errors.append(f"{metrics_path}: malformed params_json for {key}")
    return errors


def validate_index():
    errors = []
    if not INDEX_PATH.exists():
        errors.append(f"missing {INDEX_PATH}")
        return errors
    fields, rows = read_csv(INDEX_PATH)
    missing = REQUIRED_INDEX_FIELDS - set(fields)
    if missing:
        errors.append(f"{INDEX_PATH}: missing fields {sorted(missing)}")
    for row in rows:
        params_json = row.get("params_json", "").strip()
        if params_json:
            try:
                json.loads(params_json)
            except json.JSONDecodeError:
                errors.append(f"{INDEX_PATH}: invalid params_json in row {row.get('design')}")
    return errors


def main():
    errors = []
    errors.extend(validate_metrics())
    errors.extend(validate_index())
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("OK: runs validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
