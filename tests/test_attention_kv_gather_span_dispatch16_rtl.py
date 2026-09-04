from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_capacity_gather_scheduler import layer_descriptors


ROOT = Path(__file__).resolve().parents[1]
PACKETIZER = ROOT / "npu/sim/rtl/attention_kv_gather_span_packetizer.sv"
DISPATCH = ROOT / "npu/sim/rtl/attention_kv_gather_span_dispatch16.sv"


def _drive(row: object) -> str:
    return f"""
    desc_layer = 5'd{row.layer};
    desc_tile = 7'd{row.tile};
    desc_segment = 4'd{row.segment};
    desc_operation_consume = 1'b1;
    desc_source_hbm = 1'b1;
    desc_source_endpoint = 4'd{row.source_endpoint};
    desc_destination_cluster = 4'd{row.destination_cluster};
    desc_plane = 4'd{row.plane};
    desc_canonical_base_address = 20'd{row.canonical_base_address};
    desc_source_byte_address = 34'd{row.source_byte_address};
    desc_destination_is_resident_cache = 1'b0;
    desc_destination_byte_address = 34'd{row.destination_byte_address};
    desc_payload_bytes = 21'd{row.payload_bytes};
    desc_valid = 1'b1;
    while (!desc_ready) @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    desc_valid = 1'b0;
"""


def test_four_hbm_sources_expand_full_tiles_concurrently(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    rows = layer_descriptors(0)[28:32]
    assert {row.source_endpoint for row in rows} == {0, 3, 12, 15}
    initialization = "\n".join(
        f"    expected_base[{row.source_endpoint}] = 34'd{row.source_byte_address};\n"
        f"    expected_destination[{row.source_endpoint}] = 4'd{row.destination_cluster};"
        for row in rows
    )
    drives = "".join(_drive(row) for row in rows)
    tb = tmp_path / "tb.sv"
    tb.write_text(
        f"""`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg [31:0] cycle = 0;
  reg desc_valid = 0;
  wire desc_ready;
  reg [4:0] desc_layer = 0;
  reg [6:0] desc_tile = 0;
  reg [3:0] desc_segment = 0;
  reg desc_operation_consume = 0;
  reg desc_source_hbm = 0;
  reg [3:0] desc_source_endpoint = 0;
  reg [3:0] desc_destination_cluster = 0;
  reg [3:0] desc_plane = 0;
  reg [19:0] desc_canonical_base_address = 0;
  reg [33:0] desc_source_byte_address = 0;
  reg desc_destination_is_resident_cache = 0;
  reg [33:0] desc_destination_byte_address = 0;
  reg [20:0] desc_payload_bytes = 0;
  reg desc_last = 0;
  wire [15:0] cmd_valid;
  reg [15:0] cmd_ready;
  wire [16*5-1:0] cmd_layer;
  wire [16*7-1:0] cmd_tile;
  wire [16*4-1:0] cmd_segment;
  wire [15:0] cmd_operation_consume;
  wire [15:0] cmd_source_hbm;
  wire [16*4-1:0] cmd_source_endpoint;
  wire [16*4-1:0] cmd_destination_cluster;
  wire [16*4-1:0] cmd_plane;
  wire [16*20-1:0] cmd_canonical_byte_address;
  wire [16*34-1:0] cmd_source_byte_address;
  wire [15:0] cmd_destination_is_resident_cache;
  wire [16*34-1:0] cmd_destination_byte_address;
  wire [16*12-1:0] cmd_packet_index;
  wire [16*8-1:0] cmd_tag;
  wire [16*4-1:0] cmd_flit_count;
  wire [15:0] cmd_descriptor_last;
  wire [15:0] cmd_schedule_last;
  wire [16*13-1:0] accepted_descriptor_count;
  wire [16*25-1:0] generated_packet_count;
  wire [15:0] packetizer_protocol_error;
  integer count [0:15];
  reg [33:0] expected_base [0:15];
  reg [3:0] expected_destination [0:15];
  integer lane;
  integer ready_count;
  integer simultaneous;
  integer max_simultaneous = 0;

  attention_kv_gather_span_dispatch16 dut (.*);
  always #1 clk = ~clk;

  always @(*) begin
    cmd_ready = 16'd0;
    for (ready_count = 0; ready_count < 16; ready_count = ready_count + 1)
      cmd_ready[ready_count] = ((cycle + ready_count) % 7) != 2;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      cycle <= cycle + 1;
      simultaneous = 0;
      for (lane = 0; lane < 16; lane = lane + 1) begin
        if (cmd_valid[lane] && cmd_ready[lane]) begin
          simultaneous = simultaneous + 1;
          if (cmd_source_endpoint[(lane*4) +: 4] !== lane[3:0] ||
              !cmd_source_hbm[lane] || !cmd_operation_consume[lane] ||
              cmd_destination_cluster[(lane*4) +: 4] !== expected_destination[lane] ||
              cmd_source_byte_address[(lane*34) +: 34] !==
                expected_base[lane] + count[lane] * 256 ||
              cmd_canonical_byte_address[(lane*20) +: 20] !== count[lane] * 256 ||
              cmd_packet_index[(lane*12) +: 12] !== count[lane] ||
              cmd_tag[(lane*8) +: 8] !== (count[lane] & 255) ||
              cmd_flit_count[(lane*4) +: 4] !== 8 ||
              cmd_descriptor_last[lane] !== (count[lane] == 4095)) begin
            $display("FAIL lane=%0d count=%0d", lane, count[lane]);
            $finish(1);
          end
          count[lane] <= count[lane] + 1;
        end
      end
      if (simultaneous > max_simultaneous)
        max_simultaneous <= simultaneous;
      if (cycle > 32'd10000) begin
        $display("FAIL timeout");
        $finish(1);
      end
    end
  end

  initial begin
    for (lane = 0; lane < 16; lane = lane + 1) begin
      count[lane] = 0;
      expected_base[lane] = 0;
      expected_destination[lane] = 0;
    end
{initialization}
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1;
{drives}
    while (count[0] != 4096 || count[3] != 4096 ||
           count[12] != 4096 || count[15] != 4096) @(posedge clk);
    @(negedge clk);
    if (packetizer_protocol_error != 0 || max_simultaneous < 4) begin
      $display("FAIL errors=%h max_simultaneous=%0d", packetizer_protocol_error,
        max_simultaneous);
      $finish(1);
    end
    $display("PASS packets=16384 max_simultaneous=%0d", max_simultaneous);
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "dispatch.vvp"
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            str(PACKETIZER),
            str(DISPATCH),
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
    assert "PASS packets=16384 max_simultaneous=4" in result.stdout
