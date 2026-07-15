#!/usr/bin/env python3
"""Guard the exact decode-score local cluster before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "config": args.design_dir / "config.json",
        "generated": args.design_dir / "verilog" / "config.json",
        "manifest": args.design_dir / "verilog" / "attention_decode_score_local_cluster_manifest.json",
        "top": args.design_dir / "verilog" / "top.v",
        "macro_manifest": args.design_dir / "macro_manifest.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"missing decode-score local-cluster artifact: {path}")

    config = _load(paths["config"])
    if config != _load(paths["generated"]):
        raise SystemExit("generated config does not match source config")
    body = config.get("attention_decode_score_local_cluster")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_decode_score_local_cluster object")
    manifest = _load(paths["manifest"])
    if manifest.get("semantic_profile") != "decode_m1x8_score_sram_two_pass_iterdiv_v1":
        raise SystemExit("unexpected local-cluster semantic profile")
    if int(manifest.get("max_blocks", 0)) != int(body.get("max_blocks", 0)):
        raise SystemExit("manifest max_blocks does not match config")
    if manifest.get("score_tile_result_mode") != "packed_score_row":
        raise SystemExit("local cluster must use the exact packed M1x8 score interface")
    if manifest.get("divider_impl") != "iterative_restoring":
        raise SystemExit("local cluster must use the measured iterative-restoring divider")
    if int(manifest.get("score_bank_macro_count", 0)) != 56:
        raise SystemExit("local cluster must instantiate all 56 score-bank macros")
    if manifest.get("value_replay") != "external_ready_valid_address_matched":
        raise SystemExit("value replay must use an address-matched ready/valid interface")
    scale_lanes = int(manifest.get("score_scale_lanes_per_cycle", 0))
    if scale_lanes != int(body.get("score_scale_lanes_per_cycle", 0)) or scale_lanes not in {1, 2, 4, 8}:
        raise SystemExit("manifest score scaler lanes do not match the supported config")
    scaling = manifest.get("score_scaling")
    if not isinstance(scaling, dict) or scaling != {
        "metadata_source": "external_command_multiplier_shift",
        "product_bits": 64,
        "rounding": "symmetric_magnitude_round_to_nearest",
        "saturation": "signed_s32",
        "shift_bits": 6,
        "shift_zero_valid": True,
    }:
        raise SystemExit("local cluster score scaling contract is incomplete or unexpected")

    macro_manifest = _load(paths["macro_manifest"])
    if "fakeram45_2048x39" not in macro_manifest.get("blackboxes", []):
        raise SystemExit("macro manifest is missing fakeram45_2048x39")
    if len(macro_manifest.get("additional_lefs", [])) != 1 or len(macro_manifest.get("additional_libs", [])) != 1:
        raise SystemExit("local cluster must carry one FakeRAM LEF and Liberty view")

    text = paths["top"].read_text(encoding="utf-8", errors="replace")
    top_name = str(config.get("top_name") or "")
    if not re.search(rf"^module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")
    required = (
        "u_score_tile",
        "u_score_bank",
        "u_two_pass",
        "value_req_valid",
        "value_req_ready",
        "value_req_addr",
        "value_rsp_valid",
        "value_rsp_ready",
        "value_rsp_matrix",
        "score_response_valid",
        "value_response_valid",
        "protocol_error",
        "result_global_max",
        "result_exp_sum",
        "result_value",
        "DIV_ITER",
        "command_score_multiplier",
        "command_score_shift",
        "command_block_count_valid",
        "active_block_count_q",
        "assign two_pass_fill_score_row = scaled_score_row_q",
    )
    for token in required:
        if token not in text:
            raise SystemExit(f"local-cluster RTL missing semantic token: {token}")
    if text.count("fakeram45_2048x39 u_group_") != 56:
        raise SystemExit("local-cluster RTL does not contain exactly 56 score-bank macro instances")
    for forbidden in (
        "result_hash",
        "equivalence_hash",
        "final_magnitude / exp_sum_accum",
        ".fill_score_row(tile_result_score_row)",
    ):
        if forbidden in text:
            raise SystemExit(f"local-cluster RTL contains forbidden abstraction token: {forbidden}")

    print(f"OK: decode-score local-cluster guard passed for {args.design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
