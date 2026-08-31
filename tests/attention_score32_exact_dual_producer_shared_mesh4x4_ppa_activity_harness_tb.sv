`timescale 1ns/1ps

module attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg enable = 1'b0;
  reg [31:0] control = 32'h29d4_81b7;
  wire [127:0] observable;

  integer cycle_count;
  integer vc0_accepted;
  integer vc1_accepted;
  integer simultaneous_cycles;
  integer endpoint_i;

  attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness dut (
    .clk(clk),
    .rst_n(rst_n),
    .enable(enable),
    .control(control),
    .observable(observable)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle_count <= 0;
      vc0_accepted <= 0;
      vc1_accepted <= 0;
      simultaneous_cycles <= 0;
    end else if (enable) begin
      cycle_count <= cycle_count + 1;
      if (|(dut.vc0_in_valid_w & dut.vc0_in_ready_w))
        vc0_accepted <= vc0_accepted + 1;
      if (|(dut.vc1_in_valid_w & dut.vc1_in_ready_w))
        vc1_accepted <= vc1_accepted + 1;
      if (|(dut.vc0_in_valid_w & dut.vc1_in_valid_w))
        simultaneous_cycles <= simultaneous_cycles + 1;

      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (dut.vc0_in_valid_w[endpoint_i] &&
            dut.vc0_in_vc_w[(endpoint_i*2) +: 2] != 2'd0)
          $fatal(1, "VC0 activity emitted wrong VC at endpoint %0d", endpoint_i);
        if (dut.vc1_in_valid_w[endpoint_i] &&
            dut.vc1_in_vc_w[(endpoint_i*2) +: 2] != 2'd1)
          $fatal(1, "VC1 activity emitted wrong VC at endpoint %0d", endpoint_i);
      end

      if (dut.transport_protocol_error_w ||
          (|dut.injection_protocol_error_w) ||
          (|dut.ejection_protocol_error_w))
        $fatal(1, "shared transport protocol error");
      if (^observable === 1'bx)
        $fatal(1, "observable contains X");
    end
  end

  initial begin
    repeat (5) @(posedge clk);
    rst_n <= 1'b1;
    repeat (2) @(posedge clk);
    enable <= 1'b1;
    repeat (4096) @(posedge clk);

    if (vc0_accepted == 0)
      $fatal(1, "VC0 producer made no accepted injection progress");
    if (vc1_accepted == 0)
      $fatal(1, "VC1 producer made no accepted injection progress");
    if (simultaneous_cycles == 0)
      $fatal(1, "producer activity never overlapped");
    if ((|dut.router_accepted_flit_count_w) == 1'b0)
      $fatal(1, "shared mesh accepted no flits");

    $display(
      "PASS dual-producer PPA activity vc0=%0d vc1=%0d overlap=%0d cycles=%0d",
      vc0_accepted, vc1_accepted, simultaneous_cycles, cycle_count
    );
    $finish;
  end
endmodule
