#!/usr/bin/env python3
"""Strict generated RTL guard for the dual-stream GQA8 exact-partial producer slice."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import generate
from npu.sim.perf.attention_exact_partial import (
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_partial_dual_stream_gqa8_producer_service_manifest,
)

_CONFIG_KEY = "attention_score32_exact_partial_gqa8_dual_stream_producer"
_MANIFEST_NAME = "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json"


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
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_gqa8_dual_stream_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            _MANIFEST_NAME,
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
    manifest_path = rtl_dir / _MANIFEST_NAME
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing dual-stream exact-partial producer artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    streams = int(body.get("streams", 0))
    query_heads_per_stream = int(body.get("query_heads_per_stream", 0))
    max_blocks = int(body.get("max_blocks", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    if streams != 2:
        raise SystemExit("dual-stream exact producer must remain fixed at streams=2")
    if query_heads_per_stream != 8:
        raise SystemExit("dual-stream exact producer must remain fixed at query_heads_per_stream=8")
    if max_blocks < 8 or max_blocks > 16384 or (max_blocks & (max_blocks - 1)):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if value_slices != 16:
        raise SystemExit("value_slices must remain 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain 5 for explicit 32-head addressing")

    probe_defaults = config.get("probe_defaults", {})
    if not isinstance(probe_defaults, dict):
        probe_defaults = {}
    service_model = exact_partial_dual_stream_gqa8_producer_service_manifest(
        heads=int(probe_defaults.get("heads", 8)),
        max_blocks=max_blocks,
        command_count=int(probe_defaults.get("command_count", int(probe_defaults.get("heads", 8)) // 8)),
        blocks_per_stream=int(probe_defaults.get("blocks_per_stream", 2)),
        block_counts_per_stream=tuple(int(value) for value in probe_defaults.get("block_counts_per_stream", []))
        if isinstance(probe_defaults.get("block_counts_per_stream"), list)
        else None,
        head_dim=int(probe_defaults.get("head_dim", 3)),
        head_bases=tuple(int(value) for value in probe_defaults.get("head_bases", [])) if isinstance(probe_defaults.get("head_bases"), list) else None,
        llama_wave_reference_cycles=int(probe_defaults["llama_wave_reference_cycles"]) if "llama_wave_reference_cycles" in probe_defaults else None,
    )
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        "semantic_profile": "score32_exact_partial_gqa8_dual_stream_producer_v1",
        "streams": 2,
        "query_heads_per_stream": 8,
        "token_lanes_per_head": 8,
        "structural_score_macs_per_cycle": 128,
        "max_blocks": max_blocks,
        "value_slices": 16,
        "head_id_bits": 5,
        "producer_result_mode": "exact_partial",
        "command_schedule_contract": "in_order_head_base_commands_broadcast_to_both_streams",
        "head_mapping_contract": "explicit_head_base_plus_lane_no_tile_or_wave_inference",
        "result_interface": "two_exact_partial_gqa8_streams_to_pairwise_exact_merge",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "exact_protocols": {
            "producer_partial_protocol": service_model["producer_partial_protocol"],
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
    group_manifest = submodule_manifests.get("gqa_group")
    merge_manifest = submodule_manifests.get("merge")
    if not isinstance(group_manifest, dict) or not isinstance(merge_manifest, dict):
        raise SystemExit("generated manifest must contain gqa_group and merge submodule manifests")
    _require(group_manifest, "generator", "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_group.py", "gqa_group submodule manifest")
    _require(group_manifest, "result_mode", "exact_partial", "gqa_group submodule manifest")
    _require(group_manifest, "head_id_bits", 5, "gqa_group submodule manifest")
    _require(group_manifest, "parallel_query_head_clusters", 8, "gqa_group submodule manifest")
    _require(group_manifest, "result_value_bits_per_beat", 328, "gqa_group submodule manifest")
    cluster_manifest = group_manifest.get("submodule_manifests", {}).get("multivalue_cluster", {})
    _require(cluster_manifest, "result_mode", "exact_partial", "embedded cluster manifest")
    _require(cluster_manifest, "head_id_bits", 5, "embedded cluster manifest")
    _require(cluster_manifest, "score_bank_macro_count", 56, "embedded cluster manifest")
    _require(merge_manifest, "generator", "npu/rtlgen/gen_attention_score32_online_state_merge.py", "merge submodule manifest")
    _require(merge_manifest, "result_interface", "ready_valid_exact_partial_slice_stream", "merge submodule manifest")
    _require(merge_manifest, "partial_payload_bits_per_beat", 328, "merge submodule manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    group_top = f"{top_name}__group"
    merge_top = f"{top_name}__merge"
    top_module = _extract_module(rtl, top_name)
    _extract_module(rtl, group_top)
    _extract_module(rtl, merge_top)

    if len(re.findall(rf"\bmodule\s+{re.escape(group_top)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one GQA group module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(merge_top)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one exact merge module definition")
    if top_module.count(f"{group_top} u_stream_") != 2:
        raise SystemExit("generated RTL must instantiate the exact GQA group exactly twice")
    if top_module.count(f"{merge_top} u_merge") != 1:
        raise SystemExit("generated RTL must instantiate the exact merge exactly once")

    for token in (
        "input  wire [4:0] command_head_base,",
        "input  wire signed [127:0] input_query,",
        "input  wire signed [127:0] input_key,",
        "output wire [1:0]   value_read_req_valid,",
        "input  wire [1023:0] value_response_matrix,",
        "output wire [4:0] result_head_id,",
        "assign command_ready = command_head_base_valid_w && (&stream_command_ready_w);",
        "assign input_ready = &stream_input_ready_w;",
        ".command_head_base(command_head_base)",
        ".input_query(input_query[63:0])",
        ".input_query(input_query[127:64])",
        ".input_key(input_key[63:0])",
        ".input_key(input_key[127:64])",
        ".left_head_id(stream_result_head_id_w[4:0])",
        ".right_head_id(stream_result_head_id_w[9:5])",
        "command_head_base[2:0] == 3'd0",
        "result_head_id[2:0] == 3'd7",
        "stream_result_head_w[2:0] != stream_result_head_w[5:3]",
        "stream_partial_valid = stream_result_valid_w;",
        "stream_partial_ready = stream_result_ready_w;",
        "stream_partial_last = stream_result_last_w;",
        "result_stall_cycles_q <= result_stall_cycles_q + 1'b1;",
    ):
        _require_token(top_module, token, "generated RTL")

    for forbidden in (
        "equivalence_hash",
        "result_hash",
        "finalizer",
        "local_normalization",
    ):
        if forbidden in rtl:
            raise SystemExit(f"functional datapath must not contain {forbidden} tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_partial_gqa8_dual_stream_producer_v1",
                "streams": streams,
                "query_heads_per_stream": query_heads_per_stream,
                "structural_score_macs_per_cycle": 128,
                "max_blocks": max_blocks,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
