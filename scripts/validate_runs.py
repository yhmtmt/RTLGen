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
EVAL_QUEUE_ROOT = REPO_ROOT / "runs" / "eval_queue"
EVAL_QUEUE_SCHEMA_BASENAME = "item.schema.json"

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
VALID_EVALUATION_SCOPES = {"wrapped_io", "macro_hardened"}
VALID_EVAL_QUEUE_STATES = {"queued", "evaluated"}
VALID_EVAL_QUEUE_LAYERS = {"layer1", "layer2"}
VALID_EVAL_QUEUE_RESULT_STATUS = {"ok", "fail", "partial"}
VALID_EVAL_QUEUE_SOURCE_MODES = {"config", "src_verilog"}


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

            for key in ("variant_id", "module", "evaluation_scope", "config_hash", "metrics_ref"):
                if key not in cand:
                    errors.append(f"{where}: missing required key '{key}'")
            variant_id = str(cand.get("variant_id", "")).strip()
            module = str(cand.get("module", "")).strip()
            evaluation_scope = str(cand.get("evaluation_scope", "")).strip()
            config_hash = str(cand.get("config_hash", "")).strip()
            if not variant_id:
                errors.append(f"{where}.variant_id: must be non-empty string")
            if not module:
                errors.append(f"{where}.module: must be non-empty string")
            if evaluation_scope not in VALID_EVALUATION_SCOPES:
                errors.append(
                    f"{where}.evaluation_scope: invalid '{evaluation_scope}', "
                    f"expected one of {sorted(VALID_EVALUATION_SCOPES)}"
                )
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
            if evaluation_scope == "macro_hardened" and not macro_manifest:
                errors.append(f"{where}: macro_hardened candidate requires non-empty macro_manifest")

    for warn in warnings:
        print(f"WARN: {warn}")
    return errors


def _require_non_empty_string(value, where, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: must be non-empty string")
        return ""
    return value.strip()


def _validate_eval_queue_metrics_ref(mref, where, metrics_cache, errors):
    if not isinstance(mref, dict):
        errors.append(f"{where}: expected object")
        return

    metrics_csv = _require_non_empty_string(mref.get("metrics_csv", ""), f"{where}.metrics_csv", errors)
    platform = _require_non_empty_string(mref.get("platform", ""), f"{where}.platform", errors)
    status = _require_non_empty_string(mref.get("status", ""), f"{where}.status", errors)
    param_hash = str(mref.get("param_hash", "")).strip()
    tag = str(mref.get("tag", "")).strip()
    result_path = str(mref.get("result_path", "")).strip()

    if not param_hash and not tag:
        errors.append(f"{where}: require at least one of param_hash or tag")
    if not metrics_csv or not platform or not status:
        return

    metrics_path = _resolve_repo_path(metrics_csv)
    if not metrics_path.exists():
        errors.append(f"{where}.metrics_csv: path does not exist: {metrics_csv}")
        return

    _, rows = _read_metrics_cached(metrics_path, metrics_cache)
    matches = []
    for row in rows:
        if str(row.get("platform", "")).strip() != platform:
            continue
        if str(row.get("status", "")).strip() != status:
            continue
        if param_hash and str(row.get("param_hash", "")).strip() != param_hash:
            continue
        if tag and str(row.get("tag", "")).strip() != tag:
            continue
        if result_path and str(row.get("result_path", "")).strip() != result_path:
            continue
        matches.append(row)

    if not matches:
        errors.append(
            f"{where}: no matching metrics row found "
            f"(platform={platform}, status={status}, param_hash={param_hash or '*'}, tag={tag or '*'})"
        )


def validate_eval_queue():
    errors = []
    warnings = []
    if not EVAL_QUEUE_ROOT.exists():
        return errors

    metrics_cache = {}
    seen_ids = set()

    for flow_dir in sorted(EVAL_QUEUE_ROOT.iterdir()):
        if not flow_dir.is_dir():
            continue

        flow_name = flow_dir.name
        schema_path = flow_dir / EVAL_QUEUE_SCHEMA_BASENAME
        if not schema_path.exists():
            warnings.append(f"{flow_dir}: missing {EVAL_QUEUE_SCHEMA_BASENAME}")

        for state in sorted(VALID_EVAL_QUEUE_STATES):
            state_dir = flow_dir / state
            if not state_dir.exists():
                continue
            if not state_dir.is_dir():
                errors.append(f"{state_dir}: expected directory")
                continue

            for item_path in sorted(state_dir.glob("*.json")):
                try:
                    with item_path.open("r", encoding="utf-8") as f:
                        item = json.load(f)
                except json.JSONDecodeError as exc:
                    errors.append(f"{item_path}: invalid JSON: {exc}")
                    continue

                where = str(item_path)
                if not isinstance(item, dict):
                    errors.append(f"{where}: top-level must be an object")
                    continue

                for key in (
                    "version",
                    "item_id",
                    "title",
                    "layer",
                    "flow",
                    "state",
                    "priority",
                    "created_utc",
                    "requested_by",
                    "platform",
                    "task",
                    "handoff",
                ):
                    if key not in item:
                        errors.append(f"{where}: missing required key '{key}'")

                if item.get("version") != 0.1:
                    errors.append(f"{where}: version must be 0.1")

                item_id = _require_non_empty_string(item.get("item_id", ""), f"{where}.item_id", errors)
                if item_id:
                    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", item_id):
                        errors.append(f"{where}.item_id: invalid format '{item_id}'")
                    if item_id in seen_ids:
                        errors.append(f"{where}.item_id: duplicate id '{item_id}' across eval queue")
                    seen_ids.add(item_id)

                _require_non_empty_string(item.get("title", ""), f"{where}.title", errors)
                layer = _require_non_empty_string(item.get("layer", ""), f"{where}.layer", errors)
                if layer and layer not in VALID_EVAL_QUEUE_LAYERS:
                    errors.append(f"{where}.layer: invalid '{layer}', expected one of {sorted(VALID_EVAL_QUEUE_LAYERS)}")

                flow = _require_non_empty_string(item.get("flow", ""), f"{where}.flow", errors)
                if flow and flow != flow_name:
                    errors.append(f"{where}.flow: '{flow}' must match directory name '{flow_name}'")

                state_value = _require_non_empty_string(item.get("state", ""), f"{where}.state", errors)
                if state_value and state_value not in VALID_EVAL_QUEUE_STATES:
                    errors.append(f"{where}.state: invalid '{state_value}', expected one of {sorted(VALID_EVAL_QUEUE_STATES)}")
                if state_value and state_value != state:
                    errors.append(f"{where}.state: '{state_value}' does not match parent directory '{state}'")

                priority = item.get("priority")
                if isinstance(priority, bool) or not isinstance(priority, int) or priority < 0 or priority > 5:
                    errors.append(f"{where}.priority: must be integer in range [0, 5]")

                _require_non_empty_string(item.get("created_utc", ""), f"{where}.created_utc", errors)
                _require_non_empty_string(item.get("requested_by", ""), f"{where}.requested_by", errors)
                _require_non_empty_string(item.get("platform", ""), f"{where}.platform", errors)

                task = item.get("task")
                if not isinstance(task, dict):
                    errors.append(f"{where}.task: expected object")
                else:
                    _require_non_empty_string(task.get("objective", ""), f"{where}.task.objective", errors)
                    source_mode = _require_non_empty_string(
                        task.get("source_mode", ""),
                        f"{where}.task.source_mode",
                        errors,
                    )
                    if source_mode and source_mode not in VALID_EVAL_QUEUE_SOURCE_MODES:
                        errors.append(
                            f"{where}.task.source_mode: invalid '{source_mode}', "
                            f"expected one of {sorted(VALID_EVAL_QUEUE_SOURCE_MODES)}"
                        )
                        source_mode = ""

                    commands = task.get("commands")
                    if not isinstance(commands, list) or not commands:
                        errors.append(f"{where}.task.commands: must be non-empty array")
                    else:
                        for i, cmd in enumerate(commands):
                            cwhere = f"{where}.task.commands[{i}]"
                            if not isinstance(cmd, dict):
                                errors.append(f"{cwhere}: expected object")
                                continue
                            _require_non_empty_string(cmd.get("name", ""), f"{cwhere}.name", errors)
                            run_cmd = _require_non_empty_string(cmd.get("run", ""), f"{cwhere}.run", errors)
                            if run_cmd and "pre_synth_compute.py" in run_cmd:
                                has_config_flag = bool(re.search(r"(?:^|\s)--config(?:\s|$)", run_cmd))
                                has_src_flag = bool(re.search(r"(?:^|\s)--src_verilog_dir(?:\s|$)", run_cmd))
                                if source_mode == "config":
                                    if not has_config_flag:
                                        errors.append(
                                            f"{cwhere}.run: source_mode=config requires --config for pre_synth_compute.py"
                                        )
                                    if has_src_flag:
                                        errors.append(
                                            f"{cwhere}.run: source_mode=config must not include --src_verilog_dir"
                                        )
                                    module_match = re.search(r"(?:^|\s)--module\s+([^\s]+)", run_cmd)
                                    if module_match:
                                        module_name = module_match.group(1).strip()
                                        if module_name.endswith("_wrapper"):
                                            errors.append(
                                                f"{cwhere}.run: --module {module_name} looks like wrapper; "
                                                "use source_mode=src_verilog with --src_verilog_dir"
                                            )
                                elif source_mode == "src_verilog":
                                    if not has_src_flag:
                                        errors.append(
                                            f"{cwhere}.run: source_mode=src_verilog requires --src_verilog_dir "
                                            "for pre_synth_compute.py"
                                        )
                                    if has_config_flag:
                                        errors.append(
                                            f"{cwhere}.run: source_mode=src_verilog must not include --config"
                                        )

                    expected_outputs = task.get("expected_outputs")
                    if not isinstance(expected_outputs, list) or not expected_outputs:
                        errors.append(f"{where}.task.expected_outputs: must be non-empty array")
                    else:
                        for i, out in enumerate(expected_outputs):
                            _require_non_empty_string(out, f"{where}.task.expected_outputs[{i}]", errors)

                    inputs = task.get("inputs", {})
                    if inputs is not None:
                        if not isinstance(inputs, dict):
                            errors.append(f"{where}.task.inputs: expected object")
                        else:
                            input_lists = {}
                            for key in ("configs", "design_dirs", "sweeps", "macro_manifests", "candidate_manifests"):
                                values = inputs.get(key, [])
                                if not isinstance(values, list):
                                    errors.append(f"{where}.task.inputs.{key}: expected array")
                                    continue
                                input_lists[key] = values
                                for i, path_text in enumerate(values):
                                    text = _require_non_empty_string(
                                        path_text, f"{where}.task.inputs.{key}[{i}]", errors
                                    )
                                    if text:
                                        p = _resolve_repo_path(text)
                                        if not p.exists():
                                            errors.append(f"{where}.task.inputs.{key}[{i}]: path does not exist: {text}")
                            if source_mode == "config":
                                if not input_lists.get("configs"):
                                    errors.append(
                                        f"{where}.task.inputs.configs: source_mode=config requires at least one config path"
                                    )
                            elif source_mode == "src_verilog":
                                if not input_lists.get("design_dirs"):
                                    errors.append(
                                        f"{where}.task.inputs.design_dirs: source_mode=src_verilog "
                                        "requires at least one design_dir path"
                                    )

                handoff = item.get("handoff")
                if not isinstance(handoff, dict):
                    errors.append(f"{where}.handoff: expected object")
                else:
                    _require_non_empty_string(handoff.get("branch", ""), f"{where}.handoff.branch", errors)
                    _require_non_empty_string(handoff.get("pr_title", ""), f"{where}.handoff.pr_title", errors)
                    checklist = handoff.get("checklist")
                    if not isinstance(checklist, list) or not checklist:
                        errors.append(f"{where}.handoff.checklist: must be non-empty array")
                    else:
                        for i, text in enumerate(checklist):
                            _require_non_empty_string(text, f"{where}.handoff.checklist[{i}]", errors)

                if state == "queued":
                    if item.get("result") not in (None, {}):
                        errors.append(f"{where}.result: queued item must not contain result payload")
                else:
                    result = item.get("result")
                    if not isinstance(result, dict):
                        errors.append(f"{where}.result: evaluated item requires object result")
                        continue
                    for key in ("completed_utc", "executor", "branch", "status", "summary", "metrics_rows"):
                        if key not in result:
                            errors.append(f"{where}.result: missing required key '{key}'")
                    _require_non_empty_string(result.get("completed_utc", ""), f"{where}.result.completed_utc", errors)
                    _require_non_empty_string(result.get("executor", ""), f"{where}.result.executor", errors)
                    _require_non_empty_string(result.get("branch", ""), f"{where}.result.branch", errors)
                    _require_non_empty_string(result.get("summary", ""), f"{where}.result.summary", errors)
                    result_status = _require_non_empty_string(result.get("status", ""), f"{where}.result.status", errors)
                    if result_status and result_status not in VALID_EVAL_QUEUE_RESULT_STATUS:
                        errors.append(
                            f"{where}.result.status: invalid '{result_status}', "
                            f"expected one of {sorted(VALID_EVAL_QUEUE_RESULT_STATUS)}"
                        )

                    metrics_rows = result.get("metrics_rows")
                    if not isinstance(metrics_rows, list):
                        errors.append(f"{where}.result.metrics_rows: expected array")
                    else:
                        if result_status == "ok" and not metrics_rows:
                            errors.append(f"{where}.result.metrics_rows: status=ok requires at least one metrics row")
                        for i, mref in enumerate(metrics_rows):
                            _validate_eval_queue_metrics_ref(
                                mref,
                                f"{where}.result.metrics_rows[{i}]",
                                metrics_cache,
                                errors,
                            )

    for warn in warnings:
        print(f"WARN: {warn}")
    return errors


def main():
    errors = []
    errors.extend(validate_metrics())
    errors.extend(validate_metadata())
    errors.extend(validate_module_candidates())
    errors.extend(validate_eval_queue())
    errors.extend(validate_index())
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("OK: runs validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
