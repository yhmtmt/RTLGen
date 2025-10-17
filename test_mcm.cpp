#include "mcm.hpp"
#include "gtest/gtest.h"

namespace operations_research {

class McmOptimizerTest : public ::testing::Test {
protected:
    void SetUp() override {
    }
};

TEST_F(McmOptimizerTest, BuildAndSolve) {
    McmOptimizer optimizer;
    optimizer.Build({3, 5, 7}, 5, 16, 16);
}

} // namespace operations_research
