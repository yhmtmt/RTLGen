`timescale 1ns/1ps
module decoder_output_ranker_policy_r64_wrapper(
  input clk,
  input rst_n,
  input use_ranktree,
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
  wire serial_ready, tree_ready;
  wire serial_valid, tree_valid;
  wire serial_mask, tree_mask;
  wire [15:0] serial_token, tree_token;
  wire signed [15:0] serial_logit, tree_logit;
  wire [31:0] serial_accepted, tree_accepted, serial_stalls, tree_stalls;
  wire [31:0] serial_fifo, tree_fifo, serial_final, tree_final;
  assign in_ready = use_ranktree ? tree_ready : serial_ready;
  assign out_valid = use_ranktree ? tree_valid : serial_valid;
  assign out_valid_mask = use_ranktree ? tree_mask : serial_mask;
  assign out_token_ids = use_ranktree ? tree_token : serial_token;
  assign out_logits = use_ranktree ? tree_logit : serial_logit;
  assign accepted_group_count = use_ranktree ? tree_accepted : serial_accepted;
  assign producer_stall_cycles = use_ranktree ? tree_stalls : serial_stalls;
  assign fifo_max_occupancy = use_ranktree ? tree_fifo : serial_fifo;
  assign final_completion_cycle = use_ranktree ? tree_final : serial_final;
  decoder_output_ranker_policy_r64_wrapper_serial64 serial_path (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid && !use_ranktree), .in_ready(serial_ready),
    .in_last(in_last), .in_base_token_id(in_base_token_id), .in_lane_valid(in_lane_valid), .in_logits(in_logits),
    .out_valid(serial_valid), .out_ready(out_ready && !use_ranktree), .out_valid_mask(serial_mask),
    .out_token_ids(serial_token), .out_logits(serial_logit), .accepted_group_count(serial_accepted),
    .producer_stall_cycles(serial_stalls), .fifo_max_occupancy(serial_fifo), .final_completion_cycle(serial_final)
  );
  decoder_output_ranker_policy_r64_wrapper_ranktree64 tree_path (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid && use_ranktree), .in_ready(tree_ready),
    .in_last(in_last), .in_base_token_id(in_base_token_id), .in_lane_valid(in_lane_valid), .in_logits(in_logits),
    .out_valid(tree_valid), .out_ready(out_ready && use_ranktree), .out_valid_mask(tree_mask),
    .out_token_ids(tree_token), .out_logits(tree_logit), .accepted_group_count(tree_accepted),
    .producer_stall_cycles(tree_stalls), .fifo_max_occupancy(tree_fifo), .final_completion_cycle(tree_final)
  );
endmodule
