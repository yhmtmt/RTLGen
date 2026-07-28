#!/usr/bin/env python3
"""Generate the full functional GQA8 producer/local16/global score32 hierarchy."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate as generate_banked_tree
from npu.rtlgen.gen_attention_score32_exact_local_cluster_gqa8 import _top as generate_cluster_wrapper
from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8 import (
    generate as generate_local_temporal_reducer,
)
from npu.rtlgen.gen_attention_score32_exact_partial_gqa8_dual_stream_producer import (
    generate as generate_producer,
)
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local16_global_tree_gqa8_service_manifest,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_local16_global_tree_gqa8"
_MANIFEST_NAME = "attention_score32_exact_local16_global_tree_gqa8_manifest.json"


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
    # Keep the physical type ordering fixed: p54 clusters 0..7, p53 clusters 8..15.
    if cluster_producers != tuple([54] * 8 + [53] * 8):
        raise SystemExit("cluster_producers must be exactly eight 54s followed by eight 53s")
    if params["radix"] != 2 or params["value_slices"] != 16 or params["head_id_bits"] != 5:
        raise SystemExit("wrapper requires radix=2, value_slices=16, and head_id_bits=5")
    if params["persistent_waves"] != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    if params["divider_lanes"] != 8 or params["finalizer_banks"] != 59:
        raise SystemExit("wrapper must remain on the c16/r2/l8/b59 finalized tree")
    return params


def _slice(name: str, index: int, width: int) -> str:
    return f"{name}[{index * width} +: {width}]"


def _partition(name: str, producer_base: int, producers: int, width_per_producer: int) -> str:
    return f"{name}[{producer_base * width_per_producer} +: {producers * width_per_producer}]"


def _block_count_assignments(*, name: str, producers: int, windows: tuple[tuple[int, int], ...]) -> str:
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


def _cluster_instance(
    *,
    cluster: int,
    producers: int,
    producer_base: int,
    cluster_top: str,
) -> str:
    block_counts = "p54_command_block_count_w" if producers == 54 else "p53_command_block_count_w"
    return f"""  {cluster_top} u_cluster_{cluster} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_fire_w),
      .command_ready(cluster_command_ready_w[{cluster}]),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_block_count({block_counts}),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid({_partition("input_valid", producer_base, producers, 1)}),
      .input_ready({_partition("input_ready", producer_base, producers, 1)}),
      .input_last({_partition("input_last", producer_base, producers, 1)}),
      .input_query({_partition("input_query", producer_base, producers, 128)}),
      .input_key({_partition("input_key", producer_base, producers, 128)}),
      .value_read_req_valid({_partition("value_read_req_valid", producer_base, producers, 2)}),
      .value_read_req_ready({_partition("value_read_req_ready", producer_base, producers, 2)}),
      .value_read_req_address({_partition("value_read_req_address", producer_base, producers, 28)}),
      .value_read_req_slice({_partition("value_read_req_slice", producer_base, producers, 8)}),
      .value_response_valid({_partition("value_response_valid", producer_base, producers, 2)}),
      .value_response_ready({_partition("value_response_ready", producer_base, producers, 2)}),
      .value_response_address({_partition("value_response_address", producer_base, producers, 28)}),
      .value_response_slice({_partition("value_response_slice", producer_base, producers, 8)}),
      .value_response_matrix({_partition("value_response_matrix", producer_base, producers, 1024)}),
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
      .protocol_error(cluster_protocol_error[{cluster}])
  );"""


def _top(
    *,
    top_name: str,
    p54_cluster_top: str,
    p53_cluster_top: str,
    global_tree_top: str,
) -> str:
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
    p54_counts = _block_count_assignments(
        name="p54_command_block_count_w",
        producers=54,
        windows=((0, 10), (10, 20), (20, 30), (30, 40)),
    )
    p53_counts = _block_count_assignments(
        name="p53_command_block_count_w",
        producers=53,
        windows=((0, 11), (11, 22), (22, 33), (33, 44)),
    )
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_local16_global_tree_gqa8.py
module {top_name} (
    input  wire clk,
    input  wire rst_n,
    input  wire command_valid,
    output wire command_ready,
    input  wire [15:0] command_id,
    input  wire [4:0] command_head_base,
    input  wire [31:0] command_score_multiplier,
    input  wire [5:0] command_score_shift,
    input  wire [855:0] input_valid,
    output wire [855:0] input_ready,
    input  wire [855:0] input_last,
    input  wire signed [109567:0] input_query,
    input  wire signed [109567:0] input_key,
    output wire [1711:0] value_read_req_valid,
    input  wire [1711:0] value_read_req_ready,
    output wire [23967:0] value_read_req_address,
    output wire [6847:0] value_read_req_slice,
    input  wire [1711:0] value_response_valid,
    output wire [1711:0] value_response_ready,
    input  wire [23967:0] value_response_address,
    input  wire [6847:0] value_response_slice,
    input  wire [876543:0] value_response_matrix,
    output wire root_valid,
    input  wire root_ready,
    output wire [15:0] root_command_id,
    output wire [4:0] root_head_id,
    output wire [3:0] root_slice,
    output wire root_last,
    output wire [319:0] root_value,
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
    output wire [15:0] cluster_protocol_error,
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
    output wire protocol_error
);
  wire [15:0] cluster_command_ready_w;
  wire [15:0] cluster_out_valid_w;
  wire [15:0] cluster_out_ready_w;
  wire [255:0] cluster_out_command_id_w;
  wire [79:0] cluster_out_head_id_w;
  wire [511:0] cluster_out_global_max_w;
  wire [527:0] cluster_out_exp_sum_w;
  wire [63:0] cluster_out_slice_w;
  wire [15:0] cluster_out_last_w;
  wire [5247:0] cluster_out_value_w;
  wire command_head_base_valid_w = (command_head_base[2:0] == 3'd0);
  wire command_fire_w = command_valid && command_ready;

  assign command_ready = command_head_base_valid_w && (&cluster_command_ready_w);

{p54_counts}

{p53_counts}

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

  assign protocol_error = (|cluster_protocol_error) || global_protocol_error;
endmodule
"""


def _top_pin_bits() -> int:
    # Count every scalar bit in the concrete top interface, including monitoring.
    return 1_173_953


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    producer_top = f"{top_name}__producer"
    p54_reducer_top = f"{top_name}__local_temporal_p54"
    p53_reducer_top = f"{top_name}__local_temporal_p53"
    p54_cluster_top = f"{top_name}__cluster_p54"
    p53_cluster_top = f"{top_name}__cluster_p53"
    global_tree_top = f"{top_name}__global_tree"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="score32_exact_local16_global_full_") as temp_name:
        temp_dir = Path(temp_name)
        producer_dir = temp_dir / "producer"
        p54_dir = temp_dir / "p54"
        p53_dir = temp_dir / "p53"
        global_dir = temp_dir / "global"
        generate_producer(
            {
                "top_name": producer_top,
                "attention_score32_exact_partial_gqa8_dual_stream_producer": {
                    "streams": 2,
                    "query_heads_per_stream": 8,
                    "max_blocks": 8,
                    "value_slices": 16,
                    "head_id_bits": 5,
                },
            },
            producer_dir,
        )
        for producers, reducer_top, reducer_dir in (
            (54, p54_reducer_top, p54_dir),
            (53, p53_reducer_top, p53_dir),
        ):
            generate_local_temporal_reducer(
                {
                    "top_name": reducer_top,
                    "attention_score32_exact_local_temporal_reducer_gqa8": {
                        "producers": producers,
                        "value_slices": 16,
                        "head_id_bits": 5,
                        "persistent_waves": LOCAL_TEMPORAL_WAVES,
                    },
                },
                reducer_dir,
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
        producer_rtl = (producer_dir / "top.v").read_text(encoding="utf-8")
        p54_rtl = (p54_dir / "top.v").read_text(encoding="utf-8")
        p53_rtl = (p53_dir / "top.v").read_text(encoding="utf-8")
        global_rtl = (global_dir / "top.v").read_text(encoding="utf-8")
        producer_manifest = json.loads(
            (producer_dir / "attention_score32_exact_partial_gqa8_dual_stream_producer_manifest.json").read_text()
        )
        p54_manifest = json.loads(
            (p54_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text()
        )
        p53_manifest = json.loads(
            (p53_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text()
        )
        global_manifest = json.loads(
            (global_dir / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text()
        )

    cluster54_rtl = generate_cluster_wrapper(
        top_name=p54_cluster_top,
        producer_top=producer_top,
        reducer_top=p54_reducer_top,
        producers=54,
        head_id_bits=5,
    )
    cluster53_rtl = generate_cluster_wrapper(
        top_name=p53_cluster_top,
        producer_top=producer_top,
        reducer_top=p53_reducer_top,
        producers=53,
        head_id_bits=5,
    )
    top_rtl = _top(
        top_name=top_name,
        p54_cluster_top=p54_cluster_top,
        p53_cluster_top=p53_cluster_top,
        global_tree_top=global_tree_top,
    )
    rtl = "\n\n".join((producer_rtl.rstrip(), p54_rtl.rstrip(), p53_rtl.rstrip(), global_rtl.rstrip(), cluster54_rtl.rstrip(), cluster53_rtl.rstrip(), top_rtl.rstrip())) + "\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cluster_producers = tuple(int(value) for value in params["cluster_producers"])
    defaults = config.get("probe_defaults", {})
    group_count = len(defaults.get("head_bases", [0])) if isinstance(defaults, dict) else 1
    service_model = exact_local16_global_tree_gqa8_service_manifest(
        cluster_producers=cluster_producers,
        head_groups=group_count,
    )
    manifest: JsonDict = {
        "version": 2,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local16_global_tree_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local16_global_tree_gqa8_full_compute_v1",
        "clusters": 16,
        "cluster_producers": list(cluster_producers),
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": 856,
        "total_value_memory_lanes": 1712,
        "radix": 2,
        "value_slices": 16,
        "head_id_bits": 5,
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "divider_lanes": 8,
        "finalizer_banks": 59,
        "top_pin_bits": _top_pin_bits(),
        "result_interface": "856_real_dual_stream_producers_to_16_local_reducers_to_c16_ordered_banked_finalized_root",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "command_schedule_contract": "one_shared_atomic_wave_command_across_all_16_clusters",
        "head_mapping_contract": "head_base_selects_internal_p54_and_p53_two_block_producer_windows",
        "block_count_contract": {
            "top_level_pin": False,
            "default_blocks_per_stream": 1,
            "extra_blocks_per_stream": 1,
            "p54_group_ranges": [[0, 9], [10, 19], [20, 29], [30, 39]],
            "p53_group_ranges": [[0, 10], [11, 21], [22, 32], [33, 43]],
            "blocks_per_stream_per_cluster": 64,
        },
        "interface_adaptation": {
            "producer_inputs": "independent_flattened_ready_valid_query_key_lanes_for_all_856_producers",
            "value_memory": "independent_flattened_request_response_lanes_for_all_1712_streams",
            "local_to_global": "direct_16_reducer_output_mapping_without_field_remap",
        },
        "comparison_baseline_contract": "structured_full_row_producer_local_global_reference_comparison_hashes_summary_only",
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": "none",
        "remaining_abstractions": [
            "external_query_key_source_open",
            "external_value_memory_system_open",
            "physical_ppa_open",
        ],
        "equivalence_hash": False,
        "service_model": service_model,
        "submodule_manifests": {
            "shared_producer": producer_manifest,
            "local_temporal_reducer_p54": p54_manifest,
            "local_temporal_reducer_p53": p53_manifest,
            "banked_tree": global_manifest,
            "cluster_instance_counts": {"p54": 8, "p53": 8},
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    if isinstance(config.get("report_links"), dict):
        if config["report_links"].get("proposal_id"):
            manifest["linked_proposal_id"] = str(config["report_links"]["proposal_id"])
        if config["report_links"].get("proposal_path"):
            manifest["linked_proposal_path"] = str(config["report_links"]["proposal_path"])
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
