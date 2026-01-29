`timescale 1ns/1ps

module tb_axi_lite_mmio;
  localparam CLK_PERIOD = 10;
  localparam OFF_VERSION     = 32'h0000_0000;
  localparam OFF_CAPS        = 32'h0000_0004;
  localparam OFF_STATUS      = 32'h0000_0008;
  localparam OFF_CONTROL     = 32'h0000_000C;
  localparam OFF_IRQ_STATUS  = 32'h0000_0010;
  localparam OFF_IRQ_ENABLE  = 32'h0000_0014;
  localparam OFF_CQ_BASE_LO  = 32'h0000_0020;
  localparam OFF_CQ_BASE_HI  = 32'h0000_0024;
  localparam OFF_CQ_SIZE     = 32'h0000_0028;
  localparam OFF_CQ_HEAD     = 32'h0000_002C;
  localparam OFF_CQ_TAIL     = 32'h0000_0030;
  localparam OFF_DOORBELL    = 32'h0000_0040;

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

  axi_mem_router axi_mem (
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

  `include "npu/sim/rtl/axi_lite_host_tasks.svh"

  integer fd;
  integer bytes_read;
  integer max_bytes;
  reg [7:0] bin_data [0:4095];
  reg [1023:0] desc_path;
  reg [31:0] rdata;
  reg [31:0] cq_tail;
  reg [31:0] cq_head;
  reg [31:0] irq_status;
  integer test_bytes;
  reg [63:0] expected_src;
  reg [63:0] expected_dst;
  reg [31:0] expected_dma_bytes;

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

    // Read binary descriptor stream into CQ memory model.
    max_bytes = 4096;
    desc_path = "npu/mapper/examples/minimal_descriptors.bin";
    if ($value$plusargs("desc=%s", desc_path)) begin end
    fd = $fopen(desc_path, "rb");
    if (fd == 0) begin
      $display("ERROR: cannot open descriptor bin file %0s", desc_path);
      $finish(1);
    end
    bytes_read = $fread(bin_data, fd, 0, max_bytes);
    $fclose(fd);
    if (bytes_read <= 0) begin
      $display("ERROR: no bytes read from descriptor bin file");
      $finish(1);
    end

    // Read VERSION
    axi_lite_read(OFF_VERSION, rdata);
    if (rdata !== 32'h0001_0001) begin
      $display("ERROR: VERSION mismatch %h", rdata);
      $finish(1);
    end

    // Write IRQ_ENABLE
    host_init_mmio(32'h0000_0000, 32'h0000_0010, 32'h0000_1000, 32'h0000_0007);

    // Write CQ registers and doorbell
    if (!$value$plusargs("bytes=%d", test_bytes))
      test_bytes = bytes_read;
    expected_src = {bin_data[15], bin_data[14], bin_data[13], bin_data[12],
                    bin_data[11], bin_data[10], bin_data[9], bin_data[8]};
    expected_dst = {bin_data[23], bin_data[22], bin_data[21], bin_data[20],
                    bin_data[19], bin_data[18], bin_data[17], bin_data[16]};
    expected_dma_bytes = {bin_data[27], bin_data[26], bin_data[25], bin_data[24]};
    cq_tail = bytes_read[31:0];
    host_submit_cq(cq_tail);

    // Expect DMA request and accept it
    repeat (5) @(posedge clk);
    if (dma_req_valid !== 1'b1) begin
      $display("ERROR: expected dma_req_valid via AXI-Lite wrapper");
      $finish(1);
    end
    if (dma_req_src !== expected_src) begin
      $display("ERROR: dma_req_src mismatch %h", dma_req_src);
      $finish(1);
    end
    if (dma_req_dst !== expected_dst) begin
      $display("ERROR: dma_req_dst mismatch %h", dma_req_dst);
      $finish(1);
    end
    if (dma_req_bytes !== expected_dma_bytes) begin
      $display("ERROR: dma_req_bytes mismatch %h", dma_req_bytes);
      $finish(1);
    end
    dma_req_ready = 1'b1;
    @(posedge clk);
    dma_req_ready = 1'b0;

    // Read IRQ_STATUS
    host_wait_irq(600, 32'h0000_0002, irq_status);
    host_wait_cq_head(cq_tail, 20, cq_head);
    if (cq_head !== cq_tail) begin
      $display("ERROR: cq_head %h != cq_tail %h", cq_head, cq_tail);
      $finish(1);
    end

    axi_lite_read(OFF_IRQ_STATUS, irq_status);
    if (irq_status[0] !== 1'b1) begin
      $display("ERROR: expected CQ_EMPTY IRQ status via AXI-Lite");
      $finish(1);
    end
    if (irq_status[1] !== 1'b1) begin
      $display("ERROR: expected EVENT IRQ status via AXI-Lite");
      $finish(1);
    end

    // Check DMA copy data in memory model.
    for (j = 0; j < test_bytes; j = j + 1) begin
      if (axi_mem.mem[expected_dst[20:0] + j] !== axi_mem.mem[expected_src[20:0] + j]) begin
        $display("ERROR: DMA copy mismatch at byte %0d", j);
        $finish(1);
      end
    end

    $display("PASS: AXI-Lite MMIO wrapper");
    $finish(0);
  end

  // Simple command queue memory model: map cq_mem_addr to bin_data
  always @(*) begin
    integer i;
    integer base;
    reg [255:0] rdata_next;
    base = cq_mem_addr[11:0];
    rdata_next = 0;
    for (i = 0; i < 32; i = i + 1) begin
      if ((base + i) < 4096)
        rdata_next[(i*8) +: 8] = bin_data[base + i];
    end
    cq_mem_rdata = rdata_next;
  end

endmodule
