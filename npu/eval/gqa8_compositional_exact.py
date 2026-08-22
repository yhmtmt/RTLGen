#!/usr/bin/env python3
"""Bounded concrete-RTL component simulations for the composed GQA8 probe."""

from __future__ import annotations

import contextlib
from concurrent.futures import ThreadPoolExecutor
import io
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from npu.eval.check_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_guard import (
    main as strict_guard_main,
)
from npu.sim.perf.attention_exact_partial import (
    PARTIAL_PAYLOAD_BITS,
    WEIGHTED_NUMERATOR_BITS,
    pack_numerators,
)

JsonDict = dict[str, Any]

BACKEND = "compositional_icarus"
CLUSTER_RUN_JOBS = 3
GLOBAL_VALUE_OFFSET = 91
GLOBAL_ROW_BITS = GLOBAL_VALUE_OFFSET + PARTIAL_PAYLOAD_BITS
_GLOBAL_SUMMARY_RE = re.compile(
    r"GLOBAL_SUMMARY root_rows=(\d+) root_completed=(\d+) finalizer_accepted=(\d+) "
    r"tree_completed=(\d+) protocol_error=(\d+) first_root=(-?\d+) last_root=(-?\d+) drain=(\d+)"
)
_MODULE_RE = re.compile(r"(?ms)^module\s+([A-Za-z_][A-Za-z0-9_$]*)\b.*?^endmodule\s*$")


def extract_module_family(rtl: str, *, prefix: str) -> str:
    modules = [match.group(0) for match in _MODULE_RE.finditer(rtl) if match.group(1).startswith(prefix)]
    if not modules or not any(re.match(rf"module\s+{re.escape(prefix)}\b", module) for module in modules):
        raise ValueError(f"generated RTL has no complete module family for {prefix}")
    return "\n\n".join(modules) + "\n"


def _cluster_driver_data(*, cluster: int, logical_head_groups: int) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    producers = probe.CLUSTER_PRODUCERS[cluster]
    wave_commands = probe._wave_commands(logical_head_groups=logical_head_groups)
    query_streams: list[list[int]] = [[] for _ in range(producers)]
    key_streams: list[list[int]] = [[] for _ in range(producers)]
    last_streams: list[list[int]] = [[] for _ in range(producers)]
    beat_limits = [[0 for _ in range(producers)] for _ in wave_commands]
    max_beats = 0
    for producer in range(producers):
        cursor = 0
        for command_index, command in enumerate(wave_commands):
            block_count = probe.exact_local_cluster_gqa8_command_block_counts(
                producers=producers,
                group_index=int(command["group_index"]),
            )[producer]
            blocks = [
                probe.full_probe._stream_block_beats(
                    cluster=cluster,
                    producer=producer,
                    group_index=int(command["group_index"]),
                    wave_index=int(command["wave_index"]),
                    stream=stream,
                    block_count=block_count,
                    seed=probe.SEED,
                )
                for stream in range(probe.STREAMS)
            ]
            for block in range(block_count):
                for dimension in range(probe.HEAD_DIM):
                    queries0, keys0 = blocks[0][block][dimension]
                    queries1, keys1 = blocks[1][block][dimension]
                    query_streams[producer].append(
                        probe.full_probe._pack(list(queries0), 8)
                        | (probe.full_probe._pack(list(queries1), 8) << 64)
                    )
                    key_streams[producer].append(
                        probe.full_probe._pack(list(keys0), 8)
                        | (probe.full_probe._pack(list(keys1), 8) << 64)
                    )
                    last_streams[producer].append(int(dimension + 1 == probe.HEAD_DIM))
                    cursor += 1
            beat_limits[command_index][producer] = cursor
        max_beats = max(max_beats, cursor)
    query_words = [0] * (producers * max_beats)
    key_words = [0] * (producers * max_beats)
    last_words = [0] * (producers * max_beats)
    for producer in range(producers):
        for beat_index, query in enumerate(query_streams[producer]):
            flat = producer * max_beats + beat_index
            query_words[flat] = query
            key_words[flat] = key_streams[producer][beat_index]
            last_words[flat] = last_streams[producer][beat_index]
    return {
        "wave_commands": wave_commands,
        "query_words": query_words,
        "key_words": key_words,
        "last_words": last_words,
        "beat_limits": beat_limits,
        "max_beats_per_producer": max_beats,
    }


def _write_cluster_sidecars(directory: Path, *, cluster: int, logical_head_groups: int) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    data = _cluster_driver_data(cluster=cluster, logical_head_groups=logical_head_groups)
    probe._write_memh(directory / "query.memh", data["query_words"], width_bits=128)
    probe._write_memh(directory / "key.memh", data["key_words"], width_bits=128)
    probe._write_memh(directory / "last.memh", data["last_words"], width_bits=1)
    fill_words = [
        value
        for command in data["wave_commands"]
        for value in probe._fill_rows_for_wave(
            cluster=cluster,
            head_base=int(command["head_base"]),
            wave=int(command["wave_index"]),
        )
    ]
    probe._write_memh(directory / "fill.memh", fill_words, width_bits=512)
    return {
        "query_words": len(data["query_words"]),
        "key_words": len(data["key_words"]),
        "last_words": len(data["last_words"]),
        "fill_words": len(fill_words),
        "max_beats_per_producer": int(data["max_beats_per_producer"]),
    }


def _command_initializers(*, logical_head_groups: int) -> tuple[str, str]:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    commands = probe._wave_commands(logical_head_groups=logical_head_groups)
    command_lines = []
    for index, command in enumerate(commands):
        command_lines.append(
            f"    command_id_mem[{index}] = 16'h{int(command['command_id']):04x}; "
            f"head_base_mem[{index}] = 5'd{int(command['head_base'])}; "
            f"multiplier_mem[{index}] = 32'd{int(command['multiplier'])}; "
            f"shift_mem[{index}] = 6'd{int(command['shift'])}; "
            f"wave_index_mem[{index}] = 3'd{int(command['wave_index'])};"
        )
    return "\n".join(command_lines), str(len(commands))


def cluster_testbench(
    *,
    top_name: str,
    producers: int,
    logical_head_groups: int,
    output_ready_pattern: tuple[bool, ...] = (True, True, False, True),
) -> str:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    if producers not in (53, 54):
        raise ValueError("component cluster must have 53 or 54 producers")
    command_init, command_count = _command_initializers(logical_head_groups=logical_head_groups)
    representative = 0 if producers == 54 else 8
    data = _cluster_driver_data(cluster=representative, logical_head_groups=logical_head_groups)
    beat_limit_init = "\n".join(
        f"    beat_limit_mem[{command}][{producer}] = 32'd{int(data['beat_limits'][command][producer])};"
        for command in range(int(command_count))
        for producer in range(producers)
    )
    expected_rows = logical_head_groups * probe.EXPECTED_PER_CLUSTER["emitted_beat_count"]
    timeout_cycles = logical_head_groups * probe.TB_TIMEOUT_CYCLES
    if not output_ready_pattern:
        raise ValueError("cluster output ready pattern must not be empty")
    ready_init = "\n".join(
        f"    out_ready_mem[{index}] = 1'b{int(value)};"
        for index, value in enumerate(output_ready_pattern)
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam integer COMMANDS = {command_count};
  localparam integer MAX_BEATS = {int(data["max_beats_per_producer"])};
  localparam integer ROWS_PER_TARGET = {probe.ROWS_PER_BUFFER};
  localparam integer ROWS_PER_STREAM = {probe.ROWS_PER_STREAM};
  localparam integer EXPECTED_ROWS = {expected_rows};
  localparam integer TB_TIMEOUT_CYCLES = {timeout_cycles};
  localparam integer OUT_READY_LEN = {len(output_ready_pattern)};
  reg clk = 0, rst_n = 0;
  integer cluster_id = 0, cycle = 0, issued = 0, active = -1;
  integer fill_command = 0, fill_row = -1, rows_seen = 0, producer_handshakes = 0;
  integer producer, flat_index, command_drive_index, fill_drive_index;
  integer beat_issue [0:PRODUCERS-1];
  reg pending_summary = 0;
  reg [15:0] command_id_mem [0:COMMANDS-1];
  reg [4:0] head_base_mem [0:COMMANDS-1];
  reg [31:0] multiplier_mem [0:COMMANDS-1];
  reg [5:0] shift_mem [0:COMMANDS-1];
  reg [2:0] wave_index_mem [0:COMMANDS-1];
  reg [31:0] beat_limit_mem [0:COMMANDS-1][0:PRODUCERS-1];
  reg [127:0] query_mem [0:(PRODUCERS*MAX_BEATS)-1];
  reg [127:0] key_mem [0:(PRODUCERS*MAX_BEATS)-1];
  reg last_mem [0:(PRODUCERS*MAX_BEATS)-1];
  reg [511:0] fill_mem [0:(COMMANDS*ROWS_PER_TARGET)-1];
  reg out_ready_mem [0:OUT_READY_LEN-1];
  wire preload_complete = fill_command >= ((COMMANDS < 2) ? COMMANDS : 2);
  wire command_valid = rst_n && preload_complete && (issued < COMMANDS);
  wire command_ready, fill_target_ready, fill_ready, out_valid;
  wire [PRODUCERS-1:0] input_ready;
  reg [PRODUCERS-1:0] input_valid, input_last;
  reg signed [(PRODUCERS*128)-1:0] input_query, input_key;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire out_last;
  wire [327:0] out_value;
  wire [31:0] wave_accept, completed, emitted, fill_targets, fill_rows;
  wire [31:0] requests, responses, command_accepts, command_releases;
  wire group_error, local_error, temporal_error, reducer_error, atomic_error;
  wire invalid_metadata_error, invalid_address_error, residency_error, overwrite_error;
  wire command_error, buffer_map_error, release_guard_error, sram_error, protocol_error;
  wire fill_target_valid = rst_n && (fill_command < COMMANDS) && (fill_row < 0)
      && (fill_command <= issued + 1);
  wire fill_valid = rst_n && (fill_command < COMMANDS) && (fill_row >= 0);
  wire [511:0] fill_data = (fill_row >= 0)
      ? fill_mem[fill_drive_index * ROWS_PER_TARGET + fill_row] : '0;
  wire out_ready = out_ready_mem[cycle % OUT_READY_LEN];

  {top_name} dut (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(fill_target_valid), .fill_target_ready(fill_target_ready),
    .fill_target_buffer_sel(wave_index_mem[fill_drive_index][0]),
    .fill_target_command_id(command_id_mem[fill_drive_index]),
    .fill_target_head_base(head_base_mem[fill_drive_index]),
    .fill_target_wave_index(wave_index_mem[fill_drive_index]),
    .fill_valid(fill_valid), .fill_ready(fill_ready),
    .fill_buffer_sel(wave_index_mem[fill_drive_index][0]),
    .fill_stream(fill_row >= ROWS_PER_STREAM),
    .fill_block_slot((fill_row >> 4) & 6'h3f), .fill_slice(fill_row & 4'hf), .fill_data(fill_data),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_id(command_id_mem[command_drive_index]), .command_head_base(head_base_mem[command_drive_index]),
    .command_wave_index(wave_index_mem[command_drive_index]),
    .command_score_multiplier(multiplier_mem[command_drive_index]),
    .command_score_shift(shift_mem[command_drive_index]),
    .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
    .input_query(input_query), .input_key(input_key),
    .out_valid(out_valid), .out_ready(out_ready), .out_command_id(out_command_id),
    .out_head_id(out_head_id), .out_global_max(out_global_max), .out_exp_sum(out_exp_sum),
    .out_slice(out_slice), .out_last(out_last), .out_value(out_value),
    .wave_command_accept_count(wave_accept), .reducer_completed_command_count(completed),
    .reducer_emitted_beat_count(emitted),
    .group_contract_error(group_error), .local_tree_protocol_error(local_error),
    .temporal_merge_protocol_error(temporal_error), .reducer_protocol_error(reducer_error),
    .atomic_command_protocol_error(atomic_error),
    .sram_fill_target_accept_count(fill_targets), .sram_fill_row_accept_count(fill_rows),
    .sram_request_accept_count(requests), .sram_response_accept_count(responses),
    .sram_command_accept_count(command_accepts), .sram_command_release_count(command_releases),
    .sram_invalid_metadata_error(invalid_metadata_error),
    .sram_invalid_address_error(invalid_address_error), .sram_residency_error(residency_error),
    .sram_overwrite_error(overwrite_error), .sram_command_error(command_error),
    .sram_buffer_map_error(buffer_map_error), .sram_release_guard_error(release_guard_error),
    .sram_protocol_error(sram_error), .protocol_error(protocol_error)
  );
  always #5 clk = ~clk;
  always @* begin
    command_drive_index = (issued < COMMANDS) ? issued : COMMANDS-1;
    fill_drive_index = (fill_command < COMMANDS) ? fill_command : COMMANDS-1;
    input_valid = '0; input_last = '0; input_query = '0; input_key = '0;
    for (producer = 0; producer < PRODUCERS; producer = producer + 1) begin
      if (rst_n && active >= 0 && beat_issue[producer] < beat_limit_mem[active][producer]) begin
        flat_index = producer * MAX_BEATS + beat_issue[producer];
        input_valid[producer] = 1'b1; input_last[producer] = last_mem[flat_index];
        input_query[producer*128 +: 128] = query_mem[flat_index];
        input_key[producer*128 +: 128] = key_mem[flat_index];
      end
    end
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0; issued <= 0; active <= -1; fill_command <= 0; fill_row <= -1;
      rows_seen <= 0; producer_handshakes <= 0; pending_summary <= 0;
      for (producer = 0; producer < PRODUCERS; producer = producer + 1) beat_issue[producer] <= 0;
    end else begin
      cycle <= cycle + 1;
      if (fill_target_valid && fill_target_ready) fill_row <= 0;
      if (fill_valid && fill_ready) begin
        if (fill_row == ROWS_PER_TARGET-1) begin fill_command <= fill_command + 1; fill_row <= -1; end
        else fill_row <= fill_row + 1;
      end
      if (command_valid && command_ready) begin active <= issued; issued <= issued + 1; end
      for (producer = 0; producer < PRODUCERS; producer = producer + 1)
        if (input_valid[producer] && input_ready[producer]) beat_issue[producer] <= beat_issue[producer] + 1;
      producer_handshakes <= producer_handshakes + $countones(input_valid & input_ready);
      if (out_valid && out_ready) begin
        $display("CLUSTER_RESULT cluster=%0d cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
                 cluster_id, out_command_id, out_head_id, out_slice, out_last,
                 out_global_max, out_exp_sum, out_value, cycle);
        rows_seen <= rows_seen + 1;
        if (rows_seen + 1 == EXPECTED_ROWS) pending_summary <= 1;
      end
      if (pending_summary) begin
        $display("CLUSTER_SUMMARY cluster=%0d wave_accept=%0d completed=%0d emitted=%0d fill_targets=%0d fill_rows=%0d requests=%0d responses=%0d command_accepts=%0d command_releases=%0d errors=%0d",
                 cluster_id, wave_accept, completed, emitted, fill_targets, fill_rows, requests, responses,
                 command_accepts, command_releases,
                 group_error | local_error | temporal_error | reducer_error | atomic_error |
                 invalid_metadata_error | invalid_address_error | residency_error | overwrite_error |
                 command_error | buffer_map_error | release_guard_error | sram_error | protocol_error);
        $display("CLUSTER_COUNTS cluster=%0d producer_handshakes=%0d", cluster_id, producer_handshakes);
        #1 $finish;
      end
      if (cycle >= TB_TIMEOUT_CYCLES) begin $display("TB_TIMEOUT cycle=%0d", cycle); #1 $finish; end
    end
  end
  initial begin
    if (!$value$plusargs("CLUSTER=%d", cluster_id)) cluster_id = 0;
    $readmemh("query.memh", query_mem); $readmemh("key.memh", key_mem);
    $readmemh("last.memh", last_mem); $readmemh("fill.memh", fill_mem);
{command_init}
{beat_limit_init}
{ready_init}
    repeat (3) @(posedge clk); @(negedge clk); rst_n = 1;
  end
endmodule
"""


def _pack_global_row(row: JsonDict) -> int:
    value = 0
    value |= int(row["command_id"])
    value |= int(row["head_id"]) << 16
    value |= (int(row["global_max"]) & 0xFFFF_FFFF) << 21
    value |= int(row["exp_sum"]) << 53
    value |= int(row["slice"]) << 86
    value |= int(bool(row["last"])) << 90
    value |= pack_numerators(row["value"]) << GLOBAL_VALUE_OFFSET
    return value


def _write_global_sidecar(directory: Path, cluster_rows: list[list[JsonDict]]) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    if len(cluster_rows) != probe.CLUSTERS or len({len(rows) for rows in cluster_rows}) != 1:
        raise ValueError("global composition requires 16 equal-length cluster streams")
    words = [_pack_global_row(row) for rows in cluster_rows for row in rows]
    probe._write_memh(directory / "global_rows.memh", words, width_bits=GLOBAL_ROW_BITS)
    return {
        "global_row_words": len(words),
        "rows_per_cluster": len(cluster_rows[0]),
        "row_bits": GLOBAL_ROW_BITS,
        "value_offset": GLOBAL_VALUE_OFFSET,
        "numerator_lanes": 8,
        "numerator_bits": WEIGHTED_NUMERATOR_BITS,
        "value_packing": "canonical_pack_numerators",
    }


def global_testbench(
    *,
    top_name: str,
    rows_per_cluster: int,
    output_ready_pattern: tuple[bool, ...],
    timeout_cycles: int,
) -> str:
    ready_init = "\n".join(
        f"    ready_mem[{index}] = 1'b{int(value)};" for index, value in enumerate(output_ready_pattern)
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer CLUSTERS=16, ROWS={rows_per_cluster}, READY_LEN={len(output_ready_pattern)};
  localparam integer EXPECTED_ROOT_ROWS={rows_per_cluster}, TB_TIMEOUT_CYCLES={timeout_cycles};
  reg clk=0, rst_n=0; integer cycle=0, root_rows=0, first_root=-1, last_root=-1, leaf;
  integer row_index [0:CLUSTERS-1]; reg pending_summary=0;
  reg [{GLOBAL_ROW_BITS - 1}:0] row_mem [0:(CLUSTERS*ROWS)-1]; reg ready_mem [0:READY_LEN-1];
  reg [15:0] leaf_valid; wire [15:0] leaf_ready; reg [255:0] leaf_command_id;
  reg [79:0] leaf_head_id; reg [511:0] leaf_global_max; reg [527:0] leaf_exp_sum;
  reg [63:0] leaf_slice; reg [15:0] leaf_last; reg [5247:0] leaf_value;
  wire root_valid; wire [15:0] root_command_id; wire [4:0] root_head_id;
  wire [3:0] root_slice; wire root_last; wire [319:0] root_value;
  wire [31:0] root_completed, finalizer_accepted, tree_completed;
  wire tree_error, order_error, finalizer_error, protocol_error;
  wire root_ready = ready_mem[cycle % READY_LEN];
  {top_name} dut (
    .clk(clk), .rst_n(rst_n), .leaf_valid(leaf_valid), .leaf_ready(leaf_ready),
    .leaf_command_id(leaf_command_id), .leaf_head_id(leaf_head_id),
    .leaf_global_max(leaf_global_max), .leaf_exp_sum(leaf_exp_sum),
    .leaf_slice(leaf_slice), .leaf_last(leaf_last), .leaf_value(leaf_value),
    .root_valid(root_valid), .root_ready(root_ready), .root_command_id(root_command_id),
    .root_head_id(root_head_id), .root_slice(root_slice), .root_last(root_last), .root_value(root_value),
    .root_completed_count(root_completed), .finalizer_accepted_count(finalizer_accepted),
    .tree_root_completed_count(tree_completed), .tree_protocol_error(tree_error),
    .order_protocol_error(order_error), .finalizer_protocol_error(finalizer_error),
    .protocol_error(protocol_error)
  );
  always #5 clk=~clk;
  always @* begin
    leaf_valid='0; leaf_command_id='0; leaf_head_id='0; leaf_global_max='0;
    leaf_exp_sum='0; leaf_slice='0; leaf_last='0; leaf_value='0;
    for (leaf=0; leaf<CLUSTERS; leaf=leaf+1) if (row_index[leaf] < ROWS) begin
      leaf_valid[leaf]=1;
      leaf_command_id[leaf*16 +: 16]=row_mem[leaf*ROWS+row_index[leaf]][0 +: 16];
      leaf_head_id[leaf*5 +: 5]=row_mem[leaf*ROWS+row_index[leaf]][16 +: 5];
      leaf_global_max[leaf*32 +: 32]=row_mem[leaf*ROWS+row_index[leaf]][21 +: 32];
      leaf_exp_sum[leaf*33 +: 33]=row_mem[leaf*ROWS+row_index[leaf]][53 +: 33];
      leaf_slice[leaf*4 +: 4]=row_mem[leaf*ROWS+row_index[leaf]][86 +: 4];
      leaf_last[leaf]=row_mem[leaf*ROWS+row_index[leaf]][90];
      leaf_value[leaf*328 +: 328]=row_mem[leaf*ROWS+row_index[leaf]][91 +: 328];
    end
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      cycle<=0; root_rows<=0; first_root<=-1; last_root<=-1; pending_summary<=0;
      for (leaf=0; leaf<CLUSTERS; leaf=leaf+1) row_index[leaf]<=0;
    end else begin
      cycle<=cycle+1;
      for (leaf=0; leaf<CLUSTERS; leaf=leaf+1)
        if (leaf_valid[leaf] && leaf_ready[leaf]) row_index[leaf]<=row_index[leaf]+1;
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        if (first_root<0) first_root<=cycle; last_root<=cycle; root_rows<=root_rows+1;
        if (root_rows+1==EXPECTED_ROOT_ROWS) pending_summary<=1;
      end
      if (pending_summary) begin
        $display("GLOBAL_SUMMARY root_rows=%0d root_completed=%0d finalizer_accepted=%0d tree_completed=%0d protocol_error=%0d first_root=%0d last_root=%0d drain=%0d",
                 root_rows, root_completed, finalizer_accepted, tree_completed,
                 tree_error | order_error | finalizer_error | protocol_error,
                 first_root, last_root, cycle);
        #1 $finish;
      end
      if (cycle>=TB_TIMEOUT_CYCLES) begin $display("TB_TIMEOUT cycle=%0d",cycle); #1 $finish; end
    end
  end
  initial begin
    $readmemh("global_rows.memh",row_mem);
{ready_init}
    repeat(3) @(posedge clk); @(negedge clk); rst_n=1;
  end
endmodule
"""


def _run_process(
    command: list[str],
    *,
    cwd: Path,
    timeout_sec: int,
    phase: str,
) -> tuple[subprocess.CompletedProcess[str] | None, JsonDict | None]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as exc:
        return None, {
            "phase": phase,
            "status": "subprocess_timeout",
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }
    except (MemoryError, OSError, RuntimeError) as exc:
        return None, {
            "phase": phase,
            "status": "resource_failure",
            "returncode": 137 if isinstance(exc, MemoryError) else 125,
            "stdout": "",
            "stderr": str(exc),
        }
    if result.returncode:
        from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

        resource_failure = probe._is_resource_termination(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
        )
        return result, {
            "phase": phase,
            "status": (
                "resource_failure"
                if resource_failure
                else ("compile_failed" if phase.startswith("compile_") else "run_failed")
            ),
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    if "TB_TIMEOUT" in (result.stdout or ""):
        return result, {
            "phase": phase,
            "status": "testbench_timeout",
            "returncode": 124,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    return result, None


def _diagnostic(failure: JsonDict) -> str:
    text = str(failure.get("stderr") or failure.get("stdout") or "")
    return f"phase={failure['phase']} returncode={failure['returncode']}\n{text}".strip()


def run_compositional_exact(
    *,
    config: JsonDict,
    work_dir: Path,
    rtl_dir: Path,
    fakeram_path: Path,
    logical_head_groups: int,
    output_ready_pattern: tuple[bool, ...],
    compile_timeout_sec: int,
    simulation_timeout_sec: int,
) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    top_name = str(config["top_name"])
    modules = probe._hierarchical_module_names(top_name)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            strict_guard_main(["--design-dir", str(work_dir), "--config", str(rtl_dir / "config.json")])
    except SystemExit as exc:
        return {
            "simulation_status": "guard_failed",
            "returncode": 1,
            "stderr": f"phase=strict_generated_top_guard\n{exc}",
            "stdout": "",
            "phase_records": [{"phase": "strict_generated_top_guard", "returncode": 1}],
        }

    compile_dir = work_dir / "component_build"
    compile_dir.mkdir()
    generated_rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    component_rtl_dirs: dict[str, Path] = {}
    for kind in ("p54_cluster", "p53_cluster", "global_tree"):
        component_rtl_dir = compile_dir / f"{kind}_rtl"
        component_rtl_dir.mkdir()
        family = extract_module_family(generated_rtl, prefix=modules[kind])
        (component_rtl_dir / "top.v").write_text(family, encoding="utf-8")
        component_rtl_dirs[kind] = component_rtl_dir
    binaries: dict[str, Path] = {}
    phase_records: list[JsonDict] = [{"phase": "strict_generated_top_guard", "returncode": 0}]
    for kind, producers in (("p54_cluster", 54), ("p53_cluster", 53)):
        tb_path = compile_dir / f"{kind}_tb.v"
        sim_path = compile_dir / f"{kind}.out"
        tb_path.write_text(
            cluster_testbench(
                top_name=modules[kind],
                producers=producers,
                logical_head_groups=logical_head_groups,
                output_ready_pattern=output_ready_pattern,
            ),
            encoding="ascii",
        )
        command = probe._icarus_compile_command(
            rtl_dir=component_rtl_dirs[kind],
            fakeram_path=fakeram_path,
            tb_path=tb_path,
            sim_path=sim_path,
        )
        result, failure = _run_process(
            command,
            cwd=compile_dir,
            timeout_sec=compile_timeout_sec,
            phase=f"compile_{kind}",
        )
        phase_records.append(
            {"phase": f"compile_{kind}", "returncode": failure["returncode"] if failure else 0}
        )
        if failure:
            return {
                "simulation_status": failure["status"],
                "returncode": failure["returncode"],
                "stderr": _diagnostic(failure),
                "stdout": str(failure.get("stdout") or ""),
                "phase_records": phase_records,
            }
        binaries[kind] = sim_path

    cluster_stdout: list[str] = []
    cluster_sidecars: list[JsonDict] = []
    observed_cluster_rows: list[list[JsonDict]] = [[] for _ in range(probe.CLUSTERS)]
    cluster_summaries: list[JsonDict] = []
    producer_handshakes = 0

    def run_cluster(
        cluster: int,
    ) -> tuple[int, JsonDict, subprocess.CompletedProcess[str] | None, JsonDict | None]:
        producers = probe.CLUSTER_PRODUCERS[cluster]
        run_dir = work_dir / f"cluster_{cluster:02d}"
        run_dir.mkdir()
        try:
            sidecar = _write_cluster_sidecars(
                run_dir,
                cluster=cluster,
                logical_head_groups=logical_head_groups,
            )
            kind = "p54_cluster" if producers == 54 else "p53_cluster"
            result, failure = _run_process(
                [probe._tool("vvp"), str(binaries[kind]), f"+CLUSTER={cluster}"],
                cwd=run_dir,
                timeout_sec=simulation_timeout_sec,
                phase=f"run_cluster_{cluster}",
            )
            return cluster, sidecar, result, failure
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    try:
        with ThreadPoolExecutor(max_workers=CLUSTER_RUN_JOBS) as executor:
            cluster_results = list(executor.map(run_cluster, range(probe.CLUSTERS)))
    except (MemoryError, OSError, RuntimeError, ValueError) as exc:
        resource_failure = isinstance(exc, (MemoryError, OSError))
        return {
            "simulation_status": "resource_failure" if resource_failure else "run_failed",
            "returncode": 137 if isinstance(exc, MemoryError) else (125 if resource_failure else 1),
            "stderr": f"phase=prepare_or_run_clusters\n{exc}",
            "stdout": "",
            "phase_records": phase_records,
        }
    for cluster, sidecar, result, failure in cluster_results:
        cluster_sidecars.append(sidecar)
        phase_records.append(
            {"phase": f"run_cluster_{cluster}", "returncode": failure["returncode"] if failure else 0}
        )
        if failure:
            return {
                "simulation_status": failure["status"],
                "returncode": failure["returncode"],
                "stderr": _diagnostic(failure),
                "stdout": str(failure.get("stdout") or ""),
                "phase_records": phase_records,
            }
        stdout = result.stdout or ""
        cluster_stdout.append(stdout)
        _, parsed_summaries, parsed_rows, _, timeout_cycle = probe._parse_stdout(stdout)
        if timeout_cycle is not None or len(parsed_summaries) != 1:
            return {
                "simulation_status": "testbench_timeout" if timeout_cycle is not None else "run_failed",
                "returncode": 124 if timeout_cycle is not None else 1,
                "stderr": f"phase=run_cluster_{cluster}: missing unique cluster summary",
                "stdout": stdout,
                "phase_records": phase_records,
            }
        observed_cluster_rows[cluster] = parsed_rows[cluster]
        cluster_summaries.extend(parsed_summaries)
        match = re.search(r"CLUSTER_COUNTS cluster=\d+ producer_handshakes=(\d+)", stdout)
        if not match:
            return {
                "simulation_status": "run_failed",
                "returncode": 1,
                "stderr": f"phase=run_cluster_{cluster}: missing producer handshake count",
                "stdout": stdout,
                "phase_records": phase_records,
            }
        producer_handshakes += int(match.group(1))

    global_dir = work_dir / "global"
    global_dir.mkdir()
    global_sidecar = _write_global_sidecar(global_dir, observed_cluster_rows)
    global_tb = compile_dir / "global_tb.v"
    global_sim = compile_dir / "global.out"
    global_tb.write_text(
        global_testbench(
            top_name=modules["global_tree"],
            rows_per_cluster=int(global_sidecar["rows_per_cluster"]),
            output_ready_pattern=output_ready_pattern,
            timeout_cycles=logical_head_groups * probe.TB_TIMEOUT_CYCLES,
        ),
        encoding="ascii",
    )
    result, failure = _run_process(
        probe._icarus_compile_command(
            rtl_dir=component_rtl_dirs["global_tree"],
            fakeram_path=fakeram_path,
            tb_path=global_tb,
            sim_path=global_sim,
        ),
        cwd=compile_dir,
        timeout_sec=compile_timeout_sec,
        phase="compile_global_tree",
    )
    phase_records.append(
        {"phase": "compile_global_tree", "returncode": failure["returncode"] if failure else 0}
    )
    if failure:
        return {
            "simulation_status": failure["status"],
            "returncode": failure["returncode"],
            "stderr": _diagnostic(failure),
            "stdout": str(failure.get("stdout") or ""),
            "phase_records": phase_records,
        }
    result, failure = _run_process(
        [probe._tool("vvp"), str(global_sim)],
        cwd=global_dir,
        timeout_sec=simulation_timeout_sec,
        phase="run_global_tree",
    )
    phase_records.append(
        {"phase": "run_global_tree", "returncode": failure["returncode"] if failure else 0}
    )
    if failure:
        return {
            "simulation_status": failure["status"],
            "returncode": failure["returncode"],
            "stderr": _diagnostic(failure),
            "stdout": str(failure.get("stdout") or ""),
            "phase_records": phase_records,
        }
    global_stdout = result.stdout or ""
    global_match = _GLOBAL_SUMMARY_RE.search(global_stdout)
    if not global_match:
        return {
            "simulation_status": "run_failed",
            "returncode": 1,
            "stderr": "phase=run_global_tree: missing global summary",
            "stdout": global_stdout,
            "phase_records": phase_records,
        }
    root_rows, root_completed, finalizer_accepted, tree_completed, global_error, first_root, last_root, drain = (
        int(value) for value in global_match.groups()
    )
    totals = {
        key: sum(int(summary[key]) for summary in cluster_summaries)
        for key in (
            "fill_target_accept_count",
            "fill_row_accept_count",
            "request_accept_count",
            "response_accept_count",
            "emitted_beat_count",
        )
    }
    global_count_error = int(
        root_completed != root_rows
        or finalizer_accepted != root_rows
        or tree_completed != root_rows
    )
    protocol_error = (
        global_error
        | global_count_error
        | int(any(int(summary["errors"]) for summary in cluster_summaries))
    )
    wave_commands = logical_head_groups * probe.WAVES
    synthetic_summary = (
        f"SUMMARY producer_handshakes={producer_handshakes} fill_targets={totals['fill_target_accept_count']} "
        f"fill_rows={totals['fill_row_accept_count']} sram_requests={totals['request_accept_count']} "
        f"sram_responses={totals['response_accept_count']} cluster_rows={totals['emitted_beat_count']} "
        f"root_rows={root_rows} command_accepts={wave_commands} cadence_accepts={wave_commands} "
        f"protocol_error={protocol_error} first_root={first_root} last_root={last_root} drain={drain}"
    )
    return {
        "simulation_status": "ok",
        "returncode": 0,
        "stderr": "",
        "stdout": "\n".join(cluster_stdout + [global_stdout, synthetic_summary]),
        "phase_records": phase_records,
        "component_metadata": {
            "proof": "concrete_rtl_composition",
            "strict_generated_top_guard": "passed",
            "compiled_cluster_variants": {"p54": 1, "p53": 1},
            "cluster_replays": 16,
            "cluster_run_jobs": CLUSTER_RUN_JOBS,
            "global_tree_simulations": 1,
            "cluster_sidecars": cluster_sidecars,
            "global_sidecar": global_sidecar,
            "global_counts": {
                "root_completed_count": root_completed,
                "finalizer_accepted_count": finalizer_accepted,
                "tree_root_completed_count": tree_completed,
                "counts_passed": not bool(global_count_error),
            },
        },
    }
