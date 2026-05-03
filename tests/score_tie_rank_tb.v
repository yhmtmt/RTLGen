`timescale 1ns/1ps

module score_tie_rank_tb;
  reg  [63:0] scores;
  reg  signed [63:0] logits;
  wire [1:0] best_index;
  wire [15:0] best_score;
  wire signed [15:0] best_logit;

  score_tie_rank_r4_s16_l16 dut (
    .scores(scores),
    .logits(logits),
    .best_index(best_index),
    .best_score(best_score),
    .best_logit(best_logit)
  );

  task check_rank;
    input [63:0] s;
    input signed [63:0] l;
    input [1:0] exp_index;
    input [15:0] exp_score;
    input signed [15:0] exp_logit;
    begin
      scores = s;
      logits = l;
      #1;
      if (best_index !== exp_index || best_score !== exp_score || best_logit !== exp_logit) begin
        $display(
          "FAIL score_tie_rank: index=%0d score=%0d logit=%0d expected index=%0d score=%0d logit=%0d",
          best_index, best_score, best_logit, exp_index, exp_score, exp_logit
        );
        $fatal;
      end
    end
  endtask

  initial begin
    check_rank(
      {16'd7, 16'd25, 16'd8, 16'd5},
      {16'sd4, -16'sd2, 16'sd9, 16'sd1},
      2'd2,
      16'd25,
      -16'sd2
    );
    check_rank(
      {16'd10, 16'd10, 16'd10, 16'd9},
      {-16'sd4, 16'sd6, 16'sd3, 16'sd8},
      2'd2,
      16'd10,
      16'sd6
    );
    check_rank(
      {16'd11, 16'd11, 16'd10, 16'd4},
      {16'sd2, 16'sd2, 16'sd9, 16'sd1},
      2'd2,
      16'd11,
      16'sd2
    );
    check_rank(
      {16'd1, 16'd3, 16'd3, 16'd3},
      {-16'sd1, -16'sd5, -16'sd2, -16'sd8},
      2'd1,
      16'd3,
      -16'sd2
    );
    $display("All score tie-rank tests passed.");
    $finish;
  end
endmodule
