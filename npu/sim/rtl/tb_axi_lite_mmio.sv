`timescale 1ns/1ps

module tb_axi_lite_mmio;
  localparam CLK_PERIOD = 10;

  reg clk;
  reg rst_n;

  reg  [31:0] s_axi_awaddr;
  reg         s_axi_awvalid;
  wire        s_axi_awready;
  reg  [31:0] s_axi_wdata;
  reg  [3:0]  s_axi_wstrb;
  reg         s_axi_wvalid;
  wire        s_axi_wready;
  wire [1:0]  s_axi_bresp;
  wire        s_axi_bvalid;
  reg         s_axi_bready;
  reg  [31:0] s_axi_araddr;
  reg         s_axi_arvalid;
  wire        s_axi_arready;
  wire [31:0] s_axi_rdata;
  wire [1:0]  s_axi_rresp;
  wire        s_axi_rvalid;
  reg         s_axi_rready;
  wire        irq;
  wire        dma_req_valid;
  wire [63:0] dma_req_src;
  wire [63:0] dma_req_dst;
  wire [31:0] dma_req_bytes;
  reg         dma_req_ready;
  reg         dma_resp_done;
  wire [63:0] cq_mem_addr;
  reg [255:0] cq_mem_rdata;
  wire        m_axi_awvalid;
  reg         m_axi_awready;
  wire [63:0] m_axi_awaddr;
  wire [7:0]  m_axi_awlen;
  wire [2:0]  m_axi_awsize;
  wire        m_axi_wvalid;
  reg         m_axi_wready;
  wire [255:0] m_axi_wdata;
  wire [31:0] m_axi_wstrb;
  wire        m_axi_wlast;
  reg         m_axi_bvalid;
  wire        m_axi_bready;
  wire        m_axi_arvalid;
  reg         m_axi_arready;
  wire [63:0] m_axi_araddr;
  wire [7:0]  m_axi_arlen;
  wire [2:0]  m_axi_arsize;
  reg         m_axi_rvalid;
  wire        m_axi_rready;
  reg [255:0] m_axi_rdata;
  reg         m_axi_rlast;
  reg [7:0]   mem_bytes [0:4095];
  integer     j;

  npu_top_axi dut (
    .clk(clk),
    .rst_n(rst_n),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .irq(irq),
    .dma_req_valid(dma_req_valid),
    .dma_req_src(dma_req_src),
    .dma_req_dst(dma_req_dst),
    .dma_req_bytes(dma_req_bytes),
    .dma_req_ready(dma_req_ready),
    .dma_resp_done(dma_resp_done),
    .cq_mem_addr(cq_mem_addr),
    .cq_mem_rdata(cq_mem_rdata),
    .m_axi_awvalid(m_axi_awvalid),
    .m_axi_awready(m_axi_awready),
    .m_axi_awaddr(m_axi_awaddr),
    .m_axi_awlen(m_axi_awlen),
    .m_axi_awsize(m_axi_awsize),
    .m_axi_wvalid(m_axi_wvalid),
    .m_axi_wready(m_axi_wready),
    .m_axi_wdata(m_axi_wdata),
    .m_axi_wstrb(m_axi_wstrb),
    .m_axi_wlast(m_axi_wlast),
    .m_axi_bvalid(m_axi_bvalid),
    .m_axi_bready(m_axi_bready),
    .m_axi_arvalid(m_axi_arvalid),
    .m_axi_arready(m_axi_arready),
    .m_axi_araddr(m_axi_araddr),
    .m_axi_arlen(m_axi_arlen),
    .m_axi_arsize(m_axi_arsize),
    .m_axi_rvalid(m_axi_rvalid),
    .m_axi_rready(m_axi_rready),
    .m_axi_rdata(m_axi_rdata),
    .m_axi_rlast(m_axi_rlast)
  );

  axi_mem_model axi_mem (
    .clk(clk),
    .rst_n(rst_n),
    .m_axi_awvalid(m_axi_awvalid),
    .m_axi_awready(m_axi_awready),
    .m_axi_awaddr(m_axi_awaddr),
    .m_axi_awlen(m_axi_awlen),
    .m_axi_awsize(m_axi_awsize),
    .m_axi_wvalid(m_axi_wvalid),
    .m_axi_wready(m_axi_wready),
    .m_axi_wdata(m_axi_wdata),
    .m_axi_wstrb(m_axi_wstrb),
    .m_axi_wlast(m_axi_wlast),
    .m_axi_bvalid(m_axi_bvalid),
    .m_axi_bready(m_axi_bready),
    .m_axi_arvalid(m_axi_arvalid),
    .m_axi_arready(m_axi_arready),
    .m_axi_araddr(m_axi_araddr),
    .m_axi_arlen(m_axi_arlen),
    .m_axi_arsize(m_axi_arsize),
    .m_axi_rvalid(m_axi_rvalid),
    .m_axi_rready(m_axi_rready),
    .m_axi_rdata(m_axi_rdata),
    .m_axi_rlast(m_axi_rlast)
  );

  initial clk = 0;
  always #(CLK_PERIOD/2) clk = ~clk;

  task axi_write(input [31:0] addr, input [31:0] data);
    begin
      @(posedge clk);
      s_axi_awaddr <= addr;
      s_axi_awvalid <= 1'b1;
      s_axi_wdata <= data;
      s_axi_wstrb <= 4'hF;
      s_axi_wvalid <= 1'b1;
      s_axi_bready <= 1'b1;
      wait (s_axi_awready && s_axi_wready);
      @(posedge clk);
      s_axi_awvalid <= 1'b0;
      s_axi_wvalid <= 1'b0;
      wait (s_axi_bvalid);
      @(posedge clk);
      s_axi_bready <= 1'b0;
    end
  endtask

  task axi_read(input [31:0] addr, output [31:0] data);
    begin
      @(posedge clk);
      s_axi_araddr <= addr;
      s_axi_arvalid <= 1'b1;
      s_axi_rready <= 1'b1;
      wait (s_axi_arready);
      @(posedge clk);
      s_axi_arvalid <= 1'b0;
      wait (s_axi_rvalid);
      data = s_axi_rdata;
      @(posedge clk);
      s_axi_rready <= 1'b0;
    end
  endtask

  reg [31:0] rdata;

  initial begin
    s_axi_awaddr = 0;
    s_axi_awvalid = 0;
    s_axi_wdata = 0;
    s_axi_wstrb = 0;
    s_axi_wvalid = 0;
    s_axi_bready = 0;
    s_axi_araddr = 0;
    s_axi_arvalid = 0;
    s_axi_rready = 0;
    dma_req_ready = 0;
    dma_resp_done = 0;
    cq_mem_rdata = 0;
    rst_n = 0;
    #(CLK_PERIOD*4);
    rst_n = 1;

    // Init small memory and CQ data
    for (j = 0; j < 4096; j = j + 1) begin
      mem_bytes[j] = j[7:0];
    end

    // Read VERSION
    axi_read(32'h0000_0000, rdata);
    if (rdata !== 32'h0001_0001) begin
      $display("ERROR: VERSION mismatch %h", rdata);
      $finish(1);
    end

    // Write IRQ_ENABLE
    axi_write(32'h0000_0014, 32'h0000_0007);

    // Feed a single DMA_COPY descriptor via CQ memory model
    // Descriptor layout: header + src/dst/size.
    cq_mem_rdata = 0;
    cq_mem_rdata[7:0] = 8'h01; // DMA_COPY
    cq_mem_rdata[63:32] = 32'h0000_0001;
    cq_mem_rdata[127:64] = 64'h0000_0000_0000_0000;
    cq_mem_rdata[191:128] = 64'h0000_0000_0000_0100;
    cq_mem_rdata[223:192] = 32'h0000_0020; // 32 bytes

    // Write CQ registers and doorbell
    axi_write(32'h0000_0020, 32'h0000_0000);
    axi_write(32'h0000_0024, 32'h0000_0010);
    axi_write(32'h0000_0028, 32'h0000_1000);
    axi_write(32'h0000_0030, 32'h0000_0020); // one descriptor
    axi_write(32'h0000_0040, 32'h0000_0001);

    // Read IRQ_STATUS
    begin : wait_irq
      integer t;
      for (t = 0; t < 20; t = t + 1) begin
        axi_read(32'h0000_0010, rdata);
        if (rdata[0] === 1'b1)
          disable wait_irq;
      end
    end
    if (rdata[0] !== 1'b1) begin
      $display("ERROR: expected CQ_EMPTY IRQ status via AXI-Lite");
      $finish(1);
    end

    // Expect DMA request and accept it
    repeat (5) @(posedge clk);
    if (dma_req_valid !== 1'b1) begin
      $display("ERROR: expected dma_req_valid via AXI-Lite wrapper");
      $finish(1);
    end
    dma_req_ready = 1'b1;
    @(posedge clk);
    dma_req_ready = 1'b0;

    $display("PASS: AXI-Lite MMIO wrapper");
    $finish(0);
  end

endmodule
