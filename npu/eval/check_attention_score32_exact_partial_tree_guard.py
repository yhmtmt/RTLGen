#!/usr/bin/env python3
"""Strict generated RTL guard for standalone score32 exact partial trees."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_tree import generate
from npu.rtlgen.gen_attention_score32_online_state_merge import LEGACY_MONOLITHIC_LUT_EXACT
from npu.sim.perf.attention_exact_partial import PARTIAL_LINK_BITS, PARTIAL_PAYLOAD_BITS


_SUPPORTED_CLUSTERS = {2, 4, 8, 16}


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
        raise SystemExit(f"generated RTL does not define top module {module_name}")
    return match.group(0)


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_tree_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_partial_tree_manifest.json",
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
    manifest_path = rtl_dir / "attention_score32_exact_partial_tree_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact partial tree artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_partial_tree")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_partial_tree object")
    clusters = int(body.get("clusters", 0))
    radix = int(body.get("radix", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    if clusters not in _SUPPORTED_CLUSTERS:
        raise SystemExit("clusters must be one of 2, 4, 8, 16")
    if clusters & (clusters - 1):
        raise SystemExit("clusters must be a power of two")
    if radix != 2:
        raise SystemExit("radix must be 2 for the current exact partial tree")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")

    tree_nodes = clusters - 1
    tree_stages = int(math.log2(clusters))
    slice_bits = _clog2(value_slices)
    root_index = tree_nodes - 1
    pair_top_name = f"{top_name}__pair_node"

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
        "semantic_profile": "score32_online_exact_partial_radix2_tree_v1",
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "exp_scale_impl": exp_scale_impl,
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
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    pair_manifest = manifest.get("submodule_manifests")
    if not isinstance(pair_manifest, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    pair_merge_manifest = pair_manifest.get("pair_merge")
    if not isinstance(pair_merge_manifest, dict):
        raise SystemExit("generated manifest must contain pair_merge submodule manifest")
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
    _require(
        pair_merge_manifest,
        "exp_scale_impl",
        exp_scale_impl,
        "pair-merge submodule manifest",
    )

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    top_module = _extract_module(rtl, top_name)
    top_module_body = top_module.split(");", 1)[1]

    for token in (
        f"localparam integer CLUSTERS = {clusters};",
        f"localparam integer TREE_STAGES = {tree_stages};",
        f"localparam integer TREE_NODES = {tree_nodes};",
        f"localparam integer HEAD_ID_BITS = {head_id_bits};",
        f"localparam integer VALUE_SLICES = {value_slices};",
        f"localparam integer SLICE_BITS = {slice_bits};",
        f"localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};",
        f"assign root_valid = node_valid_w[{root_index}];",
        f"assign root_command_id = node_command_id_w[{root_index}];",
        f"assign root_head_id = node_head_id_w[{root_index}];",
        f"assign root_global_max = node_global_max_w[{root_index}];",
        f"assign root_exp_sum = node_exp_sum_w[{root_index}];",
        f"assign root_slice = node_slice_w[{root_index}];",
        f"assign root_last = node_last_w[{root_index}];",
        f"assign root_value = node_value_w[{root_index}];",
        f"assign root_completed_count = node_completed_count_w[{root_index}];",
        f"assign cycle_count = node_cycle_count_w[{root_index}];",
        "assign protocol_error = |node_protocol_error;",
        "wire node_valid_w [0:TREE_NODES-1];",
        "wire node_ready_w [0:TREE_NODES-1];",
        "wire [31:0] node_completed_count_w [0:TREE_NODES-1];",
        "wire node_protocol_error_w [0:TREE_NODES-1];",
    ):
        _require_token(top_module, token, "generated RTL")

    for token in (
        f"output wire [{tree_nodes * 32 - 1}:0] node_completed_count,",
        f"output wire [{tree_stages * 32 - 1}:0] stage_completed_count,",
        f"output wire [{tree_nodes - 1}:0] node_protocol_error,",
        f"output wire [{tree_stages - 1}:0] stage_protocol_error,",
        "output wire [31:0]  cycle_count,",
        "output wire [31:0]  root_completed_count,",
        "output wire         protocol_error",
    ):
        _require_token(top_module, token, "generated RTL")

    if re.search(r"^\s*reg\b", top_module_body, re.MULTILINE):
        raise SystemExit("top module must not contain internal reg storage")

    instance_indices = {int(index) for index in re.findall(rf"\bu_node_(\d+)\b", top_module)}
    if instance_indices != set(range(tree_nodes)):
        raise SystemExit("generated RTL must instantiate every pair node exactly once")
    if top_module.count(f"{pair_top_name} u_node_") != tree_nodes:
        raise SystemExit("generated RTL pair-node instance count does not match tree_nodes")

    _require_token(top_module, f".out_ready(root_ready)", "generated RTL")
    for node_index in range(tree_nodes):
        _require_token(top_module, f".out_valid(node_valid_w[{node_index}])", "generated RTL")
        _require_token(top_module, f".completed_count(node_completed_count_w[{node_index}])", "generated RTL")
        _require_token(top_module, f".protocol_error(node_protocol_error_w[{node_index}])", "generated RTL")
        if node_index == root_index:
            _require_token(top_module, f"{pair_top_name} u_node_{node_index} (", "generated RTL")
        else:
            _require_token(top_module, f".out_ready(node_ready_w[{node_index}])", "generated RTL")
        _require_token(
            top_module,
            f"assign node_completed_count[{node_index * 32} +: 32] = node_completed_count_w[{node_index}];",
            "generated RTL",
        )
        _require_token(
            top_module,
            f"assign node_protocol_error[{node_index}] = node_protocol_error_w[{node_index}];",
            "generated RTL",
        )
    for stage in range(tree_stages):
        _require_token(
            top_module,
            f"assign stage_completed_count[{stage * 32} +: 32] =",
            "generated RTL",
        )
        _require_token(
            top_module,
            f"assign stage_protocol_error[{stage}] =",
            "generated RTL",
        )

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_partial_tree_v1",
                "clusters": clusters,
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
