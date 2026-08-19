`timescale 1ns/1ps

// Convert the fifteen shared-root deframed codec streams into the sixteen
// packed leaf streams consumed by the exact global reduction tree.  Leaves
// zero through fourteen are decoded independently; leaf fifteen is a direct
// canonical stream from the root-local producer.
module local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter #(
  parameter integer SOURCE_COUNT = 15,
  parameter integer LEAF_COUNT = 16,
  parameter integer BEAT_W = 419,
  parameter integer FLIT_W = 256,
  parameter integer RESERVOIR_W = 768
) (
  input wire clk,
  input wire rst_n,

  input wire [SOURCE_COUNT-1:0] source_group_ctx_valid,
  output wire [SOURCE_COUNT-1:0] source_group_ctx_ready,
  input wire [SOURCE_COUNT*16-1:0] source_group_command_id,
  input wire [SOURCE_COUNT*5-1:0] source_group_head_base,
  input wire [SOURCE_COUNT-1:0] source_flit_valid,
  output wire [SOURCE_COUNT-1:0] source_flit_ready,
  input wire [SOURCE_COUNT*FLIT_W-1:0] source_flit_data,
  input wire [SOURCE_COUNT-1:0] source_flit_group_last,
  output wire [SOURCE_COUNT-1:0] decoder_protocol_error,

  input wire root_local_valid,
  output wire root_local_ready,
  input wire [BEAT_W-1:0] root_local_beat_data,

  output wire [LEAF_COUNT-1:0] leaf_valid,
  input wire [LEAF_COUNT-1:0] leaf_ready,
  output wire [LEAF_COUNT*16-1:0] leaf_command_id,
  output wire [LEAF_COUNT*5-1:0] leaf_head_id,
  output wire [LEAF_COUNT*32-1:0] leaf_global_max,
  output wire [LEAF_COUNT*33-1:0] leaf_exp_sum,
  output wire [LEAF_COUNT*4-1:0] leaf_slice,
  output wire [LEAF_COUNT-1:0] leaf_last,
  output wire [LEAF_COUNT*328-1:0] leaf_value,
  output wire protocol_error
);
  wire [SOURCE_COUNT-1:0] decoder_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] decoder_flit_ready_w;
  wire [SOURCE_COUNT-1:0] decoder_beat_valid_w;
  wire [SOURCE_COUNT-1:0] decoder_beat_ready_w;
  wire [SOURCE_COUNT*BEAT_W-1:0] decoder_beat_data_w;

  assign source_group_ctx_ready = decoder_ctx_ready_w;
  assign source_flit_ready = decoder_flit_ready_w;
  assign root_local_ready = leaf_ready[SOURCE_COUNT];

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_decoder
      local_reducer_aggregate_stats_once_exact_decoder #(
        .BEAT_W(BEAT_W),
        .FLIT_W(FLIT_W),
        .RESERVOIR_W(RESERVOIR_W)
      ) decoder (
        .clk(clk),
        .rst_n(rst_n),
        .group_ctx_valid(source_group_ctx_valid[source_g]),
        .group_ctx_ready(decoder_ctx_ready_w[source_g]),
        .group_command_id(source_group_command_id[source_g*16 +: 16]),
        .group_head_base(source_group_head_base[source_g*5 +: 5]),
        .flit_valid(source_flit_valid[source_g]),
        .flit_ready(decoder_flit_ready_w[source_g]),
        .flit_data(source_flit_data[source_g*FLIT_W +: FLIT_W]),
        .flit_group_last(source_flit_group_last[source_g]),
        .beat_valid(decoder_beat_valid_w[source_g]),
        .beat_ready(decoder_beat_ready_w[source_g]),
        .beat_data(decoder_beat_data_w[source_g*BEAT_W +: BEAT_W]),
        .protocol_error(decoder_protocol_error[source_g])
      );

      assign decoder_beat_ready_w[source_g] = leaf_ready[source_g];
      assign leaf_valid[source_g] = decoder_beat_valid_w[source_g];
      assign leaf_command_id[source_g*16 +: 16] =
        decoder_beat_data_w[source_g*BEAT_W + 0 +: 16];
      assign leaf_head_id[source_g*5 +: 5] =
        decoder_beat_data_w[source_g*BEAT_W + 16 +: 5];
      assign leaf_global_max[source_g*32 +: 32] =
        decoder_beat_data_w[source_g*BEAT_W + 21 +: 32];
      assign leaf_exp_sum[source_g*33 +: 33] =
        decoder_beat_data_w[source_g*BEAT_W + 53 +: 33];
      assign leaf_slice[source_g*4 +: 4] =
        decoder_beat_data_w[source_g*BEAT_W + 86 +: 4];
      assign leaf_last[source_g] =
        decoder_beat_data_w[source_g*BEAT_W + 90];
      assign leaf_value[source_g*328 +: 328] =
        decoder_beat_data_w[source_g*BEAT_W + 91 +: 328];
    end
  endgenerate

  assign leaf_valid[SOURCE_COUNT] = root_local_valid;
  assign leaf_command_id[SOURCE_COUNT*16 +: 16] = root_local_beat_data[15:0];
  assign leaf_head_id[SOURCE_COUNT*5 +: 5] = root_local_beat_data[20:16];
  assign leaf_global_max[SOURCE_COUNT*32 +: 32] = root_local_beat_data[52:21];
  assign leaf_exp_sum[SOURCE_COUNT*33 +: 33] = root_local_beat_data[85:53];
  assign leaf_slice[SOURCE_COUNT*4 +: 4] = root_local_beat_data[89:86];
  assign leaf_last[SOURCE_COUNT] = root_local_beat_data[90];
  assign leaf_value[SOURCE_COUNT*328 +: 328] = root_local_beat_data[BEAT_W-1:91];

  assign protocol_error = |decoder_protocol_error;

`ifndef SYNTHESIS
  initial begin
    if (SOURCE_COUNT != 15 || LEAF_COUNT != 16) begin
      $error("shared-root leaf adapter requires 15 remote sources and 16 leaves");
      $finish(1);
    end
    if (BEAT_W != 419) begin
      $error("shared-root leaf adapter BEAT_W must be 419");
      $finish(1);
    end
    if (FLIT_W != 256) begin
      $error("shared-root leaf adapter FLIT_W must be 256");
      $finish(1);
    end
  end
`endif
endmodule
