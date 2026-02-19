`timescale 1ns/1ps

module tb_cpp_vec_act_fp16_smoke;
  localparam [17:0] FP_ZERO    = {2'b01, 16'h0000};
  localparam [17:0] FP_ONE     = {2'b01, 1'b0, 5'd15, 10'd0};
  localparam [17:0] FP_HALF    = {2'b01, 1'b0, 5'd14, 10'd0};
  localparam [17:0] FP_QTR     = {2'b01, 1'b0, 5'd13, 10'd0};
  localparam [17:0] FP_NEG_ONE = {2'b01, 1'b1, 5'd15, 10'd0};

  wire [17:0] y_relu;
  wire [17:0] y_gelu;
  wire [17:0] y_softmax;
  wire [17:0] y_layernorm;
  wire [17:0] y_drelu;
  wire [17:0] y_dgelu;
  wire [17:0] y_dsoftmax;
  wire [17:0] y_dlayernorm;

  vec_act_fp16_relu_fp16 u_relu (
    .X(FP_NEG_ONE),
    .Y(y_relu)
  );

  vec_act_fp16_gelu_fp16 u_gelu (
    .X(FP_ONE),
    .Y(y_gelu)
  );

  vec_act_fp16_softmax_fp16 u_softmax (
    .X(FP_ONE),
    .Y(y_softmax)
  );

  vec_act_fp16_layernorm_fp16 u_layernorm (
    .X(FP_NEG_ONE),
    .Y(y_layernorm)
  );

  vec_act_fp16_drelu_fp16 u_drelu (
    .X(FP_ONE),
    .Y(y_drelu)
  );

  vec_act_fp16_dgelu_fp16 u_dgelu (
    .X(FP_ONE),
    .Y(y_dgelu)
  );

  vec_act_fp16_dsoftmax_fp16 u_dsoftmax (
    .X(FP_ONE),
    .Y(y_dsoftmax)
  );

  vec_act_fp16_dlayernorm_fp16 u_dlayernorm (
    .X(FP_NEG_ONE),
    .Y(y_dlayernorm)
  );

  initial begin
    #1;
    if (y_relu !== FP_ZERO) begin
      $display("FAIL: relu expected %h got %h", FP_ZERO, y_relu);
      $fatal(1);
    end
    if (y_gelu !== FP_HALF) begin
      $display("FAIL: gelu expected %h got %h", FP_HALF, y_gelu);
      $fatal(1);
    end
    if (y_softmax !== FP_ONE) begin
      $display("FAIL: softmax expected %h got %h", FP_ONE, y_softmax);
      $fatal(1);
    end
    if (y_layernorm !== FP_NEG_ONE) begin
      $display("FAIL: layernorm expected %h got %h", FP_NEG_ONE, y_layernorm);
      $fatal(1);
    end
    if (y_drelu !== FP_ONE) begin
      $display("FAIL: drelu expected %h got %h", FP_ONE, y_drelu);
      $fatal(1);
    end
    if (y_dgelu !== FP_HALF) begin
      $display("FAIL: dgelu expected %h got %h", FP_HALF, y_dgelu);
      $fatal(1);
    end
    if (y_dsoftmax !== FP_QTR) begin
      $display("FAIL: dsoftmax expected %h got %h", FP_QTR, y_dsoftmax);
      $fatal(1);
    end
    if (y_dlayernorm !== FP_ONE) begin
      $display("FAIL: dlayernorm expected %h got %h", FP_ONE, y_dlayernorm);
      $fatal(1);
    end
    $display("PASS: C++ fp16 activation smoke");
    $finish;
  end
endmodule
