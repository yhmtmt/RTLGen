#!/usr/bin/env python3
"""Strict generated RTL guard for standalone score32 exact root finalizers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


_SUPPORTED_LANES = {1, 2, 4, 8}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_selected_config(*, design_dir: Path, selected: Path | None) -> Path:
    config_path = selected or (design_dir / "config.json")
    config_path = config_path.resolve()
    if not config_path.exists():
        raise SystemExit(f"missing config: {config_path}")
    try:
        relative_path = config_path.relative_to(design_dir)
    except ValueError as exc:
        raise SystemExit(f"selected config must live under design-dir: {config_path}") from exc
    if len(relative_path.parts) != 1:
        raise SystemExit(f"selected config must be a direct child of design-dir, got: {relative_path.as_posix()}")
    return config_path


def _require(mapping: dict[str, object], key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def _strip_comments(text: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", no_block)


def _contains_operator_division(text: str) -> bool:
    stripped = _strip_comments(text)
    return re.search(r"(?<![*/])/(?![/*])", stripped) is not None


def _require_token(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"{label} missing semantic token: {token}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_root_finalizer_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact root finalizer artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_root_finalizer")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_root_finalizer object")
    divider_lanes = int(body.get("divider_lanes", 0))
    if divider_lanes not in _SUPPORTED_LANES:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, 8")
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
        "semantic_profile": "score32_online_exact_root_finalizer_iterdiv_v1",
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "physical_divider_lanes": divider_lanes,
        "divider_groups_per_beat": 8 // divider_lanes,
        "divider_iterations_per_group": 57,
        "divider_cycles_per_beat": (8 // divider_lanes) * 57,
        "input_value_bits_per_beat": 328,
        "output_value_bits_per_beat": 320,
        "result_interface": "ready_valid_exact_finalized_slice_stream",
        "protocol_error_conditions": ["last_semantics", "exp_sum_zero", "final_value_overflow"],
        "final_divider_embodied": True,
        "equivalence_hash": False,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"^\s*module\s+{re.escape(top_name)}\b", rtl, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")
    for token in (
        f"localparam integer DIVIDER_LANES = {divider_lanes};",
        "localparam integer DIVIDE_ITERATIONS = 57;",
        "localparam integer DIVIDEND_BITS = 57;",
        "assign in_ready = (state_q == IDLE) && !out_valid_q;",
        "assign out_valid = out_valid_q;",
        "assign protocol_error = protocol_error_q;",
        "accepted_count <= accepted_count + 1'b1;",
        "completed_count <= completed_count + 1'b1;",
        "if (out_valid_q && out_ready) begin",
        "rounded_dividend =",
    ):
        _require_token(rtl, token, "generated RTL")
    for token in (
        "input  wire         in_valid,",
        "output wire         in_ready,",
        "output wire         out_valid,",
        "input  wire         out_ready,",
        "output reg  [31:0]  accepted_count,",
        "output reg  [31:0]  completed_count,",
        "output reg  [31:0]  cycle_count,",
        "output wire         protocol_error",
    ):
        _require_token(rtl, token, "generated RTL")
    if _contains_operator_division(rtl):
        raise SystemExit("generated RTL must not contain combinational division operators")

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_root_finalizer_v1",
                "divider_lanes": divider_lanes,
                "divider_iterations_per_group": 57,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
