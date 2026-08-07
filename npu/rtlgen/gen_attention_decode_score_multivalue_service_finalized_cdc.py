#!/usr/bin/env python3
"""Generate dual-clock decode-score service through full-context finalization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_service_temporal_cdc import (
    generate as generate_service_temporal_cdc,
)
from npu.rtlgen.gen_attention_score32_exact_root_finalizer import (
    generate as generate_finalizer,
)
from npu.sim.perf.attention_exact_partial import HEAD_ID_BITS, VALUE_SLICES

JsonDict = dict[str, Any]

_CONFIG_KEY = "attention_decode_score_multivalue_service_finalized_cdc"
_GENERATOR = "npu/rtlgen/gen_attention_decode_score_multivalue_service_finalized_cdc.py"
_MANIFEST = "attention_decode_score_multivalue_service_finalized_cdc_manifest.json"
_CDC_MANIFEST = "attention_decode_score_multivalue_service_temporal_cdc_manifest.json"
_FINALIZER_MANIFEST = "attention_score32_exact_root_finalizer_manifest.json"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")
    service = body.get("service")
    temporal = body.get("temporal_stream", {})
    if not isinstance(service, dict) or not isinstance(temporal, dict):
        raise SystemExit("service and temporal_stream must be JSON objects")
    service_params = dict(service)
    if str(service_params.get("result_mode", "")).strip().lower() != "exact_partial":
        raise SystemExit("service.result_mode must be exact_partial")
    if int(service_params.get("head_id_bits", HEAD_ID_BITS)) != HEAD_ID_BITS:
        raise SystemExit(f"service.head_id_bits must remain fixed at {HEAD_ID_BITS}")
    clusters = int(service_params.get("cluster_count", 1))
    if not 1 <= clusters <= 32:
        raise SystemExit("service.cluster_count must be in [1, 32]")
    cdc_depth = int(body.get("cdc_fifo_depth", 4))
    if cdc_depth not in {4, 8, 16}:
        raise SystemExit("cdc_fifo_depth must be one of 4, 8, or 16")
    divider_lanes = int(body.get("divider_lanes", 8))
    if divider_lanes not in {1, 2, 4, 8}:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, or 8")
    return {
        "top_name": top_name,
        "service": service_params,
        "temporal": dict(temporal),
        "clusters": clusters,
        "source_w": max(1, (clusters - 1).bit_length()),
        "cdc_depth": cdc_depth,
        "divider_lanes": divider_lanes,
    }


def _wrapper(
    *,
    top_name: str,
    cdc_top: str,
    finalizer_top: str,
    clusters: int,
    source_w: int,
) -> str:
    return f"""module {top_name} (
    input  wire         service_clk,
    input  wire         service_rst_n,
    input  wire         temporal_clk,
    input  wire         temporal_rst_n,
    input  wire         preload_valid,
    output wire         preload_ready,
    input  wire [13:0]  preload_addr,
    input  wire [3:0]   preload_value_slice,
    input  wire [511:0] preload_matrix,
    input  wire [{clusters - 1}:0] cluster_command_valid,
    output wire [{clusters - 1}:0] cluster_command_ready,
    input  wire [{clusters * 16 - 1}:0] cluster_command_id,
    input  wire [{clusters * 16 - 1}:0] cluster_logical_sequence_id,
    input  wire [{clusters * 16 - 1}:0] cluster_logical_command_id,
    input  wire [{clusters * 14 - 1}:0] cluster_window_index,
    input  wire [{clusters * 15 - 1}:0] cluster_window_count,
    input  wire [{clusters * 15 - 1}:0] cluster_command_block_count,
    input  wire [{clusters * HEAD_ID_BITS - 1}:0] cluster_command_head_id,
    input  wire [{clusters * 32 - 1}:0] cluster_command_score_multiplier,
    input  wire [{clusters * 6 - 1}:0] cluster_command_score_shift,
    input  wire [{clusters - 1}:0] cluster_input_valid,
    output wire [{clusters - 1}:0] cluster_input_ready,
    input  wire [{clusters - 1}:0] cluster_input_last,
    input  wire [{clusters * 8 - 1}:0] cluster_input_a,
    input  wire [{clusters * 64 - 1}:0] cluster_input_b,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_sequence_id,
    output wire [14:0]  out_window_count,
    output wire [15:0]  out_command_id,
    output wire [{HEAD_ID_BITS - 1}:0] out_head_id,
    output wire [3:0]   out_slice,
    output wire         out_last,
    output wire [319:0] out_value,
    output wire [{clusters - 1}:0] cluster_metadata_busy,
    output wire         service_shared_result_valid,
    output wire         service_shared_result_ready,
    output wire [{source_w - 1}:0] service_shared_result_cluster,
    output wire [15:0]  service_shared_result_command_id,
    output wire         service_shared_result_last,
    output wire [{clusters * 32 - 1}:0] service_cluster_accepted_count,
    output wire [{clusters * 32 - 1}:0] service_cluster_completed_count,
    output wire [31:0]  service_accepted_req_count,
    output wire [31:0]  service_emitted_resp_count,
    output wire [31:0]  temporal_input_accepted_count,
    output wire [31:0]  temporal_merge_completed_count,
    output wire [31:0]  temporal_emitted_beat_count,
    output wire [31:0]  temporal_completed_head_count,
    output wire [31:0]  temporal_output_stall_cycles,
    output wire [31:0]  cdc_write_occupancy,
    output wire [31:0]  cdc_read_occupancy,
    output wire [31:0]  cdc_accepted_count,
    output wire [31:0]  cdc_emitted_count,
    output wire [31:0]  cdc_full_cycles,
    output wire [31:0]  cdc_empty_cycles,
    output wire         cdc_overflow_error,
    output wire         cdc_underflow_error,
    output wire         cdc_write_protocol_error,
    output wire         cdc_read_protocol_error,
    output wire [31:0]  finalizer_accepted_count,
    output wire [31:0]  finalizer_completed_count,
    output wire [31:0]  finalizer_cycle_count,
    output wire         metadata_protocol_error,
    output wire         cdc_wrapper_protocol_error,
    output wire         service_protocol_error,
    output wire         temporal_protocol_error,
    output wire         finalizer_protocol_error,
    output wire         protocol_error
);
  localparam integer HEAD_ID_BITS = {HEAD_ID_BITS};

  wire temporal_out_valid_w;
  wire temporal_out_ready_w;
  wire [15:0] temporal_out_sequence_id_w;
  wire [HEAD_ID_BITS-1:0] temporal_out_head_id_w;
  wire [14:0] temporal_out_window_count_w;
  wire [15:0] temporal_out_command_id_w;
  wire [31:0] temporal_out_global_max_w;
  wire [32:0] temporal_out_exp_sum_w;
  wire [3:0] temporal_out_slice_w;
  wire temporal_out_last_w;
  wire [327:0] temporal_out_value_w;

  wire finalizer_in_ready_w;
  wire finalizer_out_valid_w;
  wire finalizer_out_ready_w;
  wire [15:0] finalizer_out_command_id_w;
  wire [HEAD_ID_BITS-1:0] finalizer_out_head_id_w;
  wire [3:0] finalizer_out_slice_w;
  wire finalizer_out_last_w;
  wire [319:0] finalizer_out_value_w;

  reg metadata_valid_q;
  reg [15:0] metadata_sequence_id_q;
  reg [14:0] metadata_window_count_q;
  reg [15:0] metadata_command_id_q;
  reg [HEAD_ID_BITS-1:0] metadata_head_id_q;
  reg [3:0] metadata_slice_q;
  reg metadata_last_q;
  reg metadata_protocol_error_q;

  wire temporal_domain_error_w;
  wire metadata_open_w = !metadata_valid_q && !temporal_domain_error_w;
  wire finalizer_input_fire_w =
      temporal_out_valid_w && temporal_out_ready_w;
  wire finalizer_output_metadata_error_w =
      finalizer_out_valid_w
      && (!metadata_valid_q
          || finalizer_out_command_id_w != metadata_command_id_q
          || finalizer_out_head_id_w != metadata_head_id_q
          || finalizer_out_slice_w != metadata_slice_q
          || finalizer_out_last_w != metadata_last_q);
  assign temporal_domain_error_w =
      metadata_protocol_error_q || finalizer_output_metadata_error_w
      || cdc_wrapper_protocol_error || temporal_protocol_error
      || finalizer_protocol_error;
  wire finalizer_output_fire_w =
      finalizer_out_valid_w && finalizer_out_ready_w;

  assign temporal_out_ready_w =
      finalizer_in_ready_w && metadata_open_w;
  assign finalizer_out_ready_w =
      out_ready && metadata_valid_q
      && !finalizer_output_metadata_error_w && !temporal_domain_error_w;
  assign out_valid =
      finalizer_out_valid_w && metadata_valid_q
      && !finalizer_output_metadata_error_w && !temporal_domain_error_w;
  assign out_sequence_id = metadata_sequence_id_q;
  assign out_window_count = metadata_window_count_q;
  assign out_command_id = finalizer_out_command_id_w;
  assign out_head_id = finalizer_out_head_id_w;
  assign out_slice = finalizer_out_slice_w;
  assign out_last = finalizer_out_last_w;
  assign out_value = finalizer_out_value_w;
  assign metadata_protocol_error =
      metadata_protocol_error_q || finalizer_output_metadata_error_w;
  assign protocol_error =
      metadata_protocol_error || cdc_wrapper_protocol_error
      || service_protocol_error || temporal_protocol_error
      || finalizer_protocol_error || cdc_overflow_error
      || cdc_underflow_error || cdc_write_protocol_error
      || cdc_read_protocol_error;

  always @(posedge temporal_clk or negedge temporal_rst_n) begin
    if (!temporal_rst_n) begin
      metadata_valid_q <= 1'b0;
      metadata_sequence_id_q <= 16'd0;
      metadata_window_count_q <= 15'd0;
      metadata_command_id_q <= 16'd0;
      metadata_head_id_q <= {{HEAD_ID_BITS{{1'b0}}}};
      metadata_slice_q <= 4'd0;
      metadata_last_q <= 1'b0;
      metadata_protocol_error_q <= 1'b0;
    end else begin
      if (finalizer_output_metadata_error_w)
        metadata_protocol_error_q <= 1'b1;
      if (finalizer_input_fire_w) begin
        metadata_valid_q <= 1'b1;
        metadata_sequence_id_q <= temporal_out_sequence_id_w;
        metadata_window_count_q <= temporal_out_window_count_w;
        metadata_command_id_q <= temporal_out_command_id_w;
        metadata_head_id_q <= temporal_out_head_id_w;
        metadata_slice_q <= temporal_out_slice_w;
        metadata_last_q <= temporal_out_last_w;
      end
      if (finalizer_output_fire_w)
        metadata_valid_q <= 1'b0;
    end
  end

  {cdc_top} u_service_temporal_cdc (
      .service_clk(service_clk),
      .service_rst_n(service_rst_n),
      .temporal_clk(temporal_clk),
      .temporal_rst_n(temporal_rst_n),
      .preload_valid(preload_valid),
      .preload_ready(preload_ready),
      .preload_addr(preload_addr),
      .preload_value_slice(preload_value_slice),
      .preload_matrix(preload_matrix),
      .cluster_command_valid(cluster_command_valid),
      .cluster_command_ready(cluster_command_ready),
      .cluster_command_id(cluster_command_id),
      .cluster_logical_sequence_id(cluster_logical_sequence_id),
      .cluster_logical_command_id(cluster_logical_command_id),
      .cluster_window_index(cluster_window_index),
      .cluster_window_count(cluster_window_count),
      .cluster_command_block_count(cluster_command_block_count),
      .cluster_command_head_id(cluster_command_head_id),
      .cluster_command_score_multiplier(cluster_command_score_multiplier),
      .cluster_command_score_shift(cluster_command_score_shift),
      .cluster_input_valid(cluster_input_valid),
      .cluster_input_ready(cluster_input_ready),
      .cluster_input_last(cluster_input_last),
      .cluster_input_a(cluster_input_a),
      .cluster_input_b(cluster_input_b),
      .out_valid(temporal_out_valid_w),
      .out_ready(temporal_out_ready_w),
      .out_sequence_id(temporal_out_sequence_id_w),
      .out_head_id(temporal_out_head_id_w),
      .out_window_count(temporal_out_window_count_w),
      .out_command_id(temporal_out_command_id_w),
      .out_global_max(temporal_out_global_max_w),
      .out_exp_sum(temporal_out_exp_sum_w),
      .out_slice(temporal_out_slice_w),
      .out_last(temporal_out_last_w),
      .out_value(temporal_out_value_w),
      .cluster_metadata_busy(cluster_metadata_busy),
      .service_shared_result_valid(service_shared_result_valid),
      .service_shared_result_ready(service_shared_result_ready),
      .service_shared_result_cluster(service_shared_result_cluster),
      .service_shared_result_command_id(service_shared_result_command_id),
      .service_shared_result_last(service_shared_result_last),
      .service_cluster_accepted_count(service_cluster_accepted_count),
      .service_cluster_completed_count(service_cluster_completed_count),
      .service_accepted_req_count(service_accepted_req_count),
      .service_emitted_resp_count(service_emitted_resp_count),
      .temporal_input_accepted_count(temporal_input_accepted_count),
      .temporal_merge_completed_count(temporal_merge_completed_count),
      .temporal_emitted_beat_count(temporal_emitted_beat_count),
      .temporal_completed_head_count(temporal_completed_head_count),
      .temporal_output_stall_cycles(temporal_output_stall_cycles),
      .cdc_write_occupancy(cdc_write_occupancy),
      .cdc_read_occupancy(cdc_read_occupancy),
      .cdc_accepted_count(cdc_accepted_count),
      .cdc_emitted_count(cdc_emitted_count),
      .cdc_full_cycles(cdc_full_cycles),
      .cdc_empty_cycles(cdc_empty_cycles),
      .cdc_overflow_error(cdc_overflow_error),
      .cdc_underflow_error(cdc_underflow_error),
      .cdc_write_protocol_error(cdc_write_protocol_error),
      .cdc_read_protocol_error(cdc_read_protocol_error),
      .wrapper_protocol_error(cdc_wrapper_protocol_error),
      .service_protocol_error(service_protocol_error),
      .temporal_protocol_error(temporal_protocol_error)
  );

  {finalizer_top} u_finalizer (
      .clk(temporal_clk),
      .rst_n(temporal_rst_n),
      .in_valid(temporal_out_valid_w && metadata_open_w),
      .in_ready(finalizer_in_ready_w),
      .in_command_id(temporal_out_command_id_w),
      .in_head_id(temporal_out_head_id_w),
      .in_exp_sum(temporal_out_exp_sum_w),
      .in_slice(temporal_out_slice_w),
      .in_last(temporal_out_last_w),
      .in_value(temporal_out_value_w),
      .out_valid(finalizer_out_valid_w),
      .out_ready(finalizer_out_ready_w),
      .out_command_id(finalizer_out_command_id_w),
      .out_head_id(finalizer_out_head_id_w),
      .out_slice(finalizer_out_slice_w),
      .out_last(finalizer_out_last_w),
      .out_value(finalizer_out_value_w),
      .accepted_count(finalizer_accepted_count),
      .completed_count(finalizer_completed_count),
      .cycle_count(finalizer_cycle_count),
      .protocol_error(finalizer_protocol_error)
  );
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    cdc_top = f"{top_name}__service_temporal_cdc"
    finalizer_top = f"{top_name}__finalizer"
    out_dir.mkdir(parents=True, exist_ok=True)

    cdc_config = {
        "top_name": cdc_top,
        "attention_decode_score_multivalue_service_temporal_cdc": {
            "service": params["service"],
            "temporal_stream": params["temporal"],
            "cdc_fifo_depth": int(params["cdc_depth"]),
        },
    }
    finalizer_config = {
        "top_name": finalizer_top,
        "attention_score32_exact_root_finalizer": {
            "value_slices": VALUE_SLICES,
            "head_id_bits": HEAD_ID_BITS,
            "divider_lanes": int(params["divider_lanes"]),
        },
    }
    with tempfile.TemporaryDirectory(prefix="decode-service-finalized-cdc-gen-") as name:
        temp = Path(name)
        cdc_dir = temp / "cdc"
        finalizer_dir = temp / "finalizer"
        generate_service_temporal_cdc(cdc_config, cdc_dir)
        generate_finalizer(finalizer_config, finalizer_dir)
        cdc_rtl = (cdc_dir / "top.v").read_text(encoding="utf-8")
        finalizer_rtl = (finalizer_dir / "top.v").read_text(encoding="utf-8")
        cdc_manifest = json.loads(
            (cdc_dir / _CDC_MANIFEST).read_text(encoding="utf-8")
        )
        finalizer_manifest = json.loads(
            (finalizer_dir / _FINALIZER_MANIFEST).read_text(encoding="utf-8")
        )

    wrapper_rtl = _wrapper(
        top_name=top_name,
        cdc_top=cdc_top,
        finalizer_top=finalizer_top,
        clusters=int(params["clusters"]),
        source_w=int(params["source_w"]),
    )
    top_text = "\n\n".join((cdc_rtl, finalizer_rtl, wrapper_rtl)) + "\n"
    (out_dir / "top.v").write_text(top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": 1,
        "top_name": top_name,
        "generator": _GENERATOR,
        "semantic_profile": "decode_score_multivalue_service_finalized_cdc_v1",
        "result_mode": "exact_partial_to_exact_finalized",
        "cluster_count": int(params["clusters"]),
        "divider_lanes": int(params["divider_lanes"]),
        "full_context_normalization_embodied": True,
        "output_interface": {
            "kind": "ready_valid_exact_finalized_slice_stream",
            "value_bits": 320,
            "beats_per_head": VALUE_SLICES,
            "metadata": [
                "logical_sequence_id",
                "window_count",
                "logical_command_id",
                "head_id",
                "slice",
                "last",
            ],
        },
        "finalizer_metadata_hold": {
            "capture": "exactly_on_finalizer_input_handshake",
            "release": "matching_finalizer_output_handshake",
            "consistency_checked": [
                "logical_command_id",
                "head_id",
                "slice",
                "last",
            ],
            "single_inflight": True,
        },
        "remaining_abstractions": [
            "persistent_state_sram_physical_mapping",
            "synchronizer_metastability_mtbf_and_library_cells",
            "external_hbm_dram",
            "physical_ppa",
        ],
        "submodule_manifests": {
            "service_temporal_cdc": cdc_manifest,
            "root_finalizer": finalizer_manifest,
        },
        "dependency_sources": [
            {"path": _GENERATOR, "sha256": _sha256_file(Path(__file__))},
            {
                "path": "npu/rtlgen/gen_attention_decode_score_multivalue_service_temporal_cdc.py",
                "sha256": _sha256_file(
                    REPO_ROOT
                    / "npu/rtlgen/gen_attention_decode_score_multivalue_service_temporal_cdc.py"
                ),
            },
            {
                "path": "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py",
                "sha256": _sha256_file(
                    REPO_ROOT
                    / "npu/rtlgen/gen_attention_score32_exact_root_finalizer.py"
                ),
            },
        ],
        "generated_top_sha256": _sha256_text(top_text),
    }
    (out_dir / _MANIFEST).write_text(
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
