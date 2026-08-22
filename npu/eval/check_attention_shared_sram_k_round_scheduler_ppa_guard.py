#!/usr/bin/env python3
"""Guard generated shared-SRAM K-round scheduler physical artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


CONFIG_KEY = "attention_shared_sram_k_round_scheduler_ppa_harness"
MANIFEST_NAME = "attention_shared_sram_k_round_scheduler_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1"


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
    expected_geometry = {
        "banks": 17,
        "words_per_group": 128,
        "dimension_groups": 8,
        "dimensions_per_group": 16,
    }
    for key, value in expected_geometry.items():
        if int(body.get(key, value)) != value:
            raise SystemExit(f"unsupported K-round geometry: {key}")
    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        raise SystemExit("config proposal linkage is missing or incorrect")

    verilog_dir = design_dir / "verilog"
    rtl = (verilog_dir / "top.v").read_text(encoding="utf-8")
    manifest = _load(verilog_dir / MANIFEST_NAME)
    expected_manifest = {
        "top_name": top_name,
        "semantic_profile": "attention_shared_sram_k_round_scheduler_logic_ppa_activity_v1",
        "banks": 17,
        "words_per_group": 128,
        "dimension_groups": 8,
        "rounds_per_group": 8,
        "dimensions_per_group": 16,
        "requests_per_command": 1024,
        "compute_beats_per_command": 1024,
        "window_storage_bits": 34816,
        "compute_boundary_bits": 1088,
        "full_capacity_macro_area_included": False,
        "shared_sram_access_energy_included": False,
        "external_hbm_dram_included": False,
        "activity_checksum_is_equivalence_proof": False,
        "synthetic_response_profile": "metadata_lane_replicated_v1",
        "synthetic_response_generator_is_dut": False,
        "narrow_io_harness_overhead_included": True,
        "linked_proposal_id": PROPOSAL_ID,
    }
    mismatches = {
        key: (manifest.get(key), value)
        for key, value in expected_manifest.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise SystemExit(f"generated harness manifest mismatch: {mismatches}")
    if hashlib.sha256(rtl.encode("utf-8")).hexdigest() != manifest.get(
        "generated_top_sha256"
    ):
        raise SystemExit("generated top hash does not match manifest")
    required = (
        "attention_shared_sram_k_round_scheduler",
        "module attention_shared_sram_k_round_bank",
        '(* keep = "true" *) reg [1023:0] buffer_mem0',
        '(* keep = "true" *) reg [1023:0] buffer_mem1',
        "build_word",
        "build_word = {16{{lane ^ 32'ha5a5_5a5a, lane}}};",
        "fold_compute",
        "output wire [31:0] activity_checksum",
        ".WORDS_PER_GROUP(128)",
        ".DIM_GROUPS(8)",
    )
    missing = [fragment for fragment in required if fragment not in rtl]
    if missing:
        raise SystemExit(f"generated physical harness is incomplete: {missing}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    check(args.design_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
