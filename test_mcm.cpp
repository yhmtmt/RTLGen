#include "mcm.hpp"
#include "gtest/gtest.h"

namespace operations_research {

class McmOptimizerTest : public ::testing::Test {
protected:
    void SetUp() override {
        const char* argv[] = {"test_mcm", "5", "11"};
        args_ = parse_args(3, const_cast<char**>(argv));
    }

    McmArgs args_;
};

TEST_F(McmOptimizerTest, BuildAndSolve) {
    McmOptimizer optimizer(args_);
    optimizer.Optimize();
}

} // namespace operations_research
