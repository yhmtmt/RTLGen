`timescale 1ns/1ps

// Complete VC0 shared-SRAM transport service. Producer residency events are
// admitted into exact stream contexts, expanded into endpoint-local packet
// descriptors, transported through the 4x4 mesh, and retired only after the
// destination SRAM accepts every flit and the consumer accepts completion.
module attention_shared_stream_context_service #(
  parameter integer ADDR_W = 32,
  parameter integer MAX_PACKETS_PER_CONTEXT = 68,
  parameter integer PACKET_INDEX_W = 7,
  parameter integer TAG_W = 8,
  parameter integer TX_DESC_DEPTH = 8
) (
  input wire clk,
  input wire rst_n,
  input wire layer_start,
  input wire layer_idle,
  input wire [7:0] layer_expected_remote_contexts,
  input wire [15:0] event_valid,
  output wire [15:0] event_ready,
  input wire [16*3-1:0] event_wave,
  input wire [16*4-1:0] event_source,
  input wire [16*ADDR_W-1:0] event_source_base_addr,
  input wire [16*ADDR_W-1:0] event_destination_base_addr,
  input wire [16*(PACKET_INDEX_W+1)-1:0] event_packet_count,

  input wire completion_ready,
  output wire completion_valid,
  output wire [2:0] completion_wave,
  output wire [3:0] completion_destination,

  output wire [15:0] tx_mem_req_valid,
  input wire [15:0] tx_mem_req_ready,
  output wire [16*ADDR_W-1:0] tx_mem_req_addr,
  input wire [15:0] tx_mem_rsp_valid,
  output wire [15:0] tx_mem_rsp_ready,
  input wire [16*256-1:0] tx_mem_rsp_data,
  output wire [15:0] rx_mem_write_valid,
  input wire [15:0] rx_mem_write_ready,
  output wire [16*ADDR_W-1:0] rx_mem_write_addr,
  output wire [16*256-1:0] rx_mem_write_data,

  output wire context_valid,
  output wire context_ready,
  output wire [2:0] context_wave,
  output wire [3:0] context_destination,
  output wire [3:0] context_source,
  output wire [ADDR_W-1:0] context_source_base_addr,
  output wire [ADDR_W-1:0] context_destination_base_addr,
  output wire [PACKET_INDEX_W:0] context_packet_count,
  output wire admission_complete,
  output reg transport_complete,
  output wire [7:0] admitted_count,
  output reg [7:0] completed_count,
  output wire [15:0] endpoint_protocol_error,
  output wire protocol_error
);
  wire layer_active_w;
  wire admission_error_w;
  wire engine_error_w;
  reg [7:0] expected_contexts_q;

  wire [15:0] unused_tx_desc_valid;
  wire [15:0] unused_tx_desc_ready;
  wire [16*4-1:0] unused_tx_desc_destination;
  wire [16*2-1:0] unused_tx_desc_vc;
  wire [16*8-1:0] unused_tx_desc_tag;
  wire [16*ADDR_W-1:0] unused_tx_desc_base_addr;
  wire [16*4-1:0] unused_tx_desc_flit_count;
  wire [15:0] unused_rx_desc_valid;
  wire [15:0] unused_rx_desc_ready;
  wire [16*4-1:0] unused_rx_desc_source;
  wire [16*2-1:0] unused_rx_desc_vc;
  wire [16*8-1:0] unused_rx_desc_tag;
  wire [16*ADDR_W-1:0] unused_rx_desc_base_addr;
  wire [16*4-1:0] unused_rx_desc_flit_count;

  attention_shared_stream_context_admission #(
    .ADDR_W(ADDR_W),
    .MAX_PACKETS_PER_CONTEXT(MAX_PACKETS_PER_CONTEXT),
    .PACKET_INDEX_W(PACKET_INDEX_W)
  ) admission (
    .clk(clk), .rst_n(rst_n),
    .layer_start(layer_start), .layer_idle(layer_idle),
    .layer_expected_remote_contexts(layer_expected_remote_contexts),
    .event_valid(event_valid), .event_ready(event_ready),
    .event_wave(event_wave), .event_source(event_source),
    .event_source_base_addr(event_source_base_addr),
    .event_destination_base_addr(event_destination_base_addr),
    .event_packet_count(event_packet_count),
    .context_valid(context_valid), .context_ready(context_ready),
    .context_wave(context_wave), .context_destination(context_destination),
    .context_cluster(), .context_source(context_source),
    .context_source_base_addr(context_source_base_addr),
    .context_destination_base_addr(context_destination_base_addr),
    .context_packet_count(context_packet_count),
    .layer_active(layer_active_w), .layer_complete(admission_complete),
    .admitted_count(admitted_count), .protocol_error(admission_error_w)
  );

  attention_shared_stream_context_engine #(
    .ADDR_W(ADDR_W),
    .MAX_PACKETS_PER_CONTEXT(MAX_PACKETS_PER_CONTEXT),
    .PACKET_INDEX_W(PACKET_INDEX_W),
    .TAG_W(TAG_W),
    .TX_DESC_DEPTH(TX_DESC_DEPTH)
  ) engine (
    .clk(clk), .rst_n(rst_n),
    .context_valid(context_valid), .context_ready(context_ready),
    .context_wave(context_wave), .context_destination(context_destination),
    .context_source(context_source),
    .context_source_base_addr(context_source_base_addr),
    .context_destination_base_addr(context_destination_base_addr),
    .context_packet_count(context_packet_count),
    .context_completion_valid(completion_valid),
    .context_completion_ready(completion_ready),
    .context_completion_wave(completion_wave),
    .context_completion_destination(completion_destination),
    .tx_desc_valid(unused_tx_desc_valid), .tx_desc_ready(unused_tx_desc_ready),
    .tx_desc_destination(unused_tx_desc_destination), .tx_desc_vc(unused_tx_desc_vc),
    .tx_desc_tag(unused_tx_desc_tag), .tx_desc_base_addr(unused_tx_desc_base_addr),
    .tx_desc_flit_count(unused_tx_desc_flit_count),
    .rx_desc_valid(unused_rx_desc_valid), .rx_desc_ready(unused_rx_desc_ready),
    .rx_desc_source(unused_rx_desc_source), .rx_desc_vc(unused_rx_desc_vc),
    .rx_desc_tag(unused_rx_desc_tag), .rx_desc_base_addr(unused_rx_desc_base_addr),
    .rx_desc_flit_count(unused_rx_desc_flit_count),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr), .rx_mem_write_data(rx_mem_write_data),
    .endpoint_protocol_error(endpoint_protocol_error), .protocol_error(engine_error_w)
  );

  assign protocol_error = admission_error_w | engine_error_w;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      expected_contexts_q <= 8'b0;
      completed_count <= 8'b0;
      transport_complete <= 1'b0;
    end else begin
      if (layer_start && layer_idle && !protocol_error) begin
        expected_contexts_q <= layer_expected_remote_contexts;
        completed_count <= 8'b0;
        transport_complete <= (layer_expected_remote_contexts == 0);
      end
      if (completion_valid && completion_ready && !protocol_error) begin
        completed_count <= completed_count + 1'b1;
        if (completed_count == expected_contexts_q - 1'b1)
          transport_complete <= 1'b1;
      end
    end
  end

`ifndef SYNTHESIS
  always @(posedge clk) begin
    if (rst_n && completion_valid && completion_ready &&
        completed_count >= expected_contexts_q)
      $error("shared-stream service observed excess context completion");
  end
`endif
endmodule
