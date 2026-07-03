#!/usr/bin/env python3
"""Release gate for the score32 exp-LUT attention frontier."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
PASS_STATUS = "mixed_int8_generation_quality_pass"


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _check_quality(payload: JsonDict, *, expected_candidate_id: str) -> tuple[JsonDict, list[str]]:
    failures: list[str] = []
    summary = payload.get("candidate_summary")
    if not isinstance(summary, dict):
        summary = payload.get("summary")
    if not isinstance(summary, dict):
        return {}, ["quality payload is missing candidate_summary/summary"]

    decision = payload.get("decision")
    if not isinstance(decision, dict):
        decision = summary.get("decision")
    if not isinstance(decision, dict):
        decision = {}

    candidate_id = str(summary.get("candidate_id") or "")
    decision_status = str(decision.get("status") or summary.get("decision_status") or "")
    if candidate_id != expected_candidate_id:
        failures.append(f"quality candidate_id {candidate_id!r} does not match {expected_candidate_id!r}")
    if decision_status != PASS_STATUS:
        failures.append(f"quality decision status {decision_status!r} does not match {PASS_STATUS!r}")

    thresholds = decision.get("thresholds")
    if not isinstance(thresholds, dict):
        thresholds = {}
    nll_delta = _float(summary.get("teacher_forced_mean_nll_delta"))
    if nll_delta == 0.0 and "teacher_forced_nll_delta_mean" in summary:
        nll_delta = _float(summary.get("teacher_forced_nll_delta_mean"))
    max_nll_delta = _float(thresholds.get("teacher_forced_mean_nll_delta_max"), 0.4)
    candidate_ref_prob = _float(summary.get("teacher_forced_candidate_reference_token_prob_mean"))
    if candidate_ref_prob == 0.0 and "candidate_probability_assigned_to_reference_token_mean" in summary:
        candidate_ref_prob = _float(summary.get("candidate_probability_assigned_to_reference_token_mean"))
    min_candidate_ref_prob = _float(
        thresholds.get("teacher_forced_candidate_reference_token_prob_mean_min"),
        0.1,
    )
    free_run_match = _float(summary.get("free_run_token_match_rate"))
    if free_run_match == 0.0 and "free_running_match_rate" in summary:
        free_run_match = _float(summary.get("free_running_match_rate"))
    min_free_run_match = _float(thresholds.get("free_running_match_rate_min"), 0.75)

    if nll_delta > max_nll_delta:
        failures.append(f"teacher-forced mean NLL delta {nll_delta:g} exceeds {max_nll_delta:g}")
    if candidate_ref_prob < min_candidate_ref_prob:
        failures.append(
            f"candidate reference-token probability {candidate_ref_prob:g} is below {min_candidate_ref_prob:g}"
        )
    if free_run_match < min_free_run_match:
        failures.append(f"free-run token match {free_run_match:g} is below {min_free_run_match:g}")

    precision = payload.get("precision")
    if not isinstance(precision, dict):
        precision = summary
    expected_precision = {
        "q_bits": 8,
        "k_bits": 8,
        "v_bits": 8,
        "score_bits": 32,
        "weight_bits": 16,
    }
    for key, expected in expected_precision.items():
        if _int(precision.get(key), -1) != expected:
            failures.append(f"quality precision {key}={precision.get(key)!r} does not match {expected}")
    softmax_mode = str(precision.get("softmax_mode") or summary.get("softmax_mode") or "")
    if "exp_lut_div" not in softmax_mode:
        failures.append(f"quality softmax_mode {softmax_mode!r} is not an exp_lut_div mode")

    return {
        "candidate_id": candidate_id,
        "decision_status": decision_status,
        "teacher_forced_mean_nll_delta": nll_delta,
        "teacher_forced_candidate_reference_token_prob_mean": candidate_ref_prob,
        "free_run_token_match_rate": free_run_match,
        "softmax_mode": softmax_mode,
    }, failures


def _check_config(payload: JsonDict, *, expected_bucket_shift: int) -> tuple[JsonDict, list[str]]:
    failures: list[str] = []
    cfg = payload.get("attention_dual_stream_composed")
    if not isinstance(cfg, dict):
        return {}, ["config is missing attention_dual_stream_composed"]

    top_name = str(payload.get("top_name") or "")
    semantic_profile = str(cfg.get("semantic_profile") or "")
    softmax_impl = str(cfg.get("softmax_impl") or "")
    bucket_shift = _int(cfg.get("softmax_reciprocal_lut_bucket_shift"), -1)
    if semantic_profile != "score32_exp_lut_div":
        failures.append(f"semantic_profile {semantic_profile!r} does not match 'score32_exp_lut_div'")
    if softmax_impl != "exp_lut_div":
        failures.append(f"softmax_impl {softmax_impl!r} does not match 'exp_lut_div'")
    if bucket_shift != expected_bucket_shift:
        failures.append(f"softmax bucket shift {bucket_shift} does not match {expected_bucket_shift}")
    if _int(cfg.get("softmax_score_bits"), -1) != 32:
        failures.append("softmax_score_bits is not 32")
    if _int(cfg.get("softmax_weight_bits"), -1) != 16:
        failures.append("softmax_weight_bits is not 16")
    if _int(cfg.get("value_bits"), -1) != 8:
        failures.append("value_bits is not 8")
    if "score32_w16_exp_lut_div" not in top_name:
        failures.append(f"top_name {top_name!r} does not name the score32 w16 exp-LUT divider wrapper")
    return {
        "top_name": top_name,
        "semantic_profile": semantic_profile,
        "softmax_impl": softmax_impl,
        "softmax_reciprocal_lut_bucket_shift": bucket_shift,
        "equivalence_hash": bool(cfg.get("equivalence_hash")),
    }, failures


def _check_metrics(path: Path, *, expected_design: str) -> tuple[JsonDict, list[str]]:
    failures: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ok_rows = [row for row in rows if str(row.get("status") or "").lower() == "ok"]
    if not ok_rows:
        return {"row_count": len(rows), "ok_row_count": 0}, ["metrics CSV has no ok rows"]
    for row in ok_rows:
        design = str(row.get("design") or "")
        if design != expected_design:
            failures.append(f"metrics design {design!r} does not match config top_name {expected_design!r}")
            break
    best = min(
        ok_rows,
        key=lambda row: (
            _float(row.get("critical_path_ns"), 1.0e30),
            _float(row.get("instance_area_um2"), _float(row.get("stdcell_area_um2"), 1.0e30)),
        ),
    )
    critical_path_ns = _float(best.get("critical_path_ns"))
    area_um2 = _float(best.get("instance_area_um2"), _float(best.get("stdcell_area_um2")))
    power_mw = _float(best.get("total_power_mw"))
    if critical_path_ns <= 0.0:
        failures.append("best metrics row has non-positive critical_path_ns")
    if area_um2 <= 0.0:
        failures.append("best metrics row has non-positive area")
    if power_mw <= 0.0:
        failures.append("best metrics row has non-positive total_power_mw")
    return {
        "row_count": len(rows),
        "ok_row_count": len(ok_rows),
        "best_param_hash": best.get("param_hash"),
        "best_tag": best.get("tag"),
        "critical_path_ns": critical_path_ns,
        "area_um2": area_um2,
        "total_power_mw": power_mw,
    }, failures


def build_payload(args: argparse.Namespace) -> JsonDict:
    quality = _load_json(args.quality_json)
    config = _load_json(args.config_json)
    quality_summary, quality_failures = _check_quality(
        quality,
        expected_candidate_id=args.expected_candidate_id,
    )
    config_summary, config_failures = _check_config(config, expected_bucket_shift=args.expected_bucket_shift)
    metrics_summary, metrics_failures = _check_metrics(
        args.metrics_csv,
        expected_design=str(config.get("top_name") or ""),
    )
    failures = quality_failures + config_failures + metrics_failures
    return {
        "version": 1,
        "model": "attention_score32_exp_lut_div_frontier_release_gate_v1",
        "release_ready": not failures,
        "failures": failures,
        "inputs": {
            "quality_json": str(args.quality_json),
            "metrics_csv": str(args.metrics_csv),
            "config_json": str(args.config_json),
            "expected_candidate_id": args.expected_candidate_id,
            "expected_bucket_shift": args.expected_bucket_shift,
        },
        "quality": quality_summary,
        "config": config_summary,
        "metrics": metrics_summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-json", required=True, type=Path)
    parser.add_argument("--metrics-csv", required=True, type=Path)
    parser.add_argument("--config-json", required=True, type=Path)
    parser.add_argument("--expected-candidate-id", default="score32_exp_lut_div")
    parser.add_argument("--expected-bucket-shift", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    payload = build_payload(args)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if payload["release_ready"]:
        return 0
    for failure in payload["failures"]:
        print(f"release gate failed: {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
