`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer LEAF_COUNT = 16;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer GROUP_FLITS = 167;
  localparam integer GROUP_PACKETS = 21;
  localparam integer SIM_TIMEOUT_CYCLES = 10000;
  localparam integer NODES = 16;
  localparam integer DATA_W = 256;
  localparam integer TAG_W = 8;
  localparam integer FRAGMENT_W = 3;
  localparam integer VC_W = 2;
`ifdef SHARED_ROOT_PHYSICAL_BANKS
  localparam integer ROOT_PHYSICAL_BANKS = `SHARED_ROOT_PHYSICAL_BANKS;
`else
  localparam integer ROOT_PHYSICAL_BANKS = SOURCE_COUNT;
`endif

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg ctx_pending = 1'b1;
  wire [SOURCE_COUNT-1:0] source_ctx_valid;
  wire [SOURCE_COUNT-1:0] source_ctx_ready;
  wire [SOURCE_COUNT-1:0] encoder_ctx_ready;
  wire composition_ctx_ready;
  wire context_fire = ctx_pending && composition_ctx_ready &&
    (&source_ctx_ready) && (&encoder_ctx_ready);
  assign source_ctx_valid = {SOURCE_COUNT{context_fire}};

  wire [SOURCE_COUNT*16-1:0] group_command_id = {SOURCE_COUNT{16'h5a00}};
  wire [SOURCE_COUNT*5-1:0] group_head_base = {SOURCE_COUNT{5'd0}};
  wire [SOURCE_COUNT*4-1:0] group_source = {
    4'd14, 4'd13, 4'd12, 4'd11, 4'd10, 4'd9, 4'd8, 4'd7,
    4'd6, 4'd5, 4'd4, 4'd3, 4'd2, 4'd1, 4'd0
  };
  wire [SOURCE_COUNT*4-1:0] group_destination = {SOURCE_COUNT{4'd15}};
  wire [SOURCE_COUNT*VC_W-1:0] group_vc = {SOURCE_COUNT{2'd0}};
  wire [SOURCE_COUNT*3-1:0] group_epoch = {SOURCE_COUNT{3'd0}};

  reg [31:0] source_beat_index [0:SOURCE_COUNT-1];
  wire [SOURCE_COUNT-1:0] encoder_beat_valid;
  wire [SOURCE_COUNT-1:0] encoder_beat_ready;
  wire [SOURCE_COUNT*BEAT_W-1:0] encoder_beat_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_valid;
  wire [SOURCE_COUNT-1:0] encoder_flit_ready;
  wire [SOURCE_COUNT*FLIT_W-1:0] encoder_flit_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_group_last;
  wire [SOURCE_COUNT-1:0] encoder_error;
  wire [SOURCE_COUNT-1:0] tx_group_complete;
  wire [SOURCE_COUNT-1:0] tx_protocol_error;
  wire [SOURCE_COUNT*32-1:0] tx_descriptor_count;

  wire [SOURCE_COUNT-1:0] tx_release_valid;
  wire [SOURCE_COUNT-1:0] tx_release_ready;

  wire [NODES-1:0] mesh_in_valid;
  wire [NODES-1:0] mesh_in_ready;
  wire [NODES*4-1:0] mesh_in_dest;
  wire [NODES*4-1:0] mesh_in_source;
  wire [NODES*TAG_W-1:0] mesh_in_tag;
  wire [NODES*FRAGMENT_W-1:0] mesh_in_fragment;
  wire [NODES-1:0] mesh_in_last;
  wire [NODES*VC_W-1:0] mesh_in_vc;
  wire [NODES*DATA_W-1:0] mesh_in_data;
  wire [NODES-1:0] mesh_out_valid;
  wire [NODES-1:0] mesh_out_ready;
  wire [NODES*4-1:0] mesh_out_dest;
  wire [NODES*4-1:0] mesh_out_source;
  wire [NODES*TAG_W-1:0] mesh_out_tag;
  wire [NODES*FRAGMENT_W-1:0] mesh_out_fragment;
  wire [NODES-1:0] mesh_out_last;
  wire [NODES*VC_W-1:0] mesh_out_vc;
  wire [NODES*DATA_W-1:0] mesh_out_data;
  wire [NODES*32-1:0] router_accepted;
  wire [NODES*32-1:0] router_forwarded;
  wire [NODES*32-1:0] router_input_stall;
  wire [NODES*32-1:0] router_output_stall;
  wire [NODES*32-1:0] router_contention;
  wire [NODES*32-1:0] router_current_occupancy;
  wire [NODES*32-1:0] router_max_occupancy;
  wire [NODES*5*32-1:0] router_route_count;

  wire [SOURCE_COUNT-1:0] source_mesh_in_valid;
  wire [SOURCE_COUNT-1:0] source_mesh_in_ready;
  wire [SOURCE_COUNT*4-1:0] source_mesh_in_dest;
  wire [SOURCE_COUNT*4-1:0] source_mesh_in_source;
  wire [SOURCE_COUNT*TAG_W-1:0] source_mesh_in_tag;
  wire [SOURCE_COUNT*FRAGMENT_W-1:0] source_mesh_in_fragment;
  wire [SOURCE_COUNT-1:0] source_mesh_in_last;
  wire [SOURCE_COUNT*VC_W-1:0] source_mesh_in_vc;
  wire [SOURCE_COUNT*DATA_W-1:0] source_mesh_in_data;
  wire [SOURCE_COUNT-1:0] source_mesh_out_valid;
  wire [SOURCE_COUNT-1:0] source_mesh_out_ready;
  wire [SOURCE_COUNT*4-1:0] source_mesh_out_dest;
  wire [SOURCE_COUNT*4-1:0] source_mesh_out_source;
  wire [SOURCE_COUNT*TAG_W-1:0] source_mesh_out_tag;
  wire [SOURCE_COUNT*FRAGMENT_W-1:0] source_mesh_out_fragment;
  wire [SOURCE_COUNT-1:0] source_mesh_out_last;
  wire [SOURCE_COUNT*VC_W-1:0] source_mesh_out_vc;
  wire [SOURCE_COUNT*DATA_W-1:0] source_mesh_out_data;

  wire composition_mesh_in_valid;
  wire composition_mesh_in_ready;
  wire [3:0] composition_mesh_in_dest;
  wire [3:0] composition_mesh_in_source;
  wire [TAG_W-1:0] composition_mesh_in_tag;
  wire [FRAGMENT_W-1:0] composition_mesh_in_fragment;
  wire composition_mesh_in_last;
  wire [VC_W-1:0] composition_mesh_in_vc;
  wire [DATA_W-1:0] composition_mesh_in_data;
  wire composition_mesh_out_valid;
  wire composition_mesh_out_ready;
  wire [3:0] composition_mesh_out_dest;
  wire [3:0] composition_mesh_out_source;
  wire [TAG_W-1:0] composition_mesh_out_tag;
  wire [FRAGMENT_W-1:0] composition_mesh_out_fragment;
  wire composition_mesh_out_last;
  wire [VC_W-1:0] composition_mesh_out_vc;
  wire [DATA_W-1:0] composition_mesh_out_data;

  wire root_local_valid;
  wire root_local_ready;
  wire [BEAT_W-1:0] root_local_beat_data;
  wire root_valid;
  wire root_ready = 1'b1;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [SOURCE_COUNT-1:0] group_complete;
  wire [SOURCE_COUNT-1:0] descriptor_installed;
  wire [SOURCE_COUNT-1:0] source_protocol_error;
  wire tree_protocol_error;
  wire composition_protocol_error;
  wire [31:0] root_accepted_flit_count;
  wire [31:0] root_descriptor_install_count;
  wire [31:0] root_completion_count;
  wire [31:0] root_replay_packet_count;
  wire [5:0] max_occupied_slots;

  function [BEAT_W-1:0] make_partial_beat(input integer beat_index);
    integer lane;
    reg [BEAT_W-1:0] result;
    begin
      result = {BEAT_W{1'b0}};
      result[15:0] = 16'h5a00;
      result[20:16] = beat_index / 16;
      result[52:21] = 32'd0;
      result[85:53] = 33'd1;
      result[89:86] = beat_index % 16;
      result[90] = ((beat_index % 16) == 15);
      for (lane = 0; lane < 8; lane = lane + 1)
        result[91 + lane*41 +: 41] = 41'd1;
      make_partial_beat = result;
    end
  endfunction

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_source
      localparam integer SOURCE_ID = source_g;
      assign encoder_beat_valid[SOURCE_ID] = !ctx_pending &&
        (source_beat_index[SOURCE_ID] < GROUP_BEATS);
      assign encoder_beat_data[SOURCE_ID*BEAT_W +: BEAT_W] =
        make_partial_beat(source_beat_index[SOURCE_ID]);

      local_reducer_aggregate_stats_once_exact_encoder encoder (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(source_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(encoder_ctx_ready[SOURCE_ID]),
        .group_command_id(16'h5a00), .group_head_base(5'd0),
        .beat_valid(encoder_beat_valid[SOURCE_ID]),
        .beat_ready(encoder_beat_ready[SOURCE_ID]),
        .beat_data(encoder_beat_data[SOURCE_ID*BEAT_W +: BEAT_W]),
        .flit_valid(encoder_flit_valid[SOURCE_ID]),
        .flit_ready(encoder_flit_ready[SOURCE_ID]),
        .flit_data(encoder_flit_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .flit_group_last(encoder_flit_group_last[SOURCE_ID]),
        .protocol_error(encoder_error[SOURCE_ID])
      );

      local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
        .LOCAL_ENDPOINT_ID(SOURCE_ID),
        .TX_ENABLE(1), .RX_ENABLE(0),
        .SRC_BASE_ADDR(0), .DST_BASE_ADDR(4096)
      ) source_tx (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(source_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(source_ctx_ready[SOURCE_ID]),
        .group_command_id(16'h5a00), .group_head_base(5'd0),
        .group_source(SOURCE_ID[3:0]), .group_destination(4'd15),
        .group_vc(2'd0), .group_epoch(3'd0),
        .codec_in_valid(encoder_flit_valid[SOURCE_ID]),
        .codec_in_ready(encoder_flit_ready[SOURCE_ID]),
        .codec_in_data(encoder_flit_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .codec_in_group_last(encoder_flit_group_last[SOURCE_ID]),
        .tx_release_valid(tx_release_valid[SOURCE_ID]),
        .tx_release_ready(tx_release_ready[SOURCE_ID]),
        .codec_out_valid(), .codec_out_ready(1'b0), .codec_out_data(),
        .codec_out_group_last(), .tx_group_complete(tx_group_complete[SOURCE_ID]),
        .rx_group_complete(), .rx_descriptor_installed(),
        .protocol_error(tx_protocol_error[SOURCE_ID]),
        .tx_descriptor_count(tx_descriptor_count[SOURCE_ID*32 +: 32]),
        .rx_completion_count(), .replay_packet_count(),
        .max_source_occupancy(), .max_destination_occupancy(),
        .mesh_in_valid(source_mesh_in_valid[SOURCE_ID]),
        .mesh_in_ready(source_mesh_in_ready[SOURCE_ID]),
        .mesh_in_destination(source_mesh_in_dest[SOURCE_ID*4 +: 4]),
        .mesh_in_source(source_mesh_in_source[SOURCE_ID*4 +: 4]),
        .mesh_in_tag(source_mesh_in_tag[SOURCE_ID*TAG_W +: TAG_W]),
        .mesh_in_fragment(source_mesh_in_fragment[SOURCE_ID*FRAGMENT_W +: FRAGMENT_W]),
        .mesh_in_last(source_mesh_in_last[SOURCE_ID]),
        .mesh_in_vc(source_mesh_in_vc[SOURCE_ID*VC_W +: VC_W]),
        .mesh_in_data(source_mesh_in_data[SOURCE_ID*DATA_W +: DATA_W]),
        .mesh_out_valid(source_mesh_out_valid[SOURCE_ID]),
        .mesh_out_ready(source_mesh_out_ready[SOURCE_ID]),
        .mesh_out_destination(source_mesh_out_dest[SOURCE_ID*4 +: 4]),
        .mesh_out_source(source_mesh_out_source[SOURCE_ID*4 +: 4]),
        .mesh_out_tag(source_mesh_out_tag[SOURCE_ID*TAG_W +: TAG_W]),
        .mesh_out_fragment(source_mesh_out_fragment[SOURCE_ID*FRAGMENT_W +: FRAGMENT_W]),
        .mesh_out_last(source_mesh_out_last[SOURCE_ID]),
        .mesh_out_vc(source_mesh_out_vc[SOURCE_ID*VC_W +: VC_W]),
        .mesh_out_data(source_mesh_out_data[SOURCE_ID*DATA_W +: DATA_W])
      );
    end
  endgenerate

  local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition #(
    .PHYSICAL_BANKS(ROOT_PHYSICAL_BANKS)
  ) composition (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(context_fire),
    .group_ctx_ready(composition_ctx_ready),
    .group_command_id(group_command_id),
    .group_head_base(group_head_base),
    .group_source(group_source),
    .group_destination(group_destination),
    .group_vc(group_vc),
    .group_epoch(group_epoch),
    .tx_release_valid(tx_release_valid),
    .tx_release_ready(tx_release_ready),
    .root_local_valid(root_local_valid),
    .root_local_ready(root_local_ready),
    .root_local_beat_data(root_local_beat_data),
    .mesh_in_valid(composition_mesh_in_valid),
    .mesh_in_ready(composition_mesh_in_ready),
    .mesh_in_destination(composition_mesh_in_dest),
    .mesh_in_source(composition_mesh_in_source),
    .mesh_in_tag(composition_mesh_in_tag),
    .mesh_in_fragment(composition_mesh_in_fragment),
    .mesh_in_last(composition_mesh_in_last),
    .mesh_in_vc(composition_mesh_in_vc),
    .mesh_in_data(composition_mesh_in_data),
    .mesh_out_valid(composition_mesh_out_valid),
    .mesh_out_ready(composition_mesh_out_ready),
    .mesh_out_destination(composition_mesh_out_dest),
    .mesh_out_source(composition_mesh_out_source),
    .mesh_out_tag(composition_mesh_out_tag),
    .mesh_out_fragment(composition_mesh_out_fragment),
    .mesh_out_last(composition_mesh_out_last),
    .mesh_out_vc(composition_mesh_out_vc),
    .mesh_out_data(composition_mesh_out_data),
    .root_valid(root_valid), .root_ready(root_ready),
    .root_command_id(root_command_id), .root_head_id(root_head_id),
    .root_slice(root_slice), .root_last(root_last), .root_value(root_value),
    .group_complete(group_complete),
    .descriptor_installed(descriptor_installed),
    .source_protocol_error(source_protocol_error),
    .tree_protocol_error(tree_protocol_error),
    .protocol_error(composition_protocol_error),
    .root_accepted_flit_count(root_accepted_flit_count),
    .root_descriptor_install_count(root_descriptor_install_count),
    .root_completion_count(root_completion_count),
    .root_replay_packet_count(root_replay_packet_count),
    .max_occupied_slots(max_occupied_slots)
  );

  assign mesh_in_valid[SOURCE_COUNT] = composition_mesh_in_valid;
  assign mesh_in_dest[SOURCE_COUNT*4 +: 4] = composition_mesh_in_dest;
  assign mesh_in_source[SOURCE_COUNT*4 +: 4] = composition_mesh_in_source;
  assign mesh_in_tag[SOURCE_COUNT*TAG_W +: TAG_W] = composition_mesh_in_tag;
  assign mesh_in_fragment[SOURCE_COUNT*FRAGMENT_W +: FRAGMENT_W] = composition_mesh_in_fragment;
  assign mesh_in_last[SOURCE_COUNT] = composition_mesh_in_last;
  assign mesh_in_vc[SOURCE_COUNT*VC_W +: VC_W] = composition_mesh_in_vc;
  assign mesh_in_data[SOURCE_COUNT*DATA_W +: DATA_W] = composition_mesh_in_data;
  assign composition_mesh_in_ready = mesh_in_ready[SOURCE_COUNT];

  assign composition_mesh_out_valid = mesh_out_valid[SOURCE_COUNT];
  assign mesh_out_ready[SOURCE_COUNT] = composition_mesh_out_ready;
  assign composition_mesh_out_dest = mesh_out_dest[SOURCE_COUNT*4 +: 4];
  assign composition_mesh_out_source = mesh_out_source[SOURCE_COUNT*4 +: 4];
  assign composition_mesh_out_tag = mesh_out_tag[SOURCE_COUNT*TAG_W +: TAG_W];
  assign composition_mesh_out_fragment = mesh_out_fragment[SOURCE_COUNT*FRAGMENT_W +: FRAGMENT_W];
  assign composition_mesh_out_last = mesh_out_last[SOURCE_COUNT];
  assign composition_mesh_out_vc = mesh_out_vc[SOURCE_COUNT*VC_W +: VC_W];
  assign composition_mesh_out_data = mesh_out_data[SOURCE_COUNT*DATA_W +: DATA_W];

  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_mesh_map
      assign mesh_in_valid[source_g] = source_mesh_in_valid[source_g];
      assign source_mesh_in_ready[source_g] = mesh_in_ready[source_g];
      assign mesh_in_dest[source_g*4 +: 4] = source_mesh_in_dest[source_g*4 +: 4];
      assign mesh_in_source[source_g*4 +: 4] = source_mesh_in_source[source_g*4 +: 4];
      assign mesh_in_tag[source_g*TAG_W +: TAG_W] = source_mesh_in_tag[source_g*TAG_W +: TAG_W];
      assign mesh_in_fragment[source_g*FRAGMENT_W +: FRAGMENT_W] = source_mesh_in_fragment[source_g*FRAGMENT_W +: FRAGMENT_W];
      assign mesh_in_last[source_g] = source_mesh_in_last[source_g];
      assign mesh_in_vc[source_g*VC_W +: VC_W] = source_mesh_in_vc[source_g*VC_W +: VC_W];
      assign mesh_in_data[source_g*DATA_W +: DATA_W] = source_mesh_in_data[source_g*DATA_W +: DATA_W];
      assign source_mesh_out_valid[source_g] = mesh_out_valid[source_g];
      assign mesh_out_ready[source_g] = source_mesh_out_ready[source_g];
      assign source_mesh_out_dest[source_g*4 +: 4] = mesh_out_dest[source_g*4 +: 4];
      assign source_mesh_out_source[source_g*4 +: 4] = mesh_out_source[source_g*4 +: 4];
      assign source_mesh_out_tag[source_g*TAG_W +: TAG_W] = mesh_out_tag[source_g*TAG_W +: TAG_W];
      assign source_mesh_out_fragment[source_g*FRAGMENT_W +: FRAGMENT_W] = mesh_out_fragment[source_g*FRAGMENT_W +: FRAGMENT_W];
      assign source_mesh_out_last[source_g] = mesh_out_last[source_g];
      assign source_mesh_out_vc[source_g*VC_W +: VC_W] = mesh_out_vc[source_g*VC_W +: VC_W];
      assign source_mesh_out_data[source_g*DATA_W +: DATA_W] = mesh_out_data[source_g*DATA_W +: DATA_W];
    end
  endgenerate

  noc_segmented_mesh4x4 mesh (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(mesh_in_valid), .endpoint_in_ready(mesh_in_ready),
    .endpoint_in_dest(mesh_in_dest), .endpoint_in_source(mesh_in_source),
    .endpoint_in_tag(mesh_in_tag), .endpoint_in_fragment(mesh_in_fragment),
    .endpoint_in_last(mesh_in_last), .endpoint_in_vc(mesh_in_vc),
    .endpoint_in_data(mesh_in_data), .endpoint_out_valid(mesh_out_valid),
    .endpoint_out_ready(mesh_out_ready), .endpoint_out_dest(mesh_out_dest),
    .endpoint_out_source(mesh_out_source), .endpoint_out_tag(mesh_out_tag),
    .endpoint_out_fragment(mesh_out_fragment), .endpoint_out_last(mesh_out_last),
    .endpoint_out_vc(mesh_out_vc), .endpoint_out_data(mesh_out_data),
    .router_accepted_flit_count(router_accepted),
    .router_forwarded_flit_count(router_forwarded),
    .router_input_stall_cycles(router_input_stall),
    .router_output_stall_cycles(router_output_stall),
    .router_contention_cycles(router_contention),
    .router_current_input_occupancy(router_current_occupancy),
    .router_max_input_occupancy(router_max_occupancy),
    .router_route_flit_count(router_route_count)
  );

  reg [31:0] root_beat_index = 0;
  wire root_local_active = !ctx_pending;
  wire root_local_valid_w = root_local_active && (root_beat_index < GROUP_BEATS);
  wire [BEAT_W-1:0] root_local_beat = make_partial_beat(root_beat_index);
  assign root_local_valid = root_local_valid_w;
  assign root_local_beat_data = root_local_beat;

  wire root_local_fire = root_local_valid_w && root_local_ready;

  integer source_i;
  integer lane_i;
  integer root_count = 0;
  integer source_desc_sum;
  reg root_seen_delivery = 1'b0;
  reg [SOURCE_COUNT-1:0] source_mask = {SOURCE_COUNT{1'b0}};
  integer root_first_delivery_cycle = 0;
  integer root_last_delivery_cycle = 0;
  reg [39:0] observed_lane;
  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      ctx_pending <= 1'b1;
      root_beat_index <= 0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        source_beat_index[source_i] <= 0;
    end else begin
      cycle <= cycle + 1;
      if (cycle >= SIM_TIMEOUT_CYCLES) begin
        $display("TIMEOUT banks=%0d root_rows=%0d root_local=%0d flits=%0d desc=%0d comp=%0d replay=%0d slots=%0d source0=%0d source14=%0d",
          ROOT_PHYSICAL_BANKS, root_count, root_beat_index,
          root_accepted_flit_count, root_descriptor_install_count,
          root_completion_count, root_replay_packet_count,
          max_occupied_slots, source_beat_index[0], source_beat_index[14]);
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
          $display("SOURCE %0d next=%0d replay=%0d word=%0d slot=%0d states=%0d/%0d rsp_valid=%0d rsp_ready=%0d read_valid=%0d read_ready=%0d",
            source_i,
            composition.root_rx.next_packet_q[source_i],
            composition.root_rx.replay_active_q[source_i],
            composition.root_rx.replay_word_q[source_i],
            composition.root_rx.replay_slot_q[source_i],
            composition.root_rx.slot_state[source_i][0],
            composition.root_rx.slot_state[source_i][1],
            composition.root_rx.storage_read_rsp_valid_w[source_i],
            composition.root_rx.storage_read_rsp_ready_w[source_i],
            composition.root_rx.storage_read_req_valid_w[source_i],
            composition.root_rx.storage_read_req_ready_w[source_i]);
        $fatal(1, "full-chain shared-root timeout");
      end
      if (context_fire)
        ctx_pending <= 1'b0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        if (encoder_beat_valid[source_i] && encoder_beat_ready[source_i])
          source_beat_index[source_i] <= source_beat_index[source_i] + 1'b1;
      if (root_local_fire)
        root_beat_index <= root_beat_index + 1'b1;

      if (composition_protocol_error || (|encoder_error) ||
          (|tx_protocol_error))
        $fatal(1, "full-chain protocol error");

      if (root_valid && root_ready) begin
        if (root_command_id !== 16'h5a00 ||
            root_head_id !== (root_count / 16) ||
            root_slice !== (root_count % 16) ||
            root_last !== ((root_count % 16) == 15))
          $fatal(1, "root metadata mismatch row=%0d", root_count);
        for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
          observed_lane = root_value[lane_i*40 +: 40];
          if (observed_lane !== 40'd65535)
            $fatal(1, "root lane mismatch row=%0d lane=%0d value=%h",
              root_count, lane_i, observed_lane);
        end
        root_count = root_count + 1;
        if (root_count == GROUP_BEATS) begin
          source_desc_sum = 0;
          for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
            source_desc_sum = source_desc_sum + tx_descriptor_count[source_i*32 +: 32];
          if (root_accepted_flit_count !== SOURCE_COUNT*GROUP_FLITS ||
              root_descriptor_install_count !== SOURCE_COUNT*GROUP_PACKETS ||
              root_completion_count !== SOURCE_COUNT*GROUP_PACKETS ||
              root_replay_packet_count !== SOURCE_COUNT*GROUP_PACKETS ||
              source_desc_sum !== SOURCE_COUNT*GROUP_PACKETS ||
              source_mask !== {SOURCE_COUNT{1'b1}} ||
              (root_last_delivery_cycle - root_first_delivery_cycle + 1) !==
                SOURCE_COUNT*GROUP_FLITS ||
              max_occupied_slots > SOURCE_COUNT*2)
            $fatal(1, "transport count mismatch flits=%0d desc=%0d comp=%0d replay=%0d txdesc=%0d",
              root_accepted_flit_count, root_descriptor_install_count,
              root_completion_count, root_replay_packet_count, source_desc_sum);
          $display("PASS full_chain rows=%0d remote_beats=%0d flits=%0d packets=%0d descriptors=%0d completions=%0d replays=%0d source_mask=%h root_delivery_span=%0d final_cycle=%0d tree_drain_cycles=%0d max_aggregate_slots=%0d slots_per_source=2",
            root_count, SOURCE_COUNT*GROUP_BEATS, root_accepted_flit_count,
            SOURCE_COUNT*GROUP_PACKETS, root_descriptor_install_count,
            root_completion_count, root_replay_packet_count,
            source_mask,
            root_last_delivery_cycle - root_first_delivery_cycle + 1,
            cycle, cycle - root_last_delivery_cycle, max_occupied_slots);
          $finish;
        end
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n && mesh_out_valid[15] && mesh_out_ready[15]) begin
      source_mask[mesh_out_source[15*4 +: 4]] <= 1'b1;
      if (!root_seen_delivery) begin
        root_seen_delivery <= 1'b1;
        root_first_delivery_cycle <= cycle;
      end
      root_last_delivery_cycle <= cycle;
    end
  end

  initial begin
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
      source_beat_index[source_i] = 0;
    repeat (5) @(posedge clk);
    rst_n = 1'b1;
  end
endmodule
