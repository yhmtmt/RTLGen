`timescale 1ns/1ps

module fp_mac_tb;
  reg  [31:0] A;
  reg  [31:0] B;
  reg  [31:0] C;
  reg         negateAB;
  reg         negateC;
  reg  [1:0]  RndMode;
  wire [31:0] R;

  fp32_mac dut (.A(A), .B(B), .C(C), .negateAB(negateAB), .negateC(negateC), .RndMode(RndMode), .R(R));

  task check;
    input [31:0] a;
    input [31:0] b;
    input [31:0] c;
    input [31:0] exp;
    begin
      A = a; B = b; C = c;
      negateAB = 1'b0;
      negateC = 1'b0;
      RndMode = 2'b00; // nearest-even
      #1;
      if (R !== exp) begin
        $display("FAIL: A=%h B=%h C=%h got=%h expected=%h", a, b, c, R, exp);
        $fatal;
      end else begin
        $display("PASS: A=%h B=%h C=%h -> %h", a, b, c, R);
      end
    end
  endtask

  initial begin
    check(32'h3f800000, 32'h40000000, 32'h40400000, 32'h40a00000); // 1.0*2.0+3.0 = 5.0
    check(32'hbf800000, 32'hc0000000, 32'hbf800000, 32'h3f800000); // -1.0*-2.0 + -1.0 = 1.0
    check(32'h3f000000, 32'h3f000000, 32'h3e800000, 32'h3f000000); // 0.5*0.5+0.25 = 0.5
    check(32'h00000000, 32'h40a00000, 32'h3f800000, 32'h3f800000); // 0.0*5.0+1.0 = 1.0
    $display("All fp32_mac tests passed.");
    $finish;
  end
endmodule
