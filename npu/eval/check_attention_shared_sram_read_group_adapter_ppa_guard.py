#!/usr/bin/env python3
"""Guard generated shared-SRAM read-adapter physical harness artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


CONFIG_KEY = "attention_shared_sram_read_group_adapter_ppa_harness"
MANIFEST_NAME = "attention_shared_sram_read_group_adapter_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_sram_read_group_adapter_ppa_v1"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def check(design_dir: Path) -> None:
    config = _load(design_dir / "config.json")
    body = config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        raise SystemExit(f"config missing {CONFIG_KEY}")
    top_name = str(config.get("top_name") or "").strip()
    if top_name != design_dir.name:
        raise SystemExit("top_name must match the design directory")
    beat_width = int(body.get("beat_width", 0))
    group_slots = int(body.get("group_slots", 0))
    if beat_width not in {256, 512} or group_slots not in {1, 2}:
        raise SystemExit("unsupported adapter geometry")
    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        raise SystemExit("config proposal linkage is missing or incorrect")

    verilog_dir = design_dir / "verilog"
    rtl = (verilog_dir / "top.v").read_text(encoding="utf-8")
    manifest = _load(verilog_dir / MANIFEST_NAME)
    expected = {
        "top_name": top_name,
        "beat_width": beat_width,
        "group_slots": group_slots,
        "segments_per_macro_read": 1024 // beat_width,
        "buffer_payload_bits": 1024 * group_slots,
        "payload_reset_required": False,
        "linked_proposal_id": PROPOSAL_ID,
        "full_capacity_macro_area_included": False,
        "synthetic_response_profile": "metadata_lane_replicated_v1",
        "synthetic_response_generator_is_dut": False,
        "narrow_io_harness_overhead_included": True,
        "response_bus_retention": "kept_full_bus_endpoint_lane_fold_v1",
    }
    mismatches = {key: (manifest.get(key), value) for key, value in expected.items() if manifest.get(key) != value}
    if mismatches:
        raise SystemExit(f"generated harness manifest mismatch: {mismatches}")
    required = (
        "attention_shared_sram_read_group_adapter",
        f".BEAT_W(BEAT_W)",
        f"localparam integer BEAT_W = {beat_width};",
        f"localparam integer GROUP_SLOTS = {group_slots};",
        '(* keep = "true" *) reg [MACRO_W-1:0] slot_data',
        "build_macro_word",
        "build_macro_word = {32{lane}};",
        "fold_beat",
        '(* keep = "true" *) wire [BEAT_W-1:0] rsp_data;',
        "fold_beat = value[31:0] ^ value[BEAT_W-1 -: 32];",
        "access_reduction_proven",
    )
    missing = [fragment for fragment in required if fragment not in rtl]
    if missing:
        raise SystemExit(f"generated physical harness is incomplete: {missing}")
    forbidden = (
        "slot_data[reset_i] <=",
        "32'h9e37_79b9 *",
    )
    present = [fragment for fragment in forbidden if fragment in rtl]
    if present:
        raise SystemExit(f"generated physical harness contains forbidden payload logic: {present}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    check(args.design_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
