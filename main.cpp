#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <limits>
#include "multiplier.hpp"
#include "adder.hpp"

#include <nlohmann/json.hpp>

#include <onnxruntime_cxx_api.h>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <config.json>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    CircuitConfig config;

    if (readConfig(filename, config)) {
        std::cout << "Configuration Loaded Successfully:\n";
        std::cout << "Operand Bit Width: " << config.operand.bit_width << "\n";
        std::cout << "Operand Signed: " << (config.operand.is_signed ? "Yes" : "No") << "\n";
        if (config.multiplier) {
            std::cout << "Multiplier Module Name: " << config.multiplier->module_name << "\n";
            std::cout << "PPG Algorithm: " << config.multiplier->ppg_algorithm << "\n";
            std::cout << "Compressor Structure: " << config.multiplier->compressor_structure << "\n";
            std::cout << "CPA Structure: " << config.multiplier->cpa_structure << "\n";
            std::cout << "Pipeline Depth: " << config.multiplier->pipeline_depth << "\n";
        }

        if(config.multiplier_yosys){
            std::cout << "Yosys Multiplier Module Name: " << config.multiplier_yosys->module_name << "\n";
            std::cout << "Yosys Booth Type: " << config.multiplier_yosys->booth_type << "\n";
            std::cout << "Yosys Multiplier Signed: " << (config.multiplier_yosys->is_signed ? "Yes" : "No") << "\n";
            std::cout << "Yosys Multiplier Bit Width: " << config.multiplier_yosys->bit_width << "\n";
        }

        if (config.adder) {
            std::cout << "Adder Module Name: " << config.adder->module_name << "\n";
            std::cout << "CPA Structure: " << config.adder->cpa_structure << "\n";
            std::cout << "Pipeline Depth: " << config.adder->pipeline_depth << "\n";
        }
    } else {
        std::cerr << "Failed to load configuration.\n";
        return 1;
    }

    if (config.multiplier) {
        Operand multiplicand;
        multiplicand.width = config.operand.bit_width;
        multiplicand.is_signed = config.operand.is_signed;
        multiplicand.bits.assign(multiplicand.width, false); // Initialize bits

        Operand multiplier_operand = multiplicand; // Use the same operand for simplicity

        try{
            CTType ctype = get_compressor_type(config.multiplier->compressor_structure);
            CPAType cptype = get_cpa_type(config.multiplier->cpa_structure);
            PPType ptype = get_ppg_algorithm(config.multiplier->ppg_algorithm);
            MultiplierGenerator mg;
            mg.build(multiplicand, multiplier_operand, ctype, ptype, cptype, config.multiplier->module_name);
        }
        catch (const std::invalid_argument &e)
        {
            std::cerr << "Error: " << e.what() << std::endl;
            return 1;
        }
    }

    if (config.multiplier_yosys) {
        MultiplierGenerator mg;
        mg.build_yosys(*config.multiplier_yosys, config.multiplier_yosys->module_name);
    }

    if (config.adder) {
        Operand operand_a;
        operand_a.width = config.operand.bit_width;
        operand_a.is_signed = config.operand.is_signed;
        operand_a.bits.assign(operand_a.width, false); // Initialize bits

        Operand operand_b = operand_a; // Use the same operand for simplicity
        try{
            CPAType cptype = get_cpa_type(config.adder->cpa_structure);
            CarryPropagatingAdder cpa;
            cpa.init(config.operand.bit_width, cptype);
            cpa.dump_hdl(config.adder->module_name);
        }
        catch (const std::invalid_argument &e)
        {
            std::cerr << "Error: " << e.what() << std::endl;
            return 1;
        }
    }

    return 0;
}
