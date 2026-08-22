`timescale 1ns/1ps

module attention_shared_stream_context_admission_tb;
  localparam integer ADDR_W = 32;
  localparam integer PACKET_INDEX_W = 7;
  localparam integer PACKET_COUNT_W = PACKET_INDEX_W + 1;
  localparam integer LEGAL_WAVES = 7;
  localparam integer CONTEXT_COUNT = 112;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg layer_start = 1'b0;
  reg layer_idle = 1'b1;
  reg [7:0] layer_expected_remote_contexts = 0;
  reg [15:0] event_valid = 16'b0;
  wire [15:0] event_ready;
  reg [16*3-1:0] event_wave = 0;
  reg [16*4-1:0] event_source = 0;
  reg [16*ADDR_W-1:0] event_source_base_addr = 0;
  reg [16*ADDR_W-1:0] event_destination_base_addr = 0;
  reg [16*PACKET_COUNT_W-1:0] event_packet_count = 0;
  wire context_valid;
  reg context_ready = 1'b0;
  wire [2:0] context_wave;
  wire [3:0] context_destination;
  wire [3:0] context_cluster;
  wire [3:0] context_source;
  wire [ADDR_W-1:0] context_source_base_addr;
  wire [ADDR_W-1:0] context_destination_base_addr;
  wire [PACKET_INDEX_W:0] context_packet_count;
  wire layer_active;
  wire layer_complete;
  wire [7:0] admitted_count;
  wire protocol_error;

  integer cycle = 0;
  integer observed = 0;
  integer wave_i;
  integer lane_i;
  integer output_index;
  integer held_checks = 0;
  reg error_mode = 1'b0;
  reg held_valid = 1'b0;
  reg [2:0] held_wave = 0;
  reg [3:0] held_cluster = 0;
  reg [3:0] held_source = 0;
  reg [ADDR_W-1:0] held_source_base = 0;
  reg [ADDR_W-1:0] held_destination_base = 0;
  reg [PACKET_COUNT_W-1:0] held_packet_count = 0;
  reg seen [0:127];

  attention_shared_stream_context_admission #(.ADDR_W(ADDR_W)) dut (
    .clk(clk), .rst_n(rst_n), .layer_start(layer_start), .layer_idle(layer_idle),
    .layer_expected_remote_contexts(layer_expected_remote_contexts),
    .event_valid(event_valid), .event_ready(event_ready), .event_wave(event_wave),
    .event_source(event_source),
    .event_source_base_addr(event_source_base_addr),
    .event_destination_base_addr(event_destination_base_addr),
    .event_packet_count(event_packet_count),
    .context_valid(context_valid), .context_ready(context_ready),
    .context_wave(context_wave), .context_cluster(context_cluster),
    .context_destination(context_destination),
    .context_source(context_source),
    .context_source_base_addr(context_source_base_addr),
    .context_destination_base_addr(context_destination_base_addr),
    .context_packet_count(context_packet_count),
    .layer_active(layer_active), .layer_complete(layer_complete),
    .admitted_count(admitted_count), .protocol_error(protocol_error)
  );

  always #1 clk = ~clk;

  function [3:0] expected_shift;
    input integer wave;
    begin
      case (wave)
        0: expected_shift = 4;
        1: expected_shift = 7;
        2: expected_shift = 10;
        3: expected_shift = 13;
        5: expected_shift = 3;
        6: expected_shift = 6;
        default: expected_shift = 9;
      endcase
    end
  endfunction

  function [ADDR_W-1:0] source_base;
    input integer wave;
    input integer lane;
    begin
      source_base = 32'h0010_0000 + (wave * 32'h0001_0000) + (lane * 32'h0000_0100);
    end
  endfunction

  function [ADDR_W-1:0] destination_base;
    input integer wave;
    input integer lane;
    begin
      destination_base = 32'h0020_0000 + (wave * 32'h0001_0000) + (lane * 32'h0000_0100);
    end
  endfunction

  task send_wave;
    input integer wave;
    begin
      @(negedge clk);
      event_valid = 16'hffff;
      for (lane_i = 0; lane_i < 16; lane_i = lane_i + 1) begin
        event_wave[(lane_i*3) +: 3] = wave[2:0];
        event_source[(lane_i*4) +: 4] = lane_i[3:0] + expected_shift(wave);
        event_source_base_addr[(lane_i*ADDR_W) +: ADDR_W] = source_base(wave, lane_i);
        event_destination_base_addr[(lane_i*ADDR_W) +: ADDR_W] = destination_base(wave, lane_i);
        event_packet_count[(lane_i*PACKET_COUNT_W) +: PACKET_COUNT_W] = 68;
      end
      @(posedge clk);
      if (event_ready !== 16'hffff)
        $fatal(1, "event lanes were not ready for wave %0d", wave);
      @(negedge clk);
      event_valid = 16'b0;
    end
  endtask

  task start_layer;
    input integer expected_count;
    begin
      @(negedge clk);
      layer_expected_remote_contexts = expected_count;
      layer_start = 1'b1;
      @(posedge clk);
      @(negedge clk);
      layer_start = 1'b0;
    end
  endtask

  task send_one;
    input integer wave;
    input integer lane;
    input integer source;
    begin
      @(negedge clk);
      event_valid = (16'b1 << lane);
      event_wave[(lane*3) +: 3] = wave[2:0];
      event_source[(lane*4) +: 4] = source[3:0];
      event_source_base_addr[(lane*ADDR_W) +: ADDR_W] = source_base(wave, lane);
      event_destination_base_addr[(lane*ADDR_W) +: ADDR_W] = destination_base(wave, lane);
      event_packet_count[(lane*PACKET_COUNT_W) +: PACKET_COUNT_W] = 68;
      @(posedge clk);
      @(negedge clk);
      event_valid = 16'b0;
    end
  endtask

  always @(posedge clk) begin
    if (rst_n) begin
      cycle = cycle + 1;
      context_ready <= error_mode ? 1'b0 : (((cycle % 7) != 3) && ((cycle % 11) != 5));
      if (context_valid && !context_ready) begin
        if (held_valid) begin
          if (context_wave !== held_wave || context_cluster !== held_cluster ||
              context_source !== held_source ||
              context_source_base_addr !== held_source_base ||
              context_destination_base_addr !== held_destination_base ||
              context_packet_count !== held_packet_count)
            $fatal(1, "admission output changed under backpressure");
          held_checks = held_checks + 1;
        end else begin
          held_valid <= 1'b1;
          held_wave <= context_wave;
          held_cluster <= context_cluster;
          held_source <= context_source;
          held_source_base <= context_source_base_addr;
          held_destination_base <= context_destination_base_addr;
          held_packet_count <= context_packet_count;
        end
      end else begin
        held_valid <= 1'b0;
      end

      if (context_valid && context_ready) begin
        output_index = (context_wave * 16) + context_cluster;
        if (context_destination !== context_cluster)
          $fatal(1, "destination alias mismatch");
        if (seen[output_index])
          $fatal(1, "duplicate or local context wave=%0d cluster=%0d", context_wave, context_cluster);
        seen[output_index] = 1'b1;
        if (context_source !== context_cluster + expected_shift(context_wave))
          $fatal(1, "source shift mismatch wave=%0d cluster=%0d source=%0d",
            context_wave, context_cluster, context_source);
        if (context_source_base_addr !== source_base(context_wave, context_cluster) ||
            context_destination_base_addr !== destination_base(context_wave, context_cluster) ||
            context_packet_count !== 68)
          $fatal(1, "base address metadata mismatch wave=%0d cluster=%0d",
            context_wave, context_cluster);
        observed = observed + 1;
      end
    end
  end

  initial begin
    for (lane_i = 0; lane_i < 128; lane_i = lane_i + 1)
      seen[lane_i] = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    if ($test$plusargs("EMPTY_CASE")) begin
      start_layer(0);
      if (!layer_complete || layer_active || admitted_count != 0 || protocol_error)
        $fatal(1, "zero-context layer did not complete cleanly");
      $display("PASS admission empty_layer");
      $finish;
    end else if ($test$plusargs("ERROR_CASE")) begin
      start_layer(1);
      send_one(0, 0, 0);
      if (!protocol_error || event_ready != 0 || context_valid)
        $fatal(1, "local event did not fail closed");
      send_one(0, 1, 5);
      if (event_ready != 0 || context_valid)
        $fatal(1, "admission resumed after invalid event");
      $display("PASS admission invalid_event_fail_closed");
      $finish;
    end else if ($test$plusargs("DUPLICATE_CASE")) begin
      error_mode = 1'b1;
      start_layer(2);
      send_one(0, 1, 5);
      send_one(0, 1, 5);
      if (!protocol_error || event_ready != 0 || context_valid)
        $fatal(1, "duplicate event did not fail closed");
      $display("PASS admission duplicate_event_fail_closed");
      $finish;
    end else begin
      start_layer(CONTEXT_COUNT);
      send_wave(5);
      send_wave(2);
      send_wave(0);
      send_wave(7);
      send_wave(1);
      send_wave(6);
      send_wave(3);
      wait (layer_complete && observed == CONTEXT_COUNT);
      if (admitted_count != CONTEXT_COUNT || protocol_error || held_checks == 0)
        $fatal(1, "admission mismatch admitted=%0d observed=%0d error=%0d holds=%0d",
          admitted_count, observed, protocol_error, held_checks);
      $display("PASS admission contexts=%0d holds=%0d", observed, held_checks);
      $finish;
    end
  end

  initial begin
    #100000;
    $fatal(1, "admission simulation timeout");
  end
endmodule
