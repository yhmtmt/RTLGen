
module adder_brentkung_32u_wrapper(
  input clk,
  input [31:0] a,
  input [31:0] b,
  output [31:0] sum,
  output cout
);

  reg [31:0] a_reg;
  reg [31:0] b_reg;
  wire [31:0] sum_wire;
  wire cout_wire;
  reg [31:0] sum_reg;
  reg cout_reg;

  adder_brentkung_32u dut (
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
