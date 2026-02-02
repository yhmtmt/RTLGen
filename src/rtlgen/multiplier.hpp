#ifndef MULTIPLIER_HPP
#define MULTIPLIER_HPP

#include <regex> // Include for std::regex
#include <numeric> // Include for std::accumulate
#include <algorithm> // For std::all_of, std::any_of
#include <cfloat>
#include "config.hpp"
#include "boolexp.hpp"
#include "adder.hpp"

// Forward declaration
class RTLGen;

struct BoothEncoder
{
    // s2(i) = !y(2i+1) y(2i) y(2i-1) + y(2i+1) !y(2i) !y(2i-1)
    // s1(i) = y(2i)^y(2i-1)
    // neg(i) = y(2i+1)
    // c(i) = y(2i+1)(!y(2i)+!y(2i-1))
    BoolExp * s2, *s1, *neg, *c;
    BoothEncoder() : s2(nullptr), s1(nullptr), neg(nullptr), c(nullptr) {}
};

struct Normal4Encoder
{
    BoolExp * s1, *s2, *s3;
    Normal4Encoder(): s1(nullptr), s2(nullptr), s3(nullptr) {}
};

// sum: (a XOR b) XOR cin
// cout: (a and b) or (b and cin) or (a and cin)
//      equivalent to (a and b) or (cin and (a XOR b))
enum FullAdderInput { FA_A, FA_B, FA_CIN };
enum FullAdderOutput { FA_SUM, FA_COUT };
enum HalfAdderInput { HA_A, HA_B };
enum HalfAdderOutput { HA_SUM, HA_COUT };

// Bit types for PPBit
enum Bit {
    BIT_NONE,       // Unused or uninitialized bit
    BIT_EXPRESSION, // Bit represented by a BoolExp
    BIT_ZERO,       // Constant zero bit
    BIT_ONE,        // Constant one bit
    BIT_SIGN        // Sign bit
};

// PPBit structure representing a bit in the partial product
// It can be a constant (zero, one, sign) or an expression (BoolExp)
struct PPBit {
    Bit bit_type;          // Type of the bit (BIT_NONE, BIT_EXPRESSION, etc.)
    BoolExp* expression;   // Pointer to a BoolExp object (used when bit_type is BIT_EXPRESSION)

    PPBit() : bit_type(BIT_NONE), expression(nullptr) {}

    ~PPBit() {
    }

    // Set the bit as an expression with a BoolExp
    void setExpression(BoolExp* exp) {
        bit_type = BIT_EXPRESSION;
        expression = exp;
    }

    // Set the bit as a constant type (BIT_ZERO, BIT_ONE, BIT_SIGN, etc.)
    void setConstant(Bit type) {
        bit_type = type;
        if (expression) {
            delete expression;
            expression = nullptr;
        }
    }

    // Check if the bit is an expression
    bool isExpression() const {
        return bit_type == BIT_EXPRESSION;
    }
};

// CTNode represents 3:2, 2:2, 1:1 compression. 
// for 3:2 and 2:2 compression, the carry output is passed to j+1 th column  
enum CompressorType{
    CT_NONE, // No compression
    CT_3_2,  // 3:2 compressor
    CT_2_2,  // 2:2 compressor
    CT_4_2,  // 4:2 compressor (sum + 2 carries)
    CT_1_1   // 1:1 compressor
};

struct CTNode{
    int istage, icol; // stage and column index
    int ipp0, ipp1;   // input pp indices, ipp0 is the first input, ipp1 is the last input
    int sum;          // output pp index sum to (istage+1,icol)
    std::vector<int> couts; // output pp indices to (istage+1,icol+1)
    CompressorType type;

    CTNode(): type(CT_NONE), ipp0(-1), icol(-1), ipp1(-1), sum(-1){}
    CTNode(int _ipp, int _istage, int _icol): type(CT_1_1), ipp0(_ipp), ipp1(_ipp), istage(_istage), icol(_icol), sum(-1){}
    CTNode(int _ipp0, int _ipp1, int _istage, int _icol): ipp0(_ipp0), ipp1(_ipp1), istage(_istage), icol(_icol), sum(-1){
        if(ipp1 - ipp0 == 1){
            type = CT_2_2;
        }else if(ipp1 - ipp0 == 2){
            type = CT_3_2;
        }else if(ipp1 - ipp0 == 0){
            type = CT_1_1;
        }else{
            type = CT_NONE;
        }
    }

    bool is_absent(){
        return ipp0 == -1 && icol == -1;
    }
};

// CTNodePin represents the pin of the CTNode. 
// Each stage and column has partial product bits. 
// Outputs are arranged in the order carry bits, sum bits, and pass through bits.
// Inputs are arrange in the order full adder inputs, half adder inputs, and pass through bits.
struct CTNodePin{
    int istage, icol, icmp, ipin; // i: stage, j: column, k: compressor index, l: pin index
    double tarr,treq; // arrival time
    double tslack; // slack time
    CTNodePin(): istage(-1), icol(-1), icmp(-1), ipin(-1), tarr(-1.0), treq(-1.0), tslack(-1.0){} // default constructor
    CTNodePin(const double _tarr):tarr(_tarr){}
    CTNodePin(const int _istage, const int _icol, const int _icmp, const int _ipin, const double _tarr = -1.0)
        : istage(_istage), icol(_icol), icmp(_icmp), ipin(_ipin), tarr(_tarr) {}

    void init_timing_info(){
        tarr = 0.0;
        treq =  FLT_MAX;
        tslack = -1.0;
    }

    void set_tarr(const double _tarr){
        tarr = std::max(tarr, _tarr);
    }
};

struct Operand {
    bool is_signed, is_const;
    int width;
    std::vector<bool> bits; // Boolean vector representing the operand

    Operand() : is_signed(false), is_const(false), width(0) {}

    // Function to parse a number string into the Operand
    bool parse(const std::string& numberStr) {
        std::regex binaryRegex("^\\d+'b[01]+$");
        std::regex hexRegex("^\\d+'h[0-9a-fA-F]+$");
        std::regex octRegex("^\\d+'o[0-7]+$");
        std::regex decRegex("^\\d+'d\\d+$");

        std::smatch match;
        std::string valueStr;

        if (std::regex_match(numberStr, match, binaryRegex)) {
            width = std::stoi(numberStr.substr(0, numberStr.find('\'')));
            valueStr = numberStr.substr(numberStr.find('b') + 1);
            is_signed = false;
        } else if (std::regex_match(numberStr, match, hexRegex)) {
            width = std::stoi(numberStr.substr(0, numberStr.find('\'')));
            valueStr = numberStr.substr(numberStr.find('h') + 1);
            is_signed = false;
        } else if (std::regex_match(numberStr, match, octRegex)) {
            width = std::stoi(numberStr.substr(0, numberStr.find('\'')));
            valueStr = numberStr.substr(numberStr.find('o') + 1);
            is_signed = false;
        } else if (std::regex_match(numberStr, match, decRegex)) {
            width = std::stoi(numberStr.substr(0, numberStr.find('\'')));
            valueStr = numberStr.substr(numberStr.find('d') + 1);
            is_signed = false;
        } else {
            std::cerr << "Error: Invalid number format: " << numberStr << std::endl;
            return false;
        }

        bits.assign(width, false);

        // Convert the value string to bits
        if (numberStr.find('b') != std::string::npos) {
            // Binary
            for (size_t i = 0; i < valueStr.size(); ++i) {
                bits[width - valueStr.size() + i] = (valueStr[i] == '1');
            }
        } else {
            unsigned long long value = 0;
            if (numberStr.find('h') != std::string::npos) {
                // Hexadecimal
                value = std::stoull(valueStr, nullptr, 16);
            } else if (numberStr.find('o') != std::string::npos) {
                // Octal
                value = std::stoull(valueStr, nullptr, 8);
            } else if (numberStr.find('d') != std::string::npos) {
                // Decimal
                value = std::stoull(valueStr, nullptr, 10);
            }
            for (int i = 0; i < width; ++i) {
                bits[width - 1 - i] = (value >> i) & 1;
            }
        }

        return true;
    }

    // Compute multiplication result as an Operand
    Operand multiply(const Operand& other) const {
        Operand result;
        result.is_signed = is_signed || other.is_signed;
        result.width = width + other.width; // Result width is the sum of operand widths
        result.bits.assign(result.width, false);

        // Perform multiplication
        for (int i = 0; i < other.width; ++i) {
            if (other.bits[i]) {
                for (int j = 0; j < width; ++j) {
                    result.bits[i + j] = static_cast<bool>(result.bits[i + j]) ^ static_cast<bool>(bits[j]); // XOR for addition in binary
                }
            }
        }

        // Handle signed multiplication
        if (result.is_signed) {
            bool sign_bit = bits[width - 1] ^ other.bits[other.width - 1];
            for (int i = width + other.width - 1; i >= 0; --i) {
                result.bits[i] = sign_bit;
            }
        }

        return result;
    }

    // Convert Operand to string in the specified format
    std::string toString(const std::string& format = "dec") const {
        unsigned long long value = 0;

        // Convert bits to an integer value
        for (int i = 0; i < width; ++i) {
            if (bits[i]) {
                value |= (1ULL << i);
            }
        }

        // Handle signed values
        if (is_signed && bits[width - 1]) {
            value = (~value + 1) & ((1ULL << width) - 1); // Two's complement
            return "-" + toStringUnsigned(value, format);
        }

        return toStringUnsigned(value, format);
    }

private:
    // Helper function to convert unsigned value to string in the specified format
    std::string toStringUnsigned(unsigned long long value, const std::string& format) const {
        std::ostringstream oss;

        if (format == "bin") {
            oss << "0b" << std::bitset<64>(value).to_string().substr(64 - width);
        } else if (format == "hex") {
            oss << "0x" << std::hex << std::uppercase << value;
        } else if (format == "oct") {
            oss << "0o" << std::oct << value;
        } else { // Default to decimal
            oss << value;
        }

        return oss.str();
    }
};



class MultiplierGenerator
{
private:
    int cols_pps, rows_pps;

    BoolExpManager exp_manager;                      // manager for BoolExp objects

    // partial product generation
    std::vector<std::vector<PPBit>> pps;             // partial products given. 
    
    ////////////////////////////   generate partial products based on the type of ppType
    void gen_pp(Operand multiplicand, Operand multiplier, PPType ppType);
    void gen_normal_pp(Operand multiplicand, Operand multiplier);
    void gen_booth4_pp(Operand multiplicand, Operand multiplier);
    std::vector<BoothEncoder> bes;                   // booth encoder signals corresponding to each row. decoders are attached to the pps.
    std::vector<std::vector<BoolExp*>> pxs;           // booth decoder signals corresponding to each row. decoders are attached to the pps.

    void gen_normal4_pp(Operand multiplicand, Operand multiplier);
    std::vector<Normal4Encoder> n4es;                 // normal radix-4 encoder signals corresponding to each row. decoders are attached to the pps.

    ////////////////////////////  compressor tree generation
    float dfas[3][2]; // delay table for full adder
    float dhas[2][2]; // delay table for half adder
    int num_stages;                                                    // number of adder stages in ct
    std::vector<std::vector<int>> ct_pps;                              // pps in each column of the stage.

    // ct_ipin[istage] and ct_opin[istage+1] are the input and output pins of compressor ct[istage].
    std::vector<std::vector<std::vector<CTNode>>> ct;                  // compressor tree for each stage;
    std::vector<std::vector<std::vector<CTNodePin>>> ct_ipin, ct_opin; // input and output pins of the csa tree, stage, column, pin index
    // pin_assign[istage][icol] is interconnection assignment between ct_ipin[istage][icol] and ct_opin[istage][icol]
    // ct_opin[istage][icol][pin_assign[istage][icol][ipp]] is connected to ct_ipin[istage][icol][ipp]
    std::vector<std::vector<std::vector<int>>> pin_assign;             // pin assignment for each stage, column, pin index
    // builds compression tree. determines assignments of adders and interconnections
    void build_ct(bool enable_c42, bool use_direct_ilp);

    // count initial number of partial products per column and estimate max stages
    void count_pps(int & num_max_stages);
    // count minimum number of FAs and HAs required for each column (legacy)
    void count_fas_and_has(std::vector<int> &num_fas, std::vector<int> &num_has, int & num_max_stages);

    // optimizing compressor assignment using ILP solver
    void opt_ct_assignment(
                            std::vector<std::vector<int>> &ct_3_2,
                            std::vector<std::vector<int>> &ct_2_2,
                            std::vector<std::vector<int>> &ct_4_2,
                            int num_max_stages,
                            bool enable_c42);

    // legacy FA/HA assignment ILP
    void opt_fas_and_has_assignment(
                            std::vector<int> &num_fas, std::vector<int> &num_has,
                            std::vector<std::vector<int>> &fas, std::vector<std::vector<int>> &has,
                            int num_max_stages);
    // according to optimization by opt_fas_and_has_assignment, allocate compressors of ct and pin structures. 
    void alloc_and_load_ct(
                            std::vector<std::vector<int>> &ct_3_2,
                            std::vector<std::vector<int>> &ct_2_2,
                            std::vector<std::vector<int>> &ct_4_2);
    void alloc_and_load_ct_legacy(
                            std::vector<std::vector<int>> &ct_fas,
                            std::vector<std::vector<int>> &ct_has);
    void opt_ct_wire_assignment(); // optimize compresssors interconnections
    double do_ct_sta();            // returns the maximum delay of the csa tree (used for optimization)
    
    // final carry propagation adder
    CarryPropagatingAdder cpa; // carry propagating adder
    int cpa_col_start, cpa_col_end;
    void build_cpa(CPAType cptype); 

    // dump hdl files of the multiplier. called from build function.
    void dump_hdl(Operand multiplicand, Operand multiplier, const std::string& module_name);
    void dump_hdl_ct(std::ofstream & verilog_file);
    void dump_hdl_fa(std::ofstream & verilog_file, const std::string& module_name);
    void dump_hdl_ha(std::ofstream & verilog_file, const std::string& module_name);
    void dump_hdl_c42(std::ofstream & verilog_file, const std::string& module_name);


public:
    MultiplierGenerator(){
        dfas[FA_A][FA_SUM] = 1.0;
        dfas[FA_A][FA_COUT] = 0.5;
        dfas[FA_B][FA_SUM] = 1.0;
        dfas[FA_B][FA_COUT] = 0.5;
        dfas[FA_CIN][FA_SUM] = 0.5;
        dfas[FA_CIN][FA_COUT] = 0.5;
        dhas[HA_A][HA_SUM] = 0.5;
        dhas[HA_A][HA_COUT] = 0.5;
        dhas[HA_B][HA_SUM] = 0.5;
        dhas[HA_B][HA_COUT] = 0.5;
    }

    ~MultiplierGenerator(){
    }
    
    // dump hdl testbench for the multiplier. called from build function.
    void dump_hdl_tb(Operand multiplicand, Operand multiplier, const std::string& module_name);

    void build(Operand multiplicand, Operand multiplier,
                          CTType ctype, PPType ppType, CPAType cptype, const std::string& module_name,
                          bool enable_c42 = false, bool use_direct_ilp = false);
    void build_yosys(const MultiplierYosysConfig& config, const std::string& module_name);
};

#endif
