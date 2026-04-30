#!/usr/bin/env python3
"""Summarize decoder quantization sweeps by comparable dimensions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

DEFAULT_FP_SWEEP = Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json")
DEFAULT_DISTRIBUTION_SWEEP = Path(
    "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_distribution_robustness_v1.json"
)
DEFAULT_Q8_NORM_FRONTIER = Path(
    "runs/datasets/llm_decoder_eval_tiny_v1/decoder_q8_norm_frontier__l2_decoder_q8_normalization_frontier_v1.json"
)

DIMENSION_LABELS = {
    "logit_format": "Logit Format",
    "softmax_input_format": "Softmax Input Format",
    "softmax_weight_format": "Softmax Weight Format",
    "normalization_reciprocal_format": "Normalization Reciprocal Format",
    "probability_output_format": "Probability Output Format",
    "approximate_pwl_probability_path": "Approximate PWL Probability Path",
    "reference": "Reference",
    "other": "Other",
}


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _quality(row: JsonDict) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate"))
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate"))
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    exact_safe = sample_count > 0 and next_matches == sample_count and topk_matches == sample_count
    topk_safe = sample_count > 0 and topk_matches == sample_count
    if exact_safe:
        gate = "exact_safe"
    elif topk_safe:
        gate = "topk_safe_only"
    else:
        gate = "blocked"
    return {
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_match_rate": next_rate,
        "topk_contains_reference_rate": topk_rate,
        "next_token_mismatch_sample_ids": row.get("next_token_mismatch_sample_ids") or [],
        "topk_miss_sample_ids": row.get("topk_miss_sample_ids") or [],
        "gate": gate,
        "exact_safe": exact_safe,
        "topk_safe": topk_safe,
    }


def _dimension(row: JsonDict) -> str:
    template = str(row.get("template") or "")
    if template == "candidate_onnx_softmax_exact":
        return "reference"
    if template.startswith("grid_logits_") or _as_int(row.get("logit_quant_bits")):
        return "logit_format"
    if template.startswith("grid_softmax_input_"):
        return "softmax_input_format"
    if template.startswith("grid_softmax_weight_"):
        return "softmax_weight_format"
    if template.startswith("grid_norm_recip_"):
        return "normalization_reciprocal_format"
    if template.startswith("grid_prob_") or _as_int(row.get("probability_quant_bits")):
        return "probability_output_format"
    if template.startswith("grid_approx_pwl_"):
        return "approximate_pwl_probability_path"
    return "other"


def _format_descriptor(row: JsonDict) -> str:
    parts: list[str] = []
    for key, label in (
        ("logit_quant_bits", "logit_q"),
        ("logit_float_format", "logit"),
        ("softmax_input_quant_bits", "input_q"),
        ("softmax_input_float_format", "input"),
        ("softmax_weight_quant_bits", "weight_q"),
        ("softmax_weight_float_format", "weight"),
        ("normalization_reciprocal_bits", "recip_q"),
        ("normalization_reciprocal_float_format", "recip"),
        ("probability_quant_bits", "prob_q"),
        ("probability_float_format", "prob"),
    ):
        value = row.get(key)
        if value in (None, "", 0):
            continue
        if key.endswith("_quant_bits") or key == "normalization_reciprocal_bits":
            parts.append(f"{label}{value}")
        else:
            parts.append(f"{label}={value}")
    mode = str(row.get("normalization_mode") or "").strip()
    if mode and mode != "exact":
        parts.append(f"norm={mode}")
    return ", ".join(parts) or "reference"


def _row_record(row: JsonDict, *, source: str) -> JsonDict:
    return {
        "source": source,
        "template": str(row.get("template") or ""),
        "dimension": _dimension(row),
        "format_descriptor": _format_descriptor(row),
        "candidate_semantics": row.get("candidate_semantics", ""),
        "quality": _quality(row),
    }


def _dimension_summary(rows: list[JsonDict]) -> JsonDict:
    exact_safe = [row for row in rows if row["quality"]["exact_safe"]]
    topk_only = [row for row in rows if row["quality"]["topk_safe"] and not row["quality"]["exact_safe"]]
    blocked = [row for row in rows if not row["quality"]["topk_safe"]]
    return {
        "row_count": len(rows),
        "exact_safe_count": len(exact_safe),
        "topk_safe_only_count": len(topk_only),
        "blocked_count": len(blocked),
        "exact_safe_templates": [row["template"] for row in exact_safe],
        "topk_safe_only_templates": [row["template"] for row in topk_only],
        "blocked_templates": [row["template"] for row in blocked],
    }


def _group_dimensions(rows: list[JsonDict]) -> list[JsonDict]:
    grouped: dict[str, list[JsonDict]] = {}
    for row in rows:
        grouped.setdefault(str(row["dimension"]), []).append(row)
    out: list[JsonDict] = []
    for name, items in grouped.items():
        items = sorted(
            items,
            key=lambda row: (
                row["quality"]["gate"] != "exact_safe",
                row["quality"]["gate"] != "topk_safe_only",
                row["source"],
                row["template"],
            ),
        )
        out.append(
            {
                "dimension": name,
                "label": DIMENSION_LABELS.get(name, name),
                "comparison_scope": "within_dimension_only",
                "summary": _dimension_summary(items),
                "rows": items,
            }
        )
    out.sort(key=lambda row: (row["dimension"] in {"reference", "other"}, row["label"]))
    return out


def _q8_norm_summary(path: Path | None) -> JsonDict | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    rows = payload.get("ranked_rows")
    if not isinstance(rows, list):
        return None
    measured = [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("normalization"), dict)
        and str(row["normalization"].get("rank_source") or "").startswith("measured_")
    ]
    return {
        "source": str(path),
        "decision": payload.get("decision", {}),
        "measured_rows": [
            {
                "template": row.get("template"),
                "rank": row.get("rank"),
                "rank_source": row["normalization"].get("rank_source"),
                "ppa_metrics": row["normalization"].get("ppa_metrics"),
            }
            for row in measured
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Quantization Outline",
        "",
        f"- fp_sweep: `{payload['source_artifacts']['fp_format_sweep']}`",
        f"- distribution_sweep: `{payload['source_artifacts']['distribution_robustness_sweep']}`",
        f"- q8_norm_frontier: `{payload['source_artifacts']['q8_norm_frontier'] or ''}`",
        "",
        "## Interpretation",
        "",
    ]
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Comparable Dimensions", ""])
    for dimension in payload["dimensions"]:
        lines.append(f"### {dimension['label']}")
        lines.append("")
        summary = dimension["summary"]
        lines.append(
            "- scope: `{}`; rows: {}; exact-safe: {}; top-k-only: {}; blocked: {}".format(
                dimension["comparison_scope"],
                summary["row_count"],
                summary["exact_safe_count"],
                summary["topk_safe_only_count"],
                summary["blocked_count"],
            )
        )
        lines.append("")
        lines.append("| source | template | descriptor | gate | next-token | top-k | misses |")
        lines.append("|---|---|---|---|---:|---:|---|")
        for row in dimension["rows"]:
            quality = row["quality"]
            misses = ", ".join(quality["next_token_mismatch_sample_ids"] or quality["topk_miss_sample_ids"]) or ""
            lines.append(
                "| `{source}` | `{template}` | {descriptor} | `{gate}` | {next}/{samples} | {topk}/{samples} | {misses} |".format(
                    source=row["source"],
                    template=row["template"],
                    descriptor=row["format_descriptor"],
                    gate=quality["gate"],
                    next=quality["next_token_matches"],
                    topk=quality["topk_matches"],
                    samples=quality["sample_count"],
                    misses=misses,
                )
            )
        lines.append("")
    if payload.get("q8_norm_frontier"):
        lines.extend(["## Measured Q8 Normalization PPA", ""])
        for row in payload["q8_norm_frontier"]["measured_rows"]:
            metrics = row.get("ppa_metrics") or {}
            lines.append(
                "- `{}` rank {} via `{}`: critical_path_ns={}, die_area={}, total_power_mw={}".format(
                    row.get("template"),
                    row.get("rank"),
                    row.get("rank_source"),
                    metrics.get("critical_path_ns"),
                    metrics.get("die_area"),
                    metrics.get("total_power_mw"),
                )
            )
    lines.extend(["", "## Next Step", ""])
    for item in payload["next_step"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(
    *,
    fp_sweep_path: Path = DEFAULT_FP_SWEEP,
    distribution_sweep_path: Path = DEFAULT_DISTRIBUTION_SWEEP,
    q8_norm_frontier_path: Path | None = DEFAULT_Q8_NORM_FRONTIER,
) -> JsonDict:
    fp_sweep = _load_json(fp_sweep_path)
    distribution_sweep = _load_json(distribution_sweep_path)
    records: list[JsonDict] = []
    for source, sweep in (("fp_format", fp_sweep), ("distribution", distribution_sweep)):
        rows = sweep.get("templates")
        if not isinstance(rows, list):
            raise SystemExit(f"{source} sweep JSON must contain templates list")
        records.extend(_row_record(row, source=source) for row in rows if isinstance(row, dict))
    q8_norm = _q8_norm_summary(q8_norm_frontier_path)
    return {
        "version": 0.1,
        "source_artifacts": {
            "fp_format_sweep": str(fp_sweep_path),
            "distribution_robustness_sweep": str(distribution_sweep_path),
            "q8_norm_frontier": str(q8_norm_frontier_path) if q8_norm_frontier_path is not None else None,
        },
        "scope_note": (
            "This report groups decoder quantization evidence by comparable dimension. It must not be read "
            "as one global ranking across logits, normalization, probability storage, and approximate PWL paths."
        ),
        "interpretation": [
            "bf16/fp16 probability and reciprocal software paths preserve next-token and top-k on the current fp-format and distribution sweeps.",
            "fixed q8 probability output storage is blocked on the distribution robustness sweep, while q8/q6 logit quantization remains exact-safe there.",
            "fp8 probability storage is not a current frontier candidate: e5m2 drops samples and e4m3 is blocked in both sweeps.",
            "q8 reciprocal and bf16 reciprocal normalization now have measured integrated PPA for the current row-8 Nangate45 datapath framing.",
        ],
        "dimensions": _group_dimensions(records),
        "q8_norm_frontier": q8_norm,
        "next_step": [
            "Use the measured q8 reciprocal and bf16 reciprocal datapaths as the immediate hardware frontier.",
            "Broaden distribution coverage before treating these exact-safe rows as generally robust across weights and prompts.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fp-sweep", default=str(DEFAULT_FP_SWEEP), help="decoder fp-format sweep JSON")
    ap.add_argument("--distribution-sweep", default=str(DEFAULT_DISTRIBUTION_SWEEP), help="decoder distribution sweep JSON")
    ap.add_argument("--q8-norm-frontier", default=str(DEFAULT_Q8_NORM_FRONTIER), help="q8 normalization frontier JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown path")
    args = ap.parse_args()
    report = build_report(
        fp_sweep_path=Path(args.fp_sweep),
        distribution_sweep_path=Path(args.distribution_sweep),
        q8_norm_frontier_path=Path(args.q8_norm_frontier) if args.q8_norm_frontier else None,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
