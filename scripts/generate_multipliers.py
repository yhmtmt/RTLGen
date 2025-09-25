import os
import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Generate multipliers for each configuration file in a directory.")
    parser.add_argument("--config_dir", default="multiplier_configs", help="Directory containing configuration files.")
    parser.add_argument("--platform", required=True, help="Name of the platform (e.g., sky130hd, nangate45).")
    parser.add_argument("--optimization_target", default="area", choices=["area", "timing", "power"], help="Optimization target for autotuner.")
    parser.add_argument("--core_utilization_min", type=int, default=20, help="Min value for CORE_UTILIZATION.")
    parser.add_argument("--core_utilization_max", type=int, default=80, help="Max value for CORE_UTILIZATION.")
    parser.add_argument("--place_density_min", type=float, default=0.2, help="Min value for PLACE_DENSITY.")
    parser.add_argument("--place_density_max", type=float, default=0.8, help="Max value for PLACE_DENSITY.")
    parser.add_argument("--clock_period_min", type=float, default=0.0, help="Min value for CLOCK_PERIOD.")
    parser.add_argument("--clock_period_max", type=float, default=20.0, help="Max value for CLOCK_PERIOD.")
    args = parser.parse_args()

    if not os.path.isdir(args.config_dir):
        print(f"Error: Directory not found: {args.config_dir}", file=sys.stderr)
        sys.exit(1)

    for filename in sorted(os.listdir(args.config_dir)):
        if filename.endswith(".json"):
            config_path = os.path.join(args.config_dir, filename)
            print(f"--- Generating design for {config_path} ---")
            
            cmd = [
                "python3", "generate_design.py",
                config_path,
                args.platform,
                "--optimization_target", args.optimization_target,
                "--core_utilization_min", str(args.core_utilization_min),
                "--core_utilization_max", str(args.core_utilization_max),
                "--place_density_min", str(args.place_density_min),
                "--place_density_max", str(args.place_density_max),
                "--clock_period_min", str(args.clock_period_min),
                "--clock_period_max", str(args.clock_period_max),
            ]
            
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error generating design for {config_path}: {e}", file=sys.stderr)
            except FileNotFoundError:
                print(f"Error: 'generate_design.py' not found. Make sure it is in the current directory.", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    main()
