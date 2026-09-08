`timescale 1ns/1ps

// Expands one exact K/V gather span into 256-byte, eight-flit packet commands.
// Full K planes are emitted in block-paired stream order. A downstream
// descriptor-pair scheduler installs receive state before transmit release.
module attention_kv_gather_span_packetizer (
  input wire clk,
  input wire rst_n,

  input wire desc_valid,
  output wire desc_ready,
  input wire [4:0] desc_layer,
  input wire [6:0] desc_tile,
  input wire [3:0] desc_segment,
  input wire desc_operation_consume,
  input wire desc_source_hbm,
  input wire [3:0] desc_source_endpoint,
  input wire [3:0] desc_destination_cluster,
  input wire [3:0] desc_plane,
  input wire [19:0] desc_canonical_base_address,
  input wire [33:0] desc_source_byte_address,
  input wire desc_destination_is_resident_cache,
  input wire [33:0] desc_destination_byte_address,
  input wire [20:0] desc_payload_bytes,
  input wire desc_last,

  output wire cmd_valid,
  input wire cmd_ready,
  output wire [4:0] cmd_layer,
  output wire [6:0] cmd_tile,
  output wire [3:0] cmd_segment,
  output wire cmd_operation_consume,
  output wire cmd_source_hbm,
  output wire [3:0] cmd_source_endpoint,
  output wire [3:0] cmd_destination_cluster,
  output wire [3:0] cmd_plane,
  output wire [19:0] cmd_canonical_byte_address,
  output wire [33:0] cmd_source_byte_address,
  output wire cmd_destination_is_resident_cache,
  output wire [33:0] cmd_destination_byte_address,
  output wire [11:0] cmd_packet_index,
  output wire [7:0] cmd_tag,
  output wire [3:0] cmd_flit_count,
  output wire cmd_descriptor_last,
  output wire cmd_schedule_last,

  output reg [13:0] accepted_descriptor_count,
  output reg [24:0] generated_packet_count,
  output reg protocol_error
);
  reg active_q;
  reg [4:0] layer_q;
  reg [6:0] tile_q;
  reg [3:0] segment_q;
  reg operation_consume_q;
  reg source_hbm_q;
  reg [3:0] source_endpoint_q;
  reg [3:0] destination_cluster_q;
  reg [3:0] plane_q;
  reg [19:0] canonical_base_q;
  reg [33:0] source_base_q;
  reg destination_is_resident_q;
  reg [33:0] destination_base_q;
  reg [12:0] packet_count_q;
  reg [11:0] packet_index_q;
  reg schedule_last_q;

  wire descriptor_last_w =
    {1'b0, packet_index_q} + 13'd1 == packet_count_q;
  wire cmd_fire = cmd_valid && cmd_ready;
  wire desc_fire = desc_valid && desc_ready;
  wire [20:0] canonical_end_address =
    {1'b0, desc_canonical_base_address} + desc_payload_bytes;
  wire [34:0] source_end_address =
    {1'b0, desc_source_byte_address} + {14'd0, desc_payload_bytes};
  wire [34:0] destination_end_address =
    {1'b0, desc_destination_byte_address} + {14'd0, desc_payload_bytes};
  wire desc_fields_valid =
    desc_payload_bytes != 0 &&
    desc_payload_bytes[7:0] == 0 &&
    desc_payload_bytes <= 21'h100000 &&
    desc_canonical_base_address[7:0] == 0 &&
    desc_source_byte_address[7:0] == 0 &&
    desc_destination_byte_address[7:0] == 0 &&
    canonical_end_address <= 21'h100000 &&
    source_end_address <= 35'h400000000 &&
    destination_end_address <= 35'h400000000;
  wire key_block_interleave = operation_consume_q && plane_q < 4'd4 &&
    packet_count_q == 13'd512;
  wire [19:0] packet_byte_offset = key_block_interleave ?
    ({3'd0, packet_index_q[2], 16'd0} +
     {4'd0, packet_index_q[8:3], 10'd0} +
     {10'd0, packet_index_q[1:0], 8'd0}) :
    {packet_index_q, 8'd0};

  assign desc_ready = !protocol_error &&
    (!active_q || (cmd_fire && descriptor_last_w));
  assign cmd_valid = active_q && !protocol_error;
  assign cmd_layer = layer_q;
  assign cmd_tile = tile_q;
  assign cmd_segment = segment_q;
  assign cmd_operation_consume = operation_consume_q;
  assign cmd_source_hbm = source_hbm_q;
  assign cmd_source_endpoint = source_endpoint_q;
  assign cmd_destination_cluster = destination_cluster_q;
  assign cmd_plane = plane_q;
  assign cmd_canonical_byte_address =
    canonical_base_q + packet_byte_offset;
  assign cmd_source_byte_address = source_base_q + {14'd0, packet_byte_offset};
  assign cmd_destination_is_resident_cache = destination_is_resident_q;
  assign cmd_destination_byte_address =
    destination_base_q + {14'd0, packet_byte_offset};
  assign cmd_packet_index = packet_index_q;
  assign cmd_tag = packet_index_q[7:0];
  assign cmd_flit_count = 4'd8;
  assign cmd_descriptor_last = descriptor_last_w;
  assign cmd_schedule_last = schedule_last_q && descriptor_last_w;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_q <= 1'b0;
      layer_q <= 5'd0;
      tile_q <= 7'd0;
      segment_q <= 4'd0;
      operation_consume_q <= 1'b0;
      source_hbm_q <= 1'b0;
      source_endpoint_q <= 4'd0;
      destination_cluster_q <= 4'd0;
      plane_q <= 4'd0;
      canonical_base_q <= 20'd0;
      source_base_q <= 34'd0;
      destination_is_resident_q <= 1'b0;
      destination_base_q <= 34'd0;
      packet_count_q <= 13'd0;
      packet_index_q <= 12'd0;
      schedule_last_q <= 1'b0;
      accepted_descriptor_count <= 14'd0;
      generated_packet_count <= 25'd0;
      protocol_error <= 1'b0;
    end else begin
      if (cmd_fire) begin
        generated_packet_count <= generated_packet_count + 1'b1;
        if (descriptor_last_w) begin
          active_q <= 1'b0;
          packet_index_q <= 12'd0;
        end else begin
          packet_index_q <= packet_index_q + 1'b1;
        end
      end

      if (desc_fire) begin
        accepted_descriptor_count <= accepted_descriptor_count + 1'b1;
        if (!desc_fields_valid) begin
          active_q <= 1'b0;
          protocol_error <= 1'b1;
        end else begin
          active_q <= 1'b1;
          layer_q <= desc_layer;
          tile_q <= desc_tile;
          segment_q <= desc_segment;
          operation_consume_q <= desc_operation_consume;
          source_hbm_q <= desc_source_hbm;
          source_endpoint_q <= desc_source_endpoint;
          destination_cluster_q <= desc_destination_cluster;
          plane_q <= desc_plane;
          canonical_base_q <= desc_canonical_base_address;
          source_base_q <= desc_source_byte_address;
          destination_is_resident_q <= desc_destination_is_resident_cache;
          destination_base_q <= desc_destination_byte_address;
          packet_count_q <= {desc_payload_bytes[20:8]};
          packet_index_q <= 12'd0;
          schedule_last_q <= desc_last;
        end
      end
    end
  end
endmodule
