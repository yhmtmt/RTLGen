#!/usr/bin/env python3
"""Probe the exact-partial reduction tree with ordered banked root finalizers."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate as generate_tree
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    exact_banked_finalized_tree_service_manifest,
    finalize_partial_beats,
    finalizer_accept_interval_cycles,
    finalizer_cycles_per_beat,
    merge_balanced_partial_streams,
    pack_numerators,
    partial_stream_from_blocks,
    simulate_exact_banked_finalizer,
    unpack_final_values,
)

JsonDict = dict[str, Any]

_ROOT_RE = re.compile(
    r"ROOT_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_LEAF_RE = re.compile(r"LEAF_SUMMARY leaf=(\d+) accepted=(\d+) issued=(\d+)")
_NODE_RE = re.compile(r"NODE_SUMMARY stage=(\d+) node=(\d+) count=(\d+) error=(\d+)")
_STAGE_RE = re.compile(r"STAGE_SUMMARY stage=(\d+) count=(\d+) error=(\d+)")
_FINALIZER_RE = re.compile(
    r"FINALIZER_SUMMARY accepted=(\d+) completed=(\d+) protocol_error=(\d+) tree_root_completed=(\d+) tree_protocol_error=(\d+) order_protocol_error=(\d+) fifo_high_watermark=(\d+) dispatch_stall=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) dut_cycle=(\d+) tb_cycle=(\d+) first=(\d+) last=(\d+) protocol_error=(\d+) root_completed=(\d+)"
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


def _commands(heads: int) -> tuple[dict[str, int], ...]:
    head_count = int(heads)
    if head_count < 1 or head_count > 32:
        raise ValueError("heads must be in [1, 32]")
    return tuple({"command_id": 0x5A00 + head_index, "head_id": head_index} for head_index in range(head_count))


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _score_rows(leaf: int, command_index: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            ((leaf * 43 + command_index * 29 + block * 17 + lane * 11) % 255) - 127 + (14 if lane == block else 0)
            for lane in range(8)
        )
        for block in range(3)
    )


def _value_blocks(leaf: int, command_index: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    ((leaf * 59 + command_index * 31 + block * 23 + value_slice * 13 + row * 7 + lane * 5) % 255)
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block in range(3)
    )


def _leaf_stream(leaf: int, *, heads: int) -> tuple[ExactPartialBeat, ...]:
    beats: list[ExactPartialBeat] = []
    for command_index, command in enumerate(_commands(heads)):
        beats.extend(
            partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=_score_rows(leaf, command_index),
                value_blocks=_value_blocks(leaf, command_index),
            )
        )
    return tuple(beats)


def _shape(clusters: int) -> list[list[int]]:
    level_sizes: list[list[int]] = []
    next_index = 0
    width = clusters // 2
    while width:
        level_sizes.append(list(range(next_index, next_index + width)))
        next_index += width
        width //= 2
    return level_sizes


def _default_ready_pattern() -> tuple[bool, ...]:
    return tuple(((cycle % 5) != 2) and (((cycle + 3) % 11) != 7) for cycle in range(64))


def _expected(
    clusters: int,
    *,
    heads: int,
    divider_lanes: int,
    finalizer_banks: int,
    output_ready_pattern: tuple[bool, ...],
) -> dict[str, object]:
    leaves = [_leaf_stream(leaf, heads=heads) for leaf in range(clusters)]
    merged = merge_balanced_partial_streams(leaves)
    finalized = finalize_partial_beats(merged)
    root_rows = [
        {
            "command_id": beat.command_id,
            "head_id": beat.head_id,
            "slice": beat.slice_index,
            "last": beat.last,
            "value": list(beat.values),
        }
        for beat in finalized
    ]
    levels = _shape(clusters)
    total_results = len(root_rows)
    leaf_rows = [
        [
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in leaf
        ]
        for leaf in leaves
    ]
    finalizer_reference = simulate_exact_banked_finalizer(
        merged,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
        output_ready_pattern=output_ready_pattern,
    )
    return {
        "heads": heads,
        "leaves": leaf_rows,
        "root": root_rows,
        "leaf_hash": _hash(leaf_rows),
        "root_hash": _hash(root_rows),
        "leaf_accept_count": [total_results] * clusters,
        "node_completed_count": [total_results] * (clusters - 1),
        "stage_completed_count": [len(level) * total_results for level in levels],
        "node_protocol_error": [False] * (clusters - 1),
        "stage_protocol_error": [False] * len(levels),
        "banked_finalizer_reference": finalizer_reference,
    }


def _config(clusters: int, divider_lanes: int, finalizer_banks: int) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_banked_finalized_tree_c{clusters}_r2_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_banked_finalized_tree": {
            "clusters": clusters,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


def _ready_mem_init(pattern: tuple[bool, ...]) -> str:
    return "\n".join(
        f"    root_ready_mem[{index}] = 1'b{1 if ready else 0};" for index, ready in enumerate(pattern)
    )


def _saturated_drive_blocks(clusters: int) -> tuple[str, str]:
    combinational_lines = []
    sequential_lines = []
    for leaf in range(clusters):
        combinational_lines.extend(
            [
                f"      if (leaf_issue[{leaf}] < TOTAL_RESULTS) begin",
                f"        leaf_valid[{leaf}] = 1'b1;",
                f"        leaf_command_id[({leaf} * 16) +: 16] = leaf_cmd_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_head_id[({leaf} * 5) +: 5] = leaf_head_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_global_max[({leaf} * 32) +: 32] = leaf_max_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_exp_sum[({leaf} * 33) +: 33] = leaf_sum_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_slice[({leaf} * 4) +: 4] = leaf_slice_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_last[{leaf}] = leaf_last_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_value[({leaf} * 328) +: 328] = leaf_value_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                "      end",
            ]
        )
        sequential_lines.extend(
            [
                f"      if (leaf_valid[{leaf}] && leaf_ready[{leaf}]) begin",
                f"        leaf_accept_count[{leaf}] <= leaf_accept_count[{leaf}] + 1;",
                f"        leaf_issue[{leaf}] <= leaf_issue[{leaf}] + 1;",
                "      end",
            ]
        )
    return "\n".join(combinational_lines), "\n".join(sequential_lines)


def _skewed_drive_blocks(clusters: int) -> tuple[str, str]:
    combinational_lines = []
    sequential_lines = []
    for leaf in range(clusters):
        combinational_lines.extend(
            [
                f"      if (leaf_pending[{leaf}]) begin",
                f"        leaf_valid[{leaf}] = 1'b1;",
                f"        leaf_command_id[({leaf} * 16) +: 16] = leaf_cmd_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_head_id[({leaf} * 5) +: 5] = leaf_head_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_global_max[({leaf} * 32) +: 32] = leaf_max_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_exp_sum[({leaf} * 33) +: 33] = leaf_sum_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_slice[({leaf} * 4) +: 4] = leaf_slice_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_last[{leaf}] = leaf_last_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                f"        leaf_value[({leaf} * 328) +: 328] = leaf_value_mem[({leaf} * TOTAL_RESULTS) + leaf_issue[{leaf}]];",
                "      end",
            ]
        )
        sequential_lines.extend(
            [
                f"      if (!leaf_pending[{leaf}] && leaf_issue[{leaf}] < TOTAL_RESULTS) begin",
                f"        if ((((cycle + {leaf * 3}) % (3 + ({leaf} % 5))) != 0) && (((cycle + leaf_issue[{leaf}] + {leaf}) % 7) != 1)) begin",
                f"          leaf_pending[{leaf}] <= 1'b1;",
                "        end",
                "      end",
                f"      if (leaf_pending[{leaf}] && leaf_ready[{leaf}]) begin",
                f"        leaf_pending[{leaf}] <= 1'b0;",
                f"        leaf_accept_count[{leaf}] <= leaf_accept_count[{leaf}] + 1;",
                f"        leaf_issue[{leaf}] <= leaf_issue[{leaf}] + 1;",
                "      end",
            ]
        )
    return "\n".join(combinational_lines), "\n".join(sequential_lines)


def _testbench(
    *,
    top_name: str,
    clusters: int,
    heads: int,
    divider_lanes: int,
    finalizer_banks: int,
    expected: dict[str, object],
    saturated: bool,
    output_ready_pattern: tuple[bool, ...],
) -> str:
    leaf_rows = expected["leaves"]
    total_results = len(expected["root"])
    mem_depth = clusters * total_results
    leaf_init: list[str] = []
    for leaf in range(clusters):
        rows = leaf_rows[leaf]
        for beat_index, beat in enumerate(rows):
            flat_index = (leaf * total_results) + beat_index
            leaf_init.append(
                f"    leaf_cmd_mem[{flat_index}] = 16'h{int(beat['command_id']):04x}; "
                f"leaf_head_mem[{flat_index}] = 5'd{int(beat['head_id'])}; "
                f"leaf_max_mem[{flat_index}] = {_signed_literal(int(beat['global_max']), 32)}; "
                f"leaf_sum_mem[{flat_index}] = 33'd{int(beat['exp_sum'])}; "
                f"leaf_slice_mem[{flat_index}] = 4'd{int(beat['slice'])}; "
                f"leaf_last_mem[{flat_index}] = 1'b{1 if beat['last'] else 0}; "
                f"leaf_value_mem[{flat_index}] = 328'h{pack_numerators(beat['value']):082x};"
            )

    drive_comb, drive_seq = (
        _saturated_drive_blocks(clusters) if saturated else _skewed_drive_blocks(clusters)
    )
    leaf_accept_displays = [
        f'        $display("LEAF_SUMMARY leaf={leaf} accepted=%0d issued=%0d", leaf_accept_count[{leaf}], leaf_issue[{leaf}]);'
        for leaf in range(clusters)
    ]
    node_stage_displays = []
    stage_levels = _shape(clusters)
    for stage, indices in enumerate(stage_levels):
        for node_index in indices:
            node_stage_displays.append(
                f'        $display("NODE_SUMMARY stage={stage} node={node_index} count=%0d error=%0d", '
                f"node_completed_count[{node_index * 32} +: 32], node_protocol_error[{node_index}]);"
            )
    stage_displays = [
        f'        $display("STAGE_SUMMARY stage={stage} count=%0d error=%0d", '
        f"stage_completed_count[{stage * 32} +: 32], stage_protocol_error[{stage}]);"
        for stage in range(len(stage_levels))
    ]
    timeout_cycles = max(
        5000,
        (clusters * total_results * 4) + (total_results * (finalizer_accept_interval_cycles(divider_lanes) + 8)),
    )

    return f"""`timescale 1ns/1ps
module tb;
  localparam integer CLUSTERS = {clusters};
  localparam integer HEADS = {heads};
  localparam integer TOTAL_RESULTS = {total_results};
  localparam integer MEM_DEPTH = {mem_depth};
  localparam integer ROOT_READY_PATTERN_LEN = {len(output_ready_pattern)};
  reg clk = 0, rst_n = 0;
  reg [CLUSTERS-1:0] leaf_valid;
  wire [CLUSTERS-1:0] leaf_ready;
  reg [(CLUSTERS*16)-1:0] leaf_command_id;
  reg [(CLUSTERS*5)-1:0] leaf_head_id;
  reg [(CLUSTERS*32)-1:0] leaf_global_max;
  reg [(CLUSTERS*33)-1:0] leaf_exp_sum;
  reg [(CLUSTERS*4)-1:0] leaf_slice;
  reg [CLUSTERS-1:0] leaf_last;
  reg [(CLUSTERS*328)-1:0] leaf_value;
  wire root_valid;
  reg root_ready;
  reg root_ready_mem [0:ROOT_READY_PATTERN_LEN-1];
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [31:0] cycle_count;
  wire [31:0] root_completed_count;
  wire [31:0] finalizer_accepted_count;
  wire [31:0] tree_root_completed_count;
  wire [31:0] order_fifo_occupancy;
  wire [31:0] order_fifo_high_watermark;
  wire [31:0] order_enqueued_count;
  wire [31:0] order_dequeued_count;
  wire [31:0] dispatch_stall_cycles;
  wire [31:0] dispatch_bank_id;
  wire [31:0] head_bank_id;
  wire [{(clusters - 1) * 32 - 1}:0] node_completed_count;
  wire [{int(math.log2(clusters)) * 32 - 1}:0] stage_completed_count;
  wire [{clusters - 2}:0] node_protocol_error;
  wire [{int(math.log2(clusters)) - 1}:0] stage_protocol_error;
  wire [{finalizer_banks - 1}:0] bank_protocol_error;
  wire [{finalizer_banks - 1}:0] bank_outstanding;
  wire tree_protocol_error;
  wire order_protocol_error;
  wire finalizer_protocol_error;
  wire protocol_error;

  reg [15:0] leaf_cmd_mem [0:MEM_DEPTH-1];
  reg [4:0] leaf_head_mem [0:MEM_DEPTH-1];
  reg signed [31:0] leaf_max_mem [0:MEM_DEPTH-1];
  reg [32:0] leaf_sum_mem [0:MEM_DEPTH-1];
  reg [3:0] leaf_slice_mem [0:MEM_DEPTH-1];
  reg leaf_last_mem [0:MEM_DEPTH-1];
  reg [327:0] leaf_value_mem [0:MEM_DEPTH-1];
  reg leaf_pending [0:CLUSTERS-1];
  reg [31:0] leaf_issue [0:CLUSTERS-1];
  reg [31:0] leaf_accept_count [0:CLUSTERS-1];
  integer init_index;
  integer cycle = 0;
  integer root_seen = 0;
  integer first_output_cycle = -1;
  integer last_output_cycle = -1;
  reg pending_summary = 0;
  integer leaf_index;

  always #5 clk = ~clk;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid),
      .leaf_ready(leaf_ready),
      .leaf_command_id(leaf_command_id),
      .leaf_head_id(leaf_head_id),
      .leaf_global_max(leaf_global_max),
      .leaf_exp_sum(leaf_exp_sum),
      .leaf_slice(leaf_slice),
      .leaf_last(leaf_last),
      .leaf_value(leaf_value),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(cycle_count),
      .root_completed_count(root_completed_count),
      .finalizer_accepted_count(finalizer_accepted_count),
      .tree_root_completed_count(tree_root_completed_count),
      .order_fifo_occupancy(order_fifo_occupancy),
      .order_fifo_high_watermark(order_fifo_high_watermark),
      .order_enqueued_count(order_enqueued_count),
      .order_dequeued_count(order_dequeued_count),
      .dispatch_stall_cycles(dispatch_stall_cycles),
      .dispatch_bank_id(dispatch_bank_id),
      .head_bank_id(head_bank_id),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .bank_protocol_error(bank_protocol_error),
      .bank_outstanding(bank_outstanding),
      .tree_protocol_error(tree_protocol_error),
      .order_protocol_error(order_protocol_error),
      .finalizer_protocol_error(finalizer_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    leaf_valid = {{CLUSTERS{{1'b0}}}};
    leaf_command_id = {{(CLUSTERS*16){{1'b0}}}};
    leaf_head_id = {{(CLUSTERS*5){{1'b0}}}};
    leaf_global_max = {{(CLUSTERS*32){{1'b0}}}};
    leaf_exp_sum = {{(CLUSTERS*33){{1'b0}}}};
    leaf_slice = {{(CLUSTERS*4){{1'b0}}}};
    leaf_last = {{CLUSTERS{{1'b0}}}};
    leaf_value = {{(CLUSTERS*328){{1'b0}}}};
    root_ready = root_ready_mem[cycle % ROOT_READY_PATTERN_LEN];
{drive_comb}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      root_seen <= 0;
      first_output_cycle <= -1;
      last_output_cycle <= -1;
      pending_summary <= 1'b0;
      for (leaf_index = 0; leaf_index < CLUSTERS; leaf_index = leaf_index + 1) begin
        leaf_pending[leaf_index] <= 1'b0;
        leaf_issue[leaf_index] <= 32'd0;
        leaf_accept_count[leaf_index] <= 32'd0;
      end
    end else begin
      cycle <= cycle + 1;
{drive_seq}
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        if (first_output_cycle < 0) first_output_cycle <= cycle;
        last_output_cycle <= cycle;
        root_seen <= root_seen + 1;
        if (root_seen + 1 == TOTAL_RESULTS) pending_summary <= 1'b1;
      end
      if (pending_summary) begin
{chr(10).join(leaf_accept_displays)}
{chr(10).join(node_stage_displays)}
{chr(10).join(stage_displays)}
        $display("FINALIZER_SUMMARY accepted=%0d completed=%0d protocol_error=%0d tree_root_completed=%0d tree_protocol_error=%0d order_protocol_error=%0d fifo_high_watermark=%0d dispatch_stall=%0d",
                 finalizer_accepted_count, root_completed_count, finalizer_protocol_error, tree_root_completed_count, tree_protocol_error, order_protocol_error, order_fifo_high_watermark, dispatch_stall_cycles);
        $display("SUMMARY outputs=%0d dut_cycle=%0d tb_cycle=%0d first=%0d last=%0d protocol_error=%0d root_completed=%0d",
                 root_seen, cycle_count, cycle, first_output_cycle, last_output_cycle, protocol_error, root_completed_count);
        #1 $finish;
      end
      if (cycle > {timeout_cycles}) $fatal(1, "timeout");
    end
  end

  initial begin
    for (init_index = 0; init_index < MEM_DEPTH; init_index = init_index + 1) begin
      leaf_cmd_mem[init_index] = 16'd0;
      leaf_head_mem[init_index] = 5'd0;
      leaf_max_mem[init_index] = 32'sd0;
      leaf_sum_mem[init_index] = 33'd0;
      leaf_slice_mem[init_index] = 4'd0;
      leaf_last_mem[init_index] = 1'b0;
      leaf_value_mem[init_index] = 328'd0;
    end
{_ready_mem_init(output_ready_pattern)}
{chr(10).join(leaf_init)}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def build_report(
    clusters: int = 16,
    heads: int = 32,
    divider_lanes: int = 8,
    finalizer_banks: int = 59,
    *,
    saturated: bool = False,
    output_ready_pattern: tuple[bool, ...] | None = None,
) -> JsonDict:
    ready_pattern = output_ready_pattern or _default_ready_pattern()
    expected = _expected(
        clusters,
        heads=heads,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
        output_ready_pattern=ready_pattern,
    )
    with tempfile.TemporaryDirectory(
        prefix=f"score32_exact_banked_finalized_tree_c{clusters}_l{divider_lanes}_b{finalizer_banks}_"
    ) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate_tree(_config(clusters, divider_lanes, finalizer_banks), temp_dir / "rtl")
        tb_path = temp_dir / "tb.sv"
        top_name = str(_config(clusters, divider_lanes, finalizer_banks)["top_name"])
        tb_path.write_text(
            _testbench(
                top_name=top_name,
                clusters=clusters,
                heads=heads,
                divider_lanes=divider_lanes,
                finalizer_banks=finalizer_banks,
                expected=expected,
                saturated=saturated,
                output_ready_pattern=ready_pattern,
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

    observed_root: list[dict[str, object]] = []
    leaf_summary: list[int] = [0] * clusters
    node_count = clusters - 1
    stage_count = int(math.log2(clusters))
    node_completed_count: list[int] = [0] * node_count
    node_protocol_error: list[bool] = [False] * node_count
    stage_completed_count: list[int] = [0] * stage_count
    stage_protocol_error: list[bool] = [False] * stage_count
    finalizer_summary: dict[str, object] | None = None
    summary: dict[str, object] | None = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _ROOT_RE.fullmatch(stripped):
            observed_root.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "value": list(unpack_final_values(int(match.group(5), 16))),
                    "cycle": int(match.group(6)),
                }
            )
        elif match := _LEAF_RE.fullmatch(stripped):
            leaf = int(match.group(1))
            leaf_summary[leaf] = int(match.group(2))
            if int(match.group(3)) != int(match.group(2)):
                raise RuntimeError(f"leaf issue/accept mismatch in leaf {leaf}: {stripped}")
        elif match := _NODE_RE.fullmatch(stripped):
            node = int(match.group(2))
            node_completed_count[node] = int(match.group(3))
            node_protocol_error[node] = bool(int(match.group(4)))
        elif match := _STAGE_RE.fullmatch(stripped):
            stage = int(match.group(1))
            stage_completed_count[stage] = int(match.group(2))
            stage_protocol_error[stage] = bool(int(match.group(3)))
        elif match := _FINALIZER_RE.fullmatch(stripped):
            finalizer_summary = {
                "accepted": int(match.group(1)),
                "completed": int(match.group(2)),
                "finalizer_protocol_error": bool(int(match.group(3))),
                "tree_root_completed": int(match.group(4)),
                "tree_protocol_error": bool(int(match.group(5))),
                "order_protocol_error": bool(int(match.group(6))),
                "fifo_high_watermark": int(match.group(7)),
                "dispatch_stall_cycles": int(match.group(8)),
            }
        elif match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "dut_cycle": int(match.group(2)),
                "tb_cycle": int(match.group(3)),
                "first_output_cycle": int(match.group(4)),
                "last_output_cycle": int(match.group(5)),
                "protocol_error": bool(int(match.group(6))),
                "root_completed_count": int(match.group(7)),
            }
    if summary is None or finalizer_summary is None:
        raise RuntimeError("summary missing from banked finalized tree probe")

    observed_rows = [{key: value for key, value in row.items() if key != "cycle"} for row in observed_root]
    root_hash = _hash(observed_rows)
    expected_hash = str(expected["root_hash"])
    first_output_cycle = int(summary["first_output_cycle"])
    last_output_cycle = int(summary["last_output_cycle"])
    output_interval_cycles = max(0, last_output_cycle - first_output_cycle)
    interval_beats = max(0, int(summary["outputs"]) - 1)
    measured_workload_manifest = exact_banked_finalized_tree_service_manifest(
        clusters=clusters,
        heads=heads,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
    )
    measured_workload_manifest.update(
        {
            "measured_heads": heads,
            "leaf_accepts_per_leaf": len(expected["root"]),
            "total_leaf_beats": clusters * len(expected["root"]),
            "root_outputs": len(expected["root"]),
            "first_output_cycle": first_output_cycle,
            "last_output_cycle": last_output_cycle,
            "drain_cycles": int(summary["tb_cycle"]),
            "measured_root_output_interval_beats": interval_beats,
            "measured_root_output_interval_cycles": output_interval_cycles,
            "measured_root_output_interval_beats_per_cycle": (
                round(interval_beats / output_interval_cycles, 6) if output_interval_cycles else 0.0
            ),
            "measured_root_output_interval_cycles_per_beat": (
                round(output_interval_cycles / interval_beats, 6) if interval_beats else 0.0
            ),
            "protocol_error": bool(summary["protocol_error"]),
            "saturated_leaf_mode": bool(saturated),
            "root_ready_pattern_length": len(ready_pattern),
        }
    )
    passed = (
        observed_rows == expected["root"]
        and leaf_summary == expected["leaf_accept_count"]
        and node_completed_count == expected["node_completed_count"]
        and stage_completed_count == expected["stage_completed_count"]
        and node_protocol_error == expected["node_protocol_error"]
        and stage_protocol_error == expected["stage_protocol_error"]
        and bool(summary["protocol_error"]) is False
        and bool(finalizer_summary["finalizer_protocol_error"]) is False
        and bool(finalizer_summary["tree_protocol_error"]) is False
        and bool(finalizer_summary["order_protocol_error"]) is False
        and int(summary["outputs"]) == len(expected["root"])
        and int(summary["root_completed_count"]) == len(expected["root"])
        and int(finalizer_summary["accepted"]) == len(expected["root"])
        and int(finalizer_summary["tree_root_completed"]) == len(expected["root"])
        and root_hash == expected_hash
    )
    return {
        "clusters": clusters,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
        "heads": heads,
        "saturated": saturated,
        "passed": passed,
        "expected_root_hash": expected_hash,
        "observed_root_hash": root_hash,
        "outputs": len(observed_rows),
        "first_output_cycle": first_output_cycle,
        "last_output_cycle": last_output_cycle,
        "drain_cycles": int(summary["tb_cycle"]),
        "dut_cycle": int(summary["dut_cycle"]),
        "leaf_accept_count": leaf_summary,
        "node_completed_count": node_completed_count,
        "node_protocol_error": node_protocol_error,
        "stage_completed_count": stage_completed_count,
        "stage_protocol_error": stage_protocol_error,
        "finalizer_accepted_count": int(finalizer_summary["accepted"]),
        "finalizer_completed_count": int(finalizer_summary["completed"]),
        "tree_root_completed_count": int(finalizer_summary["tree_root_completed"]),
        "tree_protocol_error": bool(finalizer_summary["tree_protocol_error"]),
        "order_protocol_error": bool(finalizer_summary["order_protocol_error"]),
        "finalizer_protocol_error": bool(finalizer_summary["finalizer_protocol_error"]),
        "protocol_error": bool(summary["protocol_error"]),
        "order_fifo_high_watermark": int(finalizer_summary["fifo_high_watermark"]),
        "dispatch_stall_cycles": int(finalizer_summary["dispatch_stall_cycles"]),
        "measured_workload_manifest": measured_workload_manifest,
        "theoretical_full_llama_service_manifest": exact_banked_finalized_tree_service_manifest(
            clusters=clusters,
            heads=32,
            divider_lanes=divider_lanes,
            finalizer_banks=finalizer_banks,
        ),
        "banked_finalizer_reference": expected["banked_finalizer_reference"],
        "ideal_divider_cycles_per_beat": finalizer_cycles_per_beat(divider_lanes),
        "per_bank_accept_interval_cycles": finalizer_accept_interval_cycles(divider_lanes),
        "observed_rows": observed_rows,
    }


def _pattern_from_bits(bits: str) -> tuple[bool, ...]:
    cleaned = bits.strip()
    if not cleaned or any(ch not in {"0", "1"} for ch in cleaned):
        raise ValueError("root_ready_pattern must be a non-empty bit string")
    return tuple(ch == "1" for ch in cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clusters", type=int, default=16)
    parser.add_argument("--heads", type=int, default=32)
    parser.add_argument("--divider-lanes", type=int, default=8)
    parser.add_argument("--finalizer-banks", type=int, default=59)
    parser.add_argument("--saturated", action="store_true")
    parser.add_argument("--root-ready-pattern", type=str, default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ready_pattern = _pattern_from_bits(args.root_ready_pattern) if args.root_ready_pattern else None
    report = build_report(
        clusters=args.clusters,
        heads=args.heads,
        divider_lanes=args.divider_lanes,
        finalizer_banks=args.finalizer_banks,
        saturated=args.saturated,
        output_ready_pattern=ready_pattern,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "clusters": report["clusters"],
                    "divider_lanes": report["divider_lanes"],
                    "finalizer_banks": report["finalizer_banks"],
                    "heads": report["heads"],
                    "saturated": report["saturated"],
                    "passed": report["passed"],
                    "outputs": report["outputs"],
                    "first_output_cycle": report["first_output_cycle"],
                    "last_output_cycle": report["last_output_cycle"],
                    "drain_cycles": report["drain_cycles"],
                    "observed_root_hash": report["observed_root_hash"],
                },
                sort_keys=True,
            )
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
