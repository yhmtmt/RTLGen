`timescale 1ns/1ps

module local_reducer_aggregate_aligned_exact_codec_tb;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer SECOND_PAYLOAD_W = BEAT_W - FLIT_W;
  localparam integer SECOND_PAD_W = FLIT_W - SECOND_PAYLOAD_W;
  localparam integer ENCODER_VECTOR_COUNT = 12;
  localparam integer CADENCE_VECTOR_COUNT = 6;
  localparam integer LOOPBACK_VECTOR_COUNT = 10;
  localparam integer MODE_IDLE = 0;
  localparam integer MODE_ENCODER = 1;
  localparam integer MODE_LOOPBACK = 2;
  localparam integer MODE_MANUAL_DECODER = 3;
  localparam integer MODE_CADENCE = 4;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle_count = 0;

  reg enc_beat_valid = 1'b0;
  wire enc_beat_ready;
  reg [BEAT_W-1:0] enc_beat_data = {BEAT_W{1'b0}};
  wire enc_flit_valid;
  wire enc_flit_ready;
  wire [FLIT_W-1:0] enc_flit_data;
  wire enc_flit_phase;
  wire enc_flit_beat_last;

  reg dec_flit_valid = 1'b0;
  wire dec_flit_ready;
  reg [FLIT_W-1:0] dec_flit_data = {FLIT_W{1'b0}};
  reg dec_flit_phase = 1'b0;
  reg dec_flit_beat_last = 1'b0;
  wire dec_beat_valid;
  wire dec_beat_ready;
  wire [BEAT_W-1:0] dec_beat_data;
  wire dec_partial_valid;
  wire dec_protocol_error;

  reg manual_flit_valid = 1'b0;
  reg [FLIT_W-1:0] manual_flit_data = {FLIT_W{1'b0}};
  reg manual_flit_phase = 1'b0;
  reg manual_flit_beat_last = 1'b0;
  reg [2:0] mode = MODE_IDLE[2:0];

  reg [31:0] stall_state = 32'h1badf00d;
  reg [BEAT_W-1:0] encoder_vectors [0:ENCODER_VECTOR_COUNT-1];
  reg [BEAT_W-1:0] cadence_vectors [0:CADENCE_VECTOR_COUNT-1];
  reg [BEAT_W-1:0] loopback_vectors [0:LOOPBACK_VECTOR_COUNT-1];
  reg manual_dec_ready = 1'b0;

  integer encoder_flit_count = 0;
  integer cadence_encoder_beat_count = 0;
  integer cadence_flit_count = 0;
  integer cadence_decoder_beat_count = 0;
  integer loopback_beat_count = 0;
  integer encoder_hold_checks = 0;
  integer decoder_hold_checks = 0;
  integer cadence_encoder_beat_cycles [0:CADENCE_VECTOR_COUNT-1];
  integer cadence_flit_cycles [0:(CADENCE_VECTOR_COUNT*2)-1];
  integer cadence_decoder_beat_cycles [0:CADENCE_VECTOR_COUNT-1];

  reg held_encoder_valid = 1'b0;
  reg [FLIT_W+1:0] held_encoder_flit = {(FLIT_W+2){1'b0}};
  reg held_decoder_valid = 1'b0;
  reg [BEAT_W-1:0] held_decoder_beat = {BEAT_W{1'b0}};

  assign enc_flit_ready =
    (mode == MODE_ENCODER) ? stall_state[0] :
    ((mode == MODE_LOOPBACK || mode == MODE_CADENCE) ? dec_flit_ready : 1'b0);
  assign dec_beat_ready =
    (mode == MODE_LOOPBACK) ? stall_state[1] :
    ((mode == MODE_CADENCE) ? 1'b1 :
     ((mode == MODE_MANUAL_DECODER) ? manual_dec_ready : 1'b0));

  local_reducer_aggregate_aligned_exact_encoder #(
    .BEAT_W(BEAT_W),
    .FLIT_W(FLIT_W)
  ) encoder_dut (
    .clk(clk),
    .rst_n(rst_n),
    .beat_valid(enc_beat_valid),
    .beat_ready(enc_beat_ready),
    .beat_data(enc_beat_data),
    .flit_valid(enc_flit_valid),
    .flit_ready(enc_flit_ready),
    .flit_data(enc_flit_data),
    .flit_phase(enc_flit_phase),
    .flit_beat_last(enc_flit_beat_last)
  );

  local_reducer_aggregate_aligned_exact_decoder #(
    .BEAT_W(BEAT_W),
    .FLIT_W(FLIT_W)
  ) decoder_dut (
    .clk(clk),
    .rst_n(rst_n),
    .flit_valid(dec_flit_valid),
    .flit_ready(dec_flit_ready),
    .flit_data(dec_flit_data),
    .flit_phase(dec_flit_phase),
    .flit_beat_last(dec_flit_beat_last),
    .beat_valid(dec_beat_valid),
    .beat_ready(dec_beat_ready),
    .beat_data(dec_beat_data),
    .partial_valid(dec_partial_valid),
    .protocol_error(dec_protocol_error)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n)
      cycle_count <= 0;
    else
      cycle_count <= cycle_count + 1;
  end

  function automatic [31:0] next_state;
    input [31:0] state;
    begin
      next_state = {state[30:0], state[31] ^ state[21] ^ state[1] ^ state[0]};
    end
  endfunction

  function automatic [BEAT_W-1:0] make_beat;
    input integer index;
    reg [447:0] tmp;
    reg [31:0] state;
    integer chunk;
    begin
      case (index)
        0: make_beat = {BEAT_W{1'b0}};
        1: make_beat = {BEAT_W{1'b1}};
        2: begin
          make_beat = {BEAT_W{1'b0}};
          make_beat[0] = 1'b1;
          make_beat[255] = 1'b1;
          make_beat[256] = 1'b1;
          make_beat[418] = 1'b1;
        end
        3: begin
          for (chunk = 0; chunk < BEAT_W; chunk = chunk + 1)
            make_beat[chunk] = chunk[0];
        end
        default: begin
          tmp = {448{1'b0}};
          state = 32'h6d2b79f5 ^ (index * 32'h9e3779b9);
          for (chunk = 0; chunk < 14; chunk = chunk + 1) begin
            state = state * 32'h45d9f3b + 32'h27100001;
            tmp[(chunk * 32) +: 32] = state ^ {state[15:0], state[31:16]};
          end
          make_beat = tmp[BEAT_W-1:0];
        end
      endcase
    end
  endfunction

  function automatic [FLIT_W-1:0] expected_flit;
    input [BEAT_W-1:0] beat;
    input integer phase;
    begin
      if (phase == 0)
        expected_flit = beat[FLIT_W-1:0];
      else
        expected_flit = {{SECOND_PAD_W{1'b0}}, beat[BEAT_W-1:FLIT_W]};
    end
  endfunction

  task automatic apply_reset;
    integer hold_cycles;
    begin
      rst_n = 1'b0;
      enc_beat_valid = 1'b0;
      enc_beat_data = {BEAT_W{1'b0}};
      dec_flit_valid = 1'b0;
      dec_flit_data = {FLIT_W{1'b0}};
      dec_flit_phase = 1'b0;
      dec_flit_beat_last = 1'b0;
      manual_flit_valid = 1'b0;
      manual_flit_data = {FLIT_W{1'b0}};
      manual_flit_phase = 1'b0;
      manual_flit_beat_last = 1'b0;
      manual_dec_ready = 1'b0;
      held_encoder_valid = 1'b0;
      held_decoder_valid = 1'b0;
      stall_state = 32'h1badf00d;
      for (hold_cycles = 0; hold_cycles < 3; hold_cycles = hold_cycles + 1)
        @(posedge clk);
      rst_n = 1'b1;
      @(posedge clk);
    end
  endtask

  task automatic load_vectors;
    integer i;
    begin
      for (i = 0; i < ENCODER_VECTOR_COUNT; i = i + 1)
        encoder_vectors[i] = make_beat(i);
      for (i = 0; i < CADENCE_VECTOR_COUNT; i = i + 1)
        cadence_vectors[i] = make_beat(i + 64);
      for (i = 0; i < LOOPBACK_VECTOR_COUNT; i = i + 1)
        loopback_vectors[i] = make_beat(i + 32);
    end
  endtask

  task automatic send_encoder_beat;
    input [BEAT_W-1:0] beat;
    begin
      @(negedge clk);
      enc_beat_valid = 1'b1;
      enc_beat_data = beat;
      while (!enc_beat_ready)
        @(posedge clk);
      @(posedge clk);
      @(negedge clk);
      enc_beat_valid = 1'b0;
      enc_beat_data = {BEAT_W{1'b0}};
    end
  endtask

  task automatic send_manual_flit;
    input [FLIT_W-1:0] data;
    input phase;
    input last;
    begin
      @(negedge clk);
      manual_flit_valid = 1'b1;
      manual_flit_data = data;
      manual_flit_phase = phase;
      manual_flit_beat_last = last;
      while (!dec_flit_ready)
        @(posedge clk);
      @(posedge clk);
      @(negedge clk);
      manual_flit_valid = 1'b0;
      manual_flit_data = {FLIT_W{1'b0}};
      manual_flit_phase = 1'b0;
      manual_flit_beat_last = 1'b0;
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      stall_state <= 32'h1badf00d;
    end else begin
      stall_state <= next_state(stall_state);
    end
  end

  always @(*) begin
    if (mode == MODE_LOOPBACK || mode == MODE_CADENCE) begin
      dec_flit_valid = enc_flit_valid;
      dec_flit_data = enc_flit_data;
      dec_flit_phase = enc_flit_phase;
      dec_flit_beat_last = enc_flit_beat_last;
    end else if (mode == MODE_MANUAL_DECODER) begin
      dec_flit_valid = manual_flit_valid;
      dec_flit_data = manual_flit_data;
      dec_flit_phase = manual_flit_phase;
      dec_flit_beat_last = manual_flit_beat_last;
    end else begin
      dec_flit_valid = 1'b0;
      dec_flit_data = {FLIT_W{1'b0}};
      dec_flit_phase = 1'b0;
      dec_flit_beat_last = 1'b0;
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      held_encoder_valid <= 1'b0;
      held_encoder_flit <= {(FLIT_W+2){1'b0}};
      held_decoder_valid <= 1'b0;
      held_decoder_beat <= {BEAT_W{1'b0}};
    end else begin
      if (mode != MODE_MANUAL_DECODER && enc_flit_valid && !enc_flit_ready) begin
        if (held_encoder_valid &&
            held_encoder_flit !== {enc_flit_phase, enc_flit_beat_last, enc_flit_data})
          $fatal(1, "encoder output changed under backpressure");
        held_encoder_valid <= 1'b1;
        held_encoder_flit <= {enc_flit_phase, enc_flit_beat_last, enc_flit_data};
        encoder_hold_checks <= encoder_hold_checks + 1;
      end else begin
        held_encoder_valid <= 1'b0;
      end

      if (dec_beat_valid && !dec_beat_ready) begin
        if (held_decoder_valid && held_decoder_beat !== dec_beat_data)
          $fatal(1, "decoder beat changed under backpressure");
        held_decoder_valid <= 1'b1;
        held_decoder_beat <= dec_beat_data;
        decoder_hold_checks <= decoder_hold_checks + 1;
      end else begin
        held_decoder_valid <= 1'b0;
      end
    end
  end

  always @(posedge clk) begin
    integer beat_index;
    integer phase_index;
    if (rst_n && mode == MODE_ENCODER && enc_flit_valid && enc_flit_ready) begin
      beat_index = encoder_flit_count / 2;
      phase_index = encoder_flit_count % 2;
      if (beat_index >= ENCODER_VECTOR_COUNT)
        $fatal(1, "encoder emitted too many flits");
      if (enc_flit_phase !== phase_index[0])
        $fatal(1, "encoder phase mismatch for flit %0d", encoder_flit_count);
      if (enc_flit_beat_last !== phase_index[0])
        $fatal(1, "encoder last mismatch for flit %0d", encoder_flit_count);
      if (enc_flit_data !== expected_flit(encoder_vectors[beat_index], phase_index))
        $fatal(1, "encoder flit payload mismatch for beat %0d phase %0d", beat_index, phase_index);
      if (phase_index == 1 && enc_flit_data[FLIT_W-1:SECOND_PAYLOAD_W] !== {SECOND_PAD_W{1'b0}})
        $fatal(1, "encoder phase-1 padding was not zero");
      encoder_flit_count <= encoder_flit_count + 1;
    end
    if (rst_n && mode == MODE_CADENCE && enc_flit_valid && enc_flit_ready) begin
      cadence_flit_cycles[cadence_flit_count] = cycle_count;
      cadence_flit_count <= cadence_flit_count + 1;
    end
    if (rst_n && mode == MODE_CADENCE && enc_beat_valid && enc_beat_ready) begin
      cadence_encoder_beat_cycles[cadence_encoder_beat_count] = cycle_count;
      cadence_encoder_beat_count <= cadence_encoder_beat_count + 1;
    end
  end

  always @(posedge clk) begin
    if (rst_n && mode == MODE_CADENCE && dec_beat_valid && dec_beat_ready) begin
      if (cadence_decoder_beat_count >= CADENCE_VECTOR_COUNT)
        $fatal(1, "cadence decoder emitted too many beats");
      if (dec_beat_data !== cadence_vectors[cadence_decoder_beat_count])
        $fatal(1, "cadence decoder beat mismatch for beat %0d", cadence_decoder_beat_count);
      cadence_decoder_beat_cycles[cadence_decoder_beat_count] = cycle_count;
      cadence_decoder_beat_count <= cadence_decoder_beat_count + 1;
    end
    if (rst_n && mode == MODE_LOOPBACK && dec_beat_valid && dec_beat_ready) begin
      if (loopback_beat_count >= LOOPBACK_VECTOR_COUNT)
        $fatal(1, "decoder emitted too many beats");
      if (dec_beat_data !== loopback_vectors[loopback_beat_count])
        $fatal(1, "decoder beat mismatch for beat %0d", loopback_beat_count);
      loopback_beat_count <= loopback_beat_count + 1;
    end
  end

  initial begin
    load_vectors();

    mode = MODE_ENCODER[2:0];
    encoder_flit_count = 0;
    loopback_beat_count = 0;
    encoder_hold_checks = 0;
    decoder_hold_checks = 0;
    apply_reset();
    repeat (2) @(posedge clk);
    begin : encoder_phase
      integer i;
      for (i = 0; i < ENCODER_VECTOR_COUNT; i = i + 1)
        send_encoder_beat(encoder_vectors[i]);
    end
    wait (encoder_flit_count == (ENCODER_VECTOR_COUNT * 2));
    repeat (4) @(posedge clk);
    if (encoder_hold_checks == 0)
      $fatal(1, "encoder never experienced backpressure");

    mode = MODE_CADENCE[2:0];
    cadence_encoder_beat_count = 0;
    cadence_flit_count = 0;
    cadence_decoder_beat_count = 0;
    apply_reset();
    repeat (2) @(posedge clk);
    begin : cadence_phase
      integer c;
      for (c = 0; c < CADENCE_VECTOR_COUNT; c = c + 1)
        send_encoder_beat(cadence_vectors[c]);
    end
    wait (cadence_decoder_beat_count == CADENCE_VECTOR_COUNT);
    repeat (3) @(posedge clk);
    begin : cadence_checks
      integer k;
      if (cadence_encoder_beat_count != CADENCE_VECTOR_COUNT)
        $fatal(1, "encoder cadence accepted %0d beats instead of %0d", cadence_encoder_beat_count, CADENCE_VECTOR_COUNT);
      if (cadence_flit_count != (CADENCE_VECTOR_COUNT * 2))
        $fatal(1, "cadence emitted %0d flits instead of %0d", cadence_flit_count, CADENCE_VECTOR_COUNT * 2);
      for (k = 0; k < (CADENCE_VECTOR_COUNT * 2) - 1; k = k + 1)
        if (cadence_flit_cycles[k+1] != (cadence_flit_cycles[k] + 1))
          $fatal(1, "always-ready flit cadence bubbled between flits %0d and %0d", k, k + 1);
      for (k = 0; k < CADENCE_VECTOR_COUNT - 1; k = k + 1) begin
        if (cadence_encoder_beat_cycles[k+1] != cadence_flit_cycles[(2 * k) + 1])
          $fatal(1, "encoder did not accept beat %0d on prior phase-1 acceptance cycle", k + 1);
        if (cadence_flit_cycles[2 * (k + 1)] != cadence_decoder_beat_cycles[k])
          $fatal(1, "decoder did not accept next phase-0 flit on prior beat-drain cycle for beat %0d", k);
        if (cadence_decoder_beat_cycles[k+1] != (cadence_decoder_beat_cycles[k] + 2))
          $fatal(1, "decoder output cadence bubbled between beats %0d and %0d", k, k + 1);
      end
    end

    mode = MODE_LOOPBACK[2:0];
    loopback_beat_count = 0;
    apply_reset();
    repeat (2) @(posedge clk);
    begin : loopback_phase
      integer j;
      for (j = 0; j < LOOPBACK_VECTOR_COUNT; j = j + 1)
        send_encoder_beat(loopback_vectors[j]);
    end
    wait (loopback_beat_count == LOOPBACK_VECTOR_COUNT);
    repeat (4) @(posedge clk);
    if (dec_protocol_error)
      $fatal(1, "decoder protocol_error asserted during exact loopback");
    if (decoder_hold_checks == 0)
      $fatal(1, "decoder never experienced output backpressure");

    mode = MODE_MANUAL_DECODER[2:0];
    apply_reset();
    repeat (2) @(posedge clk);
    send_manual_flit(expected_flit(make_beat(80), 0), 1'b0, 1'b0);
    @(negedge clk);
    if (!dec_partial_valid)
      $fatal(1, "decoder did not retain first flit as partial state");
    if (dec_beat_valid)
      $fatal(1, "decoder emitted a beat after only one flit");

    rst_n = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;
    @(negedge clk);
    if (dec_partial_valid)
      $fatal(1, "reset did not clear decoder partial state");
    if (dec_protocol_error)
      $fatal(1, "reset did not clear decoder protocol_error");

    send_manual_flit(expected_flit(make_beat(80), 1), 1'b1, 1'b1);
    @(negedge clk);
    if (!dec_protocol_error)
      $fatal(1, "decoder failed to reject lone phase-1 flit after reset");
    if (dec_beat_valid)
      $fatal(1, "decoder emitted a beat from a half-beat sequence");

    apply_reset();
    mode = MODE_MANUAL_DECODER[2:0];
    repeat (2) @(posedge clk);
    manual_dec_ready = 1'b0;
    send_manual_flit(expected_flit(make_beat(81), 0), 1'b0, 1'b0);
    send_manual_flit(expected_flit(make_beat(81), 1), 1'b1, 1'b1);
    repeat (3) @(posedge clk);
    if (!dec_beat_valid)
      $fatal(1, "decoder did not produce a full beat after two valid flits");
    if (dec_beat_data !== make_beat(81))
      $fatal(1, "decoder reconstructed the wrong beat after manual framing");
    manual_dec_ready = 1'b1;
    @(posedge clk);
    @(negedge clk);
    if (dec_beat_valid)
      $fatal(1, "decoder beat did not drain after ready");

    $display(
      "PASS local_reducer_aggregate_aligned_exact_codec encoder_flits=%0d loopback_beats=%0d encoder_holds=%0d decoder_holds=%0d",
      encoder_flit_count,
      loopback_beat_count,
      encoder_hold_checks,
      decoder_hold_checks
    );
    $finish;
  end
endmodule
