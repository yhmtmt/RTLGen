#include "mcm_ilp.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <map>
#include <stdexcept>

#include "mcm_algorithms.hpp"
#include "ortools/linear_solver/linear_solver.h"

namespace mcm {
namespace {

using operations_research::MPConstraint;
using operations_research::MPVariable;
using operations_research::MPSolver;

constexpr Value kSaturationGuard = std::numeric_limits<Value>::max() / 4;

Value saturatingShift(Value value, int shift) {
    if (shift <= 0) {
        return value;
    }
    Value result = value;
    for (int i = 0; i < shift; ++i) {
        if (result > kSaturationGuard) {
            return kSaturationGuard;
        }
        result <<= 1;
    }
    return result;
}

Value saturatingPow2(int exponent) {
    if (exponent <= 0) {
        return 1;
    }
    return saturatingShift(1, exponent);
}

void addSelectionEquality(MPSolver &solver, MPVariable *lhs, MPVariable *rhs,
                          MPVariable *selector, double bigM) {
    // lhs - rhs <= bigM * (1 - selector)
    MPConstraint *upper = solver.MakeRowConstraint(-solver.infinity(), bigM);
    upper->SetCoefficient(lhs, 1.0);
    upper->SetCoefficient(rhs, -1.0);
    upper->SetCoefficient(selector, bigM);

    // rhs - lhs <= bigM * (1 - selector)
    MPConstraint *lower = solver.MakeRowConstraint(-solver.infinity(), bigM);
    lower->SetCoefficient(rhs, 1.0);
    lower->SetCoefficient(lhs, -1.0);
    lower->SetCoefficient(selector, bigM);
}

void addShiftEquality(MPSolver &solver, MPVariable *shifted, MPVariable *value,
                      MPVariable *selector, double factor, double bigM) {
    // shifted - factor * value <= bigM * (1 - selector)
    MPConstraint *upper = solver.MakeRowConstraint(-solver.infinity(), bigM);
    upper->SetCoefficient(shifted, 1.0);
    upper->SetCoefficient(value, -factor);
    upper->SetCoefficient(selector, bigM);

    // factor * value - shifted <= bigM * (1 - selector)
    MPConstraint *lower = solver.MakeRowConstraint(-solver.infinity(), bigM);
    lower->SetCoefficient(value, factor);
    lower->SetCoefficient(shifted, -1.0);
    lower->SetCoefficient(selector, bigM);
}

std::string sanitize(const std::string &value) {
    std::string upper;
    upper.reserve(value.size());
    for (char ch : value) {
        if (ch == '_' || ch == '-' || std::isspace(static_cast<unsigned char>(ch))) {
            continue;
        }
        upper.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(ch))));
    }
    return upper;
}

Value roundToValue(double v) {
    return static_cast<Value>(std::llround(v));
}

} // namespace

std::optional<AdderEstimator> parseEstimator(const std::string &name) {
    std::string token = sanitize(name);
    if (token == "BHA") {
        return AdderEstimator::BHA;
    }
    if (token == "BHM") {
        return AdderEstimator::BHM;
    }
    if (token == "RAGN") {
        return AdderEstimator::RAGn;
    }
    if (token == "HCUB" || token == "HCUBIC") {
        return AdderEstimator::HCub;
    }
    return std::nullopt;
}

std::string estimatorToString(AdderEstimator estimator) {
    switch (estimator) {
    case AdderEstimator::BHA:
        return "BHA";
    case AdderEstimator::BHM:
        return "BHM";
    case AdderEstimator::RAGn:
        return "RAGn";
    case AdderEstimator::HCub:
        return "H_cub";
    }
    return "unknown";
}

int estimateAdders(const InputSpec &input, AdderEstimator estimator) {
    using Runner = Solution (*)(const InputSpec &);
    static const std::map<AdderEstimator, Runner> kEstimators = {
        {AdderEstimator::BHA, runBHA}, {AdderEstimator::BHM, runBHM},
        {AdderEstimator::RAGn, runRAGn}, {AdderEstimator::HCub, runHCub}};
    auto it = kEstimators.find(estimator);
    if (it == kEstimators.end()) {
        return -1;
    }
    Solution sol = it->second(input);
    return static_cast<int>(sol.operationCount());
}

IlpResult runIlpOptimal(const IlpConfig &config) {
    IlpResult result;
    result.solution.name = "ILP_2023";
    result.solution.ready = {1};
    if (config.bitWidth <= 0 || config.adderBudget <= 0) {
        return result;
    }
    auto cleanedTargets = uniqueSorted(config.targets);
    if (cleanedTargets.empty()) {
        result.feasible = true;
        return result;
    }
    const Value targetMax = *cleanedTargets.rbegin();
    const int shiftLimit = std::max(0, std::min(config.bitWidth + 1, 30));
    const int rshiftLimit = shiftLimit;
    const Value baseBound =
        saturatingPow2(std::min(config.bitWidth + shiftLimit + 3, 60));
    Value valueBound = std::max(targetMax, baseBound);
    if (valueBound <= 0) {
        valueBound = baseBound;
    }
    const Value shiftedBound = saturatingShift(valueBound, shiftLimit);
    const Value absBound = saturatingShift(shiftedBound, 1);
    const double bigValue = static_cast<double>(std::max(valueBound, Value(1))) * 4.0;
    const double bigShifted =
        static_cast<double>(std::max(shiftedBound, Value(1))) * 4.0;
    const double bigAbs = static_cast<double>(std::max(absBound, Value(1))) * 4.0;

    MPSolver solver("mcm_ilp", MPSolver::CBC_MIXED_INTEGER_PROGRAMMING);

    const int adderCount = config.adderBudget;
    std::vector<MPVariable *> values(adderCount + 1, nullptr);
    values[0] = solver.MakeIntVar(1.0, 1.0, "val_0");
    for (int a = 1; a <= adderCount; ++a) {
        values[a] =
            solver.MakeIntVar(1.0, static_cast<double>(valueBound), "val_" + std::to_string(a));
    }

    std::vector<MPVariable *> uVals(adderCount + 1, nullptr);
    std::vector<MPVariable *> vVals(adderCount + 1, nullptr);
    std::vector<MPVariable *> shiftedU(adderCount + 1, nullptr);
    std::vector<MPVariable *> shiftedV(adderCount + 1, nullptr);
    std::vector<MPVariable *> signedV(adderCount + 1, nullptr);
    std::vector<MPVariable *> sumVars(adderCount + 1, nullptr);
    std::vector<MPVariable *> absVars(adderCount + 1, nullptr);
    std::vector<MPVariable *> subVars(adderCount + 1, nullptr);
    std::vector<MPVariable *> sumSigns(adderCount + 1, nullptr);

    for (int a = 1; a <= adderCount; ++a) {
        const std::string prefix = "a" + std::to_string(a);
        uVals[a] = solver.MakeIntVar(1.0, static_cast<double>(valueBound), prefix + "_u");
        vVals[a] = solver.MakeIntVar(1.0, static_cast<double>(valueBound), prefix + "_v");
        shiftedU[a] =
            solver.MakeIntVar(0.0, static_cast<double>(shiftedBound), prefix + "_sU");
        shiftedV[a] =
            solver.MakeIntVar(0.0, static_cast<double>(shiftedBound), prefix + "_sV");
        signedV[a] = solver.MakeIntVar(-static_cast<double>(shiftedBound),
                                       static_cast<double>(shiftedBound), prefix + "_sgV");
        sumVars[a] = solver.MakeIntVar(-static_cast<double>(absBound),
                                       static_cast<double>(absBound), prefix + "_sum");
        absVars[a] =
            solver.MakeIntVar(0.0, static_cast<double>(absBound), prefix + "_abs");
        subVars[a] = solver.MakeBoolVar(prefix + "_sub");
        sumSigns[a] = solver.MakeBoolVar(prefix + "_sign");
    }

    auto makeChoiceMatrix = [&](const std::string &label, int width) {
        std::vector<std::vector<MPVariable *>> matrix(adderCount + 1);
        for (int a = 1; a <= adderCount; ++a) {
            matrix[a].resize(width);
            for (int i = 0; i < width; ++i) {
                matrix[a][i] =
                    solver.MakeBoolVar(label + "_" + std::to_string(a) + "_" + std::to_string(i));
            }
        }
        return matrix;
    };

    std::vector<std::vector<MPVariable *>> uSelect(adderCount + 1);
    std::vector<std::vector<MPVariable *>> vSelect(adderCount + 1);
    for (int a = 1; a <= adderCount; ++a) {
        uSelect[a].resize(a);
        vSelect[a].resize(a);
        MPConstraint *uSum = solver.MakeRowConstraint(1.0, 1.0);
        MPConstraint *vSum = solver.MakeRowConstraint(1.0, 1.0);
        for (int k = 0; k < a; ++k) {
            uSelect[a][k] =
                solver.MakeBoolVar("u_idx_" + std::to_string(a) + "_" + std::to_string(k));
            vSelect[a][k] =
                solver.MakeBoolVar("v_idx_" + std::to_string(a) + "_" + std::to_string(k));
            uSum->SetCoefficient(uSelect[a][k], 1.0);
            vSum->SetCoefficient(vSelect[a][k], 1.0);

            addSelectionEquality(solver, uVals[a], values[k], uSelect[a][k], bigValue);
            addSelectionEquality(solver, vVals[a], values[k], vSelect[a][k], bigValue);
        }
    }

    const int shiftChoices = shiftLimit + 1;
    auto uShift = makeChoiceMatrix("u_shift", shiftChoices);
    auto vShift = makeChoiceMatrix("v_shift", shiftChoices);
    const int rshiftChoices = rshiftLimit + 1;
    auto rShift = makeChoiceMatrix("r_shift", rshiftChoices);

    std::vector<double> shiftFactors(shiftChoices, 1.0);
    for (int s = 0; s < shiftChoices; ++s) {
        shiftFactors[s] = std::ldexp(1.0, s);
    }
    std::vector<double> rShiftFactors(rshiftChoices, 1.0);
    for (int s = 0; s < rshiftChoices; ++s) {
        rShiftFactors[s] = std::ldexp(1.0, s);
    }

    for (int a = 1; a <= adderCount; ++a) {
        MPConstraint *uShiftSum = solver.MakeRowConstraint(1.0, 1.0);
        MPConstraint *vShiftSum = solver.MakeRowConstraint(1.0, 1.0);
        MPConstraint *rShiftSum = solver.MakeRowConstraint(1.0, 1.0);
        for (int s = 0; s < shiftChoices; ++s) {
            uShiftSum->SetCoefficient(uShift[a][s], 1.0);
            vShiftSum->SetCoefficient(vShift[a][s], 1.0);
            addShiftEquality(solver, shiftedU[a], uVals[a], uShift[a][s], shiftFactors[s],
                             bigShifted);
            addShiftEquality(solver, shiftedV[a], vVals[a], vShift[a][s], shiftFactors[s],
                             bigShifted);
        }
        for (int s = 0; s < rshiftChoices; ++s) {
            rShiftSum->SetCoefficient(rShift[a][s], 1.0);
            addShiftEquality(solver, absVars[a], values[a], rShift[a][s], rShiftFactors[s],
                             bigAbs);
        }
        // signedV control based on subVars[a]
        MPConstraint *addPos = solver.MakeRowConstraint(-solver.infinity(), 0.0);
        addPos->SetCoefficient(signedV[a], 1.0);
        addPos->SetCoefficient(shiftedV[a], -1.0);
        addPos->SetCoefficient(subVars[a], -bigShifted);

        MPConstraint *addNeg = solver.MakeRowConstraint(-solver.infinity(), 0.0);
        addNeg->SetCoefficient(shiftedV[a], 1.0);
        addNeg->SetCoefficient(signedV[a], -1.0);
        addNeg->SetCoefficient(subVars[a], -bigShifted);

        MPConstraint *subUpper = solver.MakeRowConstraint(-solver.infinity(), bigShifted);
        subUpper->SetCoefficient(signedV[a], 1.0);
        subUpper->SetCoefficient(shiftedV[a], 1.0);
        subUpper->SetCoefficient(subVars[a], bigShifted);

        MPConstraint *subLower = solver.MakeRowConstraint(-solver.infinity(), bigShifted);
        subLower->SetCoefficient(signedV[a], -1.0);
        subLower->SetCoefficient(shiftedV[a], -1.0);
        subLower->SetCoefficient(subVars[a], bigShifted);

        MPConstraint *sumConstraint =
            solver.MakeRowConstraint(0.0, 0.0); // equality
        sumConstraint->SetCoefficient(sumVars[a], 1.0);
        sumConstraint->SetCoefficient(shiftedU[a], -1.0);
        sumConstraint->SetCoefficient(signedV[a], -1.0);

        MPConstraint *absGte = solver.MakeRowConstraint(0.0, solver.infinity());
        absGte->SetCoefficient(absVars[a], 1.0);
        absGte->SetCoefficient(sumVars[a], -1.0);

        MPConstraint *absNegGte = solver.MakeRowConstraint(0.0, solver.infinity());
        absNegGte->SetCoefficient(absVars[a], 1.0);
        absNegGte->SetCoefficient(sumVars[a], 1.0);

        // Sum sign tracking
        MPConstraint *sumPos = solver.MakeRowConstraint(-solver.infinity(), 0.0);
        sumPos->SetCoefficient(sumVars[a], 1.0);
        sumPos->SetCoefficient(sumSigns[a], -bigAbs);

        MPConstraint *sumNeg = solver.MakeRowConstraint(-solver.infinity(), bigAbs);
        sumNeg->SetCoefficient(sumVars[a], -1.0);
        sumNeg->SetCoefficient(sumSigns[a], bigAbs);

        MPConstraint *absUpperPos =
            solver.MakeRowConstraint(-solver.infinity(), bigAbs);
        absUpperPos->SetCoefficient(absVars[a], 1.0);
        absUpperPos->SetCoefficient(sumVars[a], -1.0);
        absUpperPos->SetCoefficient(sumSigns[a], bigAbs);

        MPConstraint *absUpperNeg =
            solver.MakeRowConstraint(-solver.infinity(), 0.0);
        absUpperNeg->SetCoefficient(absVars[a], 1.0);
        absUpperNeg->SetCoefficient(sumVars[a], 1.0);
        absUpperNeg->SetCoefficient(sumSigns[a], -bigAbs);
    }

    const int targetCount = static_cast<int>(cleanedTargets.size());
    std::vector<std::vector<MPVariable *>> targetMatch(adderCount + 1,
                                                       std::vector<MPVariable *>(targetCount, nullptr));
    for (int a = 0; a <= adderCount; ++a) {
        for (int t = 0; t < targetCount; ++t) {
            targetMatch[a][t] = solver.MakeBoolVar("target_" + std::to_string(a) + "_" +
                                                   std::to_string(t));
            const double target = static_cast<double>(cleanedTargets[t]);
            // value[a] - target <= bigValue * (1 - match)
            MPConstraint *hi = solver.MakeRowConstraint(-solver.infinity(), bigValue + target);
            hi->SetCoefficient(values[a], 1.0);
            hi->SetCoefficient(targetMatch[a][t], bigValue);

            // target - value[a] <= bigValue * (1 - match)
            MPConstraint *lo = solver.MakeRowConstraint(-solver.infinity(), bigValue - target);
            lo->SetCoefficient(values[a], -1.0);
            lo->SetCoefficient(targetMatch[a][t], bigValue);
        }
    }
    for (int t = 0; t < targetCount; ++t) {
        MPConstraint *cover = solver.MakeRowConstraint(1.0, 1.0);
        for (int a = 0; a <= adderCount; ++a) {
            cover->SetCoefficient(targetMatch[a][t], 1.0);
        }
    }

    const auto status = solver.Solve();
    if (status != MPSolver::OPTIMAL && status != MPSolver::FEASIBLE) {
        return result;
    }

    result.feasible = true;
    std::vector<Value> realized(adderCount + 1, 1);
    for (int a = 1; a <= adderCount; ++a) {
        realized[a] = roundToValue(values[a]->solution_value());
    }
    std::vector<int> uIndex(adderCount + 1, 0);
    std::vector<int> vIndex(adderCount + 1, 0);
    std::vector<int> uShiftSel(adderCount + 1, 0);
    std::vector<int> vShiftSel(adderCount + 1, 0);
    std::vector<int> rShiftSel(adderCount + 1, 0);
    std::vector<bool> subSel(adderCount + 1, false);

    for (int a = 1; a <= adderCount; ++a) {
        for (int k = 0; k < a; ++k) {
            if (uSelect[a][k]->solution_value() > 0.5) {
                uIndex[a] = k;
            }
            if (vSelect[a][k]->solution_value() > 0.5) {
                vIndex[a] = k;
            }
        }
        for (int s = 0; s < shiftChoices; ++s) {
            if (uShift[a][s]->solution_value() > 0.5) {
                uShiftSel[a] = s;
            }
            if (vShift[a][s]->solution_value() > 0.5) {
                vShiftSel[a] = s;
            }
        }
        for (int s = 0; s < rshiftChoices; ++s) {
            if (rShift[a][s]->solution_value() > 0.5) {
                rShiftSel[a] = s;
            }
        }
        subSel[a] = subVars[a]->solution_value() > 0.5;
        Operation op;
        op.u = realized[uIndex[a]];
        op.v = realized[vIndex[a]];
        op.l1 = uShiftSel[a];
        op.l2 = vShiftSel[a];
        op.rShift = rShiftSel[a];
        op.subtraction = subSel[a];
        op.result = realized[a];
        result.solution.operations.push_back(op);
        result.solution.ready.insert(realized[a]);
    }
    result.solution.synthesizedTargets = cleanedTargets;
    return result;
}

} // namespace mcm
