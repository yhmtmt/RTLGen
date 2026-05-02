`timescale 1ns/1ps

module softmax_rowwise_q12_pwl_tb;
  reg  [47:0] X;
  wire [47:0] Y;

  softmax_rowwise_q12_pwl_r4 dut (.X(X), .Y(Y));

`ifdef SOFTMAX_Q12_PWL_RECIP_Q12_BUCKET8
  localparam [47:0] EXP_EQUAL = {12'd1024, 12'd1024, 12'd1024, 12'd1024};
  localparam [47:0] EXP_LADDER = {12'd1, 12'd63, 12'd466, 12'd3447};
`else
  localparam [47:0] EXP_EQUAL = {12'd1024, 12'd1024, 12'd1024, 12'd1024};
  localparam [47:0] EXP_LADDER = {12'd1, 12'd65, 12'd480, 12'd3549};
`endif

  task check_row;
    input [47:0] a;
    input [47:0] exp;
    begin
      X = a;
      #1;
      if (Y !== exp) begin
        $display(
          "FAIL softmax_rowwise_q12_pwl: got=[%0d,%0d,%0d,%0d] expected=[%0d,%0d,%0d,%0d]",
          Y[11:0], Y[23:12], Y[35:24], Y[47:36],
          exp[11:0], exp[23:12], exp[35:24], exp[47:36]
        );
        $fatal;
      end
    end
  endtask

  initial begin
    check_row({12'd0, 12'd0, 12'd0, 12'd0}, EXP_EQUAL);
    check_row({12'h800, 12'hc00, 12'he00, 12'd0}, EXP_LADDER);
    $display("All q12 PWL row-wise softmax tests passed.");
    $finish;
  end
endmodule
