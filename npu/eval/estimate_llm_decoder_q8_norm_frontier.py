#!/usr/bin/env python3
"""Summarize q8 PWL normalization frontier quality and cost tradeoffs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

BASELINE_Q8_EXACT = "grid_approx_pwl_in_q8_w_q8_norm_exact"
BF16_ANCHOR = "grid_approx_pwl_bf16_path"
Q8_PREFIX = "grid_approx_pwl_in_q8_w_q8_norm_recip_q"

COST_MODEL = {
    "name": "decoder_q8_normalization_planning_proxy_v1",
    "source": "hand_written_planning_proxy_not_literature_backed",
    "unit": "heuristic_planning_units",
    "calibration_status": "uncalibrated",
    "ppa_balance": (
        "The score is a single planning scalar. It does not independently balance timing, "
        "power, and area, and it must not be read as Nangate45 PPA."
    ),
    "intended_use": (
        "Choose the next RTLGen/OpenROAD calibration target after quality-gated decoder "
        "sweeps; do not use it as hardware acceptance evidence."
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
        "exact_safe": exact_safe,
        "topk_safe": topk_safe,
        "gate": gate,
    }


def _normalization_cost(row: JsonDict) -> float:
    mode = str(row.get("normalization_mode") or "").strip()
    if mode == "exact":
        return 52.0
    if mode == "reciprocal_quantized":
        bits = _as_int(row.get("normalization_reciprocal_bits"), 10)
        return 10.0 + 0.75 * bits
    if mode == "reciprocal_float":
        fmt = str(row.get("normalization_reciprocal_float_format") or "").strip()
        return 22.0 if fmt == "bf16" else 28.0
    return 40.0


def _row_record(row: JsonDict) -> JsonDict:
    template = str(row.get("template") or "")
    quality = _quality(row)
    norm_cost = _normalization_cost(row)
    if template == BF16_ANCHOR:
        role = "bf16_primary_anchor"
    elif template == BASELINE_Q8_EXACT:
        role = "q8_exact_normalization_baseline"
    elif template.startswith(Q8_PREFIX):
        role = "q8_reciprocal_candidate"
    else:
        role = "reference_or_context"
    return {
        "template": template,
        "candidate_semantics": row.get("candidate_semantics"),
        "role": role,
        "quality": quality,
        "normalization": {
            "mode": row.get("normalization_mode", "exact"),
            "reciprocal_bits": row.get("normalization_reciprocal_bits", 0),
            "reciprocal_float_format": row.get("normalization_reciprocal_float_format", ""),
            "relative_cost_units": round(norm_cost, 3),
            "unit": COST_MODEL["unit"],
            "calibration_status": COST_MODEL["calibration_status"],
        },
        "frontier_score": round(norm_cost + (0.0 if quality["exact_safe"] else 1000.0), 3),
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder q8 Normalization Frontier",
        "",
        f"- source_sweep: `{payload['source_sweep']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- selected_candidate: `{payload['decision']['selected_candidate'] or ''}`",
        f"- reason: {payload['decision']['reason']}",
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
        "## Quality And Normalization Cost",
        "",
        "| template | role | gate | next-token | top-k | norm mode | recip bits | norm cost |",
        "|---|---|---|---:|---:|---|---:|---:|",
    ]
    for row in payload["ranked_rows"]:
        quality = row["quality"]
        norm = row["normalization"]
        lines.append(
            "| `{template}` | `{role}` | `{gate}` | {next}/{samples} | {topk}/{samples} | `{mode}` | {bits} | {cost:.3f} |".format(
                template=row["template"],
                role=row["role"],
                gate=quality["gate"],
                next=quality["next_token_matches"],
                topk=quality["topk_matches"],
                samples=quality["sample_count"],
                mode=norm["mode"],
                bits=norm["reciprocal_bits"] or "",
                cost=norm["relative_cost_units"],
            )
        )
    lines.extend(["", "## Blocked Rows", ""])
    blocked = [row for row in payload["ranked_rows"] if not row["quality"]["exact_safe"]]
    if not blocked:
        lines.append("- none")
    for row in blocked:
        quality = row["quality"]
        lines.append(
            "- `{}`: next misses `{}`, top-k misses `{}`".format(
                row["template"],
                ", ".join(quality["next_token_mismatch_sample_ids"]) or "none",
                ", ".join(quality["topk_miss_sample_ids"]) or "none",
            )
        )
    lines.extend(["", "## Next Step", ""])
    for item in payload["next_step"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(*, sweep_path: Path) -> JsonDict:
    sweep = _load_json(sweep_path)
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain a templates list")
    records = [_row_record(row) for row in rows if isinstance(row, dict)]
    interesting = [
        row
        for row in records
        if row["template"] in {BF16_ANCHOR, BASELINE_Q8_EXACT} or row["template"].startswith(Q8_PREFIX)
    ]
    missing = [template for template in (BF16_ANCHOR, BASELINE_Q8_EXACT) if template not in {row["template"] for row in interesting}]
    if missing:
        raise SystemExit(f"missing required frontier rows: {', '.join(missing)}")
    reciprocal_survivors = [
        row
        for row in interesting
        if row["role"] == "q8_reciprocal_candidate" and row["quality"]["exact_safe"]
    ]
    reciprocal_survivors.sort(
        key=lambda row: (
            row["normalization"]["relative_cost_units"],
            _as_int(row["normalization"]["reciprocal_bits"]),
            row["template"],
        )
    )
    if reciprocal_survivors:
        selected = reciprocal_survivors[0]
        decision = {
            "decision": "q8_reciprocal_candidate_survived",
            "selected_candidate": selected["template"],
            "reason": (
                f"{selected['template']} preserved the exact prompt-stress gate with lower modeled "
                "normalization cost than q8 exact normalization. It should be costed against the bf16 anchor next."
            ),
        }
    else:
        decision = {
            "decision": "keep_q8_exact_or_bf16_anchor",
            "selected_candidate": None,
            "reason": (
                "No q8 reciprocal-normalization row preserved both next-token and top-k on every prompt-stress sample. "
                "Keep q8 exact normalization as the q8 quality baseline and bf16 reciprocal PWL as the primary anchor."
            ),
        }
    ranked = sorted(
        interesting,
        key=lambda row: (
            not row["quality"]["exact_safe"],
            row["frontier_score"],
            row["template"],
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
    return {
        "version": 0.1,
        "source_sweep": str(sweep_path),
        "frontier_scope": {
            "rough_grid": sweep.get("rough_grid"),
            "quality_gate": "candidate must match next-token and top-k for every prompt-stress sample",
            "scope_note": (
                "This is a focused q8 PWL normalization frontier. It tests reciprocal-normalization "
                "precision as a replacement for q8 exact normalization; it is not RTL or OpenROAD PPA. "
                "The normalization cost values are uncalibrated heuristic planning units."
            ),
        },
        "cost_model": COST_MODEL,
        "decision": decision,
        "ranked_rows": ranked,
        "next_step": [
            "If a q8 reciprocal row survives, compare it against bf16 reciprocal PWL with an RTL/OpenROAD-oriented block estimate.",
            "If no q8 reciprocal row survives, keep q8 exact normalization only as a quality baseline and move the implementation frontier to bf16 reciprocal PWL.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize q8 PWL normalization frontier quality/cost tradeoffs")
    ap.add_argument("--sweep", required=True, help="q8 normalization frontier sweep JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown report path")
    args = ap.parse_args()
    report = build_report(sweep_path=Path(args.sweep))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
