`timescale 1ns/1ps

// Compact-pin activity harness for the complete VC0 shared-SRAM service.
// Producer/memory stimulus is intentionally outside the `service` hierarchy
// so hierarchical reports can separate the reusable DUT from harness logic.
module attention_shared_stream_context_service_ppa_activity_harness (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [31:0] control,
  output wire [127:0] observable
);
  localparam integer ADDR_W = 32;
  localparam integer PACKET_INDEX_W = 7;
  localparam integer REMOTE_CONTEXTS = 112;

  reg layer_start_q;
  reg run_started_q;
  reg [6:0] event_index_q;
  wire [2:0] remote_wave_ordinal = event_index_q[6:4];
  wire [3:0] event_cluster_w = event_index_q[3:0];
  reg [2:0] event_wave_w;
  reg [3:0] event_shift_w;
  wire [3:0] event_source_w = event_cluster_w + event_shift_w;

  reg [15:0] event_valid_w;
  wire [15:0] event_ready_w;
  reg [16*3-1:0] event_wave_bus_w;
  reg [16*4-1:0] event_source_bus_w;
  reg [16*ADDR_W-1:0] event_source_base_w;
  reg [16*ADDR_W-1:0] event_destination_base_w;
  reg [16*(PACKET_INDEX_W+1)-1:0] event_packet_count_w;

  wire completion_valid_w;
  wire [2:0] completion_wave_w;
  wire [3:0] completion_destination_w;
  wire [15:0] tx_mem_req_valid_w;
  reg [15:0] tx_mem_req_ready_w;
  wire [16*ADDR_W-1:0] tx_mem_req_addr_w;
  reg [15:0] tx_mem_rsp_valid_w;
  wire [15:0] tx_mem_rsp_ready_w;
  reg [16*256-1:0] tx_mem_rsp_data_w;
  wire [15:0] rx_mem_write_valid_w;
  reg [15:0] rx_mem_write_ready_w;
  wire [16*ADDR_W-1:0] rx_mem_write_addr_w;
  wire [16*256-1:0] rx_mem_write_data_w;
  wire context_valid_w;
  wire context_ready_w;
  wire [2:0] context_wave_w;
  wire [3:0] context_destination_w;
  wire [3:0] context_source_w;
  wire [ADDR_W-1:0] context_source_base_w;
  wire [ADDR_W-1:0] context_destination_base_w;
  wire [PACKET_INDEX_W:0] context_packet_count_w;
  wire admission_complete_w;
  wire transport_complete_w;
  wire [7:0] admitted_count_w;
  wire [7:0] completed_count_w;
  wire [15:0] endpoint_protocol_error_w;
  wire protocol_error_w;

  reg [15:0] response_pending_q;
  reg [16*256-1:0] response_data_q;
  reg [31:0] cycle_q;
  reg [31:0] accepted_write_count_q;
  reg [127:0] write_fold_q;
  reg [4:0] accepted_write_count_w;
  reg [127:0] accepted_write_fold_w;
  integer comb_lane_i;
  integer seq_lane_i;

  function [255:0] response_word;
    input [3:0] endpoint;
    input [ADDR_W-1:0] address;
    input [31:0] salt;
    begin
      response_word = {
        address ^ salt,
        {4{salt ^ {24'b0, endpoint, 4'b0}}},
        address,
        salt,
        {8{endpoint}}
      };
    end
  endfunction

  always @(*) begin
    case (remote_wave_ordinal)
      3'd0: begin event_wave_w = 3'd0; event_shift_w = 4'd4; end
      3'd1: begin event_wave_w = 3'd1; event_shift_w = 4'd7; end
      3'd2: begin event_wave_w = 3'd2; event_shift_w = 4'd10; end
      3'd3: begin event_wave_w = 3'd3; event_shift_w = 4'd13; end
      3'd4: begin event_wave_w = 3'd5; event_shift_w = 4'd3; end
      3'd5: begin event_wave_w = 3'd6; event_shift_w = 4'd6; end
      default: begin event_wave_w = 3'd7; event_shift_w = 4'd9; end
    endcase

    event_valid_w = 16'b0;
    event_wave_bus_w = 0;
    event_source_bus_w = 0;
    event_source_base_w = 0;
    event_destination_base_w = 0;
    event_packet_count_w = 0;
    // Admission samples layer_start on an edge. Hold residency events for one
    // additional cycle so they are first presented after layer_active is set.
    if (enable && run_started_q && !layer_start_q &&
        event_index_q < REMOTE_CONTEXTS) begin
      event_valid_w[event_cluster_w] = 1'b1;
      event_wave_bus_w[(event_cluster_w*3) +: 3] = event_wave_w;
      event_source_bus_w[(event_cluster_w*4) +: 4] = event_source_w;
      event_source_base_w[(event_cluster_w*ADDR_W) +: ADDR_W] =
        32'h0100_0000 + (event_wave_w * 32'h0010_0000) +
        (event_cluster_w * 32'h0001_0000);
      event_destination_base_w[(event_cluster_w*ADDR_W) +: ADDR_W] =
        32'h0200_0000 + (event_wave_w * 32'h0010_0000) +
        (event_cluster_w * 32'h0001_0000);
      event_packet_count_w[
        (event_cluster_w*(PACKET_INDEX_W+1)) +: (PACKET_INDEX_W+1)
      ] = 8'd68;
    end

    tx_mem_req_ready_w = 16'b0;
    tx_mem_rsp_valid_w = response_pending_q;
    tx_mem_rsp_data_w = response_data_q;
    rx_mem_write_ready_w = 16'b0;
    accepted_write_count_w = 0;
    accepted_write_fold_w = 0;
    for (comb_lane_i = 0; comb_lane_i < 16; comb_lane_i = comb_lane_i + 1) begin
      tx_mem_req_ready_w[comb_lane_i] = enable && !response_pending_q[comb_lane_i] &&
        ((cycle_q[2:0] ^ comb_lane_i[2:0]) != control[2:0]);
      rx_mem_write_ready_w[comb_lane_i] = enable &&
        ((cycle_q[3:0] + comb_lane_i[3:0]) != control[7:4]);
      if (rx_mem_write_valid_w[comb_lane_i] && rx_mem_write_ready_w[comb_lane_i]) begin
        accepted_write_count_w = accepted_write_count_w + 1'b1;
        accepted_write_fold_w = accepted_write_fold_w ^
          rx_mem_write_data_w[(comb_lane_i*256) +: 128] ^
          rx_mem_write_data_w[(comb_lane_i*256)+128 +: 128] ^
          {96'b0, rx_mem_write_addr_w[(comb_lane_i*ADDR_W) +: ADDR_W]};
      end
    end
  end

  (* keep_hierarchy = "yes" *)
  attention_shared_stream_context_service service (
    .clk(clk), .rst_n(rst_n),
    .layer_start(layer_start_q), .layer_idle(1'b1),
    .layer_expected_remote_contexts(8'd112),
    .event_valid(event_valid_w), .event_ready(event_ready_w),
    .event_wave(event_wave_bus_w), .event_source(event_source_bus_w),
    .event_source_base_addr(event_source_base_w),
    .event_destination_base_addr(event_destination_base_w),
    .event_packet_count(event_packet_count_w),
    .completion_ready(enable && ((cycle_q[4:0] ^ control[12:8]) != 5'b0)),
    .completion_valid(completion_valid_w),
    .completion_wave(completion_wave_w),
    .completion_destination(completion_destination_w),
    .tx_mem_req_valid(tx_mem_req_valid_w), .tx_mem_req_ready(tx_mem_req_ready_w),
    .tx_mem_req_addr(tx_mem_req_addr_w), .tx_mem_rsp_valid(tx_mem_rsp_valid_w),
    .tx_mem_rsp_ready(tx_mem_rsp_ready_w), .tx_mem_rsp_data(tx_mem_rsp_data_w),
    .rx_mem_write_valid(rx_mem_write_valid_w),
    .rx_mem_write_ready(rx_mem_write_ready_w),
    .rx_mem_write_addr(rx_mem_write_addr_w), .rx_mem_write_data(rx_mem_write_data_w),
    .context_valid(context_valid_w), .context_ready(context_ready_w),
    .context_wave(context_wave_w), .context_destination(context_destination_w),
    .context_source(context_source_w),
    .context_source_base_addr(context_source_base_w),
    .context_destination_base_addr(context_destination_base_w),
    .context_packet_count(context_packet_count_w),
    .admission_complete(admission_complete_w),
    .transport_complete(transport_complete_w), .admitted_count(admitted_count_w),
    .completed_count(completed_count_w),
    .endpoint_protocol_error(endpoint_protocol_error_w),
    .protocol_error(protocol_error_w)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      layer_start_q <= 1'b0;
      run_started_q <= 1'b0;
      event_index_q <= 0;
      response_pending_q <= 0;
      response_data_q <= 0;
      cycle_q <= 0;
      accepted_write_count_q <= 0;
      write_fold_q <= 0;
    end else begin
      cycle_q <= cycle_q + 1'b1;
      layer_start_q <= 1'b0;
      if (!enable) begin
        run_started_q <= 1'b0;
        event_index_q <= 0;
      end else if (!run_started_q) begin
        layer_start_q <= 1'b1;
        run_started_q <= 1'b1;
        event_index_q <= 0;
      end else if (event_index_q < REMOTE_CONTEXTS &&
                   event_valid_w[event_cluster_w] && event_ready_w[event_cluster_w]) begin
        event_index_q <= event_index_q + 1'b1;
      end

      for (seq_lane_i = 0; seq_lane_i < 16; seq_lane_i = seq_lane_i + 1) begin
        if (response_pending_q[seq_lane_i]) begin
          if (tx_mem_rsp_ready_w[seq_lane_i])
            response_pending_q[seq_lane_i] <= 1'b0;
        end else if (tx_mem_req_valid_w[seq_lane_i] && tx_mem_req_ready_w[seq_lane_i]) begin
          response_pending_q[seq_lane_i] <= 1'b1;
          response_data_q[(seq_lane_i*256) +: 256] <= response_word(
            seq_lane_i[3:0], tx_mem_req_addr_w[(seq_lane_i*ADDR_W) +: ADDR_W],
            control ^ cycle_q
          );
        end
      end
      if (accepted_write_count_w != 0) begin
        accepted_write_count_q <= accepted_write_count_q + accepted_write_count_w;
        write_fold_q <= write_fold_q ^ accepted_write_fold_w;
      end
    end
  end

  assign observable = write_fold_q ^ {
    cycle_q,
    accepted_write_count_q,
    event_index_q,
    admitted_count_w,
    completed_count_w,
    context_source_base_w[7:0],
    context_destination_base_w[7:0],
    context_wave_w,
    context_destination_w,
    context_source_w,
    context_packet_count_w,
    admission_complete_w,
    transport_complete_w,
    protocol_error_w,
    ^endpoint_protocol_error_w,
    completion_valid_w,
    ^{completion_wave_w, completion_destination_w}
  };
endmodule
