`timescale 1ns/1ps

module axi_mem_model (
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
  reg [7:0] mem [0:2097151];
  reg [63:0] aw_addr_q;
  reg [63:0] ar_addr_q;
  reg [8:0] aw_beats_left;
  reg [8:0] ar_beats_left;
  reg [63:0] ar_addr_inc;
  integer k;

  integer j;
  initial begin
    for (j = 0; j < 2097152; j = j + 1) begin
      mem[j] = j[7:0];
    end
  end

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
    end else begin
      if (m_axi_awvalid && m_axi_awready) begin
        aw_addr_q <= m_axi_awaddr;
        aw_beats_left <= m_axi_awlen + 1;
      end

      if (m_axi_wvalid && m_axi_wready) begin
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

      if (m_axi_bvalid && m_axi_bready) begin
        m_axi_bvalid <= 1'b0;
      end

      if (m_axi_arvalid && m_axi_arready) begin
        ar_addr_q <= m_axi_araddr;
        ar_beats_left <= m_axi_arlen + 1;
        m_axi_rvalid <= 1'b1;
        m_axi_rlast <= (m_axi_arlen == 0);
        for (k = 0; k < 32; k = k + 1) begin
          m_axi_rdata[(k*8)+:8] <= mem[m_axi_araddr[20:0] + k];
        end
      end

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

endmodule
