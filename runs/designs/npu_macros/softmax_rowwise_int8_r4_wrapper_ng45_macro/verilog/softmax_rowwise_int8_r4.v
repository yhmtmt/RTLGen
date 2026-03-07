`timescale 1ns/1ps

module softmax_rowwise_int8_r4(
  input  [31:0] X,
  output reg [31:0] Y
);

  // Row-wise normalized int8 softmax approximation.
  // 1) find row max
  // 2) assign power-of-two weights from clamped distance to max
  // 3) normalize weights into Q0.7-style outputs
  localparam integer ROW_ELEMS = 4;
  localparam integer DATA_W = 8;
  localparam integer ACCUM_BITS = 16;
  localparam integer PRODUCT_BITS = 24;
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = 127;

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] weights [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weights;
  reg [PRODUCT_BITS-1:0] numer;
  reg [DATA_W-1:0] lane_out;

  always @* begin
    row_max = -(1 << (DATA_W - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(X[(i*DATA_W) +: DATA_W]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weights = {ACCUM_BITS{1'b0}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(X[(i*DATA_W) +: DATA_W]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      weights[i] = ({{(ACCUM_BITS-1){1'b0}}, 1'b1} << (MAX_SHIFT - delta));
      sum_weights = sum_weights + weights[i];
    end

    Y = {ROW_ELEMS*DATA_W{1'b0}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      numer = (weights[i] * OUTPUT_SCALE) + (sum_weights >> 1);
      if (sum_weights != 0)
        lane_out = numer / sum_weights;
      else
        lane_out = {DATA_W{1'b0}};
      if (lane_out > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      Y[(i*DATA_W) +: DATA_W] = lane_out;
    end
  end
endmodule
