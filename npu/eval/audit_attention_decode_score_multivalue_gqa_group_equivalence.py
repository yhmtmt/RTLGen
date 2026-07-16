#!/usr/bin/env python3
"""Audit Llama7B GQA8 arithmetic through direct and compositional RTL proofs."""

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
    _FAKERAM_MODEL,
    _RESULT_RE,
    _SREQ_RE,
    _VREQ_RE,
    _WRITE_RE,
    _pack,
    _testbench,
    _tool,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.rtlgen.gen_attention_decode_score_multivalue_gqa_group import generate as generate_group
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


_FLAT_WRITE_RE = re.compile(r"FWRITE head=(\d+) addr=(\d+) row=([0-9a-fA-F]+)")
_FLAT_SREQ_RE = re.compile(r"FSREQ head=(\d+) addr=(\d+)")
_FLAT_RESULT_RE = re.compile(
    r"FRESULT head=(\d+) slice=(\d+) last=(\d+) id=(\d+) max=(-?\d+) "
    r"sum=(\d+) value=([0-9a-fA-F]+) error=(\d+)"
)
_FLAT_COMPLETE_RE = re.compile(r"FCOMPLETE cycles=(\d+)")


def _flat_testbench(
    *,
    top_name: str,
    queries: list[list[list[int]]],
    keys: list[list[list[int]]],
    values: list[list[list[list[int]]]],
    multiplier: int,
    shift: int,
) -> str:
    block_count = len(keys)
    total_beats = block_count * HEAD_DIM
    beat_init = "\n".join(
        "    q_mem[{index}] = 64'h{query:016x}; k_mem[{index}] = 64'h{key:016x};".format(
            index=block * HEAD_DIM + dim,
            query=_pack([queries[head][block][dim] for head in range(HEAD_COUNT)], 8),
            key=_pack(keys[block][dim], 8),
        )
        for block in range(block_count)
        for dim in range(HEAD_DIM)
    )
    last_cases = "\n".join(
        f"      {((block + 1) * HEAD_DIM) - 1}: input_last = 1'b1;"
        for block in range(block_count)
    )
    value_init = "\n".join(
        "    value_mem[{index}] = 512'h{value:0128x};".format(
            index=block * VALUE_SLICES + value_slice,
            value=_pack([lane for row in values[block][value_slice] for lane in row], 8),
        )
        for block in range(block_count)
        for value_slice in range(VALUE_SLICES)
    )
    child_monitors = "\n".join(
        f"""      if (dut.u_head_{head}.score_write_valid && dut.u_head_{head}.score_write_ready)
        $display("FWRITE head={head} addr=%0d row=%064x", dut.u_head_{head}.score_write_addr, dut.u_head_{head}.score_write_data);
      if (dut.u_head_{head}.score_read_fire)
        $display("FSREQ head={head} addr=%0d", dut.u_head_{head}.score_read_req_addr);"""
        for head in range(HEAD_COUNT)
    )
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer BLOCK_COUNT = {block_count};
  localparam integer TOTAL_BEATS = {total_beats};
  reg clk = 0, rst_n = 0;
  reg command_valid, input_valid, input_last;
  wire command_ready, input_ready;
  reg signed [63:0] input_query, input_key;
  wire value_read_req_valid, value_response_ready;
  reg value_read_req_ready, value_response_valid;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg [13:0] value_response_address;
  reg [3:0] value_response_slice;
  reg [511:0] value_response_matrix;
  wire result_valid, result_last;
  reg result_ready;
  wire [2:0] result_head;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  wire protocol_error;
  reg [63:0] q_mem [0:TOTAL_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:BLOCK_COUNT*16-1];
  integer input_index = 0, cycle = 0, result_count = 0;
  reg value_pending = 0;
  reg [13:0] pending_addr = 0;
  reg [3:0] pending_slice = 0;
  integer pending_delay = 0;

  always #5 clk = ~clk;
  {top_name} dut (
      .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready),
      .command_id(16'h{COMMAND_ID:04x}), .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(32'd{multiplier}), .command_score_shift(6'd{shift}),
      .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
      .input_query(input_query), .input_key(input_key),
      .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address), .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid), .value_response_ready(value_response_ready),
      .value_response_address(value_response_address), .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix), .result_valid(result_valid), .result_ready(result_ready),
      .result_head(result_head), .result_command_id(result_command_id),
      .result_global_max(result_global_max), .result_exp_sum(result_exp_sum),
      .result_slice(result_slice), .result_last(result_last), .result_value(result_value),
      .accepted_count(accepted_count), .completed_count(completed_count),
      .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    input_valid = rst_n && input_index < TOTAL_BEATS;
    input_query = input_index < TOTAL_BEATS ? q_mem[input_index] : 0;
    input_key = input_index < TOTAL_BEATS ? k_mem[input_index] : 0;
    input_last = 0;
    case (input_index)
{last_cases}
      default: input_last = 0;
    endcase
    value_read_req_ready = 1'b1;
    result_ready = 1'b1;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      input_index <= 0; cycle <= 0; result_count <= 0;
      value_pending <= 0; value_response_valid <= 0; pending_delay <= 0;
      value_response_address <= 0; value_response_slice <= 0; value_response_matrix <= 0;
    end else begin
      cycle <= cycle + 1;
      if (input_valid && input_ready) input_index <= input_index + 1;
      if (value_read_req_valid && value_read_req_ready) begin
        if (value_pending || value_response_valid) $fatal(1, "multiple outstanding value requests");
        value_pending <= 1;
        pending_addr <= value_read_req_address;
        pending_slice <= value_read_req_slice;
        pending_delay <= 1;
        $display("VREQ addr=%0d slice=%0d", value_read_req_address, value_read_req_slice);
      end
      if (value_pending) begin
        if (pending_delay == 0) begin
          value_pending <= 0;
          value_response_valid <= 1;
          value_response_address <= pending_addr;
          value_response_slice <= pending_slice;
          value_response_matrix <= value_mem[pending_addr * 16 + pending_slice];
        end else pending_delay <= pending_delay - 1;
      end
      if (value_response_valid && value_response_ready) value_response_valid <= 0;
{child_monitors}
      if (result_valid && result_ready) begin
        $display("FRESULT head=%0d slice=%0d last=%0d id=%0d max=%0d sum=%0d value=%080x error=%0d", result_head, result_slice, result_last, result_command_id, $signed(result_global_max), result_exp_sum, result_value, protocol_error);
        result_count <= result_count + 1;
        if (result_last && result_head == 3'd7) begin
          if (result_count != 127) $fatal(1, "wrong result beat count");
          $display("FCOMPLETE cycles=%0d", cycle);
          #1 $finish;
        end
      end
      if (cycle > 130000) $fatal(1, "timeout");
    end
  end

  initial begin
{beat_init}
{value_init}
    value_response_valid = 0; value_response_address = 0;
    value_response_slice = 0; value_response_matrix = 0;
    repeat (3) @(posedge clk); @(negedge clk); rst_n = 1;
  end
endmodule
"""


def _run_flat_group(
    *,
    config: JsonDict,
    queries: list[list[list[int]]],
    keys: list[list[list[int]]],
    values: list[list[list[list[int]]]],
    multiplier: int,
    shift: int,
) -> JsonDict:
    with tempfile.TemporaryDirectory(prefix="gqa8-flat-audit-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        direct_config = json.loads(json.dumps(config))
        generate_group(direct_config, rtl_dir)
        tb_path = tmp / "tb.sv"
        tb_path.write_text(
            _flat_testbench(
                top_name=str(direct_config["top_name"]),
                queries=queries,
                keys=keys,
                values=values,
                multiplier=multiplier,
                shift=shift,
            ),
            encoding="utf-8",
        )
        simv = tmp / "simv"
        compiled = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl_dir / "top.v"), str(tb_path)],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if compiled.returncode:
            raise RuntimeError(f"flat GQA8 iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=240)
        if run.returncode:
            raise RuntimeError(f"flat GQA8 simulation failed:\n{run.stdout}\n{run.stderr}")

    writes: list[list[tuple[int, list[int]]]] = [[] for _ in range(HEAD_COUNT)]
    score_requests: list[list[int]] = [[] for _ in range(HEAD_COUNT)]
    value_requests: list[tuple[int, int]] = []
    results: list[list[JsonDict]] = [[] for _ in range(HEAD_COUNT)]
    completion_cycles = 0
    for raw_line in run.stdout.splitlines():
        line = raw_line.strip()
        if match := _FLAT_WRITE_RE.fullmatch(line):
            head = int(match.group(1))
            writes[head].append((int(match.group(2)), unpack_signed(int(match.group(3), 16), lanes=8, bits=32)))
        elif match := _FLAT_SREQ_RE.fullmatch(line):
            score_requests[int(match.group(1))].append(int(match.group(2)))
        elif match := _VREQ_RE.fullmatch(line):
            value_requests.append((int(match.group(1)), int(match.group(2))))
        elif match := _FLAT_RESULT_RE.fullmatch(line):
            head = int(match.group(1))
            results[head].append(
                {
                    "slice": int(match.group(2)),
                    "last": bool(int(match.group(3))),
                    "command_id": int(match.group(4)),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "value": unpack_signed(int(match.group(7), 16), lanes=8, bits=40),
                    "protocol_error": bool(int(match.group(8))),
                }
            )
        elif match := _FLAT_COMPLETE_RE.fullmatch(line):
            completion_cycles = int(match.group(1))

    expected_scores = [
        [
            list(requantize_score_row(_raw_scores(queries[head][block], keys[block]), multiplier=multiplier, shift=shift))
            for block in range(len(keys))
        ]
        for head in range(HEAD_COUNT)
    ]
    expected_results = [_expected_results(expected_scores[head], values) for head in range(HEAD_COUNT)]
    observed_results = [
        [{key: value for key, value in row.items() if key != "protocol_error"} for row in head_rows]
        for head_rows in results
    ]
    expected_value_requests = [
        (block, value_slice) for block in range(len(keys)) for value_slice in range(VALUE_SLICES)
    ]
    passed = (
        all([address for address, _ in writes[head]] == list(range(len(keys))) for head in range(HEAD_COUNT))
        and all([row for _, row in writes[head]] == expected_scores[head] for head in range(HEAD_COUNT))
        and all(score_requests[head] == list(range(len(keys))) for head in range(HEAD_COUNT))
        and value_requests == expected_value_requests
        and observed_results == expected_results
        and not any(row["protocol_error"] for head_rows in results for row in head_rows)
        and completion_cycles > 0
    )
    per_head = [
        {
            "head": head,
            "expected_score_sha256": _hash(expected_scores[head]),
            "observed_score_sha256": _hash([row for _, row in writes[head]]),
            "expected_result_sha256": _hash(expected_results[head]),
            "observed_result_sha256": _hash(observed_results[head]),
            "score_write_count": len(writes[head]),
            "score_read_count": len(score_requests[head]),
            "result_count": len(observed_results[head]),
        }
        for head in range(HEAD_COUNT)
    ]
    return {
        "simulation_run": True,
        "equivalence_pass": passed,
        "block_count": len(keys),
        "head_dim": HEAD_DIM,
        "value_slices": VALUE_SLICES,
        "completion_cycles": completion_cycles,
        "shared_value_read_request_count": len(value_requests),
        "shared_value_read_requests_sha256": _hash([list(request) for request in value_requests]),
        "expected_group_result_sha256": _ordered_group_hash(per_head, "expected_result_sha256"),
        "observed_group_result_sha256": _ordered_group_hash(per_head, "observed_result_sha256"),
        "heads": per_head,
    }


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


def _compact_head(row: JsonDict) -> JsonDict:
    """Retain proof-carrying hashes and counts without serializing full tensors."""
    return {
        key: value
        for key, value in row.items()
        if key not in {"expected_results", "observed_results", "value_read_requests"}
    } | {
        "value_read_request_count": len(row["value_read_requests"]),
        "value_read_requests_sha256": _hash(row["value_read_requests"]),
    }


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
    flat_group = _run_flat_group(
        config=config,
        queries=queries,
        keys=keys,
        values=values,
        multiplier=multiplier,
        shift=shift,
    )
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
    group_results_match = expected_group_results == observed_group_results
    result_order = [
        {"head": row["head"], "slice": row["slice"]}
        for row in observed_group_results
    ]
    passed = (
        arithmetic_pass
        and distinct_queries_pass
        and shared_inputs_pass
        and expected_group_hash == observed_group_hash
        and group_results_match
        and protocol["sharing_and_order_pass"]
        and flat_group["equivalence_pass"]
        and flat_group["expected_group_result_sha256"] == expected_group_hash
        and flat_group["observed_group_result_sha256"] == observed_group_hash
    )
    return {
        "version": 1,
        "model": "llama7b_gqa8_shared_kv_direct_rtl_equivalence_v2",
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
        "group_results_match": group_results_match,
        "group_result_count": len(observed_group_results),
        "group_result_order_sha256": _hash(result_order),
        "arithmetic_equivalence_pass": arithmetic_pass,
        "wrapper_protocol": protocol,
        "flat_8_cluster_rtl": flat_group,
        "flat_8_cluster_rtl_simulation_run": flat_group["simulation_run"],
        "flat_8_cluster_equivalence_pass": flat_group["equivalence_pass"],
        "heads": [_compact_head(row) for row in heads],
        "evidence_detail_policy": "compact_hashes_and_counts_no_full_intermediate_tensors",
        "compositional_proof": {
            "method": "flat_8_cluster_rtl_plus_per_head_reference_and_protocol",
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
            "flat_8_cluster_rtl_simulation_run": True,
            "scope_limit": (
                "The direct flat simulation is bounded to three KV blocks, but exercises all eight query heads, "
                "the full 128-element head dimension, all 16 value slices, shared K/V replay, intermediate score "
                "writes and reads, and all 128 ordered result beats."
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
        f"- direct flat eight-cluster RTL pass: `{payload['flat_8_cluster_equivalence_pass']}`",
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
