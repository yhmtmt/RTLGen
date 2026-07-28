#!/usr/bin/env python3
"""Strict source-level guard for the cluster-SRAM-composed full score32 GQA8 hierarchy."""

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

from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import generate

CONFIG_KEY = "attention_score32_exact_local16_global_tree_cluster_sram_gqa8"
MANIFEST_NAME = "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json"


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
    with tempfile.TemporaryDirectory(prefix="score32_gqa8_full_cluster_sram_guard_") as temp_name:
        generated = Path(temp_name)
        generate(config, generated)
        for name in ("top.v", "config.json", MANIFEST_NAME):
            if (generated / name).read_bytes() != (rtl_dir / name).read_bytes():
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = (args.config or (design_dir / "config.json")).resolve()
    rtl_dir = design_dir / "verilog"
    config = _load(config_path)
    if _load(rtl_dir / "config.json") != config:
        raise SystemExit("generated config does not match source config")
    body = config.get(CONFIG_KEY)
    if not isinstance(body, dict):
        raise SystemExit(f"config must contain {CONFIG_KEY}")
    top_name = str(config.get("top_name") or "")
    p54_cluster_top = f"{top_name}__cluster_p54"
    p53_cluster_top = f"{top_name}__cluster_p53"
    global_top = f"{top_name}__global_tree"
    manifest = _load(rtl_dir / MANIFEST_NAME)
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")

    expected_manifest = {
        "semantic_profile": "score32_exact_local16_global_tree_cluster_sram_gqa8_full_compute_v1",
        "clusters": 16,
        "cluster_producers": [54] * 8 + [53] * 8,
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": 856,
        "internal_value_memory_lanes": 1712,
        "external_fill_interfaces": 16,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "equivalence_hash": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            raise SystemExit(f"generated manifest {key} must be {expected!r}")
    if manifest.get("service_model", {}).get("per_cluster_internal_value_memory_lanes") != [108] * 8 + [106] * 8:
        raise SystemExit("manifest must record the exact 8*108 + 8*106 internal lane partition")

    top = _module(rtl, top_name)
    p54_cluster = _module(rtl, p54_cluster_top)
    p53_cluster = _module(rtl, p53_cluster_top)
    _module(rtl, global_top)

    if len(re.findall(rf"\b{re.escape(p54_cluster_top)}\s+u_cluster_", top)) != 8:
        raise SystemExit("top must instantiate exactly 8 p54 cluster-SRAM composed clusters")
    if len(re.findall(rf"\b{re.escape(p53_cluster_top)}\s+u_cluster_", top)) != 8:
        raise SystemExit("top must instantiate exactly 8 p53 cluster-SRAM composed clusters")
    for module_text, label in ((p54_cluster, "p54"), (p53_cluster, "p53")):
        if len(re.findall(r"\bu_compute_cluster\s*\(", module_text)) != 1:
            raise SystemExit(f"{label} composed cluster must instantiate exactly one real compute cluster")
        if len(re.findall(r"\bu_sram_endpoint\s*\(", module_text)) != 1:
            raise SystemExit(f"{label} composed cluster must instantiate exactly one SRAM endpoint")

    for token in (
        "input  wire [15:0] fill_target_valid",
        "output wire [15:0] fill_target_ready",
        "input  wire [8191:0] fill_data",
        "output wire [511:0] cluster_sram_command_release_count",
        "output wire [15:0] cluster_sram_release_guard_error",
        "output wire [15:0] cluster_fill_schedule_contract_error",
        "output wire fill_schedule_contract_error",
        "output wire [4:0] expected_head_base",
        "output wire [2:0] expected_wave_index",
        "assign command_ready = command_head_base_match_w && (&cluster_compute_command_ready_w) && (&cluster_sram_command_ready_w);",
        "wire [4:0] expected_head_base_w = {schedule_head_group_q, 3'd0};",
        "wire [1:0] next_schedule_head_group_w =",
        "wire [2:0] next_schedule_wave_w = (schedule_wave_q == 3'd7) ? 3'd0 : (schedule_wave_q + 3'd1);",
        "assign cluster_fill_schedule_contract_error = cluster_fill_schedule_contract_error_q;",
        "assign fill_schedule_contract_error = |cluster_fill_schedule_contract_error_q;",
        ".command_wave_index(schedule_wave_q)",
        ".compute_command_ready(cluster_compute_command_ready_w[0])",
        ".sram_command_ready(cluster_sram_command_ready_w[0])",
        ".fill_target_command_id(fill_target_command_id[0 +: 16])",
        ".fill_data(fill_data[0 +: 512])",
        "assign protocol_error = command_cadence_error_q || fill_schedule_contract_error || (|cluster_protocol_error) ||",
        "if (command_valid && (&cluster_compute_command_ready_w) && (&cluster_sram_command_ready_w) &&",
    ):
        _require(top, token)
    for forbidden in (
        "output wire [1711:0] value_read_req_valid",
        "input  wire [1711:0] value_response_valid",
        "input  wire [876543:0] value_response_matrix",
        "command_block_count,",
    ):
        if forbidden in top:
            raise SystemExit(f"top contains forbidden external value-lane token: {forbidden}")

    for module_text in (p54_cluster, p53_cluster):
        for token in (
            "wire release_count_pending_w = (wave_command_accept_count > released_count_q);",
            "assign producer_completed_match_w[gpi] =",
            "producer_command_completed_count[(gpi * 32) +: 32] == wave_command_accept_count",
            "wire release_invariant_satisfied_w =",
            "release_count_pending_w && all_producers_completed_w && endpoint_responses_drained_w;",
            "wire fill_target_buffer_map_w = (fill_target_buffer_sel == fill_target_wave_index[0]);",
            "if (wave_command_accept_count != released_count_q)",
            "if (!release_count_pending_w || !all_producers_completed_w || !endpoint_responses_drained_w)",
        ):
            _require(module_text, token, "composed cluster RTL")
    for token in (
        "assign fill_target_schedule_allowed_w[gfill] =",
        "(fill_target_head_base[(gfill * 5) +: 5] == expected_head_base_w) &&",
        "(fill_target_wave_index[(gfill * 3) +: 3] == schedule_wave_q)",
        "(fill_target_head_base[(gfill * 5) +: 5] == next_expected_head_base_w) &&",
        "(fill_target_wave_index[(gfill * 3) +: 3] == next_schedule_wave_w));",
        "assign fill_target_ready[gfill] =",
        "fill_target_schedule_allowed_w[gfill] ? fill_target_ready_internal_w[gfill] : 1'b0;",
        "if (fill_target_valid[0] && fill_target_metadata_valid_w[0] && !fill_target_schedule_allowed_w[0])",
        "if (fill_target_valid[15] && fill_target_metadata_valid_w[15] && !fill_target_schedule_allowed_w[15])",
    ):
        _require(top, token)

    _compare_regeneration(config, rtl_dir)
    print(
        json.dumps(
            {
                "status": "ok",
                "clusters": 16,
                "total_local_producers": 856,
                "internal_value_memory_lanes": 1712,
                "external_fill_interfaces": 16,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
