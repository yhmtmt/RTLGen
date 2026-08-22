`timescale 1ns/1ps

// Area-conservative K scheduler.  Two 17-word windows alternate over eight
// block rounds per dimension group, avoiding the 2x128-word state vector of
// the fully parallel window while preserving one request per SRAM bank.
module attention_shared_sram_k_round_scheduler #(
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
  output reg [(BANKS*3)-1:0] bank_req_group,
  output reg [(BANKS*3)-1:0] bank_req_round,
  output reg [(BANKS*7)-1:0] bank_req_word_slot,

  input wire [BANKS-1:0] bank_rsp_valid,
  output wire [BANKS-1:0] bank_rsp_ready,
  input wire [(BANKS*1024)-1:0] bank_rsp_data,
  input wire [BANKS-1:0] bank_rsp_buffer,
  input wire [(BANKS*3)-1:0] bank_rsp_group,
  input wire [(BANKS*3)-1:0] bank_rsp_round,
  input wire [(BANKS*7)-1:0] bank_rsp_word_slot,

  output wire compute_valid,
  input wire compute_ready,
  output wire [2:0] compute_group,
  output wire [2:0] compute_round,
  output wire [3:0] compute_dimension,
  output wire compute_last,
  output wire [BANKS-1:0] compute_word_valid,
  output wire [(BANKS*64)-1:0] compute_k_beats,

  output reg done,
  output reg protocol_error,
  output reg [63:0] bank_request_count,
  output reg [63:0] bank_response_count,
  output reg [63:0] compute_beat_count,
  output reg [63:0] bank_request_stall_count,
  output reg [63:0] compute_output_stall_count,
  output reg [63:0] compute_wait_for_window_count
);
  localparam integer ROUNDS_PER_GROUP = (WORDS_PER_GROUP + BANKS - 1) / BANKS;
  localparam integer TOTAL_WINDOWS = DIM_GROUPS * ROUNDS_PER_GROUP;
  localparam integer WINDOW_INDEX_W = $clog2(TOTAL_WINDOWS + 1);

  localparam [1:0] BUF_EMPTY = 2'd0;
  localparam [1:0] BUF_FILL = 2'd1;
  localparam [1:0] BUF_READY = 2'd2;
  localparam [1:0] BUF_COMPUTE = 2'd3;

  reg busy_q;
  reg [ADDR_W-1:0] base_word_addr_q;
  reg [4:0] base_bank_q;
  reg [1:0] buffer_state [0:1];
  reg [2:0] buffer_group [0:1];
  reg [2:0] buffer_round [0:1];
  reg fill_active_q;
  reg fill_buffer_q;
  reg [2:0] fill_group_q;
  reg [2:0] fill_round_q;
  reg issuing_q;
  reg [BANKS-1:0] issue_done_mask_q;
  reg [BANKS-1:0] issued_local_q;
  reg [BANKS-1:0] received_local_q;
  reg [5:0] response_count_q;
  reg [WINDOW_INDEX_W-1:0] next_fill_window_q;

  reg compute_active_q;
  reg compute_buffer_q;
  reg [3:0] compute_dimension_q;
  reg [WINDOW_INDEX_W-1:0] expected_compute_window_q;

  reg [BANKS-1:0] window_valid_mask;
  reg [BANKS-1:0] request_fire_mask;
  reg [BANKS-1:0] request_issued_local_mask;
  reg [BANKS-1:0] response_received_mask;
  reg ready_buffer_found;
  reg ready_buffer_select;
  reg [63:0] request_stall_increment;
  integer req_local_i;
  integer req_bank_i;
  integer stall_bank_i;
  integer mask_bank_i;

  function [ADDR_W-1:0] word_addr;
    input [2:0] group_index;
    input [6:0] word_slot;
    begin
      word_addr = base_word_addr_q + ADDR_W'(word_slot * DIM_GROUPS) +
        ADDR_W'(group_index);
    end
  endfunction

  function [BANKS-1:0] valid_mask_for_round;
    input [2:0] round_index;
    integer local_i;
    begin
      valid_mask_for_round = {BANKS{1'b0}};
      for (local_i = 0; local_i < BANKS; local_i = local_i + 1)
        if ((round_index * BANKS) + local_i < WORDS_PER_GROUP)
          valid_mask_for_round[local_i] = 1'b1;
    end
  endfunction

  function [4:0] bank_offset_for_local;
    input [4:0] local_index;
    begin
      case (local_index)
        5'd0: bank_offset_for_local = 5'd0;
        5'd1: bank_offset_for_local = 5'd8;
        5'd2: bank_offset_for_local = 5'd16;
        5'd3: bank_offset_for_local = 5'd7;
        5'd4: bank_offset_for_local = 5'd15;
        5'd5: bank_offset_for_local = 5'd6;
        5'd6: bank_offset_for_local = 5'd14;
        5'd7: bank_offset_for_local = 5'd5;
        5'd8: bank_offset_for_local = 5'd13;
        5'd9: bank_offset_for_local = 5'd4;
        5'd10: bank_offset_for_local = 5'd12;
        5'd11: bank_offset_for_local = 5'd3;
        5'd12: bank_offset_for_local = 5'd11;
        5'd13: bank_offset_for_local = 5'd2;
        5'd14: bank_offset_for_local = 5'd10;
        5'd15: bank_offset_for_local = 5'd1;
        5'd16: bank_offset_for_local = 5'd9;
        default: bank_offset_for_local = 5'd0;
      endcase
    end
  endfunction

  function [4:0] bank_for_local;
    input [4:0] base_bank;
    input [2:0] group_index;
    input [4:0] local_index;
    reg [5:0] bank_sum;
    begin
      bank_sum = {1'b0, base_bank} + {3'd0, group_index} +
        {1'b0, bank_offset_for_local(local_index)};
      if (bank_sum >= 6'd34)
        bank_for_local = 5'(bank_sum - 6'd34);
      else if (bank_sum >= 6'd17)
        bank_for_local = 5'(bank_sum - 6'd17);
      else
        bank_for_local = bank_sum[4:0];
    end
  endfunction

  assign command_ready = !busy_q && !protocol_error;
  wire command_fire = command_valid && command_ready;

  always @* begin
    bank_req_valid = {BANKS{1'b0}};
    bank_req_word_addr = {(BANKS*ADDR_W){1'b0}};
    bank_req_buffer = {BANKS{1'b0}};
    bank_req_group = {(BANKS*3){1'b0}};
    bank_req_round = {(BANKS*3){1'b0}};
    bank_req_word_slot = {(BANKS*7){1'b0}};
    window_valid_mask = valid_mask_for_round(fill_round_q);
    req_bank_i = 0;
    if (fill_active_q && issuing_q && !protocol_error) begin
      for (req_local_i = 0; req_local_i < BANKS; req_local_i = req_local_i + 1) begin
        if (window_valid_mask[req_local_i]) begin
          req_bank_i = 32'(bank_for_local(
            base_bank_q, fill_group_q, 5'(req_local_i)
          ));
          if (!issue_done_mask_q[req_bank_i]) begin
            bank_req_valid[req_bank_i] = 1'b1;
            bank_req_word_addr[req_bank_i*ADDR_W +: ADDR_W] = word_addr(
              fill_group_q, 7'((fill_round_q * BANKS) + req_local_i)
            );
            bank_req_buffer[req_bank_i] = fill_buffer_q;
            bank_req_group[req_bank_i*3 +: 3] = fill_group_q;
            bank_req_round[req_bank_i*3 +: 3] = fill_round_q;
            bank_req_word_slot[req_bank_i*7 +: 7] =
              7'((fill_round_q * BANKS) + req_local_i);
          end
        end
      end
    end
    request_fire_mask = bank_req_valid & bank_req_ready;
  end

  assign bank_rsp_ready = {BANKS{busy_q && !protocol_error}};
  wire [BANKS-1:0] response_fire_mask = bank_rsp_valid & bank_rsp_ready;
  wire [5:0] response_fire_count = 6'($countones(response_fire_mask));
  wire [BANKS-1:0] response_error_mask;
  wire [(BANKS*BANKS)-1:0] response_local_onehots;
  wire [(BANKS*BANKS)-1:0] request_local_onehots;
  wire response_batch_error = |response_error_mask;

  genvar metadata_bank_g;
  generate
    for (metadata_bank_g = 0; metadata_bank_g < BANKS;
         metadata_bank_g = metadata_bank_g + 1) begin : gen_response_metadata
      wire [6:0] response_slot =
        bank_rsp_word_slot[metadata_bank_g*7 +: 7];
      wire [7:0] round_base = {1'b0, fill_round_q, 4'b0} +
        {5'd0, fill_round_q};
      wire [7:0] response_slot_ext = {1'b0, response_slot};
      wire response_slot_in_range = response_slot_ext >= round_base &&
        response_slot_ext < round_base + 8'(BANKS) &&
        response_slot_ext < 8'(WORDS_PER_GROUP);
      wire [4:0] response_local = 5'(response_slot_ext - round_base);
      wire response_local_valid = response_slot_in_range &&
        window_valid_mask[response_local];
      wire response_local_issued = response_local_valid &&
        issued_local_q[response_local];
      wire response_local_received = response_local_valid &&
        received_local_q[response_local];
      wire [4:0] expected_response_bank = bank_for_local(
        base_bank_q, fill_group_q, response_local
      );
      assign response_error_mask[metadata_bank_g] =
        response_fire_mask[metadata_bank_g] &&
        (!fill_active_q ||
         bank_rsp_buffer[metadata_bank_g] != fill_buffer_q ||
         bank_rsp_group[metadata_bank_g*3 +: 3] != fill_group_q ||
         bank_rsp_round[metadata_bank_g*3 +: 3] != fill_round_q ||
         !response_local_valid || !response_local_issued ||
         response_local_received || expected_response_bank != 5'(metadata_bank_g));
      assign response_local_onehots[metadata_bank_g*BANKS +: BANKS] =
        (response_fire_mask[metadata_bank_g] && response_local_valid) ?
          (BANKS'(1) << response_local) : {BANKS{1'b0}};

      wire [7:0] request_slot_ext =
        {1'b0, bank_req_word_slot[metadata_bank_g*7 +: 7]};
      wire [4:0] request_local = 5'(request_slot_ext - round_base);
      assign request_local_onehots[metadata_bank_g*BANKS +: BANKS] =
        request_fire_mask[metadata_bank_g] ?
          (BANKS'(1) << request_local) : {BANKS{1'b0}};
    end
  endgenerate

  always @* begin
    request_issued_local_mask = {BANKS{1'b0}};
    response_received_mask = {BANKS{1'b0}};
    for (mask_bank_i = 0; mask_bank_i < BANKS; mask_bank_i = mask_bank_i + 1) begin
      request_issued_local_mask = request_issued_local_mask |
        request_local_onehots[mask_bank_i*BANKS +: BANKS];
      response_received_mask = response_received_mask |
        response_local_onehots[mask_bank_i*BANKS +: BANKS];
    end
  end

  // The checked Llama7B geometry has eight rounds per group.  Keeping the
  // decode as bit selection avoids synthesizing generic divide/modulo logic.
  wire [2:0] expected_group = expected_compute_window_q[5:3];
  wire [2:0] expected_round = expected_compute_window_q[2:0];
  always @* begin
    ready_buffer_found = 1'b0;
    ready_buffer_select = 1'b0;
    if (buffer_state[0] == BUF_READY && buffer_group[0] == expected_group &&
        buffer_round[0] == expected_round) begin
      ready_buffer_found = 1'b1;
      ready_buffer_select = 1'b0;
    end else if (buffer_state[1] == BUF_READY && buffer_group[1] == expected_group &&
                 buffer_round[1] == expected_round) begin
      ready_buffer_found = 1'b1;
      ready_buffer_select = 1'b1;
    end
  end

  wire selected_buffer = compute_active_q ? compute_buffer_q : ready_buffer_select;
  wire [3:0] selected_dimension = compute_active_q ? compute_dimension_q : 4'd0;
  assign compute_valid = busy_q && !protocol_error &&
    (compute_active_q || ready_buffer_found);
  assign compute_group = expected_group;
  assign compute_round = expected_round;
  assign compute_dimension = selected_dimension;
  assign compute_last = compute_valid && selected_dimension == 4'd15;
  assign compute_word_valid = valid_mask_for_round(expected_round);
  wire compute_fire = compute_valid && compute_ready;

  (* keep = "true" *) wire [(BANKS*64)-1:0] selected_bank_lanes;
  genvar storage_bank_g;
  generate
    for (storage_bank_g = 0; storage_bank_g < BANKS;
         storage_bank_g = storage_bank_g + 1) begin : gen_bank_storage
      attention_shared_sram_k_round_bank bank_storage (
        .clk(clk),
        .write_valid(
          bank_rsp_valid[storage_bank_g] && bank_rsp_ready[storage_bank_g] &&
          !response_batch_error && busy_q && !protocol_error
        ),
        .write_buffer(fill_buffer_q),
        .write_data(bank_rsp_data[storage_bank_g*1024 +: 1024]),
        .read_buffer(selected_buffer),
        .read_dimension(selected_dimension),
        .read_lane(selected_bank_lanes[storage_bank_g*64 +: 64])
      );
    end
  endgenerate

  genvar compute_local_g;
  generate
    for (compute_local_g = 0; compute_local_g < BANKS;
         compute_local_g = compute_local_g + 1) begin : gen_compute
      wire [4:0] compute_storage_bank = bank_for_local(
        base_bank_q, expected_group, 5'(compute_local_g)
      );
      assign compute_k_beats[compute_local_g*64 +: 64] =
        compute_word_valid[compute_local_g] ?
          selected_bank_lanes[compute_storage_bank*64 +: 64] : 64'd0;
    end
  endgenerate

  always @* begin
    request_stall_increment = 64'd0;
    for (stall_bank_i = 0; stall_bank_i < BANKS; stall_bank_i = stall_bank_i + 1)
      if (bank_req_valid[stall_bank_i] && !bank_req_ready[stall_bank_i])
        request_stall_increment = request_stall_increment + 1'b1;
  end

`ifndef SYNTHESIS
  initial begin
    if (BANKS != 17 || WORDS_PER_GROUP != 128 || DIM_GROUPS != 8 ||
        DIMS_PER_GROUP != 16 || ROUNDS_PER_GROUP != 8) begin
      $error("attention_shared_sram_k_round_scheduler requires Llama7B 17/128/8/16 geometry");
      $finish(1);
    end
  end
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy_q <= 1'b0;
      base_word_addr_q <= {ADDR_W{1'b0}};
      base_bank_q <= 5'd0;
      buffer_state[0] <= BUF_EMPTY;
      buffer_state[1] <= BUF_EMPTY;
      buffer_group[0] <= 3'd0;
      buffer_group[1] <= 3'd0;
      buffer_round[0] <= 3'd0;
      buffer_round[1] <= 3'd0;
      fill_active_q <= 1'b0;
      fill_buffer_q <= 1'b0;
      fill_group_q <= 3'd0;
      fill_round_q <= 3'd0;
      issuing_q <= 1'b0;
      issue_done_mask_q <= {BANKS{1'b0}};
      issued_local_q <= {BANKS{1'b0}};
      received_local_q <= {BANKS{1'b0}};
      response_count_q <= 6'd0;
      next_fill_window_q <= {WINDOW_INDEX_W{1'b0}};
      compute_active_q <= 1'b0;
      compute_buffer_q <= 1'b0;
      compute_dimension_q <= 4'd0;
      expected_compute_window_q <= {WINDOW_INDEX_W{1'b0}};
      done <= 1'b0;
      protocol_error <= 1'b0;
      bank_request_count <= 64'd0;
      bank_response_count <= 64'd0;
      compute_beat_count <= 64'd0;
      bank_request_stall_count <= 64'd0;
      compute_output_stall_count <= 64'd0;
      compute_wait_for_window_count <= 64'd0;
    end else begin
      done <= 1'b0;
      bank_request_stall_count <= bank_request_stall_count + request_stall_increment;
      if (compute_valid && !compute_ready)
        compute_output_stall_count <= compute_output_stall_count + 1'b1;
      if (busy_q && !compute_active_q && !ready_buffer_found)
        compute_wait_for_window_count <= compute_wait_for_window_count + 1'b1;

      if (command_fire) begin
        busy_q <= 1'b1;
        base_word_addr_q <= command_base_word_addr;
        base_bank_q <= 5'(32'(command_base_word_addr) % BANKS);
        buffer_state[0] <= BUF_EMPTY;
        buffer_state[1] <= BUF_EMPTY;
        fill_active_q <= 1'b0;
        next_fill_window_q <= {WINDOW_INDEX_W{1'b0}};
        compute_active_q <= 1'b0;
        expected_compute_window_q <= {WINDOW_INDEX_W{1'b0}};
      end

      if (busy_q && !fill_active_q &&
          next_fill_window_q < WINDOW_INDEX_W'(TOTAL_WINDOWS) &&
          (buffer_state[0] == BUF_EMPTY || buffer_state[1] == BUF_EMPTY)) begin
        fill_active_q <= 1'b1;
        fill_buffer_q <= (buffer_state[0] == BUF_EMPTY) ? 1'b0 : 1'b1;
        fill_group_q <= next_fill_window_q[5:3];
        fill_round_q <= next_fill_window_q[2:0];
        buffer_state[(buffer_state[0] == BUF_EMPTY) ? 0 : 1] <= BUF_FILL;
        buffer_group[(buffer_state[0] == BUF_EMPTY) ? 0 : 1] <=
          next_fill_window_q[5:3];
        buffer_round[(buffer_state[0] == BUF_EMPTY) ? 0 : 1] <=
          next_fill_window_q[2:0];
        next_fill_window_q <= next_fill_window_q + 1'b1;
        issuing_q <= 1'b1;
        issue_done_mask_q <= {BANKS{1'b0}};
        issued_local_q <= {BANKS{1'b0}};
        received_local_q <= {BANKS{1'b0}};
        response_count_q <= 6'd0;
      end

      if (|request_fire_mask) begin
        bank_request_count <= bank_request_count + 64'($countones(request_fire_mask));
        issued_local_q <= issued_local_q | request_issued_local_mask;
        issue_done_mask_q <= issue_done_mask_q | request_fire_mask;
        if ($countones(issue_done_mask_q | request_fire_mask) ==
            $countones(window_valid_mask))
          issuing_q <= 1'b0;
      end

      if (response_batch_error)
        protocol_error <= 1'b1;
      if ((|bank_rsp_valid) && !response_batch_error && busy_q && !protocol_error) begin
        bank_response_count <= bank_response_count + 64'(response_fire_count);
        received_local_q <= received_local_q | response_received_mask;
        response_count_q <= response_count_q + response_fire_count;
        if (response_count_q + response_fire_count ==
            $countones(window_valid_mask)) begin
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
          compute_active_q <= 1'b1;
          compute_dimension_q <= 4'd1;
        end else if (compute_dimension_q == 4'd15) begin
          buffer_state[compute_buffer_q] <= BUF_EMPTY;
          compute_active_q <= 1'b0;
          compute_dimension_q <= 4'd0;
          if (expected_compute_window_q == WINDOW_INDEX_W'(TOTAL_WINDOWS-1)) begin
            busy_q <= 1'b0;
            done <= 1'b1;
          end else begin
            expected_compute_window_q <= expected_compute_window_q + 1'b1;
          end
        end else begin
          compute_dimension_q <= compute_dimension_q + 1'b1;
        end
      end
    end
  end
endmodule
