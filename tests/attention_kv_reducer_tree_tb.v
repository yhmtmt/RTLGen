`timescale 1ns/1ps

module attention_kv_reducer_tree_tb;
  reg clk;
  reg rst_n;
  reg partial_valid;
  wire partial_ready;
  reg [127:0] value_fragments;
  reg [95:0] stat_fragments;
  wire reduced_valid;
  reg reduced_ready;
  wire signed [63:0] reduced_value_fragment;
  wire [23:0] reduced_stat_fragment;
  wire [15:0] accepted_group_count;
  wire [15:0] completed_group_count;
  wire [15:0] producer_stall_cycles;
  wire [15:0] cycle_count;
  wire [15:0] final_completion_cycle;

  attention_kv_reducer_tree_p4_l4_v8_s12_a16 dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .value_fragments(value_fragments),
    .stat_fragments(stat_fragments),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_group_count(accepted_group_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

  always #5 clk = ~clk;

  function [31:0] pack_values;
    input signed [7:0] lane0;
    input signed [7:0] lane1;
    input signed [7:0] lane2;
    input signed [7:0] lane3;
    begin
      pack_values = {lane3[7:0], lane2[7:0], lane1[7:0], lane0[7:0]};
    end
  endfunction

  function [23:0] pack_stats;
    input [11:0] stat0;
    input [11:0] stat1;
    begin
      pack_stats = {stat1, stat0};
    end
  endfunction

  initial begin
    #1000;
    $display("FAIL attention_kv_reducer_tree: simulation timeout");
    $fatal;
  end

  initial begin
    clk = 1'b0;
    rst_n = 1'b1;
    partial_valid = 1'b0;
    value_fragments = 128'h0;
    stat_fragments = 96'h0;
    reduced_ready = 1'b0;

    #1 rst_n = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    while (partial_ready !== 1'b1) begin
      @(negedge clk);
    end
    partial_valid = 1'b1;
    value_fragments = {
      pack_values(8'sd4, -8'sd1, 8'sd2, 8'sd3),
      pack_values(8'sd1, 8'sd7, -8'sd2, 8'sd6),
      pack_values(-8'sd3, 8'sd5, 8'sd4, -8'sd1),
      pack_values(8'sd10, -8'sd2, 8'sd3, 8'sd4)
    };
    stat_fragments = {
      pack_stats(12'd11, 12'd13),
      pack_stats(12'd7, 12'd8),
      pack_stats(12'd3, 12'd5),
      pack_stats(12'd2, 12'd4)
    };
    @(negedge clk);
    partial_valid = 1'b0;
    value_fragments = 128'h0;
    stat_fragments = 96'h0;

    repeat (5) @(negedge clk);
    if (!reduced_valid) begin
      $display("FAIL attention_kv_reducer_tree: reduced_valid was not asserted");
      $fatal;
    end
    if ($signed(reduced_value_fragment[15:0]) !== 16'sd12 ||
        $signed(reduced_value_fragment[31:16]) !== 16'sd9 ||
        $signed(reduced_value_fragment[47:32]) !== 16'sd7 ||
        $signed(reduced_value_fragment[63:48]) !== 16'sd12 ||
        reduced_stat_fragment[11:0] !== 12'd23 ||
        reduced_stat_fragment[23:12] !== 12'd30) begin
      $display(
        "FAIL attention_kv_reducer_tree values: lanes=[%0d,%0d,%0d,%0d] stats=[%0d,%0d]",
        $signed(reduced_value_fragment[15:0]),
        $signed(reduced_value_fragment[31:16]),
        $signed(reduced_value_fragment[47:32]),
        $signed(reduced_value_fragment[63:48]),
        reduced_stat_fragment[11:0],
        reduced_stat_fragment[23:12]
      );
      $fatal;
    end
    if (accepted_group_count !== 16'd1 || completed_group_count !== 16'd1 ||
        producer_stall_cycles !== 16'd0 || cycle_count === 16'd0 ||
        final_completion_cycle === 16'd0) begin
      $display(
        "FAIL attention_kv_reducer_tree observables: accepted=%0d groups=%0d stalls=%0d cycles=%0d final=%0d",
        accepted_group_count,
        completed_group_count,
        producer_stall_cycles,
        cycle_count,
        final_completion_cycle
      );
      $fatal;
    end

    reduced_ready = 1'b1;
    @(negedge clk);
    reduced_ready = 1'b0;

    $display("All attention/KV reducer tree tests passed.");
    $finish;
  end
endmodule
