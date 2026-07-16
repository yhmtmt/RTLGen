#!/usr/bin/env python3
"""Compose the measured GQA8 group proof with the direct array wrapper protocol proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
JsonDict = dict[str, Any]
_GROUP_MODEL = "llama7b_gqa8_shared_kv_compositional_arithmetic_equivalence_v1"
_GROUP_DECISION = "llama7b_gqa8_shared_kv_equivalence_pass"
_ARRAY_COUNTS = (1, 2, 4)
_PROTOCOL_TEST = (
    "tests/test_attention_decode_score_multivalue_gqa_array.py::"
    "test_multivalue_gqa_array_atomic_broadcast_and_independent_channels"
)


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_group_equivalence(payload: JsonDict) -> JsonDict:
    wrapper = payload.get("wrapper_protocol")
    expected_hash = payload.get("expected_group_result_sha256")
    observed_hash = payload.get("observed_group_result_sha256")
    if not (
        payload.get("model") == _GROUP_MODEL
        and payload.get("decision") == _GROUP_DECISION
        and payload.get("equivalence_pass") is True
        and payload.get("distinct_query_heads_pass") is True
        and payload.get("shared_inputs_pass") is True
        and payload.get("arithmetic_equivalence_pass") is True
        and int(payload.get("query_heads_per_kv", 0)) == 8
        and isinstance(wrapper, dict)
        and wrapper.get("sharing_and_order_pass") is True
        and isinstance(expected_hash, str)
        and bool(expected_hash)
        and expected_hash == observed_hash
    ):
        raise ValueError("merged GQA8 group equivalence contract did not pass")
    return {
        "model": payload["model"],
        "decision": payload["decision"],
        "semantic_profile": payload.get("semantic_profile"),
        "expected_group_result_sha256": expected_hash,
        "observed_group_result_sha256": observed_hash,
    }


def _validate_array_configs(configs: list[JsonDict]) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for config in configs:
        body = config.get("attention_decode_score_multivalue_gqa_array")
        if not isinstance(body, dict):
            raise ValueError("array config lacks attention_decode_score_multivalue_gqa_array")
        row = {
            "top_name": str(config.get("top_name") or ""),
            "group_count": int(body.get("group_count", 0)),
            "max_blocks": int(body.get("max_blocks", 0)),
            "array_n": int(body.get("array_n", 0)),
            "value_slices": int(body.get("value_slices", 0)),
            "score_scale_lanes_per_cycle": int(body.get("score_scale_lanes_per_cycle", 0)),
            "query_heads_per_kv": int(body.get("query_heads_per_kv", 0)),
            "divider_impl": str(body.get("divider_impl") or ""),
        }
        if not row["top_name"]:
            raise ValueError("array config top_name is empty")
        if (
            row["max_blocks"] != 16384
            or row["array_n"] != 8
            or row["value_slices"] != 16
            or row["score_scale_lanes_per_cycle"] != 1
            or row["query_heads_per_kv"] != 8
            or row["divider_impl"] != "iterative_restoring"
        ):
            raise ValueError("array config is not the exact Llama7B GQA8 physical profile")
        rows.append(row)
    counts = tuple(sorted(row["group_count"] for row in rows))
    if counts != _ARRAY_COUNTS:
        raise ValueError(f"array configs must cover group counts {_ARRAY_COUNTS}")
    return sorted(rows, key=lambda row: int(row["group_count"]))


def _run_protocol_test(target: str) -> JsonDict:
    command = [sys.executable, "-m", "pytest", "-q", target]
    run = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=180)
    output = (run.stdout + "\n" + run.stderr).strip()
    passed_count = sum(int(value) for value in re.findall(r"(\d+) passed", output))
    return {
        "test_target": target,
        "command": ["python3", "-m", "pytest", "-q", target],
        "returncode": run.returncode,
        "passed_test_count": passed_count,
        "atomic_broadcast_and_independent_channels_pass": (
            run.returncode == 0 and passed_count == len(_ARRAY_COUNTS)
        ),
    }


def _build_report(
    *, group_equivalence: JsonDict, array_configs: list[JsonDict], protocol: JsonDict
) -> JsonDict:
    group = _validate_group_equivalence(group_equivalence)
    config_rows = _validate_array_configs(array_configs)
    protocol_pass = protocol.get("atomic_broadcast_and_independent_channels_pass") is True
    per_array_hashes = [
        {
            "group_count": row["group_count"],
            "expected_array_result_sha256": _hash(
                [group["expected_group_result_sha256"]] * int(row["group_count"])
            ),
            "observed_array_result_sha256": _hash(
                [group["observed_group_result_sha256"]] * int(row["group_count"])
            ),
        }
        for row in config_rows
    ]
    hashes_pass = all(
        row["expected_array_result_sha256"] == row["observed_array_result_sha256"]
        for row in per_array_hashes
    )
    passed = protocol_pass and hashes_pass
    return {
        "version": 1,
        "model": "llama7b_gqa8_multigroup_array_compositional_equivalence_v1",
        "decision": (
            "llama7b_gqa8_multigroup_array_equivalence_pass"
            if passed
            else "llama7b_gqa8_multigroup_array_equivalence_fail"
        ),
        "equivalence_pass": passed,
        "precision_status": "exact" if passed else "rejected",
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1",
        "query_heads_per_kv": 8,
        "logical_kv_groups": 4,
        "measured_group_counts": list(_ARRAY_COUNTS),
        "array_configs": config_rows,
        "group_equivalence": group,
        "array_result_hashes": per_array_hashes,
        "array_protocol": protocol,
        "compositional_proof": {
            "method": "merged_complete_group_equivalence_plus_array_wrapper_protocol",
            "group_claim": (
                "Each instantiated group is the same generated complete GQA8 group whose arithmetic, shared-K/V "
                "behavior, and ordered result stream passed the merged group equivalence gate."
            ),
            "array_claim": (
                "The generated array wrapper protocol simulation covers one, two, and four groups and verifies "
                "atomic command/input broadcast plus independent value-memory and result channels."
            ),
            "flat_32_cluster_arithmetic_simulation_run": False,
            "scope_limit": (
                "The proof composes a merged complete-group arithmetic proof with direct array-wrapper protocol "
                "simulation; it does not claim a monolithic 32-cluster arithmetic simulation."
            ),
        },
    }


def build_report(
    *, group_equivalence_json: Path, array_config_paths: list[Path], protocol_test_target: str
) -> JsonDict:
    return _build_report(
        group_equivalence=_load(group_equivalence_json),
        array_configs=[_load(path) for path in array_config_paths],
        protocol=_run_protocol_test(protocol_test_target),
    )


def _markdown(payload: JsonDict) -> str:
    proof = payload["compositional_proof"]
    return (
        "# Llama7B GQA8 Multi-Group Array Equivalence\n\n"
        f"- decision: `{payload['decision']}`\n"
        f"- equivalence pass: `{payload['equivalence_pass']}`\n"
        f"- group counts: `{payload['measured_group_counts']}`\n"
        f"- wrapper protocol pass: "
        f"`{payload['array_protocol']['atomic_broadcast_and_independent_channels_pass']}`\n\n"
        "## Proof Boundary\n\n"
        f"{proof['group_claim']}\n\n{proof['array_claim']}\n\n"
        f"**Scope:** {proof['scope_limit']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group-equivalence-json", type=Path, required=True)
    parser.add_argument("--array-config", type=Path, action="append", required=True)
    parser.add_argument("--protocol-test-target", default=_PROTOCOL_TEST)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        group_equivalence_json=args.group_equivalence_json,
        array_config_paths=args.array_config,
        protocol_test_target=args.protocol_test_target,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_markdown(payload), encoding="utf-8")
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
