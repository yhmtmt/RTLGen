`timescale 1ns/1ps

module noc_sram_packet_mesh4x4_tb;
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 16;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  integer endpoint_i;

  reg [15:0] tx_desc_valid = 0;
  wire [15:0] tx_desc_ready;
  reg [63:0] tx_desc_destination = 0;
  reg [31:0] tx_desc_vc = 0;
  reg [127:0] tx_desc_tag = 0;
  reg [16*ADDR_W-1:0] tx_desc_base_addr = 0;
  reg [63:0] tx_desc_flit_count = 0;
  wire [15:0] tx_mem_req_valid;
  reg [15:0] tx_mem_req_ready = 16'hffff;
  wire [16*ADDR_W-1:0] tx_mem_req_addr;
  reg [15:0] tx_mem_rsp_valid = 0;
  wire [15:0] tx_mem_rsp_ready;
  reg [16*DATA_W-1:0] tx_mem_rsp_data = 0;

  reg [15:0] rx_desc_valid = 0;
  wire [15:0] rx_desc_ready;
  reg [63:0] rx_desc_source = 0;
  reg [31:0] rx_desc_vc = 0;
  reg [127:0] rx_desc_tag = 0;
  reg [16*ADDR_W-1:0] rx_desc_base_addr = 0;
  reg [63:0] rx_desc_flit_count = 0;
  wire [15:0] rx_mem_write_valid;
  reg [15:0] rx_mem_write_ready = 16'hffff;
  wire [16*ADDR_W-1:0] rx_mem_write_addr;
  wire [16*DATA_W-1:0] rx_mem_write_data;
  wire [15:0] rx_completion_valid;
  reg [15:0] rx_completion_ready = 0;
  wire [63:0] rx_completion_source;
  wire [31:0] rx_completion_vc;
  wire [127:0] rx_completion_tag;
  wire [15:0] endpoint_protocol_error;

  integer source0_requests = 0;
  integer source3_requests = 0;
  integer destination12_writes = 0;
  integer destination15_writes = 0;
  reg completion12 = 1'b0;
  reg completion15 = 1'b0;

  noc_sram_packet_mesh4x4 #(
    .ADDR_W(ADDR_W)
  ) dut (
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
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr),
    .rx_mem_write_data(rx_mem_write_data),
    .rx_completion_valid(rx_completion_valid),
    .rx_completion_ready(rx_completion_ready),
    .rx_completion_source(rx_completion_source),
    .rx_completion_vc(rx_completion_vc),
    .rx_completion_tag(rx_completion_tag),
    .endpoint_protocol_error(endpoint_protocol_error),
    .router_accepted_flit_count(), .router_forwarded_flit_count(),
    .router_input_stall_cycles(), .router_output_stall_cycles(),
    .router_contention_cycles(), .router_current_input_occupancy(),
    .router_max_input_occupancy(), .router_route_flit_count()
  );

  always #5 clk = ~clk;

  function [DATA_W-1:0] memory_data;
    input [3:0] source;
    input [ADDR_W-1:0] address;
    begin
      memory_data = {{(DATA_W-36){1'b0}}, source, 16'hcafe, address};
    end
  endfunction

  task install_receive_descriptors;
    begin
      @(negedge clk);
      rx_desc_source[(12*4) +: 4] = 4'd3;
      rx_desc_vc[(12*2) +: 2] = 2'd2;
      rx_desc_tag[(12*8) +: 8] = 8'h32;
      rx_desc_base_addr[(12*ADDR_W) +: ADDR_W] = 16'h1200;
      rx_desc_flit_count[(12*4) +: 4] = 4'd3;
      rx_desc_source[(15*4) +: 4] = 4'd0;
      rx_desc_vc[(15*2) +: 2] = 2'd1;
      rx_desc_tag[(15*8) +: 8] = 8'h08;
      rx_desc_base_addr[(15*ADDR_W) +: ADDR_W] = 16'h1800;
      rx_desc_flit_count[(15*4) +: 4] = 4'd8;
      rx_desc_valid = 16'h9000;
      @(posedge clk);
      while ((rx_desc_ready & 16'h9000) != 16'h9000) @(posedge clk);
      @(negedge clk);
      rx_desc_valid = 0;
    end
  endtask

  task install_transmit_descriptors;
    begin
      @(negedge clk);
      tx_desc_destination[(0*4) +: 4] = 4'd15;
      tx_desc_vc[(0*2) +: 2] = 2'd1;
      tx_desc_tag[(0*8) +: 8] = 8'h08;
      tx_desc_base_addr[(0*ADDR_W) +: ADDR_W] = 16'h0100;
      tx_desc_flit_count[(0*4) +: 4] = 4'd8;
      tx_desc_destination[(3*4) +: 4] = 4'd12;
      tx_desc_vc[(3*2) +: 2] = 2'd2;
      tx_desc_tag[(3*8) +: 8] = 8'h32;
      tx_desc_base_addr[(3*ADDR_W) +: ADDR_W] = 16'h0300;
      tx_desc_flit_count[(3*4) +: 4] = 4'd3;
      tx_desc_valid = 16'h0009;
      @(posedge clk);
      while ((tx_desc_ready & 16'h0009) != 16'h0009) @(posedge clk);
      @(negedge clk);
      tx_desc_valid = 0;
    end
  endtask

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      tx_mem_rsp_valid <= 0;
      tx_mem_rsp_data <= 0;
      source0_requests <= 0;
      source3_requests <= 0;
    end else begin
      cycle <= cycle + 1;
      tx_mem_req_ready <= 16'hffff;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (tx_mem_req_valid[endpoint_i] && tx_mem_req_ready[endpoint_i]) begin
          tx_mem_rsp_valid[endpoint_i] <= 1'b1;
          tx_mem_rsp_data[(endpoint_i*DATA_W) +: DATA_W] <= memory_data(
            endpoint_i[3:0], tx_mem_req_addr[(endpoint_i*ADDR_W) +: ADDR_W]);
          if (endpoint_i == 0)
            source0_requests <= source0_requests + 1;
          else if (endpoint_i == 3)
            source3_requests <= source3_requests + 1;
          else
            $fatal(1, "unexpected memory request from endpoint %0d", endpoint_i);
        end else if (tx_mem_rsp_valid[endpoint_i] && tx_mem_rsp_ready[endpoint_i]) begin
          tx_mem_rsp_valid[endpoint_i] <= 1'b0;
        end
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      rx_mem_write_ready <= 16'hffff;
      if ((cycle % 5) == 2)
        rx_mem_write_ready[15] <= 1'b0;
      if ((cycle % 7) == 3)
        rx_mem_write_ready[12] <= 1'b0;

      if (rx_mem_write_valid[12] && rx_mem_write_ready[12]) begin
        if (rx_mem_write_addr[(12*ADDR_W) +: ADDR_W] !==
            (16'h1200 + destination12_writes * 32))
          $fatal(1, "wrong destination-12 write address");
        if (rx_mem_write_data[(12*DATA_W) +: DATA_W] !==
            memory_data(4'd3, 16'h0300 + destination12_writes * 32))
          $fatal(1, "wrong destination-12 write data");
        destination12_writes <= destination12_writes + 1;
      end
      if (rx_mem_write_valid[15] && rx_mem_write_ready[15]) begin
        if (rx_mem_write_addr[(15*ADDR_W) +: ADDR_W] !==
            (16'h1800 + destination15_writes * 32))
          $fatal(1, "wrong destination-15 write address");
        if (rx_mem_write_data[(15*DATA_W) +: DATA_W] !==
            memory_data(4'd0, 16'h0100 + destination15_writes * 32))
          $fatal(1, "wrong destination-15 write data");
        destination15_writes <= destination15_writes + 1;
      end

      if (rx_completion_valid[12] && rx_completion_ready[12]) begin
        if (rx_completion_source[(12*4) +: 4] !== 3 ||
            rx_completion_vc[(12*2) +: 2] !== 2 ||
            rx_completion_tag[(12*8) +: 8] !== 8'h32)
          $fatal(1, "wrong destination-12 completion");
        completion12 <= 1'b1;
      end
      if (rx_completion_valid[15] && rx_completion_ready[15]) begin
        if (rx_completion_source[(15*4) +: 4] !== 0 ||
            rx_completion_vc[(15*2) +: 2] !== 1 ||
            rx_completion_tag[(15*8) +: 8] !== 8'h08)
          $fatal(1, "wrong destination-15 completion");
        completion15 <= 1'b1;
      end

      if (endpoint_protocol_error != 0)
        $fatal(1, "endpoint protocol error: %h", endpoint_protocol_error);
    end
  end

  initial begin
    #500000;
    $fatal(1, "simulation timeout");
  end

  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    install_receive_descriptors();
    install_transmit_descriptors();
    repeat (8) @(negedge clk);
    rx_completion_ready = 16'h9000;
    while (!completion12 || !completion15) @(negedge clk);
    repeat (3) @(negedge clk);
    if (source0_requests != 8 || source3_requests != 3 ||
        destination12_writes != 3 || destination15_writes != 8)
      $fatal(1, "wrong final request/write counts");
    $display("PASS noc_sram_packet_mesh4x4 req0=%0d req3=%0d write12=%0d write15=%0d cycles=%0d",
      source0_requests, source3_requests,
      destination12_writes, destination15_writes, cycle);
    $finish;
  end
endmodule
