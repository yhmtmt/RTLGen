`timescale 1ns/1ps

module candidate_stream_merge_fifo_tb;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg in_last;
  reg [1:0] in_valid_mask;
  reg [15:0] in_token_ids;
  reg signed [31:0] in_logits;
  wire out_valid;
  reg out_ready;
  wire [1:0] out_valid_mask;
  wire [15:0] out_token_ids;
  wire signed [31:0] out_logits;
  wire [15:0] accepted_group_count;
  wire [15:0] producer_stall_cycles;
  wire [15:0] fifo_max_occupancy;
  wire [15:0] final_completion_cycle;

  candidate_stream_merge_fifo_k2_l16_t8_d2 dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_last(in_last),
    .in_valid_mask(in_valid_mask),
    .in_token_ids(in_token_ids),
    .in_logits(in_logits),
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

  always #5 clk = ~clk;

  task send_group;
    input last;
    input [1:0] mask;
    input [7:0] token0;
    input signed [15:0] logit0;
    input [7:0] token1;
    input signed [15:0] logit1;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_last = last;
      in_valid_mask = mask;
      in_token_ids = {token1, token0};
      in_logits = {logit1, logit0};
      @(negedge clk);
      while (!in_ready) begin
        @(negedge clk);
      end
      in_valid = 1'b0;
      in_last = 1'b0;
      in_valid_mask = 2'b00;
      in_token_ids = 16'h0000;
      in_logits = 32'sh00000000;
    end
  endtask

  initial begin
    clk = 1'b0;
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_last = 1'b0;
    in_valid_mask = 2'b00;
    in_token_ids = 16'h0000;
    in_logits = 32'sh00000000;
    out_ready = 1'b0;

    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    // The second group ties token 5's logit with token 1; lower token id wins.
    send_group(1'b0, 2'b11, 8'd5, 16'sd10, 8'd2, 16'sd7);
    send_group(1'b1, 2'b11, 8'd1, 16'sd10, 8'd3, 16'sd12);

    repeat (8) @(negedge clk);
    if (!out_valid) begin
      $display("FAIL candidate_stream_merge_fifo: out_valid was not asserted");
      $fatal;
    end
    if (out_valid_mask !== 2'b11 ||
        out_token_ids[7:0] !== 8'd3 ||
        out_token_ids[15:8] !== 8'd1 ||
        $signed(out_logits[15:0]) !== 16'sd12 ||
        $signed(out_logits[31:16]) !== 16'sd10) begin
      $display(
        "FAIL candidate_stream_merge_fifo: tokens=[%0d,%0d] logits=[%0d,%0d] mask=%b",
        out_token_ids[7:0],
        out_token_ids[15:8],
        $signed(out_logits[15:0]),
        $signed(out_logits[31:16]),
        out_valid_mask
      );
      $fatal;
    end
    if (accepted_group_count !== 16'd2 || producer_stall_cycles !== 16'd0 ||
        fifo_max_occupancy === 16'd0 || final_completion_cycle === 16'd0) begin
      $display(
        "FAIL candidate_stream_merge_fifo observables: accepted=%0d stalls=%0d fifo_max=%0d final_cycle=%0d",
        accepted_group_count,
        producer_stall_cycles,
        fifo_max_occupancy,
        final_completion_cycle
      );
      $fatal;
    end

    out_ready = 1'b1;
    @(negedge clk);
    out_ready = 1'b0;

    $display("All candidate-stream merge FIFO tests passed.");
    $finish;
  end
endmodule
