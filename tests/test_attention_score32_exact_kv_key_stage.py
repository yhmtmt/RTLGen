from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)
from npu.sim.perf.attention_kv_tile_layout import (
    KEY_HEAD_TILE_ONE_BUFFER_FILL_CYCLES,
    KEY_STAGE_COMMAND_INPUT_CYCLES,
)


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_stage.sv"
TRANSPOSE_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_ingress_transpose.sv"
COMPOSED_RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_ingress.sv"


def test_one_buffer_full_head_service_bound_is_explicit() -> None:
    assert KEY_HEAD_TILE_ONE_BUFFER_FILL_CYCLES == 12_351
    assert KEY_STAGE_COMMAND_INPUT_CYCLES == 256


def _testbench(*, producers: int, group: int, composed: bool = False) -> str:
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
    dut = (
        "attention_score32_exact_kv_key_ingress #(.PRODUCERS(PRODUCERS)) dut (.*);"
        if composed
        else "attention_score32_exact_kv_key_stage #(.PRODUCERS(PRODUCERS)) dut (.*);"
    )
    if composed:
        key_fill = """
    for (block_index = 0; block_index < 64; block_index = block_index + 1) begin
      while (!key_block_target_ready) @(posedge clk);
      @(negedge clk);
      key_block_target_slot = block_index;
      key_block_target_valid = 1;
      @(posedge clk);
      @(negedge clk);
      key_block_target_valid = 0;
      for (stream = 0; stream < 2; stream = stream + 1) begin
        for (token_lane = 0; token_lane < 8; token_lane = token_lane + 1) begin
          for (chunk = 0; chunk < 4; chunk = chunk + 1) begin
            ingress_tile_byte_addr =
              (GROUP * 20'd131072) +
              ((stream * 512 + block_index * 8 + token_lane) * 128) +
              (chunk * 32);
            for (byte_lane = 0; byte_lane < 32; byte_lane = byte_lane + 1)
              ingress_data[(byte_lane*8) +: 8] =
                key_byte(block_index, chunk * 32 + byte_lane, stream * 8 + token_lane);
            ingress_byte_valid = 32'hffff_ffff;
            ingress_valid = 1;
            @(posedge clk);
            @(negedge clk);
          end
        end
      end
      ingress_valid = 0;
    end
    while (!fill_complete) @(posedge clk);
"""
    else:
        key_fill = """
    for (producer = 0; producer < PRODUCERS; producer = producer + 1) begin
      for (block_index = 0; block_index < count_mem[producer]; block_index = block_index + 1) begin
        for (dimension = 0; dimension < 128; dimension = dimension + 1) begin
          key_write_producer = producer;
          key_write_producer_block = block_index;
          key_write_dimension = dimension;
          key_write_data = key_pattern(base_mem[producer] + block_index, dimension);
          key_write_last = dimension == 127;
          key_write_valid = 1;
          @(posedge clk);
          @(negedge clk);
        end
      end
    end
    key_write_valid = 0;
"""
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam [1:0] GROUP = 2'd{group};
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer producer;
  integer ready_i;
  integer check_i;
  integer block_index;
  integer dimension;
  integer stream;
  integer token_lane;
  integer chunk;
  integer byte_lane;
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
  reg key_write_valid = 0;
  wire key_write_ready;
  reg [1:0] key_write_kv_head = GROUP;
  reg [5:0] key_write_producer = 0;
  reg key_write_producer_block = 0;
  reg [6:0] key_write_dimension = 0;
  reg [127:0] key_write_data = 0;
  reg key_write_last = 0;
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
  reg key_block_target_valid = 0;
  wire key_block_target_ready;
  reg [1:0] key_block_target_kv_head = GROUP;
  reg [5:0] key_block_target_slot = 0;
  reg ingress_valid = 0;
  wire ingress_ready;
  reg [19:0] ingress_tile_byte_addr = 0;
  reg [255:0] ingress_data = 0;
  reg [31:0] ingress_byte_valid = 0;

  function automatic [7:0] key_byte;
    input [5:0] slot;
    input [6:0] dim;
    input [3:0] lane;
    begin
      key_byte = slot * 17 + dim * 3 + lane * 11 + 5;
    end
  endfunction

  function automatic [127:0] key_pattern;
    input [5:0] slot;
    input [6:0] dim;
    integer lane;
    begin
      for (lane = 0; lane < 16; lane = lane + 1)
        key_pattern[(lane*8) +: 8] = key_byte(slot, dim, lane);
    end
  endfunction

  function automatic [63:0] query_pattern;
    input [6:0] dim;
    reg [31:0] word;
    begin
      word = {{23'd0, GROUP, dim}};
      query_pattern = {{word ^ 32'h3ca55ac3, word}};
    end
  endfunction

  {dut}
  always #1 clk = ~clk;

  always @(*) begin
    for (ready_i = 0; ready_i < PRODUCERS; ready_i = ready_i + 1)
      producer_ready[ready_i] = ((cycle + ready_i) % 7) != 0;
  end

  always @(posedge clk) begin
    cycle <= cycle + 1;
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
        if (producer_last[check_i] !==
            ((accepted[check_i] % 128) == 127)) begin
          $display("LAST_MISMATCH producer=%0d beat=%0d", check_i, accepted[check_i]);
          $finish(1);
        end
        accepted[check_i] <= accepted[check_i] + 1;
      end
    end
    if (cycle > 30000) begin
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

{key_fill}
    if (!fill_complete || protocol_error) begin
      $display("FILL_FAILED complete=%0d error=%0d", fill_complete, protocol_error);
      $finish(1);
    end

    command_valid = 1;
    @(posedge clk);
    @(negedge clk);
    command_valid = 0;
    while (!command_done) @(posedge clk);
    @(negedge clk);
    for (producer = 0; producer < PRODUCERS; producer = producer + 1) begin
      if (accepted[producer] != count_mem[producer] * 128) begin
        $display("COUNT_MISMATCH producer=%0d expected=%0d got=%0d",
                 producer, count_mem[producer] * 128, accepted[producer]);
        $finish(1);
      end
    end
    if (protocol_error) begin
      $display("PROTOCOL_ERROR");
      $finish(1);
    end
    $display("PASS producers=%0d group=%0d cycles=%0d", PRODUCERS, GROUP, cycle);
    $finish(0);
  end
endmodule
"""


@pytest.mark.parametrize(("producers", "group"), [(53, 3), (54, 2)])
def test_full_key_tile_and_query_group_drive_every_producer(
    tmp_path: Path, producers: int, group: int
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "tb.sv"
    tb.write_text(_testbench(producers=producers, group=group), encoding="utf-8")
    binary = tmp_path / "sim.vvp"
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
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"PASS producers={producers} group={group}" in completed.stdout


@pytest.mark.parametrize(("producers", "group"), [(53, 3), (54, 2)])
def test_canonical_flits_transpose_into_full_parallel_key_stage(
    tmp_path: Path, producers: int, group: int
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    tb = tmp_path / "tb_composed.sv"
    tb.write_text(
        _testbench(producers=producers, group=group, composed=True), encoding="utf-8"
    )
    binary = tmp_path / "composed.vvp"
    compiled = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(binary),
            str(TRANSPOSE_RTL),
            str(RTL),
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
