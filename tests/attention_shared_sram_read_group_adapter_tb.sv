`timescale 1ns/1ps

module attention_shared_sram_read_group_adapter_tb #(
  parameter integer BEAT_W = 256,
  parameter integer GROUP_SLOTS = 2,
  parameter integer TEST_GROUPS = 4
);
  localparam integer ADDR_W = 32;
  localparam integer MACRO_W = 1024;
  localparam integer MACRO_BYTES = MACRO_W / 8;
  localparam integer BEAT_BYTES = BEAT_W / 8;
  localparam integer SEGMENTS = MACRO_W / BEAT_W;
  localparam integer SLOT_W = (GROUP_SLOTS <= 1) ? 1 : $clog2(GROUP_SLOTS);
  localparam integer GROUP_COUNT = TEST_GROUPS;
  localparam integer TOTAL_REQUESTS = GROUP_COUNT * SEGMENTS;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;

  reg req_valid = 1'b0;
  wire req_ready;
  reg [ADDR_W-1:0] req_addr = 0;
  wire rsp_valid;
  reg rsp_ready = 1'b0;
  wire [BEAT_W-1:0] rsp_data;
  wire [ADDR_W-1:0] rsp_addr;

  wire macro_req_valid;
  reg macro_req_ready = 1'b1;
  wire [ADDR_W-1:0] macro_req_addr;
  wire [SLOT_W-1:0] macro_req_slot;
  reg macro_rsp_valid = 1'b0;
  wire macro_rsp_ready;
  reg [MACRO_W-1:0] macro_rsp_data = 0;
  reg [ADDR_W-1:0] macro_rsp_addr = 0;
  reg [SLOT_W-1:0] macro_rsp_slot = 0;

  wire protocol_error;
  wire [63:0] beat_request_count;
  wire [63:0] macro_read_count;
  wire [63:0] beat_response_count;
  wire [63:0] beat_request_stall_count;
  wire [63:0] beat_response_stall_count;
  wire [63:0] macro_request_stall_count;
  wire [63:0] macro_response_stall_count;
  wire access_reduction_proven;

  reg macro_pending = 1'b0;
  integer macro_delay = 0;
  reg steady_case = 1'b0;
  reg invalid_meta_case = 1'b0;
  integer request_fire_cycle = -1;
  integer first_response_cycle = -1;
  integer response_count = 0;
  integer last_response_cycle = -1;
  integer max_response_interval = 0;
  integer held_response_valid = 0;
  reg [BEAT_W-1:0] held_response_data = 0;
  reg [ADDR_W-1:0] held_response_addr = 0;
  integer held_request_valid = 0;
  reg [ADDR_W-1:0] held_request_addr = 0;
  integer held_macro_request_valid = 0;
  reg [ADDR_W-1:0] held_macro_request_addr = 0;
  reg [SLOT_W-1:0] held_macro_request_slot = 0;

  attention_shared_sram_read_group_adapter #(
    .ADDR_W(ADDR_W),
    .BEAT_W(BEAT_W),
    .GROUP_SLOTS(GROUP_SLOTS)
  ) dut (
    .clk(clk), .rst_n(rst_n),
    .req_valid(req_valid), .req_ready(req_ready), .req_addr(req_addr),
    .rsp_valid(rsp_valid), .rsp_ready(rsp_ready), .rsp_data(rsp_data),
    .rsp_addr(rsp_addr),
    .macro_req_valid(macro_req_valid), .macro_req_ready(macro_req_ready),
    .macro_req_addr(macro_req_addr), .macro_req_slot(macro_req_slot),
    .macro_rsp_valid(macro_rsp_valid), .macro_rsp_ready(macro_rsp_ready),
    .macro_rsp_data(macro_rsp_data), .macro_rsp_addr(macro_rsp_addr),
    .macro_rsp_slot(macro_rsp_slot), .protocol_error(protocol_error),
    .beat_request_count(beat_request_count),
    .macro_read_count(macro_read_count),
    .beat_response_count(beat_response_count),
    .beat_request_stall_count(beat_request_stall_count),
    .beat_response_stall_count(beat_response_stall_count),
    .macro_request_stall_count(macro_request_stall_count),
    .macro_response_stall_count(macro_response_stall_count),
    .access_reduction_proven(access_reduction_proven)
  );

  always #5 clk = ~clk;

  function [BEAT_W-1:0] expected_beat;
    input [ADDR_W-1:0] address;
    integer word_i;
    begin
      expected_beat = {BEAT_W{1'b0}};
      for (word_i = 0; word_i < BEAT_W / 32; word_i = word_i + 1)
        expected_beat[word_i*32 +: 32] = address[31:0] ^
          (32'h5100_0000 + word_i);
    end
  endfunction

  function [MACRO_W-1:0] expected_macro_word;
    input [ADDR_W-1:0] address;
    integer segment_i;
    begin
      expected_macro_word = {MACRO_W{1'b0}};
      for (segment_i = 0; segment_i < SEGMENTS; segment_i = segment_i + 1)
        expected_macro_word[segment_i*BEAT_W +: BEAT_W] =
          expected_beat(address + segment_i * BEAT_BYTES);
    end
  endfunction

  always @(*) begin
    // Periodic request backpressure exercises descriptor stability.
    macro_req_ready = steady_case || ((cycle % 5) != 2);
    if (steady_case)
      rsp_ready = 1'b1;
    else
      rsp_ready = (cycle >= 20) && ((cycle % 4) != 1);
  end

  // A two-cycle-or-less synchronous macro response model.  The response
  // metadata is intentionally echoed so the adapter can validate ownership.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      macro_pending <= 1'b0;
      macro_delay <= 0;
      macro_rsp_valid <= 1'b0;
      macro_rsp_data <= {MACRO_W{1'b0}};
      macro_rsp_addr <= {ADDR_W{1'b0}};
      macro_rsp_slot <= {SLOT_W{1'b0}};
    end else begin
      cycle <= cycle + 1;
      if (macro_rsp_valid && macro_rsp_ready)
        macro_rsp_valid <= 1'b0;

      if (macro_req_valid && macro_req_ready) begin
        if (macro_pending || (macro_rsp_valid && !macro_rsp_ready))
          $fatal(1, "macro port accepted a second transaction");
        macro_pending <= 1'b1;
        macro_delay <= 0;
        macro_rsp_data <= expected_macro_word(macro_req_addr);
        macro_rsp_addr <= invalid_meta_case ?
          (macro_req_addr + MACRO_BYTES) : macro_req_addr;
        macro_rsp_slot <= macro_req_slot;
      end

      if (macro_pending && !macro_rsp_valid) begin
        if (macro_delay == 0) begin
          macro_pending <= 1'b0;
          macro_rsp_valid <= 1'b1;
        end else begin
          macro_delay <= macro_delay - 1;
        end
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      request_fire_cycle <= -1;
      first_response_cycle <= -1;
      response_count <= 0;
      last_response_cycle <= -1;
      max_response_interval <= 0;
      held_response_valid <= 0;
      held_request_valid <= 0;
      held_macro_request_valid <= 0;
    end else begin
      if (req_valid && req_ready && request_fire_cycle < 0)
        request_fire_cycle <= cycle;

      if (req_valid && !req_ready) begin
        if (held_request_valid && held_request_addr !== req_addr)
          $fatal(1, "request address changed under backpressure");
        held_request_valid <= 1;
        held_request_addr <= req_addr;
      end else begin
        held_request_valid <= 0;
      end

      if (macro_req_valid && !macro_req_ready) begin
        if (held_macro_request_valid &&
            (held_macro_request_addr !== macro_req_addr ||
             held_macro_request_slot !== macro_req_slot))
          $fatal(1, "macro request changed under backpressure");
        held_macro_request_valid <= 1;
        held_macro_request_addr <= macro_req_addr;
        held_macro_request_slot <= macro_req_slot;
      end else begin
        held_macro_request_valid <= 0;
      end

      if (rsp_valid && !rsp_ready) begin
        if (held_response_valid &&
            (held_response_data !== rsp_data || held_response_addr !== rsp_addr))
          $fatal(1, "response changed under backpressure");
        held_response_valid <= 1;
        held_response_data <= rsp_data;
        held_response_addr <= rsp_addr;
      end else begin
        held_response_valid <= 0;
      end

      if (rsp_valid && rsp_ready) begin
        if (first_response_cycle < 0)
          first_response_cycle <= cycle;
        if (last_response_cycle >= 0 &&
            cycle - last_response_cycle > max_response_interval)
          max_response_interval <= cycle - last_response_cycle;
        last_response_cycle <= cycle;
        if (rsp_data !== expected_beat(rsp_addr))
          $fatal(1, "response payload mismatch addr=%h", rsp_addr);
        if (rsp_addr[$clog2(BEAT_BYTES)-1:0] != 0)
          $fatal(1, "response address is not beat aligned");
        response_count <= response_count + 1;
      end
    end
  end

  task send_request;
    input [ADDR_W-1:0] address;
    begin
      @(negedge clk);
      req_valid = 1'b1;
      req_addr = address;
      @(posedge clk);
      while (!req_ready) @(posedge clk);
      @(negedge clk);
      req_valid = 1'b0;
    end
  endtask

  task send_request_stream;
    integer request_i;
    integer next_group;
    integer next_segment;
    begin
      @(negedge clk);
      req_valid = 1'b1;
      req_addr = 32'h0000_1000;
      for (request_i = 0; request_i < TOTAL_REQUESTS; request_i = request_i + 1) begin
        @(posedge clk);
        while (!req_ready) @(posedge clk);
        if (request_i + 1 < TOTAL_REQUESTS) begin
          next_group = (request_i + 1) / SEGMENTS;
          next_segment = (request_i + 1) % SEGMENTS;
          @(negedge clk);
          req_addr = 32'h0000_1000 + next_group * MACRO_BYTES +
                     next_segment * BEAT_BYTES;
        end else begin
          @(negedge clk);
          req_valid = 1'b0;
        end
      end
    end
  endtask

  task send_malformed_sequence;
    begin
      send_request(32'h0000_1000);
      @(negedge clk);
      req_valid = 1'b1;
      req_addr = 32'h0000_1000 + (2 * BEAT_BYTES);
      repeat (4) @(posedge clk);
      if (!protocol_error)
        $fatal(1, "nonsequential request did not set protocol_error");
      @(negedge clk);
      req_valid = 1'b0;
      $display("PASS adapter malformed_sequence BEAT_W=%0d", BEAT_W);
      $finish;
    end
  endtask

  task send_orphan_response;
    begin
      @(negedge clk);
      macro_rsp_valid = 1'b1;
      macro_rsp_data = {MACRO_W{1'b0}};
      macro_rsp_addr = 32'h0000_1000;
      macro_rsp_slot = {SLOT_W{1'b0}};
      repeat (3) @(posedge clk);
      if (!protocol_error)
        $fatal(1, "orphan macro response did not set protocol_error");
      @(negedge clk);
      macro_rsp_valid = 1'b0;
      $display("PASS adapter orphan_response BEAT_W=%0d", BEAT_W);
      $finish;
    end
  endtask

  integer group_i;
  integer segment_i;
  initial begin
    steady_case = $test$plusargs("STEADY");
    invalid_meta_case = $test$plusargs("INVALID_META");
    if ($test$plusargs("MALFORMED")) begin
      repeat (3) @(negedge clk);
      rst_n = 1'b1;
      send_malformed_sequence;
    end
    if ($test$plusargs("ORPHAN")) begin
      repeat (3) @(negedge clk);
      rst_n = 1'b1;
      send_orphan_response;
    end

    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    fork
      begin
        send_request_stream;
      end
      begin
        wait (protocol_error || response_count == TOTAL_REQUESTS);
      end
    join_any
    if (invalid_meta_case) begin
      if (!protocol_error)
        $fatal(1, "invalid macro metadata did not set protocol_error");
      $display("PASS adapter invalid_metadata BEAT_W=%0d", BEAT_W);
      $finish;
    end
    if (protocol_error && !invalid_meta_case)
      $fatal(1, "normal adapter case raised protocol_error");
    if (response_count != TOTAL_REQUESTS) begin
      repeat (200) @(posedge clk);
      if (response_count != TOTAL_REQUESTS)
        $fatal(1, "response timeout count=%0d expected=%0d",
               response_count, TOTAL_REQUESTS);
    end
    if (beat_request_count !== TOTAL_REQUESTS ||
        macro_read_count !== GROUP_COUNT ||
        beat_response_count !== TOTAL_REQUESTS ||
        !access_reduction_proven)
      $fatal(1, "wrong final counters req=%0d macro=%0d rsp=%0d reduction=%0d",
             beat_request_count, macro_read_count, beat_response_count,
             access_reduction_proven);
    if (steady_case && GROUP_SLOTS == 2 && max_response_interval > 1)
      $fatal(1, "steady-state response interval=%0d", max_response_interval);

    $display("PASS adapter BEAT_W=%0d GROUP_SLOTS=%0d requests=%0d macro_reads=%0d responses=%0d fill_latency=%0d steady_interval=%0d request_stalls=%0d response_stalls=%0d macro_request_stalls=%0d",
             BEAT_W, GROUP_SLOTS, beat_request_count, macro_read_count,
             beat_response_count, first_response_cycle - request_fire_cycle,
             max_response_interval, beat_request_stall_count,
             beat_response_stall_count, macro_request_stall_count);
    $finish;
  end

  initial begin
    #100000;
    $fatal(1, "adapter simulation timeout");
  end
endmodule
