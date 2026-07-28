#!/usr/bin/env python3
"""Probe the dual-stream GQA8 exact-partial producer against a structured reference."""

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

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import generate as generate_tree
from npu.sim.perf.attention_exact_partial import (
    exact_partial_dual_stream_gqa8_producer_service_manifest,
    merge_partial_streams,
    partial_stream_from_blocks,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]

_COMMAND_RE = re.compile(r"COMMAND_ACCEPT idx=(\d+) cmd=(\d+) head_base=(\d+) cycle=(\d+)")
_RESULT_RE = re.compile(
    r"RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) protocol_error=(\d+) command_accept=(\d+) command_complete=(\d+) "
    r"stream0_accept=(\d+) stream1_accept=(\d+) stream0_complete=(\d+) stream1_complete=(\d+) "
    r"merge_complete=(\d+) result_stall=(\d+) stream0_error=(\d+) stream1_error=(\d+) merge_error=(\d+)"
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
  initial begin
    addr_q = 0;
    rd_out_q = 0;
    for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0;
  end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) begin
        for (idx = 0; idx < 39; idx = idx + 1) begin
          if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
        end
      end
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


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((int(value) & mask) << (index * bits) for index, value in enumerate(values))


def _default_config() -> JsonDict:
    return {
        "top_name": "attention_score32_exact_partial_gqa8_dual_stream_producer_b8",
        "attention_score32_exact_partial_gqa8_dual_stream_producer": {
            "streams": 2,
            "query_heads_per_stream": 8,
            "max_blocks": 8,
            "value_slices": 16,
            "head_id_bits": 5,
        },
        "probe_defaults": {
            "heads": 8,
            "command_count": 1,
            "blocks_per_stream": 2,
            "head_dim": 3,
        },
    }


def _resolve_workload(
    config: JsonDict,
    *,
    heads: int | None,
    command_count: int | None,
    blocks_per_stream: int | None,
    head_dim: int | None,
    head_bases: tuple[int, ...] | None,
) -> dict[str, object]:
    defaults = config.get("probe_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    resolved_heads = int(heads if heads is not None else defaults.get("heads", 8))
    resolved_command_count = int(command_count if command_count is not None else defaults.get("command_count", resolved_heads // 8))
    resolved_blocks_per_stream = int(blocks_per_stream if blocks_per_stream is not None else defaults.get("blocks_per_stream", 2))
    resolved_head_dim = int(head_dim if head_dim is not None else defaults.get("head_dim", 3))
    configured_head_bases = head_bases
    if configured_head_bases is None and isinstance(defaults.get("head_bases"), list):
        configured_head_bases = tuple(int(value) for value in defaults["head_bases"])

    if resolved_heads < 8 or resolved_heads > 32 or resolved_heads % 8:
        raise ValueError("heads must be a multiple of 8 in [8, 32]")
    if resolved_command_count < 1:
        raise ValueError("command_count must be positive")
    if resolved_blocks_per_stream < 1 or resolved_blocks_per_stream > 8:
        raise ValueError("blocks_per_stream must be in [1, 8]")
    if resolved_head_dim < 1:
        raise ValueError("head_dim must be positive")
    if configured_head_bases is None:
        head_groups = tuple(group * 8 for group in range(resolved_heads // 8))
        configured_head_bases = tuple(head_groups[index % len(head_groups)] for index in range(resolved_command_count))
    if len(configured_head_bases) != resolved_command_count:
        raise ValueError("head_bases length must match command_count")
    for base in configured_head_bases:
        if base % 8 or base < 0 or base > 24:
            raise ValueError("head_bases entries must be aligned to 8 in [0, 24]")
    return {
        "heads": resolved_heads,
        "command_count": resolved_command_count,
        "blocks_per_stream": resolved_blocks_per_stream,
        "head_dim": resolved_head_dim,
        "head_bases": tuple(configured_head_bases),
        "llama_wave_reference_cycles": defaults.get("llama_wave_reference_cycles"),
    }


def _command_schedule(*, heads: int, command_count: int, head_bases: tuple[int, ...]) -> tuple[dict[str, int], ...]:
    if heads < 8 or heads > 32 or heads % 8:
        raise ValueError("heads must be a multiple of 8 in [8, 32]")
    schedule = []
    for group in range(command_count):
        head_base = int(head_bases[group])
        multiplier, shift = ((1 << 20), 0) if group % 3 == 0 else (7 + group, 1 if group % 3 == 1 else 2)
        schedule.append(
            {
                "command_id": 0x7200 + group,
                "head_base": head_base,
                "multiplier": multiplier,
                "shift": shift,
            }
    )
    return tuple(schedule)


def _block_beats(
    stream: int,
    command_index: int,
    *,
    blocks_per_stream: int,
    head_dim: int,
) -> list[list[tuple[list[int], list[int]]]]:
    blocks: list[list[tuple[list[int], list[int]]]] = []
    for block in range(blocks_per_stream):
        block_beats: list[tuple[list[int], list[int]]] = []
        for beat in range(head_dim):
            queries = [
                ((stream * 41 + command_index * 29 + block * 17 + beat * 11 + head * 7) % 63) - 31
                for head in range(8)
            ]
            keys = [
                ((stream * 53 + command_index * 31 + block * 19 + beat * 13 + lane * 5) % 127) - 63
                for lane in range(8)
            ]
            block_beats.append((queries, keys))
        blocks.append(block_beats)
    return blocks


def _values_for(stream: int, command_index: int, *, blocks_per_stream: int) -> list[list[list[list[int]]]]:
    return [
        [
            [
                [
                    ((stream * 67 + command_index * 37 + block * 23 + value_slice * 17 + row * 11 + lane * 7) % 255)
                    - 127
                    for lane in range(8)
                ]
                for row in range(8)
            ]
            for value_slice in range(16)
        ]
        for block in range(blocks_per_stream)
    ]


def _raw_scores(block: list[tuple[list[int], list[int]]], head_lane: int) -> list[int]:
    return [
        sum(queries[head_lane] * keys[token_lane] for queries, keys in block)
        for token_lane in range(8)
    ]


def _expected(workload: dict[str, object]) -> list[dict[str, object]]:
    heads = int(workload["heads"])
    command_count = int(workload["command_count"])
    blocks_per_stream = int(workload["blocks_per_stream"])
    head_dim = int(workload["head_dim"])
    head_bases = tuple(int(value) for value in workload["head_bases"])
    rows: list[dict[str, object]] = []
    for command_index, command in enumerate(
        _command_schedule(heads=heads, command_count=command_count, head_bases=head_bases)
    ):
        merged_per_head = []
        for head_lane in range(8):
            stream_partials = []
            for stream in range(2):
                blocks = _block_beats(stream, command_index, blocks_per_stream=blocks_per_stream, head_dim=head_dim)
                score_rows = [
                    list(
                        requantize_score_row(
                            _raw_scores(block, head_lane),
                            multiplier=int(command["multiplier"]),
                            shift=int(command["shift"]),
                        )
                    )
                    for block in blocks
                ]
                stream_partials.append(
                    partial_stream_from_blocks(
                        command_id=int(command["command_id"]),
                        head_id=int(command["head_base"]) + head_lane,
                        score_rows=score_rows,
                        value_blocks=_values_for(stream, command_index, blocks_per_stream=blocks_per_stream),
                    )
                )
            merged_per_head.append(merge_partial_streams(stream_partials[0], stream_partials[1]))
        for head_lane in range(8):
            for beat in merged_per_head[head_lane]:
                rows.append(
                    {
                        "command_id": beat.command_id,
                        "head_id": beat.head_id,
                        "slice": beat.slice_index,
                        "last": beat.last,
                        "global_max": beat.max_score,
                        "exp_sum": beat.exp_sum,
                        "value": list(beat.numerators),
                    }
                )
    return rows


def _testbench(
    *,
    top_name: str,
    workload: dict[str, object],
    output_ready_pattern: tuple[bool, ...],
    stress_interfaces: bool,
) -> str:
    heads = int(workload["heads"])
    command_count = int(workload["command_count"])
    blocks_per_stream = int(workload["blocks_per_stream"])
    head_dim = int(workload["head_dim"])
    head_bases = tuple(int(value) for value in workload["head_bases"])
    commands = _command_schedule(heads=heads, command_count=command_count, head_bases=head_bases)
    beats0 = []
    beats1 = []
    lasts = []
    for command_index in range(len(commands)):
        blocks0 = _block_beats(0, command_index, blocks_per_stream=blocks_per_stream, head_dim=head_dim)
        blocks1 = _block_beats(1, command_index, blocks_per_stream=blocks_per_stream, head_dim=head_dim)
        for block in range(blocks_per_stream):
            for beat in range(head_dim):
                queries0, keys0 = blocks0[block][beat]
                queries1, keys1 = blocks1[block][beat]
                beats0.append((queries0, keys0))
                beats1.append((queries1, keys1))
                lasts.append(1 if beat == head_dim - 1 else 0)

    cmd_init = "\n".join(
        f"    cmd_id_mem[{index}] = 16'h{int(command['command_id']):04x}; "
        f"cmd_head_base_mem[{index}] = 5'd{int(command['head_base'])}; "
        f"cmd_mult_mem[{index}] = 32'd{int(command['multiplier'])}; "
        f"cmd_shift_mem[{index}] = 6'd{int(command['shift'])};"
        for index, command in enumerate(commands)
    )
    beat_init = "\n".join(
        f"    query_mem[{index}] = 128'h{_pack(beats1[index][0], 8):016x}{_pack(beats0[index][0], 8):016x}; "
        f"key_mem[{index}] = 128'h{_pack(beats1[index][1], 8):016x}{_pack(beats0[index][1], 8):016x}; "
        f"last_mem[{index}] = 1'b{lasts[index]};"
        for index in range(len(beats0))
    )
    value_init = []
    for stream in range(2):
        for command_index in range(len(commands)):
            values = _values_for(stream, command_index, blocks_per_stream=blocks_per_stream)
            for block in range(blocks_per_stream):
                for value_slice in range(16):
                    flat = [lane for row in values[block][value_slice] for lane in row]
                    value_init.append(
                        f"    value_mem[{(((stream * len(commands)) + command_index) * blocks_per_stream + block) * 16 + value_slice}] = 512'h{_pack(flat, 8):0128x};"
                    )
    ready_init = "\n".join(
        f"    result_ready_mem[{index}] = 1'b{1 if value else 0};" for index, value in enumerate(output_ready_pattern)
    )
    total_beats = len(beats0)
    total_results = len(commands) * 8 * 16
    command_valid_expr = "1'b1" if not stress_interfaces else "(((cycle + issued_commands) % 5) != 2)"
    input_valid_expr = "1'b1" if not stress_interfaces else "(((cycle + input_index) % 7) != 3)"
    request_ready0_expr = "1'b1" if not stress_interfaces else "(((cycle + 1) % 4) != 1)"
    request_ready1_expr = "1'b1" if not stress_interfaces else "(((cycle + 3) % 6) != 2)"
    response_delay0_expr = "0" if not stress_interfaces else "((value_read_req_slice[3:0] + active_cmd0) % 3) + 1"
    response_delay1_expr = (
        "0"
        if not stress_interfaces
        else "((value_read_req_address[27:14] + value_read_req_slice[7:4] + active_cmd1) % 4) + 1"
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer HEADS = {heads};
  localparam integer COMMAND_COUNT = {len(commands)};
  localparam integer BLOCK_COUNT = {blocks_per_stream};
  localparam integer HEAD_DIM = {head_dim};
  localparam integer BEATS_PER_COMMAND = BLOCK_COUNT * HEAD_DIM;
  localparam integer TOTAL_BEATS = {total_beats};
  localparam integer TOTAL_RESULTS = {total_results};
  localparam integer READY_PATTERN_LEN = {len(output_ready_pattern)};

  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer issued_commands = 0;
  integer input_index = 0;
  integer active_cmd0 = 0;
  integer active_cmd1 = 0;
  integer result_seen = 0;
  reg finish_pending = 0;
  integer finish_drain_cycles = 0;

  reg [15:0] cmd_id_mem [0:COMMAND_COUNT-1];
  reg [4:0] cmd_head_base_mem [0:COMMAND_COUNT-1];
  reg [31:0] cmd_mult_mem [0:COMMAND_COUNT-1];
  reg [5:0] cmd_shift_mem [0:COMMAND_COUNT-1];
  reg [127:0] query_mem [0:TOTAL_BEATS-1];
  reg [127:0] key_mem [0:TOTAL_BEATS-1];
  reg last_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:(2*COMMAND_COUNT*BLOCK_COUNT*16)-1];
  reg result_ready_mem [0:READY_PATTERN_LEN-1];

  reg command_valid;
  wire command_ready;
  reg input_valid;
  wire input_ready;
  reg input_last;
  reg signed [127:0] input_query;
  reg signed [127:0] input_key;
  wire [1:0] value_read_req_valid;
  reg  [1:0] value_read_req_ready;
  wire [27:0] value_read_req_address;
  wire [7:0] value_read_req_slice;
  reg  [1:0] value_response_valid;
  wire [1:0] value_response_ready;
  reg  [27:0] value_response_address;
  reg  [7:0] value_response_slice;
  reg  [1023:0] value_response_matrix;
  wire result_valid;
  reg  result_ready;
  wire [15:0] result_command_id;
  wire [4:0] result_head_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire result_last;
  wire [327:0] result_value;
  wire [31:0] cycle_count;
  wire [31:0] command_accept_count;
  wire [31:0] command_completed_count;
  wire [63:0] stream_command_accept_count;
  wire [63:0] stream_completed_count;
  wire [1:0] stream_partial_valid;
  wire [1:0] stream_partial_ready;
  wire [1:0] stream_partial_last;
  wire [31:0] merge_completed_count;
  wire [31:0] result_stall_cycles;
  wire [1:0] stream_protocol_error;
  wire merge_protocol_error;
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
      .command_head_base(cmd_head_base_mem[issued_commands]),
      .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(cmd_mult_mem[issued_commands]),
      .command_score_shift(cmd_shift_mem[issued_commands]),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_query(input_query),
      .input_key(input_key),
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
      .cycle_count(cycle_count),
      .command_accept_count(command_accept_count),
      .command_completed_count(command_completed_count),
      .stream_command_accept_count(stream_command_accept_count),
      .stream_completed_count(stream_completed_count),
      .stream_partial_valid(stream_partial_valid),
      .stream_partial_ready(stream_partial_ready),
      .stream_partial_last(stream_partial_last),
      .merge_completed_count(merge_completed_count),
      .result_stall_cycles(result_stall_cycles),
      .stream_protocol_error(stream_protocol_error),
      .merge_protocol_error(merge_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && issued_commands < COMMAND_COUNT && {command_valid_expr};
    input_valid = rst_n && input_index < (issued_commands * BEATS_PER_COMMAND) && {input_valid_expr};
    input_query = input_index < TOTAL_BEATS ? query_mem[input_index] : 0;
    input_key = input_index < TOTAL_BEATS ? key_mem[input_index] : 0;
    input_last = input_index < TOTAL_BEATS ? last_mem[input_index] : 0;
    value_read_req_ready[0] = {request_ready0_expr};
    value_read_req_ready[1] = {request_ready1_expr};
    result_ready = result_ready_mem[cycle % READY_PATTERN_LEN];
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issued_commands <= 0;
      input_index <= 0;
      active_cmd0 <= 0;
      active_cmd1 <= 0;
      result_seen <= 0;
      pending0 <= 0;
      pending1 <= 0;
      pending_delay0 <= 0;
      pending_delay1 <= 0;
      finish_pending <= 0;
      finish_drain_cycles <= 0;
      value_response_valid <= 0;
      value_response_address <= 0;
      value_response_slice <= 0;
      value_response_matrix <= 0;
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        $display("COMMAND_ACCEPT idx=%0d cmd=%0d head_base=%0d cycle=%0d",
                 issued_commands, cmd_id_mem[issued_commands], cmd_head_base_mem[issued_commands], cycle);
        active_cmd0 <= issued_commands;
        active_cmd1 <= issued_commands;
        issued_commands <= issued_commands + 1;
      end
      if (input_valid && input_ready) begin
        input_index <= input_index + 1;
      end

      if (value_read_req_valid[0] && value_read_req_ready[0]) begin
        if (pending0 || value_response_valid[0]) $fatal(1, "stream0 multiple outstanding value requests");
        pending0 <= 1;
        pending_addr0 <= value_read_req_address[13:0];
        pending_slice0 <= value_read_req_slice[3:0];
        pending_delay0 <= {response_delay0_expr};
      end
      if (value_read_req_valid[1] && value_read_req_ready[1]) begin
        if (pending1 || value_response_valid[1]) $fatal(1, "stream1 multiple outstanding value requests");
        pending1 <= 1;
        pending_addr1 <= value_read_req_address[27:14];
        pending_slice1 <= value_read_req_slice[7:4];
        pending_delay1 <= {response_delay1_expr};
      end

      if (pending0) begin
        if (pending_delay0 == 0) begin
          pending0 <= 0;
          value_response_valid[0] <= 1;
          value_response_address[13:0] <= pending_addr0;
          value_response_slice[3:0] <= pending_slice0;
          value_response_matrix[511:0] <= value_mem[((active_cmd0 * BLOCK_COUNT) + pending_addr0) * 16 + pending_slice0];
        end else begin
          pending_delay0 <= pending_delay0 - 1;
        end
      end
      if (pending1) begin
        if (pending_delay1 == 0) begin
          pending1 <= 0;
          value_response_valid[1] <= 1;
          value_response_address[27:14] <= pending_addr1;
          value_response_slice[7:4] <= pending_slice1;
          value_response_matrix[1023:512] <= value_mem[(((COMMAND_COUNT + active_cmd1) * BLOCK_COUNT) + pending_addr1) * 16 + pending_slice1];
        end else begin
          pending_delay1 <= pending_delay1 - 1;
        end
      end
      if (value_response_valid[0] && value_response_ready[0]) value_response_valid[0] <= 0;
      if (value_response_valid[1] && value_response_ready[1]) value_response_valid[1] <= 0;

      if (result_valid && result_ready) begin
        $display("RESULT cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
                 result_command_id, result_head_id, result_slice, result_last, $signed(result_global_max),
                 result_exp_sum, result_value, cycle);
        result_seen <= result_seen + 1;
        if (result_seen + 1 == TOTAL_RESULTS) begin
          finish_pending <= 1'b1;
          finish_drain_cycles <= cycle + 1;
        end
      end
      if (finish_pending) begin
        $display("SUMMARY outputs=%0d drain=%0d protocol_error=%0d command_accept=%0d command_complete=%0d stream0_accept=%0d stream1_accept=%0d stream0_complete=%0d stream1_complete=%0d merge_complete=%0d result_stall=%0d stream0_error=%0d stream1_error=%0d merge_error=%0d",
                 result_seen, finish_drain_cycles, protocol_error, command_accept_count, command_completed_count,
                 stream_command_accept_count[31:0], stream_command_accept_count[63:32],
                 stream_completed_count[31:0], stream_completed_count[63:32],
                 merge_completed_count, result_stall_cycles, stream_protocol_error[0], stream_protocol_error[1], merge_protocol_error);
        #1 $finish;
      end
      if (cycle > 60000) $fatal(1, "timeout");
    end
  end

  initial begin
{cmd_init}
{beat_init}
{chr(10).join(value_init)}
{ready_init}
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


def _unpack_result_value(word: int) -> tuple[int, ...]:
    values = []
    mask = (1 << 41) - 1
    for lane in range(8):
        raw = (word >> (lane * 41)) & mask
        if raw & (1 << 40):
            raw -= 1 << 41
        values.append(raw)
    return tuple(values)


def _run_case(
    config: JsonDict,
    *,
    heads: int | None,
    command_count: int | None,
    blocks_per_stream: int | None,
    head_dim: int | None,
    head_bases: tuple[int, ...] | None,
    output_ready_pattern: tuple[bool, ...],
    stress_interfaces: bool,
) -> JsonDict:
    workload = _resolve_workload(
        config,
        heads=heads,
        command_count=command_count,
        blocks_per_stream=blocks_per_stream,
        head_dim=head_dim,
        head_bases=head_bases,
    )
    expected = _expected(workload)
    resolved_heads = int(workload["heads"])
    with tempfile.TemporaryDirectory(prefix=f"score32_exact_partial_dual_stream_h{heads}_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        run_config = json.loads(json.dumps(config))
        probe_defaults = run_config.setdefault("probe_defaults", {})
        probe_defaults["heads"] = int(workload["heads"])
        probe_defaults["command_count"] = int(workload["command_count"])
        probe_defaults["blocks_per_stream"] = int(workload["blocks_per_stream"])
        probe_defaults["head_dim"] = int(workload["head_dim"])
        probe_defaults["head_bases"] = list(int(value) for value in workload["head_bases"])
        generate_tree(run_config, temp_dir / "rtl")
        tb_path = temp_dir / "tb.sv"
        fakeram_path = temp_dir / "fakeram45_2048x39.sv"
        tb_path.write_text(
            _testbench(
                top_name=str(run_config["top_name"]),
                workload=workload,
                output_ready_pattern=output_ready_pattern,
                stress_interfaces=stress_interfaces,
            ),
            encoding="utf-8",
        )
        fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")
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
                str(fakeram_path),
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
    observed: list[dict[str, object]] = []
    summary: dict[str, int] | None = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _COMMAND_RE.fullmatch(stripped):
            command_accepts.append(
                {
                    "index": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "head_base": int(match.group(3)),
                    "cycle": int(match.group(4)),
                }
            )
        elif match := _RESULT_RE.fullmatch(stripped):
            observed.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "value": list(_unpack_result_value(int(match.group(7), 16))),
                    "cycle": int(match.group(8)),
                }
            )
        elif match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "drain_cycles": int(match.group(2)),
                "protocol_error": int(match.group(3)),
                "command_accept_count": int(match.group(4)),
                "command_complete_count": int(match.group(5)),
                "stream0_accept_count": int(match.group(6)),
                "stream1_accept_count": int(match.group(7)),
                "stream0_complete_count": int(match.group(8)),
                "stream1_complete_count": int(match.group(9)),
                "merge_complete_count": int(match.group(10)),
                "result_stall_cycles": int(match.group(11)),
                "stream0_protocol_error": int(match.group(12)),
                "stream1_protocol_error": int(match.group(13)),
                "merge_protocol_error": int(match.group(14)),
            }
    if summary is None:
        raise RuntimeError(f"missing SUMMARY line in simulation output:\n{run.stdout}")

    observed_rows = [
        {
            "command_id": row["command_id"],
            "head_id": row["head_id"],
            "slice": row["slice"],
            "last": row["last"],
            "global_max": row["global_max"],
            "exp_sum": row["exp_sum"],
            "value": row["value"],
        }
        for row in observed
    ]
    return {
        "heads": resolved_heads,
        "commands": int(workload["command_count"]),
        "blocks_per_stream": int(workload["blocks_per_stream"]),
        "head_dim": int(workload["head_dim"]),
        "head_bases": list(int(value) for value in workload["head_bases"]),
        "command_accepts": command_accepts,
        "outputs": len(observed_rows),
        "observed_rows": observed_rows,
        "expected_rows": expected,
        "summary": summary,
        "interface_mode": "stress" if stress_interfaces else "ideal",
        "passed": observed_rows == expected
        and summary["protocol_error"] == 0
        and summary["stream0_protocol_error"] == 0
        and summary["stream1_protocol_error"] == 0
        and summary["merge_protocol_error"] == 0,
    }


def build_report(
    config: JsonDict | None = None,
    *,
    heads: int | None = None,
    command_count: int | None = None,
    blocks_per_stream: int | None = None,
    head_dim: int | None = None,
    head_bases: tuple[int, ...] | None = None,
    output_ready_pattern: tuple[bool, ...] | None = None,
    stress_interfaces: bool | None = None,
) -> JsonDict:
    base_config = json.loads(json.dumps(config or _default_config()))
    configured_mode = base_config.get("probe_defaults", {}).get("interface_mode", "stress")
    use_stress = bool(stress_interfaces if stress_interfaces is not None else configured_mode != "ideal")
    ready_pattern = output_ready_pattern or (
        (True, False, True, True, False, True, False, True, True, True, False, True)
        if use_stress
        else (True,)
    )
    result = _run_case(
        base_config,
        heads=heads,
        command_count=command_count,
        blocks_per_stream=blocks_per_stream,
        head_dim=head_dim,
        head_bases=head_bases,
        output_ready_pattern=ready_pattern,
        stress_interfaces=use_stress,
    )
    reference_cycles = base_config.get("probe_defaults", {}).get("llama_wave_reference_cycles")
    reference_delta = None
    if isinstance(reference_cycles, int):
        reference_delta = int(result["summary"]["drain_cycles"]) - reference_cycles
    return {
        "decision": "score32_exact_partial_dual_stream_gqa8_pass" if result["passed"] else "score32_exact_partial_dual_stream_gqa8_fail",
        "passed": bool(result["passed"]),
        "top_name": str(base_config["top_name"]),
        "heads": int(result["heads"]),
        "commands": result["commands"],
        "blocks_per_stream": int(result["blocks_per_stream"]),
        "head_dim": int(result["head_dim"]),
        "head_bases": result["head_bases"],
        "outputs": result["outputs"],
        "expected_outputs": len(result["expected_rows"]),
        "command_accept_cycles": result["command_accepts"],
        "integrated_drain_cycles": int(result["summary"]["drain_cycles"]),
        "command_accept_count": int(result["summary"]["command_accept_count"]),
        "command_complete_count": int(result["summary"]["command_complete_count"]),
        "stream_command_accept_count": [
            int(result["summary"]["stream0_accept_count"]),
            int(result["summary"]["stream1_accept_count"]),
        ],
        "stream_complete_count": [
            int(result["summary"]["stream0_complete_count"]),
            int(result["summary"]["stream1_complete_count"]),
        ],
        "merge_complete_count": int(result["summary"]["merge_complete_count"]),
        "result_stall_cycles": int(result["summary"]["result_stall_cycles"]),
        "interface_mode": result["interface_mode"],
        "llama_wave_reference_cycles": reference_cycles,
        "llama_wave_drain_delta_vs_986": reference_delta,
        "stream_protocol_error": [
            bool(result["summary"]["stream0_protocol_error"]),
            bool(result["summary"]["stream1_protocol_error"]),
        ],
        "merge_protocol_error": bool(result["summary"]["merge_protocol_error"]),
        "protocol_error": bool(result["summary"]["protocol_error"]),
        "observed_rows": result["observed_rows"],
        "expected_rows": result["expected_rows"],
        "service_model": exact_partial_dual_stream_gqa8_producer_service_manifest(
            heads=int(result["heads"]),
            max_blocks=int(base_config["attention_score32_exact_partial_gqa8_dual_stream_producer"]["max_blocks"]),
            command_count=int(result["commands"]),
            blocks_per_stream=int(result["blocks_per_stream"]),
            head_dim=int(result["head_dim"]),
            head_bases=tuple(int(value) for value in result["head_bases"]),
            llama_wave_reference_cycles=reference_cycles if isinstance(reference_cycles, int) else None,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--heads", type=int, default=None)
    parser.add_argument("--command-count", type=int, default=None)
    parser.add_argument("--blocks-per-stream", type=int, default=None)
    parser.add_argument("--head-dim", type=int, default=None)
    parser.add_argument("--head-bases", type=str, default=None)
    parser.add_argument("--result-ready-pattern", type=str, default=None)
    parser.add_argument("--ideal-interfaces", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = _default_config()
    if args.config is not None:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    pattern = None
    if args.result_ready_pattern:
        pattern = tuple(token.strip() in {"1", "true", "True"} for token in args.result_ready_pattern.split(","))
        if not pattern:
            raise SystemExit("result-ready-pattern must not be empty")
    head_bases = None
    if args.head_bases:
        head_bases = tuple(int(token.strip()) for token in args.head_bases.split(",") if token.strip())
        if not head_bases:
            raise SystemExit("head-bases must not be empty")
    report = build_report(
        config=config,
        heads=args.heads,
        command_count=args.command_count,
        blocks_per_stream=args.blocks_per_stream,
        head_dim=args.head_dim,
        head_bases=head_bases,
        output_ready_pattern=pattern,
        stress_interfaces=False if args.ideal_interfaces else None,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "heads": report["heads"],
                    "commands": report["commands"],
                    "outputs": report["outputs"],
                    "integrated_drain_cycles": report["integrated_drain_cycles"],
                    "protocol_error": report["protocol_error"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
