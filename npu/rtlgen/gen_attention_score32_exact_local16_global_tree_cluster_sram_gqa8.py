#!/usr/bin/env python3
"""Generate the full score32 exact GQA8 hierarchy with one local SRAM endpoint per cluster."""

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

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate as generate_banked_tree
from npu.rtlgen.gen_attention_score32_exact_cluster_sram_composed_gqa8 import generate as generate_cluster_sram
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local16_global_tree_cluster_sram_gqa8_service_manifest,
)

JsonDict = dict[str, Any]

CONFIG_KEY = "attention_score32_exact_local16_global_tree_cluster_sram_gqa8"
MANIFEST_NAME = "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json"
_CLUSTER_MANIFEST = "attention_score32_exact_cluster_sram_composed_gqa8_manifest.json"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    cluster_producers = tuple(int(value) for value in body.get("cluster_producers", []))
    params = {
        "top_name": top_name,
        "clusters": int(body.get("clusters", 16)),
        "cluster_producers": cluster_producers,
        "radix": int(body.get("radix", 2)),
        "value_slices": int(body.get("value_slices", 16)),
        "head_id_bits": int(body.get("head_id_bits", 5)),
        "persistent_waves": int(body.get("persistent_waves", LOCAL_TEMPORAL_WAVES)),
        "divider_lanes": int(body.get("divider_lanes", 8)),
        "finalizer_banks": int(body.get("finalizer_banks", 59)),
    }
    if params["clusters"] != 16:
        raise SystemExit("clusters must remain fixed at 16")
    if cluster_producers != tuple([54] * 8 + [53] * 8):
        raise SystemExit("cluster_producers must be exactly eight 54s followed by eight 53s")
    if params["radix"] != 2 or params["value_slices"] != 16 or params["head_id_bits"] != 5:
        raise SystemExit("wrapper requires radix=2, value_slices=16, and head_id_bits=5")
    if params["persistent_waves"] != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    if params["divider_lanes"] != 8 or params["finalizer_banks"] != 59:
        raise SystemExit("wrapper must remain on the c16/r2/l8/b59 finalized tree")
    return params


def build_default_config() -> JsonDict:
    return {
        "top_name": "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_p54x8_p53x8_c16_r2_l8_b59",
        CONFIG_KEY: {
            "clusters": 16,
            "cluster_producers": [54] * 8 + [53] * 8,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "persistent_waves": LOCAL_TEMPORAL_WAVES,
            "divider_lanes": 8,
            "finalizer_banks": 59,
        },
        "probe_defaults": {
            "head_bases": [0, 8, 16, 24],
            "waves": LOCAL_TEMPORAL_WAVES,
            "seed": 29,
        },
    }


def _slice(name: str, index: int, width: int) -> str:
    return f"{name}[{index * width} +: {width}]"


def _partition(name: str, producer_base: int, producers: int, width_per_producer: int) -> str:
    return f"{name}[{producer_base * width_per_producer} +: {producers * width_per_producer}]"


def _cluster_instance(*, cluster: int, producers: int, producer_base: int, cluster_top: str) -> str:
    return f"""  {cluster_top} u_cluster_{cluster} (
      .clk(clk),
      .rst_n(rst_n),
      .fill_target_valid(fill_target_valid[{cluster}] && fill_target_schedule_allowed_w[{cluster}]),
      .fill_target_ready(fill_target_ready_internal_w[{cluster}]),
      .fill_target_buffer_sel(fill_target_buffer_sel[{cluster}]),
      .fill_target_command_id({_slice("fill_target_command_id", cluster, 16)}),
      .fill_target_head_base({_slice("fill_target_head_base", cluster, 5)}),
      .fill_target_wave_index({_slice("fill_target_wave_index", cluster, 3)}),
      .fill_valid(fill_valid[{cluster}]),
      .fill_ready(fill_ready[{cluster}]),
      .fill_buffer_sel(fill_buffer_sel[{cluster}]),
      .fill_stream(fill_stream[{cluster}]),
      .fill_block_slot({_slice("fill_block_slot", cluster, 6)}),
      .fill_slice({_slice("fill_slice", cluster, 4)}),
      .fill_data({_slice("fill_data", cluster, 512)}),
      .command_valid(command_fire_w),
      .command_ready(),
      .compute_command_ready(cluster_compute_command_ready_w[{cluster}]),
      .sram_command_ready(cluster_sram_command_ready_w[{cluster}]),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_wave_index(schedule_wave_q),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid({_partition("input_valid", producer_base, producers, 1)}),
      .input_ready({_partition("input_ready", producer_base, producers, 1)}),
      .input_last({_partition("input_last", producer_base, producers, 1)}),
      .input_query({_partition("input_query", producer_base, producers, 128)}),
      .input_key({_partition("input_key", producer_base, producers, 128)}),
      .out_valid(cluster_out_valid_w[{cluster}]),
      .out_ready(cluster_out_ready_w[{cluster}]),
      .out_command_id({_slice("cluster_out_command_id_w", cluster, 16)}),
      .out_head_id({_slice("cluster_out_head_id_w", cluster, 5)}),
      .out_global_max({_slice("cluster_out_global_max_w", cluster, 32)}),
      .out_exp_sum({_slice("cluster_out_exp_sum_w", cluster, 33)}),
      .out_slice({_slice("cluster_out_slice_w", cluster, 4)}),
      .out_last(cluster_out_last_w[{cluster}]),
      .out_value({_slice("cluster_out_value_w", cluster, PARTIAL_PAYLOAD_BITS)}),
      .cluster_cycle_count({_slice("cluster_cycle_count", cluster, 32)}),
      .wave_command_accept_count({_slice("cluster_wave_command_accept_count", cluster, 32)}),
      .wave_command_issue_wait_cycles({_slice("cluster_wave_command_issue_wait_cycles", cluster, 32)}),
      .producer_ready_skew_cycles({_slice("cluster_producer_ready_skew_cycles", cluster, 32)}),
      .reducer_active_wave_index(),
      .reducer_emitting(),
      .reducer_active_head_base(),
      .reducer_collect_beat_index(),
      .reducer_emit_beat_index(),
      .reducer_cycle_count(),
      .reducer_local_root_completed_count(),
      .reducer_temporal_merge_completed_count(),
      .reducer_emitted_beat_count({_slice("cluster_emitted_beat_count", cluster, 32)}),
      .reducer_completed_command_count({_slice("cluster_completed_command_count", cluster, 32)}),
      .reducer_local_stall_cycles(),
      .reducer_output_stall_cycles(),
      .producer_cycle_count(),
      .producer_command_accept_count(),
      .producer_command_completed_count(),
      .producer_stream_command_accept_count(),
      .producer_stream_completed_count(),
      .producer_merge_completed_count(),
      .producer_result_stall_cycles(),
      .producer_stream_protocol_error(),
      .producer_merge_protocol_error(),
      .producer_protocol_error(),
      .group_contract_error(cluster_group_contract_error[{cluster}]),
      .local_tree_protocol_error(cluster_local_tree_protocol_error[{cluster}]),
      .temporal_merge_protocol_error(cluster_temporal_merge_protocol_error[{cluster}]),
      .reducer_protocol_error(cluster_reducer_protocol_error[{cluster}]),
      .atomic_command_protocol_error(cluster_atomic_command_protocol_error[{cluster}]),
      .sram_cycle_count({_slice("cluster_sram_cycle_count", cluster, 32)}),
      .sram_fill_target_accept_count({_slice("cluster_sram_fill_target_accept_count", cluster, 32)}),
      .sram_fill_row_accept_count({_slice("cluster_sram_fill_row_accept_count", cluster, 32)}),
      .sram_fill_stall_cycles({_slice("cluster_sram_fill_stall_cycles", cluster, 32)}),
      .sram_request_accept_count({_slice("cluster_sram_request_accept_count", cluster, 32)}),
      .sram_request_stall_cycles({_slice("cluster_sram_request_stall_cycles", cluster, 32)}),
      .sram_response_accept_count({_slice("cluster_sram_response_accept_count", cluster, 32)}),
      .sram_response_stall_cycles({_slice("cluster_sram_response_stall_cycles", cluster, 32)}),
      .sram_bank_conflict_count({_slice("cluster_sram_bank_conflict_count", cluster, 32)}),
      .sram_command_accept_count({_slice("cluster_sram_command_accept_count", cluster, 32)}),
      .sram_command_release_count({_slice("cluster_sram_command_release_count", cluster, 32)}),
      .sram_buffer0_occupancy_rows({_slice("cluster_sram_buffer0_occupancy_rows", cluster, 12)}),
      .sram_buffer1_occupancy_rows({_slice("cluster_sram_buffer1_occupancy_rows", cluster, 12)}),
      .sram_outstanding_response_occupancy({_slice("cluster_sram_outstanding_response_occupancy", cluster, 8)}),
      .sram_invalid_metadata_error(cluster_sram_invalid_metadata_error[{cluster}]),
      .sram_invalid_address_error(cluster_sram_invalid_address_error[{cluster}]),
      .sram_residency_error(cluster_sram_residency_error[{cluster}]),
      .sram_overwrite_error(cluster_sram_overwrite_error[{cluster}]),
      .sram_command_error(cluster_sram_command_error[{cluster}]),
      .sram_buffer_map_error(cluster_sram_buffer_map_error[{cluster}]),
      .sram_release_guard_error(cluster_sram_release_guard_error[{cluster}]),
      .sram_protocol_error(cluster_sram_protocol_error[{cluster}]),
      .protocol_error(cluster_protocol_error[{cluster}])
  );"""


def _top_pin_bits() -> int:
    widths = [
        1,
        1,
        1,
        1,
        16,
        16,
        16,
        256,
        80,
        48,
        16,
        16,
        16,
        16,
        96,
        64,
        8192,
        856,
        856,
        856,
        109568,
        109568,
        1,
        1,
        16,
        5,
        32,
        33,
        4,
        1,
        320,
        5,
        3,
        32,
        1,
        16,
        1,
        512,
        512,
        512,
        512,
        512,
        512,
        16,
        16,
        16,
        16,
        16,
        16,
        512,
        512,
        512,
        512,
        512,
        512,
        512,
        512,
        512,
        512,
        512,
        192,
        192,
        128,
        16,
        16,
        16,
        16,
        16,
        16,
        16,
        16,
        32,
        32,
        32,
        32,
        32,
        32,
        32,
        32,
        32,
        32,
        480,
        128,
        15,
        4,
        59,
        59,
        1,
        1,
        1,
        1,
        1,
        1,
    ]
    return sum(widths)


def _top(*, top_name: str, p54_cluster_top: str, p53_cluster_top: str, global_tree_top: str) -> str:
    cluster_instances: list[str] = []
    producer_base = 0
    for cluster, producers in enumerate([54] * 8 + [53] * 8):
        cluster_instances.append(
            _cluster_instance(
                cluster=cluster,
                producers=producers,
                producer_base=producer_base,
                cluster_top=p54_cluster_top if producers == 54 else p53_cluster_top,
            )
        )
        producer_base += producers
    instances = "\n\n".join(cluster_instances)
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py
module {top_name} (
    input  wire clk,
    input  wire rst_n,
    input  wire command_valid,
    output wire command_ready,
    input  wire [15:0] command_id,
    input  wire [4:0] command_head_base,
    input  wire [31:0] command_score_multiplier,
    input  wire [5:0] command_score_shift,
    input  wire [15:0] fill_target_valid,
    output wire [15:0] fill_target_ready,
    input  wire [15:0] fill_target_buffer_sel,
    input  wire [255:0] fill_target_command_id,
    input  wire [79:0] fill_target_head_base,
    input  wire [47:0] fill_target_wave_index,
    input  wire [15:0] fill_valid,
    output wire [15:0] fill_ready,
    input  wire [15:0] fill_buffer_sel,
    input  wire [15:0] fill_stream,
    input  wire [95:0] fill_block_slot,
    input  wire [63:0] fill_slice,
    input  wire [8191:0] fill_data,
    input  wire [855:0] input_valid,
    output wire [855:0] input_ready,
    input  wire [855:0] input_last,
    input  wire signed [109567:0] input_query,
    input  wire signed [109567:0] input_key,
    output wire root_valid,
    input  wire root_ready,
    output wire [15:0] root_command_id,
    output wire [4:0] root_head_id,
    output wire [3:0] root_slice,
    output wire root_last,
    output wire [319:0] root_value,
    output wire [4:0] expected_head_base,
    output wire [2:0] expected_wave_index,
    output wire [31:0] cadence_command_accept_count,
    output wire command_cadence_error,
    output wire [15:0] cluster_fill_schedule_contract_error,
    output wire fill_schedule_contract_error,
    output wire [511:0] cluster_cycle_count,
    output wire [511:0] cluster_wave_command_accept_count,
    output wire [511:0] cluster_wave_command_issue_wait_cycles,
    output wire [511:0] cluster_producer_ready_skew_cycles,
    output wire [511:0] cluster_emitted_beat_count,
    output wire [511:0] cluster_completed_command_count,
    output wire [15:0] cluster_group_contract_error,
    output wire [15:0] cluster_local_tree_protocol_error,
    output wire [15:0] cluster_temporal_merge_protocol_error,
    output wire [15:0] cluster_reducer_protocol_error,
    output wire [15:0] cluster_atomic_command_protocol_error,
    output wire [511:0] cluster_sram_cycle_count,
    output wire [511:0] cluster_sram_fill_target_accept_count,
    output wire [511:0] cluster_sram_fill_row_accept_count,
    output wire [511:0] cluster_sram_fill_stall_cycles,
    output wire [511:0] cluster_sram_request_accept_count,
    output wire [511:0] cluster_sram_request_stall_cycles,
    output wire [511:0] cluster_sram_response_accept_count,
    output wire [511:0] cluster_sram_response_stall_cycles,
    output wire [511:0] cluster_sram_bank_conflict_count,
    output wire [511:0] cluster_sram_command_accept_count,
    output wire [511:0] cluster_sram_command_release_count,
    output wire [191:0] cluster_sram_buffer0_occupancy_rows,
    output wire [191:0] cluster_sram_buffer1_occupancy_rows,
    output wire [127:0] cluster_sram_outstanding_response_occupancy,
    output wire [15:0] cluster_sram_invalid_metadata_error,
    output wire [15:0] cluster_sram_invalid_address_error,
    output wire [15:0] cluster_sram_residency_error,
    output wire [15:0] cluster_sram_overwrite_error,
    output wire [15:0] cluster_sram_command_error,
    output wire [15:0] cluster_sram_buffer_map_error,
    output wire [15:0] cluster_sram_release_guard_error,
    output wire [15:0] cluster_sram_protocol_error,
    output wire [31:0] global_cycle_count,
    output wire [31:0] global_root_completed_count,
    output wire [31:0] global_finalizer_accepted_count,
    output wire [31:0] global_tree_root_completed_count,
    output wire [31:0] global_order_fifo_occupancy,
    output wire [31:0] global_order_fifo_high_watermark,
    output wire [31:0] global_order_enqueued_count,
    output wire [31:0] global_order_dequeued_count,
    output wire [31:0] global_dispatch_stall_cycles,
    output wire [31:0] global_dispatch_bank_id,
    output wire [31:0] global_head_bank_id,
    output wire [479:0] global_node_completed_count,
    output wire [127:0] global_stage_completed_count,
    output wire [14:0] global_node_protocol_error,
    output wire [3:0] global_stage_protocol_error,
    output wire [58:0] global_bank_protocol_error,
    output wire [58:0] global_bank_outstanding,
    output wire global_tree_protocol_error,
    output wire global_order_protocol_error,
    output wire global_finalizer_protocol_error,
    output wire global_protocol_error,
    output wire [15:0] cluster_protocol_error,
    output wire protocol_error
);
  wire [15:0] cluster_compute_command_ready_w;
  wire [15:0] cluster_sram_command_ready_w;
  wire [15:0] fill_target_ready_internal_w;
  wire [15:0] fill_target_schedule_allowed_w;
  wire [15:0] fill_target_metadata_valid_w;
  wire [15:0] cluster_out_valid_w;
  wire [15:0] cluster_out_ready_w;
  wire [255:0] cluster_out_command_id_w;
  wire [79:0] cluster_out_head_id_w;
  wire [511:0] cluster_out_global_max_w;
  wire [527:0] cluster_out_exp_sum_w;
  wire [63:0] cluster_out_slice_w;
  wire [15:0] cluster_out_last_w;
  wire [5247:0] cluster_out_value_w;
  reg [1:0] schedule_head_group_q;
  reg [2:0] schedule_wave_q;
  reg [31:0] cadence_command_accept_count_q;
  reg command_cadence_error_q;
  reg [15:0] cluster_fill_schedule_contract_error_q;
  wire [4:0] expected_head_base_w = {{schedule_head_group_q, 3'd0}};
  wire [1:0] next_schedule_head_group_w =
      (schedule_wave_q == 3'd7) ? ((schedule_head_group_q == 2'd3) ? 2'd0 : (schedule_head_group_q + 2'd1)) :
      schedule_head_group_q;
  wire [2:0] next_schedule_wave_w = (schedule_wave_q == 3'd7) ? 3'd0 : (schedule_wave_q + 3'd1);
  wire [4:0] next_expected_head_base_w = {{next_schedule_head_group_w, 3'd0}};
  wire command_head_base_match_w = (command_head_base == expected_head_base_w);
  wire command_fire_w = command_valid && command_ready;

  assign expected_head_base = expected_head_base_w;
  assign expected_wave_index = schedule_wave_q;
  assign cadence_command_accept_count = cadence_command_accept_count_q;
  assign command_cadence_error = command_cadence_error_q;
  assign cluster_fill_schedule_contract_error = cluster_fill_schedule_contract_error_q;
  assign fill_schedule_contract_error = |cluster_fill_schedule_contract_error_q;
  assign command_ready = command_head_base_match_w && (&cluster_compute_command_ready_w) && (&cluster_sram_command_ready_w);
  generate
    genvar gfill;
    for (gfill = 0; gfill < 16; gfill = gfill + 1) begin : g_fill_schedule
      assign fill_target_metadata_valid_w[gfill] =
          (fill_target_head_base[(gfill * 5) +: 5] == 5'd0) ||
          (fill_target_head_base[(gfill * 5) +: 5] == 5'd8) ||
          (fill_target_head_base[(gfill * 5) +: 5] == 5'd16) ||
          (fill_target_head_base[(gfill * 5) +: 5] == 5'd24);
      assign fill_target_schedule_allowed_w[gfill] =
          ((fill_target_head_base[(gfill * 5) +: 5] == expected_head_base_w) &&
           (fill_target_wave_index[(gfill * 3) +: 3] == schedule_wave_q)) ||
          ((fill_target_head_base[(gfill * 5) +: 5] == next_expected_head_base_w) &&
           (fill_target_wave_index[(gfill * 3) +: 3] == next_schedule_wave_w));
      assign fill_target_ready[gfill] =
          fill_target_schedule_allowed_w[gfill] ? fill_target_ready_internal_w[gfill] : 1'b0;
    end
  endgenerate

{instances}

  {global_tree_top} u_global_tree (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(cluster_out_valid_w),
      .leaf_ready(cluster_out_ready_w),
      .leaf_command_id(cluster_out_command_id_w),
      .leaf_head_id(cluster_out_head_id_w),
      .leaf_global_max(cluster_out_global_max_w),
      .leaf_exp_sum(cluster_out_exp_sum_w),
      .leaf_slice(cluster_out_slice_w),
      .leaf_last(cluster_out_last_w),
      .leaf_value(cluster_out_value_w),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(global_cycle_count),
      .root_completed_count(global_root_completed_count),
      .finalizer_accepted_count(global_finalizer_accepted_count),
      .tree_root_completed_count(global_tree_root_completed_count),
      .order_fifo_occupancy(global_order_fifo_occupancy),
      .order_fifo_high_watermark(global_order_fifo_high_watermark),
      .order_enqueued_count(global_order_enqueued_count),
      .order_dequeued_count(global_order_dequeued_count),
      .dispatch_stall_cycles(global_dispatch_stall_cycles),
      .dispatch_bank_id(global_dispatch_bank_id),
      .head_bank_id(global_head_bank_id),
      .node_completed_count(global_node_completed_count),
      .stage_completed_count(global_stage_completed_count),
      .node_protocol_error(global_node_protocol_error),
      .stage_protocol_error(global_stage_protocol_error),
      .bank_protocol_error(global_bank_protocol_error),
      .bank_outstanding(global_bank_outstanding),
      .tree_protocol_error(global_tree_protocol_error),
      .order_protocol_error(global_order_protocol_error),
      .finalizer_protocol_error(global_finalizer_protocol_error),
      .protocol_error(global_protocol_error)
  );

  assign protocol_error = command_cadence_error_q || fill_schedule_contract_error || (|cluster_protocol_error) ||
      (|cluster_sram_protocol_error) || global_protocol_error;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      schedule_head_group_q <= 2'd0;
      schedule_wave_q <= 3'd0;
      cadence_command_accept_count_q <= 32'd0;
      command_cadence_error_q <= 1'b0;
      cluster_fill_schedule_contract_error_q <= 16'd0;
    end else begin
      if (command_valid && (&cluster_compute_command_ready_w) && (&cluster_sram_command_ready_w) &&
          !command_head_base_match_w) begin
        command_cadence_error_q <= 1'b1;
      end
      if (fill_target_valid[0] && (!fill_target_metadata_valid_w[0] || !fill_target_schedule_allowed_w[0]))
        cluster_fill_schedule_contract_error_q[0] <= 1'b1;
      if (fill_target_valid[1] && (!fill_target_metadata_valid_w[1] || !fill_target_schedule_allowed_w[1]))
        cluster_fill_schedule_contract_error_q[1] <= 1'b1;
      if (fill_target_valid[2] && (!fill_target_metadata_valid_w[2] || !fill_target_schedule_allowed_w[2]))
        cluster_fill_schedule_contract_error_q[2] <= 1'b1;
      if (fill_target_valid[3] && (!fill_target_metadata_valid_w[3] || !fill_target_schedule_allowed_w[3]))
        cluster_fill_schedule_contract_error_q[3] <= 1'b1;
      if (fill_target_valid[4] && (!fill_target_metadata_valid_w[4] || !fill_target_schedule_allowed_w[4]))
        cluster_fill_schedule_contract_error_q[4] <= 1'b1;
      if (fill_target_valid[5] && (!fill_target_metadata_valid_w[5] || !fill_target_schedule_allowed_w[5]))
        cluster_fill_schedule_contract_error_q[5] <= 1'b1;
      if (fill_target_valid[6] && (!fill_target_metadata_valid_w[6] || !fill_target_schedule_allowed_w[6]))
        cluster_fill_schedule_contract_error_q[6] <= 1'b1;
      if (fill_target_valid[7] && (!fill_target_metadata_valid_w[7] || !fill_target_schedule_allowed_w[7]))
        cluster_fill_schedule_contract_error_q[7] <= 1'b1;
      if (fill_target_valid[8] && (!fill_target_metadata_valid_w[8] || !fill_target_schedule_allowed_w[8]))
        cluster_fill_schedule_contract_error_q[8] <= 1'b1;
      if (fill_target_valid[9] && (!fill_target_metadata_valid_w[9] || !fill_target_schedule_allowed_w[9]))
        cluster_fill_schedule_contract_error_q[9] <= 1'b1;
      if (fill_target_valid[10] && (!fill_target_metadata_valid_w[10] || !fill_target_schedule_allowed_w[10]))
        cluster_fill_schedule_contract_error_q[10] <= 1'b1;
      if (fill_target_valid[11] && (!fill_target_metadata_valid_w[11] || !fill_target_schedule_allowed_w[11]))
        cluster_fill_schedule_contract_error_q[11] <= 1'b1;
      if (fill_target_valid[12] && (!fill_target_metadata_valid_w[12] || !fill_target_schedule_allowed_w[12]))
        cluster_fill_schedule_contract_error_q[12] <= 1'b1;
      if (fill_target_valid[13] && (!fill_target_metadata_valid_w[13] || !fill_target_schedule_allowed_w[13]))
        cluster_fill_schedule_contract_error_q[13] <= 1'b1;
      if (fill_target_valid[14] && (!fill_target_metadata_valid_w[14] || !fill_target_schedule_allowed_w[14]))
        cluster_fill_schedule_contract_error_q[14] <= 1'b1;
      if (fill_target_valid[15] && (!fill_target_metadata_valid_w[15] || !fill_target_schedule_allowed_w[15]))
        cluster_fill_schedule_contract_error_q[15] <= 1'b1;
      if (command_fire_w) begin
        cadence_command_accept_count_q <= cadence_command_accept_count_q + 1'b1;
        if (schedule_wave_q == 3'd7) begin
          schedule_wave_q <= 3'd0;
          schedule_head_group_q <= (schedule_head_group_q == 2'd3) ? 2'd0 : (schedule_head_group_q + 2'd1);
        end else begin
          schedule_wave_q <= schedule_wave_q + 3'd1;
        end
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    p54_cluster_top = f"{top_name}__cluster_p54"
    p53_cluster_top = f"{top_name}__cluster_p53"
    global_tree_top = f"{top_name}__global_tree"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="score32_exact_local16_global_tree_cluster_sram_") as temp_name:
        temp_dir = Path(temp_name)
        p54_dir = temp_dir / "p54"
        p53_dir = temp_dir / "p53"
        global_dir = temp_dir / "global"
        generate_cluster_sram(
            {
                "top_name": p54_cluster_top,
                "attention_score32_exact_cluster_sram_composed_gqa8": {
                    "producers": 54,
                    "head_id_bits": 5,
                    "persistent_waves": LOCAL_TEMPORAL_WAVES,
                },
            },
            p54_dir,
        )
        generate_cluster_sram(
            {
                "top_name": p53_cluster_top,
                "attention_score32_exact_cluster_sram_composed_gqa8": {
                    "producers": 53,
                    "head_id_bits": 5,
                    "persistent_waves": LOCAL_TEMPORAL_WAVES,
                },
            },
            p53_dir,
        )
        generate_banked_tree(
            {
                "top_name": global_tree_top,
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": 16,
                    "radix": 2,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": 8,
                    "finalizer_banks": 59,
                },
            },
            global_dir,
        )
        p54_rtl = (p54_dir / "top.v").read_text(encoding="utf-8").rstrip()
        p53_rtl = (p53_dir / "top.v").read_text(encoding="utf-8").rstrip()
        global_rtl = (global_dir / "top.v").read_text(encoding="utf-8").rstrip()
        p54_manifest = json.loads((p54_dir / _CLUSTER_MANIFEST).read_text(encoding="utf-8"))
        p53_manifest = json.loads((p53_dir / _CLUSTER_MANIFEST).read_text(encoding="utf-8"))
        global_manifest = json.loads(
            (global_dir / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text(encoding="utf-8")
        )

    rtl = "\n\n".join([p54_rtl, p53_rtl, global_rtl, _top(
        top_name=top_name,
        p54_cluster_top=p54_cluster_top,
        p53_cluster_top=p53_cluster_top,
        global_tree_top=global_tree_top,
    ).rstrip()]) + "\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cluster_producers = tuple(int(value) for value in params["cluster_producers"])
    service_model = exact_local16_global_tree_cluster_sram_gqa8_service_manifest(
        cluster_producers=cluster_producers,
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    manifest: JsonDict = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local16_global_tree_cluster_sram_gqa8_full_compute_v1",
        "clusters": 16,
        "cluster_producers": list(cluster_producers),
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": 856,
        "internal_value_memory_lanes": 1712,
        "external_fill_interfaces": 16,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "top_pin_bits": _top_pin_bits(),
        "result_interface": "856_real_dual_stream_producers_to_16_local_sram_clusters_to_c16_ordered_banked_finalized_root",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "command_schedule_contract": service_model["command_wave_contract"],
        "command_head_contract": service_model["command_head_contract"],
        "release_invariant_contract": service_model["release_invariant_contract"],
        "buffer_mapping_contract": service_model["buffer_mapping_contract"],
        "fill_prefetch_window_contract": service_model["fill_prefetch_window_contract"],
        "interface_adaptation": {
            "producer_inputs": "independent_flattened_ready_valid_query_key_lanes_for_all_856_producers",
            "external_fill": "sixteen_per_cluster_hbm_return_fill_target_and_fill_row_interfaces",
            "internal_value_memory": "all_1712_value_request_response_lanes are fully internal to the sixteen cluster SRAM endpoints",
            "local_to_global": "direct_16_cluster_output_mapping_without_field_remap",
        },
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": "none",
        "remaining_abstractions": service_model["remaining_abstractions"],
        "equivalence_hash": False,
        "service_model": service_model,
        "submodule_manifests": {
            "cluster_sram_composed_p54": p54_manifest,
            "cluster_sram_composed_p53": p53_manifest,
            "banked_tree": global_manifest,
            "cluster_instance_counts": {"p54": 8, "p53": 8},
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
