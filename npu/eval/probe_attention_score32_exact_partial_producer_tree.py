#!/usr/bin/env python3
"""Probe the first producer-coupled exact reduction slice with native overlap timing."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree import generate as generate_tree
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    exact_banked_finalized_tree_full_wave_saturated_service,
    exact_partial_producer_tree_service_manifest,
    finalizer_accept_interval_cycles,
    finalizer_output_latency_cycles,
    finalize_partial_beat,
    finalize_partial_beats,
    merge_partial_streams,
    pack_final_values,
    partial_stream_from_blocks,
    unpack_final_values,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]

_COMMAND_RE = re.compile(r"COMMAND_ACCEPT idx=(\d+) cmd=(\d+) head=(\d+) cycle=(\d+)")
_PARTIAL_RE = re.compile(
    r"PARTIAL_RESULT producer=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_ROOT_RE = re.compile(
    r"ROOT_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) first_root=(-?\d+) last_root=(-?\d+) protocol_error=(\d+) "
    r"command_accept=(\d+) command_complete=(\d+) p0_accept=(\d+) p1_accept=(\d+) p0_complete=(\d+) "
    r"p1_complete=(\d+) p0_leaf_stall=(\d+) p1_leaf_stall=(\d+) tree_stall=(\d+) root_completed=(\d+) "
    r"finalizer_accepted=(\d+) p0_error=(\d+) p1_error=(\d+) tree_error=(\d+) order_error=(\d+) finalizer_error=(\d+)"
)
_STANDALONE_PARTIAL_RE = re.compile(
    r"PARTIAL_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_STANDALONE_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) protocol_error=(\d+) accept=(\d+) complete=(\d+)"
)

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


def _default_config() -> JsonDict:
    return {
        "top_name": "attention_score32_exact_partial_producer_tree_c2_r2_l8_b59",
        "attention_score32_exact_partial_producer_tree": {
            "producers": 2,
            "clusters": 2,
            "radix": 2,
            "max_blocks": 16,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": 8,
            "finalizer_banks": 59,
        },
        "probe_defaults": {
            "heads": 4,
        },
    }


def _command_schedule(heads: int) -> tuple[dict[str, int], ...]:
    if heads < 1 or heads > 32:
        raise ValueError("heads must be in [1, 32]")
    schedule = []
    for head in range(heads):
        multiplier, shift = ((1 << 20), 0) if head % 3 == 0 else (5 + head, 1 if head % 3 == 1 else 2)
        schedule.append(
            {
                "command_id": 0x6200 + head,
                "head_id": head,
                "multiplier": multiplier,
                "shift": shift,
            }
        )
    return tuple(schedule)


def _beats_for(producer: int, command_index: int, *, head_dim: int = 3) -> list[list[tuple[int, list[int]]]]:
    blocks: list[list[tuple[int, list[int]]]] = []
    for block in range(3):
        block_beats: list[tuple[int, list[int]]] = []
        for beat in range(head_dim):
            q = ((producer * 37 + command_index * 19 + block * 11 + beat * 7) % 63) - 31
            keys = [
                ((producer * 47 + command_index * 23 + block * 17 + beat * 13 + lane * 5) % 127) - 63
                for lane in range(8)
            ]
            block_beats.append((q, keys))
        blocks.append(block_beats)
    return blocks


def _values_for(producer: int, command_index: int) -> list[list[list[list[int]]]]:
    return [
        [
            [
                [
                    ((producer * 59 + command_index * 31 + block * 17 + value_slice * 13 + row * 11 + lane * 7) % 255)
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


def _expected(heads: int) -> JsonDict:
    commands = _command_schedule(heads)
    producer_rows: list[list[dict[str, object]]] = [[], []]
    merged_rows: list[dict[str, object]] = []
    finalized_rows: list[dict[str, object]] = []
    for producer in range(2):
        for command_index, command in enumerate(commands):
            score_rows = [
                list(
                    requantize_score_row(
                        _raw_scores(block),
                        multiplier=int(command["multiplier"]),
                        shift=int(command["shift"]),
                    )
                )
                for block in _beats_for(producer, command_index)
            ]
            partials = partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=score_rows,
                value_blocks=_values_for(producer, command_index),
            )
            producer_rows[producer].extend(
                {
                    "command_id": beat.command_id,
                    "head_id": beat.head_id,
                    "slice": beat.slice_index,
                    "last": beat.last,
                    "global_max": beat.max_score,
                    "exp_sum": beat.exp_sum,
                    "value": list(beat.numerators),
                }
                for beat in partials
            )

    for command_index, command in enumerate(commands):
        left = partial_stream_from_blocks(
            command_id=int(command["command_id"]),
            head_id=int(command["head_id"]),
            score_rows=[
                list(
                    requantize_score_row(
                        _raw_scores(block),
                        multiplier=int(command["multiplier"]),
                        shift=int(command["shift"]),
                    )
                )
                for block in _beats_for(0, command_index)
            ],
            value_blocks=_values_for(0, command_index),
        )
        right = partial_stream_from_blocks(
            command_id=int(command["command_id"]),
            head_id=int(command["head_id"]),
            score_rows=[
                list(
                    requantize_score_row(
                        _raw_scores(block),
                        multiplier=int(command["multiplier"]),
                        shift=int(command["shift"]),
                    )
                )
                for block in _beats_for(1, command_index)
            ],
            value_blocks=_values_for(1, command_index),
        )
        merged = merge_partial_streams(left, right)
        merged_rows.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in merged
        )
        finalized_rows.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "value": list(beat.values),
            }
            for beat in finalize_partial_beats(merged)
        )

    return {
        "commands": commands,
        "producer_rows": producer_rows,
        "merged_rows": merged_rows,
        "finalized_rows": finalized_rows,
        "producer_hash": [_hash(producer_rows[0]), _hash(producer_rows[1])],
        "merged_hash": _hash(merged_rows),
        "final_hash": _hash(finalized_rows),
    }


def _config(config: JsonDict, *, heads: int) -> JsonDict:
    merged = json.loads(json.dumps(config))
    probe_defaults = merged.setdefault("probe_defaults", {})
    if isinstance(probe_defaults, dict):
        probe_defaults["heads"] = heads
    return merged


def _ready_init(pattern: tuple[bool, ...]) -> str:
    return "\n".join(
        f"    root_ready_mem[{index}] = 1'b{1 if value else 0};" for index, value in enumerate(pattern)
    )


def _testbench(*, top_name: str, heads: int, output_ready_pattern: tuple[bool, ...]) -> str:
    commands = _command_schedule(heads)
    producer_beats = []
    producer_lasts = []
    for producer in range(2):
        flat = [
            beat
            for command_index in range(heads)
            for block in _beats_for(producer, command_index)
            for beat in block
        ]
        lasts = [
            1 if beat_index % 3 == 2 else 0
            for command_index in range(heads)
            for block in _beats_for(producer, command_index)
            for beat_index, _ in enumerate(block)
        ]
        producer_beats.append(flat)
        producer_lasts.append(lasts)

    cmd_init = "\n".join(
        f"    cmd_id_mem[{index}] = 16'h{int(command['command_id']):04x}; "
        f"cmd_head_mem[{index}] = 5'd{int(command['head_id'])}; "
        f"cmd_mult_mem[{index}] = 32'd{int(command['multiplier'])}; "
        f"cmd_shift_mem[{index}] = 6'd{int(command['shift'])};"
        for index, command in enumerate(commands)
    )
    beat_init0 = "\n".join(
        f"    q_mem0[{index}] = {_signed_literal(q, 8)}; k_mem0[{index}] = 64'h{_pack(keys, 8):016x}; last_mem0[{index}] = 1'b{producer_lasts[0][index]};"
        for index, (q, keys) in enumerate(producer_beats[0])
    )
    beat_init1 = "\n".join(
        f"    q_mem1[{index}] = {_signed_literal(q, 8)}; k_mem1[{index}] = 64'h{_pack(keys, 8):016x}; last_mem1[{index}] = 1'b{producer_lasts[1][index]};"
        for index, (q, keys) in enumerate(producer_beats[1])
    )
    value_init = []
    for producer in range(2):
        for command_index in range(heads):
            values = _values_for(producer, command_index)
            for block in range(3):
                for value_slice in range(16):
                    flat = [lane for row in values[block][value_slice] for lane in row]
                    value_init.append(
                        f"    value_mem[{(((producer * heads) + command_index) * 3 + block) * 16 + value_slice}] = 512'h{_pack(flat, 8):0128x};"
                    )
    timeout_cycles = max(40000, heads * 700)
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer HEADS = {heads};
  localparam integer BLOCK_COUNT = 3;
  localparam integer HEAD_DIM = 3;
  localparam integer BEATS_PER_COMMAND = BLOCK_COUNT * HEAD_DIM;
  localparam integer TOTAL_BEATS = HEADS * BEATS_PER_COMMAND;
  localparam integer TOTAL_RESULTS = HEADS * 16;
  localparam integer ROOT_READY_PATTERN_LEN = {len(output_ready_pattern)};
  reg clk = 0, rst_n = 0;
  integer cycle = 0;
  integer issued_commands = 0;
  integer input_index0 = 0;
  integer input_index1 = 0;
  integer active_cmd0 = 0;
  integer active_cmd1 = 0;
  integer root_seen = 0;
  integer first_root_cycle = -1;
  integer last_root_cycle = -1;
  reg pending_summary = 0;

  reg [15:0] cmd_id_mem [0:HEADS-1];
  reg [4:0] cmd_head_mem [0:HEADS-1];
  reg [31:0] cmd_mult_mem [0:HEADS-1];
  reg [5:0] cmd_shift_mem [0:HEADS-1];
  reg signed [7:0] q_mem0 [0:TOTAL_BEATS-1];
  reg [63:0] k_mem0 [0:TOTAL_BEATS-1];
  reg last_mem0 [0:TOTAL_BEATS-1];
  reg signed [7:0] q_mem1 [0:TOTAL_BEATS-1];
  reg [63:0] k_mem1 [0:TOTAL_BEATS-1];
  reg last_mem1 [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:(2*HEADS*BLOCK_COUNT*16)-1];
  reg root_ready_mem [0:ROOT_READY_PATTERN_LEN-1];

  reg command_valid;
  wire command_ready;
  reg producer0_input_valid;
  wire producer0_input_ready;
  reg producer0_input_last;
  reg signed [7:0] producer0_input_a;
  reg signed [63:0] producer0_input_b;
  wire producer0_value_read_req_valid;
  reg producer0_value_read_req_ready;
  wire [13:0] producer0_value_read_req_address;
  wire [3:0] producer0_value_read_req_slice;
  reg producer0_value_response_valid;
  wire producer0_value_response_ready;
  reg [13:0] producer0_value_response_address;
  reg [3:0] producer0_value_response_slice;
  reg [511:0] producer0_value_response_matrix;
  reg producer1_input_valid;
  wire producer1_input_ready;
  reg producer1_input_last;
  reg signed [7:0] producer1_input_a;
  reg signed [63:0] producer1_input_b;
  wire producer1_value_read_req_valid;
  reg producer1_value_read_req_ready;
  wire [13:0] producer1_value_read_req_address;
  wire [3:0] producer1_value_read_req_slice;
  reg producer1_value_response_valid;
  wire producer1_value_response_ready;
  reg [13:0] producer1_value_response_address;
  reg [3:0] producer1_value_response_slice;
  reg [511:0] producer1_value_response_matrix;
  wire root_valid;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [31:0] cycle_count;
  wire [31:0] command_accept_count;
  wire [31:0] command_completed_count;
  wire [31:0] producer0_command_accept_count;
  wire [31:0] producer1_command_accept_count;
  wire [31:0] producer0_partial_completed_count;
  wire [31:0] producer1_partial_completed_count;
  wire [31:0] producer0_leaf_stall_cycles;
  wire [31:0] producer1_leaf_stall_cycles;
  wire [1:0] producer_partial_valid;
  wire [1:0] producer_partial_ready;
  wire [1:0] producer_partial_last;
  wire [31:0] tree_root_completed_count;
  wire [31:0] finalizer_accepted_count;
  wire [31:0] order_fifo_occupancy;
  wire [31:0] order_fifo_high_watermark;
  wire [31:0] order_enqueued_count;
  wire [31:0] order_dequeued_count;
  wire [31:0] tree_dispatch_stall_cycles;
  wire [31:0] dispatch_bank_id;
  wire [31:0] head_bank_id;
  wire [31:0] node_completed_count;
  wire [31:0] stage_completed_count;
  wire [0:0] node_protocol_error;
  wire [0:0] stage_protocol_error;
  wire [58:0] bank_protocol_error;
  wire [58:0] bank_outstanding;
  wire [1:0] producer_protocol_error;
  wire tree_protocol_error;
  wire order_protocol_error;
  wire finalizer_protocol_error;
  wire protocol_error;

  reg pending0 = 0, pending1 = 0;
  reg [13:0] pending_addr0 = 0, pending_addr1 = 0;
  reg [3:0] pending_slice0 = 0, pending_slice1 = 0;
  integer pending_delay0 = 0, pending_delay1 = 0;

  always #5 clk = ~clk;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .command_id(cmd_id_mem[issued_commands]),
      .command_head_id(cmd_head_mem[issued_commands]),
      .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(cmd_mult_mem[issued_commands]),
      .command_score_shift(cmd_shift_mem[issued_commands]),
      .producer0_input_valid(producer0_input_valid),
      .producer0_input_ready(producer0_input_ready),
      .producer0_input_last(producer0_input_last),
      .producer0_input_a(producer0_input_a),
      .producer0_input_b(producer0_input_b),
      .producer0_value_read_req_valid(producer0_value_read_req_valid),
      .producer0_value_read_req_ready(producer0_value_read_req_ready),
      .producer0_value_read_req_address(producer0_value_read_req_address),
      .producer0_value_read_req_slice(producer0_value_read_req_slice),
      .producer0_value_response_valid(producer0_value_response_valid),
      .producer0_value_response_ready(producer0_value_response_ready),
      .producer0_value_response_address(producer0_value_response_address),
      .producer0_value_response_slice(producer0_value_response_slice),
      .producer0_value_response_matrix(producer0_value_response_matrix),
      .producer1_input_valid(producer1_input_valid),
      .producer1_input_ready(producer1_input_ready),
      .producer1_input_last(producer1_input_last),
      .producer1_input_a(producer1_input_a),
      .producer1_input_b(producer1_input_b),
      .producer1_value_read_req_valid(producer1_value_read_req_valid),
      .producer1_value_read_req_ready(producer1_value_read_req_ready),
      .producer1_value_read_req_address(producer1_value_read_req_address),
      .producer1_value_read_req_slice(producer1_value_read_req_slice),
      .producer1_value_response_valid(producer1_value_response_valid),
      .producer1_value_response_ready(producer1_value_response_ready),
      .producer1_value_response_address(producer1_value_response_address),
      .producer1_value_response_slice(producer1_value_response_slice),
      .producer1_value_response_matrix(producer1_value_response_matrix),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(cycle_count),
      .command_accept_count(command_accept_count),
      .command_completed_count(command_completed_count),
      .producer0_command_accept_count(producer0_command_accept_count),
      .producer1_command_accept_count(producer1_command_accept_count),
      .producer0_partial_completed_count(producer0_partial_completed_count),
      .producer1_partial_completed_count(producer1_partial_completed_count),
      .producer0_leaf_stall_cycles(producer0_leaf_stall_cycles),
      .producer1_leaf_stall_cycles(producer1_leaf_stall_cycles),
      .producer_partial_valid(producer_partial_valid),
      .producer_partial_ready(producer_partial_ready),
      .producer_partial_last(producer_partial_last),
      .tree_root_completed_count(tree_root_completed_count),
      .finalizer_accepted_count(finalizer_accepted_count),
      .order_fifo_occupancy(order_fifo_occupancy),
      .order_fifo_high_watermark(order_fifo_high_watermark),
      .order_enqueued_count(order_enqueued_count),
      .order_dequeued_count(order_dequeued_count),
      .tree_dispatch_stall_cycles(tree_dispatch_stall_cycles),
      .dispatch_bank_id(dispatch_bank_id),
      .head_bank_id(head_bank_id),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .bank_protocol_error(bank_protocol_error),
      .bank_outstanding(bank_outstanding),
      .producer_protocol_error(producer_protocol_error),
      .tree_protocol_error(tree_protocol_error),
      .order_protocol_error(order_protocol_error),
      .finalizer_protocol_error(finalizer_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && issued_commands < HEADS && (((cycle + issued_commands) % 5) != 2);
    producer0_input_valid =
        rst_n && input_index0 < (issued_commands * BEATS_PER_COMMAND) && ((cycle % 5) != 1);
    producer1_input_valid =
        rst_n && input_index1 < (issued_commands * BEATS_PER_COMMAND)
        && (((cycle + 2) % 7) != 3) && (((cycle + input_index1) % 11) != 5);
    producer0_input_a = input_index0 < TOTAL_BEATS ? q_mem0[input_index0] : 0;
    producer0_input_b = input_index0 < TOTAL_BEATS ? k_mem0[input_index0] : 0;
    producer0_input_last = input_index0 < TOTAL_BEATS ? last_mem0[input_index0] : 0;
    producer1_input_a = input_index1 < TOTAL_BEATS ? q_mem1[input_index1] : 0;
    producer1_input_b = input_index1 < TOTAL_BEATS ? k_mem1[input_index1] : 0;
    producer1_input_last = input_index1 < TOTAL_BEATS ? last_mem1[input_index1] : 0;
    producer0_value_read_req_ready = ((cycle + 1) % 4) != 1;
    producer1_value_read_req_ready = ((cycle + 3) % 6) != 2;
    root_ready = root_ready_mem[cycle % ROOT_READY_PATTERN_LEN];
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issued_commands <= 0;
      input_index0 <= 0;
      input_index1 <= 0;
      active_cmd0 <= 0;
      active_cmd1 <= 0;
      root_seen <= 0;
      first_root_cycle <= -1;
      last_root_cycle <= -1;
      pending_summary <= 1'b0;
      pending0 <= 0;
      pending1 <= 0;
      pending_delay0 <= 0;
      pending_delay1 <= 0;
      producer0_value_response_valid <= 0;
      producer1_value_response_valid <= 0;
      producer0_value_response_address <= 0;
      producer1_value_response_address <= 0;
      producer0_value_response_slice <= 0;
      producer1_value_response_slice <= 0;
      producer0_value_response_matrix <= 0;
      producer1_value_response_matrix <= 0;
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        $display("COMMAND_ACCEPT idx=%0d cmd=%0d head=%0d cycle=%0d",
                 issued_commands, cmd_id_mem[issued_commands], cmd_head_mem[issued_commands], cycle);
        active_cmd0 <= issued_commands;
        active_cmd1 <= issued_commands;
        issued_commands <= issued_commands + 1;
      end
      if (producer0_input_valid && producer0_input_ready) input_index0 <= input_index0 + 1;
      if (producer1_input_valid && producer1_input_ready) input_index1 <= input_index1 + 1;

      if (producer0_value_read_req_valid && producer0_value_read_req_ready) begin
        if (pending0 || producer0_value_response_valid) $fatal(1, "producer0 multiple outstanding value requests");
        pending0 <= 1;
        pending_addr0 <= producer0_value_read_req_address;
        pending_slice0 <= producer0_value_read_req_slice;
        pending_delay0 <= ((producer0_value_read_req_slice + active_cmd0) % 3) + 1;
      end
      if (producer1_value_read_req_valid && producer1_value_read_req_ready) begin
        if (pending1 || producer1_value_response_valid) $fatal(1, "producer1 multiple outstanding value requests");
        pending1 <= 1;
        pending_addr1 <= producer1_value_read_req_address;
        pending_slice1 <= producer1_value_read_req_slice;
        pending_delay1 <= ((producer1_value_read_req_address + producer1_value_read_req_slice + active_cmd1) % 4) + 1;
      end

      if (pending0) begin
        if (pending_delay0 == 0) begin
          pending0 <= 0;
          producer0_value_response_valid <= 1;
          producer0_value_response_address <= pending_addr0;
          producer0_value_response_slice <= pending_slice0;
          producer0_value_response_matrix <= value_mem[((active_cmd0 * BLOCK_COUNT) + pending_addr0) * 16 + pending_slice0];
        end else begin
          pending_delay0 <= pending_delay0 - 1;
        end
      end
      if (pending1) begin
        if (pending_delay1 == 0) begin
          pending1 <= 0;
          producer1_value_response_valid <= 1;
          producer1_value_response_address <= pending_addr1;
          producer1_value_response_slice <= pending_slice1;
          producer1_value_response_matrix <= value_mem[(((HEADS + active_cmd1) * BLOCK_COUNT) + pending_addr1) * 16 + pending_slice1];
        end else begin
          pending_delay1 <= pending_delay1 - 1;
        end
      end
      if (producer0_value_response_valid && producer0_value_response_ready) producer0_value_response_valid <= 0;
      if (producer1_value_response_valid && producer1_value_response_ready) producer1_value_response_valid <= 0;

      if (producer_partial_valid[0] && producer_partial_ready[0]) begin
        $display("PARTIAL_RESULT producer=0 cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
                 dut.producer0_result_command_id_w, dut.producer0_result_head_id_w, dut.producer0_result_slice_w,
                 dut.producer0_result_last_w, $signed(dut.producer0_result_global_max_w), dut.producer0_result_exp_sum_w,
                 dut.producer0_result_value_w, cycle);
      end
      if (producer_partial_valid[1] && producer_partial_ready[1]) begin
        $display("PARTIAL_RESULT producer=1 cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
                 dut.producer1_result_command_id_w, dut.producer1_result_head_id_w, dut.producer1_result_slice_w,
                 dut.producer1_result_last_w, $signed(dut.producer1_result_global_max_w), dut.producer1_result_exp_sum_w,
                 dut.producer1_result_value_w, cycle);
      end
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        if (first_root_cycle < 0) first_root_cycle <= cycle;
        last_root_cycle <= cycle;
        root_seen <= root_seen + 1;
        if (root_seen + 1 == TOTAL_RESULTS) pending_summary <= 1'b1;
      end
      if (pending_summary) begin
        $display("SUMMARY outputs=%0d drain=%0d first_root=%0d last_root=%0d protocol_error=%0d command_accept=%0d command_complete=%0d p0_accept=%0d p1_accept=%0d p0_complete=%0d p1_complete=%0d p0_leaf_stall=%0d p1_leaf_stall=%0d tree_stall=%0d root_completed=%0d finalizer_accepted=%0d p0_error=%0d p1_error=%0d tree_error=%0d order_error=%0d finalizer_error=%0d",
                 root_seen, cycle + 1, first_root_cycle, last_root_cycle, protocol_error, command_accept_count,
                 command_completed_count, producer0_command_accept_count, producer1_command_accept_count,
                 producer0_partial_completed_count, producer1_partial_completed_count, producer0_leaf_stall_cycles,
                 producer1_leaf_stall_cycles, tree_dispatch_stall_cycles, tree_root_completed_count,
                 finalizer_accepted_count, producer_protocol_error[0], producer_protocol_error[1],
                 tree_protocol_error, order_protocol_error, finalizer_protocol_error);
        #1 $finish;
      end
      if (cycle > {timeout_cycles}) $fatal(1, "timeout");
    end
  end

  initial begin
{cmd_init}
{beat_init0}
{beat_init1}
{chr(10).join(value_init)}
{_ready_init(output_ready_pattern)}
    producer0_value_response_valid = 0;
    producer1_value_response_valid = 0;
    producer0_value_response_address = 0;
    producer1_value_response_address = 0;
    producer0_value_response_slice = 0;
    producer1_value_response_slice = 0;
    producer0_value_response_matrix = 0;
    producer1_value_response_matrix = 0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _run_case(
    config: JsonDict,
    *,
    heads: int,
    output_ready_pattern: tuple[bool, ...],
) -> JsonDict:
    expected = _expected(heads)
    run_config = _config(config, heads=heads)
    with tempfile.TemporaryDirectory(
        prefix=f"score32_exact_partial_producer_tree_h{heads}_native_"
    ) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate_tree(run_config, temp_dir / "rtl")
        tb_path = temp_dir / "tb.sv"
        tb_path.write_text(
            _testbench(
                top_name=str(run_config["top_name"]),
                heads=heads,
                output_ready_pattern=output_ready_pattern,
            ),
            encoding="utf-8",
        )
        simv = temp_dir / "simv"
        compiled = subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(simv),
                str(temp_dir / "rtl" / "top.v"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=900)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")

    command_accepts: list[dict[str, int]] = []
    partials: list[list[dict[str, object]]] = [[], []]
    root_rows: list[dict[str, object]] = []
    summary: dict[str, int] | None = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _COMMAND_RE.fullmatch(stripped):
            command_accepts.append(
                {
                    "index": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "cycle": int(match.group(4)),
                }
            )
        elif match := _PARTIAL_RE.fullmatch(stripped):
            producer = int(match.group(1))
            partials[producer].append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": int(match.group(8), 16),
                    "cycle": int(match.group(9)),
                }
            )
        elif match := _ROOT_RE.fullmatch(stripped):
            root_rows.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "value": list(unpack_final_values(int(match.group(5), 16))),
                    "cycle": int(match.group(6)),
                }
            )
        elif match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "drain_cycles": int(match.group(2)),
                "first_root_cycle": int(match.group(3)),
                "last_root_cycle": int(match.group(4)),
                "protocol_error": int(match.group(5)),
                "command_accept_count": int(match.group(6)),
                "command_complete_count": int(match.group(7)),
                "producer0_command_accept_count": int(match.group(8)),
                "producer1_command_accept_count": int(match.group(9)),
                "producer0_partial_completed_count": int(match.group(10)),
                "producer1_partial_completed_count": int(match.group(11)),
                "producer0_leaf_stall_cycles": int(match.group(12)),
                "producer1_leaf_stall_cycles": int(match.group(13)),
                "tree_dispatch_stall_cycles": int(match.group(14)),
                "tree_root_completed_count": int(match.group(15)),
                "finalizer_accepted_count": int(match.group(16)),
                "producer0_protocol_error": int(match.group(17)),
                "producer1_protocol_error": int(match.group(18)),
                "tree_protocol_error": int(match.group(19)),
                "order_protocol_error": int(match.group(20)),
                "finalizer_protocol_error": int(match.group(21)),
            }
    if summary is None:
        raise RuntimeError(f"missing SUMMARY line in simulation output:\n{run.stdout}")

    expected_root = expected["finalized_rows"]
    observed_root = [
        {
            "command_id": row["command_id"],
            "head_id": row["head_id"],
            "slice": row["slice"],
            "last": row["last"],
            "value": row["value"],
        }
        for row in root_rows
    ]
    partial_windows = []
    for producer in range(2):
        cycles = [int(row["cycle"]) for row in partials[producer]]
        partial_windows.append(
            {
                "first_cycle": cycles[0] if cycles else -1,
                "last_cycle": cycles[-1] if cycles else -1,
                "beats": len(cycles),
            }
        )
    return {
        "heads": heads,
        "command_accepts": command_accepts,
        "producer_partial_windows": partial_windows,
        "producer_partial_hashes": [
            _hash(
                [
                    {
                        "command_id": row["command_id"],
                        "head_id": row["head_id"],
                        "slice": row["slice"],
                        "last": row["last"],
                        "global_max": row["global_max"],
                        "exp_sum": row["exp_sum"],
                        "value": row["value"],
                    }
                    for row in partials[index]
                ]
            )
            for index in range(2)
        ],
        "outputs": len(root_rows),
        "observed_root": observed_root,
        "observed_root_hash": _hash(observed_root),
        "expected_root_hash": expected["final_hash"],
        "expected_outputs": len(expected_root),
        "summary": summary,
        "passed": observed_root == expected_root
        and len(command_accepts) == heads
        and summary["protocol_error"] == 0
        and summary["producer0_protocol_error"] == 0
        and summary["producer1_protocol_error"] == 0
        and summary["tree_protocol_error"] == 0
        and summary["order_protocol_error"] == 0
        and summary["finalizer_protocol_error"] == 0,
    }


def _standalone_testbench(*, cluster_top_name: str, producer: int, heads: int) -> str:
    commands = _command_schedule(heads)
    flat = [
        beat
        for command_index in range(heads)
        for block in _beats_for(producer, command_index)
        for beat in block
    ]
    lasts = [
        1 if beat_index % 3 == 2 else 0
        for command_index in range(heads)
        for block in _beats_for(producer, command_index)
        for beat_index, _ in enumerate(block)
    ]
    cmd_init = "\n".join(
        f"    cmd_id_mem[{index}] = 16'h{int(command['command_id']):04x}; "
        f"cmd_head_mem[{index}] = 5'd{int(command['head_id'])}; "
        f"cmd_mult_mem[{index}] = 32'd{int(command['multiplier'])}; "
        f"cmd_shift_mem[{index}] = 6'd{int(command['shift'])};"
        for index, command in enumerate(commands)
    )
    beat_init = "\n".join(
        f"    q_mem[{index}] = {_signed_literal(q, 8)}; k_mem[{index}] = 64'h{_pack(keys, 8):016x}; last_mem[{index}] = 1'b{lasts[index]};"
        for index, (q, keys) in enumerate(flat)
    )
    value_init = []
    for command_index in range(heads):
        values = _values_for(producer, command_index)
        for block in range(3):
            for value_slice in range(16):
                flat_values = [lane for row in values[block][value_slice] for lane in row]
                value_init.append(
                    f"    value_mem[{((command_index * 3) + block) * 16 + value_slice}] = 512'h{_pack(flat_values, 8):0128x};"
                )
    ready_expr = "((cycle + 1) % 4) != 1" if producer == 0 else "((cycle + 3) % 6) != 2"
    input_expr = "((cycle % 5) != 1)" if producer == 0 else "(((cycle + 2) % 7) != 3) && (((cycle + input_index) % 11) != 5)"
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer HEADS = {heads};
  localparam integer BLOCK_COUNT = 3;
  localparam integer BEATS_PER_COMMAND = BLOCK_COUNT * 3;
  localparam integer TOTAL_BEATS = HEADS * BEATS_PER_COMMAND;
  localparam integer TOTAL_RESULTS = HEADS * 16;
  reg clk = 0, rst_n = 0;
  integer cycle = 0;
  integer issue_index = 0;
  integer input_index = 0;
  integer active_cmd = 0;
  integer seen = 0;
  reg [15:0] cmd_id_mem [0:HEADS-1];
  reg [4:0] cmd_head_mem [0:HEADS-1];
  reg [31:0] cmd_mult_mem [0:HEADS-1];
  reg [5:0] cmd_shift_mem [0:HEADS-1];
  reg signed [7:0] q_mem [0:TOTAL_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_BEATS-1];
  reg last_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:(HEADS*BLOCK_COUNT*16)-1];
  reg command_valid;
  wire command_ready;
  reg input_valid;
  wire input_ready;
  reg input_last;
  reg signed [7:0] input_a;
  reg signed [63:0] input_b;
  wire value_read_req_valid;
  reg value_read_req_ready;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg value_response_valid;
  wire value_response_ready;
  reg [13:0] value_response_address;
  reg [3:0] value_response_slice;
  reg [511:0] value_response_matrix;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire [4:0] result_head_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire result_last;
  wire [327:0] result_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  wire [31:0] cycle_count;
  wire protocol_error;
  reg pending = 0;
  reg [13:0] pending_addr = 0;
  reg [3:0] pending_slice = 0;
  integer pending_delay = 0;

  always #5 clk = ~clk;

  {cluster_top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .command_id(cmd_id_mem[issue_index]),
      .command_head_id(cmd_head_mem[issue_index]),
      .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(cmd_mult_mem[issue_index]),
      .command_score_shift(cmd_shift_mem[issue_index]),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_a(input_a),
      .input_b(input_b),
      .value_read_req_valid(value_read_req_valid),
      .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address),
      .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid),
      .value_response_ready(value_response_ready),
      .value_response_address(value_response_address),
      .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix),
      .result_valid(result_valid),
      .result_ready(result_ready),
      .result_command_id(result_command_id),
      .result_head_id(result_head_id),
      .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum),
      .result_slice(result_slice),
      .result_last(result_last),
      .result_value(result_value),
      .accepted_count(accepted_count),
      .completed_count(completed_count),
      .cycle_count(cycle_count),
      .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && issue_index < HEADS && (((cycle + issue_index) % 5) != 2);
    input_valid = rst_n && input_index < (issue_index * BEATS_PER_COMMAND) && {input_expr};
    input_a = input_index < TOTAL_BEATS ? q_mem[input_index] : 0;
    input_b = input_index < TOTAL_BEATS ? k_mem[input_index] : 0;
    input_last = input_index < TOTAL_BEATS ? last_mem[input_index] : 0;
    value_read_req_ready = {ready_expr};
    result_ready = 1'b1;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issue_index <= 0;
      input_index <= 0;
      active_cmd <= 0;
      seen <= 0;
      pending <= 0;
      pending_delay <= 0;
      value_response_valid <= 0;
      value_response_address <= 0;
      value_response_slice <= 0;
      value_response_matrix <= 0;
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        active_cmd <= issue_index;
        issue_index <= issue_index + 1;
      end
      if (input_valid && input_ready) input_index <= input_index + 1;
      if (value_read_req_valid && value_read_req_ready) begin
        if (pending || value_response_valid) $fatal(1, "multiple outstanding value requests");
        pending <= 1;
        pending_addr <= value_read_req_address;
        pending_slice <= value_read_req_slice;
        pending_delay <= ((value_read_req_slice + active_cmd + {producer}) % 4) + 1;
      end
      if (pending) begin
        if (pending_delay == 0) begin
          pending <= 0;
          value_response_valid <= 1;
          value_response_address <= pending_addr;
          value_response_slice <= pending_slice;
          value_response_matrix <= value_mem[((active_cmd * BLOCK_COUNT) + pending_addr) * 16 + pending_slice];
        end else begin
          pending_delay <= pending_delay - 1;
        end
      end
      if (value_response_valid && value_response_ready) value_response_valid <= 0;
      if (result_valid && result_ready) begin
        $display("PARTIAL_RESULT cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
                 result_command_id, result_head_id, result_slice, result_last, $signed(result_global_max),
                 result_exp_sum, result_value, cycle);
        seen <= seen + 1;
        if (seen + 1 == TOTAL_RESULTS) begin
          $display("SUMMARY outputs=%0d drain=%0d protocol_error=%0d accept=%0d complete=%0d",
                   seen + 1, cycle + 1, protocol_error, accepted_count, completed_count + 1);
          #1 $finish;
        end
      end
      if (cycle > 80000) $fatal(1, "timeout");
    end
  end

  initial begin
{cmd_init}
{beat_init}
{chr(10).join(value_init)}
    value_response_valid = 0;
    value_response_address = 0;
    value_response_slice = 0;
    value_response_matrix = 0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _run_standalone_producer_case(config: JsonDict, *, producer: int, heads: int) -> JsonDict:
    body = dict(config["attention_score32_exact_partial_producer_tree"])
    cluster_top_name = f"standalone_exact_partial_producer_{producer}"
    cluster_config = {
        "top_name": cluster_top_name,
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": int(body["max_blocks"]),
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
            "result_mode": "exact_partial",
            "head_id_bits": int(body["head_id_bits"]),
        },
    }
    with tempfile.TemporaryDirectory(prefix=f"standalone_exact_partial_producer_{producer}_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate_cluster(cluster_config, temp_dir / "rtl")
        tb_path = temp_dir / "tb.sv"
        tb_path.write_text(_standalone_testbench(cluster_top_name=cluster_top_name, producer=producer, heads=heads), encoding="utf-8")
        simv = temp_dir / "simv"
        compiled = subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(simv),
                str(temp_dir / "rtl" / "top.v"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=900)
        if run.returncode:
            raise RuntimeError(f"standalone producer simulation failed:\n{run.stdout}\n{run.stderr}")

    partials: list[dict[str, object]] = []
    summary: dict[str, int] | None = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _STANDALONE_PARTIAL_RE.fullmatch(stripped):
            partials.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "value": int(match.group(7), 16),
                    "cycle": int(match.group(8)),
                }
            )
        elif match := _STANDALONE_SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "drain_cycles": int(match.group(2)),
                "protocol_error": int(match.group(3)),
                "accept_count": int(match.group(4)),
                "complete_count": int(match.group(5)),
            }
    if summary is None:
        raise RuntimeError(f"missing standalone summary for producer {producer}")
    return {
        "producer": producer,
        "partials": partials,
        "summary": summary,
    }


def _staged_parallel_then_reducer_baseline(
    *,
    heads: int,
    standalone_producer_cases: list[JsonDict],
) -> JsonDict:
    producer_phase_drain_cycles = max(int(case["summary"]["drain_cycles"]) for case in standalone_producer_cases)
    producer_phase_last_partial_cycle = max(int(case["partials"][-1]["cycle"]) for case in standalone_producer_cases)
    reducer_service = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=2,
        heads=heads,
        divider_lanes=8,
        finalizer_banks=59,
    )
    reducer_phase_origin_cycle = producer_phase_drain_cycles
    return {
        "baseline_kind": "producer_parallel_then_reducer_staged",
        "producer_phase_origin_cycle": 0,
        "producer_phase_last_partial_cycle": producer_phase_last_partial_cycle,
        "producer_phase_drain_cycles": producer_phase_drain_cycles,
        "reducer_phase_origin_cycle": reducer_phase_origin_cycle,
        "reducer_service": reducer_service,
        "first_output_cycle": reducer_phase_origin_cycle + int(reducer_service["first_output_cycle"]),
        "last_output_cycle": reducer_phase_origin_cycle + int(reducer_service["last_output_cycle"]),
        "drain_cycles": reducer_phase_origin_cycle + int(reducer_service["drain_cycles"]),
    }


def _fully_serialized_producer_then_reducer_diagnostic(
    *,
    heads: int,
    standalone_producer_cases: list[JsonDict],
) -> JsonDict:
    reducer_service = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=2,
        heads=heads,
        divider_lanes=8,
        finalizer_banks=59,
    )
    producer_serialized_phase_drain_cycles = sum(int(case["summary"]["drain_cycles"]) for case in standalone_producer_cases)
    return {
        "diagnostic_kind": "producer_fully_serialized_then_reducer_staged",
        "producer_serialized_phase_drain_cycles": producer_serialized_phase_drain_cycles,
        "reducer_phase_origin_cycle": producer_serialized_phase_drain_cycles,
        "first_output_cycle": producer_serialized_phase_drain_cycles + int(reducer_service["first_output_cycle"]),
        "last_output_cycle": producer_serialized_phase_drain_cycles + int(reducer_service["last_output_cycle"]),
        "drain_cycles": producer_serialized_phase_drain_cycles + int(reducer_service["drain_cycles"]),
    }


def build_report(
    config: JsonDict | None = None,
    *,
    heads: int | None = None,
    output_ready_pattern: tuple[bool, ...] | None = None,
) -> JsonDict:
    base_config = json.loads(json.dumps(config or _default_config()))
    probe_defaults = base_config.get("probe_defaults", {})
    resolved_heads = heads or int(probe_defaults.get("heads", 4))
    ready_pattern = output_ready_pattern or (True, False, True, True, False, True, True, True, False, True)
    integrated = _run_case(
        base_config,
        heads=resolved_heads,
        output_ready_pattern=ready_pattern,
    )
    standalone0 = _run_standalone_producer_case(base_config, producer=0, heads=resolved_heads)
    standalone1 = _run_standalone_producer_case(base_config, producer=1, heads=resolved_heads)
    staged_baseline = _staged_parallel_then_reducer_baseline(
        heads=resolved_heads,
        standalone_producer_cases=[standalone0, standalone1],
    )
    diagnostic_serialized = _fully_serialized_producer_then_reducer_diagnostic(
        heads=resolved_heads,
        standalone_producer_cases=[standalone0, standalone1],
    )
    staged_overlap_cycles_saved = int(staged_baseline["drain_cycles"]) - int(integrated["summary"]["drain_cycles"])
    report = {
        "decision": "score32_exact_partial_producer_tree_overlap_pass"
        if integrated["passed"]
        and int(standalone0["summary"]["protocol_error"]) == 0
        and int(standalone1["summary"]["protocol_error"]) == 0
        else "score32_exact_partial_producer_tree_overlap_fail",
        "passed": bool(
            integrated["passed"]
            and int(standalone0["summary"]["protocol_error"]) == 0
            and int(standalone1["summary"]["protocol_error"]) == 0
        ),
        "top_name": str(base_config["top_name"]),
        "heads": resolved_heads,
        "outputs": integrated["outputs"],
        "expected_outputs": integrated["expected_outputs"],
        "observed_root_hash": integrated["observed_root_hash"],
        "expected_root_hash": integrated["expected_root_hash"],
        "command_accept_cycles": integrated["command_accepts"],
        "producer_partial_windows": integrated["producer_partial_windows"],
        "producer_leaf_stall_cycles": [
            int(integrated["summary"]["producer0_leaf_stall_cycles"]),
            int(integrated["summary"]["producer1_leaf_stall_cycles"]),
        ],
        "tree_dispatch_stall_cycles": int(integrated["summary"]["tree_dispatch_stall_cycles"]),
        "first_output_cycle": int(integrated["summary"]["first_root_cycle"]),
        "last_output_cycle": int(integrated["summary"]["last_root_cycle"]),
        "integrated_drain_cycles": int(integrated["summary"]["drain_cycles"]),
        "producer_parallel_phase_last_partial_cycle": int(staged_baseline["producer_phase_last_partial_cycle"]),
        "producer_parallel_phase_drain_cycles": int(staged_baseline["producer_phase_drain_cycles"]),
        "staged_reducer_phase_origin_cycle": int(staged_baseline["reducer_phase_origin_cycle"]),
        "staged_reducer_service_drain_cycles": int(staged_baseline["reducer_service"]["drain_cycles"]),
        "staged_reducer_service_first_output_offset": int(staged_baseline["reducer_service"]["first_output_cycle"]),
        "staged_reducer_service_last_output_offset": int(staged_baseline["reducer_service"]["last_output_cycle"]),
        "producer_parallel_then_reducer_bound_cycles": int(staged_baseline["drain_cycles"]),
        "producer_parallel_then_reducer_first_output_cycle": int(staged_baseline["first_output_cycle"]),
        "producer_parallel_then_reducer_last_output_cycle": int(staged_baseline["last_output_cycle"]),
        "producer_parallel_then_reducer_overlap_cycles_saved": staged_overlap_cycles_saved,
        "producer_parallel_then_reducer_overlap_fraction": staged_overlap_cycles_saved
        / float(max(1, int(staged_baseline["drain_cycles"]))),
        "command_accept_count": int(integrated["summary"]["command_accept_count"]),
        "command_complete_count": int(integrated["summary"]["command_complete_count"]),
        "producer_command_accept_count": [
            int(integrated["summary"]["producer0_command_accept_count"]),
            int(integrated["summary"]["producer1_command_accept_count"]),
        ],
        "producer_partial_completed_count": [
            int(integrated["summary"]["producer0_partial_completed_count"]),
            int(integrated["summary"]["producer1_partial_completed_count"]),
        ],
        "tree_root_completed_count": int(integrated["summary"]["tree_root_completed_count"]),
        "finalizer_accepted_count": int(integrated["summary"]["finalizer_accepted_count"]),
        "producer_protocol_error": [
            bool(integrated["summary"]["producer0_protocol_error"]),
            bool(integrated["summary"]["producer1_protocol_error"]),
        ],
        "tree_protocol_error": bool(integrated["summary"]["tree_protocol_error"]),
        "order_protocol_error": bool(integrated["summary"]["order_protocol_error"]),
        "finalizer_protocol_error": bool(integrated["summary"]["finalizer_protocol_error"]),
        "protocol_error": bool(integrated["summary"]["protocol_error"]),
        "standalone_producer_protocol_error": [
            bool(standalone0["summary"]["protocol_error"]),
            bool(standalone1["summary"]["protocol_error"]),
        ],
        "integrated_case": integrated,
        "producer_parallel_then_reducer_baseline": staged_baseline,
        "producer_fully_serialized_then_reducer_diagnostic": diagnostic_serialized,
        "standalone_producer_cases": [standalone0, standalone1],
        "service_model": exact_partial_producer_tree_service_manifest(
            heads=resolved_heads,
            max_blocks=int(base_config["attention_score32_exact_partial_producer_tree"]["max_blocks"]),
            divider_lanes=int(base_config["attention_score32_exact_partial_producer_tree"]["divider_lanes"]),
            finalizer_banks=int(base_config["attention_score32_exact_partial_producer_tree"]["finalizer_banks"]),
        ),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--heads", type=int, default=None)
    parser.add_argument("--root-ready-pattern", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = _default_config()
    if args.config is not None:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    pattern = None
    if args.root_ready_pattern:
        pattern = tuple(token.strip() in {"1", "true", "True"} for token in args.root_ready_pattern.split(","))
        if not pattern:
            raise SystemExit("root-ready-pattern must not be empty")
    report = build_report(config=config, heads=args.heads, output_ready_pattern=pattern)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "heads": report["heads"],
                    "outputs": report["outputs"],
                    "observed_root_hash": report["observed_root_hash"],
                    "integrated_drain_cycles": report["integrated_drain_cycles"],
                    "producer_parallel_then_reducer_bound_cycles": report[
                        "producer_parallel_then_reducer_bound_cycles"
                    ],
                    "producer_parallel_then_reducer_overlap_cycles_saved": report[
                        "producer_parallel_then_reducer_overlap_cycles_saved"
                    ],
                    "protocol_error": report["protocol_error"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
