from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_wave_command_barrier16.sv"


def test_staggered_cluster_commands_commit_as_one_wave(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    testbench = tmp_path / "tb.sv"
    testbench.write_text(
        r"""`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg [15:0] cluster_command_valid = 0;
  wire [15:0] cluster_command_ready;
  reg [16*16-1:0] cluster_command_id = 0;
  reg [16*5-1:0] cluster_command_head_base = 0;
  reg [16*3-1:0] cluster_command_wave_index = 0;
  reg [16*5-1:0] cluster_command_layer = 0;
  wire hierarchy_command_valid;
  reg hierarchy_command_ready = 0;
  wire [15:0] hierarchy_command_id;
  wire [4:0] hierarchy_command_head_base;
  wire [2:0] hierarchy_command_wave_index;
  wire [4:0] hierarchy_command_layer;
  wire [10:0] completed_wave_count;
  wire protocol_error;
  integer cluster;
  integer wave_count;
  integer commits = 0;

  attention_score32_exact_kv_wave_command_barrier16 dut (.*);
  always #1 clk = ~clk;
  always @(posedge clk)
    if (hierarchy_command_valid && hierarchy_command_ready)
      commits <= commits + 1;

  initial begin
    for (cluster = 0; cluster < 16; cluster = cluster + 1) begin
      cluster_command_id[(cluster*16) +: 16] = 16'h824a;
      cluster_command_head_base[(cluster*5) +: 5] = 5'd16;
      cluster_command_wave_index[(cluster*3) +: 3] = 3'd6;
      cluster_command_layer[(cluster*5) +: 5] = 5'd18;
    end
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1;
    for (cluster = 0; cluster < 16; cluster = cluster + 1) begin
      cluster_command_valid[cluster] = 1;
      @(posedge clk);
      @(negedge clk);
      if (hierarchy_command_valid !== (cluster == 15)) begin
        $display("EARLY_OR_MISSING_VALID cluster=%0d valid=%0d", cluster,
                 hierarchy_command_valid);
        $finish(1);
      end
    end
    repeat (3) @(posedge clk);
    if (cluster_command_ready != 0 || commits != 0) begin
      $display("COMMITTED_WITHOUT_READY");
      $finish(1);
    end
    @(negedge clk); hierarchy_command_ready = 1;
    @(posedge clk);
    @(negedge clk); hierarchy_command_ready = 0;
    cluster_command_valid = 0;
    if (hierarchy_command_id != 16'h824a ||
        hierarchy_command_head_base != 16 ||
        hierarchy_command_wave_index != 6 || hierarchy_command_layer != 18 ||
        commits != 1 || completed_wave_count != 1 || protocol_error) begin
      $display("FAIL cmd=%h head=%0d wave=%0d layer=%0d commits=%0d count=%0d error=%0d",
               hierarchy_command_id, hierarchy_command_head_base,
               hierarchy_command_wave_index, hierarchy_command_layer,
               commits, completed_wave_count, protocol_error);
      $finish(1);
    end
    for (wave_count = 1; wave_count < 1024; wave_count = wave_count + 1) begin
      @(negedge clk);
      cluster_command_valid = 16'hffff;
      hierarchy_command_ready = 1;
      @(posedge clk);
      @(negedge clk);
      cluster_command_valid = 0;
      hierarchy_command_ready = 0;
    end
    if (commits != 1024 || completed_wave_count != 1024 || protocol_error) begin
      $display("FULL_MODEL_COUNT_FAIL commits=%0d count=%0d error=%0d",
               commits, completed_wave_count, protocol_error);
      $finish(1);
    end
    $display("PASS waves=%0d", completed_wave_count);
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "sim.vvp"
    compiled = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(RTL), str(testbench)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert compiled.returncode == 0, compiled.stderr
    completed = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS" in completed.stdout
