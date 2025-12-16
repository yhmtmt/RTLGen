
module adder_sklansky_8u_wrapper(
  input clk,
  input [7:0] a,
  input [7:0] b,
  output [7:0] sum,
  output cout
);

  reg [7:0] a_reg;
  reg [7:0] b_reg;
  wire [7:0] sum_wire;
  wire cout_wire;
  reg [7:0] sum_reg;
  reg cout_reg;

  adder_sklansky_8u dut (
    .a(a_reg),
    .b(b_reg),
    .sum(sum_wire),
    .cout(cout_wire)
  );

  always @(posedge clk) begin
    a_reg <= a;
    b_reg <= b;
    sum_reg <= sum_wire;
    cout_reg <= cout_wire;
  end

  assign sum = sum_reg;
  assign cout = cout_reg;

endmodule
