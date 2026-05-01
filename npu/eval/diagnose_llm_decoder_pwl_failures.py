#!/usr/bin/env python3
"""Diagnose per-sample PWL decoder frontier misses from a quality sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
DEFAULT_TEMPLATES = [
    "candidate_onnx_softmax_exact",
    "grid_approx_pwl_bf16_path",
    "grid_approx_pwl_in_q8_w_q8_norm_exact",
    "grid_approx_pwl_in_q8_w_q8_norm_recip_q10",
]
DEFAULT_FOCUS_SAMPLES = [
    "dist2_arith_three_plus_five",
    "dist2_sequence_months",
]
DEFAULT_CONTROL_SAMPLES = [
    "dist2_arith_two_plus_two",
    "dist2_arith_six_times_two",
    "dist2_sequence_numbers",
    "dist2_sequence_weekdays",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return _repo_root() / candidate


def _load_json(path: str | Path) -> JsonDict:
    with _resolve(path).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _load_jsonl(path: str | Path) -> list[JsonDict]:
    out: list[JsonDict] = []
    with _resolve(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise SystemExit(f"expected object at {path}:{line_no}")
            out.append(payload)
    return out


def _portable(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_repo_root()))
    except ValueError:
        return str(path)


def _samples_by_id(sample_file: str | Path) -> dict[str, JsonDict]:
    return {str(sample["sample_id"]): sample for sample in _load_jsonl(sample_file)}


def _sweep_rows_by_template(sweep: JsonDict) -> dict[str, JsonDict]:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain templates list")
    return {str(row.get("template") or ""): row for row in rows if isinstance(row, dict)}


def _quality_samples_by_id(quality_path: str | Path) -> dict[str, JsonDict]:
    quality = _load_json(quality_path)
    samples = quality.get("samples")
    if not isinstance(samples, list):
        raise SystemExit(f"quality JSON must contain samples list: {quality_path}")
    return {str(sample.get("sample_id") or ""): sample for sample in samples if isinstance(sample, dict)}


def _manifest_samples_by_id(manifest_path: str | Path) -> dict[str, JsonDict]:
    manifest = _load_json(manifest_path)
    samples = manifest.get("samples")
    if not isinstance(samples, list):
        raise SystemExit(f"candidate manifest must contain samples list: {manifest_path}")
    return {str(sample.get("sample_id") or ""): sample for sample in samples if isinstance(sample, dict)}


def _topk(doc: JsonDict) -> list[JsonDict]:
    candidate = doc.get("candidate")
    if not isinstance(candidate, dict):
        return []
    topk = candidate.get("topk")
    return [dict(row) for row in topk] if isinstance(topk, list) else []


def _next(doc: JsonDict) -> JsonDict:
    candidate = doc.get("candidate")
    if not isinstance(candidate, dict):
        return {"token_id": None, "token_text": ""}
    return {
        "token_id": candidate.get("next_token_id"),
        "token_text": candidate.get("next_token_text"),
    }


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


def _sample_summary(
    *,
    sample_id: str,
    sample: JsonDict,
    exact_doc: JsonDict,
    row: JsonDict,
    quality_sample: JsonDict,
    candidate_doc: JsonDict,
) -> JsonDict:
    exact_topk = _topk(exact_doc)
    candidate_topk = _topk(candidate_doc)
    exact_next = _next(exact_doc)
    candidate_next = _next(candidate_doc)
    exact_id = exact_next.get("token_id")
    candidate_id = candidate_next.get("token_id")
    exact_score = _score_for(exact_topk, exact_id)
    candidate_score = _score_for(candidate_topk, candidate_id)
    exact_token_candidate_score = _score_for(candidate_topk, exact_id)
    exact_candidate_delta = None
    if candidate_score is not None and exact_token_candidate_score is not None:
        exact_candidate_delta = candidate_score - exact_token_candidate_score
    distribution = quality_sample.get("reference_distribution")
    candidate_distribution = quality_sample.get("candidate_distribution")
    return {
        "sample_id": sample_id,
        "category": sample.get("category"),
        "prompt": sample.get("prompt"),
        "expected_continuation": sample.get("expected_continuation"),
        "aggregate": quality_sample.get("aggregate", {}),
        "reference_margin": {
            "top1_top2_logit_margin": (distribution or {}).get("top1_top2_logit_margin")
            if isinstance(distribution, dict)
            else None,
            "topk_probability_mass": (distribution or {}).get("topk_probability_mass")
            if isinstance(distribution, dict)
            else None,
        },
        "candidate_margin": {
            "top1_top2_score_margin": (candidate_distribution or {}).get("top1_top2_score_margin")
            if isinstance(candidate_distribution, dict)
            else None,
            "score_sum": (candidate_distribution or {}).get("score_sum") if isinstance(candidate_distribution, dict) else None,
            "topk_score_mass": (candidate_distribution or {}).get("topk_score_mass")
            if isinstance(candidate_distribution, dict)
            else None,
        },
        "exact_next": exact_next,
        "candidate_next": candidate_next,
        "exact_rank_in_candidate_topk": _rank_for(candidate_topk, exact_id),
        "candidate_rank_in_exact_topk": _rank_for(exact_topk, candidate_id),
        "candidate_score_minus_exact_token_score": exact_candidate_delta,
        "exact_topk": exact_topk,
        "candidate_topk": candidate_topk,
        "stage_settings": {
            "template": row.get("template"),
            "candidate_semantics": row.get("candidate_semantics"),
            "softmax_mode": row.get("softmax_mode"),
            "softmax_input_quant_bits": row.get("softmax_input_quant_bits"),
            "softmax_weight_quant_bits": row.get("softmax_weight_quant_bits"),
            "softmax_input_float_format": row.get("softmax_input_float_format"),
            "softmax_weight_float_format": row.get("softmax_weight_float_format"),
            "normalization_mode": row.get("normalization_mode"),
            "normalization_reciprocal_bits": row.get("normalization_reciprocal_bits"),
            "normalization_reciprocal_float_format": row.get("normalization_reciprocal_float_format"),
            "probability_float_format": row.get("probability_float_format"),
            "probability_quant_bits": row.get("probability_quant_bits"),
        },
    }


def _candidate_doc(manifest_sample: JsonDict) -> JsonDict:
    candidate_json = str(manifest_sample.get("candidate_json") or "").strip()
    if not candidate_json:
        raise SystemExit(f"candidate manifest sample missing candidate_json: {manifest_sample}")
    return _load_json(candidate_json)


def _diagnosis(rows: list[JsonDict], focus_samples: list[str]) -> JsonDict:
    non_exact = [row for row in rows if row["template"] != "candidate_onnx_softmax_exact"]
    miss_sets = {
        row["template"]: set(row.get("next_token_mismatch_sample_ids") or [])
        for row in non_exact
    }
    common_misses = set(focus_samples)
    for misses in miss_sets.values():
        common_misses &= misses
    all_topk_safe = all(not row.get("topk_miss_sample_ids") for row in non_exact)
    q8_exact = next((row for row in non_exact if row["template"] == "grid_approx_pwl_in_q8_w_q8_norm_exact"), None)
    q8_recip = next((row for row in non_exact if row["template"] == "grid_approx_pwl_in_q8_w_q8_norm_recip_q10"), None)
    bf16 = next((row for row in non_exact if row["template"] == "grid_approx_pwl_bf16_path"), None)
    same_miss_pattern = len({tuple(sorted(misses)) for misses in miss_sets.values()}) <= 1
    if same_miss_pattern and all_topk_safe and q8_exact is not None:
        cause = "shared_pwl_softmax_or_logit_margin_sensitivity"
        conclusion = (
            "The same exact-token misses appear across bf16 reciprocal, q8 exact normalization, "
            "and q8 reciprocal q10. Normalization precision is unlikely to be the root cause."
        )
    elif q8_recip is not None and bf16 is not None and miss_sets.get(q8_recip["template"]) != miss_sets.get(bf16["template"]):
        cause = "format_or_normalization_sensitive"
        conclusion = "q8 reciprocal and bf16 rows differ on sample misses; keep format/normalization in scope."
    else:
        cause = "mixed_or_inconclusive"
        conclusion = "The focused rows do not collapse to a single obvious failure mechanism."
    return {
        "cause": cause,
        "summary": conclusion,
        "all_topk_safe": all_topk_safe,
        "same_miss_pattern": same_miss_pattern,
        "common_next_token_misses": sorted(common_misses),
        "recommended_next_step": (
            "Run a focused PWL/logit sensitivity ladder on the failing arithmetic and sequence samples, "
            "with exact top-k retained as the broad gate and exact next-token treated as a margin stress signal."
        ),
    }


def _write_md(doc: JsonDict, path: Path) -> None:
    lines = [
        "# Decoder PWL Failure Diagnosis",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- decision: `{doc['diagnosis']['cause']}`",
        f"- summary: {doc['diagnosis']['summary']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Template Summary",
        "",
        "| template | next-token | top-k | misses |",
        "|---|---:|---:|---|",
    ]
    for row in doc["template_summaries"]:
        misses = ", ".join(row["next_token_mismatch_sample_ids"]) or "none"
        lines.append(
            f"| `{row['template']}` | {row['next_token_matches']}/{row['sample_count']} | "
            f"{row['topk_matches']}/{row['sample_count']} | {misses} |"
        )
    lines.extend(["", "## Focus Samples", ""])
    for sample in doc["focus_samples"]:
        lines.append(f"### `{sample['sample_id']}`")
        lines.append("")
        lines.append(f"- category: `{sample.get('category')}`")
        lines.append(f"- prompt: `{sample.get('prompt')}`")
        exact_next = sample["exact_next"]
        lines.append(f"- exact next: `{exact_next.get('token_text')}` ({exact_next.get('token_id')})")
        for template in sample["templates"]:
            candidate_next = template["candidate_next"]
            aggregate = template.get("aggregate", {})
            delta = template.get("candidate_score_minus_exact_token_score")
            delta_text = "" if delta is None else f", candidate-minus-exact-score={delta:.6g}"
            lines.append(
                f"- `{template['template']}`: next `{candidate_next.get('token_text')}` "
                f"({candidate_next.get('token_id')}), exact_rank_in_candidate_topk="
                f"{template.get('exact_rank_in_candidate_topk')}, next_match="
                f"{aggregate.get('next_token_id_match')}, topk_contains="
                f"{aggregate.get('topk_contains_reference_id')}{delta_text}"
            )
        lines.append("")
    lines.extend(["## Control Samples", ""])
    for sample in doc["control_samples"]:
        lines.append(f"- `{sample['sample_id']}` ({sample.get('category')}): exact `{sample['exact_next'].get('token_text')}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", required=True)
    parser.add_argument("--sample-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--template", action="append", default=[])
    parser.add_argument("--focus-sample", action="append", default=[])
    parser.add_argument("--control-sample", action="append", default=[])
    args = parser.parse_args()

    sweep_path = _resolve(args.sweep)
    sweep = _load_json(sweep_path)
    samples = _samples_by_id(args.sample_file)
    rows_by_template = _sweep_rows_by_template(sweep)
    templates = args.template or DEFAULT_TEMPLATES
    focus_samples = args.focus_sample or DEFAULT_FOCUS_SAMPLES
    control_samples = args.control_sample or DEFAULT_CONTROL_SAMPLES
    missing_templates = [template for template in templates if template not in rows_by_template]
    if missing_templates:
        raise SystemExit(f"templates missing from sweep: {missing_templates}")
    missing_samples = [sample_id for sample_id in [*focus_samples, *control_samples] if sample_id not in samples]
    if missing_samples:
        raise SystemExit(f"samples missing from sample file: {missing_samples}")

    exact_row = rows_by_template["candidate_onnx_softmax_exact"]
    exact_manifest = _manifest_samples_by_id(exact_row["candidate_manifest"])
    quality_by_template = {
        template: _quality_samples_by_id(rows_by_template[template]["quality_json"])
        for template in templates
    }
    manifest_by_template = {
        template: _manifest_samples_by_id(rows_by_template[template]["candidate_manifest"])
        for template in templates
    }

    template_summaries: list[JsonDict] = []
    selected_rows: list[JsonDict] = []
    for template in templates:
        row = rows_by_template[template]
        sample_count = int(row.get("sample_count") or 0)
        next_rate = float(row.get("next_token_id_match_rate") or 0.0)
        topk_rate = float(row.get("topk_contains_reference_id_rate") or 0.0)
        summary = {
            "template": template,
            "candidate_semantics": row.get("candidate_semantics"),
            "sample_count": sample_count,
            "next_token_matches": round(next_rate * sample_count),
            "topk_matches": round(topk_rate * sample_count),
            "next_token_match_rate": next_rate,
            "topk_contains_reference_id_rate": topk_rate,
            "next_token_mismatch_sample_ids": row.get("next_token_mismatch_sample_ids") or [],
            "topk_miss_sample_ids": row.get("topk_miss_sample_ids") or [],
        }
        template_summaries.append(summary)
        selected_rows.append({**row, **summary})

    def build_sample(sample_id: str) -> JsonDict:
        exact_doc = _candidate_doc(exact_manifest[sample_id])
        exact_next = _next(exact_doc)
        out: JsonDict = {
            "sample_id": sample_id,
            "category": samples[sample_id].get("category"),
            "prompt": samples[sample_id].get("prompt"),
            "expected_continuation": samples[sample_id].get("expected_continuation"),
            "exact_next": exact_next,
            "exact_topk": _topk(exact_doc),
            "templates": [],
        }
        for template in templates:
            if template == "candidate_onnx_softmax_exact":
                continue
            candidate_doc = _candidate_doc(manifest_by_template[template][sample_id])
            quality_sample = quality_by_template[template][sample_id]
            out["templates"].append(
                {
                    "template": template,
                    **_sample_summary(
                        sample_id=sample_id,
                        sample=samples[sample_id],
                        exact_doc=exact_doc,
                        row=rows_by_template[template],
                        quality_sample=quality_sample,
                        candidate_doc=candidate_doc,
                    ),
                }
            )
        return out

    doc: JsonDict = {
        "version": 0.1,
        "source_sweep": _portable(sweep_path),
        "sample_file": _portable(_resolve(args.sample_file)),
        "focus_sample_ids": focus_samples,
        "control_sample_ids": control_samples,
        "templates": templates,
        "template_summaries": template_summaries,
        "diagnosis": _diagnosis(selected_rows, focus_samples),
        "focus_samples": [build_sample(sample_id) for sample_id in focus_samples],
        "control_samples": [build_sample(sample_id) for sample_id in control_samples],
    }
    out_path = _resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = _resolve(args.out_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    _write_md(doc, md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
