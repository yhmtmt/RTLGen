#!/usr/bin/env python3

import json
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Execute evaluation and extract results.")
    parser.add_argument("config", help="Path to the configuration JSON file.")
    parser.add_argument("platform", help="Name of the platform (e.g., sky130hd, nangate45 and asap7).")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    module_name = config["multiplier"]["module_name"]
    wrapper_name = f"{module_name}_wrapper"

    dest_base = "/orfs/flow/designs"
    platform_dir = os.path.join(args.platform, wrapper_name)
    dest_platform_dir = os.path.join(dest_base, platform_dir)

    # Execute make
    design_config_path = os.path.join(dest_platform_dir, "config.mk")
    # Change current directory to /orfs/flow before running make
    os.chdir("/orfs/flow")
    make_command = ["make", f"DESIGN_CONFIG={design_config_path}"]
    print(f"Executing: {' '.join(make_command)}")
    subprocess.run(make_command, check=True)

    # Extract results
    extract_results(args.platform, wrapper_name)

def extract_results(platform, wrapper_name):
    # Construct paths
    report_path = f"/orfs/flow/reports/{platform}/{wrapper_name}/base/6_finish.rpt"
    def_path = f"/orfs/flow/results/{platform}/{wrapper_name}/base/6_final.def"

    print("\n--- Extraction Results ---")

    # --- Extract critical path delay and power ---
    try:
        with open(report_path, 'r') as f:
            lines = f.readlines()

        # Critical path delay
        try:
            delay_index = -1
            for i, line in enumerate(lines):
                if "finish critical path delay" in line:
                    delay_index = i
                    break
            if delay_index != -1 and delay_index + 2 < len(lines):
                critical_path_delay = lines[delay_index + 2].strip()
                print(f"Critical Path Delay: {critical_path_delay}")
            else:
                print("Could not find critical path delay.")
        except Exception as e:
            print(f"Error extracting critical path delay: {e}")

        # Power consumption
        try:
            power_index = -1
            for i, line in enumerate(lines):
                if "finish report_power" in line:
                    power_index = i
                    break
            if power_index != -1 and power_index + 11 < len(lines):
                power_line = lines[power_index + 11].strip()
                power_values = power_line.split()
                if len(power_values) >= 5:
                    total_power = power_values[4]
                    print(f"Total Power Consumption: {total_power}")
                else:
                    print(f"Could not parse power consumption line: {power_line}")
            else:
                print("Could not find power consumption information.")
        except Exception as e:
            print(f"Error extracting power consumption: {e}")

    except FileNotFoundError:
        print(f"Error: Report file not found at {report_path}")
    except Exception as e:
        print(f"An error occurred while processing {report_path}: {e}")


    # --- Extract die size ---
    try:
        with open(def_path, 'r') as f:
            lines = f.readlines()

        die_area_line = None
        for line in lines:
            if line.strip().startswith("DIEAREA"):
                die_area_line = line.strip()
                break

        if die_area_line:
            try:
                parts = die_area_line.split()
                # Example: DIEAREA ( 0 0 ) ( 40000 40000 ) ;
                width = int(parts[6])
                height = int(parts[7])
                area = width * height
                print(f"Die Size (WxH): {width} x {height}")
                print(f"Die Area: {area}")
            except (IndexError, ValueError) as e:
                print(f"Could not parse DIEAREA line: {die_area_line}, error: {e}")
        else:
            print("Could not find DIEAREA information.")

    except FileNotFoundError:
        print(f"Error: DEF file not found at {def_path}")
    except Exception as e:
        print(f"An error occurred while processing {def_path}: {e}")


if __name__ == "__main__":
    main()
