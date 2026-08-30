`timescale 1ns/1ps

// Exact VC0 shared-SRAM service and VC1 stats-once reducer sharing one mesh.
// Producer data, SRAM service, and root-consumer readiness remain explicit at
// this boundary; no traffic generator or schedule approximation is internal.
module attention_score32_exact_dual_producer_shared_mesh4x4 #(
  parameter integer VC0_ADDR_W = 32,
  parameter integer VC0_MAX_PACKETS_PER_CONTEXT = 68,
  parameter integer VC0_PACKET_INDEX_W = 7,
  parameter integer TAG_W = 8,
  parameter integer VC0_TX_DESC_DEPTH = 8,
  parameter integer VC1_BEAT_W = 419,
  parameter integer VC1_PHYSICAL_BANKS = 15,
  parameter integer VC1_USE_FAKERAM = 0,
  parameter integer MESH_FIFO_DEPTH = 4,
  parameter integer ENABLE_DEBUG_COUNTERS = 1
) (
  input wire clk,
  input wire rst_n,

  input wire vc0_layer_start,
  input wire vc0_layer_idle,
  input wire [7:0] vc0_layer_expected_remote_contexts,
  input wire [15:0] vc0_event_valid,
  output wire [15:0] vc0_event_ready,
  input wire [16*3-1:0] vc0_event_wave,
  input wire [16*4-1:0] vc0_event_source,
  input wire [16*VC0_ADDR_W-1:0] vc0_event_source_base_addr,
  input wire [16*VC0_ADDR_W-1:0] vc0_event_destination_base_addr,
  input wire [16*(VC0_PACKET_INDEX_W+1)-1:0] vc0_event_packet_count,
  input wire vc0_completion_ready,
  output wire vc0_completion_valid,
  output wire [2:0] vc0_completion_wave,
  output wire [3:0] vc0_completion_destination,
  output wire [15:0] vc0_tx_mem_req_valid,
  input wire [15:0] vc0_tx_mem_req_ready,
  output wire [16*VC0_ADDR_W-1:0] vc0_tx_mem_req_addr,
  input wire [15:0] vc0_tx_mem_rsp_valid,
  output wire [15:0] vc0_tx_mem_rsp_ready,
  input wire [16*256-1:0] vc0_tx_mem_rsp_data,
  output wire [15:0] vc0_rx_mem_write_valid,
  input wire [15:0] vc0_rx_mem_write_ready,
  output wire [16*VC0_ADDR_W-1:0] vc0_rx_mem_write_addr,
  output wire [16*256-1:0] vc0_rx_mem_write_data,
  output wire vc0_context_valid,
  output wire vc0_context_ready,
  output wire [2:0] vc0_context_wave,
  output wire [3:0] vc0_context_destination,
  output wire [3:0] vc0_context_source,
  output wire [VC0_ADDR_W-1:0] vc0_context_source_base_addr,
  output wire [VC0_ADDR_W-1:0] vc0_context_destination_base_addr,
  output wire [VC0_PACKET_INDEX_W:0] vc0_context_packet_count,
  output wire vc0_admission_complete,
  output wire vc0_transport_complete,
  output wire [7:0] vc0_admitted_count,
  output wire [7:0] vc0_completed_count,
  output wire [15:0] vc0_endpoint_protocol_error,
  output wire vc0_protocol_error,

  input wire [14:0] vc1_source_beat_valid,
  output wire [14:0] vc1_source_beat_ready,
  input wire [15*VC1_BEAT_W-1:0] vc1_source_beat_data,
  input wire vc1_root_local_beat_valid,
  output wire vc1_root_local_beat_ready,
  input wire [VC1_BEAT_W-1:0] vc1_root_local_beat_data,
  input wire [14:0] vc1_remote_group_ready,
  input wire vc1_root_local_group_ready,
  input wire vc1_admission_enable,
  input wire [15:0] vc1_base_command_id,
  output wire vc1_group_admission_pulse,
  output wire [1:0] vc1_group_index,
  output wire [4:0] vc1_head_base,
  output wire [2:0] vc1_group_epoch,
  output wire [14:0] vc1_source_producer_accept,
  output wire vc1_root_producer_accept,
  output wire [14:0] vc1_source_ctx_valid,
  output wire vc1_root_ctx_valid,
  output wire [2:0] vc1_admitted_group_count,
  output wire vc1_done,
  output wire vc1_root_valid,
  input wire vc1_root_ready,
  output wire [15:0] vc1_root_command_id,
  output wire [4:0] vc1_root_head_id,
  output wire [3:0] vc1_root_slice,
  output wire vc1_root_last,
  output wire [319:0] vc1_root_value,
  output wire [14:0] vc1_group_complete,
  output wire [14:0] vc1_descriptor_installed,
  output wire [14:0] vc1_source_protocol_error,
  output wire vc1_tree_protocol_error,
  output wire vc1_protocol_error,
  output wire [15*32-1:0] vc1_source_tx_descriptor_counts,
  output wire [31:0] vc1_source_tx_descriptor_count,
  output wire [31:0] vc1_root_accepted_flit_count,
  output wire [31:0] vc1_root_descriptor_install_count,
  output wire [31:0] vc1_root_completion_count,
  output wire [31:0] vc1_root_replay_packet_count,
  output wire [5:0] vc1_max_occupied_slots,
  output wire [16*32-1:0] shared_router_accepted_flit_counts,
  output wire [31:0] shared_accepted_flit_count,
  output wire [31:0] shared_contention_cycles,
  output wire [31:0] shared_input_stall_cycles,
  output wire [31:0] shared_output_stall_cycles,
  output wire [16*32-1:0] shared_router_forwarded_flit_counts,
  output wire [16*32-1:0] shared_router_current_input_occupancy,
  output wire [16*32-1:0] shared_router_max_input_occupancy,
  output wire [16*5*32-1:0] shared_router_route_flit_counts,
  output wire [15:0] shared_injection_protocol_error,
  output wire [15:0] shared_ejection_protocol_error,
  output wire shared_transport_protocol_error,
  output wire protocol_error
);
  wire [15:0] vc0_transport_in_valid_w;
  wire [15:0] vc0_transport_in_ready_w;
  wire [16*4-1:0] vc0_transport_in_destination_w;
  wire [16*4-1:0] vc0_transport_in_source_w;
  wire [16*TAG_W-1:0] vc0_transport_in_tag_w;
  wire [16*3-1:0] vc0_transport_in_fragment_w;
  wire [15:0] vc0_transport_in_last_w;
  wire [16*2-1:0] vc0_transport_in_vc_w;
  wire [16*256-1:0] vc0_transport_in_data_w;
  wire [15:0] vc0_transport_out_valid_w;
  wire [15:0] vc0_transport_out_ready_w;
  wire [16*4-1:0] vc0_transport_out_destination_w;
  wire [16*4-1:0] vc0_transport_out_source_w;
  wire [16*TAG_W-1:0] vc0_transport_out_tag_w;
  wire [16*3-1:0] vc0_transport_out_fragment_w;
  wire [15:0] vc0_transport_out_last_w;
  wire [16*2-1:0] vc0_transport_out_vc_w;
  wire [16*256-1:0] vc0_transport_out_data_w;

  wire [15:0] vc1_transport_in_valid_w;
  wire [15:0] vc1_transport_in_ready_w;
  wire [16*4-1:0] vc1_transport_in_destination_w;
  wire [16*4-1:0] vc1_transport_in_source_w;
  wire [16*TAG_W-1:0] vc1_transport_in_tag_w;
  wire [16*3-1:0] vc1_transport_in_fragment_w;
  wire [15:0] vc1_transport_in_last_w;
  wire [16*2-1:0] vc1_transport_in_vc_w;
  wire [16*256-1:0] vc1_transport_in_data_w;
  wire [15:0] vc1_transport_out_valid_w;
  wire [15:0] vc1_transport_out_ready_w;
  wire [16*4-1:0] vc1_transport_out_destination_w;
  wire [16*4-1:0] vc1_transport_out_source_w;
  wire [16*TAG_W-1:0] vc1_transport_out_tag_w;
  wire [16*3-1:0] vc1_transport_out_fragment_w;
  wire [15:0] vc1_transport_out_last_w;
  wire [16*2-1:0] vc1_transport_out_vc_w;
  wire [16*256-1:0] vc1_transport_out_data_w;
  wire [16*32-1:0] shared_router_accepted_flit_counts_w;
  wire [16*32-1:0] shared_router_input_stall_counts_w;
  wire [16*32-1:0] shared_router_output_stall_counts_w;
  wire [16*32-1:0] shared_router_contention_counts_w;

  attention_shared_stream_context_service #(
    .ADDR_W(VC0_ADDR_W),
    .MAX_PACKETS_PER_CONTEXT(VC0_MAX_PACKETS_PER_CONTEXT),
    .PACKET_INDEX_W(VC0_PACKET_INDEX_W),
    .TAG_W(TAG_W),
    .TX_DESC_DEPTH(VC0_TX_DESC_DEPTH),
    .INTERNAL_MESH(0)
  ) vc0_service (
    .clk(clk), .rst_n(rst_n),
    .layer_start(vc0_layer_start), .layer_idle(vc0_layer_idle),
    .layer_expected_remote_contexts(vc0_layer_expected_remote_contexts),
    .event_valid(vc0_event_valid), .event_ready(vc0_event_ready),
    .event_wave(vc0_event_wave), .event_source(vc0_event_source),
    .event_source_base_addr(vc0_event_source_base_addr),
    .event_destination_base_addr(vc0_event_destination_base_addr),
    .event_packet_count(vc0_event_packet_count),
    .completion_ready(vc0_completion_ready),
    .completion_valid(vc0_completion_valid),
    .completion_wave(vc0_completion_wave),
    .completion_destination(vc0_completion_destination),
    .tx_mem_req_valid(vc0_tx_mem_req_valid),
    .tx_mem_req_ready(vc0_tx_mem_req_ready),
    .tx_mem_req_addr(vc0_tx_mem_req_addr),
    .tx_mem_rsp_valid(vc0_tx_mem_rsp_valid),
    .tx_mem_rsp_ready(vc0_tx_mem_rsp_ready),
    .tx_mem_rsp_data(vc0_tx_mem_rsp_data),
    .rx_mem_write_valid(vc0_rx_mem_write_valid),
    .rx_mem_write_ready(vc0_rx_mem_write_ready),
    .rx_mem_write_addr(vc0_rx_mem_write_addr),
    .rx_mem_write_data(vc0_rx_mem_write_data),
    .context_valid(vc0_context_valid), .context_ready(vc0_context_ready),
    .context_wave(vc0_context_wave),
    .context_destination(vc0_context_destination),
    .context_source(vc0_context_source),
    .context_source_base_addr(vc0_context_source_base_addr),
    .context_destination_base_addr(vc0_context_destination_base_addr),
    .context_packet_count(vc0_context_packet_count),
    .admission_complete(vc0_admission_complete),
    .transport_complete(vc0_transport_complete),
    .admitted_count(vc0_admitted_count), .completed_count(vc0_completed_count),
    .endpoint_protocol_error(vc0_endpoint_protocol_error),
    .protocol_error(vc0_protocol_error),
    .transport_endpoint_in_valid(vc0_transport_in_valid_w),
    .transport_endpoint_in_ready(vc0_transport_in_ready_w),
    .transport_endpoint_in_destination(vc0_transport_in_destination_w),
    .transport_endpoint_in_source(vc0_transport_in_source_w),
    .transport_endpoint_in_tag(vc0_transport_in_tag_w),
    .transport_endpoint_in_fragment(vc0_transport_in_fragment_w),
    .transport_endpoint_in_last(vc0_transport_in_last_w),
    .transport_endpoint_in_vc(vc0_transport_in_vc_w),
    .transport_endpoint_in_data(vc0_transport_in_data_w),
    .transport_endpoint_out_valid(vc0_transport_out_valid_w),
    .transport_endpoint_out_ready(vc0_transport_out_ready_w),
    .transport_endpoint_out_destination(vc0_transport_out_destination_w),
    .transport_endpoint_out_source(vc0_transport_out_source_w),
    .transport_endpoint_out_tag(vc0_transport_out_tag_w),
    .transport_endpoint_out_fragment(vc0_transport_out_fragment_w),
    .transport_endpoint_out_last(vc0_transport_out_last_w),
    .transport_endpoint_out_vc(vc0_transport_out_vc_w),
    .transport_endpoint_out_data(vc0_transport_out_data_w)
  );

  local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper #(
    .BEAT_W(VC1_BEAT_W),
    .PHYSICAL_BANKS(VC1_PHYSICAL_BANKS),
    .USE_FAKERAM(VC1_USE_FAKERAM),
    .INTERNAL_MESH(0)
  ) vc1_reducer (
    .clk(clk), .rst_n(rst_n),
    .source_beat_valid(vc1_source_beat_valid),
    .source_beat_ready(vc1_source_beat_ready),
    .source_beat_data(vc1_source_beat_data),
    .root_local_beat_valid(vc1_root_local_beat_valid),
    .root_local_beat_ready(vc1_root_local_beat_ready),
    .root_local_beat_data(vc1_root_local_beat_data),
    .remote_group_ready(vc1_remote_group_ready),
    .root_local_group_ready(vc1_root_local_group_ready),
    .admission_enable(vc1_admission_enable),
    .base_command_id(vc1_base_command_id),
    .group_admission_pulse(vc1_group_admission_pulse),
    .group_index(vc1_group_index), .head_base(vc1_head_base),
    .group_epoch(vc1_group_epoch),
    .source_producer_accept(vc1_source_producer_accept),
    .root_producer_accept(vc1_root_producer_accept),
    .source_ctx_valid(vc1_source_ctx_valid), .root_ctx_valid(vc1_root_ctx_valid),
    .admitted_group_count(vc1_admitted_group_count), .done(vc1_done),
    .root_valid(vc1_root_valid), .root_ready(vc1_root_ready),
    .root_command_id(vc1_root_command_id), .root_head_id(vc1_root_head_id),
    .root_slice(vc1_root_slice), .root_last(vc1_root_last),
    .root_value(vc1_root_value), .group_complete(vc1_group_complete),
    .descriptor_installed(vc1_descriptor_installed),
    .source_protocol_error(vc1_source_protocol_error),
    .tree_protocol_error(vc1_tree_protocol_error),
    .protocol_error(vc1_protocol_error),
    .source_tx_descriptor_counts(vc1_source_tx_descriptor_counts),
    .source_tx_descriptor_count(vc1_source_tx_descriptor_count),
    .root_accepted_flit_count(vc1_root_accepted_flit_count),
    .root_descriptor_install_count(vc1_root_descriptor_install_count),
    .root_completion_count(vc1_root_completion_count),
    .root_replay_packet_count(vc1_root_replay_packet_count),
    .max_occupied_slots(vc1_max_occupied_slots),
    .mesh_router_accepted_flit_counts(shared_router_accepted_flit_counts),
    .mesh_accepted_flit_count(shared_accepted_flit_count),
    .mesh_contention_cycles(shared_contention_cycles),
    .mesh_input_stall_cycles(shared_input_stall_cycles),
    .mesh_output_stall_cycles(shared_output_stall_cycles),
    .transport_endpoint_in_valid(vc1_transport_in_valid_w),
    .transport_endpoint_in_ready(vc1_transport_in_ready_w),
    .transport_endpoint_in_destination(vc1_transport_in_destination_w),
    .transport_endpoint_in_source(vc1_transport_in_source_w),
    .transport_endpoint_in_tag(vc1_transport_in_tag_w),
    .transport_endpoint_in_fragment(vc1_transport_in_fragment_w),
    .transport_endpoint_in_last(vc1_transport_in_last_w),
    .transport_endpoint_in_vc(vc1_transport_in_vc_w),
    .transport_endpoint_in_data(vc1_transport_in_data_w),
    .transport_endpoint_out_valid(vc1_transport_out_valid_w),
    .transport_endpoint_out_ready(vc1_transport_out_ready_w),
    .transport_endpoint_out_destination(vc1_transport_out_destination_w),
    .transport_endpoint_out_source(vc1_transport_out_source_w),
    .transport_endpoint_out_tag(vc1_transport_out_tag_w),
    .transport_endpoint_out_fragment(vc1_transport_out_fragment_w),
    .transport_endpoint_out_last(vc1_transport_out_last_w),
    .transport_endpoint_out_vc(vc1_transport_out_vc_w),
    .transport_endpoint_out_data(vc1_transport_out_data_w),
    .transport_router_accepted_flit_counts(shared_router_accepted_flit_counts_w),
    .transport_router_input_stall_counts(shared_router_input_stall_counts_w),
    .transport_router_output_stall_counts(shared_router_output_stall_counts_w),
    .transport_router_contention_counts(shared_router_contention_counts_w)
  );

  noc_shared_vc_dual_producer_transport4x4 #(
    .TAG_W(TAG_W), .FIFO_DEPTH(MESH_FIFO_DEPTH),
    .ENABLE_DEBUG_COUNTERS(ENABLE_DEBUG_COUNTERS)
  ) shared_transport (
    .clk(clk), .rst_n(rst_n),
    .producer0_in_valid(vc0_transport_in_valid_w),
    .producer0_in_ready(vc0_transport_in_ready_w),
    .producer0_in_destination(vc0_transport_in_destination_w),
    .producer0_in_source(vc0_transport_in_source_w),
    .producer0_in_tag(vc0_transport_in_tag_w),
    .producer0_in_fragment(vc0_transport_in_fragment_w),
    .producer0_in_last(vc0_transport_in_last_w),
    .producer0_in_vc(vc0_transport_in_vc_w),
    .producer0_in_data(vc0_transport_in_data_w),
    .producer1_in_valid(vc1_transport_in_valid_w),
    .producer1_in_ready(vc1_transport_in_ready_w),
    .producer1_in_destination(vc1_transport_in_destination_w),
    .producer1_in_source(vc1_transport_in_source_w),
    .producer1_in_tag(vc1_transport_in_tag_w),
    .producer1_in_fragment(vc1_transport_in_fragment_w),
    .producer1_in_last(vc1_transport_in_last_w),
    .producer1_in_vc(vc1_transport_in_vc_w),
    .producer1_in_data(vc1_transport_in_data_w),
    .producer0_out_valid(vc0_transport_out_valid_w),
    .producer0_out_ready(vc0_transport_out_ready_w),
    .producer0_out_destination(vc0_transport_out_destination_w),
    .producer0_out_source(vc0_transport_out_source_w),
    .producer0_out_tag(vc0_transport_out_tag_w),
    .producer0_out_fragment(vc0_transport_out_fragment_w),
    .producer0_out_last(vc0_transport_out_last_w),
    .producer0_out_vc(vc0_transport_out_vc_w),
    .producer0_out_data(vc0_transport_out_data_w),
    .producer1_out_valid(vc1_transport_out_valid_w),
    .producer1_out_ready(vc1_transport_out_ready_w),
    .producer1_out_destination(vc1_transport_out_destination_w),
    .producer1_out_source(vc1_transport_out_source_w),
    .producer1_out_tag(vc1_transport_out_tag_w),
    .producer1_out_fragment(vc1_transport_out_fragment_w),
    .producer1_out_last(vc1_transport_out_last_w),
    .producer1_out_vc(vc1_transport_out_vc_w),
    .producer1_out_data(vc1_transport_out_data_w),
    .injection_protocol_error(shared_injection_protocol_error),
    .ejection_protocol_error(shared_ejection_protocol_error),
    .protocol_error(shared_transport_protocol_error),
    .router_accepted_flit_count(shared_router_accepted_flit_counts_w),
    .router_forwarded_flit_count(shared_router_forwarded_flit_counts),
    .router_input_stall_cycles(shared_router_input_stall_counts_w),
    .router_output_stall_cycles(shared_router_output_stall_counts_w),
    .router_contention_cycles(shared_router_contention_counts_w),
    .router_current_input_occupancy(shared_router_current_input_occupancy),
    .router_max_input_occupancy(shared_router_max_input_occupancy),
    .router_route_flit_count(shared_router_route_flit_counts)
  );

  assign protocol_error = vc0_protocol_error || vc1_protocol_error ||
    shared_transport_protocol_error;
endmodule
