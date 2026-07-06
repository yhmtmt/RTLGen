#!/usr/bin/env python3
"""Audit measured-command-control score32 exp-LUT composed datapath promotion readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"invalid JSON object in {path}")
    return payload


def _diagnosis(payload: JsonDict) -> JsonDict:
    diag = payload.get("diagnosis")
    return diag if isinstance(diag, dict) else {}


def _extract_candidate_metrics_csv(payload: JsonDict) -> str:
    candidate = payload.get("best_requested")
    if isinstance(candidate, dict):
        value = candidate.get("substituted_compute_metrics_csv")
        if isinstance(value, str) and value:
            return value

    best_feasible = payload.get("best_feasible")
    if isinstance(best_feasible, dict):
        value = best_feasible.get("substituted_compute_metrics_csv")
        if isinstance(value, str) and value:
            return value

    best_area_fit = payload.get("best_area_fit")
    if isinstance(best_area_fit, dict):
        value = best_area_fit.get("substituted_compute_metrics_csv")
        if isinstance(value, str) and value:
            return value

    for row in payload.get("rows", []):
        if isinstance(row, dict):
            value = row.get("substituted_compute_metrics_csv")
            if isinstance(value, str) and value:
                return value

    value = payload.get("measured_dual_stream_composed_metrics_csv")
    if isinstance(value, str) and value:
        return value

    return ""


def _candidate_supported(payload: JsonDict) -> bool:
    diagnosis = _diagnosis(payload)
    return _as_str(diagnosis.get("decision"), "").strip() == "dual_stream_feasible"


def _recommended_next_step_from_l2(payload: JsonDict) -> str:
    return _as_str(_diagnosis(payload).get("recommended_next_step"), "")


def _l1_wrapper_metrics(payload: JsonDict) -> list[str]:
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        return []
    out: list[str] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metrics_ref = proposal.get("metrics_ref")
        if not isinstance(metrics_ref, dict):
            continue
        metrics_csv = _as_str(metrics_ref.get("metrics_csv"))
        if metrics_csv:
            out.append(metrics_csv)
    return out


def _l1_wrapper_status(payload: JsonDict) -> bool:
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        return False
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        if _as_bool(proposal.get("physical_metrics_present"), False):
            return True

        metrics_ref = proposal.get("metrics_ref")
        if not isinstance(metrics_ref, dict):
            continue
        if _as_str(metrics_ref.get("status")).strip().lower() == "ok" and _as_str(
            metrics_ref.get("result_kind")
        ).strip().lower() == "physical_metrics":
            return True
    return False


def _backed_by_measured_wrapper(payload: JsonDict, wrapper_payload: JsonDict) -> bool:
    measured_metrics_csv = _extract_candidate_metrics_csv(payload)
    if not measured_metrics_csv:
        return False

    wrapper_metrics = _l1_wrapper_metrics(wrapper_payload)
    if not wrapper_metrics:
        return False

    return measured_metrics_csv in wrapper_metrics


def _build_payload(
    *, measured_composed_json: JsonDict, dual_stream_wrapper_json: JsonDict
) -> JsonDict:
    l2_decision = _as_str(_diagnosis(measured_composed_json).get("decision"))
    l2_recommended_next_step = _recommended_next_step_from_l2(measured_composed_json)
    l2_supported = _candidate_supported(measured_composed_json)
    wrapper_accepted = _l1_wrapper_status(dual_stream_wrapper_json)
    wrapper_metrics_match = _backed_by_measured_wrapper(measured_composed_json, dual_stream_wrapper_json)

    decision = "decoder_attention_score32_exp_lut_measured_wrapper_promotion_pending_cluster_validation"
    recommended_next_step = (
        "run partitioned/cluster wrapper physical validation before promoting the reduced-replica score32 exp-LUT datapath"
    )
    if not l2_supported:
        decision = "decoder_attention_score32_exp_lut_measured_wrapper_promotion_blocked_by_measured_decision"
        recommended_next_step = (
            "revisit reduced-replica command-control schedule: the merged L2 measured-command-control "
            "result is not dual_stream_feasible."
        )
    elif not wrapper_accepted:
        recommended_next_step = (
            "run updated partitioned/cluster wrapper physical validation for the measured command-control variant"
        )
    elif wrapper_metrics_match:
        decision = "decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded"
        recommended_next_step = (
            "promote reduced-replica score32 exp-LUT datapath using the measured dual-stream wrapper "
            "instead of partitioned-wrapper physical follow-up."
        )
    else:
        recommended_next_step = (
            "align the L2 measured command-control variant and L1 measured dual-stream wrapper metrics "
            "before wrapper promotion."
        )

    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_exp_lut_measured_wrapper_promotion_v1",
        "decision": decision,
        "diagnosis": {
            "decision": decision,
            "recommended_next_step": recommended_next_step,
            "l2_measured_decision": l2_decision,
            "l2_recommended_next_step": l2_recommended_next_step,
            "l2_candidate_supported": l2_supported,
            "l1_wrapper_present": bool(dual_stream_wrapper_json),
            "l1_wrapper_accepted": wrapper_accepted,
            "l1_wrapper_metrics_match": wrapper_metrics_match,
            "l2_selected_wrapper_metrics_csv": _extract_candidate_metrics_csv(measured_composed_json),
        },
        "source_artifacts": {
            "measured_composed_decision": "decoder_attention_composed_datapath_physical_feasibility",
            "measured_wrapper_ppa": "control_plane/shadow_exports/l1_promotions/l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1.json",
        },
        "next_step": {
            "decision_scope": "score32 exp-LUT reduced-replica composed-datapath L2 to measured wrapper promotion",
            "recommended_next_step": recommended_next_step,
            "requires_partitioned_or_cluster_validation": decision
            != "decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded",
        },
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    lines = [
        "# Score32 Exp-LUT Measured Wrapper Promotion Audit",
        "",
        "## Decision",
        f"- decision: `{payload['decision']}`",
        f"- recommended_next_step: `{payload['diagnosis']['recommended_next_step']}`",
        "",
        "## Readiness",
        f"- l2_measured_decision: `{payload['diagnosis']['l2_measured_decision']}`",
        f"- l1_wrapper_accepted: `{payload['diagnosis']['l1_wrapper_accepted']}`",
        f"- l1_wrapper_metrics_match: `{payload['diagnosis']['l1_wrapper_metrics_match']}`",
        f"- requires_partitioned_or_cluster_validation: `{payload['next_step']['requires_partitioned_or_cluster_validation']}`",
        "",
        f"- l2_selected_wrapper_metrics_csv: `{payload['diagnosis']['l2_selected_wrapper_metrics_csv']}`",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured-composed-datapath-json", type=Path, required=True)
    parser.add_argument("--measured-dual-stream-wrapper-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    measured_composed = _load_json(args.measured_composed_datapath_json)
    dual_stream_wrapper = _load_json(args.measured_dual_stream_wrapper_json)

    payload = _build_payload(
        measured_composed_json=measured_composed,
        dual_stream_wrapper_json=dual_stream_wrapper,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

