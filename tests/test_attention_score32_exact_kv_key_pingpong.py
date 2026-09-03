from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)
from npu.sim.perf.attention_kv_tile_layout import key_ingress_architecture_service


ROOT = Path(__file__).resolve().parents[1]
TRANSPOSE_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv"
STAGE_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_stage_wide.sv"
COMPOSED_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_ingress.sv"


def test_key_ingress_architecture_service_bounds() -> None:
    expected = {
        "one_buffer_serial": (1, 128, False, 12_351),
        "pingpong_serial": (2, 128, True, 8_256),
        "one_buffer_wide": (1, 256, False, 8_255),
        "pingpong_wide_auto": (2, 256, True, 4_160),
    }
    for name, row in expected.items():
        service = key_ingress_architecture_service(architecture=name)
        assert (
            service.transpose_buffers,
            service.stage_write_bits,
            service.target_from_first_flit,
            service.head_cycles_without_stall,
        ) == row
        assert service.ingress_floor_cycles == 4_096


def _testbench(*, producers: int, group: int) -> str:
    counts = exact_local_cluster_gqa8_command_block_counts(
        producers=producers, group_index=group
    )
    bases = exact_local_cluster_gqa8_slot_bases(
        producers=producers, group_index=group
    )
    init = "\n".join(
        f"    base_mem[{producer}] = 6'd{bases[producer]}; "
        f"count_mem[{producer}] = 2'd{counts[producer]};"
        for producer in range(producers)
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam [1:0] GROUP = 2'd{group};
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer block_slot;
  integer stream;
  integer token_lane;
  integer chunk;
  integer byte_lane;
  integer dimension;
  integer producer;
  integer ready_i;
  integer check_i;
  integer ingress_accepts = 0;
  integer ingress_stalls = 0;
  integer first_ingress_cycle = -1;
  integer last_ingress_cycle = -1;
  integer accepted [0:PRODUCERS-1];
  reg [5:0] base_mem [0:PRODUCERS-1];
  reg [1:0] count_mem [0:PRODUCERS-1];

  reg fill_target_valid = 0;
  wire fill_target_ready;
  reg [1:0] fill_target_kv_head = GROUP;
  reg query_write_valid = 0;
  wire query_write_ready;
  reg [1:0] query_write_kv_head = GROUP;
  reg [6:0] query_write_dimension = 0;
  reg [63:0] query_write_data = 0;
  reg query_write_last = 0;
  reg ingress_valid = 0;
  wire ingress_ready;
  reg [19:0] ingress_tile_byte_addr = 0;
  reg [255:0] ingress_data = 0;
  reg [31:0] ingress_byte_valid = 0;
  wire fill_complete;
  reg command_valid = 0;
  wire command_ready;
  reg [1:0] command_kv_head = GROUP;
  wire [PRODUCERS-1:0] producer_valid;
  reg [PRODUCERS-1:0] producer_ready;
  wire [PRODUCERS-1:0] producer_last;
  wire [(PRODUCERS*128)-1:0] producer_query;
  wire [(PRODUCERS*128)-1:0] producer_key;
  wire command_done;
  wire protocol_error;

  function automatic [7:0] key_byte;
    input [5:0] slot_i;
    input [6:0] dim_i;
    input [3:0] lane_i;
    begin
      key_byte = slot_i * 17 + dim_i * 3 + lane_i * 11 + 5;
    end
  endfunction

  function automatic [127:0] key_pattern;
    input [5:0] slot_i;
    input [6:0] dim_i;
    integer lane_i;
    begin
      for (lane_i = 0; lane_i < 16; lane_i = lane_i + 1)
        key_pattern[(lane_i*8) +: 8] = key_byte(slot_i, dim_i, lane_i);
    end
  endfunction

  function automatic [63:0] query_pattern;
    input [6:0] dim_i;
    reg [31:0] word;
    begin
      word = {{23'd0, GROUP, dim_i}};
      query_pattern = {{word ^ 32'h3ca55ac3, word}};
    end
  endfunction

  attention_score32_exact_kv_key_pingpong_ingress #(.PRODUCERS(PRODUCERS)) dut (.*);
  always #1 clk = ~clk;

  always @(*) begin
    for (ready_i = 0; ready_i < PRODUCERS; ready_i = ready_i + 1)
      producer_ready[ready_i] = ((cycle + ready_i) % 7) != 0;
  end

  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (ingress_valid && ingress_ready) begin
      if (first_ingress_cycle < 0)
        first_ingress_cycle <= cycle;
      last_ingress_cycle <= cycle;
      ingress_accepts <= ingress_accepts + 1;
    end else if (ingress_valid) begin
      ingress_stalls <= ingress_stalls + 1;
    end
    for (check_i = 0; check_i < PRODUCERS; check_i = check_i + 1) begin
      if (producer_valid[check_i] && producer_ready[check_i]) begin
        if (producer_key[(check_i*128) +: 128] !==
            key_pattern(base_mem[check_i] + (accepted[check_i] / 128),
                        accepted[check_i] % 128)) begin
          $display("KEY_MISMATCH producer=%0d beat=%0d", check_i, accepted[check_i]);
          $finish(1);
        end
        if (producer_query[(check_i*128) +: 128] !==
            {{2{{query_pattern(accepted[check_i] % 128)}}}}) begin
          $display("QUERY_MISMATCH producer=%0d beat=%0d", check_i, accepted[check_i]);
          $finish(1);
        end
        if (producer_last[check_i] !== ((accepted[check_i] % 128) == 127)) begin
          $display("LAST_MISMATCH producer=%0d beat=%0d", check_i, accepted[check_i]);
          $finish(1);
        end
        accepted[check_i] <= accepted[check_i] + 1;
      end
    end
    if (cycle > 15000) begin
      $display("TIMEOUT");
      $finish(1);
    end
  end

  initial begin
{init}
    for (producer = 0; producer < PRODUCERS; producer = producer + 1)
      accepted[producer] = 0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;
    fill_target_valid = 1;
    @(posedge clk);
    @(negedge clk);
    fill_target_valid = 0;

    for (dimension = 0; dimension < 128; dimension = dimension + 1) begin
      query_write_dimension = dimension;
      query_write_data = query_pattern(dimension);
      query_write_last = dimension == 127;
      query_write_valid = 1;
      @(posedge clk);
      @(negedge clk);
    end
    query_write_valid = 0;

    ingress_valid = 1;
    ingress_byte_valid = 32'hffff_ffff;
    for (block_slot = 0; block_slot < 64; block_slot = block_slot + 1) begin
      for (stream = 0; stream < 2; stream = stream + 1) begin
        for (token_lane = 0; token_lane < 8; token_lane = token_lane + 1) begin
          for (chunk = 0; chunk < 4; chunk = chunk + 1) begin
            ingress_tile_byte_addr = (GROUP * 20'd131072) |
              (stream << 16) | (block_slot << 10) | (token_lane << 7) | (chunk << 5);
            for (byte_lane = 0; byte_lane < 32; byte_lane = byte_lane + 1)
              ingress_data[(byte_lane*8) +: 8] =
                key_byte(block_slot, chunk * 32 + byte_lane,
                         stream * 8 + token_lane);
            while (!ingress_ready) @(posedge clk);
            @(posedge clk);
            @(negedge clk);
          end
        end
      end
    end
    ingress_valid = 0;

    repeat (63) @(posedge clk);
    @(negedge clk);
    if (fill_complete) begin
      $display("EARLY_FILL_COMPLETE");
      $finish(1);
    end
    @(posedge clk);
    @(negedge clk);
    if (!fill_complete || ingress_accepts != 4096 || ingress_stalls != 0 ||
        last_ingress_cycle - first_ingress_cycle + 1 != 4096 || protocol_error) begin
      $display("INGRESS_FAIL complete=%0d accepts=%0d stalls=%0d span=%0d error=%0d",
               fill_complete, ingress_accepts, ingress_stalls,
               last_ingress_cycle - first_ingress_cycle + 1, protocol_error);
      $finish(1);
    end

    command_valid = 1;
    @(posedge clk);
    @(negedge clk);
    command_valid = 0;
    while (!command_done) @(posedge clk);
    @(negedge clk);
    for (producer = 0; producer < PRODUCERS; producer = producer + 1)
      if (accepted[producer] != count_mem[producer] * 128) begin
        $display("COUNT_MISMATCH producer=%0d expected=%0d got=%0d",
                 producer, count_mem[producer] * 128, accepted[producer]);
        $finish(1);
      end
    if (protocol_error) begin
      $display("PROTOCOL_ERROR");
      $finish(1);
    end
    $display("PASS producers=%0d group=%0d cycles=%0d ingress_span=%0d",
             PRODUCERS, GROUP, cycle,
             last_ingress_cycle - first_ingress_cycle + 1);
    $finish(0);
  end
endmodule
"""


@pytest.mark.parametrize(("producers", "group"), [(53, 3), (54, 2)])
def test_pingpong_wide_ingress_sustains_flit_rate_and_drives_producers(
    tmp_path: Path, producers: int, group: int
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / f"tb_p{producers}.sv"
    tb.write_text(_testbench(producers=producers, group=group), encoding="utf-8")
    binary = tmp_path / f"sim_p{producers}.vvp"
    compiled = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            str(TRANSPOSE_RTL),
            str(STAGE_RTL),
            str(COMPOSED_RTL),
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
    assert f"PASS producers={producers} group={group}" in completed.stdout
    assert "ingress_span=4096" in completed.stdout
