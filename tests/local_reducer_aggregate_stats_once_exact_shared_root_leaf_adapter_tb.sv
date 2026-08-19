`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer LEAF_COUNT = 16;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer SIM_TIMEOUT_CYCLES = 2000000;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg [SOURCE_COUNT-1:0] group_ctx_valid;
  wire [SOURCE_COUNT-1:0] bridge_group_ctx_ready;
  wire [SOURCE_COUNT-1:0] encoder_group_ctx_ready;
  reg [SOURCE_COUNT-1:0] bridge_ctx_done;
  reg [SOURCE_COUNT-1:0] encoder_ctx_done;
  reg [SOURCE_COUNT*16-1:0] group_command_id;
  reg [SOURCE_COUNT*5-1:0] group_head_base;

  reg [SOURCE_COUNT-1:0] encoder_beat_valid;
  wire [SOURCE_COUNT-1:0] encoder_beat_ready;
  reg [SOURCE_COUNT*BEAT_W-1:0] encoder_beat_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_valid;
  wire [SOURCE_COUNT-1:0] encoder_flit_ready;
  wire [SOURCE_COUNT*FLIT_W-1:0] encoder_flit_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_group_last;
  wire [SOURCE_COUNT-1:0] encoder_protocol_error;

  reg [SOURCE_COUNT-1:0] source_flit_valid;
  wire [SOURCE_COUNT-1:0] source_flit_ready;
  reg [SOURCE_COUNT*FLIT_W-1:0] source_flit_data;
  reg [SOURCE_COUNT-1:0] source_flit_group_last;

  wire [LEAF_COUNT-1:0] leaf_valid;
  reg [LEAF_COUNT-1:0] leaf_ready;
  wire [LEAF_COUNT*16-1:0] leaf_command_id;
  wire [LEAF_COUNT*5-1:0] leaf_head_id;
  wire [LEAF_COUNT*32-1:0] leaf_global_max;
  wire [LEAF_COUNT*33-1:0] leaf_exp_sum;
  wire [LEAF_COUNT*4-1:0] leaf_slice;
  wire [LEAF_COUNT-1:0] leaf_last;
  wire [LEAF_COUNT*328-1:0] leaf_value;
  wire [SOURCE_COUNT-1:0] decoder_protocol_error;
  wire protocol_error;

  reg [31:0] source_beat_index [0:SOURCE_COUNT-1];
  reg [31:0] root_beat_index;
  integer leaf_beat_count [0:LEAF_COUNT-1];
  integer source_i;
  integer leaf_i;
  integer word_i;
  reg [BEAT_W-1:0] expected_beat;
  reg held_valid [0:LEAF_COUNT-1];
  reg [15:0] held_command [0:LEAF_COUNT-1];
  reg [4:0] held_head [0:LEAF_COUNT-1];
  reg [31:0] held_max [0:LEAF_COUNT-1];
  reg [32:0] held_sum [0:LEAF_COUNT-1];
  reg [3:0] held_slice [0:LEAF_COUNT-1];
  reg held_last [0:LEAF_COUNT-1];
  reg [327:0] held_value [0:LEAF_COUNT-1];

  function [BEAT_W-1:0] make_beat(input integer source, input integer beat_index);
    integer head_index;
    integer slice_index;
    reg [BEAT_W-1:0] result;
    begin
      head_index = beat_index / 16;
      slice_index = beat_index % 16;
      result = {BEAT_W{1'b0}};
      result[15:0] = 16'h4000 + source;
      result[20:16] = ((source % 4) * 8) + head_index;
      result[52:21] = 32'ha0000000 |
        (source * 32'h00010000) | (head_index * 32'h00000100);
      result[85:53] = 33'h100000000 |
        (source * 33'h00010000) | (head_index * 33'h00000100);
      result[89:86] = slice_index;
      result[90] = (slice_index == 15);
      for (word_i = 0; word_i < 10; word_i = word_i + 1)
        result[91 + word_i*32 +: 32] =
          32'h51000000 | (source * 32'h00100000) |
          (beat_index * 32'h00000100) | word_i;
      result[411 +: 8] = (source * 8) + slice_index;
      make_beat = result;
    end
  endfunction

  always @* begin
    group_ctx_valid = {SOURCE_COUNT{1'b0}};
    group_command_id = {SOURCE_COUNT*16{1'b0}};
    group_head_base = {SOURCE_COUNT*5{1'b0}};
    encoder_beat_valid = {SOURCE_COUNT{1'b0}};
    encoder_beat_data = {SOURCE_COUNT*BEAT_W{1'b0}};
    source_flit_valid = encoder_flit_valid;
    source_flit_data = encoder_flit_data;
    source_flit_group_last = encoder_flit_group_last;
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
      group_ctx_valid[source_i] =
        !(bridge_ctx_done[source_i] && encoder_ctx_done[source_i]);
      group_command_id[source_i*16 +: 16] = 16'h4000 + source_i;
      group_head_base[source_i*5 +: 5] = (source_i % 4) * 8;
      encoder_beat_valid[source_i] = encoder_ctx_done[source_i] &&
        (source_beat_index[source_i] < GROUP_BEATS);
      encoder_beat_data[source_i*BEAT_W +: BEAT_W] =
        make_beat(source_i, source_beat_index[source_i]);
    end
  end

  always @* begin
    for (leaf_i = 0; leaf_i < LEAF_COUNT; leaf_i = leaf_i + 1)
      // Each leaf has a distinct deterministic stall pattern.
      leaf_ready[leaf_i] = ((cycle + leaf_i * 3) % 11 != 0) &&
        ((cycle + leaf_i * 5) % 17 != 3);
  end

  assign encoder_flit_ready = source_flit_ready;

  wire root_local_valid = (root_beat_index < GROUP_BEATS);
  wire root_local_ready;
  wire [BEAT_W-1:0] root_local_beat_data =
    make_beat(SOURCE_COUNT, root_beat_index);

  always @(posedge clk) begin
    if (!rst_n) begin
      bridge_ctx_done <= {SOURCE_COUNT{1'b0}};
      encoder_ctx_done <= {SOURCE_COUNT{1'b0}};
      root_beat_index <= 0;
      cycle <= 0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        source_beat_index[source_i] <= 0;
    end else begin
      cycle <= cycle + 1;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
        if (group_ctx_valid[source_i] && bridge_group_ctx_ready[source_i])
          bridge_ctx_done[source_i] <= 1'b1;
        if (group_ctx_valid[source_i] && encoder_group_ctx_ready[source_i])
          encoder_ctx_done[source_i] <= 1'b1;
        if (encoder_beat_valid[source_i] && encoder_beat_ready[source_i])
          source_beat_index[source_i] <= source_beat_index[source_i] + 1;
      end
      if (root_local_valid && root_local_ready)
        root_beat_index <= root_beat_index + 1;
    end
  end

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_encoder
      local_reducer_aggregate_stats_once_exact_encoder encoder (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid[source_g]),
        .group_ctx_ready(encoder_group_ctx_ready[source_g]),
        .group_command_id(group_command_id[source_g*16 +: 16]),
        .group_head_base(group_head_base[source_g*5 +: 5]),
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

  local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter bridge (
    .clk(clk), .rst_n(rst_n),
    .source_group_ctx_valid(group_ctx_valid),
    .source_group_ctx_ready(bridge_group_ctx_ready),
    .source_group_command_id(group_command_id),
    .source_group_head_base(group_head_base),
    .source_flit_valid(source_flit_valid),
    .source_flit_ready(source_flit_ready),
    .source_flit_data(source_flit_data),
    .source_flit_group_last(source_flit_group_last),
    .decoder_protocol_error(decoder_protocol_error),
    .root_local_valid(root_local_valid),
    .root_local_ready(root_local_ready),
    .root_local_beat_data(root_local_beat_data),
    .leaf_valid(leaf_valid), .leaf_ready(leaf_ready),
    .leaf_command_id(leaf_command_id), .leaf_head_id(leaf_head_id),
    .leaf_global_max(leaf_global_max), .leaf_exp_sum(leaf_exp_sum),
    .leaf_slice(leaf_slice), .leaf_last(leaf_last), .leaf_value(leaf_value),
    .protocol_error(protocol_error)
  );

  initial begin
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
      source_beat_index[source_i] = 0;
    for (leaf_i = 0; leaf_i < LEAF_COUNT; leaf_i = leaf_i + 1) begin
      leaf_beat_count[leaf_i] = 0;
      held_valid[leaf_i] = 1'b0;
    end
    root_beat_index = 0;
    bridge_ctx_done = {SOURCE_COUNT{1'b0}};
    encoder_ctx_done = {SOURCE_COUNT{1'b0}};
    repeat (5) @(posedge clk);
    rst_n = 1'b1;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (cycle > SIM_TIMEOUT_CYCLES)
        $fatal(1, "TIMEOUT shared-root leaf adapter");

      for (leaf_i = 0; leaf_i < LEAF_COUNT; leaf_i = leaf_i + 1) begin
        if (held_valid[leaf_i]) begin
          if (!leaf_valid[leaf_i] ||
              leaf_command_id[leaf_i*16 +: 16] !== held_command[leaf_i] ||
              leaf_head_id[leaf_i*5 +: 5] !== held_head[leaf_i] ||
              leaf_global_max[leaf_i*32 +: 32] !== held_max[leaf_i] ||
              leaf_exp_sum[leaf_i*33 +: 33] !== held_sum[leaf_i] ||
              leaf_slice[leaf_i*4 +: 4] !== held_slice[leaf_i] ||
              leaf_last[leaf_i] !== held_last[leaf_i] ||
              leaf_value[leaf_i*328 +: 328] !== held_value[leaf_i])
            $fatal(1, "leaf %0d changed while stalled", leaf_i);
        end

        if (leaf_valid[leaf_i] && leaf_ready[leaf_i]) begin
          expected_beat = make_beat(leaf_i, leaf_beat_count[leaf_i]);
          if (leaf_command_id[leaf_i*16 +: 16] !== expected_beat[15:0] ||
              leaf_head_id[leaf_i*5 +: 5] !== expected_beat[20:16] ||
              leaf_global_max[leaf_i*32 +: 32] !== expected_beat[52:21] ||
              leaf_exp_sum[leaf_i*33 +: 33] !== expected_beat[85:53] ||
              leaf_slice[leaf_i*4 +: 4] !== expected_beat[89:86] ||
              leaf_last[leaf_i] !== expected_beat[90] ||
              leaf_value[leaf_i*328 +: 328] !== expected_beat[BEAT_W-1:91])
            $fatal(1, "leaf %0d mapping mismatch at beat %0d", leaf_i,
              leaf_beat_count[leaf_i]);
          leaf_beat_count[leaf_i] = leaf_beat_count[leaf_i] + 1;
          held_valid[leaf_i] = 1'b0;
        end else if (leaf_valid[leaf_i]) begin
          held_valid[leaf_i] = 1'b1;
          held_command[leaf_i] = leaf_command_id[leaf_i*16 +: 16];
          held_head[leaf_i] = leaf_head_id[leaf_i*5 +: 5];
          held_max[leaf_i] = leaf_global_max[leaf_i*32 +: 32];
          held_sum[leaf_i] = leaf_exp_sum[leaf_i*33 +: 33];
          held_slice[leaf_i] = leaf_slice[leaf_i*4 +: 4];
          held_last[leaf_i] = leaf_last[leaf_i];
          held_value[leaf_i] = leaf_value[leaf_i*328 +: 328];
        end
      end

      if (protocol_error !== 1'b0 || |encoder_protocol_error)
        $fatal(1, "unexpected protocol error");

      if (leaf_beat_count[0] == GROUP_BEATS &&
          leaf_beat_count[1] == GROUP_BEATS &&
          leaf_beat_count[2] == GROUP_BEATS &&
          leaf_beat_count[3] == GROUP_BEATS &&
          leaf_beat_count[4] == GROUP_BEATS &&
          leaf_beat_count[5] == GROUP_BEATS &&
          leaf_beat_count[6] == GROUP_BEATS &&
          leaf_beat_count[7] == GROUP_BEATS &&
          leaf_beat_count[8] == GROUP_BEATS &&
          leaf_beat_count[9] == GROUP_BEATS &&
          leaf_beat_count[10] == GROUP_BEATS &&
          leaf_beat_count[11] == GROUP_BEATS &&
          leaf_beat_count[12] == GROUP_BEATS &&
          leaf_beat_count[13] == GROUP_BEATS &&
          leaf_beat_count[14] == GROUP_BEATS &&
          leaf_beat_count[15] == GROUP_BEATS) begin
        $display("PASS shared_root_leaf_adapter leaves=%0d beats_per_leaf=%0d",
          LEAF_COUNT, GROUP_BEATS);
        $finish;
      end
    end
  end
endmodule
