`timescale 1ns/1ps

module activation_tanh_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_tanh;

  tanh_int8_pwl dut_tanh (.X(X), .Y(Y_tanh));

  task check_tanh;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_tanh !== exp) begin
        $display("FAIL tanh_pwl: X_raw=%0d got=%0d expected=%0d", a, Y_tanh, exp);
        $fatal;
      end
    end
  endtask

  reg signed [7:0] prev_y;
  reg signed [7:0] pos_y;
  reg signed [7:0] neg_y;

  initial begin
    check_tanh(-8'sd128, -8'sd16);  // clamp low to -1.0 in Q4
    check_tanh(-8'sd64,  -8'sd16);  // -4.0 -> saturated
    check_tanh(-8'sd32,  -8'sd16);  // -2.0 -> saturated
    check_tanh(-8'sd16,  -8'sd12);  // -1.0 -> -0.75
    check_tanh(8'sd0,     8'sd0);   // 0.0
    check_tanh(8'sd16,    8'sd12);  // 1.0 -> 0.75
    check_tanh(8'sd32,    8'sd16);  // 2.0 -> saturated
    check_tanh(8'sd64,    8'sd16);  // 4.0 -> saturated
    check_tanh(8'sd127,   8'sd16);  // clamp high

    // Monotonicity across representative samples.
    X = -8'sd64; #1; prev_y = Y_tanh;
    X = -8'sd32; #1; if (Y_tanh < prev_y) begin $display("FAIL tanh monotonic @ -2.0"); $fatal; end prev_y = Y_tanh;
    X = -8'sd16; #1; if (Y_tanh < prev_y) begin $display("FAIL tanh monotonic @ -1.0"); $fatal; end prev_y = Y_tanh;
    X = 8'sd16;  #1; if (Y_tanh < prev_y) begin $display("FAIL tanh monotonic @ 1.0"); $fatal; end prev_y = Y_tanh;
    X = 8'sd32;  #1; if (Y_tanh < prev_y) begin $display("FAIL tanh monotonic @ 2.0"); $fatal; end prev_y = Y_tanh;
    X = 8'sd64;  #1; if (Y_tanh < prev_y) begin $display("FAIL tanh monotonic @ 4.0"); $fatal; end

    // Odd symmetry at representative points.
    X = 8'sd16;  #1; pos_y = Y_tanh;
    X = -8'sd16; #1; neg_y = Y_tanh;
    if (neg_y !== -pos_y) begin $display("FAIL tanh odd symmetry @ 1.0"); $fatal; end

    X = 8'sd32;  #1; pos_y = Y_tanh;
    X = -8'sd32; #1; neg_y = Y_tanh;
    if (neg_y !== -pos_y) begin $display("FAIL tanh odd symmetry @ 2.0"); $fatal; end

    $display("All int8 tanh PWL tests passed.");
    $finish;
  end
endmodule
