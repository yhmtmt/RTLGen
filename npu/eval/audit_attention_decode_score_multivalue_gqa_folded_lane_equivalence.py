#!/usr/bin/env python3
"""Prove direct RTL equivalence across folded Llama7B GQA8 lane counts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from npu.eval.audit_attention_decode_score_multivalue_gqa_group_equivalence import (
    HEAD_COUNT,
    VALUE_SLICES,
    _run_flat_group,
    _shared_vectors,
)

JsonDict = dict[str, Any]
_EXPECTED_LANES = {1, 2, 4, 8}
_SCORE_BANK_MACROS_PER_LANE = 56


def _lane_count(config: JsonDict) -> int:
    body = config.get("attention_decode_score_multivalue_gqa_group")
    if not isinstance(body, dict):
        raise ValueError("config requires attention_decode_score_multivalue_gqa_group")
    if int(body.get("query_heads_per_kv", 0)) != HEAD_COUNT:
        raise ValueError("folded lane audit requires query_heads_per_kv=8")
    lanes = int(body.get("parallel_query_head_lanes", HEAD_COUNT))
    if lanes not in _EXPECTED_LANES:
        raise ValueError("parallel_query_head_lanes must be one of 1,2,4,8")
    return lanes


def build_report(configs: list[tuple[str, JsonDict]]) -> JsonDict:
    indexed: dict[int, tuple[str, JsonDict]] = {}
    for source, config in configs:
        lanes = _lane_count(config)
        if lanes in indexed:
            raise ValueError(f"duplicate folded lane config: {lanes}")
        indexed[lanes] = (source, config)
    if set(indexed) != _EXPECTED_LANES:
        raise ValueError("folded lane audit requires exactly one config for lanes 1,2,4,8")

    queries, keys, values = _shared_vectors()
    rows: list[JsonDict] = []
    for lanes in sorted(indexed):
        source, config = indexed[lanes]
        direct = _run_flat_group(
            config=config,
            queries=queries,
            keys=keys,
            values=values,
            multiplier=1,
            shift=0,
        )
        waves = HEAD_COUNT // lanes
        rows.append(
            {
                "parallel_query_head_lanes": lanes,
                "physical_query_head_clusters": lanes,
                "query_head_waves": waves,
                "score_bank_macro_count": _SCORE_BANK_MACROS_PER_LANE * lanes,
                "query_input_replays_per_command": waves,
                "key_input_replays_per_command": waves,
                "shared_value_reads_per_block": VALUE_SLICES * waves,
                "shared_value_read_request_count": direct["shared_value_read_request_count"],
                "completion_cycles": direct["completion_cycles"],
                "equivalence_pass": direct["equivalence_pass"],
                "expected_group_result_sha256": direct["expected_group_result_sha256"],
                "observed_group_result_sha256": direct["observed_group_result_sha256"],
                "shared_value_read_requests_sha256": direct[
                    "shared_value_read_requests_sha256"
                ],
                "score_write_count": sum(row["score_write_count"] for row in direct["heads"]),
                "score_read_count": sum(row["score_read_count"] for row in direct["heads"]),
                "result_count": sum(row["result_count"] for row in direct["heads"]),
                "config_path": source,
            }
        )

    reference_hash = rows[-1]["expected_group_result_sha256"]
    all_hashes_match = all(
        row["expected_group_result_sha256"] == reference_hash
        and row["observed_group_result_sha256"] == reference_hash
        for row in rows
    )
    passed = all(row["equivalence_pass"] for row in rows) and all_hashes_match
    latency_best = min(rows, key=lambda row: int(row["completion_cycles"]))
    return {
        "version": 1,
        "model": "llama7b_gqa8_folded_query_head_lane_direct_rtl_equivalence_v1",
        "decision": (
            "llama7b_gqa8_folded_lane_equivalence_pass"
            if passed
            else "llama7b_gqa8_folded_lane_equivalence_fail"
        ),
        "equivalence_pass": passed,
        "precision_contract": "exact_signed_int8_qkv_s32_score_lut_softmax_integer_output",
        "query_heads_per_kv": HEAD_COUNT,
        "tested_parallel_query_head_lanes": sorted(indexed),
        "shared_result_sha256": reference_hash,
        "all_lane_result_hashes_match": all_hashes_match,
        "latency_best_parallel_query_head_lanes": latency_best[
            "parallel_query_head_lanes"
        ],
        "latency_best_completion_cycles": latency_best["completion_cycles"],
        "rows": rows,
        "scope": {
            "block_count": len(keys),
            "head_dimension": 128,
            "value_slices": VALUE_SLICES,
            "direct_rtl_simulation": True,
            "intermediate_score_writes_and_reads_checked": True,
            "ordered_result_beats_checked": HEAD_COUNT * VALUE_SLICES,
            "producer_contract": (
                "Each of 8/L waves replays one complete packed Q/K packet; no hidden query or key buffer is assumed."
            ),
        },
    }


def _render_markdown(payload: JsonDict) -> str:
    lines = [
        "# Llama7B GQA8 Folded Query-Head Lane Equivalence",
        "",
        f"- decision: `{payload['decision']}`",
        f"- equivalence pass: `{payload['equivalence_pass']}`",
        f"- shared result hash: `{payload['shared_result_sha256']}`",
        f"- precision contract: `{payload['precision_contract']}`",
        "",
        "| lanes | waves | macros | cycles | Q/K replays | value reads/block | pass |",
        "|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {parallel_query_head_lanes} | {query_head_waves} | {score_bank_macro_count} | "
            "{completion_cycles} | {query_input_replays_per_command} | "
            "{shared_value_reads_per_block} | {equivalence_pass} |".format(**row)
        )
    lines.extend(["", payload["scope"]["producer_contract"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    configs = [
        (str(path), json.loads(path.read_text(encoding="utf-8")))
        for path in args.config
    ]
    payload = build_report(configs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps({"decision": payload["decision"], "ok": payload["equivalence_pass"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
