`timescale 1ns/1ps

// Waits until all 16 cluster ingress paths have the same filled-wave command,
// then commits that command atomically with the generated score hierarchy.
module attention_score32_exact_kv_wave_command_barrier16 (
  input wire clk,
  input wire rst_n,
  input wire [15:0] cluster_command_valid,
  output wire [15:0] cluster_command_ready,
  input wire [16*16-1:0] cluster_command_id,
  input wire [16*5-1:0] cluster_command_head_base,
  input wire [16*3-1:0] cluster_command_wave_index,
  input wire [16*5-1:0] cluster_command_layer,
  output wire hierarchy_command_valid,
  input wire hierarchy_command_ready,
  output wire [15:0] hierarchy_command_id,
  output wire [4:0] hierarchy_command_head_base,
  output wire [2:0] hierarchy_command_wave_index,
  output wire [4:0] hierarchy_command_layer,
  output reg [10:0] completed_wave_count,
  output reg protocol_error
);
  reg metadata_match_r;
  integer cluster_i;

  always @(*) begin
    metadata_match_r = 1'b1;
    for (cluster_i = 1; cluster_i < 16; cluster_i = cluster_i + 1) begin
      if (cluster_command_id[(cluster_i*16) +: 16] != cluster_command_id[0 +: 16] ||
          cluster_command_head_base[(cluster_i*5) +: 5] !=
            cluster_command_head_base[0 +: 5] ||
          cluster_command_wave_index[(cluster_i*3) +: 3] !=
            cluster_command_wave_index[0 +: 3] ||
          cluster_command_layer[(cluster_i*5) +: 5] !=
            cluster_command_layer[0 +: 5])
        metadata_match_r = 1'b0;
    end
  end

  wire all_clusters_valid = &cluster_command_valid;
  assign hierarchy_command_valid = all_clusters_valid && metadata_match_r &&
    !protocol_error;
  assign cluster_command_ready = {16{
    hierarchy_command_valid && hierarchy_command_ready
  }};
  assign hierarchy_command_id = cluster_command_id[0 +: 16];
  assign hierarchy_command_head_base = cluster_command_head_base[0 +: 5];
  assign hierarchy_command_wave_index = cluster_command_wave_index[0 +: 3];
  assign hierarchy_command_layer = cluster_command_layer[0 +: 5];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      completed_wave_count <= 11'd0;
      protocol_error <= 1'b0;
    end else begin
      if (all_clusters_valid && !metadata_match_r)
        protocol_error <= 1'b1;
      if (hierarchy_command_valid && hierarchy_command_ready)
        completed_wave_count <= completed_wave_count + 1'b1;
    end
  end
endmodule
