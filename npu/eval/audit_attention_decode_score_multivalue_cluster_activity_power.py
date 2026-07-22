#!/usr/bin/env python3
"""Measure activity-backed power across feasible multivalue-cluster PPA rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

from npu.eval.generate_attention_decode_score_multivalue_cluster_activity import (
    generate_phase_activity,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report


JsonDict = dict[str, Any]
_MAX_FAILURE_DETAIL_LINES = 16
_MAX_FAILURE_DETAIL_LINE_CHARS = 400
_MAX_FAILURE_DETAIL_BYTES = 4096
_ABSOLUTE_PATH_RE = re.compile(r"/[^\s\"'`<>|&(){}\[\]]+")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVALUATOR_LOCAL_PATH_PLACEHOLDER = "<evaluator-local-path>"
_TARGETED_BINARY_FSM_PROFILE = "targeted_binary"
_TARGETED_BINARY_FSM_CHECKER = "attention_decode_score_multivalue_cluster_targeted_binary_fsm_v1"
_TARGETED_BINARY_FSM_FLOW_VARIANT = (
    "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
)
_TARGETED_BINARY_FSM_CONFIG = (
    "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
    "config_targeted_binary_fsm.json"
)
_TARGETED_BINARY_FSM_PNR_ITEM = (
    "l1_decoder_attention_decode_score_multivalue_cluster_pnr_targeted_binary_fsm_8ns_v1"
)
_TARGETED_BINARY_FSM_DESIGN = "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
_TARGETED_BINARY_FSM_PLATFORM = "nangate45"
_TARGETED_BINARY_FSM_TAG_PREFIX = "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm"
_TARGETED_BINARY_FSM_NETLIST = (
    "results/nangate45/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
    "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500/1_synth.v"
)
_TARGETED_BINARY_FSM_SIGNAL_INDICES = {
    "state_q": [0, 1, 2],
    "reducer.state": [0, 1, 2, 3],
}
_POWER_COMPONENTS = ("internal_w", "switching_w", "leakage_w", "total_w")


def _redact_path(path: str) -> str:
    normalized = path.rstrip(".,;:!?)]}")
    token = Path(normalized)
    if token.is_absolute():
        try:
            return str(token.relative_to(_REPO_ROOT))
        except ValueError:
            return _EVALUATOR_LOCAL_PATH_PLACEHOLDER
    return normalized


def _sanitize_failure_line(line: str) -> str:
    return _ABSOLUTE_PATH_RE.sub(
        lambda match: _redact_path(match.group(0)),
        line,
    )


def _collect_failure_detail(lines: list[str]) -> list[str]:
    detail = [line.strip() for line in lines if line.strip()]
    detail = [line for line in detail if line]
    detail = [line[:_MAX_FAILURE_DETAIL_LINE_CHARS] for line in detail[-_MAX_FAILURE_DETAIL_LINES:]]
    while detail and sum(len(line) for line in detail) > _MAX_FAILURE_DETAIL_BYTES:
        detail = detail[1:]
    return detail


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _params(row: JsonDict) -> JsonDict:
    try:
        payload = json.loads(str(row.get("params_json", "{}")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid params_json for PPA row {row.get('param_hash')}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"params_json is not an object for PPA row {row.get('param_hash')}")
    return payload


def _metric_provenance(row: JsonDict, metrics_csv: Path) -> JsonDict:
    fields = (
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "instance_area_um2",
        "stdcell_area_um2",
        "stdcell_count",
        "core_area_um2",
        "utilization_pct",
        "flow_elapsed_seconds",
        "stage_elapsed_seconds",
        "params_json",
    )
    return {
        "metrics_csv": _redact_path(str(metrics_csv)),
        **{field: row[field] for field in fields if str(row.get(field, "")).strip()},
    }


def _feasible_metrics(
    metrics_csv: Path,
    clock_period_ns: float,
    *,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
) -> list[JsonDict]:
    normalized_required_flow_variant = str(required_flow_variant or "").strip() or None
    normalized_required_synth_args = (
        None if required_synth_args is None else str(required_synth_args).strip()
    )

    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        raw_rows = [dict(row) for row in csv.DictReader(handle)]
    selected: dict[str, JsonDict] = {}
    for row in raw_rows:
        if str(row.get("status", "")) != "ok":
            continue
        params = _params(row)
        row_clock = float(params.get("CLOCK_PERIOD", 0.0))
        critical_path = float(row.get("critical_path_ns") or math.inf)
        flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
        synth_args = str(params.get("SYNTH_ARGS", "")).strip()
        if not flow_variant or abs(row_clock - clock_period_ns) > 1e-9:
            continue
        if (
            normalized_required_flow_variant is not None
            and flow_variant != normalized_required_flow_variant
        ):
            continue
        if (
            normalized_required_synth_args is not None
            and synth_args != normalized_required_synth_args
        ):
            continue
        if not math.isfinite(critical_path) or critical_path > clock_period_ns:
            continue
        previous = selected.get(flow_variant)
        if previous is None or float(row.get("instance_area_um2") or math.inf) < float(
            previous.get("instance_area_um2") or math.inf
        ):
            selected[flow_variant] = row
    if not selected:
        if normalized_required_flow_variant is not None or normalized_required_synth_args is not None:
            details = []
            if normalized_required_flow_variant is not None:
                details.append(f"FLOW_VARIANT={normalized_required_flow_variant}")
            if normalized_required_synth_args is not None:
                details.append(f"SYNTH_ARGS={normalized_required_synth_args or '<empty/default>'}")
            raise ValueError(
                f"no status=ok timing-feasible rows in {metrics_csv} matching "
                f"{', '.join(details)} at {clock_period_ns:g} ns"
            )
        raise ValueError(
            f"no status=ok timing-feasible {clock_period_ns:g} ns rows in {metrics_csv}"
        )
    return sorted(
        selected.values(),
        key=lambda row: (
            float(row.get("die_area") or math.inf),
            float(row.get("instance_area_um2") or math.inf),
            float(row.get("critical_path_ns") or math.inf),
        ),
    )


def _validate_targeted_binary_fsm_diagnostic(
    path: Path,
    *,
    required_profile: str,
    required_flow_variant: str | None,
    required_synth_args: str | None,
) -> JsonDict:
    if required_profile != _TARGETED_BINARY_FSM_PROFILE:
        raise ValueError(f"unsupported binary-FSM diagnostic profile: {required_profile}")
    if required_flow_variant != _TARGETED_BINARY_FSM_FLOW_VARIANT:
        raise ValueError("targeted binary-FSM diagnostic requires the exact targeted FLOW_VARIANT")
    if required_synth_args != "":
        raise ValueError("targeted binary-FSM diagnostic requires empty/default SYNTH_ARGS")

    diagnostic = _load(path)
    selected = diagnostic.get("selected_exact_row")
    if not isinstance(selected, dict):
        raise ValueError("binary-FSM diagnostic has no selected exact row")
    checks = {
        "version": type(diagnostic.get("version")) is int and diagnostic.get("version") == 1,
        "profile": diagnostic.get("profile") == _TARGETED_BINARY_FSM_PROFILE,
        "checker": diagnostic.get("checker") == _TARGETED_BINARY_FSM_CHECKER,
        "expected_flow_variant": (
            diagnostic.get("expected_flow_variant") == _TARGETED_BINARY_FSM_FLOW_VARIANT
        ),
        "netlist_exists": diagnostic.get("netlist_exists") is True,
        "expected_logical_netlist_path": (
            diagnostic.get("expected_logical_netlist_path") == _TARGETED_BINARY_FSM_NETLIST
        ),
        "promotion_valid": diagnostic.get("promotion_valid") is True,
        "width_valid": diagnostic.get("width_valid") is True,
        "selected_design": selected.get("design") == _TARGETED_BINARY_FSM_DESIGN,
        "selected_platform": selected.get("platform") == _TARGETED_BINARY_FSM_PLATFORM,
        "selected_tag": str(selected.get("tag") or "").startswith(
            _TARGETED_BINARY_FSM_TAG_PREFIX
        ),
        "selected_status": selected.get("status") == "ok",
        "selected_flow_variant": (
            selected.get("flow_variant") == _TARGETED_BINARY_FSM_FLOW_VARIANT
        ),
        "selected_synth_args": str(selected.get("synth_args") or "").strip() == "",
        "selected_die_area": selected.get("die_area") == "0 0 2500 2500",
        "selected_core_area": selected.get("core_area") == "50 50 2450 2450",
        "selected_place_density": str(selected.get("place_density") or "").strip() == "0.4",
        "selected_synth_hierarchical": (
            str(selected.get("synth_hierarchical") or "").strip() == "1"
        ),
        "selected_synth_memory_max_bits": (
            str(selected.get("synth_memory_max_bits") or "").strip() == "65536"
        ),
        "selected_failure_stage": not str(selected.get("failure_stage") or "").strip(),
        "selected_failure_returncode": selected.get("failure_returncode") in (None, ""),
        "selected_failure_signature": not str(
            selected.get("failure_signature") or ""
        ).strip(),
        "selected_param_hash": bool(str(selected.get("param_hash") or "").strip()),
        "selected_config_hash": bool(str(selected.get("config_hash") or "").strip()),
    }
    try:
        clock_period_ns = float(selected.get("clock_period_ns"))
        critical_path_ns = float(selected.get("critical_path_ns"))
    except (TypeError, ValueError):
        clock_period_ns = math.nan
        critical_path_ns = math.nan
    checks["selected_clock_period_ns"] = (
        math.isfinite(clock_period_ns) and clock_period_ns == 8.0
    )
    checks["selected_critical_path_ns"] = (
        math.isfinite(critical_path_ns) and critical_path_ns <= 8.0
    )
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(
            "targeted binary-FSM diagnostic failed strict validation: " + ", ".join(failed)
        )
    _validate_targeted_binary_fsm_signals(diagnostic.get("signals"))
    return diagnostic


def _validate_targeted_binary_fsm_signals(value: object) -> None:
    if not isinstance(value, dict) or set(value) != set(_TARGETED_BINARY_FSM_SIGNAL_INDICES):
        raise ValueError("targeted binary-FSM diagnostic has an invalid signals object")
    for signal, expected_indices in _TARGETED_BINARY_FSM_SIGNAL_INDICES.items():
        evidence = value.get(signal)
        if not isinstance(evidence, dict):
            raise ValueError(f"targeted binary-FSM diagnostic has no evidence for {signal}")
        if evidence.get("expected_bit_indices") != expected_indices:
            raise ValueError(f"targeted binary-FSM diagnostic has wrong expected indices for {signal}")
        packed = evidence.get("observed_packed_ranges")
        bits = evidence.get("observed_bit_indices")
        if not isinstance(packed, list) or not isinstance(bits, list):
            raise ValueError(f"targeted binary-FSM diagnostic has malformed evidence for {signal}")
        if bool(packed) == bool(bits):
            raise ValueError(
                f"targeted binary-FSM diagnostic must use exactly one observed representation for {signal}"
            )
        if packed:
            if len(packed) != 1 or not isinstance(packed[0], dict):
                raise ValueError(f"targeted binary-FSM diagnostic has invalid packed range for {signal}")
            msb = packed[0].get("msb")
            lsb = packed[0].get("lsb")
            if (
                not isinstance(msb, int)
                or isinstance(msb, bool)
                or not isinstance(lsb, int)
                or isinstance(lsb, bool)
            ):
                raise ValueError(f"targeted binary-FSM diagnostic has invalid packed range for {signal}")
            observed_indices = list(range(min(msb, lsb), max(msb, lsb) + 1))
        else:
            if any(not isinstance(bit, int) or isinstance(bit, bool) for bit in bits):
                raise ValueError(f"targeted binary-FSM diagnostic has invalid bit indices for {signal}")
            observed_indices = sorted(bits)
        if observed_indices != expected_indices or len(observed_indices) != len(expected_indices):
            raise ValueError(f"targeted binary-FSM diagnostic has wrong observed indices for {signal}")


def _validate_binary_fsm_metric_identity(diagnostic: JsonDict, metric: JsonDict) -> None:
    selected = diagnostic.get("selected_exact_row")
    if not isinstance(selected, dict):
        raise TypeError("validated binary-FSM diagnostic selected row is not an object")
    identity_matches = (
        str(metric.get("param_hash") or "").strip()
        == str(selected.get("param_hash") or "").strip()
        and str(metric.get("config_hash") or "").strip()
        == str(selected.get("config_hash") or "").strip()
        and str(metric.get("design") or "").strip()
        == str(selected.get("design") or "").strip()
        and str(metric.get("platform") or "").strip()
        == str(selected.get("platform") or "").strip()
    )
    try:
        metric_critical_path = float(metric.get("critical_path_ns"))
        selected_critical_path = float(selected.get("critical_path_ns"))
    except (TypeError, ValueError):
        identity_matches = False
        metric_critical_path = math.nan
        selected_critical_path = math.nan
    critical_path_matches = (
        math.isfinite(metric_critical_path)
        and math.isfinite(selected_critical_path)
        and math.isclose(
            metric_critical_path,
            selected_critical_path,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    )
    if not identity_matches or not critical_path_matches:
        raise ValueError("binary-FSM diagnostic does not match the selected PPA metrics row")


def _validate_targeted_config(path: Path, payload: JsonDict) -> None:
    normalized = path.as_posix()
    if normalized != _TARGETED_BINARY_FSM_CONFIG and not normalized.endswith(
        "/" + _TARGETED_BINARY_FSM_CONFIG
    ):
        raise ValueError("targeted activity power requires exact config_targeted_binary_fsm.json")
    cluster = payload.get("attention_decode_score_multivalue_cluster")
    if not isinstance(cluster, dict) or cluster.get("fsm_encoding") != "binary":
        raise ValueError("targeted activity config must require binary FSM encoding")


def _validate_strict_activity_power(
    activity_power: JsonDict,
    *,
    activity_manifest: JsonDict,
    flow_variant: str,
    clock_period_ns: float,
) -> None:
    expected_phases = {
        str(phase.get("phase", phase.get("name", ""))).strip()
        for phase in activity_manifest.get("phases", [])
        if isinstance(phase, dict)
    }
    phases = activity_power.get("phases")
    if not expected_phases or not isinstance(phases, list):
        raise ValueError("strict activity power requires every declared phase")
    observed_phases = {
        str(phase.get("phase", phase.get("name", ""))).strip()
        for phase in phases
        if isinstance(phase, dict)
    }
    if observed_phases != expected_phases or len(phases) != len(expected_phases):
        raise ValueError("strict activity power phase set does not match the activity manifest")
    if activity_power.get("model") != "postroute_phase_vcd_power_v1":
        raise ValueError("strict activity power requires direct routed VCD power")
    if activity_power.get("status") != "activity_backed":
        raise ValueError("strict activity power status is not activity_backed")
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("strict activity power promotion gate did not pass")
    if activity_power.get("flow_variant") != flow_variant:
        raise ValueError("strict activity power FLOW_VARIANT does not match the selected PPA row")
    if float(activity_power.get("clock_period_ns") or 0.0) != clock_period_ns:
        raise ValueError("strict activity power clock does not match the selected PPA row")
    if float(activity_power.get("min_sequential_register_activity_coverage") or 0.0) != 1.0:
        raise ValueError("strict activity power did not require 100% sequential coverage")

    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("strict activity power phase is not an object")
        phase_name = str(phase.get("phase", phase.get("name", ""))).strip()
        if not all(
            phase.get(gate) is True
            for gate in (
                "direct_vcd_annotation_pin_gate_pass",
                "trace_coverage_gate_pass",
                "annotation_gate_pass",
                "sequential_register_activity_gate_pass",
                "clock_period_gate_pass",
                "power_numeric_gate_pass",
                "phase_gate_pass",
            )
        ):
            raise ValueError(f"strict activity gates failed for phase {phase_name}")
        if float(phase.get("sequential_register_activity_coverage") or 0.0) != 1.0:
            raise ValueError(f"sequential coverage is below 100% for phase {phase_name}")
        assignments = int(phase.get("sequential_register_activity_assignment_count") or 0)
        matched = int(phase.get("sequential_register_activity_matched_count") or 0)
        applied = int(phase.get("sequential_register_activity_applied_count") or 0)
        if assignments <= 0 or assignments != matched or matched != applied:
            raise ValueError(f"sequential activity mapping is incomplete for phase {phase_name}")
        power = phase.get("power")
        if not isinstance(power, dict):
            raise ValueError(f"missing routed power for phase {phase_name}")
        for component in _POWER_COMPONENTS:
            value = power.get(component)
            if value is None or not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"non-finite {component} for phase {phase_name}")
        if float(power["total_w"]) <= 0.0:
            raise ValueError(f"non-positive total_w for phase {phase_name}")
    energy = activity_power.get("full_context_energy_j")
    if energy is None or not math.isfinite(float(energy)) or float(energy) <= 0.0:
        raise ValueError("strict activity power requires finite positive full-context energy")


def _sanitized_failure(exc: Exception) -> JsonDict:
    lines = [_sanitize_failure_line(line).strip() for line in str(exc).splitlines()]
    lines = [line for line in lines if line]
    if lines:
        summary = lines[0][:240]
    else:
        summary = f"{type(exc).__name__} failure"
    sanitized_lines = _collect_failure_detail(lines)
    if not sanitized_lines:
        sanitized_lines = lines[-_MAX_FAILURE_DETAIL_LINES:]
    return {
        "error_type": type(exc).__name__,
        "error_summary": summary,
        "detail": sanitized_lines,
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        "# Shared-score multivalue cluster activity power",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promoted candidates: `{payload['promoted_candidate_count']}`",
        f"- measured candidates: `{payload['candidate_count']}`",
        "",
        "| variant | path ns | instance mm2 | status | head cycles | head latency ms | energy mJ |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in payload["candidates"]:
        metric = row["ppa_metric"]
        activity = row.get("activity_power", {})
        energy = activity.get("full_context_energy_j")
        lines.append(
            "| {variant} | {path_ns} | {area_mm2:.6f} | {status} | {cycles} | {latency_ms} | {energy_mj} |".format(
                variant=row["flow_variant"],
                path_ns=metric.get("critical_path_ns"),
                area_mm2=float(metric.get("instance_area_um2", 0.0)) / 1.0e6,
                status=row["status"],
                cycles=activity.get("full_context_cycles"),
                latency_ms=(
                    float(activity["full_context_latency_s"]) * 1.0e3
                    if activity.get("full_context_latency_s") is not None
                    else None
                ),
                energy_mj=float(energy) * 1.0e3 if energy is not None else None,
            )
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    config: Path,
    cluster_metrics_csv: Path,
    equivalence_json: Path,
    orfs_design_config: Path,
    clock_period_ns: float,
    activity_dir: Path,
    min_sequential_register_activity_coverage: float = 0.95,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
    source_pnr_item_id: str | None = None,
    binary_fsm_diagnostic: Path | None = None,
    required_binary_fsm_profile: str | None = None,
) -> JsonDict:
    if not (0.0 < min_sequential_register_activity_coverage <= 1.0):
        raise ValueError("min_sequential_register_activity_coverage must be in (0, 1]")
    equivalence = _load(equivalence_json)
    if not equivalence.get("equivalence_pass"):
        raise ValueError("multivalue-cluster end-to-end equivalence did not pass")
    if (binary_fsm_diagnostic is None) != (required_binary_fsm_profile is None):
        raise ValueError(
            "binary_fsm_diagnostic and required_binary_fsm_profile must be provided together"
        )
    binary_diagnostic = None
    if binary_fsm_diagnostic is not None and required_binary_fsm_profile is not None:
        if min_sequential_register_activity_coverage != 1.0:
            raise ValueError("targeted activity power requires 100% sequential coverage")
        if source_pnr_item_id != _TARGETED_BINARY_FSM_PNR_ITEM:
            raise ValueError("targeted activity power requires the exact targeted-binary PNR item")
        config_payload = _load(config)
        _validate_targeted_config(config, config_payload)
        binary_diagnostic = _validate_targeted_binary_fsm_diagnostic(
            binary_fsm_diagnostic,
            required_profile=required_binary_fsm_profile,
            required_flow_variant=required_flow_variant,
            required_synth_args=required_synth_args,
        )
    else:
        config_payload = _load(config)
    activity_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "score_fill.vcd",
        "replay_value.vcd",
        "finalize_result.vcd",
        "attention_decode_score_multivalue_cluster_activity_manifest.json",
    ):
        path = activity_dir / name
        if path.is_file():
            path.unlink()
    activity_manifest = generate_phase_activity(
        config_payload,
        activity_dir,
        block_count=3,
        head_dim=128,
        clock_period_ns=clock_period_ns,
    )
    activity_manifest_path = (
        activity_dir / "attention_decode_score_multivalue_cluster_activity_manifest.json"
    )
    rows: list[JsonDict] = []
    for metric in _feasible_metrics(
        cluster_metrics_csv,
        clock_period_ns,
        required_flow_variant=required_flow_variant,
        required_synth_args=required_synth_args,
    ):
        params = _params(metric)
        flow_variant = str(params["FLOW_VARIANT"])
        if binary_diagnostic is not None:
            _validate_binary_fsm_metric_identity(binary_diagnostic, metric)
        candidate: JsonDict = {
            "candidate_id": f"multivalue_cluster_activity_{flow_variant}",
            "flow_variant": flow_variant,
            "ppa_metric": _metric_provenance(metric, cluster_metrics_csv),
        }
        try:
            activity_power = build_power_report(
                manifest=activity_manifest,
                manifest_path=activity_manifest_path,
                design_config=orfs_design_config,
                flow_variant=flow_variant,
                scope="tb/dut",
                min_vcd_coverage=0.05,
                min_vcd_pins=32,
                min_sequential_register_activity_coverage=min_sequential_register_activity_coverage,
                min_macro_active_coverage=0.01,
                min_macro_active_pins=16,
                timeout_seconds=1800,
            )
            if required_binary_fsm_profile is not None:
                _validate_strict_activity_power(
                    activity_power,
                    activity_manifest=activity_manifest,
                    flow_variant=flow_variant,
                    clock_period_ns=clock_period_ns,
                )
            candidate["activity_power"] = activity_power
            candidate["status"] = (
                "activity_backed" if activity_power.get("promotion_gate_pass") else "rejected_gate"
            )
        except Exception as exc:  # preserve an explicit negative row for physical-tool failures
            candidate["status"] = "measurement_failed"
            candidate["failure"] = _sanitized_failure(exc)
        rows.append(candidate)
    promoted = [row for row in rows if row["status"] == "activity_backed"]
    best = None
    if promoted:
        best = min(
            promoted,
            key=lambda row: (
                float(row["activity_power"]["full_context_energy_j"]),
                float(row["ppa_metric"]["instance_area_um2"]),
                float(row["ppa_metric"]["critical_path_ns"]),
            ),
        )
    selection_contract: JsonDict = {
        "required_flow_variant": str(required_flow_variant or "").strip() or None,
        "required_synth_args": (
            None if required_synth_args is None else str(required_synth_args).strip()
        ),
        "min_sequential_register_activity_coverage": min_sequential_register_activity_coverage,
    }
    if required_binary_fsm_profile is not None and binary_fsm_diagnostic is not None:
        selection_contract.update(
            {
                "required_binary_fsm_profile": required_binary_fsm_profile,
                "binary_fsm_diagnostic": _redact_path(str(binary_fsm_diagnostic)),
            }
        )
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_cluster_activity_power_v1",
        "decision": (
            "activity_backed_cluster_power_measured"
            if best is not None
            else "activity_power_rejected_no_gated_candidate"
        ),
        "promotion_gate_pass": best is not None,
        "candidate_count": len(rows),
        "promoted_candidate_count": len(promoted),
        "best_candidate_id": best["candidate_id"] if best is not None else None,
        "best": best,
        "candidates": rows,
        "activity_contract": {
            "clock_period_ns": activity_manifest["clock_period_ns"],
            "representative_block_count": activity_manifest["block_count"],
            "representative_full_transaction_cycles": activity_manifest[
                "representative_full_transaction_cycles"
            ],
            "phase_partition_cycle_sum": activity_manifest["phase_partition_cycle_sum"],
            "phases": activity_manifest["phases"],
        },
        "precision_status": "unchanged_integer_contract_from_merged_multivalue_equivalence",
        "equivalence": {
            "equivalence_pass": True,
            "decision": equivalence.get("decision"),
            "score_tensor_hash": equivalence.get("score_tensor_hash"),
            "final_tensor_hash": equivalence.get("final_tensor_hash"),
        },
        "source_dependencies": (
            [
                str(source_pnr_item_id).strip(),
                "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
            ]
            if str(source_pnr_item_id or "").strip()
            else [
                "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
                "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
            ]
        ),
        "selection_contract": selection_contract,
        "remaining_abstractions": [
            "FakeRAM area and power use Nangate45 proxy LEF/Liberty views, not SRAM compiler signoff.",
            "Value-memory, NoC, HBM/DRAM, command-distribution, and clock-tree composition outside the cluster are not included.",
            "RTL VCD is mapped to the routed netlist; each candidate records and gates direct annotation coverage.",
            "Score multiplier and shift derivation remain external to the cluster boundary.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--cluster-metrics-csv", type=Path, required=True)
    parser.add_argument("--equivalence-json", type=Path, required=True)
    parser.add_argument("--orfs-design-config", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=8.0)
    parser.add_argument(
        "--required-flow-variant",
        default=None,
        help="Optional exact FLOW_VARIANT to require before candidate measurement",
    )
    parser.add_argument(
        "--required-synth-args",
        default=None,
        help="Optional exact SYNTH_ARGS to require before candidate measurement",
    )
    parser.add_argument(
        "--source-pnr-item-id",
        default=None,
        help="Optional source PNR work-item ID for source_dependencies tracking",
    )
    parser.add_argument("--binary-fsm-diagnostic", type=Path, default=None)
    parser.add_argument("--required-binary-fsm-profile", default=None)
    parser.add_argument(
        "--min-sequential-register-activity-coverage",
        type=float,
        default=0.95,
    )
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        config=args.config,
        cluster_metrics_csv=args.cluster_metrics_csv,
        equivalence_json=args.equivalence_json,
        orfs_design_config=args.orfs_design_config,
        clock_period_ns=args.clock_period_ns,
        activity_dir=args.activity_dir,
        required_flow_variant=args.required_flow_variant,
        required_synth_args=args.required_synth_args,
        source_pnr_item_id=args.source_pnr_item_id,
        binary_fsm_diagnostic=args.binary_fsm_diagnostic,
        required_binary_fsm_profile=args.required_binary_fsm_profile,
        min_sequential_register_activity_coverage=args.min_sequential_register_activity_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
