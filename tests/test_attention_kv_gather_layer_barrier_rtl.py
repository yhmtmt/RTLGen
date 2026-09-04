from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_kv_gather_layer_barrier.sv"


def test_barrier_waits_for_payload_acceptance(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "tb.sv"
    tb.write_text(
        """`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg descriptor_valid = 0;
  wire descriptor_ready;
  reg [4:0] descriptor_layer = 0;
  reg descriptor_operation_consume = 0;
  wire released_valid;
  reg released_ready = 1;
  reg [4:0] accepted_refill_flits = 0;
  reg [4:0] accepted_consume_flits = 0;
  wire [4:0] active_layer;
  wire [22:0] refill_flit_count;
  wire [22:0] consume_flit_count;
  wire refill_complete;
  wire consume_complete;
  wire [5:0] completed_layer_count;
  wire protocol_error;
  integer layer_i;

  attention_kv_gather_layer_barrier #(
    .REFILL_FLITS_PER_LAYER(3), .CONSUME_FLITS_PER_LAYER(5), .LAYER_COUNT(32)
  ) dut (.*);
  always #1 clk = ~clk;

  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk); rst_n = 1;

    descriptor_valid = 1;
    descriptor_layer = 0;
    descriptor_operation_consume = 0;
    #0;
    if (!descriptor_ready || !released_valid) $finish(1);
    @(posedge clk); @(negedge clk);

    descriptor_operation_consume = 1;
    #0;
    if (descriptor_ready || released_valid) $finish(1);
    accepted_refill_flits = 1;
    @(posedge clk); @(negedge clk);
    accepted_refill_flits = 2;
    @(posedge clk); @(negedge clk);
    accepted_refill_flits = 0;
    if (!refill_complete || !descriptor_ready || !released_valid) $finish(1);
    @(posedge clk); @(negedge clk);

    descriptor_layer = 1;
    descriptor_operation_consume = 0;
    #0;
    if (descriptor_ready || released_valid) $finish(1);
    accepted_consume_flits = 2;
    @(posedge clk); @(negedge clk);
    accepted_consume_flits = 3;
    @(posedge clk); @(negedge clk);
    accepted_consume_flits = 0;
    if (!consume_complete || !descriptor_ready || !released_valid) $finish(1);
    @(posedge clk); @(negedge clk);
    if (active_layer != 1 || refill_flit_count != 0 || consume_flit_count != 0 ||
        completed_layer_count != 1 || protocol_error) begin
      $display("FAIL layer=%0d refill=%0d consume=%0d complete=%0d error=%0d",
        active_layer, refill_flit_count, consume_flit_count,
        completed_layer_count, protocol_error);
      $finish(1);
    end

    for (layer_i = 1; layer_i < 32; layer_i = layer_i + 1) begin
      descriptor_layer = layer_i;
      descriptor_operation_consume = 1;
      accepted_refill_flits = 3;
      @(posedge clk); @(negedge clk);
      accepted_refill_flits = 0;
      if (!refill_complete || !descriptor_ready || !released_valid) $finish(1);
      @(posedge clk); @(negedge clk);
      descriptor_valid = 0;
      accepted_consume_flits = 5;
      @(posedge clk); @(negedge clk);
      accepted_consume_flits = 0;

      if (layer_i == 31) begin
        if (!consume_complete || completed_layer_count != 32 || protocol_error) begin
          $display("FAIL final layer=%0d consume=%0d complete=%0d error=%0d",
            active_layer, consume_flit_count, completed_layer_count, protocol_error);
          $finish(1);
        end
      end else begin
        descriptor_valid = 1;
        descriptor_layer = layer_i + 1;
        descriptor_operation_consume = 0;
        #0;
        if (!consume_complete || !descriptor_ready || !released_valid) $finish(1);
        @(posedge clk); @(negedge clk);
        if (active_layer != layer_i + 1 || completed_layer_count != layer_i + 1 ||
            protocol_error) $finish(1);
      end
    end
    $display("PASS payload barriers");
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "barrier.vvp"
    result = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(RTL), str(tb)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS payload barriers" in result.stdout
