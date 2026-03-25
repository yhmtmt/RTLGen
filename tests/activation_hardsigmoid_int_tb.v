`timescale 1ns/1ps

module activation_hardsigmoid_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_hardsigmoid;

  hardsigmoid_int8_pwl dut_hardsigmoid (.X(X), .Y(Y_hardsigmoid));

  task check_hardsigmoid;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_hardsigmoid !== exp) begin
        $display("FAIL hardsigmoid_pwl: X_raw=%0d got=%0d expected=%0d", a, Y_hardsigmoid, exp);
        $fatal;
      end
    end
  endtask

  reg signed [7:0] prev_y;

  initial begin
    check_hardsigmoid(-8'sd128, 8'sd0);   // clamp low
    check_hardsigmoid(-8'sd48,  8'sd0);   // below -2.625 breakpoint -> 0.0
    check_hardsigmoid(-8'sd16,  8'sd5);   // -1.0 -> about 0.3125
    check_hardsigmoid(8'sd0,    8'sd8);   // 0.0 -> 0.5
    check_hardsigmoid(8'sd16,   8'sd11);  // 1.0 -> about 0.6875
    check_hardsigmoid(8'sd48,   8'sd16);  // above 2.6875 breakpoint -> 1.0
    check_hardsigmoid(8'sd127,  8'sd16);  // clamp high

    X = -8'sd64; #1; prev_y = Y_hardsigmoid;
    X = -8'sd48; #1; if (Y_hardsigmoid < prev_y) begin $display("FAIL hardsigmoid monotonic @ -3.0"); $fatal; end prev_y = Y_hardsigmoid;
    X = -8'sd16; #1; if (Y_hardsigmoid < prev_y) begin $display("FAIL hardsigmoid monotonic @ -1.0"); $fatal; end prev_y = Y_hardsigmoid;
    X = 8'sd0;   #1; if (Y_hardsigmoid < prev_y) begin $display("FAIL hardsigmoid monotonic @ 0.0"); $fatal; end prev_y = Y_hardsigmoid;
    X = 8'sd16;  #1; if (Y_hardsigmoid < prev_y) begin $display("FAIL hardsigmoid monotonic @ 1.0"); $fatal; end prev_y = Y_hardsigmoid;
    X = 8'sd48;  #1; if (Y_hardsigmoid < prev_y) begin $display("FAIL hardsigmoid monotonic @ 3.0"); $fatal; end

    $display("All int8 hard-sigmoid PWL tests passed.");
    $finish;
  end
endmodule
