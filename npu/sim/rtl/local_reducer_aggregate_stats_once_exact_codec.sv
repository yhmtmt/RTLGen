`timescale 1ns/1ps

// Exact stats-once transport for one GQA8 aggregate group.
//
// The stream is little-endian at the bit level.  Each head contributes
// max[31:0], exp_sum[32:0], and sixteen 328-bit value slices.  The rolling
// reservoirs are deliberately bounded; neither module stores a whole group.

module local_reducer_aggregate_stats_once_exact_encoder #(
  parameter integer BEAT_W = 419,
  parameter integer FLIT_W = 256,
  parameter integer RESERVOIR_W = 768
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              group_ctx_valid,
  output wire              group_ctx_ready,
  input  wire [15:0]       group_command_id,
  input  wire [4:0]        group_head_base,
  input  wire              beat_valid,
  output wire              beat_ready,
  input  wire [BEAT_W-1:0] beat_data,
  output wire              flit_valid,
  input  wire              flit_ready,
  output wire [FLIT_W-1:0] flit_data,
  output wire              flit_group_last,
  output wire              protocol_error
);
  localparam integer VALUE_W = 328;
  localparam integer STATS_W = 65;
  localparam integer FIRST_APPEND_W = STATS_W + VALUE_W;
  localparam integer BEAT_COUNT_W = 7;
  localparam integer HEAD_OFFSET_W = 3;
  localparam integer SLICE_W = 4;

  reg active_q;
  reg input_done_q;
  reg [15:0] command_q;
  reg [4:0] head_base_q;
  reg [HEAD_OFFSET_W-1:0] head_offset_q;
  reg [SLICE_W-1:0] slice_q;
  reg [BEAT_COUNT_W-1:0] beat_count_q;
  reg head_stats_valid_q;
  reg [31:0] head_max_q;
  reg [32:0] head_sum_q;
  reg [RESERVOIR_W-1:0] reservoir_q;
  reg [10:0] reservoir_count_q;
  reg protocol_error_q;

  wire flit_is_valid = active_q &&
    ((reservoir_count_q >= FLIT_W) ||
     (input_done_q && (reservoir_count_q != 0)));
  wire flit_fire = flit_is_valid && flit_ready;
  wire expected_first_slice = (slice_q == 0);
  wire [9:0] append_count = expected_first_slice ? FIRST_APPEND_W : VALUE_W;
  wire [10:0] reservoir_after_pop_count =
    reservoir_count_q - (flit_fire ? FLIT_W : 0);
  wire append_fits =
    (reservoir_after_pop_count + append_count) <= RESERVOIR_W;
  wire beat_fire = beat_valid && beat_ready;
  wire [4:0] expected_head = head_base_q + head_offset_q;
  wire order_ok =
    (beat_data[15:0] == command_q) &&
    (beat_data[20:16] == expected_head) &&
    (beat_data[89:86] == slice_q) &&
    (beat_data[90] == (slice_q == 15));
  wire stats_ok = expected_first_slice ||
    ((beat_data[52:21] == head_max_q) &&
     (beat_data[85:53] == head_sum_q));

  reg [FIRST_APPEND_W-1:0] append_payload;
  reg [RESERVOIR_W-1:0] append_payload_ext;
  reg [RESERVOIR_W-1:0] reservoir_after_pop;
  reg [RESERVOIR_W-1:0] reservoir_after_append;
  integer append_base;

  assign group_ctx_ready = !active_q;
  assign beat_ready = active_q && !input_done_q && append_fits;
  assign flit_valid = flit_is_valid;
  assign flit_data = flit_is_valid ? reservoir_q[FLIT_W-1:0] : {FLIT_W{1'b0}};
  assign flit_group_last = flit_is_valid && input_done_q &&
    (reservoir_count_q <= FLIT_W);
  assign protocol_error = protocol_error_q;

  // Removing a flit and appending a beat may happen in the same cycle.  The
  // append offset is therefore based on the post-pop reservoir occupancy.
  always @* begin
    append_payload = {FIRST_APPEND_W{1'b0}};
    if (expected_first_slice) begin
      // The stream starts with the 65 statistics bits, followed by the
      // 328-bit value.  Both subfields are themselves LSB-first.
      append_payload[STATS_W-1:0] = beat_data[85:21];
      append_payload[FIRST_APPEND_W-1:STATS_W] = beat_data[BEAT_W-1:91];
    end else begin
      append_payload[VALUE_W-1:0] = beat_data[BEAT_W-1:91];
    end

    reservoir_after_pop = reservoir_q;
    append_base = reservoir_count_q;
    if (flit_fire) begin
      reservoir_after_pop = reservoir_q >> FLIT_W;
      append_base = reservoir_count_q - FLIT_W;
    end

    append_payload_ext = {RESERVOIR_W{1'b0}};
    append_payload_ext[FIRST_APPEND_W-1:0] = append_payload;
    reservoir_after_append = reservoir_after_pop;
    if (beat_fire)
      reservoir_after_append = reservoir_after_pop |
        (append_payload_ext << append_base);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_q <= 1'b0;
      input_done_q <= 1'b0;
      command_q <= 16'b0;
      head_base_q <= 5'b0;
      head_offset_q <= 3'b0;
      slice_q <= 4'b0;
      beat_count_q <= 7'b0;
      head_stats_valid_q <= 1'b0;
      head_max_q <= 32'b0;
      head_sum_q <= 33'b0;
      reservoir_q <= {RESERVOIR_W{1'b0}};
      reservoir_count_q <= 11'b0;
      protocol_error_q <= 1'b0;
    end else begin
      if (group_ctx_valid && group_ctx_ready) begin
        active_q <= 1'b1;
        input_done_q <= 1'b0;
        command_q <= group_command_id;
        head_base_q <= group_head_base;
        head_offset_q <= 3'b0;
        slice_q <= 4'b0;
        beat_count_q <= 7'b0;
        head_stats_valid_q <= 1'b0;
        head_max_q <= 32'b0;
        head_sum_q <= 33'b0;
        reservoir_q <= {RESERVOIR_W{1'b0}};
        reservoir_count_q <= 11'b0;
        if (!((group_head_base == 0) || (group_head_base == 8) ||
              (group_head_base == 16) || (group_head_base == 24)))
          protocol_error_q <= 1'b1;
      end else begin
        reservoir_q <= reservoir_after_append;
        reservoir_count_q <= reservoir_after_pop_count +
          (beat_fire ? append_count : 0);

        if (beat_fire) begin
          if (!order_ok || !stats_ok)
            protocol_error_q <= 1'b1;
          if (expected_first_slice) begin
            head_stats_valid_q <= 1'b1;
            head_max_q <= beat_data[52:21];
            head_sum_q <= beat_data[85:53];
          end
          beat_count_q <= beat_count_q + 1'b1;
          if (beat_count_q == 7'd127) begin
            input_done_q <= 1'b1;
          end else if (slice_q == 4'd15) begin
            head_offset_q <= head_offset_q + 1'b1;
            slice_q <= 4'b0;
            head_stats_valid_q <= 1'b0;
          end else begin
            slice_q <= slice_q + 1'b1;
          end
        end

        if (flit_fire && input_done_q && (reservoir_count_q <= FLIT_W)) begin
          active_q <= 1'b0;
          input_done_q <= 1'b0;
          head_stats_valid_q <= 1'b0;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (BEAT_W != 419) begin
      $error("stats-once encoder BEAT_W must be 419");
      $finish(1);
    end
    if (FLIT_W != 256) begin
      $error("stats-once encoder FLIT_W must be 256");
      $finish(1);
    end
    if (RESERVOIR_W < 648) begin
      $error("stats-once encoder RESERVOIR_W must be at least 648");
      $finish(1);
    end
  end
`endif
endmodule


module local_reducer_aggregate_stats_once_exact_decoder #(
  parameter integer BEAT_W = 419,
  parameter integer FLIT_W = 256,
  parameter integer RESERVOIR_W = 768
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              group_ctx_valid,
  output wire              group_ctx_ready,
  input  wire [15:0]       group_command_id,
  input  wire [4:0]        group_head_base,
  input  wire              flit_valid,
  output wire              flit_ready,
  input  wire [FLIT_W-1:0] flit_data,
  input  wire              flit_group_last,
  output wire              beat_valid,
  input  wire              beat_ready,
  output wire [BEAT_W-1:0] beat_data,
  output wire              protocol_error
);
  localparam integer VALUE_W = 328;
  localparam integer STATS_W = 65;
  localparam integer FIRST_BITS = STATS_W + VALUE_W;

  reg active_q;
  reg input_done_q;
  reg [15:0] command_q;
  reg [4:0] head_base_q;
  reg [2:0] head_offset_q;
  reg [3:0] slice_q;
  reg [7:0] flit_index_q;
  reg [7:0] beat_count_q;
  reg [31:0] head_max_q;
  reg [32:0] head_sum_q;
  reg [RESERVOIR_W-1:0] reservoir_q;
  reg [10:0] reservoir_count_q;
  reg beat_valid_q;
  reg [BEAT_W-1:0] beat_data_q;
  reg protocol_error_q;

  wire first_slice = (slice_q == 0);
  wire [9:0] needed_bits = first_slice ? FIRST_BITS : VALUE_W;
  wire beat_fire = beat_valid_q && beat_ready;
  wire beat_slot_available = !beat_valid_q || beat_fire;
  wire flit_is_last_position = (flit_index_q == 8'd166);
  wire [9:0] accepted_flit_bits = flit_is_last_position ? 10'd8 : FLIT_W;
  wire flit_padding_zero = (flit_data[FLIT_W-1:8] == {(FLIT_W-8){1'b0}});
  wire parse_fire = active_q && beat_slot_available &&
    (beat_count_q < 128) && (reservoir_count_q >= needed_bits);
  wire [10:0] reservoir_after_parse_count = reservoir_count_q -
    (parse_fire ? needed_bits : 0);
  wire flit_has_room =
    (reservoir_after_parse_count + accepted_flit_bits) <= RESERVOIR_W;
  wire flit_fire = flit_valid && flit_ready;

  reg [BEAT_W-1:0] parsed_beat;
  reg [VALUE_W-1:0] parsed_value;
  reg [31:0] parsed_max;
  reg [32:0] parsed_sum;
  reg [RESERVOIR_W-1:0] shifted_reservoir;
  reg [RESERVOIR_W-1:0] flit_payload_ext;
  reg [RESERVOIR_W-1:0] reservoir_after_events;
  integer flit_append_base;

  assign group_ctx_ready = !active_q;
  // A consumed output beat opens the output slot in the same cycle.  Parsing
  // and flit reception may therefore overlap, with the flit appended after
  // the parsed bits in the post-parse reservoir.
  assign flit_ready = active_q && !input_done_q && flit_has_room;
  assign beat_valid = beat_valid_q;
  assign beat_data = beat_data_q;
  assign protocol_error = protocol_error_q;

  always @* begin
    parsed_max = reservoir_q[31:0];
    parsed_sum = reservoir_q[64:32];
    if (first_slice)
      parsed_value = reservoir_q >> STATS_W;
    else
      parsed_value = reservoir_q[VALUE_W-1:0];

    parsed_beat = {BEAT_W{1'b0}};
    parsed_beat[15:0] = command_q;
    parsed_beat[20:16] = head_base_q + head_offset_q;
    parsed_beat[52:21] = first_slice ? parsed_max : head_max_q;
    parsed_beat[85:53] = first_slice ? parsed_sum : head_sum_q;
    parsed_beat[89:86] = slice_q;
    parsed_beat[90] = (slice_q == 15);
    parsed_beat[BEAT_W-1:91] = parsed_value;
    shifted_reservoir = reservoir_q >> needed_bits;

    flit_payload_ext = {RESERVOIR_W{1'b0}};
    if (flit_is_last_position)
      flit_payload_ext[7:0] = flit_data[7:0];
    else
      flit_payload_ext[FLIT_W-1:0] = flit_data;
    flit_append_base = reservoir_after_parse_count;
    reservoir_after_events = shifted_reservoir;
    if (!parse_fire)
      reservoir_after_events = reservoir_q;
    if (flit_fire)
      reservoir_after_events = reservoir_after_events |
        (flit_payload_ext << flit_append_base);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_q <= 1'b0;
      input_done_q <= 1'b0;
      command_q <= 16'b0;
      head_base_q <= 5'b0;
      head_offset_q <= 3'b0;
      slice_q <= 4'b0;
      flit_index_q <= 8'b0;
      beat_count_q <= 8'b0;
      head_max_q <= 32'b0;
      head_sum_q <= 33'b0;
      reservoir_q <= {RESERVOIR_W{1'b0}};
      reservoir_count_q <= 11'b0;
      beat_valid_q <= 1'b0;
      beat_data_q <= {BEAT_W{1'b0}};
      protocol_error_q <= 1'b0;
    end else begin
      if (group_ctx_valid && group_ctx_ready) begin
        active_q <= 1'b1;
        input_done_q <= 1'b0;
        command_q <= group_command_id;
        head_base_q <= group_head_base;
        head_offset_q <= 3'b0;
        slice_q <= 4'b0;
        flit_index_q <= 8'b0;
        beat_count_q <= 8'b0;
        head_max_q <= 32'b0;
        head_sum_q <= 33'b0;
        reservoir_q <= {RESERVOIR_W{1'b0}};
        reservoir_count_q <= 11'b0;
        beat_valid_q <= 1'b0;
        beat_data_q <= {BEAT_W{1'b0}};
        if (!((group_head_base == 0) || (group_head_base == 8) ||
              (group_head_base == 16) || (group_head_base == 24)))
          protocol_error_q <= 1'b1;
      end else begin
        if (beat_fire) begin
          beat_valid_q <= 1'b0;
          beat_data_q <= {BEAT_W{1'b0}};
        end

        reservoir_q <= reservoir_after_events;
        reservoir_count_q <= reservoir_after_parse_count +
          (flit_fire ? accepted_flit_bits : 0);

        if (flit_fire) begin
          if (flit_group_last != flit_is_last_position)
            protocol_error_q <= 1'b1;
          if (flit_is_last_position && !flit_padding_zero)
            protocol_error_q <= 1'b1;
          // An early group-last is an error marker only.  The decoder still
          // requires the exact-position terminal flit and cannot close from
          // the early marker.
          if (flit_is_last_position)
            input_done_q <= 1'b1;
          if (!flit_is_last_position)
            flit_index_q <= flit_index_q + 1'b1;
        end

        if (parse_fire) begin
          beat_valid_q <= 1'b1;
          beat_data_q <= parsed_beat;
          beat_count_q <= beat_count_q + 1'b1;
          if (first_slice) begin
            head_max_q <= parsed_max;
            head_sum_q <= parsed_sum;
          end
          if (slice_q == 4'd15) begin
            head_offset_q <= head_offset_q + 1'b1;
            slice_q <= 4'b0;
          end else begin
            slice_q <= slice_q + 1'b1;
          end
        end

        // A valid group closes only after all 128 reconstructed beats have
        // drained.  A malformed/truncated group can be abandoned once its
        // reservoir is empty, while retaining the sticky error indication.
        if (input_done_q && beat_count_q == 8'd128 && beat_fire &&
            reservoir_after_parse_count == 0) begin
          active_q <= 1'b0;
          input_done_q <= 1'b0;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (BEAT_W != 419) begin
      $error("stats-once decoder BEAT_W must be 419");
      $finish(1);
    end
    if (FLIT_W != 256) begin
      $error("stats-once decoder FLIT_W must be 256");
      $finish(1);
    end
    if (RESERVOIR_W < 584) begin
      $error("stats-once decoder RESERVOIR_W must be at least 584");
      $finish(1);
    end
  end
`endif
endmodule
