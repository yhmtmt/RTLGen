`timescale 1ns/1ps

module noc_descriptor_pair_scheduler_ppa_harness #(
  parameter integer NODES = 16,
  parameter integer DATA_W = 256,
  parameter integer COUNTER_W = 32,
  parameter bit GENERATED_SOURCE = 1'b0
) (
  input wire clk,
  input wire rst_n,
  output wire [COUNTER_W-1:0] accepted_command_count,
  output wire [COUNTER_W-1:0] installed_receive_count,
  output wire [COUNTER_W-1:0] submitted_transmit_count,
  output wire [COUNTER_W-1:0] endpoint_stall_cycles,
  output wire protocol_error,
  output wire [DATA_W-1:0] observed_state
);
  localparam integer COMMAND_W = 102;
  reg [31:0] current_cycle;
  wire cmd_valid;
  wire cmd_ready;
  wire [COMMAND_W-1:0] cmd_data;
  wire [31:0] cmd_release_cycle = cmd_data[31:0];
  wire [3:0] cmd_source = cmd_data[35:32];
  wire [3:0] cmd_destination = cmd_data[39:36];
  wire [1:0] cmd_vc = cmd_data[41:40];
  wire [7:0] cmd_tag = cmd_data[49:42];
  wire [23:0] cmd_tx_base_addr = cmd_data[73:50];
  wire [23:0] cmd_rx_base_addr = cmd_data[97:74];
  wire [3:0] cmd_flit_count = cmd_data[101:98];
  wire command_source_protocol_error;
  wire scheduler_protocol_error;
  wire [NODES-1:0] tx_desc_valid;
  reg [NODES-1:0] tx_desc_ready;
  wire [NODES*4-1:0] tx_desc_destination;
  wire [NODES*2-1:0] tx_desc_vc;
  wire [NODES*8-1:0] tx_desc_tag;
  wire [NODES*24-1:0] tx_desc_base_addr;
  wire [NODES*4-1:0] tx_desc_flit_count;
  wire [NODES-1:0] rx_desc_valid;
  reg [NODES-1:0] rx_desc_ready;
  wire [NODES*4-1:0] rx_desc_source;
  wire [NODES*2-1:0] rx_desc_vc;
  wire [NODES*8-1:0] rx_desc_tag;
  wire [NODES*24-1:0] rx_desc_base_addr;
  wire [NODES*4-1:0] rx_desc_flit_count;
  wire [COUNTER_W-1:0] release_wait_cycles;
  reg [DATA_W-1:0] observed_state_r;
  reg [3:0] tx_observed_index;
  reg [3:0] rx_observed_index;
  integer observed_i;

  assign observed_state = observed_state_r;
  assign protocol_error = command_source_protocol_error | scheduler_protocol_error;

  always @(*) begin
    tx_observed_index = 4'b0;
    rx_observed_index = 4'b0;
    for (observed_i = 0; observed_i < NODES; observed_i = observed_i + 1) begin
      if (tx_desc_valid[observed_i] && tx_desc_ready[observed_i])
        tx_observed_index = observed_i[3:0];
      if (rx_desc_valid[observed_i] && rx_desc_ready[observed_i])
        rx_observed_index = observed_i[3:0];
    end
  end

  generate
    if (GENERATED_SOURCE) begin : generated_command_source
      wire generated_done;
      wire [COUNTER_W-1:0] generated_command_count;
      wire generated_protocol_error;
      assign command_source_protocol_error = generated_protocol_error;
      noc_llama7b_phase2_command_generator #(
        .COMMAND_W(COMMAND_W),
        .COUNTER_W(COUNTER_W)
      ) generator (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_data(cmd_data),
        .done(generated_done),
        .generated_command_count(generated_command_count),
        .protocol_error(generated_protocol_error)
      );
    end else begin : prefetched_command_source
      wire command_mem_req_valid;
      reg command_mem_req_ready;
      wire [13:0] command_mem_req_addr;
      wire command_mem_rsp_valid;
      wire command_mem_rsp_ready;
      wire [COMMAND_W-1:0] command_mem_rsp_data;
      reg [13:0] pending_command_addr;
      reg pending_command_valid;
      wire [COUNTER_W-1:0] prefetch_request_count;
      wire [COUNTER_W-1:0] prefetch_response_count;
      wire [COUNTER_W-1:0] prefetch_delivered_count;
      wire [COUNTER_W-1:0] prefetch_memory_stalls;
      wire prefetch_protocol_error;
      assign command_source_protocol_error = prefetch_protocol_error;
      assign command_mem_rsp_valid = pending_command_valid;
      assign command_mem_rsp_data = command_word(pending_command_addr);

      function [COMMAND_W-1:0] command_word;
        input [13:0] address;
        reg [3:0] source;
        reg [3:0] destination;
        reg [3:0] flit_count;
        begin
          source = address[3:0];
          destination = address[7:4] + address[3:0] + 1'b1;
          flit_count = {1'b0, address[2:0]} + 1'b1;
          command_word = {
            flit_count,
            {address, 10'h155},
            {address, 10'h0aa},
            address[7:0] ^ 8'h5a,
            address[1:0],
            destination,
            source,
            {18'b0, address}
          };
        end
      endfunction

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          command_mem_req_ready <= 1'b1;
          pending_command_addr <= 0;
          pending_command_valid <= 1'b0;
        end else begin
          command_mem_req_ready <= !current_cycle[4] || current_cycle[1];
          if (pending_command_valid && command_mem_rsp_ready)
            pending_command_valid <= 1'b0;
          if (command_mem_req_valid && command_mem_req_ready) begin
            pending_command_addr <= command_mem_req_addr;
            pending_command_valid <= 1'b1;
          end
        end
      end

      noc_descriptor_command_prefetch #(
        .COMMAND_W(COMMAND_W),
        .ADDR_W(14),
        .COUNT_W(14),
        .COUNTER_W(COUNTER_W)
      ) prefetch (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .command_count(14'h3fff),
        .mem_req_valid(command_mem_req_valid),
        .mem_req_ready(command_mem_req_ready),
        .mem_req_addr(command_mem_req_addr),
        .mem_rsp_valid(command_mem_rsp_valid),
        .mem_rsp_ready(command_mem_rsp_ready),
        .mem_rsp_data(command_mem_rsp_data),
        .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_data(cmd_data),
        .request_count(prefetch_request_count),
        .response_count(prefetch_response_count),
        .delivered_command_count(prefetch_delivered_count),
        .memory_stall_cycles(prefetch_memory_stalls),
        .protocol_error(prefetch_protocol_error)
      );
    end
  endgenerate

  noc_descriptor_pair_scheduler #(
    .NODES(NODES),
    .COUNTER_W(COUNTER_W)
  ) scheduler (
    .clk(clk), .rst_n(rst_n), .current_cycle(current_cycle),
    .cmd_valid(cmd_valid), .cmd_ready(cmd_ready),
    .cmd_release_cycle(cmd_release_cycle), .cmd_source(cmd_source),
    .cmd_destination(cmd_destination), .cmd_vc(cmd_vc), .cmd_tag(cmd_tag),
    .cmd_tx_base_addr(cmd_tx_base_addr), .cmd_rx_base_addr(cmd_rx_base_addr),
    .cmd_flit_count(cmd_flit_count),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .accepted_command_count(accepted_command_count),
    .installed_receive_count(installed_receive_count),
    .submitted_transmit_count(submitted_transmit_count),
    .release_wait_cycles(release_wait_cycles),
    .endpoint_stall_cycles(endpoint_stall_cycles),
    .protocol_error(scheduler_protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      current_cycle <= GENERATED_SOURCE ? 32'd400000 : 32'd0;
      tx_desc_ready <= {NODES{1'b1}};
      rx_desc_ready <= {NODES{1'b1}};
      observed_state_r <= {DATA_W{1'b0}};
    end else begin
      current_cycle <= current_cycle + 1'b1;
      tx_desc_ready <= {NODES{1'b1}} ^
        ({{(NODES-1){1'b0}}, current_cycle[2]} << current_cycle[7:4]);
      rx_desc_ready <= {NODES{1'b1}} ^
        ({{(NODES-1){1'b0}}, current_cycle[3]} << current_cycle[11:8]);
      if (|(tx_desc_valid & tx_desc_ready))
        observed_state_r <= {observed_state_r[DATA_W-2:0], observed_state_r[DATA_W-1]} ^
          {{(DATA_W-42){1'b0}},
           tx_desc_tag[(tx_observed_index*8) +: 8],
           tx_desc_base_addr[(tx_observed_index*24) +: 24],
           tx_desc_destination[(tx_observed_index*4) +: 4],
           tx_desc_vc[(tx_observed_index*2) +: 2],
           tx_desc_flit_count[(tx_observed_index*4) +: 4]};
      if (|(rx_desc_valid & rx_desc_ready))
        observed_state_r <= {observed_state_r[DATA_W-3:0], observed_state_r[DATA_W-1:DATA_W-2]} ^
          {{(DATA_W-42){1'b0}},
           rx_desc_tag[(rx_observed_index*8) +: 8],
           rx_desc_base_addr[(rx_observed_index*24) +: 24],
           rx_desc_source[(rx_observed_index*4) +: 4],
           rx_desc_vc[(rx_observed_index*2) +: 2],
           rx_desc_flit_count[(rx_observed_index*4) +: 4]};
    end
  end
endmodule
