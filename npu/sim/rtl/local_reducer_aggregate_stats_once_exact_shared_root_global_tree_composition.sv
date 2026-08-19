`timescale 1ns/1ps

// Fixed full-chain boundary for fifteen remote stats-once sources and one
// root-local canonical source.  The remote packet TX adapters and the 4x4
// mesh are outside this wrapper; this block owns the root RX endpoint, the
// fifteen packet-to-canonical decoders, and the exact sixteen-leaf tree.
//
// Context admission is deliberately atomic.  A caller may hold
// group_ctx_valid high, but neither child sees a context until both children
// report ready in the same cycle.
module local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer ENDPOINT_W = 4,
  parameter integer ADDR_W = 16,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer SOURCE_COUNT = 15,
  parameter integer LEAF_COUNT = 16,
  parameter integer BEAT_W = 419,
  parameter integer ROOT_ENDPOINT_ID = 15
) (
  input wire clk,
  input wire rst_n,

  input wire group_ctx_valid,
  output wire group_ctx_ready,
  input wire [SOURCE_COUNT*16-1:0] group_command_id,
  input wire [SOURCE_COUNT*5-1:0] group_head_base,
  input wire [SOURCE_COUNT*4-1:0] group_source,
  input wire [SOURCE_COUNT*4-1:0] group_destination,
  input wire [SOURCE_COUNT*VC_W-1:0] group_vc,
  input wire [SOURCE_COUNT*3-1:0] group_epoch,

  output wire [SOURCE_COUNT-1:0] tx_release_valid,
  input wire [SOURCE_COUNT-1:0] tx_release_ready,

  input wire root_local_valid,
  output wire root_local_ready,
  input wire [BEAT_W-1:0] root_local_beat_data,

  output wire mesh_in_valid,
  input wire mesh_in_ready,
  output wire [ENDPOINT_W-1:0] mesh_in_destination,
  output wire [ENDPOINT_W-1:0] mesh_in_source,
  output wire [TAG_W-1:0] mesh_in_tag,
  output wire [FRAGMENT_W-1:0] mesh_in_fragment,
  output wire mesh_in_last,
  output wire [VC_W-1:0] mesh_in_vc,
  output wire [DATA_W-1:0] mesh_in_data,

  input wire mesh_out_valid,
  output wire mesh_out_ready,
  input wire [ENDPOINT_W-1:0] mesh_out_destination,
  input wire [ENDPOINT_W-1:0] mesh_out_source,
  input wire [TAG_W-1:0] mesh_out_tag,
  input wire [FRAGMENT_W-1:0] mesh_out_fragment,
  input wire mesh_out_last,
  input wire [VC_W-1:0] mesh_out_vc,
  input wire [DATA_W-1:0] mesh_out_data,

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
  output wire [31:0] root_accepted_flit_count,
  output wire [31:0] root_descriptor_install_count,
  output wire [31:0] root_completion_count,
  output wire [31:0] root_replay_packet_count,
  output wire [5:0] max_occupied_slots
);
  wire [SOURCE_COUNT-1:0] rx_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] leaf_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] atomic_ctx_valid_w;
  wire atomic_ctx_ready_w;

  // Valid is gated by both ready vectors so the two child protocols can
  // never consume different subsets of one group context.
  assign atomic_ctx_ready_w = (&rx_ctx_ready_w) && (&leaf_ctx_ready_w);
  assign group_ctx_ready = atomic_ctx_ready_w;
  assign atomic_ctx_valid_w = {SOURCE_COUNT{group_ctx_valid &&
    atomic_ctx_ready_w}};

  wire [SOURCE_COUNT-1:0] codec_out_valid_w;
  wire [SOURCE_COUNT-1:0] codec_out_ready_w;
  wire [SOURCE_COUNT*DATA_W-1:0] codec_out_data_w;
  wire [SOURCE_COUNT-1:0] codec_out_group_last_w;
  wire [SOURCE_COUNT-1:0] rx_group_complete_w;
  wire [SOURCE_COUNT-1:0] rx_descriptor_installed_w;
  wire [SOURCE_COUNT-1:0] rx_protocol_error_w;
  wire rx_protocol_error;

  local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter #(
    .DATA_W(DATA_W),
    .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W),
    .VC_W(VC_W),
    .ENDPOINT_W(ENDPOINT_W),
    .ADDR_W(ADDR_W),
    .FLIT_COUNT_W(FLIT_COUNT_W),
    .SOURCE_COUNT(SOURCE_COUNT),
    .ROOT_ENDPOINT_ID(ROOT_ENDPOINT_ID)
  ) root_rx (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(atomic_ctx_valid_w),
    .group_ctx_ready(rx_ctx_ready_w),
    .group_command_id(group_command_id),
    .group_head_base(group_head_base),
    .group_source(group_source),
    .group_destination(group_destination),
    .group_vc(group_vc),
    .group_epoch(group_epoch),
    .tx_release_valid(tx_release_valid),
    .tx_release_ready(tx_release_ready),
    .codec_out_valid(codec_out_valid_w),
    .codec_out_ready(codec_out_ready_w),
    .codec_out_data(codec_out_data_w),
    .codec_out_group_last(codec_out_group_last_w),
    .group_complete(rx_group_complete_w),
    .descriptor_installed(rx_descriptor_installed_w),
    .source_protocol_error(rx_protocol_error_w),
    .mesh_in_valid(mesh_in_valid),
    .mesh_in_ready(mesh_in_ready),
    .mesh_in_destination(mesh_in_destination),
    .mesh_in_source(mesh_in_source),
    .mesh_in_tag(mesh_in_tag),
    .mesh_in_fragment(mesh_in_fragment),
    .mesh_in_last(mesh_in_last),
    .mesh_in_vc(mesh_in_vc),
    .mesh_in_data(mesh_in_data),
    .mesh_out_valid(mesh_out_valid),
    .mesh_out_ready(mesh_out_ready),
    .mesh_out_destination(mesh_out_destination),
    .mesh_out_source(mesh_out_source),
    .mesh_out_tag(mesh_out_tag),
    .mesh_out_fragment(mesh_out_fragment),
    .mesh_out_last(mesh_out_last),
    .mesh_out_vc(mesh_out_vc),
    .mesh_out_data(mesh_out_data),
    .root_accepted_flit_count(root_accepted_flit_count),
    .root_descriptor_install_count(root_descriptor_install_count),
    .root_completion_count(root_completion_count),
    .root_replay_packet_count(root_replay_packet_count),
    .max_occupied_slots(max_occupied_slots),
    .protocol_error(rx_protocol_error)
  );

  wire [LEAF_COUNT-1:0] leaf_valid_w;
  wire [LEAF_COUNT-1:0] leaf_ready_w;
  wire [LEAF_COUNT*16-1:0] leaf_command_id_w;
  wire [LEAF_COUNT*5-1:0] leaf_head_id_w;
  wire [LEAF_COUNT*32-1:0] leaf_global_max_w;
  wire [LEAF_COUNT*33-1:0] leaf_exp_sum_w;
  wire [LEAF_COUNT*4-1:0] leaf_slice_w;
  wire [LEAF_COUNT-1:0] leaf_last_w;
  wire [LEAF_COUNT*328-1:0] leaf_value_w;
  wire leaf_protocol_error;

  local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter #(
    .SOURCE_COUNT(SOURCE_COUNT),
    .LEAF_COUNT(LEAF_COUNT),
    .BEAT_W(BEAT_W),
    .FLIT_W(DATA_W)
  ) leaves (
    .clk(clk), .rst_n(rst_n),
    .source_group_ctx_valid(atomic_ctx_valid_w),
    .source_group_ctx_ready(leaf_ctx_ready_w),
    .source_group_command_id(group_command_id),
    .source_group_head_base(group_head_base),
    .source_flit_valid(codec_out_valid_w),
    .source_flit_ready(codec_out_ready_w),
    .source_flit_data(codec_out_data_w),
    .source_flit_group_last(codec_out_group_last_w),
    .decoder_protocol_error(source_protocol_error),
    .root_local_valid(root_local_valid),
    .root_local_ready(root_local_ready),
    .root_local_beat_data(root_local_beat_data),
    .leaf_valid(leaf_valid_w),
    .leaf_ready(leaf_ready_w),
    .leaf_command_id(leaf_command_id_w),
    .leaf_head_id(leaf_head_id_w),
    .leaf_global_max(leaf_global_max_w),
    .leaf_exp_sum(leaf_exp_sum_w),
    .leaf_slice(leaf_slice_w),
    .leaf_last(leaf_last_w),
    .leaf_value(leaf_value_w),
    .protocol_error(leaf_protocol_error)
  );

  attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59 tree (
    .clk(clk), .rst_n(rst_n),
    .leaf_valid(leaf_valid_w), .leaf_ready(leaf_ready_w),
    .leaf_command_id(leaf_command_id_w), .leaf_head_id(leaf_head_id_w),
    .leaf_global_max(leaf_global_max_w), .leaf_exp_sum(leaf_exp_sum_w),
    .leaf_slice(leaf_slice_w), .leaf_last(leaf_last_w),
    .leaf_value(leaf_value_w),
    .root_valid(root_valid), .root_ready(root_ready),
    .root_command_id(root_command_id), .root_head_id(root_head_id),
    .root_slice(root_slice), .root_last(root_last), .root_value(root_value),
    .protocol_error(tree_protocol_error)
  );

  assign group_complete = rx_group_complete_w;
  assign descriptor_installed = rx_descriptor_installed_w;
  assign protocol_error = rx_protocol_error || leaf_protocol_error ||
    tree_protocol_error || (|rx_protocol_error_w);

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || TAG_W != 8 || FRAGMENT_W != 3 || VC_W != 2 ||
        ENDPOINT_W != 4 || SOURCE_COUNT != 15 || LEAF_COUNT != 16 ||
        BEAT_W != 419 || ROOT_ENDPOINT_ID != 15) begin
      $error("shared-root full-chain composition width/count contract changed");
      $finish(1);
    end
  end
`endif
endmodule
