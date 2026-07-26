#!/usr/bin/env python3
"""Audit strict post-route activity power for the score32 dual-stream schedule wrapper."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from npu.eval.extract_sequential_register_vcd_activity import extract_sequential_register_vcd_activity
from npu.eval.generate_attention_dual_stream_schedule_wrapper_activity import (
    _DEFAULT_CLOCK_PERIOD_NS,
    _DEFAULT_SERVICE_WINDOW_CYCLES,
    _OUTPUT_MANIFEST_NAME,
    _OUTPUT_TOP_NAME,
    _OUTPUT_VCD_NAME,
    _OUTPUT_WRAPPER_MANIFEST_NAME,
    generate_activity,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_schedule_wrapper_postroute_activity_power_v1"
_POSTROUTE_MANIFEST_NAME = "attention_dual_stream_schedule_wrapper_postroute_power_manifest.json"
_POSTROUTE_SEQUENTIAL_ACTIVITY_NAME = (
    "attention_dual_stream_schedule_wrapper_sequential_register_vcd_activity_v1.json"
)
_EXPECTED_PLATFORM = "nangate45"
_EXPECTED_FLOW_VARIANT = "attention_dual_stream_schedule_wrapper_score32_exp_lut"
_EXPECTED_CRITICAL_PATH_NS = 48.6509
_EXPECTED_INSTANCE_AREA_UM2 = 693452.0
_EXPECTED_TOTAL_POWER_MW = 60.7
_EXPECTED_PLACE_DENSITY = 0.4
_EXPECTED_REPLICA_COUNT = 428
_EXPECTED_TILE_WAVES = 8
_EXPECTED_LAYERS = 32
_EXPECTED_QKV_CYCLES = 192
_EXPECTED_REDUCTION_CYCLES = 141
_EXPECTED_KV_WRITE_CYCLES = 10
_EXPECTED_LAYER_CYCLES = 8231
_SCOPE = "tb/dut"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path(__file__).resolve().parents[2].resolve()).as_posix()
    except ValueError:
        return path.name


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _require_positive(value: Any, label: str) -> float:
    numeric = _as_float(value, float("nan"))
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{label} must be a finite positive number")
    return numeric


def _select_authoritative_metric(metrics_csv: Path, *, design_name: str) -> JsonDict:
    matches: list[JsonDict] = []
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("status", "")).strip() != "ok":
                continue
            if str(row.get("design", "")).strip() != design_name:
                continue
            if str(row.get("platform", "")).strip() != _EXPECTED_PLATFORM:
                continue
            params = json.loads(str(row.get("params_json") or "{}"))
            if str(params.get("FLOW_VARIANT") or "").strip() != _EXPECTED_FLOW_VARIANT:
                continue
            if abs(_as_float(params.get("CLOCK_PERIOD")) - _DEFAULT_CLOCK_PERIOD_NS) > 1e-9:
                continue
            if abs(_as_float(params.get("PLACE_DENSITY")) - _EXPECTED_PLACE_DENSITY) > 1e-9:
                continue
            matches.append({"row": dict(row), "params": params})
    if len(matches) != 1:
        raise ValueError(
            "expected exactly one authoritative density-0.4 routed row for the score32 wrapper, "
            f"found {len(matches)}"
        )
    row = matches[0]["row"]
    critical_path_ns = _as_float(row.get("critical_path_ns"))
    instance_area_um2 = _as_float(row.get("instance_area_um2"))
    total_power_mw = _as_float(row.get("total_power_mw"))
    if abs(critical_path_ns - _EXPECTED_CRITICAL_PATH_NS) > 1e-9:
        raise ValueError("authoritative wrapper critical_path_ns mismatch")
    if abs(instance_area_um2 - _EXPECTED_INSTANCE_AREA_UM2) > 1e-9:
        raise ValueError("authoritative wrapper instance_area_um2 mismatch")
    if abs(total_power_mw - _EXPECTED_TOTAL_POWER_MW) > 1e-9:
        raise ValueError("authoritative wrapper total_power_mw mismatch")
    return matches[0]


def _validate_recost_contract(payload: JsonDict, *, design_name: str) -> JsonDict:
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict) or str(diagnosis.get("decision") or "") != "dual_stream_feasible":
        raise ValueError("recost decision must be dual_stream_feasible")
    row = payload.get("best_requested")
    if not isinstance(row, dict):
        raise ValueError("recost payload missing best_requested row")
    checks = {
        "substituted_compute_arch": design_name,
        "substituted_compute_variant_kind": "dual_stream_schedule_wrapper",
        "substituted_compute_semantic_profile": "score32_exp_lut_div",
        "replica_recost_area_fit_replica_count": _EXPECTED_REPLICA_COUNT,
        "replica_recost_tile_service_cycles": _DEFAULT_SERVICE_WINDOW_CYCLES,
        "tile_service_cycles": _DEFAULT_SERVICE_WINDOW_CYCLES,
        "tile_waves": _EXPECTED_TILE_WAVES,
        "layers": _EXPECTED_LAYERS,
        "replica_recost_qkv_cycles": _EXPECTED_QKV_CYCLES,
        "cross_tile_reduction_cycles": _EXPECTED_REDUCTION_CYCLES,
        "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
        "replica_recost_layer_cycles": _EXPECTED_LAYER_CYCLES,
    }
    for key, expected in checks.items():
        actual = row.get(key)
        if actual != expected:
            raise ValueError(f"recost contract mismatch for {key}: expected {expected!r}, got {actual!r}")
    residual_cycles = _as_int(row.get("replica_recost_layer_cycles")) - (
        _EXPECTED_TILE_WAVES * _DEFAULT_SERVICE_WINDOW_CYCLES
    )
    if residual_cycles != (_EXPECTED_QKV_CYCLES + _EXPECTED_REDUCTION_CYCLES + _EXPECTED_KV_WRITE_CYCLES):
        raise ValueError("recost residual cycle contract mismatch")
    return {
        "replica_count": _EXPECTED_REPLICA_COUNT,
        "tile_waves": _EXPECTED_TILE_WAVES,
        "layers": _EXPECTED_LAYERS,
        "service_window_cycles": _DEFAULT_SERVICE_WINDOW_CYCLES,
        "cluster_service_cycles_from_config_must_remain_distinct": True,
        "residual_layer_cycles": residual_cycles,
        "residual_breakdown": {
            "qkv_cycles": _EXPECTED_QKV_CYCLES,
            "cross_tile_reduction_cycles": _EXPECTED_REDUCTION_CYCLES,
            "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
        },
        "latency_us": _as_float(row.get("replica_recost_latency_us")),
        "logic_area_um2": _as_float(row.get("replica_recost_compute_area_um2")),
    }


def _prepare_postroute_manifest(*, activity_dir: Path, activity_manifest: JsonDict) -> tuple[JsonDict, Path]:
    vcd_path = activity_dir / _OUTPUT_VCD_NAME
    if not vcd_path.is_file():
        raise ValueError("generated wrapper activity VCD is missing")
    vcd_sha256 = str(activity_manifest.get("hashes", {}).get("vcd_sha256") or "").strip().lower()
    if not vcd_sha256 or _sha256_file(vcd_path) != vcd_sha256:
        raise ValueError("generated wrapper VCD hash does not match the activity manifest")
    sequential_activity = extract_sequential_register_vcd_activity(
        vcd_path,
        source_vcd_sha256=vcd_sha256,
        scope=_SCOPE,
    )
    sequential_activity_path = activity_dir / _POSTROUTE_SEQUENTIAL_ACTIVITY_NAME
    sequential_activity_path.write_text(
        json.dumps(sequential_activity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    postroute_manifest = {
        "version": 1,
        "model": "attention_dual_stream_schedule_wrapper_postroute_activity_manifest_v1",
        "clock_period_ns": _DEFAULT_CLOCK_PERIOD_NS,
        "phases": [
            {
                "phase": "service_window",
                "vcd": _OUTPUT_VCD_NAME,
                "vcd_sha256": vcd_sha256,
                "sequential_register_activity": sequential_activity_path.name,
                "sequential_register_activity_sha256": _sha256_file(sequential_activity_path),
                "measured_cycles": _DEFAULT_SERVICE_WINDOW_CYCLES,
                "full_context_cycles": _DEFAULT_SERVICE_WINDOW_CYCLES,
                "requires_macro_activity": False,
            }
        ],
    }
    manifest_path = activity_dir / _POSTROUTE_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(postroute_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return postroute_manifest, manifest_path


def _strict_service_window_measurement(
    *,
    activity_power: JsonDict,
    manifest_sha256: str,
    expected_vcd_sha256: str,
    expected_cycle_count: int,
    authoritative_critical_path_ns: float,
) -> JsonDict:
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("postroute power promotion_gate_pass failed")
    if activity_power.get("status") != "activity_backed":
        raise ValueError("postroute power status is not activity_backed")
    if str(activity_power.get("source_activity_manifest_sha256") or "").strip().lower() != manifest_sha256:
        raise ValueError("postroute power source_activity_manifest_sha256 mismatch")
    phases = activity_power.get("phases")
    if not isinstance(phases, list) or len(phases) != 1 or not isinstance(phases[0], dict):
        raise ValueError("postroute power must contain exactly one service_window phase")
    phase = phases[0]
    if str(phase.get("phase") or "").strip() != "service_window":
        raise ValueError("postroute power phase mismatch")
    if str(phase.get("vcd_sha256") or "").strip().lower() != expected_vcd_sha256:
        raise ValueError("postroute power VCD hash mismatch")
    if int(phase.get("measured_cycles", 0)) != expected_cycle_count:
        raise ValueError("postroute power measured_cycles mismatch")
    if int(phase.get("full_context_cycles", 0)) != expected_cycle_count:
        raise ValueError("postroute power full_context_cycles mismatch")
    if int(phase.get("macro_activity_assignment_count", 0)) != 0:
        raise ValueError("wrapper postroute phase must remain macro-less")
    for gate_key in (
        "annotation_gate_pass",
        "sequential_register_activity_gate_pass",
        "clock_period_gate_pass",
        "power_numeric_gate_pass",
        "structural_macro_activity_gate_pass",
        "phase_gate_pass",
    ):
        if phase.get(gate_key) is not True:
            raise ValueError(f"postroute power gate failed: {gate_key}")
    power = phase.get("power")
    if not isinstance(power, dict):
        raise ValueError("postroute power phase missing power section")
    internal_w = _require_positive(power.get("internal_w"), "internal_w")
    switching_w = _require_positive(power.get("switching_w"), "switching_w")
    leakage_w = _require_positive(power.get("leakage_w"), "leakage_w")
    total_w = _require_positive(power.get("total_w"), "total_w")
    if abs((internal_w + switching_w + leakage_w) - total_w) > 1e-9:
        raise ValueError("postroute power total_w does not match internal+switching+leakage")
    annotation_clock_ns = _DEFAULT_CLOCK_PERIOD_NS
    promotion_clock_ns = max(annotation_clock_ns, authoritative_critical_path_ns)
    dynamic_energy_j = (internal_w + switching_w) * expected_cycle_count * annotation_clock_ns * 1e-9
    leakage_energy_j = leakage_w * expected_cycle_count * promotion_clock_ns * 1e-9
    return {
        "label": "wrapper_service_window_energy",
        "cycle_count": expected_cycle_count,
        "annotation_clock_ns": annotation_clock_ns,
        "promotion_clock_ns": promotion_clock_ns,
        "annotation_duration_s": expected_cycle_count * annotation_clock_ns * 1e-9,
        "promotion_duration_s": expected_cycle_count * promotion_clock_ns * 1e-9,
        "power_w": {
            "internal": internal_w,
            "switching": switching_w,
            "dynamic": internal_w + switching_w,
            "leakage": leakage_w,
            "total": total_w,
        },
        "energy_j": {
            "dynamic": dynamic_energy_j,
            "leakage": leakage_energy_j,
            "dynamic_plus_leakage": dynamic_energy_j + leakage_energy_j,
        },
    }


def build_report(
    *,
    config: Path,
    metrics_csv: Path,
    recost_json: Path,
    orfs_design_config: Path,
    activity_dir: Path,
) -> JsonDict:
    config_payload = _load(config)
    design_name = str(config_payload.get("top_name") or "").strip()
    if not design_name:
        raise ValueError("config requires non-empty top_name")
    wrapper = config_payload.get("attention_dual_stream_schedule_wrapper")
    if not isinstance(wrapper, dict):
        raise ValueError("config requires attention_dual_stream_schedule_wrapper object")
    cluster_service_cycles = _as_int(wrapper.get("cluster_service_cycles"))
    if cluster_service_cycles <= 0:
        raise ValueError("config cluster_service_cycles must be positive")
    if cluster_service_cycles == _DEFAULT_SERVICE_WINDOW_CYCLES:
        raise ValueError("cluster_service_cycles must remain distinct from the 986-cycle wrapper service window")
    if cluster_service_cycles == 4:
        pass
    authoritative_metric = _select_authoritative_metric(metrics_csv, design_name=design_name)
    recost_contract = _validate_recost_contract(_load(recost_json), design_name=design_name)
    if cluster_service_cycles != 4:
        raise ValueError("expected the authoritative wrapper config to retain cluster_service_cycles=4")
    activity_dir.mkdir(parents=True, exist_ok=True)
    activity_manifest = generate_activity(
        config_payload,
        activity_dir,
        clock_period_ns=_DEFAULT_CLOCK_PERIOD_NS,
        service_window_cycles=_DEFAULT_SERVICE_WINDOW_CYCLES,
    )
    if _as_int(activity_manifest.get("service_window_cycles")) != _DEFAULT_SERVICE_WINDOW_CYCLES:
        raise ValueError("generated activity manifest service_window_cycles mismatch")
    if _as_int(activity_manifest.get("cycle_count")) != _DEFAULT_SERVICE_WINDOW_CYCLES:
        raise ValueError("generated activity manifest cycle_count mismatch")
    if _as_int(activity_manifest.get("cluster_service_cycles")) == _DEFAULT_SERVICE_WINDOW_CYCLES:
        raise ValueError("activity manifest incorrectly collapsed the 986-cycle service window to cluster_service_cycles")
    gates = activity_manifest.get("gates")
    if not isinstance(gates, dict) or not all(
        bool(gates.get(key))
        for key in (
            "equivalence_pass",
            "protocol_gate_ok",
            "count_gate_ok",
            "hash_gate_ok",
            "observable_completion_gate_ok",
            "window_active_gate_ok",
            "both_clusters_issue_gate_ok",
            "service_window_gate_ok",
        )
    ):
        raise ValueError("generated activity manifest gates failed")
    counters = activity_manifest.get("request_result_protocol_counters")
    if not isinstance(counters, dict):
        raise ValueError("generated activity manifest is missing request_result_protocol_counters")
    if _as_int(counters.get("window_active_cycles")) != _DEFAULT_SERVICE_WINDOW_CYCLES:
        raise ValueError("generated activity window_active_cycles must equal the 986-cycle service window")
    window_issue_counts = counters.get("window_issue_counts")
    if not isinstance(window_issue_counts, dict):
        raise ValueError("generated activity manifest is missing window_issue_counts")
    if _as_int(window_issue_counts.get("0")) <= 0 or _as_int(window_issue_counts.get("1")) <= 0:
        raise ValueError("generated activity manifest did not sustain both clusters inside the measured window")
    postroute_manifest, postroute_manifest_path = _prepare_postroute_manifest(
        activity_dir=activity_dir,
        activity_manifest=activity_manifest,
    )
    activity_power = build_power_report(
        manifest=postroute_manifest,
        manifest_path=postroute_manifest_path,
        design_config=orfs_design_config,
        flow_variant=_EXPECTED_FLOW_VARIANT,
        scope=_SCOPE,
        min_vcd_coverage=0.02,
        min_vcd_pins=8,
        min_sequential_register_activity_coverage=0.95,
        min_macro_active_coverage=0.0,
        min_macro_active_pins=0,
        timeout_seconds=1800,
    )
    authoritative_row = authoritative_metric["row"]
    service_window_energy = _strict_service_window_measurement(
        activity_power=activity_power,
        manifest_sha256=_sha256_file(postroute_manifest_path),
        expected_vcd_sha256=str(activity_manifest["hashes"]["vcd_sha256"]),
        expected_cycle_count=_DEFAULT_SERVICE_WINDOW_CYCLES,
        authoritative_critical_path_ns=_as_float(authoritative_row["critical_path_ns"]),
    )
    total_compute_energy_j = (
        service_window_energy["energy_j"]["dynamic_plus_leakage"]
        * _EXPECTED_REPLICA_COUNT
        * _EXPECTED_TILE_WAVES
        * _EXPECTED_LAYERS
    )
    return {
        "version": 1,
        "model": _MODEL,
        "decision": "score32_schedule_wrapper_postroute_activity_power_recorded",
        "promotion_gate_pass": True,
        "inputs": {
            "config": _portable_path(config),
            "metrics_csv": _portable_path(metrics_csv),
            "recost_json": _portable_path(recost_json),
            "orfs_design_config": _portable_path(orfs_design_config),
            "activity_dir": _portable_path(activity_dir),
        },
        "selection_contract": {
            "design": design_name,
            "platform": _EXPECTED_PLATFORM,
            "flow_variant": _EXPECTED_FLOW_VARIANT,
            "clock_period_ns": _DEFAULT_CLOCK_PERIOD_NS,
            "place_density": _EXPECTED_PLACE_DENSITY,
            "authoritative_metrics": {
                "critical_path_ns": _as_float(authoritative_row["critical_path_ns"]),
                "instance_area_um2": _as_float(authoritative_row["instance_area_um2"]),
                "total_power_mw": _as_float(authoritative_row["total_power_mw"]),
                "param_hash": authoritative_row["param_hash"],
            },
        },
        "recost_contract": recost_contract,
        "activity_manifest": {
            "model": activity_manifest["model"],
            "cycle_count": activity_manifest["cycle_count"],
            "service_window_cycles": activity_manifest["service_window_cycles"],
            "cluster_service_cycles": activity_manifest["cluster_service_cycles"],
            "hashes": activity_manifest["hashes"],
            "gates": activity_manifest["gates"],
            "request_result_protocol_counters": activity_manifest["request_result_protocol_counters"],
        },
        "postroute_power": activity_power,
        "best": {
            "candidate_id": "score32_schedule_wrapper_postroute_activity_power",
            "status": "activity_backed",
            "authoritative_wrapper_total_ppa": {
                "critical_path_ns": _as_float(authoritative_row["critical_path_ns"]),
                "instance_area_um2": _as_float(authoritative_row["instance_area_um2"]),
                "total_power_mw": _as_float(authoritative_row["total_power_mw"]),
            },
            "component_service_window_energy": service_window_energy,
            "replica_scaled_wrapper_compute_energy_j_per_token": total_compute_energy_j,
        },
        "next_step": {
            "recommended_next_step": (
                "Use the measured 986-cycle wrapper service-window energy, the routed 48.6509 ns promotion clock, "
                "and the unchanged HBM energy closure in the score32 integrated frontier rerank."
            ),
            "residual_layer_cycles_not_measured_in_wrapper_activity": recost_contract["residual_layer_cycles"],
            "residual_breakdown": recost_contract["residual_breakdown"],
        },
        "assumptions": [
            "VCD annotation and SDC matching remain bound to the 10 ns routed-flow contract.",
            "Wrapper dynamic energy uses the annotated 10 ns service-window cycle energy.",
            "Wrapper leakage energy uses the promotion/rerank clock max(10 ns, 48.6509 ns).",
            "The 343 residual per-layer cycles are retained outside the wrapper activity term: qkv=192, reduction=141, kv_write=10.",
            "Raw VCD, ODB, SPEF, and temporary activity files remain evaluator-local and are not portable artifacts.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    energy = best["component_service_window_energy"]
    lines = [
        "# Score32 Wrapper Postroute Activity Power",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promotion_gate_pass: `{payload['promotion_gate_pass']}`",
        f"- authoritative path ns: `{best['authoritative_wrapper_total_ppa']['critical_path_ns']}`",
        f"- annotation clock ns: `{energy['annotation_clock_ns']}`",
        f"- promotion clock ns: `{energy['promotion_clock_ns']}`",
        f"- service-window dynamic J: `{energy['energy_j']['dynamic']}`",
        f"- service-window leakage J: `{energy['energy_j']['leakage']}`",
        f"- service-window total J: `{energy['energy_j']['dynamic_plus_leakage']}`",
        f"- replica-scaled wrapper compute J/token: `{best['replica_scaled_wrapper_compute_energy_j_per_token']}`",
        "",
        "## Residual Cycles",
        "",
        f"- qkv: `{payload['recost_contract']['residual_breakdown']['qkv_cycles']}`",
        f"- reduction: `{payload['recost_contract']['residual_breakdown']['cross_tile_reduction_cycles']}`",
        f"- kv_write: `{payload['recost_contract']['residual_breakdown']['kv_write_cycles']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--metrics-csv", type=Path, required=True)
    parser.add_argument("--recost-json", type=Path, required=True)
    parser.add_argument("--orfs-design-config", type=Path, required=True)
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        config=args.config,
        metrics_csv=args.metrics_csv,
        recost_json=args.recost_json,
        orfs_design_config=args.orfs_design_config,
        activity_dir=args.activity_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
