#!/usr/bin/env python3
"""Guard generated exact K ingress transpose physical artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


CONFIG_KEY = "attention_score32_exact_kv_key_ingress_ppa_harness"
MANIFEST_NAME = "attention_score32_exact_kv_key_ingress_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_score32_exact_kv_key_ingress_ppa_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]


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
    architecture = str(body.get("architecture") or "").strip()
    producers = int(body.get("producers", 0))
    kv_head = int(body.get("kv_head", -1))
    if architecture not in {"one_buffer_serial", "pingpong_wide_auto"}:
        raise SystemExit("unsupported K ingress architecture")
    if producers not in {53, 54} or kv_head not in range(4):
        raise SystemExit("unsupported K ingress p53/p54 geometry")
    links = config.get("report_links")
    if not isinstance(links, dict) or links.get("proposal_id") != PROPOSAL_ID:
        raise SystemExit("config proposal linkage is missing or incorrect")

    verilog_dir = design_dir / "verilog"
    rtl = (verilog_dir / "top.v").read_text(encoding="utf-8")
    manifest = _load(verilog_dir / MANIFEST_NAME)
    expected = {
        "top_name": top_name,
        "semantic_profile": "attention_score32_exact_kv_key_ingress_logic_ppa_activity_v1",
        "architecture": architecture,
        "producers": producers,
        "kv_head": kv_head,
        "canonical_ingress_flits": 4096,
        "output_beats": 8192 if architecture == "one_buffer_serial" else 4096,
        "transpose_storage_bits": 16384 if architecture == "one_buffer_serial" else 32768,
        "full_k_stage_macro_area_included": False,
        "full_k_stage_macro_energy_included": False,
        "external_hbm_dram_included": False,
        "activity_checksum_is_equivalence_proof": False,
        "narrow_io_harness_overhead_included": True,
        "linked_proposal_id": PROPOSAL_ID,
        "top_pin_bits": 197,
    }
    mismatches = {
        key: (manifest.get(key), value)
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise SystemExit(f"generated harness manifest mismatch: {mismatches}")
    if hashlib.sha256(rtl.encode("utf-8")).hexdigest() != manifest.get(
        "generated_top_sha256"
    ):
        raise SystemExit("generated top hash does not match manifest")
    source_path = REPO_ROOT / str(manifest.get("source_rtl") or "")
    if not source_path.is_file():
        raise SystemExit("manifest source RTL is missing")
    normalized_source = source_path.read_text(encoding="utf-8").rstrip() + "\n"
    if hashlib.sha256(normalized_source.encode("utf-8")).hexdigest() != manifest.get(
        "source_sha256"
    ):
        raise SystemExit("source RTL hash does not match manifest")
    required = [
        f"module {top_name}",
        "input wire [31:0] seed",
        "output wire [31:0] activity_checksum",
        "fold_output",
        "ingress_count_q < 32'd4096",
        ".ingress_byte_valid(32'hffff_ffff)",
    ]
    if architecture == "one_buffer_serial":
        required.extend(
            [
                "module attention_score32_exact_kv_key_single_buffer_transpose",
                ".target_valid(target_pending_q)",
                "output_count_q == 32'd8191",
            ]
        )
    else:
        required.extend(
            [
                "module attention_score32_exact_kv_key_pingpong_transpose",
                "line_data_mem [0:1][0:63]",
                "output_count_q == 32'd4095",
            ]
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
