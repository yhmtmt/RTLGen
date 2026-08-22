`timescale 1ns/1ps

module attention_shared_stream_context_engine_tb #(
  parameter integer MAX_PACKETS_PER_CONTEXT = 68,
  parameter integer PACKET_INDEX_W = 7,
  parameter integer TEST_CONTEXT_COUNT = 112,
  parameter integer TX_DESC_DEPTH = 1
);
  localparam integer ADDR_W = 32;
  localparam integer CONTEXT_COUNT = 112;
  localparam integer PACKET_COUNT_W = PACKET_INDEX_W + 1;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg context_valid = 1'b0;
  wire context_ready;
  reg [2:0] context_wave = 0;
  reg [3:0] context_destination = 0;
  reg [3:0] context_source = 0;
  reg [ADDR_W-1:0] context_source_base_addr = 0;
  reg [ADDR_W-1:0] context_destination_base_addr = 0;
  reg [PACKET_COUNT_W-1:0] context_packet_count = MAX_PACKETS_PER_CONTEXT;
  wire context_completion_valid;
  reg context_completion_ready = 1'b0;
  wire [2:0] context_completion_wave;
  wire [3:0] context_completion_destination;

  wire [15:0] tx_desc_valid;
  wire [15:0] tx_desc_ready;
  wire [63:0] tx_desc_destination;
  wire [31:0] tx_desc_vc;
  wire [127:0] tx_desc_tag;
  wire [16*ADDR_W-1:0] tx_desc_base_addr;
  wire [63:0] tx_desc_flit_count;
  wire [15:0] rx_desc_valid;
  wire [15:0] rx_desc_ready;
  wire [63:0] rx_desc_source;
  wire [31:0] rx_desc_vc;
  wire [127:0] rx_desc_tag;
  wire [16*ADDR_W-1:0] rx_desc_base_addr;
  wire [63:0] rx_desc_flit_count;

  wire [15:0] tx_mem_req_valid;
  reg [15:0] tx_mem_req_ready = 16'hffff;
  wire [16*ADDR_W-1:0] tx_mem_req_addr;
  reg [15:0] tx_mem_rsp_valid = 16'b0;
  wire [15:0] tx_mem_rsp_ready;
  reg [16*256-1:0] tx_mem_rsp_data = 0;
  wire [15:0] rx_mem_write_valid;
  reg [15:0] rx_mem_write_ready = 16'hffff;
  wire [16*ADDR_W-1:0] rx_mem_write_addr;
  wire [16*256-1:0] rx_mem_write_data;
  wire [15:0] endpoint_protocol_error;
  wire protocol_error;

  reg rsp_pending [0:15];
  reg [255:0] rsp_data [0:15];
  integer cycle = 0;
  integer wave_i;
  integer lane_i;
  integer endpoint_i;
  integer command_count = 0;
  integer tx_descriptor_count = 0;
  integer rx_descriptor_count = 0;
  integer write_count = 0;
  integer completion_count = 0;
  integer descriptor_backpressure = 0;
  integer max_tx_valid_per_cycle = 0;
  integer max_rx_valid_per_cycle = 0;
  integer max_tx_descriptors_per_cycle = 0;
  integer max_rx_descriptors_per_cycle = 0;
  integer expected_descriptor_count = 0;
  integer expected_flit_count = 0;
  integer submitted_contexts = 0;
  integer variable_count_case = 0;
  integer invalid_case_mode = 0;
  integer parallel_tx_count = 0;
  integer parallel_rx_count = 0;
  integer held_completion_checks = 0;
  reg [ADDR_W-1:0] source_base_by_endpoint [0:15];
  reg [ADDR_W-1:0] destination_base_by_endpoint [0:15];
  reg [3:0] destination_by_source_endpoint [0:15];
  reg [3:0] source_by_destination_endpoint [0:15];
  integer expected_tx_packet [0:15];
  integer expected_rx_packet [0:15];
  reg completion_seen [0:127];
  reg completion_held = 1'b0;
  reg completion_stall_seen = 1'b0;
  reg [2:0] held_completion_wave = 0;
  reg [3:0] held_completion_destination = 0;

  attention_shared_stream_context_engine #(
    .ADDR_W(ADDR_W),
    .MAX_PACKETS_PER_CONTEXT(MAX_PACKETS_PER_CONTEXT),
    .PACKET_INDEX_W(PACKET_INDEX_W),
    .TAG_W(8),
    .TX_DESC_DEPTH(TX_DESC_DEPTH)
  ) dut (
    .clk(clk), .rst_n(rst_n),
    .context_valid(context_valid), .context_ready(context_ready),
    .context_wave(context_wave), .context_destination(context_destination),
    .context_source(context_source),
    .context_source_base_addr(context_source_base_addr),
    .context_destination_base_addr(context_destination_base_addr),
    .context_packet_count(context_packet_count),
    .context_completion_valid(context_completion_valid),
    .context_completion_ready(context_completion_ready),
    .context_completion_wave(context_completion_wave),
    .context_completion_destination(context_completion_destination),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr), .rx_mem_write_data(rx_mem_write_data),
    .endpoint_protocol_error(endpoint_protocol_error), .protocol_error(protocol_error)
  );

  always #1 clk = ~clk;

  function [3:0] shift_for_wave;
    input integer wave;
    begin
      case (wave)
        0: shift_for_wave = 4;
        1: shift_for_wave = 7;
        2: shift_for_wave = 10;
        3: shift_for_wave = 13;
        5: shift_for_wave = 3;
        6: shift_for_wave = 6;
        default: shift_for_wave = 9;
      endcase
    end
  endfunction

  function [ADDR_W-1:0] make_source_base;
    input integer wave;
    input integer cluster;
    begin
      make_source_base = 32'h0100_0000 + wave * 32'h0010_0000 + cluster * 32'h0000_1000;
    end
  endfunction

  function [ADDR_W-1:0] make_destination_base;
    input integer wave;
    input integer cluster;
    begin
      make_destination_base = 32'h0200_0000 + wave * 32'h0010_0000 + cluster * 32'h0000_1000;
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
    tx_mem_rsp_valid = 16'b0;
    tx_mem_rsp_data = 0;
    tx_mem_req_ready = 16'b0;
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      tx_mem_rsp_valid[endpoint_i] = rsp_pending[endpoint_i];
      tx_mem_rsp_data[(endpoint_i*256) +: 256] = rsp_data[endpoint_i];
      tx_mem_req_ready[endpoint_i] = !rsp_pending[endpoint_i] &&
        (((cycle + endpoint_i) % 5) != 1);
      rx_mem_write_ready[endpoint_i] = (((cycle + endpoint_i) % 13) != 3);
    end
    context_completion_ready = completion_stall_seen &&
      ((cycle % 17) != 5) && ((cycle % 23) != 7);
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

  task submit_context;
    input integer wave;
    input integer cluster;
    integer packet_value;
    begin
      @(negedge clk);
      context_wave = wave[2:0];
      context_destination = cluster[3:0];
      context_source = cluster[3:0] + shift_for_wave(wave);
      context_source_base_addr = make_source_base(wave, cluster);
      context_destination_base_addr = make_destination_base(wave, cluster);
      packet_value = (variable_count_case && submitted_contexts == 0) ? 257 :
        ((variable_count_case) ? 3 : MAX_PACKETS_PER_CONTEXT);
      context_packet_count = packet_value;
      expected_descriptor_count = expected_descriptor_count + packet_value;
      expected_flit_count = expected_flit_count + (packet_value * 8);
      context_valid = 1'b1;
      @(posedge clk);
      while (!context_ready)
        @(posedge clk);
      source_base_by_endpoint[context_source] = context_source_base_addr;
      destination_base_by_endpoint[context_destination] = context_destination_base_addr;
      destination_by_source_endpoint[context_source] = context_destination;
      source_by_destination_endpoint[context_destination] = context_source;
      expected_tx_packet[context_source] = 0;
      expected_rx_packet[context_destination] = 0;
      @(negedge clk);
      context_valid = 1'b0;
      submitted_contexts = submitted_contexts + 1;
    end
  endtask

  always @(posedge clk) begin
    if (rst_n) begin
      integer cycle_tx_descriptors;
      integer cycle_rx_descriptors;
      integer cycle_tx_valid_count;
      integer cycle_rx_valid_count;
      if (context_valid && context_ready)
        command_count = command_count + 1;
      cycle_tx_descriptors = 0;
      cycle_rx_descriptors = 0;
      cycle_tx_valid_count = 0;
      cycle_rx_valid_count = 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (tx_desc_valid[endpoint_i] && !tx_desc_ready[endpoint_i])
          descriptor_backpressure = descriptor_backpressure + 1;
        if (rx_desc_valid[endpoint_i] && !rx_desc_ready[endpoint_i])
          descriptor_backpressure = descriptor_backpressure + 1;
        if (tx_desc_valid[endpoint_i])
          cycle_tx_valid_count = cycle_tx_valid_count + 1;
        if (rx_desc_valid[endpoint_i])
          cycle_rx_valid_count = cycle_rx_valid_count + 1;
        if (tx_desc_valid[endpoint_i] && tx_desc_ready[endpoint_i]) begin
          cycle_tx_descriptors = cycle_tx_descriptors + 1;
          tx_descriptor_count = tx_descriptor_count + 1;
          if (tx_desc_vc[(endpoint_i*2) +: 2] !== 0 ||
              tx_desc_destination[(endpoint_i*4) +: 4] !== destination_by_source_endpoint[endpoint_i] ||
              tx_desc_tag[(endpoint_i*8) +: 8] !== (expected_tx_packet[endpoint_i] & 255) ||
              tx_desc_base_addr[(endpoint_i*ADDR_W) +: ADDR_W] !==
                source_base_by_endpoint[endpoint_i] + (expected_tx_packet[endpoint_i] * 256) ||
              tx_desc_flit_count[(endpoint_i*4) +: 4] !== 8)
            $fatal(1, "TX descriptor mismatch endpoint=%0d tag=%0d expected_tag=%0d dest=%0d expected_dest=%0d base=%h expected_base=%h flits=%0d",
              endpoint_i, tx_desc_tag[(endpoint_i*8) +: 8], expected_tx_packet[endpoint_i] & 255,
              tx_desc_destination[(endpoint_i*4) +: 4], destination_by_source_endpoint[endpoint_i],
              tx_desc_base_addr[(endpoint_i*ADDR_W) +: ADDR_W],
              source_base_by_endpoint[endpoint_i] + (expected_tx_packet[endpoint_i] * 256),
              tx_desc_flit_count[(endpoint_i*4) +: 4]);
          expected_tx_packet[endpoint_i] = expected_tx_packet[endpoint_i] + 1;
        end
        if (rx_desc_valid[endpoint_i] && rx_desc_ready[endpoint_i]) begin
          cycle_rx_descriptors = cycle_rx_descriptors + 1;
          rx_descriptor_count = rx_descriptor_count + 1;
          if (rx_desc_vc[(endpoint_i*2) +: 2] !== 0 ||
              rx_desc_source[(endpoint_i*4) +: 4] !== source_by_destination_endpoint[endpoint_i] ||
              rx_desc_tag[(endpoint_i*8) +: 8] !== (expected_rx_packet[endpoint_i] & 255) ||
              rx_desc_base_addr[(endpoint_i*ADDR_W) +: ADDR_W] !==
                destination_base_by_endpoint[endpoint_i] + (expected_rx_packet[endpoint_i] * 256) ||
              rx_desc_flit_count[(endpoint_i*4) +: 4] !== 8)
            $fatal(1, "RX descriptor mismatch endpoint=%0d tag=%0d", endpoint_i,
              rx_desc_tag[(endpoint_i*8) +: 8]);
          expected_rx_packet[endpoint_i] = expected_rx_packet[endpoint_i] + 1;
        end
        if (rx_mem_write_valid[endpoint_i] && rx_mem_write_ready[endpoint_i])
          write_count = write_count + 1;
      end
      if (cycle_tx_valid_count > max_tx_valid_per_cycle)
        max_tx_valid_per_cycle = cycle_tx_valid_count;
      if (cycle_rx_valid_count > max_rx_valid_per_cycle)
        max_rx_valid_per_cycle = cycle_rx_valid_count;
      if (cycle_tx_descriptors > max_tx_descriptors_per_cycle)
        max_tx_descriptors_per_cycle = cycle_tx_descriptors;
      if (cycle_rx_descriptors > max_rx_descriptors_per_cycle)
        max_rx_descriptors_per_cycle = cycle_rx_descriptors;
      if (context_completion_valid && !context_completion_ready) begin
        completion_stall_seen <= 1'b1;
        if (completion_held) begin
          if (context_completion_wave !== held_completion_wave ||
              context_completion_destination !== held_completion_destination)
            $fatal(1, "context completion changed under backpressure");
          held_completion_checks = held_completion_checks + 1;
        end else begin
          completion_held <= 1'b1;
          held_completion_wave <= context_completion_wave;
          held_completion_destination <= context_completion_destination;
        end
      end else begin
        completion_held <= 1'b0;
      end
      if (context_completion_valid && context_completion_ready) begin
        if (context_completion_wave == 4 ||
            completion_seen[(context_completion_wave*16) + context_completion_destination])
          $fatal(1, "duplicate context completion wave=%0d destination=%0d",
            context_completion_wave, context_completion_destination);
        completion_seen[(context_completion_wave*16) + context_completion_destination] = 1'b1;
        completion_count = completion_count + 1;
      end
      if (protocol_error && !invalid_case_mode)
        $fatal(1, "unexpected engine protocol error endpoint=%h", endpoint_protocol_error);
    end
  end

  initial begin
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      source_base_by_endpoint[endpoint_i] = 0;
      destination_base_by_endpoint[endpoint_i] = 0;
      destination_by_source_endpoint[endpoint_i] = 0;
      source_by_destination_endpoint[endpoint_i] = 0;
      expected_tx_packet[endpoint_i] = 0;
      expected_rx_packet[endpoint_i] = 0;
    end
    for (endpoint_i = 0; endpoint_i < 128; endpoint_i = endpoint_i + 1)
      completion_seen[endpoint_i] = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    variable_count_case = $test$plusargs("VARIABLE_COUNT_CASE");
    invalid_case_mode = $test$plusargs("INVALID_CASE");
    if ($test$plusargs("PARALLEL_CASE")) begin
      @(negedge clk);
      dut.source_busy = 16'hffff;
      dut.destination_busy = 16'hffff;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        dut.context_active[endpoint_i] = 1'b1;
        dut.context_wave_q[endpoint_i] = 3'd0;
        dut.context_source_q[endpoint_i] = endpoint_i[3:0] + 4'd4;
        dut.context_destination_q[endpoint_i] = endpoint_i[3:0];
        dut.context_src_base_q[endpoint_i] = 32'h0100_0000 + endpoint_i * 32'h1000;
        dut.context_dst_base_q[endpoint_i] = 32'h0200_0000 + endpoint_i * 32'h1000;
        dut.context_packet_count_q[endpoint_i] = 68;
        dut.rx_installed_count[endpoint_i] = 0;
        dut.tx_issued_count[endpoint_i] = 0;
        dut.completed_count[endpoint_i] = 0;
        dut.context_done_pending[endpoint_i] = 1'b0;
        destination_by_source_endpoint[endpoint_i] = endpoint_i[3:0];
        source_by_destination_endpoint[endpoint_i] = endpoint_i[3:0] + 4'd4;
        source_base_by_endpoint[endpoint_i] = 32'h0100_0000 + endpoint_i * 32'h1000;
        destination_base_by_endpoint[endpoint_i] = 32'h0200_0000 + endpoint_i * 32'h1000;
        expected_tx_packet[endpoint_i] = 0;
        expected_rx_packet[endpoint_i] = 0;
      end
      #0;
      parallel_tx_count = 0;
      parallel_rx_count = 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (tx_desc_valid[endpoint_i] && tx_desc_ready[endpoint_i])
          parallel_tx_count = parallel_tx_count + 1;
        if (rx_desc_valid[endpoint_i] && rx_desc_ready[endpoint_i])
          parallel_rx_count = parallel_rx_count + 1;
      end
      if (parallel_tx_count != 0 || parallel_rx_count != 16 ||
          tx_desc_valid != 16'h0000 || rx_desc_valid != 16'hffff)
        $fatal(1, "parallel RX lead mismatch tx_valid=%h rx_valid=%h tx=%0d rx=%0d",
          tx_desc_valid, rx_desc_valid, parallel_tx_count, parallel_rx_count);
      @(posedge clk);
      @(negedge clk);
      #0;
      parallel_tx_count = 0;
      parallel_rx_count = 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (tx_desc_valid[endpoint_i] && tx_desc_ready[endpoint_i])
          parallel_tx_count = parallel_tx_count + 1;
        if (rx_desc_valid[endpoint_i] && rx_desc_ready[endpoint_i])
          parallel_rx_count = parallel_rx_count + 1;
      end
      if (parallel_tx_count != 16 || parallel_rx_count != 16 ||
          tx_desc_valid != 16'hffff || rx_desc_valid != 16'hffff)
        $fatal(1, "parallel descriptor issue mismatch tx_valid=%h rx_valid=%h tx=%0d rx=%0d",
          tx_desc_valid, rx_desc_valid, parallel_tx_count, parallel_rx_count);
      $display("PASS engine parallel_descriptors rx_lead=16 tx=%0d rx=%0d",
        parallel_tx_count, parallel_rx_count);
      $finish;
    end else if ($test$plusargs("INVALID_CASE")) begin
      @(negedge clk);
      context_source = 4'd3;
      context_destination = 4'd3;
      context_source_base_addr = 32'h1000;
      context_destination_base_addr = 32'h2000;
      context_packet_count = MAX_PACKETS_PER_CONTEXT;
      context_valid = 1'b1;
      @(posedge clk);
      if (!context_ready)
        $fatal(1, "invalid command did not handshake structurally");
      @(negedge clk);
      context_valid = 1'b0;
      if (!protocol_error)
        $fatal(1, "invalid local command did not set protocol_error");
      @(negedge clk);
      context_source = 4'd1;
      context_destination = 4'd2;
      context_source_base_addr = 32'h3000;
      context_destination_base_addr = 32'h4000;
      context_packet_count = MAX_PACKETS_PER_CONTEXT;
      context_valid = 1'b1;
      @(posedge clk);
      if (context_ready)
        $fatal(1, "engine accepted a command after protocol_error");
      @(negedge clk);
      context_valid = 1'b0;
      $display("PASS engine invalid_command_fail_closed");
      $finish;
    end else begin
      for (wave_i = 0; wave_i < 8; wave_i = wave_i + 1) begin
        if (wave_i != 4)
          for (lane_i = 0; lane_i < 16; lane_i = lane_i + 1)
            if (submitted_contexts < TEST_CONTEXT_COUNT)
              submit_context(wave_i, lane_i);
      end
      wait (completion_count == TEST_CONTEXT_COUNT);
      repeat (20) @(negedge clk);
      if (command_count != TEST_CONTEXT_COUNT ||
          tx_descriptor_count != expected_descriptor_count ||
          rx_descriptor_count != expected_descriptor_count ||
          write_count != expected_flit_count ||
          completion_count != TEST_CONTEXT_COUNT ||
          ((TEST_CONTEXT_COUNT >= 16) &&
           (descriptor_backpressure == 0 || held_completion_checks == 0)) || protocol_error ||
          (TEST_CONTEXT_COUNT >= 16 &&
           (max_tx_valid_per_cycle < 2 || max_rx_valid_per_cycle < 2)))
        $fatal(1,
          "engine mismatch commands=%0d tx=%0d rx=%0d writes=%0d completions=%0d bp=%0d holds=%0d max_tx_valid=%0d max_rx_valid=%0d max_tx_fire=%0d max_rx_fire=%0d error=%0d",
          command_count, tx_descriptor_count, rx_descriptor_count, write_count,
          completion_count, descriptor_backpressure, held_completion_checks,
          max_tx_valid_per_cycle, max_rx_valid_per_cycle,
          max_tx_descriptors_per_cycle, max_rx_descriptors_per_cycle, protocol_error);
      $display("PASS engine contexts=%0d descriptors=%0d flits=%0d", command_count,
        tx_descriptor_count, write_count);
      $finish;
    end
  end

  initial begin
    #100000000;
    $fatal(1, "engine simulation timeout");
  end
endmodule
