#include "rtl_operations.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include "cmvm.hpp"
#include "mcm_algorithms.hpp"
#include "mcm_ilp.hpp"

namespace {

constexpr unsigned __int128 kUint128Max = ~static_cast<unsigned __int128>(0);

std::string toUpper(std::string value) {
    for (char &ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

uint32_t encodeFp32(double v) {
    union {
        float f;
        uint32_t u;
    } conv;
    conv.f = static_cast<float>(v);
    return conv.u;
}

std::string zeroLiteral(int width) {
    if (width <= 0) {
        throw std::runtime_error("Output width must be positive");
    }
    std::ostringstream oss;
    oss << "{" << width << "{1'b0}}";
    return oss.str();
}

std::string extendSignal(const std::string &signal, int signalWidth, int targetWidth,
                         bool isSigned) {
    if (signalWidth <= 0 || targetWidth <= 0) {
        throw std::runtime_error("Signal widths must be positive");
    }
    if (targetWidth <= signalWidth) {
        if (isSigned) {
            std::ostringstream oss;
            oss << "$signed(" << signal << ")";
            return oss.str();
        }
        return signal;
    }
    int pad = targetWidth - signalWidth;
    std::ostringstream oss;
    if (isSigned) {
        oss << "{{" << pad << "{" << signal << "[" << (signalWidth - 1) << "]}}," << signal
            << "}";
    } else {
        oss << "{{" << pad << "{1'b0}}," << signal << "}";
    }
    return oss.str();
}

std::string emitShiftedExpr(const std::string &extended, int shift) {
    if (shift == 0) {
        return extended;
    }
    std::ostringstream oss;
    oss << "(" << extended << " << " << shift << ")";
    return oss.str();
}

std::string emitSumChain(std::ofstream &os, const std::vector<std::string> &terms,
                         const std::string &prefix, bool signedResult, int width) {
    if (terms.empty()) {
        return zeroLiteral(width);
    }
    if (terms.size() == 1) {
        return terms.front();
    }
    std::string acc = terms[0];
    for (std::size_t idx = 1; idx < terms.size(); ++idx) {
        std::string wireName = prefix + "_" + std::to_string(idx - 1);
        os << "  wire " << (signedResult ? "signed " : "") << "[" << (width - 1) << ":0] "
           << wireName << " = " << acc << " + " << terms[idx] << ";\n";
        acc = wireName;
    }
    return acc;
}

int ceilLog2U64(unsigned long long value) {
    if (value <= 1) {
        return 0;
    }
    unsigned long long v = 1;
    int bits = 0;
    while (v < value) {
        v <<= 1;
        ++bits;
    }
    return bits;
}

int ceilLog2Uint128(unsigned __int128 value) {
    if (value <= 1) {
        return 0;
    }
    unsigned __int128 v = 1;
    int bits = 0;
    while (v < value) {
        v <<= 1;
        ++bits;
    }
    return bits;
}

unsigned __int128 mulUint128(unsigned __int128 a, unsigned __int128 b) {
    if (a == 0 || b == 0) {
        return 0;
    }
    if (a > kUint128Max / b) {
        throw std::runtime_error("Magnitude overflow while computing CMVM bounds");
    }
    return a * b;
}

void addSafe(unsigned __int128 &acc, unsigned __int128 value) {
    if (value > kUint128Max - acc) {
        throw std::runtime_error("Magnitude overflow while computing CMVM bounds");
    }
    acc += value;
}

unsigned __int128 maxUnsignedValue(int width) {
    if (width <= 0 || width >= 128) {
        throw std::runtime_error("Operand bit width must be in [1,127]");
    }
    return (static_cast<unsigned __int128>(1) << width) - 1;
}

unsigned __int128 maxAbsSignedValue(int width) {
    if (width <= 0 || width >= 128) {
        throw std::runtime_error("Operand bit width must be in [1,127]");
    }
    return static_cast<unsigned __int128>(1) << (width - 1);
}

int computeSignedWidth(unsigned __int128 positiveBound, unsigned __int128 negativeBound) {
    int width = 1;
    while (true) {
        if (width >= 128) {
            throw std::runtime_error("Required signed width exceeds 127 bits");
        }
        unsigned __int128 posLimit =
            (width == 1) ? 0 : ((static_cast<unsigned __int128>(1) << (width - 1)) - 1);
        unsigned __int128 negLimit = static_cast<unsigned __int128>(1) << (width - 1);
        if (positiveBound <= posLimit && negativeBound <= negLimit) {
            return width;
        }
        ++width;
    }
}

int computeUnsignedWidth(unsigned __int128 bound) {
    int width = 1;
    while (true) {
        if (width >= 128) {
            throw std::runtime_error("Required unsigned width exceeds 127 bits");
        }
        unsigned __int128 limit = (static_cast<unsigned __int128>(1) << width) - 1;
        if (bound <= limit) {
            return width;
        }
        ++width;
    }
}

mcm::Solution runHeuristicMcm(const McmOperationConfig &config,
                              const OperandDefinition &operand) {
    mcm::InputSpec spec{operand.bit_width, config.constants};
    std::string algo = toUpper(config.synthesis.algorithm);
    if (algo == "BHA") {
        return mcm::runBHA(spec);
    }
    if (algo == "BHM") {
        return mcm::runBHM(spec);
    }
    if (algo == "RAGN" || algo == "RAG-N") {
        return mcm::runRAGn(spec);
    }
    if (algo == "HCUB" || algo == "H_CUB") {
        return mcm::runHCub(spec);
    }
    throw std::runtime_error("Unknown heuristic MCM algorithm: " + config.synthesis.algorithm);
}

mcm::Solution runIlpMcm(const McmOperationConfig &config, const OperandDefinition &operand) {
    mcm::IlpConfig ilp{operand.bit_width, config.constants, 0};
    int budget = config.synthesis.max_adders;
    if (budget <= 0) {
        auto estimator = mcm::parseEstimator(config.synthesis.algorithm)
                             .value_or(mcm::AdderEstimator::HCub);
        mcm::InputSpec spec{operand.bit_width, config.constants};
        budget = mcm::estimateAdders(spec, estimator);
        if (budget <= 0) {
            throw std::runtime_error("Failed to estimate ILP adder budget");
        }
    }
    ilp.adderBudget = budget;
    auto result = mcm::runIlpOptimal(ilp);
    if (!result.feasible) {
        throw std::runtime_error("ILP synthesis failed within budget " + std::to_string(budget));
    }
    return result.solution;
}

mcm::Solution synthesizeMcm(const McmOperationConfig &config, const OperandDefinition &operand) {
    std::string engine = toUpper(config.synthesis.engine);
    if (engine == "ILP") {
        return runIlpMcm(config, operand);
    }
    if (engine.empty() || engine == "HEURISTIC") {
        return runHeuristicMcm(config, operand);
    }
    throw std::runtime_error("Unknown MCM synthesis engine: " + config.synthesis.engine);
}

unsigned __int128 fundamentalMagnitude(const mcm::Operation &op) {
    return static_cast<unsigned __int128>(op.result) << op.rShift;
}

unsigned __int128 computeMaxMagnitude(const mcm::Solution &solution,
                                      const std::vector<long long> &constants) {
    unsigned __int128 maxMag = 1;
    for (long long c : constants) {
        unsigned long long absC = static_cast<unsigned long long>(std::llabs(c));
        if (absC > 0 && static_cast<unsigned __int128>(absC) > maxMag) {
            maxMag = absC;
        }
    }
    for (const auto &op : solution.operations) {
        unsigned __int128 mag = fundamentalMagnitude(op);
        if (mag > maxMag) {
            maxMag = mag;
        }
    }
    return maxMag;
}

void writeScheduleFile(const std::string &moduleName, const mcm::Solution &solution,
                       const std::vector<long long> &constants) {
    std::ofstream sched(moduleName + ".sched");
    if (!sched.is_open()) {
        throw std::runtime_error("Failed to write schedule for " + moduleName);
    }
    sched << "# MCM schedule for " << moduleName << "\n";
    sched << "# constants:";
    for (long long c : constants) {
        sched << " " << c;
    }
    sched << "\n";
    for (std::size_t idx = 0; idx < solution.operations.size(); ++idx) {
        sched << (idx + 1) << ": " << solution.operations[idx].describe() << "\n";
    }
}

int computeWidthForCoeffs(const std::vector<long long> &coeffs, const OperandDefinition &operand,
                          bool &isSigned) {
    if (operand.is_signed) {
        unsigned __int128 magnitude = 0;
        unsigned __int128 maxAbs = maxAbsSignedValue(operand.bit_width);
        for (long long coeff : coeffs) {
            addSafe(magnitude,
                    mulUint128(maxAbs, static_cast<unsigned __int128>(std::llabs(coeff))));
        }
        isSigned = true;
        int width = computeSignedWidth(magnitude, magnitude);
        return std::max(width, operand.bit_width);
    }
    unsigned __int128 positive = 0;
    unsigned __int128 negative = 0;
    unsigned __int128 maxVal = maxUnsignedValue(operand.bit_width);
    for (long long coeff : coeffs) {
        unsigned __int128 term =
            mulUint128(maxVal, static_cast<unsigned __int128>(std::llabs(coeff)));
        if (coeff >= 0) {
            addSafe(positive, term);
        } else {
            addSafe(negative, term);
        }
    }
    isSigned = negative > 0;
    int width = isSigned ? computeSignedWidth(positive, negative) : computeUnsignedWidth(positive);
    return std::max(width, operand.bit_width);
}

cse::CmvmSynthesisOptions makeCmvmOptions(const CmvmSynthesisConfig &cfg) {
    cse::CmvmSynthesisOptions opts;
    opts.algorithm = cfg.algorithm;
    opts.differenceRows = cfg.difference_rows;
    opts.maxPairSearch = cfg.max_pair_search;
    opts.fallbackAlgorithm = cfg.fallback_algorithm;
    return opts;
}

int shiftFromPowerOfTwo(long long coeff) {
    long long mag = std::llabs(coeff);
    int shift = 0;
    while (mag > 1 && (mag & 1LL) == 0) {
        mag >>= 1LL;
        ++shift;
    }
    return shift;
}

} // namespace

void emitMcmModule(const McmOperationConfig &config, const OperandDefinition &operand) {
    if (operand.bit_width <= 0) {
        throw std::runtime_error("Operand bit width must be positive for MCM generation");
    }
    if (operand.dimensions != 1) {
        throw std::runtime_error("MCM operand must be scalar (dimensions = 1)");
    }
    if (config.constants.empty()) {
        throw std::runtime_error("MCM operation requires at least one constant");
    }
    auto maxIt = std::max_element(config.constants.begin(), config.constants.end());
    if (*maxIt <= 0) {
        throw std::runtime_error("MCM constants must be positive");
    }

    mcm::Solution solution = synthesizeMcm(config, operand);
    if (config.synthesis.emit_schedule) {
        writeScheduleFile(config.module_name, solution, config.constants);
    }

    unsigned __int128 maxMag = computeMaxMagnitude(solution, config.constants);
    int outWidth = operand.bit_width + ceilLog2Uint128(maxMag);
    outWidth = std::max(outWidth, operand.bit_width);
    int internalWidth = std::max(outWidth, operand.bit_width + ceilLog2Uint128(maxMag));

    std::ofstream os(config.module_name + ".v");
    if (!os.is_open()) {
        throw std::runtime_error("Failed to open output file for " + config.module_name);
    }

    std::vector<std::string> ports;
    {
        std::ostringstream port;
        port << "input " << (operand.is_signed ? "signed " : "") << "[" << (operand.bit_width - 1)
             << ":0] " << operand.name << "_0";
        ports.push_back(port.str());
    }
    for (std::size_t idx = 0; idx < config.constants.size(); ++idx) {
        std::ostringstream port;
        port << "output " << (operand.is_signed ? "signed " : "") << "[" << (outWidth - 1) << ":0] "
             << config.module_name << "_out" << idx;
        ports.push_back(port.str());
    }

    os << "module " << config.module_name << "(\n";
    for (std::size_t i = 0; i < ports.size(); ++i) {
        os << "    " << ports[i];
        if (i + 1 < ports.size()) {
            os << ",";
        }
        os << "\n";
    }
    os << ");\n\n";
    os << "  // Automatically generated multiple-constant multiplication block (" << solution.name
       << ")\n";

    const std::string lane = operand.name + "_0";
    const std::string baseWire = config.module_name + "_base";
    os << "  wire " << (operand.is_signed ? "signed " : "") << "[" << (internalWidth - 1)
       << ":0] " << baseWire << " = "
       << extendSignal(lane, operand.bit_width, internalWidth, operand.is_signed) << ";\n";

    std::unordered_map<mcm::Value, std::string> valueSignals;
    valueSignals[1] = baseWire;

    for (std::size_t idx = 0; idx < solution.operations.size(); ++idx) {
        const auto &op = solution.operations[idx];
        auto uIt = valueSignals.find(op.u);
        auto vIt = valueSignals.find(op.v);
        if (uIt == valueSignals.end() || vIt == valueSignals.end()) {
            throw std::runtime_error("Incomplete MCM schedule for " + config.module_name);
        }
        std::string lhs = emitShiftedExpr(uIt->second, op.l1);
        std::string rhs = emitShiftedExpr(vIt->second, op.l2);
        if (op.subtraction) {
            unsigned __int128 lhsCoeff = static_cast<unsigned __int128>(op.u) << op.l1;
            unsigned __int128 rhsCoeff = static_cast<unsigned __int128>(op.v) << op.l2;
            if (rhsCoeff > lhsCoeff) {
                std::swap(lhs, rhs);
            }
        }
        std::string expr =
            op.subtraction ? "(" + lhs + " - " + rhs + ")" : "(" + lhs + " + " + rhs + ")";
        if (op.rShift > 0) {
            expr = "(" + expr + ") " + (operand.is_signed ? ">>>" : ">>") + " " +
                   std::to_string(op.rShift);
        }
        std::string wireName = config.module_name + "_n" + std::to_string(idx);
        os << "  wire " << (operand.is_signed ? "signed " : "") << "[" << (internalWidth - 1)
           << ":0] " << wireName << " = " << expr << ";\n";
        valueSignals[op.result] = wireName;
    }

    os << "\n";
    for (std::size_t idx = 0; idx < config.constants.size(); ++idx) {
        int shift = 0;
        mcm::Value odd = mcm::normalizeOdd(config.constants[idx], shift);
        auto it = valueSignals.find(odd);
        if (it == valueSignals.end()) {
            throw std::runtime_error("Failed to synthesize constant " + std::to_string(odd));
        }
        std::string widened =
            extendSignal(it->second, internalWidth, outWidth, operand.is_signed);
        std::string outExpr = emitShiftedExpr(widened, shift);
        os << "  assign " << config.module_name << "_out" << idx << " = " << outExpr << ";\n";
    }
    os << "endmodule\n";
}

void emitCmvmModule(const CmvmOperationConfig &config, const OperandDefinition &operand) {
    if (operand.bit_width <= 0) {
        throw std::runtime_error("Operand bit width must be positive for CMVM generation");
    }
    if (operand.dimensions <= 0) {
        throw std::runtime_error("Operand dimensions must be positive for CMVM generation");
    }
    if (config.matrix.empty()) {
        throw std::runtime_error("CMVM matrix cannot be empty");
    }
    const std::size_t cols = config.matrix.front().size();
    if (cols == 0) {
        throw std::runtime_error("CMVM matrix rows must have at least one column");
    }
    if (static_cast<int>(cols) != operand.dimensions) {
        throw std::runtime_error("CMVM matrix column count must match operand dimensions");
    }

    cse::ProblemInstance instance;
    instance.rows = static_cast<int>(config.matrix.size());
    instance.cols = static_cast<int>(cols);
    instance.bitWidth = operand.bit_width;
    instance.matrix = config.matrix;

    auto options = makeCmvmOptions(config.synthesis);
    auto outcome = cse::synthesizeCmvm(instance, options);
    const auto &ctx = outcome.context;

    std::vector<std::string> ports;
    for (int lane = 0; lane < operand.dimensions; ++lane) {
        std::ostringstream port;
        port << "input " << (operand.is_signed ? "signed " : "") << "[" << (operand.bit_width - 1)
             << ":0] " << operand.name << "_" << lane;
        ports.push_back(port.str());
    }

    const std::size_t rowCount = config.matrix.size();
    std::vector<int> rowWidths(rowCount, operand.bit_width);
    std::vector<bool> rowSigned(rowCount, operand.is_signed);
    for (std::size_t row = 0; row < rowCount; ++row) {
        bool signedRow = rowSigned[row];
        rowWidths[row] = computeWidthForCoeffs(config.matrix[row], operand, signedRow);
        rowSigned[row] = signedRow;
    }

    for (std::size_t row = 0; row < ctx.expressions.size(); ++row) {
        std::ostringstream port;
        port << "output " << (rowSigned[row] ? "signed " : "") << "[" << (rowWidths[row] - 1)
             << ":0] " << config.module_name << "_out" << row;
        ports.push_back(port.str());
    }

    std::ofstream os(config.module_name + ".v");
    if (!os.is_open()) {
        throw std::runtime_error("Failed to open output file for " + config.module_name);
    }

    os << "module " << config.module_name << "(\n";
    for (std::size_t i = 0; i < ports.size(); ++i) {
        os << "    " << ports[i];
        if (i + 1 < ports.size()) {
            os << ",";
        }
        os << "\n";
    }
    os << ");\n\n";
    os << "  // Automatically generated constant matrix-vector multiplication block ("
       << outcome.stats.name << ")\n";

    const auto &signals = ctx.table.signals();
    std::vector<std::string> signalNames(signals.size());
    std::vector<int> signalWidths(signals.size(), operand.bit_width);
    std::vector<bool> signalSigned(signals.size(), operand.is_signed);

    for (const auto &sig : signals) {
        bool signedSig = operand.is_signed;
        int width = computeWidthForCoeffs(sig.coeffs, operand, signedSig);
        if (sig.id >= static_cast<int>(signalNames.size())) {
            signalNames.resize(sig.id + 1);
            signalWidths.resize(sig.id + 1, operand.bit_width);
            signalSigned.resize(sig.id + 1, operand.is_signed);
        }
        signalNames[sig.id] = config.module_name + "_s" + std::to_string(sig.id);
        signalWidths[sig.id] = width;
        signalSigned[sig.id] = signedSig;
    }

    for (const auto &sig : signals) {
        std::string expr;
        if (sig.left < 0 && sig.right < 0) {
            int lane = -1;
            long long coeff = 0;
            for (std::size_t idx = 0; idx < sig.coeffs.size(); ++idx) {
                if (sig.coeffs[idx] != 0) {
                    lane = static_cast<int>(idx);
                    coeff = sig.coeffs[idx];
                    break;
                }
            }
            if (lane < 0) {
                expr = zeroLiteral(signalWidths[sig.id]);
            } else {
                int shift = shiftFromPowerOfTwo(coeff);
                std::string base =
                    extendSignal(operand.name + "_" + std::to_string(lane), operand.bit_width,
                                 signalWidths[sig.id], operand.is_signed);
                expr = emitShiftedExpr(base, shift);
                if (coeff < 0) {
                    expr = "-(" + expr + ")";
                }
            }
        } else {
            std::string leftExpr = extendSignal(signalNames[sig.left], signalWidths[sig.left],
                                                signalWidths[sig.id], signalSigned[sig.left]);
            std::string rightExpr = extendSignal(signalNames[sig.right], signalWidths[sig.right],
                                                 signalWidths[sig.id], signalSigned[sig.right]);
            if (sig.leftSign < 0) {
                leftExpr = "-(" + leftExpr + ")";
            }
            if (sig.rightSign < 0) {
                rightExpr = "-(" + rightExpr + ")";
            }
            expr = leftExpr + " + " + rightExpr;
        }
        os << "  wire " << (signalSigned[sig.id] ? "signed " : "") << "["
           << (signalWidths[sig.id] - 1) << ":0] " << signalNames[sig.id] << " = " << expr
           << ";\n";
    }

    os << "\n";
    std::vector<std::string> rowSignals(ctx.expressions.size());
    for (std::size_t row = 0; row < ctx.expressions.size(); ++row) {
        std::vector<std::string> terms;
        for (const auto &term : ctx.expressions[row].terms()) {
            int id = term.signal;
            std::string termExpr = extendSignal(signalNames[id], signalWidths[id], rowWidths[row],
                                                signalSigned[id]);
            if (term.sign < 0) {
                termExpr = "-(" + termExpr + ")";
            }
            terms.push_back(termExpr);
        }
        std::string rowExpr =
            emitSumChain(os, terms, config.module_name + "_r" + std::to_string(row) + "_acc",
                         rowSigned[row], rowWidths[row]);
        std::string rowWire = config.module_name + "_row" + std::to_string(row);
        os << "  wire " << (rowSigned[row] ? "signed " : "") << "[" << (rowWidths[row] - 1)
           << ":0] " << rowWire << " = " << rowExpr << ";\n";
        rowSignals[row] = rowWire;
    }

    int recombIdx = 0;
    for (auto it = outcome.relations.rbegin(); it != outcome.relations.rend(); ++it) {
        const auto &rel = *it;
        if (rel.target < 0 || rel.reference < 0 ||
            rel.target >= static_cast<int>(rowSignals.size()) ||
            rel.reference >= static_cast<int>(rowSignals.size())) {
            throw std::runtime_error("Invalid recombination relation in CMVM synthesis");
        }
        std::string lhs =
            extendSignal(rowSignals[rel.target], rowWidths[rel.target], rowWidths[rel.target],
                         rowSigned[rel.target]);
        std::string rhs =
            extendSignal(rowSignals[rel.reference], rowWidths[rel.reference], rowWidths[rel.target],
                         rowSigned[rel.reference]);
        std::string wire = config.module_name + "_rec" + std::to_string(recombIdx++);
        os << "  wire " << (rowSigned[rel.target] ? "signed " : "") << "["
           << (rowWidths[rel.target] - 1) << ":0] " << wire << " = " << lhs << " + " << rhs
           << ";\n";
        rowSignals[rel.target] = wire;
    }

    os << "\n";
    for (std::size_t row = 0; row < rowSignals.size(); ++row) {
        os << "  assign " << config.module_name << "_out" << row << " = " << rowSignals[row]
           << ";\n\n";
    }
    os << "endmodule\n";
}

void emitActivationModule(const ActivationOperationConfig &config, const OperandDefinition &operand) {
    std::string fn = toUpper(config.function);
    if (fn != "RELU" && fn != "RELU6" && fn != "LEAKY_RELU" && fn != "TANH" &&
        fn != "GELU" && fn != "SOFTMAX" && fn != "LAYERNORM" && fn != "DRELU" &&
        fn != "DGELU" && fn != "DSOFTMAX" && fn != "DLAYERNORM" && fn != "PWL") {
        throw std::runtime_error("Unsupported activation function: " + config.function);
    }

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    bool is_fp = (operand.kind == "fp");
    int data_width = operand.bit_width;
    if (is_fp) {
        if (!operand.fp_format.has_value()) {
            throw std::runtime_error("FP activation requires fp_format on operand " + operand.name);
        }
        // FloPoCo-style: add 2 exception bits to total width
        data_width = operand.fp_format->total_width + 2;
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  [" << (data_width - 1) << ":0] X,\n";
    os << "  output [" << (data_width - 1) << ":0] Y\n";
    os << ");\n\n";

    if (is_fp) {
        int total_w = operand.fp_format->total_width;
        int frac_w = operand.fp_format->mantissa_width;
        int exp_w = total_w - frac_w - 1;
        os << "  wire [1:0] exn = X[" << (data_width - 1) << ":" << (data_width - 2) << "];\n";
        os << "  wire sign = X[" << (data_width - 3) << "];\n";
        os << "  wire [" << (data_width - 4) << ":0] payload = X[" << (data_width - 4) << ":0];\n";
        os << "  wire [" << (exp_w - 1) << ":0] exp_bits = X[" << (frac_w + exp_w - 1) << ":" << frac_w << "];\n";
        os << "  wire [" << (frac_w - 1) << ":0] frac_bits = X[" << (frac_w - 1) << ":0];\n";
        os << "  wire is_normal = (exn == 2'b01);\n";
        if (fn == "LEAKY_RELU") {
            if (config.alpha_num != 1 || (config.alpha_den & (config.alpha_den - 1)) != 0) {
                throw std::runtime_error("FP leaky_relu currently supports alpha_num=1 and alpha_den power-of-two");
            }
            int shift = 0;
            int den = config.alpha_den;
            while ((den >>= 1) > 0) ++shift;
            os << "  wire underflow = exp_bits <= " << shift << ";\n";
            os << "  wire [" << (exp_w - 1) << ":0] exp_scaled = exp_bits - " << shift << ";\n";
            os << "  wire [" << (data_width - 1) << ":0] scaled = underflow ? {2'b01, " << (data_width - 2) << "'b0}\n"
               << "                                            : {2'b01, 1'b1, exp_scaled, frac_bits};\n";
            os << "  wire [" << (data_width - 1) << ":0] leaky_val = (is_normal && sign) ? scaled : X;\n";
            os << "  assign Y = leaky_val;\n";
        } else if (fn == "TANH") {
            int bias = (1 << (exp_w - 1)) - 1; // exponent for 1.0
            int clamp_exp = bias + 3;          // ~|x| >= 8
            os << "  wire [" << (data_width - 3) << ":0] abs_payload = sign ? (~payload + 1'b1) : payload;\n";
            os << "  wire clamp_hi = is_normal && (exp_bits >= " << clamp_exp << ");\n";
            os << "  wire mid = is_normal && (exp_bits >= " << bias << ") && (exp_bits < " << clamp_exp << ");\n";
            os << "  wire [" << (exp_w - 1) << ":0] exp_scaled = exp_bits - 1'b1;\n";
            os << "  wire [" << (data_width - 1) << ":0] one_val = {2'b01, sign, " << exp_w << "'d" << bias << ", " << frac_w << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] mid_val = {2'b01, sign, exp_scaled, frac_bits};\n";
            os << "  wire [" << (data_width - 1) << ":0] pass_val = {2'b01, sign, exp_bits, frac_bits};\n";
            os << "  assign Y = clamp_hi ? one_val : (mid ? mid_val : pass_val);\n";
        } else if (fn == "GELU") {
            // Approximate GELU as 0.5 * ReLU(x)
            os << "  wire [" << (exp_w - 1) << ":0] exp_half = exp_bits - 1'b1;\n";
            os << "  wire underflow = exp_bits == { " << exp_w << "{1'b0}};\n";
            os << "  wire [" << (data_width - 1) << ":0] half_val = {2'b01, sign, exp_half, frac_bits};\n";
            os << "  wire [" << (data_width - 1) << ":0] relu_half = (is_normal && sign) ? {2'b01, " << (data_width - 2) << "'b0} : half_val;\n";
            os << "  assign Y = relu_half;\n";
        } else if (fn == "SOFTMAX") {
            int bias = (1 << (exp_w - 1)) - 1; // exponent for 1.0
            os << "  wire [" << (data_width - 1) << ":0] zero_fp = {2'b01, " << (data_width - 2) << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] one_fp = {2'b01, 1'b0, " << exp_w << "'d" << bias << ", " << frac_w << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] pos_passthrough = {2'b01, 1'b0, exp_bits, frac_bits};\n";
            os << "  assign Y = (is_normal && sign) ? zero_fp : ((is_normal && (exp_bits >= " << bias << ")) ? one_fp : pos_passthrough);\n";
        } else if (fn == "LAYERNORM") {
            // Scalar placeholder for lane-wise vector path.
            os << "  assign Y = X;\n";
        } else if (fn == "DRELU") {
            int bias = (1 << (exp_w - 1)) - 1; // exponent for 1.0
            os << "  wire [" << (data_width - 1) << ":0] zero_fp = {2'b01, " << (data_width - 2) << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] one_fp = {2'b01, 1'b0, " << exp_w << "'d" << bias << ", " << frac_w << "'b0};\n";
            os << "  assign Y = (is_normal && !sign && (X[" << (data_width - 4) << ":0] != 0)) ? one_fp : zero_fp;\n";
        } else if (fn == "DGELU") {
            int half_exp = (1 << (exp_w - 1)) - 2; // exponent for 0.5
            os << "  wire [" << (data_width - 1) << ":0] zero_fp = {2'b01, " << (data_width - 2) << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] half_fp = {2'b01, 1'b0, " << exp_w << "'d" << half_exp << ", " << frac_w << "'b0};\n";
            os << "  assign Y = (is_normal && !sign && (X[" << (data_width - 4) << ":0] != 0)) ? half_fp : zero_fp;\n";
        } else if (fn == "DSOFTMAX") {
            int qtr_exp = (1 << (exp_w - 1)) - 3; // exponent for 0.25
            os << "  wire [" << (data_width - 1) << ":0] zero_fp = {2'b01, " << (data_width - 2) << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] qtr_fp = {2'b01, 1'b0, " << exp_w << "'d" << qtr_exp << ", " << frac_w << "'b0};\n";
            os << "  assign Y = is_normal ? qtr_fp : zero_fp;\n";
        } else if (fn == "DLAYERNORM") {
            int bias = (1 << (exp_w - 1)) - 1; // exponent for 1.0
            os << "  assign Y = {2'b01, 1'b0, " << exp_w << "'d" << bias << ", " << frac_w << "'b0};\n";
        } else if (fn == "PWL") {
            if (operand.fp_format->total_width != 32) {
                throw std::runtime_error("FP PWL currently supports only 32-bit formats");
            }
            if (config.xs.size() < 2 || config.xs.size() != config.ys.size()) {
                throw std::runtime_error("FP PWL requires at least two points with matching x/y lengths");
            }
            int segs = static_cast<int>(config.xs.size()) - 1;
            os << "  wire [33:0] abs_bits = {exn, 1'b0, payload};\n";
            os << "  reg [33:0] y_bits;\n";
            for (int i = 0; i < segs; ++i) {
                uint32_t thr = encodeFp32(config.xs[i + 1]);
                uint32_t yenc = encodeFp32(config.ys[i + 1]);
                os << "  localparam [33:0] PWL_THR_" << i << " = 34'h" << std::hex << std::setw(9) << std::setfill('0') << thr << std::dec << ";\n";
                os << "  localparam [33:0] PWL_Y_" << i << " = 34'h" << std::hex << std::setw(9) << std::setfill('0') << yenc << std::dec << ";\n";
            }
            uint32_t ylast = encodeFp32(config.ys.back());
            os << "  localparam [33:0] PWL_Y_LAST = 34'h" << std::hex << std::setw(9) << std::setfill('0') << ylast << std::dec << ";\n";
            os << "  always @* begin\n";
            os << "    y_bits = {exn, 1'b0, payload};\n";
            os << "    if (exn == 2'b01) begin\n";
            for (int i = 0; i < segs; ++i) {
                os << "      if (abs_bits < PWL_THR_" << i << ") y_bits = PWL_Y_" << i << ";\n";
                os << "      else ";
            }
            os << "      y_bits = PWL_Y_LAST;\n";
            os << "    end\n";
            os << "    if (" << (config.symmetric ? "1'b1" : "1'b0") << " && sign) y_bits = {y_bits[33:32], 1'b1, y_bits[30:0]};\n";
            os << "  end\n";
            os << "  assign Y = y_bits;\n";
        } else { // RELU
            os << "  wire [" << (data_width - 1) << ":0] relu_val = (is_normal && sign) ? {2'b01, "
               << (data_width - 2) << "'b0} : X;\n";
            os << "  assign Y = relu_val;\n";
        }
    } else {
        // Integer activation
        if (fn == "RELU6") {
            os << "  // ReLU6 is clamped to constant 6 (truncated to width)\n";
        }
        os << "  wire signed [" << (data_width - 1) << ":0] x_signed = X;\n";
        os << "  wire [" << (data_width - 1) << ":0] zero_val = {" << data_width << "{1'b0}};\n";
        os << "  wire [" << (data_width - 1) << ":0] one_val = {{(" << (data_width - 1)
           << "){1'b0}}, 1'b1};\n";
        os << "  wire signed [" << (data_width - 1) << ":0] softmax_thr = "
           << data_width << "'sd31;\n";
        os << "  wire [" << (data_width - 1) << ":0] softmax_sat = "
           << data_width << "'d127;\n";
        os << "  wire [" << (data_width - 1) << ":0] softmax_pos = (x_signed > softmax_thr) ? softmax_sat : (X << 2);\n";
        os << "  wire [" << (data_width - 1) << ":0] softmax_val = x_signed[" << (data_width - 1)
           << "] ? zero_val : softmax_pos;\n";
        os << "  wire [" << ((2 * data_width) - 1) << ":0] dsoftmax_num = softmax_val * (softmax_sat - softmax_val);\n";
        if (fn == "RELU6") {
            os << "  wire [" << (data_width - 1) << ":0] six_val = " << data_width
               << "'d6;\n";
            os << "  wire [" << (data_width - 1) << ":0] relu = x_signed[" << (data_width - 1)
               << "] ? zero_val : X;\n";
            os << "  assign Y = (relu > six_val) ? six_val : relu;\n";
        } else if (fn == "LEAKY_RELU") {
            os << "  wire [" << (data_width - 1) << ":0] neg_scaled = (x_signed * "
               << config.alpha_num << ") / " << config.alpha_den << ";\n";
            os << "  assign Y = x_signed[" << (data_width - 1)
               << "] ? neg_scaled : X;\n";
        } else if (fn == "TANH") {
            // Clamp to +/- (2^(w-1)-1)
            os << "  wire [" << (data_width - 1) << ":0] max_val = {1'b0, {" << (data_width - 1)
               << "{1'b1}}};\n";
            os << "  assign Y = x_signed[" << (data_width - 1)
               << "] ? (~max_val + 1'b1) : max_val;\n";
        } else if (fn == "GELU") {
            os << "  // Approximate GELU: 0.5 * ReLU(x)\n";
            os << "  wire [" << (data_width - 1) << ":0] relu = x_signed[" << (data_width - 1)
               << "] ? zero_val : X;\n";
            os << "  assign Y = relu >> 1;\n";
        } else if (fn == "SOFTMAX") {
            os << "  // Approximate SOFTMAX: rectified and scaled into [0, 127]\n";
            os << "  assign Y = softmax_val;\n";
        } else if (fn == "LAYERNORM") {
            os << "  // Scalar placeholder for layernorm: scale down by 2\n";
            os << "  assign Y = x_signed >>> 1;\n";
        } else if (fn == "DRELU") {
            os << "  assign Y = (x_signed > 0) ? one_val : zero_val;\n";
        } else if (fn == "DGELU") {
            os << "  assign Y = (x_signed > 0) ? one_val : zero_val;\n";
        } else if (fn == "DSOFTMAX") {
            os << "  // Approximate dsoftmax from softmax_val: p*(1-p)\n";
            os << "  assign Y = dsoftmax_num >> " << (data_width - 1) << ";\n";
        } else if (fn == "DLAYERNORM") {
            os << "  assign Y = one_val;\n";
        } else if (fn == "PWL") {
            int frac_bits = config.frac_bits > 0 ? config.frac_bits : data_width / 2;
            // Build segments from explicit points if provided, otherwise from breakpoints/slopes.
            std::vector<double> xs = config.xs;
            std::vector<double> ys = config.ys;
            if (!xs.empty() && xs.size() == ys.size()) {
                // Use provided points
            } else if (!config.breakpoints.empty() && !config.slopes.empty()) {
                xs.push_back(0.0);
                ys.push_back(0.0);
                double acc = 0.0;
                double prev_bp = 0.0;
                for (std::size_t i = 0; i < config.breakpoints.size(); ++i) {
                    double bp = config.breakpoints[i];
                    double m = (i < config.slopes.size()) ? config.slopes[i] : config.slopes.back();
                    acc += m * (bp - prev_bp);
                    xs.push_back(bp);
                    ys.push_back(acc);
                    prev_bp = bp;
                }
            } else {
                throw std::runtime_error("PWL activation requires points or breakpoints/slopes");
            }
            int segs = static_cast<int>(xs.size()) - 1;
            os << "  // PWL from user-specified points (" << segs << " segments), symmetric=" << (config.symmetric ? 1 : 0) << "\n";
            if (config.symmetric) {
                os << "  wire [" << (data_width - 1) << ":0] abs_x = x_signed[" << (data_width - 1)
                   << "] ? (~X + 1'b1) : X;\n";
                os << "  reg [" << (data_width - 1) << ":0] y_abs;\n";
                os << "  always @* begin\n";
                os << "    y_abs = 0;\n";
                for (int i = 0; i < segs; ++i) {
                    double x0 = xs[i];
                    double x1 = xs[i + 1];
                    double y0 = ys[i];
                    double y1 = ys[i + 1];
                    double m = (y1 - y0) / (x1 - x0);
                    double c = y0 - m * x0;
                    long long x0f = static_cast<long long>(std::llround(x0 * (1LL << frac_bits)));
                    long long x1f = static_cast<long long>(std::llround(x1 * (1LL << frac_bits)));
                    long long mf = static_cast<long long>(std::llround(m * (1LL << frac_bits)));
                    long long cf = static_cast<long long>(std::llround(c * (1LL << frac_bits)));
                    os << "    " << (i == 0 ? "if" : "else if") << " (abs_x >= " << x0f << " && abs_x < " << x1f << ") y_abs = ((" << mf << " * abs_x) >> "
                       << frac_bits << ") + " << cf << ";\n";
                }
                if (config.clamp) {
                    long long high_sat = static_cast<long long>(std::llround(ys.back() * (1LL << frac_bits)));
                    os << "    else y_abs = " << high_sat << ";\n";
                }
                os << "  end\n";
                os << "  assign Y = (x_signed[" << (data_width - 1) << "] ? (~y_abs + 1'b1) : y_abs);\n";
            } else {
                os << "  reg signed [" << (data_width - 1) << ":0] y_signed;\n";
                os << "  always @* begin\n";
                os << "    y_signed = 0;\n";
                for (int i = 0; i < segs; ++i) {
                    double x0 = xs[i];
                    double x1 = xs[i + 1];
                    double y0 = ys[i];
                    double y1 = ys[i + 1];
                    double m = (y1 - y0) / (x1 - x0);
                    double c = y0 - m * x0;
                    long long x0f = static_cast<long long>(std::llround(x0 * (1LL << frac_bits)));
                    long long x1f = static_cast<long long>(std::llround(x1 * (1LL << frac_bits)));
                    long long mf = static_cast<long long>(std::llround(m * (1LL << frac_bits)));
                    long long cf = static_cast<long long>(std::llround(c * (1LL << frac_bits)));
                    os << "    " << (i == 0 ? "if" : "else if") << " (x_signed >= " << x0f << " && x_signed < " << x1f << ") y_signed = ((" << mf << " * x_signed) >>> "
                       << frac_bits << ") + " << cf << ";\n";
                }
                if (config.clamp) {
                    long long low_sat = static_cast<long long>(std::llround(ys.front() * (1LL << frac_bits)));
                    long long high_sat = static_cast<long long>(std::llround(ys.back() * (1LL << frac_bits)));
                    os << "    else if (x_signed < "
                       << static_cast<long long>(std::llround(xs.front() * (1LL << frac_bits)))
                       << ") y_signed = " << low_sat << ";\n";
                    os << "    else y_signed = " << high_sat << ";\n";
                }
                os << "  end\n";
                os << "  assign Y = y_signed;\n";
            }
        } else {
            os << "  assign Y = x_signed[" << (data_width - 1)
               << "] ? zero_val : X;\n";
        }
    }

    os << "endmodule\n";
}

void emitSoftmaxRowwiseModule(const SoftmaxRowwiseOperationConfig &config, const OperandDefinition &operand) {
    if (operand.kind != "int") {
        throw std::runtime_error("softmax_rowwise currently supports only integer operands");
    }
    if (operand.bit_width < 2 || operand.bit_width > 24) {
        throw std::runtime_error("softmax_rowwise operand bit_width must be in [2, 24]");
    }
    if (config.impl != "shift_exp" && config.impl != "pwl_exp") {
        throw std::runtime_error("Unsupported softmax_rowwise impl: " + config.impl);
    }
    if (config.normalization_mode != "exact" && config.normalization_mode != "reciprocal_quantized") {
        throw std::runtime_error("Unsupported softmax_rowwise normalization_mode: " + config.normalization_mode);
    }
    if (config.normalization_mode == "reciprocal_quantized" && (config.reciprocal_bits < 1 || config.reciprocal_bits > 24)) {
        throw std::runtime_error("softmax_rowwise reciprocal_bits must be in [1, 24]");
    }
    if (config.reciprocal_lut_bucket_shift < 0 || config.reciprocal_lut_bucket_shift > 12) {
        throw std::runtime_error("softmax_rowwise reciprocal_lut_bucket_shift must be in [0, 12]");
    }
    if (config.row_elems <= 0) {
        throw std::runtime_error("softmax_rowwise row_elems must be positive");
    }
    if (config.max_shift < 0 || config.max_shift > 15) {
        throw std::runtime_error("softmax_rowwise max_shift must be in [0, 15]");
    }
    if (config.input_frac_bits < 0 || config.input_frac_bits > 16) {
        throw std::runtime_error("softmax_rowwise input_frac_bits must be in [0, 16]");
    }
    const int weight_bits = (config.weight_bits == 0) ? operand.bit_width : config.weight_bits;
    if (weight_bits < 2 || weight_bits > 24) {
        throw std::runtime_error("softmax_rowwise weight_bits must be in [2, 24]");
    }
    if (config.accum_bits < 4 || config.accum_bits > 64) {
        throw std::runtime_error("softmax_rowwise accum_bits must be in [4, 64]");
    }
    const long long output_max = (1LL << operand.bit_width) - 1;
    if (config.output_scale <= 0 || config.output_scale > output_max) {
        throw std::runtime_error("softmax_rowwise output_scale exceeds the operand output range");
    }

    const int data_width = operand.bit_width;
    const int row_width = config.row_elems * data_width;
    const bool reciprocal_quantized = config.normalization_mode == "reciprocal_quantized";
    const int reciprocal_bucket_step = reciprocal_quantized ? (1 << config.reciprocal_lut_bucket_shift) : 1;
    const int reciprocal_value_bits = reciprocal_quantized
        ? static_cast<int>(std::ceil(std::log2(static_cast<double>(config.output_scale) * std::ldexp(1.0, config.reciprocal_bits) + 1.0)))
        : data_width;
    const int product_bits = config.accum_bits + reciprocal_value_bits;
    const long long max_weight = (config.impl == "shift_exp") ? (1LL << config.max_shift) : ((1LL << weight_bits) - 1);
    const int max_sum_bits = static_cast<int>(
        std::ceil(std::log2(static_cast<double>(config.row_elems) * static_cast<double>(max_weight) + 1.0))
    );
    if (config.accum_bits < std::max(1, max_sum_bits)) {
        throw std::runtime_error("softmax_rowwise accum_bits is too small for the row_elems/weight envelope");
    }

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  [" << (row_width - 1) << ":0] X,\n";
    os << "  output reg [" << (row_width - 1) << ":0] Y\n";
    os << ");\n\n";
    os << "  // Row-wise normalized integer softmax approximation.\n";
    os << "  // 1) find row max\n";
    os << "  // 2) assign approximation weights from distance to max\n";
    os << "  // 3) normalize weights into unsigned integer outputs\n";
    os << "  localparam integer ROW_ELEMS = " << config.row_elems << ";\n";
    os << "  localparam integer DATA_W = " << data_width << ";\n";
    os << "  localparam integer ACCUM_BITS = " << config.accum_bits << ";\n";
    os << "  localparam integer PRODUCT_BITS = " << product_bits << ";\n";
    os << "  localparam integer MAX_SHIFT = " << config.max_shift << ";\n";
    os << "  localparam integer OUTPUT_SCALE = " << config.output_scale << ";\n\n";
    if (config.impl == "pwl_exp") {
        const int input_scale = 1 << config.input_frac_bits;
        const int x2 = 2 * input_scale;
        const int x4 = 4 * input_scale;
        const int x8 = 8 * input_scale;
        const int weight_scale = (1 << weight_bits) - 1;
        auto scaled_exp = [&](double x) {
            return static_cast<int>(std::llround(std::exp(x) * static_cast<double>(weight_scale)));
        };
        const int y0 = weight_scale;
        const int y2 = scaled_exp(-2.0);
        const int y4 = scaled_exp(-4.0);
        const int y8 = scaled_exp(-8.0);
        os << "  localparam integer INPUT_FRAC_BITS = " << config.input_frac_bits << ";\n";
        os << "  localparam integer WEIGHT_BITS = " << weight_bits << ";\n";
        os << "  localparam integer PWL_X2 = " << x2 << ";\n";
        os << "  localparam integer PWL_X4 = " << x4 << ";\n";
        os << "  localparam integer PWL_X8 = " << x8 << ";\n";
        os << "  localparam integer PWL_Y0 = " << y0 << ";\n";
        os << "  localparam integer PWL_Y2 = " << y2 << ";\n";
        os << "  localparam integer PWL_Y4 = " << y4 << ";\n";
        os << "  localparam integer PWL_Y8 = " << y8 << ";\n\n";
        os << "  function [ACCUM_BITS-1:0] pwl_weight;\n";
        os << "    input integer delta_in;\n";
        os << "    integer clamped_delta;\n";
        os << "    integer seg_x0;\n";
        os << "    integer seg_width;\n";
        os << "    integer y0;\n";
        os << "    integer y1;\n";
        os << "    integer ydiff;\n";
        os << "    reg [63:0] interp_num;\n";
        os << "    begin\n";
        os << "      clamped_delta = delta_in;\n";
        os << "      if (clamped_delta < 0)\n";
        os << "        clamped_delta = 0;\n";
        os << "      if (clamped_delta > PWL_X8) begin\n";
        os << "        pwl_weight = {ACCUM_BITS{1'b0}};\n";
        os << "      end else if (clamped_delta == PWL_X8) begin\n";
        os << "        pwl_weight = PWL_Y8;\n";
        os << "      end else begin\n";
        os << "        if (clamped_delta <= PWL_X2) begin\n";
        os << "          seg_x0 = 0;\n";
        os << "          seg_width = PWL_X2;\n";
        os << "          y0 = PWL_Y0;\n";
        os << "          y1 = PWL_Y2;\n";
        os << "        end else if (clamped_delta <= PWL_X4) begin\n";
        os << "          seg_x0 = PWL_X2;\n";
        os << "          seg_width = PWL_X4 - PWL_X2;\n";
        os << "          y0 = PWL_Y2;\n";
        os << "          y1 = PWL_Y4;\n";
        os << "        end else begin\n";
        os << "          seg_x0 = PWL_X4;\n";
        os << "          seg_width = PWL_X8 - PWL_X4;\n";
        os << "          y0 = PWL_Y4;\n";
        os << "          y1 = PWL_Y8;\n";
        os << "        end\n";
        os << "        ydiff = y0 - y1;\n";
        os << "        interp_num = ((clamped_delta - seg_x0) * ydiff) + (seg_width >> 1);\n";
        os << "        pwl_weight = y0 - (interp_num / seg_width);\n";
        os << "      end\n";
        os << "    end\n";
        os << "  endfunction\n\n";
    }
    if (reciprocal_quantized) {
        const int max_sum = static_cast<int>(config.row_elems * max_weight);
        const int bucket_shift = config.reciprocal_lut_bucket_shift;
        const int max_bucket = (max_sum + reciprocal_bucket_step - 1) >> bucket_shift;
        const long long scale = static_cast<long long>(config.output_scale) << config.reciprocal_bits;
        os << "  localparam integer RECIP_BITS = " << config.reciprocal_bits << ";\n";
        os << "  localparam integer RECIP_VALUE_BITS = " << reciprocal_value_bits << ";\n\n";
        os << "  localparam integer RECIP_BUCKET_SHIFT = " << bucket_shift << ";\n\n";
        os << "  function [RECIP_VALUE_BITS-1:0] recip_lut;\n";
        os << "    input [ACCUM_BITS-1:0] bucket;\n";
        os << "    begin\n";
        os << "      case (bucket)\n";
        os << "        " << config.accum_bits << "'d0: recip_lut = {RECIP_VALUE_BITS{1'b0}};\n";
        for (int bucket = 1; bucket <= max_bucket; ++bucket) {
            const int denom = bucket << bucket_shift;
            const long long recip = (scale + (denom / 2)) / denom;
            os << "        " << config.accum_bits << "'d" << bucket
               << ": recip_lut = " << reciprocal_value_bits << "'d" << recip << ";\n";
        }
        os << "        default: recip_lut = {RECIP_VALUE_BITS{1'b0}};\n";
        os << "      endcase\n";
        os << "    end\n";
        os << "  endfunction\n\n";
    }
    os << "  integer i;\n";
    os << "  integer signed lane_val;\n";
    os << "  integer signed row_max;\n";
    os << "  integer delta;\n";
    os << "  reg [ACCUM_BITS-1:0] weights [0:ROW_ELEMS-1];\n";
    os << "  reg [ACCUM_BITS-1:0] sum_weights;\n";
    os << "  reg [PRODUCT_BITS-1:0] numer;\n";
    os << "  reg [PRODUCT_BITS-1:0] scaled_out;\n";
    if (reciprocal_quantized) {
        os << "  reg [RECIP_VALUE_BITS-1:0] reciprocal;\n";
        os << "  reg [ACCUM_BITS-1:0] reciprocal_bucket;\n";
    }
    os << "  reg [DATA_W-1:0] lane_out;\n\n";
    os << "  always @* begin\n";
    os << "    row_max = -(1 << (DATA_W - 1));\n";
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      lane_val = $signed(X[(i*DATA_W) +: DATA_W]);\n";
    os << "      if (lane_val > row_max)\n";
    os << "        row_max = lane_val;\n";
    os << "    end\n\n";
    os << "    sum_weights = {ACCUM_BITS{1'b0}};\n";
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      lane_val = $signed(X[(i*DATA_W) +: DATA_W]);\n";
    os << "      delta = row_max - lane_val;\n";
    os << "      if (delta < 0)\n";
    os << "        delta = 0;\n";
    if (config.impl == "shift_exp") {
        os << "      if (delta > MAX_SHIFT)\n";
        os << "        delta = MAX_SHIFT;\n";
        os << "      weights[i] = ({{(ACCUM_BITS-1){1'b0}}, 1'b1} << (MAX_SHIFT - delta));\n";
    } else {
        os << "      weights[i] = pwl_weight(delta);\n";
    }
    os << "      sum_weights = sum_weights + weights[i];\n";
    os << "    end\n\n";
    os << "    Y = {ROW_ELEMS*DATA_W{1'b0}};\n";
    if (reciprocal_quantized) {
        if (config.reciprocal_lut_bucket_shift > 0) {
            os << "    reciprocal_bucket = (sum_weights + " << config.accum_bits << "'d" << (reciprocal_bucket_step - 1)
               << ") >> RECIP_BUCKET_SHIFT;\n";
        } else {
            os << "    reciprocal_bucket = sum_weights;\n";
        }
        os << "    reciprocal = recip_lut(reciprocal_bucket);\n";
    }
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    if (reciprocal_quantized) {
        os << "      numer = (weights[i] * reciprocal) + ({{(PRODUCT_BITS-1){1'b0}}, 1'b1} << (RECIP_BITS - 1));\n";
        os << "      scaled_out = numer >> RECIP_BITS;\n";
    } else {
        os << "      numer = (weights[i] * OUTPUT_SCALE) + (sum_weights >> 1);\n";
        os << "      if (sum_weights != 0)\n";
        os << "        scaled_out = numer / sum_weights;\n";
        os << "      else\n";
        os << "        scaled_out = {PRODUCT_BITS{1'b0}};\n";
    }
    os << "      if (scaled_out > OUTPUT_SCALE)\n";
    os << "        lane_out = " << data_width << "'d" << config.output_scale << ";\n";
    os << "      else\n";
    os << "        lane_out = scaled_out[DATA_W-1:0];\n";
    os << "      Y[(i*DATA_W) +: DATA_W] = lane_out;\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitAttentionKvReducerModule(const AttentionKvReducerOperationConfig &config,
                                  const OperandDefinition &operand) {
    const int value_bits = config.value_bits > 0 ? config.value_bits : operand.bit_width;
    if (config.lanes <= 0 || config.lanes > 256) {
        throw std::runtime_error("attention_kv_reducer lanes must be in [1, 256]");
    }
    if (value_bits <= 0 || value_bits > 32) {
        throw std::runtime_error("attention_kv_reducer value_bits must be in [1, 32]");
    }
    if (config.stat_bits <= 0 || config.stat_bits > 64) {
        throw std::runtime_error("attention_kv_reducer stat_bits must be in [1, 64]");
    }
    if (config.partials <= 0 || config.partials > 1024) {
        throw std::runtime_error("attention_kv_reducer partials must be in [1, 1024]");
    }
    if (config.counter_bits <= 0 || config.counter_bits > 64) {
        throw std::runtime_error("attention_kv_reducer counter_bits must be in [1, 64]");
    }

    const int min_accum_bits = value_bits +
        std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.partials))) + 1;
    if (config.accum_bits < min_accum_bits || config.accum_bits > 128) {
        std::ostringstream oss;
        oss << "attention_kv_reducer accum_bits must be in [" << min_accum_bits
            << ", 128] for this value_bits/partials";
        throw std::runtime_error(oss.str());
    }

    const int value_fragment_width = config.lanes * value_bits;
    const int reduced_value_width = config.lanes * config.accum_bits;
    const int stat_fragment_width = 2 * config.stat_bits;
    const std::string signed_kw = config.signed_values ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  clk,\n";
    os << "  input  rst_n,\n";
    os << "  input  partial_valid,\n";
    os << "  output partial_ready,\n";
    os << "  input  partial_last,\n";
    os << "  input  [" << (value_fragment_width - 1) << ":0] value_fragment,\n";
    os << "  input  [" << (stat_fragment_width - 1) << ":0] stat_fragment,\n";
    os << "  output reg reduced_valid,\n";
    os << "  input  reduced_ready,\n";
    os << "  output reg " << signed_kw << "[" << (reduced_value_width - 1)
       << ":0] reduced_value_fragment,\n";
    os << "  output reg [" << (stat_fragment_width - 1) << ":0] reduced_stat_fragment,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_partial_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] completed_group_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] producer_stall_cycles,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] cycle_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] final_completion_cycle\n";
    os << ");\n\n";
    os << "  // Attention/KV cross-tile reducer primitive for clustered decoder exploration.\n";
    os << "  // The first measured contract is exact fixed-width reduction of value lanes and\n";
    os << "  // two per-tile statistic fields; softmax rescaling is modeled above this block.\n";
    os << "  localparam integer LANES = " << config.lanes << ";\n";
    os << "  localparam integer VALUE_W = " << value_bits << ";\n";
    os << "  localparam integer STAT_W = " << config.stat_bits << ";\n";
    os << "  localparam integer ACCUM_W = " << config.accum_bits << ";\n";
    os << "  localparam integer COUNT_W = " << config.counter_bits << ";\n";
    os << "  localparam integer PARTIALS = " << config.partials << ";\n\n";
    os << "  reg " << signed_kw << "[ACCUM_W-1:0] value_accum [0:LANES-1];\n";
    os << "  reg [STAT_W-1:0] stat0_accum;\n";
    os << "  reg [STAT_W-1:0] stat1_accum;\n";
    os << "  reg [COUNT_W-1:0] partial_count_in_group;\n\n";
    os << "  wire close_group = partial_last || (partial_count_in_group == (PARTIALS - 1));\n";
    os << "  assign partial_ready = !reduced_valid || reduced_ready;\n\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "  wire " << signed_kw << "[VALUE_W-1:0] lane_value_" << lane
           << " = value_fragment[(" << lane << "*VALUE_W) +: VALUE_W];\n";
        if (config.signed_values) {
            os << "  wire signed [ACCUM_W-1:0] lane_value_ext_" << lane
               << " = {{(ACCUM_W-VALUE_W){lane_value_" << lane << "[VALUE_W-1]}}, lane_value_"
               << lane << "};\n";
        } else {
            os << "  wire [ACCUM_W-1:0] lane_value_ext_" << lane
               << " = {{(ACCUM_W-VALUE_W){1'b0}}, lane_value_" << lane << "};\n";
        }
        os << "  wire " << signed_kw << "[ACCUM_W-1:0] lane_next_" << lane
           << " = value_accum[" << lane << "] + lane_value_ext_" << lane << ";\n";
    }
    os << "  wire [STAT_W-1:0] stat0_next = stat0_accum + stat_fragment[0 +: STAT_W];\n";
    os << "  wire [STAT_W-1:0] stat1_next = stat1_accum + stat_fragment[STAT_W +: STAT_W];\n\n";
    os << "  integer i;\n";
    os << "  always @(posedge clk or negedge rst_n) begin\n";
    os << "    if (!rst_n) begin\n";
    os << "      reduced_valid <= 1'b0;\n";
    os << "      reduced_value_fragment <= {" << reduced_value_width << "{1'b0}};\n";
    os << "      reduced_stat_fragment <= {" << stat_fragment_width << "{1'b0}};\n";
    os << "      accepted_partial_count <= {COUNT_W{1'b0}};\n";
    os << "      completed_group_count <= {COUNT_W{1'b0}};\n";
    os << "      producer_stall_cycles <= {COUNT_W{1'b0}};\n";
    os << "      cycle_count <= {COUNT_W{1'b0}};\n";
    os << "      final_completion_cycle <= {COUNT_W{1'b0}};\n";
    os << "      partial_count_in_group <= {COUNT_W{1'b0}};\n";
    os << "      stat0_accum <= {STAT_W{1'b0}};\n";
    os << "      stat1_accum <= {STAT_W{1'b0}};\n";
    os << "      for (i = 0; i < LANES; i = i + 1)\n";
    os << "        value_accum[i] <= {ACCUM_W{1'b0}};\n";
    os << "    end else begin\n";
    os << "      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (reduced_valid && reduced_ready)\n";
    os << "        reduced_valid <= 1'b0;\n\n";
    os << "      if (partial_valid && !partial_ready)\n";
    os << "        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (partial_valid && partial_ready) begin\n";
    os << "        accepted_partial_count <= accepted_partial_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "        value_accum[" << lane << "] <= close_group ? {ACCUM_W{1'b0}} : lane_next_"
           << lane << ";\n";
    }
    os << "        stat0_accum <= close_group ? {STAT_W{1'b0}} : stat0_next;\n";
    os << "        stat1_accum <= close_group ? {STAT_W{1'b0}} : stat1_next;\n";
    os << "        if (close_group) begin\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "          reduced_value_fragment[(" << lane << "*ACCUM_W) +: ACCUM_W] <= lane_next_"
           << lane << ";\n";
    }
    os << "          reduced_stat_fragment[0 +: STAT_W] <= stat0_next;\n";
    os << "          reduced_stat_fragment[STAT_W +: STAT_W] <= stat1_next;\n";
    os << "          reduced_valid <= 1'b1;\n";
    os << "          completed_group_count <= completed_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "          partial_count_in_group <= {COUNT_W{1'b0}};\n";
    os << "          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end else begin\n";
    os << "          partial_count_in_group <= partial_count_in_group + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end\n";
    os << "      end\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitAttentionKvReducerTreeModule(const AttentionKvReducerTreeOperationConfig &config,
                                      const OperandDefinition &operand) {
    const int value_bits = config.value_bits > 0 ? config.value_bits : operand.bit_width;
    if (config.lanes <= 0 || config.lanes > 256) {
        throw std::runtime_error("attention_kv_reducer_tree lanes must be in [1, 256]");
    }
    if (value_bits <= 0 || value_bits > 32) {
        throw std::runtime_error("attention_kv_reducer_tree value_bits must be in [1, 32]");
    }
    if (config.stat_bits <= 0 || config.stat_bits > 64) {
        throw std::runtime_error("attention_kv_reducer_tree stat_bits must be in [1, 64]");
    }
    if (config.partials <= 1 || config.partials > 1024 ||
        (config.partials & (config.partials - 1)) != 0) {
        throw std::runtime_error("attention_kv_reducer_tree partials must be a power of two in [2, 1024]");
    }
    if (config.counter_bits <= 0 || config.counter_bits > 64) {
        throw std::runtime_error("attention_kv_reducer_tree counter_bits must be in [1, 64]");
    }

    const int min_accum_bits = value_bits +
        std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.partials))) + 1;
    if (config.accum_bits < min_accum_bits || config.accum_bits > 128) {
        std::ostringstream oss;
        oss << "attention_kv_reducer_tree accum_bits must be in [" << min_accum_bits
            << ", 128] for this value_bits/partials";
        throw std::runtime_error(oss.str());
    }

    const int stages = ceilLog2U64(static_cast<unsigned long long>(config.partials));
    const int input_value_width = config.partials * config.lanes * value_bits;
    const int input_stat_width = config.partials * 2 * config.stat_bits;
    const int reduced_value_width = config.lanes * config.accum_bits;
    const int reduced_stat_width = 2 * config.stat_bits;
    const std::string signed_kw = config.signed_values ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  clk,\n";
    os << "  input  rst_n,\n";
    os << "  input  partial_valid,\n";
    os << "  output partial_ready,\n";
    os << "  input  [" << (input_value_width - 1) << ":0] value_fragments,\n";
    os << "  input  [" << (input_stat_width - 1) << ":0] stat_fragments,\n";
    os << "  output reg reduced_valid,\n";
    os << "  input  reduced_ready,\n";
    os << "  output reg " << signed_kw << "[" << (reduced_value_width - 1)
       << ":0] reduced_value_fragment,\n";
    os << "  output reg [" << (reduced_stat_width - 1) << ":0] reduced_stat_fragment,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_group_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] completed_group_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] producer_stall_cycles,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] cycle_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] final_completion_cycle\n";
    os << ");\n\n";
    os << "  // Registered binary tree reducer for hierarchical clustered attention exploration.\n";
    os << "  // It reduces all partial fragments for one group in parallel through log2(PARTIALS)\n";
    os << "  // registered pairwise stages. Softmax/layernorm math remains outside this block.\n";
    os << "  localparam integer LANES = " << config.lanes << ";\n";
    os << "  localparam integer VALUE_W = " << value_bits << ";\n";
    os << "  localparam integer STAT_W = " << config.stat_bits << ";\n";
    os << "  localparam integer ACCUM_W = " << config.accum_bits << ";\n";
    os << "  localparam integer COUNT_W = " << config.counter_bits << ";\n";
    os << "  localparam integer PARTIALS = " << config.partials << ";\n";
    os << "  localparam integer STAGES = " << stages << ";\n\n";
    os << "  assign partial_ready = !reduced_valid || reduced_ready;\n\n";

    int nodes = config.partials / 2;
    for (int stage = 0; stage < stages; ++stage) {
        for (int node = 0; node < nodes; ++node) {
            for (int lane = 0; lane < config.lanes; ++lane) {
                os << "  reg " << signed_kw << "[ACCUM_W-1:0] stage" << stage
                   << "_node" << node << "_lane" << lane << ";\n";
            }
            os << "  reg [STAT_W-1:0] stage" << stage << "_node" << node << "_stat0;\n";
            os << "  reg [STAT_W-1:0] stage" << stage << "_node" << node << "_stat1;\n";
        }
        nodes /= 2;
    }
    os << "  reg [STAGES-1:0] valid_pipe;\n";
    os << "  wire advance = !reduced_valid || reduced_ready;\n\n";

    for (int partial = 0; partial < config.partials; ++partial) {
        for (int lane = 0; lane < config.lanes; ++lane) {
            const int base = (partial * config.lanes + lane) * value_bits;
            os << "  wire " << signed_kw << "[VALUE_W-1:0] partial" << partial
               << "_lane" << lane << " = value_fragments[" << base << " +: VALUE_W];\n";
            if (config.signed_values) {
                os << "  wire signed [ACCUM_W-1:0] partial" << partial << "_lane" << lane
                   << "_ext = {{(ACCUM_W-VALUE_W){partial" << partial << "_lane" << lane
                   << "[VALUE_W-1]}}, partial" << partial << "_lane" << lane << "};\n";
            } else {
                os << "  wire [ACCUM_W-1:0] partial" << partial << "_lane" << lane
                   << "_ext = {{(ACCUM_W-VALUE_W){1'b0}}, partial" << partial
                   << "_lane" << lane << "};\n";
            }
        }
        os << "  wire [STAT_W-1:0] partial" << partial << "_stat0 = stat_fragments["
           << (partial * 2 * config.stat_bits) << " +: STAT_W];\n";
        os << "  wire [STAT_W-1:0] partial" << partial << "_stat1 = stat_fragments["
           << ((partial * 2 + 1) * config.stat_bits) << " +: STAT_W];\n";
    }
    os << "\n";

    os << "  always @(posedge clk or negedge rst_n) begin\n";
    os << "    if (!rst_n) begin\n";
    os << "      reduced_valid <= 1'b0;\n";
    os << "      reduced_value_fragment <= {" << reduced_value_width << "{1'b0}};\n";
    os << "      reduced_stat_fragment <= {" << reduced_stat_width << "{1'b0}};\n";
    os << "      accepted_group_count <= {COUNT_W{1'b0}};\n";
    os << "      completed_group_count <= {COUNT_W{1'b0}};\n";
    os << "      producer_stall_cycles <= {COUNT_W{1'b0}};\n";
    os << "      cycle_count <= {COUNT_W{1'b0}};\n";
    os << "      final_completion_cycle <= {COUNT_W{1'b0}};\n";
    os << "      valid_pipe <= {STAGES{1'b0}};\n";
    nodes = config.partials / 2;
    for (int stage = 0; stage < stages; ++stage) {
        for (int node = 0; node < nodes; ++node) {
            for (int lane = 0; lane < config.lanes; ++lane) {
                os << "      stage" << stage << "_node" << node << "_lane" << lane
                   << " <= {ACCUM_W{1'b0}};\n";
            }
            os << "      stage" << stage << "_node" << node << "_stat0 <= {STAT_W{1'b0}};\n";
            os << "      stage" << stage << "_node" << node << "_stat1 <= {STAT_W{1'b0}};\n";
        }
        nodes /= 2;
    }
    os << "    end else begin\n";
    os << "      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "      if (partial_valid && !partial_ready)\n";
    os << "        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "      if (advance) begin\n";
    if (stages == 1) {
        os << "        valid_pipe <= partial_valid;\n";
    } else {
        os << "        valid_pipe <= {valid_pipe[STAGES-2:0], partial_valid};\n";
    }
    os << "        reduced_valid <= valid_pipe[STAGES-1];\n";
    os << "        if (partial_valid)\n";
    os << "          accepted_group_count <= accepted_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        if (valid_pipe[STAGES-1]) begin\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "          reduced_value_fragment[(" << lane << "*ACCUM_W) +: ACCUM_W] <= stage"
           << (stages - 1) << "_node0_lane" << lane << ";\n";
    }
    os << "          reduced_stat_fragment[0 +: STAT_W] <= stage" << (stages - 1)
       << "_node0_stat0;\n";
    os << "          reduced_stat_fragment[STAT_W +: STAT_W] <= stage" << (stages - 1)
       << "_node0_stat1;\n";
    os << "          completed_group_count <= completed_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end\n";

    for (int node = 0; node < config.partials / 2; ++node) {
        const int lhs = 2 * node;
        const int rhs = lhs + 1;
        for (int lane = 0; lane < config.lanes; ++lane) {
            os << "        stage0_node" << node << "_lane" << lane << " <= partial"
               << lhs << "_lane" << lane << "_ext + partial" << rhs << "_lane"
               << lane << "_ext;\n";
        }
        os << "        stage0_node" << node << "_stat0 <= partial" << lhs
           << "_stat0 + partial" << rhs << "_stat0;\n";
        os << "        stage0_node" << node << "_stat1 <= partial" << lhs
           << "_stat1 + partial" << rhs << "_stat1;\n";
    }
    int prev_nodes = config.partials / 2;
    for (int stage = 1; stage < stages; ++stage) {
        const int curr_nodes = prev_nodes / 2;
        for (int node = 0; node < curr_nodes; ++node) {
            const int lhs = 2 * node;
            const int rhs = lhs + 1;
            for (int lane = 0; lane < config.lanes; ++lane) {
                os << "        stage" << stage << "_node" << node << "_lane" << lane
                   << " <= stage" << (stage - 1) << "_node" << lhs << "_lane" << lane
                   << " + stage" << (stage - 1) << "_node" << rhs << "_lane" << lane
                   << ";\n";
            }
            os << "        stage" << stage << "_node" << node << "_stat0 <= stage"
               << (stage - 1) << "_node" << lhs << "_stat0 + stage" << (stage - 1)
               << "_node" << rhs << "_stat0;\n";
            os << "        stage" << stage << "_node" << node << "_stat1 <= stage"
               << (stage - 1) << "_node" << lhs << "_stat1 + stage" << (stage - 1)
               << "_node" << rhs << "_stat1;\n";
        }
        prev_nodes = curr_nodes;
    }
    os << "      end\n";
    os << "    end\n";
    os << "  end\n\n";
    os << "endmodule\n";
}

void emitAttentionKvReducerFoldedModule(const AttentionKvReducerFoldedOperationConfig &config,
                                        const OperandDefinition &operand) {
    const int value_bits = config.value_bits > 0 ? config.value_bits : operand.bit_width;
    if (config.lanes <= 0 || config.lanes > 256) {
        throw std::runtime_error("attention_kv_reducer_folded lanes must be in [1, 256]");
    }
    if (value_bits <= 0 || value_bits > 32) {
        throw std::runtime_error("attention_kv_reducer_folded value_bits must be in [1, 32]");
    }
    if (config.stat_bits <= 0 || config.stat_bits > 64) {
        throw std::runtime_error("attention_kv_reducer_folded stat_bits must be in [1, 64]");
    }
    if (config.partials <= 1 || config.partials > 1024) {
        throw std::runtime_error("attention_kv_reducer_folded partials must be in [2, 1024]");
    }
    if (config.partials_per_cycle <= 0 || config.partials_per_cycle > config.partials ||
        config.partials % config.partials_per_cycle != 0) {
        throw std::runtime_error("attention_kv_reducer_folded partials_per_cycle must divide partials");
    }
    if (config.counter_bits <= 0 || config.counter_bits > 64) {
        throw std::runtime_error("attention_kv_reducer_folded counter_bits must be in [1, 64]");
    }

    const int min_accum_bits = value_bits +
        std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.partials))) + 1;
    if (config.accum_bits < min_accum_bits || config.accum_bits > 128) {
        std::ostringstream oss;
        oss << "attention_kv_reducer_folded accum_bits must be in [" << min_accum_bits
            << ", 128] for this value_bits/partials";
        throw std::runtime_error(oss.str());
    }

    const int chunks = config.partials / config.partials_per_cycle;
    const int input_value_width = config.partials_per_cycle * config.lanes * value_bits;
    const int input_stat_width = config.partials_per_cycle * 2 * config.stat_bits;
    const int reduced_value_width = config.lanes * config.accum_bits;
    const int reduced_stat_width = 2 * config.stat_bits;
    const std::string signed_kw = config.signed_values ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  clk,\n";
    os << "  input  rst_n,\n";
    os << "  input  partial_valid,\n";
    os << "  output partial_ready,\n";
    os << "  input  [" << (input_value_width - 1) << ":0] value_fragments,\n";
    os << "  input  [" << (input_stat_width - 1) << ":0] stat_fragments,\n";
    os << "  output reg reduced_valid,\n";
    os << "  input  reduced_ready,\n";
    os << "  output reg " << signed_kw << "[" << (reduced_value_width - 1)
       << ":0] reduced_value_fragment,\n";
    os << "  output reg [" << (reduced_stat_width - 1) << ":0] reduced_stat_fragment,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_chunk_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] completed_group_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] producer_stall_cycles,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] cycle_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] final_completion_cycle\n";
    os << ");\n\n";
    os << "  // Folded attention/KV reducer for macro-friendly clustered attention exploration.\n";
    os << "  // It accepts PARTIALS_PER_CYCLE partial fragments per cycle, reducing the top-level\n";
    os << "  // bus width relative to the full tree while preserving exact grouped sums.\n";
    os << "  localparam integer LANES = " << config.lanes << ";\n";
    os << "  localparam integer VALUE_W = " << value_bits << ";\n";
    os << "  localparam integer STAT_W = " << config.stat_bits << ";\n";
    os << "  localparam integer ACCUM_W = " << config.accum_bits << ";\n";
    os << "  localparam integer COUNT_W = " << config.counter_bits << ";\n";
    os << "  localparam integer PARTIALS = " << config.partials << ";\n";
    os << "  localparam integer PARTIALS_PER_CYCLE = " << config.partials_per_cycle << ";\n";
    os << "  localparam integer CHUNKS_PER_GROUP = " << chunks << ";\n\n";
    os << "  reg " << signed_kw << "[ACCUM_W-1:0] value_accum [0:LANES-1];\n";
    os << "  reg [STAT_W-1:0] stat0_accum;\n";
    os << "  reg [STAT_W-1:0] stat1_accum;\n";
    os << "  reg [COUNT_W-1:0] chunk_count_in_group;\n\n";
    os << "  wire close_group = (chunk_count_in_group == (CHUNKS_PER_GROUP - 1));\n";
    os << "  assign partial_ready = !reduced_valid || reduced_ready;\n\n";

    for (int partial = 0; partial < config.partials_per_cycle; ++partial) {
        for (int lane = 0; lane < config.lanes; ++lane) {
            const int base = (partial * config.lanes + lane) * value_bits;
            os << "  wire " << signed_kw << "[VALUE_W-1:0] chunk" << partial
               << "_lane" << lane << " = value_fragments[" << base << " +: VALUE_W];\n";
            if (config.signed_values) {
                os << "  wire signed [ACCUM_W-1:0] chunk" << partial << "_lane" << lane
                   << "_ext = {{(ACCUM_W-VALUE_W){chunk" << partial << "_lane" << lane
                   << "[VALUE_W-1]}}, chunk" << partial << "_lane" << lane << "};\n";
            } else {
                os << "  wire [ACCUM_W-1:0] chunk" << partial << "_lane" << lane
                   << "_ext = {{(ACCUM_W-VALUE_W){1'b0}}, chunk" << partial
                   << "_lane" << lane << "};\n";
            }
        }
        os << "  wire [STAT_W-1:0] chunk" << partial << "_stat0 = stat_fragments["
           << (partial * 2 * config.stat_bits) << " +: STAT_W];\n";
        os << "  wire [STAT_W-1:0] chunk" << partial << "_stat1 = stat_fragments["
           << ((partial * 2 + 1) * config.stat_bits) << " +: STAT_W];\n";
    }
    os << "\n";

    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "  wire " << signed_kw << "[ACCUM_W-1:0] lane_chunk_sum_" << lane << " = ";
        for (int partial = 0; partial < config.partials_per_cycle; ++partial) {
            if (partial > 0) {
                os << " + ";
            }
            os << "chunk" << partial << "_lane" << lane << "_ext";
        }
        os << ";\n";
        os << "  wire " << signed_kw << "[ACCUM_W-1:0] lane_next_" << lane
           << " = value_accum[" << lane << "] + lane_chunk_sum_" << lane << ";\n";
    }
    os << "  wire [STAT_W-1:0] stat0_chunk_sum = ";
    for (int partial = 0; partial < config.partials_per_cycle; ++partial) {
        if (partial > 0) {
            os << " + ";
        }
        os << "chunk" << partial << "_stat0";
    }
    os << ";\n";
    os << "  wire [STAT_W-1:0] stat1_chunk_sum = ";
    for (int partial = 0; partial < config.partials_per_cycle; ++partial) {
        if (partial > 0) {
            os << " + ";
        }
        os << "chunk" << partial << "_stat1";
    }
    os << ";\n";
    os << "  wire [STAT_W-1:0] stat0_next = stat0_accum + stat0_chunk_sum;\n";
    os << "  wire [STAT_W-1:0] stat1_next = stat1_accum + stat1_chunk_sum;\n\n";

    os << "  integer i;\n";
    os << "  always @(posedge clk or negedge rst_n) begin\n";
    os << "    if (!rst_n) begin\n";
    os << "      reduced_valid <= 1'b0;\n";
    os << "      reduced_value_fragment <= {" << reduced_value_width << "{1'b0}};\n";
    os << "      reduced_stat_fragment <= {" << reduced_stat_width << "{1'b0}};\n";
    os << "      accepted_chunk_count <= {COUNT_W{1'b0}};\n";
    os << "      completed_group_count <= {COUNT_W{1'b0}};\n";
    os << "      producer_stall_cycles <= {COUNT_W{1'b0}};\n";
    os << "      cycle_count <= {COUNT_W{1'b0}};\n";
    os << "      final_completion_cycle <= {COUNT_W{1'b0}};\n";
    os << "      chunk_count_in_group <= {COUNT_W{1'b0}};\n";
    os << "      stat0_accum <= {STAT_W{1'b0}};\n";
    os << "      stat1_accum <= {STAT_W{1'b0}};\n";
    os << "      for (i = 0; i < LANES; i = i + 1)\n";
    os << "        value_accum[i] <= {ACCUM_W{1'b0}};\n";
    os << "    end else begin\n";
    os << "      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (reduced_valid && reduced_ready)\n";
    os << "        reduced_valid <= 1'b0;\n\n";
    os << "      if (partial_valid && !partial_ready)\n";
    os << "        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (partial_valid && partial_ready) begin\n";
    os << "        accepted_chunk_count <= accepted_chunk_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "        value_accum[" << lane << "] <= close_group ? {ACCUM_W{1'b0}} : lane_next_"
           << lane << ";\n";
    }
    os << "        stat0_accum <= close_group ? {STAT_W{1'b0}} : stat0_next;\n";
    os << "        stat1_accum <= close_group ? {STAT_W{1'b0}} : stat1_next;\n";
    os << "        if (close_group) begin\n";
    for (int lane = 0; lane < config.lanes; ++lane) {
        os << "          reduced_value_fragment[(" << lane << "*ACCUM_W) +: ACCUM_W] <= lane_next_"
           << lane << ";\n";
    }
    os << "          reduced_stat_fragment[0 +: STAT_W] <= stat0_next;\n";
    os << "          reduced_stat_fragment[STAT_W +: STAT_W] <= stat1_next;\n";
    os << "          reduced_valid <= 1'b1;\n";
    os << "          completed_group_count <= completed_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "          chunk_count_in_group <= {COUNT_W{1'b0}};\n";
    os << "          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end else begin\n";
    os << "          chunk_count_in_group <= chunk_count_in_group + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end\n";
    os << "      end\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitBf16RecipNormModule(const Bf16RecipNormOperationConfig &config, const OperandDefinition &operand) {
    if (operand.bit_width != 16) {
        throw std::runtime_error("bf16_recip_norm expects a 16-bit packed bf16 operand");
    }
    if (operand.kind == "fp" && (!operand.fp_format.has_value() ||
                                 operand.fp_format->total_width != 16 ||
                                 operand.fp_format->mantissa_width != 7)) {
        throw std::runtime_error("bf16_recip_norm fp operands must use bf16 {total_width=16, mantissa_width=7}");
    }
    if (config.row_elems <= 0 || config.row_elems > 1024) {
        throw std::runtime_error("bf16_recip_norm row_elems must be in [1, 1024]");
    }
    if (config.q_frac_bits < 4 || config.q_frac_bits > 20) {
        throw std::runtime_error("bf16_recip_norm q_frac_bits must be in [4, 20]");
    }
    if (config.sum_bits < 8 || config.sum_bits > 64) {
        throw std::runtime_error("bf16_recip_norm sum_bits must be in [8, 64]");
    }
    if (config.reciprocal_bits < 4 || config.reciprocal_bits > 24) {
        throw std::runtime_error("bf16_recip_norm reciprocal_bits must be in [4, 24]");
    }
    if (config.reciprocal_lut_bucket_shift < 0 || config.reciprocal_lut_bucket_shift > 12) {
        throw std::runtime_error("bf16_recip_norm reciprocal_lut_bucket_shift must be in [0, 12]");
    }

    const int data_width = 16;
    const int row_width = config.row_elems * data_width;
    const unsigned long long q_one = 1ULL << config.q_frac_bits;
    const unsigned long long max_sum = static_cast<unsigned long long>(config.row_elems) * q_one;
    const unsigned long long bucket_step = 1ULL << config.reciprocal_lut_bucket_shift;
    const unsigned long long max_bucket = (max_sum + bucket_step - 1ULL) / bucket_step;
    if (max_sum >= (1ULL << std::min(config.sum_bits, 63))) {
        throw std::runtime_error("bf16_recip_norm sum_bits is too small for row_elems/q_frac_bits envelope");
    }
    if (max_bucket > 16384ULL) {
        throw std::runtime_error("bf16_recip_norm reciprocal LUT exceeds 16384 entries; increase reciprocal_lut_bucket_shift");
    }
    const int reciprocal_value_bits = config.reciprocal_bits + config.q_frac_bits + 1;
    const int product_bits = config.sum_bits + reciprocal_value_bits;
    const unsigned long long reciprocal_scale = 1ULL << (config.reciprocal_bits + config.q_frac_bits);

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  [" << (row_width - 1) << ":0] X,\n";
    os << "  output reg [" << (row_width - 1) << ":0] Y\n";
    os << ");\n\n";
    os << "  // Packed-bf16 row normalization proxy.\n";
    os << "  // Positive bf16 lanes are converted to fixed-point, summed, multiplied by\n";
    os << "  // a bucketed reciprocal, and converted back to bf16. Subnormals, negative\n";
    os << "  // inputs, NaNs, and infinities are clamped for an L1 datapath cost proxy.\n";
    os << "  localparam integer ROW_ELEMS = " << config.row_elems << ";\n";
    os << "  localparam integer DATA_W = 16;\n";
    os << "  localparam integer Q_FRAC_BITS = " << config.q_frac_bits << ";\n";
    os << "  localparam integer SUM_BITS = " << config.sum_bits << ";\n";
    os << "  localparam integer RECIP_BITS = " << config.reciprocal_bits << ";\n";
    os << "  localparam integer RECIP_VALUE_BITS = " << reciprocal_value_bits << ";\n";
    os << "  localparam integer RECIP_BUCKET_SHIFT = " << config.reciprocal_lut_bucket_shift << ";\n";
    os << "  localparam integer PRODUCT_BITS = " << product_bits << ";\n";
    os << "  localparam [SUM_BITS-1:0] Q_ONE = " << config.sum_bits << "'d" << q_one << ";\n\n";

    os << "  function [SUM_BITS-1:0] bf16_to_q;\n";
    os << "    input [15:0] x;\n";
    os << "    integer exp_unbiased;\n";
    os << "    integer shift;\n";
    os << "    reg [7:0] mant;\n";
    os << "    reg [SUM_BITS+8:0] raw;\n";
    os << "    begin\n";
    os << "      raw = {SUM_BITS+9{1'b0}};\n";
    os << "      if (x[15] || x[14:7] == 8'd0) begin\n";
    os << "        bf16_to_q = {SUM_BITS{1'b0}};\n";
    os << "      end else if (x[14:7] > 8'd127) begin\n";
    os << "        bf16_to_q = Q_ONE;\n";
    os << "      end else begin\n";
    os << "        mant = {1'b1, x[6:0]};\n";
    os << "        exp_unbiased = x[14:7] - 127;\n";
    os << "        shift = Q_FRAC_BITS + exp_unbiased - 7;\n";
    os << "        if (shift >= 0)\n";
    os << "          raw = {{(SUM_BITS+1){1'b0}}, mant} << shift;\n";
    os << "        else\n";
    os << "          raw = {{(SUM_BITS+1){1'b0}}, mant} >> (-shift);\n";
    os << "        if (raw > Q_ONE)\n";
    os << "          bf16_to_q = Q_ONE;\n";
    os << "        else\n";
    os << "          bf16_to_q = raw[SUM_BITS-1:0];\n";
    os << "      end\n";
    os << "    end\n";
    os << "  endfunction\n\n";

    os << "  function [15:0] q_to_bf16;\n";
    os << "    input [SUM_BITS-1:0] q;\n";
    os << "    integer msb;\n";
    os << "    integer k;\n";
    os << "    integer exp_val;\n";
    os << "    reg [7:0] exp_bits;\n";
    os << "    reg [7:0] sig;\n";
    os << "    reg [SUM_BITS-1:0] norm;\n";
    os << "    begin\n";
    os << "      if (q == {SUM_BITS{1'b0}}) begin\n";
    os << "        q_to_bf16 = 16'h0000;\n";
    os << "      end else begin\n";
    os << "        msb = 0;\n";
    os << "        for (k = 0; k < SUM_BITS; k = k + 1) begin\n";
    os << "          if (q[k]) msb = k;\n";
    os << "        end\n";
    os << "        exp_val = 127 + msb - Q_FRAC_BITS;\n";
    os << "        if (exp_val <= 0) begin\n";
    os << "          q_to_bf16 = 16'h0000;\n";
    os << "        end else if (exp_val >= 255) begin\n";
    os << "          q_to_bf16 = 16'h7f7f;\n";
    os << "        end else begin\n";
    os << "          if (msb >= 7)\n";
    os << "            norm = q >> (msb - 7);\n";
    os << "          else\n";
    os << "            norm = q << (7 - msb);\n";
    os << "          exp_bits = exp_val;\n";
    os << "          sig = norm[7:0];\n";
    os << "          q_to_bf16 = {1'b0, exp_bits, sig[6:0]};\n";
    os << "        end\n";
    os << "      end\n";
    os << "    end\n";
    os << "  endfunction\n\n";

    os << "  function [RECIP_VALUE_BITS-1:0] recip_lut;\n";
    os << "    input [SUM_BITS-1:0] bucket;\n";
    os << "    begin\n";
    os << "      case (bucket)\n";
    os << "        " << config.sum_bits << "'d0: recip_lut = {RECIP_VALUE_BITS{1'b0}};\n";
    for (unsigned long long bucket = 1; bucket <= max_bucket; ++bucket) {
        const unsigned long long denom = bucket * bucket_step;
        const unsigned long long recip = (reciprocal_scale + (denom / 2ULL)) / denom;
        os << "        " << config.sum_bits << "'d" << bucket
           << ": recip_lut = " << reciprocal_value_bits << "'d" << recip << ";\n";
    }
    os << "        default: recip_lut = {RECIP_VALUE_BITS{1'b0}};\n";
    os << "      endcase\n";
    os << "    end\n";
    os << "  endfunction\n\n";

    os << "  integer i;\n";
    os << "  reg [SUM_BITS-1:0] q_values [0:ROW_ELEMS-1];\n";
    os << "  reg [SUM_BITS-1:0] sum_values;\n";
    os << "  reg [SUM_BITS-1:0] reciprocal_bucket;\n";
    os << "  reg [RECIP_VALUE_BITS-1:0] reciprocal;\n";
    os << "  reg [PRODUCT_BITS-1:0] product;\n";
    os << "  reg [PRODUCT_BITS-1:0] rounded_product;\n";
    os << "  reg [SUM_BITS-1:0] norm_q;\n\n";

    os << "  always @* begin\n";
    os << "    sum_values = {SUM_BITS{1'b0}};\n";
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      q_values[i] = bf16_to_q(X[(i*DATA_W) +: DATA_W]);\n";
    os << "      sum_values = sum_values + q_values[i];\n";
    os << "    end\n\n";
    os << "    Y = {ROW_ELEMS*DATA_W{1'b0}};\n";
    if (config.reciprocal_lut_bucket_shift > 0) {
        os << "    reciprocal_bucket = (sum_values + " << config.sum_bits << "'d" << (bucket_step - 1ULL)
           << ") >> RECIP_BUCKET_SHIFT;\n";
    } else {
        os << "    reciprocal_bucket = sum_values;\n";
    }
    os << "    reciprocal = recip_lut(reciprocal_bucket);\n\n";
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      product = q_values[i] * reciprocal;\n";
    os << "      rounded_product = product + ({{(PRODUCT_BITS-1){1'b0}}, 1'b1} << (RECIP_BITS - 1));\n";
    os << "      norm_q = rounded_product >> RECIP_BITS;\n";
    os << "      if (norm_q > Q_ONE)\n";
    os << "        norm_q = Q_ONE;\n";
    os << "      Y[(i*DATA_W) +: DATA_W] = q_to_bf16(norm_q);\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitScoreTieRankModule(const ScoreTieRankOperationConfig &config, const OperandDefinition &operand) {
    const int score_bits = config.score_bits > 0 ? config.score_bits : operand.bit_width;
    if (score_bits <= 0 || score_bits > 64) {
        throw std::runtime_error("score_tie_rank score_bits must be in [1, 64]");
    }
    if (config.row_elems <= 0 || config.row_elems > 1024) {
        throw std::runtime_error("score_tie_rank row_elems must be in [1, 1024]");
    }
    if (config.logit_bits <= 0 || config.logit_bits > 64) {
        throw std::runtime_error("score_tie_rank logit_bits must be in [1, 64]");
    }

    const int index_bits = std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.row_elems)));
    const int score_row_width = config.row_elems * score_bits;
    const int logit_row_width = config.row_elems * config.logit_bits;
    const std::string signed_kw = config.logit_signed ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  [" << (score_row_width - 1) << ":0] scores,\n";
    os << "  input  " << signed_kw << "[" << (logit_row_width - 1) << ":0] logits,\n";
    os << "  output reg [" << (index_bits - 1) << ":0] best_index,\n";
    os << "  output reg [" << (score_bits - 1) << ":0] best_score,\n";
    os << "  output reg " << signed_kw << "[" << (config.logit_bits - 1) << ":0] best_logit\n";
    os << ");\n\n";
    os << "  // Row-wise rank selection for quantized decoder scores.\n";
    os << "  // Primary key: larger score. Tie-break key: larger pre-quantized logit.\n";
    os << "  // Exact ties retain the lowest lane index for deterministic ranking.\n";
    os << "  localparam integer ROW_ELEMS = " << config.row_elems << ";\n";
    os << "  localparam integer SCORE_W = " << score_bits << ";\n";
    os << "  localparam integer LOGIT_W = " << config.logit_bits << ";\n";
    os << "  localparam integer INDEX_W = " << index_bits << ";\n\n";
    os << "  integer i;\n";
    os << "  reg [SCORE_W-1:0] score_i;\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] logit_i;\n\n";
    os << "  always @* begin\n";
    os << "    best_index = {INDEX_W{1'b0}};\n";
    os << "    best_score = scores[0 +: SCORE_W];\n";
    if (config.logit_signed) {
        os << "    best_logit = $signed(logits[0 +: LOGIT_W]);\n";
    } else {
        os << "    best_logit = logits[0 +: LOGIT_W];\n";
    }
    os << "    for (i = 1; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      score_i = scores[(i*SCORE_W) +: SCORE_W];\n";
    if (config.logit_signed) {
        os << "      logit_i = $signed(logits[(i*LOGIT_W) +: LOGIT_W]);\n";
    } else {
        os << "      logit_i = logits[(i*LOGIT_W) +: LOGIT_W];\n";
    }
    os << "      if ((score_i > best_score) || ((score_i == best_score) && (logit_i > best_logit))) begin\n";
    os << "        best_index = i;\n";
    os << "        best_score = score_i;\n";
    os << "        best_logit = logit_i;\n";
    os << "      end\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitLogitRankModule(const LogitRankOperationConfig &config, const OperandDefinition &operand) {
    const int logit_bits = config.logit_bits > 0 ? config.logit_bits : operand.bit_width;
    if (logit_bits <= 0 || logit_bits > 64) {
        throw std::runtime_error("logit_rank logit_bits must be in [1, 64]");
    }
    if (config.row_elems <= 0 || config.row_elems > 1024) {
        throw std::runtime_error("logit_rank row_elems must be in [1, 1024]");
    }
    if (config.top_k <= 0 || config.top_k > config.row_elems) {
        throw std::runtime_error("logit_rank top_k must be in [1, row_elems]");
    }

    const int index_bits = std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.row_elems)));
    const int logit_row_width = config.row_elems * logit_bits;
    const int top_index_width = config.top_k * index_bits;
    const int top_logit_width = config.top_k * logit_bits;
    const std::string signed_kw = config.logit_signed ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  " << signed_kw << "[" << (logit_row_width - 1) << ":0] logits,\n";
    os << "  output reg [" << (top_index_width - 1) << ":0] top_indices,\n";
    os << "  output reg " << signed_kw << "[" << (top_logit_width - 1) << ":0] top_logits\n";
    os << ");\n\n";
    os << "  // Row-wise logit-only rank selection.\n";
    os << "  // Primary key: larger logit. Exact ties retain the lowest lane index.\n";
    os << "  localparam integer ROW_ELEMS = " << config.row_elems << ";\n";
    os << "  localparam integer LOGIT_W = " << logit_bits << ";\n";
    os << "  localparam integer TOP_K = " << config.top_k << ";\n";
    os << "  localparam integer INDEX_W = " << index_bits << ";\n\n";
    os << "  integer i;\n";
    os << "  integer k;\n";
    os << "  integer insert_pos;\n";
    os << "  reg [TOP_K-1:0] top_valid;\n";
    os << "  reg [INDEX_W-1:0] lane_index;\n";
    os << "  reg [INDEX_W-1:0] top_index_k;\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] logit_i;\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] top_logit_k;\n\n";
    os << "  always @* begin\n";
    os << "    top_indices = {" << top_index_width << "{1'b0}};\n";
    os << "    top_logits = {" << top_logit_width << "{1'b0}};\n";
    os << "    top_valid = {TOP_K{1'b0}};\n\n";
    os << "    for (i = 0; i < ROW_ELEMS; i = i + 1) begin\n";
    os << "      lane_index = i;\n";
    if (config.logit_signed) {
        os << "      logit_i = $signed(logits[(i*LOGIT_W) +: LOGIT_W]);\n";
    } else {
        os << "      logit_i = logits[(i*LOGIT_W) +: LOGIT_W];\n";
    }
    os << "      insert_pos = TOP_K;\n";
    os << "      for (k = 0; k < TOP_K; k = k + 1) begin\n";
    os << "        top_index_k = top_indices[(k*INDEX_W) +: INDEX_W];\n";
    if (config.logit_signed) {
        os << "        top_logit_k = $signed(top_logits[(k*LOGIT_W) +: LOGIT_W]);\n";
    } else {
        os << "        top_logit_k = top_logits[(k*LOGIT_W) +: LOGIT_W];\n";
    }
    os << "        if ((insert_pos == TOP_K) && (!top_valid[k] || (logit_i > top_logit_k) || ((logit_i == top_logit_k) && (lane_index < top_index_k))))\n";
    os << "          insert_pos = k;\n";
    os << "      end\n\n";
    os << "      if (insert_pos < TOP_K) begin\n";
    os << "        for (k = TOP_K - 1; k > 0; k = k - 1) begin\n";
    os << "          if (k > insert_pos) begin\n";
    os << "            top_indices[(k*INDEX_W) +: INDEX_W] = top_indices[((k-1)*INDEX_W) +: INDEX_W];\n";
    os << "            top_logits[(k*LOGIT_W) +: LOGIT_W] = top_logits[((k-1)*LOGIT_W) +: LOGIT_W];\n";
    os << "            top_valid[k] = top_valid[k-1];\n";
    os << "          end\n";
    os << "        end\n";
    os << "        top_indices[(insert_pos*INDEX_W) +: INDEX_W] = lane_index;\n";
    os << "        top_logits[(insert_pos*LOGIT_W) +: LOGIT_W] = logit_i;\n";
    os << "        top_valid[insert_pos] = 1'b1;\n";
    os << "      end\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitCandidateStreamMergeFifoModule(const CandidateStreamMergeFifoOperationConfig &config,
                                        const OperandDefinition &operand) {
    const int logit_bits = config.logit_bits > 0 ? config.logit_bits : operand.bit_width;
    if (config.top_k <= 0 || config.top_k > 16) {
        throw std::runtime_error("candidate_stream_merge_fifo top_k must be in [1, 16]");
    }
    if (logit_bits <= 0 || logit_bits > 64) {
        throw std::runtime_error("candidate_stream_merge_fifo logit_bits must be in [1, 64]");
    }
    if (config.token_id_bits <= 0 || config.token_id_bits > 32) {
        throw std::runtime_error("candidate_stream_merge_fifo token_id_bits must be in [1, 32]");
    }
    if (config.fifo_depth_groups <= 0 || config.fifo_depth_groups > 4096) {
        throw std::runtime_error("candidate_stream_merge_fifo fifo_depth_groups must be in [1, 4096]");
    }
    if (config.counter_bits <= 0 || config.counter_bits > 64) {
        throw std::runtime_error("candidate_stream_merge_fifo counter_bits must be in [1, 64]");
    }

    const int ptr_bits = std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.fifo_depth_groups)));
    const int token_row_width = config.top_k * config.token_id_bits;
    const int logit_row_width = config.top_k * logit_bits;
    const std::string signed_kw = config.logit_signed ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  clk,\n";
    os << "  input  rst_n,\n";
    os << "  input  in_valid,\n";
    os << "  output in_ready,\n";
    os << "  input  in_last,\n";
    os << "  input  [" << (config.top_k - 1) << ":0] in_valid_mask,\n";
    os << "  input  [" << (token_row_width - 1) << ":0] in_token_ids,\n";
    os << "  input  " << signed_kw << "[" << (logit_row_width - 1) << ":0] in_logits,\n";
    os << "  output reg out_valid,\n";
    os << "  input  out_ready,\n";
    os << "  output reg [" << (config.top_k - 1) << ":0] out_valid_mask,\n";
    os << "  output reg [" << (token_row_width - 1) << ":0] out_token_ids,\n";
    os << "  output reg " << signed_kw << "[" << (logit_row_width - 1) << ":0] out_logits,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_group_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] producer_stall_cycles,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] fifo_max_occupancy,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] final_completion_cycle\n";
    os << ");\n\n";
    os << "  // CandidateStream ready-valid merger for decoder logit-rank streaming.\n";
    os << "  // Ordering contract: larger logit wins; exact ties keep the lower token id.\n";
    os << "  // Observable counters match the perf-sim/RTL equivalence contract.\n";
    os << "  localparam integer TOP_K = " << config.top_k << ";\n";
    os << "  localparam integer LOGIT_W = " << logit_bits << ";\n";
    os << "  localparam integer TOKEN_ID_W = " << config.token_id_bits << ";\n";
    os << "  localparam integer FIFO_DEPTH = " << config.fifo_depth_groups << ";\n";
    os << "  localparam integer PTR_W = " << ptr_bits << ";\n";
    os << "  localparam integer COUNT_W = " << config.counter_bits << ";\n\n";
    os << "  localparam [COUNT_W-1:0] FIFO_DEPTH_COUNT = " << config.counter_bits << "'d" << config.fifo_depth_groups << ";\n";
    os << "  localparam [PTR_W-1:0] FIFO_LAST_PTR = " << ptr_bits << "'d" << (config.fifo_depth_groups - 1) << ";\n\n";
    os << "  reg fifo_last [0:FIFO_DEPTH-1];\n";
    os << "  reg [TOP_K-1:0] fifo_mask [0:FIFO_DEPTH-1];\n";
    os << "  reg [TOP_K*TOKEN_ID_W-1:0] fifo_token_ids [0:FIFO_DEPTH-1];\n";
    os << "  reg " << signed_kw << "[TOP_K*LOGIT_W-1:0] fifo_logits [0:FIFO_DEPTH-1];\n";
    os << "  reg [PTR_W-1:0] rd_ptr;\n";
    os << "  reg [PTR_W-1:0] wr_ptr;\n";
    os << "  reg [COUNT_W-1:0] occupancy;\n";
    os << "  reg [COUNT_W-1:0] cycle_count;\n\n";
    os << "  reg [TOP_K-1:0] top_valid;\n";
    os << "  reg [TOKEN_ID_W-1:0] top_token [0:TOP_K-1];\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] top_logit [0:TOP_K-1];\n";
    os << "  reg [TOP_K-1:0] work_valid;\n";
    os << "  reg [TOKEN_ID_W-1:0] work_token [0:TOP_K-1];\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] work_logit [0:TOP_K-1];\n";
    os << "  reg [TOP_K-1:0] read_mask;\n";
    os << "  reg [TOP_K*TOKEN_ID_W-1:0] read_token_ids;\n";
    os << "  reg " << signed_kw << "[TOP_K*LOGIT_W-1:0] read_logits;\n";
    os << "  reg read_last;\n";
    os << "  reg [TOKEN_ID_W-1:0] cand_token;\n";
    os << "  reg " << signed_kw << "[LOGIT_W-1:0] cand_logit;\n";
    os << "  integer i;\n";
    os << "  integer k;\n";
    os << "  integer insert_pos;\n";
    os << "  integer pop_group;\n";
    os << "  integer push_group;\n\n";
    os << "  assign in_ready = (occupancy < FIFO_DEPTH_COUNT);\n\n";
    os << "  always @(posedge clk or negedge rst_n) begin\n";
    os << "    if (!rst_n) begin\n";
    os << "      rd_ptr <= {PTR_W{1'b0}};\n";
    os << "      wr_ptr <= {PTR_W{1'b0}};\n";
    os << "      occupancy <= {COUNT_W{1'b0}};\n";
    os << "      cycle_count <= {COUNT_W{1'b0}};\n";
    os << "      accepted_group_count <= {COUNT_W{1'b0}};\n";
    os << "      producer_stall_cycles <= {COUNT_W{1'b0}};\n";
    os << "      fifo_max_occupancy <= {COUNT_W{1'b0}};\n";
    os << "      final_completion_cycle <= {COUNT_W{1'b0}};\n";
    os << "      out_valid <= 1'b0;\n";
    os << "      out_valid_mask <= {TOP_K{1'b0}};\n";
    os << "      out_token_ids <= {TOP_K*TOKEN_ID_W{1'b0}};\n";
    os << "      out_logits <= {TOP_K*LOGIT_W{1'b0}};\n";
    os << "      top_valid <= {TOP_K{1'b0}};\n";
    os << "      for (i = 0; i < TOP_K; i = i + 1) begin\n";
    os << "        top_token[i] <= {TOKEN_ID_W{1'b0}};\n";
    os << "        top_logit[i] <= {LOGIT_W{1'b0}};\n";
    os << "      end\n";
    os << "    end else begin\n";
    os << "      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "      push_group = in_valid && in_ready;\n";
    os << "      pop_group = (occupancy != {COUNT_W{1'b0}}) && !out_valid;\n\n";
    os << "      if (in_valid && !in_ready)\n";
    os << "        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (out_valid && out_ready) begin\n";
    os << "        out_valid <= 1'b0;\n";
    os << "        top_valid <= {TOP_K{1'b0}};\n";
    os << "      end\n\n";
    os << "      if (push_group) begin\n";
    os << "        fifo_last[wr_ptr] <= in_last;\n";
    os << "        fifo_mask[wr_ptr] <= in_valid_mask;\n";
    os << "        fifo_token_ids[wr_ptr] <= in_token_ids;\n";
    os << "        fifo_logits[wr_ptr] <= in_logits;\n";
    os << "        accepted_group_count <= accepted_group_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        if (wr_ptr == FIFO_LAST_PTR)\n";
    os << "          wr_ptr <= {PTR_W{1'b0}};\n";
    os << "        else\n";
    os << "          wr_ptr <= wr_ptr + {{(PTR_W-1){1'b0}}, 1'b1};\n";
    os << "      end\n\n";
    os << "      if (pop_group) begin\n";
    os << "        read_last = fifo_last[rd_ptr];\n";
    os << "        read_mask = fifo_mask[rd_ptr];\n";
    os << "        read_token_ids = fifo_token_ids[rd_ptr];\n";
    os << "        read_logits = fifo_logits[rd_ptr];\n";
    os << "        work_valid = top_valid;\n";
    os << "        for (i = 0; i < TOP_K; i = i + 1) begin\n";
    os << "          work_token[i] = top_token[i];\n";
    os << "          work_logit[i] = top_logit[i];\n";
    os << "        end\n\n";
    os << "        for (i = 0; i < TOP_K; i = i + 1) begin\n";
    os << "          if (read_mask[i]) begin\n";
    os << "            cand_token = read_token_ids[(i*TOKEN_ID_W) +: TOKEN_ID_W];\n";
    if (config.logit_signed) {
        os << "            cand_logit = $signed(read_logits[(i*LOGIT_W) +: LOGIT_W]);\n";
    } else {
        os << "            cand_logit = read_logits[(i*LOGIT_W) +: LOGIT_W];\n";
    }
    os << "            insert_pos = TOP_K;\n";
    os << "            for (k = 0; k < TOP_K; k = k + 1) begin\n";
    os << "              if ((insert_pos == TOP_K) && (!work_valid[k] || (cand_logit > work_logit[k]) || ((cand_logit == work_logit[k]) && (cand_token < work_token[k]))))\n";
    os << "                insert_pos = k;\n";
    os << "            end\n";
    os << "            if (insert_pos < TOP_K) begin\n";
    os << "              for (k = TOP_K - 1; k > 0; k = k - 1) begin\n";
    os << "                if (k > insert_pos) begin\n";
    os << "                  work_valid[k] = work_valid[k-1];\n";
    os << "                  work_token[k] = work_token[k-1];\n";
    os << "                  work_logit[k] = work_logit[k-1];\n";
    os << "                end\n";
    os << "              end\n";
    os << "              work_valid[insert_pos] = 1'b1;\n";
    os << "              work_token[insert_pos] = cand_token;\n";
    os << "              work_logit[insert_pos] = cand_logit;\n";
    os << "            end\n";
    os << "          end\n";
    os << "        end\n\n";
    os << "        top_valid <= work_valid;\n";
    os << "        for (i = 0; i < TOP_K; i = i + 1) begin\n";
    os << "          top_token[i] <= work_token[i];\n";
    os << "          top_logit[i] <= work_logit[i];\n";
    os << "        end\n";
    os << "        if (read_last) begin\n";
    os << "          out_valid <= 1'b1;\n";
    os << "          out_valid_mask <= work_valid;\n";
    os << "          for (i = 0; i < TOP_K; i = i + 1) begin\n";
    os << "            out_token_ids[(i*TOKEN_ID_W) +: TOKEN_ID_W] <= work_token[i];\n";
    os << "            out_logits[(i*LOGIT_W) +: LOGIT_W] <= work_logit[i];\n";
    os << "          end\n";
    os << "          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end\n";
    os << "        if (rd_ptr == FIFO_LAST_PTR)\n";
    os << "          rd_ptr <= {PTR_W{1'b0}};\n";
    os << "        else\n";
    os << "          rd_ptr <= rd_ptr + {{(PTR_W-1){1'b0}}, 1'b1};\n";
    os << "      end\n\n";
    os << "      if (push_group && !pop_group)\n";
    os << "        occupancy <= occupancy + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "      else if (!push_group && pop_group)\n";
    os << "        occupancy <= occupancy - {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if ((occupancy + (push_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}}) - (pop_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}})) > fifo_max_occupancy)\n";
    os << "        fifo_max_occupancy <= occupancy + (push_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}}) - (pop_group ? {{(COUNT_W-1){1'b0}}, 1'b1} : {COUNT_W{1'b0}});\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}

void emitAttentionKvTileModule(const AttentionKvTileOperationConfig &config,
                               const OperandDefinition &operand) {
    const int data_bits = config.kv_bits > 0 ? config.kv_bits : operand.bit_width;
    if (config.head_dim <= 0 || config.head_dim > 4096) {
        throw std::runtime_error("attention_kv_tile head_dim must be in [1, 4096]");
    }
    if (data_bits <= 0 || data_bits > 32) {
        throw std::runtime_error("attention_kv_tile kv_bits must be in [1, 32]");
    }
    if (config.lanes <= 0 || config.lanes > 256 || config.lanes > config.head_dim) {
        throw std::runtime_error("attention_kv_tile lanes must be in [1, min(256, head_dim)]");
    }
    if (config.stream_bytes_per_cycle <= 0 || config.stream_bytes_per_cycle > 4096) {
        throw std::runtime_error("attention_kv_tile stream_bytes_per_cycle must be in [1, 4096]");
    }
    if (config.counter_bits <= 0 || config.counter_bits > 64) {
        throw std::runtime_error("attention_kv_tile counter_bits must be in [1, 64]");
    }
    if (config.stream_bytes_per_cycle * 8 < config.lanes * data_bits * 2) {
        throw std::runtime_error("attention_kv_tile stream_bytes_per_cycle cannot carry query+key lane payload");
    }

    const int product_width = 2 * data_bits;
    const int min_accum_bits = product_width +
        std::max(1, ceilLog2U64(static_cast<unsigned long long>(config.head_dim))) + 1;
    if (config.accum_bits < min_accum_bits || config.accum_bits > 128) {
        std::ostringstream oss;
        oss << "attention_kv_tile accum_bits must be in [" << min_accum_bits
            << ", 128] for this head_dim/kv_bits";
        throw std::runtime_error(oss.str());
    }

    const int fragment_width = config.lanes * data_bits;
    const int expected_tiles = (config.head_dim + config.lanes - 1) / config.lanes;
    const std::string signed_kw = config.signed_inputs ? "signed " : "";

    std::string filename = config.module_name + ".v";
    std::ofstream os(filename);
    if (!os) {
        throw std::runtime_error("Failed to open " + filename + " for writing");
    }

    os << "`timescale 1ns/1ps\n\n";
    os << "module " << config.module_name << "(\n";
    os << "  input  clk,\n";
    os << "  input  rst_n,\n";
    os << "  input  tile_valid,\n";
    os << "  output tile_ready,\n";
    os << "  input  tile_last,\n";
    os << "  input  [" << (fragment_width - 1) << ":0] query_fragment,\n";
    os << "  input  [" << (fragment_width - 1) << ":0] key_fragment,\n";
    os << "  output reg score_valid,\n";
    os << "  input  score_ready,\n";
    os << "  output reg " << signed_kw << "[" << (config.accum_bits - 1) << ":0] score,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_tile_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] accepted_byte_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] producer_stall_cycles,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] cycle_count,\n";
    os << "  output reg [" << (config.counter_bits - 1) << ":0] final_completion_cycle\n";
    os << ");\n\n";
    os << "  // Attention/KV tile stream primitive for single-token decoder exploration.\n";
    os << "  // Each accepted tile consumes LANES query/key pairs, accumulates their dot product,\n";
    os << "  // and emits one score when tile_last closes the head fragment stream.\n";
    os << "  localparam integer HEAD_DIM = " << config.head_dim << ";\n";
    os << "  localparam integer DATA_W = " << data_bits << ";\n";
    os << "  localparam integer LANES = " << config.lanes << ";\n";
    os << "  localparam integer PRODUCT_W = " << product_width << ";\n";
    os << "  localparam integer ACCUM_W = " << config.accum_bits << ";\n";
    os << "  localparam integer COUNT_W = " << config.counter_bits << ";\n";
    os << "  localparam integer EXPECTED_TILES = " << expected_tiles << ";\n";
    os << "  localparam [COUNT_W-1:0] STREAM_BYTES_PER_TILE = "
       << config.counter_bits << "'d" << config.stream_bytes_per_cycle << ";\n\n";
    os << "  reg " << signed_kw << "[ACCUM_W-1:0] running_sum;\n";
    os << "  reg [COUNT_W-1:0] tile_count_in_score;\n";
    std::vector<std::string> lane_terms;
    lane_terms.reserve(static_cast<std::size_t>(config.lanes));
    for (int lane = 0; lane < config.lanes; ++lane) {
        const std::string product_name = "lane_product_" + std::to_string(lane);
        const std::string term_name = "lane_term_" + std::to_string(lane);
        os << "  wire " << signed_kw << "[PRODUCT_W-1:0] " << product_name << " = ";
        if (config.signed_inputs) {
            os << "$signed(query_fragment[(" << lane << "*DATA_W) +: DATA_W]) * "
               << "$signed(key_fragment[(" << lane << "*DATA_W) +: DATA_W]);\n";
            os << "  wire signed [ACCUM_W-1:0] " << term_name
               << " = {{(ACCUM_W-PRODUCT_W){" << product_name << "[PRODUCT_W-1]}}, "
               << product_name << "};\n";
        } else {
            os << "query_fragment[(" << lane << "*DATA_W) +: DATA_W] * "
               << "key_fragment[(" << lane << "*DATA_W) +: DATA_W];\n";
            os << "  wire [ACCUM_W-1:0] " << term_name
               << " = {{(ACCUM_W-PRODUCT_W){1'b0}}, " << product_name << "};\n";
        }
        lane_terms.push_back(term_name);
    }
    const std::string partial_expr = emitSumChain(os, lane_terms, "partial_sum_chain",
                                                  config.signed_inputs, config.accum_bits);
    os << "  wire " << signed_kw << "[ACCUM_W-1:0] partial_sum = " << partial_expr << ";\n\n";
    os << "  assign tile_ready = !score_valid || score_ready;\n\n";
    os << "  always @(posedge clk or negedge rst_n) begin\n";
    os << "    if (!rst_n) begin\n";
    os << "      running_sum <= {ACCUM_W{1'b0}};\n";
    os << "      score <= {ACCUM_W{1'b0}};\n";
    os << "      score_valid <= 1'b0;\n";
    os << "      accepted_tile_count <= {COUNT_W{1'b0}};\n";
    os << "      accepted_byte_count <= {COUNT_W{1'b0}};\n";
    os << "      producer_stall_cycles <= {COUNT_W{1'b0}};\n";
    os << "      cycle_count <= {COUNT_W{1'b0}};\n";
    os << "      final_completion_cycle <= {COUNT_W{1'b0}};\n";
    os << "      tile_count_in_score <= {COUNT_W{1'b0}};\n";
    os << "    end else begin\n";
    os << "      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (score_valid && score_ready)\n";
    os << "        score_valid <= 1'b0;\n\n";
    os << "      if (tile_valid && !tile_ready)\n";
    os << "        producer_stall_cycles <= producer_stall_cycles + {{(COUNT_W-1){1'b0}}, 1'b1};\n\n";
    os << "      if (tile_valid && tile_ready) begin\n";
    os << "        accepted_tile_count <= accepted_tile_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        accepted_byte_count <= accepted_byte_count + STREAM_BYTES_PER_TILE;\n";
    os << "        if (tile_last) begin\n";
    os << "          score <= running_sum + partial_sum;\n";
    os << "          score_valid <= 1'b1;\n";
    os << "          running_sum <= {ACCUM_W{1'b0}};\n";
    os << "          tile_count_in_score <= {COUNT_W{1'b0}};\n";
    os << "          final_completion_cycle <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end else begin\n";
    os << "          running_sum <= running_sum + partial_sum;\n";
    os << "          tile_count_in_score <= tile_count_in_score + {{(COUNT_W-1){1'b0}}, 1'b1};\n";
    os << "        end\n";
    os << "      end\n";
    os << "    end\n";
    os << "  end\n";
    os << "endmodule\n";
}
