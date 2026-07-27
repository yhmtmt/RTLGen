#!/usr/bin/env python3
"""Strict generated RTL guard for banked score32 exact finalized trees."""

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

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_banked_finalized_tree_service_manifest,
)

_SUPPORTED_CLUSTERS = {2, 4, 8, 16}
_SUPPORTED_LANES = {1, 2, 4, 8}
_PPA_SWEEP_TAG_PREFIX = "attention_score32_exact_banked_finalized_tree_c16_bank_firstpass_v1"
_PPA_SWEEP_FLOW_PARAMS = {
    "CLOCK_PERIOD": [8.0],
    "DIE_AREA": ["0 0 2700 2700"],
    "CORE_AREA": ["100 100 2600 2600"],
    "PLACE_DENSITY": [0.3, 0.5],
    "SYNTH_HIERARCHICAL": [1],
}
_PPA_SWEEP_ALLOWED_BANKS = {16, 32, 59, 64}


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
    with tempfile.TemporaryDirectory(prefix="score32_exact_banked_finalized_tree_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_banked_finalized_tree_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {relative_name}")


def _validate_ppa_sweep(*, config: dict[str, object], sweep_path: Path) -> None:
    if not sweep_path.is_file():
        raise SystemExit(f"missing sweep: {sweep_path}")
    sweep = _load_json(sweep_path)
    if sweep.get("tag_prefix") != _PPA_SWEEP_TAG_PREFIX:
        raise SystemExit(f"banked PPA sweep tag_prefix must be {_PPA_SWEEP_TAG_PREFIX}")
    if sweep.get("flow_params") != _PPA_SWEEP_FLOW_PARAMS:
        raise SystemExit("banked PPA sweep flow_params do not match the checked-in banked-finalized-tree contract")

    body = config.get("attention_score32_exact_banked_finalized_tree")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_banked_finalized_tree object")
    clusters = int(body.get("clusters", 0))
    radix = int(body.get("radix", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))
    if clusters != 16 or radix != 2 or divider_lanes != 8 or finalizer_banks not in _PPA_SWEEP_ALLOWED_BANKS:
        raise SystemExit(
            "banked PPA sweep membership requires c16/r2/l8 with finalizer_banks in {16, 32, 59, 64}"
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--sweep", type=Path, default=None)
    args = ap.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_banked_finalized_tree_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing banked exact finalized tree artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")
    if args.sweep is not None:
        _validate_ppa_sweep(config=config, sweep_path=args.sweep.resolve())

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_banked_finalized_tree")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_banked_finalized_tree object")

    clusters = int(body.get("clusters", 0))
    radix = int(body.get("radix", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))
    if clusters not in _SUPPORTED_CLUSTERS:
        raise SystemExit("clusters must be one of 2, 4, 8, 16")
    if radix != 2:
        raise SystemExit("radix must be 2 for the current banked exact finalized tree")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes not in _SUPPORTED_LANES:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, 8")
    if finalizer_banks < 1 or finalizer_banks > 64:
        raise SystemExit("finalizer_banks must be in [1, 64]")

    tree_nodes = clusters - 1
    tree_stages = int(math.log2(clusters))
    slice_bits = _clog2(value_slices)
    bank_id_bits = _clog2(finalizer_banks)
    tree_top_name = f"{top_name}__partial_tree"
    finalizer_top_name = f"{top_name}__root_finalizer"
    service_manifest = exact_banked_finalized_tree_service_manifest(
        clusters=clusters,
        heads=32,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
    )

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py",
        "semantic_profile": "score32_online_exact_banked_finalized_radix2_tree_v1",
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
        "tree_stages": tree_stages,
        "tree_nodes": tree_nodes,
        "result_interface": "clusters_ready_valid_exact_partial_leaf_streams_to_ordered_banked_exact_finalized_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "order_fifo_depth": finalizer_banks,
        "order_fifo_entry_bits": bank_id_bits,
        "order_fifo_storage_bits": finalizer_banks * bank_id_bits,
        "ordering_contract": "single_bank_id_fifo_exact_issue_order_one_beat_per_entry",
        "actual_finalizer_accept_interval_cycles": service_manifest["per_bank_accept_interval_cycles"],
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": True,
        "noc_closure": False,
        "sram_closure": False,
        "macro_eval_excludes_io_pads": True,
        "equivalence_hash": False,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    _require(manifest, "service_model", service_manifest, "generated manifest")

    submanifests = manifest.get("submodule_manifests")
    if not isinstance(submanifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    tree_manifest = submanifests.get("partial_tree")
    if not isinstance(tree_manifest, dict):
        raise SystemExit("generated manifest must contain partial_tree submodule manifest")
    finalizer_manifest = submanifests.get("root_finalizer")
    if not isinstance(finalizer_manifest, dict):
        raise SystemExit("generated manifest must contain root_finalizer submodule manifest")
    _require(tree_manifest, "top_name", tree_top_name, "partial-tree submodule manifest")
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
        "output_latency_cycles_per_beat": ((8 // divider_lanes) * 57) + 1,
        "accept_interval_cycles_per_beat": ((8 // divider_lanes) * 57) + 2,
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

    if len(re.findall(rf"\bmodule\s+{re.escape(finalizer_top_name)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one root finalizer module definition")
    if top_module.count(f"{finalizer_top_name} u_finalizer_bank_") != finalizer_banks:
        raise SystemExit("generated RTL finalizer instance count does not match finalizer_banks")

    for token in (
        f"output wire [{finalizer_banks - 1}:0] bank_protocol_error,",
        f"output wire [{finalizer_banks - 1}:0] bank_outstanding,",
        "output wire [31:0]  order_fifo_occupancy,",
        "output wire [31:0]  order_fifo_high_watermark,",
        "output wire [31:0]  order_enqueued_count,",
        "output wire [31:0]  order_dequeued_count,",
        "output wire [31:0]  dispatch_stall_cycles,",
        "output wire [31:0]  dispatch_bank_id,",
        "output wire [31:0]  head_bank_id,",
        "output wire         order_protocol_error,",
        "wire order_fifo_dequeue_fire_w = root_valid_r && root_ready;",
        "wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;",
        "wire tree_root_ready_w = dispatch_bank_in_ready_r && order_fifo_enqueue_ready_w;",
        "order_fifo_mem[order_fifo_tail_q] <= dispatch_bank_q;",
        "bank_outstanding_q[dispatch_bank_q] <= 1'b1;",
        "bank_outstanding_q[order_fifo_head_bank_id_w] <= 1'b0;",
        "dispatch_stall_cycles_q <= dispatch_stall_cycles_q + 1'b1;",
        "order_protocol_error_q <= 1'b1;",
    ):
        _require_token(top_module, token, "generated RTL")

    _require_token(tree_module, "assign protocol_error = |node_protocol_error;", "generated tree RTL")
    _require_token(finalizer_module, "localparam integer DIVIDE_ITERATIONS = 57;", "generated finalizer RTL")
    _require_token(finalizer_module, "assign in_ready = (state_q == IDLE) && !out_valid_q;", "generated finalizer RTL")
    if _contains_operator_division(finalizer_module):
        raise SystemExit("generated finalizer RTL must not contain combinational division operators")
    if "equivalence_hash" in rtl:
        raise SystemExit("functional datapath must not contain equivalence_hash tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_banked_finalized_tree_v1",
                "clusters": clusters,
                "divider_lanes": divider_lanes,
                "finalizer_banks": finalizer_banks,
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
