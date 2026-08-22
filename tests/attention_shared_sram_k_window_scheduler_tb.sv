`timescale 1ns/1ps

module attention_shared_sram_k_window_scheduler_tb;
  localparam integer ADDR_W = 16;
  localparam integer BANKS = 17;
  localparam integer WORDS = 128;
  localparam integer GROUPS = 8;
  localparam integer DIMS = 16;
  localparam integer GROUP_W = 3;
  localparam integer SLOT_W = 7;
  localparam integer DIM_W = 4;
  localparam integer BASE_WORD = 5;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  reg command_valid = 1'b0;
  wire command_ready;

  wire [BANKS-1:0] bank_req_valid;
  reg [BANKS-1:0] bank_req_ready;
  wire [(BANKS*ADDR_W)-1:0] bank_req_word_addr;
  wire [BANKS-1:0] bank_req_buffer;
  wire [(BANKS*GROUP_W)-1:0] bank_req_group;
  wire [(BANKS*SLOT_W)-1:0] bank_req_slot;

  reg [BANKS-1:0] bank_rsp_valid = 0;
  wire [BANKS-1:0] bank_rsp_ready;
  reg [(BANKS*1024)-1:0] bank_rsp_data = 0;
  reg [BANKS-1:0] bank_rsp_buffer = 0;
  reg [(BANKS*GROUP_W)-1:0] bank_rsp_group = 0;
  reg [(BANKS*SLOT_W)-1:0] bank_rsp_slot = 0;

  wire compute_valid;
  reg compute_ready;
  wire [GROUP_W-1:0] compute_group;
  wire [DIM_W-1:0] compute_dimension;
  wire compute_last;
  wire [(WORDS*64)-1:0] compute_k_beats;
  wire done;
  wire protocol_error;
  wire [63:0] bank_request_count;
  wire [63:0] bank_response_count;
  wire [63:0] compute_beat_count;
  wire [63:0] bank_request_stall_count;
  wire [63:0] bank_response_stall_count;
  wire [63:0] compute_output_stall_count;
  wire [63:0] compute_wait_for_window_count;

  reg request_seen [0:GROUPS-1][0:WORDS-1];
  integer first_request_cycle [0:GROUPS-1];
  integer last_request_cycle [0:GROUPS-1];
  integer request_count_by_group [0:GROUPS-1];
  integer compute_start_cycle [0:GROUPS-1];
  integer compute_end_cycle [0:GROUPS-1];
  integer expected_compute_group = 0;
  integer expected_compute_dimension = 0;
  integer last_compute_cycle = -1;
  integer max_compute_interval = 0;
  integer compute_count = 0;
  integer bank_i;
  integer group_i;
  integer slot_i;
  integer addr_i;
  integer word_i;
  reg backpressure_case;
  reg malformed_case;
  reg malformed_sent = 1'b0;

  attention_shared_sram_k_window_scheduler #(
    .ADDR_W(ADDR_W),
    .BANKS(BANKS),
    .WORDS_PER_GROUP(WORDS),
    .DIM_GROUPS(GROUPS),
    .DIMS_PER_GROUP(DIMS)
  ) dut (
    .clk(clk), .rst_n(rst_n),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_base_word_addr(ADDR_W'(BASE_WORD)),
    .bank_req_valid(bank_req_valid), .bank_req_ready(bank_req_ready),
    .bank_req_word_addr(bank_req_word_addr),
    .bank_req_buffer(bank_req_buffer), .bank_req_group(bank_req_group),
    .bank_req_slot(bank_req_slot),
    .bank_rsp_valid(bank_rsp_valid), .bank_rsp_ready(bank_rsp_ready),
    .bank_rsp_data(bank_rsp_data), .bank_rsp_buffer(bank_rsp_buffer),
    .bank_rsp_group(bank_rsp_group), .bank_rsp_slot(bank_rsp_slot),
    .compute_valid(compute_valid), .compute_ready(compute_ready),
    .compute_group(compute_group), .compute_dimension(compute_dimension),
    .compute_last(compute_last), .compute_k_beats(compute_k_beats),
    .done(done), .protocol_error(protocol_error),
    .bank_request_count(bank_request_count),
    .bank_response_count(bank_response_count),
    .compute_beat_count(compute_beat_count),
    .bank_request_stall_count(bank_request_stall_count),
    .bank_response_stall_count(bank_response_stall_count),
    .compute_output_stall_count(compute_output_stall_count),
    .compute_wait_for_window_count(compute_wait_for_window_count)
  );

  always #5 clk = ~clk;

  function [63:0] expected_lane;
    input integer group_value;
    input integer slot_value;
    input integer dimension_value;
    begin
      expected_lane = 64'h4b00_0000_0000_0000 |
        (group_value << 16) | (slot_value << 8) | dimension_value;
    end
  endfunction

  function [1023:0] expected_word;
    input integer group_value;
    input integer slot_value;
    integer dimension_value;
    begin
      expected_word = 1024'd0;
      for (dimension_value = 0; dimension_value < DIMS;
           dimension_value = dimension_value + 1)
        expected_word[dimension_value*64 +: 64] =
          expected_lane(group_value, slot_value, dimension_value);
    end
  endfunction

  always @* begin
    for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1)
      bank_req_ready[bank_i] = !backpressure_case ||
        (((cycle + bank_i) % 4) != 0);
    compute_ready = !backpressure_case || ((cycle % 5) != 2);
  end

  // One-cycle pipelined bank response.  Every bank can accept and return one
  // word per cycle, matching the intended independently banked macro array.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      bank_rsp_valid <= {BANKS{1'b0}};
      bank_rsp_data <= {(BANKS*1024){1'b0}};
      bank_rsp_buffer <= {BANKS{1'b0}};
      bank_rsp_group <= {(BANKS*GROUP_W){1'b0}};
      bank_rsp_slot <= {(BANKS*SLOT_W){1'b0}};
      malformed_sent <= 1'b0;
    end else begin
      cycle <= cycle + 1;
      bank_rsp_valid <= bank_req_valid & bank_req_ready;
      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        if (bank_req_valid[bank_i] && bank_req_ready[bank_i]) begin
          group_i = bank_req_group[bank_i*GROUP_W +: GROUP_W];
          slot_i = bank_req_slot[bank_i*SLOT_W +: SLOT_W];
          bank_rsp_buffer[bank_i] <= bank_req_buffer[bank_i];
          bank_rsp_group[bank_i*GROUP_W +: GROUP_W] <=
            (malformed_case && !malformed_sent) ? GROUP_W'(group_i + 1) :
            GROUP_W'(group_i);
          bank_rsp_slot[bank_i*SLOT_W +: SLOT_W] <= SLOT_W'(slot_i);
          bank_rsp_data[bank_i*1024 +: 1024] <= expected_word(group_i, slot_i);
          if (malformed_case && !malformed_sent)
            malformed_sent <= 1'b1;
        end
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        if (bank_req_valid[bank_i] && bank_req_ready[bank_i]) begin
          group_i = bank_req_group[bank_i*GROUP_W +: GROUP_W];
          slot_i = bank_req_slot[bank_i*SLOT_W +: SLOT_W];
          addr_i = bank_req_word_addr[bank_i*ADDR_W +: ADDR_W];
          if (addr_i != BASE_WORD + slot_i*GROUPS + group_i)
            $fatal(1, "request address mismatch bank=%0d group=%0d slot=%0d addr=%0d",
                   bank_i, group_i, slot_i, addr_i);
          if ((addr_i % BANKS) != bank_i)
            $fatal(1, "request routed to wrong bank");
          if (request_seen[group_i][slot_i])
            $fatal(1, "duplicate request group=%0d slot=%0d", group_i, slot_i);
          request_seen[group_i][slot_i] <= 1'b1;
          request_count_by_group[group_i] = request_count_by_group[group_i] + 1;
          if (first_request_cycle[group_i] < 0)
            first_request_cycle[group_i] <= cycle;
          last_request_cycle[group_i] <= cycle;
        end
      end

      if (compute_valid && compute_ready) begin
        if (compute_group != expected_compute_group ||
            compute_dimension != expected_compute_dimension)
          $fatal(1, "compute order mismatch got g=%0d d=%0d expected g=%0d d=%0d",
                 compute_group, compute_dimension,
                 expected_compute_group, expected_compute_dimension);
        if (compute_last != (expected_compute_dimension == DIMS-1))
          $fatal(1, "compute_last mismatch");
        for (word_i = 0; word_i < WORDS; word_i = word_i + 1)
          if (compute_k_beats[word_i*64 +: 64] !==
              expected_lane(expected_compute_group, word_i,
                            expected_compute_dimension))
            $fatal(1, "compute K data mismatch g=%0d d=%0d word=%0d",
                   expected_compute_group, expected_compute_dimension, word_i);
        if (last_compute_cycle >= 0 &&
            cycle - last_compute_cycle > max_compute_interval)
          max_compute_interval <= cycle - last_compute_cycle;
        last_compute_cycle <= cycle;
        compute_count <= compute_count + 1;
        if (expected_compute_dimension == 0)
          compute_start_cycle[expected_compute_group] <= cycle;
        if (expected_compute_dimension == DIMS-1) begin
          compute_end_cycle[expected_compute_group] <= cycle;
          expected_compute_dimension <= 0;
          expected_compute_group <= expected_compute_group + 1;
        end else begin
          expected_compute_dimension <= expected_compute_dimension + 1;
        end
      end

      if (malformed_case && protocol_error) begin
        $display("PASS k_window malformed_response requests=%0d responses=%0d",
                 bank_request_count, bank_response_count);
        $finish;
      end

      if (done) begin
        if (protocol_error)
          $fatal(1, "protocol_error asserted in valid run");
        if (bank_request_count != GROUPS*WORDS ||
            bank_response_count != GROUPS*WORDS ||
            compute_beat_count != GROUPS*DIMS ||
            compute_count != GROUPS*DIMS)
          $fatal(1, "counter mismatch req=%0d rsp=%0d compute=%0d observed=%0d",
                 bank_request_count, bank_response_count,
                 compute_beat_count, compute_count);
        for (group_i = 0; group_i < GROUPS; group_i = group_i + 1) begin
          if (request_count_by_group[group_i] != WORDS)
            $fatal(1, "group request count mismatch group=%0d count=%0d",
                   group_i, request_count_by_group[group_i]);
          if (!backpressure_case &&
              last_request_cycle[group_i] - first_request_cycle[group_i] != 7)
            $fatal(1, "ideal group did not issue in eight cycles group=%0d span=%0d",
                   group_i,
                   last_request_cycle[group_i] - first_request_cycle[group_i]);
          $display("TRACE group=%0d first_req=%0d last_req=%0d compute_start=%0d compute_end=%0d",
                   group_i, first_request_cycle[group_i],
                   last_request_cycle[group_i], compute_start_cycle[group_i],
                   compute_end_cycle[group_i]);
        end
        if (!backpressure_case && max_compute_interval != 1)
          $fatal(1, "double buffering did not sustain one compute beat/cycle interval=%0d",
                 max_compute_interval);
        if (backpressure_case &&
            (bank_request_stall_count == 0 || compute_output_stall_count == 0))
          $fatal(1, "backpressure counters were not exercised");
        $display("PASS k_window backpressure=%0d requests=%0d responses=%0d compute=%0d max_compute_interval=%0d request_stalls=%0d compute_stalls=%0d wait=%0d",
                 backpressure_case, bank_request_count, bank_response_count,
                 compute_beat_count, max_compute_interval,
                 bank_request_stall_count, compute_output_stall_count,
                 compute_wait_for_window_count);
        $finish;
      end

      if (cycle > 5000)
        $fatal(1, "timeout");
    end
  end

  initial begin
    backpressure_case = $test$plusargs("BACKPRESSURE");
    malformed_case = $test$plusargs("MALFORMED");
    for (group_i = 0; group_i < GROUPS; group_i = group_i + 1) begin
      first_request_cycle[group_i] = -1;
      last_request_cycle[group_i] = -1;
      request_count_by_group[group_i] = 0;
      compute_start_cycle[group_i] = -1;
      compute_end_cycle[group_i] = -1;
      for (slot_i = 0; slot_i < WORDS; slot_i = slot_i + 1)
        request_seen[group_i][slot_i] = 1'b0;
    end
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    @(negedge clk);
    command_valid = 1'b1;
    @(posedge clk);
    while (!command_ready) @(posedge clk);
    @(negedge clk);
    command_valid = 1'b0;
  end
endmodule
