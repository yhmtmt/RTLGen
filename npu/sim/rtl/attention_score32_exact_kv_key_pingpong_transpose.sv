`timescale 1ns/1ps

// Two-buffer K-only transposer. The first canonical flit of each paired-stream
// block supplies its target metadata, so consecutive blocks need no target gap.
module attention_score32_exact_kv_key_pingpong_transpose #(
  parameter integer PRODUCERS = 53
) (
  input  wire clk,
  input  wire rst_n,

  input  wire ingress_valid,
  output wire ingress_ready,
  input  wire [19:0] ingress_tile_byte_addr,
  input  wire [255:0] ingress_data,
  input  wire [31:0] ingress_byte_valid,

  output wire key_valid,
  input  wire key_ready,
  output wire [5:0] key_producer,
  output wire [1:0] key_kv_head,
  output wire key_producer_block,
  output wire [5:0] key_dimension_pair,
  output wire [255:0] key_data,
  output wire key_last,

  output reg protocol_error
);
  reg fill_active_q;
  reg fill_sel_q;
  reg drain_active_q;
  reg drain_sel_q;
  reg [1:0] ready_q;
  reg [6:0] complete_line_count_q;
  reg [5:0] drain_pair_q;

  reg [1:0] buffer_kv_head_q [0:1];
  reg [5:0] buffer_block_slot_q [0:1];
  reg [5:0] buffer_producer_q [0:1];
  reg buffer_producer_block_q [0:1];
  reg [255:0] line_data_mem [0:1][0:63];
  reg [31:0] line_byte_valid_mem [0:1][0:63];

  wire decoded_is_key = !ingress_tile_byte_addr[19];
  wire [1:0] decoded_kv_head = ingress_tile_byte_addr[18:17];
  wire decoded_stream = ingress_tile_byte_addr[16];
  wire [5:0] decoded_block_slot = ingress_tile_byte_addr[15:10];
  wire [2:0] decoded_token_lane = ingress_tile_byte_addr[9:7];
  wire [1:0] decoded_dimension_chunk = ingress_tile_byte_addr[6:5];
  wire ingress_aligned = ingress_tile_byte_addr[4:0] == 5'd0;
  wire [5:0] decoded_line_index =
    {decoded_stream, decoded_token_lane, decoded_dimension_chunk};

  function automatic producer_has_extra;
    input integer producer;
    input [1:0] group_index;
    integer start_index;
    integer stop_index;
    begin
      if (PRODUCERS == 53) begin
        start_index = group_index * 11;
        stop_index = start_index + 11;
      end else begin
        start_index = group_index * 10;
        stop_index = start_index + 10;
      end
      producer_has_extra = (producer >= start_index) && (producer < stop_index);
    end
  endfunction

  function automatic [6:0] map_key_slot;
    input [5:0] block_slot;
    input [1:0] group_index;
    integer producer;
    integer cursor;
    integer block_count;
    integer slot;
    reg found;
    begin
      map_key_slot = 7'd0;
      cursor = 0;
      slot = {26'd0, block_slot};
      found = 1'b0;
      for (producer = 0; producer < PRODUCERS; producer = producer + 1) begin
        block_count = producer_has_extra(producer, group_index) ? 2 : 1;
        if (!found && slot >= cursor && slot < cursor + block_count) begin
          map_key_slot[6:1] = producer[5:0];
          map_key_slot[0] = (slot - cursor) == 1;
          found = 1'b1;
        end
        cursor = cursor + block_count;
      end
    end
  endfunction

  wire buffer0_busy = (fill_active_q && !fill_sel_q) ||
    (drain_active_q && !drain_sel_q) || ready_q[0];
  wire buffer1_busy = (fill_active_q && fill_sel_q) ||
    (drain_active_q && drain_sel_q) || ready_q[1];
  wire free_exists = !buffer0_busy || !buffer1_busy;
  wire free_sel = buffer0_busy;
  wire selected_fill_buffer = fill_active_q ? fill_sel_q : free_sel;

  wire decoded_target_match = !fill_active_q ||
    ((decoded_kv_head == buffer_kv_head_q[fill_sel_q]) &&
     (decoded_block_slot == buffer_block_slot_q[fill_sel_q]));
  wire ingress_metadata_valid = decoded_is_key && ingress_aligned &&
    (ingress_byte_valid != 32'd0) && decoded_target_match;
  wire [31:0] selected_byte_valid = fill_active_q ?
    line_byte_valid_mem[fill_sel_q][decoded_line_index] : 32'd0;
  wire [31:0] merged_byte_valid = selected_byte_valid | ingress_byte_valid;
  wire byte_overlap = |(selected_byte_valid & ingress_byte_valid);
  wire line_completes = ingress_metadata_valid &&
    (selected_byte_valid != 32'hffff_ffff) &&
    (merged_byte_valid == 32'hffff_ffff);
  wire ingress_fire = ingress_valid && ingress_ready;
  wire key_fire = key_valid && key_ready;
  wire fill_finishes = ingress_fire && fill_active_q && ingress_metadata_valid &&
    !byte_overlap && line_completes && complete_line_count_q == 7'd63;
  wire drain_finishes = key_fire && key_last;
  wire [6:0] first_target_mapping = map_key_slot(decoded_block_slot, decoded_kv_head);

  assign ingress_ready = fill_active_q || free_exists;
  assign key_valid = drain_active_q;
  assign key_producer = buffer_producer_q[drain_sel_q];
  assign key_kv_head = buffer_kv_head_q[drain_sel_q];
  assign key_producer_block = buffer_producer_block_q[drain_sel_q];
  assign key_dimension_pair = drain_pair_q;
  assign key_last = drain_pair_q == 6'd63;

  integer lane_i;
  integer dim_i;
  integer chunk_i;
  integer byte_index_i;
  integer line_i;
  integer half_i;
  reg [255:0] key_data_r;
  always @(*) begin
    key_data_r = 256'd0;
    dim_i = 0;
    chunk_i = 0;
    byte_index_i = 0;
    line_i = 0;
    for (half_i = 0; half_i < 2; half_i = half_i + 1) begin
      dim_i = ({26'd0, drain_pair_q} * 2) + half_i;
      chunk_i = dim_i >> 5;
      byte_index_i = dim_i & 31;
      for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
        line_i = lane_i * 4 + chunk_i;
        key_data_r[(half_i * 128) + (lane_i * 8) +: 8] =
          line_data_mem[drain_sel_q][line_i][(byte_index_i * 8) +: 8];
        key_data_r[(half_i * 128) + ((lane_i + 8) * 8) +: 8] =
          line_data_mem[drain_sel_q][line_i + 32][(byte_index_i * 8) +: 8];
      end
    end
  end
  assign key_data = key_data_r;

  integer clear_i;
  integer byte_i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      fill_active_q <= 1'b0;
      fill_sel_q <= 1'b0;
      drain_active_q <= 1'b0;
      drain_sel_q <= 1'b0;
      ready_q <= 2'b00;
      complete_line_count_q <= 7'd0;
      drain_pair_q <= 6'd0;
      protocol_error <= 1'b0;
      for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1) begin
        line_byte_valid_mem[0][clear_i] <= 32'd0;
        line_byte_valid_mem[1][clear_i] <= 32'd0;
      end
    end else begin
      if (ingress_valid && !ingress_ready) begin
        // Legal backpressure; the source must hold its flit.
      end

      if (ingress_fire) begin
        if (!ingress_metadata_valid || byte_overlap) begin
          protocol_error <= 1'b1;
        end else begin
          if (!fill_active_q) begin
            fill_active_q <= 1'b1;
            fill_sel_q <= selected_fill_buffer;
            buffer_kv_head_q[selected_fill_buffer] <= decoded_kv_head;
            buffer_block_slot_q[selected_fill_buffer] <= decoded_block_slot;
            buffer_producer_q[selected_fill_buffer] <= first_target_mapping[6:1];
            buffer_producer_block_q[selected_fill_buffer] <= first_target_mapping[0];
            complete_line_count_q <= line_completes ? 7'd1 : 7'd0;
            for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1)
              line_byte_valid_mem[selected_fill_buffer][clear_i] <= 32'd0;
          end else if (line_completes) begin
            complete_line_count_q <= complete_line_count_q + 1'b1;
          end

          for (byte_i = 0; byte_i < 32; byte_i = byte_i + 1) begin
            if (ingress_byte_valid[byte_i] && !selected_byte_valid[byte_i])
              line_data_mem[selected_fill_buffer][decoded_line_index][(byte_i * 8) +: 8] <=
                ingress_data[(byte_i * 8) +: 8];
          end
          line_byte_valid_mem[selected_fill_buffer][decoded_line_index] <= merged_byte_valid;

          if (fill_finishes) begin
            fill_active_q <= 1'b0;
            complete_line_count_q <= 7'd0;
            if (!drain_active_q) begin
              drain_active_q <= 1'b1;
              drain_sel_q <= fill_sel_q;
              drain_pair_q <= 6'd0;
            end else if (!drain_finishes) begin
              ready_q[fill_sel_q] <= 1'b1;
            end
          end
        end
      end

      if (key_fire && !key_last)
        drain_pair_q <= drain_pair_q + 1'b1;

      if (drain_finishes) begin
        drain_pair_q <= 6'd0;
        if (fill_finishes) begin
          drain_active_q <= 1'b1;
          drain_sel_q <= fill_sel_q;
        end else if (ready_q[~drain_sel_q]) begin
          drain_active_q <= 1'b1;
          drain_sel_q <= ~drain_sel_q;
          ready_q[~drain_sel_q] <= 1'b0;
        end else begin
          drain_active_q <= 1'b0;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if ((PRODUCERS != 53) && (PRODUCERS != 54)) begin
      $error("attention_score32_exact_kv_key_pingpong_transpose PRODUCERS must be 53 or 54");
      $finish(1);
    end
  end
`endif
endmodule
