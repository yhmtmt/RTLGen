#ifndef BOOLEXP_HPP
#define BOOLEXP_HPP

enum LogicOp{
    AND, OR, XOR, NOT, NAND, NOR, XNOR, ZERO, ONE, NOP // Logical operations
};

 // express the bit of operand
struct OpBit{
    char iop;   // Operand index: 0 for multiplicand, 1 for multiplier
    char neg;   // Negation: 1 if negated, 0 otherwise
    short ibit; // Bit index within the operand
};

// Express the logic function as a tree of operations and variables
struct BoolExp {
    std::string name;
    LogicOp operation;                     // Logical operation
    std::vector<BoolExp*> children;        // Child nodes (sub-expressions) as pointers
    std::vector<OpBit> inputs;             // Operand bits (leaf nodes)

    BoolExp(const std::string &_name, LogicOp op)
        : name(_name), operation(op) {}

    // Constructor for an operation node
    BoolExp(const std::string &_name, LogicOp op, const std::vector<BoolExp*>& childNodes)
        : name(_name), operation(op), children(childNodes) {}

    // Constructor for a leaf node
    BoolExp(const std::string &_name, LogicOp op, const std::vector<OpBit>& in)
        : name(_name), operation(op), inputs(in) {}

    ~BoolExp() {
        // Do not delete children here, as they may be shared
    }

    // Setter for operation
    void setOperation(LogicOp op) {
        operation = op;
    }

    // Setter for children
    void setChildren(const std::vector<BoolExp*>& childNodes) {
        children = childNodes;
    }

    // Setter for inputs
    void setInputs(const std::vector<OpBit>& in) {
        inputs = in;
    }

    // Evaluate the logic function
    bool evaluate(const std::vector<std::vector<bool>>& operandBits) const {
        if (operation == ONE) {
            return true; // Always return true for ONE
        } else if (operation == ZERO) {
            return false; // Always return false for ZERO
        } else if (operation == NOP) {
            return !inputs.empty() ? operandBits[inputs[0].iop][inputs[0].ibit] ^ inputs[0].neg : false; // Return the first input bit
        }

        // Collect results from children and inputs
        std::vector<bool> results;
        for (const auto* child : children) {
            results.push_back(child->evaluate(operandBits));
        }
        for (const auto& bit : inputs) {
            results.push_back(operandBits[bit.iop][bit.ibit] ^ bit.neg);
        }

        // Combine results based on the operation
        return applyOperation(results);
    }


    bool generateAssignments(std::ostream& os, const std::vector<std::string>& operands){
        if (operation == ONE) {
            os << "  assign " << name << " = 1'b1;\n";
            return true;
        } else if (operation == ZERO) {
            os << "  assign " << name << " = 1'b0;\n";
            return true;
        } else if (operation == NOP) {
            os << "  assign " << name << " = ";
            if (inputs.size() == 1){
                os << (inputs[0].neg ? "~" : "") << operands[inputs[0].iop] << "[" << inputs[0].ibit << "];\n";
            }else if (children.size() == 1){
                os << children[0]->name << ";\n";
            }else
            {
                os << "1'b0; // NOP operation not allowed for multiple operands\n";
                return false;
            }
            return true;
        }else if(operation == NOT){
            os << "  assign " << name << " = ";
            if(inputs.size() == 1)
            os << (inputs[0].neg ? "" : "~") << operands[inputs[0].iop] << "[" << inputs[0].ibit << "];\n";
            else if(children.size() == 1)
            os << "~" << children[0]->name << ";\n";
            else{
                os << "1'b0; // NOT operation not allowed for multiple oeprands\n";
                return false;
            }
            return true;
        }

        // Generate the operation assignment
        bool negate = false;
        if(operation == NAND || operation == NOR || operation == XNOR)
            negate = true;

        if (negate)
            os << "  assign " << name << " = ~(";
        else
            os << "  assign " << name << " = ";

        bool first = true;
        for (size_t i = 0; i < children.size(); ++i) {
            if (!first) os << " " << getOperationSymbol(operation) << " ";
            os << children[i]->name;
            first = false;
        }
        for (const auto& bit : inputs) {
            if (!first) os << " " << getOperationSymbol(operation) << " ";
            os << (bit.neg ? "~" : "") << operands[bit.iop] << "[" << bit.ibit << "]";
            first = false;
        }

        if (negate)
            os << ");\n";
        else
            os << ";\n";
        return true;
    }

private:
    // Apply the logical operation to the child results
    bool applyOperation(const std::vector<bool>& childResults) const {
        if (operation == AND) {
            return std::all_of(childResults.begin(), childResults.end(), [](bool v) { return v; });
        } else if (operation == OR) {
            return std::any_of(childResults.begin(), childResults.end(), [](bool v) { return v; });
        } else if (operation == XOR) {
            return std::accumulate(childResults.begin(), childResults.end(), false, std::bit_xor<>());
        } else if (operation == NOT) {
            return !childResults[0];
        }
        // Add other operations as needed
        return false;
    }

    char getOperationSymbol(LogicOp op){
        switch (op) {
            case AND: return '&';
            case OR: return '|';
            case XOR: return '^';
            case NOT: return '~';
            case NAND: return '&'; // NAND is not directly representable in Verilog
            case NOR: return '|';  // NOR is not directly representable in Verilog
            case XNOR: return '^'; // XNOR is not directly representable in Verilog
            case ZERO: return '0';
            case ONE: return '1';
            case NOP: return ' ';  // NOP does not have a direct symbol
            default: return '?';   // Unknown operation
        }
    }
};

class BoolExpManager {
private:
    std::map<std::string, BoolExp*> expressions; // Map to hold BoolExp objects with unique names

public:
    ~BoolExpManager() {
        // Destructor to clean up allocated BoolExp objects
        for (auto& pair : expressions) {
            delete pair.second;
        }
    }

    // Allocate a BoolExp with specified construction arguments
    BoolExp* allocate(const std::string& name, LogicOp operation) {
        if (expressions.find(name) != expressions.end()) {
            return nullptr; // Name already exists, return nullptr
        }
        BoolExp* newExp = new BoolExp(name, operation);
        expressions[name] = newExp;
        return newExp;
    }
    
    // Allocate a BoolExp with specified construction arguments and name
    BoolExp* allocate(const std::string& name, LogicOp operation, const std::vector<BoolExp*>& childNodes) {
        if (expressions.find(name) != expressions.end()) {
            return nullptr; // Name already exists, return nullptr
        }

        BoolExp* newExp = new BoolExp(name, operation, childNodes);
        expressions[name] = newExp;
        return newExp;
    }

    BoolExp* allocate(const std::string& name, LogicOp operation, const std::vector<OpBit>& inputs) {
        if (expressions.find(name) != expressions.end()) {
            return nullptr; // Name already exists, return nullptr
        }

        BoolExp* newExp = new BoolExp(name, operation, inputs);
        expressions[name] = newExp;
        return newExp;
    }

    // Retrieve a BoolExp by name
    BoolExp* get(const std::string& name) const {
        auto it = expressions.find(name);
        return (it != expressions.end()) ? it->second : nullptr;
    }

    // Generate Verilog wires for all managed BoolExp objects
    void generateVerilogWires(std::ostream& os, std::vector<std::string> operands) const {
        for (const auto& pair : expressions) {
            os << "  wire " << pair.first << ";\n";
        }
        for(const auto & pair : expressions) {                
            if (!pair.second->generateAssignments(os, operands)) {
                std::cerr << "Error generating assignment for " << pair.first << std::endl;
            }
        }
    }
};

#endif // BOOLEXP_HPP