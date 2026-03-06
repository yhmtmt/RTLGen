`timescale 1ns/1ps

module softmax_rowwise_tb;
  reg  [31:0] X;
  wire [31:0] Y;

  softmax_rowwise_int8_r4 dut (.X(X), .Y(Y));

  task check_row;
    input [31:0] a;
    input [31:0] exp;
    begin
      X = a;
      #1;
      if (Y !== exp) begin
        $display(
          "FAIL softmax_rowwise: X=[%0d,%0d,%0d,%0d] got=[%0d,%0d,%0d,%0d] expected=[%0d,%0d,%0d,%0d]",
          $signed(a[7:0]), $signed(a[15:8]), $signed(a[23:16]), $signed(a[31:24]),
          Y[7:0], Y[15:8], Y[23:16], Y[31:24],
          exp[7:0], exp[15:8], exp[23:16], exp[31:24]
        );
        $fatal;
      end
    end
  endtask

  initial begin
    check_row({8'd0, 8'd0, 8'd0, 8'd0}, {8'd32, 8'd32, 8'd32, 8'd32});
    check_row({8'd0, 8'd0, 8'd0, 8'd4}, {8'd7, 8'd7, 8'd7, 8'd107});
    check_row({8'd8, 8'd4, 8'd0, 8'hfc}, {8'd118, 8'd7, 8'd1, 8'd1});
    $display("All row-wise softmax tests passed.");
    $finish;
  end
endmodule
