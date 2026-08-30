`timescale 1ns/1ps

// Fixed exact stats-once transport composition for the 15 remote producers
// and endpoint-15 shared root.  Context admission is the only scheduling
// boundary owned here.  Packet descriptors and the two physical packet slots
// remain inside the endpoint adapters.
module local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer ENDPOINT_W = 4,
  parameter integer ADDR_W = 16,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer SOURCE_COUNT = 15,
  parameter integer BEAT_W = 419,
  parameter integer ROOT_ENDPOINT_ID = 15,
  parameter integer PHYSICAL_BANKS = 15,
  parameter integer USE_FAKERAM = 0,
  parameter integer INTERNAL_MESH = 1
) (
  input wire clk,
  input wire rst_n,

  // Canonical 419-bit aggregate streams.  Each stream carries 128 beats for
  // one admitted group and must preserve valid/data while beat_ready is low.
  input wire [SOURCE_COUNT-1:0] source_beat_valid,
  output wire [SOURCE_COUNT-1:0] source_beat_ready,
  input wire [SOURCE_COUNT*BEAT_W-1:0] source_beat_data,
  input wire root_local_beat_valid,
  output wire root_local_beat_ready,
  input wire [BEAT_W-1:0] root_local_beat_data,

  // Producer group readiness is independent from stream valid/ready.
  input wire [SOURCE_COUNT-1:0] remote_group_ready,
  input wire root_local_group_ready,
  input wire admission_enable,
  input wire [15:0] base_command_id,

  output wire group_admission_pulse,
  output wire [1:0] group_index,
  output wire [4:0] head_base,
  output wire [2:0] group_epoch,
  output wire [SOURCE_COUNT-1:0] source_producer_accept,
  output wire root_producer_accept,
  output wire [SOURCE_COUNT-1:0] source_ctx_valid,
  output wire root_ctx_valid,
  output wire [2:0] admitted_group_count,
  output wire done,

  output wire root_valid,
  input wire root_ready,
  output wire [15:0] root_command_id,
  output wire [4:0] root_head_id,
  output wire [3:0] root_slice,
  output wire root_last,
  output wire [319:0] root_value,

  output wire [SOURCE_COUNT-1:0] group_complete,
  output wire [SOURCE_COUNT-1:0] descriptor_installed,
  output wire [SOURCE_COUNT-1:0] source_protocol_error,
  output wire tree_protocol_error,
  output wire protocol_error,

  // Adapter-owned transport counters and mesh-level counters.  The packed
  // per-source/per-endpoint vectors preserve attribution for analysis.
  output wire [SOURCE_COUNT*32-1:0] source_tx_descriptor_counts,
  output reg [31:0] source_tx_descriptor_count,
  output wire [31:0] root_accepted_flit_count,
  output wire [31:0] root_descriptor_install_count,
  output wire [31:0] root_completion_count,
  output wire [31:0] root_replay_packet_count,
  output wire [5:0] max_occupied_slots,
  output wire [16*32-1:0] mesh_router_accepted_flit_counts,
  output reg [31:0] mesh_accepted_flit_count,
  output reg [31:0] mesh_contention_cycles,
  output reg [31:0] mesh_input_stall_cycles,
  output reg [31:0] mesh_output_stall_cycles,

  // External transport boundary. In INTERNAL_MESH mode the injection and
  // ready ports remain observable, but the external return/counter inputs are
  // ignored. Setting INTERNAL_MESH=0 removes the private mesh.
  output wire [15:0] transport_endpoint_in_valid,
  input wire [15:0] transport_endpoint_in_ready,
  output wire [16*ENDPOINT_W-1:0] transport_endpoint_in_destination,
  output wire [16*ENDPOINT_W-1:0] transport_endpoint_in_source,
  output wire [16*TAG_W-1:0] transport_endpoint_in_tag,
  output wire [16*FRAGMENT_W-1:0] transport_endpoint_in_fragment,
  output wire [15:0] transport_endpoint_in_last,
  output wire [16*VC_W-1:0] transport_endpoint_in_vc,
  output wire [16*DATA_W-1:0] transport_endpoint_in_data,
  input wire [15:0] transport_endpoint_out_valid,
  output wire [15:0] transport_endpoint_out_ready,
  input wire [16*ENDPOINT_W-1:0] transport_endpoint_out_destination,
  input wire [16*ENDPOINT_W-1:0] transport_endpoint_out_source,
  input wire [16*TAG_W-1:0] transport_endpoint_out_tag,
  input wire [16*FRAGMENT_W-1:0] transport_endpoint_out_fragment,
  input wire [15:0] transport_endpoint_out_last,
  input wire [16*VC_W-1:0] transport_endpoint_out_vc,
  input wire [16*DATA_W-1:0] transport_endpoint_out_data,
  input wire [16*32-1:0] transport_router_accepted_flit_counts,
  input wire [16*32-1:0] transport_router_input_stall_counts,
  input wire [16*32-1:0] transport_router_output_stall_counts,
  input wire [16*32-1:0] transport_router_contention_counts
);
  localparam integer NODES = 16;

  wire [SOURCE_COUNT-1:0] encoder_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] encoder_beat_ready_w;
  wire [SOURCE_COUNT-1:0] adapter_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] source_ctx_ready_w =
    encoder_ctx_ready_w & adapter_ctx_ready_w;
  wire shared_root_ctx_ready_w;

  wire [SOURCE_COUNT-1:0] encoder_flit_valid_w;
  wire [SOURCE_COUNT-1:0] encoder_flit_ready_w;
  wire [SOURCE_COUNT*DATA_W-1:0] encoder_flit_data_w;
  wire [SOURCE_COUNT-1:0] encoder_flit_group_last_w;
  wire [SOURCE_COUNT-1:0] encoder_protocol_error_w;

  wire [SOURCE_COUNT-1:0] adapter_tx_release_valid_w;
  wire [SOURCE_COUNT-1:0] adapter_tx_release_ready_w;
  wire [SOURCE_COUNT-1:0] adapter_tx_complete_w;
  wire [SOURCE_COUNT-1:0] adapter_protocol_error_w;
  wire [SOURCE_COUNT*32-1:0] adapter_tx_descriptor_counts_w;

  wire [SOURCE_COUNT-1:0] source_mesh_in_valid_w;
  wire [SOURCE_COUNT-1:0] source_mesh_in_ready_w;
  wire [SOURCE_COUNT*ENDPOINT_W-1:0] source_mesh_in_destination_w;
  wire [SOURCE_COUNT*ENDPOINT_W-1:0] source_mesh_in_source_w;
  wire [SOURCE_COUNT*TAG_W-1:0] source_mesh_in_tag_w;
  wire [SOURCE_COUNT*FRAGMENT_W-1:0] source_mesh_in_fragment_w;
  wire [SOURCE_COUNT-1:0] source_mesh_in_last_w;
  wire [SOURCE_COUNT*VC_W-1:0] source_mesh_in_vc_w;
  wire [SOURCE_COUNT*DATA_W-1:0] source_mesh_in_data_w;
  wire [SOURCE_COUNT-1:0] source_mesh_out_valid_w;
  wire [SOURCE_COUNT-1:0] source_mesh_out_ready_w;
  wire [SOURCE_COUNT*ENDPOINT_W-1:0] source_mesh_out_destination_w;
  wire [SOURCE_COUNT*ENDPOINT_W-1:0] source_mesh_out_source_w;
  wire [SOURCE_COUNT*TAG_W-1:0] source_mesh_out_tag_w;
  wire [SOURCE_COUNT*FRAGMENT_W-1:0] source_mesh_out_fragment_w;
  wire [SOURCE_COUNT-1:0] source_mesh_out_last_w;
  wire [SOURCE_COUNT*VC_W-1:0] source_mesh_out_vc_w;
  wire [SOURCE_COUNT*DATA_W-1:0] source_mesh_out_data_w;
  wire [SOURCE_COUNT-1:0] unused_source_mesh_out_ready_w;

  wire [SOURCE_COUNT*16-1:0] group_command_id_w;
  wire [SOURCE_COUNT*5-1:0] group_head_base_w;
  wire [SOURCE_COUNT*4-1:0] group_source_w;
  wire [SOURCE_COUNT*4-1:0] group_destination_w;
  wire [SOURCE_COUNT*VC_W-1:0] group_vc_w;
  wire [SOURCE_COUNT*3-1:0] group_epoch_w;
  wire admission_protocol_error_w;
  wire composition_protocol_error_w;
  wire [16*32-1:0] mesh_router_input_stall_counts_w;
  wire [16*32-1:0] mesh_router_output_stall_counts_w;
  wire [16*32-1:0] mesh_router_contention_counts_w;
  wire [15:0] internal_mesh_endpoint_in_ready_w;
  wire [15:0] internal_mesh_endpoint_out_valid_w;
  wire [16*ENDPOINT_W-1:0] internal_mesh_endpoint_out_destination_w;
  wire [16*ENDPOINT_W-1:0] internal_mesh_endpoint_out_source_w;
  wire [16*TAG_W-1:0] internal_mesh_endpoint_out_tag_w;
  wire [16*FRAGMENT_W-1:0] internal_mesh_endpoint_out_fragment_w;
  wire [15:0] internal_mesh_endpoint_out_last_w;
  wire [16*VC_W-1:0] internal_mesh_endpoint_out_vc_w;
  wire [16*DATA_W-1:0] internal_mesh_endpoint_out_data_w;
  wire [16*32-1:0] internal_mesh_router_accepted_flit_counts_w;
  wire [16*32-1:0] internal_mesh_router_input_stall_counts_w;
  wire [16*32-1:0] internal_mesh_router_output_stall_counts_w;
  wire [16*32-1:0] internal_mesh_router_contention_counts_w;

  local_reducer_aggregate_stats_once_exact_shared_root_group_admission admission (
    .clk(clk),
    .rst_n(rst_n),
    .admission_enable(admission_enable),
    .remote_group_ready(remote_group_ready),
    .root_local_group_ready(root_local_group_ready),
    .source_ctx_ready(source_ctx_ready_w),
    .shared_root_ctx_ready(shared_root_ctx_ready_w),
    .group_admission_pulse(group_admission_pulse),
    .group_index(group_index),
    .head_base(head_base),
    .group_epoch(group_epoch),
    .source_producer_accept(source_producer_accept),
    .root_producer_accept(root_producer_accept),
    .source_ctx_valid(source_ctx_valid),
    .shared_root_ctx_valid(root_ctx_valid),
    .admitted_group_count(admitted_group_count),
    .done(done),
    .protocol_error(admission_protocol_error_w)
  );

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_source
      localparam integer SOURCE_ID = source_g;

      assign group_command_id_w[SOURCE_ID*16 +: 16] =
        base_command_id + group_index;
      assign group_head_base_w[SOURCE_ID*5 +: 5] = head_base;
      assign group_source_w[SOURCE_ID*4 +: 4] = SOURCE_ID[3:0];
      assign group_destination_w[SOURCE_ID*4 +: 4] = ROOT_ENDPOINT_ID[3:0];
      assign group_vc_w[SOURCE_ID*VC_W +: VC_W] = {{(VC_W-1){1'b0}}, 1'b1};
      assign group_epoch_w[SOURCE_ID*3 +: 3] = group_epoch;
      assign source_beat_ready[SOURCE_ID] = encoder_beat_ready_w[SOURCE_ID];

      local_reducer_aggregate_stats_once_exact_encoder encoder (
        .clk(clk),
        .rst_n(rst_n),
        .group_ctx_valid(source_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(encoder_ctx_ready_w[SOURCE_ID]),
        .group_command_id(group_command_id_w[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base_w[SOURCE_ID*5 +: 5]),
        .beat_valid(source_beat_valid[SOURCE_ID]),
        .beat_ready(encoder_beat_ready_w[SOURCE_ID]),
        .beat_data(source_beat_data[SOURCE_ID*BEAT_W +: BEAT_W]),
        .flit_valid(encoder_flit_valid_w[SOURCE_ID]),
        .flit_ready(encoder_flit_ready_w[SOURCE_ID]),
        .flit_data(encoder_flit_data_w[SOURCE_ID*DATA_W +: DATA_W]),
        .flit_group_last(encoder_flit_group_last_w[SOURCE_ID]),
        .protocol_error(encoder_protocol_error_w[SOURCE_ID])
      );

      local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
        .LOCAL_ENDPOINT_ID(SOURCE_ID),
        .TX_ENABLE(1),
        .RX_ENABLE(0),
        .SRC_BASE_ADDR(0),
        .DST_BASE_ADDR(4096)
      ) source_tx (
        .clk(clk),
        .rst_n(rst_n),
        .group_ctx_valid(source_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(adapter_ctx_ready_w[SOURCE_ID]),
        .group_command_id(group_command_id_w[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base_w[SOURCE_ID*5 +: 5]),
        .group_source(group_source_w[SOURCE_ID*4 +: 4]),
        .group_destination(group_destination_w[SOURCE_ID*4 +: 4]),
        .group_vc(group_vc_w[SOURCE_ID*VC_W +: VC_W]),
        .group_epoch(group_epoch_w[SOURCE_ID*3 +: 3]),
        .codec_in_valid(encoder_flit_valid_w[SOURCE_ID]),
        .codec_in_ready(encoder_flit_ready_w[SOURCE_ID]),
        .codec_in_data(encoder_flit_data_w[SOURCE_ID*DATA_W +: DATA_W]),
        .codec_in_group_last(encoder_flit_group_last_w[SOURCE_ID]),
        .tx_release_valid(adapter_tx_release_valid_w[SOURCE_ID]),
        .tx_release_ready(adapter_tx_release_ready_w[SOURCE_ID]),
        .codec_out_valid(),
        .codec_out_ready(1'b0),
        .codec_out_data(),
        .codec_out_group_last(),
        .tx_group_complete(adapter_tx_complete_w[SOURCE_ID]),
        .rx_group_complete(),
        .rx_descriptor_installed(),
        .protocol_error(adapter_protocol_error_w[SOURCE_ID]),
        .tx_descriptor_count(adapter_tx_descriptor_counts_w[SOURCE_ID*32 +: 32]),
        .rx_completion_count(),
        .replay_packet_count(),
        .max_source_occupancy(),
        .max_destination_occupancy(),
        .mesh_in_valid(source_mesh_in_valid_w[SOURCE_ID]),
        .mesh_in_ready(source_mesh_in_ready_w[SOURCE_ID]),
        .mesh_in_destination(source_mesh_in_destination_w[SOURCE_ID*ENDPOINT_W +: ENDPOINT_W]),
        .mesh_in_source(source_mesh_in_source_w[SOURCE_ID*ENDPOINT_W +: ENDPOINT_W]),
        .mesh_in_tag(source_mesh_in_tag_w[SOURCE_ID*TAG_W +: TAG_W]),
        .mesh_in_fragment(source_mesh_in_fragment_w[SOURCE_ID*FRAGMENT_W +: FRAGMENT_W]),
        .mesh_in_last(source_mesh_in_last_w[SOURCE_ID]),
        .mesh_in_vc(source_mesh_in_vc_w[SOURCE_ID*VC_W +: VC_W]),
        .mesh_in_data(source_mesh_in_data_w[SOURCE_ID*DATA_W +: DATA_W]),
        // TX-only endpoint: no physical RX path is fabricated here.
        .mesh_out_valid(1'b0),
        .mesh_out_ready(unused_source_mesh_out_ready_w[SOURCE_ID]),
        .mesh_out_destination({ENDPOINT_W{1'b0}}),
        .mesh_out_source({ENDPOINT_W{1'b0}}),
        .mesh_out_tag({TAG_W{1'b0}}),
        .mesh_out_fragment({FRAGMENT_W{1'b0}}),
        .mesh_out_last(1'b0),
        .mesh_out_vc({VC_W{1'b0}}),
        .mesh_out_data({DATA_W{1'b0}})
      );
    end
  endgenerate

  wire composition_mesh_in_valid_w;
  wire composition_mesh_in_ready_w;
  wire [ENDPOINT_W-1:0] composition_mesh_in_destination_w;
  wire [ENDPOINT_W-1:0] composition_mesh_in_source_w;
  wire [TAG_W-1:0] composition_mesh_in_tag_w;
  wire [FRAGMENT_W-1:0] composition_mesh_in_fragment_w;
  wire composition_mesh_in_last_w;
  wire [VC_W-1:0] composition_mesh_in_vc_w;
  wire [DATA_W-1:0] composition_mesh_in_data_w;
  wire composition_mesh_out_valid_w;
  wire composition_mesh_out_ready_w;
  wire [ENDPOINT_W-1:0] composition_mesh_out_destination_w;
  wire [ENDPOINT_W-1:0] composition_mesh_out_source_w;
  wire [TAG_W-1:0] composition_mesh_out_tag_w;
  wire [FRAGMENT_W-1:0] composition_mesh_out_fragment_w;
  wire composition_mesh_out_last_w;
  wire [VC_W-1:0] composition_mesh_out_vc_w;
  wire [DATA_W-1:0] composition_mesh_out_data_w;

  local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition #(
    .DATA_W(DATA_W),
    .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W),
    .VC_W(VC_W),
    .ENDPOINT_W(ENDPOINT_W),
    .ADDR_W(ADDR_W),
    .FLIT_COUNT_W(FLIT_COUNT_W),
    .SOURCE_COUNT(SOURCE_COUNT),
    .BEAT_W(BEAT_W),
    .ROOT_ENDPOINT_ID(ROOT_ENDPOINT_ID),
    .PHYSICAL_BANKS(PHYSICAL_BANKS),
    .USE_FAKERAM(USE_FAKERAM)
  ) shared_root (
    .clk(clk),
    .rst_n(rst_n),
    .group_ctx_valid(root_ctx_valid),
    .group_ctx_ready(shared_root_ctx_ready_w),
    .group_command_id(group_command_id_w),
    .group_head_base(group_head_base_w),
    .group_source(group_source_w),
    .group_destination(group_destination_w),
    .group_vc(group_vc_w),
    .group_epoch(group_epoch_w),
    .tx_release_valid(adapter_tx_release_valid_w),
    .tx_release_ready(adapter_tx_release_ready_w),
    .root_local_valid(root_local_beat_valid),
    .root_local_ready(root_local_beat_ready),
    .root_local_beat_data(root_local_beat_data),
    .mesh_in_valid(composition_mesh_in_valid_w),
    .mesh_in_ready(composition_mesh_in_ready_w),
    .mesh_in_destination(composition_mesh_in_destination_w),
    .mesh_in_source(composition_mesh_in_source_w),
    .mesh_in_tag(composition_mesh_in_tag_w),
    .mesh_in_fragment(composition_mesh_in_fragment_w),
    .mesh_in_last(composition_mesh_in_last_w),
    .mesh_in_vc(composition_mesh_in_vc_w),
    .mesh_in_data(composition_mesh_in_data_w),
    .mesh_out_valid(composition_mesh_out_valid_w),
    .mesh_out_ready(composition_mesh_out_ready_w),
    .mesh_out_destination(composition_mesh_out_destination_w),
    .mesh_out_source(composition_mesh_out_source_w),
    .mesh_out_tag(composition_mesh_out_tag_w),
    .mesh_out_fragment(composition_mesh_out_fragment_w),
    .mesh_out_last(composition_mesh_out_last_w),
    .mesh_out_vc(composition_mesh_out_vc_w),
    .mesh_out_data(composition_mesh_out_data_w),
    .root_valid(root_valid),
    .root_ready(root_ready),
    .root_command_id(root_command_id),
    .root_head_id(root_head_id),
    .root_slice(root_slice),
    .root_last(root_last),
    .root_value(root_value),
    .group_complete(group_complete),
    .descriptor_installed(descriptor_installed),
    .source_protocol_error(source_protocol_error),
    .tree_protocol_error(tree_protocol_error),
    .protocol_error(composition_protocol_error_w),
    .root_accepted_flit_count(root_accepted_flit_count),
    .root_descriptor_install_count(root_descriptor_install_count),
    .root_completion_count(root_completion_count),
    .root_replay_packet_count(root_replay_packet_count),
    .max_occupied_slots(max_occupied_slots)
  );

  wire [15:0] mesh_endpoint_in_valid_w;
  wire [15:0] mesh_endpoint_in_ready_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_in_destination_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_in_source_w;
  wire [16*TAG_W-1:0] mesh_endpoint_in_tag_w;
  wire [16*FRAGMENT_W-1:0] mesh_endpoint_in_fragment_w;
  wire [15:0] mesh_endpoint_in_last_w;
  wire [16*VC_W-1:0] mesh_endpoint_in_vc_w;
  wire [16*DATA_W-1:0] mesh_endpoint_in_data_w;
  wire [15:0] mesh_endpoint_out_valid_w;
  wire [15:0] mesh_endpoint_out_ready_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_out_destination_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_out_source_w;
  wire [16*TAG_W-1:0] mesh_endpoint_out_tag_w;
  wire [16*FRAGMENT_W-1:0] mesh_endpoint_out_fragment_w;
  wire [15:0] mesh_endpoint_out_last_w;
  wire [16*VC_W-1:0] mesh_endpoint_out_vc_w;
  wire [16*DATA_W-1:0] mesh_endpoint_out_data_w;

  assign mesh_endpoint_in_valid_w[SOURCE_COUNT-1:0] =
    source_mesh_in_valid_w;
  assign mesh_endpoint_in_valid_w[ROOT_ENDPOINT_ID] =
    composition_mesh_in_valid_w;
  assign mesh_endpoint_in_destination_w[SOURCE_COUNT*ENDPOINT_W-1:0] =
    source_mesh_in_destination_w;
  assign mesh_endpoint_in_destination_w[ROOT_ENDPOINT_ID*ENDPOINT_W +: ENDPOINT_W] =
    composition_mesh_in_destination_w;
  assign mesh_endpoint_in_source_w[SOURCE_COUNT*ENDPOINT_W-1:0] =
    source_mesh_in_source_w;
  assign mesh_endpoint_in_source_w[ROOT_ENDPOINT_ID*ENDPOINT_W +: ENDPOINT_W] =
    composition_mesh_in_source_w;
  assign mesh_endpoint_in_tag_w[SOURCE_COUNT*TAG_W-1:0] = source_mesh_in_tag_w;
  assign mesh_endpoint_in_tag_w[ROOT_ENDPOINT_ID*TAG_W +: TAG_W] = composition_mesh_in_tag_w;
  assign mesh_endpoint_in_fragment_w[SOURCE_COUNT*FRAGMENT_W-1:0] = source_mesh_in_fragment_w;
  assign mesh_endpoint_in_fragment_w[ROOT_ENDPOINT_ID*FRAGMENT_W +: FRAGMENT_W] = composition_mesh_in_fragment_w;
  assign mesh_endpoint_in_last_w[SOURCE_COUNT-1:0] = source_mesh_in_last_w;
  assign mesh_endpoint_in_last_w[ROOT_ENDPOINT_ID] = composition_mesh_in_last_w;
  assign mesh_endpoint_in_vc_w[SOURCE_COUNT*VC_W-1:0] = source_mesh_in_vc_w;
  assign mesh_endpoint_in_vc_w[ROOT_ENDPOINT_ID*VC_W +: VC_W] = composition_mesh_in_vc_w;
  assign mesh_endpoint_in_data_w[SOURCE_COUNT*DATA_W-1:0] = source_mesh_in_data_w;
  assign mesh_endpoint_in_data_w[ROOT_ENDPOINT_ID*DATA_W +: DATA_W] = composition_mesh_in_data_w;

  assign transport_endpoint_in_valid = mesh_endpoint_in_valid_w;
  assign transport_endpoint_in_destination = mesh_endpoint_in_destination_w;
  assign transport_endpoint_in_source = mesh_endpoint_in_source_w;
  assign transport_endpoint_in_tag = mesh_endpoint_in_tag_w;
  assign transport_endpoint_in_fragment = mesh_endpoint_in_fragment_w;
  assign transport_endpoint_in_last = mesh_endpoint_in_last_w;
  assign transport_endpoint_in_vc = mesh_endpoint_in_vc_w;
  assign transport_endpoint_in_data = mesh_endpoint_in_data_w;

  assign mesh_endpoint_in_ready_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_in_ready_w : transport_endpoint_in_ready;
  assign mesh_endpoint_out_valid_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_valid_w : transport_endpoint_out_valid;
  assign mesh_endpoint_out_destination_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_destination_w : transport_endpoint_out_destination;
  assign mesh_endpoint_out_source_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_source_w : transport_endpoint_out_source;
  assign mesh_endpoint_out_tag_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_tag_w : transport_endpoint_out_tag;
  assign mesh_endpoint_out_fragment_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_fragment_w : transport_endpoint_out_fragment;
  assign mesh_endpoint_out_last_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_last_w : transport_endpoint_out_last;
  assign mesh_endpoint_out_vc_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_vc_w : transport_endpoint_out_vc;
  assign mesh_endpoint_out_data_w = (INTERNAL_MESH != 0) ?
    internal_mesh_endpoint_out_data_w : transport_endpoint_out_data;

  assign source_mesh_in_ready_w = mesh_endpoint_in_ready_w[SOURCE_COUNT-1:0];
  assign composition_mesh_in_ready_w = mesh_endpoint_in_ready_w[ROOT_ENDPOINT_ID];

  assign source_mesh_out_valid_w = mesh_endpoint_out_valid_w[SOURCE_COUNT-1:0];
  assign composition_mesh_out_valid_w = mesh_endpoint_out_valid_w[ROOT_ENDPOINT_ID];
  assign source_mesh_out_destination_w = mesh_endpoint_out_destination_w[SOURCE_COUNT*ENDPOINT_W-1:0];
  assign composition_mesh_out_destination_w = mesh_endpoint_out_destination_w[ROOT_ENDPOINT_ID*ENDPOINT_W +: ENDPOINT_W];
  assign source_mesh_out_source_w = mesh_endpoint_out_source_w[SOURCE_COUNT*ENDPOINT_W-1:0];
  assign composition_mesh_out_source_w = mesh_endpoint_out_source_w[ROOT_ENDPOINT_ID*ENDPOINT_W +: ENDPOINT_W];
  assign source_mesh_out_tag_w = mesh_endpoint_out_tag_w[SOURCE_COUNT*TAG_W-1:0];
  assign composition_mesh_out_tag_w = mesh_endpoint_out_tag_w[ROOT_ENDPOINT_ID*TAG_W +: TAG_W];
  assign source_mesh_out_fragment_w = mesh_endpoint_out_fragment_w[SOURCE_COUNT*FRAGMENT_W-1:0];
  assign composition_mesh_out_fragment_w = mesh_endpoint_out_fragment_w[ROOT_ENDPOINT_ID*FRAGMENT_W +: FRAGMENT_W];
  assign source_mesh_out_last_w = mesh_endpoint_out_last_w[SOURCE_COUNT-1:0];
  assign composition_mesh_out_last_w = mesh_endpoint_out_last_w[ROOT_ENDPOINT_ID];
  assign source_mesh_out_vc_w = mesh_endpoint_out_vc_w[SOURCE_COUNT*VC_W-1:0];
  assign composition_mesh_out_vc_w = mesh_endpoint_out_vc_w[ROOT_ENDPOINT_ID*VC_W +: VC_W];
  assign source_mesh_out_data_w = mesh_endpoint_out_data_w[SOURCE_COUNT*DATA_W-1:0];
  assign composition_mesh_out_data_w = mesh_endpoint_out_data_w[ROOT_ENDPOINT_ID*DATA_W +: DATA_W];
  // Endpoints 0..14 are TX-only in this composition. They have no receive
  // consumer, so keep their ejection direction explicitly drainable instead
  // of propagating undriven ready values into an external shared mesh.
  assign source_mesh_out_ready_w = {SOURCE_COUNT{1'b1}};
  assign mesh_endpoint_out_ready_w[SOURCE_COUNT-1:0] = source_mesh_out_ready_w;
  assign mesh_endpoint_out_ready_w[ROOT_ENDPOINT_ID] = composition_mesh_out_ready_w;
  assign transport_endpoint_out_ready = mesh_endpoint_out_ready_w;

  assign mesh_router_accepted_flit_counts = (INTERNAL_MESH != 0) ?
    internal_mesh_router_accepted_flit_counts_w : transport_router_accepted_flit_counts;
  assign mesh_router_input_stall_counts_w = (INTERNAL_MESH != 0) ?
    internal_mesh_router_input_stall_counts_w : transport_router_input_stall_counts;
  assign mesh_router_output_stall_counts_w = (INTERNAL_MESH != 0) ?
    internal_mesh_router_output_stall_counts_w : transport_router_output_stall_counts;
  assign mesh_router_contention_counts_w = (INTERNAL_MESH != 0) ?
    internal_mesh_router_contention_counts_w : transport_router_contention_counts;

  generate
    if (INTERNAL_MESH != 0) begin : gen_internal_mesh
      noc_segmented_mesh4x4 #(
        .DATA_W(DATA_W),
        .TAG_W(TAG_W),
        .FRAGMENT_W(FRAGMENT_W),
        .VC_W(VC_W)
      ) mesh (
        .clk(clk),
        .rst_n(rst_n),
        .endpoint_in_valid(mesh_endpoint_in_valid_w),
        .endpoint_in_ready(internal_mesh_endpoint_in_ready_w),
        .endpoint_in_dest(mesh_endpoint_in_destination_w),
        .endpoint_in_source(mesh_endpoint_in_source_w),
        .endpoint_in_tag(mesh_endpoint_in_tag_w),
        .endpoint_in_fragment(mesh_endpoint_in_fragment_w),
        .endpoint_in_last(mesh_endpoint_in_last_w),
        .endpoint_in_vc(mesh_endpoint_in_vc_w),
        .endpoint_in_data(mesh_endpoint_in_data_w),
        .endpoint_out_valid(internal_mesh_endpoint_out_valid_w),
        .endpoint_out_ready(mesh_endpoint_out_ready_w),
        .endpoint_out_dest(internal_mesh_endpoint_out_destination_w),
        .endpoint_out_source(internal_mesh_endpoint_out_source_w),
        .endpoint_out_tag(internal_mesh_endpoint_out_tag_w),
        .endpoint_out_fragment(internal_mesh_endpoint_out_fragment_w),
        .endpoint_out_last(internal_mesh_endpoint_out_last_w),
        .endpoint_out_vc(internal_mesh_endpoint_out_vc_w),
        .endpoint_out_data(internal_mesh_endpoint_out_data_w),
        .router_accepted_flit_count(internal_mesh_router_accepted_flit_counts_w),
        .router_forwarded_flit_count(),
        .router_input_stall_cycles(internal_mesh_router_input_stall_counts_w),
        .router_output_stall_cycles(internal_mesh_router_output_stall_counts_w),
        .router_contention_cycles(internal_mesh_router_contention_counts_w),
        .router_current_input_occupancy(),
        .router_max_input_occupancy(),
        .router_route_flit_count()
      );
    end
  endgenerate

  integer sum_i;
  always @* begin
    source_tx_descriptor_count = 0;
    mesh_accepted_flit_count = 0;
    mesh_contention_cycles = 0;
    mesh_input_stall_cycles = 0;
    mesh_output_stall_cycles = 0;
    for (sum_i = 0; sum_i < SOURCE_COUNT; sum_i = sum_i + 1)
      source_tx_descriptor_count = source_tx_descriptor_count +
        adapter_tx_descriptor_counts_w[sum_i*32 +: 32];
    for (sum_i = 0; sum_i < NODES; sum_i = sum_i + 1) begin
      mesh_accepted_flit_count = mesh_accepted_flit_count +
        mesh_router_accepted_flit_counts[sum_i*32 +: 32];
      mesh_contention_cycles = mesh_contention_cycles +
        mesh_router_contention_counts_w[sum_i*32 +: 32];
      mesh_input_stall_cycles = mesh_input_stall_cycles +
        mesh_router_input_stall_counts_w[sum_i*32 +: 32];
      mesh_output_stall_cycles = mesh_output_stall_cycles +
        mesh_router_output_stall_counts_w[sum_i*32 +: 32];
    end
  end

  assign source_tx_descriptor_counts = adapter_tx_descriptor_counts_w;
  assign protocol_error = admission_protocol_error_w ||
    composition_protocol_error_w || (|encoder_protocol_error_w) ||
    (|adapter_protocol_error_w);

`ifndef SYNTHESIS
  initial begin
    if (INTERNAL_MESH != 0 && INTERNAL_MESH != 1) begin
      $error("INTERNAL_MESH must be 0 or 1");
      $finish(1);
    end
  end
`endif

endmodule
