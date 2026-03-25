`timescale 1ns/1ps

module activation_leakyrelu_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_leakyrelu;

  leakyrelu_int8 dut_leakyrelu (.X(X), .Y(Y_leakyrelu));

  task check_leakyrelu;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_leakyrelu !== exp) begin
        $display("FAIL leakyrelu_int: X_raw=%0d got=%0d expected=%0d", a, Y_leakyrelu, exp);
        $fatal;
      end
    end
  endtask

  initial begin
    check_leakyrelu(-8'sd128, -8'sd16);
    check_leakyrelu(-8'sd16,  -8'sd2);
    check_leakyrelu(-8'sd8,   -8'sd1);
    check_leakyrelu(-8'sd7,    8'sd0);
    check_leakyrelu(-8'sd1,    8'sd0);
    check_leakyrelu(8'sd0,     8'sd0);
    check_leakyrelu(8'sd1,     8'sd1);
    check_leakyrelu(8'sd7,     8'sd7);
    check_leakyrelu(8'sd127,   8'sd127);
    $display("All int8 LeakyReLU tests passed.");
    $finish;
  end
endmodule
