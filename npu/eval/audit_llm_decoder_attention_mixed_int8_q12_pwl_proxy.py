#!/usr/bin/env python3
"""Audit whether measured q12/PWL softmax can proxy the qkv8_float_exact frontier direction."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

JsonDict = dict[str, Any]


DECISION_QUALITY_PASS = "mixed_int8_native_attention_shadow_pass"
CANDIDATE_ID = "qkv8_q12_pwl_recip_q12_bucket8"
DEFAULT_COMPOSED_METRICS = (
    Path("runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv")
)
DEFAULT_FULL_VALUE_METRICS = (
    Path("runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv")
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _is_one(value: Any, *, tol: float = 1e-12) -> bool:
    if value is None:
        return False
    return abs(_as_float(value) - 1.0) <= tol


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object at {path}")
    return payload


def _merge_num(values: list[Any], *, default: float = 0.0) -> float:
    nums = [_as_float(v) for v in values if v is not None and str(v) != ""]
    return mean(nums) if nums else default


def _value_from_keys(row: JsonDict, keys: tuple[str, ...], *, default: float | None = None) -> Any:
    for key in keys:
        if key in row:
            value = row.get(key)
            if value is not None:
                return value
    return default


def _extract_decision_status(row: JsonDict) -> str:
    if "decision_status" in row and isinstance(row["decision_status"], str):
        return row["decision_status"].strip()
    decision = row.get("decision")
    if isinstance(decision, dict):
        status = decision.get("status")
        if isinstance(status, str):
            return status.strip()
    if isinstance(row.get("status"), str) and row.get("status").strip():
        return row["status"].strip()
    return ""


def _is_candidate_row(node: Any) -> bool:
    return isinstance(node, dict) and isinstance(node.get("candidate_id"), (str, int))


def _known_candidate_rows(payload: JsonDict) -> list[JsonDict]:
    out: list[JsonDict] = []

    def _append(value: Any) -> None:
        if not isinstance(value, dict):
            return
        candidate_id = value.get("candidate_id")
        if isinstance(candidate_id, (str, int)):
            out.append(dict(value))

    for key in (
        "candidate_summaries",
        "candidate_summary",
        "candidate_rows",
        "candidate_row",
        "candidates",
        "rows",
        "results",
        "best_candidate",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            if _is_candidate_row(value):
                _append(value)
            else:
                for item in value.values():
                    if _is_candidate_row(item):
                        _append(item)
        elif isinstance(value, list):
            for item in value:
                if _is_candidate_row(item):
                    _append(item)

    return out


def _all_candidate_rows(payload: JsonDict) -> list[JsonDict]:
    candidates = _known_candidate_rows(payload)
    if candidates:
        return candidates

    found: list[JsonDict] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if _is_candidate_row(node):
                found.append(dict(node))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def _summarize_candidate_rows(rows: list[JsonDict], *, candidate_id: str) -> JsonDict:
    def _candidate_rows(candidate_rows: list[JsonDict]) -> list[JsonDict]:
        return [row for row in candidate_rows if isinstance(row.get("candidate_id"), (str, int))]

    grouped = [row for row in _candidate_rows(rows) if _as_str(row.get("candidate_id")) == candidate_id]
    if not grouped:
        return {}

    # Prefer explicit summary rows when available.
    summary_like = [
        row
        for row in grouped
        if any(key in row for key in ("top1_match_rate", "topk_contains_rate", "mean_probability_kl", "comparison_count"))
    ]
    sample_rows = summary_like or grouped

    top1 = _merge_num([
        _value_from_keys(row, ("top1_match_rate", "top1_match", "top1", "top1_match_ratio"))
        for row in sample_rows
    ])
    topk = _merge_num([
        _value_from_keys(row, ("topk_contains_rate", "topk_contains", "topk", "topk_contains_ratio"))
        for row in sample_rows
    ])
    kl = _merge_num([
        _value_from_keys(row, ("mean_probability_kl", "probability_kl", "mean_kl", "kl"))
        for row in sample_rows
    ])
    cosine = _merge_num([
        _value_from_keys(row, ("mean_logit_cosine", "logit_cosine"))
        for row in sample_rows
    ])
    comparison_count = int(_value_from_keys(
        summary_like[0] if summary_like else grouped[0], ("comparison_count",), default=0
    ) or 0)
    if comparison_count <= 0 and not summary_like:
        # Prompt-level rows: one row is one sample point.
        comparison_count = len(grouped)

    statuses: list[str] = []
    for row in grouped:
        status = _extract_decision_status(row)
        if status:
            statuses.append(status)
    decision_status = statuses[0] if statuses else ""

    precision = {}
    precision_keys = ("candidate_id", "precision_profile", "q_bits", "k_bits", "v_bits", "weight_bits", "score_bits", "softmax_mode")
    for key in precision_keys:
        for row in grouped:
            value = row.get(key)
            if value is not None:
                precision[key] = value
                break

    max_abs_logit_delta = _merge_num(
        [_value_from_keys(row, ("max_abs_logit_delta_max", "max_abs_logit_delta")) for row in sample_rows], default=0.0
    )
    return {
        "candidate_id": candidate_id,
        "decision_status": decision_status,
        "top1_match_rate": top1,
        "topk_contains_rate": topk,
        "mean_probability_kl": kl,
        "mean_logit_cosine": cosine,
        "comparison_count": comparison_count,
        "max_abs_logit_delta_max": max_abs_logit_delta,
        "precision": precision,
    }


def _quality_candidate_summary(payload: JsonDict, candidate_id: str) -> JsonDict:
    rows = _all_candidate_rows(payload)
    return _summarize_candidate_rows(rows, candidate_id=candidate_id)


def _quality_status_category(decision_status: str) -> str:
    status = decision_status.lower()
    if status == DECISION_QUALITY_PASS:
        return "pass"
    if "caution" in status or "hold" in status:
        return "caution"
    if "fail" in status or "reject" in status:
        return "reject"
    return "unknown"


def _collect_row_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ok_rows = [row for row in rows if str(row.get("status", "") or "ok").strip() == "ok"]
    if not ok_rows:
        ok_rows = rows
    parsed: list[JsonDict] = []
    for row in ok_rows:
        cp = _as_float(row.get("critical_path_ns"), default=float("nan"))
        if cp == float("inf") or cp != cp:
            continue
        die_area = _value_from_keys(
            row,
            ("die_area", "die_area_um2", "die_area_mm2"),
            default=None,
        )
        total_power = _value_from_keys(row, ("total_power_mw", "total_power", "power_mw"), default=None)
        instance_area = _value_from_keys(row, ("instance_area_um2", "instance_area"), default=None)
        if total_power is None or die_area is None:
            continue
        parsed.append(
            {
                "critical_path_ns": cp,
                "die_area": _as_float(die_area),
                "instance_area": _as_float(instance_area, default=0.0),
                "total_power_mw": _as_float(total_power),
                "design": row.get("design", ""),
                "tag": row.get("tag", ""),
                "status": row.get("status", "ok"),
            }
        )
    return parsed


def _best_row(rows: list[JsonDict]) -> JsonDict | None:
    if not rows:
        return None
    return min(
        rows,
        key=lambda row: (
            _as_float(row.get("critical_path_ns"), float("inf")),
            _as_float(row.get("total_power_mw"), float("inf")),
        ),
    )


def _load_best_metrics_summary(path: Path) -> JsonDict | None:
    rows = _collect_row_candidates(path)
    if not rows:
        return None
    best = _best_row(rows)
    if not best:
        return None
    return {
        "metrics_csv": str(path),
        "critical_path_ns": best["critical_path_ns"],
        "total_power_mw": best["total_power_mw"],
        "die_area": best["die_area"],
        "instance_area": best["instance_area"],
        "candidate_design": best["design"],
        "tag": best["tag"],
        "ok_row_count": len(rows),
    }


def _version_hint_from_path(path: str) -> str:
    match = re.search(r"q\d+k\d+v(\d+)", path)
    if match:
        return match.group(1)
    match = re.search(r"kv8_v(\d+)", path)
    if match:
        return match.group(1)
    match = re.search(r"_v(\d+)", path)
    if match:
        return match.group(1)
    return ""


def _candidate_is_qkv8_float_exact(obj: Any) -> bool:
    return isinstance(obj, dict) and str(obj.get("candidate_id")) == "qkv8_float_exact"


def _candidate_payload(candidate_obj: JsonDict, source: str | None = None) -> JsonDict:
    summary = _summarize_candidate_rows([candidate_obj], candidate_id=_as_str(candidate_obj.get("candidate_id")))
    if source:
        summary["source"] = source
    return summary


def _extract_frontier_qkv8_source(payload: JsonDict) -> tuple[JsonDict | None, bool]:
    direction = payload.get("quality_backed_direction")
    if isinstance(direction, dict):
        if _candidate_is_qkv8_float_exact(direction):
            return _candidate_payload(direction, "quality_backed_direction"), True
        candidate = direction.get("candidate")
        if _candidate_is_qkv8_float_exact(candidate):
            summary = _summarize_candidate_rows([dict(candidate)], candidate_id="qkv8_float_exact")
            summary["source"] = "quality_backed_direction.candidate"
            return summary, True

    for key in ("qkv8_float_exact_source", "qkv8_source", "quality_backed_candidate"):
        value = payload.get(key)
        if _candidate_is_qkv8_float_exact(value):
            return _candidate_payload(value, key), True

    # Fallback: search nested candidates for qkv8_float_exact.
    for key, value in payload.items():
        if isinstance(value, dict) and _candidate_is_qkv8_float_exact(value):
            return _candidate_payload(value, f"payload.{key}"), True
    for row in _all_candidate_rows(payload):
        if str(row.get("candidate_id")) == "qkv8_float_exact":
            return _candidate_payload(row, "recursive"), True

    return {"candidate_id": "qkv8_float_exact", "candidate_not_found": True}, False


def _build_markdown(payload: JsonDict, path: Path) -> None:
    quality = payload["q12_pwl_quality"]
    frontier = payload["qkv8_float_exact_source"]
    ppa = payload["ppa_proxy"]
    decision = payload["decision"]

    lines = [
        f"# {payload['model']}",
        "",
        f"- status: `{decision['status']}`",
        f"- recommended_next_step: `{payload['recommended_next_step']}`",
        "",
        "## Quality Candidate",
        "",
        "| metric | value |",
        "|---|---|",
        f"| candidate_id | {quality.get('candidate_id')} |",
        f"| decision_status | {quality.get('decision_status')} |",
        f"| top1_match_rate | {quality.get('top1_match_rate')} |",
        f"| topk_contains_rate | {quality.get('topk_contains_rate')} |",
        f"| mean_probability_kl | {quality.get('mean_probability_kl')} |",
        f"| quality_pass_for_proxy | {quality.get('proxy_pass')} |",
        f"| qkv8_float_exact_is_quality_backed_source | {frontier.get('is_quality_backed_direction', False)} |",
        "",
        "## PPA Proxy",
        "",
        "| scope | candidate_design | critical_path_ns | die_area | instance_area | total_power_mw |",
        "|---|---|---:|---:|---:|---:|",
        (
            "| composed_q12_pwl | "
            f"{(ppa['composed_q12_pwl'] or {}).get('candidate_design', '')} | "
            f"{(ppa['composed_q12_pwl'] or {}).get('critical_path_ns', '')} | "
            f"{(ppa['composed_q12_pwl'] or {}).get('die_area', '')} | "
            f"{(ppa['composed_q12_pwl'] or {}).get('instance_area', '')} | "
            f"{(ppa['composed_q12_pwl'] or {}).get('total_power_mw', '')} |"
        ),
        (
            "| full_value_v8 (separate) | "
            f"{(ppa['full_value_v8'] or {}).get('candidate_design', '')} | "
            f"{(ppa['full_value_v8'] or {}).get('critical_path_ns', '')} | "
            f"{(ppa['full_value_v8'] or {}).get('die_area', '')} | "
            f"{(ppa['full_value_v8'] or {}).get('instance_area', '')} | "
            f"{(ppa['full_value_v8'] or {}).get('total_power_mw', '')} |"
        ),
        "",
        "## Remaining Abstractions",
    ]
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_payload(args: argparse.Namespace) -> JsonDict:
    q12_quality = _quality_candidate_summary(_load_json(args.q12_pwl_native_quality_json), CANDIDATE_ID)
    if not q12_quality:
        q12_quality = {
            "candidate_id": CANDIDATE_ID,
            "decision_status": "",
            "top1_match_rate": None,
            "topk_contains_rate": None,
            "mean_probability_kl": None,
            "comparison_count": 0,
            "max_abs_logit_delta_max": None,
        }

    quality_status = _quality_status_category(q12_quality.get("decision_status", ""))
    q12_quality["proxy_pass"] = (
        quality_status == "pass"
        and _is_one(q12_quality.get("top1_match_rate"))
        and _is_one(q12_quality.get("topk_contains_rate"))
    )
    q12_quality["quality_passed"] = q12_quality["proxy_pass"]

    frontier_payload = _load_json(args.quality_backed_frontier_json)
    qkv8_source, qkv8_is_source = _extract_frontier_qkv8_source(frontier_payload)
    qkv8_source["is_quality_backed_direction"] = bool(qkv8_is_source)

    composed = _load_best_metrics_summary(args.composed_q12_pwl_metrics)
    v8 = _load_best_metrics_summary(args.full_value_v8_metrics) if args.full_value_v8_metrics else None

    composed_version = ""
    if composed:
        composed_version = _version_hint_from_path((composed.get("candidate_design") or "") + "|" + composed["metrics_csv"])

    if not qkv8_is_source:
        decision_status = "q12_pwl_proxy_missing_evidence"
        next_step = (
            "Align quality-backed frontier inputs to explicitly identify qkv8_float_exact as the active quality-backed direction "
            "before promoting this proxy check."
        )
    elif not q12_quality["decision_status"] and not q12_quality["proxy_pass"]:
        decision_status = "q12_pwl_proxy_missing_evidence"
        next_step = (
            "Collect per-candidate quality evidence for qkv8_q12_pwl_recip_q12_bucket8 from the same mixed-int8 artifact generation "
            "that produced the frontier."
        )
    elif q12_quality["decision_status"] and quality_status == "fail":
        decision_status = "q12_pwl_proxy_quality_rejected"
        next_step = (
            "Do not use q12/PWL composed proxy evidence yet; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate "
            "before re-running this audit."
        )
    elif q12_quality["decision_status"] and quality_status == "caution":
        decision_status = "q12_pwl_proxy_quality_caution"
        next_step = (
            "Treat q12/PWL softmax as a provisional proxy only; resolve quality caution before closing as quality-backed."
        )
    elif not q12_quality["proxy_pass"]:
        decision_status = "q12_pwl_proxy_quality_caution"
        next_step = (
            "The candidate is not a strict pass for top-1/top-k at 1.0, so keep this path as quality-risk only."
        )
    else:
        if not composed:
            decision_status = "q12_pwl_proxy_missing_evidence"
            next_step = (
                "Collect measured composed q12/PWL v12/P8 datapath metrics and re-run the proxy audit before deciding."
            )
        elif (composed_version == "6") or (v8 is None):
            decision_status = "q12_pwl_proxy_v8_recost_required"
            next_step = (
                "Quality passes for qkv8_q12_pwl_recip_q12_bucket8; however this is a measured q12/PWL proxy from a v6 datapath. "
                "Generate/attach v8 full-value composed q12/PWL PPA before treating it as quality-backed."
            )
        else:
            decision_status = "q12_pwl_proxy_quality_caution"
            next_step = (
                "Quality passes and a v8 composed proxy is available; still keep this as a bounded proxy unless "
                "the v8 proxy is explicitly sanctioned by the follow-on quality gate."
            )

    ppa_proxy = {
        "composed_q12_pwl": composed,
        "full_value_v8": v8,
        "composed_q12_pwl_version_hint": composed_version or None,
        "composed_q12_pwl_is_v6_proxy": composed_version == "6",
        "full_value_v8_present": v8 is not None,
    }
    if composed:
        ppa_proxy.update(
            {
                "composed_metrics_path": composed.get("metrics_csv"),
                "composed_value_bits": int(composed_version) if composed_version.isdigit() else None,
                "composed_best_critical_path_ns": composed.get("critical_path_ns"),
                "composed_best_total_power_mw": composed.get("total_power_mw"),
                "composed_best_die_area_um2": composed.get("die_area"),
                "composed_best_instance_area_um2": composed.get("instance_area"),
            }
        )
    if v8:
        ppa_proxy.update(
            {
                "v8_full_value_metrics_path": v8.get("metrics_csv"),
                "v8_full_value_best_critical_path_ns": v8.get("critical_path_ns"),
                "v8_full_value_best_total_power_mw": v8.get("total_power_mw"),
                "v8_full_value_best_die_area_um2": v8.get("die_area"),
                "v8_full_value_best_instance_area_um2": v8.get("instance_area"),
            }
        )

    return {
        "version": 1,
        "model": "llm_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1",
        "decision": {
            "status": decision_status,
            "quality_status": quality_status,
            "rationale": next_step,
            "recommended_next_step": next_step,
        },
        "inputs": {
            "q12_pwl_native_quality_json": str(args.q12_pwl_native_quality_json),
            "quality_backed_frontier_json": str(args.quality_backed_frontier_json),
            "composed_q12_pwl_metrics_csv": str(args.composed_q12_pwl_metrics),
            "full_value_v8_metrics_csv": str(args.full_value_v8_metrics) if args.full_value_v8_metrics else "",
        },
        "q12_pwl_quality": q12_quality,
        "qkv8_float_exact_source": qkv8_source,
        "ppa_proxy": ppa_proxy,
        "remaining_abstractions": [
            "This audit is a measured datapath proxy check, not a full, fully recosted quality-backed frontier decision.",
            "The composed q12/PWL path is treated as a proxy if not quality-backed by direct qkv8_float_exact service-space evidence.",
            "Full Llama7B latency/energy/cost ranking remains unchanged until v8 full-value composed PPA replaces this proxy.",
            "No additional model-level perplexity check is performed in this script.",
        ],
        "recommended_next_step": next_step,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--q12-pwl-native-quality-json", type=Path, required=True)
    parser.add_argument("--quality-backed-frontier-json", type=Path, required=True)
    parser.add_argument("--composed-q12-pwl-metrics", type=Path, default=DEFAULT_COMPOSED_METRICS)
    parser.add_argument("--full-value-v8-metrics", type=Path, default=DEFAULT_FULL_VALUE_METRICS)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = _build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _build_markdown(payload, args.out_md)
    print(json.dumps({"ok": True, "out": str(args.out), "out_md": str(args.out_md), "decision": payload["decision"]["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
