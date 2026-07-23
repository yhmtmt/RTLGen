#!/usr/bin/env python3
"""Validate the shared-score multi-value decode cluster before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


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
        raise SystemExit(
            f"selected config must be a direct child of design-dir, got: {relative_path.as_posix()}"
        )
    return config_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Config used to generate the design; defaults to <design-dir>/config.json",
    )
    args = parser.parse_args()
    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    config = _load_json(config_path)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    if not generated_config_path.exists():
        raise SystemExit(f"missing generated config: {generated_config_path}")
    generated_config = _load_json(generated_config_path)
    manifest = _load_json(rtl_dir / "attention_decode_score_multivalue_cluster_manifest.json")
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    errors: list[str] = []
    if config != generated_config:
        errors.append(
            f"selected config {config_path} does not match generated config {generated_config_path}"
        )
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
    body = config.get("attention_decode_score_multivalue_cluster")
    fsm_encoding = str(body.get("fsm_encoding", "default")).strip().lower() if isinstance(body, dict) else "default"
    if manifest.get("fsm_encoding") != fsm_encoding:
        errors.append("manifest fsm_encoding does not match config")
    if fsm_encoding == "explicit_onehot":
        if manifest.get("controller_state_width") != 7:
            errors.append("explicit_onehot controller_state_width must be 7")
        reducer_manifest = manifest.get("submodule_manifests", {}).get("multivalue_reducer", {})
        if reducer_manifest.get("state_width") != 11:
            errors.append("explicit_onehot reducer state_width must be 11")
        if '(* fsm_encoding = "none", fsm_extract = "no" *) reg [6:0] state_q;' not in rtl:
            errors.append("explicit_onehot RTL missing guarded 7-bit cluster state register")
        if '(* fsm_encoding = "none", fsm_extract = "no" *) reg [10:0] state;' not in rtl:
            errors.append("explicit_onehot RTL missing guarded 11-bit reducer state register")
    elif fsm_encoding == "binary":
        if '(* fsm_encoding = "binary" *) reg [2:0] state_q;' not in rtl:
            errors.append("binary RTL missing cluster state attribute")
        if '(* fsm_encoding = "binary" *) reg [3:0] state;' not in rtl:
            errors.append("binary RTL missing reducer state attribute")
    if errors:
        raise SystemExit("; ".join(errors))
    print(
        json.dumps(
            {
                "design": expected_top,
                "config": str(config_path),
                "guard": "attention_decode_score_multivalue_cluster_v1",
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
