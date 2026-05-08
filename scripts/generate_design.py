#!/usr/bin/env python3

import json
import os
import subprocess
import argparse
import shutil
from pathlib import Path
current_file_path = os.path.dirname(os.path.abspath(__file__))
repo_root = Path(current_file_path).resolve().parent


def _default_operand(config):
    operands = config.get("operands", [])
    if operands:
        return operands[0]
    if "operand" in config:
        return {
            "name": "operand",
            "bit_width": config["operand"]["bit_width"],
            "signed": config["operand"]["signed"],
            "kind": "int",
        }
    raise ValueError("No operand definition found in config")


def _resolve_operand(config, operand_name=""):
    if operand_name:
        for operand in config.get("operands", []):
            if operand.get("name") == operand_name:
                return operand
        raise ValueError(f"Unknown operand reference: {operand_name}")
    return _default_operand(config)


def _operand_signal_width(operand):
    if operand.get("kind", "int") == "fp":
        fp_format = operand.get("fp_format", {})
        total_width = int(fp_format.get("total_width", operand.get("bit_width", 0)))
        return total_width + 2
    return int(operand["bit_width"])


def _ceil_log2_at_least_one(value):
    value = int(value)
    if value <= 1:
        return 1
    bits = 0
    span = 1
    while span < value:
        span <<= 1
        bits += 1
    return max(bits, 1)


def identify_design(config):
    if "multiplier" in config:
        operand = _resolve_operand(config, config["multiplier"].get("operand", ""))
        module_name = config["multiplier"]["module_name"]
        bit_width = int(_operand_signal_width(operand))
        return {
            "kind": "multiplier",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "input_width": bit_width,
            "output_width": bit_width * 2,
            "include_mg_cpa": True,
        }
    if "multiplier_yosys" in config:
        operand = _resolve_operand(config, config["multiplier_yosys"].get("operand", ""))
        module_name = config["multiplier_yosys"]["module_name"]
        bit_width = int(_operand_signal_width(operand))
        return {
            "kind": "multiplier_yosys",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "input_width": bit_width,
            "output_width": bit_width * 2,
            "include_mg_cpa": False,
        }
    if "adder" in config:
        operand = _resolve_operand(config, config["adder"].get("operand", ""))
        module_name = config["adder"]["module_name"]
        bit_width = int(_operand_signal_width(operand))
        return {
            "kind": "adder",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "input_width": bit_width,
            "output_width": bit_width,
            "include_mg_cpa": False,
        }

    operations = config.get("operations", [])
    if len(operations) != 1:
        raise ValueError("generate_design.py currently supports configs with exactly one operation entry")
    entry = operations[0]
    module_name = entry["module_name"]
    operand = _resolve_operand(config, entry.get("operand", ""))
    bit_width = int(_operand_signal_width(operand))
    op_type = entry["type"]
    if op_type == "bf16_recip_norm":
        fp_format = operand.get("fp_format", {})
        bit_width = int(fp_format.get("total_width", operand.get("bit_width", 0)))
    if op_type == "activation":
        return {
            "kind": "scalar_unary",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "input_width": bit_width,
            "output_width": bit_width,
            "include_mg_cpa": False,
        }
    if op_type in {"softmax_rowwise", "bf16_recip_norm"}:
        options = entry.get("options", {})
        row_elems = int(options.get("row_elems", 1))
        if row_elems <= 0:
            raise ValueError(f"{op_type} row_elems must be positive")
        row_width = bit_width * row_elems
        return {
            "kind": "vector_unary",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "input_width": row_width,
            "output_width": row_width,
            "include_mg_cpa": False,
        }
    if op_type == "score_tie_rank":
        options = entry.get("options", {})
        row_elems = int(options.get("row_elems", 1))
        score_bits = int(options.get("score_bits", bit_width) or bit_width)
        logit_bits = int(options.get("logit_bits", 16))
        if row_elems <= 0:
            raise ValueError("score_tie_rank row_elems must be positive")
        if score_bits <= 0:
            raise ValueError("score_tie_rank score_bits must be positive")
        if logit_bits <= 0:
            raise ValueError("score_tie_rank logit_bits must be positive")
        return {
            "kind": "score_tie_rank",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "score_width": score_bits * row_elems,
            "logit_width": logit_bits * row_elems,
            "index_width": _ceil_log2_at_least_one(row_elems),
            "score_bits": score_bits,
            "logit_bits": logit_bits,
            "logit_signed": bool(options.get("logit_signed", True)),
            "include_mg_cpa": False,
        }
    if op_type == "logit_rank":
        options = entry.get("options", {})
        row_elems = int(options.get("row_elems", 1))
        logit_bits = int(options.get("logit_bits", bit_width) or bit_width)
        top_k = int(options.get("top_k", 1))
        if row_elems <= 0:
            raise ValueError("logit_rank row_elems must be positive")
        if logit_bits <= 0:
            raise ValueError("logit_rank logit_bits must be positive")
        if top_k <= 0 or top_k > row_elems:
            raise ValueError("logit_rank top_k must be in [1, row_elems]")
        index_width = _ceil_log2_at_least_one(row_elems)
        return {
            "kind": "logit_rank",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "logit_width": logit_bits * row_elems,
            "top_index_width": index_width * top_k,
            "top_logit_width": logit_bits * top_k,
            "index_bits": index_width,
            "logit_bits": logit_bits,
            "top_k": top_k,
            "logit_signed": bool(options.get("logit_signed", True)),
            "include_mg_cpa": False,
        }
    if op_type == "candidate_stream_merge_fifo":
        options = entry.get("options", {})
        top_k = int(options.get("top_k", 1))
        logit_bits = int(options.get("logit_bits", bit_width) or bit_width)
        token_id_bits = int(options.get("token_id_bits", 16))
        fifo_depth_groups = int(options.get("fifo_depth_groups", 16))
        counter_bits = int(options.get("counter_bits", 32))
        if top_k <= 0:
            raise ValueError("candidate_stream_merge_fifo top_k must be positive")
        if logit_bits <= 0:
            raise ValueError("candidate_stream_merge_fifo logit_bits must be positive")
        if token_id_bits <= 0:
            raise ValueError("candidate_stream_merge_fifo token_id_bits must be positive")
        if fifo_depth_groups <= 0:
            raise ValueError("candidate_stream_merge_fifo fifo_depth_groups must be positive")
        if counter_bits <= 0:
            raise ValueError("candidate_stream_merge_fifo counter_bits must be positive")
        return {
            "kind": "candidate_stream_merge_fifo",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "top_k": top_k,
            "logit_bits": logit_bits,
            "token_id_bits": token_id_bits,
            "token_width": token_id_bits * top_k,
            "logit_width": logit_bits * top_k,
            "counter_bits": counter_bits,
            "logit_signed": bool(options.get("logit_signed", True)),
            "include_mg_cpa": False,
        }
    raise ValueError(f"generate_design.py does not support operation type: {op_type}")


def locate_rtlgen_binary():
    candidates = [
        repo_root / "build" / "rtlgen",
        repo_root / "bin" / "rtlgen",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return "rtlgen"

def main():
    parser = argparse.ArgumentParser(description="Generate Verilog and OpenROAD files.")
    parser.add_argument("config", help="Path to the configuration JSON file.")
    parser.add_argument("platform", help="Name of the platform (e.g., sky130hd, nangate45).")
    parser.add_argument("--optimization_target", default="area", choices=["area", "timing", "power"], help="Optimization target for autotuner.")
    parser.add_argument("--core_utilization_min", type=int, default=20, help="Min value for CORE_UTILIZATION.")
    parser.add_argument("--core_utilization_max", type=int, default=70, help="Max value for CORE_UTILIZATION.")
    parser.add_argument("--place_density_min", type=float, default=0.2, help="Min value for PLACE_DENSITY.")
    parser.add_argument("--place_density_max", type=float, default=0.7, help="Max value for PLACE_DENSITY.")
    parser.add_argument("--clock_period_min", type=float, default=5.0, help="Min value for CLOCK_PERIOD.")
    parser.add_argument("--clock_period_max", type=float, default=20.0, help="Max value for CLOCK_PERIOD.")
    parser.add_argument("--force_gen", type=bool, default=False, help="Force generate if source files exist.")
    
    args = parser.parse_args()

    # Read JSON config file
    with open(args.config, "r") as f:
        config = json.load(f)

    design = identify_design(config)
    module_name = design["module_name"]
    wrapper_name = design["wrapper_name"]

    # Create directories
    src_dir = os.path.join("src", wrapper_name)
    os.makedirs(src_dir, exist_ok=True)

    platform_dir = os.path.join(args.platform, wrapper_name)
    os.makedirs(platform_dir, exist_ok=True)

    # Setting destination path. 
    dest_base = "/orfs/flow/designs"
    dest_platform_dir = os.path.join(dest_base, platform_dir)
    dest_src_dir = os.path.join(dest_base, src_dir)

    # Generate Verilog
    if args.force_gen or not os.path.isdir(dest_src_dir):
        ld_library_path = os.path.expanduser("~/work/or-tools_x86_64_Ubuntu-22.04_cpp_v9.10.4067/lib")
        onnxruntime_lib = str(repo_root / "third_party" / "onnxruntime-linux-x64-1.23.1" / "lib")

        env = os.environ.copy()
        ld_paths = [ld_library_path, onnxruntime_lib, env.get("LD_LIBRARY_PATH", "")]
        env["LD_LIBRARY_PATH"] = ":".join([p for p in ld_paths if p])

        subprocess.run([locate_rtlgen_binary(), args.config], env=env, check=True)
        os.rename(f"{module_name}.v", os.path.join(src_dir, f"{module_name}.v"))
        # Only multiplier (non-Yosys) emits MG_CPA.v
        if design["include_mg_cpa"]:
            os.rename("MG_CPA.v", os.path.join(src_dir, "MG_CPA.v"))

        # Generate Wrapper
        generate_wrapper(config, src_dir, design)
        print(f"Generated files in {src_dir}")
        # Move to /orfs/flow
        os.makedirs(os.path.dirname(dest_src_dir), exist_ok=True)
        if os.path.isdir(dest_src_dir):
            shutil.rmtree(dest_src_dir)
        shutil.move(src_dir, dest_src_dir)
        print(f"Moved generated src files to {dest_src_dir}")

    # Generate OpenROAD files
    generate_config_mk(platform_dir, args.platform, design)
    generate_constraint_sdc(platform_dir)
    generate_autotuner_json(platform_dir, args)


    # Copy platform-specific files
    if args.platform == "nangate45":
        shutil.copy(current_file_path + "/nangate45/grid_strategy-M1-M4-M7.tcl", platform_dir)
        shutil.copy(current_file_path + "/nangate45/rules-base.json", platform_dir)
    elif args.platform == "sky130hd":
        shutil.copy(current_file_path + "/sky130hd/rules-base.json", platform_dir)
    elif args.platform == "asap7":
        shutil.copy(current_file_path + "/asap7/rules-base.json", platform_dir)

    print(f"Generated platform files in {platform_dir}")

    # Create parent directories for destination
    os.makedirs(os.path.dirname(dest_platform_dir), exist_ok=True)

    # Remove destination if it exists to avoid nesting
    if os.path.isdir(dest_platform_dir):
        shutil.rmtree(dest_platform_dir)
    shutil.move(platform_dir, dest_platform_dir)

    print(f"Moved generated platform files to {dest_platform_dir}")

def generate_wrapper(config, src_dir, design):
    module_name = design["module_name"]
    wrapper_name = design["wrapper_name"]
    input_width = int(design.get("input_width", 0))
    output_width = int(design.get("output_width", 0))

    if design["kind"] in ("multiplier", "multiplier_yosys"):
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input [{input_width-1}:0] multiplicand,
  input [{input_width-1}:0] multiplier,
  output [{output_width-1}:0] product
);

  reg [{input_width-1}:0] multiplicand_reg;
  reg [{input_width-1}:0] multiplier_reg;
  wire [{output_width-1}:0] product_wire;
  reg [{output_width-1}:0] product_reg;

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
    elif design["kind"] == "adder":
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input [{input_width-1}:0] a,
  input [{input_width-1}:0] b,
  output [{output_width-1}:0] sum,
  output cout
);

  reg [{input_width-1}:0] a_reg;
  reg [{input_width-1}:0] b_reg;
  wire [{output_width-1}:0] sum_wire;
  wire cout_wire;
  reg [{output_width-1}:0] sum_reg;
  reg cout_reg;

  {module_name} dut (
    .a(a_reg),
    .b(b_reg),
    .sum(sum_wire),
    .cout(cout_wire)
  );

  always @(posedge clk) begin
    a_reg <= a;
    b_reg <= b;
    sum_reg <= sum_wire;
    cout_reg <= cout_wire;
  end

  assign sum = sum_reg;
  assign cout = cout_reg;

endmodule
"""
    elif design["kind"] in ("scalar_unary", "vector_unary"):
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input [{input_width-1}:0] X,
  output [{output_width-1}:0] Y
);

  reg [{input_width-1}:0] x_reg;
  wire [{output_width-1}:0] y_wire;
  reg [{output_width-1}:0] y_reg;

  {module_name} dut (
    .X(x_reg),
    .Y(y_wire)
  );

  always @(posedge clk) begin
    x_reg <= X;
    y_reg <= y_wire;
  end

  assign Y = y_reg;

endmodule
"""
    elif design["kind"] == "score_tie_rank":
        score_width = int(design["score_width"])
        logit_width = int(design["logit_width"])
        index_width = int(design["index_width"])
        score_bits = int(design["score_bits"])
        logit_bits = int(design["logit_bits"])
        signed_kw = "signed " if design.get("logit_signed", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input [{score_width-1}:0] scores,
  input {signed_kw}[{logit_width-1}:0] logits,
  output [{index_width-1}:0] best_index,
  output [{score_bits-1}:0] best_score,
  output {signed_kw}[{logit_bits-1}:0] best_logit
);

  reg [{score_width-1}:0] scores_reg;
  reg {signed_kw}[{logit_width-1}:0] logits_reg;
  wire [{index_width-1}:0] best_index_wire;
  wire [{score_bits-1}:0] best_score_wire;
  wire {signed_kw}[{logit_bits-1}:0] best_logit_wire;
  reg [{index_width-1}:0] best_index_reg;
  reg [{score_bits-1}:0] best_score_reg;
  reg {signed_kw}[{logit_bits-1}:0] best_logit_reg;

  {module_name} dut (
    .scores(scores_reg),
    .logits(logits_reg),
    .best_index(best_index_wire),
    .best_score(best_score_wire),
    .best_logit(best_logit_wire)
  );

  always @(posedge clk) begin
    scores_reg <= scores;
    logits_reg <= logits;
    best_index_reg <= best_index_wire;
    best_score_reg <= best_score_wire;
    best_logit_reg <= best_logit_wire;
  end

  assign best_index = best_index_reg;
  assign best_score = best_score_reg;
  assign best_logit = best_logit_reg;

endmodule
"""
    elif design["kind"] == "logit_rank":
        logit_width = int(design["logit_width"])
        top_index_width = int(design["top_index_width"])
        top_logit_width = int(design["top_logit_width"])
        signed_kw = "signed " if design.get("logit_signed", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input {signed_kw}[{logit_width-1}:0] logits,
  output [{top_index_width-1}:0] top_indices,
  output {signed_kw}[{top_logit_width-1}:0] top_logits
);

  reg {signed_kw}[{logit_width-1}:0] logits_reg;
  wire [{top_index_width-1}:0] top_indices_wire;
  wire {signed_kw}[{top_logit_width-1}:0] top_logits_wire;
  reg [{top_index_width-1}:0] top_indices_reg;
  reg {signed_kw}[{top_logit_width-1}:0] top_logits_reg;

  {module_name} dut (
    .logits(logits_reg),
    .top_indices(top_indices_wire),
    .top_logits(top_logits_wire)
  );

  always @(posedge clk) begin
    logits_reg <= logits;
    top_indices_reg <= top_indices_wire;
    top_logits_reg <= top_logits_wire;
  end

  assign top_indices = top_indices_reg;
  assign top_logits = top_logits_reg;

endmodule
"""
    elif design["kind"] == "candidate_stream_merge_fifo":
        top_k = int(design["top_k"])
        token_width = int(design["token_width"])
        logit_width = int(design["logit_width"])
        counter_bits = int(design["counter_bits"])
        signed_kw = "signed " if design.get("logit_signed", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  input in_valid,
  output in_ready,
  input in_last,
  input [{top_k-1}:0] in_valid_mask,
  input [{token_width-1}:0] in_token_ids,
  input {signed_kw}[{logit_width-1}:0] in_logits,
  output out_valid,
  input out_ready,
  output [{top_k-1}:0] out_valid_mask,
  output [{token_width-1}:0] out_token_ids,
  output {signed_kw}[{logit_width-1}:0] out_logits,
  output [{counter_bits-1}:0] accepted_group_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] fifo_max_occupancy,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_last(in_last),
    .in_valid_mask(in_valid_mask),
    .in_token_ids(in_token_ids),
    .in_logits(in_logits),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_valid_mask(out_valid_mask),
    .out_token_ids(out_token_ids),
    .out_logits(out_logits),
    .accepted_group_count(accepted_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .fifo_max_occupancy(fifo_max_occupancy),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    else:
        raise ValueError(f"Unsupported design kind for wrapper generation: {design['kind']}")

    with open(os.path.join(src_dir, f"{wrapper_name}.v"), "w") as f:
        f.write(wrapper_content)

def generate_config_mk(platform_dir, platform, design):
    module_name = design["module_name"]
    wrapper_name = design["wrapper_name"]
    verilog_files = [
        f"$(DESIGN_HOME)/src/{wrapper_name}/{module_name}.v",
        f"$(DESIGN_HOME)/src/{wrapper_name}/{wrapper_name}.v",
    ]
    if design["include_mg_cpa"]:
        verilog_files.append(f"$(DESIGN_HOME)/src/{wrapper_name}/MG_CPA.v")

    content = f"""
export PLATFORM = {platform}
export DESIGN_NAME = {wrapper_name}
export VERILOG_FILES = {' '.join(verilog_files)}
export SDC_FILE = $(DESIGN_HOME)/{platform}/{wrapper_name}/constraint.sdc
export TOP_MODULE = {wrapper_name}
export CORE_UTILIZATION = 30
"""
    if platform == "nangate45":
        content += "export PDN_TCL ?= $(DESIGN_HOME)/nangate45/$(DESIGN_NAME)/grid_strategy-M1-M4-M7.tcl\n"
        content += "\n# Register-wrapped Layer-1 blocks are evaluated as macro timing boundaries, not chip pads.\n"
        content += "# Allow dense block-pin placement so wide datapath buses do not fail at IO placement.\n"
        content += "export IO_PLACER_H ?= metal3 metal5\n"
        content += "export IO_PLACER_V ?= metal4 metal6\n"
        content += "export PLACE_PINS_ARGS ?= -min_distance 0\n"
    with open(os.path.join(platform_dir, "config.mk"), "w") as f:
        f.write(content)

def generate_constraint_sdc(platform_dir):
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
    with open(current_file_path+"/autotuner_base.json", "r") as f:
        content = json.load(f)

    content["_SDC_CLK_PERIOD"]["minmax"] = [args.clock_period_min, args.clock_period_max]
    content["CORE_UTILIZATION"]["minmax"] = [args.core_utilization_min, args.core_utilization_max]
    content["_FR_FILE_PATH"] = content["_FR_FILE_PATH"].replace("sky130hd", args.platform)

    with open(os.path.join(platform_dir, "autotuner.json"), "w") as f:
        json.dump(content, f, indent=4)

if __name__ == "__main__":
    main()
