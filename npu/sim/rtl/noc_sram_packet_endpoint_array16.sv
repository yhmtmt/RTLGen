`timescale 1ns/1ps

`ifndef NOC_SRAM_PACKET_ENDPOINT_ARRAY16_SV
`define NOC_SRAM_PACKET_ENDPOINT_ARRAY16_SV

// Exact sixteen-endpoint boundary for the SRAM-packet mesh wrapper.
module noc_sram_packet_endpoint_array16 #(
  parameter integer DATA_W = 256,
  parameter integer ENDPOINT_W = 4,
  parameter integer VC_W = 2,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer ADDR_W = 24,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer TX_DESC_DEPTH = 4,
  parameter integer TX_OUTSTANDING = 8,
  parameter integer RX_CONTEXTS = 8
) (
  input wire clk,
  input wire rst_n,

  input wire [15:0] tx_desc_valid,
  output wire [15:0] tx_desc_ready,
  input wire [16*ENDPOINT_W-1:0] tx_desc_destination,
  input wire [16*VC_W-1:0] tx_desc_vc,
  input wire [16*TAG_W-1:0] tx_desc_tag,
  input wire [16*ADDR_W-1:0] tx_desc_base_addr,
  input wire [16*FLIT_COUNT_W-1:0] tx_desc_flit_count,

  output wire [15:0] tx_mem_req_valid,
  input wire [15:0] tx_mem_req_ready,
  output wire [16*ADDR_W-1:0] tx_mem_req_addr,
  input wire [15:0] tx_mem_rsp_valid,
  output wire [15:0] tx_mem_rsp_ready,
  input wire [16*DATA_W-1:0] tx_mem_rsp_data,

  output wire [15:0] mesh_in_valid,
  input wire [15:0] mesh_in_ready,
  output wire [16*ENDPOINT_W-1:0] mesh_in_destination,
  output wire [16*ENDPOINT_W-1:0] mesh_in_source,
  output wire [16*TAG_W-1:0] mesh_in_tag,
  output wire [16*FRAGMENT_W-1:0] mesh_in_fragment,
  output wire [15:0] mesh_in_last,
  output wire [16*VC_W-1:0] mesh_in_vc,
  output wire [16*DATA_W-1:0] mesh_in_data,

  input wire [15:0] rx_desc_valid,
  output wire [15:0] rx_desc_ready,
  input wire [16*ENDPOINT_W-1:0] rx_desc_source,
  input wire [16*VC_W-1:0] rx_desc_vc,
  input wire [16*TAG_W-1:0] rx_desc_tag,
  input wire [16*ADDR_W-1:0] rx_desc_base_addr,
  input wire [16*FLIT_COUNT_W-1:0] rx_desc_flit_count,

  input wire [15:0] mesh_out_valid,
  output wire [15:0] mesh_out_ready,
  input wire [16*ENDPOINT_W-1:0] mesh_out_destination,
  input wire [16*ENDPOINT_W-1:0] mesh_out_source,
  input wire [16*TAG_W-1:0] mesh_out_tag,
  input wire [16*FRAGMENT_W-1:0] mesh_out_fragment,
  input wire [15:0] mesh_out_last,
  input wire [16*VC_W-1:0] mesh_out_vc,
  input wire [16*DATA_W-1:0] mesh_out_data,

  output wire [15:0] rx_mem_write_valid,
  input wire [15:0] rx_mem_write_ready,
  output wire [16*ADDR_W-1:0] rx_mem_write_addr,
  output wire [16*DATA_W-1:0] rx_mem_write_data,

  output wire [15:0] rx_completion_valid,
  input wire [15:0] rx_completion_ready,
  output wire [16*ENDPOINT_W-1:0] rx_completion_source,
  output wire [16*VC_W-1:0] rx_completion_vc,
  output wire [16*TAG_W-1:0] rx_completion_tag,
  output wire [15:0] endpoint_protocol_error
);
  localparam integer NODES = 16;

  genvar node_g;
  generate
    for (node_g = 0; node_g < NODES; node_g = node_g + 1) begin : gen_endpoints
      noc_sram_packet_endpoint #(
        .DATA_W(DATA_W),
        .ENDPOINT_W(ENDPOINT_W),
        .VC_W(VC_W),
        .TAG_W(TAG_W),
        .FRAGMENT_W(FRAGMENT_W),
        .ADDR_W(ADDR_W),
        .FLIT_COUNT_W(FLIT_COUNT_W),
        .TX_DESC_DEPTH(TX_DESC_DEPTH),
        .TX_OUTSTANDING(TX_OUTSTANDING),
        .RX_CONTEXTS(RX_CONTEXTS),
        .LOCAL_ENDPOINT_ID(node_g)
      ) endpoint (
        .clk(clk),
        .rst_n(rst_n),
        .tx_desc_valid(tx_desc_valid[node_g]),
        .tx_desc_ready(tx_desc_ready[node_g]),
        .tx_desc_destination(tx_desc_destination[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .tx_desc_vc(tx_desc_vc[(node_g*VC_W) +: VC_W]),
        .tx_desc_tag(tx_desc_tag[(node_g*TAG_W) +: TAG_W]),
        .tx_desc_base_addr(tx_desc_base_addr[(node_g*ADDR_W) +: ADDR_W]),
        .tx_desc_flit_count(tx_desc_flit_count[(node_g*FLIT_COUNT_W) +: FLIT_COUNT_W]),
        .tx_mem_req_valid(tx_mem_req_valid[node_g]),
        .tx_mem_req_ready(tx_mem_req_ready[node_g]),
        .tx_mem_req_addr(tx_mem_req_addr[(node_g*ADDR_W) +: ADDR_W]),
        .tx_mem_rsp_valid(tx_mem_rsp_valid[node_g]),
        .tx_mem_rsp_ready(tx_mem_rsp_ready[node_g]),
        .tx_mem_rsp_data(tx_mem_rsp_data[(node_g*DATA_W) +: DATA_W]),
        .tx_flit_valid(mesh_in_valid[node_g]),
        .tx_flit_ready(mesh_in_ready[node_g]),
        .tx_flit_source(mesh_in_source[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .tx_flit_destination(mesh_in_destination[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .tx_flit_vc(mesh_in_vc[(node_g*VC_W) +: VC_W]),
        .tx_flit_tag(mesh_in_tag[(node_g*TAG_W) +: TAG_W]),
        .tx_flit_fragment(mesh_in_fragment[(node_g*FRAGMENT_W) +: FRAGMENT_W]),
        .tx_flit_last(mesh_in_last[node_g]),
        .tx_flit_data(mesh_in_data[(node_g*DATA_W) +: DATA_W]),
        .rx_desc_valid(rx_desc_valid[node_g]),
        .rx_desc_ready(rx_desc_ready[node_g]),
        .rx_desc_source(rx_desc_source[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .rx_desc_vc(rx_desc_vc[(node_g*VC_W) +: VC_W]),
        .rx_desc_tag(rx_desc_tag[(node_g*TAG_W) +: TAG_W]),
        .rx_desc_base_addr(rx_desc_base_addr[(node_g*ADDR_W) +: ADDR_W]),
        .rx_desc_flit_count(rx_desc_flit_count[(node_g*FLIT_COUNT_W) +: FLIT_COUNT_W]),
        .rx_flit_valid(mesh_out_valid[node_g]),
        .rx_flit_ready(mesh_out_ready[node_g]),
        .rx_flit_source(mesh_out_source[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .rx_flit_destination(mesh_out_destination[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .rx_flit_vc(mesh_out_vc[(node_g*VC_W) +: VC_W]),
        .rx_flit_tag(mesh_out_tag[(node_g*TAG_W) +: TAG_W]),
        .rx_flit_fragment(mesh_out_fragment[(node_g*FRAGMENT_W) +: FRAGMENT_W]),
        .rx_flit_last(mesh_out_last[node_g]),
        .rx_flit_data(mesh_out_data[(node_g*DATA_W) +: DATA_W]),
        .rx_mem_write_valid(rx_mem_write_valid[node_g]),
        .rx_mem_write_ready(rx_mem_write_ready[node_g]),
        .rx_mem_write_addr(rx_mem_write_addr[(node_g*ADDR_W) +: ADDR_W]),
        .rx_mem_write_data(rx_mem_write_data[(node_g*DATA_W) +: DATA_W]),
        .rx_completion_valid(rx_completion_valid[node_g]),
        .rx_completion_ready(rx_completion_ready[node_g]),
        .rx_completion_source(rx_completion_source[(node_g*ENDPOINT_W) +: ENDPOINT_W]),
        .rx_completion_vc(rx_completion_vc[(node_g*VC_W) +: VC_W]),
        .rx_completion_tag(rx_completion_tag[(node_g*TAG_W) +: TAG_W]),
        .protocol_error(endpoint_protocol_error[node_g])
      );
    end
  endgenerate
endmodule

`endif
