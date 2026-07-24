from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    return None


_SUMMARY_RE = re.compile(
    r"SUMMARY backend_match=(\d+) "
    r"accepted=(\d+) emitted=(\d+) fragments=(\d+) bank_conflict=(\d+) response_block=(\d+) "
    r"req_max=(\d+) resp_max=(\d+) completion_cycle=(\d+) "
    r"beh_req_hash=([0-9a-fA-F]+) macro_req_hash=([0-9a-fA-F]+) "
    r"beh_resp_hash=([0-9a-fA-F]+) macro_resp_hash=([0-9a-fA-F]+)"
)


_TB = r"""
`timescale 1ns/1ps

module banked_value_memory_service_backend_tb;
  localparam integer PACKET_W = 128;
  localparam integer VALUE_W = 512;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 14;
  localparam integer VALUE_SLICE_W = 4;
  localparam integer STORE_DEPTH = 16;
  localparam integer BANKS = 4;
  localparam integer BANK_QUEUE_DEPTH = 4;
  localparam integer READ_LATENCY = 2;
  localparam integer COUNTER_W = 32;
  localparam integer REQUEST_COUNT = 16;
  localparam integer EXPECTED_FRAGMENTS = REQUEST_COUNT * (VALUE_W / PACKET_W);

  reg clk;
  reg rst_n;

  reg preload_valid;
  wire preload_ready_beh;
  wire preload_ready_macro;
  reg [ADDR_W-1:0] preload_addr;
  reg [VALUE_SLICE_W-1:0] preload_value_slice;
  reg [VALUE_W-1:0] preload_matrix;

  reg req_valid;
  wire req_ready_beh;
  wire req_ready_macro;
  reg [SOURCE_W-1:0] req_source;
  reg [TAG_W-1:0] req_tag;
  reg [ADDR_W-1:0] req_addr;
  reg [VALUE_SLICE_W-1:0] req_value_slice;

  wire resp_valid_beh;
  wire resp_valid_macro;
  reg resp_ready;
  wire [SOURCE_W-1:0] resp_source_beh;
  wire [SOURCE_W-1:0] resp_source_macro;
  wire [TAG_W-1:0] resp_tag_beh;
  wire [TAG_W-1:0] resp_tag_macro;
  wire [ADDR_W-1:0] resp_addr_beh;
  wire [ADDR_W-1:0] resp_addr_macro;
  wire [VALUE_SLICE_W-1:0] resp_value_slice_beh;
  wire [VALUE_SLICE_W-1:0] resp_value_slice_macro;
  wire [1:0] resp_fragment_idx_beh;
  wire [1:0] resp_fragment_idx_macro;
  wire resp_last_beh;
  wire resp_last_macro;
  wire [PACKET_W-1:0] resp_data_beh;
  wire [PACKET_W-1:0] resp_data_macro;

  wire [COUNTER_W-1:0] accepted_req_count_beh;
  wire [COUNTER_W-1:0] accepted_req_count_macro;
  wire [COUNTER_W-1:0] emitted_resp_count_beh;
  wire [COUNTER_W-1:0] emitted_resp_count_macro;
  wire [COUNTER_W-1:0] bank_conflict_count_beh;
  wire [COUNTER_W-1:0] bank_conflict_count_macro;
  wire [COUNTER_W-1:0] response_block_cycles_beh;
  wire [COUNTER_W-1:0] response_block_cycles_macro;
  wire [COUNTER_W-1:0] req_current_occupancy_beh;
  wire [COUNTER_W-1:0] req_current_occupancy_macro;
  wire [COUNTER_W-1:0] req_max_occupancy_beh;
  wire [COUNTER_W-1:0] req_max_occupancy_macro;
  wire [COUNTER_W-1:0] resp_current_occupancy_beh;
  wire [COUNTER_W-1:0] resp_current_occupancy_macro;
  wire [COUNTER_W-1:0] resp_max_occupancy_beh;
  wire [COUNTER_W-1:0] resp_max_occupancy_macro;

  reg [ADDR_W-1:0] req_plan_addr [0:REQUEST_COUNT-1];
  reg [VALUE_SLICE_W-1:0] req_plan_slice [0:REQUEST_COUNT-1];
  reg [SOURCE_W-1:0] req_plan_source [0:REQUEST_COUNT-1];
  integer cycle;
  integer fragment_count;
  integer completion_cycle_beh;
  integer completion_cycle_macro;
  reg [63:0] req_hash_beh;
  reg [63:0] req_hash_macro;
  reg [63:0] resp_hash_beh;
  reg [63:0] resp_hash_macro;
  integer req_index;
  integer guard_cycles;

  function [63:0] mix64;
    input [63:0] state;
    input [63:0] word;
    begin
      mix64 = {state[56:0], state[63:57]} ^ (word + 64'h9e3779b97f4a7c15);
    end
  endfunction

  function [511:0] make_matrix;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    integer lane_i;
    reg [31:0] word_value;
    reg [15:0] low_word;
    begin
      make_matrix = {VALUE_W{1'b0}};
      for (lane_i = 0; lane_i < 16; lane_i = lane_i + 1) begin
        low_word = (((addr * 16) + value_slice) * 17 + lane_i) & 16'hffff;
        word_value = {
          8'h80 ^ addr[7:0],
          4'ha ^ value_slice,
          lane_i[3:0],
          low_word
        };
        make_matrix[(lane_i * 32) +: 32] = word_value;
      end
    end
  endfunction

  task automatic clear_inputs;
    begin
      preload_valid = 1'b0;
      preload_addr = {ADDR_W{1'b0}};
      preload_value_slice = {VALUE_SLICE_W{1'b0}};
      preload_matrix = {VALUE_W{1'b0}};
      req_valid = 1'b0;
      req_source = {SOURCE_W{1'b0}};
      req_tag = {TAG_W{1'b0}};
      req_addr = {ADDR_W{1'b0}};
      req_value_slice = {VALUE_SLICE_W{1'b0}};
    end
  endtask

  task automatic drive_idle_cycle;
    begin
      @(negedge clk);
      clear_inputs();
    end
  endtask

  task automatic drive_preload_cycle;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    begin
      @(negedge clk);
      if (preload_ready_beh !== preload_ready_macro) begin
        $fatal(1, "preload_ready mismatch before preload");
      end
      clear_inputs();
      preload_valid = 1'b1;
      preload_addr = addr;
      preload_value_slice = value_slice;
      preload_matrix = make_matrix(addr, value_slice);
    end
  endtask

  task automatic drive_request_cycle;
    input integer plan_index;
    input integer issue_preload;
    input [ADDR_W-1:0] preload_addr_i;
    input [VALUE_SLICE_W-1:0] preload_slice_i;
    reg issued;
    begin
      issued = 1'b0;
      while (!issued) begin
        @(negedge clk);
        if (req_ready_beh !== req_ready_macro) begin
          $fatal(1, "req_ready mismatch before request %0d", plan_index);
        end
        clear_inputs();
        if (req_ready_beh) begin
          req_valid = 1'b1;
          req_source = req_plan_source[plan_index];
          req_tag = plan_index[TAG_W-1:0];
          req_addr = req_plan_addr[plan_index];
          req_value_slice = req_plan_slice[plan_index];
          if (issue_preload != 0) begin
            preload_valid = 1'b1;
            preload_addr = preload_addr_i;
            preload_value_slice = preload_slice_i;
            preload_matrix = make_matrix(preload_addr_i, preload_slice_i);
          end
          issued = 1'b1;
        end
      end
    end
  endtask

  banked_value_memory_service #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W),
    .STORE_DEPTH(STORE_DEPTH),
    .BANKS(BANKS),
    .BANK_QUEUE_DEPTH(BANK_QUEUE_DEPTH),
    .READ_LATENCY(READ_LATENCY),
    .COUNTER_W(COUNTER_W),
    .INIT_FROM_GENERATOR(0),
    .MEMORY_IMPL(0)
  ) u_behavioral (
    .clk(clk),
    .rst_n(rst_n),
    .preload_valid(preload_valid),
    .preload_ready(preload_ready_beh),
    .preload_addr(preload_addr),
    .preload_value_slice(preload_value_slice),
    .preload_matrix(preload_matrix),
    .req_valid(req_valid),
    .req_ready(req_ready_beh),
    .req_source(req_source),
    .req_tag(req_tag),
    .req_addr(req_addr),
    .req_value_slice(req_value_slice),
    .resp_valid(resp_valid_beh),
    .resp_ready(resp_ready),
    .resp_source(resp_source_beh),
    .resp_tag(resp_tag_beh),
    .resp_addr(resp_addr_beh),
    .resp_value_slice(resp_value_slice_beh),
    .resp_fragment_idx(resp_fragment_idx_beh),
    .resp_last(resp_last_beh),
    .resp_data(resp_data_beh),
    .accepted_req_count(accepted_req_count_beh),
    .emitted_resp_count(emitted_resp_count_beh),
    .bank_conflict_count(bank_conflict_count_beh),
    .response_block_cycles(response_block_cycles_beh),
    .req_current_occupancy(req_current_occupancy_beh),
    .req_max_occupancy(req_max_occupancy_beh),
    .resp_current_occupancy(resp_current_occupancy_beh),
    .resp_max_occupancy(resp_max_occupancy_beh)
  );

  banked_value_memory_service #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W),
    .STORE_DEPTH(STORE_DEPTH),
    .BANKS(BANKS),
    .BANK_QUEUE_DEPTH(BANK_QUEUE_DEPTH),
    .READ_LATENCY(READ_LATENCY),
    .COUNTER_W(COUNTER_W),
    .INIT_FROM_GENERATOR(0),
    .MEMORY_IMPL(1)
  ) u_macro (
    .clk(clk),
    .rst_n(rst_n),
    .preload_valid(preload_valid),
    .preload_ready(preload_ready_macro),
    .preload_addr(preload_addr),
    .preload_value_slice(preload_value_slice),
    .preload_matrix(preload_matrix),
    .req_valid(req_valid),
    .req_ready(req_ready_macro),
    .req_source(req_source),
    .req_tag(req_tag),
    .req_addr(req_addr),
    .req_value_slice(req_value_slice),
    .resp_valid(resp_valid_macro),
    .resp_ready(resp_ready),
    .resp_source(resp_source_macro),
    .resp_tag(resp_tag_macro),
    .resp_addr(resp_addr_macro),
    .resp_value_slice(resp_value_slice_macro),
    .resp_fragment_idx(resp_fragment_idx_macro),
    .resp_last(resp_last_macro),
    .resp_data(resp_data_macro),
    .accepted_req_count(accepted_req_count_macro),
    .emitted_resp_count(emitted_resp_count_macro),
    .bank_conflict_count(bank_conflict_count_macro),
    .response_block_cycles(response_block_cycles_macro),
    .req_current_occupancy(req_current_occupancy_macro),
    .req_max_occupancy(req_max_occupancy_macro),
    .resp_current_occupancy(resp_current_occupancy_macro),
    .resp_max_occupancy(resp_max_occupancy_macro)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (rst_n) begin
      if (req_valid && req_ready_beh && req_ready_macro) begin
        req_hash_beh <= mix64(
          req_hash_beh,
          {44'd0, req_source, req_tag, req_addr[7:0], req_value_slice, cycle[7:0]}
        );
        req_hash_macro <= mix64(
          req_hash_macro,
          {44'd0, req_source, req_tag, req_addr[7:0], req_value_slice, cycle[7:0]}
        );
      end
      if (resp_valid_beh && resp_ready) begin
        fragment_count <= fragment_count + 1;
        resp_hash_beh <= mix64(
          resp_hash_beh,
          resp_data_beh[63:0] ^ resp_data_beh[127:64] ^
          {40'd0, resp_source_beh, resp_tag_beh, resp_addr_beh[7:0], resp_value_slice_beh, resp_fragment_idx_beh, resp_last_beh}
        );
        if (resp_last_beh && (completion_cycle_beh < 0) &&
            (emitted_resp_count_beh + 1 == REQUEST_COUNT)) begin
          completion_cycle_beh <= cycle;
        end
      end
      if (resp_valid_macro && resp_ready) begin
        resp_hash_macro <= mix64(
          resp_hash_macro,
          resp_data_macro[63:0] ^ resp_data_macro[127:64] ^
          {40'd0, resp_source_macro, resp_tag_macro, resp_addr_macro[7:0], resp_value_slice_macro, resp_fragment_idx_macro, resp_last_macro}
        );
        if (resp_last_macro && (completion_cycle_macro < 0) &&
            (emitted_resp_count_macro + 1 == REQUEST_COUNT)) begin
          completion_cycle_macro <= cycle;
        end
      end
    end
  end

  always @(*) begin
    resp_ready = rst_n && ((cycle % 7) != 3);
  end

  always @(negedge clk) begin
    if (!rst_n) begin
      if (resp_valid_beh !== resp_valid_macro) begin
        $fatal(1, "resp_valid mismatch during reset release");
      end
    end else begin
      if (preload_ready_beh !== preload_ready_macro) begin
        $fatal(1, "preload_ready mismatch");
      end
      if (req_ready_beh !== req_ready_macro) begin
        $fatal(1, "req_ready mismatch");
      end
      if (resp_valid_beh !== resp_valid_macro) begin
        $fatal(1, "resp_valid mismatch cycle=%0d", cycle);
      end
      if (accepted_req_count_beh !== accepted_req_count_macro ||
          emitted_resp_count_beh !== emitted_resp_count_macro ||
          bank_conflict_count_beh !== bank_conflict_count_macro ||
          response_block_cycles_beh !== response_block_cycles_macro ||
          req_current_occupancy_beh !== req_current_occupancy_macro ||
          req_max_occupancy_beh !== req_max_occupancy_macro ||
          resp_current_occupancy_beh !== resp_current_occupancy_macro ||
          resp_max_occupancy_beh !== resp_max_occupancy_macro) begin
        $fatal(1, "counter mismatch cycle=%0d", cycle);
      end
      if (resp_valid_beh) begin
        if (resp_source_beh !== resp_source_macro ||
            resp_tag_beh !== resp_tag_macro ||
            resp_addr_beh !== resp_addr_macro ||
            resp_value_slice_beh !== resp_value_slice_macro ||
            resp_fragment_idx_beh !== resp_fragment_idx_macro ||
            resp_last_beh !== resp_last_macro ||
            resp_data_beh !== resp_data_macro) begin
          $fatal(1, "response payload mismatch cycle=%0d", cycle);
        end
      end
    end
  end

  initial begin
    clk = 1'b0;
    rst_n = 1'b0;
    cycle = 0;
    fragment_count = 0;
    completion_cycle_beh = -1;
    completion_cycle_macro = -1;
    req_hash_beh = 64'h0123_4567_89ab_cdef;
    req_hash_macro = 64'h0123_4567_89ab_cdef;
    resp_hash_beh = 64'hfedc_ba98_7654_3210;
    resp_hash_macro = 64'hfedc_ba98_7654_3210;
    clear_inputs();

    req_plan_addr[0] = 14'd0;   req_plan_slice[0] = 4'd0;  req_plan_source[0] = 2'd0;
    req_plan_addr[1] = 14'd1;   req_plan_slice[1] = 4'd1;  req_plan_source[1] = 2'd1;
    req_plan_addr[2] = 14'd2;   req_plan_slice[2] = 4'd2;  req_plan_source[2] = 2'd2;
    req_plan_addr[3] = 14'd3;   req_plan_slice[3] = 4'd3;  req_plan_source[3] = 2'd3;
    req_plan_addr[4] = 14'd4;   req_plan_slice[4] = 4'd5;  req_plan_source[4] = 2'd0;
    req_plan_addr[5] = 14'd5;   req_plan_slice[5] = 4'd6;  req_plan_source[5] = 2'd1;
    req_plan_addr[6] = 14'd6;   req_plan_slice[6] = 4'd7;  req_plan_source[6] = 2'd2;
    req_plan_addr[7] = 14'd7;   req_plan_slice[7] = 4'd8;  req_plan_source[7] = 2'd3;
    req_plan_addr[8] = 14'd8;   req_plan_slice[8] = 4'd10; req_plan_source[8] = 2'd0;
    req_plan_addr[9] = 14'd9;   req_plan_slice[9] = 4'd11; req_plan_source[9] = 2'd1;
    req_plan_addr[10] = 14'd10; req_plan_slice[10] = 4'd12; req_plan_source[10] = 2'd2;
    req_plan_addr[11] = 14'd11; req_plan_slice[11] = 4'd13; req_plan_source[11] = 2'd3;
    req_plan_addr[12] = 14'd12; req_plan_slice[12] = 4'd15; req_plan_source[12] = 2'd0;
    req_plan_addr[13] = 14'd13; req_plan_slice[13] = 4'd14; req_plan_source[13] = 2'd1;
    req_plan_addr[14] = 14'd14; req_plan_slice[14] = 4'd9;  req_plan_source[14] = 2'd2;
    req_plan_addr[15] = 14'd15; req_plan_slice[15] = 4'd4;  req_plan_source[15] = 2'd3;

    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    for (req_index = 0; req_index < 12; req_index = req_index + 1) begin
      drive_preload_cycle(req_plan_addr[req_index], req_plan_slice[req_index]);
    end
    drive_idle_cycle();

    drive_request_cycle(0, 1, req_plan_addr[13], req_plan_slice[13]);
    drive_request_cycle(1, 1, req_plan_addr[14], req_plan_slice[14]);
    drive_request_cycle(2, 1, req_plan_addr[15], req_plan_slice[15]);
    drive_request_cycle(3, 1, req_plan_addr[12], req_plan_slice[12]);
    for (req_index = 4; req_index < REQUEST_COUNT; req_index = req_index + 1) begin
      drive_request_cycle(req_index, 0, {ADDR_W{1'b0}}, {VALUE_SLICE_W{1'b0}});
    end

    guard_cycles = 0;
    while ((emitted_resp_count_beh < REQUEST_COUNT) || (emitted_resp_count_macro < REQUEST_COUNT) ||
           resp_valid_beh || resp_valid_macro) begin
      drive_idle_cycle();
      guard_cycles = guard_cycles + 1;
      if (guard_cycles > 600) begin
        $fatal(
          1,
          "timeout waiting for service completion accepted=%0d emitted=%0d req_occ=%0d resp_occ=%0d resp_valid=%0d",
          accepted_req_count_beh,
          emitted_resp_count_beh,
          req_current_occupancy_beh,
          resp_current_occupancy_beh,
          resp_valid_beh
        );
      end
    end

    if (req_hash_beh !== req_hash_macro) begin
      $fatal(1, "request hash mismatch");
    end
    if (resp_hash_beh !== resp_hash_macro) begin
      $fatal(1, "response hash mismatch");
    end
    if (completion_cycle_beh !== completion_cycle_macro) begin
      $fatal(1, "completion cycle mismatch");
    end
    if (accepted_req_count_beh !== REQUEST_COUNT || emitted_resp_count_beh !== REQUEST_COUNT) begin
      $fatal(1, "unexpected request/response completion counts");
    end
    if (fragment_count !== EXPECTED_FRAGMENTS) begin
      $fatal(1, "unexpected fragment count %0d", fragment_count);
    end

    $display(
      "SUMMARY backend_match=1 accepted=%0d emitted=%0d fragments=%0d bank_conflict=%0d response_block=%0d req_max=%0d resp_max=%0d completion_cycle=%0d beh_req_hash=%016x macro_req_hash=%016x beh_resp_hash=%016x macro_resp_hash=%016x",
      accepted_req_count_beh,
      emitted_resp_count_beh,
      fragment_count,
      bank_conflict_count_beh,
      response_block_cycles_beh,
      req_max_occupancy_beh,
      resp_max_occupancy_beh,
      completion_cycle_beh,
      req_hash_beh,
      req_hash_macro,
      resp_hash_beh,
      resp_hash_macro
    );
    $finish;
  end
endmodule
"""


def test_banked_value_memory_service_macro_backend_matches_behavioral(tmp_path: Path) -> None:
    iverilog = _tool("iverilog")
    vvp = _tool("vvp")
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")

    tb_path = tmp_path / "banked_value_memory_service_backend_tb.sv"
    simv_path = tmp_path / "banked_value_memory_service_backend_tb.vvp"
    tb_path.write_text(_TB, encoding="utf-8")

    compile_run = subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "banked_value_memory_service_backend_tb",
            "-o",
            str(simv_path),
            str(tb_path),
            str(REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv"),
            str(REPO_ROOT / "npu/sim/rtl/banked_value_memory_service.sv"),
            str(REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_run.returncode == 0, compile_run.stderr

    sim_run = subprocess.run(
        [vvp, str(simv_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert sim_run.returncode == 0, sim_run.stderr or sim_run.stdout

    match = _SUMMARY_RE.search(sim_run.stdout)
    assert match is not None, sim_run.stdout
    (
        backend_match,
        accepted,
        emitted,
        fragments,
        bank_conflict,
        response_block,
        req_max,
        resp_max,
        completion_cycle,
        beh_req_hash,
        macro_req_hash,
        beh_resp_hash,
        macro_resp_hash,
    ) = match.groups()

    assert backend_match == "1"
    assert accepted == "16"
    assert emitted == "16"
    assert fragments == "64"
    assert int(bank_conflict) > 0
    assert int(response_block) > 0
    assert int(req_max) > 0
    assert int(resp_max) > 0
    assert int(completion_cycle) > 0
    assert beh_req_hash == macro_req_hash
    assert beh_resp_hash == macro_resp_hash
