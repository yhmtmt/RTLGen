`timescale 1ns/1ps

module fp_add_tb;
  reg  [33:0] X;
  reg  [33:0] Y;
  wire [33:0] R;

  fp32_add dut (.X(X), .Y(Y), .R(R));

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
    // exn bits set to 2'b01 for normal numbers
    check(34'h13f000000, 34'h13f800000, 34'h13fc00000); // 0.5 + 1.0 = 1.5
    check(34'h140400000, 34'h13f000000, 34'h140600000); // 3.0 + 0.5 = 3.5
    check(34'h1c0000000, 34'h1c0200000, 34'h1c0900000); // -2.0 + -2.5 = -4.5
    check(34'h100000000, 34'h140a00000, 34'h140a00000); // 0.0 + 5.0 = 5.0
    $display("All fp32_add tests passed.");
    $finish;
  end
endmodule
