`timescale 1ns/1ps

module adder_skew_tb;
  reg  [7:0] a;
  reg  [7:0] b;
  wire [7:0] sum;
  wire cout;

  skewprefix_adder8 dut (
    .a(a),
    .b(b),
    .sum(sum),
    .cout(cout)
  );

  integer i, j;
  initial begin
    for (i = 0; i < 64; i = i + 1) begin
      for (j = 0; j < 64; j = j + 1) begin
        a = i[7:0];
        b = j[7:0];
        #1;
        if ({cout, sum} !== (a + b)) begin
          $display("FAIL a=%0d b=%0d got=%0d exp=%0d", a, b, {cout, sum}, a + b);
          $finish(1);
        end
      end
    end
    $display("PASS adder_skew_tb");
    $finish;
  end
endmodule
