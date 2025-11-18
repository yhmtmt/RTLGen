#include <gtest/gtest.h>
#include "multiplier.hpp"

TEST(BoolExpTest, EvaluateLeafNode) {
    // Test a leaf node with a single input
    OpBit input = {0, 0, 0}; // Operand index 0, no negation, bit index 0
    BoolExp leafNode("leaf_and", AND, std::vector<OpBit>{input}); // Fix constructor usage

    std::vector<std::vector<bool>> operandBits = {{true, false, true}}; // Operand 0: 101
    EXPECT_TRUE(leafNode.evaluate(operandBits));
}

TEST(BoolExpTest, EvaluateOperationNode) {
    // Test an operation node with child nodes
    OpBit input1 = {0, 0, 0}; // Operand index 0, no negation, bit index 0
    OpBit input2 = {0, 0, 1}; // Operand index 0, no negation, bit index 1

    BoolExp child1("child1_and", AND, std::vector<OpBit>{input1});
    BoolExp child2("child2_and", AND, std::vector<OpBit>{input2});

    BoolExp parentNode("parent_or", OR, std::vector<BoolExp*>{&child1, &child2}); // Explicitly specify the type

    std::vector<std::vector<bool>> operandBits = {{true, false, true}}; // Operand 0: 101
    EXPECT_TRUE(parentNode.evaluate(operandBits));
}

TEST(BoolExpTest, EvaluateComplexExpression) {
    // Test a more complex expression
    OpBit input1 = {0, 0, 0}; // Operand index 0, no negation, bit index 0
    OpBit input2 = {0, 0, 1}; // Operand index 0, no negation, bit index 1
    OpBit input3 = {0, 0, 2}; // Operand index 0, no negation, bit index 2

    BoolExp child1("child1_and", AND, std::vector<OpBit>{input1});
    BoolExp child2("child2_and", AND, std::vector<OpBit>{input2});
    BoolExp child3("child3_and", AND, std::vector<OpBit>{input3});

    BoolExp intermediateNode("intermediate_xor", XOR, std::vector<BoolExp*>{&child1, &child2}); // Explicitly specify the type
    BoolExp rootNode("root_or", OR, std::vector<BoolExp*>{&intermediateNode, &child3}); // Explicitly specify the type

    std::vector<std::vector<bool>> operandBits = {{true, false, true}}; // Operand 0: 101
    EXPECT_TRUE(rootNode.evaluate(operandBits));
}

TEST(BoolExpTest, EvaluateNegatedInput) {
    // Test a negated input
    OpBit input = {0, 1, 0}; // Operand index 0, negated, bit index 0
    BoolExp leafNode("negated_and", AND, {input});

    std::vector<std::vector<bool>> operandBits = {{true, false, true}}; // Operand 0: 101
    EXPECT_FALSE(leafNode.evaluate(operandBits));
}
