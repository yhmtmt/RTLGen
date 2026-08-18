`timescale 1ns/1ps

// Compact-boundary activity harness for the 419b <-> 2x256b aligned codec.
// Source and sink folding are deterministic support logic; no NoC router,
// endpoint, SRAM bitcell, local reducer, or global tree is included.
module local_reducer_aggregate_aligned_exact_codec_ppa_harness #(
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,
  output wire [31:0] observed_data,
  output wire [COUNTER_W-1:0] accepted_beat_count,
  output wire [COUNTER_W-1:0] emitted_flit_count,
  output wire [COUNTER_W-1:0] decoded_beat_count,
  output wire protocol_error
);
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;

  reg [BEAT_W-1:0] source_state_q;
  reg [COUNTER_W-1:0] cycle_count_q;
  reg [COUNTER_W-1:0] accepted_count_q;
  reg [COUNTER_W-1:0] emitted_count_q;
  reg [COUNTER_W-1:0] decoded_count_q;
  reg [31:0] observed_q;

  wire source_valid = cycle_count_q[2:0] != 3'b111;
  wire source_ready;
  wire [BEAT_W-1:0] source_beat = source_state_q;
  wire flit_valid;
  wire flit_ready;
  wire [FLIT_W-1:0] flit_data;
  wire flit_phase;
  wire flit_beat_last;
  wire decoded_valid;
  wire decoded_ready = cycle_count_q[3:1] != 3'b101;
  wire [BEAT_W-1:0] decoded_data;
  wire decoder_partial_valid;
  wire decoder_protocol_error;

  wire source_fire = source_valid && source_ready;
  wire flit_fire = flit_valid && flit_ready;
  wire decoded_fire = decoded_valid && decoded_ready;

  assign accepted_beat_count = accepted_count_q;
  assign emitted_flit_count = emitted_count_q;
  assign decoded_beat_count = decoded_count_q;
  assign observed_data = observed_q;
  assign protocol_error = decoder_protocol_error;

  function [31:0] fold_beat;
    input [BEAT_W-1:0] value;
    integer bit_i;
    begin
      fold_beat = 32'b0;
      for (bit_i = 0; bit_i < BEAT_W; bit_i = bit_i + 1)
        fold_beat[bit_i % 32] = fold_beat[bit_i % 32] ^ value[bit_i];
    end
  endfunction

  (* keep_hierarchy = "yes" *)
  local_reducer_aggregate_aligned_exact_encoder u_encoder (
    .clk(clk),
    .rst_n(rst_n),
    .beat_valid(source_valid),
    .beat_ready(source_ready),
    .beat_data(source_beat),
    .flit_valid(flit_valid),
    .flit_ready(flit_ready),
    .flit_data(flit_data),
    .flit_phase(flit_phase),
    .flit_beat_last(flit_beat_last)
  );

  (* keep_hierarchy = "yes" *)
  local_reducer_aggregate_aligned_exact_decoder u_decoder (
    .clk(clk),
    .rst_n(rst_n),
    .flit_valid(flit_valid),
    .flit_ready(flit_ready),
    .flit_data(flit_data),
    .flit_phase(flit_phase),
    .flit_beat_last(flit_beat_last),
    .beat_valid(decoded_valid),
    .beat_ready(decoded_ready),
    .beat_data(decoded_data),
    .partial_valid(decoder_partial_valid),
    .protocol_error(decoder_protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      source_state_q <= {
        {13{32'h1357_9bdf}},
        3'b101
      };
      cycle_count_q <= {COUNTER_W{1'b0}};
      accepted_count_q <= {COUNTER_W{1'b0}};
      emitted_count_q <= {COUNTER_W{1'b0}};
      decoded_count_q <= {COUNTER_W{1'b0}};
      observed_q <= 32'b0;
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
      if (source_fire) begin
        source_state_q <= {
          source_state_q[BEAT_W-2:0],
          source_state_q[BEAT_W-1] ^ source_state_q[302] ^
          source_state_q[171] ^ source_state_q[5]
        };
        accepted_count_q <= accepted_count_q + 1'b1;
      end
      if (flit_fire)
        emitted_count_q <= emitted_count_q + 1'b1;
      if (decoded_fire) begin
        decoded_count_q <= decoded_count_q + 1'b1;
        observed_q <= fold_beat(decoded_data);
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (COUNTER_W < 4) begin
      $error("local_reducer_aggregate_aligned_exact_codec_ppa_harness COUNTER_W must be at least 4");
      $finish(1);
    end
  end
`endif
endmodule
