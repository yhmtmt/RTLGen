#!/usr/bin/env python3
"""Guard the direct Llama7B GQA8 multi-group array before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


_SUPPORTED_GROUP_COUNTS = (1, 2, 4)
_FAKERAM = "fakeram45_2048x39"
_FAKERAM_LEF = "/orfs/flow/platforms/nangate45/lef/fakeram45_2048x39.lef"
_FAKERAM_LIB = "/orfs/flow/platforms/nangate45/lib/fakeram45_2048x39.lib"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(mapping: dict, key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "config": args.design_dir / "config.json",
        "generated": args.design_dir / "verilog" / "config.json",
        "manifest": args.design_dir / "verilog" / "attention_decode_score_multivalue_gqa_array_manifest.json",
        "top": args.design_dir / "verilog" / "top.v",
        "macro_manifest": args.design_dir / "macro_manifest.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"missing decode-score multivalue GQA-array artifact: {path}")

    config = _load(paths["config"])
    if config != _load(paths["generated"]):
        raise SystemExit("generated config does not match source config")
    body = config.get("attention_decode_score_multivalue_gqa_array")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_decode_score_multivalue_gqa_array object")

    expected_config = {
        "max_blocks": 16384,
        "array_n": 8,
        "value_slices": 16,
        "divider_impl": "iterative_restoring",
        "score_scale_lanes_per_cycle": 1,
        "query_heads_per_kv": 8,
    }
    for key, expected in expected_config.items():
        _require(body, key, expected, "GQA-array config")
    group_count = body.get("group_count")
    if group_count not in _SUPPORTED_GROUP_COUNTS:
        raise SystemExit("GQA-array config group_count must be exactly one of 1, 2, or 4")

    top_name = str(config.get("top_name") or "")
    if f"_g{group_count}" not in top_name:
        raise SystemExit("GQA-array top_name must encode its group count as _g1, _g2, or _g4")

    manifest = _load(paths["manifest"])
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_array.py",
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1",
        "max_blocks": 16384,
        "score_tile_array_n": 8,
        "score_scale_lanes_per_cycle": 1,
        "divider_impl": "iterative_restoring",
        "value_slices": 16,
        "query_heads_per_kv": 8,
        "group_count": group_count,
        "logical_kv_groups": group_count,
        "total_parallel_query_heads": 8 * group_count,
        "total_score_bank_macros": 448 * group_count,
        "per_group_macro_count": 448,
        "independent_external_value_ports": group_count,
        "serialization": "none",
        "no_serialization": True,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    group_manifest = manifest.get("submodule_manifests", {}).get("gqa_group", {})
    _require(group_manifest, "top_name", f"{top_name}__group", "embedded GQA-group manifest")
    _require(
        group_manifest,
        "semantic_profile",
        "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1",
        "embedded GQA-group manifest",
    )
    _require(group_manifest, "query_heads_per_kv", 8, "embedded GQA-group manifest")
    _require(group_manifest, "value_slices", 16, "embedded GQA-group manifest")
    _require(group_manifest.get("submodule_manifests", {}).get("multivalue_cluster", {}), "score_bank_macro_count", 56, "embedded cluster manifest")

    macro_manifest = _load(paths["macro_manifest"])
    if macro_manifest.get("design_id") != top_name or macro_manifest.get("module") != top_name:
        raise SystemExit("macro manifest design_id and module must match config top_name")
    if macro_manifest.get("platform") != "nangate45":
        raise SystemExit("macro manifest platform must be nangate45")
    if macro_manifest.get("flow_variant") != "decode_score_multivalue_gqa_array_v1":
        raise SystemExit("macro manifest flow_variant must be decode_score_multivalue_gqa_array_v1")
    if macro_manifest.get("blackboxes") != [_FAKERAM]:
        raise SystemExit("macro manifest must contain exactly the FakeRAM blackbox contract")
    if macro_manifest.get("additional_lefs") != [_FAKERAM_LEF]:
        raise SystemExit("macro manifest must contain the FakeRAM LEF contract")
    if macro_manifest.get("additional_libs") != [_FAKERAM_LIB]:
        raise SystemExit("macro manifest must contain the FakeRAM Liberty contract")
    if macro_manifest.get("additional_gds") != []:
        raise SystemExit("macro manifest additional_gds must be empty")
    if macro_manifest.get("blackbox_verilog") != ["npu/rtl/fakeram45_2048x39_blackbox.v"]:
        raise SystemExit("macro manifest must contain the FakeRAM blackbox Verilog contract")
    source = macro_manifest.get("source", {})
    if source.get("generator") != "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_array.py":
        raise SystemExit("macro manifest source generator must identify the GQA-array generator")
    if source.get("config") != f"runs/designs/npu_blocks/{top_name}/config.json":
        raise SystemExit("macro manifest source config must identify the source design config")

    macro_params = macro_manifest.get("manifest_params", {})
    expected_macro_params = {
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1",
        "macro_count": 448 * group_count,
        "score_bank_macro_count": 448 * group_count,
        "per_group_macro_count": 448,
        "group_count": group_count,
        "logical_kv_groups": group_count,
        "total_parallel_query_heads": 8 * group_count,
        "independent_external_value_ports": group_count,
        "serialization": "none",
        "query_heads_per_kv": 8,
        "score_scale_lanes_per_cycle": 1,
        "score_passes_per_query_head": 1,
        "value_slices": 16,
    }
    for key, expected in expected_macro_params.items():
        _require(macro_params, key, expected, "macro manifest")

    text = paths["top"].read_text(encoding="utf-8", errors="replace")
    group_top = f"{top_name}__group"
    if len(re.findall(rf"^module\s+{re.escape(top_name)}\s*\(", text, re.MULTILINE)) != 1:
        raise SystemExit(f"generated RTL must define exactly one array top module {top_name}")
    if len(re.findall(rf"^module\s+{re.escape(group_top)}\s*\(", text, re.MULTILINE)) != 1:
        raise SystemExit(f"generated RTL must define exactly one complete group module {group_top}")
    if text.count(f"{group_top} u_group_") != group_count:
        raise SystemExit("GQA-array RTL group instance count does not match group_count")
    if text.count(f"{group_top}__cluster u_head_") != 8:
        raise SystemExit("embedded GQA group must instantiate eight query-head clusters")
    if text.count("fakeram45_2048x39 u_group_") != 56:
        raise SystemExit("embedded GQA group must contain exactly 56 score-bank macro instances")
    packed_width = 64 * group_count
    if not re.search(rf"input\s+wire\s+signed\s+\[{packed_width - 1}:0\]\s+input_query", text):
        raise SystemExit("GQA-array RTL must expose the packed query bus")
    if not re.search(rf"input\s+wire\s+signed\s+\[{packed_width - 1}:0\]\s+input_key", text):
        raise SystemExit("GQA-array RTL must expose the packed key bus")
    for group in range(group_count):
        q_lo = group * 64
        q_hi = q_lo + 63
        addr_lo = group * 14
        addr_hi = addr_lo + 13
        slice_lo = group * 4
        slice_hi = slice_lo + 3
        matrix_lo = group * 512
        matrix_hi = matrix_lo + 511
        head_lo = group * 3
        head_hi = head_lo + 2
        command_lo = group * 16
        command_hi = command_lo + 15
        max_lo = group * 32
        max_hi = max_lo + 31
        sum_lo = group * 33
        sum_hi = sum_lo + 32
        value_lo = group * 320
        value_hi = value_lo + 319
        connections = (
            f".input_query(input_query[{q_hi}:{q_lo}])",
            f".input_key(input_key[{q_hi}:{q_lo}])",
            f".value_read_req_valid(value_read_req_valid[{group}])",
            f".value_read_req_ready(value_read_req_ready[{group}])",
            f".value_read_req_address(value_read_req_address[{addr_hi}:{addr_lo}])",
            f".value_read_req_slice(value_read_req_slice[{slice_hi}:{slice_lo}])",
            f".value_response_valid(value_response_valid[{group}])",
            f".value_response_ready(value_response_ready[{group}])",
            f".value_response_address(value_response_address[{addr_hi}:{addr_lo}])",
            f".value_response_slice(value_response_slice[{slice_hi}:{slice_lo}])",
            f".value_response_matrix(value_response_matrix[{matrix_hi}:{matrix_lo}])",
            f".result_valid(result_valid[{group}])",
            f".result_ready(result_ready[{group}])",
            f".result_head(result_head[{head_hi}:{head_lo}])",
            f".result_command_id(result_command_id[{command_hi}:{command_lo}])",
            f".result_global_max(result_global_max[{max_hi}:{max_lo}])",
            f".result_exp_sum(result_exp_sum[{sum_hi}:{sum_lo}])",
            f".result_slice(result_slice[{slice_hi}:{slice_lo}])",
            f".result_last(result_last[{group}])",
            f".result_value(result_value[{value_hi}:{value_lo}])",
        )
        for connection in connections:
            if connection not in text:
                raise SystemExit(f"GQA-array RTL missing exact group {group} connection: {connection}")
    for token in (
        "GROUP_COUNT =",
        "TOTAL_PARALLEL_QUERY_HEADS",
        "TOTAL_SCORE_BANK_MACROS",
        "wire command_ready_all = &child_command_ready",
        "wire input_ready_all = &child_input_ready",
        ".command_valid(command_valid && command_ready)",
        ".input_valid(input_valid && input_ready)",
        "assign protocol_error = |child_protocol_error",
        "value_read_req_valid[0]",
        "value_response_valid[0]",
        "result_valid[0]",
    ):
        if token not in text:
            raise SystemExit(f"GQA-array RTL missing semantic token: {token}")
    for forbidden in (
        "result_hash",
        "equivalence_hash",
        "hash",
        "value_read_req_arbiter",
        "value_response_arbiter",
        "serialize",
        " / exp_sum_accum",
        "% exp_sum_accum",
    ):
        if forbidden in text.lower():
            raise SystemExit(f"GQA-array RTL contains forbidden abstraction token: {forbidden}")

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_decode_score_multivalue_gqa_array_v1",
                "group_count": group_count,
                "macro_count": 448 * group_count,
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
