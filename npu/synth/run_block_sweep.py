#!/usr/bin/env python3
"""
OpenROAD sweep driver for block-level NPU macros.

Example:
  python npu/synth/run_block_sweep.py \
    --design_dir runs/designs/npu_blocks/dma_stub \
    --platform nangate45 \
    --top dma_stub \
    --sweep npu/synth/block_sweep_example.json
"""

import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEST_BASE = Path("/orfs/flow/designs")
REPORT_BASE = Path("/orfs/flow/reports")
RESULT_BASE = Path("/orfs/flow/results")
LOG_BASE = Path("/orfs/flow/logs")
SRC_BASE = DEST_BASE / "src"


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_verilog_dir(verilog_dir: Path) -> str:
    hashes = []
    for v in sorted(verilog_dir.glob("*.v")):
        hashes.append(sha1_file(v))
    payload = "".join(hashes)
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def resolve_manifest_path(path_value: str, manifest_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    local = (manifest_path.parent / path).resolve()
    if local.exists():
        return local
    return (REPO_ROOT / path).resolve()


def load_macro_manifest(manifest_path: Optional[Path]) -> Optional[Dict[str, object]]:
    if manifest_path is None:
        return None
    raw = load_json(manifest_path)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid macro manifest format: {manifest_path}")

    blackboxes = [str(x).strip() for x in raw.get("blackboxes", []) if str(x).strip()]
    additional_lefs = [
        resolve_manifest_path(str(x), manifest_path)
        for x in raw.get("additional_lefs", [])
    ]
    additional_libs = [
        resolve_manifest_path(str(x), manifest_path)
        for x in raw.get("additional_libs", [])
    ]
    additional_gds = [
        resolve_manifest_path(str(x), manifest_path)
        for x in raw.get("additional_gds", [])
    ]
    blackbox_verilog = [
        resolve_manifest_path(str(x), manifest_path)
        for x in raw.get("blackbox_verilog", [])
    ]

    macro_placement_tcl = raw.get("macro_placement_tcl")
    placement_path = None
    if macro_placement_tcl:
        placement_path = resolve_manifest_path(str(macro_placement_tcl), manifest_path)

    for path in additional_lefs + additional_libs + additional_gds + blackbox_verilog:
        if not path.exists():
            raise FileNotFoundError(f"Macro manifest file not found: {path}")
    if placement_path and not placement_path.exists():
        raise FileNotFoundError(f"Macro placement file not found: {placement_path}")

    return {
        "blackboxes": blackboxes,
        "additional_lefs": additional_lefs,
        "additional_libs": additional_libs,
        "additional_gds": additional_gds,
        "blackbox_verilog": blackbox_verilog,
        "macro_placement_tcl": placement_path,
        "manifest_path": manifest_path.resolve(),
    }


def normalize_match_token(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value).strip()


def parse_macro_select_args(values: Optional[List[str]]) -> Dict[str, object]:
    selectors: Dict[str, object] = {}
    for raw in values or []:
        token = str(raw).strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(f"Invalid --macro_select value (expected key=value): {raw}")
        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --macro_select key in: {raw}")
        selectors[key] = value
    return selectors


def flatten_selector_dict(obj: object, prefix: str = "") -> Dict[str, object]:
    flat: Dict[str, object] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_txt = str(key)
            child = f"{prefix}.{key_txt}" if prefix else key_txt
            flat.update(flatten_selector_dict(value, child))
        return flat
    if prefix:
        flat[prefix] = obj
    return flat


def entry_matches_context(when: Dict[str, object], context: Dict[str, object]) -> bool:
    for key, expected in when.items():
        if key not in context:
            return False
        actual_token = normalize_match_token(context[key])
        if isinstance(expected, list):
            expected_tokens = [normalize_match_token(x) for x in expected]
            if actual_token not in expected_tokens:
                return False
        else:
            if actual_token != normalize_match_token(expected):
                return False
    return True


def load_macro_library(library_path: Path) -> Dict[str, object]:
    raw = load_json(library_path)
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid macro library format: {library_path}")

    raw_entries = raw.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError(f"Macro library must contain non-empty entries[]: {library_path}")

    entries: List[Dict[str, object]] = []
    for index, item in enumerate(raw_entries):
        if not isinstance(item, dict):
            raise ValueError(f"Macro library entries[{index}] must be an object")
        if item.get("enabled") is False:
            continue

        manifest_value = item.get("manifest", item.get("macro_manifest", ""))
        if not str(manifest_value).strip():
            raise ValueError(
                f"Macro library entries[{index}] missing manifest/macro_manifest path"
            )
        manifest_path = resolve_manifest_path(str(manifest_value), library_path)
        manifest = load_macro_manifest(manifest_path.resolve())
        if manifest is None:
            raise ValueError(f"Failed to load manifest for library entry {index}: {manifest_path}")

        name = str(item.get("name", f"entry_{index}")).strip() or f"entry_{index}"
        when_raw = item.get("when", {})
        if when_raw is None:
            when_raw = {}
        if not isinstance(when_raw, dict):
            raise ValueError(f"Macro library entries[{index}].when must be an object")
        when: Dict[str, object] = {str(k): v for k, v in when_raw.items()}

        try:
            priority = int(item.get("priority", 0))
        except Exception as exc:
            raise ValueError(
                f"Macro library entries[{index}].priority must be an integer: {exc}"
            ) from exc

        entries.append(
            {
                "index": index,
                "name": name,
                "manifest": manifest,
                "manifest_path": manifest_path.resolve(),
                "when": when,
                "priority": priority,
                "notes": str(item.get("notes", "")),
            }
        )

    if not entries:
        raise ValueError(f"Macro library has no enabled entries: {library_path}")

    return {
        "library_path": library_path.resolve(),
        "entries": entries,
        "default_entry": str(raw.get("default_entry", "")).strip(),
        "require_match": bool(raw.get("require_match", False)),
    }


def select_macro_manifest_from_library(
    macro_library: Dict[str, object],
    context: Dict[str, object],
    require_match: bool = False,
) -> tuple[Optional[Dict[str, object]], Optional[Dict[str, object]]]:
    entries: List[Dict[str, object]] = macro_library.get("entries", [])
    matches: List[Dict[str, object]] = []
    for entry in entries:
        when = entry.get("when", {})
        if not isinstance(when, dict):
            continue
        if entry_matches_context(when, context):
            matches.append(entry)

    if matches:
        matches.sort(
            key=lambda e: (
                int(e.get("priority", 0)),
                len(e.get("when", {})),
                -int(e.get("index", 0)),
            ),
            reverse=True,
        )
        selected = matches[0]
        if len(matches) > 1:
            first = matches[0]
            second = matches[1]
            if (
                int(first.get("priority", 0)) == int(second.get("priority", 0))
                and len(first.get("when", {})) == len(second.get("when", {}))
            ):
                print(
                    "[WARN] Macro library selection tie; choosing first match by index: "
                    f"{first.get('name')} over {second.get('name')}"
                )
        return selected["manifest"], {
            "mode": "library",
            "library_path": str(macro_library.get("library_path", "")),
            "entry_name": str(selected.get("name", "")),
            "entry_index": int(selected.get("index", -1)),
            "entry_priority": int(selected.get("priority", 0)),
            "manifest_path": str(selected.get("manifest_path", "")),
            "when": selected.get("when", {}),
        }

    default_entry = str(macro_library.get("default_entry", "")).strip()
    if default_entry:
        for entry in entries:
            if str(entry.get("name", "")) == default_entry:
                return entry["manifest"], {
                    "mode": "library_default",
                    "library_path": str(macro_library.get("library_path", "")),
                    "entry_name": str(entry.get("name", "")),
                    "entry_index": int(entry.get("index", -1)),
                    "entry_priority": int(entry.get("priority", 0)),
                    "manifest_path": str(entry.get("manifest_path", "")),
                    "when": entry.get("when", {}),
                }
        raise ValueError(
            "Macro library default_entry not found in entries: "
            f"{default_entry} ({macro_library.get('library_path')})"
        )

    if require_match or bool(macro_library.get("require_match", False)):
        raise ValueError(
            "No macro library entry matched selector context and require_match is set."
        )
    return None, None


def cartesian_product(grid: Dict[str, List]) -> List[Dict[str, object]]:
    keys = sorted(grid.keys())
    values = []
    for k in keys:
        v = grid[k]
        if not isinstance(v, list):
            v = [v]
        values.append(v)
    combos = []
    for prod in itertools.product(*values):
        combos.append({k: v for k, v in zip(keys, prod)})
    return combos


def make_run_id(
    params: Dict[str, object], extra: Optional[Dict[str, object]] = None
) -> str:
    if extra:
        payload = json.dumps({"params": params, "extra": extra}, sort_keys=True)
    else:
        payload = json.dumps(params, sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()[:8]


def slugify_token(value: str, fallback: str = "mode") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_")
    if not slug:
        return fallback
    return slug


def parse_bool_token(value: object, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token in {"1", "true", "yes", "on", "use", "enable", "enabled"}:
        return True
    if token in {"0", "false", "no", "off", "none", "disable", "disabled"}:
        return False
    raise ValueError(f"Invalid boolean token: {value}")


def default_mode_compare_entries() -> List[Dict[str, object]]:
    return [
        {
            "name": "flat_nomacro",
            "use_macro": False,
            "param_overrides": {
                "SYNTH_HIERARCHICAL": 0,
                "SYNTH_KEEP_MODULES": "",
            },
            "notes": "Flattened baseline without hardened macros",
        },
        {
            "name": "hier_macro",
            "use_macro": True,
            "param_overrides": {"SYNTH_HIERARCHICAL": 1},
            "notes": "Hierarchical top-level with hardened macro abstraction",
        },
    ]


def parse_mode_compare_config(sweep: Dict[str, object]) -> Optional[Dict[str, object]]:
    raw = sweep.get("mode_compare")
    if raw is None:
        return None

    repeat_count = 1

    if isinstance(raw, bool):
        if not raw:
            return None
        raw_modes = default_mode_compare_entries()
        report_dir = "comparisons"
    elif isinstance(raw, list):
        raw_modes = raw
        report_dir = "comparisons"
    elif isinstance(raw, dict):
        if raw.get("enabled", True) is False:
            return None
        raw_modes = raw.get("modes")
        if raw_modes is None:
            raw_modes = default_mode_compare_entries()
        if not isinstance(raw_modes, list):
            raise ValueError("mode_compare.modes must be a list")
        report_dir = str(raw.get("report_dir", "comparisons")).strip() or "comparisons"
        raw_repeat = raw.get("repeat", 1)
        try:
            repeat_count = int(raw_repeat)
        except Exception as exc:
            raise ValueError(f"mode_compare.repeat must be an integer: {exc}") from exc
        if repeat_count < 1:
            raise ValueError("mode_compare.repeat must be >= 1")
    else:
        raise ValueError(
            "mode_compare must be one of: bool, list, or object with enabled/modes/report_dir"
        )

    if not raw_modes:
        raise ValueError("mode_compare requires at least one mode entry")

    parsed_modes: List[Dict[str, object]] = []
    used_slugs: Dict[str, int] = {}
    for index, item in enumerate(raw_modes):
        if not isinstance(item, dict):
            raise ValueError(f"mode_compare.modes[{index}] must be an object")
        name = str(item.get("name", f"mode_{index + 1}")).strip() or f"mode_{index + 1}"
        slug = slugify_token(name, fallback=f"mode_{index + 1}")
        slug_count = used_slugs.get(slug, 0)
        used_slugs[slug] = slug_count + 1
        if slug_count > 0:
            slug = f"{slug}_{slug_count + 1}"
        use_macro = parse_bool_token(item.get("use_macro", True), default=True)
        raw_overrides = item.get("param_overrides", item.get("flow_params", {}))
        if raw_overrides is None:
            raw_overrides = {}
        if not isinstance(raw_overrides, dict):
            raise ValueError(
                f"mode_compare.modes[{index}].param_overrides must be an object"
            )
        param_overrides: Dict[str, object] = {
            str(key): value for key, value in raw_overrides.items()
        }
        parsed_modes.append(
            {
                "name": name,
                "slug": slug,
                "use_macro": use_macro,
                "param_overrides": param_overrides,
                "notes": str(item.get("notes", "")),
            }
        )

    return {
        "report_dir": report_dir,
        "repeat": repeat_count,
        "modes": parsed_modes,
    }


def apply_mode_to_params(
    base_params: Dict[str, object],
    mode: Dict[str, object],
    default_tag_prefix: str,
) -> Dict[str, object]:
    params = dict(base_params)
    overrides: Dict[str, object] = dict(mode.get("param_overrides", {}))
    params.update(overrides)
    override_keys = set(overrides.keys())

    mode_slug = str(mode.get("slug", "mode")).strip() or "mode"
    if "TAG" in params and "TAG" not in override_keys:
        params["TAG"] = f"{params['TAG']}_{mode_slug}"

    if "FLOW_VARIANT" in params and "FLOW_VARIANT" not in override_keys:
        params["FLOW_VARIANT"] = f"{params['FLOW_VARIANT']}_{mode_slug}"
    elif "FLOW_VARIANT" not in params:
        params["FLOW_VARIANT"] = mode_slug

    if "TAG" not in params:
        base_prefix = str(params.get("tag_prefix", default_tag_prefix)).strip() or default_tag_prefix
        if "tag_prefix" in override_keys:
            params["tag_prefix"] = str(params["tag_prefix"])
        else:
            params["tag_prefix"] = f"{base_prefix}_{mode_slug}"

    return params


def write_sdc(clock_period: float, path: Path, clock_port: str = "clk"):
    if clock_port:
        content = f"""set clock_port "{clock_port}"
set clock_period {clock_period}
set input_delay 2.0
set output_delay 2.0

create_clock [get_ports $clock_port] -period $clock_period

set_input_delay $input_delay -clock $clock_port [all_inputs]
set_output_delay $output_delay -clock $clock_port [all_outputs]

set_load -pin_load 0.05 [all_outputs]
"""
    else:
        content = """# Combinational / clockless block constraint template
set_load -pin_load 0.05 [all_outputs]
"""
    path.write_text(content)


def parse_finish_report(report_path: Path) -> Dict[str, object]:
    metrics: Dict[str, object] = {}
    try:
        lines = report_path.read_text().splitlines()
    except FileNotFoundError:
        return metrics

    for i, line in enumerate(lines):
        if "finish critical path delay" in line and i + 2 < len(lines):
            metrics["critical_path_ns"] = safe_float(lines[i + 2].strip())
            break

    for i, line in enumerate(lines):
        if "finish report_power" in line and i + 11 < len(lines):
            parts = lines[i + 11].split()
            if len(parts) >= 5:
                metrics["total_power_mw"] = safe_float(parts[4])
            break

    return metrics


def parse_die_area(def_path: Path) -> float:
    dbu_per_micron = 1.0
    die_area = 0.0

    try:
        with def_path.open() as f:
            for line in f:
                line = line.strip()
                if line.startswith("UNITS DISTANCE MICRONS"):
                    parts = line.replace(";", "").split()
                    if len(parts) >= 4:
                        try:
                            dbu_per_micron = float(parts[3])
                        except ValueError:
                            dbu_per_micron = 1.0
                elif line.startswith("DIEAREA"):
                    m = re.search(
                        r"DIEAREA\s+\(\s*(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s*\)",
                        line,
                    )
                    if m:
                        x1, y1, x2, y2 = map(int, m.groups())
                        width = max(0, x2 - x1)
                        height = max(0, y2 - y1)
                        die_area = float(width * height)
                        break
    except FileNotFoundError:
        return 0.0

    if dbu_per_micron > 0 and die_area > 0:
        return die_area / (dbu_per_micron * dbu_per_micron)
    return 0.0


def parse_rect_param(value: object) -> Optional[tuple[float, float, float, float]]:
    if value is None:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    parts = txt.replace(",", " ").split()
    if len(parts) != 4:
        return None
    try:
        x1, y1, x2, y2 = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
    except ValueError:
        return None
    return x1, y1, x2, y2


def parse_macro_size_from_lef(lef_path: Path) -> Optional[tuple[float, float]]:
    try:
        text = lef_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(
        r"(?im)^\s*SIZE\s+([0-9]*\.?[0-9]+)\s+BY\s+([0-9]*\.?[0-9]+)\s*;",
        text,
    )
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except ValueError:
        return None


def validate_macro_fit_in_core(
    macro_manifest: Optional[Dict[str, object]],
    sweep_params: Dict[str, object],
) -> None:
    if macro_manifest is None:
        return
    core = parse_rect_param(sweep_params.get("CORE_AREA"))
    if core is None:
        return
    _, _, core_x2, core_y2 = core
    core_x1, core_y1, _, _ = core
    core_w = max(0.0, core_x2 - core_x1)
    core_h = max(0.0, core_y2 - core_y1)
    if core_w <= 0 or core_h <= 0:
        return

    for lef in macro_manifest.get("additional_lefs", []):
        lef_path = Path(lef)
        size = parse_macro_size_from_lef(lef_path)
        if size is None:
            continue
        macro_w, macro_h = size
        if macro_w > core_w or macro_h > core_h:
            raise ValueError(
                "Macro LEF does not fit requested CORE_AREA: "
                f"{lef_path.name} size=({macro_w}um, {macro_h}um) "
                f"core=({core_w}um, {core_h}um). "
                "Re-harden macro with smaller die/core area or increase top-level floorplan."
            )


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def parse_stage_metrics(metrics_json_path: Path, stage_prefix: str) -> Dict[str, object]:
    metrics: Dict[str, object] = {}
    try:
        data = json.loads(metrics_json_path.read_text())
    except FileNotFoundError:
        return metrics
    except json.JSONDecodeError:
        return metrics

    fmax_hz = safe_float(data.get(f"{stage_prefix}__timing__fmax"))
    if fmax_hz is not None and fmax_hz > 0:
        metrics["critical_path_ns"] = 1.0e9 / fmax_hz
    metrics["total_power_mw"] = safe_float(data.get(f"{stage_prefix}__power__total"))
    metrics["die_area"] = safe_float(data.get(f"{stage_prefix}__design__die__area"))
    return metrics


def parse_elapsed_seconds_from_text(text: str) -> Optional[float]:
    m = re.search(r"Elapsed time:\s*(\d+):(\d+(?:\.\d+)?)\[h:\]min:sec\.", text)
    if not m:
        return None
    try:
        minutes = int(m.group(1))
        seconds = float(m.group(2))
    except ValueError:
        return None
    return minutes * 60.0 + seconds


def parse_elapsed_seconds_from_log(log_path: Path) -> Optional[float]:
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return None
    return parse_elapsed_seconds_from_text(text)


def sum_elapsed_seconds_in_log_dir(log_dir: Path) -> Optional[float]:
    if not log_dir.is_dir():
        return None
    total = 0.0
    found = False
    for log_path in sorted(log_dir.glob("*.log")):
        elapsed = parse_elapsed_seconds_from_log(log_path)
        if elapsed is None:
            continue
        total += elapsed
        found = True
    if not found:
        return None
    return total


def resolve_flow_log_dir(platform: str, design_name: str, tag: str, flow_variant: str) -> Path:
    tag_dir = LOG_BASE / platform / design_name / str(tag)
    if tag_dir.is_dir():
        return tag_dir
    variant_dir = LOG_BASE / platform / design_name / str(flow_variant)
    if variant_dir.is_dir():
        return variant_dir
    base_dir = LOG_BASE / platform / design_name / "base"
    if base_dir.is_dir():
        return base_dir
    return variant_dir


def resolve_stage_metrics_path(
    platform: str,
    design_name: str,
    tag: str,
    make_target: str,
    flow_variant: str,
) -> Path:
    tag_path = LOG_BASE / platform / design_name / str(tag) / f"{make_target}.json"
    if tag_path.exists():
        return tag_path
    variant_path = LOG_BASE / platform / design_name / flow_variant / f"{make_target}.json"
    if variant_path.exists():
        return variant_path
    base_path = LOG_BASE / platform / design_name / "base" / f"{make_target}.json"
    if base_path.exists():
        return base_path
    return tag_path


def count_blackbox_instances_in_netlist(
    netlist_path: Path, blackboxes: List[str]
) -> Dict[str, int]:
    counts = {name: 0 for name in blackboxes}
    if not blackboxes or not netlist_path.exists():
        return counts
    text = netlist_path.read_text(encoding="utf-8", errors="ignore")
    for name in blackboxes:
        # Match module-name-led instantiations (optionally escaped), with or without parameterization.
        pattern = re.compile(
            rf"(?m)^\s*\\?{re.escape(name)}\s*(?:#\s*\(|\s+)"
        )
        counts[name] = len(pattern.findall(text))
    return counts


def metal_layer_number(layer_name: str) -> Optional[int]:
    m = re.fullmatch(r"metal(\d+)", str(layer_name).strip(), flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def max_pg_pin_layer_in_lef(lef_text: str) -> Optional[int]:
    max_pg_layer: Optional[int] = None
    current_pin: Optional[str] = None
    pg_pin = False

    for line in lef_text.splitlines():
        s = line.strip()
        pin_match = re.match(r"PIN\s+(\S+)", s)
        if pin_match:
            current_pin = pin_match.group(1)
            pg_pin = False
            continue
        if current_pin is None:
            continue

        if re.match(r"USE\s+(POWER|GROUND)\s*;", s, flags=re.IGNORECASE):
            pg_pin = True
            continue

        layer_match = re.match(r"LAYER\s+([^\s;]+)\s*;", s, flags=re.IGNORECASE)
        if pg_pin and layer_match:
            layer_num = metal_layer_number(layer_match.group(1))
            if layer_num is not None:
                if max_pg_layer is None or layer_num > max_pg_layer:
                    max_pg_layer = layer_num
            continue

        end_match = re.match(r"END\s+(\S+)$", s)
        if end_match and end_match.group(1) == current_pin:
            current_pin = None
            pg_pin = False

    return max_pg_layer


def sanitize_lef_obs_above_layer(lef_text: str, max_layer: int) -> tuple[str, List[str]]:
    out_lines: List[str] = []
    removed_layers: List[str] = []
    in_obs = False
    skip_layer = False

    for line in lef_text.splitlines():
        s = line.strip()
        if not in_obs:
            out_lines.append(line)
            if s == "OBS":
                in_obs = True
            continue

        if s == "END":
            in_obs = False
            skip_layer = False
            out_lines.append(line)
            continue

        layer_match = re.match(r"LAYER\s+([^\s;]+)\s*;", s, flags=re.IGNORECASE)
        if layer_match:
            layer_name = layer_match.group(1)
            layer_num = metal_layer_number(layer_name)
            if layer_num is not None and layer_num > max_layer:
                skip_layer = True
                if layer_name not in removed_layers:
                    removed_layers.append(layer_name)
                continue
            skip_layer = False
            out_lines.append(line)
            continue

        if not skip_layer:
            out_lines.append(line)

    sanitized = "\n".join(out_lines) + "\n"
    return sanitized, removed_layers


def copy_or_sanitize_macro_lef(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8", errors="ignore")
    max_pg_layer = max_pg_pin_layer_in_lef(text)
    if max_pg_layer is None:
        shutil.copy(src, dst)
        return

    sanitized_text, removed_layers = sanitize_lef_obs_above_layer(text, max_pg_layer)
    if removed_layers:
        dst.write_text(sanitized_text, encoding="utf-8")
        removed = ", ".join(removed_layers)
        print(
            "[INFO] Sanitized macro LEF obstructions above PG pin layer "
            f"metal{max_pg_layer}: {src} -> {dst} (removed: {removed})"
        )
        return

    shutil.copy(src, dst)


def write_preserve_blackbox_synth_script(script_path: Path):
    base_synth = Path("/orfs/flow/scripts/synth.tcl")
    if not base_synth.exists():
        raise FileNotFoundError(base_synth)
    text = base_synth.read_text(encoding="utf-8")

    hierarchy_marker = "hierarchy -check -top $::env(DESIGN_NAME)\n"
    if hierarchy_marker not in text:
        raise RuntimeError("Failed to locate hierarchy marker in synth.tcl")
    keep_block = (
        "if { [env_var_exists_and_non_empty SYNTH_BLACKBOXES] } {\n"
        "  foreach m $::env(SYNTH_BLACKBOXES) {\n"
        "    setattr -set keep 1 t:$m\n"
        "  }\n"
        "}\n"
    )
    text = text.replace(hierarchy_marker, hierarchy_marker + "\n" + keep_block + "\n", 1)

    setundef_marker = "setundef -zero"
    if setundef_marker not in text:
        raise RuntimeError("Failed to locate setundef marker in synth.tcl")
    setundef_block = (
        "if { [env_var_exists_and_non_empty SYNTH_BLACKBOXES] } {\n"
        "  puts \"SYNTH_BLACKBOXES set -> skipping setundef -zero to preserve macro instances\"\n"
        "} else {\n"
        "  setundef -zero\n"
        "}"
    )
    text = text.replace(setundef_marker, setundef_block, 1)

    script_path.write_text(text, encoding="utf-8")


def copy_manifest_assets(
    manifest: Dict[str, object],
    dest_platform_dir: Path,
    design_name: str,
    platform: str,
) -> Dict[str, object]:
    macros_dir = dest_platform_dir / "macros"
    macros_dir.mkdir(parents=True, exist_ok=True)

    def _copy_files(paths: List[Path], sanitize_lef: bool = False) -> List[str]:
        copied = []
        for src in paths:
            suffix = src.suffix
            stem = src.stem
            dst = macros_dir / src.name
            if dst.exists():
                src_hash = sha1_file(src)[:8]
                dst = macros_dir / f"{stem}_{src_hash}{suffix}"
            if sanitize_lef and src.suffix.lower() == ".lef":
                copy_or_sanitize_macro_lef(src, dst)
            else:
                shutil.copy(src, dst)
            copied.append(f"$(DESIGN_HOME)/{platform}/{design_name}/macros/{dst.name}")
        return copied

    lef_entries = _copy_files(manifest.get("additional_lefs", []), sanitize_lef=True)
    lib_entries = _copy_files(manifest.get("additional_libs", []))
    gds_entries = _copy_files(manifest.get("additional_gds", []))

    placement_rel = ""
    placement_path = manifest.get("macro_placement_tcl")
    if placement_path is not None:
        placement_dst = dest_platform_dir / "macro_placement.tcl"
        shutil.copy(placement_path, placement_dst)
        placement_rel = f"$(DESIGN_HOME)/{platform}/{design_name}/macro_placement.tcl"

    return {
        "additional_lefs": lef_entries,
        "additional_libs": lib_entries,
        "additional_gds": gds_entries,
        "macro_placement_tcl": placement_rel,
        "blackboxes": manifest.get("blackboxes", []),
    }


def copy_manifest_blackbox_verilog(manifest: Dict[str, object], dest_src_dir: Path):
    for src in manifest.get("blackbox_verilog", []):
        src_path = Path(src)
        dst = dest_src_dir / src_path.name
        if dst.exists():
            src_hash = sha1_file(src_path)[:8]
            dst = dest_src_dir / f"{src_path.stem}_{src_hash}{src_path.suffix}"
        shutil.copy(src_path, dst)


def is_synth_target(make_target: Optional[str]) -> bool:
    if not make_target:
        return False
    return make_target in {
        "synth",
        "1_1_yosys_canonicalize",
        "1_2_yosys",
        "1_2_yosys.v",
        "1_3_synth",
        "1_synth",
        "1_synth.v",
    }


def deduplicate_verilog_sources(src_dir: Path) -> List[Path]:
    kept: List[Path] = []
    seen_hashes: Dict[str, Path] = {}
    for src in sorted(src_dir.glob("*.v")):
        file_hash = sha1_file(src)
        if file_hash in seen_hashes:
            print(
                "[INFO] Removing duplicate Verilog source by content hash: "
                f"{src.name} (duplicate of {seen_hashes[file_hash].name})"
            )
            src.unlink()
            continue
        seen_hashes[file_hash] = src
        kept.append(src)
    return kept


def ensure_design_assets(
    design_name: str,
    platform: str,
    top: str,
    verilog_dir: Path,
    sdc_template: Path,
    force: bool,
    macro_manifest: Optional[Dict[str, object]],
):
    dest_platform_dir = DEST_BASE / platform / design_name
    dest_src_dir = SRC_BASE / design_name

    if force or not dest_platform_dir.is_dir():
        dest_src_dir.parent.mkdir(parents=True, exist_ok=True)
        if dest_src_dir.is_dir():
            shutil.rmtree(dest_src_dir)
        shutil.copytree(verilog_dir, dest_src_dir)
        if macro_manifest is not None:
            copy_manifest_blackbox_verilog(macro_manifest, dest_src_dir)

        dest_platform_dir.parent.mkdir(parents=True, exist_ok=True)
        if dest_platform_dir.is_dir():
            shutil.rmtree(dest_platform_dir)
        dest_platform_dir.mkdir(parents=True, exist_ok=True)

        deduped_verilog = deduplicate_verilog_sources(dest_src_dir)
        verilog_files = [str(p) for p in deduped_verilog]
        if not verilog_files:
            raise ValueError(f"No .v files found in {verilog_dir}")
        verilog_expr = " ".join(
            f"$(DESIGN_HOME)/src/{design_name}/{Path(v).name}" for v in verilog_files
        )
        config_lines = [
            f"export PLATFORM = {platform}",
            f"export DESIGN_NAME = {top}",
            f"export DESIGN_NICKNAME = {design_name}",
            f"export VERILOG_FILES = {verilog_expr}",
            f"export SDC_FILE = $(DESIGN_HOME)/{platform}/{design_name}/constraint.sdc",
            f"export TOP_MODULE = {top}",
            "export CORE_UTILIZATION = 30",
        ]

        if macro_manifest is not None:
            copied = copy_manifest_assets(macro_manifest, dest_platform_dir, design_name, platform)
            blackboxes = copied.get("blackboxes", [])
            if blackboxes:
                config_lines.append(f"export SYNTH_BLACKBOXES = {' '.join(blackboxes)}")
            if copied.get("additional_lefs"):
                config_lines.append(
                    f"export ADDITIONAL_LEFS = {' '.join(copied['additional_lefs'])}"
                )
            if copied.get("additional_libs"):
                config_lines.append(
                    f"export ADDITIONAL_LIBS = {' '.join(copied['additional_libs'])}"
                )
            if copied.get("additional_gds"):
                config_lines.append(
                    f"export ADDITIONAL_GDS = {' '.join(copied['additional_gds'])}"
                )
            if copied.get("macro_placement_tcl"):
                config_lines.append(
                    f"export MACRO_PLACEMENT_TCL = {copied['macro_placement_tcl']}"
                )

        config_mk = "\n".join(config_lines) + "\n"
        (dest_platform_dir / "config.mk").write_text(config_mk)
        sdc_dst = dest_platform_dir / "constraint.sdc"
        if sdc_template and sdc_template.exists():
            shutil.copy(sdc_template, sdc_dst)
        else:
            write_sdc(10.0, sdc_dst, "clk")

    return dest_platform_dir


def append_metrics(metrics_path: Path, row: Dict[str, object]):
    header = [
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
    ]
    needs_header = not metrics_path.exists()
    with metrics_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if needs_header:
            writer.writeheader()
        writer.writerow({h: row.get(h, "") for h in header})


def _fmt_metric(value: object) -> str:
    num = safe_float(value)
    if num is None:
        return ""
    return f"{num:.4f}"


def _fmt_delta(value: object, baseline: Optional[float]) -> str:
    num = safe_float(value)
    if num is None or baseline is None:
        return ""
    return f"{num - baseline:+.4f}"


def _fmt_count(value: object) -> str:
    num = safe_float(value)
    if num is None:
        return ""
    return str(int(num))


def _collect_numbers(rows: List[Dict[str, object]], key: str) -> List[float]:
    vals: List[float] = []
    for row in rows:
        num = safe_float(row.get(key))
        if num is not None:
            vals.append(num)
    return vals


def _mean_or_none(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return statistics.mean(values)


def _stdev_or_none(values: List[float]) -> Optional[float]:
    if len(values) < 2:
        return 0.0 if values else None
    return statistics.stdev(values)


def _relative_path_text(path_value: object) -> str:
    txt = str(path_value or "").strip()
    if not txt:
        return ""
    p = Path(txt)
    if p.is_absolute():
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return txt
    return txt


def write_mode_compare_report(
    circuit_root: Path,
    report_dir_name: str,
    design_name: str,
    platform: str,
    compare_group: str,
    base_params: Dict[str, object],
    make_target: Optional[str],
    mode_rows: List[Dict[str, object]],
) -> Path:
    report_dir = circuit_root / report_dir_name
    report_dir.mkdir(parents=True, exist_ok=True)
    tag_hint = str(base_params.get("TAG", base_params.get("tag_prefix", "run"))).strip()
    stem = slugify_token(tag_hint, fallback="run")
    report_path = report_dir / f"{stem}_{compare_group}.md"

    make_target_text = make_target or "full_flow"

    baseline_cp = safe_float(mode_rows[0].get("critical_path_ns")) if mode_rows else None
    baseline_area = safe_float(mode_rows[0].get("die_area")) if mode_rows else None
    baseline_power = safe_float(mode_rows[0].get("total_power_mw")) if mode_rows else None
    baseline_flow_time = safe_float(mode_rows[0].get("flow_elapsed_seconds")) if mode_rows else None
    baseline_stage_time = safe_float(mode_rows[0].get("stage_elapsed_seconds")) if mode_rows else None

    mode_groups: Dict[str, List[Dict[str, object]]] = {}
    mode_order: List[str] = []
    for row in mode_rows:
        key = str(row.get("mode_name", "default"))
        if key not in mode_groups:
            mode_groups[key] = []
            mode_order.append(key)
        mode_groups[key].append(row)

    summary_rows: List[Dict[str, object]] = []
    for mode_name in mode_order:
        rows = mode_groups[mode_name]
        cp_vals = _collect_numbers(rows, "critical_path_ns")
        area_vals = _collect_numbers(rows, "die_area")
        power_vals = _collect_numbers(rows, "total_power_mw")
        flow_vals = _collect_numbers(rows, "flow_elapsed_seconds")
        stage_vals = _collect_numbers(rows, "stage_elapsed_seconds")
        ok_count = sum(1 for row in rows if str(row.get("status", "")) == "ok")
        summary_rows.append(
            {
                "mode_name": mode_name,
                "mode_use_macro": rows[0].get("mode_use_macro", False),
                "ok_count": ok_count,
                "total_count": len(rows),
                "cp_mean": _mean_or_none(cp_vals),
                "cp_std": _stdev_or_none(cp_vals),
                "area_mean": _mean_or_none(area_vals),
                "area_std": _stdev_or_none(area_vals),
                "power_mean": _mean_or_none(power_vals),
                "power_std": _stdev_or_none(power_vals),
                "flow_time_mean": _mean_or_none(flow_vals),
                "flow_time_std": _stdev_or_none(flow_vals),
                "stage_time_mean": _mean_or_none(stage_vals),
                "stage_time_std": _stdev_or_none(stage_vals),
            }
        )

    baseline_summary = summary_rows[0] if summary_rows else {}
    baseline_cp_mean = safe_float(baseline_summary.get("cp_mean"))
    baseline_area_mean = safe_float(baseline_summary.get("area_mean"))
    baseline_power_mean = safe_float(baseline_summary.get("power_mean"))
    baseline_flow_mean = safe_float(baseline_summary.get("flow_time_mean"))
    baseline_stage_mean = safe_float(baseline_summary.get("stage_time_mean"))

    lines = [
        f"# Mode Compare: {design_name} ({platform})",
        "",
        f"- compare_group: `{compare_group}`",
        f"- make_target: `{make_target_text}`",
        f"- base_params: `{json.dumps(base_params, sort_keys=True)}`",
        "",
        "## Summary (Mean +/- Stddev)",
        "",
        "| mode | use_macro | ok/total | cp_mean_ns | cp_std_ns | d_cp_mean_ns | die_area_mean_um2 | die_area_std_um2 | d_area_mean_um2 | power_mean_mw | power_std_mw | d_power_mean_mw | flow_time_mean_s | flow_time_std_s | d_flow_time_mean_s | stage_time_mean_s | stage_time_std_s | d_stage_time_mean_s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        lines.append(
            "| {mode} | {use_macro} | {ok_total} | {cp_mean} | {cp_std} | {d_cp_mean} | {area_mean} | {area_std} | {d_area_mean} | {power_mean} | {power_std} | {d_power_mean} | {flow_mean} | {flow_std} | {d_flow_mean} | {stage_mean} | {stage_std} | {d_stage_mean} |".format(
                mode=row.get("mode_name", ""),
                use_macro="yes"
                if parse_bool_token(row.get("mode_use_macro", False), default=False)
                else "no",
                ok_total=f"{row.get('ok_count', 0)}/{row.get('total_count', 0)}",
                cp_mean=_fmt_metric(row.get("cp_mean")),
                cp_std=_fmt_metric(row.get("cp_std")),
                d_cp_mean=_fmt_delta(row.get("cp_mean"), baseline_cp_mean),
                area_mean=_fmt_metric(row.get("area_mean")),
                area_std=_fmt_metric(row.get("area_std")),
                d_area_mean=_fmt_delta(row.get("area_mean"), baseline_area_mean),
                power_mean=_fmt_metric(row.get("power_mean")),
                power_std=_fmt_metric(row.get("power_std")),
                d_power_mean=_fmt_delta(row.get("power_mean"), baseline_power_mean),
                flow_mean=_fmt_metric(row.get("flow_time_mean")),
                flow_std=_fmt_metric(row.get("flow_time_std")),
                d_flow_mean=_fmt_delta(row.get("flow_time_mean"), baseline_flow_mean),
                stage_mean=_fmt_metric(row.get("stage_time_mean")),
                stage_std=_fmt_metric(row.get("stage_time_std")),
                d_stage_mean=_fmt_delta(row.get("stage_time_mean"), baseline_stage_mean),
            )
        )

    lines.extend(
        [
            "",
            "## Per-Run Results",
            "",
            "| mode | repeat | use_macro | status | tag | critical_path_ns | d_cp_ns | die_area_um2 | d_area_um2 | total_power_mw | d_power_mw | flow_time_s | d_flow_time_s | stage_time_s | d_stage_time_s | macro_manifest | missing_blackboxes | result_json |",
            "|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
        ]
    )

    for row in mode_rows:
        missing = row.get("missing_blackboxes", [])
        if isinstance(missing, list):
            missing_txt = ", ".join(str(x) for x in missing)
        else:
            missing_txt = str(missing or "")
        lines.append(
            "| {mode} | {repeat} | {use_macro} | {status} | {tag} | {cp} | {dcp} | {area} | {darea} | {pwr} | {dpwr} | {flow_time} | {d_flow_time} | {stage_time} | {d_stage_time} | {manifest} | {missing} | {result_json} |".format(
                mode=row.get("mode_name", ""),
                repeat=_fmt_count(row.get("repeat_index")),
                use_macro="yes" if parse_bool_token(row.get("mode_use_macro", False), default=False) else "no",
                status=row.get("status", ""),
                tag=row.get("tag", ""),
                cp=_fmt_metric(row.get("critical_path_ns")),
                dcp=_fmt_delta(row.get("critical_path_ns"), baseline_cp),
                area=_fmt_metric(row.get("die_area")),
                darea=_fmt_delta(row.get("die_area"), baseline_area),
                pwr=_fmt_metric(row.get("total_power_mw")),
                dpwr=_fmt_delta(row.get("total_power_mw"), baseline_power),
                flow_time=_fmt_metric(row.get("flow_elapsed_seconds")),
                d_flow_time=_fmt_delta(row.get("flow_elapsed_seconds"), baseline_flow_time),
                stage_time=_fmt_metric(row.get("stage_elapsed_seconds")),
                d_stage_time=_fmt_delta(row.get("stage_elapsed_seconds"), baseline_stage_time),
                manifest=_relative_path_text(row.get("macro_manifest_path", "")),
                missing=missing_txt,
                result_json=_relative_path_text(row.get("work_result_json", "")),
            )
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_single(design_dir: Path, design_name: str, platform: str, top: str, verilog_dir: Path,
               sdc_template: Path, sweep_params: Dict[str, object], out_root: Path,
               skip_existing: bool, dry_run: bool, force_copy: bool,
               make_target: Optional[str], macro_manifest: Optional[Dict[str, object]],
               macro_selection: Optional[Dict[str, object]] = None,
               run_id_extra: Optional[Dict[str, object]] = None,
               mode_name: Optional[str] = None,
               mode_use_macro: Optional[bool] = None,
               compare_group: str = "") -> Optional[Dict[str, object]]:
    config_hash = sha1_verilog_dir(verilog_dir)
    run_id = make_run_id(sweep_params, run_id_extra)
    tag_prefix = sweep_params.get("TAG") or sweep_params.get("tag_prefix") or "run"
    tag = sweep_params.get("TAG", f"{tag_prefix}_{run_id}")

    circuit_root = out_root / design_name
    work_root = circuit_root / "work"
    run_dir = work_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result_path = run_dir / "result.json"
    if skip_existing and result_path.exists():
        print(f"[INFO] Skipping existing run: {run_dir}")
        try:
            return json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "design": design_name,
                "platform": platform,
                "param_hash": run_id,
                "tag": tag,
                "status": "unknown",
                "work_result_json": str(result_path),
            }

    if dry_run:
        print(f"[DRY] {design_name} {platform} tag={tag} params={sweep_params}")
        return {
            "design": design_name,
            "platform": platform,
            "param_hash": run_id,
            "tag": tag,
            "status": "dry_run",
            "critical_path_ns": None,
            "die_area": None,
            "total_power_mw": None,
            "flow_elapsed_seconds": None,
            "stage_elapsed_seconds": None,
            "macro_manifest_path": (
                str(macro_manifest.get("manifest_path", ""))
                if macro_manifest is not None
                else ""
            ),
            "work_result_json": str(result_path),
            "mode_name": mode_name or "",
            "mode_use_macro": bool(mode_use_macro),
            "compare_group": compare_group,
        }

    ensure_design_assets(
        design_name,
        platform,
        top,
        verilog_dir,
        sdc_template,
        force_copy,
        macro_manifest,
    )
    validate_macro_fit_in_core(macro_manifest, sweep_params)

    clock_period = float(sweep_params.get("CLOCK_PERIOD", 10.0))
    clock_port = str(sweep_params.get("CLOCK_PORT", "clk")).strip()
    write_sdc(
        clock_period,
        DEST_BASE / platform / design_name / "constraint.sdc",
        clock_port,
    )
    flow_variant = str(sweep_params.get("FLOW_VARIANT", "base"))

    env = os.environ.copy()
    env.update({k: str(v) for k, v in sweep_params.items()})
    env["TAG"] = tag

    env.setdefault("DISABLE_GUI_SAVE_IMAGES", "1")
    design_config_path = DEST_BASE / platform / design_name / "config.mk"
    sdc_path = DEST_BASE / platform / design_name / "constraint.sdc"
    make_cmd = [
        "make",
        f"DESIGN_CONFIG={design_config_path}",
        f"TAG={tag}",
        f"SDC_FILE={sdc_path}",
    ]
    for k, v in sweep_params.items():
        make_cmd.append(f"{k.upper()}={v}")

    blackboxes = []
    if macro_manifest is not None:
        blackboxes = [str(x).strip() for x in macro_manifest.get("blackboxes", []) if str(x).strip()]
    if blackboxes:
        synth_script_override = run_dir / "synth_preserve_blackbox.tcl"
        write_preserve_blackbox_synth_script(synth_script_override)
        make_cmd.append(f"SYNTH_SCRIPT={synth_script_override.resolve()}")

    # Macro abstract libs can crash Yosys/ABC in synth; run synth once with
    # macro libs disabled, then continue with full libs using cached netlist.
    use_macro_synth_workaround = (
        macro_manifest is not None
        and bool(macro_manifest.get("additional_libs"))
        and not is_synth_target(make_target)
    )
    if use_macro_synth_workaround:
        synth_cmd = list(make_cmd)
        synth_cmd.append("ADDITIONAL_LIBS=")
        synth_cmd.append("synth")
        print(f"[INFO] Running OpenROAD flow: {' '.join(synth_cmd)}")
        subprocess.run(synth_cmd, cwd="/orfs/flow", check=True, env=env)

        synth_netlist = RESULT_BASE / platform / design_name / flow_variant / "1_synth.v"
        if not synth_netlist.exists():
            synth_netlist = RESULT_BASE / platform / design_name / "base" / "1_synth.v"
        if not synth_netlist.exists():
            raise FileNotFoundError(f"Missing synthesized netlist: {synth_netlist}")
        make_cmd.append(f"SYNTH_NETLIST_FILES={synth_netlist}")

    if make_target:
        make_cmd.append(make_target)
    print(f"[INFO] Running OpenROAD flow: {' '.join(make_cmd)}")
    subprocess.run(make_cmd, cwd="/orfs/flow", check=True, env=env)

    blackbox_counts: Dict[str, int] = {}
    missing_blackboxes: List[str] = []
    if macro_manifest is not None:
        if blackboxes:
            synth_netlist = RESULT_BASE / platform / design_name / flow_variant / "1_synth.v"
            if not synth_netlist.exists():
                synth_netlist = RESULT_BASE / platform / design_name / "base" / "1_synth.v"
            if synth_netlist.exists():
                blackbox_counts = count_blackbox_instances_in_netlist(synth_netlist, blackboxes)
                missing_blackboxes = [name for name, count in blackbox_counts.items() if count == 0]
                if missing_blackboxes:
                    print(
                        "[WARN] Requested macro blackboxes missing in synthesized netlist "
                        f"{synth_netlist}: {', '.join(sorted(missing_blackboxes))}"
                    )
            else:
                print(
                    "[WARN] Unable to verify blackbox preservation; synthesized netlist not found: "
                    f"{synth_netlist}"
                )

    stage_prefix_map = {
        "3_3_place_gp": "globalplace",
        "3_4_place_resized": "placeopt",
        "3_5_place_dp": "detailedplace",
        "4_1_cts": "cts",
    }
    use_stage_metrics = bool(make_target and make_target in stage_prefix_map)
    if use_stage_metrics:
        metrics_path = resolve_stage_metrics_path(
            platform,
            design_name,
            tag,
            str(make_target),
            flow_variant,
        )
        metrics = parse_stage_metrics(metrics_path, stage_prefix_map[str(make_target)])
        report_path = metrics_path
    else:
        report_path = REPORT_BASE / platform / design_name / str(tag) / "6_finish.rpt"
        def_path = RESULT_BASE / platform / design_name / str(tag) / "6_final.def"
        variant_report = REPORT_BASE / platform / design_name / flow_variant / "6_finish.rpt"
        variant_def = RESULT_BASE / platform / design_name / flow_variant / "6_final.def"
        if not report_path.exists():
            report_path = variant_report
        if not def_path.exists():
            def_path = variant_def
        if not def_path.exists():
            def_path = RESULT_BASE / platform / design_name / "base" / "6_final.def"
        if not report_path.exists():
            report_path = REPORT_BASE / platform / design_name / "base" / "6_finish.rpt"

        metrics = parse_finish_report(report_path)
        if platform.lower() == "asap7":
            if metrics.get("critical_path_ns") is not None:
                metrics["critical_path_ns"] = metrics["critical_path_ns"] / 1000.0
            if metrics.get("total_power_mw") is not None:
                metrics["total_power_mw"] = metrics["total_power_mw"] / 1000.0
        metrics["die_area"] = parse_die_area(def_path)

    log_dir = resolve_flow_log_dir(platform, design_name, str(tag), flow_variant)
    flow_elapsed_seconds = sum_elapsed_seconds_in_log_dir(log_dir)
    stage_elapsed_seconds = None
    if make_target:
        stage_elapsed_seconds = parse_elapsed_seconds_from_log(log_dir / f"{make_target}.log")
    status = "ok" if metrics.get("critical_path_ns") is not None else "fail"

    payload = {
        "design": design_name,
        "platform": platform,
        "config_hash": config_hash,
        "param_hash": run_id,
        "tag": tag,
        "status": status,
        "critical_path_ns": metrics.get("critical_path_ns"),
        "die_area": metrics.get("die_area"),
        "total_power_mw": metrics.get("total_power_mw"),
        "flow_elapsed_seconds": flow_elapsed_seconds,
        "stage_elapsed_seconds": stage_elapsed_seconds,
        "params_json": json.dumps(sweep_params, sort_keys=True),
        "result_path": str(report_path),
        "blackbox_instance_counts": blackbox_counts,
        "missing_blackboxes": missing_blackboxes,
        "macro_manifest_path": (
            str(macro_manifest.get("manifest_path", ""))
            if macro_manifest is not None
            else ""
        ),
        "macro_selection": macro_selection or {},
        "work_result_json": str(result_path),
        "mode_name": mode_name or "",
        "mode_use_macro": bool(mode_use_macro),
        "compare_group": compare_group,
    }
    result_path.write_text(json.dumps(payload, indent=2))

    metrics_path = circuit_root / "metrics.csv"
    append_metrics(metrics_path, payload)
    return payload


def build_macro_selector_context(
    design_name: str,
    platform: str,
    top: str,
    sweep_params: Dict[str, object],
    cli_selectors: Dict[str, object],
) -> Dict[str, object]:
    context: Dict[str, object] = {
        "design_name": design_name,
        "platform": platform,
        "top_module": top,
    }
    for key, value in sweep_params.items():
        context[str(key)] = value
    for key, value in cli_selectors.items():
        context[str(key)] = value
    return context


def augment_macro_selector_context(context: Dict[str, object]) -> Dict[str, object]:
    out = dict(context)

    mac_type = str(out.get("compute.gemm.mac_type", "")).strip().lower()
    has_cpp_cfg = any(k.startswith("compute.gemm.rtlgen_cpp.") for k in out)

    if "compute.gemm.lanes" not in out and "compute.gemm.lanes_per_module" in out:
        out["compute.gemm.lanes"] = out["compute.gemm.lanes_per_module"]
    if "compute.gemm.lanes_per_module" not in out and "compute.gemm.lanes" in out:
        out["compute.gemm.lanes_per_module"] = out["compute.gemm.lanes"]

    if "compute.gemm.mac_source" not in out:
        if mac_type == "int16":
            out["compute.gemm.mac_source"] = "builtin_int16_dot"
        elif mac_type == "fp16":
            out["compute.gemm.mac_source"] = "rtlgen_cpp" if has_cpp_cfg else "builtin_fp16_dot"
        elif mac_type == "int8":
            out["compute.gemm.mac_source"] = "rtlgen_cpp" if has_cpp_cfg else "builtin_int8_dot"

    if "compute.gemm.num_modules" not in out:
        out["compute.gemm.num_modules"] = 2
    if "compute.gemm.pipeline" not in out:
        out["compute.gemm.pipeline"] = 1

    if "compute.gemm.accum_width" not in out:
        source = str(out.get("compute.gemm.mac_source", "")).strip().lower()
        if source == "rtlgen_cpp" and mac_type in ("int8", "fp16"):
            out["compute.gemm.accum_width"] = 16
        else:
            out["compute.gemm.accum_width"] = 32

    return out


def main():
    ap = argparse.ArgumentParser(description="OpenROAD sweep driver for NPU block macros")
    ap.add_argument("--design_dir", required=True, help="runs/designs/<circuit_type>/<design> path")
    ap.add_argument("--platform", required=True, help="OpenROAD platform name")
    ap.add_argument("--top", required=True, help="Top module name")
    ap.add_argument("--verilog_dir", help="Verilog directory (default: <design_dir>/verilog)")
    ap.add_argument("--sdc", help="Optional SDC template to copy")
    ap.add_argument("--sweep", required=True, help="Sweep JSON")
    ap.add_argument(
        "--macro_manifest",
        help=(
            "Optional JSON manifest for hardened macros. "
            "Supports additional_lefs/additional_libs/blackboxes and macro_placement_tcl."
        ),
    )
    ap.add_argument(
        "--macro_library",
        help=(
            "Optional JSON macro-library file (entries[] with manifest + when match rules). "
            "Selected per sweep point from context keys."
        ),
    )
    ap.add_argument(
        "--macro_select",
        action="append",
        default=[],
        help=(
            "Additional macro-library selector key=value (repeatable). "
            "Overrides same keys from sweep params."
        ),
    )
    ap.add_argument(
        "--macro_select_json",
        help=(
            "Optional JSON file whose flattened keys are added to macro-library "
            "selector context (e.g., compute.gemm.mac_type=fp16)."
        ),
    )
    ap.add_argument(
        "--macro_required",
        action="store_true",
        help="Fail if no macro-library entry matches selector context.",
    )
    ap.add_argument("--out_root", help="Root under runs/designs (default: parent of design_dir)")
    ap.add_argument("--skip_existing", action="store_true", help="Skip existing runs")
    ap.add_argument("--dry_run", action="store_true", help="Print sweep only")
    ap.add_argument("--force_copy", action="store_true", help="Force copy to /orfs/flow")
    ap.add_argument(
        "--repeat",
        type=int,
        help=(
            "Repeat count per sweep point/mode for statistical stability. "
            "Overrides sweep.repeat and mode_compare.repeat."
        ),
    )
    ap.add_argument(
        "--make_target",
        help="Optional make target (e.g., 3_5_place_dp, finish). Default runs full flow.",
    )
    args = ap.parse_args()

    design_dir = Path(args.design_dir)
    if not design_dir.is_dir():
        raise FileNotFoundError(design_dir)
    design_name = design_dir.name
    verilog_dir = Path(args.verilog_dir) if args.verilog_dir else design_dir / "verilog"
    if not verilog_dir.is_dir():
        raise FileNotFoundError(verilog_dir)

    out_root = Path(args.out_root) if args.out_root else design_dir.parent
    if args.macro_manifest and args.macro_library:
        raise ValueError("Use either --macro_manifest or --macro_library, not both.")

    macro_manifest = (
        load_macro_manifest(Path(args.macro_manifest).resolve())
        if args.macro_manifest
        else None
    )
    macro_library = (
        load_macro_library(Path(args.macro_library).resolve())
        if args.macro_library
        else None
    )
    macro_select_from_json: Dict[str, object] = {}
    if args.macro_select_json:
        selector_obj = load_json(Path(args.macro_select_json).resolve())
        if not isinstance(selector_obj, dict):
            raise ValueError("--macro_select_json must contain a JSON object at top level")
        macro_select_from_json = flatten_selector_dict(selector_obj)
    macro_select_overrides = parse_macro_select_args(args.macro_select)
    macro_select_context = dict(macro_select_from_json)
    macro_select_context.update(macro_select_overrides)
    sweep = load_json(Path(args.sweep))
    grid = sweep.get("flow_params", {})
    combos = cartesian_product(grid)
    tag_prefix = str(sweep.get("tag_prefix", "run"))
    mode_compare_cfg = parse_mode_compare_config(sweep)
    if mode_compare_cfg is not None:
        mode_names = [str(x.get("name", "")) for x in mode_compare_cfg.get("modes", [])]
        print(f"[INFO] mode_compare enabled with modes: {', '.join(mode_names)}")
        if macro_manifest is None and macro_library is None:
            for mode in mode_compare_cfg.get("modes", []):
                if mode.get("use_macro"):
                    print(
                        "[WARN] mode_compare has use_macro=true but no --macro_manifest/--macro_library was provided."
                    )
                    break
    repeat_count = 1
    if "repeat" in sweep:
        try:
            repeat_count = int(sweep.get("repeat", 1))
        except Exception as exc:
            raise ValueError(f"sweep.repeat must be an integer: {exc}") from exc
    if mode_compare_cfg is not None:
        try:
            repeat_count = int(mode_compare_cfg.get("repeat", repeat_count))
        except Exception as exc:
            raise ValueError(f"mode_compare.repeat must be an integer: {exc}") from exc
    if args.repeat is not None:
        repeat_count = int(args.repeat)
    if repeat_count < 1:
        raise ValueError("repeat count must be >= 1")
    if repeat_count > 1:
        print(f"[INFO] Repeating each sweep point/mode {repeat_count} times")
    active_manifest_signature: Optional[str] = None
    for base_params in combos:
        params_seed = dict(base_params)
        if tag_prefix and "tag_prefix" not in params_seed:
            params_seed["tag_prefix"] = tag_prefix
        if (
            "DIE_AREA" in params_seed
            and "CORE_AREA" in params_seed
            and "CORE_UTILIZATION" not in params_seed
        ):
            params_seed["CORE_UTILIZATION"] = ""

        compare_group = make_run_id(base_params)
        if mode_compare_cfg is None:
            mode_items = [
                {
                    "name": "",
                    "slug": "",
                    "use_macro": True,
                    "param_overrides": {},
                    "notes": "",
                }
            ]
        else:
            mode_items = [dict(x) for x in mode_compare_cfg.get("modes", [])]

        mode_rows: List[Dict[str, object]] = []
        for mode in mode_items:
            mode_name = str(mode.get("name", "")).strip() or "default"
            mode_slug = str(mode.get("slug", "")).strip() or "default"
            mode_use_macro = bool(mode.get("use_macro", True))
            if mode_compare_cfg is None:
                params = dict(params_seed)
            else:
                params = apply_mode_to_params(params_seed, mode, tag_prefix)

            selected_manifest = macro_manifest if mode_use_macro else None
            macro_selection = None
            if mode_use_macro and macro_library is not None:
                selector_context = build_macro_selector_context(
                    design_name=design_name,
                    platform=args.platform,
                    top=args.top,
                    sweep_params=params,
                    cli_selectors=macro_select_context,
                )
                selector_context = augment_macro_selector_context(selector_context)
                selected_manifest, macro_selection = select_macro_manifest_from_library(
                    macro_library,
                    selector_context,
                    require_match=args.macro_required,
                )
                if macro_selection is not None:
                    macro_selection = dict(macro_selection)
                    macro_selection["selector_context"] = selector_context
                if macro_selection is not None:
                    print(
                        "[INFO] Selected macro library entry "
                        f"{macro_selection.get('entry_name')} -> "
                        f"{macro_selection.get('manifest_path')}"
                    )
                else:
                    print("[INFO] No macro selected from library for this sweep point")
            elif not mode_use_macro and mode_compare_cfg is not None:
                macro_selection = {
                    "mode": "mode_compare_disabled_macro",
                    "mode_name": mode_name,
                }

            manifest_signature = (
                str(selected_manifest.get("manifest_path", ""))
                if selected_manifest is not None
                else ""
            )
            for repeat_index in range(repeat_count):
                repeat_suffix = f"r{repeat_index + 1}"
                params_run = dict(params)
                if repeat_count > 1:
                    if "TAG" in params_run:
                        params_run["TAG"] = f"{params_run['TAG']}_{repeat_suffix}"
                    if "FLOW_VARIANT" in params_run:
                        params_run["FLOW_VARIANT"] = f"{params_run['FLOW_VARIANT']}_{repeat_suffix}"
                    if "TAG" not in params_run and "tag_prefix" in params_run:
                        params_run["tag_prefix"] = f"{params_run['tag_prefix']}_{repeat_suffix}"

                force_copy = args.force_copy or (manifest_signature != active_manifest_signature)
                run_id_extra = None
                if mode_compare_cfg is not None:
                    run_id_extra = {"compare_group": compare_group, "mode": mode_slug}
                    if repeat_count > 1:
                        run_id_extra["repeat"] = repeat_index + 1
                elif repeat_count > 1:
                    run_id_extra = {"repeat": repeat_index + 1}

                row = run_single(
                    design_dir=design_dir,
                    design_name=design_name,
                    platform=args.platform,
                    top=args.top,
                    verilog_dir=verilog_dir,
                    sdc_template=Path(args.sdc) if args.sdc else None,
                    sweep_params=params_run,
                    out_root=out_root,
                    skip_existing=args.skip_existing,
                    dry_run=args.dry_run,
                    force_copy=force_copy,
                    make_target=args.make_target,
                    macro_manifest=selected_manifest,
                    macro_selection=macro_selection,
                    run_id_extra=run_id_extra,
                    mode_name=mode_name,
                    mode_use_macro=mode_use_macro,
                    compare_group=compare_group if mode_compare_cfg is not None else "",
                )
                if row is not None:
                    row = dict(row)
                    row.setdefault("mode_name", mode_name)
                    row.setdefault("mode_use_macro", mode_use_macro)
                    row.setdefault("repeat_index", repeat_index + 1)
                    mode_rows.append(row)
                active_manifest_signature = manifest_signature

        if mode_compare_cfg is not None and mode_rows and not args.dry_run:
            report_path = write_mode_compare_report(
                circuit_root=out_root / design_name,
                report_dir_name=str(mode_compare_cfg.get("report_dir", "comparisons")),
                design_name=design_name,
                platform=args.platform,
                compare_group=compare_group,
                base_params=base_params,
                make_target=args.make_target,
                mode_rows=mode_rows,
            )
            print(f"[INFO] Wrote mode comparison report: {report_path}")


if __name__ == "__main__":
    sys.exit(main())
