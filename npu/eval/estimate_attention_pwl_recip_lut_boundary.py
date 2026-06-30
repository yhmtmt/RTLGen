#!/usr/bin/env python3
"""Estimate direct reciprocal-LUT size for composed PWL softmax candidates."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

WARN_CASES = 8192
BLOCK_CASES = 65536


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    source: str
    row_elems: int
    score_bits: int
    weight_bits: int
    reciprocal_bits: int
    bucket_shift: int
    accum_bits: int
    softmax_impl: str


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _as_int(value: Any, *, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"{name} must be an integer, got {value!r}") from exc


def _candidate_from_config(path: Path) -> Candidate:
    payload = _load_json(path)
    comp = payload.get("attention_dual_stream_composed")
    if not isinstance(comp, dict):
        raise SystemExit(f"missing attention_dual_stream_composed object: {path}")
    candidate_id = str(payload.get("top_name") or path.parent.name or path.stem).strip()
    softmax_impl = str(comp.get("softmax_impl") or "exact_div").strip()
    return Candidate(
        candidate_id=candidate_id,
        source=path.as_posix(),
        row_elems=_as_int(comp.get("softmax_row_elems", 8), name=f"{path}: softmax_row_elems"),
        score_bits=_as_int(comp.get("softmax_score_bits", 8), name=f"{path}: softmax_score_bits"),
        weight_bits=_as_int(comp.get("softmax_weight_bits", 8), name=f"{path}: softmax_weight_bits"),
        reciprocal_bits=_as_int(comp.get("reciprocal_bits", 10), name=f"{path}: reciprocal_bits"),
        bucket_shift=_as_int(
            comp.get("softmax_reciprocal_lut_bucket_shift", 0),
            name=f"{path}: softmax_reciprocal_lut_bucket_shift",
        ),
        accum_bits=_as_int(comp.get("softmax_accum_bits", 24), name=f"{path}: softmax_accum_bits"),
        softmax_impl=softmax_impl,
    )


def _parse_candidate_spec(spec: str) -> Candidate:
    name, sep, rest = spec.partition(":")
    if not sep:
        raise SystemExit(f"candidate spec must be name:key=value,...: {spec}")
    fields: dict[str, str] = {}
    for part in rest.split(","):
        key, eq, value = part.partition("=")
        if not eq:
            raise SystemExit(f"candidate field must be key=value in {spec}: {part}")
        fields[key.strip()] = value.strip()
    return Candidate(
        candidate_id=name.strip(),
        source=f"candidate:{spec}",
        row_elems=_as_int(fields.get("row_elems", 8), name=f"{name}: row_elems"),
        score_bits=_as_int(fields.get("score_bits", fields.get("s", 8)), name=f"{name}: score_bits"),
        weight_bits=_as_int(fields.get("weight_bits", fields.get("w", 8)), name=f"{name}: weight_bits"),
        reciprocal_bits=_as_int(fields.get("reciprocal_bits", fields.get("r", 10)), name=f"{name}: reciprocal_bits"),
        bucket_shift=_as_int(fields.get("bucket_shift", fields.get("bucket", 0)), name=f"{name}: bucket_shift"),
        accum_bits=_as_int(fields.get("accum_bits", 24), name=f"{name}: accum_bits"),
        softmax_impl=fields.get("softmax_impl", "pwl_recip_lut"),
    )


def estimate_candidate(candidate: Candidate) -> JsonDict:
    output_scale = (1 << candidate.weight_bits) - 1
    max_sum_weight = candidate.row_elems * output_scale
    bucket_step = 1 << candidate.bucket_shift
    case_count = math.ceil(max_sum_weight / bucket_step)
    entry_bits = candidate.reciprocal_bits + candidate.weight_bits
    rom_bits = case_count * entry_bits
    denom_address_bits = max(1, math.ceil(math.log2(case_count + 1)))
    direct_lut_verdict = "not_applicable"
    next_step = "Candidate does not use the direct PWL reciprocal-LUT implementation."
    if candidate.softmax_impl == "pwl_recip_lut":
        if case_count > BLOCK_CASES:
            direct_lut_verdict = "requires_compact_reciprocal_before_ppa"
            next_step = (
                "Do not launch direct-LUT OpenROAD PPA for this point; first implement a compact reciprocal "
                "approximation or a coarser denominator schedule."
            )
        elif case_count > WARN_CASES:
            direct_lut_verdict = "boundary_probe_only"
            next_step = (
                "Treat direct-LUT PPA as a synthesis-boundary probe, not as the final architecture point."
            )
        else:
            direct_lut_verdict = "direct_lut_ppa_reasonable"
            next_step = "Direct-LUT PPA is small enough to measure as a concrete candidate."
    return {
        "candidate_id": candidate.candidate_id,
        "source": candidate.source,
        "softmax_impl": candidate.softmax_impl,
        "row_elems": candidate.row_elems,
        "score_bits": candidate.score_bits,
        "weight_bits": candidate.weight_bits,
        "reciprocal_bits": candidate.reciprocal_bits,
        "bucket_shift": candidate.bucket_shift,
        "bucket_step": bucket_step,
        "max_sum_weight": max_sum_weight,
        "reciprocal_case_count": case_count,
        "reciprocal_entry_bits": entry_bits,
        "reciprocal_rom_bits": rom_bits,
        "denominator_address_bits": denom_address_bits,
        "direct_lut_warn_case_threshold": WARN_CASES,
        "direct_lut_block_case_threshold": BLOCK_CASES,
        "direct_lut_verdict": direct_lut_verdict,
        "next_step": next_step,
    }


def build_payload(candidates: list[Candidate]) -> JsonDict:
    rows = [estimate_candidate(candidate) for candidate in candidates]
    ranked = sorted(rows, key=lambda row: int(row["reciprocal_case_count"]))
    blocked = [row for row in rows if row["direct_lut_verdict"] == "requires_compact_reciprocal_before_ppa"]
    boundary = [row for row in rows if row["direct_lut_verdict"] == "boundary_probe_only"]
    reasonable = [row for row in rows if row["direct_lut_verdict"] == "direct_lut_ppa_reasonable"]
    if blocked:
        decision = "compact_reciprocal_required_for_widest_points"
    elif boundary:
        decision = "direct_lut_boundary_probe"
    elif reasonable:
        decision = "direct_lut_ppa_reasonable"
    else:
        decision = "no_pwl_recip_lut_candidates"
    return {
        "version": 1,
        "estimator": "attention_pwl_recip_lut_boundary_v1",
        "threshold_basis": {
            "warning": (
                "Engineering guardrail: above this many generated Verilog reciprocal case entries, "
                "use direct-LUT PPA only to find synthesis-boundary behavior."
            ),
            "blocking": (
                "Engineering guardrail: above this many generated Verilog reciprocal case entries, "
                "measure a compact reciprocal architecture before direct-LUT OpenROAD PPA."
            ),
            "direct_lut_warn_case_threshold": WARN_CASES,
            "direct_lut_block_case_threshold": BLOCK_CASES,
        },
        "decision": decision,
        "candidate_count": len(rows),
        "reasonable_direct_lut_candidate_count": len(reasonable),
        "boundary_probe_candidate_count": len(boundary),
        "blocked_direct_lut_candidate_count": len(blocked),
        "candidate_rows": ranked,
    }


def _write_report_md(payload: JsonDict) -> str:
    lines = [
        "# Attention PWL Reciprocal-LUT Boundary",
        "",
        f"- decision: `{payload['decision']}`",
        f"- candidate_count: `{payload['candidate_count']}`",
        f"- warning_cases: `{payload['threshold_basis']['direct_lut_warn_case_threshold']}`",
        f"- blocking_cases: `{payload['threshold_basis']['direct_lut_block_case_threshold']}`",
        "",
        "## Candidates",
        "",
        "| candidate_id | score_bits | weight_bits | recip_bits | bucket_shift | cases | rom_bits | verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["candidate_rows"]:
        lines.append(
            "| {candidate_id} | {score_bits} | {weight_bits} | {reciprocal_bits} | {bucket_shift} | {reciprocal_case_count} | {reciprocal_rom_bits} | {direct_lut_verdict} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Case counts are generated-Verilog reciprocal denominator cases for the current direct-LUT PWL implementation.",
            "- This is a synthesis-risk guardrail, not a PPA result.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", action="append", default=[], help="Composed attention config.json path")
    ap.add_argument(
        "--candidate",
        action="append",
        default=[],
        help="name:key=value,...; keys include s/score_bits,w/weight_bits,r/reciprocal_bits,bucket/bucket_shift,row_elems",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    candidates = [_candidate_from_config(Path(path)) for path in args.config]
    candidates.extend(_parse_candidate_spec(spec) for spec in args.candidate)
    if not candidates:
        raise SystemExit("at least one --config or --candidate is required")

    payload = build_payload(candidates)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_write_report_md(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
