#!/usr/bin/env python3
"""Generate exact-partial temporal reduction with macro-backed persistent state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    generate as generate_merge,
)
from npu.sim.perf.attention_exact_partial import (
    HEAD_ID_BITS,
    PARTIAL_PAYLOAD_BITS,
    VALUE_SLICES,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_partial_temporal_stream_sram"
_GENERATOR = "npu/rtlgen/gen_attention_score32_exact_partial_temporal_stream_sram.py"
_MANIFEST = "attention_score32_exact_partial_temporal_stream_sram_manifest.json"
_STATE_BITS = 394
_PHYSICAL_BITS = 416
_STATE_ENTRIES = 512
_BANKS = 8
_MACROS_PER_BANK = 13
_MACRO_COUNT = 104


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clog2(value: int) -> int:
    resolved = 1
    while (1 << resolved) < max(2, int(value)):
        resolved += 1
    return resolved


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")
    heads = int(body.get("heads", 32))
    value_slices = int(body.get("value_slices", VALUE_SLICES))
    head_id_bits = int(body.get("head_id_bits", HEAD_ID_BITS))
    fifo_depth = int(body.get("fifo_depth", 4))
    exp_scale_impl = str(
        body.get("exp_scale_impl", FACTORED_H33_L64_MUL_EXACT)
    ).strip()
    keep_hierarchy = bool(body.get("keep_hierarchy", True))
    if heads != 32 or value_slices != VALUE_SLICES or head_id_bits != HEAD_ID_BITS:
        raise SystemExit("heads/value_slices/head_id_bits must remain fixed at 32/16/5")
    if fifo_depth < 2 or fifo_depth > 16 or fifo_depth & (fifo_depth - 1):
        raise SystemExit("fifo_depth must be a power of two in [2, 16]")
    return {
        "top_name": top_name,
        "fifo_depth": fifo_depth,
        "exp_scale_impl": exp_scale_impl,
        "keep_hierarchy": keep_hierarchy,
    }


def _memory_proxy(module_name: str) -> str:
    return f"""module {module_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         req_valid,
    output wire         req_ready,
    input  wire         req_write,
    input  wire [8:0]   req_addr,
    input  wire [{_STATE_BITS - 1}:0] req_wdata,
    output wire         read_valid,
    input  wire         read_ready,
    output wire [{_STATE_BITS - 1}:0] read_data,
    output reg  [31:0]  request_count,
    output reg  [31:0]  read_request_count,
    output reg  [31:0]  read_response_count,
    output reg  [31:0]  write_count,
    output reg  [31:0]  request_stall_cycles,
    output reg  [31:0]  response_stall_cycles,
    output wire         protocol_error
);
  localparam integer BANKS = {_BANKS};
  localparam integer LANES = {_MACROS_PER_BANK};
  localparam integer STATE_BITS = {_STATE_BITS};
  localparam integer PHYSICAL_BITS = {_PHYSICAL_BITS};

  wire [PHYSICAL_BITS-1:0] padded_wdata = {{22'd0, req_wdata}};
  wire [BANKS*PHYSICAL_BITS-1:0] bank_read_words;
  reg [2:0] read_bank_q;
  reg read_pending_q;
  reg read_valid_q;
  reg protocol_error_q;
  reg req_blocked_q;
  reg req_blocked_write_q;
  reg [8:0] req_blocked_addr_q;
  reg [STATE_BITS-1:0] req_blocked_wdata_q;
  reg response_blocked_q;
  reg [STATE_BITS-1:0] response_blocked_data_q;

  wire req_fire = req_valid && req_ready;
  wire read_fire = req_fire && !req_write;
  wire [PHYSICAL_BITS-1:0] selected_read_word =
      bank_read_words[(read_bank_q * PHYSICAL_BITS) +: PHYSICAL_BITS];

  assign req_ready = !read_pending_q && !read_valid_q;
  assign read_valid = read_valid_q;
  assign read_data = selected_read_word[STATE_BITS-1:0];
  assign protocol_error = protocol_error_q;

  genvar bank_i;
  genvar lane_i;
  generate
    for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin : gen_bank
      for (lane_i = 0; lane_i < LANES; lane_i = lane_i + 1) begin : gen_lane
        fakeram45_64x32 u_state_mem (
            .rd_out(bank_read_words[
                (bank_i * PHYSICAL_BITS) + (lane_i * 32) +: 32]),
            .addr_in(req_addr[5:0]),
            .we_in(req_write),
            .wd_in(padded_wdata[(lane_i * 32) +: 32]),
            .w_mask_in(32'hffffffff),
            .clk(clk),
            .ce_in(req_fire && (req_addr[8:6] == bank_i[2:0]))
        );
      end
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      read_bank_q <= 3'd0;
      read_pending_q <= 1'b0;
      read_valid_q <= 1'b0;
      protocol_error_q <= 1'b0;
      req_blocked_q <= 1'b0;
      req_blocked_write_q <= 1'b0;
      req_blocked_addr_q <= 9'd0;
      req_blocked_wdata_q <= {{STATE_BITS{{1'b0}}}};
      response_blocked_q <= 1'b0;
      response_blocked_data_q <= {{STATE_BITS{{1'b0}}}};
      request_count <= 32'd0;
      read_request_count <= 32'd0;
      read_response_count <= 32'd0;
      write_count <= 32'd0;
      request_stall_cycles <= 32'd0;
      response_stall_cycles <= 32'd0;
    end else begin
      if (req_fire) begin
        request_count <= request_count + 32'd1;
        if (req_write)
          write_count <= write_count + 32'd1;
        else begin
          read_request_count <= read_request_count + 32'd1;
          read_bank_q <= req_addr[8:6];
          read_pending_q <= 1'b1;
        end
      end
      if (read_pending_q) begin
        read_pending_q <= 1'b0;
        read_valid_q <= 1'b1;
      end
      if (read_valid_q && read_ready) begin
        read_valid_q <= 1'b0;
        read_response_count <= read_response_count + 32'd1;
      end

      if (req_valid && !req_ready) begin
        request_stall_cycles <= request_stall_cycles + 32'd1;
        if (req_blocked_q
            && (req_write != req_blocked_write_q
                || req_addr != req_blocked_addr_q
                || req_wdata != req_blocked_wdata_q))
          protocol_error_q <= 1'b1;
        req_blocked_q <= 1'b1;
        req_blocked_write_q <= req_write;
        req_blocked_addr_q <= req_addr;
        req_blocked_wdata_q <= req_wdata;
      end else begin
        req_blocked_q <= 1'b0;
      end
      if (read_valid_q && !read_ready) begin
        response_stall_cycles <= response_stall_cycles + 32'd1;
        if (response_blocked_q && read_data != response_blocked_data_q)
          protocol_error_q <= 1'b1;
        response_blocked_q <= 1'b1;
        response_blocked_data_q <= read_data;
      end else begin
        response_blocked_q <= 1'b0;
      end
    end
  end
endmodule
"""


def _lowest_pending_function() -> str:
    return """  function automatic [HEAD_ID_BITS-1:0] lowest_pending_head;
    input [HEADS-1:0] pending;
    integer scan;
    begin
      lowest_pending_head = {HEAD_ID_BITS{1'b0}};
      for (scan = HEADS - 1; scan >= 0; scan = scan - 1)
        if (pending[scan]) lowest_pending_head = scan[HEAD_ID_BITS-1:0];
    end
  endfunction"""


def _top(
    *,
    top_name: str,
    merge_top: str,
    memory_top: str,
    fifo_depth: int,
) -> str:
    fifo_ptr_bits = _clog2(fifo_depth)
    return f"""module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         in_valid,
    output wire         in_ready,
    input  wire [15:0]  in_sequence_id,
    input  wire [4:0]   in_head_id,
    input  wire [13:0]  in_window_index,
    input  wire [14:0]  in_window_count,
    input  wire [15:0]  in_command_id,
    input  wire signed [31:0] in_global_max,
    input  wire [32:0]  in_exp_sum,
    input  wire [3:0]   in_slice,
    input  wire         in_last,
    input  wire [327:0] in_value,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_sequence_id,
    output wire [4:0]   out_head_id,
    output wire [14:0]  out_window_count,
    output wire [15:0]  out_command_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [3:0]   out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  input_accepted_count,
    output wire [31:0]  merge_completed_count,
    output wire [31:0]  emitted_beat_count,
    output wire [31:0]  completed_head_count,
    output wire [31:0]  fifo_full_stall_cycles,
    output wire [31:0]  output_stall_cycles,
    output wire [{fifo_ptr_bits}:0] fifo_level,
    output wire [31:0]  state_memory_request_count,
    output wire [31:0]  state_memory_read_request_count,
    output wire [31:0]  state_memory_read_response_count,
    output wire [31:0]  state_memory_write_count,
    output wire [31:0]  state_memory_request_stall_cycles,
    output wire [31:0]  state_memory_response_stall_cycles,
    output wire         state_memory_protocol_error,
    output wire         protocol_error
);
  localparam integer HEADS = 32;
  localparam integer HEAD_ID_BITS = 5;
  localparam integer FIFO_DEPTH = {fifo_depth};
  localparam integer FIFO_PTR_BITS = {fifo_ptr_bits};
  localparam [3:0] LAST_SLICE = 4'd15;
  localparam [14:0] MAX_WINDOW_COUNT = 15'd16384;
  localparam [3:0] S_IDLE = 4'd0;
  localparam [3:0] S_STATE_READ_WAIT = 4'd1;
  localparam [3:0] S_MERGE_LAUNCH = 4'd2;
  localparam [3:0] S_MERGE_WRITE = 4'd3;
  localparam [3:0] S_EMIT_REQUEST = 4'd4;
  localparam [3:0] S_EMIT_READ_WAIT = 4'd5;
  localparam [3:0] S_EMIT_OUTPUT = 4'd6;

  reg [15:0] fifo_sequence_q [0:FIFO_DEPTH-1];
  reg [4:0] fifo_head_q [0:FIFO_DEPTH-1];
  reg [13:0] fifo_window_index_q [0:FIFO_DEPTH-1];
  reg [14:0] fifo_window_count_q [0:FIFO_DEPTH-1];
  reg [15:0] fifo_command_q [0:FIFO_DEPTH-1];
  reg signed [31:0] fifo_max_q [0:FIFO_DEPTH-1];
  reg [32:0] fifo_sum_q [0:FIFO_DEPTH-1];
  reg [3:0] fifo_slice_q [0:FIFO_DEPTH-1];
  reg fifo_last_q [0:FIFO_DEPTH-1];
  reg [327:0] fifo_value_q [0:FIFO_DEPTH-1];
  reg [FIFO_PTR_BITS-1:0] fifo_rd_q;
  reg [FIFO_PTR_BITS-1:0] fifo_wr_q;
  reg [FIFO_PTR_BITS:0] fifo_count_q;

  reg [HEADS-1:0] head_active_q;
  reg [15:0] head_sequence_q [0:HEADS-1];
  reg [15:0] head_command_q [0:HEADS-1];
  reg [14:0] head_window_count_q [0:HEADS-1];
  reg [14:0] head_next_window_q [0:HEADS-1];
  reg [3:0] head_expected_slice_q [0:HEADS-1];
  reg [HEADS-1:0] emit_pending_q;

  reg [3:0] state_q;
  reg [15:0] work_sequence_q;
  reg [4:0] work_head_q;
  reg [14:0] work_window_index_q;
  reg [14:0] work_window_count_q;
  reg [15:0] work_command_q;
  reg signed [31:0] work_max_q;
  reg [32:0] work_sum_q;
  reg [3:0] work_slice_q;
  reg work_last_q;
  reg [327:0] work_value_q;
  reg signed [31:0] old_max_q;
  reg [32:0] old_sum_q;
  reg [327:0] old_value_q;
  reg [4:0] emit_head_q;
  reg [3:0] emit_slice_q;
  reg signed [31:0] emit_max_q;
  reg [32:0] emit_sum_q;
  reg [327:0] emit_value_q;

  reg [31:0] cycle_count_q;
  reg [31:0] input_accepted_count_q;
  reg [31:0] emitted_beat_count_q;
  reg [31:0] completed_head_count_q;
  reg [31:0] fifo_full_stall_cycles_q;
  reg [31:0] output_stall_cycles_q;
  reg protocol_error_q;
  integer reset_i;

  wire fifo_empty_w = fifo_count_q == 0;
  wire fifo_full_w = fifo_count_q == FIFO_DEPTH;
  wire push_w = in_valid && in_ready;
  wire [15:0] front_sequence_w = fifo_sequence_q[fifo_rd_q];
  wire [4:0] front_head_w = fifo_head_q[fifo_rd_q];
  wire [13:0] front_window_index_w = fifo_window_index_q[fifo_rd_q];
  wire [14:0] front_window_count_w = fifo_window_count_q[fifo_rd_q];
  wire [15:0] front_command_w = fifo_command_q[fifo_rd_q];
  wire signed [31:0] front_max_w = fifo_max_q[fifo_rd_q];
  wire [32:0] front_sum_w = fifo_sum_q[fifo_rd_q];
  wire [3:0] front_slice_w = fifo_slice_q[fifo_rd_q];
  wire front_last_w = fifo_last_q[fifo_rd_q];
  wire [327:0] front_value_w = fifo_value_q[fifo_rd_q];
  wire front_first_head_w = !head_active_q[front_head_w];
  wire front_needs_merge_w =
      head_active_q[front_head_w] && front_window_index_w != 0;
  wire front_error_w =
      !fifo_empty_w
      && ((front_last_w != (front_slice_w == LAST_SLICE))
          || front_window_count_w == 0
          || front_window_count_w > MAX_WINDOW_COUNT
          || (front_first_head_w
              && (front_window_index_w != 0 || front_slice_w != 0))
          || (!front_first_head_w
              && (front_sequence_w != head_sequence_q[front_head_w]
                  || front_command_w != head_command_q[front_head_w]
                  || front_window_count_w != head_window_count_q[front_head_w]
                  || {{1'b0, front_window_index_w}}
                     != head_next_window_q[front_head_w]
                  || front_slice_w != head_expected_slice_q[front_head_w])));

  wire memory_req_ready_w;
  reg memory_req_valid_r;
  reg memory_req_write_r;
  reg [8:0] memory_req_addr_r;
  reg [393:0] memory_req_wdata_r;
  wire memory_read_valid_w;
  reg memory_read_ready_r;
  wire [393:0] memory_read_data_w;
  wire memory_read_state_valid_w = memory_read_data_w[393];
  wire signed [31:0] memory_read_max_w = memory_read_data_w[392:361];
  wire [32:0] memory_read_sum_w = memory_read_data_w[360:328];
  wire [327:0] memory_read_value_w = memory_read_data_w[327:0];

  wire merge_left_ready_w;
  wire merge_right_ready_w;
  wire merge_out_valid_w;
  wire signed [31:0] merge_out_max_w;
  wire [32:0] merge_out_sum_w;
  wire [3:0] merge_out_slice_w;
  wire merge_out_last_w;
  wire [327:0] merge_out_value_w;
  wire [31:0] merge_completed_count_w;
  wire merge_protocol_error_w;
  wire merge_input_valid_w =
      state_q == S_MERGE_LAUNCH && !protocol_error_q;
  wire merge_launch_fire_w =
      merge_input_valid_w && merge_left_ready_w && merge_right_ready_w;
  wire merge_write_fire_w =
      state_q == S_MERGE_WRITE && merge_out_valid_w
      && memory_req_valid_r && memory_req_ready_w;
  wire direct_write_fire_w =
      state_q == S_IDLE && !fifo_empty_w && !front_error_w
      && !front_needs_merge_w && memory_req_valid_r && memory_req_ready_w;
  wire state_read_fire_w =
      state_q == S_IDLE && !fifo_empty_w && !front_error_w
      && front_needs_merge_w && memory_req_valid_r && memory_req_ready_w;
  wire emit_read_fire_w =
      state_q == S_EMIT_REQUEST && memory_req_valid_r && memory_req_ready_w;
  wire pop_w = direct_write_fire_w || state_read_fire_w;
  wire emit_fire_w = out_valid && out_ready;
  wire [4:0] next_emit_head_w = lowest_pending_head(emit_pending_q);

  assign in_ready = !fifo_full_w && !protocol_error;
  assign out_valid = state_q == S_EMIT_OUTPUT && !protocol_error;
  assign out_sequence_id = head_sequence_q[emit_head_q];
  assign out_head_id = emit_head_q;
  assign out_window_count = head_window_count_q[emit_head_q];
  assign out_command_id = head_command_q[emit_head_q];
  assign out_global_max = emit_max_q;
  assign out_exp_sum = emit_sum_q;
  assign out_slice = emit_slice_q;
  assign out_last = emit_slice_q == LAST_SLICE;
  assign out_value = emit_value_q;
  assign cycle_count = cycle_count_q;
  assign input_accepted_count = input_accepted_count_q;
  assign merge_completed_count = merge_completed_count_w;
  assign emitted_beat_count = emitted_beat_count_q;
  assign completed_head_count = completed_head_count_q;
  assign fifo_full_stall_cycles = fifo_full_stall_cycles_q;
  assign output_stall_cycles = output_stall_cycles_q;
  assign fifo_level = fifo_count_q;
  assign protocol_error =
      protocol_error_q || merge_protocol_error_w || state_memory_protocol_error;

{_lowest_pending_function()}

  always @* begin
    memory_req_valid_r = 1'b0;
    memory_req_write_r = 1'b0;
    memory_req_addr_r = 9'd0;
    memory_req_wdata_r = 394'd0;
    memory_read_ready_r = 1'b0;
    if (state_q == S_IDLE && !fifo_empty_w && !front_error_w
        && emit_pending_q == 0) begin
      memory_req_valid_r = 1'b1;
      memory_req_write_r = !front_needs_merge_w;
      memory_req_addr_r = {{front_head_w, front_slice_w}};
      memory_req_wdata_r =
          {{1'b1, front_max_w, front_sum_w, front_value_w}};
    end else if (state_q == S_STATE_READ_WAIT) begin
      memory_read_ready_r = 1'b1;
    end else if (state_q == S_MERGE_WRITE && merge_out_valid_w) begin
      memory_req_valid_r = 1'b1;
      memory_req_write_r = 1'b1;
      memory_req_addr_r = {{work_head_q, work_slice_q}};
      memory_req_wdata_r =
          {{1'b1, merge_out_max_w, merge_out_sum_w, merge_out_value_w}};
    end else if (state_q == S_EMIT_REQUEST) begin
      memory_req_valid_r = 1'b1;
      memory_req_write_r = 1'b0;
      memory_req_addr_r = {{emit_head_q, emit_slice_q}};
    end else if (state_q == S_EMIT_READ_WAIT) begin
      memory_read_ready_r = 1'b1;
    end
  end

  {memory_top} u_state_memory (
      .clk(clk),
      .rst_n(rst_n),
      .req_valid(memory_req_valid_r),
      .req_ready(memory_req_ready_w),
      .req_write(memory_req_write_r),
      .req_addr(memory_req_addr_r),
      .req_wdata(memory_req_wdata_r),
      .read_valid(memory_read_valid_w),
      .read_ready(memory_read_ready_r),
      .read_data(memory_read_data_w),
      .request_count(state_memory_request_count),
      .read_request_count(state_memory_read_request_count),
      .read_response_count(state_memory_read_response_count),
      .write_count(state_memory_write_count),
      .request_stall_cycles(state_memory_request_stall_cycles),
      .response_stall_cycles(state_memory_response_stall_cycles),
      .protocol_error(state_memory_protocol_error)
  );

  {merge_top} u_pair_merge (
      .clk(clk),
      .rst_n(rst_n),
      .left_valid(merge_input_valid_w),
      .left_ready(merge_left_ready_w),
      .left_command_id(work_command_q),
      .left_head_id(work_head_q),
      .left_global_max(work_max_q),
      .left_exp_sum(work_sum_q),
      .left_slice(work_slice_q),
      .left_last(work_last_q),
      .left_value(work_value_q),
      .right_valid(merge_input_valid_w),
      .right_ready(merge_right_ready_w),
      .right_command_id(work_command_q),
      .right_head_id(work_head_q),
      .right_global_max(old_max_q),
      .right_exp_sum(old_sum_q),
      .right_slice(work_slice_q),
      .right_last(work_last_q),
      .right_value(old_value_q),
      .out_valid(merge_out_valid_w),
      .out_ready(memory_req_ready_w && state_q == S_MERGE_WRITE),
      .out_command_id(),
      .out_head_id(),
      .out_global_max(merge_out_max_w),
      .out_exp_sum(merge_out_sum_w),
      .out_slice(merge_out_slice_w),
      .out_last(merge_out_last_w),
      .out_value(merge_out_value_w),
      .completed_count(merge_completed_count_w),
      .cycle_count(),
      .protocol_error(merge_protocol_error_w)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fifo_rd_q <= 0;
      fifo_wr_q <= 0;
      fifo_count_q <= 0;
      head_active_q <= 0;
      emit_pending_q <= 0;
      state_q <= S_IDLE;
      work_sequence_q <= 0;
      work_head_q <= 0;
      work_window_index_q <= 0;
      work_window_count_q <= 0;
      work_command_q <= 0;
      work_max_q <= 0;
      work_sum_q <= 0;
      work_slice_q <= 0;
      work_last_q <= 0;
      work_value_q <= 0;
      old_max_q <= 0;
      old_sum_q <= 0;
      old_value_q <= 0;
      emit_head_q <= 0;
      emit_slice_q <= 0;
      emit_max_q <= 0;
      emit_sum_q <= 0;
      emit_value_q <= 0;
      cycle_count_q <= 0;
      input_accepted_count_q <= 0;
      emitted_beat_count_q <= 0;
      completed_head_count_q <= 0;
      fifo_full_stall_cycles_q <= 0;
      output_stall_cycles_q <= 0;
      protocol_error_q <= 0;
      for (reset_i = 0; reset_i < HEADS; reset_i = reset_i + 1) begin
        head_sequence_q[reset_i] <= 0;
        head_command_q[reset_i] <= 0;
        head_window_count_q[reset_i] <= 0;
        head_next_window_q[reset_i] <= 0;
        head_expected_slice_q[reset_i] <= 0;
      end
    end else begin
      cycle_count_q <= cycle_count_q + 1;
      if (in_valid && !in_ready)
        fifo_full_stall_cycles_q <= fifo_full_stall_cycles_q + 1;
      if (out_valid && !out_ready)
        output_stall_cycles_q <= output_stall_cycles_q + 1;
      if (merge_protocol_error_w || state_memory_protocol_error)
        protocol_error_q <= 1'b1;
      if (state_q == S_IDLE && !fifo_empty_w && front_error_w)
        protocol_error_q <= 1'b1;

      if (push_w) begin
        fifo_sequence_q[fifo_wr_q] <= in_sequence_id;
        fifo_head_q[fifo_wr_q] <= in_head_id;
        fifo_window_index_q[fifo_wr_q] <= in_window_index;
        fifo_window_count_q[fifo_wr_q] <= in_window_count;
        fifo_command_q[fifo_wr_q] <= in_command_id;
        fifo_max_q[fifo_wr_q] <= in_global_max;
        fifo_sum_q[fifo_wr_q] <= in_exp_sum;
        fifo_slice_q[fifo_wr_q] <= in_slice;
        fifo_last_q[fifo_wr_q] <= in_last;
        fifo_value_q[fifo_wr_q] <= in_value;
        fifo_wr_q <= fifo_wr_q + 1'b1;
        input_accepted_count_q <= input_accepted_count_q + 1;
      end
      if (pop_w) fifo_rd_q <= fifo_rd_q + 1'b1;
      case ({{push_w, pop_w}})
        2'b10: fifo_count_q <= fifo_count_q + 1'b1;
        2'b01: fifo_count_q <= fifo_count_q - 1'b1;
        default: fifo_count_q <= fifo_count_q;
      endcase

      if (direct_write_fire_w) begin
        if (front_first_head_w) begin
          head_active_q[front_head_w] <= 1'b1;
          head_sequence_q[front_head_w] <= front_sequence_w;
          head_command_q[front_head_w] <= front_command_w;
          head_window_count_q[front_head_w] <= front_window_count_w;
        end
        if (front_last_w) begin
          head_expected_slice_q[front_head_w] <= 0;
          head_next_window_q[front_head_w] <=
              {{1'b0, front_window_index_w}} + 1;
          if ({{1'b0, front_window_index_w}} == front_window_count_w - 1)
            emit_pending_q[front_head_w] <= 1'b1;
        end else begin
          head_expected_slice_q[front_head_w] <= front_slice_w + 1'b1;
        end
      end

      case (state_q)
        S_IDLE: begin
          if (emit_pending_q != 0) begin
            emit_head_q <= next_emit_head_w;
            emit_slice_q <= 0;
            emit_pending_q[next_emit_head_w] <= 1'b0;
            state_q <= S_EMIT_REQUEST;
          end else if (state_read_fire_w) begin
            work_sequence_q <= front_sequence_w;
            work_head_q <= front_head_w;
            work_window_index_q <= {{1'b0, front_window_index_w}};
            work_window_count_q <= front_window_count_w;
            work_command_q <= front_command_w;
            work_max_q <= front_max_w;
            work_sum_q <= front_sum_w;
            work_slice_q <= front_slice_w;
            work_last_q <= front_last_w;
            work_value_q <= front_value_w;
            state_q <= S_STATE_READ_WAIT;
          end
        end
        S_STATE_READ_WAIT: begin
          if (memory_read_valid_w && memory_read_ready_r) begin
            if (!memory_read_state_valid_w) begin
              protocol_error_q <= 1'b1;
              state_q <= S_IDLE;
            end else begin
              old_max_q <= memory_read_max_w;
              old_sum_q <= memory_read_sum_w;
              old_value_q <= memory_read_value_w;
              state_q <= S_MERGE_LAUNCH;
            end
          end
        end
        S_MERGE_LAUNCH: begin
          if (merge_launch_fire_w) state_q <= S_MERGE_WRITE;
        end
        S_MERGE_WRITE: begin
          if (merge_write_fire_w) begin
            if (merge_out_last_w) begin
              head_expected_slice_q[work_head_q] <= 0;
              head_next_window_q[work_head_q] <= work_window_index_q + 1;
              if (work_window_index_q == work_window_count_q - 1)
                emit_pending_q[work_head_q] <= 1'b1;
            end else begin
              head_expected_slice_q[work_head_q] <= work_slice_q + 1'b1;
            end
            state_q <= S_IDLE;
          end
        end
        S_EMIT_REQUEST: begin
          if (emit_read_fire_w) state_q <= S_EMIT_READ_WAIT;
        end
        S_EMIT_READ_WAIT: begin
          if (memory_read_valid_w && memory_read_ready_r) begin
            if (!memory_read_state_valid_w) begin
              protocol_error_q <= 1'b1;
              state_q <= S_IDLE;
            end else begin
              emit_max_q <= memory_read_max_w;
              emit_sum_q <= memory_read_sum_w;
              emit_value_q <= memory_read_value_w;
              state_q <= S_EMIT_OUTPUT;
            end
          end
        end
        S_EMIT_OUTPUT: begin
          if (emit_fire_w) begin
            emitted_beat_count_q <= emitted_beat_count_q + 1;
            if (emit_slice_q == LAST_SLICE) begin
              completed_head_count_q <= completed_head_count_q + 1;
              head_active_q[emit_head_q] <= 1'b0;
              head_next_window_q[emit_head_q] <= 0;
              head_expected_slice_q[emit_head_q] <= 0;
              state_q <= S_IDLE;
            end else begin
              emit_slice_q <= emit_slice_q + 1'b1;
              state_q <= S_EMIT_REQUEST;
            end
          end
        end
        default: state_q <= S_IDLE;
      endcase
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    merge_top = f"{top_name}__pair_merge"
    memory_top = f"{top_name}__state_memory_proxy"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="exact-partial-temporal-sram-") as name:
        merge_dir = Path(name) / "merge"
        generate_merge(
            {
                "top_name": merge_top,
                "attention_score32_online_state_merge": {
                    "value_slices": VALUE_SLICES,
                    "head_id_bits": HEAD_ID_BITS,
                    "exp_scale_impl": str(params["exp_scale_impl"]),
                    "keep_hierarchy": bool(params["keep_hierarchy"]),
                },
            },
            merge_dir,
        )
        merge_rtl = (merge_dir / "top.v").read_text(encoding="utf-8")
        merge_manifest = json.loads(
            (merge_dir / "attention_score32_online_state_merge_manifest.json").read_text(
                encoding="utf-8"
            )
        )
    proxy_rtl = _memory_proxy(memory_top)
    top_rtl = _top(
        top_name=top_name,
        merge_top=merge_top,
        memory_top=memory_top,
        fifo_depth=int(params["fifo_depth"]),
    )
    top_text = "\n\n".join((merge_rtl, proxy_rtl, top_rtl)) + "\n"
    (out_dir / "top.v").write_text(top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": 1,
        "top_name": top_name,
        "generator": _GENERATOR,
        "semantic_profile": "score32_exact_partial_temporal_stream_sram_v1",
        "stream_interface_compatible_with": (
            "gen_attention_score32_exact_partial_temporal_stream"
        ),
        "persistent_state_backend": "fakeram45_64x32_banked_8x13",
        "logical_state": {
            "entries": _STATE_ENTRIES,
            "bits_per_entry": _STATE_BITS,
            "packing": ["valid[1]", "global_max[32]", "exp_sum[33]", "value[328]"],
        },
        "physical_state": {
            "banks": _BANKS,
            "bank_select": "address[8:6]",
            "rows_per_bank": 64,
            "macros_per_bank": _MACROS_PER_BANK,
            "physical_bits_per_entry": _PHYSICAL_BITS,
            "pad_bits": 22,
            "macro_count": _MACRO_COUNT,
        },
        "access_schedule": {
            "macro_read_response_latency_cycles": 1,
            "first_window_slice": "direct_write",
            "later_window_slice": "synchronous_read_then_exact_pair_merge_then_write",
            "emission": "synchronous_read_then_ready_valid_output",
            "single_1rw_request_inflight": True,
        },
        "sequencing_metadata_storage": "per_head_registers",
        "persistent_state_inferred_as_flops": False,
        "fifo_depth": int(params["fifo_depth"]),
        "submodule_manifests": {"pair_merge": merge_manifest},
        "remaining_abstractions": [
            "upstream_service_and_clock_domain_crossing",
            "downstream_full_context_final_normalizer",
            "macro_library_timing_and_physical_ppa",
        ],
        "dependency_sources": [
            {"path": _GENERATOR, "sha256": _sha256_file(Path(__file__))},
            {
                "path": "npu/rtlgen/gen_attention_score32_online_state_merge.py",
                "sha256": _sha256_file(
                    REPO_ROOT / "npu/rtlgen/gen_attention_score32_online_state_merge.py"
                ),
            },
        ],
        "generated_top_sha256": _sha256_text(top_text),
    }
    (out_dir / _MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    macro_manifest = {
        "version": "0.1",
        "design_id": top_name,
        "module": top_name,
        "platform": "nangate45",
        "flow_variant": "exact_partial_temporal_state_sram_v1",
        "blackboxes": ["fakeram45_64x32"],
        "additional_lefs": [
            "/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef"
        ],
        "additional_libs": [
            "/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib"
        ],
        "additional_gds": [],
        "blackbox_verilog": ["npu/rtl/fakeram45_64x32_blackbox.v"],
        "source": {
            "mode": "generated_exact_partial_temporal_state_sram",
            "generator": _GENERATOR,
        },
        "manifest_params": {
            "macro_count": _MACRO_COUNT,
            "state_entries": _STATE_ENTRIES,
            "logical_state_bits": _STATE_BITS,
            "physical_state_bits": _PHYSICAL_BITS,
            "pad_bits": 22,
            "bank_count": _BANKS,
            "macros_per_bank": _MACROS_PER_BANK,
        },
    }
    (out_dir / "macro_manifest.json").write_text(
        json.dumps(macro_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
