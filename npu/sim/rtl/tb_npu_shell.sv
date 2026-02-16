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

  function integer sx8(input [7:0] v);
    begin
      if (v[7])
        sx8 = v - 256;
      else
        sx8 = v;
    end
  endfunction

  integer fd;
  integer bytes_read;
  integer max_bytes;
  reg [7:0] bin_data [0:4095];
  integer j;
  reg [DATA_W-1:0] cq_tail;
  reg [DATA_W-1:0] cq_head;
  reg [DATA_W-1:0] irq_status;
  integer test_bytes;
  integer gemm_test_bytes;
  integer gemm_count;
  integer gemm_desc_count;
  integer gemm_desc_offsets [0:127];
  reg [31:0] gemm_desc_tags [0:127];
  reg [63:0] gemm_desc_uids [0:127];
  integer gemm_desc_expected_accum [0:127];
  integer vec_count;
  integer vec_desc_count;
  integer vec_desc_offsets [0:127];
  reg [63:0] vec_desc_expected [0:127];
  reg [1:0] vec_desc_op [0:127];
  reg [31:0] gemm_log_tag;
  integer gemm_log_offset;
  reg [63:0] gemm_log_uid;
  integer gemm_lookup_i;
  integer gemm_done_index;
  integer gemm_accum_slot;
  integer scan_off;
  integer scan_size;
  integer scan_iter;
  reg [7:0] scan_opcode;
  reg [31:0] scan_tag;
  integer gemm_mac_test;
  integer gemm_m;
  integer gemm_n;
  integer gemm_k;
  integer gemm_cycles;
  integer gemm_dot;
  integer gemm_lane;
  integer vec_tmp;
  integer vec_op_sel;
  integer gemm_mac_lanes;
  reg [63:0] vec_expected_vec;
  reg [63:0] sim_cycle;
  reg [1:0] gemm_slot_valid_prev;
  reg [1:0] gemm_slot_done_prev;
  reg vec_done_pulse_prev;
  reg [63:0] gemm_slot_start_cycle0;
  reg [63:0] gemm_slot_start_cycle1;
  reg [63:0] gemm_done_uid;
  reg [DATA_W-1:0] expected_dma_bytes;
  reg [63:0] expected_dma_src;
  reg [63:0] expected_dma_dst;
  reg sram_test;
  reg event_test;
  reg vec_test;
  reg vec_gelu_test;
  string bin_path;
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
    sim_cycle = 0;
    gemm_slot_valid_prev = 2'b00;
    gemm_slot_done_prev = 2'b00;
    gemm_slot_start_cycle0 = 0;
    gemm_slot_start_cycle1 = 0;
    gemm_count = 0;
    gemm_desc_count = 0;
    vec_count = 0;
    vec_desc_count = 0;
    vec_done_pulse_prev = 1'b0;
    gemm_mac_lanes = ($bits(dut.gemm_mac_a_vec0) / 8);
    if (gemm_mac_lanes < 1)
      gemm_mac_lanes = 1;
    #(CLK_PERIOD*4);
    rst_n = 1;

    sram_test = 0;
    if ($value$plusargs("sram_test=%d", sram_test))
      sram_test = (sram_test != 0);
    event_test = 0;
    if ($value$plusargs("event_test=%d", event_test))
      event_test = (event_test != 0);
    vec_test = 0;
    if ($value$plusargs("vec_test=%d", vec_test))
      vec_test = (vec_test != 0);
    vec_gelu_test = 0;
    if ($value$plusargs("vec_gelu_test=%d", vec_gelu_test))
      vec_gelu_test = (vec_gelu_test != 0);
    gemm_mac_test = 0;
    if ($value$plusargs("gemm_mac_test=%d", gemm_mac_test))
      gemm_mac_test = (gemm_mac_test != 0);

    if ($value$plusargs("bin=%s", bin_path)) begin
      // Read binary descriptor stream from override path
      max_bytes = 4096;
      fd = $fopen(bin_path, "rb");
      if (fd == 0) begin
        $display("ERROR: cannot open descriptor bin file %s", bin_path);
        $finish(1);
      end
      bytes_read = $fread(bin_data, fd, 0, max_bytes);
      $fclose(fd);
      if (bytes_read <= 0) begin
        $display("ERROR: no bytes read from descriptor bin file %s", bin_path);
        $finish(1);
      end
    end else if (event_test) begin
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
    end else if (vec_test) begin
      integer idx;
      for (idx = 0; idx < 128; idx = idx + 1)
        bin_data[idx] = 0;

      // Descriptor 0: VEC_OP relu (flags[1:0]=00)
      bin_data[0] = 8'h11;
      bin_data[2] = 8'h01;
      bin_data[8] = 8'hf8;  // -8 -> 0
      bin_data[9] = 8'h01;  // 1
      bin_data[10] = 8'h7f; // 127
      bin_data[11] = 8'h80; // -128 -> 0
      bin_data[12] = 8'h04;
      bin_data[13] = 8'hfb; // -5 -> 0
      bin_data[14] = 8'h00;
      bin_data[15] = 8'h20;

      // Descriptor 1: VEC_OP add (flags[1:0]=01)
      bin_data[32] = 8'h11;
      bin_data[33] = 8'h01;
      bin_data[34] = 8'h01;
      bin_data[40] = 8'h01;
      bin_data[41] = 8'h02;
      bin_data[42] = 8'h03;
      bin_data[43] = 8'h04;
      bin_data[44] = 8'h7f;
      bin_data[45] = 8'h80;
      bin_data[46] = 8'h10;
      bin_data[47] = 8'hf0;
      bin_data[48] = 8'h01;
      bin_data[49] = 8'hfe;
      bin_data[50] = 8'h05;
      bin_data[51] = 8'hfc;
      bin_data[52] = 8'h01;
      bin_data[53] = 8'h01;
      bin_data[54] = 8'hf0;
      bin_data[55] = 8'h10;

      // Descriptor 2: VEC_OP mul (flags[1:0]=10)
      bin_data[64] = 8'h11;
      bin_data[65] = 8'h02;
      bin_data[66] = 8'h01;
      bin_data[72] = 8'h02;
      bin_data[73] = 8'h03;
      bin_data[74] = 8'hfc; // -4
      bin_data[75] = 8'h05;
      bin_data[76] = 8'h10;
      bin_data[77] = 8'hff; // -1
      bin_data[78] = 8'h08;
      bin_data[79] = 8'hf8; // -8
      bin_data[80] = 8'h03;
      bin_data[81] = 8'h02;
      bin_data[82] = 8'h02;
      bin_data[83] = 8'h04;
      bin_data[84] = 8'h04;
      bin_data[85] = 8'h02;
      bin_data[86] = 8'hff; // -1
      bin_data[87] = 8'h02;

      // Descriptor 3: VEC_OP relu/gelu (flags[1:0]=00/11)
      bin_data[96] = 8'h11;
      bin_data[97] = vec_gelu_test ? 8'h03 : 8'h00;
      bin_data[98] = 8'h01;
      bin_data[104] = 8'hf0; // -16 -> 0
      bin_data[105] = 8'h04; // 4 -> 2
      bin_data[106] = 8'h08; // 8 -> 4
      bin_data[107] = 8'h01; // 1 -> 0
      bin_data[108] = 8'h7f; // 127 -> 63
      bin_data[109] = 8'h80; // -128 -> 0
      bin_data[110] = 8'h20; // 32 -> 16
      bin_data[111] = 8'h02; // 2 -> 1

      bytes_read = 128;
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
    expected_dma_src = {bin_data[15], bin_data[14], bin_data[13], bin_data[12],
                        bin_data[11], bin_data[10], bin_data[9], bin_data[8]};
    expected_dma_dst = {bin_data[23], bin_data[22], bin_data[21], bin_data[20],
                        bin_data[19], bin_data[18], bin_data[17], bin_data[16]};
    // Parse descriptor stream so GEMM timing logs can include stable tag/offset IDs.
    gemm_desc_count = 0;
    vec_desc_count = 0;
    scan_off = 0;
    scan_iter = 0;
    while (((scan_off + 32) <= bytes_read) && (scan_iter < 256)) begin
      scan_opcode = bin_data[scan_off];
      scan_size = bin_data[scan_off + 2];
      if (scan_size <= 0)
        scan_size = 1;
      if ((scan_opcode == 8'h10) && (gemm_desc_count < 128)) begin
        scan_tag = {bin_data[scan_off + 7], bin_data[scan_off + 6], bin_data[scan_off + 5], bin_data[scan_off + 4]};
        gemm_desc_tags[gemm_desc_count] = scan_tag;
        gemm_desc_offsets[gemm_desc_count] = scan_off;
        if (scan_size >= 2) begin
          gemm_desc_uids[gemm_desc_count] = {
            bin_data[scan_off + 63], bin_data[scan_off + 62], bin_data[scan_off + 61], bin_data[scan_off + 60],
            bin_data[scan_off + 59], bin_data[scan_off + 58], bin_data[scan_off + 57], bin_data[scan_off + 56]
          };
        end else begin
          gemm_desc_uids[gemm_desc_count] = 64'hFFFF_FFFF_FFFF_FFFF;
        end
        gemm_dot = 0;
        for (gemm_lane = 0; gemm_lane < gemm_mac_lanes; gemm_lane = gemm_lane + 1) begin
          gemm_dot = gemm_dot + (sx8(bin_data[scan_off + 8 + gemm_lane]) * sx8(bin_data[scan_off + 16 + gemm_lane]));
        end
        if (scan_size >= 2) begin
          gemm_m = {bin_data[scan_off + 35], bin_data[scan_off + 34], bin_data[scan_off + 33], bin_data[scan_off + 32]};
          gemm_n = {bin_data[scan_off + 39], bin_data[scan_off + 38], bin_data[scan_off + 37], bin_data[scan_off + 36]};
          gemm_k = {bin_data[scan_off + 43], bin_data[scan_off + 42], bin_data[scan_off + 41], bin_data[scan_off + 40]};
        end else begin
          gemm_m = scan_tag[31:20];
          gemm_n = scan_tag[19:10];
          gemm_k = scan_tag[9:0];
        end
        if ((gemm_m == 0) || (gemm_n == 0) || (gemm_k == 0))
          gemm_cycles = 1;
        else
          gemm_cycles = ((gemm_m * gemm_n * gemm_k) >> 10) + 1;
        if ((scan_size >= 2) && gemm_desc_uids[gemm_desc_count][63])
          gemm_cycles = gemm_cycles + 8;
        gemm_desc_expected_accum[gemm_desc_count] = gemm_dot * gemm_cycles;
        gemm_desc_count = gemm_desc_count + 1;
      end else if ((scan_opcode == 8'h11) && (vec_desc_count < 128)) begin
        vec_op_sel = bin_data[scan_off + 1] & 8'h3;
        vec_expected_vec = 64'h0;
        for (gemm_lane = 0; gemm_lane < gemm_mac_lanes; gemm_lane = gemm_lane + 1) begin
          if (vec_op_sel == 1) begin
            vec_tmp = sx8(bin_data[scan_off + 8 + gemm_lane]) + sx8(bin_data[scan_off + 16 + gemm_lane]);
          end else if (vec_op_sel == 2) begin
            vec_tmp = sx8(bin_data[scan_off + 8 + gemm_lane]) * sx8(bin_data[scan_off + 16 + gemm_lane]);
          end else if (vec_op_sel == 3) begin
            vec_tmp = sx8(bin_data[scan_off + 8 + gemm_lane]);
            if (vec_tmp < 0)
              vec_tmp = 0;
            else
              vec_tmp = vec_tmp >>> 1;
          end else begin
            vec_tmp = sx8(bin_data[scan_off + 8 + gemm_lane]);
            if (vec_tmp < 0)
              vec_tmp = 0;
          end
          vec_expected_vec[(gemm_lane * 8) +: 8] = vec_tmp & 8'hff;
        end
        vec_desc_offsets[vec_desc_count] = scan_off;
        vec_desc_expected[vec_desc_count] = vec_expected_vec;
        vec_desc_op[vec_desc_count] = vec_op_sel[1:0];
        vec_desc_count = vec_desc_count + 1;
      end
      scan_off = scan_off + (scan_size * 32);
      scan_iter = scan_iter + 1;
    end

    // Tail points to end of descriptor stream
    cq_tail = bytes_read[DATA_W-1:0];
    mmio_write(OFF_CQ_TAIL, cq_tail);
    mmio_write(OFF_DOORBELL, 32'h1);

    // DMA request should assert; handshake and complete
    if (!event_test && !vec_test) begin
      repeat (5) @(posedge clk);
      if (dma_req_valid !== 1'b1) begin
        $display("ERROR: expected dma_req_valid");
        $finish(1);
      end
      if (!sram_test) begin
        if (dma_req_src !== expected_dma_src) begin
          $display("ERROR: dma_req_src mismatch %h", dma_req_src);
          $finish(1);
        end
        if (dma_req_dst !== expected_dma_dst) begin
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

    if (event_test || vec_test) begin
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
      gemm_test_bytes = 0;
      if ($value$plusargs("gemm_mem_test=%d", gemm_test_bytes)) begin
        // GEMM stub path: C should match A for test_bytes
        for (j = 0; j < gemm_test_bytes; j = j + 1) begin
          if (axi_mem.mem[21'h3000 + j] !== axi_mem.mem[21'h1000 + j]) begin
            $display("ERROR: GEMM mem copy mismatch at byte %0d", j);
            $finish(1);
          end
        end
      end
    end

    // With multi-inflight GEMM, IRQ/CQ may complete before GEMM compute finishes.
    // Wait for all GEMM descriptors to emit completion timing lines.
    if (gemm_desc_count > 0) begin : wait_gemm_done
      integer w;
      for (w = 0; w < 2000; w = w + 1) begin
        @(negedge clk);
        if (gemm_count >= gemm_desc_count)
          disable wait_gemm_done;
      end
      if (gemm_count < gemm_desc_count) begin
        $display("ERROR: GEMM completion timeout count=%0d expected=%0d", gemm_count, gemm_desc_count);
        $finish(1);
      end
    end

    if (vec_desc_count > 0) begin : wait_vec_done
      integer vw;
      for (vw = 0; vw < 2000; vw = vw + 1) begin
        @(negedge clk);
        if (vec_count >= vec_desc_count)
          disable wait_vec_done;
      end
      if (vec_count < vec_desc_count) begin
        $display("ERROR: VEC completion timeout count=%0d expected=%0d", vec_count, vec_desc_count);
        $finish(1);
      end
    end

    // Allow negedge monitor to emit final completion line before finish.
    @(negedge clk);
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
    sim_cycle <= sim_cycle + 1;
    if (m_axi_bvalid)
      saw_bvalid <= 1'b1;
  end

  // Sample on negedge so DUT's non-blocking assignments from posedge are visible.
  always @(negedge clk) begin
    if (!rst_n) begin
      gemm_slot_valid_prev <= 2'b00;
      gemm_slot_done_prev <= 2'b00;
      gemm_slot_start_cycle0 <= 0;
      gemm_slot_start_cycle1 <= 0;
      gemm_count <= 0;
      vec_count <= 0;
      vec_done_pulse_prev <= 1'b0;
    end else begin
      if (!gemm_slot_valid_prev[0] && dut.gemm_slot_valid[0]) begin
        gemm_slot_start_cycle0 <= sim_cycle;
      end
      if (!gemm_slot_valid_prev[1] && dut.gemm_slot_valid[1]) begin
        gemm_slot_start_cycle1 <= sim_cycle;
      end
      if (!gemm_slot_done_prev[0] && dut.gemm_slot_done[0]) begin
        gemm_done_uid = dut.gemm_slot_uid0;
        gemm_log_tag = 32'hFFFF_FFFF;
        gemm_log_offset = -1;
        gemm_log_uid = 64'hFFFF_FFFF_FFFF_FFFF;
        if (gemm_done_uid != 64'hFFFF_FFFF_FFFF_FFFF) begin
          for (gemm_lookup_i = 0; gemm_lookup_i < gemm_desc_count; gemm_lookup_i = gemm_lookup_i + 1) begin
            if (gemm_desc_uids[gemm_lookup_i] == gemm_done_uid) begin
              gemm_log_uid = gemm_desc_uids[gemm_lookup_i];
              gemm_log_tag = gemm_desc_tags[gemm_lookup_i];
              gemm_log_offset = gemm_desc_offsets[gemm_lookup_i];
            end
          end
        end
        if ((gemm_log_offset < 0) && (gemm_count < gemm_desc_count)) begin
          gemm_log_uid = gemm_desc_uids[gemm_count];
          gemm_log_tag = gemm_desc_tags[gemm_count];
          gemm_log_offset = gemm_desc_offsets[gemm_count];
        end
        if (gemm_mac_test) begin
          gemm_done_index = -1;
          for (gemm_lookup_i = 0; gemm_lookup_i < gemm_desc_count; gemm_lookup_i = gemm_lookup_i + 1) begin
            if (gemm_desc_offsets[gemm_lookup_i] == gemm_log_offset)
              gemm_done_index = gemm_lookup_i;
          end
          if (gemm_done_index >= 0) begin
            gemm_accum_slot = dut.gemm_slot_accum0;
            if (gemm_accum_slot != gemm_desc_expected_accum[gemm_done_index]) begin
              $display("ERROR: GEMM MAC mismatch slot0 offset=%0d got=%0d exp=%0d",
                       gemm_log_offset, gemm_accum_slot, gemm_desc_expected_accum[gemm_done_index]);
              $finish(1);
            end
          end
        end
        gemm_count = gemm_count + 1;
        $display("GEMM_TIMING index=%0d op_uid=0x%016h tag=0x%08h offset=%0d start_cycle=%0d end_cycle=%0d cycles=%0d",
                 gemm_count, gemm_log_uid, gemm_log_tag, gemm_log_offset,
                 gemm_slot_start_cycle0, sim_cycle, (sim_cycle - gemm_slot_start_cycle0));
      end
      if (!gemm_slot_done_prev[1] && dut.gemm_slot_done[1]) begin
        gemm_done_uid = dut.gemm_slot_uid1;
        gemm_log_tag = 32'hFFFF_FFFF;
        gemm_log_offset = -1;
        gemm_log_uid = 64'hFFFF_FFFF_FFFF_FFFF;
        if (gemm_done_uid != 64'hFFFF_FFFF_FFFF_FFFF) begin
          for (gemm_lookup_i = 0; gemm_lookup_i < gemm_desc_count; gemm_lookup_i = gemm_lookup_i + 1) begin
            if (gemm_desc_uids[gemm_lookup_i] == gemm_done_uid) begin
              gemm_log_uid = gemm_desc_uids[gemm_lookup_i];
              gemm_log_tag = gemm_desc_tags[gemm_lookup_i];
              gemm_log_offset = gemm_desc_offsets[gemm_lookup_i];
            end
          end
        end
        if ((gemm_log_offset < 0) && (gemm_count < gemm_desc_count)) begin
          gemm_log_uid = gemm_desc_uids[gemm_count];
          gemm_log_tag = gemm_desc_tags[gemm_count];
          gemm_log_offset = gemm_desc_offsets[gemm_count];
        end
        if (gemm_mac_test) begin
          gemm_done_index = -1;
          for (gemm_lookup_i = 0; gemm_lookup_i < gemm_desc_count; gemm_lookup_i = gemm_lookup_i + 1) begin
            if (gemm_desc_offsets[gemm_lookup_i] == gemm_log_offset)
              gemm_done_index = gemm_lookup_i;
          end
          if (gemm_done_index >= 0) begin
            gemm_accum_slot = dut.gemm_slot_accum1;
            if (gemm_accum_slot != gemm_desc_expected_accum[gemm_done_index]) begin
              $display("ERROR: GEMM MAC mismatch slot1 offset=%0d got=%0d exp=%0d",
                       gemm_log_offset, gemm_accum_slot, gemm_desc_expected_accum[gemm_done_index]);
              $finish(1);
            end
          end
        end
        gemm_count = gemm_count + 1;
        $display("GEMM_TIMING index=%0d op_uid=0x%016h tag=0x%08h offset=%0d start_cycle=%0d end_cycle=%0d cycles=%0d",
                 gemm_count, gemm_log_uid, gemm_log_tag, gemm_log_offset,
                 gemm_slot_start_cycle1, sim_cycle, (sim_cycle - gemm_slot_start_cycle1));
      end
      if (!vec_done_pulse_prev && dut.vec_done_pulse) begin
        if (vec_count >= vec_desc_count) begin
          $display("ERROR: unexpected VEC completion vec_count=%0d vec_desc_count=%0d", vec_count, vec_desc_count);
          $finish(1);
        end
        for (gemm_lane = 0; gemm_lane < gemm_mac_lanes; gemm_lane = gemm_lane + 1) begin
          if (dut.vec_last_result[(gemm_lane*8) +: 8] !== vec_desc_expected[vec_count][(gemm_lane*8) +: 8]) begin
            $display("ERROR: VEC mismatch index=%0d lane=%0d got=0x%02h exp=0x%02h",
                     vec_count, gemm_lane,
                     dut.vec_last_result[(gemm_lane*8) +: 8],
                     vec_desc_expected[vec_count][(gemm_lane*8) +: 8]);
            $finish(1);
          end
        end
        vec_count = vec_count + 1;
        $display("VEC_DONE index=%0d offset=%0d op=%0d",
                 vec_count, vec_desc_offsets[vec_count-1], vec_desc_op[vec_count-1]);
      end
      gemm_slot_valid_prev <= dut.gemm_slot_valid;
      gemm_slot_done_prev <= dut.gemm_slot_done;
      vec_done_pulse_prev <= dut.vec_done_pulse;
    end
  end

endmodule
