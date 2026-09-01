`timescale 1ns/1ps

module attention_score32_exact_dual_producer_shared_mesh4x4_full_tb;
  localparam integer VC0_ADDR_W = 32;
  localparam integer VC0_PACKET_INDEX_W = 7;
  localparam integer VC0_CONTEXTS = 112;
  localparam integer VC0_CONTEXTS_PER_WAVE = 16;
  localparam integer VC0_PACKETS_PER_CONTEXT = 68;
  localparam integer VC0_WORDS_PER_CONTEXT = VC0_PACKETS_PER_CONTEXT * 8;
  localparam integer VC0_TOTAL_PACKETS = VC0_CONTEXTS * VC0_PACKETS_PER_CONTEXT;
  localparam integer VC0_TOTAL_FLITS = VC0_TOTAL_PACKETS * 8;
  localparam integer VC1_BEAT_W = 419;
  localparam integer VC1_SOURCE_COUNT = 15;
  localparam integer VC1_GROUP_BEATS = 128;
  localparam integer VC1_GROUP_PACKETS = 15 * 21;
  localparam integer VC1_GROUP_FLITS = 15 * 167;
  localparam integer VC1_GROUPS = 4;
  localparam integer VC1_TOTAL_PACKETS = VC1_GROUPS * VC1_GROUP_PACKETS;
  localparam integer VC1_TOTAL_FLITS = VC1_GROUPS * VC1_GROUP_FLITS;
  localparam integer VC1_TOTAL_ROWS = VC1_GROUPS * VC1_GROUP_BEATS;
  localparam integer BASE_COMMAND_ID = 16'h6a00;

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

  reg vc0_run_started_q = 1'b0;
  reg [6:0] vc0_event_index_q = 7'd0;
  wire [2:0] vc0_remote_wave_ordinal_w = vc0_event_index_q[6:4];
  wire [3:0] vc0_event_cluster_w = vc0_event_index_q[3:0];
  reg [2:0] vc0_event_wave_w = 3'b0;
  reg [3:0] vc0_event_shift_w = 4'b0;
  wire [3:0] vc0_event_source_w = vc0_event_cluster_w + vc0_event_shift_w;

  reg [15:0] vc0_rsp_pending_q = 16'b0;
  reg [16*256-1:0] vc0_rsp_data_q = 0;
  reg [VC0_WORDS_PER_CONTEXT-1:0] vc0_request_seen [0:VC0_CONTEXTS-1];
  reg [VC0_WORDS_PER_CONTEXT-1:0] vc0_write_seen [0:VC0_CONTEXTS-1];
  reg [31:0] vc0_request_cycle [0:VC0_CONTEXTS-1][0:VC0_WORDS_PER_CONTEXT-1];
  reg [VC0_CONTEXTS-1:0] vc0_context_seen = 0;
  reg [VC0_CONTEXTS-1:0] vc0_completion_seen = 0;
  reg [15:0] vc0_tx_req_held = 16'b0;
  reg [16*VC0_ADDR_W-1:0] vc0_tx_req_hold_addr = 0;
  reg [15:0] vc0_write_held = 16'b0;
  reg [16*VC0_ADDR_W-1:0] vc0_write_hold_addr = 0;
  reg [16*256-1:0] vc0_write_hold_data = 0;
  reg vc0_completion_held = 1'b0;
  reg vc0_completion_stall_seen = 1'b0;
  reg [2:0] vc0_held_completion_wave = 0;
  reg [3:0] vc0_held_completion_destination = 0;

  integer vc1_source_beat_index [0:VC1_SOURCE_COUNT-1];
  integer vc1_root_beat_index = 0;
  integer vc1_group_count_seen = 0;
  integer vc1_active_group_id = 0;
  integer vc1_descriptor_pulse_count = 0;
  integer vc1_group_complete_pulse_count = 0;
  reg [VC1_SOURCE_COUNT-1:0] vc1_descriptor_seen = 0;
  integer vc1_group_complete_count_by_source [0:VC1_SOURCE_COUNT-1];
  integer vc1_root_count = 0;
  reg vc1_stream_active = 1'b0;
  reg vc1_root_stall_observed = 1'b0;
  reg service_envelope_mode = 1'b0;
  reg vc1_all_input_done;
  reg [15:0] stalled_root_command = 0;
  reg [4:0] stalled_root_head = 0;
  reg [3:0] stalled_root_slice = 0;
  reg stalled_root_last = 1'b0;
  reg [319:0] stalled_root_value = 0;

  integer cycle = 0;
  integer vc0_context_count = 0;
  integer vc0_completion_count = 0;
  integer vc0_tx_request_count = 0;
  integer vc0_write_count = 0;
  integer vc0_completion_hold_checks = 0;
  integer overlap_valid_cycles = 0;
  integer overlap_arbitrated_cycles = 0;
  integer overlap_valid_delta = 0;
  integer overlap_arb_delta = 0;
  integer descriptor_delta = 0;
  integer group_complete_delta = 0;
  integer req_delta = 0;
  integer write_delta = 0;
  integer wait_cycles = 0;
  integer vc0_done_cycle = -1;
  integer vc1_done_cycle = -1;
  integer service_done_cycle = -1;
  integer comb_endpoint_i;
  integer comb_source_i;
  integer done_source_i;
  integer req_endpoint_i;
  integer mon_endpoint_i;
  integer mon_source_i;
  integer mon_lane_i;
  integer reset_context_i;
  integer reset_source_i;
  integer final_context_i;
  integer actual_wave_i;
  integer actual_cluster_i;
  integer actual_word_i;
  integer actual_context_i;
  integer temp_error_i;
  integer expected_source_i;
  integer expected_addr_i;
  integer arb_trace_fd = 0;
  integer arb_trace_cycle = 0;
  integer trace_endpoint_i;
  string arb_trace_path;
  reg [255:0] expected_data_q;
  reg [15:0] arb_trace_producer0_valid_mask;
  reg [15:0] arb_trace_producer1_valid_mask;
  reg [15:0] arb_trace_mesh_ready_mask;
  reg [15:0] arb_trace_producer0_ready_mask;
  reg [15:0] arb_trace_producer1_ready_mask;
  reg [15:0] arb_trace_out_valid_mask;
  reg [31:0] arb_trace_out_vc_pack;

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

  function integer shift_for_wave;
    input integer wave;
    begin
      case (wave)
        0: shift_for_wave = 4;
        1: shift_for_wave = 7;
        2: shift_for_wave = 10;
        3: shift_for_wave = 13;
        5: shift_for_wave = 3;
        6: shift_for_wave = 6;
        7: shift_for_wave = 9;
        default: shift_for_wave = -1;
      endcase
    end
  endfunction

  function integer wave_from_ordinal;
    input integer ordinal;
    begin
      case (ordinal)
        0: wave_from_ordinal = 0;
        1: wave_from_ordinal = 1;
        2: wave_from_ordinal = 2;
        3: wave_from_ordinal = 3;
        4: wave_from_ordinal = 5;
        5: wave_from_ordinal = 6;
        default: wave_from_ordinal = 7;
      endcase
    end
  endfunction

  function integer wave_slot;
    input integer wave;
    begin
      case (wave)
        0: wave_slot = 0;
        1: wave_slot = 1;
        2: wave_slot = 2;
        3: wave_slot = 3;
        5: wave_slot = 4;
        6: wave_slot = 5;
        7: wave_slot = 6;
        default: wave_slot = -1;
      endcase
    end
  endfunction

  function integer context_id_from_wave_cluster;
    input integer wave;
    input integer cluster;
    integer slot;
    begin
      slot = wave_slot(wave);
      if (slot < 0 || cluster < 0 || cluster >= 16)
        context_id_from_wave_cluster = -1;
      else
        context_id_from_wave_cluster = slot * VC0_CONTEXTS_PER_WAVE + cluster;
    end
  endfunction

  function [VC0_ADDR_W-1:0] vc0_source_base;
    input integer wave;
    input integer cluster;
    begin
      vc0_source_base =
        32'h0100_0000 + wave * 32'h0010_0000 + cluster * 32'h0001_0000;
    end
  endfunction

  function [VC0_ADDR_W-1:0] vc0_destination_base;
    input integer wave;
    input integer cluster;
    begin
      vc0_destination_base =
        32'h0200_0000 + wave * 32'h0010_0000 + cluster * 32'h0001_0000;
    end
  endfunction

  function integer vc0_expected_source;
    input integer wave;
    input integer cluster;
    integer shift_value;
    begin
      shift_value = shift_for_wave(wave);
      if (shift_value < 0)
        vc0_expected_source = -1;
      else
        vc0_expected_source = (cluster + shift_value) & 15;
    end
  endfunction

  function [255:0] response_word;
    input integer endpoint;
    input [VC0_ADDR_W-1:0] address;
    input integer salt;
    integer repeated;
    begin
      repeated = salt ^ (endpoint << 4);
      response_word = {
        address ^ salt,
        {4{repeated[31:0]}},
        address,
        salt[31:0],
        {8{endpoint[3:0]}}
      };
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

  task decode_source_addr;
    input [VC0_ADDR_W-1:0] address;
    output integer wave;
    output integer cluster;
    output integer word;
    output integer context_id;
    output integer error;
    integer local_offset;
    begin
      wave = -1;
      cluster = -1;
      word = -1;
      context_id = -1;
      error = 0;
      if (address < 32'h0100_0000) begin
        error = 1;
      end else begin
        local_offset = address - 32'h0100_0000;
        wave = local_offset / 32'h0010_0000;
        local_offset = local_offset % 32'h0010_0000;
        cluster = local_offset / 32'h0001_0000;
        local_offset = local_offset % 32'h0001_0000;
        if ((local_offset % 32) != 0)
          error = 1;
        word = local_offset / 32;
        context_id = context_id_from_wave_cluster(wave, cluster);
        if (context_id < 0 || word < 0 || word >= VC0_WORDS_PER_CONTEXT)
          error = 1;
      end
    end
  endtask

  task decode_destination_addr;
    input [VC0_ADDR_W-1:0] address;
    output integer wave;
    output integer cluster;
    output integer word;
    output integer context_id;
    output integer error;
    integer local_offset;
    begin
      wave = -1;
      cluster = -1;
      word = -1;
      context_id = -1;
      error = 0;
      if (address < 32'h0200_0000) begin
        error = 1;
      end else begin
        local_offset = address - 32'h0200_0000;
        wave = local_offset / 32'h0010_0000;
        local_offset = local_offset % 32'h0010_0000;
        cluster = local_offset / 32'h0001_0000;
        local_offset = local_offset % 32'h0001_0000;
        if ((local_offset % 32) != 0)
          error = 1;
        word = local_offset / 32;
        context_id = context_id_from_wave_cluster(wave, cluster);
        if (context_id < 0 || word < 0 || word >= VC0_WORDS_PER_CONTEXT)
          error = 1;
      end
    end
  endtask

  always @(*) begin
    vc0_event_wave_w = wave_from_ordinal(vc0_remote_wave_ordinal_w);
    vc0_event_shift_w = shift_for_wave(vc0_event_wave_w);

    vc0_event_valid = 16'b0;
    vc0_event_wave = 0;
    vc0_event_source = 0;
    vc0_event_source_base_addr = 0;
    vc0_event_destination_base_addr = 0;
    vc0_event_packet_count = 0;
    if (rst_n && vc0_run_started_q && !vc0_layer_start &&
        vc0_event_index_q < VC0_CONTEXTS) begin
      vc0_event_valid[vc0_event_cluster_w] = 1'b1;
      vc0_event_wave[(vc0_event_cluster_w*3) +: 3] = vc0_event_wave_w;
      vc0_event_source[(vc0_event_cluster_w*4) +: 4] = vc0_event_source_w;
      vc0_event_source_base_addr[(vc0_event_cluster_w*VC0_ADDR_W) +: VC0_ADDR_W] =
        vc0_source_base(vc0_event_wave_w, vc0_event_cluster_w);
      vc0_event_destination_base_addr[(vc0_event_cluster_w*VC0_ADDR_W) +: VC0_ADDR_W] =
        vc0_destination_base(vc0_event_wave_w, vc0_event_cluster_w);
      vc0_event_packet_count[
        (vc0_event_cluster_w*(VC0_PACKET_INDEX_W+1)) +:
        (VC0_PACKET_INDEX_W+1)
      ] = VC0_PACKETS_PER_CONTEXT;
    end

    vc0_tx_mem_req_ready = 16'b0;
    vc0_tx_mem_rsp_valid = vc0_rsp_pending_q;
    vc0_tx_mem_rsp_data = vc0_rsp_data_q;
    vc0_rx_mem_write_ready = 16'b0;
    for (comb_endpoint_i = 0; comb_endpoint_i < 16; comb_endpoint_i = comb_endpoint_i + 1) begin
      vc0_tx_mem_req_ready[comb_endpoint_i] =
        !vc0_rsp_pending_q[comb_endpoint_i] &&
        (service_envelope_mode || (((cycle & 7) ^ (comb_endpoint_i & 7)) != 0));
      vc0_rx_mem_write_ready[comb_endpoint_i] = service_envelope_mode ||
        ((((cycle & 15) + comb_endpoint_i) & 15) != 0);
    end
    vc0_completion_ready = service_envelope_mode ||
      (vc0_completion_stall_seen &&
       ((cycle % 17) != 5) && ((cycle % 23) != 7));
    vc1_root_ready = service_envelope_mode ||
      (((cycle % 11) != 3) && ((cycle % 17) != 5));
  end

  always @(*) begin
    vc1_source_beat_valid = {VC1_SOURCE_COUNT{1'b0}};
    vc1_source_beat_data = {(VC1_SOURCE_COUNT*VC1_BEAT_W){1'b0}};
    vc1_root_local_beat_valid = 1'b0;
    vc1_root_local_beat_data = {VC1_BEAT_W{1'b0}};
    if (vc1_stream_active) begin
      for (comb_source_i = 0; comb_source_i < VC1_SOURCE_COUNT; comb_source_i = comb_source_i + 1) begin
        vc1_source_beat_valid[comb_source_i] =
          (vc1_source_beat_index[comb_source_i] < VC1_GROUP_BEATS);
        vc1_source_beat_data[comb_source_i*VC1_BEAT_W +: VC1_BEAT_W] =
          make_canonical_beat(vc1_active_group_id, vc1_source_beat_index[comb_source_i]);
      end
      vc1_root_local_beat_valid = (vc1_root_beat_index < VC1_GROUP_BEATS);
      vc1_root_local_beat_data =
        make_canonical_beat(vc1_active_group_id, vc1_root_beat_index);
    end
  end

  always @(*) begin
    vc1_all_input_done = (vc1_root_beat_index >= VC1_GROUP_BEATS);
    for (done_source_i = 0; done_source_i < VC1_SOURCE_COUNT; done_source_i = done_source_i + 1)
      if (vc1_source_beat_index[done_source_i] < VC1_GROUP_BEATS)
        vc1_all_input_done = 1'b0;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      vc0_layer_start <= 1'b0;
      vc0_run_started_q <= 1'b0;
      vc0_event_index_q <= 7'd0;
      vc0_rsp_pending_q <= 16'b0;
      vc0_rsp_data_q <= 0;
      vc0_tx_request_count <= 0;
    end else begin
      cycle <= cycle + 1;
      vc0_layer_start <= 1'b0;
      if (!vc0_run_started_q) begin
        vc0_layer_start <= 1'b1;
        vc0_run_started_q <= 1'b1;
        vc0_event_index_q <= 7'd0;
      end else if (vc0_event_index_q < VC0_CONTEXTS &&
                   vc0_event_valid[vc0_event_cluster_w] &&
                   vc0_event_ready[vc0_event_cluster_w]) begin
        vc0_event_index_q <= vc0_event_index_q + 1'b1;
      end

      req_delta = 0;
      for (req_endpoint_i = 0; req_endpoint_i < 16; req_endpoint_i = req_endpoint_i + 1) begin
        if (vc0_rsp_pending_q[req_endpoint_i]) begin
          if (vc0_tx_mem_rsp_ready[req_endpoint_i])
            vc0_rsp_pending_q[req_endpoint_i] <= 1'b0;
        end else if (vc0_tx_mem_req_valid[req_endpoint_i] &&
                     vc0_tx_mem_req_ready[req_endpoint_i]) begin
          decode_source_addr(
            vc0_tx_mem_req_addr[(req_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W],
            actual_wave_i,
            actual_cluster_i,
            actual_word_i,
            actual_context_i,
            temp_error_i
          );
          if (temp_error_i)
            $fatal(1, "vc0 request address decode failed endpoint=%0d addr=%h",
              req_endpoint_i, vc0_tx_mem_req_addr[(req_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W]);
          expected_source_i = vc0_expected_source(actual_wave_i, actual_cluster_i);
          if (req_endpoint_i != expected_source_i)
            $fatal(1, "vc0 source endpoint mismatch endpoint=%0d expected=%0d wave=%0d cluster=%0d",
              req_endpoint_i, expected_source_i, actual_wave_i, actual_cluster_i);
          if (vc0_request_seen[actual_context_i][actual_word_i])
            $fatal(1, "duplicate vc0 source request context=%0d word=%0d",
              actual_context_i, actual_word_i);
          vc0_request_seen[actual_context_i][actual_word_i] <= 1'b1;
          vc0_request_cycle[actual_context_i][actual_word_i] <= cycle;
          vc0_rsp_pending_q[req_endpoint_i] <= 1'b1;
          vc0_rsp_data_q[(req_endpoint_i*256) +: 256] <= response_word(
            req_endpoint_i,
            vc0_tx_mem_req_addr[(req_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W],
            cycle
          );
          req_delta = req_delta + 1;
        end
      end
      vc0_tx_request_count <= vc0_tx_request_count + req_delta;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      arb_trace_cycle <= 0;
    end else if (arb_trace_fd != 0) begin
      arb_trace_producer0_valid_mask = 16'b0;
      arb_trace_producer1_valid_mask = 16'b0;
      arb_trace_mesh_ready_mask = 16'b0;
      arb_trace_producer0_ready_mask = 16'b0;
      arb_trace_producer1_ready_mask = 16'b0;
      arb_trace_out_valid_mask = 16'b0;
      arb_trace_out_vc_pack = 32'b0;
      for (trace_endpoint_i = 0; trace_endpoint_i < 16; trace_endpoint_i = trace_endpoint_i + 1) begin
        arb_trace_producer0_valid_mask[trace_endpoint_i] =
          dut.vc0_transport_in_valid_w[trace_endpoint_i];
        arb_trace_producer1_valid_mask[trace_endpoint_i] =
          dut.vc1_transport_in_valid_w[trace_endpoint_i];
        arb_trace_mesh_ready_mask[trace_endpoint_i] =
          dut.shared_transport.mesh_endpoint_in_ready_w[trace_endpoint_i];
        arb_trace_producer0_ready_mask[trace_endpoint_i] =
          dut.vc0_transport_in_ready_w[trace_endpoint_i];
        arb_trace_producer1_ready_mask[trace_endpoint_i] =
          dut.vc1_transport_in_ready_w[trace_endpoint_i];
        arb_trace_out_valid_mask[trace_endpoint_i] =
          dut.shared_transport.mesh_endpoint_in_valid_w[trace_endpoint_i];
        arb_trace_out_vc_pack[(trace_endpoint_i * 2) +: 2] =
          dut.shared_transport.mesh_endpoint_in_valid_w[trace_endpoint_i] ?
            dut.shared_transport.mesh_endpoint_in_vc_w[(trace_endpoint_i * 2) +: 2] :
            2'b0;
      end
      $fdisplay(arb_trace_fd, "ARB %0d %04h %04h %04h %04h %04h %04h %08h",
        arb_trace_cycle,
        arb_trace_producer0_valid_mask,
        arb_trace_producer1_valid_mask,
        arb_trace_mesh_ready_mask,
        arb_trace_producer0_ready_mask,
        arb_trace_producer1_ready_mask,
        arb_trace_out_valid_mask,
        arb_trace_out_vc_pack);
      arb_trace_cycle <= arb_trace_cycle + 1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      vc0_context_count <= 0;
      vc0_completion_count <= 0;
      vc0_write_count <= 0;
      vc0_context_seen <= 0;
      vc0_completion_seen <= 0;
      vc0_completion_held <= 1'b0;
      vc0_completion_stall_seen <= 1'b0;
      vc0_held_completion_wave <= 0;
      vc0_held_completion_destination <= 0;
      vc0_completion_hold_checks <= 0;
      vc0_tx_req_held <= 16'b0;
      vc0_tx_req_hold_addr <= 0;
      vc0_write_held <= 16'b0;
      vc0_write_hold_addr <= 0;
      vc0_write_hold_data <= 0;

      vc1_group_count_seen <= 0;
      vc1_active_group_id <= 0;
      vc1_descriptor_pulse_count <= 0;
      vc1_group_complete_pulse_count <= 0;
      vc1_descriptor_seen <= 0;
      vc1_root_count <= 0;
      vc1_stream_active <= 1'b0;
      vc1_root_beat_index <= 0;
      vc1_root_stall_observed <= 1'b0;
      stalled_root_command <= 0;
      stalled_root_head <= 0;
      stalled_root_slice <= 0;
      stalled_root_last <= 1'b0;
      stalled_root_value <= 0;

      overlap_valid_cycles <= 0;
      overlap_arbitrated_cycles <= 0;
      wait_cycles <= 0;
      vc0_done_cycle <= -1;
      vc1_done_cycle <= -1;
      service_done_cycle <= -1;

      for (reset_context_i = 0; reset_context_i < VC0_CONTEXTS; reset_context_i = reset_context_i + 1) begin
        vc0_request_seen[reset_context_i] <= 0;
        vc0_write_seen[reset_context_i] <= 0;
      end
      for (reset_source_i = 0; reset_source_i < VC1_SOURCE_COUNT; reset_source_i = reset_source_i + 1) begin
        vc1_source_beat_index[reset_source_i] <= 0;
        vc1_group_complete_count_by_source[reset_source_i] <= 0;
      end
    end else begin
      overlap_valid_delta = 0;
      overlap_arb_delta = 0;
      descriptor_delta = 0;
      group_complete_delta = 0;
      write_delta = 0;

      if (vc1_group_admission_pulse) begin
        if (vc1_group_index !== vc1_group_count_seen[1:0] ||
            vc1_head_base !== vc1_group_count_seen * 8 ||
            vc1_group_epoch !== vc1_group_count_seen[2:0] ||
            vc1_source_producer_accept !== {VC1_SOURCE_COUNT{1'b1}} ||
            !vc1_root_producer_accept ||
            vc1_source_ctx_valid !== {VC1_SOURCE_COUNT{1'b1}} ||
            !vc1_root_ctx_valid)
          $fatal(1, "vc1 admission metadata mismatch group=%0d", vc1_group_count_seen);
        vc1_group_count_seen <= vc1_group_count_seen + 1;
        vc1_active_group_id <= vc1_group_index;
        vc1_stream_active <= 1'b1;
        vc1_remote_group_ready <= {VC1_SOURCE_COUNT{1'b0}};
        vc1_root_local_group_ready <= 1'b0;
        vc1_root_beat_index <= 0;
        for (mon_source_i = 0; mon_source_i < VC1_SOURCE_COUNT; mon_source_i = mon_source_i + 1)
          vc1_source_beat_index[mon_source_i] <= 0;
      end else begin
        if (vc1_all_input_done && vc1_stream_active &&
            vc1_group_count_seen < VC1_GROUPS) begin
          vc1_remote_group_ready <= {VC1_SOURCE_COUNT{1'b1}};
          vc1_root_local_group_ready <= 1'b1;
        end
        if (vc1_root_local_beat_valid && vc1_root_local_beat_ready)
          vc1_root_beat_index <= vc1_root_beat_index + 1;
        for (mon_source_i = 0; mon_source_i < VC1_SOURCE_COUNT; mon_source_i = mon_source_i + 1)
          if (vc1_source_beat_valid[mon_source_i] && vc1_source_beat_ready[mon_source_i])
            vc1_source_beat_index[mon_source_i] <= vc1_source_beat_index[mon_source_i] + 1;
      end

      for (mon_endpoint_i = 0; mon_endpoint_i < 16; mon_endpoint_i = mon_endpoint_i + 1) begin
        if (dut.vc0_transport_in_valid_w[mon_endpoint_i] &&
            dut.vc1_transport_in_valid_w[mon_endpoint_i]) begin
          overlap_valid_delta = overlap_valid_delta + 1;
          if (dut.vc0_transport_in_ready_w[mon_endpoint_i] ^
              dut.vc1_transport_in_ready_w[mon_endpoint_i])
            overlap_arb_delta = overlap_arb_delta + 1;
        end

        if (vc0_tx_req_held[mon_endpoint_i]) begin
          if (!vc0_tx_mem_req_valid[mon_endpoint_i] ||
              vc0_tx_mem_req_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] !==
              vc0_tx_req_hold_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W])
            $fatal(1, "vc0 tx request changed under stall endpoint=%0d", mon_endpoint_i);
        end
        if (vc0_tx_mem_req_valid[mon_endpoint_i] && !vc0_tx_mem_req_ready[mon_endpoint_i]) begin
          vc0_tx_req_held[mon_endpoint_i] <= 1'b1;
          vc0_tx_req_hold_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] <=
            vc0_tx_mem_req_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W];
        end else begin
          vc0_tx_req_held[mon_endpoint_i] <= 1'b0;
        end

        if (vc0_write_held[mon_endpoint_i]) begin
          if (!vc0_rx_mem_write_valid[mon_endpoint_i] ||
              vc0_rx_mem_write_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] !==
              vc0_write_hold_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] ||
              vc0_rx_mem_write_data[(mon_endpoint_i*256) +: 256] !==
              vc0_write_hold_data[(mon_endpoint_i*256) +: 256])
            $fatal(1, "vc0 write changed under stall endpoint=%0d", mon_endpoint_i);
        end
        if (vc0_rx_mem_write_valid[mon_endpoint_i] && !vc0_rx_mem_write_ready[mon_endpoint_i]) begin
          vc0_write_held[mon_endpoint_i] <= 1'b1;
          vc0_write_hold_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W] <=
            vc0_rx_mem_write_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W];
          vc0_write_hold_data[(mon_endpoint_i*256) +: 256] <=
            vc0_rx_mem_write_data[(mon_endpoint_i*256) +: 256];
        end else begin
          vc0_write_held[mon_endpoint_i] <= 1'b0;
        end
      end

      for (mon_source_i = 0; mon_source_i < VC1_SOURCE_COUNT; mon_source_i = mon_source_i + 1) begin
        if (vc1_descriptor_installed[mon_source_i]) begin
          vc1_descriptor_seen[mon_source_i] <= 1'b1;
          descriptor_delta = descriptor_delta + 1;
        end
        if (vc1_group_complete[mon_source_i]) begin
          vc1_group_complete_count_by_source[mon_source_i] <=
            vc1_group_complete_count_by_source[mon_source_i] + 1;
          group_complete_delta = group_complete_delta + 1;
        end
      end
      overlap_valid_cycles <= overlap_valid_cycles + overlap_valid_delta;
      overlap_arbitrated_cycles <= overlap_arbitrated_cycles + overlap_arb_delta;
      vc1_descriptor_pulse_count <= vc1_descriptor_pulse_count + descriptor_delta;
      vc1_group_complete_pulse_count <= vc1_group_complete_pulse_count + group_complete_delta;

      if (vc0_context_valid && vc0_context_ready) begin
        actual_context_i = context_id_from_wave_cluster(
          vc0_context_wave,
          vc0_context_destination
        );
        if (actual_context_i < 0 || vc0_context_seen[actual_context_i])
          $fatal(1, "unexpected/duplicate vc0 context wave=%0d destination=%0d",
            vc0_context_wave, vc0_context_destination);
        expected_source_i = vc0_expected_source(
          vc0_context_wave,
          vc0_context_destination
        );
        if (vc0_context_source !== expected_source_i[3:0] ||
            vc0_context_source_base_addr !==
              vc0_source_base(vc0_context_wave, vc0_context_destination) ||
            vc0_context_destination_base_addr !==
              vc0_destination_base(vc0_context_wave, vc0_context_destination) ||
            vc0_context_packet_count !== VC0_PACKETS_PER_CONTEXT)
          $fatal(1, "vc0 context metadata mismatch wave=%0d destination=%0d source=%0d expected_source=%0d",
            vc0_context_wave, vc0_context_destination, vc0_context_source,
            expected_source_i);
        vc0_context_seen[actual_context_i] <= 1'b1;
        vc0_context_count <= vc0_context_count + 1;
      end

      if (vc0_completion_valid && !vc0_completion_ready) begin
        vc0_completion_stall_seen <= 1'b1;
        if (vc0_completion_held) begin
          if (vc0_completion_wave !== vc0_held_completion_wave ||
              vc0_completion_destination !== vc0_held_completion_destination)
            $fatal(1, "vc0 completion changed under backpressure");
          vc0_completion_hold_checks <= vc0_completion_hold_checks + 1;
        end else begin
          vc0_completion_held <= 1'b1;
          vc0_held_completion_wave <= vc0_completion_wave;
          vc0_held_completion_destination <= vc0_completion_destination;
        end
      end else begin
        vc0_completion_held <= 1'b0;
      end

      if (vc0_completion_valid && vc0_completion_ready) begin
        actual_context_i = context_id_from_wave_cluster(
          vc0_completion_wave,
          vc0_completion_destination
        );
        if (actual_context_i < 0 || vc0_completion_seen[actual_context_i])
          $fatal(1, "unexpected/duplicate vc0 completion wave=%0d destination=%0d",
            vc0_completion_wave, vc0_completion_destination);
        vc0_completion_seen[actual_context_i] <= 1'b1;
        vc0_completion_count <= vc0_completion_count + 1;
      end

      for (mon_endpoint_i = 0; mon_endpoint_i < 16; mon_endpoint_i = mon_endpoint_i + 1) begin
        if (vc0_rx_mem_write_valid[mon_endpoint_i] &&
            vc0_rx_mem_write_ready[mon_endpoint_i]) begin
          decode_destination_addr(
            vc0_rx_mem_write_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W],
            actual_wave_i,
            actual_cluster_i,
            actual_word_i,
            actual_context_i,
            temp_error_i
          );
          if (temp_error_i || mon_endpoint_i != actual_cluster_i)
            $fatal(1, "vc0 write address decode failed endpoint=%0d addr=%h",
              mon_endpoint_i, vc0_rx_mem_write_addr[(mon_endpoint_i*VC0_ADDR_W) +: VC0_ADDR_W]);
          if (vc0_write_seen[actual_context_i][actual_word_i])
            $fatal(1, "duplicate vc0 write context=%0d word=%0d",
              actual_context_i, actual_word_i);
          if (!vc0_request_seen[actual_context_i][actual_word_i])
            $fatal(1, "vc0 write observed before source request context=%0d word=%0d",
              actual_context_i, actual_word_i);
          expected_source_i = vc0_expected_source(actual_wave_i, actual_cluster_i);
          expected_addr_i =
            vc0_source_base(actual_wave_i, actual_cluster_i) + actual_word_i * 32;
          expected_data_q = response_word(
            expected_source_i,
            expected_addr_i[VC0_ADDR_W-1:0],
            vc0_request_cycle[actual_context_i][actual_word_i]
          );
          if (vc0_rx_mem_write_data[(mon_endpoint_i*256) +: 256] !== expected_data_q)
            $fatal(1, "vc0 payload mismatch context=%0d word=%0d endpoint=%0d",
              actual_context_i, actual_word_i, mon_endpoint_i);
          vc0_write_seen[actual_context_i][actual_word_i] <= 1'b1;
          write_delta = write_delta + 1;
        end
      end
      vc0_write_count <= vc0_write_count + write_delta;

      if (vc1_root_valid && !vc1_root_ready) begin
        if (!vc1_root_stall_observed) begin
          stalled_root_command <= vc1_root_command_id;
          stalled_root_head <= vc1_root_head_id;
          stalled_root_slice <= vc1_root_slice;
          stalled_root_last <= vc1_root_last;
          stalled_root_value <= vc1_root_value;
          vc1_root_stall_observed <= 1'b1;
        end else if (vc1_root_command_id !== stalled_root_command ||
                     vc1_root_head_id !== stalled_root_head ||
                     vc1_root_slice !== stalled_root_slice ||
                     vc1_root_last !== stalled_root_last ||
                     vc1_root_value !== stalled_root_value) begin
          $fatal(1, "vc1 root output changed under backpressure");
        end
      end else begin
        vc1_root_stall_observed <= 1'b0;
      end

      if (vc1_root_valid && vc1_root_ready) begin
        if (vc1_root_command_id !== BASE_COMMAND_ID + (vc1_root_count / VC1_GROUP_BEATS) ||
            vc1_root_head_id !== ((vc1_root_count / 16) % 8) +
              ((vc1_root_count / VC1_GROUP_BEATS) * 8) ||
            vc1_root_slice !== (vc1_root_count % 16) ||
            vc1_root_last !== ((vc1_root_count % 16) == 15))
          $fatal(1, "vc1 root metadata mismatch row=%0d cmd=%h head=%0d slice=%0d last=%0d",
            vc1_root_count, vc1_root_command_id, vc1_root_head_id,
            vc1_root_slice, vc1_root_last);
        for (mon_lane_i = 0; mon_lane_i < 8; mon_lane_i = mon_lane_i + 1)
          if (vc1_root_value[mon_lane_i*40 +: 40] !== 40'h0ffff)
            $fatal(1, "vc1 root canonical mismatch row=%0d lane=%0d value=%h",
              vc1_root_count, mon_lane_i, vc1_root_value[mon_lane_i*40 +: 40]);
        vc1_root_count <= vc1_root_count + 1;
      end

      if (protocol_error || vc0_protocol_error || vc1_protocol_error ||
          vc1_tree_protocol_error || shared_transport_protocol_error ||
          (|vc0_endpoint_protocol_error) || (|vc1_source_protocol_error) ||
          (|shared_injection_protocol_error) || (|shared_ejection_protocol_error))
        $fatal(1, "protocol error top=%0d vc0=%0d vc1=%0d tree=%0d shared=%0d vc0_ep=%h vc1_src=%h inj=%h ej=%h",
          protocol_error, vc0_protocol_error, vc1_protocol_error,
          vc1_tree_protocol_error, shared_transport_protocol_error,
          vc0_endpoint_protocol_error, vc1_source_protocol_error,
          shared_injection_protocol_error, shared_ejection_protocol_error);

      if (vc0_transport_complete && vc0_done_cycle < 0)
        vc0_done_cycle <= cycle;
      if (vc1_done && vc1_done_cycle < 0)
        vc1_done_cycle <= cycle;
      if (vc0_transport_complete && vc1_done && service_done_cycle < 0)
        service_done_cycle <= cycle;

      if (vc0_transport_complete &&
          vc1_done &&
          vc1_root_count == VC1_TOTAL_ROWS &&
          vc1_source_tx_descriptor_count == VC1_TOTAL_PACKETS &&
          vc1_root_completion_count == VC1_TOTAL_PACKETS)
        wait_cycles <= wait_cycles + 1;
      else
        wait_cycles <= 0;

      if (wait_cycles == 4) begin
        if (!vc0_admission_complete ||
            vc0_event_index_q !== VC0_CONTEXTS ||
            vc0_admitted_count !== VC0_CONTEXTS ||
            vc0_completed_count !== VC0_CONTEXTS ||
            vc0_context_count !== VC0_CONTEXTS ||
            vc0_completion_count !== VC0_CONTEXTS ||
            vc0_context_seen !== {VC0_CONTEXTS{1'b1}} ||
            vc0_completion_seen !== {VC0_CONTEXTS{1'b1}} ||
            vc0_tx_request_count !== VC0_TOTAL_FLITS ||
            vc0_write_count !== VC0_TOTAL_FLITS ||
            (!service_envelope_mode && vc0_completion_hold_checks == 0))
          $fatal(1, "vc0 totals mismatch event=%0d admitted=%0d completed=%0d contexts=%0d completions=%0d requests=%0d writes=%0d holds=%0d",
            vc0_event_index_q, vc0_admitted_count, vc0_completed_count,
            vc0_context_count, vc0_completion_count, vc0_tx_request_count,
            vc0_write_count, vc0_completion_hold_checks);
        for (final_context_i = 0; final_context_i < VC0_CONTEXTS; final_context_i = final_context_i + 1) begin
          if (vc0_request_seen[final_context_i] !== {VC0_WORDS_PER_CONTEXT{1'b1}})
            $fatal(1, "missing vc0 source requests context=%0d", final_context_i);
          if (vc0_write_seen[final_context_i] !== {VC0_WORDS_PER_CONTEXT{1'b1}})
            $fatal(1, "missing vc0 writes context=%0d", final_context_i);
        end

        if (vc1_group_count_seen !== VC1_GROUPS ||
            vc1_admitted_group_count !== VC1_GROUPS ||
            !vc1_done ||
            vc1_root_count !== VC1_TOTAL_ROWS ||
            vc1_descriptor_seen !== {VC1_SOURCE_COUNT{1'b1}} ||
            vc1_descriptor_pulse_count !== VC1_TOTAL_PACKETS ||
            vc1_group_complete_pulse_count !== VC1_GROUPS * VC1_SOURCE_COUNT ||
            vc1_source_tx_descriptor_count !== VC1_TOTAL_PACKETS ||
            vc1_root_accepted_flit_count !== VC1_TOTAL_FLITS ||
            vc1_root_descriptor_install_count !== VC1_TOTAL_PACKETS ||
            vc1_root_completion_count !== VC1_TOTAL_PACKETS ||
            vc1_root_replay_packet_count !== VC1_TOTAL_PACKETS)
          $fatal(1, "vc1 totals mismatch groups=%0d admitted=%0d done=%0d rows=%0d desc_pulses=%0d complete_pulses=%0d txdesc=%0d flits=%0d installs=%0d completions=%0d replay=%0d",
            vc1_group_count_seen, vc1_admitted_group_count, vc1_done,
            vc1_root_count, vc1_descriptor_pulse_count,
            vc1_group_complete_pulse_count, vc1_source_tx_descriptor_count,
            vc1_root_accepted_flit_count, vc1_root_descriptor_install_count,
            vc1_root_completion_count, vc1_root_replay_packet_count);
        for (mon_source_i = 0; mon_source_i < VC1_SOURCE_COUNT; mon_source_i = mon_source_i + 1) begin
          if (vc1_source_tx_descriptor_counts[mon_source_i*32 +: 32] !==
              VC1_GROUPS * 21)
            $fatal(1, "vc1 source descriptor count mismatch source=%0d count=%0d",
              mon_source_i, vc1_source_tx_descriptor_counts[mon_source_i*32 +: 32]);
          if (vc1_group_complete_count_by_source[mon_source_i] !== VC1_GROUPS)
            $fatal(1, "vc1 group completion count mismatch source=%0d count=%0d",
              mon_source_i, vc1_group_complete_count_by_source[mon_source_i]);
        end

        if (overlap_valid_cycles == 0 || overlap_arbitrated_cycles == 0 ||
            shared_contention_cycles == 0 || shared_input_stall_cycles == 0 ||
            shared_output_stall_cycles == 0)
          $fatal(1, "shared overlap/contention missing overlap_valid=%0d overlap_arb=%0d contention=%0d in_stall=%0d out_stall=%0d",
            overlap_valid_cycles, overlap_arbitrated_cycles,
            shared_contention_cycles, shared_input_stall_cycles,
            shared_output_stall_cycles);

        $display("PASS exact_dual_producer_shared_mesh_full vc0_contexts=%0d vc0_packets=%0d vc0_flits=%0d vc1_groups=%0d vc1_rows=%0d vc1_packets=%0d vc1_flits=%0d overlap_valid=%0d overlap_arb=%0d contention=%0d service_envelope=%0d service_cycles=%0d vc0_done_cycle=%0d vc1_done_cycle=%0d",
          vc0_context_count, VC0_TOTAL_PACKETS, vc0_write_count,
          vc1_group_count_seen, vc1_root_count, vc1_source_tx_descriptor_count,
          vc1_root_accepted_flit_count, overlap_valid_cycles,
          overlap_arbitrated_cycles, shared_contention_cycles,
          service_envelope_mode, service_done_cycle, vc0_done_cycle,
          vc1_done_cycle);
        $finish;
      end

      if (cycle > 300000) begin
        $fatal(1, "full shared-mesh timeout cycle=%0d vc0_contexts=%0d vc0_completions=%0d vc0_writes=%0d vc1_groups=%0d vc1_rows=%0d vc1_packets=%0d vc1_done=%0d",
          cycle, vc0_context_count, vc0_completion_count, vc0_write_count,
          vc1_group_count_seen, vc1_root_count, vc1_source_tx_descriptor_count,
          vc1_done);
      end
    end
  end

  initial begin
    service_envelope_mode = $test$plusargs("SERVICE_ENVELOPE");
    if ($value$plusargs("ARB_TRACE=%s", arb_trace_path)) begin
      arb_trace_fd = $fopen(arb_trace_path, "w");
      if (arb_trace_fd == 0)
        $fatal(1, "failed to open ARB_TRACE=%0s", arb_trace_path);
    end
    vc1_remote_group_ready = {VC1_SOURCE_COUNT{1'b1}};
    vc1_root_local_group_ready = 1'b1;
    for (reset_source_i = 0; reset_source_i < VC1_SOURCE_COUNT; reset_source_i = reset_source_i + 1) begin
      vc1_source_beat_index[reset_source_i] = 0;
      vc1_group_complete_count_by_source[reset_source_i] = 0;
    end
    for (reset_context_i = 0; reset_context_i < VC0_CONTEXTS; reset_context_i = reset_context_i + 1) begin
      vc0_request_seen[reset_context_i] = 0;
      vc0_write_seen[reset_context_i] = 0;
    end
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
