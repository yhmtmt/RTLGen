
module adder_koggestone_16u_wrapper(
  input clk,
  input [15:0] a,
  input [15:0] b,
  output [15:0] sum,
  output cout
);

  reg [15:0] a_reg;
  reg [15:0] b_reg;
  wire [15:0] sum_wire;
  wire cout_wire;
  reg [15:0] sum_reg;
  reg cout_reg;

  adder_koggestone_16u dut (
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
