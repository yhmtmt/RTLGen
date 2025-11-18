#pragma once

#include <optional>
#include <string>
#include <vector>

#include "mcm.hpp"

namespace mcm {

enum class AdderEstimator { BHA, BHM, RAGn, HCub };

struct IlpConfig {
    int bitWidth{0};
    std::vector<Value> targets;
    int adderBudget{0};
};

struct IlpResult {
    bool feasible{false};
    Solution solution;
};

int estimateAdders(const InputSpec &input, AdderEstimator estimator);
IlpResult runIlpOptimal(const IlpConfig &config);

std::optional<AdderEstimator> parseEstimator(const std::string &name);
std::string estimatorToString(AdderEstimator estimator);

} // namespace mcm
