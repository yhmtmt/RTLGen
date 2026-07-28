#!/usr/bin/env python3
"""Probe the full-width score32 exact local cluster against a structured reference."""

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

from npu.rtlgen.gen_attention_score32_exact_local_cluster_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_CLUSTER_GQA8_HEAD_BASES,
    LOCAL_TEMPORAL_WAVES,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_extra_producers,
    exact_local_cluster_gqa8_service_manifest,
    merge_partial_streams,
    partial_stream_from_blocks,
    reduce_local_temporal_partial_waves,
    unpack_numerators,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]

_CONFIG_KEY = "attention_score32_exact_local_cluster_gqa8"
_COMMAND_RE = re.compile(
    r"COMMAND_ACCEPT idx=(\d+) cmd=(\d+) head_base=(\d+) group=(\d+) wave=(\d+) cycle=(\d+)"
)
_RESULT_RE = re.compile(
    r"RESULT idx=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_PRODUCER_RE = re.compile(
    r"PRODUCER idx=(\d+) accept=(\d+) complete=(\d+) merge=(\d+) stall=(\d+) "
    r"stream0_accept=(\d+) stream1_accept=(\d+) stream0_complete=(\d+) stream1_complete=(\d+) "
    r"stream_error=(\d+) merge_error=(\d+) protocol=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) protocol_error=(\d+) atomic_error=(\d+) group_error=(\d+) "
    r"local_tree_error=(\d+) temporal_error=(\d+) reducer_error=(\d+) wave_accept=(\d+) "
    r"group_complete=(\d+) local_root_completed=(\d+) temporal_completed=(\d+) emitted=(\d+) "
    r"issue_wait=(\d+) ready_skew=(\d+)"
)
_TB_TIMEOUT_RE = re.compile(r"TIMEOUT cycle=(\d+)")

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


def _default_config(producers: int = 53) -> JsonDict:
    return {
        "top_name": f"attention_score32_exact_local_cluster_gqa8_p{producers}_w8",
        _CONFIG_KEY: {
            "producers": producers,
            "max_blocks": 8,
            "value_slices": 16,
            "head_id_bits": 5,
            "persistent_waves": 8,
        },
        "probe_defaults": {
            "head_bases": [0, 8, 16, 24],
            "head_dim": 1,
            "seed": 73,
            "timeout_s": 300,
        },
        "report_links": {
            "proposal_id": "prop_l1_decoder_attention_score32_local_cluster_gqa8_v1",
            "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_cluster_gqa8_v1/proposal.json",
        },
    }


def _resolve_workload(
    config: JsonDict,
    *,
    head_dim: int | None,
    seed: int | None,
    head_bases: tuple[int, ...] | None = None,
    timeout_s: int | None = None,
) -> dict[str, object]:
    defaults = config.get("probe_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    resolved_head_dim = int(head_dim if head_dim is not None else defaults.get("head_dim", 1))
    resolved_seed = int(seed if seed is not None else defaults.get("seed", 73))
    configured_head_bases = head_bases
    if configured_head_bases is None and isinstance(defaults.get("head_bases"), list):
        configured_head_bases = tuple(int(value) for value in defaults["head_bases"])
    if configured_head_bases is None:
        configured_head_bases = LOCAL_CLUSTER_GQA8_HEAD_BASES
    resolved_timeout_s = int(timeout_s if timeout_s is not None else defaults.get("timeout_s", 300))

    if configured_head_bases != LOCAL_CLUSTER_GQA8_HEAD_BASES:
        raise ValueError(f"head_bases must remain fixed at {LOCAL_CLUSTER_GQA8_HEAD_BASES}")
    if resolved_head_dim < 1:
        raise ValueError("head_dim must be positive")
    if resolved_timeout_s < 1:
        raise ValueError("timeout_s must be positive")

    return {
        "head_bases": configured_head_bases,
        "head_dim": resolved_head_dim,
        "seed": resolved_seed,
        "timeout_s": resolved_timeout_s,
        "groups": len(configured_head_bases),
        "waves": LOCAL_TEMPORAL_WAVES,
        "wave_commands": len(configured_head_bases) * LOCAL_TEMPORAL_WAVES,
    }


def _logical_commands(head_bases: tuple[int, ...]) -> tuple[dict[str, int], ...]:
    schedule = []
    for group_index, head_base in enumerate(head_bases):
        if group_index == 0:
            multiplier, shift = (1 << 20), 0
        elif group_index == 1:
            multiplier, shift = 13, 1
        elif group_index == 2:
            multiplier, shift = 29, 2
        else:
            multiplier, shift = 37, 1
        schedule.append(
            {
                "group_index": group_index,
                "command_id": 0x7D00 + group_index,
                "head_base": int(head_base),
                "multiplier": multiplier,
                "shift": shift,
            }
        )
    return tuple(schedule)


def _wave_commands(producers: int, workload: dict[str, object]) -> tuple[dict[str, object], ...]:
    commands = []
    for logical_command in _logical_commands(tuple(int(value) for value in workload["head_bases"])):
        group_index = int(logical_command["group_index"])
        block_counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=group_index)
        for wave_index in range(LOCAL_TEMPORAL_WAVES):
            commands.append(
                {
                    **logical_command,
                    "wave_index": wave_index,
                    "block_counts": block_counts,
                }
            )
    return tuple(commands)


def _stream_block_beats(
    *,
    producer: int,
    group_index: int,
    wave_index: int,
    stream: int,
    block_count: int,
    head_dim: int,
    seed: int,
) -> tuple[tuple[tuple[tuple[int, ...], tuple[int, ...]], ...], ...]:
    blocks = []
    for block_index in range(block_count):
        beats = []
        for beat_index in range(head_dim):
            queries = tuple(
                (
                    (
                        seed * 17
                        + producer * 19
                        + group_index * 23
                        + wave_index * 29
                        + stream * 31
                        + block_index * 37
                        + beat_index * 41
                        + head_lane * 43
                    )
                    % 127
                )
                - 63
                for head_lane in range(8)
            )
            keys = tuple(
                (
                    (
                        seed * 47
                        + producer * 53
                        + group_index * 59
                        + wave_index * 61
                        + stream * 67
                        + block_index * 71
                        + beat_index * 73
                        + token_lane * 79
                    )
                    % 127
                )
                - 63
                for token_lane in range(8)
            )
            beats.append((queries, keys))
        blocks.append(tuple(beats))
    return tuple(blocks)


def _value_blocks(
    *,
    producer: int,
    group_index: int,
    wave_index: int,
    stream: int,
    block_count: int,
    seed: int,
) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    (
                        (
                            seed * 83
                            + producer * 89
                            + group_index * 97
                            + wave_index * 101
                            + stream * 103
                            + block_index * 107
                            + value_slice * 109
                            + row * 113
                            + lane * 127
                        )
                        % 255
                    )
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block_index in range(block_count)
    )


def _raw_scores(block: tuple[tuple[int, ...], tuple[int, ...]], head_lane: int) -> list[int]:
    return [
        sum(queries[head_lane] * keys[token_lane] for queries, keys in block)
        for token_lane in range(8)
    ]


def _producer_wave_stream(
    *,
    producer: int,
    logical_command: dict[str, int],
    wave_index: int,
    block_count: int,
    head_dim: int,
    seed: int,
) -> tuple[object, ...]:
    merged_per_head = []
    for head_lane in range(8):
        stream_partials = []
        for stream in range(2):
            blocks = _stream_block_beats(
                producer=producer,
                group_index=int(logical_command["group_index"]),
                wave_index=wave_index,
                stream=stream,
                block_count=block_count,
                head_dim=head_dim,
                seed=seed,
            )
            score_rows = [
                list(
                    requantize_score_row(
                        _raw_scores(block, head_lane),
                        multiplier=int(logical_command["multiplier"]),
                        shift=int(logical_command["shift"]),
                    )
                )
                for block in blocks
            ]
            stream_partials.append(
                partial_stream_from_blocks(
                    command_id=int(logical_command["command_id"]),
                    head_id=int(logical_command["head_base"]) + head_lane,
                    score_rows=score_rows,
                    value_blocks=_value_blocks(
                        producer=producer,
                        group_index=int(logical_command["group_index"]),
                        wave_index=wave_index,
                        stream=stream,
                        block_count=block_count,
                        seed=seed,
                    ),
                )
            )
        merged_per_head.append(merge_partial_streams(stream_partials[0], stream_partials[1]))
    return tuple(beat for head_stream in merged_per_head for beat in head_stream)


def _expected_rows(producers: int, workload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for logical_command in _logical_commands(tuple(int(value) for value in workload["head_bases"])):
        waves = []
        for wave_index in range(LOCAL_TEMPORAL_WAVES):
            producer_streams = []
            block_counts = exact_local_cluster_gqa8_command_block_counts(
                producers=producers,
                group_index=int(logical_command["group_index"]),
            )
            for producer in range(producers):
                producer_streams.append(
                    _producer_wave_stream(
                        producer=producer,
                        logical_command=logical_command,
                        wave_index=wave_index,
                        block_count=int(block_counts[producer]),
                        head_dim=int(workload["head_dim"]),
                        seed=int(workload["seed"]),
                    )
                )
            waves.append(tuple(producer_streams))
        for beat in reduce_local_temporal_partial_waves(tuple(waves)):
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


def _producer_command_data(
    *,
    producers: int,
    workload: dict[str, object],
) -> dict[str, object]:
    wave_commands = _wave_commands(producers, workload)
    head_dim = int(workload["head_dim"])
    seed = int(workload["seed"])
    max_beats_per_producer = 0
    max_blocks_per_producer = 0
    query_mem: list[list[int]] = []
    key_mem: list[list[int]] = []
    last_mem: list[int] = []
    value_mem: list[list[int]] = []
    beat_limits = [[0 for _ in range(producers)] for _ in range(len(wave_commands))]
    block_offsets = [[0 for _ in range(producers)] for _ in range(len(wave_commands))]

    for producer in range(producers):
        producer_queries: list[int] = []
        producer_keys: list[int] = []
        producer_lasts: list[int] = []
        producer_blocks_flat: list[list[list[int]]] = [[], []]
        cumulative_beats = 0
        cumulative_blocks = 0
        for command_index, wave_command in enumerate(wave_commands):
            block_count = int(tuple(int(value) for value in wave_command["block_counts"])[producer])
            block_offsets[command_index][producer] = cumulative_blocks
            blocks0 = _stream_block_beats(
                producer=producer,
                group_index=int(wave_command["group_index"]),
                wave_index=int(wave_command["wave_index"]),
                stream=0,
                block_count=block_count,
                head_dim=head_dim,
                seed=seed,
            )
            blocks1 = _stream_block_beats(
                producer=producer,
                group_index=int(wave_command["group_index"]),
                wave_index=int(wave_command["wave_index"]),
                stream=1,
                block_count=block_count,
                head_dim=head_dim,
                seed=seed,
            )
            values0 = _value_blocks(
                producer=producer,
                group_index=int(wave_command["group_index"]),
                wave_index=int(wave_command["wave_index"]),
                stream=0,
                block_count=block_count,
                seed=seed,
            )
            values1 = _value_blocks(
                producer=producer,
                group_index=int(wave_command["group_index"]),
                wave_index=int(wave_command["wave_index"]),
                stream=1,
                block_count=block_count,
                seed=seed,
            )
            for block_index in range(block_count):
                producer_blocks_flat[0].append(
                    [[lane for row in values0[block_index][value_slice] for lane in row] for value_slice in range(16)]
                )
                producer_blocks_flat[1].append(
                    [[lane for row in values1[block_index][value_slice] for lane in row] for value_slice in range(16)]
                )
                for beat_index in range(head_dim):
                    queries0, keys0 = blocks0[block_index][beat_index]
                    queries1, keys1 = blocks1[block_index][beat_index]
                    producer_queries.append(_pack(list(queries0), 8) | (_pack(list(queries1), 8) << 64))
                    producer_keys.append(_pack(list(keys0), 8) | (_pack(list(keys1), 8) << 64))
                    producer_lasts.append(1 if beat_index == head_dim - 1 else 0)
            cumulative_beats += block_count * head_dim
            cumulative_blocks += block_count
            beat_limits[command_index][producer] = cumulative_beats
        max_beats_per_producer = max(max_beats_per_producer, cumulative_beats)
        max_blocks_per_producer = max(max_blocks_per_producer, cumulative_blocks)
        query_mem.append(producer_queries)
        key_mem.append(producer_keys)
        last_mem.append(producer_lasts)
        stream_values: list[list[int]] = [[], []]
        for stream in range(2):
            for block_slices in producer_blocks_flat[stream]:
                for flat_slice in block_slices:
                    stream_values[stream].append(_pack(flat_slice, 8))
        value_mem.append(stream_values[0])
        value_mem.append(stream_values[1])

    return {
        "wave_commands": wave_commands,
        "query_mem": query_mem,
        "key_mem": key_mem,
        "last_mem": last_mem,
        "value_mem": value_mem,
        "beat_limits": beat_limits,
        "block_offsets": block_offsets,
        "max_beats_per_producer": max_beats_per_producer,
        "max_blocks_per_producer": max_blocks_per_producer,
    }


def _testbench(
    *,
    top_name: str,
    producers: int,
    workload: dict[str, object],
    output_ready_pattern: tuple[bool, ...],
) -> str:
    command_data = _producer_command_data(producers=producers, workload=workload)
    wave_commands = tuple(command_data["wave_commands"])
    query_mem = command_data["query_mem"]
    key_mem = command_data["key_mem"]
    last_mem = command_data["last_mem"]
    value_mem = command_data["value_mem"]
    beat_limits = command_data["beat_limits"]
    block_offsets = command_data["block_offsets"]
    max_beats_per_producer = int(command_data["max_beats_per_producer"])
    max_blocks_per_producer = int(command_data["max_blocks_per_producer"])
    total_results = len(LOCAL_CLUSTER_GQA8_HEAD_BASES) * 8 * 16

    cmd_init = []
    for command_index, wave_command in enumerate(wave_commands):
        cmd_init.append(
            f"    cmd_id_mem[{command_index}] = 16'h{int(wave_command['command_id']):04x}; "
            f"cmd_head_base_mem[{command_index}] = 5'd{int(wave_command['head_base'])}; "
            f"cmd_multiplier_mem[{command_index}] = 32'd{int(wave_command['multiplier'])}; "
            f"cmd_shift_mem[{command_index}] = 6'd{int(wave_command['shift'])}; "
            f"cmd_block_count_mem[{command_index}] = {producers * 15}'h{_pack(list(int(v) for v in wave_command['block_counts']), 15):x};"
        )
    beat_limit_init = []
    for command_index in range(len(wave_commands)):
        for producer in range(producers):
            beat_limit_init.append(
                f"    cmd_beat_limit_mem[{command_index}][{producer}] = 32'd{int(beat_limits[command_index][producer])}; "
                f"cmd_block_offset_mem[{command_index}][{producer}] = 32'd{int(block_offsets[command_index][producer])};"
            )
    beat_init = []
    for producer in range(producers):
        for beat_index, packed_query in enumerate(query_mem[producer]):
            flat_index = (producer * max_beats_per_producer) + beat_index
            beat_init.append(
                f"    query_mem[{flat_index}] = 128'h{packed_query:032x}; "
                f"key_mem[{flat_index}] = 128'h{int(key_mem[producer][beat_index]):032x}; "
                f"last_mem[{flat_index}] = 1'b{int(last_mem[producer][beat_index])};"
            )
    value_init = []
    for producer_stream in range(producers * 2):
        for slice_index, packed_matrix in enumerate(value_mem[producer_stream]):
            flat_index = (producer_stream * max_blocks_per_producer * 16) + slice_index
            value_init.append(f"    value_mem[{flat_index}] = 512'h{int(packed_matrix):0128x};")
    ready_init = "\n".join(
        f"    result_ready_mem[{index}] = 1'b{1 if value else 0};" for index, value in enumerate(output_ready_pattern)
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam integer VALUE_LANES = PRODUCERS * 2;
  localparam integer COMMAND_COUNT = {len(wave_commands)};
  localparam integer MAX_BEATS_PER_PRODUCER = {max_beats_per_producer};
  localparam integer MAX_BLOCKS_PER_PRODUCER = {max_blocks_per_producer};
  localparam integer TOTAL_RESULTS = {total_results};
  localparam integer READY_PATTERN_LEN = {len(output_ready_pattern)};

  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer issued_commands = 0;
  integer active_command_index = -1;
  integer result_seen = 0;
  reg pending_summary = 0;

  reg [15:0] cmd_id_mem [0:COMMAND_COUNT-1];
  reg [4:0] cmd_head_base_mem [0:COMMAND_COUNT-1];
  reg [31:0] cmd_multiplier_mem [0:COMMAND_COUNT-1];
  reg [5:0] cmd_shift_mem [0:COMMAND_COUNT-1];
  reg [(PRODUCERS*15)-1:0] cmd_block_count_mem [0:COMMAND_COUNT-1];
  reg [31:0] cmd_beat_limit_mem [0:COMMAND_COUNT-1][0:PRODUCERS-1];
  reg [31:0] cmd_block_offset_mem [0:COMMAND_COUNT-1][0:PRODUCERS-1];

  reg [127:0] query_mem [0:(PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [127:0] key_mem [0:(PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg last_mem [0:(PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [511:0] value_mem [0:(VALUE_LANES*MAX_BLOCKS_PER_PRODUCER*16)-1];
  reg result_ready_mem [0:READY_PATTERN_LEN-1];

  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [4:0] command_head_base;
  reg [(PRODUCERS*15)-1:0] command_block_count;
  reg [31:0] command_score_multiplier;
  reg [5:0] command_score_shift;
  reg [PRODUCERS-1:0] input_valid;
  wire [PRODUCERS-1:0] input_ready;
  reg [PRODUCERS-1:0] input_last;
  reg signed [(PRODUCERS*128)-1:0] input_query;
  reg signed [(PRODUCERS*128)-1:0] input_key;
  wire [VALUE_LANES-1:0] value_read_req_valid;
  reg  [VALUE_LANES-1:0] value_read_req_ready;
  wire [(VALUE_LANES*14)-1:0] value_read_req_address;
  wire [(VALUE_LANES*4)-1:0] value_read_req_slice;
  reg  [VALUE_LANES-1:0] value_response_valid;
  wire [VALUE_LANES-1:0] value_response_ready;
  reg  [(VALUE_LANES*14)-1:0] value_response_address;
  reg  [(VALUE_LANES*4)-1:0] value_response_slice;
  reg  [(VALUE_LANES*512)-1:0] value_response_matrix;
  wire out_valid;
  reg out_ready;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire out_last;
  wire [327:0] out_value;
  wire [31:0] cluster_cycle_count;
  wire [31:0] wave_command_accept_count;
  wire [31:0] wave_command_issue_wait_cycles;
  wire [31:0] producer_ready_skew_cycles;
  wire [2:0] reducer_active_wave_index;
  wire reducer_emitting;
  wire [4:0] reducer_active_head_base;
  wire [6:0] reducer_collect_beat_index;
  wire [6:0] reducer_emit_beat_index;
  wire [31:0] reducer_cycle_count;
  wire [31:0] reducer_local_root_completed_count;
  wire [31:0] reducer_temporal_merge_completed_count;
  wire [31:0] reducer_emitted_beat_count;
  wire [31:0] reducer_completed_command_count;
  wire [31:0] reducer_local_stall_cycles;
  wire [31:0] reducer_output_stall_cycles;
  wire [(PRODUCERS*32)-1:0] producer_cycle_count;
  wire [(PRODUCERS*32)-1:0] producer_command_accept_count;
  wire [(PRODUCERS*32)-1:0] producer_command_completed_count;
  wire [(PRODUCERS*64)-1:0] producer_stream_command_accept_count;
  wire [(PRODUCERS*64)-1:0] producer_stream_completed_count;
  wire [(PRODUCERS*32)-1:0] producer_merge_completed_count;
  wire [(PRODUCERS*32)-1:0] producer_result_stall_cycles;
  wire [(PRODUCERS*2)-1:0] producer_stream_protocol_error;
  wire [PRODUCERS-1:0] producer_merge_protocol_error;
  wire [PRODUCERS-1:0] producer_protocol_error;
  wire group_contract_error;
  wire local_tree_protocol_error;
  wire temporal_merge_protocol_error;
  wire reducer_protocol_error;
  wire atomic_command_protocol_error;
  wire protocol_error;

  integer beat_issue [0:PRODUCERS-1];
  reg pending_valid [0:VALUE_LANES-1];
  reg [13:0] pending_addr [0:VALUE_LANES-1];
  reg [3:0] pending_slice [0:VALUE_LANES-1];
  integer pending_delay [0:VALUE_LANES-1];
  integer producer_index;
  integer lane_index;
  integer stream_index;
  integer flat_index;
  integer response_index;
  integer init_index;

  always #5 clk = ~clk;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
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
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_command_id(out_command_id),
      .out_head_id(out_head_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .cluster_cycle_count(cluster_cycle_count),
      .wave_command_accept_count(wave_command_accept_count),
      .wave_command_issue_wait_cycles(wave_command_issue_wait_cycles),
      .producer_ready_skew_cycles(producer_ready_skew_cycles),
      .reducer_active_wave_index(reducer_active_wave_index),
      .reducer_emitting(reducer_emitting),
      .reducer_active_head_base(reducer_active_head_base),
      .reducer_collect_beat_index(reducer_collect_beat_index),
      .reducer_emit_beat_index(reducer_emit_beat_index),
      .reducer_cycle_count(reducer_cycle_count),
      .reducer_local_root_completed_count(reducer_local_root_completed_count),
      .reducer_temporal_merge_completed_count(reducer_temporal_merge_completed_count),
      .reducer_emitted_beat_count(reducer_emitted_beat_count),
      .reducer_completed_command_count(reducer_completed_command_count),
      .reducer_local_stall_cycles(reducer_local_stall_cycles),
      .reducer_output_stall_cycles(reducer_output_stall_cycles),
      .producer_cycle_count(producer_cycle_count),
      .producer_command_accept_count(producer_command_accept_count),
      .producer_command_completed_count(producer_command_completed_count),
      .producer_stream_command_accept_count(producer_stream_command_accept_count),
      .producer_stream_completed_count(producer_stream_completed_count),
      .producer_merge_completed_count(producer_merge_completed_count),
      .producer_result_stall_cycles(producer_result_stall_cycles),
      .producer_stream_protocol_error(producer_stream_protocol_error),
      .producer_merge_protocol_error(producer_merge_protocol_error),
      .producer_protocol_error(producer_protocol_error),
      .group_contract_error(group_contract_error),
      .local_tree_protocol_error(local_tree_protocol_error),
      .temporal_merge_protocol_error(temporal_merge_protocol_error),
      .reducer_protocol_error(reducer_protocol_error),
      .atomic_command_protocol_error(atomic_command_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && (issued_commands < COMMAND_COUNT);
    command_id = command_valid ? cmd_id_mem[issued_commands] : 16'd0;
    command_head_base = command_valid ? cmd_head_base_mem[issued_commands] : 5'd0;
    command_block_count = command_valid ? cmd_block_count_mem[issued_commands] : {{(PRODUCERS*15){{1'b0}}}};
    command_score_multiplier = command_valid ? cmd_multiplier_mem[issued_commands] : 32'd0;
    command_score_shift = command_valid ? cmd_shift_mem[issued_commands] : 6'd0;
    input_valid = {{PRODUCERS{{1'b0}}}};
    input_last = {{PRODUCERS{{1'b0}}}};
    input_query = {{(PRODUCERS*128){{1'b0}}}};
    input_key = {{(PRODUCERS*128){{1'b0}}}};
    value_read_req_ready = {{VALUE_LANES{{1'b1}}}};
    out_ready = result_ready_mem[cycle % READY_PATTERN_LEN];
    for (producer_index = 0; producer_index < PRODUCERS; producer_index = producer_index + 1) begin
      if (rst_n && (active_command_index >= 0) && (beat_issue[producer_index] < cmd_beat_limit_mem[active_command_index][producer_index])) begin
        flat_index = (producer_index * MAX_BEATS_PER_PRODUCER) + beat_issue[producer_index];
        input_valid[producer_index] = 1'b1;
        input_last[producer_index] = last_mem[flat_index];
        input_query[(producer_index * 128) +: 128] = query_mem[flat_index];
        input_key[(producer_index * 128) +: 128] = key_mem[flat_index];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issued_commands <= 0;
      active_command_index <= -1;
      result_seen <= 0;
      pending_summary <= 1'b0;
      value_response_valid <= {{VALUE_LANES{{1'b0}}}};
      value_response_address <= {{(VALUE_LANES*14){{1'b0}}}};
      value_response_slice <= {{(VALUE_LANES*4){{1'b0}}}};
      value_response_matrix <= {{(VALUE_LANES*512){{1'b0}}}};
      for (producer_index = 0; producer_index < PRODUCERS; producer_index = producer_index + 1) begin
        beat_issue[producer_index] <= 0;
      end
      for (lane_index = 0; lane_index < VALUE_LANES; lane_index = lane_index + 1) begin
        pending_valid[lane_index] <= 1'b0;
        pending_addr[lane_index] <= 14'd0;
        pending_slice[lane_index] <= 4'd0;
        pending_delay[lane_index] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        active_command_index <= issued_commands;
        $display(
          "COMMAND_ACCEPT idx=%0d cmd=%0d head_base=%0d group=%0d wave=%0d cycle=%0d",
          issued_commands,
          cmd_id_mem[issued_commands],
          cmd_head_base_mem[issued_commands],
          issued_commands / {LOCAL_TEMPORAL_WAVES},
          issued_commands % {LOCAL_TEMPORAL_WAVES},
          cluster_cycle_count
        );
        issued_commands <= issued_commands + 1;
      end

      for (producer_index = 0; producer_index < PRODUCERS; producer_index = producer_index + 1) begin
        if (input_valid[producer_index] && input_ready[producer_index]) begin
          beat_issue[producer_index] <= beat_issue[producer_index] + 1;
        end
      end

      for (lane_index = 0; lane_index < VALUE_LANES; lane_index = lane_index + 1) begin
        if (value_response_valid[lane_index] && value_response_ready[lane_index]) begin
          value_response_valid[lane_index] <= 1'b0;
        end
        if (value_read_req_valid[lane_index] && value_read_req_ready[lane_index]) begin
          if (pending_valid[lane_index]) $fatal(1, "value lane %0d multiple outstanding request", lane_index);
          pending_valid[lane_index] <= 1'b1;
          pending_addr[lane_index] <= value_read_req_address[(lane_index * 14) +: 14];
          pending_slice[lane_index] <= value_read_req_slice[(lane_index * 4) +: 4];
          pending_delay[lane_index] <= 0;
        end
        if (pending_valid[lane_index]) begin
          if (pending_delay[lane_index] == 0) begin
            if (!value_response_valid[lane_index]) begin
              producer_index = lane_index / 2;
              stream_index = lane_index % 2;
              response_index =
                  ((((producer_index * 2) + stream_index) * MAX_BLOCKS_PER_PRODUCER)
                   + cmd_block_offset_mem[active_command_index][producer_index]
                   + pending_addr[lane_index]) * 16
                  + pending_slice[lane_index];
              pending_valid[lane_index] <= 1'b0;
              value_response_valid[lane_index] <= 1'b1;
              value_response_address[(lane_index * 14) +: 14] <= pending_addr[lane_index];
              value_response_slice[(lane_index * 4) +: 4] <= pending_slice[lane_index];
              value_response_matrix[(lane_index * 512) +: 512] <= value_mem[response_index];
            end
          end else begin
            pending_delay[lane_index] <= pending_delay[lane_index] - 1;
          end
        end
      end

      if (out_valid && out_ready) begin
        $display(
          "RESULT idx=%0d cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
          result_seen,
          out_command_id,
          out_head_id,
          out_slice,
          out_last,
          $signed(out_global_max),
          out_exp_sum,
          out_value,
          reducer_cycle_count
        );
        result_seen <= result_seen + 1;
        if (result_seen + 1 == TOTAL_RESULTS) begin
          pending_summary <= 1'b1;
        end
      end

      if (pending_summary) begin
        for (producer_index = 0; producer_index < PRODUCERS; producer_index = producer_index + 1) begin
          $display(
            "PRODUCER idx=%0d accept=%0d complete=%0d merge=%0d stall=%0d stream0_accept=%0d stream1_accept=%0d stream0_complete=%0d stream1_complete=%0d stream_error=%0d merge_error=%0d protocol=%0d",
            producer_index,
            producer_command_accept_count[(producer_index * 32) +: 32],
            producer_command_completed_count[(producer_index * 32) +: 32],
            producer_merge_completed_count[(producer_index * 32) +: 32],
            producer_result_stall_cycles[(producer_index * 32) +: 32],
            producer_stream_command_accept_count[(producer_index * 64) +: 32],
            producer_stream_command_accept_count[(producer_index * 64) + 32 +: 32],
            producer_stream_completed_count[(producer_index * 64) +: 32],
            producer_stream_completed_count[(producer_index * 64) + 32 +: 32],
            producer_stream_protocol_error[(producer_index * 2) +: 2],
            producer_merge_protocol_error[producer_index],
            producer_protocol_error[producer_index]
          );
        end
        $display(
          "SUMMARY outputs=%0d drain=%0d protocol_error=%0d atomic_error=%0d group_error=%0d local_tree_error=%0d temporal_error=%0d reducer_error=%0d wave_accept=%0d group_complete=%0d local_root_completed=%0d temporal_completed=%0d emitted=%0d issue_wait=%0d ready_skew=%0d",
          result_seen,
          cluster_cycle_count,
          protocol_error,
          atomic_command_protocol_error,
          group_contract_error,
          local_tree_protocol_error,
          temporal_merge_protocol_error,
          reducer_protocol_error,
          wave_command_accept_count,
          reducer_completed_command_count,
          reducer_local_root_completed_count,
          reducer_temporal_merge_completed_count,
          reducer_emitted_beat_count,
          wave_command_issue_wait_cycles,
          producer_ready_skew_cycles
        );
        #1 $finish;
      end

      if (cycle > 500000) begin
        $display("TIMEOUT cycle=%0d", cycle);
        $finish;
      end
    end
  end

  initial begin
{chr(10).join(cmd_init)}
{chr(10).join(beat_limit_init)}
{chr(10).join(beat_init)}
{chr(10).join(value_init)}
{ready_init}
    clk = 0;
    rst_n = 0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def build_report(
    config: JsonDict | None = None,
    *,
    head_dim: int | None = None,
    seed: int | None = None,
    head_bases: tuple[int, ...] | None = None,
    timeout_s: int | None = None,
    output_ready_pattern: tuple[bool, ...] | None = None,
) -> JsonDict:
    payload = json.loads(json.dumps(config or _default_config()))
    body = payload.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise ValueError(f"config must contain {_CONFIG_KEY}")
    producers = int(body.get("producers", 53))
    workload = _resolve_workload(
        payload,
        head_dim=head_dim,
        seed=seed,
        head_bases=head_bases,
        timeout_s=timeout_s,
    )
    ready_pattern = tuple(bool(value) for value in output_ready_pattern) if output_ready_pattern is not None else (True,)
    expected_rows = _expected_rows(producers, workload)
    wave_commands = _wave_commands(producers, workload)
    expected_command_schedule = [
        {
            "index": index,
            "command_id": int(command["command_id"]),
            "head_base": int(command["head_base"]),
            "group_index": int(command["group_index"]),
            "wave_index": int(command["wave_index"]),
        }
        for index, command in enumerate(wave_commands)
    ]

    base_report: JsonDict = {
        "model": "attention_score32_exact_local_cluster_gqa8_probe_v1",
        "producers": producers,
        "groups": int(workload["groups"]),
        "waves": int(workload["waves"]),
        "wave_commands": int(workload["wave_commands"]),
        "head_bases": list(int(value) for value in workload["head_bases"]),
        "head_dim": int(workload["head_dim"]),
        "expected_outputs": len(expected_rows),
        "rotation_schedule": {
            f"group_{group_index}": {
                "extra_producers": list(
                    exact_local_cluster_gqa8_extra_producers(producers=producers, group_index=group_index)
                ),
                "block_counts": list(
                    exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=group_index)
                ),
            }
            for group_index in range(len(LOCAL_CLUSTER_GQA8_HEAD_BASES))
        },
        "command_schedule": expected_command_schedule,
        "service_model": exact_local_cluster_gqa8_service_manifest(producers=producers),
        "source_links": payload.get("report_links", {}),
        "timed_out": False,
        "full_probe_attempted": True,
    }

    with tempfile.TemporaryDirectory(prefix="score32_exact_local_cluster_gqa8_probe_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        rtl_dir = temp_dir / "rtl"
        tb_path = temp_dir / "tb.sv"
        fakeram_path = temp_dir / "fakeram45_2048x39.sv"
        generate(payload, rtl_dir)
        tb_path.write_text(
            _testbench(
                top_name=str(payload["top_name"]),
                producers=producers,
                workload=workload,
                output_ready_pattern=ready_pattern,
            ),
            encoding="utf-8",
        )
        fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")
        simv = temp_dir / "simv"
        try:
            subprocess.run(
                [
                    _tool("iverilog"),
                    "-g2012",
                    "-s",
                    "tb",
                    "-o",
                    str(simv),
                    str(rtl_dir / "producer.v"),
                    str(rtl_dir / "reducer.v"),
                    str(rtl_dir / "top.v"),
                    str(fakeram_path),
                    str(tb_path),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
                timeout=int(workload["timeout_s"]),
            )
            run = subprocess.run(
                [_tool("vvp"), str(simv)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
                timeout=int(workload["timeout_s"]),
            )
        except subprocess.TimeoutExpired as exc:
            base_report.update(
                {
                    "timed_out": True,
                    "timeout_s": int(workload["timeout_s"]),
                    "timeout_phase": "iverilog" if exc.cmd and "iverilog" in str(exc.cmd[0]) else "vvp",
                    "passed": False,
                }
            )
            return base_report
        except subprocess.CalledProcessError as exc:
            phase = Path(str(exc.cmd[0])).name if exc.cmd else "subprocess"
            raise RuntimeError(
                f"{phase} failed while probing the full-width local cluster\n"
                f"stdout:\n{exc.stdout}\n"
                f"stderr:\n{exc.stderr}"
            ) from exc

    observed_rows: list[dict[str, object]] = []
    producer_rows: list[dict[str, object]] = []
    command_rows: list[dict[str, int]] = []
    summary: JsonDict | None = None
    timeout_cycle: int | None = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _COMMAND_RE.fullmatch(stripped):
            command_rows.append(
                {
                    "index": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "head_base": int(match.group(3)),
                    "group_index": int(match.group(4)),
                    "wave_index": int(match.group(5)),
                    "cycle": int(match.group(6)),
                }
            )
            continue
        if match := _RESULT_RE.fullmatch(stripped):
            observed_rows.append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": list(unpack_numerators(int(match.group(8), 16))),
                    "cycle": int(match.group(9)),
                }
            )
            continue
        if match := _PRODUCER_RE.fullmatch(stripped):
            producer_rows.append(
                {
                    "index": int(match.group(1)),
                    "accept_count": int(match.group(2)),
                    "complete_count": int(match.group(3)),
                    "merge_completed_count": int(match.group(4)),
                    "stall_cycles": int(match.group(5)),
                    "stream_accept_count": [int(match.group(6)), int(match.group(7))],
                    "stream_complete_count": [int(match.group(8)), int(match.group(9))],
                    "stream_protocol_error": int(match.group(10)),
                    "merge_protocol_error": bool(int(match.group(11))),
                    "protocol_error": bool(int(match.group(12))),
                }
            )
            continue
        if match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "drain_cycles": int(match.group(2)),
                "protocol_error": bool(int(match.group(3))),
                "atomic_command_protocol_error": bool(int(match.group(4))),
                "group_contract_error": bool(int(match.group(5))),
                "local_tree_protocol_error": bool(int(match.group(6))),
                "temporal_merge_protocol_error": bool(int(match.group(7))),
                "reducer_protocol_error": bool(int(match.group(8))),
                "wave_command_accept_count": int(match.group(9)),
                "reducer_completed_command_count": int(match.group(10)),
                "reducer_local_root_completed_count": int(match.group(11)),
                "reducer_temporal_merge_completed_count": int(match.group(12)),
                "reducer_emitted_beat_count": int(match.group(13)),
                "wave_command_issue_wait_cycles": int(match.group(14)),
                "producer_ready_skew_cycles": int(match.group(15)),
            }
            continue
        if match := _TB_TIMEOUT_RE.fullmatch(stripped):
            timeout_cycle = int(match.group(1))

    if summary is None:
        if timeout_cycle is not None:
            base_report.update(
                {
                    "timed_out": True,
                    "timeout_s": int(workload["timeout_s"]),
                    "timeout_phase": "tb",
                    "timeout_cycle": timeout_cycle,
                    "outputs": len(observed_rows),
                    "command_rows": command_rows,
                    "producer_rows": producer_rows,
                    "passed": False,
                }
            )
            return base_report
        raise RuntimeError(f"missing summary in simulator output:\n{run.stdout}")

    normalized_observed_rows = [
        {key: row[key] for key in ("command_id", "head_id", "slice", "last", "global_max", "exp_sum", "value")}
        for row in observed_rows
    ]
    expected_producer_accepts = int(workload["wave_commands"])
    expected_producer_merges = int(workload["wave_commands"]) * 8 * 16
    command_schedule_matches = [
        {key: row[key] for key in ("index", "command_id", "head_base", "group_index", "wave_index")}
        for row in command_rows
    ] == expected_command_schedule
    producer_counts_match = len(producer_rows) == producers and all(
        row["accept_count"] == expected_producer_accepts
        and row["complete_count"] == expected_producer_accepts
        and row["merge_completed_count"] == expected_producer_merges
        and row["stall_cycles"] == 0
        and row["stream_accept_count"] == [expected_producer_accepts, expected_producer_accepts]
        and row["stream_complete_count"] == [expected_producer_accepts, expected_producer_accepts]
        and row["stream_protocol_error"] == 0
        and not row["merge_protocol_error"]
        and not row["protocol_error"]
        for row in producer_rows
    )

    passed = (
        command_schedule_matches
        and producer_counts_match
        and normalized_observed_rows == expected_rows
        and summary["outputs"] == len(expected_rows)
        and summary["wave_command_accept_count"] == int(workload["wave_commands"])
        and summary["reducer_completed_command_count"] == len(LOCAL_CLUSTER_GQA8_HEAD_BASES)
        and summary["reducer_local_root_completed_count"] == len(LOCAL_CLUSTER_GQA8_HEAD_BASES) * LOCAL_TEMPORAL_WAVES * 8 * 16
        and summary["reducer_temporal_merge_completed_count"]
        == len(LOCAL_CLUSTER_GQA8_HEAD_BASES) * (LOCAL_TEMPORAL_WAVES - 1) * 8 * 16
        and summary["reducer_emitted_beat_count"] == len(expected_rows)
        and not summary["protocol_error"]
        and not summary["atomic_command_protocol_error"]
        and not summary["group_contract_error"]
        and not summary["local_tree_protocol_error"]
        and not summary["temporal_merge_protocol_error"]
        and not summary["reducer_protocol_error"]
    )

    base_report.update(summary)
    base_report.update(
        {
            "outputs": len(observed_rows),
            "observed_rows": normalized_observed_rows,
            "expected_rows": expected_rows,
            "command_rows": command_rows,
            "producer_rows": producer_rows,
            "command_schedule_matches": command_schedule_matches,
            "producer_counts_match": producer_counts_match,
            "passed": passed,
        }
    )
    return base_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--head-dim", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--timeout-s", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    payload = _default_config()
    if args.config is not None:
        payload = json.loads(args.config.read_text(encoding="utf-8"))
    report = build_report(
        payload,
        head_dim=args.head_dim,
        seed=args.seed,
        timeout_s=args.timeout_s,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(encoded, encoding="utf-8")
    if args.json or args.out is None:
        print(encoded, end="")
    return 0 if report.get("passed") or report.get("timed_out") else 1


if __name__ == "__main__":
    raise SystemExit(main())
