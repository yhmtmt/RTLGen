`timescale 1ns/1ps

module tb_banked_value_memory_service_parallel;
  parameter integer PACKET_W = 128;
  localparam integer CLK_PERIOD = 10;
  localparam integer VALUE_W = 512;
  localparam integer SOURCES = 2;
  localparam integer SOURCE_W = 1;
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
  reg [SOURCES*SOURCE_W-1:0] src_req_source;
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

  wire [31:0] service_accepted_req_count;
  wire [31:0] service_emitted_resp_count;
  wire [31:0] service_response_block_cycles;

  wire [SOURCES-1:0] wide_resp_valid;
  reg [SOURCES-1:0] wide_resp_ready;
  reg [SOURCES-1:0] seg_accept_enable;
  wire [SOURCES*SOURCE_W-1:0] wide_resp_source;
  wire [SOURCES*TAG_W-1:0] wide_resp_tag;
  wire [SOURCES*ADDR_W-1:0] wide_resp_addr;
  wire [SOURCES*VALUE_SLICE_W-1:0] wide_resp_value_slice;
  wire [SOURCES*VALUE_W-1:0] wide_resp_matrix;

  reg [VALUE_W-1:0] expected_matrix [0:1];
  reg [TAG_W-1:0] expected_tag [0:1];
  reg [ADDR_W-1:0] expected_addr [0:1];
  reg [VALUE_SLICE_W-1:0] expected_slice [0:1];
  reg [TAG_W-1:0] expected_group_tag [0:1];
  reg [TAG_W-1:0] observed_seg_tag [0:(2 * FRAGMENTS) - 1];
  reg [FRAG_IDX_W-1:0] observed_seg_frag [0:(2 * FRAGMENTS) - 1];
  integer observed_seg_count;
  integer observed_wide_count;
  integer wide_release_done;
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
    .src_req_source(src_req_source),
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
    .injection_stall_cycles(),
    .arbitration_contention_cycles(),
    .response_block_cycles(),
    .req_current_occupancy(),
    .req_max_occupancy(),
    .resp_current_occupancy(),
    .resp_max_occupancy()
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
    .READ_LATENCY(1)
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
    .bank_conflict_count(),
    .response_block_cycles(service_response_block_cycles),
    .req_current_occupancy(),
    .req_max_occupancy(),
    .resp_current_occupancy(),
    .resp_max_occupancy()
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
        word_value = {matrix_id, wi[15:0], matrix_id ^ wi[15:0], 16'h7000 + wi[15:0]};
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

  task automatic pulse_request;
    input integer src;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    begin
      @(negedge clk);
      src_req_valid[src] = 1'b1;
      src_req_source[(src * SOURCE_W) +: SOURCE_W] = {SOURCE_W{1'b1}};
      src_req_tag[(src * TAG_W) +: TAG_W] = tag;
      src_req_addr[(src * ADDR_W) +: ADDR_W] = addr;
      src_req_value_slice[(src * VALUE_SLICE_W) +: VALUE_SLICE_W] = value_slice;
      while (!src_req_ready[src]) begin
        @(posedge clk);
        @(negedge clk);
      end
      @(posedge clk);
      @(negedge clk);
      src_req_valid[src] = 1'b0;
      src_req_source[(src * SOURCE_W) +: SOURCE_W] = {SOURCE_W{1'b0}};
      src_req_tag[(src * TAG_W) +: TAG_W] = {TAG_W{1'b0}};
      src_req_addr[(src * ADDR_W) +: ADDR_W] = {ADDR_W{1'b0}};
      src_req_value_slice[(src * VALUE_SLICE_W) +: VALUE_SLICE_W] = {VALUE_SLICE_W{1'b0}};
    end
  endtask

  always @(posedge clk) begin
      if (!rst_n) begin
      observed_seg_count <= 0;
      observed_wide_count <= 0;
      wide_release_done <= 0;
    end else begin
      wide_resp_ready[1] <= 1'b1;

      if (src_resp_valid[0] && src_resp_ready[0]) begin
        observed_seg_tag[observed_seg_count] <= src_resp_tag[0 +: TAG_W];
        observed_seg_frag[observed_seg_count] <= src_resp_fragment_idx[0 +: FRAG_IDX_W];
        observed_seg_count <= observed_seg_count + 1;
      end

      if (wide_resp_valid[0] && wide_resp_ready[0]) begin
        if (observed_wide_count >= 2) begin
          $display("ERROR: unexpected extra wide response");
          $finish(1);
        end
        if (wide_resp_source[0 +: SOURCE_W] !== {SOURCE_W{1'b0}} ||
            wide_resp_tag[0 +: TAG_W] !== expected_tag[observed_wide_count] ||
            wide_resp_addr[0 +: ADDR_W] !== expected_addr[observed_wide_count] ||
            wide_resp_value_slice[0 +: VALUE_SLICE_W] !== expected_slice[observed_wide_count] ||
            wide_resp_matrix[0 +: VALUE_W] !== expected_matrix[observed_wide_count]) begin
          $display("ERROR: wide response mismatch index=%0d", observed_wide_count);
          $finish(1);
        end
        observed_wide_count <= observed_wide_count + 1;
      end

      if (wide_resp_valid[0] && !wide_release_done && (service_accepted_req_count == 2)) begin
        wide_release_done <= 1;
        fork
          begin
            repeat (2) @(posedge clk);
            wide_resp_ready[0] <= 1'b1;
          end
        join_none
      end
    end
  end

  initial begin
    preload_valid = 1'b0;
    preload_addr = {ADDR_W{1'b0}};
    preload_value_slice = {VALUE_SLICE_W{1'b0}};
    preload_matrix = {VALUE_W{1'b0}};
    src_req_valid = {SOURCES{1'b0}};
    src_req_source = {(SOURCES * SOURCE_W){1'b0}};
    src_req_tag = {(SOURCES * TAG_W){1'b0}};
    src_req_addr = {(SOURCES * ADDR_W){1'b0}};
    src_req_value_slice = {(SOURCES * VALUE_SLICE_W){1'b0}};
    wide_resp_ready = {SOURCES{1'b0}};
    seg_accept_enable = {SOURCES{1'b1}};
    rst_n = 1'b0;
    observed_seg_count = 0;
    observed_wide_count = 0;
    wide_release_done = 0;

    expected_matrix[0] = build_matrix(16'h1111);
    expected_matrix[1] = build_matrix(16'h2222);
    expected_tag[0] = 8'h11;
    expected_tag[1] = 8'h22;
    expected_addr[0] = 12'd0;
    expected_addr[1] = 12'd1;
    expected_slice[0] = 4'h1;
    expected_slice[1] = 4'h2;
    expected_group_tag[0] = expected_tag[0];
    expected_group_tag[1] = expected_tag[1];

    #(CLK_PERIOD * 4);
    rst_n = 1'b1;

    preload_entry(expected_addr[0], expected_slice[0], expected_matrix[0]);
    preload_entry(expected_addr[1], expected_slice[1], expected_matrix[1]);

    fork
      pulse_request(0, expected_tag[0], expected_addr[0], expected_slice[0]);
      begin
        wait (service_accepted_req_count >= 1);
        pulse_request(0, expected_tag[1], expected_addr[1], expected_slice[1]);
      end
    join

    wait (service_accepted_req_count == 2);
    wait (observed_wide_count == 2);
    repeat (2) @(posedge clk);

    if (reasm_protocol_error != {SOURCES{1'b0}}) begin
      $display("ERROR: protocol_error asserted during valid same-source traffic flags=%b",
               reasm_protocol_error);
      $finish(1);
    end
    if (service_emitted_resp_count != 2 || service_response_block_cycles == 0) begin
      $display("ERROR: expected two packets and response backpressure resp=%0d block=%0d",
               service_emitted_resp_count, service_response_block_cycles);
      $finish(1);
    end
    if ((observed_seg_tag[0] == observed_seg_tag[FRAGMENTS]) ||
        ((observed_seg_tag[0] != expected_tag[0]) && (observed_seg_tag[0] != expected_tag[1])) ||
        ((observed_seg_tag[FRAGMENTS] != expected_tag[0]) && (observed_seg_tag[FRAGMENTS] != expected_tag[1]))) begin
      $display("ERROR: expected two distinct packet groups got tags=%0h,%0h",
               observed_seg_tag[0], observed_seg_tag[FRAGMENTS]);
      $finish(1);
    end
    for (src_i = 0; src_i < FRAGMENTS; src_i = src_i + 1) begin
      if (observed_seg_tag[src_i] !== observed_seg_tag[0] ||
          observed_seg_frag[src_i] !== src_i[FRAG_IDX_W-1:0]) begin
        $display("ERROR: first packet segment order mismatch idx=%0d tag=%0h frag=%0d",
                 src_i, observed_seg_tag[src_i], observed_seg_frag[src_i]);
        $finish(1);
      end
      if (observed_seg_tag[src_i + FRAGMENTS] !== observed_seg_tag[FRAGMENTS] ||
          observed_seg_frag[src_i + FRAGMENTS] !== src_i[FRAG_IDX_W-1:0]) begin
        $display("ERROR: second packet segment order mismatch idx=%0d tag=%0h frag=%0d",
                 src_i + FRAGMENTS,
                 observed_seg_tag[src_i + FRAGMENTS],
                 observed_seg_frag[src_i + FRAGMENTS]);
        $finish(1);
      end
    end

    $display("PASS: tb_banked_value_memory_service_parallel packet_w=%0d", PACKET_W);
    $finish(0);
  end

  initial begin
    repeat (1200) @(posedge clk);
    $display("ERROR: tb_banked_value_memory_service_parallel timeout");
    $finish(1);
  end
endmodule
