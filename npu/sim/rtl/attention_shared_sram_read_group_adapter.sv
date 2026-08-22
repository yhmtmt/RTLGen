`timescale 1ns/1ps

// Packs ordered endpoint SRAM reads into one aligned shared-SRAM macro read.
//
// The endpoint side is an ordered byte-addressed beat stream.  The macro side
// returns one 1024-bit word and echoes the request slot and address as
// metadata.  Two group slots are used by default so collection, macro access,
// and ordered emission can overlap.
module attention_shared_sram_read_group_adapter #(
  parameter integer ADDR_W = 32,
  parameter integer BEAT_W = 256,
  parameter integer GROUP_SLOTS = 2
) (
  input wire clk,
  input wire rst_n,

  input wire req_valid,
  output wire req_ready,
  input wire [ADDR_W-1:0] req_addr,

  output wire rsp_valid,
  input wire rsp_ready,
  output wire [BEAT_W-1:0] rsp_data,
  output wire [ADDR_W-1:0] rsp_addr,

  output wire macro_req_valid,
  input wire macro_req_ready,
  output wire [ADDR_W-1:0] macro_req_addr,
  output wire [(GROUP_SLOTS <= 1 ? 1 : $clog2(GROUP_SLOTS))-1:0] macro_req_slot,

  input wire macro_rsp_valid,
  output wire macro_rsp_ready,
  input wire [1023:0] macro_rsp_data,
  input wire [ADDR_W-1:0] macro_rsp_addr,
  input wire [(GROUP_SLOTS <= 1 ? 1 : $clog2(GROUP_SLOTS))-1:0] macro_rsp_slot,

  output reg protocol_error,
  output reg [63:0] beat_request_count,
  output reg [63:0] macro_read_count,
  output reg [63:0] beat_response_count,
  output reg [63:0] beat_request_stall_count,
  output reg [63:0] beat_response_stall_count,
  output reg [63:0] macro_request_stall_count,
  output reg [63:0] macro_response_stall_count,
  output wire access_reduction_proven
);
  localparam integer MACRO_W = 1024;
  localparam integer MACRO_BYTES = MACRO_W / 8;
  localparam integer BEAT_BYTES = BEAT_W / 8;
  localparam integer SEGMENTS = MACRO_W / BEAT_W;
  localparam integer SLOT_W = (GROUP_SLOTS <= 1) ? 1 : $clog2(GROUP_SLOTS);
  localparam integer BEAT_ALIGN_W = $clog2(BEAT_BYTES);
  localparam integer MACRO_ALIGN_W = $clog2(MACRO_BYTES);
  localparam integer SEGMENT_W = (SEGMENTS <= 1) ? 1 : $clog2(SEGMENTS);
  localparam [SLOT_W-1:0] LAST_SLOT = SLOT_W'(GROUP_SLOTS - 1);
  localparam [SEGMENT_W-1:0] LAST_SEGMENT = SEGMENT_W'(SEGMENTS - 1);

  localparam [2:0] ST_EMPTY = 3'd0;
  localparam [2:0] ST_COLLECT = 3'd1;
  localparam [2:0] ST_READY = 3'd2;
  localparam [2:0] ST_INFLIGHT = 3'd3;
  localparam [2:0] ST_EMIT = 3'd4;

  reg [2:0] slot_state [0:GROUP_SLOTS-1];
  reg [ADDR_W-1:0] slot_base_addr [0:GROUP_SLOTS-1];
  reg [ADDR_W-1:0] slot_next_addr [0:GROUP_SLOTS-1];
  (* keep = "true" *) reg [MACRO_W-1:0] slot_data [0:GROUP_SLOTS-1];

  reg [SLOT_W-1:0] collect_slot_q;
  reg [SLOT_W-1:0] issue_slot_q;
  reg [SLOT_W-1:0] emit_slot_q;
  reg [SLOT_W-1:0] macro_slot_q;
  reg [ADDR_W-1:0] macro_addr_q;
  reg macro_inflight_q;
  reg [SEGMENT_W-1:0] emit_index_q;

  integer reset_i;

  function [SLOT_W-1:0] slot_inc;
    input [SLOT_W-1:0] slot;
    begin
      if (slot == LAST_SLOT)
        slot_inc = {SLOT_W{1'b0}};
      else
        slot_inc = slot + 1'b1;
    end
  endfunction

  wire collect_slot_empty = slot_state[collect_slot_q] == ST_EMPTY;
  wire collect_slot_active = slot_state[collect_slot_q] == ST_COLLECT;
  wire first_request_valid =
    (req_addr[BEAT_ALIGN_W-1:0] == {BEAT_ALIGN_W{1'b0}}) &&
    (req_addr[MACRO_ALIGN_W-1:0] == {MACRO_ALIGN_W{1'b0}});
  wire continuing_request_valid = req_addr == slot_next_addr[collect_slot_q];
  wire request_metadata_valid = collect_slot_empty ? first_request_valid :
    (collect_slot_active ? continuing_request_valid : 1'b0);
  wire request_slot_available = collect_slot_empty || collect_slot_active;
  wire request_fire = req_valid && req_ready;
  wire request_metadata_error = req_valid && !protocol_error &&
    request_slot_available && !request_metadata_valid;

  assign req_ready = !protocol_error && request_slot_available &&
    request_metadata_valid;

  wire macro_response_valid_for_request =
    macro_rsp_valid && macro_inflight_q;
  wire macro_response_metadata_valid =
    (macro_rsp_slot == macro_slot_q) && (macro_rsp_addr == macro_addr_q);
  wire macro_response_metadata_error =
    macro_response_valid_for_request && !macro_response_metadata_valid;
  wire macro_response_without_request = macro_rsp_valid && !macro_inflight_q;
  wire macro_response_fire = macro_rsp_valid && macro_rsp_ready;
  wire macro_response_accept = macro_response_fire &&
    macro_response_metadata_valid;
  wire macro_request_fire = macro_req_valid && macro_req_ready;

  assign macro_req_valid = !protocol_error &&
    (!macro_inflight_q || macro_response_accept) &&
    (slot_state[issue_slot_q] == ST_READY);
  assign macro_req_addr = slot_base_addr[issue_slot_q];
  assign macro_req_slot = issue_slot_q;

  // The macro word is captured as soon as its request is in flight.  A bad
  // response is consumed only when it is for the active transaction; the
  // sticky error then prevents any further architectural activity.
  assign macro_rsp_ready = macro_inflight_q && !protocol_error;

  assign rsp_valid = !protocol_error && (slot_state[emit_slot_q] == ST_EMIT);
  assign rsp_data = slot_data[emit_slot_q][emit_index_q * BEAT_W +: BEAT_W];
  assign rsp_addr = slot_base_addr[emit_slot_q] + (emit_index_q * BEAT_BYTES);
  wire response_fire = rsp_valid && rsp_ready;

  assign access_reduction_proven =
    (macro_read_count != 0) &&
    (beat_request_count == (macro_read_count * SEGMENTS)) &&
    (beat_response_count == beat_request_count);

`ifndef SYNTHESIS
  initial begin
    if (BEAT_W != 256 && BEAT_W != 512) begin
      $error("attention_shared_sram_read_group_adapter BEAT_W must be 256 or 512");
      $finish(1);
    end
    if ((MACRO_W % BEAT_W) != 0 || SEGMENTS < 1) begin
      $error("attention_shared_sram_read_group_adapter invalid segment geometry");
      $finish(1);
    end
    if (GROUP_SLOTS < 1) begin
      $error("attention_shared_sram_read_group_adapter GROUP_SLOTS must be positive");
      $finish(1);
    end
  end
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      collect_slot_q <= {SLOT_W{1'b0}};
      issue_slot_q <= {SLOT_W{1'b0}};
      emit_slot_q <= {SLOT_W{1'b0}};
      macro_slot_q <= {SLOT_W{1'b0}};
      macro_addr_q <= {ADDR_W{1'b0}};
      macro_inflight_q <= 1'b0;
      emit_index_q <= {SEGMENT_W{1'b0}};
      protocol_error <= 1'b0;
      beat_request_count <= 64'd0;
      macro_read_count <= 64'd0;
      beat_response_count <= 64'd0;
      beat_request_stall_count <= 64'd0;
      beat_response_stall_count <= 64'd0;
      macro_request_stall_count <= 64'd0;
      macro_response_stall_count <= 64'd0;
      for (reset_i = 0; reset_i < GROUP_SLOTS; reset_i = reset_i + 1) begin
        slot_state[reset_i] <= ST_EMPTY;
        slot_base_addr[reset_i] <= {ADDR_W{1'b0}};
        slot_next_addr[reset_i] <= {ADDR_W{1'b0}};
      end
    end else begin
      if (request_metadata_error || macro_response_metadata_error ||
          macro_response_without_request)
        protocol_error <= 1'b1;

      if (req_valid && !req_ready)
        beat_request_stall_count <= beat_request_stall_count + 1'b1;
      if (rsp_valid && !rsp_ready)
        beat_response_stall_count <= beat_response_stall_count + 1'b1;
      if (macro_req_valid && !macro_req_ready)
        macro_request_stall_count <= macro_request_stall_count + 1'b1;
      if (macro_rsp_valid && !macro_rsp_ready)
        macro_response_stall_count <= macro_response_stall_count + 1'b1;

      if (request_fire) begin
        beat_request_count <= beat_request_count + 1'b1;
        if (collect_slot_empty) begin
          slot_base_addr[collect_slot_q] <= req_addr;
          slot_next_addr[collect_slot_q] <= req_addr + BEAT_BYTES;
          if (SEGMENTS == 1) begin
            slot_state[collect_slot_q] <= ST_READY;
            collect_slot_q <= slot_inc(collect_slot_q);
          end else begin
            slot_state[collect_slot_q] <= ST_COLLECT;
          end
        end else begin
          slot_next_addr[collect_slot_q] <= req_addr + BEAT_BYTES;
          if (slot_next_addr[collect_slot_q] + BEAT_BYTES ==
              slot_base_addr[collect_slot_q] + MACRO_BYTES) begin
            slot_state[collect_slot_q] <= ST_READY;
            collect_slot_q <= slot_inc(collect_slot_q);
          end
        end
      end

      if (macro_response_accept) begin
        macro_inflight_q <= 1'b0;
        slot_data[macro_slot_q] <= macro_rsp_data;
        slot_state[macro_slot_q] <= ST_EMIT;
      end

      // Retire and launch may handshake together.  The new request
      // assignment intentionally follows response retirement so the single
      // macro port remains in flight for the next group.
      if (macro_request_fire) begin
        macro_inflight_q <= 1'b1;
        macro_slot_q <= issue_slot_q;
        macro_addr_q <= slot_base_addr[issue_slot_q];
        slot_state[issue_slot_q] <= ST_INFLIGHT;
        issue_slot_q <= slot_inc(issue_slot_q);
        macro_read_count <= macro_read_count + 1'b1;
      end

      if (response_fire) begin
        beat_response_count <= beat_response_count + 1'b1;
        if (emit_index_q == LAST_SEGMENT) begin
          slot_state[emit_slot_q] <= ST_EMPTY;
          emit_slot_q <= slot_inc(emit_slot_q);
          emit_index_q <= {SEGMENT_W{1'b0}};
        end else begin
          emit_index_q <= emit_index_q + 1'b1;
        end
      end
    end
  end
endmodule
