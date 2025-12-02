`timescale 1ns/1ps

module fp_mul_tb;
  reg  [33:0] X;
  reg  [33:0] Y;
  wire [33:0] R;

  fp32_mul dut (.X(X), .Y(Y), .R(R));

  task check;
    input [33:0] a;
    input [33:0] b;
    input [33:0] exp;
    begin
      X = a;
      Y = b;
      #1;
      if (R !== exp) begin
        $display("FAIL: X=%h Y=%h got=%h expected=%h", a, b, R, exp);
        $fatal;
      end else begin
        $display("PASS: X=%h Y=%h -> %h", a, b, R);
      end
    end
  endtask

  initial begin
    // encoding: [33:32]=exception (00 normal), [31]=sign, [30:23]=exp, [22:0]=mantissa
    check(34'h03f000000, 34'h0bf800000, 34'h0bf000000); // 0.5 * -1.0 = -0.5
    check(34'h040400000, 34'h03f000000, 34'h03fc00000); // 3.0 * 0.5 = 1.5
    check(34'h0c0000000, 34'h0c0200000, 34'h040a00000); // -2.0 * -2.5 = 5.0
    check(34'h03f800000, 34'h03e800000, 34'h03e800000); // 1.0 * 0.25 = 0.25
    $display("All fp32_mul tests passed.");
    $finish;
  end
endmodule
