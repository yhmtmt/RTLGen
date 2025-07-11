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

        nodes[i][0] = i - 1; // ouptut node
        nodes[i][i] = i;     // input node
    }
}


float CarryPropagatingAdder::do_sta()
{
    // funout
    for (int i = 0; i < nodes.size(); i++)
    {
        fo[CP_G][i][0] = 1;
        fo[CP_P][i][0] = 0;
    }

    for (int w = 0; w < nodes.size(); w++)
    {
        // compute width w node
        for (int i = 0; i < nodes.size(); i++)
        {
            int j = i - w;
            if (i == j || j < 0)
            {
                break; // out of range
            }
            int k = nodes[i][j];
            if (k == -1)
            {
                continue; // no path
            }
            if (fo[CP_P][i][j] == 0)
            {
                fo[CP_P][i][k]++;
                fo[CP_P][k][j]++;
            }
            if (fo[CP_G][i][j] == 0)
            {
                fo[CP_G][i][k]++;
                fo[CP_G][k][j]++;
                fo[CP_P][k][j]++; // p1 to g
            }
            // upper parent
            fo[CP_P][i][k] += fo[CP_P][i][j];
            fo[CP_G][i][k] += fo[CP_G][i][j];
            // lower parent
            fo[CP_P][k][j] += fo[CP_P][i][j];
            fo[CP_G][k][j] += fo[CP_G][i][j];
        }
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

    // compute arival time
    for (int w = 0; w < nodes.size(); w++)
    {
        // compute width w node
        for (int i = 0; i < nodes.size(); i++)
        {
            int j = i - w;
            if (j <= 0)
            {
                break; // out of range
            }
            calc_tarr(i, j);
        }
    }

    // compute critical path delay
    tcrit = 0.f;
    for (int i = 0; i < nodes.size(); i++)
    {
        output_delays[i] = tarr[CP_G][i][0];
        tcrit = std::max(tcrit, output_delays[i]);
    }

    // compute required time
    for (int i = 0; i < nodes.size(); i++)
    {
        treq[CP_G][i][0] = tcrit;
        treq[CP_P][i][0] = tcrit;
    }

    for (int w = nodes.size() - 1; w >= 0; w--)
    {
        // compute width w node
        for (int i = 0; i < nodes.size(); i++)
        {
            int j = i - w;
            int k = nodes[i][j];
            if (j <= 0 || k == -1)
            {
                break; // out of range
            }
            // upper parent
            treq[CP_P][i][k] = std::min((double)treq[CP_P][i][k], treq[CP_P][i][j] - delays[CP_P1][CP_P]);
            treq[CP_G][i][k] = std::min((double)treq[CP_G][i][k], treq[CP_G][i][j] - delays[CP_G1][CP_G]);
            // lower parent
            treq[CP_P][k][j] = std::min((double)treq[CP_P][k][j], treq[CP_P][i][j] - delays[CP_P0][CP_P]);
            treq[CP_G][k][j] = std::min((double)treq[CP_G][k][j], treq[CP_G][i][j] - delays[CP_G0][CP_G]);
            treq[CP_G][k][j] = std::min((double)treq[CP_G][k][j], treq[CP_G][i][j] - delays[CP_P1][CP_G]); // p1 to g
        }
    }
}

float CarryPropagatingAdder::calc_tarr(int i, int j)
{
    if (i == j)
    {
        tarr[CP_P][i][i] = input_delays[i] + delay_p;
        tarr[CP_G][i][i] = input_delays[i] + delay_g;
        return std::max(tarr[CP_P][i][i], tarr[CP_G][i][i]);
    }

    if (i < 0 || i >= nodes.size() || j < 0 || j >= nodes[i].size() || i <= j)
    {
        return FLT_MAX;
    }

    int k = nodes[i][j];
    if (k == -1)
    {
        return FLT_MAX; // No path
    }

    if (i == j || tarr[CP_P][i][j] != 0.f || tarr[CP_G][i][j] != 0.f)
    {
        return std::max(tarr[CP_P][i][j], tarr[CP_G][i][j]); // Already calculated
    }

    tarr[CP_P][i][j] = std::max(tarr[CP_P][i][k] + delays[CP_P1][CP_P], tarr[CP_P][k][j] + delays[CP_P0][CP_P]);
    tarr[CP_G][i][j] = std::max(tarr[CP_G][i][k] + delays[CP_G1][CP_G], tarr[CP_G][k][j] + delays[CP_G0][CP_G]);
    tarr[CP_G][i][j] = std::max((double)tarr[CP_G][i][j], tarr[CP_P][i][k] + delays[CP_P1][CP_G]); // p1 to g

    return std::max(tarr[CP_P][i][j], tarr[CP_G][i][j]);
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
    verilog_file << "  input [0:" << nodes.size() - 1 << "] a,\n";
    verilog_file << "  input [0:" << nodes.size() - 1 << "] b,\n";
    verilog_file << "  output [0:" << nodes.size() - 1 << "] sum,\n";
    verilog_file << "  output [0:" << nodes.size() - 1 << "] cout\n";
    verilog_file << ");\n\n";

    // Write the logic for the carry propagating adder
    // (This part is simplified and should be replaced with actual logic)
    for(int i = 0; i < nodes.size(); i++){
        for(int j = 0; j < nodes[i].size(); j++){
            if(i == j){
                verilog_file << " wire p_" << i << "_" << i << " = a[" << i << "] ^ b[" << i << "];\n";
                verilog_file << " wire g_" << i << "_" << i << " = a[" << i << "] & b[" << i << "];\n";      
            }else{
                int k = nodes[i][j];
                if (k == -1) continue; // no path

                // p_i_k, g_i_k, p_k_j, g_k_j
                // p_i_j = p_i_k . p_k_j
                // g_i_j = g_i_k + p_i_k . g_k_j
                if(fo[CP_P][i][j] > 0)
                    verilog_file << " wire p_" << i << "_" << j << " = p_" << i << "_" << k << " & p_" << k << "_" << j << ";\n";
                if(fo[CP_G][i][j] > 0)               
                    verilog_file << " wire g_" << i << "_" << j << " = g_" << i << "_" << k << " | (p_" << i << "_" << k << " & g_" << k << "_" << j << ");\n";
            }
        }
        if (i == 0)
            verilog_file << " assign sum[" << i << "] = p_" << i << "_" << 0 << ";\n";
        else
            verilog_file << " assign sum[" << i << "] = p_" << i << "_" << 0 << "^ g_" << i - 1 << "_0;\n";
        
        verilog_file << " assign cout[" << i << "] = g_" << i << "_" << 0 << ";\n";
    }
    verilog_file << "endmodule\n";

    verilog_file.close();
}

