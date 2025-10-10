#include "mcm.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

namespace operations_research {

McmArgs parse_args(int argc, char* argv[]) {
    McmArgs args;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg.find("=") != std::string::npos) {
            std::string key = arg.substr(0, arg.find("="));
            std::string value = arg.substr(arg.find("=") + 1);
            if (key == "timelimit") {
                args.timelimit = std::stod(value);
            } else if (key == "wIn") {
                args.wIn = std::stoi(value);
            } else if (key == "wOut") {
                args.wOut = std::stoi(value);
            } else if (key == "pipeline") {
                args.pipeline = (value == "true");
            } else if (key == "verbose") {
                args.verbose = (value == "true");
            } else if (key == "min_ad") {
                args.min_ad = (value == "true");
            } else if (key == "nb_adders_start") {
                args.nb_adders_start = std::stoi(value);
            } else if (key == "use_rpag") {
                args.use_rpag = (value == "true");
            } else if (key == "use_mcm") {
                args.use_mcm = (value == "true");
            } else if (key == "threads") {
                args.threads = std::stoi(value);
            } else if (key == "ws_timelimit") {
                args.ws_timelimit = std::stod(value);
            } else if (key == "file_ag") {
                args.file_ag = value;
            } else {
                std::cerr << "Unrecognized keyword " << key << " ignored" << std::endl;
            }
        } else {
            args.target_consts.push_back(std::stoi(arg));
        }
    }
    return args;
}

McmOptimizer::McmOptimizer(const McmArgs& args)
    : args_(args),
      solver_("McmSolver", MPSolver::SCIP_MIXED_INTEGER_PROGRAMMING) {
}

void McmOptimizer::Optimize() {
    BuildIlpModel();
    SolveIlpModel();
    PrintSolution();
}

void McmOptimizer::BuildIlpModel() {
    const double infinity = solver_.infinity();

    // This is a C++ translation of the ILP model from ilp1.jl
    // It is a simplified version and does not include all the features.

    // Parameters
    const int NA = 10; // Max number of adders
    const int wordlength = 16; // Wordlength of the constants
    const int Smin = -wordlength;
    const int Smax = wordlength;
    const int NO = args_.target_consts.size();
    const int max_c = *std::max_element(args_.target_consts.begin(), args_.target_consts.end());

    // Variables

    // ca[a]: odd part of the value of adder a
    std::vector<MPVariable*> ca(NA + 1);
    for (int a = 0; a <= NA; ++a) {
        ca[a] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca[" + std::to_string(a) + "]");
    }
    solver_.MakeRowConstraint(1, 1)->SetCoefficient(ca[0], 1); // C1: ca[0] = 1

    // used_adder[a]: 1 if adder a is used
    std::vector<MPVariable*> used_adder(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        used_adder[a] = solver_.MakeBoolVar("used_adder[" + std::to_string(a) + "]");
    }

    // cai[a][i]: odd part of the i-th input to adder a
    std::vector<std::vector<MPVariable*>> cai(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            cai[a][i] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "cai[" + std::to_string(a) + "][" + std::to_string(i) + "]");
        }
    }

    // caik[a][i][k]: 1 if input i of adder a is from adder k
    std::vector<std::vector<std::vector<MPVariable*>>> caik(
        NA + 1, std::vector<std::vector<MPVariable*>>(
            2, std::vector<MPVariable*>(NA + 1)));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            for (int k = 0; k < a; ++k) {
                caik[a][i][k] = solver_.MakeBoolVar(
                    "caik[" + std::to_string(a) + "][" + std::to_string(i) + "][" + std::to_string(k) + "]");
            }
        }
    }

    // oaj[a][j]: 1 if adder a's output is constant j
    std::vector<std::vector<MPVariable*>> oaj(NA + 1, std::vector<MPVariable*>(NO));
    for (int a = 0; a <= NA; ++a) {
        for (int j = 0; j < NO; ++j) {
            oaj[a][j] = solver_.MakeBoolVar("oaj[" + std::to_string(a) + "][" + std::to_string(j) + "]");
        }
    }

    // Constraints

    // C3: An input to an adder must come from a previous adder
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
            for (int k = 0; k < a; ++k) {
                c->SetCoefficient(caik[a][i][k], 1);
            }
        }
    }

    // Link cai and caik
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            for (int k = 0; k < a; ++k) {
                MPConstraint* const c_link1 = solver_.MakeRowConstraint(-infinity, max_c);
                c_link1->SetCoefficient(cai[a][i], 1);
                c_link1->SetCoefficient(ca[k], -1);
                c_link1->SetCoefficient(caik[a][i][k], -max_c);

                MPConstraint* const c_link2 = solver_.MakeRowConstraint(-max_c, infinity);
                c_link2->SetCoefficient(cai[a][i], 1);
                c_link2->SetCoefficient(ca[k], -1);
                c_link2->SetCoefficient(caik[a][i][k], max_c);
            }
        }
    }

    // C6: All target constants must be generated
    for (int j = 0; j < NO; ++j) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        for (int a = 0; a <= NA; ++a) {
            c->SetCoefficient(oaj[a][j], 1);
        }
    }

    // Link ca and oaj
    for (int a = 0; a <= NA; ++a) {
        for (int j = 0; j < NO; ++j) {
            MPConstraint* const c_link1 = solver_.MakeRowConstraint(-infinity, max_c);
            c_link1->SetCoefficient(ca[a], 1);
            c_link1->SetCoefficient(oaj[a][j], -max_c);
            c_link1->SetUB(args_.target_consts[j]);

            MPConstraint* const c_link2 = solver_.MakeRowConstraint(-max_c, infinity);
            c_link2->SetCoefficient(ca[a], 1);
            c_link2->SetCoefficient(oaj[a][j], max_c);
            c_link2->SetLB(args_.target_consts[j]);
        }
    }

    // C2: Adder output is sum of inputs (simplified, no shifts/signs)
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(0, 0);
        c->SetCoefficient(ca[a], 1);
        c->SetCoefficient(cai[a][0], -1);
        c->SetCoefficient(cai[a][1], -1);
    }

    // Objective: Minimize the number of adders used
    MPObjective* const objective = solver_.MutableObjective();
    for (int a = 1; a <= NA; ++a) {
        objective->SetCoefficient(used_adder[a], 1);
    }
    objective->SetMinimization();

    // Link used_adder to ca
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(0, infinity);
        c->SetCoefficient(ca[a], 1);
        c->SetCoefficient(used_adder[a], -max_c);
    }
}

void McmOptimizer::SolveIlpModel() {
    const MPSolver::ResultStatus result_status = solver_.Solve();
    if (result_status != MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution!" << std::endl;
    }
}

void McmOptimizer::PrintSolution() {
    std::cout << "Solution:" << std::endl;
    std::cout << "Objective value = " << solver_.Objective().Value() << std::endl;
}

} // namespace operations_research
