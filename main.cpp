#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <limits>
#include "multiplier.hpp"
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
    int pipeline_depth;
};

struct CircuitConfig {
    OperandConfig operand;
    MultiplierConfig multiplier;
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

        config.multiplier.module_name = j["multiplier"]["module_name"]; // Read module name
        config.multiplier.ppg_algorithm = j["multiplier"]["ppg_algorithm"];
        config.multiplier.compressor_structure = j["multiplier"]["compressor_structure"];
        config.multiplier.pipeline_depth = j["multiplier"]["pipeline_depth"];

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
        std::cout << "Module Name: " << config.multiplier.module_name << "\n";
        std::cout << "Operand Bit Width: " << config.operand.bit_width << "\n";
        std::cout << "Operand Signed: " << (config.operand.is_signed ? "Yes" : "No") << "\n";
        std::cout << "PPG Algorithm: " << config.multiplier.ppg_algorithm << "\n";
        std::cout << "Compressor Structure: " << config.multiplier.compressor_structure << "\n";
        std::cout << "Pipeline Depth: " << config.multiplier.pipeline_depth << "\n";
    } else {
        std::cerr << "Failed to load configuration.\n";
        return 1;
    }

    Operand multiplicand;
    multiplicand.width = config.operand.bit_width;
    multiplicand.is_signed = config.operand.is_signed;
    multiplicand.bits.assign(multiplicand.width, false); // Initialize bits

    Operand multiplier = multiplicand; // Use the same operand for simplicity

    CTType ctype;
    if (config.multiplier.compressor_structure == "AdderTree") {
        ctype = AdderTree;
    } else if (config.multiplier.compressor_structure == "CSATree") {
        ctype = CSATree;
    } else if (config.multiplier.compressor_structure == "Sequential") {
        ctype = Sequential;
    } else {
        std::cerr << "Error: Unknown compressor structure: " << config.multiplier.compressor_structure << "\n";
        return 1;
    }

    PPType ptype;
    if (config.multiplier.ppg_algorithm == "Normal") {
        ptype = Normal;
    } else if (config.multiplier.ppg_algorithm == "Normal4") {
        ptype = Normal4;
    } else if (config.multiplier.ppg_algorithm == "Normal8") {
        ptype = Normal8;
    } else if (config.multiplier.ppg_algorithm == "Normal16") {
        ptype = Normal16;
    } else if (config.multiplier.ppg_algorithm == "Booth4") {
        ptype = Booth4;
    } else if (config.multiplier.ppg_algorithm == "Booth8") {
        ptype = Booth8;
    } else if (config.multiplier.ppg_algorithm == "Booth16") {
        ptype = Booth16;
    } else {
        std::cerr << "Error: Unknown PPG algorithm: " << config.multiplier.ppg_algorithm << "\n";
        return 1;
    }

    MultiplierGenerator mg;
    mg.build(multiplicand, multiplier, ctype, ptype, config.multiplier.module_name);

    return 0;
}
