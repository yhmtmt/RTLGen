#!/usr/bin/env python3
"""Build Llama7B attention local-cost profiles for reciprocal-LUT softmax choices."""

from __future__ import annotations

import argparse
import csv
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _safe_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
    lines = text.splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines)
    csv_rows = list(reader)
    good_rows = [row for row in csv_rows if None not in row]
    if reader.fieldnames and good_rows and len(good_rows) == len(csv_rows):
        return [{str(key): str(value or "") for key, value in row.items()} for row in good_rows]

    header = lines[0].split(",")
    rows: list[dict[str, str]] = [{str(key): str(value or "") for key, value in row.items()} for row in good_rows]
    prefix_len = max(len(header) - 2, 0)
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(",", prefix_len)
        if len(parts) < prefix_len + 1:
            continue
        front = parts[:prefix_len]
        rest = parts[prefix_len]
        if "," in rest:
            params_json, result_path = rest.rsplit(",", 1)
        else:
            params_json, result_path = rest, ""
        params_json = params_json.strip()
        if len(params_json) >= 2 and params_json[0] == '"' and params_json[-1] == '"':
            params_json = params_json[1:-1].replace('""', '"')
        values = front + [params_json, result_path]
        if len(values) == len(header):
            rows.append(dict(zip(header, values)))
    return rows


def _best_ok_metrics(path: Path) -> JsonDict:
    rows = [row for row in _load_metrics_rows(path) if str(row.get("status", "")).strip() == "ok"]
    if not rows:
        raise SystemExit(f"no ok metrics rows found: {path}")

    def sort_key(row: dict[str, str]) -> tuple[float, float, float, str]:
        area = _safe_float(row.get("die_area"))
        if area is None:
            area = _safe_float(row.get("instance_area_um2"))
        return (
            _safe_float(row.get("critical_path_ns")) or float("inf"),
            area or float("inf"),
            _safe_float(row.get("total_power_mw")) or float("inf"),
            str(row.get("param_hash", "")),
        )

    row = sorted(rows, key=sort_key)[0]
    area = _safe_float(row.get("die_area"))
    if area is None:
        area = _safe_float(row.get("instance_area_um2"))
    return {
        "clock_ns": _safe_float(row.get("critical_path_ns")) or 0.0,
        "area_um2": area or 0.0,
        "power_mw": _safe_float(row.get("total_power_mw")) or 0.0,
        "param_hash": str(row.get("param_hash", "")),
        "tag": str(row.get("tag", "")),
    }


def _find_profile(payload: JsonDict, name: str) -> JsonDict:
    profiles = payload.get("profiles", [])
    if not isinstance(profiles, list):
        raise SystemExit("base costs must contain a list-valued profiles field")
    for profile in profiles:
        if isinstance(profile, dict) and profile.get("name") == name:
            return profile
    raise SystemExit(f"profile template not found: {name}")


def _profile_for_bits(template: JsonDict, *, bits: int, metrics_csv: str, metrics: JsonDict) -> JsonDict:
    profile = deepcopy(template)
    profile["name"] = re.sub(r"_q\d+$", f"_q{bits}", str(template["name"]))
    profile["description"] = re.sub(r"q\d+ reciprocal", f"q{bits} reciprocal", str(template.get("description", "")))
    profile["description"] = re.sub(r"q\d+ reciprocal", f"q{bits} reciprocal", profile["description"])
    softmax = dict(profile.get("softmax_weight_generator", {}))
    softmax["design"] = f"attention_softmax_weight_int8_r8_acc24_recip_q{bits}_wrapper"
    softmax["clock_ns"] = round(float(metrics["clock_ns"]), 6)
    softmax["area_um2"] = round(float(metrics["area_um2"]), 6)
    softmax["power_mw"] = round(float(metrics["power_mw"]), 6)
    softmax["metrics_csv"] = metrics_csv
    softmax["param_hash"] = metrics["param_hash"]
    softmax["tag"] = metrics["tag"]
    profile["softmax_weight_generator"] = softmax
    return profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--base-costs", required=True)
    parser.add_argument("--template-profile", required=True)
    parser.add_argument("--bits-list", default="8,10,12")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    base_path = repo_root / args.base_costs
    payload = json.loads(base_path.read_text(encoding="utf-8"))
    template = _find_profile(payload, args.template_profile)
    bits_values = [int(value.strip()) for value in args.bits_list.split(",") if value.strip()]

    profiles: list[JsonDict] = []
    metric_refs: dict[str, str] = {}
    for bits in bits_values:
        metrics_csv = (
            f"runs/designs/activations/attention_softmax_weight_int8_r8_acc24_recip_q{bits}_wrapper/metrics.csv"
        )
        metrics = _best_ok_metrics(repo_root / metrics_csv)
        profiles.append(_profile_for_bits(template, bits=bits, metrics_csv=metrics_csv, metrics=metrics))
        metric_refs[f"q{bits}"] = metrics_csv

    out_payload = {
        "version": 0.1,
        "name": "llama7b_attention_local_costs_endpoint_recip_lut_q8_q10_q12_v1",
        "platform": payload.get("platform", "nangate45"),
        "core_utilization": payload.get("core_utilization"),
        "scope": (
            "Per-cluster L1 costs for endpoint SRAM/NoC Llama7B search using the same "
            "local datapath/FIFO/router/endpoint boundary as the endpoint all-measured "
            "cost file, but sweeping q8/q10/q12 standalone reciprocal-LUT softmax-weight "
            "generator profiles built from merged metrics.csv artifacts."
        ),
        "source_costs": args.base_costs,
        "source_template_profile": args.template_profile,
        "softmax_metric_refs": metric_refs,
        "profiles": profiles,
    }

    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
