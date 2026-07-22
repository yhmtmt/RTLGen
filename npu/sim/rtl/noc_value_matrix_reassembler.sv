`timescale 1ns/1ps

// Reassembles segmented 512-bit matrix responses back into a single wide
// ready/valid response at a source endpoint.
module noc_value_matrix_reassembler #(
  parameter integer PACKET_W = 128,
  parameter integer VALUE_W = 512,
  parameter integer FRAG_IDX_W = ((VALUE_W / PACKET_W) <= 1) ? 1 : $clog2(VALUE_W / PACKET_W),
  parameter integer SOURCE_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 12,
  parameter integer VALUE_SLICE_W = 4
) (
  input wire clk,
  input wire rst_n,

  input wire seg_valid,
  output wire seg_ready,
  input wire [SOURCE_W-1:0] seg_source,
  input wire [TAG_W-1:0] seg_tag,
  input wire [ADDR_W-1:0] seg_addr,
  input wire [VALUE_SLICE_W-1:0] seg_value_slice,
  input wire [FRAG_IDX_W-1:0] seg_fragment_idx,
  input wire seg_last,
  input wire [PACKET_W-1:0] seg_data,

  output wire wide_valid,
  input wire wide_ready,
  output wire [SOURCE_W-1:0] wide_source,
  output wire [TAG_W-1:0] wide_tag,
  output wire [ADDR_W-1:0] wide_addr,
  output wire [VALUE_SLICE_W-1:0] wide_value_slice,
  output wire [VALUE_W-1:0] wide_matrix
) ;
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;

  reg collecting;
  reg wide_valid_r;
  reg [SOURCE_W-1:0] wide_source_r;
  reg [TAG_W-1:0] wide_tag_r;
  reg [ADDR_W-1:0] wide_addr_r;
  reg [VALUE_SLICE_W-1:0] wide_value_slice_r;
  reg [VALUE_W-1:0] wide_matrix_r;

  wire seg_fire = seg_valid && seg_ready;
  wire wide_fire = wide_valid && wide_ready;

  assign seg_ready = !wide_valid_r;
  assign wide_valid = wide_valid_r;
  assign wide_source = wide_source_r;
  assign wide_tag = wide_tag_r;
  assign wide_addr = wide_addr_r;
  assign wide_value_slice = wide_value_slice_r;
  assign wide_matrix = wide_matrix_r;

  initial begin
    if ((PACKET_W != 128) && (PACKET_W != 256)) begin
      $error("noc_value_matrix_reassembler PACKET_W must be 128 or 256, got %0d", PACKET_W);
      $finish(1);
    end
    if (VALUE_W != 512) begin
      $error("noc_value_matrix_reassembler VALUE_W must be 512, got %0d", VALUE_W);
      $finish(1);
    end
    if ((VALUE_W % PACKET_W) != 0) begin
      $error("noc_value_matrix_reassembler VALUE_W must be an integer multiple of PACKET_W");
      $finish(1);
    end
    if ((1 << FRAG_IDX_W) < FRAGMENTS) begin
      $error("noc_value_matrix_reassembler FRAG_IDX_W is too small for %0d fragments", FRAGMENTS);
      $finish(1);
    end
    if (VALUE_SLICE_W != 4) begin
      $error("noc_value_matrix_reassembler VALUE_SLICE_W must be 4, got %0d", VALUE_SLICE_W);
      $finish(1);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      collecting <= 1'b0;
      wide_valid_r <= 1'b0;
      wide_source_r <= {SOURCE_W{1'b0}};
      wide_tag_r <= {TAG_W{1'b0}};
      wide_addr_r <= {ADDR_W{1'b0}};
      wide_value_slice_r <= {VALUE_SLICE_W{1'b0}};
      wide_matrix_r <= {VALUE_W{1'b0}};
    end else begin
      if (wide_fire) begin
        wide_valid_r <= 1'b0;
      end

      if (seg_fire) begin
        if (!collecting) begin
          wide_source_r <= seg_source;
          wide_tag_r <= seg_tag;
          wide_addr_r <= seg_addr;
          wide_value_slice_r <= seg_value_slice;
          collecting <= !seg_last;
        end
        wide_matrix_r[(seg_fragment_idx * PACKET_W) +: PACKET_W] <= seg_data;
        if (seg_last) begin
          wide_valid_r <= 1'b1;
          collecting <= 1'b0;
        end
      end
    end
  end
endmodule
