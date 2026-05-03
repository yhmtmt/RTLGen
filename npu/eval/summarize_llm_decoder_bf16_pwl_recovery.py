#!/usr/bin/env python3
"""Summarize bf16/PWL decoder recovery from a narrow calibration grid."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
DEFAULT_BASELINE = "grid_approx_pwl_bf16_path"
DEFAULT_RECOVERY = "grid_approx_pwl_bf16_path_logit_tiebreak"


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


def _template_row(sweep: JsonDict, template: str) -> JsonDict:
    rows = sweep.get("templates")
    if not isinstance(rows, list):
        raise SystemExit("sweep JSON must contain templates list")
    for row in rows:
        if isinstance(row, dict) and row.get("template") == template:
            return row
    raise SystemExit(f"template not found in sweep: {template}")


def _matches(row: JsonDict) -> tuple[int, int, int]:
    sample_count = int(row.get("sample_count") or 0)
    next_matches = round(float(row.get("next_token_id_match_rate") or 0.0) * sample_count)
    topk_matches = round(float(row.get("topk_contains_reference_id_rate") or 0.0) * sample_count)
    return sample_count, next_matches, topk_matches


def _mismatch_ids(row: JsonDict) -> list[str]:
    return [str(v) for v in row.get("next_token_mismatch_sample_ids") or []]


def _topk_miss_ids(row: JsonDict) -> list[str]:
    return [str(v) for v in row.get("topk_miss_sample_ids") or []]


def _row_summary(row: JsonDict) -> JsonDict:
    sample_count, next_matches, topk_matches = _matches(row)
    return {
        "template": row.get("template"),
        "candidate_semantics": row.get("candidate_semantics"),
        "sample_count": sample_count,
        "next_token_matches": next_matches,
        "topk_matches": topk_matches,
        "next_token_mismatch_sample_ids": _mismatch_ids(row),
        "topk_miss_sample_ids": _topk_miss_ids(row),
        "score_tie_breaker": row.get("score_tie_breaker", ""),
        "normalization_mode": row.get("normalization_mode", ""),
        "normalization_reciprocal_float_format": row.get("normalization_reciprocal_float_format", ""),
    }


def build_report(
    *,
    sweep_path: Path,
    baseline_template: str = DEFAULT_BASELINE,
    recovery_template: str = DEFAULT_RECOVERY,
) -> JsonDict:
    sweep_path = _resolve(sweep_path)
    sweep = _load_json(sweep_path)
    baseline = _row_summary(_template_row(sweep, baseline_template))
    recovery = _row_summary(_template_row(sweep, recovery_template))

    baseline_misses = set(baseline["next_token_mismatch_sample_ids"])
    recovery_misses = set(recovery["next_token_mismatch_sample_ids"])
    recovered = sorted(baseline_misses - recovery_misses)
    regressions = sorted(recovery_misses - baseline_misses)
    sample_count = int(recovery["sample_count"])
    exact_safe = (
        sample_count > 0
        and int(recovery["next_token_matches"]) == sample_count
        and int(recovery["topk_matches"]) == sample_count
    )
    if exact_safe and baseline_misses and not recovery_misses:
        decision = "tie_break_recovery_sufficient"
        recommended = (
            "Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly "
            "score-tie ranking check before full QAT infrastructure."
        )
    elif recovered and not regressions:
        decision = "partial_recovery"
        recommended = "Keep bf16/PWL on the frontier, but run a real QAT/fine-tuning experiment before replacing q12."
    elif regressions:
        decision = "recovery_regresses"
        recommended = "Do not use this ranking calibration without a broader prompt-distribution guard."
    else:
        decision = "no_recovery"
        recommended = "Move to a real QAT/fine-tuning experiment or stay with q12 exact-safe hardware."

    return {
        "version": 0.1,
        "source_sweep": _portable(sweep_path),
        "baseline_template": baseline_template,
        "recovery_template": recovery_template,
        "mechanism": {
            "type": "score_tie_breaker",
            "tie_breaker": "logit",
            "training_interpretation": (
                "This is a narrow QAT/calibration proxy. It does not update weights; it checks whether "
                "the bf16/PWL exact-next losses are pure equal-score ranking losses that a tiny "
                "logit-preserving calibration could recover."
            ),
        },
        "baseline": baseline,
        "recovery": recovery,
        "recovered_sample_ids": recovered,
        "regression_sample_ids": regressions,
        "diagnosis": {
            "decision": decision,
            "exact_safe_after_recovery": exact_safe,
            "recovered_count": len(recovered),
            "regression_count": len(regressions),
            "recommended_next_step": recommended,
        },
    }


def _fmt_ids(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else ""


def _write_md(doc: JsonDict, path: Path) -> None:
    baseline = doc["baseline"]
    recovery = doc["recovery"]
    lines = [
        "# Decoder bf16/PWL Recovery",
        "",
        f"- source_sweep: `{doc['source_sweep']}`",
        f"- decision: `{doc['diagnosis']['decision']}`",
        f"- exact_safe_after_recovery: `{doc['diagnosis']['exact_safe_after_recovery']}`",
        f"- recovered_count: {doc['diagnosis']['recovered_count']}",
        f"- regression_count: {doc['diagnosis']['regression_count']}",
        f"- recommended_next_step: {doc['diagnosis']['recommended_next_step']}",
        "",
        "## Mechanism",
        "",
        doc["mechanism"]["training_interpretation"],
        "",
        "## Quality",
        "",
        "| template | next-token | top-k | mismatches |",
        "|---|---:|---:|---|",
        (
            f"| `{baseline['template']}` | {baseline['next_token_matches']}/{baseline['sample_count']} | "
            f"{baseline['topk_matches']}/{baseline['sample_count']} | "
            f"{_fmt_ids(baseline['next_token_mismatch_sample_ids'])} |"
        ),
        (
            f"| `{recovery['template']}` | {recovery['next_token_matches']}/{recovery['sample_count']} | "
            f"{recovery['topk_matches']}/{recovery['sample_count']} | "
            f"{_fmt_ids(recovery['next_token_mismatch_sample_ids'])} |"
        ),
        "",
        f"- recovered_sample_ids: {_fmt_ids(doc['recovered_sample_ids'])}",
        f"- regression_sample_ids: {_fmt_ids(doc['regression_sample_ids'])}",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--baseline-template", default=DEFAULT_BASELINE)
    ap.add_argument("--recovery-template", default=DEFAULT_RECOVERY)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    doc = build_report(
        sweep_path=Path(args.sweep),
        baseline_template=str(args.baseline_template),
        recovery_template=str(args.recovery_template),
    )
    out_path = _resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_md(doc, _resolve(args.out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
