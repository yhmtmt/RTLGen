`timescale 1ns/1ps

// Converts the canonical planar int8 K/V tile layout into the existing exact
// score32 cluster interfaces. One target is buffered at a time: either one
// 1 KiB V block or the matching pair of 1 KiB K blocks from both streams.
module attention_score32_exact_kv_ingress_transpose #(
  parameter integer PRODUCERS = 53
) (
  input  wire clk,
  input  wire rst_n,

  input  wire target_valid,
  output wire target_ready,
  input  wire target_is_key,
  input  wire [1:0] target_kv_head,
  input  wire target_stream,
  input  wire [5:0] target_block_slot,

  input  wire ingress_valid,
  output wire ingress_ready,
  input  wire [19:0] ingress_tile_byte_addr,
  input  wire [255:0] ingress_data,
  input  wire [31:0] ingress_byte_valid,

  output wire value_valid,
  input  wire value_ready,
  output wire value_stream,
  output wire [1:0] value_kv_head,
  output wire [5:0] value_block_slot,
  output wire [3:0] value_slice,
  output wire [511:0] value_data,
  output wire value_last,

  output wire key_valid,
  input  wire key_ready,
  output wire [5:0] key_producer,
  output wire [1:0] key_kv_head,
  output wire key_producer_block,
  output wire [6:0] key_dimension,
  output wire [127:0] key_data,
  output wire key_last,

  output reg protocol_error
);
  localparam [1:0] STATE_IDLE = 2'd0;
  localparam [1:0] STATE_FILL = 2'd1;
  localparam [1:0] STATE_DRAIN = 2'd2;

  reg [1:0] state_q;
  reg target_is_key_q;
  reg [1:0] target_kv_head_q;
  reg target_stream_q;
  reg [5:0] target_block_slot_q;
  reg [5:0] target_key_producer_q;
  reg target_key_producer_block_q;
  reg [6:0] complete_line_count_q;
  reg [6:0] output_index_q;
  reg [255:0] line_data_mem [0:63];
  reg [31:0] line_byte_valid_mem [0:63];

  wire decoded_is_key = !ingress_tile_byte_addr[19];
  wire [1:0] decoded_kv_head = ingress_tile_byte_addr[18:17];
  wire decoded_stream = ingress_tile_byte_addr[16];
  wire [5:0] decoded_block_slot = ingress_tile_byte_addr[15:10];
  wire [2:0] decoded_token_lane = ingress_tile_byte_addr[9:7];
  wire [1:0] decoded_dimension_chunk = ingress_tile_byte_addr[6:5];
  wire ingress_aligned = ingress_tile_byte_addr[4:0] == 5'd0;
  wire [5:0] decoded_line_index = target_is_key_q ?
    {decoded_stream, decoded_token_lane, decoded_dimension_chunk} :
    {1'b0, decoded_token_lane, decoded_dimension_chunk};
  wire decoded_target_match = ingress_aligned &&
    (decoded_is_key == target_is_key_q) &&
    (decoded_kv_head == target_kv_head_q) &&
    (decoded_block_slot == target_block_slot_q) &&
    (target_is_key_q || (decoded_stream == target_stream_q));
  wire [31:0] selected_byte_valid = line_byte_valid_mem[decoded_line_index];
  wire [31:0] merged_byte_valid = selected_byte_valid | ingress_byte_valid;
  wire line_completes = decoded_target_match &&
    (selected_byte_valid != 32'hffff_ffff) &&
    (merged_byte_valid == 32'hffff_ffff);
  wire byte_overlap = |(selected_byte_valid & ingress_byte_valid);
  wire ingress_fire = ingress_valid && ingress_ready;
  wire value_fire = value_valid && value_ready;
  wire key_fire = key_valid && key_ready;

  integer byte_i;
  integer clear_i;
  integer lane_i;
  integer line_i;
  integer chunk_i;
  integer byte_index_i;

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

  wire [6:0] target_key_mapping = map_key_slot(target_block_slot, target_kv_head);

  assign target_ready = state_q == STATE_IDLE;
  assign ingress_ready = state_q == STATE_FILL;

  assign value_valid = (state_q == STATE_DRAIN) && !target_is_key_q;
  assign value_stream = target_stream_q;
  assign value_kv_head = target_kv_head_q;
  assign value_block_slot = target_block_slot_q;
  assign value_slice = output_index_q[3:0];
  assign value_last = output_index_q == 7'd15;

  assign key_valid = (state_q == STATE_DRAIN) && target_is_key_q;
  assign key_producer = target_key_producer_q;
  assign key_kv_head = target_kv_head_q;
  assign key_producer_block = target_key_producer_block_q;
  assign key_dimension = output_index_q;
  assign key_last = output_index_q == 7'd127;

  reg [511:0] value_data_r;
  reg [127:0] key_data_r;
  always @(*) begin
    value_data_r = 512'd0;
    key_data_r = 128'd0;
    chunk_i = 0;
    byte_index_i = 0;
    line_i = 0;
    if (target_is_key_q) begin
      chunk_i = {30'd0, output_index_q[6:5]};
      byte_index_i = {27'd0, output_index_q[4:0]};
      for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
        line_i = (lane_i * 4) + chunk_i;
        key_data_r[(lane_i * 8) +: 8] =
          line_data_mem[line_i][(byte_index_i * 8) +: 8];
        key_data_r[((lane_i + 8) * 8) +: 8] =
          line_data_mem[line_i + 32][(byte_index_i * 8) +: 8];
      end
    end else begin
      chunk_i = {30'd0, output_index_q[3:2]};
      for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
        line_i = (lane_i * 4) + chunk_i;
        value_data_r[(lane_i * 64) +: 64] =
          line_data_mem[line_i][((output_index_q & 7'h3) * 64) +: 64];
      end
    end
  end
  assign value_data = value_data_r;
  assign key_data = key_data_r;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= STATE_IDLE;
      target_is_key_q <= 1'b0;
      target_kv_head_q <= 2'd0;
      target_stream_q <= 1'b0;
      target_block_slot_q <= 6'd0;
      target_key_producer_q <= 6'd0;
      target_key_producer_block_q <= 1'b0;
      complete_line_count_q <= 7'd0;
      output_index_q <= 7'd0;
      protocol_error <= 1'b0;
      for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1)
        line_byte_valid_mem[clear_i] <= 32'd0;
    end else begin
      if (target_valid && target_ready) begin
        target_is_key_q <= target_is_key;
        target_kv_head_q <= target_kv_head;
        target_stream_q <= target_stream;
        target_block_slot_q <= target_block_slot;
        target_key_producer_q <= target_key_mapping[6:1];
        target_key_producer_block_q <= target_key_mapping[0];
        complete_line_count_q <= 7'd0;
        output_index_q <= 7'd0;
        for (clear_i = 0; clear_i < 64; clear_i = clear_i + 1)
          line_byte_valid_mem[clear_i] <= 32'd0;
        state_q <= STATE_FILL;
      end

      if (ingress_fire) begin
        if (!decoded_target_match || ingress_byte_valid == 32'd0) begin
          protocol_error <= 1'b1;
        end else begin
          if (byte_overlap)
            protocol_error <= 1'b1;
          for (byte_i = 0; byte_i < 32; byte_i = byte_i + 1) begin
            if (ingress_byte_valid[byte_i] && !selected_byte_valid[byte_i])
              line_data_mem[decoded_line_index][(byte_i * 8) +: 8] <=
                ingress_data[(byte_i * 8) +: 8];
          end
          line_byte_valid_mem[decoded_line_index] <= merged_byte_valid;
          if (line_completes) begin
            complete_line_count_q <= complete_line_count_q + 1'b1;
            if ((!target_is_key_q && complete_line_count_q == 7'd31) ||
                (target_is_key_q && complete_line_count_q == 7'd63)) begin
              output_index_q <= 7'd0;
              state_q <= STATE_DRAIN;
            end
          end
        end
      end

      if (value_fire || key_fire) begin
        if ((!target_is_key_q && value_last) || (target_is_key_q && key_last)) begin
          state_q <= STATE_IDLE;
          output_index_q <= 7'd0;
        end else begin
          output_index_q <= output_index_q + 1'b1;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if ((PRODUCERS != 53) && (PRODUCERS != 54)) begin
      $error("attention_score32_exact_kv_ingress_transpose PRODUCERS must be 53 or 54");
      $finish(1);
    end
  end
`endif
endmodule
