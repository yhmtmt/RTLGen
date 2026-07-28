#!/usr/bin/env python3
"""Probe the GQA8-banked local temporal exact-partial reducer against a structured reference."""

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

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_PAYLOAD_BITS,
    exact_local_temporal_reducer_gqa8_service_manifest,
    pack_numerators,
    partial_stream_from_blocks,
    reduce_local_temporal_partial_waves,
    unpack_numerators,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_local_temporal_reducer_gqa8"
_RESULT_RE = re.compile(
    r"RESULT idx=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) protocol_error=(\d+) group_error=(\d+) local_tree_error=(\d+) temporal_error=(\d+) "
    r"local_root_completed=(\d+) temporal_completed=(\d+) emitted=(\d+) commands=(\d+) local_stall=(\d+) output_stall=(\d+)"
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _git_head() -> str:
    return (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _default_config(producers: int = 53) -> JsonDict:
    return {
        "top_name": f"attention_score32_exact_local_temporal_reducer_gqa8_p{producers}_w8",
        _CONFIG_KEY: {
            "producers": producers,
            "value_slices": 16,
            "head_id_bits": 5,
            "persistent_waves": 8,
        },
        "probe_defaults": {
            "heads": 16,
            "command_count": 2,
            "head_bases": [0, 8],
            "seed": 23,
        },
        "report_links": {
            "proposal_id": "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1",
            "proposal_path": (
                "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json"
            ),
        },
    }


def _resolve_workload(
    config: JsonDict,
    *,
    heads: int | None,
    command_count: int | None,
    seed: int | None,
    head_bases: tuple[int, ...] | None = None,
) -> dict[str, object]:
    defaults = config.get("probe_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    resolved_heads = int(heads if heads is not None else defaults.get("heads", 16))
    resolved_command_count = int(command_count if command_count is not None else defaults.get("command_count", 2))
    resolved_seed = int(seed if seed is not None else defaults.get("seed", 23))
    configured_head_bases = head_bases
    if configured_head_bases is None and isinstance(defaults.get("head_bases"), list):
        configured_head_bases = tuple(int(value) for value in defaults["head_bases"])

    if resolved_heads < 8 or resolved_heads > 32 or (resolved_heads % 8):
        raise ValueError("heads must be a multiple of 8 in [8, 32]")
    if resolved_command_count < 1:
        raise ValueError("command_count must be positive")
    if configured_head_bases is None:
        head_groups = tuple(group * 8 for group in range(resolved_heads // 8))
        configured_head_bases = tuple(head_groups[index % len(head_groups)] for index in range(resolved_command_count))
    if len(configured_head_bases) != resolved_command_count:
        raise ValueError("head_bases length must match command_count")
    for base in configured_head_bases:
        if base < 0 or base > (resolved_heads - 8) or (base % 8):
            raise ValueError("head_bases entries must be aligned 8-head group bases within the configured heads")
    return {
        "heads": resolved_heads,
        "command_count": resolved_command_count,
        "head_bases": tuple(configured_head_bases),
        "seed": resolved_seed,
    }


def _command_schedule(*, command_count: int, head_bases: tuple[int, ...]) -> tuple[dict[str, int], ...]:
    return tuple({"command_id": 0x7B00 + index, "head_base": int(head_bases[index])} for index in range(command_count))


def _block_count(producer: int, command_index: int, wave: int, head_lane: int, seed: int) -> int:
    return 1 + ((seed + producer * 5 + command_index * 7 + wave * 11 + head_lane * 13) % 3)


def _score_rows(
    producer: int,
    command_index: int,
    wave: int,
    head_lane: int,
    seed: int,
    blocks: int,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            ((seed * 19 + producer * 29 + command_index * 23 + wave * 17 + head_lane * 13 + block * 11 + lane * 7) % 255)
            - 127
            for lane in range(8)
        )
        for block in range(blocks)
    )


def _value_blocks(
    producer: int,
    command_index: int,
    wave: int,
    head_lane: int,
    seed: int,
    blocks: int,
) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    (
                        (
                            seed * 31
                            + producer * 37
                            + command_index * 23
                            + wave * 19
                            + head_lane * 17
                            + block * 13
                            + value_slice * 11
                            + row * 7
                            + lane * 5
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
        for block in range(blocks)
    )


def _producer_wave_stream(
    *,
    producer: int,
    command_index: int,
    command_id: int,
    head_base: int,
    wave: int,
    seed: int,
) -> tuple[object, ...]:
    stream = []
    for head_lane in range(8):
        blocks = _block_count(producer, command_index, wave, head_lane, seed)
        stream.extend(
            partial_stream_from_blocks(
                command_id=command_id,
                head_id=head_base + head_lane,
                score_rows=_score_rows(producer, command_index, wave, head_lane, seed, blocks),
                value_blocks=_value_blocks(producer, command_index, wave, head_lane, seed, blocks),
            )
        )
    return tuple(stream)


def _leaf_rows(producers: int, workload: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    commands = _command_schedule(
        command_count=int(workload["command_count"]),
        head_bases=tuple(int(value) for value in workload["head_bases"]),
    )
    leaf_rows: list[list[dict[str, object]]] = [[] for _ in range(producers)]
    expected_rows: list[dict[str, object]] = []
    for command_index, command in enumerate(commands):
        waves = []
        for wave in range(LOCAL_TEMPORAL_WAVES):
            producer_streams = []
            for producer in range(producers):
                stream = _producer_wave_stream(
                    producer=producer,
                    command_index=command_index,
                    command_id=int(command["command_id"]),
                    head_base=int(command["head_base"]),
                    wave=wave,
                    seed=int(workload["seed"]),
                )
                producer_streams.append(stream)
                leaf_rows[producer].extend(
                    {
                        "command_id": beat.command_id,
                        "head_id": beat.head_id,
                        "slice": beat.slice_index,
                        "last": beat.last,
                        "global_max": beat.max_score,
                        "exp_sum": beat.exp_sum,
                        "value": list(beat.numerators),
                    }
                    for beat in stream
                )
            waves.append(tuple(producer_streams))
        expected_rows.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in reduce_local_temporal_partial_waves(tuple(waves))
        )
    flattened_leaf_rows = [row for producer_rows in leaf_rows for row in producer_rows]
    return flattened_leaf_rows, expected_rows


def _ready_pattern(stress_interfaces: bool, output_ready_pattern: tuple[bool, ...] | None, seed: int) -> tuple[bool, ...]:
    if output_ready_pattern is not None:
        return tuple(bool(value) for value in output_ready_pattern)
    if not stress_interfaces:
        return (True,)
    return tuple((((seed + index * 5) % 11) not in {2, 7}) for index in range(23))


def _pack_leaf_word(row: dict[str, object]) -> int:
    return (
        ((int(row["command_id"]) & 0xFFFF) << 403)
        | ((int(row["head_id"]) & 0x1F) << 398)
        | ((int(row["global_max"]) & ((1 << 32) - 1)) << 366)
        | ((int(row["exp_sum"]) & ((1 << 33) - 1)) << 333)
        | ((int(row["slice"]) & 0xF) << 329)
        | ((1 if row["last"] else 0) << 328)
        | pack_numerators(row["value"])
    )


def _write_leaf_mem(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(f"{_pack_leaf_word(row):0105x}\n" for row in rows), encoding="utf-8")


def _pack_bool_pattern(values: tuple[bool, ...]) -> str:
    return "\n".join(f"    result_ready_mem[{index}] = 1'b{1 if value else 0};" for index, value in enumerate(values))


def _testbench(
    *,
    top_name: str,
    producers: int,
    command_count: int,
    leaf_rows: list[dict[str, object]],
    output_ready_pattern: tuple[bool, ...],
    stress_interfaces: bool,
    seed: int,
    leaf_mem_path: Path,
) -> str:
    total_leaf_beats = len(leaf_rows) // producers
    total_results = command_count * 8 * 16
    launch_gate = (
        "1'b1"
        if not stress_interfaces
        else f"((((cycle + leaf_index * 3 + leaf_issue[leaf_index] + {seed}) % 9) != 2) && "
        f"(((cycle + leaf_index + {seed}) % 13) != 5))"
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam integer TOTAL_LEAF_BEATS = {total_leaf_beats};
  localparam integer TOTAL_RESULTS = {total_results};
  localparam integer MEM_DEPTH = {len(leaf_rows)};
  localparam integer READY_PATTERN_LEN = {len(output_ready_pattern)};

  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer seen = 0;
  reg pending_summary = 0;

  reg [PRODUCERS-1:0] leaf_valid;
  wire [PRODUCERS-1:0] leaf_ready;
  reg [(PRODUCERS*16)-1:0] leaf_command_id;
  reg [(PRODUCERS*5)-1:0] leaf_head_id;
  reg [(PRODUCERS*32)-1:0] leaf_global_max;
  reg [(PRODUCERS*33)-1:0] leaf_exp_sum;
  reg [(PRODUCERS*4)-1:0] leaf_slice;
  reg [PRODUCERS-1:0] leaf_last;
  reg [(PRODUCERS*328)-1:0] leaf_value;
  wire out_valid;
  reg out_ready;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire out_last;
  wire [327:0] out_value;
  wire [2:0] active_wave_index;
  wire emitting;
  wire [4:0] active_head_base;
  wire [6:0] collect_beat_index;
  wire [6:0] emit_beat_index;
  wire [31:0] cycle_count;
  wire [31:0] local_root_completed_count;
  wire [31:0] temporal_merge_completed_count;
  wire [31:0] emitted_beat_count;
  wire [31:0] completed_command_count;
  wire [31:0] local_stall_cycles;
  wire [31:0] output_stall_cycles;
  wire group_contract_error;
  wire local_tree_protocol_error;
  wire temporal_merge_protocol_error;
  wire protocol_error;

  reg [418:0] leaf_mem [0:MEM_DEPTH-1];
  reg result_ready_mem [0:READY_PATTERN_LEN-1];
  reg [418:0] leaf_word;
  reg [31:0] leaf_issue [0:PRODUCERS-1];
  reg leaf_pending [0:PRODUCERS-1];
  integer leaf_index;
  integer init_index;

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
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_command_id(out_command_id),
      .out_head_id(out_head_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .active_wave_index(active_wave_index),
      .emitting(emitting),
      .active_head_base(active_head_base),
      .collect_beat_index(collect_beat_index),
      .emit_beat_index(emit_beat_index),
      .cycle_count(cycle_count),
      .local_root_completed_count(local_root_completed_count),
      .temporal_merge_completed_count(temporal_merge_completed_count),
      .emitted_beat_count(emitted_beat_count),
      .completed_command_count(completed_command_count),
      .local_stall_cycles(local_stall_cycles),
      .output_stall_cycles(output_stall_cycles),
      .group_contract_error(group_contract_error),
      .local_tree_protocol_error(local_tree_protocol_error),
      .temporal_merge_protocol_error(temporal_merge_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    leaf_valid = {{PRODUCERS{{1'b0}}}};
    leaf_command_id = {{(PRODUCERS*16){{1'b0}}}};
    leaf_head_id = {{(PRODUCERS*5){{1'b0}}}};
    leaf_global_max = {{(PRODUCERS*32){{1'b0}}}};
    leaf_exp_sum = {{(PRODUCERS*33){{1'b0}}}};
    leaf_slice = {{(PRODUCERS*4){{1'b0}}}};
    leaf_last = {{PRODUCERS{{1'b0}}}};
    leaf_value = {{(PRODUCERS*328){{1'b0}}}};
    leaf_word = 419'd0;
    out_ready = result_ready_mem[cycle % READY_PATTERN_LEN];
    for (leaf_index = 0; leaf_index < PRODUCERS; leaf_index = leaf_index + 1) begin
      if (rst_n && leaf_pending[leaf_index]) begin
        leaf_valid[leaf_index] = 1'b1;
        leaf_word = leaf_mem[(leaf_index * TOTAL_LEAF_BEATS) + leaf_issue[leaf_index]];
        leaf_command_id[(leaf_index * 16) +: 16] = leaf_word[418 -: 16];
        leaf_head_id[(leaf_index * 5) +: 5] = leaf_word[402 -: 5];
        leaf_global_max[(leaf_index * 32) +: 32] = leaf_word[397 -: 32];
        leaf_exp_sum[(leaf_index * 33) +: 33] = leaf_word[365 -: 33];
        leaf_slice[(leaf_index * 4) +: 4] = leaf_word[332 -: 4];
        leaf_last[leaf_index] = leaf_word[328];
        leaf_value[(leaf_index * 328) +: 328] = leaf_word[327:0];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      seen <= 0;
      pending_summary <= 1'b0;
      for (leaf_index = 0; leaf_index < PRODUCERS; leaf_index = leaf_index + 1) begin
        leaf_issue[leaf_index] <= 0;
        leaf_pending[leaf_index] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      for (leaf_index = 0; leaf_index < PRODUCERS; leaf_index = leaf_index + 1) begin
        if (!leaf_pending[leaf_index] && (leaf_issue[leaf_index] < TOTAL_LEAF_BEATS) && {launch_gate}) begin
          leaf_pending[leaf_index] <= 1'b1;
        end
        if (leaf_pending[leaf_index] && leaf_ready[leaf_index]) begin
          leaf_pending[leaf_index] <= 1'b0;
          leaf_issue[leaf_index] <= leaf_issue[leaf_index] + 1;
        end
      end
      if (out_valid && out_ready) begin
        $display(
          "RESULT idx=%0d cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",
          seen, out_command_id, out_head_id, out_slice, out_last, $signed(out_global_max), out_exp_sum, out_value, cycle_count
        );
        seen <= seen + 1;
        if (seen + 1 == TOTAL_RESULTS) begin
          pending_summary <= 1'b1;
        end
      end
      if (pending_summary) begin
        $display(
          "SUMMARY outputs=%0d drain=%0d protocol_error=%0d group_error=%0d local_tree_error=%0d temporal_error=%0d local_root_completed=%0d temporal_completed=%0d emitted=%0d commands=%0d local_stall=%0d output_stall=%0d",
          seen,
          cycle_count,
          protocol_error,
          group_contract_error,
          local_tree_protocol_error,
          temporal_merge_protocol_error,
          local_root_completed_count,
          temporal_merge_completed_count,
          emitted_beat_count,
          completed_command_count,
          local_stall_cycles,
          output_stall_cycles
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
    $readmemh("{leaf_mem_path.as_posix()}", leaf_mem);
{_pack_bool_pattern(output_ready_pattern)}
    for (init_index = 0; init_index < PRODUCERS; init_index = init_index + 1) begin
      leaf_issue[init_index] = 0;
      leaf_pending[init_index] = 0;
    end
    clk = 0;
    rst_n = 0;
    #25 rst_n = 1;
  end
endmodule
"""


def build_report(
    config: JsonDict | None = None,
    *,
    heads: int | None = None,
    command_count: int | None = None,
    seed: int | None = None,
    head_bases: tuple[int, ...] | None = None,
    stress_interfaces: bool = False,
    output_ready_pattern: tuple[bool, ...] | None = None,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
    depends_on_item_ids: list[str] | None = None,
) -> JsonDict:
    payload = json.loads(json.dumps(config or _default_config()))
    body = payload.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise ValueError(f"config must contain {_CONFIG_KEY}")
    producers = int(body.get("producers", 53))
    workload = _resolve_workload(payload, heads=heads, command_count=command_count, seed=seed, head_bases=head_bases)
    leaf_rows, expected_rows = _leaf_rows(producers, workload)
    ready_pattern = _ready_pattern(stress_interfaces, output_ready_pattern, int(workload["seed"]))

    with tempfile.TemporaryDirectory(prefix="score32_exact_local_temporal_gqa8_probe_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        rtl_dir = temp_dir / "rtl"
        tb_path = temp_dir / "tb.sv"
        leaf_mem_path = temp_dir / "leaf_mem.hex"
        generate(payload, rtl_dir)
        _write_leaf_mem(leaf_mem_path, leaf_rows)
        tb_path.write_text(
            _testbench(
                top_name=str(payload["top_name"]),
                producers=producers,
                command_count=int(workload["command_count"]),
                leaf_rows=leaf_rows,
                output_ready_pattern=ready_pattern,
                stress_interfaces=stress_interfaces,
                seed=int(workload["seed"]),
                leaf_mem_path=leaf_mem_path,
            ),
            encoding="utf-8",
        )
        simv = temp_dir / "simv"
        subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-o",
                str(simv),
                str(rtl_dir / "top.v"),
                str(tb_path),
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        run = subprocess.run(
            [_tool("vvp"), str(simv)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    observed_rows = []
    summary = None
    for line in run.stdout.splitlines():
        result_match = _RESULT_RE.fullmatch(line.strip())
        if result_match is not None:
            observed_rows.append(
                {
                    "index": int(result_match.group(1)),
                    "command_id": int(result_match.group(2)),
                    "head_id": int(result_match.group(3)),
                    "slice": int(result_match.group(4)),
                    "last": bool(int(result_match.group(5))),
                    "global_max": int(result_match.group(6)),
                    "exp_sum": int(result_match.group(7)),
                    "value": list(unpack_numerators(int(result_match.group(8), 16))),
                    "cycle": int(result_match.group(9)),
                }
            )
            continue
        summary_match = _SUMMARY_RE.fullmatch(line.strip())
        if summary_match is not None:
            summary = {
                "outputs": int(summary_match.group(1)),
                "drain_cycles": int(summary_match.group(2)),
                "protocol_error": bool(int(summary_match.group(3))),
                "group_contract_error": bool(int(summary_match.group(4))),
                "local_tree_protocol_error": bool(int(summary_match.group(5))),
                "temporal_merge_protocol_error": bool(int(summary_match.group(6))),
                "local_root_completed_count": int(summary_match.group(7)),
                "temporal_merge_completed_count": int(summary_match.group(8)),
                "emitted_beat_count": int(summary_match.group(9)),
                "completed_command_count": int(summary_match.group(10)),
                "local_stall_cycles": int(summary_match.group(11)),
                "output_stall_cycles": int(summary_match.group(12)),
            }
    if summary is None:
        raise RuntimeError(f"missing summary in simulator output:\n{run.stdout}")

    normalized_observed_rows = [
        {key: row[key] for key in ("command_id", "head_id", "slice", "last", "global_max", "exp_sum", "value")}
        for row in observed_rows
    ]
    per_group_local_roots = LOCAL_TEMPORAL_WAVES * 8 * 16
    per_group_temporal_merges = (LOCAL_TEMPORAL_WAVES - 1) * 8 * 16
    per_group_outputs = 8 * 16
    passed = (
        normalized_observed_rows == expected_rows
        and summary["outputs"] == len(expected_rows)
        and summary["emitted_beat_count"] == len(expected_rows)
        and summary["completed_command_count"] == int(workload["command_count"])
        and summary["local_root_completed_count"] == int(workload["command_count"]) * per_group_local_roots
        and summary["temporal_merge_completed_count"] == int(workload["command_count"]) * per_group_temporal_merges
        and not summary["protocol_error"]
        and not summary["group_contract_error"]
        and not summary["local_tree_protocol_error"]
        and not summary["temporal_merge_protocol_error"]
    )

    report: JsonDict = {
        "version": 1,
        "model": "attention_score32_exact_local_temporal_reducer_gqa8_probe_v1",
        "passed": passed,
        "interface_mode": "stress" if stress_interfaces else "ideal",
        "input_stream_contract": "gqa8_head_major_slice_minor_wave_serialized_compatible_with_existing_dual_stream_producer",
        "producers": producers,
        "commands": int(workload["command_count"]),
        "heads": int(workload["heads"]),
        "head_bases": list(int(value) for value in workload["head_bases"]),
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "expected_outputs": len(expected_rows),
        "outputs": summary["outputs"],
        "drain_cycles": summary["drain_cycles"],
        "local_root_completed_count": summary["local_root_completed_count"],
        "temporal_merge_completed_count": summary["temporal_merge_completed_count"],
        "emitted_beat_count": summary["emitted_beat_count"],
        "completed_command_count": summary["completed_command_count"],
        "local_stall_cycles": summary["local_stall_cycles"],
        "output_stall_cycles": summary["output_stall_cycles"],
        "protocol_error": summary["protocol_error"],
        "group_contract_error": summary["group_contract_error"],
        "local_tree_protocol_error": summary["local_tree_protocol_error"],
        "temporal_merge_protocol_error": summary["temporal_merge_protocol_error"],
        "ready_pattern_period": len(ready_pattern),
        "per_group_counts": {
            "local_roots": per_group_local_roots,
            "temporal_merges": per_group_temporal_merges,
            "outputs": per_group_outputs,
        },
        "expected_rows": expected_rows,
        "observed_rows": normalized_observed_rows,
        "observed_cycles": [row["cycle"] for row in observed_rows],
        "service_model": exact_local_temporal_reducer_gqa8_service_manifest(
            producers=producers,
            waves=LOCAL_TEMPORAL_WAVES,
            head_groups=len({int(value) for value in workload["head_bases"]}),
        ),
        "source_identities": {
            "repo_commit": _git_head(),
            "files": [
                {
                    "path": rel,
                    "sha256": _sha256_file(REPO_ROOT / rel),
                }
                for rel in (
                    "npu/rtlgen/gen_attention_score32_exact_local_reducer.py",
                    "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8.py",
                    "npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py",
                    "npu/sim/perf/attention_exact_partial.py",
                )
            ],
            "expected_rows_hash": _hash(expected_rows),
            "observed_rows_hash": _hash(normalized_observed_rows),
        },
    }
    linkage = dict(payload.get("report_links") or {})
    if proposal_id:
        linkage["proposal_id"] = str(proposal_id)
    if proposal_path:
        linkage["proposal_path"] = str(proposal_path)
    depends = [str(item).strip() for item in (depends_on_item_ids or []) if str(item).strip()]
    if depends:
        linkage["depends_on_item_ids"] = depends
    if linkage:
        report["source_links"] = linkage
    return report


def _build_markdown(report: JsonDict) -> str:
    lines = [
        "# Score32 Exact Local Temporal Reducer GQA8 Probe",
        "",
        f"- passed: `{report['passed']}`",
        f"- interface_mode: `{report['interface_mode']}`",
        f"- repo_commit: `{report['source_identities']['repo_commit']}`",
        f"- producers: `{report['producers']}`",
        f"- commands: `{report['commands']}`",
        f"- heads: `{report['heads']}`",
        f"- head_bases: `{report['head_bases']}`",
        f"- persistent_waves: `{report['persistent_waves']}`",
        f"- outputs: `{report['outputs']}` / `{report['expected_outputs']}`",
        f"- drain_cycles: `{report['drain_cycles']}`",
        f"- local_root_completed_count: `{report['local_root_completed_count']}`",
        f"- temporal_merge_completed_count: `{report['temporal_merge_completed_count']}`",
        f"- emitted_beat_count: `{report['emitted_beat_count']}`",
        f"- completed_command_count: `{report['completed_command_count']}`",
        f"- local_stall_cycles: `{report['local_stall_cycles']}`",
        f"- output_stall_cycles: `{report['output_stall_cycles']}`",
        f"- protocol_error: `{report['protocol_error']}`",
        f"- group_contract_error: `{report['group_contract_error']}`",
        f"- local_tree_protocol_error: `{report['local_tree_protocol_error']}`",
        f"- temporal_merge_protocol_error: `{report['temporal_merge_protocol_error']}`",
    ]
    linkage = dict(report.get("source_links") or {})
    if linkage.get("proposal_id"):
        lines.append(f"- proposal_id: `{linkage['proposal_id']}`")
    if linkage.get("proposal_path"):
        lines.append(f"- proposal_path: `{linkage['proposal_path']}`")
    depends = linkage.get("depends_on_item_ids")
    if isinstance(depends, list) and depends:
        lines.append(f"- depends_on_item_ids: `{', '.join(str(item) for item in depends)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--heads", type=int)
    parser.add_argument("--command-count", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--head-base", action="append", default=[])
    parser.add_argument("--stress-interfaces", action="store_true")
    parser.add_argument("--proposal-id")
    parser.add_argument("--proposal-path")
    parser.add_argument("--depends-on-item-id", action="append", default=[])
    args = parser.parse_args()

    config = None
    if args.config is not None:
        config_payload = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(config_payload, dict):
            raise SystemExit("config must decode to a JSON object")
        config = config_payload
    head_bases = tuple(int(value) for value in args.head_base) if args.head_base else None
    report = build_report(
        config,
        heads=args.heads,
        command_count=args.command_count,
        seed=args.seed,
        head_bases=head_bases,
        stress_interfaces=bool(args.stress_interfaces),
        proposal_id=str(args.proposal_id or "").strip() or None,
        proposal_path=str(args.proposal_path or "").strip() or None,
        depends_on_item_ids=[str(item).strip() for item in args.depends_on_item_id if str(item).strip()],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
