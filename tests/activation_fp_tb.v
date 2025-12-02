`timescale 1ns/1ps

module activation_fp_tb;
  reg  [33:0] X;
  wire [33:0] Y;

  relu_fp32 dut (.X(X), .Y(Y));

  task check;
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
    check(34'h13f800000, 34'h13f800000); // +1.0 stays
    check(34'h1bf800000, 34'h100000000); // -1.0 -> +0 with exn=01
    check(34'h100000000, 34'h100000000); // +0 stays
    check(34'h300000001, 34'h300000001); // NaN/inf (exn=11) passthrough
    $display("All fp activation tests passed.");
    $finish;
  end
endmodule
