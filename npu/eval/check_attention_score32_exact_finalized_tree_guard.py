#!/usr/bin/env python3
"""Strict generated RTL guard for composed score32 exact finalized trees."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_finalized_tree import generate
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
)


_SUPPORTED_CLUSTERS = {2, 4, 8, 16}
_SUPPORTED_LANES = {1, 2, 4, 8}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_selected_config(*, design_dir: Path, selected: Path | None) -> Path:
    config_path = selected or (design_dir / "config.json")
    config_path = config_path.resolve()
    if not config_path.exists():
        raise SystemExit(f"missing config: {config_path}")
    try:
        relative_path = config_path.relative_to(design_dir)
    except ValueError as exc:
        raise SystemExit(f"selected config must live under design-dir: {config_path}") from exc
    if len(relative_path.parts) != 1:
        raise SystemExit(f"selected config must be a direct child of design-dir, got: {relative_path.as_posix()}")
    return config_path


def _require(mapping: dict[str, object], key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def _require_token(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"{label} missing semantic token: {token}")


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _extract_module(rtl: str, module_name: str) -> str:
    pattern = re.compile(rf"module\s+{re.escape(module_name)}\b.*?endmodule\s*", re.DOTALL)
    match = pattern.search(rtl)
    if match is None:
        raise SystemExit(f"generated RTL does not define module {module_name}")
    return match.group(0)


def _strip_comments(text: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", no_block)


def _contains_operator_division(text: str) -> bool:
    stripped = _strip_comments(text)
    return re.search(r"(?<![*/])/(?![/*])", stripped) is not None


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_finalized_tree_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_finalized_tree_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {relative_name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_finalized_tree_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact finalized tree artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_finalized_tree")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_finalized_tree object")
    clusters = int(body.get("clusters", 0))
    radix = int(body.get("radix", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    if clusters not in _SUPPORTED_CLUSTERS:
        raise SystemExit("clusters must be one of 2, 4, 8, 16")
    if clusters & (clusters - 1):
        raise SystemExit("clusters must be a power of two")
    if radix != 2:
        raise SystemExit("radix must be 2 for the current exact finalized tree")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes not in _SUPPORTED_LANES:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, 8")

    tree_nodes = clusters - 1
    tree_stages = int(math.log2(clusters))
    slice_bits = _clog2(value_slices)
    tree_top_name = f"{top_name}__partial_tree"
    finalizer_top_name = f"{top_name}__root_finalizer"
    pair_top_name = f"{tree_top_name}__pair_node"

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_finalized_tree.py",
        "semantic_profile": "score32_online_exact_finalized_radix2_tree_v1",
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "tree_stages": tree_stages,
        "tree_nodes": tree_nodes,
        "result_interface": "clusters_ready_valid_exact_partial_leaf_streams_to_exact_finalized_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "equivalence_hash": False,
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": True,
        "macro_eval_excludes_io_pads": True,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    submanifests = manifest.get("submodule_manifests")
    if not isinstance(submanifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    tree_manifest = submanifests.get("partial_tree")
    if not isinstance(tree_manifest, dict):
        raise SystemExit("generated manifest must contain partial_tree submodule manifest")
    finalizer_manifest = submanifests.get("root_finalizer")
    if not isinstance(finalizer_manifest, dict):
        raise SystemExit("generated manifest must contain root_finalizer submodule manifest")

    expected_tree_manifest = {
        "top_name": tree_top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
        "semantic_profile": "score32_online_exact_partial_radix2_tree_v1",
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "tree_stages": tree_stages,
        "tree_nodes": tree_nodes,
        "result_interface": "clusters_ready_valid_exact_partial_leaf_streams_to_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": False,
        "macro_eval_excludes_io_pads": True,
    }
    for key, expected in expected_tree_manifest.items():
        _require(tree_manifest, key, expected, "partial-tree submodule manifest")

    pair_manifest = tree_manifest.get("submodule_manifests")
    if not isinstance(pair_manifest, dict):
        raise SystemExit("partial-tree submodule manifest must contain submodule_manifests")
    pair_merge_manifest = pair_manifest.get("pair_merge")
    if not isinstance(pair_merge_manifest, dict):
        raise SystemExit("partial-tree submodule manifest must contain pair_merge manifest")
    _require(
        pair_merge_manifest,
        "top_name",
        pair_top_name,
        "pair-merge submodule manifest",
    )
    _require(
        pair_merge_manifest,
        "generator",
        "npu/rtlgen/gen_attention_score32_online_state_merge.py",
        "pair-merge submodule manifest",
    )
    _require(
        pair_merge_manifest,
        "semantic_profile",
        "score32_online_exact_partial_pair_merge_v1",
        "pair-merge submodule manifest",
    )

    expected_finalizer_manifest = {
        "top_name": finalizer_top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
        "semantic_profile": "score32_online_exact_root_finalizer_iterdiv_v1",
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "physical_divider_lanes": divider_lanes,
        "divider_groups_per_beat": 8 // divider_lanes,
        "divider_iterations_per_group": 57,
        "divider_cycles_per_beat": (8 // divider_lanes) * 57,
        "input_value_bits_per_beat": 328,
        "output_value_bits_per_beat": 320,
        "result_interface": "ready_valid_exact_finalized_slice_stream",
        "protocol_error_conditions": ["last_semantics", "exp_sum_zero", "final_value_overflow"],
        "final_divider_embodied": True,
        "equivalence_hash": False,
    }
    for key, expected in expected_finalizer_manifest.items():
        _require(finalizer_manifest, key, expected, "root-finalizer submodule manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    tree_module = _extract_module(rtl, tree_top_name)
    finalizer_module = _extract_module(rtl, finalizer_top_name)
    top_module = _extract_module(rtl, top_name)
    top_module_body = top_module.split(");", 1)[1]

    for token in (
        f"input  wire [{clusters - 1}:0] leaf_valid,",
        f"output wire [{clusters - 1}:0] leaf_ready,",
        "output wire         root_valid,",
        "input  wire         root_ready,",
        "output wire [15:0]  root_command_id,",
        f"output wire [{head_id_bits - 1}:0] root_head_id,",
        f"output wire [{slice_bits - 1}:0] root_slice,",
        "output wire [319:0] root_value,",
        "output wire [31:0]  cycle_count,",
        "output wire [31:0]  root_completed_count,",
        "output wire [31:0]  finalizer_accepted_count,",
        "output wire [31:0]  tree_root_completed_count,",
        f"output wire [{tree_nodes * 32 - 1}:0] node_completed_count,",
        f"output wire [{tree_stages * 32 - 1}:0] stage_completed_count,",
        f"output wire [{tree_nodes - 1}:0] node_protocol_error,",
        f"output wire [{tree_stages - 1}:0] stage_protocol_error,",
        "output wire         tree_protocol_error,",
        "output wire         finalizer_protocol_error,",
        "output wire         protocol_error",
        "wire tree_root_valid;",
        "wire tree_root_ready;",
        "wire [15:0] tree_root_command_id;",
        f"wire [{head_id_bits - 1}:0] tree_root_head_id;",
        "wire signed [31:0] tree_root_global_max;",
        "wire [32:0] tree_root_exp_sum;",
        f"wire [{slice_bits - 1}:0] tree_root_slice;",
        "wire tree_root_last;",
        "wire [327:0] tree_root_value;",
        "wire [31:0] tree_cycle_count;",
        "wire [31:0] tree_root_completed_count_w;",
        "wire [31:0] finalizer_accepted_count_w;",
        "wire [31:0] finalizer_completed_count_w;",
        "wire [31:0] finalizer_cycle_count_w;",
        "assign cycle_count = finalizer_cycle_count_w;",
        "assign root_completed_count = finalizer_completed_count_w;",
        "assign finalizer_accepted_count = finalizer_accepted_count_w;",
        "assign tree_root_completed_count = tree_root_completed_count_w;",
        "assign protocol_error = tree_protocol_error | finalizer_protocol_error;",
        f"{tree_top_name} u_tree (",
        ".root_valid(tree_root_valid),",
        ".root_ready(tree_root_ready),",
        ".root_command_id(tree_root_command_id),",
        ".root_head_id(tree_root_head_id),",
        ".root_global_max(tree_root_global_max),",
        ".root_exp_sum(tree_root_exp_sum),",
        ".root_slice(tree_root_slice),",
        ".root_last(tree_root_last),",
        ".root_value(tree_root_value),",
        ".cycle_count(tree_cycle_count),",
        ".root_completed_count(tree_root_completed_count_w),",
        ".node_completed_count(node_completed_count),",
        ".stage_completed_count(stage_completed_count),",
        ".node_protocol_error(node_protocol_error),",
        ".stage_protocol_error(stage_protocol_error),",
        ".protocol_error(tree_protocol_error)",
        f"{finalizer_top_name} u_finalizer (",
        ".in_valid(tree_root_valid),",
        ".in_ready(tree_root_ready),",
        ".in_command_id(tree_root_command_id),",
        ".in_head_id(tree_root_head_id),",
        ".in_exp_sum(tree_root_exp_sum),",
        ".in_slice(tree_root_slice),",
        ".in_last(tree_root_last),",
        ".in_value(tree_root_value),",
        ".out_valid(root_valid),",
        ".out_ready(root_ready),",
        ".out_command_id(root_command_id),",
        ".out_head_id(root_head_id),",
        ".out_slice(root_slice),",
        ".out_last(root_last),",
        ".out_value(root_value),",
        ".accepted_count(finalizer_accepted_count_w),",
        ".completed_count(finalizer_completed_count_w),",
        ".cycle_count(finalizer_cycle_count_w),",
        ".protocol_error(finalizer_protocol_error)",
    ):
        _require_token(top_module, token, "generated RTL")

    if re.search(r"^\s*reg\b", top_module_body, re.MULTILINE):
        raise SystemExit("top module must not contain internal reg storage")
    if re.search(r"^\s*always\b", top_module_body, re.MULTILINE):
        raise SystemExit("top module must not contain sequential or combinational always blocks")

    instance_indices = {int(index) for index in re.findall(rf"\bu_node_(\d+)\b", tree_module)}
    if instance_indices != set(range(tree_nodes)):
        raise SystemExit("generated RTL must instantiate every pair node exactly once")
    if tree_module.count(f"{pair_top_name} u_node_") != tree_nodes:
        raise SystemExit("generated RTL pair-node instance count does not match tree_nodes")

    for token in (
        f"localparam integer CLUSTERS = {clusters};",
        f"localparam integer TREE_STAGES = {tree_stages};",
        f"localparam integer TREE_NODES = {tree_nodes};",
        f"localparam integer HEAD_ID_BITS = {head_id_bits};",
        f"localparam integer VALUE_SLICES = {value_slices};",
        f"localparam integer SLICE_BITS = {slice_bits};",
        f"localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};",
        "assign protocol_error = |node_protocol_error;",
        "wire node_valid_w [0:TREE_NODES-1];",
        "wire node_ready_w [0:TREE_NODES-1];",
        "wire [31:0] node_completed_count_w [0:TREE_NODES-1];",
        "wire node_protocol_error_w [0:TREE_NODES-1];",
    ):
        _require_token(tree_module, token, "generated RTL")

    for token in (
        f"localparam integer DIVIDER_LANES = {divider_lanes};",
        "localparam integer DIVIDE_ITERATIONS = 57;",
        "localparam integer DIVIDEND_BITS = 57;",
        "assign in_ready = (state_q == IDLE) && !out_valid_q;",
        "assign out_valid = out_valid_q;",
        "assign protocol_error = protocol_error_q;",
        "accepted_count <= accepted_count + 1'b1;",
        "completed_count <= completed_count + 1'b1;",
        "if (out_valid_q && out_ready) begin",
        "rounded_dividend =",
        "state_q <= DIVIDE;",
        "div_bit_count_q <= DIVIDE_ITERATIONS[5:0];",
    ):
        _require_token(finalizer_module, token, "generated finalizer RTL")
    if _contains_operator_division(finalizer_module):
        raise SystemExit("generated finalizer RTL must not contain combinational division operators")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_finalized_tree_v1",
                "clusters": clusters,
                "divider_lanes": divider_lanes,
                "tree_nodes": tree_nodes,
                "tree_stages": tree_stages,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
