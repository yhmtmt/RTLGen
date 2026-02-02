#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <limits>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace mcm {

using Value = long long;

struct Operation {
    Value u{1};
    Value v{1};
    int l1{0};
    int l2{0};
    bool subtraction{false};
    int rShift{0};
    Value result{1};

    std::string describe() const {
        std::ostringstream oss;
        oss << "|(" << u << " << " << l1 << ") "
            << (subtraction ? "-" : "+") << " (" << v << " << " << l2
            << ")| >> " << rShift << " = " << result;
        return oss.str();
    }
};

struct Solution {
    std::string name;
    std::vector<Operation> operations;
    std::vector<Value> synthesizedTargets;
    std::set<Value> ready;

    size_t operationCount() const { return operations.size(); }
};

struct InputSpec {
    int bitWidth{0};
    std::vector<Value> targets;
};

struct AOpOptions {
    int bitWidth{0};
    int maxShift{0};
    bool oddOutputs{false};
    bool allowRightShift{false};
    Value maxValue{0};
};

inline Value normalizeOdd(Value v, int &shifts) {
    shifts = 0;
    if (v == 0) {
        return 0;
    }
    while ((v & 1LL) == 0) {
        v >>= 1;
        ++shifts;
    }
    return v;
}

inline Value normalizeOdd(Value v) {
    int dummy = 0;
    return normalizeOdd(v, dummy);
}

inline int csdCost(Value v) {
    Value n = std::llabs(v);
    int cost = 0;
    int carry = 0;
    while (n > 0 || carry != 0) {
        int bit = static_cast<int>(n & 1LL);
        n >>= 1;
        int digit = bit + carry;
        if (digit == 0 || digit == 1) {
            if (digit == 1) {
                ++cost;
            }
            carry = 0;
        } else if (digit == 2) {
            digit = -1;
            ++cost;
            carry = 1;
        } else if (digit == -1) {
            ++cost;
            carry = 0;
        }
    }
    return cost == 0 ? 1 : cost;
}

inline Value closestValue(const std::set<Value> &ready, Value target) {
    if (ready.empty()) {
        return 1;
    }
    auto it = ready.lower_bound(target);
    if (it == ready.begin()) {
        return *it;
    }
    if (it == ready.end()) {
        return *std::prev(it);
    }
    Value higher = *it;
    Value lower = *std::prev(it);
    return (std::llabs(higher - target) < std::llabs(lower - target)) ? higher
                                                                      : lower;
}

inline AOpOptions makeAoddOptions(int bitWidth, Value maxValue) {
    AOpOptions opts;
    opts.bitWidth = bitWidth;
    opts.maxShift = bitWidth + 1;
    opts.oddOutputs = true;
    opts.allowRightShift = true;
    opts.maxValue = maxValue;
    return opts;
}

inline AOpOptions makeLinearOptions(int bitWidth, Value maxValue) {
    AOpOptions opts;
    opts.bitWidth = bitWidth;
    opts.maxShift = bitWidth + 1;
    opts.oddOutputs = false;
    opts.allowRightShift = false;
    opts.maxValue = maxValue;
    return opts;
}

std::unordered_map<Value, Operation> generateSuccessors(const std::set<Value> &ready,
                                                        const AOpOptions &opts);

} // namespace mcm
