#!/usr/bin/env python3
"""Rank decoder survivor sweep rows with an explicit rough cost proxy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

COST_MODEL = {
    "name": "decoder_survivor_relative_softmax_cost_v1",
    "source": "hand_written_planning_proxy_not_literature_backed",
    "unit": "heuristic_planning_units",
    "calibration_status": "uncalibrated",
    "ppa_balance": (
        "The ranking score is a single planning scalar. It is not derived from papers or "
        "calibrated physical data, and it does not independently optimize timing, power, "
        "and area."
    ),
    "intended_use": (
        "Rank exact-safe decoder survivors well enough to choose the next RTLGen/OpenROAD "
        "calibration target; do not use it as hardware acceptance evidence."
    ),
    "quality_gate": "eligible rows must match next-token and top-k on every prompt-stress sample",
    "rtlgen_calibration_proposal": "prop_l1_decoder_normalization_arithmetic_calibration_v1",
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


def _width_from_row(row: JsonDict, *, prefix: str) -> int:
    quant_bits = _as_int(row.get(f"{prefix}_quant_bits"))
    if quant_bits:
        return quant_bits
    fmt = str(row.get(f"{prefix}_float_format") or "").strip()
    if fmt == "bf16" or fmt == "fp16":
        return 16
    if fmt.startswith("fp8"):
        return 8
    return 32


def _format_width(fmt: str) -> int:
    fmt = fmt.strip()
    if fmt in {"bf16", "fp16"}:
        return 16
    if fmt.startswith("fp8"):
        return 8
    return 32


def _cost_proxy(row: JsonDict) -> JsonDict:
    softmax_mode = str(row.get("softmax_mode") or "").strip()
    normalization_mode = str(row.get("normalization_mode") or "").strip()
    prob_fmt = str(row.get("probability_float_format") or "").strip()
    logit_quant_bits = _as_int(row.get("logit_quant_bits"))

    if softmax_mode == "approx_pwl":
        input_width = _width_from_row(row, prefix="softmax_input")
        weight_width = _width_from_row(row, prefix="softmax_weight")
        pwl_eval = 16.0 + 0.25 * (input_width + weight_width)
        exp_or_pwl_cost = pwl_eval
        softmax_path = "pwl_lut_interpolate"
    else:
        input_width = logit_quant_bits or 32
        weight_width = 0
        exp_or_pwl_cost = 100.0
        softmax_path = "exact_exp"

    if normalization_mode == "reciprocal_quantized":
        norm_bits = _as_int(row.get("normalization_reciprocal_bits"), 10)
        normalization_cost = 8.0 + norm_bits
    elif normalization_mode == "reciprocal_float":
        norm_fmt = str(row.get("normalization_reciprocal_float_format") or "").strip()
        normalization_cost = 18.0 if norm_fmt == "bf16" else 26.0
    else:
        normalization_cost = 30.0

    probability_width = _format_width(prob_fmt)
    probability_write_cost = 2.0 + 0.125 * probability_width
    input_cast_cost = 0.25 * input_width
    relative_cost_units = exp_or_pwl_cost + normalization_cost + probability_write_cost + input_cast_cost

    return {
        "relative_cost_units": round(relative_cost_units, 3),
        "unit": COST_MODEL["unit"],
        "calibration_status": COST_MODEL["calibration_status"],
        "softmax_path": softmax_path,
        "softmax_eval_cost": round(exp_or_pwl_cost, 3),
        "normalization_cost": round(normalization_cost, 3),
        "probability_write_cost": round(probability_write_cost, 3),
        "input_cast_cost": round(input_cast_cost, 3),
        "input_width_bits": input_width,
        "weight_width_bits": weight_width,
        "probability_width_bits": probability_width,
    }


def _quality(row: JsonDict) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate"))
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate"))
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    exact_safe = sample_count > 0 and next_matches == sample_count and topk_matches == sample_count
    topk_safe = sample_count > 0 and topk_matches == sample_count
    if exact_safe:
        gate = "exact_safe_survivor"
    elif topk_safe:
        gate = "topk_safe_not_exact"
    else:
        gate = "blocked_quality"
    return {
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_match_rate": next_rate,
        "topk_contains_reference_rate": topk_rate,
        "next_token_mismatch_sample_ids": row.get("next_token_mismatch_sample_ids") or [],
        "topk_miss_sample_ids": row.get("topk_miss_sample_ids") or [],
        "gate": gate,
        "eligible_for_cost_narrowing": exact_safe,
        "topk_safe": topk_safe,
    }


def _rank_rows(sweep: JsonDict) -> list[JsonDict]:
    templates = sweep.get("templates")
    if not isinstance(templates, list):
        raise SystemExit("sweep JSON must contain a templates list")
    rows: list[JsonDict] = []
    for row in templates:
        if not isinstance(row, dict):
            continue
        quality = _quality(row)
        cost = _cost_proxy(row)
        rank_penalty = 0.0
        if not quality["eligible_for_cost_narrowing"]:
            rank_penalty += 1000.0
        rank_penalty += (1.0 - quality["next_token_match_rate"]) * 100.0
        rows.append(
            {
                "template": row.get("template"),
                "candidate_semantics": row.get("candidate_semantics"),
                "quality": quality,
                "cost_proxy": cost,
                "ranking_score": round(cost["relative_cost_units"] + rank_penalty, 3),
            }
        )
    rows.sort(
        key=lambda row: (
            not bool(row["quality"]["eligible_for_cost_narrowing"]),
            row["ranking_score"],
            str(row["template"]),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Survivor Cost Proxy",
        "",
        f"- source_sweep: `{payload['source_sweep']}`",
        f"- recommendation: `{payload['recommendation']['template']}`",
        f"- reason: {payload['recommendation']['reason']}",
        f"- cost_model_source: `{payload['cost_model']['source']}`",
        f"- cost_model_unit: `{payload['cost_model']['unit']}`",
        f"- rtlgen_calibration_proposal: `{payload['cost_model']['rtlgen_calibration_proposal']}`",
        "",
        "## Cost Model",
        "",
        payload["cost_model"]["scope_note"],
        "",
        payload["cost_model"]["ppa_balance"],
        "",
        payload["cost_model"]["intended_use"],
        "",
        "| rank | template | gate | next-token | top-k | relative cost | softmax path |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for row in payload["ranked_candidates"]:
        quality = row["quality"]
        cost = row["cost_proxy"]
        lines.append(
            "| {rank} | `{template}` | `{gate}` | {next}/{samples} | {topk}/{samples} | {cost:.3f} | `{path}` |".format(
                rank=row["rank"],
                template=row["template"],
                gate=quality["gate"],
                next=quality["next_token_matches"],
                topk=quality["topk_matches"],
                samples=quality["sample_count"],
                cost=cost["relative_cost_units"],
                path=cost["softmax_path"],
            )
        )
    lines.extend(
        [
            "",
            "## Blocked Or Non-Exact Rows",
            "",
        ]
    )
    for row in payload["ranked_candidates"]:
        if row["quality"]["eligible_for_cost_narrowing"]:
            continue
        quality = row["quality"]
        lines.append(
            "- `{}`: gate `{}`, next misses `{}`, top-k misses `{}`".format(
                row["template"],
                quality["gate"],
                ", ".join(quality["next_token_mismatch_sample_ids"]) or "none",
                ", ".join(quality["topk_miss_sample_ids"]) or "none",
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(*, sweep_path: Path) -> JsonDict:
    sweep = _load_json(sweep_path)
    ranked = _rank_rows(sweep)
    eligible = [row for row in ranked if row["quality"]["eligible_for_cost_narrowing"]]
    if not eligible:
        recommendation = {
            "template": None,
            "decision": "block",
            "reason": "No prompt-stress row passed exact next-token and top-k gates.",
        }
    else:
        best = eligible[0]
        recommendation = {
            "template": best["template"],
            "decision": "promote_to_implementation_costing",
            "reason": (
                f"{best['template']} passed exact prompt-stress quality and has the lowest "
                "relative cost among exact-safe survivors in this proxy model."
            ),
        }
    return {
        "version": 0.1,
        "source_sweep": str(sweep_path),
        "cost_model": {
            **COST_MODEL,
            "scope_note": (
                "This is a relative planning proxy for decoder softmax/probability-path implementation cost. "
                "It weights exact exp paths above PWL paths and lower-width datapaths below fp-style datapaths. "
                "It is not RTL, OpenROAD PPA, or final hardware acceptance. The cost values are "
                "uncalibrated heuristic planning units."
            ),
        },
        "recommendation": recommendation,
        "ranked_candidates": ranked,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank decoder survivor sweep rows with a rough cost proxy")
    ap.add_argument("--sweep", required=True, help="decoder survivor prompt-stress sweep JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown report path")
    args = ap.parse_args()

    payload = build_report(sweep_path=Path(args.sweep))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md), "recommendation": payload["recommendation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
