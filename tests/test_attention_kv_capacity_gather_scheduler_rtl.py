from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_capacity_gather_scheduler import (
    CONSUME,
    HBM,
    llama7b_descriptors,
)


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_kv_capacity_gather_scheduler.sv"


def test_rtl_matches_complete_capacity_gather_schedule(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "tb.sv"
    tb.write_text(
        """`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg enable = 0;
  reg [31:0] cycle = 0;
  wire desc_valid;
  wire desc_ready = cycle[2:0] != 3'd3;
  wire [4:0] desc_layer;
  wire [6:0] desc_tile;
  wire [3:0] desc_segment;
  wire desc_operation_consume;
  wire desc_source_hbm;
  wire [3:0] desc_source_endpoint;
  wire [3:0] desc_destination_cluster;
  wire [3:0] desc_plane;
  wire [19:0] desc_canonical_base_address;
  wire [33:0] desc_source_byte_address;
  wire desc_destination_is_resident_cache;
  wire [33:0] desc_destination_byte_address;
  wire [20:0] desc_payload_bytes;
  wire desc_last;
  wire done;
  wire [15:0] generated_descriptor_count;
  wire protocol_error;
  wire [140:0] desc_bundle = {
    desc_layer, desc_tile, desc_segment, desc_operation_consume,
    desc_source_hbm, desc_source_endpoint, desc_destination_cluster,
    desc_plane, desc_canonical_base_address, desc_source_byte_address,
    desc_destination_is_resident_cache, desc_destination_byte_address,
    desc_payload_bytes, desc_last
  };
  reg held_valid = 0;
  reg [140:0] held_bundle = 0;

  attention_kv_capacity_gather_scheduler dut (.*);
  always #1 clk = ~clk;

  always @(posedge clk) begin
    if (rst_n) begin
      cycle <= cycle + 1;
      if (desc_valid && !desc_ready) begin
        if (held_valid && desc_bundle !== held_bundle) begin
          $display("FAIL unstable descriptor");
          $finish(1);
        end
        held_valid <= 1;
        held_bundle <= desc_bundle;
      end else if (desc_valid && desc_ready) begin
        held_valid <= 0;
        $display("D %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
          desc_layer, desc_tile, desc_segment, desc_operation_consume,
          desc_source_hbm, desc_source_endpoint, desc_destination_cluster,
          desc_plane, desc_canonical_base_address, desc_source_byte_address,
          desc_destination_is_resident_cache, desc_destination_byte_address,
          desc_payload_bytes, desc_last);
      end
    end
  end

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1; enable = 1;
    while (!done && cycle < 32'd100000) @(posedge clk);
    @(negedge clk);
    if (!done || protocol_error || generated_descriptor_count != 16'd33344) begin
      $display("FAIL done=%0d error=%0d count=%0d", done, protocol_error,
        generated_descriptor_count);
      $finish(1);
    end
    $display("PASS count=%0d", generated_descriptor_count);
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "gather.vvp"
    compile_result = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(RTL), str(tb)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    result = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    observed = [
        tuple(int(value) for value in line.split()[1:])
        for line in result.stdout.splitlines()
        if line.startswith("D ")
    ]
    expected = [
        (
            row.layer,
            row.tile,
            row.segment,
            int(row.operation == CONSUME),
            int(row.source == HBM),
            row.source_endpoint,
            row.destination_cluster,
            row.plane,
            row.canonical_base_address,
            row.source_byte_address,
            int(row.operation != CONSUME),
            row.destination_byte_address,
            row.payload_bytes,
            int(row.last),
        )
        for row in llama7b_descriptors()
    ]
    assert observed == expected
    assert "PASS count=33344" in result.stdout
