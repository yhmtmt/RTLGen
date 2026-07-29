#!/usr/bin/env python3
"""Run the cluster-SRAM-composed full GQA8 hierarchy against the exact reference."""

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
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import probe_attention_score32_exact_local16_global_tree_gqa8 as full_probe
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import (
    CONFIG_KEY,
    build_default_config,
    generate,
)
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    compose_local16_global_tree_gqa8_exact,
    exact_local16_global_tree_cluster_sram_gqa8_service_manifest,
    unpack_final_values,
    unpack_numerators,
)
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    BLOCK_SLOTS_PER_STREAM,
    ROWS_PER_BUFFER,
    STREAMS,
    VALUE_SLICES,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)

JsonDict = dict[str, Any]

CLUSTERS = 16
CLUSTER_PRODUCERS = tuple([54] * 8 + [53] * 8)
TOTAL_PRODUCERS = sum(CLUSTER_PRODUCERS)
COMMAND_ID = 0x8200
HEAD_BASE = 0
SEED = 29
WAVES = LOCAL_TEMPORAL_WAVES
TB_TIMEOUT_CYCLES = 50_000
DEFAULT_SUBPROCESS_TIMEOUT_SEC = 900
DEFAULT_ROOT_READY_PATTERN = (True, True, False, True)
MAX_BEATS_PER_PRODUCER = WAVES * 2

EXPECTED_TOTALS = {
    "fill_target_accept_count": 128,
    "fill_row_accept_count": 262_144,
    "producer_handshake_count": 8_192,
    "sram_request_accept_count": 262_144,
    "sram_response_accept_count": 262_144,
    "cluster_row_count": 2_048,
    "root_row_count": 128,
}
EXPECTED_PER_CLUSTER = {
    "wave_command_accept_count": 8,
    "completed_command_count": 1,
    "emitted_beat_count": 128,
    "fill_target_accept_count": 8,
    "fill_row_accept_count": 16_384,
    "request_accept_count": 16_384,
    "response_accept_count": 16_384,
    "command_accept_count": 8,
    "command_release_count": 8,
}

_CLUSTER_RESULT_RE = re.compile(
    r"CLUSTER_RESULT cluster=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) "
    r"max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_ROOT_RESULT_RE = re.compile(
    r"ROOT_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY producer_handshakes=(\d+) fill_targets=(\d+) fill_rows=(\d+) "
    r"sram_requests=(\d+) sram_responses=(\d+) cluster_rows=(\d+) root_rows=(\d+) "
    r"command_accepts=(\d+) cadence_accepts=(\d+) protocol_error=(\d+) "
    r"first_root=(-?\d+) last_root=(-?\d+) drain=(\d+)"
)
_CLUSTER_SUMMARY_RE = re.compile(
    r"CLUSTER_SUMMARY cluster=(\d+) wave_accept=(\d+) completed=(\d+) emitted=(\d+) "
    r"fill_targets=(\d+) fill_rows=(\d+) requests=(\d+) responses=(\d+) "
    r"command_accepts=(\d+) command_releases=(\d+) errors=(\d+)"
)
_TB_TIMEOUT_RE = re.compile(r"TB_TIMEOUT cycle=(\d+)")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def compare_full_rows(
    expected_rows: list[dict[str, object]],
    observed_rows: list[dict[str, object]],
) -> JsonDict:
    """Compare every structured field; hashes are diagnostics, not the oracle."""
    result: JsonDict = {
        "passed": expected_rows == observed_rows,
        "expected_row_count": len(expected_rows),
        "observed_row_count": len(observed_rows),
        "expected_hash": _hash(expected_rows),
        "observed_hash": _hash(observed_rows),
        "first_mismatch": None,
    }
    shared_rows = min(len(expected_rows), len(observed_rows))
    for index in range(shared_rows):
        expected = expected_rows[index]
        observed = observed_rows[index]
        if expected == observed:
            continue
        for field in sorted(set(expected) | set(observed)):
            if expected.get(field) != observed.get(field):
                result["first_mismatch"] = {
                    "row": index,
                    "field": field,
                    "expected": expected.get(field),
                    "observed": observed.get(field),
                }
                return result
    if len(expected_rows) != len(observed_rows):
        result["first_mismatch"] = {
            "row": shared_rows,
            "field": "__row_count__",
            "expected": len(expected_rows),
            "observed": len(observed_rows),
        }
    return result


def compare_compositional_rows(
    *,
    expected_cluster_rows: list[list[dict[str, object]]],
    observed_cluster_rows: list[list[dict[str, object]]],
    expected_root_rows: list[dict[str, object]],
    observed_root_rows: list[dict[str, object]],
) -> JsonDict:
    if len(expected_cluster_rows) != CLUSTERS or len(observed_cluster_rows) != CLUSTERS:
        raise ValueError("compositional audit requires exactly 16 cluster row streams")
    clusters = [
        compare_full_rows(expected_cluster_rows[index], observed_cluster_rows[index])
        for index in range(CLUSTERS)
    ]
    root = compare_full_rows(expected_root_rows, observed_root_rows)
    return {
        "passed": all(bool(result["passed"]) for result in clusters) and bool(root["passed"]),
        "clusters": clusters,
        "root": root,
    }


def expected_schedule_prefix(*, command_count: int) -> tuple[tuple[int, int], ...]:
    """Retain the public schedule helper while exposing this probe's fixed prefix."""
    resolved = int(command_count)
    if resolved < 0:
        raise ValueError("command_count must be non-negative")
    head_bases = (0, 8, 16, 24)
    return tuple((head_bases[(index // WAVES) % 4], index % WAVES) for index in range(resolved))


def expected_counts() -> JsonDict:
    return {
        "totals": dict(EXPECTED_TOTALS),
        "per_cluster": [dict(EXPECTED_PER_CLUSTER) for _ in range(CLUSTERS)],
    }


def _logical_command() -> dict[str, int]:
    multiplier, shift = full_probe._score_params(HEAD_BASE)
    return {
        "logical_index": 0,
        "group_index": 0,
        "command_id": COMMAND_ID,
        "head_base": HEAD_BASE,
        "multiplier": multiplier,
        "shift": shift,
    }


def _cluster_bases() -> tuple[int, ...]:
    bases: list[int] = []
    cursor = 0
    for producers in CLUSTER_PRODUCERS:
        bases.append(cursor)
        cursor += producers
    return tuple(bases)


def _reference() -> dict[str, object]:
    logical_command = _logical_command()
    composition = compose_local16_global_tree_gqa8_exact(
        tuple(
            tuple(
                tuple(
                    full_probe._producer_wave_stream(
                        cluster=cluster,
                        producer=producer,
                        logical_command=logical_command,
                        wave_index=wave,
                        block_count=exact_local_cluster_gqa8_command_block_counts(
                            producers=CLUSTER_PRODUCERS[cluster],
                            group_index=0,
                        )[producer],
                        seed=SEED,
                    )
                    for producer in range(CLUSTER_PRODUCERS[cluster])
                )
                for wave in range(WAVES)
            )
            for cluster in range(CLUSTERS)
        )
    )
    cluster_rows = [
        [
            {
                "cluster": cluster,
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in composition.cluster_compositions[cluster].temporal_aggregate
        ]
        for cluster in range(CLUSTERS)
    ]
    root_rows = [
        {
            "command_id": beat.command_id,
            "head_id": beat.head_id,
            "slice": beat.slice_index,
            "last": beat.last,
            "value": list(beat.values),
        }
        for beat in composition.finalized_beats
    ]
    return {
        "cluster_rows": cluster_rows,
        "root_rows": root_rows,
        "cluster_hashes": [_hash(rows) for rows in cluster_rows],
        "root_hash": _hash(root_rows),
    }


def _query_key_words() -> tuple[list[int], list[int]]:
    query_words = [0] * (TOTAL_PRODUCERS * MAX_BEATS_PER_PRODUCER)
    key_words = [0] * (TOTAL_PRODUCERS * MAX_BEATS_PER_PRODUCER)
    cluster_bases = _cluster_bases()
    for cluster, producers in enumerate(CLUSTER_PRODUCERS):
        block_counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=0)
        for producer, block_count in enumerate(block_counts):
            global_producer = cluster_bases[cluster] + producer
            beat_cursor = 0
            for wave in range(WAVES):
                stream_blocks = [
                    full_probe._stream_block_beats(
                        cluster=cluster,
                        producer=producer,
                        group_index=0,
                        wave_index=wave,
                        stream=stream,
                        block_count=block_count,
                        seed=SEED,
                    )
                    for stream in range(STREAMS)
                ]
                for block in range(block_count):
                    queries0, keys0 = stream_blocks[0][block][0]
                    queries1, keys1 = stream_blocks[1][block][0]
                    flat = (global_producer * MAX_BEATS_PER_PRODUCER) + beat_cursor
                    query_words[flat] = full_probe._pack(list(queries0), 8) | (
                        full_probe._pack(list(queries1), 8) << 64
                    )
                    key_words[flat] = full_probe._pack(list(keys0), 8) | (
                        full_probe._pack(list(keys1), 8) << 64
                    )
                    beat_cursor += 1
    return query_words, key_words


def _fill_rows_for_wave(*, cluster: int, wave: int) -> list[int]:
    producers = CLUSTER_PRODUCERS[cluster]
    block_counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=0)
    slot_bases = exact_local_cluster_gqa8_slot_bases(producers=producers, group_index=0)
    rows: list[int | None] = [None] * ROWS_PER_BUFFER
    for producer, block_count in enumerate(block_counts):
        for stream in range(STREAMS):
            value_blocks = full_probe._value_blocks(
                cluster=cluster,
                producer=producer,
                group_index=0,
                wave_index=wave,
                stream=stream,
                block_count=block_count,
                seed=SEED,
            )
            for block in range(block_count):
                block_slot = slot_bases[producer] + block
                for value_slice in range(VALUE_SLICES):
                    flat = (stream * BLOCK_SLOTS_PER_STREAM * VALUE_SLICES) + (
                        block_slot * VALUE_SLICES
                    ) + value_slice
                    rows[flat] = full_probe._pack(
                        [lane for row in value_blocks[block][value_slice] for lane in row],
                        8,
                    )
    if any(row is None for row in rows):
        raise AssertionError(f"incomplete p{producers} fill schedule for cluster {cluster} wave {wave}")
    return [int(row) for row in rows]


def _write_memh(path: Path, values: Iterable[int], *, width_bits: int) -> None:
    width_hex = (width_bits + 3) // 4
    with path.open("w", encoding="ascii") as handle:
        for value in values:
            handle.write(f"{int(value) & ((1 << width_bits) - 1):0{width_hex}x}\n")


def _write_memh_sidecars(directory: Path) -> dict[str, object]:
    query_words, key_words = _query_key_words()
    query_path = directory / "query.memh"
    key_path = directory / "key.memh"
    fill_path = directory / "fill.memh"
    _write_memh(query_path, query_words, width_bits=128)
    _write_memh(key_path, key_words, width_bits=128)
    with fill_path.open("w", encoding="ascii") as handle:
        for cluster in range(CLUSTERS):
            for wave in range(WAVES):
                for value in _fill_rows_for_wave(cluster=cluster, wave=wave):
                    handle.write(f"{value:0128x}\n")
    return {
        "query": query_path.name,
        "key": key_path.name,
        "fill": fill_path.name,
        "query_words": len(query_words),
        "key_words": len(key_words),
        "fill_words": CLUSTERS * WAVES * ROWS_PER_BUFFER,
    }


def _sum_slices(signal: str, width: int = 32) -> str:
    return " + ".join(f"{signal}[{cluster * width} +: {width}]" for cluster in range(CLUSTERS))


def _cluster_result_logging() -> str:
    lines: list[str] = []
    for cluster in range(CLUSTERS):
        lines.extend(
            [
                f"      if (dut.cluster_out_valid_w[{cluster}] && dut.cluster_out_ready_w[{cluster}]) begin",
                f'        $display("CLUSTER_RESULT cluster={cluster} cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",',
                f"                 dut.cluster_out_command_id_w[{cluster * 16} +: 16],",
                f"                 dut.cluster_out_head_id_w[{cluster * 5} +: 5],",
                f"                 dut.cluster_out_slice_w[{cluster * 4} +: 4],",
                f"                 dut.cluster_out_last_w[{cluster}],",
                f"                 $signed(dut.cluster_out_global_max_w[{cluster * 32} +: 32]),",
                f"                 dut.cluster_out_exp_sum_w[{cluster * 33} +: 33],",
                f"                 dut.cluster_out_value_w[{cluster * 328} +: 328], cycle);",
                "      end",
            ]
        )
    return "\n".join(lines)


def _cluster_summary_logging() -> str:
    lines: list[str] = []
    error_signals = (
        "cluster_group_contract_error",
        "cluster_local_tree_protocol_error",
        "cluster_temporal_merge_protocol_error",
        "cluster_reducer_protocol_error",
        "cluster_atomic_command_protocol_error",
        "cluster_sram_invalid_metadata_error",
        "cluster_sram_invalid_address_error",
        "cluster_sram_residency_error",
        "cluster_sram_overwrite_error",
        "cluster_sram_command_error",
        "cluster_sram_buffer_map_error",
        "cluster_sram_release_guard_error",
        "cluster_sram_protocol_error",
        "cluster_protocol_error",
        "cluster_fill_schedule_contract_error",
    )
    for cluster in range(CLUSTERS):
        errors = " | ".join(f"{signal}[{cluster}]" for signal in error_signals)
        lines.extend(
            [
                f'        $display("CLUSTER_SUMMARY cluster={cluster} wave_accept=%0d completed=%0d emitted=%0d fill_targets=%0d fill_rows=%0d requests=%0d responses=%0d command_accepts=%0d command_releases=%0d errors=%0d",',
                f"                 cluster_wave_command_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_completed_command_count[{cluster * 32} +: 32],",
                f"                 cluster_emitted_beat_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_fill_target_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_fill_row_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_request_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_response_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_command_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_sram_command_release_count[{cluster * 32} +: 32],",
                f"                 {errors});",
            ]
        )
    return "\n".join(lines)


def _testbench(
    *,
    top_name: str,
    output_ready_pattern: tuple[bool, ...] = DEFAULT_ROOT_READY_PATTERN,
) -> str:
    if not output_ready_pattern:
        raise ValueError("root ready pattern must not be empty")
    multiplier, shift = full_probe._score_params(HEAD_BASE)
    ready_init = "\n".join(
        f"    root_ready_mem[{index}] = 1'b{int(value)};"
        for index, value in enumerate(output_ready_pattern)
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer CLUSTERS = {CLUSTERS};
  localparam integer WAVES = {WAVES};
  localparam integer TOTAL_PRODUCERS = {TOTAL_PRODUCERS};
  localparam integer MAX_BEATS_PER_PRODUCER = {MAX_BEATS_PER_PRODUCER};
  localparam integer ROWS_PER_TARGET = {ROWS_PER_BUFFER};
  localparam integer ROOT_READY_PATTERN_LEN = {len(output_ready_pattern)};
  localparam integer EXPECTED_ROOT_ROWS = {EXPECTED_TOTALS["root_row_count"]};
  localparam integer TB_TIMEOUT_CYCLES = {TB_TIMEOUT_CYCLES};

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  integer issued_commands = 0;
  integer active_command_index = -1;
  integer producer_handshakes = 0;
  integer cluster_rows_seen = 0;
  integer root_rows_seen = 0;
  integer first_root_cycle = -1;
  integer last_root_cycle = -1;
  reg pending_summary = 1'b0;
  reg preload_complete;

  reg [127:0] query_mem [0:(TOTAL_PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [127:0] key_mem [0:(TOTAL_PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [511:0] fill_mem [0:(CLUSTERS*WAVES*ROWS_PER_TARGET)-1];
  reg root_ready_mem [0:ROOT_READY_PATTERN_LEN-1];

  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [4:0] command_head_base;
  reg [31:0] command_score_multiplier;
  reg [5:0] command_score_shift;
  reg [15:0] fill_target_valid;
  wire [15:0] fill_target_ready;
  reg [15:0] fill_target_buffer_sel;
  reg [255:0] fill_target_command_id;
  reg [79:0] fill_target_head_base;
  reg [47:0] fill_target_wave_index;
  reg [15:0] fill_valid;
  wire [15:0] fill_ready;
  reg [15:0] fill_buffer_sel;
  reg [15:0] fill_stream;
  reg [95:0] fill_block_slot;
  reg [63:0] fill_slice;
  reg [8191:0] fill_data;
  reg [855:0] input_valid;
  wire [855:0] input_ready;
  reg [855:0] input_last;
  reg signed [109567:0] input_query;
  reg signed [109567:0] input_key;
  wire root_valid;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [4:0] expected_head_base;
  wire [2:0] expected_wave_index;
  wire [31:0] cadence_command_accept_count;
  wire command_cadence_error;
  wire [15:0] cluster_fill_schedule_contract_error;
  wire fill_schedule_contract_error;
  wire [511:0] cluster_wave_command_accept_count;
  wire [511:0] cluster_emitted_beat_count;
  wire [511:0] cluster_completed_command_count;
  wire [15:0] cluster_group_contract_error;
  wire [15:0] cluster_local_tree_protocol_error;
  wire [15:0] cluster_temporal_merge_protocol_error;
  wire [15:0] cluster_reducer_protocol_error;
  wire [15:0] cluster_atomic_command_protocol_error;
  wire [511:0] cluster_sram_fill_target_accept_count;
  wire [511:0] cluster_sram_fill_row_accept_count;
  wire [511:0] cluster_sram_request_accept_count;
  wire [511:0] cluster_sram_response_accept_count;
  wire [511:0] cluster_sram_command_accept_count;
  wire [511:0] cluster_sram_command_release_count;
  wire [15:0] cluster_sram_invalid_metadata_error;
  wire [15:0] cluster_sram_invalid_address_error;
  wire [15:0] cluster_sram_residency_error;
  wire [15:0] cluster_sram_overwrite_error;
  wire [15:0] cluster_sram_command_error;
  wire [15:0] cluster_sram_buffer_map_error;
  wire [15:0] cluster_sram_release_guard_error;
  wire [15:0] cluster_sram_protocol_error;
  wire [31:0] global_root_completed_count;
  wire [31:0] global_finalizer_accepted_count;
  wire [31:0] global_tree_root_completed_count;
  wire global_tree_protocol_error;
  wire global_order_protocol_error;
  wire global_finalizer_protocol_error;
  wire [15:0] cluster_protocol_error;
  wire protocol_error;

  integer beat_issue [0:TOTAL_PRODUCERS-1];
  integer fill_wave [0:CLUSTERS-1];
  integer fill_row_index [0:CLUSTERS-1];
  integer producer_index;
  integer cluster_index;
  integer local_producer;
  integer producer_block_count;
  integer flat_index;
  integer fill_flat_index;

  {top_name} dut (
      .clk(clk), .rst_n(rst_n),
      .command_valid(command_valid), .command_ready(command_ready),
      .command_id(command_id), .command_head_base(command_head_base),
      .command_score_multiplier(command_score_multiplier), .command_score_shift(command_score_shift),
      .fill_target_valid(fill_target_valid), .fill_target_ready(fill_target_ready),
      .fill_target_buffer_sel(fill_target_buffer_sel),
      .fill_target_command_id(fill_target_command_id),
      .fill_target_head_base(fill_target_head_base),
      .fill_target_wave_index(fill_target_wave_index),
      .fill_valid(fill_valid), .fill_ready(fill_ready), .fill_buffer_sel(fill_buffer_sel),
      .fill_stream(fill_stream), .fill_block_slot(fill_block_slot),
      .fill_slice(fill_slice), .fill_data(fill_data),
      .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
      .input_query(input_query), .input_key(input_key),
      .root_valid(root_valid), .root_ready(root_ready), .root_command_id(root_command_id),
      .root_head_id(root_head_id), .root_slice(root_slice), .root_last(root_last), .root_value(root_value),
      .expected_head_base(expected_head_base), .expected_wave_index(expected_wave_index),
      .cadence_command_accept_count(cadence_command_accept_count),
      .command_cadence_error(command_cadence_error),
      .cluster_fill_schedule_contract_error(cluster_fill_schedule_contract_error),
      .fill_schedule_contract_error(fill_schedule_contract_error),
      .cluster_wave_command_accept_count(cluster_wave_command_accept_count),
      .cluster_emitted_beat_count(cluster_emitted_beat_count),
      .cluster_completed_command_count(cluster_completed_command_count),
      .cluster_group_contract_error(cluster_group_contract_error),
      .cluster_local_tree_protocol_error(cluster_local_tree_protocol_error),
      .cluster_temporal_merge_protocol_error(cluster_temporal_merge_protocol_error),
      .cluster_reducer_protocol_error(cluster_reducer_protocol_error),
      .cluster_atomic_command_protocol_error(cluster_atomic_command_protocol_error),
      .cluster_sram_fill_target_accept_count(cluster_sram_fill_target_accept_count),
      .cluster_sram_fill_row_accept_count(cluster_sram_fill_row_accept_count),
      .cluster_sram_request_accept_count(cluster_sram_request_accept_count),
      .cluster_sram_response_accept_count(cluster_sram_response_accept_count),
      .cluster_sram_command_accept_count(cluster_sram_command_accept_count),
      .cluster_sram_command_release_count(cluster_sram_command_release_count),
      .cluster_sram_invalid_metadata_error(cluster_sram_invalid_metadata_error),
      .cluster_sram_invalid_address_error(cluster_sram_invalid_address_error),
      .cluster_sram_residency_error(cluster_sram_residency_error),
      .cluster_sram_overwrite_error(cluster_sram_overwrite_error),
      .cluster_sram_command_error(cluster_sram_command_error),
      .cluster_sram_buffer_map_error(cluster_sram_buffer_map_error),
      .cluster_sram_release_guard_error(cluster_sram_release_guard_error),
      .cluster_sram_protocol_error(cluster_sram_protocol_error),
      .global_root_completed_count(global_root_completed_count),
      .global_finalizer_accepted_count(global_finalizer_accepted_count),
      .global_tree_root_completed_count(global_tree_root_completed_count),
      .global_tree_protocol_error(global_tree_protocol_error),
      .global_order_protocol_error(global_order_protocol_error),
      .global_finalizer_protocol_error(global_finalizer_protocol_error),
      .cluster_protocol_error(cluster_protocol_error), .protocol_error(protocol_error)
  );

  always #5 clk = ~clk;

  always @* begin
    preload_complete = 1'b1;
    for (cluster_index = 0; cluster_index < CLUSTERS; cluster_index = cluster_index + 1)
      if (fill_wave[cluster_index] < 2) preload_complete = 1'b0;

    command_valid = rst_n && preload_complete && (issued_commands < WAVES);
    command_id = 16'h{COMMAND_ID:04x};
    command_head_base = 5'd{HEAD_BASE};
    command_score_multiplier = 32'd{multiplier};
    command_score_shift = 6'd{shift};
    root_ready = root_ready_mem[cycle % ROOT_READY_PATTERN_LEN];

    fill_target_valid = 16'd0;
    fill_target_buffer_sel = 16'd0;
    fill_target_command_id = 256'd0;
    fill_target_head_base = 80'd0;
    fill_target_wave_index = 48'd0;
    fill_valid = 16'd0;
    fill_buffer_sel = 16'd0;
    fill_stream = 16'd0;
    fill_block_slot = 96'd0;
    fill_slice = 64'd0;
    fill_data = 8192'd0;
    for (cluster_index = 0; cluster_index < CLUSTERS; cluster_index = cluster_index + 1) begin
      if (rst_n && (fill_wave[cluster_index] < WAVES)) begin
        if (fill_row_index[cluster_index] < 0) begin
          if ((expected_head_base == 5'd0) &&
              (fill_wave[cluster_index] <= (expected_wave_index + 1'b1))) begin
            fill_target_valid[cluster_index] = 1'b1;
            fill_target_buffer_sel[cluster_index] = fill_wave[cluster_index][0];
            fill_target_command_id[(cluster_index * 16) +: 16] = 16'h{COMMAND_ID:04x};
            fill_target_head_base[(cluster_index * 5) +: 5] = 5'd{HEAD_BASE};
            fill_target_wave_index[(cluster_index * 3) +: 3] = fill_wave[cluster_index][2:0];
          end
        end else begin
          fill_valid[cluster_index] = 1'b1;
          fill_buffer_sel[cluster_index] = fill_wave[cluster_index][0];
          fill_stream[cluster_index] = (fill_row_index[cluster_index] >= 1024);
          fill_block_slot[(cluster_index * 6) +: 6] =
              (fill_row_index[cluster_index] >> 4) & 6'h3f;
          fill_slice[(cluster_index * 4) +: 4] = fill_row_index[cluster_index] & 4'hf;
          fill_flat_index = ((cluster_index * WAVES + fill_wave[cluster_index]) * ROWS_PER_TARGET)
              + fill_row_index[cluster_index];
          fill_data[(cluster_index * 512) +: 512] = fill_mem[fill_flat_index];
        end
      end
    end

    input_valid = 856'd0;
    input_last = 856'd0;
    input_query = 109568'd0;
    input_key = 109568'd0;
    for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1) begin
      if (producer_index < 432) begin
        local_producer = producer_index % 54;
        producer_block_count = (local_producer < 10) ? 2 : 1;
      end else begin
        local_producer = (producer_index - 432) % 53;
        producer_block_count = (local_producer < 11) ? 2 : 1;
      end
      if (rst_n && (active_command_index >= 0) &&
          (beat_issue[producer_index] < ((active_command_index + 1) * producer_block_count))) begin
        flat_index = (producer_index * MAX_BEATS_PER_PRODUCER) + beat_issue[producer_index];
        input_valid[producer_index] = 1'b1;
        input_last[producer_index] = 1'b1;
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
      producer_handshakes <= 0;
      cluster_rows_seen <= 0;
      root_rows_seen <= 0;
      first_root_cycle <= -1;
      last_root_cycle <= -1;
      pending_summary <= 1'b0;
      for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1)
        beat_issue[producer_index] <= 0;
      for (cluster_index = 0; cluster_index < CLUSTERS; cluster_index = cluster_index + 1) begin
        fill_wave[cluster_index] <= 0;
        fill_row_index[cluster_index] <= -1;
      end
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        $display("COMMAND_ACCEPT idx=%0d cmd=%0d head_base=%0d wave=%0d cycle=%0d",
                 issued_commands, command_id, command_head_base, issued_commands, cycle);
        active_command_index <= issued_commands;
        issued_commands <= issued_commands + 1;
      end
      for (cluster_index = 0; cluster_index < CLUSTERS; cluster_index = cluster_index + 1) begin
        if (fill_target_valid[cluster_index] && fill_target_ready[cluster_index])
          fill_row_index[cluster_index] <= 0;
        if (fill_valid[cluster_index] && fill_ready[cluster_index]) begin
          if (fill_row_index[cluster_index] == ROWS_PER_TARGET - 1) begin
            fill_wave[cluster_index] <= fill_wave[cluster_index] + 1;
            fill_row_index[cluster_index] <= -1;
          end else begin
            fill_row_index[cluster_index] <= fill_row_index[cluster_index] + 1;
          end
        end
      end
      for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1) begin
        if (input_valid[producer_index] && input_ready[producer_index]) begin
          beat_issue[producer_index] <= beat_issue[producer_index] + 1;
        end
      end
      producer_handshakes <= producer_handshakes + $countones(input_valid & input_ready);
      cluster_rows_seen <= cluster_rows_seen +
          $countones(dut.cluster_out_valid_w & dut.cluster_out_ready_w);
{_cluster_result_logging()}
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        if (first_root_cycle < 0) first_root_cycle <= cycle;
        last_root_cycle <= cycle;
        root_rows_seen <= root_rows_seen + 1;
        if (root_rows_seen + 1 == EXPECTED_ROOT_ROWS) pending_summary <= 1'b1;
      end
      if (pending_summary) begin
        $display("SUMMARY producer_handshakes=%0d fill_targets=%0d fill_rows=%0d sram_requests=%0d sram_responses=%0d cluster_rows=%0d root_rows=%0d command_accepts=%0d cadence_accepts=%0d protocol_error=%0d first_root=%0d last_root=%0d drain=%0d",
                 producer_handshakes,
                 {_sum_slices("cluster_sram_fill_target_accept_count")},
                 {_sum_slices("cluster_sram_fill_row_accept_count")},
                 {_sum_slices("cluster_sram_request_accept_count")},
                 {_sum_slices("cluster_sram_response_accept_count")},
                 cluster_rows_seen, root_rows_seen, issued_commands, cadence_command_accept_count,
                 protocol_error, first_root_cycle, last_root_cycle, cycle);
{_cluster_summary_logging()}
        #1 $finish;
      end
      if (cycle >= TB_TIMEOUT_CYCLES) begin
        $display("TB_TIMEOUT cycle=%0d", cycle);
        #1 $finish;
      end
    end
  end

  initial begin
    $readmemh("query.memh", query_mem);
    $readmemh("key.memh", key_mem);
    $readmemh("fill.memh", fill_mem);
{ready_init}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _parse_stdout(
    stdout: str,
) -> tuple[dict[str, int], list[dict[str, int]], list[list[dict[str, object]]], list[dict[str, object]], int | None]:
    summary: dict[str, int] = {}
    cluster_summaries: list[dict[str, int]] = []
    cluster_rows: list[list[dict[str, object]]] = [[] for _ in range(CLUSTERS)]
    root_rows: list[dict[str, object]] = []
    tb_timeout_cycle: int | None = None
    for line in stdout.splitlines():
        if match := _CLUSTER_RESULT_RE.search(line):
            cluster = int(match.group(1))
            cluster_rows[cluster].append(
                {
                    "cluster": cluster,
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": list(unpack_numerators(int(match.group(8)))),
                }
            )
        elif match := _ROOT_RESULT_RE.search(line):
            root_rows.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "value": list(unpack_final_values(int(match.group(5)))),
                }
            )
        elif match := _SUMMARY_RE.search(line):
            keys = (
                "producer_handshake_count",
                "fill_target_accept_count",
                "fill_row_accept_count",
                "sram_request_accept_count",
                "sram_response_accept_count",
                "cluster_row_count",
                "root_row_count",
                "command_accept_count",
                "cadence_command_accept_count",
                "protocol_error",
                "first_root_cycle",
                "last_root_cycle",
                "drain_cycles",
            )
            summary = {key: int(match.group(index + 1)) for index, key in enumerate(keys)}
        elif match := _CLUSTER_SUMMARY_RE.search(line):
            keys = (
                "cluster",
                "wave_command_accept_count",
                "completed_command_count",
                "emitted_beat_count",
                "fill_target_accept_count",
                "fill_row_accept_count",
                "request_accept_count",
                "response_accept_count",
                "command_accept_count",
                "command_release_count",
                "errors",
            )
            cluster_summaries.append({key: int(match.group(index + 1)) for index, key in enumerate(keys)})
        elif match := _TB_TIMEOUT_RE.search(line):
            tb_timeout_cycle = int(match.group(1))
    cluster_summaries.sort(key=lambda row: row["cluster"])
    return summary, cluster_summaries, cluster_rows, root_rows, tb_timeout_cycle


def _failure_classification(
    *,
    simulation_status: str,
    returncode: int | None,
    stderr: str,
    tb_timeout_cycle: int | None,
    passed: bool,
) -> str:
    if passed:
        return "passed"
    inconclusive_codes = {124, 125, 137, -9}
    oom = "out of memory" in stderr.lower() or "cannot allocate memory" in stderr.lower()
    if (
        simulation_status in {"subprocess_timeout", "resource_failure", "testbench_timeout"}
        or tb_timeout_cycle is not None
        or returncode in inconclusive_codes
        or oom
    ):
        return "failed_inconclusive"
    return "failed_conclusive"


def _evaluate_observations(
    *,
    reference: dict[str, object],
    summary: dict[str, int],
    cluster_summaries: list[dict[str, int]],
    observed_cluster_rows: list[list[dict[str, object]]],
    observed_root_rows: list[dict[str, object]],
    simulation_status: str = "ok",
    returncode: int | None = 0,
    stderr: str = "",
    tb_timeout_cycle: int | None = None,
) -> JsonDict:
    row_audit = compare_compositional_rows(
        expected_cluster_rows=reference["cluster_rows"],  # type: ignore[arg-type]
        observed_cluster_rows=observed_cluster_rows,
        expected_root_rows=reference["root_rows"],  # type: ignore[arg-type]
        observed_root_rows=observed_root_rows,
    )
    totals_ok = all(summary.get(key) == value for key, value in EXPECTED_TOTALS.items())
    totals_ok = totals_ok and summary.get("command_accept_count") == WAVES
    totals_ok = totals_ok and summary.get("cadence_command_accept_count") == WAVES
    totals_ok = totals_ok and summary.get("protocol_error") == 0
    clusters_ok = len(cluster_summaries) == CLUSTERS
    if clusters_ok:
        for cluster, observed in enumerate(cluster_summaries):
            if observed.get("cluster") != cluster or observed.get("errors") != 0:
                clusters_ok = False
                break
            if any(observed.get(key) != value for key, value in EXPECTED_PER_CLUSTER.items()):
                clusters_ok = False
                break
    passed = (
        simulation_status == "ok"
        and returncode in (None, 0)
        and tb_timeout_cycle is None
        and totals_ok
        and clusters_ok
        and bool(row_audit["passed"])
    )
    classification = _failure_classification(
        simulation_status=simulation_status,
        returncode=returncode,
        stderr=stderr,
        tb_timeout_cycle=tb_timeout_cycle,
        passed=passed,
    )
    return {
        "passed": passed,
        "classification": classification,
        "simulation_status": simulation_status,
        "returncode": returncode,
        "tb_timeout_cycle": tb_timeout_cycle,
        "summary": summary,
        "cluster_summaries": cluster_summaries,
        "counts_passed": totals_ok and clusters_ok,
        "full_row_audit": row_audit,
        "observed_cluster_hashes": [_hash(rows) for rows in observed_cluster_rows],
        "expected_cluster_hashes": list(reference["cluster_hashes"]),
        "observed_root_hash": _hash(observed_root_rows),
        "expected_root_hash": str(reference["root_hash"]),
    }


def build_report(
    *,
    config: JsonDict | None = None,
    output_ready_pattern: tuple[bool, ...] = DEFAULT_ROOT_READY_PATTERN,
    timeout_sec: int = DEFAULT_SUBPROCESS_TIMEOUT_SEC,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
) -> JsonDict:
    resolved_config = json.loads(json.dumps(config if config is not None else build_default_config()))
    body = resolved_config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        raise ValueError(f"config must contain {CONFIG_KEY}")
    cluster_producers = tuple(int(value) for value in body.get("cluster_producers", ()))
    if cluster_producers != CLUSTER_PRODUCERS:
        raise ValueError("probe requires exactly eight p54 clusters followed by eight p53 clusters")
    reference = _reference()
    simulation_status = "ok"
    returncode: int | None = 0
    stdout = ""
    stderr = ""
    sidecars: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="score32_exact_full_cluster_sram_probe_") as temp_name:
        temp_dir = Path(temp_name)
        rtl_dir = temp_dir / "rtl"
        generate(resolved_config, rtl_dir)
        sidecars = _write_memh_sidecars(temp_dir)
        tb_path = temp_dir / "tb.v"
        tb_path.write_text(
            _testbench(
                top_name=str(resolved_config["top_name"]),
                output_ready_pattern=tuple(bool(value) for value in output_ready_pattern),
            ),
            encoding="ascii",
        )
        fakeram_path = temp_dir / "fakeram45_2048x39.v"
        fakeram_path.write_text(full_probe._FAKERAM_MODEL, encoding="ascii")
        sim_path = temp_dir / "sim.out"
        try:
            compile_result = subprocess.run(
                [
                    _tool("iverilog"),
                    "-g2012",
                    "-s",
                    "tb",
                    "-o",
                    str(sim_path),
                    str(rtl_dir / "top.v"),
                    str(fakeram_path),
                    str(tb_path),
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=int(timeout_sec),
            )
            if compile_result.returncode:
                simulation_status = "compile_failed"
                returncode = compile_result.returncode
                stderr = compile_result.stderr
            else:
                run_result = subprocess.run(
                    [_tool("vvp"), str(sim_path)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=int(timeout_sec),
                )
                stdout = run_result.stdout
                stderr = run_result.stderr
                returncode = run_result.returncode
                if run_result.returncode:
                    simulation_status = "run_failed"
        except subprocess.TimeoutExpired as exc:
            simulation_status = "subprocess_timeout"
            returncode = 124
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        except (MemoryError, OSError, RuntimeError) as exc:
            simulation_status = "resource_failure"
            returncode = 137 if isinstance(exc, MemoryError) else 125
            stderr = str(exc)
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")

    summary, cluster_summaries, cluster_rows, root_rows, tb_timeout_cycle = _parse_stdout(stdout)
    effective_status = "testbench_timeout" if tb_timeout_cycle is not None else simulation_status
    report = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=root_rows,
        simulation_status=effective_status,
        returncode=returncode,
        stderr=stderr,
        tb_timeout_cycle=tb_timeout_cycle,
    )
    report.update(
        {
            "clusters": CLUSTERS,
            "cluster_producers": list(CLUSTER_PRODUCERS),
            "total_local_producers": TOTAL_PRODUCERS,
            "logical_head_groups": 1,
            "head_base": HEAD_BASE,
            "command_id": COMMAND_ID,
            "seed": SEED,
            "persistent_waves": WAVES,
            "root_ready_pattern": [int(value) for value in output_ready_pattern],
            "tb_timeout_cycles": TB_TIMEOUT_CYCLES,
            "subprocess_timeout_sec": int(timeout_sec),
            "expected_counts": expected_counts(),
            "memh_sidecars": sidecars,
            "service_model": exact_local16_global_tree_cluster_sram_gqa8_service_manifest(
                cluster_producers=CLUSTER_PRODUCERS
            ),
        }
    )
    linkage = dict(resolved_config.get("report_links") or {})
    if proposal_id:
        linkage["proposal_id"] = proposal_id
    if proposal_path:
        linkage["proposal_path"] = proposal_path
    if linkage:
        report["source_links"] = linkage
    return report


def _render_text(report: JsonDict) -> str:
    summary = dict(report.get("summary") or {})
    return "\n".join(
        [
            "# attention_score32_exact_local16_global_tree_cluster_sram_gqa8_probe",
            "",
            f"- passed: `{report['passed']}`",
            f"- classification: `{report['classification']}`",
            f"- simulation_status: `{report['simulation_status']}`",
            f"- producer_handshakes: `{summary.get('producer_handshake_count', 0)}`",
            f"- fill_targets: `{summary.get('fill_target_accept_count', 0)}`",
            f"- fill_rows: `{summary.get('fill_row_accept_count', 0)}`",
            f"- sram_requests: `{summary.get('sram_request_accept_count', 0)}`",
            f"- sram_responses: `{summary.get('sram_response_accept_count', 0)}`",
            f"- cluster_rows: `{summary.get('cluster_row_count', 0)}`",
            f"- root_rows: `{summary.get('root_row_count', 0)}`",
            f"- observed_root_hash: `{report['observed_root_hash']}`",
            f"- expected_root_hash: `{report['expected_root_hash']}`",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--root-ready-pattern", type=str, default="1,1,0,1")
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_SUBPROCESS_TIMEOUT_SEC)
    parser.add_argument("--proposal-id", type=str)
    parser.add_argument("--proposal-path", type=str)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    config = build_default_config() if args.config is None else json.loads(args.config.read_text(encoding="utf-8"))
    ready_pattern = tuple(value.strip() == "1" for value in args.root_ready_pattern.split(",") if value.strip())
    report = build_report(
        config=config,
        output_ready_pattern=ready_pattern or DEFAULT_ROOT_READY_PATTERN,
        timeout_sec=args.timeout_sec,
        proposal_id=str(args.proposal_id or "").strip() or None,
        proposal_path=str(args.proposal_path or "").strip() or None,
    )
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else _render_text(report))
    return 0 if report["passed"] else 1


__all__ = [
    "DEFAULT_ROOT_READY_PATTERN",
    "DEFAULT_SUBPROCESS_TIMEOUT_SEC",
    "EXPECTED_PER_CLUSTER",
    "EXPECTED_TOTALS",
    "TB_TIMEOUT_CYCLES",
    "build_report",
    "compare_compositional_rows",
    "compare_full_rows",
    "expected_counts",
    "expected_schedule_prefix",
]


if __name__ == "__main__":
    raise SystemExit(main())
