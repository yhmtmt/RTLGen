#include <iostream>
#include <vector>
#include <fstream>
#include <limits>
#include <cmath> // Include cmath for log2
#include <bitset>
#include <regex>
#include <numeric> // Include for std::accumulate
#include "adder.hpp"

CarryPropagatingAdder::CarryPropagatingAdder()
{
    // initial (p, g) delays
    delay_p = delay_g = 1.0;

    // operator delays
    delays[CP_P0][CP_P] = delays[CP_P1][CP_P] = 1.0;
    delays[CP_G0][CP_G] = delays[CP_P1][CP_G] = 2.0;
    delays[CP_G1][CP_G] = 1.0;

    // no path in the node
    delays[CP_P0][CP_G] = 0.0;
    delays[CP_G0][CP_P] = 0.0;
    delays[CP_G1][CP_P] = 0.0;

    // area for p and g operator
    area[CP_P] = 1.0;
    area[CP_G] = 2.0;
}

void CarryPropagatingAdder::clear(){
    input_delays.clear();
    output_delays.clear();
    nodes.clear();
    minlist.clear();
    tcrit = 0.f;
    area_total = 0.f;
    tarr[CP_P].clear();
    tarr[CP_G].clear();
    treq[CP_P].clear();
    treq[CP_G].clear();
    fo[CP_P].clear();
    fo[CP_G].clear();
}

void CarryPropagatingAdder::init(int ninputs, CPAType cpatype, const std::vector<float>& input_delay_values)
{
    clear();

    input_delays.assign(ninputs, 0.f);
    if (!input_delay_values.empty())
    {
        if (input_delay_values.size() == 1)
        {
            input_delays.assign(ninputs, input_delay_values.front());
        }
        else if (input_delay_values.size() == static_cast<std::size_t>(ninputs))
        {
            input_delays = input_delay_values;
        }
        else
        {
            std::cerr << "[ERROR] input_delays must be length 1 or match bit width\n";
            exit(1);
        }
    }
    output_delays.resize(ninputs, 0.f);
    nodes.resize(ninputs);
    tarr[CP_P].resize(ninputs);
    treq[CP_P].resize(ninputs);
    tarr[CP_G].resize(ninputs);
    treq[CP_G].resize(ninputs);
    fo[CP_P].resize(ninputs);
    fo[CP_G].resize(ninputs);
    for (int i = 0; i < ninputs; i++)
    {
        nodes[i].resize(i + 1, -1);
        tarr[CP_P][i].resize(i + 1, 0.f);
        treq[CP_P][i].resize(i + 1, FLT_MAX);
        tarr[CP_G][i].resize(i + 1, 0.f);
        treq[CP_G][i].resize(i + 1, FLT_MAX);
        fo[CP_P][i].resize(i + 1, 0);
        fo[CP_G][i].resize(i + 1, 0);

        nodes[i][i] = i;     // input node
    }

    switch(cpatype){
        case CPA_Ripple:
            init_ripple(ninputs);
            break;
        case CPA_KoggeStone:
            init_koggestone(ninputs);
            break;
        case CPA_BrentKung:
            init_brentkung(ninputs);
            break;
        case CPA_Sklansky:
            init_sklansky(ninputs);
            break;
        case CPA_SkewAwarePrefix:
            init_skewaware(ninputs);
            break;
        default:
            std::cerr << "[ERROR] Unknown CPAType in CarryPropagatingAdder::init" << std::endl;
            exit(1);
    }

    do_sta();
}

void CarryPropagatingAdder::init_ripple(int ninputs)
{
    for (int i = 0; i < ninputs; i++){
        // (i,0) is <(i,i),(i-1,0)>
        if(i != 0)
            nodes[i][0] = i - 1; // ouptut node
    }
}

void CarryPropagatingAdder::init_koggestone(int ninputs)
{
    // Fill Kogge-Stone network
    // For each bit i, for each j < i, set nodes[i][j] appropriately
    for (int i = 0; i < ninputs; i++) {
        for (int j = 0; j < i; j++) {
            int span = i - j;
            // Find the largest power of 2 less than or equal to span
            int d = 1;
            while (d * 2 <= span) d *= 2;
            int k = i - d;
            nodes[i][j] = k;
        }
    }
}

void CarryPropagatingAdder::init_brentkung(int ninputs)
{
    // Brent-Kung network construction
    // Up-sweep (reduce) phase
    int levels = 0;
    for (int t = 1; t < ninputs; t <<= 1) levels++;
    for (int d = 2; d < ninputs; d <<= 1) {
        for (int i = d - 1; i < ninputs; i += d) {
            int j = i - d + 1;
            if (j >= 0) {
                nodes[i][j] = i - d / 2;
            }
        }
    }

    // Down-sweep (propagate) phase
    for (int i = 2; i < ninputs; i++){
        if(nodes[i][0] == -1){
            for(int k = i - 1; k >= 0; k--){
                if(nodes[k][0] != -1 && nodes[k][0] < i){
                    nodes[i][0] = k;
                    break;
                }
            }
        }
    } 
}

void CarryPropagatingAdder::init_sklansky(int ninputs)
{
    // Sklansky network construction (divide-and-conquer, "binary tree" adder)
    for (int d = 1; d < ninputs; d <<= 1) {
        for (int i = d; i < ninputs; i += 2*d) {
            int j = i - d;
            if (j >= 0) {
                for(int k = 0; k < d && i + k < ninputs; k++){
                    nodes[i+k][j] = i - 1;
                }
            }
        }
    }
}

void CarryPropagatingAdder::init_skewaware(int ninputs)
{
    struct Segment {
        int msb;
        int lsb;
        float arrival;
    };

    std::vector<Segment> segments;
    segments.reserve(ninputs);
    for (int i = 0; i < ninputs; i++) {
        segments.push_back({i, i, input_delays[i] + static_cast<float>(delay_g)});
    }

    const float merge_delay = static_cast<float>(delays[CP_G1][CP_G]);

    while (segments.size() > 1) {
        float best_cost = std::numeric_limits<float>::infinity();
        int best_idx = -1;

        for (std::size_t idx = 0; idx + 1 < segments.size(); ++idx) {
            // Ensure contiguity
            if (segments[idx + 1].lsb != segments[idx].msb + 1) {
                continue;
            }
            float cost = std::max(segments[idx].arrival, segments[idx + 1].arrival) + merge_delay;
            if (cost < best_cost) {
                best_cost = cost;
                best_idx = static_cast<int>(idx);
            }
        }

        if (best_idx == -1) {
            std::cerr << "[ERROR] SkewAwarePrefix construction failed due to non-contiguous segments\n";
            exit(1);
        }

        const auto &low = segments[best_idx];
        const auto &high = segments[best_idx + 1];
        int boundary = high.lsb - 1;
        nodes[high.msb][low.lsb] = boundary;

        Segment merged{high.msb, low.lsb, best_cost};
        segments[best_idx] = merged;
        segments.erase(segments.begin() + best_idx + 1);
    }
}

float CarryPropagatingAdder::do_sta()
{
    // treq should be initialized FLT_MAX
    // tarr should be initialized -FLT_MAX
    for(int i = 0; i < nodes.size(); i++){
        for(int j = 0; j < i; j++){
            treq[CP_P][i][j] = treq[CP_G][i][j] = FLT_MAX;
            tarr[CP_P][i][j] = tarr[CP_G][i][j] = -FLT_MAX;
        }
    }

    for(int i = 0; i < nodes.size(); i++){
        treq[CP_P][i][i] = FLT_MAX;
        treq[CP_G][i][i] = FLT_MAX;
        tarr[CP_P][i][i] = input_delays[i] + delay_p;
        tarr[CP_G][i][i] = input_delays[i] + delay_g;
    }

    // funout computation
    // initialization
    for (int i = 0; i < nodes.size(); i++)
    {
        for (int j = 0; j < nodes[i].size(); j++)
        {
            fo[CP_P][i][j] = 0;
            fo[CP_G][i][j] = 0;
        }
    }

    // sum is computed as G(i-1,0)^P(i,i) for i>0, P(0,0) for i=0
    for (int i = 0; i < nodes.size(); i++)
    {
        if (i > 0)
        {
            calc_gfo(i - 1, 0);
        }
        calc_pfo(i, i);
    }
    // cout is g_{n-1}_0
    calc_gfo(nodes.size() - 1, 0);

    // area computation (not including input and output nodes)
    for (int i = 0; i < nodes.size(); i++)
    {
        for (int j = 0; j < nodes[i].size(); j++)
        {
            if (i == j)
            {
                continue; // skip diagonal
            }

            if (nodes[i][j] == -1)
            {
                continue; // no path
            }

            if (fo[CP_G][i][j])
                area_total += area[CP_G];
            if (fo[CP_P][i][j])
                area_total += area[CP_P];
        }
    }

    // compute critical path delay
    tcrit = 0.f;
    for (int i = 0; i < nodes.size(); i++){
        if(!calc_tarr(i, 0))
            return false;
        tcrit = std::max(tcrit, tarr[CP_G][i][0]);
        output_delays[i] = tarr[CP_G][i][0];
    }

    for (int i = 0; i < nodes.size(); i++)
    {
        output_delays[i] = tarr[CP_G][i][0];
        tcrit = std::max(tcrit, output_delays[i]);
    }

    // compute required time
    for (int i = 0; i < nodes.size(); i++)
    {
        if(!calc_tpreq(i, 0, tcrit))
            return false;
        if(!calc_tgreq(i, 0, tcrit))    
            return false;
    }
    return tcrit;
}

bool CarryPropagatingAdder::calc_tarr(int i, int j)
{
    if (tarr[CP_P][i][j] > 0 || tarr[CP_G][i][j] > 0)
        return true; // already calculated

    int k = nodes[i][j];
    if (k == -1)
        return false;

    if (i != j)
    {
        if (!calc_tarr(i, k + 1))
            return false;
        if (!calc_tarr(k, j))
            return false;
    }

    // g(i, j) = g(i, k+1)  + p(i, k+1) g(k, j)
    // p(i, j) = p(i, k+1) p(k, j)
    tarr[CP_P][i][j] = std::max(tarr[CP_P][i][k + 1] + delays[CP_P1][CP_P], tarr[CP_P][k][j] + delays[CP_P0][CP_P]);
    tarr[CP_G][i][j] = std::max(tarr[CP_G][i][k + 1] + delays[CP_G1][CP_G], tarr[CP_G][k][j] + delays[CP_G0][CP_G]);
    tarr[CP_G][i][j] = std::max((double)tarr[CP_G][i][j], tarr[CP_P][k][j] + delays[CP_P0][CP_G]);
    return true;
}

bool CarryPropagatingAdder::calc_tpreq(int i, int j, float tpreq)
{
//    std::cout << "calc_tpreq(" << i << ", " << j << ", " << tpreq << ")\n";
    if (treq[CP_P][i][j] <= tpreq)
        return true; // already calculated

    treq[CP_P][i][j] = tpreq;

    if(i == j){ // input node
        return true;
    }

    int k = nodes[i][j];
    if (k == -1)
        return false;

    // upper parent (p is derived only from p1)
    tpreq = treq[CP_P][i][j] - delays[CP_P1][CP_P];
    if (!calc_tpreq(i, k+1, tpreq))
        return false;

    // lower parent (p is derived from p0)
    tpreq = treq[CP_P][i][j] - delays[CP_P0][CP_P]; // p0 to p
    if (!calc_tpreq(k, j, tpreq))
        return false;

    return true;
}
bool CarryPropagatingAdder::calc_tgreq(int i, int j, float tgreq)
{
//    std::cout << "calc_tgreq(" << i << ", " << j << ", " << tgreq << ")\n";
    if (treq[CP_G][i][j] <= tgreq)
        return true; // already calculated
    treq[CP_G][i][j] = tgreq;

    if(i == j){// input node
        return true;
    }

    int k = nodes[i][j];
    if (k == -1)
        return false;

    // upper parent (g is derived both from (g1, p1))
    tgreq = treq[CP_G][i][j] - delays[CP_G1][CP_G];
    if (!calc_tgreq(i, k + 1, tgreq))
        return false;
    float tpreq = treq[CP_G][i][j] - delays[CP_P1][CP_G];
    if (!calc_tpreq(i, k + 1, tpreq))
        return false;

    // lower parent
    tgreq = treq[CP_G][i][j] - delays[CP_G0][CP_G]; // g0 to g
    if (!calc_tgreq(k, j, tgreq))
        return false;

    return true;
}

void CarryPropagatingAdder::dump_hdl(const std::string& module_name)
{
    std::ofstream verilog_file(module_name + ".v");
    if (!verilog_file.is_open())
    {
        std::cerr << "Error: Could not open file " << module_name << ".v" << std::endl;
        return;
    }

    // Write the module header
    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input [" << nodes.size() - 1 << ":0] a,\n";
    verilog_file << "  input [" << nodes.size() - 1 << ":0] b,\n";
    verilog_file << "  output [" << nodes.size() - 1 << ":0] sum,\n";
    verilog_file << "  output cout\n";
    verilog_file << ");\n\n";

    // Write the logic for the carry propagating adder
    // (This part is simplified and should be replaced with actual logic)
    for(int i = 0; i < nodes.size(); i++){
        // input p,g wires
        verilog_file << "  wire p_" << i <<  "_" <<  i << ";\n";
        verilog_file << "  wire g_" << i <<  "_" <<  i << ";\n";
        verilog_file << " assign p_" << i << "_" << i << " = a[" << i << "] ^ b[" << i << "];\n";
        verilog_file << " assign g_" << i << "_" << i << " = a[" << i << "] & b[" << i << "];\n";
        for (int j = 0; j < i; j++)
        {
            if (nodes[i][j] != -1)
            {
                verilog_file << "  wire p_" << i << "_" << j << ";\n";
                verilog_file << "  wire g_" << i << "_" << j << ";\n";
            }
        }
    }

    for(int i = 0; i < nodes.size(); i++){
        for(int j = 0; j < i; j++){
            int k = nodes[i][j];
            if (k == -1)
                continue; // no path

            // p_i_k+1, g_i_k+1, p_k_j, g_k_j
            // p_i_j = p_i_k+1 . p_k_j
            // g_i_j = g_i_k+1 + p_i_k+1 . g_k_j
            verilog_file << " assign p_" << i << "_" << j << " = p_" << i << "_" << k+1 << " & p_" << k << "_" << j << ";\n";
            verilog_file << " assign g_" << i << "_" << j << " = g_" << i << "_" << k+1 << " | (p_" << i << "_" << k+1 << " & g_" << k << "_" << j << ");\n";
        }
        if (i == 0)
            verilog_file << " assign sum[" << i << "] = p_0_0;\n";
        else
            verilog_file << " assign sum[" << i << "] = p_" << i << "_" << i << "^ g_" << i - 1 << "_0;\n";
    }
    verilog_file << " assign cout = g_" << nodes.size() - 1 << "_0;\n";
    verilog_file << "endmodule\n";

    verilog_file.close();
}
