`timescale 1ns/1ps

// Layer admission for the 112 remote shared-SRAM contexts.
//
// The producer reports readiness independently for each cluster lane.  Events
// are retained by (wave, cluster), then selected with a round-robin scan.  A
// selected context is held until the consumer accepts it; this keeps the
// admission contract independent of downstream backpressure.
module attention_shared_stream_context_admission #(
  parameter integer ADDR_W = 32,
  parameter integer MAX_PACKETS_PER_CONTEXT = 68,
  parameter integer PACKET_INDEX_W = 7
) (
  input wire clk,
  input wire rst_n,
  input wire layer_start,
  input wire layer_idle,
  input wire [7:0] layer_expected_remote_contexts,
  input wire [15:0] event_valid,
  output wire [15:0] event_ready,
  input wire [16*3-1:0] event_wave,
  input wire [16*4-1:0] event_source,
  input wire [16*ADDR_W-1:0] event_source_base_addr,
  input wire [16*ADDR_W-1:0] event_destination_base_addr,
  input wire [16*(PACKET_INDEX_W+1)-1:0] event_packet_count,

  output wire context_valid,
  input wire context_ready,
  output wire [2:0] context_wave,
  output wire [3:0] context_destination,
  output wire [3:0] context_cluster,
  output wire [3:0] context_source,
  output wire [ADDR_W-1:0] context_source_base_addr,
  output wire [ADDR_W-1:0] context_destination_base_addr,
  output wire [PACKET_INDEX_W:0] context_packet_count,

  output wire layer_active,
  output wire layer_complete,
  output reg [7:0] admitted_count,
  output reg protocol_error
);
  localparam integer CLUSTERS = 16;
  localparam integer WAVES = 8;
  localparam integer MAX_REMOTE_CONTEXTS = 112;
  localparam integer INDEX_W = 7;
  localparam integer PACKET_COUNT_W = PACKET_INDEX_W + 1;

  reg [15:0] seen_by_wave [0:WAVES-1];
  reg [15:0] pending_by_wave [0:WAVES-1];
  reg [ADDR_W-1:0] source_base_by_index [0:CLUSTERS*WAVES-1];
  reg [ADDR_W-1:0] destination_base_by_index [0:CLUSTERS*WAVES-1];
  reg [PACKET_COUNT_W-1:0] packet_count_by_index [0:CLUSTERS*WAVES-1];
  reg [3:0] source_by_index [0:CLUSTERS*WAVES-1];
  reg layer_active_r;
  reg layer_complete_r;
  reg [7:0] expected_remote_contexts_q;
  reg hold_valid;
  reg [INDEX_W-1:0] hold_index;
  reg [INDEX_W-1:0] rr_pointer;

  reg candidate_valid;
  reg [INDEX_W-1:0] candidate_index;
  reg [2:0] candidate_wave;
  reg [3:0] candidate_cluster;
  reg [3:0] candidate_source;
  reg [ADDR_W-1:0] candidate_source_base;
  reg [ADDR_W-1:0] candidate_destination_base;
  reg [PACKET_COUNT_W-1:0] candidate_packet_count;
  integer lane_i;
  integer scan_offset;
  integer scan_index;
  integer scan_wave;
  integer scan_cluster;
  integer reset_i;

  assign layer_active = layer_active_r;
  assign layer_complete = layer_complete_r;
  assign event_ready = {CLUSTERS{layer_active_r && !layer_complete_r && !protocol_error}};

  always @(*) begin
    candidate_valid = 1'b0;
    candidate_index = {INDEX_W{1'b0}};
    candidate_wave = 3'b0;
    candidate_cluster = 4'b0;
    candidate_source = 4'b0;
    candidate_source_base = {ADDR_W{1'b0}};
    candidate_destination_base = {ADDR_W{1'b0}};
    candidate_packet_count = {PACKET_COUNT_W{1'b0}};
    for (scan_offset = 0; scan_offset < CLUSTERS * WAVES; scan_offset = scan_offset + 1) begin
      scan_index = rr_pointer + scan_offset;
      if (scan_index >= CLUSTERS * WAVES)
        scan_index = scan_index - CLUSTERS * WAVES;
      scan_wave = scan_index / CLUSTERS;
      scan_cluster = scan_index % CLUSTERS;
      if (pending_by_wave[scan_wave][scan_cluster] && !candidate_valid) begin
        candidate_valid = 1'b1;
        candidate_index = scan_index[INDEX_W-1:0];
        candidate_wave = scan_wave[2:0];
        candidate_cluster = scan_cluster[3:0];
        candidate_source = source_by_index[scan_index];
        candidate_source_base = source_base_by_index[scan_index];
        candidate_destination_base = destination_base_by_index[scan_index];
        candidate_packet_count = packet_count_by_index[scan_index];
      end
    end
  end

  assign context_valid = !protocol_error && (hold_valid || candidate_valid);
  assign context_wave = hold_valid ? hold_index[6:4] : candidate_wave;
  assign context_destination = hold_valid ? hold_index[3:0] : candidate_cluster;
  assign context_cluster = hold_valid ? hold_index[3:0] : candidate_cluster;
  assign context_source = hold_valid
    ? source_by_index[hold_index]
    : candidate_source;
  assign context_source_base_addr = hold_valid
    ? source_base_by_index[hold_index]
    : candidate_source_base;
  assign context_destination_base_addr = hold_valid
    ? destination_base_by_index[hold_index]
    : candidate_destination_base;
  assign context_packet_count = hold_valid
    ? packet_count_by_index[hold_index]
    : candidate_packet_count;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      layer_active_r <= 1'b0;
      layer_complete_r <= 1'b0;
      hold_valid <= 1'b0;
      hold_index <= {INDEX_W{1'b0}};
      rr_pointer <= {INDEX_W{1'b0}};
      admitted_count <= 8'b0;
      expected_remote_contexts_q <= 8'b0;
      protocol_error <= 1'b0;
      for (reset_i = 0; reset_i < WAVES; reset_i = reset_i + 1) begin
        seen_by_wave[reset_i] <= 16'b0;
        pending_by_wave[reset_i] <= 16'b0;
      end
      for (reset_i = 0; reset_i < CLUSTERS * WAVES; reset_i = reset_i + 1) begin
        source_base_by_index[reset_i] <= {ADDR_W{1'b0}};
        destination_base_by_index[reset_i] <= {ADDR_W{1'b0}};
        packet_count_by_index[reset_i] <= {PACKET_COUNT_W{1'b0}};
        source_by_index[reset_i] <= 4'b0;
      end
    end else begin
      if (layer_start) begin
        if (protocol_error || layer_active_r || !layer_idle ||
            layer_expected_remote_contexts > MAX_REMOTE_CONTEXTS) begin
          protocol_error <= 1'b1;
        end else begin
          layer_active_r <= (layer_expected_remote_contexts != 0);
          layer_complete_r <= (layer_expected_remote_contexts == 0);
          hold_valid <= 1'b0;
          rr_pointer <= {INDEX_W{1'b0}};
          admitted_count <= 8'b0;
          expected_remote_contexts_q <= layer_expected_remote_contexts;
          for (reset_i = 0; reset_i < WAVES; reset_i = reset_i + 1) begin
            seen_by_wave[reset_i] <= 16'b0;
            pending_by_wave[reset_i] <= 16'b0;
          end
        end
      end

      if (layer_active_r && !layer_complete_r) begin
        for (lane_i = 0; lane_i < CLUSTERS; lane_i = lane_i + 1) begin
          if (event_valid[lane_i] && event_ready[lane_i]) begin
            if (event_source[(lane_i*4) +: 4] == lane_i[3:0]) begin
              protocol_error <= 1'b1;
            end else if (seen_by_wave[event_wave[(lane_i*3) +: 3]][lane_i]) begin
              protocol_error <= 1'b1;
            end else if ((event_source_base_addr[(lane_i*ADDR_W) +: ADDR_W] & 8'hff) != 0 ||
                         (event_destination_base_addr[(lane_i*ADDR_W) +: ADDR_W] & 8'hff) != 0) begin
              protocol_error <= 1'b1;
            end else if (event_packet_count[(lane_i*PACKET_COUNT_W) +: PACKET_COUNT_W] == 0 ||
                         event_packet_count[(lane_i*PACKET_COUNT_W) +: PACKET_COUNT_W] > MAX_PACKETS_PER_CONTEXT) begin
              protocol_error <= 1'b1;
            end else begin
              seen_by_wave[event_wave[(lane_i*3) +: 3]][lane_i] <= 1'b1;
              pending_by_wave[event_wave[(lane_i*3) +: 3]][lane_i] <= 1'b1;
              source_by_index[(event_wave[(lane_i*3) +: 3] * CLUSTERS) + lane_i] <=
                event_source[(lane_i*4) +: 4];
              source_base_by_index[(event_wave[(lane_i*3) +: 3] * CLUSTERS) + lane_i] <=
                event_source_base_addr[(lane_i*ADDR_W) +: ADDR_W];
              destination_base_by_index[(event_wave[(lane_i*3) +: 3] * CLUSTERS) + lane_i] <=
                event_destination_base_addr[(lane_i*ADDR_W) +: ADDR_W];
              packet_count_by_index[(event_wave[(lane_i*3) +: 3] * CLUSTERS) + lane_i] <=
                event_packet_count[(lane_i*PACKET_COUNT_W) +: PACKET_COUNT_W];
            end
          end
        end

        if (context_valid && context_ready) begin
          if (hold_valid) begin
            pending_by_wave[hold_index[6:4]][hold_index[3:0]] <= 1'b0;
            hold_valid <= 1'b0;
            rr_pointer <= (hold_index == 7'd127) ? 7'd0 : hold_index + 1'b1;
          end else begin
            pending_by_wave[candidate_wave][candidate_cluster] <= 1'b0;
            rr_pointer <= (candidate_index == 7'd127) ? 7'd0 : candidate_index + 1'b1;
          end
          admitted_count <= admitted_count + 1'b1;
          if (admitted_count == expected_remote_contexts_q - 1'b1) begin
            layer_active_r <= 1'b0;
            layer_complete_r <= 1'b1;
          end else if (!hold_valid && candidate_valid && !context_ready) begin
            hold_valid <= 1'b1;
            hold_index <= candidate_index;
          end
        end else if (!hold_valid && candidate_valid) begin
          hold_valid <= 1'b1;
          hold_index <= candidate_index;
        end
      end

      if (event_valid != 16'b0 && !layer_active_r)
        protocol_error <= 1'b1;
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (ADDR_W < 8)
      $error("attention_shared_stream_context_admission ADDR_W must expose 256-byte alignment");
    if (MAX_PACKETS_PER_CONTEXT < 1)
      $error("attention_shared_stream_context_admission requires a positive packet bound");
    if (PACKET_INDEX_W < $clog2(MAX_PACKETS_PER_CONTEXT))
      $error("attention_shared_stream_context_admission PACKET_INDEX_W cannot represent packet counts");
  end
`endif
endmodule
