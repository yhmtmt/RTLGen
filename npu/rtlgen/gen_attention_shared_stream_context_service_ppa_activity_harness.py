#!/usr/bin/env python3
"""Generate the compact physical top for the complete VC0 context service."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_shared_stream_context_service_ppa_activity_harness"
GENERATOR = "npu/rtlgen/gen_attention_shared_stream_context_service_ppa_activity_harness.py"
MANIFEST_NAME = "attention_shared_stream_context_service_ppa_activity_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_stream_context_service_ppa_v1"
PROPOSAL_PATH = f"docs/proposals/{PROPOSAL_ID}/proposal.json"
HIERARCHY_PREFIX = "composition/service/"

_RTL_SOURCES = (
    "npu/sim/rtl/noc_ready_valid_fifo.sv",
    "npu/sim/rtl/noc_segmented_mesh_router.sv",
    "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
    "npu/sim/rtl/attention_shared_stream_context_admission.sv",
    "npu/sim/rtl/attention_shared_stream_context_engine.sv",
    "npu/sim/rtl/attention_shared_stream_context_service.sv",
    "npu/sim/rtl/attention_shared_stream_context_service_ppa_activity_harness.sv",
)


def _load(path: Path) -> dict[str, Any]:
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


def _validate(config: dict[str, Any]) -> str:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    if int(body.get("remote_contexts", 112)) != 112:
        raise SystemExit("remote_contexts must remain 112 for the canonical Llama7B service")
    if int(body.get("packets_per_context", 68)) != 68:
        raise SystemExit("packets_per_context must remain 68 for the canonical Llama7B service")
    if str(body.get("hierarchy_area_prefix", HIERARCHY_PREFIX)).strip() != HIERARCHY_PREFIX:
        raise SystemExit(f"hierarchy_area_prefix must remain {HIERARCHY_PREFIX!r}")
    return top_name


def _top(top_name: str) -> str:
    return f'''// Generated compact physical top for the complete VC0 shared-stream service.
(* keep_hierarchy = "yes" *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire enable,
  input wire [31:0] control,
  output wire [127:0] observable
);
  (* keep_hierarchy = "yes" *)
  attention_shared_stream_context_service_ppa_activity_harness composition (
    .clk(clk), .rst_n(rst_n), .enable(enable),
    .control(control), .observable(observable)
  );
endmodule
'''


def generate(config: dict[str, Any], out_dir: Path) -> None:
    config = json.loads(json.dumps(config))
    top_name = _validate(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = [
        {"path": GENERATOR, "sha256": _sha256(REPO_ROOT / GENERATOR), "role": "generator"}
    ]
    chunks: list[str] = []
    for relative in _RTL_SOURCES:
        path = REPO_ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required service RTL source is missing: {relative}")
        records.append({"path": relative, "sha256": _sha256(path), "role": "service_dependency"})
        chunks.append(path.read_text(encoding="utf-8").rstrip())
    chunks.append(_top(top_name).rstrip())
    (out_dir / "top.v").write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    manifest = {
        "version": 1,
        "generator": GENERATOR,
        "top_name": top_name,
        "semantic_profile": "attention_shared_stream_context_service_ppa_v1",
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
            "module": "attention_shared_stream_context_service_ppa_activity_harness",
            "dut_instance_name": "service",
            "dut_module": "attention_shared_stream_context_service",
            "dut_hierarchy_area_prefix": HIERARCHY_PREFIX,
        },
        "service_contract": {
            "remote_contexts": 112,
            "packets_per_context": 68,
            "flits_per_packet": 8,
            "total_packets": 7616,
            "total_flits": 60928,
            "virtual_channel": 0,
            "mesh": "noc_sram_packet_mesh4x4",
            "producer_addresses_are_external": True,
            "completion_releases_endpoint_ownership": True,
        },
        "hierarchy_area_prefix": HIERARCHY_PREFIX,
        "source_files": records,
        "generated_top_sha256": _sha256(out_dir / "top.v"),
        "power_scope": {
            "whole_harness_power_is_upper_bound": True,
            "stimulus_logic_is_dut_area": False,
            "dut_area_scope": HIERARCHY_PREFIX,
            "workload_activity_power_measured": False,
        },
        "remaining_abstractions": [
            "Source and destination SRAM bitcells are accounted separately from this service.",
            "VC1 exact reduction uses a separate embodied mesh in the dual-network point.",
            "HBM/DRAM service remains external by design.",
        ],
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
