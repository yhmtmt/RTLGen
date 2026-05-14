`timescale 1ns/1ps
module decoder_r64_k1_producer_ranker_physical_wrapper(
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
  output [0:0] out_valid_mask,
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
  wire [5:0] local_top_indices;
  wire signed [15:0] local_top_logits;
  wire [15:0] local_token_ids;
  logit_rank_r64_l16_k1 ranker (
    .logits(masked_logits),
    .top_indices(local_top_indices),
    .top_logits(local_top_logits)
  );
  assign local_token_ids[0 +: 16] = in_base_token_id + { 10'd0, local_top_indices[0 +: 6] };
  candidate_stream_merge_fifo_k1_l16_t16_d16 merger (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_last(in_last),
    .in_valid_mask(1'b1),
    .in_token_ids(local_token_ids),
    .in_logits(local_top_logits),
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
