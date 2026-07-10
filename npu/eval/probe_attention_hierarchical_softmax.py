#!/usr/bin/env python3
"""Compare scalable online and two-pass score32 attention composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.sim.perf.attention_online import (
    block_stats,
    finalize_value,
    merge_balanced,
    merge_sequence,
    score_buffer_bytes,
    two_pass_stats,
    width_bounds,
)
from npu.sim.perf.attention_separated import ROW_ELEMS, VALUE_DIM

JsonDict = dict[str, Any]


def _scores(*, length: int, distribution: str, seed: int) -> list[int]:
    rng = random.Random(seed)
    scale = 1 << 28
    if distribution == "normal_std1":
        return [round(rng.gauss(0.0, 1.0) * scale) for _ in range(length)]
    if distribution == "normal_std4":
        return [round(rng.gauss(0.0, 4.0) * scale) for _ in range(length)]
    if distribution == "monotonic_ramp16":
        return [round((-8.0 + 16.0 * index / max(1, length - 1)) * scale) for index in range(length)]
    raise ValueError(f"unknown distribution: {distribution}")


def _values(*, length: int, seed: int) -> list[list[int]]:
    rng = random.Random(seed ^ 0x5A17C9E3)
    return [[rng.randint(-128, 127) for _ in range(VALUE_DIM)] for _ in range(length)]


def _blocks(scores: list[int], values: list[list[int]]) -> tuple[list[list[int]], list[list[list[int]]]]:
    if len(scores) % ROW_ELEMS:
        raise ValueError(f"length must be divisible by {ROW_ELEMS}")
    return (
        [scores[index : index + ROW_ELEMS] for index in range(0, len(scores), ROW_ELEMS)],
        [values[index : index + ROW_ELEMS] for index in range(0, len(values), ROW_ELEMS)],
    )


def _error(candidate, reference) -> JsonDict:
    candidate_value = finalize_value(candidate)
    reference_value = finalize_value(reference)
    errors = [abs(left - right) for left, right in zip(candidate_value, reference_value)]
    return {
        "exp_sum_relative_error": abs(candidate.exp_sum - reference.exp_sum) / max(1, reference.exp_sum),
        "max_abs_value_error_q16": max(errors),
        "mean_abs_value_error_q16": sum(errors) / len(errors),
        "max_abs_value_error": max(errors) / 65535.0,
    }


def build_report(*, lengths: list[int], distributions: list[str], seed: int) -> JsonDict:
    rows: list[JsonDict] = []
    for length in lengths:
        for distribution in distributions:
            scores = _scores(length=length, distribution=distribution, seed=seed)
            values = _values(length=length, seed=seed)
            score_blocks, value_blocks = _blocks(scores, values)
            leaves = [
                block_stats(score_row, value_matrix)
                for score_row, value_matrix in zip(score_blocks, value_blocks)
            ]
            reference = two_pass_stats(score_blocks, value_blocks)
            for architecture, candidate in (
                ("online_streaming", merge_sequence(leaves)),
                ("online_balanced", merge_balanced(leaves)),
            ):
                error = _error(candidate, reference)
                rows.append(
                    {
                        "length": length,
                        "distribution": distribution,
                        "architecture": architecture,
                        "block_count": len(leaves),
                        "passes": 1,
                        "score_buffer_bytes_32_heads": 0,
                        "arithmetic_exact_vs_two_pass": all(value == 0 for value in error.values()),
                        **error,
                    }
                )
            rows.append(
                {
                    "length": length,
                    "distribution": distribution,
                    "architecture": "two_pass_global_max",
                    "block_count": len(leaves),
                    "passes": 2,
                    "score_buffer_bytes_32_heads": score_buffer_bytes(
                        context_tokens=length, attention_heads=32, score_bits=32
                    ),
                    "arithmetic_exact_vs_two_pass": True,
                    "exp_sum_relative_error": 0.0,
                    "max_abs_value_error_q16": 0,
                    "mean_abs_value_error_q16": 0.0,
                    "max_abs_value_error": 0.0,
                }
            )

    online_rows = [row for row in rows if str(row["architecture"]).startswith("online_")]
    online_error_bound_q16 = 655
    online_pass = bool(online_rows) and all(
        int(row["max_abs_value_error_q16"]) <= online_error_bound_q16 for row in online_rows
    )
    return {
        "version": 1,
        "model": "attention_hierarchical_softmax_architecture_probe_v1",
        "decision": "online_candidate_retained" if online_pass else "two_pass_exact_selected",
        "seed": seed,
        "lengths": lengths,
        "distributions": distributions,
        "online_error_bound_q16": online_error_bound_q16,
        "online_pass": online_pass,
        "width_bounds": width_bounds(),
        "llama7b_score_buffer": {
            "bytes": score_buffer_bytes(context_tokens=131072, attention_heads=32, score_bits=32),
            "mib": score_buffer_bytes(context_tokens=131072, attention_heads=32, score_bits=32) / (1024 * 1024),
            "current_shared_sram_mib": 68,
            "fits_current_shared_sram": True,
        },
        "rows": rows,
        "next_step": (
            "Implement and quality-test both online and two-pass RTL."
            if online_pass
            else "Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison."
        ),
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Hierarchical Attention Composition Probe",
        "",
        f"- decision: `{payload['decision']}`",
        f"- online pass: `{payload['online_pass']}`",
        f"- Llama7B score buffer MiB: `{payload['llama7b_score_buffer']['mib']}`",
        "",
        "| length | distribution | architecture | max value error q16 | exp-sum relative error |",
        "|---:|---|---|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['length']} | {row['distribution']} | {row['architecture']} | "
            f"{row['max_abs_value_error_q16']} | {row['exp_sum_relative_error']:.9g} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _int_list(value: str) -> list[int]:
    values = [int(item) for item in value.split(",") if item.strip()]
    if not values or any(item <= 0 or item % ROW_ELEMS for item in values):
        raise argparse.ArgumentTypeError(f"lengths must be positive multiples of {ROW_ELEMS}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lengths", type=_int_list, default=[128, 4096, 131072])
    parser.add_argument("--distributions", default="normal_std1,normal_std4,monotonic_ramp16")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        lengths=args.lengths,
        distributions=[item for item in args.distributions.split(",") if item],
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"decision": payload["decision"], "online_pass": payload["online_pass"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
