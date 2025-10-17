#ifndef MCM_HPP
#define MCM_HPP

#include <vector>
#include <string>
#include "ortools/linear_solver/linear_solver.h"

namespace operations_research {
    // Data structure to store optimization result
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

    void Build(std::vector<int> target_consts, int NA = 10, int wordlength=16, int Smax=16);
    void PrintSolution();
private:

    MPSolver solver_;
    std::vector<AdderInfo> optimization_result;
};

} // namespace operations_research

#endif // MCM_HPP
