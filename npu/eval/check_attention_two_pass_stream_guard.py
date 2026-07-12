#!/usr/bin/env python3
"""Guard the scalable external-memory two-pass attention engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "config": args.design_dir / "config.json",
        "generated": args.design_dir / "verilog" / "config.json",
        "manifest": args.design_dir / "verilog" / "attention_two_pass_stream_manifest.json",
        "top": args.design_dir / "verilog" / "top.v",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"missing two-pass stream artifact: {path}")
    config = json.loads(paths["config"].read_text(encoding="utf-8"))
    if config != json.loads(paths["generated"].read_text(encoding="utf-8")):
        raise SystemExit("generated config does not match source config")
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    body = config.get("attention_two_pass_stream") or {}
    if manifest.get("semantic_profile") != "q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max":
        raise SystemExit("unexpected stream semantic profile")
    for key in ("max_blocks", "div_lanes_per_cycle"):
        if int(manifest.get(key, 0)) != int(body.get(key, 0)):
            raise SystemExit(f"manifest {key} does not match config")
    divider_impl = str(body.get("divider_impl", "combinational"))
    if manifest.get("divider_impl") != divider_impl:
        raise SystemExit("manifest divider_impl does not match config")
    if manifest.get("score_storage") != "external_ready_valid_sram":
        raise SystemExit("score storage must use external ready/valid SRAM")
    text = paths["top"].read_text(encoding="utf-8")
    top_name = str(config.get("top_name") or "")
    if not re.search(rf"^module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"missing top module {top_name}")
    required = (
        "score_write_valid",
        "score_write_ready",
        "score_read_req_valid",
        "score_read_req_ready",
        "replay_valid",
        "replay_ready",
        "default: exp_lut = 16'd0",
        "numerator_accum",
    )
    if divider_impl == "iterative_restoring":
        required += ("DIV_ITER", "div_remainder", "div_bit_count", "div_trial_remainder")
        if "final_magnitude / exp_sum_accum" in text:
            raise SystemExit("iterative stream RTL must not contain a combinational final divider")
    else:
        required += ("final_magnitude / exp_sum_accum", "DIV_LANES")
    for token in required:
        if token not in text:
            raise SystemExit(f"stream RTL missing semantic token: {token}")
    for forbidden in ("score_mem", "value_mem", "result_weights", "result_hash"):
        if forbidden in text:
            raise SystemExit(f"stream RTL contains forbidden abstraction token: {forbidden}")
    print(f"OK: two-pass stream guard passed for {args.design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
