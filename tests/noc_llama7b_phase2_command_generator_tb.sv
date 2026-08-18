`timescale 1ns/1ps

module noc_llama7b_phase2_command_generator_tb;
  localparam integer COMMAND_W = 102;
  localparam integer COMMAND_COUNT = 11576;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg enable = 1'b0;
  reg cmd_ready = 1'b0;
  wire cmd_valid;
  wire [COMMAND_W-1:0] cmd_data;
  wire done;
  wire [31:0] generated_command_count;
  wire protocol_error;

  reg [COMMAND_W-1:0] expected [0:COMMAND_COUNT-1];
  reg [COMMAND_W-1:0] held_command = {COMMAND_W{1'b0}};
  reg held_valid = 1'b0;
  integer observed = 0;
  integer cycle = 0;
  string expected_mem;

  noc_llama7b_phase2_command_generator dut (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .cmd_valid(cmd_valid), .cmd_ready(cmd_ready), .cmd_data(cmd_data),
    .done(done), .generated_command_count(generated_command_count),
    .protocol_error(protocol_error)
  );

  always #1 clk = ~clk;

  always @(posedge clk) begin
    if (rst_n) begin
      cycle = cycle + 1;
      cmd_ready <= (cycle % 7 != 2) && (cycle % 11 != 5);
      if (cmd_valid && !cmd_ready) begin
        if (held_valid && cmd_data !== held_command)
          $fatal(1, "command changed under backpressure at index %0d", observed);
        held_command <= cmd_data;
        held_valid <= 1'b1;
      end else begin
        held_valid <= 1'b0;
      end
      if (cmd_valid && cmd_ready) begin
        if (observed >= COMMAND_COUNT)
          $fatal(1, "generator emitted too many commands");
        if (cmd_data !== expected[observed])
          $fatal(1,
            "command mismatch index=%0d expected=%026h observed=%026h",
            observed, expected[observed], cmd_data);
        observed = observed + 1;
      end
    end
  end

  initial begin
    if (!$value$plusargs("EXPECTED_COMMAND_MEM=%s", expected_mem))
      $fatal(1, "EXPECTED_COMMAND_MEM is required");
    $readmemh(expected_mem, expected);
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    enable = 1'b1;
    wait (done);
    repeat (2) @(negedge clk);
    if (observed != COMMAND_COUNT ||
        generated_command_count != COMMAND_COUNT || protocol_error)
      $fatal(1,
        "generator completion mismatch observed=%0d generated=%0d error=%0d",
        observed, generated_command_count, protocol_error);
    if (cmd_valid)
      $fatal(1, "cmd_valid remained asserted after completion");
    $display("PASS commands=%0d cycles=%0d", observed, cycle);
    $finish;
  end
endmodule
