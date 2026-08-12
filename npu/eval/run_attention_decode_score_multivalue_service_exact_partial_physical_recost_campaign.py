#!/usr/bin/env python3
"""Compose the four lane-matched exact-partial physical recost points."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.audit_attention_decode_score_multivalue_service_exact_partial_physical_recost import (
    build_report as build_recost_report,
)


JsonDict = dict[str, Any]
AuditRunner = Callable[..., JsonDict]

_CAMPAIGN_MODEL = "attention_decode_score_multivalue_service_exact_partial_physical_recost_campaign_v1"
_SUMMARY_MODEL = "attention_decode_score_multivalue_service_exact_partial_physical_recost_campaign_summary_v1"
_AUDIT_MODEL = "decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1"
_CAMPAIGN_ID = "attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2"
_PROPOSAL_ID = "prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1"
_PROPOSAL_PATH = f"docs/proposals/{_PROPOSAL_ID}/proposal.json"
_PHYSICAL_DEPENDENCY = "l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1"
_FUNCTIONAL_DEPENDENCY = (
    "l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2"
)
_WORKLOAD_DEPENDENCY = (
    "l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1"
)
_DEPENDENCIES = (_PHYSICAL_DEPENDENCY, _FUNCTIONAL_DEPENDENCY, _WORKLOAD_DEPENDENCY)
_LANES = (1, 2, 4, 8)
_SERVICE_PERIOD_NS = 10.0
_TEMPORAL_PERIOD_NS = 12.0
_SERVICE_ANCHOR = (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_decode_score_multivalue_service_activity_power__"
    "l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1_r8.json"
)
_FUNCTIONAL_ROOT = (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe__"
    f"{_FUNCTIONAL_DEPENDENCY}"
)
_FUNCTIONAL_SUMMARY_MODEL = (
    "attention_decode_score_multivalue_service_finalized_cdc_lane_campaign_summary_v1"
)
_FUNCTIONAL_CAMPAIGN_ID = (
    "attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1"
)
_WORKLOAD_MODEL = "attention_decode_score_multivalue_service_workload_correspondence_v1"
_WORKLOAD_JSON = (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_exact_partial_c1_workload_correspondence__"
    f"{_WORKLOAD_DEPENDENCY}.json"
)


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _string(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(repo_root: Path, value: Any, label: str) -> Path:
    relative = Path(_string(value, label))
    if relative.is_absolute():
        raise ValueError(f"{label} must be repository-relative")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    return resolved


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise ValueError(f"{label} is not materialized: {path}")
    return path


def _validate_campaign(payload: JsonDict) -> JsonDict:
    if _string(payload.get("model"), "campaign model") != _CAMPAIGN_MODEL:
        raise ValueError("campaign model mismatch")
    if _string(payload.get("campaign_id"), "campaign_id") != _CAMPAIGN_ID:
        raise ValueError("campaign_id mismatch")
    proposal_ref = payload.get("proposal_ref")
    if not isinstance(proposal_ref, dict) or proposal_ref != {
        "proposal_id": _PROPOSAL_ID,
        "proposal_path": _PROPOSAL_PATH,
    }:
        raise ValueError("campaign proposal_ref mismatch")
    dependencies = payload.get("depends_on_item_ids")
    if dependencies != list(_DEPENDENCIES):
        raise ValueError(
            "campaign must require exactly the physical, functional, and workload dependency items"
        )

    fixed = payload.get("fixed_inputs")
    if not isinstance(fixed, dict):
        raise ValueError("campaign requires fixed_inputs")
    if fixed.get("service_activity_power_json") != _SERVICE_ANCHOR:
        raise ValueError("campaign must use the promoted c1 service activity anchor r8")
    if fixed.get("service_period_ns") != _SERVICE_PERIOD_NS:
        raise ValueError("campaign service_period_ns must be 10")
    if fixed.get("temporal_period_ns") != _TEMPORAL_PERIOD_NS:
        raise ValueError("campaign temporal_period_ns must be 12")
    if fixed.get("fifo_canonical_timed_domain") != "source":
        raise ValueError("campaign must use source-domain canonical FIFO accounting")
    expected_summary = f"{_FUNCTIONAL_ROOT}/campaign_summary.json"
    if fixed.get("functional_probe_summary_json") != expected_summary:
        raise ValueError("campaign functional probe summary must come from the required functional item")
    if fixed.get("workload_correspondence_json") != _WORKLOAD_JSON:
        raise ValueError(
            "campaign workload correspondence must come from the required workload item"
        )

    for domain in ("source", "destination"):
        fifo = fixed.get(f"async_fifo_{domain}")
        expected_design = f"attention_exact_partial_async_fifo_d4_{domain}_domain_physical"
        expected_root = f"runs/designs/npu_blocks/{expected_design}"
        if not isinstance(fifo, dict) or fifo != {
            "design": expected_design,
            "metrics_csv": f"{expected_root}/metrics.csv",
            "config_json": f"{expected_root}/config.json",
            "macro_manifest_json": f"{expected_root}/macro_manifest.json",
        }:
            raise ValueError(f"campaign async_fifo_{domain} bundle mismatch")

    points = payload.get("points")
    if not isinstance(points, list) or len(points) != len(_LANES):
        raise ValueError("campaign requires exactly four points")
    for point, lane in zip(points, _LANES, strict=True):
        design = f"attention_score32_exact_partial_temporal_finalizer_physical_l{lane}"
        design_root = f"runs/designs/npu_blocks/{design}"
        expected = {
            "divider_lanes": lane,
            "temporal_design": design,
            "temporal_metrics_csv": f"{design_root}/metrics.csv",
            "temporal_config_json": f"{design_root}/config.json",
            "temporal_macro_manifest_json": f"{design_root}/macro_manifest.json",
            "functional_probe_json": f"{_FUNCTIONAL_ROOT}/lane{lane}.json",
        }
        if point != expected:
            raise ValueError(f"campaign point mismatch for divider_lanes={lane}")
    return payload


def _validate_functional_summary(
    *, summary_path: Path, campaign: JsonDict, repo_root: Path
) -> None:
    summary = _load_json(summary_path)
    if summary.get("model") != _FUNCTIONAL_SUMMARY_MODEL or summary.get("passed") is not True:
        raise ValueError("functional dependency campaign summary must be passing")
    if summary.get("campaign_id") != _FUNCTIONAL_CAMPAIGN_ID:
        raise ValueError("functional dependency campaign summary campaign_id mismatch")
    fixed = summary.get("fixed_parameters")
    if not isinstance(fixed, dict) or fixed.get("service_period_ns") != _SERVICE_PERIOD_NS:
        raise ValueError("functional dependency campaign summary service period mismatch")
    if fixed.get("temporal_period_ns") != _TEMPORAL_PERIOD_NS:
        raise ValueError("functional dependency campaign summary temporal period mismatch")
    if summary.get("divider_lanes") != list(_LANES) or summary.get("point_count") != len(_LANES):
        raise ValueError("functional dependency campaign summary lane set mismatch")
    points = summary.get("points")
    if not isinstance(points, list) or len(points) != len(_LANES):
        raise ValueError("functional dependency campaign summary points mismatch")
    for point, campaign_point, lane in zip(points, campaign["points"], _LANES, strict=True):
        if not isinstance(point, dict) or point.get("divider_lanes") != lane:
            raise ValueError(f"functional dependency summary lane mismatch for divider_lanes={lane}")
        probe_path = _require_file(
            _repo_path(repo_root, campaign_point["functional_probe_json"], "functional_probe_json"),
            f"functional probe lane {lane}",
        )
        if point.get("output") != campaign_point["functional_probe_json"]:
            raise ValueError(f"functional dependency output path mismatch for divider_lanes={lane}")
        if point.get("sha256") != _sha256(probe_path):
            raise ValueError(f"functional dependency hash mismatch for divider_lanes={lane}")


def _validate_workload_correspondence(path: Path) -> dict[int, JsonDict]:
    payload = _load_json(path)
    if payload.get("model") != _WORKLOAD_MODEL or payload.get("passed") is not True:
        raise ValueError("workload correspondence dependency must be passing")
    workload = payload.get("workload")
    if not isinstance(workload, dict):
        raise ValueError("workload correspondence requires workload metadata")
    if workload.get("sequence_length") != 131072 or workload.get("windows_per_head") != 5462:
        raise ValueError("workload correspondence must describe the selected Llama7B 131k workload")
    lane_reports = payload.get("lane_reports")
    if not isinstance(lane_reports, list) or len(lane_reports) != len(_LANES):
        raise ValueError("workload correspondence lane set mismatch")
    by_lane: dict[int, JsonDict] = {}
    for report, lane in zip(lane_reports, _LANES, strict=True):
        if not isinstance(report, dict) or report.get("divider_lanes") != lane:
            raise ValueError(f"workload correspondence lane mismatch for divider_lanes={lane}")
        proof = report.get("affine_recurrence_proof")
        projection = report.get("projection")
        if not isinstance(proof, dict) or proof.get("proven") is not True:
            raise ValueError(f"workload affine proof missing for divider_lanes={lane}")
        if proof.get("bounded_window_counts") != [1, 2, 3, 4]:
            raise ValueError(f"workload affine proof bounds mismatch for divider_lanes={lane}")
        if not isinstance(projection, dict) or projection.get("windows_per_head") != 5462:
            raise ValueError(f"workload projection missing for divider_lanes={lane}")
        startup = proof.get("startup_cycles")
        steady = proof.get("steady_state_cycles_per_additional_full_window")
        measured = proof.get("measured_service_span_cycles")
        deltas = proof.get("counter_deltas")
        if (
            not isinstance(startup, int)
            or isinstance(startup, bool)
            or startup <= 0
            or not isinstance(steady, int)
            or isinstance(steady, bool)
            or steady <= 0
        ):
            raise ValueError(f"workload affine coefficients invalid for divider_lanes={lane}")
        if measured != [startup + index * steady for index in range(4)]:
            raise ValueError(f"workload affine measurements mismatch for divider_lanes={lane}")
        if deltas != [steady, steady, steady]:
            raise ValueError(f"workload affine deltas mismatch for divider_lanes={lane}")
        service_cycles = projection.get("service_cycles_per_head")
        final_drain = projection.get("temporal_final_drain_cycles_per_head")
        expected_service_cycles = startup + (5462 - 1) * steady
        if service_cycles != expected_service_cycles:
            raise ValueError(f"workload service projection mismatch for divider_lanes={lane}")
        if not isinstance(final_drain, int) or isinstance(final_drain, bool) or final_drain <= 0:
            raise ValueError(f"workload final drain invalid for divider_lanes={lane}")
        expected_head_ns = service_cycles * _SERVICE_PERIOD_NS + final_drain * _TEMPORAL_PERIOD_NS
        if projection.get("head_latency_ns_serial_upper_bound") != expected_head_ns:
            raise ValueError(f"workload head latency mismatch for divider_lanes={lane}")
        if projection.get("layer_latency_ns_serial_upper_bound") != expected_head_ns * 32:
            raise ValueError(f"workload layer latency mismatch for divider_lanes={lane}")
        if report.get("tail_adjustment_used_in_projection") is not False:
            raise ValueError(f"workload projection must conservatively omit tail saving for lane={lane}")
        by_lane[lane] = report
    return by_lane


def _audit_kwargs(*, campaign: JsonDict, point: JsonDict, repo_root: Path) -> JsonDict:
    fixed = campaign["fixed_inputs"]
    source = fixed["async_fifo_source"]
    destination = fixed["async_fifo_destination"]
    raw_paths = {
        "service_activity_power_json": fixed["service_activity_power_json"],
        "temporal_metrics_csv": point["temporal_metrics_csv"],
        "temporal_config_json": point["temporal_config_json"],
        "temporal_macro_manifest_json": point["temporal_macro_manifest_json"],
        "async_fifo_source_metrics_csv": source["metrics_csv"],
        "async_fifo_source_config_json": source["config_json"],
        "async_fifo_source_macro_manifest_json": source["macro_manifest_json"],
        "async_fifo_destination_metrics_csv": destination["metrics_csv"],
        "async_fifo_destination_config_json": destination["config_json"],
        "async_fifo_destination_macro_manifest_json": destination["macro_manifest_json"],
        "functional_probe_json": point["functional_probe_json"],
    }
    paths = {
        key: _require_file(_repo_path(repo_root, value, key), key)
        for key, value in raw_paths.items()
    }
    return {
        **paths,
        "temporal_design": point["temporal_design"],
        "temporal_clock_period_ns": fixed["temporal_period_ns"],
        "async_fifo_source_design": source["design"],
        "async_fifo_source_clock_period_ns": fixed["service_period_ns"],
        "async_fifo_destination_design": destination["design"],
        "async_fifo_destination_clock_period_ns": fixed["temporal_period_ns"],
        "fifo_canonical_timed_domain": fixed["fifo_canonical_timed_domain"],
        "csv_out": None,
    }


def _lightweight_point(report: JsonDict, *, lane: int) -> JsonDict:
    rows = report.get("rows")
    if report.get("model") != _AUDIT_MODEL or not isinstance(rows, list) or len(rows) != 1:
        raise ValueError(f"recost audit returned an invalid report for divider_lanes={lane}")
    row = rows[0]
    if not isinstance(row, dict) or row.get("divider_lanes") != lane:
        raise ValueError(f"recost audit returned the wrong lane for divider_lanes={lane}")
    timing_bounds = report.get("timing_bounds")
    if not isinstance(timing_bounds, dict):
        raise ValueError(f"recost audit omitted timing bounds for divider_lanes={lane}")
    composed = report.get("composed_physical")
    if not isinstance(composed, dict) or not isinstance(composed.get("power_provenance"), dict):
        raise ValueError(f"recost audit omitted physical power provenance for divider_lanes={lane}")
    if not isinstance(composed.get("composition_contract"), dict):
        raise ValueError(f"recost audit omitted composition contract for divider_lanes={lane}")
    energy = report.get("energy_contract")
    if not isinstance(energy, dict) or energy.get("exact_token_energy_claimed") is not False:
        raise ValueError(f"recost audit overstated energy status for divider_lanes={lane}")
    return {
        "divider_lanes": lane,
        "candidate_id": report.get("candidate_id"),
        "inputs": report.get("inputs"),
        "input_hashes": report.get("input_hashes"),
        "timing_bounds": timing_bounds,
        "composed_physical": {
            key: composed.get(key)
            for key in (
                "instance_area_um2",
                "instance_area_mm2",
                "generic_composed_total_power_mw",
                "service_activity_window_power_mw",
                "service_activity_window_energy_j",
                "power_provenance",
                "composition_contract",
            )
        },
        "energy_contract": energy,
        "functional_contract": report.get("functional_contract"),
    }


def run_campaign(
    *,
    campaign_path: Path,
    out: Path,
    csv_out: Path,
    repo_root: Path = _REPO_ROOT,
    audit_runner: AuditRunner = build_recost_report,
) -> JsonDict:
    repo_root = repo_root.resolve()
    campaign_path = campaign_path.resolve()
    campaign = _validate_campaign(_load_json(campaign_path))
    summary_path = _require_file(
        _repo_path(
            repo_root,
            campaign["fixed_inputs"]["functional_probe_summary_json"],
            "functional_probe_summary_json",
        ),
        "functional dependency campaign summary",
    )
    _validate_functional_summary(summary_path=summary_path, campaign=campaign, repo_root=repo_root)
    workload_path = _require_file(
        _repo_path(
            repo_root,
            campaign["fixed_inputs"]["workload_correspondence_json"],
            "workload_correspondence_json",
        ),
        "workload correspondence dependency",
    )
    workload_by_lane = _validate_workload_correspondence(workload_path)

    rows: list[JsonDict] = []
    point_summaries: list[JsonDict] = []
    for point in campaign["points"]:
        lane = point["divider_lanes"]
        print(f"recosting exact-partial composed service divider_lanes={lane}", flush=True)
        report = audit_runner(**_audit_kwargs(campaign=campaign, point=point, repo_root=repo_root))
        point_summary = _lightweight_point(report, lane=lane)
        workload = workload_by_lane[lane]
        proof = workload["affine_recurrence_proof"]
        projection = workload["projection"]
        row = dict(report["rows"][0])
        row.update(
            {
                "workload_windows_per_head": projection["windows_per_head"],
                "workload_service_startup_cycles": proof["startup_cycles"],
                "workload_service_steady_cycles_per_window": proof[
                    "steady_state_cycles_per_additional_full_window"
                ],
                "workload_service_cycles_per_head": projection["service_cycles_per_head"],
                "workload_temporal_final_drain_cycles_per_head": projection[
                    "temporal_final_drain_cycles_per_head"
                ],
                "workload_head_latency_ns_serial_upper_bound": projection[
                    "head_latency_ns_serial_upper_bound"
                ],
                "workload_layer_latency_ns_serial_upper_bound": projection[
                    "layer_latency_ns_serial_upper_bound"
                ],
            }
        )
        rows.append(row)
        point_summary["workload_correspondence"] = {
            "affine_recurrence_proof": proof,
            "projection": projection,
            "tail_adjustment_used_in_projection": workload[
                "tail_adjustment_used_in_projection"
            ],
        }
        point_summaries.append(point_summary)

    fieldnames = list(rows[0])
    if any(list(row) != fieldnames for row in rows):
        raise ValueError("recost audit CSV row schemas differ across lanes")
    summary = {
        "model": _SUMMARY_MODEL,
        "decision": "exact_partial_composed_service_physical_recost_campaign_recorded",
        "campaign_id": _CAMPAIGN_ID,
        "passed": True,
        "proposal_ref": campaign["proposal_ref"],
        "dependency_contract": {
            "depends_on_item_ids": list(_DEPENDENCIES),
            "all_dependencies_required": True,
            "all_dependencies_materialized": True,
        },
        "campaign_path": campaign_path.relative_to(repo_root).as_posix(),
        "campaign_sha256": _sha256(campaign_path),
        "functional_dependency_summary_sha256": _sha256(summary_path),
        "workload_correspondence_sha256": _sha256(workload_path),
        "divider_lanes": list(_LANES),
        "point_count": len(rows),
        "points": point_summaries,
        "rows": rows,
        "artifact_contract": {
            "one_aggregate_json": True,
            "one_four_row_csv": True,
            "per_lane_recost_reports_omitted": True,
            "overlap_and_serial_bounds_preserved": True,
            "provisional_energy_provenance_preserved": True,
            "llama7b_workload_projection_preserved": True,
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    if out.parent.resolve() != csv_out.parent.resolve():
        raise ValueError("aggregate JSON and CSV outputs must share a directory")
    with tempfile.TemporaryDirectory(prefix="exact-partial-physical-recost-", dir=out.parent) as temp_name:
        stage_root = Path(temp_name)
        staged_json = stage_root / out.name
        staged_csv = stage_root / csv_out.name
        staged_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with staged_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        staged_json.replace(out)
        staged_csv.replace(csv_out)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    args = parser.parse_args(argv)
    run_campaign(campaign_path=args.campaign, out=args.out, csv_out=args.csv_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
