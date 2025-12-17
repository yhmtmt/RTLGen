
module mult4s_normal_ripple_wrapper(
  input clk,
  input [3:0] multiplicand,
  input [3:0] multiplier,
  output [7:0] product
);

  reg [3:0] multiplicand_reg;
  reg [3:0] multiplier_reg;
  wire [7:0] product_wire;
  reg [7:0] product_reg;

  mult4s_normal_ripple dut (
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
