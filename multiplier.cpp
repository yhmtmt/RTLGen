#include <iostream>
#include <vector>
#include <fstream>
#include <limits>
#include <cmath> // Include cmath for log2
#include <bitset>
#include <regex>
#include <numeric> // Include for std::accumulate
#include <ortools/linear_solver/linear_solver.h>
#include "multiplier.hpp"

///////////////////////////////////////////////////////////////////////////////////////////////// MultiplierGenerator methods
void MultiplierGenerator::build(Operand multiplicand, Operand multiplier,
                                           CTType ctype, PPType ptype, const std::string &module_name)
{
    gen_pp(multiplicand, multiplier, ptype);
    build_ct();
    build_cpa();
    dump_hdl(multiplicand, multiplier, module_name);
    dump_hdl_tb(multiplicand, multiplier, module_name);
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
    int width_cpa = cpa.nodes.size();
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cta;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] ctb;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] cts;\n";
    verilog_file << "  wire [" << width_cpa - 1 << ":0] ctc;\n\n";

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
    // thus if width_cpa is less than cols_pps, we need to add ctc[width_cpa-1] to the msb of the product.
    for (int icol = 0; icol < cpa_col_start; icol++)
        verilog_file << "  assign product[" << icol << "] = pp_" << num_stages << "_" << icol << "_" << 0 << ";\n"; // zero padding

    verilog_file << "  assign product[" << cpa_col_end << ":" << cpa_col_start << "] = cts;\n"; // cts is the sum output of the cpa
    if (cpa_col_end + 1 <  cols_pps)
    {
        verilog_file << "  assign product[" << cols_pps - 1 << "] = ctc[" << width_cpa - 1 << "];\n";
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
    int width_p = cols_pps;
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
                    int icout = node.cout; // get_pp_out_index(istage+1, icol+1, icmp, 1);
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
                    int icout = node.cout; // get_pp_out_index(istage+1, icol+1, icmp, 1);
                    verilog_file << "  MG_HA ha_" << istage << "_" << icol << "_" << icmp << "(\n";
                    verilog_file << "    .a(pp_" << istage << "_" << icol << "_" << ia << "),\n";
                    verilog_file << "    .b(pp_" << istage << "_" << icol << "_" << ib << "),\n";
                    verilog_file << "    .sum(pp_" << istage + 1 << "_" << icol << "_" << isum << "),\n";
                    if(icout < 0)
                        verilog_file << "    .cout()\n";
                    else
                        verilog_file << "    .cout(pp_" << istage + 1 << "_" << icol + 1 << "_" << icout << ")\n";
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
            pp[i + j].expression = exp_manager.allocate("pp_" + std::to_string(i) + "_" + std::to_string(i + j), AND, std::vector<OpBit>{(OpBit){0, 0, j}, (OpBit){1, 0, i}}); // multiplicand[j] * multiplier[i]
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
                                     NOP, std::vector<OpBit>({(OpBit){1, 0, multiplier.width - 1}})); // sign bit of multiplier

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
            pp[multiplicand.width - 1].expression->setInputs({(OpBit){0, 0, 0}, (OpBit){1, 0, multiplier.width - 1}});

            for (int j = 1; j < multiplicand.width; j++)
            { // (0,1,j):negated multiplicand, (1,0,multiplier.width-1):multiplier's sign bit
                pp[multiplier.width - 1 + j].expression->setInputs({(OpBit){0, 1, j}, (OpBit){1, 0, multiplier.width - 1}});
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
       x[i] = exp_manager.allocate("x_" + std::to_string(i), NOP, {(OpBit){0, 0, i}});
    }
    if(multiplier.is_signed){
        x[multiplicand.width] = exp_manager.allocate("x_" + std::to_string(multiplicand.width), NOP, {(OpBit){0, 0, multiplicand.width-1}}); // sign bit
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
                OpBit bit = (OpBit){1, 0, multiplier.width-1};
                OpBit nbit = (OpBit){1, 1, multiplier.width-1};
                y[i] = exp_manager.allocate("y_" + std::to_string(i-1), NOP, std::vector<OpBit>({bit}));
                ny[i] = exp_manager.allocate("ny_" + std::to_string(i-1), NOP, std::vector<OpBit>({nbit}));                      
            }else{ // sign extension with zero
                y[i] = exp_manager.get("zero");
                ny[i] = exp_manager.get("one");              
            }
        }
        else
        {
            OpBit bit = (OpBit){1, 0, i - 1};
            OpBit nbit = (OpBit){1, 1, i - 1};
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
        y[i] = exp_manager.allocate("y_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){1, 0, i}});
        ny[i] = exp_manager.allocate("ny_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){1, 1, i}});
    }
    if(multiplier.width % 2 == 1){ // extension for odd width multiplier
        if(multiplier.is_signed){
            y[multiplier.width] = exp_manager.allocate("y_" + std::to_string(multiplier.width), NOP, std::vector<OpBit>{(OpBit){1, 0, multiplier.width-1}});
            ny[multiplier.width] = exp_manager.allocate("ny_" + std::to_string(multiplier.width), NOP, std::vector<OpBit>{(OpBit){1, 1, multiplier.width-1}});
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
        x[i] = exp_manager.allocate("x_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){0, 0, i}});
        if(i == 0){
            x2[i] = exp_manager.get("zero");
        }
        else{
            x2[i] = exp_manager.allocate("x2_" + std::to_string(i), NOP, std::vector<OpBit>{(OpBit){0, 0, i-1}});
        }
    }
    if(multiplicand.is_signed){
        x[multiplicand.width] = exp_manager.allocate("x_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, multiplicand.width-1}});
        x2[multiplicand.width] = exp_manager.allocate("x2_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, multiplicand.width-1}});
        x[multiplicand.width + 1] = exp_manager.allocate("x_" + std::to_string(multiplicand.width + 1), NOP, std::vector<OpBit>{(OpBit){0, 0, multiplicand.width-1}});
        x2[multiplicand.width + 1] = exp_manager.allocate("x2_" + std::to_string(multiplicand.width), NOP, std::vector<OpBit>{(OpBit){0, 0, multiplicand.width-1}});
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
            OpBit c = (OpBit){1, 0, multiplier.width - 1};
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


void MultiplierGenerator::count_fas_and_has(std::vector<int> &num_fas, std::vector<int> &num_has, int & num_max_stages)
{
    num_fas.resize(cols_pps, 0);
    num_has.resize(cols_pps, 0);
    num_stages = 0;
    ct_pps.resize(rows_pps, std::vector<int>(cols_pps, 0));

    // counting the number of FAs and HAs for each column
    // we can determine the numbers scanning from younger column to older column by one pass
    for (int icol = 0; icol < cols_pps; icol++)
    {
        // counting pps.
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

void MultiplierGenerator::alloc_and_load_ct(std::vector<std::vector<int>> &ct_fas, std::vector<std::vector<int>> &ct_has)
{
    // assigninig compressors according to ct_fas and ct_has
    ct.resize(num_stages, std::vector<std::vector<CTNode>>(cols_pps, std::vector<CTNode>(0)));
    for (int istage = 0; istage < num_stages; istage++){
        for(int icol = 0; icol < cols_pps; icol++){ 
            // compressor assignment of current stage (computed in opt_fas_and_has_assignment)
            int npps = ct_pps[istage][icol];
            auto & cmps = ct[istage][icol];
            int icmp = 0;
            int nfas = ct_fas[istage][icol];
            int nhas = ct_has[istage][icol];
            int npass = npps - nfas * 3 - nhas * 2;
            cmps.resize(nfas + nhas + npass);
            int ipp = 0;
            for(int ifas = 0; ifas < nfas; ifas++){
                cmps[icmp] = CTNode(ipp, ipp + 2, istage, icol);
                ipp += 3;
                icmp++;
            }
            for(int ihas = 0; ihas < nhas; ihas++){
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
                int nfas = ct_fas[istage-1][icol];
                int nhas = ct_has[istage-1][icol];
                int npass = ct_pps[istage-1][icol] - nfas * 3 - nhas * 2;
                // carry output pins (0th column does not have carry pps)
                if(icol != 0){
                    int nfac = ct_fas[istage-1][icol-1];
                    int nhac = ct_has[istage-1][icol-1];
                    auto & cmps = ct[istage-1][icol-1];
                    int icmp = 0;
                    for(int ifac = 0; ifac < nfac; ifac++){
                        opins[ipps] = CTNodePin(istage-1, icol-1, icmp, 1);
                        cmps[icmp].cout = ipps;
                        ipps++;
                        icmp++;
                    }

                    for(int ihac = 0; ihac < nhac; ihac++){
                        opins[ipps] = CTNodePin(istage-1, icol-1, icmp, 1);
                        cmps[icmp].cout = ipps;
                        ipps++;
                        icmp++;
                    }
                }

                // sum ouptut pins
                int icmp = 0;
                auto & cmps = ct[istage-1][icol];
                for(int ifas = 0; ifas < nfas; ifas++){
                    opins[ipps] = CTNodePin(istage-1, icol, icmp, 0);
                    cmps[icmp].sum = ipps;
                    ipps++;
                    icmp++;
                }

                for(int ihas = 0; ihas < nhas; ihas++){
                    opins[ipps] = CTNodePin(istage-1, icol, icmp, 0);
                    cmps[icmp].sum = ipps;
                    ipps++;
                    icmp++;
                }

                // pass through pins
                for(int ipass = 0; ipass < npass; ipass++){
                    opins[ipps] = CTNodePin(istage-1, icol, icmp, 0);
                    cmps[icmp].sum = ipps;
                    ipps++;
                    icmp++;
                }
            }

            if(istage == num_stages) continue; // no input pins for the last stage

            // ipin correspondance to inputs of compressors at (istage, icol)
            int nfas = ct_fas[istage][icol];
            int nhas = ct_has[istage][icol];
            int npass = npps - nfas * 3 - nhas * 2;

            auto & ipins = ct_ipin[istage][icol];
            ipins.resize(npps);
            int ipp = 0;
            int icmp = 0;
            // input pins of FAs 
            for (int ifas = 0; ifas < nfas; ifas++)
            {
                ipins[ipp] = CTNodePin(istage, icol, icmp, 0);
                ipins[ipp + 1] = CTNodePin(istage, icol, icmp, 1);
                ipins[ipp + 2] = CTNodePin(istage, icol, icmp, 2);
                ipp += 3;
                icmp++;
            }
            // input pins of HAs
            for (int ihas = 0; ihas < nhas; ihas++)
            {
                ipins[ipp] = CTNodePin(istage, icol, icmp, 0);
                ipins[ipp + 1] = CTNodePin(istage, icol, icmp, 1);
                ipp += 2;
                icmp++;
            }

            // pass through pins
            for (int ipass = 0; ipass < npass; ipass++)
            {
                ipins[ipp] = CTNodePin(istage, icol, icmp, 0);
                ipp++;
                icmp++;
            }
        }
    }
}

// Builds CSA tree for given partial products.
// The algorithm is based on the paper "UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators" by Dongsheng Zuo
void MultiplierGenerator::build_ct()
{
    int num_max_stages = 0;
    std::vector<int> num_fas(cols_pps, 0);
    std::vector<int> num_has(cols_pps, 0);

    count_fas_and_has(num_fas, num_has, num_max_stages);
    num_max_stages += 1;

    std::vector<std::vector<int>> ct_fas;
    std::vector<std::vector<int>> ct_has;

    opt_fas_and_has_assignment(num_fas, num_has, ct_fas, ct_has, num_max_stages);

    alloc_and_load_ct(ct_fas, ct_has);

    // UFO-MAC paper does not describe the wire assignment clearly, and it seems infeasible to assign wires optimally.
    // Thus we assign wires in a simple way.
    opt_ct_wire_assignment();
}

void MultiplierGenerator::opt_fas_and_has_assignment(
                                             std::vector<int> &num_fas, std::vector<int> &num_has,
                                             std::vector<std::vector<int>> &ct_fas, std::vector<std::vector<int>> &ct_has, int num_max_stages)
{
    ct_fas.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_has.resize(num_max_stages, std::vector<int>(cols_pps, 0));
    ct_pps.resize(num_max_stages, std::vector<int>(cols_pps, 0));

    int cols_pps = ct_pps[0].size();
    int M = 0;
    for (auto n : num_fas) M += n;
    for (auto n : num_has) M += n;

    // Import OR-Tools
    namespace operations_research = operations_research;

    // Create the solver
    operations_research::MPSolver solver("opt_fas_and_has_assignment", operations_research::MPSolver::CBC_MIXED_INTEGER_PROGRAMMING);

    // Variables
    std::vector<std::vector<operations_research::MPVariable*>> x_fa(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps));
    std::vector<std::vector<operations_research::MPVariable*>> x_ha(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps));
    std::vector<std::vector<operations_research::MPVariable*>> x_pp(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps));
    std::vector<std::vector<operations_research::MPVariable*>> y(num_max_stages, std::vector<operations_research::MPVariable*>(cols_pps));

    for (int i = 0; i < num_max_stages; ++i) {
        for (int j = 0; j < cols_pps; ++j) {
            x_fa[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_fa_" + std::to_string(i) + "_" + std::to_string(j));
            x_ha[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_ha_" + std::to_string(i) + "_" + std::to_string(j));
            x_pp[i][j] = solver.MakeIntVar(0, solver.infinity(), "x_pp_" + std::to_string(i) + "_" + std::to_string(j));
            y[i][j] = solver.MakeBoolVar("y_" + std::to_string(i) + "_" + std::to_string(j));
        }
    }

    // Constraints
    for (int j = 0; j < cols_pps; ++j) {
        operations_research::MPConstraint* num_pps_constraint = solver.MakeRowConstraint(ct_pps[0][j], ct_pps[0][j]);
        num_pps_constraint->SetCoefficient(x_pp[0][j], 1);

        // Ensure the total number of FAs and HAs matches the required number for each column
        operations_research::MPConstraint* total_fas_constraint = solver.MakeRowConstraint(num_fas[j], num_fas[j]);
        operations_research::MPConstraint* total_has_constraint = solver.MakeRowConstraint(num_has[j], num_has[j]);
        for (int i = 0; i < num_max_stages; ++i) {
            total_fas_constraint->SetCoefficient(x_fa[i][j], 1);
            total_has_constraint->SetCoefficient(x_ha[i][j], 1);
        }
        
        // Ensure the number of PPs is updated correctly across stages
        for (int i = 1; i < num_max_stages; ++i) {
            operations_research::MPConstraint* pp_update_constraint = solver.MakeRowConstraint(0,0);
            pp_update_constraint->SetCoefficient(x_pp[i][j], -1);
            pp_update_constraint->SetCoefficient(x_fa[i-1][j], -2); // eq.(8) in the paper is wrong. -2 x_fa[i][j] - x_ha[i][j] should be -2 x_fa[i-1][j] - x_ha[i-1][j]
            pp_update_constraint->SetCoefficient(x_ha[i-1][j], -1);
            if (j > 0) {
                pp_update_constraint->SetCoefficient(x_fa[i-1][j-1], 1);
                pp_update_constraint->SetCoefficient(x_ha[i-1][j-1], 1);
            }
            pp_update_constraint->SetCoefficient(x_pp[i-1][j], 1);
        }

        // Ensure the number of PPs in each stage is sufficient for the assigned adders
        for (int i = 0; i < num_max_stages; ++i) {
            operations_research::MPConstraint *pp_sufficient_constraint = solver.MakeRowConstraint(0, solver.infinity());
            pp_sufficient_constraint->SetCoefficient(x_pp[i][j], 1);
            pp_sufficient_constraint->SetCoefficient(x_fa[i][j], -3);
            pp_sufficient_constraint->SetCoefficient(x_ha[i][j], -2);
        }

        // Link y[i][j] with x_fa[i][j] and x_ha[i][j]
        for (int i = 0; i < num_max_stages; ++i)
        {
            operations_research::MPConstraint *y_link_constraint = solver.MakeRowConstraint(0, solver.infinity());
            y_link_constraint->SetCoefficient(y[i][j], M);
            y_link_constraint->SetCoefficient(x_fa[i][j], -1);
            y_link_constraint->SetCoefficient(x_ha[i][j], -1);
        }
    }

    // Minimize the maximum stage where adders are assigned
    operations_research::MPVariable *min_stages = solver.MakeIntVar(0, num_max_stages, "min_stages");
    for (int i = 0; i < num_max_stages; ++i)
    {
        for (int j = 0; j < cols_pps; ++j)
        {
            // eq (10) in the paper S >= (i+1) y[i][j] . 
            operations_research::MPConstraint *min_stage_constraint = solver.MakeRowConstraint(0, solver.infinity());
            min_stage_constraint->SetCoefficient(min_stages, 1);
            min_stage_constraint->SetCoefficient(y[i][j], -(i+1));
        }
    }

    // Set the objective to minimize min_stages
    operations_research::MPObjective* objective = solver.MutableObjective();
    objective->SetCoefficient(min_stages, 1);
    objective->SetMinimization();

    // Solve the problem
    const operations_research::MPSolver::ResultStatus result_status = solver.Solve();

    if (result_status != operations_research::MPSolver::OPTIMAL) {
        std::cerr << "The problem does not have an optimal solution." << std::endl;
        return;
    }

    // Substitute the minimum value for stages (this value iis adder stages that is one less than the actual number of pp stages. )
    num_stages = static_cast<int>(min_stages->solution_value());

    // Extract the results
    for (int i = 0; i < num_max_stages; ++i) {
        int is_pp_exist = false;
        for (int j = 0; j < cols_pps; ++j) {
            ct_fas[i][j] = static_cast<int>(x_fa[i][j]->solution_value());
            ct_has[i][j] = static_cast<int>(x_ha[i][j]->solution_value());
            ct_pps[i][j] = static_cast<int>(x_pp[i][j]->solution_value());
            if( ct_pps[i][j] > 0 ) is_pp_exist = true;
        }
        if(is_pp_exist && i >= num_stages) {
            // the last stage is num_stages + 1, so we can stop here.
            break;
        }
    }
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
                int num_pins = cmp.ipp1 - cmp.ipp0 + 1;
                if(num_pins == 1){ // no delay (wire only)
                    ct_opin[istage+1][icol][cmp.sum].set_tarr(tarr);
                }else if(num_pins == 2){ // HA
                    ct_opin[istage+1][icol][cmp.sum].set_tarr(tarr + dhas[icmp_pin][HA_SUM]); // sum pin
                    if(icol+1 < cols_pps)
                     ct_opin[istage+1][icol+1][cmp.cout].set_tarr(tarr + dhas[icmp_pin][HA_COUT]); // carry pin
                }else if(num_pins == 3){ // FA 
                    ct_opin[istage+1][icol][cmp.sum].set_tarr(tarr + dfas[icmp_pin][FA_SUM]); // sum pin
                    if(icol+1 < cols_pps)
                        ct_opin[istage+1][icol+1][cmp.cout].set_tarr(tarr + dfas[icmp_pin][FA_COUT]); // carry pin
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
            auto & opins_cout = ct_opin[istage+1][icol+1];
            // computing treq
            for (int ipp = 0; ipp < ipins.size(); ipp++){
                int icmp_stage = ipins[ipp].istage;
                int icmp_col = ipins[ipp].icol;
                int icmp = ipins[ipp].icmp;
                int icmp_pin = ipins[ipp].ipin;
                auto & cmp = ct[icmp_stage][icmp_col][icmp];
                int num_pins = cmp.ipp1 - cmp.ipp0 + 1;
                if(num_pins == 1){
                    ipins[ipp].treq = opins_sum[cmp.sum].treq;
                }else if(num_pins == 2){
                    if(cmp.cout == -1){ // no carry output
                        ipins[ipp].treq = opins_sum[cmp.sum].treq - dhas[icmp_pin][HA_SUM];
                    }else{
                        ipins[ipp].treq = std::min(opins_sum[cmp.sum].treq - dhas[icmp_pin][HA_SUM], opins_cout[cmp.cout].treq - dhas[icmp_pin][HA_COUT]);
                    }
                }else if(num_pins == 3){
                    if(cmp.cout == -1){ // no carry output
                        ipins[ipp].treq = opins_sum[cmp.sum].treq - dfas[icmp_pin][FA_SUM];
                    }else{
                        ipins[ipp].treq = std::min(opins_sum[cmp.sum].treq - dfas[icmp_pin][FA_SUM], opins_cout[cmp.cout].treq - dfas[icmp_pin][FA_COUT]);
                    }
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

}

void MultiplierGenerator::build_cpa()
{
    // ct_pps[0][icol] is the number of pps in 0th stage column icol. it could be 0 or 1. otherwise 2 because compression tree aligns the output to 2 
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
    for (int i = 0; i < ct_pps[0].size(); i++){
        if(ct_pps[0][i] > 1){
            cpa_col_start = i;
            break;
        }
    }

    std::vector<int> num_cpa_inputs; 
    for (int i = cpa_col_start; i < ct_pps[0].size(); i++){
        if(ct_pps[0][i] > 0){
            num_cpa_inputs.push_back(ct_pps[0][i]);
            cpa_col_end = i;
        }
    }
    
    // the lsbs and the msbs of the adder can only be 1 bit adder. 
    cpa.init(num_cpa_inputs.size());
    cpa.do_sta();
}


