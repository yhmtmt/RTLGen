#include "mcm.hpp"
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>

namespace operations_research {

void McmOptimizer::Build(std::vector<int> _target_consts, int _NA, int _wordlength, int _Smax)
{
    target_consts = _target_consts;
    NA = _NA;
    wordlength = _wordlength;
    Smax = _Smax;
    
    const double infinity = solver_.infinity();
    // This is a C++ translation of the ILP model from ilp1.jl
    // see Toward the Multiple Constant Multiplication at Minimal Hardware Cost
    // It is a simplified version and does not include all the features.
    
    // Parameters
    const int NO = target_consts.size();
    const int max_c = *std::max_element(target_consts.begin(), target_consts.end());

    // Variables

    // ca[a]: odd part of the value of adder a
    std::vector<MPVariable*> ca(NA + 1);
    for (int a = 0; a <= NA; ++a) {
        ca[a] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca[" + std::to_string(a) + "]");
    }
    solver_.MakeRowConstraint(1, 1)->SetCoefficient(ca[0], 1); // C1: ca[0] = 1

    // ca_nsh[a]: constant obtained in adder a before the negative shifts
    std::vector<MPVariable*> ca_nsh (NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_nsh[a] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca_nsh[" + std::to_string(a) + "]");
    }

    // ca_odd[a]: variable used to ensure ca[a] is odd
    std::vector<MPVariable*> ca_odd(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_odd[a] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca_odd[" + std::to_string(a) + "]");
    }

    // ca_i[a][i]: odd part of the i-th input to adder a
    std::vector<std::vector<MPVariable*>> ca_i(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) { // left and right inputs
            ca_i[a][i] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca_i[" + std::to_string(a) + "][" + std::to_string(i) + "]");
        }
    }

    // ca_l_sh[a]: constant of adder from left input before adder a and after the left shift
    std::vector<MPVariable*> ca_l_sh(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_l_sh[a] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca_l_sh[" + std::to_string(a) + "]");
    }

    // ca_i_sh_sg[a][i]: constant of adder from input i before adder a and after the shift and sign
    std::vector<std::vector<MPVariable*>> ca_i_sh_sg(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            ca_i_sh_sg[a][i] = solver_.MakeIntVar(1, (1 << wordlength) - 1, "ca_i_sh_sg[" + std::to_string(a) + "][" + std::to_string(i) + "]");
        }
    }   

    // phi[a][i]: sign of i input of adder a
    std::vector<std::vector<MPVariable*>> phi(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            phi[a][i] = solver_.MakeBoolVar("phi[" + std::to_string(a) + "][" + std::to_string(i) + "]");
        }
    }   

    // ca_i_k[a][i][k]: 1 if input i of adder a is from adder k
    std::vector<std::vector<std::vector<MPVariable*>>> ca_i_k(
        NA + 1, std::vector<std::vector<MPVariable*>>(
            2, std::vector<MPVariable*>(NA + 1)));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            for (int k = 0; k < a; ++k) {
                ca_i_k[a][i][k] = solver_.MakeBoolVar(
                    "ca_i_k[" + std::to_string(a) + "][" + std::to_string(i) + "][" + std::to_string(k) + "]");
            }
        }
    }

    // sigma[a][s]: 1 if left shift before adder a is s
    std::vector<std::vector<MPVariable*>> sigma(NA + 1, std::vector<MPVariable*>(Smax + 1));
    for (int a = 1; a <= NA; ++a) {
        for (int s = Smax; s <= 0; ++s) {
            sigma[a][-s] = solver_.MakeBoolVar("sigma[" + std::to_string(a) + "][" + std::to_string(s) + "]");
        }
    }   

    // psi[a][s]: 1 if negative shift of adder a is equal to s
    std::vector<std::vector<MPVariable*>> psi(NA + 1, std::vector<MPVariable*>(Smax + 1));
    for (int a = 1; a <= NA; ++a) {
        for (int s = -Smax; s <= 0; ++s) {
            psi[a][-s] = solver_.MakeBoolVar("psi[" + std::to_string(a) + "][" + std::to_string(s) + "]");
        }
    }   

    // oaj[a][j]: 1 if adder a's output is constant j
    std::vector<std::vector<MPVariable*>> oaj(NA + 1, std::vector<MPVariable*>(NO));
    for (int a = 0; a <= NA; ++a) {
        for (int j = 0; j < NO; ++j) {
            oaj[a][j] = solver_.MakeBoolVar("oaj[" + std::to_string(a) + "][" + std::to_string(j) + "]");
        }
    }

    // used_adder[a]: 1 if adder a is used
    std::vector<MPVariable*> used_adder(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        used_adder[a] = solver_.MakeBoolVar("used_adder[" + std::to_string(a) + "]");
    }

    // Constraints
    // C1: ca_nsh[a] = ca_i_sh_sg[a][0] + ca_i_sh_sg[a][1]
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(0, 0);
        c->SetCoefficient(ca_nsh[a], 1);
        c->SetCoefficient(ca_i_sh_sg[a][0], -1);
        c->SetCoefficient(ca_i_sh_sg[a][1], -1);
    }

    // C2: ca_nsh[a] = 2^(-s) * ca[a] if psi[a][s] = 1 where a in [1, NA] and s in [-Smax,0]
    for (int a = 1; a <= NA; ++a) {
        for (int s = -Smax; s <= 0; ++s) {
            // -inf <= ca_nsh[a] - 2^(-s) * ca[a] - M * (1 - psi[a][s]) <=0
            MPConstraint* const c = solver_.MakeRowConstraint(-infinity, max_c);
            c->SetCoefficient(ca_nsh[a], 1);
            c->SetCoefficient(ca[a], -(1 << -s));
            c->SetCoefficient(psi[a][-s], max_c);
        }
    }

    // C3: sum_s psi[a][s] = 1 for each adder a
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        for (int s = -Smax; s <= 0; ++s) {
            c->SetCoefficient(psi[a][-s], 1);
        }
    }

    // C4: sigma[a][0] = sum_s={-Smax..-1} psi[a][s] for each adder a
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(0, 0);
        c->SetCoefficient(sigma[a][0], 1);
        for (int s = -Smax; s <= -1; ++s) {
            c->SetCoefficient(psi[a][-s], -1);
        }
    }

    // C5: ca[a] = 2*ca_odd[a] + 1 for each adder a
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        c->SetCoefficient(ca[a], 1);
        c->SetCoefficient(ca_odd[a], -2);
    }
 
    // C6: ca_i[a][i] = c[k] if ca_i_k[a][i][k] = 1 where a in [1, NA], i in [0,1], k in [0,a-1]
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            for (int k = 0; k < a; ++k) {
                // -inf <= ca_i[a][i] - ca[k] - M * (1 - ca_i_k[a][i][k]) <=0
                MPConstraint* const c = solver_.MakeRowConstraint(-infinity, max_c);
                c->SetCoefficient(ca_i[a][i], 1);
                c->SetCoefficient(ca[k], -1);
                c->SetCoefficient(ca_i_k[a][i][k], max_c);
            }
        }
    }

    // C7: sum_k ca_i_k[a][i][k] = 1 for each adder a and input i
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
            for (int k = 0; k < a; ++k) {
                c->SetCoefficient(ca_i_k[a][i][k], 1);
            }
        }
    }

    // C8: ca_l_sh[a] = 2^s * ca_i[a][0] if sigma[a][s] = 1 where a in [1, NA] and s in [0,Smax]
    for (int a = 1; a <= NA; ++a) {
        for (int s = 0; s <= Smax; ++s) {
            // -inf <= ca_l_sh[a] - 2^s * ca_i[a][0] - M * (1 - sigma[a][s]) <=0
            MPConstraint* const c = solver_.MakeRowConstraint(-infinity, max_c);
            c->SetCoefficient(ca_l_sh[a], 1);
            c->SetCoefficient(ca_i[a][0], -(1 << s));
            c->SetCoefficient(sigma[a][s], max_c);
        }
    }

    // C9: sum_s sigma[a][s] = 1 for each adder a
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        for (int s = 0; s <= Smax; ++s) {
            c->SetCoefficient(sigma[a][s], 1);
        }
    }

    // C10,11: ca_i_sh_sg[a][0] = ca_l_sh[a] if phi[a][0] = 0 and ca_i_sh_sg[a][0] = -ca_l_sh[a] if phi[a][0] = 1 for each adder a
    //         ca_i_sh_sg[a][1] = ca_i[a][1] if phi[a][1] = 0 and ca_i_sh_sg[a][1] = -ca_i[a][1] if phi[a][1] = 1 for each adder a
    for (int a = 1; a <= NA; ++a) {
        // -inf <= ca_i_sh_sg[a][0] - ca_l_sh[a] - M * (1 - phi[a][0]) <=0
        MPConstraint* const c1 = solver_.MakeRowConstraint(-infinity, max_c);
        c1->SetCoefficient(ca_i_sh_sg[a][0], 1);
        c1->SetCoefficient(ca_l_sh[a], -1);
        c1->SetCoefficient(phi[a][0], max_c);
        // -inf <= ca_i_sh_sg[a][0] + ca_l_sh[a] - M * phi[a][0] <=0
        MPConstraint* const c2 = solver_.MakeRowConstraint(-infinity, 0);
        c2->SetCoefficient(ca_i_sh_sg[a][0], 1);
        c2->SetCoefficient(ca_l_sh[a], 1);
        c2->SetCoefficient(phi[a][0], -max_c);

        // -inf <= ca_i_sh_sg[a][1] - ca_i[a][1] - M *(1 - phi[a][1]) <=0
        MPConstraint* const c3 = solver_.MakeRowConstraint(-infinity, max_c);
        c3->SetCoefficient(ca_i_sh_sg[a][1], 1);
        c3->SetCoefficient(ca_i[a][1], -1);
        c3->SetCoefficient(phi[a][1], max_c);
        // -inf <= ca_i_sh_sg[a][1] + ca_i[a][1] - M * phi[a][1] <=0
        MPConstraint* const c4 = solver_.MakeRowConstraint(-infinity, 0);
        c4->SetCoefficient(ca_i_sh_sg[a][1], 1);
        c4->SetCoefficient(ca_i[a][1], 1);
        c4->SetCoefficient(phi[a][1], -max_c);
    }

    // C12: ca[a] = Cj if oaj[a][j] = 1 where a in [0, NA] and j in [0, NO-1]
    for (int a = 0; a <= NA; ++a) {
        for (int j = 0; j < NO; ++j) {
            // -inf <= ca[a] - target_consts[j] - M * (1 - oaj[a][j]) <=0
            MPConstraint* const c = solver_.MakeRowConstraint(-infinity, max_c);
            c->SetCoefficient(ca[a], 1);
            c->SetCoefficient(oaj[a][j], max_c);
            c->SetUB(target_consts[j]);
        }
    }

    // C13: All target constants must be generated
    for (int j = 0; j < NO; ++j) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        for (int a = 0; a <= NA; ++a) {
            c->SetCoefficient(oaj[a][j], 1);
        }
    }

    // Link used_adder to ca
    for (int a = 1; a <= NA; ++a) {
        MPConstraint* const c = solver_.MakeRowConstraint(-infinity, 0);
        c->SetCoefficient(ca[a], 1);
        c->SetCoefficient(used_adder[a], -max_c);
    }

    // Objective: Minimize the number of adders used
    MPObjective* const objective = solver_.MutableObjective();
    for (int a = 1; a <= NA; ++a) {
        objective->SetCoefficient(used_adder[a], 1);
    }
    objective->SetMinimization();

    const MPSolver::ResultStatus result_status = solver_.Solve();
    if (result_status != MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution!" << std::endl;
        return;
    }

    optimization_result.clear();

    // extract adder graph structure. 
    // ca[a], ca_i_k[a][i][k], phi[a][i], sigma[a][s], psi[a][s], used_adder[a]
    for (int a = 1; a <= NA; ++a) {
        if (used_adder[a]->solution_value() > 0.5) {
            AdderInfo info;
            info.index = a;
            info.ca = static_cast<int>(ca[a]->solution_value());
            info.input_adders.clear();
            info.input_signs.clear();
            for (int i = 0; i < 2; ++i) {
                for (int k = 0; k < a; ++k) {
                    if (ca_i_k[a][i][k]->solution_value() > 0.5) {
                        info.input_adders.push_back(k);
                    }
                }
                info.input_signs.push_back(phi[a][i]->solution_value() > 0.5 ? '-' : '+');
            }
            info.left_shift = -1;
            for (int s = 0; s <= Smax; ++s) {
                if (sigma[a][s]->solution_value() > 0.5) {
                    info.left_shift = s;
                }
            }
            info.negative_shift = 0;
            for (int s = -Smax; s <= 0; ++s) {
                if (psi[a][-s]->solution_value() > 0.5) {
                    info.negative_shift = s;
                }
            }
            optimization_result.push_back(info);

            // Print for debug
            std::cout << "Adder " << a << ": ca = " << info.ca << ", inputs: ";
            for (size_t idx = 0; idx < info.input_adders.size(); ++idx) {
                std::cout << "from adder " << info.input_adders[idx] << " sign: " << info.input_signs[idx] << " ";
            }
            std::cout << "left shift: " << info.left_shift << " ";
            std::cout << "negative shift: " << info.negative_shift << std::endl;
        }
    }
}

bool McmOptimizer::GenerateVerilog(const std::string& module_name) {
    if (optimization_result.empty()) {
        std::cerr << "[ERROR] No optimization result found. Run Build() first." << std::endl;
        return false;
    }

    std::ofstream verilog_file(module_name + ".v");
    if (!verilog_file.is_open()) {
        std::cerr << "[ERROR] Cannot open file for writing: " << module_name << ".v" << std::endl;
        return false;
    }

    // Use stored parameters for input/output width
    int input_width = wordlength;
    int output_width = wordlength;

    verilog_file << "`timescale 1ns/1ps\n";
    verilog_file << "module " << module_name << "(input wire [" << input_width-1 << ":0] x, output wire [" << output_width-1 << ":0] y);\n";
    verilog_file << "    // Constant multiplier generated by McmOptimizer\n";

    // Declare intermediate wires for each adder
    for (const auto& info : optimization_result) {
        verilog_file << "    wire [" << output_width-1 << ":0] a" << info.index << ";\n";
    }
    verilog_file << "\n";

    // Generate logic for each adder
    for (const auto& info : optimization_result) {
        std::string left_expr, right_expr;
        // Left input
        if (info.input_adders.size() > 0) {
            left_expr = "a" + std::to_string(info.input_adders[0]);
        } else {
            left_expr = "x";
        }
        if (info.left_shift > 0)
            left_expr = "(" + left_expr + " << " + std::to_string(info.left_shift) + ")";
        // Right input
        if (info.input_adders.size() > 1) {
            right_expr = "a" + std::to_string(info.input_adders[1]);
        } else {
            right_expr = "x";
        }

        // Signs
        if (info.input_signs.size() > 0 && info.input_signs[0] == '-')
            left_expr = "-" + left_expr;
        if (info.input_signs.size() > 1 && info.input_signs[1] == '-')
            right_expr = "-" + right_expr;

        std::string negative_shift_str = "";
        if (info.negative_shift < 0)
            negative_shift_str = " >> " + std::to_string(-info.negative_shift);

        verilog_file << "    assign a" << info.index << " =" << "(" << left_expr << " + " << right_expr << ")"
                     << negative_shift_str << "; // ca = " << info.ca << "\n";
    }

    // Output assignment: connect last adder to output, or use ca directly if only one
    if (!optimization_result.empty()) {
        verilog_file << "    assign y = a" << optimization_result.back().index << ";\n";
    } else {
        verilog_file << "    assign y = x;\n";
    }

    verilog_file << "endmodule\n";
    verilog_file.close();

    std::cout << "[INFO] Verilog file generated: " << module_name << ".v" << std::endl;
    return true;
}

void McmOptimizer::PrintSolution() {
    std::cout << "Solution:" << std::endl;
    std::cout << "Objective value = " << solver_.Objective().Value() << std::endl;
    for (const auto& info : optimization_result) {
        std::cout << "Adder " << info.index << ": ca = " << info.ca << ", inputs: ";
        for (size_t idx = 0; idx < info.input_adders.size(); ++idx) {
            std::cout << "from adder " << info.input_adders[idx] << " sign: " << info.input_signs[idx] << " ";
        }
        std::cout << "left shift: " << info.left_shift << " ";
        std::cout << "negative shift: " << info.negative_shift << std::endl;
    }
}

} // namespace operations_research
