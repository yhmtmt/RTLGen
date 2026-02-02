#include "mcm_ilp.hpp"

#include <exception>
#include <iostream>
#include <optional>
#include <stdexcept>

namespace {

void printUsage(const char *prog) {
    std::cerr << "Usage: " << prog
              << " <bitwidth> <target1> [target2 ...] (--adder-count N | --estimator NAME)\n";
    std::cerr << "Estimator names: BHA, BHM, RAGn, H_cub\n";
}

} // namespace

int main(int argc, char **argv) {
    using namespace mcm;
    if (argc < 4) {
        printUsage(argv[0]);
        return 1;
    }
    try {
        int bitWidth = std::stoi(argv[1]);
        if (bitWidth <= 0) {
            throw std::invalid_argument("bitwidth must be positive");
        }
        std::vector<Value> targets;
        std::optional<int> adderBudget;
        std::optional<AdderEstimator> estimator;
        int idx = 2;
        while (idx < argc) {
            std::string token = argv[idx];
            if (token == "--adder-count") {
                if (idx + 1 >= argc) {
                    throw std::invalid_argument("--adder-count expects an integer");
                }
                adderBudget = std::stoi(argv[++idx]);
                ++idx;
                continue;
            }
            if (token == "--estimator") {
                if (idx + 1 >= argc) {
                    throw std::invalid_argument("--estimator expects a name");
                }
                auto parsed = parseEstimator(argv[++idx]);
                if (!parsed) {
                    throw std::invalid_argument("unknown estimator: " + std::string(argv[idx]));
                }
                estimator = parsed;
                ++idx;
                continue;
            }
            Value value = std::stoll(token);
            if (value <= 0) {
                throw std::invalid_argument("targets must be positive integers");
            }
            targets.push_back(value);
            ++idx;
        }
        if (targets.empty()) {
            throw std::invalid_argument("at least one target constant is required");
        }
        if (!adderBudget.has_value()) {
            if (!estimator.has_value()) {
                throw std::invalid_argument(
                    "either --adder-count or --estimator must be provided");
            }
            InputSpec spec{bitWidth, targets};
            int estimate = estimateAdders(spec, *estimator);
            if (estimate <= 0) {
                throw std::runtime_error("failed to estimate adder budget via " +
                                         estimatorToString(*estimator));
            }
            adderBudget = estimate;
        }
        IlpConfig config{bitWidth, targets, *adderBudget};
        auto ilpResult = runIlpOptimal(config);
        if (!ilpResult.feasible) {
            std::cerr << "ILP solver could not find a solution with " << *adderBudget
                      << " adders\n";
            return 2;
        }
        const auto &solution = ilpResult.solution;
        std::cout << "Algorithm: " << solution.name << "\n";
        std::cout << "Bit-width : " << bitWidth << "\n";
        std::cout << "Adders    : " << solution.operationCount() << " (budget "
                  << *adderBudget << ")\n";
        std::cout << "Targets   : ";
        for (size_t i = 0; i < solution.synthesizedTargets.size(); ++i) {
            if (i != 0) {
                std::cout << ", ";
            }
            std::cout << solution.synthesizedTargets[i];
        }
        std::cout << "\n";
        std::cout << "Operations:\n";
        for (size_t i = 0; i < solution.operations.size(); ++i) {
            std::cout << "  #" << (i + 1) << " " << solution.operations[i].describe() << "\n";
        }
    } catch (const std::exception &ex) {
        std::cerr << "error: " << ex.what() << "\n";
        printUsage(argv[0]);
        return 1;
    }
    return 0;
}
