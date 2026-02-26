(* blackbox *)
module gemm_compute_array (
    input  wire [31:0] slot_a_flat,
    input  wire [31:0] slot_b_flat,
    input  wire signed [31:0] slot_accum_in_flat,
    output wire signed [31:0] slot_accum_next_flat
);
endmodule
