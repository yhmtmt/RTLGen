`timescale 1ns/1ps

// Ready/valid on-chip SRAM endpoint service model.
//
// The block models the part of the decoder-attention service path that was
// still analytic in the cluster scheduler: finite endpoint buffering, finite
// per-bank queues, and a locality-first bank drain policy.
module onchip_service_endpoint #(
  parameter integer DATA_W = 128,
  parameter integer BANKS = 4,
  parameter integer BANK_SEL_W = 2,
  parameter integer BANK_QUEUE_DEPTH = 4,
  parameter integer ENDPOINT_QUEUE_DEPTH = 8,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,

  input wire in_valid,
  output wire in_ready,
  input wire [BANK_SEL_W-1:0] in_bank,
  input wire in_last,
  input wire [DATA_W-1:0] in_data,

  output wire out_valid,
  input wire out_ready,
  output wire [BANK_SEL_W-1:0] out_bank,
  output wire out_last,
  output wire [DATA_W-1:0] out_data,

  output reg [COUNTER_W-1:0] accepted_beat_count,
  output reg [COUNTER_W-1:0] emitted_beat_count,
  output reg [COUNTER_W-1:0] producer_stall_cycles,
  output reg [COUNTER_W-1:0] consumer_stall_cycles,
  output reg [COUNTER_W-1:0] endpoint_max_occupancy,
  output reg [COUNTER_W-1:0] bank_max_occupancy,
  output reg [COUNTER_W-1:0] cycle_count,
  output reg [COUNTER_W-1:0] final_completion_cycle
);
  localparam integer BANK_PTR_W = (BANK_QUEUE_DEPTH <= 1) ? 1 : $clog2(BANK_QUEUE_DEPTH);
  localparam integer BANK_COUNT_W = (BANK_QUEUE_DEPTH <= 1) ? 1 : $clog2(BANK_QUEUE_DEPTH + 1);
  localparam integer TOTAL_COUNT_W = (ENDPOINT_QUEUE_DEPTH <= 1) ? 1 : $clog2(ENDPOINT_QUEUE_DEPTH + 1);
  localparam [BANK_COUNT_W-1:0] BANK_QUEUE_DEPTH_VALUE = BANK_QUEUE_DEPTH;
  localparam [BANK_PTR_W-1:0] BANK_QUEUE_LAST = BANK_QUEUE_DEPTH - 1;
  localparam [TOTAL_COUNT_W-1:0] ENDPOINT_QUEUE_DEPTH_VALUE = ENDPOINT_QUEUE_DEPTH;

  reg [DATA_W-1:0] data_mem [0:BANKS-1][0:BANK_QUEUE_DEPTH-1];
  reg last_mem [0:BANKS-1][0:BANK_QUEUE_DEPTH-1];
  reg [BANK_PTR_W-1:0] rd_ptr [0:BANKS-1];
  reg [BANK_PTR_W-1:0] wr_ptr [0:BANKS-1];
  reg [BANK_COUNT_W-1:0] bank_count [0:BANKS-1];
  reg [TOTAL_COUNT_W-1:0] total_count;
  reg [BANK_SEL_W-1:0] preferred_bank;

  reg any_bank_valid;
  reg [BANK_SEL_W-1:0] grant_bank;

  integer scan_i;
  integer bank_i;
  integer scan_bank_int;
  reg [BANK_SEL_W-1:0] scan_bank;

  always @(*) begin
    any_bank_valid = 1'b0;
    grant_bank = preferred_bank;
    if (bank_count[preferred_bank] != {BANK_COUNT_W{1'b0}}) begin
      any_bank_valid = 1'b1;
      grant_bank = preferred_bank;
    end else begin
      for (scan_i = 1; scan_i <= BANKS; scan_i = scan_i + 1) begin
        scan_bank_int = preferred_bank + scan_i;
        if (scan_bank_int >= BANKS) begin
          scan_bank_int = scan_bank_int - BANKS;
        end
        scan_bank = scan_bank_int[BANK_SEL_W-1:0];
        if (!any_bank_valid && bank_count[scan_bank] != {BANK_COUNT_W{1'b0}}) begin
          any_bank_valid = 1'b1;
          grant_bank = scan_bank;
        end
      end
    end
  end

  assign in_ready =
    (bank_count[in_bank] < BANK_QUEUE_DEPTH_VALUE) &&
    (total_count < ENDPOINT_QUEUE_DEPTH_VALUE);
  assign out_valid = any_bank_valid;
  assign out_bank = grant_bank;
  assign out_last = any_bank_valid ? last_mem[grant_bank][rd_ptr[grant_bank]] : 1'b0;
  assign out_data = any_bank_valid ? data_mem[grant_bank][rd_ptr[grant_bank]] : {DATA_W{1'b0}};

  wire accept_fire = in_valid && in_ready;
  wire emit_fire = out_valid && out_ready;

  function [BANK_PTR_W-1:0] ptr_inc;
    input [BANK_PTR_W-1:0] ptr;
    begin
      if (ptr == BANK_QUEUE_LAST) begin
        ptr_inc = {BANK_PTR_W{1'b0}};
      end else begin
        ptr_inc = ptr + {{(BANK_PTR_W-1){1'b0}}, 1'b1};
      end
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      total_count <= {TOTAL_COUNT_W{1'b0}};
      preferred_bank <= {BANK_SEL_W{1'b0}};
      accepted_beat_count <= {COUNTER_W{1'b0}};
      emitted_beat_count <= {COUNTER_W{1'b0}};
      producer_stall_cycles <= {COUNTER_W{1'b0}};
      consumer_stall_cycles <= {COUNTER_W{1'b0}};
      endpoint_max_occupancy <= {COUNTER_W{1'b0}};
      bank_max_occupancy <= {COUNTER_W{1'b0}};
      cycle_count <= {COUNTER_W{1'b0}};
      final_completion_cycle <= {COUNTER_W{1'b0}};
      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        rd_ptr[bank_i] <= {BANK_PTR_W{1'b0}};
        wr_ptr[bank_i] <= {BANK_PTR_W{1'b0}};
        bank_count[bank_i] <= {BANK_COUNT_W{1'b0}};
      end
    end else begin
      cycle_count <= cycle_count + {{(COUNTER_W-1){1'b0}}, 1'b1};

      if (in_valid && !in_ready) begin
        producer_stall_cycles <= producer_stall_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end
      if (out_valid && !out_ready) begin
        consumer_stall_cycles <= consumer_stall_cycles + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end

      if (accept_fire) begin
        data_mem[in_bank][wr_ptr[in_bank]] <= in_data;
        last_mem[in_bank][wr_ptr[in_bank]] <= in_last;
        wr_ptr[in_bank] <= ptr_inc(wr_ptr[in_bank]);
        accepted_beat_count <= accepted_beat_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
      end

      if (emit_fire) begin
        rd_ptr[grant_bank] <= ptr_inc(rd_ptr[grant_bank]);
        preferred_bank <= grant_bank;
        emitted_beat_count <= emitted_beat_count + {{(COUNTER_W-1){1'b0}}, 1'b1};
        if (out_last) begin
          final_completion_cycle <= cycle_count;
        end
      end

      if (accept_fire && emit_fire) begin
        total_count <= total_count;
        if (in_bank == grant_bank) begin
          bank_count[in_bank] <= bank_count[in_bank];
        end else begin
          bank_count[in_bank] <= bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1};
          bank_count[grant_bank] <= bank_count[grant_bank] - {{(BANK_COUNT_W-1){1'b0}}, 1'b1};
          if ((bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1}) > bank_max_occupancy[BANK_COUNT_W-1:0]) begin
            bank_max_occupancy <= {{(COUNTER_W-BANK_COUNT_W){1'b0}},
                                   bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1}};
          end
        end
      end else if (accept_fire) begin
        total_count <= total_count + {{(TOTAL_COUNT_W-1){1'b0}}, 1'b1};
        bank_count[in_bank] <= bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1};
        if ((bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1}) > bank_max_occupancy[BANK_COUNT_W-1:0]) begin
          bank_max_occupancy <= {{(COUNTER_W-BANK_COUNT_W){1'b0}},
                                 bank_count[in_bank] + {{(BANK_COUNT_W-1){1'b0}}, 1'b1}};
        end
        if ((total_count + {{(TOTAL_COUNT_W-1){1'b0}}, 1'b1}) > endpoint_max_occupancy[TOTAL_COUNT_W-1:0]) begin
          endpoint_max_occupancy <= {{(COUNTER_W-TOTAL_COUNT_W){1'b0}},
                                     total_count + {{(TOTAL_COUNT_W-1){1'b0}}, 1'b1}};
        end
      end else if (emit_fire) begin
        total_count <= total_count - {{(TOTAL_COUNT_W-1){1'b0}}, 1'b1};
        bank_count[grant_bank] <= bank_count[grant_bank] - {{(BANK_COUNT_W-1){1'b0}}, 1'b1};
      end
    end
  end
endmodule
