`timescale 1ns/1ps

// One physical-bank leaf owns two 1024-bit round words.  Keeping this boundary
// explicit lets hierarchical synthesis map the 17 identical storage leaves
// independently instead of constructing one flat multiwrite state vector.
(* keep_hierarchy = "true" *)
module attention_shared_sram_k_round_bank (
  input wire clk,
  input wire write_valid,
  input wire write_buffer,
  input wire [1023:0] write_data,
  input wire read_buffer,
  input wire [3:0] read_dimension,
  output reg [63:0] read_lane
);
  (* keep = "true" *) reg [1023:0] buffer_mem0;
  (* keep = "true" *) reg [1023:0] buffer_mem1;

  always @(posedge clk) begin
    if (write_valid) begin
      if (write_buffer)
        buffer_mem1 <= write_data;
      else
        buffer_mem0 <= write_data;
    end
  end

  always @* begin
    if (read_buffer)
      read_lane = buffer_mem1[read_dimension*64 +: 64];
    else
      read_lane = buffer_mem0[read_dimension*64 +: 64];
  end
endmodule
