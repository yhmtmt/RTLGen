#!/usr/bin/env python3
"""Summarize broad-distribution quality for decoder PWL survivor candidates."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

PRIMARY_SURVIVORS = {
    "grid_approx_pwl_float_norm_exact",
    "grid_approx_pwl_in_q12_w_q12_norm_exact",
}
PRECISION_CONTROLS = {
    "grid_approx_pwl_fp16_norm_exact",
    "grid_approx_pwl_bf16_norm_exact",
    "grid_approx_pwl_in_q10_w_q10_norm_exact",
    "grid_approx_pwl_in_q8_w_q8_norm_exact",
}


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


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sample_categories(sample_file: str | Path) -> dict[str, str]:
    categories: dict[str, str] = {}
    for row in _load_jsonl(sample_file):
        sample_id = str(row.get("sample_id") or "").strip()
        if sample_id:
            categories[sample_id] = str(row.get("category") or "uncategorized")
    return categories


def _template_family(row: JsonDict) -> str:
    template = str(row.get("template") or "")
    if template == "candidate_onnx_softmax_exact":
        return "exact_reference_proxy"
    if str(row.get("softmax_mode") or "exact") == "approx_pwl":
        return "pwl"
    return "exact_softmax_variant"


def _role(template: str) -> str:
    if template in PRIMARY_SURVIVORS:
        return "primary_survivor_candidate"
    if template in PRECISION_CONTROLS:
        return "precision_control"
    if template.startswith("grid_exact_"):
        return "exact_softmax_control"
    return "reference_proxy" if template == "candidate_onnx_softmax_exact" else "other"


def _category_counts(sample_ids: list[str], categories: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for sample_id in sample_ids:
        counts[categories.get(sample_id, "uncategorized")] += 1
    return dict(sorted(counts.items()))


def _row_summary(row: JsonDict, categories: dict[str, str]) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate"))
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate"))
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    next_misses = [str(v) for v in row.get("next_token_mismatch_sample_ids") or []]
    topk_misses = [str(v) for v in row.get("topk_miss_sample_ids") or []]
    distribution = row.get("distribution") if isinstance(row.get("distribution"), dict) else {}
    exact_safe = sample_count > 0 and next_matches == sample_count and topk_matches == sample_count
    topk_safe = sample_count > 0 and topk_matches == sample_count
    template = str(row.get("template") or "")
    return {
        "template": template,
        "role": _role(template),
        "family": _template_family(row),
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_match_rate": next_rate,
        "topk_contains_reference_id_rate": topk_rate,
        "next_token_mismatch_sample_ids": next_misses,
        "topk_miss_sample_ids": topk_misses,
        "next_token_miss_categories": _category_counts(next_misses, categories),
        "topk_miss_categories": _category_counts(topk_misses, categories),
        "exact_safe": exact_safe,
        "topk_safe": topk_safe,
        "gate": "exact_safe_survivor" if exact_safe else "topk_safe_not_exact" if topk_safe else "blocked_quality",
        "softmax_mode": row.get("softmax_mode", "exact"),
        "logit_quant_bits": row.get("logit_quant_bits", 0),
        "softmax_input_quant_bits": row.get("softmax_input_quant_bits", 0),
        "softmax_input_float_format": row.get("softmax_input_float_format", ""),
        "softmax_weight_quant_bits": row.get("softmax_weight_quant_bits", 0),
        "softmax_weight_float_format": row.get("softmax_weight_float_format", ""),
        "normalization_mode": row.get("normalization_mode", "exact"),
        "candidate_score_sum_min": distribution.get("candidate_score_sum_min"),
        "candidate_top1_top2_score_margin_min": distribution.get("candidate_top1_top2_score_margin_min"),
    }


def _diagnosis(rows: list[JsonDict]) -> JsonDict:
    by_template = {str(row["template"]): row for row in rows}
    q12 = by_template.get("grid_approx_pwl_in_q12_w_q12_norm_exact")
    float_pwl = by_template.get("grid_approx_pwl_float_norm_exact")
    fp16_pwl = by_template.get("grid_approx_pwl_fp16_norm_exact")
    q10 = by_template.get("grid_approx_pwl_in_q10_w_q10_norm_exact")
    q8 = by_template.get("grid_approx_pwl_in_q8_w_q8_norm_exact")
    exact_fp16 = by_template.get("grid_exact_softmax_fp16_path")

    exact_safe_survivors = [
        row["template"]
        for row in (float_pwl, q12, fp16_pwl)
        if row is not None and row["exact_safe"]
    ]
    all_rows_topk_safe = all(row["topk_safe"] for row in rows if row["family"] != "exact_reference_proxy")

    if q12 and q12["exact_safe"] and float_pwl and float_pwl["exact_safe"]:
        if fp16_pwl and fp16_pwl["exact_safe"]:
            decision = "q12_and_fp16_pwl_broad_safe"
            recommended = "Move q12 and fp16 PWL candidates into RTL/PPA calibration, with q10/q8 retained only as lower-cost risk controls."
        else:
            decision = "q12_pwl_broad_safe_fp16_borderline"
            recommended = "Promote q12 PWL to RTL/PPA calibration and inspect fp16 PWL misses before treating it as a survivor."
    elif q12 and q12["topk_safe"]:
        decision = "q12_pwl_topk_safe_not_exact"
        recommended = "Treat q12 PWL as rank-stable but margin-sensitive; inspect misses by category before hardware spend."
    else:
        decision = "pwl_survivors_not_broad_safe"
        recommended = "Do not promote q12/fp16 PWL to hardware selection yet; return to curve or precision design."

    controls = {
        "q10_exact_safe": bool(q10 and q10["exact_safe"]),
        "q8_exact_safe": bool(q8 and q8["exact_safe"]),
        "exact_fp16_exact_safe": bool(exact_fp16 and exact_fp16["exact_safe"]),
    }
    return {
        "decision": decision,
        "exact_safe_survivors": exact_safe_survivors,
        "all_rows_topk_safe": all_rows_topk_safe,
        "recommended_next_step": recommended,
        "controls": controls,
        "summary": (
            "This broad distribution check reuses the expanded v2 prompt set to test whether the focused "
            "PWL/logit survivor rows remain exact-safe outside the six-sample ladder. q10/q8 and bf16 rows "
            "remain in the grid as negative precision controls, while exact fp16/q12 rows keep logit-format "
            "effects visible."
        ),
    }


def _write_md(doc: JsonDict, path: Path) -> None:
    lines = [
        "# Decoder PWL Survivor Distribution",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- sample_file: `{doc['sample_file']}`",
        f"- decision: `{doc['diagnosis']['decision']}`",
        f"- summary: {doc['diagnosis']['summary']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Template Summary",
        "",
        "| template | role | next-token | top-k | gate | miss categories |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in doc["template_summaries"]:
        categories = ", ".join(f"{key}:{value}" for key, value in row["next_token_miss_categories"].items()) or "none"
        lines.append(
            "| `{template}` | `{role}` | {next}/{samples} | {topk}/{samples} | `{gate}` | {categories} |".format(
                template=row["template"],
                role=row["role"],
                next=row["next_token_matches"],
                topk=row["topk_matches"],
                samples=row["sample_count"],
                gate=row["gate"],
                categories=categories,
            )
        )
    lines.extend(["", "## Exact-Safe Survivors", ""])
    survivors = doc["diagnosis"]["exact_safe_survivors"]
    if survivors:
        for template in survivors:
            lines.append(f"- `{template}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Miss Details", ""])
    for row in doc["template_summaries"]:
        if not row["next_token_mismatch_sample_ids"]:
            continue
        lines.append(f"### `{row['template']}`")
        lines.append("")
        for sample_id in row["next_token_mismatch_sample_ids"]:
            category = doc["sample_categories"].get(sample_id, "uncategorized")
            lines.append(f"- `{sample_id}` ({category})")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--sample-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    sweep_path = _resolve(args.sweep)
    sweep = _load_json(sweep_path)
    templates = sweep.get("templates")
    if not isinstance(templates, list):
        raise SystemExit("sweep JSON must contain templates list")
    categories = _sample_categories(args.sample_file)
    rows = [_row_summary(row, categories) for row in templates if isinstance(row, dict)]
    doc = {
        "version": 0.1,
        "source_sweep": _portable(sweep_path),
        "sample_file": _portable(_resolve(args.sample_file)),
        "sample_count": len(categories),
        "sample_categories": categories,
        "template_summaries": rows,
        "diagnosis": _diagnosis(rows),
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
