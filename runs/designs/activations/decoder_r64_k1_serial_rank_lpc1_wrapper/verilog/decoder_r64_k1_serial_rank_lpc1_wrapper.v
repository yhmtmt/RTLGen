`timescale 1ns/1ps
module decoder_r64_k1_serial_rank_lpc1_wrapper(
  input clk,
  input rst_n,
  input in_valid,
  output in_ready,
  input in_last,
  input [15:0] in_base_token_id,
  input [63:0] in_lane_valid,
  input signed [1023:0] in_logits,
  output out_valid,
  input out_ready,
  output out_valid_mask,
  output [15:0] out_token_ids,
  output signed [15:0] out_logits,
  output [31:0] accepted_group_count,
  output [31:0] producer_stall_cycles,
  output [31:0] fifo_max_occupancy,
  output [31:0] final_completion_cycle
);
  wire signed [1023:0] masked_logits;
  assign masked_logits[0 +: 16] = in_lane_valid[0] ? in_logits[0 +: 16] : -16'sd32768;
  assign masked_logits[16 +: 16] = in_lane_valid[1] ? in_logits[16 +: 16] : -16'sd32768;
  assign masked_logits[32 +: 16] = in_lane_valid[2] ? in_logits[32 +: 16] : -16'sd32768;
  assign masked_logits[48 +: 16] = in_lane_valid[3] ? in_logits[48 +: 16] : -16'sd32768;
  assign masked_logits[64 +: 16] = in_lane_valid[4] ? in_logits[64 +: 16] : -16'sd32768;
  assign masked_logits[80 +: 16] = in_lane_valid[5] ? in_logits[80 +: 16] : -16'sd32768;
  assign masked_logits[96 +: 16] = in_lane_valid[6] ? in_logits[96 +: 16] : -16'sd32768;
  assign masked_logits[112 +: 16] = in_lane_valid[7] ? in_logits[112 +: 16] : -16'sd32768;
  assign masked_logits[128 +: 16] = in_lane_valid[8] ? in_logits[128 +: 16] : -16'sd32768;
  assign masked_logits[144 +: 16] = in_lane_valid[9] ? in_logits[144 +: 16] : -16'sd32768;
  assign masked_logits[160 +: 16] = in_lane_valid[10] ? in_logits[160 +: 16] : -16'sd32768;
  assign masked_logits[176 +: 16] = in_lane_valid[11] ? in_logits[176 +: 16] : -16'sd32768;
  assign masked_logits[192 +: 16] = in_lane_valid[12] ? in_logits[192 +: 16] : -16'sd32768;
  assign masked_logits[208 +: 16] = in_lane_valid[13] ? in_logits[208 +: 16] : -16'sd32768;
  assign masked_logits[224 +: 16] = in_lane_valid[14] ? in_logits[224 +: 16] : -16'sd32768;
  assign masked_logits[240 +: 16] = in_lane_valid[15] ? in_logits[240 +: 16] : -16'sd32768;
  assign masked_logits[256 +: 16] = in_lane_valid[16] ? in_logits[256 +: 16] : -16'sd32768;
  assign masked_logits[272 +: 16] = in_lane_valid[17] ? in_logits[272 +: 16] : -16'sd32768;
  assign masked_logits[288 +: 16] = in_lane_valid[18] ? in_logits[288 +: 16] : -16'sd32768;
  assign masked_logits[304 +: 16] = in_lane_valid[19] ? in_logits[304 +: 16] : -16'sd32768;
  assign masked_logits[320 +: 16] = in_lane_valid[20] ? in_logits[320 +: 16] : -16'sd32768;
  assign masked_logits[336 +: 16] = in_lane_valid[21] ? in_logits[336 +: 16] : -16'sd32768;
  assign masked_logits[352 +: 16] = in_lane_valid[22] ? in_logits[352 +: 16] : -16'sd32768;
  assign masked_logits[368 +: 16] = in_lane_valid[23] ? in_logits[368 +: 16] : -16'sd32768;
  assign masked_logits[384 +: 16] = in_lane_valid[24] ? in_logits[384 +: 16] : -16'sd32768;
  assign masked_logits[400 +: 16] = in_lane_valid[25] ? in_logits[400 +: 16] : -16'sd32768;
  assign masked_logits[416 +: 16] = in_lane_valid[26] ? in_logits[416 +: 16] : -16'sd32768;
  assign masked_logits[432 +: 16] = in_lane_valid[27] ? in_logits[432 +: 16] : -16'sd32768;
  assign masked_logits[448 +: 16] = in_lane_valid[28] ? in_logits[448 +: 16] : -16'sd32768;
  assign masked_logits[464 +: 16] = in_lane_valid[29] ? in_logits[464 +: 16] : -16'sd32768;
  assign masked_logits[480 +: 16] = in_lane_valid[30] ? in_logits[480 +: 16] : -16'sd32768;
  assign masked_logits[496 +: 16] = in_lane_valid[31] ? in_logits[496 +: 16] : -16'sd32768;
  assign masked_logits[512 +: 16] = in_lane_valid[32] ? in_logits[512 +: 16] : -16'sd32768;
  assign masked_logits[528 +: 16] = in_lane_valid[33] ? in_logits[528 +: 16] : -16'sd32768;
  assign masked_logits[544 +: 16] = in_lane_valid[34] ? in_logits[544 +: 16] : -16'sd32768;
  assign masked_logits[560 +: 16] = in_lane_valid[35] ? in_logits[560 +: 16] : -16'sd32768;
  assign masked_logits[576 +: 16] = in_lane_valid[36] ? in_logits[576 +: 16] : -16'sd32768;
  assign masked_logits[592 +: 16] = in_lane_valid[37] ? in_logits[592 +: 16] : -16'sd32768;
  assign masked_logits[608 +: 16] = in_lane_valid[38] ? in_logits[608 +: 16] : -16'sd32768;
  assign masked_logits[624 +: 16] = in_lane_valid[39] ? in_logits[624 +: 16] : -16'sd32768;
  assign masked_logits[640 +: 16] = in_lane_valid[40] ? in_logits[640 +: 16] : -16'sd32768;
  assign masked_logits[656 +: 16] = in_lane_valid[41] ? in_logits[656 +: 16] : -16'sd32768;
  assign masked_logits[672 +: 16] = in_lane_valid[42] ? in_logits[672 +: 16] : -16'sd32768;
  assign masked_logits[688 +: 16] = in_lane_valid[43] ? in_logits[688 +: 16] : -16'sd32768;
  assign masked_logits[704 +: 16] = in_lane_valid[44] ? in_logits[704 +: 16] : -16'sd32768;
  assign masked_logits[720 +: 16] = in_lane_valid[45] ? in_logits[720 +: 16] : -16'sd32768;
  assign masked_logits[736 +: 16] = in_lane_valid[46] ? in_logits[736 +: 16] : -16'sd32768;
  assign masked_logits[752 +: 16] = in_lane_valid[47] ? in_logits[752 +: 16] : -16'sd32768;
  assign masked_logits[768 +: 16] = in_lane_valid[48] ? in_logits[768 +: 16] : -16'sd32768;
  assign masked_logits[784 +: 16] = in_lane_valid[49] ? in_logits[784 +: 16] : -16'sd32768;
  assign masked_logits[800 +: 16] = in_lane_valid[50] ? in_logits[800 +: 16] : -16'sd32768;
  assign masked_logits[816 +: 16] = in_lane_valid[51] ? in_logits[816 +: 16] : -16'sd32768;
  assign masked_logits[832 +: 16] = in_lane_valid[52] ? in_logits[832 +: 16] : -16'sd32768;
  assign masked_logits[848 +: 16] = in_lane_valid[53] ? in_logits[848 +: 16] : -16'sd32768;
  assign masked_logits[864 +: 16] = in_lane_valid[54] ? in_logits[864 +: 16] : -16'sd32768;
  assign masked_logits[880 +: 16] = in_lane_valid[55] ? in_logits[880 +: 16] : -16'sd32768;
  assign masked_logits[896 +: 16] = in_lane_valid[56] ? in_logits[896 +: 16] : -16'sd32768;
  assign masked_logits[912 +: 16] = in_lane_valid[57] ? in_logits[912 +: 16] : -16'sd32768;
  assign masked_logits[928 +: 16] = in_lane_valid[58] ? in_logits[928 +: 16] : -16'sd32768;
  assign masked_logits[944 +: 16] = in_lane_valid[59] ? in_logits[944 +: 16] : -16'sd32768;
  assign masked_logits[960 +: 16] = in_lane_valid[60] ? in_logits[960 +: 16] : -16'sd32768;
  assign masked_logits[976 +: 16] = in_lane_valid[61] ? in_logits[976 +: 16] : -16'sd32768;
  assign masked_logits[992 +: 16] = in_lane_valid[62] ? in_logits[992 +: 16] : -16'sd32768;
  assign masked_logits[1008 +: 16] = in_lane_valid[63] ? in_logits[1008 +: 16] : -16'sd32768;
  localparam STATE_IDLE = 2'd0;
  localparam STATE_SCAN = 2'd1;
  localparam STATE_EMIT = 2'd2;
  reg [1:0] state;
  reg signed [1023:0] tile_logits;
  reg [15:0] tile_base_token_id;
  reg tile_last;
  reg [5:0] chunk_index;
  reg best_valid;
  reg signed [15:0] best_logit;
  reg [15:0] best_token_id;
  reg signed [15:0] chunk_logits;
  reg [15:0] chunk_base_token_id;
  wire merge_in_ready;
  wire accept_input = in_valid && in_ready;
  wire emit_done = (state == STATE_EMIT) && merge_in_ready;
  assign in_ready = (state == STATE_IDLE);

  always @* begin
    chunk_logits = '0;
    chunk_base_token_id = tile_base_token_id;
    case (chunk_index)
      6'd0: begin
        chunk_logits = tile_logits[0 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd0;
      end
      6'd1: begin
        chunk_logits = tile_logits[16 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd1;
      end
      6'd2: begin
        chunk_logits = tile_logits[32 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd2;
      end
      6'd3: begin
        chunk_logits = tile_logits[48 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd3;
      end
      6'd4: begin
        chunk_logits = tile_logits[64 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd4;
      end
      6'd5: begin
        chunk_logits = tile_logits[80 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd5;
      end
      6'd6: begin
        chunk_logits = tile_logits[96 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd6;
      end
      6'd7: begin
        chunk_logits = tile_logits[112 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd7;
      end
      6'd8: begin
        chunk_logits = tile_logits[128 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd8;
      end
      6'd9: begin
        chunk_logits = tile_logits[144 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd9;
      end
      6'd10: begin
        chunk_logits = tile_logits[160 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd10;
      end
      6'd11: begin
        chunk_logits = tile_logits[176 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd11;
      end
      6'd12: begin
        chunk_logits = tile_logits[192 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd12;
      end
      6'd13: begin
        chunk_logits = tile_logits[208 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd13;
      end
      6'd14: begin
        chunk_logits = tile_logits[224 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd14;
      end
      6'd15: begin
        chunk_logits = tile_logits[240 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd15;
      end
      6'd16: begin
        chunk_logits = tile_logits[256 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd16;
      end
      6'd17: begin
        chunk_logits = tile_logits[272 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd17;
      end
      6'd18: begin
        chunk_logits = tile_logits[288 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd18;
      end
      6'd19: begin
        chunk_logits = tile_logits[304 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd19;
      end
      6'd20: begin
        chunk_logits = tile_logits[320 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd20;
      end
      6'd21: begin
        chunk_logits = tile_logits[336 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd21;
      end
      6'd22: begin
        chunk_logits = tile_logits[352 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd22;
      end
      6'd23: begin
        chunk_logits = tile_logits[368 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd23;
      end
      6'd24: begin
        chunk_logits = tile_logits[384 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd24;
      end
      6'd25: begin
        chunk_logits = tile_logits[400 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd25;
      end
      6'd26: begin
        chunk_logits = tile_logits[416 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd26;
      end
      6'd27: begin
        chunk_logits = tile_logits[432 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd27;
      end
      6'd28: begin
        chunk_logits = tile_logits[448 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd28;
      end
      6'd29: begin
        chunk_logits = tile_logits[464 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd29;
      end
      6'd30: begin
        chunk_logits = tile_logits[480 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd30;
      end
      6'd31: begin
        chunk_logits = tile_logits[496 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd31;
      end
      6'd32: begin
        chunk_logits = tile_logits[512 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd32;
      end
      6'd33: begin
        chunk_logits = tile_logits[528 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd33;
      end
      6'd34: begin
        chunk_logits = tile_logits[544 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd34;
      end
      6'd35: begin
        chunk_logits = tile_logits[560 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd35;
      end
      6'd36: begin
        chunk_logits = tile_logits[576 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd36;
      end
      6'd37: begin
        chunk_logits = tile_logits[592 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd37;
      end
      6'd38: begin
        chunk_logits = tile_logits[608 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd38;
      end
      6'd39: begin
        chunk_logits = tile_logits[624 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd39;
      end
      6'd40: begin
        chunk_logits = tile_logits[640 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd40;
      end
      6'd41: begin
        chunk_logits = tile_logits[656 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd41;
      end
      6'd42: begin
        chunk_logits = tile_logits[672 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd42;
      end
      6'd43: begin
        chunk_logits = tile_logits[688 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd43;
      end
      6'd44: begin
        chunk_logits = tile_logits[704 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd44;
      end
      6'd45: begin
        chunk_logits = tile_logits[720 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd45;
      end
      6'd46: begin
        chunk_logits = tile_logits[736 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd46;
      end
      6'd47: begin
        chunk_logits = tile_logits[752 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd47;
      end
      6'd48: begin
        chunk_logits = tile_logits[768 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd48;
      end
      6'd49: begin
        chunk_logits = tile_logits[784 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd49;
      end
      6'd50: begin
        chunk_logits = tile_logits[800 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd50;
      end
      6'd51: begin
        chunk_logits = tile_logits[816 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd51;
      end
      6'd52: begin
        chunk_logits = tile_logits[832 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd52;
      end
      6'd53: begin
        chunk_logits = tile_logits[848 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd53;
      end
      6'd54: begin
        chunk_logits = tile_logits[864 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd54;
      end
      6'd55: begin
        chunk_logits = tile_logits[880 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd55;
      end
      6'd56: begin
        chunk_logits = tile_logits[896 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd56;
      end
      6'd57: begin
        chunk_logits = tile_logits[912 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd57;
      end
      6'd58: begin
        chunk_logits = tile_logits[928 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd58;
      end
      6'd59: begin
        chunk_logits = tile_logits[944 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd59;
      end
      6'd60: begin
        chunk_logits = tile_logits[960 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd60;
      end
      6'd61: begin
        chunk_logits = tile_logits[976 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd61;
      end
      6'd62: begin
        chunk_logits = tile_logits[992 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd62;
      end
      6'd63: begin
        chunk_logits = tile_logits[1008 +: 16];
        chunk_base_token_id = tile_base_token_id + 16'd63;
      end
      default: begin
        chunk_logits = tile_logits[0 +: 16];
        chunk_base_token_id = tile_base_token_id;
      end
    endcase
  end
  wire [0:0] chunk_top_index;
  wire signed [15:0] chunk_top_logit;
  logit_rank_r1_l16_k1 chunk_rank (
    .logits(chunk_logits),
    .top_indices(chunk_top_index),
    .top_logits(chunk_top_logit)
  );
  wire [15:0] chunk_top_token_id = chunk_base_token_id + { 15'd0, chunk_top_index };
  wire chunk_beats_best = !best_valid || (chunk_top_logit > best_logit) || ((chunk_top_logit == best_logit) && (chunk_top_token_id < best_token_id));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= STATE_IDLE;
      tile_logits <= '0;
      tile_base_token_id <= '0;
      tile_last <= 1'b0;
      chunk_index <= '0;
      best_valid <= 1'b0;
      best_logit <= '0;
      best_token_id <= '0;
    end else begin
      case (state)
        STATE_IDLE: begin
          if (accept_input) begin
            tile_logits <= masked_logits;
            tile_base_token_id <= in_base_token_id;
            tile_last <= in_last;
            chunk_index <= '0;
            best_valid <= 1'b0;
            best_logit <= '0;
            best_token_id <= '0;
            state <= STATE_SCAN;
          end
        end
        STATE_SCAN: begin
          if (chunk_beats_best) begin
            best_valid <= 1'b1;
            best_logit <= chunk_top_logit;
            best_token_id <= chunk_top_token_id;
          end
          if (chunk_index == 6'd63) begin
            state <= STATE_EMIT;
          end else begin
            chunk_index <= chunk_index + 1'b1;
          end
        end
        STATE_EMIT: begin
          if (emit_done) begin
            state <= STATE_IDLE;
          end
        end
        default: state <= STATE_IDLE;
      endcase
    end
  end
  candidate_stream_merge_fifo_k1_l16_t16_d16 merger (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(state == STATE_EMIT),
    .in_ready(merge_in_ready),
    .in_last(tile_last),
    .in_valid_mask(1'b1),
    .in_token_ids(best_token_id),
    .in_logits(best_logit),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_valid_mask(out_valid_mask),
    .out_token_ids(out_token_ids),
    .out_logits(out_logits),
    .accepted_group_count(accepted_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .fifo_max_occupancy(fifo_max_occupancy),
    .final_completion_cycle(final_completion_cycle)
  );
endmodule
