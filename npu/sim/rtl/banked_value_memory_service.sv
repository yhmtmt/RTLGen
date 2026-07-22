`timescale 1ns/1ps

// Banked value-memory service. Requests are keyed by address and semantic
// value_slice. Responses preserve the request metadata and return a segmented
// 512-bit matrix with fragment index/last sideband.
module banked_value_memory_service #(
  parameter integer PACKET_W = 128,
  parameter integer VALUE_W = 512,
  parameter integer FRAG_IDX_W = ((VALUE_W / PACKET_W) <= 1) ? 1 : $clog2(VALUE_W / PACKET_W),
  parameter integer SOURCE_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 12,
  parameter integer VALUE_SLICE_W = 4,
  parameter integer STORE_DEPTH = 16,
  parameter integer BANKS = 4,
  parameter integer BANK_QUEUE_DEPTH = 2,
  parameter integer READ_LATENCY = 2,
  parameter integer COUNTER_W = 32,
  parameter integer INIT_FROM_GENERATOR = 0
) (
  input wire clk,
  input wire rst_n,

  input wire preload_valid,
  output wire preload_ready,
  input wire [ADDR_W-1:0] preload_addr,
  input wire [VALUE_SLICE_W-1:0] preload_value_slice,
  input wire [VALUE_W-1:0] preload_matrix,

  input wire req_valid,
  output wire req_ready,
  input wire [SOURCE_W-1:0] req_source,
  input wire [TAG_W-1:0] req_tag,
  input wire [ADDR_W-1:0] req_addr,
  input wire [VALUE_SLICE_W-1:0] req_value_slice,

  output wire resp_valid,
  input wire resp_ready,
  output wire [SOURCE_W-1:0] resp_source,
  output wire [TAG_W-1:0] resp_tag,
  output wire [ADDR_W-1:0] resp_addr,
  output wire [VALUE_SLICE_W-1:0] resp_value_slice,
  output wire [FRAG_IDX_W-1:0] resp_fragment_idx,
  output wire resp_last,
  output wire [PACKET_W-1:0] resp_data,

  output reg [COUNTER_W-1:0] accepted_req_count,
  output reg [COUNTER_W-1:0] emitted_resp_count,
  output reg [COUNTER_W-1:0] bank_conflict_count,
  output reg [COUNTER_W-1:0] response_block_cycles,
  output wire [COUNTER_W-1:0] req_current_occupancy,
  output reg [COUNTER_W-1:0] req_max_occupancy,
  output wire [COUNTER_W-1:0] resp_current_occupancy,
  output reg [COUNTER_W-1:0] resp_max_occupancy
);
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;
  localparam integer VALUE_SLICE_COUNT = (1 << VALUE_SLICE_W);
  localparam integer STORE_ENTRY_COUNT = STORE_DEPTH * VALUE_SLICE_COUNT;
  localparam integer BANK_SEL_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer BANK_PTR_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer BANK_COUNT_W = (BANK_QUEUE_DEPTH <= 1) ? 1 : $clog2(BANK_QUEUE_DEPTH + 1);
  localparam integer LAT_W = (READ_LATENCY <= 1) ? 1 : $clog2(READ_LATENCY + 1);
  localparam integer REQ_META_W = SOURCE_W + TAG_W + ADDR_W + VALUE_SLICE_W;
  localparam integer REQ_OCC_W = $clog2((BANKS * (BANK_QUEUE_DEPTH + 1)) + BANKS + 1);
  localparam integer RESP_OCC_W = $clog2(BANKS + 1);
  localparam integer REQ_SRC_LSB = 0;
  localparam integer REQ_TAG_LSB = REQ_SRC_LSB + SOURCE_W;
  localparam integer REQ_ADDR_LSB = REQ_TAG_LSB + TAG_W;
  localparam integer REQ_SLICE_LSB = REQ_ADDR_LSB + ADDR_W;

  wire [BANKS-1:0] bank_fifo_in_valid;
  wire [BANKS-1:0] bank_fifo_in_ready;
  wire [BANKS-1:0] bank_fifo_out_valid;
  wire [BANKS-1:0] bank_fifo_out_ready;
  wire [BANKS-1:0] bank_launch_fire;
  wire [BANKS*REQ_META_W-1:0] bank_fifo_out_bus;
  wire [BANKS*BANK_COUNT_W-1:0] bank_fifo_occupancy_bus;

  reg [BANKS-1:0] bank_busy;
  reg [SOURCE_W-1:0] active_source [0:BANKS-1];
  reg [TAG_W-1:0] active_tag [0:BANKS-1];
  reg [ADDR_W-1:0] active_addr [0:BANKS-1];
  reg [VALUE_SLICE_W-1:0] active_slice [0:BANKS-1];
  reg [VALUE_W-1:0] active_matrix [0:BANKS-1];
  reg [FRAG_IDX_W-1:0] active_fragment [0:BANKS-1];
  reg [LAT_W-1:0] bank_latency [0:BANKS-1];
  reg [BANKS-1:0] bank_ready_fragment_r;
  reg [BANK_PTR_W-1:0] resp_rr_cursor;
  reg [BANK_PTR_W-1:0] resp_grant_bank_r;
  reg any_ready_response_r;
  reg [REQ_OCC_W-1:0] req_occupancy_sum_r;
  reg [RESP_OCC_W-1:0] resp_occupancy_sum_r;

  reg [VALUE_W-1:0] value_mem [0:STORE_ENTRY_COUNT-1];

  integer occ_bank_i;
  integer seq_bank_i;
  integer scan_i;
  integer scan_bank_int;
  integer init_addr;
  integer init_slice;
  reg [BANK_PTR_W-1:0] scan_bank;

  function [REQ_META_W-1:0] pack_req;
    input [SOURCE_W-1:0] source;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    begin
      pack_req = {REQ_META_W{1'b0}};
      pack_req[REQ_SRC_LSB +: SOURCE_W] = source;
      pack_req[REQ_TAG_LSB +: TAG_W] = tag;
      pack_req[REQ_ADDR_LSB +: ADDR_W] = addr;
      pack_req[REQ_SLICE_LSB +: VALUE_SLICE_W] = value_slice;
    end
  endfunction

  function [SOURCE_W-1:0] meta_source;
    input [REQ_META_W-1:0] meta;
    begin
      meta_source = meta[REQ_SRC_LSB +: SOURCE_W];
    end
  endfunction

  function [TAG_W-1:0] meta_tag;
    input [REQ_META_W-1:0] meta;
    begin
      meta_tag = meta[REQ_TAG_LSB +: TAG_W];
    end
  endfunction

  function [ADDR_W-1:0] meta_addr;
    input [REQ_META_W-1:0] meta;
    begin
      meta_addr = meta[REQ_ADDR_LSB +: ADDR_W];
    end
  endfunction

  function [VALUE_SLICE_W-1:0] meta_slice;
    input [REQ_META_W-1:0] meta;
    begin
      meta_slice = meta[REQ_SLICE_LSB +: VALUE_SLICE_W];
    end
  endfunction

  function [BANK_SEL_W-1:0] bank_from_addr;
    input [ADDR_W-1:0] addr;
    integer bank_int;
    begin
      bank_int = addr % BANKS;
      bank_from_addr = bank_int[BANK_SEL_W-1:0];
    end
  endfunction

  function integer store_index;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    begin
      store_index = (addr * VALUE_SLICE_COUNT) + value_slice;
    end
  endfunction

  function [VALUE_W-1:0] generated_matrix;
    input integer addr;
    input integer value_slice;
    integer word_i;
    reg [63:0] word_value;
    begin
      generated_matrix = {VALUE_W{1'b0}};
      for (word_i = 0; word_i < (VALUE_W / 64); word_i = word_i + 1) begin
        word_value = {8'hd0 + value_slice[7:0], 8'h40 + word_i[7:0],
                      addr[15:0], value_slice[15:0], word_i[15:0]};
        generated_matrix[(word_i * 64) +: 64] = word_value;
      end
    end
  endfunction

  wire preload_fire = preload_valid && preload_ready;
  wire req_fire = req_valid && req_ready;
  wire resp_fire = resp_valid && resp_ready;

  assign preload_ready = 1'b1;
  assign req_ready = bank_fifo_in_ready[bank_from_addr(req_addr)];
  assign resp_valid = any_ready_response_r;
  assign resp_source = active_source[resp_grant_bank_r];
  assign resp_tag = active_tag[resp_grant_bank_r];
  assign resp_addr = active_addr[resp_grant_bank_r];
  assign resp_value_slice = active_slice[resp_grant_bank_r];
  assign resp_fragment_idx = active_fragment[resp_grant_bank_r];
  assign resp_last = any_ready_response_r &&
                     (active_fragment[resp_grant_bank_r] == (FRAGMENTS - 1));
  assign resp_data = any_ready_response_r ?
    active_matrix[resp_grant_bank_r][(active_fragment[resp_grant_bank_r] * PACKET_W) +: PACKET_W] :
    {PACKET_W{1'b0}};
  assign req_current_occupancy = {{(COUNTER_W-REQ_OCC_W){1'b0}}, req_occupancy_sum_r};
  assign resp_current_occupancy = {{(COUNTER_W-RESP_OCC_W){1'b0}}, resp_occupancy_sum_r};

  genvar bank_gi;
  generate
    for (bank_gi = 0; bank_gi < BANKS; bank_gi = bank_gi + 1) begin : gen_bank_fifo
      noc_ready_valid_fifo #(
        .WIDTH(REQ_META_W),
        .DEPTH(BANK_QUEUE_DEPTH)
      ) u_bank_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(bank_fifo_in_valid[bank_gi]),
        .in_ready(bank_fifo_in_ready[bank_gi]),
        .in_data(pack_req(req_source, req_tag, req_addr, req_value_slice)),
        .out_valid(bank_fifo_out_valid[bank_gi]),
        .out_ready(bank_fifo_out_ready[bank_gi]),
        .out_data(bank_fifo_out_bus[(bank_gi * REQ_META_W) +: REQ_META_W]),
        .occupancy(bank_fifo_occupancy_bus[(bank_gi * BANK_COUNT_W) +: BANK_COUNT_W]),
        .max_occupancy()
      );

      assign bank_fifo_in_valid[bank_gi] =
        req_valid && (bank_from_addr(req_addr) == bank_gi[BANK_SEL_W-1:0]);
      assign bank_fifo_out_ready[bank_gi] = !bank_busy[bank_gi] && bank_fifo_out_valid[bank_gi];
      assign bank_launch_fire[bank_gi] = bank_fifo_out_valid[bank_gi] && bank_fifo_out_ready[bank_gi];
    end
  endgenerate

  always @(*) begin
    req_occupancy_sum_r = {REQ_OCC_W{1'b0}};
    resp_occupancy_sum_r = {RESP_OCC_W{1'b0}};
    for (occ_bank_i = 0; occ_bank_i < BANKS; occ_bank_i = occ_bank_i + 1) begin
      req_occupancy_sum_r = req_occupancy_sum_r +
        bank_fifo_occupancy_bus[(occ_bank_i * BANK_COUNT_W) +: BANK_COUNT_W];
      if (bank_busy[occ_bank_i]) begin
        req_occupancy_sum_r = req_occupancy_sum_r + {{(REQ_OCC_W-1){1'b0}}, 1'b1};
      end
      bank_ready_fragment_r[occ_bank_i] =
        bank_busy[occ_bank_i] && (bank_latency[occ_bank_i] == {LAT_W{1'b0}});
      if (bank_ready_fragment_r[occ_bank_i]) begin
        resp_occupancy_sum_r = resp_occupancy_sum_r + {{(RESP_OCC_W-1){1'b0}}, 1'b1};
      end
    end

    any_ready_response_r = 1'b0;
    resp_grant_bank_r = resp_rr_cursor;
    for (scan_i = 0; scan_i < BANKS; scan_i = scan_i + 1) begin
      scan_bank_int = resp_rr_cursor + scan_i;
      if (scan_bank_int >= BANKS) begin
        scan_bank_int = scan_bank_int - BANKS;
      end
      scan_bank = scan_bank_int[BANK_PTR_W-1:0];
      if (!any_ready_response_r && bank_ready_fragment_r[scan_bank]) begin
        any_ready_response_r = 1'b1;
        resp_grant_bank_r = scan_bank;
      end
    end
  end

  integer init_i;
  initial begin
    if ((PACKET_W != 128) && (PACKET_W != 256)) begin
      $error("banked_value_memory_service PACKET_W must be 128 or 256, got %0d", PACKET_W);
      $finish(1);
    end
    if (VALUE_W != 512) begin
      $error("banked_value_memory_service VALUE_W must be 512, got %0d", VALUE_W);
      $finish(1);
    end
    if ((VALUE_W % PACKET_W) != 0) begin
      $error("banked_value_memory_service VALUE_W must be an integer multiple of PACKET_W");
      $finish(1);
    end
    if (VALUE_SLICE_W != 4) begin
      $error("banked_value_memory_service VALUE_SLICE_W must be 4, got %0d", VALUE_SLICE_W);
      $finish(1);
    end
    if ((1 << FRAG_IDX_W) < FRAGMENTS) begin
      $error("banked_value_memory_service FRAG_IDX_W is too small for %0d fragments", FRAGMENTS);
      $finish(1);
    end
    if ((STORE_DEPTH <= 0) || (BANKS <= 0)) begin
      $error("banked_value_memory_service STORE_DEPTH and BANKS must be positive");
      $finish(1);
    end
    if (STORE_DEPTH > (1 << ADDR_W)) begin
      $error("banked_value_memory_service STORE_DEPTH exceeds ADDR_W encoding");
      $finish(1);
    end
    for (init_i = 0; init_i < STORE_ENTRY_COUNT; init_i = init_i + 1) begin
      if (INIT_FROM_GENERATOR != 0) begin
        init_addr = init_i / VALUE_SLICE_COUNT;
        init_slice = init_i % VALUE_SLICE_COUNT;
        value_mem[init_i] = generated_matrix(init_addr, init_slice);
      end else begin
        value_mem[init_i] = {VALUE_W{1'b0}};
      end
    end
  end

  integer preload_idx;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      bank_busy <= {BANKS{1'b0}};
      for (seq_bank_i = 0; seq_bank_i < BANKS; seq_bank_i = seq_bank_i + 1) begin
        active_source[seq_bank_i] <= {SOURCE_W{1'b0}};
        active_tag[seq_bank_i] <= {TAG_W{1'b0}};
        active_addr[seq_bank_i] <= {ADDR_W{1'b0}};
        active_slice[seq_bank_i] <= {VALUE_SLICE_W{1'b0}};
        active_matrix[seq_bank_i] <= {VALUE_W{1'b0}};
        active_fragment[seq_bank_i] <= {FRAG_IDX_W{1'b0}};
        bank_latency[seq_bank_i] <= {LAT_W{1'b0}};
      end
      resp_rr_cursor <= {BANK_PTR_W{1'b0}};
      accepted_req_count <= {COUNTER_W{1'b0}};
      emitted_resp_count <= {COUNTER_W{1'b0}};
      bank_conflict_count <= {COUNTER_W{1'b0}};
      response_block_cycles <= {COUNTER_W{1'b0}};
      req_max_occupancy <= {COUNTER_W{1'b0}};
      resp_max_occupancy <= {COUNTER_W{1'b0}};
    end else begin
      if (preload_fire && (preload_addr < STORE_DEPTH[ADDR_W-1:0])) begin
        preload_idx = store_index(preload_addr, preload_value_slice);
        value_mem[preload_idx] <= preload_matrix;
      end

      if (req_fire) begin
        accepted_req_count <= accepted_req_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        if (bank_busy[bank_from_addr(req_addr)] ||
            (bank_fifo_occupancy_bus[(bank_from_addr(req_addr) * BANK_COUNT_W) +: BANK_COUNT_W] != {BANK_COUNT_W{1'b0}})) begin
          bank_conflict_count <= bank_conflict_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        end
      end

      for (seq_bank_i = 0; seq_bank_i < BANKS; seq_bank_i = seq_bank_i + 1) begin
        if (bank_launch_fire[seq_bank_i]) begin
          bank_busy[seq_bank_i] <= 1'b1;
          active_source[seq_bank_i] <=
            meta_source(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]);
          active_tag[seq_bank_i] <=
            meta_tag(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]);
          active_addr[seq_bank_i] <=
            meta_addr(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]);
          active_slice[seq_bank_i] <=
            meta_slice(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]);
          active_fragment[seq_bank_i] <= {FRAG_IDX_W{1'b0}};
          if (READ_LATENCY == 0) begin
            bank_latency[seq_bank_i] <= {LAT_W{1'b0}};
          end else begin
            bank_latency[seq_bank_i] <= READ_LATENCY[LAT_W-1:0];
          end
          if (meta_addr(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]) <
              STORE_DEPTH[ADDR_W-1:0]) begin
            active_matrix[seq_bank_i] <=
              value_mem[store_index(
                meta_addr(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]),
                meta_slice(bank_fifo_out_bus[(seq_bank_i * REQ_META_W) +: REQ_META_W]))];
          end else begin
            active_matrix[seq_bank_i] <= {VALUE_W{1'b0}};
          end
        end else if (bank_busy[seq_bank_i] && (bank_latency[seq_bank_i] != {LAT_W{1'b0}})) begin
          bank_latency[seq_bank_i] <=
            bank_latency[seq_bank_i] - {{(LAT_W-1){1'b0}}, 1'b1};
        end
      end

      if (resp_valid && !resp_ready) begin
        response_block_cycles <= response_block_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (resp_fire) begin
        if (resp_last) begin
          bank_busy[resp_grant_bank_r] <= 1'b0;
          active_fragment[resp_grant_bank_r] <= {FRAG_IDX_W{1'b0}};
          emitted_resp_count <= emitted_resp_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        end else begin
          active_fragment[resp_grant_bank_r] <=
            active_fragment[resp_grant_bank_r] + {{(FRAG_IDX_W-1){1'b0}}, 1'b1};
        end
        if (resp_grant_bank_r == (BANKS - 1)) begin
          resp_rr_cursor <= {BANK_PTR_W{1'b0}};
        end else begin
          resp_rr_cursor <= resp_grant_bank_r + {{(BANK_PTR_W-1){1'b0}}, 1'b1};
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
