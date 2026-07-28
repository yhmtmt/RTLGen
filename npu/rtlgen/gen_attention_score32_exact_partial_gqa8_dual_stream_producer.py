#!/usr/bin/env python3
"""Generate a dual-stream GQA8 exact-partial producer slice."""

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
from npu.rtlgen.gen_attention_score32_online_state_merge import generate as generate_merge
from npu.sim.perf.attention_exact_partial import (
    HEAD_ID_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_partial_dual_stream_gqa8_producer_service_manifest,
)

JsonDict = dict[str, Any]

_STREAMS = 2
_QUERY_HEADS_PER_STREAM = 8
_VALUE_SLICES = 16
_ARRAY_N = 8
_CONFIG_KEY = "attention_score32_exact_partial_gqa8_dual_stream_producer"
_MANIFEST_NAME = "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")

    streams = int(body.get("streams", _STREAMS))
    query_heads_per_stream = int(body.get("query_heads_per_stream", _QUERY_HEADS_PER_STREAM))
    max_blocks = int(body.get("max_blocks", 8))
    value_slices = int(body.get("value_slices", _VALUE_SLICES))
    head_id_bits = int(body.get("head_id_bits", HEAD_ID_BITS))

    if streams != _STREAMS:
        raise SystemExit("dual-stream exact producer currently requires streams=2")
    if query_heads_per_stream != _QUERY_HEADS_PER_STREAM:
        raise SystemExit("dual-stream exact producer currently requires query_heads_per_stream=8")
    if max_blocks < 8 or max_blocks > 16384 or (max_blocks & (max_blocks - 1)):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if value_slices != _VALUE_SLICES:
        raise SystemExit("dual-stream exact producer currently requires value_slices=16")
    if head_id_bits != HEAD_ID_BITS:
        raise SystemExit("dual-stream exact producer currently requires head_id_bits=5")

    return {
        "top_name": top_name,
        "streams": streams,
        "query_heads_per_stream": query_heads_per_stream,
        "max_blocks": max_blocks,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
    }


def _slice(name: str, index: int, width: int) -> str:
    lo = index * width
    return f"{name}[{lo + width - 1}:{lo}]"


def _group_instances(group_top: str, head_id_bits: int) -> str:
    blocks: list[str] = []
    for stream in range(_STREAMS):
        blocks.append(
            f"""  {group_top} u_stream_{stream} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid && command_ready),
      .command_ready(stream_command_ready_w[{stream}]),
      .command_id(command_id),
      .command_block_count(command_block_count),
      .command_head_base(command_head_base),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid && input_ready),
      .input_ready(stream_input_ready_w[{stream}]),
      .input_last(input_last),
      .input_query({_slice("input_query", stream, 64)}),
      .input_key({_slice("input_key", stream, 64)}),
      .value_read_req_valid(value_read_req_valid[{stream}]),
      .value_read_req_ready(value_read_req_ready[{stream}]),
      .value_read_req_address({_slice("value_read_req_address", stream, 14)}),
      .value_read_req_slice({_slice("value_read_req_slice", stream, 4)}),
      .value_response_valid(value_response_valid[{stream}]),
      .value_response_ready(value_response_ready[{stream}]),
      .value_response_address({_slice("value_response_address", stream, 14)}),
      .value_response_slice({_slice("value_response_slice", stream, 4)}),
      .value_response_matrix({_slice("value_response_matrix", stream, 512)}),
      .result_valid(stream_result_valid_w[{stream}]),
      .result_ready(stream_result_ready_w[{stream}]),
      .result_head({_slice("stream_result_head_w", stream, 3)}),
      .result_head_id({_slice("stream_result_head_id_w", stream, head_id_bits)}),
      .result_command_id({_slice("stream_result_command_id_w", stream, 16)}),
      .result_global_max({_slice("stream_result_global_max_w", stream, 32)}),
      .result_exp_sum({_slice("stream_result_exp_sum_w", stream, 33)}),
      .result_slice({_slice("stream_result_slice_w", stream, 4)}),
      .result_last(stream_result_last_w[{stream}]),
      .result_value({_slice("stream_result_value_w", stream, PARTIAL_PAYLOAD_BITS)}),
      .accepted_count({_slice("stream_command_accept_count_w", stream, 32)}),
      .completed_count({_slice("stream_completed_count_w", stream, 32)}),
      .cycle_count({_slice("stream_cycle_count_w", stream, 32)}),
      .protocol_error(stream_protocol_error_w[{stream}])
  );"""
        )
    return "\n\n".join(blocks)


def _top(*, top_name: str, group_top: str, merge_top: str, head_id_bits: int) -> str:
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_partial_gqa8_dual_stream_producer.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [{head_id_bits - 1}:0] command_head_base,
    input  wire [14:0]  command_block_count,
    input  wire [31:0]  command_score_multiplier,
    input  wire [5:0]   command_score_shift,
    input  wire         input_valid,
    output wire         input_ready,
    input  wire         input_last,
    input  wire signed [127:0] input_query,
    input  wire signed [127:0] input_key,
    output wire [1:0]   value_read_req_valid,
    input  wire [1:0]   value_read_req_ready,
    output wire [27:0]  value_read_req_address,
    output wire [7:0]   value_read_req_slice,
    input  wire [1:0]   value_response_valid,
    output wire [1:0]   value_response_ready,
    input  wire [27:0]  value_response_address,
    input  wire [7:0]   value_response_slice,
    input  wire [1023:0] value_response_matrix,
    output wire         result_valid,
    input  wire         result_ready,
    output wire [15:0]  result_command_id,
    output wire [{head_id_bits - 1}:0] result_head_id,
    output wire signed [31:0] result_global_max,
    output wire [32:0]  result_exp_sum,
    output wire [3:0]   result_slice,
    output wire         result_last,
    output wire [327:0] result_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  command_accept_count,
    output wire [31:0]  command_completed_count,
    output wire [63:0]  stream_command_accept_count,
    output wire [63:0]  stream_completed_count,
    output wire [1:0]   stream_partial_valid,
    output wire [1:0]   stream_partial_ready,
    output wire [1:0]   stream_partial_last,
    output wire [31:0]  merge_completed_count,
    output wire [31:0]  result_stall_cycles,
    output wire [1:0]   stream_protocol_error,
    output wire         merge_protocol_error,
    output wire         protocol_error
);
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};
  localparam integer HEAD_ID_BITS = {head_id_bits};

  wire [1:0] stream_command_ready_w;
  wire [1:0] stream_input_ready_w;
  wire [1:0] stream_result_valid_w;
  wire [1:0] stream_result_ready_w;
  wire [5:0] stream_result_head_w;
  wire [9:0] stream_result_head_id_w;
  wire [31:0] stream_result_command_id_w;
  wire [63:0] stream_result_global_max_w;
  wire [65:0] stream_result_exp_sum_w;
  wire [7:0] stream_result_slice_w;
  wire [1:0] stream_result_last_w;
  wire [655:0] stream_result_value_w;
  wire [63:0] stream_command_accept_count_w;
  wire [63:0] stream_completed_count_w;
  wire [63:0] stream_cycle_count_w;
  wire [1:0] stream_protocol_error_w;

  wire command_head_base_valid_w = (command_head_base[2:0] == 3'd0) && (command_head_base <= 5'd24);
  wire command_fire_w = command_valid && command_ready;
  wire merge_fire_w = result_valid && result_ready;

  reg [31:0] cycle_count_q;
  reg [31:0] command_accept_count_q;
  reg [31:0] command_completed_count_q;
  reg [31:0] result_stall_cycles_q;
  reg protocol_error_q;

  assign command_ready = command_head_base_valid_w && (&stream_command_ready_w);
  assign input_ready = &stream_input_ready_w;
  assign cycle_count = cycle_count_q;
  assign command_accept_count = command_accept_count_q;
  assign command_completed_count = command_completed_count_q;
  assign stream_command_accept_count = stream_command_accept_count_w;
  assign stream_completed_count = stream_completed_count_w;
  assign stream_partial_valid = stream_result_valid_w;
  assign stream_partial_ready = stream_result_ready_w;
  assign stream_partial_last = stream_result_last_w;
  assign result_stall_cycles = result_stall_cycles_q;
  assign stream_protocol_error = stream_protocol_error_w;
  assign protocol_error = protocol_error_q || (|stream_protocol_error_w) || merge_protocol_error;

{_group_instances(group_top, head_id_bits)}

  {merge_top} u_merge (
      .clk(clk),
      .rst_n(rst_n),
      .left_valid(stream_result_valid_w[0]),
      .left_ready(stream_result_ready_w[0]),
      .left_command_id(stream_result_command_id_w[15:0]),
      .left_head_id(stream_result_head_id_w[4:0]),
      .left_global_max(stream_result_global_max_w[31:0]),
      .left_exp_sum(stream_result_exp_sum_w[32:0]),
      .left_slice(stream_result_slice_w[3:0]),
      .left_last(stream_result_last_w[0]),
      .left_value(stream_result_value_w[327:0]),
      .right_valid(stream_result_valid_w[1]),
      .right_ready(stream_result_ready_w[1]),
      .right_command_id(stream_result_command_id_w[31:16]),
      .right_head_id(stream_result_head_id_w[9:5]),
      .right_global_max(stream_result_global_max_w[63:32]),
      .right_exp_sum(stream_result_exp_sum_w[65:33]),
      .right_slice(stream_result_slice_w[7:4]),
      .right_last(stream_result_last_w[1]),
      .right_value(stream_result_value_w[655:328]),
      .out_valid(result_valid),
      .out_ready(result_ready),
      .out_command_id(result_command_id),
      .out_head_id(result_head_id),
      .out_global_max(result_global_max),
      .out_exp_sum(result_exp_sum),
      .out_slice(result_slice),
      .out_last(result_last),
      .out_value(result_value),
      .completed_count(merge_completed_count),
      .cycle_count(),
      .protocol_error(merge_protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle_count_q <= 32'd0;
      command_accept_count_q <= 32'd0;
      command_completed_count_q <= 32'd0;
      result_stall_cycles_q <= 32'd0;
      protocol_error_q <= 1'b0;
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
      if (command_fire_w) begin
        command_accept_count_q <= command_accept_count_q + 1'b1;
      end
      if (result_valid && !result_ready) begin
        result_stall_cycles_q <= result_stall_cycles_q + 1'b1;
      end
      if (merge_fire_w && result_last && (result_head_id[2:0] == 3'd7)) begin
        command_completed_count_q <= command_completed_count_q + 1'b1;
      end
      if (command_valid && (&stream_command_ready_w) && !command_head_base_valid_w) begin
        protocol_error_q <= 1'b1;
      end
      if ((stream_result_valid_w[0] && stream_result_valid_w[1]) && (stream_result_head_w[2:0] != stream_result_head_w[5:3])) begin
        protocol_error_q <= 1'b1;
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    group_top = f"{top_name}__group"
    merge_top = f"{top_name}__merge"

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_dual_stream_gqa8_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        group_dir = temp_dir / "group"
        merge_dir = temp_dir / "merge"
        generate_group(
            {
                "top_name": group_top,
                "attention_decode_score_multivalue_gqa_group": {
                    "max_blocks": int(params["max_blocks"]),
                    "array_n": _ARRAY_N,
                    "value_slices": int(params["value_slices"]),
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "query_heads_per_kv": int(params["query_heads_per_stream"]),
                    "parallel_query_head_lanes": int(params["query_heads_per_stream"]),
                    "result_mode": "exact_partial",
                    "head_id_bits": int(params["head_id_bits"]),
                },
            },
            group_dir,
        )
        generate_merge(
            {
                "top_name": merge_top,
                "attention_score32_online_state_merge": {
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                },
            },
            merge_dir,
        )
        group_rtl = (group_dir / "top.v").read_text(encoding="utf-8")
        merge_rtl = (merge_dir / "top.v").read_text(encoding="utf-8")
        group_manifest = json.loads(
            (group_dir / "attention_decode_score_multivalue_gqa_group_manifest.json").read_text(encoding="utf-8")
        )
        merge_manifest = json.loads(
            (merge_dir / "attention_score32_online_state_merge_manifest.json").read_text(encoding="utf-8")
        )

    top_text = _top(
        top_name=top_name,
        group_top=group_top,
        merge_top=merge_top,
        head_id_bits=int(params["head_id_bits"]),
    )
    (out_dir / "top.v").write_text(group_rtl + "\n\n" + merge_rtl + "\n\n" + top_text + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    probe_defaults = config.get("probe_defaults", {})
    if not isinstance(probe_defaults, dict):
        probe_defaults = {}
    service_model = exact_partial_dual_stream_gqa8_producer_service_manifest(
        heads=int(probe_defaults.get("heads", 8)),
        max_blocks=int(params["max_blocks"]),
        command_count=int(probe_defaults.get("command_count", int(probe_defaults.get("heads", 8)) // 8)),
        blocks_per_stream=int(probe_defaults.get("blocks_per_stream", 2)),
        head_dim=int(probe_defaults.get("head_dim", 3)),
        head_bases=tuple(int(value) for value in probe_defaults.get("head_bases", [])) if isinstance(probe_defaults.get("head_bases"), list) else None,
        llama_wave_reference_cycles=int(probe_defaults["llama_wave_reference_cycles"]) if "llama_wave_reference_cycles" in probe_defaults else None,
    )
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_partial_gqa8_dual_stream_producer_v1",
        "streams": 2,
        "query_heads_per_stream": 8,
        "token_lanes_per_head": 8,
        "structural_score_macs_per_cycle": 128,
        "max_blocks": int(params["max_blocks"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "producer_result_mode": "exact_partial",
        "command_schedule_contract": "in_order_head_base_commands_broadcast_to_both_streams",
        "head_mapping_contract": "explicit_head_base_plus_lane_no_tile_or_wave_inference",
        "result_interface": "two_exact_partial_gqa8_streams_to_pairwise_exact_merge",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "exact_protocols": {
            "producer_partial_protocol": service_model["producer_partial_protocol"],
        },
        "remaining_abstractions": service_model["remaining_abstractions"],
        "equivalence_hash": False,
        "service_model": service_model,
        "submodule_manifests": {
            "gqa_group": group_manifest,
            "merge": merge_manifest,
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    (out_dir / _MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
