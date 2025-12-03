#include <iostream>
#include <fstream>
#include <unordered_set>
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

        config.operands.clear();
        config.multipliers.clear();
        config.adders.clear();
        config.yosys_multipliers.clear();
        config.mcm_operations.clear();
        config.cmvm_operations.clear();
        config.fp_operations.clear();
        config.activation_operations.clear();
        config.onnx_model.reset();

        if (j.contains("operand")) {
            config.operand.bit_width = j["operand"]["bit_width"];
            config.operand.is_signed = j["operand"]["signed"];
        } else {
            config.operand.bit_width = 0;
            config.operand.is_signed = false;
        }

        if (j.contains("operands")) {
            const auto &ops = j["operands"];
            if (!ops.is_array()) {
                throw std::runtime_error("\"operands\" must be an array");
            }
            std::unordered_set<std::string> seenNames;
            for (const auto &entry : ops) {
                OperandDefinition def;
                def.name = entry.at("name").get<std::string>();
                if (def.name.empty()) {
                    throw std::runtime_error("Operand name cannot be empty");
                }
                if (!seenNames.insert(def.name).second) {
                    throw std::runtime_error("Duplicate operand name: " + def.name);
                }
                def.dimensions = entry.value("dimensions", 1);
                def.bit_width = entry.at("bit_width").get<int>();
                def.is_signed = entry.at("signed").get<bool>();
                def.kind = entry.value("kind", "int");
                if (def.kind == "fp") {
                    if (!entry.contains("fp_format") || !entry["fp_format"].is_object()) {
                        throw std::runtime_error("Floating-point operand requires fp_format {total_width, mantissa_width}");
                    }
                    OperandDefinition::FpFormat fmt;
                    fmt.total_width = entry["fp_format"].at("total_width").get<int>();
                    fmt.mantissa_width = entry["fp_format"].at("mantissa_width").get<int>();
                    if (fmt.total_width <= 0 || fmt.mantissa_width <= 0) {
                        throw std::runtime_error("fp_format widths must be positive for operand " + def.name);
                    }
                    if (fmt.mantissa_width >= fmt.total_width - 1) {
                        throw std::runtime_error("mantissa_width must be at least 1 smaller than total_width for operand " + def.name);
                    }
                    def.fp_format = fmt;
                    def.bit_width = fmt.total_width;
                }
                if (def.dimensions <= 0) {
                    throw std::runtime_error("Operand dimensions must be positive");
                }
                if (def.bit_width <= 0) {
                    throw std::runtime_error("Operand bit_width must be positive");
                }
                config.operands.push_back(def);
            }
        }

        auto parseInputDelays = [&](const json &node) -> std::vector<float> {
            if (!node.contains("input_delays")) {
                return {};
            }
            const auto &delaysNode = node["input_delays"];
            std::vector<float> delays;
            if (delaysNode.is_number()) {
                delays.push_back(delaysNode.get<float>());
            } else if (delaysNode.is_array()) {
                if (delaysNode.empty()) {
                    throw std::runtime_error("\"input_delays\" array must not be empty");
                }
                for (const auto &d : delaysNode) {
                    if (!d.is_number()) {
                        throw std::runtime_error("\"input_delays\" entries must be numeric");
                    }
                    delays.push_back(d.get<float>());
                }
            } else {
                throw std::runtime_error("\"input_delays\" must be a number or array");
            }
            return delays;
        };

        auto parseAdderNode = [&](const json &node, const std::string &operandName, const std::string &moduleOverride) {
            AdderConfig adder;
            adder.module_name = moduleOverride.empty() ? node.at("module_name").get<std::string>() : moduleOverride;
            adder.operand = operandName;
            adder.cpa_structure = node.at("cpa_structure").get<std::string>();
            adder.pipeline_depth = node.value("pipeline_depth", 1);
            adder.input_delays = parseInputDelays(node);
            config.adders.push_back(adder);
        };

        auto parseMultiplierNode = [&](const json &node, const std::string &operandName, const std::string &moduleOverride) {
            MultiplierConfig multiplier;
            multiplier.module_name = moduleOverride.empty() ? node.at("module_name").get<std::string>() : moduleOverride;
            multiplier.operand = operandName;
            multiplier.ppg_algorithm = node.at("ppg_algorithm").get<std::string>();
            multiplier.compressor_structure = node.at("compressor_structure").get<std::string>();
            multiplier.cpa_structure = node.at("cpa_structure").get<std::string>();
            multiplier.pipeline_depth = node.value("pipeline_depth", 1);
            config.multipliers.push_back(multiplier);
        };

        auto parseYosysMultiplierNode = [&](const json &node, const std::string &operandName, const std::string &moduleOverride) {
            MultiplierYosysConfig yc;
            yc.module_name = moduleOverride.empty() ? node.at("module_name").get<std::string>() : moduleOverride;
            yc.operand = operandName;
            yc.booth_type = node.at("booth_type").get<std::string>();
            yc.is_signed = false;
            yc.bit_width = 0;
            config.yosys_multipliers.push_back(yc);
        };

        if (j.contains("multiplier")) {
            parseMultiplierNode(j["multiplier"], "", "");
        }

        if (j.contains("adder")) {
            parseAdderNode(j["adder"], "", "");
        }

        if (j.contains("multiplier_yosys")) {
            parseYosysMultiplierNode(j["multiplier_yosys"], "", "");
        }

        if (j.contains("operations")) {
            const auto &ops = j["operations"];
            if (!ops.is_array()) {
                throw std::runtime_error("\"operations\" must be an array");
            }
            for (const auto &entry : ops) {
                std::string type = entry.at("type").get<std::string>();
                std::string module_name = entry.at("module_name").get<std::string>();
                std::string operand_name = entry.value("operand", "");
                if (type == "adder") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    parseAdderNode(options, operand_name, module_name);
                } else if (type == "multiplier") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    parseMultiplierNode(options, operand_name, module_name);
                } else if (type == "multiplier_yosys") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    parseYosysMultiplierNode(options, operand_name, module_name);
                } else if (type == "mcm") {
                    if (!entry.contains("constants") || !entry["constants"].is_array()) {
                        throw std::runtime_error("MCM operation requires \"constants\" array");
                    }
                    McmOperationConfig mcm;
                    mcm.module_name = module_name;
                    mcm.operand = operand_name;
                    for (const auto &c : entry["constants"]) {
                        long long coeff = c.get<long long>();
                        if (coeff <= 0) {
                            throw std::runtime_error("MCM constants must be positive integers");
                        }
                        mcm.constants.push_back(coeff);
                    }
                    if (mcm.constants.empty()) {
                        throw std::runtime_error("MCM operation requires at least one constant");
                    }
                    if (entry.contains("synthesis")) {
                        const auto &syn = entry["synthesis"];
                        mcm.synthesis.engine = syn.value("engine", "heuristic");
                        mcm.synthesis.algorithm = syn.value("algorithm", "HCub");
                        mcm.synthesis.max_adders = syn.value("max_adders", 0);
                        mcm.synthesis.emit_schedule = syn.value("emit_schedule", false);
                    }
                    config.mcm_operations.push_back(mcm);
                } else if (type == "cmvm") {
                    if (operand_name.empty()) {
                        throw std::runtime_error("CMVM operation must reference an operand");
                    }
                    if (!entry.contains("matrix") || !entry["matrix"].is_array()) {
                        throw std::runtime_error("CMVM operation requires a \"matrix\" array");
                    }
                    CmvmOperationConfig cmvm;
                    cmvm.module_name = module_name;
                    cmvm.operand = operand_name;
                    const auto &matrix = entry["matrix"];
                    if (matrix.empty()) {
                        throw std::runtime_error("CMVM matrix cannot be empty");
                    }
                    std::size_t cols = matrix.front().size();
                    if (cols == 0) {
                        throw std::runtime_error("CMVM matrix rows must have at least one column");
                    }
                    for (const auto &row : matrix) {
                        if (!row.is_array() || row.size() != cols) {
                            throw std::runtime_error("CMVM matrix rows must have equal length");
                        }
                        std::vector<long long> values;
                        values.reserve(row.size());
                        for (const auto &val : row) {
                            values.push_back(val.get<long long>());
                        }
                        cmvm.matrix.push_back(std::move(values));
                    }
                    if (entry.contains("synthesis")) {
                        const auto &syn = entry["synthesis"];
                        cmvm.synthesis.algorithm = syn.value("algorithm", "HCMVM");
                        cmvm.synthesis.difference_rows = syn.value("difference_rows", false);
                        cmvm.synthesis.max_pair_search = syn.value("max_pair_search", 0);
                        if (syn.contains("fallback_algorithm")) {
                            cmvm.synthesis.fallback_algorithm = syn["fallback_algorithm"].get<std::string>();
                        }
                    }
                    config.cmvm_operations.push_back(cmvm);
                } else if (type == "fp_mul") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    FpOperationConfig fp;
                    fp.type = type;
                    fp.module_name = module_name;
                    fp.operand = operand_name;
                    fp.rounding_mode = options.value("rounding_mode", "RNE");
                    fp.flush_subnormals = options.value("flush_subnormals", false);
                    fp.pipeline_stages = options.value("pipeline_stages", 0);
                    config.fp_operations.push_back(fp);
                } else if (type == "fp_add") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    FpOperationConfig fp;
                    fp.type = type;
                    fp.module_name = module_name;
                    fp.operand = operand_name;
                    fp.rounding_mode = options.value("rounding_mode", "RNE");
                    fp.flush_subnormals = options.value("flush_subnormals", false);
                    fp.pipeline_stages = options.value("pipeline_stages", 0);
                    config.fp_operations.push_back(fp);
                } else if (type == "fp_mac") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    FpOperationConfig fp;
                    fp.type = type;
                    fp.module_name = module_name;
                    fp.operand = operand_name;
                    fp.rounding_mode = options.value("rounding_mode", "RNE");
                    fp.flush_subnormals = options.value("flush_subnormals", false);
                    fp.pipeline_stages = options.value("pipeline_stages", 0);
                    config.fp_operations.push_back(fp);
                } else if (type == "activation") {
                    const json &options = entry.contains("options") ? entry["options"] : entry;
                    ActivationOperationConfig act;
                    act.module_name = module_name;
                    act.operand = operand_name;
                    act.function = options.at("function").get<std::string>();
                    act.alpha_num = options.value("alpha_num", 1);
                    act.alpha_den = options.value("alpha_den", 10);
                    act.impl = options.value("impl", "default");
                    act.frac_bits = options.value("frac_bits", 0);
                    act.segments = options.value("segments", 0);
                    if (options.contains("breakpoints")) for (const auto &bp : options["breakpoints"]) act.breakpoints.push_back(bp.get<double>());
                    if (options.contains("slopes")) for (const auto &s : options["slopes"]) act.slopes.push_back(s.get<double>());
                    if (options.contains("intercepts")) for (const auto &c : options["intercepts"]) act.intercepts.push_back(c.get<double>());
                    if (options.contains("points")) {
                        const auto &pts = options["points"];
                        if (!pts.is_array()) throw std::runtime_error("\"points\" must be an array of [x,y]");
                        for (const auto &pt : pts) {
                            if (!pt.is_array() || pt.size() != 2) throw std::runtime_error("Each point must be [x,y]");
                            act.xs.push_back(pt[0].get<double>());
                            act.ys.push_back(pt[1].get<double>());
                        }
                    }
                    act.clamp = options.value("clamp", true);
                    act.symmetric = options.value("symmetric", true);
                    if (act.alpha_den == 0) {
                        throw std::runtime_error("alpha_den must be non-zero for activation " + act.module_name);
                    }
                    config.activation_operations.push_back(act);
                } else {
                    throw std::runtime_error("Unknown operation type: " + type);
                }
            }
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
