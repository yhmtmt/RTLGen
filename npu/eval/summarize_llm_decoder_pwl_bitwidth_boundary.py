#!/usr/bin/env python3
"""Summarize the decoder PWL integer bit-width boundary on a distribution sweep."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


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


def _category_counts(sample_ids: list[str], categories: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for sample_id in sample_ids:
        counts[categories.get(sample_id, "uncategorized")] += 1
    return dict(sorted(counts.items()))


def _bits_from_template(template: str) -> int | None:
    match = re.search(r"_in_q(\d+)_w_q\1_", template)
    if match:
        return int(match.group(1))
    match = re.search(r"_logits_q(\d+)$", template)
    if match:
        return int(match.group(1))
    return None


def _family(row: JsonDict) -> str:
    template = str(row.get("template") or "")
    if template == "candidate_onnx_softmax_exact":
        return "reference"
    if template == "grid_approx_pwl_float_norm_exact":
        return "unquantized_pwl_control"
    if template == "grid_approx_pwl_bf16_path":
        return "bf16_hardware_anchor"
    if template.startswith("grid_exact_logits_q"):
        return "exact_softmax_logit_control"
    if template.startswith("grid_approx_pwl_in_q"):
        return "pwl_integer_boundary"
    return "other"


def _row_summary(row: JsonDict, categories: dict[str, str]) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate"))
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate"))
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    next_misses = [str(v) for v in row.get("next_token_mismatch_sample_ids") or []]
    topk_misses = [str(v) for v in row.get("topk_miss_sample_ids") or []]
    exact_safe = sample_count > 0 and next_matches == sample_count and topk_matches == sample_count
    topk_safe = sample_count > 0 and topk_matches == sample_count
    template = str(row.get("template") or "")
    return {
        "template": template,
        "family": _family(row),
        "bit_width": _bits_from_template(template),
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
        "gate": "exact_safe" if exact_safe else "topk_safe_only" if topk_safe else "blocked",
        "softmax_input_quant_bits": row.get("softmax_input_quant_bits", 0),
        "softmax_weight_quant_bits": row.get("softmax_weight_quant_bits", 0),
        "softmax_input_float_format": row.get("softmax_input_float_format", ""),
        "softmax_weight_float_format": row.get("softmax_weight_float_format", ""),
        "normalization_mode": row.get("normalization_mode", "exact"),
        "normalization_reciprocal_float_format": row.get("normalization_reciprocal_float_format", ""),
    }


def _diagnosis(rows: list[JsonDict]) -> JsonDict:
    integer_rows = [row for row in rows if row["family"] == "pwl_integer_boundary"]
    exact_safe = sorted((row for row in integer_rows if row["exact_safe"]), key=lambda row: row["bit_width"] or 99)
    topk_safe = sorted((row for row in integer_rows if row["topk_safe"]), key=lambda row: row["bit_width"] or 99)
    minimum_exact = exact_safe[0] if exact_safe else None
    minimum_topk = topk_safe[0] if topk_safe else None
    q12 = next((row for row in integer_rows if row["bit_width"] == 12), None)
    q11 = next((row for row in integer_rows if row["bit_width"] == 11), None)
    q10 = next((row for row in integer_rows if row["bit_width"] == 10), None)
    bf16 = next((row for row in rows if row["template"] == "grid_approx_pwl_bf16_path"), None)

    if minimum_exact is not None and minimum_exact["bit_width"] is not None and minimum_exact["bit_width"] < 12:
        decision = "sub_q12_integer_pwl_survivor"
        recommended = (
            f"Promote q{minimum_exact['bit_width']} PWL to the next PPA calibration before spending more q12 hardware effort."
        )
    elif q12 is not None and q12["exact_safe"]:
        decision = "q12_remains_integer_exact_floor"
        recommended = "Keep q12 as the integer exact-safe floor and prefer bf16/q8 top-k frontier unless exact next-token is required."
    elif minimum_topk is not None:
        decision = "integer_pwl_topk_only"
        recommended = "Treat integer PWL as rank-stable but not exact-safe; do not schedule another integer PPA run yet."
    else:
        decision = "integer_pwl_boundary_blocked"
        recommended = "Return to curve/logit precision design before hardware calibration."

    return {
        "decision": decision,
        "minimum_exact_safe_template": minimum_exact["template"] if minimum_exact else None,
        "minimum_exact_safe_bits": minimum_exact["bit_width"] if minimum_exact else None,
        "minimum_topk_safe_template": minimum_topk["template"] if minimum_topk else None,
        "minimum_topk_safe_bits": minimum_topk["bit_width"] if minimum_topk else None,
        "q10_exact_safe": bool(q10 and q10["exact_safe"]),
        "q11_exact_safe": bool(q11 and q11["exact_safe"]),
        "q12_exact_safe": bool(q12 and q12["exact_safe"]),
        "bf16_gate": bf16["gate"] if bf16 else "missing",
        "recommended_next_step": recommended,
        "summary": (
            "The boundary sweep narrows the integer PWL precision floor after q12 proved exact-safe "
            "but expensive. It compares q10/q11/q12/q13 PWL exact-normalization rows against the "
            "unquantized PWL control and the measured bf16 reciprocal hardware anchor on the same "
            "expanded v2 prompt distribution."
        ),
    }


def _write_md(doc: JsonDict, path: Path) -> None:
    lines = [
        "# Decoder PWL Bit-Width Boundary",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- sample_file: `{doc['sample_file']}`",
        f"- decision: `{doc['diagnosis']['decision']}`",
        f"- minimum_exact_safe_bits: `{doc['diagnosis']['minimum_exact_safe_bits']}`",
        f"- minimum_topk_safe_bits: `{doc['diagnosis']['minimum_topk_safe_bits']}`",
        f"- summary: {doc['diagnosis']['summary']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Template Summary",
        "",
        "| template | family | bits | next-token | top-k | gate | miss categories |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in doc["template_summaries"]:
        categories = ", ".join(f"{key}:{value}" for key, value in row["next_token_miss_categories"].items()) or "none"
        lines.append(
            "| `{template}` | `{family}` | {bits} | {next}/{samples} | {topk}/{samples} | `{gate}` | {categories} |".format(
                template=row["template"],
                family=row["family"],
                bits=row["bit_width"] if row["bit_width"] is not None else "",
                next=row["next_token_matches"],
                topk=row["topk_matches"],
                samples=row["sample_count"],
                gate=row["gate"],
                categories=categories,
            )
        )
    lines.extend(["", "## Exact-Safe Integer Rows", ""])
    survivors = [
        row for row in doc["template_summaries"] if row["family"] == "pwl_integer_boundary" and row["exact_safe"]
    ]
    if survivors:
        for row in sorted(survivors, key=lambda item: item["bit_width"] or 99):
            lines.append(f"- q{row['bit_width']}: `{row['template']}`")
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
