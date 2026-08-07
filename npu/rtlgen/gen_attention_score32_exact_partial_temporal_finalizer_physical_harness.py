#!/usr/bin/env python3
"""Generate a narrow-IO physical harness for SRAM temporal reduction and finalization."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream_sram import (
    generate as generate_temporal,
)
from npu.rtlgen.gen_attention_score32_exact_root_finalizer import (
    generate as generate_finalizer,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_partial_temporal_finalizer_physical_harness"
_MANIFEST = "attention_score32_exact_partial_temporal_finalizer_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_exact_partial_physical_calibration_v1"
_PROPOSAL_PATH = f"docs/proposals/{_PROPOSAL_ID}/proposal.json"
_TOP_PIN_BITS = 388


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
    divider_lanes = int(body.get("divider_lanes", 8))
    if divider_lanes not in {1, 2, 4, 8}:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, or 8")
    if int(body.get("heads", 2)) != 2 or int(body.get("windows", 2)) != 2:
        raise SystemExit("physical calibration traffic must remain fixed at 2 heads x 2 windows")
    return {
        "top_name": top_name,
        "divider_lanes": divider_lanes,
    }


def _payload_expression() -> str:
    words = [
        f"{{9'd0, (source_lfsr_q ^ 32'h{0x10203040 * (lane + 1):08x})}}"
        for lane in reversed(range(8))
    ]
    return "{\n      " + ",\n      ".join(words) + "\n  }"


def _top(*, top_name: str, temporal_top: str, finalizer_top: str) -> str:
    return f"""// Generated narrow-IO physical calibration harness.
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [31:0] seed,
    output wire        done,
    output wire [31:0] folded_result,
    output wire [31:0] cycle_count,
    output wire [31:0] source_accepted_count,
    output wire [31:0] temporal_emitted_count,
    output wire [31:0] finalizer_completed_count,
    output wire [31:0] state_request_count,
    output wire [31:0] state_read_count,
    output wire [31:0] state_write_count,
    output wire [31:0] state_stall_count,
    output wire [31:0] output_stall_count,
    output wire [31:0] protocol_error_count
);
  localparam integer SOURCE_BEATS = 64;
  localparam integer FINAL_BEATS = 32;

  reg running_q;
  reg done_q;
  reg [6:0] source_index_q;
  reg [31:0] source_lfsr_q;
  reg [31:0] cycle_count_q;
  reg [31:0] folded_result_q;
  reg [31:0] output_stall_count_q;
  reg [31:0] protocol_error_count_q;

  wire source_valid_w = running_q && source_index_q < SOURCE_BEATS;
  wire source_ready_w;
  wire source_fire_w = source_valid_w && source_ready_w;
  wire [4:0] source_head_w = {{4'd0, source_index_q[5]}};
  wire [13:0] source_window_w = {{13'd0, source_index_q[4]}};
  wire [3:0] source_slice_w = source_index_q[3:0];
  wire [327:0] source_value_w = {_payload_expression()};
  wire [31:0] lfsr_next_w = {{
      source_lfsr_q[30:0],
      source_lfsr_q[31] ^ source_lfsr_q[21]
          ^ source_lfsr_q[1] ^ source_lfsr_q[0]
  }};

  wire temporal_valid_w;
  wire temporal_ready_w;
  wire [15:0] temporal_command_w;
  wire [4:0] temporal_head_w;
  wire [32:0] temporal_sum_w;
  wire [3:0] temporal_slice_w;
  wire temporal_last_w;
  wire [327:0] temporal_value_w;
  wire [31:0] temporal_input_count_w;
  wire [31:0] temporal_emitted_count_w;
  wire [31:0] temporal_output_stalls_w;
  wire [31:0] state_request_count_w;
  wire [31:0] state_read_count_w;
  wire [31:0] state_write_count_w;
  wire [31:0] state_request_stalls_w;
  wire [31:0] state_response_stalls_w;
  wire temporal_state_error_w;
  wire temporal_error_w;

  wire final_valid_w;
  wire final_ready_w =
      running_q && (cycle_count_q[2:0] != 3'b000);
  wire [15:0] final_command_w;
  wire [4:0] final_head_w;
  wire [3:0] final_slice_w;
  wire final_last_w;
  wire [319:0] final_value_w;
  wire [31:0] finalizer_completed_count_w;
  wire finalizer_error_w;
  wire final_fire_w = final_valid_w && final_ready_w;
  wire [31:0] final_fold_w =
      {{16'd0, final_command_w}}
      ^ {{27'd0, final_head_w}}
      ^ {{28'd0, final_slice_w}}
      ^ {{31'd0, final_last_w}}
      ^ final_value_w[31:0]
      ^ final_value_w[63:32]
      ^ final_value_w[95:64]
      ^ final_value_w[127:96]
      ^ final_value_w[159:128]
      ^ final_value_w[191:160]
      ^ final_value_w[223:192]
      ^ final_value_w[255:224]
      ^ final_value_w[287:256]
      ^ final_value_w[319:288];

  assign done = done_q;
  assign folded_result = folded_result_q;
  assign cycle_count = cycle_count_q;
  assign source_accepted_count = temporal_input_count_w;
  assign temporal_emitted_count = temporal_emitted_count_w;
  assign finalizer_completed_count = finalizer_completed_count_w;
  assign state_request_count = state_request_count_w;
  assign state_read_count = state_read_count_w;
  assign state_write_count = state_write_count_w;
  assign state_stall_count =
      state_request_stalls_w + state_response_stalls_w;
  assign output_stall_count =
      output_stall_count_q + temporal_output_stalls_w;
  assign protocol_error_count = protocol_error_count_q;

  {temporal_top} u_temporal (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(source_valid_w),
      .in_ready(source_ready_w),
      .in_sequence_id(16'h5100 + {{15'd0, source_index_q[5]}}),
      .in_head_id(source_head_w),
      .in_window_index(source_window_w),
      .in_window_count(15'd2),
      .in_command_id(16'h6200 + {{15'd0, source_index_q[5]}}),
      .in_global_max(32'sd0),
      .in_exp_sum(33'h080000000 + {{27'd0, source_index_q[5:0]}}),
      .in_slice(source_slice_w),
      .in_last(source_slice_w == 4'd15),
      .in_value(source_value_w),
      .out_valid(temporal_valid_w),
      .out_ready(temporal_ready_w),
      .out_sequence_id(),
      .out_head_id(temporal_head_w),
      .out_window_count(),
      .out_command_id(temporal_command_w),
      .out_global_max(),
      .out_exp_sum(temporal_sum_w),
      .out_slice(temporal_slice_w),
      .out_last(temporal_last_w),
      .out_value(temporal_value_w),
      .cycle_count(),
      .input_accepted_count(temporal_input_count_w),
      .merge_completed_count(),
      .emitted_beat_count(temporal_emitted_count_w),
      .completed_head_count(),
      .fifo_full_stall_cycles(),
      .output_stall_cycles(temporal_output_stalls_w),
      .fifo_level(),
      .state_memory_request_count(state_request_count_w),
      .state_memory_read_request_count(state_read_count_w),
      .state_memory_read_response_count(),
      .state_memory_write_count(state_write_count_w),
      .state_memory_request_stall_cycles(state_request_stalls_w),
      .state_memory_response_stall_cycles(state_response_stalls_w),
      .state_memory_protocol_error(temporal_state_error_w),
      .protocol_error(temporal_error_w)
  );

  {finalizer_top} u_finalizer (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(temporal_valid_w),
      .in_ready(temporal_ready_w),
      .in_command_id(temporal_command_w),
      .in_head_id(temporal_head_w),
      .in_exp_sum(temporal_sum_w),
      .in_slice(temporal_slice_w),
      .in_last(temporal_last_w),
      .in_value(temporal_value_w),
      .out_valid(final_valid_w),
      .out_ready(final_ready_w),
      .out_command_id(final_command_w),
      .out_head_id(final_head_w),
      .out_slice(final_slice_w),
      .out_last(final_last_w),
      .out_value(final_value_w),
      .accepted_count(),
      .completed_count(finalizer_completed_count_w),
      .cycle_count(),
      .protocol_error(finalizer_error_w)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running_q <= 1'b0;
      done_q <= 1'b0;
      source_index_q <= 7'd0;
      source_lfsr_q <= 32'h1;
      cycle_count_q <= 32'd0;
      folded_result_q <= 32'd0;
      output_stall_count_q <= 32'd0;
      protocol_error_count_q <= 32'd0;
    end else begin
      if (start && !running_q && !done_q) begin
        running_q <= 1'b1;
        source_lfsr_q <= seed == 0 ? 32'h1 : seed;
      end
      if (running_q) cycle_count_q <= cycle_count_q + 1'b1;
      if (source_fire_w) begin
        source_index_q <= source_index_q + 1'b1;
        source_lfsr_q <= lfsr_next_w;
      end
      if (final_valid_w && !final_ready_w)
        output_stall_count_q <= output_stall_count_q + 1'b1;
      if (final_fire_w) begin
        folded_result_q <= folded_result_q ^ final_fold_w;
        if (finalizer_completed_count_w == FINAL_BEATS - 1) begin
          running_q <= 1'b0;
          done_q <= 1'b1;
        end
      end
      if (temporal_error_w || temporal_state_error_w || finalizer_error_w)
        protocol_error_count_q <= protocol_error_count_q + 1'b1;
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    temporal_top = f"{top_name}__temporal"
    finalizer_top = f"{top_name}__finalizer"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="exact-partial-physical-harness-") as name:
        temp = Path(name)
        temporal_dir = temp / "temporal"
        finalizer_dir = temp / "finalizer"
        generate_temporal(
            {
                "top_name": temporal_top,
                "attention_score32_exact_partial_temporal_stream_sram": {
                    "heads": 32,
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "fifo_depth": 4,
                    "exp_scale_impl": "factored_h33_l64_mul_exact",
                    "keep_hierarchy": True,
                },
            },
            temporal_dir,
        )
        generate_finalizer(
            {
                "top_name": finalizer_top,
                "attention_score32_exact_root_finalizer": {
                    "value_slices": 16,
                    "head_id_bits": 5,
                    "divider_lanes": int(params["divider_lanes"]),
                },
            },
            finalizer_dir,
        )
        temporal_rtl = (temporal_dir / "top.v").read_text(encoding="utf-8")
        finalizer_rtl = (finalizer_dir / "top.v").read_text(encoding="utf-8")
        temporal_manifest = json.loads(
            (
                temporal_dir
                / "attention_score32_exact_partial_temporal_stream_sram_manifest.json"
            ).read_text(encoding="utf-8")
        )
        finalizer_manifest = json.loads(
            (
                finalizer_dir / "attention_score32_exact_root_finalizer_manifest.json"
            ).read_text(encoding="utf-8")
        )
        macro_manifest = json.loads(
            (temporal_dir / "macro_manifest.json").read_text(encoding="utf-8")
        )

    rtl = "\n\n".join(
        (
            temporal_rtl,
            finalizer_rtl,
            _top(
                top_name=top_name,
                temporal_top=temporal_top,
                finalizer_top=finalizer_top,
            ),
        )
    )
    (out_dir / "top.v").write_text(rtl + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    macro_manifest["design_id"] = top_name
    macro_manifest["module"] = top_name
    macro_manifest["flow_variant"] = "exact_partial_temporal_finalizer_physical_harness_v1"
    macro_manifest["source"] = {
        "mode": "generated_physical_harness",
        "generator": (
            "npu/rtlgen/"
            "gen_attention_score32_exact_partial_temporal_finalizer_physical_harness.py"
        ),
    }
    (out_dir / "macro_manifest.json").write_text(
        json.dumps(macro_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "version": 1,
        "generator": (
            "npu/rtlgen/"
            "gen_attention_score32_exact_partial_temporal_finalizer_physical_harness.py"
        ),
        "top_name": top_name,
        "semantic_profile": "exact_partial_temporal_sram_finalizer_physical_harness_v1",
        "divider_lanes": int(params["divider_lanes"]),
        "clock_domains": ["temporal_clk"],
        "clock_port": "clk",
        "traffic": {
            "heads": 2,
            "windows_per_head": 2,
            "slices_per_window": 16,
            "source_beats": 64,
            "finalized_beats": 32,
            "ready_valid_stability": "source state advances only on input handshake",
            "output_stalls": "cycle_count[2:0] == 0",
        },
        "top_pin_bits": _TOP_PIN_BITS,
        "external_interface": "clk_reset_start_seed_done_folded_result_and_counters_only",
        "macro_count": 104,
        "macro_area_um2": 104 * 20.14 * 61.6,
        "persistent_state_inferred_as_flops": False,
        "physical_timing_claim": "single_temporal_clock_domain",
        "whole_dual_clock_common_delay_claim": False,
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": _PROPOSAL_PATH,
        "submodule_manifests": {
            "temporal_sram": temporal_manifest,
            "root_finalizer": finalizer_manifest,
        },
    }
    (out_dir / _MANIFEST).write_text(
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
