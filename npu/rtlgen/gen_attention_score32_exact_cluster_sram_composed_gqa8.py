#!/usr/bin/env python3
"""Generate a real-producer GQA8 local cluster composed with one local SRAM endpoint."""

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

from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import generate as generate_sram_service
from npu.rtlgen.gen_attention_score32_exact_local_cluster_gqa8 import generate as generate_cluster
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local_cluster_gqa8_service_manifest,
)
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    COMMAND_HEAD_BASE_W,
    COMMAND_WAVE_W,
    ROW_BITS,
    VALUE_SLICE_W,
    cluster_sram_service_manifest,
)

JsonDict = dict[str, Any]

CONFIG_KEY = "attention_score32_exact_cluster_sram_composed_gqa8"
MANIFEST_NAME = "attention_score32_exact_cluster_sram_composed_gqa8_manifest.json"
_CLUSTER_MANIFEST = "attention_score32_exact_local_cluster_gqa8_manifest.json"
_SRAM_MANIFEST = "attention_score32_exact_cluster_sram_service_gqa8_manifest.json"


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
    producers = int(body.get("producers", 53))
    head_id_bits = int(body.get("head_id_bits", 5))
    persistent_waves = int(body.get("persistent_waves", LOCAL_TEMPORAL_WAVES))
    if producers not in {53, 54}:
        raise SystemExit("producers must be exactly 53 or 54")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain fixed at 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    return {
        "top_name": top_name,
        "producers": producers,
        "head_id_bits": head_id_bits,
        "persistent_waves": persistent_waves,
    }


def build_default_config(*, producers: int = 53) -> JsonDict:
    producer_count = int(producers)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    return {
        "top_name": f"attention_score32_exact_cluster_sram_composed_gqa8_p{producer_count}",
        CONFIG_KEY: {
            "producers": producer_count,
            "head_id_bits": 5,
            "persistent_waves": LOCAL_TEMPORAL_WAVES,
        },
        "probe_defaults": {
            "head_bases": [0, 8, 16, 24],
            "waves": LOCAL_TEMPORAL_WAVES,
            "seed": 29,
        },
    }


def _slice(name: str, index: int, width: int) -> str:
    return f"{name}[{index * width} +: {width}]"


def _block_count_assignments(*, name: str, producers: int) -> str:
    if producers == 54:
        windows = ((0, 10), (10, 20), (20, 30), (30, 40))
    else:
        windows = ((0, 11), (11, 22), (22, 33), (33, 44))
    lines = [f"  wire [{producers * 15 - 1}:0] {name};"]
    for producer in range(producers):
        conditions = [
            f"((command_head_base[4:3] == 2'd{group}) && ({producer} >= {start}) && ({producer} < {stop}))"
            for group, (start, stop) in enumerate(windows)
        ]
        lines.append(
            f"  assign {name}[{producer * 15} +: 15] = ({' || '.join(conditions)}) ? 15'd2 : 15'd1;"
        )
    return "\n".join(lines)


def _top_pin_bits(*, producers: int, head_id_bits: int) -> int:
    return (
        1
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
        + 16
        + COMMAND_HEAD_BASE_W
        + COMMAND_WAVE_W
        + 1
        + 1
        + 1
        + 1
        + 6
        + VALUE_SLICE_W
        + ROW_BITS
        + 1
        + 1
        + 16
        + head_id_bits
        + COMMAND_WAVE_W
        + 32
        + 6
        + producers
        + producers
        + producers
        + (producers * 128)
        + (producers * 128)
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
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 12
        + 12
        + 8
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1
    )


def _top(*, top_name: str, cluster_top: str, sram_top: str, producers: int, head_id_bits: int) -> str:
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_cluster_sram_composed_gqa8.py
module {top_name} (
    input  wire clk,
    input  wire rst_n,
    input  wire fill_target_valid,
    output wire fill_target_ready,
    input  wire fill_target_buffer_sel,
    input  wire [15:0] fill_target_command_id,
    input  wire [{COMMAND_HEAD_BASE_W - 1}:0] fill_target_head_base,
    input  wire [{COMMAND_WAVE_W - 1}:0] fill_target_wave_index,
    input  wire fill_valid,
    output wire fill_ready,
    input  wire fill_buffer_sel,
    input  wire fill_stream,
    input  wire [5:0] fill_block_slot,
    input  wire [{VALUE_SLICE_W - 1}:0] fill_slice,
    input  wire [{ROW_BITS - 1}:0] fill_data,
    input  wire command_valid,
    output wire command_ready,
    output wire compute_command_ready,
    output wire sram_command_ready,
    input  wire [15:0] command_id,
    input  wire [{head_id_bits - 1}:0] command_head_base,
    input  wire [{COMMAND_WAVE_W - 1}:0] command_wave_index,
    input  wire [31:0] command_score_multiplier,
    input  wire [5:0] command_score_shift,
    input  wire [{producers - 1}:0] input_valid,
    output wire [{producers - 1}:0] input_ready,
    input  wire [{producers - 1}:0] input_last,
    input  wire signed [{(producers * 128) - 1}:0] input_query,
    input  wire signed [{(producers * 128) - 1}:0] input_key,
    output wire out_valid,
    input  wire out_ready,
    output wire [15:0] out_command_id,
    output wire [{head_id_bits - 1}:0] out_head_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0] out_exp_sum,
    output wire [3:0] out_slice,
    output wire out_last,
    output wire [327:0] out_value,
    output wire [31:0] cluster_cycle_count,
    output wire [31:0] wave_command_accept_count,
    output wire [31:0] wave_command_issue_wait_cycles,
    output wire [31:0] producer_ready_skew_cycles,
    output wire [2:0] reducer_active_wave_index,
    output wire reducer_emitting,
    output wire [4:0] reducer_active_head_base,
    output wire [6:0] reducer_collect_beat_index,
    output wire [6:0] reducer_emit_beat_index,
    output wire [31:0] reducer_cycle_count,
    output wire [31:0] reducer_local_root_completed_count,
    output wire [31:0] reducer_temporal_merge_completed_count,
    output wire [31:0] reducer_emitted_beat_count,
    output wire [31:0] reducer_completed_command_count,
    output wire [31:0] reducer_local_stall_cycles,
    output wire [31:0] reducer_output_stall_cycles,
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
    output wire group_contract_error,
    output wire local_tree_protocol_error,
    output wire temporal_merge_protocol_error,
    output wire reducer_protocol_error,
    output wire atomic_command_protocol_error,
    output wire [31:0] sram_cycle_count,
    output wire [31:0] sram_fill_target_accept_count,
    output wire [31:0] sram_fill_row_accept_count,
    output wire [31:0] sram_fill_stall_cycles,
    output wire [31:0] sram_request_accept_count,
    output wire [31:0] sram_request_stall_cycles,
    output wire [31:0] sram_response_accept_count,
    output wire [31:0] sram_response_stall_cycles,
    output wire [31:0] sram_bank_conflict_count,
    output wire [31:0] sram_command_accept_count,
    output wire [31:0] sram_command_release_count,
    output wire [11:0] sram_buffer0_occupancy_rows,
    output wire [11:0] sram_buffer1_occupancy_rows,
    output wire [7:0] sram_outstanding_response_occupancy,
    output wire sram_invalid_metadata_error,
    output wire sram_invalid_address_error,
    output wire sram_residency_error,
    output wire sram_overwrite_error,
    output wire sram_command_error,
    output wire sram_buffer_map_error,
    output wire sram_release_guard_error,
    output wire sram_protocol_error,
    output wire protocol_error
);
  localparam integer PRODUCERS = {producers};
  localparam integer HEAD_ID_BITS = {head_id_bits};

  wire [PRODUCERS*2-1:0] value_read_req_valid_w;
  wire [PRODUCERS*2-1:0] value_read_req_ready_w;
  wire [PRODUCERS*28-1:0] value_read_req_address_w;
  wire [PRODUCERS*8-1:0] value_read_req_slice_w;
  wire [PRODUCERS*2-1:0] value_response_valid_w;
  wire [PRODUCERS*2-1:0] value_response_ready_w;
  wire [PRODUCERS*28-1:0] value_response_address_w;
  wire [PRODUCERS*8-1:0] value_response_slice_w;
  wire [PRODUCERS*1024-1:0] value_response_matrix_w;
  wire cluster_command_ready_w;
  wire sram_command_ready_w;
  wire command_head_base_valid_w = (command_head_base[2:0] == 3'd0) && (command_head_base <= 5'd24);
  wire command_fire_w = command_valid && command_ready;
  wire fill_target_buffer_map_w = (fill_target_buffer_sel == fill_target_wave_index[0]);
  wire fill_target_ready_w;
  wire command_buffer_sel_w = command_wave_index[0];
  reg command_buffer_sel_q;
  reg [31:0] released_count_q;
  wire [PRODUCERS-1:0] producer_completed_match_w;
  wire all_producers_completed_w = &producer_completed_match_w;
  wire endpoint_responses_drained_w = (sram_outstanding_response_occupancy == 8'd0);
  wire release_count_pending_w = (wave_command_accept_count > released_count_q);
  wire release_invariant_satisfied_w =
      release_count_pending_w && all_producers_completed_w && endpoint_responses_drained_w;
  wire command_release_valid_w = release_invariant_satisfied_w;
  reg sram_buffer_map_error_q;
  reg sram_release_guard_error_q;

  assign command_ready = command_head_base_valid_w && cluster_command_ready_w && sram_command_ready_w;
  assign compute_command_ready = cluster_command_ready_w;
  assign sram_command_ready = sram_command_ready_w;
  assign fill_target_ready = fill_target_buffer_map_w ? fill_target_ready_w : 1'b0;
  assign sram_buffer_map_error = sram_buffer_map_error_q;
  assign sram_release_guard_error = sram_release_guard_error_q;
  assign sram_protocol_error = sram_invalid_metadata_error || sram_invalid_address_error ||
      sram_residency_error || sram_overwrite_error || sram_command_error ||
      sram_buffer_map_error_q || sram_release_guard_error_q;
  assign protocol_error = atomic_command_protocol_error || (|producer_protocol_error) ||
      reducer_protocol_error || sram_protocol_error;

{_block_count_assignments(name="command_block_count_w", producers=producers)}

  generate
    genvar gpi;
    for (gpi = 0; gpi < PRODUCERS; gpi = gpi + 1) begin : g_release_guard
      assign producer_completed_match_w[gpi] =
          (producer_command_completed_count[(gpi * 32) +: 32] == wave_command_accept_count);
    end
  endgenerate

  {cluster_top} u_compute_cluster (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_fire_w),
      .command_ready(cluster_command_ready_w),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_block_count(command_block_count_w),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_query(input_query),
      .input_key(input_key),
      .value_read_req_valid(value_read_req_valid_w),
      .value_read_req_ready(value_read_req_ready_w),
      .value_read_req_address(value_read_req_address_w),
      .value_read_req_slice(value_read_req_slice_w),
      .value_response_valid(value_response_valid_w),
      .value_response_ready(value_response_ready_w),
      .value_response_address(value_response_address_w),
      .value_response_slice(value_response_slice_w),
      .value_response_matrix(value_response_matrix_w),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_command_id(out_command_id),
      .out_head_id(out_head_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .cluster_cycle_count(cluster_cycle_count),
      .wave_command_accept_count(wave_command_accept_count),
      .wave_command_issue_wait_cycles(wave_command_issue_wait_cycles),
      .producer_ready_skew_cycles(producer_ready_skew_cycles),
      .reducer_active_wave_index(reducer_active_wave_index),
      .reducer_emitting(reducer_emitting),
      .reducer_active_head_base(reducer_active_head_base),
      .reducer_collect_beat_index(reducer_collect_beat_index),
      .reducer_emit_beat_index(reducer_emit_beat_index),
      .reducer_cycle_count(reducer_cycle_count),
      .reducer_local_root_completed_count(reducer_local_root_completed_count),
      .reducer_temporal_merge_completed_count(reducer_temporal_merge_completed_count),
      .reducer_emitted_beat_count(reducer_emitted_beat_count),
      .reducer_completed_command_count(reducer_completed_command_count),
      .reducer_local_stall_cycles(reducer_local_stall_cycles),
      .reducer_output_stall_cycles(reducer_output_stall_cycles),
      .producer_cycle_count(producer_cycle_count),
      .producer_command_accept_count(producer_command_accept_count),
      .producer_command_completed_count(producer_command_completed_count),
      .producer_stream_command_accept_count(producer_stream_command_accept_count),
      .producer_stream_completed_count(producer_stream_completed_count),
      .producer_merge_completed_count(producer_merge_completed_count),
      .producer_result_stall_cycles(producer_result_stall_cycles),
      .producer_stream_protocol_error(producer_stream_protocol_error),
      .producer_merge_protocol_error(producer_merge_protocol_error),
      .producer_protocol_error(producer_protocol_error),
      .group_contract_error(group_contract_error),
      .local_tree_protocol_error(local_tree_protocol_error),
      .temporal_merge_protocol_error(temporal_merge_protocol_error),
      .reducer_protocol_error(reducer_protocol_error),
      .atomic_command_protocol_error(atomic_command_protocol_error),
      .protocol_error()
  );

  {sram_top} u_sram_endpoint (
      .clk(clk),
      .rst_n(rst_n),
      .fill_target_valid(fill_target_valid && fill_target_buffer_map_w),
      .fill_target_ready(fill_target_ready_w),
      .fill_target_buffer_sel(fill_target_buffer_sel),
      .fill_target_command_id(fill_target_command_id),
      .fill_target_head_base(fill_target_head_base),
      .fill_target_wave_index(fill_target_wave_index),
      .fill_valid(fill_valid),
      .fill_ready(fill_ready),
      .fill_buffer_sel(fill_buffer_sel),
      .fill_stream(fill_stream),
      .fill_block_slot(fill_block_slot),
      .fill_slice(fill_slice),
      .fill_data(fill_data),
      .command_valid(command_fire_w),
      .command_ready(sram_command_ready_w),
      .command_buffer_sel(command_buffer_sel_w),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_wave_index(command_wave_index),
      .command_release_valid(command_release_valid_w),
      .command_release_buffer_sel(command_buffer_sel_q),
      .value_read_req_valid(value_read_req_valid_w),
      .value_read_req_ready(value_read_req_ready_w),
      .value_read_req_address(value_read_req_address_w),
      .value_read_req_slice(value_read_req_slice_w),
      .value_response_valid(value_response_valid_w),
      .value_response_ready(value_response_ready_w),
      .value_response_address(value_response_address_w),
      .value_response_slice(value_response_slice_w),
      .value_response_matrix(value_response_matrix_w),
      .value_response_tag(),
      .cycle_count(sram_cycle_count),
      .fill_target_accept_count(sram_fill_target_accept_count),
      .fill_row_accept_count(sram_fill_row_accept_count),
      .fill_stall_cycles(sram_fill_stall_cycles),
      .request_accept_count(sram_request_accept_count),
      .request_stall_cycles(sram_request_stall_cycles),
      .response_accept_count(sram_response_accept_count),
      .response_stall_cycles(sram_response_stall_cycles),
      .bank_conflict_count(sram_bank_conflict_count),
      .command_accept_count(sram_command_accept_count),
      .command_release_count(sram_command_release_count),
      .buffer0_occupancy_rows(sram_buffer0_occupancy_rows),
      .buffer1_occupancy_rows(sram_buffer1_occupancy_rows),
      .outstanding_response_occupancy(sram_outstanding_response_occupancy),
      .protocol_error_invalid_metadata(sram_invalid_metadata_error),
      .protocol_error_invalid_address(sram_invalid_address_error),
      .protocol_error_residency(sram_residency_error),
      .protocol_error_overwrite(sram_overwrite_error),
      .protocol_error_command(sram_command_error),
      .protocol_error()
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      command_buffer_sel_q <= 1'b0;
      released_count_q <= 32'd0;
      sram_buffer_map_error_q <= 1'b0;
      sram_release_guard_error_q <= 1'b0;
    end else begin
      if (fill_target_valid && !fill_target_buffer_map_w)
        sram_buffer_map_error_q <= 1'b1;
      if (command_fire_w) begin
        if (wave_command_accept_count != released_count_q)
          sram_release_guard_error_q <= 1'b1;
        command_buffer_sel_q <= command_buffer_sel_w;
      end
      if (command_release_valid_w) begin
        if (!release_count_pending_w || !all_producers_completed_w || !endpoint_responses_drained_w)
          sram_release_guard_error_q <= 1'b1;
        released_count_q <= released_count_q + 1'b1;
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    cluster_top = f"{top_name}__compute_cluster"
    sram_top = f"{top_name}__sram_endpoint"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="score32_exact_cluster_sram_composed_") as temp_name:
        temp_dir = Path(temp_name)
        cluster_dir = temp_dir / "cluster"
        sram_dir = temp_dir / "sram"
        generate_cluster(
            {
                "top_name": cluster_top,
                "attention_score32_exact_local_cluster_gqa8": {
                    "producers": int(params["producers"]),
                    "max_blocks": 8,
                    "value_slices": 16,
                    "head_id_bits": int(params["head_id_bits"]),
                    "persistent_waves": int(params["persistent_waves"]),
                },
            },
            cluster_dir,
        )
        generate_sram_service(
            {
                "top_name": sram_top,
                "attention_score32_exact_cluster_sram_service_gqa8": {
                    "producers": int(params["producers"]),
                },
            },
            sram_dir,
        )
        cluster_rtl = [
            (cluster_dir / "producer.v").read_text(encoding="utf-8").rstrip(),
            (cluster_dir / "reducer.v").read_text(encoding="utf-8").rstrip(),
            (cluster_dir / "top.v").read_text(encoding="utf-8").rstrip(),
        ]
        sram_rtl = (sram_dir / "top.v").read_text(encoding="utf-8").rstrip()
        cluster_manifest = json.loads((cluster_dir / _CLUSTER_MANIFEST).read_text(encoding="utf-8"))
        sram_manifest = json.loads((sram_dir / _SRAM_MANIFEST).read_text(encoding="utf-8"))

    rtl = "\n\n".join(cluster_rtl + [sram_rtl, _top(
        top_name=top_name,
        cluster_top=cluster_top,
        sram_top=sram_top,
        producers=int(params["producers"]),
        head_id_bits=int(params["head_id_bits"]),
    ).rstrip()]) + "\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    compute_manifest = exact_local_cluster_gqa8_service_manifest(
        producers=int(params["producers"]),
        waves=int(params["persistent_waves"]),
    )
    sram_service = cluster_sram_service_manifest(producers=int(params["producers"]))
    manifest: JsonDict = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_cluster_sram_composed_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_cluster_sram_composed_gqa8_v1",
        "producers": int(params["producers"]),
        "producer_input_lanes": int(params["producers"]),
        "internal_value_memory_lanes": int(params["producers"]) * 2,
        "external_fill_interfaces": 1,
        "persistent_waves": int(params["persistent_waves"]),
        "value_slices": 16,
        "head_id_bits": int(params["head_id_bits"]),
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "result_interface": "full_width_exact_gqa8_cluster_with_one_local_sram_endpoint_and_128beat_aggregate_output",
        "command_schedule_contract": compute_manifest["top_command_contract"],
        "buffer_mapping_contract": "fill_target_and_command_buffer_sel_are_deterministic_and_equal_to_wave_index_lsb",
        "release_invariant_contract": (
            "release_pulses_once_after_every_real_producer_command_completed_count_equals_wave_command_accept_count_"
            "and_wave_command_accept_count_exceeds_released_count_with_zero_sram_outstanding_response_occupancy"
        ),
        "comparison_baseline_contract": compute_manifest["comparison_baseline_contract"],
        "comparison_cycle_origin": compute_manifest["comparison_cycle_origin"],
        "diagnostic_only_baseline": "none",
        "remaining_abstractions": [
            "external_hbm_return_fill_plane_open",
            "external_mesh_noc_fill_transport_open",
            "global_c16_exact_reduction_open",
        ],
        "equivalence_hash": False,
        "top_pin_bits": _top_pin_bits(
            producers=int(params["producers"]),
            head_id_bits=int(params["head_id_bits"]),
        ),
        "service_model": {
            "compute_cluster": compute_manifest,
            "sram_endpoint": sram_service,
        },
        "submodule_manifests": {
            "compute_cluster": cluster_manifest,
            "sram_endpoint": sram_manifest,
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
