#!/usr/bin/env python3
"""Synthesize decoder-normalization cost evidence from merged L1 PPA rows."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

DEFAULT_SWEEP = Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_normalization_frontier_v1.json")
DEFAULT_MULT_PROMOTION = Path("control_plane/shadow_exports/l1_promotions/l1_decoder_norm_q8_recip_mult_calibration_v1_r2.json")
DEFAULT_ADDER_PROMOTION = Path("control_plane/shadow_exports/l1_promotions/l1_decoder_norm_accumulator_adder_calibration_v1_r2.json")
PROPOSAL_ID = "prop_l1_decoder_normalization_arithmetic_calibration_v1"
Q8_PREFIX = "grid_approx_pwl_in_q8_w_q8_norm_recip_q"
Q8_EXACT = "grid_approx_pwl_in_q8_w_q8_norm_exact"
BF16_ANCHOR = "grid_approx_pwl_bf16_path"
METRIC_KEYS = ("critical_path_ns", "die_area", "total_power_mw")


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _block_id(metrics_ref: JsonDict) -> str:
    metrics_csv = str(metrics_ref.get("metrics_csv") or "")
    if not metrics_csv:
        return "unknown"
    return Path(metrics_csv).parent.name.removesuffix("_wrapper")


def _parse_width(block_id: str) -> int | None:
    match = re.search(r"(?:^|_)(?:mult|adder_)?(\d+)u(?:_|$)", block_id)
    return int(match.group(1)) if match else None


def _parse_topology(block_id: str) -> str:
    if block_id.startswith("mult"):
        match = re.match(r"mult\d+u_(.+)", block_id)
        return match.group(1) if match else "unknown"
    if block_id.startswith("adder_"):
        match = re.match(r"adder_([^_]+)_", block_id)
        return match.group(1) if match else "unknown"
    return "unknown"


def _primitive_family(block_id: str) -> str:
    if block_id.startswith("mult"):
        return "multiplier"
    if block_id.startswith("adder"):
        return "adder"
    return "unknown"


def _metric_summary(row: JsonDict) -> JsonDict:
    summary = row.get("metric_summary")
    if not isinstance(summary, dict):
        return {key: None for key in METRIC_KEYS}
    return {key: _as_float(summary.get(key)) for key in METRIC_KEYS}


def _promotion_rows(path: Path) -> list[JsonDict]:
    payload = _load_json(path)
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        raise SystemExit(f"promotion artifact must contain proposals list: {path}")
    rows: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metrics_ref = proposal.get("metrics_ref")
        if not isinstance(metrics_ref, dict):
            continue
        block_id = _block_id(metrics_ref)
        metrics = _metric_summary(proposal)
        rows.append(
            {
                "block_id": block_id,
                "family": _primitive_family(block_id),
                "width_bits": _parse_width(block_id),
                "topology": _parse_topology(block_id),
                "platform": metrics_ref.get("platform"),
                "status": metrics_ref.get("status"),
                "metrics_ref": metrics_ref,
                "metrics": metrics,
                "selection_reason": proposal.get("selection_reason"),
            }
        )
    return rows


def _quality(row: JsonDict) -> JsonDict:
    sample_count = _as_int(row.get("sample_count"))
    next_rate = _as_float(row.get("next_token_id_match_rate")) or 0.0
    topk_rate = _as_float(row.get("topk_contains_reference_id_rate")) or 0.0
    next_matches = round(next_rate * sample_count)
    topk_matches = round(topk_rate * sample_count)
    return {
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "exact_safe": sample_count > 0 and next_matches == sample_count and topk_matches == sample_count,
    }


def _frontier_templates(sweep_path: Path) -> dict[str, JsonDict]:
    sweep = _load_json(sweep_path)
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain a templates list")
    by_template: dict[str, JsonDict] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("template"), str):
            template = row["template"]
            if template in {Q8_EXACT, BF16_ANCHOR} or template.startswith(Q8_PREFIX):
                by_template[template] = row
    missing = [template for template in (Q8_EXACT, BF16_ANCHOR) if template not in by_template]
    if missing:
        raise SystemExit(f"missing required frontier rows: {', '.join(missing)}")
    return by_template


def _ok_nangate45(rows: list[JsonDict]) -> list[JsonDict]:
    return [row for row in rows if row["status"] == "ok" and row["platform"] == "nangate45"]


def _best_row(rows: list[JsonDict], *, family: str, width_bits: int) -> JsonDict:
    matches = [
        row
        for row in _ok_nangate45(rows)
        if row["family"] == family and row["width_bits"] == width_bits and all(row["metrics"][key] is not None for key in METRIC_KEYS)
    ]
    if not matches:
        raise SystemExit(f"missing Nangate45 {family} {width_bits}u primitive evidence")
    return min(matches, key=lambda row: tuple(float(row["metrics"][key]) for key in METRIC_KEYS) + (row["block_id"],))


def _sum_metrics(rows: list[JsonDict]) -> JsonDict:
    return {key: round(sum(float(row["metrics"][key]) for row in rows), 6) for key in METRIC_KEYS}


def _reciprocal_bits(template: str) -> int:
    match = re.search(r"_q(\d+)$", template)
    return int(match.group(1)) if match else 0


def _candidate_rows(
    *,
    templates: dict[str, JsonDict],
    selected_mult16: JsonDict,
    selected_adder64: JsonDict,
) -> list[JsonDict]:
    primitive_combo = [selected_mult16, selected_adder64]
    primitive_sum = _sum_metrics(primitive_combo)
    rows: list[JsonDict] = []
    for template in sorted(templates):
        source = templates[template]
        if template.startswith(Q8_PREFIX):
            rows.append(
                {
                    "template": template,
                    "normalization_path": "q8_reciprocal_quantized",
                    "reciprocal_bits": _reciprocal_bits(template),
                    "quality": _quality(source),
                    "calibration_status": "integer_reciprocal_primitives_calibrated_not_integrated_datapath",
                    "primitive_envelope": {
                        "multiplier_operand_envelope_bits": 16,
                        "accumulator_adder_bits": 64,
                        "note": (
                            "q10/q12/q14/q16 all map to the same current 16-bit multiplier envelope "
                            "and the same accumulator primitive. These L1 metrics therefore do not prove "
                            "a physical PPA advantage for q10 over q12/q14/q16."
                        ),
                    },
                    "selected_primitives": [row["block_id"] for row in primitive_combo],
                    "primitive_sum_proxy": primitive_sum,
                    "unmeasured_gaps": [
                        "integrated normalization datapath routing/control",
                        "pipeline/register placement around reciprocal multiply and accumulation",
                    ],
                }
            )
        elif template == Q8_EXACT:
            rows.append(
                {
                    "template": template,
                    "normalization_path": "q8_exact_normalization",
                    "reciprocal_bits": 0,
                    "quality": _quality(source),
                    "calibration_status": "unmeasured_gap",
                    "selected_primitives": [selected_adder64["block_id"]],
                    "measured_partial_primitives": ["64-bit accumulator adder"],
                    "unmeasured_gaps": ["integer exact divider/reciprocal datapath"],
                }
            )
        elif template == BF16_ANCHOR:
            rows.append(
                {
                    "template": template,
                    "normalization_path": "bf16_reciprocal_pwl_anchor",
                    "reciprocal_bits": 0,
                    "quality": _quality(source),
                    "calibration_status": "unmeasured_gap",
                    "selected_primitives": [],
                    "unmeasured_gaps": [
                        "bf16 reciprocal path",
                        "bf16 multiply/round/convert datapath",
                        "integrated normalization datapath routing/control",
                    ],
                }
            )
    return rows


def _write_markdown(path: Path, payload: JsonDict) -> None:
    selected = payload["selected_primitives"]
    rows = payload["candidate_calibration"]
    lines = [
        "# Decoder Normalization PPA Calibration",
        "",
        f"- calibration_status: `{payload['calibration_status']}`",
        f"- platform: `{payload['platform']}`",
        f"- source_sweep: `{payload['source_sweep']}`",
        f"- proposal: `{payload['proposal_id']}`",
        "",
        "## Selected Primitive Evidence",
        "",
        "| role | block | critical_path_ns | die_area | total_power_mw | metrics_csv |",
        "|---|---|---:|---:|---:|---|",
    ]
    for role, row in selected.items():
        metrics = row["metrics"]
        lines.append(
            "| `{role}` | `{block}` | {cp:.6g} | {area:.6g} | {power:.6g} | `{csv}` |".format(
                role=role,
                block=row["block_id"],
                cp=metrics["critical_path_ns"],
                area=metrics["die_area"],
                power=metrics["total_power_mw"],
                csv=row["metrics_ref"]["metrics_csv"],
            )
        )
    lines.extend(
        [
            "",
            "## Candidate Calibration",
            "",
            "| template | status | exact-safe | reciprocal bits | primitive critical_path_ns sum | primitive area sum | primitive power sum | gaps |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        primitive_sum = row.get("primitive_sum_proxy") or {}
        quality = row["quality"]
        lines.append(
            "| `{template}` | `{status}` | {safe} | {bits} | {cp} | {area} | {power} | {gaps} |".format(
                template=row["template"],
                status=row["calibration_status"],
                safe="yes" if quality["exact_safe"] else "no",
                bits=row["reciprocal_bits"] or "",
                cp=primitive_sum.get("critical_path_ns", ""),
                area=primitive_sum.get("die_area", ""),
                power=primitive_sum.get("total_power_mw", ""),
                gaps=", ".join(f"`{gap}`" for gap in row.get("unmeasured_gaps", [])),
            )
        )
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Step", ""])
    for item in payload["next_step"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_report(
    *,
    sweep_path: Path = DEFAULT_SWEEP,
    mult_promotion_path: Path = DEFAULT_MULT_PROMOTION,
    adder_promotion_path: Path = DEFAULT_ADDER_PROMOTION,
) -> JsonDict:
    mult_rows = _promotion_rows(mult_promotion_path)
    adder_rows = _promotion_rows(adder_promotion_path)
    templates = _frontier_templates(sweep_path)
    selected_mult16 = _best_row(mult_rows, family="multiplier", width_bits=16)
    selected_adder64 = _best_row(adder_rows, family="adder", width_bits=64)
    candidate_rows = _candidate_rows(
        templates=templates,
        selected_mult16=selected_mult16,
        selected_adder64=selected_adder64,
    )
    reciprocal_rows = [row for row in candidate_rows if row["template"].startswith(Q8_PREFIX)]
    identical_recip_metrics = len({json.dumps(row.get("primitive_sum_proxy", {}), sort_keys=True) for row in reciprocal_rows}) <= 1
    return {
        "version": 0.1,
        "proposal_id": PROPOSAL_ID,
        "source_sweep": str(sweep_path),
        "source_artifacts": {
            "multiplier_promotion": str(mult_promotion_path),
            "adder_promotion": str(adder_promotion_path),
        },
        "platform": "nangate45",
        "calibration_status": "partial_integer_reciprocal_primitives_calibrated",
        "scope": {
            "measured": "integer reciprocal multiplier and accumulator/adder primitive PPA from merged L1 rows",
            "not_measured": "full integrated normalization datapath, exact divider, bf16 reciprocal/multiply datapath",
            "score_policy": "No weighted PPA score is emitted; delay, area, and power remain separate axes.",
        },
        "primitive_evidence": {
            "multipliers": mult_rows,
            "adders": adder_rows,
        },
        "selected_primitives": {
            "q8_reciprocal_multiplier_16u": selected_mult16,
            "q8_accumulator_adder_64u": selected_adder64,
        },
        "candidate_calibration": candidate_rows,
        "interpretation": [
            "The q8 reciprocal path now has measured Nangate45 multiplier and accumulator/adder primitive evidence.",
            "The q8 exact-normalization row is still blocked for hardware acceptance by an unmeasured exact divider/reciprocal datapath.",
            "The bf16 reciprocal PWL anchor is still blocked for hardware acceptance by unmeasured bf16 reciprocal and multiply/convert datapaths.",
            (
                "The q8 reciprocal q10/q12/q14/q16 rows share the same measured primitive envelope in this calibration. "
                "Under that envelope, physical PPA does not justify preferring q10 over q12/q14/q16; q10 remains a "
                "quality/minimum-precision choice from the prompt-stress sweep."
            )
            if identical_recip_metrics
            else "The q8 reciprocal rows do not share identical primitive sums; inspect per-row primitive envelopes before ranking.",
        ],
        "next_step": [
            "Use the calibrated primitive axes to plan an integrated q8 reciprocal-normalization datapath measurement.",
            "Do not compare q8 reciprocal against bf16 as a hardware decision until bf16 reciprocal/multiply primitives are also measured.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibrate decoder normalization costs from merged L1 primitive PPA evidence")
    ap.add_argument("--sweep", default=str(DEFAULT_SWEEP), help="q8 normalization frontier sweep JSON")
    ap.add_argument("--mult-promotion", default=str(DEFAULT_MULT_PROMOTION), help="merged multiplier L1 promotion artifact")
    ap.add_argument("--adder-promotion", default=str(DEFAULT_ADDER_PROMOTION), help="merged adder L1 promotion artifact")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown report path")
    args = ap.parse_args()
    report = build_report(
        sweep_path=Path(args.sweep),
        mult_promotion_path=Path(args.mult_promotion),
        adder_promotion_path=Path(args.adder_promotion),
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
