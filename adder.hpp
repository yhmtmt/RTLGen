#ifndef ADDER_HPP
#define ADDER_HPP

#include <regex> // Include for std::regex
#include <numeric> // Include for std::accumulate
#include <algorithm> // For std::all_of, std::any_of
#include <cfloat>

// Carry Propagating Adder
// takes generally 2 tuple of (p0,g0) and (p1,g1) as input
// (p0,g0) aggregates lower inputs and (p1,g1) aggregates higher inputs.
// p : p1 p0
// g : g1 + g0 p1
enum CPOperatorInput { CP_P0, CP_G0, CP_P1, CP_G1 };
enum CPOperatorOutput { CP_P, CP_G };

struct CarryPropagatingAdder
{
    std::vector<float> input_delays, output_delays;
    std::vector<std::vector<int>> nodes;
    std::vector<std::vector<float>> tarr[2]; // arrival time for each node. CP_P and CP_G
    std::vector<std::vector<float>> treq[2]; // arrival time for each node. CP_P and CP_G
    std::vector<std::vector<int>> fo[2]; // fanout for each node. CP_P and CP_G
    float tcrit;
    float area_total;

    std::vector<int> minlist;

    // input (a, b) (p, g) = (a + b, a b)
    // takes generally 2 tuple of (p0,g0) and (p1,g1) as input
    // (p0,g0) aggregates lower inputs and (p1,g1) aggregates higher inputs.
    // p : p1 p0
    // g : g1 + g0 p1
    double delays[4][2];
    double area[2]; // area for p and g
    double delay_p, delay_g; // delay generating  (p, g) from input (a, b)

    CarryPropagatingAdder();

    ~CarryPropagatingAdder()
    {
        clear();
    }

    void clear();

    void init(int ninputs);

    float do_sta();
    float calc_tarr(int i, int j);

    void dump_hdl(const std::string& module_name);
};


#endif