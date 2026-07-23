`timescale 1ns/1ps

module tb_noc_value_matrix_reassembler;
  parameter integer PACKET_W = 128;
  localparam integer CLK_PERIOD = 10;
  localparam integer VALUE_W = 512;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 12;
  localparam integer VALUE_SLICE_W = 4;
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;
  localparam integer FRAG_IDX_W = (FRAGMENTS <= 1) ? 1 : $clog2(FRAGMENTS);

  reg clk;
  reg rst_n;
  reg seg_valid;
  wire seg_ready;
  reg [SOURCE_W-1:0] seg_source;
  reg [TAG_W-1:0] seg_tag;
  reg [ADDR_W-1:0] seg_addr;
  reg [VALUE_SLICE_W-1:0] seg_value_slice;
  reg [FRAG_IDX_W-1:0] seg_fragment_idx;
  reg seg_last;
  reg [PACKET_W-1:0] seg_data;
  wire wide_valid;
  reg wide_ready;
  wire [SOURCE_W-1:0] wide_source;
  wire [TAG_W-1:0] wide_tag;
  wire [ADDR_W-1:0] wide_addr;
  wire [VALUE_SLICE_W-1:0] wide_value_slice;
  wire [VALUE_W-1:0] wide_matrix;
  wire protocol_error;

  reg [VALUE_W-1:0] expected_matrix;
  integer frag_i;

  noc_value_matrix_reassembler #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .seg_valid(seg_valid),
    .seg_ready(seg_ready),
    .seg_source(seg_source),
    .seg_tag(seg_tag),
    .seg_addr(seg_addr),
    .seg_value_slice(seg_value_slice),
    .seg_fragment_idx(seg_fragment_idx),
    .seg_last(seg_last),
    .seg_data(seg_data),
    .wide_valid(wide_valid),
    .wide_ready(wide_ready),
    .wide_source(wide_source),
    .wide_tag(wide_tag),
    .wide_addr(wide_addr),
    .wide_value_slice(wide_value_slice),
    .wide_matrix(wide_matrix),
    .protocol_error(protocol_error)
  );

  initial clk = 1'b0;
  always #(CLK_PERIOD/2) clk = ~clk;

  function [VALUE_W-1:0] build_matrix;
    input [15:0] matrix_id;
    integer wi;
    reg [63:0] word_value;
    begin
      build_matrix = {VALUE_W{1'b0}};
      for (wi = 0; wi < (VALUE_W / 64); wi = wi + 1) begin
        word_value = {matrix_id, wi[15:0], matrix_id + wi[15:0], 16'h5000 + wi[15:0]};
        build_matrix[(wi * 64) +: 64] = word_value;
      end
    end
  endfunction

  task automatic reset_dut;
    begin
      rst_n = 1'b0;
      seg_valid = 1'b0;
      seg_source = {SOURCE_W{1'b0}};
      seg_tag = {TAG_W{1'b0}};
      seg_addr = {ADDR_W{1'b0}};
      seg_value_slice = {VALUE_SLICE_W{1'b0}};
      seg_fragment_idx = {FRAG_IDX_W{1'b0}};
      seg_last = 1'b0;
      seg_data = {PACKET_W{1'b0}};
      repeat (3) @(posedge clk);
      rst_n = 1'b1;
      @(posedge clk);
    end
  endtask

  task automatic send_segment;
    input [SOURCE_W-1:0] source;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    input [FRAG_IDX_W-1:0] fragment_idx;
    input last;
    input [PACKET_W-1:0] data;
    begin
      @(negedge clk);
      seg_source = source;
      seg_tag = tag;
      seg_addr = addr;
      seg_value_slice = value_slice;
      seg_fragment_idx = fragment_idx;
      seg_last = last;
      seg_data = data;
      seg_valid = 1'b1;
      while (!seg_ready) begin
        @(posedge clk);
        @(negedge clk);
      end
      @(posedge clk);
      @(negedge clk);
      seg_valid = 1'b0;
    end
  endtask

  initial begin
    wide_ready = 1'b1;
    expected_matrix = build_matrix(16'h3456);
    reset_dut();

    for (frag_i = 0; frag_i < FRAGMENTS; frag_i = frag_i + 1) begin
      send_segment(2'd1, 8'h44, 12'h055, 4'h3, frag_i[FRAG_IDX_W-1:0],
                   (frag_i == (FRAGMENTS - 1)),
                   expected_matrix[(frag_i * PACKET_W) +: PACKET_W]);
    end
    wait (wide_valid);
    @(posedge clk);
    if (protocol_error !== 1'b0 ||
        wide_source !== 2'd1 ||
        wide_tag !== 8'h44 ||
        wide_addr !== 12'h055 ||
        wide_value_slice !== 4'h3 ||
        wide_matrix !== expected_matrix) begin
      $display("ERROR: valid reassembly failed");
      $finish(1);
    end

    reset_dut();
    send_segment(2'd2, 8'h66, 12'h077, 4'h5, {{(FRAG_IDX_W-1){1'b0}}, 1'b1}, 1'b0,
                 {PACKET_W{1'b1}});
    @(posedge clk);
    if (protocol_error !== 1'b1) begin
      $display("ERROR: expected protocol_error on out-of-order fragment");
      $finish(1);
    end

    reset_dut();
    send_segment(2'd0, 8'h80, 12'h088, 4'h6, {FRAG_IDX_W{1'b0}}, 1'b0, {PACKET_W{1'b0}});
    send_segment(2'd0, 8'h81, 12'h088, 4'h6, {{(FRAG_IDX_W-1){1'b0}}, 1'b1},
                 (FRAGMENTS == 2),
                 {PACKET_W{1'b1}});
    @(posedge clk);
    if (protocol_error !== 1'b1) begin
      $display("ERROR: expected protocol_error on metadata mismatch");
      $finish(1);
    end

    $display("PASS: tb_noc_value_matrix_reassembler packet_w=%0d", PACKET_W);
    $finish(0);
  end

  initial begin
    repeat (400) @(posedge clk);
    $display("ERROR: tb_noc_value_matrix_reassembler timeout");
    $finish(1);
  end
endmodule
