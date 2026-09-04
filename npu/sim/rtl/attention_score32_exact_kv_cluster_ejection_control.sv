`timescale 1ns/1ps

// Converts one ordered canonical mesh ejection stream into target and payload
// handshakes for the exact K and V ingress paths. One K plane followed by the
// matching V plane constitutes a cluster wave.
module attention_score32_exact_kv_cluster_ejection_control (
  input wire clk,
  input wire rst_n,

  input wire canonical_valid,
  output reg canonical_ready,
  input wire [4:0] canonical_layer,
  input wire [6:0] canonical_tile,
  input wire [19:0] canonical_tile_byte_address,
  input wire [255:0] canonical_data,

  output reg key_fill_target_valid,
  input wire key_fill_target_ready,
  output wire [1:0] key_fill_target_kv_head,
  output reg key_ingress_valid,
  input wire key_ingress_ready,
  output wire [19:0] key_ingress_tile_byte_address,
  output wire [255:0] key_ingress_data,
  output wire [31:0] key_ingress_byte_valid,
  input wire key_fill_complete,

  output reg value_fill_target_valid,
  input wire value_fill_target_ready,
  output wire value_fill_target_buffer_sel,
  output wire [15:0] value_fill_target_command_id,
  output wire [4:0] value_fill_target_head_base,
  output wire [2:0] value_fill_target_wave_index,
  output reg value_block_target_valid,
  input wire value_block_target_ready,
  output wire [1:0] value_block_target_kv_head,
  output wire value_block_target_stream,
  output wire [5:0] value_block_target_slot,
  output reg value_ingress_valid,
  input wire value_ingress_ready,
  output wire [19:0] value_ingress_tile_byte_address,
  output wire [255:0] value_ingress_data,
  output wire [31:0] value_ingress_byte_valid,
  input wire value_fill_complete,

  output wire command_valid,
  input wire command_ready,
  output wire [15:0] command_id,
  output wire [4:0] command_head_base,
  output wire [2:0] command_wave_index,
  output wire [4:0] command_layer,

  output reg [12:0] accepted_key_flit_count,
  output reg [12:0] accepted_value_flit_count,
  output reg [10:0] completed_wave_count,
  output reg protocol_error
);
  localparam [2:0] STATE_KEY_TARGET = 3'd0;
  localparam [2:0] STATE_KEY_DATA = 3'd1;
  localparam [2:0] STATE_VALUE_TARGET = 3'd2;
  localparam [2:0] STATE_VALUE_BLOCK_TARGET = 3'd3;
  localparam [2:0] STATE_VALUE_DATA = 3'd4;
  localparam [2:0] STATE_WAIT_COMPLETE = 3'd5;
  localparam [2:0] STATE_COMMAND = 3'd6;
  localparam [12:0] PLANE_FLITS = 13'd4096;

  reg [2:0] state_q;
  reg [4:0] active_layer_q;
  reg [6:0] active_tile_q;
  reg [1:0] active_head_q;
  reg [2:0] active_wave_q;
  reg [12:0] plane_flit_index_q;
  reg key_complete_q;
  reg value_complete_q;

  wire decoded_is_value = canonical_tile_byte_address[19];
  wire [1:0] decoded_head = canonical_tile_byte_address[18:17];
  wire decoded_stream = canonical_tile_byte_address[16];
  wire [5:0] decoded_block_slot = canonical_tile_byte_address[15:10];
  wire [2:0] decoded_wave = canonical_tile[6:4];
  wire [19:0] key_plane_base = {1'b0, active_head_q, 17'd0};
  wire [19:0] value_plane_base = {1'b1, active_head_q, 17'd0};
  wire [19:0] expected_key_address = key_plane_base +
    {2'd0, plane_flit_index_q[11:6], 10'd0} +
    {3'd0, plane_flit_index_q[5], 16'd0} +
    {10'd0, plane_flit_index_q[4:0], 5'd0};
  wire [19:0] expected_value_address = value_plane_base +
    {2'd0, plane_flit_index_q, 5'd0};
  wire tuple_matches = canonical_layer == active_layer_q &&
    canonical_tile == active_tile_q && decoded_head == active_head_q;
  wire key_first_valid = !decoded_is_value &&
    canonical_tile_byte_address[16:0] == 17'd0;
  wire value_first_valid = decoded_is_value && tuple_matches &&
    canonical_tile_byte_address[16:0] == 17'd0;
  wire key_payload_valid = !decoded_is_value && tuple_matches &&
    canonical_tile_byte_address == expected_key_address;
  wire value_payload_valid = decoded_is_value && tuple_matches &&
    canonical_tile_byte_address == expected_value_address;

  function automatic [15:0] logical_command_id;
    input [4:0] layer;
    input [1:0] head;
    begin
      logical_command_id = 16'h8200 + {9'd0, layer, head};
    end
  endfunction

  assign key_fill_target_kv_head = state_q == STATE_KEY_TARGET ?
    decoded_head : active_head_q;
  assign key_ingress_tile_byte_address = canonical_tile_byte_address;
  assign key_ingress_data = canonical_data;
  assign key_ingress_byte_valid = 32'hffff_ffff;

  assign value_fill_target_buffer_sel = active_wave_q[0];
  assign value_fill_target_command_id = logical_command_id(
    active_layer_q, active_head_q
  );
  assign value_fill_target_head_base = {active_head_q, 3'd0};
  assign value_fill_target_wave_index = active_wave_q;
  assign value_block_target_kv_head = active_head_q;
  assign value_block_target_stream = decoded_stream;
  assign value_block_target_slot = decoded_block_slot;
  assign value_ingress_tile_byte_address = canonical_tile_byte_address;
  assign value_ingress_data = canonical_data;
  assign value_ingress_byte_valid = 32'hffff_ffff;

  assign command_valid = state_q == STATE_COMMAND;
  assign command_id = logical_command_id(active_layer_q, active_head_q);
  assign command_head_base = {active_head_q, 3'd0};
  assign command_wave_index = active_wave_q;
  assign command_layer = active_layer_q;

  wire key_target_fire = key_fill_target_valid && key_fill_target_ready;
  wire key_ingress_fire = key_ingress_valid && key_ingress_ready;
  wire value_target_fire = value_fill_target_valid && value_fill_target_ready;
  wire value_block_target_fire = value_block_target_valid && value_block_target_ready;
  wire value_ingress_fire = value_ingress_valid && value_ingress_ready;
  wire command_fire = command_valid && command_ready;

  always @(*) begin
    canonical_ready = 1'b0;
    key_fill_target_valid = 1'b0;
    key_ingress_valid = 1'b0;
    value_fill_target_valid = 1'b0;
    value_block_target_valid = 1'b0;
    value_ingress_valid = 1'b0;
    case (state_q)
      STATE_KEY_TARGET: begin
        key_fill_target_valid = canonical_valid && key_first_valid;
      end
      STATE_KEY_DATA: begin
        canonical_ready = key_ingress_ready;
        key_ingress_valid = canonical_valid;
      end
      STATE_VALUE_TARGET: begin
        value_fill_target_valid = canonical_valid && value_first_valid;
      end
      STATE_VALUE_BLOCK_TARGET: begin
        value_block_target_valid = canonical_valid && value_payload_valid;
      end
      STATE_VALUE_DATA: begin
        canonical_ready = value_ingress_ready;
        value_ingress_valid = canonical_valid;
      end
      default: begin
      end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= STATE_KEY_TARGET;
      active_layer_q <= 5'd0;
      active_tile_q <= 7'd0;
      active_head_q <= 2'd0;
      active_wave_q <= 3'd0;
      plane_flit_index_q <= 13'd0;
      key_complete_q <= 1'b0;
      value_complete_q <= 1'b0;
      accepted_key_flit_count <= 13'd0;
      accepted_value_flit_count <= 13'd0;
      completed_wave_count <= 11'd0;
      protocol_error <= 1'b0;
    end else begin
      if (key_fill_complete)
        key_complete_q <= 1'b1;
      if (value_fill_complete)
        value_complete_q <= 1'b1;

      if (canonical_valid && state_q == STATE_KEY_TARGET && !key_first_valid)
        protocol_error <= 1'b1;
      if (canonical_valid && state_q == STATE_VALUE_TARGET && !value_first_valid)
        protocol_error <= 1'b1;
      if (canonical_valid && state_q == STATE_VALUE_BLOCK_TARGET &&
          !value_payload_valid)
        protocol_error <= 1'b1;

      if (key_target_fire) begin
        active_layer_q <= canonical_layer;
        active_tile_q <= canonical_tile;
        active_head_q <= decoded_head;
        active_wave_q <= decoded_wave;
        plane_flit_index_q <= 13'd0;
        key_complete_q <= 1'b0;
        value_complete_q <= 1'b0;
        accepted_key_flit_count <= 13'd0;
        accepted_value_flit_count <= 13'd0;
        state_q <= STATE_KEY_DATA;
      end

      if (key_ingress_fire) begin
        if (!key_payload_valid)
          protocol_error <= 1'b1;
        accepted_key_flit_count <= accepted_key_flit_count + 1'b1;
        if (plane_flit_index_q == PLANE_FLITS - 1'b1) begin
          plane_flit_index_q <= 13'd0;
          state_q <= STATE_VALUE_TARGET;
        end else begin
          plane_flit_index_q <= plane_flit_index_q + 1'b1;
        end
      end

      if (value_target_fire) begin
        plane_flit_index_q <= 13'd0;
        state_q <= STATE_VALUE_BLOCK_TARGET;
      end

      if (value_block_target_fire)
        state_q <= STATE_VALUE_DATA;

      if (value_ingress_fire) begin
        if (!value_payload_valid)
          protocol_error <= 1'b1;
        accepted_value_flit_count <= accepted_value_flit_count + 1'b1;
        if (plane_flit_index_q == PLANE_FLITS - 1'b1) begin
          plane_flit_index_q <= 13'd0;
          state_q <= STATE_WAIT_COMPLETE;
        end else begin
          plane_flit_index_q <= plane_flit_index_q + 1'b1;
          if (plane_flit_index_q[4:0] == 5'd31)
            state_q <= STATE_VALUE_BLOCK_TARGET;
        end
      end

      if (state_q == STATE_WAIT_COMPLETE &&
          (key_complete_q || key_fill_complete) &&
          (value_complete_q || value_fill_complete))
        state_q <= STATE_COMMAND;

      if (command_fire) begin
        completed_wave_count <= completed_wave_count + 1'b1;
        state_q <= STATE_KEY_TARGET;
      end

      if ((key_fill_complete && state_q == STATE_KEY_TARGET) ||
          (value_fill_complete && state_q < STATE_VALUE_TARGET))
        protocol_error <= 1'b1;
    end
  end
endmodule
