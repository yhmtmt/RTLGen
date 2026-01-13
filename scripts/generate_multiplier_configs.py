import json
import os
import argparse
import shutil

def generate_configs(max_bit_width):
    output_dir = "multiplier_configs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    algorithms = ["Booth4", "Normal"]
    cpa_structures = ["KoggeStone", "BrentKung", "Sklansky", "Ripple"]
    
    bit_width = 4
    while bit_width <= max_bit_width:
        for signed in [True, False]:
            for algorithm in algorithms:
                for cpa_structure in cpa_structures:
                    signed_str = "signed" if signed else "unsigned"
                    signed_suffix = "s" if signed else "u"
                    
                    config = {
                        "operand": {
                            "bit_width": bit_width,
                            "signed": signed
                        },
                        "multiplier": {
                            "module_name": f"{algorithm.lower()}_multiplier_{cpa_structure.lower()}_{bit_width}{signed_suffix}",
                            "ppg_algorithm": algorithm,
                            "compressor_structure": "AdderTree",
                            "compressor_library": "fa_ha",
                            "compressor_assignment": "legacy_fa_ha",
                            "cpa_structure": cpa_structure,
                            "pipeline_depth": 1
                        }
                    }
                    
                    filename = f"{output_dir}/config_{algorithm.lower()}_{cpa_structure.lower()}_{signed_str}_{bit_width}bit.json"
                    
                    with open(filename, 'w') as f:
                        json.dump(config, f, indent=4)
        
        bit_width *= 2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate multiplier configuration files for bit widths that are powers of two.")
    parser.add_argument("--max_bit_width", type=int, default=64, help="Maximum bit width (e.g., 64).")
    args = parser.parse_args()
    
    generate_configs(args.max_bit_width)
    print(f"Generated configuration files in the 'multiplier_configs' directory for bit widths up to {args.max_bit_width}.")
