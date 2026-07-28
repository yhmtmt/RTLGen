#!/usr/bin/env python3
"""Generate a full-width GQA8 score32 exact local cluster from real producers and reducer."""

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

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8 import generate as generate_reducer
from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import generate as generate_producer
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local_cluster_gqa8_service_manifest,
)

JsonDict = dict[str, Any]

_CONFIG_KEY = "attention_score32_exact_local_cluster_gqa8"
_MANIFEST_NAME = "attention_score32_exact_local_cluster_gqa8_manifest.json"
_PRODUCER_RTL_NAME = "producer.v"
_REDUCER_RTL_NAME = "reducer.v"
_VERILATOR_LINT_STUBS_NAME = "verilator_wrapper_blackboxes.v"


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

    producers = int(body.get("producers", 53))
    max_blocks = int(body.get("max_blocks", 8))
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    persistent_waves = int(body.get("persistent_waves", LOCAL_TEMPORAL_WAVES))

    if producers not in {53, 54}:
        raise SystemExit("producers must be exactly 53 or 54")
    if max_blocks != 8:
        raise SystemExit("max_blocks must remain fixed at 8 for the corrected p53/p54 cluster schedule")
    if value_slices != 16:
        raise SystemExit("value_slices must remain fixed at 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain fixed at 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")

    return {
        "top_name": top_name,
        "producers": producers,
        "max_blocks": max_blocks,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "persistent_waves": persistent_waves,
    }


def _slice(name: str, index: int, width: int) -> str:
    lo = index * width
    return f"{name}[{lo + width - 1}:{lo}]"


def _top_pin_bits(*, producers: int, head_id_bits: int) -> int:
    value_lanes = producers * 2
    return (
        2
        + 1
        + 1
        + 16
        + head_id_bits
        + (producers * 15)
        + 32
        + 6
        + producers
        + producers
        + producers
        + (producers * 128)
        + (producers * 128)
        + value_lanes
        + value_lanes
        + (value_lanes * 14)
        + (value_lanes * 4)
        + value_lanes
        + value_lanes
        + (value_lanes * 14)
        + (value_lanes * 4)
        + (value_lanes * 512)
        + 1
        + 1
        + 16
        + head_id_bits
        + 32
        + 33
        + 4
        + 1
        + PARTIAL_PAYLOAD_BITS
        + 32
        + 32
        + 32
        + 32
        + 3
        + 1
        + 5
        + 7
        + 7
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + (producers * 32)
        + (producers * 32)
        + (producers * 32)
        + (producers * 64)
        + (producers * 64)
        + (producers * 32)
        + (producers * 32)
        + (producers * 2)
        + producers
        + producers
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
    )


def _producer_instances(*, producer_top: str, producers: int) -> str:
    blocks: list[str] = []
    for producer in range(producers):
        blocks.append(
            f"""  {producer_top} u_producer_{producer} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(group_command_fire_w),
      .command_ready(producer_command_ready_w[{producer}]),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_block_count({_slice("command_block_count", producer, 15)}),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid[{producer}]),
      .input_ready(input_ready[{producer}]),
      .input_last(input_last[{producer}]),
      .input_query({_slice("input_query", producer, 128)}),
      .input_key({_slice("input_key", producer, 128)}),
      .value_read_req_valid({_slice("value_read_req_valid", producer, 2)}),
      .value_read_req_ready({_slice("value_read_req_ready", producer, 2)}),
      .value_read_req_address({_slice("value_read_req_address", producer, 28)}),
      .value_read_req_slice({_slice("value_read_req_slice", producer, 8)}),
      .value_response_valid({_slice("value_response_valid", producer, 2)}),
      .value_response_ready({_slice("value_response_ready", producer, 2)}),
      .value_response_address({_slice("value_response_address", producer, 28)}),
      .value_response_slice({_slice("value_response_slice", producer, 8)}),
      .value_response_matrix({_slice("value_response_matrix", producer, 1024)}),
      .result_valid(producer_result_valid_w[{producer}]),
      .result_ready(producer_result_ready_w[{producer}]),
      .result_command_id({_slice("producer_result_command_id_w", producer, 16)}),
      .result_head_id({_slice("producer_result_head_id_w", producer, 5)}),
      .result_global_max({_slice("producer_result_global_max_w", producer, 32)}),
      .result_exp_sum({_slice("producer_result_exp_sum_w", producer, 33)}),
      .result_slice({_slice("producer_result_slice_w", producer, 4)}),
      .result_last(producer_result_last_w[{producer}]),
      .result_value({_slice("producer_result_value_w", producer, PARTIAL_PAYLOAD_BITS)}),
      .cycle_count({_slice("producer_cycle_count", producer, 32)}),
      .command_accept_count({_slice("producer_command_accept_count", producer, 32)}),
      .command_completed_count({_slice("producer_command_completed_count", producer, 32)}),
      .stream_command_accept_count({_slice("producer_stream_command_accept_count", producer, 64)}),
      .stream_completed_count({_slice("producer_stream_completed_count", producer, 64)}),
      .stream_partial_valid(),
      .stream_partial_ready(),
      .stream_partial_last(),
      .merge_completed_count({_slice("producer_merge_completed_count", producer, 32)}),
      .result_stall_cycles({_slice("producer_result_stall_cycles", producer, 32)}),
      .stream_protocol_error({_slice("producer_stream_protocol_error", producer, 2)}),
      .merge_protocol_error(producer_merge_protocol_error[{producer}]),
      .protocol_error(producer_protocol_error[{producer}])
  );"""
        )
    return "\n\n".join(blocks)


def _verilator_lint_stubs(*, producer_top: str, reducer_top: str, producers: int, head_id_bits: int) -> str:
    slice_bits = 4
    return f"""// Auto-generated Verilator wrapper-lint blackboxes for score32 exact local cluster GQA8
(* blackbox *) module {producer_top} (
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
endmodule

(* blackbox *) module {reducer_top} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{producers - 1}:0] leaf_valid,
    output wire [{producers - 1}:0] leaf_ready,
    input  wire [{producers * 16 - 1}:0] leaf_command_id,
    input  wire [{producers * head_id_bits - 1}:0] leaf_head_id,
    input  wire [{producers * 32 - 1}:0] leaf_global_max,
    input  wire [{producers * 33 - 1}:0] leaf_exp_sum,
    input  wire [{producers * slice_bits - 1}:0] leaf_slice,
    input  wire [{producers - 1}:0] leaf_last,
    input  wire [{producers * PARTIAL_PAYLOAD_BITS - 1}:0] leaf_value,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_command_id,
    output wire [{head_id_bits - 1}:0] out_head_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [{slice_bits - 1}:0] out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output wire [2:0]   active_wave_index,
    output wire         emitting,
    output wire [4:0]   active_head_base,
    output wire [6:0]   collect_beat_index,
    output wire [6:0]   emit_beat_index,
    output wire [31:0]  cycle_count,
    output wire [31:0]  local_root_completed_count,
    output wire [31:0]  temporal_merge_completed_count,
    output wire [31:0]  emitted_beat_count,
    output wire [31:0]  completed_command_count,
    output wire [31:0]  local_stall_cycles,
    output wire [31:0]  output_stall_cycles,
    output wire         group_contract_error,
    output wire         local_tree_protocol_error,
    output wire         temporal_merge_protocol_error,
    output wire         protocol_error
);
endmodule
"""


def _top(*, top_name: str, producer_top: str, reducer_top: str, producers: int, head_id_bits: int) -> str:
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_local_cluster_gqa8.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [{head_id_bits - 1}:0] command_head_base,
    input  wire [{(producers * 15) - 1}:0] command_block_count,
    input  wire [31:0]  command_score_multiplier,
    input  wire [5:0]   command_score_shift,
    input  wire [{producers - 1}:0] input_valid,
    output wire [{producers - 1}:0] input_ready,
    input  wire [{producers - 1}:0] input_last,
    input  wire signed [{(producers * 128) - 1}:0] input_query,
    input  wire signed [{(producers * 128) - 1}:0] input_key,
    output wire [{(producers * 2) - 1}:0] value_read_req_valid,
    input  wire [{(producers * 2) - 1}:0] value_read_req_ready,
    output wire [{(producers * 28) - 1}:0] value_read_req_address,
    output wire [{(producers * 8) - 1}:0] value_read_req_slice,
    input  wire [{(producers * 2) - 1}:0] value_response_valid,
    output wire [{(producers * 2) - 1}:0] value_response_ready,
    input  wire [{(producers * 28) - 1}:0] value_response_address,
    input  wire [{(producers * 8) - 1}:0] value_response_slice,
    input  wire [{(producers * 1024) - 1}:0] value_response_matrix,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_command_id,
    output wire [{head_id_bits - 1}:0] out_head_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [3:0]   out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output wire [31:0]  cluster_cycle_count,
    output wire [31:0]  wave_command_accept_count,
    output wire [31:0]  wave_command_issue_wait_cycles,
    output wire [31:0]  producer_ready_skew_cycles,
    output wire [2:0]   reducer_active_wave_index,
    output wire         reducer_emitting,
    output wire [4:0]   reducer_active_head_base,
    output wire [6:0]   reducer_collect_beat_index,
    output wire [6:0]   reducer_emit_beat_index,
    output wire [31:0]  reducer_cycle_count,
    output wire [31:0]  reducer_local_root_completed_count,
    output wire [31:0]  reducer_temporal_merge_completed_count,
    output wire [31:0]  reducer_emitted_beat_count,
    output wire [31:0]  reducer_completed_command_count,
    output wire [31:0]  reducer_local_stall_cycles,
    output wire [31:0]  reducer_output_stall_cycles,
    output wire [{(producers * 32) - 1}:0] producer_cycle_count,
    output wire [{(producers * 32) - 1}:0] producer_command_accept_count,
    output wire [{(producers * 32) - 1}:0] producer_command_completed_count,
    output wire [{(producers * 64) - 1}:0] producer_stream_command_accept_count,
    output wire [{(producers * 64) - 1}:0] producer_stream_completed_count,
    output wire [{(producers * 32) - 1}:0] producer_merge_completed_count,
    output wire [{(producers * 32) - 1}:0] producer_result_stall_cycles,
    output wire [{(producers * 2) - 1}:0] producer_stream_protocol_error,
    output wire [{producers - 1}:0] producer_merge_protocol_error,
    output wire [{producers - 1}:0] producer_protocol_error,
    output wire         group_contract_error,
    output wire         local_tree_protocol_error,
    output wire         temporal_merge_protocol_error,
    output wire         reducer_protocol_error,
    output wire         atomic_command_protocol_error,
    output wire         protocol_error
);
  localparam integer PRODUCERS = {producers};
  localparam integer HEAD_ID_BITS = {head_id_bits};
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};

  wire [PRODUCERS-1:0] producer_command_ready_w;
  wire [PRODUCERS-1:0] producer_result_valid_w;
  wire [PRODUCERS-1:0] producer_result_ready_w;
  wire [(PRODUCERS * 16) - 1:0] producer_result_command_id_w;
  wire [(PRODUCERS * HEAD_ID_BITS) - 1:0] producer_result_head_id_w;
  wire [(PRODUCERS * 32) - 1:0] producer_result_global_max_w;
  wire [(PRODUCERS * 33) - 1:0] producer_result_exp_sum_w;
  wire [(PRODUCERS * 4) - 1:0] producer_result_slice_w;
  wire [PRODUCERS-1:0] producer_result_last_w;
  wire [(PRODUCERS * PARTIAL_PAYLOAD_BITS) - 1:0] producer_result_value_w;

  wire group_command_fire_w = command_valid && command_ready;
  wire [PRODUCERS-1:0] producer_command_accept_w = {{PRODUCERS{{group_command_fire_w}}}} & producer_command_ready_w;

  reg [31:0] cluster_cycle_count_q;
  reg [31:0] wave_command_accept_count_q;
  reg [31:0] wave_command_issue_wait_cycles_q;
  reg [31:0] producer_ready_skew_cycles_q;
  reg atomic_command_protocol_error_q;

  assign command_ready = &producer_command_ready_w;
  assign cluster_cycle_count = cluster_cycle_count_q;
  assign wave_command_accept_count = wave_command_accept_count_q;
  assign wave_command_issue_wait_cycles = wave_command_issue_wait_cycles_q;
  assign producer_ready_skew_cycles = producer_ready_skew_cycles_q;
  assign atomic_command_protocol_error = atomic_command_protocol_error_q;
  assign protocol_error = atomic_command_protocol_error_q || (|producer_protocol_error) || reducer_protocol_error;

{_producer_instances(producer_top=producer_top, producers=producers)}

  {reducer_top} u_reducer (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(producer_result_valid_w),
      .leaf_ready(producer_result_ready_w),
      .leaf_command_id(producer_result_command_id_w),
      .leaf_head_id(producer_result_head_id_w),
      .leaf_global_max(producer_result_global_max_w),
      .leaf_exp_sum(producer_result_exp_sum_w),
      .leaf_slice(producer_result_slice_w),
      .leaf_last(producer_result_last_w),
      .leaf_value(producer_result_value_w),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_command_id(out_command_id),
      .out_head_id(out_head_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .active_wave_index(reducer_active_wave_index),
      .emitting(reducer_emitting),
      .active_head_base(reducer_active_head_base),
      .collect_beat_index(reducer_collect_beat_index),
      .emit_beat_index(reducer_emit_beat_index),
      .cycle_count(reducer_cycle_count),
      .local_root_completed_count(reducer_local_root_completed_count),
      .temporal_merge_completed_count(reducer_temporal_merge_completed_count),
      .emitted_beat_count(reducer_emitted_beat_count),
      .completed_command_count(reducer_completed_command_count),
      .local_stall_cycles(reducer_local_stall_cycles),
      .output_stall_cycles(reducer_output_stall_cycles),
      .group_contract_error(group_contract_error),
      .local_tree_protocol_error(local_tree_protocol_error),
      .temporal_merge_protocol_error(temporal_merge_protocol_error),
      .protocol_error(reducer_protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cluster_cycle_count_q <= 32'd0;
      wave_command_accept_count_q <= 32'd0;
      wave_command_issue_wait_cycles_q <= 32'd0;
      producer_ready_skew_cycles_q <= 32'd0;
      atomic_command_protocol_error_q <= 1'b0;
    end else begin
      cluster_cycle_count_q <= cluster_cycle_count_q + 1'b1;
      if (command_valid && !command_ready) begin
        wave_command_issue_wait_cycles_q <= wave_command_issue_wait_cycles_q + 1'b1;
      end
      if (command_valid && (|producer_command_ready_w) && !(&producer_command_ready_w)) begin
        producer_ready_skew_cycles_q <= producer_ready_skew_cycles_q + 1'b1;
      end
      if (group_command_fire_w) begin
        wave_command_accept_count_q <= wave_command_accept_count_q + 1'b1;
        if (producer_command_accept_w != {{PRODUCERS{{1'b1}}}}) begin
          atomic_command_protocol_error_q <= 1'b1;
        end
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    producer_top = f"{top_name}__producer"
    reducer_top = f"{top_name}__reducer"

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_cluster_gqa8_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        producer_dir = temp_dir / "producer"
        reducer_dir = temp_dir / "reducer"
        generate_producer(
            {
                "top_name": producer_top,
                "attention_score32_exact_partial_gqa8_dual_stream_producer": {
                    "streams": 2,
                    "query_heads_per_stream": 8,
                    "max_blocks": int(params["max_blocks"]),
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                },
            },
            producer_dir,
        )
        generate_reducer(
            {
                "top_name": reducer_top,
                "attention_score32_exact_local_temporal_reducer_gqa8": {
                    "producers": int(params["producers"]),
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "persistent_waves": int(params["persistent_waves"]),
                },
            },
            reducer_dir,
        )
        producer_rtl = (producer_dir / "top.v").read_text(encoding="utf-8")
        reducer_rtl = (reducer_dir / "top.v").read_text(encoding="utf-8")
        producer_manifest = json.loads(
            (producer_dir / "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        reducer_manifest = json.loads(
            (reducer_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    top_text = _top(
        top_name=top_name,
        producer_top=producer_top,
        reducer_top=reducer_top,
        producers=int(params["producers"]),
        head_id_bits=int(params["head_id_bits"]),
    )
    (out_dir / _PRODUCER_RTL_NAME).write_text(producer_rtl + "\n", encoding="utf-8")
    (out_dir / _REDUCER_RTL_NAME).write_text(reducer_rtl + "\n", encoding="utf-8")
    (out_dir / "top.v").write_text(top_text + "\n", encoding="utf-8")
    (out_dir / _VERILATOR_LINT_STUBS_NAME).write_text(
        _verilator_lint_stubs(
            producer_top=producer_top,
            reducer_top=reducer_top,
            producers=int(params["producers"]),
            head_id_bits=int(params["head_id_bits"]),
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    service_model = exact_local_cluster_gqa8_service_manifest(
        producers=int(params["producers"]),
        waves=int(params["persistent_waves"]),
    )
    manifest: JsonDict = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_cluster_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local_cluster_gqa8_v1",
        "producers": int(params["producers"]),
        "producer_instance_count": int(params["producers"]),
        "max_blocks": int(params["max_blocks"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "persistent_waves": int(params["persistent_waves"]),
        "query_head_groups": 4,
        "query_heads_per_group": 8,
        "value_memory_lanes": int(params["producers"]) * 2,
        "producer_input_lanes": int(params["producers"]),
        "result_interface": "full_width_exact_gqa8_producer_cluster_to_128beat_aggregate_after_group_major_8wave_reduce",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "rtl_files": [
            "top.v",
            _PRODUCER_RTL_NAME,
            _REDUCER_RTL_NAME,
            _VERILATOR_LINT_STUBS_NAME,
        ],
        "top_pin_bits": _top_pin_bits(
            producers=int(params["producers"]),
            head_id_bits=int(params["head_id_bits"]),
        ),
        "command_schedule_contract": service_model["top_command_contract"],
        "atomic_command_issue_contract": service_model["atomic_command_issue_contract"],
        "producer_input_contract": service_model["producer_input_contract"],
        "value_memory_contract": service_model["value_memory_contract"],
        "producer_leaf_wiring_contract": service_model["producer_leaf_wiring_contract"],
        "local_reduction_contract": service_model["local_reduction_contract"],
        "temporal_accumulation_contract": service_model["temporal_accumulation_contract"],
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "remaining_abstractions": service_model["remaining_abstractions"],
        "service_model": service_model,
        "submodule_manifests": {
            "producer": producer_manifest,
            "gqa8_local_temporal_reducer": reducer_manifest,
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    report_links = config.get("report_links")
    if isinstance(report_links, dict):
        if "proposal_id" in report_links:
            manifest["linked_proposal_id"] = str(report_links["proposal_id"])
        if "proposal_path" in report_links:
            manifest["linked_proposal_path"] = str(report_links["proposal_path"])
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
