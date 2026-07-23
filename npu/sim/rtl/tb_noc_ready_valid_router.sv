`timescale 1ns/1ps

module tb_noc_ready_valid_router;
  parameter integer PACKET_W = 128;
  parameter integer ARB_MODE = 0;
  localparam integer CLK_PERIOD = 10;
  localparam integer VALUE_W = 512;
  localparam integer SOURCES = 3;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 12;
  localparam integer VALUE_SLICE_W = 4;
  localparam integer BANKS = 2;
  localparam integer REQ_QUEUE_DEPTH = 1;
  localparam integer RESP_QUEUE_DEPTH = 1;
  localparam integer LOCALITY_BURST_MAX = 2;
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;
  localparam integer FRAG_IDX_W = (FRAGMENTS <= 1) ? 1 : $clog2(FRAGMENTS);

  reg clk;
  reg rst_n;

  reg [SOURCES-1:0] src_req_valid;
  wire [SOURCES-1:0] src_req_ready;
  reg [SOURCES*TAG_W-1:0] src_req_tag;
  reg [SOURCES*ADDR_W-1:0] src_req_addr;
  reg [SOURCES*VALUE_SLICE_W-1:0] src_req_value_slice;

  wire [SOURCES-1:0] src_resp_valid;
  reg [SOURCES-1:0] src_resp_ready;
  wire [SOURCES*SOURCE_W-1:0] src_resp_source;
  wire [SOURCES*TAG_W-1:0] src_resp_tag;
  wire [SOURCES*ADDR_W-1:0] src_resp_addr;
  wire [SOURCES*VALUE_SLICE_W-1:0] src_resp_value_slice;
  wire [SOURCES*FRAG_IDX_W-1:0] src_resp_fragment_idx;
  wire [SOURCES-1:0] src_resp_last;
  wire [SOURCES*PACKET_W-1:0] src_resp_data;

  wire req_valid;
  reg req_ready;
  wire [SOURCE_W-1:0] req_source;
  wire [TAG_W-1:0] req_tag;
  wire [ADDR_W-1:0] req_addr;
  wire [VALUE_SLICE_W-1:0] req_value_slice;

  reg resp_valid;
  wire resp_ready;
  reg [SOURCE_W-1:0] resp_source;
  reg [TAG_W-1:0] resp_tag;
  reg [ADDR_W-1:0] resp_addr;
  reg [VALUE_SLICE_W-1:0] resp_value_slice;
  reg [FRAG_IDX_W-1:0] resp_fragment_idx;
  reg resp_last;
  reg [PACKET_W-1:0] resp_data;

  wire [31:0] injection_stall_cycles;
  wire [31:0] arbitration_contention_cycles;
  wire [31:0] response_block_cycles;
  wire [31:0] req_max_occupancy;
  wire [31:0] resp_max_occupancy;

  integer observed_req_tags [0:15];
  integer observed_req_sources [0:15];
  integer observed_req_count;
  integer fairness_grants_to_source1;
  integer fairness_total_grants;
  integer fairness_nonpreferred_gap;
  integer fairness_max_gap;
  integer observed_resp_tags [0:SOURCES-1][0:3];
  integer observed_resp_frags [0:SOURCES-1][0:3];
  integer observed_resp_count [0:SOURCES-1];
  integer src_i;

  noc_ready_valid_router #(
    .PACKET_W(PACKET_W),
    .VALUE_W(VALUE_W),
    .SOURCES(SOURCES),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .VALUE_SLICE_W(VALUE_SLICE_W),
    .BANKS(BANKS),
    .REQ_QUEUE_DEPTH(REQ_QUEUE_DEPTH),
    .RESP_QUEUE_DEPTH(RESP_QUEUE_DEPTH),
    .ARB_MODE(ARB_MODE),
    .LOCALITY_BURST_MAX(LOCALITY_BURST_MAX)
  ) dut (
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
    .injection_stall_cycles(injection_stall_cycles),
    .arbitration_contention_cycles(arbitration_contention_cycles),
    .response_block_cycles(response_block_cycles),
    .req_current_occupancy(),
    .req_max_occupancy(req_max_occupancy),
    .resp_current_occupancy(),
    .resp_max_occupancy(resp_max_occupancy)
  );

  initial clk = 1'b0;
  always #(CLK_PERIOD/2) clk = ~clk;

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

  task automatic issue_response;
    input [SOURCE_W-1:0] source;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    input [FRAG_IDX_W-1:0] fragment_idx;
    input last;
    input [PACKET_W-1:0] data;
    begin : wait_fire
      @(negedge clk);
      resp_source = source;
      resp_tag = tag;
      resp_addr = addr;
      resp_value_slice = value_slice;
      resp_fragment_idx = fragment_idx;
      resp_last = last;
      resp_data = data;
      resp_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (resp_valid && resp_ready) begin
          @(negedge clk);
          resp_valid = 1'b0;
          disable wait_fire;
        end
      end
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      observed_req_count <= 0;
      fairness_grants_to_source1 <= 0;
      fairness_total_grants <= 0;
      fairness_nonpreferred_gap <= 0;
      fairness_max_gap <= 0;
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        observed_resp_count[src_i] <= 0;
      end
    end else begin
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        if (src_resp_valid[src_i] && src_resp_ready[src_i]) begin
          observed_resp_tags[src_i][observed_resp_count[src_i]] <=
            src_resp_tag[(src_i * TAG_W) +: TAG_W];
          observed_resp_frags[src_i][observed_resp_count[src_i]] <=
            src_resp_fragment_idx[(src_i * FRAG_IDX_W) +: FRAG_IDX_W];
          observed_resp_count[src_i] <= observed_resp_count[src_i] + 1;
        end
      end

      if (req_valid && req_ready) begin
        observed_req_tags[observed_req_count] <= req_tag;
        observed_req_sources[observed_req_count] <= req_source;
        observed_req_count <= observed_req_count + 1;
        if ((ARB_MODE == 1) && (fairness_total_grants < 6)) begin
          fairness_total_grants <= fairness_total_grants + 1;
          if (req_source == 1) begin
            fairness_grants_to_source1 <= fairness_grants_to_source1 + 1;
            fairness_nonpreferred_gap <= 0;
          end else begin
            fairness_nonpreferred_gap <= fairness_nonpreferred_gap + 1;
            if ((fairness_nonpreferred_gap + 1) > fairness_max_gap) begin
              fairness_max_gap <= fairness_nonpreferred_gap + 1;
            end
          end
        end
      end
    end
  end

  initial begin
    src_req_valid = {SOURCES{1'b0}};
    src_req_tag = {(SOURCES * TAG_W){1'b0}};
    src_req_addr = {(SOURCES * ADDR_W){1'b0}};
    src_req_value_slice = {(SOURCES * VALUE_SLICE_W){1'b0}};
    src_resp_ready = {SOURCES{1'b0}};
    req_ready = 1'b0;
    resp_valid = 1'b0;
    resp_source = {SOURCE_W{1'b0}};
    resp_tag = {TAG_W{1'b0}};
    resp_addr = {ADDR_W{1'b0}};
    resp_value_slice = {VALUE_SLICE_W{1'b0}};
    resp_fragment_idx = {FRAG_IDX_W{1'b0}};
    resp_last = 1'b0;
    resp_data = {PACKET_W{1'b0}};
    rst_n = 1'b0;
    observed_req_count = 0;
    fairness_grants_to_source1 = 0;
    fairness_total_grants = 0;
    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      observed_resp_count[src_i] = 0;
    end

    #(CLK_PERIOD * 4);
    rst_n = 1'b1;

    @(negedge clk);
    set_request(0, 8'h01, 12'd0, 4'h0);
    repeat (3) @(posedge clk);
    @(negedge clk);
    clear_request(0);
    req_ready = 1'b1;
    wait (observed_req_count >= 1);
    if (observed_req_sources[0] !== 0) begin
      $display("ERROR: request source spoofed through ingress got=%0d", observed_req_sources[0]);
      $finish(1);
    end
    observed_req_count = 0;
    req_ready = 1'b0;

    @(negedge clk);
    set_request(0, 8'h10, 12'd0, 4'h1);
    set_request(1, 8'h20, 12'd1, 4'h2);
    set_request(2, 8'h30, 12'd0, 4'h3);
    @(posedge clk);
    @(negedge clk);
    clear_request(0);
    clear_request(1);
    clear_request(2);
    repeat (2) @(posedge clk);
    req_ready = 1'b1;
    wait (observed_req_count >= 3);

    if (ARB_MODE == 0) begin
      if (observed_req_tags[0] !== 8'h20 || observed_req_tags[1] !== 8'h30 || observed_req_tags[2] !== 8'h10) begin
        $display("ERROR: RR order mismatch got=%0h,%0h,%0h",
                 observed_req_tags[0], observed_req_tags[1], observed_req_tags[2]);
        $finish(1);
      end
    end else begin
      if (observed_req_tags[0] !== 8'h30 || observed_req_tags[1] !== 8'h20 || observed_req_tags[2] !== 8'h10) begin
        $display("ERROR: locality-first order mismatch got=%0h,%0h,%0h",
                 observed_req_tags[0], observed_req_tags[1], observed_req_tags[2]);
        $finish(1);
      end
    end

    if (ARB_MODE == 1) begin
      observed_req_count = 0;
      fairness_total_grants = 0;
      fairness_grants_to_source1 = 0;
      fairness_nonpreferred_gap = 0;
      fairness_max_gap = 0;
      @(negedge clk);
      set_request(0, 8'h40, 12'd0, 4'h4);
      set_request(1, 8'h50, 12'd1, 4'h5);
      set_request(2, 8'h60, 12'd0, 4'h6);
      repeat (6) @(posedge clk);
      @(negedge clk);
      clear_request(0);
      clear_request(1);
      clear_request(2);
      if (fairness_grants_to_source1 < 2) begin
        $display("ERROR: locality-first fairness failed to sustain service for the nonpreferred bank");
        $finish(1);
      end
      if (fairness_max_gap > LOCALITY_BURST_MAX) begin
        $display("ERROR: locality-first fairness gap exceeded bound gap=%0d bound=%0d",
                 fairness_max_gap, LOCALITY_BURST_MAX);
        $finish(1);
      end
    end

    src_resp_ready = 3'b101;
    fork
      begin
        issue_response(1, 8'ha0, 12'd5, 4'h8, 0, 1'b0, {PACKET_W{1'b1}});
        issue_response(1, 8'ha0, 12'd5, 4'h8, FRAGMENTS-1, 1'b1, {PACKET_W{1'b0}});
      end
      begin
        repeat (5) @(posedge clk);
        @(negedge clk);
        src_resp_ready[1] = 1'b1;
      end
    join
    issue_response(0, 8'hb0, 12'd9, 4'h9, 0, 1'b1, {{(PACKET_W-8){1'b0}}, 8'h55});
    wait ((observed_resp_count[1] == 2) && (observed_resp_count[0] == 1));
    repeat (2) @(posedge clk);

    if (observed_resp_tags[1][0] !== 8'ha0 ||
        observed_resp_frags[1][0] !== 0 ||
        observed_resp_tags[1][1] !== 8'ha0 ||
        observed_resp_frags[1][1] !== (FRAGMENTS - 1) ||
        observed_resp_tags[0][0] !== 8'hb0) begin
      $display("ERROR: response routing metadata mismatch");
      $finish(1);
    end
    if (injection_stall_cycles == 0 || arbitration_contention_cycles == 0 || response_block_cycles == 0) begin
      $display("ERROR: expected router counters to move stall=%0d contention=%0d block=%0d",
               injection_stall_cycles, arbitration_contention_cycles, response_block_cycles);
      $finish(1);
    end
    if (req_max_occupancy == 0 || resp_max_occupancy == 0) begin
      $display("ERROR: expected router occupancy counters to move req=%0d resp=%0d",
               req_max_occupancy, resp_max_occupancy);
      $finish(1);
    end

    $display("PASS: tb_noc_ready_valid_router packet_w=%0d arb_mode=%0d", PACKET_W, ARB_MODE);
    $finish(0);
  end

  initial begin
    repeat (400) @(posedge clk);
    $display("ERROR: tb_noc_ready_valid_router timeout");
    $finish(1);
  end
endmodule
