`timescale 1ns/1ps

// Compact-boundary physical harness for the exact endpoint/mesh composition.
// It generates collision-free descriptor epochs and finite SRAM handshakes.
// SRAM bitcells and workload-derived activity are intentionally not modeled.
module noc_sram_packet_mesh4x4_ppa_harness #(
  parameter integer DATA_W = 256,
  parameter integer ADDR_W = 24,
  parameter integer COUNTER_W = 32,
  parameter integer TX_DESC_DEPTH = 4,
  parameter integer TX_OUTSTANDING = 8,
  parameter integer RX_CONTEXTS = 8,
  parameter integer ROUTER_FIFO_DEPTH = 4
) (
  input wire clk,
  input wire rst_n,
  output wire [15:0] observed_valid,
  output wire [DATA_W-1:0] observed_flit,
  output wire [COUNTER_W-1:0] issued_packet_count,
  output wire [COUNTER_W-1:0] completed_packet_count,
  output wire protocol_error
);
  localparam integer NODES = 16;
  localparam integer ENDPOINT_W = 4;
  localparam integer VC_W = 2;
  localparam integer TAG_W = 8;
  localparam integer FLIT_COUNT_W = 4;
  localparam integer OBSERVE_SLICE_W = DATA_W / NODES;
  localparam [1:0] INSTALL_RX = 2'd0;
  localparam [1:0] INSTALL_TX = 2'd1;
  localparam [1:0] RUN_PACKETS = 2'd2;

  reg [1:0] setup_state;
  reg [7:0] epoch;
  reg [15:0] descriptor_pending;
  reg [15:0] completion_seen;
  reg [COUNTER_W-1:0] issued_count_q;
  reg [COUNTER_W-1:0] completed_count_q;
  reg [COUNTER_W-1:0] cycle_count_q;

  reg [16*ENDPOINT_W-1:0] tx_desc_destination;
  reg [16*VC_W-1:0] tx_desc_vc;
  reg [16*TAG_W-1:0] tx_desc_tag;
  reg [16*ADDR_W-1:0] tx_desc_base_addr;
  reg [16*FLIT_COUNT_W-1:0] tx_desc_flit_count;
  wire [15:0] tx_desc_valid =
    (setup_state == INSTALL_TX) ? descriptor_pending : 16'h0000;
  wire [15:0] tx_desc_ready;

  reg [16*ENDPOINT_W-1:0] rx_desc_source;
  reg [16*VC_W-1:0] rx_desc_vc;
  reg [16*TAG_W-1:0] rx_desc_tag;
  reg [16*ADDR_W-1:0] rx_desc_base_addr;
  reg [16*FLIT_COUNT_W-1:0] rx_desc_flit_count;
  wire [15:0] rx_desc_valid =
    (setup_state == INSTALL_RX) ? descriptor_pending : 16'h0000;
  wire [15:0] rx_desc_ready;

  wire [15:0] tx_mem_req_valid;
  reg [15:0] tx_mem_req_ready;
  wire [16*ADDR_W-1:0] tx_mem_req_addr;
  reg [15:0] tx_mem_rsp_valid;
  wire [15:0] tx_mem_rsp_ready;
  reg [16*DATA_W-1:0] tx_mem_rsp_data;
  reg [DATA_W-1:0] source_data_state [0:NODES-1];

  wire [15:0] rx_mem_write_valid;
  reg [15:0] rx_mem_write_ready;
  wire [16*ADDR_W-1:0] rx_mem_write_addr;
  wire [16*DATA_W-1:0] rx_mem_write_data;
  wire [15:0] rx_completion_valid;
  reg [15:0] rx_completion_ready;
  wire [16*ENDPOINT_W-1:0] rx_completion_source;
  wire [16*VC_W-1:0] rx_completion_vc;
  wire [16*TAG_W-1:0] rx_completion_tag;
  wire [15:0] endpoint_protocol_error;

  wire [16*COUNTER_W-1:0] router_accepted_flit_count;
  wire [16*COUNTER_W-1:0] router_forwarded_flit_count;
  wire [16*COUNTER_W-1:0] router_input_stall_cycles;
  wire [16*COUNTER_W-1:0] router_output_stall_cycles;
  wire [16*COUNTER_W-1:0] router_contention_cycles;
  wire [16*COUNTER_W-1:0] router_current_input_occupancy;
  wire [16*COUNTER_W-1:0] router_max_input_occupancy;
  wire [16*5*COUNTER_W-1:0] router_route_flit_count;

  reg [15:0] observed_valid_q;
  reg [DATA_W-1:0] observed_q;
  integer node_i;

  function [ENDPOINT_W-1:0] destination_for_source;
    input [ENDPOINT_W-1:0] source;
    begin
      destination_for_source = source + 4'd5;
    end
  endfunction

  function [ENDPOINT_W-1:0] source_for_destination;
    input [ENDPOINT_W-1:0] destination;
    begin
      source_for_destination = destination + 4'd11;
    end
  endfunction

  function [FLIT_COUNT_W-1:0] count_for_source;
    input [ENDPOINT_W-1:0] source;
    begin
      count_for_source =
        {1'b0, (source[2:0] ^ {3{source[3]}})} + 1'b1;
    end
  endfunction

  function [VC_W-1:0] vc_for_source;
    input [ENDPOINT_W-1:0] source;
    begin
      vc_for_source = source[1:0] ^ source[3:2];
    end
  endfunction

  function [TAG_W-1:0] tag_for_source;
    input [ENDPOINT_W-1:0] source;
    begin
      tag_for_source = {epoch[3:0], source};
    end
  endfunction

  function [ADDR_W-1:0] tx_base_for_source;
    input [ENDPOINT_W-1:0] source;
    begin
      tx_base_for_source =
        ({{(ADDR_W-ENDPOINT_W){1'b0}}, source} << 12) |
        ({{(ADDR_W-8){1'b0}}, epoch} << 4);
    end
  endfunction

  function [ADDR_W-1:0] rx_base_for_destination;
    input [ENDPOINT_W-1:0] destination;
    begin
      rx_base_for_destination =
        ({{(ADDR_W-1){1'b0}}, 1'b1} << (ADDR_W - 1)) |
        ({{(ADDR_W-ENDPOINT_W){1'b0}}, destination} << 12) |
        ({{(ADDR_W-8){1'b0}}, epoch} << 4);
    end
  endfunction

  function [DATA_W-1:0] advance_data;
    input [DATA_W-1:0] value;
    begin
      advance_data = {
        value[DATA_W-2:0],
        value[DATA_W-1] ^ value[(DATA_W/2)-1] ^ value[21] ^ value[5] ^ value[0]
      };
    end
  endfunction

  function [5:0] popcount16;
    input [15:0] value;
    integer bit_i;
    begin
      popcount16 = 0;
      for (bit_i = 0; bit_i < 16; bit_i = bit_i + 1)
        popcount16 = popcount16 + {{5{1'b0}}, value[bit_i]};
    end
  endfunction

  assign observed_valid = observed_valid_q;
  assign observed_flit = observed_q;
  assign issued_packet_count = issued_count_q;
  assign completed_packet_count = completed_count_q;
  assign protocol_error = |endpoint_protocol_error;

  always @(*) begin
    tx_desc_destination = 0;
    tx_desc_vc = 0;
    tx_desc_tag = 0;
    tx_desc_base_addr = 0;
    tx_desc_flit_count = 0;
    rx_desc_source = 0;
    rx_desc_vc = 0;
    rx_desc_tag = 0;
    rx_desc_base_addr = 0;
    rx_desc_flit_count = 0;
    tx_mem_req_ready = 0;
    rx_mem_write_ready = 0;
    rx_completion_ready = 0;
    for (node_i = 0; node_i < NODES; node_i = node_i + 1) begin
      tx_desc_destination[(node_i*ENDPOINT_W) +: ENDPOINT_W] =
        destination_for_source(node_i[ENDPOINT_W-1:0]);
      tx_desc_vc[(node_i*VC_W) +: VC_W] =
        vc_for_source(node_i[ENDPOINT_W-1:0]);
      tx_desc_tag[(node_i*TAG_W) +: TAG_W] =
        tag_for_source(node_i[ENDPOINT_W-1:0]);
      tx_desc_base_addr[(node_i*ADDR_W) +: ADDR_W] =
        tx_base_for_source(node_i[ENDPOINT_W-1:0]);
      tx_desc_flit_count[(node_i*FLIT_COUNT_W) +: FLIT_COUNT_W] =
        count_for_source(node_i[ENDPOINT_W-1:0]);

      rx_desc_source[(node_i*ENDPOINT_W) +: ENDPOINT_W] =
        source_for_destination(node_i[ENDPOINT_W-1:0]);
      rx_desc_vc[(node_i*VC_W) +: VC_W] =
        vc_for_source(source_for_destination(node_i[ENDPOINT_W-1:0]));
      rx_desc_tag[(node_i*TAG_W) +: TAG_W] =
        tag_for_source(source_for_destination(node_i[ENDPOINT_W-1:0]));
      rx_desc_base_addr[(node_i*ADDR_W) +: ADDR_W] =
        rx_base_for_destination(node_i[ENDPOINT_W-1:0]);
      rx_desc_flit_count[(node_i*FLIT_COUNT_W) +: FLIT_COUNT_W] =
        count_for_source(source_for_destination(node_i[ENDPOINT_W-1:0]));

      tx_mem_req_ready[node_i] =
        (!tx_mem_rsp_valid[node_i] || tx_mem_rsp_ready[node_i]) &&
        (cycle_count_q[2:0] != node_i[2:0]);
      rx_mem_write_ready[node_i] =
        cycle_count_q[2:0] != (node_i[2:0] ^ 3'b101);
      rx_completion_ready[node_i] =
        cycle_count_q[3:1] != node_i[2:0];
    end
  end

  noc_sram_packet_mesh4x4 #(
    .DATA_W(DATA_W),
    .ADDR_W(ADDR_W),
    .TX_DESC_DEPTH(TX_DESC_DEPTH),
    .TX_OUTSTANDING(TX_OUTSTANDING),
    .RX_CONTEXTS(RX_CONTEXTS),
    .ROUTER_FIFO_DEPTH(ROUTER_FIFO_DEPTH),
    .COUNTER_W(COUNTER_W)
  ) composition (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .rx_mem_write_valid(rx_mem_write_valid), .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr), .rx_mem_write_data(rx_mem_write_data),
    .rx_completion_valid(rx_completion_valid),
    .rx_completion_ready(rx_completion_ready),
    .rx_completion_source(rx_completion_source),
    .rx_completion_vc(rx_completion_vc),
    .rx_completion_tag(rx_completion_tag),
    .endpoint_protocol_error(endpoint_protocol_error),
    .router_accepted_flit_count(router_accepted_flit_count),
    .router_forwarded_flit_count(router_forwarded_flit_count),
    .router_input_stall_cycles(router_input_stall_cycles),
    .router_output_stall_cycles(router_output_stall_cycles),
    .router_contention_cycles(router_contention_cycles),
    .router_current_input_occupancy(router_current_input_occupancy),
    .router_max_input_occupancy(router_max_input_occupancy),
    .router_route_flit_count(router_route_flit_count)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      setup_state <= INSTALL_RX;
      epoch <= 0;
      descriptor_pending <= 16'hffff;
      completion_seen <= 0;
      issued_count_q <= 0;
      completed_count_q <= 0;
      cycle_count_q <= 0;
      tx_mem_rsp_valid <= 0;
      tx_mem_rsp_data <= 0;
      observed_valid_q <= 0;
      observed_q <= 0;
      for (node_i = 0; node_i < NODES; node_i = node_i + 1)
        source_data_state[node_i] <= {{(DATA_W-5){1'b0}}, node_i[3:0], 1'b1};
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
      observed_valid_q <= rx_mem_write_valid & rx_mem_write_ready;

      issued_count_q <= issued_count_q +
        {{(COUNTER_W-6){1'b0}}, popcount16(tx_desc_valid & tx_desc_ready)};
      completed_count_q <= completed_count_q +
        {{(COUNTER_W-6){1'b0}},
         popcount16(rx_completion_valid & rx_completion_ready)};

      case (setup_state)
        INSTALL_RX: begin
          descriptor_pending <= descriptor_pending & ~rx_desc_ready;
          if ((descriptor_pending & ~rx_desc_ready) == 0) begin
            descriptor_pending <= 16'hffff;
            setup_state <= INSTALL_TX;
          end
        end
        INSTALL_TX: begin
          descriptor_pending <= descriptor_pending & ~tx_desc_ready;
          if ((descriptor_pending & ~tx_desc_ready) == 0) begin
            descriptor_pending <= 0;
            completion_seen <= 0;
            setup_state <= RUN_PACKETS;
          end
        end
        default: begin
          completion_seen <= completion_seen |
            (rx_completion_valid & rx_completion_ready);
          if ((completion_seen |
               (rx_completion_valid & rx_completion_ready)) == 16'hffff) begin
            epoch <= epoch + 1'b1;
            descriptor_pending <= 16'hffff;
            completion_seen <= 0;
            setup_state <= INSTALL_RX;
          end
        end
      endcase

      for (node_i = 0; node_i < NODES; node_i = node_i + 1) begin
        if (tx_mem_req_valid[node_i] && tx_mem_req_ready[node_i]) begin
          tx_mem_rsp_valid[node_i] <= 1'b1;
          tx_mem_rsp_data[(node_i*DATA_W) +: DATA_W] <=
            advance_data(source_data_state[node_i]) ^
            {{(DATA_W-ADDR_W){1'b0}},
             tx_mem_req_addr[(node_i*ADDR_W) +: ADDR_W]};
          source_data_state[node_i] <= advance_data(source_data_state[node_i]);
        end else if (tx_mem_rsp_valid[node_i] && tx_mem_rsp_ready[node_i]) begin
          tx_mem_rsp_valid[node_i] <= 1'b0;
        end

        if ((rx_mem_write_valid[node_i] && rx_mem_write_ready[node_i]) ||
            (rx_completion_valid[node_i] && rx_completion_ready[node_i])) begin
          observed_q[(node_i*OBSERVE_SLICE_W) +: OBSERVE_SLICE_W] <=
            ((rx_mem_write_valid[node_i] && rx_mem_write_ready[node_i]) ?
              (rx_mem_write_data[
                 (node_i*DATA_W) + (epoch[3:0]*OBSERVE_SLICE_W) +: OBSERVE_SLICE_W
               ] ^ rx_mem_write_addr[(node_i*ADDR_W) +: OBSERVE_SLICE_W]) :
              observed_q[(node_i*OBSERVE_SLICE_W) +: OBSERVE_SLICE_W]) ^
            ((rx_completion_valid[node_i] && rx_completion_ready[node_i]) ?
              {2'b0,
               rx_completion_source[(node_i*ENDPOINT_W) +: ENDPOINT_W],
               rx_completion_vc[(node_i*VC_W) +: VC_W],
               rx_completion_tag[(node_i*TAG_W) +: TAG_W]} :
              {OBSERVE_SLICE_W{1'b0}});
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || DATA_W % NODES != 0 || ADDR_W < OBSERVE_SLICE_W ||
        COUNTER_W < 6 || OBSERVE_SLICE_W != 16) begin
      $error("noc_sram_packet_mesh4x4_ppa_harness parameter contract violated");
      $finish(1);
    end
  end
`endif
endmodule
