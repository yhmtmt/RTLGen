#!/usr/bin/env python3
"""Validate the composed multivalue service before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


_SCORE_BANK_BLACKBOX = "fakeram45_2048x39"
_SCORE_BANK_BLACKBOX_VERILOG = "npu/rtl/fakeram45_2048x39_blackbox.v"
_SCORE_BANK_LEF = "/orfs/flow/platforms/nangate45/lef/fakeram45_2048x39.lef"
_SCORE_BANK_LIB = "/orfs/flow/platforms/nangate45/lib/fakeram45_2048x39.lib"
_VALUE_MEM_BLACKBOX = "fakeram45_64x32"
_VALUE_MEM_BLACKBOX_VERILOG = "npu/rtl/fakeram45_64x32_blackbox.v"
_VALUE_MEM_LEF = "/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef"
_VALUE_MEM_LIB = "/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib"
_SUPPORTED_CLUSTER_COUNTS = {1, 2}


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
        raise SystemExit(
            f"selected config must be a direct child of design-dir, got: {relative_path.as_posix()}"
        )
    return config_path


def _require(mapping: dict[str, object], key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def _source_w(cluster_count: int) -> int:
    return max(1, (cluster_count - 1).bit_length())


def _semantic_profile(result_mode: str) -> str:
    if result_mode == "exact_partial":
        return "decode_m1x8_shared_score_16x8d_value_exact_partial_onchip_service_v1"
    return "decode_m1x8_shared_score_16x8d_value_iterdiv_onchip_service_v1"


def _cluster_semantic_profile(result_mode: str) -> str:
    if result_mode == "exact_partial":
        return "decode_m1x8_shared_score_16x8d_value_exact_partial_v1"
    return "decode_m1x8_shared_score_16x8d_value_iterdiv_v1"


def _result_value_bits(result_mode: str) -> int:
    return 328 if result_mode == "exact_partial" else 320


def _top_pin_bits(cluster_count: int, *, result_mode: str, head_id_bits: int) -> int:
    source_w = _source_w(cluster_count)
    base_bits = 1487 + source_w
    per_cluster_bits = 687 + source_w
    if result_mode == "exact_partial":
        base_bits += head_id_bits + (_result_value_bits(result_mode) - 320)
        per_cluster_bits += (2 * head_id_bits) + (_result_value_bits(result_mode) - 320)
    return base_bits + (cluster_count * per_cluster_bits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Config used to generate the design; defaults to <design-dir>/config.json",
    )
    args = parser.parse_args()

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    paths = {
        "config": config_path,
        "generated": rtl_dir / "config.json",
        "manifest": rtl_dir / "attention_decode_score_multivalue_service_manifest.json",
        "generated_macro_manifest": rtl_dir / "macro_manifest.json",
        "design_macro_manifest": design_dir / "macro_manifest.json",
        "top": rtl_dir / "top.v",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"missing decode-score multivalue service artifact: {path}")

    config = _load_json(paths["config"])
    generated_config = _load_json(paths["generated"])
    if config != generated_config:
        raise SystemExit("generated config does not match source config")
    body = config.get("attention_decode_score_multivalue_service")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_decode_score_multivalue_service object")

    expected_config = {
        "max_blocks": 16,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
        "score_scale_lanes_per_cycle": 1,
        "value_memory_backend": "macro_banked_4x16x64x32",
    }
    for key, expected in expected_config.items():
        _require(body, key, expected, "service config")
    cluster_count = int(body.get("cluster_count", 0))
    result_mode = str(body.get("result_mode", "normalized")).strip().lower()
    head_id_bits = int(body.get("head_id_bits", 5))
    if cluster_count not in _SUPPORTED_CLUSTER_COUNTS:
        raise SystemExit("service config cluster_count must be exactly one of 1 or 2 for this first physical patch")
    if result_mode not in {"normalized", "exact_partial"}:
        raise SystemExit("service config result_mode must be normalized or exact_partial")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("service config head_id_bits must be in [1, 8]")
    if result_mode == "exact_partial":
        if body.get("result_mode") != "exact_partial":
            raise SystemExit("service config must explicitly set result_mode=exact_partial")
        if "head_id_bits" not in body:
            raise SystemExit("service config exact_partial mode must explicitly set head_id_bits")

    top_name = str(config.get("top_name") or "")
    expected_suffix = f"_c{cluster_count}_p128_b4_q4_rl2_rr"
    if expected_suffix not in top_name:
        raise SystemExit("service top_name must encode c/p/b/q/rl/rr physical point")

    manifest = _load_json(paths["manifest"])
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_decode_score_multivalue_service.py",
        "semantic_profile": _semantic_profile(result_mode),
        "cluster_count": cluster_count,
        "max_blocks": 16,
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
        "value_dimensions": 128,
        "value_slices": 16,
        "score_scale_lanes_per_cycle": 1,
        "fsm_encoding": "default",
        "result_mode": result_mode,
        "head_id_bits": head_id_bits,
        "result_value_bits_per_beat": _result_value_bits(result_mode),
        "value_memory_backend": "macro_banked_4x16x64x32",
        "value_memory_promotable": True,
        "score_bank_macro_count": 56 * cluster_count,
        "value_memory_macro_count": 64,
        "total_macro_count": (56 * cluster_count) + 64,
        "shared_result_egress": "single_ready_valid_round_robin_hold_reg_v2",
        "shared_result_egress_initiation_interval": 1,
        "shared_result_egress_stall_semantics": "stable_until_handshake",
        "response_metadata_guard": "single_outstanding_per_cluster_v1",
        "top_pin_bits": _top_pin_bits(cluster_count, result_mode=result_mode, head_id_bits=head_id_bits),
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    cluster_manifest = manifest.get("submodule_manifests", {}).get("multivalue_cluster", {})
    _require(
        cluster_manifest,
        "semantic_profile",
        _cluster_semantic_profile(result_mode),
        "embedded cluster manifest",
    )
    _require(cluster_manifest, "score_bank_macro_count", 56, "embedded cluster manifest")
    _require(cluster_manifest, "result_mode", result_mode, "embedded cluster manifest")
    _require(
        cluster_manifest,
        "result_value_bits_per_beat",
        _result_value_bits(result_mode),
        "embedded cluster manifest",
    )
    if result_mode == "exact_partial":
        _require(cluster_manifest, "head_id_bits", head_id_bits, "embedded cluster manifest")

    design_macro_manifest = _load_json(paths["design_macro_manifest"])
    generated_macro_manifest = _load_json(paths["generated_macro_manifest"])
    if design_macro_manifest != generated_macro_manifest:
        raise SystemExit("design macro_manifest.json must match generated verilog/macro_manifest.json exactly")
    _require(design_macro_manifest, "design_id", top_name, "macro manifest")
    _require(design_macro_manifest, "module", top_name, "macro manifest")
    _require(design_macro_manifest, "platform", "nangate45", "macro manifest")
    _require(design_macro_manifest, "flow_variant", "decode_score_multivalue_service_v1", "macro manifest")
    _require(
        design_macro_manifest,
        "blackboxes",
        [_SCORE_BANK_BLACKBOX, _VALUE_MEM_BLACKBOX],
        "macro manifest",
    )
    _require(
        design_macro_manifest,
        "additional_lefs",
        [_SCORE_BANK_LEF, _VALUE_MEM_LEF],
        "macro manifest",
    )
    _require(
        design_macro_manifest,
        "additional_libs",
        [_SCORE_BANK_LIB, _VALUE_MEM_LIB],
        "macro manifest",
    )
    _require(design_macro_manifest, "additional_gds", [], "macro manifest")
    _require(
        design_macro_manifest,
        "blackbox_verilog",
        [_SCORE_BANK_BLACKBOX_VERILOG, _VALUE_MEM_BLACKBOX_VERILOG],
        "macro manifest",
    )

    macro_params = design_macro_manifest.get("manifest_params", {})
    expected_macro_params = {
        "semantic_profile": _semantic_profile(result_mode),
        "cluster_count": cluster_count,
        "score_bank_macro_count": 56 * cluster_count,
        "value_memory_backend": "macro_banked_4x16x64x32",
        "value_memory_macro_count": 64,
        "value_memory_bank_count": 4,
        "value_memory_macros_per_bank": 16,
        "value_memory_macro_depth": 64,
        "value_memory_logical_depth_per_bank": 64,
        "value_memory_logical_depth_total": 256,
        "value_memory_macro_overprovision_factor": 1,
        "value_memory_lane_width_bits": 32,
        "value_memory_physical_contract": "banked_4x16x64x32_exact_capacity",
        "value_memory_promotable": True,
        "total_macro_count": (56 * cluster_count) + 64,
        "packet_w": 128,
        "banks": 4,
        "max_blocks": 16,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
        "score_scale_lanes_per_cycle": 1,
        "result_mode": result_mode,
        "head_id_bits": head_id_bits,
        "result_value_bits_per_beat": _result_value_bits(result_mode),
        "score_passes_per_command": 1,
        "value_slices": 16,
        "shared_result_egress": "single_ready_valid_round_robin_hold_reg_v2",
        "top_pin_bits": _top_pin_bits(cluster_count, result_mode=result_mode, head_id_bits=head_id_bits),
        "macro_eval_excludes_io_pads": True,
    }
    for key, expected in expected_macro_params.items():
        _require(macro_params, key, expected, "macro manifest")
    if int(macro_params.get("minimum_core_side_um", 0)) <= 0:
        raise SystemExit("macro manifest minimum_core_side_um must be positive")
    if int(macro_params.get("minimum_die_side_um", 0)) <= int(macro_params.get("minimum_core_side_um", 0)):
        raise SystemExit("macro manifest minimum_die_side_um must exceed minimum_core_side_um")

    rtl = paths["top"].read_text(encoding="utf-8", errors="replace")
    cluster_top = f"{top_name}__cluster"
    if f"localparam integer CLUSTERS = {cluster_count};" not in rtl:
        raise SystemExit("service RTL must bind CLUSTERS to the requested cluster_count")
    required_tokens = (
        "noc_ready_valid_router #(",
        "noc_value_matrix_reassembler #(",
        "banked_value_memory_service #(",
        ".MEMORY_IMPL(1)",
        "for (gi = 0; gi < CLUSTERS; gi = gi + 1) begin : gen_cluster",
        f"{cluster_top} u_cluster (",
        "shared_result_valid_q",
        "result_rr_cursor_q",
        "candidate_valid_count_r",
        "protocol_error_q || (|cluster_protocol_error) || (|reassembler_protocol_error)",
        "gen_value_macro_backend",
        "fakeram45_64x32 u_value_mem_lane",
        "macro_capture_pending_q",
        "bank_from_addr(preload_addr) == macro_bank_gi",
    )
    for token in required_tokens:
        if token not in rtl:
            raise SystemExit(f"service RTL missing semantic token: {token}")
    if result_mode == "exact_partial":
        for token in (
            "cluster_command_head_id",
            "cluster_result_head_id",
            "shared_result_head_id",
            "raw_cluster_result_head_id",
            "shared_result_head_id_q",
            ".command_head_id(",
            ".result_head_id(",
        ):
            if token not in rtl:
                raise SystemExit(f"service RTL missing exact_partial token: {token}")
    for forbidden in ("equivalence_hash", "result_hash", "sha256", "checksum"):
        if re.search(rf"\b{re.escape(forbidden)}\b", rtl, flags=re.IGNORECASE):
            raise SystemExit(f"service RTL contains forbidden abstraction token: {forbidden}")
    if "behavioral_only_non_promotable" in rtl:
        raise SystemExit("service RTL must not embed a behavioral-only physical contract")

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_decode_score_multivalue_service_v1",
                "cluster_count": cluster_count,
                "result_mode": result_mode,
                "top_pin_bits": _top_pin_bits(
                    cluster_count, result_mode=result_mode, head_id_bits=head_id_bits
                ),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
