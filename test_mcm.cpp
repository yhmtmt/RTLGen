#include "mcm.hpp"
#include <gtest/gtest.h>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <string>
#include <cstdio>

// Helper function to check if a file exists
bool file_exists(const std::string& filename) {
    std::ifstream f(filename.c_str());
    return f.good();
}

// Helper to run iverilog and check output for multiple outputs
void run_iverilog_test(const std::string& module_name, const std::vector<int> & target_consts,  int input_val) {
    // Generate testbench for multiple outputs
    std::ofstream tb_file(module_name + "_tb.v");
    tb_file << "`timescale 1ns/1ps\n";
    tb_file << "module " << module_name << "_tb;\n";
    tb_file << "    reg [31:0] x;\n";
    for (size_t i = 0; i < target_consts.size(); ++i) {
        tb_file << "    wire [31:0] y" << target_consts[i] << ";\n";
    }
    tb_file << "    " << module_name << " uut(.x(x)";
    for (size_t i = 0; i < target_consts.size(); ++i) {
        tb_file << ", .y" << target_consts[i] << "(y" << target_consts[i] << ")";
    }
    tb_file << ");\n";
    tb_file << "    initial begin\n";
    tb_file << "        x = " << input_val << ";\n";
    tb_file << "        #10;\n";
    for (size_t i = 0; i < target_consts.size(); ++i) {
        tb_file << "        if (y" << target_consts[i] << " !== " << target_consts[i] * input_val << ") begin\n";
        tb_file << "            $display(\"FAIL: x=%d, y" << target_consts[i] << "=%d, expected=%d\", x, y" << target_consts[i] << ", " << target_consts[i] * input_val << ");\n";
        tb_file << "            $finish;\n";
        tb_file << "        end\n";
    }
    tb_file << "        $display(\"PASS\");\n";
    tb_file << "        $finish;\n";
    tb_file << "    end\n";
    tb_file << "endmodule\n";
    tb_file.close();

    std::string iverilog_cmd = "iverilog -o " + module_name + ".vvp " + module_name + ".v " + module_name + "_tb.v";
    int ret = system(iverilog_cmd.c_str());
    ASSERT_EQ(ret, 0);

    std::string vvp_cmd = "vvp " + module_name + ".vvp";
    FILE* pipe = popen(vvp_cmd.c_str(), "r");
    ASSERT_TRUE(pipe != nullptr);

    char buffer[128];
    std::string result = "";
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }
    int pclose_ret = pclose(pipe);
    ASSERT_NE(result.find("PASS"), std::string::npos);
    ASSERT_EQ(WEXITSTATUS(pclose_ret), 0);
}

TEST(McmOptimizerTest, BuildOptimizationResult) {
    operations_research::McmOptimizer optimizer;
    std::vector<int> target_consts = {3}; // Test constant multiplier by 3
    int NA = 2;
    int wordlength = 32;
    int Smax = 2;
    optimizer.Build(target_consts, NA, wordlength, Smax);

    // Use accessor to check optimization result
    const auto& result = optimizer.GetOptimizationResult();
    ASSERT_FALSE(result.empty());
    // Check the ca value matches the target constant somewhere
    bool found = false;
    for (const auto& info : result) {
        if (info.ca == 3) found = true;
    }
    ASSERT_TRUE(found);
}

TEST(McmOptimizerTest, GenerateVerilogAndSimulate) {
    operations_research::McmOptimizer optimizer;
    std::vector<int> target_consts = {3}; // Test constant multiplier by 3
    int NA = 2;
    int wordlength = 32;
    int Smax = 2;
    optimizer.Build(target_consts, NA, wordlength, Smax);

    std::string module_name = "test_mcm_mult3";
    bool success = optimizer.GenerateVerilog(module_name);
    ASSERT_TRUE(success);
    ASSERT_TRUE(file_exists(module_name + ".v"));

    // Test a few input/output pairs
    run_iverilog_test(module_name, target_consts, 0);
    run_iverilog_test(module_name, target_consts, 1);
    run_iverilog_test(module_name, target_consts, 2);
    run_iverilog_test(module_name, target_consts, 10);
    run_iverilog_test(module_name, target_consts, 123);
}
 


TEST(McmOptimizerTest, BuildOptimizationResultMultipleConstants) {
    operations_research::McmOptimizer optimizer;
    std::vector<int> target_consts = {3, 5}; // Test with two constants
    int NA = 4;
    int wordlength = 32;
    int Smax = 2;
    optimizer.Build(target_consts, NA, wordlength, Smax);

    // Use accessor to check optimization result
    const auto& result = optimizer.GetOptimizationResult();
    ASSERT_FALSE(result.empty());
    // Check the ca value matches at least one of the target constants somewhere
    bool found3 = false, found5 = false;
    for (const auto& info : result) {
        if (info.ca == 3) found3 = true;
        if (info.ca == 5) found5 = true;
    }
    ASSERT_TRUE(found3 || found5);
}

TEST(McmOptimizerTest, GenerateVerilogAndSimulateMultipleConstants) {
    operations_research::McmOptimizer optimizer;
    std::vector<int> target_consts = {3, 5}; // Test with two constants
    int NA = 4;
    int wordlength = 32;
    int Smax = 2;
    optimizer.Build(target_consts, NA, wordlength, Smax);

    std::string module_name = "test_mcm_mult3_5";
    bool success = optimizer.GenerateVerilog(module_name);
    ASSERT_TRUE(success);
    ASSERT_TRUE(file_exists(module_name + ".v"));

    // Test a few input/output pairs for both outputs
    run_iverilog_test(module_name, target_consts, 0);
    run_iverilog_test(module_name, target_consts, 1);
    run_iverilog_test(module_name, target_consts, 2);
    run_iverilog_test(module_name, target_consts, 10);
    run_iverilog_test(module_name, target_consts, 123);
}