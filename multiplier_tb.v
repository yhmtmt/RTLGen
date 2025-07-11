// Testbench for a parameterized signed/unsigned multiplier
`timescale 1ns / 1ps

module multiplier_tb;

    // Testbench parameters
    localparam CLK_PERIOD = 10; // ns
    localparam TEST_WIDTH = 8;  // Bit-width for this test run
    localparam MAX_WIDTH  = 64; // Max bit-width supported by the DUT

    // Testbench signals
    reg clk;
    reg rst_n;
    reg [MAX_WIDTH-1:0] a_vec;
    reg [MAX_WIDTH-1:0] b_vec;

    // DUT outputs
    wire [2*TEST_WIDTH-1:0] p_unsigned;
    wire [2*TEST_WIDTH-1:0] p_signed;

    // Golden reference for checking
    reg signed [2*MAX_WIDTH-1:0] expected_p;
    integer i;
    integer error_count;

    // Instantiate the Unsigned Multiplier
    multiplier #(
        .DATA_WIDTH(TEST_WIDTH),
        .SIGNED_MULT(0)
    ) dut_unsigned (
        .clk(clk),
        .rst_n(rst_n),
        .a(a_vec[TEST_WIDTH-1:0]),
        .b(b_vec[TEST_WIDTH-1:0]),
        .p(p_unsigned)
    );

    // Instantiate the Signed Multiplier
    multiplier #(
        .DATA_WIDTH(TEST_WIDTH),
        .SIGNED_MULT(1)
    ) dut_signed (
        .clk(clk),
        .rst_n(rst_n),
        .a(a_vec[TEST_WIDTH-1:0]),
        .b(b_vec[TEST_WIDTH-1:0]),
        .p(p_signed)
    );

    // Clock generator
    always #((CLK_PERIOD)/2) clk = ~clk;

    // Main test sequence
    initial begin
        // 1. Initialization and Reset
        $display("--- [INFO] Starting Multiplier Testbench ---");
        $display("--- [INFO] Testing with DATA_WIDTH = %0d ---", TEST_WIDTH);
        clk = 1'b0;
        rst_n = 1'b0;
        a_vec = 0;
        b_vec = 0;
        error_count = 0;

        repeat(2) @(posedge clk);
        rst_n = 1'b1;
        $display("--- [INFO] Reset released ---");
        @(posedge clk);

        // 2. Unsigned Multiplication Tests
        $display("\n--- Testing Unsigned Multiplication ---");
        // Test case: 0 * B
        a_vec = 0; b_vec = 5;
        check_unsigned;

        // Test case: A * 0
        a_vec = 12; b_vec = 0;
        check_unsigned;

        // Test case: 1 * B
        a_vec = 1; b_vec = 25;
        check_unsigned;

        // Test case: General case
        a_vec = 10; b_vec = 15;
        check_unsigned;

        // Test case: Max value * Max value
        a_vec = ~0; b_vec = ~0;
        check_unsigned;

        // 3. Signed Multiplication Tests
        $display("\n--- Testing Signed Multiplication ---");
        // Test case: Positive * Positive
        a_vec = 10; b_vec = 7;
        check_signed;

        // Test case: Positive * Negative
        a_vec = 10; b_vec = -7;
        check_signed;

        // Test case: Negative * Positive
        a_vec = -10; b_vec = 7;
        check_signed;

        // Test case: Negative * Negative
        a_vec = -10; b_vec = -7;
        check_signed;
        
        // Test case: Min negative value
        a_vec = (1 << (TEST_WIDTH-1)); // Min signed value
        b_vec = 2;
        check_signed;

        // 4. Randomized Tests
        $display("\n--- Running 20 Randomized Tests ---");
        for (i = 0; i < 20; i = i + 1) begin
            a_vec = {$random()} % (2**TEST_WIDTH);
            b_vec = {$random()} % (2**TEST_WIDTH);
            check_unsigned;
            check_signed;
        end

        // 5. Final Report
        $display("\n--- [INFO] Testbench Finished ---");
        if (error_count == 0) begin
            $display("--- [PASS] All tests passed! ---");
        end else begin
            $display("--- [FAIL] %0d errors found! ---", error_count);
        end
        $finish;
    end

    // Task to check unsigned results
    task check_unsigned;
    begin
        @(posedge clk);
        #1; // Allow combinational logic to settle
        expected_p = a_vec[TEST_WIDTH-1:0] * b_vec[TEST_WIDTH-1:0];
        if (p_unsigned === expected_p) begin
            $display("[PASS] Unsigned: %0d * %0d = %0d", a_vec[TEST_WIDTH-1:0], b_vec[TEST_WIDTH-1:0], p_unsigned);
        end else begin
            $display("[FAIL] Unsigned: %0d * %0d. GOT: %0d, EXP: %0d", a_vec[TEST_WIDTH-1:0], b_vec[TEST_WIDTH-1:0], p_unsigned, expected_p);
            error_count = error_count + 1;
        end
    end
    endtask

    // Task to check signed results
    task check_signed;
    begin
        @(posedge clk);
        #1; // Allow combinational logic to settle
        expected_p = $signed(a_vec[TEST_WIDTH-1:0]) * $signed(b_vec[TEST_WIDTH-1:0]);
        if ($signed(p_signed) === expected_p) begin
            $display("[PASS] Signed: %0d * %0d = %0d", $signed(a_vec[TEST_WIDTH-1:0]), $signed(b_vec[TEST_WIDTH-1:0]), $signed(p_signed));
        end else begin
            $display("[FAIL] Signed: %0d * %0d. GOT: %0d, EXP: %0d", $signed(a_vec[TEST_WIDTH-1:0]), $signed(b_vec[TEST_WIDTH-1:0]), $signed(p_signed), expected_p);
            error_count = error_count + 1;
        end
    end
    endtask

endmodule