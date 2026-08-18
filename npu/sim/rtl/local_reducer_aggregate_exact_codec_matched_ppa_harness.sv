`timescale 1ns/1ps

// Matched activity harness for the aligned and stats-once exact transports.
// The source, stalls, counters, and full-bit sink are intentionally shared so
// that a PPA comparison changes only the transport codec.
module local_reducer_aggregate_exact_codec_matched_ppa_harness #(
  parameter integer MODE_STATS_ONCE = 0,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,
  output wire [31:0] observed_data,
  output wire [COUNTER_W-1:0] accepted_beat_count,
  output wire [COUNTER_W-1:0] emitted_flit_count,
  output wire [COUNTER_W-1:0] decoded_beat_count,
  output wire [COUNTER_W-1:0] completed_group_count,
  output wire protocol_error
);
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer VALUE_W = 328;

  reg [COUNTER_W-1:0] cycle_count_q;
  reg [COUNTER_W-1:0] accepted_count_q;
  reg [COUNTER_W-1:0] emitted_count_q;
  reg [COUNTER_W-1:0] decoded_count_q;
  reg [COUNTER_W-1:0] completed_group_count_q;
  reg [15:0] group_id_q;
  reg [15:0] expected_group_id_q;
  reg [7:0] source_group_beat_q;
  reg [7:0] decoded_group_beat_q;
  reg group_open_q;
  reg [31:0] observed_q;
  reg mismatch_q;

  wire [15:0] group_command_id = group_id_q;
  wire [4:0] group_head_base = {3'b000, group_id_q[1:0], 3'b000};
  wire group_ctx_valid = !group_open_q;
  wire common_source_valid = group_open_q &&
    (source_group_beat_q < 8'd128) && (cycle_count_q[2:0] != 3'b111);
  wire common_flit_ready = (cycle_count_q[4:0] != 5'h03) &&
    (cycle_count_q[4:0] != 5'h11) && (cycle_count_q[4:0] != 5'h1c);
  wire common_decoded_ready = (cycle_count_q[5:2] != 4'hb) &&
    (cycle_count_q[5:2] != 4'he);

  wire [BEAT_W-1:0] source_beat = make_canonical_beat(
    group_id_q, source_group_beat_q);
  wire source_ready;
  wire encoder_flit_valid;
  wire encoder_flit_ready;
  wire [FLIT_W-1:0] encoder_flit_data;
  wire encoder_flit_phase;
  wire encoder_flit_beat_last;
  wire encoder_flit_group_last;
  wire decoder_flit_valid;
  wire decoder_flit_ready;
  wire [FLIT_W-1:0] decoder_flit_data;
  wire decoder_flit_phase;
  wire decoder_flit_beat_last;
  wire decoder_flit_group_last;
  wire decoded_valid;
  wire decoded_ready = common_decoded_ready;
  wire [BEAT_W-1:0] decoded_data;
  wire decoder_partial_valid;
  wire encoder_protocol_error;
  wire decoder_protocol_error;
  wire encoder_group_ctx_ready;
  wire decoder_group_ctx_ready;
  wire context_ready;
  wire context_fire = group_ctx_valid && context_ready;
  wire source_fire = common_source_valid && source_ready;
  wire flit_fire = encoder_flit_valid && encoder_flit_ready;
  wire decoded_fire = decoded_valid && decoded_ready;
  wire decoded_group_last = decoded_fire && (decoded_group_beat_q == 8'd127);
  wire [BEAT_W-1:0] expected_decoded_beat = make_canonical_beat(
    expected_group_id_q, decoded_group_beat_q);

  assign accepted_beat_count = accepted_count_q;
  assign emitted_flit_count = emitted_count_q;
  assign decoded_beat_count = decoded_count_q;
  assign completed_group_count = completed_group_count_q;
  assign observed_data = observed_q;
  // The exact decoded-beat comparison is part of the direct harness gate.
  // Keep the public interface limited to the generator integration contract.
  assign protocol_error = encoder_protocol_error | decoder_protocol_error |
    mismatch_q;

  function automatic [VALUE_W-1:0] canonical_value;
    input [15:0] group_id;
    input [7:0] beat_index;
    reg [31:0] state;
    integer lane;
    begin
      canonical_value = {VALUE_W{1'b0}};
      for (lane = 0; lane < 10; lane = lane + 1) begin
        state = 32'h6d2b79f5 ^ (group_id * 32'h9e3779b9) ^
          (beat_index * 32'h45d9f3b) ^ (lane * 32'h27d4eb2d);
        state = state ^ (state << 13);
        state = state ^ (state >> 17);
        state = state ^ (state << 5);
        canonical_value[(lane * 32) +: 32] = state;
      end
      state = 32'hb5297a4d ^ (group_id * 32'h7f4a7c15) ^
        (beat_index * 32'h94d049bb);
      state = state ^ (state << 13) ^ (state >> 11);
      canonical_value[320 +: 8] = state[7:0];
    end
  endfunction

  function automatic [BEAT_W-1:0] make_canonical_beat;
    input [15:0] group_id;
    input [7:0] beat_index;
    reg [4:0] head;
    reg [3:0] slice;
    reg [31:0] head_max;
    reg [32:0] head_sum;
    begin
      head = {3'b000, group_id[1:0], 3'b000} + (beat_index >> 4);
      slice = beat_index[3:0];
      head_max = 32'h1200_0000 ^ (group_id * 32'h0101_0101) ^
        ((beat_index >> 4) * 32'h0011_1111);
      head_sum = 33'h0_1a2b_3c4d ^ (group_id * 33'h0_0001_2345) ^
        ((beat_index >> 4) * 33'h0_0000_1111);
      make_canonical_beat = {BEAT_W{1'b0}};
      make_canonical_beat[15:0] = group_id;
      make_canonical_beat[20:16] = head;
      make_canonical_beat[52:21] = head_max;
      make_canonical_beat[85:53] = head_sum;
      make_canonical_beat[89:86] = slice;
      make_canonical_beat[90] = (slice == 4'd15);
      make_canonical_beat[BEAT_W-1:91] = canonical_value(group_id, beat_index);
    end
  endfunction

  function automatic [31:0] fold_all_bits;
    input [BEAT_W-1:0] value;
    integer bit_i;
    begin
      fold_all_bits = 32'b0;
      for (bit_i = 0; bit_i < BEAT_W; bit_i = bit_i + 1)
        fold_all_bits[bit_i % 32] = fold_all_bits[bit_i % 32] ^ value[bit_i];
    end
  endfunction

  generate
    if (MODE_STATS_ONCE == 0) begin : g_aligned
      assign context_ready = 1'b1;
      assign encoder_group_ctx_ready = 1'b1;
      assign decoder_group_ctx_ready = 1'b1;
      assign encoder_flit_ready = common_flit_ready && decoder_flit_ready;
      assign decoder_flit_valid = encoder_flit_valid && common_flit_ready;
      assign decoder_flit_data = encoder_flit_data;
      assign decoder_flit_phase = encoder_flit_phase;
      assign decoder_flit_beat_last = encoder_flit_beat_last;
      assign decoder_flit_group_last = 1'b0;

      (* keep_hierarchy = "yes" *)
      local_reducer_aggregate_aligned_exact_encoder u_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .beat_valid(common_source_valid),
        .beat_ready(source_ready),
        .beat_data(source_beat),
        .flit_valid(encoder_flit_valid),
        .flit_ready(encoder_flit_ready),
        .flit_data(encoder_flit_data),
        .flit_phase(encoder_flit_phase),
        .flit_beat_last(encoder_flit_beat_last)
      );

      (* keep_hierarchy = "yes" *)
      local_reducer_aggregate_aligned_exact_decoder u_decoder (
        .clk(clk),
        .rst_n(rst_n),
        .flit_valid(decoder_flit_valid),
        .flit_ready(decoder_flit_ready),
        .flit_data(decoder_flit_data),
        .flit_phase(decoder_flit_phase),
        .flit_beat_last(decoder_flit_beat_last),
        .beat_valid(decoded_valid),
        .beat_ready(decoded_ready),
        .beat_data(decoded_data),
        .partial_valid(decoder_partial_valid),
        .protocol_error(decoder_protocol_error)
      );
      assign encoder_protocol_error = 1'b0;
    end else begin : g_stats_once
      assign context_ready = encoder_group_ctx_ready && decoder_group_ctx_ready;
      assign encoder_flit_ready = common_flit_ready && decoder_flit_ready;
      assign decoder_flit_valid = encoder_flit_valid && common_flit_ready;
      assign decoder_flit_data = encoder_flit_data;
      assign decoder_flit_group_last = encoder_flit_group_last;
      assign decoder_flit_phase = 1'b0;
      assign decoder_flit_beat_last = 1'b0;

      (* keep_hierarchy = "yes" *)
      local_reducer_aggregate_stats_once_exact_encoder u_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid),
        .group_ctx_ready(encoder_group_ctx_ready),
        .group_command_id(group_command_id),
        .group_head_base(group_head_base),
        .beat_valid(common_source_valid),
        .beat_ready(source_ready),
        .beat_data(source_beat),
        .flit_valid(encoder_flit_valid),
        .flit_ready(encoder_flit_ready),
        .flit_data(encoder_flit_data),
        .flit_group_last(encoder_flit_group_last),
        .protocol_error(encoder_protocol_error)
      );

      (* keep_hierarchy = "yes" *)
      local_reducer_aggregate_stats_once_exact_decoder u_decoder (
        .clk(clk),
        .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid),
        .group_ctx_ready(decoder_group_ctx_ready),
        .group_command_id(group_command_id),
        .group_head_base(group_head_base),
        .flit_valid(decoder_flit_valid),
        .flit_ready(decoder_flit_ready),
        .flit_data(decoder_flit_data),
        .flit_group_last(decoder_flit_group_last),
        .beat_valid(decoded_valid),
        .beat_ready(decoded_ready),
        .beat_data(decoded_data),
        .protocol_error(decoder_protocol_error)
      );
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle_count_q <= {COUNTER_W{1'b0}};
      accepted_count_q <= {COUNTER_W{1'b0}};
      emitted_count_q <= {COUNTER_W{1'b0}};
      decoded_count_q <= {COUNTER_W{1'b0}};
      completed_group_count_q <= {COUNTER_W{1'b0}};
      group_id_q <= 16'b0;
      expected_group_id_q <= 16'b0;
      source_group_beat_q <= 8'b0;
      decoded_group_beat_q <= 8'b0;
      group_open_q <= 1'b0;
      observed_q <= 32'b0;
      mismatch_q <= 1'b0;
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;

      if (context_fire) begin
        group_open_q <= 1'b1;
        expected_group_id_q <= group_id_q;
        source_group_beat_q <= 8'b0;
        decoded_group_beat_q <= 8'b0;
      end

      if (source_fire) begin
        accepted_count_q <= accepted_count_q + 1'b1;
        if (source_group_beat_q < 8'd127)
          source_group_beat_q <= source_group_beat_q + 1'b1;
        else
          source_group_beat_q <= 8'd128;
      end

      if (flit_fire)
        emitted_count_q <= emitted_count_q + 1'b1;

      if (decoded_fire) begin
        decoded_count_q <= decoded_count_q + 1'b1;
        observed_q <= observed_q ^ fold_all_bits(decoded_data);
        if (decoded_data != expected_decoded_beat)
          mismatch_q <= 1'b1;
        if (decoded_group_beat_q < 8'd127)
          decoded_group_beat_q <= decoded_group_beat_q + 1'b1;
        else
          decoded_group_beat_q <= 8'd128;
      end

      if (decoded_group_last) begin
        completed_group_count_q <= completed_group_count_q + 1'b1;
        group_open_q <= 1'b0;
        group_id_q <= group_id_q + 1'b1;
        decoded_group_beat_q <= 8'b0;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (!((MODE_STATS_ONCE == 0) || (MODE_STATS_ONCE == 1))) begin
      $error("MODE_STATS_ONCE must be 0 or 1");
      $finish(1);
    end
    if (COUNTER_W < 8) begin
      $error("COUNTER_W must be at least 8");
      $finish(1);
    end
  end
`endif
endmodule
