`timescale 1ns/1ps

module logit_rank_r64_l16_k1(
  input  signed [1023:0] logits,
  output reg [5:0] top_indices,
  output reg signed [15:0] top_logits
);

  // Row-wise logit-only rank selection.
  // Primary key: larger logit. Exact ties retain the lowest lane index.
  localparam integer ROW_ELEMS = 64;
  localparam integer LOGIT_W = 16;
  localparam integer TOP_K = 1;
  localparam integer INDEX_W = 6;

  integer i;
  integer k;
  integer insert_pos;
  reg [TOP_K-1:0] top_valid;
  reg [INDEX_W-1:0] lane_index;
  reg [INDEX_W-1:0] top_index_k;
  reg signed [LOGIT_W-1:0] logit_i;
  reg signed [LOGIT_W-1:0] top_logit_k;

  always @* begin
    top_indices = {6{1'b0}};
    top_logits = {16{1'b0}};
    top_valid = {TOP_K{1'b0}};

    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_index = i;
      logit_i = $signed(logits[(i*LOGIT_W) +: LOGIT_W]);
      insert_pos = TOP_K;
      for (k = 0; k < TOP_K; k = k + 1) begin
        top_index_k = top_indices[(k*INDEX_W) +: INDEX_W];
        top_logit_k = $signed(top_logits[(k*LOGIT_W) +: LOGIT_W]);
        if ((insert_pos == TOP_K) && (!top_valid[k] || (logit_i > top_logit_k) || ((logit_i == top_logit_k) && (lane_index < top_index_k))))
          insert_pos = k;
      end

      if (insert_pos < TOP_K) begin
        for (k = TOP_K - 1; k > 0; k = k - 1) begin
          if (k > insert_pos) begin
            top_indices[(k*INDEX_W) +: INDEX_W] = top_indices[((k-1)*INDEX_W) +: INDEX_W];
            top_logits[(k*LOGIT_W) +: LOGIT_W] = top_logits[((k-1)*LOGIT_W) +: LOGIT_W];
            top_valid[k] = top_valid[k-1];
          end
        end
        top_indices[(insert_pos*INDEX_W) +: INDEX_W] = lane_index;
        top_logits[(insert_pos*LOGIT_W) +: LOGIT_W] = logit_i;
        top_valid[insert_pos] = 1'b1;
      end
    end
  end
endmodule
