#ifndef CONFIG_HPP
#define CONFIG_HPP

#include <string>
#include <vector>
#include <optional>
#include <nlohmann/json.hpp>

enum CPAType{
    CPA_Ripple, // Ripple Carry Adder
    CPA_KoggeStone, // Kogge-Stone Adder
    CPA_BrentKung, // Brent-Kung Adder
    CPA_Sklansky, // Sklansky Adder
    CPA_SkewAwarePrefix // Skew-aware prefix adder (arrival-sensitive)
};

// Partial Product type
// Unsigned n bit integer [ 0, 2^n-1] 
// Signed n bit integer [-2^(n-1), 2^(n-1)-1] 

// Unsigned n bit x Unsigned m bit => Unsigned n+m bit
// [0, 2^(n+m) -2^n -2^m + 1]
//
// Signed n bit x Signed m bit => n+m bit
// [-2^(n+m-2)+2^(n-1), 2^(n+m-2)] (n>m)
// [-2^(n+m-2)+2^(m-1), 2^(n+m-2)] (m<=n)
//
// Signed n bit x Unsigned m bit >= n + m bit 
// [-2^(n+m-1)+2^(n-1), 2^(n+m-1)-2^m-2^(n-1)+1]
//
// Signed case 
// - extend pp rows to msb (2n-1) according to sign bit
// - Invert and add 1 to last row if multiplier is negative. 
// - output should be signed even when both operands are unsigned. 
//   This means additional 1 bit required, n + m + 1 bit as the total. 

enum PPType{
    Normal,  
    // full n x n pps 

    Normal4, // radix-4 n/2 x (n+1) pps selected from {0x, 1x, 2x, 3x}
    // 3x<=2x+x (1 addition)

    Normal8, // radix-8 n/3 x (n+2) pps selected from {0x, ..., 7x}
    // 5x<=2x+3x, 6x<=3x<<1, 7x<=4x+3x (3 addition)

    Normal16, // radix-16
    // n/4 x (n+4) pps selected from {0x, ..., 15x}
    // 9x=7x+2x, 10x<=5x<<1, 11x<=3x+8x, 12x<=6x<<1, 13x<=12x+x, 14x<=7x<<2, 15x<=14x+x (7 additions)

    Booth4,  // radix-4 Booth
    // n/2 x (n+1) pps selected from {-2, -1, 0, 1, 2}
    // -2x(i+1) + x(i) + x(i-1)

    Booth8,  // radix-8 Booth
    // n/3 x (n+2) pps selected from {-4, ..., 0, ..., 4}
    // 1 addition for 3x
    // -4x(i+2) + 2x(i+1) + x(i) + x(i-1)

    Booth16  // radix-16 Booth 
    // n/16 x (n+4) pps selected from {-8, ..., 0, ...., 8}
    // 3 addition for 3x, 5x, 7x
    // -8x(i+3) + 4x(i+2) + 2x(i+1) + x(i) + x(i-1)
};

// Compression Tree type
enum CTType{
    AdderTree, // 2:1 Adder
    CSATree   // 3:2 FA and 2:2 HA
};

enum CompressorLibrary{
    FA_HA,     // 3:2 and 2:2 only
    FA_HA_C42  // 3:2, 2:2, and 4:2
};

enum CompressorAssignment{
    LegacyFAHA, // legacy FA/HA-count-based ILP
    DirectILP   // direct compressor assignment ILP
};
// Operand configuration
struct OperandConfig {
    int bit_width;
    bool is_signed;
};


struct MultiplierConfig {
    std::string module_name;
    std::string operand;
    std::string ppg_algorithm;
    std::string compressor_structure;
    std::string compressor_library{"fa_ha"};
    std::string compressor_assignment{"legacy_fa_ha"};
    std::string cpa_structure;
    int pipeline_depth;
};

struct MacConfig {
    std::string module_name;
    std::string operand;
    std::string ppg_algorithm;
    std::string compressor_structure;
    std::string compressor_library{"fa_ha"};
    std::string compressor_assignment{"legacy_fa_ha"};
    std::string cpa_structure;
    int pipeline_depth{1};
    std::string accumulation_mode{"pp_row_feedback"};
};

struct MultiplierYosysConfig {
    std::string module_name;
    std::string operand;
    std::string booth_type;
    bool is_signed;
    int bit_width;
};

struct AdderConfig {
    std::string module_name;
    std::string operand;
    std::string cpa_structure;
    int pipeline_depth;
    std::vector<float> input_delays;
};

struct OperandDefinition {
    std::string name;
    int dimensions{1};
    int bit_width{0};
    bool is_signed{false};
    std::string kind{"int"}; // "int" (default) or "fp"
    struct FpFormat {
        int total_width{0};
        int mantissa_width{0};
        int exponent_width() const { return total_width - mantissa_width - 1; }
    };
    std::optional<FpFormat> fp_format;
};

struct McmSynthesisConfig {
    std::string engine{"heuristic"};
    std::string algorithm{"HCub"};
    int max_adders{0};
    bool emit_schedule{false};
};

struct McmOperationConfig {
    std::string module_name;
    std::string operand;
    std::vector<long long> constants;
    McmSynthesisConfig synthesis;
};

struct CmvmSynthesisConfig {
    std::string algorithm{"HCMVM"};
    bool difference_rows{false};
    int max_pair_search{0};
    std::optional<std::string> fallback_algorithm;
};

struct CmvmOperationConfig {
    std::string module_name;
    std::string operand;
    std::vector<std::vector<long long>> matrix;
    CmvmSynthesisConfig synthesis;
};

struct FpOperationConfig {
    std::string type; // fp_mul, fp_add, fp_mac
    std::string module_name;
    std::string operand;
    std::string rounding_mode{"RNE"};
    bool flush_subnormals{false};
    int pipeline_stages{0};
};

struct ActivationOperationConfig {
    std::string module_name;
    std::string operand;
    std::string function; // relu, relu6, leaky_relu, tanh, gelu, pwl
    int alpha_num{1};     // for leaky relu (numerator)
    int alpha_den{10};    // for leaky relu (denominator)
    std::string impl{"default"}; // activation impl hint (e.g., pwl)
    int frac_bits{0}; // for fixed-point tanh
    int segments{0};
    std::vector<double> breakpoints;
    std::vector<double> slopes;
    std::vector<double> intercepts;
    std::vector<double> xs;   // pwl points x
    std::vector<double> ys;   // pwl points f(x)
    bool clamp{true};
    bool symmetric{true};
};

struct CircuitConfig {
    OperandConfig operand;
    std::vector<OperandDefinition> operands;
    std::vector<MultiplierConfig> multipliers;
    std::vector<MacConfig> mac_operations;
    std::vector<AdderConfig> adders;
    std::vector<MultiplierYosysConfig> yosys_multipliers;
    std::vector<McmOperationConfig> mcm_operations;
    std::vector<CmvmOperationConfig> cmvm_operations;
    std::vector<FpOperationConfig> fp_operations;
    std::vector<ActivationOperationConfig> activation_operations;
    std::optional<std::string> onnx_model; // Added ONNX model path
};

// get_ppg_algorithm ppg_algorithm to enum
inline PPType get_ppg_algorithm(const std::string& algo) {
    if (algo == "Normal") return Normal;
    if (algo == "Normal4") return Normal4;
    if (algo == "Normal8") return Normal8;
    if (algo == "Normal16") return Normal16;
    if (algo == "Booth4") return Booth4;
    if (algo == "Booth8") return Booth8;
    if (algo == "Booth16") return Booth16;
    throw std::invalid_argument("Unknown PPG algorithm: " + algo);
}

// get_compressor_type compressor_structure to enum
inline CTType get_compressor_type(const std::string& structure) {
    if (structure == "AdderTree") return AdderTree;
    if (structure == "CSATree") return CSATree;
    throw std::invalid_argument("Unknown compressor structure: " + structure);
}

inline CompressorLibrary get_compressor_library(const std::string& library) {
    if (library == "fa_ha") return FA_HA;
    if (library == "fa_ha_c42") return FA_HA_C42;
    throw std::invalid_argument("Unknown compressor library: " + library);
}

inline CompressorAssignment get_compressor_assignment(const std::string& assignment) {
    if (assignment == "legacy_fa_ha") return LegacyFAHA;
    if (assignment == "direct_ilp") return DirectILP;
    throw std::invalid_argument("Unknown compressor assignment: " + assignment);
}

// get_cpa_type cpa_structure to enum
inline CPAType get_cpa_type(const std::string& structure) {
    if (structure == "Ripple") return CPA_Ripple;
    if (structure == "KoggeStone") return CPA_KoggeStone;
    if (structure == "BrentKung") return CPA_BrentKung;
    if (structure == "Sklansky") return CPA_Sklansky;
    if (structure == "SkewAwarePrefix") return CPA_SkewAwarePrefix;
    throw std::invalid_argument("Unknown CPA structure: " + structure);
}

bool readConfig(const std::string& filename, CircuitConfig& config);

#endif // CONFIG_HPP
