#!/usr/bin/env python3
"""Generate phase VCD activity for the real eight-head GQA group wrapper."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.generate_attention_decode_score_multivalue_cluster_activity import (
    _DEFAULT_CLOCK_PERIOD_NS,
    _DEFAULT_HEAD_DIM,
    _DEFAULT_SCORE_MULTIPLIER,
    _DEFAULT_SCORE_SHIFT,
    _FAKERAM_MODEL,
    _FINALIZE_DIVIDE_CYCLES_PER_DIM,
    _FINALIZE_RESULT_EMIT_CYCLES,
    _PHASES,
    _REPLAY_CLEAR_CYCLES,
    _TARGET_MAX_BLOCKS,
    _VALUE_DIMS,
    _VALUE_SLICES,
    _pack,
    _parse_phase_cycles,
    _replay_value_scaling,
    _score_fill_scaling,
    _sha256_file,
    _tool,
    _vectors,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_gqa_group import (
    generate as generate_group,
)

JsonDict = dict[str, Any]
_PHASE_DONE_PREFIX = "PHASE_DONE"
_QUERY_HEADS_PER_KV = 8
_GQA_FINALIZE_RESULT_CYCLES = 58208


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config must be a JSON object")
    return payload


def _validate_request(*, config: JsonDict, block_count: int, head_dim: int) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_decode_score_multivalue_gqa_group")
    if not top_name or not isinstance(body, dict):
        raise ValueError("config requires top_name and attention_decode_score_multivalue_gqa_group")
    max_blocks = int(body.get("max_blocks", 0))
    if max_blocks != _TARGET_MAX_BLOCKS:
        raise ValueError(f"activity generation requires max_blocks={_TARGET_MAX_BLOCKS}")
    if int(body.get("query_heads_per_kv", 8)) != _QUERY_HEADS_PER_KV:
        raise ValueError("activity generation requires query_heads_per_kv=8")
    if block_count < 1:
        raise ValueError("block_count must be >= 1")
    if head_dim not in {3, 128}:
        raise ValueError("head_dim must be 3 or 128")
    beats, values = _vectors(head_dim=head_dim)
    if block_count > len(beats):
        raise ValueError(f"block_count must be <= available representative blocks ({len(beats)})")
    return {
        "top_name": top_name,
        "max_blocks": max_blocks,
        "score_scale_lanes_per_cycle": int(body.get("score_scale_lanes_per_cycle", 1)),
        "beats": beats[:block_count],
        "values": values[:block_count],
    }


def _phase_expr(phase: str) -> str:
    if phase == "score_fill":
        states = " || ".join(
            f"dut.u_head_{head}.state_q == 3'd{state}"
            for head in range(_QUERY_HEADS_PER_KV)
            for state in range(1, 6)
        )
        return f"(command_valid && command_ready) || ({states})"
    if phase == "replay_value":
        states = " || ".join(
            f"dut.u_head_{head}.reducer.state == 4'd{state}"
            for head in range(_QUERY_HEADS_PER_KV)
            for state in range(2, 7)
        )
        return f"({states})"
    if phase == "finalize_result":
        states = " || ".join(
            f"dut.u_head_{head}.reducer.state == 4'd{state}"
            for head in range(_QUERY_HEADS_PER_KV)
            for state in range(7, 11)
        )
        return f"({states})"
    raise ValueError(f"unknown phase: {phase}")


def _gqa_finalize_result_scaling(*, cycle_count: int) -> JsonDict:
    single_head_cycles = _VALUE_DIMS * _FINALIZE_DIVIDE_CYCLES_PER_DIM + _FINALIZE_RESULT_EMIT_CYCLES
    expected_cycles = _GQA_FINALIZE_RESULT_CYCLES
    if cycle_count != expected_cycles:
        raise RuntimeError(
            "GQA finalize_result cycles diverged from the serialized eight-head result contract: "
            f"measured={cycle_count} expected={expected_cycles}"
        )
    return {
        "kind": "fixed_per_command_serialized_query_heads",
        "query_heads_per_kv": _QUERY_HEADS_PER_KV,
        "value_dimensions_per_head": _VALUE_DIMS,
        "divide_cycles_per_dimension": _FINALIZE_DIVIDE_CYCLES_PER_DIM,
        "result_emit_cycles_per_head": _FINALIZE_RESULT_EMIT_CYCLES,
        "single_head_reference_cycles": single_head_cycles,
        "measured_group_cycles": cycle_count,
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "full_context_cycles": cycle_count,
        "formula": "measured fixed group-finalize contract; child divide and serialized result phases overlap",
    }


def _query_lanes(q: int, beat_index: int) -> list[int]:
    return [
        ((q + head * 31 + beat_index * head * 3 + 127) % 255) - 127
        for head in range(_QUERY_HEADS_PER_KV)
    ]


def _testbench(
    *,
    top_name: str,
    beats: list[list[tuple[int, list[int]]]],
    values: list[list[list[list[int]]]],
    block_count: int,
    head_dim: int,
    score_multiplier: int,
    score_shift: int,
    phase: str,
    vcd_path: Path,
    clock_period_ns: float,
) -> str:
    flat_beats = [beat for block in beats for beat in block]
    beat_init = "\n".join(
        f"    query_mem[{index}] = 64'h{_pack(_query_lanes(q, index), 8):016x}; "
        f"key_mem[{index}] = 64'h{_pack(keys, 8):016x};"
        for index, (q, keys) in enumerate(flat_beats)
    )
    last_indices = {
        sum(len(block) for block in beats[: index + 1]) - 1
        for index in range(len(beats))
    }
    last_cases = "\n".join(f"      {index}: input_last = 1'b1;" for index in sorted(last_indices))
    value_init = "\n".join(
        f"    value_mem[{block * _VALUE_SLICES + value_slice}] = 512'h"
        f"{_pack([lane for row in values[block][value_slice] for lane in row], 8):0128x};"
        for block in range(block_count)
        for value_slice in range(_VALUE_SLICES)
    )
    phase_active = _phase_expr(phase)
    clock_half_period = clock_period_ns / 2.0
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer BLOCK_COUNT = {block_count};
  localparam integer HEAD_DIM = {head_dim};
  localparam integer TOTAL_BEATS = {len(flat_beats)};
  reg clk = 0, rst_n = 0;
  reg command_valid, input_valid, input_last;
  wire command_ready, input_ready;
  reg [63:0] input_query;
  reg signed [63:0] input_key;
  wire value_read_req_valid, value_response_ready;
  reg value_read_req_ready, value_response_valid;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg [13:0] value_response_address;
  reg [3:0] value_response_slice;
  reg [511:0] value_response_matrix;
  wire result_valid, result_last;
  reg result_ready;
  wire [2:0] result_head;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  wire protocol_error;
  reg [63:0] query_mem [0:TOTAL_BEATS-1];
  reg [63:0] key_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:BLOCK_COUNT*{_VALUE_SLICES}-1];
  integer input_index = 0;
  integer phase_cycles = 0;
  reg value_pending = 0;
  reg [13:0] pending_addr = 0;
  reg [3:0] pending_slice = 0;
  integer pending_delay = 0;
  reg phase_started = 0;

  always #{clock_half_period:g} clk = ~clk;

  {top_name} dut (
      .clk(clk), .rst_n(rst_n), .command_valid(command_valid), .command_ready(command_ready),
      .command_id(16'h4a21), .command_block_count(BLOCK_COUNT),
      .command_score_multiplier(32'd{score_multiplier}), .command_score_shift(6'd{score_shift}),
      .input_valid(input_valid), .input_ready(input_ready), .input_last(input_last),
      .input_query(input_query), .input_key(input_key),
      .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address), .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid), .value_response_ready(value_response_ready),
      .value_response_address(value_response_address), .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix), .result_valid(result_valid), .result_ready(result_ready),
      .result_head(result_head), .result_command_id(result_command_id), .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum), .result_slice(result_slice), .result_last(result_last),
      .result_value(result_value), .accepted_count(accepted_count), .completed_count(completed_count),
      .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    input_valid = rst_n && input_index < TOTAL_BEATS;
    input_query = input_index < TOTAL_BEATS ? query_mem[input_index] : 0;
    input_key = input_index < TOTAL_BEATS ? key_mem[input_index] : 0;
    input_last = 0;
    case (input_index)
{last_cases}
      default: input_last = 0;
    endcase
    value_read_req_ready = 1'b1;
    result_ready = 1'b1;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      input_index <= 0;
      phase_cycles <= 0;
      value_pending <= 0;
      value_response_valid <= 0;
      pending_delay <= 0;
      value_response_address <= 0;
      value_response_slice <= 0;
      value_response_matrix <= 0;
      phase_started <= 0;
    end else begin
      if (input_valid && input_ready) input_index <= input_index + 1;
      if (value_read_req_valid && value_read_req_ready) begin
        if (value_pending || value_response_valid) $fatal(1, "multiple outstanding value requests");
        value_pending <= 1;
        pending_addr <= value_read_req_address;
        pending_slice <= value_read_req_slice;
        pending_delay <= 1;
      end
      if (value_pending) begin
        if (pending_delay == 0) begin
          value_pending <= 0;
          value_response_valid <= 1;
          value_response_address <= pending_addr;
          value_response_slice <= pending_slice;
          value_response_matrix <= value_mem[pending_addr * {_VALUE_SLICES} + pending_slice];
        end else pending_delay <= pending_delay - 1;
      end
      if (value_response_valid && value_response_ready) value_response_valid <= 0;
      if (!phase_started && ({phase_active})) begin
        phase_started <= 1;
        phase_cycles <= 1;
        $dumpon;
      end else if (phase_started && ({phase_active})) begin
        phase_cycles <= phase_cycles + 1;
      end else if (phase_started && !({phase_active})) begin
        if (protocol_error) $fatal(1, "protocol_error raised during {phase}");
        $display("{_PHASE_DONE_PREFIX} phase={phase} cycles=%0d service_cycles=%0d accepted=%0d completed=%0d", phase_cycles, cycle_count, accepted_count, completed_count);
        $dumpoff;
        #1 $finish;
      end
      if (cycle_count > 100000) $fatal(1, "timeout");
    end
  end

  initial begin
    $dumpfile("{vcd_path.as_posix()}");
    $dumpvars(0, dut);
    $dumpoff;
{beat_init}
{value_init}
    value_response_valid = 0; value_response_address = 0; value_response_slice = 0; value_response_matrix = 0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;
  end
endmodule
"""


def _run_phase(
    *,
    config: JsonDict,
    phase: str,
    out_dir: Path,
    block_count: int,
    head_dim: int,
    clock_period_ns: float,
    score_multiplier: int,
    score_shift: int,
) -> tuple[int, int, Path]:
    validated = _validate_request(config=config, block_count=block_count, head_dim=head_dim)
    with tempfile.TemporaryDirectory(prefix=f"decode-score-gqa-group-{phase}-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        generate_group(json.loads(json.dumps(config)), rtl_dir)
        vcd_path = tmp / f"{phase}.vcd"
        tb_path = tmp / "tb.sv"
        tb_path.write_text(
            _testbench(
                top_name=str(validated["top_name"]),
                beats=validated["beats"],
                values=validated["values"],
                block_count=block_count,
                head_dim=head_dim,
                score_multiplier=score_multiplier,
                score_shift=score_shift,
                phase=phase,
                vcd_path=vcd_path,
                clock_period_ns=clock_period_ns,
            ),
            encoding="utf-8",
        )
        simv = tmp / "simv"
        compiled = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), str(rtl_dir / "top.v"), str(tb_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed for {phase}: {compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(f"simulation failed for {phase}:\n{run.stdout}\n{run.stderr}")
        cycle_count, service_cycles = _parse_phase_cycles(run.stdout, phase)
        phase_out = out_dir / f"{phase}.vcd"
        phase_out.write_bytes(vcd_path.read_bytes())
        return cycle_count, service_cycles, phase_out


def generate_phase_activity(
    config: JsonDict,
    out_dir: Path,
    *,
    block_count: int = 3,
    head_dim: int = _DEFAULT_HEAD_DIM,
    clock_period_ns: float = _DEFAULT_CLOCK_PERIOD_NS,
    score_multiplier: int = _DEFAULT_SCORE_MULTIPLIER,
    score_shift: int = _DEFAULT_SCORE_SHIFT,
) -> JsonDict:
    if clock_period_ns <= 0.0:
        raise ValueError("clock_period_ns must be > 0")
    validated = _validate_request(config=config, block_count=block_count, head_dim=head_dim)
    out_dir.mkdir(parents=True, exist_ok=True)
    phases: list[JsonDict] = []
    full_service_cycles = 0
    for phase in _PHASES:
        cycle_count, service_cycles, vcd_path = _run_phase(
            config=config,
            phase=phase,
            out_dir=out_dir,
            block_count=block_count,
            head_dim=head_dim,
            clock_period_ns=clock_period_ns,
            score_multiplier=score_multiplier,
            score_shift=score_shift,
        )
        if phase == "score_fill":
            scaling = _score_fill_scaling(cycle_count=cycle_count, block_count=block_count)
        elif phase == "replay_value":
            scaling = _replay_value_scaling(cycle_count=cycle_count, block_count=block_count)
        else:
            scaling = _gqa_finalize_result_scaling(cycle_count=cycle_count)
            full_service_cycles = service_cycles
        phases.append(
            {
                "phase": phase,
                "measured_cycles": cycle_count,
                "full_context_cycles": scaling["full_context_cycles"],
                "vcd": vcd_path.name,
                "vcd_sha256": _sha256_file(vcd_path),
                "requires_macro_activity": phase in {"score_fill", "replay_value"},
                "scaling": scaling,
            }
        )

    partition_cycles = sum(int(row["measured_cycles"]) for row in phases)
    if partition_cycles != full_service_cycles:
        raise RuntimeError(
            "GQA group phase activity does not partition the representative transaction: "
            f"phases={partition_cycles}, service={full_service_cycles}"
        )
    manifest = {
        "version": 1,
        "model": "decode_score_multivalue_gqa_group_phase_activity_v1",
        "generator": "npu/eval/generate_attention_decode_score_multivalue_gqa_group_activity.py",
        "top_name": validated["top_name"],
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_activity_v1",
        "activity_generation": "explicit_script_only",
        "scope": "tb/dut",
        "scope_semantics": "the complete generated GQA8 group wrapper, including all eight query-head clusters",
        "clock_period_ns": clock_period_ns,
        "block_count": block_count,
        "head_dim": head_dim,
        "beats_per_block": head_dim,
        "max_blocks": validated["max_blocks"],
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "query_heads_per_kv": _QUERY_HEADS_PER_KV,
        "query_activity_profile": "eight_distinct_deterministic_signed_int8_query_lanes",
        "score_multiplier": score_multiplier,
        "score_shift": score_shift,
        "score_scale_lanes_per_cycle": validated["score_scale_lanes_per_cycle"],
        "value_slices": _VALUE_SLICES,
        "value_dimensions_per_head": _VALUE_DIMS,
        "representative_full_transaction_cycles": full_service_cycles,
        "phase_partition_cycle_sum": partition_cycles,
        "phases": phases,
    }
    manifest_path = out_dir / "attention_decode_score_multivalue_gqa_group_activity_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--block-count", type=int, default=3)
    parser.add_argument("--head-dim", type=int, default=_DEFAULT_HEAD_DIM, choices=[3, 128])
    parser.add_argument("--clock-period-ns", type=float, default=_DEFAULT_CLOCK_PERIOD_NS)
    args = parser.parse_args()
    generate_phase_activity(
        _load(args.config),
        args.out,
        block_count=args.block_count,
        head_dim=args.head_dim,
        clock_period_ns=args.clock_period_ns,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
