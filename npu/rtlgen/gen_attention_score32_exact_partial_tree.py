#!/usr/bin/env python3
"""Generate a radix-2 streamed exact-partial reduction tree for score32 online merge."""

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
    exact_partial_tree_service_manifest,
)

JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_exact_partial_tree")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_exact_partial_tree")

    clusters = int(body.get("clusters", 16))
    radix = int(body.get("radix", 2))
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    pair_node_impl_explicit = "pair_node_impl" in body
    pair_node_impl = str(body.get("pair_node_impl", LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL)).strip()
    if clusters < 2 or clusters > 16 or (clusters & (clusters - 1)):
        raise SystemExit("clusters must be a power of two in [2, 16]")
    if radix != 2:
        raise SystemExit("phase B only implements radix=2")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
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
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "exp_scale_impl": exp_scale_impl,
        "pair_node_impl": pair_node_impl,
        "pair_node_impl_explicit": pair_node_impl_explicit,
    }


def _tree_levels(clusters: int) -> list[list[dict[str, Any]]]:
    levels: list[list[dict[str, Any]]] = []
    previous: list[tuple[str, int]] = [("leaf", index) for index in range(clusters)]
    next_node_index = 0
    stage = 0
    while len(previous) > 1:
        level: list[dict[str, Any]] = []
        for slot in range(0, len(previous), 2):
            level.append(
                {
                    "stage": stage,
                    "slot": slot // 2,
                    "node_index": next_node_index,
                    "left": previous[slot],
                    "right": previous[slot + 1],
                }
            )
            next_node_index += 1
        levels.append(level)
        previous = [("node", node["node_index"]) for node in level]
        stage += 1
    return levels


def _top_pin_bits(*, clusters: int, head_id_bits: int, stages: int, nodes: int, slice_bits: int) -> int:
    leaf_bits = clusters * (1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS + 1)
    root_bits = 1 + 1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS
    monitor_bits = 32 + 32 + (nodes * 32) + (stages * 32) + nodes + stages + 1
    return 2 + leaf_bits + root_bits + monitor_bits


def _source_expr(source: tuple[str, int], *, field: str, width: int, head_id_bits: int, slice_bits: int) -> str:
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
    root_index = levels[-1][0]["node_index"]
    blocks: list[str] = []
    for level in levels:
        for node in level:
            node_index = int(node["node_index"])
            out_ready = "root_ready" if node_index == root_index else f"node_ready_w[{node_index}]"
            blocks.append(
                f"""  {pair_top_name} u_node_{node_index} (
      .clk(clk),
      .rst_n(rst_n),
      .left_valid({_source_expr(node["left"], field="valid", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_ready({_source_expr(node["left"], field="ready", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_command_id({_source_expr(node["left"], field="command_id", width=16, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_head_id({_source_expr(node["left"], field="head_id", width=head_id_bits, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_global_max({_source_expr(node["left"], field="global_max", width=32, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_exp_sum({_source_expr(node["left"], field="exp_sum", width=33, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_slice({_source_expr(node["left"], field="slice", width=slice_bits, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_last({_source_expr(node["left"], field="last", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .left_value({_source_expr(node["left"], field="value", width=PARTIAL_PAYLOAD_BITS, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_valid({_source_expr(node["right"], field="valid", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_ready({_source_expr(node["right"], field="ready", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_command_id({_source_expr(node["right"], field="command_id", width=16, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_head_id({_source_expr(node["right"], field="head_id", width=head_id_bits, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_global_max({_source_expr(node["right"], field="global_max", width=32, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_exp_sum({_source_expr(node["right"], field="exp_sum", width=33, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_slice({_source_expr(node["right"], field="slice", width=slice_bits, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_last({_source_expr(node["right"], field="last", width=1, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
      .right_value({_source_expr(node["right"], field="value", width=PARTIAL_PAYLOAD_BITS, head_id_bits=head_id_bits, slice_bits=slice_bits)}),
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
        indices = [int(node["node_index"]) for node in level]
        count_expr = " + ".join(f"node_completed_count_w[{index}]" for index in indices)
        error_expr = " | ".join(f"node_protocol_error_w[{index}]" for index in indices)
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


def _top(*, top_name: str, pair_top_name: str, clusters: int, value_slices: int, head_id_bits: int) -> str:
    slice_bits = _clog2(value_slices)
    levels = _tree_levels(clusters)
    node_count = clusters - 1
    stage_count = len(levels)
    root_index = levels[-1][0]["node_index"]
    node_count_assigns, node_error_assigns = _node_assigns(node_count)
    stage_count_assigns, stage_error_assigns = _stage_assigns(levels)
    instances = _instance_block(
        pair_top_name=pair_top_name,
        levels=levels,
        head_id_bits=head_id_bits,
        slice_bits=slice_bits,
    )
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_partial_tree.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{clusters - 1}:0] leaf_valid,
    output wire [{clusters - 1}:0] leaf_ready,
    input  wire [{clusters * 16 - 1}:0] leaf_command_id,
    input  wire [{clusters * head_id_bits - 1}:0] leaf_head_id,
    input  wire [{clusters * 32 - 1}:0] leaf_global_max,
    input  wire [{clusters * 33 - 1}:0] leaf_exp_sum,
    input  wire [{clusters * slice_bits - 1}:0] leaf_slice,
    input  wire [{clusters - 1}:0] leaf_last,
    input  wire [{clusters * PARTIAL_PAYLOAD_BITS - 1}:0] leaf_value,
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
  localparam integer CLUSTERS = {clusters};
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
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_tree_pair_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        if params["pair_node_impl"] == LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL:
            generate_merge(
                {
                    "top_name": pair_top_name,
                    "attention_score32_online_state_merge": {
                        "value_slices": int(params["value_slices"]),
                        "head_id_bits": int(params["head_id_bits"]),
                        "exp_scale_impl": str(params["exp_scale_impl"]),
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
        clusters=int(params["clusters"]),
        value_slices=int(params["value_slices"]),
        head_id_bits=int(params["head_id_bits"]),
    )
    (out_dir / "top.v").write_text(pair_rtl + "\n\n" + top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    theoretical_full_llama_service_manifest = exact_partial_tree_service_manifest(
        clusters=int(params["clusters"]),
        heads=32,
        pair_node_impl=str(params["pair_node_impl"]),
    )
    node_count = int(params["clusters"]) - 1
    stage_count = int(math.log2(int(params["clusters"])))
    manifest = {
        "version": 1,
        "top_name": params["top_name"],
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
        "semantic_profile": "score32_online_exact_partial_radix2_tree_v1",
        "clusters": int(params["clusters"]),
        "radix": int(params["radix"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "exp_scale_impl": str(params["exp_scale_impl"]),
        "tree_stages": stage_count,
        "tree_nodes": node_count,
        "result_interface": "clusters_ready_valid_exact_partial_leaf_streams_to_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": False,
        "macro_eval_excludes_io_pads": True,
        "top_pin_bits": _top_pin_bits(
            clusters=int(params["clusters"]),
            head_id_bits=int(params["head_id_bits"]),
            stages=stage_count,
            nodes=node_count,
            slice_bits=_clog2(int(params["value_slices"])),
        ),
        "theoretical_full_llama_service_manifest": theoretical_full_llama_service_manifest,
        "submodule_manifests": {"pair_merge": pair_manifest},
    }
    if bool(params["pair_node_impl_explicit"]):
        manifest["pair_node_impl"] = str(params["pair_node_impl"])
    (out_dir / "attention_score32_exact_partial_tree_manifest.json").write_text(
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
