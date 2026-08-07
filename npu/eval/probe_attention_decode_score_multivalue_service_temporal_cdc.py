#!/usr/bin/env python3
"""Probe real c1 exact-partial service across the temporal async FIFO."""

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

from npu.eval import probe_attention_decode_score_multivalue_integrated_service as service_probe
from npu.eval import probe_attention_decode_score_multivalue_service_temporal as prior_probe
from npu.rtlgen.gen_attention_decode_score_multivalue_service_temporal_cdc import (
    generate,
)

JsonDict = dict[str, Any]

_MANIFEST = "attention_decode_score_multivalue_service_temporal_cdc_manifest.json"
_OUT_RE = re.compile(
    r"OUT sequence=(\d+) head=(\d+) count=(\d+) command=(\d+) max=(-?\d+) "
    r"sum=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY service_cycles=(\d+) temporal_cycles=(\d+) commands=(\d+) "
    r"second_refused=(\d+) first_terminal=(-?\d+) second_accept=(-?\d+) "
    r"outputs=(\d+) stable=(\d+) cdc_accepted=(\d+) cdc_emitted=(\d+) "
    r"cdc_full=(\d+) cdc_empty=(\d+) overflow=(\d+) underflow=(\d+) "
    r"cdc_wr_error=(\d+) cdc_rd_error=(\d+) wrapper_error=(\d+) "
    r"service_error=(\d+) temporal_error=(\d+) protocol_error=(\d+) "
    r"service_accepted=(\d+) service_completed=(\d+) service_req=(\d+) "
    r"service_resp=(\d+) temporal_inputs=(\d+) temporal_merges=(\d+) "
    r"temporal_emitted=(\d+) temporal_heads=(\d+) output_stalls=(\d+)"
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config(top_name: str, *, cdc_depth: int) -> JsonDict:
    workload = service_probe._workload_contract()
    return {
        "top_name": top_name,
        "attention_decode_score_multivalue_service_temporal_cdc": {
            "cdc_fifo_depth": cdc_depth,
            "service": {
                "cluster_count": 1,
                "max_blocks": int(workload["max_blocks"]),
                "packet_w": 128,
                "banks": 2,
                "req_queue_depth": 2,
                "resp_queue_depth": 2,
                "bank_queue_depth": 2,
                "read_latency": 1,
                "arb_mode": "round_robin",
                "locality_burst_max": 2,
                "score_scale_lanes_per_cycle": 1,
                "result_mode": "exact_partial",
                "head_id_bits": 5,
                "value_memory_backend": "behavioral",
            },
            "temporal_stream": {
                "fifo_depth": 4,
                "exp_scale_impl": "factored_h33_l64_mul_exact",
                "keep_hierarchy": True,
            },
        },
    }


def _testbench(
    *,
    top_name: str,
    service_period_ns: float,
    temporal_period_ns: float,
    mismatch_metadata: bool,
) -> str:
    if service_period_ns <= 0 or temporal_period_ns <= 0:
        raise ValueError("clock periods must be positive")
    values = service_probe._shared_value_matrices()
    entries = service_probe._preload_entries(values)
    workload = service_probe._workload_contract()
    beats_per_window = int(
        service_probe._workload_expected_counts(workload)["input_beat_count"]
    )
    all_beats = [
        beat
        for window_index in range(2)
        for block in service_probe._cluster_beats(window_index)
        for beat in block
    ]
    preload_init = "\n".join(
        "    preload_addr_mem[{0}] = 14'd{1}; preload_slice_mem[{0}] = 4'd{2}; "
        "preload_matrix_mem[{0}] = 512'h{3};".format(
            index, entry["addr"], entry["slice"], entry["matrix_hex"]
        )
        for index, entry in enumerate(entries)
    )
    input_init = "\n".join(
        "    q_mem[{0}] = {1}; k_mem[{0}] = 64'h{2:016x};".format(
            index,
            service_probe._signed_literal(query, 8),
            service_probe._pack(keys, 8),
        )
        for index, (query, keys) in enumerate(all_beats)
    )
    mismatch_block = (
        """
      if (!mismatch_injected && cluster_command_valid && cluster_command_ready) begin
        force dut.u_service.shared_result_command_id_q = 16'hdead;
        mismatch_injected <= 1'b1;
      end
"""
        if mismatch_metadata
        else ""
    )
    completion = "wrapper_protocol_error" if mismatch_metadata else "output_count == 16"
    return f"""`timescale 1ns/1ps
{service_probe._FAKERAM_MODEL}
module tb;
  localparam integer PRELOAD_COUNT = {len(entries)};
  localparam integer BEATS_PER_WINDOW = {beats_per_window};
  localparam integer TOTAL_INPUT_BEATS = {len(all_beats)};

  reg service_clk = 1'b0;
  reg temporal_clk = 1'b0;
  reg service_rst_n = 1'b0;
  reg temporal_rst_n = 1'b0;
  always #{service_period_ns / 2.0:g} service_clk = ~service_clk;
  always #{temporal_period_ns / 2.0:g} temporal_clk = ~temporal_clk;

  reg preload_valid;
  wire preload_ready;
  reg [13:0] preload_addr;
  reg [3:0] preload_value_slice;
  reg [511:0] preload_matrix;
  reg [13:0] preload_addr_mem [0:PRELOAD_COUNT-1];
  reg [3:0] preload_slice_mem [0:PRELOAD_COUNT-1];
  reg [511:0] preload_matrix_mem [0:PRELOAD_COUNT-1];
  reg signed [7:0] q_mem [0:TOTAL_INPUT_BEATS-1];
  reg [63:0] k_mem [0:TOTAL_INPUT_BEATS-1];

  reg cluster_command_valid;
  wire cluster_command_ready;
  reg [15:0] cluster_command_id;
  reg [15:0] cluster_logical_sequence_id;
  reg [15:0] cluster_logical_command_id;
  reg [13:0] cluster_window_index;
  reg [14:0] cluster_window_count;
  reg [14:0] cluster_command_block_count;
  reg [4:0] cluster_command_head_id;
  reg [31:0] cluster_command_score_multiplier;
  reg [5:0] cluster_command_score_shift;
  reg cluster_input_valid;
  wire cluster_input_ready;
  reg cluster_input_last;
  reg [7:0] cluster_input_a;
  reg [63:0] cluster_input_b;

  wire out_valid;
  wire out_ready;
  wire [15:0] out_sequence_id;
  wire [4:0] out_head_id;
  wire [14:0] out_window_count;
  wire [15:0] out_command_id;
  wire signed [31:0] out_global_max;
  wire [32:0] out_exp_sum;
  wire [3:0] out_slice;
  wire out_last;
  wire [327:0] out_value;
  wire cluster_metadata_busy;
  wire service_shared_result_valid;
  wire service_shared_result_ready;
  wire service_shared_result_last;
  wire [31:0] service_cluster_accepted_count;
  wire [31:0] service_cluster_completed_count;
  wire service_cluster_protocol_error;
  wire [31:0] service_accepted_req_count;
  wire [31:0] service_emitted_resp_count;
  wire [31:0] temporal_input_accepted_count;
  wire [31:0] temporal_merge_completed_count;
  wire [31:0] temporal_emitted_beat_count;
  wire [31:0] temporal_completed_head_count;
  wire [31:0] temporal_output_stall_cycles;
  wire [31:0] cdc_accepted_count;
  wire [31:0] cdc_emitted_count;
  wire [31:0] cdc_full_cycles;
  wire [31:0] cdc_empty_cycles;
  wire cdc_overflow_error;
  wire cdc_underflow_error;
  wire cdc_write_protocol_error;
  wire cdc_read_protocol_error;
  wire wrapper_protocol_error;
  wire service_protocol_error;
  wire temporal_protocol_error;
  wire protocol_error;

  integer service_cycle;
  integer temporal_cycle;
  integer preload_index;
  integer command_count;
  integer active_window;
  integer input_index;
  integer second_refused_cycles;
  integer first_terminal_cycle;
  integer second_accept_cycle;
  integer output_count;
  reg preload_done;
  reg input_active;
  reg mismatch_injected;
  reg blocked_output_valid;
  reg stable_output_seen;
  reg summary_done;
  reg [463:0] blocked_output;

  assign out_ready = temporal_rst_n &&
      (((temporal_cycle % 11) != 2) && ((temporal_cycle % 11) != 3) &&
       ((temporal_cycle % 11) != 7));

  {top_name} dut (
      .service_clk(service_clk),
      .service_rst_n(service_rst_n),
      .temporal_clk(temporal_clk),
      .temporal_rst_n(temporal_rst_n),
      .preload_valid(preload_valid),
      .preload_ready(preload_ready),
      .preload_addr(preload_addr),
      .preload_value_slice(preload_value_slice),
      .preload_matrix(preload_matrix),
      .cluster_command_valid(cluster_command_valid),
      .cluster_command_ready(cluster_command_ready),
      .cluster_command_id(cluster_command_id),
      .cluster_logical_sequence_id(cluster_logical_sequence_id),
      .cluster_logical_command_id(cluster_logical_command_id),
      .cluster_window_index(cluster_window_index),
      .cluster_window_count(cluster_window_count),
      .cluster_command_block_count(cluster_command_block_count),
      .cluster_command_head_id(cluster_command_head_id),
      .cluster_command_score_multiplier(cluster_command_score_multiplier),
      .cluster_command_score_shift(cluster_command_score_shift),
      .cluster_input_valid(cluster_input_valid),
      .cluster_input_ready(cluster_input_ready),
      .cluster_input_last(cluster_input_last),
      .cluster_input_a(cluster_input_a),
      .cluster_input_b(cluster_input_b),
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
      .cluster_metadata_busy(cluster_metadata_busy),
      .service_shared_result_valid(service_shared_result_valid),
      .service_shared_result_ready(service_shared_result_ready),
      .service_shared_result_last(service_shared_result_last),
      .service_cluster_accepted_count(service_cluster_accepted_count),
      .service_cluster_completed_count(service_cluster_completed_count),
      .service_cluster_protocol_error(service_cluster_protocol_error),
      .service_accepted_req_count(service_accepted_req_count),
      .service_emitted_resp_count(service_emitted_resp_count),
      .temporal_input_accepted_count(temporal_input_accepted_count),
      .temporal_merge_completed_count(temporal_merge_completed_count),
      .temporal_emitted_beat_count(temporal_emitted_beat_count),
      .temporal_completed_head_count(temporal_completed_head_count),
      .temporal_output_stall_cycles(temporal_output_stall_cycles),
      .cdc_accepted_count(cdc_accepted_count),
      .cdc_emitted_count(cdc_emitted_count),
      .cdc_full_cycles(cdc_full_cycles),
      .cdc_empty_cycles(cdc_empty_cycles),
      .cdc_overflow_error(cdc_overflow_error),
      .cdc_underflow_error(cdc_underflow_error),
      .cdc_write_protocol_error(cdc_write_protocol_error),
      .cdc_read_protocol_error(cdc_read_protocol_error),
      .wrapper_protocol_error(wrapper_protocol_error),
      .service_protocol_error(service_protocol_error),
      .temporal_protocol_error(temporal_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    preload_valid = service_rst_n && !preload_done;
    preload_addr = preload_done ? 14'd0 : preload_addr_mem[preload_index];
    preload_value_slice = preload_done ? 4'd0 : preload_slice_mem[preload_index];
    preload_matrix = preload_done ? 512'd0 : preload_matrix_mem[preload_index];
    cluster_command_valid =
        service_rst_n && preload_done && (command_count < 2);
    cluster_command_id = (command_count == 0)
        ? 16'h{prior_probe.PHYSICAL_COMMAND_IDS[0]:04x}
        : 16'h{prior_probe.PHYSICAL_COMMAND_IDS[1]:04x};
    cluster_logical_sequence_id = 16'h{prior_probe.SEQUENCE_ID:04x};
    cluster_logical_command_id = 16'h{prior_probe.LOGICAL_COMMAND_ID:04x};
    cluster_window_index = command_count[13:0];
    cluster_window_count = 15'd2;
    cluster_command_block_count = 15'd{int(workload["command_block_count"])};
    cluster_command_head_id = 5'd{prior_probe.HEAD_ID};
    cluster_command_score_multiplier = 32'd1;
    cluster_command_score_shift = 6'd0;
    cluster_input_valid = service_rst_n && input_active;
    cluster_input_a = input_active
        ? q_mem[(active_window * BEATS_PER_WINDOW) + input_index] : 8'd0;
    cluster_input_b = input_active
        ? k_mem[(active_window * BEATS_PER_WINDOW) + input_index] : 64'd0;
    cluster_input_last =
        input_active && (((input_index + 1) % 128) == 0);
  end

  always @(posedge service_clk or negedge service_rst_n) begin
    if (!service_rst_n) begin
      service_cycle <= 0;
      preload_index <= 0;
      preload_done <= 1'b0;
      command_count <= 0;
      active_window <= 0;
      input_index <= 0;
      input_active <= 1'b0;
      second_refused_cycles <= 0;
      first_terminal_cycle <= -1;
      second_accept_cycle <= -1;
      mismatch_injected <= 1'b0;
    end else begin
      service_cycle <= service_cycle + 1;
      if (!preload_done && preload_valid && preload_ready) begin
        if (preload_index == PRELOAD_COUNT - 1)
          preload_done <= 1'b1;
        else
          preload_index <= preload_index + 1;
      end
      if (cluster_command_valid && cluster_command_ready) begin
        if (command_count == 1) second_accept_cycle <= service_cycle;
        active_window <= command_count;
        input_index <= 0;
        input_active <= 1'b1;
        command_count <= command_count + 1;
      end
      if ((command_count == 1) && cluster_command_valid &&
          !cluster_command_ready && cluster_metadata_busy)
        second_refused_cycles <= second_refused_cycles + 1;
      if (cluster_input_valid && cluster_input_ready) begin
        if (input_index == BEATS_PER_WINDOW - 1)
          input_active <= 1'b0;
        else
          input_index <= input_index + 1;
      end
      if ((first_terminal_cycle < 0) && service_shared_result_valid &&
          service_shared_result_ready && service_shared_result_last)
        first_terminal_cycle <= service_cycle;
{mismatch_block}
      if (service_cycle > 160000) $fatal(1, "service-side timeout");
    end
  end

  always @(posedge temporal_clk or negedge temporal_rst_n) begin
    if (!temporal_rst_n) begin
      temporal_cycle <= 0;
      output_count <= 0;
      blocked_output_valid <= 1'b0;
      stable_output_seen <= 1'b0;
      blocked_output <= 464'd0;
      summary_done <= 1'b0;
    end else begin
      temporal_cycle <= temporal_cycle + 1;
      if (out_valid && !out_ready) begin
        if (!blocked_output_valid) begin
          blocked_output_valid <= 1'b1;
          blocked_output <= {{
              out_sequence_id, out_head_id, out_window_count, out_command_id,
              out_global_max, out_exp_sum, out_slice, out_last, out_value
          }};
        end else begin
          if ({{out_sequence_id, out_head_id, out_window_count, out_command_id,
                out_global_max, out_exp_sum, out_slice, out_last, out_value}}
              !== blocked_output)
            $fatal(1, "temporal output changed under backpressure");
          stable_output_seen <= 1'b1;
        end
      end else begin
        blocked_output_valid <= 1'b0;
      end
      if (out_valid && out_ready) begin
        $display("OUT sequence=%0d head=%0d count=%0d command=%0d max=%0d sum=%0d slice=%0d last=%0d value=%082x",
                 out_sequence_id, out_head_id, out_window_count, out_command_id,
                 $signed(out_global_max), out_exp_sum, out_slice, out_last,
                 out_value);
        output_count <= output_count + 1;
      end
      if (!summary_done && ({completion})) begin
        summary_done <= 1'b1;
        $display("SUMMARY service_cycles=%0d temporal_cycles=%0d commands=%0d second_refused=%0d first_terminal=%0d second_accept=%0d outputs=%0d stable=%0d cdc_accepted=%0d cdc_emitted=%0d cdc_full=%0d cdc_empty=%0d overflow=%0d underflow=%0d cdc_wr_error=%0d cdc_rd_error=%0d wrapper_error=%0d service_error=%0d temporal_error=%0d protocol_error=%0d service_accepted=%0d service_completed=%0d service_req=%0d service_resp=%0d temporal_inputs=%0d temporal_merges=%0d temporal_emitted=%0d temporal_heads=%0d output_stalls=%0d",
                 service_cycle, temporal_cycle, command_count,
                 second_refused_cycles, first_terminal_cycle,
                 second_accept_cycle, output_count, stable_output_seen,
                 cdc_accepted_count, cdc_emitted_count, cdc_full_cycles,
                 cdc_empty_cycles, cdc_overflow_error, cdc_underflow_error,
                 cdc_write_protocol_error, cdc_read_protocol_error,
                 wrapper_protocol_error, service_protocol_error,
                 temporal_protocol_error, protocol_error,
                 service_cluster_accepted_count,
                 service_cluster_completed_count, service_accepted_req_count,
                 service_emitted_resp_count, temporal_input_accepted_count,
                 temporal_merge_completed_count, temporal_emitted_beat_count,
                 temporal_completed_head_count, temporal_output_stall_cycles);
        $finish;
      end
      if (temporal_cycle > 220000) $fatal(1, "temporal-side timeout");
    end
  end

  initial begin
{preload_init}
{input_init}
    repeat (4) @(posedge service_clk);
    @(negedge service_clk);
    service_rst_n = 1'b1;
    #{service_period_ns * 1.3:g};
    temporal_rst_n = 1'b1;
  end
endmodule
"""


def _parse(stdout: str) -> tuple[list[JsonDict], JsonDict]:
    rows: list[JsonDict] = []
    summary: JsonDict | None = None
    for line in stdout.splitlines():
        if match := _OUT_RE.fullmatch(line.strip()):
            rows.append(
                {
                    "sequence_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "window_count": int(match.group(3)),
                    "command_id": int(match.group(4)),
                    "global_max": int(match.group(5)),
                    "exp_sum": int(match.group(6)),
                    "slice": int(match.group(7)),
                    "last": int(match.group(8)),
                    "value": int(match.group(9), 16),
                }
            )
        if match := _SUMMARY_RE.fullmatch(line.strip()):
            keys = (
                "service_cycles",
                "temporal_cycles",
                "commands",
                "second_refused",
                "first_terminal",
                "second_accept",
                "outputs",
                "stable",
                "cdc_accepted",
                "cdc_emitted",
                "cdc_full",
                "cdc_empty",
                "overflow",
                "underflow",
                "cdc_wr_error",
                "cdc_rd_error",
                "wrapper_error",
                "service_error",
                "temporal_error",
                "protocol_error",
                "service_accepted",
                "service_completed",
                "service_req",
                "service_resp",
                "temporal_inputs",
                "temporal_merges",
                "temporal_emitted",
                "temporal_heads",
                "output_stalls",
            )
            summary = {
                key: int(value)
                for key, value in zip(keys, match.groups(), strict=True)
            }
    if summary is None:
        raise RuntimeError(f"simulation did not emit SUMMARY\n{stdout}")
    return rows, summary


def build_report(
    *,
    service_period_ns: float = 10.0,
    temporal_period_ns: float = 7.0,
    cdc_depth: int = 4,
    mismatch_metadata: bool = False,
) -> JsonDict:
    top_name = "attention_decode_score_multivalue_service_temporal_cdc_probe"
    config = _config(top_name, cdc_depth=cdc_depth)
    expected = [] if mismatch_metadata else prior_probe._expected_rows()
    with tempfile.TemporaryDirectory(prefix="decode-service-temporal-cdc-probe-") as name:
        temp = Path(name)
        rtl_dir = temp / "rtl"
        generate(config, rtl_dir)
        tb_path = temp / "tb.sv"
        tb_path.write_text(
            _testbench(
                top_name=top_name,
                service_period_ns=service_period_ns,
                temporal_period_ns=temporal_period_ns,
                mismatch_metadata=mismatch_metadata,
            ),
            encoding="utf-8",
        )
        simv = temp / "simv"
        compile_run = subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(simv),
                str(rtl_dir / "top.v"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if compile_run.returncode:
            raise RuntimeError(f"iverilog failed:\n{compile_run.stderr}")
        sim_run = subprocess.run(
            [_tool("vvp"), str(simv)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if sim_run.returncode:
            raise RuntimeError(
                f"simulation failed:\n{sim_run.stdout}\n{sim_run.stderr}"
            )
        observed, summary = _parse(sim_run.stdout)
        manifest = json.loads(
            (rtl_dir / _MANIFEST).read_text(encoding="utf-8")
        )

    error_free = all(
        summary[key] == 0
        for key in (
            "overflow",
            "underflow",
            "cdc_wr_error",
            "cdc_rd_error",
            "service_error",
            "temporal_error",
        )
    )
    if mismatch_metadata:
        passed = (
            not observed
            and summary["wrapper_error"] == 1
            and summary["protocol_error"] == 1
            and summary["cdc_accepted"] == 0
            and summary["temporal_inputs"] == 0
            and error_free
        )
    else:
        passed = (
            observed == expected
            and len(observed) == 16
            and summary["commands"] == 2
            and summary["second_refused"] > 0
            and summary["first_terminal"] >= 0
            and summary["second_accept"] > summary["first_terminal"]
            and summary["stable"] == 1
            and summary["wrapper_error"] == 0
            and summary["protocol_error"] == 0
            and summary["service_accepted"] == 2
            and summary["service_completed"] == 2
            and summary["service_req"] == 96
            and summary["service_resp"] == 96
            and summary["cdc_accepted"] == 32
            and summary["cdc_emitted"] == 32
            and summary["temporal_inputs"] == 32
            and summary["temporal_merges"] == 16
            and summary["temporal_emitted"] == 16
            and summary["temporal_heads"] == 1
            and summary["output_stalls"] > 0
            and error_free
        )
    return {
        "model": "attention_decode_score_multivalue_service_temporal_cdc_probe_v1",
        "passed": passed,
        "service_period_ns": service_period_ns,
        "temporal_period_ns": temporal_period_ns,
        "reset_release": "service_then_temporal_skewed",
        "cdc_depth": cdc_depth,
        "mismatch_metadata": mismatch_metadata,
        "observed_rows": observed,
        "expected_rows": expected,
        "summary": summary,
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-period-ns", type=float, default=10.0)
    parser.add_argument("--temporal-period-ns", type=float, default=7.0)
    parser.add_argument("--cdc-depth", type=int, default=4)
    parser.add_argument("--mismatch-metadata", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(
        service_period_ns=args.service_period_ns,
        temporal_period_ns=args.temporal_period_ns,
        cdc_depth=args.cdc_depth,
        mismatch_metadata=args.mismatch_metadata,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
