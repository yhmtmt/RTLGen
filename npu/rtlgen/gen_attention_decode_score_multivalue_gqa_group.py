#!/usr/bin/env python3
"""Generate an 8-head GQA wrapper around the shared-score multivalue cluster."""

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


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(config: dict[str, Any]) -> dict[str, int | str]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_decode_score_multivalue_gqa_group")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_decode_score_multivalue_gqa_group")

    max_blocks = int(body.get("max_blocks", 16384))
    array_n = int(body.get("array_n", 8))
    value_slices = int(body.get("value_slices", 16))
    scale_lanes = int(body.get("score_scale_lanes_per_cycle", 1))
    divider_impl = str(body.get("divider_impl", "iterative_restoring")).strip()
    query_heads_per_kv = int(body.get("query_heads_per_kv", 8))
    parallel_lanes = int(body.get("parallel_query_head_lanes", query_heads_per_kv))

    if max_blocks < 8 or max_blocks > 16384 or max_blocks & (max_blocks - 1):
        raise SystemExit("max_blocks must be a power of two in [8, 16384]")
    if array_n != 8:
        raise SystemExit("array_n must be 8")
    if value_slices != 16:
        raise SystemExit("value_slices must be 16")
    if scale_lanes not in {1, 2, 4, 8}:
        raise SystemExit("score_scale_lanes_per_cycle must be one of 1,2,4,8")
    if divider_impl != "iterative_restoring":
        raise SystemExit("divider_impl must be iterative_restoring")
    if query_heads_per_kv != 8:
        raise SystemExit("query_heads_per_kv must be 8 for Llama7B GQA8")
    if parallel_lanes not in {1, 2, 4, 8} or query_heads_per_kv % parallel_lanes:
        raise SystemExit("parallel_query_head_lanes must be one of 1,2,4,8 and divide query_heads_per_kv")

    body.update(
        {
            "max_blocks": max_blocks,
            "array_n": array_n,
            "value_slices": value_slices,
            "score_scale_lanes_per_cycle": scale_lanes,
            "divider_impl": divider_impl,
            "query_heads_per_kv": query_heads_per_kv,
        }
    )
    return {
        "top_name": top_name,
        "max_blocks": max_blocks,
        "array_n": array_n,
        "value_slices": value_slices,
        "score_scale_lanes_per_cycle": scale_lanes,
        "divider_impl": divider_impl,
        "query_heads_per_kv": query_heads_per_kv,
        "parallel_query_head_lanes": parallel_lanes,
    }


def _bus_slice(name: str, index: int, width: int) -> str:
    lo = index * width
    hi = lo + width - 1
    return f"{name}[{hi}:{lo}]"


def _match_expr(name: str, width: int, count: int) -> str:
    if count <= 1:
        return "1'b1"
    base = _bus_slice(name, 0, width)
    return " && ".join(f"({_bus_slice(name, idx, width)} == {base})" for idx in range(1, count))


def _result_mux_cases(query_heads_per_kv: int) -> str:
    cases: list[str] = []
    for head in range(query_heads_per_kv):
        cases.append(
            f"""      3'd{head}: begin
        result_command_id = {_bus_slice("child_result_command_id_bus", head, 16)};
        result_global_max = $signed({_bus_slice("child_result_global_max_bus", head, 32)});
        result_exp_sum = {_bus_slice("child_result_exp_sum_bus", head, 33)};
        result_slice = {_bus_slice("child_result_slice_bus", head, 4)};
        result_last = child_result_last[{head}];
        result_value = {_bus_slice("child_result_value_bus", head, 320)};
      end"""
        )
    return "\n".join(cases)


def _result_ready_assigns(query_heads_per_kv: int, *, selector: str = "result_head_q") -> str:
    assigns = []
    for head in range(query_heads_per_kv):
        assigns.append(f"  assign child_result_ready[{head}] = result_ready && ({selector} == 3'd{head});")
    return "\n".join(assigns)


def _cluster_instances(cluster_top: str, query_heads_per_kv: int) -> str:
    instances: list[str] = []
    for head in range(query_heads_per_kv):
        instances.append(
            f"""  {cluster_top} u_head_{head} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid && command_ready),
      .command_ready(child_command_ready[{head}]),
      .command_id(command_id),
      .command_block_count(command_block_count),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid && input_ready),
      .input_ready(child_input_ready[{head}]),
      .input_last(input_last),
      .input_a(input_query[{head * 8 + 7}:{head * 8}]),
      .input_b(input_key),
      .value_read_req_valid(child_value_read_req_valid[{head}]),
      .value_read_req_ready(child_value_read_req_ready[{head}]),
      .value_read_req_address({_bus_slice("child_value_read_req_address_bus", head, 14)}),
      .value_read_req_slice({_bus_slice("child_value_read_req_slice_bus", head, 4)}),
      .value_response_valid(child_value_response_valid[{head}]),
      .value_response_ready(child_value_response_ready[{head}]),
      .value_response_address(value_response_address),
      .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix),
      .result_valid(child_result_valid[{head}]),
      .result_ready(child_result_ready[{head}]),
      .result_command_id({_bus_slice("child_result_command_id_bus", head, 16)}),
      .result_global_max({_bus_slice("child_result_global_max_bus", head, 32)}),
      .result_exp_sum({_bus_slice("child_result_exp_sum_bus", head, 33)}),
      .result_slice({_bus_slice("child_result_slice_bus", head, 4)}),
      .result_last(child_result_last[{head}]),
      .result_value({_bus_slice("child_result_value_bus", head, 320)}),
      .accepted_count({_bus_slice("child_accepted_count_bus", head, 32)}),
      .completed_count({_bus_slice("child_completed_count_bus", head, 32)}),
      .cycle_count({_bus_slice("child_cycle_count_bus", head, 32)}),
      .protocol_error(child_protocol_error[{head}])
  );"""
        )
    return "\n\n".join(instances)


def _folded_cluster_instances(cluster_top: str, parallel_lanes: int) -> str:
    instances: list[str] = []
    for lane in range(parallel_lanes):
        instances.append(
            f"""  wire signed [7:0] lane_input_query_{lane} =
      input_query[((wave_q * PARALLEL_QUERY_HEAD_LANES + {lane}) * 8) +: 8];

  {cluster_top} u_lane_{lane} (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(child_command_valid),
      .command_ready(child_command_ready[{lane}]),
      .command_id(child_command_id),
      .command_block_count(child_command_block_count),
      .command_score_multiplier(child_command_score_multiplier),
      .command_score_shift(child_command_score_shift),
      .input_valid(input_valid && input_ready),
      .input_ready(child_input_ready[{lane}]),
      .input_last(input_last),
      .input_a(lane_input_query_{lane}),
      .input_b(input_key),
      .value_read_req_valid(child_value_read_req_valid[{lane}]),
      .value_read_req_ready(child_value_read_req_ready[{lane}]),
      .value_read_req_address({_bus_slice("child_value_read_req_address_bus", lane, 14)}),
      .value_read_req_slice({_bus_slice("child_value_read_req_slice_bus", lane, 4)}),
      .value_response_valid(child_value_response_valid[{lane}]),
      .value_response_ready(child_value_response_ready[{lane}]),
      .value_response_address(value_response_address),
      .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix),
      .result_valid(child_result_valid[{lane}]),
      .result_ready(child_result_ready[{lane}]),
      .result_command_id({_bus_slice("child_result_command_id_bus", lane, 16)}),
      .result_global_max({_bus_slice("child_result_global_max_bus", lane, 32)}),
      .result_exp_sum({_bus_slice("child_result_exp_sum_bus", lane, 33)}),
      .result_slice({_bus_slice("child_result_slice_bus", lane, 4)}),
      .result_last(child_result_last[{lane}]),
      .result_value({_bus_slice("child_result_value_bus", lane, 320)}),
      .accepted_count({_bus_slice("child_accepted_count_bus", lane, 32)}),
      .completed_count({_bus_slice("child_completed_count_bus", lane, 32)}),
      .cycle_count({_bus_slice("child_cycle_count_bus", lane, 32)}),
      .protocol_error(child_protocol_error[{lane}])
  );"""
        )
    return "\n\n".join(instances)


def _wrapper(*, top_name: str, params: dict[str, int | str], cluster_top: str) -> str:
    max_blocks = int(params["max_blocks"])
    value_slices = int(params["value_slices"])
    query_heads_per_kv = int(params["query_heads_per_kv"])
    addr_bits = 14
    slice_bits = _clog2(value_slices)
    head_bits = _clog2(query_heads_per_kv)
    addr_match = _match_expr("child_value_read_req_address_bus", addr_bits, query_heads_per_kv)
    slice_match = _match_expr("child_value_read_req_slice_bus", slice_bits, query_heads_per_kv)
    return f"""// Auto-generated by npu/rtlgen/gen_attention_decode_score_multivalue_gqa_group.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [14:0]  command_block_count,
    input  wire [31:0]  command_score_multiplier,
    input  wire [5:0]   command_score_shift,
    input  wire         input_valid,
    output wire         input_ready,
    input  wire         input_last,
    input  wire signed [63:0] input_query,
    input  wire signed [63:0] input_key,
    output wire         value_read_req_valid,
    input  wire         value_read_req_ready,
    output wire [13:0]  value_read_req_address,
    output wire [{slice_bits - 1}:0] value_read_req_slice,
    input  wire         value_response_valid,
    output wire         value_response_ready,
    input  wire [13:0]  value_response_address,
    input  wire [{slice_bits - 1}:0] value_response_slice,
    input  wire [511:0] value_response_matrix,
    output wire         result_valid,
    input  wire         result_ready,
    output wire [{head_bits - 1}:0] result_head,
    output reg  [15:0]  result_command_id,
    output reg  signed [31:0] result_global_max,
    output reg  [32:0]  result_exp_sum,
    output reg  [{slice_bits - 1}:0] result_slice,
    output reg          result_last,
    output reg  [319:0] result_value,
    output reg  [31:0]  accepted_count,
    output reg  [31:0]  completed_count,
    output reg  [31:0]  cycle_count,
    output wire         protocol_error
);
  localparam integer MAX_BLOCKS = {max_blocks};
  localparam integer VALUE_SLICES = {value_slices};
  localparam integer QUERY_HEADS_PER_KV = {query_heads_per_kv};

  reg command_active_q;
  reg [{head_bits - 1}:0] result_head_q;
  reg [{slice_bits - 1}:0] expected_slice_q;
  reg protocol_error_q;

  wire [QUERY_HEADS_PER_KV-1:0] child_command_ready;
  wire [QUERY_HEADS_PER_KV-1:0] child_input_ready;
  wire [QUERY_HEADS_PER_KV-1:0] child_value_read_req_valid;
  wire [QUERY_HEADS_PER_KV-1:0] child_value_read_req_ready;
  wire [QUERY_HEADS_PER_KV-1:0] child_value_response_valid;
  wire [QUERY_HEADS_PER_KV-1:0] child_value_response_ready;
  wire [QUERY_HEADS_PER_KV-1:0] child_result_valid;
  wire [QUERY_HEADS_PER_KV-1:0] child_result_ready;
  wire [QUERY_HEADS_PER_KV-1:0] child_result_last;
  wire [QUERY_HEADS_PER_KV-1:0] child_protocol_error;
  wire [QUERY_HEADS_PER_KV*{addr_bits}-1:0] child_value_read_req_address_bus;
  wire [QUERY_HEADS_PER_KV*{slice_bits}-1:0] child_value_read_req_slice_bus;
  wire [QUERY_HEADS_PER_KV*16-1:0] child_result_command_id_bus;
  wire [QUERY_HEADS_PER_KV*32-1:0] child_result_global_max_bus;
  wire [QUERY_HEADS_PER_KV*33-1:0] child_result_exp_sum_bus;
  wire [QUERY_HEADS_PER_KV*{slice_bits}-1:0] child_result_slice_bus;
  wire [QUERY_HEADS_PER_KV*320-1:0] child_result_value_bus;
  wire [QUERY_HEADS_PER_KV*32-1:0] child_accepted_count_bus;
  wire [QUERY_HEADS_PER_KV*32-1:0] child_completed_count_bus;
  wire [QUERY_HEADS_PER_KV*32-1:0] child_cycle_count_bus;

  wire command_block_count_valid = command_block_count != 0 && command_block_count <= MAX_BLOCKS;
  wire command_ready_all = &child_command_ready;
  wire input_ready_all = &child_input_ready;
  wire any_value_req_valid = |child_value_read_req_valid;
  wire all_value_req_valid = &child_value_read_req_valid;
  wire value_req_addr_match = {addr_match};
  wire value_req_slice_match = {slice_match};
  wire value_req_consistent = all_value_req_valid && value_req_addr_match && value_req_slice_match;
  wire value_req_divergent = any_value_req_valid && (!all_value_req_valid || !value_req_addr_match || !value_req_slice_match);
  wire any_value_rsp_ready = |child_value_response_ready;
  wire value_rsp_ready_all = &child_value_response_ready;
  wire value_rsp_divergent = any_value_rsp_ready && !value_rsp_ready_all;
  wire any_child_protocol_error = |child_protocol_error;

  assign command_ready = !command_active_q && command_block_count_valid && command_ready_all;
  assign input_ready = command_active_q && input_ready_all;

  assign value_read_req_valid = value_req_consistent;
  assign value_read_req_address = child_value_read_req_address_bus[{addr_bits - 1}:0];
  assign value_read_req_slice = child_value_read_req_slice_bus[{slice_bits - 1}:0];
  assign child_value_read_req_ready = {{QUERY_HEADS_PER_KV{{value_read_req_valid && value_read_req_ready}}}};

  assign value_response_ready = value_rsp_ready_all;
  assign child_value_response_valid = {{QUERY_HEADS_PER_KV{{value_response_valid && value_response_ready}}}};

  assign result_valid = child_result_valid[result_head_q];
  assign result_head = result_head_q;
{_result_ready_assigns(query_heads_per_kv)}
  assign protocol_error = protocol_error_q || any_child_protocol_error;

  always @(*) begin
    result_command_id = 16'd0;
    result_global_max = 32'sd0;
    result_exp_sum = 33'd0;
    result_slice = {slice_bits}'d0;
    result_last = 1'b0;
    result_value = 320'd0;
    case (result_head_q)
{_result_mux_cases(query_heads_per_kv)}
      default: begin
        result_command_id = 16'd0;
        result_global_max = 32'sd0;
        result_exp_sum = 33'd0;
        result_slice = {slice_bits}'d0;
        result_last = 1'b0;
        result_value = 320'd0;
      end
    endcase
  end

{_cluster_instances(cluster_top, query_heads_per_kv)}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      command_active_q <= 1'b0;
      result_head_q <= {head_bits}'d0;
      expected_slice_q <= {slice_bits}'d0;
      protocol_error_q <= 1'b0;
      accepted_count <= 32'd0;
      completed_count <= 32'd0;
      cycle_count <= 32'd0;
    end else begin
      cycle_count <= cycle_count + 1'b1;

      if (value_req_divergent || value_rsp_divergent) begin
        protocol_error_q <= 1'b1;
      end

      if (command_valid && command_ready) begin
        command_active_q <= 1'b1;
        result_head_q <= {head_bits}'d0;
        expected_slice_q <= {slice_bits}'d0;
        accepted_count <= accepted_count + 1'b1;
      end

      if (result_valid && result_ready) begin
        if (result_slice != expected_slice_q) begin
          protocol_error_q <= 1'b1;
        end
        if (expected_slice_q == VALUE_SLICES - 1) begin
          if (!result_last) begin
            protocol_error_q <= 1'b1;
          end
          expected_slice_q <= {slice_bits}'d0;
          if (result_head_q == QUERY_HEADS_PER_KV - 1) begin
            command_active_q <= 1'b0;
            completed_count <= completed_count + 1'b1;
          end else begin
            result_head_q <= result_head_q + 1'b1;
          end
        end else begin
          if (result_last) begin
            protocol_error_q <= 1'b1;
          end
          expected_slice_q <= expected_slice_q + 1'b1;
        end
      end
    end
  end
endmodule
"""


def _folded_wrapper(*, top_name: str, params: dict[str, int | str], cluster_top: str) -> str:
    max_blocks = int(params["max_blocks"])
    value_slices = int(params["value_slices"])
    query_heads_per_kv = int(params["query_heads_per_kv"])
    parallel_lanes = int(params["parallel_query_head_lanes"])
    waves = query_heads_per_kv // parallel_lanes
    addr_bits = 14
    slice_bits = _clog2(value_slices)
    lane_bits = _clog2(parallel_lanes)
    wave_bits = _clog2(waves)
    addr_match = _match_expr("child_value_read_req_address_bus", addr_bits, parallel_lanes)
    slice_match = _match_expr("child_value_read_req_slice_bus", slice_bits, parallel_lanes)
    return f"""// Auto-generated folded GQA wrapper by npu/rtlgen/gen_attention_decode_score_multivalue_gqa_group.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [14:0]  command_block_count,
    input  wire [31:0]  command_score_multiplier,
    input  wire [5:0]   command_score_shift,
    input  wire         input_valid,
    output wire         input_ready,
    input  wire         input_last,
    input  wire signed [63:0] input_query,
    input  wire signed [63:0] input_key,
    output wire         value_read_req_valid,
    input  wire         value_read_req_ready,
    output wire [13:0]  value_read_req_address,
    output wire [{slice_bits - 1}:0] value_read_req_slice,
    input  wire         value_response_valid,
    output wire         value_response_ready,
    input  wire [13:0]  value_response_address,
    input  wire [{slice_bits - 1}:0] value_response_slice,
    input  wire [511:0] value_response_matrix,
    output wire         result_valid,
    input  wire         result_ready,
    output wire [2:0]   result_head,
    output reg  [15:0]  result_command_id,
    output reg  signed [31:0] result_global_max,
    output reg  [32:0]  result_exp_sum,
    output reg  [{slice_bits - 1}:0] result_slice,
    output reg          result_last,
    output reg  [319:0] result_value,
    output reg  [31:0]  accepted_count,
    output reg  [31:0]  completed_count,
    output reg  [31:0]  cycle_count,
    output wire         protocol_error
);
  localparam integer MAX_BLOCKS = {max_blocks};
  localparam integer VALUE_SLICES = {value_slices};
  localparam integer QUERY_HEADS_PER_KV = {query_heads_per_kv};
  localparam integer PARALLEL_QUERY_HEAD_LANES = {parallel_lanes};
  localparam integer QUERY_HEAD_WAVES = {waves};

  reg command_active_q;
  reg launch_pending_q;
  reg [{wave_bits - 1}:0] wave_q;
  reg [{lane_bits - 1}:0] result_lane_q;
  reg [{slice_bits - 1}:0] expected_slice_q;
  reg [15:0] active_command_id_q;
  reg [14:0] active_block_count_q;
  reg [31:0] active_score_multiplier_q;
  reg [5:0] active_score_shift_q;
  reg protocol_error_q;

  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_command_ready;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_input_ready;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_value_read_req_valid;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_value_read_req_ready;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_value_response_valid;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_value_response_ready;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_result_valid;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_result_ready;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_result_last;
  wire [PARALLEL_QUERY_HEAD_LANES-1:0] child_protocol_error;
  wire [PARALLEL_QUERY_HEAD_LANES*{addr_bits}-1:0] child_value_read_req_address_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*{slice_bits}-1:0] child_value_read_req_slice_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*16-1:0] child_result_command_id_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*32-1:0] child_result_global_max_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*33-1:0] child_result_exp_sum_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*{slice_bits}-1:0] child_result_slice_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*320-1:0] child_result_value_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*32-1:0] child_accepted_count_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*32-1:0] child_completed_count_bus;
  wire [PARALLEL_QUERY_HEAD_LANES*32-1:0] child_cycle_count_bus;

  wire command_block_count_valid = command_block_count != 0 && command_block_count <= MAX_BLOCKS;
  wire command_ready_all = &child_command_ready;
  wire input_ready_all = &child_input_ready;
  wire child_command_valid = (command_valid && command_ready) || launch_pending_q;
  wire [15:0] child_command_id = command_active_q ? active_command_id_q : command_id;
  wire [14:0] child_command_block_count = command_active_q ? active_block_count_q : command_block_count;
  wire [31:0] child_command_score_multiplier =
      command_active_q ? active_score_multiplier_q : command_score_multiplier;
  wire [5:0] child_command_score_shift = command_active_q ? active_score_shift_q : command_score_shift;
  wire any_value_req_valid = |child_value_read_req_valid;
  wire all_value_req_valid = &child_value_read_req_valid;
  wire value_req_addr_match = {addr_match};
  wire value_req_slice_match = {slice_match};
  wire value_req_consistent = all_value_req_valid && value_req_addr_match && value_req_slice_match;
  wire value_req_divergent = any_value_req_valid &&
      (!all_value_req_valid || !value_req_addr_match || !value_req_slice_match);
  wire any_value_rsp_ready = |child_value_response_ready;
  wire value_rsp_ready_all = &child_value_response_ready;
  wire value_rsp_divergent = any_value_rsp_ready && !value_rsp_ready_all;
  wire any_child_protocol_error = |child_protocol_error;

  assign command_ready = !command_active_q && command_block_count_valid && command_ready_all;
  assign input_ready = command_active_q && !launch_pending_q && input_ready_all;
  assign value_read_req_valid = value_req_consistent;
  assign value_read_req_address = child_value_read_req_address_bus[{addr_bits - 1}:0];
  assign value_read_req_slice = child_value_read_req_slice_bus[{slice_bits - 1}:0];
  assign child_value_read_req_ready =
      {{PARALLEL_QUERY_HEAD_LANES{{value_read_req_valid && value_read_req_ready}}}};
  assign value_response_ready = value_rsp_ready_all;
  assign child_value_response_valid =
      {{PARALLEL_QUERY_HEAD_LANES{{value_response_valid && value_response_ready}}}};
  assign result_valid = child_result_valid[result_lane_q];
  assign result_head = (wave_q * PARALLEL_QUERY_HEAD_LANES) + result_lane_q;
{_result_ready_assigns(parallel_lanes, selector="result_lane_q")}
  assign protocol_error = protocol_error_q || any_child_protocol_error;

  always @(*) begin
    result_command_id = 16'd0;
    result_global_max = 32'sd0;
    result_exp_sum = 33'd0;
    result_slice = {slice_bits}'d0;
    result_last = 1'b0;
    result_value = 320'd0;
    case (result_lane_q)
{_result_mux_cases(parallel_lanes)}
      default: begin
        result_command_id = 16'd0;
        result_global_max = 32'sd0;
        result_exp_sum = 33'd0;
        result_slice = {slice_bits}'d0;
        result_last = 1'b0;
        result_value = 320'd0;
      end
    endcase
  end

{_folded_cluster_instances(cluster_top, parallel_lanes)}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      command_active_q <= 1'b0;
      launch_pending_q <= 1'b0;
      wave_q <= {wave_bits}'d0;
      result_lane_q <= {lane_bits}'d0;
      expected_slice_q <= {slice_bits}'d0;
      active_command_id_q <= 16'd0;
      active_block_count_q <= 15'd0;
      active_score_multiplier_q <= 32'd0;
      active_score_shift_q <= 6'd0;
      protocol_error_q <= 1'b0;
      accepted_count <= 32'd0;
      completed_count <= 32'd0;
      cycle_count <= 32'd0;
    end else begin
      cycle_count <= cycle_count + 1'b1;

      if (value_req_divergent || value_rsp_divergent) begin
        protocol_error_q <= 1'b1;
      end

      if (command_valid && command_ready) begin
        command_active_q <= 1'b1;
        launch_pending_q <= 1'b0;
        wave_q <= {wave_bits}'d0;
        result_lane_q <= {lane_bits}'d0;
        expected_slice_q <= {slice_bits}'d0;
        active_command_id_q <= command_id;
        active_block_count_q <= command_block_count;
        active_score_multiplier_q <= command_score_multiplier;
        active_score_shift_q <= command_score_shift;
        accepted_count <= accepted_count + 1'b1;
      end

      if (launch_pending_q && command_ready_all) begin
        launch_pending_q <= 1'b0;
      end

      if (result_valid && result_ready) begin
        if (result_slice != expected_slice_q) begin
          protocol_error_q <= 1'b1;
        end
        if (expected_slice_q == VALUE_SLICES - 1) begin
          if (!result_last) begin
            protocol_error_q <= 1'b1;
          end
          expected_slice_q <= {slice_bits}'d0;
          if (result_lane_q == PARALLEL_QUERY_HEAD_LANES - 1) begin
            result_lane_q <= {lane_bits}'d0;
            if (wave_q == QUERY_HEAD_WAVES - 1) begin
              command_active_q <= 1'b0;
              completed_count <= completed_count + 1'b1;
            end else begin
              wave_q <= wave_q + 1'b1;
              launch_pending_q <= 1'b1;
            end
          end else begin
            result_lane_q <= result_lane_q + 1'b1;
          end
        end else begin
          if (result_last) begin
            protocol_error_q <= 1'b1;
          end
          expected_slice_q <= expected_slice_q + 1'b1;
        end
      end
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    params = _validate(config)
    top_name = str(params["top_name"])
    cluster_top = f"{top_name}__cluster"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_text:
        tmp_dir = Path(tmp_text)
        cluster_dir = tmp_dir / "cluster"
        generate_cluster(
            {
                "top_name": cluster_top,
                "attention_decode_score_multivalue_cluster": {
                    "max_blocks": int(params["max_blocks"]),
                    "array_n": int(params["array_n"]),
                    "value_slices": int(params["value_slices"]),
                    "divider_impl": str(params["divider_impl"]),
                    "score_scale_lanes_per_cycle": int(params["score_scale_lanes_per_cycle"]),
                },
            },
            cluster_dir,
        )
        cluster_rtl = (cluster_dir / "top.v").read_text(encoding="utf-8")
        cluster_manifest = json.loads(
            (cluster_dir / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
        )

    parallel_lanes = int(params["parallel_query_head_lanes"])
    wrapper = _wrapper if parallel_lanes == int(params["query_heads_per_kv"]) else _folded_wrapper
    rtl = cluster_rtl + "\n\n" + wrapper(top_name=top_name, params=params, cluster_top=cluster_top) + "\n"
    (out_dir / "top.v").write_text(rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_decode_score_multivalue_gqa_group.py",
        "top_name": top_name,
        "semantic_profile": (
            "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1"
            if parallel_lanes == int(params["query_heads_per_kv"])
            else "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_folded_group_v1"
        ),
        "query_heads_per_kv": int(params["query_heads_per_kv"]),
        "max_blocks": int(params["max_blocks"]),
        "score_tile_array_n": int(params["array_n"]),
        "score_scale_lanes_per_cycle": int(params["score_scale_lanes_per_cycle"]),
        "value_slices": int(params["value_slices"]),
        "value_dimensions_per_head": int(params["value_slices"]) * int(params["array_n"]),
        "parallel_query_head_clusters": parallel_lanes,
        "parallel_query_head_lanes": parallel_lanes,
        "query_head_waves": int(params["query_heads_per_kv"]) // parallel_lanes,
        "query_input_replays_per_command": int(params["query_heads_per_kv"]) // parallel_lanes,
        "key_input_replays_per_command": int(params["query_heads_per_kv"]) // parallel_lanes,
        "query_head_score_computations_per_command": int(params["query_heads_per_kv"]),
        "score_passes_per_query_head": 1,
        "shared_external_value_reads_per_block": (
            int(params["value_slices"]) * int(params["query_heads_per_kv"]) // parallel_lanes
        ),
        "internal_value_reads_per_block_per_head": int(params["value_slices"]),
        "result_beats_per_command": int(params["query_heads_per_kv"]) * int(params["value_slices"]),
        "result_value_bits_per_beat": 320,
        "submodule_manifests": {
            "multivalue_cluster": cluster_manifest,
        },
    }
    (out_dir / "attention_decode_score_multivalue_gqa_group_manifest.json").write_text(
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
