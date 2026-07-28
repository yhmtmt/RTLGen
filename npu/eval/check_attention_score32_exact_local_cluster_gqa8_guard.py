#!/usr/bin/env python3
"""Strict generated RTL guard for the full-width score32 exact local cluster."""

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

from npu.rtlgen.gen_attention_score32_exact_local_cluster_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_CLUSTER_GQA8_HEAD_BASES,
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local_cluster_gqa8_service_manifest,
)

_CONFIG_KEY = "attention_score32_exact_local_cluster_gqa8"
_MANIFEST_NAME = "attention_score32_exact_local_cluster_gqa8_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_score32_local_cluster_gqa8_v1"
_PROPOSAL_PATH = "docs/proposals/prop_l1_decoder_attention_score32_local_cluster_gqa8_v1/proposal.json"
_PRODUCER_RTL_NAME = "producer.v"
_REDUCER_RTL_NAME = "reducer.v"
_VERILATOR_LINT_STUBS_NAME = "verilator_wrapper_blackboxes.v"


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


def _top_pin_bits(*, producers: int) -> int:
    value_lanes = producers * 2
    return (
        2
        + 1
        + 1
        + 16
        + 5
        + (producers * 15)
        + 32
        + 6
        + producers
        + producers
        + producers
        + (producers * 128)
        + (producers * 128)
        + value_lanes
        + value_lanes
        + (value_lanes * 14)
        + (value_lanes * 4)
        + value_lanes
        + value_lanes
        + (value_lanes * 14)
        + (value_lanes * 4)
        + (value_lanes * 512)
        + 1
        + 1
        + 16
        + 5
        + 32
        + 33
        + 4
        + 1
        + PARTIAL_PAYLOAD_BITS
        + 32
        + 32
        + 32
        + 32
        + 3
        + 1
        + 5
        + 7
        + 7
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + (producers * 32)
        + (producers * 32)
        + (producers * 32)
        + (producers * 64)
        + (producers * 64)
        + (producers * 32)
        + (producers * 32)
        + (producers * 2)
        + producers
        + producers
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
    )


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_cluster_gqa8_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            _PRODUCER_RTL_NAME,
            _REDUCER_RTL_NAME,
            _VERILATOR_LINT_STUBS_NAME,
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
    producer_path = rtl_dir / _PRODUCER_RTL_NAME
    reducer_path = rtl_dir / _REDUCER_RTL_NAME
    lint_stub_path = rtl_dir / _VERILATOR_LINT_STUBS_NAME
    for path in (config_path, generated_config_path, manifest_path, top_path, producer_path, reducer_path, lint_stub_path):
        if not path.is_file():
            raise SystemExit(f"missing full-width local-cluster artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    producers = int(body.get("producers", 0))
    max_blocks = int(body.get("max_blocks", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    persistent_waves = int(body.get("persistent_waves", 0))
    if producers not in {53, 54}:
        raise SystemExit("producers must remain exactly 53 or 54")
    if max_blocks != 8:
        raise SystemExit("max_blocks must remain fixed at 8")
    if value_slices != 16:
        raise SystemExit("value_slices must remain 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain {LOCAL_TEMPORAL_WAVES}")

    probe_defaults = config.get("probe_defaults")
    if not isinstance(probe_defaults, dict):
        raise SystemExit("config must include probe_defaults")
    _require(probe_defaults, "head_bases", list(LOCAL_CLUSTER_GQA8_HEAD_BASES), "probe_defaults")
    _require(probe_defaults, "head_dim", 1, "probe_defaults")
    _require(probe_defaults, "seed", 73, "probe_defaults")

    service_model = exact_local_cluster_gqa8_service_manifest(producers=producers)
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_cluster_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local_cluster_gqa8_v1",
        "producers": producers,
        "producer_instance_count": producers,
        "max_blocks": 8,
        "value_slices": 16,
        "head_id_bits": 5,
        "persistent_waves": 8,
        "query_head_groups": 4,
        "query_heads_per_group": 8,
        "value_memory_lanes": producers * 2,
        "producer_input_lanes": producers,
        "result_interface": "full_width_exact_gqa8_producer_cluster_to_128beat_aggregate_after_group_major_8wave_reduce",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "rtl_files": [
            "top.v",
            _PRODUCER_RTL_NAME,
            _REDUCER_RTL_NAME,
            _VERILATOR_LINT_STUBS_NAME,
        ],
        "top_pin_bits": _top_pin_bits(producers=producers),
        "command_schedule_contract": service_model["top_command_contract"],
        "atomic_command_issue_contract": service_model["atomic_command_issue_contract"],
        "producer_input_contract": service_model["producer_input_contract"],
        "value_memory_contract": service_model["value_memory_contract"],
        "producer_leaf_wiring_contract": service_model["producer_leaf_wiring_contract"],
        "local_reduction_contract": service_model["local_reduction_contract"],
        "temporal_accumulation_contract": service_model["temporal_accumulation_contract"],
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "remaining_abstractions": service_model["remaining_abstractions"],
        "service_model": service_model,
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": _PROPOSAL_PATH,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    _require(manifest, "checked_in_probe_defaults", probe_defaults, "generated manifest")

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config must include report_links for evaluator artifact linkage")
    _require(links, "proposal_id", _PROPOSAL_ID, "report_links")
    _require(links, "proposal_path", _PROPOSAL_PATH, "report_links")

    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    producer_manifest = submodule_manifests.get("producer")
    reducer_manifest = submodule_manifests.get("gqa8_local_temporal_reducer")
    if not isinstance(producer_manifest, dict) or not isinstance(reducer_manifest, dict):
        raise SystemExit("generated manifest must contain producer and gqa8_local_temporal_reducer submodule manifests")
    _require(
        producer_manifest,
        "generator",
        "npu/rtlgen/gen_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        "producer submodule manifest",
    )
    _require(producer_manifest, "max_blocks", 8, "producer submodule manifest")
    _require(producer_manifest, "query_heads_per_stream", 8, "producer submodule manifest")
    _require(producer_manifest, "head_id_bits", 5, "producer submodule manifest")
    _require(
        reducer_manifest,
        "generator",
        "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8.py",
        "reducer submodule manifest",
    )
    _require(reducer_manifest, "producers", producers, "reducer submodule manifest")
    _require(reducer_manifest, "query_heads_per_group", 8, "reducer submodule manifest")

    top_rtl = top_path.read_text(encoding="utf-8", errors="replace")
    producer_rtl = producer_path.read_text(encoding="utf-8", errors="replace")
    reducer_rtl = reducer_path.read_text(encoding="utf-8", errors="replace")
    lint_stub_rtl = lint_stub_path.read_text(encoding="utf-8", errors="replace")
    producer_top = f"{top_name}__producer"
    reducer_top = f"{top_name}__reducer"
    top_module = _extract_module(top_rtl, top_name)
    _extract_module(producer_rtl, producer_top)
    _extract_module(reducer_rtl, reducer_top)

    if len(re.findall(rf"\bmodule\s+{re.escape(producer_top)}\b", producer_rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one reusable producer module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(reducer_top)}\b", reducer_rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one reusable reducer module definition")
    _require_token(lint_stub_rtl, f"(* blackbox *) module {producer_top}", "Verilator lint stubs")
    _require_token(lint_stub_rtl, f"(* blackbox *) module {reducer_top}", "Verilator lint stubs")
    if top_module.count(f"{producer_top} u_producer_") != producers:
        raise SystemExit(f"generated RTL must instantiate the producer exactly {producers} times")
    if top_module.count(f"{reducer_top} u_reducer") != 1:
        raise SystemExit("generated RTL must instantiate the reducer exactly once")

    command_hi = (producers * 15) - 1
    command_lo = command_hi - 14
    query_hi = (producers * 128) - 1
    query_lo = query_hi - 127
    lane_hi = (producers * 2) - 1
    lane_lo = lane_hi - 1
    addr_hi = (producers * 28) - 1
    addr_lo = addr_hi - 27
    matrix_hi = (producers * 1024) - 1
    matrix_lo = matrix_hi - 1023
    for token in (
        "wire group_command_fire_w = command_valid && command_ready;",
        "wire [PRODUCERS-1:0] producer_command_accept_w = {PRODUCERS{group_command_fire_w}} & producer_command_ready_w;",
        "assign command_ready = &producer_command_ready_w;",
        "assign protocol_error = atomic_command_protocol_error_q || (|producer_protocol_error) || reducer_protocol_error;",
        ".command_valid(group_command_fire_w)",
        ".leaf_valid(producer_result_valid_w)",
        ".leaf_ready(producer_result_ready_w)",
        ".leaf_command_id(producer_result_command_id_w)",
        ".leaf_head_id(producer_result_head_id_w)",
        ".leaf_global_max(producer_result_global_max_w)",
        ".leaf_exp_sum(producer_result_exp_sum_w)",
        ".leaf_slice(producer_result_slice_w)",
        ".leaf_last(producer_result_last_w)",
        ".leaf_value(producer_result_value_w)",
        "wave_command_accept_count_q <= wave_command_accept_count_q + 1'b1;",
        "producer_ready_skew_cycles_q <= producer_ready_skew_cycles_q + 1'b1;",
        "if (producer_command_accept_w != {PRODUCERS{1'b1}}) begin",
        ".command_block_count(command_block_count[14:0])",
        f".command_block_count(command_block_count[{command_hi}:{command_lo}])",
        ".input_query(input_query[127:0])",
        f".input_query(input_query[{query_hi}:{query_lo}])",
        ".value_read_req_valid(value_read_req_valid[1:0])",
        f".value_read_req_valid(value_read_req_valid[{lane_hi}:{lane_lo}])",
        ".value_read_req_address(value_read_req_address[27:0])",
        f".value_read_req_address(value_read_req_address[{addr_hi}:{addr_lo}])",
        ".value_response_matrix(value_response_matrix[1023:0])",
        f".value_response_matrix(value_response_matrix[{matrix_hi}:{matrix_lo}])",
    ):
        _require_token(top_module, token, "generated RTL")

    for forbidden in ("equivalence_hash", "result_hash", "reduced_proxy", "hash_only"):
        if forbidden in top_module:
            raise SystemExit(f"full-width local-cluster RTL must not contain {forbidden} tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_local_cluster_gqa8_v1",
                "producers": producers,
                "top_pin_bits": _top_pin_bits(producers=producers),
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
