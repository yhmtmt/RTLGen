`timescale 1ns/1ps

// Holds one descriptor ownership token per destination until its terminal
// packet completes at ejection. Packets within a descriptor remain pipelined.
module attention_kv_destination_descriptor_guard16 (
  input wire clk,
  input wire rst_n,

  input wire descriptor_valid,
  output wire descriptor_ready,
  input wire [3:0] descriptor_source,
  input wire [3:0] descriptor_destination,
  output wire guarded_valid,
  input wire guarded_ready,

  input wire [15:0] packet_command_accept,
  input wire [16*4-1:0] packet_command_source,
  input wire [16*4-1:0] packet_command_destination,
  input wire [16*8-1:0] packet_command_tag,
  input wire [15:0] packet_command_descriptor_last,

  input wire [15:0] packet_completion_valid,
  input wire [16*4-1:0] packet_completion_source,
  input wire [16*8-1:0] packet_completion_tag,

  output reg [15:0] destination_locked,
  output reg [15:0] descriptor_final_pending,
  output wire [16*4-1:0] locked_descriptor_source,
  output reg [15:0] accepted_descriptor_count,
  output reg [15:0] completed_descriptor_count,
  output reg protocol_error
);
  reg [3:0] locked_source_q [0:15];
  reg [7:0] final_tag_q [0:15];
  reg [15:0] final_accept_valid_r;
  reg [3:0] final_accept_source_r [0:15];
  reg [7:0] final_accept_tag_r [0:15];
  reg duplicate_final_accept_r;
  reg [4:0] completion_count_r;
  integer source_i;
  integer destination_i;
  integer final_destination_i;
  integer reset_i;

  wire descriptor_destination_free = !destination_locked[descriptor_destination];
  wire descriptor_fire = descriptor_valid && descriptor_ready;

  assign guarded_valid = descriptor_valid && descriptor_destination_free &&
    !protocol_error;
  assign descriptor_ready = guarded_ready && descriptor_destination_free &&
    !protocol_error;

  genvar destination_g;
  generate
    for (destination_g = 0; destination_g < 16;
         destination_g = destination_g + 1) begin : gen_lock_telemetry
      assign locked_descriptor_source[(destination_g*4) +: 4] =
        locked_source_q[destination_g];
    end
  endgenerate

  always @(*) begin
    final_accept_valid_r = 16'd0;
    duplicate_final_accept_r = 1'b0;
    final_destination_i = 0;
    for (destination_i = 0; destination_i < 16; destination_i = destination_i + 1) begin
      final_accept_source_r[destination_i] = 4'd0;
      final_accept_tag_r[destination_i] = 8'd0;
    end
    for (source_i = 0; source_i < 16; source_i = source_i + 1) begin
      if (packet_command_accept[source_i] &&
          packet_command_descriptor_last[source_i]) begin
        final_destination_i = packet_command_destination[(source_i*4) +: 4];
        if (final_accept_valid_r[final_destination_i]) begin
          duplicate_final_accept_r = 1'b1;
        end else begin
          final_accept_valid_r[final_destination_i] = 1'b1;
          final_accept_source_r[final_destination_i] =
            packet_command_source[(source_i*4) +: 4];
          final_accept_tag_r[final_destination_i] =
            packet_command_tag[(source_i*8) +: 8];
        end
      end
    end
  end

  always @(*) begin
    completion_count_r = 5'd0;
    for (destination_i = 0; destination_i < 16; destination_i = destination_i + 1) begin
      if (packet_completion_valid[destination_i] &&
          descriptor_final_pending[destination_i] &&
          packet_completion_source[(destination_i*4) +: 4] ==
            locked_source_q[destination_i] &&
          packet_completion_tag[(destination_i*8) +: 8] ==
            final_tag_q[destination_i])
        completion_count_r = completion_count_r + 1'b1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      destination_locked <= 16'd0;
      descriptor_final_pending <= 16'd0;
      accepted_descriptor_count <= 16'd0;
      completed_descriptor_count <= 16'd0;
      protocol_error <= 1'b0;
      for (reset_i = 0; reset_i < 16; reset_i = reset_i + 1) begin
        locked_source_q[reset_i] <= 4'd0;
        final_tag_q[reset_i] <= 8'd0;
      end
    end else begin
      if (descriptor_fire) begin
        destination_locked[descriptor_destination] <= 1'b1;
        descriptor_final_pending[descriptor_destination] <= 1'b0;
        locked_source_q[descriptor_destination] <= descriptor_source;
        accepted_descriptor_count <= accepted_descriptor_count + 1'b1;
      end

      if (duplicate_final_accept_r)
        protocol_error <= 1'b1;

      for (destination_i = 0; destination_i < 16; destination_i = destination_i + 1) begin
        if (final_accept_valid_r[destination_i]) begin
          if (!destination_locked[destination_i] ||
              descriptor_final_pending[destination_i] ||
              final_accept_source_r[destination_i] != locked_source_q[destination_i]) begin
            protocol_error <= 1'b1;
          end else begin
            descriptor_final_pending[destination_i] <= 1'b1;
            final_tag_q[destination_i] <= final_accept_tag_r[destination_i];
          end
        end

        if (packet_completion_valid[destination_i] &&
            descriptor_final_pending[destination_i] &&
            packet_completion_source[(destination_i*4) +: 4] ==
              locked_source_q[destination_i] &&
            packet_completion_tag[(destination_i*8) +: 8] ==
              final_tag_q[destination_i]) begin
          destination_locked[destination_i] <= 1'b0;
          descriptor_final_pending[destination_i] <= 1'b0;
        end
      end
      completed_descriptor_count <= completed_descriptor_count + completion_count_r;
    end
  end
endmodule
