`timescale 1ns/1ps

module mac_pp_feedback_tb;
  reg  [7:0] multiplicand;
  reg  [7:0] multiplier;
  reg  [15:0] accumulator;
  wire [15:0] result;
  reg signed [15:0] expected;
  integer i;

  int8_mac_pp_feedback dut (
    .multiplicand(multiplicand),
    .multiplier(multiplier),
    .accumulator(accumulator),
    .result(result)
  );

  initial begin
    for (i = 0; i < 200; i = i + 1) begin
      multiplicand = $random;
      multiplier = $random;
      accumulator = $random;
      #1;
      expected = $signed(multiplicand) * $signed(multiplier) + $signed(accumulator);
      if ($signed(result) !== expected) begin
        $display("FAIL i=%0d a=%0d b=%0d acc=%0d got=%0d expected=%0d",
                 i, $signed(multiplicand), $signed(multiplier), $signed(accumulator),
                 $signed(result), expected);
        $fatal;
      end
    end
    $display("PASS: MAC pp_row_feedback tests completed.");
    $finish;
  end
endmodule
