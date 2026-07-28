#!/usr/bin/env python3
"""Strict generated RTL guard for the structural GQA8 local16-to-global exact wrapper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local16_global_tree_gqa8_service_manifest,
)

_CONFIG_KEY = "attention_score32_exact_local16_global_tree_gqa8"


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


def _extract_module(rtl: str, module_name: str) -> str:
    pattern = re.compile(rf"module\s+{re.escape(module_name)}\b.*?endmodule\s*", re.DOTALL)
    match = pattern.search(rtl)
    if match is None:
        raise SystemExit(f"generated RTL does not define module {module_name}")
    return match.group(0)


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_local16_global_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_local16_global_tree_gqa8_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {relative_name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_local16_global_tree_gqa8_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing local16-global exact tree artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    clusters = int(body.get("clusters", 0))
    cluster_producers = tuple(int(value) for value in body.get("cluster_producers", []))
    radix = int(body.get("radix", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    persistent_waves = int(body.get("persistent_waves", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))

    if clusters != 16:
        raise SystemExit("clusters must remain fixed at 16")
    if len(cluster_producers) != 16:
        raise SystemExit("cluster_producers must contain exactly 16 entries")
    if cluster_producers.count(54) != 8 or cluster_producers.count(53) != 8:
        raise SystemExit("cluster_producers must contain exactly eight 54s and eight 53s")
    if radix != 2:
        raise SystemExit("radix must remain fixed at 2")
    if value_slices != 16:
        raise SystemExit("value_slices must remain fixed at 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain fixed at 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    if divider_lanes != 8 or finalizer_banks != 59:
        raise SystemExit("wrapper must remain on the c16/r2/l8/b59 finalized tree")

    probe_defaults = config.get("probe_defaults", {})
    resolved_group_count = 1
    if isinstance(probe_defaults, dict):
        head_bases = probe_defaults.get("head_bases")
        if isinstance(head_bases, list) and head_bases:
            resolved_group_count = len(head_bases)
        else:
            resolved_group_count = max(1, int(probe_defaults.get("heads", 8)) // 8)
    service_model = exact_local16_global_tree_gqa8_service_manifest(
        cluster_producers=cluster_producers,
        head_groups=resolved_group_count,
    )

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local16_global_tree_gqa8.py",
        "semantic_profile": "score32_exact_local16_global_tree_gqa8_v1",
        "clusters": 16,
        "cluster_producers": list(cluster_producers),
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": 856,
        "radix": 2,
        "value_slices": 16,
        "head_id_bits": 5,
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "result_interface": "packed_856_leaf_exact_partial_inputs_to_c16_ordered_banked_exact_finalized_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "command_schedule_contract": "group_major_gqa8_exact_8_wave_local_aggregation_preserved_across_all_16_clusters",
        "head_mapping_contract": "flat_leaf_indices_partitioned_by_cluster_leaf_base_indices_without_head_metadata_remap",
        "equivalence_hash": False,
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "remaining_abstractions": service_model["remaining_abstractions"],
        "service_model": service_model,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    if isinstance(config.get("probe_defaults"), dict):
        _require(manifest, "checked_in_probe_defaults", config["probe_defaults"], "generated manifest")
    if isinstance(config.get("report_links"), dict):
        proposal_id = str(config["report_links"].get("proposal_id") or "").strip()
        proposal_path = str(config["report_links"].get("proposal_path") or "").strip()
        if proposal_id:
            _require(manifest, "linked_proposal_id", proposal_id, "generated manifest")
        if proposal_path:
            _require(manifest, "linked_proposal_path", proposal_path, "generated manifest")

    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    reducer54_manifest = submodule_manifests.get("local_temporal_reducer_p54")
    reducer53_manifest = submodule_manifests.get("local_temporal_reducer_p53")
    banked_tree_manifest = submodule_manifests.get("banked_tree")
    if not isinstance(reducer54_manifest, dict) or not isinstance(reducer53_manifest, dict) or not isinstance(banked_tree_manifest, dict):
        raise SystemExit("generated manifest must contain p54, p53, and banked_tree submodule manifests")
    _require(submodule_manifests, "cluster_instance_counts", {"p54": 8, "p53": 8}, "generated manifest")
    _require(reducer54_manifest, "producers", 54, "p54 reducer manifest")
    _require(reducer53_manifest, "producers", 53, "p53 reducer manifest")
    _require(reducer54_manifest, "persistent_waves", 8, "p54 reducer manifest")
    _require(reducer53_manifest, "persistent_waves", 8, "p53 reducer manifest")
    _require(banked_tree_manifest, "clusters", 16, "banked-tree manifest")
    _require(banked_tree_manifest, "divider_lanes", 8, "banked-tree manifest")
    _require(banked_tree_manifest, "finalizer_banks", 59, "banked-tree manifest")
    _require(banked_tree_manifest, "actual_finalizer_accept_interval_cycles", 59, "banked-tree manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    reducer54_top_name = f"{top_name}__local_temporal_p54"
    reducer53_top_name = f"{top_name}__local_temporal_p53"
    banked_tree_top_name = f"{top_name}__global_tree"
    top_module = _extract_module(rtl, top_name)
    _extract_module(rtl, reducer54_top_name)
    _extract_module(rtl, reducer53_top_name)
    _extract_module(rtl, banked_tree_top_name)

    if len(re.findall(rf"\bmodule\s+{re.escape(reducer54_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one p54 local reducer module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(reducer53_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one p53 local reducer module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(banked_tree_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one banked-tree module definition")
    if len(re.findall(rf"\b{re.escape(reducer54_top_name)}\s+u_cluster_\d+\b", top_module)) != 8:
        raise SystemExit("generated RTL must instantiate the p54 local reducer exactly eight times")
    if len(re.findall(rf"\b{re.escape(reducer53_top_name)}\s+u_cluster_\d+\b", top_module)) != 8:
        raise SystemExit("generated RTL must instantiate the p53 local reducer exactly eight times")
    if top_module.count(f"{banked_tree_top_name} u_global_tree") != 1:
        raise SystemExit("generated RTL must instantiate the banked finalized tree exactly once")

    for token in (
        "input  wire [855:0] leaf_valid,",
        "output wire [855:0] leaf_ready,",
        "input  wire [13695:0] leaf_command_id,",
        "input  wire [4279:0] leaf_head_id,",
        "input  wire [27391:0] leaf_global_max,",
        "input  wire [28247:0] leaf_exp_sum,",
        "input  wire [3423:0] leaf_slice,",
        "input  wire [280767:0] leaf_value,",
        ".leaf_valid(leaf_valid[0 +: 54])",
        ".leaf_valid(leaf_valid[803 +: 53])",
        ".leaf_command_id(leaf_command_id[0 +: 864])",
        ".leaf_command_id(leaf_command_id[12848 +: 848])",
        ".leaf_head_id(leaf_head_id[0 +: 270])",
        ".leaf_head_id(leaf_head_id[4015 +: 265])",
        ".leaf_value(leaf_value[0 +: 17712])",
        ".leaf_value(leaf_value[263384 +: 17384])",
        ".leaf_valid(cluster_out_valid_w)",
        ".leaf_ready(cluster_out_ready_w)",
        ".leaf_command_id(cluster_out_command_id_w)",
        ".leaf_head_id(cluster_out_head_id_w)",
        ".leaf_global_max(cluster_out_global_max_w)",
        ".leaf_exp_sum(cluster_out_exp_sum_w)",
        ".leaf_slice(cluster_out_slice_w)",
        ".leaf_last(cluster_out_last_w)",
        ".leaf_value(cluster_out_value_w)",
        "assign protocol_error = (|cluster_protocol_error) || global_protocol_error;",
    ):
        _require_token(top_module, token, "generated RTL")

    for forbidden_token in (
        "producer_value_read_req",
        "producer_input_a",
        "producer_input_b",
        "value_response_matrix",
        "command_valid",
        "command_ready",
    ):
        if forbidden_token in top_module:
            raise SystemExit(f"functional wrapper top must not contain producer-coupled token: {forbidden_token}")

    if "equivalence_hash" in rtl:
        raise SystemExit("functional datapath must not contain equivalence_hash tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "clusters": 16,
                "total_local_producers": 856,
                "divider_lanes": 8,
                "finalizer_banks": 59,
                "status": "ok",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
