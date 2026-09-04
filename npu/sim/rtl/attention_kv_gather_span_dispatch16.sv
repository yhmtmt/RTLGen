`timescale 1ns/1ps

// Routes each exact gather span to the packetizer at its physical injection
// endpoint. Independent sources expand spans concurrently; a busy selected
// source alone backpressures the descriptor scheduler.
module attention_kv_gather_span_dispatch16 (
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

  output wire [15:0] cmd_valid,
  input wire [15:0] cmd_ready,
  output wire [16*5-1:0] cmd_layer,
  output wire [16*7-1:0] cmd_tile,
  output wire [16*4-1:0] cmd_segment,
  output wire [15:0] cmd_operation_consume,
  output wire [15:0] cmd_source_hbm,
  output wire [16*4-1:0] cmd_source_endpoint,
  output wire [16*4-1:0] cmd_destination_cluster,
  output wire [16*4-1:0] cmd_plane,
  output wire [16*20-1:0] cmd_canonical_byte_address,
  output wire [16*34-1:0] cmd_source_byte_address,
  output wire [15:0] cmd_destination_is_resident_cache,
  output wire [16*34-1:0] cmd_destination_byte_address,
  output wire [16*12-1:0] cmd_packet_index,
  output wire [16*8-1:0] cmd_tag,
  output wire [16*4-1:0] cmd_flit_count,
  output wire [15:0] cmd_descriptor_last,
  output wire [15:0] cmd_schedule_last,
  output wire [16*13-1:0] accepted_descriptor_count,
  output wire [16*25-1:0] generated_packet_count,
  output wire [15:0] packetizer_protocol_error
);
  wire [15:0] lane_desc_ready;
  assign desc_ready = lane_desc_ready[desc_source_endpoint];

  genvar lane_g;
  generate
    for (lane_g = 0; lane_g < 16; lane_g = lane_g + 1) begin : gen_lanes
      attention_kv_gather_span_packetizer u_packetizer (
        .clk(clk),
        .rst_n(rst_n),
        .desc_valid(desc_valid && (desc_source_endpoint == lane_g[3:0])),
        .desc_ready(lane_desc_ready[lane_g]),
        .desc_layer(desc_layer),
        .desc_tile(desc_tile),
        .desc_segment(desc_segment),
        .desc_operation_consume(desc_operation_consume),
        .desc_source_hbm(desc_source_hbm),
        .desc_source_endpoint(desc_source_endpoint),
        .desc_destination_cluster(desc_destination_cluster),
        .desc_plane(desc_plane),
        .desc_canonical_base_address(desc_canonical_base_address),
        .desc_source_byte_address(desc_source_byte_address),
        .desc_destination_is_resident_cache(desc_destination_is_resident_cache),
        .desc_destination_byte_address(desc_destination_byte_address),
        .desc_payload_bytes(desc_payload_bytes),
        .desc_last(desc_last),
        .cmd_valid(cmd_valid[lane_g]),
        .cmd_ready(cmd_ready[lane_g]),
        .cmd_layer(cmd_layer[(lane_g*5) +: 5]),
        .cmd_tile(cmd_tile[(lane_g*7) +: 7]),
        .cmd_segment(cmd_segment[(lane_g*4) +: 4]),
        .cmd_operation_consume(cmd_operation_consume[lane_g]),
        .cmd_source_hbm(cmd_source_hbm[lane_g]),
        .cmd_source_endpoint(cmd_source_endpoint[(lane_g*4) +: 4]),
        .cmd_destination_cluster(cmd_destination_cluster[(lane_g*4) +: 4]),
        .cmd_plane(cmd_plane[(lane_g*4) +: 4]),
        .cmd_canonical_byte_address(cmd_canonical_byte_address[(lane_g*20) +: 20]),
        .cmd_source_byte_address(cmd_source_byte_address[(lane_g*34) +: 34]),
        .cmd_destination_is_resident_cache(
          cmd_destination_is_resident_cache[lane_g]
        ),
        .cmd_destination_byte_address(
          cmd_destination_byte_address[(lane_g*34) +: 34]
        ),
        .cmd_packet_index(cmd_packet_index[(lane_g*12) +: 12]),
        .cmd_tag(cmd_tag[(lane_g*8) +: 8]),
        .cmd_flit_count(cmd_flit_count[(lane_g*4) +: 4]),
        .cmd_descriptor_last(cmd_descriptor_last[lane_g]),
        .cmd_schedule_last(cmd_schedule_last[lane_g]),
        .accepted_descriptor_count(
          accepted_descriptor_count[(lane_g*13) +: 13]
        ),
        .generated_packet_count(generated_packet_count[(lane_g*25) +: 25]),
        .protocol_error(packetizer_protocol_error[lane_g])
      );
    end
  endgenerate
endmodule
