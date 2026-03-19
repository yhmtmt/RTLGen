`timescale 1ns/1ps

module activation_sigmoid_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_sigmoid;

  sigmoid_int8_pwl dut_sigmoid (.X(X), .Y(Y_sigmoid));

  task check_sigmoid;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_sigmoid !== exp) begin
        $display("FAIL sigmoid_pwl: X_raw=%0d got=%0d expected=%0d", a, Y_sigmoid, exp);
        $fatal;
      end
    end
  endtask

  reg signed [7:0] prev_y;

  initial begin
    check_sigmoid(-8'sd128, 8'sd0);  // clamp low
    check_sigmoid(-8'sd64, 8'sd0);   // -4.0
    check_sigmoid(-8'sd32, 8'sd2);   // -2.0 -> 0.125 in Q4
    check_sigmoid(8'sd0, 8'sd8);     // 0.5 in Q4
    check_sigmoid(8'sd32, 8'sd14);   // 0.875 in Q4
    check_sigmoid(8'sd64, 8'sd16);   // 1.0 in Q4
    check_sigmoid(8'sd127, 8'sd16);  // clamp high

    // Monotonicity across representative samples.
    X = -8'sd64; #1; prev_y = Y_sigmoid;
    X = -8'sd48; #1; if (Y_sigmoid < prev_y) begin $display("FAIL sigmoid monotonic @ -3.0"); $fatal; end prev_y = Y_sigmoid;
    X = -8'sd16; #1; if (Y_sigmoid < prev_y) begin $display("FAIL sigmoid monotonic @ -1.0"); $fatal; end prev_y = Y_sigmoid;
    X = 8'sd16;  #1; if (Y_sigmoid < prev_y) begin $display("FAIL sigmoid monotonic @ 1.0"); $fatal; end prev_y = Y_sigmoid;
    X = 8'sd48;  #1; if (Y_sigmoid < prev_y) begin $display("FAIL sigmoid monotonic @ 3.0"); $fatal; end

    $display("All int8 sigmoid PWL tests passed.");
    $finish;
  end
endmodule
