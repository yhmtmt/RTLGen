from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTROL_RTL = (
    ROOT
    / "npu/sim/rtl/attention_score32_exact_kv_cluster_ejection_control.sv"
)


def _testbench() -> str:
    return r"""`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer flit;
  integer key_targets = 0;
  integer value_targets = 0;
  integer block_targets = 0;
  integer key_flits = 0;
  integer value_flits = 0;
  integer commands = 0;

  reg canonical_valid = 0;
  wire canonical_ready;
  reg [4:0] canonical_layer = 5'd11;
  reg [6:0] canonical_tile = 7'd93;
  reg [19:0] canonical_tile_byte_address = 0;
  reg [255:0] canonical_data = 0;

  wire key_fill_target_valid;
  reg key_fill_target_ready = 0;
  wire [1:0] key_fill_target_kv_head;
  wire key_ingress_valid;
  reg key_ingress_ready;
  wire [19:0] key_ingress_tile_byte_address;
  wire [255:0] key_ingress_data;
  wire [31:0] key_ingress_byte_valid;
  reg key_fill_complete = 0;

  wire value_fill_target_valid;
  reg value_fill_target_ready = 0;
  wire value_fill_target_buffer_sel;
  wire [15:0] value_fill_target_command_id;
  wire [4:0] value_fill_target_head_base;
  wire [2:0] value_fill_target_wave_index;
  wire value_block_target_valid;
  reg value_block_target_ready;
  wire [1:0] value_block_target_kv_head;
  wire value_block_target_stream;
  wire [5:0] value_block_target_slot;
  wire value_ingress_valid;
  reg value_ingress_ready;
  wire [19:0] value_ingress_tile_byte_address;
  wire [255:0] value_ingress_data;
  wire [31:0] value_ingress_byte_valid;
  reg value_fill_complete = 0;

  wire command_valid;
  reg command_ready = 0;
  wire [15:0] command_id;
  wire [4:0] command_head_base;
  wire [2:0] command_wave_index;
  wire [4:0] command_layer;
  wire [12:0] accepted_key_flit_count;
  wire [12:0] accepted_value_flit_count;
  wire [10:0] completed_wave_count;
  wire protocol_error;

  attention_score32_exact_kv_cluster_ejection_control dut (.*);

  always #1 clk = ~clk;

  always @(*) begin
    key_ingress_ready = (cycle % 7) != 2;
    value_block_target_ready = (cycle % 5) != 1;
    value_ingress_ready = (cycle % 11) != 4;
  end

  always @(posedge clk) begin
    cycle <= cycle + 1;
    key_fill_complete <= 0;
    value_fill_complete <= 0;
    if (key_fill_target_valid && key_fill_target_ready) begin
      key_targets <= key_targets + 1;
      if (key_fill_target_kv_head != 3) begin
        $display("BAD_KEY_TARGET");
        $finish(1);
      end
    end
    if (key_ingress_valid && key_ingress_ready) begin
      key_flits <= key_flits + 1;
      if (key_ingress_byte_valid != 32'hffff_ffff ||
          key_ingress_tile_byte_address != (20'h60000 +
            (key_flits / 64) * 1024 + ((key_flits / 32) % 2) * 65536 +
            (key_flits % 32) * 32) ||
          key_ingress_data[31:0] != key_flits) begin
        $display("BAD_KEY_FLIT index=%0d addr=%h data=%h", key_flits,
                 key_ingress_tile_byte_address, key_ingress_data[31:0]);
        $finish(1);
      end
      if (key_flits == 4095)
        key_fill_complete <= 1;
    end
    if (value_fill_target_valid && value_fill_target_ready) begin
      value_targets <= value_targets + 1;
      if (value_fill_target_buffer_sel != 1 ||
          value_fill_target_command_id != 16'h822f ||
          value_fill_target_head_base != 24 ||
          value_fill_target_wave_index != 5) begin
        $display("BAD_VALUE_TARGET");
        $finish(1);
      end
    end
    if (value_block_target_valid && value_block_target_ready) begin
      block_targets <= block_targets + 1;
      if (value_block_target_kv_head != 3 ||
          value_block_target_stream != block_targets[6] ||
          value_block_target_slot != block_targets[5:0]) begin
        $display("BAD_BLOCK_TARGET index=%0d stream=%0d slot=%0d",
                 block_targets, value_block_target_stream,
                 value_block_target_slot);
        $finish(1);
      end
    end
    if (value_ingress_valid && value_ingress_ready) begin
      value_flits <= value_flits + 1;
      if (value_ingress_byte_valid != 32'hffff_ffff ||
          value_ingress_tile_byte_address != (20'he0000 + value_flits * 32) ||
          value_ingress_data[31:0] != (32'h80000000 | value_flits)) begin
        $display("BAD_VALUE_FLIT index=%0d addr=%h data=%h", value_flits,
                 value_ingress_tile_byte_address, value_ingress_data[31:0]);
        $finish(1);
      end
      if (value_flits == 4095)
        value_fill_complete <= 1;
    end
    if (command_valid && command_ready) begin
      commands <= commands + 1;
      if (command_id != 16'h822f || command_head_base != 24 ||
          command_wave_index != 5 || command_layer != 11) begin
        $display("BAD_COMMAND");
        $finish(1);
      end
    end
    if (cycle > 30000) begin
      $display("TIMEOUT");
      $finish(1);
    end
  end

  task automatic send_flit;
    input [19:0] address;
    input [31:0] marker;
    begin
      @(negedge clk);
      canonical_tile_byte_address = address;
      canonical_data = {224'd0, marker};
      canonical_valid = 1;
      while (!canonical_ready)
        @(negedge clk);
      @(posedge clk);
    end
  endtask

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;

    canonical_tile_byte_address = 20'h60000;
    canonical_data = 0;
    canonical_valid = 1;
    while (!key_fill_target_valid)
      @(negedge clk);
    key_fill_target_ready = 1;
    @(posedge clk);
    @(negedge clk);
    key_fill_target_ready = 0;
    canonical_valid = 0;
    for (flit = 0; flit < 4096; flit = flit + 1)
      send_flit(20'h60000 + (flit / 64) * 1024 +
                ((flit / 32) % 2) * 65536 + (flit % 32) * 32, flit);

    @(negedge clk);
    canonical_tile_byte_address = 20'he0000;
    canonical_data = 256'h80000000;
    canonical_valid = 1;
    while (!value_fill_target_valid)
      @(negedge clk);
    value_fill_target_ready = 1;
    @(posedge clk);
    @(negedge clk);
    value_fill_target_ready = 0;
    canonical_valid = 0;
    for (flit = 0; flit < 4096; flit = flit + 1)
      send_flit(20'he0000 + flit * 32, 32'h80000000 | flit);
    @(negedge clk);
    canonical_valid = 0;

    while (!command_valid)
      @(posedge clk);
    repeat (3) @(posedge clk);
    @(negedge clk);
    command_ready = 1;
    @(posedge clk);
    @(negedge clk);
    command_ready = 0;
    if (key_targets != 1 || value_targets != 1 || block_targets != 128 ||
        key_flits != 4096 || value_flits != 4096 || commands != 1 ||
        accepted_key_flit_count != 4096 ||
        accepted_value_flit_count != 4096 || completed_wave_count != 1 ||
        protocol_error) begin
      $display("SUMMARY_FAIL kt=%0d vt=%0d bt=%0d k=%0d v=%0d cmd=%0d ak=%0d av=%0d waves=%0d error=%0d", key_targets,
               value_targets, block_targets, key_flits, value_flits, commands,
               accepted_key_flit_count, accepted_value_flit_count,
               completed_wave_count, protocol_error);
      $finish(1);
    end
    $display("PASS cycles=%0d", cycle);
    $finish(0);
  end
endmodule
"""


def test_full_k_v_wave_derives_targets_and_command_under_backpressure(
    tmp_path: Path,
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    testbench = tmp_path / "tb.sv"
    testbench.write_text(_testbench(), encoding="utf-8")
    binary = tmp_path / "sim.vvp"
    compiled = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            str(CONTROL_RTL),
            str(testbench),
        ],
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
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS" in completed.stdout
