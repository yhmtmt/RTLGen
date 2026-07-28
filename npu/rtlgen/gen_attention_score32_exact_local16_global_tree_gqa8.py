#!/usr/bin/env python3
"""Generate the full structural GQA8 exact local16-to-global finalized tree wrapper."""

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
from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_gqa8 import (
    generate as generate_local_temporal_reducer,
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


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, int(value)))))


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")

    clusters = int(body.get("clusters", 16))
    cluster_producers = tuple(int(value) for value in body.get("cluster_producers", []))
    radix = int(body.get("radix", 2))
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    persistent_waves = int(body.get("persistent_waves", LOCAL_TEMPORAL_WAVES))
    divider_lanes = int(body.get("divider_lanes", 8))
    finalizer_banks = int(body.get("finalizer_banks", 59))

    if clusters != 16:
        raise SystemExit("clusters must remain fixed at 16")
    if len(cluster_producers) != clusters:
        raise SystemExit("cluster_producers must contain exactly 16 entries")
    if cluster_producers.count(54) != 8 or cluster_producers.count(53) != 8:
        raise SystemExit("cluster_producers must contain exactly eight 54s and eight 53s")
    if radix != 2:
        raise SystemExit("radix must remain fixed at 2")
    if value_slices != 16:
        raise SystemExit("value_slices must remain fixed at 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain fixed at 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    if divider_lanes != 8:
        raise SystemExit("divider_lanes must remain fixed at 8")
    if finalizer_banks != 59:
        raise SystemExit("finalizer_banks must remain fixed at 59")

    return {
        "top_name": top_name,
        "clusters": clusters,
        "cluster_producers": cluster_producers,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "persistent_waves": persistent_waves,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
    }


def _cluster_leaf_base_indices(cluster_producers: tuple[int, ...]) -> tuple[int, ...]:
    bases: list[int] = []
    next_base = 0
    for producers in cluster_producers:
        bases.append(next_base)
        next_base += int(producers)
    return tuple(bases)


def _top_pin_bits(*, total_leaves: int, clusters: int, head_id_bits: int, slice_bits: int, banks: int) -> int:
    node_count = clusters - 1
    stage_count = int(math.log2(clusters))
    leaf_bits = total_leaves * (1 + 1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS)
    root_bits = 1 + 1 + 16 + head_id_bits + slice_bits + 1 + FINAL_PAYLOAD_BITS
    cluster_monitor_bits = clusters * ((7 * 32) + 4)
    global_monitor_bits = (11 * 32) + (node_count * 32) + (stage_count * 32) + node_count + stage_count + banks + banks + 4
    return leaf_bits + root_bits + cluster_monitor_bits + global_monitor_bits + 1


def _cluster_instance(
    *,
    cluster: int,
    producer_count: int,
    leaf_base: int,
    head_id_bits: int,
    slice_bits: int,
    reducer54_top_name: str,
    reducer53_top_name: str,
) -> str:
    reducer_top_name = reducer54_top_name if producer_count == 54 else reducer53_top_name
    return f"""  {reducer_top_name} u_cluster_{cluster} (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid[{leaf_base} +: {producer_count}]),
      .leaf_ready(leaf_ready[{leaf_base} +: {producer_count}]),
      .leaf_command_id(leaf_command_id[{leaf_base * 16} +: {producer_count * 16}]),
      .leaf_head_id(leaf_head_id[{leaf_base * head_id_bits} +: {producer_count * head_id_bits}]),
      .leaf_global_max(leaf_global_max[{leaf_base * 32} +: {producer_count * 32}]),
      .leaf_exp_sum(leaf_exp_sum[{leaf_base * 33} +: {producer_count * 33}]),
      .leaf_slice(leaf_slice[{leaf_base * slice_bits} +: {producer_count * slice_bits}]),
      .leaf_last(leaf_last[{leaf_base} +: {producer_count}]),
      .leaf_value(leaf_value[{leaf_base * PARTIAL_PAYLOAD_BITS} +: {producer_count * PARTIAL_PAYLOAD_BITS}]),
      .out_valid(cluster_out_valid_w[{cluster}]),
      .out_ready(cluster_out_ready_w[{cluster}]),
      .out_command_id(cluster_out_command_id_w[{cluster * 16} +: 16]),
      .out_head_id(cluster_out_head_id_w[{cluster * head_id_bits} +: {head_id_bits}]),
      .out_global_max(cluster_out_global_max_w[{cluster * 32} +: 32]),
      .out_exp_sum(cluster_out_exp_sum_w[{cluster * 33} +: 33]),
      .out_slice(cluster_out_slice_w[{cluster * slice_bits} +: {slice_bits}]),
      .out_last(cluster_out_last_w[{cluster}]),
      .out_value(cluster_out_value_w[{cluster * PARTIAL_PAYLOAD_BITS} +: PARTIAL_PAYLOAD_BITS]),
      .active_wave_index(),
      .emitting(),
      .active_head_base(),
      .collect_beat_index(),
      .emit_beat_index(),
      .cycle_count(cluster_cycle_count[{cluster * 32} +: 32]),
      .local_root_completed_count(cluster_local_root_completed_count[{cluster * 32} +: 32]),
      .temporal_merge_completed_count(cluster_temporal_merge_completed_count[{cluster * 32} +: 32]),
      .emitted_beat_count(cluster_emitted_beat_count[{cluster * 32} +: 32]),
      .completed_command_count(cluster_completed_command_count[{cluster * 32} +: 32]),
      .local_stall_cycles(cluster_local_stall_cycles[{cluster * 32} +: 32]),
      .output_stall_cycles(cluster_output_stall_cycles[{cluster * 32} +: 32]),
      .group_contract_error(cluster_group_contract_error[{cluster}]),
      .local_tree_protocol_error(cluster_local_tree_protocol_error[{cluster}]),
      .temporal_merge_protocol_error(cluster_temporal_merge_protocol_error[{cluster}]),
      .protocol_error(cluster_protocol_error[{cluster}])
  );"""


def _top(
    *,
    top_name: str,
    reducer54_top_name: str,
    reducer53_top_name: str,
    global_tree_top_name: str,
    cluster_producers: tuple[int, ...],
    head_id_bits: int,
    value_slices: int,
    finalizer_banks: int,
) -> str:
    clusters = len(cluster_producers)
    total_leaves = sum(cluster_producers)
    slice_bits = _clog2(value_slices)
    node_count = clusters - 1
    stage_count = int(math.log2(clusters))
    cluster_bases = _cluster_leaf_base_indices(cluster_producers)
    cluster_instances = "\n\n".join(
        _cluster_instance(
            cluster=cluster,
            producer_count=int(cluster_producers[cluster]),
            leaf_base=int(cluster_bases[cluster]),
            head_id_bits=head_id_bits,
            slice_bits=slice_bits,
            reducer54_top_name=reducer54_top_name,
            reducer53_top_name=reducer53_top_name,
        )
        for cluster in range(clusters)
    )
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_local16_global_tree_gqa8.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{total_leaves - 1}:0] leaf_valid,
    output wire [{total_leaves - 1}:0] leaf_ready,
    input  wire [{(total_leaves * 16) - 1}:0] leaf_command_id,
    input  wire [{(total_leaves * head_id_bits) - 1}:0] leaf_head_id,
    input  wire [{(total_leaves * 32) - 1}:0] leaf_global_max,
    input  wire [{(total_leaves * 33) - 1}:0] leaf_exp_sum,
    input  wire [{(total_leaves * slice_bits) - 1}:0] leaf_slice,
    input  wire [{total_leaves - 1}:0] leaf_last,
    input  wire [{(total_leaves * PARTIAL_PAYLOAD_BITS) - 1}:0] leaf_value,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [15:0]  root_command_id,
    output wire [{head_id_bits - 1}:0] root_head_id,
    output wire [{slice_bits - 1}:0] root_slice,
    output wire         root_last,
    output wire [319:0] root_value,
    output wire [{(clusters * 32) - 1}:0] cluster_cycle_count,
    output wire [{(clusters * 32) - 1}:0] cluster_local_root_completed_count,
    output wire [{(clusters * 32) - 1}:0] cluster_temporal_merge_completed_count,
    output wire [{(clusters * 32) - 1}:0] cluster_emitted_beat_count,
    output wire [{(clusters * 32) - 1}:0] cluster_completed_command_count,
    output wire [{(clusters * 32) - 1}:0] cluster_local_stall_cycles,
    output wire [{(clusters * 32) - 1}:0] cluster_output_stall_cycles,
    output wire [{clusters - 1}:0] cluster_group_contract_error,
    output wire [{clusters - 1}:0] cluster_local_tree_protocol_error,
    output wire [{clusters - 1}:0] cluster_temporal_merge_protocol_error,
    output wire [{clusters - 1}:0] cluster_protocol_error,
    output wire [31:0]  global_cycle_count,
    output wire [31:0]  global_root_completed_count,
    output wire [31:0]  global_finalizer_accepted_count,
    output wire [31:0]  global_tree_root_completed_count,
    output wire [31:0]  global_order_fifo_occupancy,
    output wire [31:0]  global_order_fifo_high_watermark,
    output wire [31:0]  global_order_enqueued_count,
    output wire [31:0]  global_order_dequeued_count,
    output wire [31:0]  global_dispatch_stall_cycles,
    output wire [31:0]  global_dispatch_bank_id,
    output wire [31:0]  global_head_bank_id,
    output wire [{(node_count * 32) - 1}:0] global_node_completed_count,
    output wire [{(stage_count * 32) - 1}:0] global_stage_completed_count,
    output wire [{node_count - 1}:0] global_node_protocol_error,
    output wire [{stage_count - 1}:0] global_stage_protocol_error,
    output wire [{finalizer_banks - 1}:0] global_bank_protocol_error,
    output wire [{finalizer_banks - 1}:0] global_bank_outstanding,
    output wire         global_tree_protocol_error,
    output wire         global_order_protocol_error,
    output wire         global_finalizer_protocol_error,
    output wire         global_protocol_error,
    output wire         protocol_error
);
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};

  wire [{clusters - 1}:0] cluster_out_valid_w;
  wire [{clusters - 1}:0] cluster_out_ready_w;
  wire [{(clusters * 16) - 1}:0] cluster_out_command_id_w;
  wire [{(clusters * head_id_bits) - 1}:0] cluster_out_head_id_w;
  wire [{(clusters * 32) - 1}:0] cluster_out_global_max_w;
  wire [{(clusters * 33) - 1}:0] cluster_out_exp_sum_w;
  wire [{(clusters * slice_bits) - 1}:0] cluster_out_slice_w;
  wire [{clusters - 1}:0] cluster_out_last_w;
  wire [{(clusters * PARTIAL_PAYLOAD_BITS) - 1}:0] cluster_out_value_w;

{cluster_instances}

  {global_tree_top_name} u_global_tree (
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


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    reducer54_top_name = f"{top_name}__local_temporal_p54"
    reducer53_top_name = f"{top_name}__local_temporal_p53"
    global_tree_top_name = f"{top_name}__global_tree"

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="score32_exact_local16_global_tree_gqa8_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        reducer54_dir = temp_dir / "local54"
        reducer53_dir = temp_dir / "local53"
        global_tree_dir = temp_dir / "global_tree"
        generate_local_temporal_reducer(
            {
                "top_name": reducer54_top_name,
                "attention_score32_exact_local_temporal_reducer_gqa8": {
                    "producers": 54,
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "persistent_waves": int(params["persistent_waves"]),
                },
            },
            reducer54_dir,
        )
        generate_local_temporal_reducer(
            {
                "top_name": reducer53_top_name,
                "attention_score32_exact_local_temporal_reducer_gqa8": {
                    "producers": 53,
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "persistent_waves": int(params["persistent_waves"]),
                },
            },
            reducer53_dir,
        )
        generate_banked_tree(
            {
                "top_name": global_tree_top_name,
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": int(params["clusters"]),
                    "radix": int(params["radix"]),
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "divider_lanes": int(params["divider_lanes"]),
                    "finalizer_banks": int(params["finalizer_banks"]),
                },
            },
            global_tree_dir,
        )
        reducer54_rtl = (reducer54_dir / "top.v").read_text(encoding="utf-8")
        reducer53_rtl = (reducer53_dir / "top.v").read_text(encoding="utf-8")
        global_tree_rtl = (global_tree_dir / "top.v").read_text(encoding="utf-8")
        reducer54_manifest = json.loads(
            (reducer54_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        reducer53_manifest = json.loads(
            (reducer53_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        global_tree_manifest = json.loads(
            (global_tree_dir / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    top_text = _top(
        top_name=top_name,
        reducer54_top_name=reducer54_top_name,
        reducer53_top_name=reducer53_top_name,
        global_tree_top_name=global_tree_top_name,
        cluster_producers=tuple(int(value) for value in params["cluster_producers"]),
        head_id_bits=int(params["head_id_bits"]),
        value_slices=int(params["value_slices"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    rtl_text = reducer54_rtl + "\n\n" + reducer53_rtl + "\n\n" + global_tree_rtl + "\n\n" + top_text
    (out_dir / "top.v").write_text(rtl_text.rstrip() + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    probe_defaults = config.get("probe_defaults", {})
    if not isinstance(probe_defaults, dict):
        probe_defaults = {}
    configured_head_bases = probe_defaults.get("head_bases")
    if isinstance(configured_head_bases, list) and configured_head_bases:
        resolved_group_count = len(tuple(int(value) for value in configured_head_bases))
    else:
        resolved_group_count = max(1, int(probe_defaults.get("heads", 8)) // 8)

    cluster_producers = tuple(int(value) for value in params["cluster_producers"])
    cluster_bases = _cluster_leaf_base_indices(cluster_producers)
    service_model = exact_local16_global_tree_gqa8_service_manifest(
        cluster_producers=cluster_producers,
        waves=int(params["persistent_waves"]),
        head_groups=resolved_group_count,
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    manifest: JsonDict = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local16_global_tree_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local16_global_tree_gqa8_v1",
        "clusters": int(params["clusters"]),
        "cluster_producers": list(cluster_producers),
        "cluster_leaf_base_indices": list(cluster_bases),
        "cluster_leaf_ranges": [
            {
                "cluster": index,
                "leaf_base": int(cluster_bases[index]),
                "leaf_limit": int(cluster_bases[index] + cluster_producers[index] - 1),
                "producers": int(cluster_producers[index]),
            }
            for index in range(int(params["clusters"]))
        ],
        "clusters_with_54_producers": cluster_producers.count(54),
        "clusters_with_53_producers": cluster_producers.count(53),
        "total_local_producers": sum(cluster_producers),
        "radix": int(params["radix"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "persistent_waves": int(params["persistent_waves"]),
        "divider_lanes": int(params["divider_lanes"]),
        "finalizer_banks": int(params["finalizer_banks"]),
        "result_interface": "packed_856_leaf_exact_partial_inputs_to_c16_ordered_banked_exact_finalized_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "top_pin_bits": _top_pin_bits(
            total_leaves=sum(cluster_producers),
            clusters=int(params["clusters"]),
            head_id_bits=int(params["head_id_bits"]),
            slice_bits=_clog2(int(params["value_slices"])),
            banks=int(params["finalizer_banks"]),
        ),
        "command_schedule_contract": "group_major_gqa8_exact_8_wave_local_aggregation_preserved_across_all_16_clusters",
        "head_mapping_contract": "flat_leaf_indices_partitioned_by_cluster_leaf_base_indices_without_head_metadata_remap",
        "interface_adaptation": {
            "top_leaf_partitioning": "direct_flat_packed_leaf_buses_partitioned_by_cluster_leaf_base_indices",
            "local_to_global_leaf_mapping": "direct_ready_valid_command_id_head_id_global_max_exp_sum_slice_last_value_mapping_without_field_remap",
            "finalized_output_semantics": "existing_c16_banked_tree_root_contract_consumes_global_max_and_exp_sum_and_emits_finalized_values_only",
        },
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "remaining_abstractions": service_model["remaining_abstractions"],
        "equivalence_hash": False,
        "service_model": service_model,
        "submodule_manifests": {
            "local_temporal_reducer_p54": reducer54_manifest,
            "local_temporal_reducer_p53": reducer53_manifest,
            "banked_tree": global_tree_manifest,
            "cluster_instance_counts": {
                "p54": cluster_producers.count(54),
                "p53": cluster_producers.count(53),
            },
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    if isinstance(config.get("report_links"), dict):
        proposal_id = str(config["report_links"].get("proposal_id") or "").strip()
        proposal_path = str(config["report_links"].get("proposal_path") or "").strip()
        if proposal_id:
            manifest["linked_proposal_id"] = proposal_id
        if proposal_path:
            manifest["linked_proposal_path"] = proposal_path

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
