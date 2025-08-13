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

void CarryPropagatingAdder::init(int ninputs)
{
    // initially ripple carry adder is configured.
    input_delays.resize(ninputs, 0.f);
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
        // (i,0) is <(i,i),(i-1,0)>
        if(i != 0)
            nodes[i][0] = i - 1; // ouptut node
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
        for (int j = 1; j < nodes[i].size(); j++)
        {
            fo[CP_P][i][j] = 0;
            fo[CP_G][i][j] = 0;
        }

        // sum is computed as G(i-1,0)^P(i,i) for i>0, P(0,0) for i=0
        // all G(i,0) has 1 funout for sum computation
        fo[CP_G][i][0] = 1;
        fo[CP_P][i][0] = 0;
        // all P(i,i) has 1 funout for sum computation
        fo[CP_G][i][i] = 0; 
        fo[CP_P][i][i] = 1; 
    }

    // compute width w node
    for (int i = 0; i < nodes.size(); i++)
    {
        if(!calc_gfo(i, 0))
            return false; // error in the path
        if(!calc_pfo(i, 0))
            return false; // error in the path
    }

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
    if (treq[CP_P][i][j] <= 0)
        return true; // already calculated
    treq[CP_P][i][j] = tpreq;

    int k = nodes[i][j];
    if (k == -1)
        return false;

    // upper parent (p is derived only from p1)
    tpreq = treq[CP_P][i][j] - delays[CP_P1][CP_P];
    if (!calc_tpreq(k, j, tpreq))
        return false;

    // lower parent (p is derived from p0)
    treq[CP_P][k][j] = treq[CP_P][i][j] - delays[CP_P0][CP_P]; // p0 to p
    if (!calc_tpreq(k, j, tpreq))
        return false;

    return true;
}
bool CarryPropagatingAdder::calc_tgreq(int i, int j, float tgreq)
{

    if (treq[CP_G][i][j] <= tgreq)
        return true; // already calculated
    treq[CP_G][i][j] = tgreq;

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
    verilog_file << "  output [" << nodes.size() - 1 << ":0] cout\n";
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
            if (nodes[i][j] == -1)
            {
                continue; // no path
            }
            if(fo[CP_P][i][j] >0)
                verilog_file << "  wire p_" << i << "_" << j << ";\n";
            if(fo[CP_G][i][j] >0)
                verilog_file << "  wire g_" << i << "_" << j << ";\n";
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
            if (fo[CP_P][i][j] > 0)
                verilog_file << " assign p_" << i << "_" << j << " = p_" << i << "_" << k+1 << " & p_" << k << "_" << j << ";\n";
            if (fo[CP_G][i][j] > 0)
                verilog_file << " assign g_" << i << "_" << j << " = g_" << i << "_" << k+1 << " | (p_" << i << "_" << k+1 << " & g_" << k << "_" << j << ");\n";
        }
        if (i == 0)
            verilog_file << " assign sum[" << i << "] = p_0_0;\n";
        else
            verilog_file << " assign sum[" << i << "] = p_" << i << "_" << i << "^ g_" << i - 1 << "_0;\n";
        
        verilog_file << " assign cout[" << i << "] = g_" << i << "_" << 0 << ";\n";
    }
    verilog_file << "endmodule\n";

    verilog_file.close();
}

