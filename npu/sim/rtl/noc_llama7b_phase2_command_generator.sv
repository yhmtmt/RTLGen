`timescale 1ns/1ps

// Generates the complete command stream for the checked Llama7B Phase-2
// schedule. The stream is represented by wave/class/cluster/packet counters;
// no per-packet command image or refill engine is required.
module noc_llama7b_phase2_command_generator #(
  parameter integer COMMAND_W = 102,
  parameter integer COUNTER_W = 32
) (
  input wire clk,
  input wire rst_n,
  input wire enable,

  output wire cmd_valid,
  input wire cmd_ready,
  output wire [COMMAND_W-1:0] cmd_data,

  output reg done,
  output reg [COUNTER_W-1:0] generated_command_count,
  output reg protocol_error
);
  localparam integer EXPECTED_COMMANDS = 11576;

  localparam PHASE_REDUCTION = 1'b0;
  localparam PHASE_SHARED = 1'b1;

  reg [3:0] release_epoch;
  reg phase;
  reg [3:0] cluster;
  reg [6:0] packet;

  reg [31:0] command_release_cycle;
  reg [3:0] command_source;
  reg [3:0] command_destination;
  reg [1:0] command_vc;
  reg [7:0] command_tag;
  reg [13:0] command_packet_id;
  reg [3:0] command_flit_count;

  wire command_fire = cmd_valid && cmd_ready;
  wire [2:0] transfer_wave =
    phase == PHASE_SHARED ? release_epoch[2:0] : release_epoch[2:0] - 1'b1;

  function [31:0] epoch_release_cycle;
    input [3:0] epoch;
    begin
      case (epoch)
        4'd0: epoch_release_cycle = 32'd9341;
        4'd1: epoch_release_cycle = 32'd57311;
        4'd2: epoch_release_cycle = 32'd105281;
        4'd3: epoch_release_cycle = 32'd153251;
        4'd4: epoch_release_cycle = 32'd201221;
        4'd5: epoch_release_cycle = 32'd249190;
        4'd6: epoch_release_cycle = 32'd297160;
        4'd7: epoch_release_cycle = 32'd345130;
        4'd8: epoch_release_cycle = 32'd393100;
        default: epoch_release_cycle = 32'd0;
      endcase
    end
  endfunction

  function [13:0] wave_packet_base;
    input [2:0] wave;
    begin
      case (wave)
        3'd0: wave_packet_base = 14'd0;
        3'd1: wave_packet_base = 14'd1583;
        3'd2: wave_packet_base = 14'd3166;
        3'd3: wave_packet_base = 14'd4749;
        3'd4: wave_packet_base = 14'd6332;
        3'd5: wave_packet_base = 14'd6827;
        3'd6: wave_packet_base = 14'd8410;
        3'd7: wave_packet_base = 14'd9993;
      endcase
    end
  endfunction

  function [3:0] shared_home_shift;
    input [2:0] wave;
    begin
      case (wave)
        3'd0: shared_home_shift = 4'd4;
        3'd1: shared_home_shift = 4'd7;
        3'd2: shared_home_shift = 4'd10;
        3'd3: shared_home_shift = 4'd13;
        3'd4: shared_home_shift = 4'd0;
        3'd5: shared_home_shift = 4'd3;
        3'd6: shared_home_shift = 4'd6;
        3'd7: shared_home_shift = 4'd9;
      endcase
    end
  endfunction

  function [13:0] full_cluster_offset;
    input [3:0] cluster_index;
    reg [13:0] value;
    begin
      value = {10'b0, cluster_index};
      full_cluster_offset =
        (value << 6) + (value << 5) + (value << 2) + value;
    end
  endfunction

  function [13:0] reduction_cluster_offset;
    input [3:0] cluster_index;
    reg [13:0] value;
    begin
      value = {10'b0, cluster_index};
      reduction_cluster_offset = (value << 5) + value;
    end
  endfunction

  function [13:0] shared_packet_id;
    input [2:0] wave;
    input [3:0] cluster_index;
    input [6:0] packet_index;
    begin
      shared_packet_id = wave_packet_base(wave) +
        full_cluster_offset(cluster_index) + {7'b0, packet_index};
    end
  endfunction

  function [13:0] reduction_packet_id;
    input [2:0] wave;
    input [3:0] cluster_index;
    input [6:0] packet_index;
    begin
      if (wave == 3'd4)
        reduction_packet_id = wave_packet_base(wave) +
          reduction_cluster_offset(cluster_index) + {7'b0, packet_index};
      else
        reduction_packet_id = wave_packet_base(wave) +
          full_cluster_offset(cluster_index) + 14'd68 +
          {7'b0, packet_index};
    end
  endfunction

  function [7:0] reduction_tag;
    input [2:0] wave;
    input [6:0] packet_index;
    reg [7:0] wave_tag_base;
    begin
      case (wave)
        3'd0: wave_tag_base = 8'd0;
        3'd1: wave_tag_base = 8'd33;
        3'd2: wave_tag_base = 8'd66;
        3'd3: wave_tag_base = 8'd99;
        3'd4: wave_tag_base = 8'd132;
        3'd5: wave_tag_base = 8'd165;
        3'd6: wave_tag_base = 8'd198;
        3'd7: wave_tag_base = 8'd231;
      endcase
      reduction_tag = wave_tag_base + {1'b0, packet_index};
    end
  endfunction

  always @(*) begin
    command_release_cycle = epoch_release_cycle(release_epoch);
    command_source = 4'd0;
    command_destination = 4'd0;
    command_vc = 2'd0;
    command_tag = 8'd0;
    command_packet_id = 14'd0;
    command_flit_count = 4'd8;

    if (phase == PHASE_SHARED) begin
      command_source = cluster + shared_home_shift(transfer_wave);
      command_destination = cluster;
      command_vc = 2'd0;
      command_tag = {1'b0, packet};
      command_packet_id = shared_packet_id(transfer_wave, cluster, packet);
    end else begin
      command_source = cluster;
      command_destination = 4'd15;
      command_vc = 2'd1;
      command_tag = reduction_tag(transfer_wave, packet);
      command_packet_id = reduction_packet_id(transfer_wave, cluster, packet);
      if (packet == 7'd32)
        command_flit_count = 4'd4;
    end
  end

  assign cmd_valid = enable && !done;
  assign cmd_data = {
    command_flit_count,
    2'b0, command_packet_id, 8'b0,
    2'b0, command_packet_id, 8'b0,
    command_tag,
    command_vc,
    command_destination,
    command_source,
    command_release_cycle
  };

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      release_epoch <= 4'd0;
      phase <= PHASE_SHARED;
      cluster <= 4'd0;
      packet <= 7'd0;
      done <= 1'b0;
      generated_command_count <= {COUNTER_W{1'b0}};
      protocol_error <= 1'b0;
    end else if (command_fire) begin
      generated_command_count <= generated_command_count + 1'b1;
      if (phase == PHASE_SHARED) begin
        if (packet == 7'd67) begin
          packet <= 7'd0;
          if (cluster == 4'd15) begin
            cluster <= 4'd0;
            release_epoch <= release_epoch + 1'b1;
            phase <= PHASE_REDUCTION;
          end else begin
            cluster <= cluster + 1'b1;
          end
        end else begin
          packet <= packet + 1'b1;
        end
      end else begin
        if (packet == 7'd32) begin
          packet <= 7'd0;
          if (cluster == 4'd14) begin
            cluster <= 4'd0;
            if (release_epoch == 4'd8) begin
              done <= 1'b1;
              if (generated_command_count + 1'b1 != EXPECTED_COMMANDS)
                protocol_error <= 1'b1;
            end else if (release_epoch == 4'd4) begin
              release_epoch <= release_epoch + 1'b1;
              phase <= PHASE_REDUCTION;
            end else begin
              phase <= PHASE_SHARED;
            end
          end else begin
            cluster <= cluster + 1'b1;
          end
        end else begin
          packet <= packet + 1'b1;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (COMMAND_W != 102) begin
      $error("noc_llama7b_phase2_command_generator COMMAND_W must be 102");
      $finish(1);
    end
  end
`endif
endmodule
