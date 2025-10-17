#ifndef MCM_HPP
#define MCM_HPP

#include <vector>
#include <string>
#include "ortools/linear_solver/linear_solver.h"

namespace operations_research {

class McmOptimizer {
public:
    McmOptimizer() : solver_("MCM_Solver", MPSolver::CBC_MIXED_INTEGER_PROGRAMMING) {}

    void Build(std::vector<int> target_consts, int NA = 10, int wordlength=16, int Smax=16);
    void PrintSolution();
private:
    MPSolver solver_;
    // Add more member variables for the ILP model
};

} // namespace operations_research

#endif // MCM_HPP
