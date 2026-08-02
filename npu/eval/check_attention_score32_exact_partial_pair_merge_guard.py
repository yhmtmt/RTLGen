#!/usr/bin/env python3
"""Strict generated RTL guard for standalone folded score32 exact partial pair merges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_pair_merge_folded import (
    FACTORED_H33_L64_MUL_EXACT,
    GENERIC_SCALE_DIVIDER_EXACT,
    MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT,
    PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
    PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES,
    PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES,
    generate,
)

_PPA_SWEEP_FLOW_PARAMS = {
    "CLOCK_PERIOD": [8.0],
    "DIE_AREA": ["0 0 1500 1500"],
    "CORE_AREA": ["50 50 1450 1450"],
    "IO_PLACER_H": ["metal3 metal5"],
    "IO_PLACER_V": ["metal4 metal6"],
    "PLACE_DENSITY": [0.3],
    "PLACE_PINS_ARGS": ["-min_distance 1"],
    "SYNTH_HIERARCHICAL": [1],
}
_PPA_SWEEP_TAG_PREFIX_BY_DIVIDER_IMPL = {
    GENERIC_SCALE_DIVIDER_EXACT: "attention_score32_exact_partial_pair_merge_sharedscale_v1",
    MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT: "attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1",
}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(mapping: dict[str, object], key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_pair_merge_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_partial_pair_merge_folded_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated pair-merge artifacts do not match current generator output: {relative_name}")


def _validate_sweep(*, sweep_path: Path, scale_divider_impl: str) -> None:
    sweep = _load_json(sweep_path)
    expected_tag_prefix = _PPA_SWEEP_TAG_PREFIX_BY_DIVIDER_IMPL[scale_divider_impl]
    if sweep.get("tag_prefix") != expected_tag_prefix:
        raise SystemExit(f"pair-merge PPA sweep tag_prefix must be {expected_tag_prefix}")
    if sweep.get("flow_params") != _PPA_SWEEP_FLOW_PARAMS:
        raise SystemExit("pair-merge PPA sweep flow_params do not match the checked-in contract")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--sweep", type=Path, default=None)
    args = ap.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = (args.config or (design_dir / "config.json")).resolve()
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_partial_pair_merge_folded_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact partial pair-merge artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_partial_pair_merge_folded")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_partial_pair_merge_folded object")
    lane_parallelism = int(body.get("lane_parallelism", 0))
    scale_divider_impl_explicit = "scale_divider_impl" in body
    scale_divider_impl = str(body.get("scale_divider_impl", GENERIC_SCALE_DIVIDER_EXACT))
    if lane_parallelism != 1:
        raise SystemExit("lane_parallelism must be 1 for the shared-scale exact pair merge")
    if scale_divider_impl not in _PPA_SWEEP_TAG_PREFIX_BY_DIVIDER_IMPL:
        supported = ", ".join(sorted(_PPA_SWEEP_TAG_PREFIX_BY_DIVIDER_IMPL))
        raise SystemExit(f"scale_divider_impl must be one of: {supported}")
    if args.sweep is not None:
        _validate_sweep(sweep_path=args.sweep.resolve(), scale_divider_impl=scale_divider_impl)

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_pair_merge_folded.py",
        "semantic_profile": "score32_online_exact_partial_pair_merge_folded_sharedscale_v1",
        "numerical_semantics": "score32_online_exact_partial_pair_merge_v1",
        "lane_parallelism": 1,
        "implementation_style": "shared_single_scale_folded_exact_v1",
        "shared_signed_scale_datapaths": 1,
        "shared_unsigned_scale_datapaths": 1,
        "pair_capture_to_output_latency_cycles": PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_to_output_latency_cycles": PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_interval_cycles": PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES,
        "service_cycle_definition": "active_edge_preupdate_handshake_v1",
        "output_cycle_event": "first_out_valid_handshake_opportunity",
        "exp_scale_impl": FACTORED_H33_L64_MUL_EXACT,
    }
    if scale_divider_impl_explicit:
        expected_manifest["scale_divider_impl"] = scale_divider_impl
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    if not scale_divider_impl_explicit and "scale_divider_impl" in manifest:
        raise SystemExit("legacy absent-key config must not gain manifest scale_divider_impl")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    for token in (
        "localparam [2:0] PHASE_EXP_SUM_LEFT = 3'd1;",
        "localparam [2:0] PHASE_EXP_SUM_RIGHT = 3'd2;",
        "localparam [2:0] PHASE_LANE_LEFT = 3'd3;",
        "localparam [2:0] PHASE_LANE_RIGHT = 3'd4;",
        "active_scaled_left_exp_sum_q <= shared_unsigned_scaled_w;",
        "active_scaled_left_lane_q <= shared_signed_scaled_w;",
        "lane_merged_r = sat_add_signed41(active_scaled_left_lane_q, shared_signed_scaled_w);",
        "assign left_ready = !left_hold_valid_q;",
        "assign right_ready = !right_hold_valid_q;",
    ):
        if token not in rtl:
            raise SystemExit(f"generated RTL missing semantic token: {token}")
    for function_name in ("scale_signed41", "scale_unsigned33"):
        call_count = len(re.findall(rf"\b{function_name}\s*\(", rtl))
        if call_count != 1:
            raise SystemExit(
                f"generated RTL must contain exactly one {function_name} invocation; found {call_count}"
            )
    if scale_divider_impl == GENERIC_SCALE_DIVIDER_EXACT:
        for token in (
            "quotient = product / 57'd16777215;",
            "quotient = product / 65'd16777215;",
        ):
            if token not in rtl:
                raise SystemExit(f"generated generic-divider RTL missing token: {token}")
    elif scale_divider_impl == MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT:
        for token in (
            "/ 57'd16777215",
            "/ 65'd16777215",
        ):
            if token in rtl:
                raise SystemExit(f"generated Mersenne-divider RTL must not contain generic division token: {token}")
        for token in (
            "function automatic [33:0] divide_mersenne24_u57;",
            "function automatic [41:0] divide_mersenne24_u65;",
            "if (chunk_sum >= 26'd33554430) correction = 2'd2;",
            "else if (chunk_sum >= 26'd16777215) correction = 2'd1;",
            "quotient = divide_mersenne24_u57(product);",
            "quotient = divide_mersenne24_u65(product);",
        ):
            if token not in rtl:
                raise SystemExit(f"generated Mersenne-divider RTL missing token: {token}")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_partial_pair_merge_v1",
                "lane_parallelism": lane_parallelism,
                "pair_capture_to_output_latency_cycles": PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
