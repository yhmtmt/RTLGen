`timescale 1ns/1ps

// Exact shared-SRAM transport controller for a parameterized packet context.
//
// The controller owns context admission and packet ordering.  The existing
// descriptor-driven endpoint and 4x4 mesh own SRAM reads, writes, buffering,
// routing, and flit handshakes.  A context has eight flits per packet and an
// eight-packet receive window.  The default context has 68 packets; tags carry
// the low eight bits of the full packet index and safely reuse modulo 256.
module attention_shared_stream_context_engine #(
  parameter integer ADDR_W = 32,
  parameter integer MAX_PACKETS_PER_CONTEXT = 68,
  parameter integer PACKET_INDEX_W = 7,
  parameter integer TAG_W = 8,
  parameter integer TX_DESC_DEPTH = 8
) (
  input wire clk,
  input wire rst_n,

  input wire context_valid,
  output wire context_ready,
  input wire [2:0] context_wave,
  input wire [3:0] context_destination,
  input wire [3:0] context_source,
  input wire [ADDR_W-1:0] context_source_base_addr,
  input wire [ADDR_W-1:0] context_destination_base_addr,
  input wire [PACKET_INDEX_W:0] context_packet_count,

  output wire context_completion_valid,
  input wire context_completion_ready,
  output wire [2:0] context_completion_wave,
  output wire [3:0] context_completion_destination,

  // Descriptor ports are exposed for exact transport accounting and tests.
  output reg [15:0] tx_desc_valid,
  output wire [15:0] tx_desc_ready,
  output reg [16*4-1:0] tx_desc_destination,
  output reg [16*2-1:0] tx_desc_vc,
  output reg [16*8-1:0] tx_desc_tag,
  output reg [16*ADDR_W-1:0] tx_desc_base_addr,
  output reg [16*4-1:0] tx_desc_flit_count,

  output reg [15:0] rx_desc_valid,
  output wire [15:0] rx_desc_ready,
  output reg [16*4-1:0] rx_desc_source,
  output reg [16*2-1:0] rx_desc_vc,
  output reg [16*8-1:0] rx_desc_tag,
  output reg [16*ADDR_W-1:0] rx_desc_base_addr,
  output reg [16*4-1:0] rx_desc_flit_count,

  output wire [15:0] tx_mem_req_valid,
  input wire [15:0] tx_mem_req_ready,
  output wire [16*ADDR_W-1:0] tx_mem_req_addr,
  input wire [15:0] tx_mem_rsp_valid,
  output wire [15:0] tx_mem_rsp_ready,
  input wire [16*256-1:0] tx_mem_rsp_data,

  output wire [15:0] rx_mem_write_valid,
  input wire [15:0] rx_mem_write_ready,
  output wire [16*ADDR_W-1:0] rx_mem_write_addr,
  output wire [16*256-1:0] rx_mem_write_data,

  output wire [15:0] endpoint_protocol_error,
  output wire protocol_error
);
  localparam integer NODES = 16;
  localparam integer FLITS_PER_PACKET = 8;
  localparam integer PACKET_BYTES = 256;
  localparam integer CONTEXTS = 16;
  localparam integer PACKET_COUNT_W = PACKET_INDEX_W + 1;
  localparam integer COUNTER_INDEX_W = (PACKET_INDEX_W < 8) ? 8 : PACKET_INDEX_W;

  reg context_active [0:CONTEXTS-1];
  reg [2:0] context_wave_q [0:CONTEXTS-1];
  reg [3:0] context_source_q [0:CONTEXTS-1];
  reg [3:0] context_destination_q [0:CONTEXTS-1];
  reg [ADDR_W-1:0] context_src_base_q [0:CONTEXTS-1];
  reg [ADDR_W-1:0] context_dst_base_q [0:CONTEXTS-1];
  reg [PACKET_COUNT_W-1:0] context_packet_count_q [0:CONTEXTS-1];
  // These are counts, so the extra bit represents MAX_PACKETS_PER_CONTEXT.
  reg [COUNTER_INDEX_W:0] rx_installed_count [0:CONTEXTS-1];
  reg [COUNTER_INDEX_W:0] tx_issued_count [0:CONTEXTS-1];
  reg [COUNTER_INDEX_W:0] completed_count [0:CONTEXTS-1];
  reg context_done_pending [0:CONTEXTS-1];

  reg [15:0] source_busy;
  reg [15:0] destination_busy;
  reg protocol_error_q;

  reg free_context_found;
  reg [3:0] free_context_index;
  reg [15:0] descriptor_rx_context_valid;
  reg [15:0] descriptor_tx_context_valid;
  integer comb_i;
  integer reset_i;

  wire transport_error = protocol_error_q | (|endpoint_protocol_error);
  wire context_command_fire = context_valid && context_ready;
  wire context_command_is_valid =
    (context_source != context_destination) &&
    !source_busy[context_source] &&
    !destination_busy[context_destination] &&
    (context_packet_count != 0) &&
    (context_packet_count <= MAX_PACKETS_PER_CONTEXT) &&
    (context_source_base_addr[7:0] == 8'b0) &&
    (context_destination_base_addr[7:0] == 8'b0);

  wire context_command_metadata_invalid =
    (context_source == context_destination) ||
    (context_packet_count == 0) ||
    (context_packet_count > MAX_PACKETS_PER_CONTEXT) ||
    (context_source_base_addr[7:0] != 8'b0) ||
    (context_destination_base_addr[7:0] != 8'b0);

  // Ready advertises structural capacity only.  A malformed command still
  // handshakes so it cannot wedge the producer; it sets protocol_error and
  // is discarded without reserving an endpoint.
  // Valid commands wait for endpoint reservations.  Metadata-invalid
  // commands may handshake and become a sticky protocol error, preventing a
  // producer from wedging on a command that can never be allocated.
  assign context_ready = !transport_error && free_context_found &&
    (context_command_metadata_invalid ||
     (!source_busy[context_source] && !destination_busy[context_destination]));
  assign protocol_error = transport_error;

  // The engine uses the existing exact endpoint/mesh composition.  The
  // endpoint parameters are widened only for the byte addresses; flit width,
  // VC, tag, and packet-count contracts remain fixed.
  wire [15:0] mesh_rx_completion_valid;
  wire [15:0] mesh_rx_completion_ready;
  wire [16*4-1:0] mesh_rx_completion_source;
  wire [16*2-1:0] mesh_rx_completion_vc;
  wire [16*8-1:0] mesh_rx_completion_tag;

  assign mesh_rx_completion_ready = 16'hffff;

  noc_sram_packet_mesh4x4 #(
    .DATA_W(256),
    .ENDPOINT_W(4),
    .VC_W(2),
    .VC_COUNT(4),
    .TAG_W(TAG_W),
    .FRAGMENT_W(3),
    .ADDR_W(ADDR_W),
    .FLIT_COUNT_W(4),
    .TX_DESC_DEPTH(TX_DESC_DEPTH),
    .TX_OUTSTANDING(8),
    .RX_CONTEXTS(8),
    .ROUTER_FIFO_DEPTH(4),
    .COUNTER_W(32)
  ) transport_mesh (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr),
    .rx_mem_write_data(rx_mem_write_data),
    .rx_completion_valid(mesh_rx_completion_valid),
    .rx_completion_ready(mesh_rx_completion_ready),
    .rx_completion_source(mesh_rx_completion_source),
    .rx_completion_vc(mesh_rx_completion_vc),
    .rx_completion_tag(mesh_rx_completion_tag),
    .endpoint_protocol_error(endpoint_protocol_error),
    .router_accepted_flit_count(), .router_forwarded_flit_count(),
    .router_input_stall_cycles(), .router_output_stall_cycles(),
    .router_contention_cycles(), .router_current_input_occupancy(),
    .router_max_input_occupancy(), .router_route_flit_count()
  );

  // Reservations make source and destination endpoints unique per active
  // context.  Therefore every eligible context can issue one descriptor in
  // the same cycle; there is no global descriptor arbiter on this path.
  always @(*) begin
    free_context_found = 1'b0;
    free_context_index = 4'b0;
    descriptor_rx_context_valid = 16'b0;
    descriptor_tx_context_valid = 16'b0;
    tx_desc_valid = 16'b0;
    tx_desc_destination = {16*4{1'b0}};
    tx_desc_vc = {16*2{1'b0}};
    tx_desc_tag = {16*8{1'b0}};
    tx_desc_base_addr = {16*ADDR_W{1'b0}};
    tx_desc_flit_count = {16*4{1'b0}};
    rx_desc_valid = 16'b0;
    rx_desc_source = {16*4{1'b0}};
    rx_desc_vc = {16*2{1'b0}};
    rx_desc_tag = {16*8{1'b0}};
    rx_desc_base_addr = {16*ADDR_W{1'b0}};
    rx_desc_flit_count = {16*4{1'b0}};

    for (comb_i = 0; comb_i < CONTEXTS; comb_i = comb_i + 1) begin
      if (!context_active[comb_i] && !free_context_found) begin
        free_context_found = 1'b1;
        free_context_index = comb_i[3:0];
      end
      if (!transport_error && context_active[comb_i] &&
          (rx_installed_count[comb_i] < context_packet_count_q[comb_i]) &&
          (rx_installed_count[comb_i] >= completed_count[comb_i]) &&
          ((rx_installed_count[comb_i] - completed_count[comb_i]) < 8)) begin
        descriptor_rx_context_valid[comb_i] = 1'b1;
        rx_desc_valid[context_destination_q[comb_i]] = 1'b1;
        rx_desc_source[(context_destination_q[comb_i]*4) +: 4] = context_source_q[comb_i];
        rx_desc_vc[(context_destination_q[comb_i]*2) +: 2] = 2'b0;
        rx_desc_tag[(context_destination_q[comb_i]*8) +: 8] = rx_installed_count[comb_i][7:0];
        rx_desc_base_addr[(context_destination_q[comb_i]*ADDR_W) +: ADDR_W] =
          context_dst_base_q[comb_i] + (rx_installed_count[comb_i] * PACKET_BYTES);
        rx_desc_flit_count[(context_destination_q[comb_i]*4) +: 4] = FLITS_PER_PACKET;
      end
      if (!transport_error && context_active[comb_i] &&
          (tx_issued_count[comb_i] < context_packet_count_q[comb_i]) &&
          (tx_issued_count[comb_i] < rx_installed_count[comb_i])) begin
        descriptor_tx_context_valid[comb_i] = 1'b1;
        tx_desc_valid[context_source_q[comb_i]] = 1'b1;
        tx_desc_destination[(context_source_q[comb_i]*4) +: 4] = context_destination_q[comb_i];
        tx_desc_vc[(context_source_q[comb_i]*2) +: 2] = 2'b0;
        tx_desc_tag[(context_source_q[comb_i]*8) +: 8] = tx_issued_count[comb_i][7:0];
        tx_desc_base_addr[(context_source_q[comb_i]*ADDR_W) +: ADDR_W] =
          context_src_base_q[comb_i] + (tx_issued_count[comb_i] * PACKET_BYTES);
        tx_desc_flit_count[(context_source_q[comb_i]*4) +: 4] = FLITS_PER_PACKET;
      end
    end
  end

  // Match each endpoint completion to the unique context occupying its
  // destination endpoint and require the next packet tag in sequence.
  reg [15:0] completion_good;
  reg [15:0] completion_match;
  reg [3:0] completion_context [0:NODES-1];
  integer completion_ep;
  integer completion_ctx_i;
  always @(*) begin
    completion_good = 16'b0;
    completion_match = 16'b0;
    for (completion_ep = 0; completion_ep < NODES; completion_ep = completion_ep + 1) begin
      completion_context[completion_ep] = 4'b0;
      for (completion_ctx_i = 0; completion_ctx_i < CONTEXTS; completion_ctx_i = completion_ctx_i + 1) begin
        if (context_active[completion_ctx_i] &&
            context_destination_q[completion_ctx_i] == completion_ep[3:0] &&
            !completion_match[completion_ep]) begin
          completion_match[completion_ep] = 1'b1;
          completion_context[completion_ep] = completion_ctx_i[3:0];
          if (!context_done_pending[completion_ctx_i] &&
              completed_count[completion_ctx_i] < rx_installed_count[completion_ctx_i] &&
              mesh_rx_completion_source[(completion_ep*4) +: 4] == context_source_q[completion_ctx_i] &&
              mesh_rx_completion_vc[(completion_ep*2) +: 2] == 2'b0 &&
              mesh_rx_completion_tag[(completion_ep*8) +: 8] == completed_count[completion_ctx_i][7:0])
            completion_good[completion_ep] = 1'b1;
        end
      end
    end
  end

  // One context completion is arbitrated independently of packet completion.
  reg completion_hold_valid;
  reg [3:0] completion_hold_context;
  reg completion_candidate_valid;
  reg [3:0] completion_candidate_context;
  integer candidate_i;
  always @(*) begin
    completion_candidate_valid = 1'b0;
    completion_candidate_context = 4'b0;
    for (candidate_i = 0; candidate_i < CONTEXTS; candidate_i = candidate_i + 1) begin
      if (context_active[candidate_i] && context_done_pending[candidate_i] &&
          !completion_candidate_valid) begin
        completion_candidate_valid = 1'b1;
        completion_candidate_context = candidate_i[3:0];
      end
    end
  end

  assign context_completion_valid = completion_hold_valid || completion_candidate_valid;
  assign context_completion_wave = completion_hold_valid
    ? context_wave_q[completion_hold_context]
    : context_wave_q[completion_candidate_context];
  assign context_completion_destination = completion_hold_valid
    ? context_destination_q[completion_hold_context]
    : context_destination_q[completion_candidate_context];

  integer state_i;
  integer completion_i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      source_busy <= 16'b0;
      destination_busy <= 16'b0;
      protocol_error_q <= 1'b0;
      completion_hold_valid <= 1'b0;
      completion_hold_context <= 4'b0;
      for (reset_i = 0; reset_i < CONTEXTS; reset_i = reset_i + 1) begin
        context_active[reset_i] <= 1'b0;
        context_wave_q[reset_i] <= 3'b0;
        context_source_q[reset_i] <= 4'b0;
        context_destination_q[reset_i] <= 4'b0;
        context_src_base_q[reset_i] <= {ADDR_W{1'b0}};
        context_dst_base_q[reset_i] <= {ADDR_W{1'b0}};
        context_packet_count_q[reset_i] <= {PACKET_COUNT_W{1'b0}};
        rx_installed_count[reset_i] <= {(COUNTER_INDEX_W+1){1'b0}};
        tx_issued_count[reset_i] <= {(COUNTER_INDEX_W+1){1'b0}};
        completed_count[reset_i] <= {(COUNTER_INDEX_W+1){1'b0}};
        context_done_pending[reset_i] <= 1'b0;
      end
    end else begin
      if (context_command_fire) begin
        if (!context_command_is_valid) begin
          protocol_error_q <= 1'b1;
        end else begin
          context_active[free_context_index] <= 1'b1;
          context_wave_q[free_context_index] <= context_wave;
          context_source_q[free_context_index] <= context_source;
          context_destination_q[free_context_index] <= context_destination;
          context_src_base_q[free_context_index] <= context_source_base_addr;
          context_dst_base_q[free_context_index] <= context_destination_base_addr;
          context_packet_count_q[free_context_index] <= context_packet_count;
          rx_installed_count[free_context_index] <= {(COUNTER_INDEX_W+1){1'b0}};
          tx_issued_count[free_context_index] <= {(COUNTER_INDEX_W+1){1'b0}};
          completed_count[free_context_index] <= {(COUNTER_INDEX_W+1){1'b0}};
          context_done_pending[free_context_index] <= 1'b0;
          source_busy[context_source] <= 1'b1;
          destination_busy[context_destination] <= 1'b1;
        end
      end

      for (state_i = 0; state_i < CONTEXTS; state_i = state_i + 1) begin
        if (descriptor_rx_context_valid[state_i] &&
            rx_desc_ready[context_destination_q[state_i]])
          rx_installed_count[state_i] <= rx_installed_count[state_i] + 1'b1;
        if (descriptor_tx_context_valid[state_i] &&
            tx_desc_ready[context_source_q[state_i]])
          tx_issued_count[state_i] <= tx_issued_count[state_i] + 1'b1;
      end

      for (completion_i = 0; completion_i < NODES; completion_i = completion_i + 1) begin
        if (mesh_rx_completion_valid[completion_i]) begin
          if (!completion_good[completion_i]) begin
            protocol_error_q <= 1'b1;
          end else begin
            completed_count[completion_context[completion_i]] <=
              completed_count[completion_context[completion_i]] + 1'b1;
            if (completed_count[completion_context[completion_i]] ==
                context_packet_count_q[completion_context[completion_i]] - 1'b1)
              context_done_pending[completion_context[completion_i]] <= 1'b1;
          end
        end
      end

      if (context_completion_valid && context_completion_ready) begin
        if (completion_hold_valid) begin
          context_active[completion_hold_context] <= 1'b0;
          context_done_pending[completion_hold_context] <= 1'b0;
          source_busy[context_source_q[completion_hold_context]] <= 1'b0;
          destination_busy[context_destination_q[completion_hold_context]] <= 1'b0;
          completion_hold_valid <= 1'b0;
        end else begin
          context_active[completion_candidate_context] <= 1'b0;
          context_done_pending[completion_candidate_context] <= 1'b0;
          source_busy[context_source_q[completion_candidate_context]] <= 1'b0;
          destination_busy[context_destination_q[completion_candidate_context]] <= 1'b0;
        end
      end else if (!completion_hold_valid && completion_candidate_valid) begin
        completion_hold_valid <= 1'b1;
        completion_hold_context <= completion_candidate_context;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (ADDR_W < 8)
      $error("attention_shared_stream_context_engine ADDR_W must expose 256-byte alignment");
    if (MAX_PACKETS_PER_CONTEXT < 1)
      $error("attention_shared_stream_context_engine requires a positive packet count");
    if (PACKET_INDEX_W < $clog2(MAX_PACKETS_PER_CONTEXT))
      $error("attention_shared_stream_context_engine PACKET_INDEX_W cannot represent packet indices");
    if (TAG_W != 8)
      $error("attention_shared_stream_context_engine requires an 8-bit packet tag");
  end
`endif
endmodule
