#ifndef MCM_HPP
#define MCM_HPP

#include <vector>
#include <string>
#include "ortools/linear_solver/linear_solver.h"

namespace operations_research {

struct McmArgs {
    std::vector<int> target_consts;
    double timelimit = 0.0;
    int wIn = 0;
    int wOut = 0;
    bool pipeline = false;
    bool verbose = false;
    bool min_ad = false;
    int nb_adders_start = 0;
    bool use_rpag = false;
    bool use_mcm = false;
    int threads = 0;
    double ws_timelimit = 0.0;
    std::string file_ag = "addergraph.txt";
};

McmArgs parse_args(int argc, char* argv[]);

class McmOptimizer {
public:
    McmOptimizer(const McmArgs& args);
    void Optimize();

private:
    void BuildIlpModel();
    void SolveIlpModel();
    void PrintSolution();

    const McmArgs& args_;
    MPSolver solver_;
    // Add more member variables for the ILP model
};

} // namespace operations_research

#endif // MCM_HPP
