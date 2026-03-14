#include <gtest/gtest.h>
#include "config.hpp"

// Declare the function to test
bool printOnnxModelSummary(const std::string& model_path);

TEST(ONNXTest, PrintModelSummary) {
    // Use the repo-tracked fixture path injected by CMake.
    std::string model_path = TEST_ONNX_MODEL_PATH;
    bool s = printOnnxModelSummary(model_path);
    EXPECT_TRUE(s);
}
