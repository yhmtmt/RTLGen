#!/usr/bin/env python3
"""Strict generated RTL guard for the GQA8 local temporal reducer physical harness."""

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

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness import generate
from npu.rtlgen.gen_attention_score32_online_state_merge import LEGACY_MONOLITHIC_LUT_EXACT
from npu.sim.perf.attention_exact_partial import (
    FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
)

_CONFIG_KEY = "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"
_MANIFEST_NAME = "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"


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
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_temporal_gqa8_physical_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in ("top.v", "config.json", _MANIFEST_NAME):
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
    manifest_path = rtl_dir / _MANIFEST_NAME
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing physical harness artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    producers = int(body.get("producers", 0))
    mode = str(body.get("mode", "")).strip()
    waves = int(body.get("waves", 0))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    pair_node_impl_explicit = "pair_node_impl" in body
    pair_node_impl = str(body.get("pair_node_impl", LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL)).strip()
    keep_hierarchy = bool(body.get("keep_hierarchy", False))
    if producers not in {53, 54}:
        raise SystemExit("producers must remain exactly 53 or 54")
    if mode not in {"reducer", "source_only"}:
        raise SystemExit("mode must remain reducer or source_only")
    if waves != 8:
        raise SystemExit("waves must remain 8")
    if pair_node_impl not in {
        LEGACY_PARALLEL_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
        FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    }:
        raise SystemExit("pair_node_impl must be absent or a supported exact merge implementation")
    if mode == "source_only" and pair_node_impl_explicit:
        raise SystemExit("source_only mode must not specify pair_node_impl")

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local_temporal_reducer_gqa8_physical_harness_v1",
        "producers": producers,
        "mode": mode,
        "waves": 8,
        "exp_scale_impl": exp_scale_impl,
        "keep_hierarchy": keep_hierarchy,
        "command_count": 2,
        "query_heads_per_group": 8,
        "head_group_bases": [0, 8],
        "value_slices": 16,
        "head_id_bits": 5,
        "result_interface": "narrow_io_observable_structural_local_temporal_gqa8_harness",
        "equivalence_hash": False,
        "top_pin_bits": 776,
        "source_traffic_contract": "shared_state_atomic_batch_stable_ready_valid",
        "source_state_contract": "single_shared_held_lfsr_and_12bit_batch_counter",
        "source_batch_contract": "all_leaf_valids_atomic_advance_on_all_leaf_handshakes",
        "command_schedule_contract": "two_explicit_gqa8_head_groups_0_and_8_each_over_8_waves",
        "head_mapping_contract": "head_major_slice_minor_source_order_with_explicit_head_ids",
        "wave_terminal_contract": "advance_only_after_source_head_lane7_slice15_per_wave",
        "per_leaf_payload_state": False,
        "observable_contract": "done_plus_final_command_head_max_sum_slice_last_value_and_counters",
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json",
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    if pair_node_impl_explicit:
        _require(manifest, "pair_node_impl", pair_node_impl, "generated manifest")
    _require(
        manifest,
        "caveats",
        ["structural_only", "nonlinear_ppa_delta_vs_functional_reducer_measurement"],
        "generated manifest",
    )

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config must include report_links for evaluator artifact linkage")
    _require(links, "proposal_id", _PROPOSAL_ID, "report_links")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    gqa8_reducer_manifest = submodule_manifests.get("gqa8_reducer")
    if mode == "reducer":
        if not isinstance(gqa8_reducer_manifest, dict):
            raise SystemExit("reducer mode must include gqa8 reducer manifest")
        _require(
            gqa8_reducer_manifest,
            "generator",
            "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8.py",
            "gqa8 reducer submodule manifest",
        )
        _require(gqa8_reducer_manifest, "query_heads_per_group", 8, "gqa8 reducer submodule manifest")
        _require(gqa8_reducer_manifest, "exp_scale_impl", exp_scale_impl, "gqa8 reducer submodule manifest")
        _require(gqa8_reducer_manifest, "keep_hierarchy", keep_hierarchy, "gqa8 reducer submodule manifest")
        if pair_node_impl_explicit:
            _require(gqa8_reducer_manifest, "pair_node_impl", pair_node_impl, "gqa8 reducer submodule manifest")
        local_reducer_manifest = gqa8_reducer_manifest.get("submodule_manifests", {}).get("local_reducer")
        temporal_merge_manifest = gqa8_reducer_manifest.get("submodule_manifests", {}).get("temporal_merge")
        if not isinstance(local_reducer_manifest, dict):
            raise SystemExit("gqa8 reducer manifest must include local_reducer submodule manifest")
        if not isinstance(temporal_merge_manifest, dict):
            raise SystemExit("gqa8 reducer manifest must include temporal_merge submodule manifest")
        _require(local_reducer_manifest, "exp_scale_impl", exp_scale_impl, "local reducer submodule manifest")
        _require(local_reducer_manifest, "keep_hierarchy", keep_hierarchy, "local reducer submodule manifest")
        pair_manifest = local_reducer_manifest.get("submodule_manifests", {}).get("pair_merge")
        if not isinstance(pair_manifest, dict):
            raise SystemExit("local reducer manifest must include pair_merge submodule manifest")
        _require(pair_manifest, "exp_scale_impl", exp_scale_impl, "pair_merge submodule manifest")
        _require(pair_manifest, "keep_hierarchy", keep_hierarchy, "pair_merge submodule manifest")
        _require(temporal_merge_manifest, "exp_scale_impl", exp_scale_impl, "temporal_merge submodule manifest")
        _require(temporal_merge_manifest, "keep_hierarchy", keep_hierarchy, "temporal_merge submodule manifest")
        if pair_node_impl == FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL:
            _require(local_reducer_manifest, "pair_node_impl", pair_node_impl, "local reducer submodule manifest")
            _require(pair_manifest, "generator", "npu/rtlgen/gen_attention_score32_exact_partial_pair_merge_folded.py", "pair_merge submodule manifest")
            _require(pair_manifest, "scale_divider_impl", "mersenne24_correction2_exact", "pair_merge submodule manifest")
            _require(
                temporal_merge_manifest,
                "generator",
                "npu/rtlgen/gen_attention_score32_exact_partial_pair_merge_folded.py",
                "temporal_merge submodule manifest",
            )
            _require(
                temporal_merge_manifest,
                "scale_divider_impl",
                "mersenne24_correction2_exact",
                "temporal_merge submodule manifest",
            )
            _require(manifest, "pair_node_scale_divider_impl", "mersenne24_correction2_exact", "generated manifest")
            _require(
                manifest,
                "pair_capture_to_output_latency_cycles",
                gqa8_reducer_manifest["pair_capture_to_output_latency_cycles"],
                "generated manifest",
            )
            _require(
                manifest,
                "pair_compute_launch_to_output_latency_cycles",
                gqa8_reducer_manifest["pair_compute_launch_to_output_latency_cycles"],
                "generated manifest",
            )
            _require(
                manifest,
                "pair_compute_launch_interval_cycles",
                gqa8_reducer_manifest["pair_compute_launch_interval_cycles"],
                "generated manifest",
            )
        if keep_hierarchy:
            if rtl.count("(* keep_hierarchy = 1 *)") < 2:
                raise SystemExit("generated RTL must preserve both local pair and temporal merge hierarchy markers")
    elif gqa8_reducer_manifest is not None:
        raise SystemExit("source_only mode must not include gqa8 reducer manifest")

    top_module = _extract_module(rtl, top_name)
    _require_token(top_module, "localparam integer COMMANDS = 2;", "generated RTL")
    _require_token(top_module, "localparam integer GQA_HEADS = 8;", "generated RTL")
    _require_token(top_module, "localparam integer WAVES = 8;", "generated RTL")
    _require_token(top_module, "reg [31:0] shared_lfsr_q;", "generated RTL")
    _require_token(top_module, "reg [11:0] shared_beat_count_q;", "generated RTL")
    _require_token(top_module, "wire batch_command_index_w = shared_beat_count_q[10];", "generated RTL")
    _require_token(top_module, "wire [2:0] batch_wave_index_w = shared_beat_count_q[9:7];", "generated RTL")
    _require_token(top_module, "wire [2:0] batch_head_lane_w = shared_beat_count_q[6:4];", "generated RTL")
    _require_token(top_module, "wire [SLICE_BITS-1:0] batch_slice_index_w = shared_beat_count_q[3:0];", "generated RTL")
    _require_token(top_module, "wire atomic_batch_valid_w = batch_pending_w && batch_ready_w;", "generated RTL")
    _require_token(top_module, "if (running_q && atomic_batch_fire_w) begin", "generated RTL")
    _require_token(top_module, "source_fold_q <= source_fold_q ^ source_fold_next_w;", "generated RTL")
    _require_token(top_module, "leaf_fire_count_q <= leaf_fire_count_q + leaf_fire_count_inc_w;", "generated RTL")
    _require_token(top_module, "output wire [327:0] final_value,", "generated RTL")
    _require_token(top_module, "assign leaf_command_id_w[0 +: 16] = 16'h7b00 + {15'd0, batch_command_index_w};", "generated RTL")

    if mode == "reducer":
        reducer_top = f"{top_name}__reducer"
        _extract_module(rtl, reducer_top)
        if top_module.count(f"{reducer_top} u_reducer") != 1:
            raise SystemExit("generated RTL must instantiate the GQA8 reducer exactly once in reducer mode")
        _require_token(top_module, "wire reducer_final_result_w =", "generated RTL")
        _require_token(top_module, "(reducer_out_command_id_w == 16'h7b01)", "generated RTL")
        _require_token(top_module, "(reducer_out_head_id_w == 5'd15)", "generated RTL")
        _require_token(top_module, "(reducer_out_slice_w == 4'd15);", "generated RTL")
        if pair_node_impl == FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL:
            if "case (bucket)" in rtl:
                raise SystemExit("folded exact merge RTL must not contain monolithic exp LUT case statements")
    else:
        if "__reducer" in top_module:
            raise SystemExit("source_only RTL must not instantiate the GQA8 reducer")
        _require_token(top_module, "if (SOURCE_ONLY_MODE == 1'b1) begin", "generated RTL")
        _require_token(top_module, "if (shared_beat_count_q == 12'd2047) begin", "generated RTL")

    for forbidden in (
        "equivalence_hash",
        "openroad",
        "hash_out",
        "leaf_lfsr_q",
        "leaf_beat_count_q",
        "leaf_value_q",
        "shared_lfsr_q [0:PRODUCERS-1]",
        "state_value_q [0:STATE_BEATS-1]",
    ):
        if forbidden in top_module:
            raise SystemExit(f"physical harness RTL must not contain {forbidden} tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_v1",
                "producers": producers,
                "mode": mode,
                "waves": waves,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
