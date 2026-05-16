#!/usr/bin/env python3
"""Gate attention/KV structural reductions by quality risk and hardware benefit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


def _kv_risk(*, kv_bits: int) -> tuple[str, str]:
    if kv_bits >= 16:
        return "low", "keeps baseline KV precision"
    if kv_bits >= 8:
        return "medium", "plausible cache quantization, but must be checked on long-context prompts"
    return "high", "low-bit KV cache can perturb attention scores and retrieval behavior"


def _sharing_risk(*, kv_sharing: str) -> tuple[str, str]:
    if kv_sharing == "mha":
        return "low", "preserves baseline per-head K/V structure"
    if kv_sharing in {"gqa4", "gqa8"}:
        return "medium", "plausible if the model is trained or adapted for grouped-query attention"
    if kv_sharing == "mqa":
        return "high", "collapses all K/V heads and should be treated as retraining-required"
    return "unknown", "unrecognized KV sharing mode"


def _risk_level(*, sharing_risk: str, kv_risk: str) -> str:
    ordered = ["low", "medium", "high", "unknown"]
    if "unknown" in {sharing_risk, kv_risk}:
        return "unknown"
    return max((sharing_risk, kv_risk), key=ordered.index)


def _candidate_class(*, kv_sharing: str, kv_bits: int, combined_risk: str) -> str:
    if kv_sharing == "mqa":
        return "bound_only_retrain_required"
    if kv_bits < 8:
        return "quality_experiment_required"
    if combined_risk == "low":
        return "conservative_reference"
    return "deployable_if_model_supports_structure"


def _find_reference(rows: list[JsonDict]) -> JsonDict:
    exact = [
        row
        for row in rows
        if row["kv_sharing"] == "mha" and int(row["kv_bits"]) == 16
    ]
    if exact:
        return exact[0]
    return max(rows, key=lambda row: (int(row["kv_heads"]), int(row["kv_bits"])))


def _focused_rows(
    *,
    physical_hbm_frontier: JsonDict,
    sequence_length_list: list[int],
    die_area_mm2_list: list[float],
) -> list[JsonDict]:
    wanted_seq = set(sequence_length_list)
    wanted_die = {float(value) for value in die_area_mm2_list}
    return [
        row
        for row in physical_hbm_frontier.get("best_by_kv_structure", [])
        if int(row["sequence_length"]) in wanted_seq and float(row["die_area_mm2"]) in wanted_die
    ]


def build_report(
    *,
    physical_hbm_frontier: JsonDict,
    sequence_length_list: list[int],
    die_area_mm2_list: list[float],
) -> JsonDict:
    rows = _focused_rows(
        physical_hbm_frontier=physical_hbm_frontier,
        sequence_length_list=sequence_length_list,
        die_area_mm2_list=die_area_mm2_list,
    )
    if not rows:
        raise ValueError("no matching physical-HBM frontier rows for requested sequence/die focus")

    grouped: dict[tuple[int, float], list[JsonDict]] = {}
    for row in rows:
        key = (int(row["sequence_length"]), float(row["die_area_mm2"]))
        grouped.setdefault(key, []).append(row)

    candidate_rows: list[JsonDict] = []
    for key, group_rows in sorted(grouped.items()):
        reference = _find_reference(group_rows)
        reference_latency = float(reference["latency_us"])
        for row in sorted(group_rows, key=lambda item: (float(item["latency_us"]), item["kv_sharing"], int(item["kv_bits"]))):
            sharing_risk, sharing_reason = _sharing_risk(kv_sharing=str(row["kv_sharing"]))
            kv_risk, kv_reason = _kv_risk(kv_bits=int(row["kv_bits"]))
            combined = _risk_level(sharing_risk=sharing_risk, kv_risk=kv_risk)
            candidate_class = _candidate_class(
                kv_sharing=str(row["kv_sharing"]),
                kv_bits=int(row["kv_bits"]),
                combined_risk=combined,
            )
            speedup = reference_latency / float(row["latency_us"]) if float(row["latency_us"]) > 0 else 0.0
            candidate_rows.append(
                {
                    "sequence_length": key[0],
                    "die_area_mm2": key[1],
                    "kv_sharing": row["kv_sharing"],
                    "kv_heads": row["kv_heads"],
                    "kv_bits": row["kv_bits"],
                    "latency_us": row["latency_us"],
                    "hbm_byte_share": row["hbm_byte_share"],
                    "dominant_tile_resource": row["dominant_tile_resource"],
                    "stack_count": row["stack_count"],
                    "data_rate_mtps": row["data_rate_mtps"],
                    "hardware_speedup_vs_mha16": round(speedup, 6),
                    "sharing_quality_risk": sharing_risk,
                    "kv_precision_quality_risk": kv_risk,
                    "combined_quality_risk": combined,
                    "candidate_class": candidate_class,
                    "quality_rationale": [sharing_reason, kv_reason],
                }
            )

    practical = [
        row
        for row in candidate_rows
        if row["candidate_class"] in {"deployable_if_model_supports_structure", "conservative_reference"}
        and row["combined_quality_risk"] in {"low", "medium"}
    ]
    experiments = [
        row
        for row in candidate_rows
        if row["candidate_class"] == "quality_experiment_required"
    ]
    bounds = [
        row
        for row in candidate_rows
        if row["candidate_class"] == "bound_only_retrain_required"
    ]

    practical_best = sorted(practical, key=lambda row: (row["latency_us"], row["hbm_byte_share"]))[:12]
    experiment_best = sorted(experiments, key=lambda row: (row["latency_us"], row["hbm_byte_share"]))[:12]
    bound_best = sorted(bounds, key=lambda row: (row["latency_us"], row["hbm_byte_share"]))[:12]
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_quality_gate_v1",
        "inputs": {
            "physical_hbm_frontier_model": physical_hbm_frontier.get("model", ""),
            "sequence_length_list": sequence_length_list,
            "die_area_mm2_list": die_area_mm2_list,
        },
        "sweep_summary": {
            "candidate_row_count": len(candidate_rows),
            "practical_candidate_count": len(practical),
            "quality_experiment_candidate_count": len(experiments),
            "bound_only_candidate_count": len(bounds),
        },
        "recommendation": {
            "primary_hardware_candidate": "gqa8_kv8",
            "primary_quality_experiment": "gqa8_kv4",
            "bound_only_candidate": "mqa_kv4",
            "reason": (
                "MQA/KV4 is the strongest hardware lower bound, but both dimensions carry high "
                "quality risk. GQA8/KV8 is the conservative structural candidate; GQA8/KV4 is "
                "the useful quality experiment for testing whether low-bit KV can recover enough "
                "of the HBM benefit without changing to MQA."
            ),
        },
        "practical_candidates": practical_best,
        "quality_experiment_candidates": experiment_best,
        "bound_only_candidates": bound_best,
        "all_candidate_rows": candidate_rows,
        "assumptions": [
            "This gate does not claim measured LLaMA quality; it prevents hardware-only winners from being treated as deployable.",
            "GQA candidates require a model trained or adapted for grouped-query attention before deployment.",
            "MQA candidates are classified as bound-only unless a retrained/adapted model is supplied.",
            "KV4 candidates require long-context quality and retrieval-stability experiments before they can be promoted.",
            "The hardware benefit values come from the merged physical-HBM frontier artifact.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    lines = [
        "# Decoder Attention/KV Quality Gate",
        "",
        f"- model: `{payload['model']}`",
        f"- candidate_row_count: `{payload['sweep_summary']['candidate_row_count']}`",
        f"- primary_hardware_candidate: `{rec['primary_hardware_candidate']}`",
        f"- primary_quality_experiment: `{rec['primary_quality_experiment']}`",
        f"- bound_only_candidate: `{rec['bound_only_candidate']}`",
        "",
        "## Recommendation",
        "",
        rec["reason"],
        "",
        "## Practical Candidates",
        "",
        "| seq | die | kv | bits | latency_us | speedup | hbm_share | risk | class |",
        "|---:|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["practical_candidates"][:10]:
        lines.append(
            "| {seq} | {die} | {kv} | {bits} | {lat} | {speed} | {share} | {risk} | {cls} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                kv=row["kv_sharing"],
                bits=row["kv_bits"],
                lat=row["latency_us"],
                speed=row["hardware_speedup_vs_mha16"],
                share=row["hbm_byte_share"],
                risk=row["combined_quality_risk"],
                cls=row["candidate_class"],
            )
        )
    lines.extend(
        [
            "",
            "## Quality Experiments",
            "",
            "| seq | die | kv | bits | latency_us | speedup | hbm_share | risk |",
            "|---:|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["quality_experiment_candidates"][:10]:
        lines.append(
            "| {seq} | {die} | {kv} | {bits} | {lat} | {speed} | {share} | {risk} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                kv=row["kv_sharing"],
                bits=row["kv_bits"],
                lat=row["latency_us"],
                speed=row["hardware_speedup_vs_mha16"],
                share=row["hbm_byte_share"],
                risk=row["combined_quality_risk"],
            )
        )
    lines.extend(
        [
            "",
            "## Bound Only",
            "",
            "| seq | die | kv | bits | latency_us | speedup | hbm_share | reason |",
            "|---:|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["bound_only_candidates"][:10]:
        lines.append(
            "| {seq} | {die} | {kv} | {bits} | {lat} | {speed} | {share} | {reason} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                kv=row["kv_sharing"],
                bits=row["kv_bits"],
                lat=row["latency_us"],
                speed=row["hardware_speedup_vs_mha16"],
                share=row["hbm_byte_share"],
                reason="; ".join(row["quality_rationale"]),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--physical-hbm-frontier", required=True)
    ap.add_argument("--sequence-length-list", type=_int_list, default=[131072])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[100, 200, 400])
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    physical = json.loads(Path(args.physical_hbm_frontier).read_text(encoding="utf-8"))
    payload = build_report(
        physical_hbm_frontier=physical,
        sequence_length_list=args.sequence_length_list,
        die_area_mm2_list=args.die_area_mm2_list,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
