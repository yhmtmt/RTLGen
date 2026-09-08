`timescale 1ns/1ps

// Composes canonical per-cluster mesh ejection with the exact K staging and V
// SRAM-fill ingress paths. The resulting command is admitted atomically by the
// K stage and an external cluster that composes score compute with V residency.
module attention_score32_exact_kv_cluster_ejection_ingress #(
  parameter integer PRODUCERS = 53
) (
  input wire clk,
  input wire rst_n,

  input wire canonical_valid,
  output wire canonical_ready,
  input wire [4:0] canonical_layer,
  input wire [6:0] canonical_tile,
  input wire [19:0] canonical_tile_byte_address,
  input wire [255:0] canonical_data,

  input wire query_write_valid,
  output wire query_write_ready,
  input wire [1:0] query_write_kv_head,
  input wire [6:0] query_write_dimension,
  input wire [63:0] query_write_data,
  input wire query_write_last,

  output wire [PRODUCERS-1:0] producer_valid,
  input wire [PRODUCERS-1:0] producer_ready,
  output wire [PRODUCERS-1:0] producer_last,
  output wire [(PRODUCERS*128)-1:0] producer_query,
  output wire [(PRODUCERS*128)-1:0] producer_key,

  output wire endpoint_fill_target_valid,
  input wire endpoint_fill_target_ready,
  output wire endpoint_fill_target_buffer_sel,
  output wire [15:0] endpoint_fill_target_command_id,
  output wire [4:0] endpoint_fill_target_head_base,
  output wire [2:0] endpoint_fill_target_wave_index,
  output wire endpoint_fill_valid,
  input wire endpoint_fill_ready,
  output wire endpoint_fill_buffer_sel,
  output wire endpoint_fill_stream,
  output wire [5:0] endpoint_fill_block_slot,
  output wire [3:0] endpoint_fill_slice,
  output wire [511:0] endpoint_fill_data,

  output wire cluster_command_valid,
  input wire cluster_command_ready,
  output wire [15:0] command_id,
  output wire [4:0] command_head_base,
  output wire [2:0] command_wave_index,
  output wire [4:0] command_layer,

  output wire key_command_done,
  output wire [12:0] accepted_key_flit_count,
  output wire [12:0] accepted_value_flit_count,
  output wire [10:0] completed_wave_count,
  output wire protocol_error
);
  wire key_fill_target_valid;
  wire key_fill_target_ready;
  wire [1:0] key_fill_target_kv_head;
  wire key_ingress_valid;
  wire key_ingress_ready;
  wire [19:0] key_ingress_tile_byte_address;
  wire [255:0] key_ingress_data;
  wire [31:0] key_ingress_byte_valid;
  wire key_fill_complete;
  wire value_fill_target_valid;
  wire value_fill_target_ready;
  wire value_fill_target_buffer_sel;
  wire [15:0] value_fill_target_command_id;
  wire [4:0] value_fill_target_head_base;
  wire [2:0] value_fill_target_wave_index;
  wire value_block_target_valid;
  wire value_block_target_ready;
  wire [1:0] value_block_target_kv_head;
  wire value_block_target_stream;
  wire [5:0] value_block_target_slot;
  wire value_ingress_valid;
  wire value_ingress_ready;
  wire [19:0] value_ingress_tile_byte_address;
  wire [255:0] value_ingress_data;
  wire [31:0] value_ingress_byte_valid;
  wire value_fill_complete;
  wire value_fill_active;
  wire [7:0] value_completed_block_count;
  wire control_command_valid;
  wire control_command_ready;
  wire key_command_ready;
  wire key_protocol_error;
  wire value_protocol_error;
  wire control_protocol_error;

  assign control_command_ready = key_command_ready && cluster_command_ready;
  assign cluster_command_valid = control_command_valid && key_command_ready;
  wire key_command_valid = control_command_valid && cluster_command_ready;
  assign protocol_error = control_protocol_error || key_protocol_error ||
    value_protocol_error;

  attention_score32_exact_kv_cluster_ejection_control u_control (
    .clk(clk), .rst_n(rst_n),
    .canonical_valid(canonical_valid), .canonical_ready(canonical_ready),
    .canonical_layer(canonical_layer), .canonical_tile(canonical_tile),
    .canonical_tile_byte_address(canonical_tile_byte_address),
    .canonical_data(canonical_data),
    .key_fill_target_valid(key_fill_target_valid),
    .key_fill_target_ready(key_fill_target_ready),
    .key_fill_target_kv_head(key_fill_target_kv_head),
    .key_ingress_valid(key_ingress_valid), .key_ingress_ready(key_ingress_ready),
    .key_ingress_tile_byte_address(key_ingress_tile_byte_address),
    .key_ingress_data(key_ingress_data),
    .key_ingress_byte_valid(key_ingress_byte_valid),
    .key_fill_complete(key_fill_complete),
    .value_fill_target_valid(value_fill_target_valid),
    .value_fill_target_ready(value_fill_target_ready),
    .value_fill_target_buffer_sel(value_fill_target_buffer_sel),
    .value_fill_target_command_id(value_fill_target_command_id),
    .value_fill_target_head_base(value_fill_target_head_base),
    .value_fill_target_wave_index(value_fill_target_wave_index),
    .value_block_target_valid(value_block_target_valid),
    .value_block_target_ready(value_block_target_ready),
    .value_block_target_kv_head(value_block_target_kv_head),
    .value_block_target_stream(value_block_target_stream),
    .value_block_target_slot(value_block_target_slot),
    .value_ingress_valid(value_ingress_valid),
    .value_ingress_ready(value_ingress_ready),
    .value_ingress_tile_byte_address(value_ingress_tile_byte_address),
    .value_ingress_data(value_ingress_data),
    .value_ingress_byte_valid(value_ingress_byte_valid),
    .value_fill_complete(value_fill_complete),
    .command_valid(control_command_valid), .command_ready(control_command_ready),
    .command_id(command_id), .command_head_base(command_head_base),
    .command_wave_index(command_wave_index), .command_layer(command_layer),
    .accepted_key_flit_count(accepted_key_flit_count),
    .accepted_value_flit_count(accepted_value_flit_count),
    .completed_wave_count(completed_wave_count),
    .protocol_error(control_protocol_error)
  );

  attention_score32_exact_kv_key_pingpong_ingress #(
    .PRODUCERS(PRODUCERS)
  ) u_key_ingress (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(key_fill_target_valid),
    .fill_target_ready(key_fill_target_ready),
    .fill_target_kv_head(key_fill_target_kv_head),
    .query_write_valid(query_write_valid), .query_write_ready(query_write_ready),
    .query_write_kv_head(query_write_kv_head),
    .query_write_dimension(query_write_dimension),
    .query_write_data(query_write_data), .query_write_last(query_write_last),
    .ingress_valid(key_ingress_valid), .ingress_ready(key_ingress_ready),
    .ingress_tile_byte_addr(key_ingress_tile_byte_address),
    .ingress_data(key_ingress_data), .ingress_byte_valid(key_ingress_byte_valid),
    .fill_complete(key_fill_complete), .command_valid(key_command_valid),
    .command_ready(key_command_ready),
    .command_kv_head(command_head_base[4:3]),
    .producer_valid(producer_valid), .producer_ready(producer_ready),
    .producer_last(producer_last), .producer_query(producer_query),
    .producer_key(producer_key), .command_done(key_command_done),
    .protocol_error(key_protocol_error)
  );

  attention_score32_exact_kv_value_ingress #(
    .PRODUCERS(PRODUCERS)
  ) u_value_ingress (
    .clk(clk), .rst_n(rst_n),
    .fill_target_valid(value_fill_target_valid),
    .fill_target_ready(value_fill_target_ready),
    .fill_target_buffer_sel(value_fill_target_buffer_sel),
    .fill_target_command_id(value_fill_target_command_id),
    .fill_target_head_base(value_fill_target_head_base),
    .fill_target_wave_index(value_fill_target_wave_index),
    .endpoint_fill_target_valid(endpoint_fill_target_valid),
    .endpoint_fill_target_ready(endpoint_fill_target_ready),
    .endpoint_fill_target_buffer_sel(endpoint_fill_target_buffer_sel),
    .endpoint_fill_target_command_id(endpoint_fill_target_command_id),
    .endpoint_fill_target_head_base(endpoint_fill_target_head_base),
    .endpoint_fill_target_wave_index(endpoint_fill_target_wave_index),
    .block_target_valid(value_block_target_valid),
    .block_target_ready(value_block_target_ready),
    .block_target_kv_head(value_block_target_kv_head),
    .block_target_stream(value_block_target_stream),
    .block_target_slot(value_block_target_slot),
    .ingress_valid(value_ingress_valid), .ingress_ready(value_ingress_ready),
    .ingress_tile_byte_addr(value_ingress_tile_byte_address),
    .ingress_data(value_ingress_data),
    .ingress_byte_valid(value_ingress_byte_valid),
    .endpoint_fill_valid(endpoint_fill_valid),
    .endpoint_fill_ready(endpoint_fill_ready),
    .endpoint_fill_buffer_sel(endpoint_fill_buffer_sel),
    .endpoint_fill_stream(endpoint_fill_stream),
    .endpoint_fill_block_slot(endpoint_fill_block_slot),
    .endpoint_fill_slice(endpoint_fill_slice),
    .endpoint_fill_data(endpoint_fill_data),
    .fill_complete(value_fill_complete), .fill_active(value_fill_active),
    .completed_block_count(value_completed_block_count),
    .protocol_error(value_protocol_error)
  );
endmodule
