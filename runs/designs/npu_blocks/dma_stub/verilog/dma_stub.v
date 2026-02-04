module dma_stub(
  input  wire clk,
  input  wire rst_n,
  input  wire start,
  input  wire [63:0] src,
  input  wire [63:0] dst,
  input  wire [31:0] bytes,
  output reg  busy,
  output reg  done
);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start) begin
        busy <= 1'b1;
        done <= 1'b1;
        busy <= 1'b0;
      end
    end
  end
endmodule
