`timescale 1ns/1ps

// Runtime-loaded workload replay for the exact endpoint plus 4x4 mesh RTL.
// Descriptor word layout: release[31:0], source[35:32], destination[39:36],
// VC[41:40], tag[49:42], flit_count[53:50]. Packet ID is the array index.
module noc_sram_packet_mesh4x4_workload_tb;
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 24;
  localparam integer MAX_PACKETS = 12000;
  localparam integer RX_CONTEXTS = 8;
  localparam integer BOUNDED_PACKET_SLOTS = 563;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  integer packet_count = 0;
  integer expected_flits = 0;
  integer timeout_cycles = 2000000;
  integer plusarg_status;
  integer drain_cycle = 0;
  integer submitted_packets = 0;
  integer completed_packets = 0;
  integer accepted_writes = 0;
  integer comb_endpoint_i;
  integer comb_context_i;
  integer seq_endpoint_i;
  integer seq_context_i;
  integer packet_i;
  integer queue_i;
  integer selected_packet;
  integer selected_index;
  integer free_context;
  integer duplicate_context;
  integer comb_selected_packet;
  integer comb_selected_index;
  integer comb_free_context;
  integer comb_duplicate_context;
  integer write_fragment;
  integer request_packet;
  integer request_fragment;
  integer request_slot;
  integer response_packet;
  integer response_fragment;
  integer descriptor_slot;
  integer tx_fire_count;
  integer completion_fire_count;
  integer write_fire_count;
  integer completion_packet [0:15];
  reg [15:0] completion_shadow_valid = 0;

  reg [95:0] descriptors [0:MAX_PACKETS-1];
  reg [15:0] command_order [0:MAX_PACKETS-1];
  reg [15:0] source_order [0:MAX_PACKETS-1];
  reg [15:0] destination_order [0:MAX_PACKETS-1];
  reg [31:0] source_queue_meta [0:15];
  reg [31:0] destination_queue_meta [0:15];
  integer source_position [0:15];
  integer destination_position [0:15];
  reg [MAX_PACKETS-1:0] rx_installed = 0;
  reg [MAX_PACKETS-1:0] tx_submitted = 0;
  reg [MAX_PACKETS-1:0] packet_completed = 0;
  reg [127:0] live_context_valid = 0;
  integer live_context_packet [0:127];

`ifdef SERIAL_PAIRED_SCHEDULER
  wire [15:0] tx_desc_valid;
`else
  reg [15:0] tx_desc_valid = 0;
`endif
  wire [15:0] tx_desc_ready;
`ifdef SERIAL_PAIRED_SCHEDULER
  wire [63:0] tx_desc_destination;
  wire [31:0] tx_desc_vc;
  wire [127:0] tx_desc_tag;
  wire [16*ADDR_W-1:0] tx_desc_base_addr;
  wire [63:0] tx_desc_flit_count;
`else
  reg [63:0] tx_desc_destination = 0;
  reg [31:0] tx_desc_vc = 0;
  reg [127:0] tx_desc_tag = 0;
  reg [16*ADDR_W-1:0] tx_desc_base_addr = 0;
  reg [63:0] tx_desc_flit_count = 0;
`endif
  wire [15:0] tx_mem_req_valid;
  wire [15:0] tx_mem_req_ready;
  wire [16*ADDR_W-1:0] tx_mem_req_addr;
  reg [15:0] tx_mem_rsp_valid = 0;
  wire [15:0] tx_mem_rsp_ready;
  reg [16*DATA_W-1:0] tx_mem_rsp_data = 0;
  reg [ADDR_W-1:0] pending_read_addr [0:16*8-1];
  integer pending_read_rd [0:15];
  integer pending_read_wr [0:15];
  integer pending_read_count [0:15];
  integer pending_read_packet [0:16*8-1];

`ifdef GENERATED_COMMAND_SOURCE
  integer serial_rx_position = 0;
  integer serial_tx_position = 0;
  integer tx_packet_queue [0:16*MAX_PACKETS-1];
  integer tx_packet_rd [0:15];
  integer tx_packet_wr [0:15];
  integer tx_packet_fragment [0:15];
  reg [ADDR_W-1:0] packet_tx_base [0:MAX_PACKETS-1];
  reg [ADDR_W-1:0] packet_rx_base [0:MAX_PACKETS-1];
  reg [BOUNDED_PACKET_SLOTS-1:0] tx_slot_live [0:15];
  reg [BOUNDED_PACKET_SLOTS-1:0] rx_slot_live [0:15];
`endif

`ifdef SERIAL_PAIRED_SCHEDULER
  wire [15:0] rx_desc_valid;
`else
  reg [15:0] rx_desc_valid = 0;
`endif
  wire [15:0] rx_desc_ready;
`ifdef SERIAL_PAIRED_SCHEDULER
  wire [63:0] rx_desc_source;
  wire [31:0] rx_desc_vc;
  wire [127:0] rx_desc_tag;
  wire [16*ADDR_W-1:0] rx_desc_base_addr;
  wire [63:0] rx_desc_flit_count;
`else
  reg [63:0] rx_desc_source = 0;
  reg [31:0] rx_desc_vc = 0;
  reg [127:0] rx_desc_tag = 0;
  reg [16*ADDR_W-1:0] rx_desc_base_addr = 0;
  reg [63:0] rx_desc_flit_count = 0;
`endif
  wire [15:0] rx_mem_write_valid;
  reg [15:0] rx_mem_write_ready = 16'hffff;
  wire [16*ADDR_W-1:0] rx_mem_write_addr;
  wire [16*DATA_W-1:0] rx_mem_write_data;
  wire [15:0] rx_completion_valid;
  reg [15:0] rx_completion_ready = 16'hffff;
  wire [63:0] rx_completion_source;
  wire [31:0] rx_completion_vc;
  wire [127:0] rx_completion_tag;
  wire [15:0] endpoint_protocol_error;

  wire [16*32-1:0] router_accepted_flit_count;
  wire [16*32-1:0] router_forwarded_flit_count;
  wire [16*32-1:0] router_input_stall_cycles;
  wire [16*32-1:0] router_output_stall_cycles;
  wire [16*32-1:0] router_contention_cycles;
  wire [16*32-1:0] router_current_input_occupancy;
  wire [16*32-1:0] router_max_input_occupancy;
  wire [16*5*32-1:0] router_route_flit_count;

  string descriptor_mem;
  string command_order_mem;
  string source_order_mem;
  string destination_order_mem;
  string source_meta_mem;
  string destination_meta_mem;

`ifdef SERIAL_PAIRED_SCHEDULER
  localparam integer COMMAND_W = 102;
  wire scheduler_cmd_valid;
  wire scheduler_cmd_ready;
  wire [COMMAND_W-1:0] scheduler_command;
`ifndef GENERATED_COMMAND_SOURCE
  wire command_mem_req_valid;
  wire command_mem_req_ready = 1'b1;
  wire [13:0] command_mem_req_addr;
  reg command_mem_pending = 1'b0;
  reg [13:0] command_mem_pending_addr = 0;
  wire command_mem_rsp_valid = command_mem_pending;
  wire command_mem_rsp_ready;
  wire [COMMAND_W-1:0] command_mem_rsp_data =
    workload_command(command_mem_pending_addr);
  wire [31:0] prefetch_request_count;
  wire [31:0] prefetch_response_count;
  wire [31:0] prefetch_delivered_command_count;
  wire [31:0] prefetch_memory_stall_cycles;
  wire prefetch_protocol_error;
`else
  wire command_generator_done;
  wire [31:0] generated_command_count;
  wire command_generator_protocol_error;
`endif
  wire [31:0] scheduler_accepted_command_count;
  wire [31:0] scheduler_installed_receive_count;
  wire [31:0] scheduler_submitted_transmit_count;
  wire [31:0] scheduler_release_wait_cycles;
  wire [31:0] scheduler_endpoint_stall_cycles;
  wire scheduler_protocol_error;

`ifndef GENERATED_COMMAND_SOURCE
  function [COMMAND_W-1:0] workload_command;
    input [13:0] command_address;
    reg [15:0] command_packet;
    begin
      command_packet = command_order[command_address];
      workload_command = {
        descriptors[command_packet][53:50],
        {command_packet, 8'b0},
        {command_packet, 8'b0},
        descriptors[command_packet][49:42],
        descriptors[command_packet][41:40],
        descriptors[command_packet][39:36],
        descriptors[command_packet][35:32],
        descriptors[command_packet][31:0]
      };
    end
  endfunction

  noc_descriptor_command_prefetch #(
    .COMMAND_W(COMMAND_W),
    .ADDR_W(14),
    .COUNT_W(14)
  ) command_prefetch (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .command_count(packet_count[13:0]),
    .mem_req_valid(command_mem_req_valid),
    .mem_req_ready(command_mem_req_ready),
    .mem_req_addr(command_mem_req_addr),
    .mem_rsp_valid(command_mem_rsp_valid),
    .mem_rsp_ready(command_mem_rsp_ready),
    .mem_rsp_data(command_mem_rsp_data),
    .cmd_valid(scheduler_cmd_valid), .cmd_ready(scheduler_cmd_ready),
    .cmd_data(scheduler_command),
    .request_count(prefetch_request_count),
    .response_count(prefetch_response_count),
    .delivered_command_count(prefetch_delivered_command_count),
    .memory_stall_cycles(prefetch_memory_stall_cycles),
    .protocol_error(prefetch_protocol_error)
  );
`else
  noc_llama7b_phase2_command_generator command_generator (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .cmd_valid(scheduler_cmd_valid), .cmd_ready(scheduler_cmd_ready),
    .cmd_data(scheduler_command), .done(command_generator_done),
    .generated_command_count(generated_command_count),
    .protocol_error(command_generator_protocol_error)
  );
`endif

  noc_descriptor_pair_scheduler scheduler (
    .clk(clk), .rst_n(rst_n), .current_cycle(cycle),
    .cmd_valid(scheduler_cmd_valid), .cmd_ready(scheduler_cmd_ready),
    .cmd_release_cycle(scheduler_command[31:0]),
    .cmd_source(scheduler_command[35:32]),
    .cmd_destination(scheduler_command[39:36]),
    .cmd_vc(scheduler_command[41:40]),
    .cmd_tag(scheduler_command[49:42]),
    .cmd_tx_base_addr(scheduler_command[73:50]),
    .cmd_rx_base_addr(scheduler_command[97:74]),
    .cmd_flit_count(scheduler_command[101:98]),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .accepted_command_count(scheduler_accepted_command_count),
    .installed_receive_count(scheduler_installed_receive_count),
    .submitted_transmit_count(scheduler_submitted_transmit_count),
    .release_wait_cycles(scheduler_release_wait_cycles),
    .endpoint_stall_cycles(scheduler_endpoint_stall_cycles),
    .protocol_error(scheduler_protocol_error)
  );
`endif

  function [DATA_W-1:0] memory_data;
    input [3:0] source;
    input [15:0] packet_id;
    input [2:0] fragment;
    begin
      memory_data = {DATA_W{1'b0}};
      memory_data[3:0] = source;
      memory_data[19:4] = packet_id;
      memory_data[22:20] = fragment;
      memory_data[54:23] = 32'h5a17c0de;
    end
  endfunction

  noc_sram_packet_mesh4x4 #(
    .ADDR_W(ADDR_W),
    .RX_CONTEXTS(RX_CONTEXTS)
  ) dut (
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
    .rx_completion_valid(rx_completion_valid),
    .rx_completion_ready(rx_completion_ready),
    .rx_completion_source(rx_completion_source),
    .rx_completion_vc(rx_completion_vc),
    .rx_completion_tag(rx_completion_tag),
    .endpoint_protocol_error(endpoint_protocol_error),
    .router_accepted_flit_count(router_accepted_flit_count),
    .router_forwarded_flit_count(router_forwarded_flit_count),
    .router_input_stall_cycles(router_input_stall_cycles),
    .router_output_stall_cycles(router_output_stall_cycles),
    .router_contention_cycles(router_contention_cycles),
    .router_current_input_occupancy(router_current_input_occupancy),
    .router_max_input_occupancy(router_max_input_occupancy),
    .router_route_flit_count(router_route_flit_count)
  );

  always #1 clk = ~clk;

  genvar ready_g;
  generate
    for (ready_g = 0; ready_g < 16; ready_g = ready_g + 1) begin : g_sram_ready
      assign tx_mem_req_ready[ready_g] = pending_read_count[ready_g] < 8;
    end
  endgenerate

  // Select at most one released descriptor per source and destination. The
  // receive side must handshake first; the transmit side observes that state
  // no earlier than the following cycle.
`ifndef SERIAL_PAIRED_SCHEDULER
  always @(*) begin
    tx_desc_valid = 0;
    tx_desc_destination = 0;
    tx_desc_vc = 0;
    tx_desc_tag = 0;
    tx_desc_base_addr = 0;
    tx_desc_flit_count = 0;
    rx_desc_valid = 0;
    rx_desc_source = 0;
    rx_desc_vc = 0;
    rx_desc_tag = 0;
    rx_desc_base_addr = 0;
    rx_desc_flit_count = 0;

    for (comb_endpoint_i = 0; comb_endpoint_i < 16; comb_endpoint_i = comb_endpoint_i + 1) begin
      if (rst_n &&
          destination_position[comb_endpoint_i] < destination_queue_meta[comb_endpoint_i][31:16]) begin
        comb_selected_index = destination_queue_meta[comb_endpoint_i][15:0] +
          destination_position[comb_endpoint_i];
        comb_selected_packet = destination_order[comb_selected_index];
        comb_free_context = 0;
        comb_duplicate_context = 0;
        for (comb_context_i = 0; comb_context_i < RX_CONTEXTS;
             comb_context_i = comb_context_i + 1) begin
          if (!live_context_valid[comb_endpoint_i*RX_CONTEXTS + comb_context_i])
            comb_free_context = 1;
          else if (descriptors[live_context_packet[comb_endpoint_i*RX_CONTEXTS + comb_context_i]][35:32] ==
                   descriptors[comb_selected_packet][35:32] &&
                   descriptors[live_context_packet[comb_endpoint_i*RX_CONTEXTS + comb_context_i]][41:40] ==
                   descriptors[comb_selected_packet][41:40] &&
                   descriptors[live_context_packet[comb_endpoint_i*RX_CONTEXTS + comb_context_i]][49:42] ==
                   descriptors[comb_selected_packet][49:42])
            comb_duplicate_context = 1;
        end
        if (descriptors[comb_selected_packet][31:0] <= cycle &&
            comb_free_context && !comb_duplicate_context) begin
          rx_desc_valid[comb_endpoint_i] = 1'b1;
          rx_desc_source[(comb_endpoint_i*4) +: 4] = descriptors[comb_selected_packet][35:32];
          rx_desc_vc[(comb_endpoint_i*2) +: 2] = descriptors[comb_selected_packet][41:40];
          rx_desc_tag[(comb_endpoint_i*8) +: 8] = descriptors[comb_selected_packet][49:42];
          rx_desc_base_addr[(comb_endpoint_i*ADDR_W) +: ADDR_W] = comb_selected_packet << 8;
          rx_desc_flit_count[(comb_endpoint_i*4) +: 4] = descriptors[comb_selected_packet][53:50];
        end
      end

      if (rst_n && source_position[comb_endpoint_i] < source_queue_meta[comb_endpoint_i][31:16]) begin
        comb_selected_index = source_queue_meta[comb_endpoint_i][15:0] +
          source_position[comb_endpoint_i];
        comb_selected_packet = source_order[comb_selected_index];
        if (descriptors[comb_selected_packet][31:0] <= cycle &&
            rx_installed[comb_selected_packet]) begin
          tx_desc_valid[comb_endpoint_i] = 1'b1;
          tx_desc_destination[(comb_endpoint_i*4) +: 4] = descriptors[comb_selected_packet][39:36];
          tx_desc_vc[(comb_endpoint_i*2) +: 2] = descriptors[comb_selected_packet][41:40];
          tx_desc_tag[(comb_endpoint_i*8) +: 8] = descriptors[comb_selected_packet][49:42];
          tx_desc_base_addr[(comb_endpoint_i*ADDR_W) +: ADDR_W] = comb_selected_packet << 8;
          tx_desc_flit_count[(comb_endpoint_i*4) +: 4] = descriptors[comb_selected_packet][53:50];
        end
      end
    end
  end
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle <= 0;
      tx_mem_rsp_valid <= 0;
      tx_mem_rsp_data <= 0;
      submitted_packets <= 0;
      completed_packets <= 0;
      accepted_writes <= 0;
      rx_installed <= 0;
      tx_submitted <= 0;
      packet_completed <= 0;
      live_context_valid <= 0;
      completion_shadow_valid <= 0;
`ifdef GENERATED_COMMAND_SOURCE
      serial_rx_position <= 0;
      serial_tx_position <= 0;
`endif
`ifdef SERIAL_PAIRED_SCHEDULER
`ifndef GENERATED_COMMAND_SOURCE
      command_mem_pending <= 1'b0;
      command_mem_pending_addr <= 0;
`endif
`endif
      for (seq_endpoint_i = 0; seq_endpoint_i < 16; seq_endpoint_i = seq_endpoint_i + 1) begin
        source_position[seq_endpoint_i] <= 0;
        destination_position[seq_endpoint_i] <= 0;
        completion_packet[seq_endpoint_i] <= 0;
        pending_read_rd[seq_endpoint_i] <= 0;
        pending_read_wr[seq_endpoint_i] <= 0;
        pending_read_count[seq_endpoint_i] <= 0;
`ifdef GENERATED_COMMAND_SOURCE
        tx_packet_rd[seq_endpoint_i] <= 0;
        tx_packet_wr[seq_endpoint_i] <= 0;
        tx_packet_fragment[seq_endpoint_i] <= 0;
        tx_slot_live[seq_endpoint_i] <= 0;
        rx_slot_live[seq_endpoint_i] <= 0;
`endif
      end
    end else begin
      cycle <= cycle + 1;
`ifdef SERIAL_PAIRED_SCHEDULER
`ifndef GENERATED_COMMAND_SOURCE
      if (command_mem_pending && command_mem_rsp_ready)
        command_mem_pending <= 1'b0;
      if (command_mem_req_valid && command_mem_req_ready) begin
        command_mem_pending <= 1'b1;
        command_mem_pending_addr <= command_mem_req_addr;
      end
`endif
`endif
      tx_fire_count = 0;
      completion_fire_count = 0;
      write_fire_count = 0;

      for (seq_endpoint_i = 0; seq_endpoint_i < 16; seq_endpoint_i = seq_endpoint_i + 1) begin
`ifdef GENERATED_COMMAND_SOURCE
        if (tx_mem_rsp_valid[seq_endpoint_i] && tx_mem_rsp_ready[seq_endpoint_i]) begin
          response_packet =
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) + 4 +: 16];
          response_fragment =
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) + 20 +: 3];
          if (response_fragment + 1 == descriptors[response_packet][53:50]) begin
            request_slot = packet_tx_base[response_packet] >> 8;
            tx_slot_live[seq_endpoint_i][request_slot] <= 1'b0;
          end
        end
`endif
        request_packet = -1;
        request_fragment = -1;
        if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
`ifdef GENERATED_COMMAND_SOURCE
          request_packet = tx_packet_queue[
            seq_endpoint_i*MAX_PACKETS + tx_packet_rd[seq_endpoint_i]];
          request_fragment = tx_packet_fragment[seq_endpoint_i];
          if (tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] !==
              packet_tx_base[request_packet] + request_fragment*32)
            $fatal(1,
              "TX packet-slot address mismatch endpoint=%0d packet=%0d fragment=%0d address=%h base=%h",
              seq_endpoint_i, request_packet, request_fragment,
              tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W],
              packet_tx_base[request_packet]);
          if (request_fragment + 1 == descriptors[request_packet][53:50]) begin
            tx_packet_rd[seq_endpoint_i] <= tx_packet_rd[seq_endpoint_i] + 1;
            tx_packet_fragment[seq_endpoint_i] <= 0;
          end else begin
            tx_packet_fragment[seq_endpoint_i] <= request_fragment + 1;
          end
`else
          request_packet = tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
          request_fragment =
            (tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 5) & 7;
`endif
        end

        if (!tx_mem_rsp_valid[seq_endpoint_i] || tx_mem_rsp_ready[seq_endpoint_i]) begin
          if (pending_read_count[seq_endpoint_i] > 0) begin
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b1;
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) +: DATA_W] <= memory_data(
              seq_endpoint_i[3:0],
              pending_read_packet[seq_endpoint_i*8 + pending_read_rd[seq_endpoint_i]],
              (pending_read_addr[seq_endpoint_i*8 + pending_read_rd[seq_endpoint_i]] >> 5) & 7);
            pending_read_rd[seq_endpoint_i] <= (pending_read_rd[seq_endpoint_i] + 1) % 8;
            if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
              pending_read_addr[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
                tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
              pending_read_packet[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
                request_packet;
              pending_read_wr[seq_endpoint_i] <= (pending_read_wr[seq_endpoint_i] + 1) % 8;
            end else begin
              pending_read_count[seq_endpoint_i] <= pending_read_count[seq_endpoint_i] - 1;
            end
          end else if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
            // Empty-queue bypass: a request accepted at this edge becomes the
            // response consumed at the following edge.
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b1;
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) +: DATA_W] <= memory_data(
              seq_endpoint_i[3:0], request_packet, request_fragment[2:0]);
          end else begin
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b0;
          end
        end else if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
          pending_read_addr[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
            tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
          pending_read_packet[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
            request_packet;
          pending_read_wr[seq_endpoint_i] <= (pending_read_wr[seq_endpoint_i] + 1) % 8;
          pending_read_count[seq_endpoint_i] <= pending_read_count[seq_endpoint_i] + 1;
        end

        if (rx_desc_valid[seq_endpoint_i] && rx_desc_ready[seq_endpoint_i]) begin
`ifdef SERIAL_PAIRED_SCHEDULER
`ifdef GENERATED_COMMAND_SOURCE
          selected_packet = command_order[serial_rx_position];
          serial_rx_position <= serial_rx_position + 1;
          if (descriptors[selected_packet][39:36] != seq_endpoint_i[3:0] ||
              rx_desc_source[(seq_endpoint_i*4) +: 4] !== descriptors[selected_packet][35:32] ||
              rx_desc_vc[(seq_endpoint_i*2) +: 2] !== descriptors[selected_packet][41:40] ||
              rx_desc_tag[(seq_endpoint_i*8) +: 8] !== descriptors[selected_packet][49:42] ||
              rx_desc_flit_count[(seq_endpoint_i*4) +: 4] !== descriptors[selected_packet][53:50])
            $fatal(1, "generated RX descriptor metadata mismatch for packet %0d", selected_packet);
          packet_rx_base[selected_packet] <=
            rx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
          descriptor_slot =
            rx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
          if (descriptor_slot < 0 || descriptor_slot >= BOUNDED_PACKET_SLOTS)
            $fatal(1, "generated RX descriptor slot is out of bounds: %0d", descriptor_slot);
          if (rx_slot_live[seq_endpoint_i][descriptor_slot])
            $fatal(1,
              "generated RX descriptor reuses live slot endpoint=%0d slot=%0d packet=%0d",
              seq_endpoint_i, descriptor_slot, selected_packet);
          rx_slot_live[seq_endpoint_i][descriptor_slot] <= 1'b1;
`else
          selected_packet = rx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
`endif
`else
          selected_index = destination_queue_meta[seq_endpoint_i][15:0] +
            destination_position[seq_endpoint_i];
          selected_packet = destination_order[selected_index];
          destination_position[seq_endpoint_i] <= destination_position[seq_endpoint_i] + 1;
`endif
          rx_installed[selected_packet] <= 1'b1;
          free_context = -1;
          for (seq_context_i = 0; seq_context_i < RX_CONTEXTS;
               seq_context_i = seq_context_i + 1)
            if (!live_context_valid[seq_endpoint_i*RX_CONTEXTS + seq_context_i] && free_context < 0)
              free_context = seq_context_i;
          if (free_context < 0)
            $fatal(1, "testbench lost RX context accounting at endpoint %0d", seq_endpoint_i);
          live_context_valid[seq_endpoint_i*RX_CONTEXTS + free_context] <= 1'b1;
          live_context_packet[seq_endpoint_i*RX_CONTEXTS + free_context] <= selected_packet;
        end

        if (tx_desc_valid[seq_endpoint_i] && tx_desc_ready[seq_endpoint_i]) begin
`ifdef SERIAL_PAIRED_SCHEDULER
`ifdef GENERATED_COMMAND_SOURCE
          selected_packet = command_order[serial_tx_position];
          serial_tx_position <= serial_tx_position + 1;
          if (descriptors[selected_packet][35:32] != seq_endpoint_i[3:0] ||
              tx_desc_destination[(seq_endpoint_i*4) +: 4] !== descriptors[selected_packet][39:36] ||
              tx_desc_vc[(seq_endpoint_i*2) +: 2] !== descriptors[selected_packet][41:40] ||
              tx_desc_tag[(seq_endpoint_i*8) +: 8] !== descriptors[selected_packet][49:42] ||
              tx_desc_flit_count[(seq_endpoint_i*4) +: 4] !== descriptors[selected_packet][53:50])
            $fatal(1, "generated TX descriptor metadata mismatch for packet %0d", selected_packet);
          packet_tx_base[selected_packet] <=
            tx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
          descriptor_slot =
            tx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
          if (descriptor_slot < 0 || descriptor_slot >= BOUNDED_PACKET_SLOTS)
            $fatal(1, "generated TX descriptor slot is out of bounds: %0d", descriptor_slot);
          if (tx_slot_live[seq_endpoint_i][descriptor_slot])
            $fatal(1,
              "generated TX descriptor reuses live slot endpoint=%0d slot=%0d packet=%0d",
              seq_endpoint_i, descriptor_slot, selected_packet);
          tx_slot_live[seq_endpoint_i][descriptor_slot] <= 1'b1;
          tx_packet_queue[seq_endpoint_i*MAX_PACKETS + tx_packet_wr[seq_endpoint_i]] <=
            selected_packet;
          tx_packet_wr[seq_endpoint_i] <= tx_packet_wr[seq_endpoint_i] + 1;
`else
          selected_packet = tx_desc_base_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
`endif
`else
          selected_index = source_queue_meta[seq_endpoint_i][15:0] + source_position[seq_endpoint_i];
          selected_packet = source_order[selected_index];
          source_position[seq_endpoint_i] <= source_position[seq_endpoint_i] + 1;
`endif
          if (!rx_installed[selected_packet])
            $fatal(1, "TX descriptor accepted before RX descriptor for packet %0d", selected_packet);
          tx_submitted[selected_packet] <= 1'b1;
          tx_fire_count = tx_fire_count + 1;
        end

        if (rx_completion_valid[seq_endpoint_i] && rx_completion_ready[seq_endpoint_i]) begin
          selected_packet = completion_packet[seq_endpoint_i];
          if (!completion_shadow_valid[seq_endpoint_i])
            $fatal(1, "unexpected completion at endpoint %0d", seq_endpoint_i);
          if (rx_completion_source[(seq_endpoint_i*4) +: 4] !== descriptors[selected_packet][35:32] ||
              rx_completion_vc[(seq_endpoint_i*2) +: 2] !== descriptors[selected_packet][41:40] ||
              rx_completion_tag[(seq_endpoint_i*8) +: 8] !== descriptors[selected_packet][49:42])
            $fatal(1, "completion metadata mismatch for packet %0d", selected_packet);
          if (packet_completed[selected_packet])
            $fatal(1, "duplicate completion for packet %0d", selected_packet);
          packet_completed[selected_packet] <= 1'b1;
          completion_fire_count = completion_fire_count + 1;
          completion_shadow_valid[seq_endpoint_i] <= 1'b0;
        end

        if (rx_mem_write_valid[seq_endpoint_i] && rx_mem_write_ready[seq_endpoint_i]) begin
`ifdef GENERATED_COMMAND_SOURCE
          selected_packet =
            rx_mem_write_data[(seq_endpoint_i*DATA_W) + 4 +: 16];
          write_fragment =
            rx_mem_write_data[(seq_endpoint_i*DATA_W) + 20 +: 3];
`else
          selected_packet = rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
          write_fragment =
            (rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 5) & 7;
`endif
          if (selected_packet < 0 || selected_packet >= packet_count)
            $fatal(1, "destination write names invalid packet %0d", selected_packet);
          if (descriptors[selected_packet][39:36] != seq_endpoint_i[3:0])
            $fatal(1, "packet %0d written at wrong endpoint %0d", selected_packet, seq_endpoint_i);
`ifdef GENERATED_COMMAND_SOURCE
          if (rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] !==
              packet_rx_base[selected_packet] + write_fragment*32)
            $fatal(1,
              "RX packet-slot address mismatch endpoint=%0d packet=%0d fragment=%0d address=%h base=%h",
              seq_endpoint_i, selected_packet, write_fragment,
              rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W],
              packet_rx_base[selected_packet]);
`endif
          if (rx_mem_write_data[(seq_endpoint_i*DATA_W) +: DATA_W] !== memory_data(
                descriptors[selected_packet][35:32],
                selected_packet[15:0], write_fragment[2:0]))
            $fatal(1, "packet %0d destination data mismatch", selected_packet);
          write_fire_count = write_fire_count + 1;

          if (write_fragment + 1 == descriptors[selected_packet][53:50]) begin
            free_context = -1;
            for (seq_context_i = 0; seq_context_i < RX_CONTEXTS;
                 seq_context_i = seq_context_i + 1)
              if (live_context_valid[seq_endpoint_i*RX_CONTEXTS + seq_context_i] &&
                  live_context_packet[seq_endpoint_i*RX_CONTEXTS + seq_context_i] == selected_packet)
                free_context = seq_context_i;
            if (free_context < 0)
              $fatal(1, "completed packet %0d has no live context", selected_packet);
            live_context_valid[seq_endpoint_i*RX_CONTEXTS + free_context] <= 1'b0;
`ifdef GENERATED_COMMAND_SOURCE
            descriptor_slot = packet_rx_base[selected_packet] >> 8;
            rx_slot_live[seq_endpoint_i][descriptor_slot] <= 1'b0;
`endif
            completion_packet[seq_endpoint_i] <= selected_packet;
            completion_shadow_valid[seq_endpoint_i] <= 1'b1;
          end
        end
      end

      submitted_packets <= submitted_packets + tx_fire_count;
      completed_packets <= completed_packets + completion_fire_count;
      accepted_writes <= accepted_writes + write_fire_count;

      if (endpoint_protocol_error != 0)
        $fatal(1, "endpoint protocol error: %h", endpoint_protocol_error);
`ifdef SERIAL_PAIRED_SCHEDULER
`ifdef GENERATED_COMMAND_SOURCE
      if (command_generator_protocol_error || scheduler_protocol_error)
        $fatal(1, "descriptor command path protocol error generator=%0d scheduler=%0d",
          command_generator_protocol_error, scheduler_protocol_error);
`else
      if (prefetch_protocol_error || scheduler_protocol_error)
        $fatal(1, "descriptor command path protocol error prefetch=%0d scheduler=%0d",
          prefetch_protocol_error, scheduler_protocol_error);
`endif
`endif
      if (cycle > 0 && (cycle % 100000) == 0)
        $display("PROGRESS workload cycle=%0d submitted=%0d completed=%0d writes=%0d",
          cycle, submitted_packets, completed_packets, accepted_writes);
      if (cycle >= timeout_cycles)
        $fatal(1, "workload timeout cycle=%0d submitted=%0d completed=%0d", cycle,
          submitted_packets, completed_packets);
    end
  end

  task finish_and_check;
    integer aggregate_contention;
    integer aggregate_input_stalls;
    integer aggregate_max_occupancy;
    begin
      aggregate_contention = 0;
      aggregate_input_stalls = 0;
      aggregate_max_occupancy = 0;
      for (queue_i = 0; queue_i < 16; queue_i = queue_i + 1) begin
        aggregate_contention = aggregate_contention +
          router_contention_cycles[(queue_i*32) +: 32];
        aggregate_input_stalls = aggregate_input_stalls +
          router_input_stall_cycles[(queue_i*32) +: 32];
        if (router_max_input_occupancy[(queue_i*32) +: 32] > aggregate_max_occupancy)
          aggregate_max_occupancy = router_max_input_occupancy[(queue_i*32) +: 32];
      end
      if (submitted_packets != packet_count || completed_packets != packet_count)
        $fatal(1, "packet count mismatch expected=%0d submitted=%0d completed=%0d",
          packet_count, submitted_packets, completed_packets);
      if (accepted_writes != expected_flits)
        $fatal(1, "flit count mismatch expected=%0d writes=%0d",
          expected_flits, accepted_writes);
`ifdef SERIAL_PAIRED_SCHEDULER
`ifdef GENERATED_COMMAND_SOURCE
      if (!command_generator_done || generated_command_count != packet_count ||
          scheduler_accepted_command_count != packet_count ||
          scheduler_installed_receive_count != packet_count ||
          scheduler_submitted_transmit_count != packet_count ||
          serial_rx_position != packet_count || serial_tx_position != packet_count)
        $fatal(1,
          "command count mismatch generated=%0d accepted=%0d rx=%0d tx=%0d rx_pos=%0d tx_pos=%0d expected=%0d done=%0d",
          generated_command_count, scheduler_accepted_command_count,
          scheduler_installed_receive_count, scheduler_submitted_transmit_count,
          serial_rx_position, serial_tx_position, packet_count, command_generator_done);
      for (queue_i = 0; queue_i < 16; queue_i = queue_i + 1) begin
        if (tx_slot_live[queue_i] != 0 || rx_slot_live[queue_i] != 0)
          $fatal(1, "bounded packet slots remain live at endpoint %0d tx=%h rx=%h",
            queue_i, tx_slot_live[queue_i], rx_slot_live[queue_i]);
        if (tx_packet_rd[queue_i] != tx_packet_wr[queue_i])
          $fatal(1, "TX packet-slot queue did not drain at endpoint %0d rd=%0d wr=%0d",
            queue_i, tx_packet_rd[queue_i], tx_packet_wr[queue_i]);
      end
`else
      if (scheduler_accepted_command_count != packet_count ||
          scheduler_installed_receive_count != packet_count ||
          scheduler_submitted_transmit_count != packet_count ||
          prefetch_request_count != packet_count ||
          prefetch_response_count != packet_count ||
          prefetch_delivered_command_count != packet_count)
        $fatal(1,
          "command count mismatch req=%0d rsp=%0d delivered=%0d accepted=%0d rx=%0d tx=%0d expected=%0d",
          prefetch_request_count, prefetch_response_count,
          prefetch_delivered_command_count,
          scheduler_accepted_command_count, scheduler_installed_receive_count,
          scheduler_submitted_transmit_count, packet_count);
`endif
`endif
      for (packet_i = 0; packet_i < packet_count; packet_i = packet_i + 1)
        if (!rx_installed[packet_i] || !tx_submitted[packet_i] || !packet_completed[packet_i])
          $fatal(1, "packet %0d did not traverse the complete endpoint path", packet_i);
      $display(
        "PASS workload packets=%0d flits=%0d cycles=%0d contention=%0d input_stalls=%0d max_occupancy=%0d",
        packet_count, accepted_writes, drain_cycle, aggregate_contention,
        aggregate_input_stalls, aggregate_max_occupancy);
      $finish;
    end
  endtask

  initial begin
    if (!$value$plusargs("PACKET_COUNT=%d", packet_count) || packet_count <= 0 ||
        packet_count > MAX_PACKETS)
      $fatal(1, "PACKET_COUNT must be in [1, %0d]", MAX_PACKETS);
    if (!$value$plusargs("EXPECTED_FLITS=%d", expected_flits) || expected_flits <= 0)
      $fatal(1, "EXPECTED_FLITS must be positive");
    plusarg_status = $value$plusargs("TIMEOUT_CYCLES=%d", timeout_cycles);
    if (!$value$plusargs("DESC_MEM=%s", descriptor_mem) ||
        !$value$plusargs("CMD_ORDER_MEM=%s", command_order_mem) ||
        !$value$plusargs("SRC_ORDER_MEM=%s", source_order_mem) ||
        !$value$plusargs("DST_ORDER_MEM=%s", destination_order_mem) ||
        !$value$plusargs("SRC_META_MEM=%s", source_meta_mem) ||
        !$value$plusargs("DST_META_MEM=%s", destination_meta_mem))
      $fatal(1, "all workload memory paths are required");
    $readmemh(descriptor_mem, descriptors, 0, packet_count - 1);
    $readmemh(command_order_mem, command_order, 0, packet_count - 1);
    $readmemh(source_order_mem, source_order, 0, packet_count - 1);
    $readmemh(destination_order_mem, destination_order, 0, packet_count - 1);
    $readmemh(source_meta_mem, source_queue_meta);
    $readmemh(destination_meta_mem, destination_queue_meta);

    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    while (completed_packets < packet_count) @(negedge clk);
    drain_cycle = cycle;
    repeat (3) @(negedge clk);
    finish_and_check();
  end
endmodule
