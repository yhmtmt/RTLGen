#!/usr/bin/env python3
"""Validate runs/designs metrics.csv files, metadata.json, and the global runs/index.csv."""

import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_ROOT = REPO_ROOT / "runs" / "designs"
INDEX_PATH = REPO_ROOT / "runs" / "index.csv"
SCHEMA_PATH = REPO_ROOT / "docs" / "metadata_schema.json"
CANDIDATES_ROOT = REPO_ROOT / "runs" / "candidates"
CANDIDATE_SCHEMA_BASENAME = "module_candidates.schema.json"

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

REQUIRED_METADATA_FIELDS = {"design_id", "circuit_type", "generator"}
VALID_CIRCUIT_TYPES = {"multipliers", "prefix_adders", "activations", "mcm", "cmvm", "fp_ops", "mac", "npu_blocks", "other"}
VALID_GENERATORS = {"rtlgen", "yosys", "flopoco", "manual", "other"}


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def read_metrics_csv(path: Path):
    # Handle mixed historical formats:
    # 1) unquoted JSON in params_json
    # 2) CSV-quoted JSON in params_json (newer rows)
    # Also repair legacy missing newline after result.json.
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"result\.json(?=[A-Za-z0-9_])", "result.json\n", text)
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
        params_json = params_json.strip()
        if len(params_json) >= 2 and params_json[0] == '"' and params_json[-1] == '"':
            # CSV-quoted JSON escaping uses doubled quotes.
            params_json = params_json[1:-1].replace('""', '"')
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
            key = (
                row.get("design"),
                row.get("platform"),
                row.get("param_hash"),
                row.get("result_path"),
            )
            if key in seen:
                errors.append(f"duplicate run: {key} in {metrics_path}")
            else:
                seen.add(key)
            params_json = row.get("params_json", "").strip()
            if params_json:
                try:
                    parsed = json.loads(params_json)
                except json.JSONDecodeError:
                    errors.append(f"{metrics_path}: malformed params_json for {key}")
                    continue
                if not isinstance(parsed, dict):
                    errors.append(f"{metrics_path}: params_json must decode to object for {key}")
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


def validate_metadata():
    """Validate metadata.json files under runs/designs/ (if present)."""
    errors = []
    warnings = []
    for metadata_path in DESIGNS_ROOT.rglob("metadata.json"):
        try:
            with metadata_path.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{metadata_path}: invalid JSON: {e}")
            continue

        # Check required fields
        missing = REQUIRED_METADATA_FIELDS - set(data.keys())
        if missing:
            errors.append(f"{metadata_path}: missing required fields {sorted(missing)}")

        # Validate circuit_type enum
        circuit_type = data.get("circuit_type")
        if circuit_type and circuit_type not in VALID_CIRCUIT_TYPES:
            errors.append(f"{metadata_path}: invalid circuit_type '{circuit_type}', expected one of {sorted(VALID_CIRCUIT_TYPES)}")

        # Validate generator enum
        generator = data.get("generator")
        if generator and generator not in VALID_GENERATORS:
            errors.append(f"{metadata_path}: invalid generator '{generator}', expected one of {sorted(VALID_GENERATORS)}")

        # Validate design_id matches directory name
        design_id = data.get("design_id")
        expected_id = metadata_path.parent.name
        if design_id and design_id != expected_id:
            warnings.append(f"{metadata_path}: design_id '{design_id}' does not match directory name '{expected_id}'")

        # Validate widths if present
        widths = data.get("widths")
        if widths is not None:
            if not isinstance(widths, list):
                errors.append(f"{metadata_path}: widths must be an array")
            elif not all(isinstance(w, int) and w > 0 for w in widths):
                errors.append(f"{metadata_path}: widths must be positive integers")

        # Validate signedness if present
        signedness = data.get("signedness")
        if signedness and signedness not in {"signed", "unsigned", "mixed"}:
            errors.append(f"{metadata_path}: invalid signedness '{signedness}'")

    # Print warnings (non-fatal)
    for warn in warnings:
        print(f"WARN: {warn}")

    return errors


def _read_metrics_cached(path: Path, cache):
    key = str(path.resolve())
    if key in cache:
        return cache[key]
    fields, rows = read_metrics_csv(path)
    cache[key] = (fields, rows)
    return fields, rows


def _resolve_repo_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def validate_module_candidates():
    errors = []
    warnings = []
    if not CANDIDATES_ROOT.exists():
        return errors

    metrics_cache = {}
    manifests = sorted(CANDIDATES_ROOT.rglob("*.json"))
    for manifest_path in manifests:
        if manifest_path.name == CANDIDATE_SCHEMA_BASENAME:
            continue

        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                doc = json.load(f)
        except json.JSONDecodeError as exc:
            errors.append(f"{manifest_path}: invalid JSON: {exc}")
            continue

        if not isinstance(doc, dict):
            errors.append(f"{manifest_path}: top-level must be an object")
            continue

        for key in ("version", "pdk", "candidates"):
            if key not in doc:
                errors.append(f"{manifest_path}: missing required key '{key}'")

        version = doc.get("version")
        if version != 0.1:
            errors.append(f"{manifest_path}: version must be 0.1")

        pdk = str(doc.get("pdk", "")).strip()
        if not pdk:
            errors.append(f"{manifest_path}: pdk must be a non-empty string")

        dir_name = manifest_path.parent.name
        if dir_name != "candidates" and pdk and dir_name != pdk:
            warnings.append(
                f"{manifest_path}: parent directory '{dir_name}' does not match pdk '{pdk}'"
            )

        candidates = doc.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"{manifest_path}: candidates must be a non-empty array")
            continue

        seen_variant_ids = set()
        for i, cand in enumerate(candidates):
            where = f"{manifest_path}: candidates[{i}]"
            if not isinstance(cand, dict):
                errors.append(f"{where}: expected object")
                continue

            for key in ("variant_id", "module", "config_hash", "metrics_ref"):
                if key not in cand:
                    errors.append(f"{where}: missing required key '{key}'")
            variant_id = str(cand.get("variant_id", "")).strip()
            module = str(cand.get("module", "")).strip()
            config_hash = str(cand.get("config_hash", "")).strip()
            if not variant_id:
                errors.append(f"{where}.variant_id: must be non-empty string")
            if not module:
                errors.append(f"{where}.module: must be non-empty string")
            if not config_hash:
                errors.append(f"{where}.config_hash: must be non-empty string")
            if variant_id:
                if variant_id in seen_variant_ids:
                    errors.append(f"{where}: duplicate variant_id '{variant_id}'")
                seen_variant_ids.add(variant_id)

            circuit_type = str(cand.get("circuit_type", "")).strip()
            if circuit_type and circuit_type not in VALID_CIRCUIT_TYPES:
                errors.append(
                    f"{where}.circuit_type: invalid '{circuit_type}', expected one of {sorted(VALID_CIRCUIT_TYPES)}"
                )

            mref = cand.get("metrics_ref")
            if not isinstance(mref, dict):
                errors.append(f"{where}.metrics_ref: expected object")
                continue
            for key in ("metrics_csv", "platform"):
                if key not in mref:
                    errors.append(f"{where}.metrics_ref: missing required key '{key}'")
            metrics_csv = str(mref.get("metrics_csv", "")).strip()
            platform = str(mref.get("platform", "")).strip()
            if not metrics_csv:
                errors.append(f"{where}.metrics_ref.metrics_csv: must be non-empty string")
                continue
            if not platform:
                errors.append(f"{where}.metrics_ref.platform: must be non-empty string")
                continue

            param_hash = str(mref.get("param_hash", "")).strip()
            tag = str(mref.get("tag", "")).strip()
            if not param_hash and not tag:
                errors.append(f"{where}.metrics_ref: require at least one of param_hash or tag")

            metrics_path = _resolve_repo_path(metrics_csv)
            if not metrics_path.exists():
                errors.append(f"{where}.metrics_ref.metrics_csv: path does not exist: {metrics_csv}")
                continue

            _, rows = _read_metrics_cached(metrics_path, metrics_cache)
            matches = []
            for row in rows:
                if str(row.get("platform", "")).strip() != platform:
                    continue
                if param_hash and str(row.get("param_hash", "")).strip() != param_hash:
                    continue
                if tag and str(row.get("tag", "")).strip() != tag:
                    continue
                mref_cfg = str(mref.get("config_hash", "")).strip()
                if mref_cfg and str(row.get("config_hash", "")).strip() != mref_cfg:
                    continue
                mref_status = str(mref.get("status", "")).strip()
                if mref_status and str(row.get("status", "")).strip() != mref_status:
                    continue
                matches.append(row)

            if not matches:
                errors.append(
                    f"{where}.metrics_ref: no matching metrics row found "
                    f"(platform={platform}, param_hash={param_hash or '*'}, tag={tag or '*'})"
                )
                continue

            if pdk and platform != pdk:
                warnings.append(
                    f"{where}.metrics_ref.platform '{platform}' differs from manifest pdk '{pdk}'"
                )

            if module and any(str(row.get("design", "")).strip() != module for row in matches):
                errors.append(f"{where}: module '{module}' does not match metrics row design field")

            if config_hash and any(str(row.get("config_hash", "")).strip() != config_hash for row in matches):
                errors.append(
                    f"{where}: config_hash '{config_hash}' does not match referenced metrics row config_hash"
                )

            macro_manifest = str(cand.get("macro_manifest", "")).strip()
            if macro_manifest:
                macro_path = _resolve_repo_path(macro_manifest)
                if not macro_path.exists():
                    errors.append(f"{where}.macro_manifest: path does not exist: {macro_manifest}")

    for warn in warnings:
        print(f"WARN: {warn}")
    return errors


def main():
    errors = []
    errors.extend(validate_metrics())
    errors.extend(validate_metadata())
    errors.extend(validate_module_candidates())
    errors.extend(validate_index())
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("OK: runs validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
