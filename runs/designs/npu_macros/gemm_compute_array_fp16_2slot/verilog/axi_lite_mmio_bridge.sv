// Simple AXI-Lite to MMIO bridge (single-beat)
module axi_lite_mmio_bridge (
    input  wire                  clk,
    input  wire                  rst_n,
    // AXI-Lite slave interface
    input  wire [31:0]           s_axi_awaddr,
    input  wire                  s_axi_awvalid,
    output reg                   s_axi_awready,
    input  wire [31:0] s_axi_wdata,
    input  wire [(32/8)-1:0]    s_axi_wstrb,
    input  wire                  s_axi_wvalid,
    output reg                   s_axi_wready,
    output reg  [1:0]            s_axi_bresp,
    output reg                   s_axi_bvalid,
    input  wire                  s_axi_bready,
    input  wire [31:0]           s_axi_araddr,
    input  wire                  s_axi_arvalid,
    output reg                   s_axi_arready,
    output reg  [31:0] s_axi_rdata,
    output reg  [1:0]            s_axi_rresp,
    output reg                   s_axi_rvalid,
    input  wire                  s_axi_rready,
    // MMIO side
    output reg  [11:0] mmio_addr,
    output reg                   mmio_we,
    output reg  [31:0] mmio_wdata,
    input  wire [31:0] mmio_rdata
);

  reg read_pending;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s_axi_awready <= 1'b0;
      s_axi_wready <= 1'b0;
      s_axi_bvalid <= 1'b0;
      s_axi_bresp <= 2'b00;
      s_axi_arready <= 1'b0;
      s_axi_rvalid <= 1'b0;
      s_axi_rresp <= 2'b00;
      s_axi_rdata <= 0;
      mmio_addr <= 0;
      mmio_we <= 1'b0;
      mmio_wdata <= 0;
      read_pending <= 1'b0;
    end else begin
      s_axi_awready <= s_axi_awvalid;
      s_axi_wready <= s_axi_wvalid;
      s_axi_arready <= (!read_pending && !s_axi_rvalid);
      mmio_we <= 1'b0;

      if (s_axi_awvalid && s_axi_wvalid) begin
        mmio_addr <= s_axi_awaddr[11:0];
        mmio_wdata <= s_axi_wdata;
        mmio_we <= 1'b1;
        s_axi_bvalid <= 1'b1;
        s_axi_bresp <= 2'b00;
      end

      if (s_axi_bvalid && s_axi_bready)
        s_axi_bvalid <= 1'b0;

      if (s_axi_arvalid && s_axi_arready) begin
        mmio_addr <= s_axi_araddr[11:0];
        read_pending <= 1'b1;
      end

      if (read_pending && !s_axi_rvalid) begin
        s_axi_rdata <= mmio_rdata;
        s_axi_rvalid <= 1'b1;
        s_axi_rresp <= 2'b00;
        read_pending <= 1'b0;
      end

      if (s_axi_rvalid && s_axi_rready) begin
        s_axi_rvalid <= 1'b0;
      end
    end
  end

endmodule
