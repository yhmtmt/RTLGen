`timescale 1ns/1ps

// Exact transient-capacity K/V gather path from static Llama7B descriptors to
// resident-cache writes and canonical per-cluster ingress flits.
module attention_kv_capacity_gather_mesh_ingress (
  input wire clk,
  input wire rst_n,
  input wire enable,

  output wire [15:0] source_req_valid,
  input wire [15:0] source_req_ready,
  output wire [15:0] source_req_is_hbm,
  output wire [16*33-1:0] source_req_byte_address,
  input wire [15:0] source_rsp_valid,
  output wire [15:0] source_rsp_ready,
  input wire [16*256-1:0] source_rsp_data,

  output wire [15:0] resident_write_valid,
  input wire [15:0] resident_write_ready,
  output wire [16*33-1:0] resident_write_byte_address,
  output wire [16*256-1:0] resident_write_data,

  output wire [15:0] canonical_ingress_valid,
  input wire [15:0] canonical_ingress_ready,
  output wire [16*5-1:0] canonical_ingress_layer,
  output wire [16*7-1:0] canonical_ingress_tile,
  output wire [16*20-1:0] canonical_ingress_tile_byte_address,
  output wire [16*256-1:0] canonical_ingress_data,

  output wire [4:0] active_layer,
  output wire [22:0] refill_flit_count,
  output wire [22:0] consume_flit_count,
  output wire refill_complete,
  output wire consume_complete,
  output wire [5:0] completed_layer_count,
  output wire [12:0] generated_descriptor_count,
  output wire [16*13-1:0] lane_accepted_descriptor_count,
  output wire [16*25-1:0] lane_generated_packet_count,
  output wire [24:0] accepted_packet_command_count,
  output wire [12:0] completed_descriptor_count,
  output wire schedule_packet_submitted,
  output wire [16*4-1:0] active_packet_segment,
  output wire [16*4-1:0] active_packet_plane,
  output wire [15:0] packet_completion_valid,
  output wire [16*4-1:0] packet_completion_source,
  output wire [16*2-1:0] packet_completion_vc,
  output wire [16*8-1:0] packet_completion_tag,
  output wire [16*32-1:0] router_accepted_flit_count,
  output wire [16*32-1:0] router_forwarded_flit_count,
  output wire [16*32-1:0] router_input_stall_cycles,
  output wire [16*32-1:0] router_output_stall_cycles,
  output wire [16*32-1:0] router_contention_cycles,
  output wire [16*32-1:0] router_current_input_occupancy,
  output wire [16*32-1:0] router_max_input_occupancy,
  output wire [16*5*32-1:0] router_route_flit_count,
  output wire done,
  output wire [15:0] endpoint_protocol_error,
  output wire [15:0] packetizer_protocol_error,
  output wire scheduler_protocol_error,
  output wire barrier_protocol_error,
  output wire mesh_command_protocol_error,
  output wire protocol_error
);
  wire scheduler_desc_valid;
  wire scheduler_desc_ready;
  wire [4:0] scheduler_desc_layer;
  wire [6:0] scheduler_desc_tile;
  wire [3:0] scheduler_desc_segment;
  wire scheduler_desc_operation_consume;
  wire scheduler_desc_source_hbm;
  wire [3:0] scheduler_desc_source_endpoint;
  wire [3:0] scheduler_desc_destination_cluster;
  wire [3:0] scheduler_desc_plane;
  wire [19:0] scheduler_desc_canonical_base_address;
  wire [33:0] scheduler_desc_source_byte_address;
  wire scheduler_desc_destination_is_resident_cache;
  wire [33:0] scheduler_desc_destination_byte_address;
  wire [20:0] scheduler_desc_payload_bytes;
  wire scheduler_desc_last;
  wire scheduler_done;

  wire released_desc_valid;
  wire released_desc_ready;
  reg [4:0] accepted_refill_flits_r;
  reg [4:0] accepted_consume_flits_r;

  wire [15:0] cmd_valid;
  wire [15:0] cmd_ready;
  wire [16*5-1:0] cmd_layer;
  wire [16*7-1:0] cmd_tile;
  wire [15:0] cmd_operation_consume;
  wire [15:0] cmd_source_hbm;
  wire [16*4-1:0] cmd_source_endpoint;
  wire [16*4-1:0] cmd_destination_cluster;
  wire [16*20-1:0] cmd_canonical_byte_address;
  wire [16*34-1:0] cmd_source_byte_address;
  wire [15:0] cmd_destination_is_resident_cache;
  wire [16*34-1:0] cmd_destination_byte_address;
  wire [16*12-1:0] cmd_packet_index;
  wire [16*8-1:0] cmd_tag;
  wire [16*4-1:0] cmd_flit_count;
  wire [15:0] cmd_descriptor_last;
  wire [15:0] cmd_schedule_last;
  wire mesh_protocol_error;
  integer count_i;

  assign done = scheduler_done && schedule_packet_submitted && consume_complete;
  assign protocol_error = scheduler_protocol_error | barrier_protocol_error |
    mesh_command_protocol_error | mesh_protocol_error |
    (|packetizer_protocol_error);

  always @(*) begin
    accepted_refill_flits_r = 5'd0;
    accepted_consume_flits_r = 5'd0;
    for (count_i = 0; count_i < 16; count_i = count_i + 1) begin
      if (resident_write_valid[count_i] && resident_write_ready[count_i])
        accepted_refill_flits_r = accepted_refill_flits_r + 1'b1;
      if (canonical_ingress_valid[count_i] && canonical_ingress_ready[count_i])
        accepted_consume_flits_r = accepted_consume_flits_r + 1'b1;
    end
  end

  attention_kv_capacity_gather_scheduler u_scheduler (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .desc_valid(scheduler_desc_valid), .desc_ready(scheduler_desc_ready),
    .desc_layer(scheduler_desc_layer), .desc_tile(scheduler_desc_tile),
    .desc_segment(scheduler_desc_segment),
    .desc_operation_consume(scheduler_desc_operation_consume),
    .desc_source_hbm(scheduler_desc_source_hbm),
    .desc_source_endpoint(scheduler_desc_source_endpoint),
    .desc_destination_cluster(scheduler_desc_destination_cluster),
    .desc_plane(scheduler_desc_plane),
    .desc_canonical_base_address(scheduler_desc_canonical_base_address),
    .desc_source_byte_address(scheduler_desc_source_byte_address),
    .desc_destination_is_resident_cache(
      scheduler_desc_destination_is_resident_cache
    ),
    .desc_destination_byte_address(scheduler_desc_destination_byte_address),
    .desc_payload_bytes(scheduler_desc_payload_bytes), .desc_last(scheduler_desc_last),
    .done(scheduler_done), .generated_descriptor_count(generated_descriptor_count),
    .protocol_error(scheduler_protocol_error)
  );

  attention_kv_gather_layer_barrier u_barrier (
    .clk(clk), .rst_n(rst_n),
    .descriptor_valid(scheduler_desc_valid),
    .descriptor_ready(scheduler_desc_ready),
    .descriptor_layer(scheduler_desc_layer),
    .descriptor_operation_consume(scheduler_desc_operation_consume),
    .released_valid(released_desc_valid), .released_ready(released_desc_ready),
    .accepted_refill_flits(accepted_refill_flits_r),
    .accepted_consume_flits(accepted_consume_flits_r),
    .active_layer(active_layer), .refill_flit_count(refill_flit_count),
    .consume_flit_count(consume_flit_count), .refill_complete(refill_complete),
    .consume_complete(consume_complete), .completed_layer_count(completed_layer_count),
    .protocol_error(barrier_protocol_error)
  );

  attention_kv_gather_span_dispatch16 u_dispatch (
    .clk(clk), .rst_n(rst_n),
    .desc_valid(released_desc_valid), .desc_ready(released_desc_ready),
    .desc_layer(scheduler_desc_layer), .desc_tile(scheduler_desc_tile),
    .desc_segment(scheduler_desc_segment),
    .desc_operation_consume(scheduler_desc_operation_consume),
    .desc_source_hbm(scheduler_desc_source_hbm),
    .desc_source_endpoint(scheduler_desc_source_endpoint),
    .desc_destination_cluster(scheduler_desc_destination_cluster),
    .desc_plane(scheduler_desc_plane),
    .desc_canonical_base_address(scheduler_desc_canonical_base_address),
    .desc_source_byte_address(scheduler_desc_source_byte_address),
    .desc_destination_is_resident_cache(
      scheduler_desc_destination_is_resident_cache
    ),
    .desc_destination_byte_address(scheduler_desc_destination_byte_address),
    .desc_payload_bytes(scheduler_desc_payload_bytes), .desc_last(scheduler_desc_last),
    .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_layer(cmd_layer),
    .cmd_tile(cmd_tile), .cmd_segment(active_packet_segment),
    .cmd_operation_consume(cmd_operation_consume), .cmd_source_hbm(cmd_source_hbm),
    .cmd_source_endpoint(cmd_source_endpoint),
    .cmd_destination_cluster(cmd_destination_cluster),
    .cmd_plane(active_packet_plane),
    .cmd_canonical_byte_address(cmd_canonical_byte_address),
    .cmd_source_byte_address(cmd_source_byte_address),
    .cmd_destination_is_resident_cache(cmd_destination_is_resident_cache),
    .cmd_destination_byte_address(cmd_destination_byte_address),
    .cmd_packet_index(cmd_packet_index), .cmd_tag(cmd_tag),
    .cmd_flit_count(cmd_flit_count), .cmd_descriptor_last(cmd_descriptor_last),
    .cmd_schedule_last(cmd_schedule_last),
    .accepted_descriptor_count(lane_accepted_descriptor_count),
    .generated_packet_count(lane_generated_packet_count),
    .packetizer_protocol_error(packetizer_protocol_error)
  );

  attention_kv_gather_packet_mesh4x4 u_packet_mesh (
    .clk(clk), .rst_n(rst_n), .cmd_valid(cmd_valid), .cmd_ready(cmd_ready),
    .cmd_layer(cmd_layer), .cmd_tile(cmd_tile),
    .cmd_operation_consume(cmd_operation_consume), .cmd_source_hbm(cmd_source_hbm),
    .cmd_source_endpoint(cmd_source_endpoint),
    .cmd_destination_cluster(cmd_destination_cluster),
    .cmd_canonical_byte_address(cmd_canonical_byte_address),
    .cmd_source_byte_address(cmd_source_byte_address),
    .cmd_destination_is_resident_cache(cmd_destination_is_resident_cache),
    .cmd_destination_byte_address(cmd_destination_byte_address),
    .cmd_packet_index(cmd_packet_index), .cmd_tag(cmd_tag),
    .cmd_flit_count(cmd_flit_count), .cmd_descriptor_last(cmd_descriptor_last),
    .cmd_schedule_last(cmd_schedule_last),
    .source_req_valid(source_req_valid), .source_req_ready(source_req_ready),
    .source_req_is_hbm(source_req_is_hbm),
    .source_req_byte_address(source_req_byte_address),
    .source_rsp_valid(source_rsp_valid), .source_rsp_ready(source_rsp_ready),
    .source_rsp_data(source_rsp_data),
    .resident_write_valid(resident_write_valid),
    .resident_write_ready(resident_write_ready),
    .resident_write_byte_address(resident_write_byte_address),
    .resident_write_data(resident_write_data),
    .canonical_ingress_valid(canonical_ingress_valid),
    .canonical_ingress_ready(canonical_ingress_ready),
    .canonical_ingress_layer(canonical_ingress_layer),
    .canonical_ingress_tile(canonical_ingress_tile),
    .canonical_ingress_tile_byte_address(canonical_ingress_tile_byte_address),
    .canonical_ingress_data(canonical_ingress_data),
    .endpoint_protocol_error(endpoint_protocol_error),
    .packet_completion_valid(packet_completion_valid),
    .packet_completion_source(packet_completion_source),
    .packet_completion_vc(packet_completion_vc),
    .packet_completion_tag(packet_completion_tag),
    .router_accepted_flit_count(router_accepted_flit_count),
    .router_forwarded_flit_count(router_forwarded_flit_count),
    .router_input_stall_cycles(router_input_stall_cycles),
    .router_output_stall_cycles(router_output_stall_cycles),
    .router_contention_cycles(router_contention_cycles),
    .router_current_input_occupancy(router_current_input_occupancy),
    .router_max_input_occupancy(router_max_input_occupancy),
    .router_route_flit_count(router_route_flit_count),
    .accepted_packet_command_count(accepted_packet_command_count),
    .completed_descriptor_count(completed_descriptor_count),
    .schedule_packet_submitted(schedule_packet_submitted),
    .command_protocol_error(mesh_command_protocol_error),
    .protocol_error(mesh_protocol_error)
  );
endmodule
