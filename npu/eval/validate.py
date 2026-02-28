#!/usr/bin/env python3
"""
Lightweight validator for NPU evaluation campaign/result JSON files.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_MACRO_MODES = {"flat_nomacro", "hier_macro"}
VALID_STATUS = {"ok", "fail", "skipped"}


def die(msg: str) -> None:
    print(f"validate: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        die(f"failed to read {path}: {exc}")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")
    if not isinstance(doc, dict):
        die(f"{path}: top-level must be an object")
    return doc


def expect_keys(obj: Dict[str, Any], required: List[str], where: str) -> None:
    for key in required:
        if key not in obj:
            die(f"{where}: missing required key '{key}'")


def expect_string(value: Any, where: str, allow_empty: bool = False) -> None:
    if not isinstance(value, str):
        die(f"{where}: expected string")
    if not allow_empty and not value.strip():
        die(f"{where}: string must be non-empty")


def expect_number_or_none(value: Any, where: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        die(f"{where}: expected number or null")
    if value < 0:
        die(f"{where}: expected non-negative number")


def maybe_check_path(path_txt: str, check_paths: bool, where: str) -> None:
    if not check_paths:
        return
    if not path_txt:
        return
    p = Path(path_txt)
    if not p.exists():
        die(f"{where}: path does not exist: {path_txt}")


def validate_campaign(doc: Dict[str, Any], check_paths: bool) -> None:
    expect_keys(
        doc,
        [
            "version",
            "campaign_id",
            "platform",
            "make_target",
            "repeats",
            "models",
            "architecture_points",
            "outputs",
        ],
        "campaign",
    )
    if doc.get("version") != 0.1:
        die("campaign.version must be 0.1")
    expect_string(doc["campaign_id"], "campaign.campaign_id")
    expect_string(doc["platform"], "campaign.platform")
    expect_string(doc["make_target"], "campaign.make_target")
    repeats = doc["repeats"]
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        die("campaign.repeats must be an integer >= 1")

    models = doc["models"]
    if not isinstance(models, list) or not models:
        die("campaign.models must be a non-empty array")
    model_ids = set()
    for i, model in enumerate(models):
        where = f"campaign.models[{i}]"
        if not isinstance(model, dict):
            die(f"{where}: expected object")
        expect_keys(model, ["model_id", "onnx_path"], where)
        expect_string(model["model_id"], f"{where}.model_id")
        expect_string(model["onnx_path"], f"{where}.onnx_path")
        maybe_check_path(model["onnx_path"], check_paths, f"{where}.onnx_path")
        mid = model["model_id"]
        if mid in model_ids:
            die(f"{where}: duplicate model_id '{mid}'")
        model_ids.add(mid)
        if "mapper_arch" in model:
            expect_string(model["mapper_arch"], f"{where}.mapper_arch")
            maybe_check_path(model["mapper_arch"], check_paths, f"{where}.mapper_arch")
        if "perf_config" in model:
            expect_string(model["perf_config"], f"{where}.perf_config")
            maybe_check_path(model["perf_config"], check_paths, f"{where}.perf_config")
        if "mapper_extra_args" in model:
            args = model["mapper_extra_args"]
            if not isinstance(args, list):
                die(f"{where}.mapper_extra_args: expected array")
            for j, arg in enumerate(args):
                expect_string(arg, f"{where}.mapper_extra_args[{j}]")

    points = doc["architecture_points"]
    if not isinstance(points, list) or not points:
        die("campaign.architecture_points must be a non-empty array")
    arch_ids = set()
    for i, point in enumerate(points):
        where = f"campaign.architecture_points[{i}]"
        if not isinstance(point, dict):
            die(f"{where}: expected object")
        expect_keys(point, ["arch_id", "synth_design_dir", "sweep_file"], where)
        expect_string(point["arch_id"], f"{where}.arch_id")
        expect_string(point["synth_design_dir"], f"{where}.synth_design_dir")
        expect_string(point["sweep_file"], f"{where}.sweep_file")
        maybe_check_path(point["synth_design_dir"], check_paths, f"{where}.synth_design_dir")
        maybe_check_path(point["sweep_file"], check_paths, f"{where}.sweep_file")
        aid = point["arch_id"]
        if aid in arch_ids:
            die(f"{where}: duplicate arch_id '{aid}'")
        arch_ids.add(aid)
        for k in ("rtlgen_config", "macro_manifest", "macro_library", "macro_select_json"):
            if k in point:
                expect_string(point[k], f"{where}.{k}")
                maybe_check_path(point[k], check_paths, f"{where}.{k}")

    outputs = doc["outputs"]
    if not isinstance(outputs, dict):
        die("campaign.outputs must be an object")
    expect_keys(outputs, ["campaign_dir", "results_csv"], "campaign.outputs")
    expect_string(outputs["campaign_dir"], "campaign.outputs.campaign_dir")
    expect_string(outputs["results_csv"], "campaign.outputs.results_csv")


def validate_result_row(doc: Dict[str, Any], check_paths: bool) -> None:
    expect_keys(
        doc,
        [
            "version",
            "campaign_id",
            "run_id",
            "timestamp_utc",
            "status",
            "platform",
            "model_id",
            "arch_id",
            "macro_mode",
            "physical",
            "performance",
            "artifacts",
        ],
        "result_row",
    )
    if doc.get("version") != 0.1:
        die("result_row.version must be 0.1")
    for key in ("campaign_id", "run_id", "timestamp_utc", "platform", "model_id", "arch_id"):
        expect_string(doc[key], f"result_row.{key}")

    status = doc["status"]
    expect_string(status, "result_row.status")
    if status not in VALID_STATUS:
        die(f"result_row.status must be one of {sorted(VALID_STATUS)}")

    macro_mode = doc["macro_mode"]
    expect_string(macro_mode, "result_row.macro_mode")
    if macro_mode not in VALID_MACRO_MODES:
        die(f"result_row.macro_mode must be one of {sorted(VALID_MACRO_MODES)}")

    if "repeat_index" in doc:
        r = doc["repeat_index"]
        if isinstance(r, bool) or not isinstance(r, int) or r < 1:
            die("result_row.repeat_index must be integer >= 1")

    physical = doc["physical"]
    if not isinstance(physical, dict):
        die("result_row.physical must be an object")
    expect_keys(
        physical,
        [
            "critical_path_ns",
            "die_area_um2",
            "total_power_mw",
            "flow_elapsed_s",
            "place_gp_elapsed_s",
        ],
        "result_row.physical",
    )
    for k in ("critical_path_ns", "die_area_um2", "total_power_mw", "flow_elapsed_s", "place_gp_elapsed_s"):
        expect_number_or_none(physical[k], f"result_row.physical.{k}")

    performance = doc["performance"]
    if not isinstance(performance, dict):
        die("result_row.performance must be an object")
    expect_keys(
        performance,
        ["cycles", "latency_ms", "throughput_infer_per_s", "energy_mj"],
        "result_row.performance",
    )
    for k in ("cycles", "latency_ms", "throughput_infer_per_s", "energy_mj"):
        expect_number_or_none(performance[k], f"result_row.performance.{k}")

    artifacts = doc["artifacts"]
    if not isinstance(artifacts, dict):
        die("result_row.artifacts must be an object")
    expect_keys(
        artifacts,
        ["synth_result_json", "perf_trace_json", "schedule_yml", "descriptors_bin"],
        "result_row.artifacts",
    )
    for key in ("synth_result_json", "perf_trace_json", "schedule_yml", "descriptors_bin"):
        expect_string(artifacts[key], f"result_row.artifacts.{key}", allow_empty=True)
        maybe_check_path(artifacts[key], check_paths, f"result_row.artifacts.{key}")

    if status == "ok":
        for k in ("critical_path_ns", "die_area_um2", "total_power_mw"):
            if physical.get(k) is None:
                die(f"result_row.status=ok requires result_row.physical.{k}")
        for k in ("cycles", "latency_ms", "throughput_infer_per_s", "energy_mj"):
            if performance.get(k) is None:
                die(f"result_row.status=ok requires result_row.performance.{k}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate NPU evaluation campaign/result JSON")
    ap.add_argument("--campaign", help="Campaign JSON path")
    ap.add_argument("--result-row", help="Result-row JSON path")
    ap.add_argument(
        "--check_paths",
        action="store_true",
        help="Also verify that path-like fields exist on disk",
    )
    args = ap.parse_args()

    selected = int(bool(args.campaign)) + int(bool(args.result_row))
    if selected != 1:
        die("choose exactly one of --campaign or --result-row")

    if args.campaign:
        path = Path(args.campaign)
        doc = load_json(path)
        validate_campaign(doc, check_paths=args.check_paths)
        print(f"OK: campaign {path}")
        return 0

    path = Path(args.result_row)
    doc = load_json(path)
    validate_result_row(doc, check_paths=args.check_paths)
    print(f"OK: result_row {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
