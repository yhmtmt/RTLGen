#!/usr/bin/env python3
"""Generate a staged exact-partial local reducer with odd-leaf carry support."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    LEGACY_MONOLITHIC_LUT_EXACT,
    SEGMENTED_LUT_9X256_EXACT,
    generate as generate_merge,
)
from npu.rtlgen.gen_attention_score32_exact_partial_pair_merge_folded import (
    MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT,
    generate as generate_folded_merge,
)
from npu.sim.perf.attention_exact_partial import (
    FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_partial_staged_tree_service_manifest,
)

JsonDict = dict[str, Any]
_SUPPORTED_EXP_SCALE_IMPLS = {
    LEGACY_MONOLITHIC_LUT_EXACT,
    SEGMENTED_LUT_9X256_EXACT,
    FACTORED_H33_L64_MUL_EXACT,
}


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_exact_local_reducer")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_exact_local_reducer")

    producers = int(body.get("producers", 53))
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    pair_node_impl_explicit = "pair_node_impl" in body
    pair_node_impl = str(body.get("pair_node_impl", LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL)).strip()
    keep_hierarchy = bool(body.get("keep_hierarchy", False))
    if producers < 2 or producers > 64:
        raise SystemExit("producers must be in [2, 64]")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if exp_scale_impl not in _SUPPORTED_EXP_SCALE_IMPLS:
        supported = ", ".join(sorted(_SUPPORTED_EXP_SCALE_IMPLS))
        raise SystemExit(f"exp_scale_impl must be one of: {supported}")
    if pair_node_impl not in {
        LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
        FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    }:
        raise SystemExit(
            "pair_node_impl must be absent or one of "
            f"{LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL}, "
            f"{FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL}"
        )
    if (
        pair_node_impl == FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL
        and exp_scale_impl != FACTORED_H33_L64_MUL_EXACT
    ):
        raise SystemExit(
            "folded_sharedscale_mersenne_exact requires exp_scale_impl factored_h33_l64_mul_exact"
        )
    return {
        "top_name": top_name,
        "producers": producers,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "exp_scale_impl": exp_scale_impl,
        "pair_node_impl": pair_node_impl,
        "pair_node_impl_explicit": pair_node_impl_explicit,
        "keep_hierarchy": keep_hierarchy,
    }


def _tree_levels(producers: int) -> list[list[dict[str, Any]]]:
    levels: list[list[dict[str, Any]]] = []
    previous: list[tuple[str, int]] = [("leaf", index) for index in range(producers)]
    next_node_index = 0
    stage = 0
    while len(previous) > 1:
        level: list[dict[str, Any]] = []
        next_previous: list[tuple[str, int]] = []
        slot = 0
        while slot < len(previous):
            if slot + 1 >= len(previous):
                next_previous.append(previous[slot])
            else:
                level.append(
                    {
                        "stage": stage,
                        "slot": slot // 2,
                        "node_index": next_node_index,
                        "left": previous[slot],
                        "right": previous[slot + 1],
                    }
                )
                next_previous.append(("node", next_node_index))
                next_node_index += 1
            slot += 2
        levels.append(level)
        previous = next_previous
        stage += 1
    return levels


def _source_expr(source: tuple[str, int], *, field: str, head_id_bits: int, slice_bits: int) -> str:
    kind, index = source
    if kind == "leaf":
        if field == "valid":
            return f"leaf_valid[{index}]"
        if field == "ready":
            return f"leaf_ready[{index}]"
        if field == "command_id":
            return f"leaf_command_id[{index * 16} +: 16]"
        if field == "head_id":
            return f"leaf_head_id[{index * head_id_bits} +: HEAD_ID_BITS]"
        if field == "global_max":
            return f"leaf_global_max[{index * 32} +: 32]"
        if field == "exp_sum":
            return f"leaf_exp_sum[{index * 33} +: 33]"
        if field == "slice":
            return f"leaf_slice[{index * slice_bits} +: SLICE_BITS]"
        if field == "last":
            return f"leaf_last[{index}]"
        if field == "value":
            return f"leaf_value[{index * PARTIAL_PAYLOAD_BITS} +: PARTIAL_PAYLOAD_BITS]"
        raise AssertionError(field)
    if field == "valid":
        return f"node_valid_w[{index}]"
    if field == "ready":
        return f"node_ready_w[{index}]"
    if field == "command_id":
        return f"node_command_id_w[{index}]"
    if field == "head_id":
        return f"node_head_id_w[{index}]"
    if field == "global_max":
        return f"node_global_max_w[{index}]"
    if field == "exp_sum":
        return f"node_exp_sum_w[{index}]"
    if field == "slice":
        return f"node_slice_w[{index}]"
    if field == "last":
        return f"node_last_w[{index}]"
    if field == "value":
        return f"node_value_w[{index}]"
    raise AssertionError(field)


def _instance_block(*, pair_top_name: str, levels: list[list[dict[str, Any]]], head_id_bits: int, slice_bits: int) -> str:
    root_index = levels[-1][-1]["node_index"]
    blocks: list[str] = []
    for level in levels:
        for node in level:
            node_index = int(node["node_index"])
            out_ready = "root_ready" if node_index == root_index else f"node_ready_w[{node_index}]"
            blocks.append(
                f"""  {pair_top_name} u_node_{node_index} (
      .clk(clk),
      .rst_n(rst_n),
      .left_valid({_source_expr(node["left"], field="valid", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_ready({_source_expr(node["left"], field="ready", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_command_id({_source_expr(node["left"], field="command_id", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_head_id({_source_expr(node["left"], field="head_id", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_global_max({_source_expr(node["left"], field="global_max", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_exp_sum({_source_expr(node["left"], field="exp_sum", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_slice({_source_expr(node["left"], field="slice", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_last({_source_expr(node["left"], field="last", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_value({_source_expr(node["left"], field="value", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_valid({_source_expr(node["right"], field="valid", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_ready({_source_expr(node["right"], field="ready", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_command_id({_source_expr(node["right"], field="command_id", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_head_id({_source_expr(node["right"], field="head_id", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_global_max({_source_expr(node["right"], field="global_max", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_exp_sum({_source_expr(node["right"], field="exp_sum", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_slice({_source_expr(node["right"], field="slice", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_last({_source_expr(node["right"], field="last", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_value({_source_expr(node["right"], field="value", head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .out_valid(node_valid_w[{node_index}]),
      .out_ready({out_ready}),
      .out_command_id(node_command_id_w[{node_index}]),
      .out_head_id(node_head_id_w[{node_index}]),
      .out_global_max(node_global_max_w[{node_index}]),
      .out_exp_sum(node_exp_sum_w[{node_index}]),
      .out_slice(node_slice_w[{node_index}]),
      .out_last(node_last_w[{node_index}]),
      .out_value(node_value_w[{node_index}]),
      .completed_count(node_completed_count_w[{node_index}]),
      .cycle_count(node_cycle_count_w[{node_index}]),
      .protocol_error(node_protocol_error_w[{node_index}])
  );"""
            )
    return "\n\n".join(blocks)


def _stage_assigns(levels: list[list[dict[str, Any]]]) -> tuple[str, str]:
    stage_count_lines: list[str] = []
    stage_error_lines: list[str] = []
    for stage, level in enumerate(levels):
        if level:
            count_expr = " + ".join(f"node_completed_count_w[{int(node['node_index'])}]" for node in level)
            error_expr = " | ".join(f"node_protocol_error_w[{int(node['node_index'])}]" for node in level)
        else:
            count_expr = "32'd0"
            error_expr = "1'b0"
        stage_count_lines.append(f"  assign stage_completed_count[{stage * 32} +: 32] = {count_expr};")
        stage_error_lines.append(f"  assign stage_protocol_error[{stage}] = {error_expr};")
    return "\n".join(stage_count_lines), "\n".join(stage_error_lines)


def _node_assigns(node_count: int) -> tuple[str, str]:
    count_lines = [
        f"  assign node_completed_count[{index * 32} +: 32] = node_completed_count_w[{index}];"
        for index in range(node_count)
    ]
    error_lines = [
        f"  assign node_protocol_error[{index}] = node_protocol_error_w[{index}];"
        for index in range(node_count)
    ]
    return "\n".join(count_lines), "\n".join(error_lines)


def _top_pin_bits(*, producers: int, head_id_bits: int, stages: int, nodes: int, slice_bits: int) -> int:
    leaf_bits = producers * (1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS + 1)
    root_bits = 1 + 1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS
    monitor_bits = 32 + 32 + (nodes * 32) + (stages * 32) + max(1, nodes) + max(1, stages) + 1
    return 2 + leaf_bits + root_bits + monitor_bits


def _top(*, top_name: str, pair_top_name: str, producers: int, value_slices: int, head_id_bits: int) -> str:
    slice_bits = _clog2(value_slices)
    levels = _tree_levels(producers)
    node_count = producers - 1
    stage_count = len(levels)
    root_index = levels[-1][-1]["node_index"]
    node_count_assigns, node_error_assigns = _node_assigns(node_count)
    stage_count_assigns, stage_error_assigns = _stage_assigns(levels)
    instances = _instance_block(
        pair_top_name=pair_top_name,
        levels=levels,
        head_id_bits=head_id_bits,
        slice_bits=slice_bits,
    )
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_local_reducer.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{producers - 1}:0] leaf_valid,
    output wire [{producers - 1}:0] leaf_ready,
    input  wire [{producers * 16 - 1}:0] leaf_command_id,
    input  wire [{producers * head_id_bits - 1}:0] leaf_head_id,
    input  wire [{producers * 32 - 1}:0] leaf_global_max,
    input  wire [{producers * 33 - 1}:0] leaf_exp_sum,
    input  wire [{producers * slice_bits - 1}:0] leaf_slice,
    input  wire [{producers - 1}:0] leaf_last,
    input  wire [{producers * PARTIAL_PAYLOAD_BITS - 1}:0] leaf_value,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [15:0]  root_command_id,
    output wire [{head_id_bits - 1}:0] root_head_id,
    output wire signed [31:0] root_global_max,
    output wire [32:0]  root_exp_sum,
    output wire [{slice_bits - 1}:0] root_slice,
    output wire         root_last,
    output wire [327:0] root_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  root_completed_count,
    output wire [{node_count * 32 - 1}:0] node_completed_count,
    output wire [{stage_count * 32 - 1}:0] stage_completed_count,
    output wire [{node_count - 1}:0] node_protocol_error,
    output wire [{stage_count - 1}:0] stage_protocol_error,
    output wire         protocol_error
);
  localparam integer PRODUCERS = {producers};
  localparam integer TREE_STAGES = {stage_count};
  localparam integer TREE_NODES = {node_count};
  localparam integer HEAD_ID_BITS = {head_id_bits};
  localparam integer VALUE_SLICES = {value_slices};
  localparam integer SLICE_BITS = {slice_bits};
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};

  wire node_valid_w [0:TREE_NODES-1];
  wire node_ready_w [0:TREE_NODES-1];
  wire [15:0] node_command_id_w [0:TREE_NODES-1];
  wire [HEAD_ID_BITS-1:0] node_head_id_w [0:TREE_NODES-1];
  wire signed [31:0] node_global_max_w [0:TREE_NODES-1];
  wire [32:0] node_exp_sum_w [0:TREE_NODES-1];
  wire [SLICE_BITS-1:0] node_slice_w [0:TREE_NODES-1];
  wire node_last_w [0:TREE_NODES-1];
  wire [PARTIAL_PAYLOAD_BITS-1:0] node_value_w [0:TREE_NODES-1];
  wire [31:0] node_completed_count_w [0:TREE_NODES-1];
  wire [31:0] node_cycle_count_w [0:TREE_NODES-1];
  wire node_protocol_error_w [0:TREE_NODES-1];

  assign root_valid = node_valid_w[{root_index}];
  assign root_command_id = node_command_id_w[{root_index}];
  assign root_head_id = node_head_id_w[{root_index}];
  assign root_global_max = node_global_max_w[{root_index}];
  assign root_exp_sum = node_exp_sum_w[{root_index}];
  assign root_slice = node_slice_w[{root_index}];
  assign root_last = node_last_w[{root_index}];
  assign root_value = node_value_w[{root_index}];
  assign root_completed_count = node_completed_count_w[{root_index}];
  assign cycle_count = node_cycle_count_w[{root_index}];
  assign protocol_error = |node_protocol_error;

{node_count_assigns}
{node_error_assigns}
{stage_count_assigns}
{stage_error_assigns}

{instances}
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    out_dir.mkdir(parents=True, exist_ok=True)

    pair_top_name = f"{params['top_name']}__pair_node"
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_reducer_pair_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        if params["pair_node_impl"] == LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL:
            generate_merge(
                {
                    "top_name": pair_top_name,
                    "attention_score32_online_state_merge": {
                        "value_slices": int(params["value_slices"]),
                        "head_id_bits": int(params["head_id_bits"]),
                        "exp_scale_impl": str(params["exp_scale_impl"]),
                        "keep_hierarchy": bool(params["keep_hierarchy"]),
                    },
                },
                temp_dir,
            )
            pair_manifest_name = "attention_score32_online_state_merge_manifest.json"
        else:
            generate_folded_merge(
                {
                    "top_name": pair_top_name,
                    "attention_score32_exact_partial_pair_merge_folded": {
                        "value_slices": int(params["value_slices"]),
                        "head_id_bits": int(params["head_id_bits"]),
                        "exp_scale_impl": str(params["exp_scale_impl"]),
                        "scale_divider_impl": MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT,
                        "lane_parallelism": 1,
                        "keep_hierarchy": bool(params["keep_hierarchy"]),
                    },
                },
                temp_dir,
            )
            pair_manifest_name = "attention_score32_exact_partial_pair_merge_folded_manifest.json"
        pair_rtl = (temp_dir / "top.v").read_text(encoding="utf-8")
        pair_manifest = json.loads((temp_dir / pair_manifest_name).read_text(encoding="utf-8"))

    top_text = _top(
        top_name=str(params["top_name"]),
        pair_top_name=pair_top_name,
        producers=int(params["producers"]),
        value_slices=int(params["value_slices"]),
        head_id_bits=int(params["head_id_bits"]),
    )
    (out_dir / "top.v").write_text(pair_rtl + "\n\n" + top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    service_model = exact_partial_staged_tree_service_manifest(
        producers=int(params["producers"]),
        heads=32,
        pair_node_impl=str(params["pair_node_impl"]),
    )
    node_count = int(params["producers"]) - 1
    stage_count = len(_tree_levels(int(params["producers"])))
    manifest = {
        "version": 1,
        "top_name": params["top_name"],
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_reducer.py",
        "semantic_profile": "score32_online_exact_partial_staged_local_reducer_v1",
        "producers": int(params["producers"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "exp_scale_impl": str(params["exp_scale_impl"]),
        "keep_hierarchy": bool(params["keep_hierarchy"]),
        "tree_stages": stage_count,
        "tree_nodes": node_count,
        "result_interface": "arbitrary_count_ready_valid_exact_partial_leaf_streams_to_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": False,
        "top_pin_bits": _top_pin_bits(
            producers=int(params["producers"]),
            head_id_bits=int(params["head_id_bits"]),
            stages=stage_count,
            nodes=node_count,
            slice_bits=_clog2(int(params["value_slices"])),
        ),
        "service_model": service_model,
        "submodule_manifests": {"pair_merge": pair_manifest},
    }
    if bool(params["pair_node_impl_explicit"]):
        manifest["pair_node_impl"] = str(params["pair_node_impl"])
    if params["pair_node_impl"] == FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL:
        manifest.update(
            {
                "pair_node_scale_divider_impl": pair_manifest["scale_divider_impl"],
                "pair_capture_to_output_latency_cycles": pair_manifest["pair_capture_to_output_latency_cycles"],
                "pair_compute_launch_to_output_latency_cycles": (
                    pair_manifest["pair_compute_launch_to_output_latency_cycles"]
                ),
                "pair_compute_launch_interval_cycles": pair_manifest["pair_compute_launch_interval_cycles"],
            }
        )
    (out_dir / "attention_score32_exact_local_reducer_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
