#include "rtl_operations.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
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
    if (fn != "RELU" && fn != "RELU6" && fn != "LEAKY_RELU" && fn != "TANH" && fn != "GELU") {
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
            // PWL-ish tanh: if |x| >= clamp_exp -> +/-1, if |x| >= bias (>=1.0) scale by 0.5, else pass through
            int clamp_exp = 0x82; // ~|x| >= 8
            int bias = (1 << (exp_w - 1)) - 1; // 127 for fp32
            os << "  wire [" << (data_width - 3) << ":0] abs_payload = sign ? (~payload + 1'b1) : payload;\n";
            os << "  wire clamp_hi = is_normal && (exp_bits >= " << clamp_exp << ");\n";
            os << "  wire mid = is_normal && (exp_bits >= " << bias << ") && (exp_bits < " << clamp_exp << ");\n";
            os << "  wire [" << (exp_w - 1) << ":0] exp_scaled = exp_bits - 1'b1;\n";
            os << "  wire [" << (data_width - 1) << ":0] one_val = {2'b01, sign, " << exp_w << "'d" << bias << ", " << frac_w << "'b0};\n";
            os << "  wire [" << (data_width - 1) << ":0] mid_val = {2'b01, sign, exp_scaled, frac_bits};\n";
            os << "  wire [" << (data_width - 1) << ":0] pass_val = {2'b01, sign, exp_bits, frac_bits};\n";
            os << "  assign Y = clamp_hi ? one_val : (mid ? mid_val : pass_val);\n";
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
        } else {
            os << "  assign Y = x_signed[" << (data_width - 1)
               << "] ? zero_val : X;\n";
        }
    }

    os << "endmodule\n";
}
