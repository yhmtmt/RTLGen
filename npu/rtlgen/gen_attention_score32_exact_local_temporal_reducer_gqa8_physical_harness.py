#!/usr/bin/env python3
"""Generate a narrow-IO structural harness for the GQA8 local temporal score32 reducer."""

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
from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    LEGACY_MONOLITHIC_LUT_EXACT,
    SEGMENTED_LUT_9X256_EXACT,
)
from npu.sim.perf.attention_exact_partial import LOCAL_TEMPORAL_WAVES, PARTIAL_PAYLOAD_BITS

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness"
_MANIFEST_NAME = "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1"
_PROPOSAL_PATH = "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1/proposal.json"
_SUPPORTED_EXP_SCALE_IMPLS = {
    LEGACY_MONOLITHIC_LUT_EXACT,
    SEGMENTED_LUT_9X256_EXACT,
    FACTORED_H33_L64_MUL_EXACT,
}


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
    mode = str(body.get("mode", "reducer")).strip()
    waves = int(body.get("waves", LOCAL_TEMPORAL_WAVES))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    if producers not in {53, 54}:
        raise SystemExit("producers must be exactly 53 or 54")
    if mode not in {"reducer", "source_only"}:
        raise SystemExit("mode must be reducer or source_only")
    if waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"waves must remain fixed at {LOCAL_TEMPORAL_WAVES}")
    if exp_scale_impl not in _SUPPORTED_EXP_SCALE_IMPLS:
        supported = ", ".join(sorted(_SUPPORTED_EXP_SCALE_IMPLS))
        raise SystemExit(f"exp_scale_impl must be one of: {supported}")
    return {
        "top_name": top_name,
        "producers": producers,
        "mode": mode,
        "waves": waves,
        "exp_scale_impl": exp_scale_impl,
    }


def _top_pin_bits() -> int:
    input_bits = 1 + 1 + 1 + 32
    result_bits = 1 + 16 + 5 + 32 + 33 + 4 + 1 + PARTIAL_PAYLOAD_BITS + 32
    counter_bits = (9 * 32) + 1
    return input_bits + result_bits + counter_bits


def _leaf_assigns(producers: int) -> str:
    lines: list[str] = []
    for index in range(producers):
        value_fields = ",\n          ".join(
            f"{{shared_lfsr_q[{field}], "
            f"(shared_lfsr_q ^ batch_signature_w ^ 32'h{(0x10203040 * (field + 1)) ^ (index * 0x01010011):08x}), "
            f"(shared_beat_count_q[7:0] ^ 8'h{((field + 1) * 0x11) ^ (index & 0xFF):02x})}}"
            for field in range(8)
        )
        lines.extend(
            [
                f"  assign leaf_valid_w[{index}] = atomic_batch_valid_w;",
                f"  assign leaf_command_id_w[{index * 16} +: 16] = 16'h7b00 + {{15'd0, batch_command_index_w}};",
                f"  assign leaf_head_id_w[{index * 5} +: 5] = batch_head_id_w;",
                f"  assign leaf_global_max_w[{index * 32} +: 32] = "
                f"$signed(shared_lfsr_q ^ batch_signature_w ^ 32'h{0x13579BDF ^ (index * 0x00210021):08x});",
                f"  assign leaf_exp_sum_w[{index * 33} +: 33] = "
                f"{{1'b0, shared_lfsr_q}} + {{22'd0, shared_beat_count_q}} + 33'd{index + 1};",
                f"  assign leaf_slice_w[{index * 4} +: 4] = batch_slice_index_w;",
                f"  assign leaf_last_w[{index}] = batch_last_w;",
                f"""  assign leaf_value_w[{index * PARTIAL_PAYLOAD_BITS} +: PARTIAL_PAYLOAD_BITS] = {{
          {value_fields}
      }};""",
            ]
        )
    return "\n".join(lines)


def _batch_ready_assign(*, mode: str) -> str:
    if mode == "reducer":
        return "  assign batch_ready_w = &reducer_leaf_ready_w;"
    return "  assign batch_ready_w = 1'b1;"


def _source_fold_terms(producers: int) -> str:
    terms: list[str] = []
    for index in range(producers):
        terms.extend(
            [
                f"32'h{0xA5A50000 + index:08x}",
                f"{{16'd0, leaf_command_id_w[{index * 16} +: 16]}}",
                f"{{27'd0, leaf_head_id_w[{index * 5} +: 5]}}",
                f"leaf_global_max_w[{index * 32} +: 32]",
                f"leaf_exp_sum_w[{index * 33} +: 32]",
                f"{{28'd0, leaf_slice_w[{index * 4} +: 4]}}",
                f"{{31'd0, leaf_last_w[{index}]}}",
            ]
        )
        terms.extend(
            f"leaf_value_w[{index * PARTIAL_PAYLOAD_BITS + offset} +: 32]" for offset in range(0, 320, 32)
        )
        terms.append(f"{{24'd0, leaf_value_w[{index * PARTIAL_PAYLOAD_BITS + 320} +: 8]}}")
    return " ^\n      ".join(terms)


def _top(*, top_name: str, reducer_top: str, producers: int, mode: str, waves: int) -> str:
    reducer_block = ""
    if mode == "reducer":
        reducer_block = f"""
  {reducer_top} u_reducer (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid_w),
      .leaf_ready(reducer_leaf_ready_w),
      .leaf_command_id(leaf_command_id_w),
      .leaf_head_id(leaf_head_id_w),
      .leaf_global_max(leaf_global_max_w),
      .leaf_exp_sum(leaf_exp_sum_w),
      .leaf_slice(leaf_slice_w),
      .leaf_last(leaf_last_w),
      .leaf_value(leaf_value_w),
      .out_valid(reducer_out_valid_w),
      .out_ready(reducer_out_ready_w),
      .out_command_id(reducer_out_command_id_w),
      .out_head_id(reducer_out_head_id_w),
      .out_global_max(reducer_out_global_max_w),
      .out_exp_sum(reducer_out_exp_sum_w),
      .out_slice(reducer_out_slice_w),
      .out_last(reducer_out_last_w),
      .out_value(reducer_out_value_w),
      .active_wave_index(),
      .emitting(),
      .active_head_base(),
      .collect_beat_index(),
      .emit_beat_index(),
      .cycle_count(reducer_cycle_count_w),
      .local_root_completed_count(local_root_completed_count_w),
      .temporal_merge_completed_count(temporal_merge_completed_count_w),
      .emitted_beat_count(emitted_beat_count_w),
      .completed_command_count(completed_command_count_w),
      .local_stall_cycles(local_stall_cycles_w),
      .output_stall_cycles(output_stall_cycles_w),
      .group_contract_error(group_contract_error_w),
      .local_tree_protocol_error(local_tree_protocol_error_w),
      .temporal_merge_protocol_error(temporal_merge_protocol_error_w),
      .protocol_error(reducer_protocol_error_w)
  );"""
    return f"""// Generated by npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness.py
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [31:0]  seed,
    output wire         done,
    output wire [15:0]  final_command_id,
    output wire [4:0]   final_head_id,
    output wire signed [31:0] final_global_max,
    output wire [32:0]  final_exp_sum,
    output wire [3:0]   final_slice,
    output wire         final_last,
    output wire [327:0] final_value,
    output wire [31:0]  source_fold,
    output wire [31:0]  cycle_count,
    output wire [31:0]  leaf_fire_count,
    output wire [31:0]  observed_result_count,
    output wire [31:0]  completed_command_count,
    output wire [31:0]  local_root_completed_count,
    output wire [31:0]  temporal_merge_completed_count,
    output wire [31:0]  local_stall_cycles,
    output wire [31:0]  output_stall_cycles,
    output wire [31:0]  source_stall_cycles,
    output wire         protocol_error_seen
);
  localparam integer PRODUCERS = {producers};
  localparam integer HEAD_ID_BITS = 5;
  localparam integer GQA_HEADS = 8;
  localparam integer VALUE_SLICES = 16;
  localparam integer SLICE_BITS = 4;
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};
  localparam integer WAVES = {waves};
  localparam integer COMMANDS = 2;
  localparam integer TOTAL_LEAF_BEATS = COMMANDS * WAVES * GQA_HEADS * VALUE_SLICES;
  localparam SOURCE_ONLY_MODE = 1'b{1 if mode == "source_only" else 0};

  reg running_q;
  reg done_q;
  reg [31:0] cycle_count_q;
  reg [31:0] leaf_fire_count_q;
  reg [31:0] observed_result_count_q;
  reg [31:0] source_fold_q;
  reg [31:0] source_stall_cycles_q;
  reg [15:0] final_command_id_q;
  reg [4:0] final_head_id_q;
  reg signed [31:0] final_global_max_q;
  reg [32:0] final_exp_sum_q;
  reg [3:0] final_slice_q;
  reg final_last_q;
  reg [327:0] final_value_q;

  reg [31:0] shared_lfsr_q;
  reg [11:0] shared_beat_count_q;

  wire [PRODUCERS-1:0] leaf_valid_w;
  wire [PRODUCERS*16-1:0] leaf_command_id_w;
  wire [PRODUCERS*HEAD_ID_BITS-1:0] leaf_head_id_w;
  wire [PRODUCERS*32-1:0] leaf_global_max_w;
  wire [PRODUCERS*33-1:0] leaf_exp_sum_w;
  wire [PRODUCERS*SLICE_BITS-1:0] leaf_slice_w;
  wire [PRODUCERS-1:0] leaf_last_w;
  wire [PRODUCERS*PARTIAL_PAYLOAD_BITS-1:0] leaf_value_w;
  wire [PRODUCERS-1:0] reducer_leaf_ready_w;
  wire batch_pending_w = running_q && (shared_beat_count_q < 12'd2048);
  wire batch_ready_w;
  wire atomic_batch_valid_w = batch_pending_w && batch_ready_w;
  wire atomic_batch_fire_w = atomic_batch_valid_w;
  wire batch_command_index_w = shared_beat_count_q[10];
  wire [2:0] batch_wave_index_w = shared_beat_count_q[9:7];
  wire [2:0] batch_head_lane_w = shared_beat_count_q[6:4];
  wire [SLICE_BITS-1:0] batch_slice_index_w = shared_beat_count_q[3:0];
  wire [4:0] batch_head_base_w = {{1'b0, batch_command_index_w, 3'd0}};
  wire [4:0] batch_head_id_w = batch_head_base_w + {{2'd0, batch_head_lane_w}};
  wire batch_last_w = (batch_slice_index_w == 4'd15);
  wire [31:0] batch_signature_w = {{
      5'd0,
      batch_command_index_w,
      batch_wave_index_w,
      batch_head_lane_w,
      batch_slice_index_w,
      shared_beat_count_q[7:0],
      8'h96
  }};
  wire reducer_out_valid_w;
  wire reducer_out_ready_w;
  wire [15:0] reducer_out_command_id_w;
  wire [4:0] reducer_out_head_id_w;
  wire signed [31:0] reducer_out_global_max_w;
  wire [32:0] reducer_out_exp_sum_w;
  wire [3:0] reducer_out_slice_w;
  wire reducer_out_last_w;
  wire [327:0] reducer_out_value_w;
  wire [31:0] reducer_cycle_count_w;
  wire [31:0] local_root_completed_count_w;
  wire [31:0] temporal_merge_completed_count_w;
  wire [31:0] emitted_beat_count_w;
  wire [31:0] completed_command_count_w;
  wire [31:0] local_stall_cycles_w;
  wire [31:0] output_stall_cycles_w;
  wire group_contract_error_w;
  wire local_tree_protocol_error_w;
  wire temporal_merge_protocol_error_w;
  wire reducer_protocol_error_w;
  wire reducer_result_fire_w = reducer_out_valid_w && reducer_out_ready_w;
  wire reducer_final_result_w =
      reducer_result_fire_w
      && reducer_out_last_w
      && (reducer_out_command_id_w == 16'h7b01)
      && (reducer_out_head_id_w == 5'd15)
      && (reducer_out_slice_w == 4'd15);
  wire [31:0] leaf_fire_count_inc_w = atomic_batch_fire_w ? 32'd{producers} : 32'd0;
  wire [31:0] source_fold_next_w =
      {_source_fold_terms(producers)};

{_leaf_assigns(producers)}
{_batch_ready_assign(mode=mode)}

  assign reducer_out_ready_w = running_q && (SOURCE_ONLY_MODE == 1'b0) && (cycle_count_q[0] || cycle_count_q[3] || !done_q);
  assign done = done_q;
  assign final_command_id = final_command_id_q;
  assign final_head_id = final_head_id_q;
  assign final_global_max = final_global_max_q;
  assign final_exp_sum = final_exp_sum_q;
  assign final_slice = final_slice_q;
  assign final_last = final_last_q;
  assign final_value = final_value_q;
  assign source_fold = source_fold_q;
  assign cycle_count = cycle_count_q;
  assign leaf_fire_count = leaf_fire_count_q;
  assign observed_result_count = observed_result_count_q;
  assign completed_command_count = (SOURCE_ONLY_MODE == 1'b1) ? 32'd0 : completed_command_count_w;
  assign local_root_completed_count = (SOURCE_ONLY_MODE == 1'b1) ? 32'd0 : local_root_completed_count_w;
  assign temporal_merge_completed_count = (SOURCE_ONLY_MODE == 1'b1) ? 32'd0 : temporal_merge_completed_count_w;
  assign local_stall_cycles = (SOURCE_ONLY_MODE == 1'b1) ? 32'd0 : local_stall_cycles_w;
  assign output_stall_cycles = (SOURCE_ONLY_MODE == 1'b1) ? 32'd0 : output_stall_cycles_w;
  assign source_stall_cycles = source_stall_cycles_q;
  assign protocol_error_seen =
      (SOURCE_ONLY_MODE == 1'b1)
      ? 1'b0
      : (reducer_protocol_error_w || group_contract_error_w || local_tree_protocol_error_w || temporal_merge_protocol_error_w);
{reducer_block}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running_q <= 1'b0;
      done_q <= 1'b0;
      cycle_count_q <= 32'd0;
      leaf_fire_count_q <= 32'd0;
      observed_result_count_q <= 32'd0;
      source_fold_q <= 32'd0;
      source_stall_cycles_q <= 32'd0;
      final_command_id_q <= 16'd0;
      final_head_id_q <= 5'd0;
      final_global_max_q <= 32'sd0;
      final_exp_sum_q <= 33'd0;
      final_slice_q <= 4'd0;
      final_last_q <= 1'b0;
      final_value_q <= 328'd0;
      shared_lfsr_q <= 32'h1;
      shared_beat_count_q <= 12'd0;
    end else begin
      if (start) begin
        running_q <= 1'b1;
        done_q <= 1'b0;
        cycle_count_q <= 32'd0;
        leaf_fire_count_q <= 32'd0;
        observed_result_count_q <= 32'd0;
        source_fold_q <= seed ^ 32'h5a5a1234;
        source_stall_cycles_q <= 32'd0;
        final_command_id_q <= 16'd0;
        final_head_id_q <= 5'd0;
        final_global_max_q <= 32'sd0;
        final_exp_sum_q <= 33'd0;
        final_slice_q <= 4'd0;
        final_last_q <= 1'b0;
        final_value_q <= 328'd0;
        shared_lfsr_q <= seed ^ 32'h9e3779b9;
        shared_beat_count_q <= 12'd0;
      end else begin
        if (running_q && !done_q) begin
          cycle_count_q <= cycle_count_q + 1'b1;
        end
        if (running_q && atomic_batch_fire_w) begin
          shared_lfsr_q <= {{shared_lfsr_q[30:0],
              shared_lfsr_q[31] ^ shared_lfsr_q[21] ^ shared_lfsr_q[1] ^ shared_lfsr_q[0]}};
          shared_beat_count_q <= shared_beat_count_q + 1'b1;
          source_fold_q <= source_fold_q ^ source_fold_next_w;
        end
        if (running_q) begin
          leaf_fire_count_q <= leaf_fire_count_q + leaf_fire_count_inc_w;
          if (batch_pending_w && !atomic_batch_fire_w) begin
            source_stall_cycles_q <= source_stall_cycles_q + 1'b1;
          end
        end
        if (SOURCE_ONLY_MODE == 1'b1) begin
          if (running_q && atomic_batch_fire_w) begin
            observed_result_count_q <= observed_result_count_q + 1'b1;
            final_command_id_q <= leaf_command_id_w[0 +: 16];
            final_head_id_q <= leaf_head_id_w[0 +: HEAD_ID_BITS];
            final_global_max_q <= leaf_global_max_w[0 +: 32];
            final_exp_sum_q <= leaf_exp_sum_w[0 +: 33];
            final_slice_q <= leaf_slice_w[0 +: SLICE_BITS];
            final_last_q <= leaf_last_w[0];
            final_value_q <= leaf_value_w[0 +: PARTIAL_PAYLOAD_BITS];
            if (shared_beat_count_q == 12'd2047) begin
              done_q <= 1'b1;
              running_q <= 1'b0;
            end
          end
        end else begin
          if (running_q && reducer_result_fire_w) begin
            observed_result_count_q <= observed_result_count_q + 1'b1;
            final_command_id_q <= reducer_out_command_id_w;
            final_head_id_q <= reducer_out_head_id_w;
            final_global_max_q <= reducer_out_global_max_w;
            final_exp_sum_q <= reducer_out_exp_sum_w;
            final_slice_q <= reducer_out_slice_w;
            final_last_q <= reducer_out_last_w;
            final_value_q <= reducer_out_value_w;
          end
          if (running_q && reducer_final_result_w) begin
            done_q <= 1'b1;
            running_q <= 1'b0;
          end
        end
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    mode = str(params["mode"])
    reducer_top = f"{top_name}__reducer"
    reducer_manifest: dict[str, Any] | None = None
    reducer_rtl = ""

    out_dir.mkdir(parents=True, exist_ok=True)
    if mode == "reducer":
        with tempfile.TemporaryDirectory(prefix="score32_exact_local_temporal_gqa8_physical_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            reducer_dir = temp_dir / "reducer"
            generate_reducer(
                {
                    "top_name": reducer_top,
                    "attention_score32_exact_local_temporal_reducer_gqa8": {
                    "producers": int(params["producers"]),
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "persistent_waves": int(params["waves"]),
                    "exp_scale_impl": str(params["exp_scale_impl"]),
                },
                "probe_defaults": {
                    "heads": 16,
                        "command_count": 2,
                        "head_bases": [0, 8],
                        "seed": 23,
                    },
                },
                reducer_dir,
            )
            reducer_rtl = (reducer_dir / "top.v").read_text(encoding="utf-8")
            reducer_manifest = json.loads(
                (reducer_dir / "attention_score32_exact_local_temporal_reducer_gqa8_manifest.json").read_text(
                    encoding="utf-8"
                )
            )

    top_text = _top(
        top_name=top_name,
        reducer_top=reducer_top,
        producers=int(params["producers"]),
        mode=mode,
        waves=int(params["waves"]),
    )
    rtl_text = top_text if mode == "source_only" else reducer_rtl + "\n\n" + top_text
    (out_dir / "top.v").write_text(rtl_text + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local_temporal_reducer_gqa8_physical_harness_v1",
        "producers": int(params["producers"]),
        "mode": mode,
        "waves": int(params["waves"]),
        "exp_scale_impl": str(params["exp_scale_impl"]),
        "command_count": 2,
        "query_heads_per_group": 8,
        "head_group_bases": [0, 8],
        "value_slices": 16,
        "head_id_bits": 5,
        "result_interface": "narrow_io_observable_structural_local_temporal_gqa8_harness",
        "equivalence_hash": False,
        "top_pin_bits": _top_pin_bits(),
        "source_traffic_contract": "shared_state_atomic_batch_stable_ready_valid",
        "source_state_contract": "single_shared_held_lfsr_and_12bit_batch_counter",
        "source_batch_contract": "all_leaf_valids_atomic_advance_on_all_leaf_handshakes",
        "command_schedule_contract": "two_explicit_gqa8_head_groups_0_and_8_each_over_8_waves",
        "head_mapping_contract": "head_major_slice_minor_source_order_with_explicit_head_ids",
        "wave_terminal_contract": "advance_only_after_source_head_lane7_slice15_per_wave",
        "per_leaf_payload_state": False,
        "observable_contract": "done_plus_final_command_head_max_sum_slice_last_value_and_counters",
        "caveats": [
            "structural_only",
            "nonlinear_ppa_delta_vs_functional_reducer_measurement",
        ],
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": _PROPOSAL_PATH,
        "submodule_manifests": {
            "gqa8_reducer": reducer_manifest,
        },
    }
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
