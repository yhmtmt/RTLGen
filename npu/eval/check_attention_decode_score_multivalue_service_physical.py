#!/usr/bin/env python3
"""Validate the physical sweep contract for the composed multivalue service."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


_EXPECTED_FLOW_VARIANT_PREFIX = "decode_score_multivalue_service"
_EXPECTED_CLOCK_PERIOD = 10.0
_EXPECTED_PLACE_DENSITY = 0.4
_EXPECTED_SYNTH_HIERARCHICAL = 1
_EXPECTED_SYNTH_MEMORY_MAX_BITS = 65536
_EXPECTED_RESULT_TOKEN = "attention_decode_score_multivalue_service"
_EXPECTED_AREAS = {
    1: {"die_side_um": 3000, "core_side_um": 2950, "modes": ("macro_conservative_c1_die_3000",)},
    2: {
        "die_side_um": 3700,
        "core_side_um": 3650,
        "modes": ("flattened_wrapper", "hierarchical_macro"),
    },
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_mapping(payload: dict[str, object], *keys: str) -> dict[str, object]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _parse_params_json(value: str) -> dict[str, object]:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty params_json")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            parsed = json.loads(text[1:-1].replace('""', '"'))
        else:
            raise
    if not isinstance(parsed, dict):
        raise ValueError("params_json did not decode to a JSON object")
    return parsed


def _to_str(value: object) -> str:
    return str(value or "").strip()


def _to_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _parse_area(value: str) -> tuple[float, float]:
    parts = _to_str(value).split()
    if len(parts) != 4:
        raise ValueError(f"invalid area box: {value}")
    x0, y0, x1, y1 = [float(part) for part in parts]
    return max(0.0, x1 - x0), max(0.0, y1 - y0)


def _variant_candidates(base_flow_variant: str, mode_name: str) -> set[str]:
    return {base_flow_variant, f"{base_flow_variant}_{mode_name}"}


def _read_metrics_rows(metrics_path: Path) -> list[dict[str, str]]:
    with metrics_path.open(newline="", encoding="utf-8") as stream:
        return [row for row in csv.DictReader(stream) if row]


def _resolve_repo_path(path_text: str) -> Path:
    return Path(path_text).resolve() if Path(path_text).is_absolute() else (Path.cwd() / path_text).resolve()


def _matching_row(
    rows: list[dict[str, str]],
    *,
    flow_variants: set[str],
    die_side_um: int,
    core_side_um: int,
) -> dict[str, str] | None:
    expected_die = f"0 0 {die_side_um} {die_side_um}"
    expected_core = f"50 50 {core_side_um} {core_side_um}"
    for row in rows:
        if _to_str(row.get("status")).lower() != "ok":
            continue
        if _EXPECTED_RESULT_TOKEN not in _to_str(row.get("result_path", "")):
            continue
        try:
            params = _parse_params_json(_to_str(row.get("params_json", "")))
        except Exception:
            continue
        if _to_str(params.get("FLOW_VARIANT")) not in flow_variants:
            continue
        try:
            if float(_to_str(params.get("CLOCK_PERIOD", ""))) != _EXPECTED_CLOCK_PERIOD:
                continue
            if float(_to_str(row.get("critical_path_ns", "inf"))) > _EXPECTED_CLOCK_PERIOD:
                continue
        except ValueError:
            continue
        if _to_str(params.get("DIE_AREA")) != expected_die:
            continue
        if _to_str(params.get("CORE_AREA")) != expected_core:
            continue
        return row
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument("--sweep", type=Path, required=True)
    args = parser.parse_args()

    design_dir = args.design_dir.resolve()
    metrics_path = args.metrics_path.resolve()
    sweep_path = args.sweep.resolve()
    if not metrics_path.exists():
        raise SystemExit(f"missing metrics.csv: {metrics_path}")
    if not sweep_path.exists():
        raise SystemExit(f"missing sweep json: {sweep_path}")

    config = _load_json(design_dir / "config.json")
    macro_manifest = _load_json(design_dir / "macro_manifest.json")
    body = config.get("attention_decode_score_multivalue_service")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_decode_score_multivalue_service object")
    cluster_count = int(body.get("cluster_count", 0))
    if cluster_count not in _EXPECTED_AREAS:
        raise SystemExit(f"unsupported cluster_count for first-patch physical service sweep: {cluster_count}")

    sweep = _load_json(sweep_path)
    flow_params = _first_mapping(sweep, "flow_params", "parameters")
    base_flow_variant = _to_str(
        (flow_params.get("FLOW_VARIANT") or [""])[0]
        if isinstance(flow_params.get("FLOW_VARIANT"), list)
        else flow_params.get("FLOW_VARIANT")
    )
    if not base_flow_variant.startswith(_EXPECTED_FLOW_VARIANT_PREFIX):
        raise SystemExit("service sweep FLOW_VARIANT must identify the composed service flow")
    clock_values = flow_params.get("CLOCK_PERIOD")
    if clock_values != [10] and clock_values != [_EXPECTED_CLOCK_PERIOD]:
        raise SystemExit("service sweep CLOCK_PERIOD must be exactly [10]")
    if flow_params.get("PLACE_DENSITY") != [_EXPECTED_PLACE_DENSITY]:
        raise SystemExit("service sweep PLACE_DENSITY must be exactly [0.4]")
    if flow_params.get("SYNTH_HIERARCHICAL") != [_EXPECTED_SYNTH_HIERARCHICAL]:
        raise SystemExit("service sweep SYNTH_HIERARCHICAL must be exactly [1]")
    if flow_params.get("SYNTH_MEMORY_MAX_BITS") != [_EXPECTED_SYNTH_MEMORY_MAX_BITS]:
        raise SystemExit("service sweep SYNTH_MEMORY_MAX_BITS must be exactly [65536]")

    expected = _EXPECTED_AREAS[cluster_count]
    mode_compare = sweep.get("mode_compare")
    expected_modes = list(expected["modes"])
    if cluster_count == 2:
        if not isinstance(mode_compare, dict):
            raise SystemExit("c2 service sweep must use mode_compare for flattened/hierarchical comparison")
        modes = mode_compare.get("modes")
        if not isinstance(modes, list) or [mode.get("name") for mode in modes] != expected_modes:
            raise SystemExit("c2 service sweep must contain flattened_wrapper and hierarchical_macro modes in order")
        for mode in modes:
            if mode.get("use_macro") is not True:
                raise SystemExit("c2 service sweep modes must preserve macro usage")
            overrides = mode.get("param_overrides")
            if not isinstance(overrides, dict):
                raise SystemExit("c2 service sweep modes must define param_overrides")
            expected_die = f"0 0 {expected['die_side_um']} {expected['die_side_um']}"
            expected_core = f"50 50 {expected['core_side_um']} {expected['core_side_um']}"
            if _to_str(overrides.get("DIE_AREA")) != expected_die:
                raise SystemExit("c2 service sweep DIE_AREA must be 0 0 3700 3700")
            if _to_str(overrides.get("CORE_AREA")) != expected_core:
                raise SystemExit("c2 service sweep CORE_AREA must be 50 50 3650 3650")
        if _to_int(modes[0].get("param_overrides", {}).get("SYNTH_HIERARCHICAL")) != 0:
            raise SystemExit("flattened_wrapper mode must override SYNTH_HIERARCHICAL=0")
        if _to_int(modes[1].get("param_overrides", {}).get("SYNTH_HIERARCHICAL")) != 1:
            raise SystemExit("hierarchical_macro mode must override SYNTH_HIERARCHICAL=1")
    else:
        if not isinstance(mode_compare, dict):
            raise SystemExit("service sweep must use mode_compare with a single explicit macro mode")
        modes = mode_compare.get("modes")
        if not isinstance(modes, list) or len(modes) != 1 or modes[0].get("name") != expected_modes[0]:
            raise SystemExit("service sweep single-mode contract does not match expected die policy")
        if modes[0].get("use_macro") is not True:
            raise SystemExit("service sweep must preserve macro usage")
        overrides = modes[0].get("param_overrides")
        if not isinstance(overrides, dict):
            raise SystemExit("service sweep mode must define param_overrides")
        expected_die = f"0 0 {expected['die_side_um']} {expected['die_side_um']}"
        expected_core = f"50 50 {expected['core_side_um']} {expected['core_side_um']}"
        if _to_str(overrides.get("DIE_AREA")) != expected_die:
            raise SystemExit(f"service sweep DIE_AREA must be {expected_die}")
        if _to_str(overrides.get("CORE_AREA")) != expected_core:
            raise SystemExit(f"service sweep CORE_AREA must be {expected_core}")

    min_core_side_um = int(macro_manifest.get("manifest_params", {}).get("minimum_core_side_um", 0))
    min_die_side_um = int(macro_manifest.get("manifest_params", {}).get("minimum_die_side_um", 0))
    if int(expected["core_side_um"]) < min_core_side_um:
        raise SystemExit("service sweep core side violates macro-manifest minimum_core_side_um")
    if int(expected["die_side_um"]) < min_die_side_um:
        raise SystemExit("service sweep die side violates macro-manifest minimum_die_side_um")

    rows = _read_metrics_rows(metrics_path)
    matched_rows: list[dict[str, str]] = []
    for mode_name in expected_modes:
        row = _matching_row(
            rows,
            flow_variants=_variant_candidates(base_flow_variant, mode_name),
            die_side_um=int(expected["die_side_um"]),
            core_side_um=int(expected["core_side_um"]),
        )
        if row is not None:
            matched_rows.append(row)

    if cluster_count == 2 and len(matched_rows) == 0:
        raise SystemExit(
            "stop_monolithic_path: both c2 hierarchy modes failed to produce a 10ns status=ok row "
            "at DIE_AREA=0 0 3700 3700 / CORE_AREA=50 50 3650 3650"
        )
    if cluster_count != 2 and len(matched_rows) != len(expected_modes):
        raise SystemExit(
            "missing required 10ns composed-service row for the configured die/core envelope"
        )

    expected_macro_manifest_path = (design_dir / "macro_manifest.json").resolve()
    for row in matched_rows:
        work_result_json = _to_str(row.get("work_result_json", ""))
        if not work_result_json:
            raise SystemExit("matched service metrics row must record work_result_json")
        result_payload = _load_json(_resolve_repo_path(work_result_json))
        macro_manifest_path = _to_str(result_payload.get("macro_manifest_path", ""))
        if not macro_manifest_path:
            raise SystemExit("matched service result.json must record macro_manifest_path")
        if _resolve_repo_path(macro_manifest_path) != expected_macro_manifest_path:
            raise SystemExit("matched service result.json macro_manifest_path does not match design macro_manifest.json")

    print(
        json.dumps(
            {
                "design": str(config.get("top_name") or ""),
                "checker": "attention_decode_score_multivalue_service_physical_v1",
                "cluster_count": cluster_count,
                "matched_rows": len(matched_rows),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
