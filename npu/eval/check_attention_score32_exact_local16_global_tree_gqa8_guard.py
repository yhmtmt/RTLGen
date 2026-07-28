#!/usr/bin/env python3
"""Strict source-level guard for the full functional score32 GQA8 hierarchy."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import generate

_CONFIG_KEY = "attention_score32_exact_local16_global_tree_gqa8"
_MANIFEST_NAME = "attention_score32_exact_local16_global_tree_gqa8_manifest.json"


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON object required: {path}")
    return payload


def _require(text: str, token: str, label: str = "generated RTL") -> None:
    if token not in text:
        raise SystemExit(f"{label} missing semantic token: {token}")


def _module(text: str, name: str) -> str:
    matches = re.findall(rf"module\s+{re.escape(name)}\b.*?endmodule", text, flags=re.DOTALL)
    if len(matches) != 1:
        raise SystemExit(f"module {name} must be defined exactly once, found {len(matches)}")
    return matches[0]


def _compare_regeneration(config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_gqa8_full_guard_") as temp_name:
        generated = Path(temp_name)
        generate(config, generated)
        for name in ("top.v", "config.json", _MANIFEST_NAME):
            if (generated / name).read_bytes() != (rtl_dir / name).read_bytes():
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = (args.config or (design_dir / "config.json")).resolve()
    try:
        relative_config = config_path.relative_to(design_dir)
    except ValueError as exc:
        raise SystemExit("selected config must live under design-dir") from exc
    if len(relative_config.parts) != 1:
        raise SystemExit("selected config must be a direct child of design-dir")
    rtl_dir = design_dir / "verilog"
    config = _load(config_path)
    if _load(rtl_dir / "config.json") != config:
        raise SystemExit("generated config does not match source config")
    body = config.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise SystemExit(f"config must contain {_CONFIG_KEY}")
    top_name = str(config.get("top_name") or "")
    producer_top = f"{top_name}__producer"
    p54_cluster_top = f"{top_name}__cluster_p54"
    p53_cluster_top = f"{top_name}__cluster_p53"
    global_top = f"{top_name}__global_tree"
    manifest = _load(rtl_dir / _MANIFEST_NAME)
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")

    expected_manifest = {
        "semantic_profile": "score32_exact_local16_global_tree_gqa8_full_compute_v1",
        "clusters": 16,
        "cluster_producers": [54] * 8 + [53] * 8,
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": 856,
        "total_value_memory_lanes": 1712,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "top_pin_bits": 1_173_953,
        "equivalence_hash": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            raise SystemExit(f"generated manifest {key} must be {expected!r}")

    top = _module(rtl, top_name)
    producer = _module(rtl, producer_top)
    p54_cluster = _module(rtl, p54_cluster_top)
    p53_cluster = _module(rtl, p53_cluster_top)
    _module(rtl, global_top)
    for module_name in (
        f"{top_name}__local_temporal_p54",
        f"{top_name}__local_temporal_p53",
    ):
        _module(rtl, module_name)

    if len(re.findall(r"\bu_producer_\d+\s*\(", p54_cluster)) != 54:
        raise SystemExit("p54 cluster must instantiate exactly 54 functional producers")
    if len(re.findall(r"\bu_producer_\d+\s*\(", p53_cluster)) != 53:
        raise SystemExit("p53 cluster must instantiate exactly 53 functional producers")
    if len(re.findall(rf"\b{re.escape(p54_cluster_top)}\s+u_cluster_", top)) != 8:
        raise SystemExit("top must instantiate exactly 8 p54 clusters")
    if len(re.findall(rf"\b{re.escape(p53_cluster_top)}\s+u_cluster_", top)) != 8:
        raise SystemExit("top must instantiate exactly 8 p53 clusters")
    if len(re.findall(rf"\b{re.escape(global_top)}\s+u_global_tree", top)) != 1:
        raise SystemExit("top must instantiate the finalized global tree exactly once")

    for token in (
        "input  wire [855:0] input_valid",
        "input  wire signed [109567:0] input_query",
        "output wire [1711:0] value_read_req_valid",
        "input  wire [876543:0] value_response_matrix",
        "output wire [319:0] root_value",
        "assign command_ready = command_head_base_valid_w && (&cluster_command_ready_w);",
        "wire command_fire_w = command_valid && command_ready;",
        ".command_valid(command_fire_w)",
        ".input_valid(input_valid[0 +: 54])",
        ".input_valid(input_valid[803 +: 53])",
        ".value_response_matrix(value_response_matrix[822272 +: 54272])",
        ".leaf_valid(cluster_out_valid_w)",
        ".leaf_value(cluster_out_value_w)",
        "assign p54_command_block_count_w[0 +: 15]",
        "command_head_base[4:3] == 2'd0",
        "(0 >= 0) && (0 < 10)",
        "assign p53_command_block_count_w[0 +: 15]",
        "(0 >= 0) && (0 < 11)",
        "assign protocol_error = (|cluster_protocol_error) || global_protocol_error;",
    ):
        _require(top, token)
    for forbidden in (
        " leaf_valid,",
        " leaf_command_id,",
        "command_block_count,",
        "(* blackbox *)",
    ):
        if forbidden in top:
            raise SystemExit(f"functional top contains forbidden legacy/auxiliary token: {forbidden}")
    if "(* blackbox *)" in rtl:
        raise SystemExit("concrete RTL must not rely on blackbox definitions")
    if producer.count("module ") < 1:
        raise SystemExit("shared producer module is not concrete")

    _compare_regeneration(config, rtl_dir)
    print(
        json.dumps(
            {
                "status": "ok",
                "clusters": 16,
                "total_local_producers": 856,
                "total_value_memory_lanes": 1712,
                "divider_lanes": 8,
                "finalizer_banks": 59,
                "top_pin_bits": 1_173_953,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
