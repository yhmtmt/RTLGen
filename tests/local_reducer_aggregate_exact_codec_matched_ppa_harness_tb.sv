`timescale 1ns/1ps

module local_reducer_aggregate_exact_codec_matched_ppa_harness_tb;
  localparam integer COUNTER_W = 32;
  localparam integer REQUIRED_GROUPS = 3;
  localparam integer MAX_CYCLES = 200000;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle_count = 0;

  wire [31:0] aligned_observed;
  wire [COUNTER_W-1:0] aligned_accepted;
  wire [COUNTER_W-1:0] aligned_flits;
  wire [COUNTER_W-1:0] aligned_decoded;
  wire [COUNTER_W-1:0] aligned_groups;
  wire aligned_error;

  wire [31:0] stats_observed;
  wire [COUNTER_W-1:0] stats_accepted;
  wire [COUNTER_W-1:0] stats_flits;
  wire [COUNTER_W-1:0] stats_decoded;
  wire [COUNTER_W-1:0] stats_groups;
  wire stats_error;

  local_reducer_aggregate_exact_codec_matched_ppa_harness #(
    .MODE_STATS_ONCE(0),
    .COUNTER_W(COUNTER_W)
  ) aligned_dut (
    .clk(clk),
    .rst_n(rst_n),
    .observed_data(aligned_observed),
    .accepted_beat_count(aligned_accepted),
    .emitted_flit_count(aligned_flits),
    .decoded_beat_count(aligned_decoded),
    .completed_group_count(aligned_groups),
    .protocol_error(aligned_error)
  );

  local_reducer_aggregate_exact_codec_matched_ppa_harness #(
    .MODE_STATS_ONCE(1),
    .COUNTER_W(COUNTER_W)
  ) stats_dut (
    .clk(clk),
    .rst_n(rst_n),
    .observed_data(stats_observed),
    .accepted_beat_count(stats_accepted),
    .emitted_flit_count(stats_flits),
    .decoded_beat_count(stats_decoded),
    .completed_group_count(stats_groups),
    .protocol_error(stats_error)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n)
      cycle_count <= 0;
    else
      cycle_count <= cycle_count + 1;
  end

  initial begin
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    while ((aligned_groups < REQUIRED_GROUPS) ||
           (stats_groups < REQUIRED_GROUPS)) begin
      @(posedge clk);
      if (cycle_count >= MAX_CYCLES) begin
        $display("FAIL timeout cycles=%0d aligned_groups=%0d stats_groups=%0d aligned_accepted=%0d aligned_flits=%0d aligned_decoded=%0d stats_accepted=%0d stats_flits=%0d stats_decoded=%0d aligned_error=%b stats_error=%b",
          cycle_count, aligned_groups, stats_groups, aligned_accepted,
          aligned_flits, aligned_decoded, stats_accepted, stats_flits,
          stats_decoded, aligned_error, stats_error);
        $finish(1);
      end
    end
    #1;
    if (aligned_error || stats_error) begin
      $display("FAIL error aligned=%b stats=%b", aligned_error, stats_error);
      $finish(1);
    end
    if (aligned_dut.mismatch_q || stats_dut.mismatch_q) begin
      $display("FAIL exact decoded-beat comparison aligned=%b stats=%b",
        aligned_dut.mismatch_q, stats_dut.mismatch_q);
      $finish(1);
    end
    if (aligned_accepted < aligned_groups * 128 ||
        aligned_accepted >= (aligned_groups + 1) * 128 ||
        aligned_decoded < aligned_groups * 128 ||
        aligned_decoded >= (aligned_groups + 1) * 128 ||
        stats_accepted < stats_groups * 128 ||
        stats_accepted >= (stats_groups + 1) * 128 ||
        stats_decoded < stats_groups * 128 ||
        stats_decoded >= (stats_groups + 1) * 128) begin
      $display("FAIL group counters aligned accepted=%0d decoded=%0d groups=%0d stats accepted=%0d decoded=%0d groups=%0d",
        aligned_accepted, aligned_decoded, aligned_groups, stats_accepted,
        stats_decoded, stats_groups);
      $finish(1);
    end
    if (aligned_groups < REQUIRED_GROUPS || stats_groups < REQUIRED_GROUPS ||
        aligned_flits < aligned_groups * 256 ||
        aligned_flits >= (aligned_groups + 1) * 256 ||
        stats_flits < stats_groups * 167 ||
        stats_flits >= (stats_groups + 1) * 167) begin
      $display("FAIL counts aligned beats=%0d decoded=%0d flits=%0d stats_flits=%0d",
        aligned_accepted, aligned_decoded, aligned_flits, stats_flits);
      $finish(1);
    end
    $display("PASS local_reducer_aggregate_exact_codec_matched_ppa_harness groups=%0d beats=%0d aligned_flits=%0d stats_flits=%0d cycles=%0d observed=%h",
      aligned_groups, aligned_decoded, aligned_flits, stats_flits,
      cycle_count, aligned_observed);
    $finish(0);
  end
endmodule
