#!/usr/bin/env python3
"""Audit Llama7B GQA8 arithmetic by composing cluster and wrapper proofs.

This audit deliberately does not simulate a flat eight-cluster design. It runs
the real generated single-cluster RTL once for each query head, with one shared
key tensor and one shared value tensor, and compares every head against the
performance/reference math. A separate wrapper protocol test proves shared key
broadcast, shared external value replay, and serialized head/slice result order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_decode_score_multivalue_cluster_equivalence import (
    _RESULT_RE,
    _SREQ_RE,
    _VREQ_RE,
    _WRITE_RE,
    _testbench,
    _tool,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.sim.perf.attention_online import finalize_value, requantize_score_row, two_pass_stats
from npu.sim.perf.attention_separated import unpack_signed

JsonDict = dict[str, Any]
HEAD_COUNT = 8
VALUE_SLICES = 16
HEAD_DIM = 128
COMMAND_ID = 0x4A21
DEFAULT_PROTOCOL_TEST = (
    "tests/test_attention_decode_score_multivalue_gqa_group.py::"
    "test_multivalue_gqa_group_atomic_replay_and_result_order"
)


def _hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _shared_vectors() -> tuple[list[list[list[int]]], list[list[list[int]]], list[list[list[list[int]]]]]:
    """Return distinct Q heads and shared K/V tensors for three KV blocks."""
    block_count = 3
    queries = [
        [
            [((block * 29 + dim * 17 + head * 31 + head * dim * 3) % 255) - 127 for dim in range(HEAD_DIM)]
            for block in range(block_count)
        ]
        for head in range(HEAD_COUNT)
    ]
    keys = [
        [
            [((block * 37 + dim * 11 + lane * 19 + dim * lane) % 255) - 127 for lane in range(8)]
            for dim in range(HEAD_DIM)
        ]
        for block in range(block_count)
    ]
    values = [
        [
            [
                [((block * 41 + value_slice * 23 + row * 7 + lane * 13) % 255) - 127 for lane in range(8)]
                for row in range(8)
            ]
            for value_slice in range(VALUE_SLICES)
        ]
        for block in range(block_count)
    ]
    return queries, keys, values


def _raw_scores(query: list[int], keys: list[list[int]]) -> list[int]:
    return [sum(query[dim] * keys[dim][lane] for dim in range(HEAD_DIM)) for lane in range(8)]


def _cluster_config(config: JsonDict) -> JsonDict:
    body = config.get("attention_decode_score_multivalue_gqa_group")
    if not isinstance(body, dict):
        raise ValueError("config requires attention_decode_score_multivalue_gqa_group")
    if int(body.get("query_heads_per_kv", HEAD_COUNT)) != HEAD_COUNT:
        raise ValueError("arithmetic audit requires query_heads_per_kv=8")
    return {
        "top_name": f"{config.get('top_name', 'gqa8')}__arithmetic_cluster",
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": int(body.get("max_blocks", 16384)),
            "array_n": int(body.get("array_n", 8)),
            "value_slices": int(body.get("value_slices", VALUE_SLICES)),
            "divider_impl": str(body.get("divider_impl", "iterative_restoring")),
            "score_scale_lanes_per_cycle": int(body.get("score_scale_lanes_per_cycle", 1)),
        },
    }


def _parse_rtl_output(output: str) -> tuple[list[tuple[int, list[int]]], list[int], list[tuple[int, int]], list[JsonDict]]:
    writes: list[tuple[int, list[int]]] = []
    score_requests: list[int] = []
    value_requests: list[tuple[int, int]] = []
    results: list[JsonDict] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if match := _WRITE_RE.fullmatch(line):
            writes.append((int(match.group(1)), unpack_signed(int(match.group(2), 16), lanes=8, bits=32)))
        elif match := _SREQ_RE.fullmatch(line):
            score_requests.append(int(match.group(1)))
        elif match := _VREQ_RE.fullmatch(line):
            value_requests.append((int(match.group(1)), int(match.group(2))))
        elif match := _RESULT_RE.fullmatch(line):
            results.append(
                {
                    "slice": int(match.group(1)),
                    "last": bool(int(match.group(2))),
                    "command_id": int(match.group(3)),
                    "global_max": int(match.group(4)),
                    "exp_sum": int(match.group(5)),
                    "value": unpack_signed(int(match.group(6), 16), lanes=8, bits=40),
                    "protocol_error": bool(int(match.group(7))),
                }
            )
    return writes, score_requests, value_requests, results


def _expected_results(
    score_rows: list[list[int]], values: list[list[list[list[int]]]]
) -> list[JsonDict]:
    rows: list[JsonDict] = []
    for value_slice in range(VALUE_SLICES):
        stats = two_pass_stats(score_rows, [block[value_slice] for block in values])
        rows.append(
            {
                "slice": value_slice,
                "last": value_slice == VALUE_SLICES - 1,
                "command_id": COMMAND_ID,
                "global_max": stats.max_score,
                "exp_sum": stats.exp_sum,
                "value": list(finalize_value(stats)),
            }
        )
    return rows


def _run_head(
    *,
    head: int,
    rtl_path: Path,
    top_name: str,
    work_dir: Path,
    queries: list[list[list[int]]],
    keys: list[list[list[int]]],
    values: list[list[list[list[int]]]],
    multiplier: int,
    shift: int,
) -> JsonDict:
    beats = [
        [(queries[head][block][dim], keys[block][dim]) for dim in range(HEAD_DIM)]
        for block in range(len(keys))
    ]
    tb_path = work_dir / f"head_{head}_tb.sv"
    tb_path.write_text(
        _testbench(
            top_name=top_name,
            scenario="always_ready",
            beats=beats,
            values=values,
            multiplier=multiplier,
            shift=shift,
        ),
        encoding="utf-8",
    )
    simv = work_dir / f"head_{head}_simv"
    compiled = subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl_path), str(tb_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if compiled.returncode:
        raise RuntimeError(f"head {head} iverilog failed:\n{compiled.stderr}")
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
    if run.returncode:
        raise RuntimeError(f"head {head} simulation failed:\n{run.stdout}\n{run.stderr}")

    writes, score_requests, value_requests, observed = _parse_rtl_output(run.stdout)
    expected_scores = [
        list(requantize_score_row(_raw_scores(queries[head][block], keys[block]), multiplier=multiplier, shift=shift))
        for block in range(len(keys))
    ]
    expected = _expected_results(expected_scores, values)
    observed_results = [{key: value for key, value in row.items() if key != "protocol_error"} for row in observed]
    expected_requests = [(block, value_slice) for block in range(len(keys)) for value_slice in range(VALUE_SLICES)]
    passed = (
        [address for address, _ in writes] == list(range(len(keys)))
        and [row for _, row in writes] == expected_scores
        and score_requests == list(range(len(keys)))
        and value_requests == expected_requests
        and observed_results == expected
        and not any(row["protocol_error"] for row in observed)
    )
    return {
        "head": head,
        "arithmetic_equivalence_pass": passed,
        "query_sha256": _hash(queries[head]),
        "shared_key_sha256": _hash(keys),
        "shared_value_sha256": _hash(values),
        "expected_score_sha256": _hash(expected_scores),
        "observed_score_sha256": _hash([row for _, row in writes]),
        "expected_result_sha256": _hash(expected),
        "observed_result_sha256": _hash(observed_results),
        "score_read_addresses": score_requests,
        "value_read_requests": [list(request) for request in value_requests],
        "expected_results": expected,
        "observed_results": observed_results,
    }


def _ordered_group_hash(heads: list[JsonDict], field: str) -> str:
    ordered = sorted(heads, key=lambda row: int(row["head"]))
    return _hash([{"head": row["head"], "result_sha256": row[field]} for row in ordered])


def _ordered_group_results(heads: list[JsonDict], field: str) -> list[JsonDict]:
    ordered = sorted(heads, key=lambda row: int(row["head"]))
    return [{"head": row["head"], **result} for row in ordered for result in row[field]]


def _run_protocol_test(repo_root: Path, target: str) -> JsonDict:
    command = [sys.executable, "-m", "pytest", "-q", target]
    run = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, timeout=120)
    output = (run.stdout + "\n" + run.stderr).strip()
    passed_count = sum(int(value) for value in re.findall(r"(\d+) passed", output))
    return {
        "test_target": target,
        "command": ["python3", "-m", "pytest", "-q", target],
        "returncode": run.returncode,
        "passed_test_count": passed_count,
        "sharing_and_order_pass": run.returncode == 0 and passed_count == 1,
    }


def build_report(config: JsonDict, *, protocol_test_target: str = DEFAULT_PROTOCOL_TEST) -> JsonDict:
    cluster_config = _cluster_config(config)
    queries, keys, values = _shared_vectors()
    multiplier = 1
    shift = 0
    with tempfile.TemporaryDirectory(prefix="gqa8-arithmetic-audit-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        generate_cluster(cluster_config, rtl_dir)
        heads = [
            _run_head(
                head=head,
                rtl_path=rtl_dir / "top.v",
                top_name=str(cluster_config["top_name"]),
                work_dir=tmp,
                queries=queries,
                keys=keys,
                values=values,
                multiplier=multiplier,
                shift=shift,
            )
            for head in range(HEAD_COUNT)
        ]
    protocol = _run_protocol_test(REPO_ROOT, protocol_test_target)
    query_hashes = [row["query_sha256"] for row in heads]
    shared_inputs_pass = (
        {row["shared_key_sha256"] for row in heads} == {_hash(keys)}
        and {row["shared_value_sha256"] for row in heads} == {_hash(values)}
    )
    arithmetic_pass = all(row["arithmetic_equivalence_pass"] for row in heads)
    distinct_queries_pass = len(set(query_hashes)) == HEAD_COUNT
    expected_group_hash = _ordered_group_hash(heads, "expected_result_sha256")
    observed_group_hash = _ordered_group_hash(heads, "observed_result_sha256")
    expected_group_results = _ordered_group_results(heads, "expected_results")
    observed_group_results = _ordered_group_results(heads, "observed_results")
    passed = (
        arithmetic_pass
        and distinct_queries_pass
        and shared_inputs_pass
        and expected_group_hash == observed_group_hash
        and expected_group_results == observed_group_results
        and protocol["sharing_and_order_pass"]
    )
    return {
        "version": 1,
        "model": "llama7b_gqa8_shared_kv_compositional_arithmetic_equivalence_v1",
        "decision": "llama7b_gqa8_shared_kv_equivalence_pass" if passed else "llama7b_gqa8_shared_kv_equivalence_fail",
        "equivalence_pass": passed,
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1",
        "query_heads_per_kv": HEAD_COUNT,
        "head_dim": HEAD_DIM,
        "value_slices": VALUE_SLICES,
        "shared_key_sha256": _hash(keys),
        "shared_value_sha256": _hash(values),
        "distinct_query_heads_pass": distinct_queries_pass,
        "shared_inputs_pass": shared_inputs_pass,
        "per_head_result_sha256": [row["observed_result_sha256"] for row in heads],
        "expected_group_result_sha256": expected_group_hash,
        "observed_group_result_sha256": observed_group_hash,
        "group_result_sha256": observed_group_hash,
        "expected_group_results": expected_group_results,
        "observed_group_results": observed_group_results,
        "arithmetic_equivalence_pass": arithmetic_pass,
        "wrapper_protocol": protocol,
        "heads": heads,
        "compositional_proof": {
            "method": "single_cluster_arithmetic_plus_wrapper_protocol",
            "arithmetic_claim": (
                "The real generated single-cluster RTL is simulated independently for each of eight distinct "
                "query heads against the perf/reference math, while every run uses identical key and value tensors."
            ),
            "wrapper_claim": (
                "The focused wrapper protocol test verifies atomic shared-key broadcast, one shared external "
                "value replay, and deterministic head-major then slice-major result order."
            ),
            "composition_claim": (
                "Because the wrapper only broadcasts shared keys and shared value responses to "
                "arithmetic-equivalent children and serializes their unchanged results in the tested order, "
                "the two checks compose to the GQA8 claim."
            ),
            "flat_8_cluster_rtl_simulation_run": False,
            "scope_limit": (
                "This is a compositional proof; it does not claim that a flat eight-cluster RTL simulation was run."
            ),
        },
    }


def _render_markdown(payload: JsonDict) -> str:
    proof = payload["compositional_proof"]
    lines = [
        "# Llama7B GQA8 Shared-K/V Arithmetic Equivalence",
        "",
        f"- decision: `{payload['decision']}`",
        f"- equivalence pass: `{payload['equivalence_pass']}`",
        f"- real single-cluster arithmetic pass: `{payload['arithmetic_equivalence_pass']}`",
        f"- wrapper sharing/order protocol pass: `{payload['wrapper_protocol']['sharing_and_order_pass']}`",
        f"- expected group result hash: `{payload['expected_group_result_sha256']}`",
        f"- observed group result hash: `{payload['observed_group_result_sha256']}`",
        "",
        "## Compositional Proof",
        "",
        proof["arithmetic_claim"],
        "",
        proof["wrapper_claim"],
        "",
        proof["composition_claim"],
        "",
        f"**Scope:** {proof['scope_limit']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--protocol-test-target", default=DEFAULT_PROTOCOL_TEST)
    args = parser.parse_args()
    payload = build_report(
        json.loads(args.config.read_text(encoding="utf-8")),
        protocol_test_target=args.protocol_test_target,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps({"decision": payload["decision"], "ok": payload["equivalence_pass"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
