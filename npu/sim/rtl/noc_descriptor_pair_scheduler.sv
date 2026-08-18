`timescale 1ns/1ps

// Converts a producer-fed packet command stream into endpoint descriptors.
// Receive state is installed before the corresponding transmit descriptor is
// released, so packet arrival cannot race destination context allocation.
module noc_descriptor_pair_scheduler #(
  parameter integer NODES = 16,
  parameter integer ENDPOINT_W = 4,
  parameter integer VC_W = 2,
  parameter integer TAG_W = 8,
  parameter integer ADDR_W = 24,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer RELEASE_W = 32,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,
  input wire [RELEASE_W-1:0] current_cycle,

  input wire cmd_valid,
  output wire cmd_ready,
  input wire [RELEASE_W-1:0] cmd_release_cycle,
  input wire [ENDPOINT_W-1:0] cmd_source,
  input wire [ENDPOINT_W-1:0] cmd_destination,
  input wire [VC_W-1:0] cmd_vc,
  input wire [TAG_W-1:0] cmd_tag,
  input wire [ADDR_W-1:0] cmd_tx_base_addr,
  input wire [ADDR_W-1:0] cmd_rx_base_addr,
  input wire [FLIT_COUNT_W-1:0] cmd_flit_count,

  output reg [NODES-1:0] tx_desc_valid,
  input wire [NODES-1:0] tx_desc_ready,
  output reg [NODES*ENDPOINT_W-1:0] tx_desc_destination,
  output reg [NODES*VC_W-1:0] tx_desc_vc,
  output reg [NODES*TAG_W-1:0] tx_desc_tag,
  output reg [NODES*ADDR_W-1:0] tx_desc_base_addr,
  output reg [NODES*FLIT_COUNT_W-1:0] tx_desc_flit_count,

  output reg [NODES-1:0] rx_desc_valid,
  input wire [NODES-1:0] rx_desc_ready,
  output reg [NODES*ENDPOINT_W-1:0] rx_desc_source,
  output reg [NODES*VC_W-1:0] rx_desc_vc,
  output reg [NODES*TAG_W-1:0] rx_desc_tag,
  output reg [NODES*ADDR_W-1:0] rx_desc_base_addr,
  output reg [NODES*FLIT_COUNT_W-1:0] rx_desc_flit_count,

  output reg [COUNTER_W-1:0] accepted_command_count,
  output reg [COUNTER_W-1:0] installed_receive_count,
  output reg [COUNTER_W-1:0] submitted_transmit_count,
  output reg [COUNTER_W-1:0] release_wait_cycles,
  output reg [COUNTER_W-1:0] endpoint_stall_cycles,
  output reg protocol_error
);
  reg command_active;
  reg receive_installed;
  reg [RELEASE_W-1:0] active_release_cycle;
  reg [ENDPOINT_W-1:0] active_source;
  reg [ENDPOINT_W-1:0] active_destination;
  reg [VC_W-1:0] active_vc;
  reg [TAG_W-1:0] active_tag;
  reg [ADDR_W-1:0] active_tx_base_addr;
  reg [ADDR_W-1:0] active_rx_base_addr;
  reg [FLIT_COUNT_W-1:0] active_flit_count;

  wire command_released = command_active && current_cycle >= active_release_cycle;
  wire receive_valid = command_released && !receive_installed;
  wire transmit_valid = command_released && receive_installed;
  wire receive_fire = receive_valid && rx_desc_ready[active_destination];
  wire transmit_fire = transmit_valid && tx_desc_ready[active_source];
  wire [ENDPOINT_W:0] command_source_extended = {1'b0, cmd_source};
  wire [ENDPOINT_W:0] command_destination_extended = {1'b0, cmd_destination};
  localparam [ENDPOINT_W:0] NODE_COUNT = NODES[ENDPOINT_W:0];
  wire command_fields_valid =
    cmd_flit_count != {FLIT_COUNT_W{1'b0}} &&
    command_source_extended < NODE_COUNT &&
    command_destination_extended < NODE_COUNT;

  // A completing transmit can be replaced without an idle queue cycle.
  assign cmd_ready = !command_active || transmit_fire;

  always @(*) begin
    tx_desc_valid = {NODES{1'b0}};
    tx_desc_destination = {(NODES*ENDPOINT_W){1'b0}};
    tx_desc_vc = {(NODES*VC_W){1'b0}};
    tx_desc_tag = {(NODES*TAG_W){1'b0}};
    tx_desc_base_addr = {(NODES*ADDR_W){1'b0}};
    tx_desc_flit_count = {(NODES*FLIT_COUNT_W){1'b0}};
    rx_desc_valid = {NODES{1'b0}};
    rx_desc_source = {(NODES*ENDPOINT_W){1'b0}};
    rx_desc_vc = {(NODES*VC_W){1'b0}};
    rx_desc_tag = {(NODES*TAG_W){1'b0}};
    rx_desc_base_addr = {(NODES*ADDR_W){1'b0}};
    rx_desc_flit_count = {(NODES*FLIT_COUNT_W){1'b0}};

    if (receive_valid) begin
      rx_desc_valid[active_destination] = 1'b1;
      rx_desc_source[(active_destination*ENDPOINT_W) +: ENDPOINT_W] = active_source;
      rx_desc_vc[(active_destination*VC_W) +: VC_W] = active_vc;
      rx_desc_tag[(active_destination*TAG_W) +: TAG_W] = active_tag;
      rx_desc_base_addr[(active_destination*ADDR_W) +: ADDR_W] = active_rx_base_addr;
      rx_desc_flit_count[(active_destination*FLIT_COUNT_W) +: FLIT_COUNT_W] = active_flit_count;
    end
    if (transmit_valid) begin
      tx_desc_valid[active_source] = 1'b1;
      tx_desc_destination[(active_source*ENDPOINT_W) +: ENDPOINT_W] = active_destination;
      tx_desc_vc[(active_source*VC_W) +: VC_W] = active_vc;
      tx_desc_tag[(active_source*TAG_W) +: TAG_W] = active_tag;
      tx_desc_base_addr[(active_source*ADDR_W) +: ADDR_W] = active_tx_base_addr;
      tx_desc_flit_count[(active_source*FLIT_COUNT_W) +: FLIT_COUNT_W] = active_flit_count;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      command_active <= 1'b0;
      receive_installed <= 1'b0;
      active_release_cycle <= {RELEASE_W{1'b0}};
      active_source <= {ENDPOINT_W{1'b0}};
      active_destination <= {ENDPOINT_W{1'b0}};
      active_vc <= {VC_W{1'b0}};
      active_tag <= {TAG_W{1'b0}};
      active_tx_base_addr <= {ADDR_W{1'b0}};
      active_rx_base_addr <= {ADDR_W{1'b0}};
      active_flit_count <= {FLIT_COUNT_W{1'b0}};
      accepted_command_count <= {COUNTER_W{1'b0}};
      installed_receive_count <= {COUNTER_W{1'b0}};
      submitted_transmit_count <= {COUNTER_W{1'b0}};
      release_wait_cycles <= {COUNTER_W{1'b0}};
      endpoint_stall_cycles <= {COUNTER_W{1'b0}};
      protocol_error <= 1'b0;
    end else begin
      if (command_active && current_cycle < active_release_cycle)
        release_wait_cycles <= release_wait_cycles + 1'b1;
      if ((receive_valid && !rx_desc_ready[active_destination]) ||
          (transmit_valid && !tx_desc_ready[active_source]))
        endpoint_stall_cycles <= endpoint_stall_cycles + 1'b1;

      if (receive_fire) begin
        receive_installed <= 1'b1;
        installed_receive_count <= installed_receive_count + 1'b1;
      end
      if (transmit_fire) begin
        command_active <= 1'b0;
        receive_installed <= 1'b0;
        submitted_transmit_count <= submitted_transmit_count + 1'b1;
      end

      if (cmd_valid && cmd_ready) begin
        accepted_command_count <= accepted_command_count + 1'b1;
        if (!command_fields_valid) begin
          command_active <= 1'b0;
          receive_installed <= 1'b0;
          protocol_error <= 1'b1;
        end else begin
          command_active <= 1'b1;
          receive_installed <= 1'b0;
          active_release_cycle <= cmd_release_cycle;
          active_source <= cmd_source;
          active_destination <= cmd_destination;
          active_vc <= cmd_vc;
          active_tag <= cmd_tag;
          active_tx_base_addr <= cmd_tx_base_addr;
          active_rx_base_addr <= cmd_rx_base_addr;
          active_flit_count <= cmd_flit_count;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (NODES <= 1 || (1 << ENDPOINT_W) < NODES) begin
      $error("noc_descriptor_pair_scheduler endpoint width cannot represent NODES");
      $finish(1);
    end
  end
`endif
endmodule
