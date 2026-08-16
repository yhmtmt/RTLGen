`timescale 1ns/1ps

// Runtime-loaded workload replay for the exact endpoint plus 4x4 mesh RTL.
// Descriptor word layout: release[31:0], source[35:32], destination[39:36],
// VC[41:40], tag[49:42], flit_count[53:50]. Packet ID is the array index.
module noc_sram_packet_mesh4x4_workload_tb;
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 24;
  localparam integer MAX_PACKETS = 12000;
  localparam integer RX_CONTEXTS = 8;

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
  integer tx_fire_count;
  integer completion_fire_count;
  integer write_fire_count;
  integer completion_packet [0:15];
  reg [15:0] completion_shadow_valid = 0;

  reg [95:0] descriptors [0:MAX_PACKETS-1];
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

  reg [15:0] tx_desc_valid = 0;
  wire [15:0] tx_desc_ready;
  reg [63:0] tx_desc_destination = 0;
  reg [31:0] tx_desc_vc = 0;
  reg [127:0] tx_desc_tag = 0;
  reg [16*ADDR_W-1:0] tx_desc_base_addr = 0;
  reg [63:0] tx_desc_flit_count = 0;
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

  reg [15:0] rx_desc_valid = 0;
  wire [15:0] rx_desc_ready;
  reg [63:0] rx_desc_source = 0;
  reg [31:0] rx_desc_vc = 0;
  reg [127:0] rx_desc_tag = 0;
  reg [16*ADDR_W-1:0] rx_desc_base_addr = 0;
  reg [63:0] rx_desc_flit_count = 0;
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
  string source_order_mem;
  string destination_order_mem;
  string source_meta_mem;
  string destination_meta_mem;

  function [DATA_W-1:0] memory_data;
    input [3:0] source;
    input [ADDR_W-1:0] address;
    reg [15:0] packet_id;
    reg [2:0] fragment;
    begin
      packet_id = address[23:8];
      fragment = address[7:5];
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
      for (seq_endpoint_i = 0; seq_endpoint_i < 16; seq_endpoint_i = seq_endpoint_i + 1) begin
        source_position[seq_endpoint_i] <= 0;
        destination_position[seq_endpoint_i] <= 0;
        completion_packet[seq_endpoint_i] <= 0;
        pending_read_rd[seq_endpoint_i] <= 0;
        pending_read_wr[seq_endpoint_i] <= 0;
        pending_read_count[seq_endpoint_i] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      tx_fire_count = 0;
      completion_fire_count = 0;
      write_fire_count = 0;

      for (seq_endpoint_i = 0; seq_endpoint_i < 16; seq_endpoint_i = seq_endpoint_i + 1) begin
        if (!tx_mem_rsp_valid[seq_endpoint_i] || tx_mem_rsp_ready[seq_endpoint_i]) begin
          if (pending_read_count[seq_endpoint_i] > 0) begin
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b1;
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) +: DATA_W] <= memory_data(
              seq_endpoint_i[3:0],
              pending_read_addr[seq_endpoint_i*8 + pending_read_rd[seq_endpoint_i]]);
            pending_read_rd[seq_endpoint_i] <= (pending_read_rd[seq_endpoint_i] + 1) % 8;
            if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
              pending_read_addr[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
                tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
              pending_read_wr[seq_endpoint_i] <= (pending_read_wr[seq_endpoint_i] + 1) % 8;
            end else begin
              pending_read_count[seq_endpoint_i] <= pending_read_count[seq_endpoint_i] - 1;
            end
          end else if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
            // Empty-queue bypass: a request accepted at this edge becomes the
            // response consumed at the following edge.
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b1;
            tx_mem_rsp_data[(seq_endpoint_i*DATA_W) +: DATA_W] <= memory_data(
              seq_endpoint_i[3:0], tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W]);
          end else begin
            tx_mem_rsp_valid[seq_endpoint_i] <= 1'b0;
          end
        end else if (tx_mem_req_valid[seq_endpoint_i] && tx_mem_req_ready[seq_endpoint_i]) begin
          pending_read_addr[seq_endpoint_i*8 + pending_read_wr[seq_endpoint_i]] <=
            tx_mem_req_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W];
          pending_read_wr[seq_endpoint_i] <= (pending_read_wr[seq_endpoint_i] + 1) % 8;
          pending_read_count[seq_endpoint_i] <= pending_read_count[seq_endpoint_i] + 1;
        end

        if (rx_desc_valid[seq_endpoint_i] && rx_desc_ready[seq_endpoint_i]) begin
          selected_index = destination_queue_meta[seq_endpoint_i][15:0] +
            destination_position[seq_endpoint_i];
          selected_packet = destination_order[selected_index];
          rx_installed[selected_packet] <= 1'b1;
          destination_position[seq_endpoint_i] <= destination_position[seq_endpoint_i] + 1;
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
          selected_index = source_queue_meta[seq_endpoint_i][15:0] + source_position[seq_endpoint_i];
          selected_packet = source_order[selected_index];
          if (!rx_installed[selected_packet])
            $fatal(1, "TX descriptor accepted before RX descriptor for packet %0d", selected_packet);
          tx_submitted[selected_packet] <= 1'b1;
          source_position[seq_endpoint_i] <= source_position[seq_endpoint_i] + 1;
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
          selected_packet = rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 8;
          write_fragment =
            (rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] >> 5) & 7;
          if (selected_packet < 0 || selected_packet >= packet_count)
            $fatal(1, "destination write names invalid packet %0d", selected_packet);
          if (descriptors[selected_packet][39:36] != seq_endpoint_i[3:0])
            $fatal(1, "packet %0d written at wrong endpoint %0d", selected_packet, seq_endpoint_i);
          if (rx_mem_write_data[(seq_endpoint_i*DATA_W) +: DATA_W] !== memory_data(
                descriptors[selected_packet][35:32],
                (selected_packet << 8) |
                  ((rx_mem_write_addr[(seq_endpoint_i*ADDR_W) +: ADDR_W] & 24'h0000ff))))
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
        !$value$plusargs("SRC_ORDER_MEM=%s", source_order_mem) ||
        !$value$plusargs("DST_ORDER_MEM=%s", destination_order_mem) ||
        !$value$plusargs("SRC_META_MEM=%s", source_meta_mem) ||
        !$value$plusargs("DST_META_MEM=%s", destination_meta_mem))
      $fatal(1, "all workload memory paths are required");
    $readmemh(descriptor_mem, descriptors, 0, packet_count - 1);
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
