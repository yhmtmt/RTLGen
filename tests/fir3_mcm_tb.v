`timescale 1ns/1ps

module fir3_mcm_tb;
  reg  signed [11:0] sample_0;
  wire signed [18:0] fir3_mcm_out0;
  wire signed [18:0] fir3_mcm_out1;
  wire signed [18:0] fir3_mcm_out2;

  fir3_mcm dut (
    .sample_0(sample_0),
    .fir3_mcm_out0(fir3_mcm_out0),
    .fir3_mcm_out1(fir3_mcm_out1),
    .fir3_mcm_out2(fir3_mcm_out2)
  );

  task check_case(input integer val);
    begin
      sample_0 = val;
      #1;
      if (fir3_mcm_out0 !== 23 * val) begin
        $display("FAIL out0: val=%0d got=%0d exp=%0d", val, fir3_mcm_out0, 23 * val);
        $finish(1);
      end
      if (fir3_mcm_out1 !== 45 * val) begin
        $display("FAIL out1: val=%0d got=%0d exp=%0d", val, fir3_mcm_out1, 45 * val);
        $finish(1);
      end
      if (fir3_mcm_out2 !== 97 * val) begin
        $display("FAIL out2: val=%0d got=%0d exp=%0d", val, fir3_mcm_out2, 97 * val);
        $finish(1);
      end
    end
  endtask

  initial begin
    check_case(0);
    check_case(7);
    check_case(-8);
    $display("PASS fir3_mcm_tb");
    $finish;
  end
endmodule
