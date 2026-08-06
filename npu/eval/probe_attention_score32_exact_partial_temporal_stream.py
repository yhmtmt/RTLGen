#!/usr/bin/env python3
"""Probe the finite-buffered exact-partial temporal stream reducer."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream import generate
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    ExactPartialWindowRecord,
    VALUE_SLICES,
    merge_ordered_exact_partial_temporal_stream,
    pack_numerators,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_partial_temporal_stream"
_MANIFEST_NAME = "attention_score32_exact_partial_temporal_stream_manifest.json"
_OUT_RE = re.compile(
    r"OUT sequence=(\d+) head=(\d+) window_count=(\d+) command=(\d+) "
    r"max=(-?\d+) exp=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY cycles=(\d+) sent=(\d+) outputs=(\d+) protocol_error=(\d+) "
    r"input_stalls=(\d+) fifo_full_stalls=(\d+) output_stalls=(\d+) "
    r"input_accepted=(\d+) merge_completed=(\d+) emitted=(\d+) completed_heads=(\d+)"
)


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"config must decode to a JSON object: {path}")
    return payload


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _window(
    *,
    sequence_id: int,
    command_id: int,
    head_id: int,
    window_index: int,
    window_count: int,
) -> ExactPartialWindowRecord:
    beats: list[ExactPartialBeat] = []
    for slice_index in range(VALUE_SLICES):
        numerators = tuple(
            ((head_id + 1) * 1000)
            + ((window_index + 1) * 100)
            + (slice_index * 9)
            + lane
            for lane in range(8)
        )
        beats.append(
            ExactPartialBeat(
                command_id=command_id,
                head_id=head_id,
                slice_index=slice_index,
                last=slice_index == VALUE_SLICES - 1,
                max_score=2000 + (head_id * 31) + (window_index * 7) + slice_index,
                exp_sum=40 + (head_id * 3) + window_index + slice_index,
                numerators=numerators,
            )
        )
    return ExactPartialWindowRecord(
        sequence_id=sequence_id,
        head_id=head_id,
        window_index=window_index,
        window_count=window_count,
        beats=tuple(beats),
    )


def _records(*, heads: int, windows: int, sequence_id: int) -> tuple[ExactPartialWindowRecord, ...]:
    records: list[ExactPartialWindowRecord] = []
    for window_index in range(windows):
        for head_id in range(heads):
            records.append(
                _window(
                    sequence_id=sequence_id,
                    command_id=0x7200 + head_id,
                    head_id=head_id,
                    window_index=window_index,
                    window_count=windows,
                )
            )
    return tuple(records)


def _rows_from_records(records: tuple[ExactPartialWindowRecord, ...]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for record in records:
        for beat in record.beats:
            rows.append(
                {
                    "sequence_id": record.sequence_id,
                    "head_id": record.head_id,
                    "window_index": record.window_index,
                    "window_count": record.window_count,
                    "command_id": beat.command_id,
                    "global_max": beat.max_score,
                    "exp_sum": beat.exp_sum,
                    "slice": beat.slice_index,
                    "last": 1 if beat.last else 0,
                    "value": pack_numerators(beat.numerators),
                }
            )
    return rows


def _expected_rows(records: tuple[ExactPartialWindowRecord, ...]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for result in merge_ordered_exact_partial_temporal_stream(records):
        for beat in result.beats:
            rows.append(
                {
                    "sequence_id": result.sequence_id,
                    "head_id": result.head_id,
                    "window_count": result.window_count,
                    "command_id": beat.command_id,
                    "global_max": beat.max_score,
                    "exp_sum": beat.exp_sum,
                    "slice": beat.slice_index,
                    "last": 1 if beat.last else 0,
                    "value": pack_numerators(beat.numerators),
                }
            )
    return rows


def _verilog_int(value: int, bits: int, *, signed: bool = False) -> str:
    if signed:
        if value < 0:
            return f"-{bits}'sd{abs(value)}"
        return f"{bits}'sd{value}"
    return f"{bits}'d{value}"


def _array_initializers(name: str, rows: list[dict[str, int]], key: str, bits: int, *, signed: bool = False) -> str:
    return "\n".join(
        f"    {name}[{index}] = {_verilog_int(int(row[key]), bits, signed=signed)};" for index, row in enumerate(rows)
    )


def _array_hex_initializers(name: str, rows: list[dict[str, int]], key: str, bits: int) -> str:
    hex_digits = (bits + 3) // 4
    return "\n".join(f"    {name}[{index}] = {bits}'h{int(row[key]):0{hex_digits}x};" for index, row in enumerate(rows))


def _tb(*, top_name: str, rows: list[dict[str, int]], expected_outputs: int, stress: bool, expect_error: bool) -> str:
    input_count = len(rows)
    last_index = max(0, input_count - 1)
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer INPUT_COUNT = {input_count};
  localparam integer EXPECTED_OUTPUTS = {expected_outputs};
  localparam integer STRESS = {1 if stress else 0};
  localparam integer EXPECT_ERROR = {1 if expect_error else 0};
  localparam integer HEAD_ID_BITS = 5;
  localparam integer SLICE_BITS = 4;
  localparam integer PARTIAL_PAYLOAD_BITS = 328;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg [15:0] sequence_mem [0:INPUT_COUNT-1];
  reg [HEAD_ID_BITS-1:0] head_mem [0:INPUT_COUNT-1];
  reg [13:0] window_index_mem [0:INPUT_COUNT-1];
  reg [14:0] window_count_mem [0:INPUT_COUNT-1];
  reg [15:0] command_mem [0:INPUT_COUNT-1];
  reg signed [31:0] max_mem [0:INPUT_COUNT-1];
  reg [32:0] exp_mem [0:INPUT_COUNT-1];
  reg [SLICE_BITS-1:0] slice_mem [0:INPUT_COUNT-1];
  reg last_mem [0:INPUT_COUNT-1];
  reg [PARTIAL_PAYLOAD_BITS-1:0] value_mem [0:INPUT_COUNT-1];

  integer send_index = 0;
  integer output_count = 0;
  integer input_stalls = 0;
  integer tb_cycle = 0;

  initial begin
{_array_initializers("sequence_mem", rows, "sequence_id", 16)}
{_array_initializers("head_mem", rows, "head_id", 5)}
{_array_initializers("window_index_mem", rows, "window_index", 14)}
{_array_initializers("window_count_mem", rows, "window_count", 15)}
{_array_initializers("command_mem", rows, "command_id", 16)}
{_array_initializers("max_mem", rows, "global_max", 32, signed=True)}
{_array_initializers("exp_mem", rows, "exp_sum", 33)}
{_array_initializers("slice_mem", rows, "slice", 4)}
{_array_initializers("last_mem", rows, "last", 1)}
{_array_hex_initializers("value_mem", rows, "value", 328)}
    repeat (5) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end

  wire [31:0] send_index_safe = (send_index < INPUT_COUNT) ? send_index[31:0] : 32'd{last_index};

  wire source_enable = !STRESS || ((tb_cycle % 7) != 3);
  wire in_valid = rst_n && (send_index < INPUT_COUNT) && source_enable;
  wire in_ready;
  wire [15:0] in_sequence_id = sequence_mem[send_index_safe];
  wire [HEAD_ID_BITS-1:0] in_head_id = head_mem[send_index_safe];
  wire [13:0] in_window_index = window_index_mem[send_index_safe];
  wire [14:0] in_window_count = window_count_mem[send_index_safe];
  wire [15:0] in_command_id = command_mem[send_index_safe];
  wire signed [31:0] in_global_max = max_mem[send_index_safe];
  wire [32:0] in_exp_sum = exp_mem[send_index_safe];
  wire [SLICE_BITS-1:0] in_slice = slice_mem[send_index_safe];
  wire in_last = last_mem[send_index_safe];
  wire [PARTIAL_PAYLOAD_BITS-1:0] in_value = value_mem[send_index_safe];

  wire out_valid;
  wire out_ready = !STRESS || (((tb_cycle % 11) != 2) && ((tb_cycle % 11) != 3) && ((tb_cycle % 11) != 7));
  wire [15:0] out_sequence_id;
  wire [HEAD_ID_BITS-1:0] out_head_id;
  wire [14:0] out_window_count;
  wire [15:0] out_command_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [SLICE_BITS-1:0] out_slice;
  wire out_last;
  wire [PARTIAL_PAYLOAD_BITS-1:0] out_value;
  wire [31:0] dut_cycle_count;
  wire [31:0] input_accepted_count;
  wire [31:0] merge_completed_count;
  wire [31:0] emitted_beat_count;
  wire [31:0] completed_head_count;
  wire [31:0] fifo_full_stall_cycles;
  wire [31:0] output_stall_cycles;
  wire [2:0] fifo_level;
  wire protocol_error;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(in_valid),
      .in_ready(in_ready),
      .in_sequence_id(in_sequence_id),
      .in_head_id(in_head_id),
      .in_window_index(in_window_index),
      .in_window_count(in_window_count),
      .in_command_id(in_command_id),
      .in_global_max(in_global_max),
      .in_exp_sum(in_exp_sum),
      .in_slice(in_slice),
      .in_last(in_last),
      .in_value(in_value),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_sequence_id(out_sequence_id),
      .out_head_id(out_head_id),
      .out_window_count(out_window_count),
      .out_command_id(out_command_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .cycle_count(dut_cycle_count),
      .input_accepted_count(input_accepted_count),
      .merge_completed_count(merge_completed_count),
      .emitted_beat_count(emitted_beat_count),
      .completed_head_count(completed_head_count),
      .fifo_full_stall_cycles(fifo_full_stall_cycles),
      .output_stall_cycles(output_stall_cycles),
      .fifo_level(fifo_level),
      .protocol_error(protocol_error)
  );

  always @(posedge clk) begin
    if (rst_n) begin
      tb_cycle <= tb_cycle + 1;
      if (in_valid && !in_ready) input_stalls <= input_stalls + 1;
      if (in_valid && in_ready) send_index <= send_index + 1;
      if (out_valid && out_ready) begin
        $display("OUT sequence=%0d head=%0d window_count=%0d command=%0d max=%0d exp=%0d slice=%0d last=%0d value=%0h",
                 out_sequence_id, out_head_id, out_window_count, out_command_id,
                 out_global_max, out_exp_sum, out_slice, out_last, out_value);
        output_count <= output_count + 1;
      end
      if ((EXPECT_ERROR && protocol_error) || (!EXPECT_ERROR && output_count == EXPECTED_OUTPUTS)) begin
        $display("SUMMARY cycles=%0d sent=%0d outputs=%0d protocol_error=%0d input_stalls=%0d fifo_full_stalls=%0d output_stalls=%0d input_accepted=%0d merge_completed=%0d emitted=%0d completed_heads=%0d",
                 tb_cycle, send_index, output_count, protocol_error, input_stalls,
                 fifo_full_stall_cycles, output_stall_cycles, input_accepted_count,
                 merge_completed_count, emitted_beat_count, completed_head_count);
        $finish;
      end
      if (tb_cycle > 5000) begin
        $display("SUMMARY cycles=%0d sent=%0d outputs=%0d protocol_error=%0d input_stalls=%0d fifo_full_stalls=%0d output_stalls=%0d input_accepted=%0d merge_completed=%0d emitted=%0d completed_heads=%0d",
                 tb_cycle, send_index, output_count, protocol_error, input_stalls,
                 fifo_full_stall_cycles, output_stall_cycles, input_accepted_count,
                 merge_completed_count, emitted_beat_count, completed_head_count);
        $fatal(1, "timeout");
      end
    end
  end
endmodule
"""


def _parse_stdout(stdout: str) -> tuple[list[dict[str, int]], dict[str, int]]:
    observed: list[dict[str, int]] = []
    summary: dict[str, int] | None = None
    for line in stdout.splitlines():
        out_match = _OUT_RE.search(line)
        if out_match:
            observed.append(
                {
                    "sequence_id": int(out_match.group(1)),
                    "head_id": int(out_match.group(2)),
                    "window_count": int(out_match.group(3)),
                    "command_id": int(out_match.group(4)),
                    "global_max": int(out_match.group(5)),
                    "exp_sum": int(out_match.group(6)),
                    "slice": int(out_match.group(7)),
                    "last": int(out_match.group(8)),
                    "value": int(out_match.group(9), 16),
                }
            )
        summary_match = _SUMMARY_RE.search(line)
        if summary_match:
            keys = (
                "cycles",
                "sent",
                "outputs",
                "protocol_error",
                "input_stalls",
                "fifo_full_stalls",
                "output_stalls",
                "input_accepted",
                "merge_completed",
                "emitted",
                "completed_heads",
            )
            summary = {key: int(value) for key, value in zip(keys, summary_match.groups(), strict=True)}
    if summary is None:
        raise RuntimeError(f"simulation did not print SUMMARY\n{stdout}")
    return observed, summary


def build_report(
    *,
    config: JsonDict,
    stress_interfaces: bool = False,
    order_violation: bool = False,
) -> JsonDict:
    defaults = config.get("probe_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    heads = int(defaults.get("heads", 2))
    windows = int(defaults.get("windows", 3))
    sequence_id = int(defaults.get("sequence_id", 9))
    if heads != 2 or windows != 3:
        raise ValueError("probe is intentionally fixed to 2 interleaved heads x 3 windows")

    records = _records(heads=heads, windows=windows, sequence_id=sequence_id)
    rows = _rows_from_records(records)
    expected = _expected_rows(records)
    if order_violation:
        rows[1] = dict(rows[1])
        rows[1]["slice"] = 2

    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_temporal_stream_probe_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        rtl_dir = temp_dir / "rtl"
        generate(config, rtl_dir)
        tb_path = temp_dir / "tb.v"
        tb_path.write_text(
            _tb(
                top_name=str(config["top_name"]),
                rows=rows,
                expected_outputs=len(expected),
                stress=stress_interfaces,
                expect_error=order_violation,
            ),
            encoding="utf-8",
        )
        simv = temp_dir / "simv"
        compile_cmd = [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tb_path),
            str(rtl_dir / "top.v"),
        ]
        compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=180)
        if compile_proc.returncode != 0:
            raise RuntimeError(compile_proc.stderr)
        sim_proc = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=180)
        if sim_proc.returncode != 0:
            raise RuntimeError(sim_proc.stdout + sim_proc.stderr)
        observed, summary = _parse_stdout(sim_proc.stdout)
        manifest = json.loads((rtl_dir / _MANIFEST_NAME).read_text(encoding="utf-8"))

    passed = bool(summary["protocol_error"]) if order_violation else (observed == expected and not summary["protocol_error"])
    return {
        "model": "attention_score32_exact_partial_temporal_stream_probe_v1",
        "passed": passed,
        "interface_mode": "stress" if stress_interfaces else "ideal",
        "order_violation": order_violation,
        "heads": heads,
        "windows": windows,
        "inputs": len(rows),
        "expected_outputs": 0 if order_violation else len(expected),
        "outputs": summary["outputs"],
        "observed_rows": observed,
        "expected_rows": [] if order_violation else expected,
        "summary": summary,
        "manifest": manifest,
        "remaining_abstractions": [
            "upstream_service_command_metadata_binding",
            "service_to_temporal_reducer_clock_domain_crossing",
            "downstream_full_context_final_normalizer",
            "physical_sram_macro_mapping_for_persistent_state",
            "physical_ppa",
        ],
    }


def _markdown(report: JsonDict) -> str:
    summary = report["summary"]
    return "\n".join(
        [
            "# attention_score32_exact_partial_temporal_stream",
            "",
            f"- passed: `{report['passed']}`",
            f"- interface_mode: `{report['interface_mode']}`",
            f"- order_violation: `{report['order_violation']}`",
            f"- inputs: `{report['inputs']}`",
            f"- outputs: `{report['outputs']}`",
            f"- expected_outputs: `{report['expected_outputs']}`",
            f"- protocol_error: `{bool(summary['protocol_error'])}`",
            f"- fifo_full_stalls: `{summary['fifo_full_stalls']}`",
            f"- output_stalls: `{summary['output_stalls']}`",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--stress-interfaces", action="store_true")
    parser.add_argument("--order-violation", action="store_true")
    args = parser.parse_args()
    report = build_report(
        config=_load(args.config),
        stress_interfaces=args.stress_interfaces,
        order_violation=args.order_violation,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.out.with_suffix(".md").write_text(_markdown(report) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
