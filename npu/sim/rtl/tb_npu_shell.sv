`timescale 1ns/1ps

module tb_npu_shell;
  localparam CLK_PERIOD = 10;
  localparam MMIO_ADDR_W = 12;
  localparam DATA_W = 32;

  // MMIO offsets (match npu/rtlgen/gen.py)
  localparam OFF_VERSION     = 12'h000;
  localparam OFF_CAPS        = 12'h004;
  localparam OFF_STATUS      = 12'h008;
  localparam OFF_CONTROL     = 12'h00C;
  localparam OFF_IRQ_STATUS  = 12'h010;
  localparam OFF_IRQ_ENABLE  = 12'h014;
  localparam OFF_CQ_BASE_LO  = 12'h020;
  localparam OFF_CQ_BASE_HI  = 12'h024;
  localparam OFF_CQ_SIZE     = 12'h028;
  localparam OFF_CQ_HEAD     = 12'h02C;
  localparam OFF_CQ_TAIL     = 12'h030;
  localparam OFF_DOORBELL    = 12'h040;

  reg clk;
  reg rst_n;
  reg [MMIO_ADDR_W-1:0] mmio_addr;
  reg mmio_we;
  reg [DATA_W-1:0] mmio_wdata;
  wire [DATA_W-1:0] mmio_rdata;
  wire irq;
  wire dma_req_valid;
  wire [63:0] dma_req_src;
  wire [63:0] dma_req_dst;
  wire [31:0] dma_req_bytes;
  reg dma_req_ready;
  reg dma_resp_done;
  wire [63:0] cq_mem_addr;
  reg [255:0] cq_mem_rdata;
  wire m_axi_awvalid;
  reg  m_axi_awready;
  wire [63:0] m_axi_awaddr;
  wire [7:0] m_axi_awlen;
  wire [2:0] m_axi_awsize;
  wire m_axi_wvalid;
  reg  m_axi_wready;
  wire [255:0] m_axi_wdata;
  wire [31:0] m_axi_wstrb;
  wire m_axi_wlast;
  reg  m_axi_bvalid;
  wire m_axi_bready;
  wire m_axi_arvalid;
  reg  m_axi_arready;
  wire [63:0] m_axi_araddr;
  wire [7:0] m_axi_arlen;
  wire [2:0] m_axi_arsize;
  reg  m_axi_rvalid;
  wire m_axi_rready;
  reg [255:0] m_axi_rdata;
  reg  m_axi_rlast;
  reg  saw_bvalid;

  npu_top dut (
    .clk(clk),
    .rst_n(rst_n),
    .mmio_addr(mmio_addr),
    .mmio_we(mmio_we),
    .mmio_wdata(mmio_wdata),
    .mmio_rdata(mmio_rdata),
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

  initial clk = 0;
  always #(CLK_PERIOD/2) clk = ~clk;

  task mmio_write(input [MMIO_ADDR_W-1:0] addr, input [DATA_W-1:0] data);
    begin
      @(posedge clk);
      mmio_addr <= addr;
      mmio_wdata <= data;
      mmio_we <= 1'b1;
      @(posedge clk);
      mmio_we <= 1'b0;
      mmio_addr <= 0;
      mmio_wdata <= 0;
    end
  endtask

  task mmio_read(input [MMIO_ADDR_W-1:0] addr, output [DATA_W-1:0] data);
    begin
      @(posedge clk);
      mmio_addr <= addr;
      mmio_we <= 1'b0;
      @(posedge clk);
      data = mmio_rdata;
      mmio_addr <= 0;
    end
  endtask

  integer fd;
  integer bytes_read;
  integer max_bytes;
  reg [7:0] bin_data [0:4095];
  integer j;
  reg [DATA_W-1:0] cq_tail;
  reg [DATA_W-1:0] cq_head;
  reg [DATA_W-1:0] irq_status;
  integer test_bytes;
  reg [DATA_W-1:0] expected_dma_bytes;

  initial begin
    mmio_addr = 0;
    mmio_we = 0;
    mmio_wdata = 0;
    rst_n = 0;
    dma_req_ready = 0;
    dma_resp_done = 0;
    saw_bvalid = 0;
    #(CLK_PERIOD*4);
    rst_n = 1;

    // Read binary descriptor stream
    max_bytes = 4096;
    fd = $fopen("npu/mapper/examples/minimal_descriptors.bin", "rb");
    if (fd == 0) begin
      $display("ERROR: cannot open descriptor bin file");
      $finish(1);
    end
    bytes_read = $fread(bin_data, fd, 0, max_bytes);
    $fclose(fd);
    if (bytes_read <= 0) begin
      $display("ERROR: no bytes read from descriptor bin file");
      $finish(1);
    end

    // MMIO init
    mmio_write(OFF_CQ_BASE_LO, 32'h0000_0000);
    mmio_write(OFF_CQ_BASE_HI, 32'h0000_0010);
    mmio_write(OFF_CQ_SIZE,    32'h0000_1000);
    mmio_write(OFF_IRQ_ENABLE, 32'h0000_0007);

    if (!$value$plusargs("bytes=%d", test_bytes))
      test_bytes = bytes_read;
    expected_dma_bytes = {bin_data[27], bin_data[26], bin_data[25], bin_data[24]};

    // Tail points to end of descriptor stream
    cq_tail = bytes_read[DATA_W-1:0];
    mmio_write(OFF_CQ_TAIL, cq_tail);
    mmio_write(OFF_DOORBELL, 32'h1);

    // DMA request should assert; handshake and complete
    repeat (5) @(posedge clk);
    if (dma_req_valid !== 1'b1) begin
      $display("ERROR: expected dma_req_valid");
      $finish(1);
    end
    if (dma_req_src !== 64'h0000_0030_0000_0000) begin
      $display("ERROR: dma_req_src mismatch %h", dma_req_src);
      $finish(1);
    end
    if (dma_req_dst !== 64'h0000_0030_0010_0000) begin
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

    // Wait for AXI DMA shim to complete the burst
    begin : wait_irq
      integer t;
      for (t = 0; t < 600; t = t + 1) begin
        @(posedge clk);
        mmio_read(OFF_IRQ_STATUS, irq_status);
        if (irq_status[1] === 1'b1)
          disable wait_irq;
      end
    end

    // Wait for head to catch up (one descriptor per cycle)
    begin : wait_loop
      integer i;
      for (i = 0; i < 20; i = i + 1) begin
        mmio_read(OFF_CQ_HEAD, cq_head);
        if (cq_head == cq_tail)
          disable wait_loop;
      end
    end
    if (cq_head !== cq_tail) begin
      $display("ERROR: cq_head %h != cq_tail %h", cq_head, cq_tail);
      $finish(1);
    end

    mmio_read(OFF_IRQ_STATUS, irq_status);
    if (irq_status[0] !== 1'b1) begin
      $display("ERROR: expected CQ_EMPTY IRQ status");
      $finish(1);
    end
    if (irq_status[1] !== 1'b1) begin
      $display("ERROR: expected EVENT IRQ status from DMA (saw_bvalid=%0d)", saw_bvalid);
      $finish(1);
    end

    // Check that 4KB at destination matches source
    for (j = 0; j < test_bytes; j = j + 1) begin
      if (axi_mem.mem[21'h100000 + j] !== axi_mem.mem[21'h000000 + j]) begin
        $display("ERROR: DMA copy mismatch at byte %0d", j);
        $finish(1);
      end
    end

    $display("PASS: RTL shell bring-up complete");
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

  always @(posedge clk) begin
    if (m_axi_bvalid)
      saw_bvalid <= 1'b1;
  end

endmodule
