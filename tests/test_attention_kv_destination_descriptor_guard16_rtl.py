from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_kv_destination_descriptor_guard16.sv"


@pytest.mark.parametrize("width", [16, 22])
def test_destination_guard_waits_for_terminal_packet_completion(tmp_path: Path, width: int) -> None:
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
  reg [3:0] descriptor_source = 0;
  reg [3:0] descriptor_destination = 0;
  wire guarded_valid;
  reg guarded_ready = 1;
  reg [15:0] packet_command_accept = 0;
  reg [16*4-1:0] packet_command_source = 0;
  reg [16*4-1:0] packet_command_destination = 0;
  reg [16*8-1:0] packet_command_tag = 0;
  reg [15:0] packet_command_descriptor_last = 0;
  reg [15:0] packet_completion_valid = 0;
  reg [16*4-1:0] packet_completion_source = 0;
  reg [16*8-1:0] packet_completion_tag = 0;
  wire [15:0] destination_locked;
  wire [15:0] descriptor_final_pending;
  wire [16*4-1:0] locked_descriptor_source;
  wire [TB_COUNT_BITS-1:0] accepted_descriptor_count;
  wire [TB_COUNT_BITS-1:0] completed_descriptor_count;
  wire protocol_error;
  integer span;

  attention_kv_destination_descriptor_guard16 #(.COUNT_WIDTH(TB_COUNT_BITS)) dut (.*);
  always #1 clk = ~clk;

  task accept_descriptor;
    input [3:0] source_i;
    input [3:0] destination_i;
    begin
      descriptor_source = source_i;
      descriptor_destination = destination_i;
      descriptor_valid = 1;
      #0;
      if (!descriptor_ready || !guarded_valid) $finish(1);
      @(posedge clk); @(negedge clk);
      descriptor_valid = 0;
    end
  endtask

  task accept_final_packet;
    input [3:0] source_i;
    input [3:0] destination_i;
    input [7:0] tag_i;
    begin
      packet_command_source[(source_i*4) +: 4] = source_i;
      packet_command_destination[(source_i*4) +: 4] = destination_i;
      packet_command_tag[(source_i*8) +: 8] = tag_i;
      packet_command_descriptor_last[source_i] = 1;
      packet_command_accept[source_i] = 1;
      @(posedge clk); @(negedge clk);
      packet_command_accept = 0;
      packet_command_descriptor_last = 0;
    end
  endtask

  task complete_packet;
    input [3:0] source_i;
    input [3:0] destination_i;
    input [7:0] tag_i;
    begin
      packet_completion_source[(destination_i*4) +: 4] = source_i;
      packet_completion_tag[(destination_i*8) +: 8] = tag_i;
      packet_completion_valid[destination_i] = 1;
      @(posedge clk); @(negedge clk);
      packet_completion_valid = 0;
    end
  endtask

  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk); rst_n = 1;

    accept_descriptor(0, 5);
    if (!destination_locked[5] || locked_descriptor_source[5*4 +: 4] != 0 ||
        accepted_descriptor_count != 1) $finish(1);

    descriptor_source = 3;
    descriptor_destination = 5;
    descriptor_valid = 1;
    #0;
    if (descriptor_ready || guarded_valid) $finish(1);

    descriptor_destination = 6;
    #0;
    if (!descriptor_ready || !guarded_valid) $finish(1);
    @(posedge clk); @(negedge clk);
    descriptor_valid = 0;
    if (!destination_locked[5] || !destination_locked[6] ||
        accepted_descriptor_count != 2) $finish(1);

    accept_final_packet(0, 5, 8'hff);
    if (!descriptor_final_pending[5]) $finish(1);
    complete_packet(0, 5, 8'h7f);
    if (!destination_locked[5] || completed_descriptor_count != 0) $finish(1);
    complete_packet(0, 5, 8'hff);
    if (destination_locked[5] || descriptor_final_pending[5] ||
        completed_descriptor_count != 1) $finish(1);

    accept_descriptor(3, 5);
    accept_final_packet(3, 6, 8'h21);
    complete_packet(3, 6, 8'h21);
    accept_final_packet(3, 5, 8'h44);
    complete_packet(3, 5, 8'h44);
    if (destination_locked != 0 || accepted_descriptor_count != 3 ||
        completed_descriptor_count != 3 || protocol_error) $finish(1);

    // Paired spans reuse packet tags and alternate resident/HBM sources.
    // Cross the old 16-bit boundary through real handshakes, not forced state.
    for (span=0; span<EXTRA_SPANS; span=span+1) begin
      accept_descriptor((span%2) ? 3 : 0, 5);
      accept_final_packet((span%2) ? 3 : 0, 5, 8'h03);
      descriptor_source = (span%2) ? 0 : 3;
      descriptor_destination = 5;
      descriptor_valid = 1;
      repeat(3) begin
        #0;
        if(descriptor_ready || guarded_valid || !destination_locked[5]) $fatal(1,"early ownership transfer");
        @(posedge clk); @(negedge clk);
      end
      descriptor_valid = 0;
      complete_packet((span%2) ? 3 : 0, 5, 8'h03);
      if(destination_locked[5] || protocol_error ||
         accepted_descriptor_count != span+4 || completed_descriptor_count != span+4)
        $fatal(1,"paired count or completion");
    end

    accept_final_packet(7, 7, 8'h55);
    if (!protocol_error) $finish(1);
    descriptor_valid = 1;
    descriptor_source = 1;
    descriptor_destination = 1;
    #0;
    if (descriptor_ready || guarded_valid) $finish(1);

    $display("PASS accepted=%0d completed=%0d",
      accepted_descriptor_count, completed_descriptor_count);
    $finish(0);
  end
endmodule
""".replace("TB_COUNT_BITS", str(width))
        .replace("EXTRA_SPANS", "66000" if width == 22 else "0"),
        encoding="utf-8",
    )
    binary = tmp_path / "guard.vvp"
    compiled = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(RTL), str(tb)],
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
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    total = 66003 if width == 22 else 3
    assert f"PASS accepted={total} completed={total}" in completed.stdout
