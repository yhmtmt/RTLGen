`timescale 1ns/1ps

module activation_fp_tb;
  reg  [33:0] X;
  wire [33:0] Y;
  wire [33:0] Y_leaky;

  relu_fp32 dut (.X(X), .Y(Y));
  leakyrelu_fp32 dut_leaky (.X(X), .Y(Y_leaky));

  task check_relu;
    input [33:0] a;
    input [33:0] exp;
    begin
      X = a;
      #1;
      if (Y !== exp) begin
        $display("FAIL fp relu: X=%h got=%h expected=%h", a, Y, exp);
        $fatal;
      end
    end
  endtask

  initial begin
    check_relu(34'h13f800000, 34'h13f800000); // +1.0 stays
    check_relu(34'h1bf800000, 34'h100000000); // -1.0 -> +0 with exn=01
    check_relu(34'h100000000, 34'h100000000); // +0 stays
    check_relu(34'h300000001, 34'h300000001); // NaN/inf (exn=11) passthrough
    // leaky_relu with alpha=1/4: exponent decremented by 2 on negative normals
    X = 34'h1bf800000; #1; if (Y_leaky !== 34'h1be800000) begin $display("FAIL fp leaky"); $fatal; end
    $display("All fp activation tests passed.");
    $finish;
  end
endmodule
