#!/usr/bin/env python3
"""
Lightweight validator for NPU evaluation campaign/result JSON files.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_MACRO_MODES = {"flat_nomacro", "hier_macro"}
VALID_STATUS = {"ok", "fail", "skipped"}
VALID_LAYER1_EVAL_SCOPES = {"wrapped_io", "macro_hardened"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_layer1_modules(
    layer1: Dict[str, Any],
    *,
    where: str,
    campaign_platform: str,
    check_paths: bool,
) -> None:
    allowed = {"manifest", "variant_ids", "allow_wrapped_io"}
    for key in layer1.keys():
        if key not in allowed:
            die(f"{where}: unknown key '{key}'")

    expect_keys(layer1, ["manifest", "variant_ids"], where)
    manifest_path_txt = layer1["manifest"]
    expect_string(manifest_path_txt, f"{where}.manifest")

    # Candidate manifest is required for deterministic layer handoff, regardless of check_paths.
    manifest_path = Path(manifest_path_txt)
    if not manifest_path.exists():
        die(f"{where}.manifest: path does not exist: {manifest_path_txt}")
    maybe_check_path(manifest_path_txt, check_paths, f"{where}.manifest")

    variant_ids = layer1["variant_ids"]
    if not isinstance(variant_ids, list) or not variant_ids:
        die(f"{where}.variant_ids must be a non-empty array")

    seen_ids = set()
    selected_ids: List[str] = []
    for i, variant_id in enumerate(variant_ids):
        expect_string(variant_id, f"{where}.variant_ids[{i}]")
        vid = str(variant_id).strip()
        if vid in seen_ids:
            die(f"{where}.variant_ids: duplicate id '{vid}'")
        seen_ids.add(vid)
        selected_ids.append(vid)

    allow_wrapped_raw = layer1.get("allow_wrapped_io", False)
    if not isinstance(allow_wrapped_raw, bool):
        die(f"{where}.allow_wrapped_io: expected boolean")
    allow_wrapped = bool(allow_wrapped_raw)

    manifest_doc = load_json(manifest_path)
    pdk = str(manifest_doc.get("pdk", "")).strip()
    if pdk and pdk != campaign_platform:
        die(
            f"{where}: candidate manifest pdk '{pdk}' does not match "
            f"campaign platform '{campaign_platform}'"
        )

    candidates_raw = manifest_doc.get("candidates")
    if not isinstance(candidates_raw, list) or not candidates_raw:
        die(f"{where}.manifest: candidates must be a non-empty array")

    by_variant_id: Dict[str, Dict[str, Any]] = {}
    for i, cand in enumerate(candidates_raw):
        cwhere = f"{where}.manifest.candidates[{i}]"
        if not isinstance(cand, dict):
            die(f"{cwhere}: expected object")
        variant_id = str(cand.get("variant_id", "")).strip()
        if not variant_id:
            die(f"{cwhere}: missing non-empty variant_id")
        if variant_id in by_variant_id:
            die(f"{where}.manifest: duplicate variant_id '{variant_id}'")
        scope = str(cand.get("evaluation_scope", "")).strip()
        if scope not in VALID_LAYER1_EVAL_SCOPES:
            die(
                f"{cwhere}.evaluation_scope: invalid '{scope}', "
                f"expected one of {sorted(VALID_LAYER1_EVAL_SCOPES)}"
            )
        by_variant_id[variant_id] = cand

    wrapped_ids: List[str] = []
    for variant_id in selected_ids:
        cand = by_variant_id.get(variant_id)
        if cand is None:
            die(f"{where}.variant_ids: unknown variant_id '{variant_id}' in manifest")
        scope = str(cand.get("evaluation_scope", "")).strip()
        if scope == "wrapped_io":
            wrapped_ids.append(variant_id)

    if wrapped_ids and not allow_wrapped:
        die(
            f"{where}: selected wrapped_io candidates {wrapped_ids}; "
            "re-evaluate as macro_hardened or set allow_wrapped_io=true to override"
        )


def validate_model_manifest(
    *,
    manifest_path_txt: str,
    model_set_id: str,
    check_paths: bool,
) -> Dict[str, Dict[str, str]]:
    manifest_path = Path(manifest_path_txt)
    if not manifest_path.exists():
        die(f"campaign.model_manifest: path does not exist: {manifest_path_txt}")
    maybe_check_path(manifest_path_txt, check_paths, "campaign.model_manifest")

    manifest = load_json(manifest_path)
    expect_keys(manifest, ["version", "model_set_id", "models"], "campaign.model_manifest")
    if manifest.get("version") != 0.1:
        die("campaign.model_manifest.version must be 0.1")

    manifest_model_set_id = str(manifest.get("model_set_id", "")).strip()
    if manifest_model_set_id != model_set_id:
        die(
            f"campaign.model_manifest.model_set_id '{manifest_model_set_id}' "
            f"does not match campaign.model_set_id '{model_set_id}'"
        )

    models = manifest.get("models")
    if not isinstance(models, list) or not models:
        die("campaign.model_manifest.models must be a non-empty array")

    by_id: Dict[str, Dict[str, str]] = {}
    for i, model in enumerate(models):
        where = f"campaign.model_manifest.models[{i}]"
        if not isinstance(model, dict):
            die(f"{where}: expected object")
        expect_keys(model, ["model_id", "onnx_path", "onnx_sha256"], where)
        model_id = str(model.get("model_id", "")).strip()
        onnx_path = str(model.get("onnx_path", "")).strip()
        onnx_sha = str(model.get("onnx_sha256", "")).strip().lower()
        if not model_id:
            die(f"{where}.model_id must be non-empty")
        if model_id in by_id:
            die(f"campaign.model_manifest.models: duplicate model_id '{model_id}'")
        if not onnx_path:
            die(f"{where}.onnx_path must be non-empty")
        if not SHA256_RE.fullmatch(onnx_sha):
            die(f"{where}.onnx_sha256 must be 64 lowercase hex chars")
        maybe_check_path(onnx_path, check_paths, f"{where}.onnx_path")
        if check_paths:
            p = Path(onnx_path)
            actual_sha = sha256_file(p)
            if actual_sha != onnx_sha:
                die(
                    f"{where}.onnx_sha256 mismatch for {onnx_path}: "
                    f"manifest={onnx_sha} actual={actual_sha}"
                )
        by_id[model_id] = {
            "model_id": model_id,
            "onnx_path": onnx_path,
            "onnx_sha256": onnx_sha,
        }
    return by_id


def validate_campaign(doc: Dict[str, Any], check_paths: bool) -> None:
    expect_keys(
        doc,
        [
            "version",
            "campaign_id",
            "model_set_id",
            "model_manifest",
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
    expect_string(doc["model_set_id"], "campaign.model_set_id")
    expect_string(doc["model_manifest"], "campaign.model_manifest")
    expect_string(doc["platform"], "campaign.platform")
    expect_string(doc["make_target"], "campaign.make_target")
    model_set_id = str(doc["model_set_id"]).strip()
    model_manifest = str(doc["model_manifest"]).strip()
    model_manifest_by_id = validate_model_manifest(
        manifest_path_txt=model_manifest,
        model_set_id=model_set_id,
        check_paths=check_paths,
    )

    if "physical_source_campaign" in doc:
        expect_string(doc["physical_source_campaign"], "campaign.physical_source_campaign")
        maybe_check_path(doc["physical_source_campaign"], check_paths, "campaign.physical_source_campaign")

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
        mref = model_manifest_by_id.get(str(mid))
        if mref is None:
            die(f"{where}: model_id '{mid}' is not present in campaign.model_manifest")
        manifest_onnx_path = str(mref.get("onnx_path", "")).strip()
        if str(model["onnx_path"]).strip() != manifest_onnx_path:
            die(
                f"{where}.onnx_path '{model['onnx_path']}' does not match "
                f"campaign.model_manifest path '{manifest_onnx_path}'"
            )
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
        if "layer1_modules" in point:
            layer1 = point["layer1_modules"]
            if not isinstance(layer1, dict):
                die(f"{where}.layer1_modules: expected object")
            validate_layer1_modules(
                layer1,
                where=f"{where}.layer1_modules",
                campaign_platform=str(doc["platform"]),
                check_paths=check_paths,
            )
        if "physical_select" in point:
            sel = point["physical_select"]
            if not isinstance(sel, dict):
                die(f"{where}.physical_select: expected object")
            allowed_sel = {"compare_group", "tag_prefix"}
            for key in sel.keys():
                if key not in allowed_sel:
                    die(f"{where}.physical_select: unknown key '{key}'")
            if "compare_group" in sel:
                expect_string(sel["compare_group"], f"{where}.physical_select.compare_group")
            if "tag_prefix" in sel:
                expect_string(sel["tag_prefix"], f"{where}.physical_select.tag_prefix")

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

    has_model_set = "model_set_id" in doc
    has_model_manifest = "model_manifest" in doc
    has_onnx_sha = "onnx_sha256" in doc
    if has_model_set or has_model_manifest or has_onnx_sha:
        if not (has_model_set and has_model_manifest and has_onnx_sha):
            die(
                "result_row.model_set_id, result_row.model_manifest, and "
                "result_row.onnx_sha256 must appear together"
            )
        expect_string(doc["model_set_id"], "result_row.model_set_id")
        expect_string(doc["model_manifest"], "result_row.model_manifest")
        maybe_check_path(doc["model_manifest"], check_paths, "result_row.model_manifest")
        expect_string(doc["onnx_sha256"], "result_row.onnx_sha256")
        if not SHA256_RE.fullmatch(str(doc["onnx_sha256"]).strip().lower()):
            die("result_row.onnx_sha256 must be 64 lowercase hex chars")
    if "mapper_arch_hash" in doc:
        expect_string(doc["mapper_arch_hash"], "result_row.mapper_arch_hash")
        mhash = str(doc["mapper_arch_hash"]).strip().lower()
        if mhash and not SHA256_RE.fullmatch(mhash):
            die("result_row.mapper_arch_hash must be empty or 64 lowercase hex chars")
    if "perf_config_hash" in doc:
        expect_string(doc["perf_config_hash"], "result_row.perf_config_hash")
        phash = str(doc["perf_config_hash"]).strip().lower()
        if phash and not SHA256_RE.fullmatch(phash):
            die("result_row.perf_config_hash must be empty or 64 lowercase hex chars")
    if "physical_source_campaign" in doc:
        expect_string(doc["physical_source_campaign"], "result_row.physical_source_campaign")

    has_sample_id = "sample_id" in doc
    has_batch_id = "batch_id" in doc
    if has_sample_id != has_batch_id:
        die("result_row.sample_id and result_row.batch_id must appear together")
    if has_sample_id:
        expect_string(doc["sample_id"], "result_row.sample_id")
        expect_string(doc["batch_id"], "result_row.batch_id")
    if "sample_index" in doc:
        sidx = doc["sample_index"]
        if isinstance(sidx, bool) or not isinstance(sidx, int) or sidx < 1:
            die("result_row.sample_index must be integer >= 1")
        if not has_sample_id:
            die("result_row.sample_index requires result_row.sample_id and result_row.batch_id")

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
