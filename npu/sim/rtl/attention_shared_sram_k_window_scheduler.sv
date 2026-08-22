`timescale 1ns/1ps

// Prefetches eight 16-dimension Llama7B K groups from 17 interleaved shared
// SRAM banks into two concrete 16 KiB windows.  A ready window exposes all
// 128 eight-token K beats for one head dimension in a single compute cycle.
module attention_shared_sram_k_window_scheduler #(
  parameter integer ADDR_W = 16,
  parameter integer BANKS = 17,
  parameter integer WORDS_PER_GROUP = 128,
  parameter integer DIM_GROUPS = 8,
  parameter integer DIMS_PER_GROUP = 16
) (
  input wire clk,
  input wire rst_n,

  input wire command_valid,
  output wire command_ready,
  input wire [ADDR_W-1:0] command_base_word_addr,

  output reg [BANKS-1:0] bank_req_valid,
  input wire [BANKS-1:0] bank_req_ready,
  output reg [(BANKS*ADDR_W)-1:0] bank_req_word_addr,
  output reg [BANKS-1:0] bank_req_buffer,
  output reg [(BANKS*((DIM_GROUPS <= 1) ? 1 : $clog2(DIM_GROUPS)))-1:0] bank_req_group,
  output reg [(BANKS*((WORDS_PER_GROUP <= 1) ? 1 : $clog2(WORDS_PER_GROUP)))-1:0] bank_req_slot,

  input wire [BANKS-1:0] bank_rsp_valid,
  output wire [BANKS-1:0] bank_rsp_ready,
  input wire [(BANKS*1024)-1:0] bank_rsp_data,
  input wire [BANKS-1:0] bank_rsp_buffer,
  input wire [(BANKS*((DIM_GROUPS <= 1) ? 1 : $clog2(DIM_GROUPS)))-1:0] bank_rsp_group,
  input wire [(BANKS*((WORDS_PER_GROUP <= 1) ? 1 : $clog2(WORDS_PER_GROUP)))-1:0] bank_rsp_slot,

  output wire compute_valid,
  input wire compute_ready,
  output wire [((DIM_GROUPS <= 1) ? 1 : $clog2(DIM_GROUPS))-1:0] compute_group,
  output wire [((DIMS_PER_GROUP <= 1) ? 1 : $clog2(DIMS_PER_GROUP))-1:0] compute_dimension,
  output wire compute_last,
  output wire [(WORDS_PER_GROUP*64)-1:0] compute_k_beats,

  output reg done,
  output reg protocol_error,
  output reg [63:0] bank_request_count,
  output reg [63:0] bank_response_count,
  output reg [63:0] compute_beat_count,
  output reg [63:0] bank_request_stall_count,
  output reg [63:0] bank_response_stall_count,
  output reg [63:0] compute_output_stall_count,
  output reg [63:0] compute_wait_for_window_count
);
  localparam integer GROUP_W = (DIM_GROUPS <= 1) ? 1 : $clog2(DIM_GROUPS);
  localparam integer SLOT_W = (WORDS_PER_GROUP <= 1) ? 1 : $clog2(WORDS_PER_GROUP);
  localparam integer DIM_W = (DIMS_PER_GROUP <= 1) ? 1 : $clog2(DIMS_PER_GROUP);
  localparam integer ISSUE_ROUNDS = (WORDS_PER_GROUP + BANKS - 1) / BANKS;
  localparam integer ROUND_W = (ISSUE_ROUNDS <= 1) ? 1 : $clog2(ISSUE_ROUNDS);
  localparam integer RESPONSE_COUNT_W = $clog2(WORDS_PER_GROUP + 1);

  localparam [1:0] BUF_EMPTY = 2'd0;
  localparam [1:0] BUF_FILL = 2'd1;
  localparam [1:0] BUF_READY = 2'd2;
  localparam [1:0] BUF_COMPUTE = 2'd3;

  reg busy_q;
  reg [ADDR_W-1:0] base_word_addr_q;
  reg [1:0] buffer_state [0:1];
  reg [GROUP_W-1:0] buffer_group [0:1];
  reg [1023:0] buffer_mem [0:(2*WORDS_PER_GROUP)-1];

  reg fill_active_q;
  reg fill_buffer_q;
  reg [GROUP_W-1:0] fill_group_q;
  reg [ROUND_W-1:0] issue_round_q;
  reg issuing_q;
  reg [BANKS-1:0] issue_done_mask_q;
  reg [WORDS_PER_GROUP-1:0] issued_bitmap_q;
  reg [WORDS_PER_GROUP-1:0] received_bitmap_q;
  reg [RESPONSE_COUNT_W-1:0] response_count_q;
  reg [GROUP_W:0] next_prefetch_group_q;

  reg compute_active_q;
  reg compute_buffer_q;
  reg [GROUP_W-1:0] expected_compute_group_q;
  reg [DIM_W-1:0] compute_dimension_q;

  reg [BANKS-1:0] round_valid_mask;
  reg response_batch_error;
  reg [RESPONSE_COUNT_W-1:0] response_fire_count;
  reg [SLOT_W-1:0] response_slot;
  reg [GROUP_W-1:0] response_group;
  reg [ADDR_W-1:0] response_global_word;
  reg ready_buffer_found;
  reg ready_buffer_select;
  integer req_lane_i;
  integer rsp_bank_i;
  integer rsp_other_i;
  integer stall_bank_i;
  integer seq_bank_i;
  integer word_offset_i;
  integer target_bank_i;
  integer reset_i;
  reg [63:0] request_stall_increment;
  reg [63:0] response_stall_increment;

  wire command_fire = command_valid && command_ready;
  assign command_ready = !busy_q && !protocol_error;

  function [ADDR_W-1:0] window_word_addr;
    input [GROUP_W-1:0] group_index;
    input [SLOT_W-1:0] word_slot;
    begin
      window_word_addr = base_word_addr_q +
        ADDR_W'(word_slot * DIM_GROUPS) + ADDR_W'(group_index);
    end
  endfunction

  always @* begin
    bank_req_valid = {BANKS{1'b0}};
    bank_req_word_addr = {(BANKS*ADDR_W){1'b0}};
    bank_req_buffer = {BANKS{1'b0}};
    bank_req_group = {(BANKS*GROUP_W){1'b0}};
    bank_req_slot = {(BANKS*SLOT_W){1'b0}};
    round_valid_mask = {BANKS{1'b0}};
    word_offset_i = 0;
    target_bank_i = 0;
    if (fill_active_q && issuing_q && !protocol_error) begin
      for (req_lane_i = 0; req_lane_i < BANKS; req_lane_i = req_lane_i + 1) begin
        word_offset_i = (issue_round_q * BANKS) + req_lane_i;
        if (word_offset_i < WORDS_PER_GROUP) begin
          target_bank_i = 32'(window_word_addr(
            fill_group_q, SLOT_W'(word_offset_i)
          )) % BANKS;
          round_valid_mask[target_bank_i] = 1'b1;
          if (!issue_done_mask_q[target_bank_i]) begin
            bank_req_valid[target_bank_i] = 1'b1;
            bank_req_word_addr[target_bank_i*ADDR_W +: ADDR_W] =
              window_word_addr(fill_group_q, SLOT_W'(word_offset_i));
            bank_req_buffer[target_bank_i] = fill_buffer_q;
            bank_req_group[target_bank_i*GROUP_W +: GROUP_W] = fill_group_q;
            bank_req_slot[target_bank_i*SLOT_W +: SLOT_W] = SLOT_W'(word_offset_i);
          end
        end
      end
    end
  end
  wire [BANKS-1:0] request_fire_mask = bank_req_valid & bank_req_ready;

  assign bank_rsp_ready = {BANKS{busy_q && !protocol_error}};

  // Validate the whole response batch before any window write.  Responses
  // must carry a previously issued slot and the bank implied by interleaving.
  always @* begin
    response_batch_error = 1'b0;
    response_fire_count = {RESPONSE_COUNT_W{1'b0}};
    response_slot = {SLOT_W{1'b0}};
    response_group = {GROUP_W{1'b0}};
    response_global_word = {ADDR_W{1'b0}};
    for (rsp_bank_i = 0; rsp_bank_i < BANKS; rsp_bank_i = rsp_bank_i + 1) begin
      if (bank_rsp_valid[rsp_bank_i] && bank_rsp_ready[rsp_bank_i]) begin
        response_fire_count = response_fire_count + 1'b1;
        response_slot = bank_rsp_slot[rsp_bank_i*SLOT_W +: SLOT_W];
        response_group = bank_rsp_group[rsp_bank_i*GROUP_W +: GROUP_W];
        response_global_word = window_word_addr(response_group, response_slot);
        if (!fill_active_q ||
            bank_rsp_buffer[rsp_bank_i] != fill_buffer_q ||
            response_group != fill_group_q ||
            !issued_bitmap_q[response_slot] ||
            received_bitmap_q[response_slot] ||
            ((32'(response_global_word) % BANKS) != rsp_bank_i))
          response_batch_error = 1'b1;
        for (rsp_other_i = rsp_bank_i + 1; rsp_other_i < BANKS;
             rsp_other_i = rsp_other_i + 1)
          if (bank_rsp_valid[rsp_other_i] && bank_rsp_ready[rsp_other_i] &&
              bank_rsp_buffer[rsp_other_i] == bank_rsp_buffer[rsp_bank_i] &&
              bank_rsp_group[rsp_other_i*GROUP_W +: GROUP_W] ==
                bank_rsp_group[rsp_bank_i*GROUP_W +: GROUP_W] &&
              bank_rsp_slot[rsp_other_i*SLOT_W +: SLOT_W] ==
                bank_rsp_slot[rsp_bank_i*SLOT_W +: SLOT_W])
            response_batch_error = 1'b1;
      end
    end
  end

  always @* begin
    ready_buffer_found = 1'b0;
    ready_buffer_select = 1'b0;
    if (buffer_state[0] == BUF_READY &&
        buffer_group[0] == expected_compute_group_q) begin
      ready_buffer_found = 1'b1;
      ready_buffer_select = 1'b0;
    end else if (buffer_state[1] == BUF_READY &&
                 buffer_group[1] == expected_compute_group_q) begin
      ready_buffer_found = 1'b1;
      ready_buffer_select = 1'b1;
    end
  end

  wire selected_compute_buffer = compute_active_q ? compute_buffer_q : ready_buffer_select;
  wire [DIM_W-1:0] selected_compute_dimension =
    compute_active_q ? compute_dimension_q : {DIM_W{1'b0}};
  assign compute_valid = busy_q && !protocol_error &&
    (compute_active_q || ready_buffer_found);
  assign compute_group = expected_compute_group_q;
  assign compute_dimension = selected_compute_dimension;
  assign compute_last = compute_valid &&
    (selected_compute_dimension == DIM_W'(DIMS_PER_GROUP - 1));
  wire compute_fire = compute_valid && compute_ready;

  always @* begin
    request_stall_increment = 64'd0;
    response_stall_increment = 64'd0;
    for (stall_bank_i = 0; stall_bank_i < BANKS; stall_bank_i = stall_bank_i + 1) begin
      if (bank_req_valid[stall_bank_i] && !bank_req_ready[stall_bank_i])
        request_stall_increment = request_stall_increment + 1'b1;
      if (bank_rsp_valid[stall_bank_i] && !bank_rsp_ready[stall_bank_i])
        response_stall_increment = response_stall_increment + 1'b1;
    end
  end

  genvar word_g;
  generate
    for (word_g = 0; word_g < WORDS_PER_GROUP; word_g = word_g + 1) begin : gen_compute_k
      assign compute_k_beats[word_g*64 +: 64] =
        buffer_mem[(selected_compute_buffer * WORDS_PER_GROUP) + word_g]
          [selected_compute_dimension*64 +: 64];
    end
  endgenerate

`ifndef SYNTHESIS
  initial begin
    if (BANKS != 17 || WORDS_PER_GROUP != 128 || DIM_GROUPS != 8 ||
        DIMS_PER_GROUP != 16) begin
      $error("attention_shared_sram_k_window_scheduler requires Llama7B 17/128/8/16 geometry");
      $finish(1);
    end
  end
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy_q <= 1'b0;
      base_word_addr_q <= {ADDR_W{1'b0}};
      buffer_state[0] <= BUF_EMPTY;
      buffer_state[1] <= BUF_EMPTY;
      buffer_group[0] <= {GROUP_W{1'b0}};
      buffer_group[1] <= {GROUP_W{1'b0}};
      fill_active_q <= 1'b0;
      fill_buffer_q <= 1'b0;
      fill_group_q <= {GROUP_W{1'b0}};
      issue_round_q <= {ROUND_W{1'b0}};
      issuing_q <= 1'b0;
      issue_done_mask_q <= {BANKS{1'b0}};
      issued_bitmap_q <= {WORDS_PER_GROUP{1'b0}};
      received_bitmap_q <= {WORDS_PER_GROUP{1'b0}};
      response_count_q <= {RESPONSE_COUNT_W{1'b0}};
      next_prefetch_group_q <= {(GROUP_W+1){1'b0}};
      compute_active_q <= 1'b0;
      compute_buffer_q <= 1'b0;
      expected_compute_group_q <= {GROUP_W{1'b0}};
      compute_dimension_q <= {DIM_W{1'b0}};
      done <= 1'b0;
      protocol_error <= 1'b0;
      bank_request_count <= 64'd0;
      bank_response_count <= 64'd0;
      compute_beat_count <= 64'd0;
      bank_request_stall_count <= 64'd0;
      bank_response_stall_count <= 64'd0;
      compute_output_stall_count <= 64'd0;
      compute_wait_for_window_count <= 64'd0;
      for (reset_i = 0; reset_i < 2*WORDS_PER_GROUP; reset_i = reset_i + 1)
        buffer_mem[reset_i] <= 1024'd0;
    end else begin
      done <= 1'b0;

      bank_request_stall_count <= bank_request_stall_count + request_stall_increment;
      bank_response_stall_count <= bank_response_stall_count + response_stall_increment;
      if (compute_valid && !compute_ready)
        compute_output_stall_count <= compute_output_stall_count + 1'b1;
      if (busy_q && !compute_active_q && !ready_buffer_found)
        compute_wait_for_window_count <= compute_wait_for_window_count + 1'b1;

      if (command_fire) begin
        busy_q <= 1'b1;
        base_word_addr_q <= command_base_word_addr;
        buffer_state[0] <= BUF_EMPTY;
        buffer_state[1] <= BUF_EMPTY;
        next_prefetch_group_q <= {(GROUP_W+1){1'b0}};
        expected_compute_group_q <= {GROUP_W{1'b0}};
        compute_active_q <= 1'b0;
      end

      // Start the next group whenever either concrete window is empty.
      if (busy_q && !fill_active_q &&
          next_prefetch_group_q < (GROUP_W+1)'(DIM_GROUPS)) begin
        if (buffer_state[0] == BUF_EMPTY || buffer_state[1] == BUF_EMPTY) begin
          fill_active_q <= 1'b1;
          fill_buffer_q <= (buffer_state[0] == BUF_EMPTY) ? 1'b0 : 1'b1;
          fill_group_q <= next_prefetch_group_q[GROUP_W-1:0];
          buffer_group[(buffer_state[0] == BUF_EMPTY) ? 0 : 1] <=
            next_prefetch_group_q[GROUP_W-1:0];
          buffer_state[(buffer_state[0] == BUF_EMPTY) ? 0 : 1] <= BUF_FILL;
          next_prefetch_group_q <= next_prefetch_group_q + 1'b1;
          issue_round_q <= {ROUND_W{1'b0}};
          issuing_q <= 1'b1;
          issue_done_mask_q <= {BANKS{1'b0}};
          issued_bitmap_q <= {WORDS_PER_GROUP{1'b0}};
          received_bitmap_q <= {WORDS_PER_GROUP{1'b0}};
          response_count_q <= {RESPONSE_COUNT_W{1'b0}};
        end
      end

      if (|request_fire_mask) begin
        bank_request_count <= bank_request_count + 64'($countones(request_fire_mask));
        for (seq_bank_i = 0; seq_bank_i < BANKS; seq_bank_i = seq_bank_i + 1)
          if (request_fire_mask[seq_bank_i])
            issued_bitmap_q[bank_req_slot[seq_bank_i*SLOT_W +: SLOT_W]] <= 1'b1;
        if (((issue_done_mask_q | request_fire_mask) & round_valid_mask) ==
            round_valid_mask) begin
          issue_done_mask_q <= {BANKS{1'b0}};
          if (issue_round_q == ROUND_W'(ISSUE_ROUNDS - 1))
            issuing_q <= 1'b0;
          else
            issue_round_q <= issue_round_q + 1'b1;
        end else begin
          issue_done_mask_q <= issue_done_mask_q | request_fire_mask;
        end
      end

      if (response_batch_error)
        protocol_error <= 1'b1;
      if ((|bank_rsp_valid) && !response_batch_error && busy_q && !protocol_error) begin
        bank_response_count <= bank_response_count + 64'(response_fire_count);
        for (seq_bank_i = 0; seq_bank_i < BANKS; seq_bank_i = seq_bank_i + 1) begin
          if (bank_rsp_valid[seq_bank_i] && bank_rsp_ready[seq_bank_i]) begin
            received_bitmap_q[bank_rsp_slot[seq_bank_i*SLOT_W +: SLOT_W]] <= 1'b1;
            buffer_mem[(fill_buffer_q * WORDS_PER_GROUP) +
              32'(bank_rsp_slot[seq_bank_i*SLOT_W +: SLOT_W])] <=
              bank_rsp_data[seq_bank_i*1024 +: 1024];
          end
        end
        response_count_q <= response_count_q + response_fire_count;
        if (response_count_q + response_fire_count ==
            RESPONSE_COUNT_W'(WORDS_PER_GROUP)) begin
          buffer_state[fill_buffer_q] <= BUF_READY;
          fill_active_q <= 1'b0;
          issuing_q <= 1'b0;
        end
      end

      if (compute_fire) begin
        compute_beat_count <= compute_beat_count + 1'b1;
        if (!compute_active_q) begin
          compute_buffer_q <= ready_buffer_select;
          buffer_state[ready_buffer_select] <= BUF_COMPUTE;
          if (DIMS_PER_GROUP == 1) begin
            buffer_state[ready_buffer_select] <= BUF_EMPTY;
            if (expected_compute_group_q == GROUP_W'(DIM_GROUPS - 1)) begin
              busy_q <= 1'b0;
              done <= 1'b1;
            end else begin
              expected_compute_group_q <= expected_compute_group_q + 1'b1;
            end
          end else begin
            compute_active_q <= 1'b1;
            compute_dimension_q <= DIM_W'(1);
          end
        end else if (compute_dimension_q == DIM_W'(DIMS_PER_GROUP - 1)) begin
          buffer_state[compute_buffer_q] <= BUF_EMPTY;
          compute_active_q <= 1'b0;
          compute_dimension_q <= {DIM_W{1'b0}};
          if (expected_compute_group_q == GROUP_W'(DIM_GROUPS - 1)) begin
            busy_q <= 1'b0;
            done <= 1'b1;
          end else begin
            expected_compute_group_q <= expected_compute_group_q + 1'b1;
          end
        end else begin
          compute_dimension_q <= compute_dimension_q + 1'b1;
        end
      end
    end
  end
endmodule
