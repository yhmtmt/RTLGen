#include <iostream>
#include <fstream>
#include "config.hpp"
#include <onnxruntime_cxx_api.h> // ONNX Runtime C++ API

using json = nlohmann::json;

// Function to print ONNX model summary
bool printOnnxModelSummary(const std::string& model_path) {
    try {
        Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "RTLGen");
        Ort::SessionOptions session_options;
        Ort::Session session(env, model_path.c_str(), session_options);

        std::cout << "[INFO] ONNX model loaded: " << model_path << std::endl;
        size_t num_inputs = session.GetInputCount();
        size_t num_outputs = session.GetOutputCount();

        Ort::AllocatorWithDefaultOptions allocator;

        std::cout << "[INFO] Number of inputs: " << num_inputs << std::endl;
        for (size_t i = 0; i < num_inputs; ++i) {
            Ort::AllocatedStringPtr input_name_ptr = session.GetInputNameAllocated(i, allocator);
            std::cout << "  Input[" << i << "]: " << input_name_ptr.get() << std::endl;
        }

        std::cout << "[INFO] Number of outputs: " << num_outputs << std::endl;
        for (size_t i = 0; i < num_outputs; ++i) {
            Ort::AllocatedStringPtr output_name_ptr = session.GetOutputNameAllocated(i, allocator);
            std::cout << "  Output[" << i << "]: " << output_name_ptr.get() << std::endl;
        }
    } catch (const Ort::Exception& e) {
        std::cerr << "Error loading ONNX model: " << e.what() << std::endl;
        return false;
    }
    return true;
}

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
            multiplier_config.module_name = j["multiplier"]["module_name"];
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

        if (j.contains("onnx_model")) {
            config.onnx_model = j["onnx_model"].get<std::string>();
            printOnnxModelSummary(config.onnx_model.value());
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: Invalid JSON format: " << e.what() << std::endl;
        return false;
    }

    return true;
}
