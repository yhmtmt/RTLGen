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
  output reg [15:0] generated_descriptor_count,
  output reg protocol_error
);
  localparam PHASE_REFILL = 1'b0;
  localparam PHASE_CONSUME = 1'b1;
  localparam [20:0] TILE_BYTES = 21'h100000;
  localparam [20:0] PLANE_BYTES = 21'h020000;
  localparam [20:0] TAIL_BYTES = 21'h004000;
  localparam [20:0] TAIL_HBM_BYTES = 21'h01c000;
  localparam [20:0] BLOCK_BYTES = 21'h000400;
  localparam [3:0] ALL_PLANES = 4'd8;
  localparam [15:0] EXPECTED_DESCRIPTORS = 16'd49472;

  reg phase_q;
  reg [4:0] layer_q;
  reg [3:0] refill_segment_q;
  reg [1:0] group_q;
  reg [2:0] wave_q;
  reg [3:0] tile_lane_q;
  reg tensor_q;
  reg split_q;
  reg key_special_q;
  reg [5:0] key_block_q;
  reg key_stream_q;

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
    tile_r = 7'd0;
    descriptor_segment_r = 4'd0;
    plane_r = ALL_PLANES;
    source_hbm_r = 1'b1;
    canonical_base_r = 20'd0;
    resident_offset_r = 27'd0;
    payload_r = TILE_BYTES;

    if (phase_q == PHASE_REFILL) begin
      if (refill_segment_q < 4'd2) begin
        tile_r = {3'd0, refill_segment_q};
        descriptor_segment_r = 4'd0;
        resident_offset_r = {3'd0, refill_segment_q, 20'd0};
      end else begin
        tile_r = 7'd2;
        plane_r = refill_segment_q - 4'd2;
        descriptor_segment_r = plane_r;
        canonical_base_r = {plane_r[2:0], 17'd0};
        resident_offset_r = 27'h0200000 + {10'd0, plane_r[2:0], 14'd0};
        payload_r = TAIL_BYTES;
      end
    end else if (!tensor_q) begin
      plane_r = {2'd0, group_q};
      if (key_special_q) begin
        tile_r = 7'd2;
        descriptor_segment_r = {key_stream_q, key_block_q[2:0]};
        canonical_base_r = {1'd0, group_q, 17'd0} +
          {3'd0, key_stream_q, 16'd0} + {4'd0, key_block_q, 10'd0};
        source_hbm_r = key_stream_q || key_block_q >= 6'd16;
        resident_offset_r = 27'h0200000 +
          {11'd0, group_q, 14'd0} + {11'd0, key_block_q, 10'd0};
        payload_r = BLOCK_BYTES;
      end else begin
        tile_r = {wave_q, tile_lane_q};
        if (wave_q == 3'd0 && tile_lane_q >= 4'd2)
          tile_r = {3'd0, tile_lane_q} + 1'b1;
        descriptor_segment_r = {1'b0, group_q, 1'b0};
        canonical_base_r = {1'd0, group_q, 17'd0};
        if (tile_r < 7'd2) begin
          source_hbm_r = 1'b0;
          resident_offset_r = {tile_r, 20'd0} + {7'd0, canonical_base_r};
        end
        payload_r = PLANE_BYTES;
      end
    end else begin
      tile_r = {wave_q, tile_lane_q};
      plane_r = {1'b0, 1'b1, group_q};
      descriptor_segment_r = {plane_r[2:0], 1'b0} + split_q;
      canonical_base_r = {plane_r[2:0], 17'd0} +
        (split_q ? 20'h04000 : 20'd0);
      if (tile_r < 7'd2) begin
        source_hbm_r = 1'b0;
        resident_offset_r = {tile_r, 20'd0} + {7'd0, canonical_base_r};
        payload_r = PLANE_BYTES;
      end else if (tile_r == 7'd2) begin
        resident_offset_r = 27'h0200000 +
          {10'd0, plane_r[2:0], 14'd0};
        source_hbm_r = split_q;
        payload_r = split_q ? TAIL_HBM_BYTES : TAIL_BYTES;
      end else begin
        payload_r = PLANE_BYTES;
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
    layer_q == 5'd31 && group_q == 2'd3 && wave_q == 3'd7 &&
    tile_lane_q == 4'd15 && tensor_q && !split_q;

  wire desc_fire = desc_valid && desc_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      phase_q <= PHASE_REFILL;
      layer_q <= 5'd0;
      refill_segment_q <= 4'd0;
      group_q <= 2'd0;
      wave_q <= 3'd0;
      tile_lane_q <= 4'd0;
      tensor_q <= 1'b0;
      split_q <= 1'b0;
      key_special_q <= 1'b0;
      key_block_q <= 6'd0;
      key_stream_q <= 1'b0;
      done <= 1'b0;
      generated_descriptor_count <= 16'd0;
      protocol_error <= 1'b0;
    end else if (desc_fire) begin
      generated_descriptor_count <= generated_descriptor_count + 1'b1;
      if (phase_q == PHASE_REFILL) begin
        if (refill_segment_q == 4'd9) begin
          phase_q <= PHASE_CONSUME;
          group_q <= 2'd0;
          wave_q <= 3'd0;
          tile_lane_q <= 4'd0;
          tensor_q <= 1'b0;
          split_q <= 1'b0;
          key_special_q <= 1'b0;
          key_block_q <= 6'd0;
          key_stream_q <= 1'b0;
        end else begin
          refill_segment_q <= refill_segment_q + 1'b1;
        end
      end else if (!tensor_q && key_special_q) begin
        if (!key_stream_q) begin
          key_stream_q <= 1'b1;
        end else begin
          key_stream_q <= 1'b0;
          if (key_block_q != 6'd63) begin
            key_block_q <= key_block_q + 1'b1;
          end else begin
            key_block_q <= 6'd0;
            key_special_q <= 1'b0;
            tensor_q <= 1'b1;
            tile_lane_q <= 4'd0;
          end
        end
      end else if (!tensor_q) begin
        if ((wave_q == 3'd0 && tile_lane_q != 4'd14) ||
            (wave_q != 3'd0 && tile_lane_q != 4'd15)) begin
          tile_lane_q <= tile_lane_q + 1'b1;
        end else if (wave_q == 3'd0) begin
          tile_lane_q <= 4'd0;
          key_special_q <= 1'b1;
          key_block_q <= 6'd0;
          key_stream_q <= 1'b0;
        end else begin
          tile_lane_q <= 4'd0;
          tensor_q <= 1'b1;
        end
      end else if ({wave_q, tile_lane_q} == 7'd2 && !split_q) begin
        split_q <= 1'b1;
      end else begin
        split_q <= 1'b0;
        if (tile_lane_q != 4'd15) begin
          tile_lane_q <= tile_lane_q + 1'b1;
        end else begin
          tile_lane_q <= 4'd0;
          tensor_q <= 1'b0;
          if (wave_q != 3'd7) begin
            wave_q <= wave_q + 1'b1;
          end else begin
            wave_q <= 3'd0;
            if (group_q != 2'd3) begin
              group_q <= group_q + 1'b1;
            end else if (layer_q == 5'd31) begin
              done <= 1'b1;
              if (generated_descriptor_count + 1'b1 != EXPECTED_DESCRIPTORS)
                protocol_error <= 1'b1;
            end else begin
              phase_q <= PHASE_REFILL;
              layer_q <= layer_q + 1'b1;
              refill_segment_q <= 4'd0;
              group_q <= 2'd0;
            end
          end
        end
      end
    end
  end
endmodule
