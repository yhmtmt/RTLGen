#!/usr/bin/env python3
"""Summarize q8 PWL normalization frontier quality and PPA tradeoffs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

BASELINE_Q8_EXACT = "grid_approx_pwl_in_q8_w_q8_norm_exact"
BF16_ANCHOR = "grid_approx_pwl_bf16_path"
Q8_PREFIX = "grid_approx_pwl_in_q8_w_q8_norm_recip_q"
DEFAULT_Q8_RECIP_PPA = Path("control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json")
METRIC_KEYS = ("critical_path_ns", "die_area", "total_power_mw")

COST_MODEL = {
    "name": "decoder_q8_normalization_ppa_frontier_v2",
    "source": "rtlgen_openroad_q8_reciprocal_datapath_metrics",
    "unit": "nangate45_physical_metrics",
    "calibration_status": "q8_reciprocal_integrated_datapath_measured",
    "ppa_balance": (
        "Measured q8 reciprocal candidates are ranked lexicographically by critical path, "
        "then area, then power. Exact q8 and bf16 reciprocal normalization remain unmeasured "
        "hardware gaps and are not compared as accepted PPA."
    ),
    "intended_use": (
        "Replace the q8 reciprocal normalization heuristic with merged RTLGen/OpenROAD "
        "datapath evidence while preserving quality gates from the decoder sweep."
    ),
    "rtlgen_calibration_proposal": "prop_l1_decoder_q8_recip_norm_datapath_v1",
    "fallback_source": "hand_written_planning_proxy_used_only_when_ppa_artifact_is_absent",
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


def _metric_summary(row: JsonDict) -> JsonDict:
    summary = row.get("metric_summary")
    if not isinstance(summary, dict):
        return {key: None for key in METRIC_KEYS}
    return {key: _as_float(summary.get(key), default=None) for key in METRIC_KEYS}


def _recip_bits_from_metrics_ref(metrics_ref: JsonDict) -> int | None:
    text = " ".join(str(metrics_ref.get(key) or "") for key in ("metrics_csv", "result_path", "tag"))
    match = re.search(r"recip_q(\d+)", text)
    return int(match.group(1)) if match else None


def _load_q8_recip_ppa(path: Path | None) -> dict[int, JsonDict]:
    if path is None or not path.exists():
        return {}
    payload = _load_json(path)
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        raise SystemExit(f"q8 reciprocal PPA artifact must contain proposals list: {path}")
    rows: dict[int, JsonDict] = {}
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        metrics_ref = proposal.get("metrics_ref")
        if not isinstance(metrics_ref, dict):
            continue
        bits = _recip_bits_from_metrics_ref(metrics_ref)
        metrics = _metric_summary(proposal)
        if bits is None or str(metrics_ref.get("status") or "") != "ok":
            continue
        if any(metrics[key] is None for key in METRIC_KEYS):
            continue
        rows[bits] = {
            "reciprocal_bits": bits,
            "platform": metrics_ref.get("platform"),
            "metrics_ref": metrics_ref,
            "metrics": metrics,
            "selection_reason": proposal.get("selection_reason"),
        }
    return rows


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


def _heuristic_normalization_cost(row: JsonDict) -> float:
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


def _normalization_record(row: JsonDict, *, q8_recip_ppa: dict[int, JsonDict]) -> JsonDict:
    mode = str(row.get("normalization_mode") or "exact").strip()
    bits = _as_int(row.get("normalization_reciprocal_bits"), 0)
    heuristic_cost = _heuristic_normalization_cost(row)
    record: JsonDict = {
        "mode": mode,
        "reciprocal_bits": bits,
        "reciprocal_float_format": row.get("normalization_reciprocal_float_format", ""),
        "heuristic_fallback_units": round(heuristic_cost, 3),
        "heuristic_fallback_unit": "heuristic_planning_units",
        "ppa_metrics": None,
        "metrics_ref": None,
        "rank_source": "unmeasured_gap",
        "rank_key": [2, round(heuristic_cost, 6)],
        "unit": COST_MODEL["unit"],
    }
    if mode == "reciprocal_quantized":
        ppa = q8_recip_ppa.get(bits)
        if ppa is not None:
            metrics = ppa["metrics"]
            record.update(
                {
                    "ppa_metrics": metrics,
                    "metrics_ref": ppa["metrics_ref"],
                    "rank_source": "measured_q8_reciprocal_datapath_ppa",
                    "rank_key": [0] + [float(metrics[key]) for key in METRIC_KEYS],
                    "calibration_status": "integrated_q8_reciprocal_datapath_measured",
                }
            )
            return record
        record.update(
            {
                "rank_source": "heuristic_fallback_missing_q8_reciprocal_ppa",
                "rank_key": [1, round(heuristic_cost, 6)],
                "calibration_status": "missing_integrated_q8_reciprocal_datapath_ppa",
            }
        )
        return record
    if mode == "exact":
        record["calibration_status"] = "unmeasured_exact_normalization_datapath"
    elif mode == "reciprocal_float":
        record["calibration_status"] = "unmeasured_float_reciprocal_datapath"
    else:
        record["calibration_status"] = "unmeasured_normalization_datapath"
    return record


def _row_record(row: JsonDict, *, q8_recip_ppa: dict[int, JsonDict]) -> JsonDict:
    template = str(row.get("template") or "")
    quality = _quality(row)
    normalization = _normalization_record(row, q8_recip_ppa=q8_recip_ppa)
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
        "normalization": normalization,
        "frontier_rank_key": normalization["rank_key"] if quality["exact_safe"] else [9, *normalization["rank_key"]],
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
        "## Quality And Normalization PPA",
        "",
        "| template | role | gate | next-token | top-k | norm mode | recip bits | rank source | critical_path_ns | die_area | total_power_mw |",
        "|---|---|---|---:|---:|---|---:|---|---:|---:|---:|",
    ]
    for row in payload["ranked_rows"]:
        quality = row["quality"]
        norm = row["normalization"]
        metrics = norm.get("ppa_metrics") or {}
        lines.append(
            "| `{template}` | `{role}` | `{gate}` | {next}/{samples} | {topk}/{samples} | `{mode}` | {bits} | `{rank_source}` | {cp} | {area} | {power} |".format(
                template=row["template"],
                role=row["role"],
                gate=quality["gate"],
                next=quality["next_token_matches"],
                topk=quality["topk_matches"],
                samples=quality["sample_count"],
                mode=norm["mode"],
                bits=norm["reciprocal_bits"] or "",
                rank_source=norm["rank_source"],
                cp=metrics.get("critical_path_ns", ""),
                area=metrics.get("die_area", ""),
                power=metrics.get("total_power_mw", ""),
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


def build_report(*, sweep_path: Path, q8_recip_ppa_path: Path | None = DEFAULT_Q8_RECIP_PPA) -> JsonDict:
    sweep = _load_json(sweep_path)
    q8_recip_ppa = _load_q8_recip_ppa(q8_recip_ppa_path)
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain a templates list")
    records = [_row_record(row, q8_recip_ppa=q8_recip_ppa) for row in rows if isinstance(row, dict)]
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
            row["normalization"]["rank_key"],
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
                f"{selected['template']} preserved the exact prompt-stress gate and has the best "
                f"{selected['normalization']['rank_source']} among exact-safe q8 reciprocal candidates. "
                "q8 exact and bf16 reciprocal normalization remain unmeasured hardware gaps."
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
            row["frontier_rank_key"],
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
                "precision as a replacement for q8 exact normalization. q8 reciprocal rows use merged "
                "RTLGen/OpenROAD integrated datapath metrics when the PPA artifact is available; exact "
                "q8 and bf16 normalization paths remain unmeasured."
            ),
        },
        "source_artifacts": {
            "q8_reciprocal_datapath_ppa": str(q8_recip_ppa_path) if q8_recip_ppa_path is not None else None,
            "q8_reciprocal_ppa_bits": sorted(q8_recip_ppa),
        },
        "cost_model": COST_MODEL,
        "decision": decision,
        "ranked_rows": ranked,
        "next_step": [
            "Measure bf16 reciprocal/multiply normalization before making a q8-versus-bf16 hardware decision.",
            "Measure or model q8 exact normalization only if it remains a candidate beyond the reciprocal path.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize q8 PWL normalization frontier quality/PPA tradeoffs")
    ap.add_argument("--sweep", required=True, help="q8 normalization frontier sweep JSON")
    ap.add_argument("--q8-recip-ppa", default=str(DEFAULT_Q8_RECIP_PPA), help="merged q8 reciprocal datapath promotion JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown report path")
    args = ap.parse_args()
    report = build_report(
        sweep_path=Path(args.sweep),
        q8_recip_ppa_path=Path(args.q8_recip_ppa) if args.q8_recip_ppa else None,
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
