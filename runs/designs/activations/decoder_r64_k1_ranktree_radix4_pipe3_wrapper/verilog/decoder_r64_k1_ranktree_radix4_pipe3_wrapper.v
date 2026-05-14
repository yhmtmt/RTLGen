`timescale 1ns/1ps
module decoder_r64_k1_ranktree_radix4_pipe3_wrapper(
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
  reg signed [255:0] stage1_logits;
  reg [255:0] stage1_token_ids;
  reg stage2_valid;
  reg stage2_last;
  reg signed [63:0] stage2_logits;
  reg [63:0] stage2_token_ids;
  reg stage3_valid;
  reg stage3_last;
  reg signed [15:0] stage3_logits;
  reg [15:0] stage3_token_ids;
  wire stage3_ready = !stage3_valid || merge_in_ready;
  wire stage2_ready = !stage2_valid || stage3_ready;
  wire stage1_ready = !stage1_valid || stage2_ready;
  assign in_ready = stage1_ready;

  wire signed [255:0] level0_logits;
  reg [255:0] level0_token_ids;
  wire [1:0] level0_index_0;
  logit_rank_r4_l16_k1 rank_l0_g0 (
    .logits(masked_logits[0 +: 64]),
    .top_indices(level0_index_0),
    .top_logits(level0_logits[0 +: 16])
  );
  always @* begin
    case (level0_index_0)
      2'd0: level0_token_ids[0 +: 16] = in_base_token_id + 16'd0;
      2'd1: level0_token_ids[0 +: 16] = in_base_token_id + 16'd1;
      2'd2: level0_token_ids[0 +: 16] = in_base_token_id + 16'd2;
      2'd3: level0_token_ids[0 +: 16] = in_base_token_id + 16'd3;
      default: level0_token_ids[0 +: 16] = in_base_token_id + 16'd0;
    endcase
  end
  wire [1:0] level0_index_1;
  logit_rank_r4_l16_k1 rank_l0_g1 (
    .logits(masked_logits[64 +: 64]),
    .top_indices(level0_index_1),
    .top_logits(level0_logits[16 +: 16])
  );
  always @* begin
    case (level0_index_1)
      2'd0: level0_token_ids[16 +: 16] = in_base_token_id + 16'd4;
      2'd1: level0_token_ids[16 +: 16] = in_base_token_id + 16'd5;
      2'd2: level0_token_ids[16 +: 16] = in_base_token_id + 16'd6;
      2'd3: level0_token_ids[16 +: 16] = in_base_token_id + 16'd7;
      default: level0_token_ids[16 +: 16] = in_base_token_id + 16'd4;
    endcase
  end
  wire [1:0] level0_index_2;
  logit_rank_r4_l16_k1 rank_l0_g2 (
    .logits(masked_logits[128 +: 64]),
    .top_indices(level0_index_2),
    .top_logits(level0_logits[32 +: 16])
  );
  always @* begin
    case (level0_index_2)
      2'd0: level0_token_ids[32 +: 16] = in_base_token_id + 16'd8;
      2'd1: level0_token_ids[32 +: 16] = in_base_token_id + 16'd9;
      2'd2: level0_token_ids[32 +: 16] = in_base_token_id + 16'd10;
      2'd3: level0_token_ids[32 +: 16] = in_base_token_id + 16'd11;
      default: level0_token_ids[32 +: 16] = in_base_token_id + 16'd8;
    endcase
  end
  wire [1:0] level0_index_3;
  logit_rank_r4_l16_k1 rank_l0_g3 (
    .logits(masked_logits[192 +: 64]),
    .top_indices(level0_index_3),
    .top_logits(level0_logits[48 +: 16])
  );
  always @* begin
    case (level0_index_3)
      2'd0: level0_token_ids[48 +: 16] = in_base_token_id + 16'd12;
      2'd1: level0_token_ids[48 +: 16] = in_base_token_id + 16'd13;
      2'd2: level0_token_ids[48 +: 16] = in_base_token_id + 16'd14;
      2'd3: level0_token_ids[48 +: 16] = in_base_token_id + 16'd15;
      default: level0_token_ids[48 +: 16] = in_base_token_id + 16'd12;
    endcase
  end
  wire [1:0] level0_index_4;
  logit_rank_r4_l16_k1 rank_l0_g4 (
    .logits(masked_logits[256 +: 64]),
    .top_indices(level0_index_4),
    .top_logits(level0_logits[64 +: 16])
  );
  always @* begin
    case (level0_index_4)
      2'd0: level0_token_ids[64 +: 16] = in_base_token_id + 16'd16;
      2'd1: level0_token_ids[64 +: 16] = in_base_token_id + 16'd17;
      2'd2: level0_token_ids[64 +: 16] = in_base_token_id + 16'd18;
      2'd3: level0_token_ids[64 +: 16] = in_base_token_id + 16'd19;
      default: level0_token_ids[64 +: 16] = in_base_token_id + 16'd16;
    endcase
  end
  wire [1:0] level0_index_5;
  logit_rank_r4_l16_k1 rank_l0_g5 (
    .logits(masked_logits[320 +: 64]),
    .top_indices(level0_index_5),
    .top_logits(level0_logits[80 +: 16])
  );
  always @* begin
    case (level0_index_5)
      2'd0: level0_token_ids[80 +: 16] = in_base_token_id + 16'd20;
      2'd1: level0_token_ids[80 +: 16] = in_base_token_id + 16'd21;
      2'd2: level0_token_ids[80 +: 16] = in_base_token_id + 16'd22;
      2'd3: level0_token_ids[80 +: 16] = in_base_token_id + 16'd23;
      default: level0_token_ids[80 +: 16] = in_base_token_id + 16'd20;
    endcase
  end
  wire [1:0] level0_index_6;
  logit_rank_r4_l16_k1 rank_l0_g6 (
    .logits(masked_logits[384 +: 64]),
    .top_indices(level0_index_6),
    .top_logits(level0_logits[96 +: 16])
  );
  always @* begin
    case (level0_index_6)
      2'd0: level0_token_ids[96 +: 16] = in_base_token_id + 16'd24;
      2'd1: level0_token_ids[96 +: 16] = in_base_token_id + 16'd25;
      2'd2: level0_token_ids[96 +: 16] = in_base_token_id + 16'd26;
      2'd3: level0_token_ids[96 +: 16] = in_base_token_id + 16'd27;
      default: level0_token_ids[96 +: 16] = in_base_token_id + 16'd24;
    endcase
  end
  wire [1:0] level0_index_7;
  logit_rank_r4_l16_k1 rank_l0_g7 (
    .logits(masked_logits[448 +: 64]),
    .top_indices(level0_index_7),
    .top_logits(level0_logits[112 +: 16])
  );
  always @* begin
    case (level0_index_7)
      2'd0: level0_token_ids[112 +: 16] = in_base_token_id + 16'd28;
      2'd1: level0_token_ids[112 +: 16] = in_base_token_id + 16'd29;
      2'd2: level0_token_ids[112 +: 16] = in_base_token_id + 16'd30;
      2'd3: level0_token_ids[112 +: 16] = in_base_token_id + 16'd31;
      default: level0_token_ids[112 +: 16] = in_base_token_id + 16'd28;
    endcase
  end
  wire [1:0] level0_index_8;
  logit_rank_r4_l16_k1 rank_l0_g8 (
    .logits(masked_logits[512 +: 64]),
    .top_indices(level0_index_8),
    .top_logits(level0_logits[128 +: 16])
  );
  always @* begin
    case (level0_index_8)
      2'd0: level0_token_ids[128 +: 16] = in_base_token_id + 16'd32;
      2'd1: level0_token_ids[128 +: 16] = in_base_token_id + 16'd33;
      2'd2: level0_token_ids[128 +: 16] = in_base_token_id + 16'd34;
      2'd3: level0_token_ids[128 +: 16] = in_base_token_id + 16'd35;
      default: level0_token_ids[128 +: 16] = in_base_token_id + 16'd32;
    endcase
  end
  wire [1:0] level0_index_9;
  logit_rank_r4_l16_k1 rank_l0_g9 (
    .logits(masked_logits[576 +: 64]),
    .top_indices(level0_index_9),
    .top_logits(level0_logits[144 +: 16])
  );
  always @* begin
    case (level0_index_9)
      2'd0: level0_token_ids[144 +: 16] = in_base_token_id + 16'd36;
      2'd1: level0_token_ids[144 +: 16] = in_base_token_id + 16'd37;
      2'd2: level0_token_ids[144 +: 16] = in_base_token_id + 16'd38;
      2'd3: level0_token_ids[144 +: 16] = in_base_token_id + 16'd39;
      default: level0_token_ids[144 +: 16] = in_base_token_id + 16'd36;
    endcase
  end
  wire [1:0] level0_index_10;
  logit_rank_r4_l16_k1 rank_l0_g10 (
    .logits(masked_logits[640 +: 64]),
    .top_indices(level0_index_10),
    .top_logits(level0_logits[160 +: 16])
  );
  always @* begin
    case (level0_index_10)
      2'd0: level0_token_ids[160 +: 16] = in_base_token_id + 16'd40;
      2'd1: level0_token_ids[160 +: 16] = in_base_token_id + 16'd41;
      2'd2: level0_token_ids[160 +: 16] = in_base_token_id + 16'd42;
      2'd3: level0_token_ids[160 +: 16] = in_base_token_id + 16'd43;
      default: level0_token_ids[160 +: 16] = in_base_token_id + 16'd40;
    endcase
  end
  wire [1:0] level0_index_11;
  logit_rank_r4_l16_k1 rank_l0_g11 (
    .logits(masked_logits[704 +: 64]),
    .top_indices(level0_index_11),
    .top_logits(level0_logits[176 +: 16])
  );
  always @* begin
    case (level0_index_11)
      2'd0: level0_token_ids[176 +: 16] = in_base_token_id + 16'd44;
      2'd1: level0_token_ids[176 +: 16] = in_base_token_id + 16'd45;
      2'd2: level0_token_ids[176 +: 16] = in_base_token_id + 16'd46;
      2'd3: level0_token_ids[176 +: 16] = in_base_token_id + 16'd47;
      default: level0_token_ids[176 +: 16] = in_base_token_id + 16'd44;
    endcase
  end
  wire [1:0] level0_index_12;
  logit_rank_r4_l16_k1 rank_l0_g12 (
    .logits(masked_logits[768 +: 64]),
    .top_indices(level0_index_12),
    .top_logits(level0_logits[192 +: 16])
  );
  always @* begin
    case (level0_index_12)
      2'd0: level0_token_ids[192 +: 16] = in_base_token_id + 16'd48;
      2'd1: level0_token_ids[192 +: 16] = in_base_token_id + 16'd49;
      2'd2: level0_token_ids[192 +: 16] = in_base_token_id + 16'd50;
      2'd3: level0_token_ids[192 +: 16] = in_base_token_id + 16'd51;
      default: level0_token_ids[192 +: 16] = in_base_token_id + 16'd48;
    endcase
  end
  wire [1:0] level0_index_13;
  logit_rank_r4_l16_k1 rank_l0_g13 (
    .logits(masked_logits[832 +: 64]),
    .top_indices(level0_index_13),
    .top_logits(level0_logits[208 +: 16])
  );
  always @* begin
    case (level0_index_13)
      2'd0: level0_token_ids[208 +: 16] = in_base_token_id + 16'd52;
      2'd1: level0_token_ids[208 +: 16] = in_base_token_id + 16'd53;
      2'd2: level0_token_ids[208 +: 16] = in_base_token_id + 16'd54;
      2'd3: level0_token_ids[208 +: 16] = in_base_token_id + 16'd55;
      default: level0_token_ids[208 +: 16] = in_base_token_id + 16'd52;
    endcase
  end
  wire [1:0] level0_index_14;
  logit_rank_r4_l16_k1 rank_l0_g14 (
    .logits(masked_logits[896 +: 64]),
    .top_indices(level0_index_14),
    .top_logits(level0_logits[224 +: 16])
  );
  always @* begin
    case (level0_index_14)
      2'd0: level0_token_ids[224 +: 16] = in_base_token_id + 16'd56;
      2'd1: level0_token_ids[224 +: 16] = in_base_token_id + 16'd57;
      2'd2: level0_token_ids[224 +: 16] = in_base_token_id + 16'd58;
      2'd3: level0_token_ids[224 +: 16] = in_base_token_id + 16'd59;
      default: level0_token_ids[224 +: 16] = in_base_token_id + 16'd56;
    endcase
  end
  wire [1:0] level0_index_15;
  logit_rank_r4_l16_k1 rank_l0_g15 (
    .logits(masked_logits[960 +: 64]),
    .top_indices(level0_index_15),
    .top_logits(level0_logits[240 +: 16])
  );
  always @* begin
    case (level0_index_15)
      2'd0: level0_token_ids[240 +: 16] = in_base_token_id + 16'd60;
      2'd1: level0_token_ids[240 +: 16] = in_base_token_id + 16'd61;
      2'd2: level0_token_ids[240 +: 16] = in_base_token_id + 16'd62;
      2'd3: level0_token_ids[240 +: 16] = in_base_token_id + 16'd63;
      default: level0_token_ids[240 +: 16] = in_base_token_id + 16'd60;
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

  wire signed [63:0] level1_logits;
  reg [63:0] level1_token_ids;
  wire [1:0] level1_index_0;
  logit_rank_r4_l16_k1 rank_l1_g0 (
    .logits(stage1_logits[0 +: 64]),
    .top_indices(level1_index_0),
    .top_logits(level1_logits[0 +: 16])
  );
  always @* begin
    case (level1_index_0)
      2'd0: level1_token_ids[0 +: 16] = stage1_token_ids[0 +: 16];
      2'd1: level1_token_ids[0 +: 16] = stage1_token_ids[16 +: 16];
      2'd2: level1_token_ids[0 +: 16] = stage1_token_ids[32 +: 16];
      2'd3: level1_token_ids[0 +: 16] = stage1_token_ids[48 +: 16];
      default: level1_token_ids[0 +: 16] = stage1_token_ids[0 +: 16];
    endcase
  end
  wire [1:0] level1_index_1;
  logit_rank_r4_l16_k1 rank_l1_g1 (
    .logits(stage1_logits[64 +: 64]),
    .top_indices(level1_index_1),
    .top_logits(level1_logits[16 +: 16])
  );
  always @* begin
    case (level1_index_1)
      2'd0: level1_token_ids[16 +: 16] = stage1_token_ids[64 +: 16];
      2'd1: level1_token_ids[16 +: 16] = stage1_token_ids[80 +: 16];
      2'd2: level1_token_ids[16 +: 16] = stage1_token_ids[96 +: 16];
      2'd3: level1_token_ids[16 +: 16] = stage1_token_ids[112 +: 16];
      default: level1_token_ids[16 +: 16] = stage1_token_ids[64 +: 16];
    endcase
  end
  wire [1:0] level1_index_2;
  logit_rank_r4_l16_k1 rank_l1_g2 (
    .logits(stage1_logits[128 +: 64]),
    .top_indices(level1_index_2),
    .top_logits(level1_logits[32 +: 16])
  );
  always @* begin
    case (level1_index_2)
      2'd0: level1_token_ids[32 +: 16] = stage1_token_ids[128 +: 16];
      2'd1: level1_token_ids[32 +: 16] = stage1_token_ids[144 +: 16];
      2'd2: level1_token_ids[32 +: 16] = stage1_token_ids[160 +: 16];
      2'd3: level1_token_ids[32 +: 16] = stage1_token_ids[176 +: 16];
      default: level1_token_ids[32 +: 16] = stage1_token_ids[128 +: 16];
    endcase
  end
  wire [1:0] level1_index_3;
  logit_rank_r4_l16_k1 rank_l1_g3 (
    .logits(stage1_logits[192 +: 64]),
    .top_indices(level1_index_3),
    .top_logits(level1_logits[48 +: 16])
  );
  always @* begin
    case (level1_index_3)
      2'd0: level1_token_ids[48 +: 16] = stage1_token_ids[192 +: 16];
      2'd1: level1_token_ids[48 +: 16] = stage1_token_ids[208 +: 16];
      2'd2: level1_token_ids[48 +: 16] = stage1_token_ids[224 +: 16];
      2'd3: level1_token_ids[48 +: 16] = stage1_token_ids[240 +: 16];
      default: level1_token_ids[48 +: 16] = stage1_token_ids[192 +: 16];
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

  wire signed [15:0] level2_logits;
  reg [15:0] level2_token_ids;
  wire [1:0] level2_index_0;
  logit_rank_r4_l16_k1 rank_l2_g0 (
    .logits(stage2_logits[0 +: 64]),
    .top_indices(level2_index_0),
    .top_logits(level2_logits[0 +: 16])
  );
  always @* begin
    case (level2_index_0)
      2'd0: level2_token_ids[0 +: 16] = stage2_token_ids[0 +: 16];
      2'd1: level2_token_ids[0 +: 16] = stage2_token_ids[16 +: 16];
      2'd2: level2_token_ids[0 +: 16] = stage2_token_ids[32 +: 16];
      2'd3: level2_token_ids[0 +: 16] = stage2_token_ids[48 +: 16];
      default: level2_token_ids[0 +: 16] = stage2_token_ids[0 +: 16];
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

  candidate_stream_merge_fifo_k1_l16_t16_d16 merger (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(stage3_valid),
    .in_ready(merge_in_ready),
    .in_last(stage3_last),
    .in_valid_mask(1'b1),
    .in_token_ids(stage3_token_ids[0 +: 16]),
    .in_logits(stage3_logits[0 +: 16]),
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
