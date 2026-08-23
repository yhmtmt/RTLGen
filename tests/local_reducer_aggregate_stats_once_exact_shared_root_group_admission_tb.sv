`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_group_admission_tb;
  localparam integer SOURCE_COUNT = 15;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg admission_enable = 1'b0;
  reg [SOURCE_COUNT-1:0] remote_group_ready = {SOURCE_COUNT{1'b0}};
  reg root_local_group_ready = 1'b0;
  reg [SOURCE_COUNT-1:0] source_ctx_ready = {SOURCE_COUNT{1'b0}};
  reg shared_root_ctx_ready = 1'b0;

  wire group_admission_pulse;
  wire [1:0] group_index;
  wire [4:0] head_base;
  wire [2:0] group_epoch;
  wire [SOURCE_COUNT-1:0] source_producer_accept;
  wire root_producer_accept;
  wire [SOURCE_COUNT-1:0] source_ctx_valid;
  wire shared_root_ctx_valid;
  wire [2:0] admitted_group_count;
  wire done;
  wire protocol_error;

  always #5 clk = ~clk;

  local_reducer_aggregate_stats_once_exact_shared_root_group_admission dut (
    .clk(clk), .rst_n(rst_n), .admission_enable(admission_enable),
    .remote_group_ready(remote_group_ready),
    .root_local_group_ready(root_local_group_ready),
    .source_ctx_ready(source_ctx_ready),
    .shared_root_ctx_ready(shared_root_ctx_ready),
    .group_admission_pulse(group_admission_pulse),
    .group_index(group_index), .head_base(head_base),
    .group_epoch(group_epoch),
    .source_producer_accept(source_producer_accept),
    .root_producer_accept(root_producer_accept),
    .source_ctx_valid(source_ctx_valid),
    .shared_root_ctx_valid(shared_root_ctx_valid),
    .admitted_group_count(admitted_group_count), .done(done),
    .protocol_error(protocol_error)
  );

  task expect_no_admission;
    input [1:0] expected_group;
    begin
      #1;
      if (group_admission_pulse || (|source_producer_accept) ||
          root_producer_accept || (|source_ctx_valid) || shared_root_ctx_valid)
        $fatal(1, "partial admission at group %0d", expected_group);
      if (group_index !== expected_group || head_base !== (expected_group * 8) ||
          group_epoch !== expected_group)
        $fatal(1, "pending metadata changed at group %0d", expected_group);
    end
  endtask

  task admit_group;
    input [1:0] expected_group;
    begin
      @(negedge clk);
      remote_group_ready = {SOURCE_COUNT{1'b1}};
      root_local_group_ready = 1'b1;
      source_ctx_ready = {SOURCE_COUNT{1'b1}};
      shared_root_ctx_ready = 1'b1;
      #1;
      if (!group_admission_pulse ||
          source_producer_accept !== {SOURCE_COUNT{1'b1}} ||
          !root_producer_accept || source_ctx_valid !== {SOURCE_COUNT{1'b1}} ||
          !shared_root_ctx_valid)
        $fatal(1, "non-atomic admission for group %0d", expected_group);
      if (group_index !== expected_group || head_base !== (expected_group * 8) ||
          group_epoch !== expected_group)
        $fatal(1, "wrong admission metadata for group %0d", expected_group);
      @(posedge clk);
      #1;
      remote_group_ready = {SOURCE_COUNT{1'b0}};
      root_local_group_ready = 1'b0;
    end
  endtask

  integer group;
  initial begin
    #12;
    rst_n = 1'b1;
    // Readiness may change freely while admission is disabled.
    remote_group_ready[0] = 1'b1;
    @(posedge clk);
    #1;
    remote_group_ready[0] = 1'b0;
    @(posedge clk);
    #1;
    if (protocol_error)
      $fatal(1, "disabled readiness change was treated as a regression");
    admission_enable = 1'b1;

    // Producer 3 and destination 9 delay group 0. No partial valid/accept is
    // permitted, and downstream ready may legally toggle while waiting.
    @(negedge clk);
    remote_group_ready = {SOURCE_COUNT{1'b1}};
    root_local_group_ready = 1'b1;
    source_ctx_ready = {SOURCE_COUNT{1'b1}};
    shared_root_ctx_ready = 1'b1;
    remote_group_ready[3] = 1'b0;
    source_ctx_ready[9] = 1'b0;
    expect_no_admission(2'd0);
    @(posedge clk);
    @(negedge clk);
    source_ctx_ready[4] = 1'b0;
    source_ctx_ready[9] = 1'b1;
    expect_no_admission(2'd0);
    @(posedge clk);
    @(negedge clk);
    source_ctx_ready[4] = 1'b1;
    remote_group_ready[3] = 1'b1;
    #1;
    if (!group_admission_pulse)
      $fatal(1, "delayed group 0 did not become admissible");
    @(posedge clk);
    #1;
    remote_group_ready = {SOURCE_COUNT{1'b0}};
    root_local_group_ready = 1'b0;
    if (group_index !== 2'd1 || head_base !== 5'd8 || group_epoch !== 3'd1 ||
        admitted_group_count !== 3'd1 || protocol_error)
      $fatal(1, "group 0 admission/advance failed");

    for (group = 1; group < 4; group = group + 1)
      admit_group(group[1:0]);

    #1;
    if (!done || admitted_group_count !== 3'd4 || protocol_error)
      $fatal(1, "four-group run failed done=%b count=%0d error=%b",
        done, admitted_group_count, protocol_error);

    // Keeping enable asserted is legal. The accepted group-3 ready levels
    // retire first; only a fresh all-producer-ready context is a fifth group.
    @(posedge clk);
    @(negedge clk);
    remote_group_ready = {SOURCE_COUNT{1'b1}};
    root_local_group_ready = 1'b1;
    @(posedge clk);
    #1;
    if (!protocol_error || group_admission_pulse)
      $fatal(1, "fresh fifth group was not rejected");

    // Reset and prove producer-held readiness regression is detected.
    rst_n = 1'b0;
    admission_enable = 1'b0;
    remote_group_ready = {SOURCE_COUNT{1'b0}};
    source_ctx_ready = {SOURCE_COUNT{1'b0}};
    root_local_group_ready = 1'b0;
    shared_root_ctx_ready = 1'b0;
    @(posedge clk);
    #1;
    rst_n = 1'b1;
    admission_enable = 1'b1;
    remote_group_ready[0] = 1'b1;
    @(posedge clk);
    #1;
    remote_group_ready[0] = 1'b0;
    @(posedge clk);
    #1;
    if (!protocol_error || group_admission_pulse)
      $fatal(1, "producer readiness regression was not detected");

    $display("PASS group_admission four_groups=4 exact_done=1 exact_error=0");
    $finish;
  end
endmodule
