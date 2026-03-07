
module softmax_rowwise_int8_r4_wrapper(
  input clk,
  input [31:0] X,
  output [31:0] Y
);

  reg [31:0] x_reg;
  wire [31:0] y_wire;
  reg [31:0] y_reg;

  softmax_rowwise_int8_r4 dut (
    .X(x_reg),
    .Y(y_wire)
  );

  always @(posedge clk) begin
    x_reg <= X;
    y_reg <= y_wire;
  end

  assign Y = y_reg;

endmodule
