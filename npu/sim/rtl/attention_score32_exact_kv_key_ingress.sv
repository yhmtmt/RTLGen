`timescale 1ns/1ps

// Composes canonical planar K-flit transposition with the producer-local
// staging store. Block target sequencing and Q writes remain explicit ports.
module attention_score32_exact_kv_key_ingress #(
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
  input wire key_block_target_valid,
  output wire key_block_target_ready,
  input wire [1:0] key_block_target_kv_head,
  input wire [5:0] key_block_target_slot,
  input wire ingress_valid,
  output wire ingress_ready,
  input wire [19:0] ingress_tile_byte_addr,
  input wire [255:0] ingress_data,
  input wire [31:0] ingress_byte_valid,
  output wire fill_complete,
  input wire command_valid,
  output wire command_ready,
  input wire [1:0] command_kv_head,
  output wire [PRODUCERS-1:0] producer_valid,
  input wire [PRODUCERS-1:0] producer_ready,
  output wire [PRODUCERS-1:0] producer_last,
  output wire [(PRODUCERS*128)-1:0] producer_query,
  output wire [(PRODUCERS*128)-1:0] producer_key,
  output wire command_done,
  output wire protocol_error
);
  wire [1:0] transposed_key_head;
  wire [5:0] transposed_key_producer;
  wire transposed_key_producer_block;
  wire [6:0] transposed_key_dimension;
  wire [127:0] transposed_key_data;
  wire transposed_key_valid;
  wire transposed_key_ready;
  wire transposed_key_last;
  wire unexpected_value_valid;
  wire unexpected_value_stream;
  wire [1:0] unexpected_value_head;
  wire [5:0] unexpected_value_block;
  wire [3:0] unexpected_value_slice;
  wire [511:0] unexpected_value_data;
  wire unexpected_value_last;
  wire transpose_error;
  wire stage_error;

  attention_score32_exact_kv_ingress_transpose #(.PRODUCERS(PRODUCERS)) u_transpose (
    .clk(clk),
    .rst_n(rst_n),
    .target_valid(key_block_target_valid),
    .target_ready(key_block_target_ready),
    .target_is_key(1'b1),
    .target_kv_head(key_block_target_kv_head),
    .target_stream(1'b0),
    .target_block_slot(key_block_target_slot),
    .ingress_valid(ingress_valid),
    .ingress_ready(ingress_ready),
    .ingress_tile_byte_addr(ingress_tile_byte_addr),
    .ingress_data(ingress_data),
    .ingress_byte_valid(ingress_byte_valid),
    .value_valid(unexpected_value_valid),
    .value_ready(1'b0),
    .value_stream(unexpected_value_stream),
    .value_kv_head(unexpected_value_head),
    .value_block_slot(unexpected_value_block),
    .value_slice(unexpected_value_slice),
    .value_data(unexpected_value_data),
    .value_last(unexpected_value_last),
    .key_valid(transposed_key_valid),
    .key_ready(transposed_key_ready),
    .key_producer(transposed_key_producer),
    .key_kv_head(transposed_key_head),
    .key_producer_block(transposed_key_producer_block),
    .key_dimension(transposed_key_dimension),
    .key_data(transposed_key_data),
    .key_last(transposed_key_last),
    .protocol_error(transpose_error)
  );

  attention_score32_exact_kv_key_stage #(.PRODUCERS(PRODUCERS)) u_stage (
    .clk(clk),
    .rst_n(rst_n),
    .fill_target_valid(fill_target_valid),
    .fill_target_ready(fill_target_ready),
    .fill_target_kv_head(fill_target_kv_head),
    .query_write_valid(query_write_valid),
    .query_write_ready(query_write_ready),
    .query_write_kv_head(query_write_kv_head),
    .query_write_dimension(query_write_dimension),
    .query_write_data(query_write_data),
    .query_write_last(query_write_last),
    .key_write_valid(transposed_key_valid),
    .key_write_ready(transposed_key_ready),
    .key_write_kv_head(transposed_key_head),
    .key_write_producer(transposed_key_producer),
    .key_write_producer_block(transposed_key_producer_block),
    .key_write_dimension(transposed_key_dimension),
    .key_write_data(transposed_key_data),
    .key_write_last(transposed_key_dimension == 7'd127),
    .fill_complete(fill_complete),
    .command_valid(command_valid),
    .command_ready(command_ready),
    .command_kv_head(command_kv_head),
    .producer_valid(producer_valid),
    .producer_ready(producer_ready),
    .producer_last(producer_last),
    .producer_query(producer_query),
    .producer_key(producer_key),
    .command_done(command_done),
    .protocol_error(stage_error)
  );

  wire unexpected_value_fold = ^{
    unexpected_value_stream,
    unexpected_value_head,
    unexpected_value_block,
    unexpected_value_slice,
    unexpected_value_data,
    unexpected_value_last
  };
  wire key_last_mismatch = transposed_key_valid &&
    (transposed_key_last != (transposed_key_dimension == 7'd127));
  assign protocol_error = transpose_error || stage_error || key_last_mismatch ||
    unexpected_value_valid || (unexpected_value_valid && unexpected_value_fold);
endmodule
