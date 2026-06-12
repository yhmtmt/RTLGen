#!/usr/bin/env python3
"""Check generated composed dual-stream attention RTL before PPA."""

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
    manifest_path = design_dir / "verilog" / "attention_dual_stream_composed_manifest.json"
    top_path = design_dir / "verilog" / "top.v"
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest: {manifest_path}")
    if not top_path.exists():
        raise SystemExit(f"missing generated RTL: {top_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    top_text = top_path.read_text(encoding="utf-8")
    top_name = str(manifest["top_name"])
    total_macs = int(manifest["total_macs"])
    streams = int(manifest["streams"])
    if streams != 2:
        raise SystemExit(f"expected 2 streams, found {streams}")
    if f"module {top_name} " not in top_text:
        raise SystemExit(f"missing top module {top_name}")

    mac_instances = len(re.findall(r"\bu_mac_\d{4}\s*\(", top_text))
    if mac_instances != total_macs:
        raise SystemExit(f"MAC instance count mismatch: expected {total_macs}, found {mac_instances}")
    value_instances = len(re.findall(r"\bu_value_stream_\d+\s*\(", top_text))
    if value_instances != 2:
        raise SystemExit(f"value stream count mismatch: expected 2, found {value_instances}")
    if len(re.findall(r"\bu_softmax\s*\(", top_text)) != 1:
        raise SystemExit("expected exactly one shared softmax instance")
    if "stream_buf_0" not in top_text or "stream_buf_1" not in top_text:
        raise SystemExit("missing dual stream buffer registers")
    if "result_hash <=" not in top_text:
        raise SystemExit("result_hash is not updated")

    fold_match = re.search(r"\bwire\s+\[31:0\]\s+compute_fold\s*=\s*(.*?);", top_text, flags=re.DOTALL)
    if fold_match is None:
        raise SystemExit("missing compute_fold assignment")
    fold_expr = fold_match.group(1)
    missing_macs = [f"mac_r_{idx:04d}" for idx in range(total_macs) if f"mac_r_{idx:04d}" not in fold_expr]
    if missing_macs:
        raise SystemExit(f"MAC outputs are not visible in compute fold: {missing_macs[:8]}")
    for token in ("softmax_weight_hash", "value_hash_0", "value_hash_1", "value_accum_0", "value_accum_1"):
        if token not in top_text:
            raise SystemExit(f"missing result visibility token: {token}")

    print(
        json.dumps(
            {
                "ok": True,
                "design_dir": str(design_dir),
                "top_name": top_name,
                "streams": streams,
                "total_macs": total_macs,
                "value_streams": value_instances,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
