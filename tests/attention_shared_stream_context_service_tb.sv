`timescale 1ns/1ps

module attention_shared_stream_context_service_tb;
  localparam integer ADDR_W = 32;
  localparam integer PACKETS = 3;
  localparam integer PACKET_INDEX_W = 2;
  localparam integer CONTEXTS = 4;
  localparam integer WORDS_PER_CONTEXT = PACKETS * 8;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg layer_start = 1'b0;
  reg layer_idle = 1'b1;
  reg [7:0] layer_expected_remote_contexts = CONTEXTS;
  reg [15:0] event_valid = 16'b0;
  wire [15:0] event_ready;
  reg [16*3-1:0] event_wave = 0;
  reg [16*4-1:0] event_source = 0;
  reg [16*ADDR_W-1:0] event_source_base_addr = 0;
  reg [16*ADDR_W-1:0] event_destination_base_addr = 0;
  reg [16*(PACKET_INDEX_W+1)-1:0] event_packet_count = 0;

  reg completion_ready = 1'b0;
  wire completion_valid;
  wire [2:0] completion_wave;
  wire [3:0] completion_destination;
  wire [15:0] tx_mem_req_valid;
  reg [15:0] tx_mem_req_ready = 16'b0;
  wire [16*ADDR_W-1:0] tx_mem_req_addr;
  reg [15:0] tx_mem_rsp_valid = 16'b0;
  wire [15:0] tx_mem_rsp_ready;
  reg [16*256-1:0] tx_mem_rsp_data = 0;
  wire [15:0] rx_mem_write_valid;
  reg [15:0] rx_mem_write_ready = 16'b0;
  wire [16*ADDR_W-1:0] rx_mem_write_addr;
  wire [16*256-1:0] rx_mem_write_data;
  wire context_valid;
  wire context_ready;
  wire [2:0] context_wave;
  wire [3:0] context_destination;
  wire [3:0] context_source;
  wire [ADDR_W-1:0] context_source_base_addr;
  wire [ADDR_W-1:0] context_destination_base_addr;
  wire [PACKET_INDEX_W:0] context_packet_count;
  wire admission_complete;
  wire transport_complete;
  wire [7:0] admitted_count;
  wire [7:0] completed_count;
  wire [15:0] endpoint_protocol_error;
  wire protocol_error;

  reg rsp_pending [0:15];
  reg [255:0] rsp_data [0:15];
  reg [WORDS_PER_CONTEXT-1:0] write_seen [0:CONTEXTS-1];
  integer cycle = 0;
  integer endpoint_i;
  integer context_count = 0;
  integer completion_count = 0;
  integer write_count = 0;
  integer offset;
  integer word_index;
  reg [ADDR_W-1:0] expected_source_addr;
  reg [255:0] expected_data;

  attention_shared_stream_context_service #(
    .ADDR_W(ADDR_W),
    .MAX_PACKETS_PER_CONTEXT(PACKETS),
    .PACKET_INDEX_W(PACKET_INDEX_W),
    .TX_DESC_DEPTH(2)
  ) dut (
    .clk(clk), .rst_n(rst_n),
    .layer_start(layer_start), .layer_idle(layer_idle),
    .layer_expected_remote_contexts(layer_expected_remote_contexts),
    .event_valid(event_valid), .event_ready(event_ready),
    .event_wave(event_wave), .event_source(event_source),
    .event_source_base_addr(event_source_base_addr),
    .event_destination_base_addr(event_destination_base_addr),
    .event_packet_count(event_packet_count),
    .completion_ready(completion_ready), .completion_valid(completion_valid),
    .completion_wave(completion_wave),
    .completion_destination(completion_destination),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr), .rx_mem_write_data(rx_mem_write_data),
    .context_valid(context_valid), .context_ready(context_ready),
    .context_wave(context_wave), .context_destination(context_destination),
    .context_source(context_source),
    .context_source_base_addr(context_source_base_addr),
    .context_destination_base_addr(context_destination_base_addr),
    .context_packet_count(context_packet_count),
    .admission_complete(admission_complete),
    .transport_complete(transport_complete), .admitted_count(admitted_count),
    .completed_count(completed_count),
    .endpoint_protocol_error(endpoint_protocol_error), .protocol_error(protocol_error)
  );

  always #1 clk = ~clk;

  function [ADDR_W-1:0] source_base;
    input integer destination;
    begin
      source_base = 32'h0100_0000 + destination * 32'h0000_1000;
    end
  endfunction

  function [ADDR_W-1:0] destination_base;
    input integer destination;
    begin
      destination_base = 32'h0200_0000 + destination * 32'h0000_1000;
    end
  endfunction

  function [255:0] memory_word;
    input [3:0] endpoint;
    input [ADDR_W-1:0] address;
    begin
      memory_word = {220'b0, endpoint, address};
    end
  endfunction

  always @(*) begin
    tx_mem_req_ready = 16'b0;
    tx_mem_rsp_valid = 16'b0;
    tx_mem_rsp_data = 0;
    rx_mem_write_ready = 16'b0;
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      tx_mem_req_ready[endpoint_i] = !rsp_pending[endpoint_i] &&
        (((cycle + endpoint_i) % 5) != 1);
      tx_mem_rsp_valid[endpoint_i] = rsp_pending[endpoint_i];
      tx_mem_rsp_data[(endpoint_i*256) +: 256] = rsp_data[endpoint_i];
      rx_mem_write_ready[endpoint_i] = ((cycle + endpoint_i) % 7) != 2;
    end
    completion_ready = ((cycle % 11) != 3) && ((cycle % 13) != 5);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        rsp_pending[endpoint_i] <= 1'b0;
        rsp_data[endpoint_i] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (rsp_pending[endpoint_i]) begin
          if (tx_mem_rsp_ready[endpoint_i])
            rsp_pending[endpoint_i] <= 1'b0;
        end else if (tx_mem_req_valid[endpoint_i] && tx_mem_req_ready[endpoint_i]) begin
          rsp_pending[endpoint_i] <= 1'b1;
          rsp_data[endpoint_i] <= memory_word(endpoint_i[3:0],
            tx_mem_req_addr[(endpoint_i*ADDR_W) +: ADDR_W]);
        end
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (context_valid && context_ready) begin
        if (context_wave !== 0 || context_destination !== context_count[3:0] ||
            context_source !== (context_count + 4) ||
            context_source_base_addr !== source_base(context_count) ||
            context_destination_base_addr !== destination_base(context_count) ||
            context_packet_count !== PACKETS)
          $fatal(1, "context trace mismatch index=%0d wave=%0d src=%0d dst=%0d",
            context_count, context_wave, context_source, context_destination);
        $display("TRACE_CONTEXT %0d %0d %0d %0d %0d %0d %0d", cycle, context_wave,
          context_destination, context_source, context_packet_count,
          context_source_base_addr, context_destination_base_addr);
        context_count = context_count + 1;
      end
      if (completion_valid && completion_ready) begin
        if (completion_wave !== 0 || completion_destination >= CONTEXTS)
          $fatal(1, "completion identity mismatch wave=%0d destination=%0d",
            completion_wave, completion_destination);
        $display("TRACE_COMPLETION %0d %0d %0d", cycle, completion_wave,
          completion_destination);
        completion_count = completion_count + 1;
      end
      for (endpoint_i = 0; endpoint_i < CONTEXTS; endpoint_i = endpoint_i + 1) begin
        if (rx_mem_write_valid[endpoint_i] && rx_mem_write_ready[endpoint_i]) begin
          offset = rx_mem_write_addr[(endpoint_i*ADDR_W) +: ADDR_W] -
            destination_base(endpoint_i);
          if (offset < 0 || (offset % 32) != 0)
            $fatal(1, "unaligned destination write endpoint=%0d offset=%0d", endpoint_i, offset);
          word_index = offset / 32;
          if (word_index < 0 || word_index >= WORDS_PER_CONTEXT ||
              write_seen[endpoint_i][word_index])
            $fatal(1, "duplicate/out-of-range write endpoint=%0d word=%0d",
              endpoint_i, word_index);
          expected_source_addr = source_base(endpoint_i) + offset;
          expected_data = memory_word((endpoint_i + 4), expected_source_addr);
          if (rx_mem_write_data[(endpoint_i*256) +: 256] !== expected_data)
            $fatal(1, "payload mismatch endpoint=%0d word=%0d", endpoint_i, word_index);
          write_seen[endpoint_i][word_index] = 1'b1;
          write_count = write_count + 1;
        end
      end
      if (protocol_error)
        $fatal(1, "unexpected service protocol error endpoint=%h", endpoint_protocol_error);
    end
  end

  initial begin
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      rsp_pending[endpoint_i] = 1'b0;
      rsp_data[endpoint_i] = 0;
      if (endpoint_i < CONTEXTS)
        write_seen[endpoint_i] = 0;
    end
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    @(negedge clk);
    layer_start = 1'b1;
    @(posedge clk);
    @(negedge clk);
    layer_start = 1'b0;
    for (endpoint_i = 0; endpoint_i < CONTEXTS; endpoint_i = endpoint_i + 1) begin
      event_wave[(endpoint_i*3) +: 3] = 0;
      event_source[(endpoint_i*4) +: 4] = endpoint_i + 4;
      event_source_base_addr[(endpoint_i*ADDR_W) +: ADDR_W] = source_base(endpoint_i);
      event_destination_base_addr[(endpoint_i*ADDR_W) +: ADDR_W] = destination_base(endpoint_i);
      event_packet_count[(endpoint_i*(PACKET_INDEX_W+1)) +: (PACKET_INDEX_W+1)] = PACKETS;
      event_valid[endpoint_i] = 1'b1;
    end
    @(posedge clk);
    if ((event_ready & ((1 << CONTEXTS) - 1)) !== ((1 << CONTEXTS) - 1))
      $fatal(1, "service did not accept all producer events");
    @(negedge clk);
    event_valid = 0;

    wait (transport_complete);
    repeat (5) @(negedge clk);
    if (!admission_complete || admitted_count != CONTEXTS ||
        completed_count != CONTEXTS || context_count != CONTEXTS ||
        completion_count != CONTEXTS || write_count != CONTEXTS * WORDS_PER_CONTEXT)
      $fatal(1, "service totals mismatch admitted=%0d completed=%0d contexts=%0d writes=%0d",
        admitted_count, completed_count, context_count, write_count);
    for (endpoint_i = 0; endpoint_i < CONTEXTS; endpoint_i = endpoint_i + 1)
      if (write_seen[endpoint_i] !== {WORDS_PER_CONTEXT{1'b1}})
        $fatal(1, "missing destination writes endpoint=%0d seen=%h",
          endpoint_i, write_seen[endpoint_i]);
    $display("PASS shared_stream_service contexts=%0d packets=%0d flits=%0d",
      context_count, context_count * PACKETS, write_count);
    $finish;
  end

  initial begin
    #2000000;
    $fatal(1, "shared-stream service timeout");
  end
endmodule
