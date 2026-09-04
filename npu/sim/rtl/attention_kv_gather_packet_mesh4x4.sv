`timescale 1ns/1ps

// Concurrent exact K/V packet transport over the existing endpoint-backed
// deterministic-XY mesh. Receive state is installed before transmit release.
module attention_kv_gather_packet_mesh4x4 (
  input wire clk,
  input wire rst_n,

  input wire [15:0] cmd_valid,
  output wire [15:0] cmd_ready,
  input wire [16*5-1:0] cmd_layer,
  input wire [16*7-1:0] cmd_tile,
  input wire [15:0] cmd_operation_consume,
  input wire [15:0] cmd_source_hbm,
  input wire [16*4-1:0] cmd_source_endpoint,
  input wire [16*4-1:0] cmd_destination_cluster,
  input wire [16*20-1:0] cmd_canonical_byte_address,
  input wire [16*34-1:0] cmd_source_byte_address,
  input wire [15:0] cmd_destination_is_resident_cache,
  input wire [16*34-1:0] cmd_destination_byte_address,
  input wire [16*12-1:0] cmd_packet_index,
  input wire [16*8-1:0] cmd_tag,
  input wire [16*4-1:0] cmd_flit_count,
  input wire [15:0] cmd_descriptor_last,
  input wire [15:0] cmd_schedule_last,

  output wire [15:0] source_req_valid,
  input wire [15:0] source_req_ready,
  output wire [15:0] source_req_is_hbm,
  output wire [16*33-1:0] source_req_byte_address,
  input wire [15:0] source_rsp_valid,
  output wire [15:0] source_rsp_ready,
  input wire [16*256-1:0] source_rsp_data,

  output wire [15:0] resident_write_valid,
  input wire [15:0] resident_write_ready,
  output wire [16*33-1:0] resident_write_byte_address,
  output wire [16*256-1:0] resident_write_data,

  output wire [15:0] canonical_ingress_valid,
  input wire [15:0] canonical_ingress_ready,
  output wire [16*5-1:0] canonical_ingress_layer,
  output wire [16*7-1:0] canonical_ingress_tile,
  output wire [16*20-1:0] canonical_ingress_tile_byte_address,
  output wire [16*256-1:0] canonical_ingress_data,

  output wire [15:0] endpoint_protocol_error,
  output wire [15:0] packet_completion_valid,
  output wire [16*4-1:0] packet_completion_source,
  output wire [16*2-1:0] packet_completion_vc,
  output wire [16*8-1:0] packet_completion_tag,
  output wire [16*32-1:0] router_accepted_flit_count,
  output wire [16*32-1:0] router_forwarded_flit_count,
  output wire [16*32-1:0] router_input_stall_cycles,
  output wire [16*32-1:0] router_output_stall_cycles,
  output wire [16*32-1:0] router_contention_cycles,
  output wire [16*32-1:0] router_current_input_occupancy,
  output wire [16*32-1:0] router_max_input_occupancy,
  output wire [16*5*32-1:0] router_route_flit_count,
  output reg [24:0] accepted_packet_command_count,
  output reg [12:0] submitted_descriptor_count,
  output reg schedule_packet_submitted,
  output reg command_protocol_error,
  output wire protocol_error
);
  reg [15:0] receive_installed_q;
  reg [3:0] destination_rr_q [0:15];

  reg [15:0] tx_desc_valid_r;
  wire [15:0] tx_desc_ready_w;
  reg [16*4-1:0] tx_desc_destination_r;
  reg [16*2-1:0] tx_desc_vc_r;
  reg [16*8-1:0] tx_desc_tag_r;
  reg [16*34-1:0] tx_desc_base_addr_r;
  reg [16*4-1:0] tx_desc_flit_count_r;

  reg [15:0] rx_desc_valid_r;
  wire [15:0] rx_desc_ready_w;
  reg [16*4-1:0] rx_desc_source_r;
  reg [16*2-1:0] rx_desc_vc_r;
  reg [16*8-1:0] rx_desc_tag_r;
  reg [16*34-1:0] rx_desc_base_addr_r;
  reg [16*4-1:0] rx_desc_flit_count_r;

  wire [15:0] mesh_tx_mem_req_valid;
  wire [16*34-1:0] mesh_tx_mem_req_addr;
  wire [15:0] mesh_tx_mem_rsp_ready;
  wire [15:0] mesh_rx_mem_write_valid;
  reg [15:0] mesh_rx_mem_write_ready;
  wire [16*34-1:0] mesh_rx_mem_write_addr;
  wire [16*256-1:0] mesh_rx_mem_write_data;

  reg [15:0] command_fields_valid_r;
  reg [15:0] destination_candidate_valid_r;
  reg [3:0] destination_candidate_source_r [0:15];
  reg [4:0] accepted_command_count_r;
  reg [4:0] submitted_descriptor_count_r;
  reg schedule_packet_submitted_r;
  integer source_i;
  integer destination_i;
  integer scan_offset_i;
  integer scan_source_i;
  integer accepted_source_i;
  integer reset_i;

  assign cmd_ready = tx_desc_valid_r & tx_desc_ready_w;
  assign source_req_valid = mesh_tx_mem_req_valid;
  assign source_rsp_ready = mesh_tx_mem_rsp_ready;
  assign protocol_error = command_protocol_error | (|endpoint_protocol_error);

  genvar endpoint_g;
  generate
    for (endpoint_g = 0; endpoint_g < 16; endpoint_g = endpoint_g + 1) begin : gen_ports
      assign source_req_is_hbm[endpoint_g] =
        mesh_tx_mem_req_addr[(endpoint_g*34) + 33];
      assign source_req_byte_address[(endpoint_g*33) +: 33] =
        mesh_tx_mem_req_addr[(endpoint_g*34) +: 33];

      assign resident_write_valid[endpoint_g] =
        mesh_rx_mem_write_valid[endpoint_g] &&
        mesh_rx_mem_write_addr[(endpoint_g*34) + 33];
      assign resident_write_byte_address[(endpoint_g*33) +: 33] =
        mesh_rx_mem_write_addr[(endpoint_g*34) +: 33];
      assign resident_write_data[(endpoint_g*256) +: 256] =
        mesh_rx_mem_write_data[(endpoint_g*256) +: 256];

      assign canonical_ingress_valid[endpoint_g] =
        mesh_rx_mem_write_valid[endpoint_g] &&
        !mesh_rx_mem_write_addr[(endpoint_g*34) + 33];
      assign canonical_ingress_layer[(endpoint_g*5) +: 5] =
        mesh_rx_mem_write_addr[(endpoint_g*34) + 27 +: 5];
      assign canonical_ingress_tile[(endpoint_g*7) +: 7] =
        mesh_rx_mem_write_addr[(endpoint_g*34) + 20 +: 7];
      assign canonical_ingress_tile_byte_address[(endpoint_g*20) +: 20] =
        mesh_rx_mem_write_addr[(endpoint_g*34) +: 20];
      assign canonical_ingress_data[(endpoint_g*256) +: 256] =
        mesh_rx_mem_write_data[(endpoint_g*256) +: 256];
    end
  endgenerate

  always @(*) begin
    command_fields_valid_r = 16'd0;
    destination_candidate_valid_r = 16'd0;
    tx_desc_valid_r = 16'd0;
    tx_desc_destination_r = 0;
    tx_desc_vc_r = 0;
    tx_desc_tag_r = 0;
    tx_desc_base_addr_r = 0;
    tx_desc_flit_count_r = 0;
    rx_desc_valid_r = 16'd0;
    rx_desc_source_r = 0;
    rx_desc_vc_r = 0;
    rx_desc_tag_r = 0;
    rx_desc_base_addr_r = 0;
    rx_desc_flit_count_r = 0;
    mesh_rx_mem_write_ready = 16'd0;

    for (source_i = 0; source_i < 16; source_i = source_i + 1) begin
      command_fields_valid_r[source_i] =
        !command_protocol_error &&
        cmd_source_endpoint[(source_i*4) +: 4] == source_i[3:0] &&
        cmd_flit_count[(source_i*4) +: 4] == 4'd8 &&
        cmd_tag[(source_i*8) +: 8] ==
          cmd_packet_index[(source_i*12) +: 8] &&
        cmd_destination_is_resident_cache[source_i] ==
          !cmd_operation_consume[source_i] &&
        !cmd_source_byte_address[(source_i*34) + 33] &&
        !cmd_destination_byte_address[(source_i*34) + 33];
      if (cmd_valid[source_i] && receive_installed_q[source_i] &&
          command_fields_valid_r[source_i]) begin
        tx_desc_valid_r[source_i] = 1'b1;
        tx_desc_destination_r[(source_i*4) +: 4] =
          cmd_destination_cluster[(source_i*4) +: 4];
        tx_desc_tag_r[(source_i*8) +: 8] = cmd_tag[(source_i*8) +: 8];
        tx_desc_base_addr_r[(source_i*34) +: 34] = {
          cmd_source_hbm[source_i],
          cmd_source_byte_address[(source_i*34) +: 33]
        };
        tx_desc_flit_count_r[(source_i*4) +: 4] = 4'd8;
      end
    end

    for (destination_i = 0; destination_i < 16; destination_i = destination_i + 1) begin
      destination_candidate_source_r[destination_i] = 4'd0;
      for (scan_offset_i = 0; scan_offset_i < 16; scan_offset_i = scan_offset_i + 1) begin
        scan_source_i = destination_rr_q[destination_i] + scan_offset_i;
        if (scan_source_i >= 16)
          scan_source_i = scan_source_i - 16;
        if (!destination_candidate_valid_r[destination_i] &&
            cmd_valid[scan_source_i] && !receive_installed_q[scan_source_i] &&
            command_fields_valid_r[scan_source_i] &&
            cmd_destination_cluster[(scan_source_i*4) +: 4] == destination_i[3:0]) begin
          destination_candidate_valid_r[destination_i] = 1'b1;
          destination_candidate_source_r[destination_i] = scan_source_i[3:0];
        end
      end
      if (destination_candidate_valid_r[destination_i]) begin
        scan_source_i = destination_candidate_source_r[destination_i];
        rx_desc_valid_r[destination_i] = 1'b1;
        rx_desc_source_r[(destination_i*4) +: 4] = scan_source_i[3:0];
        rx_desc_tag_r[(destination_i*8) +: 8] = cmd_tag[(scan_source_i*8) +: 8];
        if (cmd_destination_is_resident_cache[scan_source_i]) begin
          rx_desc_base_addr_r[(destination_i*34) +: 34] = {
            1'b1, cmd_destination_byte_address[(scan_source_i*34) +: 33]
          };
        end else begin
          rx_desc_base_addr_r[(destination_i*34) +: 34] = {
            2'b00,
            cmd_layer[(scan_source_i*5) +: 5],
            cmd_tile[(scan_source_i*7) +: 7],
            cmd_canonical_byte_address[(scan_source_i*20) +: 20]
          };
        end
        rx_desc_flit_count_r[(destination_i*4) +: 4] = 4'd8;
      end

      if (mesh_rx_mem_write_addr[(destination_i*34) + 33])
        mesh_rx_mem_write_ready[destination_i] = resident_write_ready[destination_i];
      else
        mesh_rx_mem_write_ready[destination_i] = canonical_ingress_ready[destination_i];
    end
  end

  always @(*) begin
    accepted_command_count_r = 5'd0;
    submitted_descriptor_count_r = 5'd0;
    schedule_packet_submitted_r = 1'b0;
    for (accepted_source_i = 0; accepted_source_i < 16;
         accepted_source_i = accepted_source_i + 1) begin
      if (tx_desc_valid_r[accepted_source_i] && tx_desc_ready_w[accepted_source_i]) begin
        accepted_command_count_r = accepted_command_count_r + 1'b1;
        if (cmd_descriptor_last[accepted_source_i])
          submitted_descriptor_count_r = submitted_descriptor_count_r + 1'b1;
        if (cmd_schedule_last[accepted_source_i])
          schedule_packet_submitted_r = 1'b1;
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      receive_installed_q <= 16'd0;
      accepted_packet_command_count <= 25'd0;
      submitted_descriptor_count <= 13'd0;
      schedule_packet_submitted <= 1'b0;
      command_protocol_error <= 1'b0;
      for (reset_i = 0; reset_i < 16; reset_i = reset_i + 1)
        destination_rr_q[reset_i] <= 4'd0;
    end else begin
      accepted_packet_command_count <=
        accepted_packet_command_count + accepted_command_count_r;
      submitted_descriptor_count <=
        submitted_descriptor_count + submitted_descriptor_count_r;
      if (schedule_packet_submitted_r)
        schedule_packet_submitted <= 1'b1;
      for (source_i = 0; source_i < 16; source_i = source_i + 1) begin
        if (cmd_valid[source_i] && !command_fields_valid_r[source_i])
          command_protocol_error <= 1'b1;
        if (tx_desc_valid_r[source_i] && tx_desc_ready_w[source_i])
          receive_installed_q[source_i] <= 1'b0;
      end
      for (destination_i = 0; destination_i < 16; destination_i = destination_i + 1) begin
        if (rx_desc_valid_r[destination_i] && rx_desc_ready_w[destination_i]) begin
          receive_installed_q[destination_candidate_source_r[destination_i]] <= 1'b1;
          destination_rr_q[destination_i] <=
            destination_candidate_source_r[destination_i] + 1'b1;
        end
      end
    end
  end

  noc_sram_packet_mesh4x4 #(
    .ADDR_W(34),
    .TX_DESC_DEPTH(8),
    .TX_OUTSTANDING(8),
    .RX_CONTEXTS(8),
    .ROUTER_FIFO_DEPTH(4)
  ) u_mesh (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(tx_desc_valid_r), .tx_desc_ready(tx_desc_ready_w),
    .tx_desc_destination(tx_desc_destination_r), .tx_desc_vc(tx_desc_vc_r),
    .tx_desc_tag(tx_desc_tag_r), .tx_desc_base_addr(tx_desc_base_addr_r),
    .tx_desc_flit_count(tx_desc_flit_count_r),
    .tx_mem_req_valid(mesh_tx_mem_req_valid), .tx_mem_req_ready(source_req_ready),
    .tx_mem_req_addr(mesh_tx_mem_req_addr), .tx_mem_rsp_valid(source_rsp_valid),
    .tx_mem_rsp_ready(mesh_tx_mem_rsp_ready), .tx_mem_rsp_data(source_rsp_data),
    .rx_desc_valid(rx_desc_valid_r), .rx_desc_ready(rx_desc_ready_w),
    .rx_desc_source(rx_desc_source_r), .rx_desc_vc(rx_desc_vc_r),
    .rx_desc_tag(rx_desc_tag_r), .rx_desc_base_addr(rx_desc_base_addr_r),
    .rx_desc_flit_count(rx_desc_flit_count_r),
    .rx_mem_write_valid(mesh_rx_mem_write_valid),
    .rx_mem_write_ready(mesh_rx_mem_write_ready),
    .rx_mem_write_addr(mesh_rx_mem_write_addr),
    .rx_mem_write_data(mesh_rx_mem_write_data),
    .rx_completion_valid(packet_completion_valid), .rx_completion_ready(16'hffff),
    .rx_completion_source(packet_completion_source),
    .rx_completion_vc(packet_completion_vc),
    .rx_completion_tag(packet_completion_tag),
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
endmodule
