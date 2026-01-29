`timescale 1ns/1ps

module axi_mem_router (
  input  wire        clk,
  input  wire        rst_n,
  input  wire        m_axi_awvalid,
  output reg         m_axi_awready,
  input  wire [63:0] m_axi_awaddr,
  input  wire [7:0]  m_axi_awlen,
  input  wire [2:0]  m_axi_awsize,
  input  wire        m_axi_wvalid,
  output reg         m_axi_wready,
  input  wire [255:0] m_axi_wdata,
  input  wire [31:0] m_axi_wstrb,
  input  wire        m_axi_wlast,
  output reg         m_axi_bvalid,
  input  wire        m_axi_bready,
  input  wire        m_axi_arvalid,
  output reg         m_axi_arready,
  input  wire [63:0] m_axi_araddr,
  input  wire [7:0]  m_axi_arlen,
  input  wire [2:0]  m_axi_arsize,
  output reg         m_axi_rvalid,
  input  wire        m_axi_rready,
  output reg [255:0] m_axi_rdata,
  output reg         m_axi_rlast
);
  `include "npu/rtlgen/out/sram_map.vh"

  reg [7:0] mem [0:2097151];
  reg [63:0] aw_addr_q;
  reg [63:0] ar_addr_q;
  reg [8:0] aw_beats_left;
  reg [8:0] ar_beats_left;
  reg [63:0] ar_addr_inc;
  reg        aw_is_sram;
  reg        ar_is_sram;
  integer    k;

  integer j;
  initial begin
    for (j = 0; j < 2097152; j = j + 1) begin
      mem[j] = j[7:0];
    end
  end

  reg [7:0] aw_sram_sel;
  reg [7:0] ar_sram_sel;
  reg       sram_read_issue;
  reg       sram_read_wait;
  reg [63:0] sram_read_addr;
  reg [8:0]  sram_read_beats;

  localparam int SRAM_COUNT_SAFE = (SRAM_COUNT > 0) ? SRAM_COUNT : 1;
  wire [255:0] sram_rdata [0:SRAM_MAX-1];

  genvar gi;
  generate
    if (SRAM_COUNT > 0) begin : gen_sram
      for (gi = 0; gi < SRAM_MAX; gi = gi + 1) begin : gen_sram_inst
        if (gi < SRAM_COUNT) begin : gen_sram_active
          localparam int DEPTH = (sram_size(gi[7:0]) > 0) ? (sram_size(gi[7:0]) / sram_word_bytes(gi[7:0])) : 1;
          localparam int ADDR_W = (DEPTH > 1) ? $clog2(DEPTH) : 1;
          localparam int WORD_SHIFT = (sram_word_bytes(gi[7:0]) > 1) ? $clog2(sram_word_bytes(gi[7:0])) : 0;
          wire we_sel = aw_is_sram && (aw_sram_sel == gi[7:0]) && m_axi_wvalid && m_axi_wready;
          wire re_sel = sram_read_issue && ar_is_sram && (ar_sram_sel == gi[7:0]);
          wire [ADDR_W-1:0] waddr = (aw_addr_q - sram_base(gi[7:0])) >> WORD_SHIFT;
          wire [ADDR_W-1:0] raddr = (sram_read_addr - sram_base(gi[7:0])) >> WORD_SHIFT;

          sram_1r1w #(
            .ADDR_WIDTH(ADDR_W),
            .DATA_WIDTH(sram_word_bytes(gi[7:0]) * 8),
            .READ_LATENCY(1),
            .BYTE_ENABLE(1)
          ) u_sram (
            .clk(clk),
            .we(we_sel),
            .waddr(waddr),
            .wdata(m_axi_wdata),
            .wstrb(m_axi_wstrb),
            .re(re_sel),
            .raddr(raddr),
            .rdata(sram_rdata[gi])
          );
        end else begin : gen_sram_inactive
          assign sram_rdata[gi] = 0;
        end
      end
    end
  endgenerate

  function automatic [8:0] find_sram_sel(input [63:0] addr);
    integer idx;
    reg hit;
    reg [7:0] sel;
    begin
      hit = 1'b0;
      sel = 0;
      for (idx = 0; idx < SRAM_COUNT; idx = idx + 1) begin
        if (!hit && addr >= sram_base(idx[7:0]) && addr < (sram_base(idx[7:0]) + sram_size(idx[7:0]))) begin
          hit = 1'b1;
          sel = idx[7:0];
        end
      end
      find_sram_sel = {hit, sel};
    end
  endfunction

  function automatic [63:0] sram_base(input [7:0] idx);
    begin
      case (idx)
        0: sram_base = SRAM_BASE0;
        1: sram_base = SRAM_BASE1;
        2: sram_base = SRAM_BASE2;
        3: sram_base = SRAM_BASE3;
        4: sram_base = SRAM_BASE4;
        5: sram_base = SRAM_BASE5;
        6: sram_base = SRAM_BASE6;
        7: sram_base = SRAM_BASE7;
        default: sram_base = 0;
      endcase
    end
  endfunction

  function automatic [63:0] sram_size(input [7:0] idx);
    begin
      case (idx)
        0: sram_size = SRAM_SIZE0;
        1: sram_size = SRAM_SIZE1;
        2: sram_size = SRAM_SIZE2;
        3: sram_size = SRAM_SIZE3;
        4: sram_size = SRAM_SIZE4;
        5: sram_size = SRAM_SIZE5;
        6: sram_size = SRAM_SIZE6;
        7: sram_size = SRAM_SIZE7;
        default: sram_size = 0;
      endcase
    end
  endfunction

  function automatic integer sram_align(input [7:0] idx);
    begin
      case (idx)
        0: sram_align = SRAM_ALIGN0;
        1: sram_align = SRAM_ALIGN1;
        2: sram_align = SRAM_ALIGN2;
        3: sram_align = SRAM_ALIGN3;
        4: sram_align = SRAM_ALIGN4;
        5: sram_align = SRAM_ALIGN5;
        6: sram_align = SRAM_ALIGN6;
        7: sram_align = SRAM_ALIGN7;
        default: sram_align = 0;
      endcase
    end
  endfunction

  function automatic integer sram_word_bytes(input [7:0] idx);
    begin
      case (idx)
        0: sram_word_bytes = SRAM_WORD_BYTES0;
        1: sram_word_bytes = SRAM_WORD_BYTES1;
        2: sram_word_bytes = SRAM_WORD_BYTES2;
        3: sram_word_bytes = SRAM_WORD_BYTES3;
        4: sram_word_bytes = SRAM_WORD_BYTES4;
        5: sram_word_bytes = SRAM_WORD_BYTES5;
        6: sram_word_bytes = SRAM_WORD_BYTES6;
        7: sram_word_bytes = SRAM_WORD_BYTES7;
        default: sram_word_bytes = 0;
      endcase
    end
  endfunction

  function automatic [255:0] mux_sram_rdata(input [7:0] sel);
    integer idx;
    begin
      mux_sram_rdata = 0;
      for (idx = 0; idx < SRAM_COUNT; idx = idx + 1) begin
        if (sel == idx[7:0])
          mux_sram_rdata = sram_rdata[idx];
      end
    end
  endfunction

  task automatic check_alignment(input [63:0] addr, input [7:0] sel);
    integer align;
    begin
      align = sram_align(sel);
      if (align > 0 && (addr % align) != 0) begin
        $display("WARN: SRAM access misaligned addr=%h align=%0d", addr, align);
      end
    end
  endtask

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m_axi_awready <= 1'b1;
      m_axi_wready <= 1'b1;
      m_axi_arready <= 1'b1;
      m_axi_bvalid <= 1'b0;
      m_axi_rvalid <= 1'b0;
      m_axi_rdata <= 0;
      m_axi_rlast <= 1'b0;
      aw_addr_q <= 0;
      ar_addr_q <= 0;
      aw_beats_left <= 0;
      ar_beats_left <= 0;
      aw_is_sram <= 1'b0;
      ar_is_sram <= 1'b0;
      aw_sram_sel <= 0;
      ar_sram_sel <= 0;
      sram_read_issue <= 1'b0;
      sram_read_wait <= 1'b0;
      sram_read_addr <= 0;
      sram_read_beats <= 0;
    end else begin
      if (m_axi_awvalid && m_axi_awready) begin
        reg [8:0] aw_match;
        aw_match = find_sram_sel(m_axi_awaddr);
        aw_sram_sel <= aw_match[7:0];
        aw_is_sram <= aw_match[8];
        if (aw_match[8])
          check_alignment(m_axi_awaddr, aw_sram_sel);
        aw_addr_q <= m_axi_awaddr;
        aw_beats_left <= m_axi_awlen + 1;
      end

      if (m_axi_wvalid && m_axi_wready) begin
        if (aw_is_sram) begin
          aw_addr_q <= aw_addr_q + (1 << m_axi_awsize);
          if (aw_beats_left != 0)
            aw_beats_left <= aw_beats_left - 1;
          if (m_axi_wlast) begin
            m_axi_bvalid <= 1'b1;
          end
        end else begin
          for (k = 0; k < 32; k = k + 1) begin
            if (m_axi_wstrb[k]) begin
              mem[aw_addr_q[20:0] + k] <= m_axi_wdata[(k*8)+:8];
            end
          end
          aw_addr_q <= aw_addr_q + 32;
          if (aw_beats_left != 0)
            aw_beats_left <= aw_beats_left - 1;
          if (m_axi_wlast) begin
            m_axi_bvalid <= 1'b1;
          end
        end
      end

      if (m_axi_bvalid && m_axi_bready) begin
        m_axi_bvalid <= 1'b0;
      end

      if (m_axi_arvalid && m_axi_arready) begin
        reg [8:0] ar_match;
        ar_match = find_sram_sel(m_axi_araddr);
        ar_sram_sel <= ar_match[7:0];
        ar_is_sram <= ar_match[8];
        if (ar_match[8])
          check_alignment(m_axi_araddr, ar_sram_sel);
        ar_addr_q <= m_axi_araddr;
        ar_beats_left <= m_axi_arlen + 1;
        if (ar_match[8]) begin
          sram_read_addr <= m_axi_araddr;
          sram_read_beats <= m_axi_arlen + 1;
          sram_read_issue <= 1'b1;
          sram_read_wait <= 1'b0;
        end else begin
          m_axi_rvalid <= 1'b1;
          m_axi_rlast <= (m_axi_arlen == 0);
          for (k = 0; k < 32; k = k + 1) begin
            m_axi_rdata[(k*8)+:8] <= mem[m_axi_araddr[20:0] + k];
          end
        end
      end

      if (ar_is_sram) begin
        if (sram_read_issue) begin
          sram_read_issue <= 1'b0;
          sram_read_wait <= 1'b1;
        end else if (sram_read_wait && !m_axi_rvalid) begin
          m_axi_rvalid <= 1'b1;
          m_axi_rdata <= mux_sram_rdata(ar_sram_sel);
          m_axi_rlast <= (sram_read_beats == 1);
          sram_read_wait <= 1'b0;
        end

        if (m_axi_rvalid && m_axi_rready) begin
          m_axi_rvalid <= 1'b0;
          m_axi_rlast <= 1'b0;
          if (sram_read_beats > 1) begin
            sram_read_beats <= sram_read_beats - 1;
            sram_read_addr <= sram_read_addr + (1 << m_axi_arsize);
            sram_read_issue <= 1'b1;
          end else begin
            sram_read_beats <= 0;
          end
        end
      end else begin
        if (m_axi_rvalid && m_axi_rready) begin
          if (ar_beats_left > 1) begin
            ar_addr_inc = ar_addr_q + 32;
            ar_addr_q <= ar_addr_inc;
            ar_beats_left <= ar_beats_left - 1;
            m_axi_rlast <= (ar_beats_left == 2);
            for (k = 0; k < 32; k = k + 1) begin
              m_axi_rdata[(k*8)+:8] <= mem[ar_addr_inc[20:0] + k];
            end
          end else begin
            m_axi_rvalid <= 1'b0;
            m_axi_rlast <= 1'b0;
            ar_beats_left <= 0;
          end
        end
      end
    end
  end

endmodule
