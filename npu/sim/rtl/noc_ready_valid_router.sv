`timescale 1ns/1ps

// Multi-source ready/valid transport for metadata requests and segmented
// matrix responses. Requests preserve source/tag/address/value_slice. The
// response path adds fragment index and last metadata for a segmented 512-bit
// matrix return.
module noc_ready_valid_router #(
  parameter integer PACKET_W = 128,
  parameter integer VALUE_W = 512,
  parameter integer FRAG_IDX_W = ((VALUE_W / PACKET_W) <= 1) ? 1 : $clog2(VALUE_W / PACKET_W),
  parameter integer SOURCES = 4,
  parameter integer SOURCE_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 12,
  parameter integer VALUE_SLICE_W = 4,
  parameter integer BANKS = 4,
  parameter integer REQ_QUEUE_DEPTH = 2,
  parameter integer RESP_QUEUE_DEPTH = 2,
  parameter integer ARB_MODE = 0,
  parameter integer LOCALITY_BURST_MAX = 2,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,

  input wire [SOURCES-1:0] src_req_valid,
  output wire [SOURCES-1:0] src_req_ready,
  input wire [SOURCES*SOURCE_W-1:0] src_req_source,
  input wire [SOURCES*TAG_W-1:0] src_req_tag,
  input wire [SOURCES*ADDR_W-1:0] src_req_addr,
  input wire [SOURCES*VALUE_SLICE_W-1:0] src_req_value_slice,

  output wire [SOURCES-1:0] src_resp_valid,
  input wire [SOURCES-1:0] src_resp_ready,
  output wire [SOURCES*SOURCE_W-1:0] src_resp_source,
  output wire [SOURCES*TAG_W-1:0] src_resp_tag,
  output wire [SOURCES*ADDR_W-1:0] src_resp_addr,
  output wire [SOURCES*VALUE_SLICE_W-1:0] src_resp_value_slice,
  output wire [SOURCES*FRAG_IDX_W-1:0] src_resp_fragment_idx,
  output wire [SOURCES-1:0] src_resp_last,
  output wire [SOURCES*PACKET_W-1:0] src_resp_data,

  output wire req_valid,
  input wire req_ready,
  output wire [SOURCE_W-1:0] req_source,
  output wire [TAG_W-1:0] req_tag,
  output wire [ADDR_W-1:0] req_addr,
  output wire [VALUE_SLICE_W-1:0] req_value_slice,

  input wire resp_valid,
  output wire resp_ready,
  input wire [SOURCE_W-1:0] resp_source,
  input wire [TAG_W-1:0] resp_tag,
  input wire [ADDR_W-1:0] resp_addr,
  input wire [VALUE_SLICE_W-1:0] resp_value_slice,
  input wire [FRAG_IDX_W-1:0] resp_fragment_idx,
  input wire resp_last,
  input wire [PACKET_W-1:0] resp_data,

  output reg [COUNTER_W-1:0] injection_stall_cycles,
  output reg [COUNTER_W-1:0] arbitration_contention_cycles,
  output reg [COUNTER_W-1:0] response_block_cycles,
  output wire [COUNTER_W-1:0] req_current_occupancy,
  output reg [COUNTER_W-1:0] req_max_occupancy,
  output wire [COUNTER_W-1:0] resp_current_occupancy,
  output reg [COUNTER_W-1:0] resp_max_occupancy
);
  localparam integer FRAGMENTS = VALUE_W / PACKET_W;
  localparam integer REQ_META_W = SOURCE_W + TAG_W + ADDR_W + VALUE_SLICE_W;
  localparam integer RESP_META_W = SOURCE_W + TAG_W + ADDR_W + VALUE_SLICE_W + FRAG_IDX_W + 1 + PACKET_W;
  localparam integer REQ_COUNT_W = (REQ_QUEUE_DEPTH <= 1) ? 1 : $clog2(REQ_QUEUE_DEPTH + 1);
  localparam integer RESP_COUNT_W = (RESP_QUEUE_DEPTH <= 1) ? 1 : $clog2(RESP_QUEUE_DEPTH + 1);
  localparam integer SOURCE_PTR_W = (SOURCES <= 1) ? 1 : $clog2(SOURCES);
  localparam integer BANK_SEL_W = (BANKS <= 1) ? 1 : $clog2(BANKS);
  localparam integer REQ_OCC_W = $clog2((SOURCES * (REQ_QUEUE_DEPTH + 1)) + 1);
  localparam integer RESP_OCC_W = $clog2((SOURCES * (RESP_QUEUE_DEPTH + 1)) + 1);
  localparam integer LOCALITY_BURST_W = (LOCALITY_BURST_MAX <= 1) ? 1 : $clog2(LOCALITY_BURST_MAX + 1);
  localparam integer REQ_SRC_LSB = 0;
  localparam integer REQ_TAG_LSB = REQ_SRC_LSB + SOURCE_W;
  localparam integer REQ_ADDR_LSB = REQ_TAG_LSB + TAG_W;
  localparam integer REQ_SLICE_LSB = REQ_ADDR_LSB + ADDR_W;
  localparam integer RESP_SRC_LSB = 0;
  localparam integer RESP_TAG_LSB = RESP_SRC_LSB + SOURCE_W;
  localparam integer RESP_ADDR_LSB = RESP_TAG_LSB + TAG_W;
  localparam integer RESP_SLICE_LSB = RESP_ADDR_LSB + ADDR_W;
  localparam integer RESP_FRAG_LSB = RESP_SLICE_LSB + VALUE_SLICE_W;
  localparam integer RESP_LAST_LSB = RESP_FRAG_LSB + FRAG_IDX_W;
  localparam integer RESP_DATA_LSB = RESP_LAST_LSB + 1;

  wire [SOURCES-1:0] req_fifo_out_valid;
  wire [SOURCES-1:0] req_fifo_out_ready;
  wire [SOURCES*REQ_META_W-1:0] req_fifo_out_bus;
  wire [SOURCES*REQ_COUNT_W-1:0] req_fifo_occupancy_bus;

  wire [SOURCES-1:0] resp_fifo_out_valid;
  wire [SOURCES*RESP_META_W-1:0] resp_fifo_out_bus;
  wire [SOURCES*RESP_COUNT_W-1:0] resp_fifo_occupancy_bus;
  wire [SOURCES-1:0] resp_fifo_in_valid;
  wire [SOURCES-1:0] resp_fifo_in_ready;
  wire [RESP_META_W-1:0] resp_bus;

  reg grant_valid_r;
  reg [SOURCE_PTR_W-1:0] grant_idx_r;
  reg [REQ_META_W-1:0] grant_req_r;
  reg [SOURCES-1:0] req_fifo_out_ready_r;
  reg [SOURCE_PTR_W-1:0] rr_cursor;
  reg [BANK_SEL_W-1:0] preferred_bank;
  reg [LOCALITY_BURST_W-1:0] locality_burst_count;
  reg [REQ_OCC_W-1:0] req_occupancy_sum_r;
  reg [RESP_OCC_W-1:0] resp_occupancy_sum_r;
  reg any_injection_stall_r;
  reg arbitration_contended_r;
  reg [SOURCE_PTR_W-1:0] resp_target_idx_r;
  reg resp_target_valid_r;

  integer src_i;
  integer scan_i;
  integer scan_src_int;
  integer req_ready_count;
  reg fallback_hit;
  reg locality_hit;
  reg alternate_hit;
  reg [SOURCE_PTR_W-1:0] fallback_idx;
  reg [SOURCE_PTR_W-1:0] locality_idx;
  reg [SOURCE_PTR_W-1:0] alternate_idx;
  reg [REQ_META_W-1:0] fallback_req;
  reg [REQ_META_W-1:0] locality_req;
  reg [REQ_META_W-1:0] alternate_req;
  reg [SOURCE_PTR_W-1:0] scan_src;

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

  function [RESP_META_W-1:0] pack_resp;
    input [SOURCE_W-1:0] source;
    input [TAG_W-1:0] tag;
    input [ADDR_W-1:0] addr;
    input [VALUE_SLICE_W-1:0] value_slice;
    input [FRAG_IDX_W-1:0] fragment_idx;
    input last;
    input [PACKET_W-1:0] data;
    begin
      pack_resp = {RESP_META_W{1'b0}};
      pack_resp[RESP_SRC_LSB +: SOURCE_W] = source;
      pack_resp[RESP_TAG_LSB +: TAG_W] = tag;
      pack_resp[RESP_ADDR_LSB +: ADDR_W] = addr;
      pack_resp[RESP_SLICE_LSB +: VALUE_SLICE_W] = value_slice;
      pack_resp[RESP_FRAG_LSB +: FRAG_IDX_W] = fragment_idx;
      pack_resp[RESP_LAST_LSB] = last;
      pack_resp[RESP_DATA_LSB +: PACKET_W] = data;
    end
  endfunction

  function [SOURCE_W-1:0] req_source_from_meta;
    input [REQ_META_W-1:0] meta;
    begin
      req_source_from_meta = meta[REQ_SRC_LSB +: SOURCE_W];
    end
  endfunction

  function [TAG_W-1:0] req_tag_from_meta;
    input [REQ_META_W-1:0] meta;
    begin
      req_tag_from_meta = meta[REQ_TAG_LSB +: TAG_W];
    end
  endfunction

  function [ADDR_W-1:0] req_addr_from_meta;
    input [REQ_META_W-1:0] meta;
    begin
      req_addr_from_meta = meta[REQ_ADDR_LSB +: ADDR_W];
    end
  endfunction

  function [VALUE_SLICE_W-1:0] req_slice_from_meta;
    input [REQ_META_W-1:0] meta;
    begin
      req_slice_from_meta = meta[REQ_SLICE_LSB +: VALUE_SLICE_W];
    end
  endfunction

  function [BANK_SEL_W-1:0] req_bank_from_meta;
    input [REQ_META_W-1:0] meta;
    integer bank_int;
    begin
      bank_int = req_addr_from_meta(meta) % BANKS;
      req_bank_from_meta = bank_int[BANK_SEL_W-1:0];
    end
  endfunction

  function [SOURCE_W-1:0] resp_source_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_source_from_meta = meta[RESP_SRC_LSB +: SOURCE_W];
    end
  endfunction

  function [TAG_W-1:0] resp_tag_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_tag_from_meta = meta[RESP_TAG_LSB +: TAG_W];
    end
  endfunction

  function [ADDR_W-1:0] resp_addr_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_addr_from_meta = meta[RESP_ADDR_LSB +: ADDR_W];
    end
  endfunction

  function [VALUE_SLICE_W-1:0] resp_slice_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_slice_from_meta = meta[RESP_SLICE_LSB +: VALUE_SLICE_W];
    end
  endfunction

  function [FRAG_IDX_W-1:0] resp_fragment_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_fragment_from_meta = meta[RESP_FRAG_LSB +: FRAG_IDX_W];
    end
  endfunction

  function resp_last_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_last_from_meta = meta[RESP_LAST_LSB];
    end
  endfunction

  function [PACKET_W-1:0] resp_data_from_meta;
    input [RESP_META_W-1:0] meta;
    begin
      resp_data_from_meta = meta[RESP_DATA_LSB +: PACKET_W];
    end
  endfunction

  wire req_fire = req_valid && req_ready;
  wire resp_fire = resp_valid && resp_ready;

  assign req_valid = grant_valid_r;
  assign req_source = req_source_from_meta(grant_req_r);
  assign req_tag = req_tag_from_meta(grant_req_r);
  assign req_addr = req_addr_from_meta(grant_req_r);
  assign req_value_slice = req_slice_from_meta(grant_req_r);
  assign resp_bus = pack_resp(resp_source, resp_tag, resp_addr, resp_value_slice,
                              resp_fragment_idx, resp_last, resp_data);
  assign req_current_occupancy = {{(COUNTER_W-REQ_OCC_W){1'b0}}, req_occupancy_sum_r};
  assign resp_current_occupancy = {{(COUNTER_W-RESP_OCC_W){1'b0}}, resp_occupancy_sum_r};

  genvar req_gi;
  generate
    for (req_gi = 0; req_gi < SOURCES; req_gi = req_gi + 1) begin : gen_req_fifo
      noc_ready_valid_fifo #(
        .WIDTH(REQ_META_W),
        .DEPTH(REQ_QUEUE_DEPTH)
      ) u_req_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(src_req_valid[req_gi]),
        .in_ready(src_req_ready[req_gi]),
        .in_data(pack_req(src_req_source[(req_gi * SOURCE_W) +: SOURCE_W],
                          src_req_tag[(req_gi * TAG_W) +: TAG_W],
                          src_req_addr[(req_gi * ADDR_W) +: ADDR_W],
                          src_req_value_slice[(req_gi * VALUE_SLICE_W) +: VALUE_SLICE_W])),
        .out_valid(req_fifo_out_valid[req_gi]),
        .out_ready(req_fifo_out_ready_r[req_gi]),
        .out_data(req_fifo_out_bus[(req_gi * REQ_META_W) +: REQ_META_W]),
        .occupancy(req_fifo_occupancy_bus[(req_gi * REQ_COUNT_W) +: REQ_COUNT_W]),
        .max_occupancy()
      );
    end
  endgenerate

  genvar resp_gi;
  generate
    for (resp_gi = 0; resp_gi < SOURCES; resp_gi = resp_gi + 1) begin : gen_resp_fifo
      noc_ready_valid_fifo #(
        .WIDTH(RESP_META_W),
        .DEPTH(RESP_QUEUE_DEPTH)
      ) u_resp_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(resp_fifo_in_valid[resp_gi]),
        .in_ready(resp_fifo_in_ready[resp_gi]),
        .in_data(resp_bus),
        .out_valid(src_resp_valid[resp_gi]),
        .out_ready(src_resp_ready[resp_gi]),
        .out_data(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]),
        .occupancy(resp_fifo_occupancy_bus[(resp_gi * RESP_COUNT_W) +: RESP_COUNT_W]),
        .max_occupancy()
      );

      assign src_resp_source[(resp_gi * SOURCE_W) +: SOURCE_W] =
        resp_source_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_tag[(resp_gi * TAG_W) +: TAG_W] =
        resp_tag_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_addr[(resp_gi * ADDR_W) +: ADDR_W] =
        resp_addr_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_value_slice[(resp_gi * VALUE_SLICE_W) +: VALUE_SLICE_W] =
        resp_slice_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_fragment_idx[(resp_gi * FRAG_IDX_W) +: FRAG_IDX_W] =
        resp_fragment_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_last[resp_gi] =
        resp_last_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);
      assign src_resp_data[(resp_gi * PACKET_W) +: PACKET_W] =
        resp_data_from_meta(resp_fifo_out_bus[(resp_gi * RESP_META_W) +: RESP_META_W]);

      assign resp_fifo_in_valid[resp_gi] =
        resp_valid && resp_target_valid_r && (resp_target_idx_r == resp_gi[SOURCE_PTR_W-1:0]);
    end
  endgenerate

  always @(*) begin
    grant_valid_r = 1'b0;
    grant_idx_r = {SOURCE_PTR_W{1'b0}};
    grant_req_r = {REQ_META_W{1'b0}};
    req_fifo_out_ready_r = {SOURCES{1'b0}};
    req_occupancy_sum_r = {REQ_OCC_W{1'b0}};
    resp_occupancy_sum_r = {RESP_OCC_W{1'b0}};
    any_injection_stall_r = 1'b0;
    arbitration_contended_r = 1'b0;
    req_ready_count = 0;
    fallback_hit = 1'b0;
    locality_hit = 1'b0;
    alternate_hit = 1'b0;
    fallback_idx = {SOURCE_PTR_W{1'b0}};
    locality_idx = {SOURCE_PTR_W{1'b0}};
    alternate_idx = {SOURCE_PTR_W{1'b0}};
    fallback_req = {REQ_META_W{1'b0}};
    locality_req = {REQ_META_W{1'b0}};
    alternate_req = {REQ_META_W{1'b0}};

    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      req_occupancy_sum_r = req_occupancy_sum_r +
        req_fifo_occupancy_bus[(src_i * REQ_COUNT_W) +: REQ_COUNT_W];
      resp_occupancy_sum_r = resp_occupancy_sum_r +
        resp_fifo_occupancy_bus[(src_i * RESP_COUNT_W) +: RESP_COUNT_W];
      if (src_req_valid[src_i] && !src_req_ready[src_i]) begin
        any_injection_stall_r = 1'b1;
      end
      if (req_fifo_out_valid[src_i]) begin
        req_ready_count = req_ready_count + 1;
      end
    end

    arbitration_contended_r = (req_ready_count > 1);

    for (scan_i = 0; scan_i < SOURCES; scan_i = scan_i + 1) begin
      scan_src_int = rr_cursor + scan_i;
      if (scan_src_int >= SOURCES) begin
        scan_src_int = scan_src_int - SOURCES;
      end
      scan_src = scan_src_int[SOURCE_PTR_W-1:0];
      if (req_fifo_out_valid[scan_src]) begin
        if (!fallback_hit) begin
          fallback_hit = 1'b1;
          fallback_idx = scan_src;
          fallback_req = req_fifo_out_bus[(scan_src * REQ_META_W) +: REQ_META_W];
        end
        if ((req_bank_from_meta(req_fifo_out_bus[(scan_src * REQ_META_W) +: REQ_META_W]) == preferred_bank) &&
            !locality_hit) begin
          locality_hit = 1'b1;
          locality_idx = scan_src;
          locality_req = req_fifo_out_bus[(scan_src * REQ_META_W) +: REQ_META_W];
        end
        if ((req_bank_from_meta(req_fifo_out_bus[(scan_src * REQ_META_W) +: REQ_META_W]) != preferred_bank) &&
            !alternate_hit) begin
          alternate_hit = 1'b1;
          alternate_idx = scan_src;
          alternate_req = req_fifo_out_bus[(scan_src * REQ_META_W) +: REQ_META_W];
        end
      end
    end

    if (ARB_MODE == 0) begin
      if (fallback_hit) begin
        grant_valid_r = 1'b1;
        grant_idx_r = fallback_idx;
        grant_req_r = fallback_req;
      end
    end else begin
      if (locality_hit && (!alternate_hit || (locality_burst_count < LOCALITY_BURST_MAX))) begin
        grant_valid_r = 1'b1;
        grant_idx_r = locality_idx;
        grant_req_r = locality_req;
      end else if (alternate_hit) begin
        grant_valid_r = 1'b1;
        grant_idx_r = alternate_idx;
        grant_req_r = alternate_req;
      end else if (locality_hit) begin
        grant_valid_r = 1'b1;
        grant_idx_r = locality_idx;
        grant_req_r = locality_req;
      end else if (fallback_hit) begin
        grant_valid_r = 1'b1;
        grant_idx_r = fallback_idx;
        grant_req_r = fallback_req;
      end
    end

    if (req_fire) begin
      req_fifo_out_ready_r[grant_idx_r] = 1'b1;
    end
  end

  always @(*) begin
    resp_target_valid_r = 1'b0;
    resp_target_idx_r = {SOURCE_PTR_W{1'b0}};
    for (src_i = 0; src_i < SOURCES; src_i = src_i + 1) begin
      if (!resp_target_valid_r && (resp_source == src_i[SOURCE_W-1:0])) begin
        resp_target_valid_r = 1'b1;
        resp_target_idx_r = src_i[SOURCE_PTR_W-1:0];
      end
    end
  end

  assign resp_ready = resp_target_valid_r && resp_fifo_in_ready[resp_target_idx_r];

  integer init_src;
  integer init_bank;
  initial begin
    if ((PACKET_W != 128) && (PACKET_W != 256)) begin
      $error("noc_ready_valid_router PACKET_W must be 128 or 256, got %0d", PACKET_W);
      $finish(1);
    end
    if (VALUE_W != 512) begin
      $error("noc_ready_valid_router VALUE_W must be 512, got %0d", VALUE_W);
      $finish(1);
    end
    if ((VALUE_W % PACKET_W) != 0) begin
      $error("noc_ready_valid_router VALUE_W must be an integer multiple of PACKET_W");
      $finish(1);
    end
    if (VALUE_SLICE_W != 4) begin
      $error("noc_ready_valid_router VALUE_SLICE_W must be 4, got %0d", VALUE_SLICE_W);
      $finish(1);
    end
    if ((1 << FRAG_IDX_W) < FRAGMENTS) begin
      $error("noc_ready_valid_router FRAG_IDX_W is too small for %0d fragments", FRAGMENTS);
      $finish(1);
    end
    if ((SOURCES <= 0) || (BANKS <= 0)) begin
      $error("noc_ready_valid_router SOURCES and BANKS must be positive");
      $finish(1);
    end
    if (SOURCES > (1 << SOURCE_W)) begin
      $error("noc_ready_valid_router SOURCE_W is too small for SOURCES");
      $finish(1);
    end
    if (LOCALITY_BURST_MAX <= 0) begin
      $error("noc_ready_valid_router LOCALITY_BURST_MAX must be positive");
      $finish(1);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rr_cursor <= {SOURCE_PTR_W{1'b0}};
      preferred_bank <= {BANK_SEL_W{1'b0}};
      locality_burst_count <= {LOCALITY_BURST_W{1'b0}};
      injection_stall_cycles <= {COUNTER_W{1'b0}};
      arbitration_contention_cycles <= {COUNTER_W{1'b0}};
      response_block_cycles <= {COUNTER_W{1'b0}};
      req_max_occupancy <= {COUNTER_W{1'b0}};
      resp_max_occupancy <= {COUNTER_W{1'b0}};
    end else begin
      if (any_injection_stall_r) begin
        injection_stall_cycles <= injection_stall_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (grant_valid_r && arbitration_contended_r) begin
        arbitration_contention_cycles <= arbitration_contention_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (resp_valid && !resp_ready) begin
        response_block_cycles <= response_block_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (req_fire) begin
        if (grant_idx_r == (SOURCES - 1)) begin
          rr_cursor <= {SOURCE_PTR_W{1'b0}};
        end else begin
          rr_cursor <= grant_idx_r + {{(SOURCE_PTR_W-1){1'b0}}, 1'b1};
        end

        if (req_bank_from_meta(grant_req_r) == preferred_bank) begin
          if (locality_burst_count < LOCALITY_BURST_MAX[LOCALITY_BURST_W-1:0]) begin
            locality_burst_count <= locality_burst_count + {{(LOCALITY_BURST_W-1){1'b0}}, 1'b1};
          end
        end else begin
          preferred_bank <= req_bank_from_meta(grant_req_r);
          locality_burst_count <= {{(LOCALITY_BURST_W-1){1'b0}}, 1'b1};
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
