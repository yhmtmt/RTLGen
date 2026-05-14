`timescale 1ns/1ps

module candidate_stream_merge_fifo_k1_l16_t16_d16(
  input  clk,
  input  rst_n,
  input  in_valid,
  output in_ready,
  input  in_last,
  input  [0:0] in_valid_mask,
  input  [15:0] in_token_ids,
  input  signed [15:0] in_logits,
  output reg out_valid,
  input  out_ready,
  output reg [0:0] out_valid_mask,
  output reg [15:0] out_token_ids,
  output reg signed [15:0] out_logits,
  output reg [31:0] accepted_group_count,
  output reg [31:0] producer_stall_cycles,
  output reg [31:0] fifo_max_occupancy,
  output reg [31:0] final_completion_cycle
);

  // CandidateStream ready-valid merger for decoder logit-rank streaming.
  // Ordering contract: larger logit wins; exact ties keep the lower token id.
  // Observable counters match the perf-sim/RTL equivalence contract.
  localparam integer TOP_K = 1;
  localparam integer LOGIT_W = 16;
  localparam integer TOKEN_ID_W = 16;
  localparam integer FIFO_DEPTH = 16;
  localparam integer PTR_W = 4;
  localparam integer COUNT_W = 32;

  localparam [COUNT_W-1:0] FIFO_DEPTH_COUNT = 32'd16;
  localparam [PTR_W-1:0] FIFO_LAST_PTR = 4'd15;

  reg fifo_last [0:FIFO_DEPTH-1];
  reg [TOP_K-1:0] fifo_mask [0:FIFO_DEPTH-1];
  reg [TOP_K*TOKEN_ID_W-1:0] fifo_token_ids [0:FIFO_DEPTH-1];
  reg signed [TOP_K*LOGIT_W-1:0] fifo_logits [0:FIFO_DEPTH-1];
  reg [PTR_W-1:0] rd_ptr;
  reg [PTR_W-1:0] wr_ptr;
  reg [COUNT_W-1:0] occupancy;
  reg [COUNT_W-1:0] cycle_count;

  reg [TOP_K-1:0] top_valid;
  reg [TOKEN_ID_W-1:0] top_token [0:TOP_K-1];
  reg signed [LOGIT_W-1:0] top_logit [0:TOP_K-1];
  reg [TOP_K-1:0] work_valid;
  reg [TOKEN_ID_W-1:0] work_token [0:TOP_K-1];
  reg signed [LOGIT_W-1:0] work_logit [0:TOP_K-1];
  reg [TOP_K-1:0] read_mask;
  reg [TOP_K*TOKEN_ID_W-1:0] read_token_ids;
  reg signed [TOP_K*LOGIT_W-1:0] read_logits;
  reg read_last;
  reg [TOKEN_ID_W-1:0] cand_token;
  reg signed [LOGIT_W-1:0] cand_logit;
  integer i;
  integer k;
  integer insert_pos;
  integer pop_group;
  integer push_group;

  assign in_ready = (occupancy < FIFO_DEPTH_COUNT);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rd_ptr <= {PTR_W{1'b0}};
      wr_ptr <= {PTR_W{1'b0}};
      occupancy <= {COUNT_W{1'b0}};
      cycle_count <= {COUNT_W{1'b0}};
      accepted_group_count <= {COUNT_W{1'b0}};
      producer_stall_cycles <= {COUNT_W{1'b0}};
      fifo_max_occupancy <= {COUNT_W{1'b0}};
      final_completion_cycle <= {COUNT_W{1'b0}};
      out_valid <= 1'b0;
      out_valid_mask <= {TOP_K{1'b0}};
      out_token_ids <= {TOP_K*TOKEN_ID_W{1'b0}};
      out_logits <= {TOP_K*LOGIT_W{1'b0}};
      top_valid <= {TOP_K{1'b0}};
      for (i = 0; i < TOP_K; i = i + 1) begin
        top_token[i] <= {TOKEN_ID_W{1'b0}};
        top_logit[i] <= {LOGIT_W{1'b0}};
      end
    end else begin
      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};
      push_group = in_valid && in_ready;
      pop_group = (occupancy != {COUNT_W{1'b0}}) && !out_valid;

      if (in_valid && !in_ready)
        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};

      if (out_valid && out_ready) begin
        out_valid <= 1'b0;
        top_valid <= {TOP_K{1'b0}};
      end

      if (push_group) begin
        fifo_last[wr_ptr] <= in_last;
        fifo_mask[wr_ptr] <= in_valid_mask;
        fifo_token_ids[wr_ptr] <= in_token_ids;
        fifo_logits[wr_ptr] <= in_logits;
        accepted_group_count <= accepted_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};
        if (wr_ptr == FIFO_LAST_PTR)
          wr_ptr <= {PTR_W{1'b0}};
        else
          wr_ptr <= wr_ptr + {{(PTR_W-1){1'b0}}, 1'b1};
      end

      if (pop_group) begin
        read_last = fifo_last[rd_ptr];
        read_mask = fifo_mask[rd_ptr];
        read_token_ids = fifo_token_ids[rd_ptr];
        read_logits = fifo_logits[rd_ptr];
        work_valid = top_valid;
        for (i = 0; i < TOP_K; i = i + 1) begin
          work_token[i] = top_token[i];
          work_logit[i] = top_logit[i];
        end

        for (i = 0; i < TOP_K; i = i + 1) begin
          if (read_mask[i]) begin
            cand_token = read_token_ids[(i*TOKEN_ID_W) +: TOKEN_ID_W];
            cand_logit = $signed(read_logits[(i*LOGIT_W) +: LOGIT_W]);
            insert_pos = TOP_K;
            for (k = 0; k < TOP_K; k = k + 1) begin
              if ((insert_pos == TOP_K) && (!work_valid[k] || (cand_logit > work_logit[k]) || ((cand_logit == work_logit[k]) && (cand_token < work_token[k]))))
                insert_pos = k;
            end
            if (insert_pos < TOP_K) begin
              for (k = TOP_K - 1; k > 0; k = k - 1) begin
                if (k > insert_pos) begin
                  work_valid[k] = work_valid[k-1];
                  work_token[k] = work_token[k-1];
                  work_logit[k] = work_logit[k-1];
                end
              end
              work_valid[insert_pos] = 1'b1;
              work_token[insert_pos] = cand_token;
              work_logit[insert_pos] = cand_logit;
            end
          end
        end

        top_valid <= work_valid;
        for (i = 0; i < TOP_K; i = i + 1) begin
          top_token[i] <= work_token[i];
          top_logit[i] <= work_logit[i];
        end
        if (read_last) begin
          out_valid <= 1'b1;
          out_valid_mask <= work_valid;
          for (i = 0; i < TOP_K; i = i + 1) begin
            out_token_ids[(i*TOKEN_ID_W) +: TOKEN_ID_W] <= work_token[i];
            out_logits[(i*LOGIT_W) +: LOGIT_W] <= work_logit[i];
          end
          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};
        end
        if (rd_ptr == FIFO_LAST_PTR)
          rd_ptr <= {PTR_W{1'b0}};
        else
          rd_ptr <= rd_ptr + {{(PTR_W-1){1'b0}}, 1'b1};
      end

      if (push_group && !pop_group)
        occupancy <= occupancy + {{(COUNT_W-1){1'b0}}, 1'b1};
      else if (!push_group && pop_group)
        occupancy <= occupancy - {{(COUNT_W-1){1'b0}}, 1'b1};

      if ((occupancy + (push_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}}) - (pop_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}})) > fifo_max_occupancy)
        fifo_max_occupancy <= occupancy + (push_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}}) - (pop_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}});
    end
  end
endmodule
