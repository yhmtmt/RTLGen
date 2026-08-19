#!/usr/bin/env python3
"""Guard exact shared-root storage macro physical-harness artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


_CONFIG_KEY = "attention_score32_exact_shared_root_storage_physical_harness"
_MANIFEST = "attention_score32_exact_shared_root_storage_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_attention_score32_exact_shared_root_storage_macro_ppa_v1"
_EXPECTED_MACROS = {2: 32, 4: 32, 8: 64, 15: 120}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def check(design_dir: Path) -> None:
    config = _load(design_dir / "config.json")
    body = config.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise SystemExit(f"config missing {_CONFIG_KEY}")
    banks = int(body.get("physical_banks", 0))
    if banks not in _EXPECTED_MACROS:
        raise SystemExit(f"unsupported physical_banks={banks}")
    top_name = str(config.get("top_name") or "").strip()
    if not top_name or top_name != design_dir.name:
        raise SystemExit("top_name must match the design directory")
    report_links = config.get("report_links")
    if not isinstance(report_links, dict) or report_links.get("proposal_id") != _PROPOSAL_ID:
        raise SystemExit("config proposal linkage is missing or incorrect")

    verilog_dir = design_dir / "verilog"
    rtl = (verilog_dir / "top.v").read_text(encoding="utf-8")
    manifest = _load(verilog_dir / _MANIFEST)
    macro = _load(verilog_dir / "macro_manifest.json")
    expected = _EXPECTED_MACROS[banks]
    if manifest.get("top_name") != top_name or manifest.get("physical_banks") != banks:
        raise SystemExit("generated harness manifest identity mismatch")
    if manifest.get("macro_count") != expected:
        raise SystemExit("generated harness macro count mismatch")
    if manifest.get("linked_proposal_id") != _PROPOSAL_ID:
        raise SystemExit("generated harness proposal linkage mismatch")
    if manifest.get("top_pin_bits") != 228:
        raise SystemExit("physical harness top-pin contract changed")
    if macro.get("module") != top_name or macro.get("blackboxes") != ["fakeram45_64x32"]:
        raise SystemExit("macro manifest module or blackbox mismatch")
    params = macro.get("manifest_params")
    if not isinstance(params, dict) or params.get("macro_count") != expected:
        raise SystemExit("macro manifest inventory mismatch")
    required_fragments = (
        ".USE_FAKERAM(1)",
        "local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric",
        "fakeram45_64x32 u_packet_mem",
        "read_pending_q",
        "folded_result_q",
    )
    missing = [fragment for fragment in required_fragments if fragment not in rtl]
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
