`timescale 1ns/1ps

module attention_shared_stream_context_service_full_tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg enable = 1'b0;
  reg [31:0] control = 32'b0;
  wire [127:0] observable;
  integer cycles;

  always #5 clk = ~clk;

  attention_shared_stream_context_service_ppa_activity_harness dut (
    .clk(clk), .rst_n(rst_n), .enable(enable), .control(control),
    .observable(observable)
  );

  initial begin
    #17;
    rst_n = 1'b1;
    enable = 1'b1;
    for (cycles = 0; cycles < 250000; cycles = cycles + 1) begin
      @(posedge clk);
      #1;
      if (dut.protocol_error_w || (|dut.endpoint_protocol_error_w))
        $fatal(1, "full service protocol error cycle=%0d", cycles);
      if (dut.transport_complete_w) begin
        if (!dut.admission_complete_w || dut.event_index_q !== 7'd112 ||
            dut.admitted_count_w !== 8'd112 || dut.completed_count_w !== 8'd112 ||
            dut.accepted_write_count_q !== 32'd60928 ||
            dut.write_fold_q !== 128'h0000000000000d100000000000000d10 ||
            cycles !== 7783)
          $fatal(1, "full service counters failed cycle=%0d event=%0d admitted=%0d completed=%0d writes=%0d fold=%h",
            cycles, dut.event_index_q, dut.admitted_count_w, dut.completed_count_w,
            dut.accepted_write_count_q, dut.write_fold_q);
        $display("PASS shared_stream_full contexts=%0d packets=%0d flits=%0d cycles=%0d fold=%032h",
          dut.completed_count_w, 7616, dut.accepted_write_count_q, cycles,
          dut.write_fold_q);
        $finish;
      end
    end
    $fatal(1, "full service timeout event=%0d admitted=%0d completed=%0d writes=%0d",
      dut.event_index_q, dut.admitted_count_w, dut.completed_count_w,
      dut.accepted_write_count_q);
  end
endmodule
