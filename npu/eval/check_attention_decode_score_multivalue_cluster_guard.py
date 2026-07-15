#!/usr/bin/env python3
"""Validate the shared-score multi-value decode cluster before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args()
    design_dir = args.design_dir.resolve()
    config = json.loads((design_dir / "config.json").read_text(encoding="utf-8"))
    rtl_dir = design_dir / "verilog"
    manifest = json.loads(
        (rtl_dir / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    errors: list[str] = []
    expected_top = str(config.get("top_name") or "")
    if manifest.get("top_name") != expected_top:
        errors.append("manifest top_name does not match config")
    expected = {
        "value_slices": 16,
        "value_dimensions": 128,
        "score_passes_per_command": 1,
        "score_writes_per_block": 1,
        "score_reads_per_block": 1,
        "value_reads_per_block": 16,
        "result_beats_per_command": 16,
        "result_value_bits_per_beat": 320,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"manifest {key} must be {value}")
    required = (
        "value_read_req_slice",
        "value_response_slice",
        "result_slice",
        "result_last",
        "numerator_accum [0:VALUE_DIMS-1]",
        "score_read_req_valid",
        "score_replay_valid",
    )
    for token in required:
        if token not in rtl:
            errors.append(f"RTL missing {token}")
    if re.search(r"\b(hash|sha256|checksum)\b", rtl, flags=re.IGNORECASE):
        errors.append("measured RTL must not contain equivalence hash logic")
    if "result_value [5119:0]" in rtl or "output wire [5119:0]" in rtl:
        errors.append("result must remain a streamed 320-bit slice, not a 5120-bit port")
    if "/ exp_sum_accum" in rtl or "% exp_sum_accum" in rtl:
        errors.append("iterative divider RTL must not infer arithmetic division")
    if errors:
        raise SystemExit("; ".join(errors))
    print(
        json.dumps(
            {
                "design": expected_top,
                "guard": "attention_decode_score_multivalue_cluster_v1",
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
