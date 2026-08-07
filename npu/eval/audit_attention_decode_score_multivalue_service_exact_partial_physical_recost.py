#!/usr/bin/env python3
"""Normalize exact-partial composed-service physical evidence for later rerank."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MODEL = "decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1"
_DECISION = "exact_partial_composed_service_physical_recost_recorded"
_EXPECTED_SERVICE_MODEL = "decoder_attention_decode_score_multivalue_service_activity_power_v1"
_EXPECTED_SERVICE_DECISION = "activity_backed_service_power_measured"
_EXPECTED_SERVICE_CASE_ID = "c1_p128_b4_rr"
_EXPECTED_SERVICE_DESIGN = "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr"
_EXPECTED_TEMPORAL_PROPOSAL_ID = "prop_l1_decoder_attention_exact_partial_physical_calibration_v1"
_EXPECTED_TEMPORAL_PROPOSAL_PATH = (
    "docs/proposals/prop_l1_decoder_attention_exact_partial_physical_calibration_v1/proposal.json"
)
_EXPECTED_TEMPORAL_DESIGN_PREFIX = "attention_score32_exact_partial_temporal_finalizer_physical_l"
_EXPECTED_FIFO_DESIGN_PREFIX = "attention_exact_partial_async_fifo_d4_"
_EXPECTED_FIFO_PROPOSAL_ID = _EXPECTED_TEMPORAL_PROPOSAL_ID
_EXPECTED_FIFO_PROPOSAL_PATH = _EXPECTED_TEMPORAL_PROPOSAL_PATH
_EXPECTED_FUNCTIONAL_MODEL = "attention_decode_score_multivalue_service_finalized_cdc_probe_v1"
_FIFO_AREA_REL_TOL = 0.05
_FIFO_POWER_REL_TOL = 0.5
_CSV_FIELDS = (
    "candidate_id",
    "service_case_id",
    "fifo_timed_domain",
    "fifo_canonical_rule",
    "energy_status",
    "service_domain_period_ns",
    "temporal_domain_period_ns",
    "service_cycles",
    "temporal_cycles",
    "finalizer_cycles",
    "service_domain_time_ns",
    "temporal_domain_time_ns",
    "overlap_lower_bound_ns",
    "serial_upper_bound_ns",
    "overlap_lower_bound_us",
    "serial_upper_bound_us",
    "throughput_upper_bound_per_s",
    "throughput_lower_bound_per_s",
    "service_instance_area_um2",
    "temporal_instance_area_um2",
    "fifo_instance_area_um2",
    "composed_instance_area_um2",
    "service_generic_total_power_mw",
    "temporal_generic_total_power_mw",
    "fifo_generic_total_power_mw",
    "generic_composed_total_power_mw",
    "service_activity_window_power_mw",
    "service_activity_window_dynamic_power_mw",
    "service_activity_window_leakage_power_mw",
    "service_activity_window_energy_j",
    "service_activity_window_cycle_count",
    "service_design",
    "temporal_design",
    "fifo_canonical_design",
    "fifo_source_design",
    "fifo_destination_design",
    "service_source_item_id",
    "temporal_proposal_id",
    "fifo_proposal_id",
)


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _string(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _finite_float(value: Any, label: str, *, positive: bool | None = None) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be a finite number")
    if positive is True and numeric <= 0.0:
        raise ValueError(f"{label} must be positive")
    if positive is False and numeric < 0.0:
        raise ValueError(f"{label} must be non-negative")
    return numeric


def _int(value: Any, label: str, *, positive: bool | None = None) -> int:
    numeric = _finite_float(value, label)
    if int(numeric) != numeric:
        raise ValueError(f"{label} must be an integer")
    integer = int(numeric)
    if positive is True and integer <= 0:
        raise ValueError(f"{label} must be positive")
    if positive is False and integer < 0:
        raise ValueError(f"{label} must be non-negative")
    return integer


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _row_sha256(row: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _params_json(row: dict[str, str], *, label: str) -> JsonDict:
    raw = str(row.get("params_json") or "").strip()
    if not raw:
        raise ValueError(f"{label} params_json must be present")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} params_json must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} params_json must be an object")
    return payload


def _clock_matches(row: dict[str, str], *, label: str, requested_clock_period_ns: float) -> bool:
    params = _params_json(row, label=label)
    actual = _finite_float(params.get("CLOCK_PERIOD"), f"{label} params_json.CLOCK_PERIOD", positive=True)
    return abs(actual - requested_clock_period_ns) <= 1.0e-9


def _select_metrics_row(
    metrics_csv: Path,
    *,
    label: str,
    design: str,
    requested_clock_period_ns: float,
) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    for row in _load_metrics_rows(metrics_csv):
        if str(row.get("design") or "").strip() != design:
            continue
        if str(row.get("status") or "").strip() != "ok":
            continue
        if not _clock_matches(row, label=label, requested_clock_period_ns=requested_clock_period_ns):
            continue
        matches.append(row)
    if len(matches) != 1:
        raise ValueError(
            f"{label} requires exactly one status=ok row for design {design!r} at CLOCK_PERIOD={requested_clock_period_ns:g} ns"
        )
    row = matches[0]
    critical_path_ns = _finite_float(row.get("critical_path_ns"), f"{label} critical_path_ns", positive=True)
    if critical_path_ns > requested_clock_period_ns:
        raise ValueError(f"{label} selected row is not timing-feasible at {requested_clock_period_ns:g} ns")
    return {
        "design": design,
        "platform": _string(row.get("platform"), f"{label} platform"),
        "config_hash": _string(row.get("config_hash"), f"{label} config_hash"),
        "param_hash": _string(row.get("param_hash"), f"{label} param_hash"),
        "tag": _string(row.get("tag"), f"{label} tag"),
        "status": "ok",
        "critical_path_ns": critical_path_ns,
        "die_area_um2": _finite_float(row.get("die_area"), f"{label} die_area", positive=True),
        "total_power_mw": _finite_float(row.get("total_power_mw"), f"{label} total_power_mw", positive=False),
        "instance_area_um2": _finite_float(row.get("instance_area_um2"), f"{label} instance_area_um2", positive=True),
        "core_area_um2": _finite_float(row.get("core_area_um2"), f"{label} core_area_um2", positive=True),
        "requested_clock_period_ns": requested_clock_period_ns,
        "params_json": _params_json(row, label=label),
        "row_sha256": _row_sha256(row),
    }


def _load_design_config(path: Path, *, label: str, expected_top_name: str | None = None) -> JsonDict:
    payload = _load_json(path)
    if expected_top_name is not None:
        if _string(payload.get("top_name"), f"{label} top_name") != expected_top_name:
            raise ValueError(f"{label} top_name mismatch")
    return payload


def _load_macro_manifest(path: Path, *, label: str, expected_module: str | None = None) -> JsonDict:
    payload = _load_json(path)
    if expected_module is not None:
        if _string(payload.get("module"), f"{label} module") != expected_module:
            raise ValueError(f"{label} module mismatch")
    return payload


def _validate_measurement_status(payload: JsonDict, *, label: str) -> None:
    status = _string(payload.get("status"), f"{label} status")
    if status != "ok":
        raise ValueError(f"{label} status must be 'ok'")


def _validate_proposal_ref(
    payload: JsonDict,
    *,
    label: str,
    expected_id: str,
    expected_path: str,
) -> JsonDict | None:
    proposal_ref = payload.get("proposal_ref")
    if proposal_ref is None:
        return None
    if not isinstance(proposal_ref, dict):
        raise ValueError(f"{label} proposal_ref must be an object")
    proposal_id = _string(proposal_ref.get("proposal_id"), f"{label} proposal_ref.proposal_id")
    proposal_path = _string(proposal_ref.get("proposal_path"), f"{label} proposal_ref.proposal_path")
    if proposal_id != expected_id or proposal_path != expected_path:
        raise ValueError(f"{label} proposal_ref mismatches the expected source proposal")
    return {"proposal_id": proposal_id, "proposal_path": proposal_path}


def _validate_service_anchor(payload: JsonDict) -> JsonDict:
    if _string(payload.get("model"), "service anchor model") != _EXPECTED_SERVICE_MODEL:
        raise ValueError("service anchor has an unexpected model")
    if _string(payload.get("decision"), "service anchor decision") != _EXPECTED_SERVICE_DECISION:
        raise ValueError("service anchor has an unexpected decision")
    selection = payload.get("selection_contract")
    if not isinstance(selection, dict):
        raise ValueError("service anchor requires selection_contract")
    if _string(selection.get("case_id"), "service anchor selection_contract.case_id") != _EXPECTED_SERVICE_CASE_ID:
        raise ValueError("service anchor case_id must be c1_p128_b4_rr")
    if payload.get("promotion_gate_pass") is not True:
        raise ValueError("service anchor promotion_gate_pass must be true")
    best = payload.get("best")
    if not isinstance(best, dict):
        raise ValueError("service anchor requires best")
    ppa_metric = best.get("ppa_metric")
    if not isinstance(ppa_metric, dict):
        raise ValueError("service anchor requires best.ppa_metric")
    if _string(ppa_metric.get("status"), "service anchor best.ppa_metric.status") != "ok":
        raise ValueError("service anchor ppa metric status must be ok")
    if _string(ppa_metric.get("design"), "service anchor best.ppa_metric.design") != _EXPECTED_SERVICE_DESIGN:
        raise ValueError("service anchor design mismatch")
    activity_contract = payload.get("activity_contract")
    if not isinstance(activity_contract, dict):
        raise ValueError("service anchor requires activity_contract")
    service_clock_ns = _finite_float(
        activity_contract.get("clock_period_ns"),
        "service anchor activity_contract.clock_period_ns",
        positive=True,
    )
    service_cycles = _int(
        activity_contract.get("cycle_count"),
        "service anchor activity_contract.cycle_count",
        positive=True,
    )
    result_semantics = activity_contract.get("result_semantics")
    if result_semantics is not None:
        if not isinstance(result_semantics, dict):
            raise ValueError("service anchor activity_contract.result_semantics must be an object")
        if _string(result_semantics.get("result_mode"), "service anchor result_mode") != "exact_partial":
            raise ValueError("service anchor result_mode must be exact_partial")
        if result_semantics.get("supports_sequence_window_composition") is not True:
            raise ValueError("service anchor must support sequence-window composition")
    activity_power = best.get("activity_power")
    if not isinstance(activity_power, dict):
        raise ValueError("service anchor requires best.activity_power")
    if _string(activity_power.get("status"), "service anchor best.activity_power.status") != "activity_backed":
        raise ValueError("service anchor best.activity_power.status must be activity_backed")
    authoritative = best.get("authoritative_composed_c1_total_ppa")
    if not isinstance(authoritative, dict):
        raise ValueError("service anchor requires best.authoritative_composed_c1_total_ppa")
    instance_area_um2 = _finite_float(
        authoritative.get("instance_area_um2"),
        "service anchor authoritative instance_area_um2",
        positive=True,
    )
    generic_total_power_mw = _finite_float(
        authoritative.get("total_power_mw"),
        "service anchor authoritative total_power_mw",
        positive=False,
    )
    critical_path_ns = _finite_float(
        authoritative.get("critical_path_ns"),
        "service anchor authoritative critical_path_ns",
        positive=True,
    )
    if critical_path_ns > service_clock_ns:
        raise ValueError("service anchor critical_path_ns exceeds the service domain period")
    service_window = best.get("component_service_window_energy")
    if not isinstance(service_window, dict):
        raise ValueError("service anchor requires best.component_service_window_energy")
    if service_window.get("is_total_token_energy") is not False:
        raise ValueError("service anchor component_service_window_energy must not claim total-token energy")
    power_w = service_window.get("power_w")
    energy_j = service_window.get("energy_j")
    if not isinstance(power_w, dict) or not isinstance(energy_j, dict):
        raise ValueError("service anchor component_service_window_energy requires power_w and energy_j")
    service_window_power_total_w = _finite_float(
        power_w.get("total"),
        "service anchor component_service_window_energy.power_w.total",
        positive=True,
    )
    service_window_power_dynamic_w = _finite_float(
        power_w.get("dynamic"),
        "service anchor component_service_window_energy.power_w.dynamic",
        positive=False,
    )
    service_window_power_leakage_w = _finite_float(
        power_w.get("leakage"),
        "service anchor component_service_window_energy.power_w.leakage",
        positive=False,
    )
    service_window_energy_total_j = _finite_float(
        energy_j.get("dynamic_plus_leakage"),
        "service anchor component_service_window_energy.energy_j.dynamic_plus_leakage",
        positive=True,
    )
    service_window_energy_dynamic_j = _finite_float(
        energy_j.get("dynamic"),
        "service anchor component_service_window_energy.energy_j.dynamic",
        positive=False,
    )
    service_window_energy_leakage_j = _finite_float(
        energy_j.get("leakage"),
        "service anchor component_service_window_energy.energy_j.leakage",
        positive=False,
    )
    service_window_cycle_count = _int(
        service_window.get("cycle_count"),
        "service anchor component_service_window_energy.cycle_count",
        positive=True,
    )
    source_item_id = ""
    dependency = payload.get("dependency_contract")
    if isinstance(dependency, dict):
        integrated = dependency.get("integrated_service_c1")
        if isinstance(integrated, dict):
            if integrated.get("exact_match") is not True:
                raise ValueError("service anchor integrated_service_c1.exact_match must be true")
            if integrated.get("no_protocol_errors") is not True:
                raise ValueError("service anchor integrated_service_c1.no_protocol_errors must be true")
            if integrated.get("cycle_bound_ok") is not True:
                raise ValueError("service anchor integrated_service_c1.cycle_bound_ok must be true")
    for key in ("source_item_id", "item_id", "report_item_id"):
        if key in payload and str(payload.get(key) or "").strip():
            source_item_id = str(payload.get(key)).strip()
            break
    if not source_item_id:
        source_item_id = str(payload.get("source_item_id") or best.get("source_item_id") or "").strip()
    _validate_proposal_ref(
        payload,
        label="service anchor",
        expected_id="prop_l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1",
        expected_path=(
            "docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1/proposal.json"
        ),
    )
    return {
        "case_id": _EXPECTED_SERVICE_CASE_ID,
        "design": _EXPECTED_SERVICE_DESIGN,
        "clock_period_ns": service_clock_ns,
        "activity_contract_cycle_count": service_cycles,
        "critical_path_ns": critical_path_ns,
        "instance_area_um2": instance_area_um2,
        "generic_total_power_mw": generic_total_power_mw,
        "die_area_um2": _finite_float(authoritative.get("die_area"), "service anchor die_area", positive=True),
        "activity_backed_window": {
            "cycle_count": service_window_cycle_count,
            "power_total_w": service_window_power_total_w,
            "power_dynamic_w": service_window_power_dynamic_w,
            "power_leakage_w": service_window_power_leakage_w,
            "energy_total_j": service_window_energy_total_j,
            "energy_dynamic_j": service_window_energy_dynamic_j,
            "energy_leakage_j": service_window_energy_leakage_j,
        },
        "activity_power": {
            "status": _string(activity_power.get("status"), "service anchor best.activity_power.status"),
            "scope": str(activity_power.get("scope") or "").strip(),
        },
        "source_item_id": source_item_id,
    }


def _validate_temporal_measurement(
    *,
    metrics_csv: Path,
    design: str,
    requested_clock_period_ns: float,
    config_json: Path,
    macro_manifest_json: Path,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
) -> JsonDict:
    row = _select_metrics_row(
        metrics_csv,
        label="temporal row",
        design=design,
        requested_clock_period_ns=requested_clock_period_ns,
    )
    design = row["design"]
    if not design.startswith(_EXPECTED_TEMPORAL_DESIGN_PREFIX):
        raise ValueError("temporal row design must be an exact-partial temporal-finalizer harness")
    config = _load_design_config(config_json, label="temporal config", expected_top_name=design)
    harness = config.get("attention_score32_exact_partial_temporal_finalizer_physical_harness")
    if not isinstance(harness, dict):
        raise ValueError("temporal config requires attention_score32_exact_partial_temporal_finalizer_physical_harness")
    divider_lanes = _int(harness.get("divider_lanes"), "temporal config divider_lanes", positive=True)
    if f"_l{divider_lanes}" not in design:
        raise ValueError("temporal config divider_lanes must match design suffix")
    manifest = _load_macro_manifest(macro_manifest_json, label="temporal macro manifest", expected_module=design)
    params = manifest.get("manifest_params")
    if not isinstance(params, dict):
        raise ValueError("temporal macro manifest requires manifest_params")
    macro_count = _int(params.get("macro_count"), "temporal macro manifest macro_count", positive=True)
    if macro_count != 104:
        raise ValueError("temporal row macro_count must be 104")
    config_links = config.get("report_links")
    if not isinstance(config_links, dict):
        raise ValueError("temporal config requires report_links")
    effective_proposal_id = proposal_id or _string(config_links.get("proposal_id"), "temporal config report_links.proposal_id")
    effective_proposal_path = proposal_path or _string(
        config_links.get("proposal_path"), "temporal config report_links.proposal_path"
    )
    if (
        effective_proposal_id != _EXPECTED_TEMPORAL_PROPOSAL_ID
        or effective_proposal_path != _EXPECTED_TEMPORAL_PROPOSAL_PATH
    ):
        raise ValueError("temporal config proposal lineage mismatches the expected source proposal")
    return {
        "design": design,
        "clock_period_ns": row["requested_clock_period_ns"],
        "critical_path_ns": row["critical_path_ns"],
        "instance_area_um2": row["instance_area_um2"],
        "total_power_mw": row["total_power_mw"],
        "die_area_um2": row["die_area_um2"],
        "raw_macro_area_um2": _finite_float(
            params.get("total_macro_area_um2", 0.0),
            "temporal macro manifest total_macro_area_um2",
            positive=False,
        ),
        "macro_count": macro_count,
        "divider_lanes": divider_lanes,
        "proposal_ref": {"proposal_id": effective_proposal_id, "proposal_path": effective_proposal_path},
        "metrics_csv": _portable_path(metrics_csv),
        "config_json": _portable_path(config_json),
        "macro_manifest_json": _portable_path(macro_manifest_json),
        "selected_row_sha256": row["row_sha256"],
    }


def _validate_fifo_measurement(
    *,
    metrics_csv: Path,
    design: str,
    requested_clock_period_ns: float,
    config_json: Path,
    macro_manifest_json: Path,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
) -> JsonDict:
    row = _select_metrics_row(
        metrics_csv,
        label="async fifo row",
        design=design,
        requested_clock_period_ns=requested_clock_period_ns,
    )
    design = row["design"]
    if not design.startswith(_EXPECTED_FIFO_DESIGN_PREFIX):
        raise ValueError("async fifo row design must be an exact-partial async-fifo harness")
    config = _load_design_config(config_json, label="async fifo config", expected_top_name=design)
    harness = config.get("attention_exact_partial_async_fifo_physical_harness")
    if not isinstance(harness, dict):
        raise ValueError("async fifo config requires attention_exact_partial_async_fifo_physical_harness")
    timed_domain = _string(harness.get("timed_domain"), "async fifo config timed_domain")
    if timed_domain not in {"source", "destination"}:
        raise ValueError("async fifo row timed_domain must be source or destination")
    manifest = _load_macro_manifest(macro_manifest_json, label="async fifo macro manifest", expected_module=design)
    params = manifest.get("manifest_params")
    if not isinstance(params, dict):
        raise ValueError("async fifo macro manifest requires manifest_params")
    manifest_timed_domain = _string(params.get("timed_domain"), "async fifo macro manifest timed_domain")
    if manifest_timed_domain != timed_domain:
        raise ValueError("async fifo manifest timed_domain mismatch")
    macro_count = _int(params.get("macro_count", 0), "async fifo macro manifest macro_count", positive=False)
    if macro_count != 0:
        raise ValueError("async fifo row macro_count must be 0")
    config_links = config.get("report_links")
    if not isinstance(config_links, dict):
        raise ValueError("async fifo config requires report_links")
    effective_proposal_id = proposal_id or _string(config_links.get("proposal_id"), "async fifo config report_links.proposal_id")
    effective_proposal_path = proposal_path or _string(
        config_links.get("proposal_path"), "async fifo config report_links.proposal_path"
    )
    if effective_proposal_id != _EXPECTED_FIFO_PROPOSAL_ID or effective_proposal_path != _EXPECTED_FIFO_PROPOSAL_PATH:
        raise ValueError("async fifo config proposal lineage mismatches the expected source proposal")
    return {
        "design": design,
        "timed_domain": timed_domain,
        "clock_period_ns": row["requested_clock_period_ns"],
        "critical_path_ns": row["critical_path_ns"],
        "instance_area_um2": row["instance_area_um2"],
        "total_power_mw": row["total_power_mw"],
        "die_area_um2": row["die_area_um2"],
        "macro_count": macro_count,
        "proposal_ref": {"proposal_id": effective_proposal_id, "proposal_path": effective_proposal_path},
        "metrics_csv": _portable_path(metrics_csv),
        "config_json": _portable_path(config_json),
        "macro_manifest_json": _portable_path(macro_manifest_json),
        "selected_row_sha256": row["row_sha256"],
    }


def _require_close_rel(actual: float, expected: float, *, label: str, rel_tol: float) -> None:
    if expected == 0.0:
        if abs(actual) > rel_tol:
            raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")
        return
    if abs(actual - expected) / abs(expected) > rel_tol:
        raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


def _validate_fifo_pair(
    *,
    source_metrics_csv: Path,
    source_design: str,
    source_clock_period_ns: float,
    source_config_json: Path,
    source_macro_manifest_json: Path,
    destination_metrics_csv: Path,
    destination_design: str,
    destination_clock_period_ns: float,
    destination_config_json: Path,
    destination_macro_manifest_json: Path,
    canonical_timed_domain: str = "source",
) -> JsonDict:
    source = _validate_fifo_measurement(
        metrics_csv=source_metrics_csv,
        design=source_design,
        requested_clock_period_ns=source_clock_period_ns,
        config_json=source_config_json,
        macro_manifest_json=source_macro_manifest_json,
    )
    destination = _validate_fifo_measurement(
        metrics_csv=destination_metrics_csv,
        design=destination_design,
        requested_clock_period_ns=destination_clock_period_ns,
        config_json=destination_config_json,
        macro_manifest_json=destination_macro_manifest_json,
    )
    if source["timed_domain"] != "source":
        raise ValueError("async fifo source view must have timed_domain=source")
    if destination["timed_domain"] != "destination":
        raise ValueError("async fifo destination view must have timed_domain=destination")
    if canonical_timed_domain not in {"source", "destination"}:
        raise ValueError("canonical FIFO timed domain must be source or destination")
    if source["proposal_ref"] != destination["proposal_ref"]:
        raise ValueError("async fifo source/destination proposal lineage mismatch")
    if abs(source["clock_period_ns"] - destination["clock_period_ns"]) > 1.0e-9:
        raise ValueError("async fifo source/destination requested clock periods must match")
    _require_close_rel(
        source["die_area_um2"],
        destination["die_area_um2"],
        label="async fifo die_area_um2",
        rel_tol=1.0e-9,
    )
    _require_close_rel(
        source["instance_area_um2"],
        destination["instance_area_um2"],
        label="async fifo instance_area_um2",
        rel_tol=_FIFO_AREA_REL_TOL,
    )
    _require_close_rel(
        source["total_power_mw"],
        destination["total_power_mw"],
        label="async fifo total_power_mw",
        rel_tol=_FIFO_POWER_REL_TOL,
    )
    canonical = source if canonical_timed_domain == "source" else destination
    diagnostic = destination if canonical_timed_domain == "source" else source
    return {
        "canonical_timed_domain": canonical_timed_domain,
        "canonical_rule": f"{canonical_timed_domain}_domain_preferred_single_fifo_accounting",
        "source_view": source,
        "destination_view": destination,
        "canonical_view": canonical,
        "diagnostic_view": diagnostic,
        "area_consistency_rel_tol": _FIFO_AREA_REL_TOL,
        "power_consistency_rel_tol": _FIFO_POWER_REL_TOL,
    }


def _validate_functional_probe(payload: JsonDict) -> JsonDict:
    if _string(payload.get("model"), "functional probe model") != _EXPECTED_FUNCTIONAL_MODEL:
        raise ValueError("functional probe has an unexpected model")
    if payload.get("passed") is not True:
        raise ValueError("functional probe must have passed")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("functional probe requires summary")
    return {
        "service_period_ns": _finite_float(payload.get("service_period_ns"), "functional probe service_period_ns", positive=True),
        "temporal_period_ns": _finite_float(payload.get("temporal_period_ns"), "functional probe temporal_period_ns", positive=True),
        "service_cycles": _int(summary.get("service_cycles"), "functional probe summary.service_cycles", positive=True),
        "temporal_cycles": _int(summary.get("temporal_cycles"), "functional probe summary.temporal_cycles", positive=True),
        "finalizer_cycles": _int(summary.get("finalizer_cycles"), "functional probe summary.finalizer_cycles", positive=True),
        "cdc_accepted": _int(summary.get("cdc_accepted"), "functional probe summary.cdc_accepted", positive=True),
        "cdc_emitted": _int(summary.get("cdc_emitted"), "functional probe summary.cdc_emitted", positive=True),
        "finalizer_completed": _int(
            summary.get("finalizer_completed"),
            "functional probe summary.finalizer_completed",
            positive=True,
        ),
    }


def build_report(
    *,
    service_activity_power_json: Path,
    temporal_metrics_csv: Path,
    temporal_design: str,
    temporal_clock_period_ns: float,
    temporal_config_json: Path,
    temporal_macro_manifest_json: Path,
    async_fifo_source_metrics_csv: Path,
    async_fifo_source_design: str,
    async_fifo_source_clock_period_ns: float,
    async_fifo_source_config_json: Path,
    async_fifo_source_macro_manifest_json: Path,
    async_fifo_destination_metrics_csv: Path,
    async_fifo_destination_design: str,
    async_fifo_destination_clock_period_ns: float,
    async_fifo_destination_config_json: Path,
    async_fifo_destination_macro_manifest_json: Path,
    fifo_canonical_timed_domain: str = "source",
    functional_probe_json: Path,
    csv_out: Path | None = None,
) -> JsonDict:
    service_path = service_activity_power_json.resolve()
    temporal_metrics_path = temporal_metrics_csv.resolve()
    temporal_config_path = temporal_config_json.resolve()
    temporal_macro_manifest_path = temporal_macro_manifest_json.resolve()
    fifo_source_metrics_path = async_fifo_source_metrics_csv.resolve()
    fifo_source_config_path = async_fifo_source_config_json.resolve()
    fifo_source_macro_manifest_path = async_fifo_source_macro_manifest_json.resolve()
    fifo_destination_metrics_path = async_fifo_destination_metrics_csv.resolve()
    fifo_destination_config_path = async_fifo_destination_config_json.resolve()
    fifo_destination_macro_manifest_path = async_fifo_destination_macro_manifest_json.resolve()
    probe_path = functional_probe_json.resolve()

    service_payload = _load_json(service_path)
    probe_payload = _load_json(probe_path)

    service = _validate_service_anchor(service_payload)
    temporal = _validate_temporal_measurement(
        metrics_csv=temporal_metrics_path,
        design=temporal_design,
        requested_clock_period_ns=temporal_clock_period_ns,
        config_json=temporal_config_path,
        macro_manifest_json=temporal_macro_manifest_path,
    )
    fifo = _validate_fifo_pair(
        source_metrics_csv=fifo_source_metrics_path,
        source_design=async_fifo_source_design,
        source_clock_period_ns=async_fifo_source_clock_period_ns,
        source_config_json=fifo_source_config_path,
        source_macro_manifest_json=fifo_source_macro_manifest_path,
        destination_metrics_csv=fifo_destination_metrics_path,
        destination_design=async_fifo_destination_design,
        destination_clock_period_ns=async_fifo_destination_clock_period_ns,
        destination_config_json=fifo_destination_config_path,
        destination_macro_manifest_json=fifo_destination_macro_manifest_path,
        canonical_timed_domain=fifo_canonical_timed_domain,
    )
    probe = _validate_functional_probe(probe_payload)

    service_domain_period_ns = service["clock_period_ns"]
    temporal_domain_period_ns = temporal["clock_period_ns"]
    service_domain_period_ns = max(service_domain_period_ns, fifo["source_view"]["clock_period_ns"])
    temporal_domain_period_ns = max(temporal_domain_period_ns, fifo["destination_view"]["clock_period_ns"])

    temporal_domain_cycles = probe["temporal_cycles"] + probe["finalizer_cycles"]
    service_domain_time_ns = round(probe["service_cycles"] * service_domain_period_ns, 6)
    temporal_domain_time_ns = round(temporal_domain_cycles * temporal_domain_period_ns, 6)
    overlap_lower_bound_ns = round(max(service_domain_time_ns, temporal_domain_time_ns), 6)
    serial_upper_bound_ns = round(service_domain_time_ns + temporal_domain_time_ns, 6)
    overlap_lower_bound_us = round(overlap_lower_bound_ns / 1000.0, 9)
    serial_upper_bound_us = round(serial_upper_bound_ns / 1000.0, 9)
    throughput_upper_bound_per_s = round(1_000_000.0 / overlap_lower_bound_us, 12)
    throughput_lower_bound_per_s = round(1_000_000.0 / serial_upper_bound_us, 12)

    composed_instance_area_um2 = round(
        service["instance_area_um2"] + temporal["instance_area_um2"] + fifo["canonical_view"]["instance_area_um2"],
        6,
    )
    generic_composed_total_power_mw = round(
        service["generic_total_power_mw"] + temporal["total_power_mw"] + fifo["canonical_view"]["total_power_mw"],
        12,
    )
    energy_status = "bounded_provisional_activity_plus_openroad_physical_power_not_exact_token_energy"
    candidate_id = (
        "exact_partial_service_c1_"
        f"{fifo['canonical_timed_domain']}_fifo_"
        f"{temporal['design'].rsplit('_', 1)[-1]}"
    )

    row = {
        "candidate_id": candidate_id,
        "service_case_id": service["case_id"],
        "fifo_timed_domain": fifo["canonical_timed_domain"],
        "fifo_canonical_rule": fifo["canonical_rule"],
        "energy_status": energy_status,
        "service_domain_period_ns": service_domain_period_ns,
        "temporal_domain_period_ns": temporal_domain_period_ns,
        "service_cycles": probe["service_cycles"],
        "temporal_cycles": probe["temporal_cycles"],
        "finalizer_cycles": probe["finalizer_cycles"],
        "service_domain_time_ns": service_domain_time_ns,
        "temporal_domain_time_ns": temporal_domain_time_ns,
        "overlap_lower_bound_ns": overlap_lower_bound_ns,
        "serial_upper_bound_ns": serial_upper_bound_ns,
        "overlap_lower_bound_us": overlap_lower_bound_us,
        "serial_upper_bound_us": serial_upper_bound_us,
        "throughput_upper_bound_per_s": throughput_upper_bound_per_s,
        "throughput_lower_bound_per_s": throughput_lower_bound_per_s,
        "service_instance_area_um2": service["instance_area_um2"],
        "temporal_instance_area_um2": temporal["instance_area_um2"],
        "fifo_instance_area_um2": fifo["canonical_view"]["instance_area_um2"],
        "composed_instance_area_um2": composed_instance_area_um2,
        "service_generic_total_power_mw": service["generic_total_power_mw"],
        "temporal_generic_total_power_mw": temporal["total_power_mw"],
        "fifo_generic_total_power_mw": fifo["canonical_view"]["total_power_mw"],
        "generic_composed_total_power_mw": generic_composed_total_power_mw,
        "service_activity_window_power_mw": round(service["activity_backed_window"]["power_total_w"] * 1000.0, 12),
        "service_activity_window_dynamic_power_mw": round(
            service["activity_backed_window"]["power_dynamic_w"] * 1000.0, 12
        ),
        "service_activity_window_leakage_power_mw": round(
            service["activity_backed_window"]["power_leakage_w"] * 1000.0, 12
        ),
        "service_activity_window_energy_j": service["activity_backed_window"]["energy_total_j"],
        "service_activity_window_cycle_count": service["activity_backed_window"]["cycle_count"],
        "service_design": service["design"],
        "temporal_design": temporal["design"],
        "fifo_canonical_design": fifo["canonical_view"]["design"],
        "fifo_source_design": fifo["source_view"]["design"],
        "fifo_destination_design": fifo["destination_view"]["design"],
        "service_source_item_id": service["source_item_id"],
        "temporal_proposal_id": (
            temporal["proposal_ref"]["proposal_id"] if temporal["proposal_ref"] else _EXPECTED_TEMPORAL_PROPOSAL_ID
        ),
        "fifo_proposal_id": (
            fifo["canonical_view"]["proposal_ref"]["proposal_id"]
            if fifo["canonical_view"]["proposal_ref"]
            else _EXPECTED_FIFO_PROPOSAL_ID
        ),
    }

    report = {
        "model": _MODEL,
        "decision": _DECISION,
        "candidate_id": candidate_id,
        "inputs": {
            "service_activity_power_json": _portable_path(service_path),
            "temporal_metrics_csv": _portable_path(temporal_metrics_path),
            "temporal_design": temporal_design,
            "temporal_clock_period_ns": temporal_clock_period_ns,
            "temporal_config_json": _portable_path(temporal_config_path),
            "temporal_macro_manifest_json": _portable_path(temporal_macro_manifest_path),
            "async_fifo_source_metrics_csv": _portable_path(fifo_source_metrics_path),
            "async_fifo_source_design": async_fifo_source_design,
            "async_fifo_source_clock_period_ns": async_fifo_source_clock_period_ns,
            "async_fifo_source_config_json": _portable_path(fifo_source_config_path),
            "async_fifo_source_macro_manifest_json": _portable_path(fifo_source_macro_manifest_path),
            "async_fifo_destination_metrics_csv": _portable_path(fifo_destination_metrics_path),
            "async_fifo_destination_design": async_fifo_destination_design,
            "async_fifo_destination_clock_period_ns": async_fifo_destination_clock_period_ns,
            "async_fifo_destination_config_json": _portable_path(fifo_destination_config_path),
            "async_fifo_destination_macro_manifest_json": _portable_path(fifo_destination_macro_manifest_path),
            "fifo_canonical_timed_domain": fifo_canonical_timed_domain,
            "functional_probe_json": _portable_path(probe_path),
        },
        "input_hashes": {
            "service_activity_power_json": {
                "file_sha256": _sha256_file(service_path),
                "canonical_json_sha256": _canonical_json_sha256(service_payload),
            },
            "temporal_metrics_csv": {
                "file_sha256": _sha256_file(temporal_metrics_path),
                "selected_row_sha256": temporal["selected_row_sha256"],
            },
            "temporal_config_json": {
                "file_sha256": _sha256_file(temporal_config_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(temporal_config_path)),
            },
            "temporal_macro_manifest_json": {
                "file_sha256": _sha256_file(temporal_macro_manifest_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(temporal_macro_manifest_path)),
            },
            "async_fifo_source_metrics_csv": {
                "file_sha256": _sha256_file(fifo_source_metrics_path),
                "selected_row_sha256": fifo["source_view"]["selected_row_sha256"],
            },
            "async_fifo_source_config_json": {
                "file_sha256": _sha256_file(fifo_source_config_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(fifo_source_config_path)),
            },
            "async_fifo_source_macro_manifest_json": {
                "file_sha256": _sha256_file(fifo_source_macro_manifest_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(fifo_source_macro_manifest_path)),
            },
            "async_fifo_destination_metrics_csv": {
                "file_sha256": _sha256_file(fifo_destination_metrics_path),
                "selected_row_sha256": fifo["destination_view"]["selected_row_sha256"],
            },
            "async_fifo_destination_config_json": {
                "file_sha256": _sha256_file(fifo_destination_config_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(fifo_destination_config_path)),
            },
            "async_fifo_destination_macro_manifest_json": {
                "file_sha256": _sha256_file(fifo_destination_macro_manifest_path),
                "canonical_json_sha256": _canonical_json_sha256(_load_json(fifo_destination_macro_manifest_path)),
            },
            "functional_probe_json": {
                "file_sha256": _sha256_file(probe_path),
                "canonical_json_sha256": _canonical_json_sha256(probe_payload),
            },
        },
        "normalized_measurements": {
            "service_anchor": service,
            "temporal_island": temporal,
            "async_fifo_pair": fifo,
        },
        "timing_bounds": {
            "service_domain": {
                "period_ns": service_domain_period_ns,
                "cycles": probe["service_cycles"],
                "time_ns": service_domain_time_ns,
                "clock_sources": ["service_activity_anchor"]
                + ["async_fifo_source_domain"],
                "activity_window_cycle_count_not_assumed_equal": service["activity_contract_cycle_count"],
            },
            "temporal_domain": {
                "period_ns": temporal_domain_period_ns,
                "cycles": temporal_domain_cycles,
                "time_ns": temporal_domain_time_ns,
                "components": {
                    "temporal_cycles": probe["temporal_cycles"],
                    "finalizer_cycles": probe["finalizer_cycles"],
                },
                "clock_sources": ["temporal_finalizer_physical_row"]
                + ["async_fifo_destination_domain"],
            },
            "overlap_lower_bound_ns": overlap_lower_bound_ns,
            "serial_upper_bound_ns": serial_upper_bound_ns,
            "overlap_lower_bound_us": overlap_lower_bound_us,
            "serial_upper_bound_us": serial_upper_bound_us,
            "throughput_upper_bound_per_s": throughput_upper_bound_per_s,
            "throughput_lower_bound_per_s": throughput_lower_bound_per_s,
            "latency_contract": {
                "derived_from_functional_cycles_and_domain_periods": True,
                "openroad_critical_paths_not_used_as_cdc_latency": True,
                "service_activity_window_cycles_not_assumed_equal_to_functional_service_cycles": True,
                "combined_latency_not_derived_from_activity_window_cycles": True,
            },
        },
        "composed_physical": {
            "instance_area_um2": composed_instance_area_um2,
            "instance_area_mm2": round(composed_instance_area_um2 / 1.0e6, 9),
            "generic_composed_total_power_mw": generic_composed_total_power_mw,
            "service_activity_window_power_mw": round(service["activity_backed_window"]["power_total_w"] * 1000.0, 12),
            "service_activity_window_energy_j": service["activity_backed_window"]["energy_total_j"],
            "power_provenance": {
                "service_generic_total_power_mw": "generic_openroad_routed_ppa_not_activity_backed",
                "service_activity_window_power_mw": "activity_backed_service_window_power_from_component_service_window_energy",
                "temporal_generic_total_power_mw": "openroad_physical_estimate_only_not_activity_backed",
                "async_fifo_generic_total_power_mw": (
                    "openroad_physical_estimate_only_not_activity_backed_counted_once_via_canonical_fifo_view"
                ),
                "generic_composed_total_power_mw": "homogeneous_generic_openroad_power_sum_only",
            },
            "composition_contract": {
                "service_instance_area_added_once": True,
                "temporal_instance_area_added_once": True,
                "fifo_instance_area_added_once": True,
                "die_area_added": False,
                "raw_macro_area_added": False,
                "both_fifo_domain_views_consumed_for_validation": True,
                "both_fifo_domain_views_added": False,
                "fifo_canonical_rule": fifo["canonical_rule"],
                "service_activity_window_power_summed_with_generic_power": False,
            },
            "ignored_measurements": {
                "service_die_area_um2": service["die_area_um2"],
                "temporal_die_area_um2": temporal["die_area_um2"],
                "temporal_raw_macro_area_um2": temporal["raw_macro_area_um2"],
                "fifo_source_die_area_um2": fifo["source_view"]["die_area_um2"],
                "fifo_destination_die_area_um2": fifo["destination_view"]["die_area_um2"],
            },
            "fifo_diagnostics": {
                "source_view": fifo["source_view"],
                "destination_view": fifo["destination_view"],
                "canonical_view": fifo["canonical_view"],
                "diagnostic_view": fifo["diagnostic_view"],
            },
        },
        "energy_contract": {
            "status": energy_status,
            "exact_token_energy_claimed": False,
            "reason": (
                "The service c1 anchor carries both generic OpenROAD PPA power and a separate activity-backed "
                "service-window power measurement. The temporal/finalizer and FIFO rows carry only standalone OpenROAD "
                "physical power estimates. The report therefore preserves separate power views and remains a "
                "bounded/provisional energy input rather than an exact token-energy ranking."
            ),
            "exact_total_token_energy_from_composed_components": False,
            "service_activity_window_cycles_not_proven_same_as_functional_probe_service_cycles": True,
        },
        "functional_contract": probe,
        "rows": [row],
        "remaining_abstractions": [
            "This report is an additive physical normalization of independently measured service, temporal/finalizer, and one FIFO-domain row; it is not a routed whole-top signoff result.",
            "CDC latency remains bounded by functional overlap/serial timing from the finalized exact-partial probe rather than by an end-to-end routed dual-clock top.",
            "Temporal/finalizer and FIFO power remain standalone OpenROAD physical estimates; exact token-energy ranking requires composed activity-backed evidence.",
            "The service activity-window cycle count and the finalized CDC probe service cycles are preserved separately and not assumed to be the same workload without an explicit proof.",
        ],
    }

    if csv_out is not None:
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        with csv_out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            writer.writerow({field: row[field] for field in _CSV_FIELDS})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-activity-power-json", type=Path, required=True)
    parser.add_argument("--temporal-metrics-csv", type=Path, required=True)
    parser.add_argument("--temporal-design", required=True)
    parser.add_argument("--temporal-clock-period-ns", type=float, required=True)
    parser.add_argument("--temporal-config-json", type=Path, required=True)
    parser.add_argument("--temporal-macro-manifest-json", type=Path, required=True)
    parser.add_argument("--async-fifo-source-metrics-csv", type=Path, required=True)
    parser.add_argument("--async-fifo-source-design", required=True)
    parser.add_argument("--async-fifo-source-clock-period-ns", type=float, required=True)
    parser.add_argument("--async-fifo-source-config-json", type=Path, required=True)
    parser.add_argument("--async-fifo-source-macro-manifest-json", type=Path, required=True)
    parser.add_argument("--async-fifo-destination-metrics-csv", type=Path, required=True)
    parser.add_argument("--async-fifo-destination-design", required=True)
    parser.add_argument("--async-fifo-destination-clock-period-ns", type=float, required=True)
    parser.add_argument("--async-fifo-destination-config-json", type=Path, required=True)
    parser.add_argument("--async-fifo-destination-macro-manifest-json", type=Path, required=True)
    parser.add_argument(
        "--fifo-canonical-timed-domain",
        choices=("source", "destination"),
        default="source",
    )
    parser.add_argument("--functional-probe-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    args = parser.parse_args(argv)

    report = build_report(
        service_activity_power_json=args.service_activity_power_json,
        temporal_metrics_csv=args.temporal_metrics_csv,
        temporal_design=args.temporal_design,
        temporal_clock_period_ns=args.temporal_clock_period_ns,
        temporal_config_json=args.temporal_config_json,
        temporal_macro_manifest_json=args.temporal_macro_manifest_json,
        async_fifo_source_metrics_csv=args.async_fifo_source_metrics_csv,
        async_fifo_source_design=args.async_fifo_source_design,
        async_fifo_source_clock_period_ns=args.async_fifo_source_clock_period_ns,
        async_fifo_source_config_json=args.async_fifo_source_config_json,
        async_fifo_source_macro_manifest_json=args.async_fifo_source_macro_manifest_json,
        async_fifo_destination_metrics_csv=args.async_fifo_destination_metrics_csv,
        async_fifo_destination_design=args.async_fifo_destination_design,
        async_fifo_destination_clock_period_ns=args.async_fifo_destination_clock_period_ns,
        async_fifo_destination_config_json=args.async_fifo_destination_config_json,
        async_fifo_destination_macro_manifest_json=args.async_fifo_destination_macro_manifest_json,
        fifo_canonical_timed_domain=args.fifo_canonical_timed_domain,
        functional_probe_json=args.functional_probe_json,
        csv_out=args.csv_out,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
