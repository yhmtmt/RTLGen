#!/usr/bin/env python3
"""Probe exact-partial score32 cluster egress and pairwise merge equivalence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.rtlgen.gen_attention_score32_online_state_merge import generate as generate_merge
from npu.sim.perf.attention_exact_partial import (
    merge_partial_streams,
    pack_numerators,
    partial_stream_from_blocks,
    unpack_numerators,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]

_CLUSTER_RE = re.compile(
    r"CLUSTER_RESULT cluster=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+) error=(\d+)"
)
_MERGE_RE = re.compile(
    r"MERGE_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+) error=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY c0_accept=(\d+) c0_complete=(\d+) c1_accept=(\d+) c1_complete=(\d+) merge_complete=(\d+) merge_cycle=(\d+) c0_error=(\d+) c1_error=(\d+) merge_error=(\d+)"
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((int(value) & mask) << (index * bits) for index, value in enumerate(values))


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _command_schedule() -> tuple[dict[str, int], ...]:
    return (
        {"command_id": 0x4A21, "head_id": 0, "multiplier": 1 << 20, "shift": 0},
        {"command_id": 0x4A22, "head_id": 7, "multiplier": 3, "shift": 1},
        {"command_id": 0x4A23, "head_id": 19, "multiplier": 1 << 20, "shift": 0},
    )


def _beats_for(cluster: int, command_index: int, *, head_dim: int = 3) -> list[list[tuple[int, list[int]]]]:
    blocks: list[list[tuple[int, list[int]]]] = []
    for block in range(3):
        block_beats: list[tuple[int, list[int]]] = []
        for beat in range(head_dim):
            q = ((cluster * 29 + command_index * 17 + block * 11 + beat * 5) % 63) - 31
            keys = [
                ((cluster * 41 + command_index * 13 + block * 7 + beat * 19 + lane * 3) % 127) - 63
                for lane in range(8)
            ]
            block_beats.append((q, keys))
        blocks.append(block_beats)
    return blocks


def _values_for(cluster: int, command_index: int) -> list[list[list[list[int]]]]:
    return [
        [
            [
                [
                    ((cluster * 53 + command_index * 31 + block * 17 + value_slice * 13 + row * 11 + lane * 7) % 255)
                    - 127
                    for lane in range(8)
                ]
                for row in range(8)
            ]
            for value_slice in range(16)
        ]
        for block in range(3)
    ]


def _raw_scores(block: list[tuple[int, list[int]]]) -> list[int]:
    return [sum(query * keys[lane] for query, keys in block) for lane in range(8)]


def _expected() -> dict[str, object]:
    commands = _command_schedule()
    clusters: list[list[dict[str, object]]] = [[], []]
    merged: list[dict[str, object]] = []
    for cluster in range(2):
        for command_index, command in enumerate(commands):
            beats = _beats_for(cluster, command_index)
            values = _values_for(cluster, command_index)
            score_rows = [
                list(
                    requantize_score_row(
                        _raw_scores(block),
                        multiplier=int(command["multiplier"]),
                        shift=int(command["shift"]),
                    )
                )
                for block in beats
            ]
            partial = partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=score_rows,
                value_blocks=values,
            )
            clusters[cluster].append(
                {
                    "command_id": int(command["command_id"]),
                    "head_id": int(command["head_id"]),
                    "score_rows": score_rows,
                    "partial": [
                        {
                            "command_id": beat.command_id,
                            "head_id": beat.head_id,
                            "slice": beat.slice_index,
                            "last": beat.last,
                            "global_max": beat.max_score,
                            "exp_sum": beat.exp_sum,
                            "value": list(beat.numerators),
                        }
                        for beat in partial
                    ],
                }
            )
    for command_index, command in enumerate(commands):
        left = partial_stream_from_blocks(
            command_id=int(command["command_id"]),
            head_id=int(command["head_id"]),
            score_rows=clusters[0][command_index]["score_rows"],
            value_blocks=_values_for(0, command_index),
        )
        right = partial_stream_from_blocks(
            command_id=int(command["command_id"]),
            head_id=int(command["head_id"]),
            score_rows=clusters[1][command_index]["score_rows"],
            value_blocks=_values_for(1, command_index),
        )
        merged.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in merge_partial_streams(left, right)
        )
    return {"commands": commands, "clusters": clusters, "merged": merged}


_FAKERAM_MODEL = """
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


def _testbench(*, cluster0_top: str, cluster1_top: str, merge_top: str) -> str:
    commands = _command_schedule()
    flat0 = [beat for command_index in range(len(commands)) for block in _beats_for(0, command_index) for beat in block]
    flat1 = [beat for command_index in range(len(commands)) for block in _beats_for(1, command_index) for beat in block]
    lasts0 = [
        1 if beat_index % 3 == 2 else 0
        for command_index in range(len(commands))
        for block in _beats_for(0, command_index)
        for beat_index, _ in enumerate(block)
    ]
    lasts1 = [
        1 if beat_index % 3 == 2 else 0
        for command_index in range(len(commands))
        for block in _beats_for(1, command_index)
        for beat_index, _ in enumerate(block)
    ]
    beat_init0 = "\n".join(
        f"    q_mem0[{index}] = {_signed_literal(q, 8)}; k_mem0[{index}] = 64'h{_pack(keys, 8):016x}; last_mem0[{index}] = 1'b{lasts0[index]};"
        for index, (q, keys) in enumerate(flat0)
    )
    beat_init1 = "\n".join(
        f"    q_mem1[{index}] = {_signed_literal(q, 8)}; k_mem1[{index}] = 64'h{_pack(keys, 8):016x}; last_mem1[{index}] = 1'b{lasts1[index]};"
        for index, (q, keys) in enumerate(flat1)
    )
    value_init = []
    for cluster in range(2):
        for command_index in range(len(commands)):
            values = _values_for(cluster, command_index)
            for block in range(3):
                for value_slice in range(16):
                    flat = [lane for row in values[block][value_slice] for lane in row]
                    value_init.append(
                        f"    value_mem[{(((cluster * len(commands)) + command_index) * 3 + block) * 16 + value_slice}] = 512'h{_pack(flat, 8):0128x};"
                    )
    cmd_init = "\n".join(
        f"    cmd_id_mem[{index}] = 16'h{int(command['command_id']):04x}; cmd_head_mem[{index}] = 5'd{int(command['head_id'])};"
        f" cmd_mult_mem[{index}] = 32'd{int(command['multiplier'])}; cmd_shift_mem[{index}] = 6'd{int(command['shift'])};"
        for index, command in enumerate(commands)
    )
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer CMD_COUNT = {len(commands)};
  localparam integer BLOCK_COUNT = 3;
  localparam integer HEAD_DIM = 3;
  localparam integer BEATS_PER_COMMAND = BLOCK_COUNT * HEAD_DIM;
  localparam integer TOTAL_BEATS = CMD_COUNT * BEATS_PER_COMMAND;
  localparam integer TOTAL_RESULTS = CMD_COUNT * 16;
  reg clk = 0, rst_n = 0;
  reg [15:0] cmd_id_mem [0:CMD_COUNT-1];
  reg [4:0] cmd_head_mem [0:CMD_COUNT-1];
  reg [31:0] cmd_mult_mem [0:CMD_COUNT-1];
  reg [5:0] cmd_shift_mem [0:CMD_COUNT-1];
  reg signed [7:0] q_mem0 [0:TOTAL_BEATS-1];
  reg [63:0] k_mem0 [0:TOTAL_BEATS-1];
  reg last_mem0 [0:TOTAL_BEATS-1];
  reg signed [7:0] q_mem1 [0:TOTAL_BEATS-1];
  reg [63:0] k_mem1 [0:TOTAL_BEATS-1];
  reg last_mem1 [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:2*CMD_COUNT*BLOCK_COUNT*16-1];
  integer cycle = 0;
  integer issue_index = 0;
  integer input_index0 = 0;
  integer input_index1 = 0;
  integer active_cmd0 = 0;
  integer active_cmd1 = 0;
  integer merge_results = 0;

  reg command_valid;
  wire command_ready0, command_ready1;
  reg input_valid0, input_valid1;
  wire input_ready0, input_ready1;
  reg input_last0, input_last1;
  reg signed [7:0] input_a0, input_a1;
  reg signed [63:0] input_b0, input_b1;
  wire value_read_req_valid0, value_read_req_valid1;
  reg value_read_req_ready0, value_read_req_ready1;
  wire [13:0] value_read_req_address0, value_read_req_address1;
  wire [3:0] value_read_req_slice0, value_read_req_slice1;
  reg value_response_valid0, value_response_valid1;
  wire value_response_ready0, value_response_ready1;
  reg [13:0] value_response_address0, value_response_address1;
  reg [3:0] value_response_slice0, value_response_slice1;
  reg [511:0] value_response_matrix0, value_response_matrix1;
  wire cluster_result_valid0, cluster_result_valid1;
  wire cluster_result_ready0, cluster_result_ready1;
  wire [15:0] cluster_result_command_id0, cluster_result_command_id1;
  wire [4:0] cluster_result_head_id0, cluster_result_head_id1;
  wire signed [31:0] cluster_result_global_max0, cluster_result_global_max1;
  wire [32:0] cluster_result_exp_sum0, cluster_result_exp_sum1;
  wire [3:0] cluster_result_slice0, cluster_result_slice1;
  wire cluster_result_last0, cluster_result_last1;
  wire [327:0] cluster_result_value0, cluster_result_value1;
  wire [31:0] accepted_count0, accepted_count1;
  wire [31:0] completed_count0, completed_count1;
  wire [31:0] cycle_count0, cycle_count1;
  wire protocol_error0, protocol_error1;

  reg pending0 = 0, pending1 = 0;
  reg [13:0] pending_addr0 = 0, pending_addr1 = 0;
  reg [3:0] pending_slice0 = 0, pending_slice1 = 0;
  integer pending_delay0 = 0, pending_delay1 = 0;

  wire merge_valid;
  reg merge_ready;
  wire [15:0] merge_command_id;
  wire [4:0] merge_head_id;
  wire signed [31:0] merge_global_max;
  wire [32:0] merge_exp_sum;
  wire [3:0] merge_slice;
  wire merge_last;
  wire [327:0] merge_value;
  wire [31:0] merge_completed_count;
  wire [31:0] merge_cycle_count;
  wire merge_protocol_error;

  always #5 clk = ~clk;

  {cluster0_top} c0 (
      .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready0),
      .command_id(cmd_id_mem[issue_index]), .command_block_count(BLOCK_COUNT), .command_head_id(cmd_head_mem[issue_index]),
      .command_score_multiplier(cmd_mult_mem[issue_index]), .command_score_shift(cmd_shift_mem[issue_index]),
      .input_valid(input_valid0), .input_ready(input_ready0), .input_last(input_last0), .input_a(input_a0), .input_b(input_b0),
      .value_read_req_valid(value_read_req_valid0), .value_read_req_ready(value_read_req_ready0),
      .value_read_req_address(value_read_req_address0), .value_read_req_slice(value_read_req_slice0),
      .value_response_valid(value_response_valid0), .value_response_ready(value_response_ready0),
      .value_response_address(value_response_address0), .value_response_slice(value_response_slice0), .value_response_matrix(value_response_matrix0),
      .result_valid(cluster_result_valid0), .result_ready(cluster_result_ready0), .result_command_id(cluster_result_command_id0),
      .result_head_id(cluster_result_head_id0), .result_global_max(cluster_result_global_max0), .result_exp_sum(cluster_result_exp_sum0),
      .result_slice(cluster_result_slice0), .result_last(cluster_result_last0), .result_value(cluster_result_value0),
      .accepted_count(accepted_count0), .completed_count(completed_count0), .cycle_count(cycle_count0), .protocol_error(protocol_error0)
  );

  {cluster1_top} c1 (
      .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready1),
      .command_id(cmd_id_mem[issue_index]), .command_block_count(BLOCK_COUNT), .command_head_id(cmd_head_mem[issue_index]),
      .command_score_multiplier(cmd_mult_mem[issue_index]), .command_score_shift(cmd_shift_mem[issue_index]),
      .input_valid(input_valid1), .input_ready(input_ready1), .input_last(input_last1), .input_a(input_a1), .input_b(input_b1),
      .value_read_req_valid(value_read_req_valid1), .value_read_req_ready(value_read_req_ready1),
      .value_read_req_address(value_read_req_address1), .value_read_req_slice(value_read_req_slice1),
      .value_response_valid(value_response_valid1), .value_response_ready(value_response_ready1),
      .value_response_address(value_response_address1), .value_response_slice(value_response_slice1), .value_response_matrix(value_response_matrix1),
      .result_valid(cluster_result_valid1), .result_ready(cluster_result_ready1), .result_command_id(cluster_result_command_id1),
      .result_head_id(cluster_result_head_id1), .result_global_max(cluster_result_global_max1), .result_exp_sum(cluster_result_exp_sum1),
      .result_slice(cluster_result_slice1), .result_last(cluster_result_last1), .result_value(cluster_result_value1),
      .accepted_count(accepted_count1), .completed_count(completed_count1), .cycle_count(cycle_count1), .protocol_error(protocol_error1)
  );

  {merge_top} merge (
      .clk(clk), .rst_n(rst_n),
      .left_valid(cluster_result_valid0), .left_ready(cluster_result_ready0),
      .left_command_id(cluster_result_command_id0), .left_head_id(cluster_result_head_id0),
      .left_global_max(cluster_result_global_max0), .left_exp_sum(cluster_result_exp_sum0),
      .left_slice(cluster_result_slice0), .left_last(cluster_result_last0), .left_value(cluster_result_value0),
      .right_valid(cluster_result_valid1), .right_ready(cluster_result_ready1),
      .right_command_id(cluster_result_command_id1), .right_head_id(cluster_result_head_id1),
      .right_global_max(cluster_result_global_max1), .right_exp_sum(cluster_result_exp_sum1),
      .right_slice(cluster_result_slice1), .right_last(cluster_result_last1), .right_value(cluster_result_value1),
      .out_valid(merge_valid), .out_ready(merge_ready),
      .out_command_id(merge_command_id), .out_head_id(merge_head_id), .out_global_max(merge_global_max),
      .out_exp_sum(merge_exp_sum), .out_slice(merge_slice), .out_last(merge_last), .out_value(merge_value),
      .completed_count(merge_completed_count), .cycle_count(merge_cycle_count), .protocol_error(merge_protocol_error)
  );

  always @* begin
    command_valid = rst_n && issue_index < CMD_COUNT && command_ready0 && command_ready1;
    input_valid0 = rst_n && input_index0 < (issue_index * BEATS_PER_COMMAND) && ((cycle % 5) != 2);
    input_valid1 = rst_n && input_index1 < (issue_index * BEATS_PER_COMMAND) && ((cycle % 7) != 3);
    input_a0 = input_index0 < TOTAL_BEATS ? q_mem0[input_index0] : 0;
    input_b0 = input_index0 < TOTAL_BEATS ? k_mem0[input_index0] : 0;
    input_last0 = input_index0 < TOTAL_BEATS ? last_mem0[input_index0] : 0;
    input_a1 = input_index1 < TOTAL_BEATS ? q_mem1[input_index1] : 0;
    input_b1 = input_index1 < TOTAL_BEATS ? k_mem1[input_index1] : 0;
    input_last1 = input_index1 < TOTAL_BEATS ? last_mem1[input_index1] : 0;
    value_read_req_ready0 = (cycle % 4) != 1;
    value_read_req_ready1 = (cycle % 6) != 2;
    merge_ready = (cycle % 9) != 4 && (cycle % 9) != 5;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issue_index <= 0;
      input_index0 <= 0;
      input_index1 <= 0;
      active_cmd0 <= 0;
      active_cmd1 <= 0;
      merge_results <= 0;
      pending0 <= 0; pending1 <= 0;
      pending_delay0 <= 0; pending_delay1 <= 0;
      value_response_valid0 <= 0; value_response_valid1 <= 0;
      value_response_address0 <= 0; value_response_address1 <= 0;
      value_response_slice0 <= 0; value_response_slice1 <= 0;
      value_response_matrix0 <= 0; value_response_matrix1 <= 0;
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready0 && command_ready1) begin
        active_cmd0 <= issue_index;
        active_cmd1 <= issue_index;
        issue_index <= issue_index + 1;
      end
      if (input_valid0 && input_ready0) input_index0 <= input_index0 + 1;
      if (input_valid1 && input_ready1) input_index1 <= input_index1 + 1;
      if (value_read_req_valid0 && value_read_req_ready0) begin
        if (pending0 || value_response_valid0) $fatal(1, "cluster0 multiple outstanding requests");
        pending0 <= 1;
        pending_addr0 <= value_read_req_address0;
        pending_slice0 <= value_read_req_slice0;
        pending_delay0 <= ((value_read_req_slice0 + active_cmd0) % 3) + 1;
      end
      if (value_read_req_valid1 && value_read_req_ready1) begin
        if (pending1 || value_response_valid1) $fatal(1, "cluster1 multiple outstanding requests");
        pending1 <= 1;
        pending_addr1 <= value_read_req_address1;
        pending_slice1 <= value_read_req_slice1;
        pending_delay1 <= ((value_read_req_address1 + value_read_req_slice1 + 1) % 4) + 1;
      end
      if (pending0) begin
        if (pending_delay0 == 0) begin
          pending0 <= 0;
          value_response_valid0 <= 1;
          value_response_address0 <= pending_addr0;
          value_response_slice0 <= pending_slice0;
          value_response_matrix0 <= value_mem[((active_cmd0) * BLOCK_COUNT + pending_addr0) * 16 + pending_slice0];
        end else pending_delay0 <= pending_delay0 - 1;
      end
      if (pending1) begin
        if (pending_delay1 == 0) begin
          pending1 <= 0;
          value_response_valid1 <= 1;
          value_response_address1 <= pending_addr1;
          value_response_slice1 <= pending_slice1;
          value_response_matrix1 <= value_mem[(((CMD_COUNT + active_cmd1) * BLOCK_COUNT) + pending_addr1) * 16 + pending_slice1];
        end else pending_delay1 <= pending_delay1 - 1;
      end
      if (value_response_valid0 && value_response_ready0) value_response_valid0 <= 0;
      if (value_response_valid1 && value_response_ready1) value_response_valid1 <= 0;

      if (cluster_result_valid0 && cluster_result_ready0)
        $display("CLUSTER_RESULT cluster=0 cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d error=%0d",
                 cluster_result_command_id0, cluster_result_head_id0, cluster_result_slice0, cluster_result_last0,
                 $signed(cluster_result_global_max0), cluster_result_exp_sum0, cluster_result_value0, cycle, protocol_error0);
      if (cluster_result_valid1 && cluster_result_ready1)
        $display("CLUSTER_RESULT cluster=1 cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d error=%0d",
                 cluster_result_command_id1, cluster_result_head_id1, cluster_result_slice1, cluster_result_last1,
                 $signed(cluster_result_global_max1), cluster_result_exp_sum1, cluster_result_value1, cycle, protocol_error1);
      if (merge_valid && merge_ready) begin
        $display("MERGE_RESULT cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d error=%0d",
                 merge_command_id, merge_head_id, merge_slice, merge_last, $signed(merge_global_max), merge_exp_sum, merge_value, cycle, merge_protocol_error);
        merge_results <= merge_results + 1;
        if (merge_results + 1 == TOTAL_RESULTS) begin
          $display("SUMMARY c0_accept=%0d c0_complete=%0d c1_accept=%0d c1_complete=%0d merge_complete=%0d merge_cycle=%0d c0_error=%0d c1_error=%0d merge_error=%0d",
                   accepted_count0, completed_count0, accepted_count1, completed_count1, merge_completed_count + 1, merge_cycle_count,
                   protocol_error0, protocol_error1, merge_protocol_error);
          #1 $finish;
        end
      end
      if (cycle > 20000) $fatal(1, "timeout");
    end
  end

  initial begin
{cmd_init}
{beat_init0}
{beat_init1}
{chr(10).join(value_init)}
    value_response_valid0 = 0; value_response_valid1 = 0;
    value_response_address0 = 0; value_response_address1 = 0;
    value_response_slice0 = 0; value_response_slice1 = 0;
    value_response_matrix0 = 0; value_response_matrix1 = 0;
    repeat (3) @(posedge clk); @(negedge clk); rst_n = 1;
  end
endmodule
"""


def build_report() -> JsonDict:
    expected = _expected()
    with tempfile.TemporaryDirectory(prefix="score32-exact-partial-") as tmp_text:
        tmp = Path(tmp_text)
        cluster0_dir = tmp / "cluster0"
        cluster1_dir = tmp / "cluster1"
        merge_dir = tmp / "merge"
        generate_cluster(
            {
                "top_name": "exact_partial_cluster0",
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": 16,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "result_mode": "exact_partial",
                    "head_id_bits": 5,
                },
            },
            cluster0_dir,
        )
        generate_cluster(
            {
                "top_name": "exact_partial_cluster1",
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": 16,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "result_mode": "exact_partial",
                    "head_id_bits": 5,
                },
            },
            cluster1_dir,
        )
        generate_merge(
            {
                "top_name": "exact_partial_merge",
                "attention_score32_online_state_merge": {"value_slices": 16, "head_id_bits": 5},
            },
            merge_dir,
        )
        tb_path = tmp / "tb.sv"
        tb_path.write_text(
            _testbench(
                cluster0_top="exact_partial_cluster0",
                cluster1_top="exact_partial_cluster1",
                merge_top="exact_partial_merge",
            ),
            encoding="utf-8",
        )

        verilator = subprocess.run(
            [
                _tool("verilator"),
                "--lint-only",
                "--timing",
                "-Wall",
                "-Wno-fatal",
                str(cluster0_dir / "top.v"),
                str(cluster1_dir / "top.v"),
                str(merge_dir / "top.v"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if verilator.returncode:
            raise RuntimeError(f"verilator failed:\n{verilator.stderr}")

        simv = tmp / "simv"
        iverilog = subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(simv),
                str(cluster0_dir / "top.v"),
                str(cluster1_dir / "top.v"),
                str(merge_dir / "top.v"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if iverilog.returncode:
            raise RuntimeError(f"iverilog failed:\n{iverilog.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")

    observed_clusters = [[], []]
    observed_merge = []
    summary = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _CLUSTER_RE.fullmatch(stripped):
            observed_clusters[int(match.group(1))].append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": list(unpack_numerators(int(match.group(8), 16))),
                    "cycle": int(match.group(9)),
                    "protocol_error": bool(int(match.group(10))),
                }
            )
        elif match := _MERGE_RE.fullmatch(stripped):
            observed_merge.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "value": list(unpack_numerators(int(match.group(7), 16))),
                    "cycle": int(match.group(8)),
                    "protocol_error": bool(int(match.group(9))),
                }
            )
        elif match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "c0_accept": int(match.group(1)),
                "c0_complete": int(match.group(2)),
                "c1_accept": int(match.group(3)),
                "c1_complete": int(match.group(4)),
                "merge_complete": int(match.group(5)),
                "merge_cycle": int(match.group(6)),
                "c0_error": bool(int(match.group(7))),
                "c1_error": bool(int(match.group(8))),
                "merge_error": bool(int(match.group(9))),
            }
    if summary is None:
        raise RuntimeError("simulation summary missing")

    expected_clusters = [
        [row for command in expected["clusters"][cluster] for row in command["partial"]]
        for cluster in range(2)
    ]
    clean_cluster_obs = [
        [{key: value for key, value in row.items() if key not in {"cycle", "protocol_error"}} for row in cluster_rows]
        for cluster_rows in observed_clusters
    ]
    clean_merge_obs = [{key: value for key, value in row.items() if key not in {"cycle", "protocol_error"}} for row in observed_merge]
    passed = (
        clean_cluster_obs == expected_clusters
        and clean_merge_obs == expected["merged"]
        and not any(row["protocol_error"] for cluster_rows in observed_clusters for row in cluster_rows)
        and not any(row["protocol_error"] for row in observed_merge)
        and not summary["c0_error"]
        and not summary["c1_error"]
        and not summary["merge_error"]
        and summary["c0_accept"] == len(_command_schedule())
        and summary["c1_accept"] == len(_command_schedule())
        and summary["c0_complete"] == len(_command_schedule())
        and summary["c1_complete"] == len(_command_schedule())
        and summary["merge_complete"] == len(expected["merged"])
    )
    return {
        "version": 1,
        "model": "score32_exact_partial_pair_probe_v1",
        "decision": "pass" if passed else "fail",
        "equivalence_pass": passed,
        "semantic_profile": "score32_online_exact_partial_pair_merge_v1",
        "command_count": len(_command_schedule()),
        "cluster_result_count": [len(rows) for rows in observed_clusters],
        "merge_result_count": len(observed_merge),
        "cluster_hashes": [_hash(rows) for rows in clean_cluster_obs],
        "merge_hash": _hash(clean_merge_obs),
        "summary": summary,
        "expected": {
            "cluster_hashes": [_hash(rows) for rows in expected_clusters],
            "merge_hash": _hash(expected["merged"]),
        },
        "observed_clusters": observed_clusters,
        "observed_merge": observed_merge,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
