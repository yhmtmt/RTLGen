#!/usr/bin/env python3
"""Estimate top-1 recovery room for the decoder bf16/PWL path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any


JsonDict = dict[str, Any]
DEFAULT_SWEEP = Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json")
DEFAULT_SAMPLE_FILE = Path("runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl")
DEFAULT_TEMPLATE = "grid_approx_pwl_bf16_path"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return _repo_root() / candidate


def _portable(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_repo_root()))
    except ValueError:
        return str(path)


def _load_json(path: str | Path) -> JsonDict:
    with _resolve(path).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _load_jsonl(path: str | Path) -> list[JsonDict]:
    rows: list[JsonDict] = []
    with _resolve(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise SystemExit(f"expected object at {path}:{line_no}")
            rows.append(payload)
    return rows


def _manifest_samples_by_id(manifest_path: str | Path) -> dict[str, JsonDict]:
    manifest = _load_json(manifest_path)
    samples = manifest.get("samples")
    if not isinstance(samples, list):
        raise SystemExit(f"candidate manifest must contain samples list: {manifest_path}")
    return {str(sample.get("sample_id") or ""): sample for sample in samples if isinstance(sample, dict)}


def _quality_samples_by_id(quality_path: str | Path) -> dict[str, JsonDict]:
    quality = _load_json(quality_path)
    samples = quality.get("samples")
    if not isinstance(samples, list):
        raise SystemExit(f"quality JSON must contain samples list: {quality_path}")
    return {str(sample.get("sample_id") or ""): sample for sample in samples if isinstance(sample, dict)}


def _candidate_doc(manifest_sample: JsonDict) -> JsonDict:
    candidate_json = str(manifest_sample.get("candidate_json") or "").strip()
    if not candidate_json:
        raise SystemExit(f"candidate manifest sample missing candidate_json: {manifest_sample}")
    return _load_json(candidate_json)


def _next(doc: JsonDict) -> JsonDict:
    candidate = doc.get("candidate")
    if not isinstance(candidate, dict):
        return {"token_id": None, "token_text": ""}
    return {
        "token_id": candidate.get("next_token_id"),
        "token_text": candidate.get("next_token_text"),
    }


def _topk(doc: JsonDict) -> list[JsonDict]:
    candidate = doc.get("candidate")
    if not isinstance(candidate, dict):
        return []
    topk = candidate.get("topk")
    return [dict(row) for row in topk] if isinstance(topk, list) else []


def _score_for(topk: list[JsonDict], token_id: Any) -> float | None:
    for row in topk:
        if row.get("token_id") == token_id:
            try:
                return float(row.get("score"))
            except (TypeError, ValueError):
                return None
    return None


def _rank_for(topk: list[JsonDict], token_id: Any) -> int | None:
    for index, row in enumerate(topk, start=1):
        if row.get("token_id") == token_id:
            return index
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def _template_row(sweep: JsonDict, template: str) -> JsonDict:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain templates list")
    for row in rows:
        if isinstance(row, dict) and row.get("template") == template:
            return row
    raise SystemExit(f"template not found in sweep: {template}")


def _samples_by_id(sample_file: str | Path) -> dict[str, JsonDict]:
    return {str(row.get("sample_id") or ""): row for row in _load_jsonl(sample_file)}


def _miss_record(
    *,
    sample_id: str,
    sample: JsonDict,
    exact_doc: JsonDict,
    candidate_doc: JsonDict,
    quality_sample: JsonDict,
    correct_margin_stats: JsonDict,
) -> JsonDict:
    exact_next = _next(exact_doc)
    candidate_next = _next(candidate_doc)
    candidate_topk = _topk(candidate_doc)
    exact_token_id = exact_next.get("token_id")
    candidate_token_id = candidate_next.get("token_id")
    exact_rank = _rank_for(candidate_topk, exact_token_id)
    candidate_score = _score_for(candidate_topk, candidate_token_id)
    exact_score = _score_for(candidate_topk, exact_token_id)
    gap = None
    if candidate_score is not None and exact_score is not None:
        gap = candidate_score - exact_score
    median_margin = correct_margin_stats.get("median")
    p90_margin = correct_margin_stats.get("p90")
    if exact_rank == 2 and gap is not None and median_margin is not None and gap <= median_margin:
        class_name = "easy_rank2_below_median_margin"
    elif exact_rank is not None and exact_rank <= 3 and gap is not None and p90_margin is not None and gap <= p90_margin:
        class_name = "moderate_top3_within_p90_margin"
    elif exact_rank is not None and exact_rank <= 5:
        class_name = "hard_topk_present"
    else:
        class_name = "blocked_reference_missing_from_topk"
    distribution = quality_sample.get("candidate_distribution")
    return {
        "sample_id": sample_id,
        "category": sample.get("category"),
        "prompt": sample.get("prompt"),
        "expected_continuation": sample.get("expected_continuation"),
        "exact_next": exact_next,
        "candidate_next": candidate_next,
        "reference_rank_in_candidate_topk": exact_rank,
        "candidate_score": candidate_score,
        "reference_token_candidate_score": exact_score,
        "score_gap_to_flip_top1": gap,
        "candidate_top1_top2_margin": (distribution or {}).get("top1_top2_score_margin")
        if isinstance(distribution, dict)
        else None,
        "recovery_class": class_name,
        "topk_contains_reference": bool((quality_sample.get("aggregate") or {}).get("topk_contains_reference_id")),
    }


def build_report(
    *,
    sweep_path: Path = DEFAULT_SWEEP,
    sample_file: Path = DEFAULT_SAMPLE_FILE,
    template: str = DEFAULT_TEMPLATE,
) -> JsonDict:
    sweep_path = _resolve(sweep_path)
    sample_file = _resolve(sample_file)
    sweep = _load_json(sweep_path)
    row = _template_row(sweep, template)
    exact_row = _template_row(sweep, "candidate_onnx_softmax_exact")
    samples = _samples_by_id(sample_file)
    quality_by_id = _quality_samples_by_id(row["quality_json"])
    candidate_manifest = _manifest_samples_by_id(row["candidate_manifest"])
    exact_manifest = _manifest_samples_by_id(exact_row["candidate_manifest"])

    correct_margins: list[float] = []
    for sample_id, quality_sample in quality_by_id.items():
        aggregate = quality_sample.get("aggregate") or {}
        if not aggregate.get("next_token_id_match"):
            continue
        distribution = quality_sample.get("candidate_distribution")
        if not isinstance(distribution, dict):
            continue
        margin = _as_float(distribution.get("top1_top2_score_margin"))
        if margin is not None:
            correct_margins.append(margin)
    margin_stats = {
        "count": len(correct_margins),
        "min": min(correct_margins) if correct_margins else None,
        "p25": _quantile(correct_margins, 0.25),
        "median": median(correct_margins) if correct_margins else None,
        "p90": _quantile(correct_margins, 0.90),
        "max": max(correct_margins) if correct_margins else None,
    }

    miss_ids = [str(v) for v in row.get("next_token_mismatch_sample_ids") or []]
    misses = [
        _miss_record(
            sample_id=sample_id,
            sample=samples.get(sample_id, {}),
            exact_doc=_candidate_doc(exact_manifest[sample_id]),
            candidate_doc=_candidate_doc(candidate_manifest[sample_id]),
            quality_sample=quality_by_id[sample_id],
            correct_margin_stats=margin_stats,
        )
        for sample_id in miss_ids
    ]
    topk_safe = not row.get("topk_miss_sample_ids")
    easy_count = sum(1 for miss in misses if str(miss["recovery_class"]).startswith("easy_"))
    moderate_count = sum(1 for miss in misses if str(miss["recovery_class"]).startswith("moderate_"))
    hard_count = len(misses) - easy_count - moderate_count
    if topk_safe and misses and hard_count == 0 and easy_count >= 1:
        decision = "recoverable_margin_shift"
        recommended = "Prototype bf16/PWL-aware fine-tuning or QAT before spending more exact-safe integer PPA effort."
    elif topk_safe and misses and hard_count == 0:
        decision = "plausibly_recoverable_margin_shift"
        recommended = "Measure training sensitivity on the miss samples before treating q12 exact-safe hardware as necessary."
    elif topk_safe:
        decision = "topk_safe_but_recovery_unclear"
        recommended = "Inspect low-rank or large-gap misses before a training experiment."
    else:
        decision = "not_recoverable_from_topk_only"
        recommended = "Do not rely on training recovery without first restoring top-k containment."

    sample_count = int(row.get("sample_count") or 0)
    next_matches = round(float(row.get("next_token_id_match_rate") or 0.0) * sample_count)
    topk_matches = round(float(row.get("topk_contains_reference_id_rate") or 0.0) * sample_count)
    return {
        "version": 0.1,
        "source_sweep": _portable(sweep_path),
        "sample_file": _portable(sample_file),
        "template": template,
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "correct_sample_margin_stats": margin_stats,
        "misses": misses,
        "diagnosis": {
            "decision": decision,
            "summary": (
                "Recoverability is estimated from the score gap required to move the exact-reference "
                "token back to top-1 in the bf16/PWL candidate output. This is not training proof; it "
                "is a margin screen for whether a QAT/fine-tuning experiment is worth running."
            ),
            "topk_safe": topk_safe,
            "miss_count": len(misses),
            "easy_count": easy_count,
            "moderate_count": moderate_count,
            "hard_count": hard_count,
            "recommended_next_step": recommended,
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)


def _write_md(doc: JsonDict, path: Path) -> None:
    stats = doc["correct_sample_margin_stats"]
    lines = [
        "# Decoder bf16/PWL Recoverability",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- template: `{doc['template']}`",
        f"- decision: `{doc['diagnosis']['decision']}`",
        f"- next-token: {doc['next_token_matches']}/{doc['sample_count']}",
        f"- top-k: {doc['topk_matches']}/{doc['sample_count']}",
        f"- summary: {doc['diagnosis']['summary']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Correct-Sample Margins",
        "",
        "| count | min | p25 | median | p90 | max |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            f"| {stats['count']} | {_fmt(stats['min'])} | {_fmt(stats['p25'])} | "
            f"{_fmt(stats['median'])} | {_fmt(stats['p90'])} | {_fmt(stats['max'])} |"
        ),
        "",
        "## Miss Recovery Gaps",
        "",
        "| sample | category | rank | wrong token | reference token | gap | class |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for miss in doc["misses"]:
        lines.append(
            "| `{sample}` | `{category}` | {rank} | `{wrong}` | `{ref}` | {gap} | `{cls}` |".format(
                sample=miss["sample_id"],
                category=miss.get("category") or "",
                rank=miss.get("reference_rank_in_candidate_topk") or "",
                wrong=miss["candidate_next"].get("token_text"),
                ref=miss["exact_next"].get("token_text"),
                gap=_fmt(miss.get("score_gap_to_flip_top1")),
                cls=miss["recovery_class"],
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sweep", default=str(DEFAULT_SWEEP))
    ap.add_argument("--sample-file", default=str(DEFAULT_SAMPLE_FILE))
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    doc = build_report(sweep_path=Path(args.sweep), sample_file=Path(args.sample_file), template=str(args.template))
    out_path = _resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_md(doc, _resolve(args.out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
