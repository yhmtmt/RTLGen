`timescale 1ns/1ps

module activation_int_tb;
  reg  [7:0] X;
  wire [7:0] Y_relu;
  wire [7:0] Y_relu6;

  relu_int8 dut_relu (.X(X), .Y(Y_relu));
  relu6_int8 dut_relu6 (.X(X), .Y(Y_relu6));

  task check_relu;
    input [7:0] a;
    input [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_relu !== exp) begin
        $display("FAIL relu: X=%0d got=%0d expected=%0d", $signed(a), $signed(Y_relu), $signed(exp));
        $fatal;
      end
    end
  endtask

  task check_relu6;
    input [7:0] a;
    input [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_relu6 !== exp) begin
        $display("FAIL relu6: X=%0d got=%0d expected=%0d", $signed(a), $signed(Y_relu6), $signed(exp));
        $fatal;
      end
    end
  endtask

  initial begin
    check_relu(8'sd5, 8'sd5);
    check_relu(-8'sd3, 8'sd0);
    check_relu(8'sd0, 8'sd0);
    check_relu(-8'sd128, 8'sd0);

    check_relu6(8'sd7, 8'sd6);   // clamp
    check_relu6(8'sd5, 8'sd5);   // pass
    check_relu6(-8'sd2, 8'sd0);  // zero
    check_relu6(8'sd0, 8'sd0);

    $display("All integer activation tests passed.");
    $finish;
  end
endmodule
