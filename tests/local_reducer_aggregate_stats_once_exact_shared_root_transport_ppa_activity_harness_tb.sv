`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness_tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg enable = 1'b0;
  reg [31:0] control = 32'd0;
  wire [127:0] observable;
  integer cycles;

  always #5 clk = ~clk;

  local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness dut (
    .clk(clk), .rst_n(rst_n), .enable(enable), .control(control),
    .observable(observable)
  );

  initial begin
    #17;
    rst_n = 1'b1;
    enable = 1'b1;
    for (cycles = 0; cycles < 120000; cycles = cycles + 1) begin
      @(posedge clk);
      #1;
      if (observable[68] || observable[69])
        $fatal(1, "harness error protocol=%b timeout=%b observable=%h",
          observable[68], observable[69], observable);
      if (observable[67]) begin
        if (observable[2:0] !== 3'd4 ||
            observable[12:3] !== 10'd512 ||
            observable[26:13] !== 14'd10020 ||
            observable[37:27] !== 11'd1260 ||
            observable[48:38] !== 11'd1260 ||
            !observable[65] || !observable[66] ||
            observable[127:70] == 58'd0)
          $fatal(1, "harness exact counters failed observable=%h", observable);
        $display("PASS compact_exact_transport_harness groups=%0d rows=%0d flits=%0d packets=%0d completions=%0d checksum=%h cycles=%0d backpressure=%0d",
          observable[2:0], observable[12:3], observable[26:13],
          observable[37:27], observable[48:38], observable[127:70],
          observable[64:49], observable[65]);
        $finish;
      end
    end
    $fatal(1, "harness timeout observable=%h", observable);
  end
endmodule
