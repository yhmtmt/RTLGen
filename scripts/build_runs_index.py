#!/usr/bin/env python3
"""
Build a global runs/index.csv by aggregating metrics.csv under runs/designs/.
"""

import csv
import json
import re
from pathlib import Path, PureWindowsPath

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
    if re.match(r"^[A-Za-z]:[\\/]", path_str) or path_str.startswith("\\\\") or "\\" in path_str:
        win_path = PureWindowsPath(path_str)
        parts = win_path.parts
        if "runs" in parts:
            idx = parts.index("runs")
            return Path(*parts[idx:]).as_posix()
        if win_path.is_absolute():
            return path_str
        return Path(path_str).as_posix()
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
    # Handle mixed historical formats:
    # 1) unquoted JSON in params_json
    # 2) CSV-quoted JSON in params_json (newer rows)
    # Also repair legacy missing newline after result.json.
    text = metrics_path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
    lines = text.splitlines()
    if not lines:
        return [], []

    csv_reader = csv.DictReader(lines)
    csv_header = csv_reader.fieldnames or []
    csv_rows = list(csv_reader)
    good_csv_rows = [row for row in csv_rows if None not in row]

    legacy_header = lines[0].split(",")
    legacy_rows = []
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
        params_json = params_json.strip()
        if len(params_json) >= 2 and params_json[0] == '"' and params_json[-1] == '"':
            params_json = params_json[1:-1].replace('""', '"')
        values = front + [params_json, result_path]
        if len(values) != len(legacy_header):
            continue
        legacy_rows.append(dict(zip(legacy_header, values)))

    if csv_header and good_csv_rows and len(good_csv_rows) == len(csv_rows):
        return csv_header, good_csv_rows

    if csv_header and good_csv_rows:
        merged = []
        seen = set()
        key_fields = csv_header

        def _key(row):
            return tuple((k, row.get(k, "")) for k in key_fields)

        for row in good_csv_rows + legacy_rows:
            k = _key(row)
            if k in seen:
                continue
            seen.add(k)
            merged.append(row)
        return csv_header, merged

    return legacy_header, legacy_rows


def dedupe_metrics_rows(header, rows):
    deduped = []
    seen = set()
    for row in reversed(rows):
        key = (
            row.get("design", ""),
            row.get("platform", ""),
            row.get("param_hash", ""),
            normalize_repo_path(row.get("result_path", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    deduped.reverse()
    return deduped


def normalize_metrics_file(metrics_path: Path):
    header, rows = load_metrics(metrics_path)
    if not header:
        return []
    deduped = dedupe_metrics_rows(header, rows)
    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in deduped:
            writer.writerow({field: row.get(field, "") for field in header})
    return deduped


def main():
    rows = []
    for metrics_path in iter_metrics_files(DESIGNS_ROOT):
        circuit_type, design = parse_design_info(metrics_path)
        sram_summary_path = (
            REPO_ROOT
            / "runs"
            / "designs"
            / "sram"
            / design
            / "sram_metrics_summary.json"
        )
        sram_summary = {}
        if sram_summary_path.exists():
            try:
                sram_summary = json.loads(sram_summary_path.read_text())
            except json.JSONDecodeError:
                sram_summary = {}
        for row in normalize_metrics_file(metrics_path):
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
                    "sram_area_um2": sram_summary.get("total_area_um2", ""),
                    "sram_read_energy_pj": sram_summary.get("total_read_energy_pj", ""),
                    "sram_write_energy_pj": sram_summary.get("total_write_energy_pj", ""),
                    "sram_max_access_time_ns": sram_summary.get("max_access_time_ns", ""),
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
        "sram_area_um2",
        "sram_read_energy_pj",
        "sram_write_energy_pj",
        "sram_max_access_time_ns",
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
