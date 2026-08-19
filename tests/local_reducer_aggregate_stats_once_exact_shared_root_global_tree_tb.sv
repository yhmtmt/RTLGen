`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_global_tree_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer LEAF_COUNT = 16;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer SIM_TIMEOUT_CYCLES = 30000;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg [SOURCE_COUNT-1:0] bridge_ctx_done;
  reg [SOURCE_COUNT-1:0] encoder_ctx_done;
  wire [SOURCE_COUNT-1:0] group_ctx_valid =
    ~(bridge_ctx_done & encoder_ctx_done);
  wire [SOURCE_COUNT-1:0] bridge_group_ctx_ready;
  wire [SOURCE_COUNT-1:0] encoder_group_ctx_ready;
  wire [SOURCE_COUNT*16-1:0] group_command_id =
    {SOURCE_COUNT{16'h5a00}};
  wire [SOURCE_COUNT*5-1:0] group_head_base =
    {SOURCE_COUNT{5'd0}};

  reg [31:0] source_beat_index [0:SOURCE_COUNT-1];
  reg [31:0] root_beat_index;
  wire [SOURCE_COUNT-1:0] encoder_beat_valid;
  wire [SOURCE_COUNT-1:0] encoder_beat_ready;
  wire [SOURCE_COUNT*BEAT_W-1:0] encoder_beat_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_valid;
  wire [SOURCE_COUNT-1:0] encoder_flit_ready;
  wire [SOURCE_COUNT*FLIT_W-1:0] encoder_flit_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_group_last;
  wire [SOURCE_COUNT-1:0] encoder_protocol_error;

  wire [LEAF_COUNT-1:0] leaf_valid;
  wire [LEAF_COUNT-1:0] leaf_ready;
  wire [LEAF_COUNT*16-1:0] leaf_command_id;
  wire [LEAF_COUNT*5-1:0] leaf_head_id;
  wire [LEAF_COUNT*32-1:0] leaf_global_max;
  wire [LEAF_COUNT*33-1:0] leaf_exp_sum;
  wire [LEAF_COUNT*4-1:0] leaf_slice;
  wire [LEAF_COUNT-1:0] leaf_last;
  wire [LEAF_COUNT*328-1:0] leaf_value;
  wire [SOURCE_COUNT-1:0] decoder_protocol_error;
  wire bridge_protocol_error;

  wire root_valid;
  wire root_ready = ((cycle % 17) != 5) && ((cycle % 23) != 11);
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire tree_protocol_error;

  integer source_i;
  integer lane_i;
  integer root_count = 0;
  reg [39:0] observed_lane;

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
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_encoder
      assign encoder_beat_valid[source_g] = encoder_ctx_done[source_g] &&
        (source_beat_index[source_g] < GROUP_BEATS);
      assign encoder_beat_data[source_g*BEAT_W +: BEAT_W] =
        make_partial_beat(source_beat_index[source_g]);

      local_reducer_aggregate_stats_once_exact_encoder encoder (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid[source_g]),
        .group_ctx_ready(encoder_group_ctx_ready[source_g]),
        .group_command_id(16'h5a00), .group_head_base(5'd0),
        .beat_valid(encoder_beat_valid[source_g]),
        .beat_ready(encoder_beat_ready[source_g]),
        .beat_data(encoder_beat_data[source_g*BEAT_W +: BEAT_W]),
        .flit_valid(encoder_flit_valid[source_g]),
        .flit_ready(encoder_flit_ready[source_g]),
        .flit_data(encoder_flit_data[source_g*FLIT_W +: FLIT_W]),
        .flit_group_last(encoder_flit_group_last[source_g]),
        .protocol_error(encoder_protocol_error[source_g])
      );
    end
  endgenerate

  wire root_local_valid = root_beat_index < GROUP_BEATS;
  wire root_local_ready;
  wire [BEAT_W-1:0] root_local_beat_data =
    make_partial_beat(root_beat_index);

  local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter bridge (
    .clk(clk), .rst_n(rst_n),
    .source_group_ctx_valid(group_ctx_valid),
    .source_group_ctx_ready(bridge_group_ctx_ready),
    .source_group_command_id(group_command_id),
    .source_group_head_base(group_head_base),
    .source_flit_valid(encoder_flit_valid),
    .source_flit_ready(encoder_flit_ready),
    .source_flit_data(encoder_flit_data),
    .source_flit_group_last(encoder_flit_group_last),
    .decoder_protocol_error(decoder_protocol_error),
    .root_local_valid(root_local_valid),
    .root_local_ready(root_local_ready),
    .root_local_beat_data(root_local_beat_data),
    .leaf_valid(leaf_valid), .leaf_ready(leaf_ready),
    .leaf_command_id(leaf_command_id), .leaf_head_id(leaf_head_id),
    .leaf_global_max(leaf_global_max), .leaf_exp_sum(leaf_exp_sum),
    .leaf_slice(leaf_slice), .leaf_last(leaf_last),
    .leaf_value(leaf_value), .protocol_error(bridge_protocol_error)
  );

  attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59 tree (
    .clk(clk), .rst_n(rst_n),
    .leaf_valid(leaf_valid), .leaf_ready(leaf_ready),
    .leaf_command_id(leaf_command_id), .leaf_head_id(leaf_head_id),
    .leaf_global_max(leaf_global_max), .leaf_exp_sum(leaf_exp_sum),
    .leaf_slice(leaf_slice), .leaf_last(leaf_last),
    .leaf_value(leaf_value),
    .root_valid(root_valid), .root_ready(root_ready),
    .root_command_id(root_command_id), .root_head_id(root_head_id),
    .root_slice(root_slice), .root_last(root_last), .root_value(root_value),
    .protocol_error(tree_protocol_error)
  );

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      bridge_ctx_done <= {SOURCE_COUNT{1'b0}};
      encoder_ctx_done <= {SOURCE_COUNT{1'b0}};
      root_beat_index <= 0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        source_beat_index[source_i] <= 0;
    end else begin
      cycle <= cycle + 1;
      if (cycle >= SIM_TIMEOUT_CYCLES)
        $fatal(1, "shared-root global-tree timeout");
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
        if (group_ctx_valid[source_i] && bridge_group_ctx_ready[source_i])
          bridge_ctx_done[source_i] <= 1'b1;
        if (group_ctx_valid[source_i] && encoder_group_ctx_ready[source_i])
          encoder_ctx_done[source_i] <= 1'b1;
        if (encoder_beat_valid[source_i] && encoder_beat_ready[source_i])
          source_beat_index[source_i] <= source_beat_index[source_i] + 1'b1;
      end
      if (root_local_valid && root_local_ready)
        root_beat_index <= root_beat_index + 1'b1;

      if (bridge_protocol_error || tree_protocol_error ||
          (|encoder_protocol_error) || (|decoder_protocol_error))
        $fatal(1, "unexpected composed protocol error");

      if (root_valid && root_ready) begin
        if (root_command_id !== 16'h5a00 ||
            root_head_id !== (root_count / 16) ||
            root_slice !== (root_count % 16) ||
            root_last !== ((root_count % 16) == 15))
          $fatal(1, "root metadata mismatch at row %0d", root_count);
        for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
          observed_lane = root_value[lane_i*40 +: 40];
          if (observed_lane !== 40'd65535)
            $fatal(1, "root lane mismatch row=%0d lane=%0d value=%h",
              root_count, lane_i, observed_lane);
        end
        root_count = root_count + 1;
        if (root_count == GROUP_BEATS) begin
          $display("PASS shared_root_global_tree rows=128 lane_value=65535 cycles=%0d",
            cycle);
          $finish;
        end
      end
    end
  end

  initial begin
    bridge_ctx_done = {SOURCE_COUNT{1'b0}};
    encoder_ctx_done = {SOURCE_COUNT{1'b0}};
    root_beat_index = 0;
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
      source_beat_index[source_i] = 0;
    repeat (5) @(posedge clk);
    rst_n = 1'b1;
  end
endmodule
