`timescale 1ns/1ps

// Bounded end-to-end wrapper test.  Four groups are used here because the
// complete path is finite and the exact counter deltas are cheap to check.
// The canonical reference uses max=0, exp_sum=1, and value=1 for every leaf;
// the exact sixteen-leaf finalizer therefore emits 40'h0ffff on every lane,
// matching the established tree reference.
module local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer BEAT_W = 419;
  localparam integer DATA_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer GROUP_FLITS = 15 * 167;
  localparam integer GROUP_PACKETS = 15 * 21;
  localparam integer GROUP_COUNT = 4;
  localparam integer BASE_COMMAND_ID = 16'h5a00;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg [SOURCE_COUNT-1:0] source_beat_valid;
  wire [SOURCE_COUNT-1:0] source_beat_ready;
  reg [SOURCE_COUNT*BEAT_W-1:0] source_beat_data;
  reg root_local_beat_valid;
  wire root_local_beat_ready;
  reg [BEAT_W-1:0] root_local_beat_data;
  reg [SOURCE_COUNT-1:0] remote_group_ready;
  reg root_local_group_ready;
  reg admission_enable;

  wire group_admission_pulse;
  wire [1:0] group_index;
  wire [4:0] head_base;
  wire [2:0] group_epoch;
  wire [SOURCE_COUNT-1:0] source_producer_accept;
  wire root_producer_accept;
  wire [SOURCE_COUNT-1:0] source_ctx_valid;
  wire root_ctx_valid;
  wire [2:0] admitted_group_count;
  wire done;
  wire root_valid;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [SOURCE_COUNT-1:0] group_complete;
  wire [SOURCE_COUNT-1:0] descriptor_installed;
  wire [SOURCE_COUNT-1:0] source_protocol_error;
  wire tree_protocol_error;
  wire protocol_error;
  wire [SOURCE_COUNT*32-1:0] source_tx_descriptor_counts;
  wire [31:0] source_tx_descriptor_count;
  wire [31:0] root_accepted_flit_count;
  wire [31:0] root_descriptor_install_count;
  wire [31:0] root_completion_count;
  wire [31:0] root_replay_packet_count;
  wire [5:0] max_occupied_slots;
  wire [16*32-1:0] mesh_router_accepted_flit_counts;
  wire [31:0] mesh_accepted_flit_count;
  wire [31:0] mesh_contention_cycles;
  wire [31:0] mesh_input_stall_cycles;
  wire [31:0] mesh_output_stall_cycles;

  local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper wrapper (
    .clk(clk),
    .rst_n(rst_n),
    .source_beat_valid(source_beat_valid),
    .source_beat_ready(source_beat_ready),
    .source_beat_data(source_beat_data),
    .root_local_beat_valid(root_local_beat_valid),
    .root_local_beat_ready(root_local_beat_ready),
    .root_local_beat_data(root_local_beat_data),
    .remote_group_ready(remote_group_ready),
    .root_local_group_ready(root_local_group_ready),
    .admission_enable(admission_enable),
    .base_command_id(16'h5a00),
    .group_admission_pulse(group_admission_pulse),
    .group_index(group_index),
    .head_base(head_base),
    .group_epoch(group_epoch),
    .source_producer_accept(source_producer_accept),
    .root_producer_accept(root_producer_accept),
    .source_ctx_valid(source_ctx_valid),
    .root_ctx_valid(root_ctx_valid),
    .admitted_group_count(admitted_group_count),
    .done(done),
    .root_valid(root_valid),
    .root_ready(root_ready),
    .root_command_id(root_command_id),
    .root_head_id(root_head_id),
    .root_slice(root_slice),
    .root_last(root_last),
    .root_value(root_value),
    .group_complete(group_complete),
    .descriptor_installed(descriptor_installed),
    .source_protocol_error(source_protocol_error),
    .tree_protocol_error(tree_protocol_error),
    .protocol_error(protocol_error),
    .source_tx_descriptor_counts(source_tx_descriptor_counts),
    .source_tx_descriptor_count(source_tx_descriptor_count),
    .root_accepted_flit_count(root_accepted_flit_count),
    .root_descriptor_install_count(root_descriptor_install_count),
    .root_completion_count(root_completion_count),
    .root_replay_packet_count(root_replay_packet_count),
    .max_occupied_slots(max_occupied_slots),
    .mesh_router_accepted_flit_counts(mesh_router_accepted_flit_counts),
    .mesh_accepted_flit_count(mesh_accepted_flit_count),
    .mesh_contention_cycles(mesh_contention_cycles),
    .mesh_input_stall_cycles(mesh_input_stall_cycles),
    .mesh_output_stall_cycles(mesh_output_stall_cycles)
  );

  integer source_beat_index [0:SOURCE_COUNT-1];
  integer root_beat_index;
  integer cycle;
  integer root_count;
  integer group_count_seen;
  integer active_group_id;
  reg stream_active;
  integer source_i;
  integer lane_i;
  reg stall_observed;
  reg all_input_done;
  reg [15:0] stalled_command;
  reg [4:0] stalled_head;
  reg [3:0] stalled_slice;
  reg stalled_last;
  reg [319:0] stalled_value;

  function [BEAT_W-1:0] make_canonical_beat;
    input integer group_id;
    input integer beat_id;
    integer lane;
    reg [BEAT_W-1:0] result;
    begin
      result = {BEAT_W{1'b0}};
      result[15:0] = BASE_COMMAND_ID + group_id;
      result[20:16] = group_id * 8 + (beat_id / 16);
      result[52:21] = 32'd0;
      result[85:53] = 33'd1;
      result[89:86] = beat_id % 16;
      result[90] = ((beat_id % 16) == 15);
      for (lane = 0; lane < 8; lane = lane + 1)
        result[91 + lane*41 +: 41] = 41'd1;
      make_canonical_beat = result;
    end
  endfunction

  always @* begin
    source_beat_valid = {SOURCE_COUNT{1'b0}};
    source_beat_data = {(SOURCE_COUNT*BEAT_W){1'b0}};
    root_local_beat_valid = 1'b0;
    root_local_beat_data = {BEAT_W{1'b0}};
    if (stream_active) begin
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
        source_beat_valid[source_i] = (source_beat_index[source_i] < GROUP_BEATS);
        source_beat_data[source_i*BEAT_W +: BEAT_W] =
          make_canonical_beat(active_group_id, source_beat_index[source_i]);
      end
      root_local_beat_valid = (root_beat_index < GROUP_BEATS);
      root_local_beat_data = make_canonical_beat(active_group_id, root_beat_index);
    end
  end

  always @* begin
    all_input_done = (root_beat_index >= GROUP_BEATS);
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
      if (source_beat_index[source_i] < GROUP_BEATS)
        all_input_done = 1'b0;
  end

  // Root output stalls periodically.  This backpressures the shared root and
  // propagates through the mesh, exercising stable output and contention.
  always @* begin
    root_ready = ((cycle % 11) != 3) && ((cycle % 17) != 5);
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      root_count <= 0;
      group_count_seen <= 0;
      active_group_id <= 0;
      stream_active <= 1'b0;
      root_beat_index <= 0;
      stall_observed <= 1'b0;
      stalled_command <= 0;
      stalled_head <= 0;
      stalled_slice <= 0;
      stalled_last <= 1'b0;
      stalled_value <= 0;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        source_beat_index[source_i] <= 0;
    end else begin
      cycle <= cycle + 1;

      if (group_admission_pulse) begin
        if (group_index !== group_count_seen[1:0] ||
            head_base !== group_count_seen*8 ||
            group_epoch !== group_count_seen[2:0] ||
            source_producer_accept !== {SOURCE_COUNT{1'b1}} ||
            !root_producer_accept ||
            source_ctx_valid !== {SOURCE_COUNT{1'b1}} ||
            !root_ctx_valid)
          $fatal(1, "admission metadata or atomic accept mismatch group=%0d", group_count_seen);
        group_count_seen <= group_count_seen + 1;
        active_group_id <= group_index;
        stream_active <= 1'b1;
        remote_group_ready <= {SOURCE_COUNT{1'b0}};
        root_local_group_ready <= 1'b0;
        root_beat_index <= 0;
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
          source_beat_index[source_i] <= 0;
      end else begin
        if (all_input_done && stream_active && group_count_seen < GROUP_COUNT) begin
          remote_group_ready <= {SOURCE_COUNT{1'b1}};
          root_local_group_ready <= 1'b1;
        end
        if (root_local_beat_valid && root_local_beat_ready)
          root_beat_index <= root_beat_index + 1;
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
          if (source_beat_valid[source_i] && source_beat_ready[source_i])
            source_beat_index[source_i] <= source_beat_index[source_i] + 1;
      end

      if (root_valid && !root_ready) begin
        if (!stall_observed) begin
          stalled_command <= root_command_id;
          stalled_head <= root_head_id;
          stalled_slice <= root_slice;
          stalled_last <= root_last;
          stalled_value <= root_value;
          stall_observed <= 1'b1;
        end else if (root_command_id !== stalled_command ||
                     root_head_id !== stalled_head ||
                     root_slice !== stalled_slice ||
                     root_last !== stalled_last ||
                     root_value !== stalled_value) begin
          $fatal(1, "root output changed under backpressure");
        end
      end else begin
        stall_observed <= 1'b0;
      end

      if (protocol_error || tree_protocol_error || (|source_protocol_error))
        $fatal(1, "protocol error wrapper=%0d admission=%0d composition=%0d tree=%0d encoder=%h adapter=%h source=%h",
          protocol_error, wrapper.admission_protocol_error_w,
          wrapper.composition_protocol_error_w, tree_protocol_error,
          wrapper.encoder_protocol_error_w, wrapper.adapter_protocol_error_w,
          source_protocol_error);

      if (root_valid && root_ready) begin
        if (root_command_id !== BASE_COMMAND_ID + (root_count / GROUP_BEATS) ||
            root_head_id !== ((root_count / 16) % 8) +
              ((root_count / GROUP_BEATS) * 8) ||
            root_slice !== (root_count % 16) ||
            root_last !== ((root_count % 16) == 15))
          $fatal(1, "root metadata mismatch row=%0d cmd=%h head=%0d slice=%0d last=%0d",
            root_count, root_command_id, root_head_id, root_slice, root_last);
        for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1)
          if (root_value[lane_i*40 +: 40] !== 40'h0ffff)
            $fatal(1, "root canonical reference mismatch row=%0d lane=%0d value=%h",
              root_count, lane_i, root_value[lane_i*40 +: 40]);
        root_count <= root_count + 1;
      end

      if (cycle > 60000)
        $fatal(1, "wrapper four-group timeout groups=%0d rows=%0d txdesc=%0d flits=%0d",
          group_count_seen, root_count, source_tx_descriptor_count,
          root_accepted_flit_count);

      if (done && root_count == GROUP_COUNT*GROUP_BEATS) begin
        if (group_count_seen != GROUP_COUNT ||
            source_tx_descriptor_count !== GROUP_COUNT*GROUP_PACKETS ||
            root_accepted_flit_count !== GROUP_COUNT*GROUP_FLITS ||
            root_descriptor_install_count !== GROUP_COUNT*GROUP_PACKETS ||
            root_completion_count !== GROUP_COUNT*GROUP_PACKETS ||
            root_replay_packet_count !== GROUP_COUNT*GROUP_PACKETS ||
            mesh_contention_cycles == 0 || mesh_input_stall_cycles == 0 ||
            mesh_output_stall_cycles == 0 || max_occupied_slots > 30)
          $fatal(1, "final wrapper checks failed groups=%0d rows=%0d txdesc=%0d flits=%0d contention=%0d in_stall=%0d out_stall=%0d slots=%0d",
            group_count_seen, root_count, source_tx_descriptor_count,
            root_accepted_flit_count, mesh_contention_cycles,
            mesh_input_stall_cycles, mesh_output_stall_cycles,
            max_occupied_slots);
        $display("PASS exact_transport_wrapper groups=%0d rows=%0d packets_per_group=%0d flits_per_group=%0d txdesc=%0d root_flits=%0d contention=%0d in_stall=%0d out_stall=%0d max_slots=%0d",
          group_count_seen, root_count, GROUP_PACKETS, GROUP_FLITS,
          source_tx_descriptor_count, root_accepted_flit_count,
          mesh_contention_cycles, mesh_input_stall_cycles,
          mesh_output_stall_cycles, max_occupied_slots);
        $finish;
      end
    end
  end

  initial begin
    remote_group_ready = {SOURCE_COUNT{1'b1}};
    root_local_group_ready = 1'b1;
    admission_enable = 1'b1;
    #37;
    rst_n = 1'b1;
  end
endmodule
