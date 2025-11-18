#include "cmvm.hpp"

#include <iostream>
#include <stdexcept>

int main(int argc, char **argv) {
    using namespace cse;
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0]
                  << " <rows> <cols> <bitwidth> <matrix values...>\n";
        return 1;
    }
    try {
        int rows = std::stoi(argv[1]);
        int cols = std::stoi(argv[2]);
        int bitWidth = std::stoi(argv[3]);
        if (rows <= 0 || cols <= 0 || bitWidth <= 0) {
            throw std::invalid_argument("dimensions and bitwidth must be positive");
        }
        const int expected = rows * cols;
        if (argc != 4 + expected) {
            throw std::invalid_argument("insufficient matrix values supplied");
        }
        ProblemInstance instance;
        instance.rows = rows;
        instance.cols = cols;
        instance.bitWidth = bitWidth;
        instance.matrix.assign(rows, std::vector<long long>(cols, 0));
        int cursor = 4;
        for (int r = 0; r < rows; ++r) {
            for (int c = 0; c < cols; ++c) {
                instance.matrix[r][c] = std::stoll(argv[cursor++]);
            }
        }
        auto context = buildProblem(instance);
        auto baseline = computeNaiveCost(context.expressions);
        std::cout << "Baseline naive operations: " << baseline << "\n\n";
        const auto exact = runExactIlp(context);
        const auto h2mc = runH2mc(context);
        const auto hcmvm = runHCmvm(context);
        const AlgorithmResult results[] = {exact, h2mc, hcmvm};
        for (const auto &res : results) {
            std::cout << "Algorithm: " << res.name << "\n";
            std::cout << "  Subexpressions : " << res.subexpressionCount << "\n";
            std::cout << "  Total Ops      : " << res.totalOperations << "\n";
            if (!res.notes.empty()) {
                std::cout << "  Note          : " << res.notes << "\n";
            }
            std::cout << '\n';
        }
    } catch (const std::exception &ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }
    return 0;
}
