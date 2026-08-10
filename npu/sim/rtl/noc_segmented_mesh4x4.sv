`timescale 1ns/1ps

// Concrete 4x4 composition of deterministic-XY 256-bit flit routers.
// Endpoint index is {y[1:0], x[1:0]}; north decrements y.
module noc_segmented_mesh4x4 #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer VC_COUNT = 4,
  parameter integer FIFO_DEPTH = 4,
  parameter integer COUNTER_W = 32
) (
  input  wire                              clk,
  input  wire                              rst_n,
  input  wire [15:0]                       endpoint_in_valid,
  output wire [15:0]                       endpoint_in_ready,
  input  wire [16*4-1:0]                   endpoint_in_dest,
  input  wire [16*4-1:0]                   endpoint_in_source,
  input  wire [16*TAG_W-1:0]               endpoint_in_tag,
  input  wire [16*FRAGMENT_W-1:0]          endpoint_in_fragment,
  input  wire [15:0]                       endpoint_in_last,
  input  wire [16*VC_W-1:0]                endpoint_in_vc,
  input  wire [16*DATA_W-1:0]              endpoint_in_data,
  output wire [15:0]                       endpoint_out_valid,
  input  wire [15:0]                       endpoint_out_ready,
  output wire [16*4-1:0]                   endpoint_out_dest,
  output wire [16*4-1:0]                   endpoint_out_source,
  output wire [16*TAG_W-1:0]               endpoint_out_tag,
  output wire [16*FRAGMENT_W-1:0]          endpoint_out_fragment,
  output wire [15:0]                       endpoint_out_last,
  output wire [16*VC_W-1:0]                endpoint_out_vc,
  output wire [16*DATA_W-1:0]              endpoint_out_data,
  output wire [16*COUNTER_W-1:0]           router_accepted_flit_count,
  output wire [16*COUNTER_W-1:0]           router_forwarded_flit_count,
  output wire [16*COUNTER_W-1:0]           router_input_stall_cycles,
  output wire [16*COUNTER_W-1:0]           router_output_stall_cycles,
  output wire [16*COUNTER_W-1:0]           router_contention_cycles,
  output wire [16*COUNTER_W-1:0]           router_current_input_occupancy,
  output wire [16*COUNTER_W-1:0]           router_max_input_occupancy,
  output wire [16*5*COUNTER_W-1:0]         router_route_flit_count
);
  localparam integer NODES = 16;
  localparam integer PORTS = 5;
  localparam integer DEST_W = 4;
  localparam integer SOURCE_W = 4;
  localparam integer NORTH = 0;
  localparam integer SOUTH = 1;
  localparam integer EAST = 2;
  localparam integer WEST = 3;
  localparam integer LOCAL = 4;

  wire [NODES*PORTS-1:0] router_in_valid;
  wire [NODES*PORTS-1:0] router_in_ready;
  wire [NODES*PORTS*DEST_W-1:0] router_in_dest;
  wire [NODES*PORTS*SOURCE_W-1:0] router_in_source;
  wire [NODES*PORTS*TAG_W-1:0] router_in_tag;
  wire [NODES*PORTS*FRAGMENT_W-1:0] router_in_fragment;
  wire [NODES*PORTS-1:0] router_in_last;
  wire [NODES*PORTS*VC_W-1:0] router_in_vc;
  wire [NODES*PORTS*DATA_W-1:0] router_in_data;
  wire [NODES*PORTS-1:0] router_out_valid;
  wire [NODES*PORTS-1:0] router_out_ready;
  wire [NODES*PORTS*DEST_W-1:0] router_out_dest;
  wire [NODES*PORTS*SOURCE_W-1:0] router_out_source;
  wire [NODES*PORTS*TAG_W-1:0] router_out_tag;
  wire [NODES*PORTS*FRAGMENT_W-1:0] router_out_fragment;
  wire [NODES*PORTS-1:0] router_out_last;
  wire [NODES*PORTS*VC_W-1:0] router_out_vc;
  wire [NODES*PORTS*DATA_W-1:0] router_out_data;

  genvar node_g;
  generate
    for (node_g = 0; node_g < NODES; node_g = node_g + 1) begin : gen_nodes
      localparam integer X = node_g % 4;
      localparam integer Y = node_g / 4;

      assign router_in_valid[(node_g * PORTS) + LOCAL] = endpoint_in_valid[node_g];
      assign endpoint_in_ready[node_g] = router_in_ready[(node_g * PORTS) + LOCAL];
      assign router_in_dest[(((node_g * PORTS) + LOCAL) * DEST_W) +: DEST_W] = endpoint_in_dest[(node_g * DEST_W) +: DEST_W];
      assign router_in_source[(((node_g * PORTS) + LOCAL) * SOURCE_W) +: SOURCE_W] = endpoint_in_source[(node_g * SOURCE_W) +: SOURCE_W];
      assign router_in_tag[(((node_g * PORTS) + LOCAL) * TAG_W) +: TAG_W] = endpoint_in_tag[(node_g * TAG_W) +: TAG_W];
      assign router_in_fragment[(((node_g * PORTS) + LOCAL) * FRAGMENT_W) +: FRAGMENT_W] = endpoint_in_fragment[(node_g * FRAGMENT_W) +: FRAGMENT_W];
      assign router_in_last[(node_g * PORTS) + LOCAL] = endpoint_in_last[node_g];
      assign router_in_vc[(((node_g * PORTS) + LOCAL) * VC_W) +: VC_W] = endpoint_in_vc[(node_g * VC_W) +: VC_W];
      assign router_in_data[(((node_g * PORTS) + LOCAL) * DATA_W) +: DATA_W] = endpoint_in_data[(node_g * DATA_W) +: DATA_W];
      assign endpoint_out_valid[node_g] = router_out_valid[(node_g * PORTS) + LOCAL];
      assign router_out_ready[(node_g * PORTS) + LOCAL] = endpoint_out_ready[node_g];
      assign endpoint_out_dest[(node_g * DEST_W) +: DEST_W] = router_out_dest[(((node_g * PORTS) + LOCAL) * DEST_W) +: DEST_W];
      assign endpoint_out_source[(node_g * SOURCE_W) +: SOURCE_W] = router_out_source[(((node_g * PORTS) + LOCAL) * SOURCE_W) +: SOURCE_W];
      assign endpoint_out_tag[(node_g * TAG_W) +: TAG_W] = router_out_tag[(((node_g * PORTS) + LOCAL) * TAG_W) +: TAG_W];
      assign endpoint_out_fragment[(node_g * FRAGMENT_W) +: FRAGMENT_W] = router_out_fragment[(((node_g * PORTS) + LOCAL) * FRAGMENT_W) +: FRAGMENT_W];
      assign endpoint_out_last[node_g] = router_out_last[(node_g * PORTS) + LOCAL];
      assign endpoint_out_vc[(node_g * VC_W) +: VC_W] = router_out_vc[(((node_g * PORTS) + LOCAL) * VC_W) +: VC_W];
      assign endpoint_out_data[(node_g * DATA_W) +: DATA_W] = router_out_data[(((node_g * PORTS) + LOCAL) * DATA_W) +: DATA_W];

      if (Y > 0) begin : gen_north_link
        localparam integer NEIGHBOR = node_g - 4;
        assign router_in_valid[(node_g * PORTS) + NORTH] = router_out_valid[(NEIGHBOR * PORTS) + SOUTH];
        assign router_out_ready[(NEIGHBOR * PORTS) + SOUTH] = router_in_ready[(node_g * PORTS) + NORTH];
        assign router_in_dest[(((node_g * PORTS) + NORTH) * DEST_W) +: DEST_W] = router_out_dest[(((NEIGHBOR * PORTS) + SOUTH) * DEST_W) +: DEST_W];
        assign router_in_source[(((node_g * PORTS) + NORTH) * SOURCE_W) +: SOURCE_W] = router_out_source[(((NEIGHBOR * PORTS) + SOUTH) * SOURCE_W) +: SOURCE_W];
        assign router_in_tag[(((node_g * PORTS) + NORTH) * TAG_W) +: TAG_W] = router_out_tag[(((NEIGHBOR * PORTS) + SOUTH) * TAG_W) +: TAG_W];
        assign router_in_fragment[(((node_g * PORTS) + NORTH) * FRAGMENT_W) +: FRAGMENT_W] = router_out_fragment[(((NEIGHBOR * PORTS) + SOUTH) * FRAGMENT_W) +: FRAGMENT_W];
        assign router_in_last[(node_g * PORTS) + NORTH] = router_out_last[(NEIGHBOR * PORTS) + SOUTH];
        assign router_in_vc[(((node_g * PORTS) + NORTH) * VC_W) +: VC_W] = router_out_vc[(((NEIGHBOR * PORTS) + SOUTH) * VC_W) +: VC_W];
        assign router_in_data[(((node_g * PORTS) + NORTH) * DATA_W) +: DATA_W] = router_out_data[(((NEIGHBOR * PORTS) + SOUTH) * DATA_W) +: DATA_W];
      end else begin : gen_north_edge
        assign router_in_valid[(node_g * PORTS) + NORTH] = 1'b0;
        assign router_in_dest[(((node_g * PORTS) + NORTH) * DEST_W) +: DEST_W] = 0;
        assign router_in_source[(((node_g * PORTS) + NORTH) * SOURCE_W) +: SOURCE_W] = 0;
        assign router_in_tag[(((node_g * PORTS) + NORTH) * TAG_W) +: TAG_W] = 0;
        assign router_in_fragment[(((node_g * PORTS) + NORTH) * FRAGMENT_W) +: FRAGMENT_W] = 0;
        assign router_in_last[(node_g * PORTS) + NORTH] = 1'b0;
        assign router_in_vc[(((node_g * PORTS) + NORTH) * VC_W) +: VC_W] = 0;
        assign router_in_data[(((node_g * PORTS) + NORTH) * DATA_W) +: DATA_W] = 0;
        assign router_out_ready[(node_g * PORTS) + NORTH] = 1'b1;
      end

      if (Y < 3) begin : gen_south_link
        localparam integer NEIGHBOR = node_g + 4;
        assign router_in_valid[(node_g * PORTS) + SOUTH] = router_out_valid[(NEIGHBOR * PORTS) + NORTH];
        assign router_out_ready[(NEIGHBOR * PORTS) + NORTH] = router_in_ready[(node_g * PORTS) + SOUTH];
        assign router_in_dest[(((node_g * PORTS) + SOUTH) * DEST_W) +: DEST_W] = router_out_dest[(((NEIGHBOR * PORTS) + NORTH) * DEST_W) +: DEST_W];
        assign router_in_source[(((node_g * PORTS) + SOUTH) * SOURCE_W) +: SOURCE_W] = router_out_source[(((NEIGHBOR * PORTS) + NORTH) * SOURCE_W) +: SOURCE_W];
        assign router_in_tag[(((node_g * PORTS) + SOUTH) * TAG_W) +: TAG_W] = router_out_tag[(((NEIGHBOR * PORTS) + NORTH) * TAG_W) +: TAG_W];
        assign router_in_fragment[(((node_g * PORTS) + SOUTH) * FRAGMENT_W) +: FRAGMENT_W] = router_out_fragment[(((NEIGHBOR * PORTS) + NORTH) * FRAGMENT_W) +: FRAGMENT_W];
        assign router_in_last[(node_g * PORTS) + SOUTH] = router_out_last[(NEIGHBOR * PORTS) + NORTH];
        assign router_in_vc[(((node_g * PORTS) + SOUTH) * VC_W) +: VC_W] = router_out_vc[(((NEIGHBOR * PORTS) + NORTH) * VC_W) +: VC_W];
        assign router_in_data[(((node_g * PORTS) + SOUTH) * DATA_W) +: DATA_W] = router_out_data[(((NEIGHBOR * PORTS) + NORTH) * DATA_W) +: DATA_W];
      end else begin : gen_south_edge
        assign router_in_valid[(node_g * PORTS) + SOUTH] = 1'b0;
        assign router_in_dest[(((node_g * PORTS) + SOUTH) * DEST_W) +: DEST_W] = 0;
        assign router_in_source[(((node_g * PORTS) + SOUTH) * SOURCE_W) +: SOURCE_W] = 0;
        assign router_in_tag[(((node_g * PORTS) + SOUTH) * TAG_W) +: TAG_W] = 0;
        assign router_in_fragment[(((node_g * PORTS) + SOUTH) * FRAGMENT_W) +: FRAGMENT_W] = 0;
        assign router_in_last[(node_g * PORTS) + SOUTH] = 1'b0;
        assign router_in_vc[(((node_g * PORTS) + SOUTH) * VC_W) +: VC_W] = 0;
        assign router_in_data[(((node_g * PORTS) + SOUTH) * DATA_W) +: DATA_W] = 0;
        assign router_out_ready[(node_g * PORTS) + SOUTH] = 1'b1;
      end

      if (X < 3) begin : gen_east_link
        localparam integer NEIGHBOR = node_g + 1;
        assign router_in_valid[(node_g * PORTS) + EAST] = router_out_valid[(NEIGHBOR * PORTS) + WEST];
        assign router_out_ready[(NEIGHBOR * PORTS) + WEST] = router_in_ready[(node_g * PORTS) + EAST];
        assign router_in_dest[(((node_g * PORTS) + EAST) * DEST_W) +: DEST_W] = router_out_dest[(((NEIGHBOR * PORTS) + WEST) * DEST_W) +: DEST_W];
        assign router_in_source[(((node_g * PORTS) + EAST) * SOURCE_W) +: SOURCE_W] = router_out_source[(((NEIGHBOR * PORTS) + WEST) * SOURCE_W) +: SOURCE_W];
        assign router_in_tag[(((node_g * PORTS) + EAST) * TAG_W) +: TAG_W] = router_out_tag[(((NEIGHBOR * PORTS) + WEST) * TAG_W) +: TAG_W];
        assign router_in_fragment[(((node_g * PORTS) + EAST) * FRAGMENT_W) +: FRAGMENT_W] = router_out_fragment[(((NEIGHBOR * PORTS) + WEST) * FRAGMENT_W) +: FRAGMENT_W];
        assign router_in_last[(node_g * PORTS) + EAST] = router_out_last[(NEIGHBOR * PORTS) + WEST];
        assign router_in_vc[(((node_g * PORTS) + EAST) * VC_W) +: VC_W] = router_out_vc[(((NEIGHBOR * PORTS) + WEST) * VC_W) +: VC_W];
        assign router_in_data[(((node_g * PORTS) + EAST) * DATA_W) +: DATA_W] = router_out_data[(((NEIGHBOR * PORTS) + WEST) * DATA_W) +: DATA_W];
      end else begin : gen_east_edge
        assign router_in_valid[(node_g * PORTS) + EAST] = 1'b0;
        assign router_in_dest[(((node_g * PORTS) + EAST) * DEST_W) +: DEST_W] = 0;
        assign router_in_source[(((node_g * PORTS) + EAST) * SOURCE_W) +: SOURCE_W] = 0;
        assign router_in_tag[(((node_g * PORTS) + EAST) * TAG_W) +: TAG_W] = 0;
        assign router_in_fragment[(((node_g * PORTS) + EAST) * FRAGMENT_W) +: FRAGMENT_W] = 0;
        assign router_in_last[(node_g * PORTS) + EAST] = 1'b0;
        assign router_in_vc[(((node_g * PORTS) + EAST) * VC_W) +: VC_W] = 0;
        assign router_in_data[(((node_g * PORTS) + EAST) * DATA_W) +: DATA_W] = 0;
        assign router_out_ready[(node_g * PORTS) + EAST] = 1'b1;
      end

      if (X > 0) begin : gen_west_link
        localparam integer NEIGHBOR = node_g - 1;
        assign router_in_valid[(node_g * PORTS) + WEST] = router_out_valid[(NEIGHBOR * PORTS) + EAST];
        assign router_out_ready[(NEIGHBOR * PORTS) + EAST] = router_in_ready[(node_g * PORTS) + WEST];
        assign router_in_dest[(((node_g * PORTS) + WEST) * DEST_W) +: DEST_W] = router_out_dest[(((NEIGHBOR * PORTS) + EAST) * DEST_W) +: DEST_W];
        assign router_in_source[(((node_g * PORTS) + WEST) * SOURCE_W) +: SOURCE_W] = router_out_source[(((NEIGHBOR * PORTS) + EAST) * SOURCE_W) +: SOURCE_W];
        assign router_in_tag[(((node_g * PORTS) + WEST) * TAG_W) +: TAG_W] = router_out_tag[(((NEIGHBOR * PORTS) + EAST) * TAG_W) +: TAG_W];
        assign router_in_fragment[(((node_g * PORTS) + WEST) * FRAGMENT_W) +: FRAGMENT_W] = router_out_fragment[(((NEIGHBOR * PORTS) + EAST) * FRAGMENT_W) +: FRAGMENT_W];
        assign router_in_last[(node_g * PORTS) + WEST] = router_out_last[(NEIGHBOR * PORTS) + EAST];
        assign router_in_vc[(((node_g * PORTS) + WEST) * VC_W) +: VC_W] = router_out_vc[(((NEIGHBOR * PORTS) + EAST) * VC_W) +: VC_W];
        assign router_in_data[(((node_g * PORTS) + WEST) * DATA_W) +: DATA_W] = router_out_data[(((NEIGHBOR * PORTS) + EAST) * DATA_W) +: DATA_W];
      end else begin : gen_west_edge
        assign router_in_valid[(node_g * PORTS) + WEST] = 1'b0;
        assign router_in_dest[(((node_g * PORTS) + WEST) * DEST_W) +: DEST_W] = 0;
        assign router_in_source[(((node_g * PORTS) + WEST) * SOURCE_W) +: SOURCE_W] = 0;
        assign router_in_tag[(((node_g * PORTS) + WEST) * TAG_W) +: TAG_W] = 0;
        assign router_in_fragment[(((node_g * PORTS) + WEST) * FRAGMENT_W) +: FRAGMENT_W] = 0;
        assign router_in_last[(node_g * PORTS) + WEST] = 1'b0;
        assign router_in_vc[(((node_g * PORTS) + WEST) * VC_W) +: VC_W] = 0;
        assign router_in_data[(((node_g * PORTS) + WEST) * DATA_W) +: DATA_W] = 0;
        assign router_out_ready[(node_g * PORTS) + WEST] = 1'b1;
      end

      noc_segmented_mesh_router #(
        .DATA_W(DATA_W),
        .DEST_W(DEST_W),
        .SOURCE_W(SOURCE_W),
        .TAG_W(TAG_W),
        .FRAGMENT_W(FRAGMENT_W),
        .VC_W(VC_W),
        .VC_COUNT(VC_COUNT),
        .FIFO_DEPTH(FIFO_DEPTH),
        .X_COORD(X),
        .Y_COORD(Y),
        .COUNTER_W(COUNTER_W)
      ) u_router (
        .clk(clk), .rst_n(rst_n),
        .in_valid(router_in_valid[(node_g * PORTS) +: PORTS]),
        .in_ready(router_in_ready[(node_g * PORTS) +: PORTS]),
        .in_dest(router_in_dest[(node_g * PORTS * DEST_W) +: (PORTS * DEST_W)]),
        .in_source(router_in_source[(node_g * PORTS * SOURCE_W) +: (PORTS * SOURCE_W)]),
        .in_tag(router_in_tag[(node_g * PORTS * TAG_W) +: (PORTS * TAG_W)]),
        .in_fragment(router_in_fragment[(node_g * PORTS * FRAGMENT_W) +: (PORTS * FRAGMENT_W)]),
        .in_last(router_in_last[(node_g * PORTS) +: PORTS]),
        .in_vc(router_in_vc[(node_g * PORTS * VC_W) +: (PORTS * VC_W)]),
        .in_data(router_in_data[(node_g * PORTS * DATA_W) +: (PORTS * DATA_W)]),
        .out_valid(router_out_valid[(node_g * PORTS) +: PORTS]),
        .out_ready(router_out_ready[(node_g * PORTS) +: PORTS]),
        .out_dest(router_out_dest[(node_g * PORTS * DEST_W) +: (PORTS * DEST_W)]),
        .out_source(router_out_source[(node_g * PORTS * SOURCE_W) +: (PORTS * SOURCE_W)]),
        .out_tag(router_out_tag[(node_g * PORTS * TAG_W) +: (PORTS * TAG_W)]),
        .out_fragment(router_out_fragment[(node_g * PORTS * FRAGMENT_W) +: (PORTS * FRAGMENT_W)]),
        .out_last(router_out_last[(node_g * PORTS) +: PORTS]),
        .out_vc(router_out_vc[(node_g * PORTS * VC_W) +: (PORTS * VC_W)]),
        .out_data(router_out_data[(node_g * PORTS * DATA_W) +: (PORTS * DATA_W)]),
        .accepted_flit_count(router_accepted_flit_count[(node_g * COUNTER_W) +: COUNTER_W]),
        .forwarded_flit_count(router_forwarded_flit_count[(node_g * COUNTER_W) +: COUNTER_W]),
        .input_stall_cycles(router_input_stall_cycles[(node_g * COUNTER_W) +: COUNTER_W]),
        .output_stall_cycles(router_output_stall_cycles[(node_g * COUNTER_W) +: COUNTER_W]),
        .arbitration_contention_cycles(router_contention_cycles[(node_g * COUNTER_W) +: COUNTER_W]),
        .current_input_occupancy(router_current_input_occupancy[(node_g * COUNTER_W) +: COUNTER_W]),
        .max_input_occupancy(router_max_input_occupancy[(node_g * COUNTER_W) +: COUNTER_W]),
        .route_flit_count(router_route_flit_count[(node_g * PORTS * COUNTER_W) +: (PORTS * COUNTER_W)])
      );
    end
  endgenerate
endmodule
