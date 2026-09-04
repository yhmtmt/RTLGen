`timescale 1ns/1ps

// Orders transient refill, canonical consumption, and layer transitions by
// accepted payload flits rather than by descriptor admission.
module attention_kv_gather_layer_barrier #(
  parameter integer REFILL_FLITS_PER_LAYER = 69632,
  parameter integer CONSUME_FLITS_PER_LAYER = 4194304,
  parameter integer LAYER_COUNT = 32
) (
  input wire clk,
  input wire rst_n,

  input wire descriptor_valid,
  output wire descriptor_ready,
  input wire [4:0] descriptor_layer,
  input wire descriptor_operation_consume,
  output wire released_valid,
  input wire released_ready,

  input wire [4:0] accepted_refill_flits,
  input wire [4:0] accepted_consume_flits,

  output reg [4:0] active_layer,
  output reg [22:0] refill_flit_count,
  output reg [22:0] consume_flit_count,
  output wire refill_complete,
  output wire consume_complete,
  output reg [5:0] completed_layer_count,
  output reg protocol_error
);
  localparam [23:0] REFILL_TARGET = 24'(REFILL_FLITS_PER_LAYER);
  localparam [23:0] CONSUME_TARGET = 24'(CONSUME_FLITS_PER_LAYER);
  localparam [4:0] FINAL_LAYER = 5'(LAYER_COUNT - 1);

  reg consume_started_q;
  wire same_layer = descriptor_layer == active_layer;
  wire next_layer = active_layer != FINAL_LAYER &&
    descriptor_layer == active_layer + 1'b1;
  wire [23:0] refill_after_accept =
    {1'b0, refill_flit_count} + {19'd0, accepted_refill_flits};
  wire [23:0] consume_after_accept =
    {1'b0, consume_flit_count} + {19'd0, accepted_consume_flits};
  wire release_current_refill =
    same_layer && !descriptor_operation_consume && !consume_started_q;
  wire release_current_consume =
    same_layer && descriptor_operation_consume && refill_complete;
  wire release_next_refill =
    next_layer && !descriptor_operation_consume && consume_complete;
  wire descriptor_order_valid =
    release_current_refill || release_current_consume || release_next_refill;
  wire descriptor_fire = descriptor_valid && descriptor_ready;
  wire impossible_descriptor = descriptor_valid &&
    ((descriptor_layer < active_layer) ||
     (active_layer != FINAL_LAYER &&
      descriptor_layer > active_layer + 1'b1) ||
     (same_layer && !descriptor_operation_consume && consume_started_q) ||
     (next_layer && descriptor_operation_consume));

  assign refill_complete = {1'b0, refill_flit_count} == REFILL_TARGET;
  assign consume_complete = {1'b0, consume_flit_count} == CONSUME_TARGET;
  assign released_valid = descriptor_valid && descriptor_order_valid && !protocol_error;
  assign descriptor_ready = released_ready && descriptor_order_valid && !protocol_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_layer <= 5'd0;
      refill_flit_count <= 23'd0;
      consume_flit_count <= 23'd0;
      consume_started_q <= 1'b0;
      completed_layer_count <= 6'd0;
      protocol_error <= 1'b0;
    end else begin
      if (impossible_descriptor || refill_after_accept > REFILL_TARGET ||
          consume_after_accept > CONSUME_TARGET)
        protocol_error <= 1'b1;

      if (accepted_refill_flits != 0)
        refill_flit_count <= refill_after_accept[22:0];
      if (accepted_consume_flits != 0)
        consume_flit_count <= consume_after_accept[22:0];

      if (descriptor_fire && release_current_consume)
        consume_started_q <= 1'b1;

      if (descriptor_fire && release_next_refill) begin
        active_layer <= descriptor_layer;
        refill_flit_count <= 23'd0;
        consume_flit_count <= 23'd0;
        consume_started_q <= 1'b0;
        completed_layer_count <= completed_layer_count + 1'b1;
      end
      if (active_layer == FINAL_LAYER && consume_started_q &&
          accepted_consume_flits != 0 && consume_after_accept == CONSUME_TARGET)
        completed_layer_count <= completed_layer_count + 1'b1;
    end
  end
endmodule
