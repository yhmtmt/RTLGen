#include <gtest/gtest.h>
#include <initializer_list>

#include "cmvm.hpp"
#include "mcm_algorithms.hpp"
#include "mcm_ilp.hpp"

using namespace mcm;

TEST(MCMAlgorithms, RAGnBeatsBHMOnSimplePair) {
    InputSpec input{4, {13, 15}};
    auto bhm = runBHM(input);
    auto ragn = runRAGn(input);
    auto hcub = runHCub(input);
    EXPECT_GT(bhm.operationCount(), ragn.operationCount());
    EXPECT_EQ(ragn.operationCount(), hcub.operationCount());
}

TEST(MCMAlgorithms, HCubImprovesOverRAGn) {
    InputSpec input{6, {13, 59}};
    auto ragn = runRAGn(input);
    auto hcub = runHCub(input);
    EXPECT_LT(hcub.operationCount(), ragn.operationCount());
}

TEST(MCMAlgorithms, HCubCanOverbuildComparedToRAGn) {
    InputSpec input{5, {8, 21}};
    auto ragn = runRAGn(input);
    auto hcub = runHCub(input);
    EXPECT_GT(hcub.operationCount(), ragn.operationCount());
}

cse::ProblemInstance makeInstance(std::initializer_list<long long> values) {
    cse::ProblemInstance inst;
    inst.rows = 2;
    inst.cols = 2;
    inst.bitWidth = 4;
    inst.matrix.assign(inst.rows, std::vector<long long>(inst.cols, 0));
    auto it = values.begin();
    for (int r = 0; r < inst.rows; ++r) {
        for (int c = 0; c < inst.cols; ++c) {
            inst.matrix[r][c] = *it++;
        }
    }
    return inst;
}

TEST(CSEAlgorithms, HybridBeatsPureCSE) {
    auto inst = makeInstance({-3, -3, -3, -2});
    auto ctx = cse::buildProblem(inst);
    auto exact = cse::runExactIlp(ctx);
    auto h2 = cse::runH2mc(ctx);
    auto hcmvm = cse::runHCmvm(ctx);
    EXPECT_EQ(exact.totalOperations, h2.totalOperations);
    EXPECT_LT(hcmvm.totalOperations, h2.totalOperations);
    EXPECT_EQ(hcmvm.totalOperations, exact.totalOperations - 1);
}

TEST(MCMIlp, SolvesSimplePairWithBudget) {
    IlpConfig config;
    config.bitWidth = 6;
    config.targets = {13, 59};
    config.adderBudget = 6;
    auto result = runIlpOptimal(config);
    EXPECT_TRUE(result.feasible);
    EXPECT_EQ(result.solution.synthesizedTargets.size(), 2u);
    EXPECT_EQ(result.solution.operations.size(), config.adderBudget);
}

TEST(MCMIlp, SupportsEstimatorDrivenBudget) {
    InputSpec spec{5, {9, 21}};
    int estimate = estimateAdders(spec, AdderEstimator::HCub);
    ASSERT_GT(estimate, 0);
    IlpConfig config{spec.bitWidth, spec.targets, estimate};
    auto result = runIlpOptimal(config);
    EXPECT_TRUE(result.feasible);
}
