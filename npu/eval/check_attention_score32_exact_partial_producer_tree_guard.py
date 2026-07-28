#!/usr/bin/env python3
"""Strict generated RTL guard for the first producer-coupled exact reduction slice."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree import generate
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_partial_producer_tree_service_manifest,
)


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
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_producer_tree_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_partial_producer_tree_manifest.json",
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
    manifest_path = rtl_dir / "attention_score32_exact_partial_producer_tree_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing producer-coupled exact tree artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_exact_partial_producer_tree")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config must contain top_name and attention_score32_exact_partial_producer_tree")

    producers = int(body.get("producers", 0))
    clusters = int(body.get("clusters", 0))
    radix = int(body.get("radix", 0))
    max_blocks = int(body.get("max_blocks", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))
    if producers != 2 or clusters != 2 or radix != 2:
        raise SystemExit("producer-coupled slice must remain fixed at producers=2, clusters=2, radix=2")
    if max_blocks < 8 or max_blocks > 16384 or (max_blocks & (max_blocks - 1)):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if value_slices != 16:
        raise SystemExit("value_slices must remain 16")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes != 8 or finalizer_banks != 59:
        raise SystemExit("producer-coupled slice must remain on the c2/r2/l8/b59 finalized tree")

    service_model = exact_partial_producer_tree_service_manifest(
        heads=int(config.get("probe_defaults", {}).get("heads", 32)) if isinstance(config.get("probe_defaults"), dict) else 32,
        max_blocks=max_blocks,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
    )
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_producer_tree.py",
        "semantic_profile": "score32_online_exact_partial_two_producer_coupled_banked_tree_v1",
        "producers": 2,
        "clusters": 2,
        "radix": 2,
        "max_blocks": max_blocks,
        "value_slices": 16,
        "head_id_bits": head_id_bits,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "producer_result_mode": "exact_partial",
        "command_schedule_contract": "in_order_head_commands_broadcast_to_both_producers",
        "head_mapping_contract": "explicit_head_id_no_tile_or_wave_inference",
        "result_interface": "two_exact_partial_producers_to_c2_ordered_banked_exact_finalized_tree",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "llama_tile_cadence_unclosed": True,
        "producer_block_workload_assumptions": service_model["producer_block_workload_assumptions"],
        "exact_protocols": {
            "producer_partial_protocol": service_model["producer_partial_protocol"],
            "finalized_protocol": service_model["finalized_protocol"],
        },
        "remaining_abstractions": service_model["remaining_abstractions"],
        "equivalence_hash": False,
        "service_model": service_model,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    if isinstance(config.get("probe_defaults"), dict):
        _require(manifest, "checked_in_probe_defaults", config["probe_defaults"], "generated manifest")

    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    producer_manifest = submodule_manifests.get("producer")
    banked_tree_manifest = submodule_manifests.get("banked_tree")
    if not isinstance(producer_manifest, dict) or not isinstance(banked_tree_manifest, dict):
        raise SystemExit("generated manifest must contain producer and banked_tree submodule manifests")
    _require(producer_manifest, "generator", "npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py", "producer submodule manifest")
    _require(producer_manifest, "result_mode", "exact_partial", "producer submodule manifest")
    _require(producer_manifest, "result_value_bits_per_beat", 328, "producer submodule manifest")
    _require(producer_manifest, "head_id_bits", head_id_bits, "producer submodule manifest")
    _require(banked_tree_manifest, "generator", "npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py", "banked-tree submodule manifest")
    _require(banked_tree_manifest, "clusters", 2, "banked-tree submodule manifest")
    _require(banked_tree_manifest, "divider_lanes", 8, "banked-tree submodule manifest")
    _require(banked_tree_manifest, "finalizer_banks", 59, "banked-tree submodule manifest")
    _require(banked_tree_manifest, "actual_finalizer_accept_interval_cycles", 59, "banked-tree submodule manifest")
    banked_service = banked_tree_manifest.get("service_model")
    if not isinstance(banked_service, dict):
        raise SystemExit("banked-tree submodule manifest must contain service_model")
    _require(banked_service, "divider_iterations_per_group", 57, "banked-tree service model")
    _require(banked_service, "per_bank_output_latency_cycles", 58, "banked-tree service model")
    _require(banked_service, "per_bank_accept_interval_cycles", 59, "banked-tree service model")
    _require(banked_service, "minimum_banks_for_wrap_free_lane8_service", 59, "banked-tree service model")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    producer_top_name = f"{top_name}__producer"
    banked_tree_top_name = f"{top_name}__banked_tree"
    top_module = _extract_module(rtl, top_name)
    _extract_module(rtl, producer_top_name)
    _extract_module(rtl, banked_tree_top_name)

    if len(re.findall(rf"\bmodule\s+{re.escape(producer_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one producer module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(banked_tree_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one banked-tree module definition")
    if top_module.count(f"{producer_top_name} u_producer_") != 2:
        raise SystemExit("generated RTL must instantiate the producer module exactly twice")
    if top_module.count(f"{banked_tree_top_name} u_banked_tree") != 1:
        raise SystemExit("generated RTL must instantiate the banked finalized tree exactly once")

    for token in (
        "wire producer_command_valid_w = command_valid && command_ready;",
        "assign command_ready = producer0_command_ready_w && producer1_command_ready_w;",
        "assign tree_leaf_valid_w[0] = producer0_result_valid_w;",
        "assign tree_leaf_valid_w[1] = producer1_result_valid_w;",
        "assign producer0_result_ready_w = tree_leaf_ready_w[0];",
        "assign producer1_result_ready_w = tree_leaf_ready_w[1];",
        "assign tree_leaf_command_id_w[0 +: 16] = producer0_result_command_id_w;",
        "assign tree_leaf_command_id_w[16 +: 16] = producer1_result_command_id_w;",
        f"assign tree_leaf_head_id_w[0 +: {head_id_bits}] = producer0_result_head_id_w;",
        f"assign tree_leaf_head_id_w[{head_id_bits} +: {head_id_bits}] = producer1_result_head_id_w;",
        "assign tree_leaf_global_max_w[0 +: 32] = producer0_result_global_max_w;",
        "assign tree_leaf_global_max_w[32 +: 32] = producer1_result_global_max_w;",
        "assign tree_leaf_exp_sum_w[0 +: 33] = producer0_result_exp_sum_w;",
        "assign tree_leaf_exp_sum_w[33 +: 33] = producer1_result_exp_sum_w;",
        "assign tree_leaf_slice_w[0 +: 4] = producer0_result_slice_w;",
        "assign tree_leaf_slice_w[4 +: 4] = producer1_result_slice_w;",
        "assign tree_leaf_last_w[0] = producer0_result_last_w;",
        "assign tree_leaf_last_w[1] = producer1_result_last_w;",
        "assign tree_leaf_value_w[0 +: PARTIAL_PAYLOAD_BITS] = producer0_result_value_w;",
        "assign tree_leaf_value_w[PARTIAL_PAYLOAD_BITS +: PARTIAL_PAYLOAD_BITS] = producer1_result_value_w;",
        "assign producer_partial_valid = {producer1_result_valid_w, producer0_result_valid_w};",
        "assign producer_partial_ready = {producer1_result_ready_w, producer0_result_ready_w};",
        "assign producer_partial_last = {producer1_result_last_w, producer0_result_last_w};",
        "command_accept_count_q <= command_accept_count_q + 1'b1;",
        "command_completed_count_q <= command_completed_count_q + 1'b1;",
        "producer0_leaf_stall_cycles_q <= producer0_leaf_stall_cycles_q + 1'b1;",
        "producer1_leaf_stall_cycles_q <= producer1_leaf_stall_cycles_q + 1'b1;",
    ):
        _require_token(top_module, token, "generated RTL")

    if "equivalence_hash" in rtl:
        raise SystemExit("functional datapath must not contain equivalence_hash tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_partial_producer_tree_v1",
                "producers": producers,
                "clusters": clusters,
                "divider_lanes": divider_lanes,
                "finalizer_banks": finalizer_banks,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
