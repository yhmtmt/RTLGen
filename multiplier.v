module multiplier #(
    parameter DATA_WIDTH = 8,
    parameter SIGNED_MULT = 0 // 0 for unsigned, 1 for signed
) (
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] a,
    input [DATA_WIDTH-1:0] b,
    output reg [2*DATA_WIDTH-1:0] p
);

    // Your multiplication logic here
    // For example, a simple combinational implementation:
    always @(*) begin
        if (SIGNED_MULT) begin
            p = $signed(a) * $signed(b);
        end else begin
            p = a * b;
        end
    end

endmodule
