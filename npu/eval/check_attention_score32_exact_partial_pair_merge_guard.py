#!/usr/bin/env python3
"""Strict generated RTL guard for standalone folded score32 exact partial pair merges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
    PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES,
    PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES,
    generate,
)

_PPA_SWEEP_TAG_PREFIX = "attention_score32_exact_partial_pair_merge_sharedscale_v1"
_PPA_SWEEP_FLOW_PARAMS = {
    "CLOCK_PERIOD": [8.0],
    "DIE_AREA": ["0 0 1500 1500"],
    "CORE_AREA": ["50 50 1450 1450"],
    "PLACE_DENSITY": [0.3],
    "SYNTH_HIERARCHICAL": [1],
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
            "attention_score32_online_state_merge_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated pair-merge artifacts do not match current generator output: {relative_name}")


def _validate_sweep(*, sweep_path: Path) -> None:
    sweep = _load_json(sweep_path)
    if sweep.get("tag_prefix") != _PPA_SWEEP_TAG_PREFIX:
        raise SystemExit(f"pair-merge PPA sweep tag_prefix must be {_PPA_SWEEP_TAG_PREFIX}")
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
    manifest_path = rtl_dir / "attention_score32_online_state_merge_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact partial pair-merge artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")
    if args.sweep is not None:
        _validate_sweep(sweep_path=args.sweep.resolve())

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_online_state_merge")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_online_state_merge object")
    lane_parallelism = int(body.get("lane_parallelism", 0))
    if lane_parallelism != 1:
        raise SystemExit("lane_parallelism must be 1 for the shared-scale exact pair merge")

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_online_state_merge.py",
        "semantic_profile": "score32_online_exact_partial_pair_merge_v1",
        "lane_parallelism": 1,
        "implementation_style": "shared_single_scale_folded_exact_v1",
        "shared_signed_scale_datapaths": 1,
        "shared_unsigned_scale_datapaths": 1,
        "pair_capture_to_output_latency_cycles": PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_to_output_latency_cycles": PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_interval_cycles": PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES,
        "exp_scale_impl": FACTORED_H33_L64_MUL_EXACT,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    for token in (
        "localparam [2:0] PHASE_EXP_SUM_LEFT = 3'd1;",
        "localparam [2:0] PHASE_EXP_SUM_RIGHT = 3'd2;",
        "localparam [2:0] PHASE_LANE_LEFT = 3'd3;",
        "localparam [2:0] PHASE_LANE_RIGHT = 3'd4;",
        "active_scaled_left_exp_sum_q <= scale_unsigned33(active_left_exp_sum_q, active_left_scale_q);",
        "active_scaled_left_lane_q <= scale_signed41(",
        "lane_merged_r = sat_add_signed41(active_scaled_left_lane_q, scale_signed41(lane_right_r, active_right_scale_q));",
        "assign left_ready = !left_hold_valid_q;",
        "assign right_ready = !right_hold_valid_q;",
    ):
        if token not in rtl:
            raise SystemExit(f"generated RTL missing semantic token: {token}")

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
