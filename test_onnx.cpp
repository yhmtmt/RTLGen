#include <gtest/gtest.h>
#include "config.hpp"

// Declare the function to test
bool printOnnxModelSummary(const std::string& model_path);

TEST(ONNXTest, PrintModelSummary) {
    // Provide a path to a small ONNX model for testing
    std::string model_path = "../test_model.onnx";
    // You should place a valid ONNX model file named test_model.onnx in the workspace for this test
    bool s = printOnnxModelSummary(model_path);
    EXPECT_TRUE(s);
}