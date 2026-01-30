`timescale 1ns/1ps

module tb_npu_shell;
  localparam CLK_PERIOD = 10;
  localparam MMIO_ADDR_W = 12;
  localparam DATA_W = 32;

  `include "npu/rtlgen/out/mmio_map.vh"

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
  reg sram_test;
  reg event_test;
  `include "npu/rtlgen/out/sram_map.vh"
  localparam [63:0] MEM_DST_BASE = 64'h0000_0000_0001_0000;

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

    sram_test = 0;
    if ($value$plusargs("sram_test=%d", sram_test))
      sram_test = (sram_test != 0);
    event_test = 0;
    if ($value$plusargs("event_test=%d", event_test))
      event_test = (event_test != 0);

    if (event_test) begin
      integer idx;
      for (idx = 0; idx < 96; idx = idx + 1)
        bin_data[idx] = 0;

      // Descriptor 0: GEMM
      bin_data[0] = 8'h10;
      bin_data[2] = 8'h01;
      // Descriptor 1: EVENT_SIGNAL
      bin_data[32] = 8'h20;
      bin_data[34] = 8'h01;
      // Descriptor 2: EVENT_WAIT
      bin_data[64] = 8'h21;
      bin_data[66] = 8'h01;

      bytes_read = 96;
    end else if (sram_test) begin
      // Build two DMA_COPY descriptors: mem->SRAM, SRAM->mem
      integer idx;
      for (idx = 0; idx < 64; idx = idx + 1)
        bin_data[idx] = 0;

      // Descriptor 0
      bin_data[0] = 8'h01; // DMA_COPY
      bin_data[2] = 8'h01; // size in 32B units
      // SRC = 0x0
      // DST = SRAM_BASE0
      {bin_data[23], bin_data[22], bin_data[21], bin_data[20],
       bin_data[19], bin_data[18], bin_data[17], bin_data[16]} = SRAM_BASE0;
      // SIZE = 256 bytes
      {bin_data[27], bin_data[26], bin_data[25], bin_data[24]} = 32'd256;

      // Descriptor 1
      bin_data[32] = 8'h01; // DMA_COPY
      bin_data[34] = 8'h01;
      // SRC = SRAM_BASE0 (bytes 40..47)
      {bin_data[47], bin_data[46], bin_data[45], bin_data[44],
       bin_data[43], bin_data[42], bin_data[41], bin_data[40]} = SRAM_BASE0;
      // DST = MEM_DST_BASE (bytes 48..55)
      {bin_data[55], bin_data[54], bin_data[53], bin_data[52],
       bin_data[51], bin_data[50], bin_data[49], bin_data[48]} = MEM_DST_BASE;
      // SIZE = 256 bytes (bytes 56..59)
      {bin_data[59], bin_data[58], bin_data[57], bin_data[56]} = 32'd256;

      bytes_read = 64;
    end else begin
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
    if (!event_test) begin
      repeat (5) @(posedge clk);
      if (dma_req_valid !== 1'b1) begin
        $display("ERROR: expected dma_req_valid");
        $finish(1);
      end
      if (!sram_test) begin
        if (dma_req_src !== 64'h0000_0030_0000_0000) begin
          $display("ERROR: dma_req_src mismatch %h", dma_req_src);
          $finish(1);
        end
        if (dma_req_dst !== 64'h0000_0030_0010_0000) begin
          $display("ERROR: dma_req_dst mismatch %h", dma_req_dst);
          $finish(1);
        end
      end
      if (dma_req_bytes !== expected_dma_bytes) begin
        $display("ERROR: dma_req_bytes mismatch %h", dma_req_bytes);
        $finish(1);
      end
      dma_req_ready = 1'b1;
      @(posedge clk);
      dma_req_ready = 1'b0;
    end

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
      $display("ERROR: expected EVENT IRQ status from DMA/event (saw_bvalid=%0d)", saw_bvalid);
      $finish(1);
    end

    if (event_test) begin
      // No data check for GEMM/event stubs
    end else if (sram_test) begin
      // Check SRAM->mem copy result at MEM_DST_BASE
      for (j = 0; j < 256; j = j + 1) begin
        if (axi_mem.mem[MEM_DST_BASE[20:0] + j] !== axi_mem.mem[21'h000000 + j]) begin
          $display("ERROR: SRAM DMA copy mismatch at byte %0d", j);
          $finish(1);
        end
      end
    end else begin
      // Check that 4KB at destination matches source
      for (j = 0; j < test_bytes; j = j + 1) begin
        if (axi_mem.mem[21'h100000 + j] !== axi_mem.mem[21'h000000 + j]) begin
          $display("ERROR: DMA copy mismatch at byte %0d", j);
          $finish(1);
        end
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

  always @(posedge clk) begin
    if (m_axi_bvalid)
      saw_bvalid <= 1'b1;
  end

endmodule
