#include "mcm_algorithms.hpp"

#include <exception>
#include <functional>
#include <iostream>
#include <stdexcept>

int main(int argc, char **argv) {
    using namespace mcm;
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0]
                  << " <bitwidth> <target1> [target2 ...]\n";
        return 1;
    }
    try {
        int bitWidth = std::stoi(argv[1]);
        if (bitWidth <= 0) {
            throw std::invalid_argument("bitwidth must be positive");
        }
        std::vector<Value> targets;
        for (int i = 2; i < argc; ++i) {
            Value value = std::stoll(argv[i]);
            if (value <= 0) {
                throw std::invalid_argument("targets must be positive integers");
            }
            targets.push_back(value);
        }
        InputSpec input{bitWidth, targets};
        std::vector<std::function<Solution(const InputSpec &)>> runners = {
            runBHA, runBHM, runRAGn, runHCub};
        for (const auto &runner : runners) {
            Solution sol = runner(input);
            std::cout << "Algorithm: " << sol.name << "\n";
            std::cout << "  Operations : " << sol.operationCount() << "\n";
            std::cout << "  Synthesized: ";
            if (sol.synthesizedTargets.empty()) {
                std::cout << "(none)";
            } else {
                bool first = true;
                for (Value v : sol.synthesizedTargets) {
                    if (!first) {
                        std::cout << ", ";
                    }
                    first = false;
                    std::cout << v;
                }
            }
            std::cout << "\n\n";
        }
    } catch (const std::exception &ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }
    return 0;
}
