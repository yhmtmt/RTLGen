`timescale 1ns/1ps

module noc_descriptor_command_prefetch_tb;
  localparam integer COMMAND_W = 102;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg enable = 1'b0;
  reg [13:0] command_count = 4;
  wire mem_req_valid;
  reg mem_req_ready = 1'b0;
  wire [13:0] mem_req_addr;
  reg pending_response = 1'b0;
  reg [13:0] pending_addr = 0;
  wire mem_rsp_valid = pending_response;
  wire mem_rsp_ready;
  wire [COMMAND_W-1:0] mem_rsp_data = command_word(pending_addr);
  wire cmd_valid;
  reg cmd_ready = 1'b0;
  wire [COMMAND_W-1:0] cmd_data;
  wire [31:0] request_count;
  wire [31:0] response_count;
  wire [31:0] delivered_command_count;
  wire [31:0] memory_stall_cycles;
  wire protocol_error;
  integer observed_count = 0;

  function [COMMAND_W-1:0] command_word;
    input [13:0] address;
    begin
      command_word = {32'h1000 + address, 56'h123456789abcde, address};
    end
  endfunction

  noc_descriptor_command_prefetch dut (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .command_count(command_count),
    .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready),
    .mem_req_addr(mem_req_addr),
    .mem_rsp_valid(mem_rsp_valid), .mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_data(mem_rsp_data),
    .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_data(cmd_data),
    .request_count(request_count), .response_count(response_count),
    .delivered_command_count(delivered_command_count),
    .memory_stall_cycles(memory_stall_cycles),
    .protocol_error(protocol_error)
  );

  always #1 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n) begin
      pending_response <= 1'b0;
      pending_addr <= 0;
    end else begin
      if (pending_response && mem_rsp_ready)
        pending_response <= 1'b0;
      if (mem_req_valid && mem_req_ready) begin
        if (pending_response && !mem_rsp_ready)
          $fatal(1, "memory accepted a request while response was held");
        pending_response <= 1'b1;
        pending_addr <= mem_req_addr;
      end
      if (cmd_valid && cmd_ready) begin
        if (cmd_data !== command_word(observed_count[13:0]))
          $fatal(1, "command order/data mismatch at %0d", observed_count);
        observed_count = observed_count + 1;
      end
    end
  end

  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    enable = 1'b1;
    repeat (2) @(negedge clk);
    mem_req_ready = 1'b1;
    repeat (3) @(negedge clk);
    cmd_ready = 1'b1;
    repeat (3) @(negedge clk);
    cmd_ready = 1'b0;
    repeat (2) @(negedge clk);
    cmd_ready = 1'b1;

    wait (delivered_command_count == 4);
    repeat (2) @(negedge clk);
    if (observed_count != 4 || request_count != 4 || response_count != 4)
      $fatal(1, "prefetch count mismatch observed=%0d req=%0d rsp=%0d delivered=%0d",
        observed_count, request_count, response_count, delivered_command_count);
    if (memory_stall_cycles < 2 || protocol_error)
      $fatal(1, "stall/error accounting mismatch stalls=%0d error=%0d",
        memory_stall_cycles, protocol_error);
    $display("PASS prefetch commands=%0d stalls=%0d", observed_count, memory_stall_cycles);
    $finish;
  end
endmodule
