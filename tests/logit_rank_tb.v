`timescale 1ns/1ps

module logit_rank_tb;
  reg  signed [63:0] logits;
  wire [3:0] top_indices;
  wire signed [31:0] top_logits;

  logit_rank_r4_l16_k2 dut (
    .logits(logits),
    .top_indices(top_indices),
    .top_logits(top_logits)
  );

  task check_rank;
    input signed [63:0] l;
    input [1:0] exp_index0;
    input signed [15:0] exp_logit0;
    input [1:0] exp_index1;
    input signed [15:0] exp_logit1;
    begin
      logits = l;
      #1;
      if (top_indices[1:0] !== exp_index0 || top_logits[15:0] !== exp_logit0 ||
          top_indices[3:2] !== exp_index1 || top_logits[31:16] !== exp_logit1) begin
        $display(
          "FAIL logit_rank: got idx=[%0d,%0d] logits=[%0d,%0d] expected idx=[%0d,%0d] logits=[%0d,%0d]",
          top_indices[1:0], top_indices[3:2],
          $signed(top_logits[15:0]), $signed(top_logits[31:16]),
          exp_index0, exp_index1, exp_logit0, exp_logit1
        );
        $fatal;
      end
    end
  endtask

  initial begin
    check_rank(
      {16'sd4, -16'sd2, 16'sd9, 16'sd1},
      2'd1,
      16'sd9,
      2'd3,
      16'sd4
    );
    check_rank(
      {16'sd5, 16'sd5, 16'sd5, 16'sd4},
      2'd1,
      16'sd5,
      2'd2,
      16'sd5
    );
    check_rank(
      {-16'sd8, -16'sd2, -16'sd5, -16'sd9},
      2'd2,
      -16'sd2,
      2'd1,
      -16'sd5
    );
    $display("All logit-rank tests passed.");
    $finish;
  end
endmodule
