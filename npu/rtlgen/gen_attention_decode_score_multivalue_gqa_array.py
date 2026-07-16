#!/usr/bin/env python3
"""Generate a direct parallel array of complete Llama7B GQA8 groups."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_gqa_group import generate as generate_group


_SUPPORTED_GROUP_COUNTS = (1, 2, 4)
_GROUP_MACRO_COUNT = 448
_GROUP_QUERY_HEADS = 8


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(config: dict[str, Any]) -> dict[str, int | str]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_decode_score_multivalue_gqa_array")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_decode_score_multivalue_gqa_array")

    max_blocks = int(body.get("max_blocks", 16384))
    array_n = int(body.get("array_n", 8))
    value_slices = int(body.get("value_slices", 16))
    scale_lanes = int(body.get("score_scale_lanes_per_cycle", 1))
    divider_impl = str(body.get("divider_impl", "iterative_restoring")).strip()
    query_heads_per_kv = int(body.get("query_heads_per_kv", 8))
    group_count = int(body.get("group_count", 0))

    if max_blocks < 8 or max_blocks > 16384 or max_blocks & (max_blocks - 1):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if array_n != 8:
        raise SystemExit("array_n must be 8")
    if value_slices != 16:
        raise SystemExit("value_slices must be 16")
    if scale_lanes != 1:
        raise SystemExit("score_scale_lanes_per_cycle must be 1 for the GQA array")
    if divider_impl != "iterative_restoring":
        raise SystemExit("divider_impl must be iterative_restoring")
    if query_heads_per_kv != 8:
        raise SystemExit("query_heads_per_kv must be 8 for Llama7B GQA8")
    if group_count not in _SUPPORTED_GROUP_COUNTS:
        raise SystemExit("group_count must be exactly one of 1, 2, or 4")

    body.update(
        {
            "max_blocks": max_blocks,
            "array_n": array_n,
            "value_slices": value_slices,
            "score_scale_lanes_per_cycle": scale_lanes,
            "divider_impl": divider_impl,
            "query_heads_per_kv": query_heads_per_kv,
            "group_count": group_count,
        }
    )
    return {
        "top_name": top_name,
        "max_blocks": max_blocks,
        "array_n": array_n,
        "value_slices": value_slices,
        "score_scale_lanes_per_cycle": scale_lanes,
        "divider_impl": divider_impl,
        "query_heads_per_kv": query_heads_per_kv,
        "group_count": group_count,
    }


def _slice(name: str, index: int, width: int) -> str:
    lo = index * width
    return f"{name}[{lo + width - 1}:{lo}]"


def _group_instances(group_top: str, group_count: int) -> str:
    instances = []
    for group in range(group_count):
        instances.append(
            f"""  {group_top} u_group_{group} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid && command_ready),
      .command_ready(child_command_ready[{group}]),
      .command_id(command_id),
      .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid && input_ready),
      .input_ready(child_input_ready[{group}]),
      .input_last(input_last),
      .input_query({_slice("input_query", group, 64)}),
      .input_key({_slice("input_key", group, 64)}),
      .value_read_req_valid(value_read_req_valid[{group}]),
      .value_read_req_ready(value_read_req_ready[{group}]),
      .value_read_req_address({_slice("value_read_req_address", group, 14)}),
      .value_read_req_slice({_slice("value_read_req_slice", group, 4)}),
      .value_response_valid(value_response_valid[{group}]),
      .value_response_ready(value_response_ready[{group}]),
      .value_response_address({_slice("value_response_address", group, 14)}),
      .value_response_slice({_slice("value_response_slice", group, 4)}),
      .value_response_matrix({_slice("value_response_matrix", group, 512)}),
      .result_valid(result_valid[{group}]),
      .result_ready(result_ready[{group}]),
      .result_head({_slice("result_head", group, 3)}),
      .result_command_id({_slice("result_command_id", group, 16)}),
      .result_global_max({_slice("result_global_max", group, 32)}),
      .result_exp_sum({_slice("result_exp_sum", group, 33)}),
      .result_slice({_slice("result_slice", group, 4)}),
      .result_last(result_last[{group}]),
      .result_value({_slice("result_value", group, 320)}),
      .accepted_count({_slice("accepted_count", group, 32)}),
      .completed_count({_slice("completed_count", group, 32)}),
      .cycle_count({_slice("cycle_count", group, 32)}),
      .protocol_error(child_protocol_error[{group}])
  );"""
        )
    return "\n\n".join(instances)


def _wrapper(*, top_name: str, group_top: str, group_count: int) -> str:
    total_query_bits = group_count * 64
    total_result_heads = group_count * 3
    total_result_commands = group_count * 16
    total_result_max = group_count * 32
    total_result_sums = group_count * 33
    total_result_slices = group_count * 4
    total_result_values = group_count * 320
    total_counter_bits = group_count * 32
    return f"""// Auto-generated by npu/rtlgen/gen_attention_decode_score_multivalue_gqa_array.py
module {top_name} (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         command_valid,
    output wire                         command_ready,
    input  wire [15:0]                  command_id,
    input  wire [14:0]                  command_block_count,
    input  wire [31:0]                  command_score_multiplier,
    input  wire [5:0]                   command_score_shift,
    input  wire                         input_valid,
    output wire                         input_ready,
    input  wire                         input_last,
    input  wire signed [{total_query_bits - 1}:0] input_query,
    input  wire signed [{total_query_bits - 1}:0] input_key,
    output wire [{group_count - 1}:0]   value_read_req_valid,
    input  wire [{group_count - 1}:0]   value_read_req_ready,
    output wire [{group_count * 14 - 1}:0] value_read_req_address,
    output wire [{group_count * 4 - 1}:0] value_read_req_slice,
    input  wire [{group_count - 1}:0]   value_response_valid,
    output wire [{group_count - 1}:0]   value_response_ready,
    input  wire [{group_count * 14 - 1}:0] value_response_address,
    input  wire [{group_count * 4 - 1}:0] value_response_slice,
    input  wire [{group_count * 512 - 1}:0] value_response_matrix,
    output wire [{group_count - 1}:0]   result_valid,
    input  wire [{group_count - 1}:0]   result_ready,
    output wire [{total_result_heads - 1}:0] result_head,
    output wire [{total_result_commands - 1}:0] result_command_id,
    output wire signed [{total_result_max - 1}:0] result_global_max,
    output wire [{total_result_sums - 1}:0] result_exp_sum,
    output wire [{total_result_slices - 1}:0] result_slice,
    output wire [{group_count - 1}:0]   result_last,
    output wire [{total_result_values - 1}:0] result_value,
    output wire [{total_counter_bits - 1}:0] accepted_count,
    output wire [{total_counter_bits - 1}:0] completed_count,
    output wire [{total_counter_bits - 1}:0] cycle_count,
    output wire                         protocol_error
);
  localparam integer GROUP_COUNT = {group_count};
  localparam integer QUERY_HEADS_PER_KV = 8;
  localparam integer TOTAL_PARALLEL_QUERY_HEADS = 8 * GROUP_COUNT;
  localparam integer SCORE_BANK_MACROS_PER_GROUP = 448;
  localparam integer TOTAL_SCORE_BANK_MACROS = SCORE_BANK_MACROS_PER_GROUP * GROUP_COUNT;

  wire [GROUP_COUNT-1:0] child_command_ready;
  wire [GROUP_COUNT-1:0] child_input_ready;
  wire [GROUP_COUNT-1:0] child_protocol_error;

  wire command_ready_all = &child_command_ready;
  wire input_ready_all = &child_input_ready;

  assign command_ready = command_ready_all;
  assign input_ready = input_ready_all;
  assign protocol_error = |child_protocol_error;

{_group_instances(group_top, group_count)}
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    params = _validate(config)
    top_name = str(params["top_name"])
    group_count = int(params["group_count"])
    group_top = f"{top_name}__group"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_text:
        group_dir = Path(tmp_text) / "group"
        generate_group(
            {
                "top_name": group_top,
                "attention_decode_score_multivalue_gqa_group": {
                    "max_blocks": int(params["max_blocks"]),
                    "array_n": int(params["array_n"]),
                    "value_slices": int(params["value_slices"]),
                    "divider_impl": str(params["divider_impl"]),
                    "score_scale_lanes_per_cycle": int(params["score_scale_lanes_per_cycle"]),
                    "query_heads_per_kv": int(params["query_heads_per_kv"]),
                },
            },
            group_dir,
        )
        group_rtl = (group_dir / "top.v").read_text(encoding="utf-8")
        group_manifest = json.loads(
            (group_dir / "attention_decode_score_multivalue_gqa_group_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    rtl = group_rtl + "\n\n" + _wrapper(top_name=top_name, group_top=group_top, group_count=group_count) + "\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_array.py",
        "top_name": top_name,
        "semantic_profile": "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_array_v1",
        "max_blocks": int(params["max_blocks"]),
        "score_tile_array_n": int(params["array_n"]),
        "score_scale_lanes_per_cycle": int(params["score_scale_lanes_per_cycle"]),
        "divider_impl": str(params["divider_impl"]),
        "value_slices": int(params["value_slices"]),
        "query_heads_per_kv": int(params["query_heads_per_kv"]),
        "group_count": group_count,
        "logical_kv_groups": group_count,
        "total_parallel_query_heads": _GROUP_QUERY_HEADS * group_count,
        "total_score_bank_macros": _GROUP_MACRO_COUNT * group_count,
        "per_group_macro_count": _GROUP_MACRO_COUNT,
        "independent_external_value_ports": group_count,
        "serialization": "none",
        "no_serialization": True,
        "result_beats_per_command_per_group": 128,
        "result_value_bits_per_beat": 320,
        "submodule_manifests": {"gqa_group": group_manifest},
    }
    (out_dir / "attention_decode_score_multivalue_gqa_array_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
