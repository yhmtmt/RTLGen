`timescale 1ns/1ps

// Sixteen-endpoint shared transport for exactly two complete producer
// boundaries. Producer0 owns VC0, producer1 owns VC1. Each endpoint uses the
// existing held-grant injection arbiter and the composed fabric is exactly one
// segmented 4x4 mesh.
module noc_shared_vc_dual_producer_transport4x4 #(
  parameter integer DATA_W = 256,
  parameter integer ENDPOINT_W = 4,
  parameter integer VC_W = 2,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_COUNT = 2,
  parameter integer FIFO_DEPTH = 4,
  parameter integer COUNTER_W = 32,
  parameter integer ENABLE_DEBUG_COUNTERS = 0
) (
  input wire clk,
  input wire rst_n,

  input wire [15:0] producer0_in_valid,
  output wire [15:0] producer0_in_ready,
  input wire [16*ENDPOINT_W-1:0] producer0_in_destination,
  input wire [16*ENDPOINT_W-1:0] producer0_in_source,
  input wire [16*TAG_W-1:0] producer0_in_tag,
  input wire [16*FRAGMENT_W-1:0] producer0_in_fragment,
  input wire [15:0] producer0_in_last,
  input wire [16*VC_W-1:0] producer0_in_vc,
  input wire [16*DATA_W-1:0] producer0_in_data,

  input wire [15:0] producer1_in_valid,
  output wire [15:0] producer1_in_ready,
  input wire [16*ENDPOINT_W-1:0] producer1_in_destination,
  input wire [16*ENDPOINT_W-1:0] producer1_in_source,
  input wire [16*TAG_W-1:0] producer1_in_tag,
  input wire [16*FRAGMENT_W-1:0] producer1_in_fragment,
  input wire [15:0] producer1_in_last,
  input wire [16*VC_W-1:0] producer1_in_vc,
  input wire [16*DATA_W-1:0] producer1_in_data,

  output wire [15:0] producer0_out_valid,
  input wire [15:0] producer0_out_ready,
  output wire [16*ENDPOINT_W-1:0] producer0_out_destination,
  output wire [16*ENDPOINT_W-1:0] producer0_out_source,
  output wire [16*TAG_W-1:0] producer0_out_tag,
  output wire [16*FRAGMENT_W-1:0] producer0_out_fragment,
  output wire [15:0] producer0_out_last,
  output wire [16*VC_W-1:0] producer0_out_vc,
  output wire [16*DATA_W-1:0] producer0_out_data,

  output wire [15:0] producer1_out_valid,
  input wire [15:0] producer1_out_ready,
  output wire [16*ENDPOINT_W-1:0] producer1_out_destination,
  output wire [16*ENDPOINT_W-1:0] producer1_out_source,
  output wire [16*TAG_W-1:0] producer1_out_tag,
  output wire [16*FRAGMENT_W-1:0] producer1_out_fragment,
  output wire [15:0] producer1_out_last,
  output wire [16*VC_W-1:0] producer1_out_vc,
  output wire [16*DATA_W-1:0] producer1_out_data,

  output wire [15:0] injection_protocol_error,
  output reg [15:0] ejection_protocol_error,
  output wire protocol_error
);
  localparam integer NODES = 16;
  localparam [VC_W-1:0] PRODUCER0_EXPECTED_VC = {VC_W{1'b0}};
  localparam [VC_W-1:0] PRODUCER1_EXPECTED_VC = {{(VC_W-1){1'b0}}, 1'b1};

  wire [15:0] mesh_endpoint_in_valid_w;
  wire [15:0] mesh_endpoint_in_ready_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_in_destination_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_in_source_w;
  wire [16*TAG_W-1:0] mesh_endpoint_in_tag_w;
  wire [16*FRAGMENT_W-1:0] mesh_endpoint_in_fragment_w;
  wire [15:0] mesh_endpoint_in_last_w;
  wire [16*VC_W-1:0] mesh_endpoint_in_vc_w;
  wire [16*DATA_W-1:0] mesh_endpoint_in_data_w;

  wire [15:0] mesh_endpoint_out_valid_w;
  wire [15:0] mesh_endpoint_out_ready_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_out_destination_w;
  wire [16*ENDPOINT_W-1:0] mesh_endpoint_out_source_w;
  wire [16*TAG_W-1:0] mesh_endpoint_out_tag_w;
  wire [16*FRAGMENT_W-1:0] mesh_endpoint_out_fragment_w;
  wire [15:0] mesh_endpoint_out_last_w;
  wire [16*VC_W-1:0] mesh_endpoint_out_vc_w;
  wire [16*DATA_W-1:0] mesh_endpoint_out_data_w;

  wire [16*COUNTER_W-1:0] router_accepted_flit_count_w;
  wire [16*COUNTER_W-1:0] router_forwarded_flit_count_w;
  wire [16*COUNTER_W-1:0] router_input_stall_cycles_w;
  wire [16*COUNTER_W-1:0] router_output_stall_cycles_w;
  wire [16*COUNTER_W-1:0] router_contention_cycles_w;
  wire [16*COUNTER_W-1:0] router_current_input_occupancy_w;
  wire [16*COUNTER_W-1:0] router_max_input_occupancy_w;
  wire [16*5*COUNTER_W-1:0] router_route_flit_count_w;

  wire [15:0] route_to_producer0_w;
  wire [15:0] route_to_producer1_w;
  wire [15:0] unexpected_ejection_w;

  genvar endpoint_g;
  generate
    for (endpoint_g = 0; endpoint_g < NODES; endpoint_g = endpoint_g + 1) begin : gen_endpoints
      wire [VC_W-1:0] endpoint_mesh_out_vc_w;

      assign endpoint_mesh_out_vc_w =
        mesh_endpoint_out_vc_w[(endpoint_g * VC_W) +: VC_W];

      noc_endpoint_vc_injection_arbiter #(
        .DATA_W(DATA_W),
        .ENDPOINT_W(ENDPOINT_W),
        .VC_W(VC_W),
        .TAG_W(TAG_W),
        .FRAGMENT_W(FRAGMENT_W)
      ) injection_arbiter (
        .clk(clk),
        .rst_n(rst_n),
        .vc0_valid(producer0_in_valid[endpoint_g]),
        .vc0_ready(producer0_in_ready[endpoint_g]),
        .vc0_destination(
          producer0_in_destination[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .vc0_source(
          producer0_in_source[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .vc0_tag(producer0_in_tag[(endpoint_g * TAG_W) +: TAG_W]),
        .vc0_fragment(
          producer0_in_fragment[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W]
        ),
        .vc0_last(producer0_in_last[endpoint_g]),
        .vc0_vc(producer0_in_vc[(endpoint_g * VC_W) +: VC_W]),
        .vc0_data(producer0_in_data[(endpoint_g * DATA_W) +: DATA_W]),
        .vc1_valid(producer1_in_valid[endpoint_g]),
        .vc1_ready(producer1_in_ready[endpoint_g]),
        .vc1_destination(
          producer1_in_destination[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .vc1_source(
          producer1_in_source[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .vc1_tag(producer1_in_tag[(endpoint_g * TAG_W) +: TAG_W]),
        .vc1_fragment(
          producer1_in_fragment[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W]
        ),
        .vc1_last(producer1_in_last[endpoint_g]),
        .vc1_vc(producer1_in_vc[(endpoint_g * VC_W) +: VC_W]),
        .vc1_data(producer1_in_data[(endpoint_g * DATA_W) +: DATA_W]),
        .out_valid(mesh_endpoint_in_valid_w[endpoint_g]),
        .out_ready(mesh_endpoint_in_ready_w[endpoint_g]),
        .out_destination(
          mesh_endpoint_in_destination_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .out_source(
          mesh_endpoint_in_source_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W]
        ),
        .out_tag(mesh_endpoint_in_tag_w[(endpoint_g * TAG_W) +: TAG_W]),
        .out_fragment(
          mesh_endpoint_in_fragment_w[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W]
        ),
        .out_last(mesh_endpoint_in_last_w[endpoint_g]),
        .out_vc(mesh_endpoint_in_vc_w[(endpoint_g * VC_W) +: VC_W]),
        .out_data(mesh_endpoint_in_data_w[(endpoint_g * DATA_W) +: DATA_W]),
        .protocol_error(injection_protocol_error[endpoint_g])
      );

      assign route_to_producer0_w[endpoint_g] =
        mesh_endpoint_out_valid_w[endpoint_g] &&
        (endpoint_mesh_out_vc_w == PRODUCER0_EXPECTED_VC);
      assign route_to_producer1_w[endpoint_g] =
        mesh_endpoint_out_valid_w[endpoint_g] &&
        (endpoint_mesh_out_vc_w == PRODUCER1_EXPECTED_VC);
      assign unexpected_ejection_w[endpoint_g] =
        mesh_endpoint_out_valid_w[endpoint_g] &&
        !route_to_producer0_w[endpoint_g] &&
        !route_to_producer1_w[endpoint_g];

      assign producer0_out_valid[endpoint_g] = route_to_producer0_w[endpoint_g];
      assign producer1_out_valid[endpoint_g] = route_to_producer1_w[endpoint_g];

      assign producer0_out_destination[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_destination_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] :
          {ENDPOINT_W{1'b0}};
      assign producer0_out_source[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_source_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] :
          {ENDPOINT_W{1'b0}};
      assign producer0_out_tag[(endpoint_g * TAG_W) +: TAG_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_tag_w[(endpoint_g * TAG_W) +: TAG_W] :
          {TAG_W{1'b0}};
      assign producer0_out_fragment[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_fragment_w[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W] :
          {FRAGMENT_W{1'b0}};
      assign producer0_out_last[endpoint_g] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_last_w[endpoint_g] : 1'b0;
      assign producer0_out_vc[(endpoint_g * VC_W) +: VC_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_vc_w[(endpoint_g * VC_W) +: VC_W] :
          {VC_W{1'b0}};
      assign producer0_out_data[(endpoint_g * DATA_W) +: DATA_W] =
        route_to_producer0_w[endpoint_g] ?
          mesh_endpoint_out_data_w[(endpoint_g * DATA_W) +: DATA_W] :
          {DATA_W{1'b0}};

      assign producer1_out_destination[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_destination_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] :
          {ENDPOINT_W{1'b0}};
      assign producer1_out_source[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_source_w[(endpoint_g * ENDPOINT_W) +: ENDPOINT_W] :
          {ENDPOINT_W{1'b0}};
      assign producer1_out_tag[(endpoint_g * TAG_W) +: TAG_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_tag_w[(endpoint_g * TAG_W) +: TAG_W] :
          {TAG_W{1'b0}};
      assign producer1_out_fragment[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_fragment_w[(endpoint_g * FRAGMENT_W) +: FRAGMENT_W] :
          {FRAGMENT_W{1'b0}};
      assign producer1_out_last[endpoint_g] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_last_w[endpoint_g] : 1'b0;
      assign producer1_out_vc[(endpoint_g * VC_W) +: VC_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_vc_w[(endpoint_g * VC_W) +: VC_W] :
          {VC_W{1'b0}};
      assign producer1_out_data[(endpoint_g * DATA_W) +: DATA_W] =
        route_to_producer1_w[endpoint_g] ?
          mesh_endpoint_out_data_w[(endpoint_g * DATA_W) +: DATA_W] :
          {DATA_W{1'b0}};

      assign mesh_endpoint_out_ready_w[endpoint_g] =
        unexpected_ejection_w[endpoint_g] ? 1'b1 :
        route_to_producer0_w[endpoint_g] ? producer0_out_ready[endpoint_g] :
        route_to_producer1_w[endpoint_g] ? producer1_out_ready[endpoint_g] :
        1'b1;
    end
  endgenerate

  assign protocol_error =
    (|injection_protocol_error) || (|ejection_protocol_error);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      ejection_protocol_error <= 16'b0;
    else
      ejection_protocol_error <= ejection_protocol_error | unexpected_ejection_w;
  end

  noc_segmented_mesh4x4 #(
    .DATA_W(DATA_W),
    .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W),
    .VC_W(VC_W),
    .VC_COUNT(VC_COUNT),
    .FIFO_DEPTH(FIFO_DEPTH),
    .COUNTER_W(COUNTER_W),
    .ENABLE_DEBUG_COUNTERS(ENABLE_DEBUG_COUNTERS)
  ) mesh (
    .clk(clk),
    .rst_n(rst_n),
    .endpoint_in_valid(mesh_endpoint_in_valid_w),
    .endpoint_in_ready(mesh_endpoint_in_ready_w),
    .endpoint_in_dest(mesh_endpoint_in_destination_w),
    .endpoint_in_source(mesh_endpoint_in_source_w),
    .endpoint_in_tag(mesh_endpoint_in_tag_w),
    .endpoint_in_fragment(mesh_endpoint_in_fragment_w),
    .endpoint_in_last(mesh_endpoint_in_last_w),
    .endpoint_in_vc(mesh_endpoint_in_vc_w),
    .endpoint_in_data(mesh_endpoint_in_data_w),
    .endpoint_out_valid(mesh_endpoint_out_valid_w),
    .endpoint_out_ready(mesh_endpoint_out_ready_w),
    .endpoint_out_dest(mesh_endpoint_out_destination_w),
    .endpoint_out_source(mesh_endpoint_out_source_w),
    .endpoint_out_tag(mesh_endpoint_out_tag_w),
    .endpoint_out_fragment(mesh_endpoint_out_fragment_w),
    .endpoint_out_last(mesh_endpoint_out_last_w),
    .endpoint_out_vc(mesh_endpoint_out_vc_w),
    .endpoint_out_data(mesh_endpoint_out_data_w),
    .router_accepted_flit_count(router_accepted_flit_count_w),
    .router_forwarded_flit_count(router_forwarded_flit_count_w),
    .router_input_stall_cycles(router_input_stall_cycles_w),
    .router_output_stall_cycles(router_output_stall_cycles_w),
    .router_contention_cycles(router_contention_cycles_w),
    .router_current_input_occupancy(router_current_input_occupancy_w),
    .router_max_input_occupancy(router_max_input_occupancy_w),
    .router_route_flit_count(router_route_flit_count_w)
  );

`ifndef SYNTHESIS
  initial begin
    if (VC_W < 2) begin
      $error("noc_shared_vc_dual_producer_transport4x4 requires VC_W >= 2");
      $finish(1);
    end
  end
`endif
endmodule
