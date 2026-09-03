from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import (
    build_default_config,
    generate,
)
from npu.sim.perf.attention_kv_tile_layout import (
    VALUE_HEAD_TILE_ONE_BUFFER_FILL_CYCLES,
)


ROOT = Path(__file__).resolve().parents[1]
TRANSPOSE_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_ingress_transpose.sv"
VALUE_INGRESS_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_value_ingress.sv"


def test_one_buffer_value_head_service_bound_is_explicit() -> None:
    assert VALUE_HEAD_TILE_ONE_BUFFER_FILL_CYCLES == 6_271


def _testbench(endpoint_top: str) -> str:
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = 53;
  localparam integer LANES = 106;
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer stream;
  integer order;
  integer slot;
  integer token_lane;
  integer chunk;
  integer byte_lane;
  integer row_lane;
  integer row_byte;
  integer accepted_rows = 0;

  reg fill_target_valid = 0;
  wire fill_target_ready;
  reg fill_target_buffer_sel = 1;
  reg [15:0] fill_target_command_id = 16'h3141;
  reg [4:0] fill_target_head_base = 5'd16;
  reg [2:0] fill_target_wave_index = 3'd3;
  wire endpoint_fill_target_valid;
  wire endpoint_fill_target_ready;
  wire endpoint_fill_target_buffer_sel;
  wire [15:0] endpoint_fill_target_command_id;
  wire [4:0] endpoint_fill_target_head_base;
  wire [2:0] endpoint_fill_target_wave_index;

  reg block_target_valid = 0;
  wire block_target_ready;
  reg [1:0] block_target_kv_head = 2'd2;
  reg block_target_stream = 0;
  reg [5:0] block_target_slot = 0;
  reg ingress_valid = 0;
  wire ingress_ready;
  reg [19:0] ingress_tile_byte_addr = 0;
  reg [255:0] ingress_data = 0;
  reg [31:0] ingress_byte_valid = 0;

  wire endpoint_fill_valid;
  wire endpoint_fill_ready;
  wire endpoint_fill_buffer_sel;
  wire endpoint_fill_stream;
  wire [5:0] endpoint_fill_block_slot;
  wire [3:0] endpoint_fill_slice;
  wire [511:0] endpoint_fill_data;
  wire fill_complete;
  wire fill_active;
  wire [7:0] completed_block_count;
  wire ingress_protocol_error;

  reg command_valid = 0;
  wire command_ready;
  reg [LANES-1:0] value_read_req_valid = 0;
  wire [LANES-1:0] value_read_req_ready;
  reg [(LANES*14)-1:0] value_read_req_address = 0;
  reg [(LANES*4)-1:0] value_read_req_slice = 0;
  wire [LANES-1:0] value_response_valid;
  reg [LANES-1:0] value_response_ready = {{LANES{{1'b1}}}};
  wire [(LANES*512)-1:0] value_response_matrix;
  wire [31:0] fill_target_accept_count;
  wire [31:0] fill_row_accept_count;
  wire [11:0] buffer1_occupancy_rows;
  wire endpoint_protocol_error;

  function automatic [7:0] value_byte;
    input integer stream_i;
    input integer slot_i;
    input integer token_i;
    input integer dimension_i;
    begin
      value_byte = stream_i * 131 + slot_i * 17 + token_i * 11 + dimension_i * 3 + 7;
    end
  endfunction

  attention_score32_exact_kv_value_ingress #(.PRODUCERS(PRODUCERS)) u_ingress (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(fill_target_valid), .fill_target_ready(fill_target_ready),
    .fill_target_buffer_sel(fill_target_buffer_sel),
    .fill_target_command_id(fill_target_command_id),
    .fill_target_head_base(fill_target_head_base),
    .fill_target_wave_index(fill_target_wave_index),
    .endpoint_fill_target_valid(endpoint_fill_target_valid),
    .endpoint_fill_target_ready(endpoint_fill_target_ready),
    .endpoint_fill_target_buffer_sel(endpoint_fill_target_buffer_sel),
    .endpoint_fill_target_command_id(endpoint_fill_target_command_id),
    .endpoint_fill_target_head_base(endpoint_fill_target_head_base),
    .endpoint_fill_target_wave_index(endpoint_fill_target_wave_index),
    .block_target_valid(block_target_valid), .block_target_ready(block_target_ready),
    .block_target_kv_head(block_target_kv_head), .block_target_stream(block_target_stream),
    .block_target_slot(block_target_slot), .ingress_valid(ingress_valid),
    .ingress_ready(ingress_ready), .ingress_tile_byte_addr(ingress_tile_byte_addr),
    .ingress_data(ingress_data), .ingress_byte_valid(ingress_byte_valid),
    .endpoint_fill_valid(endpoint_fill_valid), .endpoint_fill_ready(endpoint_fill_ready),
    .endpoint_fill_buffer_sel(endpoint_fill_buffer_sel),
    .endpoint_fill_stream(endpoint_fill_stream),
    .endpoint_fill_block_slot(endpoint_fill_block_slot),
    .endpoint_fill_slice(endpoint_fill_slice), .endpoint_fill_data(endpoint_fill_data),
    .fill_complete(fill_complete), .fill_active(fill_active),
    .completed_block_count(completed_block_count), .protocol_error(ingress_protocol_error)
  );

  {endpoint_top} u_endpoint (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(endpoint_fill_target_valid),
    .fill_target_ready(endpoint_fill_target_ready),
    .fill_target_buffer_sel(endpoint_fill_target_buffer_sel),
    .fill_target_command_id(endpoint_fill_target_command_id),
    .fill_target_head_base(endpoint_fill_target_head_base),
    .fill_target_wave_index(endpoint_fill_target_wave_index),
    .fill_valid(endpoint_fill_valid), .fill_ready(endpoint_fill_ready),
    .fill_buffer_sel(endpoint_fill_buffer_sel), .fill_stream(endpoint_fill_stream),
    .fill_block_slot(endpoint_fill_block_slot), .fill_slice(endpoint_fill_slice),
    .fill_data(endpoint_fill_data),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_buffer_sel(1'b1), .command_id(16'h3141),
    .command_head_base(5'd16), .command_wave_index(3'd3),
    .command_release_valid(1'b0), .command_release_buffer_sel(1'b1),
    .value_read_req_valid(value_read_req_valid),
    .value_read_req_ready(value_read_req_ready),
    .value_read_req_address(value_read_req_address),
    .value_read_req_slice(value_read_req_slice),
    .value_response_valid(value_response_valid),
    .value_response_ready(value_response_ready),
    .value_response_matrix(value_response_matrix),
    .fill_target_accept_count(fill_target_accept_count),
    .fill_row_accept_count(fill_row_accept_count),
    .buffer1_occupancy_rows(buffer1_occupancy_rows),
    .protocol_error(endpoint_protocol_error)
  );

  always #1 clk = ~clk;

  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (endpoint_fill_valid && endpoint_fill_ready) begin
      for (row_lane = 0; row_lane < 8; row_lane = row_lane + 1)
        for (row_byte = 0; row_byte < 8; row_byte = row_byte + 1)
          if (endpoint_fill_data[((row_lane * 8 + row_byte) * 8) +: 8] !==
              value_byte(endpoint_fill_stream, endpoint_fill_block_slot, row_lane,
                         endpoint_fill_slice * 8 + row_byte)) begin
            $display("ROW_MISMATCH stream=%0d slot=%0d slice=%0d lane=%0d byte=%0d",
                     endpoint_fill_stream, endpoint_fill_block_slot,
                     endpoint_fill_slice, row_lane, row_byte);
            $finish(1);
          end
      accepted_rows <= accepted_rows + 1;
    end
    if (cycle > 20000) begin
      $display("TIMEOUT");
      $finish(1);
    end
  end

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;
    fill_target_valid = 1;
    while (!fill_target_ready) @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    fill_target_valid = 0;

    for (stream = 0; stream < 2; stream = stream + 1) begin
      for (order = 0; order < 64; order = order + 1) begin
        slot = (order * 17) % 64;
        block_target_stream = stream;
        block_target_slot = slot;
        block_target_valid = 1;
        while (!block_target_ready) @(posedge clk);
        @(posedge clk);
        @(negedge clk);
        block_target_valid = 0;

        for (token_lane = 0; token_lane < 8; token_lane = token_lane + 1) begin
          for (chunk = 0; chunk < 4; chunk = chunk + 1) begin
            ingress_tile_byte_addr = (20'd1 << 19) | (20'd2 << 17) |
              (stream << 16) | (slot << 10) | (token_lane << 7) | (chunk << 5);
            for (byte_lane = 0; byte_lane < 32; byte_lane = byte_lane + 1)
              ingress_data[(byte_lane*8) +: 8] =
                value_byte(stream, slot, token_lane, chunk * 32 + byte_lane);
            ingress_byte_valid = 32'hffff_ffff;
            ingress_valid = 1;
            while (!ingress_ready) @(posedge clk);
            @(posedge clk);
            @(negedge clk);
          end
        end
        ingress_valid = 0;
      end
    end

    while (!fill_complete) @(posedge clk);
    @(negedge clk);
    if (fill_active || completed_block_count != 128 || accepted_rows != 2048 ||
        fill_target_accept_count != 1 || fill_row_accept_count != 2048 ||
        buffer1_occupancy_rows != 2048 || ingress_protocol_error || endpoint_protocol_error) begin
      $display("FILL_FAIL active=%0d blocks=%0d rows=%0d target=%0d endpoint_rows=%0d occ=%0d ie=%0d ee=%0d",
               fill_active, completed_block_count, accepted_rows, fill_target_accept_count,
               fill_row_accept_count, buffer1_occupancy_rows,
               ingress_protocol_error, endpoint_protocol_error);
      $finish(1);
    end

    command_valid = 1;
    while (!command_ready) @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    command_valid = 0;
    value_read_req_address[0 +: 14] = 14'd0;
    value_read_req_slice[0 +: 4] = 4'd9;
    value_read_req_valid[0] = 1;
    while (!value_read_req_ready[0]) @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    value_read_req_valid[0] = 0;
    while (!value_response_valid[0]) @(posedge clk);
    @(negedge clk);
    for (row_byte = 0; row_byte < 64; row_byte = row_byte + 1)
      if (value_response_matrix[(row_byte*8) +: 8] !==
          value_byte(0, 0, row_byte / 8, 72 + (row_byte % 8))) begin
        $display("READBACK_MISMATCH byte=%0d", row_byte);
        $finish(1);
      end
    if (endpoint_protocol_error) begin
      $display("READBACK_PROTOCOL_ERROR");
      $finish(1);
    end
    $display("PASS cycles=%0d rows=%0d", cycle, accepted_rows);
    $finish(0);
  end
endmodule
"""


def test_canonical_value_flits_fill_and_read_real_cluster_sram(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    endpoint_dir = tmp_path / "endpoint"
    config = build_default_config(producers=53)
    endpoint_top = str(config["top_name"])
    generate(config, endpoint_dir)
    tb = tmp_path / "tb.sv"
    tb.write_text(_testbench(endpoint_top), encoding="utf-8")
    binary = tmp_path / "sim.vvp"
    compiled = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            str(TRANSPOSE_RTL),
            str(VALUE_INGRESS_RTL),
            str(endpoint_dir / "top.v"),
            str(tb),
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
