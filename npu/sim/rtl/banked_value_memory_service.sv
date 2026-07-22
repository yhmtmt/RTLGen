`timescale 1ns/1ps

// Banked read-only value-memory service with per-bank request queues,
// configurable read latency, and sliced 512-bit responses over a narrower
// packet transport.
module banked_value_memory_service #(
  parameter integer PACKET_W = 128,
  parameter integer SOURCE_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 12,
  parameter integer SLICE_W = 3,
  parameter integer VALUE_W = 512,
  parameter integer BANKS = 4,
  parameter integer BANK_QUEUE_DEPTH = 2,
  parameter integer RESP_QUEUE_DEPTH = 2,
  parameter integer READ_LATENCY = 2,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,

  input wire req_valid,
  output wire req_ready,
  input wire [PACKET_W-1:0] req_packet,

  output wire resp_valid,
  input wire resp_ready,
  output wire [PACKET_W-1:0] resp_packet,

  output reg [COUNTER_W-1:0] accepted_req_count,
  output reg [COUNTER_W-1:0] emitted_resp_count,
  output reg [COUNTER_W-1:0] bank_conflict_count,
  output reg [COUNTER_W-1:0] response_block_cycles,
  output wire [COUNTER_W-1:0] req_current_occupancy,
  output reg [COUNTER_W-1:0] req_max_occupancy,
  output wire [COUNTER_W-1:0] resp_current_occupancy,
  output reg [COUNTER_W-1:0] resp_max_occupancy
);
  localparam integer BANK_SEL_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer BANK_PTR_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer BANK_COUNT_W = (BANK_QUEUE_DEPTH <= 1) ? 1 : $clog2(BANK_QUEUE_DEPTH + 1);
  localparam integer RESP_COUNT_W = (RESP_QUEUE_DEPTH <= 1) ? 1 : $clog2(RESP_QUEUE_DEPTH + 1);
  localparam integer LAT_W = (READ_LATENCY <= 1) ? 1 : $clog2(READ_LATENCY);
  localparam integer SRC_LSB = 0;
  localparam integer TAG_LSB = SRC_LSB + SOURCE_W;
  localparam integer ADDR_LSB = TAG_LSB + TAG_W;
  localparam integer SLICE_LSB = ADDR_LSB + ADDR_W;
  localparam integer PAYLOAD_LSB = SLICE_LSB + SLICE_W;
  localparam integer PAYLOAD_W = PACKET_W - PAYLOAD_LSB;
  localparam integer REQ_OCC_W = $clog2((BANKS * (BANK_QUEUE_DEPTH + 1)) + BANKS + 1);

  wire [BANKS-1:0] bank_fifo_in_ready;
  wire [BANKS-1:0] bank_fifo_in_valid;
  wire [BANKS-1:0] bank_fifo_out_valid;
  wire [BANKS-1:0] bank_fifo_out_ready;
  wire [PACKET_W-1:0] bank_fifo_out_packet [0:BANKS-1];
  wire [BANK_COUNT_W-1:0] bank_fifo_occupancy [0:BANKS-1];
  wire [PACKET_W-1:0] resp_fifo_out_packet;
  wire [RESP_COUNT_W-1:0] resp_fifo_occupancy;
  wire resp_fifo_in_ready;
  wire resp_fifo_out_valid;

  reg [PACKET_W-1:0] active_packet [0:BANKS-1];
  reg [BANKS-1:0] bank_active;
  reg [LAT_W-1:0] bank_latency_left [0:BANKS-1];
  reg [BANKS-1:0] bank_launch;
  reg [BANKS-1:0] bank_resp_ready_mask;
  reg resp_fifo_in_valid;
  reg [PACKET_W-1:0] resp_fifo_in_packet;
  reg [BANK_PTR_W-1:0] resp_rr_cursor;
  reg [BANK_PTR_W-1:0] resp_grant_bank;
  reg any_ready_response;
  reg [BANK_SEL_W-1:0] target_bank;
  reg bank_conflicted;
  reg [REQ_OCC_W-1:0] req_occupancy_sum;

  integer bank_i;
  integer scan_i;
  integer scan_bank_int;
  reg [BANK_PTR_W-1:0] scan_bank;

  function [SOURCE_W-1:0] packet_source;
    input [PACKET_W-1:0] packet;
    begin
      packet_source = packet[SRC_LSB +: SOURCE_W];
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

  function [BANK_SEL_W-1:0] packet_bank;
    input [PACKET_W-1:0] packet;
    integer bank_int;
    begin
      bank_int = packet_addr(packet) % BANKS;
      packet_bank = bank_int[BANK_SEL_W-1:0];
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

  function [PAYLOAD_W-1:0] extract_slice;
    input [VALUE_W-1:0] line;
    input [SLICE_W-1:0] slice;
    integer bit_i;
    integer line_bit;
    begin
      extract_slice = {PAYLOAD_W{1'b0}};
      for (bit_i = 0; bit_i < PAYLOAD_W; bit_i = bit_i + 1) begin
        line_bit = (slice * PAYLOAD_W) + bit_i;
        if (line_bit < VALUE_W) begin
          extract_slice[bit_i] = line[line_bit];
        end
      end
    end
  endfunction

  function [PACKET_W-1:0] build_response_packet;
    input [PACKET_W-1:0] request_packet;
    reg [VALUE_W-1:0] line;
    reg [PAYLOAD_W-1:0] payload;
    begin
      line = make_value_line(packet_addr(request_packet));
      payload = extract_slice(line, packet_slice(request_packet));
      build_response_packet = request_packet;
      build_response_packet[PAYLOAD_LSB +: PAYLOAD_W] = payload;
    end
  endfunction

  genvar bank_gi;
  generate
    for (bank_gi = 0; bank_gi < BANKS; bank_gi = bank_gi + 1) begin : gen_bank_fifo
      noc_ready_valid_fifo #(
        .WIDTH(PACKET_W),
        .DEPTH(BANK_QUEUE_DEPTH)
      ) u_bank_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(bank_fifo_in_valid[bank_gi]),
        .in_ready(bank_fifo_in_ready[bank_gi]),
        .in_data(req_packet),
        .out_valid(bank_fifo_out_valid[bank_gi]),
        .out_ready(bank_launch[bank_gi]),
        .out_data(bank_fifo_out_packet[bank_gi]),
        .occupancy(bank_fifo_occupancy[bank_gi]),
        .max_occupancy()
      );
      assign bank_fifo_out_ready[bank_gi] = bank_launch[bank_gi];
    end
  endgenerate

  noc_ready_valid_fifo #(
    .WIDTH(PACKET_W),
    .DEPTH(RESP_QUEUE_DEPTH)
  ) u_resp_fifo (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(resp_fifo_in_valid),
    .in_ready(resp_fifo_in_ready),
    .in_data(resp_fifo_in_packet),
    .out_valid(resp_fifo_out_valid),
    .out_ready(resp_ready),
    .out_data(resp_fifo_out_packet),
    .occupancy(resp_fifo_occupancy),
    .max_occupancy()
  );

  assign resp_valid = resp_fifo_out_valid;
  assign resp_packet = resp_fifo_out_packet;
  assign resp_current_occupancy = {{(COUNTER_W-RESP_COUNT_W){1'b0}}, resp_fifo_occupancy};

  always @(*) begin
    target_bank = packet_bank(req_packet);
  end

  assign req_ready = bank_fifo_in_ready[target_bank];

  generate
    for (bank_gi = 0; bank_gi < BANKS; bank_gi = bank_gi + 1) begin : gen_bank_inputs
      assign bank_fifo_in_valid[bank_gi] = req_valid && (target_bank == bank_gi[BANK_SEL_W-1:0]);
    end
  endgenerate

  always @(*) begin
    bank_conflicted = 1'b0;
    if (req_valid && req_ready) begin
      if (bank_active[target_bank] || (bank_fifo_occupancy[target_bank] != {BANK_COUNT_W{1'b0}})) begin
        bank_conflicted = 1'b1;
      end
    end
  end

  always @(*) begin
    req_occupancy_sum = {REQ_OCC_W{1'b0}};
    for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
      req_occupancy_sum = req_occupancy_sum + bank_fifo_occupancy[bank_i];
      if (bank_active[bank_i]) begin
        req_occupancy_sum = req_occupancy_sum + {{(REQ_OCC_W-1){1'b0}}, 1'b1};
      end
    end
  end

  assign req_current_occupancy = {{(COUNTER_W-REQ_OCC_W){1'b0}}, req_occupancy_sum};

  always @(*) begin
    for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
      bank_launch[bank_i] = !bank_active[bank_i] && bank_fifo_out_valid[bank_i];
      bank_resp_ready_mask[bank_i] = bank_active[bank_i] && (bank_latency_left[bank_i] == {LAT_W{1'b0}});
    end

    any_ready_response = 1'b0;
    resp_grant_bank = resp_rr_cursor;
    for (scan_i = 0; scan_i < BANKS; scan_i = scan_i + 1) begin
      scan_bank_int = resp_rr_cursor + scan_i;
      if (scan_bank_int >= BANKS) begin
        scan_bank_int = scan_bank_int - BANKS;
      end
      scan_bank = scan_bank_int[BANK_PTR_W-1:0];
      if (!any_ready_response && bank_resp_ready_mask[scan_bank]) begin
        any_ready_response = 1'b1;
        resp_grant_bank = scan_bank;
      end
    end

    resp_fifo_in_valid = any_ready_response && resp_fifo_in_ready;
    resp_fifo_in_packet = any_ready_response ? build_response_packet(active_packet[resp_grant_bank]) : {PACKET_W{1'b0}};
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      bank_active <= {BANKS{1'b0}};
      resp_rr_cursor <= {BANK_PTR_W{1'b0}};
      accepted_req_count <= {COUNTER_W{1'b0}};
      emitted_resp_count <= {COUNTER_W{1'b0}};
      bank_conflict_count <= {COUNTER_W{1'b0}};
      response_block_cycles <= {COUNTER_W{1'b0}};
      req_max_occupancy <= {COUNTER_W{1'b0}};
      resp_max_occupancy <= {COUNTER_W{1'b0}};
      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        active_packet[bank_i] <= {PACKET_W{1'b0}};
        bank_latency_left[bank_i] <= {LAT_W{1'b0}};
      end
    end else begin
      if (req_valid && req_ready) begin
        accepted_req_count <= accepted_req_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        if (bank_conflicted) begin
          bank_conflict_count <= bank_conflict_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        end
      end

      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        if (bank_launch[bank_i]) begin
          bank_active[bank_i] <= 1'b1;
          active_packet[bank_i] <= bank_fifo_out_packet[bank_i];
          if (READ_LATENCY <= 1) begin
            bank_latency_left[bank_i] <= {LAT_W{1'b0}};
          end else begin
            bank_latency_left[bank_i] <= READ_LATENCY - 1;
          end
        end else if (bank_active[bank_i] && (bank_latency_left[bank_i] != {LAT_W{1'b0}})) begin
          bank_latency_left[bank_i] <= bank_latency_left[bank_i] - {{(LAT_W-1){1'b0}}, 1'b1};
        end
      end

      if (any_ready_response && !resp_fifo_in_ready) begin
        response_block_cycles <= response_block_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (resp_fifo_in_valid) begin
        bank_active[resp_grant_bank] <= 1'b0;
        if (resp_grant_bank == (BANKS - 1)) begin
          resp_rr_cursor <= {BANK_PTR_W{1'b0}};
        end else begin
          resp_rr_cursor <= resp_grant_bank + {{(BANK_PTR_W-1){1'b0}}, 1'b1};
        end
      end

      if (resp_valid && resp_ready) begin
        emitted_resp_count <= emitted_resp_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end

      if (req_current_occupancy > req_max_occupancy) begin
        req_max_occupancy <= req_current_occupancy;
      end
      if (resp_current_occupancy > resp_max_occupancy) begin
        resp_max_occupancy <= resp_current_occupancy;
      end
    end
  end
endmodule
