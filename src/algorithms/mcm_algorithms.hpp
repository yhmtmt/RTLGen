#pragma once

#include "mcm.hpp"

namespace mcm {

std::vector<Value> uniqueSorted(const std::vector<Value> &values);
std::vector<Value> makeOddTargets(const std::vector<Value> &values);

Solution runBHA(const InputSpec &input);
Solution runBHM(const InputSpec &input);
Solution runRAGn(const InputSpec &input);
Solution runHCub(const InputSpec &input);

} // namespace mcm
