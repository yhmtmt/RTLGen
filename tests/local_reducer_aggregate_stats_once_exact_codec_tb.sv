`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_codec_tb;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer VALUE_W = 328;
  localparam integer GROUP_BITS = 42504;
  localparam integer GROUP_FLITS = 167;
  localparam integer GROUP_BEATS = 128;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg [31:0] stall_state = 32'h9e37_79b9;

  reg normal_ctx_valid = 1'b0;
  wire normal_enc_ctx_ready;
  wire normal_dec_ctx_ready;
  reg [15:0] normal_command = 16'b0;
  reg [4:0] normal_head_base = 5'b0;
  reg normal_beat_valid = 1'b0;
  wire normal_beat_ready;
  reg [BEAT_W-1:0] normal_beat_data = {BEAT_W{1'b0}};
  wire normal_enc_flit_valid;
  wire normal_enc_flit_ready;
  wire [FLIT_W-1:0] normal_enc_flit_data;
  wire normal_enc_flit_group_last;
  wire normal_encoder_error;
  wire normal_dec_flit_valid;
  wire normal_dec_flit_ready;
  wire [FLIT_W-1:0] normal_dec_flit_data;
  wire normal_dec_flit_group_last;
  wire normal_dec_beat_valid;
  wire normal_dec_beat_ready;
  wire [BEAT_W-1:0] normal_dec_beat_data;
  wire normal_decoder_error;

  reg bad_ctx_valid = 1'b0;
  wire bad_ctx_ready;
  reg [15:0] bad_command = 16'b0;
  reg [4:0] bad_head_base = 5'b0;
  reg bad_flit_valid = 1'b0;
  wire bad_flit_ready;
  reg [FLIT_W-1:0] bad_flit_data = {FLIT_W{1'b0}};
  reg bad_flit_group_last = 1'b0;
  wire bad_protocol_error;

  reg [BEAT_W-1:0] expected_beats [0:GROUP_BEATS-1];
  reg [GROUP_BITS-1:0] expected_stream;
  integer normal_group_flit_count = 0;
  integer normal_driver_input_count = 0;
  integer normal_output_in_group = 0;
  integer normal_groups_completed = 0;
  integer valid_input_count_last = 0;
  integer overlap_count = 0;
  reg normal_monitor_enable = 1'b0;
  reg flit_accept_q = 1'b0;
  reg output_accept_q = 1'b0;
  reg overlap_accept_q = 1'b0;
  reg [FLIT_W-1:0] accepted_flit_data_q = {FLIT_W{1'b0}};
  reg accepted_flit_last_q = 1'b0;
  reg [BEAT_W-1:0] accepted_output_data_q = {BEAT_W{1'b0}};
  reg enc_hold_valid = 1'b0;
  reg [FLIT_W-1:0] enc_hold_data = {FLIT_W{1'b0}};
  reg enc_hold_last = 1'b0;
  reg dec_hold_valid = 1'b0;
  reg [BEAT_W-1:0] dec_hold_data = {BEAT_W{1'b0}};

  assign normal_enc_flit_ready = normal_dec_flit_ready && stall_state[0];
  assign normal_dec_flit_valid = normal_enc_flit_valid && stall_state[0];
  assign normal_dec_flit_data = normal_enc_flit_data;
  assign normal_dec_flit_group_last = normal_enc_flit_group_last;
  assign normal_dec_beat_ready = stall_state[1];
  local_reducer_aggregate_stats_once_exact_encoder encoder_dut (
    .clk(clk),
    .rst_n(rst_n),
    .group_ctx_valid(normal_ctx_valid),
    .group_ctx_ready(normal_enc_ctx_ready),
    .group_command_id(normal_command),
    .group_head_base(normal_head_base),
    .beat_valid(normal_beat_valid),
    .beat_ready(normal_beat_ready),
    .beat_data(normal_beat_data),
    .flit_valid(normal_enc_flit_valid),
    .flit_ready(normal_enc_flit_ready),
    .flit_data(normal_enc_flit_data),
    .flit_group_last(normal_enc_flit_group_last),
    .protocol_error(normal_encoder_error)
  );

  local_reducer_aggregate_stats_once_exact_decoder decoder_dut (
    .clk(clk),
    .rst_n(rst_n),
    .group_ctx_valid(normal_ctx_valid),
    .group_ctx_ready(normal_dec_ctx_ready),
    .group_command_id(normal_command),
    .group_head_base(normal_head_base),
    .flit_valid(normal_dec_flit_valid),
    .flit_ready(normal_dec_flit_ready),
    .flit_data(normal_dec_flit_data),
    .flit_group_last(normal_dec_flit_group_last),
    .beat_valid(normal_dec_beat_valid),
    .beat_ready(normal_dec_beat_ready),
    .beat_data(normal_dec_beat_data),
    .protocol_error(normal_decoder_error)
  );

  wire bad_decoder_beat_valid;
  local_reducer_aggregate_stats_once_exact_decoder bad_decoder_dut (
    .clk(clk),
    .rst_n(rst_n),
    .group_ctx_valid(bad_ctx_valid),
    .group_ctx_ready(bad_ctx_ready),
    .group_command_id(bad_command),
    .group_head_base(bad_head_base),
    .flit_valid(bad_flit_valid),
    .flit_ready(bad_flit_ready),
    .flit_data(bad_flit_data),
    .flit_group_last(bad_flit_group_last),
    .beat_valid(bad_decoder_beat_valid),
    .beat_ready(1'b1),
    .beat_data(),
    .protocol_error(bad_protocol_error)
  );

  always #5 clk = ~clk;

  function automatic [31:0] next_stall_state;
    input [31:0] state;
    begin
      next_stall_state = {state[30:0], state[31] ^ state[21] ^ state[1] ^ state[0]};
    end
  endfunction

  function automatic [BEAT_W-1:0] make_beat;
    input integer index;
    input integer command_id;
    input integer head_base;
    input integer seed;
    reg [BEAT_W-1:0] value;
    integer head;
    integer slice;
    integer lane;
    begin
      value = {BEAT_W{1'b0}};
      head = index / 16;
      slice = index % 16;
      value[15:0] = command_id[15:0];
      value[20:16] = head_base + head;
      value[52:21] = 32'h1200_0000 + seed * 32'h101 + head * 32'h31;
      value[85:53] = 33'h1 + seed * 33'h1001 + head * 33'h71;
      value[89:86] = slice[3:0];
      value[90] = (slice == 15);
      for (lane = 0; lane < 8; lane = lane + 1)
        value[91 + lane * 41 +: 41] =
          41'h10000 + seed * 41'h101 + index * 41'h13 + lane * 41'h7;
      make_beat = value;
    end
  endfunction

  function automatic [FLIT_W-1:0] expected_flit;
    input integer flit_index;
    reg [FLIT_W-1:0] result;
    begin
      result = {FLIT_W{1'b0}};
      if (flit_index < 166)
        result = expected_stream[flit_index * FLIT_W +: FLIT_W];
      else
        result[7:0] = expected_stream[166 * FLIT_W +: 8];
      expected_flit = result;
    end
  endfunction

  task automatic build_expected_stream;
    integer index;
    integer bit_position;
    begin
      expected_stream = {GROUP_BITS{1'b0}};
      bit_position = 0;
      for (index = 0; index < GROUP_BEATS; index = index + 1) begin
        if ((index % 16) == 0) begin
          expected_stream[bit_position +: 32] = expected_beats[index][52:21];
          bit_position = bit_position + 32;
          expected_stream[bit_position +: 33] = expected_beats[index][85:53];
          bit_position = bit_position + 33;
        end
        expected_stream[bit_position +: VALUE_W] = expected_beats[index][BEAT_W-1:91];
        bit_position = bit_position + VALUE_W;
      end
      if (bit_position != GROUP_BITS)
        $fatal(1, "reference stream length mismatch: %0d", bit_position);
    end
  endtask

  task automatic apply_reset;
    begin
      rst_n = 1'b0;
      normal_ctx_valid = 1'b0;
      normal_beat_valid = 1'b0;
      normal_beat_data = {BEAT_W{1'b0}};
      bad_ctx_valid = 1'b0;
      bad_flit_valid = 1'b0;
      bad_flit_data = {FLIT_W{1'b0}};
      bad_flit_group_last = 1'b0;
      stall_state = 32'h9e37_79b9;
      enc_hold_valid = 1'b0;
      dec_hold_valid = 1'b0;
      repeat (3) @(posedge clk);
      rst_n = 1'b1;
      @(posedge clk);
    end
  endtask

  task automatic send_context;
    input integer command_id;
    input integer head_base;
    begin
      @(negedge clk);
      normal_command = command_id[15:0];
      normal_head_base = head_base[4:0];
      normal_ctx_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (normal_ctx_valid && normal_enc_ctx_ready && normal_dec_ctx_ready)
          break;
      end
      @(negedge clk);
      normal_ctx_valid = 1'b0;
    end
  endtask

  task automatic send_normal_beat;
    input [BEAT_W-1:0] value;
    begin
      @(negedge clk);
      normal_beat_data = value;
      normal_beat_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (normal_beat_valid && normal_beat_ready) begin
          normal_driver_input_count = normal_driver_input_count + 1;
          break;
        end
      end
      @(negedge clk);
      normal_beat_valid = 1'b0;
      normal_beat_data = {BEAT_W{1'b0}};
    end
  endtask

  task automatic send_normal_group;
    input integer command_id;
    input integer head_base;
    input integer seed;
    integer index;
    integer timeout;
    begin
      for (index = 0; index < GROUP_BEATS; index = index + 1)
        expected_beats[index] = make_beat(index, command_id, head_base, seed);
      build_expected_stream();
      normal_group_flit_count = 0;
      normal_driver_input_count = 0;
      normal_output_in_group = 0;
      normal_monitor_enable = 1'b1;
      send_context(command_id, head_base);
      for (index = 0; index < GROUP_BEATS; index = index + 1) begin
        send_normal_beat(expected_beats[index]);
      end
      timeout = 0;
      while ((normal_group_flit_count != GROUP_FLITS) ||
             (normal_output_in_group != GROUP_BEATS)) begin
        @(posedge clk);
        timeout = timeout + 1;
        if (timeout > 200000)
          $fatal(1, "normal group timed out flits=%0d beats=%0d",
            normal_group_flit_count, normal_output_in_group);
      end
      normal_monitor_enable = 1'b0;
      if (normal_driver_input_count != GROUP_BEATS)
        $fatal(1, "valid group accepted %0d input beats", normal_driver_input_count);
      valid_input_count_last = normal_driver_input_count;
      repeat (3) @(posedge clk);
      if (decoder_dut.active_q !== 1'b0 ||
          decoder_dut.reservoir_count_q !== 0)
        $fatal(1, "decoder did not close with an empty reservoir");
      if (encoder_dut.active_q !== 1'b0)
        $fatal(1, "encoder did not close after final group flit");
      if (normal_encoder_error || normal_decoder_error)
        $fatal(1, "valid group raised protocol error enc=%b dec=%b",
          normal_encoder_error, normal_decoder_error);
      normal_monitor_enable = 1'b0;
      normal_groups_completed = normal_groups_completed + 1;
    end
  endtask

  task automatic send_bad_context;
    input integer command_id;
    input integer head_base;
    begin
      @(negedge clk);
      bad_command = command_id[15:0];
      bad_head_base = head_base[4:0];
      bad_ctx_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (bad_ctx_valid && bad_ctx_ready)
          break;
      end
      @(negedge clk);
      bad_ctx_valid = 1'b0;
    end
  endtask

  task automatic send_bad_flit;
    input [FLIT_W-1:0] data;
    input last;
    begin
      @(negedge clk);
      bad_flit_data = data;
      bad_flit_group_last = last;
      bad_flit_valid = 1'b1;
      while (1) begin
        @(posedge clk);
        if (bad_flit_valid && bad_flit_ready)
          break;
      end
      @(negedge clk);
      bad_flit_valid = 1'b0;
      bad_flit_data = {FLIT_W{1'b0}};
      bad_flit_group_last = 1'b0;
    end
  endtask

  task automatic check_early_group_last;
    begin
      apply_reset();
      send_bad_context(16'h55aa, 0);
      send_bad_flit({FLIT_W{1'b0}}, 1'b1);
      repeat (3) @(posedge clk);
      if (!bad_protocol_error)
        $fatal(1, "early group-last was not rejected");
      if (bad_decoder_dut.input_done_q !== 1'b0 || bad_ctx_ready !== 1'b0)
        $fatal(1, "early group-last forced a clean decoder close");
    end
  endtask

  task automatic check_invalid_context;
    begin
      apply_reset();
      send_bad_context(16'h55ae, 1);
      repeat (2) @(posedge clk);
      if (!bad_protocol_error)
        $fatal(1, "invalid head-base context was not rejected");
    end
  endtask

  task automatic check_reset_mid_group;
    reg [BEAT_W-1:0] partial_beat;
    begin
      apply_reset();
      normal_monitor_enable = 1'b0;
      send_context(16'h55af, 0);
      partial_beat = make_beat(0, 16'h55af, 0, 19);
      send_normal_beat(partial_beat);
      repeat (2) @(posedge clk);
      if (encoder_dut.active_q !== 1'b1 || decoder_dut.active_q !== 1'b1)
        $fatal(1, "mid-group reset setup did not activate both codecs");
      apply_reset();
      if (encoder_dut.active_q !== 1'b0 || decoder_dut.active_q !== 1'b0 ||
          normal_enc_ctx_ready !== 1'b1 || normal_dec_ctx_ready !== 1'b1)
        $fatal(1, "reset did not discard partial group state");
    end
  endtask

  task automatic check_late_group_last;
    integer index;
    reg [FLIT_W-1:0] data;
    begin
      apply_reset();
      send_bad_context(16'h55ab, 8);
      for (index = 0; index < GROUP_FLITS; index = index + 1) begin
        data = {FLIT_W{1'b0}};
        send_bad_flit(data, 1'b0);
      end
      if (!bad_protocol_error)
        $fatal(1, "missing terminal group-last was not rejected");
    end
  endtask

  task automatic check_nonzero_padding;
    integer index;
    reg [FLIT_W-1:0] data;
    begin
      apply_reset();
      send_bad_context(16'h55ac, 16);
      for (index = 0; index < GROUP_FLITS; index = index + 1) begin
        data = {FLIT_W{1'b0}};
        if (index == GROUP_FLITS - 1)
          data[8] = 1'b1;
        send_bad_flit(data, index == GROUP_FLITS - 1);
      end
      if (!bad_protocol_error)
        $fatal(1, "nonzero final padding was not rejected");
    end
  endtask

  task automatic check_encoder_order;
    reg [BEAT_W-1:0] malformed;
    begin
      apply_reset();
      normal_monitor_enable = 1'b0;
      send_context(16'h55ad, 24);
      malformed = make_beat(0, 16'h55ad, 24, 7);
      malformed[89:86] = 4'd1;
      normal_driver_input_count = 0;
      send_normal_beat(malformed);
      if (normal_driver_input_count != 1)
        $fatal(1, "malformed order driver accepted %0d input beats",
          normal_driver_input_count);
      repeat (3) @(posedge clk);
      if (!normal_encoder_error)
        $fatal(1, "encoder order violation was not sticky");
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      stall_state <= 32'h9e37_79b9;
    end else begin
      stall_state <= next_stall_state(stall_state);
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      enc_hold_valid = 1'b0;
      dec_hold_valid = 1'b0;
    end else begin
      if (enc_hold_valid && !normal_enc_flit_ready &&
          (normal_enc_flit_data !== enc_hold_data ||
           normal_enc_flit_group_last !== enc_hold_last))
        $fatal(1, "encoder flit changed while stalled");
      if (dec_hold_valid && !normal_dec_beat_ready &&
          normal_dec_beat_data !== dec_hold_data)
        $fatal(1, "decoder beat changed while stalled");
      enc_hold_valid = normal_enc_flit_valid && !normal_enc_flit_ready;
      if (enc_hold_valid) begin
        enc_hold_data = normal_enc_flit_data;
        enc_hold_last = normal_enc_flit_group_last;
      end
      dec_hold_valid = normal_dec_beat_valid && !normal_dec_beat_ready;
      if (dec_hold_valid)
        dec_hold_data = normal_dec_beat_data;
    end
  end

  // Capture handshake events before either task changes its driven signals.
  // Validation and counters are committed at the following negedge, which
  // makes group completion independent of active-region scheduling order.
  always @(posedge clk) begin
    if (!rst_n) begin
      flit_accept_q <= 1'b0;
      output_accept_q <= 1'b0;
      overlap_accept_q <= 1'b0;
    end else begin
      flit_accept_q <= normal_monitor_enable &&
        normal_enc_flit_valid && normal_enc_flit_ready;
      output_accept_q <= normal_monitor_enable &&
        normal_dec_beat_valid && normal_dec_beat_ready;
      overlap_accept_q <= normal_monitor_enable &&
        decoder_dut.parse_fire && decoder_dut.flit_fire;
      if (normal_monitor_enable && normal_enc_flit_valid && normal_enc_flit_ready) begin
        accepted_flit_data_q <= normal_enc_flit_data;
        accepted_flit_last_q <= normal_enc_flit_group_last;
      end
      if (normal_monitor_enable && normal_dec_beat_valid && normal_dec_beat_ready)
        accepted_output_data_q <= normal_dec_beat_data;
    end
  end

  always @(negedge clk) begin
    if (!rst_n) begin
      normal_group_flit_count = 0;
      normal_output_in_group = 0;
    end else begin
      if (flit_accept_q) begin
        if (normal_group_flit_count >= GROUP_FLITS)
          $fatal(1, "encoder emitted too many flits");
        if (accepted_flit_data_q !== expected_flit(normal_group_flit_count))
          $fatal(1, "independent stream mismatch at flit %0d",
            normal_group_flit_count);
        if (accepted_flit_last_q !==
            (normal_group_flit_count == GROUP_FLITS - 1))
          $fatal(1, "group-last mismatch at flit %0d", normal_group_flit_count);
        normal_group_flit_count = normal_group_flit_count + 1;
      end
      if (output_accept_q) begin
        if (normal_output_in_group >= GROUP_BEATS)
          $fatal(1, "decoder emitted too many beats");
        if (accepted_output_data_q !== expected_beats[normal_output_in_group])
          $fatal(1, "decoded beat mismatch at beat %0d", normal_output_in_group);
        normal_output_in_group = normal_output_in_group + 1;
      end
      if (overlap_accept_q)
        overlap_count = overlap_count + 1;
    end
  end

  initial begin
    normal_group_flit_count = 0;
    normal_output_in_group = 0;
    normal_groups_completed = 0;
    overlap_count = 0;
    apply_reset();
    send_normal_group(16'h1234, 0, 3);
    send_normal_group(16'h2345, 24, 11);
    if (normal_groups_completed != 2)
      $fatal(1, "expected two valid groups");
    if (overlap_count < 8)
      $fatal(1, "decoder did not demonstrate sustained parse/receive overlap: %0d",
        overlap_count);
    check_reset_mid_group();
    check_invalid_context();
    check_early_group_last();
    check_late_group_last();
    check_nonzero_padding();
    check_encoder_order();
    $display("PASS local_reducer_aggregate_stats_once_exact_codec groups=%0d input_beats_per_group=%0d flits_per_group=%0d beats_per_group=%0d overlap=%0d", normal_groups_completed, valid_input_count_last, GROUP_FLITS, GROUP_BEATS, overlap_count);
    $finish(0);
  end
endmodule
