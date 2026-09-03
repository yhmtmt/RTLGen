`timescale 1ns/1ps

// Stages one exact int8 K head tile and one eight-query-head Q group, then
// drives all p53/p54 producers with per-lane ready/valid accounting.
module attention_score32_exact_kv_key_stage #(
  parameter integer PRODUCERS = 53
) (
  input wire clk,
  input wire rst_n,

  input wire fill_target_valid,
  output wire fill_target_ready,
  input wire [1:0] fill_target_kv_head,

  input wire query_write_valid,
  output wire query_write_ready,
  input wire [1:0] query_write_kv_head,
  input wire [6:0] query_write_dimension,
  input wire [63:0] query_write_data,
  input wire query_write_last,

  input wire key_write_valid,
  output wire key_write_ready,
  input wire [1:0] key_write_kv_head,
  input wire [5:0] key_write_producer,
  input wire key_write_producer_block,
  input wire [6:0] key_write_dimension,
  input wire [127:0] key_write_data,
  input wire key_write_last,

  output wire fill_complete,

  input wire command_valid,
  output wire command_ready,
  input wire [1:0] command_kv_head,
  output wire [PRODUCERS-1:0] producer_valid,
  input wire [PRODUCERS-1:0] producer_ready,
  output wire [PRODUCERS-1:0] producer_last,
  output wire [(PRODUCERS*128)-1:0] producer_query,
  output wire [(PRODUCERS*128)-1:0] producer_key,
  output reg command_done,
  output reg protocol_error
);
  reg fill_active_q;
  reg [1:0] fill_head_q;
  reg query_complete_q;
  reg [6:0] query_expected_dimension_q;
  reg [63:0] query_mem [0:127];
  reg [63:0] key_block_valid_q;
  reg [6:0] key_expected_dimension_q [0:63];

  reg command_active_q;
  reg [7:0] command_beat_q;
  reg [PRODUCERS-1:0] pending_q;

  integer clear_i;
  integer active_i;
  integer pending_i;
  reg [PRODUCERS-1:0] active_mask_r;
  reg [PRODUCERS-1:0] accepted_mask_r;
  reg [PRODUCERS-1:0] remaining_mask_r;

  function automatic producer_has_extra;
    input integer producer;
    input [1:0] group_index;
    integer start_index;
    integer stop_index;
    begin
      if (PRODUCERS == 53) begin
        start_index = group_index * 11;
        stop_index = start_index + 11;
      end else begin
        start_index = group_index * 10;
        stop_index = start_index + 10;
      end
      producer_has_extra = (producer >= start_index) && (producer < stop_index);
    end
  endfunction

  function automatic [5:0] producer_slot;
    input [5:0] producer;
    input producer_block;
    input [1:0] group_index;
    integer index;
    integer cursor;
    begin
      cursor = 0;
      for (index = 0; index < PRODUCERS; index = index + 1) begin
        if (index < {26'd0, producer})
          cursor = cursor + (producer_has_extra(index, group_index) ? 2 : 1);
      end
      producer_slot = cursor[5:0];
      if (producer_block)
        producer_slot = producer_slot + 6'd1;
    end
  endfunction

  wire [5:0] key_write_slot = producer_slot(
    key_write_producer, key_write_producer_block, fill_head_q
  );
  wire key_write_producer_valid = {26'd0, key_write_producer} < PRODUCERS;
  wire key_write_block_valid = key_write_producer_valid &&
    (!key_write_producer_block ||
     producer_has_extra({26'd0, key_write_producer}, fill_head_q));
  wire key_write_metadata_valid =
    key_write_kv_head == fill_head_q && key_write_block_valid &&
    !key_block_valid_q[key_write_slot] &&
    key_write_dimension == key_expected_dimension_q[key_write_slot] &&
    key_write_last == (key_write_dimension == 7'd127);
  wire query_write_metadata_valid =
    query_write_kv_head == fill_head_q && !query_complete_q &&
    query_write_dimension == query_expected_dimension_q &&
    query_write_last == (query_write_dimension == 7'd127);

  assign fill_target_ready = !fill_active_q && !command_active_q;
  assign query_write_ready = fill_active_q;
  assign key_write_ready = fill_active_q;
  assign fill_complete = fill_active_q && query_complete_q && (&key_block_valid_q);
  assign command_ready = fill_complete && !command_active_q && command_kv_head == fill_head_q;
  assign producer_valid = pending_q;

  wire [8191:0] key_bank_read_data;
  generate
    genvar bank;
    for (bank = 0; bank < 64; bank = bank + 1) begin : g_key_bank
      reg [127:0] bank_mem [0:127];
      always @(posedge clk) begin
        if (key_write_valid && key_write_ready && key_write_metadata_valid &&
            key_write_slot == bank)
          bank_mem[key_write_dimension] <= key_write_data;
      end
      assign key_bank_read_data[(bank*128) +: 128] = bank_mem[command_beat_q[6:0]];
    end
  endgenerate

  always @(*) begin
    active_mask_r = {PRODUCERS{1'b1}};
    if (command_beat_q[7]) begin
      for (active_i = 0; active_i < PRODUCERS; active_i = active_i + 1)
        active_mask_r[active_i] = producer_has_extra(active_i, fill_head_q);
    end
    accepted_mask_r = pending_q & producer_ready;
    remaining_mask_r = pending_q & ~producer_ready;
  end

  generate
    genvar producer;
    for (producer = 0; producer < PRODUCERS; producer = producer + 1) begin : g_read
      localparam [5:0] PRODUCER_INDEX = producer;
      wire [5:0] read_slot_w = producer_slot(
        PRODUCER_INDEX, command_beat_q[7], fill_head_q
      );
      assign producer_query[(producer*128) +: 128] =
        {query_mem[command_beat_q[6:0]], query_mem[command_beat_q[6:0]]};
      assign producer_key[(producer*128) +: 128] =
        key_bank_read_data[(read_slot_w*128) +: 128];
      assign producer_last[producer] = pending_q[producer] &&
        (command_beat_q[6:0] == 7'd127);
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fill_active_q <= 1'b0;
      fill_head_q <= 2'd0;
      query_complete_q <= 1'b0;
      query_expected_dimension_q <= 7'd0;
      key_block_valid_q <= 64'd0;
      command_active_q <= 1'b0;
      command_beat_q <= 8'd0;
      pending_q <= {PRODUCERS{1'b0}};
      command_done <= 1'b0;
      protocol_error <= 1'b0;
      for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1)
        key_expected_dimension_q[clear_i] <= 7'd0;
    end else begin
      command_done <= 1'b0;

      if (fill_target_valid && fill_target_ready) begin
        fill_active_q <= 1'b1;
        fill_head_q <= fill_target_kv_head;
        query_complete_q <= 1'b0;
        query_expected_dimension_q <= 7'd0;
        key_block_valid_q <= 64'd0;
        for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1)
          key_expected_dimension_q[clear_i] <= 7'd0;
      end

      if (query_write_valid && query_write_ready) begin
        if (!query_write_metadata_valid) begin
          protocol_error <= 1'b1;
        end else begin
          query_mem[query_write_dimension] <= query_write_data;
          if (query_write_last)
            query_complete_q <= 1'b1;
          else
            query_expected_dimension_q <= query_expected_dimension_q + 1'b1;
        end
      end

      if (key_write_valid && key_write_ready) begin
        if (!key_write_metadata_valid) begin
          protocol_error <= 1'b1;
        end else begin
          if (key_write_last)
            key_block_valid_q[key_write_slot] <= 1'b1;
          else
            key_expected_dimension_q[key_write_slot] <=
              key_expected_dimension_q[key_write_slot] + 1'b1;
        end
      end

      if (command_valid && command_ready) begin
        fill_active_q <= 1'b0;
        command_active_q <= 1'b1;
        command_beat_q <= 8'd0;
        pending_q <= {PRODUCERS{1'b1}};
      end

      if (command_active_q && |accepted_mask_r) begin
        pending_q <= remaining_mask_r;
        if (remaining_mask_r == {PRODUCERS{1'b0}}) begin
          if (command_beat_q == 8'd255) begin
            command_active_q <= 1'b0;
            command_done <= 1'b1;
          end else begin
            command_beat_q <= command_beat_q + 1'b1;
            if (command_beat_q == 8'd127) begin
              for (pending_i = 0; pending_i < PRODUCERS; pending_i = pending_i + 1)
                pending_q[pending_i] <= producer_has_extra(pending_i, fill_head_q);
            end else
              pending_q <= active_mask_r;
          end
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if ((PRODUCERS != 53) && (PRODUCERS != 54)) begin
      $error("attention_score32_exact_kv_key_stage PRODUCERS must be 53 or 54");
      $finish(1);
    end
  end
`endif
endmodule
