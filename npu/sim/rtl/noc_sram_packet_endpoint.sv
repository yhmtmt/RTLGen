`timescale 1ns/1ps

// Descriptor-driven SRAM endpoint for the segmented NoC.
//
// TX descriptors retain payloads in source SRAM and issue one read per flit.
// RX contexts map packet identities to destination SRAM and write each flit
// directly, avoiding a packet-wide register or an implicit reassembly buffer.
module noc_sram_packet_endpoint #(
  parameter integer DATA_W = 256,
  parameter integer ENDPOINT_W = 4,
  parameter integer VC_W = 2,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer ADDR_W = 24,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer TX_DESC_DEPTH = 4,
  parameter integer TX_OUTSTANDING = 8,
  parameter integer RX_CONTEXTS = 8,
  parameter integer LOCAL_ENDPOINT_ID = 0
) (
  input wire clk,
  input wire rst_n,

  input wire tx_desc_valid,
  output wire tx_desc_ready,
  input wire [ENDPOINT_W-1:0] tx_desc_destination,
  input wire [VC_W-1:0] tx_desc_vc,
  input wire [TAG_W-1:0] tx_desc_tag,
  input wire [ADDR_W-1:0] tx_desc_base_addr,
  input wire [FLIT_COUNT_W-1:0] tx_desc_flit_count,

  output wire tx_mem_req_valid,
  input wire tx_mem_req_ready,
  output wire [ADDR_W-1:0] tx_mem_req_addr,
  input wire tx_mem_rsp_valid,
  output wire tx_mem_rsp_ready,
  input wire [DATA_W-1:0] tx_mem_rsp_data,

  output wire tx_flit_valid,
  input wire tx_flit_ready,
  output wire [ENDPOINT_W-1:0] tx_flit_source,
  output wire [ENDPOINT_W-1:0] tx_flit_destination,
  output wire [VC_W-1:0] tx_flit_vc,
  output wire [TAG_W-1:0] tx_flit_tag,
  output wire [FRAGMENT_W-1:0] tx_flit_fragment,
  output wire tx_flit_last,
  output wire [DATA_W-1:0] tx_flit_data,

  input wire rx_desc_valid,
  output wire rx_desc_ready,
  input wire [ENDPOINT_W-1:0] rx_desc_source,
  input wire [VC_W-1:0] rx_desc_vc,
  input wire [TAG_W-1:0] rx_desc_tag,
  input wire [ADDR_W-1:0] rx_desc_base_addr,
  input wire [FLIT_COUNT_W-1:0] rx_desc_flit_count,

  input wire rx_flit_valid,
  output wire rx_flit_ready,
  input wire [ENDPOINT_W-1:0] rx_flit_source,
  input wire [VC_W-1:0] rx_flit_vc,
  input wire [TAG_W-1:0] rx_flit_tag,
  input wire [FRAGMENT_W-1:0] rx_flit_fragment,
  input wire rx_flit_last,
  input wire [DATA_W-1:0] rx_flit_data,

  output wire rx_mem_write_valid,
  input wire rx_mem_write_ready,
  output wire [ADDR_W-1:0] rx_mem_write_addr,
  output wire [DATA_W-1:0] rx_mem_write_data,

  output wire rx_completion_valid,
  input wire rx_completion_ready,
  output wire [ENDPOINT_W-1:0] rx_completion_source,
  output wire [VC_W-1:0] rx_completion_vc,
  output wire [TAG_W-1:0] rx_completion_tag,
  output reg protocol_error
);
  localparam integer DATA_BYTES = DATA_W / 8;
  localparam integer TX_DESC_PTR_W = (TX_DESC_DEPTH <= 1) ? 1 : $clog2(TX_DESC_DEPTH);
  localparam integer TX_DESC_COUNT_W = (TX_DESC_DEPTH <= 1) ? 1 : $clog2(TX_DESC_DEPTH + 1);
  localparam integer TX_META_PTR_W = (TX_OUTSTANDING <= 1) ? 1 : $clog2(TX_OUTSTANDING);
  localparam integer TX_META_COUNT_W = (TX_OUTSTANDING <= 1) ? 1 : $clog2(TX_OUTSTANDING + 1);
  localparam integer RX_CONTEXT_W = (RX_CONTEXTS <= 1) ? 1 : $clog2(RX_CONTEXTS);
  localparam [ADDR_W-1:0] DATA_BYTES_VALUE = ADDR_W'(DATA_BYTES);
  localparam [FLIT_COUNT_W-1:0] MAX_FLIT_COUNT = FLIT_COUNT_W'(1 << FRAGMENT_W);
  localparam [TX_DESC_COUNT_W-1:0] TX_DESC_DEPTH_VALUE = TX_DESC_COUNT_W'(TX_DESC_DEPTH);
  localparam [TX_META_COUNT_W-1:0] TX_OUTSTANDING_VALUE = TX_META_COUNT_W'(TX_OUTSTANDING);
  localparam [TX_DESC_PTR_W-1:0] TX_DESC_LAST = TX_DESC_PTR_W'(TX_DESC_DEPTH - 1);
  localparam [TX_META_PTR_W-1:0] TX_META_LAST = TX_META_PTR_W'(TX_OUTSTANDING - 1);

  reg [ENDPOINT_W-1:0] tx_desc_destination_mem [0:TX_DESC_DEPTH-1];
  reg [VC_W-1:0] tx_desc_vc_mem [0:TX_DESC_DEPTH-1];
  reg [TAG_W-1:0] tx_desc_tag_mem [0:TX_DESC_DEPTH-1];
  reg [ADDR_W-1:0] tx_desc_base_mem [0:TX_DESC_DEPTH-1];
  reg [FLIT_COUNT_W-1:0] tx_desc_count_mem [0:TX_DESC_DEPTH-1];
  reg [TX_DESC_PTR_W-1:0] tx_desc_rd_ptr;
  reg [TX_DESC_PTR_W-1:0] tx_desc_wr_ptr;
  reg [TX_DESC_COUNT_W-1:0] tx_desc_occupancy;

  reg tx_active;
  reg [ENDPOINT_W-1:0] tx_active_destination;
  reg [VC_W-1:0] tx_active_vc;
  reg [TAG_W-1:0] tx_active_tag;
  reg [ADDR_W-1:0] tx_active_base;
  reg [FLIT_COUNT_W-1:0] tx_active_count;
  reg [FRAGMENT_W-1:0] tx_issue_fragment;

  reg [ENDPOINT_W-1:0] tx_meta_destination [0:TX_OUTSTANDING-1];
  reg [VC_W-1:0] tx_meta_vc [0:TX_OUTSTANDING-1];
  reg [TAG_W-1:0] tx_meta_tag [0:TX_OUTSTANDING-1];
  reg [FRAGMENT_W-1:0] tx_meta_fragment [0:TX_OUTSTANDING-1];
  reg tx_meta_last [0:TX_OUTSTANDING-1];
  reg [TX_META_PTR_W-1:0] tx_meta_rd_ptr;
  reg [TX_META_PTR_W-1:0] tx_meta_wr_ptr;
  reg [TX_META_COUNT_W-1:0] tx_meta_occupancy;

  reg tx_flit_valid_r;
  reg [ENDPOINT_W-1:0] tx_flit_destination_r;
  reg [VC_W-1:0] tx_flit_vc_r;
  reg [TAG_W-1:0] tx_flit_tag_r;
  reg [FRAGMENT_W-1:0] tx_flit_fragment_r;
  reg tx_flit_last_r;
  reg [DATA_W-1:0] tx_flit_data_r;

  reg rx_context_valid [0:RX_CONTEXTS-1];
  reg [ENDPOINT_W-1:0] rx_context_source [0:RX_CONTEXTS-1];
  reg [VC_W-1:0] rx_context_vc [0:RX_CONTEXTS-1];
  reg [TAG_W-1:0] rx_context_tag [0:RX_CONTEXTS-1];
  reg [ADDR_W-1:0] rx_context_base [0:RX_CONTEXTS-1];
  reg [FLIT_COUNT_W-1:0] rx_context_count [0:RX_CONTEXTS-1];
  reg [FRAGMENT_W-1:0] rx_context_expected [0:RX_CONTEXTS-1];

  reg rx_free_found;
  reg [RX_CONTEXT_W-1:0] rx_free_index;
  reg rx_duplicate_found;
  reg rx_match_found;
  reg [RX_CONTEXT_W-1:0] rx_match_index;
  reg rx_fragment_valid;
  reg rx_last_valid;

  reg rx_completion_valid_r;
  reg [ENDPOINT_W-1:0] rx_completion_source_r;
  reg [VC_W-1:0] rx_completion_vc_r;
  reg [TAG_W-1:0] rx_completion_tag_r;

  integer scan_i;
  integer reset_i;

  wire tx_desc_count_valid =
    (tx_desc_flit_count != {FLIT_COUNT_W{1'b0}}) &&
    (tx_desc_flit_count <= MAX_FLIT_COUNT);
  wire tx_desc_push = tx_desc_valid && tx_desc_ready;
  wire tx_desc_pop = !tx_active && (tx_desc_occupancy != 0);
  wire tx_request_last =
    ({{(FLIT_COUNT_W-FRAGMENT_W){1'b0}}, tx_issue_fragment} + 1'b1) == tx_active_count;
  wire tx_mem_req_fire = tx_mem_req_valid && tx_mem_req_ready;
  wire tx_mem_rsp_fire = tx_mem_rsp_valid && tx_mem_rsp_ready;
  wire tx_flit_fire = tx_flit_valid && tx_flit_ready;

  assign tx_desc_ready =
    tx_desc_count_valid &&
    ((tx_desc_occupancy < TX_DESC_DEPTH_VALUE) || tx_desc_pop);
  assign tx_mem_req_valid = tx_active && (tx_meta_occupancy < TX_OUTSTANDING_VALUE);
  assign tx_mem_req_addr =
    tx_active_base + (tx_issue_fragment * DATA_BYTES_VALUE);
  assign tx_mem_rsp_ready =
    (tx_meta_occupancy != 0) && (!tx_flit_valid_r || tx_flit_ready);

  assign tx_flit_valid = tx_flit_valid_r;
  assign tx_flit_source = LOCAL_ENDPOINT_ID[ENDPOINT_W-1:0];
  assign tx_flit_destination = tx_flit_destination_r;
  assign tx_flit_vc = tx_flit_vc_r;
  assign tx_flit_tag = tx_flit_tag_r;
  assign tx_flit_fragment = tx_flit_fragment_r;
  assign tx_flit_last = tx_flit_last_r;
  assign tx_flit_data = tx_flit_data_r;

  always @(*) begin
    rx_free_found = 1'b0;
    rx_free_index = {RX_CONTEXT_W{1'b0}};
    rx_duplicate_found = 1'b0;
    rx_match_found = 1'b0;
    rx_match_index = {RX_CONTEXT_W{1'b0}};
    for (scan_i = 0; scan_i < RX_CONTEXTS; scan_i = scan_i + 1) begin
      if (!rx_context_valid[scan_i] && !rx_free_found) begin
        rx_free_found = 1'b1;
        rx_free_index = scan_i[RX_CONTEXT_W-1:0];
      end
      if (rx_context_valid[scan_i] &&
          rx_context_source[scan_i] == rx_desc_source &&
          rx_context_vc[scan_i] == rx_desc_vc &&
          rx_context_tag[scan_i] == rx_desc_tag) begin
        rx_duplicate_found = 1'b1;
      end
      if (rx_context_valid[scan_i] &&
          rx_context_source[scan_i] == rx_flit_source &&
          rx_context_vc[scan_i] == rx_flit_vc &&
          rx_context_tag[scan_i] == rx_flit_tag &&
          !rx_match_found) begin
        rx_match_found = 1'b1;
        rx_match_index = scan_i[RX_CONTEXT_W-1:0];
      end
    end
    rx_fragment_valid = rx_match_found &&
      (rx_flit_fragment == rx_context_expected[rx_match_index]);
    rx_last_valid = rx_match_found &&
      (rx_flit_last ==
       (({{(FLIT_COUNT_W-FRAGMENT_W){1'b0}}, rx_context_expected[rx_match_index]} + 1'b1) ==
        rx_context_count[rx_match_index]));
  end

  wire rx_desc_count_valid =
    (rx_desc_flit_count != {FLIT_COUNT_W{1'b0}}) &&
    (rx_desc_flit_count <= MAX_FLIT_COUNT);
  wire rx_desc_push = rx_desc_valid && rx_desc_ready;
  wire rx_flit_protocol_valid = rx_match_found && rx_fragment_valid && rx_last_valid;
  wire rx_completion_space = !rx_completion_valid_r || rx_completion_ready;
  wire rx_flit_fire = rx_flit_valid && rx_flit_ready;
  wire rx_packet_complete = rx_flit_protocol_valid && rx_flit_last;

  assign rx_desc_ready =
    rx_desc_count_valid && rx_free_found && !rx_duplicate_found;
  assign rx_mem_write_valid = rx_flit_valid && rx_flit_protocol_valid;
  assign rx_mem_write_addr = rx_match_found ?
    rx_context_base[rx_match_index] + (rx_flit_fragment * DATA_BYTES_VALUE) :
    {ADDR_W{1'b0}};
  assign rx_mem_write_data = rx_flit_data;
  assign rx_flit_ready = rx_flit_protocol_valid ?
    (rx_mem_write_ready && (!rx_flit_last || rx_completion_space)) : 1'b1;

  assign rx_completion_valid = rx_completion_valid_r;
  assign rx_completion_source = rx_completion_source_r;
  assign rx_completion_vc = rx_completion_vc_r;
  assign rx_completion_tag = rx_completion_tag_r;

  function [TX_DESC_PTR_W-1:0] tx_desc_ptr_inc;
    input [TX_DESC_PTR_W-1:0] ptr;
    begin
      tx_desc_ptr_inc = (ptr == TX_DESC_LAST) ? {TX_DESC_PTR_W{1'b0}} : ptr + 1'b1;
    end
  endfunction

  function [TX_META_PTR_W-1:0] tx_meta_ptr_inc;
    input [TX_META_PTR_W-1:0] ptr;
    begin
      tx_meta_ptr_inc = (ptr == TX_META_LAST) ? {TX_META_PTR_W{1'b0}} : ptr + 1'b1;
    end
  endfunction

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256) begin
      $error("noc_sram_packet_endpoint DATA_W must match the 256-bit segmented mesh");
      $finish(1);
    end
    if (DATA_W % 8 != 0) begin
      $error("noc_sram_packet_endpoint DATA_W must be byte aligned");
      $finish(1);
    end
    if (TX_DESC_DEPTH < 1 || TX_OUTSTANDING < 1 || RX_CONTEXTS < 1) begin
      $error("noc_sram_packet_endpoint queue/context depths must be positive");
      $finish(1);
    end
    if (((1 << FLIT_COUNT_W) - 1) < (1 << FRAGMENT_W)) begin
      $error("noc_sram_packet_endpoint FLIT_COUNT_W cannot represent the fragment range");
      $finish(1);
    end
  end
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tx_desc_rd_ptr <= {TX_DESC_PTR_W{1'b0}};
      tx_desc_wr_ptr <= {TX_DESC_PTR_W{1'b0}};
      tx_desc_occupancy <= {TX_DESC_COUNT_W{1'b0}};
      tx_active <= 1'b0;
      tx_active_destination <= {ENDPOINT_W{1'b0}};
      tx_active_vc <= {VC_W{1'b0}};
      tx_active_tag <= {TAG_W{1'b0}};
      tx_active_base <= {ADDR_W{1'b0}};
      tx_active_count <= {FLIT_COUNT_W{1'b0}};
      tx_issue_fragment <= {FRAGMENT_W{1'b0}};
      tx_meta_rd_ptr <= {TX_META_PTR_W{1'b0}};
      tx_meta_wr_ptr <= {TX_META_PTR_W{1'b0}};
      tx_meta_occupancy <= {TX_META_COUNT_W{1'b0}};
      tx_flit_valid_r <= 1'b0;
      tx_flit_destination_r <= {ENDPOINT_W{1'b0}};
      tx_flit_vc_r <= {VC_W{1'b0}};
      tx_flit_tag_r <= {TAG_W{1'b0}};
      tx_flit_fragment_r <= {FRAGMENT_W{1'b0}};
      tx_flit_last_r <= 1'b0;
      tx_flit_data_r <= {DATA_W{1'b0}};
      rx_completion_valid_r <= 1'b0;
      rx_completion_source_r <= {ENDPOINT_W{1'b0}};
      rx_completion_vc_r <= {VC_W{1'b0}};
      rx_completion_tag_r <= {TAG_W{1'b0}};
      protocol_error <= 1'b0;
      for (reset_i = 0; reset_i < RX_CONTEXTS; reset_i = reset_i + 1) begin
        rx_context_valid[reset_i] <= 1'b0;
        rx_context_source[reset_i] <= {ENDPOINT_W{1'b0}};
        rx_context_vc[reset_i] <= {VC_W{1'b0}};
        rx_context_tag[reset_i] <= {TAG_W{1'b0}};
        rx_context_base[reset_i] <= {ADDR_W{1'b0}};
        rx_context_count[reset_i] <= {FLIT_COUNT_W{1'b0}};
        rx_context_expected[reset_i] <= {FRAGMENT_W{1'b0}};
      end
    end else begin
      if (tx_desc_valid && !tx_desc_count_valid) begin
        protocol_error <= 1'b1;
      end
      if (rx_desc_valid && (!rx_desc_count_valid || rx_duplicate_found)) begin
        protocol_error <= 1'b1;
      end

      if (tx_desc_push) begin
        tx_desc_destination_mem[tx_desc_wr_ptr] <= tx_desc_destination;
        tx_desc_vc_mem[tx_desc_wr_ptr] <= tx_desc_vc;
        tx_desc_tag_mem[tx_desc_wr_ptr] <= tx_desc_tag;
        tx_desc_base_mem[tx_desc_wr_ptr] <= tx_desc_base_addr;
        tx_desc_count_mem[tx_desc_wr_ptr] <= tx_desc_flit_count;
        tx_desc_wr_ptr <= tx_desc_ptr_inc(tx_desc_wr_ptr);
      end
      if (tx_desc_pop) begin
        tx_active <= 1'b1;
        tx_active_destination <= tx_desc_destination_mem[tx_desc_rd_ptr];
        tx_active_vc <= tx_desc_vc_mem[tx_desc_rd_ptr];
        tx_active_tag <= tx_desc_tag_mem[tx_desc_rd_ptr];
        tx_active_base <= tx_desc_base_mem[tx_desc_rd_ptr];
        tx_active_count <= tx_desc_count_mem[tx_desc_rd_ptr];
        tx_issue_fragment <= {FRAGMENT_W{1'b0}};
        tx_desc_rd_ptr <= tx_desc_ptr_inc(tx_desc_rd_ptr);
      end
      case ({tx_desc_push, tx_desc_pop})
        2'b10: tx_desc_occupancy <= tx_desc_occupancy + 1'b1;
        2'b01: tx_desc_occupancy <= tx_desc_occupancy - 1'b1;
        default: tx_desc_occupancy <= tx_desc_occupancy;
      endcase

      if (tx_mem_req_fire) begin
        tx_meta_destination[tx_meta_wr_ptr] <= tx_active_destination;
        tx_meta_vc[tx_meta_wr_ptr] <= tx_active_vc;
        tx_meta_tag[tx_meta_wr_ptr] <= tx_active_tag;
        tx_meta_fragment[tx_meta_wr_ptr] <= tx_issue_fragment;
        tx_meta_last[tx_meta_wr_ptr] <= tx_request_last;
        tx_meta_wr_ptr <= tx_meta_ptr_inc(tx_meta_wr_ptr);
        if (tx_request_last) begin
          tx_active <= 1'b0;
          tx_issue_fragment <= {FRAGMENT_W{1'b0}};
        end else begin
          tx_issue_fragment <= tx_issue_fragment + 1'b1;
        end
      end

      if (tx_mem_rsp_fire) begin
        tx_flit_valid_r <= 1'b1;
        tx_flit_destination_r <= tx_meta_destination[tx_meta_rd_ptr];
        tx_flit_vc_r <= tx_meta_vc[tx_meta_rd_ptr];
        tx_flit_tag_r <= tx_meta_tag[tx_meta_rd_ptr];
        tx_flit_fragment_r <= tx_meta_fragment[tx_meta_rd_ptr];
        tx_flit_last_r <= tx_meta_last[tx_meta_rd_ptr];
        tx_flit_data_r <= tx_mem_rsp_data;
        tx_meta_rd_ptr <= tx_meta_ptr_inc(tx_meta_rd_ptr);
      end else if (tx_flit_fire) begin
        tx_flit_valid_r <= 1'b0;
      end
      case ({tx_mem_req_fire, tx_mem_rsp_fire})
        2'b10: tx_meta_occupancy <= tx_meta_occupancy + 1'b1;
        2'b01: tx_meta_occupancy <= tx_meta_occupancy - 1'b1;
        default: tx_meta_occupancy <= tx_meta_occupancy;
      endcase

      if (rx_desc_push) begin
        rx_context_valid[rx_free_index] <= 1'b1;
        rx_context_source[rx_free_index] <= rx_desc_source;
        rx_context_vc[rx_free_index] <= rx_desc_vc;
        rx_context_tag[rx_free_index] <= rx_desc_tag;
        rx_context_base[rx_free_index] <= rx_desc_base_addr;
        rx_context_count[rx_free_index] <= rx_desc_flit_count;
        rx_context_expected[rx_free_index] <= {FRAGMENT_W{1'b0}};
      end

      if (rx_completion_valid_r && rx_completion_ready) begin
        rx_completion_valid_r <= 1'b0;
      end
      if (rx_flit_fire) begin
        if (!rx_flit_protocol_valid) begin
          protocol_error <= 1'b1;
        end else if (rx_packet_complete) begin
          rx_context_valid[rx_match_index] <= 1'b0;
          rx_context_expected[rx_match_index] <= {FRAGMENT_W{1'b0}};
          rx_completion_valid_r <= 1'b1;
          rx_completion_source_r <= rx_flit_source;
          rx_completion_vc_r <= rx_flit_vc;
          rx_completion_tag_r <= rx_flit_tag;
        end else begin
          rx_context_expected[rx_match_index] <= rx_context_expected[rx_match_index] + 1'b1;
        end
      end
    end
  end
endmodule
