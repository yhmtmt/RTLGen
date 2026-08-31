#!/usr/bin/env python3
"""Guard and annotate the complete VC0 shared-stream service PPA canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.physical_hierarchy_metrics import attach_hierarchy_reports


CONFIG_KEY = "attention_shared_stream_context_service_ppa_activity_harness"
MANIFEST_NAME = "attention_shared_stream_context_service_ppa_activity_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_stream_context_service_ppa_v1"
HIERARCHY_PREFIX = "composition/service/"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fail(message: str) -> None:
    raise SystemExit(message)


def check(design_dir: Path) -> None:
    config = _load(design_dir / "config.json")
    body = config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        _fail(f"config missing {CONFIG_KEY}")
    top_name = str(config.get("top_name", "")).strip()
    if not top_name or top_name != design_dir.name:
        _fail("top_name must match the design directory")
    if int(body.get("remote_contexts", 0)) != 112:
        _fail("physical service must retain all 112 remote contexts")
    if int(body.get("packets_per_context", 0)) != 68:
        _fail("physical service must retain 68 packets per context")
    if str(body.get("hierarchy_area_prefix", "")).strip() != HIERARCHY_PREFIX:
        _fail("config hierarchy-area prefix mismatch")

    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        _fail("config proposal linkage is missing or incorrect")
    proposal_path = REPO_ROOT / str(links.get("proposal_path", ""))
    proposal = _load(proposal_path)
    if proposal.get("proposal_id") != PROPOSAL_ID or proposal.get("layer") != "layer1":
        _fail("linked proposal identity or layer is incorrect")

    verilog_dir = design_dir / "verilog"
    rtl_path = verilog_dir / "top.v"
    manifest = _load(verilog_dir / MANIFEST_NAME)
    rtl = rtl_path.read_text(encoding="utf-8")
    if manifest.get("top_name") != top_name:
        _fail("generated manifest top identity mismatch")
    if manifest.get("linked_proposal_id") != PROPOSAL_ID:
        _fail("generated manifest proposal linkage mismatch")
    if manifest.get("top_pin_bits") != 163:
        _fail("generated top must expose exactly 163 pins")
    pins = manifest.get("top_pin_inventory")
    if not isinstance(pins, dict) or pins.get("input_bits") != 35 or pins.get("output_bits") != 128:
        _fail("generated top pin inventory mismatch")
    if manifest.get("hierarchy_area_prefix") != HIERARCHY_PREFIX:
        _fail("generated hierarchy-area prefix mismatch")
    service = manifest.get("service_contract")
    expected_service = {
        "remote_contexts": 112,
        "packets_per_context": 68,
        "flits_per_packet": 8,
        "total_packets": 7616,
        "total_flits": 60928,
        "virtual_channel": 0,
        "endpoint_array": "noc_sram_packet_endpoint_array16",
        "mesh": "noc_segmented_mesh4x4",
        "private_mesh_optional": True,
        "producer_addresses_are_external": True,
        "completion_releases_endpoint_ownership": True,
    }
    if service != expected_service:
        _fail("generated service contract does not match canonical VC0 quantities")
    power = manifest.get("power_scope")
    if (
        not isinstance(power, dict)
        or not power.get("whole_harness_power_is_upper_bound")
        or power.get("stimulus_logic_is_dut_area") is not False
        or power.get("workload_activity_power_measured") is not False
    ):
        _fail("generated power-accounting scope is incomplete")

    required_modules = (
        top_name,
        "attention_shared_stream_context_service_ppa_activity_harness",
        "attention_shared_stream_context_service",
        "attention_shared_stream_context_admission",
        "attention_shared_stream_context_engine",
        "noc_sram_packet_endpoint_array16",
        "noc_sram_packet_endpoint",
        "noc_segmented_mesh4x4",
    )
    for module in required_modules:
        if f"module {module}" not in rtl:
            _fail(f"generated top is missing required module {module}")
    for fragment in (
        "input wire clk",
        "input wire rst_n",
        "input wire enable",
        "input wire [31:0] control",
        "output wire [127:0] observable",
        "attention_shared_stream_context_service #(",
        ".INTERNAL_MESH(INTERNAL_MESH)",
        "layer_expected_remote_contexts(8'd112)",
        "event_packet_count_w",
    ):
        if fragment not in rtl:
            _fail(f"generated top is missing required contract fragment: {fragment}")

    records = manifest.get("source_files")
    if not isinstance(records, list) or not records:
        _fail("generated source inventory is missing")
    for record in records:
        if not isinstance(record, dict):
            _fail("generated source inventory contains a non-object")
        relative = str(record.get("path", "")).strip()
        expected_hash = str(record.get("sha256", "")).strip()
        path = REPO_ROOT / relative
        if not relative or not path.is_file() or len(expected_hash) != 64:
            _fail(f"invalid source inventory record: {record}")
        if _sha256(path) != expected_hash:
            _fail(f"source hash changed for {relative}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--post-sweep", action="store_true")
    args = parser.parse_args(argv)
    if args.post_sweep:
        attach_hierarchy_reports(
            args.design_dir,
            prefix=HIERARCHY_PREFIX,
            precheck=check,
        )
    else:
        check(args.design_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
