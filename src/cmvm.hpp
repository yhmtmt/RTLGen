#pragma once

#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace cse {

struct TermInstance {
    int signal{0};
    int sign{1};
};

struct TermType {
    int signal{0};
    int sign{1};
    bool operator==(const TermType &other) const {
        return signal == other.signal && sign == other.sign;
    }
    bool operator<(const TermType &other) const {
        if (signal != other.signal) {
            return signal < other.signal;
        }
        return sign < other.sign;
    }
};

struct PairKey {
    TermType a;
    TermType b;
    PairKey();
    PairKey(const TermType &lhs, const TermType &rhs);
    bool operator==(const PairKey &other) const;
    bool operator<(const PairKey &other) const;
};

struct Signal {
    int id{0};
    std::vector<long long> coeffs;
    std::string label;
    int left{-1};
    int right{-1};
    int leftSign{1};
    int rightSign{1};
};

class SignalTable {
  public:
    explicit SignalTable(int numInputs, int bitWidth);
    int ensureBaseSignal(int input, int shift);
    int createCompositeSignal(const TermType &lhs, const TermType &rhs);
    const Signal &get(int id) const;
    Signal &get(int id);
    int numInputs() const { return numInputs_; }
    int bitWidth() const { return bitWidth_; }
    int maxShift() const { return maxShift_; }
    void updateMaxShift(int shift);
    int allocateId();
    const std::vector<Signal> &signals() const { return signals_; }

  private:
    int numInputs_{0};
    int bitWidth_{0};
    int maxShift_{0};
    int nextId_{0};
    std::vector<Signal> signals_;
    std::map<std::pair<int, int>, int> baseIndex_;
};

class Expression {
  public:
    Expression() = default;
    explicit Expression(int id) : outputIndex_(id) {}

    void addTerm(int signalId, int sign);
    bool removeTerm(const TermType &term);
    int termCount() const;
    std::map<TermType, int> histogram() const;
    const std::vector<TermInstance> &terms() const { return terms_; }
    std::vector<long long> coefficients(const SignalTable &table) const;
    int outputIndex() const { return outputIndex_; }
    void setOutputIndex(int idx) { outputIndex_ = idx; }

  private:
    std::vector<TermInstance> terms_;
    int outputIndex_{-1};
};

struct DifferenceRelation {
    int target{-1};
    int reference{-1};
};

struct AlgorithmResult {
    std::string name;
    int subexpressionCount{0};
    int totalOperations{0};
    bool optimal{false};
    std::string notes;
};

struct PairUsage {
    int usage{0};
    std::vector<int> expressions;
};

struct ProblemInstance {
    int rows{0};
    int cols{0};
    int bitWidth{0};
    std::vector<std::vector<long long>> matrix;
};

struct ProblemContext {
    SignalTable table;
    std::vector<Expression> expressions;
    ProblemContext(int numInputs, int bitWidth);
};

struct CmvmSynthesisOptions {
    std::string algorithm{"HCMVM"};
    bool differenceRows{false};
    int maxPairSearch{0};
    std::optional<std::string> fallbackAlgorithm;
};

struct CmvmSynthesisOutcome {
    AlgorithmResult stats;
    ProblemContext context;
    std::vector<DifferenceRelation> relations;
};

ProblemContext buildProblem(const ProblemInstance &instance);
int computeNaiveCost(const std::vector<Expression> &expressions);

AlgorithmResult runExactIlp(const ProblemContext &base);
AlgorithmResult runH2mc(const ProblemContext &base);
AlgorithmResult runHCmvm(const ProblemContext &base);
CmvmSynthesisOutcome synthesizeCmvm(const ProblemInstance &instance,
                                    const CmvmSynthesisOptions &options);

} // namespace cse
