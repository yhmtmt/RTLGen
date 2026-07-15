#!/usr/bin/env python3
"""Prove shared-score multi-value decode cluster RTL/perf-model equivalence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate
from npu.sim.perf.attention_online import finalize_value, requantize_score_row, two_pass_stats
from npu.sim.perf.attention_separated import unpack_signed

JsonDict = dict[str, Any]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((int(value) & mask) << (index * bits) for index, value in enumerate(values))


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _vectors(*, head_dim: int = 3) -> tuple[list[list[tuple[int, list[int]]]], list[list[list[list[int]]]]]:
    short_beats = [
        [
            (-3, [2, -4, 5, -6, 7, -8, 9, -10]),
            (11, [-12, 13, -14, 15, -16, 17, -18, 19]),
            (-20, [21, -22, 23, -24, 25, -26, 27, -28]),
        ],
        [
            (4, [-1, 2, -3, 4, -5, 6, -7, 8]),
            (-9, [10, -11, 12, -13, 14, -15, 16, -17]),
            (5, [18, -19, 20, -21, 22, -23, 24, -25]),
        ],
        [
            (-7, [3, 5, -7, 9, -11, 13, -15, 17]),
            (6, [-8, 10, -12, 14, -16, 18, -20, 22]),
            (2, [23, -21, 19, -17, 15, -13, 11, -9]),
        ],
    ]
    if head_dim == 3:
        beats = short_beats
    elif head_dim == 128:
        beats = [
            [
                (
                    ((block * 17 + index * 5) % 255) - 127,
                    [((block * 31 + index * 11 + lane * 13) % 255) - 127 for lane in range(8)],
                )
                for index in range(head_dim)
            ]
            for block in range(len(short_beats))
        ]
    else:
        raise ValueError("head_dim must be 3 or 128")
    values = [
        [
            [
                [((block * 37 + value_slice * 19 + row * 7 + lane * 3) % 255) - 127 for lane in range(8)]
                for row in range(8)
            ]
            for value_slice in range(16)
        ]
        for block in range(len(beats))
    ]
    return beats, values


def _raw_scores(block: list[tuple[int, list[int]]]) -> list[int]:
    return [sum(query * keys[lane] for query, keys in block) for lane in range(8)]


_FAKERAM_MODEL = r"""
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  initial begin addr_q = 0; rd_out_q = 0; for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0; end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) for (idx = 0; idx < 39; idx = idx + 1)
        if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""


def _testbench(
    *,
    top_name: str,
    scenario: str,
    beats: list[list[tuple[int, list[int]]]],
    values: list[list[list[list[int]]]],
    multiplier: int,
    shift: int,
) -> str:
    flat_beats = [beat for block in beats for beat in block]
    beat_init = "\n".join(
        f"    q_mem[{index}] = {_signed_literal(q, 8)}; k_mem[{index}] = 64'h{_pack(keys, 8):016x};"
        for index, (q, keys) in enumerate(flat_beats)
    )
    last_indices = {sum(len(block) for block in beats[: index + 1]) - 1 for index in range(len(beats))}
    last_cases = "\n".join(f"      {index}: input_last = 1'b1;" for index in sorted(last_indices))
    value_init = "\n".join(
        f"    value_mem[{block * 16 + value_slice}] = 512'h{_pack([lane for row in values[block][value_slice] for lane in row], 8):0128x};"
        for block in range(len(values))
        for value_slice in range(16)
    )
    input_gate = "(cycle % 5) != 2" if scenario == "stalls" else "1'b1"
    request_gate = "(cycle % 4) != 1" if scenario == "stalls" else "1'b1"
    result_gate = "(cycle % 7) != 3 && (cycle % 7) != 4" if scenario == "stalls" else "1'b1"
    delay = "(value_read_req_slice % 3) + 1" if scenario == "stalls" else "1"
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer BLOCK_COUNT = {len(beats)};
  localparam integer TOTAL_BEATS = {len(flat_beats)};
  reg clk = 0, rst_n = 0;
  reg command_valid, input_valid, input_last;
  wire command_ready, input_ready;
  reg signed [7:0] input_a;
  reg signed [63:0] input_b;
  wire value_read_req_valid, value_response_ready;
  reg value_read_req_ready, value_response_valid;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg [13:0] value_response_address;
  reg [3:0] value_response_slice;
  reg [511:0] value_response_matrix;
  wire result_valid, result_last;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  wire protocol_error;
  reg signed [7:0] q_mem [0:TOTAL_BEATS-1];
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
      .command_id(16'h4a21), .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(32'd{multiplier}), .command_score_shift(6'd{shift}),
      .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
      .input_a(input_a), .input_b(input_b),
      .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address), .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid), .value_response_ready(value_response_ready),
      .value_response_address(value_response_address), .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix), .result_valid(result_valid), .result_ready(result_ready),
      .result_command_id(result_command_id), .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum), .result_slice(result_slice), .result_last(result_last),
      .result_value(result_value), .accepted_count(accepted_count), .completed_count(completed_count),
      .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    input_valid = rst_n && input_index < TOTAL_BEATS && ({input_gate});
    input_a = input_index < TOTAL_BEATS ? q_mem[input_index] : 0;
    input_b = input_index < TOTAL_BEATS ? k_mem[input_index] : 0;
    input_last = 0;
    case (input_index)
{last_cases}
      default: input_last = 0;
    endcase
    value_read_req_ready = {request_gate};
    result_ready = {result_gate};
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
        pending_delay <= {delay};
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
      if (dut.score_write_valid && dut.score_write_ready)
        $display("WRITE addr=%0d row=%064x", dut.score_write_addr, dut.score_write_data);
      if (dut.score_read_fire) $display("SREQ addr=%0d", dut.score_read_req_addr);
      if (result_valid && result_ready) begin
        $display("RESULT slice=%0d last=%0d id=%0d max=%0d sum=%0d value=%080x error=%0d", result_slice, result_last, result_command_id, $signed(result_global_max), result_exp_sum, result_value, protocol_error);
        result_count <= result_count + 1;
        if (result_last) begin
          if (result_count != 15) $fatal(1, "wrong result beat count");
          #1 $finish;
        end
      end
      if (cycle > 15000) $fatal(1, "timeout");
    end
  end

  initial begin
{beat_init}
{value_init}
    value_response_valid = 0; value_response_address = 0; value_response_slice = 0; value_response_matrix = 0;
    repeat (3) @(posedge clk); @(negedge clk); rst_n = 1;
  end
endmodule
"""


_WRITE_RE = re.compile(r"WRITE addr=(\d+) row=([0-9a-fA-F]+)")
_SREQ_RE = re.compile(r"SREQ addr=(\d+)")
_VREQ_RE = re.compile(r"VREQ addr=(\d+) slice=(\d+)")
_RESULT_RE = re.compile(
    r"RESULT slice=(\d+) last=(\d+) id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) error=(\d+)"
)


def _run_scenario(config: JsonDict, *, scenario: str, multiplier: int, shift: int) -> JsonDict:
    head_dim = 128 if scenario == "llama_head_dim_128" else 3
    beats, values = _vectors(head_dim=head_dim)
    with tempfile.TemporaryDirectory(prefix="decode-score-multivalue-") as tmp_text:
        tmp = Path(tmp_text)
        rtl = tmp / "rtl"
        generate(json.loads(json.dumps(config)), rtl)
        tb = tmp / "tb.sv"
        tb.write_text(
            _testbench(
                top_name=str(config["top_name"]),
                scenario=scenario,
                beats=beats,
                values=values,
                multiplier=multiplier,
                shift=shift,
            ),
            encoding="utf-8",
        )
        simv = tmp / "simv"
        compiled = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl / "top.v"), str(tb)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")

    writes: list[tuple[int, list[int]]] = []
    score_requests: list[int] = []
    value_requests: list[tuple[int, int]] = []
    results: list[JsonDict] = []
    for line in run.stdout.splitlines():
        if match := _WRITE_RE.fullmatch(line.strip()):
            writes.append((int(match.group(1)), unpack_signed(int(match.group(2), 16), lanes=8, bits=32)))
        elif match := _SREQ_RE.fullmatch(line.strip()):
            score_requests.append(int(match.group(1)))
        elif match := _VREQ_RE.fullmatch(line.strip()):
            value_requests.append((int(match.group(1)), int(match.group(2))))
        elif match := _RESULT_RE.fullmatch(line.strip()):
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

    score_rows = [list(requantize_score_row(_raw_scores(block), multiplier=multiplier, shift=shift)) for block in beats]
    expected_values = []
    expected_max = None
    expected_sum = None
    for value_slice in range(16):
        stats = two_pass_stats(score_rows, [values[block][value_slice] for block in range(len(values))])
        expected_values.append(list(finalize_value(stats)))
        expected_max = stats.max_score
        expected_sum = stats.exp_sum
    expected = {
        "command_id": 0x4A21,
        "global_max": expected_max,
        "exp_sum": expected_sum,
        "values": expected_values,
    }
    passed = (
        [address for address, _ in writes] == list(range(len(beats)))
        and [row for _, row in writes] == score_rows
        and score_requests == list(range(len(beats)))
        and value_requests == [(block, value_slice) for block in range(len(beats)) for value_slice in range(16)]
        and len(results) == 16
        and [row["slice"] for row in results] == list(range(16))
        and [row["last"] for row in results] == [False] * 15 + [True]
        and all(row["command_id"] == expected["command_id"] for row in results)
        and all(row["global_max"] == expected["global_max"] for row in results)
        and all(row["exp_sum"] == expected["exp_sum"] for row in results)
        and [row["value"] for row in results] == expected_values
        and not any(row["protocol_error"] for row in results)
    )
    return {
        "scenario": scenario,
        "head_dim": head_dim,
        "equivalence_pass": passed,
        "score_rows": score_rows,
        "score_read_addresses": score_requests,
        "value_read_requests": [list(request) for request in value_requests],
        "expected": expected,
        "observed": results,
    }


def build_report(config: JsonDict) -> JsonDict:
    rows = [
        _run_scenario(config, scenario=scenario, multiplier=multiplier, shift=shift)
        for scenario, multiplier, shift in (
            ("always_ready", 1 << 20, 0),
            ("stalls", 1 << 20, 0),
            ("rounded_shift", 3, 1),
            ("saturation", (1 << 32) - 1, 0),
            ("llama_head_dim_128", 1, 0),
        )
    ]
    passed = all(row["equivalence_pass"] for row in rows)
    return {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_multivalue_cluster_equivalence_v1",
        "decision": (
            "decode_score_multivalue_cluster_equivalence_pass"
            if passed
            else "decode_score_multivalue_cluster_equivalence_fail"
        ),
        "equivalence_pass": passed,
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_v1",
        "value_slices": 16,
        "value_dimensions": 128,
        "score_passes_per_command": 1,
        "score_writes_per_block": 1,
        "score_reads_per_block": 1,
        "result_beats_per_command": 16,
        "scenario_count": len(rows),
        "score_tensor_hash": _hash([row["score_rows"] for row in rows]),
        "final_tensor_hash": _hash([row["observed"] for row in rows]),
        "scenarios": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(json.loads(args.config.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(
        "# Decode Score Shared Multi-Value Cluster Equivalence\n\n"
        f"- decision: `{payload['decision']}`\n"
        f"- equivalence pass: `{payload['equivalence_pass']}`\n"
        f"- score tensor hash: `{payload['score_tensor_hash']}`\n"
        f"- final tensor hash: `{payload['final_tensor_hash']}`\n",
        encoding="utf-8",
    )
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
