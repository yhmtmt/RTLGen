`timescale 1ns/1ps

// Composes canonical planar V ingress with one exact cluster-SRAM fill port.
// One fill target owns all 128 (stream, block-slot) blocks of one KV head.
module attention_score32_exact_kv_value_ingress #(
  parameter integer PRODUCERS = 53
) (
  input  wire clk,
  input  wire rst_n,

  input  wire fill_target_valid,
  output wire fill_target_ready,
  input  wire fill_target_buffer_sel,
  input  wire [15:0] fill_target_command_id,
  input  wire [4:0] fill_target_head_base,
  input  wire [2:0] fill_target_wave_index,

  output wire endpoint_fill_target_valid,
  input  wire endpoint_fill_target_ready,
  output wire endpoint_fill_target_buffer_sel,
  output wire [15:0] endpoint_fill_target_command_id,
  output wire [4:0] endpoint_fill_target_head_base,
  output wire [2:0] endpoint_fill_target_wave_index,

  input  wire block_target_valid,
  output wire block_target_ready,
  input  wire [1:0] block_target_kv_head,
  input  wire block_target_stream,
  input  wire [5:0] block_target_slot,

  input  wire ingress_valid,
  output wire ingress_ready,
  input  wire [19:0] ingress_tile_byte_addr,
  input  wire [255:0] ingress_data,
  input  wire [31:0] ingress_byte_valid,

  output wire endpoint_fill_valid,
  input  wire endpoint_fill_ready,
  output wire endpoint_fill_buffer_sel,
  output wire endpoint_fill_stream,
  output wire [5:0] endpoint_fill_block_slot,
  output wire [3:0] endpoint_fill_slice,
  output wire [511:0] endpoint_fill_data,

  output reg fill_complete,
  output wire fill_active,
  output wire [7:0] completed_block_count,
  output wire protocol_error
);
  reg fill_active_q;
  reg fill_buffer_q;
  reg [1:0] fill_kv_head_q;
  reg [127:0] completed_blocks_q;
  reg [7:0] completed_block_count_q;
  reg metadata_error_q;

  wire fill_target_metadata_valid =
    (fill_target_head_base[2:0] == 3'd0) &&
    (fill_target_head_base <= 5'd24) &&
    (fill_target_buffer_sel == fill_target_wave_index[0]);
  wire fill_target_fire = fill_target_valid && fill_target_ready;

  wire [6:0] block_index = {block_target_stream, block_target_slot};
  wire block_target_metadata_valid =
    (block_target_kv_head == fill_kv_head_q) &&
    !completed_blocks_q[block_index];

  wire transpose_target_ready;
  wire transpose_value_valid;
  wire transpose_value_stream;
  wire [1:0] transpose_value_kv_head;
  wire [5:0] transpose_value_block_slot;
  wire [3:0] transpose_value_slice;
  wire [511:0] transpose_value_data;
  wire transpose_value_last;
  wire transpose_protocol_error;
  wire unused_key_valid;
  wire [5:0] unused_key_producer;
  wire [1:0] unused_key_kv_head;
  wire unused_key_producer_block;
  wire [6:0] unused_key_dimension;
  wire [127:0] unused_key_data;
  wire unused_key_last;
  wire value_fire = transpose_value_valid && endpoint_fill_ready;

  assign fill_target_ready = !fill_active_q && fill_target_metadata_valid &&
    endpoint_fill_target_ready;
  assign endpoint_fill_target_valid = fill_target_valid && !fill_active_q &&
    fill_target_metadata_valid;
  assign endpoint_fill_target_buffer_sel = fill_target_buffer_sel;
  assign endpoint_fill_target_command_id = fill_target_command_id;
  assign endpoint_fill_target_head_base = fill_target_head_base;
  assign endpoint_fill_target_wave_index = fill_target_wave_index;

  assign block_target_ready = fill_active_q && block_target_metadata_valid &&
    transpose_target_ready;
  assign endpoint_fill_valid = transpose_value_valid;
  assign endpoint_fill_buffer_sel = fill_buffer_q;
  assign endpoint_fill_stream = transpose_value_stream;
  assign endpoint_fill_block_slot = transpose_value_block_slot;
  assign endpoint_fill_slice = transpose_value_slice;
  assign endpoint_fill_data = transpose_value_data;

  assign fill_active = fill_active_q;
  assign completed_block_count = completed_block_count_q;
  assign protocol_error = metadata_error_q || transpose_protocol_error;

  attention_score32_exact_kv_ingress_transpose #(
    .PRODUCERS(PRODUCERS)
  ) u_transpose (
    .clk(clk),
    .rst_n(rst_n),
    .target_valid(block_target_valid && fill_active_q && block_target_metadata_valid),
    .target_ready(transpose_target_ready),
    .target_is_key(1'b0),
    .target_kv_head(block_target_kv_head),
    .target_stream(block_target_stream),
    .target_block_slot(block_target_slot),
    .ingress_valid(ingress_valid),
    .ingress_ready(ingress_ready),
    .ingress_tile_byte_addr(ingress_tile_byte_addr),
    .ingress_data(ingress_data),
    .ingress_byte_valid(ingress_byte_valid),
    .value_valid(transpose_value_valid),
    .value_ready(endpoint_fill_ready),
    .value_stream(transpose_value_stream),
    .value_kv_head(transpose_value_kv_head),
    .value_block_slot(transpose_value_block_slot),
    .value_slice(transpose_value_slice),
    .value_data(transpose_value_data),
    .value_last(transpose_value_last),
    .key_valid(unused_key_valid),
    .key_ready(1'b0),
    .key_producer(unused_key_producer),
    .key_kv_head(unused_key_kv_head),
    .key_producer_block(unused_key_producer_block),
    .key_dimension(unused_key_dimension),
    .key_data(unused_key_data),
    .key_last(unused_key_last),
    .protocol_error(transpose_protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fill_active_q <= 1'b0;
      fill_buffer_q <= 1'b0;
      fill_kv_head_q <= 2'd0;
      completed_blocks_q <= 128'd0;
      completed_block_count_q <= 8'd0;
      fill_complete <= 1'b0;
      metadata_error_q <= 1'b0;
    end else begin
      fill_complete <= 1'b0;
      if (fill_target_valid && !fill_active_q && !fill_target_metadata_valid)
        metadata_error_q <= 1'b1;

      if (fill_target_fire) begin
        fill_active_q <= 1'b1;
        fill_buffer_q <= fill_target_buffer_sel;
        fill_kv_head_q <= fill_target_head_base[4:3];
        completed_blocks_q <= 128'd0;
        completed_block_count_q <= 8'd0;
      end

      if (block_target_valid && fill_active_q && transpose_target_ready &&
          !block_target_metadata_valid)
        metadata_error_q <= 1'b1;

      if (value_fire) begin
        if (transpose_value_kv_head != fill_kv_head_q)
          metadata_error_q <= 1'b1;
        if (transpose_value_last) begin
          completed_blocks_q[{transpose_value_stream, transpose_value_block_slot}] <= 1'b1;
          completed_block_count_q <= completed_block_count_q + 1'b1;
          if (completed_block_count_q == 8'd127) begin
            fill_active_q <= 1'b0;
            fill_complete <= 1'b1;
          end
        end
      end
    end
  end
endmodule
