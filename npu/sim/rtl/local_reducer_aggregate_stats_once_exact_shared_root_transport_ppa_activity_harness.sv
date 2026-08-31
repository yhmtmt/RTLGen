`timescale 1ns/1ps

// Compact registered activity/PPA boundary for the exact shared-root path.
//
// The wide 419-bit producer streams are intentionally internal.  This keeps
// the physical top-level boundary representative of a macro with a small
// control/status interface while retaining the complete encoder, packet
// adapter, mesh, shared-root storage, decoder, and final tree hierarchy.
module local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness #(
  parameter integer GROUP_COUNT = 4,
  parameter integer MAX_CYCLES = 16'hfffe,
  parameter integer PHYSICAL_BANKS = 15,
  parameter integer USE_FAKERAM = 0,
  parameter integer INTERNAL_MESH = 1
) (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [31:0] control,
  output wire [127:0] observable,
  output wire [15:0] transport_endpoint_in_valid,
  input wire [15:0] transport_endpoint_in_ready,
  output wire [16*4-1:0] transport_endpoint_in_destination,
  output wire [16*4-1:0] transport_endpoint_in_source,
  output wire [16*8-1:0] transport_endpoint_in_tag,
  output wire [16*3-1:0] transport_endpoint_in_fragment,
  output wire [15:0] transport_endpoint_in_last,
  output wire [16*2-1:0] transport_endpoint_in_vc,
  output wire [16*256-1:0] transport_endpoint_in_data,
  input wire [15:0] transport_endpoint_out_valid,
  output wire [15:0] transport_endpoint_out_ready,
  input wire [16*4-1:0] transport_endpoint_out_destination,
  input wire [16*4-1:0] transport_endpoint_out_source,
  input wire [16*8-1:0] transport_endpoint_out_tag,
  input wire [16*3-1:0] transport_endpoint_out_fragment,
  input wire [15:0] transport_endpoint_out_last,
  input wire [16*2-1:0] transport_endpoint_out_vc,
  input wire [16*256-1:0] transport_endpoint_out_data,
  input wire [16*32-1:0] transport_router_accepted_flit_counts,
  input wire [16*32-1:0] transport_router_input_stall_counts,
  input wire [16*32-1:0] transport_router_output_stall_counts,
  input wire [16*32-1:0] transport_router_contention_counts
);
  localparam integer SOURCE_COUNT = 15;
  localparam integer BEAT_W = 419;
  localparam integer GROUP_BEATS = 128;
  localparam integer ROOT_BEATS = GROUP_COUNT * GROUP_BEATS;

  // Keep each source's producer state distinct.  The registered numerator
  // state changes only after a source beat handshake, so the generated beat
  // remains stable for the full valid/ready stall interval.
  (* keep = "true" *) reg [7:0] source_beat_count_q [0:SOURCE_COUNT-1];
  (* keep = "true" *) reg [40:0] source_numerator_q [0:SOURCE_COUNT-1];
  (* keep = "true" *) reg [7:0] root_beat_count_q;
  (* keep = "true" *) reg [40:0] root_numerator_q;

  reg [15:0] base_command_q;
  reg [15:0] stimulus_seed_q;
  reg [4:0] active_head_base_q;
  reg [15:0] active_command_q;
  reg started_q;
  reg producer_ready_q;
  reg group_inflight_q;
  reg done_q;
  reg timeout_q;
  reg protocol_error_q;
  reg root_stall_seen_q;
  reg root_output_seen_q;
  reg [15:0] cycle_count_q;
  reg [2:0] admitted_group_count_q;
  reg [9:0] root_row_count_q;
  reg [13:0] root_flit_count_q;
  reg [10:0] packet_descriptor_count_q;
  reg [10:0] root_completion_count_q;
  reg [63:0] checksum_q;

  reg [SOURCE_COUNT-1:0] source_beat_valid_w;
  wire [SOURCE_COUNT-1:0] source_beat_ready_w;
  reg [SOURCE_COUNT*BEAT_W-1:0] source_beat_data_w;
  reg root_local_beat_valid_w;
  wire root_local_beat_ready_w;
  reg [BEAT_W-1:0] root_local_beat_data_w;
  wire [SOURCE_COUNT-1:0] remote_group_ready_w;
  wire root_local_group_ready_w;
  wire admission_enable_w;
  wire root_ready_w;

  wire group_admission_pulse_w;
  wire [1:0] group_index_w;
  wire [4:0] head_base_w;
  wire [2:0] group_epoch_w;
  wire [SOURCE_COUNT-1:0] source_producer_accept_w;
  wire root_producer_accept_w;
  wire [SOURCE_COUNT-1:0] source_ctx_valid_w;
  wire root_ctx_valid_w;
  wire [2:0] wrapper_admitted_group_count_w;
  wire wrapper_done_w;
  wire root_valid_w;
  wire [15:0] root_command_id_w;
  wire [4:0] root_head_id_w;
  wire [3:0] root_slice_w;
  wire root_last_w;
  wire [319:0] root_value_w;
  wire [SOURCE_COUNT-1:0] group_complete_w;
  wire [SOURCE_COUNT-1:0] descriptor_installed_w;
  wire [SOURCE_COUNT-1:0] source_protocol_error_w;
  wire tree_protocol_error_w;
  wire wrapper_protocol_error_w;
  wire [SOURCE_COUNT*32-1:0] source_tx_descriptor_counts_w;
  wire [31:0] source_tx_descriptor_count_w;
  wire [31:0] root_accepted_flit_count_w;
  wire [31:0] root_descriptor_install_count_w;
  wire [31:0] root_completion_count_w;
  wire [31:0] root_replay_packet_count_w;
  wire [5:0] max_occupied_slots_w;
  wire [16*32-1:0] mesh_router_accepted_flit_counts_w;
  wire [31:0] mesh_accepted_flit_count_w;
  wire [31:0] mesh_contention_cycles_w;
  wire [31:0] mesh_input_stall_cycles_w;
  wire [31:0] mesh_output_stall_cycles_w;

  wire run_w = enable && started_q && !done_q && !timeout_q;
  reg all_input_beats_sent_w;
  wire root_fire_w = root_valid_w && root_ready_w;

  integer source_i;
  integer lane_i;
  reg [63:0] root_mix_w;

  function [40:0] initial_numerator;
    input integer source_id;
    input [15:0] seed;
    input [2:0] epoch;
    begin
      // Source identity and group epoch are part of the registered state,
      // preventing identical source streams from becoming one replicated
      // activity cone in synthesis.
      initial_numerator = {25'd0, seed} + 41'd257 +
        (source_id * 41'd37) + (epoch * 41'd13);
    end
  endfunction

  function [BEAT_W-1:0] make_canonical_beat;
    input [15:0] command_id;
    input [4:0] head_base;
    input [7:0] beat_index;
    input [40:0] numerator;
    integer lane;
    reg [40:0] lane_numerator;
    begin
      make_canonical_beat = {BEAT_W{1'b0}};
      make_canonical_beat[15:0] = command_id;
      make_canonical_beat[20:16] = head_base + beat_index[7:4];
      // The exact stats-once contract carries a head maximum and exp-sum
      // once per head, followed by sixteen value slices.  The harness uses
      // a stable canonical max/sum while varying only the numerators.
      make_canonical_beat[52:21] = 32'd0;
      make_canonical_beat[85:53] = 33'd1;
      make_canonical_beat[89:86] = beat_index[3:0];
      make_canonical_beat[90] = (beat_index[3:0] == 4'd15);
      for (lane = 0; lane < 8; lane = lane + 1) begin
        lane_numerator = numerator + (lane * 41'd3) + 41'd1;
        make_canonical_beat[91 + lane*41 +: 41] = lane_numerator;
      end
    end
  endfunction

  always @* begin
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
      source_beat_valid_w[source_i] = run_w && group_inflight_q &&
        (source_beat_count_q[source_i] < GROUP_BEATS);
      source_beat_data_w[source_i*BEAT_W +: BEAT_W] = make_canonical_beat(
        active_command_q, active_head_base_q, source_beat_count_q[source_i],
        source_numerator_q[source_i]);
    end
    root_local_beat_valid_w = run_w && group_inflight_q &&
      (root_beat_count_q < GROUP_BEATS);
    root_local_beat_data_w = make_canonical_beat(
      active_command_q, active_head_base_q, root_beat_count_q,
      root_numerator_q);
  end

  always @* begin
    all_input_beats_sent_w = (root_beat_count_q >= GROUP_BEATS);
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
      if (source_beat_count_q[source_i] < GROUP_BEATS)
        all_input_beats_sent_w = 1'b0;
  end

  // Producer readiness is a held group-level contract.  It is removed on
  // the atomic admission pulse and re-armed only after all 16 inputs have
  // been accepted, allowing the wrapper's internal contexts to drain.
  assign remote_group_ready_w = {SOURCE_COUNT{
    run_w && producer_ready_q && (wrapper_admitted_group_count_w < GROUP_COUNT)}};
  assign root_local_group_ready_w =
    run_w && producer_ready_q && (wrapper_admitted_group_count_w < GROUP_COUNT);
  assign admission_enable_w = run_w;

  // Registered-cycle-derived periodic stalls exercise root output stability
  // and the backpressure path without exposing a wide control port.
  assign root_ready_w = run_w &&
    (cycle_count_q[3:0] != 4'd3) && (cycle_count_q[5:0] != 6'd37);

  always @* begin
    root_mix_w = {48'd0, root_command_id_w};
    root_mix_w = root_mix_w ^ {59'd0, root_head_id_w};
    root_mix_w = root_mix_w ^ {60'd0, root_slice_w};
    root_mix_w = root_mix_w ^ {63'd0, root_last_w};
    for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1)
      root_mix_w = root_mix_w ^ {24'd0, root_value_w[lane_i*40 +: 40]};
  end

  (* keep_hierarchy = "yes" *)
  local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper #(
    .SOURCE_COUNT(SOURCE_COUNT),
    .BEAT_W(BEAT_W),
    .ROOT_ENDPOINT_ID(15),
    .PHYSICAL_BANKS(PHYSICAL_BANKS),
    .USE_FAKERAM(USE_FAKERAM),
    .INTERNAL_MESH(INTERNAL_MESH)
  ) exact_transport_wrapper (
    .clk(clk),
    .rst_n(rst_n),
    .source_beat_valid(source_beat_valid_w),
    .source_beat_ready(source_beat_ready_w),
    .source_beat_data(source_beat_data_w),
    .root_local_beat_valid(root_local_beat_valid_w),
    .root_local_beat_ready(root_local_beat_ready_w),
    .root_local_beat_data(root_local_beat_data_w),
    .remote_group_ready(remote_group_ready_w),
    .root_local_group_ready(root_local_group_ready_w),
    .admission_enable(admission_enable_w),
    .base_command_id(base_command_q),
    .group_admission_pulse(group_admission_pulse_w),
    .group_index(group_index_w),
    .head_base(head_base_w),
    .group_epoch(group_epoch_w),
    .source_producer_accept(source_producer_accept_w),
    .root_producer_accept(root_producer_accept_w),
    .source_ctx_valid(source_ctx_valid_w),
    .root_ctx_valid(root_ctx_valid_w),
    .admitted_group_count(wrapper_admitted_group_count_w),
    .done(wrapper_done_w),
    .root_valid(root_valid_w),
    .root_ready(root_ready_w),
    .root_command_id(root_command_id_w),
    .root_head_id(root_head_id_w),
    .root_slice(root_slice_w),
    .root_last(root_last_w),
    .root_value(root_value_w),
    .group_complete(group_complete_w),
    .descriptor_installed(descriptor_installed_w),
    .source_protocol_error(source_protocol_error_w),
    .tree_protocol_error(tree_protocol_error_w),
    .protocol_error(wrapper_protocol_error_w),
    .source_tx_descriptor_counts(source_tx_descriptor_counts_w),
    .source_tx_descriptor_count(source_tx_descriptor_count_w),
    .root_accepted_flit_count(root_accepted_flit_count_w),
    .root_descriptor_install_count(root_descriptor_install_count_w),
    .root_completion_count(root_completion_count_w),
    .root_replay_packet_count(root_replay_packet_count_w),
    .max_occupied_slots(max_occupied_slots_w),
    .mesh_router_accepted_flit_counts(mesh_router_accepted_flit_counts_w),
    .mesh_accepted_flit_count(mesh_accepted_flit_count_w),
    .mesh_contention_cycles(mesh_contention_cycles_w),
    .mesh_input_stall_cycles(mesh_input_stall_cycles_w),
    .mesh_output_stall_cycles(mesh_output_stall_cycles_w),
    .transport_endpoint_in_valid(transport_endpoint_in_valid),
    .transport_endpoint_in_ready(transport_endpoint_in_ready),
    .transport_endpoint_in_destination(transport_endpoint_in_destination),
    .transport_endpoint_in_source(transport_endpoint_in_source),
    .transport_endpoint_in_tag(transport_endpoint_in_tag),
    .transport_endpoint_in_fragment(transport_endpoint_in_fragment),
    .transport_endpoint_in_last(transport_endpoint_in_last),
    .transport_endpoint_in_vc(transport_endpoint_in_vc),
    .transport_endpoint_in_data(transport_endpoint_in_data),
    .transport_endpoint_out_valid(transport_endpoint_out_valid),
    .transport_endpoint_out_ready(transport_endpoint_out_ready),
    .transport_endpoint_out_destination(transport_endpoint_out_destination),
    .transport_endpoint_out_source(transport_endpoint_out_source),
    .transport_endpoint_out_tag(transport_endpoint_out_tag),
    .transport_endpoint_out_fragment(transport_endpoint_out_fragment),
    .transport_endpoint_out_last(transport_endpoint_out_last),
    .transport_endpoint_out_vc(transport_endpoint_out_vc),
    .transport_endpoint_out_data(transport_endpoint_out_data),
    .transport_router_accepted_flit_counts(transport_router_accepted_flit_counts),
    .transport_router_input_stall_counts(transport_router_input_stall_counts),
    .transport_router_output_stall_counts(transport_router_output_stall_counts),
    .transport_router_contention_counts(transport_router_contention_counts)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      base_command_q <= 16'h5a00;
      stimulus_seed_q <= 16'h0001;
      active_head_base_q <= 5'd0;
      active_command_q <= 16'h5a00;
      started_q <= 1'b0;
      producer_ready_q <= 1'b0;
      group_inflight_q <= 1'b0;
      done_q <= 1'b0;
      timeout_q <= 1'b0;
      protocol_error_q <= 1'b0;
      root_stall_seen_q <= 1'b0;
      root_output_seen_q <= 1'b0;
      cycle_count_q <= 16'd0;
      admitted_group_count_q <= 3'd0;
      root_row_count_q <= 10'd0;
      root_flit_count_q <= 14'd0;
      packet_descriptor_count_q <= 11'd0;
      root_completion_count_q <= 11'd0;
      checksum_q <= 64'h0000_0000_0000_0001;
      root_beat_count_q <= 8'd0;
      root_numerator_q <= 41'd0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
        source_beat_count_q[source_i] <= 8'd0;
        source_numerator_q[source_i] <= 41'd0;
      end
    end else begin
      if (enable && !started_q) begin
        started_q <= 1'b1;
        base_command_q <= 16'h5a00 ^ {8'd0, control[7:0]};
        stimulus_seed_q <= control[23:8] + 16'd1;
        producer_ready_q <= 1'b1;
      end

      if (run_w && (cycle_count_q != 16'hffff))
        cycle_count_q <= cycle_count_q + 1'b1;

      if (root_valid_w && !root_ready_w)
        root_stall_seen_q <= 1'b1;
      if (root_fire_w) begin
        root_output_seen_q <= 1'b1;
        root_row_count_q <= root_row_count_q + 1'b1;
        checksum_q <= {checksum_q[62:0], checksum_q[63]} ^ root_mix_w ^
          {32'd0, cycle_count_q, 16'd0};
      end

      // These are registered snapshots of the transport-owned counters; the
      // final root checksum and row count are owned by this harness.
      admitted_group_count_q <= wrapper_admitted_group_count_w;
      root_flit_count_q <= root_accepted_flit_count_w[13:0];
      packet_descriptor_count_q <= source_tx_descriptor_count_w[10:0];
      root_completion_count_q <= root_completion_count_w[10:0];
      protocol_error_q <= protocol_error_q || wrapper_protocol_error_w;

      if (group_admission_pulse_w) begin
        producer_ready_q <= 1'b0;
        group_inflight_q <= 1'b1;
        active_command_q <= base_command_q + group_index_w;
        active_head_base_q <= head_base_w;
        root_beat_count_q <= 8'd0;
        root_numerator_q <= initial_numerator(15, stimulus_seed_q, group_epoch_w);
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
          source_beat_count_q[source_i] <= 8'd0;
          source_numerator_q[source_i] <=
            initial_numerator(source_i, stimulus_seed_q, group_epoch_w);
        end
      end else if (group_inflight_q) begin
        if (root_local_beat_valid_w && root_local_beat_ready_w) begin
          root_beat_count_q <= root_beat_count_q + 1'b1;
          root_numerator_q <= root_numerator_q + 41'd17 + cycle_count_q;
        end
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
          if (source_beat_valid_w[source_i] && source_beat_ready_w[source_i]) begin
            source_beat_count_q[source_i] <= source_beat_count_q[source_i] + 1'b1;
            source_numerator_q[source_i] <= source_numerator_q[source_i] +
              41'd17 + source_i + cycle_count_q;
          end
        end
        if (all_input_beats_sent_w) begin
          group_inflight_q <= 1'b0;
          if (wrapper_admitted_group_count_w < GROUP_COUNT)
            producer_ready_q <= 1'b1;
        end
      end

      if (!done_q && wrapper_done_w && root_fire_w &&
          (root_row_count_q == ROOT_BEATS - 1))
        done_q <= 1'b1;

      if (!done_q && (cycle_count_q >= MAX_CYCLES))
        timeout_q <= 1'b1;
    end
  end

  // [127:70] checksum, [69] timeout, [68] protocol error, [67] done,
  // [66] root output seen, [65] root stall seen, [64:49] bounded cycles,
  // [48:38] root completions, [37:27] packet descriptors, [26:13] root
  // flits, [12:3] root rows, and [2:0] admitted groups.
  assign observable = {
    checksum_q[57:0], timeout_q, protocol_error_q, done_q,
    root_output_seen_q, root_stall_seen_q, cycle_count_q,
    root_completion_count_q, packet_descriptor_count_q,
    root_flit_count_q, root_row_count_q, admitted_group_count_q
  };

`ifndef SYNTHESIS
  initial begin
    if (GROUP_COUNT != 4 || SOURCE_COUNT != 15 || BEAT_W != 419 ||
        PHYSICAL_BANKS < 1 || PHYSICAL_BANKS > 15 ||
        (INTERNAL_MESH != 0 && INTERNAL_MESH != 1))
      $error("compact exact transport harness contract changed");
  end
`endif
endmodule
