#include <iostream>
#include <vector>
#include <fstream>
#include <limits>
#include <cmath> // Include cmath for log2
#include <bitset>
#include <regex>
#include <numeric> // Include for std::accumulate
#include <sstream>
#include <stdexcept>
#include <ortools/linear_solver/linear_solver.h>
#include "multiplier.hpp"
#include <chrono> // Add this include for timing
#include <cstdlib> // For system()

static int compressor_input_count(CompressorType type)
{
    switch (type) {
        case CT_4_2: return 4;
        case CT_3_2: return 3;
        case CT_2_2: return 2;
        case CT_1_1: return 1;
        default: return 0;
    }
}

static int compressor_carry_count(CompressorType type)
{
    switch (type) {
        case CT_4_2: return 2;
        case CT_3_2: return 1;
        case CT_2_2: return 1;
        case CT_1_1: return 0;
        default: return 0;
    }
}

///////////////////////////////////////////////////////////////////////////////////////////////// MultiplierGenerator methods
void MultiplierGenerator::build(Operand multiplicand, Operand multiplier,
                                           CTType ctype, PPType ptype, CPAType cptype, const std::string &module_name,
                                           bool enable_c42, bool use_direct_ilp)
{
    std::cout << "[INFO] Generating partial products..." << std::endl;
    gen_pp(multiplicand, multiplier, ptype);

    std::cout << "[INFO] Building compressor tree..." << std::endl;
    build_ct(enable_c42, use_direct_ilp);

    std::cout << "[INFO] Building carry-propagate adder..." << std::endl;
    build_cpa(cptype);

    std::cout << "[INFO] Dumping Verilog HDL..." << std::endl;
    dump_hdl(multiplicand, multiplier, module_name);

//    std::cout << "[INFO] Dumping Verilog testbench..." << std::endl;
//    dump_hdl_tb(multiplicand, multiplier, module_name);

    std::cout << "[INFO] Multiplier generation completed." << std::endl;
}

void MultiplierGenerator::build_mac(Operand multiplicand, Operand multiplier, Operand accumulator,
                                           CTType ctype, PPType ptype, CPAType cptype, const std::string &module_name,
                                           bool enable_c42, bool use_direct_ilp)
{
    std::cout << "[INFO] Generating partial products for MAC..." << std::endl;
    gen_pp(multiplicand, multiplier, ptype);
    inject_accumulator_pp_row(accumulator);

    std::cout << "[INFO] Building compressor tree..." << std::endl;
    build_ct(enable_c42, use_direct_ilp);

    std::cout << "[INFO] Building carry-propagate adder..." << std::endl;
    build_cpa(cptype);

    std::cout << "[INFO] Dumping Verilog HDL..." << std::endl;
    dump_hdl_mac(multiplicand, multiplier, accumulator, module_name);

    std::cout << "[INFO] MAC generation completed." << std::endl;
}

void MultiplierGenerator::build_yosys(const MultiplierYosysConfig& config, const std::string& module_name)
{
    if (config.booth_type == "LowpowerBooth" && !config.is_signed) {
        std::cerr << "[ERROR] Low-power Booth architecture is only supported on signed multipliers." << std::endl;
        return;
    }

    // Generate Verilog file
    std::string verilog_filename = module_name + "_yosys.v";
    std::ofstream verilog_file(verilog_filename);
    if (!verilog_file.is_open()) {
        std::cerr << "Error: Could not open file " << verilog_filename << std::endl;
        return;
    }

    verilog_file << "module " << module_name << "(" << std::endl;
    if (config.is_signed) {
        verilog_file << "  input signed [" << config.bit_width - 1 << ":0] multiplicand," << std::endl;
        verilog_file << "  input signed [" << config.bit_width - 1 << ":0] multiplier," << std::endl;
        verilog_file << "  output signed [" << config.bit_width * 2 - 1 << ":0] product" << std::endl;
    } else {
        verilog_file << "  input [" << config.bit_width - 1 << ":0] multiplicand," << std::endl;
        verilog_file << "  input [" << config.bit_width - 1 << ":0] multiplier," << std::endl;
        verilog_file << "  output [" << config.bit_width * 2 - 1 << ":0] product" << std::endl;
    }
    verilog_file << ");" << std::endl << std::endl;
    verilog_file << "  assign product = multiplicand * multiplier;" << std::endl;
    verilog_file << "endmodule" << std::endl;
    verilog_file.close();

    // Generate Yosys script
    std::string ys_filename = "synth.ys";
    std::ofstream ys_file(ys_filename);
    if (!ys_file.is_open()) {
        std::cerr << "Error: Could not open file " << ys_filename << std::endl;
        return;
    }

    ys_file << "read_verilog " << verilog_filename << std::endl;
    ys_file << "proc; opt; fsm; opt; memory; opt" << std::endl;
    if (config.booth_type == "booth") {
        ys_file << "booth" << std::endl;
    } else if (config.booth_type == "LowpowerBooth") {
        ys_file << "booth -lowpower" << std::endl;
    }
    ys_file << "techmap; opt" << std::endl;
    ys_file << "write_verilog " << module_name << ".v" << std::endl;
    ys_file.close();

    // Run Yosys
    std::string command = "yosys " + ys_filename;
    int result = system(command.c_str());

    if (result != 0) {
        std::cerr << "Error: Yosys synthesis failed." << std::endl;
        return;
    }

    std::cout << "[INFO] Yosys synthesis completed successfully." << std::endl;

    // Clean up temporary files
    remove(verilog_filename.c_str());
    remove(ys_filename.c_str());
}

void MultiplierGenerator::dump_hdl_fa(std::ofstream &verilog_file, const std::string &module_name)
{
    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input a,\n";
    verilog_file << "  input b,\n";
    verilog_file << "  input cin,\n";
    verilog_file << "  output sum,\n";
    verilog_file << "  output cout\n";
    verilog_file << ");\n\n";

    // Full adder logic
    verilog_file << "  assign sum = (a ^ b) ^ cin;\n";
    verilog_file << "  assign cout = (a & b) | (b & cin) | (a & cin);\n";

    verilog_file << "endmodule\n";
}

void MultiplierGenerator::dump_hdl_ha(std::ofstream &verilog_file, const std::string &module_name)
{
    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input a,\n";
    verilog_file << "  input b,\n";
    verilog_file << "  output sum,\n";
    verilog_file << "  output cout\n";
    verilog_file << ");\n\n";

    // Half adder logic
    verilog_file << "  assign sum = a ^ b;\n";
    verilog_file << "  assign cout = a & b;\n";

    verilog_file << "endmodule\n";
}

void MultiplierGenerator::dump_hdl_c42(std::ofstream &verilog_file, const std::string &module_name)
{
    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input a,\n";
    verilog_file << "  input b,\n";
    verilog_file << "  input c,\n";
    verilog_file << "  input d,\n";
    verilog_file << "  output sum,\n";
    verilog_file << "  output cout0two,\n";
    verilog_file << "  output cout1\n";
    verilog_file << ");\n\n";
    verilog_file << "  wire s1;\n";
    verilog_file << "  wire c1;\n";
    verilog_file << "  wire c2;\n";
    verilog_file << "  MG_FA fa0(.a(a), .b(b), .cin(c), .sum(s1), .cout(c1));\n";
    verilog_file << "  MG_FA fa1(.a(s1), .b(d), .cin(1'b0), .sum(sum), .cout(c2));\n";
    verilog_file << "  assign cout0 = c1;\n";
    verilog_file << "  assign cout1 = c2;\n";
    verilog_file << "endmodule\n";
}


void MultiplierGenerator::dump_hdl(Operand multiplicand, Operand multiplier, const std::string &module_name)
{
    std::ofstream verilog_file(module_name + ".v");
    if (!verilog_file.is_open())
    {
        std::cerr << "Error: Could not open file " << module_name << ".v" << std::endl;
        return;
    }

    // first define fa and ha modules (later used in compressor tree)
    dump_hdl_fa(verilog_file, "MG_FA");
    dump_hdl_ha(verilog_file, "MG_HA");
    dump_hdl_c42(verilog_file, "MG_C42");
    cpa.dump_hdl("MG_CPA");

    std::vector<std::string> operands= {"multiplicand", "multiplier"};

    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input [" << multiplicand.width - 1 << ":0] multiplicand,\n";
    verilog_file << "  input [" << multiplier.width - 1 << ":0] multiplier,\n";
    verilog_file << "  output [" << cols_pps - 1 << ":0] product\n";
    verilog_file << ");\n\n";

    exp_manager.generateVerilogWires(verilog_file, operands);
    dump_hdl_ct(verilog_file);

    // instantiate carry propagating adder
    int width_cpa = cpa.get_num_inputs();
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cta;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] ctb;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cts;\n";
    verilog_file << "  wire ctc;\n\n";

    verilog_file << "  MG_CPA cpa(\n";
    verilog_file << " .a(cta), .b(ctb), .sum(cts), .cout(ctc)\n";
    verilog_file << "  );\n\n";

    // compression tree's output wires named pp_<num_stages>_<col>_<index>, connected to cpa inputs. 
    // if abscent, then it is zero.
    int ipin_adder = 0;
    for (int icol = cpa_col_start; icol < ct_pps[num_stages].size(); icol++)
    {
        int npps = ct_pps[num_stages][icol];
        if(npps == 0)
            continue; // skip empty columns

        verilog_file << "  assign cta[" << ipin_adder << "] = pp_" << num_stages << "_" << icol << "_0;\n";

        verilog_file << "  assign ctb[" << ipin_adder << "] = ";
        if (npps == 2)
            verilog_file << "pp_" << num_stages << "_" << icol << "_1;\n";
        else if(npps == 1)
            verilog_file << "1'b0;\n"; // if there is no second pp, then it is zero

        ipin_adder++;
    }

    // note cols_pps is the output width of the multiplier, but cts is not necessarily equal to cols_pps.
    // because partial products are generated in a way that the last row is not necessarily equal to the width of the multiplier.
    // thus if width_cpa is less than cols_pps, we need to connect ctc to the msb of the product.
    for (int icol = 0; icol < cpa_col_start; icol++)
        verilog_file << "  assign product[" << icol << "] = pp_" << num_stages << "_" << icol << "_" << 0 << ";\n"; // zero padding

    verilog_file << "  assign product[" << cpa_col_end << ":" << cpa_col_start << "] = cts;\n"; // cts is the sum output of the cpa
    if (cpa_col_end + 1 <  cols_pps)
    {
        verilog_file << "  assign product[" << cols_pps - 1 << "] = ctc;\n";
    }

    verilog_file << "endmodule\n";
}

void MultiplierGenerator::dump_hdl_mac(Operand multiplicand, Operand multiplier, Operand accumulator, const std::string &module_name)
{
    std::ofstream verilog_file(module_name + ".v");
    if (!verilog_file.is_open())
    {
        std::cerr << "Error: Could not open file " << module_name << ".v" << std::endl;
        return;
    }

    dump_hdl_fa(verilog_file, "MG_FA");
    dump_hdl_ha(verilog_file, "MG_HA");
    dump_hdl_c42(verilog_file, "MG_C42");
    cpa.dump_hdl("MG_CPA");

    std::vector<std::string> operands= {"multiplicand", "multiplier", "accumulator"};

    verilog_file << "module " << module_name << "(\n";
    verilog_file << "  input [" << multiplicand.width - 1 << ":0] multiplicand,\n";
    verilog_file << "  input [" << multiplier.width - 1 << ":0] multiplier,\n";
    verilog_file << "  input [" << accumulator.width - 1 << ":0] accumulator,\n";
    verilog_file << "  output [" << cols_pps - 1 << ":0] result\n";
    verilog_file << ");\n\n";

    exp_manager.generateVerilogWires(verilog_file, operands);
    dump_hdl_ct(verilog_file);

    int width_cpa = cpa.get_num_inputs();
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cta;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] ctb;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cts;\n";
    verilog_file << "  wire ctc;\n\n";

    verilog_file << "  MG_CPA cpa(\n";
    verilog_file << " .a(cta), .b(ctb), .sum(cts), .cout(ctc)\n";
    verilog_file << "  );\n\n";

    int ipin_adder = 0;
    for (int icol = cpa_col_start; icol < ct_pps[num_stages].size(); icol++)
    {
        int npps = ct_pps[num_stages][icol];
        if(npps == 0)
            continue;

        verilog_file << "  assign cta[" << ipin_adder << "] = pp_" << num_stages << "_" << icol << "_0;\n";
        verilog_file << "  assign ctb[" << ipin_adder << "] = ";
        if (npps == 2)
            verilog_file << "pp_" << num_stages << "_" << icol << "_1;\n";
        else if(npps == 1)
            verilog_file << "1'b0;\n";

        ipin_adder++;
    }

    for (int icol = 0; icol < cpa_col_start; icol++)
        verilog_file << "  assign result[" << icol << "] = pp_" << num_stages << "_" << icol << "_" << 0 << ";\n";

    verilog_file << "  assign result[" << cpa_col_end << ":" << cpa_col_start << "] = cts;\n";
    if (cpa_col_end + 1 <  cols_pps)
    {
        verilog_file << "  assign result[" << cols_pps - 1 << "] = ctc;\n";
    }

    verilog_file << "endmodule\n";
}

void MultiplierGenerator::dump_hdl_tb(Operand multiplicand, Operand multiplier, const std::string &module_name)
{
    std::ofstream tb_file(module_name + "_tb.v");
    if (!tb_file.is_open())
    {
        std::cerr << "Error: Could not open file " << module_name << "_tb.v" << std::endl;
        return;
    }

    int width_a = multiplicand.width;
    int width_b = multiplier.width;
    int width_p = width_a + width_b;
    bool signed_a = multiplicand.is_signed;
    bool signed_b = multiplier.is_signed;

    tb_file << "module " << module_name << "_tb;\n";
    tb_file << "  reg [" << width_a - 1 << ":0] multiplicand;\n";
    tb_file << "  reg [" << width_b - 1 << ":0] multiplier;\n";
    tb_file << "  wire [" << width_p - 1 << ":0] product;\n";
    tb_file << "  reg [" << width_p - 1 << ":0] expected;\n";
    tb_file << "  integer i;\n";
    tb_file << "\n";
    tb_file << "  " << module_name << " uut(\n";
    tb_file << "    .multiplicand(multiplicand),\n";
    tb_file << "    .multiplier(multiplier),\n";
    tb_file << "    .product(product)\n";
    tb_file << "  );\n\n";

    tb_file << "  initial begin\n";
    tb_file << "    $display(\"Testing " << module_name << "\");\n";
    tb_file << "    $dumpfile(\"" << module_name << "_tb.vcd\");\n";
    tb_file << "    $dumpvars(0, " << module_name << "_tb);\n";
    tb_file << "    for (i = 0; i < 100; i = i + 1) begin\n";
    tb_file << "      multiplicand = $random;\n";
    tb_file << "      multiplier = $random;\n";
    tb_file << "      #1;\n";
    if (signed_a && signed_b)
    {
        tb_file << "      expected = $signed(multiplicand) * $signed(multiplier);\n";
    }
    else if (signed_a)
    {
        tb_file << "      expected = $signed(multiplicand) * multiplier;\n";
    }
    else if (signed_b)
    {
        tb_file << "      expected = multiplicand * $signed(multiplier);\n";
    }
    else
    {
        tb_file << "      expected = multiplicand * multiplier;\n";
    }
    tb_file << "      if (product !== expected) begin\n";
    tb_file << "          $display(\"FAIL: multiplicand=%h, multiplier=%h, product=%h, expected=%h\", multiplicand, multiplier, product, expected);\n";
    tb_file << "          $finish;\n";
    tb_file << "      end\n";
    tb_file << "    end\n";
    tb_file << "    $display(\"Test completed.\");\n";
    tb_file << "    $finish;\n";
    tb_file << "  end\n";
    tb_file << "endmodule\n";
}

void MultiplierGenerator::dump_hdl_ct(std::ofstream &verilog_file)
{

    //generating wires for each pp_<stage>_<coll>_<index>
    for (int istage = 0; istage < ct_pps.size(); istage++)
    {
        for (int icol = 0; icol < ct_pps[istage].size(); icol++)
        {
            int npps = ct_pps[istage][icol];
            for (int ipp = 0; ipp < npps; ipp++)
            {
                verilog_file << "  wire pp_" << istage << "_" << icol << "_" << ipp << ";\n";
            }
        }
    }

    // generating 
    for (int icol = 0; icol < cols_pps; icol++)
    {
        int ipin = 0;
        for (int irow = 0; irow < rows_pps; irow++)
        {
            if (pps[irow][icol].bit_type == BIT_NONE)
                continue; // skip empty pps

            verilog_file << "  assign pp_" << 0 << "_" << icol << "_" << ipin << " = ";
            if (pps[irow][icol].bit_type == BIT_ZERO)
                verilog_file << "1'b0;\n";
            else if (pps[irow][icol].bit_type == BIT_ONE)
                verilog_file << "1'b1;\n";
            else if (pps[irow][icol].bit_type == BIT_EXPRESSION)
                // expression is a BoolExp object, so we can use its name
                verilog_file << pps[irow][icol].expression->name << ";\n";
            ipin++;
        }
    }

    verilog_file << "\n";
    // then traversing ct and create full adder and half adder instances. the name of them is fa_<stage>_<coll>_<index> and ha_<stage>_<coll>_<index>
    for(int istage = 0; istage < ct.size(); istage++)
    {
        for(int icol = 0; icol < ct[istage].size(); icol++)
        {
            int npps = ct_ipin[istage][icol].size();
            int npps_next = ct_opin[istage][icol].size();
            // generate wires for input pins pp_<stage>_<coll>_<index>
            // note: 
            // pps are <carries from istage-1,icol-1> <carries from istage-1,icol> <remained wires from istage-1, icol>
            // 0th stage is from generated pps, but the index is the order appeared in the column of pps, not that of pps. 
            // we need to assign pp_<stage>_<coll>_<index> to inputs and outputs of compressor adders according to pin_assign.
            // 
            int iipin = 0, iopin = 0;
            for(int icmp = 0; icmp < ct[istage][icol].size(); icmp++)
            {
                auto & node = ct[istage][icol][icmp];
                if(node.type == CT_3_2)
                {
                    int ia = pin_assign[istage][icol][node.ipp0];       // get_pp_in_index(istage, icol, icmp, 0);
                    int ib = pin_assign[istage][icol][node.ipp0 + 1];   // get_pp_in_index(istage, icol, icmp, 1);
                    int icin = pin_assign[istage][icol][node.ipp0 + 2]; // get_pp_in_index(istage, icol, icmp, 2);
                    int isum = node.sum;   // get_pp_out_index(istage+1, icol, icmp, 0);
                    int icout = node.couts.empty() ? -1 : node.couts[0]; // get_pp_out_index(istage+1, icol+1, icmp, 1);
                    verilog_file << "  MG_FA fa_" << istage << "_" << icol << "_" << icmp << "(\n";
                    verilog_file << "    .a(pp_" <<istage << "_" << icol << "_" << ia << "),\n";
                    verilog_file << "    .b(pp_" <<istage << "_" << icol << "_" << ib << "),\n";
                    verilog_file << "    .cin(pp_" <<istage << "_" << icol << "_" << icin << "),\n";
                    verilog_file << "    .sum(pp_" << istage + 1 << "_" << icol << "_" << isum << "),\n";
                    if(icout < 0)
                        verilog_file << "    .cout()\n";
                    else
                        verilog_file << "    .cout(pp_" << istage + 1 << "_" << icol + 1 << "_" << icout << ")\n";
                    verilog_file << "  );\n\n";
                }
                else if(node.type == CT_2_2)
                {
                    int ia = pin_assign[istage][icol][node.ipp0];      // get_pp_in_index(istage, icol, icmp, 0);
                    int ib = pin_assign[istage][icol][node.ipp0 + 1];  // get_pp_in_index(istage, icol, icmp, 1);
                    int isum = node.sum;   // get_pp_out_index(istage+1, icol, icmp, 0);
                    int icout = node.couts.empty() ? -1 : node.couts[0]; // get_pp_out_index(istage+1, icol+1, icmp, 1);
                    verilog_file << "  MG_HA ha_" << istage << "_" << icol << "_" << icmp << "(\n";
                    verilog_file << "    .a(pp_" << istage << "_" << icol << "_" << ia << "),\n";
                    verilog_file << "    .b(pp_" << istage << "_" << icol << "_" << ib << "),\n";
                    verilog_file << "    .sum(pp_" << istage + 1 << "_" << icol << "_" << isum << "),\n";
                    if(icout < 0)
                        verilog_file << "    .cout()\n";
                    else
                        verilog_file << "    .cout(pp_" << istage + 1 << "_" << icol + 1 << "_" << icout << ")\n";
                    verilog_file << "  );\n\n";
                }else if(node.type == CT_4_2)
                {
                    int ia = pin_assign[istage][icol][node.ipp0];
                    int ib = pin_assign[istage][icol][node.ipp0 + 1];
                    int ic = pin_assign[istage][icol][node.ipp0 + 2];
                    int id = pin_assign[istage][icol][node.ipp0 + 3];
                    int isum = node.sum;
                    int icout0 = node.couts.size() > 0 ? node.couts[0] : -1;
                    int icout1 = node.couts.size() > 1 ? node.couts[1] : -1;
                    verilog_file << "  MG_C42 c42_" << istage << "_" << icol << "_" << icmp << "(\n";
                    verilog_file << "    .a(pp_" << istage << "_" << icol << "_" << ia << "),\n";
                    verilog_file << "    .b(pp_" << istage << "_" << icol << "_" << ib << "),\n";
                    verilog_file << "    .c(pp_" << istage << "_" << icol << "_" << ic << "),\n";
                    verilog_file << "    .d(pp_" << istage << "_" << icol << "_" << id << "),\n";
                    verilog_file << "    .sum(pp_" << istage + 1 << "_" << icol << "_" << isum << "),\n";
                    if(icout0 < 0)
                        verilog_file << "    .cout0(),\n";
                    else
                        verilog_file << "    .cout0(pp_" << istage + 1 << "_" << icol + 1 << "_" << icout0 << "),\n";
                    if(icout1 < 0)
                        verilog_file << "    .cout1()\n";
                    else
                        verilog_file << "    .cout1(pp_" << istage + 1 << "_" << icol + 1 << "_" << icout1 << ")\n";
                    verilog_file << "  );\n\n";
                }else if(node.type == CT_1_1)
                {
                    // pass through node
                    int ipass = pin_assign[istage][icol][node.ipp0]; // get_pp_in_index(istage, icol, icmp, 0);
                    int ipass_out = node.sum; // get_pp_out_index(istage+1, icol, icmp, 0);
                    verilog_file << "  assign pp_" << istage + 1 << "_" << icol << "_" << ipass_out << " = pp_" << istage << "_" << icol << "_" << ipass << ";\n";
                }
            }
        }
    }
}

void MultiplierGenerator::gen_pp(Operand multiplicand, Operand multiplier, PPType ppType)
{
    switch (ppType)
    {
    case Normal:
        gen_normal_pp(multiplicand, multiplier);
        break;
    case Booth4:
        gen_booth4_pp(multiplicand, multiplier);
        break;
    case Normal4:
        gen_normal4_pp(multiplicand, multiplier);
        break;
    default:
        std::cerr << "Error: Unsupported PPType." << std::endl;
        return;
    }

    // Print number of rows, columns, and total partial product bits
    int total_pp_bits = 0;
    for (const auto& row : pps) {
        for (const auto& bit : row) {
            if (bit.bit_type != BIT_NONE)
                total_pp_bits++;
        }
    }
    std::cout << "[INFO] Partial product matrix: " << rows_pps << " rows x " << cols_pps << " cols, total " << total_pp_bits << " bits." << std::endl;
}

void MultiplierGenerator::inject_accumulator_pp_row(Operand accumulator)
{
    if (accumulator.width != cols_pps) {
        std::ostringstream oss;
        oss << "MAC accumulator width (" << accumulator.width
            << ") must match multiplier product width (" << cols_pps
            << ") for pp_row_feedback mode.";
        throw std::runtime_error(oss.str());
    }

    pps.emplace_back(cols_pps, PPBit());
    auto &acc_row = pps.back();
    for (int ibit = 0; ibit < accumulator.width; ++ibit) {
        acc_row[ibit].bit_type = BIT_EXPRESSION;
        acc_row[ibit].expression = exp_manager.allocate(
            "pp_acc_" + std::to_string(ibit),
            NOP,
            std::vector<OpBit>{(OpBit){2, 0, static_cast<short>(ibit)}}
        );
    }
    rows_pps = static_cast<int>(pps.size());
    std::cout << "[INFO] Injected accumulator feedback row into partial products (width "
              << accumulator.width << ")." << std::endl;
}

// n bit multiplicand m bit multiplier. Normal radix-2 
// common
// * the result is n + m width
// unsigned
// * no extension
// * partial product rows are m
//
// 3bit x 3bit pp
// 000vvv
// 00vvv0
// 0vvv00
//
// signed (see Arithmetic Computing, 2nd edition, page 196)
// * requires sign computation for m + n bit width.
// * last row should be negative if multiplier is negative.
// 00mVvv
// 00Vvv0
// 1Xxy00
//
// m: sign bit of multiplier
// v: normal partial product
// x: negated muptiplicand and sign bit of multiplier
// V: negated v
// X: negated x
// y: lsb of multiplicand nand sign bit of multiplier
void MultiplierGenerator::gen_normal_pp(Operand multiplicand, Operand multiplier)
{
    if(multiplicand.is_signed != multiplier.is_signed)
    {
        std::cerr << "Error: Signed and unsigned operands are not compatible." << std::endl;
        return;
    }

    // first calculate cols and rows of the pps
    cols_pps = multiplicand.width + multiplier.width;
    rows_pps = multiplier.width;
    pps.resize(rows_pps);

    // unsigned case
    for (int i = 0; i < pps.size(); i++)
    {
        auto & pp = pps[i];
        pp.resize(cols_pps, PPBit());
        for (int j = 0; j < multiplicand.width; j++)
        {
            pp[i + j].bit_type = BIT_EXPRESSION;
            pp[i + j].expression = exp_manager.allocate("pp_" + std::to_string(i) + "_" + std::to_string(i + j), AND, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(j)}, (OpBit){1, 0, static_cast<short int>(i)}}); // multiplicand[j] * multiplier[i]
        }
    }

    // signed case (revise the sign related bits)
    if(multiplier.is_signed)
    {
        // modified sign in the first row
        {
            auto &pp = pps[0];
            pp[multiplicand.width - 1].expression->setOperation(NAND);
            pp[multiplicand.width].bit_type = BIT_EXPRESSION;
            pp[multiplicand.width].expression =
                exp_manager.allocate("pp_" + std::to_string(0) + "_" + std::to_string(multiplicand.width),
                                     NOP, std::vector<OpBit>({(OpBit){1, 0, static_cast<short int>(multiplier.width - 1)}})); // sign bit of multiplier

            for (int i = 1; i < pps.size() - 1; i++)
            {
                auto &pp = pps[i];
                pp[i + multiplicand.width - 1].bit_type = BIT_EXPRESSION;
                pp[i + multiplicand.width - 1].expression->setOperation(NAND);
            }
        }
        // multiplier's sign multiplication in last row
        {
            auto &pp = pps[pps.size() - 1];
            pp[multiplicand.width - 1].expression->setOperation(NAND);
            pp[multiplicand.width - 1].expression->setInputs({(OpBit){0, 0, 0}, (OpBit){1, 0, static_cast<short int>(multiplier.width - 1)}});

            for (int j = 1; j < multiplicand.width; j++)
            { // (0,1,j):negated multiplicand, (1,0,multiplier.width-1):multiplier's sign bit
                pp[multiplier.width - 1 + j].expression->setInputs({(OpBit){0, 1, static_cast<short int>(j)}, (OpBit){1, 0, static_cast<short int>(multiplier.width - 1)}});
            }
            pp[cols_pps - 2].expression->setOperation(NAND);
            pp[cols_pps - 1].bit_type = BIT_EXPRESSION;
            pp[cols_pps - 1].expression =
                exp_manager.allocate("pp_" + std::to_string(pps.size() - 1) + "_" + std::to_string(cols_pps - 1),
                                     ONE);
        }
    }
}

// n bit multiplciand m bit multiplier. Booth4 sign extension rule
// common 
// * the result is n + m width
// unsigned case
// * requires 2 bit extension, one for sign, another for 2x operation
// * requires 1 or 2 bit zero sign extension to make the last row of partial product positive. 
//          - odd width, 1 bit zero sign
//          - even width, 2 bit zero sign (result in additional row)
// * partial product rows are floor(m/2)+1
//
// 3bit x 3bit pp case
// ssvvvv
// vvvv0c <- last row does not need sign extension because it is positive
// xxxxxx <- result(6bit)
//
// 4bit x 4bit pp case
// Sssvvvvv
// Svvvvv0c
// vvvv0c00 <- last row does not need sign extension because it is positive
// xxxxxxxx <- result(8bit)
//
// signed case
// * requires sign computation for m + n bit width. 
// * requires 1-bit sign extension for multiplicand because pp row can be 2x, -2x. 
// * requires 1 bit sign extension when multiplier ct_has odd width. 
//
// 4 bit x 4 bit pp case -8 to 7 -> -56(11001000) to 64(01000000) 56(00111000)  -2^(n-1) to 2^(n-1)-1 -> -2^(2n-2)+2^(n-1) to 2^(2n-2)
// 0Sssvvvv
// 1Svvvv0c
// 00000c00

// booth 4 pp generation
// signed 
// psum selection window {t, multiplier[m-1:0], 0} -> {i+1,i,i-1} for pp(i)
// pp(0): {s' s, psum} + c
// pp(1 to (m+1)/2) : {1 s', psum} + c (placed in the next row, thus requires 1 additional row)
//
// unsigned
// psum selection window {0, multiplier[m-1:0], 0} -> {i+1,i,i-1} for pp(i)
// pp(0): {s' s s, psum} + c  
// pp(1 to (m+1)/2 - 2):  {1 s', psum} + c
// pp((m+1)/2 - 1): {psum}
// Booth4 encoder signals
void MultiplierGenerator::gen_booth4_pp(Operand multiplicand, Operand multiplier)
{
    if(multiplicand.is_signed != multiplier.is_signed)
    {
        std::cerr << "Error: Signed and unsigned operands are not compatible." << std::endl;
        return;
    }

    if (multiplier.width < 2)
    {
        return;
    }

    // note that signed case ct_has one additional row to invert last row.
    cols_pps = multiplicand.width + multiplier.width;
    if (multiplicand.is_signed)
    {
        rows_pps = (multiplier.width + 1) / 2 + 1; // additional row required to invert last row.
    }else
    {
        rows_pps = multiplier.width / 2 + 1;
    }

    // allocate the zero and one constant
    exp_manager.allocate("zero", ZERO, std::vector<OpBit>());
    exp_manager.allocate("one", ONE, std::vector<OpBit>());

    int ext_width = multiplier.is_signed ? 1 : 2;
    // allocate the multiplicand and multiplier bits. n
    std::vector<BoolExp*> x;
    x.resize(ext_width + multiplicand.width);
    for(int i = 0; i < multiplicand.width; i++){
       x[i] = exp_manager.allocate("x_" + std::to_string(i), NOP, {(OpBit){0, 0, static_cast<short int>(i)}});
    }
    if(multiplier.is_signed){
        x[multiplicand.width] = exp_manager.allocate("x_" + std::to_string(multiplicand.width), NOP, {(OpBit){0, 0, static_cast<short int>(multiplicand.width-1)}}); // sign bit
    }else{
        x[multiplicand.width] = x[multiplicand.width + 1] = exp_manager.get("zero");
    }

    bes.resize(rows_pps - (multiplier.is_signed ? 1 : 0));

    std::vector<BoolExp*> y, ny;
    y.resize(bes.size() * 2 + 1);
    ny.resize(bes.size() * 2 + 1);

    y[0] = exp_manager.get("zero");
    ny[0] = exp_manager.get("one");

    for (int i = 1; i < y.size(); i++)
    {
        if(i > multiplier.width){
            if(multiplier.is_signed){ // sign extension with msb
                OpBit bit = (OpBit){1, 0, static_cast<short int>(multiplier.width-1)};
                OpBit nbit = (OpBit){1, 1, static_cast<short int>(multiplier.width-1)};
                y[i] = exp_manager.allocate("y_" + std::to_string(i-1), NOP, std::vector<OpBit>({bit}));
                ny[i] = exp_manager.allocate("ny_" + std::to_string(i-1), NOP, std::vector<OpBit>({nbit}));                      
            }else{ // sign extension with zero
                y[i] = exp_manager.get("zero");
                ny[i] = exp_manager.get("one");              
            }
        }
        else
        {
            OpBit bit = (OpBit){1, 0, static_cast<short int>(i - 1)};
            OpBit nbit = (OpBit){1, 1, static_cast<short int>(i - 1)};
            y[i] = exp_manager.allocate("y_" + std::to_string(i - 1), NOP, std::vector<OpBit>({bit}));
            ny[i] = exp_manager.allocate("ny_" + std::to_string(i - 1), NOP, std::vector<OpBit>({nbit}));
        }
    }

    // booth4 encoder
    // s2(i) = !y(2i+1) y(2i) y(2i-1) + y(2i+1) !y(2i) !y(2i-1)
    // s1(i) = y(2i)^y(2i-1)
    // neg(i) = y(2i+1)
    // c(i) = y(2i+1)(!y(2i)+!y(2i-1))
    for(int i = 0; i < bes.size(); i++){
        BoolExp *ye[3] = {y[i * 2], y[i * 2 + 1], y[i * 2 + 2] }; // note that y and ny indices are shifted by 1
        BoolExp *nye[3] = {ny[i * 2], ny[i * 2 + 1], ny[i * 2 + 2]};
        BoolExp *a = nullptr, *b = nullptr, *c = nullptr;
        BoothEncoder &be = bes[i];

        // there would be redundant logics, but to be eliminated by logic synthesizer
        a = exp_manager.allocate("be_s2_a_" + std::to_string(i), AND, {nye[2], ye[1], ye[0]});                      // !y(2i+1) y(2i) y(2i-1)
        b = exp_manager.allocate("be_s2_b_" + std::to_string(i), AND, {ye[2], nye[1], nye[0]});                     // y(2i+1) !y(2i) !y(2i-1)
        be.s2 = exp_manager.allocate("be_s2_" + std::to_string(i), OR, (std::vector<BoolExp *>){a, b});          // !y(2i+1) y(2i) y(2i-1) + y(2i+1) !y(2i) !y(2i-1)
        be.s1 = exp_manager.allocate("be_s1_" + std::to_string(i), XOR, (std::vector<BoolExp *>){ye[1], ye[0]}); // y(2i) ^ y(2i-1)
        be.neg = exp_manager.allocate("be_neg_" + std::to_string(i), NOP, {ye[2]});                              // y(2i+1)
        c = exp_manager.allocate("be_d_" + std::to_string(i), OR, (std::vector<BoolExp *>){nye[1], nye[0]});     // !y(2i) + !y(2i-1)
        be.c = exp_manager.allocate("be_c_" + std::to_string(i), AND, (std::vector<BoolExp *>){c, be.neg});      // y(2i+1) (!y(2i) + !y(2i-1))
    }

    // booth4 decoder 
    // px(n,m) = x(m)^neg(n)
    // pp(n,m) = !(!(px(n,m-1)s2(n)) !(px(n,m)s1(n)))
    pps.resize(rows_pps);
    for(int i = 0; i < pps.size(); i++){
        pps[i].resize(cols_pps, PPBit());
    }

    pxs.resize(bes.size());
    for (int i = 0; i < bes.size(); i++)
    {
        auto & pp = pps[i];
        auto & px = pxs[i];
        pp.resize(cols_pps, PPBit());
        px.resize(multiplicand.width + ext_width + 1, nullptr); // indices are shifted by 1
        px[0] = exp_manager.allocate("px_" + std::to_string(i) + "_" + std::to_string(0), NOP, (std::vector<BoolExp *>){bes[i].neg});
        for (int j = 1; j < px.size(); j++)
        {
            px[j] = exp_manager.allocate("px_" + std::to_string(i) + "_" + std::to_string(j), XOR, (std::vector<BoolExp*>){bes[i].neg, x[j-1]});
        }

        for(int j = 0; j < (multiplicand.width + ext_width) && (2* i + j) < cols_pps; j++){
            BoolExp *a = exp_manager.allocate("be_2x_" + std::to_string(i) + "_" + std::to_string(j), NAND, (std::vector<BoolExp*>){px[j], bes[i].s2});
            BoolExp *b = exp_manager.allocate("be_x_" + std::to_string(i) + "_" + std::to_string(j), NAND, (std::vector<BoolExp*>){px[j+1], bes[i].s1});
            pp[2*i + j].bit_type = BIT_EXPRESSION;
            pp[2*i + j].expression = exp_manager.allocate("pp_" + std::to_string(i) + "_" + std::to_string(2*i + j), NAND, (std::vector<BoolExp*>){a, b});
        }

        if(i+1 < rows_pps){ // correction bit 
            pps[i+1][2 * i].bit_type = BIT_EXPRESSION;
            pps[i+1][2 * i].expression = bes[i].c;
        }

        if(i == 0){ // add msb correction s'ss
            int jmsb = multiplicand.width + ext_width - 1;
            int jext = jmsb;
            BoolExp * exp_msb = pps[0][jmsb].expression;
            if(jext + 1 < cols_pps)
            {
                pps[0][jext + 1].bit_type = BIT_EXPRESSION;
                pps[0][jext + 1].expression = exp_msb;
            }
            if(jext + 2 < cols_pps){
                pps[0][jext + 2].bit_type = BIT_EXPRESSION;
                pps[0][jext + 2].expression = exp_manager.allocate("not_pp_" + std::to_string(i) + "_" + std::to_string(jext+2), NOT, {pps[i][jmsb].expression});
            }
        }else{ // add msb correction 1s'
            int jmsb = 2 * i + multiplicand.width + ext_width - 1;
            int jext = jmsb;
            if (jmsb < cols_pps)
            {
                BoolExp *exp_msb = pps[i][jmsb].expression;
                pps[i][jext].bit_type = BIT_EXPRESSION;
                pps[i][jext].expression = exp_manager.allocate("not_pp_" + std::to_string(i) + "_" + std::to_string(jext), NOT, {exp_msb});
                if (jext + 1 < cols_pps)
                {
                    pps[i][jext + 1].bit_type = BIT_EXPRESSION;
                    pps[i][jext + 1].expression = exp_manager.get("one");
                }
            }
        }
    }
}

// n bit multiplicand m bit multiplier. normal radix-4
// common
// * multiplicand 2 bit extension (for 3x operation) 
// * result is n + m bit width
// * precalculate 3x
// unsigned case
// * partial product rows are floor((m+1)/2)
// * multiplier should extended to be even bit width (zero fill)
// * row is selected from {0x, 1x, 2x, 3x}
// 4bit x 4bit pp case
// 00vvvvvv
// vvvvvv00
// xxxxxxxx
//
// signed case
// * multiplicand 2 bit extension (for 3x operation)
// * excepting for last row, selcted from {0x, 1x, 2x, 3x}
// * even width multiplier, last row  y(n-1),y(n-2): 00->0 01->x 10->-2x, 11->-x
// * odd width multiplier, last row y(n-1): 00->0 11->-x (only we have 00 or 11)
//
// 3bit x 3bit pp case
// Sssvvv
// sXXX00
// 000c00
//
// 4bit x 4bit pp case
// Sssvvvvv
// sxxxxx00
// 00000c00
void MultiplierGenerator::gen_normal4_pp(Operand multiplicand, Operand multiplier)
{
    if (multiplier.is_signed != multiplicand.is_signed)
    {
        std::cerr << "Error: Signed and unsigned operands are not compatible." << std::endl;
        return;
    }
    if (multiplier.width < 2 || multiplicand.width < 2)
    {
        std::cerr << "Error: Multiplicand or multiplier width is less than 2." << std::endl;
        return;
    }

    // normal4 encoder
    // s3(n) =  y(n+1) y(n)
    // s2(n) =  y(n+1)!y(n)
    // s1(n) = !y(n+1) y(n)

    // normal4 decoder
    // pp(n,m) = !(!(x3(m)s3(n)) !(x3(m)s3(n)) !(x3(m)s3(n)))

    // normal 4 pp generation
    // signed (need to special treat for sign bit of multiplier)
    // psum selection window {0, multiplier[m-2:0]} -> {i+1, i} for pp(i)
    // t: sign of multiplier
    // pp(0 to (m+1)/2-2) : {psum}
    // pp((m+1)/2-1) : {1, !multiplicand[n-1:1], !(t multiplicand[0])} + (t << 1) 
    // 
    // unsigned
    // psum selection window {multiplier[m-1:0]} -> {i+1, i} for pp(i)
    // pp(0 to (m+1)/2-1) : {psum}

    exp_manager.allocate("zero", ZERO, std::vector<OpBit>{});
    std::vector<BoolExp *> y, ny;
    y.resize(multiplier.width + multiplier.width % 2);
    ny.resize(multiplier.width + multiplier.width % 2);
    for(int i = 0; i < multiplier.width; i++){
        y[i] = exp_manager.allocate("y_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){1, 0, static_cast<short int>(i)}});
        ny[i] = exp_manager.allocate("ny_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){1, 1, static_cast<short int>(i)}});
    }
    if(multiplier.width % 2 == 1){ // extension for odd width multiplier
        if(multiplier.is_signed){
            y[multiplier.width] = exp_manager.allocate("y_" + std::to_string(multiplier.width), NOP, std::vector<OpBit>{(OpBit){1, 0, static_cast<short int>(multiplier.width-1)}});
            ny[multiplier.width] = exp_manager.allocate("ny_" + std::to_string(multiplier.width), NOP, std::vector<OpBit>{(OpBit){1, 1, static_cast<short int>(multiplier.width-1)}});
        }else{
            y[multiplier.width] = exp_manager.get("zero");
            ny[multiplier.width] = exp_manager.get("one");
        }   
    }

    // 2x, 3x generation. 3x is generated by 2x + multiplicand. adder is implemented as ripple carry adder.  if faster adder required, modify the following loop.
    std::vector<BoolExp*> x, x2, x3;
    x.resize(multiplicand.width + 2);
    x2.resize(multiplicand.width + 2);
    for(int i = 0; i < multiplicand.width; i++){
        x[i] = exp_manager.allocate("x_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(i)}});
        if(i == 0){
            x2[i] = exp_manager.get("zero");
        }
        else{
            x2[i] = exp_manager.allocate("x2_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(i-1)}});
        }
    }
    if(multiplicand.is_signed){
        x[multiplicand.width] = exp_manager.allocate("x_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(multiplicand.width-1)}});
        x2[multiplicand.width] = exp_manager.allocate("x2_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(multiplicand.width-1)}});
        x[multiplicand.width + 1] = exp_manager.allocate("x_" + std::to_string(multiplicand.width + 1), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(multiplicand.width-1)}});
        x2[multiplicand.width + 1] = exp_manager.allocate("x2_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, static_cast<short int>(multiplicand.width-1)}});
    }else{
        x[multiplicand.width] = exp_manager.get("zero");
        x2[multiplicand.width] = exp_manager.get("zero");
        x[multiplicand.width + 1] = exp_manager.get("zero");
        x2[multiplicand.width + 1] = exp_manager.get("zero");
    }

    // 3x is generated by 2x + multiplicand. The adder is implemented as ripple carry adder.
    BoolExp * c = exp_manager.get("zero");
    x3.resize(multiplicand.width + 2);
    for (int i = 0; i < multiplicand.width + 2; i++)
    {
        x3[i] = exp_manager.allocate("x3_" + std::to_string(i), XOR, std::vector<BoolExp *>{x[i], x2[i], c});
        BoolExp *c0 = exp_manager.allocate("x3_c0_" + std::to_string(i), NAND, std::vector<BoolExp *>{x[i], x2[i]});
        BoolExp *c1 = exp_manager.allocate("x3_c1_" + std::to_string(i), NAND, std::vector<BoolExp *>{x[i], c});
        BoolExp *c2 = exp_manager.allocate("x3_c2_" + std::to_string(i), NAND, std::vector<BoolExp *>{x2[i], c});
        c = exp_manager.allocate("x3_c_" + std::to_string(i), NAND, std::vector<BoolExp *>{c0, c1, c2});
    }

    // note that rows_pps includes the last row for negative correction bit
    rows_pps = (multiplier.width + 1) / 2 + multiplier.is_signed ? 1 : 0;
    cols_pps = multiplicand.width + multiplier.width;
    pps.resize(rows_pps);
    // normal4 encoder
    n4es.resize(rows_pps - multiplier.is_signed ? 1 : 0);
    for(int i = 0; i < n4es.size(); i++){
        n4es[i].s3 = exp_manager.allocate("n4es_s3_" + std::to_string(i), AND, std::vector<BoolExp*>{y[2*i+1], y[2*i]});
        n4es[i].s2 = exp_manager.allocate("n4es_s2_" + std::to_string(i), AND, std::vector<BoolExp*>{y[2*i+1], ny[2*i]});
        n4es[i].s1 = exp_manager.allocate("n4es_s1_" + std::to_string(i), AND, std::vector<BoolExp*>{ny[2*i+1], y[2*i]});
    }  

    bool is_even = multiplier.width % 2 == 0;
    for(int i = 0; i < n4es.size(); i++){
        auto & pp = pps[i];
        pp.resize(cols_pps, PPBit());

        auto & ne = n4es[i];
        bool is_last_row = i == n4es.size() - 1;

        if(is_last_row && multiplier.is_signed){
            auto & pp_last = pps.back();
            pp_last.resize(cols_pps, PPBit());
            pp_last[2 * i].bit_type = BIT_EXPRESSION;
            OpBit c = (OpBit){1, 0, static_cast<short int>(multiplier.width - 1)};
            pp_last[2 * i].expression = exp_manager.allocate("pp_last_" + std::to_string(i), AND, std::vector<OpBit>{c});
        }

        for (int j = 0; j < multiplicand.width + 2 && (2 * i + j) < cols_pps; j++)
        {
            BoolExp * ppx3, * ppx2, * ppx;
            ppx3 = ppx2 = ppx = nullptr;           
            if(is_last_row && multiplier.is_signed){
                BoolExp * nx, * nx2;
                nx = exp_manager.allocate("ppnx_"+std::to_string(i)+"_"+std::to_string(j), NOT, std::vector<BoolExp*>{x[j]});
                nx2 = exp_manager.allocate("ppnx2_"+std::to_string(i)+"_"+std::to_string(j), NOT, std::vector<BoolExp*>{x2[j]});
                ppx3 = exp_manager.allocate("ppx3_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{nx, ne.s3});
                ppx2 = exp_manager.allocate("ppx2_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{nx2, ne.s2});
            }
            else
            {
                ppx3 = exp_manager.allocate("ppx3_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{x3[j], ne.s3});
                ppx2 = exp_manager.allocate("ppx2_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{x2[j], ne.s2});
            }
            ppx = exp_manager.allocate("ppx_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{x[j], ne.s1});
            pp[2 * i + j].bit_type = BIT_EXPRESSION;
            pp[2 * i + j].expression = exp_manager.allocate("pp_" + std::to_string(i) + "_" + std::to_string(j), NAND, std::vector<BoolExp *>{ppx3, ppx2, ppx});
        }
    }
}


void MultiplierGenerator::count_pps(int & num_max_stages)
{
    num_stages = 0;
    ct_pps.clear();
    ct_pps.resize(1, std::vector<int>(cols_pps, 0));

    for (int icol = 0; icol < cols_pps; icol++)
    {
        for (int irow = 0; irow < rows_pps; irow++)
        {
            if (pps[irow][icol].bit_type != BIT_NONE)
            {
                ct_pps[0][icol]++;
            }
        }
    }

    int norder = (int)ceil(log(rows_pps) / log(3.0));
    num_max_stages = (int)ceil((norder * log(3.0) - log(2.0)) / (log(3.0)-log(2.0)));
    num_max_stages += 1;
}

void MultiplierGenerator::count_fas_and_has(std::vector<int> &num_fas, std::vector<int> &num_has, int & num_max_stages)
{
    num_fas.resize(cols_pps, 0);
    num_has.resize(cols_pps, 0);
    num_stages = 0;
    ct_pps.clear();
    ct_pps.resize(rows_pps, std::vector<int>(cols_pps, 0));

    for (int icol = 0; icol < cols_pps; icol++)
    {
        for (int irow = 0; irow < rows_pps; irow++)
        {
            if (pps[irow][icol].bit_type != BIT_NONE)
            {
                ct_pps[0][icol]++;
            }
        }
        int num_inputs = ct_pps[0][icol];
        if(icol != 0)
            num_inputs += num_has[icol-1] + num_fas[icol-1];
        if (num_inputs > 2)
        {
            num_max_stages += (int)(log(0.5 * (double)(num_inputs - 1)) / log(3)) + 1;
            if (num_inputs % 2 == 0)
                num_fas[icol] = (num_inputs - 2) / 2;
            else
            {
                num_has[icol] = 1;
                num_fas[icol] = (num_inputs - 3) / 2;
            }
        }
    }
}

void MultiplierGenerator::alloc_and_load_ct(
    std::vector<std::vector<int>> &ct_3_2,
    std::vector<std::vector<int>> &ct_2_2,
    std::vector<std::vector<int>> &ct_4_2)
{
    // assigninig compressors according to ct_* assignments
    ct.resize(num_stages, std::vector<std::vector<CTNode>>(cols_pps, std::vector<CTNode>(0)));
    for (int istage = 0; istage < num_stages; istage++){
        for(int icol = 0; icol < cols_pps; icol++){ 
            // compressor assignment of current stage (computed in opt_fas_and_has_assignment)
            int npps = ct_pps[istage][icol];
            auto & cmps = ct[istage][icol];
            int icmp = 0;
            int n_c32 = ct_3_2[istage][icol];
            int n_c22 = ct_2_2[istage][icol];
            int n_c42 = ct_4_2[istage][icol];
            int used = n_c32 * 3 + n_c22 * 2 + n_c42 * 4;
            int npass = npps - used;
            cmps.resize(n_c42 + n_c32 + n_c22 + npass);
            int ipp = 0;
            for(int ic = 0; ic < n_c42; ic++){
                cmps[icmp].type = CT_4_2;
                cmps[icmp].ipp0 = ipp;
                cmps[icmp].ipp1 = ipp + 3;
                cmps[icmp].istage = istage;
                cmps[icmp].icol = icol;
                ipp += 4;
                icmp++;
            }
            for(int ic = 0; ic < n_c32; ic++){
                cmps[icmp] = CTNode(ipp, ipp + 2, istage, icol);
                ipp += 3;
                icmp++;
            }
            for(int ic = 0; ic < n_c22; ic++){
                cmps[icmp] = CTNode(ipp, ipp + 1, istage, icol);
                ipp += 2;
                icmp++;
            }
            for(int ipass = 0; ipass < npass; ipass++){
                cmps[icmp] = CTNode(ipp, istage, icol);
                ipp++;
                icmp++;
            }
        }
    }

    ct_ipin.resize(num_stages, std::vector<std::vector<CTNodePin>>(cols_pps, std::vector<CTNodePin>(0))); // adder inputs of current stage 
    ct_opin.resize(num_stages+1, std::vector<std::vector<CTNodePin>>(cols_pps, std::vector<CTNodePin>(0))); // adder outputs of previous stage defines pps in current stage
    pin_assign.resize(num_stages, std::vector<std::vector<int>>(cols_pps, std::vector<int>(0))); // pin assignment for each stage, column, pin index

    // initially, interconnect assignment is identity
    for (int istage = 0; istage < num_stages; istage++)
    {
        for (int icol = 0; icol < cols_pps; icol++)
        {
            int npps = ct_pps[istage][icol];
            pin_assign[istage][icol].resize(npps);
            for (int ipps = 0; ipps < npps; ipps++)
            {
                pin_assign[istage][icol][ipps] = ipps;
            }
        }
    }

    // pin correspondance table between outputs of compressors in istage-1 and inputs of compressors in istage
    for (int istage = 0; istage < num_stages + 1 /*pp stages is number of adder stages + 1*/; istage++)
    {
        for(int icol = 0; icol < cols_pps; icol++){
            int npps = ct_pps[istage][icol];

            // opin correspondance to outputs of compressors at (istage, icol)
            auto & opins = ct_opin[istage][icol];
            if(istage == 0){
                opins.resize(npps);
                // initialize stage as -1, icol as icol, icmp and ipin as ipin
                for(int ipp = 0; ipp < npps; ipp++){
                    opins[ipp] = CTNodePin(-1, icol, ipp, ipp); // stage -1 means this is the first stage
                }
            }else{
                int ipps = 0;
                opins.resize(npps);
                // carry output pins (0th column does not have carry pps)
                if(icol != 0){
                    auto & cmps = ct[istage-1][icol-1];
                    for(int icmp = 0; icmp < cmps.size(); icmp++){
                        int ncouts = compressor_carry_count(cmps[icmp].type);
                        if (ncouts == 0) continue;
                        cmps[icmp].couts.resize(ncouts, -1);
                        for(int icout = 0; icout < ncouts; icout++){
                            opins[ipps] = CTNodePin(istage-1, icol-1, icmp, 1 + icout);
                            cmps[icmp].couts[icout] = ipps;
                            ipps++;
                        }
                    }
                }

                // sum ouptut pins
                auto & cmps = ct[istage-1][icol];
                for(int icmp = 0; icmp < cmps.size(); icmp++){
                    int ninputs = compressor_input_count(cmps[icmp].type);
                    if (ninputs == 0) continue;
                    opins[ipps] = CTNodePin(istage-1, icol, icmp, 0);
                    cmps[icmp].sum = ipps;
                    ipps++;
                }

            }

            if(istage == num_stages) continue; // no input pins for the last stage

            // ipin correspondance to inputs of compressors at (istage, icol)
            auto & ipins = ct_ipin[istage][icol];
            ipins.resize(npps);
            int ipp = 0;
            auto & cmps = ct[istage][icol];
            for (int icmp = 0; icmp < cmps.size(); icmp++)
            {
                int ninputs = compressor_input_count(cmps[icmp].type);
                for (int ipin = 0; ipin < ninputs; ipin++)
                {
                    ipins[ipp + ipin] = CTNodePin(istage, icol, icmp, ipin);
                }
                ipp += ninputs;
            }
        }
    }
}

void MultiplierGenerator::alloc_and_load_ct_legacy(
    std::vector<std::vector<int>> &ct_fas,
    std::vector<std::vector<int>> &ct_has)
{
    ct.resize(num_stages, std::vector<std::vector<CTNode>>(cols_pps, std::vector<CTNode>(0)));
    for (int istage = 0; istage < num_stages; istage++){
        for(int icol = 0; icol < cols_pps; icol++){
            int npps = ct_pps[istage][icol];
            auto & cmps = ct[istage][icol];
            int icmp = 0;
            int n_fa = ct_fas[istage][icol];
            int n_ha = ct_has[istage][icol];
            int used = n_fa * 3 + n_ha * 2;
            int npass = npps - used;
            cmps.resize(n_fa + n_ha + npass);
            int ipp = 0;
            for(int ic = 0; ic < n_fa; ic++){
                cmps[icmp] = CTNode(ipp, ipp + 2, istage, icol);
                ipp += 3;
                icmp++;
            }
            for(int ic = 0; ic < n_ha; ic++){
                cmps[icmp] = CTNode(ipp, ipp + 1, istage, icol);
                ipp += 2;
                icmp++;
            }
            for(int ipass = 0; ipass < npass; ipass++){
                cmps[icmp] = CTNode(ipp, istage, icol);
                ipp++;
                icmp++;
            }
        }
    }

    ct_ipin.resize(num_stages, std::vector<std::vector<CTNodePin>>(cols_pps, std::vector<CTNodePin>(0)));
    ct_opin.resize(num_stages+1, std::vector<std::vector<CTNodePin>>(cols_pps, std::vector<CTNodePin>(0)));
    pin_assign.resize(num_stages, std::vector<std::vector<int>>(cols_pps, std::vector<int>(0)));

    for (int istage = 0; istage < num_stages; istage++)
    {
        for (int icol = 0; icol < cols_pps; icol++)
        {
            int npps = ct_pps[istage][icol];
            pin_assign[istage][icol].resize(npps);
            for (int ipps = 0; ipps < npps; ipps++)
            {
                pin_assign[istage][icol][ipps] = ipps;
            }
        }
    }

    for (int istage = 0; istage < num_stages + 1; istage++)
    {
        for(int icol = 0; icol < cols_pps; icol++){
            int npps = ct_pps[istage][icol];

            auto & opins = ct_opin[istage][icol];
            if(istage == 0){
                opins.resize(npps);
                for(int ipp = 0; ipp < npps; ipp++){
                    opins[ipp] = CTNodePin(-1, icol, ipp, ipp);
                }
            }else{
                int ipps = 0;
                opins.resize(npps);
                if(icol != 0){
                    auto & cmps = ct[istage-1][icol-1];
                    for(int icmp = 0; icmp < cmps.size(); icmp++){
                        int ncouts = compressor_carry_count(cmps[icmp].type);
                        if (ncouts == 0) continue;
                        cmps[icmp].couts.resize(ncouts, -1);
                        for(int icout = 0; icout < ncouts; icout++){
                            opins[ipps] = CTNodePin(istage-1, icol-1, icmp, 1 + icout);
                            cmps[icmp].couts[icout] = ipps;
                            ipps++;
                        }
                    }
                }

                auto & cmps = ct[istage-1][icol];
                for(int icmp = 0; icmp < cmps.size(); icmp++){
                    int ninputs = compressor_input_count(cmps[icmp].type);
                    if (ninputs == 0) continue;
                    opins[ipps] = CTNodePin(istage-1, icol, icmp, 0);
                    cmps[icmp].sum = ipps;
                    ipps++;
                }
            }

            if(istage == num_stages) continue;

            auto & ipins = ct_ipin[istage][icol];
            ipins.resize(npps);
            int ipp = 0;
            auto & cmps = ct[istage][icol];
            for (int icmp = 0; icmp < cmps.size(); icmp++)
            {
                int ninputs = compressor_input_count(cmps[icmp].type);
                for (int ipin = 0; ipin < ninputs; ipin++)
                {
                    ipins[ipp + ipin] = CTNodePin(istage, icol, icmp, ipin);
                }
                ipp += ninputs;
            }
        }
    }
}

// Builds CSA tree for given partial products.
// The algorithm is based on the paper "UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators" by Dongsheng Zuo
void MultiplierGenerator::build_ct(bool enable_c42, bool use_direct_ilp)
{
    int num_max_stages = 0;
    if (use_direct_ilp) {
        count_pps(num_max_stages);

        std::vector<std::vector<int>> ct_3_2;
        std::vector<std::vector<int>> ct_2_2;
        std::vector<std::vector<int>> ct_4_2;

        opt_ct_assignment(ct_3_2, ct_2_2, ct_4_2, num_max_stages, enable_c42);
        alloc_and_load_ct(ct_3_2, ct_2_2, ct_4_2);
    } else {
        std::vector<int> num_fas(cols_pps, 0);
        std::vector<int> num_has(cols_pps, 0);
        count_fas_and_has(num_fas, num_has, num_max_stages);

        std::vector<std::vector<int>> ct_fas;
        std::vector<std::vector<int>> ct_has;
        opt_fas_and_has_assignment(num_fas, num_has, ct_fas, ct_has, num_max_stages);
        alloc_and_load_ct_legacy(ct_fas, ct_has);
    }

    // UFO-MAC paper does not describe the wire assignment clearly, and it seems infeasible to assign wires optimally.
    // Thus we assign wires in a simple way.
    opt_ct_wire_assignment();
}

void MultiplierGenerator::opt_ct_assignment(
                                             std::vector<std::vector<int>> &ct_3_2,
                                             std::vector<std::vector<int>> &ct_2_2,
                                             std::vector<std::vector<int>> &ct_4_2,
                                             int num_max_stages,
                                             bool enable_c42)
{
    auto t_start = std::chrono::high_resolution_clock::now();

    std::vector<int> initial_pps = ct_pps[0];
    ct_3_2.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_2_2.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_4_2.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_pps.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    for (int j = 0; j < cols_pps; ++j) {
        ct_pps[0][j] = initial_pps[j];
    }

    int cols_pps_local = ct_pps[0].size();

    // Import OR-Tools
    namespace operations_research = operations_research;

    // Create the solver
    operations_research::MPSolver solver("opt_ct_assignment", operations_research::MPSolver::CBC_MIXED_INTEGER_PROGRAMMING);

    // Variables
    std::vector<std::vector<operations_research::MPVariable*>> x_c32(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> x_c22(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> x_c42(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> x_pp(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> y(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));

    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps; ++j) {
            x_c32[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_c32_" + std::to_string(i) + "_" + std::to_string(j));
            x_c22[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_c22_" + std::to_string(i) + "_" + std::to_string(j));
            x_c42[i][j] = solver.MakeIntVar(0, enable_c42 ? solver.infinity() : 0.0, "x_c42_" + std::to_string(i) + "_" + std::to_string(j));
            x_pp[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_pp_" + std::to_string(i) + "_" + std::to_string(j));
            y[i][j] = solver.MakeBoolVar("y_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    const int M = cols_pps_local * rows_pps;

    // Constraints
    for (int j = 0; j < cols_pps_local; ++j) {
        operations_research::MPConstraint* num_pps_constraint = solver.MakeRowConstraint(ct_pps[0][j], ct_pps[0][j]);
        num_pps_constraint->SetCoefficient(x_pp[0][j], 1);

        for (int i = 0; i < num_max_stages; ++i) {
            operations_research::MPConstraint *pp_sufficient_constraint = solver.MakeRowConstraint(0, solver.infinity());
            pp_sufficient_constraint->SetCoefficient(x_pp[i][j], 1);
            pp_sufficient_constraint->SetCoefficient(x_c32[i][j], -3);
            pp_sufficient_constraint->SetCoefficient(x_c22[i][j], -2);
            pp_sufficient_constraint->SetCoefficient(x_c42[i][j], -4);
        }

        for (int i = 1; i < num_max_stages; ++i) {
            operations_research::MPConstraint* pp_update_constraint = solver.MakeRowConstraint(0,0);
            pp_update_constraint->SetCoefficient(x_pp[i][j], -1);
            pp_update_constraint->SetCoefficient(x_pp[i-1][j], 1);
            pp_update_constraint->SetCoefficient(x_c32[i-1][j], -2);
            pp_update_constraint->SetCoefficient(x_c22[i-1][j], -1);
            pp_update_constraint->SetCoefficient(x_c42[i-1][j], -3);
            if (j > 0) {
                pp_update_constraint->SetCoefficient(x_c32[i-1][j-1], 1);
                pp_update_constraint->SetCoefficient(x_c22[i-1][j-1], 1);
                pp_update_constraint->SetCoefficient(x_c42[i-1][j-1], 2);
            }
        }

        for (int i = 0; i < num_max_stages; ++i)
        {
            operations_research::MPConstraint *y_link_constraint = solver.MakeRowConstraint(0, solver.infinity());
            y_link_constraint->SetCoefficient(y[i][j], M);
            y_link_constraint->SetCoefficient(x_c32[i][j], -1);
            y_link_constraint->SetCoefficient(x_c22[i][j], -1);
            y_link_constraint->SetCoefficient(x_c42[i][j], -1);
        }

        operations_research::MPConstraint* final_pp_constraint = solver.MakeRowConstraint(0, 2);
        final_pp_constraint->SetCoefficient(x_pp[num_max_stages - 1][j], 1);
    }

    // Minimize the maximum stage where compressors are assigned
    operations_research::MPVariable *min_stages = solver.MakeIntVar(0, num_max_stages, "min_stages");
    for (int i = 0; i < num_max_stages; ++i)
    {
        for (int j = 0; j < cols_pps_local; ++j)
        {
            operations_research::MPConstraint *min_stage_constraint = solver.MakeRowConstraint(0, solver.infinity());
            min_stage_constraint->SetCoefficient(min_stages, 1);
            min_stage_constraint->SetCoefficient(y[i][j], -(i+1));
        }
    }

    // Set the objective to minimize min_stages, then minimize compressor count
    operations_research::MPObjective* objective = solver.MutableObjective();
    const double stage_weight = static_cast<double>(rows_pps * cols_pps_local * 10);
    objective->SetCoefficient(min_stages, stage_weight);
    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps_local; ++j) {
            objective->SetCoefficient(x_c32[i][j], 1.0);
            objective->SetCoefficient(x_c22[i][j], 1.0);
            objective->SetCoefficient(x_c42[i][j], 0.9);
        }
    }
    objective->SetMinimization();

    // Solve the problem
    const operations_research::MPSolver::ResultStatus result_status = solver.Solve();

    if (result_status != operations_research::MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution." << std::endl;
        return;
    }

    num_stages = static_cast<int>(min_stages->solution_value());

    for (int i = 0; i < num_max_stages; ++i) {
        int is_pp_exist = false;
        for (int j = 0; j < cols_pps_local; ++j) {
            ct_3_2[i][j] = static_cast<int>(x_c32[i][j]->solution_value());
            ct_2_2[i][j] = static_cast<int>(x_c22[i][j]->solution_value());
            ct_4_2[i][j] = static_cast<int>(x_c42[i][j]->solution_value());
            ct_pps[i][j] = static_cast<int>(x_pp[i][j]->solution_value());
            if (ct_pps[i][j] > 0) is_pp_exist = true;
        }
        if(is_pp_exist && i >= num_stages) {
            break;
        }
    }

    int total_c32 = 0, total_c22 = 0, total_c42 = 0;
    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps_local; ++j) {
            total_c32 += ct_3_2[i][j];
            total_c22 += ct_2_2[i][j];
            total_c42 += ct_4_2[i][j];
        }
    }
    auto t_end = std::chrono::high_resolution_clock::now();
    double elapsed_sec = std::chrono::duration<double>(t_end - t_start).count();
    std::cout << "[INFO] opt_ct_assignment: num_stages = " << num_stages
              << ", num_max_stages = " << num_max_stages
              << ", total C32 = " << total_c32
              << ", total C22 = " << total_c22
              << ", total C42 = " << total_c42
              << ", elapsed = " << elapsed_sec << " sec" << std::endl;
}

void MultiplierGenerator::opt_fas_and_has_assignment(
                                             std::vector<int> &num_fas, std::vector<int> &num_has,
                                             std::vector<std::vector<int>> &ct_fas, std::vector<std::vector<int>> &ct_has, int num_max_stages)
{
    auto t_start = std::chrono::high_resolution_clock::now();

    ct_fas.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_has.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_pps.resize(num_max_stages, std::vector<int>(cols_pps, 0));

    int cols_pps_local = ct_pps[0].size();
    int M = 0;
    for (auto n : num_fas) M += n;
    for (auto n : num_has) M += n;

    namespace operations_research = operations_research;
    operations_research::MPSolver solver("opt_fas_and_has_assignment", operations_research::MPSolver::CBC_MIXED_INTEGER_PROGRAMMING);

    std::vector<std::vector<operations_research::MPVariable*>> x_fa(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> x_ha(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> x_pp(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));
    std::vector<std::vector<operations_research::MPVariable*>> y(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps_local));

    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps_local; ++j) {
            x_fa[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_fa_" + std::to_string(i) + "_" + std::to_string(j));
            x_ha[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_ha_" + std::to_string(i) + "_" + std::to_string(j));
            x_pp[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_pp_" + std::to_string(i) + "_" + std::to_string(j));
            y[i][j] = solver.MakeBoolVar("y_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    for (int j = 0; j < cols_pps_local; ++j) {
        operations_research::MPConstraint* num_pps_constraint = solver.MakeRowConstraint(ct_pps[0][j], ct_pps[0][j]);
        num_pps_constraint->SetCoefficient(x_pp[0][j], 1);

        operations_research::MPConstraint* total_fas_constraint = solver.MakeRowConstraint(num_fas[j], num_fas[j]);
        operations_research::MPConstraint* total_has_constraint = solver.MakeRowConstraint(num_has[j], num_has[j]);
        for (int i = 0; i < num_max_stages; ++i) {
            total_fas_constraint->SetCoefficient(x_fa[i][j], 1);
            total_has_constraint->SetCoefficient(x_ha[i][j], 1);
        }

        for (int i = 1; i < num_max_stages; ++i) {
            operations_research::MPConstraint* pp_update_constraint = solver.MakeRowConstraint(0,0);
            pp_update_constraint->SetCoefficient(x_pp[i][j], -1);
            pp_update_constraint->SetCoefficient(x_fa[i-1][j], -2);
            pp_update_constraint->SetCoefficient(x_ha[i-1][j], -1);
            if (j > 0) {
                pp_update_constraint->SetCoefficient(x_fa[i-1][j-1], 1);
                pp_update_constraint->SetCoefficient(x_ha[i-1][j-1], 1);
            }
            pp_update_constraint->SetCoefficient(x_pp[i-1][j], 1);
        }

        for (int i = 0; i < num_max_stages; ++i) {
            operations_research::MPConstraint *pp_sufficient_constraint = solver.MakeRowConstraint(0, solver.infinity());
            pp_sufficient_constraint->SetCoefficient(x_pp[i][j], 1);
            pp_sufficient_constraint->SetCoefficient(x_fa[i][j], -3);
            pp_sufficient_constraint->SetCoefficient(x_ha[i][j], -2);
        }

        for (int i = 0; i < num_max_stages; ++i)
        {
            operations_research::MPConstraint *y_link_constraint = solver.MakeRowConstraint(0, solver.infinity());
            y_link_constraint->SetCoefficient(y[i][j], M);
            y_link_constraint->SetCoefficient(x_fa[i][j], -1);
            y_link_constraint->SetCoefficient(x_ha[i][j], -1);
        }
    }

    operations_research::MPVariable *min_stages = solver.MakeIntVar(0, num_max_stages, "min_stages");
    for (int i = 0; i < num_max_stages; ++i)
    {
        for (int j = 0; j < cols_pps_local; ++j)
        {
            operations_research::MPConstraint *min_stage_constraint = solver.MakeRowConstraint(0, solver.infinity());
            min_stage_constraint->SetCoefficient(min_stages, 1);
            min_stage_constraint->SetCoefficient(y[i][j], -(i+1));
        }
    }

    operations_research::MPObjective* objective = solver.MutableObjective();
    objective->SetCoefficient(min_stages, 1);
    objective->SetMinimization();

    const operations_research::MPSolver::ResultStatus result_status = solver.Solve();
    if (result_status != operations_research::MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution." << std::endl;
        return;
    }

    num_stages = static_cast<int>(min_stages->solution_value());

    for (int i = 0; i < num_max_stages; ++i) {
        int is_pp_exist = false;
        for (int j = 0; j < cols_pps_local; ++j) {
            ct_fas[i][j] = static_cast<int>(x_fa[i][j]->solution_value());
            ct_has[i][j] = static_cast<int>(x_ha[i][j]->solution_value());
            ct_pps[i][j] = static_cast<int>(x_pp[i][j]->solution_value());
            if( ct_pps[i][j] > 0 ) is_pp_exist = true;
        }
        if(is_pp_exist && i >= num_stages) {
            break;
        }
    }

    int total_fas = 0, total_has = 0;
    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps_local; ++j) {
            total_fas += ct_fas[i][j];
            total_has += ct_has[i][j];
        }
    }
    auto t_end = std::chrono::high_resolution_clock::now();
    double elapsed_sec = std::chrono::duration<double>(t_end - t_start).count();
    std::cout << "[INFO] opt_fas_and_has_assignment: num_stages = " << num_stages
              << ", num_max_stages = " << num_max_stages
              << ", total FAs = " << total_fas
              << ", total HAs = " << total_has
              << ", elapsed = " << elapsed_sec << " sec" << std::endl;
}

double MultiplierGenerator::do_ct_sta()
{
    // ct_opin[stage][col] : output to pps[stage][col] 
    // ct_ipin[stage][col] : input from pps[stage][col] 
    // pin_assign[stage][col] : assignment ct_opin[stage][col] to ct_ipin[stage+1][col]
    // fill path delay down to last stage for given ct_assign. 
    // back propagate required time and slack.

    // initialize timing graph
    for(int istage = 0; istage < pin_assign.size(); istage++){
        for(int icol = 0; icol < pin_assign[istage].size(); icol++){
            for(int ipp = 0; ipp < pin_assign[istage][icol].size(); ipp++){
                ct_opin[istage][icol][ipp].init_timing_info();
                ct_ipin[istage][icol][ipp].init_timing_info();
            }
        }
    }

    // propagate arrival time
    auto get_sum_delay = [&](CompressorType type, int ipin) -> float {
        switch (type) {
            case CT_1_1:
                return 0.0f;
            case CT_2_2:
                return dhas[ipin][HA_SUM];
            case CT_3_2:
                return dfas[ipin][FA_SUM];
            case CT_4_2: {
                if (ipin == 3) return dfas[FA_B][FA_SUM];
                if (ipin == 2) return dfas[FA_CIN][FA_SUM] + dfas[FA_A][FA_SUM];
                return dfas[FA_A][FA_SUM] + dfas[FA_A][FA_SUM];
            }
            default:
                return 0.0f;
        }
    };

    auto get_carry_delay = [&](CompressorType type, int ipin) -> float {
        switch (type) {
            case CT_2_2:
                return dhas[ipin][HA_COUT];
            case CT_3_2:
                return dfas[ipin][FA_COUT];
            case CT_4_2: {
                float d_c1 = (ipin == 2) ? dfas[FA_CIN][FA_COUT] : dfas[FA_A][FA_COUT];
                float d_c2 = (ipin == 3) ? dfas[FA_B][FA_COUT] : (dfas[FA_A][FA_SUM] + dfas[FA_A][FA_COUT]);
                return std::max(d_c1, d_c2);
            }
            default:
                return 0.0f;
        }
    };

    for(int istage = 0; istage < pin_assign.size(); istage++){
        for(int icol = 0; icol < pin_assign[istage].size(); icol++){
            for(int ipp = 0; ipp < pin_assign[istage][icol].size(); ipp++){
                
                int opin = pin_assign[istage][icol][ipp];
                auto & ipin = ct_ipin[istage][icol][ipp];
                double tarr = ct_opin[istage][icol][opin].tarr;
                int icmp_stage = ipin.istage;
                int icmp_col = ipin.icol;
                int icmp = ipin.icmp;
                int icmp_pin = ipin.ipin;
                auto & cmp = ct[istage][icol][icmp];
                int num_pins = compressor_input_count(cmp.type);
                if(num_pins == 1){ // no delay (wire only)
                    ct_opin[istage+1][icol][cmp.sum].set_tarr(tarr);
                }else{
                    ct_opin[istage+1][icol][cmp.sum].set_tarr(tarr + get_sum_delay(cmp.type, icmp_pin));
                    int ncouts = compressor_carry_count(cmp.type);
                    if(icol+1 < cols_pps && ncouts > 0){
                        float carry_delay = get_carry_delay(cmp.type, icmp_pin);
                        for (int icout = 0; icout < ncouts; icout++) {
                            if (icout < cmp.couts.size() && cmp.couts[icout] >= 0) {
                                ct_opin[istage+1][icol+1][cmp.couts[icout]].set_tarr(tarr + carry_delay);
                            }
                        }
                    }
                }
            }
        }  
    }

    // determine maximum delay 
    int istage = pin_assign.size();
    auto & opin = ct_opin[istage];
    double tmax = 0;
    for(int icol = 0; icol < pin_assign[istage-1].size(); icol++){
        auto & opins = ct_opin[istage][icol];
        for(int ipp = 0; ipp < opins.size(); ipp++){
            tmax = std::max(tmax, opins[ipp].tarr);
        }
    }

    // determine required time for output
    istage--;
    for(int icol = 0; icol < pin_assign[istage].size(); icol++){
        auto & opins = ct_opin[istage + 1][icol];
        for(int ipp = 0; ipp < opins.size(); ipp++){
            opins[ipp].treq = tmax;
            opins[ipp].tslack = opins[ipp].treq - opins[ipp].tarr;
        }
    }

    for(; istage >= 0; istage--){
        for(int icol = 0; icol < pin_assign[istage].size(); icol++){
            auto & opins = ct_opin[istage][icol];
            auto & ipins = ct_ipin[istage][icol];
            auto & opins_sum = ct_opin[istage+1][icol];
            std::vector<CTNodePin> *opins_cout = nullptr;
            if (icol + 1 < ct_opin[istage+1].size()) {
                opins_cout = &ct_opin[istage+1][icol+1];
            }
            // computing treq
            for (int ipp = 0; ipp < ipins.size(); ipp++){
                int icmp_stage = ipins[ipp].istage;
                int icmp_col = ipins[ipp].icol;
                int icmp = ipins[ipp].icmp;
                int icmp_pin = ipins[ipp].ipin;
                auto & cmp = ct[icmp_stage][icmp_col][icmp];
                int num_pins = compressor_input_count(cmp.type);
                if(num_pins == 1){
                    ipins[ipp].treq = opins_sum[cmp.sum].treq;
                }else{
                    float treq_sum = opins_sum[cmp.sum].treq - get_sum_delay(cmp.type, icmp_pin);
                    float treq_carry = FLT_MAX;
                    int ncouts = compressor_carry_count(cmp.type);
                    if(opins_cout && ncouts > 0){
                        float carry_delay = get_carry_delay(cmp.type, icmp_pin);
                        for (int icout = 0; icout < ncouts; icout++) {
                            if (icout < cmp.couts.size() && cmp.couts[icout] >= 0) {
                                float cand = static_cast<float>((*opins_cout)[cmp.couts[icout]].treq - carry_delay);
                                treq_carry = std::min(treq_carry, cand);
                            }
                        }
                    }
                    ipins[ipp].treq = std::min(treq_sum, treq_carry);
                }
            }

            // transfer treq back from ipin to opin 
            for(int ipp = 0; ipp < ipins.size(); ipp++){
                int opin = pin_assign[istage][icol][ipp];
                opins[opin].treq = ipins[ipp].treq;
                opins[opin].tslack = opins[opin].treq - opins[opin].tarr;
            }
        }
    }
    return tmax;
}


void MultiplierGenerator::opt_ct_wire_assignment()
{
    if(num_stages == 0) return; // no stages, nothing to do
    
    double tmax = do_ct_sta();
    double tmax_ini = tmax;
    std::cout << "[INFO] Starting wire assignment optimization: initial max delay = " << tmax_ini << std::endl;
    double dt = 0;
    do {
        // List zero slack ct_opins in every stage
        std::vector<std::tuple<int, int, int>> zero_slack_opins; // (stage, column, pin index)
        for (int istage = 0; istage < pin_assign.size(); ++istage) {
            for (int icol = 0; icol < pin_assign[istage].size(); ++icol) {
                for (int ipps = 0; ipps < pin_assign[istage][icol].size(); ++ipps) {
                    if (ct_opin[istage][icol][ipps].tslack == 0) {
                        zero_slack_opins.emplace_back(istage, icol, ipps);
                    }
                }
            }
        }

        // List feasible swaps within the same (istage,  icol)
        std::tuple<int, int, int, int> best_swap; // (pin1, pin2, stage, col)
        double best_improvement = 0;

        for (const auto& [istage, icol, ipin1] : zero_slack_opins) {
            for (int ipin2 = 0; ipin2 < pin_assign[istage][icol].size(); ++ipin2) {
                if (ipin1 == ipin2) continue; // Skip the same pin

                int opin1 = pin_assign[istage][icol][ipin1];
                int opin2 = pin_assign[istage][icol][ipin2];

                double tarr1 = ct_opin[istage][icol][opin1].tarr;
                double tarr2 = ct_opin[istage][icol][opin2].tarr;
                double tslack2 = ct_opin[istage][icol][opin2].tslack;

                // Check feasibility of the swap
                if (tarr2 < tarr1 && (tarr1 - tarr2) < tslack2) {
                    double improvement = std::abs(tarr1 - tarr2 - tslack2 / 2);

                    if (improvement > best_improvement) {
                        best_swap = {ipin1, ipin2, istage, icol};
                        best_improvement = improvement;
                    }
                }
            }
        }

        // Apply the best swap if found
        if (best_improvement > 0) {
            auto [ipin1, ipin2, istage, icol] = best_swap;
            std::swap(pin_assign[istage][icol][ipin1], pin_assign[istage][icol][ipin2]);
            tmax = do_ct_sta();
        } else {
            break; // Exit the loop if no improvement is found
        }

    } while (true);

    std::cout << "[INFO] Finished wire assignment optimization: final max delay = " << tmax << std::endl;
}

void MultiplierGenerator::build_cpa(CPAType cptype)
{
    // ct_pps[num_stages][icol] is the number of pps in the last stage column icol.
    // cols_pps number of columns in the pps.

    // cpa is built for the lowest column with 2 pps to highest column with 1 or 2 pps. (the length is here denoted as n)
    // Think the length n cpa, n-1 is msb, 0 is lsb.
    // we have (n-1) * (n-2) node placement site in the cpa tree. 
    // Here we denote the node p[i][j] where j <= i-1 means the node accumulates i to jth column. 
    // Basically, at least, we requires output nodes p[n-1][0], p[n-2][0], ..., p[1][0] 
    // and input nodes p[n-1][n-1], p[n-2][n-2], ..., p[1][1] to be placed in the cpa tree. (ripple carry adder)
    // intermediate nodes are placed to exploit the parallelism of the cpa tree.

    // we can optimize cpa tree by iterating following two operations.

    // 1. add and legalize node
    // 2. delete and legalize node

    // by training dqn for these two operations, we can find better cpa tree.
    // but it is not easy to train dqn for this problem because of computation power and time.
    // we merely build well known cpa trees, ripple carry adder, Brent-Kung adder, Kogge-Stone adder, and so on.

    // allocating cpa nodes
    cpa_col_start = cpa_col_end = 0;
    for (int i = 0; i < ct_pps[num_stages].size(); i++){
        if(ct_pps[num_stages][i] > 1){
            cpa_col_start = i;
            break;
        }
    }

    std::vector<int> num_cpa_inputs; 
    for (int i = cpa_col_start; i < ct_pps[num_stages].size(); i++){
        if(ct_pps[num_stages][i] > 0){
            num_cpa_inputs.push_back(ct_pps[num_stages][i]);
            cpa_col_end = i;
        }
    }
    
    // the lsbs and the msbs of the adder can only be 1 bit adder. 
    cpa.init(num_cpa_inputs.size(), cptype);
}
