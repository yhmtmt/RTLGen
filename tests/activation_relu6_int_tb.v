`timescale 1ns/1ps

module activation_relu6_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_relu6;

  relu6_int8 dut_relu6 (.X(X), .Y(Y_relu6));

  task check_relu6;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_relu6 !== exp) begin
        $display("FAIL relu6_int: X_raw=%0d got=%0d expected=%0d", a, Y_relu6, exp);
        $fatal;
      end
    end
  endtask

  initial begin
    check_relu6(-8'sd128, 8'sd0);
    check_relu6(-8'sd1,   8'sd0);
    check_relu6(8'sd0,    8'sd0);
    check_relu6(8'sd1,    8'sd1);
    check_relu6(8'sd5,    8'sd5);
    check_relu6(8'sd6,    8'sd6);
    check_relu6(8'sd7,    8'sd6);
    check_relu6(8'sd127,  8'sd6);
    $display("All int8 ReLU6 tests passed.");
    $finish;
  end
endmodule
