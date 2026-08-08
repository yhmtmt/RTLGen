#!/usr/bin/env python3
"""Prove bounded RTL-to-affine workload correspondence for finalized c1."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import probe_attention_decode_score_multivalue_integrated_service as service_probe
from npu.eval import probe_attention_decode_score_multivalue_service_finalized_cdc as finalized_probe
from npu.rtlgen.gen_attention_decode_score_multivalue_service_finalized_cdc import generate
from npu.sim.perf.attention_exact_partial import (
    ExactPartialWindowRecord,
    finalize_partial_beats,
    merge_ordered_exact_partial_temporal_stream,
    pack_final_values,
    partial_stream_from_blocks,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]

SEQUENCE_LENGTH = 131072
TOKENS_PER_FULL_WINDOW = 24
FULL_WINDOWS = SEQUENCE_LENGTH // TOKENS_PER_FULL_WINDOW
FINAL_PARTIAL_TOKENS = SEQUENCE_LENGTH % TOKENS_PER_FULL_WINDOW
PROJECTED_WINDOWS = math.ceil(SEQUENCE_LENGTH / TOKENS_PER_FULL_WINDOW)
HEADS_PER_LAYER = 32
LAYERS = 32
SERVICE_PERIOD_NS = 10.0
TEMPORAL_PERIOD_NS = 12.0
DIVIDER_LANES = (1, 2, 4, 8)

_OUT_RE = re.compile(
    r"OUT sequence=(\d+) count=(\d+) command=(\d+) head=(\d+) "
    r"slice=(\d+) last=(\d+) value=([0-9a-fA-F]+)"
)
_CMD_RE = re.compile(r"CMD index=(\d+) start=(\d+) terminal=(\d+)")
_SUMMARY_RE = re.compile(
    r"SUMMARY service_cycles=(\d+) temporal_cycles=(\d+) commands=(\d+) "
    r"outputs=(\d+) refills=(\d+) service_accepted=(\d+) service_completed=(\d+) "
    r"service_req=(\d+) service_resp=(\d+) temporal_inputs=(\d+) "
    r"temporal_merges=(\d+) temporal_emitted=(\d+) temporal_heads=(\d+) "
    r"finalizer_accepted=(\d+) finalizer_completed=(\d+) finalizer_cycles=(\d+) finalizer_first_accept=(\d+) "
    r"state_requests=(\d+) state_reads=(\d+) state_responses=(\d+) "
    r"state_writes=(\d+) protocol_error=(\d+)"
)


@dataclass(frozen=True)
class HeadWorkload:
    block_counts: tuple[int, ...]
    sequence_id: int
    command_id: int
    head_id: int

    def __post_init__(self) -> None:
        if not self.block_counts or any(count not in (1, 3) for count in self.block_counts):
            raise ValueError("each head needs one or more 1-block tail or 3-block full windows")
        if 1 in self.block_counts[:-1]:
            raise ValueError("an 8-token tail is allowed only in the final window")


def _window_values(seed: int) -> list[list[list[list[int]]]]:
    values = service_probe._shared_value_matrices()
    return [
        [
            [
                [
                    ((value + 127 + seed * 29 + block_index * 11 + value_slice * 3) % 255) - 127
                    for value in row
                ]
                for row in matrix
            ]
            for value_slice, matrix in enumerate(block_values)
        ]
        for block_index, block_values in enumerate(values)
    ]


def _commands(heads: Iterable[HeadWorkload]) -> list[JsonDict]:
    commands: list[JsonDict] = []
    for head_number, head in enumerate(heads):
        for window_index, block_count in enumerate(head.block_counts):
            command_index = len(commands)
            values = _window_values(command_index + head_number * 17 + 1)
            blocks = service_probe._cluster_beats(command_index + 1)[:block_count]
            commands.append(
                {
                    "command_index": command_index,
                    "physical_command_id": 0x5000 + command_index,
                    "sequence_id": head.sequence_id,
                    "logical_command_id": head.command_id,
                    "head_id": head.head_id,
                    "window_index": window_index,
                    "window_count": len(head.block_counts),
                    "block_count": block_count,
                    "head_last": window_index == len(head.block_counts) - 1,
                    "values": values,
                    "blocks": blocks,
                }
            )
    return commands


def _expected_rows(heads: tuple[HeadWorkload, ...], commands: list[JsonDict]) -> list[JsonDict]:
    records: list[ExactPartialWindowRecord] = []
    for command in commands:
        score_rows = [
            list(requantize_score_row(service_probe._raw_scores(block), multiplier=1, shift=0))
            for block in command["blocks"]
        ]
        partials = partial_stream_from_blocks(
            command_id=command["physical_command_id"],
            head_id=command["head_id"],
            score_rows=score_rows,
            value_blocks=command["values"][: command["block_count"]],
        )
        records.append(
            ExactPartialWindowRecord(
                sequence_id=command["sequence_id"],
                head_id=command["head_id"],
                window_index=command["window_index"],
                window_count=command["window_count"],
                beats=tuple(replace(beat, command_id=command["logical_command_id"]) for beat in partials),
            )
        )
    rows: list[JsonDict] = []
    for head in heads:
        selected = [record for record in records if record.sequence_id == head.sequence_id and record.head_id == head.head_id]
        for merged in merge_ordered_exact_partial_temporal_stream(selected):
            for beat in finalize_partial_beats(merged.beats):
                rows.append(
                    {
                        "sequence_id": merged.sequence_id,
                        "window_count": merged.window_count,
                        "command_id": beat.command_id,
                        "head_id": beat.head_id,
                        "slice": beat.slice_index,
                        "last": int(beat.last),
                        "value": pack_final_values(beat.values),
                    }
                )
    return rows


def _initializers(commands: list[JsonDict]) -> tuple[str, int, int]:
    lines: list[str] = []
    preload_flat = 0
    input_flat = 0
    for command in commands:
        command_index = command["command_index"]
        entries = service_probe._preload_entries(command["values"][: command["block_count"]])
        beats = [beat for block in command["blocks"] for beat in block]
        lines.extend(
            [
                f"    cmd_preload_start[{command_index}] = {preload_flat};",
                f"    cmd_preload_count[{command_index}] = {len(entries)};",
                f"    cmd_input_start[{command_index}] = {input_flat};",
                f"    cmd_input_count[{command_index}] = {len(beats)};",
                f"    cmd_physical[{command_index}] = 16'h{command['physical_command_id']:04x};",
                f"    cmd_sequence[{command_index}] = 16'h{command['sequence_id']:04x};",
                f"    cmd_logical[{command_index}] = 16'h{command['logical_command_id']:04x};",
                f"    cmd_window_index[{command_index}] = 14'd{command['window_index']};",
                f"    cmd_window_count[{command_index}] = 15'd{command['window_count']};",
                f"    cmd_block_count[{command_index}] = 15'd{command['block_count']};",
                f"    cmd_head[{command_index}] = 5'd{command['head_id']};",
                f"    cmd_head_last[{command_index}] = 1'b{int(command['head_last'])};",
            ]
        )
        for entry in entries:
            lines.append(
                f"    preload_addr_mem[{preload_flat}] = 14'd{entry['addr']}; "
                f"preload_slice_mem[{preload_flat}] = 4'd{entry['slice']}; "
                f"preload_matrix_mem[{preload_flat}] = 512'h{entry['matrix_hex']};"
            )
            preload_flat += 1
        for query, keys in beats:
            lines.append(
                f"    q_mem[{input_flat}] = {service_probe._signed_literal(query, 8)}; "
                f"k_mem[{input_flat}] = 64'h{service_probe._pack(keys, 8):016x};"
            )
            input_flat += 1
    return "\n".join(lines), preload_flat, input_flat


def _testbench(top_name: str, heads: tuple[HeadWorkload, ...], commands: list[JsonDict]) -> str:
    init, preload_total, input_total = _initializers(commands)
    output_total = len(heads) * 16
    return f"""`timescale 1ns/1ps
{service_probe._FAKERAM_MODEL}
module tb;
  localparam integer COMMANDS = {len(commands)};
  localparam integer PRELOAD_TOTAL = {preload_total};
  localparam integer INPUT_TOTAL = {input_total};
  localparam integer OUTPUT_TOTAL = {output_total};
  localparam [2:0] REFILL=3'd0, COMMAND=3'd1, INPUTS=3'd2, TERMINAL=3'd3, HEAD_DRAIN=3'd4;

  reg service_clk=0, temporal_clk=0, service_rst_n=0, temporal_rst_n=0;
  always #5 service_clk = ~service_clk;
  always #6 temporal_clk = ~temporal_clk;
  reg preload_valid; wire preload_ready; reg [13:0] preload_addr; reg [3:0] preload_value_slice; reg [511:0] preload_matrix;
  reg [13:0] preload_addr_mem [0:PRELOAD_TOTAL-1]; reg [3:0] preload_slice_mem [0:PRELOAD_TOTAL-1]; reg [511:0] preload_matrix_mem [0:PRELOAD_TOTAL-1];
  reg signed [7:0] q_mem [0:INPUT_TOTAL-1]; reg [63:0] k_mem [0:INPUT_TOTAL-1];
  integer cmd_preload_start[0:COMMANDS-1], cmd_preload_count[0:COMMANDS-1], cmd_input_start[0:COMMANDS-1], cmd_input_count[0:COMMANDS-1];
  reg [15:0] cmd_physical[0:COMMANDS-1], cmd_sequence[0:COMMANDS-1], cmd_logical[0:COMMANDS-1];
  reg [13:0] cmd_window_index[0:COMMANDS-1]; reg [14:0] cmd_window_count[0:COMMANDS-1], cmd_block_count[0:COMMANDS-1];
  reg [4:0] cmd_head[0:COMMANDS-1]; reg cmd_head_last[0:COMMANDS-1]; integer cmd_start_cycle[0:COMMANDS-1];
  reg cluster_command_valid; wire cluster_command_ready; reg [15:0] cluster_command_id, cluster_logical_sequence_id, cluster_logical_command_id;
  reg [13:0] cluster_window_index; reg [14:0] cluster_window_count, cluster_command_block_count; reg [4:0] cluster_command_head_id;
  reg [31:0] cluster_command_score_multiplier; reg [5:0] cluster_command_score_shift; reg cluster_input_valid; wire cluster_input_ready; reg cluster_input_last; reg [7:0] cluster_input_a; reg [63:0] cluster_input_b;
  wire out_valid; wire [15:0] out_sequence_id, out_command_id; wire [14:0] out_window_count; wire [4:0] out_head_id; wire [3:0] out_slice; wire out_last; wire [319:0] out_value;
  wire service_shared_result_valid, service_shared_result_ready, service_shared_result_last;
  wire [31:0] service_cluster_accepted_count, service_cluster_completed_count, service_accepted_req_count, service_emitted_resp_count;
  wire [31:0] temporal_input_accepted_count, temporal_merge_completed_count, temporal_emitted_beat_count, temporal_completed_head_count;
  wire [31:0] temporal_state_memory_request_count, temporal_state_memory_read_request_count, temporal_state_memory_read_response_count, temporal_state_memory_write_count;
  wire [31:0] finalizer_accepted_count, finalizer_completed_count, finalizer_cycle_count; wire protocol_error;
  integer service_cycle, temporal_cycle, command_index, preload_item, input_item, output_count, refill_count, completed_heads_seen, finalizer_first_accept; reg [2:0] phase; reg summary_pending, finalizer_first_seen;

  {top_name} dut(
    .service_clk(service_clk), .service_rst_n(service_rst_n), .temporal_clk(temporal_clk), .temporal_rst_n(temporal_rst_n),
    .preload_valid(preload_valid), .preload_ready(preload_ready), .preload_addr(preload_addr), .preload_value_slice(preload_value_slice), .preload_matrix(preload_matrix),
    .cluster_command_valid(cluster_command_valid), .cluster_command_ready(cluster_command_ready), .cluster_command_id(cluster_command_id),
    .cluster_logical_sequence_id(cluster_logical_sequence_id), .cluster_logical_command_id(cluster_logical_command_id), .cluster_window_index(cluster_window_index), .cluster_window_count(cluster_window_count),
    .cluster_command_block_count(cluster_command_block_count), .cluster_command_head_id(cluster_command_head_id), .cluster_command_score_multiplier(cluster_command_score_multiplier), .cluster_command_score_shift(cluster_command_score_shift),
    .cluster_input_valid(cluster_input_valid), .cluster_input_ready(cluster_input_ready), .cluster_input_last(cluster_input_last), .cluster_input_a(cluster_input_a), .cluster_input_b(cluster_input_b),
    .out_valid(out_valid), .out_ready(1'b1), .out_sequence_id(out_sequence_id), .out_window_count(out_window_count), .out_command_id(out_command_id), .out_head_id(out_head_id), .out_slice(out_slice), .out_last(out_last), .out_value(out_value),
    .service_shared_result_valid(service_shared_result_valid), .service_shared_result_ready(service_shared_result_ready), .service_shared_result_last(service_shared_result_last),
    .service_cluster_accepted_count(service_cluster_accepted_count), .service_cluster_completed_count(service_cluster_completed_count), .service_accepted_req_count(service_accepted_req_count), .service_emitted_resp_count(service_emitted_resp_count),
    .temporal_input_accepted_count(temporal_input_accepted_count), .temporal_merge_completed_count(temporal_merge_completed_count), .temporal_emitted_beat_count(temporal_emitted_beat_count), .temporal_completed_head_count(temporal_completed_head_count),
    .temporal_state_memory_request_count(temporal_state_memory_request_count), .temporal_state_memory_read_request_count(temporal_state_memory_read_request_count), .temporal_state_memory_read_response_count(temporal_state_memory_read_response_count), .temporal_state_memory_write_count(temporal_state_memory_write_count),
    .finalizer_accepted_count(finalizer_accepted_count), .finalizer_completed_count(finalizer_completed_count), .finalizer_cycle_count(finalizer_cycle_count), .protocol_error(protocol_error));

  always @* begin
    preload_valid = service_rst_n && phase == REFILL;
    preload_addr = preload_addr_mem[cmd_preload_start[command_index]+preload_item]; preload_value_slice = preload_slice_mem[cmd_preload_start[command_index]+preload_item]; preload_matrix = preload_matrix_mem[cmd_preload_start[command_index]+preload_item];
    cluster_command_valid = service_rst_n && phase == COMMAND; cluster_command_id=cmd_physical[command_index]; cluster_logical_sequence_id=cmd_sequence[command_index]; cluster_logical_command_id=cmd_logical[command_index];
    cluster_window_index=cmd_window_index[command_index]; cluster_window_count=cmd_window_count[command_index]; cluster_command_block_count=cmd_block_count[command_index]; cluster_command_head_id=cmd_head[command_index]; cluster_command_score_multiplier=32'd1; cluster_command_score_shift=6'd0;
    cluster_input_valid = service_rst_n && phase == INPUTS; cluster_input_a=q_mem[cmd_input_start[command_index]+input_item]; cluster_input_b=k_mem[cmd_input_start[command_index]+input_item]; cluster_input_last=cluster_input_valid && (((input_item+1)%128)==0);
  end

  always @(posedge service_clk or negedge service_rst_n) begin
    if(!service_rst_n) begin service_cycle<=0; command_index<=0; preload_item<=0; input_item<=0; refill_count<=0; completed_heads_seen<=0; phase<=REFILL; end else begin
      service_cycle<=service_cycle+1;
      if(phase==REFILL && preload_valid && preload_ready) begin refill_count<=refill_count+1; if(preload_item==cmd_preload_count[command_index]-1) begin preload_item<=0; phase<=COMMAND; end else preload_item<=preload_item+1; end
      if(phase==COMMAND && cluster_command_valid && cluster_command_ready) begin cmd_start_cycle[command_index]<=service_cycle; input_item<=0; phase<=INPUTS; end
      if(phase==INPUTS && cluster_input_valid && cluster_input_ready) begin if(input_item==cmd_input_count[command_index]-1) phase<=TERMINAL; else input_item<=input_item+1; end
      if(phase==TERMINAL && service_shared_result_valid && service_shared_result_ready && service_shared_result_last) begin
        $display("CMD index=%0d start=%0d terminal=%0d",command_index,cmd_start_cycle[command_index],service_cycle);
        if(cmd_head_last[command_index]) phase<=HEAD_DRAIN; else begin command_index<=command_index+1; preload_item<=0; phase<=REFILL; end
      end
      if(phase==HEAD_DRAIN && temporal_completed_head_count>completed_heads_seen) begin completed_heads_seen<=completed_heads_seen+1; if(command_index<COMMANDS-1) begin command_index<=command_index+1; preload_item<=0; phase<=REFILL; end end
      if(service_cycle>500000) $fatal(1,"service timeout");
    end
  end

  always @(posedge temporal_clk or negedge temporal_rst_n) begin
    if(!temporal_rst_n) begin temporal_cycle<=0; output_count<=0; summary_pending<=0; finalizer_first_accept<=-1; finalizer_first_seen<=0; end else begin
      temporal_cycle<=temporal_cycle+1;
      if(!finalizer_first_seen && finalizer_accepted_count>0) begin finalizer_first_seen<=1; finalizer_first_accept<=temporal_cycle; end
      if(out_valid) begin $display("OUT sequence=%0d count=%0d command=%0d head=%0d slice=%0d last=%0d value=%080x",out_sequence_id,out_window_count,out_command_id,out_head_id,out_slice,out_last,out_value); output_count<=output_count+1; if(output_count+1==OUTPUT_TOTAL) summary_pending<=1; end
      if(summary_pending) begin
        $display("SUMMARY service_cycles=%0d temporal_cycles=%0d commands=%0d outputs=%0d refills=%0d service_accepted=%0d service_completed=%0d service_req=%0d service_resp=%0d temporal_inputs=%0d temporal_merges=%0d temporal_emitted=%0d temporal_heads=%0d finalizer_accepted=%0d finalizer_completed=%0d finalizer_cycles=%0d finalizer_first_accept=%0d state_requests=%0d state_reads=%0d state_responses=%0d state_writes=%0d protocol_error=%0d",service_cycle,temporal_cycle,COMMANDS,output_count,refill_count,service_cluster_accepted_count,service_cluster_completed_count,service_accepted_req_count,service_emitted_resp_count,temporal_input_accepted_count,temporal_merge_completed_count,temporal_emitted_beat_count,temporal_completed_head_count,finalizer_accepted_count,finalizer_completed_count,finalizer_cycle_count,finalizer_first_accept,temporal_state_memory_request_count,temporal_state_memory_read_request_count,temporal_state_memory_read_response_count,temporal_state_memory_write_count,protocol_error);
        $finish;
      end
      if(temporal_cycle>500000) $fatal(1,"temporal timeout");
    end
  end
  initial begin
{init}
    repeat(4) @(posedge service_clk); @(negedge service_clk); service_rst_n=1; #13 temporal_rst_n=1;
  end
endmodule
"""


def _parse(stdout: str) -> tuple[list[JsonDict], list[JsonDict], JsonDict]:
    rows: list[JsonDict] = []
    commands: list[JsonDict] = []
    summary: JsonDict | None = None
    keys = ("service_cycles", "temporal_cycles", "commands", "outputs", "refills", "service_accepted", "service_completed", "service_req", "service_resp", "temporal_inputs", "temporal_merges", "temporal_emitted", "temporal_heads", "finalizer_accepted", "finalizer_completed", "finalizer_cycles", "finalizer_first_accept", "state_requests", "state_reads", "state_responses", "state_writes", "protocol_error")
    for raw in stdout.splitlines():
        line = raw.strip()
        if match := _OUT_RE.fullmatch(line):
            rows.append(dict(zip(("sequence_id", "window_count", "command_id", "head_id", "slice", "last"), map(int, match.groups()[:6]), strict=True)) | {"value": int(match.group(7), 16)})
        elif match := _CMD_RE.fullmatch(line):
            commands.append({"index": int(match.group(1)), "start": int(match.group(2)), "terminal": int(match.group(3))})
        elif match := _SUMMARY_RE.fullmatch(line):
            summary = dict(zip(keys, map(int, match.groups()), strict=True))
    if summary is None:
        raise RuntimeError(f"simulation omitted SUMMARY\n{stdout}")
    return rows, commands, summary


def run_rtl_case(*, name: str, heads: tuple[HeadWorkload, ...], divider_lanes: int) -> JsonDict:
    commands = _commands(heads)
    expected = _expected_rows(heads, commands)
    top_name = f"attention_decode_score_multivalue_service_workload_{divider_lanes}"
    config = finalized_probe._config(
        top_name,
        divider_lanes=divider_lanes,
        temporal_state_backend="sram",
        service_value_memory_backend="macro_banked_4x16x64x32",
    )
    with tempfile.TemporaryDirectory(prefix="finalized-cdc-workload-") as temp_name:
        temp = Path(temp_name)
        rtl = temp / "rtl"
        generate(config, rtl)
        tb = temp / "tb.sv"
        tb.write_text(_testbench(top_name, heads, commands), encoding="utf-8")
        simv = temp / "simv"
        compile_run = subprocess.run([finalized_probe._tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl / "top.v"), str(REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"), str(tb)], capture_output=True, text=True, timeout=240)
        if compile_run.returncode:
            raise RuntimeError(f"iverilog failed for {name}/lane{divider_lanes}:\n{compile_run.stderr}")
        sim_run = subprocess.run([finalized_probe._tool("vvp"), str(simv)], capture_output=True, text=True, timeout=300)
        if sim_run.returncode:
            raise RuntimeError(f"RTL failed for {name}/lane{divider_lanes}:\n{sim_run.stdout}\n{sim_run.stderr}")
    observed, command_cycles, summary = _parse(sim_run.stdout)
    window_count = len(commands)
    head_count = len(heads)
    expected_refills = 16 * sum(command["block_count"] for command in commands)
    expected_requests = expected_refills
    counter_model = {
        "commands": window_count,
        "outputs": 16 * head_count,
        "refills": expected_refills,
        "service_accepted": window_count,
        "service_completed": window_count,
        "service_req": expected_requests,
        "service_resp": expected_requests,
        "temporal_inputs": 16 * window_count,
        "temporal_merges": 16 * (window_count - head_count),
        "temporal_emitted": 16 * head_count,
        "temporal_heads": head_count,
        "finalizer_accepted": 16 * head_count,
        "finalizer_completed": 16 * head_count,
        "state_requests": 32 * window_count,
        "state_reads": 16 * window_count,
        "state_responses": 16 * window_count,
        "state_writes": 16 * window_count,
        "protocol_error": 0,
    }
    counter_match = all(summary[key] == value for key, value in counter_model.items())
    passed = (
        observed == expected
        and len(command_cycles) == window_count
        and counter_match
    )
    if not passed:
        raise RuntimeError(f"bounded RTL correspondence failed for {name}/lane{divider_lanes}: {summary}")
    # service_cycle starts at reset release, so this includes the first refill.
    service_span = command_cycles[-1]["terminal"] + 1
    finalizer_busy_span = summary["temporal_cycles"] - summary["finalizer_first_accept"] + 1
    return {
        "name": name,
        "passed": True,
        "head_count": head_count,
        "window_count": window_count,
        "block_counts": [list(head.block_counts) for head in heads],
        "service_span_cycles": service_span,
        "finalizer_busy_span_temporal_cycles": finalizer_busy_span,
        "command_cycles": command_cycles,
        "summary": summary,
        "deterministic_counter_model": counter_model,
        "all_modeled_counters_match_rtl": counter_match,
        "distinct_window_refill_verified_by_exact_outputs": True,
        "rows_sha256": __import__("hashlib").sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest(),
    }


def _affine_proof(rows: list[JsonDict]) -> JsonDict:
    values = [row["service_span_cycles"] for row in rows]
    deltas = [right - left for left, right in zip(values, values[1:])]
    if len(set(deltas)) != 1:
        raise RuntimeError(f"service counter deltas are non-affine: values={values}, deltas={deltas}")
    startup = values[0]
    steady = deltas[0]
    return {
        "proven": True,
        "bounded_window_counts": [1, 2, 3, 4],
        "measured_service_span_cycles": values,
        "counter_deltas": deltas,
        "startup_cycles": startup,
        "steady_state_cycles_per_additional_full_window": steady,
        "recurrence": "service_cycles(N) = startup_cycles + (N - 1) * steady_state_cycles_per_additional_full_window",
    }


def build_report() -> JsonDict:
    lane_reports: list[JsonDict] = []
    for lane in DIVIDER_LANES:
        bounded = [
            run_rtl_case(name=f"full_windows_{count}", heads=(HeadWorkload((3,) * count, 0x7100, 0x6100, 3),), divider_lanes=lane)
            for count in range(1, 5)
        ]
        proof = _affine_proof(bounded)
        for row_index, row in enumerate(bounded):
            modeled_span = proof["startup_cycles"] + row_index * proof["steady_state_cycles_per_additional_full_window"]
            row["modeled_service_span_cycles"] = modeled_span
            row["service_cycle_counter_matches_affine_model"] = row["service_span_cycles"] == modeled_span
            if not row["service_cycle_counter_matches_affine_model"]:
                raise RuntimeError(f"affine service model mismatch for lane{lane}/{row['name']}")
        tail = run_rtl_case(name="three_full_plus_8_token_tail", heads=(HeadWorkload((3, 3, 3, 1), 0x7200, 0x6200, 4),), divider_lanes=lane)
        reuse = run_rtl_case(name="two_head_state_clear_reuse", heads=(HeadWorkload((3, 3), 0x7300, 0x6300, 5), HeadWorkload((3, 3), 0x7301, 0x6301, 5)), divider_lanes=lane)
        full_four = bounded[-1]["service_span_cycles"]
        tail_adjustment = tail["service_span_cycles"] - full_four
        projected_service = proof["startup_cycles"] + (PROJECTED_WINDOWS - 1) * proof["steady_state_cycles_per_additional_full_window"]
        finalizer_cycles_per_slice = 57 * (8 // lane) + 2
        final_drain = 16 * finalizer_cycles_per_slice
        if any(row["finalizer_busy_span_temporal_cycles"] != final_drain for row in bounded):
            raise RuntimeError(f"final-drain model mismatch for divider_lanes={lane}")
        if tail["finalizer_busy_span_temporal_cycles"] != final_drain:
            raise RuntimeError(f"tail final-drain model mismatch for divider_lanes={lane}")
        if tail["summary"]["finalizer_completed"] != 16 or tail["summary"]["refills"] != (3 * 3 + 1) * 16:
            raise RuntimeError("tail projection omitted finalization or refill traffic")
        lane_reports.append(
            {
                "divider_lanes": lane,
                "bounded_rtl_cases": bounded,
                "tail_rtl_case": tail,
                "state_clear_reuse_rtl_case": reuse,
                "affine_recurrence_proof": proof,
                "tail_service_adjustment_cycles": tail_adjustment,
                "tail_adjustment_used_in_projection": False,
                "final_drain_temporal_cycles": final_drain,
                "projection": {
                    "windows_per_head": PROJECTED_WINDOWS,
                    "full_windows_per_head": FULL_WINDOWS,
                    "final_partial_tokens": FINAL_PARTIAL_TOKENS,
                    "service_cycles_per_head": projected_service,
                    "temporal_final_drain_cycles_per_head": final_drain,
                    "head_latency_ns_serial_upper_bound": projected_service * SERVICE_PERIOD_NS + final_drain * TEMPORAL_PERIOD_NS,
                    "service_cycles_per_layer_serial_heads": projected_service * HEADS_PER_LAYER,
                    "temporal_final_drain_cycles_per_layer_serial_heads": final_drain * HEADS_PER_LAYER,
                    "layer_latency_ns_serial_upper_bound": (projected_service * SERVICE_PERIOD_NS + final_drain * TEMPORAL_PERIOD_NS) * HEADS_PER_LAYER,
                    "service_cycles_32_layer_serial_bound": projected_service * HEADS_PER_LAYER * LAYERS,
                    "temporal_final_drain_cycles_32_layer_serial_bound": final_drain * HEADS_PER_LAYER * LAYERS,
                },
            }
        )
    return {
        "model": "attention_decode_score_multivalue_service_workload_correspondence_v1",
        "passed": True,
        "workload": {"model": "Llama7B", "sequence_length": SEQUENCE_LENGTH, "tokens_per_full_window": TOKENS_PER_FULL_WINDOW, "full_windows_per_head": FULL_WINDOWS, "final_partial_tokens": FINAL_PARTIAL_TOKENS, "windows_per_head": PROJECTED_WINDOWS, "heads_per_layer": HEADS_PER_LAYER, "layers": LAYERS},
        "clock_contract": {"service_period_ns": SERVICE_PERIOD_NS, "temporal_period_ns": TEMPORAL_PERIOD_NS},
        "projection_counter_contract": {
            "counter": "reset_release_to_last_service_terminal_cycles",
            "includes_first_refill": True,
            "requires_exact_affine_deltas": True,
            "elapsed_testbench_clock_counters_are_diagnostic_only": True,
        },
        "lane_reports": lane_reports,
        "assumptions": [
            "one c1 service instance schedules windows and heads serially",
            "each full window is three 8-token blocks and the final partial is one 8-token block",
            "value-memory refill traffic is serialized before each command and included in bounded RTL service spans",
            "the bounded probe uses SRAM temporal state and the macro-banked 4x16x64x32 service value backend",
            "the affine projection is used only after equal deltas are observed at window_count 1, 2, 3, and 4",
            "temporal final drain is 16 slices times the RTL restoring-divider schedule of 57 cycles per lane group plus accept/output cycles",
            "layer and 32-layer values are conservative serial bounds; no inter-head or inter-layer overlap is credited",
            "elapsed testbench service/temporal/finalizer counters include CDC phase and overlap and are not projected",
        ],
        "fail_closed_guards": {"non_affine_counter_deltas": True, "missing_refill_traffic": True, "missing_single_head_finalization": True, "protocol_error": True, "software_rtl_value_mismatch": True},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
