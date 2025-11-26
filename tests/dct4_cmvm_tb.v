`timescale 1ns/1ps

module dct4_cmvm_tb;
  reg  signed [9:0] dct_in_0;
  reg  signed [9:0] dct_in_1;
  reg  signed [9:0] dct_in_2;
  reg  signed [9:0] dct_in_3;
  wire signed [15:0] dct4_cmvm_out0;
  wire signed [15:0] dct4_cmvm_out1;
  wire signed [15:0] dct4_cmvm_out2;
  wire signed [15:0] dct4_cmvm_out3;

  dct4_cmvm dut (
    .dct_in_0(dct_in_0),
    .dct_in_1(dct_in_1),
    .dct_in_2(dct_in_2),
    .dct_in_3(dct_in_3),
    .dct4_cmvm_out0(dct4_cmvm_out0),
    .dct4_cmvm_out1(dct4_cmvm_out1),
    .dct4_cmvm_out2(dct4_cmvm_out2),
    .dct4_cmvm_out3(dct4_cmvm_out3)
  );

  task check_case(
    input integer v0,
    input integer v1,
    input integer v2,
    input integer v3,
    input integer exp0,
    input integer exp1,
    input integer exp2,
    input integer exp3
  );
    begin
      dct_in_0 = v0;
      dct_in_1 = v1;
      dct_in_2 = v2;
      dct_in_3 = v3;
      #1;
      if (dct4_cmvm_out0 !== exp0) begin
        $display("FAIL out0: vals=%0d,%0d,%0d,%0d got=%0d exp=%0d", v0,v1,v2,v3,dct4_cmvm_out0,exp0);
        $finish(1);
      end
      if (dct4_cmvm_out1 !== exp1) begin
        $display("FAIL out1: vals=%0d,%0d,%0d,%0d got=%0d exp=%0d", v0,v1,v2,v3,dct4_cmvm_out1,exp1);
        $finish(1);
      end
      if (dct4_cmvm_out2 !== exp2) begin
        $display("FAIL out2: vals=%0d,%0d,%0d,%0d got=%0d exp=%0d", v0,v1,v2,v3,dct4_cmvm_out2,exp2);
        $finish(1);
      end
      if (dct4_cmvm_out3 !== exp3) begin
        $display("FAIL out3: vals=%0d,%0d,%0d,%0d got=%0d exp=%0d", v0,v1,v2,v3,dct4_cmvm_out3,exp3);
        $finish(1);
      end
    end
  endtask

  initial begin
    // Matrix:
    // [ 13  17  17  13 ]
    // [ 18  10 -10 -18 ]
    // [ 17 -13 -13  17 ]
    // [ 10 -18  18 -10 ]
    // Outputs:
    // out0 = row0 + row2, out1 = row1 + row3, out2 = row2, out3 = row3
    check_case(1, 2, 3, 4, 170, -76, 20, -12);
    check_case(-1, -1, -1, -1, -68, 0, -8, 0);
    $display("PASS dct4_cmvm_tb");
    $finish;
  end
endmodule
