`timescale 1ns/1ps

// Admit one exact stats-once reduction group only when every producer and
// every destination context can accept it.  This is a context boundary, not
// a packet scheduler: storage slots, descriptors, tags, and addresses remain
// owned by the adapters below this block.
module local_reducer_aggregate_stats_once_exact_shared_root_group_admission #(
  parameter integer SOURCE_COUNT = 15,
  parameter integer GROUP_COUNT = 4
) (
  input wire clk,
  input wire rst_n,
  input wire admission_enable,

  // Fifteen remote producer group-ready levels plus the root-local producer.
  input wire [SOURCE_COUNT-1:0] remote_group_ready,
  input wire root_local_group_ready,

  // Fifteen source-adapter context-ready levels plus shared-root RX ready.
  input wire [SOURCE_COUNT-1:0] source_ctx_ready,
  input wire shared_root_ctx_ready,

  output wire group_admission_pulse,
  output reg [1:0] group_index,
  output reg [4:0] head_base,
  output reg [2:0] group_epoch,
  output wire [SOURCE_COUNT-1:0] source_producer_accept,
  output wire root_producer_accept,
  output wire [SOURCE_COUNT-1:0] source_ctx_valid,
  output wire shared_root_ctx_valid,
  output reg [2:0] admitted_group_count,
  output reg done,
  output reg protocol_error
);
  wire [SOURCE_COUNT:0] producer_ready =
    {root_local_group_ready, remote_group_ready};
  wire [SOURCE_COUNT:0] destination_ready =
    {shared_root_ctx_ready, source_ctx_ready};
  wire all_producers_ready = &producer_ready;
  wire all_destinations_ready = &destination_ready;
  wire admission_fire = admission_enable && !done &&
    all_producers_ready && all_destinations_ready;

  reg [SOURCE_COUNT:0] producer_ready_seen_q;
  reg done_release_seen_q;

  wire producer_readiness_regressed =
    |(producer_ready_seen_q & ~producer_ready);

  // Every context destination observes valid in the same cycle in which all
  // destinations are ready.  The edge therefore accepts either all sixteen
  // contexts or none. Downstream ready is allowed to change while waiting;
  // producer group-ready is the held-valid contract checked for regression.
  assign group_admission_pulse = admission_fire;
  assign source_producer_accept = {SOURCE_COUNT{admission_fire}};
  assign root_producer_accept = admission_fire;
  assign source_ctx_valid = {SOURCE_COUNT{admission_fire}};
  assign shared_root_ctx_valid = admission_fire;

  // The pulse cycle carries the current group metadata.  Advancement is
  // deferred until the following edge, which keeps the admitted tuple stable
  // for every consumer seeing the pulse.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      group_index <= 2'd0;
      head_base <= 5'd0;
      group_epoch <= 3'd0;
      admitted_group_count <= 3'd0;
      done <= 1'b0;
      protocol_error <= 1'b0;
      producer_ready_seen_q <= {(SOURCE_COUNT+1){1'b0}};
      done_release_seen_q <= 1'b0;
    end else begin
      if (admission_fire) begin
        producer_ready_seen_q <= {(SOURCE_COUNT+1){1'b0}};
        admitted_group_count <= admitted_group_count + 3'd1;
        if (group_index == GROUP_COUNT-1) begin
          done <= 1'b1;
          done_release_seen_q <= 1'b0;
        end else begin
          group_index <= group_index + 2'd1;
          head_base <= head_base + 5'd8;
          group_epoch <= group_epoch + 3'd1;
        end
      end else if (!done) begin
        if (admission_enable) begin
          if (producer_readiness_regressed)
            protocol_error <= 1'b1;
          producer_ready_seen_q <= producer_ready_seen_q | producer_ready;
        end else begin
          producer_ready_seen_q <= {(SOURCE_COUNT+1){1'b0}};
        end
      end else begin
        if (!all_producers_ready)
          done_release_seen_q <= 1'b1;
        else if (admission_enable && done_release_seen_q)
          protocol_error <= 1'b1;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (SOURCE_COUNT != 15 || GROUP_COUNT != 4) begin
      $error("exact stats-once group admission requires 15 sources and 4 groups");
      $finish(1);
    end
  end
`endif
endmodule
