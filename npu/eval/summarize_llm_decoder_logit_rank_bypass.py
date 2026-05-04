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
DEFAULT_LOGIT_RANK_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
)
LEGACY_TIE_RANK_PPA = Path(
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


def _rank_role(row: JsonDict) -> str:
    metrics_ref = row.get("metrics_ref") or {}
    metrics_csv = str(metrics_ref.get("metrics_csv") or "")
    if "_k1_" in metrics_csv or "k1" in metrics_csv:
        return "argmax_k1"
    if "_k4_" in metrics_csv or "k4" in metrics_csv:
        return "topk_k4"
    return "rank"


def _artifact_status(*, path: Path, payload: JsonDict, rows: list[JsonDict]) -> str:
    item_id = str(payload.get("item_id") or "")
    source = f"{path} {item_id}"
    if "logit_rank" in source:
        return "measured_logit_rank_datapath"
    if "tie_rank" in source:
        return "upper_bound_from_score_tie_rank"
    if rows:
        return "measured_rank_datapath"
    return "missing_rank_ppa"


def _ppa_summary(path: Path | None) -> JsonDict | None:
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
        row["role"] = _rank_role(row)
        rows.append(row)
    if not rows:
        return None
    rows.sort(key=lambda row: (
        row["metrics"]["critical_path_ns"],
        row["metrics"]["die_area"],
        row["metrics"]["total_power_mw"],
    ))
    by_role = {str(row["role"]): row for row in rows}
    return {
        "status": _artifact_status(path=path, payload=payload, rows=rows),
        "source": str(path),
        "item_id": payload.get("item_id"),
        "selected": rows[0],
        "argmax": by_role.get("argmax_k1") or rows[0],
        "topk": by_role.get("topk_k4") or rows[0],
        "rows": rows,
    }


def build_report(*, sweep_path: Path, rank_ppa_path: Path | None = DEFAULT_LOGIT_RANK_PPA) -> JsonDict:
    sweep = _load_json(sweep_path)
    exact = _template_row(sweep, EXACT_TEMPLATE)
    bypass = _template_row(sweep, BYPASS_TEMPLATE)
    exact_quality = _quality(exact)
    bypass_quality = _quality(bypass)
    rank_ppa = _ppa_summary(rank_ppa_path)
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
        "rank_datapath_ppa": {
            "status": rank_ppa["status"] if rank_ppa is not None else "missing_rank_ppa",
            "source": str(rank_ppa_path) if rank_ppa_path is not None else None,
            "note": (
                "A merged logit-only datapath artifact is used when available. For greedy decoding, "
                "the argmax k=1 row is the closest physical proxy; for top-k/beam ranking, the k=4 row "
                "is the current measured proxy. Older score/tie-rank artifacts remain accepted only as "
                "conservative fallback evidence."
            ),
            "ppa": rank_ppa["selected"] if rank_ppa is not None else None,
            "argmax_ppa": rank_ppa["argmax"] if rank_ppa is not None else None,
            "topk_ppa": rank_ppa["topk"] if rank_ppa is not None else None,
            "ppa_rows": rank_ppa["rows"] if rank_ppa is not None else [],
        },
        "next_step": [
            "Use logit-rank bypass as the greedy/top-k architecture path if the evaluator result stays exact-safe.",
            "Use the measured logit-only argmax/top-k rows in decoder ranking instead of the older score/tie-rank proxy.",
            "Keep approximate softmax work for sampling modes where calibrated probabilities are required.",
        ],
    }


def _write_markdown(path: Path, report: JsonDict) -> None:
    decision = report["decision"]
    q = report["quality"]
    proxy = report["rank_datapath_ppa"]
    ppa = (proxy.get("ppa") or {}).get("metrics") or {}
    argmax = (proxy.get("argmax_ppa") or {}).get("metrics") or {}
    topk = (proxy.get("topk_ppa") or {}).get("metrics") or {}
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
            "## Rank Datapath PPA",
            "",
            f"- status: `{proxy['status']}`",
            f"- source: `{proxy['source'] or ''}`",
            f"- selected_critical_path_ns: `{ppa.get('critical_path_ns', '')}`",
            f"- selected_die_area: `{ppa.get('die_area', '')}`",
            f"- selected_total_power_mw: `{ppa.get('total_power_mw', '')}`",
            f"- argmax_k1_critical_path_ns: `{argmax.get('critical_path_ns', '')}`",
            f"- argmax_k1_die_area: `{argmax.get('die_area', '')}`",
            f"- argmax_k1_total_power_mw: `{argmax.get('total_power_mw', '')}`",
            f"- topk_k4_critical_path_ns: `{topk.get('critical_path_ns', '')}`",
            f"- topk_k4_die_area: `{topk.get('die_area', '')}`",
            f"- topk_k4_total_power_mw: `{topk.get('total_power_mw', '')}`",
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
    ap.add_argument("--rank-ppa", default=str(DEFAULT_LOGIT_RANK_PPA), help="rank datapath PPA promotion JSON")
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
