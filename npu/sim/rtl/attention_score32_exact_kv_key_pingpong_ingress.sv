`timescale 1ns/1ps

// Composes automatic-target ping-pong K transposition with the 256-bit-write
// banked K/Q stage.
module attention_score32_exact_kv_key_pingpong_ingress #(
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
  wire key_valid;
  wire key_ready;
  wire [5:0] key_producer;
  wire [1:0] key_kv_head;
  wire key_producer_block;
  wire [5:0] key_dimension_pair;
  wire [255:0] key_data;
  wire key_last;
  wire transpose_error;
  wire stage_error;

  assign protocol_error = transpose_error || stage_error;

  attention_score32_exact_kv_key_pingpong_transpose #(
    .PRODUCERS(PRODUCERS)
  ) u_transpose (
    .clk(clk), .rst_n(rst_n),
    .ingress_valid(ingress_valid), .ingress_ready(ingress_ready),
    .ingress_tile_byte_addr(ingress_tile_byte_addr),
    .ingress_data(ingress_data), .ingress_byte_valid(ingress_byte_valid),
    .key_valid(key_valid), .key_ready(key_ready),
    .key_producer(key_producer), .key_kv_head(key_kv_head),
    .key_producer_block(key_producer_block),
    .key_dimension_pair(key_dimension_pair), .key_data(key_data),
    .key_last(key_last), .protocol_error(transpose_error)
  );

  attention_score32_exact_kv_key_stage_wide #(
    .PRODUCERS(PRODUCERS)
  ) u_stage (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(fill_target_valid), .fill_target_ready(fill_target_ready),
    .fill_target_kv_head(fill_target_kv_head),
    .query_write_valid(query_write_valid), .query_write_ready(query_write_ready),
    .query_write_kv_head(query_write_kv_head),
    .query_write_dimension(query_write_dimension), .query_write_data(query_write_data),
    .query_write_last(query_write_last),
    .key_write_valid(key_valid), .key_write_ready(key_ready),
    .key_write_kv_head(key_kv_head), .key_write_producer(key_producer),
    .key_write_producer_block(key_producer_block),
    .key_write_dimension_pair(key_dimension_pair), .key_write_data(key_data),
    .key_write_last(key_last), .fill_complete(fill_complete),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_kv_head(command_kv_head), .producer_valid(producer_valid),
    .producer_ready(producer_ready), .producer_last(producer_last),
    .producer_query(producer_query), .producer_key(producer_key),
    .command_done(command_done), .protocol_error(stage_error)
  );
endmodule
