`timescale 1ns/1ps

module attention_score32_exact_dual_producer_shared_mesh4x4_tb;
  localparam integer VC0_ADDR_W = 32;
  localparam integer VC0_PACKET_INDEX_W = 7;
  localparam integer VC0_CONTEXTS = 4;
  localparam integer VC0_PACKETS_PER_CONTEXT = 2;
  localparam integer VC0_WORDS_PER_CONTEXT = VC0_PACKETS_PER_CONTEXT * 8;
  localparam integer VC0_DEST_BASE = 4;
  localparam integer VC1_BEAT_W = 419;
  localparam integer VC1_SOURCE_COUNT = 15;
  localparam integer VC1_GROUP_BEATS = 128;
  localparam integer VC1_GROUP_PACKETS = 15 * 21;
  localparam integer VC1_GROUP_FLITS = 15 * 167;
  localparam integer BASE_COMMAND_ID = 16'h6200;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg vc0_layer_start = 1'b0;
  reg vc0_layer_idle = 1'b1;
  reg [7:0] vc0_layer_expected_remote_contexts = VC0_CONTEXTS;
  reg [15:0] vc0_event_valid = 16'b0;
  wire [15:0] vc0_event_ready;
  reg [16*3-1:0] vc0_event_wave = 0;
  reg [16*4-1:0] vc0_event_source = 0;
  reg [16*VC0_ADDR_W-1:0] vc0_event_source_base_addr = 0;
  reg [16*VC0_ADDR_W-1:0] vc0_event_destination_base_addr = 0;
  reg [16*(VC0_PACKET_INDEX_W+1)-1:0] vc0_event_packet_count = 0;
  reg vc0_completion_ready = 1'b0;
  wire vc0_completion_valid;
  wire [2:0] vc0_completion_wave;
  wire [3:0] vc0_completion_destination;
  wire [15:0] vc0_tx_mem_req_valid;
  reg [15:0] vc0_tx_mem_req_ready = 16'b0;
  wire [16*VC0_ADDR_W-1:0] vc0_tx_mem_req_addr;
  reg [15:0] vc0_tx_mem_rsp_valid = 16'b0;
  wire [15:0] vc0_tx_mem_rsp_ready;
  reg [16*256-1:0] vc0_tx_mem_rsp_data = 0;
  wire [15:0] vc0_rx_mem_write_valid;
  reg [15:0] vc0_rx_mem_write_ready = 16'b0;
  wire [16*VC0_ADDR_W-1:0] vc0_rx_mem_write_addr;
  wire [16*256-1:0] vc0_rx_mem_write_data;
  wire vc0_context_valid;
  wire vc0_context_ready;
  wire [2:0] vc0_context_wave;
  wire [3:0] vc0_context_destination;
  wire [3:0] vc0_context_source;
  wire [VC0_ADDR_W-1:0] vc0_context_source_base_addr;
  wire [VC0_ADDR_W-1:0] vc0_context_destination_base_addr;
  wire [VC0_PACKET_INDEX_W:0] vc0_context_packet_count;
  wire vc0_admission_complete;
  wire vc0_transport_complete;
  wire [7:0] vc0_admitted_count;
  wire [7:0] vc0_completed_count;
  wire [15:0] vc0_endpoint_protocol_error;
  wire vc0_protocol_error;

  reg [VC1_SOURCE_COUNT-1:0] vc1_source_beat_valid;
  wire [VC1_SOURCE_COUNT-1:0] vc1_source_beat_ready;
  reg [VC1_SOURCE_COUNT*VC1_BEAT_W-1:0] vc1_source_beat_data;
  reg vc1_root_local_beat_valid;
  wire vc1_root_local_beat_ready;
  reg [VC1_BEAT_W-1:0] vc1_root_local_beat_data;
  reg [VC1_SOURCE_COUNT-1:0] vc1_remote_group_ready;
  reg vc1_root_local_group_ready;
  reg vc1_admission_enable = 1'b1;
  reg [15:0] vc1_base_command_id = BASE_COMMAND_ID;
  wire vc1_group_admission_pulse;
  wire [1:0] vc1_group_index;
  wire [4:0] vc1_head_base;
  wire [2:0] vc1_group_epoch;
  wire [VC1_SOURCE_COUNT-1:0] vc1_source_producer_accept;
  wire vc1_root_producer_accept;
  wire [VC1_SOURCE_COUNT-1:0] vc1_source_ctx_valid;
  wire vc1_root_ctx_valid;
  wire [2:0] vc1_admitted_group_count;
  wire vc1_done;
  wire vc1_root_valid;
  reg vc1_root_ready = 1'b0;
  wire [15:0] vc1_root_command_id;
  wire [4:0] vc1_root_head_id;
  wire [3:0] vc1_root_slice;
  wire vc1_root_last;
  wire [319:0] vc1_root_value;
  wire [VC1_SOURCE_COUNT-1:0] vc1_group_complete;
  wire [VC1_SOURCE_COUNT-1:0] vc1_descriptor_installed;
  wire [VC1_SOURCE_COUNT-1:0] vc1_source_protocol_error;
  wire vc1_tree_protocol_error;
  wire vc1_protocol_error;
  wire [VC1_SOURCE_COUNT*32-1:0] vc1_source_tx_descriptor_counts;
  wire [31:0] vc1_source_tx_descriptor_count;
  wire [31:0] vc1_root_accepted_flit_count;
  wire [31:0] vc1_root_descriptor_install_count;
  wire [31:0] vc1_root_completion_count;
  wire [31:0] vc1_root_replay_packet_count;
  wire [5:0] vc1_max_occupied_slots;
  wire [16*32-1:0] shared_router_accepted_flit_counts;
  wire [31:0] shared_accepted_flit_count;
  wire [31:0] shared_contention_cycles;
  wire [31:0] shared_input_stall_cycles;
  wire [31:0] shared_output_stall_cycles;
  wire [16*32-1:0] shared_router_forwarded_flit_counts;
  wire [16*32-1:0] shared_router_current_input_occupancy;
  wire [16*32-1:0] shared_router_max_input_occupancy;
  wire [16*5*32-1:0] shared_router_route_flit_counts;
  wire [15:0] shared_injection_protocol_error;
  wire [15:0] shared_ejection_protocol_error;
  wire shared_transport_protocol_error;
  wire protocol_error;

  reg vc0_rsp_pending [0:15];
  reg [255:0] vc0_rsp_data_mem [0:15];
  reg [VC0_WORDS_PER_CONTEXT-1:0] vc0_write_seen [0:VC0_CONTEXTS-1];
  integer vc0_source_word_count [0:VC0_CONTEXTS-1];
  integer vc0_context_count = 0;
  integer vc0_completion_count_seen = 0;
  integer vc0_write_count = 0;
  integer vc0_tx_request_count = 0;

  integer vc1_source_beat_index [0:VC1_SOURCE_COUNT-1];
  integer vc1_root_beat_index = 0;
  integer cycle = 0;
  integer vc1_root_count = 0;
  integer vc1_group_count_seen = 0;
  integer vc1_active_group_id = 0;
  integer vc1_descriptor_pulse_count = 0;
  integer vc1_group_complete_pulse_count = 0;
  integer overlap_valid_cycles = 0;
  integer overlap_arbitrated_cycles = 0;
  integer wait_cycles = 0;
  integer req_delta;
  integer overlap_valid_delta;
  integer overlap_arb_delta;
  integer descriptor_delta;
  integer group_complete_delta;
  integer write_delta;
  integer endpoint_i;
  integer source_i;
  integer lane_i;
  integer slot_i;
  integer word_index;
  integer addr_offset;
  reg vc1_stream_active = 1'b0;
  reg vc1_root_stall_observed = 1'b0;
  reg vc1_all_input_done;
  reg [15:0] stalled_command = 0;
  reg [4:0] stalled_head = 0;
  reg [3:0] stalled_slice = 0;
  reg stalled_last = 1'b0;
  reg [319:0] stalled_value = 0;
  reg [VC1_SOURCE_COUNT-1:0] vc1_descriptor_seen = 0;
  reg [VC1_SOURCE_COUNT-1:0] vc1_group_complete_seen = 0;
  reg [VC0_CONTEXTS-1:0] vc0_context_seen = 0;
  reg [VC0_CONTEXTS-1:0] vc0_completion_seen = 0;
  reg vc0_overlap_accept_seen = 1'b0;
  reg vc1_overlap_accept_seen = 1'b0;
  reg [255:0] expected_data;
  reg [VC0_ADDR_W-1:0] expected_addr;

  attention_score32_exact_dual_producer_shared_mesh4x4 dut (
    .clk(clk),
    .rst_n(rst_n),
    .vc0_layer_start(vc0_layer_start),
    .vc0_layer_idle(vc0_layer_idle),
    .vc0_layer_expected_remote_contexts(vc0_layer_expected_remote_contexts),
    .vc0_event_valid(vc0_event_valid),
    .vc0_event_ready(vc0_event_ready),
    .vc0_event_wave(vc0_event_wave),
    .vc0_event_source(vc0_event_source),
    .vc0_event_source_base_addr(vc0_event_source_base_addr),
    .vc0_event_destination_base_addr(vc0_event_destination_base_addr),
    .vc0_event_packet_count(vc0_event_packet_count),
    .vc0_completion_ready(vc0_completion_ready),
    .vc0_completion_valid(vc0_completion_valid),
    .vc0_completion_wave(vc0_completion_wave),
    .vc0_completion_destination(vc0_completion_destination),
    .vc0_tx_mem_req_valid(vc0_tx_mem_req_valid),
    .vc0_tx_mem_req_ready(vc0_tx_mem_req_ready),
    .vc0_tx_mem_req_addr(vc0_tx_mem_req_addr),
    .vc0_tx_mem_rsp_valid(vc0_tx_mem_rsp_valid),
    .vc0_tx_mem_rsp_ready(vc0_tx_mem_rsp_ready),
    .vc0_tx_mem_rsp_data(vc0_tx_mem_rsp_data),
    .vc0_rx_mem_write_valid(vc0_rx_mem_write_valid),
    .vc0_rx_mem_write_ready(vc0_rx_mem_write_ready),
    .vc0_rx_mem_write_addr(vc0_rx_mem_write_addr),
    .vc0_rx_mem_write_data(vc0_rx_mem_write_data),
    .vc0_context_valid(vc0_context_valid),
    .vc0_context_ready(vc0_context_ready),
    .vc0_context_wave(vc0_context_wave),
    .vc0_context_destination(vc0_context_destination),
    .vc0_context_source(vc0_context_source),
    .vc0_context_source_base_addr(vc0_context_source_base_addr),
    .vc0_context_destination_base_addr(vc0_context_destination_base_addr),
    .vc0_context_packet_count(vc0_context_packet_count),
    .vc0_admission_complete(vc0_admission_complete),
    .vc0_transport_complete(vc0_transport_complete),
    .vc0_admitted_count(vc0_admitted_count),
    .vc0_completed_count(vc0_completed_count),
    .vc0_endpoint_protocol_error(vc0_endpoint_protocol_error),
    .vc0_protocol_error(vc0_protocol_error),
    .vc1_source_beat_valid(vc1_source_beat_valid),
    .vc1_source_beat_ready(vc1_source_beat_ready),
    .vc1_source_beat_data(vc1_source_beat_data),
    .vc1_root_local_beat_valid(vc1_root_local_beat_valid),
    .vc1_root_local_beat_ready(vc1_root_local_beat_ready),
    .vc1_root_local_beat_data(vc1_root_local_beat_data),
    .vc1_remote_group_ready(vc1_remote_group_ready),
    .vc1_root_local_group_ready(vc1_root_local_group_ready),
    .vc1_admission_enable(vc1_admission_enable),
    .vc1_base_command_id(vc1_base_command_id),
    .vc1_group_admission_pulse(vc1_group_admission_pulse),
    .vc1_group_index(vc1_group_index),
    .vc1_head_base(vc1_head_base),
    .vc1_group_epoch(vc1_group_epoch),
    .vc1_source_producer_accept(vc1_source_producer_accept),
    .vc1_root_producer_accept(vc1_root_producer_accept),
    .vc1_source_ctx_valid(vc1_source_ctx_valid),
    .vc1_root_ctx_valid(vc1_root_ctx_valid),
    .vc1_admitted_group_count(vc1_admitted_group_count),
    .vc1_done(vc1_done),
    .vc1_root_valid(vc1_root_valid),
    .vc1_root_ready(vc1_root_ready),
    .vc1_root_command_id(vc1_root_command_id),
    .vc1_root_head_id(vc1_root_head_id),
    .vc1_root_slice(vc1_root_slice),
    .vc1_root_last(vc1_root_last),
    .vc1_root_value(vc1_root_value),
    .vc1_group_complete(vc1_group_complete),
    .vc1_descriptor_installed(vc1_descriptor_installed),
    .vc1_source_protocol_error(vc1_source_protocol_error),
    .vc1_tree_protocol_error(vc1_tree_protocol_error),
    .vc1_protocol_error(vc1_protocol_error),
    .vc1_source_tx_descriptor_counts(vc1_source_tx_descriptor_counts),
    .vc1_source_tx_descriptor_count(vc1_source_tx_descriptor_count),
    .vc1_root_accepted_flit_count(vc1_root_accepted_flit_count),
    .vc1_root_descriptor_install_count(vc1_root_descriptor_install_count),
    .vc1_root_completion_count(vc1_root_completion_count),
    .vc1_root_replay_packet_count(vc1_root_replay_packet_count),
    .vc1_max_occupied_slots(vc1_max_occupied_slots),
    .shared_router_accepted_flit_counts(shared_router_accepted_flit_counts),
    .shared_accepted_flit_count(shared_accepted_flit_count),
    .shared_contention_cycles(shared_contention_cycles),
    .shared_input_stall_cycles(shared_input_stall_cycles),
    .shared_output_stall_cycles(shared_output_stall_cycles),
    .shared_router_forwarded_flit_counts(shared_router_forwarded_flit_counts),
    .shared_router_current_input_occupancy(shared_router_current_input_occupancy),
    .shared_router_max_input_occupancy(shared_router_max_input_occupancy),
    .shared_router_route_flit_counts(shared_router_route_flit_counts),
    .shared_injection_protocol_error(shared_injection_protocol_error),
    .shared_ejection_protocol_error(shared_ejection_protocol_error),
    .shared_transport_protocol_error(shared_transport_protocol_error),
    .protocol_error(protocol_error)
  );

  function [VC0_ADDR_W-1:0] vc0_source_base;
    input integer slot;
    begin
      vc0_source_base = 32'h0100_0000 + slot * 32'h0000_1000;
    end
  endfunction

  function [VC0_ADDR_W-1:0] vc0_destination_base;
    input integer slot;
    begin
      vc0_destination_base = 32'h0200_0000 + slot * 32'h0000_1000;
    end
  endfunction

  function [255:0] vc0_memory_word;
    input [3:0] endpoint;
    input [VC0_ADDR_W-1:0] address;
    begin
      vc0_memory_word = {220'b0, endpoint, address};
    end
  endfunction

  function [VC1_BEAT_W-1:0] make_canonical_beat;
    input integer group_id;
    input integer beat_id;
    integer lane;
    reg [VC1_BEAT_W-1:0] result;
    begin
      result = {VC1_BEAT_W{1'b0}};
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
    vc1_source_beat_valid = {VC1_SOURCE_COUNT{1'b0}};
    vc1_source_beat_data = {(VC1_SOURCE_COUNT*VC1_BEAT_W){1'b0}};
    vc1_root_local_beat_valid = 1'b0;
    vc1_root_local_beat_data = {VC1_BEAT_W{1'b0}};
    if (vc1_stream_active) begin
      for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1) begin
        vc1_source_beat_valid[source_i] =
          (vc1_source_beat_index[source_i] < VC1_GROUP_BEATS);
        vc1_source_beat_data[source_i*VC1_BEAT_W +: VC1_BEAT_W] =
          make_canonical_beat(vc1_active_group_id, vc1_source_beat_index[source_i]);
      end
      vc1_root_local_beat_valid = (vc1_root_beat_index < VC1_GROUP_BEATS);
      vc1_root_local_beat_data =
        make_canonical_beat(vc1_active_group_id, vc1_root_beat_index);
    end
  end

  always @* begin
    vc1_all_input_done = (vc1_root_beat_index >= VC1_GROUP_BEATS);
    for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
      if (vc1_source_beat_index[source_i] < VC1_GROUP_BEATS)
        vc1_all_input_done = 1'b0;
  end

  always @* begin
    vc0_tx_mem_req_ready = 16'b0;
    vc0_tx_mem_rsp_valid = 16'b0;
    vc0_tx_mem_rsp_data = 0;
    vc0_rx_mem_write_ready = 16'b0;
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      if (endpoint_i < VC0_CONTEXTS)
        vc0_tx_mem_req_ready[endpoint_i] =
          !vc0_rsp_pending[endpoint_i] &&
          (cycle > 16) &&
          (((cycle + endpoint_i) % 5) != 1);
      vc0_tx_mem_rsp_valid[endpoint_i] = vc0_rsp_pending[endpoint_i];
      vc0_tx_mem_rsp_data[(endpoint_i*256) +: 256] = vc0_rsp_data_mem[endpoint_i];
      if (endpoint_i >= VC0_DEST_BASE && endpoint_i < VC0_DEST_BASE + VC0_CONTEXTS)
        vc0_rx_mem_write_ready[endpoint_i] = (((cycle + endpoint_i) % 7) != 2);
    end
    vc0_completion_ready = 1'b1;
    vc1_root_ready = ((cycle % 11) != 4) && ((cycle % 17) != 6);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      vc0_tx_request_count <= 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        vc0_rsp_pending[endpoint_i] <= 1'b0;
        vc0_rsp_data_mem[endpoint_i] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      req_delta = 0;
      for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
        if (vc0_rsp_pending[endpoint_i]) begin
          if (vc0_tx_mem_rsp_ready[endpoint_i])
            vc0_rsp_pending[endpoint_i] <= 1'b0;
        end else if (vc0_tx_mem_req_valid[endpoint_i] &&
                     vc0_tx_mem_req_ready[endpoint_i]) begin
          vc0_rsp_pending[endpoint_i] <= 1'b1;
          vc0_rsp_data_mem[endpoint_i] <= vc0_memory_word(
            endpoint_i[3:0],
            vc0_tx_mem_req_addr[(endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W]
          );
          req_delta = req_delta + 1;
        end
      end
      vc0_tx_request_count <= vc0_tx_request_count + req_delta;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      vc1_group_count_seen <= 0;
      vc1_active_group_id <= 0;
      vc1_stream_active <= 1'b0;
      vc1_root_beat_index <= 0;
      vc1_root_count <= 0;
      vc1_descriptor_pulse_count <= 0;
      vc1_group_complete_pulse_count <= 0;
      overlap_valid_cycles <= 0;
      overlap_arbitrated_cycles <= 0;
      vc1_descriptor_seen <= 0;
      vc1_group_complete_seen <= 0;
      vc0_context_seen <= 0;
      vc0_completion_seen <= 0;
      vc0_overlap_accept_seen <= 1'b0;
      vc1_overlap_accept_seen <= 1'b0;
      vc1_root_stall_observed <= 1'b0;
      stalled_command <= 0;
      stalled_head <= 0;
      stalled_slice <= 0;
      stalled_last <= 1'b0;
      stalled_value <= 0;
      wait_cycles <= 0;
      for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
        vc1_source_beat_index[source_i] <= 0;
    end else begin
      overlap_valid_delta = 0;
      overlap_arb_delta = 0;
      descriptor_delta = 0;
      group_complete_delta = 0;
      write_delta = 0;
      if (vc1_group_admission_pulse) begin
        if (vc1_group_index !== 0 ||
            vc1_head_base !== 0 ||
            vc1_group_epoch !== 0 ||
            vc1_source_producer_accept !== {VC1_SOURCE_COUNT{1'b1}} ||
            !vc1_root_producer_accept ||
            vc1_source_ctx_valid !== {VC1_SOURCE_COUNT{1'b1}} ||
            !vc1_root_ctx_valid)
          $fatal(1, "vc1 admission metadata mismatch");
        vc1_group_count_seen <= vc1_group_count_seen + 1;
        vc1_active_group_id <= vc1_group_index;
        vc1_stream_active <= 1'b1;
        vc1_remote_group_ready <= {VC1_SOURCE_COUNT{1'b0}};
        vc1_root_local_group_ready <= 1'b0;
        vc1_root_beat_index <= 0;
        for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
          vc1_source_beat_index[source_i] <= 0;
      end else begin
        if (vc1_root_local_beat_valid && vc1_root_local_beat_ready)
          vc1_root_beat_index <= vc1_root_beat_index + 1;
        for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
          if (vc1_source_beat_valid[source_i] && vc1_source_beat_ready[source_i])
            vc1_source_beat_index[source_i] <= vc1_source_beat_index[source_i] + 1;
      end

      for (endpoint_i = 0; endpoint_i < VC0_CONTEXTS; endpoint_i = endpoint_i + 1) begin
        if (dut.vc0_transport_in_valid_w[endpoint_i] &&
            dut.vc1_transport_in_valid_w[endpoint_i]) begin
          overlap_valid_delta = overlap_valid_delta + 1;
          if (dut.vc0_transport_in_ready_w[endpoint_i] ^
              dut.vc1_transport_in_ready_w[endpoint_i])
            overlap_arb_delta = overlap_arb_delta + 1;
        end
        if (dut.vc0_transport_in_valid_w[endpoint_i] &&
            dut.vc0_transport_in_ready_w[endpoint_i])
          vc0_overlap_accept_seen <= 1'b1;
        if (dut.vc1_transport_in_valid_w[endpoint_i] &&
            dut.vc1_transport_in_ready_w[endpoint_i])
          vc1_overlap_accept_seen <= 1'b1;
      end

      for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1) begin
        if (vc1_descriptor_installed[source_i]) begin
          vc1_descriptor_seen[source_i] <= 1'b1;
          descriptor_delta = descriptor_delta + 1;
        end
        if (vc1_group_complete[source_i]) begin
          vc1_group_complete_seen[source_i] <= 1'b1;
          group_complete_delta = group_complete_delta + 1;
        end
      end
      overlap_valid_cycles <= overlap_valid_cycles + overlap_valid_delta;
      overlap_arbitrated_cycles <=
        overlap_arbitrated_cycles + overlap_arb_delta;
      vc1_descriptor_pulse_count <=
        vc1_descriptor_pulse_count + descriptor_delta;
      vc1_group_complete_pulse_count <=
        vc1_group_complete_pulse_count + group_complete_delta;

      if (vc1_root_valid && !vc1_root_ready) begin
        if (!vc1_root_stall_observed) begin
          stalled_command <= vc1_root_command_id;
          stalled_head <= vc1_root_head_id;
          stalled_slice <= vc1_root_slice;
          stalled_last <= vc1_root_last;
          stalled_value <= vc1_root_value;
          vc1_root_stall_observed <= 1'b1;
        end else if (vc1_root_command_id !== stalled_command ||
                     vc1_root_head_id !== stalled_head ||
                     vc1_root_slice !== stalled_slice ||
                     vc1_root_last !== stalled_last ||
                     vc1_root_value !== stalled_value) begin
          $fatal(1, "vc1 root output changed under backpressure");
        end
      end else begin
        vc1_root_stall_observed <= 1'b0;
      end

      if (vc1_root_valid && vc1_root_ready) begin
        if (vc1_root_command_id !== BASE_COMMAND_ID ||
            vc1_root_head_id !== ((vc1_root_count / 16) % 8) ||
            vc1_root_slice !== (vc1_root_count % 16) ||
            vc1_root_last !== ((vc1_root_count % 16) == 15))
          $fatal(1, "vc1 root metadata mismatch row=%0d cmd=%h head=%0d slice=%0d last=%0d",
            vc1_root_count, vc1_root_command_id, vc1_root_head_id,
            vc1_root_slice, vc1_root_last);
        for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1)
          if (vc1_root_value[lane_i*40 +: 40] !== 40'h0ffff)
            $fatal(1, "vc1 root canonical mismatch row=%0d lane=%0d value=%h",
              vc1_root_count, lane_i, vc1_root_value[lane_i*40 +: 40]);
        vc1_root_count <= vc1_root_count + 1;
      end

      if (vc0_context_valid && vc0_context_ready) begin
        slot_i = vc0_context_destination - VC0_DEST_BASE;
        if (slot_i < 0 || slot_i >= VC0_CONTEXTS || vc0_context_seen[slot_i])
          $fatal(1, "unexpected/duplicate vc0 context dst=%0d slot=%0d seen=%b",
            vc0_context_destination, slot_i, vc0_context_seen);
        if (vc0_context_wave !== 0 ||
            vc0_context_source !== slot_i[3:0] ||
            vc0_context_source_base_addr !== vc0_source_base(slot_i) ||
            vc0_context_destination_base_addr !== vc0_destination_base(slot_i) ||
            vc0_context_packet_count !== VC0_PACKETS_PER_CONTEXT)
          $fatal(1, "vc0 context mismatch idx=%0d dst=%0d src=%0d",
            vc0_context_count, vc0_context_destination, vc0_context_source);
        vc0_context_seen[slot_i] <= 1'b1;
        vc0_context_count <= vc0_context_count + 1;
      end

      if (vc0_completion_valid && vc0_completion_ready) begin
        slot_i = vc0_completion_destination - VC0_DEST_BASE;
        if (slot_i < 0 || slot_i >= VC0_CONTEXTS || vc0_completion_seen[slot_i])
          $fatal(1, "unexpected/duplicate vc0 completion dst=%0d slot=%0d seen=%b",
            vc0_completion_destination, slot_i, vc0_completion_seen);
        if (vc0_completion_wave !== 0)
          $fatal(1, "vc0 completion mismatch idx=%0d wave=%0d dst=%0d",
            vc0_completion_count_seen, vc0_completion_wave,
            vc0_completion_destination);
        vc0_completion_seen[slot_i] <= 1'b1;
        vc0_completion_count_seen <= vc0_completion_count_seen + 1;
      end

      for (endpoint_i = VC0_DEST_BASE;
           endpoint_i < VC0_DEST_BASE + VC0_CONTEXTS;
           endpoint_i = endpoint_i + 1) begin
        if (vc0_rx_mem_write_valid[endpoint_i] &&
            vc0_rx_mem_write_ready[endpoint_i]) begin
          slot_i = endpoint_i - VC0_DEST_BASE;
          addr_offset = vc0_rx_mem_write_addr[(endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] -
            vc0_destination_base(slot_i);
          if (addr_offset < 0 || (addr_offset % 32) != 0)
            $fatal(1, "unaligned vc0 destination write endpoint=%0d offset=%0d",
              endpoint_i, addr_offset);
          word_index = addr_offset / 32;
          if (word_index < 0 || word_index >= VC0_WORDS_PER_CONTEXT ||
              vc0_write_seen[slot_i][word_index])
            $fatal(1, "duplicate/out-of-range vc0 write endpoint=%0d word=%0d",
              endpoint_i, word_index);
          expected_addr = vc0_source_base(slot_i) + addr_offset;
          expected_data = vc0_memory_word(slot_i[3:0], expected_addr);
          if (vc0_rx_mem_write_data[(endpoint_i*256) +: 256] !== expected_data)
            $fatal(1, "vc0 payload mismatch endpoint=%0d word=%0d", endpoint_i, word_index);
          vc0_write_seen[slot_i][word_index] <= 1'b1;
          vc0_source_word_count[slot_i] <= vc0_source_word_count[slot_i] + 1;
          write_delta = write_delta + 1;
        end
      end
      vc0_write_count <= vc0_write_count + write_delta;

      if (protocol_error || vc0_protocol_error || vc1_protocol_error ||
          vc1_tree_protocol_error || shared_transport_protocol_error ||
          (|vc0_endpoint_protocol_error) || (|vc1_source_protocol_error) ||
          (|shared_injection_protocol_error) || (|shared_ejection_protocol_error))
        $fatal(1, "protocol error top=%0d vc0=%0d vc1=%0d tree=%0d shared=%0d vc0_ep=%h vc1_src=%h inj=%h ej=%h",
          protocol_error, vc0_protocol_error, vc1_protocol_error,
          vc1_tree_protocol_error, shared_transport_protocol_error,
          vc0_endpoint_protocol_error, vc1_source_protocol_error,
          shared_injection_protocol_error, shared_ejection_protocol_error);

      if (vc0_transport_complete &&
          vc1_root_count == VC1_GROUP_BEATS &&
          vc1_source_tx_descriptor_count == VC1_GROUP_PACKETS &&
          vc1_root_completion_count == VC1_GROUP_PACKETS)
        wait_cycles <= wait_cycles + 1;
      else
        wait_cycles <= 0;

      if (wait_cycles == 4) begin
        if (!vc0_admission_complete ||
            vc0_admitted_count !== VC0_CONTEXTS ||
            vc0_completed_count !== VC0_CONTEXTS ||
            vc0_context_count !== VC0_CONTEXTS ||
            vc0_completion_count_seen !== VC0_CONTEXTS ||
            vc0_context_seen !== {VC0_CONTEXTS{1'b1}} ||
            vc0_completion_seen !== {VC0_CONTEXTS{1'b1}} ||
            vc0_write_count !== VC0_CONTEXTS * VC0_WORDS_PER_CONTEXT)
          $fatal(1, "vc0 totals mismatch admitted=%0d completed=%0d contexts=%0d comp=%0d req=%0d writes=%0d",
            vc0_admitted_count, vc0_completed_count, vc0_context_count,
            vc0_completion_count_seen, vc0_tx_request_count, vc0_write_count);
        for (slot_i = 0; slot_i < VC0_CONTEXTS; slot_i = slot_i + 1)
          if (vc0_write_seen[slot_i] !== {VC0_WORDS_PER_CONTEXT{1'b1}})
            $fatal(1, "missing vc0 writes slot=%0d seen=%h",
              slot_i, vc0_write_seen[slot_i]);
        if (vc1_group_count_seen !== 1 ||
            vc1_admitted_group_count !== 1 ||
            vc1_root_count !== VC1_GROUP_BEATS ||
            vc1_descriptor_seen !== {VC1_SOURCE_COUNT{1'b1}} ||
            vc1_group_complete_seen !== {VC1_SOURCE_COUNT{1'b1}} ||
            vc1_descriptor_pulse_count !== VC1_GROUP_PACKETS ||
            vc1_group_complete_pulse_count !== VC1_SOURCE_COUNT ||
            vc1_source_tx_descriptor_count !== VC1_GROUP_PACKETS ||
            vc1_root_accepted_flit_count !== VC1_GROUP_FLITS ||
            vc1_root_descriptor_install_count !== VC1_GROUP_PACKETS ||
            vc1_root_completion_count !== VC1_GROUP_PACKETS ||
            vc1_root_replay_packet_count !== VC1_GROUP_PACKETS)
          $fatal(1, "vc1 totals mismatch groups=%0d rows=%0d desc_pulses=%0d complete_pulses=%0d txdesc=%0d flits=%0d installs=%0d completions=%0d replay=%0d",
            vc1_group_count_seen, vc1_root_count, vc1_descriptor_pulse_count,
            vc1_group_complete_pulse_count, vc1_source_tx_descriptor_count,
            vc1_root_accepted_flit_count, vc1_root_descriptor_install_count,
            vc1_root_completion_count, vc1_root_replay_packet_count);
        for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
          if (vc1_source_tx_descriptor_counts[source_i*32 +: 32] !== 21)
            $fatal(1, "vc1 source descriptor count mismatch source=%0d count=%0d",
              source_i, vc1_source_tx_descriptor_counts[source_i*32 +: 32]);
        if (!vc0_overlap_accept_seen || !vc1_overlap_accept_seen ||
            overlap_valid_cycles == 0 || overlap_arbitrated_cycles == 0 ||
            shared_contention_cycles == 0 || shared_input_stall_cycles == 0 ||
            shared_output_stall_cycles == 0)
          $fatal(1, "shared contention missing vc0_accept=%0d vc1_accept=%0d valid_cycles=%0d arb_cycles=%0d shared_contention=%0d in_stall=%0d out_stall=%0d",
            vc0_overlap_accept_seen, vc1_overlap_accept_seen,
            overlap_valid_cycles, overlap_arbitrated_cycles,
            shared_contention_cycles, shared_input_stall_cycles,
            shared_output_stall_cycles);
        $display("PASS exact_dual_producer_shared_mesh vc0_words=%0d vc0_contexts=%0d vc1_rows=%0d vc1_packets=%0d vc1_flits=%0d overlap_valid=%0d overlap_arb=%0d shared_contention=%0d",
          vc0_write_count, vc0_context_count, vc1_root_count,
          vc1_source_tx_descriptor_count, vc1_root_accepted_flit_count,
          overlap_valid_cycles, overlap_arbitrated_cycles, shared_contention_cycles);
        $finish;
      end

      if (cycle > 120000)
        $fatal(1, "dual producer shared mesh timeout cycle=%0d vc0_req=%0d vc0_writes=%0d vc0_admitted=%0d vc0_completed=%0d vc0_contexts=%0d vc0_seen=%0d vc0_done=%0d vc1_rows=%0d vc1_packets=%0d vc1_done=%0d",
          cycle, vc0_tx_request_count, vc0_write_count, vc0_admitted_count,
          vc0_completed_count, vc0_context_count, vc0_completion_count_seen,
          vc0_transport_complete, vc1_root_count, vc1_source_tx_descriptor_count,
          vc1_done);
    end
  end

  initial begin
    for (endpoint_i = 0; endpoint_i < 16; endpoint_i = endpoint_i + 1) begin
      vc0_rsp_pending[endpoint_i] = 1'b0;
      vc0_rsp_data_mem[endpoint_i] = 0;
    end
    for (slot_i = 0; slot_i < VC0_CONTEXTS; slot_i = slot_i + 1) begin
      vc0_write_seen[slot_i] = 0;
      vc0_source_word_count[slot_i] = 0;
    end
    for (source_i = 0; source_i < VC1_SOURCE_COUNT; source_i = source_i + 1)
      vc1_source_beat_index[source_i] = 0;
    vc1_remote_group_ready = {VC1_SOURCE_COUNT{1'b1}};
    vc1_root_local_group_ready = 1'b1;

    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    vc0_layer_start = 1'b1;
    @(posedge clk);
    @(negedge clk);
    vc0_layer_start = 1'b0;
    for (slot_i = 0; slot_i < VC0_CONTEXTS; slot_i = slot_i + 1) begin
      vc0_event_valid[VC0_DEST_BASE + slot_i] = 1'b1;
      vc0_event_wave[(VC0_DEST_BASE + slot_i)*3 +: 3] = 0;
      vc0_event_source[(VC0_DEST_BASE + slot_i)*4 +: 4] = slot_i[3:0];
      vc0_event_source_base_addr[(VC0_DEST_BASE + slot_i)*VC0_ADDR_W +: VC0_ADDR_W] =
        vc0_source_base(slot_i);
      vc0_event_destination_base_addr[(VC0_DEST_BASE + slot_i)*VC0_ADDR_W +: VC0_ADDR_W] =
        vc0_destination_base(slot_i);
      vc0_event_packet_count[(VC0_DEST_BASE + slot_i)*(VC0_PACKET_INDEX_W+1) +:
        (VC0_PACKET_INDEX_W+1)] = VC0_PACKETS_PER_CONTEXT;
    end
    @(posedge clk);
    for (slot_i = 0; slot_i < VC0_CONTEXTS; slot_i = slot_i + 1)
      if (!vc0_event_ready[VC0_DEST_BASE + slot_i])
        $fatal(1, "vc0 event not accepted dst=%0d ready=%b",
          VC0_DEST_BASE + slot_i, vc0_event_ready[VC0_DEST_BASE + slot_i]);
    @(negedge clk);
    vc0_event_valid = 0;
  end
endmodule
