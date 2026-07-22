`timescale 1ns/1ps

module tb_banked_value_memory_service;
  parameter integer PACKET_W = 128;
  localparam integer CLK_PERIOD = 10;
  localparam integer SOURCES = 4;
  localparam integer SOURCE_W = 2;
  localparam integer TAG_W = 8;
  localparam integer ADDR_W = 12;
  localparam integer SLICE_W = 3;
  localparam integer VALUE_W = 512;
  localparam integer BANKS = 2;
  localparam integer ARB_MODE = 1;
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
  wire req_ready;
  wire [PACKET_W-1:0] req_packet;
  wire resp_valid;
  wire resp_ready;
  wire [PACKET_W-1:0] resp_packet;

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

  reg [PACKET_W-1:0] source_packets [0:SOURCES-1][0:2];
  integer sent_count [0:SOURCES-1];
  integer expected_count [0:SOURCES-1];
  integer received_count [0:SOURCES-1];
  integer seen_tag [0:SOURCES-1][0:7];
  integer cycle_count;
  integer total_expected;
  integer total_received;
  integer src_i;
  integer slot_i;

  noc_ready_valid_router #(
    .PACKET_W(PACKET_W),
    .SOURCES(SOURCES),
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .SLICE_W(SLICE_W),
    .BANKS(BANKS),
    .REQ_QUEUE_DEPTH(2),
    .RESP_QUEUE_DEPTH(2),
    .ARB_MODE(ARB_MODE)
  ) u_router (
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
    .SOURCE_W(SOURCE_W),
    .TAG_W(TAG_W),
    .ADDR_W(ADDR_W),
    .SLICE_W(SLICE_W),
    .VALUE_W(VALUE_W),
    .BANKS(BANKS),
    .BANK_QUEUE_DEPTH(2),
    .RESP_QUEUE_DEPTH(1),
    .READ_LATENCY(3)
  ) u_service (
    .clk(clk),
    .rst_n(rst_n),
    .req_valid(req_valid),
    .req_ready(req_ready),
    .req_packet(req_packet),
    .resp_valid(resp_valid),
    .resp_ready(resp_ready),
    .resp_packet(resp_packet),
    .accepted_req_count(service_accepted_req_count),
    .emitted_resp_count(service_emitted_resp_count),
    .bank_conflict_count(service_bank_conflict_count),
    .response_block_cycles(service_response_block_cycles),
    .req_current_occupancy(),
    .req_max_occupancy(service_req_max_occupancy),
    .resp_current_occupancy(),
    .resp_max_occupancy(service_resp_max_occupancy)
  );

  initial clk = 1'b0;
  always #(CLK_PERIOD/2) clk = ~clk;

  function [PACKET_W-1:0] pack_packet;
    input [SOURCE_W-1:0] src;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [SLICE_W-1:0] slice;
    begin
      pack_packet = {PACKET_W{1'b0}};
      pack_packet[SRC_LSB +: SOURCE_W] = src;
      pack_packet[TAG_LSB +: TAG_W] = tag;
      pack_packet[ADDR_LSB +: ADDR_W] = addr;
      pack_packet[SLICE_LSB +: SLICE_W] = slice;
    end
  endfunction

  function [TAG_W-1:0] packet_tag;
    input [PACKET_W-1:0] packet;
    begin
      packet_tag = packet[TAG_LSB +: TAG_W];
    end
  endfunction

  function [ADDR_W-1:0] packet_addr;
    input [PACKET_W-1:0] packet;
    begin
      packet_addr = packet[ADDR_LSB +: ADDR_W];
    end
  endfunction

  function [SLICE_W-1:0] packet_slice;
    input [PACKET_W-1:0] packet;
    begin
      packet_slice = packet[SLICE_LSB +: SLICE_W];
    end
  endfunction

  function [PAYLOAD_W-1:0] packet_payload;
    input [PACKET_W-1:0] packet;
    begin
      packet_payload = packet[PAYLOAD_LSB +: PAYLOAD_W];
    end
  endfunction

  function [VALUE_W-1:0] make_value_line;
    input [ADDR_W-1:0] addr;
    integer word_i;
    reg [63:0] word_value;
    begin
      make_value_line = {VALUE_W{1'b0}};
      for (word_i = 0; word_i < (VALUE_W / 64); word_i = word_i + 1) begin
        word_value = {16'hd000 + word_i[15:0], 16'h4100 + addr[15:0], 16'h2200 + word_i[15:0], addr[15:0] ^ (word_i * 16'h0011)};
        make_value_line[(word_i * 64) +: 64] = word_value;
      end
    end
  endfunction

  function [PAYLOAD_W-1:0] expected_payload;
    input [ADDR_W-1:0] addr;
    input [SLICE_W-1:0] slice;
    integer bit_i;
    integer line_bit;
    reg [VALUE_W-1:0] line;
    begin
      line = make_value_line(addr);
      expected_payload = {PAYLOAD_W{1'b0}};
      for (bit_i = 0; bit_i < PAYLOAD_W; bit_i = bit_i + 1) begin
        line_bit = (slice * PAYLOAD_W) + bit_i;
        if (line_bit < VALUE_W) begin
          expected_payload[bit_i] = line[line_bit];
        end
      end
    end
  endfunction

  task automatic check_response;
    input integer src;
    input [PACKET_W-1:0] packet;
    integer req_i;
    begin
      for (req_i = 0; req_i < received_count[src]; req_i = req_i + 1) begin
        if (seen_tag[src][req_i] == packet_tag(packet)) begin
          $display("ERROR: duplicate response source=%0d tag=%0h", src, packet_tag(packet));
          $finish(1);
        end
      end
      if (packet_payload(packet) !== expected_payload(packet_addr(packet), packet_slice(packet))) begin
        $display("ERROR: payload mismatch source=%0d tag=%0h addr=%0h slice=%0d",
                 src, packet_tag(packet), packet_addr(packet), packet_slice(packet));
        $finish(1);
      end
      seen_tag[src][received_count[src]] = packet_tag(packet);
      received_count[src] = received_count[src] + 1;
      total_received = total_received + 1;
    end
  endtask

  always @(*) begin
    src_req_valid = {SOURCES{1'b0}};
    src_req_packet = {(SOURCES * PACKET_W){1'b0}};
    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      if (sent_count[src_i] < expected_count[src_i]) begin
        src_req_valid[src_i] = 1'b1;
        src_req_packet[(src_i * PACKET_W) +: PACKET_W] = source_packets[src_i][sent_count[src_i]];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle_count <= 0;
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        sent_count[src_i] <= 0;
      end
    end else begin
      cycle_count <= cycle_count + 1;
      if (cycle_count < 24) begin
        src_resp_ready <= {SOURCES{1'b0}};
      end else begin
        src_resp_ready[0] <= 1'b1;
        src_resp_ready[1] <= 1'b1;
        src_resp_ready[2] <= (cycle_count[1] == 1'b0);
        src_resp_ready[3] <= 1'b1;
      end
      for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
        if (src_req_valid[src_i] && src_req_ready[src_i]) begin
          sent_count[src_i] <= sent_count[src_i] + 1;
        end
        if (src_resp_valid[src_i] && src_resp_ready[src_i]) begin
          check_response(src_i, src_resp_packet[(src_i * PACKET_W) +: PACKET_W]);
        end
      end
    end
  end

  initial begin
    rst_n = 1'b0;
    src_resp_ready = {SOURCES{1'b0}};
    cycle_count = 0;
    total_expected = 12;
    total_received = 0;

    source_packets[0][0] = pack_packet(0, 8'h10, 12'd0, 0);
    source_packets[0][1] = pack_packet(0, 8'h11, 12'd2, 1);
    source_packets[0][2] = pack_packet(0, 8'h12, 12'd4, 2);
    source_packets[1][0] = pack_packet(1, 8'h20, 12'd0, 1);
    source_packets[1][1] = pack_packet(1, 8'h21, 12'd2, 2);
    source_packets[1][2] = pack_packet(1, 8'h22, 12'd4, 3);
    source_packets[2][0] = pack_packet(2, 8'h30, 12'd1, 0);
    source_packets[2][1] = pack_packet(2, 8'h31, 12'd3, 1);
    source_packets[2][2] = pack_packet(2, 8'h32, 12'd5, 2);
    source_packets[3][0] = pack_packet(3, 8'h40, 12'd1, 3);
    source_packets[3][1] = pack_packet(3, 8'h41, 12'd3, 0);
    source_packets[3][2] = pack_packet(3, 8'h42, 12'd5, 1);

    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      expected_count[src_i] = 3;
      sent_count[src_i] = 0;
      received_count[src_i] = 0;
      for (slot_i = 0; slot_i < 8; slot_i = slot_i + 1) begin
        seen_tag[src_i][slot_i] = -1;
      end
    end

    #(CLK_PERIOD * 4);
    rst_n = 1'b1;
    wait (total_received == total_expected);
    repeat (4) @(posedge clk);

    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      if (received_count[src_i] != expected_count[src_i]) begin
        $display("ERROR: missing responses source=%0d got=%0d expected=%0d",
                 src_i, received_count[src_i], expected_count[src_i]);
        $finish(1);
      end
    end
    if (service_accepted_req_count != total_expected || service_emitted_resp_count != total_expected) begin
      $display("ERROR: service count mismatch req=%0d resp=%0d expected=%0d",
               service_accepted_req_count, service_emitted_resp_count, total_expected);
      $finish(1);
    end
    if (service_bank_conflict_count == 0) begin
      $display("ERROR: expected bank conflict counter activity");
      $finish(1);
    end
    if (router_injection_stall_cycles == 0 || router_arbitration_contention_cycles == 0) begin
      $display("ERROR: expected router counters to move stall=%0d contention=%0d",
               router_injection_stall_cycles, router_arbitration_contention_cycles);
      $finish(1);
    end
    if (router_response_block_cycles == 0 || service_response_block_cycles == 0) begin
      $display("ERROR: expected response blocking counters router=%0d service=%0d",
               router_response_block_cycles, service_response_block_cycles);
      $finish(1);
    end
    if (router_req_max_occupancy == 0 || router_resp_max_occupancy == 0 ||
        service_req_max_occupancy == 0 || service_resp_max_occupancy == 0) begin
      $display("ERROR: expected occupancy counters to rise");
      $finish(1);
    end

    $display("PASS: tb_banked_value_memory_service packet_w=%0d", PACKET_W);
    $finish(0);
  end

  initial begin
    repeat (800) @(posedge clk);
    $display("ERROR: tb_banked_value_memory_service timeout");
    $finish(1);
  end
endmodule
