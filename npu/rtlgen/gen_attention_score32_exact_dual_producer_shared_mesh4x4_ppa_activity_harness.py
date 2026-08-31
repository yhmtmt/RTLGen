#!/usr/bin/env python3
"""Generate the composed exact VC0/VC1 shared-mesh physical harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import (
    generate as generate_exact_tree,
)

JsonDict = dict[str, Any]

CONFIG_KEY = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness"
GENERATOR = "npu/rtlgen/gen_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness.py"
MANIFEST_NAME = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"
PROPOSAL_PATH = f"docs/proposals/{PROPOSAL_ID}/proposal.json"
EXACT_TREE_TOP = "attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59"
HIERARCHY_PREFIXES = (
    "composition/vc0_activity/service/",
    "composition/vc1_activity/exact_transport_wrapper/",
    "composition/shared_transport/",
)

# Keep this list explicit.  The two activity harnesses share the first five
# transport sources; _unique_sources() emits each module exactly once.
_RTL_SOURCES = (
    "npu/sim/rtl/noc_ready_valid_fifo.sv",
    "npu/sim/rtl/noc_segmented_mesh_router.sv",
    "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint_array16.sv",
    "npu/sim/rtl/noc_endpoint_vc_injection_arbiter.sv",
    "npu/sim/rtl/attention_shared_stream_context_admission.sv",
    "npu/sim/rtl/attention_shared_stream_context_engine.sv",
    "npu/sim/rtl/attention_shared_stream_context_service.sv",
    "npu/sim/rtl/attention_shared_stream_context_service_ppa_activity_harness.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_packet_bridge.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_codec.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_group_admission.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper.sv",
    "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_transport_ppa_activity_harness.sv",
    "npu/sim/rtl/noc_shared_vc_dual_producer_transport4x4.sv",
    "npu/sim/rtl/attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness.sv",
)
_GENERATOR_SOURCES = (
    "npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py",
    "npu/rtlgen/gen_attention_score32_exact_partial_tree.py",
    "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
    "npu/rtlgen/gen_attention_score32_online_state_merge.py",
    "npu/sim/perf/attention_exact_partial.py",
)
_FAKERAM_MODEL = "npu/sim/rtl/fakeram45_64x32_model.sv"
_FAKERAM_BLACKBOX = "npu/rtl/fakeram45_64x32_blackbox.v"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_sources() -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for relative in _RTL_SOURCES:
        if relative not in seen:
            seen.add(relative)
            result.append(relative)
    return tuple(result)


def _validate(config: JsonDict) -> str:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    if int(body.get("physical_banks", 15)) != 15:
        raise SystemExit("physical_banks must remain 15 for the composed physical point")
    if int(body.get("use_fakeram", 1)) != 1:
        raise SystemExit("use_fakeram must remain 1 for physical macro accounting")
    prefixes = body.get("hierarchy_area_prefixes", list(HIERARCHY_PREFIXES))
    if tuple(str(prefix).strip() for prefix in prefixes) != HIERARCHY_PREFIXES:
        raise SystemExit("hierarchy_area_prefixes must match the three composed DUT prefixes")
    return top_name


def _top(top_name: str) -> str:
    return f'''// Generated compact physical top for the exact dual-producer shared mesh.
// Verification stimulus is below the compact boundary and is excluded from
// DUT area attribution by the three composition/* hierarchy prefixes.
(* keep_hierarchy = "yes" *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [31:0] control,
  output wire [127:0] observable
);
  (* keep_hierarchy = "yes" *)
  attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness #(
    .PHYSICAL_BANKS(15),
    .USE_FAKERAM(1)
  ) composition (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .control(control), .observable(observable)
  );
endmodule
'''


def _source_records() -> list[JsonDict]:
    records: list[JsonDict] = [
        {
            "path": GENERATOR,
            "sha256": _sha256(REPO_ROOT / GENERATOR),
            "role": "composed_dual_producer_generator",
        }
    ]
    for relative in _GENERATOR_SOURCES:
        path = REPO_ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required generator source is missing: {relative}")
        records.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "role": "exact_c16_r2_l8_b59_generator_dependency",
            }
        )
    for relative in _unique_sources():
        path = REPO_ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required composed RTL source is missing: {relative}")
        records.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "role": "composed_rtl_dependency",
            }
        )
    for relative, role in (
        (_FAKERAM_MODEL, "simulation_memory_model"),
        (_FAKERAM_BLACKBOX, "physical_memory_blackbox"),
    ):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required memory source is missing: {relative}")
        records.append({"path": relative, "sha256": _sha256(path), "role": role})
    return records


def generate(config: JsonDict, out_dir: Path) -> None:
    config = json.loads(json.dumps(config))
    top_name = _validate(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="dual_producer_shared_mesh_tree_") as temp_name:
        tree_dir = Path(temp_name) / "tree"
        generate_exact_tree(
            {
                "top_name": EXACT_TREE_TOP,
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 59,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                },
            },
            tree_dir,
        )
        tree_rtl = (tree_dir / "top.v").read_text(encoding="utf-8").rstrip()
        tree_manifest = _load(
            tree_dir / "attention_score32_exact_banked_finalized_tree_manifest.json"
        )

    dependency_rtl = "\n\n".join(
        (REPO_ROOT / relative).read_text(encoding="utf-8").rstrip()
        for relative in _unique_sources()
    )
    fakeram_model = (REPO_ROOT / _FAKERAM_MODEL).read_text(encoding="utf-8").rstrip()
    fakeram_rtl = f"`ifndef SYNTHESIS\n{fakeram_model}\n`endif"
    rtl = f"{tree_rtl}\n\n{dependency_rtl}\n\n{fakeram_rtl}\n\n{_top(top_name).rstrip()}\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    source_records = _source_records()
    manifest: JsonDict = {
        "version": 1,
        "generator": GENERATOR,
        "top_name": top_name,
        "semantic_profile": "score32_exact_dual_producer_shared_mesh4x4_ppa_activity_v1",
        "linked_proposal_id": PROPOSAL_ID,
        "linked_proposal_path": PROPOSAL_PATH,
        "top_pin_inventory": {
            "input_bits": 35,
            "output_bits": 128,
            "total_bits": 163,
            "inputs": ["clk:1", "rst_n:1", "enable:1", "control:32"],
            "outputs": ["observable:128"],
        },
        "top_pin_bits": 163,
        "composition": {
            "instance_name": "composition",
            "module": "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness",
            "parameters": {"PHYSICAL_BANKS": 15, "USE_FAKERAM": 1},
            "dut_hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
            "stimulus_excluded_from_dut_area": True,
        },
        "hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
        "exact_global_tree": {
            "module": EXACT_TREE_TOP,
            "parameters": {
                "clusters": 16,
                "radix": 2,
                "value_slices": 16,
                "head_id_bits": 5,
                "divider_lanes": 8,
                "finalizer_banks": 59,
                "exp_scale_impl": "factored_h33_l64_mul_exact",
            },
            "generator_manifest": tree_manifest,
        },
        "vc0_service": {
            "virtual_channel": 0,
            "remote_contexts": 112,
            "waves": 7,
            "packets_per_context": 68,
            "total_packets": 7616,
            "flits_per_packet": 8,
            "total_flits": 60928,
            "hierarchy_area_prefix": HIERARCHY_PREFIXES[0],
        },
        "vc1_exact_reduction": {
            "virtual_channel": 1,
            "groups": 4,
            "packets_per_group": 315,
            "flits_per_group": 2505,
            "total_packets": 1260,
            "total_flits": 10020,
            "hierarchy_area_prefix": HIERARCHY_PREFIXES[1],
        },
        "shared_transport": {
            "instance_name": "shared_transport",
            "module": "noc_shared_vc_dual_producer_transport4x4",
            "mesh_module": "noc_segmented_mesh4x4",
            "mesh_count": 1,
            "injection_arbiter_module": "noc_endpoint_vc_injection_arbiter",
            "injection_arbiter_count": 16,
            "virtual_channels": 2,
            "hierarchy_area_prefix": HIERARCHY_PREFIXES[2],
        },
        "root_storage": {
            "macro_type": "fakeram45_64x32",
            "macro_count": 120,
            "physical_banks": 15,
            "macros_per_bank": 8,
            "scope": "VC1 root storage under composition/vc1_activity/exact_transport_wrapper/",
        },
        "traffic_contract": {
            "vc0_total_flits": 60928,
            "vc1_total_flits": 10020,
            "vc1_groups": 4,
            "producer_streams_are_internal_activity_stimulus": True,
            "hbm_dram": "external",
        },
        "macro_count": 120,
        "blackbox_instance_counts": {"fakeram45_64x32": 120},
        "source_files": source_records,
        "generated_top_sha256": _sha256(out_dir / "top.v"),
        "power_scope": {
            "whole_harness_power_is_upper_bound": True,
            "whole_harness_power_scope": "generated top including both activity stimuli, shared transport, and DUT",
            "stimulus_logic_is_dut_area": False,
            "dut_area_scope": list(HIERARCHY_PREFIXES),
            "workload_activity_power_measured": False,
        },
        "external_interfaces": {
            "hbm_dram": "external",
            "top_boundary_is_compact_registered_activity_control": True,
        },
        "remaining_abstractions": [
            "HBM/DRAM controller and off-chip memory service remain external by design.",
            "Whole-harness power is an upper bound until workload activity power is measured separately.",
        ],
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    macro_manifest: JsonDict = {
        "version": "0.1",
        "design_id": top_name,
        "module": top_name,
        "platform": "nangate45",
        "flow_variant": "score32_exact_dual_producer_shared_mesh4x4_ppa_activity_v1",
        "blackboxes": ["fakeram45_64x32"],
        "additional_lefs": ["/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef"],
        "additional_libs": ["/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib"],
        "additional_gds": [],
        "blackbox_verilog": [_FAKERAM_BLACKBOX],
        "source": {"mode": "generated_dual_producer_shared_mesh_physical_harness", "generator": GENERATOR},
        "hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
        "power_scope": {
            "whole_harness_power_is_upper_bound": True,
            "stimulus_logic_is_dut_area": False,
        },
        "manifest_params": {
            "physical_banks": 15,
            "root_storage_macro_type": "fakeram45_64x32",
            "macro_count": 120,
            "root_storage_macro_count": 120,
            "macros_per_bank": 8,
            "hierarchy_area_prefixes": list(HIERARCHY_PREFIXES),
        },
        "macro_count": 120,
        "blackbox_instance_counts": {"fakeram45_64x32": 120},
        "macro_inventory": [
            {
                "module": "fakeram45_64x32",
                "count": 120,
                "role": "vc1_root_storage",
                "hierarchy_prefix": HIERARCHY_PREFIXES[1],
            }
        ],
        "linked_proposal_id": PROPOSAL_ID,
        "linked_proposal_path": PROPOSAL_PATH,
        "source_files": source_records,
    }
    (out_dir / "macro_manifest.json").write_text(
        json.dumps(macro_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
