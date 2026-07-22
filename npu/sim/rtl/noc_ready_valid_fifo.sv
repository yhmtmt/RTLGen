`timescale 1ns/1ps

module noc_ready_valid_fifo #(
  parameter integer WIDTH = 128,
  parameter integer DEPTH = 4,
  parameter integer COUNT_W = (DEPTH <= 1) ? 1 : $clog2(DEPTH + 1)
) (
  input wire clk,
  input wire rst_n,

  input wire in_valid,
  output wire in_ready,
  input wire [WIDTH-1:0] in_data,

  output wire out_valid,
  input wire out_ready,
  output wire [WIDTH-1:0] out_data,

  output wire [COUNT_W-1:0] occupancy,
  output reg [COUNT_W-1:0] max_occupancy
);
  localparam [COUNT_W-1:0] DEPTH_VALUE = DEPTH;

  reg [WIDTH-1:0] mem [0:DEPTH-1];
  reg [COUNT_W-1:0] count;
  integer slot_i;

  wire out_valid_int = (count != {COUNT_W{1'b0}});
  wire out_fire = out_valid_int && out_ready;
  wire in_ready_int = (count < DEPTH_VALUE) || out_fire;
  wire in_fire = in_valid && in_ready_int;

  assign in_ready = in_ready_int;
  assign out_valid = out_valid_int;
  assign out_data = mem[0];
  assign occupancy = count;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= {COUNT_W{1'b0}};
      max_occupancy <= {COUNT_W{1'b0}};
    end else begin
      case ({in_fire, out_fire})
        2'b10: begin
          mem[count] <= in_data;
          count <= count + {{(COUNT_W-1){1'b0}}, 1'b1};
          if ((count + {{(COUNT_W-1){1'b0}}, 1'b1}) > max_occupancy) begin
            max_occupancy <= count + {{(COUNT_W-1){1'b0}}, 1'b1};
          end
        end
        2'b01: begin
          for (slot_i = 0; slot_i < (DEPTH - 1); slot_i = slot_i + 1) begin
            if ((slot_i + 1) < count) begin
              mem[slot_i] <= mem[slot_i + 1];
            end
          end
          count <= count - {{(COUNT_W-1){1'b0}}, 1'b1};
        end
        2'b11: begin
          for (slot_i = 0; slot_i < (DEPTH - 1); slot_i = slot_i + 1) begin
            if ((slot_i + 1) < count) begin
              mem[slot_i] <= mem[slot_i + 1];
            end
          end
          if (count == {{(COUNT_W-1){1'b0}}, 1'b1}) begin
            mem[0] <= in_data;
          end else begin
            mem[count - {{(COUNT_W-1){1'b0}}, 1'b1}] <= in_data;
          end
        end
        default: begin
        end
      endcase
    end
  end
endmodule
