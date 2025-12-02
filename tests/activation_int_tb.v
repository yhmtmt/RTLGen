`timescale 1ns/1ps

module activation_int_tb;
  reg  [7:0] X;
  wire [7:0] Y_relu;
  wire [7:0] Y_relu6;
  wire [7:0] Y_leaky;
  wire [7:0] Y_tanh;
  wire [7:0] Y_gelu;

  relu_int8 dut_relu (.X(X), .Y(Y_relu));
  relu6_int8 dut_relu6 (.X(X), .Y(Y_relu6));
  leakyrelu_int8 dut_leaky (.X(X), .Y(Y_leaky));
  tanh_int8 dut_tanh (.X(X), .Y(Y_tanh));
  gelu_int8 dut_gelu (.X(X), .Y(Y_gelu));

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

  task check_leaky;
    input [7:0] a;
    input [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_leaky !== exp) begin
        $display("FAIL leaky_relu: X=%0d got=%0d expected=%0d", $signed(a), $signed(Y_leaky), $signed(exp));
        $fatal;
      end
    end
  endtask

  task check_gelu;
    input [7:0] a;
    input [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_gelu !== exp) begin
        $display("FAIL gelu: X=%0d got=%0d expected=%0d", $signed(a), $signed(Y_gelu), $signed(exp));
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

    check_leaky(-8'sd8, -8'sd2); // alpha 1/4
    check_leaky(8'sd8, 8'sd8);

    // tanh clamps to +/- max
    X = 8'sd50; #1; if (Y_tanh !== 8'sh7f) begin $display("FAIL tanh pos clamp"); $fatal; end
    X = -8'sd50; #1; if (Y_tanh !== 8'sh81) begin $display("FAIL tanh neg clamp"); $fatal; end

    check_gelu(-8'sd8, 8'sd0);
    check_gelu(8'sd8, 8'sd4); // approx 0.5*x

    $display("All integer activation tests passed.");
    $finish;
  end
endmodule
