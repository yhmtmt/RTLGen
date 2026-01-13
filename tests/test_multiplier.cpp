#include <gtest/gtest.h>
#include "multiplier.hpp"
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

bool file_contains(const std::string& filename, const std::string& needle) {
    std::ifstream f(filename.c_str());
    if (!f.good()) return false;
    std::string line;
    while (std::getline(f, line)) {
        if (line.find(needle) != std::string::npos) {
            return true;
        }
    }
    return false;
}

bool file_contains_any(const std::string& filename, const std::vector<std::string>& needles) {
    for (const auto& needle : needles) {
        if (file_contains(filename, needle)) return true;
    }
    return false;
}

void run_iverilog_test(const std::string& module_name) {
    std::string iverilog_cmd = "iverilog -o " + module_name + ".vvp " + module_name + ".v " + module_name + "_tb.v MG_CPA.v";
    int ret = system(iverilog_cmd.c_str());
    ASSERT_EQ(ret, 0);

    std::string vvp_cmd = "vvp " + module_name + ".vvp";
    std::cout << "Running command: " << vvp_cmd << std::endl;

    FILE* pipe = popen(vvp_cmd.c_str(), "r");
    ASSERT_TRUE(pipe != nullptr);

    char buffer[128];
    std::string result = "";
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }

    int pclose_ret = pclose(pipe);
    ASSERT_NE(result.find("Test completed"), std::string::npos);
    ASSERT_EQ(WEXITSTATUS(pclose_ret), 0);
}

void run_iverilog_test_yosys(const std::string& module_name) {
    std::string iverilog_cmd = "iverilog -o " + module_name + ".vvp " + module_name + ".v " + module_name + "_tb.v";
    int ret = system(iverilog_cmd.c_str());
    ASSERT_EQ(ret, 0);

    std::string vvp_cmd = "vvp " + module_name + ".vvp";
    std::cout << "Running command: " << vvp_cmd << std::endl;

    FILE* pipe = popen(vvp_cmd.c_str(), "r");
    ASSERT_TRUE(pipe != nullptr);

    char buffer[128];
    std::string result = "";
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }

    int pclose_ret = pclose(pipe);
    ASSERT_NE(result.find("Test completed"), std::string::npos);
    ASSERT_EQ(WEXITSTATUS(pclose_ret), 0);
}

void run_config_test(PPType pp_type, bool is_signed, CPAType cpa_type, bool enable_c42 = false, bool use_direct_ilp = false) {
    Operand multiplicand, multiplier;
    multiplicand.width = multiplier.width = 8;
    multiplicand.is_signed = multiplier.is_signed = is_signed;

    MultiplierGenerator gen;
    std::string module_name = "test_mult_" +
        std::string(pp_type == Normal ? "normal" : "booth4") + "_" +
        std::string(is_signed ? "signed" : "unsigned") + "_" +
        (cpa_type == CPA_Ripple ? "ripple" :
         cpa_type == CPA_KoggeStone ? "koggestone" :
         cpa_type == CPA_BrentKung ? "brentkung" : "sklansky");

    gen.build(multiplicand, multiplier, AdderTree, pp_type, cpa_type, module_name, enable_c42, use_direct_ilp);
    gen.dump_hdl_tb(multiplicand, multiplier, module_name);

    ASSERT_TRUE(file_exists(module_name + ".v"));
    ASSERT_TRUE(file_exists(module_name + "_tb.v"));

    run_iverilog_test(module_name);
}

// All combinations: {Normal, Booth4} x {signed, unsigned} x {Ripple, KoggeStone, BrentKung, Sklansky}
TEST(MultiplierTest, CustomMultiplierBuild) {run_config_test(Booth4, true, CPA_Ripple);}
TEST(MultiplierTest, NormalSignedRipple)      { run_config_test(Normal, true, CPA_Ripple); }
TEST(MultiplierTest, NormalSignedKoggeStone)  { run_config_test(Normal, true, CPA_KoggeStone); }
TEST(MultiplierTest, NormalSignedBrentKung)   { run_config_test(Normal, true, CPA_BrentKung); }
TEST(MultiplierTest, NormalSignedSklansky)    { run_config_test(Normal, true, CPA_Sklansky); }

TEST(MultiplierTest, NormalUnsignedRipple)    { run_config_test(Normal, false, CPA_Ripple); }
TEST(MultiplierTest, NormalUnsignedKoggeStone){ run_config_test(Normal, false, CPA_KoggeStone); }
TEST(MultiplierTest, NormalUnsignedBrentKung) { run_config_test(Normal, false, CPA_BrentKung); }
TEST(MultiplierTest, NormalUnsignedSklansky)  { run_config_test(Normal, false, CPA_Sklansky); }

TEST(MultiplierTest, Booth4SignedRipple)      { run_config_test(Booth4, true, CPA_Ripple); }
TEST(MultiplierTest, Booth4SignedKoggeStone)  { run_config_test(Booth4, true, CPA_KoggeStone); }
TEST(MultiplierTest, Booth4SignedBrentKung)   { run_config_test(Booth4, true, CPA_BrentKung); }
TEST(MultiplierTest, Booth4SignedSklansky)    { run_config_test(Booth4, true, CPA_Sklansky); }

TEST(MultiplierTest, Booth4UnsignedRipple)    { run_config_test(Booth4, false, CPA_Ripple); }
TEST(MultiplierTest, Booth4UnsignedKoggeStone){ run_config_test(Booth4, false, CPA_KoggeStone); }
TEST(MultiplierTest, Booth4UnsignedBrentKung) { run_config_test(Booth4, false, CPA_BrentKung); }
TEST(MultiplierTest, Booth4UnsignedSklansky)  { run_config_test(Booth4, false, CPA_Sklansky); }

TEST(MultiplierTest, DirectIlp8bitBaseline)   { run_config_test(Normal, false, CPA_Ripple, false, true); }

TEST(MultiplierTest, CompressorModulePresence) {
    Operand multiplicand, multiplier;
    multiplicand.width = multiplier.width = 4;
    multiplicand.is_signed = multiplier.is_signed = false;

    MultiplierGenerator gen;
    std::string module_name = "test_mult_compressor_presence";
    gen.build(multiplicand, multiplier, AdderTree, Normal, CPA_KoggeStone, module_name, true, true);

    ASSERT_TRUE(file_exists(module_name + ".v"));
    EXPECT_TRUE(file_contains(module_name + ".v", "module MG_C42"));
}


void run_yosys_config_test(bool is_signed, const std::string& booth_type) {
    // Skip lowpower-booth with unsigned
    if (!is_signed && booth_type == "LowpowerBooth") return;

    MultiplierYosysConfig yosys_cfg;
    yosys_cfg.bit_width = 8;
    yosys_cfg.is_signed = is_signed;
    yosys_cfg.booth_type = booth_type;
    Operand multiplicand, multiplier;
    multiplicand.width = multiplier.width = 8;
    multiplier.is_signed = multiplicand.is_signed = is_signed;

    MultiplierGenerator gen;
    std::string module_name = "test_mult_yosys_" +
        std::string(is_signed ? "signed" : "unsigned") + "_" + booth_type;
    
    gen.build_yosys(yosys_cfg, module_name);
    gen.dump_hdl_tb(multiplicand, multiplier, module_name);

    ASSERT_TRUE(file_exists(module_name + ".v"));

    run_iverilog_test_yosys(module_name);
}

TEST(MultiplierTest, YosysSignedBooth) {
    run_yosys_config_test(true, "booth");
}

TEST(MultiplierTest, YosysUnsignedBooth) {
    run_yosys_config_test(false, "booth");
}

TEST(MultiplierTest, YosysSignedLowpowerBooth) {
    run_yosys_config_test(true, "LowpowerBooth");
}
