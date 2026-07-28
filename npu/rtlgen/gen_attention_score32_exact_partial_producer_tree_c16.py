#!/usr/bin/env python3
"""Generate a c16 exact-partial producer-coupled finalized tree slice."""

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

from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate as generate_cluster
from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import (
    generate as generate_banked_tree,
)
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_partial_producer_tree_service_manifest,
)

JsonDict = dict[str, Any]

_PRODUCERS = 16
_CLUSTERS = 16
_RADIX = 2
_VALUE_SLICES = 16
_DIVIDER_LANES = 8
_FINALIZER_BANKS = 59


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_exact_partial_producer_tree_c16")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_exact_partial_producer_tree_c16")

    producers = int(body.get("producers", _PRODUCERS))
    clusters = int(body.get("clusters", _CLUSTERS))
    radix = int(body.get("radix", _RADIX))
    max_blocks = int(body.get("max_blocks", 16384))
    value_slices = int(body.get("value_slices", _VALUE_SLICES))
    head_id_bits = int(body.get("head_id_bits", 5))
    divider_lanes = int(body.get("divider_lanes", _DIVIDER_LANES))
    finalizer_banks = int(body.get("finalizer_banks", _FINALIZER_BANKS))

    if producers != _PRODUCERS:
        raise SystemExit("producer-coupled c16 slice currently requires producers=16")
    if clusters != _CLUSTERS:
        raise SystemExit("producer-coupled c16 slice currently requires clusters=16")
    if radix != _RADIX:
        raise SystemExit("producer-coupled c16 slice currently requires radix=2")
    if max_blocks < 8 or max_blocks > 16384 or (max_blocks & (max_blocks - 1)):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if value_slices != _VALUE_SLICES:
        raise SystemExit("producer-coupled c16 slice currently requires value_slices=16")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes != _DIVIDER_LANES:
        raise SystemExit("producer-coupled c16 slice currently requires divider_lanes=8")
    if finalizer_banks != _FINALIZER_BANKS:
        raise SystemExit("producer-coupled c16 slice currently requires finalizer_banks=59")

    return {
        "top_name": top_name,
        "producers": producers,
        "clusters": clusters,
        "radix": radix,
        "max_blocks": max_blocks,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
    }


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _producer_instances(*, producer_top_name: str, head_id_bits: int) -> str:
    blocks: list[str] = []
    for producer in range(_PRODUCERS):
        a_lo = producer * 8
        b_lo = producer * 64
        addr_lo = producer * 14
        slice_lo = producer * 4
        matrix_lo = producer * 512
        cmd_lo = producer * 16
        head_lo = producer * head_id_bits
        max_lo = producer * 32
        sum_lo = producer * 33
        count_lo = producer * 32
        value_lo = producer * PARTIAL_PAYLOAD_BITS
        blocks.append(
            f"""  {producer_top_name} u_producer_{producer} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(producer_command_valid_w),
      .command_ready(producer_command_ready_w[{producer}]),
      .command_id(command_id),
      .command_head_id(command_head_id),
      .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(producer_input_valid[{producer}]),
      .input_ready(producer_input_ready[{producer}]),
      .input_last(producer_input_last[{producer}]),
      .input_a(producer_input_a[{a_lo} +: 8]),
      .input_b(producer_input_b[{b_lo} +: 64]),
      .value_read_req_valid(producer_value_read_req_valid[{producer}]),
      .value_read_req_ready(producer_value_read_req_ready[{producer}]),
      .value_read_req_address(producer_value_read_req_address[{addr_lo} +: 14]),
      .value_read_req_slice(producer_value_read_req_slice[{slice_lo} +: 4]),
      .value_response_valid(producer_value_response_valid[{producer}]),
      .value_response_ready(producer_value_response_ready[{producer}]),
      .value_response_address(producer_value_response_address[{addr_lo} +: 14]),
      .value_response_slice(producer_value_response_slice[{slice_lo} +: 4]),
      .value_response_matrix(producer_value_response_matrix[{matrix_lo} +: 512]),
      .result_valid(producer_result_valid_w[{producer}]),
      .result_ready(producer_result_ready_w[{producer}]),
      .result_command_id(producer_result_command_id_w[{cmd_lo} +: 16]),
      .result_head_id(producer_result_head_id_w[{head_lo} +: {head_id_bits}]),
      .result_global_max(producer_result_global_max_w[{max_lo} +: 32]),
      .result_exp_sum(producer_result_exp_sum_w[{sum_lo} +: 33]),
      .result_slice(producer_result_slice_w[{slice_lo} +: 4]),
      .result_last(producer_result_last_w[{producer}]),
      .result_value(producer_result_value_w[{value_lo} +: PARTIAL_PAYLOAD_BITS]),
      .accepted_count(producer_command_accept_count_w[{count_lo} +: 32]),
      .completed_count(producer_partial_completed_count_w[{count_lo} +: 32]),
      .cycle_count(producer_cycle_count_w[{count_lo} +: 32]),
      .protocol_error(producer_protocol_error_w[{producer}])
  );"""
        )
    return "\n\n".join(blocks)


def _leaf_assigns(*, head_id_bits: int) -> str:
    lines: list[str] = []
    for producer in range(_PRODUCERS):
        cmd_lo = producer * 16
        head_lo = producer * head_id_bits
        max_lo = producer * 32
        sum_lo = producer * 33
        slice_lo = producer * 4
        value_lo = producer * PARTIAL_PAYLOAD_BITS
        lines.extend(
            [
                f"  assign tree_leaf_valid_w[{producer}] = producer_result_valid_w[{producer}];",
                f"  assign producer_result_ready_w[{producer}] = tree_leaf_ready_w[{producer}];",
                f"  assign tree_leaf_command_id_w[{cmd_lo} +: 16] = producer_result_command_id_w[{cmd_lo} +: 16];",
                f"  assign tree_leaf_head_id_w[{head_lo} +: {head_id_bits}] = producer_result_head_id_w[{head_lo} +: {head_id_bits}];",
                f"  assign tree_leaf_global_max_w[{max_lo} +: 32] = producer_result_global_max_w[{max_lo} +: 32];",
                f"  assign tree_leaf_exp_sum_w[{sum_lo} +: 33] = producer_result_exp_sum_w[{sum_lo} +: 33];",
                f"  assign tree_leaf_slice_w[{slice_lo} +: 4] = producer_result_slice_w[{slice_lo} +: 4];",
                f"  assign tree_leaf_last_w[{producer}] = producer_result_last_w[{producer}];",
                f"  assign tree_leaf_value_w[{value_lo} +: PARTIAL_PAYLOAD_BITS] = producer_result_value_w[{value_lo} +: PARTIAL_PAYLOAD_BITS];",
            ]
        )
    return "\n".join(lines)


def _stall_counters() -> str:
    lines: list[str] = []
    for producer in range(_PRODUCERS):
        count_lo = producer * 32
        lines.append(
            f"      if (producer_result_valid_w[{producer}] && !producer_result_ready_w[{producer}]) begin\n"
            f"        producer_leaf_stall_cycles_q[{count_lo} +: 32] <= producer_leaf_stall_cycles_q[{count_lo} +: 32] + 1'b1;\n"
            f"      end"
        )
    return "\n".join(lines)


def _top(*, top_name: str, producer_top_name: str, tree_top_name: str, head_id_bits: int) -> str:
    node_count = _CLUSTERS - 1
    stage_count = _clog2(_CLUSTERS)
    leaf_assigns = _leaf_assigns(head_id_bits=head_id_bits)
    producer_instances = _producer_instances(producer_top_name=producer_top_name, head_id_bits=head_id_bits)
    stall_counters = _stall_counters()
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [{head_id_bits - 1}:0] command_head_id,
    input  wire [14:0]  command_block_count,
    input  wire [31:0]  command_score_multiplier,
    input  wire [5:0]   command_score_shift,
    input  wire [{_PRODUCERS - 1}:0] producer_input_valid,
    output wire [{_PRODUCERS - 1}:0] producer_input_ready,
    input  wire [{_PRODUCERS - 1}:0] producer_input_last,
    input  wire signed [{(_PRODUCERS * 8) - 1}:0] producer_input_a,
    input  wire signed [{(_PRODUCERS * 64) - 1}:0] producer_input_b,
    output wire [{_PRODUCERS - 1}:0] producer_value_read_req_valid,
    input  wire [{_PRODUCERS - 1}:0] producer_value_read_req_ready,
    output wire [{(_PRODUCERS * 14) - 1}:0] producer_value_read_req_address,
    output wire [{(_PRODUCERS * 4) - 1}:0] producer_value_read_req_slice,
    input  wire [{_PRODUCERS - 1}:0] producer_value_response_valid,
    output wire [{_PRODUCERS - 1}:0] producer_value_response_ready,
    input  wire [{(_PRODUCERS * 14) - 1}:0] producer_value_response_address,
    input  wire [{(_PRODUCERS * 4) - 1}:0] producer_value_response_slice,
    input  wire [{(_PRODUCERS * 512) - 1}:0] producer_value_response_matrix,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [15:0]  root_command_id,
    output wire [{head_id_bits - 1}:0] root_head_id,
    output wire [3:0]   root_slice,
    output wire         root_last,
    output wire [319:0] root_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  command_accept_count,
    output wire [31:0]  command_completed_count,
    output wire [{(_PRODUCERS * 32) - 1}:0] producer_command_accept_count,
    output wire [{(_PRODUCERS * 32) - 1}:0] producer_partial_completed_count,
    output wire [{(_PRODUCERS * 32) - 1}:0] producer_leaf_stall_cycles,
    output wire [{_PRODUCERS - 1}:0] producer_partial_valid,
    output wire [{_PRODUCERS - 1}:0] producer_partial_ready,
    output wire [{_PRODUCERS - 1}:0] producer_partial_last,
    output wire [31:0]  tree_root_completed_count,
    output wire [31:0]  finalizer_accepted_count,
    output wire [31:0]  order_fifo_occupancy,
    output wire [31:0]  order_fifo_high_watermark,
    output wire [31:0]  order_enqueued_count,
    output wire [31:0]  order_dequeued_count,
    output wire [31:0]  tree_dispatch_stall_cycles,
    output wire [31:0]  dispatch_bank_id,
    output wire [31:0]  head_bank_id,
    output wire [{(node_count * 32) - 1}:0] node_completed_count,
    output wire [{(stage_count * 32) - 1}:0] stage_completed_count,
    output wire [{node_count - 1}:0] node_protocol_error,
    output wire [{stage_count - 1}:0] stage_protocol_error,
    output wire [58:0]  bank_protocol_error,
    output wire [58:0]  bank_outstanding,
    output wire [{_PRODUCERS - 1}:0] producer_protocol_error,
    output wire         tree_protocol_error,
    output wire         order_protocol_error,
    output wire         finalizer_protocol_error,
    output wire         protocol_error
);
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};

  wire [{_PRODUCERS - 1}:0] producer_command_ready_w;
  wire [{_PRODUCERS - 1}:0] producer_result_valid_w;
  wire [{_PRODUCERS - 1}:0] producer_result_ready_w;
  wire [{(_PRODUCERS * 16) - 1}:0] producer_result_command_id_w;
  wire [{(_PRODUCERS * head_id_bits) - 1}:0] producer_result_head_id_w;
  wire [{(_PRODUCERS * 32) - 1}:0] producer_result_global_max_w;
  wire [{(_PRODUCERS * 33) - 1}:0] producer_result_exp_sum_w;
  wire [{(_PRODUCERS * 4) - 1}:0] producer_result_slice_w;
  wire [{_PRODUCERS - 1}:0] producer_result_last_w;
  wire [{(_PRODUCERS * PARTIAL_PAYLOAD_BITS) - 1}:0] producer_result_value_w;
  wire [{(_PRODUCERS * 32) - 1}:0] producer_command_accept_count_w;
  wire [{(_PRODUCERS * 32) - 1}:0] producer_partial_completed_count_w;
  wire [{(_PRODUCERS * 32) - 1}:0] producer_cycle_count_w;
  wire [{_PRODUCERS - 1}:0] producer_protocol_error_w;
  wire [31:0] tree_cycle_count_w;
  wire [31:0] root_completed_count_w;
  reg [31:0] cycle_count_q;
  reg [31:0] command_accept_count_q;
  reg [31:0] command_completed_count_q;
  reg [{(_PRODUCERS * 32) - 1}:0] producer_leaf_stall_cycles_q;

  wire command_fire_w = command_valid && command_ready;
  wire producer_command_valid_w = command_valid && command_ready;
  wire root_fire_w = root_valid && root_ready;

  wire [{_CLUSTERS - 1}:0] tree_leaf_valid_w;
  wire [{_CLUSTERS - 1}:0] tree_leaf_ready_w;
  wire [{(_CLUSTERS * 16) - 1}:0] tree_leaf_command_id_w;
  wire [{(_CLUSTERS * head_id_bits) - 1}:0] tree_leaf_head_id_w;
  wire [{(_CLUSTERS * 32) - 1}:0] tree_leaf_global_max_w;
  wire [{(_CLUSTERS * 33) - 1}:0] tree_leaf_exp_sum_w;
  wire [{(_CLUSTERS * 4) - 1}:0] tree_leaf_slice_w;
  wire [{_CLUSTERS - 1}:0] tree_leaf_last_w;
  wire [{(_CLUSTERS * PARTIAL_PAYLOAD_BITS) - 1}:0] tree_leaf_value_w;

  assign command_ready = &producer_command_ready_w;
  assign cycle_count = cycle_count_q;
  assign command_accept_count = command_accept_count_q;
  assign command_completed_count = command_completed_count_q;
  assign producer_command_accept_count = producer_command_accept_count_w;
  assign producer_partial_completed_count = producer_partial_completed_count_w;
  assign producer_leaf_stall_cycles = producer_leaf_stall_cycles_q;
  assign producer_partial_valid = producer_result_valid_w;
  assign producer_partial_ready = producer_result_ready_w;
  assign producer_partial_last = producer_result_last_w;
  assign producer_protocol_error = producer_protocol_error_w;
  assign protocol_error =
      (|producer_protocol_error_w) || tree_protocol_error || order_protocol_error || finalizer_protocol_error;

{leaf_assigns}

{producer_instances}

  {tree_top_name} u_banked_tree (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(tree_leaf_valid_w),
      .leaf_ready(tree_leaf_ready_w),
      .leaf_command_id(tree_leaf_command_id_w),
      .leaf_head_id(tree_leaf_head_id_w),
      .leaf_global_max(tree_leaf_global_max_w),
      .leaf_exp_sum(tree_leaf_exp_sum_w),
      .leaf_slice(tree_leaf_slice_w),
      .leaf_last(tree_leaf_last_w),
      .leaf_value(tree_leaf_value_w),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(tree_cycle_count_w),
      .root_completed_count(root_completed_count_w),
      .finalizer_accepted_count(finalizer_accepted_count),
      .tree_root_completed_count(tree_root_completed_count),
      .order_fifo_occupancy(order_fifo_occupancy),
      .order_fifo_high_watermark(order_fifo_high_watermark),
      .order_enqueued_count(order_enqueued_count),
      .order_dequeued_count(order_dequeued_count),
      .dispatch_stall_cycles(tree_dispatch_stall_cycles),
      .dispatch_bank_id(dispatch_bank_id),
      .head_bank_id(head_bank_id),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .bank_protocol_error(bank_protocol_error),
      .bank_outstanding(bank_outstanding),
      .tree_protocol_error(tree_protocol_error),
      .order_protocol_error(order_protocol_error),
      .finalizer_protocol_error(finalizer_protocol_error),
      .protocol_error()
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cycle_count_q <= 32'd0;
      command_accept_count_q <= 32'd0;
      command_completed_count_q <= 32'd0;
      producer_leaf_stall_cycles_q <= {(_PRODUCERS * 32)}'d0;
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
      if (command_fire_w) begin
        command_accept_count_q <= command_accept_count_q + 1'b1;
      end
      if (root_fire_w && root_last) begin
        command_completed_count_q <= command_completed_count_q + 1'b1;
      end
{stall_counters}
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    producer_top_name = f"{top_name}__producer"
    tree_top_name = f"{top_name}__banked_tree"
    head_id_bits = int(params["head_id_bits"])

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="score32_exact_partial_producer_tree_c16_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        producer_dir = temp_dir / "producer"
        tree_dir = temp_dir / "tree"
        generate_cluster(
            {
                "top_name": producer_top_name,
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": int(params["max_blocks"]),
                    "array_n": 8,
                    "value_slices": int(params["value_slices"]),
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "result_mode": "exact_partial",
                    "head_id_bits": head_id_bits,
                },
            },
            producer_dir,
        )
        generate_banked_tree(
            {
                "top_name": tree_top_name,
                "attention_score32_exact_banked_finalized_tree": {
                    "clusters": _CLUSTERS,
                    "radix": _RADIX,
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": head_id_bits,
                    "divider_lanes": int(params["divider_lanes"]),
                    "finalizer_banks": int(params["finalizer_banks"]),
                },
            },
            tree_dir,
        )
        producer_rtl = (producer_dir / "top.v").read_text(encoding="utf-8")
        tree_rtl = (tree_dir / "top.v").read_text(encoding="utf-8")
        producer_manifest = json.loads(
            (producer_dir / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
        )
        tree_manifest = json.loads(
            (tree_dir / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text(encoding="utf-8")
        )

    top_text = _top(
        top_name=top_name,
        producer_top_name=producer_top_name,
        tree_top_name=tree_top_name,
        head_id_bits=head_id_bits,
    )
    (out_dir / "top.v").write_text(producer_rtl + "\n\n" + tree_rtl + "\n\n" + top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    service_model = exact_partial_producer_tree_service_manifest(
        producers=_PRODUCERS,
        clusters=_CLUSTERS,
        heads=int(config.get("probe_defaults", {}).get("heads", 32)) if isinstance(config.get("probe_defaults"), dict) else 32,
        max_blocks=int(params["max_blocks"]),
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py",
        "top_name": top_name,
        "semantic_profile": "score32_online_exact_partial_sixteen_producer_coupled_banked_tree_v1",
        "producers": _PRODUCERS,
        "clusters": _CLUSTERS,
        "radix": _RADIX,
        "max_blocks": int(params["max_blocks"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": head_id_bits,
        "divider_lanes": int(params["divider_lanes"]),
        "finalizer_banks": int(params["finalizer_banks"]),
        "producer_result_mode": "exact_partial",
        "producer_interface": "packed_per_producer_ready_valid_score_blocks_and_value_blocks",
        "command_schedule_contract": "in_order_head_commands_broadcast_to_all_sixteen_producers",
        "head_mapping_contract": "explicit_head_id_no_tile_or_wave_inference",
        "result_interface": "sixteen_exact_partial_producers_to_c16_ordered_banked_exact_finalized_tree",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "llama_tile_cadence_unclosed": True,
        "producer_block_workload_assumptions": service_model["producer_block_workload_assumptions"],
        "exact_protocols": {
            "producer_partial_protocol": service_model["producer_partial_protocol"],
            "finalized_protocol": service_model["finalized_protocol"],
        },
        "remaining_abstractions": service_model["remaining_abstractions"],
        "equivalence_hash": False,
        "service_model": service_model,
        "submodule_manifests": {
            "producer": producer_manifest,
            "producer_instances": _PRODUCERS,
            "banked_tree": tree_manifest,
        },
    }
    if isinstance(config.get("probe_defaults"), dict):
        manifest["checked_in_probe_defaults"] = config["probe_defaults"]
    (out_dir / "attention_score32_exact_partial_producer_tree_c16_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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
