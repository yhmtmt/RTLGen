from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL_FILES = [
    "attention_score32_exact_kv_cluster_ejection_control.sv",
    "attention_score32_exact_kv_key_pingpong_transpose.sv",
    "attention_score32_exact_kv_key_stage_wide.sv",
    "attention_score32_exact_kv_key_pingpong_ingress.sv",
    "attention_score32_exact_kv_ingress_transpose.sv",
    "attention_score32_exact_kv_value_ingress.sv",
    "attention_score32_exact_kv_cluster_ejection_ingress.sv",
]


def _testbench() -> str:
    return r"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = 53;
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer dimension;
  integer flit;
  integer endpoint_targets = 0;
  integer endpoint_rows = 0;
  integer producer_beats = 0;
  integer cluster_commands = 0;
  integer producer_i;
  integer beats_this_cycle;

  reg canonical_valid = 0;
  wire canonical_ready;
  reg [4:0] canonical_layer = 5'd1;
  reg [6:0] canonical_tile = 7'd7;
  reg [19:0] canonical_tile_byte_address = 0;
  reg [255:0] canonical_data = 0;
  reg query_write_valid = 0;
  wire query_write_ready;
  reg [1:0] query_write_kv_head = 2'd2;
  reg [6:0] query_write_dimension = 0;
  reg [63:0] query_write_data = 0;
  reg query_write_last = 0;
  wire [PRODUCERS-1:0] producer_valid;
  reg [PRODUCERS-1:0] producer_ready = {PRODUCERS{1'b1}};
  wire [PRODUCERS-1:0] producer_last;
  wire [(PRODUCERS*128)-1:0] producer_query;
  wire [(PRODUCERS*128)-1:0] producer_key;
  wire endpoint_fill_target_valid;
  reg endpoint_fill_target_ready = 1;
  wire endpoint_fill_target_buffer_sel;
  wire [15:0] endpoint_fill_target_command_id;
  wire [4:0] endpoint_fill_target_head_base;
  wire [2:0] endpoint_fill_target_wave_index;
  wire endpoint_fill_valid;
  reg endpoint_fill_ready;
  wire endpoint_fill_buffer_sel;
  wire endpoint_fill_stream;
  wire [5:0] endpoint_fill_block_slot;
  wire [3:0] endpoint_fill_slice;
  wire [511:0] endpoint_fill_data;
  wire cluster_command_valid;
  reg cluster_command_ready = 0;
  wire [15:0] command_id;
  wire [4:0] command_head_base;
  wire [2:0] command_wave_index;
  wire [4:0] command_layer;
  wire key_command_done;
  wire [12:0] accepted_key_flit_count;
  wire [12:0] accepted_value_flit_count;
  wire [10:0] completed_wave_count;
  wire protocol_error;

  attention_score32_exact_kv_cluster_ejection_ingress #(
    .PRODUCERS(PRODUCERS)
  ) dut (.*);

  always #1 clk = ~clk;
  always @(*) endpoint_fill_ready = (cycle % 13) != 6;

  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (endpoint_fill_target_valid && endpoint_fill_target_ready) begin
      endpoint_targets <= endpoint_targets + 1;
      if (endpoint_fill_target_buffer_sel != 0 ||
          endpoint_fill_target_command_id != 16'h8206 ||
          endpoint_fill_target_head_base != 16 ||
          endpoint_fill_target_wave_index != 0) begin
        $display("BAD_ENDPOINT_TARGET");
        $finish(1);
      end
    end
    if (endpoint_fill_valid && endpoint_fill_ready)
      endpoint_rows <= endpoint_rows + 1;
    beats_this_cycle = 0;
    for (producer_i = 0; producer_i < PRODUCERS; producer_i = producer_i + 1)
      if (producer_valid[producer_i] === 1'b1 && producer_ready[producer_i] === 1'b1)
        beats_this_cycle = beats_this_cycle + 1;
    producer_beats <= producer_beats + beats_this_cycle;
    if (cluster_command_valid && cluster_command_ready)
      cluster_commands <= cluster_commands + 1;
    if (cycle > 40000) begin
      $display("TIMEOUT state=%0d k=%0d v=%0d key_complete=%0d value_complete=%0d rows=%0d beats=%0d error=%0d",
               dut.u_control.state_q, accepted_key_flit_count,
               accepted_value_flit_count, dut.key_fill_complete,
               dut.value_fill_complete, endpoint_rows, producer_beats,
               protocol_error);
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
      @(negedge clk);
      canonical_valid = 0;
    end
  endtask

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;

    canonical_tile_byte_address = 20'h40000;
    canonical_valid = 1;
    while (!query_write_ready)
      @(negedge clk);
    canonical_valid = 0;
    for (dimension = 0; dimension < 128; dimension = dimension + 1) begin
      query_write_dimension = dimension;
      query_write_data = {57'd0, dimension[6:0]};
      query_write_last = dimension == 127;
      query_write_valid = 1;
      @(posedge clk);
      @(negedge clk);
    end
    query_write_valid = 0;

    for (flit = 0; flit < 4096; flit = flit + 1)
      send_flit(20'h40000 + (flit / 64) * 1024 +
                ((flit / 32) % 2) * 65536 + (flit % 32) * 32, flit);
    for (flit = 0; flit < 4096; flit = flit + 1)
      send_flit(20'hc0000 + flit * 32, 32'h80000000 | flit);

    while (dut.u_control.command_valid !== 1'b1)
      @(posedge clk);
    repeat (4) @(posedge clk);
    @(negedge clk);
    cluster_command_ready = 1;
    @(posedge clk);
    @(negedge clk);
    cluster_command_ready = 0;
    while (!key_command_done)
      @(posedge clk);
    @(negedge clk);
    if (command_id != 16'h8206 || command_head_base != 16 ||
        command_wave_index != 0 || command_layer != 1 ||
        endpoint_targets != 1 || endpoint_rows != 2048 ||
        producer_beats != 8192 || cluster_commands != 1 ||
        accepted_key_flit_count != 4096 ||
        accepted_value_flit_count != 4096 || completed_wave_count != 1 ||
        protocol_error) begin
      $display("SUMMARY_FAIL target=%0d rows=%0d beats=%0d cmd=%0d k=%0d v=%0d waves=%0d error=%0d",
               endpoint_targets, endpoint_rows, producer_beats,
               cluster_commands, accepted_key_flit_count,
               accepted_value_flit_count, completed_wave_count, protocol_error);
      $finish(1);
    end
    $display("PASS cycles=%0d rows=%0d beats=%0d", cycle, endpoint_rows,
             producer_beats);
    $finish(0);
  end
endmodule
"""


def test_full_wave_reaches_real_key_and_value_ingress_and_atomic_command(
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
            *(str(ROOT / "npu/sim/rtl" / name) for name in RTL_FILES),
            str(testbench),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    completed = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS" in completed.stdout
