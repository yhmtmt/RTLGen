`timescale 1ns/1ps

module attention_kv_reducer_tb;
  reg clk;
  reg rst_n;
  reg partial_valid;
  wire partial_ready;
  reg partial_last;
  reg [31:0] value_fragment;
  reg [23:0] stat_fragment;
  wire reduced_valid;
  reg reduced_ready;
  wire signed [63:0] reduced_value_fragment;
  wire [23:0] reduced_stat_fragment;
  wire [15:0] accepted_partial_count;
  wire [15:0] completed_group_count;
  wire [15:0] producer_stall_cycles;
  wire [15:0] cycle_count;
  wire [15:0] final_completion_cycle;

  attention_kv_reducer_p3_l4_v8_s12_a16 dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .partial_last(partial_last),
    .value_fragment(value_fragment),
    .stat_fragment(stat_fragment),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_partial_count(accepted_partial_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

  always #5 clk = ~clk;

  task send_partial;
    input last;
    input signed [7:0] lane0;
    input signed [7:0] lane1;
    input signed [7:0] lane2;
    input signed [7:0] lane3;
    input [11:0] stat0;
    input [11:0] stat1;
    begin
      @(negedge clk);
      while (partial_ready !== 1'b1) begin
        @(negedge clk);
      end
      partial_valid = 1'b1;
      partial_last = last;
      value_fragment = {lane3[7:0], lane2[7:0], lane1[7:0], lane0[7:0]};
      stat_fragment = {stat1, stat0};
      @(negedge clk);
      partial_valid = 1'b0;
      partial_last = 1'b0;
      value_fragment = 32'h00000000;
      stat_fragment = 24'h000000;
    end
  endtask

  initial begin
    #1000;
    $display("FAIL attention_kv_reducer: simulation timeout");
    $fatal;
  end

  initial begin
    clk = 1'b0;
    rst_n = 1'b1;
    partial_valid = 1'b0;
    partial_last = 1'b0;
    value_fragment = 32'h00000000;
    stat_fragment = 24'h000000;
    reduced_ready = 1'b0;

    #1 rst_n = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    send_partial(1'b0, 8'sd1, -8'sd2, 8'sd3, 8'sd4, 12'd5, 12'd7);
    send_partial(1'b0, -8'sd1, 8'sd1, 8'sd2, -8'sd3, 12'd2, 12'd4);
    send_partial(1'b1, 8'sd10, -8'sd5, -8'sd1, 8'sd6, 12'd8, 12'd9);

    repeat (2) @(negedge clk);
    if (!reduced_valid) begin
      $display("FAIL attention_kv_reducer: reduced_valid was not asserted");
      $fatal;
    end
    if ($signed(reduced_value_fragment[15:0]) !== 16'sd10 ||
        $signed(reduced_value_fragment[31:16]) !== -16'sd6 ||
        $signed(reduced_value_fragment[47:32]) !== 16'sd4 ||
        $signed(reduced_value_fragment[63:48]) !== 16'sd7 ||
        reduced_stat_fragment[11:0] !== 12'd15 ||
        reduced_stat_fragment[23:12] !== 12'd20) begin
      $display(
        "FAIL attention_kv_reducer values: lanes=[%0d,%0d,%0d,%0d] stats=[%0d,%0d]",
        $signed(reduced_value_fragment[15:0]),
        $signed(reduced_value_fragment[31:16]),
        $signed(reduced_value_fragment[47:32]),
        $signed(reduced_value_fragment[63:48]),
        reduced_stat_fragment[11:0],
        reduced_stat_fragment[23:12]
      );
      $fatal;
    end
    if (accepted_partial_count !== 16'd3 || completed_group_count !== 16'd1 ||
        producer_stall_cycles !== 16'd0 || cycle_count === 16'd0 ||
        final_completion_cycle === 16'd0) begin
      $display(
        "FAIL attention_kv_reducer observables: accepted=%0d groups=%0d stalls=%0d cycles=%0d final=%0d",
        accepted_partial_count,
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

    $display("All attention/KV reducer tests passed.");
    $finish;
  end
endmodule
