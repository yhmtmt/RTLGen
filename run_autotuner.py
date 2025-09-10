import subprocess
import sys
import argparse
import json
import re

def generate_coeff_combinations(step):
    if not (1/step).is_integer():
        raise ValueError("1/step must be an integer.")
    n = int(1 / step)
    combinations = []
    for i in range(n + 1):
        for j in range(n - i + 1):
            k = n - i - j
            combinations.append((i * step, j * step, k * step))
    return combinations

def main():
    parser = argparse.ArgumentParser(description="Wrapper for openroad_autotuner that automatically generates the config path, updates it, and runs an evaluation sweep.")
    parser.add_argument("--design", required=True, help="Design name (e.g., booth4_multiplier4s_wrapper).")
    parser.add_argument("--platform", required=True, help="Platform name (e.g., nangate45).")
    parser.add_argument("--step", type=float, default=0.25, help="Step value for PPA coefficient combinations.")
    
    args, remaining_args = parser.parse_known_args()

    config_path = f"/orfs/flow/designs/{args.platform}/{args.design}/autotuner.json"

    # --- First Run ---
    cmd1 = [
        "openroad_autotuner",
        "--design", args.design,
        "--platform", args.platform,
        "--config", config_path,
    ] + remaining_args

    print("--- Running command (initial tune): ---")
    print(" ".join(cmd1))
    print("-------------------------------------")

    try:
        result1 = subprocess.run(cmd1, check=True, capture_output=True, text=True)
        
        best_results_path_1 = None
        for line in result1.stdout.splitlines():
            if "Best results written to" in line:
                match = re.search(r"Best results written to (.*)", line)
                if match:
                    best_results_path_1 = match.group(1).strip()
                    break
        
        if best_results_path_1:
            print(f"--- Found best results file: {best_results_path_1} ---")
            
            with open(best_results_path_1, 'r') as f:
                best_results_1 = json.load(f)
            
            effective_clk_period_1 = best_results_1.get("effective_clk_period")
            
            if effective_clk_period_1 is not None:
                print(f"--- Found effective_clk_period: {effective_clk_period_1} ---")
                
                new_min = 0.5 * effective_clk_period_1
                new_max = 2.0 * effective_clk_period_1
                
                print(f"--- New _SDC_CLK_PERIOD range: [{new_min}, {new_max}] ---")
                
                with open(config_path, 'r') as f:
                    autotuner_config = json.load(f)
                
                if "_SDC_CLK_PERIOD" in autotuner_config:
                    autotuner_config["_SDC_CLK_PERIOD"]["minmax"] = [new_min, new_max]
                else:
                    autotuner_config["_SDC_CLK_PERIOD"] = {"minmax": [new_min, new_max]}

                with open(config_path, 'w') as f:
                    json.dump(autotuner_config, f, indent=4)
                
                print(f"--- Updated {config_path} with new _SDC_CLK_PERIOD values. ---")

                # --- Evaluation Sweep ---
                coeff_combinations = generate_coeff_combinations(args.step)
                print(f"--- Generated {len(coeff_combinations)} coefficient combinations with step {args.step} ---")
                
                all_evaluation_metrics = []

                for i, (coeff_p, coeff_a, coeff_po) in enumerate(coeff_combinations):
                    print(f"--- Running evaluation {i+1}/{len(coeff_combinations)} with coeffs: P={coeff_p}, A={coeff_a}, Po={coeff_po} ---")
                    
                    cmd2 = [
                        "openroad_autotuner",
                        "--design", args.design,
                        "--platform", args.platform,
                        "--config", config_path,
                    ] + remaining_args + [
                        "--eval", "ppa-improv",
                        "--reference", best_results_path_1,
                        "--coeff_perform", str(coeff_p),
                        "--coeff_area", str(coeff_a),
                        "--coeff_power", str(coeff_po),
                    ]

                    result2 = subprocess.run(cmd2, check=True, capture_output=True, text=True)

                    best_results_path_2 = None
                    for line in result2.stdout.splitlines():
                        if "Best results written to" in line:
                            match = re.search(r"Best results written to (.*)", line)
                            if match:
                                best_results_path_2 = match.group(1).strip()
                                break
                    
                    if best_results_path_2:
                        with open(best_results_path_2, 'r') as f:
                            best_results_2 = json.load(f)

                        metric = best_results_2.get("metric")
                        effective_clk_period_2 = best_results_2.get("effective_clk_period")
                        die_area = best_results_2.get("die_area")
                        total_power = best_results_2.get("total_power")

                        output_list = [coeff_p, coeff_a, coeff_po, metric, effective_clk_period_2, die_area, total_power]
                        all_evaluation_metrics.append(output_list)
                    else:
                        print(f"--- Could not find best results file for coeffs: P={coeff_p}, A={coeff_a}, Po={coeff_po} ---", file=sys.stderr)

                print("--- All Evaluation Metrics ---")
                for metrics in all_evaluation_metrics:
                    print(metrics)

            else:
                print("--- 'effective_clk_period' not found in best results file. ---", file=sys.stderr)

        else:
            print("--- Could not find the path to the best results file in the output. ---", file=sys.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error running openroad_autotuner: {e}", file=sys.stderr)
        if e.stdout:
            print("--- stdout ---", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("--- stderr ---", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: 'openroad_autotuner' not found. Make sure it is in your PATH.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
