`timescale 1ns/1ps

// Five-port deterministic-XY flit router. Each physical input is demultiplexed
// into a bounded FIFO per virtual channel. Output holding registers preserve
// the complete flit while downstream ready is deasserted.
module noc_segmented_mesh_router #(
  parameter integer DATA_W = 256,
  parameter integer DEST_W = 4,
  parameter integer SOURCE_W = 4,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer VC_COUNT = 4,
  parameter integer FIFO_DEPTH = 4,
  parameter integer X_COORD = 0,
  parameter integer Y_COORD = 0,
  parameter integer COUNTER_W = 32
) (
  input  wire                         clk,
  input  wire                         rst_n,
  input  wire [4:0]                   in_valid,
  output wire [4:0]                   in_ready,
  input  wire [5*DEST_W-1:0]          in_dest,
  input  wire [5*SOURCE_W-1:0]        in_source,
  input  wire [5*TAG_W-1:0]           in_tag,
  input  wire [5*FRAGMENT_W-1:0]      in_fragment,
  input  wire [4:0]                   in_last,
  input  wire [5*VC_W-1:0]            in_vc,
  input  wire [5*DATA_W-1:0]          in_data,
  output wire [4:0]                   out_valid,
  input  wire [4:0]                   out_ready,
  output wire [5*DEST_W-1:0]          out_dest,
  output wire [5*SOURCE_W-1:0]        out_source,
  output wire [5*TAG_W-1:0]           out_tag,
  output wire [5*FRAGMENT_W-1:0]      out_fragment,
  output wire [4:0]                   out_last,
  output wire [5*VC_W-1:0]            out_vc,
  output wire [5*DATA_W-1:0]          out_data,
  output reg  [COUNTER_W-1:0]         accepted_flit_count,
  output reg  [COUNTER_W-1:0]         forwarded_flit_count,
  output reg  [COUNTER_W-1:0]         input_stall_cycles,
  output reg  [COUNTER_W-1:0]         output_stall_cycles,
  output reg  [COUNTER_W-1:0]         arbitration_contention_cycles,
  output wire [COUNTER_W-1:0]         current_input_occupancy,
  output reg  [COUNTER_W-1:0]         max_input_occupancy,
  output reg  [5*COUNTER_W-1:0]       route_flit_count
);
  localparam integer PORTS = 5;
  localparam integer INPUTS = PORTS * VC_COUNT;
  localparam integer INPUT_INDEX_W = (INPUTS <= 1) ? 1 : $clog2(INPUTS);
  localparam integer FIFO_COUNT_W = (FIFO_DEPTH <= 1) ? 1 : $clog2(FIFO_DEPTH + 1);
  localparam integer FLIT_W = DATA_W + DEST_W + SOURCE_W + TAG_W + FRAGMENT_W + 1 + VC_W;
  localparam integer DATA_LSB = 0;
  localparam integer VC_LSB = DATA_LSB + DATA_W;
  localparam integer LAST_LSB = VC_LSB + VC_W;
  localparam integer FRAGMENT_LSB = LAST_LSB + 1;
  localparam integer TAG_LSB = FRAGMENT_LSB + FRAGMENT_W;
  localparam integer SOURCE_LSB = TAG_LSB + TAG_W;
  localparam integer DEST_LSB = SOURCE_LSB + SOURCE_W;
  localparam integer NORTH = 0;
  localparam integer SOUTH = 1;
  localparam integer EAST = 2;
  localparam integer WEST = 3;
  localparam integer LOCAL = 4;

  wire [INPUTS-1:0] fifo_in_valid;
  wire [INPUTS-1:0] fifo_in_ready;
  wire [INPUTS*FLIT_W-1:0] fifo_in_bus;
  wire [INPUTS-1:0] fifo_out_valid;
  reg  [INPUTS-1:0] fifo_out_ready_r;
  wire [INPUTS*FLIT_W-1:0] fifo_out_bus;
  wire [INPUTS*FIFO_COUNT_W-1:0] fifo_occupancy_bus;

  reg [4:0] out_valid_q;
  reg [FLIT_W-1:0] out_flit_q [0:PORTS-1];
  reg [INPUT_INDEX_W-1:0] rr_cursor_q [0:PORTS-1];
  reg [PORTS*INPUTS-1:0] route_request_r;
  reg [4:0] grant_valid_r;
  reg [INPUT_INDEX_W-1:0] grant_index_r [0:PORTS-1];
  reg [FLIT_W-1:0] grant_flit_r [0:PORTS-1];
  reg [4:0] candidate_seen_r;
  reg [COUNTER_W-1:0] occupancy_sum_r;
  reg any_input_stall_r;
  reg any_output_stall_r;
  reg any_contention_r;

  integer comb_port_i;
  integer comb_input_i;
  integer comb_output_i;
  integer comb_scan_i;
  integer comb_grant_i;
  integer scan_index_i;
  integer accepted_i;
  integer forwarded_i;
  integer seq_port_i;
  integer seq_output_i;

  function automatic [FLIT_W-1:0] pack_flit;
    input [DEST_W-1:0] destination;
    input [SOURCE_W-1:0] source;
    input [TAG_W-1:0] tag;
    input [FRAGMENT_W-1:0] fragment;
    input last;
    input [VC_W-1:0] vc;
    input [DATA_W-1:0] data;
    begin
      pack_flit = {destination, source, tag, fragment, last, vc, data};
    end
  endfunction

  function automatic integer route_port;
    input [DEST_W-1:0] destination;
    integer destination_x;
    integer destination_y;
    begin
      destination_x = destination[1:0];
      destination_y = destination[3:2];
      if (destination_x < X_COORD)
        route_port = WEST;
      else if (destination_x > X_COORD)
        route_port = EAST;
      else if (destination_y < Y_COORD)
        route_port = NORTH;
      else if (destination_y > Y_COORD)
        route_port = SOUTH;
      else
        route_port = LOCAL;
    end
  endfunction

  genvar port_g;
  genvar vc_g;
  generate
    for (port_g = 0; port_g < PORTS; port_g = port_g + 1) begin : gen_ports
      for (vc_g = 0; vc_g < VC_COUNT; vc_g = vc_g + 1) begin : gen_vcs
        localparam integer FIFO_INDEX = (port_g * VC_COUNT) + vc_g;
        assign fifo_in_valid[FIFO_INDEX] = in_valid[port_g]
            && (in_vc[(port_g * VC_W) +: VC_W] == vc_g[VC_W-1:0]);
        assign fifo_in_bus[(FIFO_INDEX * FLIT_W) +: FLIT_W] = pack_flit(
            in_dest[(port_g * DEST_W) +: DEST_W],
            in_source[(port_g * SOURCE_W) +: SOURCE_W],
            in_tag[(port_g * TAG_W) +: TAG_W],
            in_fragment[(port_g * FRAGMENT_W) +: FRAGMENT_W],
            in_last[port_g],
            in_vc[(port_g * VC_W) +: VC_W],
            in_data[(port_g * DATA_W) +: DATA_W]);
        noc_ready_valid_fifo #(
          .WIDTH(FLIT_W),
          .DEPTH(FIFO_DEPTH)
        ) u_fifo (
          .clk(clk),
          .rst_n(rst_n),
          .in_valid(fifo_in_valid[FIFO_INDEX]),
          .in_ready(fifo_in_ready[FIFO_INDEX]),
          .in_data(fifo_in_bus[(FIFO_INDEX * FLIT_W) +: FLIT_W]),
          .out_valid(fifo_out_valid[FIFO_INDEX]),
          .out_ready(fifo_out_ready_r[FIFO_INDEX]),
          .out_data(fifo_out_bus[(FIFO_INDEX * FLIT_W) +: FLIT_W]),
          .occupancy(fifo_occupancy_bus[(FIFO_INDEX * FIFO_COUNT_W) +: FIFO_COUNT_W]),
          .max_occupancy()
        );
      end
      assign in_ready[port_g] =
          fifo_in_ready[(port_g * VC_COUNT) + in_vc[(port_g * VC_W) +: VC_W]];
      assign out_valid[port_g] = out_valid_q[port_g];
      assign out_data[(port_g * DATA_W) +: DATA_W] =
          out_flit_q[port_g][DATA_LSB +: DATA_W];
      assign out_vc[(port_g * VC_W) +: VC_W] =
          out_flit_q[port_g][VC_LSB +: VC_W];
      assign out_last[port_g] = out_flit_q[port_g][LAST_LSB];
      assign out_fragment[(port_g * FRAGMENT_W) +: FRAGMENT_W] =
          out_flit_q[port_g][FRAGMENT_LSB +: FRAGMENT_W];
      assign out_tag[(port_g * TAG_W) +: TAG_W] =
          out_flit_q[port_g][TAG_LSB +: TAG_W];
      assign out_source[(port_g * SOURCE_W) +: SOURCE_W] =
          out_flit_q[port_g][SOURCE_LSB +: SOURCE_W];
      assign out_dest[(port_g * DEST_W) +: DEST_W] =
          out_flit_q[port_g][DEST_LSB +: DEST_W];
    end
  endgenerate

  assign current_input_occupancy = occupancy_sum_r;

  always @(*) begin
    fifo_out_ready_r = {INPUTS{1'b0}};
    route_request_r = {(PORTS * INPUTS){1'b0}};
    grant_valid_r = 5'b0;
    candidate_seen_r = 5'b0;
    occupancy_sum_r = {COUNTER_W{1'b0}};
    any_input_stall_r = 1'b0;
    any_output_stall_r = 1'b0;
    any_contention_r = 1'b0;
    for (comb_output_i = 0; comb_output_i < PORTS; comb_output_i = comb_output_i + 1) begin
      grant_index_r[comb_output_i] = {INPUT_INDEX_W{1'b0}};
      grant_flit_r[comb_output_i] = {FLIT_W{1'b0}};
    end
    for (comb_input_i = 0; comb_input_i < INPUTS; comb_input_i = comb_input_i + 1) begin
      occupancy_sum_r = occupancy_sum_r
          + fifo_occupancy_bus[(comb_input_i * FIFO_COUNT_W) +: FIFO_COUNT_W];
      for (comb_output_i = 0; comb_output_i < PORTS; comb_output_i = comb_output_i + 1) begin
        route_request_r[(comb_output_i * INPUTS) + comb_input_i] =
            fifo_out_valid[comb_input_i]
            && (route_port(fifo_out_bus[(comb_input_i * FLIT_W) + DEST_LSB +: DEST_W])
                == comb_output_i);
      end
    end
    for (comb_port_i = 0; comb_port_i < PORTS; comb_port_i = comb_port_i + 1) begin
      if (in_valid[comb_port_i] && !in_ready[comb_port_i])
        any_input_stall_r = 1'b1;
      if (out_valid_q[comb_port_i] && !out_ready[comb_port_i])
        any_output_stall_r = 1'b1;
    end
    for (comb_output_i = 0; comb_output_i < PORTS; comb_output_i = comb_output_i + 1) begin
      for (comb_scan_i = 0; comb_scan_i < INPUTS; comb_scan_i = comb_scan_i + 1) begin
        scan_index_i = rr_cursor_q[comb_output_i] + comb_scan_i;
        if (scan_index_i >= INPUTS)
          scan_index_i = scan_index_i - INPUTS;
        if (route_request_r[(comb_output_i * INPUTS) + scan_index_i]) begin
          if (candidate_seen_r[comb_output_i])
            any_contention_r = 1'b1;
          candidate_seen_r[comb_output_i] = 1'b1;
          if (!grant_valid_r[comb_output_i]) begin
            grant_valid_r[comb_output_i] = 1'b1;
            grant_index_r[comb_output_i] = scan_index_i[INPUT_INDEX_W-1:0];
          end
        end
      end
      for (comb_grant_i = 0; comb_grant_i < INPUTS; comb_grant_i = comb_grant_i + 1) begin
        if (grant_valid_r[comb_output_i]
            && (grant_index_r[comb_output_i] == comb_grant_i[INPUT_INDEX_W-1:0]))
          grant_flit_r[comb_output_i] =
              fifo_out_bus[(comb_grant_i * FLIT_W) +: FLIT_W];
      end
      if ((!out_valid_q[comb_output_i] || out_ready[comb_output_i]) && grant_valid_r[comb_output_i])
        fifo_out_ready_r[grant_index_r[comb_output_i]] = 1'b1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid_q <= 5'b0;
      accepted_flit_count <= {COUNTER_W{1'b0}};
      forwarded_flit_count <= {COUNTER_W{1'b0}};
      input_stall_cycles <= {COUNTER_W{1'b0}};
      output_stall_cycles <= {COUNTER_W{1'b0}};
      arbitration_contention_cycles <= {COUNTER_W{1'b0}};
      max_input_occupancy <= {COUNTER_W{1'b0}};
      route_flit_count <= {(5 * COUNTER_W){1'b0}};
      for (seq_output_i = 0; seq_output_i < PORTS; seq_output_i = seq_output_i + 1) begin
        out_flit_q[seq_output_i] <= {FLIT_W{1'b0}};
        rr_cursor_q[seq_output_i] <= {INPUT_INDEX_W{1'b0}};
      end
    end else begin
      accepted_i = 0;
      forwarded_i = 0;
      for (seq_port_i = 0; seq_port_i < PORTS; seq_port_i = seq_port_i + 1) begin
        if (in_valid[seq_port_i] && in_ready[seq_port_i])
          accepted_i = accepted_i + 1;
        if (out_valid_q[seq_port_i] && out_ready[seq_port_i]) begin
          forwarded_i = forwarded_i + 1;
          route_flit_count[(seq_port_i * COUNTER_W) +: COUNTER_W]
              <= route_flit_count[(seq_port_i * COUNTER_W) +: COUNTER_W] + 1'b1;
        end
        if (!out_valid_q[seq_port_i] || out_ready[seq_port_i]) begin
          if (grant_valid_r[seq_port_i]) begin
            out_valid_q[seq_port_i] <= 1'b1;
            out_flit_q[seq_port_i] <= grant_flit_r[seq_port_i];
            if (grant_index_r[seq_port_i] == (INPUTS - 1))
              rr_cursor_q[seq_port_i] <= {INPUT_INDEX_W{1'b0}};
            else
              rr_cursor_q[seq_port_i] <= grant_index_r[seq_port_i] + 1'b1;
          end else begin
            out_valid_q[seq_port_i] <= 1'b0;
          end
        end
      end
      accepted_flit_count <= accepted_flit_count + accepted_i;
      forwarded_flit_count <= forwarded_flit_count + forwarded_i;
      if (any_input_stall_r)
        input_stall_cycles <= input_stall_cycles + 1'b1;
      if (any_output_stall_r)
        output_stall_cycles <= output_stall_cycles + 1'b1;
      if (any_contention_r)
        arbitration_contention_cycles <= arbitration_contention_cycles + 1'b1;
      if (occupancy_sum_r > max_input_occupancy)
        max_input_occupancy <= occupancy_sum_r;
    end
  end
endmodule
