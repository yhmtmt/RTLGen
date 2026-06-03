#!/usr/bin/env python3
"""Check dense GEMM tile generated RTL before PPA."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", required=True)
    args = parser.parse_args()

    design_dir = Path(args.design_dir)
    manifest_path = design_dir / "verilog" / "dense_gemm_tile_manifest.json"
    top_path = design_dir / "verilog" / "top.v"
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest: {manifest_path}")
    if not top_path.exists():
        raise SystemExit(f"missing generated RTL: {top_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    top_text = top_path.read_text(encoding="utf-8")
    expected_macs = int(manifest["macs_per_cycle"])
    top_name = str(manifest["top_name"])
    instance_count = len(re.findall(r"\bu_mac_\d{4}\s*\(", top_text))
    if instance_count != expected_macs:
        raise SystemExit(f"MAC instance count mismatch: expected {expected_macs}, found {instance_count}")
    if f"module {top_name} " not in top_text:
        raise SystemExit(f"missing top module {top_name}")
    if "result_hash <=" not in top_text:
        raise SystemExit("result_hash is not updated")
    folded_match = re.search(r"\bassign\s+folded_result\s*=\s*(.*?);", top_text, flags=re.DOTALL)
    if folded_match is None:
        raise SystemExit("missing folded_result assignment")
    folded_expr = folded_match.group(1)

    missing_outputs: list[str] = []
    pipeline_stages = int(manifest.get("pipeline_stages", 0))
    for idx in range(expected_macs):
        token = f"mac_r_{idx:04d}_q" if pipeline_stages >= 2 else f"mac_r_{idx:04d}"
        if token not in folded_expr:
            missing_outputs.append(token)
    if missing_outputs:
        raise SystemExit(f"MAC outputs are not visible in result fold: {missing_outputs[:8]}")

    print(
        json.dumps(
            {
                "ok": True,
                "design_dir": str(design_dir),
                "top_name": top_name,
                "macs_per_cycle": expected_macs,
                "instance_count": instance_count,
                "pipeline_stages": pipeline_stages,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
