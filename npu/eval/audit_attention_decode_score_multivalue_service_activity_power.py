#!/usr/bin/env python3
"""Audit strict c1 routed power for the multivalue integrated service."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from npu.eval.extract_fakeram_vcd_activity import (
    extract_multivalue_service_fakeram_vcd_activity,
)
from npu.eval.extract_sequential_register_vcd_activity import (
    extract_sequential_register_vcd_activity,
)
from npu.eval.generate_attention_decode_score_multivalue_service_activity import (
    _OUTPUT_MACRO_MANIFEST_NAME,
    _OUTPUT_MANIFEST_NAME,
    _OUTPUT_SERVICE_MANIFEST_NAME,
    _OUTPUT_VCD_NAME,
    generate_activity,
)
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import (
    _workload_contract as _expected_workload_contract,
    _workload_expected_counts,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report

JsonDict = dict[str, Any]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVALUATOR_LOCAL_PATH_PLACEHOLDER = "<evaluator-local-path>"
_ABSOLUTE_PATH_RE = re.compile(r"/[^\s\"'`<>|&(){}\[\]]+")
_MAX_FAILURE_DETAIL_LINES = 16
_MAX_FAILURE_DETAIL_LINE_CHARS = 400
_MAX_FAILURE_DETAIL_BYTES = 4096

_MODEL = "decoder_attention_decode_score_multivalue_service_activity_power_v1"
_SCOPE = "tb/dut"
_EXPECTED_PLATFORM = "nangate45"
_SCORE_PINS_PER_MACRO = 11 + 39 + 39 + 1 + 1
_VALUE_PINS_PER_MACRO = 6 + 32 + 32 + 1 + 1
_EXPECTED_MACRO_ACTIVITY_PROFILE = "multivalue_service_c1_v1"
_POSTROUTE_MANIFEST_NAME = "attention_decode_score_multivalue_service_postroute_power_manifest.json"
_POSTROUTE_MACRO_ACTIVITY_NAME = (
    "attention_decode_score_multivalue_service_fakeram_macro_pin_vcd_activity_v1.json"
)
_POSTROUTE_SEQUENTIAL_ACTIVITY_NAME = (
    "attention_decode_score_multivalue_service_sequential_register_vcd_activity_v1.json"
)
_SCORE_ACTIVITY_RE = re.compile(
    r"^score_bank/u_group_(\d+)_slice_(\d+)/(?:addr_in\[\d+\]|wd_in\[\d+\]|w_mask_in\[\d+\]|we_in|ce_in)$"
)
_VALUE_ACTIVITY_RE = re.compile(
    r"^gen_value_macro_backend/gen_value_bank\[(\d+)\]/gen_value_lane\[(\d+)\]/u_value_mem_lane/"
    r"(?:addr_in\[\d+\]|wd_in\[\d+\]|w_mask_in\[\d+\]|we_in|ce_in)$"
)


@dataclass(frozen=True)
class _ServiceCaseContract:
    case_id: str
    cluster_count: int
    design: str
    flow_variant: str
    macro_counts: dict[str, int]
    dependency_key: str
    authoritative_ppa_key: str


_SERVICE_CASES = {
    "c1_p128_b4_rr": _ServiceCaseContract(
        case_id="c1_p128_b4_rr",
        cluster_count=1,
        design="attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr",
        flow_variant="decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
        macro_counts={"fakeram45_2048x39": 56, "fakeram45_64x32": 64},
        dependency_key="integrated_service_c1",
        authoritative_ppa_key="authoritative_composed_c1_total_ppa",
    ),
    "c2_p128_b4_rr": _ServiceCaseContract(
        case_id="c2_p128_b4_rr",
        cluster_count=2,
        design="attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
        flow_variant="decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
        macro_counts={"fakeram45_2048x39": 112, "fakeram45_64x32": 64},
        dependency_key="integrated_service_c2",
        authoritative_ppa_key="authoritative_composed_c2_total_ppa",
    ),
}
_CASE_ID = _SERVICE_CASES["c1_p128_b4_rr"].case_id
_EXPECTED_DESIGN = _SERVICE_CASES["c1_p128_b4_rr"].design
_REQUIRED_FLOW_VARIANT = _SERVICE_CASES["c1_p128_b4_rr"].flow_variant
_EXPECTED_MACRO_COUNTS = dict(_SERVICE_CASES["c1_p128_b4_rr"].macro_counts)


def _case_label(case_contract: _ServiceCaseContract) -> str:
    return "c1" if case_contract.case_id == "c1_p128_b4_rr" else case_contract.case_id


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
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return f"{_EVALUATOR_LOCAL_PATH_PLACEHOLDER}/{path.name}"


def _redact_path(text: str) -> str:
    token = Path(text.rstrip(".,;:!?)]}"))
    if token.is_absolute():
        return _portable_path(token)
    return text


def _sanitize_failure_line(line: str) -> str:
    return _ABSOLUTE_PATH_RE.sub(lambda match: _redact_path(match.group(0)), line)


def _collect_failure_detail(lines: list[str]) -> list[str]:
    detail = [line.strip() for line in lines if line.strip()]
    detail = [line[:_MAX_FAILURE_DETAIL_LINE_CHARS] for line in detail[-_MAX_FAILURE_DETAIL_LINES:]]
    while detail and sum(len(line) for line in detail) > _MAX_FAILURE_DETAIL_BYTES:
        detail = detail[1:]
    return detail


def _sanitized_failure(exc: Exception) -> JsonDict:
    lines = [_sanitize_failure_line(line).strip() for line in str(exc).splitlines()]
    lines = [line for line in lines if line]
    summary = lines[0][:240] if lines else f"{type(exc).__name__} failure"
    return {
        "error_type": type(exc).__name__,
        "error_summary": summary,
        "detail": _collect_failure_detail(lines),
    }


def _service_case_contract(
    *,
    case_id: str | None = None,
    cluster_count: int | None = None,
) -> _ServiceCaseContract:
    if case_id is not None:
        contract = _SERVICE_CASES.get(str(case_id).strip())
        if contract is None:
            raise ValueError(f"unsupported service activity case_id: {case_id}")
        return contract
    if cluster_count is None:
        raise ValueError("service activity case selection requires case_id or cluster_count")
    for contract in _SERVICE_CASES.values():
        if contract.cluster_count == int(cluster_count):
            return contract
    raise ValueError(f"unsupported service activity cluster_count: {cluster_count}")


def _case_from_config(config: JsonDict, *, explicit_case_id: str | None = None) -> _ServiceCaseContract:
    body = config.get("attention_decode_score_multivalue_service")
    if not isinstance(body, dict):
        raise ValueError("config requires attention_decode_score_multivalue_service object")
    contract = _service_case_contract(
        case_id=explicit_case_id,
        cluster_count=int(body.get("cluster_count", 0)),
    )
    if int(body.get("cluster_count", 0)) != contract.cluster_count:
        raise ValueError("service config cluster_count does not match the selected case")
    return contract


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
        "metrics_csv": _portable_path(metrics_csv),
        **{field: row[field] for field in fields if str(row.get(field, "")).strip()},
    }


def _select_metric(
    metrics_csv: Path,
    *,
    case_contract: _ServiceCaseContract,
    clock_period_ns: float,
) -> JsonDict:
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    matches: list[JsonDict] = []
    for row in rows:
        if str(row.get("status", "")).strip() != "ok":
            continue
        if str(row.get("design", "")).strip() != case_contract.design:
            continue
        if str(row.get("platform", "")).strip() != _EXPECTED_PLATFORM:
            continue
        params = _params(row)
        flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
        if flow_variant != case_contract.flow_variant:
            continue
        try:
            row_clock = float(params.get("CLOCK_PERIOD", 0.0))
            critical_path_ns = float(row.get("critical_path_ns") or math.inf)
        except (TypeError, ValueError) as exc:
            raise ValueError("selected c1 row has invalid CLOCK_PERIOD or critical_path_ns") from exc
        if abs(row_clock - clock_period_ns) > 1e-9:
            raise ValueError(
                f"selected {case_contract.case_id} row CLOCK_PERIOD mismatch: expected {clock_period_ns:g}, got {row_clock:g}"
            )
        if not math.isfinite(critical_path_ns) or critical_path_ns > clock_period_ns:
            raise ValueError(
                f"selected {case_contract.case_id} row is not timing-feasible at {clock_period_ns:g} ns"
            )
        matches.append(row)
    if not matches:
        raise ValueError(
            "expected exactly one status=ok timing-feasible row with design "
            f"{case_contract.design}, platform {_EXPECTED_PLATFORM}, and FLOW_VARIANT {case_contract.flow_variant}"
        )
    if len(matches) != 1:
        raise ValueError(
            "expected exactly one status=ok timing-feasible row with design "
            f"{case_contract.design}, platform {_EXPECTED_PLATFORM}, and FLOW_VARIANT "
            f"{case_contract.flow_variant}, found {len(matches)}"
        )
    return matches[0]


def _select_c1_metric(metrics_csv: Path, *, clock_period_ns: float) -> JsonDict:
    return _select_metric(
        metrics_csv,
        case_contract=_SERVICE_CASES["c1_p128_b4_rr"],
        clock_period_ns=clock_period_ns,
    )


def _require_string_hash(payload: JsonDict, key: str, label: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"{label} missing {key}")
    return value


def _validate_cluster_equivalence(payload: JsonDict) -> JsonDict:
    if payload.get("equivalence_pass") is not True:
        raise ValueError("merged cluster equivalence did not pass")
    decision = str(payload.get("decision") or "").strip()
    if decision != "decode_score_multivalue_cluster_equivalence_pass":
        raise ValueError(
            "merged cluster equivalence decision mismatch: "
            f"expected decode_score_multivalue_cluster_equivalence_pass, got {decision or '<missing>'}"
        )
    return {
        "equivalence_pass": True,
        "decision": decision,
        "score_tensor_hash": _require_string_hash(payload, "score_tensor_hash", "merged cluster equivalence"),
        "final_tensor_hash": _require_string_hash(payload, "final_tensor_hash", "merged cluster equivalence"),
        "semantic_profile": str(payload.get("semantic_profile") or "").strip() or None,
    }


def _validate_integrated_service(
    payload: JsonDict,
    *,
    case_contract: _ServiceCaseContract = _SERVICE_CASES["c1_p128_b4_rr"],
) -> JsonDict:
    expected_workload = _expected_workload_contract()
    expected_counts = _workload_expected_counts(expected_workload)
    if payload.get("workload_contract") != expected_workload:
        raise ValueError("integrated-service workload contract mismatch")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("integrated-service report must contain cases[]")
    selected = [
        case
        for case in cases
        if isinstance(case, dict) and str(case.get("case_id") or "").strip() == case_contract.case_id
    ]
    if len(selected) != 1:
        raise ValueError(f"integrated-service report must contain exactly one {case_contract.case_id} case")
    case = selected[0]
    if case.get("decision") != "pass":
        raise ValueError(f"integrated-service {case_contract.case_id} case did not pass")
    config = case.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"integrated-service {case_contract.case_id} config is missing")
    expected_config = {
        "cluster_count": case_contract.cluster_count,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(
                f"integrated-service {case_contract.case_id} config mismatch for {key}: expected {expected!r}, got {config.get(key)!r}"
            )
    integrated = case.get("integrated_service")
    if not isinstance(integrated, dict):
        raise ValueError(f"integrated-service {case_contract.case_id} section is missing")
    if integrated.get("exact_match") is not True:
        raise ValueError(f"integrated-service {case_contract.case_id} exact_result_match gate failed")
    for key in ("no_protocol_errors", "no_drop_duplicate_deadlock_timeout", "cycle_bound_ok"):
        if integrated.get(key) is not True:
            raise ValueError(f"integrated-service {case_contract.case_id} {key} gate failed")
    counters = integrated.get("counters")
    if not isinstance(counters, dict):
        raise ValueError(f"integrated-service {case_contract.case_id} counters missing")
    required_counter_keys = {
        "request_injection_stall_cycles",
        "arbitration_contention_cycles",
        "bank_conflict_count",
        "response_block_cycles",
        "shared_result",
        "max_occupancy",
    }
    missing = required_counter_keys - set(counters)
    if missing:
        raise ValueError(
            f"integrated-service {case_contract.case_id} counters incomplete: " + ", ".join(sorted(missing))
        )
    if int(integrated.get("request_count", 0)) != int(expected_counts["request_count"]):
        raise ValueError(f"integrated-service {case_contract.case_id} request_count mismatch")
    if int(integrated.get("wide_response_count", 0)) != int(expected_counts["wide_response_count"]):
        raise ValueError(f"integrated-service {case_contract.case_id} wide_response_count mismatch")
    if int(integrated.get("result_count", 0)) != int(expected_counts["result_count"]):
        raise ValueError(f"integrated-service {case_contract.case_id} result_count mismatch")
    gates = case.get("gates")
    if not isinstance(gates, dict) or not all(
        bool(gates.get(key)) for key in ("hash_gate_ok", "protocol_gate_ok", "count_gate_ok")
    ):
        raise ValueError(f"integrated-service {case_contract.case_id} gates failed")
    egress = integrated.get("shared_result_egress")
    if not isinstance(egress, dict) or int(egress.get("documented_initiation_interval", 0)) != 1:
        raise ValueError(f"integrated-service {case_contract.case_id} shared_result_egress contract failed")
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for key in ("all_hash_gates_passed", "all_protocol_gates_passed", "all_count_gates_passed"):
            if summary.get(key) is not True:
                raise ValueError(f"integrated-service summary {key} failed")
    return {
        "case_id": case_contract.case_id,
        "config": dict(config),
        "decision": "pass",
        "exact_match": True,
        "no_protocol_errors": True,
        "no_drop_duplicate_deadlock_timeout": True,
        "cycle_bound_ok": True,
        "request_count": int(integrated["request_count"]),
        "wide_response_count": int(integrated["wide_response_count"]),
        "result_count": int(integrated["result_count"]),
        "counters": counters,
        "gates": {key: True for key in ("hash_gate_ok", "protocol_gate_ok", "count_gate_ok")},
        "shared_result_egress": egress,
        "workload_contract": expected_workload,
        "hashes": {
            "score_hash": _require_string_hash(integrated, "score_hash", f"integrated-service {case_contract.case_id}"),
            "final_hash": _require_string_hash(integrated, "final_hash", f"integrated-service {case_contract.case_id}"),
            "request_hash": _require_string_hash(integrated, "request_hash", f"integrated-service {case_contract.case_id}"),
            "wide_response_matrix_hash": _require_string_hash(
                integrated, "wide_response_matrix_hash", f"integrated-service {case_contract.case_id}"
            ),
        },
    }


def _validate_generated_activity_manifest(
    activity_manifest: JsonDict,
    activity_dir: Path,
    *,
    case_contract: _ServiceCaseContract = _SERVICE_CASES["c1_p128_b4_rr"],
) -> JsonDict:
    expected_workload = _expected_workload_contract()
    expected_counts = _workload_expected_counts(expected_workload)
    if str(activity_manifest.get("model") or "").strip() != "attention_decode_score_multivalue_service_activity_v1":
        raise ValueError("generated activity manifest model mismatch")
    if str(activity_manifest.get("case_id") or "").strip() != case_contract.case_id:
        raise ValueError("generated activity manifest case_id mismatch")
    if activity_manifest.get("workload_contract") != expected_workload:
        raise ValueError("generated activity manifest workload contract mismatch")
    if float(activity_manifest.get("clock_period_ns", 0.0)) != 10.0:
        raise ValueError("generated activity manifest clock_period_ns mismatch")
    cycle_count = int(activity_manifest.get("cycle_count", 0))
    if cycle_count <= 0:
        raise ValueError("generated activity manifest cycle_count must be positive")
    counters = activity_manifest.get("request_result_protocol_counters")
    if not isinstance(counters, dict):
        raise ValueError("generated activity manifest request_result_protocol_counters missing")
    if int(counters.get("request_count", 0)) != int(expected_counts["request_count"]):
        raise ValueError("generated activity manifest request_count mismatch")
    if int(counters.get("wide_response_count", 0)) != int(expected_counts["wide_response_count"]):
        raise ValueError("generated activity manifest wide_response_count mismatch")
    if int(counters.get("result_count", 0)) != int(expected_counts["result_count"]):
        raise ValueError("generated activity manifest result_count mismatch")
    shared = counters.get("shared")
    if not isinstance(shared, dict) or shared.get("protocol_error") is not False:
        raise ValueError("generated activity manifest shared protocol contract failed")
    bank_coverage = activity_manifest.get("value_bank_coverage")
    if not isinstance(bank_coverage, dict):
        raise ValueError("generated activity manifest value_bank_coverage missing")
    if not isinstance(bank_coverage.get("addressed_banks_over_trace"), list):
        raise ValueError("generated activity manifest addressed_banks_over_trace missing")
    if not isinstance(bank_coverage.get("inactive_banks"), list):
        raise ValueError("generated activity manifest inactive_banks missing")
    if bank_coverage.get("inactive_reason") != "three_block_reference_workload":
        raise ValueError("generated activity manifest inactive_reason mismatch")
    if case_contract.case_id == "c1_p128_b4_rr":
        if bank_coverage.get("addressed_banks_over_trace") != [0, 1, 2]:
            raise ValueError("generated activity manifest addressed_banks_over_trace mismatch")
        if bank_coverage.get("inactive_banks") != [3]:
            raise ValueError("generated activity manifest inactive_banks mismatch")
    vcd_hash = str(activity_manifest.get("hashes", {}).get("vcd_sha256") or "").strip().lower()
    if not vcd_hash:
        raise ValueError("generated activity manifest vcd_sha256 missing")
    if not (activity_dir / _OUTPUT_MANIFEST_NAME).is_file():
        raise ValueError("generated activity manifest file missing from activity_dir")
    return {
        "clock_period_ns": 10.0,
        "cycle_count": cycle_count,
        "vcd_sha256": vcd_hash,
        "generated_manifest_sha256": _sha256_file(activity_dir / _OUTPUT_MANIFEST_NAME),
        "generated_manifest_hashes": dict(activity_manifest.get("hashes") or {}),
        "bank_coverage": bank_coverage,
        "workload_contract": expected_workload,
    }


def _validate_macro_manifest_counts(
    macro_manifest: JsonDict,
    *,
    case_contract: _ServiceCaseContract = _SERVICE_CASES["c1_p128_b4_rr"],
) -> JsonDict:
    params = macro_manifest.get("manifest_params")
    if not isinstance(params, dict):
        raise ValueError("macro_manifest manifest_params missing")
    score_bank_macro_count = int(params.get("score_bank_macro_count", 0))
    value_memory_macro_count = int(params.get("value_memory_macro_count", 0))
    if score_bank_macro_count != case_contract.macro_counts["fakeram45_2048x39"]:
        raise ValueError(
            "macro_manifest score-bank macro count mismatch: expected "
            f"{case_contract.macro_counts['fakeram45_2048x39']}, got {score_bank_macro_count}"
        )
    if value_memory_macro_count != case_contract.macro_counts["fakeram45_64x32"]:
        raise ValueError(
            "macro_manifest value-memory macro count mismatch: expected "
            f"{case_contract.macro_counts['fakeram45_64x32']}, got {value_memory_macro_count}"
        )
    return {
        "fakeram45_2048x39": score_bank_macro_count,
        "fakeram45_64x32": value_memory_macro_count,
    }


def _validate_service_macro_activity_contract(
    macro_activity: JsonDict,
    *,
    macro_counts: JsonDict,
) -> JsonDict:
    pins = macro_activity.get("pins")
    if not isinstance(pins, list) or not pins:
        raise ValueError("service macro activity pins[] missing")

    score_instances: set[str] = set()
    value_instances: set[str] = set()
    score_pin_count = 0
    value_pin_count = 0
    for row in pins:
        if not isinstance(row, dict):
            raise ValueError("service macro activity pins[] must contain objects")
        full_name = str(row.get("full_name") or "").strip()
        if not full_name:
            raise ValueError("service macro activity pin full_name missing")
        score_match = _SCORE_ACTIVITY_RE.fullmatch(full_name)
        if score_match is not None:
            score_pin_count += 1
            score_instances.add(f"score_bank/u_group_{score_match.group(1)}_slice_{score_match.group(2)}")
            continue
        value_match = _VALUE_ACTIVITY_RE.fullmatch(full_name)
        if value_match is not None:
            value_pin_count += 1
            value_instances.add(
                "gen_value_macro_backend/gen_value_bank[{bank}]/gen_value_lane[{lane}]/u_value_mem_lane".format(
                    bank=value_match.group(1),
                    lane=value_match.group(2),
                )
            )
            continue
        raise ValueError(f"service macro activity contains unsupported full_name: {full_name}")

    expected_score_instance_count = int(macro_counts["fakeram45_2048x39"])
    expected_value_instance_count = int(macro_counts["fakeram45_64x32"])
    expected_score_pin_count = expected_score_instance_count * _SCORE_PINS_PER_MACRO
    expected_value_pin_count = expected_value_instance_count * _VALUE_PINS_PER_MACRO
    if len(score_instances) != expected_score_instance_count or score_pin_count != expected_score_pin_count:
        raise ValueError(
            "service macro activity score-bank structural coverage mismatch: expected "
            f"{expected_score_instance_count} instances / {expected_score_pin_count} pins, got "
            f"{len(score_instances)} instances / {score_pin_count} pins"
        )
    if len(value_instances) != expected_value_instance_count or value_pin_count != expected_value_pin_count:
        raise ValueError(
            "service macro activity value-memory structural coverage mismatch: expected "
            f"{expected_value_instance_count} instances / {expected_value_pin_count} pins, got "
            f"{len(value_instances)} instances / {value_pin_count} pins"
        )

    structural_contract = macro_activity.get("structural_macro_contract")
    if not isinstance(structural_contract, dict):
        raise ValueError("service macro activity structural_macro_contract missing")
    if str(structural_contract.get("profile") or "").strip() != _EXPECTED_MACRO_ACTIVITY_PROFILE:
        raise ValueError("service macro activity structural_macro_contract profile mismatch")
    if int(structural_contract.get("total_assignment_count", 0)) != len(pins):
        raise ValueError("service macro activity total_assignment_count mismatch")
    macro_classes = structural_contract.get("macro_classes")
    if not isinstance(macro_classes, list):
        raise ValueError("service macro activity macro_classes missing")
    by_name = {
        str(row.get("macro_name") or "").strip(): row
        for row in macro_classes
        if isinstance(row, dict) and str(row.get("macro_name") or "").strip()
    }
    expected_classes = {
        "fakeram45_2048x39": {
            "instance_scope_prefix": "score_bank",
            "instance_count": expected_score_instance_count,
            "pins_per_instance": _SCORE_PINS_PER_MACRO,
            "assignment_count": expected_score_pin_count,
        },
        "fakeram45_64x32": {
            "instance_scope_prefix": "gen_value_macro_backend",
            "instance_count": expected_value_instance_count,
            "pins_per_instance": _VALUE_PINS_PER_MACRO,
            "assignment_count": expected_value_pin_count,
        },
    }
    for macro_name, expected in expected_classes.items():
        row = by_name.get(macro_name)
        if not isinstance(row, dict):
            raise ValueError(f"service macro activity macro_classes missing {macro_name}")
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                raise ValueError(
                    f"service macro activity {macro_name} {key} mismatch: "
                    f"expected {expected_value!r}, got {row.get(key)!r}"
                )
    return {
        "profile": _EXPECTED_MACRO_ACTIVITY_PROFILE,
        "total_assignment_count": len(pins),
        "macro_classes": expected_classes,
    }


def _prepare_postroute_power_manifest(
    *,
    activity_dir: Path,
    activity_manifest: JsonDict,
    case_contract: _ServiceCaseContract,
) -> tuple[JsonDict, Path, JsonDict]:
    generated_meta = _validate_generated_activity_manifest(
        activity_manifest,
        activity_dir,
        case_contract=case_contract,
    )
    macro_counts = _validate_macro_manifest_counts(
        _load(activity_dir / _OUTPUT_MACRO_MANIFEST_NAME),
        case_contract=case_contract,
    )
    vcd_path = activity_dir / _OUTPUT_VCD_NAME
    if not vcd_path.is_file():
        raise ValueError("generated VCD missing from activity_dir")
    if _sha256_file(vcd_path) != generated_meta["vcd_sha256"]:
        raise ValueError("generated VCD hash does not match the generated activity manifest")
    if not (activity_dir / _OUTPUT_SERVICE_MANIFEST_NAME).is_file():
        raise ValueError("generated service manifest missing from activity_dir")

    macro_activity = extract_multivalue_service_fakeram_vcd_activity(
        vcd_path,
        source_vcd_sha256=generated_meta["vcd_sha256"],
        scope=_SCOPE,
    )
    macro_activity_contract = _validate_service_macro_activity_contract(
        macro_activity,
        macro_counts=macro_counts,
    )
    macro_activity_path = activity_dir / _POSTROUTE_MACRO_ACTIVITY_NAME
    macro_activity_path.write_text(
        json.dumps(macro_activity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sequential_activity = extract_sequential_register_vcd_activity(
        vcd_path,
        source_vcd_sha256=generated_meta["vcd_sha256"],
        scope=_SCOPE,
    )
    sequential_activity_path = activity_dir / _POSTROUTE_SEQUENTIAL_ACTIVITY_NAME
    sequential_activity_path.write_text(
        json.dumps(sequential_activity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    adapted_manifest = {
        "version": 1,
        "model": "attention_decode_score_multivalue_service_postroute_activity_manifest_v1",
        "clock_period_ns": activity_manifest["clock_period_ns"],
        "phases": [
            {
                "phase": "service_window",
                "vcd": _OUTPUT_VCD_NAME,
                "vcd_sha256": generated_meta["vcd_sha256"],
                "macro_activity": macro_activity_path.name,
                "macro_activity_sha256": _sha256_file(macro_activity_path),
                "sequential_register_activity": sequential_activity_path.name,
                "sequential_register_activity_sha256": _sha256_file(sequential_activity_path),
                "measured_cycles": generated_meta["cycle_count"],
                "full_context_cycles": generated_meta["cycle_count"],
                "requires_macro_activity": True,
            }
        ],
    }
    adapted_manifest_path = activity_dir / _POSTROUTE_MANIFEST_NAME
    adapted_manifest_path.write_text(
        json.dumps(adapted_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return adapted_manifest, adapted_manifest_path, {
        "generated_activity_manifest_sha256": generated_meta["generated_manifest_sha256"],
        "adapted_activity_manifest_sha256": _sha256_file(adapted_manifest_path),
        "vcd_sha256": generated_meta["vcd_sha256"],
        "cycle_count": generated_meta["cycle_count"],
        "macro_counts": macro_counts,
        "macro_activity_contract": macro_activity_contract,
        "bank_coverage": generated_meta["bank_coverage"],
    }


def _finite_positive(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite positive number") from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{label} must be a finite positive number")
    return numeric


def _strict_service_window_measurement(
    *,
    activity_power: JsonDict,
    manifest_sha256: str,
    expected_vcd_sha256: str,
    expected_clock_period_ns: float,
    expected_cycle_count: int,
    expected_macro_assignment_count: int,
) -> JsonDict:
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("postroute power promotion_gate_pass failed")
    if activity_power.get("status") != "activity_backed":
        raise ValueError("postroute power status is not activity_backed")
    if abs(float(activity_power.get("clock_period_ns", 0.0)) - expected_clock_period_ns) > 1e-9:
        raise ValueError("postroute power clock_period_ns mismatch")
    if str(activity_power.get("source_activity_manifest_sha256") or "").strip().lower() != manifest_sha256:
        raise ValueError("postroute power source_activity_manifest_sha256 mismatch")
    phases = activity_power.get("phases")
    if not isinstance(phases, list) or len(phases) != 1 or not isinstance(phases[0], dict):
        raise ValueError("postroute power must contain exactly one service_window phase")
    phase = phases[0]
    if str(phase.get("phase") or "").strip() != "service_window":
        raise ValueError("postroute power phase name mismatch")
    if str(phase.get("vcd_sha256") or "").strip().lower() != expected_vcd_sha256:
        raise ValueError("postroute power VCD hash mismatch")
    if int(phase.get("measured_cycles", 0)) != expected_cycle_count:
        raise ValueError("postroute power measured_cycles mismatch")
    if int(phase.get("full_context_cycles", 0)) != expected_cycle_count:
        raise ValueError("postroute power full_context_cycles mismatch")
    if phase.get("annotation_gate_pass") is not True:
        raise ValueError("postroute power aggregate annotation gate failed")
    if phase.get("macro_activity_gate_pass") is not True:
        raise ValueError("postroute power macro activity gate failed")
    if phase.get("structural_macro_activity_gate_pass") is not True:
        raise ValueError("postroute power structural macro activity gate failed")
    if phase.get("sequential_register_activity_gate_pass") is not True:
        raise ValueError("postroute power sequential register coverage gate failed")
    if phase.get("clock_period_gate_pass") is not True:
        raise ValueError("postroute power clock period gate failed")
    if int(phase.get("macro_activity_assignment_count", 0)) != expected_macro_assignment_count:
        raise ValueError("postroute power macro_activity_assignment_count mismatch")
    power = phase.get("power")
    if not isinstance(power, dict):
        raise ValueError("postroute power phase power section missing")
    internal_w = _finite_positive(power.get("internal_w"), "internal_w")
    switching_w = _finite_positive(power.get("switching_w"), "switching_w")
    leakage_w = _finite_positive(power.get("leakage_w"), "leakage_w")
    total_w = _finite_positive(power.get("total_w"), "total_w")
    if abs((internal_w + switching_w + leakage_w) - total_w) > 1e-9:
        raise ValueError("postroute power total_w does not match internal+switching+leakage")
    service_window_s = expected_cycle_count * expected_clock_period_ns * 1e-9
    dynamic_energy_j = (internal_w + switching_w) * service_window_s
    leakage_energy_j = leakage_w * service_window_s
    total_energy_j = dynamic_energy_j + leakage_energy_j
    return {
        "label": "component_service_window_energy",
        "is_total_token_energy": False,
        "cycle_count": expected_cycle_count,
        "duration_s": service_window_s,
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
            "dynamic_plus_leakage": total_energy_j,
        },
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    best = payload.get("best") if isinstance(payload.get("best"), dict) else {}
    service_window = (
        best.get("component_service_window_energy")
        if isinstance(best.get("component_service_window_energy"), dict)
        else {}
    )
    composed_ppa = (
        best.get("authoritative_composed_total_ppa")
        if isinstance(best.get("authoritative_composed_total_ppa"), dict)
        else {}
    )
    selection_contract = payload.get("selection_contract", {})
    case_id = selection_contract.get("case_id", "service_case")
    lines = [
        f"# Strict {case_id} routed service power audit",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promotion_gate_pass: `{payload['promotion_gate_pass']}`",
        f"- required_flow_variant: `{selection_contract.get('required_flow_variant')}`",
        f"- bank3 dynamic inactivity: `{payload['bank3_dynamic_inactivity']['inactive_banks']}`",
        f"- bank3 note: {payload['bank3_dynamic_inactivity']['statement']}",
        "",
        "| status | path ns | total power mW | service-window dynamic J | service-window leakage J | service-window total J |",
        "|---|---:|---:|---:|---:|---:|",
        "| {status} | {path_ns} | {total_power_mw} | {dynamic} | {leakage} | {total} |".format(
            status=best.get("status"),
            path_ns=composed_ppa.get("critical_path_ns"),
            total_power_mw=composed_ppa.get("total_power_mw"),
            dynamic=service_window.get("energy_j", {}).get("dynamic"),
            leakage=service_window.get("energy_j", {}).get("leakage"),
            total=service_window.get("energy_j", {}).get("dynamic_plus_leakage"),
        ),
        "",
        "## Macro Contract",
        "",
        f"- `fakeram45_2048x39`: `{payload['macro_manifest_contract']['counts']['fakeram45_2048x39']}`",
        f"- `fakeram45_64x32`: `{payload['macro_manifest_contract']['counts']['fakeram45_64x32']}`",
    ]
    if payload["promotion_gate_pass"] is not True:
        failure = payload["candidates"][0].get("failure")
        if isinstance(failure, dict):
            lines.extend(
                [
                    "",
                    "## Failure",
                    "",
                    f"- type: `{failure.get('error_type')}`",
                    f"- summary: {failure.get('error_summary')}",
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    config: Path,
    c1_metrics_csv: Path | None = None,
    metrics_csv: Path | None = None,
    equivalence_json: Path,
    integrated_service_json: Path,
    orfs_design_config: Path,
    clock_period_ns: float,
    activity_dir: Path,
    min_sequential_register_activity_coverage: float = 0.95,
    case_id: str | None = None,
) -> JsonDict:
    if abs(clock_period_ns - 10.0) > 1e-9:
        raise ValueError("strict routed service power audit requires a 10 ns clock")
    config_payload = _load(config)
    case_contract = _case_from_config(config_payload, explicit_case_id=case_id)
    selected_metrics_csv = metrics_csv or c1_metrics_csv
    if selected_metrics_csv is None:
        raise ValueError("metrics_csv is required")
    cluster_equivalence = _validate_cluster_equivalence(_load(equivalence_json))
    integrated_service = _validate_integrated_service(
        _load(integrated_service_json),
        case_contract=case_contract,
    )
    metric = _select_metric(
        selected_metrics_csv,
        case_contract=case_contract,
        clock_period_ns=clock_period_ns,
    )
    activity_dir.mkdir(parents=True, exist_ok=True)
    activity_manifest = generate_activity(
        config_payload,
        activity_dir,
        clock_period_ns=clock_period_ns,
        case_id=case_contract.case_id,
    )
    adapted_manifest, adapted_manifest_path, activity_meta = _prepare_postroute_power_manifest(
        activity_dir=activity_dir,
        activity_manifest=activity_manifest,
        case_contract=case_contract,
    )
    if activity_meta["workload_contract"] != integrated_service["workload_contract"]:
        raise ValueError(
            f"generated activity workload contract does not match integrated-service {case_contract.case_id}"
        )
    generated_hashes = activity_meta["generated_manifest_hashes"]
    integrated_hashes = integrated_service["hashes"]
    for generated_key, integrated_key in (
        ("score_hash", "score_hash"),
        ("final_hash", "final_hash"),
        ("request_hash", "request_hash"),
        ("wide_response_matrix_hash", "wide_response_matrix_hash"),
    ):
        if str(generated_hashes.get(generated_key) or "").strip() != str(integrated_hashes[integrated_key]).strip():
            raise ValueError(
                f"generated activity {generated_key} does not match integrated-service {_case_label(case_contract)} {integrated_key}"
            )
    candidate: JsonDict = {
        "candidate_id": f"multivalue_service_activity_{case_contract.flow_variant}",
        "flow_variant": case_contract.flow_variant,
        "ppa_metric": _metric_provenance(metric, selected_metrics_csv),
    }
    try:
        activity_power = build_power_report(
            manifest=adapted_manifest,
            manifest_path=adapted_manifest_path,
            design_config=orfs_design_config,
            flow_variant=case_contract.flow_variant,
            scope=_SCOPE,
            min_vcd_coverage=0.05,
            min_vcd_pins=32,
            min_sequential_register_activity_coverage=min_sequential_register_activity_coverage,
            min_macro_active_coverage=0.01,
            min_macro_active_pins=16,
            timeout_seconds=1800,
        )
    except Exception as exc:
        candidate["status"] = "measurement_failed"
        candidate["promotion_gate_pass"] = False
        candidate["failure"] = _sanitized_failure(exc)
    else:
        candidate["activity_power"] = activity_power
        try:
            service_window_energy = _strict_service_window_measurement(
                activity_power=activity_power,
                manifest_sha256=activity_meta["adapted_activity_manifest_sha256"],
                expected_vcd_sha256=activity_meta["vcd_sha256"],
                expected_clock_period_ns=clock_period_ns,
                expected_cycle_count=int(activity_meta["cycle_count"]),
                expected_macro_assignment_count=int(
                    activity_meta["macro_activity_contract"]["total_assignment_count"]
                ),
            )
        except Exception as exc:
            candidate["status"] = "rejected_gate"
            candidate["promotion_gate_pass"] = False
            candidate["failure"] = _sanitized_failure(exc)
        else:
            candidate["status"] = "activity_backed"
            candidate["promotion_gate_pass"] = True
            candidate["component_service_window_energy"] = service_window_energy
            authoritative_ppa = {
                "critical_path_ns": float(metric["critical_path_ns"]),
                "instance_area_um2": float(metric.get("instance_area_um2") or 0.0),
                "die_area": float(metric.get("die_area") or 0.0),
                "total_power_mw": float(metric.get("total_power_mw") or 0.0),
            }
            candidate["authoritative_composed_total_ppa"] = authoritative_ppa
            candidate[case_contract.authoritative_ppa_key] = dict(authoritative_ppa)
    best = candidate if candidate.get("status") == "activity_backed" else None
    inactive_banks = activity_meta["bank_coverage"]["inactive_banks"]
    if case_contract.case_id == "c1_p128_b4_rr":
        inactivity_statement = (
            "No artificial activity was injected. Bank3 may remain dynamically inactive in this exact c1 workload; "
            "it is not required to toggle, while leakage remains part of routed power."
        )
    else:
        inactivity_statement = (
            "No artificial activity was injected. Banks "
            f"{inactive_banks} may remain dynamically inactive in this exact {case_contract.case_id} workload; "
            "they are not required to toggle, while leakage remains part of routed power."
        )
    return {
        "version": 1,
        "model": _MODEL,
        "decision": (
            "activity_backed_service_power_measured"
            if best is not None
            else "activity_power_rejected_no_gated_candidate"
        ),
        "promotion_gate_pass": best is not None,
        "candidate_count": 1,
        "promoted_candidate_count": 1 if best is not None else 0,
        "best_candidate_id": best["candidate_id"] if best is not None else None,
        "best": best,
        "candidates": [candidate],
        "selection_contract": {
            "case_id": case_contract.case_id,
            "cluster_count": case_contract.cluster_count,
            "required_flow_variant": case_contract.flow_variant,
            "clock_period_ns": clock_period_ns,
            "status": "exactly_one_status_ok_timing_feasible_row_required",
        },
        "source_dependencies": {
            "service_config": _portable_path(config),
            "metrics_csv": _portable_path(selected_metrics_csv),
            "merged_cluster_equivalence_json": _portable_path(equivalence_json),
            "integrated_service_r1_json": _portable_path(integrated_service_json),
            "orfs_design_config": _portable_path(orfs_design_config),
        },
        "dependency_contract": {
            "cluster_equivalence": cluster_equivalence,
            case_contract.dependency_key: integrated_service,
        },
        "activity_contract": {
            "generated_activity_manifest_sha256": activity_meta["generated_activity_manifest_sha256"],
            "adapted_activity_manifest_sha256": activity_meta["adapted_activity_manifest_sha256"],
            "vcd_sha256": activity_meta["vcd_sha256"],
            "clock_period_ns": clock_period_ns,
            "cycle_count": int(activity_meta["cycle_count"]),
            "workload_contract": activity_meta["workload_contract"],
        },
        "macro_manifest_contract": {
            "counts": activity_meta["macro_counts"],
            "statement": (
                "Exact macro counts are required: "
                f"{activity_meta['macro_counts']['fakeram45_2048x39']} fakeram45_2048x39 score banks and "
                f"{activity_meta['macro_counts']['fakeram45_64x32']} fakeram45_64x32 value-memory macros."
            ),
        },
        "macro_activity_contract": activity_meta["macro_activity_contract"],
        "bank3_dynamic_inactivity": {
            "inactive_banks": inactive_banks,
            "statement": inactivity_statement,
        },
        "precision_status": (
            "unchanged_integer_contract_from_merged_cluster_equivalence_and_integrated_service"
        ),
        "remaining_abstractions": [
            (
                f"The service-window energy is direct routed component energy for this exact "
                f"{case_contract.case_id} workload, not total token energy."
            ),
            "FakeRAM power uses proxy Nangate45 macro views rather than SRAM compiler signoff.",
            "Evaluator-local VCD, ODB, and SPEF paths remain redacted from the portable output.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--c1-metrics-csv", type=Path)
    parser.add_argument("--metrics-csv", type=Path)
    parser.add_argument("--equivalence-json", type=Path, required=True)
    parser.add_argument("--integrated-service-json", type=Path, required=True)
    parser.add_argument("--orfs-design-config", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=10.0)
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--case-id", type=str)
    parser.add_argument(
        "--min-sequential-register-activity-coverage",
        type=float,
        default=0.95,
    )
    args = parser.parse_args()
    payload = build_report(
        config=args.config,
        c1_metrics_csv=args.c1_metrics_csv,
        metrics_csv=args.metrics_csv,
        equivalence_json=args.equivalence_json,
        integrated_service_json=args.integrated_service_json,
        orfs_design_config=args.orfs_design_config,
        clock_period_ns=args.clock_period_ns,
        activity_dir=args.activity_dir,
        min_sequential_register_activity_coverage=args.min_sequential_register_activity_coverage,
        case_id=args.case_id,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
