(* blackbox *)
module fakeram45_64x32 (
    output wire [31:0] rd_out,
    input  wire [5:0]  addr_in,
    input  wire        we_in,
    input  wire [31:0] wd_in,
    input  wire [31:0] w_mask_in,
    input  wire        clk,
    input  wire        ce_in
);
endmodule
