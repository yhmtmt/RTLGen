#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <limits>
#include <stdexcept>
#include <cstdlib>
#include <filesystem>
#include <sstream>
#include "multiplier.hpp"
#include "adder.hpp"
#include "rtl_operations.hpp"

#include <nlohmann/json.hpp>

#include <onnxruntime_cxx_api.h>

namespace {

OperandDefinition makeLegacyOperand(const CircuitConfig &config) {
    OperandDefinition def;
    def.name = "operand";
    def.dimensions = 1;
    def.bit_width = config.operand.bit_width;
    def.is_signed = config.operand.is_signed;
    return def;
}

bool findOperand(const CircuitConfig &config, const std::string &name, OperandDefinition &out) {
    for (const auto &operand : config.operands) {
        if (operand.name == name) {
            out = operand;
            return true;
        }
    }
    return false;
}

OperandDefinition resolveOperand(const CircuitConfig &config, const std::string &name) {
    if (!name.empty()) {
        OperandDefinition def;
        if (!findOperand(config, name, def)) {
            throw std::runtime_error("Unknown operand reference: " + name);
        }
        return def;
    }
    if (!config.operands.empty()) {
        return config.operands.front();
    }
    if (config.operand.bit_width <= 0) {
        throw std::runtime_error(
            "No operand definition available. Provide an entry in \"operands\" or legacy "
            "\"operand\".");
    }
    return makeLegacyOperand(config);
}

Operand makeOperandValue(const OperandDefinition &def) {
    Operand operand;
    operand.width = def.bit_width;
    operand.is_signed = def.is_signed;
    operand.bits.assign(operand.width, false);
    return operand;
}

std::filesystem::path locateFlopoco(const std::filesystem::path &exePath) {
    if (const char *env = std::getenv("FLOPOCO_BIN")) {
        std::filesystem::path candidate(env);
        if (std::filesystem::exists(candidate)) {
            return candidate;
        }
    }
    std::filesystem::path exeDir = exePath.parent_path();
    std::filesystem::path repoBin = exeDir.parent_path() / "bin" / "flopoco";
    if (std::filesystem::exists(repoBin)) {
        return repoBin;
    }
    std::filesystem::path cwdBin = std::filesystem::current_path() / "bin" / "flopoco";
    if (std::filesystem::exists(cwdBin)) {
        return cwdBin;
    }
    throw std::runtime_error("Unable to locate FloPoCo binary. Set FLOPOCO_BIN or ensure bin/flopoco exists.");
}

void runCommandOrThrow(const std::string &cmd, const std::string &what) {
    int rc = std::system(cmd.c_str());
    if (rc != 0) {
        std::ostringstream oss;
        oss << what << " failed (rc=" << rc << ")";
        throw std::runtime_error(oss.str());
    }
}

void generateFpOperator(const FpOperationConfig &fp,
                        const OperandDefinition &operand,
                        const std::filesystem::path &flopocoPath) {
    if (!operand.fp_format.has_value()) {
        throw std::runtime_error("Operand " + operand.name + " missing fp_format for fp operation " +
                                 fp.module_name);
    }
    const auto fmt = operand.fp_format.value();
    int wE = fmt.exponent_width();
    int wF = fmt.mantissa_width;
    if (wE <= 0 || wF <= 0) {
        throw std::runtime_error("Invalid fp_format dimensions for " + operand.name);
    }

    std::ostringstream cmd;
    std::filesystem::path vhdlPath = std::filesystem::absolute(fp.module_name + ".vhdl");
    std::string flopocoOp;
    if (fp.type == "fp_mul") flopocoOp = "FPMult";
    else if (fp.type == "fp_add") flopocoOp = "FPAdd";
    else if (fp.type == "fp_mac") flopocoOp = "IEEEFPFMA";
    else throw std::runtime_error("Unsupported FP operation type: " + fp.type);

    cmd << "\"" << flopocoPath.string() << "\" "
        << "name=" << fp.module_name << " "
        << "outputFile=" << vhdlPath.string() << " "
        << flopocoOp << " "
        << "wE=" << wE << " "
        << "wF=" << wF;
    std::cout << "[INFO] Running FloPoCo: " << cmd.str() << "\n";
    runCommandOrThrow(cmd.str(), "FloPoCo generation");

    if (!std::filesystem::exists(vhdlPath)) {
        throw std::runtime_error("FloPoCo did not produce expected VHDL: " + vhdlPath.string());
    }

    std::ostringstream yosysCmd;
    yosysCmd << "yosys -q -m ghdl -p \"ghdl --std=08 --ieee=synopsys -fsynopsys "
             << vhdlPath.string() << " -e " << fp.module_name
             << "; write_verilog -noattr " << fp.module_name << ".v\"";
    std::cout << "[INFO] Converting VHDL to Verilog via Yosys/GHDL\n";
    runCommandOrThrow(yosysCmd.str(), "Yosys conversion");

    std::ostringstream iverilogCmd;
    iverilogCmd << "iverilog -g2012 -s " << fp.module_name << " -t null "
                << fp.module_name << ".v";
    std::cout << "[INFO] Validating Verilog with iverilog\n";
    runCommandOrThrow(iverilogCmd.str(), "iverilog compile");
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <config.json>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    CircuitConfig config;

    if (!readConfig(filename, config)) {
        std::cerr << "Failed to load configuration.\n";
        return 1;
    }

    std::cout << "Configuration Loaded Successfully:\n";
    if (!config.operands.empty()) {
        for (const auto &operand : config.operands) {
            std::cout << "  Operand " << operand.name << ": "
                      << (operand.kind == "fp" ? "fp" : (operand.is_signed ? "signed" : "unsigned"))
                      << ", width " << operand.bit_width << ", dimensions " << operand.dimensions
                      << "\n";
        }
    } else {
        std::cout << "  Legacy operand: " << (config.operand.is_signed ? "signed" : "unsigned")
                  << ", width " << config.operand.bit_width << "\n";
    }
    std::cout << "  Operations: " << config.multipliers.size() << " multiplier(s), "
              << config.adders.size() << " adder(s), " << config.yosys_multipliers.size()
              << " yosys multiplier(s), " << config.mcm_operations.size() << " MCM block(s), "
              << config.cmvm_operations.size() << " CMVM block(s), "
              << config.fp_operations.size() << " FP op(s)\n";

    try {
        std::filesystem::path flopocoPath;
        bool needFlopoco = !config.fp_operations.empty();
        if (needFlopoco) {
            flopocoPath = locateFlopoco(std::filesystem::absolute(argv[0]));
            std::cout << "[INFO] Found FloPoCo at " << flopocoPath << "\n";
        }

        for (const auto &mult : config.multipliers) {
            OperandDefinition operandDef = resolveOperand(config, mult.operand);
            Operand lhs = makeOperandValue(operandDef);
            Operand rhs = lhs;
            CTType ctype = get_compressor_type(mult.compressor_structure);
            CPAType cptype = get_cpa_type(mult.cpa_structure);
            PPType ptype = get_ppg_algorithm(mult.ppg_algorithm);
            MultiplierGenerator generator;
            std::cout << "[INFO] Generating multiplier " << mult.module_name << "\n";
            generator.build(lhs, rhs, ctype, ptype, cptype, mult.module_name);
        }

        for (auto yosys : config.yosys_multipliers) {
            OperandDefinition operandDef = resolveOperand(config, yosys.operand);
            yosys.is_signed = operandDef.is_signed;
            yosys.bit_width = operandDef.bit_width;
            MultiplierGenerator generator;
            std::cout << "[INFO] Generating Yosys multiplier " << yosys.module_name << "\n";
            generator.build_yosys(yosys, yosys.module_name);
        }

        for (const auto &adder : config.adders) {
            OperandDefinition operandDef = resolveOperand(config, adder.operand);
            CarryPropagatingAdder cpa;
            CPAType type = get_cpa_type(adder.cpa_structure);
            std::cout << "[INFO] Generating adder " << adder.module_name << "\n";
            std::vector<float> input_delays;
            if (!adder.input_delays.empty()) {
                if (adder.input_delays.size() == 1) {
                    input_delays.assign(operandDef.bit_width, adder.input_delays.front());
                } else if (adder.input_delays.size() == static_cast<std::size_t>(operandDef.bit_width)) {
                    input_delays = adder.input_delays;
                } else {
                    throw std::runtime_error("input_delays length must be 1 or match bit width for adder " + adder.module_name);
                }
            }
            cpa.init(operandDef.bit_width, type, input_delays);
            cpa.dump_hdl(adder.module_name);
        }

        for (const auto &mcm : config.mcm_operations) {
            OperandDefinition operandDef = resolveOperand(config, mcm.operand);
            std::cout << "[INFO] Generating MCM block " << mcm.module_name << "\n";
            emitMcmModule(mcm, operandDef);
        }

        for (const auto &cmvm : config.cmvm_operations) {
            OperandDefinition operandDef = resolveOperand(config, cmvm.operand);
            std::cout << "[INFO] Generating CMVM block " << cmvm.module_name << "\n";
            emitCmvmModule(cmvm, operandDef);
        }

        for (const auto &fp : config.fp_operations) {
            OperandDefinition operandDef = resolveOperand(config, fp.operand);
            if (operandDef.kind != "fp") {
                throw std::runtime_error("FP operation " + fp.module_name +
                                         " expects an operand of kind \"fp\"");
            }
            if (fp.type == "fp_mul") {
                std::cout << "[INFO] Generating FP multiplier " << fp.module_name << "\n";
            } else if (fp.type == "fp_add") {
                std::cout << "[INFO] Generating FP adder " << fp.module_name << "\n";
            } else if (fp.type == "fp_mac") {
                std::cout << "[INFO] Generating FP fused multiply-add " << fp.module_name << "\n";
            }
            generateFpOperator(fp, operandDef, flopocoPath);
        }
    } catch (const std::exception &ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        std::cerr << "Failed to load configuration.\n";
        return 1;
    }

    return 0;
}
