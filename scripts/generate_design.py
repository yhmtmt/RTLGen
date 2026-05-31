#!/usr/bin/env python3

import json
import os
import subprocess
import argparse
import shutil
import tempfile
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
    if op_type == "attention_kv_tile":
        options = entry.get("options", {})
        kv_bits = int(options.get("kv_bits", bit_width) or bit_width)
        head_dim = int(options.get("head_dim", 64))
        lanes = int(options.get("lanes", 16))
        stream_bytes_per_cycle = int(options.get("stream_bytes_per_cycle", 256))
        accum_bits = int(options.get("accum_bits", 48))
        counter_bits = int(options.get("counter_bits", 32))
        if head_dim <= 0:
            raise ValueError("attention_kv_tile head_dim must be positive")
        if kv_bits <= 0:
            raise ValueError("attention_kv_tile kv_bits must be positive")
        if lanes <= 0 or lanes > head_dim:
            raise ValueError("attention_kv_tile lanes must be in [1, head_dim]")
        if stream_bytes_per_cycle <= 0:
            raise ValueError("attention_kv_tile stream_bytes_per_cycle must be positive")
        if stream_bytes_per_cycle * 8 < lanes * kv_bits * 2:
            raise ValueError("attention_kv_tile stream_bytes_per_cycle cannot carry query+key lane payload")
        if accum_bits <= 0:
            raise ValueError("attention_kv_tile accum_bits must be positive")
        if counter_bits <= 0:
            raise ValueError("attention_kv_tile counter_bits must be positive")
        return {
            "kind": "attention_kv_tile",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "fragment_width": lanes * kv_bits,
            "accum_bits": accum_bits,
            "counter_bits": counter_bits,
            "signed_inputs": bool(options.get("signed_inputs", True)),
            "include_mg_cpa": False,
        }
    if op_type == "attention_kv_reducer":
        options = entry.get("options", {})
        value_bits = int(options.get("value_bits", bit_width) or bit_width)
        stat_bits = int(options.get("stat_bits", 16))
        lanes = int(options.get("lanes", 16))
        partials = int(options.get("partials", 2))
        accum_bits = int(options.get("accum_bits", 32))
        counter_bits = int(options.get("counter_bits", 32))
        if lanes <= 0:
            raise ValueError("attention_kv_reducer lanes must be positive")
        if value_bits <= 0:
            raise ValueError("attention_kv_reducer value_bits must be positive")
        if stat_bits <= 0:
            raise ValueError("attention_kv_reducer stat_bits must be positive")
        if partials <= 0:
            raise ValueError("attention_kv_reducer partials must be positive")
        if accum_bits <= 0:
            raise ValueError("attention_kv_reducer accum_bits must be positive")
        if counter_bits <= 0:
            raise ValueError("attention_kv_reducer counter_bits must be positive")
        return {
            "kind": "attention_kv_reducer",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "value_width": lanes * value_bits,
            "reduced_value_width": lanes * accum_bits,
            "stat_width": 2 * stat_bits,
            "counter_bits": counter_bits,
            "signed_values": bool(options.get("signed_values", True)),
            "include_mg_cpa": False,
        }
    if op_type == "attention_kv_reducer_tree":
        options = entry.get("options", {})
        value_bits = int(options.get("value_bits", bit_width) or bit_width)
        stat_bits = int(options.get("stat_bits", 16))
        lanes = int(options.get("lanes", 16))
        partials = int(options.get("partials", 8))
        accum_bits = int(options.get("accum_bits", 32))
        counter_bits = int(options.get("counter_bits", 32))
        if lanes <= 0:
            raise ValueError("attention_kv_reducer_tree lanes must be positive")
        if value_bits <= 0:
            raise ValueError("attention_kv_reducer_tree value_bits must be positive")
        if stat_bits <= 0:
            raise ValueError("attention_kv_reducer_tree stat_bits must be positive")
        if partials <= 1 or partials & (partials - 1):
            raise ValueError("attention_kv_reducer_tree partials must be a power of two greater than one")
        if accum_bits <= 0:
            raise ValueError("attention_kv_reducer_tree accum_bits must be positive")
        if counter_bits <= 0:
            raise ValueError("attention_kv_reducer_tree counter_bits must be positive")
        return {
            "kind": "attention_kv_reducer_tree",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "value_width": partials * lanes * value_bits,
            "reduced_value_width": lanes * accum_bits,
            "stat_width": partials * 2 * stat_bits,
            "reduced_stat_width": 2 * stat_bits,
            "counter_bits": counter_bits,
            "signed_values": bool(options.get("signed_values", True)),
            "include_mg_cpa": False,
        }
    if op_type == "attention_kv_reducer_folded":
        options = entry.get("options", {})
        value_bits = int(options.get("value_bits", bit_width) or bit_width)
        stat_bits = int(options.get("stat_bits", 16))
        lanes = int(options.get("lanes", 16))
        partials = int(options.get("partials", 8))
        partials_per_cycle = int(options.get("partials_per_cycle", 2))
        accum_bits = int(options.get("accum_bits", 32))
        counter_bits = int(options.get("counter_bits", 32))
        if lanes <= 0:
            raise ValueError("attention_kv_reducer_folded lanes must be positive")
        if value_bits <= 0:
            raise ValueError("attention_kv_reducer_folded value_bits must be positive")
        if stat_bits <= 0:
            raise ValueError("attention_kv_reducer_folded stat_bits must be positive")
        if partials <= 1:
            raise ValueError("attention_kv_reducer_folded partials must be greater than one")
        if partials_per_cycle <= 0 or partials_per_cycle > partials or partials % partials_per_cycle:
            raise ValueError("attention_kv_reducer_folded partials_per_cycle must divide partials")
        if accum_bits <= 0:
            raise ValueError("attention_kv_reducer_folded accum_bits must be positive")
        if counter_bits <= 0:
            raise ValueError("attention_kv_reducer_folded counter_bits must be positive")
        wrapper_mode = str(options.get("wrapper_mode", "external_input"))
        if wrapper_mode not in ("external_input", "internal_source", "producer_coupled"):
            raise ValueError(
                "attention_kv_reducer_folded wrapper_mode must be external_input, "
                "internal_source, or producer_coupled"
            )
        kind = "attention_kv_reducer_folded"
        if wrapper_mode == "internal_source":
            kind = "attention_kv_reducer_folded_internal_source"
        elif wrapper_mode == "producer_coupled":
            kind = "attention_kv_reducer_folded_producer_coupled"
        return {
            "kind": kind,
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "value_width": partials_per_cycle * lanes * value_bits,
            "reduced_value_width": lanes * accum_bits,
            "stat_width": partials_per_cycle * 2 * stat_bits,
            "reduced_stat_width": 2 * stat_bits,
            "lanes": lanes,
            "value_bits": value_bits,
            "stat_bits": stat_bits,
            "partials": partials,
            "partials_per_cycle": partials_per_cycle,
            "accum_bits": accum_bits,
            "counter_bits": counter_bits,
            "signed_values": bool(options.get("signed_values", True)),
            "include_mg_cpa": False,
        }
    if op_type in {"attention_kv_tile_reducer_folded", "attention_kv_full_value_tile"}:
        options = entry.get("options", {})
        kv_bits = int(options.get("kv_bits", bit_width) or bit_width)
        head_dim = int(options.get("head_dim", 64))
        tile_lanes = int(options.get("tile_lanes", options.get("lanes", 16)))
        stream_bytes_per_cycle = int(options.get("stream_bytes_per_cycle", 256))
        score_bits = int(options.get("score_bits", options.get("tile_accum_bits", 48)))
        raw_value_bits = int(options.get("value_bits", 16))
        softmax_weight_bits = int(options.get("softmax_weight_bits", min(score_bits, 16)))
        weighted_value_bits = int(options.get("weighted_value_bits", raw_value_bits))
        reducer_value_bits = weighted_value_bits if op_type == "attention_kv_full_value_tile" else raw_value_bits
        stat_bits = int(options.get("stat_bits", 16))
        reducer_lanes = int(options.get("reducer_lanes", 16))
        partials = int(options.get("partials", 8))
        partials_per_cycle = int(options.get("partials_per_cycle", 2))
        reducer_accum_bits = int(options.get("reducer_accum_bits", 24))
        counter_bits = int(options.get("counter_bits", 32))
        if head_dim <= 0:
            raise ValueError(f"{op_type} head_dim must be positive")
        if kv_bits <= 0:
            raise ValueError(f"{op_type} kv_bits must be positive")
        if tile_lanes <= 0 or tile_lanes > head_dim:
            raise ValueError(f"{op_type} tile_lanes must be in [1, head_dim]")
        if stream_bytes_per_cycle * 8 < tile_lanes * kv_bits * 2:
            raise ValueError(f"{op_type} stream_bytes_per_cycle cannot carry query+key lane payload")
        if score_bits <= 0:
            raise ValueError(f"{op_type} score_bits must be positive")
        if raw_value_bits <= 0 or weighted_value_bits <= 0 or softmax_weight_bits <= 0:
            raise ValueError(f"{op_type} value/weight widths must be positive")
        if softmax_weight_bits > score_bits:
            raise ValueError(f"{op_type} softmax_weight_bits cannot exceed score_bits")
        if weighted_value_bits > raw_value_bits + softmax_weight_bits:
            raise ValueError(f"{op_type} weighted_value_bits cannot exceed value*weight product width")
        if stat_bits <= 0 or reducer_lanes <= 0:
            raise ValueError(f"{op_type} reducer widths/lanes must be positive")
        if partials <= 1:
            raise ValueError(f"{op_type} partials must be greater than one")
        if partials_per_cycle <= 0 or partials_per_cycle > partials or partials % partials_per_cycle:
            raise ValueError(f"{op_type} partials_per_cycle must divide partials")
        if reducer_accum_bits <= 0 or counter_bits <= 0:
            raise ValueError(f"{op_type} accum/counter bits must be positive")
        return {
            "kind": op_type,
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "kv_bits": kv_bits,
            "head_dim": head_dim,
            "tile_lanes": tile_lanes,
            "stream_bytes_per_cycle": stream_bytes_per_cycle,
            "score_bits": score_bits,
            "tile_fragment_width": tile_lanes * kv_bits,
            "raw_value_bits": raw_value_bits,
            "softmax_weight_bits": softmax_weight_bits,
            "weighted_value_bits": weighted_value_bits,
            "value_bits": reducer_value_bits,
            "stat_bits": stat_bits,
            "reducer_lanes": reducer_lanes,
            "partials": partials,
            "partials_per_cycle": partials_per_cycle,
            "reducer_accum_bits": reducer_accum_bits,
            "value_width": partials_per_cycle * reducer_lanes * reducer_value_bits,
            "stat_width": partials_per_cycle * 2 * stat_bits,
            "reduced_value_width": reducer_lanes * reducer_accum_bits,
            "reduced_stat_width": 2 * stat_bits,
            "counter_bits": counter_bits,
            "signed_inputs": bool(options.get("signed_inputs", True)),
            "signed_values": bool(options.get("signed_values", True)),
            "include_mg_cpa": False,
        }
    if op_type == "l1_memory_noc_primitive":
        options = entry.get("options", {})
        primitive = str(options.get("primitive", "fifo"))
        flit_bits = int(options.get("flit_bits", bit_width) or bit_width)
        depth = int(options.get("depth", 8))
        ports = int(options.get("ports", 4))
        counter_bits = int(options.get("counter_bits", 32))
        if primitive not in ("fifo", "router"):
            raise ValueError("l1_memory_noc_primitive primitive must be fifo or router")
        if flit_bits <= 0:
            raise ValueError("l1_memory_noc_primitive flit_bits must be positive")
        if depth <= 1:
            raise ValueError("l1_memory_noc_primitive depth must be greater than one")
        if ports <= 1:
            raise ValueError("l1_memory_noc_primitive ports must be greater than one")
        if counter_bits <= 0:
            raise ValueError("l1_memory_noc_primitive counter_bits must be positive")
        return {
            "kind": "l1_memory_noc_primitive",
            "module_name": module_name,
            "wrapper_name": f"{module_name}_wrapper",
            "primitive": primitive,
            "flit_bits": flit_bits,
            "depth": depth,
            "ports": ports,
            "counter_bits": counter_bits,
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

        if design["kind"] in ("attention_kv_tile_reducer_folded", "attention_kv_full_value_tile", "l1_memory_noc_primitive"):
            generate_direct_design(config, src_dir, design, env)
        else:
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


def _run_rtlgen_config(config, workdir, env):
    config_path = Path(workdir) / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    subprocess.run([locate_rtlgen_binary(), str(config_path)], cwd=workdir, env=env, check=True)


def _slice_counter(name, width, counter_bits):
    if counter_bits >= width:
        return f"{name}[{width-1}:0]"
    return f"{{{{{width-counter_bits}{{1'b0}}}}, {name}}}"


def generate_direct_design(config, src_dir, design, env):
    if design["kind"] in ("attention_kv_tile_reducer_folded", "attention_kv_full_value_tile"):
        generate_attention_tile_reducer_design(config, src_dir, design, env)
    elif design["kind"] == "l1_memory_noc_primitive":
        generate_l1_memory_noc_design(src_dir, design)
    else:
        raise ValueError(f"Unsupported direct design kind: {design['kind']}")


def generate_attention_tile_reducer_design(config, src_dir, design, env):
    module_name = design["module_name"]
    tile_name = f"{module_name}_tile"
    reducer_name = f"{module_name}_reducer"
    operand_name = config.get("operands", [{"name": "operand"}])[0].get("name", "operand")
    signed_inputs = bool(design.get("signed_inputs", True))
    signed_values = bool(design.get("signed_values", True))
    full_value_path = design["kind"] == "attention_kv_full_value_tile"

    tile_cfg = {
        "version": config.get("version", "1.1"),
        "operands": [{
            "name": operand_name,
            "dimensions": 1,
            "bit_width": design["kv_bits"],
            "signed": signed_inputs,
            "kind": "int",
        }],
        "operations": [{
            "type": "attention_kv_tile",
            "module_name": tile_name,
            "operand": operand_name,
            "options": {
                "head_dim": design["head_dim"],
                "kv_bits": design["kv_bits"],
                "lanes": design["tile_lanes"],
                "stream_bytes_per_cycle": design["stream_bytes_per_cycle"],
                "accum_bits": design["score_bits"],
                "counter_bits": design["counter_bits"],
                "signed_inputs": signed_inputs,
            },
        }],
    }
    reducer_cfg = {
        "version": config.get("version", "1.1"),
        "operands": [{
            "name": "value_fragments",
            "dimensions": 1,
            "bit_width": design["value_bits"],
            "signed": signed_values,
            "kind": "int",
        }],
        "operations": [{
            "type": "attention_kv_reducer_folded",
            "module_name": reducer_name,
            "operand": "value_fragments",
            "options": {
                "lanes": design["reducer_lanes"],
                "value_bits": design["value_bits"],
                "stat_bits": design["stat_bits"],
                "partials": design["partials"],
                "partials_per_cycle": design["partials_per_cycle"],
                "accum_bits": design["reducer_accum_bits"],
                "counter_bits": design["counter_bits"],
                "signed_values": signed_values,
            },
        }],
    }

    with tempfile.TemporaryDirectory() as tmp:
        _run_rtlgen_config(tile_cfg, tmp, env)
        _run_rtlgen_config(reducer_cfg, tmp, env)
        tile_text = (Path(tmp) / f"{tile_name}.v").read_text(encoding="utf-8")
        reducer_text = (Path(tmp) / f"{reducer_name}.v").read_text(encoding="utf-8")

    value_product_w = int(design["softmax_weight_bits"]) + int(design["raw_value_bits"])
    product_wires = []
    value_assigns = []
    for partial in range(design["partials_per_cycle"]):
        for lane in range(design["reducer_lanes"]):
            base = (partial * design["reducer_lanes"] + lane) * design["value_bits"]
            salt = (partial + 1) * 19 + lane
            if full_value_path:
                wire_name = f"weighted_value_p{partial}_l{lane}"
                product_wires.append(
                    f"  wire signed [PRODUCT_W-1:0] {wire_name} = "
                    f"$signed(score_latched[WEIGHT_W-1:0]) * "
                    f"$signed({_slice_counter('value_source_count', design['raw_value_bits'], design['counter_bits'])} + {design['raw_value_bits']}'sd{salt});"
                )
                value_assigns.append(
                    f"          reducer_value_fragments[{base} +: VALUE_W] <= {wire_name}[VALUE_W-1:0];"
                )
            else:
                value_assigns.append(
                    f"          reducer_value_fragments[{base} +: VALUE_W] <= "
                    f"score_latched[VALUE_W-1:0] + {_slice_counter('chunk_index', design['value_bits'], design['counter_bits'])} + {salt};"
                )
    stat_assigns = []
    for partial in range(design["partials_per_cycle"]):
        base0 = partial * 2 * design["stat_bits"]
        base1 = (partial * 2 + 1) * design["stat_bits"]
        stat_assigns.append(
            f"          reducer_stat_fragments[{base0} +: STAT_W] <= score_latched[STAT_W-1:0] + {partial + 1};"
        )
        stat_assigns.append(
            f"          reducer_stat_fragments[{base1} +: STAT_W] <= {_slice_counter('group_index', design['stat_bits'], design['counter_bits'])} + {partial + 33};"
        )

    tile_assigns = []
    for lane in range(design["tile_lanes"]):
        base = lane * design["kv_bits"]
        tile_assigns.append(
            f"          query_fragment[{base} +: KV_W] <= {_slice_counter('tile_source_step', design['kv_bits'], design['counter_bits'])} + {lane + 1};"
        )
        tile_assigns.append(
            f"          key_fragment[{base} +: KV_W] <= {_slice_counter('tile_source_step', design['kv_bits'], design['counter_bits'])} + {lane + 7};"
        )

    top = f"""
module {module_name}(
  input clk,
  input rst_n,
  output reduced_valid,
  output signed [{design['reduced_value_width']-1}:0] reduced_value_fragment,
  output [{design['reduced_stat_width']-1}:0] reduced_stat_fragment,
  output [{design['counter_bits']-1}:0] tile_accepted_count,
  output [{design['counter_bits']-1}:0] tile_byte_count,
  output [{design['counter_bits']-1}:0] tile_stall_cycles,
  output [{design['counter_bits']-1}:0] reducer_accepted_chunk_count,
  output [{design['counter_bits']-1}:0] reducer_completed_group_count,
  output [{design['counter_bits']-1}:0] reducer_stall_cycles,
  output [{design['counter_bits']-1}:0] final_completion_cycle
);

  localparam integer KV_W = {design['kv_bits']};
  localparam integer TILE_LANES = {design['tile_lanes']};
  localparam integer TILE_FRAGMENT_W = {design['tile_fragment_width']};
  localparam integer SCORE_W = {design['score_bits']};
  localparam integer VALUE_W = {design['value_bits']};
  localparam integer RAW_VALUE_W = {design['raw_value_bits']};
  localparam integer WEIGHT_W = {design['softmax_weight_bits']};
  localparam integer PRODUCT_W = {value_product_w};
  localparam integer STAT_W = {design['stat_bits']};
  localparam integer VALUE_WIDTH = {design['value_width']};
  localparam integer STAT_WIDTH = {design['stat_width']};
  localparam integer COUNT_W = {design['counter_bits']};
  localparam integer TILE_FRAGMENTS_PER_SCORE = {(design['head_dim'] + design['tile_lanes'] - 1) // design['tile_lanes']};
  localparam integer REDUCER_CHUNKS_PER_GROUP = {design['partials'] // design['partials_per_cycle']};

  reg [TILE_FRAGMENT_W-1:0] query_fragment;
  reg [TILE_FRAGMENT_W-1:0] key_fragment;
  reg tile_valid;
  reg [COUNT_W-1:0] tile_fragment_index;
  reg [COUNT_W-1:0] tile_source_step;
  wire tile_ready;
  wire tile_last = tile_fragment_index == (TILE_FRAGMENTS_PER_SCORE-1);
  wire score_valid;
  wire signed [SCORE_W-1:0] score;
  wire [COUNT_W-1:0] tile_cycle_count;
  wire [COUNT_W-1:0] tile_final_completion_cycle;

  reg score_pending;
  wire score_ready = !score_pending;
  reg signed [SCORE_W-1:0] score_latched;
  reg [COUNT_W-1:0] chunk_index;
  reg [COUNT_W-1:0] group_index;
  reg [COUNT_W-1:0] value_source_count;
  reg reducer_valid;
  reg [VALUE_WIDTH-1:0] reducer_value_fragments;
  reg [STAT_WIDTH-1:0] reducer_stat_fragments;
  wire reducer_ready;
  wire [COUNT_W-1:0] reducer_cycle_count;
  wire [COUNT_W-1:0] reducer_final_completion_cycle;
  wire [COUNT_W-1:0] reducer_final_completion_cycle_wire = reducer_final_completion_cycle;

{chr(10).join(product_wires)}

  {tile_name} tile (
    .clk(clk),
    .rst_n(rst_n),
    .tile_valid(tile_valid),
    .tile_ready(tile_ready),
    .tile_last(tile_last),
    .query_fragment(query_fragment),
    .key_fragment(key_fragment),
    .score_valid(score_valid),
    .score_ready(score_ready),
    .score(score),
    .accepted_tile_count(tile_accepted_count),
    .accepted_byte_count(tile_byte_count),
    .producer_stall_cycles(tile_stall_cycles),
    .cycle_count(tile_cycle_count),
    .final_completion_cycle(tile_final_completion_cycle)
  );

  {reducer_name} reducer (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(reducer_valid),
    .partial_ready(reducer_ready),
    .value_fragments(reducer_value_fragments),
    .stat_fragments(reducer_stat_fragments),
    .reduced_valid(reduced_valid),
    .reduced_ready(1'b1),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_chunk_count(reducer_accepted_chunk_count),
    .completed_group_count(reducer_completed_group_count),
    .producer_stall_cycles(reducer_stall_cycles),
    .cycle_count(reducer_cycle_count),
    .final_completion_cycle(reducer_final_completion_cycle)
  );

  assign final_completion_cycle =
      (reducer_final_completion_cycle_wire > tile_final_completion_cycle)
          ? reducer_final_completion_cycle_wire
          : tile_final_completion_cycle;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tile_valid <= 1'b0;
      tile_fragment_index <= {{COUNT_W{{1'b0}}}};
      tile_source_step <= {{COUNT_W{{1'b0}}}};
      query_fragment <= {{TILE_FRAGMENT_W{{1'b0}}}};
      key_fragment <= {{TILE_FRAGMENT_W{{1'b0}}}};
      score_pending <= 1'b0;
      score_latched <= {{SCORE_W{{1'b0}}}};
      chunk_index <= {{COUNT_W{{1'b0}}}};
      group_index <= {{COUNT_W{{1'b0}}}};
      value_source_count <= {{COUNT_W{{1'b0}}}};
      reducer_valid <= 1'b0;
      reducer_value_fragments <= {{VALUE_WIDTH{{1'b0}}}};
      reducer_stat_fragments <= {{STAT_WIDTH{{1'b0}}}};
    end else begin
      tile_valid <= 1'b1;
      if (tile_ready) begin
{chr(10).join(tile_assigns)}
        tile_source_step <= tile_source_step + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        if (tile_last)
          tile_fragment_index <= {{COUNT_W{{1'b0}}}};
        else
          tile_fragment_index <= tile_fragment_index + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
      end

      if (score_valid && score_ready) begin
        score_latched <= score;
        score_pending <= 1'b1;
        chunk_index <= {{COUNT_W{{1'b0}}}};
      end

      if (score_pending && (!reducer_valid || reducer_ready)) begin
{chr(10).join(value_assigns)}
{chr(10).join(stat_assigns)}
        reducer_valid <= 1'b1;
        if (chunk_index == (REDUCER_CHUNKS_PER_GROUP-1)) begin
          score_pending <= 1'b0;
          chunk_index <= {{COUNT_W{{1'b0}}}};
          group_index <= group_index + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        end else begin
          chunk_index <= chunk_index + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        end
        value_source_count <= value_source_count + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
      end else if (reducer_valid && reducer_ready) begin
        reducer_valid <= 1'b0;
      end
    end
  end
endmodule
"""

    out = Path(src_dir) / f"{module_name}.v"
    out.write_text(tile_text + "\n" + reducer_text + "\n" + top, encoding="utf-8")


def generate_l1_memory_noc_design(src_dir, design):
    module_name = design["module_name"]
    if design["primitive"] == "fifo":
        text = _emit_l1_fifo(module_name, design)
    else:
        text = _emit_l1_router(module_name, design)
    Path(src_dir, f"{module_name}.v").write_text(text, encoding="utf-8")


def _emit_l1_fifo(module_name, design):
    header = f"""
`timescale 1ns/1ps

module {module_name}(
  input clk,
  input rst_n,
  output [{design['counter_bits']-1}:0] accepted_flit_count,
  output [{design['counter_bits']-1}:0] emitted_flit_count,
  output [{design['counter_bits']-1}:0] max_occupancy,
  output [{design['counter_bits']-1}:0] producer_stall_cycles,
  output [{design['flit_bits']-1}:0] observed_flit
);
  localparam integer FLIT_W = {design['flit_bits']};
  localparam integer DEPTH = {design['depth']};
  localparam integer COUNT_W = {design['counter_bits']};
  localparam integer PTR_W = {_ceil_log2_at_least_one(design['depth'])};

  reg [FLIT_W-1:0] mem [0:DEPTH-1];
  reg [PTR_W-1:0] wr_ptr;
  reg [PTR_W-1:0] rd_ptr;
  reg [COUNT_W-1:0] occupancy;
  reg [COUNT_W-1:0] accepted_count;
  reg [COUNT_W-1:0] emitted_count;
  reg [COUNT_W-1:0] max_occ;
  reg [COUNT_W-1:0] stall_count;
  reg [COUNT_W-1:0] source_count;
  reg [FLIT_W-1:0] observed;

  wire push = occupancy != {design['counter_bits']}'d{design['depth']};
  wire pop = occupancy != {{COUNT_W{{1'b0}}}};

  assign accepted_flit_count = accepted_count;
  assign emitted_flit_count = emitted_count;
  assign max_occupancy = max_occ;
  assign producer_stall_cycles = stall_count;
  assign observed_flit = observed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= {{PTR_W{{1'b0}}}};
      rd_ptr <= {{PTR_W{{1'b0}}}};
      occupancy <= {{COUNT_W{{1'b0}}}};
      accepted_count <= {{COUNT_W{{1'b0}}}};
      emitted_count <= {{COUNT_W{{1'b0}}}};
      max_occ <= {{COUNT_W{{1'b0}}}};
      stall_count <= {{COUNT_W{{1'b0}}}};
      source_count <= {{COUNT_W{{1'b0}}}};
      observed <= {{FLIT_W{{1'b0}}}};
    end else begin
      if (push) begin
        mem[wr_ptr] <= {{{{(FLIT_W-COUNT_W){{1'b0}}}}, source_count}};
        source_count <= source_count + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        accepted_count <= accepted_count + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        if (wr_ptr == DEPTH-1)
          wr_ptr <= {{PTR_W{{1'b0}}}};
        else
          wr_ptr <= wr_ptr + {{{{(PTR_W-1){{1'b0}}}}, 1'b1}};
      end else begin
        stall_count <= stall_count + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
      end

      if (pop) begin
        observed <= mem[rd_ptr];
        emitted_count <= emitted_count + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
        if (rd_ptr == DEPTH-1)
          rd_ptr <= {{PTR_W{{1'b0}}}};
        else
          rd_ptr <= rd_ptr + {{{{(PTR_W-1){{1'b0}}}}, 1'b1}};
      end

      if (push && !pop)
        occupancy <= occupancy + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
      else if (!push && pop)
        occupancy <= occupancy - {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};

      if (occupancy > max_occ)
        max_occ <= occupancy;
    end
  end
endmodule
"""
    return header


def _emit_l1_router(module_name, design):
    ports = design["ports"]
    flit_bits = design["flit_bits"]
    counter_bits = design["counter_bits"]
    assigns = []
    for outp in range(ports):
        terms = []
        for inp in range(ports):
            terms.append(f"((dest_{inp} == {outp}) ? in_flit_{inp} : {{FLIT_W{{1'b0}}}})")
        assigns.append(f"  wire [FLIT_W-1:0] out_flit_{outp} = " + " | ".join(terms) + ";")
    observe_terms = " ^ ".join([f"out_flit_{i}" for i in range(ports)])
    header = f"""
`timescale 1ns/1ps

module {module_name}(
  input clk,
  input rst_n,
  output [{counter_bits-1}:0] routed_flit_count,
  output [{counter_bits-1}:0] arbitration_cycle_count,
  output [{flit_bits-1}:0] observed_flit
);
  localparam integer FLIT_W = {flit_bits};
  localparam integer PORTS = {ports};
  localparam integer COUNT_W = {counter_bits};
  localparam integer PORT_W = {_ceil_log2_at_least_one(ports)};

  reg [COUNT_W-1:0] routed_count;
  reg [COUNT_W-1:0] cycle_count;
  reg [FLIT_W-1:0] observed;
"""
    regs = "".join(
        f"  reg [FLIT_W-1:0] in_flit_{inp};\n  reg [PORT_W-1:0] dest_{inp};\n"
        for inp in range(ports)
    )
    body = f"""{regs}
{chr(10).join(assigns)}

  assign routed_flit_count = routed_count;
  assign arbitration_cycle_count = cycle_count;
  assign observed_flit = observed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      routed_count <= {{COUNT_W{{1'b0}}}};
      cycle_count <= {{COUNT_W{{1'b0}}}};
      observed <= {{FLIT_W{{1'b0}}}};
"""
    for inp in range(ports):
        body += f"      in_flit_{inp} <= {{FLIT_W{{1'b0}}}};\n      dest_{inp} <= {inp % ports};\n"
    body += "    end else begin\n      cycle_count <= cycle_count + {{(COUNT_W-1){1'b0}}, 1'b1};\n"
    for inp in range(ports):
        body += (
            f"      in_flit_{inp} <= {{{{(FLIT_W-COUNT_W){{1'b0}}}}, cycle_count}} ^ {flit_bits}'d{inp + 1};\n"
            f"      if (dest_{inp} == PORTS-1)\n"
            f"        dest_{inp} <= {{PORT_W{{1'b0}}}};\n"
            f"      else\n"
            f"        dest_{inp} <= dest_{inp} + {{{{(PORT_W-1){{1'b0}}}}, 1'b1}};\n"
        )
    body += f"      observed <= {observe_terms};\n      routed_count <= routed_count + {counter_bits}'d{ports};\n    end\n  end\nendmodule\n"
    return header + body

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
    elif design["kind"] == "attention_kv_tile":
        fragment_width = int(design["fragment_width"])
        accum_bits = int(design["accum_bits"])
        counter_bits = int(design["counter_bits"])
        signed_kw = "signed " if design.get("signed_inputs", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  input tile_valid,
  output tile_ready,
  input tile_last,
  input [{fragment_width-1}:0] query_fragment,
  input [{fragment_width-1}:0] key_fragment,
  input score_ready,
  output score_valid,
  output {signed_kw}[{accum_bits-1}:0] score,
  output [{counter_bits-1}:0] accepted_tile_count,
  output [{counter_bits-1}:0] accepted_byte_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] cycle_count,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .tile_valid(tile_valid),
    .tile_ready(tile_ready),
    .tile_last(tile_last),
    .query_fragment(query_fragment),
    .key_fragment(key_fragment),
    .score_ready(score_ready),
    .score_valid(score_valid),
    .score(score),
    .accepted_tile_count(accepted_tile_count),
    .accepted_byte_count(accepted_byte_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] == "attention_kv_reducer":
        value_width = int(design["value_width"])
        reduced_value_width = int(design["reduced_value_width"])
        stat_width = int(design["stat_width"])
        counter_bits = int(design["counter_bits"])
        signed_kw = "signed " if design.get("signed_values", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  input partial_valid,
  output partial_ready,
  input partial_last,
  input [{value_width-1}:0] value_fragment,
  input [{stat_width-1}:0] stat_fragment,
  output reduced_valid,
  input reduced_ready,
  output {signed_kw}[{reduced_value_width-1}:0] reduced_value_fragment,
  output [{stat_width-1}:0] reduced_stat_fragment,
  output [{counter_bits-1}:0] accepted_partial_count,
  output [{counter_bits-1}:0] completed_group_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] cycle_count,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .partial_last(partial_last),
    .value_fragment(value_fragment),
    .stat_fragment(stat_fragment),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_partial_count(accepted_partial_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] == "attention_kv_reducer_tree":
        value_width = int(design["value_width"])
        reduced_value_width = int(design["reduced_value_width"])
        stat_width = int(design["stat_width"])
        reduced_stat_width = int(design["reduced_stat_width"])
        counter_bits = int(design["counter_bits"])
        signed_kw = "signed " if design.get("signed_values", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  input partial_valid,
  output partial_ready,
  input [{value_width-1}:0] value_fragments,
  input [{stat_width-1}:0] stat_fragments,
  output reduced_valid,
  input reduced_ready,
  output {signed_kw}[{reduced_value_width-1}:0] reduced_value_fragment,
  output [{reduced_stat_width-1}:0] reduced_stat_fragment,
  output [{counter_bits-1}:0] accepted_group_count,
  output [{counter_bits-1}:0] completed_group_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] cycle_count,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .value_fragments(value_fragments),
    .stat_fragments(stat_fragments),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_group_count(accepted_group_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] == "attention_kv_reducer_folded":
        value_width = int(design["value_width"])
        reduced_value_width = int(design["reduced_value_width"])
        stat_width = int(design["stat_width"])
        reduced_stat_width = int(design["reduced_stat_width"])
        counter_bits = int(design["counter_bits"])
        signed_kw = "signed " if design.get("signed_values", True) else ""
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  input partial_valid,
  output partial_ready,
  input [{value_width-1}:0] value_fragments,
  input [{stat_width-1}:0] stat_fragments,
  output reduced_valid,
  input reduced_ready,
  output {signed_kw}[{reduced_value_width-1}:0] reduced_value_fragment,
  output [{reduced_stat_width-1}:0] reduced_stat_fragment,
  output [{counter_bits-1}:0] accepted_chunk_count,
  output [{counter_bits-1}:0] completed_group_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] cycle_count,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .value_fragments(value_fragments),
    .stat_fragments(stat_fragments),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_chunk_count(accepted_chunk_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] in ("attention_kv_reducer_folded_internal_source", "attention_kv_reducer_folded_producer_coupled"):
        value_width = int(design["value_width"])
        reduced_value_width = int(design["reduced_value_width"])
        stat_width = int(design["stat_width"])
        reduced_stat_width = int(design["reduced_stat_width"])
        counter_bits = int(design["counter_bits"])
        value_bits = int(design["value_bits"])
        stat_bits = int(design["stat_bits"])
        lanes = int(design["lanes"])
        partials = int(design["partials"])
        partials_per_cycle = int(design["partials_per_cycle"])
        accum_bits = int(design["accum_bits"])
        signed_kw = "signed " if design.get("signed_values", True) else ""
        producer_coupled = design["kind"] == "attention_kv_reducer_folded_producer_coupled"

        def counter_expr(width, salt):
            if counter_bits >= width:
                base = f"source_step[{width-1}:0]"
            else:
                base = f"{{{{{width-counter_bits}{{1'b0}}}}, source_step}}"
            return f"({base} + {width}'d{salt % (1 << min(width, 30))})"

        value_assigns = []
        for partial in range(partials_per_cycle):
            for lane in range(lanes):
                base = (partial * lanes + lane) * value_bits
                salt = (partial + 1) * 17 + lane
                if producer_coupled:
                    value_assigns.append(
                        f"          producer_value_fragments[{base} +: {value_bits}] <= {counter_expr(value_bits, salt)};"
                    )
                else:
                    value_assigns.append(
                        f"  assign value_fragments[{base} +: {value_bits}] = {counter_expr(value_bits, salt)};"
                    )

        stat_assigns = []
        for partial in range(partials_per_cycle):
            base0 = partial * 2 * stat_bits
            base1 = (partial * 2 + 1) * stat_bits
            if producer_coupled:
                stat_assigns.append(
                    f"          producer_stat_fragments[{base0} +: {stat_bits}] <= {counter_expr(stat_bits, partial + 1)};"
                )
                stat_assigns.append(
                    f"          producer_stat_fragments[{base1} +: {stat_bits}] <= {counter_expr(stat_bits, partial + 33)};"
                )
            else:
                stat_assigns.append(
                    f"  assign stat_fragments[{base0} +: {stat_bits}] = {counter_expr(stat_bits, partial + 1)};"
                )
                stat_assigns.append(
                    f"  assign stat_fragments[{base1} +: {stat_bits}] = {counter_expr(stat_bits, partial + 33)};"
                )

        if producer_coupled:
            producer_body = f"""
  wire partial_valid;
  wire partial_ready;
  wire reduced_ready;
  wire [VALUE_WIDTH-1:0] value_fragments;
  wire [STAT_WIDTH-1:0] stat_fragments;
  reg [VALUE_WIDTH-1:0] producer_value_fragments;
  reg [STAT_WIDTH-1:0] producer_stat_fragments;
  reg producer_valid;
  reg [COUNT_W-1:0] source_step;

  assign partial_valid = producer_valid;
  assign value_fragments = producer_value_fragments;
  assign stat_fragments = producer_stat_fragments;
  assign reduced_ready = 1'b1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      source_step <= {{COUNT_W{{1'b0}}}};
      producer_valid <= 1'b0;
      producer_value_fragments <= {{VALUE_WIDTH{{1'b0}}}};
      producer_stat_fragments <= {{STAT_WIDTH{{1'b0}}}};
    end else if (!producer_valid || partial_ready) begin
{chr(10).join(value_assigns)}
{chr(10).join(stat_assigns)}
      producer_valid <= 1'b1;
      source_step <= source_step + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
    end
  end
"""
        else:
            producer_body = f"""
  wire partial_valid;
  wire partial_ready;
  wire reduced_ready;
  wire [VALUE_WIDTH-1:0] value_fragments;
  wire [STAT_WIDTH-1:0] stat_fragments;
  reg [COUNT_W-1:0] source_step;

  assign partial_valid = 1'b1;
  assign reduced_ready = 1'b1;
{chr(10).join(value_assigns)}
{chr(10).join(stat_assigns)}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      source_step <= {{COUNT_W{{1'b0}}}};
    end else if (partial_ready) begin
      source_step <= source_step + {{{{(COUNT_W-1){{1'b0}}}}, 1'b1}};
    end
  end
"""

        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  output reduced_valid,
  output {signed_kw}[{reduced_value_width-1}:0] reduced_value_fragment,
  output [{reduced_stat_width-1}:0] reduced_stat_fragment,
  output [{counter_bits-1}:0] accepted_chunk_count,
  output [{counter_bits-1}:0] completed_group_count,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{counter_bits-1}:0] cycle_count,
  output [{counter_bits-1}:0] final_completion_cycle
);

  localparam integer LANES = {lanes};
  localparam integer VALUE_W = {value_bits};
  localparam integer STAT_W = {stat_bits};
  localparam integer ACCUM_W = {accum_bits};
  localparam integer PARTIALS = {partials};
  localparam integer PARTIALS_PER_CYCLE = {partials_per_cycle};
  localparam integer VALUE_WIDTH = {value_width};
  localparam integer STAT_WIDTH = {stat_width};
  localparam integer COUNT_W = {counter_bits};
{producer_body}

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .partial_valid(partial_valid),
    .partial_ready(partial_ready),
    .value_fragments(value_fragments),
    .stat_fragments(stat_fragments),
    .reduced_valid(reduced_valid),
    .reduced_ready(reduced_ready),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .accepted_chunk_count(accepted_chunk_count),
    .completed_group_count(completed_group_count),
    .producer_stall_cycles(producer_stall_cycles),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] in ("attention_kv_tile_reducer_folded", "attention_kv_full_value_tile"):
        reduced_value_width = int(design["reduced_value_width"])
        reduced_stat_width = int(design["reduced_stat_width"])
        counter_bits = int(design["counter_bits"])
        wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  output reduced_valid,
  output signed [{reduced_value_width-1}:0] reduced_value_fragment,
  output [{reduced_stat_width-1}:0] reduced_stat_fragment,
  output [{counter_bits-1}:0] tile_accepted_count,
  output [{counter_bits-1}:0] tile_byte_count,
  output [{counter_bits-1}:0] tile_stall_cycles,
  output [{counter_bits-1}:0] reducer_accepted_chunk_count,
  output [{counter_bits-1}:0] reducer_completed_group_count,
  output [{counter_bits-1}:0] reducer_stall_cycles,
  output [{counter_bits-1}:0] final_completion_cycle
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .reduced_valid(reduced_valid),
    .reduced_value_fragment(reduced_value_fragment),
    .reduced_stat_fragment(reduced_stat_fragment),
    .tile_accepted_count(tile_accepted_count),
    .tile_byte_count(tile_byte_count),
    .tile_stall_cycles(tile_stall_cycles),
    .reducer_accepted_chunk_count(reducer_accepted_chunk_count),
    .reducer_completed_group_count(reducer_completed_group_count),
    .reducer_stall_cycles(reducer_stall_cycles),
    .final_completion_cycle(final_completion_cycle)
  );

endmodule
"""
    elif design["kind"] == "l1_memory_noc_primitive":
        flit_bits = int(design["flit_bits"])
        counter_bits = int(design["counter_bits"])
        if design["primitive"] == "fifo":
            wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  output [{counter_bits-1}:0] accepted_flit_count,
  output [{counter_bits-1}:0] emitted_flit_count,
  output [{counter_bits-1}:0] max_occupancy,
  output [{counter_bits-1}:0] producer_stall_cycles,
  output [{flit_bits-1}:0] observed_flit
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .accepted_flit_count(accepted_flit_count),
    .emitted_flit_count(emitted_flit_count),
    .max_occupancy(max_occupancy),
    .producer_stall_cycles(producer_stall_cycles),
    .observed_flit(observed_flit)
  );

endmodule
"""
        else:
            wrapper_content = f"""
module {wrapper_name}(
  input clk,
  input rst_n,
  output [{counter_bits-1}:0] routed_flit_count,
  output [{counter_bits-1}:0] arbitration_cycle_count,
  output [{flit_bits-1}:0] observed_flit
);

  {module_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .routed_flit_count(routed_flit_count),
    .arbitration_cycle_count(arbitration_cycle_count),
    .observed_flit(observed_flit)
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
        content += "export PLACE_PINS_ARGS ?= -min_distance 1\n"
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
