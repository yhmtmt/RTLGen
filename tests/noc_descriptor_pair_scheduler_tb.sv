`timescale 1ns/1ps

module noc_descriptor_pair_scheduler_tb;
  localparam integer NODES = 16;
  reg clk = 0;
  reg rst_n = 0;
  reg [31:0] current_cycle = 0;
  reg cmd_valid = 0;
  wire cmd_ready;
  reg [31:0] cmd_release_cycle = 0;
  reg [3:0] cmd_source = 0;
  reg [3:0] cmd_destination = 0;
  reg [1:0] cmd_vc = 0;
  reg [7:0] cmd_tag = 0;
  reg [23:0] cmd_tx_base_addr = 0;
  reg [23:0] cmd_rx_base_addr = 0;
  reg [3:0] cmd_flit_count = 0;
  wire [NODES-1:0] tx_desc_valid;
  reg [NODES-1:0] tx_desc_ready = {NODES{1'b1}};
  wire [NODES*4-1:0] tx_desc_destination;
  wire [NODES*2-1:0] tx_desc_vc;
  wire [NODES*8-1:0] tx_desc_tag;
  wire [NODES*24-1:0] tx_desc_base_addr;
  wire [NODES*4-1:0] tx_desc_flit_count;
  wire [NODES-1:0] rx_desc_valid;
  reg [NODES-1:0] rx_desc_ready = {NODES{1'b1}};
  wire [NODES*4-1:0] rx_desc_source;
  wire [NODES*2-1:0] rx_desc_vc;
  wire [NODES*8-1:0] rx_desc_tag;
  wire [NODES*24-1:0] rx_desc_base_addr;
  wire [NODES*4-1:0] rx_desc_flit_count;
  wire [31:0] accepted_command_count;
  wire [31:0] installed_receive_count;
  wire [31:0] submitted_transmit_count;
  wire [31:0] release_wait_cycles;
  wire [31:0] endpoint_stall_cycles;
  wire protocol_error;
  integer rx_cycle [0:1];
  integer tx_cycle [0:1];
  integer rx_seen = 0;
  integer tx_seen = 0;

  noc_descriptor_pair_scheduler dut (
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

  always #1 clk = ~clk;
  always @(posedge clk) begin
    if (rst_n)
      current_cycle <= current_cycle + 1;
    if (rst_n && |(rx_desc_valid & rx_desc_ready)) begin
      $display("RX_FIRE cycle=%0d valid=%h ready=%h", current_cycle, rx_desc_valid, rx_desc_ready);
      rx_cycle[rx_seen] = current_cycle;
      rx_seen = rx_seen + 1;
    end
    if (rst_n && |(tx_desc_valid & tx_desc_ready)) begin
      $display("TX_FIRE cycle=%0d valid=%h ready=%h", current_cycle, tx_desc_valid, tx_desc_ready);
      tx_cycle[tx_seen] = current_cycle;
      tx_seen = tx_seen + 1;
    end
  end

  task submit;
    input [31:0] release_cycle;
    input [3:0] source;
    input [3:0] destination;
    input [7:0] tag;
    begin
      @(negedge clk);
      cmd_release_cycle = release_cycle;
      cmd_source = source;
      cmd_destination = destination;
      cmd_vc = tag[1:0];
      cmd_tag = tag;
      cmd_tx_base_addr = {tag, 8'h10, 8'h00};
      cmd_rx_base_addr = {tag, 8'h20, 8'h00};
      cmd_flit_count = 4;
      cmd_valid = 1;
      @(posedge clk);
      while (!cmd_ready)
        @(posedge clk);
      @(negedge clk);
      cmd_valid = 0;
    end
  endtask

  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1;

    fork
      begin
        submit(8, 2, 7, 8'h31);
        submit(8, 3, 9, 8'h52);
      end
      begin
        wait (rx_desc_valid[7]);
        if (rx_desc_source[(7*4) +: 4] !== 2 ||
            rx_desc_tag[(7*8) +: 8] !== 8'h31 ||
            rx_desc_flit_count[(7*4) +: 4] !== 4)
          $fatal(1, "first RX descriptor payload mismatch");
        rx_desc_ready[7] = 0;
        repeat (2) @(negedge clk);
        rx_desc_ready[7] = 1;
        wait (tx_desc_valid[2]);
        if (tx_desc_destination[(2*4) +: 4] !== 7 ||
            tx_desc_tag[(2*8) +: 8] !== 8'h31)
          $fatal(1, "first TX descriptor payload mismatch");
        tx_desc_ready[2] = 0;
        repeat (2) @(negedge clk);
        tx_desc_ready[2] = 1;
      end
    join

    wait (submitted_transmit_count == 2);
    repeat (2) @(negedge clk);
    if (rx_seen != 2 || tx_seen != 2)
      $fatal(1, "descriptor event count mismatch rx=%0d tx=%0d", rx_seen, tx_seen);
    if (rx_cycle[0] < 8 || tx_cycle[0] <= rx_cycle[0] || tx_cycle[1] <= rx_cycle[1])
      $fatal(1, "RX-before-TX/release ordering mismatch");
    if (accepted_command_count != 2 || installed_receive_count != 2 ||
        submitted_transmit_count != 2 || protocol_error)
      $fatal(1, "scheduler counters/error mismatch");
    if (endpoint_stall_cycles < 2)
      $fatal(1, "backpressure stalls were not counted");

    @(negedge clk);
    cmd_release_cycle = current_cycle;
    cmd_source = 1;
    cmd_destination = 4;
    cmd_flit_count = 0;
    cmd_valid = 1;
    @(negedge clk);
    cmd_valid = 0;
    repeat (2) @(negedge clk);
    if (!protocol_error || accepted_command_count != 3 ||
        submitted_transmit_count != 2)
      $fatal(1, "invalid command was not rejected");

    $display("PASS accepted=%0d rx=%0d tx=%0d release_wait=%0d stalls=%0d",
      accepted_command_count, installed_receive_count,
      submitted_transmit_count, release_wait_cycles, endpoint_stall_cycles);
    $finish;
  end
endmodule
