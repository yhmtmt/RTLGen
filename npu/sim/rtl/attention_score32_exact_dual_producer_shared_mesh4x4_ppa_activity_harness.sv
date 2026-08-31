`timescale 1ns/1ps

// Compact registered physical boundary for the complete VC0 and VC1
// activity harnesses sharing one embodied mesh.
module attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness #(
  parameter integer PHYSICAL_BANKS = 15,
  parameter integer USE_FAKERAM = 0
) (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [31:0] control,
  output wire [127:0] observable
);
  wire [127:0] vc0_observable_w;
  wire [127:0] vc1_observable_w;

  wire [15:0] vc0_in_valid_w;
  wire [15:0] vc0_in_ready_w;
  wire [16*4-1:0] vc0_in_destination_w;
  wire [16*4-1:0] vc0_in_source_w;
  wire [16*8-1:0] vc0_in_tag_w;
  wire [16*3-1:0] vc0_in_fragment_w;
  wire [15:0] vc0_in_last_w;
  wire [16*2-1:0] vc0_in_vc_w;
  wire [16*256-1:0] vc0_in_data_w;
  wire [15:0] vc0_out_valid_w;
  wire [15:0] vc0_out_ready_w;
  wire [16*4-1:0] vc0_out_destination_w;
  wire [16*4-1:0] vc0_out_source_w;
  wire [16*8-1:0] vc0_out_tag_w;
  wire [16*3-1:0] vc0_out_fragment_w;
  wire [15:0] vc0_out_last_w;
  wire [16*2-1:0] vc0_out_vc_w;
  wire [16*256-1:0] vc0_out_data_w;

  wire [15:0] vc1_in_valid_w;
  wire [15:0] vc1_in_ready_w;
  wire [16*4-1:0] vc1_in_destination_w;
  wire [16*4-1:0] vc1_in_source_w;
  wire [16*8-1:0] vc1_in_tag_w;
  wire [16*3-1:0] vc1_in_fragment_w;
  wire [15:0] vc1_in_last_w;
  wire [16*2-1:0] vc1_in_vc_w;
  wire [16*256-1:0] vc1_in_data_w;
  wire [15:0] vc1_out_valid_w;
  wire [15:0] vc1_out_ready_w;
  wire [16*4-1:0] vc1_out_destination_w;
  wire [16*4-1:0] vc1_out_source_w;
  wire [16*8-1:0] vc1_out_tag_w;
  wire [16*3-1:0] vc1_out_fragment_w;
  wire [15:0] vc1_out_last_w;
  wire [16*2-1:0] vc1_out_vc_w;
  wire [16*256-1:0] vc1_out_data_w;

  wire [15:0] injection_protocol_error_w;
  wire [15:0] ejection_protocol_error_w;
  wire transport_protocol_error_w;
  wire [16*32-1:0] router_accepted_flit_count_w;
  wire [16*32-1:0] router_forwarded_flit_count_w;
  wire [16*32-1:0] router_input_stall_cycles_w;
  wire [16*32-1:0] router_output_stall_cycles_w;
  wire [16*32-1:0] router_contention_cycles_w;
  wire [16*32-1:0] router_current_input_occupancy_w;
  wire [16*32-1:0] router_max_input_occupancy_w;
  wire [16*5*32-1:0] router_route_flit_count_w;
  reg [31:0] transport_fold_w;
  integer router_i;

  (* keep_hierarchy = "yes" *)
  attention_shared_stream_context_service_ppa_activity_harness #(
    .INTERNAL_MESH(0)
  ) vc0_activity (
    .clk(clk), .rst_n(rst_n), .enable(enable), .control(control),
    .observable(vc0_observable_w),
    .transport_endpoint_in_valid(vc0_in_valid_w),
    .transport_endpoint_in_ready(vc0_in_ready_w),
    .transport_endpoint_in_destination(vc0_in_destination_w),
    .transport_endpoint_in_source(vc0_in_source_w),
    .transport_endpoint_in_tag(vc0_in_tag_w),
    .transport_endpoint_in_fragment(vc0_in_fragment_w),
    .transport_endpoint_in_last(vc0_in_last_w),
    .transport_endpoint_in_vc(vc0_in_vc_w),
    .transport_endpoint_in_data(vc0_in_data_w),
    .transport_endpoint_out_valid(vc0_out_valid_w),
    .transport_endpoint_out_ready(vc0_out_ready_w),
    .transport_endpoint_out_destination(vc0_out_destination_w),
    .transport_endpoint_out_source(vc0_out_source_w),
    .transport_endpoint_out_tag(vc0_out_tag_w),
    .transport_endpoint_out_fragment(vc0_out_fragment_w),
    .transport_endpoint_out_last(vc0_out_last_w),
    .transport_endpoint_out_vc(vc0_out_vc_w),
    .transport_endpoint_out_data(vc0_out_data_w)
  );

  (* keep_hierarchy = "yes" *)
  local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness #(
    .PHYSICAL_BANKS(PHYSICAL_BANKS),
    .USE_FAKERAM(USE_FAKERAM),
    .INTERNAL_MESH(0)
  ) vc1_activity (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .control(control ^ 32'h51c0_5a17), .observable(vc1_observable_w),
    .transport_endpoint_in_valid(vc1_in_valid_w),
    .transport_endpoint_in_ready(vc1_in_ready_w),
    .transport_endpoint_in_destination(vc1_in_destination_w),
    .transport_endpoint_in_source(vc1_in_source_w),
    .transport_endpoint_in_tag(vc1_in_tag_w),
    .transport_endpoint_in_fragment(vc1_in_fragment_w),
    .transport_endpoint_in_last(vc1_in_last_w),
    .transport_endpoint_in_vc(vc1_in_vc_w),
    .transport_endpoint_in_data(vc1_in_data_w),
    .transport_endpoint_out_valid(vc1_out_valid_w),
    .transport_endpoint_out_ready(vc1_out_ready_w),
    .transport_endpoint_out_destination(vc1_out_destination_w),
    .transport_endpoint_out_source(vc1_out_source_w),
    .transport_endpoint_out_tag(vc1_out_tag_w),
    .transport_endpoint_out_fragment(vc1_out_fragment_w),
    .transport_endpoint_out_last(vc1_out_last_w),
    .transport_endpoint_out_vc(vc1_out_vc_w),
    .transport_endpoint_out_data(vc1_out_data_w),
    .transport_router_accepted_flit_counts(router_accepted_flit_count_w),
    .transport_router_input_stall_counts(router_input_stall_cycles_w),
    .transport_router_output_stall_counts(router_output_stall_cycles_w),
    .transport_router_contention_counts(router_contention_cycles_w)
  );

  (* keep_hierarchy = "yes" *)
  noc_shared_vc_dual_producer_transport4x4 shared_transport (
    .clk(clk), .rst_n(rst_n),
    .producer0_in_valid(vc0_in_valid_w), .producer0_in_ready(vc0_in_ready_w),
    .producer0_in_destination(vc0_in_destination_w),
    .producer0_in_source(vc0_in_source_w), .producer0_in_tag(vc0_in_tag_w),
    .producer0_in_fragment(vc0_in_fragment_w), .producer0_in_last(vc0_in_last_w),
    .producer0_in_vc(vc0_in_vc_w), .producer0_in_data(vc0_in_data_w),
    .producer1_in_valid(vc1_in_valid_w), .producer1_in_ready(vc1_in_ready_w),
    .producer1_in_destination(vc1_in_destination_w),
    .producer1_in_source(vc1_in_source_w), .producer1_in_tag(vc1_in_tag_w),
    .producer1_in_fragment(vc1_in_fragment_w), .producer1_in_last(vc1_in_last_w),
    .producer1_in_vc(vc1_in_vc_w), .producer1_in_data(vc1_in_data_w),
    .producer0_out_valid(vc0_out_valid_w), .producer0_out_ready(vc0_out_ready_w),
    .producer0_out_destination(vc0_out_destination_w),
    .producer0_out_source(vc0_out_source_w), .producer0_out_tag(vc0_out_tag_w),
    .producer0_out_fragment(vc0_out_fragment_w), .producer0_out_last(vc0_out_last_w),
    .producer0_out_vc(vc0_out_vc_w), .producer0_out_data(vc0_out_data_w),
    .producer1_out_valid(vc1_out_valid_w), .producer1_out_ready(vc1_out_ready_w),
    .producer1_out_destination(vc1_out_destination_w),
    .producer1_out_source(vc1_out_source_w), .producer1_out_tag(vc1_out_tag_w),
    .producer1_out_fragment(vc1_out_fragment_w), .producer1_out_last(vc1_out_last_w),
    .producer1_out_vc(vc1_out_vc_w), .producer1_out_data(vc1_out_data_w),
    .injection_protocol_error(injection_protocol_error_w),
    .ejection_protocol_error(ejection_protocol_error_w),
    .protocol_error(transport_protocol_error_w),
    .router_accepted_flit_count(router_accepted_flit_count_w),
    .router_forwarded_flit_count(router_forwarded_flit_count_w),
    .router_input_stall_cycles(router_input_stall_cycles_w),
    .router_output_stall_cycles(router_output_stall_cycles_w),
    .router_contention_cycles(router_contention_cycles_w),
    .router_current_input_occupancy(router_current_input_occupancy_w),
    .router_max_input_occupancy(router_max_input_occupancy_w),
    .router_route_flit_count(router_route_flit_count_w)
  );

  always @* begin
    transport_fold_w = 32'b0;
    for (router_i = 0; router_i < 16; router_i = router_i + 1) begin
      transport_fold_w = transport_fold_w ^
        router_accepted_flit_count_w[router_i*32 +: 32] ^
        router_forwarded_flit_count_w[router_i*32 +: 32] ^
        router_input_stall_cycles_w[router_i*32 +: 32] ^
        router_output_stall_cycles_w[router_i*32 +: 32] ^
        router_contention_cycles_w[router_i*32 +: 32];
    end
    transport_fold_w[31] = transport_fold_w[31] ^ transport_protocol_error_w;
    transport_fold_w[30] = transport_fold_w[30] ^ (|injection_protocol_error_w);
    transport_fold_w[29] = transport_fold_w[29] ^ (|ejection_protocol_error_w);
  end

  assign observable = vc0_observable_w ^
    {vc1_observable_w[63:0], vc1_observable_w[127:64]} ^
    {96'b0, transport_fold_w};
endmodule
