`timescale 1ns/1ps

module tb_banked_value_memory_service;
  parameter integer PACKET_W = 128;
  localparam integer CLK_PERIOD = 10;
  localparam integer VALUE_W = 512;
  localparam integer SOURCES = 4;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 12;
  localparam integer VALUE_SLICE_W = 4;
  localparam integer BANKS = 2;
  localparam integer STORE_DEPTH = 8;
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;
  localparam integer FRAG_IDX_W = (FRAGMENTS <= 1) ? 1 : $clog2(FRAGMENTS);

  reg clk;
  reg rst_n;

  reg preload_valid;
  wire preload_ready;
  reg [ADDR_W-1:0] preload_addr;
  reg [VALUE_SLICE_W-1:0] preload_value_slice;
  reg [VALUE_W-1:0] preload_matrix;

  reg [SOURCES-1:0] src_req_valid;
  wire [SOURCES-1:0] src_req_ready;
  reg [SOURCES*TAG_W-1:0] src_req_tag;
  reg [SOURCES*ADDR_W-1:0] src_req_addr;
  reg [SOURCES*VALUE_SLICE_W-1:0] src_req_value_slice;

  wire [SOURCES-1:0] src_resp_valid;
  wire [SOURCES*SOURCE_W-1:0] src_resp_source;
  wire [SOURCES*TAG_W-1:0] src_resp_tag;
  wire [SOURCES*ADDR_W-1:0] src_resp_addr;
  wire [SOURCES*VALUE_SLICE_W-1:0] src_resp_value_slice;
  wire [SOURCES*FRAG_IDX_W-1:0] src_resp_fragment_idx;
  wire [SOURCES-1:0] src_resp_last;
  wire [SOURCES*PACKET_W-1:0] src_resp_data;
  wire [SOURCES-1:0] src_resp_ready;
  wire [SOURCES-1:0] reasm_seg_ready;
  wire [SOURCES-1:0] reasm_protocol_error;

  wire req_valid;
  wire req_ready;
  wire [SOURCE_W-1:0] req_source;
  wire [TAG_W-1:0] req_tag;
  wire [ADDR_W-1:0] req_addr;
  wire [VALUE_SLICE_W-1:0] req_value_slice;
  wire resp_valid;
  wire resp_ready;
  wire [SOURCE_W-1:0] resp_source;
  wire [TAG_W-1:0] resp_tag;
  wire [ADDR_W-1:0] resp_addr;
  wire [VALUE_SLICE_W-1:0] resp_value_slice;
  wire [FRAG_IDX_W-1:0] resp_fragment_idx;
  wire resp_last;
  wire [PACKET_W-1:0] resp_data;

  wire [31:0] router_injection_stall_cycles;
  wire [31:0] router_arbitration_contention_cycles;
  wire [31:0] router_response_block_cycles;
  wire [31:0] router_req_max_occupancy;
  wire [31:0] router_resp_max_occupancy;
  wire [31:0] service_accepted_req_count;
  wire [31:0] service_emitted_resp_count;
  wire [31:0] service_bank_conflict_count;
  wire [31:0] service_response_block_cycles;
  wire [31:0] service_req_max_occupancy;
  wire [31:0] service_resp_max_occupancy;

  wire [SOURCES-1:0] wide_resp_valid;
  reg [SOURCES-1:0] wide_resp_ready;
  reg [SOURCES-1:0] seg_accept_enable;
  wire [SOURCES*SOURCE_W-1:0] wide_resp_source;
  wire [SOURCES*TAG_W-1:0] wide_resp_tag;
  wire [SOURCES*ADDR_W-1:0] wide_resp_addr;
  wire [SOURCES*VALUE_SLICE_W-1:0] wide_resp_value_slice;
  wire [SOURCES*VALUE_W-1:0] wide_resp_matrix;

  reg [VALUE_W-1:0] expected_matrix [0:SOURCES-1];
  reg [TAG_W-1:0] expected_tag [0:SOURCES-1];
  reg [ADDR_W-1:0] expected_addr [0:SOURCES-1];
  reg [VALUE_SLICE_W-1:0] expected_slice [0:SOURCES-1];
  integer seen_wide [0:SOURCES-1];
  integer total_seen;
  integer src_i;

  assign src_resp_ready = reasm_seg_ready & seg_accept_enable;

  noc_ready_valid_router #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCES(SOURCES),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W),
    .BANKS(BANKS),
    .REQ_QUEUE_DEPTH(1),
    .RESP_QUEUE_DEPTH(1),
    .ARB_MODE(1),
    .LOCALITY_BURST_MAX(2)
  ) u_router (
    .clk(clk),
    .rst_n(rst_n),
    .src_req_valid(src_req_valid),
    .src_req_ready(src_req_ready),
    .src_req_tag(src_req_tag),
    .src_req_addr(src_req_addr),
    .src_req_value_slice(src_req_value_slice),
    .src_resp_valid(src_resp_valid),
    .src_resp_ready(src_resp_ready),
    .src_resp_source(src_resp_source),
    .src_resp_tag(src_resp_tag),
    .src_resp_addr(src_resp_addr),
    .src_resp_value_slice(src_resp_value_slice),
    .src_resp_fragment_idx(src_resp_fragment_idx),
    .src_resp_last(src_resp_last),
    .src_resp_data(src_resp_data),
    .req_valid(req_valid),
    .req_ready(req_ready),
    .req_source(req_source),
    .req_tag(req_tag),
    .req_addr(req_addr),
    .req_value_slice(req_value_slice),
    .resp_valid(resp_valid),
    .resp_ready(resp_ready),
    .resp_source(resp_source),
    .resp_tag(resp_tag),
    .resp_addr(resp_addr),
    .resp_value_slice(resp_value_slice),
    .resp_fragment_idx(resp_fragment_idx),
    .resp_last(resp_last),
    .resp_data(resp_data),
    .injection_stall_cycles(router_injection_stall_cycles),
    .arbitration_contention_cycles(router_arbitration_contention_cycles),
    .response_block_cycles(router_response_block_cycles),
    .req_current_occupancy(),
    .req_max_occupancy(router_req_max_occupancy),
    .resp_current_occupancy(),
    .resp_max_occupancy(router_resp_max_occupancy)
  );

  banked_value_memory_service #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W),
    .STORE_DEPTH(STORE_DEPTH),
    .BANKS(BANKS),
    .BANK_QUEUE_DEPTH(1),
    .READ_LATENCY(2)
  ) u_service (
    .clk(clk),
    .rst_n(rst_n),
    .preload_valid(preload_valid),
    .preload_ready(preload_ready),
    .preload_addr(preload_addr),
    .preload_value_slice(preload_value_slice),
    .preload_matrix(preload_matrix),
    .req_valid(req_valid),
    .req_ready(req_ready),
    .req_source(req_source),
    .req_tag(req_tag),
    .req_addr(req_addr),
    .req_value_slice(req_value_slice),
    .resp_valid(resp_valid),
    .resp_ready(resp_ready),
    .resp_source(resp_source),
    .resp_tag(resp_tag),
    .resp_addr(resp_addr),
    .resp_value_slice(resp_value_slice),
    .resp_fragment_idx(resp_fragment_idx),
    .resp_last(resp_last),
    .resp_data(resp_data),
    .accepted_req_count(service_accepted_req_count),
    .emitted_resp_count(service_emitted_resp_count),
    .bank_conflict_count(service_bank_conflict_count),
    .response_block_cycles(service_response_block_cycles),
    .req_current_occupancy(),
    .req_max_occupancy(service_req_max_occupancy),
    .resp_current_occupancy(),
    .resp_max_occupancy(service_resp_max_occupancy)
  );

  genvar reasm_gi;
  generate
    for (reasm_gi = 0; reasm_gi < SOURCES; reasm_gi = reasm_gi + 1) begin : gen_reassembler
      noc_value_matrix_reassembler #(
        .PACKET_W(PACKET_W),
        .VALUE_W(VALUE_W),
        .SOURCE_W(SOURCE_W),
        .TAG_W(TAG_W),
        .ADDR_W(ADDR_W),
        .VALUE_SLICE_W(VALUE_SLICE_W)
      ) u_reassembler (
        .clk(clk),
        .rst_n(rst_n),
        .seg_valid(src_resp_valid[reasm_gi]),
        .seg_ready(reasm_seg_ready[reasm_gi]),
        .seg_source(src_resp_source[(reasm_gi * SOURCE_W) +: SOURCE_W]),
        .seg_tag(src_resp_tag[(reasm_gi * TAG_W) +: TAG_W]),
        .seg_addr(src_resp_addr[(reasm_gi * ADDR_W) +: ADDR_W]),
        .seg_value_slice(src_resp_value_slice[(reasm_gi * VALUE_SLICE_W) +: VALUE_SLICE_W]),
        .seg_fragment_idx(src_resp_fragment_idx[(reasm_gi * FRAG_IDX_W) +: FRAG_IDX_W]),
        .seg_last(src_resp_last[reasm_gi]),
        .seg_data(src_resp_data[(reasm_gi * PACKET_W) +: PACKET_W]),
        .wide_valid(wide_resp_valid[reasm_gi]),
        .wide_ready(wide_resp_ready[reasm_gi]),
        .wide_source(wide_resp_source[(reasm_gi * SOURCE_W) +: SOURCE_W]),
        .wide_tag(wide_resp_tag[(reasm_gi * TAG_W) +: TAG_W]),
        .wide_addr(wide_resp_addr[(reasm_gi * ADDR_W) +: ADDR_W]),
        .wide_value_slice(wide_resp_value_slice[(reasm_gi * VALUE_SLICE_W) +: VALUE_SLICE_W]),
        .wide_matrix(wide_resp_matrix[(reasm_gi * VALUE_W) +: VALUE_W]),
        .protocol_error(reasm_protocol_error[reasm_gi])
      );
    end
  endgenerate

  initial clk = 1'b0;
  always #(CLK_PERIOD/2) clk = ~clk;

  function [VALUE_W-1:0] build_matrix;
    input [15:0] matrix_id;
    integer wi;
    reg [63:0] word_value;
    begin
      build_matrix = {VALUE_W{1'b0}};
      for (wi = 0; wi < (VALUE_W / 64); wi = wi + 1) begin
        word_value = {matrix_id, wi[15:0], matrix_id ^ wi[15:0], 16'h9000 + wi[15:0]};
        build_matrix[(wi * 64) +: 64] = word_value;
      end
    end
  endfunction

  task automatic preload_entry;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    input [VALUE_W-1:0] matrix;
    begin
      @(negedge clk);
      preload_addr = addr;
      preload_value_slice = value_slice;
      preload_matrix = matrix;
      preload_valid = 1'b1;
      @(posedge clk);
      @(negedge clk);
      preload_valid = 1'b0;
    end
  endtask

  task automatic set_request;
    input integer src;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    begin
      src_req_valid[src] = 1'b1;
      src_req_tag[(src * TAG_W) +: TAG_W] = tag;
      src_req_addr[(src * ADDR_W) +: ADDR_W] = addr;
      src_req_value_slice[(src * VALUE_SLICE_W) +: VALUE_SLICE_W] = value_slice;
    end
  endtask

  task automatic clear_request;
    input integer src;
    begin
      src_req_valid[src] = 1'b0;
      src_req_tag[(src * TAG_W) +: TAG_W] = {TAG_W{1'b0}};
      src_req_addr[(src * ADDR_W) +: ADDR_W] = {ADDR_W{1'b0}};
      src_req_value_slice[(src * VALUE_SLICE_W) +: VALUE_SLICE_W] = {VALUE_SLICE_W{1'b0}};
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        seen_wide[src_i] <= 0;
      end
      total_seen <= 0;
    end else begin
      wide_resp_ready[0] <= 1'b1;
      wide_resp_ready[1] <= 1'b1;
      wide_resp_ready[2] <= (seen_wide[0] != 0);
      wide_resp_ready[3] <= 1'b1;

      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        if (wide_resp_valid[src_i] && wide_resp_ready[src_i]) begin
          if (seen_wide[src_i] != 0) begin
            $display("ERROR: duplicate wide response source=%0d", src_i);
            $finish(1);
          end
          if (wide_resp_source[(src_i * SOURCE_W) +: SOURCE_W] !== src_i[SOURCE_W-1:0]) begin
            $display("ERROR: source metadata mismatch source=%0d got=%0d",
                     src_i, wide_resp_source[(src_i * SOURCE_W) +: SOURCE_W]);
            $finish(1);
          end
          if (wide_resp_tag[(src_i * TAG_W) +: TAG_W] !== expected_tag[src_i] ||
              wide_resp_addr[(src_i * ADDR_W) +: ADDR_W] !== expected_addr[src_i] ||
              wide_resp_value_slice[(src_i * VALUE_SLICE_W) +: VALUE_SLICE_W] !== expected_slice[src_i]) begin
            $display("ERROR: response metadata mismatch source=%0d tag=%0h addr=%0h slice=%0d",
                     src_i,
                     wide_resp_tag[(src_i * TAG_W) +: TAG_W],
                     wide_resp_addr[(src_i * ADDR_W) +: ADDR_W],
                     wide_resp_value_slice[(src_i * VALUE_SLICE_W) +: VALUE_SLICE_W]);
            $finish(1);
          end
          if (wide_resp_matrix[(src_i * VALUE_W) +: VALUE_W] !== expected_matrix[src_i]) begin
            $display("ERROR: reconstructed matrix mismatch source=%0d", src_i);
            $finish(1);
          end
          seen_wide[src_i] <= 1;
          total_seen <= total_seen + 1;
        end
      end
    end
  end

  initial begin
    preload_valid = 1'b0;
    preload_addr = {ADDR_W{1'b0}};
    preload_value_slice = {VALUE_SLICE_W{1'b0}};
    preload_matrix = {VALUE_W{1'b0}};
    src_req_valid = {SOURCES{1'b0}};
    src_req_tag = {(SOURCES * TAG_W){1'b0}};
    src_req_addr = {(SOURCES * ADDR_W){1'b0}};
    src_req_value_slice = {(SOURCES * VALUE_SLICE_W){1'b0}};
    wide_resp_ready = {SOURCES{1'b0}};
    seg_accept_enable = {SOURCES{1'b1}};
    rst_n = 1'b0;
    total_seen = 0;
    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      seen_wide[src_i] = 0;
    end

    expected_matrix[0] = build_matrix(16'h0101);
    expected_matrix[1] = build_matrix(16'h0202);
    expected_matrix[2] = build_matrix(16'h0303);
    expected_matrix[3] = build_matrix(16'h0404);
    expected_tag[0] = 8'h10;
    expected_tag[1] = 8'h20;
    expected_tag[2] = 8'h30;
    expected_tag[3] = 8'h40;
    expected_addr[0] = 12'd0;
    expected_addr[1] = 12'd0;
    expected_addr[2] = 12'd1;
    expected_addr[3] = 12'd3;
    expected_slice[0] = 4'h1;
    expected_slice[1] = 4'h2;
    expected_slice[2] = 4'h3;
    expected_slice[3] = 4'h4;

    #(CLK_PERIOD * 4);
    rst_n = 1'b1;

    preload_entry(12'd0, 4'h1, expected_matrix[0]);
    preload_entry(12'd0, 4'h2, expected_matrix[1]);
    preload_entry(12'd1, 4'h3, expected_matrix[2]);
    preload_entry(12'd3, 4'h4, expected_matrix[3]);

    @(negedge clk);
    set_request(0, 8'h10, 12'd0, 4'h1);
    set_request(1, 8'h20, 12'd0, 4'h2);
    set_request(2, 8'h30, 12'd1, 4'h3);
    set_request(3, 8'h40, 12'd3, 4'h4);
    @(posedge clk);
    @(negedge clk);
    clear_request(0);
    clear_request(1);
    clear_request(2);
    clear_request(3);

    wait (total_seen == SOURCES);
    repeat (4) @(posedge clk);

    if (service_accepted_req_count != SOURCES || service_emitted_resp_count != SOURCES) begin
      $display("ERROR: service request/response counts mismatch req=%0d resp=%0d expected=%0d",
               service_accepted_req_count, service_emitted_resp_count, SOURCES);
      $finish(1);
    end
    if (service_bank_conflict_count == 0) begin
      $display("ERROR: expected service bank conflicts");
      $finish(1);
    end
    if (router_arbitration_contention_cycles == 0) begin
      $display("ERROR: expected router contention counter to move contention=%0d",
               router_arbitration_contention_cycles);
      $finish(1);
    end
    if (router_req_max_occupancy == 0 || router_resp_max_occupancy == 0 ||
        service_req_max_occupancy == 0 || service_resp_max_occupancy == 0) begin
      $display("ERROR: expected occupancy counters to rise");
      $finish(1);
    end
    if (reasm_protocol_error != {SOURCES{1'b0}}) begin
      $display("ERROR: protocol_error asserted during valid traffic flags=%b",
               reasm_protocol_error);
      $finish(1);
    end

    $display("PASS: tb_banked_value_memory_service packet_w=%0d", PACKET_W);
    $finish(0);
  end
  initial begin
    repeat (1200) @(posedge clk);
    $display("ERROR: tb_banked_value_memory_service timeout");
    $finish(1);
  end
endmodule
