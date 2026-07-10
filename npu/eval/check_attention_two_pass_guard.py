#!/usr/bin/env python3
"""Guard bounded two-pass attention RTL semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.design_dir / "config.json"
    generated_config = args.design_dir / "verilog" / "config.json"
    manifest_path = args.design_dir / "verilog" / "attention_two_pass_manifest.json"
    top_path = args.design_dir / "verilog" / "top.v"
    for path in (config_path, generated_config, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing two-pass artifact: {path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config != json.loads(generated_config.read_text(encoding="utf-8")):
        raise SystemExit("generated config does not match source config")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("semantic_profile") != "q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max":
        raise SystemExit("unexpected two-pass semantic profile")
    body = config.get("attention_two_pass") or {}
    if int(manifest.get("block_count", 0)) != int(body.get("block_count", 0)):
        raise SystemExit("manifest block_count does not match config")
    if int(manifest.get("exp_sum_bits", 0)) != 33:
        raise SystemExit("two-pass exp sum must be 33 bits")
    if int(manifest.get("weighted_numerator_bits", 0)) != 41:
        raise SystemExit("two-pass weighted numerator must be 41 bits")
    text = top_path.read_text(encoding="utf-8")
    top_name = str(config.get("top_name") or "")
    if not re.search(rf"^module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"missing top module {top_name}")
    required = (
        "score_mem",
        "value_mem",
        "global_max",
        "exp_sum_accum",
        "numerator_accum",
        "default: exp_lut = 16'd0",
        "state == REPLAY",
        "final_magnitude / sum_next",
        "result_valid && result_ready",
    )
    for token in required:
        if token not in text:
            raise SystemExit(f"two-pass RTL missing semantic token: {token}")
    for forbidden in ("result_hash", "result_weights", "default: exp_lut = 16'd1"):
        if forbidden in text:
            raise SystemExit(f"two-pass RTL contains forbidden local-normalization token: {forbidden}")
    print(f"OK: two-pass guard passed for {args.design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
