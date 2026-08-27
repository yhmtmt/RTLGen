`timescale 1ns/1ps

// Logic-free specialization for the representative interior router at node 5
// of the 4x4 mesh. This top is shared by physical implementation and workload
// replay so activity annotation does not cross a synthetic PPA harness.
module noc_segmented_mesh_router_node5 #(
  parameter integer X_COORD = 1,
  parameter integer Y_COORD = 1
) (
  input  wire          clk,
  input  wire          rst_n,
  input  wire [4:0]    in_valid,
  output wire [4:0]    in_ready,
  input  wire [19:0]   in_dest,
  input  wire [19:0]   in_source,
  input  wire [39:0]   in_tag,
  input  wire [14:0]   in_fragment,
  input  wire [4:0]    in_last,
  input  wire [9:0]    in_vc,
  input  wire [1279:0] in_data,
  output wire [4:0]    out_valid,
  input  wire [4:0]    out_ready,
  output wire [19:0]   out_dest,
  output wire [19:0]   out_source,
  output wire [39:0]   out_tag,
  output wire [14:0]   out_fragment,
  output wire [4:0]    out_last,
  output wire [9:0]    out_vc,
  output wire [1279:0] out_data,
  output wire [31:0]   accepted_flit_count,
  output wire [31:0]   forwarded_flit_count,
  output wire [31:0]   input_stall_cycles,
  output wire [31:0]   output_stall_cycles,
  output wire [31:0]   arbitration_contention_cycles,
  output wire [31:0]   current_input_occupancy,
  output wire [31:0]   max_input_occupancy,
  output wire [159:0]  route_flit_count
);
  noc_segmented_mesh_router #(
    .DATA_W(256),
    .DEST_W(4),
    .SOURCE_W(4),
    .TAG_W(8),
    .FRAGMENT_W(3),
    .VC_W(2),
    .VC_COUNT(4),
    .FIFO_DEPTH(4),
    .X_COORD(X_COORD),
    .Y_COORD(Y_COORD),
    .COUNTER_W(32)
  ) u_router (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_dest(in_dest),
    .in_source(in_source),
    .in_tag(in_tag),
    .in_fragment(in_fragment),
    .in_last(in_last),
    .in_vc(in_vc),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_dest(out_dest),
    .out_source(out_source),
    .out_tag(out_tag),
    .out_fragment(out_fragment),
    .out_last(out_last),
    .out_vc(out_vc),
    .out_data(out_data),
    .accepted_flit_count(accepted_flit_count),
    .forwarded_flit_count(forwarded_flit_count),
    .input_stall_cycles(input_stall_cycles),
    .output_stall_cycles(output_stall_cycles),
    .arbitration_contention_cycles(arbitration_contention_cycles),
    .current_input_occupancy(current_input_occupancy),
    .max_input_occupancy(max_input_occupancy),
    .route_flit_count(route_flit_count)
  );
endmodule
