
module mult32s_normal_sklansky_wrapper(
  input clk,
  input [31:0] multiplicand,
  input [31:0] multiplier,
  output [63:0] product
);

  reg [31:0] multiplicand_reg;
  reg [31:0] multiplier_reg;
  wire [63:0] product_wire;
  reg [63:0] product_reg;

  mult32s_normal_sklansky dut (
    .multiplicand(multiplicand_reg),
    .multiplier(multiplier_reg),
    .product(product_wire)
  );

  always @(posedge clk) begin
    multiplicand_reg <= multiplicand;
    multiplier_reg <= multiplier;
    product_reg <= product_wire;
  end

  assign product = product_reg;

endmodule
