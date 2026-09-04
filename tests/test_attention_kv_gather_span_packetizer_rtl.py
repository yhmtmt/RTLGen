from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_capacity_gather_scheduler import (
    CONSUME,
    HBM,
    layer_descriptors,
)
from npu.sim.perf.attention_kv_gather_packetizer import packet_commands


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_kv_gather_span_packetizer.sv"


def _drive_descriptor(row: object, *, last: bool) -> str:
    return f"""
    desc_layer = 5'd{row.layer};
    desc_tile = 7'd{row.tile};
    desc_segment = 4'd{row.segment};
    desc_operation_consume = 1'd{int(row.operation == CONSUME)};
    desc_source_hbm = 1'd{int(row.source == HBM)};
    desc_source_endpoint = 4'd{row.source_endpoint};
    desc_destination_cluster = 4'd{row.destination_cluster};
    desc_plane = 4'd{row.plane};
    desc_canonical_base_address = 20'd{row.canonical_base_address};
    desc_source_byte_address = 34'd{row.source_byte_address};
    desc_destination_is_resident_cache = 1'd{int(row.operation != CONSUME)};
    desc_destination_byte_address = 34'd{row.destination_byte_address};
    desc_payload_bytes = 21'd{row.payload_bytes};
    desc_last = 1'd{int(last)};
    desc_valid = 1'b1;
    while (!desc_ready) @(posedge clk);
    @(posedge clk);
    @(negedge clk);
    desc_valid = 1'b0;
"""


def test_rtl_expands_full_and_partial_spans_exactly(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    layer = layer_descriptors(0)
    hbm_tail = next(
        row
        for row in layer
        if row.operation == CONSUME and row.tile == 2 and row.plane == 4 and row.source == HBM
    )
    full_key = next(
        row
        for row in layer
        if row.operation == CONSUME and row.tile == 0 and row.plane == 0
    )
    descriptors = [layer[0], layer[2], full_key, replace(hbm_tail, last=True)]
    drives = "".join(
        _drive_descriptor(row, last=index + 1 == len(descriptors))
        for index, row in enumerate(descriptors)
    )
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
  wire cmd_valid;
  wire cmd_ready = cycle[2:0] != 3'd5;
  wire [4:0] cmd_layer;
  wire [6:0] cmd_tile;
  wire [3:0] cmd_segment;
  wire cmd_operation_consume;
  wire cmd_source_hbm;
  wire [3:0] cmd_source_endpoint;
  wire [3:0] cmd_destination_cluster;
  wire [3:0] cmd_plane;
  wire [19:0] cmd_canonical_byte_address;
  wire [33:0] cmd_source_byte_address;
  wire cmd_destination_is_resident_cache;
  wire [33:0] cmd_destination_byte_address;
  wire [11:0] cmd_packet_index;
  wire [7:0] cmd_tag;
  wire [3:0] cmd_flit_count;
  wire cmd_descriptor_last;
  wire cmd_schedule_last;
  wire [13:0] accepted_descriptor_count;
  wire [24:0] generated_packet_count;
  wire protocol_error;
  wire [144:0] cmd_bundle = {{
    cmd_layer, cmd_tile, cmd_segment, cmd_operation_consume, cmd_source_hbm,
    cmd_source_endpoint, cmd_destination_cluster, cmd_plane,
    cmd_canonical_byte_address, cmd_source_byte_address,
    cmd_destination_is_resident_cache, cmd_destination_byte_address,
    cmd_packet_index, cmd_tag, cmd_flit_count, cmd_descriptor_last,
    cmd_schedule_last
  }};
  reg held_valid = 0;
  reg [144:0] held_bundle = 0;
  reg schedule_done = 0;

  attention_kv_gather_span_packetizer dut (.*);
  always #1 clk = ~clk;

  always @(posedge clk) begin
    if (rst_n) begin
      cycle <= cycle + 1;
      if (cmd_valid && !cmd_ready) begin
        if (held_valid && cmd_bundle !== held_bundle) begin
          $display("FAIL unstable packet command");
          $finish(1);
        end
        held_valid <= 1;
        held_bundle <= cmd_bundle;
      end else if (cmd_valid && cmd_ready) begin
        held_valid <= 0;
        $display("P %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
          cmd_layer, cmd_tile, cmd_segment, cmd_operation_consume,
          cmd_source_hbm, cmd_source_endpoint, cmd_destination_cluster,
          cmd_plane, cmd_canonical_byte_address, cmd_source_byte_address,
          cmd_destination_is_resident_cache, cmd_destination_byte_address,
          cmd_packet_index, cmd_tag, cmd_flit_count, cmd_descriptor_last,
          cmd_schedule_last);
        if (cmd_schedule_last)
          schedule_done <= 1;
      end
      if (cycle > 32'd10000) begin
        $display("FAIL timeout");
        $finish(1);
      end
    end
  end

  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1;
{drives}
    while (!schedule_done) @(posedge clk);
    @(negedge clk);
    if (protocol_error || accepted_descriptor_count != 14'd4 ||
        generated_packet_count != 25'd5120) begin
      $display("FAIL error=%0d descriptors=%0d packets=%0d", protocol_error,
        accepted_descriptor_count, generated_packet_count);
      $finish(1);
    end
    $display("PASS descriptors=%0d packets=%0d", accepted_descriptor_count,
      generated_packet_count);
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "packetizer.vvp"
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
        if line.startswith("P ")
    ]
    expected = []
    for descriptor in descriptors:
        expected.extend(
            (
                packet.layer,
                packet.tile,
                packet.segment,
                int(packet.operation == CONSUME),
                int(packet.source == HBM),
                packet.source_endpoint,
                packet.destination_cluster,
                packet.plane,
                packet.canonical_byte_address,
                packet.source_byte_address,
                int(packet.destination_is_resident_cache),
                packet.destination_byte_address,
                packet.packet_index,
                packet.tag,
                packet.flit_count,
                int(packet.descriptor_last),
                int(packet.schedule_last),
            )
            for packet in packet_commands(descriptor)
        )
    assert observed == expected
    assert "PASS descriptors=4 packets=5120" in result.stdout


def test_rtl_rejects_each_address_space_overflow(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "overflow_tb.sv"
    tb.write_text(
        """`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg desc_valid = 0;
  wire desc_ready;
  reg [4:0] desc_layer = 0;
  reg [6:0] desc_tile = 0;
  reg [3:0] desc_segment = 0;
  reg desc_operation_consume = 1;
  reg desc_source_hbm = 1;
  reg [3:0] desc_source_endpoint = 0;
  reg [3:0] desc_destination_cluster = 1;
  reg [3:0] desc_plane = 0;
  reg [19:0] desc_canonical_base_address = 0;
  reg [33:0] desc_source_byte_address = 0;
  reg desc_destination_is_resident_cache = 0;
  reg [33:0] desc_destination_byte_address = 0;
  reg [20:0] desc_payload_bytes = 512;
  reg desc_last = 0;
  wire protocol_error;

  attention_kv_gather_span_packetizer dut (
    .clk(clk), .rst_n(rst_n),
    .desc_valid(desc_valid), .desc_ready(desc_ready),
    .desc_layer(desc_layer), .desc_tile(desc_tile), .desc_segment(desc_segment),
    .desc_operation_consume(desc_operation_consume),
    .desc_source_hbm(desc_source_hbm),
    .desc_source_endpoint(desc_source_endpoint),
    .desc_destination_cluster(desc_destination_cluster), .desc_plane(desc_plane),
    .desc_canonical_base_address(desc_canonical_base_address),
    .desc_source_byte_address(desc_source_byte_address),
    .desc_destination_is_resident_cache(desc_destination_is_resident_cache),
    .desc_destination_byte_address(desc_destination_byte_address),
    .desc_payload_bytes(desc_payload_bytes), .desc_last(desc_last),
    .cmd_ready(1'b0), .protocol_error(protocol_error)
  );
  always #1 clk = ~clk;

  task automatic reset_and_submit;
    begin
      rst_n = 0;
      desc_valid = 0;
      repeat (2) @(posedge clk);
      @(negedge clk); rst_n = 1; desc_valid = 1;
      if (!desc_ready) begin
        $display("FAIL descriptor unexpectedly blocked");
        $finish(1);
      end
      @(posedge clk);
      @(negedge clk); desc_valid = 0;
      if (!protocol_error) begin
        $display("FAIL overflow accepted");
        $finish(1);
      end
    end
  endtask

  initial begin
    desc_canonical_base_address = 20'hfff00;
    reset_and_submit();
    desc_canonical_base_address = 0;
    desc_source_byte_address = 34'h3ffffff00;
    reset_and_submit();
    desc_source_byte_address = 0;
    desc_destination_byte_address = 34'h3ffffff00;
    reset_and_submit();
    $display("PASS overflow checks");
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / "overflow.vvp"
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
    assert "PASS overflow checks" in result.stdout
