#!/usr/bin/env python3

import json
import os
import subprocess
import argparse
import shutil


def main():
    parser = argparse.ArgumentParser(description="Generate multiplier Verilog and OpenROAD files.")
    parser.add_argument("config", help="Path to the configuration JSON file.")
    parser.add_argument("platform", help="Name of the platform (e.g., sky130hd, nangate45).")
    parser.add_argument("--optimization_target", default="area", choices=["area", "timing", "power"], help="Optimization target for autotuner.")
    parser.add_argument("--core_utilization_min", type=int, default=20, help="Min value for CORE_UTILIZATION.")
    parser.add_argument("--core_utilization_max", type=int, default=70, help="Max value for CORE_UTILIZATION.")
    parser.add_argument("--place_density_min", type=float, default=0.2, help="Min value for PLACE_DENSITY.")
    parser.add_argument("--place_density_max", type=float, default=0.7, help="Max value for PLACE_DENSITY.")
    parser.add_argument("--clock_period_min", type=float, default=5.0, help="Min value for CLOCK_PERIOD.")
    parser.add_argument("--clock_period_max", type=float, default=20.0, help="Max value for CLOCK_PERIOD.")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    module_name = config["multiplier"]["module_name"]
    wrapper_name = f"{module_name}_wrapper"

    # Create directories
    src_dir = os.path.join("src", wrapper_name)
    os.makedirs(src_dir, exist_ok=True)

    platform_dir = os.path.join(args.platform, wrapper_name)
    os.makedirs(platform_dir, exist_ok=True)

    # Generate Verilog
    ld_library_path = os.path.expanduser("~/work/or-tools_x86_64_Ubuntu-22.04_cpp_v9.10.4067/lib")
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{ld_library_path}:{env.get('LD_LIBRARY_PATH', '')}"

    subprocess.run(["mult-gen", args.config], env=env, check=True)
    os.rename(f"{module_name}.v", os.path.join(src_dir, f"{module_name}.v"))

    # Generate Wrapper
    generate_wrapper(config, src_dir)

    # Generate OpenROAD files
    generate_config_mk(config, platform_dir, args.platform)
    generate_constraint_sdc(config, platform_dir)
    generate_autotuner_json(platform_dir, args)

    # Move MG_CPA.v
    os.rename("MG_CPA.v", os.path.join(src_dir, "MG_CPA.v"))

    # Copy platform-specific files
    if args.platform == "nangate45":
        shutil.copy("nangate45/grid_strategy-M1-M4-M7.tcl", platform_dir)
        shutil.copy("nangate45/rules-base.json", platform_dir)
    elif args.platform == "sky130hd":
        shutil.copy("sky130hd/rules-base.json", platform_dir)

    print(f"Generated files in {src_dir} and {platform_dir}")

    # Move to /orfs/flow
    dest_base = "/orfs/flow/designs"
    dest_platform_dir = os.path.join(dest_base, platform_dir)
    dest_src_dir = os.path.join(dest_base, src_dir)

    # Create parent directories for destination
    os.makedirs(os.path.dirname(dest_platform_dir), exist_ok=True)
    os.makedirs(os.path.dirname(dest_src_dir), exist_ok=True)

    # Remove destination if it exists to avoid nesting
    if os.path.isdir(dest_platform_dir):
        shutil.rmtree(dest_platform_dir)
    shutil.move(platform_dir, dest_platform_dir)

    if os.path.isdir(dest_src_dir):
        shutil.rmtree(dest_src_dir)
    shutil.move(src_dir, dest_src_dir)

    print(f"Moved generated files to {dest_platform_dir} and {dest_src_dir}")

def generate_wrapper(config, src_dir):
    module_name = config["multiplier"]["module_name"]
    bit_width = config["operand"]["bit_width"]
    wrapper_name = f"{module_name}_wrapper"
    wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input [{bit_width-1}:0] multiplicand,
  input [{bit_width-1}:0] multiplier,
  output [{2*bit_width-1}:0] product
);

  reg [{bit_width-1}:0] multiplicand_reg;
  reg [{bit_width-1}:0] multiplier_reg;
  wire [{2*bit_width-1}:0] product_wire;
  reg [{2*bit_width-1}:0] product_reg;

  {module_name} dut (
    .multiplicand(multiplicand_reg),
    .multiplier(multiplier_reg),
    .product(product_wire)
  );

  always @(posedge clk) begin
    multiplicand_reg <= multiplicand;
    multiplier_reg <= multiplier;
    product_reg <= product_wire;
  end

  assign product = product_reg;

endmodule
"""
    with open(os.path.join(src_dir, f"{wrapper_name}.v"), "w") as f:
        f.write(wrapper_content)

def generate_config_mk(config, platform_dir, platform):
    module_name = config["multiplier"]["module_name"]
    wrapper_name = f"{module_name}_wrapper"
    content = f"""
export PLATFORM = {platform}
export DESIGN_NAME = {wrapper_name}
export VERILOG_FILES = $(DESIGN_HOME)/src/{wrapper_name}/{module_name}.v $(DESIGN_HOME)/src/{wrapper_name}/{wrapper_name}.v $(DESIGN_HOME)/src/{wrapper_name}/MG_CPA.v
export SDC_FILE = $(DESIGN_HOME)/{platform}/{wrapper_name}/constraint.sdc
export TOP_MODULE = {wrapper_name}
export CORE_UTILIZATION = 30
"""
    if platform == "nangate45":
        content += "export PDN_TCL ?= $(DESIGN_HOME)/nangate45/$(DESIGN_NAME)/grid_strategy-M1-M4-M7.tcl\n"
    with open(os.path.join(platform_dir, "config.mk"), "w") as f:
        f.write(content)

def generate_constraint_sdc(config, platform_dir):
    bit_width = config["operand"]["bit_width"]
    content = f"""
set clock_port "clk"
set clock_period 10.0
set input_delay 2.0
set output_delay 2.0

create_clock [get_ports $clock_port] -period $clock_period

set_input_delay $input_delay -clock $clock_port [all_inputs]
set_output_delay $output_delay -clock $clock_port [all_outputs]

set_load -pin_load 0.05 [all_outputs]
"""
    with open(os.path.join(platform_dir, "constraint.sdc"), "w") as f:
        f.write(content)

def generate_autotuner_json(platform_dir, args):
    with open("autotuner_base.json", "r") as f:
        content = json.load(f)

    content["_SDC_CLK_PERIOD"]["minmax"] = [args.clock_period_min, args.clock_period_max]
    content["CORE_UTILIZATION"]["minmax"] = [args.core_utilization_min, args.core_utilization_max]
    content["_FR_FILE_PATH"] = content["_FR_FILE_PATH"].replace("sky130hd", args.platform)

    with open(os.path.join(platform_dir, "autotuner.json"), "w") as f:
        json.dump(content, f, indent=4)

if __name__ == "__main__":
    main()