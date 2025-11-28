#include <gtest/gtest.h>
#include "adder.hpp"
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <string>
#include <cstdio>
#include <vector>

void generate_adder_testbench(const std::string& module_name, int width) {
    std::ofstream tb_file(module_name + "_tb.v");
    tb_file << "`timescale 1ns / 1ps" << std::endl;
    tb_file << "module " << module_name << "_tb;" << std::endl;
    tb_file << "    reg [" << width - 1 << ":0] a, b;" << std::endl;
    tb_file << "    wire [" << width - 1 << ":0] sum;" << std::endl;
    tb_file << "    wire cout;" << std::endl;
    tb_file << "    integer i, j;" << std::endl;
    tb_file << "    " << module_name << " uut ( .a(a), .b(b), .sum(sum), .cout(cout) );" << std::endl;
    tb_file << "    initial begin" << std::endl;
    tb_file << "        for (i = 0; i < (1 << " << width << ") ; i = i + 1) begin" << std::endl;
    tb_file << "            for (j = 0; j < (1 << " << width << ") ; j = j + 1) begin" << std::endl;
    tb_file << "                a = i;" << std::endl;
    tb_file << "                b = j;" << std::endl;
    tb_file << "                #10;" << std::endl;
    tb_file << "                if ({cout, sum} !== a + b) begin" << std::endl;
    tb_file << "                    $display(\"Error: a=%h, b=%h, sum=%h, cout=%b, expected=%h\", a, b, sum, cout, a+b);" << std::endl;
    tb_file << "                    $finish;" << std::endl;
    tb_file << "                end" << std::endl;
    tb_file << "            end" << std::endl;
    tb_file << "        end" << std::endl;
    tb_file << "        $display(\"Test passed\");" << std::endl;
    tb_file << "        $finish;" << std::endl;
    tb_file << "    end" << std::endl;
    tb_file << "endmodule" << std::endl;
    tb_file.close();
}

void run_iverilog_test(const std::string& module_name) {
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
    ASSERT_NE(result.find("Test passed"), std::string::npos);
    ASSERT_EQ(WEXITSTATUS(pclose_ret), 0);
}

TEST(AdderText, RippleCarryAdder) {
    const int width = 11;
    const std::string module_name = "ripplecarry_adder";
    CarryPropagatingAdder adder;
    adder.init(width, CPA_Ripple);
    adder.dump_hdl(module_name);
    generate_adder_testbench(module_name, width);
    run_iverilog_test(module_name);
}

TEST(AdderTest, KoggeStoneAdder) {
    const int width = 11;
    const std::string module_name = "koggestone_adder";
    CarryPropagatingAdder adder;
    adder.init(width, CPA_KoggeStone);
    adder.dump_hdl(module_name);
    generate_adder_testbench(module_name, width);
    run_iverilog_test(module_name);
}

TEST(AdderTest, BrentKungAdder) {
    const int width = 11;
    const std::string module_name = "brentkung_adder";
    CarryPropagatingAdder adder;
    adder.init(width, CPA_BrentKung);
    adder.dump_hdl(module_name);
    generate_adder_testbench(module_name, width);
    run_iverilog_test(module_name);
}

TEST(AdderTest, SklanskyAdder) {
    const int width = 11;
    const std::string module_name = "sklansky_adder";
    CarryPropagatingAdder adder;
    adder.init(width, CPA_Sklansky);
    adder.dump_hdl(module_name);
    generate_adder_testbench(module_name, width);
    run_iverilog_test(module_name);
}

TEST(AdderTest, SkewAwarePrefixAdder) {
    const int width = 8;
    const std::string module_name = "skewaware_adder";
    CarryPropagatingAdder adder;
    std::vector<float> delays = {0.0f, 0.1f, 0.2f, 0.3f, 0.0f, 0.0f, 0.0f, 0.0f};
    adder.init(width, CPA_SkewAwarePrefix, delays);
    adder.dump_hdl(module_name);
    generate_adder_testbench(module_name, width);
    run_iverilog_test(module_name);
}
