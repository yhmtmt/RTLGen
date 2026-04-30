`timescale 1ns/1ps

module bf16_recip_norm_tb;
  reg  [63:0] X;
  wire [63:0] Y;

  bf16_recip_norm_r4 dut (.X(X), .Y(Y));

  task check_row;
    input [63:0] a;
    input [63:0] exp;
    begin
      X = a;
      #1;
      if (Y !== exp) begin
        $display(
          "FAIL bf16_recip_norm: got=[%h,%h,%h,%h] expected=[%h,%h,%h,%h]",
          Y[15:0], Y[31:16], Y[47:32], Y[63:48],
          exp[15:0], exp[31:16], exp[47:32], exp[63:48]
        );
        $fatal;
      end
    end
  endtask

  initial begin
    check_row(
      {16'h3f80, 16'h3f80, 16'h3f80, 16'h3f80},
      {16'h3e80, 16'h3e80, 16'h3e80, 16'h3e80}
    );
    check_row(
      {16'h0000, 16'h0000, 16'h0000, 16'h3f80},
      {16'h0000, 16'h0000, 16'h0000, 16'h3f80}
    );
    check_row(
      {16'h0000, 16'h0000, 16'h0000, 16'h0000},
      {16'h0000, 16'h0000, 16'h0000, 16'h0000}
    );
    $display("All bf16 reciprocal-normalization tests passed.");
    $finish;
  end
endmodule
