#include "mcm_algorithms.hpp"

#include <queue>
#include <cmath>

namespace mcm {
namespace {

using ReadySet = std::set<Value>;
using TargetSet = std::set<Value>;
using SuccessorMap = std::unordered_map<Value, Operation>;

std::vector<Value> toVector(const TargetSet &targets) {
    return std::vector<Value>(targets.begin(), targets.end());
}

Value maxTarget(const TargetSet &targets) {
    if (targets.empty()) {
        return 1;
    }
    return *targets.rbegin();
}

void addFundamental(Value value, const Operation &op, ReadySet &ready,
                    Solution &solution) {
    if (value <= 0) {
        return;
    }
    if (ready.insert(value).second) {
        Operation stored = op;
        stored.result = value;
        solution.operations.push_back(stored);
    }
}

SuccessorMap computeSuccessors(const ReadySet &ready, const AOpOptions &opts) {
    return generateSuccessors(ready, opts);
}

struct DistanceTwoPlan {
    Value intermediate{0};
    Operation opIntermediate{};
    Operation opFinal{};
};

Value pickMinComplexityTarget(const TargetSet &targets) {
    return *std::min_element(targets.begin(), targets.end(),
                             [](Value lhs, Value rhs) {
                                 int cl = csdCost(lhs);
                                 int cr = csdCost(rhs);
                                 if (cl == cr) {
                                     return lhs < rhs;
                                 }
                                 return cl < cr;
                             });
}

std::optional<DistanceTwoPlan> findDistanceTwo(Value target, const ReadySet &ready,
                                               const SuccessorMap &successors) {
    for (Value r : ready) {
        Value diff = target - r;
        if (diff == 0) {
            continue;
        }
        int shift = 0;
        Value base = normalizeOdd(std::llabs(diff), shift);
        auto it = successors.find(base);
        if (it == successors.end()) {
            continue;
        }
        DistanceTwoPlan plan;
        plan.intermediate = base;
        plan.opIntermediate = it->second;
        plan.opFinal.u = r;
        plan.opFinal.v = base;
        plan.opFinal.l1 = 0;
        plan.opFinal.l2 = shift;
        plan.opFinal.subtraction = (diff < 0);
        plan.opFinal.rShift = 0;
        plan.opFinal.result = target;
        return plan;
    }
    return std::nullopt;
}

bool synthesizeSingle(Value target, ReadySet &ready, Solution &solution,
                      const AOpOptions &opts) {
    int guard = 0;
    while (!ready.count(target) && guard < 64) {
        ++guard;
        Value closest = closestValue(ready, target);
        Value diff = target - closest;
        if (diff == 0) {
            break;
        }
        int shift = 0;
        Value oddDiff = normalizeOdd(std::llabs(diff), shift);
        auto successors = computeSuccessors(ready, opts);
        auto it = successors.find(oddDiff);
        if (it != successors.end()) {
            addFundamental(oddDiff, it->second, ready, solution);
        } else {
            Operation op;
            op.u = closest;
            op.v = 1;
            op.subtraction = diff < 0;
            Value raw = std::llabs(closest + (op.subtraction ? -1 : 1));
            int rShift = 0;
            Value oddResult = normalizeOdd(raw, rShift);
            op.rShift = rShift;
            op.result = oddResult;
            addFundamental(oddResult, op, ready, solution);
            continue;
        }
        Operation finalOp;
        finalOp.u = closest;
        finalOp.v = oddDiff;
        finalOp.l1 = 0;
        finalOp.l2 = shift;
        finalOp.subtraction = diff < 0;
        finalOp.rShift = 0;
        finalOp.result = target;
        addFundamental(target, finalOp, ready, solution);
    }
    return ready.count(target) != 0;
}

int estimateDistance(const ReadySet &ready, const SuccessorMap &successors,
                     Value target) {
    if (ready.count(target)) {
        return 0;
    }
    if (successors.count(target)) {
        return 1;
    }
    Value closest = closestValue(ready, target);
    Value diff = std::llabs(target - closest);
    if (diff == 0) {
        return 2;
    }
    int approx = static_cast<int>(std::ceil(std::log2(diff + 1)));
    return 2 + approx;
}

int estimateDistanceWithCandidate(const ReadySet &ready,
                                  const SuccessorMap &successors, Value candidate,
                                  Value target) {
    if (candidate == target) {
        return 1;
    }
    ReadySet augmented = ready;
    augmented.insert(candidate);
    Value diff = std::llabs(target - candidate);
    int approx = diff == 0 ? 1
                           : 1 + static_cast<int>(std::ceil(std::log2(diff + 1)));
    int base = estimateDistance(augmented, successors, target);
    return std::min(base, approx);
}

double cumulativeBenefit(const ReadySet &ready, const SuccessorMap &successors,
                         Value candidate, const TargetSet &targets) {
    double total = 0.0;
    for (Value t : targets) {
        int before = estimateDistance(ready, successors, t);
        int after = estimateDistanceWithCandidate(ready, successors, candidate, t);
        if (after >= before) {
            continue;
        }
        double weight = std::pow(0.1, static_cast<double>(after));
        total += weight * static_cast<double>(before - after);
    }
    return total;
}

TargetSet makeTargetSet(const std::vector<Value> &values) {
    TargetSet targets;
    for (Value v : values) {
        if (v > 0) {
            targets.insert(v);
        }
    }
    return targets;
}

bool removeTarget(TargetSet &targets, Value value, Solution &solution) {
    auto it = targets.find(value);
    if (it == targets.end()) {
        return false;
    }
    targets.erase(it);
    solution.synthesizedTargets.push_back(value);
    return true;
}

} // namespace

std::vector<Value> uniqueSorted(const std::vector<Value> &values) {
    std::set<Value> uniq;
    for (Value v : values) {
        if (v > 0) {
            uniq.insert(v);
        }
    }
    return toVector(uniq);
}

std::vector<Value> makeOddTargets(const std::vector<Value> &values) {
    std::set<Value> uniq;
    for (Value v : values) {
        if (v <= 0) {
            continue;
        }
        int shift = 0;
        Value odd = normalizeOdd(v, shift);
        uniq.insert(odd);
    }
    return toVector(uniq);
}

Solution runBHA(const InputSpec &input) {
    Solution solution;
    solution.name = "BHA";
    ReadySet ready = {1};
    TargetSet targets = makeTargetSet(uniqueSorted(input.targets));
    if (targets.empty()) {
        solution.ready = ready;
        return solution;
    }
    while (!targets.empty()) {
        Value target = *targets.begin();
        if (ready.count(target)) {
            solution.synthesizedTargets.push_back(target);
            targets.erase(target);
            continue;
        }
        Value limit = target;
        auto opts = makeLinearOptions(input.bitWidth, limit);
        auto successors = computeSuccessors(ready, opts);
        auto directIt = successors.find(target);
        if (directIt != successors.end()) {
            addFundamental(target, directIt->second, ready, solution);
            removeTarget(targets, target, solution);
            continue;
        }
        Value maxReady = *ready.rbegin();
        if (maxReady >= target) {
            if (!successors.empty()) {
                auto entry = *successors.begin();
                addFundamental(entry.first, entry.second, ready, solution);
            } else {
                Operation op;
                op.u = maxReady;
                op.v = 1;
                op.result = maxReady + 1;
                addFundamental(op.result, op, ready, solution);
            }
            continue;
        }
        Value epsilon = target - maxReady;
        if (ready.count(epsilon)) {
            Operation op;
            op.u = maxReady;
            op.v = epsilon;
            op.result = target;
            addFundamental(target, op, ready, solution);
            removeTarget(targets, target, solution);
            continue;
        }
        Value chosen = 0;
        Operation chosenOp{};
        Value bestGap = std::numeric_limits<Value>::max();
        for (const auto &entry : successors) {
            Value val = entry.first;
            if (val > epsilon) {
                continue;
            }
            Value gap = epsilon - val;
            if (gap < bestGap) {
                bestGap = gap;
                chosen = val;
                chosenOp = entry.second;
            }
        }
        if (chosen == 0 && !successors.empty()) {
            for (const auto &entry : successors) {
                if (chosen == 0 || entry.first < chosen) {
                    chosen = entry.first;
                    chosenOp = entry.second;
                }
            }
        }
        if (chosen != 0) {
            addFundamental(chosen, chosenOp, ready, solution);
            Value sum = maxReady + chosen;
            Operation op;
            op.u = maxReady;
            op.v = chosen;
            op.result = sum;
            addFundamental(sum, op, ready, solution);
            if (sum == target) {
                removeTarget(targets, target, solution);
            }
        } else {
            Operation op;
            op.u = maxReady;
            op.v = 1;
            op.result = maxReady + 1;
            addFundamental(op.result, op, ready, solution);
        }
    }
    solution.ready = ready;
    return solution;
}

Solution runBHM(const InputSpec &input) {
    Solution solution;
    solution.name = "BHM";
    ReadySet ready = {1};
    auto oddTargets = makeOddTargets(input.targets);
    TargetSet targets = makeTargetSet(oddTargets);
    if (targets.empty()) {
        solution.ready = ready;
        return solution;
    }
    while (!targets.empty()) {
        Value target = pickMinComplexityTarget(targets);
        if (ready.count(target)) {
            targets.erase(target);
            solution.synthesizedTargets.push_back(target);
            continue;
        }
        Value maxT = maxTarget(targets);
        Value limit = std::max<Value>(2 * maxT,
                                      static_cast<Value>(1ULL << (input.bitWidth + 1)));
        auto opts = makeAoddOptions(input.bitWidth, limit);
        auto successors = computeSuccessors(ready, opts);
        auto directIt = successors.find(target);
        if (directIt != successors.end()) {
            addFundamental(target, directIt->second, ready, solution);
            targets.erase(target);
            solution.synthesizedTargets.push_back(target);
            continue;
        }
        Value rc = closestValue(ready, target);
        Value epsilon = target - rc;
        Value absEps = std::llabs(epsilon);
        int shiftEps = 0;
        Value oddEps = normalizeOdd(absEps, shiftEps);
        if (ready.count(oddEps)) {
            Operation op;
            op.u = rc;
            op.v = oddEps;
            op.l1 = 0;
            op.l2 = shiftEps;
            op.subtraction = (epsilon < 0);
            op.result = target;
            addFundamental(target, op, ready, solution);
            targets.erase(target);
            solution.synthesizedTargets.push_back(target);
            continue;
        }
        Value bestBase = 0;
        Operation bestBaseOp{};
        int bestShift = 0;
        Value bestScore = std::numeric_limits<Value>::max();
        int maxShift = epsilon == 0
                           ? 0
                           : static_cast<int>(std::ceil(std::log2(absEps + 1)));
        for (const auto &entry : successors) {
            Value base = entry.first;
            for (int k = 0; k <= maxShift; ++k) {
                if (k >= 60) {
                    break;
                }
                Value scaled = base << k;
                if (scaled <= 0) {
                    continue;
                }
                Value score = std::llabs(absEps - scaled);
                if (score < bestScore) {
                    bestScore = score;
                    bestBase = base;
                    bestBaseOp = entry.second;
                    bestShift = k;
                }
            }
        }
        if (bestBase == 0 && !successors.empty()) {
            bestBase = successors.begin()->first;
            bestBaseOp = successors.begin()->second;
            bestShift = 0;
        }
        if (bestBase == 0) {
            Operation op;
            op.u = rc;
            op.v = 1;
            op.result = normalizeOdd(std::llabs(rc + 1));
            addFundamental(op.result, op, ready, solution);
            continue;
        }
        addFundamental(bestBase, bestBaseOp, ready, solution);
        Value scaled = bestBase << bestShift;
        Value addCandidate = rc + scaled;
        Value subCandidate = rc - scaled;
        bool useSub = std::llabs(target - subCandidate) <
                      std::llabs(target - addCandidate);
        Value chosenRaw = useSub ? subCandidate : addCandidate;
        Value rawAbs = std::llabs(chosenRaw);
        int rShift = 0;
        Value oddResult = normalizeOdd(rawAbs, rShift);
        Operation op;
        op.u = rc;
        op.v = bestBase;
        op.l1 = 0;
        op.l2 = bestShift;
        op.subtraction = useSub;
        op.rShift = rShift;
        op.result = oddResult;
        addFundamental(oddResult, op, ready, solution);
        if (oddResult == target) {
            targets.erase(target);
            solution.synthesizedTargets.push_back(target);
        }
    }
    solution.ready = ready;
    return solution;
}

Solution runRAGn(const InputSpec &input) {
    Solution solution;
    solution.name = "RAG-n";
    ReadySet ready = {1};
    auto oddTargets = makeOddTargets(input.targets);
    TargetSet targets = makeTargetSet(oddTargets);
    if (targets.empty()) {
        solution.ready = ready;
        return solution;
    }
    Value limit = static_cast<Value>(1ULL << (input.bitWidth + 1));
    auto opts = makeAoddOptions(input.bitWidth, limit);
    while (!targets.empty()) {
        std::vector<Value> completed;
        for (Value t : targets) {
            if (ready.count(t)) {
                completed.push_back(t);
            }
        }
        for (Value t : completed) {
            removeTarget(targets, t, solution);
        }
        if (targets.empty()) {
            break;
        }
        auto successors = computeSuccessors(ready, opts);
        bool progress = false;
        for (Value t : toVector(targets)) {
            auto it = successors.find(t);
            if (it != successors.end()) {
                addFundamental(t, it->second, ready, solution);
                removeTarget(targets, t, solution);
                progress = true;
            }
        }
        if (progress) {
            continue;
        }
        for (Value t : toVector(targets)) {
            auto plan = findDistanceTwo(t, ready, successors);
            if (!plan.has_value()) {
                continue;
            }
            if (!ready.count(plan->intermediate)) {
                addFundamental(plan->intermediate, plan->opIntermediate, ready,
                               solution);
            }
            addFundamental(t, plan->opFinal, ready, solution);
            removeTarget(targets, t, solution);
            progress = true;
            break;
        }
        if (progress) {
            continue;
        }
        Value fallbackTarget = pickMinComplexityTarget(targets);
        if (!synthesizeSingle(fallbackTarget, ready, solution, opts)) {
            break;
        }
        removeTarget(targets, fallbackTarget, solution);
    }
    solution.ready = ready;
    return solution;
}

Solution runHCub(const InputSpec &input) {
    Solution solution;
    solution.name = "H_cub";
    ReadySet ready = {1};
    auto oddTargets = makeOddTargets(input.targets);
    TargetSet targets = makeTargetSet(oddTargets);
    if (targets.empty()) {
        solution.ready = ready;
        return solution;
    }
    Value limit = static_cast<Value>(1ULL << (input.bitWidth + 2));
    auto opts = makeAoddOptions(input.bitWidth, limit);
    while (!targets.empty()) {
        std::vector<Value> completed;
        for (Value t : targets) {
            if (ready.count(t)) {
                completed.push_back(t);
            }
        }
        for (Value t : completed) {
            removeTarget(targets, t, solution);
        }
        if (targets.empty()) {
            break;
        }
        auto successors = computeSuccessors(ready, opts);
        bool progress = false;
        for (Value t : toVector(targets)) {
            auto it = successors.find(t);
            if (it != successors.end()) {
                addFundamental(t, it->second, ready, solution);
                removeTarget(targets, t, solution);
                progress = true;
            }
        }
        if (progress) {
            continue;
        }
        Value bestCandidate = 0;
        Operation bestOp{};
        double bestScore = -1.0;
        for (const auto &entry : successors) {
            Value candidate = entry.first;
            if (ready.count(candidate)) {
                continue;
            }
            double score = cumulativeBenefit(ready, successors, candidate, targets);
            if (score > bestScore) {
                bestScore = score;
                bestCandidate = candidate;
                bestOp = entry.second;
            }
        }
        if (bestCandidate == 0 && !successors.empty()) {
            Value fallback = 0;
            Value bestGap = std::numeric_limits<Value>::max();
            for (const auto &entry : successors) {
                Value candidate = entry.first;
                if (ready.count(candidate)) {
                    continue;
                }
                Value gap = 0;
                for (Value t : targets) {
                    gap += std::llabs(t - candidate);
                }
                if (gap < bestGap) {
                    bestGap = gap;
                    fallback = candidate;
                    bestOp = entry.second;
                }
            }
            bestCandidate = fallback;
        }
        if (bestCandidate == 0) {
            Operation op;
            Value maxReady = *ready.rbegin();
            op.u = maxReady;
            op.v = 1;
            Value raw = std::llabs(maxReady + 1);
            int rShift = 0;
            Value oddValue = normalizeOdd(raw, rShift);
            op.rShift = rShift;
            op.result = oddValue;
            addFundamental(oddValue, op, ready, solution);
            continue;
        }
        addFundamental(bestCandidate, bestOp, ready, solution);
    }
    solution.ready = ready;
    return solution;
}

} // namespace mcm
