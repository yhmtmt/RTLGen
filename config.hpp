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
    CPA_Sklansky // Sklansky Adder
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


// Operand configuration
struct OperandConfig {
    int bit_width;
    bool is_signed;
};


struct MultiplierConfig {
    std::string module_name; // Added module name
    std::string ppg_algorithm;
    std::string compressor_structure;
    std::string cpa_structure;
    int pipeline_depth;
};

struct MultiplierYosysConfig {
    std::string module_name; // Added module name
    std::string booth_type;
    bool is_signed;
    int bit_width;
};

struct AdderConfig {
    std::string module_name;
    std::string cpa_structure;
    int pipeline_depth;
};

struct CircuitConfig {
    OperandConfig operand;
    std::optional<MultiplierConfig> multiplier;
    std::optional<AdderConfig> adder;
    std::optional<MultiplierYosysConfig> multiplier_yosys;
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

// get_cpa_type cpa_structure to enum
inline CPAType get_cpa_type(const std::string& structure) {
    if (structure == "Ripple") return CPA_Ripple;
    if (structure == "KoggeStone") return CPA_KoggeStone;
    if (structure == "BrentKung") return CPA_BrentKung;
    if (structure == "Sklansky") return CPA_Sklansky;
    throw std::invalid_argument("Unknown CPA structure: " + structure);
}

bool readConfig(const std::string& filename, CircuitConfig& config);

#endif // CONFIG_HPP