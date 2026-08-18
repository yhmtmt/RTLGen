`timescale 1ns/1ps

// Aligned exact transport codec for one checked 419-bit local-reducer aggregate
// beat over a 256-bit flit interface.
//
// Transport contract:
// - One beat always maps to exactly two flits.
// - Phase 0 / last 0 carries beat_data[255:0].
// - Phase 1 / last 1 carries beat_data[418:256] in flit_data[162:0].
// - Phase 1 flit_data[255:163] is deterministically zero padded.
// - Decoder rejects malformed phase/last ordering and nonzero phase-1 padding.

module local_reducer_aggregate_aligned_exact_encoder #(
  parameter integer BEAT_W = 419,
  parameter integer FLIT_W = 256
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              beat_valid,
  output wire              beat_ready,
  input  wire [BEAT_W-1:0] beat_data,
  output wire              flit_valid,
  input  wire              flit_ready,
  output wire [FLIT_W-1:0] flit_data,
  output wire              flit_phase,
  output wire              flit_last
);
  localparam integer SECOND_PAYLOAD_W = BEAT_W - FLIT_W;
  localparam integer SECOND_PAD_W = FLIT_W - SECOND_PAYLOAD_W;

  reg active_r;
  reg phase_r;
  reg [BEAT_W-1:0] beat_data_r;

  wire flit_fire = flit_valid && flit_ready;
  wire release_fire = active_r && phase_r && flit_ready;
  wire beat_fire = beat_valid && beat_ready;

  assign beat_ready = !active_r || release_fire;
  assign flit_valid = active_r;
  assign flit_phase = phase_r;
  assign flit_last = phase_r;
  assign flit_data = !active_r ? {FLIT_W{1'b0}} :
    (phase_r ? {{SECOND_PAD_W{1'b0}}, beat_data_r[BEAT_W-1:FLIT_W]} :
               beat_data_r[FLIT_W-1:0]);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_r <= 1'b0;
      phase_r <= 1'b0;
      beat_data_r <= {BEAT_W{1'b0}};
    end else begin
      if (active_r) begin
        if (flit_fire) begin
          if (!phase_r) begin
            phase_r <= 1'b1;
          end else if (beat_fire) begin
            active_r <= 1'b1;
            phase_r <= 1'b0;
            beat_data_r <= beat_data;
          end else begin
            active_r <= 1'b0;
            phase_r <= 1'b0;
            beat_data_r <= {BEAT_W{1'b0}};
          end
        end
      end else if (beat_fire) begin
        active_r <= 1'b1;
        phase_r <= 1'b0;
        beat_data_r <= beat_data;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (BEAT_W != 419) begin
      $error("local_reducer_aggregate_aligned_exact_encoder BEAT_W must be 419");
      $finish(1);
    end
    if (FLIT_W != 256) begin
      $error("local_reducer_aggregate_aligned_exact_encoder FLIT_W must be 256");
      $finish(1);
    end
  end
`endif
endmodule


module local_reducer_aggregate_aligned_exact_decoder #(
  parameter integer BEAT_W = 419,
  parameter integer FLIT_W = 256
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              flit_valid,
  output wire              flit_ready,
  input  wire [FLIT_W-1:0] flit_data,
  input  wire              flit_phase,
  input  wire              flit_last,
  output wire              beat_valid,
  input  wire              beat_ready,
  output wire [BEAT_W-1:0] beat_data,
  output wire              partial_valid,
  output wire              protocol_error
) ;
  localparam integer SECOND_PAYLOAD_W = BEAT_W - FLIT_W;
  localparam integer SECOND_PAD_W = FLIT_W - SECOND_PAYLOAD_W;

  reg partial_valid_r;
  reg [FLIT_W-1:0] lower_flit_r;
  reg beat_valid_r;
  reg [BEAT_W-1:0] beat_data_r;
  reg protocol_error_r;

  wire flit_fire = flit_valid && flit_ready;
  wire beat_fire = beat_valid && beat_ready;
  wire phase0_valid = !flit_phase && !flit_last;
  wire phase1_valid = flit_phase && flit_last;
  wire phase1_padding_zero = flit_data[FLIT_W-1:SECOND_PAYLOAD_W] == {SECOND_PAD_W{1'b0}};

  assign flit_ready = !beat_valid_r || beat_ready;
  assign beat_valid = beat_valid_r;
  assign beat_data = beat_data_r;
  assign partial_valid = partial_valid_r;
  assign protocol_error = protocol_error_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      partial_valid_r <= 1'b0;
      lower_flit_r <= {FLIT_W{1'b0}};
      beat_valid_r <= 1'b0;
      beat_data_r <= {BEAT_W{1'b0}};
      protocol_error_r <= 1'b0;
    end else begin
      if (beat_fire) begin
        beat_valid_r <= 1'b0;
        beat_data_r <= {BEAT_W{1'b0}};
      end

      if (flit_fire) begin
        if (!partial_valid_r) begin
          if (phase0_valid) begin
            lower_flit_r <= flit_data;
            partial_valid_r <= 1'b1;
          end else begin
            protocol_error_r <= 1'b1;
            partial_valid_r <= 1'b0;
            lower_flit_r <= {FLIT_W{1'b0}};
          end
        end else begin
          if (phase1_valid && phase1_padding_zero) begin
            beat_data_r <= {flit_data[SECOND_PAYLOAD_W-1:0], lower_flit_r};
            beat_valid_r <= 1'b1;
            partial_valid_r <= 1'b0;
            lower_flit_r <= {FLIT_W{1'b0}};
          end else begin
            protocol_error_r <= 1'b1;
            partial_valid_r <= 1'b0;
            lower_flit_r <= {FLIT_W{1'b0}};
          end
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (BEAT_W != 419) begin
      $error("local_reducer_aggregate_aligned_exact_decoder BEAT_W must be 419");
      $finish(1);
    end
    if (FLIT_W != 256) begin
      $error("local_reducer_aggregate_aligned_exact_decoder FLIT_W must be 256");
      $finish(1);
    end
  end
`endif
endmodule
