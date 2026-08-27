`timescale 1ns/1ps

// Logic-free functional macro boundary for workload-equivalent mesh PPA/power.
// Debug counters are intentionally not part of the deployed transport interface.
module noc_segmented_mesh4x4_functional (
  input  wire            clk,
  input  wire            rst_n,
  input  wire [15:0]     endpoint_in_valid,
  output wire [15:0]     endpoint_in_ready,
  input  wire [63:0]     endpoint_in_dest,
  input  wire [63:0]     endpoint_in_source,
  input  wire [127:0]    endpoint_in_tag,
  input  wire [47:0]     endpoint_in_fragment,
  input  wire [15:0]     endpoint_in_last,
  input  wire [31:0]     endpoint_in_vc,
  input  wire [4095:0]   endpoint_in_data,
  output wire [15:0]     endpoint_out_valid,
  input  wire [15:0]     endpoint_out_ready,
  output wire [63:0]     endpoint_out_dest,
  output wire [63:0]     endpoint_out_source,
  output wire [127:0]    endpoint_out_tag,
  output wire [47:0]     endpoint_out_fragment,
  output wire [15:0]     endpoint_out_last,
  output wire [31:0]     endpoint_out_vc,
  output wire [4095:0]   endpoint_out_data
);
  noc_segmented_mesh4x4 #(
    .ENABLE_DEBUG_COUNTERS(0)
  ) u_mesh (
    .clk(clk),
    .rst_n(rst_n),
    .endpoint_in_valid(endpoint_in_valid),
    .endpoint_in_ready(endpoint_in_ready),
    .endpoint_in_dest(endpoint_in_dest),
    .endpoint_in_source(endpoint_in_source),
    .endpoint_in_tag(endpoint_in_tag),
    .endpoint_in_fragment(endpoint_in_fragment),
    .endpoint_in_last(endpoint_in_last),
    .endpoint_in_vc(endpoint_in_vc),
    .endpoint_in_data(endpoint_in_data),
    .endpoint_out_valid(endpoint_out_valid),
    .endpoint_out_ready(endpoint_out_ready),
    .endpoint_out_dest(endpoint_out_dest),
    .endpoint_out_source(endpoint_out_source),
    .endpoint_out_tag(endpoint_out_tag),
    .endpoint_out_fragment(endpoint_out_fragment),
    .endpoint_out_last(endpoint_out_last),
    .endpoint_out_vc(endpoint_out_vc),
    .endpoint_out_data(endpoint_out_data),
    .router_accepted_flit_count(),
    .router_forwarded_flit_count(),
    .router_input_stall_cycles(),
    .router_output_stall_cycles(),
    .router_contention_cycles(),
    .router_current_input_occupancy(),
    .router_max_input_occupancy(),
    .router_route_flit_count()
  );
endmodule
