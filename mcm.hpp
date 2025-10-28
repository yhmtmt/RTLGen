#ifndef MCM_HPP
#define MCM_HPP

#include <vector>
#include <string>
#include <map>
#include "ortools/linear_solver/linear_solver.h"

namespace operations_research {

struct AdderInfo {
    int index;
    int ca;
    std::vector<int> input_adders;
    std::vector<char> input_signs;
    int left_shift;
    int negative_shift;
};

class McmOptimizer {
public:
    McmOptimizer() : solver_("MCM_Solver", MPSolver::CBC_MIXED_INTEGER_PROGRAMMING) {}

    void Build(std::vector<int> _target_consts, int _NA, int _wordlength, int _Smax);
    bool GenerateVerilog(const std::string& module_name);
    void PrintSolution();

    // Accessor for optimization_result
    const std::vector<AdderInfo>& GetOptimizationResult() const {
        return optimization_result;
    }

private:
    MPSolver solver_;
    std::vector<int> target_consts;
    int NA;
    int wordlength;
    int Smax;

    std::vector<AdderInfo> optimization_result;
    std::map<int, int> output_map; // Map from target_const to adder index

    bool select_best_adders(int NO, std::vector<operations_research::MPVariable *> &ca,
                            std::vector<std::vector<std::vector<operations_research::MPVariable *>>> &ca_i_k,
                            std::vector<std::vector<MPVariable *>> &sigma,
                            std::vector<std::vector<MPVariable *>> &psi,
                            std::vector<std::vector<MPVariable *>> &phi);
};

} // namespace operations_research

#endif // MCM_HPP
