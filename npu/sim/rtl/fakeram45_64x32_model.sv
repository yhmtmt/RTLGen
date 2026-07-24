`timescale 1ns/1ps

module fakeram45_64x32 (
  output wire [31:0] rd_out,
  input  wire [5:0]  addr_in,
  input  wire        we_in,
  input  wire [31:0] wd_in,
  input  wire [31:0] w_mask_in,
  input  wire        clk,
  input  wire        ce_in
);
  reg [31:0] mem [0:63];
  reg [5:0] addr_q;
  reg [31:0] rd_out_q;
  integer idx;
  integer bit_i;
  reg [31:0] write_word;

  assign rd_out = rd_out_q;

  initial begin
    addr_q = 6'd0;
    rd_out_q = 32'd0;
    for (idx = 0; idx < 64; idx = idx + 1) begin
      mem[idx] = 32'd0;
    end
  end

  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      write_word = mem[addr_in];
      if (we_in) begin
        for (bit_i = 0; bit_i < 32; bit_i = bit_i + 1) begin
          if (w_mask_in[bit_i]) begin
            write_word[bit_i] = wd_in[bit_i];
          end
        end
        mem[addr_in] <= write_word;
      end
      addr_q <= addr_in;
    end
  end
endmodule
