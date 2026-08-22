`timescale 1ns/1ps

module attention_shared_sram_k_round_scheduler_tb;
  localparam integer ADDR_W = 16;
  localparam integer BANKS = 17;
  localparam integer WORDS = 128;
  localparam integer GROUPS = 8;
  localparam integer ROUNDS = 8;
  localparam integer DIMS = 16;
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
  wire [(BANKS*3)-1:0] bank_req_group;
  wire [(BANKS*3)-1:0] bank_req_round;
  wire [(BANKS*7)-1:0] bank_req_word_slot;

  reg [BANKS-1:0] bank_rsp_valid = 0;
  wire [BANKS-1:0] bank_rsp_ready;
  reg [(BANKS*1024)-1:0] bank_rsp_data = 0;
  reg [BANKS-1:0] bank_rsp_buffer = 0;
  reg [(BANKS*3)-1:0] bank_rsp_group = 0;
  reg [(BANKS*3)-1:0] bank_rsp_round = 0;
  reg [(BANKS*7)-1:0] bank_rsp_word_slot = 0;

  wire compute_valid;
  reg compute_ready;
  wire [2:0] compute_group;
  wire [2:0] compute_round;
  wire [3:0] compute_dimension;
  wire compute_last;
  wire [BANKS-1:0] compute_word_valid;
  wire [(BANKS*64)-1:0] compute_k_beats;

  wire done;
  wire protocol_error;
  wire [63:0] bank_request_count;
  wire [63:0] bank_response_count;
  wire [63:0] compute_beat_count;
  wire [63:0] bank_request_stall_count;
  wire [63:0] compute_output_stall_count;
  wire [63:0] compute_wait_for_window_count;

  reg request_seen [0:GROUPS-1][0:WORDS-1];
  integer request_count_by_round [0:(GROUPS*ROUNDS)-1];
  integer first_request_cycle [0:(GROUPS*ROUNDS)-1];
  integer compute_start_cycle [0:(GROUPS*ROUNDS)-1];
  integer compute_end_cycle [0:(GROUPS*ROUNDS)-1];
  integer expected_group = 0;
  integer expected_round = 0;
  integer expected_dimension = 0;
  integer compute_count = 0;
  integer last_compute_cycle = -1;
  integer max_compute_interval = 0;
  integer req_bank_i;
  integer rsp_bank_i;
  integer check_bank_i;
  integer init_group_i;
  integer init_slot_i;
  integer init_round_i;
  integer group_i;
  integer round_i;
  integer slot_i;
  integer local_i;
  integer linear_i;
  integer addr_i;
  integer valid_words_i;
  reg backpressure_case;
  reg malformed_case;
  reg malformed_sent = 1'b0;

  attention_shared_sram_k_round_scheduler #(
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
    .bank_req_buffer(bank_req_buffer),
    .bank_req_group(bank_req_group), .bank_req_round(bank_req_round),
    .bank_req_word_slot(bank_req_word_slot),
    .bank_rsp_valid(bank_rsp_valid), .bank_rsp_ready(bank_rsp_ready),
    .bank_rsp_data(bank_rsp_data), .bank_rsp_buffer(bank_rsp_buffer),
    .bank_rsp_group(bank_rsp_group), .bank_rsp_round(bank_rsp_round),
    .bank_rsp_word_slot(bank_rsp_word_slot),
    .compute_valid(compute_valid), .compute_ready(compute_ready),
    .compute_group(compute_group), .compute_round(compute_round),
    .compute_dimension(compute_dimension), .compute_last(compute_last),
    .compute_word_valid(compute_word_valid), .compute_k_beats(compute_k_beats),
    .done(done), .protocol_error(protocol_error),
    .bank_request_count(bank_request_count),
    .bank_response_count(bank_response_count),
    .compute_beat_count(compute_beat_count),
    .bank_request_stall_count(bank_request_stall_count),
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
    for (req_bank_i = 0; req_bank_i < BANKS; req_bank_i = req_bank_i + 1)
      bank_req_ready[req_bank_i] = !backpressure_case ||
        (((cycle + req_bank_i) % 4) != 0);
    compute_ready = !backpressure_case || ((cycle % 5) != 2);
  end

  // A one-register SRAM response pipe.  The request and response metadata are
  // preserved exactly so the DUT can reject stale, duplicate, or misrouted data.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      bank_rsp_valid <= {BANKS{1'b0}};
      bank_rsp_data <= {(BANKS*1024){1'b0}};
      bank_rsp_buffer <= {BANKS{1'b0}};
      bank_rsp_group <= {(BANKS*3){1'b0}};
      bank_rsp_round <= {(BANKS*3){1'b0}};
      bank_rsp_word_slot <= {(BANKS*7){1'b0}};
      malformed_sent <= 1'b0;
    end else begin
      cycle <= cycle + 1;
      bank_rsp_valid <= bank_req_valid & bank_req_ready;
      for (rsp_bank_i = 0; rsp_bank_i < BANKS; rsp_bank_i = rsp_bank_i + 1) begin
        if (bank_req_valid[rsp_bank_i] && bank_req_ready[rsp_bank_i]) begin
          group_i = bank_req_group[rsp_bank_i*3 +: 3];
          round_i = bank_req_round[rsp_bank_i*3 +: 3];
          slot_i = bank_req_word_slot[rsp_bank_i*7 +: 7];
          bank_rsp_buffer[rsp_bank_i] <= bank_req_buffer[rsp_bank_i];
          bank_rsp_group[rsp_bank_i*3 +: 3] <=
            (malformed_case && !malformed_sent) ? 3'(group_i + 1) : 3'(group_i);
          bank_rsp_round[rsp_bank_i*3 +: 3] <= 3'(round_i);
          bank_rsp_word_slot[rsp_bank_i*7 +: 7] <= 7'(slot_i);
          bank_rsp_data[rsp_bank_i*1024 +: 1024] <= expected_word(group_i, slot_i);
          if (malformed_case && !malformed_sent)
            malformed_sent <= 1'b1;
        end
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n) begin
      for (check_bank_i = 0; check_bank_i < BANKS; check_bank_i = check_bank_i + 1) begin
        if (bank_req_valid[check_bank_i] && bank_req_ready[check_bank_i]) begin
          group_i = bank_req_group[check_bank_i*3 +: 3];
          round_i = bank_req_round[check_bank_i*3 +: 3];
          slot_i = bank_req_word_slot[check_bank_i*7 +: 7];
          linear_i = group_i*ROUNDS + round_i;
          addr_i = bank_req_word_addr[check_bank_i*ADDR_W +: ADDR_W];
          if (slot_i < round_i*BANKS || slot_i >= WORDS ||
              slot_i >= (round_i+1)*BANKS)
            $fatal(1, "request slot outside round g=%0d r=%0d slot=%0d",
                   group_i, round_i, slot_i);
          if (addr_i != BASE_WORD + slot_i*GROUPS + group_i)
            $fatal(1, "request address mismatch bank=%0d g=%0d r=%0d slot=%0d addr=%0d",
                   check_bank_i, group_i, round_i, slot_i, addr_i);
          if ((addr_i % BANKS) != check_bank_i)
            $fatal(1, "request routed to wrong bank");
          if (request_seen[group_i][slot_i])
            $fatal(1, "duplicate request g=%0d slot=%0d", group_i, slot_i);
          request_seen[group_i][slot_i] <= 1'b1;
          request_count_by_round[linear_i] = request_count_by_round[linear_i] + 1;
          if (first_request_cycle[linear_i] < 0)
            first_request_cycle[linear_i] <= cycle;
        end
      end

      if (compute_valid && compute_ready) begin
        if (compute_group != expected_group || compute_round != expected_round ||
            compute_dimension != expected_dimension)
          $fatal(1, "compute order mismatch got g=%0d r=%0d d=%0d expected g=%0d r=%0d d=%0d",
                 compute_group, compute_round, compute_dimension,
                 expected_group, expected_round, expected_dimension);
        if (compute_last != (expected_dimension == DIMS-1))
          $fatal(1, "compute_last mismatch");
        valid_words_i = (expected_round == ROUNDS-1) ? 9 : BANKS;
        for (local_i = 0; local_i < BANKS; local_i = local_i + 1) begin
          if (compute_word_valid[local_i] != (local_i < valid_words_i))
            $fatal(1, "compute valid mask mismatch r=%0d local=%0d",
                   expected_round, local_i);
          if (local_i < valid_words_i) begin
            slot_i = expected_round*BANKS + local_i;
            if (compute_k_beats[local_i*64 +: 64] !==
                expected_lane(expected_group, slot_i, expected_dimension))
              $fatal(1, "compute data mismatch g=%0d r=%0d d=%0d local=%0d got=%h expected=%h local0_bank=%0d bank_lanes=%h",
                     expected_group, expected_round, expected_dimension, local_i,
                     compute_k_beats[local_i*64 +: 64],
                     expected_lane(expected_group, slot_i, expected_dimension),
                     dut.gen_compute[0].compute_storage_bank,
                     dut.selected_bank_lanes);
          end else if (compute_k_beats[local_i*64 +: 64] !== 64'd0) begin
            $fatal(1, "invalid compute lane was not zero");
          end
        end

        linear_i = expected_group*ROUNDS + expected_round;
        if (expected_dimension == 0)
          compute_start_cycle[linear_i] <= cycle;
        if (last_compute_cycle >= 0 && cycle-last_compute_cycle > max_compute_interval)
          max_compute_interval <= cycle-last_compute_cycle;
        last_compute_cycle <= cycle;
        compute_count <= compute_count + 1;
        if (expected_dimension == DIMS-1) begin
          compute_end_cycle[linear_i] <= cycle;
          expected_dimension <= 0;
          if (expected_round == ROUNDS-1) begin
            expected_round <= 0;
            expected_group <= expected_group + 1;
          end else begin
            expected_round <= expected_round + 1;
          end
        end else begin
          expected_dimension <= expected_dimension + 1;
        end
      end

      if (malformed_case && protocol_error) begin
        $display("PASS k_round malformed_response requests=%0d responses=%0d",
                 bank_request_count, bank_response_count);
        $finish;
      end

      if (done) begin
        if (protocol_error)
          $fatal(1, "protocol_error asserted in valid run");
        if (bank_request_count != GROUPS*WORDS ||
            bank_response_count != GROUPS*WORDS ||
            compute_beat_count != GROUPS*ROUNDS*DIMS ||
            compute_count != GROUPS*ROUNDS*DIMS)
          $fatal(1, "counter mismatch req=%0d rsp=%0d compute=%0d observed=%0d",
                 bank_request_count, bank_response_count,
                 compute_beat_count, compute_count);
        for (init_round_i = 0; init_round_i < GROUPS*ROUNDS;
             init_round_i = init_round_i + 1) begin
          valid_words_i = ((init_round_i % ROUNDS) == ROUNDS-1) ? 9 : BANKS;
          if (request_count_by_round[init_round_i] != valid_words_i)
            $fatal(1, "round request count mismatch linear=%0d count=%0d",
                   init_round_i, request_count_by_round[init_round_i]);
          $display("TRACE round=%0d first_req=%0d compute_start=%0d compute_end=%0d",
                   init_round_i, first_request_cycle[init_round_i],
                   compute_start_cycle[init_round_i], compute_end_cycle[init_round_i]);
        end
        if (!backpressure_case && max_compute_interval != 1)
          $fatal(1, "round buffering did not sustain one compute beat/cycle interval=%0d",
                 max_compute_interval);
        if (backpressure_case &&
            (bank_request_stall_count == 0 || compute_output_stall_count == 0))
          $fatal(1, "backpressure counters were not exercised");
        $display("PASS k_round backpressure=%0d requests=%0d responses=%0d compute=%0d max_compute_interval=%0d request_stalls=%0d compute_stalls=%0d wait=%0d",
                 backpressure_case, bank_request_count, bank_response_count,
                 compute_beat_count, max_compute_interval,
                 bank_request_stall_count, compute_output_stall_count,
                 compute_wait_for_window_count);
        $finish;
      end

      if (cycle > 10000)
        $fatal(1, "timeout");
    end
  end

  initial begin
    backpressure_case = $test$plusargs("BACKPRESSURE");
    malformed_case = $test$plusargs("MALFORMED");
    for (init_group_i = 0; init_group_i < GROUPS; init_group_i = init_group_i + 1)
      for (init_slot_i = 0; init_slot_i < WORDS; init_slot_i = init_slot_i + 1)
        request_seen[init_group_i][init_slot_i] = 1'b0;
    for (init_round_i = 0; init_round_i < GROUPS*ROUNDS;
         init_round_i = init_round_i + 1) begin
      request_count_by_round[init_round_i] = 0;
      first_request_cycle[init_round_i] = -1;
      compute_start_cycle[init_round_i] = -1;
      compute_end_cycle[init_round_i] = -1;
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
