#!/usr/bin/env python3
"""Prove external-score-SRAM two-pass stream engine equivalence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.rtlgen.gen_attention_two_pass_stream import generate
from npu.sim.perf.attention_online import two_pass_command
from npu.sim.perf.attention_separated import AttentionSeparatedCommand, default_commands, producer_result, unpack_signed

JsonDict = dict[str, Any]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _payloads(command: AttentionSeparatedCommand, block_count: int) -> list[JsonDict]:
    command = command.normalized()
    return [
        producer_result(
            AttentionSeparatedCommand(
                command_id=(command.command_id + index) & 0xFFFF,
                seed=(command.seed ^ ((index * 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF,
            )
        )
        for index in range(block_count)
    ]


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((value & mask) << (index * bits) for index, value in enumerate(values))


def _pack_values(matrix: list[list[int]]) -> int:
    return _pack([value for row in matrix for value in row], 8)


def _config(*, top_name: str, div_lanes: int) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_two_pass_stream": {"max_blocks": 16384, "div_lanes_per_cycle": div_lanes},
    }


def _ready(kind: str, scenario: str, cycle: int) -> bool:
    if scenario == "memory_stalls":
        if kind == "write":
            return cycle % 5 != 2
        if kind == "read":
            return cycle % 4 != 1
    if kind == "result" and scenario == "result_backpressure":
        return cycle % 6 not in {3, 4}
    return True


def _expected_cycle(*, block_count: int, div_lanes: int, scenario: str) -> int:
    state = "idle"
    fill_index = read_index = div_index = 0
    pending = False
    for cycle in range(10000):
        old = state
        if old == "idle":
            state = "fill"
        elif old == "fill" and fill_index < block_count and _ready("write", scenario, cycle):
            fill_index += 1
            if fill_index == block_count:
                state = "read_req"
        elif old == "read_req" and _ready("read", scenario, cycle):
            pending = True
            state = "read_data"
        elif old == "read_data" and pending:
            pending = False
            read_index += 1
            if read_index == block_count:
                state = "divide"
            else:
                state = "read_req"
        elif old == "divide":
            div_index += div_lanes
            if div_index >= 8:
                state = "hold"
        elif old == "hold" and _ready("result", scenario, cycle):
            return cycle
    raise RuntimeError("expected-cycle model timed out")


def _testbench(*, top_name: str, block_count: int, div_lanes: int, scenario: str) -> str:
    command = default_commands(1)[0]
    payloads = _payloads(command, block_count)
    init = "\n".join(
        f"    score_mem[{index}] = 256'h{_pack(payload['score_row'], 32):064x}; "
        f"value_mem[{index}] = 512'h{_pack_values(payload['value_matrix']):0128x};"
        for index, payload in enumerate(payloads)
    )
    write_ready = "score_write_ready = (cycle % 5) != 2;" if scenario == "memory_stalls" else "score_write_ready = 1'b1;"
    read_ready = "score_read_req_ready = (cycle % 4) != 1;" if scenario == "memory_stalls" else "score_read_req_ready = 1'b1;"
    result_ready = "result_ready = (cycle % 6) != 3 && (cycle % 6) != 4;" if scenario == "result_backpressure" else "result_ready = 1'b1;"
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer BLOCK_COUNT = {block_count};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid;
  wire command_ready;
  reg fill_valid;
  wire fill_ready;
  reg [255:0] fill_score_row;
  wire score_write_valid;
  reg score_write_ready;
  wire [13:0] score_write_addr;
  wire [255:0] score_write_data;
  wire score_read_req_valid;
  reg score_read_req_ready;
  wire [13:0] score_read_req_addr;
  reg replay_valid;
  wire replay_ready;
  reg [255:0] replay_score_row;
  reg [511:0] replay_value_matrix;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  reg [255:0] score_mem [0:BLOCK_COUNT-1];
  reg [511:0] value_mem [0:BLOCK_COUNT-1];
  integer fill_index;
  integer cycle;
  reg pending_valid;
  reg [13:0] pending_addr;

  always #5 clk = ~clk;
  {top_name} dut (
    .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready),
    .command_id(16'h{command.command_id:04x}), .command_block_count(BLOCK_COUNT),
    .fill_valid(fill_valid), .fill_ready(fill_ready), .fill_score_row(fill_score_row),
    .score_write_valid(score_write_valid), .score_write_ready(score_write_ready),
    .score_write_addr(score_write_addr), .score_write_data(score_write_data),
    .score_read_req_valid(score_read_req_valid), .score_read_req_ready(score_read_req_ready),
    .score_read_req_addr(score_read_req_addr), .replay_valid(replay_valid), .replay_ready(replay_ready),
    .replay_score_row(replay_score_row), .replay_value_matrix(replay_value_matrix),
    .result_valid(result_valid), .result_ready(result_ready), .result_command_id(result_command_id),
    .result_global_max(result_global_max), .result_exp_sum(result_exp_sum), .result_value(result_value),
    .accepted_count(accepted_count), .completed_count(completed_count), .cycle_count(cycle_count)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    fill_valid = fill_index < BLOCK_COUNT;
    fill_score_row = fill_index < BLOCK_COUNT ? score_mem[fill_index] : 256'd0;
    {write_ready}
    {read_ready}
    replay_valid = pending_valid;
    replay_score_row = pending_valid ? score_mem[pending_addr] : 256'd0;
    replay_value_matrix = pending_valid ? value_mem[pending_addr] : 512'd0;
    {result_ready}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      fill_index <= 0;
      cycle <= 0;
      pending_valid <= 1'b0;
      pending_addr <= 14'd0;
    end else begin
      if (score_write_valid && score_write_ready) begin
        if (score_write_addr != fill_index || score_write_data != score_mem[fill_index]) $fatal(1, "write mismatch");
        fill_index <= fill_index + 1;
      end
      if (score_read_req_valid && score_read_req_ready) begin
        pending_valid <= 1'b1;
        pending_addr <= score_read_req_addr;
      end
      if (replay_valid && replay_ready) pending_valid <= 1'b0;
      if (result_valid && result_ready) begin
        $display("RESULT cycle=%0d id=%0d max=%0d sum=%0d value=%080x", cycle, result_command_id, $signed(result_global_max), result_exp_sum, result_value);
        #1 $finish;
      end
      cycle <= cycle + 1;
      if (cycle > 1000) $fatal(1, "timeout");
    end
  end

  initial begin
{init}
    repeat (2) @(posedge clk);
    @(negedge clk); rst_n = 1'b1;
  end
endmodule
"""


_RESULT = re.compile(r"RESULT cycle=(\d+) id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)")


def _run_rtl(*, block_count: int, div_lanes: int, scenario: str) -> JsonDict:
    top_name = f"attention_two_pass_stream_d{div_lanes}"
    with tempfile.TemporaryDirectory(prefix="attention-two-pass-stream-") as tmp_text:
        tmp = Path(tmp_text)
        rtl = tmp / "rtl"
        generate(_config(top_name=top_name, div_lanes=div_lanes), rtl)
        tb = tmp / "tb.sv"
        tb.write_text(
            _testbench(top_name=top_name, block_count=block_count, div_lanes=div_lanes, scenario=scenario),
            encoding="utf-8",
        )
        sim = tmp / "simv"
        subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(sim), str(rtl / "top.v"), str(tb)],
            check=True,
            capture_output=True,
            text=True,
        )
        completed = subprocess.run([_tool("vvp"), str(sim)], check=True, capture_output=True, text=True)
        match = next((_RESULT.fullmatch(line.strip()) for line in completed.stdout.splitlines() if line.startswith("RESULT")), None)
        if match is None:
            raise RuntimeError(f"missing result:\n{completed.stdout}")
        return {
            "cycle": int(match.group(1)),
            "command_id": int(match.group(2)),
            "global_max": int(match.group(3)),
            "exp_sum": int(match.group(4)),
            "value": unpack_signed(int(match.group(5), 16), lanes=8, bits=40),
        }


def build_report(*, block_counts: list[int], div_lanes: list[int]) -> JsonDict:
    command = default_commands(1)[0]
    rows: list[JsonDict] = []
    for block_count in block_counts:
        expected = two_pass_command(command, block_count=block_count)
        for lanes in div_lanes:
            for scenario in ("always_ready", "memory_stalls", "result_backpressure"):
                rtl = _run_rtl(block_count=block_count, div_lanes=lanes, scenario=scenario)
                expected_cycle = _expected_cycle(block_count=block_count, div_lanes=lanes, scenario=scenario)
                functional = all(
                    rtl[key] == expected[key] for key in ("command_id", "global_max", "exp_sum", "value")
                )
                schedule = rtl["cycle"] == expected_cycle
                rows.append(
                    {
                        "block_count": block_count,
                        "div_lanes_per_cycle": lanes,
                        "scenario": scenario,
                        "functional_pass": functional,
                        "schedule_pass": schedule,
                        "equivalence_pass": functional and schedule,
                        "final_cycle": rtl["cycle"],
                        "expected_final_cycle": expected_cycle,
                    }
                )
    passed = bool(rows) and all(row["equivalence_pass"] for row in rows)
    return {
        "version": 1,
        "model": "attention_two_pass_stream_perf_rtl_equivalence_v1",
        "decision": "attention_two_pass_stream_equivalence_pass" if passed else "attention_two_pass_stream_equivalence_fail",
        "equivalence_pass": passed,
        "semantic_profile": "q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max",
        "score_storage": "external_ready_valid_sram",
        "kv_replay": "external_ready_valid_stream",
        "block_counts": block_counts,
        "div_lanes_per_cycle": div_lanes,
        "scenarios": ["always_ready", "memory_stalls", "result_backpressure"],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-counts", default="4,8")
    parser.add_argument("--div-lanes", default="1,2,4,8")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        block_counts=[int(value) for value in args.block_counts.split(",") if value],
        div_lanes=[int(value) for value in args.div_lanes.split(",") if value],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(
        "# Two-Pass Stream Equivalence\n\n"
        f"- decision: `{payload['decision']}`\n- equivalence pass: `{payload['equivalence_pass']}`\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": payload["decision"], "ok": payload["equivalence_pass"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
