#include "cmvm.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>

#include "ortools/linear_solver/linear_solver.h"

namespace cse {
namespace {

constexpr long long kMaxShiftLimit = 60;

std::string uppercase(std::string value) {
    for (char &ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

struct PairData {
    PairKey key;
    PairUsage usage;
};

std::vector<std::pair<int, int>> decomposeCoefficient(long long value) {
    std::vector<std::pair<int, int>> digits;
    if (value == 0) {
        return digits;
    }
    long long n = std::llabs(value);
    int sign = value >= 0 ? 1 : -1;
    int shift = 0;
    while (n != 0) {
        if (n & 1LL) {
            long long remainder = n & 3LL;
            int digit = 0;
            if (remainder == 1) {
                digit = 1;
                n -= 1;
            } else { // remainder 3
                digit = -1;
                n += 1;
            }
            digits.emplace_back(shift, digit * sign);
        }
        n >>= 1LL;
        ++shift;
    }
    return digits;
}

std::map<PairKey, PairUsage> computePairUsage(const std::vector<Expression> &expressions) {
    std::map<PairKey, PairUsage> result;
    for (size_t idx = 0; idx < expressions.size(); ++idx) {
        const auto hist = expressions[idx].histogram();
        if (hist.size() < 2) {
            continue;
        }
        std::vector<TermType> terms;
        terms.reserve(hist.size());
        for (const auto &entry : hist) {
            if (entry.second > 0) {
                terms.push_back(entry.first);
            }
        }
        if (terms.size() < 2) {
            continue;
        }
        for (size_t i = 0; i < terms.size(); ++i) {
            for (size_t j = i + 1; j < terms.size(); ++j) {
                PairKey key(terms[i], terms[j]);
                auto &usage = result[key];
                ++usage.usage;
                usage.expressions.push_back(static_cast<int>(idx));
            }
        }
    }
    return result;
}

std::vector<long long> subtractVectors(const std::vector<long long> &lhs,
                                       const std::vector<long long> &rhs) {
    std::vector<long long> diff(lhs.size(), 0);
    for (size_t i = 0; i < lhs.size(); ++i) {
        diff[i] = lhs[i] - rhs[i];
    }
    return diff;
}

Expression buildExpressionFromCoeffs(const std::vector<long long> &coeffs, SignalTable &table,
                                     int outputIndex) {
    Expression expr(outputIndex);
    for (size_t input = 0; input < coeffs.size(); ++input) {
        long long coeff = coeffs[input];
        if (coeff == 0) {
            continue;
        }
        auto digits = decomposeCoefficient(coeff);
        for (const auto &[shift, sign] : digits) {
            if (shift > kMaxShiftLimit) {
                continue;
            }
            table.updateMaxShift(shift);
            int signalId = table.ensureBaseSignal(static_cast<int>(input), shift);
            expr.addTerm(signalId, sign >= 0 ? 1 : -1);
        }
    }
    return expr;
}

bool applyPairToExpressions(const PairKey &key, const std::vector<int> &exprIndices,
                            ProblemContext &ctx) {
    int signalId = ctx.table.createCompositeSignal(key.a, key.b);
    bool applied = false;
    for (int idx : exprIndices) {
        if (idx < 0 || idx >= static_cast<int>(ctx.expressions.size())) {
            continue;
        }
        Expression &expr = ctx.expressions[idx];
        bool removedA = expr.removeTerm(key.a);
        bool removedB = expr.removeTerm(key.b);
        if (removedA && removedB) {
            expr.addTerm(signalId, 1);
            applied = true;
        }
    }
    return applied;
}

Expression subtractExpression(const Expression &lhs, const Expression &rhs, SignalTable &table) {
    auto lhsVec = lhs.coefficients(table);
    auto rhsVec = rhs.coefficients(table);
    auto diff = subtractVectors(lhsVec, rhsVec);
    return buildExpressionFromCoeffs(diff, table, lhs.outputIndex());
}

ProblemContext cloneContext(const ProblemContext &ctx) {
    ProblemContext copy(ctx.table.numInputs(), ctx.table.bitWidth());
    copy.table = ctx.table;
    copy.expressions = ctx.expressions;
    return copy;
}

CmvmSynthesisOutcome runH2mcWithContext(ProblemContext ctx, const std::string &label,
                                        int maxPairSearch) {
    int subexprCount = 0;
    while (true) {
        auto usageMap = computePairUsage(ctx.expressions);
        std::vector<std::pair<PairKey, PairUsage>> candidates(usageMap.begin(), usageMap.end());
        std::sort(candidates.begin(), candidates.end(),
                  [](const auto &lhs, const auto &rhs) { return lhs.second.usage > rhs.second.usage; });
        if (maxPairSearch > 0 && static_cast<int>(candidates.size()) > maxPairSearch) {
            candidates.resize(maxPairSearch);
        }
        PairKey bestKey;
        PairUsage bestUsage;
        int bestGain = 0;
        bool found = false;
        for (const auto &entry : candidates) {
            if (entry.second.usage < 2) {
                continue;
            }
            int gain = entry.second.usage - 1;
            if (gain > bestGain) {
                bestGain = gain;
                bestKey = entry.first;
                bestUsage = entry.second;
                found = true;
            }
        }
        if (!found) {
            break;
        }
        if (applyPairToExpressions(bestKey, bestUsage.expressions, ctx)) {
            ++subexprCount;
        } else {
            break;
        }
    }
    int totalOps = subexprCount + computeNaiveCost(ctx.expressions);
    AlgorithmResult result;
    result.name = label;
    result.subexpressionCount = subexprCount;
    result.totalOperations = totalOps;
    return {result, std::move(ctx), {}};
}

CmvmSynthesisOutcome runHCmvmWithContext(const ProblemContext &base,
                                         const CmvmSynthesisOptions &options) {
    ProblemContext ctx = cloneContext(base);
    std::vector<DifferenceRelation> relations;
    if (options.differenceRows) {
        bool improved = true;
        while (improved) {
            improved = false;
            int bestGain = 0;
            int bestI = -1;
            int bestJ = -1;
            Expression bestExpr;
            for (size_t i = 0; i < ctx.expressions.size(); ++i) {
                for (size_t j = 0; j < ctx.expressions.size(); ++j) {
                    if (i == j) {
                        continue;
                    }
                    Expression diff =
                        subtractExpression(ctx.expressions[i], ctx.expressions[j], ctx.table);
                    int gain = ctx.expressions[i].termCount() - (diff.termCount() + 1);
                    if (gain > bestGain) {
                        bestGain = gain;
                        bestI = static_cast<int>(i);
                        bestJ = static_cast<int>(j);
                        bestExpr = diff;
                    }
                }
            }
            if (bestGain > 0 && bestI >= 0 && bestJ >= 0) {
                ctx.expressions[bestI] = bestExpr;
                relations.push_back({bestI, bestJ});
                improved = true;
            }
        }
    }
    auto result = runH2mcWithContext(std::move(ctx), "H_CMVM", options.maxPairSearch);
    result.stats.totalOperations += static_cast<int>(relations.size());
    if (!relations.empty()) {
        result.stats.notes = "includes " + std::to_string(relations.size()) + " recombinations";
    }
    result.relations = relations;
    return result;
}

CmvmSynthesisOutcome runExactIlpWithContext(const ProblemContext &base) {
    using operations_research::MPConstraint;
    using operations_research::MPObjective;
    using operations_research::MPVariable;
    using operations_research::MPSolver;

    auto usageMap = computePairUsage(base.expressions);
    std::map<PairKey, PairUsage> filtered;
    for (const auto &entry : usageMap) {
        if (entry.second.usage >= 2) {
            filtered.emplace(entry.first, entry.second);
        }
    }
    AlgorithmResult fallback;
    fallback.name = "Exact_ILP";
    fallback.subexpressionCount = 0;
    fallback.totalOperations = computeNaiveCost(base.expressions);
    fallback.optimal = false;
    if (filtered.empty()) {
        fallback.notes = "no viable pairs";
        return {fallback, cloneContext(base), {}};
    }

    MPSolver solver("cse_ilp", MPSolver::CBC_MIXED_INTEGER_PROGRAMMING);

    std::map<int, std::map<TermType, MPConstraint *>> termConstraints;
    std::vector<std::map<TermType, int>> histograms(base.expressions.size());
    for (size_t i = 0; i < base.expressions.size(); ++i) {
        histograms[i] = base.expressions[i].histogram();
        for (const auto &entry : histograms[i]) {
            MPConstraint *constraint = solver.MakeRowConstraint(0.0, entry.second);
            termConstraints[static_cast<int>(i)][entry.first] = constraint;
        }
    }

    std::map<PairKey, MPVariable *> pairVars;
    std::map<PairKey, std::vector<std::pair<int, MPVariable *>>> usageByPair;

    for (const auto &entry : filtered) {
        const PairKey &key = entry.first;
        std::ostringstream xName;
        xName << "x_" << key.a.signal << "_" << key.b.signal;
        MPVariable *xVar = solver.MakeBoolVar(xName.str());
        pairVars[key] = xVar;
        for (int exprIdx : entry.second.expressions) {
            const auto &hist = histograms[exprIdx];
            auto itA = hist.find(key.a);
            auto itB = hist.find(key.b);
            if (itA == hist.end() || itB == hist.end()) {
                continue;
            }
            std::ostringstream yName;
            yName << "y_" << exprIdx << "_" << key.a.signal << "_" << key.b.signal;
            MPVariable *yVar = solver.MakeBoolVar(yName.str());
            usageByPair[key].push_back({exprIdx, yVar});
            termConstraints[exprIdx][key.a]->SetCoefficient(yVar, 1.0);
            termConstraints[exprIdx][key.b]->SetCoefficient(yVar, 1.0);
            MPConstraint *link = solver.MakeRowConstraint(-solver.infinity(), 0.0);
            link->SetCoefficient(yVar, 1.0);
            link->SetCoefficient(xVar, -1.0);
        }
    }

    if (pairVars.empty() || usageByPair.empty()) {
        fallback.notes = "insufficient structure";
        return {fallback, cloneContext(base), {}};
    }

    MPObjective *objective = solver.MutableObjective();
    for (const auto &entry : usageByPair) {
        for (const auto &usage : entry.second) {
            objective->SetCoefficient(usage.second, 1.0);
        }
    }
    for (const auto &entry : pairVars) {
        objective->SetCoefficient(entry.second, -1.0);
    }
    objective->SetMaximization();

    const auto status = solver.Solve();
    if (status != MPSolver::OPTIMAL && status != MPSolver::FEASIBLE) {
        fallback.notes = "solver failed";
        return {fallback, cloneContext(base), {}};
    }

    ProblemContext ctx = cloneContext(base);
    int subexprCount = 0;
    for (const auto &entry : pairVars) {
        if (entry.second->solution_value() < 0.5) {
            continue;
        }
        std::vector<int> exprList;
        auto usageIt = usageByPair.find(entry.first);
        if (usageIt != usageByPair.end()) {
            for (const auto &use : usageIt->second) {
                if (use.second->solution_value() >= 0.5) {
                    exprList.push_back(use.first);
                }
            }
        }
        if (!exprList.empty()) {
            if (applyPairToExpressions(entry.first, exprList, ctx)) {
                ++subexprCount;
            }
        }
    }

    AlgorithmResult result;
    result.name = "Exact_ILP";
    result.subexpressionCount = subexprCount;
    result.totalOperations = subexprCount + computeNaiveCost(ctx.expressions);
    result.optimal = (status == MPSolver::OPTIMAL);
    if (!result.optimal) {
        result.notes = "feasible (not proven optimal)";
    }
    return {result, std::move(ctx), {}};
}

} // namespace

int computeNaiveCost(const std::vector<Expression> &expressions) {
    int total = 0;
    for (const auto &expr : expressions) {
        int terms = expr.termCount();
        if (terms > 0) {
            total += terms - 1;
        }
    }
    return total;
}

PairKey::PairKey() = default;

PairKey::PairKey(const TermType &lhs, const TermType &rhs) {
    if (rhs < lhs) {
        a = rhs;
        b = lhs;
    } else {
        a = lhs;
        b = rhs;
    }
}

bool PairKey::operator<(const PairKey &other) const {
    if (a.signal != other.a.signal) {
        return a.signal < other.a.signal;
    }
    if (a.sign != other.a.sign) {
        return a.sign < other.a.sign;
    }
    if (b.signal != other.b.signal) {
        return b.signal < other.b.signal;
    }
    return b.sign < other.b.sign;
}

bool PairKey::operator==(const PairKey &other) const {
    return a.signal == other.a.signal && a.sign == other.a.sign && b.signal == other.b.signal &&
           b.sign == other.b.sign;
}

SignalTable::SignalTable(int numInputs, int bitWidth)
    : numInputs_(numInputs), bitWidth_(bitWidth), maxShift_(bitWidth), nextId_(0) {}

int SignalTable::allocateId() { return nextId_++; }

void SignalTable::updateMaxShift(int shift) {
    if (shift > maxShift_) {
        maxShift_ = shift;
    }
}

int SignalTable::ensureBaseSignal(int input, int shift) {
    if (shift < 0) {
        shift = 0;
    }
    if (shift > kMaxShiftLimit) {
        shift = static_cast<int>(kMaxShiftLimit);
    }
    updateMaxShift(shift);
    auto key = std::make_pair(input, shift);
    auto it = baseIndex_.find(key);
    if (it != baseIndex_.end()) {
        return it->second;
    }
    Signal sig;
    sig.id = allocateId();
    sig.coeffs.assign(numInputs_, 0);
    if (shift >= 0 && shift < 63) {
        sig.coeffs[input] = 1LL << shift;
    } else {
        sig.coeffs[input] = 0;
    }
    std::ostringstream oss;
    oss << "x" << input << "<<" << shift;
    sig.label = oss.str();
    signals_.push_back(sig);
    baseIndex_[key] = sig.id;
    return sig.id;
}

int SignalTable::createCompositeSignal(const TermType &lhs, const TermType &rhs) {
    const auto &leftSig = get(lhs.signal);
    const auto &rightSig = get(rhs.signal);
    Signal sig;
    sig.id = allocateId();
    sig.coeffs.assign(numInputs_, 0);
    for (int i = 0; i < numInputs_; ++i) {
        sig.coeffs[i] = lhs.sign * leftSig.coeffs[i] + rhs.sign * rightSig.coeffs[i];
    }
    std::ostringstream oss;
    oss << "s" << sig.id;
    sig.label = oss.str();
    sig.left = lhs.signal;
    sig.right = rhs.signal;
    sig.leftSign = lhs.sign;
    sig.rightSign = rhs.sign;
    signals_.push_back(sig);
    return sig.id;
}

const Signal &SignalTable::get(int id) const { return signals_.at(id); }

Signal &SignalTable::get(int id) { return signals_.at(id); }

ProblemContext::ProblemContext(int numInputs, int bitWidth)
    : table(numInputs, bitWidth) {}

void Expression::addTerm(int signalId, int sign) {
    TermInstance inst;
    inst.signal = signalId;
    inst.sign = sign >= 0 ? 1 : -1;
    terms_.push_back(inst);
}

bool Expression::removeTerm(const TermType &term) {
    for (size_t i = 0; i < terms_.size(); ++i) {
        if (terms_[i].signal == term.signal && terms_[i].sign == term.sign) {
            terms_.erase(terms_.begin() + static_cast<long>(i));
            return true;
        }
    }
    return false;
}

int Expression::termCount() const { return static_cast<int>(terms_.size()); }

std::map<TermType, int> Expression::histogram() const {
    std::map<TermType, int> hist;
    for (const auto &term : terms_) {
        TermType type{term.signal, term.sign};
        hist[type] += 1;
    }
    return hist;
}

std::vector<long long> Expression::coefficients(const SignalTable &table) const {
    std::vector<long long> coeffs(table.numInputs(), 0);
    for (const auto &term : terms_) {
        const auto &sig = table.get(term.signal);
        for (int i = 0; i < table.numInputs(); ++i) {
            coeffs[i] += term.sign * sig.coeffs[i];
        }
    }
    return coeffs;
}

ProblemContext buildProblem(const ProblemInstance &instance) {
    ProblemContext context(instance.cols, instance.bitWidth);
    context.expressions.reserve(instance.rows);
    for (int r = 0; r < instance.rows; ++r) {
        Expression expr(r);
        for (int c = 0; c < instance.cols; ++c) {
            long long coeff = instance.matrix[r][c];
            if (coeff == 0) {
                continue;
            }
            auto digits = decomposeCoefficient(coeff);
            for (const auto &[shift, sign] : digits) {
                context.table.updateMaxShift(shift);
                int signalId = context.table.ensureBaseSignal(c, shift);
                expr.addTerm(signalId, sign >= 0 ? 1 : -1);
            }
        }
        context.expressions.push_back(expr);
    }
    return context;
}

AlgorithmResult runH2mc(const ProblemContext &base) {
    ProblemContext ctx = cloneContext(base);
    return runH2mcWithContext(std::move(ctx), "H2MC", 0).stats;
}

AlgorithmResult runHCmvm(const ProblemContext &base) {
    CmvmSynthesisOptions options;
    options.algorithm = "HCMVM";
    options.differenceRows = true;
    return runHCmvmWithContext(base, options).stats;
}

AlgorithmResult runExactIlp(const ProblemContext &base) {
    return runExactIlpWithContext(base).stats;
}

CmvmSynthesisOutcome synthesizeCmvm(const ProblemInstance &instance,
                                    const CmvmSynthesisOptions &options) {
    ProblemContext base = buildProblem(instance);
    const std::string algo = uppercase(options.algorithm);
    CmvmSynthesisOutcome primary =
        (algo == "EXACTILP")
            ? runExactIlpWithContext(base)
            : (algo == "H2MC") ? runH2mcWithContext(base, "H2MC", options.maxPairSearch)
                               : (algo == "HCMVM") ? runHCmvmWithContext(base, options)
                                                   : throw std::runtime_error("Unknown CMVM algorithm: " +
                                                                              options.algorithm);
    if (options.fallbackAlgorithm) {
        const std::string fallbackAlgo = uppercase(*options.fallbackAlgorithm);
        CmvmSynthesisOutcome fallback =
            (fallbackAlgo == "EXACTILP")
                ? runExactIlpWithContext(primary.context)
                : (fallbackAlgo == "H2MC")
                      ? runH2mcWithContext(primary.context, "H2MC", options.maxPairSearch)
                      : throw std::runtime_error("Unknown CMVM fallback algorithm: " +
                                                 *options.fallbackAlgorithm);
        if (fallback.stats.totalOperations < primary.stats.totalOperations) {
            if (fallback.relations.empty() && !primary.relations.empty()) {
                fallback.relations = primary.relations;
            }
            fallback.stats.name = primary.stats.name + "+" + fallback.stats.name;
            return fallback;
        }
    }
    return primary;
}

} // namespace cse
