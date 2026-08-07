#!/usr/bin/env python3
"""Generate dual-clock exact-partial service and temporal reduction composition."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_service import (
    generate as generate_service,
)
from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream import (
    generate as generate_temporal,
)
from npu.sim.perf.attention_exact_partial import HEAD_ID_BITS, VALUE_SLICES

JsonDict = dict[str, Any]

_CONFIG_KEY = "attention_decode_score_multivalue_service_temporal_cdc"
_GENERATOR = "npu/rtlgen/gen_attention_decode_score_multivalue_service_temporal_cdc.py"
_MANIFEST = "attention_decode_score_multivalue_service_temporal_cdc_manifest.json"
_SERVICE_MANIFEST = "attention_decode_score_multivalue_service_manifest.json"
_TEMPORAL_MANIFEST = "attention_score32_exact_partial_temporal_stream_manifest.json"
_PAYLOAD_BITS = 464


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


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
    temporal_depth = int(temporal.get("fifo_depth", 4))
    if temporal_depth < 2 or temporal_depth > 16 or temporal_depth & (temporal_depth - 1):
        raise SystemExit("temporal_stream.fifo_depth must be a power of two in [2, 16]")
    return {
        "top_name": top_name,
        "service": service_params,
        "clusters": clusters,
        "source_w": _clog2(clusters),
        "cdc_depth": cdc_depth,
        "temporal_depth": temporal_depth,
        "exp_scale_impl": str(
            temporal.get("exp_scale_impl", "factored_h33_l64_mul_exact")
        ).strip(),
        "keep_hierarchy": bool(temporal.get("keep_hierarchy", True)),
    }


def _async_fifo(*, module_name: str, depth: int) -> str:
    addr_w = _clog2(depth)
    ptr_w = addr_w + 1
    return f"""// Dual-clock Gray-pointer FIFO; storage writes occur only in wr_clk.
module {module_name} (
    input  wire         wr_clk,
    input  wire         wr_rst_n,
    input  wire         wr_valid,
    output wire         wr_ready,
    input  wire [{_PAYLOAD_BITS - 1}:0] wr_data,
    input  wire         rd_clk,
    input  wire         rd_rst_n,
    output wire         rd_valid,
    input  wire         rd_ready,
    output wire [{_PAYLOAD_BITS - 1}:0] rd_data,
    output wire [31:0]  wr_occupancy,
    output wire [31:0]  rd_occupancy,
    output reg  [31:0]  accepted_count,
    output reg  [31:0]  emitted_count,
    output reg  [31:0]  full_cycles,
    output reg  [31:0]  empty_cycles,
    output reg          overflow_error,
    output reg          underflow_error,
    output reg          wr_protocol_error,
    output reg          rd_protocol_error
);
  localparam integer DEPTH = {depth};
  localparam integer ADDR_W = {addr_w};
  localparam integer PTR_W = {ptr_w};

  reg [{_PAYLOAD_BITS - 1}:0] mem [0:DEPTH-1];
  reg [PTR_W-1:0] wr_bin_q;
  reg [PTR_W-1:0] wr_gray_q;
  reg [PTR_W-1:0] rd_bin_q;
  reg [PTR_W-1:0] rd_gray_q;
  (* ASYNC_REG = "TRUE" *) reg [PTR_W-1:0] rd_gray_wr_sync1_q;
  (* ASYNC_REG = "TRUE" *) reg [PTR_W-1:0] rd_gray_wr_sync2_q;
  (* ASYNC_REG = "TRUE" *) reg [PTR_W-1:0] wr_gray_rd_sync1_q;
  (* ASYNC_REG = "TRUE" *) reg [PTR_W-1:0] wr_gray_rd_sync2_q;
  reg wr_full_q;
  reg rd_empty_q;
  reg wr_blocked_q;
  reg [{_PAYLOAD_BITS - 1}:0] wr_blocked_data_q;
  reg rd_blocked_q;
  reg [{_PAYLOAD_BITS - 1}:0] rd_blocked_data_q;

  wire wr_fire = wr_valid && wr_ready;
  wire rd_fire = rd_valid && rd_ready;
  wire [PTR_W-1:0] wr_bin_next = wr_bin_q + wr_fire;
  wire [PTR_W-1:0] rd_bin_next = rd_bin_q + rd_fire;
  wire [PTR_W-1:0] wr_gray_next = (wr_bin_next >> 1) ^ wr_bin_next;
  wire [PTR_W-1:0] rd_gray_next = (rd_bin_next >> 1) ^ rd_bin_next;
  wire [PTR_W-1:0] wr_full_compare = {{
      ~rd_gray_wr_sync2_q[PTR_W-1:PTR_W-2],
      rd_gray_wr_sync2_q[PTR_W-3:0]
  }};
  wire wr_full_next = wr_gray_next == wr_full_compare;
  wire rd_empty_next = rd_gray_next == wr_gray_rd_sync2_q;

  function automatic [PTR_W-1:0] gray_to_bin(input [PTR_W-1:0] gray);
    integer bit_index;
    begin
      gray_to_bin[PTR_W-1] = gray[PTR_W-1];
      for (bit_index = PTR_W - 2; bit_index >= 0; bit_index = bit_index - 1)
        gray_to_bin[bit_index] = gray_to_bin[bit_index + 1] ^ gray[bit_index];
    end
  endfunction

  assign wr_ready = !wr_full_q;
  assign rd_valid = !rd_empty_q;
  assign rd_data = mem[rd_bin_q[ADDR_W-1:0]];
  assign wr_occupancy = {{{{(32-PTR_W){{1'b0}}}},
      (wr_bin_q - gray_to_bin(rd_gray_wr_sync2_q))}};
  assign rd_occupancy = {{{{(32-PTR_W){{1'b0}}}},
      (gray_to_bin(wr_gray_rd_sync2_q) - rd_bin_q)}};

  always @(posedge wr_clk or negedge wr_rst_n) begin
    if (!wr_rst_n) begin
      wr_bin_q <= {{PTR_W{{1'b0}}}};
      wr_gray_q <= {{PTR_W{{1'b0}}}};
      rd_gray_wr_sync1_q <= {{PTR_W{{1'b0}}}};
      rd_gray_wr_sync2_q <= {{PTR_W{{1'b0}}}};
      wr_full_q <= 1'b0;
      accepted_count <= 32'd0;
      full_cycles <= 32'd0;
      overflow_error <= 1'b0;
      wr_protocol_error <= 1'b0;
      wr_blocked_q <= 1'b0;
      wr_blocked_data_q <= {_PAYLOAD_BITS}'d0;
    end else begin
      rd_gray_wr_sync1_q <= rd_gray_q;
      rd_gray_wr_sync2_q <= rd_gray_wr_sync1_q;
      wr_bin_q <= wr_bin_next;
      wr_gray_q <= wr_gray_next;
      wr_full_q <= wr_full_next;
      if (wr_fire) begin
        mem[wr_bin_q[ADDR_W-1:0]] <= wr_data;
        accepted_count <= accepted_count + 32'd1;
      end
      if (wr_full_q) full_cycles <= full_cycles + 32'd1;
      if (wr_fire && wr_full_q) overflow_error <= 1'b1;
      if (wr_valid && !wr_ready) begin
        if (wr_blocked_q && wr_data != wr_blocked_data_q)
          wr_protocol_error <= 1'b1;
        wr_blocked_q <= 1'b1;
        wr_blocked_data_q <= wr_data;
      end else begin
        wr_blocked_q <= 1'b0;
      end
    end
  end

  always @(posedge rd_clk or negedge rd_rst_n) begin
    if (!rd_rst_n) begin
      rd_bin_q <= {{PTR_W{{1'b0}}}};
      rd_gray_q <= {{PTR_W{{1'b0}}}};
      wr_gray_rd_sync1_q <= {{PTR_W{{1'b0}}}};
      wr_gray_rd_sync2_q <= {{PTR_W{{1'b0}}}};
      rd_empty_q <= 1'b1;
      emitted_count <= 32'd0;
      empty_cycles <= 32'd0;
      underflow_error <= 1'b0;
      rd_protocol_error <= 1'b0;
      rd_blocked_q <= 1'b0;
      rd_blocked_data_q <= {_PAYLOAD_BITS}'d0;
    end else begin
      wr_gray_rd_sync1_q <= wr_gray_q;
      wr_gray_rd_sync2_q <= wr_gray_rd_sync1_q;
      rd_bin_q <= rd_bin_next;
      rd_gray_q <= rd_gray_next;
      rd_empty_q <= rd_empty_next;
      if (rd_fire) emitted_count <= emitted_count + 32'd1;
      if (rd_empty_q) empty_cycles <= empty_cycles + 32'd1;
      if (rd_fire && rd_empty_q) underflow_error <= 1'b1;
      if (rd_valid && !rd_ready) begin
        if (rd_blocked_q && rd_data != rd_blocked_data_q)
          rd_protocol_error <= 1'b1;
        rd_blocked_q <= 1'b1;
        rd_blocked_data_q <= rd_data;
      end else begin
        rd_blocked_q <= 1'b0;
      end
    end
  end
endmodule
"""


def _wrapper(
    *,
    top_name: str,
    service_top: str,
    temporal_top: str,
    fifo_top: str,
    clusters: int,
    source_w: int,
    temporal_depth: int,
) -> str:
    fifo_level_w = _clog2(temporal_depth) + 1
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
    output wire [{HEAD_ID_BITS - 1}:0] out_head_id,
    output wire [14:0]  out_window_count,
    output wire [15:0]  out_command_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [3:0]   out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output wire [{clusters - 1}:0] cluster_metadata_busy,
    output wire         service_shared_result_valid,
    output wire         service_shared_result_ready,
    output wire [{source_w - 1}:0] service_shared_result_cluster,
    output wire [15:0]  service_shared_result_command_id,
    output wire [{HEAD_ID_BITS - 1}:0] service_shared_result_head_id,
    output wire [3:0]   service_shared_result_slice,
    output wire         service_shared_result_last,
    output wire [{clusters * 32 - 1}:0] service_cluster_accepted_count,
    output wire [{clusters * 32 - 1}:0] service_cluster_completed_count,
    output wire [{clusters - 1}:0] service_cluster_protocol_error,
    output wire [31:0]  service_accepted_req_count,
    output wire [31:0]  service_emitted_resp_count,
    output wire [31:0]  temporal_input_accepted_count,
    output wire [31:0]  temporal_merge_completed_count,
    output wire [31:0]  temporal_emitted_beat_count,
    output wire [31:0]  temporal_completed_head_count,
    output wire [31:0]  temporal_output_stall_cycles,
    output wire [{fifo_level_w - 1}:0] temporal_fifo_level,
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
    output wire         wrapper_protocol_error,
    output wire         service_protocol_error,
    output wire         temporal_protocol_error,
    output wire         protocol_error
);
  localparam integer CLUSTERS = {clusters};
  localparam integer SOURCE_W = {source_w};
  localparam integer HEAD_ID_BITS = {HEAD_ID_BITS};

  reg [CLUSTERS-1:0] metadata_valid_q;
  reg [CLUSTERS*16-1:0] metadata_sequence_id_q;
  reg [CLUSTERS*16-1:0] metadata_logical_command_id_q;
  reg [CLUSTERS*16-1:0] metadata_service_command_id_q;
  reg [CLUSTERS*14-1:0] metadata_window_index_q;
  reg [CLUSTERS*15-1:0] metadata_window_count_q;
  reg wrapper_protocol_error_q;

  wire [CLUSTERS-1:0] service_command_valid_w;
  wire [CLUSTERS-1:0] service_command_ready_w;
  wire service_domain_error_w;
  wire [CLUSTERS-1:0] command_open_w =
      ~metadata_valid_q & {{CLUSTERS{{!service_domain_error_w}}}};
  wire [CLUSTERS-1:0] command_fire_w =
      service_command_valid_w & service_command_ready_w;

  wire [31:0] service_shared_result_global_max_w;
  wire [32:0] service_shared_result_exp_sum_w;
  wire [327:0] service_shared_result_value_w;
  wire selected_metadata_valid_w =
      metadata_valid_q[service_shared_result_cluster];
  wire [15:0] selected_sequence_id_w =
      metadata_sequence_id_q[(service_shared_result_cluster * 16) +: 16];
  wire [15:0] selected_logical_command_id_w =
      metadata_logical_command_id_q[(service_shared_result_cluster * 16) +: 16];
  wire [15:0] selected_service_command_id_w =
      metadata_service_command_id_q[(service_shared_result_cluster * 16) +: 16];
  wire [13:0] selected_window_index_w =
      metadata_window_index_q[(service_shared_result_cluster * 14) +: 14];
  wire [14:0] selected_window_count_w =
      metadata_window_count_q[(service_shared_result_cluster * 15) +: 15];
  wire service_result_metadata_error_w =
      service_shared_result_valid
      && (!selected_metadata_valid_w
          || selected_service_command_id_w != service_shared_result_command_id);
  assign service_domain_error_w =
      wrapper_protocol_error_q || service_result_metadata_error_w
      || service_protocol_error || cdc_overflow_error
      || cdc_write_protocol_error;

  wire cdc_wr_valid =
      service_shared_result_valid
      && selected_metadata_valid_w
      && !service_result_metadata_error_w
      && !service_domain_error_w;
  wire cdc_wr_ready;
  wire [{_PAYLOAD_BITS - 1}:0] cdc_wr_data = {{
      selected_sequence_id_w,
      selected_logical_command_id_w,
      selected_window_index_w,
      selected_window_count_w,
      service_shared_result_head_id,
      service_shared_result_global_max_w,
      service_shared_result_exp_sum_w,
      service_shared_result_slice,
      service_shared_result_last,
      service_shared_result_value_w
  }};
  wire service_to_cdc_fire_w = cdc_wr_valid && cdc_wr_ready;

  wire cdc_rd_valid;
  wire cdc_rd_ready;
  wire [{_PAYLOAD_BITS - 1}:0] cdc_rd_data;
  wire [15:0] temporal_sequence_id_w;
  wire [15:0] temporal_command_id_w;
  wire [13:0] temporal_window_index_w;
  wire [14:0] temporal_window_count_w;
  wire [HEAD_ID_BITS-1:0] temporal_head_id_w;
  wire [31:0] temporal_global_max_w;
  wire [32:0] temporal_exp_sum_w;
  wire [3:0] temporal_slice_w;
  wire temporal_last_w;
  wire [327:0] temporal_value_w;
  wire temporal_in_ready_w;
  wire temporal_domain_error_w =
      temporal_protocol_error || cdc_underflow_error || cdc_read_protocol_error;

  assign {{
      temporal_sequence_id_w,
      temporal_command_id_w,
      temporal_window_index_w,
      temporal_window_count_w,
      temporal_head_id_w,
      temporal_global_max_w,
      temporal_exp_sum_w,
      temporal_slice_w,
      temporal_last_w,
      temporal_value_w
  }} = cdc_rd_data;
  assign service_command_valid_w = cluster_command_valid & command_open_w;
  assign cluster_command_ready = service_command_ready_w & command_open_w;
  assign service_shared_result_ready =
      cdc_wr_ready && selected_metadata_valid_w
      && !service_result_metadata_error_w && !service_domain_error_w;
  assign cdc_rd_ready = temporal_in_ready_w && !temporal_domain_error_w;
  assign cluster_metadata_busy = metadata_valid_q;
  assign wrapper_protocol_error =
      wrapper_protocol_error_q || service_result_metadata_error_w;
  assign protocol_error =
      wrapper_protocol_error || service_protocol_error || temporal_protocol_error
      || cdc_overflow_error || cdc_underflow_error
      || cdc_write_protocol_error || cdc_read_protocol_error;

  integer metadata_i;
  always @(posedge service_clk or negedge service_rst_n) begin
    if (!service_rst_n) begin
      metadata_valid_q <= {{CLUSTERS{{1'b0}}}};
      metadata_sequence_id_q <= {{(CLUSTERS*16){{1'b0}}}};
      metadata_logical_command_id_q <= {{(CLUSTERS*16){{1'b0}}}};
      metadata_service_command_id_q <= {{(CLUSTERS*16){{1'b0}}}};
      metadata_window_index_q <= {{(CLUSTERS*14){{1'b0}}}};
      metadata_window_count_q <= {{(CLUSTERS*15){{1'b0}}}};
      wrapper_protocol_error_q <= 1'b0;
    end else begin
      if (service_result_metadata_error_w)
        wrapper_protocol_error_q <= 1'b1;
      for (metadata_i = 0; metadata_i < CLUSTERS; metadata_i = metadata_i + 1) begin
        if (command_fire_w[metadata_i]) begin
          metadata_valid_q[metadata_i] <= 1'b1;
          metadata_sequence_id_q[(metadata_i*16) +: 16] <=
              cluster_logical_sequence_id[(metadata_i*16) +: 16];
          metadata_logical_command_id_q[(metadata_i*16) +: 16] <=
              cluster_logical_command_id[(metadata_i*16) +: 16];
          metadata_service_command_id_q[(metadata_i*16) +: 16] <=
              cluster_command_id[(metadata_i*16) +: 16];
          metadata_window_index_q[(metadata_i*14) +: 14] <=
              cluster_window_index[(metadata_i*14) +: 14];
          metadata_window_count_q[(metadata_i*15) +: 15] <=
              cluster_window_count[(metadata_i*15) +: 15];
        end
      end
      if (service_to_cdc_fire_w && service_shared_result_last)
        metadata_valid_q[service_shared_result_cluster] <= 1'b0;
    end
  end

  {service_top} u_service (
      .clk(service_clk),
      .rst_n(service_rst_n),
      .preload_valid(preload_valid),
      .preload_ready(preload_ready),
      .preload_addr(preload_addr),
      .preload_value_slice(preload_value_slice),
      .preload_matrix(preload_matrix),
      .cluster_command_valid(service_command_valid_w),
      .cluster_command_ready(service_command_ready_w),
      .cluster_command_id(cluster_command_id),
      .cluster_command_block_count(cluster_command_block_count),
      .cluster_command_head_id(cluster_command_head_id),
      .cluster_command_score_multiplier(cluster_command_score_multiplier),
      .cluster_command_score_shift(cluster_command_score_shift),
      .cluster_input_valid(cluster_input_valid),
      .cluster_input_ready(cluster_input_ready),
      .cluster_input_last(cluster_input_last),
      .cluster_input_a(cluster_input_a),
      .cluster_input_b(cluster_input_b),
      .shared_result_valid(service_shared_result_valid),
      .shared_result_ready(service_shared_result_ready),
      .shared_result_cluster(service_shared_result_cluster),
      .shared_result_command_id(service_shared_result_command_id),
      .shared_result_global_max(service_shared_result_global_max_w),
      .shared_result_exp_sum(service_shared_result_exp_sum_w),
      .shared_result_head_id(service_shared_result_head_id),
      .shared_result_slice(service_shared_result_slice),
      .shared_result_last(service_shared_result_last),
      .shared_result_value(service_shared_result_value_w),
      .cluster_accepted_count(service_cluster_accepted_count),
      .cluster_completed_count(service_cluster_completed_count),
      .cluster_protocol_error(service_cluster_protocol_error),
      .service_accepted_req_count(service_accepted_req_count),
      .service_emitted_resp_count(service_emitted_resp_count),
      .protocol_error(service_protocol_error)
  );

  {fifo_top} u_cdc_fifo (
      .wr_clk(service_clk),
      .wr_rst_n(service_rst_n),
      .wr_valid(cdc_wr_valid),
      .wr_ready(cdc_wr_ready),
      .wr_data(cdc_wr_data),
      .rd_clk(temporal_clk),
      .rd_rst_n(temporal_rst_n),
      .rd_valid(cdc_rd_valid),
      .rd_ready(cdc_rd_ready),
      .rd_data(cdc_rd_data),
      .wr_occupancy(cdc_write_occupancy),
      .rd_occupancy(cdc_read_occupancy),
      .accepted_count(cdc_accepted_count),
      .emitted_count(cdc_emitted_count),
      .full_cycles(cdc_full_cycles),
      .empty_cycles(cdc_empty_cycles),
      .overflow_error(cdc_overflow_error),
      .underflow_error(cdc_underflow_error),
      .wr_protocol_error(cdc_write_protocol_error),
      .rd_protocol_error(cdc_read_protocol_error)
  );

  {temporal_top} u_temporal (
      .clk(temporal_clk),
      .rst_n(temporal_rst_n),
      .in_valid(cdc_rd_valid && !temporal_domain_error_w),
      .in_ready(temporal_in_ready_w),
      .in_sequence_id(temporal_sequence_id_w),
      .in_head_id(temporal_head_id_w),
      .in_window_index(temporal_window_index_w),
      .in_window_count(temporal_window_count_w),
      .in_command_id(temporal_command_id_w),
      .in_global_max(temporal_global_max_w),
      .in_exp_sum(temporal_exp_sum_w),
      .in_slice(temporal_slice_w),
      .in_last(temporal_last_w),
      .in_value(temporal_value_w),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_sequence_id(out_sequence_id),
      .out_head_id(out_head_id),
      .out_window_count(out_window_count),
      .out_command_id(out_command_id),
      .out_global_max(out_global_max),
      .out_exp_sum(out_exp_sum),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .input_accepted_count(temporal_input_accepted_count),
      .merge_completed_count(temporal_merge_completed_count),
      .emitted_beat_count(temporal_emitted_beat_count),
      .completed_head_count(temporal_completed_head_count),
      .output_stall_cycles(temporal_output_stall_cycles),
      .fifo_level(temporal_fifo_level),
      .protocol_error(temporal_protocol_error)
  );
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    service_top = f"{top_name}__service"
    temporal_top = f"{top_name}__temporal"
    fifo_top = f"{top_name}__async_fifo"
    out_dir.mkdir(parents=True, exist_ok=True)
    service_config = {
        "top_name": service_top,
        "attention_decode_score_multivalue_service": params["service"],
    }
    temporal_config = {
        "top_name": temporal_top,
        "attention_score32_exact_partial_temporal_stream": {
            "heads": 32,
            "value_slices": VALUE_SLICES,
            "head_id_bits": HEAD_ID_BITS,
            "fifo_depth": int(params["temporal_depth"]),
            "sequence_id_bits": 16,
            "window_index_bits": 14,
            "window_count_bits": 15,
            "max_window_count": 16384,
            "exp_scale_impl": str(params["exp_scale_impl"]),
            "keep_hierarchy": bool(params["keep_hierarchy"]),
        },
    }
    with tempfile.TemporaryDirectory(prefix="decode-service-temporal-cdc-gen-") as name:
        temp = Path(name)
        service_dir = temp / "service"
        temporal_dir = temp / "temporal"
        generate_service(service_config, service_dir)
        generate_temporal(temporal_config, temporal_dir)
        service_rtl = (service_dir / "top.v").read_text(encoding="utf-8")
        temporal_rtl = (temporal_dir / "top.v").read_text(encoding="utf-8")
        service_manifest = json.loads(
            (service_dir / _SERVICE_MANIFEST).read_text(encoding="utf-8")
        )
        temporal_manifest = json.loads(
            (temporal_dir / _TEMPORAL_MANIFEST).read_text(encoding="utf-8")
        )

    fifo_rtl = _async_fifo(module_name=fifo_top, depth=int(params["cdc_depth"]))
    wrapper_rtl = _wrapper(
        top_name=top_name,
        service_top=service_top,
        temporal_top=temporal_top,
        fifo_top=fifo_top,
        clusters=int(params["clusters"]),
        source_w=int(params["source_w"]),
        temporal_depth=int(params["temporal_depth"]),
    )
    top_text = "\n\n".join((service_rtl, temporal_rtl, fifo_rtl, wrapper_rtl)) + "\n"
    (out_dir / "top.v").write_text(top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": 1,
        "top_name": top_name,
        "generator": _GENERATOR,
        "semantic_profile": "decode_score_multivalue_service_temporal_async_fifo_v1",
        "result_mode": "exact_partial",
        "cluster_count": int(params["clusters"]),
        "cdc_contract": {
            "source_domain": "service_clk/service_rst_n",
            "destination_domain": "temporal_clk/temporal_rst_n",
            "fifo_depth": int(params["cdc_depth"]),
            "fifo_depth_values": [4, 8, 16],
            "payload_bits": _PAYLOAD_BITS,
            "atomic_payload_fields": [
                "logical_sequence_id[16]",
                "logical_command_id[16]",
                "window_index[14]",
                "window_count[15]",
                "head_id[5]",
                "global_max[32]",
                "exp_sum[33]",
                "slice[4]",
                "last[1]",
                "value[328]",
            ],
            "pointer_encoding": "binary_local_gray_crossing",
            "synchronizers": "two_flip_flop_gray_each_direction",
            "storage_write": "registered_in_service_clock_domain",
            "read_interface": "stable_ready_valid",
            "reset_contract": (
                "both active_low resets asserted together; deassertion may be independently skewed"
            ),
        },
        "metadata_contract": {
            "capture": "accepted_service_command",
            "physical_command_id_guard_domain": "service_clk",
            "release": "terminal_service_beat_accepted_into_async_fifo",
        },
        "remaining_abstractions": [
            "downstream_full_context_final_normalizer",
            "persistent_state_sram_physical_mapping",
            "metastability_mtbf_and_library_cell_implementation",
            "physical_ppa",
        ],
        "submodule_manifests": {
            "service": service_manifest,
            "temporal_stream": temporal_manifest,
        },
        "dependency_sources": [
            {"path": _GENERATOR, "sha256": _sha256_file(Path(__file__))},
            {
                "path": "npu/rtlgen/gen_attention_decode_score_multivalue_service.py",
                "sha256": _sha256_file(
                    REPO_ROOT
                    / "npu/rtlgen/gen_attention_decode_score_multivalue_service.py"
                ),
            },
            {
                "path": "npu/rtlgen/gen_attention_score32_exact_partial_temporal_stream.py",
                "sha256": _sha256_file(
                    REPO_ROOT
                    / "npu/rtlgen/gen_attention_score32_exact_partial_temporal_stream.py"
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
