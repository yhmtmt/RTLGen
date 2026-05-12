`timescale 1ns/1ps

module attention_kv_tile_tb;
  reg clk;
  reg rst_n;
  reg tile_valid;
  wire tile_ready;
  reg tile_last;
  reg [15:0] query_fragment;
  reg [15:0] key_fragment;
  wire score_valid;
  reg score_ready;
  wire signed [23:0] score;
  wire [15:0] accepted_tile_count;
  wire [15:0] accepted_byte_count;
  wire [15:0] producer_stall_cycles;
  wire [15:0] cycle_count;
  wire [15:0] final_completion_cycle;

  attention_kv_tile_hd8_kv4_l4_b16 dut (
    .clk(clk),
    .rst_n(rst_n),
    .tile_valid(tile_valid),
    .tile_ready(tile_ready),
    .tile_last(tile_last),
    .query_fragment(query_fragment),
    .key_fragment(key_fragment),
    .score_valid(score_valid),
    .score_ready(score_ready),
    .score(score),
    .accepted_tile_count(accepted_tile_count),
    .accepted_byte_count(accepted_byte_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

  always #5 clk = ~clk;

  task send_tile;
    input last;
    input [15:0] query_bits;
    input [15:0] key_bits;
    begin
      @(negedge clk);
      while (tile_ready !== 1'b1) begin
        @(negedge clk);
      end
      tile_valid = 1'b1;
      tile_last = last;
      query_fragment = query_bits;
      key_fragment = key_bits;
      @(negedge clk);
      tile_valid = 1'b0;
      tile_last = 1'b0;
      query_fragment = 16'h0000;
      key_fragment = 16'h0000;
    end
  endtask

  initial begin
    #1000;
    $display("FAIL attention_kv_tile: simulation timeout");
    $fatal;
  end

  initial begin
    clk = 1'b0;
    rst_n = 1'b1;
    tile_valid = 1'b0;
    tile_last = 1'b0;
    query_fragment = 16'h0000;
    key_fragment = 16'h0000;
    score_ready = 1'b0;

    #1 rst_n = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    // Tile 0 lanes: q=[1,2,-1,3], k=[2,-1,4,1] => -1.
    send_tile(1'b0, 16'h3f21, 16'h14f2);
    // Tile 1 lanes: q=[-2,1,0,4], k=[3,2,-1,-2] => -12.
    send_tile(1'b1, 16'h401e, 16'hef23);

    repeat (2) @(negedge clk);
    if (!score_valid) begin
      $display("FAIL attention_kv_tile: score_valid was not asserted");
      $fatal;
    end
    if (score !== -24'sd13) begin
      $display("FAIL attention_kv_tile: score=%0d expected=-13", score);
      $fatal;
    end
    if (accepted_tile_count !== 16'd2 || accepted_byte_count !== 16'd32 ||
        producer_stall_cycles !== 16'd0 || cycle_count === 16'd0 ||
        final_completion_cycle === 16'd0) begin
      $display(
        "FAIL attention_kv_tile observables: tiles=%0d bytes=%0d stalls=%0d cycles=%0d final=%0d",
        accepted_tile_count,
        accepted_byte_count,
        producer_stall_cycles,
        cycle_count,
        final_completion_cycle
      );
      $fatal;
    end

    score_ready = 1'b1;
    @(negedge clk);
    score_ready = 1'b0;

    $display("All attention/KV tile tests passed.");
    $finish;
  end
endmodule
