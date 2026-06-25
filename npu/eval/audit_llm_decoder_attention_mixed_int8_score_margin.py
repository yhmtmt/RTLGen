#!/usr/bin/env python3
"""Audit mixed-int8 score precision recovery artifacts by reference-margin miss buckets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

JsonDict = dict[str, Any]

DECISION_PASS = "score_margin_audit_pass"
DECISION_NARROW_HOLD = "score_margin_audit_narrow_margin_hold"
DECISION_SYSTEMATIC_HOLD = "score_margin_audit_systematic_hold"
DECISION_UNKNOWN = "score_margin_audit_unknown"

REFERENCE_MARGIN_BUCKETS: tuple[tuple[float, str], ...] = (
    (0.5, "0_0.5"),
    (1.0, "0_5_1.0"),
    (2.0, "1.0_2.0"),
    (4.0, "2.0_4.0"),
)
NARROW_MARGIN_LABELS = {"0_0.5", "0_5_1.0"}


DecisionStatus = str


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object at {path}")
    return payload


def _row_like(value: Any) -> bool:
    return isinstance(value, dict) and ("candidate_id" in value) and (
        "reference_margin" in value
        or "reference_top1" in value
        or "candidate_top1" in value
        or "top1_match" in value
        or "topk_contains" in value
    )


def _summary_like(value: Any) -> bool:
    return isinstance(value, dict) and "candidate_id" in value and (
        "top1_match_rate" in value
        or "topk_contains_rate" in value
        or "top1_match" in value
    )


def _get_candidate_rows(payload: JsonDict) -> list[JsonDict]:
    candidates: list[JsonDict] = []
    for key in ("candidate_rows", "rows", "rows_by_candidate"):
        value = payload.get(key)
        if isinstance(value, list):
            candidates.extend([dict(row) for row in value if _row_like(row)])
    if not candidates:
        def walk(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                if _row_like(node):
                    candidates.append(dict(node))
                    return
                for value in node.values():
                    walk(value)

        walk(payload)
    return candidates


def _get_candidate_summaries(payload: JsonDict) -> list[JsonDict]:
    summaries: list[JsonDict] = []
    for key in ("candidate_summaries", "candidate_summary", "best_candidate", "summary"):
        value = payload.get(key)
        if isinstance(value, list):
            summaries.extend([dict(row) for row in value if _summary_like(row)])
        elif isinstance(value, dict) and _summary_like(value):
            summaries.append(dict(value))

    if not summaries:
        def walk(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                if _summary_like(node):
                    summaries.append(dict(node))
                    return
                for value in node.values():
                    walk(value)

        walk(payload)
    return summaries


def _precision_fields(row: JsonDict) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "candidate_id",
            "q_bits",
            "k_bits",
            "v_bits",
            "score_bits",
            "weight_bits",
            "softmax_mode",
            "precision_profile",
        )
        if key in row
    }


def _bucket_label(reference_margin: float) -> str:
    if reference_margin < 0.0:
        return "negative"
    for edge, label in REFERENCE_MARGIN_BUCKETS:
        if reference_margin < edge:
            return label
    return ">=4.0"


def _summarize_rows(rows: list[JsonDict]) -> dict[str, Any]:
    if not rows:
        return {
            "comparison_count": 0,
            "top1_match_rate": 0.0,
            "topk_contains_rate": 0.0,
            "mean_logit_cosine": 0.0,
            "mean_probability_kl": 0.0,
            "top1_miss_count": 0,
            "miss_topk_contains_rate": 0.0,
            "miss_mean_reference_margin": 0.0,
            "miss_mean_logit_cosine": 0.0,
            "miss_mean_probability_kl": 0.0,
            "miss_max_abs_logit_delta": 0.0,
            "top1_miss_by_reference_margin": {
                "0_0.5": 0,
                "0_5_1.0": 0,
                "1.0_2.0": 0,
                "2.0_4.0": 0,
                ">=4.0": 0,
                "negative": 0,
            },
            "max_abs_logit_delta": 0.0,
        }

    comparison_count = len(rows)
    top1_matches = [_as_float(row.get("top1_match"), 0.0) for row in rows]
    topk_contains = [_as_float(row.get("topk_contains"), 0.0) for row in rows]
    logit_cosine = [_as_float(row.get("logit_cosine"), 0.0) for row in rows]
    kl = [_as_float(row.get("probability_kl"), 0.0) for row in rows]
    delta = [_as_float(row.get("max_abs_logit_delta"), 0.0) for row in rows]

    misses_by_bucket = {
        "0_0.5": 0,
        "0_5_1.0": 0,
        "1.0_2.0": 0,
        "2.0_4.0": 0,
        ">=4.0": 0,
        "negative": 0,
    }

    miss_rows: list[JsonDict] = []
    for row in rows:
        if _as_float(row.get("top1_match"), 0.0) < 1.0:
            miss_rows.append(row)
            margin = _as_float(row.get("reference_margin"), 0.0)
            misses_by_bucket[_bucket_label(margin)] += 1

    miss_topk = [_as_float(row.get("topk_contains"), 0.0) for row in miss_rows]
    miss_margins = [_as_float(row.get("reference_margin"), 0.0) for row in miss_rows]
    miss_cosines = [_as_float(row.get("logit_cosine"), 0.0) for row in miss_rows]
    miss_kl = [_as_float(row.get("probability_kl"), 0.0) for row in miss_rows]
    miss_deltas = [_as_float(row.get("max_abs_logit_delta"), 0.0) for row in miss_rows]

    return {
        "comparison_count": comparison_count,
        "top1_match_rate": mean(top1_matches) if comparison_count else 0.0,
        "topk_contains_rate": mean(topk_contains) if comparison_count else 0.0,
        "mean_logit_cosine": mean(logit_cosine) if comparison_count else 0.0,
        "mean_probability_kl": mean(kl) if comparison_count else 0.0,
        "top1_miss_count": sum(1 for value in top1_matches if value < 1.0),
        "miss_topk_contains_rate": mean(miss_topk) if miss_topk else 0.0,
        "miss_mean_reference_margin": mean(miss_margins) if miss_margins else 0.0,
        "miss_mean_logit_cosine": mean(miss_cosines) if miss_cosines else 0.0,
        "miss_mean_probability_kl": mean(miss_kl) if miss_kl else 0.0,
        "miss_max_abs_logit_delta": max(miss_deltas) if miss_deltas else 0.0,
        "top1_miss_by_reference_margin": misses_by_bucket,
        "max_abs_logit_delta": max(delta) if delta else 0.0,
    }


def _coalesce_summary(
    candidate_id: str,
    row_summary: dict[str, Any],
    candidate_summary: JsonDict | None,
    *,
    row_count: int,
) -> JsonDict:
    candidate_summary = candidate_summary or {}
    out: JsonDict = {"candidate_id": candidate_id}
    precision = _precision_fields(candidate_summary)
    if precision:
        out.update(precision)

    prefer_rows = row_count > 0
    out["comparison_count"] = _as_int(
        row_summary.get("comparison_count") if prefer_rows else candidate_summary.get("comparison_count"),
        0,
    )
    out["top1_match_rate"] = _as_float(
        row_summary.get("top1_match_rate") if prefer_rows else candidate_summary.get("top1_match_rate"),
        0.0,
    )
    out["topk_contains_rate"] = _as_float(
        row_summary.get("topk_contains_rate") if prefer_rows else candidate_summary.get("topk_contains_rate"),
        0.0,
    )
    out["mean_logit_cosine"] = _as_float(
        row_summary.get("mean_logit_cosine") if prefer_rows else candidate_summary.get("mean_logit_cosine"),
        0.0,
    )
    out["mean_probability_kl"] = _as_float(
        row_summary.get("mean_probability_kl") if prefer_rows else candidate_summary.get("mean_probability_kl"),
        0.0,
    )
    out["max_abs_logit_delta"] = _as_float(
        row_summary.get("max_abs_logit_delta") if prefer_rows else (
            candidate_summary.get("max_abs_logit_delta_max") or candidate_summary.get("max_abs_logit_delta")
        ),
        0.0,
    )
    for key in (
        "miss_topk_contains_rate",
        "miss_mean_reference_margin",
        "miss_mean_logit_cosine",
        "miss_mean_probability_kl",
        "miss_max_abs_logit_delta",
    ):
        out[key] = _as_float(row_summary.get(key), 0.0) if prefer_rows else _as_float(candidate_summary.get(key), 0.0)

    if "max_abs_logit_delta_max" in candidate_summary:
        out["max_abs_logit_delta"] = _as_float(candidate_summary.get("max_abs_logit_delta_max"), out["max_abs_logit_delta"])

    if candidate_summary:
        decision_status = candidate_summary.get("decision_status")
        if isinstance(decision_status, str) and decision_status:
            out["decision_status"] = decision_status

    miss_buckets = row_summary.get("top1_miss_by_reference_margin", {}) if row_summary else {}
    if isinstance(miss_buckets, dict):
        out["top1_miss_by_reference_margin"] = {
            key: _as_int(value, 0)
            for key, value in miss_buckets.items()
        }
    else:
        out["top1_miss_by_reference_margin"] = {
            "0_0.5": 0,
            "0_5_1.0": 0,
            "1.0_2.0": 0,
            "2.0_4.0": 0,
            ">=4.0": 0,
            "negative": 0,
        }

    if row_count > 0 and "top1_miss_count" in row_summary and row_summary["top1_miss_count"] is not None:
        out["top1_miss_count"] = _as_int(row_summary["top1_miss_count"], 0)
    elif out["comparison_count"]:
        out["top1_miss_count"] = out["comparison_count"] - _as_int(round(out["top1_match_rate"] * out["comparison_count"]))
    else:
        out["top1_miss_count"] = 0

    return out


def _classify_candidate(candidate: JsonDict) -> DecisionStatus:
    comparison_count = _as_int(candidate.get("comparison_count"), 0)
    if comparison_count <= 0:
        return DECISION_UNKNOWN

    top1_match_rate = _as_float(candidate.get("top1_match_rate"), 0.0)
    topk_contains_rate = _as_float(candidate.get("topk_contains_rate"), 0.0)
    if top1_match_rate >= 1.0 and topk_contains_rate >= 1.0:
        return DECISION_PASS

    if topk_contains_rate < 1.0:
        return DECISION_SYSTEMATIC_HOLD

    top1_miss_by_reference_margin = candidate.get("top1_miss_by_reference_margin")
    top1_miss_count = _as_int(candidate.get("top1_miss_count"), 0)
    if top1_miss_count <= 0:
        return DECISION_PASS

    if not isinstance(top1_miss_by_reference_margin, dict):
        return DECISION_SYSTEMATIC_HOLD

    narrow_miss_count = sum(
        _as_int(top1_miss_by_reference_margin.get(label), 0)
        for label in NARROW_MARGIN_LABELS
    )

    if narrow_miss_count == top1_miss_count:
        return DECISION_NARROW_HOLD
    return DECISION_SYSTEMATIC_HOLD


def _status_rank(status: DecisionStatus) -> int:
    order = {
        DECISION_PASS: 0,
        DECISION_NARROW_HOLD: 1,
        DECISION_SYSTEMATIC_HOLD: 2,
        DECISION_UNKNOWN: 3,
    }
    return order.get(status, 3)


def build_payload(args: argparse.Namespace) -> JsonDict:
    source = _load_json(args.score_precision_recovery_json)
    rows = _get_candidate_rows(source)
    summaries = _get_candidate_summaries(source)
    primary_candidate_id = ""
    primary_summary = source.get("candidate_summary")
    if isinstance(primary_summary, dict):
        primary_candidate_id = _as_str(primary_summary.get("candidate_id"))
    if not primary_candidate_id:
        primary = source.get("primary_candidate_id")
        primary_candidate_id = _as_str(primary)

    rows_by_candidate: dict[str, list[JsonDict]] = {}
    for row in rows:
        candidate_id = _as_str(row.get("candidate_id"))
        if not candidate_id:
            continue
        rows_by_candidate.setdefault(candidate_id, []).append(row)

    summary_by_candidate: dict[str, JsonDict] = {}
    for row in summaries:
        candidate_id = _as_str(row.get("candidate_id"))
        if not candidate_id:
            continue
        if candidate_id not in summary_by_candidate:
            summary_by_candidate[candidate_id] = dict(row)

    if not rows_by_candidate and not summary_by_candidate:
        raise RuntimeError("no candidate rows or candidate summaries in score-precision artifact")

    candidate_ids = sorted(set(rows_by_candidate) | set(summary_by_candidate))
    candidates: list[JsonDict] = []
    for candidate_id in candidate_ids:
        candidate_rows = rows_by_candidate.get(candidate_id, [])
        summary = summary_by_candidate.get(candidate_id)
        row_summary = _summarize_rows(candidate_rows)
        candidate = _coalesce_summary(
            candidate_id,
            row_summary,
            summary,
            row_count=len(candidate_rows),
        )
        candidate["candidate_rows_used"] = len(candidate_rows)
        candidate["top1_miss_by_reference_margin"] = row_summary.get("top1_miss_by_reference_margin", candidate.get("top1_miss_by_reference_margin", {}))
        candidate["top1_miss_count"] = _as_int(
            candidate.get("top1_miss_count"),
            _as_int(row_summary.get("top1_miss_count"), 0),
        )
        if "decision_status" in candidate:
            candidate["source_decision_status"] = candidate["decision_status"]
        candidate["audit_status"] = _classify_candidate(candidate)
        candidate["narrow_margin_miss_count"] = sum(
            _as_int(candidate["top1_miss_by_reference_margin"].get(label), 0)
            for label in NARROW_MARGIN_LABELS
        )
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            0 if primary_candidate_id and _as_str(item.get("candidate_id")) == primary_candidate_id else 1,
            _status_rank(item.get("audit_status", "")),
            -_as_float(item.get("top1_match_rate")),
            -_as_int(item.get("comparison_count")),
            _as_str(item.get("candidate_id")),
        )
    )

    audit_status_counts = {
        DECISION_PASS: 0,
        DECISION_NARROW_HOLD: 0,
        DECISION_SYSTEMATIC_HOLD: 0,
        DECISION_UNKNOWN: 0,
    }
    for candidate in candidates:
        audit_status_counts[candidate["audit_status"]] = audit_status_counts.get(candidate["audit_status"], 0) + 1

    if audit_status_counts[DECISION_SYSTEMATIC_HOLD]:
        decision = DECISION_SYSTEMATIC_HOLD
        recommended_next_step = (
            "Review wide-margin top-1 mismatches before rank-sensitive hardware spend."
        )
    elif audit_status_counts[DECISION_NARROW_HOLD]:
        decision = DECISION_NARROW_HOLD
        recommended_next_step = (
            "The misses are concentrated in narrow-margin regions; keep this recovery path blocked until "
            "bounded top-k and follow-up scoring checks show stable high-margin behavior."
        )
    elif audit_status_counts[DECISION_PASS]:
        decision = DECISION_PASS
        recommended_next_step = (
            "No top-1 misses found under current sample set; keep candidate-level margin buckets for cross-set confirmation."
        )
    else:
        decision = DECISION_UNKNOWN
        recommended_next_step = (
            "No margin-complete per-comparison rows were present; rerun with candidate_rows for precise miss-bucket audit."
        )

    return {
        "version": 1,
        "model": "llm_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1",
        "decision": {
            "status": decision,
            "audit_status_counts": audit_status_counts,
            "recommended_next_step": recommended_next_step,
        },
        "inputs": {
            "score_precision_recovery_json": str(args.score_precision_recovery_json),
        },
        "primary_candidate_id": primary_candidate_id,
        "candidates": candidates,
        "candidate_count": len(candidates),
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        f"# {payload['model']}",
        "",
        f"- decision: `{payload['decision']['status']}`",
        f"- decision_counts: `{payload['decision']['audit_status_counts']}`",
        f"- primary_candidate_id: `{payload.get('primary_candidate_id', '')}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Candidates",
        "",
        "| candidate_id | audit_status | top1_match | topk_contains | mean_cosine | mean_kl | max_delta | miss_count | miss_topk | miss_margin | miss_kl | miss_cosine | narrow_miss | bucketed_misses |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for candidate in payload["candidates"]:
        bucket_text = ", ".join(
            f"{bucket}:{candidate['top1_miss_by_reference_margin'].get(bucket, 0)}"
            for bucket in ["0_0.5", "0_5_1.0", "1.0_2.0", "2.0_4.0", ">=4.0", "negative"]
        )
        lines.append(
            "| {candidate_id} | {audit_status} | {top1_match_rate:.6f} | {topk_contains_rate:.6f} | "
            "{mean_logit_cosine:.6f} | {mean_probability_kl:.6f} | {max_abs_logit_delta:.6f} | {top1_miss_count} | "
            "{miss_topk_contains_rate:.6f} | {miss_mean_reference_margin:.6f} | {miss_mean_probability_kl:.6f} | "
            "{miss_mean_logit_cosine:.6f} | {narrow_margin_miss_count} | {bucket_text} |".format(
                candidate_id=candidate.get("candidate_id"),
                audit_status=candidate.get("audit_status"),
                top1_match_rate=_as_float(candidate.get("top1_match_rate")),
                topk_contains_rate=_as_float(candidate.get("topk_contains_rate")),
                mean_logit_cosine=_as_float(candidate.get("mean_logit_cosine")),
                mean_probability_kl=_as_float(candidate.get("mean_probability_kl")),
                max_abs_logit_delta=_as_float(candidate.get("max_abs_logit_delta")),
                top1_miss_count=_as_int(candidate.get("top1_miss_count")),
                miss_topk_contains_rate=_as_float(candidate.get("miss_topk_contains_rate")),
                miss_mean_reference_margin=_as_float(candidate.get("miss_mean_reference_margin")),
                miss_mean_probability_kl=_as_float(candidate.get("miss_mean_probability_kl")),
                miss_mean_logit_cosine=_as_float(candidate.get("miss_mean_logit_cosine")),
                narrow_margin_miss_count=_as_int(candidate.get("narrow_margin_miss_count")),
                bucket_text=bucket_text,
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-precision-recovery-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    print(json.dumps({"ok": True, "status": payload["decision"]["status"], "candidate_count": payload["candidate_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
