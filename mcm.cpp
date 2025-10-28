#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include "mcm.hpp"

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

    if(wordlength >= 64) {
        std::cerr << "[ERROR] wordlength too large, must be less than 64." << std::endl;
        return;
    }
    unsigned long long ub_adder = (1ULL << wordlength) - 1;

    // ca[a]: odd part of the value of adder a
    std::vector<MPVariable*> ca(NA + 1);
    for (int a = 0; a <= NA; ++a) {
        ca[a] = solver_.MakeIntVar(1, ub_adder, "ca[" + std::to_string(a) + "]");
    }
    solver_.MakeRowConstraint(1, 1)->SetCoefficient(ca[0], 1); // C1: ca[0] = 1

    // ca_nsh[a]: constant obtained in adder a before the negative shifts
    std::vector<MPVariable*> ca_nsh (NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_nsh[a] = solver_.MakeIntVar(1, ub_adder, "ca_nsh[" + std::to_string(a) + "]");
    }

    // ca_odd[a]: variable used to ensure ca[a] is odd
    std::vector<MPVariable*> ca_odd(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_odd[a] = solver_.MakeIntVar(1, ub_adder, "ca_odd[" + std::to_string(a) + "]");
    }

    // ca_i[a][i]: odd part of the i-th input to adder a
    std::vector<std::vector<MPVariable*>> ca_i(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) { // left and right inputs
            ca_i[a][i] = solver_.MakeIntVar(1, ub_adder, "ca_i[" + std::to_string(a) + "][" + std::to_string(i) + "]");
        }
    }

    // ca_l_sh[a]: constant of adder from left input before adder a and after the left shift
    std::vector<MPVariable*> ca_l_sh(NA + 1);
    for (int a = 1; a <= NA; ++a) {
        ca_l_sh[a] = solver_.MakeIntVar(1, ub_adder, "ca_l_sh[" + std::to_string(a) + "]");
    }

    // ca_i_sh_sg[a][i]: constant of adder from input i before adder a and after the shift and sign
    std::vector<std::vector<MPVariable*>> ca_i_sh_sg(NA + 1, std::vector<MPVariable*>(2));
    for (int a = 1; a <= NA; ++a) {
        for (int i = 0; i < 2; ++i) {
            ca_i_sh_sg[a][i] = solver_.MakeIntVar(-(double)ub_adder, ub_adder, "ca_i_sh_sg[" + std::to_string(a) + "][" + std::to_string(i) + "]");
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
        for (int s = -Smax; s <= 0; ++s) {
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
            MPConstraint* const cp = solver_.MakeRowConstraint(-infinity, max_c << -s);
            cp->SetCoefficient(ca_nsh[a], 1);
            cp->SetCoefficient(ca[a], -(1 << -s));
            cp->SetCoefficient(psi[a][-s], max_c << -s);
            // -inf <= -ca_nsh[a] + 2^(-s) * ca[a] - M * (1 - psi[a][s]) <=0
            MPConstraint* const cn = solver_.MakeRowConstraint(-infinity, max_c << -s);
            cn->SetCoefficient(ca_nsh[a], -1);
            cn->SetCoefficient(ca[a], (1 << -s));
            cn->SetCoefficient(psi[a][-s], max_c << -s);
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
                MPConstraint* const cp = solver_.MakeRowConstraint(-infinity, max_c);
                cp->SetCoefficient(ca_i[a][i], 1);
                cp->SetCoefficient(ca[k], -1);
                cp->SetCoefficient(ca_i_k[a][i][k], max_c);
                // -inf <= -ca_i[a][i] + ca[k] - M * (1 - ca_i_k[a][i][k]) <=0
                MPConstraint* const cn = solver_.MakeRowConstraint(-infinity, max_c);
                cn->SetCoefficient(ca_i[a][i], -1);
                cn->SetCoefficient(ca[k], 1);
                cn->SetCoefficient(ca_i_k[a][i][k], max_c);
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
            MPConstraint* const cp = solver_.MakeRowConstraint(-infinity, max_c << s);
            cp->SetCoefficient(ca_l_sh[a], 1);
            cp->SetCoefficient(ca_i[a][0], -(1 << s));
            cp->SetCoefficient(sigma[a][s], max_c << s);
            // -inf <= -ca_l_sh[a] + 2^s * ca_i[a][0] - M * (1 - sigma[a][s]) <=0
            MPConstraint* const cn = solver_.MakeRowConstraint(-infinity, max_c << s);
            cn->SetCoefficient(ca_l_sh[a], -1);
            cn->SetCoefficient(ca_i[a][0], (1 << s));
            cn->SetCoefficient(sigma[a][s], max_c << s);
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
        // -inf <= ca_i_sh_sg[a][0] - ca_l_sh[a] - M phi[a][0] <=0
        MPConstraint* const c1p = solver_.MakeRowConstraint(-infinity, 0);
        c1p->SetCoefficient(ca_i_sh_sg[a][0], 1);
        c1p->SetCoefficient(ca_l_sh[a], -1);
        c1p->SetCoefficient(phi[a][0], -(max_c << 1));

        // -inf <= -ca_i_sh_sg[a][0] + ca_l_sh[a] - M * phi[a][0] <=0
        MPConstraint* const c1n = solver_.MakeRowConstraint(-infinity, 0);
        c1n->SetCoefficient(ca_i_sh_sg[a][0], -1);
        c1n->SetCoefficient(ca_l_sh[a], 1);
        c1n->SetCoefficient(phi[a][0], -(max_c << 1));

        // -inf <= ca_i_sh_sg[a][0] + ca_l_sh[a] - M * (1 -phi[a][0]) <=0
        MPConstraint* const c2p = solver_.MakeRowConstraint(-infinity, (max_c << 1));
        c2p->SetCoefficient(ca_i_sh_sg[a][0], 1);
        c2p->SetCoefficient(ca_l_sh[a], 1);
        c2p->SetCoefficient(phi[a][0], (max_c << 1));

        // -inf <= -ca_i_sh_sg[a][0] - ca_l_sh[a] - M * (1 -phi[a][0]) <=0
        MPConstraint* const c2n = solver_.MakeRowConstraint(-infinity, (max_c << 1));
        c2n->SetCoefficient(ca_i_sh_sg[a][0], -1);
        c2n->SetCoefficient(ca_l_sh[a], -1);
        c2n->SetCoefficient(phi[a][0], (max_c << 1));

        // -inf <= ca_i_sh_sg[a][1] - ca_i[a][1] - M * phi[a][1] <=0
        MPConstraint* const c3p = solver_.MakeRowConstraint(-infinity, 0);
        c3p->SetCoefficient(ca_i_sh_sg[a][1], 1);
        c3p->SetCoefficient(ca_i[a][1], -1);
        c3p->SetCoefficient(phi[a][1], -(max_c << 1));

        // -inf <= -ca_i_sh_sg[a][1] + ca_i[a][1] - M * phi[a][1] <=0
        MPConstraint* const c3n = solver_.MakeRowConstraint(-infinity, 0);
        c3n->SetCoefficient(ca_i_sh_sg[a][1], -1);
        c3n->SetCoefficient(ca_i[a][1], 1);
        c3n->SetCoefficient(phi[a][1], -(max_c << 1));

        // -inf <= ca_i_sh_sg[a][1] + ca_i[a][1] - M * (1-phi[a][1]) <=0
        MPConstraint* const c4p = solver_.MakeRowConstraint(-infinity, (max_c << 1));
        c4p->SetCoefficient(ca_i_sh_sg[a][1], 1);
        c4p->SetCoefficient(ca_i[a][1], 1);
        c4p->SetCoefficient(phi[a][1], (max_c << 1));

        // -inf <= -ca_i_sh_sg[a][1] + -ca_i[a][1] - M * (1-phi[a][1]) <=0
        MPConstraint* const c4n = solver_.MakeRowConstraint(-infinity, (max_c << 1));
        c4n->SetCoefficient(ca_i_sh_sg[a][1], -1);
        c4n->SetCoefficient(ca_i[a][1], -1);
        c4n->SetCoefficient(phi[a][1], (max_c << 1));
    }

    // C12: ca[a] = Cj if oaj[a][j] = 1 where a in [0, NA] and j in [0, NO-1]
    for (int a = 0; a <= NA; ++a) {
        for (int j = 0; j < NO; ++j) {
            // -inf <= ca[a] - target_consts[j] - M * (1 - oaj[a][j]) <=0
            MPConstraint* const cp = solver_.MakeRowConstraint(-infinity, max_c + target_consts[j]);
            cp->SetCoefficient(ca[a], 1);
            cp->SetCoefficient(oaj[a][j], max_c);

            // -inf <= -ca[a] + target_consts[j] - M * (1 - oaj[a][j]) <=0
            MPConstraint* const cn = solver_.MakeRowConstraint(-infinity, max_c - target_consts[j]);
            cn->SetCoefficient(ca[a], -1);
            cn->SetCoefficient(oaj[a][j], max_c);
        }
    }

    // C13: All target constants must be generated
    for (int j = 0; j < NO; ++j) {
        MPConstraint* const c = solver_.MakeRowConstraint(1, 1);
        for (int a = 0; a <= NA; ++a) {
            c->SetCoefficient(oaj[a][j], 1);
        }
    }

    MPObjective* const objective = solver_.MutableObjective();
    objective->SetMinimization();

    std::string model_str; 
    if(solver_.ExportModelAsLpFormat(false, &model_str)){
        // save to file for inspection. file name should be parameterized with the argument of this function.
        std::ofstream model_file("mcm_model.lp");
        model_file << model_str;
        model_file.close();
    }

    const MPSolver::ResultStatus result_status = solver_.Solve();
    if (result_status != MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution!" << std::endl;
        return;
    }

    optimization_result.clear();
    output_map.clear();

    // determine adders used to minimize the number of adders. for all constants, select adders to minimize the number of adders used.
    // select adders that produce target constants
    std::vector<bool> is_used_adder;
    if(!select_best_adders(NO, ca, ca_i_k, sigma, psi, phi, is_used_adder)){
        std::cerr << "[ERROR] Failed to select best adders." << std::endl;
        return;
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

    int input_width = wordlength;
    int output_width = wordlength;

    verilog_file << "`timescale 1ns/1ps\n";
    verilog_file << "module " << module_name << "(input wire [" << input_width-1 << ":0] x";
    for (const auto& pair : output_map) {
        verilog_file << ", output wire [" << output_width-1 << ":0] y" << pair.first;
    }
    verilog_file << ");\n";
    verilog_file << "    // Constant multiplier generated by McmOptimizer\n";

    verilog_file << "    wire [" << output_width-1 << ":0] a0;\n";
    for (const auto& info : optimization_result) {
        verilog_file << "    wire [" << output_width-1 << ":0] a" << info.index << ";\n";
    }
    verilog_file << "\n";

    verilog_file << "    assign a0 = x;\n";

    for (const auto& info : optimization_result) {
        std::string left_expr, right_expr;
        if (info.input_adders.size() > 0) {
            left_expr = "a" + std::to_string(info.input_adders[0]);
        } else {
            left_expr = "x";
        }
        if (info.left_shift > 0)
            left_expr = "(" + left_expr + " << " + std::to_string(info.left_shift) + ")";
        if (info.input_adders.size() > 1) {
            right_expr = "a" + std::to_string(info.input_adders[1]);
        } else {
            right_expr = "x";
        }

        if (info.input_signs.size() > 0 && info.input_signs[0] == '-')
            left_expr = "-" + left_expr;
        if (info.input_signs.size() > 1 && info.input_signs[1] == '-')
            right_expr = "-" + right_expr;

        std::string negative_shift_str = "";
        if (info.negative_shift < 0)
            negative_shift_str = " >>> " + std::to_string(-info.negative_shift);

        verilog_file << "    assign a" << info.index << " = (" << left_expr << " + " << right_expr << ")"
                     << negative_shift_str << "; // ca = " << info.ca << "\n";
    }

    for (const auto& pair : output_map) {
        verilog_file << "    assign y" << pair.first << " = a" << pair.second << ";\n";
    }

    verilog_file << "endmodule\n";
    verilog_file.close();

    std::cout << "[INFO] Verilog file generated: " << module_name << ".v" << std::endl;
    return true;
}

bool McmOptimizer::select_best_adders(int NO, std::vector<operations_research::MPVariable *> &ca,
                                      std::vector<std::vector<std::vector<operations_research::MPVariable *>>> &ca_i_k,
                                      std::vector<std::vector<MPVariable *>> &sigma,
                                      std::vector<std::vector<MPVariable *>> &psi,
                                      std::vector<std::vector<MPVariable *>> &phi,
                                      std::vector<bool> &is_used_adder)
{
    std::vector<std::vector<int>> oadders(target_consts.size());
    for (int j = 0; j < NO; ++j) {
        for (int a = 0; a <= NA; ++a) {
            if (ca[a]->solution_value() == target_consts[j] ) {
                oadders[j].push_back(a);
            }
        }
    }

    // check at least one adder produces each target constant
    for (int j = 0; j < NO; ++j) {
        if (oadders[j].empty()) {
            std::cerr << "[ERROR] No adder produces target constant " << target_consts[j] << std::endl;
            return false;
        }
    }

    is_used_adder = std::vector<bool>(NA + 1, false);

    // traverse all conbinations of adders to find minimal set
    std::function<void(int, std::set<int>&, std::set<int>&)> backtrack;
    std::function<void(int, std::set<int> &)> insert_input_adders;
    insert_input_adders = [&](int a, std::set<int>& adder_set) {
        if (a == 0) return; // base case: input adder
        for (int i = 0; i < 2; ++i) {
            for (int k = 0; k < a; ++k) {
                if (ca_i_k[a][i][k]->solution_value() > 0.5) {
                    bool added = adder_set.insert(k).second;
                    insert_input_adders(k, adder_set);
                }
            }
        }
    };

    backtrack = [&](int j, std::set<int>& current_set, std::set<int>& best_set) {
        if (j == NO) {
            if (best_set.empty() || current_set.size() < best_set.size()) {
                best_set = current_set;
            }
            return;
        }
        for (int a : oadders[j]) {
            current_set.insert(a);
            std::set<int>  new_set = current_set;
            insert_input_adders(a, new_set);
            backtrack(j + 1, new_set, best_set);
        }
    };

    std::set<int> current_set, used_adder_set;
    backtrack(0, current_set, used_adder_set);
    for (int a : used_adder_set) {
        is_used_adder[a] = true;
    }

    // extract adder graph structure. 
    // ca[a], ca_i_k[a][i][k], phi[a][i], sigma[a][s], psi[a][s]
    for (int a = 1; a <= NA; ++a) {
        if (is_used_adder[a]) {
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
    for (int j = 0; j < NO; ++j) {
        for (int a = 0; a <= NA; ++a) {
            if (is_used_adder[a] && ca[a]->solution_value() == target_consts[j]) {
                output_map[target_consts[j]] = a;
            }
        }
    }

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
