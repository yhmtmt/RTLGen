#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <limits>
#include "multiplier.hpp"
#include "adder.hpp"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct OperandConfig {
    int bit_width;
    bool is_signed;
};

struct MultiplierConfig {
    std::string module_name; // Added module name
    std::string ppg_algorithm;
    std::string compressor_structure;
    std::string cpa_structure;
    int pipeline_depth;
};

struct AdderConfig {
    std::string module_name;
    std::string cpa_structure;
    int pipeline_depth;
};

struct CircuitConfig {
    OperandConfig operand;
    std::optional<MultiplierConfig> multiplier;
    std::optional<AdderConfig> adder;
    std::optional<MultiplierYosysConfig> multiplier_yosys;
};

// Function to read JSON config from file
bool readConfig(const std::string& filename, CircuitConfig& config) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Unable to open file: " << filename << std::endl;
        return false;
    }

    try {
        json j;
        file >> j;

        config.operand.bit_width = j["operand"]["bit_width"];
        config.operand.is_signed = j["operand"]["signed"];

        if (j.contains("multiplier")) {
            MultiplierConfig multiplier_config;
            multiplier_config.module_name = j["multiplier"]["module_name"]; // Read module name
            multiplier_config.ppg_algorithm = j["multiplier"]["ppg_algorithm"];
            multiplier_config.compressor_structure = j["multiplier"]["compressor_structure"];
            multiplier_config.pipeline_depth = j["multiplier"]["pipeline_depth"];
            multiplier_config.cpa_structure = j["multiplier"]["cpa_structure"];
            config.multiplier = multiplier_config;
        }

        if (j.contains("adder")) {
            AdderConfig adder_config;
            adder_config.module_name = j["adder"]["module_name"];
            adder_config.cpa_structure = j["adder"]["cpa_structure"];
            adder_config.pipeline_depth = j["adder"]["pipeline_depth"];
            config.adder = adder_config;
        }

        if (j.contains("multiplier_yosys")) {
            MultiplierYosysConfig yosys_config;
            yosys_config.module_name = j["multiplier_yosys"]["module_name"];
            yosys_config.booth_type = j["multiplier_yosys"]["booth_type"];
            yosys_config.is_signed = j["operand"]["signed"];
            yosys_config.bit_width = j["operand"]["bit_width"];
            config.multiplier_yosys = yosys_config;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: Invalid JSON format: " << e.what() << std::endl;
        return false;
    }

    return true;
}

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

        CTType ctype;
        if (config.multiplier->compressor_structure == "AdderTree") {
            ctype = AdderTree;
        } else if (config.multiplier->compressor_structure == "CSATree") {
            ctype = CSATree;
        } else {
            std::cerr << "Error: Unknown compressor structure: " << config.multiplier->compressor_structure << "\n";
            return 1;
        }

        CPAType cptype;
        if (config.multiplier->cpa_structure == "Ripple") {
            cptype = CPA_Ripple;
        } else if (config.multiplier->cpa_structure == "KoggeStone") {
            cptype = CPA_KoggeStone;
        } else if (config.multiplier->cpa_structure == "BrentKung") {
            cptype = CPA_BrentKung;
        }else if(config.multiplier->cpa_structure == "Sklansky"){
            cptype = CPA_Sklansky;
        } else {
            std::cerr << "Error: Unknown CPA structure: " << config.multiplier->cpa_structure << "\n";
            return 1;
        }

        PPType ptype;
        if (config.multiplier->ppg_algorithm == "Normal") {
            ptype = Normal;
        } else if (config.multiplier->ppg_algorithm == "Normal4") {
            ptype = Normal4;
        } else if (config.multiplier->ppg_algorithm == "Normal8") {
            ptype = Normal8;
        } else if (config.multiplier->ppg_algorithm == "Normal16") {
            ptype = Normal16;
        } else if (config.multiplier->ppg_algorithm == "Booth4") {
            ptype = Booth4;
        } else if (config.multiplier->ppg_algorithm == "Booth8") {
            ptype = Booth8;
        } else if (config.multiplier->ppg_algorithm == "Booth16") {
            ptype = Booth16;
        } else {
            std::cerr << "Error: Unknown PPG algorithm: " << config.multiplier->ppg_algorithm << "\n";
            return 1;
        }

        MultiplierGenerator mg;
        mg.build(multiplicand, multiplier_operand, ctype, ptype, cptype, config.multiplier->module_name);
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

        CPAType cptype;
        if (config.adder->cpa_structure == "Ripple") {
            cptype = CPA_Ripple;
        } else if (config.adder->cpa_structure == "KoggeStone") {
            cptype = CPA_KoggeStone;
        } else if (config.adder->cpa_structure == "BrentKung") {
            cptype = CPA_BrentKung;
        } else {
            std::cerr << "Error: Unknown CPA structure: " << config.adder->cpa_structure << "\n";
            return 1;
        }

        CarryPropagatingAdder cpa;
        cpa.init(config.operand.bit_width, cptype);
        cpa.dump_hdl(config.adder->module_name);
    }

    return 0;
}
