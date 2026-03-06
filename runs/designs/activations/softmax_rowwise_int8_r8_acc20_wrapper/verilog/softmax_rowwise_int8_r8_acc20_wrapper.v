
module softmax_rowwise_int8_r8_acc20_wrapper(
  input clk,
  input [63:0] X,
  output [63:0] Y
);

  reg [63:0] x_reg;
  wire [63:0] y_wire;
  reg [63:0] y_reg;

  softmax_rowwise_int8_r8_acc20 dut (
    .X(x_reg),
    .Y(y_wire)
  );

  always @(posedge clk) begin
    x_reg <= X;
    y_reg <= y_wire;
  end

  assign Y = y_reg;

endmodule
