`timescale 1ns/1ps
module decoder_r64_k1_ranktree_radix2_pipe6_wrapper(
  input clk,
  input rst_n,
  input in_valid,
  output in_ready,
  input in_last,
  input [15:0] in_base_token_id,
  input [63:0] in_lane_valid,
  input signed [1023:0] in_logits,
  output out_valid,
  input out_ready,
  output out_valid_mask,
  output [15:0] out_token_ids,
  output signed [15:0] out_logits,
  output [31:0] accepted_group_count,
  output [31:0] producer_stall_cycles,
  output [31:0] fifo_max_occupancy,
  output [31:0] final_completion_cycle
);
  wire signed [1023:0] masked_logits;
  assign masked_logits[0 +: 16] = in_lane_valid[0] ? in_logits[0 +: 16] : -16'sd32768;
  assign masked_logits[16 +: 16] = in_lane_valid[1] ? in_logits[16 +: 16] : -16'sd32768;
  assign masked_logits[32 +: 16] = in_lane_valid[2] ? in_logits[32 +: 16] : -16'sd32768;
  assign masked_logits[48 +: 16] = in_lane_valid[3] ? in_logits[48 +: 16] : -16'sd32768;
  assign masked_logits[64 +: 16] = in_lane_valid[4] ? in_logits[64 +: 16] : -16'sd32768;
  assign masked_logits[80 +: 16] = in_lane_valid[5] ? in_logits[80 +: 16] : -16'sd32768;
  assign masked_logits[96 +: 16] = in_lane_valid[6] ? in_logits[96 +: 16] : -16'sd32768;
  assign masked_logits[112 +: 16] = in_lane_valid[7] ? in_logits[112 +: 16] : -16'sd32768;
  assign masked_logits[128 +: 16] = in_lane_valid[8] ? in_logits[128 +: 16] : -16'sd32768;
  assign masked_logits[144 +: 16] = in_lane_valid[9] ? in_logits[144 +: 16] : -16'sd32768;
  assign masked_logits[160 +: 16] = in_lane_valid[10] ? in_logits[160 +: 16] : -16'sd32768;
  assign masked_logits[176 +: 16] = in_lane_valid[11] ? in_logits[176 +: 16] : -16'sd32768;
  assign masked_logits[192 +: 16] = in_lane_valid[12] ? in_logits[192 +: 16] : -16'sd32768;
  assign masked_logits[208 +: 16] = in_lane_valid[13] ? in_logits[208 +: 16] : -16'sd32768;
  assign masked_logits[224 +: 16] = in_lane_valid[14] ? in_logits[224 +: 16] : -16'sd32768;
  assign masked_logits[240 +: 16] = in_lane_valid[15] ? in_logits[240 +: 16] : -16'sd32768;
  assign masked_logits[256 +: 16] = in_lane_valid[16] ? in_logits[256 +: 16] : -16'sd32768;
  assign masked_logits[272 +: 16] = in_lane_valid[17] ? in_logits[272 +: 16] : -16'sd32768;
  assign masked_logits[288 +: 16] = in_lane_valid[18] ? in_logits[288 +: 16] : -16'sd32768;
  assign masked_logits[304 +: 16] = in_lane_valid[19] ? in_logits[304 +: 16] : -16'sd32768;
  assign masked_logits[320 +: 16] = in_lane_valid[20] ? in_logits[320 +: 16] : -16'sd32768;
  assign masked_logits[336 +: 16] = in_lane_valid[21] ? in_logits[336 +: 16] : -16'sd32768;
  assign masked_logits[352 +: 16] = in_lane_valid[22] ? in_logits[352 +: 16] : -16'sd32768;
  assign masked_logits[368 +: 16] = in_lane_valid[23] ? in_logits[368 +: 16] : -16'sd32768;
  assign masked_logits[384 +: 16] = in_lane_valid[24] ? in_logits[384 +: 16] : -16'sd32768;
  assign masked_logits[400 +: 16] = in_lane_valid[25] ? in_logits[400 +: 16] : -16'sd32768;
  assign masked_logits[416 +: 16] = in_lane_valid[26] ? in_logits[416 +: 16] : -16'sd32768;
  assign masked_logits[432 +: 16] = in_lane_valid[27] ? in_logits[432 +: 16] : -16'sd32768;
  assign masked_logits[448 +: 16] = in_lane_valid[28] ? in_logits[448 +: 16] : -16'sd32768;
  assign masked_logits[464 +: 16] = in_lane_valid[29] ? in_logits[464 +: 16] : -16'sd32768;
  assign masked_logits[480 +: 16] = in_lane_valid[30] ? in_logits[480 +: 16] : -16'sd32768;
  assign masked_logits[496 +: 16] = in_lane_valid[31] ? in_logits[496 +: 16] : -16'sd32768;
  assign masked_logits[512 +: 16] = in_lane_valid[32] ? in_logits[512 +: 16] : -16'sd32768;
  assign masked_logits[528 +: 16] = in_lane_valid[33] ? in_logits[528 +: 16] : -16'sd32768;
  assign masked_logits[544 +: 16] = in_lane_valid[34] ? in_logits[544 +: 16] : -16'sd32768;
  assign masked_logits[560 +: 16] = in_lane_valid[35] ? in_logits[560 +: 16] : -16'sd32768;
  assign masked_logits[576 +: 16] = in_lane_valid[36] ? in_logits[576 +: 16] : -16'sd32768;
  assign masked_logits[592 +: 16] = in_lane_valid[37] ? in_logits[592 +: 16] : -16'sd32768;
  assign masked_logits[608 +: 16] = in_lane_valid[38] ? in_logits[608 +: 16] : -16'sd32768;
  assign masked_logits[624 +: 16] = in_lane_valid[39] ? in_logits[624 +: 16] : -16'sd32768;
  assign masked_logits[640 +: 16] = in_lane_valid[40] ? in_logits[640 +: 16] : -16'sd32768;
  assign masked_logits[656 +: 16] = in_lane_valid[41] ? in_logits[656 +: 16] : -16'sd32768;
  assign masked_logits[672 +: 16] = in_lane_valid[42] ? in_logits[672 +: 16] : -16'sd32768;
  assign masked_logits[688 +: 16] = in_lane_valid[43] ? in_logits[688 +: 16] : -16'sd32768;
  assign masked_logits[704 +: 16] = in_lane_valid[44] ? in_logits[704 +: 16] : -16'sd32768;
  assign masked_logits[720 +: 16] = in_lane_valid[45] ? in_logits[720 +: 16] : -16'sd32768;
  assign masked_logits[736 +: 16] = in_lane_valid[46] ? in_logits[736 +: 16] : -16'sd32768;
  assign masked_logits[752 +: 16] = in_lane_valid[47] ? in_logits[752 +: 16] : -16'sd32768;
  assign masked_logits[768 +: 16] = in_lane_valid[48] ? in_logits[768 +: 16] : -16'sd32768;
  assign masked_logits[784 +: 16] = in_lane_valid[49] ? in_logits[784 +: 16] : -16'sd32768;
  assign masked_logits[800 +: 16] = in_lane_valid[50] ? in_logits[800 +: 16] : -16'sd32768;
  assign masked_logits[816 +: 16] = in_lane_valid[51] ? in_logits[816 +: 16] : -16'sd32768;
  assign masked_logits[832 +: 16] = in_lane_valid[52] ? in_logits[832 +: 16] : -16'sd32768;
  assign masked_logits[848 +: 16] = in_lane_valid[53] ? in_logits[848 +: 16] : -16'sd32768;
  assign masked_logits[864 +: 16] = in_lane_valid[54] ? in_logits[864 +: 16] : -16'sd32768;
  assign masked_logits[880 +: 16] = in_lane_valid[55] ? in_logits[880 +: 16] : -16'sd32768;
  assign masked_logits[896 +: 16] = in_lane_valid[56] ? in_logits[896 +: 16] : -16'sd32768;
  assign masked_logits[912 +: 16] = in_lane_valid[57] ? in_logits[912 +: 16] : -16'sd32768;
  assign masked_logits[928 +: 16] = in_lane_valid[58] ? in_logits[928 +: 16] : -16'sd32768;
  assign masked_logits[944 +: 16] = in_lane_valid[59] ? in_logits[944 +: 16] : -16'sd32768;
  assign masked_logits[960 +: 16] = in_lane_valid[60] ? in_logits[960 +: 16] : -16'sd32768;
  assign masked_logits[976 +: 16] = in_lane_valid[61] ? in_logits[976 +: 16] : -16'sd32768;
  assign masked_logits[992 +: 16] = in_lane_valid[62] ? in_logits[992 +: 16] : -16'sd32768;
  assign masked_logits[1008 +: 16] = in_lane_valid[63] ? in_logits[1008 +: 16] : -16'sd32768;
  wire merge_in_ready;
  reg stage1_valid;
  reg stage1_last;
  reg signed [511:0] stage1_logits;
  reg [511:0] stage1_token_ids;
  reg stage2_valid;
  reg stage2_last;
  reg signed [255:0] stage2_logits;
  reg [255:0] stage2_token_ids;
  reg stage3_valid;
  reg stage3_last;
  reg signed [127:0] stage3_logits;
  reg [127:0] stage3_token_ids;
  reg stage4_valid;
  reg stage4_last;
  reg signed [63:0] stage4_logits;
  reg [63:0] stage4_token_ids;
  reg stage5_valid;
  reg stage5_last;
  reg signed [31:0] stage5_logits;
  reg [31:0] stage5_token_ids;
  reg stage6_valid;
  reg stage6_last;
  reg signed [15:0] stage6_logits;
  reg [15:0] stage6_token_ids;
  wire stage6_ready = !stage6_valid || merge_in_ready;
  wire stage5_ready = !stage5_valid || stage6_ready;
  wire stage4_ready = !stage4_valid || stage5_ready;
  wire stage3_ready = !stage3_valid || stage4_ready;
  wire stage2_ready = !stage2_valid || stage3_ready;
  wire stage1_ready = !stage1_valid || stage2_ready;
  assign in_ready = stage1_ready;

  wire signed [511:0] level0_logits;
  reg [511:0] level0_token_ids;
  wire [0:0] level0_index_0;
  logit_rank_r2_l16_k1 rank_l0_g0 (
    .logits(masked_logits[0 +: 32]),
    .top_indices(level0_index_0),
    .top_logits(level0_logits[0 +: 16])
  );
  always @* begin
    case (level0_index_0)
      1'd0: level0_token_ids[0 +: 16] = in_base_token_id + 16'd0;
      1'd1: level0_token_ids[0 +: 16] = in_base_token_id + 16'd1;
      default: level0_token_ids[0 +: 16] = in_base_token_id + 16'd0;
    endcase
  end
  wire [0:0] level0_index_1;
  logit_rank_r2_l16_k1 rank_l0_g1 (
    .logits(masked_logits[32 +: 32]),
    .top_indices(level0_index_1),
    .top_logits(level0_logits[16 +: 16])
  );
  always @* begin
    case (level0_index_1)
      1'd0: level0_token_ids[16 +: 16] = in_base_token_id + 16'd2;
      1'd1: level0_token_ids[16 +: 16] = in_base_token_id + 16'd3;
      default: level0_token_ids[16 +: 16] = in_base_token_id + 16'd2;
    endcase
  end
  wire [0:0] level0_index_2;
  logit_rank_r2_l16_k1 rank_l0_g2 (
    .logits(masked_logits[64 +: 32]),
    .top_indices(level0_index_2),
    .top_logits(level0_logits[32 +: 16])
  );
  always @* begin
    case (level0_index_2)
      1'd0: level0_token_ids[32 +: 16] = in_base_token_id + 16'd4;
      1'd1: level0_token_ids[32 +: 16] = in_base_token_id + 16'd5;
      default: level0_token_ids[32 +: 16] = in_base_token_id + 16'd4;
    endcase
  end
  wire [0:0] level0_index_3;
  logit_rank_r2_l16_k1 rank_l0_g3 (
    .logits(masked_logits[96 +: 32]),
    .top_indices(level0_index_3),
    .top_logits(level0_logits[48 +: 16])
  );
  always @* begin
    case (level0_index_3)
      1'd0: level0_token_ids[48 +: 16] = in_base_token_id + 16'd6;
      1'd1: level0_token_ids[48 +: 16] = in_base_token_id + 16'd7;
      default: level0_token_ids[48 +: 16] = in_base_token_id + 16'd6;
    endcase
  end
  wire [0:0] level0_index_4;
  logit_rank_r2_l16_k1 rank_l0_g4 (
    .logits(masked_logits[128 +: 32]),
    .top_indices(level0_index_4),
    .top_logits(level0_logits[64 +: 16])
  );
  always @* begin
    case (level0_index_4)
      1'd0: level0_token_ids[64 +: 16] = in_base_token_id + 16'd8;
      1'd1: level0_token_ids[64 +: 16] = in_base_token_id + 16'd9;
      default: level0_token_ids[64 +: 16] = in_base_token_id + 16'd8;
    endcase
  end
  wire [0:0] level0_index_5;
  logit_rank_r2_l16_k1 rank_l0_g5 (
    .logits(masked_logits[160 +: 32]),
    .top_indices(level0_index_5),
    .top_logits(level0_logits[80 +: 16])
  );
  always @* begin
    case (level0_index_5)
      1'd0: level0_token_ids[80 +: 16] = in_base_token_id + 16'd10;
      1'd1: level0_token_ids[80 +: 16] = in_base_token_id + 16'd11;
      default: level0_token_ids[80 +: 16] = in_base_token_id + 16'd10;
    endcase
  end
  wire [0:0] level0_index_6;
  logit_rank_r2_l16_k1 rank_l0_g6 (
    .logits(masked_logits[192 +: 32]),
    .top_indices(level0_index_6),
    .top_logits(level0_logits[96 +: 16])
  );
  always @* begin
    case (level0_index_6)
      1'd0: level0_token_ids[96 +: 16] = in_base_token_id + 16'd12;
      1'd1: level0_token_ids[96 +: 16] = in_base_token_id + 16'd13;
      default: level0_token_ids[96 +: 16] = in_base_token_id + 16'd12;
    endcase
  end
  wire [0:0] level0_index_7;
  logit_rank_r2_l16_k1 rank_l0_g7 (
    .logits(masked_logits[224 +: 32]),
    .top_indices(level0_index_7),
    .top_logits(level0_logits[112 +: 16])
  );
  always @* begin
    case (level0_index_7)
      1'd0: level0_token_ids[112 +: 16] = in_base_token_id + 16'd14;
      1'd1: level0_token_ids[112 +: 16] = in_base_token_id + 16'd15;
      default: level0_token_ids[112 +: 16] = in_base_token_id + 16'd14;
    endcase
  end
  wire [0:0] level0_index_8;
  logit_rank_r2_l16_k1 rank_l0_g8 (
    .logits(masked_logits[256 +: 32]),
    .top_indices(level0_index_8),
    .top_logits(level0_logits[128 +: 16])
  );
  always @* begin
    case (level0_index_8)
      1'd0: level0_token_ids[128 +: 16] = in_base_token_id + 16'd16;
      1'd1: level0_token_ids[128 +: 16] = in_base_token_id + 16'd17;
      default: level0_token_ids[128 +: 16] = in_base_token_id + 16'd16;
    endcase
  end
  wire [0:0] level0_index_9;
  logit_rank_r2_l16_k1 rank_l0_g9 (
    .logits(masked_logits[288 +: 32]),
    .top_indices(level0_index_9),
    .top_logits(level0_logits[144 +: 16])
  );
  always @* begin
    case (level0_index_9)
      1'd0: level0_token_ids[144 +: 16] = in_base_token_id + 16'd18;
      1'd1: level0_token_ids[144 +: 16] = in_base_token_id + 16'd19;
      default: level0_token_ids[144 +: 16] = in_base_token_id + 16'd18;
    endcase
  end
  wire [0:0] level0_index_10;
  logit_rank_r2_l16_k1 rank_l0_g10 (
    .logits(masked_logits[320 +: 32]),
    .top_indices(level0_index_10),
    .top_logits(level0_logits[160 +: 16])
  );
  always @* begin
    case (level0_index_10)
      1'd0: level0_token_ids[160 +: 16] = in_base_token_id + 16'd20;
      1'd1: level0_token_ids[160 +: 16] = in_base_token_id + 16'd21;
      default: level0_token_ids[160 +: 16] = in_base_token_id + 16'd20;
    endcase
  end
  wire [0:0] level0_index_11;
  logit_rank_r2_l16_k1 rank_l0_g11 (
    .logits(masked_logits[352 +: 32]),
    .top_indices(level0_index_11),
    .top_logits(level0_logits[176 +: 16])
  );
  always @* begin
    case (level0_index_11)
      1'd0: level0_token_ids[176 +: 16] = in_base_token_id + 16'd22;
      1'd1: level0_token_ids[176 +: 16] = in_base_token_id + 16'd23;
      default: level0_token_ids[176 +: 16] = in_base_token_id + 16'd22;
    endcase
  end
  wire [0:0] level0_index_12;
  logit_rank_r2_l16_k1 rank_l0_g12 (
    .logits(masked_logits[384 +: 32]),
    .top_indices(level0_index_12),
    .top_logits(level0_logits[192 +: 16])
  );
  always @* begin
    case (level0_index_12)
      1'd0: level0_token_ids[192 +: 16] = in_base_token_id + 16'd24;
      1'd1: level0_token_ids[192 +: 16] = in_base_token_id + 16'd25;
      default: level0_token_ids[192 +: 16] = in_base_token_id + 16'd24;
    endcase
  end
  wire [0:0] level0_index_13;
  logit_rank_r2_l16_k1 rank_l0_g13 (
    .logits(masked_logits[416 +: 32]),
    .top_indices(level0_index_13),
    .top_logits(level0_logits[208 +: 16])
  );
  always @* begin
    case (level0_index_13)
      1'd0: level0_token_ids[208 +: 16] = in_base_token_id + 16'd26;
      1'd1: level0_token_ids[208 +: 16] = in_base_token_id + 16'd27;
      default: level0_token_ids[208 +: 16] = in_base_token_id + 16'd26;
    endcase
  end
  wire [0:0] level0_index_14;
  logit_rank_r2_l16_k1 rank_l0_g14 (
    .logits(masked_logits[448 +: 32]),
    .top_indices(level0_index_14),
    .top_logits(level0_logits[224 +: 16])
  );
  always @* begin
    case (level0_index_14)
      1'd0: level0_token_ids[224 +: 16] = in_base_token_id + 16'd28;
      1'd1: level0_token_ids[224 +: 16] = in_base_token_id + 16'd29;
      default: level0_token_ids[224 +: 16] = in_base_token_id + 16'd28;
    endcase
  end
  wire [0:0] level0_index_15;
  logit_rank_r2_l16_k1 rank_l0_g15 (
    .logits(masked_logits[480 +: 32]),
    .top_indices(level0_index_15),
    .top_logits(level0_logits[240 +: 16])
  );
  always @* begin
    case (level0_index_15)
      1'd0: level0_token_ids[240 +: 16] = in_base_token_id + 16'd30;
      1'd1: level0_token_ids[240 +: 16] = in_base_token_id + 16'd31;
      default: level0_token_ids[240 +: 16] = in_base_token_id + 16'd30;
    endcase
  end
  wire [0:0] level0_index_16;
  logit_rank_r2_l16_k1 rank_l0_g16 (
    .logits(masked_logits[512 +: 32]),
    .top_indices(level0_index_16),
    .top_logits(level0_logits[256 +: 16])
  );
  always @* begin
    case (level0_index_16)
      1'd0: level0_token_ids[256 +: 16] = in_base_token_id + 16'd32;
      1'd1: level0_token_ids[256 +: 16] = in_base_token_id + 16'd33;
      default: level0_token_ids[256 +: 16] = in_base_token_id + 16'd32;
    endcase
  end
  wire [0:0] level0_index_17;
  logit_rank_r2_l16_k1 rank_l0_g17 (
    .logits(masked_logits[544 +: 32]),
    .top_indices(level0_index_17),
    .top_logits(level0_logits[272 +: 16])
  );
  always @* begin
    case (level0_index_17)
      1'd0: level0_token_ids[272 +: 16] = in_base_token_id + 16'd34;
      1'd1: level0_token_ids[272 +: 16] = in_base_token_id + 16'd35;
      default: level0_token_ids[272 +: 16] = in_base_token_id + 16'd34;
    endcase
  end
  wire [0:0] level0_index_18;
  logit_rank_r2_l16_k1 rank_l0_g18 (
    .logits(masked_logits[576 +: 32]),
    .top_indices(level0_index_18),
    .top_logits(level0_logits[288 +: 16])
  );
  always @* begin
    case (level0_index_18)
      1'd0: level0_token_ids[288 +: 16] = in_base_token_id + 16'd36;
      1'd1: level0_token_ids[288 +: 16] = in_base_token_id + 16'd37;
      default: level0_token_ids[288 +: 16] = in_base_token_id + 16'd36;
    endcase
  end
  wire [0:0] level0_index_19;
  logit_rank_r2_l16_k1 rank_l0_g19 (
    .logits(masked_logits[608 +: 32]),
    .top_indices(level0_index_19),
    .top_logits(level0_logits[304 +: 16])
  );
  always @* begin
    case (level0_index_19)
      1'd0: level0_token_ids[304 +: 16] = in_base_token_id + 16'd38;
      1'd1: level0_token_ids[304 +: 16] = in_base_token_id + 16'd39;
      default: level0_token_ids[304 +: 16] = in_base_token_id + 16'd38;
    endcase
  end
  wire [0:0] level0_index_20;
  logit_rank_r2_l16_k1 rank_l0_g20 (
    .logits(masked_logits[640 +: 32]),
    .top_indices(level0_index_20),
    .top_logits(level0_logits[320 +: 16])
  );
  always @* begin
    case (level0_index_20)
      1'd0: level0_token_ids[320 +: 16] = in_base_token_id + 16'd40;
      1'd1: level0_token_ids[320 +: 16] = in_base_token_id + 16'd41;
      default: level0_token_ids[320 +: 16] = in_base_token_id + 16'd40;
    endcase
  end
  wire [0:0] level0_index_21;
  logit_rank_r2_l16_k1 rank_l0_g21 (
    .logits(masked_logits[672 +: 32]),
    .top_indices(level0_index_21),
    .top_logits(level0_logits[336 +: 16])
  );
  always @* begin
    case (level0_index_21)
      1'd0: level0_token_ids[336 +: 16] = in_base_token_id + 16'd42;
      1'd1: level0_token_ids[336 +: 16] = in_base_token_id + 16'd43;
      default: level0_token_ids[336 +: 16] = in_base_token_id + 16'd42;
    endcase
  end
  wire [0:0] level0_index_22;
  logit_rank_r2_l16_k1 rank_l0_g22 (
    .logits(masked_logits[704 +: 32]),
    .top_indices(level0_index_22),
    .top_logits(level0_logits[352 +: 16])
  );
  always @* begin
    case (level0_index_22)
      1'd0: level0_token_ids[352 +: 16] = in_base_token_id + 16'd44;
      1'd1: level0_token_ids[352 +: 16] = in_base_token_id + 16'd45;
      default: level0_token_ids[352 +: 16] = in_base_token_id + 16'd44;
    endcase
  end
  wire [0:0] level0_index_23;
  logit_rank_r2_l16_k1 rank_l0_g23 (
    .logits(masked_logits[736 +: 32]),
    .top_indices(level0_index_23),
    .top_logits(level0_logits[368 +: 16])
  );
  always @* begin
    case (level0_index_23)
      1'd0: level0_token_ids[368 +: 16] = in_base_token_id + 16'd46;
      1'd1: level0_token_ids[368 +: 16] = in_base_token_id + 16'd47;
      default: level0_token_ids[368 +: 16] = in_base_token_id + 16'd46;
    endcase
  end
  wire [0:0] level0_index_24;
  logit_rank_r2_l16_k1 rank_l0_g24 (
    .logits(masked_logits[768 +: 32]),
    .top_indices(level0_index_24),
    .top_logits(level0_logits[384 +: 16])
  );
  always @* begin
    case (level0_index_24)
      1'd0: level0_token_ids[384 +: 16] = in_base_token_id + 16'd48;
      1'd1: level0_token_ids[384 +: 16] = in_base_token_id + 16'd49;
      default: level0_token_ids[384 +: 16] = in_base_token_id + 16'd48;
    endcase
  end
  wire [0:0] level0_index_25;
  logit_rank_r2_l16_k1 rank_l0_g25 (
    .logits(masked_logits[800 +: 32]),
    .top_indices(level0_index_25),
    .top_logits(level0_logits[400 +: 16])
  );
  always @* begin
    case (level0_index_25)
      1'd0: level0_token_ids[400 +: 16] = in_base_token_id + 16'd50;
      1'd1: level0_token_ids[400 +: 16] = in_base_token_id + 16'd51;
      default: level0_token_ids[400 +: 16] = in_base_token_id + 16'd50;
    endcase
  end
  wire [0:0] level0_index_26;
  logit_rank_r2_l16_k1 rank_l0_g26 (
    .logits(masked_logits[832 +: 32]),
    .top_indices(level0_index_26),
    .top_logits(level0_logits[416 +: 16])
  );
  always @* begin
    case (level0_index_26)
      1'd0: level0_token_ids[416 +: 16] = in_base_token_id + 16'd52;
      1'd1: level0_token_ids[416 +: 16] = in_base_token_id + 16'd53;
      default: level0_token_ids[416 +: 16] = in_base_token_id + 16'd52;
    endcase
  end
  wire [0:0] level0_index_27;
  logit_rank_r2_l16_k1 rank_l0_g27 (
    .logits(masked_logits[864 +: 32]),
    .top_indices(level0_index_27),
    .top_logits(level0_logits[432 +: 16])
  );
  always @* begin
    case (level0_index_27)
      1'd0: level0_token_ids[432 +: 16] = in_base_token_id + 16'd54;
      1'd1: level0_token_ids[432 +: 16] = in_base_token_id + 16'd55;
      default: level0_token_ids[432 +: 16] = in_base_token_id + 16'd54;
    endcase
  end
  wire [0:0] level0_index_28;
  logit_rank_r2_l16_k1 rank_l0_g28 (
    .logits(masked_logits[896 +: 32]),
    .top_indices(level0_index_28),
    .top_logits(level0_logits[448 +: 16])
  );
  always @* begin
    case (level0_index_28)
      1'd0: level0_token_ids[448 +: 16] = in_base_token_id + 16'd56;
      1'd1: level0_token_ids[448 +: 16] = in_base_token_id + 16'd57;
      default: level0_token_ids[448 +: 16] = in_base_token_id + 16'd56;
    endcase
  end
  wire [0:0] level0_index_29;
  logit_rank_r2_l16_k1 rank_l0_g29 (
    .logits(masked_logits[928 +: 32]),
    .top_indices(level0_index_29),
    .top_logits(level0_logits[464 +: 16])
  );
  always @* begin
    case (level0_index_29)
      1'd0: level0_token_ids[464 +: 16] = in_base_token_id + 16'd58;
      1'd1: level0_token_ids[464 +: 16] = in_base_token_id + 16'd59;
      default: level0_token_ids[464 +: 16] = in_base_token_id + 16'd58;
    endcase
  end
  wire [0:0] level0_index_30;
  logit_rank_r2_l16_k1 rank_l0_g30 (
    .logits(masked_logits[960 +: 32]),
    .top_indices(level0_index_30),
    .top_logits(level0_logits[480 +: 16])
  );
  always @* begin
    case (level0_index_30)
      1'd0: level0_token_ids[480 +: 16] = in_base_token_id + 16'd60;
      1'd1: level0_token_ids[480 +: 16] = in_base_token_id + 16'd61;
      default: level0_token_ids[480 +: 16] = in_base_token_id + 16'd60;
    endcase
  end
  wire [0:0] level0_index_31;
  logit_rank_r2_l16_k1 rank_l0_g31 (
    .logits(masked_logits[992 +: 32]),
    .top_indices(level0_index_31),
    .top_logits(level0_logits[496 +: 16])
  );
  always @* begin
    case (level0_index_31)
      1'd0: level0_token_ids[496 +: 16] = in_base_token_id + 16'd62;
      1'd1: level0_token_ids[496 +: 16] = in_base_token_id + 16'd63;
      default: level0_token_ids[496 +: 16] = in_base_token_id + 16'd62;
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage1_valid <= 1'b0;
      stage1_last <= 1'b0;
      stage1_logits <= '0;
      stage1_token_ids <= '0;
    end else if (stage1_ready) begin
      stage1_valid <= in_valid;
      stage1_last <= in_last;
      stage1_logits <= level0_logits;
      stage1_token_ids <= level0_token_ids;
    end
  end

  wire signed [255:0] level1_logits;
  reg [255:0] level1_token_ids;
  wire [0:0] level1_index_0;
  logit_rank_r2_l16_k1 rank_l1_g0 (
    .logits(stage1_logits[0 +: 32]),
    .top_indices(level1_index_0),
    .top_logits(level1_logits[0 +: 16])
  );
  always @* begin
    case (level1_index_0)
      1'd0: level1_token_ids[0 +: 16] = stage1_token_ids[0 +: 16];
      1'd1: level1_token_ids[0 +: 16] = stage1_token_ids[16 +: 16];
      default: level1_token_ids[0 +: 16] = stage1_token_ids[0 +: 16];
    endcase
  end
  wire [0:0] level1_index_1;
  logit_rank_r2_l16_k1 rank_l1_g1 (
    .logits(stage1_logits[32 +: 32]),
    .top_indices(level1_index_1),
    .top_logits(level1_logits[16 +: 16])
  );
  always @* begin
    case (level1_index_1)
      1'd0: level1_token_ids[16 +: 16] = stage1_token_ids[32 +: 16];
      1'd1: level1_token_ids[16 +: 16] = stage1_token_ids[48 +: 16];
      default: level1_token_ids[16 +: 16] = stage1_token_ids[32 +: 16];
    endcase
  end
  wire [0:0] level1_index_2;
  logit_rank_r2_l16_k1 rank_l1_g2 (
    .logits(stage1_logits[64 +: 32]),
    .top_indices(level1_index_2),
    .top_logits(level1_logits[32 +: 16])
  );
  always @* begin
    case (level1_index_2)
      1'd0: level1_token_ids[32 +: 16] = stage1_token_ids[64 +: 16];
      1'd1: level1_token_ids[32 +: 16] = stage1_token_ids[80 +: 16];
      default: level1_token_ids[32 +: 16] = stage1_token_ids[64 +: 16];
    endcase
  end
  wire [0:0] level1_index_3;
  logit_rank_r2_l16_k1 rank_l1_g3 (
    .logits(stage1_logits[96 +: 32]),
    .top_indices(level1_index_3),
    .top_logits(level1_logits[48 +: 16])
  );
  always @* begin
    case (level1_index_3)
      1'd0: level1_token_ids[48 +: 16] = stage1_token_ids[96 +: 16];
      1'd1: level1_token_ids[48 +: 16] = stage1_token_ids[112 +: 16];
      default: level1_token_ids[48 +: 16] = stage1_token_ids[96 +: 16];
    endcase
  end
  wire [0:0] level1_index_4;
  logit_rank_r2_l16_k1 rank_l1_g4 (
    .logits(stage1_logits[128 +: 32]),
    .top_indices(level1_index_4),
    .top_logits(level1_logits[64 +: 16])
  );
  always @* begin
    case (level1_index_4)
      1'd0: level1_token_ids[64 +: 16] = stage1_token_ids[128 +: 16];
      1'd1: level1_token_ids[64 +: 16] = stage1_token_ids[144 +: 16];
      default: level1_token_ids[64 +: 16] = stage1_token_ids[128 +: 16];
    endcase
  end
  wire [0:0] level1_index_5;
  logit_rank_r2_l16_k1 rank_l1_g5 (
    .logits(stage1_logits[160 +: 32]),
    .top_indices(level1_index_5),
    .top_logits(level1_logits[80 +: 16])
  );
  always @* begin
    case (level1_index_5)
      1'd0: level1_token_ids[80 +: 16] = stage1_token_ids[160 +: 16];
      1'd1: level1_token_ids[80 +: 16] = stage1_token_ids[176 +: 16];
      default: level1_token_ids[80 +: 16] = stage1_token_ids[160 +: 16];
    endcase
  end
  wire [0:0] level1_index_6;
  logit_rank_r2_l16_k1 rank_l1_g6 (
    .logits(stage1_logits[192 +: 32]),
    .top_indices(level1_index_6),
    .top_logits(level1_logits[96 +: 16])
  );
  always @* begin
    case (level1_index_6)
      1'd0: level1_token_ids[96 +: 16] = stage1_token_ids[192 +: 16];
      1'd1: level1_token_ids[96 +: 16] = stage1_token_ids[208 +: 16];
      default: level1_token_ids[96 +: 16] = stage1_token_ids[192 +: 16];
    endcase
  end
  wire [0:0] level1_index_7;
  logit_rank_r2_l16_k1 rank_l1_g7 (
    .logits(stage1_logits[224 +: 32]),
    .top_indices(level1_index_7),
    .top_logits(level1_logits[112 +: 16])
  );
  always @* begin
    case (level1_index_7)
      1'd0: level1_token_ids[112 +: 16] = stage1_token_ids[224 +: 16];
      1'd1: level1_token_ids[112 +: 16] = stage1_token_ids[240 +: 16];
      default: level1_token_ids[112 +: 16] = stage1_token_ids[224 +: 16];
    endcase
  end
  wire [0:0] level1_index_8;
  logit_rank_r2_l16_k1 rank_l1_g8 (
    .logits(stage1_logits[256 +: 32]),
    .top_indices(level1_index_8),
    .top_logits(level1_logits[128 +: 16])
  );
  always @* begin
    case (level1_index_8)
      1'd0: level1_token_ids[128 +: 16] = stage1_token_ids[256 +: 16];
      1'd1: level1_token_ids[128 +: 16] = stage1_token_ids[272 +: 16];
      default: level1_token_ids[128 +: 16] = stage1_token_ids[256 +: 16];
    endcase
  end
  wire [0:0] level1_index_9;
  logit_rank_r2_l16_k1 rank_l1_g9 (
    .logits(stage1_logits[288 +: 32]),
    .top_indices(level1_index_9),
    .top_logits(level1_logits[144 +: 16])
  );
  always @* begin
    case (level1_index_9)
      1'd0: level1_token_ids[144 +: 16] = stage1_token_ids[288 +: 16];
      1'd1: level1_token_ids[144 +: 16] = stage1_token_ids[304 +: 16];
      default: level1_token_ids[144 +: 16] = stage1_token_ids[288 +: 16];
    endcase
  end
  wire [0:0] level1_index_10;
  logit_rank_r2_l16_k1 rank_l1_g10 (
    .logits(stage1_logits[320 +: 32]),
    .top_indices(level1_index_10),
    .top_logits(level1_logits[160 +: 16])
  );
  always @* begin
    case (level1_index_10)
      1'd0: level1_token_ids[160 +: 16] = stage1_token_ids[320 +: 16];
      1'd1: level1_token_ids[160 +: 16] = stage1_token_ids[336 +: 16];
      default: level1_token_ids[160 +: 16] = stage1_token_ids[320 +: 16];
    endcase
  end
  wire [0:0] level1_index_11;
  logit_rank_r2_l16_k1 rank_l1_g11 (
    .logits(stage1_logits[352 +: 32]),
    .top_indices(level1_index_11),
    .top_logits(level1_logits[176 +: 16])
  );
  always @* begin
    case (level1_index_11)
      1'd0: level1_token_ids[176 +: 16] = stage1_token_ids[352 +: 16];
      1'd1: level1_token_ids[176 +: 16] = stage1_token_ids[368 +: 16];
      default: level1_token_ids[176 +: 16] = stage1_token_ids[352 +: 16];
    endcase
  end
  wire [0:0] level1_index_12;
  logit_rank_r2_l16_k1 rank_l1_g12 (
    .logits(stage1_logits[384 +: 32]),
    .top_indices(level1_index_12),
    .top_logits(level1_logits[192 +: 16])
  );
  always @* begin
    case (level1_index_12)
      1'd0: level1_token_ids[192 +: 16] = stage1_token_ids[384 +: 16];
      1'd1: level1_token_ids[192 +: 16] = stage1_token_ids[400 +: 16];
      default: level1_token_ids[192 +: 16] = stage1_token_ids[384 +: 16];
    endcase
  end
  wire [0:0] level1_index_13;
  logit_rank_r2_l16_k1 rank_l1_g13 (
    .logits(stage1_logits[416 +: 32]),
    .top_indices(level1_index_13),
    .top_logits(level1_logits[208 +: 16])
  );
  always @* begin
    case (level1_index_13)
      1'd0: level1_token_ids[208 +: 16] = stage1_token_ids[416 +: 16];
      1'd1: level1_token_ids[208 +: 16] = stage1_token_ids[432 +: 16];
      default: level1_token_ids[208 +: 16] = stage1_token_ids[416 +: 16];
    endcase
  end
  wire [0:0] level1_index_14;
  logit_rank_r2_l16_k1 rank_l1_g14 (
    .logits(stage1_logits[448 +: 32]),
    .top_indices(level1_index_14),
    .top_logits(level1_logits[224 +: 16])
  );
  always @* begin
    case (level1_index_14)
      1'd0: level1_token_ids[224 +: 16] = stage1_token_ids[448 +: 16];
      1'd1: level1_token_ids[224 +: 16] = stage1_token_ids[464 +: 16];
      default: level1_token_ids[224 +: 16] = stage1_token_ids[448 +: 16];
    endcase
  end
  wire [0:0] level1_index_15;
  logit_rank_r2_l16_k1 rank_l1_g15 (
    .logits(stage1_logits[480 +: 32]),
    .top_indices(level1_index_15),
    .top_logits(level1_logits[240 +: 16])
  );
  always @* begin
    case (level1_index_15)
      1'd0: level1_token_ids[240 +: 16] = stage1_token_ids[480 +: 16];
      1'd1: level1_token_ids[240 +: 16] = stage1_token_ids[496 +: 16];
      default: level1_token_ids[240 +: 16] = stage1_token_ids[480 +: 16];
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage2_valid <= 1'b0;
      stage2_last <= 1'b0;
      stage2_logits <= '0;
      stage2_token_ids <= '0;
    end else if (stage2_ready) begin
      stage2_valid <= stage1_valid;
      stage2_last <= stage1_last;
      stage2_logits <= level1_logits;
      stage2_token_ids <= level1_token_ids;
    end
  end

  wire signed [127:0] level2_logits;
  reg [127:0] level2_token_ids;
  wire [0:0] level2_index_0;
  logit_rank_r2_l16_k1 rank_l2_g0 (
    .logits(stage2_logits[0 +: 32]),
    .top_indices(level2_index_0),
    .top_logits(level2_logits[0 +: 16])
  );
  always @* begin
    case (level2_index_0)
      1'd0: level2_token_ids[0 +: 16] = stage2_token_ids[0 +: 16];
      1'd1: level2_token_ids[0 +: 16] = stage2_token_ids[16 +: 16];
      default: level2_token_ids[0 +: 16] = stage2_token_ids[0 +: 16];
    endcase
  end
  wire [0:0] level2_index_1;
  logit_rank_r2_l16_k1 rank_l2_g1 (
    .logits(stage2_logits[32 +: 32]),
    .top_indices(level2_index_1),
    .top_logits(level2_logits[16 +: 16])
  );
  always @* begin
    case (level2_index_1)
      1'd0: level2_token_ids[16 +: 16] = stage2_token_ids[32 +: 16];
      1'd1: level2_token_ids[16 +: 16] = stage2_token_ids[48 +: 16];
      default: level2_token_ids[16 +: 16] = stage2_token_ids[32 +: 16];
    endcase
  end
  wire [0:0] level2_index_2;
  logit_rank_r2_l16_k1 rank_l2_g2 (
    .logits(stage2_logits[64 +: 32]),
    .top_indices(level2_index_2),
    .top_logits(level2_logits[32 +: 16])
  );
  always @* begin
    case (level2_index_2)
      1'd0: level2_token_ids[32 +: 16] = stage2_token_ids[64 +: 16];
      1'd1: level2_token_ids[32 +: 16] = stage2_token_ids[80 +: 16];
      default: level2_token_ids[32 +: 16] = stage2_token_ids[64 +: 16];
    endcase
  end
  wire [0:0] level2_index_3;
  logit_rank_r2_l16_k1 rank_l2_g3 (
    .logits(stage2_logits[96 +: 32]),
    .top_indices(level2_index_3),
    .top_logits(level2_logits[48 +: 16])
  );
  always @* begin
    case (level2_index_3)
      1'd0: level2_token_ids[48 +: 16] = stage2_token_ids[96 +: 16];
      1'd1: level2_token_ids[48 +: 16] = stage2_token_ids[112 +: 16];
      default: level2_token_ids[48 +: 16] = stage2_token_ids[96 +: 16];
    endcase
  end
  wire [0:0] level2_index_4;
  logit_rank_r2_l16_k1 rank_l2_g4 (
    .logits(stage2_logits[128 +: 32]),
    .top_indices(level2_index_4),
    .top_logits(level2_logits[64 +: 16])
  );
  always @* begin
    case (level2_index_4)
      1'd0: level2_token_ids[64 +: 16] = stage2_token_ids[128 +: 16];
      1'd1: level2_token_ids[64 +: 16] = stage2_token_ids[144 +: 16];
      default: level2_token_ids[64 +: 16] = stage2_token_ids[128 +: 16];
    endcase
  end
  wire [0:0] level2_index_5;
  logit_rank_r2_l16_k1 rank_l2_g5 (
    .logits(stage2_logits[160 +: 32]),
    .top_indices(level2_index_5),
    .top_logits(level2_logits[80 +: 16])
  );
  always @* begin
    case (level2_index_5)
      1'd0: level2_token_ids[80 +: 16] = stage2_token_ids[160 +: 16];
      1'd1: level2_token_ids[80 +: 16] = stage2_token_ids[176 +: 16];
      default: level2_token_ids[80 +: 16] = stage2_token_ids[160 +: 16];
    endcase
  end
  wire [0:0] level2_index_6;
  logit_rank_r2_l16_k1 rank_l2_g6 (
    .logits(stage2_logits[192 +: 32]),
    .top_indices(level2_index_6),
    .top_logits(level2_logits[96 +: 16])
  );
  always @* begin
    case (level2_index_6)
      1'd0: level2_token_ids[96 +: 16] = stage2_token_ids[192 +: 16];
      1'd1: level2_token_ids[96 +: 16] = stage2_token_ids[208 +: 16];
      default: level2_token_ids[96 +: 16] = stage2_token_ids[192 +: 16];
    endcase
  end
  wire [0:0] level2_index_7;
  logit_rank_r2_l16_k1 rank_l2_g7 (
    .logits(stage2_logits[224 +: 32]),
    .top_indices(level2_index_7),
    .top_logits(level2_logits[112 +: 16])
  );
  always @* begin
    case (level2_index_7)
      1'd0: level2_token_ids[112 +: 16] = stage2_token_ids[224 +: 16];
      1'd1: level2_token_ids[112 +: 16] = stage2_token_ids[240 +: 16];
      default: level2_token_ids[112 +: 16] = stage2_token_ids[224 +: 16];
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage3_valid <= 1'b0;
      stage3_last <= 1'b0;
      stage3_logits <= '0;
      stage3_token_ids <= '0;
    end else if (stage3_ready) begin
      stage3_valid <= stage2_valid;
      stage3_last <= stage2_last;
      stage3_logits <= level2_logits;
      stage3_token_ids <= level2_token_ids;
    end
  end

  wire signed [63:0] level3_logits;
  reg [63:0] level3_token_ids;
  wire [0:0] level3_index_0;
  logit_rank_r2_l16_k1 rank_l3_g0 (
    .logits(stage3_logits[0 +: 32]),
    .top_indices(level3_index_0),
    .top_logits(level3_logits[0 +: 16])
  );
  always @* begin
    case (level3_index_0)
      1'd0: level3_token_ids[0 +: 16] = stage3_token_ids[0 +: 16];
      1'd1: level3_token_ids[0 +: 16] = stage3_token_ids[16 +: 16];
      default: level3_token_ids[0 +: 16] = stage3_token_ids[0 +: 16];
    endcase
  end
  wire [0:0] level3_index_1;
  logit_rank_r2_l16_k1 rank_l3_g1 (
    .logits(stage3_logits[32 +: 32]),
    .top_indices(level3_index_1),
    .top_logits(level3_logits[16 +: 16])
  );
  always @* begin
    case (level3_index_1)
      1'd0: level3_token_ids[16 +: 16] = stage3_token_ids[32 +: 16];
      1'd1: level3_token_ids[16 +: 16] = stage3_token_ids[48 +: 16];
      default: level3_token_ids[16 +: 16] = stage3_token_ids[32 +: 16];
    endcase
  end
  wire [0:0] level3_index_2;
  logit_rank_r2_l16_k1 rank_l3_g2 (
    .logits(stage3_logits[64 +: 32]),
    .top_indices(level3_index_2),
    .top_logits(level3_logits[32 +: 16])
  );
  always @* begin
    case (level3_index_2)
      1'd0: level3_token_ids[32 +: 16] = stage3_token_ids[64 +: 16];
      1'd1: level3_token_ids[32 +: 16] = stage3_token_ids[80 +: 16];
      default: level3_token_ids[32 +: 16] = stage3_token_ids[64 +: 16];
    endcase
  end
  wire [0:0] level3_index_3;
  logit_rank_r2_l16_k1 rank_l3_g3 (
    .logits(stage3_logits[96 +: 32]),
    .top_indices(level3_index_3),
    .top_logits(level3_logits[48 +: 16])
  );
  always @* begin
    case (level3_index_3)
      1'd0: level3_token_ids[48 +: 16] = stage3_token_ids[96 +: 16];
      1'd1: level3_token_ids[48 +: 16] = stage3_token_ids[112 +: 16];
      default: level3_token_ids[48 +: 16] = stage3_token_ids[96 +: 16];
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage4_valid <= 1'b0;
      stage4_last <= 1'b0;
      stage4_logits <= '0;
      stage4_token_ids <= '0;
    end else if (stage4_ready) begin
      stage4_valid <= stage3_valid;
      stage4_last <= stage3_last;
      stage4_logits <= level3_logits;
      stage4_token_ids <= level3_token_ids;
    end
  end

  wire signed [31:0] level4_logits;
  reg [31:0] level4_token_ids;
  wire [0:0] level4_index_0;
  logit_rank_r2_l16_k1 rank_l4_g0 (
    .logits(stage4_logits[0 +: 32]),
    .top_indices(level4_index_0),
    .top_logits(level4_logits[0 +: 16])
  );
  always @* begin
    case (level4_index_0)
      1'd0: level4_token_ids[0 +: 16] = stage4_token_ids[0 +: 16];
      1'd1: level4_token_ids[0 +: 16] = stage4_token_ids[16 +: 16];
      default: level4_token_ids[0 +: 16] = stage4_token_ids[0 +: 16];
    endcase
  end
  wire [0:0] level4_index_1;
  logit_rank_r2_l16_k1 rank_l4_g1 (
    .logits(stage4_logits[32 +: 32]),
    .top_indices(level4_index_1),
    .top_logits(level4_logits[16 +: 16])
  );
  always @* begin
    case (level4_index_1)
      1'd0: level4_token_ids[16 +: 16] = stage4_token_ids[32 +: 16];
      1'd1: level4_token_ids[16 +: 16] = stage4_token_ids[48 +: 16];
      default: level4_token_ids[16 +: 16] = stage4_token_ids[32 +: 16];
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage5_valid <= 1'b0;
      stage5_last <= 1'b0;
      stage5_logits <= '0;
      stage5_token_ids <= '0;
    end else if (stage5_ready) begin
      stage5_valid <= stage4_valid;
      stage5_last <= stage4_last;
      stage5_logits <= level4_logits;
      stage5_token_ids <= level4_token_ids;
    end
  end

  wire signed [15:0] level5_logits;
  reg [15:0] level5_token_ids;
  wire [0:0] level5_index_0;
  logit_rank_r2_l16_k1 rank_l5_g0 (
    .logits(stage5_logits[0 +: 32]),
    .top_indices(level5_index_0),
    .top_logits(level5_logits[0 +: 16])
  );
  always @* begin
    case (level5_index_0)
      1'd0: level5_token_ids[0 +: 16] = stage5_token_ids[0 +: 16];
      1'd1: level5_token_ids[0 +: 16] = stage5_token_ids[16 +: 16];
      default: level5_token_ids[0 +: 16] = stage5_token_ids[0 +: 16];
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage6_valid <= 1'b0;
      stage6_last <= 1'b0;
      stage6_logits <= '0;
      stage6_token_ids <= '0;
    end else if (stage6_ready) begin
      stage6_valid <= stage5_valid;
      stage6_last <= stage5_last;
      stage6_logits <= level5_logits;
      stage6_token_ids <= level5_token_ids;
    end
  end

  candidate_stream_merge_fifo_k1_l16_t16_d16 merger (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(stage6_valid),
    .in_ready(merge_in_ready),
    .in_last(stage6_last),
    .in_valid_mask(1'b1),
    .in_token_ids(stage6_token_ids[0 +: 16]),
    .in_logits(stage6_logits[0 +: 16]),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_valid_mask(out_valid_mask),
    .out_token_ids(out_token_ids),
    .out_logits(out_logits),
    .accepted_group_count(accepted_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .fifo_max_occupancy(fifo_max_occupancy),
    .final_completion_cycle(final_completion_cycle)
  );
endmodule
