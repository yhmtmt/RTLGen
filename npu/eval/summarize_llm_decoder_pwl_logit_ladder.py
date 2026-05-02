#!/usr/bin/env python3
"""Summarize a focused decoder PWL/logit sensitivity ladder sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
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


def _rows_by_template(sweep: JsonDict) -> dict[str, JsonDict]:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain templates list")
    return {str(row.get("template") or ""): row for row in rows if isinstance(row, dict)}


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


def _rank_for(topk: list[JsonDict], token_id: Any) -> int | None:
    for index, row in enumerate(topk, start=1):
        if row.get("token_id") == token_id:
            return index
    return None


def _template_family(row: JsonDict) -> str:
    if str(row.get("template") or "") == "candidate_onnx_softmax_exact":
        return "exact_reference_proxy"
    if str(row.get("softmax_mode") or "exact") == "approx_pwl":
        return "pwl"
    return "exact_softmax_variant"


def _row_summary(row: JsonDict, focus_samples: list[str], control_samples: list[str]) -> JsonDict:
    sample_count = int(row.get("sample_count") or 0)
    next_rate = float(row.get("next_token_id_match_rate") or 0.0)
    topk_rate = float(row.get("topk_contains_reference_id_rate") or 0.0)
    misses = [str(v) for v in row.get("next_token_mismatch_sample_ids") or []]
    topk_misses = [str(v) for v in row.get("topk_miss_sample_ids") or []]
    focus_misses = [sample_id for sample_id in focus_samples if sample_id in misses]
    control_misses = [sample_id for sample_id in control_samples if sample_id in misses]
    return {
        "template": row.get("template"),
        "family": _template_family(row),
        "sample_count": sample_count,
        "next_token_matches": round(next_rate * sample_count),
        "topk_matches": round(topk_rate * sample_count),
        "next_token_match_rate": next_rate,
        "topk_contains_reference_id_rate": topk_rate,
        "focus_misses": focus_misses,
        "control_misses": control_misses,
        "topk_misses": topk_misses,
        "softmax_mode": row.get("softmax_mode", "exact"),
        "logit_quant_bits": row.get("logit_quant_bits", 0),
        "softmax_input_quant_bits": row.get("softmax_input_quant_bits", 0),
        "softmax_input_float_format": row.get("softmax_input_float_format", ""),
        "softmax_weight_quant_bits": row.get("softmax_weight_quant_bits", 0),
        "softmax_weight_float_format": row.get("softmax_weight_float_format", ""),
        "normalization_mode": row.get("normalization_mode", "exact"),
        "normalization_reciprocal_bits": row.get("normalization_reciprocal_bits", 0),
        "normalization_reciprocal_float_format": row.get("normalization_reciprocal_float_format", ""),
        "candidate_score_sum_min": (row.get("distribution") or {}).get("candidate_score_sum_min")
        if isinstance(row.get("distribution"), dict)
        else None,
        "candidate_top1_top2_score_margin_min": (row.get("distribution") or {}).get(
            "candidate_top1_top2_score_margin_min"
        )
        if isinstance(row.get("distribution"), dict)
        else None,
    }


def _diagnosis(summaries: list[JsonDict], focus_samples: list[str]) -> JsonDict:
    by_template = {str(row["template"]): row for row in summaries}
    focus_set = set(focus_samples)

    exact_variants = [
        row
        for row in summaries
        if row["family"] == "exact_softmax_variant"
    ]
    pwl_float = by_template.get("grid_approx_pwl_float_norm_exact")
    pwl_q12 = by_template.get("grid_approx_pwl_in_q12_w_q12_norm_exact")
    pwl_q8 = by_template.get("grid_approx_pwl_in_q8_w_q8_norm_exact")
    exact_q12 = by_template.get("grid_exact_logits_q12")
    exact_variants_focus_safe = all(not row["focus_misses"] for row in exact_variants)
    pwl_float_focus_safe = bool(pwl_float and not pwl_float["focus_misses"])
    pwl_float_misses_focus = bool(pwl_float and set(pwl_float["focus_misses"]) == focus_set)
    pwl_q12_focus_safe = bool(pwl_q12 and not pwl_q12["focus_misses"])
    pwl_q8_misses_focus = bool(pwl_q8 and set(pwl_q8["focus_misses"]) == focus_set)
    exact_q12_focus_safe = bool(exact_q12 and not exact_q12["focus_misses"])
    all_topk_safe = all(not row["topk_misses"] for row in summaries if row["family"] != "exact_reference_proxy")

    if pwl_float_focus_safe and pwl_q12_focus_safe and exact_q12_focus_safe and pwl_q8_misses_focus:
        cause = "softmax_input_weight_precision_margin_sensitivity"
        summary = (
            "The unquantized PWL row and q12 PWL row preserve both focus samples, while q8 PWL flips both. "
            "Exact-softmax q10/q8 and bf16 variants also flip margin-sensitive focus samples. The immediate "
            "blocker is low-precision softmax input/weight or logit representation under tiny margins, not "
            "the PWL curve itself or reciprocal normalization."
        )
        next_step = (
            "Promote q12 or fp16-style PWL rows to the next broad distribution check and estimate their "
            "hardware cost before accepting q8/bf16 exact-next behavior."
        )
    elif exact_variants_focus_safe and pwl_float_misses_focus:
        cause = "core_pwl_curve_or_logit_margin_sensitivity"
        summary = (
            "Exact-softmax logit and float-format variants preserve the focus samples, while the unquantized PWL "
            "path still flips both exact next tokens. The immediate blocker is the PWL curve under tiny logit "
            "margins, not q8 input/weight quantization or reciprocal normalization."
        )
        next_step = (
            "Prototype a denser or range-adapted PWL exp curve around the failing shifted-logit intervals, "
            "then rerun this ladder before spending more effort on reciprocal precision."
        )
    elif exact_variants_focus_safe and not pwl_float_misses_focus and pwl_q8_misses_focus:
        cause = "pwl_quantization_sensitivity"
        summary = (
            "The float PWL path preserves the focus samples, but q8 PWL flips them. The next knob is PWL "
            "input/weight precision rather than the reciprocal path."
        )
        next_step = "Narrow the PWL input/weight bit-width boundary and map the lowest exact-safe PWL quantized row."
    elif not exact_variants_focus_safe:
        cause = "logit_or_exact_softmax_format_sensitivity"
        summary = "At least one exact-softmax logit or float-format variant flips a focus sample; keep logit format in scope."
        next_step = "Separate logit quantization from PWL approximation with a wider prompt distribution before hardware selection."
    else:
        cause = "mixed_or_inconclusive"
        summary = "The ladder did not isolate a single failure mechanism."
        next_step = "Inspect per-sample top-k score deltas before choosing the next approximation family."

    return {
        "cause": cause,
        "summary": summary,
        "recommended_next_step": next_step,
        "all_topk_safe": all_topk_safe,
        "exact_variants_focus_safe": exact_variants_focus_safe,
        "exact_q12_focus_safe": exact_q12_focus_safe,
        "pwl_float_focus_safe": pwl_float_focus_safe,
        "pwl_float_misses_focus": pwl_float_misses_focus,
        "pwl_q12_focus_safe": pwl_q12_focus_safe,
        "pwl_q8_misses_focus": pwl_q8_misses_focus,
    }


def _sample_outcomes(
    *,
    sample_ids: list[str],
    samples_by_id: dict[str, JsonDict],
    rows: list[JsonDict],
    exact_manifest: dict[str, JsonDict],
    manifest_by_template: dict[str, dict[str, JsonDict]],
    quality_by_template: dict[str, dict[str, JsonDict]],
) -> list[JsonDict]:
    out: list[JsonDict] = []
    for sample_id in sample_ids:
        exact_doc = _candidate_doc(exact_manifest[sample_id])
        exact_next = _next(exact_doc)
        exact_id = exact_next.get("token_id")
        sample_doc: JsonDict = {
            "sample_id": sample_id,
            "category": samples_by_id[sample_id].get("category"),
            "prompt": samples_by_id[sample_id].get("prompt"),
            "expected_continuation": samples_by_id[sample_id].get("expected_continuation"),
            "exact_next": exact_next,
            "templates": [],
        }
        for row in rows:
            template = str(row.get("template") or "")
            if template == "candidate_onnx_softmax_exact":
                continue
            candidate_doc = _candidate_doc(manifest_by_template[template][sample_id])
            quality_sample = quality_by_template[template][sample_id]
            candidate_next = _next(candidate_doc)
            aggregate = dict(quality_sample.get("aggregate", {}) or {})
            sample_doc["templates"].append(
                {
                    "template": template,
                    "family": _template_family(row),
                    "candidate_next": candidate_next,
                    "next_token_id_match": aggregate.get("next_token_id_match"),
                    "topk_contains_reference_id": aggregate.get("topk_contains_reference_id"),
                    "exact_rank_in_candidate_topk": _rank_for(_topk(candidate_doc), exact_id),
                }
            )
        out.append(sample_doc)
    return out


def _write_md(doc: JsonDict, path: Path) -> None:
    lines = [
        "# Decoder PWL Logit Sensitivity Ladder",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- decision: `{doc['diagnosis']['cause']}`",
        f"- summary: {doc['diagnosis']['summary']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Template Summary",
        "",
        "| template | family | next-token | top-k | focus misses | control misses |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in doc["template_summaries"]:
        focus = ", ".join(row["focus_misses"]) or "none"
        control = ", ".join(row["control_misses"]) or "none"
        lines.append(
            f"| `{row['template']}` | {row['family']} | {row['next_token_matches']}/{row['sample_count']} | "
            f"{row['topk_matches']}/{row['sample_count']} | {focus} | {control} |"
        )
    lines.extend(["", "## Focus Samples", ""])
    for sample in doc["focus_samples"]:
        lines.append(f"### `{sample['sample_id']}`")
        lines.append("")
        lines.append(f"- prompt: `{sample.get('prompt')}`")
        exact_next = sample["exact_next"]
        lines.append(f"- exact next: `{exact_next.get('token_text')}` ({exact_next.get('token_id')})")
        for template in sample["templates"]:
            if template["next_token_id_match"]:
                continue
            candidate_next = template["candidate_next"]
            lines.append(
                f"- `{template['template']}`: next `{candidate_next.get('token_text')}` "
                f"({candidate_next.get('token_id')}), exact_rank_in_candidate_topk="
                f"{template.get('exact_rank_in_candidate_topk')}, topk_contains="
                f"{template.get('topk_contains_reference_id')}"
            )
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", required=True)
    parser.add_argument("--sample-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--focus-sample", action="append", default=[])
    parser.add_argument("--control-sample", action="append", default=[])
    args = parser.parse_args()

    sweep_path = _resolve(args.sweep)
    sweep = _load_json(sweep_path)
    rows_by_template = _rows_by_template(sweep)
    rows = [row for row in sweep.get("templates", []) if isinstance(row, dict)]
    samples = {str(sample["sample_id"]): sample for sample in _load_jsonl(args.sample_file)}
    focus_samples = args.focus_sample or DEFAULT_FOCUS_SAMPLES
    control_samples = args.control_sample or DEFAULT_CONTROL_SAMPLES
    missing_samples = [sample_id for sample_id in [*focus_samples, *control_samples] if sample_id not in samples]
    if missing_samples:
        raise SystemExit(f"samples missing from sample file: {missing_samples}")
    if "candidate_onnx_softmax_exact" not in rows_by_template:
        raise SystemExit("sweep missing candidate_onnx_softmax_exact row")

    exact_manifest = _manifest_samples_by_id(rows_by_template["candidate_onnx_softmax_exact"]["candidate_manifest"])
    manifest_by_template = {
        str(row["template"]): _manifest_samples_by_id(row["candidate_manifest"])
        for row in rows
    }
    quality_by_template = {
        str(row["template"]): _quality_samples_by_id(row["quality_json"])
        for row in rows
    }

    template_summaries = [_row_summary(row, focus_samples, control_samples) for row in rows]
    doc: JsonDict = {
        "version": 0.1,
        "source_sweep": _portable(sweep_path),
        "sample_file": _portable(_resolve(args.sample_file)),
        "rough_grid": sweep.get("rough_grid"),
        "focus_sample_ids": focus_samples,
        "control_sample_ids": control_samples,
        "diagnosis": _diagnosis(template_summaries, focus_samples),
        "template_summaries": template_summaries,
        "focus_samples": _sample_outcomes(
            sample_ids=focus_samples,
            samples_by_id=samples,
            rows=rows,
            exact_manifest=exact_manifest,
            manifest_by_template=manifest_by_template,
            quality_by_template=quality_by_template,
        ),
        "control_samples": _sample_outcomes(
            sample_ids=control_samples,
            samples_by_id=samples,
            rows=rows,
            exact_manifest=exact_manifest,
            manifest_by_template=manifest_by_template,
            quality_by_template=quality_by_template,
        ),
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
