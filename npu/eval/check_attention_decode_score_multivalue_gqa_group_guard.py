#!/usr/bin/env python3
"""Guard the Llama7B GQA8 multivalue decode-score group before physical evaluation."""

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
        "manifest": (
            args.design_dir
            / "verilog"
            / "attention_decode_score_multivalue_gqa_group_manifest.json"
        ),
        "top": args.design_dir / "verilog" / "top.v",
        "macro_manifest": args.design_dir / "macro_manifest.json",
    }
    for path in paths.values():
        if not path.is_file():
            raise SystemExit(f"missing decode-score multivalue GQA-group artifact: {path}")

    config = _load(paths["config"])
    if config != _load(paths["generated"]):
        raise SystemExit("generated config does not match source config")
    body = config.get("attention_decode_score_multivalue_gqa_group")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_decode_score_multivalue_gqa_group object")

    expected_config = {
        "max_blocks": 16384,
        "array_n": 8,
        "value_slices": 16,
        "divider_impl": "iterative_restoring",
        "score_scale_lanes_per_cycle": 1,
        "query_heads_per_kv": 8,
    }
    for key, expected in expected_config.items():
        if body.get(key) != expected:
            raise SystemExit(f"GQA-group config {key} must be {expected}")

    manifest = _load(paths["manifest"])
    expected_manifest = {
        "top_name": str(config.get("top_name") or ""),
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1",
        "max_blocks": 16384,
        "score_tile_array_n": 8,
        "score_scale_lanes_per_cycle": 1,
        "value_slices": 16,
        "value_dimensions_per_head": 128,
        "query_heads_per_kv": 8,
        "parallel_query_head_clusters": 8,
        "query_head_score_computations_per_command": 8,
        "score_passes_per_query_head": 1,
        "shared_external_value_reads_per_block": 16,
        "internal_value_reads_per_block_per_head": 16,
        "result_beats_per_command": 128,
        "result_value_bits_per_beat": 320,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            raise SystemExit(f"generated manifest {key} must be {expected}")
    cluster_manifest = manifest.get("submodule_manifests", {}).get("multivalue_cluster", {})
    if cluster_manifest.get("score_bank_macro_count") != 56:
        raise SystemExit("each query-head cluster must contain 56 score-bank macros")

    macro_manifest = _load(paths["macro_manifest"])
    if "fakeram45_2048x39" not in macro_manifest.get("blackboxes", []):
        raise SystemExit("macro manifest is missing fakeram45_2048x39")
    if (
        len(macro_manifest.get("additional_lefs", [])) != 1
        or len(macro_manifest.get("additional_libs", [])) != 1
    ):
        raise SystemExit("GQA group must carry one FakeRAM LEF and Liberty view")
    macro_params = macro_manifest.get("manifest_params", {})
    expected_macro_params = {
        "macro_count": 448,
        "score_bank_macro_count": 448,
        "score_bank_macro_count_per_cluster": 56,
        "parallel_query_head_clusters": 8,
        "query_heads_per_kv": 8,
        "query_head_score_computations_per_command": 8,
        "shared_kv_heads_per_group": 1,
        "shared_external_value_reads_per_block": 16,
        "score_scale_lanes_per_cycle": 1,
        "score_passes_per_query_head": 1,
        "value_slices": 16,
    }
    for key, expected in expected_macro_params.items():
        if macro_params.get(key) != expected:
            raise SystemExit(f"macro manifest {key} must be {expected}")

    text = paths["top"].read_text(encoding="utf-8", errors="replace")
    top_name = expected_manifest["top_name"]
    cluster_top = f"{top_name}__cluster"
    if not re.search(rf"^module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")
    if text.count(f"{cluster_top} u_head_") != 8:
        raise SystemExit("GQA-group RTL must instantiate eight parallel query-head clusters")
    if text.count("fakeram45_2048x39 u_group_") != 56:
        raise SystemExit("shared cluster definition must contain exactly 56 score-bank macro instances")
    for token in (
        "QUERY_HEADS_PER_KV = 8",
        "input_query[7:0]",
        "input_query[63:56]",
        "value_req_consistent",
        "value_req_divergent",
        "value_rsp_ready_all",
        "result_head_q",
        "command_ready_all",
        "input_ready_all",
        "DIV_ITER",
    ):
        if token not in text:
            raise SystemExit(f"GQA-group RTL missing semantic token: {token}")
    for forbidden in ("result_hash", "equivalence_hash", "/ exp_sum_accum", "% exp_sum_accum"):
        if forbidden in text:
            raise SystemExit(f"GQA-group RTL contains forbidden abstraction token: {forbidden}")

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_decode_score_multivalue_gqa_group_v1",
                "macro_count": 448,
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
