#!/usr/bin/env python3
"""Break down the two exact-safe decoder PWL frontier candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

FRONTIER_TEMPLATES = (
    "grid_approx_pwl_bf16_path",
    "grid_approx_pwl_in_q8_w_q8_norm_exact",
)

COST_MODEL = {
    "name": "decoder_pwl_frontier_detail_planning_proxy_v1",
    "source": "hand_written_planning_proxy_not_literature_backed",
    "unit": "heuristic_planning_units",
    "calibration_status": "uncalibrated",
    "ppa_balance": (
        "The detail score is a decomposition aid, not an independent timing, power, and "
        "area model. It folds datapath width, table size, and normalization risk into one "
        "planning scalar."
    ),
    "intended_use": (
        "Identify which PWL decoder block should receive RTLGen/OpenROAD calibration next; "
        "do not use the score as hardware acceptance evidence."
    ),
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
    if fmt in {"bf16", "fp16"}:
        return 16
    if fmt.startswith("fp8"):
        return 8
    return 32


def _quality(row: JsonDict) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate"))
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate"))
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    exact_safe = sample_count > 0 and next_matches == sample_count and topk_matches == sample_count
    return {
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_match_rate": next_rate,
        "topk_contains_reference_rate": topk_rate,
        "exact_safe": exact_safe,
        "gate": "exact_safe_survivor" if exact_safe else "blocked_quality",
    }


def _previous_cost_by_template(cost_proxy: JsonDict | None) -> dict[str, JsonDict]:
    if not cost_proxy:
        return {}
    rows = cost_proxy.get("ranked_candidates")
    if not isinstance(rows, list):
        return {}
    result: dict[str, JsonDict] = {}
    for row in rows:
        if isinstance(row, dict) and str(row.get("template") or "") in FRONTIER_TEMPLATES:
            result[str(row["template"])] = row
    return result


def _normalization_model(row: JsonDict) -> JsonDict:
    mode = str(row.get("normalization_mode") or "").strip()
    reciprocal_float = str(row.get("normalization_reciprocal_float_format") or "").strip()
    if mode == "exact":
        return {
            "mode": "exact",
            "implementation": "sum_plus_exact_divide",
            "relative_cost_units": 52.0,
            "unit": COST_MODEL["unit"],
            "calibration_status": COST_MODEL["calibration_status"],
            "integration_risk": "high",
            "risk_reason": "Exact normalization preserves quality but carries a divider-like path that can dominate the otherwise smaller q8 PWL datapath.",
        }
    if mode == "reciprocal_float" and reciprocal_float == "bf16":
        return {
            "mode": "reciprocal_float",
            "implementation": "bf16_reciprocal_multiply",
            "relative_cost_units": 22.0,
            "unit": COST_MODEL["unit"],
            "calibration_status": COST_MODEL["calibration_status"],
            "integration_risk": "medium",
            "risk_reason": "The reciprocal path is cheaper in this planning model, but it requires a bf16-compatible reciprocal/multiply integration point.",
        }
    return {
        "mode": mode or "unknown",
        "implementation": "unclassified",
        "relative_cost_units": 36.0,
        "unit": COST_MODEL["unit"],
        "calibration_status": COST_MODEL["calibration_status"],
        "integration_risk": "unknown",
        "risk_reason": "The normalization path is outside the current two-candidate frontier model.",
    }


def _candidate_model(row: JsonDict, previous_costs: dict[str, JsonDict]) -> JsonDict:
    template = str(row.get("template") or "")
    input_width = _width_from_row(row, prefix="softmax_input")
    weight_width = _width_from_row(row, prefix="softmax_weight")
    coeffs_per_segment = 2
    segment_count = 16
    coefficient_width = weight_width
    table_bits = segment_count * coeffs_per_segment * coefficient_width
    multiplier_output_width = input_width + weight_width
    accumulator_width = max(input_width, weight_width) + 6
    table_units = table_bits / 32.0
    interpolate_units = (multiplier_output_width + accumulator_width) / 4.0
    normalization = _normalization_model(row)
    format_bridge_units = 12.0 if "bf16" in template else 5.0
    probability_write_units = 4.0
    exact_quality_penalty = 0.0 if _quality(row)["exact_safe"] else 1000.0
    total = (
        table_units
        + interpolate_units
        + float(normalization["relative_cost_units"])
        + format_bridge_units
        + probability_write_units
        + exact_quality_penalty
    )
    previous = previous_costs.get(template)
    role = "primary_candidate" if template == "grid_approx_pwl_bf16_path" else "alternate_frontier"
    return {
        "template": template,
        "candidate_semantics": row.get("candidate_semantics"),
        "role": role,
        "quality": _quality(row),
        "data_format": {
            "softmax_input_width_bits": input_width,
            "softmax_weight_width_bits": weight_width,
            "probability_output": "fp32_contract_output",
        },
        "lut_table": {
            "segment_count": segment_count,
            "coefficients_per_segment": coeffs_per_segment,
            "coefficient_width_bits": coefficient_width,
            "table_bits": table_bits,
            "relative_cost_units": round(table_units, 3),
        },
        "interpolate_datapath": {
            "multiplier_input_width_bits": [input_width, weight_width],
            "multiplier_output_width_bits": multiplier_output_width,
            "accumulator_width_bits": accumulator_width,
            "relative_cost_units": round(interpolate_units, 3),
        },
        "normalization_path": normalization,
        "integration_risk": {
            "level": normalization["integration_risk"],
            "reason": normalization["risk_reason"],
        },
        "score_terms": {
            "table_units": round(table_units, 3),
            "interpolate_units": round(interpolate_units, 3),
            "normalization_units": normalization["relative_cost_units"],
            "format_bridge_units": format_bridge_units,
            "probability_write_units": probability_write_units,
            "quality_penalty": exact_quality_penalty,
        },
        "frontier_detail_score": round(total, 3),
        "previous_survivor_cost_proxy": {
            "rank": previous.get("rank"),
            "relative_cost_units": (previous.get("cost_proxy") or {}).get("relative_cost_units"),
        }
        if previous
        else None,
    }


def _frontier_rows(sweep: JsonDict) -> dict[str, JsonDict]:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain a templates list")
    by_template = {
        str(row.get("template") or ""): row
        for row in rows
        if isinstance(row, dict) and str(row.get("template") or "") in FRONTIER_TEMPLATES
    }
    missing = [template for template in FRONTIER_TEMPLATES if template not in by_template]
    if missing:
        raise SystemExit(f"missing frontier template rows: {', '.join(missing)}")
    return by_template


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder PWL Frontier Detail",
        "",
        f"- source_sweep: `{payload['source_sweep']}`",
        f"- source_cost_proxy: `{payload['source_cost_proxy'] or ''}`",
        f"- decision: `{payload['frontier_decision']['decision']}`",
        f"- primary_candidate: `{payload['frontier_decision']['primary_candidate']}`",
        f"- alternate_candidate: `{payload['frontier_decision']['alternate_candidate']}`",
        f"- cost_model_source: `{payload['cost_model']['source']}`",
        f"- cost_model_unit: `{payload['cost_model']['unit']}`",
        f"- rtlgen_calibration_proposal: `{payload['cost_model']['rtlgen_calibration_proposal']}`",
        "",
        "## Cost Model Provenance",
        "",
        payload["cost_model"]["ppa_balance"],
        "",
        payload["cost_model"]["intended_use"],
        "",
        "## Frontier Breakdown",
        "",
        "| candidate | role | quality | table bits | multiplier out | accumulator | normalization | detail score | previous cost | risk |",
        "|---|---|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in payload["frontier_candidates"]:
        prev = row.get("previous_survivor_cost_proxy") or {}
        lines.append(
            "| `{template}` | `{role}` | {next}/{samples}, {topk}/{samples} | {table_bits} | {mult} | {acc} | `{norm}` | {score:.3f} | {prev_cost} | `{risk}` |".format(
                template=row["template"],
                role=row["role"],
                next=row["quality"]["next_token_matches"],
                topk=row["quality"]["topk_matches"],
                samples=row["quality"]["sample_count"],
                table_bits=row["lut_table"]["table_bits"],
                mult=row["interpolate_datapath"]["multiplier_output_width_bits"],
                acc=row["interpolate_datapath"]["accumulator_width_bits"],
                norm=row["normalization_path"]["implementation"],
                score=row["frontier_detail_score"],
                prev_cost=prev.get("relative_cost_units", ""),
                risk=row["integration_risk"]["level"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["frontier_decision"]["reason"],
            "",
            "## Next Experiment",
            "",
        ]
    )
    for item in payload["next_experiment"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(*, sweep_path: Path, cost_proxy_path: Path | None = None) -> JsonDict:
    sweep = _load_json(sweep_path)
    cost_proxy = _load_json(cost_proxy_path) if cost_proxy_path is not None and cost_proxy_path.exists() else None
    previous_costs = _previous_cost_by_template(cost_proxy)
    source_rows = _frontier_rows(sweep)
    candidates = [_candidate_model(source_rows[template], previous_costs) for template in FRONTIER_TEMPLATES]
    candidates.sort(key=lambda row: (row["role"] != "primary_candidate", row["frontier_detail_score"]))
    for rank, row in enumerate(candidates, start=1):
        row["frontier_rank"] = rank

    primary = "grid_approx_pwl_bf16_path"
    alternate = "grid_approx_pwl_in_q8_w_q8_norm_exact"
    return {
        "version": 0.1,
        "source_sweep": str(sweep_path),
        "source_cost_proxy": str(cost_proxy_path) if cost_proxy_path is not None else None,
        "frontier_scope": {
            "included_templates": list(FRONTIER_TEMPLATES),
            "quality_gate": "both candidates must pass exact next-token and top-k on every prompt-stress sample",
            "scope_note": (
                "This is a focused planning breakdown for the two exact-safe PWL candidates. "
                "It is not RTL, OpenROAD PPA, or final hardware acceptance. The detail "
                "scores are uncalibrated heuristic planning units."
            ),
        },
        "cost_model": COST_MODEL,
        "frontier_decision": {
            "decision": "deepen_primary_keep_alternate",
            "primary_candidate": primary,
            "alternate_candidate": alternate,
            "reason": (
                "The q8 PWL row has the smaller table and interpolation datapath, but its exact normalization "
                "path is the dominant open implementation cost. The bf16 PWL row remains the primary immediate "
                "anchor because the prior survivor cost proxy ranked it first and this detailed model isolates "
                "normalization as the main reason to keep q8 as a close alternate rather than discard it."
            ),
        },
        "frontier_candidates": candidates,
        "next_experiment": [
            "Prototype cost estimates for a bf16 reciprocal PWL decoder softmax block and a q8 PWL exact-normalization block with the same row/token contract.",
            "Add a q8 PWL reciprocal or bounded-normalization variant only if the quality sweep can keep 24/24 next-token and top-k on the prompt-stress set.",
            "Escalate the primary candidate to RTL/OpenROAD only after the normalization path is represented explicitly rather than folded into a scalar proxy.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Break down the exact-safe decoder PWL frontier candidates")
    ap.add_argument("--sweep", required=True, help="decoder survivor prompt-stress sweep JSON")
    ap.add_argument("--cost-proxy", help="optional prior survivor cost proxy JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown report path")
    args = ap.parse_args()

    report = build_report(
        sweep_path=Path(args.sweep),
        cost_proxy_path=Path(args.cost_proxy) if args.cost_proxy else None,
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
