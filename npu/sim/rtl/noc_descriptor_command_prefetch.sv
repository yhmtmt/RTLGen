`timescale 1ns/1ps

// Streams fixed-width command records from a one-cycle SRAM-style interface.
// One response buffer and one outstanding read are sufficient because the
// paired descriptor scheduler consumes at most one command every two cycles.
module noc_descriptor_command_prefetch #(
  parameter integer COMMAND_W = 102,
  parameter integer ADDR_W = 14,
  parameter integer COUNT_W = 14,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [COUNT_W-1:0] command_count,

  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [ADDR_W-1:0] mem_req_addr,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [COMMAND_W-1:0] mem_rsp_data,

  output wire cmd_valid,
  input wire cmd_ready,
  output wire [COMMAND_W-1:0] cmd_data,

  output reg [COUNTER_W-1:0] request_count,
  output reg [COUNTER_W-1:0] response_count,
  output reg [COUNTER_W-1:0] delivered_command_count,
  output reg [COUNTER_W-1:0] memory_stall_cycles,
  output reg protocol_error
);
  reg [ADDR_W-1:0] next_request_addr;
  reg request_outstanding;
  reg response_buffer_valid;
  reg [COMMAND_W-1:0] response_buffer_data;

  wire command_fire = cmd_valid && cmd_ready;
  wire response_fire = mem_rsp_valid && mem_rsp_ready;
  wire can_reserve_response_slot = !response_buffer_valid || command_fire;
  wire all_requests_issued = next_request_addr >= command_count;
  wire request_fire = mem_req_valid && mem_req_ready;

  assign mem_req_valid =
    enable && !all_requests_issued && !request_outstanding &&
    can_reserve_response_slot;
  assign mem_req_addr = next_request_addr;
  assign mem_rsp_ready = can_reserve_response_slot;
  assign cmd_valid = response_buffer_valid;
  assign cmd_data = response_buffer_data;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      next_request_addr <= {ADDR_W{1'b0}};
      request_outstanding <= 1'b0;
      response_buffer_valid <= 1'b0;
      response_buffer_data <= {COMMAND_W{1'b0}};
      request_count <= {COUNTER_W{1'b0}};
      response_count <= {COUNTER_W{1'b0}};
      delivered_command_count <= {COUNTER_W{1'b0}};
      memory_stall_cycles <= {COUNTER_W{1'b0}};
      protocol_error <= 1'b0;
    end else begin
      if (mem_req_valid && !mem_req_ready)
        memory_stall_cycles <= memory_stall_cycles + 1'b1;

      if (request_fire) begin
        next_request_addr <= next_request_addr + 1'b1;
        request_outstanding <= 1'b1;
        request_count <= request_count + 1'b1;
      end

      if (command_fire) begin
        response_buffer_valid <= 1'b0;
        delivered_command_count <= delivered_command_count + 1'b1;
      end

      if (response_fire) begin
        response_buffer_valid <= 1'b1;
        response_buffer_data <= mem_rsp_data;
        request_outstanding <= 1'b0;
        response_count <= response_count + 1'b1;
        if (!request_outstanding)
          protocol_error <= 1'b1;
      end else if (mem_rsp_valid && !request_outstanding) begin
        protocol_error <= 1'b1;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (COMMAND_W <= 0 || ADDR_W <= 0 || COUNT_W <= 0) begin
      $error("noc_descriptor_command_prefetch parameters must be positive");
      $finish(1);
    end
    if (ADDR_W < COUNT_W) begin
      $error("noc_descriptor_command_prefetch ADDR_W must represent command_count");
      $finish(1);
    end
  end
`endif
endmodule
