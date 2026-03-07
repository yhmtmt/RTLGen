// Simple 1R1W SRAM model (behavioral, for simulation)
module sram_1r1w #(
    parameter ADDR_WIDTH = 10,
    parameter DATA_WIDTH = 32,
    parameter READ_LATENCY = 1,
    parameter BYTE_ENABLE = 1
) (
    input  wire                  clk,
    input  wire                  we,
    input  wire [ADDR_WIDTH-1:0] waddr,
    input  wire [DATA_WIDTH-1:0] wdata,
    input  wire [(DATA_WIDTH/8)-1:0] wstrb,
    input  wire                  re,
    input  wire [ADDR_WIDTH-1:0] raddr,
    output reg  [DATA_WIDTH-1:0] rdata
);
  reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];
  reg [DATA_WIDTH-1:0] rdata_pipe [0:READ_LATENCY-1];
  integer i;

  always @(posedge clk) begin
    if (we) begin
      if (BYTE_ENABLE) begin
        for (i = 0; i < (DATA_WIDTH/8); i = i + 1) begin
          if (wstrb[i])
            mem[waddr][(i*8)+7 -: 8] <= wdata[(i*8)+7 -: 8];
        end
      end else begin
        mem[waddr] <= wdata;
      end
    end
    if (re) begin
      rdata_pipe[0] <= mem[raddr];
      for (i = 1; i < READ_LATENCY; i = i + 1)
        rdata_pipe[i] <= rdata_pipe[i-1];
      rdata <= rdata_pipe[READ_LATENCY-1];
    end
  end
endmodule


// Auto-generated SRAM instance wrapper
module activation_sram (
    input  wire                  clk,
    input  wire                  we,
    input  wire [13:0] waddr,
    input  wire [255:0] wdata,
    input  wire [31:0] wstrb,
    input  wire                  re,
    input  wire [13:0] raddr,
    output wire [255:0] rdata
);
  sram_1r1w #(
    .ADDR_WIDTH(14),
    .DATA_WIDTH(256),
    .READ_LATENCY(1),
    .BYTE_ENABLE(1)
  ) u_mem (
    .clk(clk),
    .we(we),
    .waddr(waddr),
    .wdata(wdata),
    .wstrb(wstrb),
    .re(re),
    .raddr(raddr),
    .rdata(rdata)
  );
endmodule

