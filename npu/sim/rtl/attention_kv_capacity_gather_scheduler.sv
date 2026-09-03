`timescale 1ns/1ps

// Exact Llama7B int8 K/V gather schedule for a 68 MiB shared resident cache.
// The external HBM controller/PHY is outside this boundary; its returned byte
// ranges enter at four explicit corner endpoints.
module attention_kv_capacity_gather_scheduler (
  input  wire clk,
  input  wire rst_n,
  input  wire enable,

  output wire desc_valid,
  input  wire desc_ready,
  output wire [4:0] desc_layer,
  output wire [6:0] desc_tile,
  output wire [3:0] desc_segment,
  output wire desc_operation_consume,
  output wire desc_source_hbm,
  output wire [3:0] desc_source_endpoint,
  output wire [3:0] desc_destination_cluster,
  output wire [3:0] desc_plane,
  output wire [19:0] desc_canonical_base_address,
  output wire [33:0] desc_source_byte_address,
  output wire desc_destination_is_resident_cache,
  output wire [33:0] desc_destination_byte_address,
  output wire [20:0] desc_payload_bytes,
  output wire desc_last,

  output reg done,
  output reg [12:0] generated_descriptor_count,
  output reg protocol_error
);
  localparam PHASE_REFILL = 1'b0;
  localparam PHASE_CONSUME = 1'b1;
  localparam [20:0] TILE_BYTES = 21'h100000;
  localparam [20:0] TAIL_BYTES = 21'h004000;
  localparam [20:0] TAIL_HBM_BYTES = 21'h01c000;
  localparam [3:0] ALL_PLANES = 4'd8;
  localparam [12:0] EXPECTED_DESCRIPTORS = 13'd4896;

  reg phase_q;
  reg [4:0] layer_q;
  reg [6:0] tile_q;
  reg [3:0] segment_q;

  reg [6:0] tile_r;
  reg [3:0] descriptor_segment_r;
  reg [3:0] plane_r;
  reg source_hbm_r;
  reg [19:0] canonical_base_r;
  reg [26:0] resident_offset_r;
  reg [20:0] payload_r;
  reg [33:0] hbm_address_r;
  reg [33:0] resident_address_r;
  reg [3:0] destination_cluster_r;
  reg [1:0] hbm_port_r;
  reg [3:0] source_endpoint_r;

  function automatic [3:0] hbm_corner_endpoint;
    input [1:0] selector;
    begin
      case (selector)
        2'd0: hbm_corner_endpoint = 4'd0;
        2'd1: hbm_corner_endpoint = 4'd3;
        2'd2: hbm_corner_endpoint = 4'd12;
        default: hbm_corner_endpoint = 4'd15;
      endcase
    end
  endfunction

  always @(*) begin
    tile_r = tile_q;
    descriptor_segment_r = segment_q;
    plane_r = ALL_PLANES;
    source_hbm_r = 1'b1;
    canonical_base_r = 20'd0;
    resident_offset_r = 27'd0;
    payload_r = TILE_BYTES;

    if (phase_q == PHASE_REFILL) begin
      if (segment_q < 4'd2) begin
        tile_r = {3'd0, segment_q};
        descriptor_segment_r = 4'd0;
        resident_offset_r = {3'd0, segment_q, 20'd0};
      end else begin
        tile_r = 7'd2;
        plane_r = segment_q - 4'd2;
        descriptor_segment_r = plane_r;
        canonical_base_r = {plane_r[2:0], 17'd0};
        resident_offset_r = 27'h0200000 + {10'd0, plane_r[2:0], 14'd0};
        payload_r = TAIL_BYTES;
      end
    end else begin
      if (tile_q < 7'd2) begin
        source_hbm_r = 1'b0;
        resident_offset_r = {tile_q, 20'd0};
      end else if (tile_q == 7'd2) begin
        plane_r = {1'b0, segment_q[3:1]};
        canonical_base_r = {plane_r[2:0], 17'd0} +
          (segment_q[0] ? 20'h04000 : 20'd0);
        resident_offset_r = 27'h0200000 +
          {10'd0, plane_r[2:0], 14'd0};
        source_hbm_r = segment_q[0];
        payload_r = segment_q[0] ? TAIL_HBM_BYTES : TAIL_BYTES;
      end
    end

    destination_cluster_r =
      {layer_q[2:0], 1'b0} + layer_q[3:0] + tile_r[3:0];
    hbm_port_r = layer_q[1:0] + tile_r[1:0] +
      ((plane_r == ALL_PLANES) ? 2'd0 : plane_r[1:0]);
    source_endpoint_r = source_hbm_r ?
      hbm_corner_endpoint(hbm_port_r) : destination_cluster_r;
    hbm_address_r = {2'd0, layer_q, 27'd0} +
      {7'd0, tile_r, 20'd0} + {14'd0, canonical_base_r};
    resident_address_r =
      ({8'd0, layer_q, 21'd0} + {12'd0, layer_q, 17'd0}) +
      {7'd0, resident_offset_r};
  end

  assign desc_valid = enable && !done;
  assign desc_layer = layer_q;
  assign desc_tile = tile_r;
  assign desc_segment = descriptor_segment_r;
  assign desc_operation_consume = phase_q == PHASE_CONSUME;
  assign desc_source_hbm = source_hbm_r;
  assign desc_source_endpoint = source_endpoint_r;
  assign desc_destination_cluster = destination_cluster_r;
  assign desc_plane = plane_r;
  assign desc_canonical_base_address = canonical_base_r;
  assign desc_source_byte_address = source_hbm_r ?
    hbm_address_r : resident_address_r;
  assign desc_destination_is_resident_cache = phase_q == PHASE_REFILL;
  assign desc_destination_byte_address = phase_q == PHASE_REFILL ?
    resident_address_r : {14'd0, canonical_base_r};
  assign desc_payload_bytes = payload_r;
  assign desc_last = phase_q == PHASE_CONSUME &&
    layer_q == 5'd31 && tile_q == 7'd127;

  wire desc_fire = desc_valid && desc_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      phase_q <= PHASE_REFILL;
      layer_q <= 5'd0;
      tile_q <= 7'd0;
      segment_q <= 4'd0;
      done <= 1'b0;
      generated_descriptor_count <= 13'd0;
      protocol_error <= 1'b0;
    end else if (desc_fire) begin
      generated_descriptor_count <= generated_descriptor_count + 1'b1;
      if (phase_q == PHASE_REFILL) begin
        if (segment_q == 4'd9) begin
          phase_q <= PHASE_CONSUME;
          tile_q <= 7'd0;
          segment_q <= 4'd0;
        end else begin
          segment_q <= segment_q + 1'b1;
        end
      end else if (tile_q == 7'd2 && segment_q != 4'd15) begin
        segment_q <= segment_q + 1'b1;
      end else if (tile_q == 7'd127) begin
        if (layer_q == 5'd31) begin
          done <= 1'b1;
          if (generated_descriptor_count + 1'b1 != EXPECTED_DESCRIPTORS)
            protocol_error <= 1'b1;
        end else begin
          phase_q <= PHASE_REFILL;
          layer_q <= layer_q + 1'b1;
          tile_q <= 7'd0;
          segment_q <= 4'd0;
        end
      end else begin
        tile_q <= tile_q + 1'b1;
        segment_q <= 4'd0;
      end
    end
  end
endmodule
