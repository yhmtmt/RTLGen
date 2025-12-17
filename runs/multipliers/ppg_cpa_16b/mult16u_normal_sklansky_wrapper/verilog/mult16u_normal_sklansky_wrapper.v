
module mult16u_normal_sklansky_wrapper(
  input clk,
  input [15:0] multiplicand,
  input [15:0] multiplier,
  output [31:0] product
);

  reg [15:0] multiplicand_reg;
  reg [15:0] multiplier_reg;
  wire [31:0] product_wire;
  reg [31:0] product_reg;

  mult16u_normal_sklansky dut (
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
