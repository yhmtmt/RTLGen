`timescale 1ns/1ps

// Multi-source ready/valid transport with request arbitration and response
// demultiplexing. The request path supports deterministic round-robin and
// locality-first selection based on the address-derived bank index.
module noc_ready_valid_router #(
  parameter integer PACKET_W = 128,
  parameter integer SOURCES = 4,
  parameter integer SOURCE_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 12,
  parameter integer SLICE_W = 3,
  parameter integer BANKS = 4,
  parameter integer REQ_QUEUE_DEPTH = 2,
  parameter integer RESP_QUEUE_DEPTH = 2,
  parameter integer ARB_MODE = 0,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,

  input wire [SOURCES-1:0] src_req_valid,
  output wire [SOURCES-1:0] src_req_ready,
  input wire [SOURCES*PACKET_W-1:0] src_req_packet,

  output wire [SOURCES-1:0] src_resp_valid,
  input wire [SOURCES-1:0] src_resp_ready,
  output wire [SOURCES*PACKET_W-1:0] src_resp_packet,

  output wire req_valid,
  input wire req_ready,
  output wire [PACKET_W-1:0] req_packet,

  input wire resp_valid,
  output wire resp_ready,
  input wire [PACKET_W-1:0] resp_packet,

  output reg [COUNTER_W-1:0] injection_stall_cycles,
  output reg [COUNTER_W-1:0] arbitration_contention_cycles,
  output reg [COUNTER_W-1:0] response_block_cycles,
  output wire [COUNTER_W-1:0] req_current_occupancy,
  output reg [COUNTER_W-1:0] req_max_occupancy,
  output wire [COUNTER_W-1:0] resp_current_occupancy,
  output reg [COUNTER_W-1:0] resp_max_occupancy
);
  localparam integer REQ_COUNT_W = (REQ_QUEUE_DEPTH <= 1) ? 1 : $clog2(REQ_QUEUE_DEPTH + 1);
  localparam integer RESP_COUNT_W = (RESP_QUEUE_DEPTH <= 1) ? 1 : $clog2(RESP_QUEUE_DEPTH + 1);
  localparam integer SOURCE_PTR_W = (SOURCES <= 1) ? 1 : $clog2(SOURCES);
  localparam integer BANK_SEL_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer SRC_LSB = 0;
  localparam integer TAG_LSB = SRC_LSB + SOURCE_W;
  localparam integer ADDR_LSB = TAG_LSB + TAG_W;
  localparam integer SLICE_LSB = ADDR_LSB + ADDR_W;
  localparam integer PAYLOAD_LSB = SLICE_LSB + SLICE_W;
  localparam integer REQ_OCC_W = $clog2((SOURCES * (REQ_QUEUE_DEPTH + 1)) + 1);
  localparam integer RESP_OCC_W = $clog2((SOURCES * (RESP_QUEUE_DEPTH + 1)) + 1);

  wire [SOURCES-1:0] req_fifo_out_valid;
  wire [SOURCES-1:0] src_req_ready_int;
  wire [SOURCES*PACKET_W-1:0] req_fifo_out_packet_bus;
  wire [SOURCES*REQ_COUNT_W-1:0] req_fifo_occupancy_bus;

  wire [SOURCES-1:0] resp_fifo_out_valid;
  wire [SOURCES-1:0] resp_fifo_in_valid;
  wire [SOURCES-1:0] resp_fifo_in_ready;
  wire [SOURCES*PACKET_W-1:0] resp_fifo_out_packet_bus;
  wire [SOURCES*RESP_COUNT_W-1:0] resp_fifo_occupancy_bus;

  reg [SOURCE_PTR_W-1:0] rr_cursor;
  reg [BANK_SEL_W-1:0] preferred_bank;

  reg grant_valid;
  reg [SOURCE_PTR_W-1:0] grant_idx;
  reg [PACKET_W-1:0] grant_packet;
  reg [SOURCES-1:0] req_fifo_out_ready_int;
  reg [SOURCE_PTR_W-1:0] resp_target_idx;
  reg resp_target_valid;
  reg any_injection_stall;
  reg arbitration_contended;
  reg [REQ_OCC_W-1:0] req_occupancy_sum;
  reg [RESP_OCC_W-1:0] resp_occupancy_sum;

  integer src_i;
  integer scan_i;
  integer scan_src_int;
  integer req_ready_count;
  integer resp_ready_count;
  reg [SOURCE_PTR_W-1:0] scan_src;
  reg locality_hit;
  reg fallback_hit;
  reg [SOURCE_PTR_W-1:0] locality_idx;
  reg [PACKET_W-1:0] locality_packet;
  reg [SOURCE_PTR_W-1:0] fallback_idx;
  reg [PACKET_W-1:0] fallback_packet;

  function [SOURCE_W-1:0] packet_source;
    input [PACKET_W-1:0] packet;
    begin
      packet_source = packet[SRC_LSB +: SOURCE_W];
    end
  endfunction

  function [ADDR_W-1:0] packet_addr;
    input [PACKET_W-1:0] packet;
    begin
      packet_addr = packet[ADDR_LSB +: ADDR_W];
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

  genvar req_gi;
  generate
    for (req_gi = 0; req_gi < SOURCES; req_gi = req_gi + 1) begin : gen_req_fifo
      noc_ready_valid_fifo #(
        .WIDTH(PACKET_W),
        .DEPTH(REQ_QUEUE_DEPTH)
      ) u_req_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(src_req_valid[req_gi]),
        .in_ready(src_req_ready_int[req_gi]),
        .in_data(src_req_packet[(req_gi * PACKET_W) +: PACKET_W]),
        .out_valid(req_fifo_out_valid[req_gi]),
        .out_ready(req_fifo_out_ready_int[req_gi]),
        .out_data(req_fifo_out_packet_bus[(req_gi * PACKET_W) +: PACKET_W]),
        .occupancy(req_fifo_occupancy_bus[(req_gi * REQ_COUNT_W) +: REQ_COUNT_W]),
        .max_occupancy()
      );
      assign src_req_ready[req_gi] = src_req_ready_int[req_gi];
    end
  endgenerate

  genvar resp_gi;
  generate
    for (resp_gi = 0; resp_gi < SOURCES; resp_gi = resp_gi + 1) begin : gen_resp_fifo
      noc_ready_valid_fifo #(
        .WIDTH(PACKET_W),
        .DEPTH(RESP_QUEUE_DEPTH)
      ) u_resp_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(resp_fifo_in_valid[resp_gi]),
        .in_ready(resp_fifo_in_ready[resp_gi]),
        .in_data(resp_packet),
        .out_valid(resp_fifo_out_valid[resp_gi]),
        .out_ready(src_resp_ready[resp_gi]),
        .out_data(resp_fifo_out_packet_bus[(resp_gi * PACKET_W) +: PACKET_W]),
        .occupancy(resp_fifo_occupancy_bus[(resp_gi * RESP_COUNT_W) +: RESP_COUNT_W]),
        .max_occupancy()
      );
      assign src_resp_valid[resp_gi] = resp_fifo_out_valid[resp_gi];
      assign src_resp_packet[(resp_gi * PACKET_W) +: PACKET_W] = resp_fifo_out_packet_bus[(resp_gi * PACKET_W) +: PACKET_W];
    end
  endgenerate

  always @(*) begin
    grant_valid = 1'b0;
    grant_idx = {SOURCE_PTR_W{1'b0}};
    grant_packet = {PACKET_W{1'b0}};
    locality_hit = 1'b0;
    fallback_hit = 1'b0;
    locality_idx = {SOURCE_PTR_W{1'b0}};
    locality_packet = {PACKET_W{1'b0}};
    fallback_idx = {SOURCE_PTR_W{1'b0}};
    fallback_packet = {PACKET_W{1'b0}};
    req_fifo_out_ready_int = {SOURCES{1'b0}};
    req_ready_count = 0;
    req_occupancy_sum = {REQ_OCC_W{1'b0}};
    any_injection_stall = 1'b0;

    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      req_occupancy_sum = req_occupancy_sum + req_fifo_occupancy_bus[(src_i * REQ_COUNT_W) +: REQ_COUNT_W];
      if (src_req_valid[src_i] && !src_req_ready_int[src_i]) begin
        any_injection_stall = 1'b0;
        any_injection_stall = 1'b1;
      end
      if (req_fifo_out_valid[src_i]) begin
        req_ready_count = req_ready_count + 1;
      end
    end

    for (scan_i = 0; scan_i < SOURCES; scan_i = scan_i + 1) begin
      scan_src_int = rr_cursor + scan_i;
      if (scan_src_int >= SOURCES) begin
        scan_src_int = scan_src_int - SOURCES;
      end
      scan_src = scan_src_int[SOURCE_PTR_W-1:0];
      if (!fallback_hit && req_fifo_out_valid[scan_src]) begin
        fallback_hit = 1'b1;
        fallback_idx = scan_src;
        fallback_packet = req_fifo_out_packet_bus[(scan_src * PACKET_W) +: PACKET_W];
      end
      if (!locality_hit && req_fifo_out_valid[scan_src] &&
          (packet_bank(req_fifo_out_packet_bus[(scan_src * PACKET_W) +: PACKET_W]) == preferred_bank)) begin
        locality_hit = 1'b1;
        locality_idx = scan_src;
        locality_packet = req_fifo_out_packet_bus[(scan_src * PACKET_W) +: PACKET_W];
      end
    end

    if (ARB_MODE != 0 && locality_hit) begin
      grant_valid = 1'b1;
      grant_idx = locality_idx;
      grant_packet = locality_packet;
    end else if (fallback_hit) begin
      grant_valid = 1'b1;
      grant_idx = fallback_idx;
      grant_packet = fallback_packet;
    end

    if (grant_valid && req_ready) begin
      req_fifo_out_ready_int[grant_idx] = 1'b1;
    end
  end

  assign req_valid = grant_valid;
  assign req_packet = grant_packet;
  assign req_current_occupancy = {{(COUNTER_W-REQ_OCC_W){1'b0}}, req_occupancy_sum};

  always @(*) begin
    resp_target_idx = {SOURCE_PTR_W{1'b0}};
    resp_target_valid = 1'b0;
    resp_ready_count = 0;
    resp_occupancy_sum = {RESP_OCC_W{1'b0}};

    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      resp_occupancy_sum = resp_occupancy_sum + resp_fifo_occupancy_bus[(src_i * RESP_COUNT_W) +: RESP_COUNT_W];
      if (resp_valid && (packet_source(resp_packet) == src_i[SOURCE_W-1:0])) begin
        resp_target_idx = src_i[SOURCE_PTR_W-1:0];
        resp_target_valid = 1'b1;
      end
      if (resp_fifo_out_valid[src_i]) begin
        resp_ready_count = resp_ready_count + 1;
      end
    end
  end

  generate
    for (resp_gi = 0; resp_gi < SOURCES; resp_gi = resp_gi + 1) begin : gen_resp_demux
      assign resp_fifo_in_valid[resp_gi] =
        resp_valid && resp_target_valid && (resp_target_idx == resp_gi[SOURCE_PTR_W-1:0]);
    end
  endgenerate

  assign resp_ready = resp_target_valid ? resp_fifo_in_ready[resp_target_idx] : 1'b0;
  assign resp_current_occupancy = {{(COUNTER_W-RESP_OCC_W){1'b0}}, resp_occupancy_sum};

  always @(*) begin
    arbitration_contended = (req_ready_count > 1);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rr_cursor <= {SOURCE_PTR_W{1'b0}};
      preferred_bank <= {BANK_SEL_W{1'b0}};
      injection_stall_cycles <= {COUNTER_W{1'b0}};
      arbitration_contention_cycles <= {COUNTER_W{1'b0}};
      response_block_cycles <= {COUNTER_W{1'b0}};
      req_max_occupancy <= {COUNTER_W{1'b0}};
      resp_max_occupancy <= {COUNTER_W{1'b0}};
    end else begin
      if (any_injection_stall) begin
        injection_stall_cycles <= injection_stall_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (grant_valid && arbitration_contended) begin
        arbitration_contention_cycles <= arbitration_contention_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (resp_valid && !resp_ready) begin
        response_block_cycles <= response_block_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (grant_valid && req_ready) begin
        preferred_bank <= packet_bank(grant_packet);
        if (grant_idx == (SOURCES - 1)) begin
          rr_cursor <= {SOURCE_PTR_W{1'b0}};
        end else begin
          rr_cursor <= grant_idx + {{(SOURCE_PTR_W-1){1'b0}}, 1'b1};
        end
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
