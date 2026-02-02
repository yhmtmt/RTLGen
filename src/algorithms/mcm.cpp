#include "mcm.hpp"

namespace mcm {
namespace {

constexpr Value defaultLimit() {
    return std::numeric_limits<Value>::max() / 4;
}

bool safeShift(Value val, int shift, Value limit, Value &out) {
    if (shift < 0) {
        return false;
    }
    if (val == 0) {
        out = 0;
        return true;
    }
    if (shift >= 60) {
        return false;
    }
    Value bound = limit > 0 ? limit : defaultLimit();
    if (std::llabs(val) > (bound >> shift)) {
        return false;
    }
    out = val << shift;
    return true;
}

} // namespace

std::unordered_map<Value, Operation> generateSuccessors(const std::set<Value> &ready,
                                                        const AOpOptions &opts) {
    std::unordered_map<Value, Operation> successors;
    const Value limit = opts.maxValue > 0 ? opts.maxValue : defaultLimit();
    for (Value u : ready) {
        for (Value v : ready) {
            for (int l1 = 0; l1 <= opts.maxShift; ++l1) {
                Value su = 0;
                if (!safeShift(u, l1, limit, su)) {
                    break;
                }
                for (int l2 = 0; l2 <= opts.maxShift; ++l2) {
                    Value sv = 0;
                    if (!safeShift(v, l2, limit, sv)) {
                        break;
                    }
                    for (int sign = 0; sign < 2; ++sign) {
                        __int128 raw = static_cast<__int128>(su) +
                                        (sign == 0 ? static_cast<__int128>(sv)
                                                   : -static_cast<__int128>(sv));
                        if (raw == 0) {
                            continue;
                        }
                        if (raw < 0) {
                            raw = -raw;
                        }
                        if (raw > limit) {
                            continue;
                        }
                        Value value = static_cast<Value>(raw);
                        int rShift = 0;
                        if (opts.oddOutputs) {
                            value = normalizeOdd(value, rShift);
                        }
                        if (value <= 0 || value > limit) {
                            continue;
                        }
                        Operation op;
                        op.u = u;
                        op.v = v;
                        op.l1 = l1;
                        op.l2 = l2;
                        op.subtraction = (sign == 1);
                        op.rShift = opts.oddOutputs ? rShift : 0;
                        op.result = value;
                        if (!successors.count(value)) {
                            successors.emplace(value, op);
                        }
                    }
                }
            }
        }
    }
    return successors;
}

} // namespace mcm
