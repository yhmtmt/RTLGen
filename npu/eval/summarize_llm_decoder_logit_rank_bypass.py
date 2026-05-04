#!/usr/bin/env python3
"""Summarize greedy/top-k decoder quality for raw-logit rank bypass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

EXACT_TEMPLATE = "candidate_onnx_softmax_exact"
BYPASS_TEMPLATE = "candidate_onnx_logit_rank_bypass"
DEFAULT_TIE_RANK_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json"
)


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


def _template_row(sweep: JsonDict, template: str) -> JsonDict:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain a templates list")
    for row in rows:
        if isinstance(row, dict) and str(row.get("template") or "") == template:
            return row
    raise SystemExit(f"missing required template row: {template}")


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
        "next_token_mismatch_sample_ids": row.get("next_token_mismatch_sample_ids") or [],
        "topk_miss_sample_ids": row.get("topk_miss_sample_ids") or [],
        "exact_safe": exact_safe,
    }


def _best_ppa(path: Path | None) -> JsonDict | None:
    if path is None or not path.exists():
        return None
    payload = _load_json(path)
    rows = []
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        metrics_ref = proposal.get("metrics_ref")
        metrics = proposal.get("metric_summary")
        if not isinstance(metrics_ref, dict) or not isinstance(metrics, dict):
            continue
        if str(metrics_ref.get("status") or "") != "ok":
            continue
        row = {
            "metrics_ref": metrics_ref,
            "metrics": {
                "critical_path_ns": _as_float(metrics.get("critical_path_ns")),
                "die_area": _as_float(metrics.get("die_area")),
                "total_power_mw": _as_float(metrics.get("total_power_mw")),
            },
            "selection_reason": proposal.get("selection_reason", ""),
        }
        rows.append(row)
    if not rows:
        return None
    rows.sort(key=lambda row: (
        row["metrics"]["critical_path_ns"],
        row["metrics"]["die_area"],
        row["metrics"]["total_power_mw"],
    ))
    return rows[0]


def build_report(*, sweep_path: Path, rank_ppa_path: Path | None = DEFAULT_TIE_RANK_PPA) -> JsonDict:
    sweep = _load_json(sweep_path)
    exact = _template_row(sweep, EXACT_TEMPLATE)
    bypass = _template_row(sweep, BYPASS_TEMPLATE)
    exact_quality = _quality(exact)
    bypass_quality = _quality(bypass)
    rank_ppa = _best_ppa(rank_ppa_path)
    exact_safe = bypass_quality["exact_safe"]
    if exact_safe:
        decision = "logit_rank_bypass_exact_safe"
        reason = (
            "Raw-logit ranking matches the reference next-token and top-k gate, so greedy/top-k generation "
            "does not need softmax, reciprocal normalization, or probability quantization on this workload."
        )
    else:
        decision = "logit_rank_bypass_blocked"
        reason = "Raw-logit ranking did not preserve the reference next-token/top-k gate."
    return {
        "version": 0.1,
        "source_sweep": str(sweep_path),
        "rough_grid": sweep.get("rough_grid"),
        "task": sweep.get("task", "greedy_next_token"),
        "decision": {
            "decision": decision,
            "reason": reason,
            "selected_candidate": BYPASS_TEMPLATE if exact_safe else None,
            "reference_candidate": EXACT_TEMPLATE,
        },
        "quality": {
            "exact_softmax": exact_quality,
            "logit_rank_bypass": bypass_quality,
        },
        "bypass_scope": {
            "generation_modes": ["greedy_next_token", "topk_ranking", "beam_candidate_ranking"],
            "not_valid_for": ["temperature_sampling", "top_p_sampling", "probability_reporting"],
            "removed_datapaths": [
                "softmax_exp_or_pwl",
                "softmax_sum_normalization",
                "reciprocal_normalization",
                "probability_quantization",
            ],
            "kept_datapaths": ["logit_transform", "topk_or_argmax_rank"],
        },
        "rank_datapath_proxy": {
            "status": "upper_bound_from_score_tie_rank" if rank_ppa is not None else "missing_rank_ppa",
            "source": str(rank_ppa_path) if rank_ppa_path is not None else None,
            "note": (
                "The existing score/logit tie-rank block is a conservative rank-like upper bound because "
                "raw-logit ranking needs only one comparison key. A dedicated logit-only top-k block should "
                "be measured before final array-level PPA claims."
            ),
            "ppa": rank_ppa,
        },
        "next_step": [
            "Use logit-rank bypass as the greedy/top-k architecture path if the evaluator result stays exact-safe.",
            "Open a dedicated Layer 1 logit-only top-k/argmax datapath measurement before full array-level PPA comparison.",
            "Keep approximate softmax work for sampling modes where calibrated probabilities are required.",
        ],
    }


def _write_markdown(path: Path, report: JsonDict) -> None:
    decision = report["decision"]
    q = report["quality"]
    proxy = report["rank_datapath_proxy"]
    ppa = (proxy.get("ppa") or {}).get("metrics") or {}
    lines = [
        "# Decoder Logit-Rank Bypass",
        "",
        f"- source_sweep: `{report['source_sweep']}`",
        f"- decision: `{decision['decision']}`",
        f"- selected_candidate: `{decision['selected_candidate'] or ''}`",
        f"- reason: {decision['reason']}",
        "",
        "## Quality",
        "",
        "| candidate | next-token | top-k | exact-safe | misses |",
        "|---|---:|---:|---|---|",
    ]
    for label, row in (("exact_softmax", q["exact_softmax"]), ("logit_rank_bypass", q["logit_rank_bypass"])):
        misses = ", ".join(row["next_token_mismatch_sample_ids"] or row["topk_miss_sample_ids"]) or "none"
        lines.append(
            f"| `{label}` | {row['next_token_matches']}/{row['sample_count']} | "
            f"{row['topk_matches']}/{row['sample_count']} | `{row['exact_safe']}` | {misses} |"
        )
    lines.extend(
        [
            "",
            "## Bypass Scope",
            "",
            "- valid_for: `greedy_next_token`, `topk_ranking`, `beam_candidate_ranking`",
            "- not_valid_for: `temperature_sampling`, `top_p_sampling`, `probability_reporting`",
            "- removed: `softmax_exp_or_pwl`, `softmax_sum_normalization`, `reciprocal_normalization`, `probability_quantization`",
            "",
            "## Rank Datapath Proxy",
            "",
            f"- status: `{proxy['status']}`",
            f"- source: `{proxy['source'] or ''}`",
            f"- critical_path_ns: `{ppa.get('critical_path_ns', '')}`",
            f"- die_area: `{ppa.get('die_area', '')}`",
            f"- total_power_mw: `{ppa.get('total_power_mw', '')}`",
            f"- note: {proxy['note']}",
            "",
            "## Next Step",
            "",
        ]
    )
    for item in report["next_step"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize raw-logit rank bypass quality")
    ap.add_argument("--sweep", required=True, help="decoder quality sweep JSON")
    ap.add_argument("--rank-ppa", default=str(DEFAULT_TIE_RANK_PPA), help="rank-like datapath PPA proxy JSON")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown path")
    args = ap.parse_args()
    report = build_report(
        sweep_path=Path(args.sweep),
        rank_ppa_path=Path(args.rank_ppa) if args.rank_ppa else None,
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
