#!/usr/bin/env python3
"""Prove composed decode-score local-cluster RTL/performance-model equivalence."""

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

from npu.rtlgen.gen_attention_decode_score_local_cluster import generate
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
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _vectors() -> tuple[list[list[tuple[int, list[int]]]], list[list[list[int]]]]:
    beats = [
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
    values = [
        [[((block * 29 + row * 7 + lane * 3) % 255) - 127 for lane in range(8)] for row in range(8)]
        for block in range(len(beats))
    ]
    return beats, values


def _raw_scores(block: list[tuple[int, list[int]]]) -> list[int]:
    return [sum(q * keys[lane] for q, keys in block) for lane in range(8)]


_FAKERAM_MODEL = r"""
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer bit_idx;
  initial begin
    addr_q = 0; rd_out_q = 0;
    for (bit_idx = 0; bit_idx < 2048; bit_idx = bit_idx + 1) mem[bit_idx] = 0;
  end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in)
        for (bit_idx = 0; bit_idx < 39; bit_idx = bit_idx + 1)
          if (w_mask_in[bit_idx]) mem[addr_in][bit_idx] <= wd_in[bit_idx];
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
    values: list[list[list[int]]],
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
        f"    value_mem[{index}] = 512'h{_pack([lane for row in matrix for lane in row], 8):0128x};"
        for index, matrix in enumerate(values)
    )
    input_valid = "(cycle % 5) != 2" if scenario == "stalls" else "1'b1"
    value_ready = "(cycle % 4) != 1" if scenario == "stalls" else "1'b1"
    result_ready = "(cycle % 7) != 3 && (cycle % 7) != 4" if scenario == "stalls" else "1'b1"
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer BLOCK_COUNT = {len(beats)};
  localparam integer TOTAL_BEATS = {len(flat_beats)};
  reg clk = 0;
  reg rst_n = 0;
  wire command_ready, input_ready;
  reg command_valid, input_valid, input_last;
  reg signed [7:0] input_a;
  reg signed [63:0] input_b;
  wire value_read_req_valid;
  reg value_read_req_ready;
  wire [13:0] value_read_req_address;
  reg value_response_valid;
  reg [13:0] value_response_address;
  reg [511:0] value_response_matrix;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  wire protocol_error;
  reg signed [7:0] q_mem [0:TOTAL_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:BLOCK_COUNT-1];
  integer input_index = 0;
  integer cycle = 0;
  reg value_pending = 0;
  reg [13:0] value_pending_addr = 0;
  integer value_delay = 0;

  always #5 clk = ~clk;
  {top_name} dut (
    .clk(clk), .rst_n(rst_n),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_id(16'h4a21), .command_block_count(BLOCK_COUNT),
    .command_score_multiplier(32'd{multiplier}), .command_score_shift(6'd{shift}),
    .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
    .input_a(input_a), .input_b(input_b),
    .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
    .value_read_req_address(value_read_req_address),
    .value_response_valid(value_response_valid), .value_response_address(value_response_address),
    .value_response_matrix(value_response_matrix),
    .result_valid(result_valid), .result_ready(result_ready),
    .result_command_id(result_command_id), .result_global_max(result_global_max),
    .result_exp_sum(result_exp_sum), .result_value(result_value),
    .accepted_count(accepted_count), .completed_count(completed_count), .cycle_count(cycle_count),
    .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    input_valid = rst_n && input_index < TOTAL_BEATS && ({input_valid});
    input_a = input_index < TOTAL_BEATS ? q_mem[input_index] : 0;
    input_b = input_index < TOTAL_BEATS ? k_mem[input_index] : 0;
    input_last = 0;
    case (input_index)
{last_cases}
      default: input_last = 0;
    endcase
    value_read_req_ready = {value_ready};
    result_ready = {result_ready};
  end

  always @(posedge clk) begin
    value_response_valid <= 0;
    if (!rst_n) begin
      input_index <= 0; cycle <= 0; value_pending <= 0; value_delay <= 0;
      value_response_address <= 0; value_response_matrix <= 0;
    end else begin
      cycle <= cycle + 1;
      if (input_valid && input_ready) input_index <= input_index + 1;
      if (value_read_req_valid && value_read_req_ready) begin
        if (value_pending) $fatal(1, "more than one value request outstanding");
        value_pending <= 1;
        value_pending_addr <= value_read_req_address;
        value_delay <= {"(value_read_req_address % 3) + 1" if scenario == "stalls" else "1"};
      end
      if (value_pending) begin
        if (value_delay == 0) begin
          value_response_valid <= 1;
          value_response_address <= value_pending_addr;
          value_response_matrix <= value_mem[value_pending_addr];
          value_pending <= 0;
        end else value_delay <= value_delay - 1;
      end
      if (dut.score_write_valid && dut.score_write_ready)
        $display("WRITE addr=%0d row=%064x", dut.score_write_addr, dut.score_write_data);
      if (result_valid && result_ready) begin
        $display("RESULT id=%0d max=%0d sum=%0d value=%080x error=%0d accepted=%0d completed=%0d", result_command_id, $signed(result_global_max), result_exp_sum, result_value, protocol_error, accepted_count, completed_count);
        #1 $finish;
      end
      if (cycle > 2500) $fatal(1, "timeout");
    end
  end

  initial begin
{beat_init}
{value_init}
    value_response_valid = 0; value_response_address = 0; value_response_matrix = 0;
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1;
  end
endmodule
"""


_WRITE_RE = re.compile(r"WRITE addr=(\d+) row=([0-9a-fA-F]+)")
_RESULT_RE = re.compile(
    r"RESULT id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) error=(\d+) accepted=(\d+) completed=(\d+)"
)


def _run_scenario(config: JsonDict, *, scenario: str, multiplier: int, shift: int) -> JsonDict:
    beats, values = _vectors()
    top_name = str(config["top_name"])
    with tempfile.TemporaryDirectory(prefix="decode-score-local-cluster-") as tmp_text:
        tmp = Path(tmp_text)
        rtl = tmp / "rtl"
        generate(json.loads(json.dumps(config)), rtl)
        tb = tmp / "tb.sv"
        tb.write_text(
            _testbench(
                top_name=top_name,
                scenario=scenario,
                beats=beats,
                values=values,
                multiplier=multiplier,
                shift=shift,
            ),
            encoding="utf-8",
        )
        simv = tmp / "simv"
        compile_run = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl / "top.v"), str(tb)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if compile_run.returncode:
            raise RuntimeError(f"iverilog failed:\n{compile_run.stderr}")
        run = subprocess.run(
            [_tool("vvp"), str(simv)], check=True, capture_output=True, text=True, timeout=60
        )

    writes: list[tuple[int, list[int]]] = []
    result: JsonDict | None = None
    for line in run.stdout.splitlines():
        if match := _WRITE_RE.fullmatch(line.strip()):
            writes.append((int(match.group(1)), unpack_signed(int(match.group(2), 16), lanes=8, bits=32)))
        elif match := _RESULT_RE.fullmatch(line.strip()):
            result = {
                "command_id": int(match.group(1)),
                "global_max": int(match.group(2)),
                "exp_sum": int(match.group(3)),
                "value": unpack_signed(int(match.group(4), 16), lanes=8, bits=40),
                "protocol_error": bool(int(match.group(5))),
                "accepted_count": int(match.group(6)),
                "completed_count_at_accept": int(match.group(7)),
            }
    expected_rows = [
        list(requantize_score_row(_raw_scores(block), multiplier=multiplier, shift=shift)) for block in beats
    ]
    stats = two_pass_stats(expected_rows, values)
    expected = {
        "command_id": 0x4A21,
        "global_max": stats.max_score,
        "exp_sum": stats.exp_sum,
        "value": list(finalize_value(stats)),
    }
    observed_rows = [row for _, row in writes]
    addresses = [address for address, _ in writes]
    passed = (
        result is not None
        and addresses == list(range(len(expected_rows)))
        and observed_rows == expected_rows
        and all(result[key] == expected[key] for key in expected)
        and result["protocol_error"] is False
        and result["accepted_count"] == 1
    )
    return {
        "scenario": scenario,
        "equivalence_pass": passed,
        "score_rows": observed_rows,
        "score_addresses": addresses,
        "expected": expected,
        "observed": result,
    }


def build_report(config: JsonDict) -> JsonDict:
    rows = [
        _run_scenario(config, scenario=scenario, multiplier=multiplier, shift=shift)
        for scenario, multiplier, shift in (
            ("always_ready", 1 << 20, 0),
            ("stalls", 1 << 20, 0),
            ("rounded_shift", 3, 1),
            ("saturation", (1 << 32) - 1, 0),
        )
    ]
    passed = all(row["equivalence_pass"] for row in rows)
    all_scores = [row["score_rows"] for row in rows]
    all_finals = [
        {
            "global_max": row["observed"]["global_max"],
            "exp_sum": row["observed"]["exp_sum"],
            "value": row["observed"]["value"],
        }
        for row in rows
    ]
    lanes = int(config["attention_decode_score_local_cluster"]["score_scale_lanes_per_cycle"])
    return {
        "version": 1,
        "model": "llm_decoder_attention_decode_score_local_cluster_equivalence_v1",
        "decision": (
            "decode_score_local_cluster_equivalence_pass"
            if passed
            else "decode_score_local_cluster_equivalence_fail"
        ),
        "equivalence_pass": passed,
        "semantic_profile": "decode_m1x8_score_sram_two_pass_iterdiv_v1",
        "score_scale_lanes_per_cycle": lanes,
        "score_scale_contract": {
            "rounding": "symmetric_magnitude_round_to_nearest",
            "saturation": "signed_32",
            "metadata_source": "external_command_input",
            "tested_multiplier_shift": [[1 << 20, 0], [3, 1], [(1 << 32) - 1, 0]],
        },
        "scenario_count": len(rows),
        "score_tensor_hash": _hash(all_scores),
        "final_tensor_hash": _hash(all_finals),
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
        "# Decode Score Local-Cluster Equivalence\n\n"
        f"- decision: `{payload['decision']}`\n"
        f"- equivalence pass: `{payload['equivalence_pass']}`\n"
        f"- score tensor hash: `{payload['score_tensor_hash']}`\n"
        f"- final tensor hash: `{payload['final_tensor_hash']}`\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": payload["decision"], "ok": payload["equivalence_pass"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
