`timescale 1ns/1ps
module decoder_output_ranker_policy_r128_wrapper(
  input clk,
  input rst_n,
  input use_ranktree,
  input in_valid,
  output in_ready,
  input in_last,
  input [15:0] in_base_token_id,
  input [127:0] in_lane_valid,
  input signed [2047:0] in_logits,
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
  wire serial0_ready, serial1_ready, serial0_valid, serial1_valid;
  wire serial0_mask, serial1_mask;
  wire [15:0] serial0_token, serial1_token;
  wire signed [15:0] serial0_logit, serial1_logit;
  wire [31:0] serial0_accepted, serial1_accepted, serial0_stalls, serial1_stalls;
  wire [31:0] serial0_fifo, serial1_fifo, serial0_final, serial1_final;
  wire serial_ready = serial0_ready && serial1_ready;
  wire serial_valid = serial0_valid && serial1_valid;
  wire serial_bank0_wins = (serial0_logit > serial1_logit) || ((serial0_logit == serial1_logit) && (serial0_token <= serial1_token));
  wire [15:0] serial_token = serial_bank0_wins ? serial0_token : serial1_token;
  wire signed [15:0] serial_logit = serial_bank0_wins ? serial0_logit : serial1_logit;
  wire serial_mask = serial0_mask && serial1_mask;
  wire [31:0] serial_accepted = serial0_accepted + serial1_accepted;
  wire [31:0] serial_stalls = serial0_stalls + serial1_stalls;
  wire [31:0] serial_fifo = (serial0_fifo > serial1_fifo) ? serial0_fifo : serial1_fifo;
  wire [31:0] serial_final = (serial0_final > serial1_final) ? serial0_final : serial1_final;
  wire tree0_ready, tree1_ready, tree0_valid, tree1_valid;
  wire tree0_mask, tree1_mask;
  wire [15:0] tree0_token, tree1_token;
  wire signed [15:0] tree0_logit, tree1_logit;
  wire [31:0] tree0_accepted, tree1_accepted, tree0_stalls, tree1_stalls;
  wire [31:0] tree0_fifo, tree1_fifo, tree0_final, tree1_final;
  wire tree_ready = tree0_ready && tree1_ready;
  wire tree_valid = tree0_valid && tree1_valid;
  wire tree_bank0_wins = (tree0_logit > tree1_logit) || ((tree0_logit == tree1_logit) && (tree0_token <= tree1_token));
  wire [15:0] tree_token = tree_bank0_wins ? tree0_token : tree1_token;
  wire signed [15:0] tree_logit = tree_bank0_wins ? tree0_logit : tree1_logit;
  wire tree_mask = tree0_mask && tree1_mask;
  wire [31:0] tree_accepted = tree0_accepted + tree1_accepted;
  wire [31:0] tree_stalls = tree0_stalls + tree1_stalls;
  wire [31:0] tree_fifo = (tree0_fifo > tree1_fifo) ? tree0_fifo : tree1_fifo;
  wire [31:0] tree_final = (tree0_final > tree1_final) ? tree0_final : tree1_final;
  assign in_ready = use_ranktree ? tree_ready : serial_ready;
  assign out_valid = use_ranktree ? tree_valid : serial_valid;
  assign out_valid_mask = use_ranktree ? tree_mask : serial_mask;
  assign out_token_ids = use_ranktree ? tree_token : serial_token;
  assign out_logits = use_ranktree ? tree_logit : serial_logit;
  assign accepted_group_count = use_ranktree ? tree_accepted : serial_accepted;
  assign producer_stall_cycles = use_ranktree ? tree_stalls : serial_stalls;
  assign fifo_max_occupancy = use_ranktree ? tree_fifo : serial_fifo;
  assign final_completion_cycle = use_ranktree ? tree_final : serial_final;
  decoder_output_ranker_policy_r128_wrapper_serial64 serial0_path (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in_valid && !use_ranktree && serial_ready), .in_ready(serial0_ready),
    .in_last(in_last),
    .in_base_token_id(in_base_token_id + 16'd0),
    .in_lane_valid(in_lane_valid[0 +: 64]),
    .in_logits(in_logits[0 +: 1024]),
    .out_valid(serial0_valid), .out_ready(out_ready && !use_ranktree && serial_valid),
    .out_valid_mask(serial0_mask), .out_token_ids(serial0_token), .out_logits(serial0_logit),
    .accepted_group_count(serial0_accepted), .producer_stall_cycles(serial0_stalls),
    .fifo_max_occupancy(serial0_fifo), .final_completion_cycle(serial0_final)
  );
  decoder_output_ranker_policy_r128_wrapper_serial64 serial1_path (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in_valid && !use_ranktree && serial_ready), .in_ready(serial1_ready),
    .in_last(in_last),
    .in_base_token_id(in_base_token_id + 16'd64),
    .in_lane_valid(in_lane_valid[64 +: 64]),
    .in_logits(in_logits[1024 +: 1024]),
    .out_valid(serial1_valid), .out_ready(out_ready && !use_ranktree && serial_valid),
    .out_valid_mask(serial1_mask), .out_token_ids(serial1_token), .out_logits(serial1_logit),
    .accepted_group_count(serial1_accepted), .producer_stall_cycles(serial1_stalls),
    .fifo_max_occupancy(serial1_fifo), .final_completion_cycle(serial1_final)
  );
  decoder_output_ranker_policy_r128_wrapper_ranktree64 tree0_path (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in_valid && use_ranktree && tree_ready), .in_ready(tree0_ready),
    .in_last(in_last),
    .in_base_token_id(in_base_token_id + 16'd0),
    .in_lane_valid(in_lane_valid[0 +: 64]),
    .in_logits(in_logits[0 +: 1024]),
    .out_valid(tree0_valid), .out_ready(out_ready && use_ranktree && tree_valid),
    .out_valid_mask(tree0_mask), .out_token_ids(tree0_token), .out_logits(tree0_logit),
    .accepted_group_count(tree0_accepted), .producer_stall_cycles(tree0_stalls),
    .fifo_max_occupancy(tree0_fifo), .final_completion_cycle(tree0_final)
  );
  decoder_output_ranker_policy_r128_wrapper_ranktree64 tree1_path (
    .clk(clk), .rst_n(rst_n),
    .in_valid(in_valid && use_ranktree && tree_ready), .in_ready(tree1_ready),
    .in_last(in_last),
    .in_base_token_id(in_base_token_id + 16'd64),
    .in_lane_valid(in_lane_valid[64 +: 64]),
    .in_logits(in_logits[1024 +: 1024]),
    .out_valid(tree1_valid), .out_ready(out_ready && use_ranktree && tree_valid),
    .out_valid_mask(tree1_mask), .out_token_ids(tree1_token), .out_logits(tree1_logit),
    .accepted_group_count(tree1_accepted), .producer_stall_cycles(tree1_stalls),
    .fifo_max_occupancy(tree1_fifo), .final_completion_cycle(tree1_final)
  );
endmodule
