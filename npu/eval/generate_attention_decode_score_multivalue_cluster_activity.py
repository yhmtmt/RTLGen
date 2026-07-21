#!/usr/bin/env python3
"""Generate phase-specific VCD activity for the shared-score multivalue cluster."""

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

from npu.eval.probe_attention_decode_score_multivalue_cluster_equivalence import (  # noqa: E402
    _FAKERAM_MODEL,
    _pack,
    _signed_literal,
    _tool,
    _vectors,
)
from npu.eval.extract_fakeram_vcd_activity import extract_fakeram_vcd_activity
from npu.eval.extract_sequential_register_vcd_activity import (
    extract_sequential_register_vcd_activity,
)
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate  # noqa: E402

JsonDict = dict[str, Any]

_PHASES = ("score_fill", "replay_value", "finalize_result")
_PHASE_DONE_PREFIX = "PHASE_DONE"
_DEFAULT_HEAD_DIM = 128
_DEFAULT_BLOCK_COUNT = 2
_DEFAULT_SCORE_MULTIPLIER = 1 << 20
_DEFAULT_SCORE_SHIFT = 0
_DEFAULT_CLOCK_PERIOD_NS = 10.0
_TARGET_MAX_BLOCKS = 16384
_VALUE_SLICES = 16
_VALUE_DIMS = _VALUE_SLICES * 8
_COMMAND_SETUP_CYCLES = 1
_REPLAY_CLEAR_CYCLES = _VALUE_SLICES
_FINALIZE_DIVIDE_CYCLES_PER_DIM = 60
_FINALIZE_RESULT_EMIT_CYCLES = _VALUE_SLICES
_REDUCER_NUMERATOR_ACCUM_WORDS = 128
_SCORE_TILE_ACCUM_WORDS = 8


def _load(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cluster_body(config: JsonDict) -> JsonDict:
    body = config.get("attention_decode_score_multivalue_cluster")
    if not isinstance(body, dict):
        raise ValueError("config requires attention_decode_score_multivalue_cluster")
    return body


def _validate_request(*, config: JsonDict, block_count: int, head_dim: int) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise ValueError("config requires top_name")
    body = _cluster_body(config)
    max_blocks = int(body.get("max_blocks", 0))
    if max_blocks != _TARGET_MAX_BLOCKS:
        raise ValueError(f"activity generation requires max_blocks={_TARGET_MAX_BLOCKS}")
    if block_count < 1:
        raise ValueError("block_count must be >= 1")
    if head_dim not in {3, 128}:
        raise ValueError("head_dim must be 3 or 128")
    beats, values = _vectors(head_dim=head_dim)
    if block_count > len(beats):
        raise ValueError(f"block_count must be <= available representative blocks ({len(beats)})")
    score_scale_lanes = int(body.get("score_scale_lanes_per_cycle", 1))
    return {
        "top_name": top_name,
        "max_blocks": max_blocks,
        "score_scale_lanes_per_cycle": score_scale_lanes,
        "beats": beats[:block_count],
        "values": values[:block_count],
    }


def _phase_expr(phase: str) -> str:
    if phase == "score_fill":
        return "(dut.state_q == 3'd0 && command_valid && command_ready) || dut.state_q == 3'd1 || dut.state_q == 3'd2 || dut.state_q == 3'd3 || dut.state_q == 3'd4 || dut.state_q == 3'd5"
    if phase == "replay_value":
        return "dut.reducer.state == 4'd2 || dut.reducer.state == 4'd3 || dut.reducer.state == 4'd4 || dut.reducer.state == 4'd5 || dut.reducer.state == 4'd6"
    if phase == "finalize_result":
        return "dut.reducer.state == 4'd7 || dut.reducer.state == 4'd8 || dut.reducer.state == 4'd9 || dut.reducer.state == 4'd10"
    raise ValueError(f"unknown phase: {phase}")


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
        f"    q_mem[{index}] = {_signed_literal(q, 8)}; k_mem[{index}] = 64'h{_pack(keys, 8):016x};"
        for index, (q, keys) in enumerate(flat_beats)
    )
    last_indices = {sum(len(block) for block in beats[: index + 1]) - 1 for index in range(len(beats))}
    last_cases = "\n".join(f"      {index}: input_last = 1'b1;" for index in sorted(last_indices))
    value_init = "\n".join(
        f"    value_mem[{block * _VALUE_SLICES + value_slice}] = 512'h"
        f"{_pack([lane for row in values[block][value_slice] for lane in row], 8):0128x};"
        for block in range(block_count)
        for value_slice in range(_VALUE_SLICES)
    )
    phase_active = _phase_expr(phase)
    clock_half_period = clock_period_ns / 2.0
    reducer_dumpvars = "\n".join(
        f"    $dumpvars(0, dut.reducer.numerator_accum[{index}]);"
        for index in range(_REDUCER_NUMERATOR_ACCUM_WORDS)
    )
    score_tile_dumpvars = "\n".join(
        f"    $dumpvars(0, dut.score_tile.accum[{index}]);"
        for index in range(_SCORE_TILE_ACCUM_WORDS)
    )
    return f"""`timescale 1ns/1ps
{_FAKERAM_MODEL}
module tb;
  localparam integer BLOCK_COUNT = {block_count};
  localparam integer HEAD_DIM = {head_dim};
  localparam integer TOTAL_BEATS = {len(flat_beats)};
  reg clk = 0, rst_n = 0;
  reg command_valid, input_valid, input_last;
  wire command_ready, input_ready;
  reg signed [7:0] input_a;
  reg signed [63:0] input_b;
  wire value_read_req_valid, value_response_ready;
  reg value_read_req_ready, value_response_valid;
  wire [13:0] value_read_req_address;
  wire [3:0] value_read_req_slice;
  reg [13:0] value_response_address;
  reg [3:0] value_response_slice;
  reg [511:0] value_response_matrix;
  wire result_valid, result_last;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [3:0] result_slice;
  wire [319:0] result_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  wire protocol_error;
  reg signed [7:0] q_mem [0:TOTAL_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_BEATS-1];
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
      .input_a(input_a), .input_b(input_b),
      .value_read_req_valid(value_read_req_valid), .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address), .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid), .value_response_ready(value_response_ready),
      .value_response_address(value_response_address), .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix), .result_valid(result_valid), .result_ready(result_ready),
      .result_command_id(result_command_id), .result_global_max(result_global_max),
      .result_exp_sum(result_exp_sum), .result_slice(result_slice), .result_last(result_last),
      .result_value(result_value), .accepted_count(accepted_count), .completed_count(completed_count),
      .cycle_count(cycle_count), .protocol_error(protocol_error)
  );

  always @* begin
    command_valid = rst_n && accepted_count == 0;
    input_valid = rst_n && input_index < TOTAL_BEATS;
    input_a = input_index < TOTAL_BEATS ? q_mem[input_index] : 0;
    input_b = input_index < TOTAL_BEATS ? k_mem[input_index] : 0;
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
      if (cycle_count > 40000) $fatal(1, "timeout");
    end
  end

  initial begin
    $dumpfile("{vcd_path.as_posix()}");
    $dumpvars(0, dut);
{reducer_dumpvars}
{score_tile_dumpvars}
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


def _parse_phase_cycles(stdout: str, phase: str) -> tuple[int, int]:
    prefix = f"{_PHASE_DONE_PREFIX} phase={phase} cycles="
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if line.startswith(prefix):
            fields = line[len(prefix) :].split()
            phase_cycles = int(fields[0])
            service_field = next(field for field in fields[1:] if field.startswith("service_cycles="))
            return phase_cycles, int(service_field.split("=", 1)[1])
    raise RuntimeError(f"simulation output missing phase completion for {phase}")


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
) -> tuple[int, int, Path, Path, Path]:
    validated = _validate_request(config=config, block_count=block_count, head_dim=head_dim)
    with tempfile.TemporaryDirectory(prefix=f"decode-score-multivalue-{phase}-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        generate(json.loads(json.dumps(config)), rtl_dir)
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
            raise RuntimeError(f"iverilog failed for {phase}:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(f"simulation failed for {phase}:\n{run.stdout}\n{run.stderr}")
        cycle_count, service_cycles = _parse_phase_cycles(run.stdout, phase)
        phase_out = out_dir / f"{phase}.vcd"
        phase_out.write_bytes(vcd_path.read_bytes())
        sidecar_path = out_dir / f"{phase}_fakeram_macro_pin_vcd_activity_v1.json"
        sidecar = extract_fakeram_vcd_activity(
            phase_out,
            source_vcd_sha256=_sha256_file(phase_out),
            scope="tb/dut",
        )
        sidecar_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sequential_sidecar_path = out_dir / f"{phase}_sequential_register_vcd_activity_v1.json"
        sequential_sidecar = extract_sequential_register_vcd_activity(
            phase_out,
            source_vcd_sha256=_sha256_file(phase_out),
            scope="tb/dut",
        )
        sequential_sidecar_path.write_text(
            json.dumps(sequential_sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return (
            cycle_count,
            service_cycles,
            phase_out,
            sidecar_path,
            sequential_sidecar_path,
        )


def _score_fill_scaling(*, cycle_count: int, block_count: int) -> JsonDict:
    variable_cycles = cycle_count - _COMMAND_SETUP_CYCLES
    if variable_cycles < 0 or variable_cycles % block_count != 0:
        raise RuntimeError("score_fill cycles do not match command-setup plus linear block contract")
    cycles_per_block = variable_cycles // block_count
    return {
        "kind": "fixed_setup_plus_linear_by_block_count",
        "command_setup_cycles": _COMMAND_SETUP_CYCLES,
        "representative_block_count": block_count,
        "cycles_per_block": cycles_per_block,
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "full_context_cycles": _COMMAND_SETUP_CYCLES + cycles_per_block * _TARGET_MAX_BLOCKS,
        "formula": "command_setup_cycles + cycles_per_block * target_max_blocks",
    }


def _replay_value_scaling(*, cycle_count: int, block_count: int) -> JsonDict:
    variable_cycles = cycle_count - _REPLAY_CLEAR_CYCLES
    if variable_cycles < 0 or variable_cycles % block_count != 0:
        raise RuntimeError("replay_value cycles do not match fixed-clear plus linear replay contract")
    replay_cycles_per_block = variable_cycles // block_count
    return {
        "kind": "fixed_clear_plus_linear_by_block_count",
        "clear_cycles": _REPLAY_CLEAR_CYCLES,
        "replay_cycles_per_block": replay_cycles_per_block,
        "representative_block_count": block_count,
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "full_context_cycles": _REPLAY_CLEAR_CYCLES + replay_cycles_per_block * _TARGET_MAX_BLOCKS,
        "formula": "clear_cycles + replay_cycles_per_block * target_max_blocks",
    }


def _finalize_result_scaling(*, cycle_count: int) -> JsonDict:
    expected_cycles = _VALUE_DIMS * _FINALIZE_DIVIDE_CYCLES_PER_DIM + _FINALIZE_RESULT_EMIT_CYCLES
    if cycle_count != expected_cycles:
        raise RuntimeError("finalize_result cycles diverged from expected fixed per-command contract")
    return {
        "kind": "fixed_per_command",
        "value_dimensions": _VALUE_DIMS,
        "divide_cycles_per_dimension": _FINALIZE_DIVIDE_CYCLES_PER_DIM,
        "result_emit_cycles": _FINALIZE_RESULT_EMIT_CYCLES,
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "full_context_cycles": cycle_count,
        "formula": "value_dimensions * divide_cycles_per_dimension + result_emit_cycles",
    }


def generate_phase_activity(
    config: JsonDict,
    out_dir: Path,
    *,
    block_count: int = _DEFAULT_BLOCK_COUNT,
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
        (
            cycle_count,
            service_cycles,
            vcd_path,
            macro_activity_path,
            sequential_register_activity_path,
        ) = _run_phase(
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
            scaling = _finalize_result_scaling(cycle_count=cycle_count)
            full_service_cycles = service_cycles
        phases.append({
            "phase": phase,
            "measured_cycles": cycle_count,
            "full_context_cycles": scaling["full_context_cycles"],
            "vcd": vcd_path.name,
            "vcd_sha256": _sha256_file(vcd_path),
            "macro_activity": macro_activity_path.name,
            "macro_activity_sha256": _sha256_file(macro_activity_path),
            "sequential_register_activity": sequential_register_activity_path.name,
            "sequential_register_activity_sha256": _sha256_file(sequential_register_activity_path),
            "requires_macro_activity": phase in {"score_fill", "replay_value"},
            "scaling": scaling,
        })

    partition_cycles = sum(int(row["measured_cycles"]) for row in phases)
    if partition_cycles != full_service_cycles:
        raise RuntimeError(
            "phase activity does not partition the representative full transaction: "
            f"phases={partition_cycles}, service={full_service_cycles}"
        )

    manifest = {
        "version": 1,
        "model": "decode_score_multivalue_cluster_phase_activity_v1",
        "generator": "npu/eval/generate_attention_decode_score_multivalue_cluster_activity.py",
        "top_name": validated["top_name"],
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_activity_v1",
        "activity_generation": "explicit_script_only",
        "clock_period_ns": clock_period_ns,
        "block_count": block_count,
        "head_dim": head_dim,
        "beats_per_block": head_dim,
        "max_blocks": validated["max_blocks"],
        "target_max_blocks": _TARGET_MAX_BLOCKS,
        "score_multiplier": score_multiplier,
        "score_shift": score_shift,
        "score_scale_lanes_per_cycle": validated["score_scale_lanes_per_cycle"],
        "value_slices": _VALUE_SLICES,
        "value_dimensions": _VALUE_DIMS,
        "representative_full_transaction_cycles": full_service_cycles,
        "phase_partition_cycle_sum": partition_cycles,
        "phases": phases,
    }
    manifest_path = out_dir / "attention_decode_score_multivalue_cluster_activity_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--block-count", type=int, default=_DEFAULT_BLOCK_COUNT)
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
