#!/usr/bin/env python3
"""Measure activity-backed power across feasible multivalue-cluster PPA rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from npu.eval.check_attention_decode_score_multivalue_cluster_binary_fsm import (
    PROFILES as EXACT_STATE_PROFILES,
)
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
_STRICT_EXACT_STATE_PROFILE = EXACT_STATE_PROFILES["explicit_onehot"]
_STRICT_EXACT_STATE_PNR_ITEM = (
    "l1_decoder_attention_decode_score_multivalue_cluster_pnr_explicit_onehot_fsm_8ns_v1"
)


def _redact_path(path: str) -> str:
    normalized = path.rstrip(".,;:!?)]}")
    token = Path(normalized)
    if token.is_absolute():
        try:
            return str(token.relative_to(_REPO_ROOT))
        except ValueError:
            return _EVALUATOR_LOCAL_PATH_PLACEHOLDER
    return normalized


def _portable_path(path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return f"{_EVALUATOR_LOCAL_PATH_PLACEHOLDER}/{path.name}"


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
        "metrics_csv": str(metrics_csv),
        **{field: row[field] for field in fields if str(row.get(field, "")).strip()},
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raw_feasible_metrics(
    metrics_csv: Path,
    clock_period_ns: float,
    *,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
) -> list[JsonDict]:
    normalized_required_flow_variant = (
        None if required_flow_variant is None else str(required_flow_variant).strip()
    )
    normalized_required_synth_args = (
        None if required_synth_args is None else str(required_synth_args).strip()
    )

    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        raw_rows = [dict(row) for row in csv.DictReader(handle)]
    feasible: list[JsonDict] = []
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
        feasible.append(row)
    if not feasible:
        if normalized_required_flow_variant is not None or normalized_required_synth_args is not None:
            details = []
            if normalized_required_flow_variant is not None:
                details.append(f"FLOW_VARIANT={normalized_required_flow_variant}")
            if normalized_required_synth_args is not None:
                details.append(
                    f"SYNTH_ARGS={normalized_required_synth_args or '<empty/default>'}"
                )
            raise ValueError(
                f"no status=ok timing-feasible rows in {metrics_csv} matching "
                f"{', '.join(details)} at {clock_period_ns:g} ns"
            )
        raise ValueError(
            f"no status=ok timing-feasible {clock_period_ns:g} ns rows in {metrics_csv}"
        )
    return feasible


def _feasible_metrics(
    metrics_csv: Path,
    clock_period_ns: float,
    *,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
) -> list[JsonDict]:
    selected: dict[str, JsonDict] = {}
    for row in _raw_feasible_metrics(
        metrics_csv,
        clock_period_ns,
        required_flow_variant=required_flow_variant,
        required_synth_args=required_synth_args,
    ):
        flow_variant = str(_params(row).get("FLOW_VARIANT", "")).strip()
        previous = selected.get(flow_variant)
        if previous is None or float(row.get("instance_area_um2") or math.inf) < float(
            previous.get("instance_area_um2") or math.inf
        ):
            selected[flow_variant] = row
    return sorted(
        selected.values(),
        key=lambda row: (
            float(row.get("die_area") or math.inf),
            float(row.get("instance_area_um2") or math.inf),
            float(row.get("critical_path_ns") or math.inf),
        ),
    )


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


def _requires_strict_exact_state_diagnostic(
    *,
    required_flow_variant: str | None,
    source_pnr_item_id: str | None,
) -> bool:
    return (
        str(required_flow_variant or "").strip() == _STRICT_EXACT_STATE_PROFILE.flow_variant
        or str(source_pnr_item_id or "").strip() == _STRICT_EXACT_STATE_PNR_ITEM
    )


def _validate_strict_exact_state_diagnostic(
    *,
    diagnostic_path: Path,
    config: Path,
    clock_period_ns: float,
    required_flow_variant: str | None,
    required_synth_args: str | None,
) -> JsonDict:
    diagnostic = _load(diagnostic_path)
    reasons: list[str] = []

    checker = str(diagnostic.get("checker") or "").strip()
    if checker != _STRICT_EXACT_STATE_PROFILE.checker_id:
        reasons.append(
            "checker mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.checker_id}, got {checker or '<missing>'}"
        )
    profile = str(diagnostic.get("profile") or "").strip()
    if profile != _STRICT_EXACT_STATE_PROFILE.name:
        reasons.append(
            "profile mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.name}, got {profile or '<missing>'}"
        )
    expected_flow_variant = str(diagnostic.get("expected_flow_variant") or "").strip()
    if expected_flow_variant != _STRICT_EXACT_STATE_PROFILE.flow_variant:
        reasons.append(
            "expected_flow_variant mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.flow_variant}, got {expected_flow_variant or '<missing>'}"
        )
    if (
        required_flow_variant is not None
        and expected_flow_variant != str(required_flow_variant).strip()
    ):
        reasons.append(
            "expected_flow_variant does not match required flow variant "
            f"{str(required_flow_variant).strip()}"
        )
    expected_config_path = str(diagnostic.get("expected_config_path") or "").strip()
    if expected_config_path != _STRICT_EXACT_STATE_PROFILE.config_path:
        reasons.append(
            "expected_config_path mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.config_path}, got {expected_config_path or '<missing>'}"
        )
    if diagnostic.get("promotion_valid") is not True:
        reasons.append("promotion_valid is not true")
    if diagnostic.get("width_valid") is not True:
        reasons.append("width_valid is not true")
    if diagnostic.get("config_exists") is not True:
        reasons.append("config_exists is not true")
    if diagnostic.get("netlist_exists") is not True:
        reasons.append("netlist_exists is not true")
    config_fsm_encoding = str(diagnostic.get("config_fsm_encoding") or "").strip()
    if config_fsm_encoding != _STRICT_EXACT_STATE_PROFILE.expected_fsm_encoding:
        reasons.append(
            "config_fsm_encoding mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.expected_fsm_encoding}, got "
            f"{config_fsm_encoding or '<missing>'}"
        )

    config_sha256 = str(diagnostic.get("config_sha256") or "").strip()
    actual_config_sha256 = _sha256_file(config)
    if not config_sha256:
        reasons.append("missing config_sha256")
    elif config_sha256 != actual_config_sha256:
        reasons.append("config_sha256 does not match the provided config")

    netlist_sha256 = str(diagnostic.get("netlist_sha256") or "").strip()
    if not netlist_sha256:
        reasons.append("missing netlist_sha256")

    selected_exact_row = diagnostic.get("selected_exact_row")
    selected_row: JsonDict | None = selected_exact_row if isinstance(selected_exact_row, dict) else None
    if selected_row is None:
        reasons.append("selected_exact_row is missing or malformed")
        selected_row = {}

    required_flow_variant_text = None if required_flow_variant is None else str(required_flow_variant).strip()
    required_synth_args_text = None if required_synth_args is None else str(required_synth_args).strip()
    observed_row_flow_variant = str(selected_row.get("flow_variant") or "").strip()
    if observed_row_flow_variant != _STRICT_EXACT_STATE_PROFILE.flow_variant:
        reasons.append(
            "selected_exact_row flow_variant mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.flow_variant}, got "
            f"{observed_row_flow_variant or '<missing>'}"
        )
    if (
        required_flow_variant_text is not None
        and observed_row_flow_variant != required_flow_variant_text
    ):
        reasons.append(
            "selected_exact_row flow_variant does not match required flow variant "
            f"{required_flow_variant_text}"
        )
    observed_row_synth_args = str(selected_row.get("synth_args") or "").strip()
    if observed_row_synth_args != _STRICT_EXACT_STATE_PROFILE.synth_args:
        reasons.append(
            "selected_exact_row synth_args mismatch: expected "
            f"{_STRICT_EXACT_STATE_PROFILE.synth_args or '<empty/default>'}, got "
            f"{observed_row_synth_args or '<missing>'}"
        )
    if (
        required_synth_args_text is not None
        and observed_row_synth_args != required_synth_args_text
    ):
        reasons.append(
            "selected_exact_row synth_args does not match required_synth_args "
            f"{required_synth_args_text or '<empty/default>'}"
        )
    if str(selected_row.get("status") or "").strip() != "ok":
        reasons.append("selected_exact_row status is not ok")
    for key in ("design", "platform", "config_hash", "param_hash"):
        if not str(selected_row.get(key) or "").strip():
            reasons.append(f"selected_exact_row is missing {key}")
    try:
        observed_clock_period = float(selected_row.get("clock_period_ns"))
    except (TypeError, ValueError):
        reasons.append("selected_exact_row clock_period_ns is missing or invalid")
    else:
        if abs(observed_clock_period - clock_period_ns) > 1e-9:
            reasons.append(
                "selected_exact_row clock_period_ns mismatch: expected "
                f"{clock_period_ns:g}, got {observed_clock_period:g}"
            )
    try:
        observed_critical_path = float(selected_row.get("critical_path_ns"))
    except (TypeError, ValueError):
        reasons.append("selected_exact_row critical_path_ns is missing or invalid")
    else:
        if not math.isfinite(observed_critical_path):
            reasons.append("selected_exact_row critical_path_ns is not finite")
        elif observed_critical_path > clock_period_ns:
            reasons.append(
                "selected_exact_row critical_path_ns exceeds required clock period "
                f"{clock_period_ns:g}"
            )

    if reasons:
        raise ValueError("strict explicit-onehot exact-state diagnostic rejected: " + "; ".join(reasons))

    return {
        "diagnostic_json": _portable_path(diagnostic_path),
        "diagnostic_sha256": _sha256_file(diagnostic_path),
        "checker": checker,
        "profile": profile,
        "expected_flow_variant": expected_flow_variant,
        "expected_config_path": expected_config_path,
        "config_sha256": config_sha256,
        "netlist_sha256": netlist_sha256,
        "selected_exact_row": selected_row,
    }


def _metric_matches_selected_exact_row(metric: JsonDict, selected_row: JsonDict) -> list[str]:
    params = _params(metric)
    reasons: list[str] = []
    for key in ("design", "platform", "config_hash", "param_hash"):
        expected = str(selected_row.get(key) or "").strip()
        observed = str(metric.get(key) or "").strip()
        if observed != expected:
            reasons.append(
                f"{key} mismatch: expected {expected or '<missing>'}, got {observed or '<missing>'}"
            )
    observed_flow_variant = str(params.get("FLOW_VARIANT") or "").strip()
    expected_flow_variant = str(selected_row.get("flow_variant") or "").strip()
    if observed_flow_variant != expected_flow_variant:
        reasons.append(
            "flow_variant mismatch: expected "
            f"{expected_flow_variant or '<missing>'}, got {observed_flow_variant or '<missing>'}"
        )
    observed_synth_args = str(params.get("SYNTH_ARGS") or "").strip()
    expected_synth_args = str(selected_row.get("synth_args") or "").strip()
    if observed_synth_args != expected_synth_args:
        reasons.append(
            "synth_args mismatch: expected "
            f"{expected_synth_args or '<empty/default>'}, got "
            f"{observed_synth_args or '<missing>'}"
        )
    try:
        observed_critical_path = float(metric.get("critical_path_ns") or math.inf)
        expected_critical_path = float(selected_row.get("critical_path_ns"))
    except (TypeError, ValueError):
        reasons.append("critical_path_ns is missing or invalid for exact-row binding")
    else:
        if abs(observed_critical_path - expected_critical_path) > 1e-9:
            reasons.append(
                "critical_path_ns mismatch: expected "
                f"{expected_critical_path:g}, got {observed_critical_path:g}"
            )
    return reasons


def _select_strict_exact_state_metric(
    feasible_metrics: list[JsonDict],
    exact_state_provenance: JsonDict,
) -> JsonDict:
    selected_row = exact_state_provenance["selected_exact_row"]
    matches: list[JsonDict] = []
    mismatches: list[tuple[JsonDict, list[str]]] = []
    for metric in feasible_metrics:
        reasons = _metric_matches_selected_exact_row(metric, selected_row)
        if reasons:
            mismatches.append((metric, reasons))
        else:
            matches.append(metric)
    if not matches:
        detail = ""
        if mismatches:
            metric, reasons = mismatches[0]
            detail = (
                f"; first mismatch for param_hash={str(metric.get('param_hash') or '<missing>').strip()}: "
                + "; ".join(reasons)
            )
        raise ValueError(
            "strict explicit-onehot exact-state diagnostic rejected: no timing-feasible metrics row "
            "matches selected_exact_row identity"
            + detail
        )
    if len(matches) > 1:
        raise ValueError(
            "strict explicit-onehot exact-state diagnostic rejected: ambiguous timing-feasible "
            f"metrics rows matched selected_exact_row identity ({len(matches)} matches)"
        )
    return matches[0]


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
    exact_state_diagnostic_json: Path | None = None,
) -> JsonDict:
    if not (0.0 < min_sequential_register_activity_coverage <= 1.0):
        raise ValueError("min_sequential_register_activity_coverage must be in (0, 1]")
    equivalence = _load(equivalence_json)
    if not equivalence.get("equivalence_pass"):
        raise ValueError("multivalue-cluster end-to-end equivalence did not pass")
    require_strict_exact_state_diagnostic = _requires_strict_exact_state_diagnostic(
        required_flow_variant=required_flow_variant,
        source_pnr_item_id=source_pnr_item_id,
    )
    if require_strict_exact_state_diagnostic and exact_state_diagnostic_json is None:
        raise ValueError(
            "strict explicit-onehot activity power requires exact_state_diagnostic_json"
        )
    feasible_metrics = _raw_feasible_metrics(
        cluster_metrics_csv,
        clock_period_ns,
        required_flow_variant=required_flow_variant,
        required_synth_args=required_synth_args,
    )
    exact_state_provenance: JsonDict | None = None
    selected_metrics = _feasible_metrics(
        cluster_metrics_csv,
        clock_period_ns,
        required_flow_variant=required_flow_variant,
        required_synth_args=required_synth_args,
    )
    if exact_state_diagnostic_json is not None:
        exact_state_provenance = _validate_strict_exact_state_diagnostic(
            diagnostic_path=exact_state_diagnostic_json,
            config=config,
            clock_period_ns=clock_period_ns,
            required_flow_variant=required_flow_variant,
            required_synth_args=required_synth_args,
        )
        selected_metrics = [_select_strict_exact_state_metric(feasible_metrics, exact_state_provenance)]
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
        _load(config),
        activity_dir,
        block_count=3,
        head_dim=128,
        clock_period_ns=clock_period_ns,
    )
    activity_manifest_path = (
        activity_dir / "attention_decode_score_multivalue_cluster_activity_manifest.json"
    )
    rows: list[JsonDict] = []
    for metric in selected_metrics:
        params = _params(metric)
        flow_variant = str(params["FLOW_VARIANT"])
        candidate: JsonDict = {
            "candidate_id": f"multivalue_cluster_activity_{flow_variant}",
            "flow_variant": flow_variant,
            "ppa_metric": _metric_provenance(metric, cluster_metrics_csv),
        }
        if exact_state_provenance is not None:
            candidate["exact_state_provenance"] = exact_state_provenance
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
        "selection_contract": {
            "required_flow_variant": (
                None if required_flow_variant is None else str(required_flow_variant).strip()
            ),
            "required_synth_args": (
                None if required_synth_args is None else str(required_synth_args).strip()
            ),
            "required_exact_state_checker": (
                _STRICT_EXACT_STATE_PROFILE.checker_id
                if require_strict_exact_state_diagnostic
                else None
            ),
            "required_exact_state_profile": (
                _STRICT_EXACT_STATE_PROFILE.name
                if require_strict_exact_state_diagnostic
                else None
            ),
            "required_exact_state_diagnostic_json": (
                None
                if exact_state_diagnostic_json is None
                else _portable_path(exact_state_diagnostic_json)
            ),
            "min_sequential_register_activity_coverage": min_sequential_register_activity_coverage,
        },
        "exact_state_diagnostic": exact_state_provenance,
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
    parser.add_argument(
        "--exact-state-diagnostic-json",
        type=Path,
        default=None,
        help="Required strict explicit-onehot exact-state diagnostic for v16 activity power",
    )
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
        exact_state_diagnostic_json=args.exact_state_diagnostic_json,
        min_sequential_register_activity_coverage=args.min_sequential_register_activity_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
