from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL_FILES = [
    "npu/sim/rtl/attention_kv_gather_packet_mesh4x4.sv",
    "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint_array16.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    "npu/sim/rtl/noc_segmented_mesh_router.sv",
    "npu/sim/rtl/noc_ready_valid_fifo.sv",
]


def test_packet_mesh_preserves_payload_and_ingress_metadata(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "tb.sv"
    tb.write_text(
        """`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg [31:0] cycle = 0;
  reg [15:0] cmd_valid = 0;
  wire [15:0] cmd_ready;
  reg [16*5-1:0] cmd_layer = 0;
  reg [16*7-1:0] cmd_tile = 0;
  reg [15:0] cmd_operation_consume = 0;
  reg [15:0] cmd_source_hbm = 0;
  reg [16*4-1:0] cmd_source_endpoint = 0;
  reg [16*4-1:0] cmd_destination_cluster = 0;
  reg [16*20-1:0] cmd_canonical_byte_address = 0;
  reg [16*34-1:0] cmd_source_byte_address = 0;
  reg [15:0] cmd_destination_is_resident_cache = 0;
  reg [16*34-1:0] cmd_destination_byte_address = 0;
  reg [16*12-1:0] cmd_packet_index = 0;
  reg [16*8-1:0] cmd_tag = 0;
  reg [16*4-1:0] cmd_flit_count = 0;
  reg [15:0] cmd_descriptor_last = 0;
  reg [15:0] cmd_schedule_last = 0;
  wire [15:0] source_req_valid;
  reg [15:0] source_req_ready;
  wire [15:0] source_req_is_hbm;
  wire [16*33-1:0] source_req_byte_address;
  reg [15:0] source_rsp_valid;
  wire [15:0] source_rsp_ready;
  reg [16*256-1:0] source_rsp_data;
  wire [15:0] resident_write_valid;
  reg [15:0] resident_write_ready;
  wire [16*33-1:0] resident_write_byte_address;
  wire [16*256-1:0] resident_write_data;
  wire [15:0] canonical_ingress_valid;
  reg [15:0] canonical_ingress_ready;
  wire [16*5-1:0] canonical_ingress_layer;
  wire [16*7-1:0] canonical_ingress_tile;
  wire [16*20-1:0] canonical_ingress_tile_byte_address;
  wire [16*256-1:0] canonical_ingress_data;
  wire [15:0] endpoint_protocol_error;
  wire command_protocol_error;
  wire protocol_error;

  reg [15:0] response_pending = 0;
  reg [32:0] response_address [0:15];
  reg response_is_hbm [0:15];
  integer writes [0:15];
  reg [3:0] expected_source [0:15];
  reg [32:0] expected_source_base [0:15];
  reg [32:0] expected_destination_base [0:15];
  reg [4:0] expected_layer [0:15];
  reg [6:0] expected_tile [0:15];
  reg expected_resident [0:15];
  integer endpoint;
  integer byte_lane;
  reg [15:0] accepted_command_mask = 0;
  integer completions = 0;

  function automatic [255:0] payload_pattern;
    input [3:0] source;
    input is_hbm;
    input [32:0] address;
    integer lane;
    begin
      for (lane = 0; lane < 32; lane = lane + 1)
        payload_pattern[(lane*8) +: 8] =
          address[7:0] + lane[7:0] + {source, 4'b0} + (is_hbm ? 8'h80 : 8'h00);
    end
  endfunction

  attention_kv_gather_packet_mesh4x4 dut (
    .clk(clk), .rst_n(rst_n),
    .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_layer(cmd_layer),
    .cmd_tile(cmd_tile), .cmd_operation_consume(cmd_operation_consume),
    .cmd_source_hbm(cmd_source_hbm),
    .cmd_source_endpoint(cmd_source_endpoint),
    .cmd_destination_cluster(cmd_destination_cluster),
    .cmd_canonical_byte_address(cmd_canonical_byte_address),
    .cmd_source_byte_address(cmd_source_byte_address),
    .cmd_destination_is_resident_cache(cmd_destination_is_resident_cache),
    .cmd_destination_byte_address(cmd_destination_byte_address),
    .cmd_packet_index(cmd_packet_index), .cmd_tag(cmd_tag),
    .cmd_flit_count(cmd_flit_count),
    .cmd_descriptor_last(cmd_descriptor_last),
    .cmd_schedule_last(cmd_schedule_last),
    .source_req_valid(source_req_valid), .source_req_ready(source_req_ready),
    .source_req_is_hbm(source_req_is_hbm),
    .source_req_byte_address(source_req_byte_address),
    .source_rsp_valid(source_rsp_valid), .source_rsp_ready(source_rsp_ready),
    .source_rsp_data(source_rsp_data),
    .resident_write_valid(resident_write_valid),
    .resident_write_ready(resident_write_ready),
    .resident_write_byte_address(resident_write_byte_address),
    .resident_write_data(resident_write_data),
    .canonical_ingress_valid(canonical_ingress_valid),
    .canonical_ingress_ready(canonical_ingress_ready),
    .canonical_ingress_layer(canonical_ingress_layer),
    .canonical_ingress_tile(canonical_ingress_tile),
    .canonical_ingress_tile_byte_address(canonical_ingress_tile_byte_address),
    .canonical_ingress_data(canonical_ingress_data),
    .endpoint_protocol_error(endpoint_protocol_error),
    .command_protocol_error(command_protocol_error), .protocol_error(protocol_error)
  );
  always #1 clk = ~clk;

  always @(*) begin
    source_req_ready = 0;
    source_rsp_valid = response_pending;
    source_rsp_data = 0;
    resident_write_ready = 16'hffff;
    canonical_ingress_ready = 16'hffff;
    resident_write_ready[0] = cycle[1:0] != 2'd1;
    canonical_ingress_ready[15] = cycle[2:0] != 3'd3;
    for (endpoint = 0; endpoint < 16; endpoint = endpoint + 1) begin
      source_req_ready[endpoint] = !response_pending[endpoint] ||
        source_rsp_ready[endpoint];
      source_rsp_data[(endpoint*256) +: 256] = payload_pattern(
        endpoint[3:0], response_is_hbm[endpoint], response_address[endpoint]
      );
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      cycle <= cycle + 1;
      for (endpoint = 0; endpoint < 16; endpoint = endpoint + 1) begin
        if (cmd_valid[endpoint] && cmd_ready[endpoint]) begin
          cmd_valid[endpoint] <= 1'b0;
          accepted_command_mask[endpoint] <= 1'b1;
        end
        if (response_pending[endpoint] && source_rsp_ready[endpoint])
          response_pending[endpoint] <= 1'b0;
        if (source_req_valid[endpoint] && source_req_ready[endpoint]) begin
          response_pending[endpoint] <= 1'b1;
          response_address[endpoint] <=
            source_req_byte_address[(endpoint*33) +: 33];
          response_is_hbm[endpoint] <= source_req_is_hbm[endpoint];
        end
        if ((resident_write_valid[endpoint] && resident_write_ready[endpoint]) ||
            (canonical_ingress_valid[endpoint] && canonical_ingress_ready[endpoint])) begin
          if (endpoint == 0 && !resident_write_valid[endpoint]) begin
            $display("FAIL expected resident endpoint=%0d", endpoint);
            $finish(1);
          end
          if (endpoint != 0 && !canonical_ingress_valid[endpoint]) begin
            $display("FAIL expected canonical endpoint=%0d", endpoint);
            $finish(1);
          end
          if (resident_write_valid[endpoint] &&
              resident_write_byte_address[(endpoint*33) +: 33] !==
                expected_destination_base[endpoint] + writes[endpoint] * 32) begin
            $display("FAIL resident address endpoint=%0d write=%0d", endpoint, writes[endpoint]);
            $finish(1);
          end
          if (canonical_ingress_valid[endpoint] &&
              (canonical_ingress_layer[(endpoint*5) +: 5] !== expected_layer[endpoint] ||
               canonical_ingress_tile[(endpoint*7) +: 7] !== expected_tile[endpoint] ||
               canonical_ingress_tile_byte_address[(endpoint*20) +: 20] !==
                 expected_destination_base[endpoint] + writes[endpoint] * 32)) begin
            $display("FAIL canonical metadata endpoint=%0d write=%0d", endpoint, writes[endpoint]);
            $finish(1);
          end
          if ((resident_write_valid[endpoint] ?
               resident_write_data[(endpoint*256) +: 256] :
               canonical_ingress_data[(endpoint*256) +: 256]) !==
              payload_pattern(expected_source[endpoint],
                cmd_source_hbm[expected_source[endpoint]],
                expected_source_base[endpoint] + writes[endpoint] * 32)) begin
            $display("FAIL data endpoint=%0d write=%0d", endpoint, writes[endpoint]);
            $finish(1);
          end
          writes[endpoint] <= writes[endpoint] + 1;
        end
      end
      if (cycle > 500) begin
        $display("FAIL timeout");
        $finish(1);
      end
    end
  end

  task automatic install_command;
    input [3:0] source;
    input [3:0] destination;
    input is_hbm;
    input is_resident;
    input [4:0] layer;
    input [6:0] tile;
    input [32:0] source_base;
    input [32:0] destination_base;
    input [7:0] tag;
    begin
      cmd_layer[(source*5) +: 5] = layer;
      cmd_tile[(source*7) +: 7] = tile;
      cmd_operation_consume[source] = !is_resident;
      cmd_source_hbm[source] = is_hbm;
      cmd_source_endpoint[(source*4) +: 4] = source;
      cmd_destination_cluster[(source*4) +: 4] = destination;
      cmd_canonical_byte_address[(source*20) +: 20] = destination_base[19:0];
      cmd_source_byte_address[(source*34) +: 34] = {1'b0, source_base};
      cmd_destination_is_resident_cache[source] = is_resident;
      cmd_destination_byte_address[(source*34) +: 34] = {1'b0, destination_base};
      cmd_tag[(source*8) +: 8] = tag;
      cmd_packet_index[(source*12) +: 12] = tag;
      cmd_flit_count[(source*4) +: 4] = 8;
      cmd_valid[source] = 1'b1;
      expected_source[destination] = source;
      expected_source_base[destination] = source_base;
      expected_destination_base[destination] = destination_base;
      expected_layer[destination] = layer;
      expected_tile[destination] = tile;
      expected_resident[destination] = is_resident;
    end
  endtask

  initial begin
    for (endpoint = 0; endpoint < 16; endpoint = endpoint + 1) begin
      response_address[endpoint] = 0;
      response_is_hbm[endpoint] = 0;
      writes[endpoint] = 0;
      expected_source[endpoint] = 0;
      expected_source_base[endpoint] = 0;
      expected_destination_base[endpoint] = 0;
      expected_layer[endpoint] = 0;
      expected_tile[endpoint] = 0;
      expected_resident[endpoint] = 0;
    end
    install_command(0, 15, 1, 0, 2, 7, 33'h10000, 33'h01000, 8'h11);
    install_command(3, 0, 1, 1, 0, 0, 33'h30000, 33'h20000, 8'h22);
    install_command(5, 5, 0, 0, 1, 9, 33'h50000, 33'h04000, 8'h33);
    install_command(12, 6, 1, 0, 31, 127, 33'h70000, 33'h0ff00, 8'h44);
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1;
    while (writes[0] != 8 || writes[5] != 8 || writes[6] != 8 || writes[15] != 8)
      @(posedge clk);
    repeat (3) @(posedge clk);
    @(negedge clk);
    if (protocol_error || endpoint_protocol_error != 0 ||
        accepted_command_mask != 16'h1029) begin
      $display("FAIL final protocol=%0d endpoint=%h accepted=%h", protocol_error,
        endpoint_protocol_error, accepted_command_mask);
      $finish(1);
    end
    $display("PASS commands=4 writes=32");
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "mesh.vvp"
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            *(str(ROOT / path) for path in RTL_FILES),
            str(tb),
        ],
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
    assert "PASS commands=4 writes=32" in result.stdout
