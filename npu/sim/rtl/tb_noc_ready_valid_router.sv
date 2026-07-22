`timescale 1ns/1ps

module tb_noc_ready_valid_router;
  parameter integer PACKET_W = 128;
  parameter integer ARB_MODE = 0;
  localparam integer CLK_PERIOD = 10;
  localparam integer SOURCES = 3;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 12;
  localparam integer SLICE_W = 3;
  localparam integer BANKS = 2;
  localparam integer REQ_QUEUE_DEPTH = 1;
  localparam integer RESP_QUEUE_DEPTH = 1;
  localparam integer SRC_LSB = 0;
  localparam integer TAG_LSB = SRC_LSB + SOURCE_W;
  localparam integer ADDR_LSB = TAG_LSB + TAG_W;
  localparam integer SLICE_LSB = ADDR_LSB + ADDR_W;
  localparam integer PAYLOAD_LSB = SLICE_LSB + SLICE_W;
  localparam integer PAYLOAD_W = PACKET_W - PAYLOAD_LSB;

  reg clk;
  reg rst_n;

  reg [SOURCES-1:0] src_req_valid;
  wire [SOURCES-1:0] src_req_ready;
  reg [SOURCES*PACKET_W-1:0] src_req_packet;
  wire [SOURCES-1:0] src_resp_valid;
  reg [SOURCES-1:0] src_resp_ready;
  wire [SOURCES*PACKET_W-1:0] src_resp_packet;

  wire req_valid;
  reg req_ready;
  wire [PACKET_W-1:0] req_packet;

  reg resp_valid;
  wire resp_ready;
  reg [PACKET_W-1:0] resp_packet;

  wire [31:0] injection_stall_cycles;
  wire [31:0] arbitration_contention_cycles;
  wire [31:0] response_block_cycles;
  wire [31:0] req_max_occupancy;
  wire [31:0] resp_max_occupancy;

  integer observed_reqs [0:3];
  integer expected_req_order [0:2];
  integer observed_req_count;
  integer observed_resp_tags [0:SOURCES-1][0:1];
  integer observed_resp_count [0:SOURCES-1];
  integer cycle_count;
  integer src_i;

  noc_ready_valid_router #(
    .PACKET_W(PACKET_W),
    .SOURCES(SOURCES),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .SLICE_W(SLICE_W),
    .BANKS(BANKS),
    .REQ_QUEUE_DEPTH(REQ_QUEUE_DEPTH),
    .RESP_QUEUE_DEPTH(RESP_QUEUE_DEPTH),
    .ARB_MODE(ARB_MODE)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .src_req_valid(src_req_valid),
    .src_req_ready(src_req_ready),
    .src_req_packet(src_req_packet),
    .src_resp_valid(src_resp_valid),
    .src_resp_ready(src_resp_ready),
    .src_resp_packet(src_resp_packet),
    .req_valid(req_valid),
    .req_ready(req_ready),
    .req_packet(req_packet),
    .resp_valid(resp_valid),
    .resp_ready(resp_ready),
    .resp_packet(resp_packet),
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

  function [PACKET_W-1:0] pack_packet;
    input [SOURCE_W-1:0] src;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [SLICE_W-1:0] slice;
    input [PAYLOAD_W-1:0] payload;
    begin
      pack_packet = {PACKET_W{1'b0}};
      pack_packet[SRC_LSB +: SOURCE_W] = src;
      pack_packet[TAG_LSB +: TAG_W] = tag;
      pack_packet[ADDR_LSB +: ADDR_W] = addr;
      pack_packet[SLICE_LSB +: SLICE_W] = slice;
      pack_packet[PAYLOAD_LSB +: PAYLOAD_W] = payload;
    end
  endfunction

  function [TAG_W-1:0] packet_tag;
    input [PACKET_W-1:0] packet;
    begin
      packet_tag = packet[TAG_LSB +: TAG_W];
    end
  endfunction

  task automatic set_source_packet;
    input integer src;
    input [PACKET_W-1:0] packet;
    begin
      src_req_packet[(src * PACKET_W) +: PACKET_W] = packet;
      src_req_valid[src] = 1'b1;
    end
  endtask

  task automatic clear_source;
    input integer src;
    begin
      src_req_packet[(src * PACKET_W) +: PACKET_W] = {PACKET_W{1'b0}};
      src_req_valid[src] = 1'b0;
    end
  endtask

  task automatic send_response;
    input [PACKET_W-1:0] packet;
    begin : wait_handshake
      resp_packet = packet;
      resp_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (resp_valid && resp_ready) begin
          @(negedge clk);
          resp_valid = 1'b0;
          resp_packet = {PACKET_W{1'b0}};
          disable wait_handshake;
        end
      end
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      observed_req_count <= 0;
      cycle_count <= 0;
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        observed_resp_count[src_i] <= 0;
      end
    end else begin
      cycle_count <= cycle_count + 1;
      if (req_valid && req_ready && observed_req_count < 4) begin
        observed_reqs[observed_req_count] <= packet_tag(req_packet);
        observed_req_count <= observed_req_count + 1;
      end
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        if (src_resp_valid[src_i] && src_resp_ready[src_i]) begin
          observed_resp_tags[src_i][observed_resp_count[src_i]] <= packet_tag(src_resp_packet[(src_i * PACKET_W) +: PACKET_W]);
          observed_resp_count[src_i] <= observed_resp_count[src_i] + 1;
        end
      end
    end
  end

  initial begin
    src_req_valid = {SOURCES{1'b0}};
    src_req_packet = {(SOURCES * PACKET_W){1'b0}};
    src_resp_ready = {SOURCES{1'b0}};
    req_ready = 1'b0;
    resp_valid = 1'b0;
    resp_packet = {PACKET_W{1'b0}};
    rst_n = 1'b0;
    observed_req_count = 0;
    cycle_count = 0;
    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      observed_resp_count[src_i] = 0;
    end

    if (ARB_MODE == 0) begin
      expected_req_order[0] = 8'h10;
      expected_req_order[1] = 8'h20;
      expected_req_order[2] = 8'h30;
    end else begin
      expected_req_order[0] = 8'h10;
      expected_req_order[1] = 8'h30;
      expected_req_order[2] = 8'h20;
    end

    #(CLK_PERIOD * 4);
    rst_n = 1'b1;

    @(negedge clk);
    set_source_packet(0, pack_packet(0, 8'h10, 12'd0, 0, {PAYLOAD_W{1'b0}}));
    set_source_packet(1, pack_packet(1, 8'h20, 12'd1, 0, {PAYLOAD_W{1'b0}}));
    set_source_packet(2, pack_packet(2, 8'h30, 12'd0, 0, {PAYLOAD_W{1'b0}}));
    wait (&src_req_ready);
    @(posedge clk);
    @(negedge clk);
    clear_source(0);
    clear_source(1);
    clear_source(2);

    @(negedge clk);
    set_source_packet(0, pack_packet(0, 8'h11, 12'd2, 0, {PAYLOAD_W{1'b0}}));
    repeat (3) @(posedge clk);
    @(negedge clk);
    clear_source(0);
    req_ready = 1'b1;
    wait (observed_req_count >= 3);

    src_resp_ready = 3'b101;
    send_response(pack_packet(1, 8'ha0, 12'd9, 0, {PAYLOAD_W{1'b1}}));
    @(negedge clk);
    resp_packet = pack_packet(1, 8'ha1, 12'd9, 0, {PAYLOAD_W{1'b0}});
    resp_valid = 1'b1;
    repeat (4) @(posedge clk);
    @(negedge clk);
    resp_valid = 1'b0;
    resp_packet = {PACKET_W{1'b0}};
    src_resp_ready[1] = 1'b1;
    wait (observed_resp_count[1] == 1);
    send_response(pack_packet(1, 8'ha1, 12'd9, 0, {PAYLOAD_W{1'b0}}));
    send_response(pack_packet(0, 8'hb0, 12'd4, 0, {{(PAYLOAD_W-8){1'b0}}, 8'h55}));
    wait (observed_resp_count[0] == 1 && observed_resp_count[1] == 2);
    repeat (2) @(posedge clk);

    for (src_i = 0; src_i < 3; src_i = src_i + 1) begin
      if (observed_reqs[src_i] !== expected_req_order[src_i]) begin
        $display("ERROR: request order mismatch index=%0d got=%0h expected=%0h",
                 src_i, observed_reqs[src_i], expected_req_order[src_i]);
        $finish(1);
      end
    end
    if (observed_resp_tags[1][0] !== 8'ha0 || observed_resp_tags[1][1] !== 8'ha1 ||
        observed_resp_tags[0][0] !== 8'hb0) begin
      $display("ERROR: response routing mismatch");
      $finish(1);
    end
    if (injection_stall_cycles == 0 || arbitration_contention_cycles == 0 || response_block_cycles == 0) begin
      $display("ERROR: expected router counters to move stall=%0d contention=%0d response_block=%0d",
               injection_stall_cycles, arbitration_contention_cycles, response_block_cycles);
      $finish(1);
    end
    if (req_max_occupancy < 2 || resp_max_occupancy == 0) begin
      $display("ERROR: expected occupancy counters to rise req=%0d resp=%0d",
               req_max_occupancy, resp_max_occupancy);
      $finish(1);
    end

    $display("PASS: tb_noc_ready_valid_router packet_w=%0d arb_mode=%0d", PACKET_W, ARB_MODE);
    $finish(0);
  end

  initial begin
    repeat (300) @(posedge clk);
    $display("ERROR: tb_noc_ready_valid_router timeout");
    $finish(1);
  end
endmodule
