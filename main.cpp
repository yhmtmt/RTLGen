#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <limits>
#include <stdexcept>
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
                      << (operand.is_signed ? "signed" : "unsigned") << ", width "
                      << operand.bit_width << ", dimensions " << operand.dimensions << "\n";
        }
    } else {
        std::cout << "  Legacy operand: " << (config.operand.is_signed ? "signed" : "unsigned")
                  << ", width " << config.operand.bit_width << "\n";
    }
    std::cout << "  Operations: " << config.multipliers.size() << " multiplier(s), "
              << config.adders.size() << " adder(s), " << config.yosys_multipliers.size()
              << " yosys multiplier(s), " << config.mcm_operations.size() << " MCM block(s), "
              << config.cmvm_operations.size() << " CMVM block(s)\n";

    try {
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
            cpa.init(operandDef.bit_width, type);
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
    } catch (const std::exception &ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        std::cerr << "Failed to load configuration.\n";
        return 1;
    }

    return 0;
}
