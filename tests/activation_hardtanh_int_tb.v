`timescale 1ns/1ps

module activation_hardtanh_int_tb;
  reg signed [7:0] X;
  wire signed [7:0] Y_hardtanh;

  hardtanh_int8_pwl dut_hardtanh (.X(X), .Y(Y_hardtanh));

  task check_hardtanh;
    input signed [7:0] a;
    input signed [7:0] exp;
    begin
      X = a;
      #1;
      if (Y_hardtanh !== exp) begin
        $display("FAIL hardtanh_pwl: X_raw=%0d got=%0d expected=%0d", a, Y_hardtanh, exp);
        $fatal;
      end
    end
  endtask

  initial begin
    check_hardtanh(-8'sd128, -8'sd16);
    check_hardtanh(-8'sd32,  -8'sd16);
    check_hardtanh(-8'sd16,  -8'sd16);
    check_hardtanh(-8'sd8,   -8'sd8);
    check_hardtanh(8'sd0,     8'sd0);
    check_hardtanh(8'sd8,     8'sd8);
    check_hardtanh(8'sd16,    8'sd16);
    check_hardtanh(8'sd32,    8'sd16);
    check_hardtanh(8'sd127,   8'sd16);
    $display("All int8 hardtanh PWL tests passed.");
    $finish;
  end
endmodule
