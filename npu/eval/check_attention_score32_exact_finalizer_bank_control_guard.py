#!/usr/bin/env python3
"""Strict generated RTL guard for standalone exact finalizer bank control."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_finalizer_bank_control import generate
from npu.sim.perf.attention_exact_partial import (
    FINALIZER_CONTROL_TRANSACTION_ID_BITS,
    HEAD_ID_BITS,
    exact_finalizer_bank_control_service_manifest,
)

_SUPPORTED_LANES = {1, 2, 4, 8}
_PPA_SWEEP_TAG_PREFIX = "attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1"
_PPA_SWEEP_FLOW_PARAMS = {
    "CLOCK_PERIOD": [8.0],
    "DIE_AREA": ["0 0 1600 1600"],
    "CORE_AREA": ["50 50 1550 1550"],
    "PLACE_DENSITY": [0.3],
    "SYNTH_HIERARCHICAL": [1],
}
_PPA_SWEEP_ALLOWED_BANKS = {1, 4, 8, 16, 32, 59}


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


def _require_token(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"{label} missing semantic token: {token}")


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _extract_module(rtl: str, module_name: str) -> str:
    pattern = re.compile(rf"module\s+{re.escape(module_name)}\b.*?endmodule\s*", re.DOTALL)
    match = pattern.search(rtl)
    if match is None:
        raise SystemExit(f"generated RTL does not define top module {module_name}")
    return match.group(0)


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_finalizer_bank_control_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in (
            "top.v",
            "config.json",
            "attention_score32_exact_finalizer_bank_control_manifest.json",
        ):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {relative_name}")


def _validate_ppa_sweep(*, config: dict[str, object], sweep_path: Path) -> None:
    if not sweep_path.is_file():
        raise SystemExit(f"missing sweep: {sweep_path}")
    sweep = _load_json(sweep_path)
    if sweep.get("tag_prefix") != _PPA_SWEEP_TAG_PREFIX:
        raise SystemExit(f"finalizer bank-control sweep tag_prefix must be {_PPA_SWEEP_TAG_PREFIX}")
    if sweep.get("flow_params") != _PPA_SWEEP_FLOW_PARAMS:
        raise SystemExit("finalizer bank-control sweep flow_params do not match the checked-in control contract")
    body = config.get("attention_score32_exact_finalizer_bank_control")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_finalizer_bank_control object")
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))
    if divider_lanes != 8 or finalizer_banks not in _PPA_SWEEP_ALLOWED_BANKS:
        raise SystemExit(
            "finalizer bank-control sweep membership requires divider_lanes == 8 and finalizer_banks in "
            f"{sorted(_PPA_SWEEP_ALLOWED_BANKS)}"
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--sweep", type=Path, default=None)
    args = ap.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / "attention_score32_exact_finalizer_bank_control_manifest.json"
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact finalizer bank-control artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")
    if args.sweep is not None:
        _validate_ppa_sweep(config=config, sweep_path=args.sweep.resolve())

    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    body = config.get("attention_score32_exact_finalizer_bank_control")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_score32_exact_finalizer_bank_control object")
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    divider_lanes = int(body.get("divider_lanes", 0))
    finalizer_banks = int(body.get("finalizer_banks", 0))
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes not in _SUPPORTED_LANES:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, 8")
    if finalizer_banks < 1 or finalizer_banks > 64:
        raise SystemExit("finalizer_banks must be in [1, 64]")

    bank_id_bits = _clog2(finalizer_banks)
    service_manifest = exact_finalizer_bank_control_service_manifest(
        heads=32,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
    )
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_finalizer_bank_control.py",
        "semantic_profile": "score32_online_exact_finalizer_bank_control_v1",
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
        "result_interface": "tree_transaction_issue_to_ordered_banked_transaction_retire_stream",
        "transaction_id_bits": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "order_fifo_depth": finalizer_banks,
        "order_fifo_entry_bits": bank_id_bits,
        "order_fifo_storage_bits": finalizer_banks * bank_id_bits,
        "ordering_contract": "single_bank_id_fifo_exact_issue_order_one_transaction_per_entry",
        "dispatch_policy": "round_robin_no_alternate_ready_scan",
        "control_only_embodied": True,
        "bank_arithmetic_embodied": False,
        "tree_payload_fanout_embodied": False,
        "root_payload_mux_embodied": False,
        "equivalence_hash": False,
        "macro_eval_excludes_io_pads": True,
        "exact_service_model_cycle_equivalence": True,
        "service_model": service_manifest,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    top_module = _extract_module(rtl, top_name)
    for token in (
        f"localparam integer TRANSACTION_ID_BITS = {FINALIZER_CONTROL_TRANSACTION_ID_BITS};",
        f"localparam integer FINALIZER_BANKS = {finalizer_banks};",
        f"localparam integer BANK_ID_BITS = {bank_id_bits};",
        "wire order_fifo_dequeue_fire_w = root_valid && root_ready;",
        "wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;",
        "wire tree_ready_w = dispatch_bank_in_ready_r && order_fifo_enqueue_ready_w;",
        "wire same_bank_replace_w =",
        "order_fifo_bank_mem[order_fifo_tail_q] <= dispatch_bank_q;",
        "order_fifo_tid_mem[order_fifo_tail_q] <= tree_transaction_id;",
        "bank_outstanding_q[dispatch_bank_q] <= 1'b1;",
        "if (head_return_transaction_id_r != order_fifo_head_transaction_id_w) begin",
        "if (!same_bank_replace_w) begin",
        "dispatch_stall_cycles_q <= dispatch_stall_cycles_q + 1'b1;",
        "assign root_transaction_id = order_fifo_head_transaction_id_w;",
        "assign protocol_error = order_protocol_error_q;",
    ):
        _require_token(top_module, token, "generated RTL")
    for forbidden in (
        "tree_head_id",
        "tree_exp_sum",
        "tree_slice",
        "tree_last",
        "tree_value",
        "bank_in_head_id",
        "bank_in_exp_sum",
        "bank_in_slice",
        "bank_in_last",
        "bank_in_value",
        "bank_out_head_id",
        "bank_out_slice",
        "bank_out_last",
        "bank_out_value",
        "root_head_id",
        "root_slice",
        "root_last",
        "root_value",
    ):
        if forbidden in top_module:
            raise SystemExit(f"generated bank-control RTL must not expose payload/metadata signal: {forbidden}")
    if "DIVIDE_ITERATIONS" in top_module or "rounded_dividend" in top_module or "exp_lut" in top_module:
        raise SystemExit("generated bank-control RTL must not embed finalizer arithmetic or exp-scale logic")
    if re.search(r"(?<![*/])/(?![/*])", re.sub(r"//.*", "", top_module)):
        raise SystemExit("generated bank-control RTL must not contain combinational division operators")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)
    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_finalizer_bank_control_v1",
                "divider_lanes": divider_lanes,
                "finalizer_banks": finalizer_banks,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
