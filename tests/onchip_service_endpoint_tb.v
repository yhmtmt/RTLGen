`timescale 1ns/1ps

module onchip_service_endpoint_tb;
  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [1:0] in_bank;
  reg in_last;
  reg [15:0] in_data;
  wire out_valid;
  reg out_ready;
  wire [1:0] out_bank;
  wire out_last;
  wire [15:0] out_data;
  wire [15:0] accepted_beat_count;
  wire [15:0] emitted_beat_count;
  wire [15:0] producer_stall_cycles;
  wire [15:0] consumer_stall_cycles;
  wire [15:0] endpoint_max_occupancy;
  wire [15:0] bank_max_occupancy;
  wire [15:0] cycle_count;
  wire [15:0] final_completion_cycle;

  integer out_index;

  onchip_service_endpoint #(
    .DATA_W(16),
    .BANKS(4),
    .BANK_SEL_W(2),
    .BANK_QUEUE_DEPTH(2),
    .ENDPOINT_QUEUE_DEPTH(4),
    .COUNTER_W(16)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_bank(in_bank),
    .in_last(in_last),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_bank(out_bank),
    .out_last(out_last),
    .out_data(out_data),
    .accepted_beat_count(accepted_beat_count),
    .emitted_beat_count(emitted_beat_count),
    .producer_stall_cycles(producer_stall_cycles),
    .consumer_stall_cycles(consumer_stall_cycles),
    .endpoint_max_occupancy(endpoint_max_occupancy),
    .bank_max_occupancy(bank_max_occupancy),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

  always #5 clk = ~clk;

  task send_beat;
    input [1:0] bank;
    input [15:0] data;
    input last;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_bank = bank;
      in_data = data;
      in_last = last;
      @(posedge clk);
      while (!in_ready) begin
        @(posedge clk);
      end
      @(negedge clk);
      in_valid = 1'b0;
      in_bank = 2'd0;
      in_data = 16'd0;
      in_last = 1'b0;
    end
  endtask

  initial begin
    #2000;
    $display("FAIL onchip_service_endpoint: simulation timeout");
    $fatal;
  end

  always @(posedge clk) begin
    if (rst_n && out_valid && out_ready) begin
      $display(
        "OUT index=%0d bank=%0d data=%0d last=%0d cycle=%0d",
        out_index,
        out_bank,
        out_data,
        out_last,
        cycle_count
      );
      out_index = out_index + 1;
    end
  end

`ifdef DEBUG_ONCHIP_SERVICE_ENDPOINT
  always @(posedge clk) begin
    if (rst_n) begin
      $display(
        "DBG cycle=%0d in_v=%0d in_r=%0d in_bank=%0d out_v=%0d out_r=%0d out_bank=%0d accepted=%0d emitted=%0d endpoint_max=%0d",
        cycle_count,
        in_valid,
        in_ready,
        in_bank,
        out_valid,
        out_ready,
        out_bank,
        accepted_beat_count,
        emitted_beat_count,
        endpoint_max_occupancy
      );
    end
  end
`endif

  initial begin
    clk = 1'b0;
    rst_n = 1'b1;
    in_valid = 1'b0;
    in_bank = 2'd0;
    in_last = 1'b0;
    in_data = 16'd0;
    out_ready = 1'b0;
    out_index = 0;

    #1 rst_n = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    send_beat(2'd0, 16'd10, 1'b0);
    send_beat(2'd1, 16'd20, 1'b0);
    send_beat(2'd0, 16'd11, 1'b0);
    send_beat(2'd1, 16'd21, 1'b0);

    @(negedge clk);
    in_valid = 1'b1;
    in_bank = 2'd2;
    in_data = 16'd30;
    in_last = 1'b1;
    @(posedge clk);
    if (in_ready !== 1'b0) begin
      $display("FAIL onchip_service_endpoint: expected endpoint-full producer stall");
      $fatal;
    end
    @(negedge clk);
    out_ready = 1'b1;
    while (!in_ready) begin
      @(negedge clk);
    end
    @(posedge clk);
    @(negedge clk);
    in_valid = 1'b0;
    in_bank = 2'd0;
    in_data = 16'd0;
    in_last = 1'b0;

    while (emitted_beat_count !== 16'd5) begin
      @(negedge clk);
    end

    out_ready = 1'b0;
    repeat (2) @(negedge clk);

    $display(
      "SUMMARY accepted=%0d emitted=%0d producer_stalls=%0d consumer_stalls=%0d endpoint_max=%0d bank_max=%0d final_cycle=%0d",
      accepted_beat_count,
      emitted_beat_count,
      producer_stall_cycles,
      consumer_stall_cycles,
      endpoint_max_occupancy,
      bank_max_occupancy,
      final_completion_cycle
    );

    if (accepted_beat_count !== 16'd5 || emitted_beat_count !== 16'd5) begin
      $display("FAIL onchip_service_endpoint: wrong beat counts");
      $fatal;
    end
    if (producer_stall_cycles === 16'd0 || consumer_stall_cycles === 16'd0) begin
      $display("FAIL onchip_service_endpoint: expected backpressure counters to move");
      $fatal;
    end
    if (endpoint_max_occupancy < 16'd4 || bank_max_occupancy < 16'd2) begin
      $display("FAIL onchip_service_endpoint: expected finite queues to fill");
      $fatal;
    end
    if (final_completion_cycle === 16'd0) begin
      $display("FAIL onchip_service_endpoint: final completion cycle was not recorded");
      $fatal;
    end

    $display("PASS onchip_service_endpoint");
    $finish;
  end
endmodule
