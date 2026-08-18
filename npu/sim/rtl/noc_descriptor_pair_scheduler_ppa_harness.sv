`timescale 1ns/1ps

module noc_descriptor_pair_scheduler_ppa_harness #(
  parameter integer NODES = 16,
  parameter integer DATA_W = 256,
  parameter integer COUNTER_W = 32
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
  reg [31:0] current_cycle;
  reg cmd_valid;
  wire cmd_ready;
  reg [31:0] cmd_release_cycle;
  reg [3:0] cmd_source;
  reg [3:0] cmd_destination;
  reg [1:0] cmd_vc;
  reg [7:0] cmd_tag;
  reg [23:0] cmd_tx_base_addr;
  reg [23:0] cmd_rx_base_addr;
  reg [3:0] cmd_flit_count;
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
    .protocol_error(protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      current_cycle <= 0;
      cmd_valid <= 0;
      cmd_release_cycle <= 0;
      cmd_source <= 0;
      cmd_destination <= 1;
      cmd_vc <= 0;
      cmd_tag <= 8'h1d;
      cmd_tx_base_addr <= 24'h010000;
      cmd_rx_base_addr <= 24'h020000;
      cmd_flit_count <= 1;
      tx_desc_ready <= {NODES{1'b1}};
      rx_desc_ready <= {NODES{1'b1}};
      observed_state_r <= {DATA_W{1'b0}};
    end else begin
      current_cycle <= current_cycle + 1'b1;
      tx_desc_ready <= {NODES{1'b1}} ^
        ({{(NODES-1){1'b0}}, current_cycle[2]} << current_cycle[7:4]);
      rx_desc_ready <= {NODES{1'b1}} ^
        ({{(NODES-1){1'b0}}, current_cycle[3]} << current_cycle[11:8]);
      cmd_valid <= 1'b1;
      if (cmd_valid && cmd_ready) begin
        cmd_source <= cmd_source + 1'b1;
        cmd_destination <= cmd_destination + 4'd3;
        cmd_vc <= cmd_vc + 1'b1;
        cmd_tag <= {cmd_tag[6:0], cmd_tag[7] ^ cmd_tag[5]};
        cmd_tx_base_addr <= cmd_tx_base_addr + 24'h000120;
        cmd_rx_base_addr <= cmd_rx_base_addr + 24'h000220;
        cmd_flit_count <= cmd_flit_count == 4'd8 ? 4'd1 : cmd_flit_count + 1'b1;
        cmd_release_cycle <= current_cycle + {28'b0, cmd_tag[3:0]};
      end
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
