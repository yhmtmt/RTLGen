`timescale 1ns/1ps

module llama7b_rmsnorm_banked_row_gamma_store_tb;
  reg clk = 0;
  reg rst_n = 0;
  reg write_en = 0;
  reg [7:0] write_beat = 0;
  reg [255:0] write_row = 0;
  reg [255:0] write_gamma = 0;
  reg read_en = 0;
  reg [7:0] read_beat = 0;
  wire read_valid;
  wire [255:0] read_row;
  wire [255:0] read_gamma;
  wire request_collision;
  integer lane;

  llama7b_rmsnorm_banked_row_gamma_store dut (.*);
  always #5 clk = ~clk;

  task write_pattern(input [7:0] beat);
    begin
      @(negedge clk);
      write_beat = beat;
      for (lane = 0; lane < 16; lane = lane + 1) begin
        write_row[(lane*16) +: 16] = {beat, lane[7:0]};
        write_gamma[(lane*16) +: 16] = {lane[7:0], beat};
      end
      write_en = 1;
      @(negedge clk);
      write_en = 0;
    end
  endtask

  task read_and_check(input [7:0] beat);
    begin
      @(negedge clk);
      read_beat = beat;
      read_en = 1;
      @(negedge clk);
      read_en = 0;
      wait (read_valid);
      #1;
      for (lane = 0; lane < 16; lane = lane + 1) begin
        if (read_row[(lane*16) +: 16] !== {beat, lane[7:0]}) $fatal(1, "row mismatch");
        if (read_gamma[(lane*16) +: 16] !== {lane[7:0], beat}) $fatal(1, "gamma mismatch");
      end
      @(negedge clk);
    end
  endtask

  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1;
    write_pattern(8'd0);
    write_pattern(8'd63);
    write_pattern(8'd64);
    write_pattern(8'd127);
    write_pattern(8'd128);
    write_pattern(8'd191);
    write_pattern(8'd192);
    write_pattern(8'd255);
    read_and_check(8'd255);
    read_and_check(8'd0);
    read_and_check(8'd192);
    read_and_check(8'd64);
    @(negedge clk);
    write_en = 1;
    read_en = 1;
    @(negedge clk);
    write_en = 0;
    read_en = 0;
    if (!request_collision) $fatal(1, "collision was not recorded");
    $display("PASS");
    $finish;
  end
endmodule
