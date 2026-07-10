#!/usr/bin/env python3
"""Generate a bounded producer/consumer attention cluster with semantic outputs.

Each accepted command occupies one producer slot. A producer derives q8 query,
key, and value payloads from the command seed and id, computes an 8-lane score
row as exact signed sums of q*k products, and holds the payload until a shared
consumer selects it. Consumers apply a bucketed-exp LUT plus exact rowwise
normalization, accumulate weighted q8 values into signed 40-bit outputs, and
hold one result entry until the external result channel accepts it.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SEMANTIC_PROFILE = "q8_k8_v8_a32_s32_w16_exp_lut_div_b20"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    top_name = str(cfg.get("top_name", "")).strip()
    if not top_name:
        raise SystemExit("config top_name must not be empty")

    cluster = cfg.get("attention_separated_cluster")
    if not isinstance(cluster, dict):
        raise SystemExit("config must contain attention_separated_cluster object")

    producer_count = _as_int(cluster, "producer_count", 1)
    consumer_count = _as_int(cluster, "consumer_count", 1)
    row_elems = _as_int(cluster, "row_elems", 8)
    head_dim = _as_int(cluster, "head_dim", 8)
    value_dim = _as_int(cluster, "value_dim", 8)
    score_bits = _as_int(cluster, "score_bits", 32)
    weight_bits = _as_int(cluster, "weight_bits", 16)
    input_frac_bits = _as_int(cluster, "input_frac_bits", 28)
    exp_bucket_shift = _as_int(cluster, "exp_bucket_shift", 20)

    if producer_count < 1 or producer_count > 8:
        raise SystemExit("attention_separated_cluster.producer_count must be in [1, 8]")
    if consumer_count < 1 or consumer_count > 8:
        raise SystemExit("attention_separated_cluster.consumer_count must be in [1, 8]")
    if consumer_count > producer_count:
        raise SystemExit(
            "attention_separated_cluster.consumer_count must be less than or equal to producer_count"
        )
    if row_elems != 8:
        raise SystemExit("attention_separated_cluster.row_elems must be 8")
    if head_dim != 8:
        raise SystemExit("attention_separated_cluster.head_dim must be 8")
    if value_dim != 8:
        raise SystemExit("attention_separated_cluster.value_dim must be 8")
    if score_bits != 32:
        raise SystemExit("attention_separated_cluster.score_bits must be 32")
    if weight_bits != 16:
        raise SystemExit("attention_separated_cluster.weight_bits must be 16")
    if input_frac_bits != 28:
        raise SystemExit("attention_separated_cluster.input_frac_bits must be 28")
    if exp_bucket_shift != 20:
        raise SystemExit("attention_separated_cluster.exp_bucket_shift must be 20")

    cluster["producer_count"] = producer_count
    cluster["consumer_count"] = consumer_count
    cluster["row_elems"] = row_elems
    cluster["head_dim"] = head_dim
    cluster["value_dim"] = value_dim
    cluster["score_bits"] = score_bits
    cluster["weight_bits"] = weight_bits
    cluster["input_frac_bits"] = input_frac_bits
    cluster["exp_bucket_shift"] = exp_bucket_shift
    return cluster


def _producer_module(
    *, module_name: str, row_elems: int, head_dim: int, value_dim: int, score_bits: int, score_frac_bits: int
) -> str:
    score_width = row_elems * score_bits
    value_matrix_width = row_elems * value_dim * 8
    return f"""module {module_name} #(parameter integer PRODUCER_INDEX = 0) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         load_valid,
    input  wire [15:0]                  load_command_id,
    input  wire [31:0]                  load_seed,
    input  wire                         pop_valid,
    output reg                          payload_valid,
    output reg  [15:0]                  payload_command_id,
    output reg  [{score_width - 1}:0]   payload_score_row,
    output reg  [{value_matrix_width - 1}:0] payload_value_matrix
);
  integer row_idx;
  integer dim_idx;
  reg signed [31:0] score_accum;

  function automatic signed [7:0] derive_q8;
    input [31:0] seed;
    input [15:0] command_id;
    input integer tag;
    input integer lane_a;
    input integer lane_b;
    reg [31:0] mixed;
    begin
      mixed = seed ^ {{16'h0, command_id}};
      mixed = mixed ^ (tag * 32'h119d_e1f3);
      mixed = mixed ^ (lane_a * 32'h344b_5409);
      mixed = mixed ^ (lane_b * 32'h27d4_eb2d);
      mixed = mixed ^ (mixed >> 16);
      mixed = mixed ^ (mixed >> 8);
      derive_q8 = {{{{4{{mixed[3]}}}}, mixed[3:0]}};
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      payload_valid <= 1'b0;
      payload_command_id <= 16'h0;
      payload_score_row <= {{{score_width}{{1'b0}}}};
      payload_value_matrix <= {{{value_matrix_width}{{1'b0}}}};
    end else begin
      if (load_valid) begin
        payload_valid <= 1'b1;
        payload_command_id <= load_command_id;
        for (row_idx = 0; row_idx < {row_elems}; row_idx = row_idx + 1) begin
          score_accum = 32'sd0;
          for (dim_idx = 0; dim_idx < {head_dim}; dim_idx = dim_idx + 1) begin
            score_accum = score_accum
                + $signed(derive_q8(load_seed, load_command_id, 17, 0, dim_idx))
                * $signed(derive_q8(load_seed, load_command_id, 51, row_idx, dim_idx));
            payload_value_matrix[(((row_idx * {value_dim}) + dim_idx) * 8) +: 8]
                <= derive_q8(load_seed, load_command_id, 85, row_idx, dim_idx);
          end
          payload_score_row[(row_idx * {score_bits}) +: {score_bits}] <= score_accum <<< {score_frac_bits};
        end
      end
      if (pop_valid) begin
        payload_valid <= 1'b0;
      end
    end
  end
endmodule
"""


def _consumer_module(
    *,
    module_name: str,
    row_elems: int,
    value_dim: int,
    score_bits: int,
    weight_bits: int,
    input_frac_bits: int,
    exp_bucket_shift: int,
) -> str:
    score_width = row_elems * score_bits
    weight_width = row_elems * weight_bits
    value_matrix_width = row_elems * value_dim * 8
    result_value_width = value_dim * 40
    max_bucket = 8 << (input_frac_bits - exp_bucket_shift)
    bucket_scale = float(1 << exp_bucket_shift) / float(1 << input_frac_bits)
    exp_entries = [
        (bucket, max(1, int(math.exp(-(bucket * bucket_scale)) * ((1 << weight_bits) - 1) + 0.5)))
        for bucket in range(max_bucket + 1)
    ]
    exp_cases = "\n".join(
        f"      32'd{bucket}: exp_lut = 16'd{value};" for bucket, value in exp_entries
    )
    return f"""module {module_name} (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         load_valid,
    input  wire [15:0]                  load_command_id,
    input  wire [{score_width - 1}:0]   load_score_row,
    input  wire [{value_matrix_width - 1}:0] load_value_matrix,
    input  wire                         pop_valid,
    output reg                          result_valid,
    output reg  [15:0]                  result_command_id,
    output reg  [{score_width - 1}:0]   result_score_row,
    output reg  [{weight_width - 1}:0]  result_weights,
    output reg  [{result_value_width - 1}:0] result_value
);
  integer row_idx;
  integer dim_idx;
  integer sum_exp;
  reg signed [31:0] max_score;
  reg signed [31:0] score_lane;
  reg signed [31:0] delta_score;
  reg [31:0] exp_bucket;
  reg [33:0] weight_numer;
  reg [15:0] exp_weight [0:{row_elems - 1}];
  reg [15:0] weight_lane [0:{row_elems - 1}];
  reg signed [7:0] value_lane;
  reg signed [39:0] accum_lane;

  function automatic [15:0] exp_lut;
    input [31:0] bucket;
    begin
      case (bucket)
{exp_cases}
      default: exp_lut = 16'd1;
      endcase
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result_valid <= 1'b0;
      result_command_id <= 16'h0;
      result_score_row <= {{{score_width}{{1'b0}}}};
      result_weights <= {{{weight_width}{{1'b0}}}};
      result_value <= {{{result_value_width}{{1'b0}}}};
    end else begin
      if (load_valid) begin
        result_valid <= 1'b1;
        result_command_id <= load_command_id;
        result_score_row <= load_score_row;

        max_score = $signed(load_score_row[0 +: {score_bits}]);
        for (row_idx = 1; row_idx < {row_elems}; row_idx = row_idx + 1) begin
          score_lane = $signed(load_score_row[(row_idx * {score_bits}) +: {score_bits}]);
          if (score_lane > max_score) begin
            max_score = score_lane;
          end
        end

        sum_exp = 0;
        for (row_idx = 0; row_idx < {row_elems}; row_idx = row_idx + 1) begin
          score_lane = $signed(load_score_row[(row_idx * {score_bits}) +: {score_bits}]);
          delta_score = max_score - score_lane;
          if (delta_score < 0) begin
            delta_score = 32'sd0;
          end
          exp_bucket = (delta_score + 32'd{1 << (exp_bucket_shift - 1)}) >> {exp_bucket_shift};
          if (exp_bucket > 32'd{max_bucket}) begin
            exp_bucket = 32'd{max_bucket};
          end
          exp_weight[row_idx] = exp_lut(exp_bucket);
          sum_exp = sum_exp + exp_weight[row_idx];
        end

        for (row_idx = 0; row_idx < {row_elems}; row_idx = row_idx + 1) begin
          if (sum_exp != 0) begin
            weight_numer = ({{1'b0, exp_weight[row_idx]}} * 17'd{(1 << weight_bits) - 1})
                + (sum_exp >> 1);
            weight_lane[row_idx] = weight_numer / sum_exp;
          end else begin
            weight_lane[row_idx] = 16'd0;
          end
          result_weights[(row_idx * {weight_bits}) +: {weight_bits}] <= weight_lane[row_idx];
        end

        for (dim_idx = 0; dim_idx < {value_dim}; dim_idx = dim_idx + 1) begin
          accum_lane = 40'sd0;
          for (row_idx = 0; row_idx < {row_elems}; row_idx = row_idx + 1) begin
            value_lane = $signed(load_value_matrix[(((row_idx * {value_dim}) + dim_idx) * 8) +: 8]);
            accum_lane = accum_lane + ($signed(value_lane) * $signed({{1'b0, weight_lane[row_idx]}}));
          end
          result_value[(dim_idx * 40) +: 40] <= accum_lane;
        end
      end

      if (pop_valid) begin
        result_valid <= 1'b0;
      end
    end
  end
endmodule
"""


def _top_module(*, top_name: str, params: dict[str, Any]) -> str:
    producer_count = int(params["producer_count"])
    consumer_count = int(params["consumer_count"])
    row_elems = int(params["row_elems"])
    value_dim = int(params["value_dim"])
    score_bits = int(params["score_bits"])
    weight_bits = int(params["weight_bits"])
    producer_idx_bits = _clog2(producer_count)
    consumer_idx_bits = _clog2(consumer_count)
    score_width = row_elems * score_bits
    weight_width = row_elems * weight_bits
    value_matrix_width = row_elems * value_dim * 8
    result_value_width = value_dim * 40
    producer_module = f"{top_name}_producer"
    consumer_module = f"{top_name}_consumer"

    producer_wires: list[str] = []
    producer_insts: list[str] = []
    for idx in range(producer_count):
        producer_wires.extend(
            [
                f"  wire                         producer_{idx}_payload_valid;",
                f"  wire [15:0]                  producer_{idx}_payload_command_id;",
                f"  wire [{score_width - 1}:0]   producer_{idx}_payload_score_row;",
                f"  wire [{value_matrix_width - 1}:0] producer_{idx}_payload_value_matrix;",
                f"  reg                          producer_{idx}_load_valid;",
                f"  reg                          producer_{idx}_pop_valid;",
            ]
        )
        producer_insts.append(
            f"""  {producer_module} #(
    .PRODUCER_INDEX({idx})
  ) u_producer_{idx} (
    .clk(clk),
    .rst_n(rst_n),
    .load_valid(producer_{idx}_load_valid),
    .load_command_id(command_id),
    .load_seed(command_seed),
    .pop_valid(producer_{idx}_pop_valid),
    .payload_valid(producer_{idx}_payload_valid),
    .payload_command_id(producer_{idx}_payload_command_id),
    .payload_score_row(producer_{idx}_payload_score_row),
    .payload_value_matrix(producer_{idx}_payload_value_matrix)
  );"""
        )

    consumer_wires: list[str] = []
    consumer_insts: list[str] = []
    for idx in range(consumer_count):
        consumer_wires.extend(
            [
                f"  wire                         consumer_{idx}_result_valid;",
                f"  wire [15:0]                  consumer_{idx}_result_command_id;",
                f"  wire [{score_width - 1}:0]   consumer_{idx}_result_score_row;",
                f"  wire [{weight_width - 1}:0]  consumer_{idx}_result_weights;",
                f"  wire [{result_value_width - 1}:0] consumer_{idx}_result_value;",
                f"  reg                          consumer_{idx}_load_valid;",
                f"  reg                          consumer_{idx}_pop_valid;",
                f"  reg  [15:0]                  consumer_{idx}_load_command_id;",
                f"  reg  [{score_width - 1}:0]   consumer_{idx}_load_score_row;",
                f"  reg  [{value_matrix_width - 1}:0] consumer_{idx}_load_value_matrix;",
            ]
        )
        consumer_insts.append(
            f"""  {consumer_module} u_consumer_{idx} (
    .clk(clk),
    .rst_n(rst_n),
    .load_valid(consumer_{idx}_load_valid),
    .load_command_id(consumer_{idx}_load_command_id),
    .load_score_row(consumer_{idx}_load_score_row),
    .load_value_matrix(consumer_{idx}_load_value_matrix),
    .pop_valid(consumer_{idx}_pop_valid),
    .result_valid(consumer_{idx}_result_valid),
    .result_command_id(consumer_{idx}_result_command_id),
    .result_score_row(consumer_{idx}_result_score_row),
    .result_weights(consumer_{idx}_result_weights),
    .result_value(consumer_{idx}_result_value)
  );"""
        )

    return f"""// Auto-generated by npu/rtlgen/gen_attention_separated_cluster.py
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         command_valid,
    output wire                         command_ready,
    input  wire [15:0]                  command_id,
    input  wire [31:0]                  command_seed,
    input  wire [{consumer_count - 1}:0] consumer_enable,
    output reg                          result_valid,
    input  wire                         result_ready,
    output reg  [15:0]                  result_command_id,
    output reg  [{score_width - 1}:0]   result_score_row,
    output reg  [{weight_width - 1}:0]  result_weights,
    output reg  [{result_value_width - 1}:0] result_value,
    output reg  [31:0]                  accepted_count,
    output reg  [31:0]                  completed_count
);
  localparam integer PRODUCER_COUNT = {producer_count};
  localparam integer CONSUMER_COUNT = {consumer_count};
  localparam integer SCORE_ROW_WIDTH = {score_width};
  localparam integer WEIGHT_ROW_WIDTH = {weight_width};
  localparam integer VALUE_MATRIX_WIDTH = {value_matrix_width};
  localparam integer RESULT_VALUE_WIDTH = {result_value_width};

  reg [{producer_idx_bits - 1}:0] issue_rr_ptr;
  reg [{producer_idx_bits - 1}:0] dispatch_producer_rr_ptr;
  reg [{consumer_idx_bits - 1}:0] dispatch_consumer_rr_ptr;
  reg [{consumer_idx_bits - 1}:0] result_rr_ptr;
  reg issue_target_valid;
  reg [{producer_idx_bits - 1}:0] issue_target_idx;
  reg dispatch_producer_valid;
  reg [{producer_idx_bits - 1}:0] dispatch_producer_idx;
  reg dispatch_consumer_valid;
  reg [{consumer_idx_bits - 1}:0] dispatch_consumer_idx;
  reg result_target_valid;
  reg [{consumer_idx_bits - 1}:0] result_target_idx;
  integer issue_scan_offset;
  integer issue_scan_index;
  integer dispatch_producer_scan_offset;
  integer dispatch_producer_scan_index;
  integer dispatch_consumer_scan_offset;
  integer dispatch_consumer_scan_index;
  integer result_scan_offset;
  integer result_scan_index;

  wire command_fire = command_valid && command_ready;
  wire dispatch_fire = dispatch_producer_valid && dispatch_consumer_valid;
  wire result_fire = result_target_valid && result_ready;

{chr(10).join(producer_wires)}
{chr(10).join(consumer_wires)}

  assign command_ready = issue_target_valid;

{chr(10).join(producer_insts)}

{chr(10).join(consumer_insts)}

  always @(*) begin
    issue_target_valid = 1'b0;
    issue_target_idx = {{{producer_idx_bits}{{1'b0}}}};
    for (issue_scan_offset = 0; issue_scan_offset < PRODUCER_COUNT; issue_scan_offset = issue_scan_offset + 1) begin
      issue_scan_index = issue_rr_ptr + issue_scan_offset;
      if (issue_scan_index >= PRODUCER_COUNT) begin
        issue_scan_index = issue_scan_index - PRODUCER_COUNT;
      end
      case (issue_scan_index)
{_producer_issue_cases(producer_count)}
      endcase
    end
  end

  always @(*) begin
    dispatch_producer_valid = 1'b0;
    dispatch_producer_idx = {{{producer_idx_bits}{{1'b0}}}};
    for (
      dispatch_producer_scan_offset = 0;
      dispatch_producer_scan_offset < PRODUCER_COUNT;
      dispatch_producer_scan_offset = dispatch_producer_scan_offset + 1
    ) begin
      dispatch_producer_scan_index = dispatch_producer_rr_ptr + dispatch_producer_scan_offset;
      if (dispatch_producer_scan_index >= PRODUCER_COUNT) begin
        dispatch_producer_scan_index = dispatch_producer_scan_index - PRODUCER_COUNT;
      end
      case (dispatch_producer_scan_index)
{_producer_dispatch_cases(producer_count)}
      endcase
    end
  end

  always @(*) begin
    dispatch_consumer_valid = 1'b0;
    dispatch_consumer_idx = {{{consumer_idx_bits}{{1'b0}}}};
    for (
      dispatch_consumer_scan_offset = 0;
      dispatch_consumer_scan_offset < CONSUMER_COUNT;
      dispatch_consumer_scan_offset = dispatch_consumer_scan_offset + 1
    ) begin
      dispatch_consumer_scan_index = dispatch_consumer_rr_ptr + dispatch_consumer_scan_offset;
      if (dispatch_consumer_scan_index >= CONSUMER_COUNT) begin
        dispatch_consumer_scan_index = dispatch_consumer_scan_index - CONSUMER_COUNT;
      end
      case (dispatch_consumer_scan_index)
{_consumer_dispatch_cases(consumer_count)}
      endcase
    end
  end

  always @(*) begin
    result_target_valid = 1'b0;
    result_target_idx = {{{consumer_idx_bits}{{1'b0}}}};
    for (result_scan_offset = 0; result_scan_offset < CONSUMER_COUNT; result_scan_offset = result_scan_offset + 1) begin
      result_scan_index = result_rr_ptr + result_scan_offset;
      if (result_scan_index >= CONSUMER_COUNT) begin
        result_scan_index = result_scan_index - CONSUMER_COUNT;
      end
      case (result_scan_index)
{_consumer_result_cases(consumer_count)}
      endcase
    end
  end

  always @(*) begin
{_control_defaults(producer_count, consumer_count, score_width, value_matrix_width)}
    if (command_fire) begin
      case (issue_target_idx)
{_producer_load_cases(producer_count)}
      endcase
    end
    if (dispatch_fire) begin
      case (dispatch_producer_idx)
{_producer_pop_cases(producer_count)}
      endcase
      case (dispatch_consumer_idx)
{_consumer_load_cases(producer_count, consumer_count)}
      endcase
    end
    if (result_fire) begin
      case (result_target_idx)
{_consumer_pop_cases(consumer_count)}
      endcase
    end
  end

  always @(*) begin
    result_valid = result_target_valid;
    result_command_id = 16'h0;
    result_score_row = {{SCORE_ROW_WIDTH{{1'b0}}}};
    result_weights = {{WEIGHT_ROW_WIDTH{{1'b0}}}};
    result_value = {{RESULT_VALUE_WIDTH{{1'b0}}}};
    if (result_target_valid) begin
      case (result_target_idx)
{_result_mux_cases(consumer_count)}
      endcase
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      issue_rr_ptr <= {{{producer_idx_bits}{{1'b0}}}};
      dispatch_producer_rr_ptr <= {{{producer_idx_bits}{{1'b0}}}};
      dispatch_consumer_rr_ptr <= {{{consumer_idx_bits}{{1'b0}}}};
      result_rr_ptr <= {{{consumer_idx_bits}{{1'b0}}}};
      accepted_count <= 32'h0;
      completed_count <= 32'h0;
    end else begin
      if (command_fire) begin
        accepted_count <= accepted_count + 32'h1;
        if (issue_target_idx == PRODUCER_COUNT - 1) begin
          issue_rr_ptr <= {{{producer_idx_bits}{{1'b0}}}};
        end else begin
          issue_rr_ptr <= issue_target_idx + 1'b1;
        end
      end
      if (dispatch_fire) begin
        if (dispatch_producer_idx == PRODUCER_COUNT - 1) begin
          dispatch_producer_rr_ptr <= {{{producer_idx_bits}{{1'b0}}}};
        end else begin
          dispatch_producer_rr_ptr <= dispatch_producer_idx + 1'b1;
        end
        if (dispatch_consumer_idx == CONSUMER_COUNT - 1) begin
          dispatch_consumer_rr_ptr <= {{{consumer_idx_bits}{{1'b0}}}};
        end else begin
          dispatch_consumer_rr_ptr <= dispatch_consumer_idx + 1'b1;
        end
      end
      if (result_fire) begin
        completed_count <= completed_count + 32'h1;
        if (result_target_idx == CONSUMER_COUNT - 1) begin
          result_rr_ptr <= {{{consumer_idx_bits}{{1'b0}}}};
        end else begin
          result_rr_ptr <= result_target_idx + 1'b1;
        end
      end
    end
  end
endmodule
"""


def _producer_issue_cases(producer_count: int) -> str:
    cases: list[str] = []
    for idx in range(producer_count):
        cases.append(
            f"""        {idx}: begin
          if (!issue_target_valid && !producer_{idx}_payload_valid) begin
            issue_target_valid = 1'b1;
            issue_target_idx = {idx};
          end
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _producer_dispatch_cases(producer_count: int) -> str:
    cases: list[str] = []
    for idx in range(producer_count):
        cases.append(
            f"""        {idx}: begin
          if (!dispatch_producer_valid && producer_{idx}_payload_valid) begin
            dispatch_producer_valid = 1'b1;
            dispatch_producer_idx = {idx};
          end
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _consumer_dispatch_cases(consumer_count: int) -> str:
    cases: list[str] = []
    for idx in range(consumer_count):
        cases.append(
            f"""        {idx}: begin
          if (!dispatch_consumer_valid && consumer_enable[{idx}] && !consumer_{idx}_result_valid) begin
            dispatch_consumer_valid = 1'b1;
            dispatch_consumer_idx = {idx};
          end
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _consumer_result_cases(consumer_count: int) -> str:
    cases: list[str] = []
    for idx in range(consumer_count):
        cases.append(
            f"""        {idx}: begin
          if (!result_target_valid && consumer_{idx}_result_valid) begin
            result_target_valid = 1'b1;
            result_target_idx = {idx};
          end
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _control_defaults(
    producer_count: int,
    consumer_count: int,
    score_width: int,
    value_matrix_width: int,
) -> str:
    lines: list[str] = []
    for idx in range(producer_count):
        lines.append(f"    producer_{idx}_load_valid = 1'b0;")
        lines.append(f"    producer_{idx}_pop_valid = 1'b0;")
    for idx in range(consumer_count):
        lines.extend(
            [
                f"    consumer_{idx}_load_valid = 1'b0;",
                f"    consumer_{idx}_pop_valid = 1'b0;",
                f"    consumer_{idx}_load_command_id = 16'h0;",
                f"    consumer_{idx}_load_score_row = {score_width}'h0;",
                f"    consumer_{idx}_load_value_matrix = {value_matrix_width}'h0;",
            ]
        )
    return "\n".join(lines)


def _producer_load_cases(producer_count: int) -> str:
    cases: list[str] = []
    for idx in range(producer_count):
        cases.append(
            f"""        {idx}: begin
          producer_{idx}_load_valid = 1'b1;
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _producer_pop_cases(producer_count: int) -> str:
    cases: list[str] = []
    for idx in range(producer_count):
        cases.append(
            f"""        {idx}: begin
          producer_{idx}_pop_valid = 1'b1;
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _consumer_load_cases(producer_count: int, consumer_count: int) -> str:
    cases: list[str] = []
    for c_idx in range(consumer_count):
        cases.append(
            f"""        {c_idx}: begin
          consumer_{c_idx}_load_valid = 1'b1;
          case (dispatch_producer_idx)
{_consumer_load_from_producer_cases(producer_count, c_idx)}
          endcase
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _consumer_load_from_producer_cases(producer_count: int, c_idx: int) -> str:
    cases: list[str] = []
    for p_idx in range(producer_count):
        cases.append(
            f"""            {p_idx}: begin
              consumer_{c_idx}_load_command_id = producer_{p_idx}_payload_command_id;
              consumer_{c_idx}_load_score_row = producer_{p_idx}_payload_score_row;
              consumer_{c_idx}_load_value_matrix = producer_{p_idx}_payload_value_matrix;
            end"""
        )
    cases.append("            default: begin end")
    return "\n".join(cases)


def _consumer_pop_cases(consumer_count: int) -> str:
    cases: list[str] = []
    for idx in range(consumer_count):
        cases.append(
            f"""        {idx}: begin
          consumer_{idx}_pop_valid = 1'b1;
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _result_mux_cases(consumer_count: int) -> str:
    cases: list[str] = []
    for idx in range(consumer_count):
        cases.append(
            f"""        {idx}: begin
          result_command_id = consumer_{idx}_result_command_id;
          result_score_row = consumer_{idx}_result_score_row;
          result_weights = consumer_{idx}_result_weights;
          result_value = consumer_{idx}_result_value;
        end"""
        )
    cases.append("        default: begin end")
    return "\n".join(cases)


def _write_top(*, cfg: dict[str, Any], comp: dict[str, Any], out_path: Path) -> None:
    top_name = str(cfg["top_name"]).strip()
    score_width = int(comp["row_elems"]) * int(comp["score_bits"])
    weight_width = int(comp["row_elems"]) * int(comp["weight_bits"])
    value_matrix_width = int(comp["row_elems"]) * int(comp["value_dim"]) * 8
    result_value_width = int(comp["value_dim"]) * 40
    producer_module = _producer_module(
        module_name=f"{top_name}_producer",
        row_elems=int(comp["row_elems"]),
        head_dim=int(comp["head_dim"]),
        value_dim=int(comp["value_dim"]),
        score_bits=int(comp["score_bits"]),
        score_frac_bits=int(comp["exp_bucket_shift"]),
    )
    consumer_module = _consumer_module(
        module_name=f"{top_name}_consumer",
        row_elems=int(comp["row_elems"]),
        value_dim=int(comp["value_dim"]),
        score_bits=int(comp["score_bits"]),
        weight_bits=int(comp["weight_bits"]),
        input_frac_bits=int(comp["input_frac_bits"]),
        exp_bucket_shift=int(comp["exp_bucket_shift"]),
    )
    top_module = _top_module(top_name=top_name, params=comp)

    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "top.v").write_text(
        "\n\n".join([producer_module, consumer_module, top_module]) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "version": 0.1,
        "generator": "npu/rtlgen/gen_attention_separated_cluster.py",
        "top_name": top_name,
        "semantic_profile": SEMANTIC_PROFILE,
        "producer_count": int(comp["producer_count"]),
        "consumer_count": int(comp["consumer_count"]),
        "row_elems": int(comp["row_elems"]),
        "head_dim": int(comp["head_dim"]),
        "value_dim": int(comp["value_dim"]),
        "score_bits": int(comp["score_bits"]),
        "weight_bits": int(comp["weight_bits"]),
        "input_frac_bits": int(comp["input_frac_bits"]),
        "exp_bucket_shift": int(comp["exp_bucket_shift"]),
        "producer_to_consumer_ratio": f"{int(comp['producer_count'])}:{int(comp['consumer_count'])}",
        "producer_queue_depth": 1,
        "consumer_queue_depth": 1,
        "producer_payload_width": 16 + score_width + value_matrix_width,
        "consumer_result_width": 16 + score_width + weight_width + result_value_width,
        "payload_width_bits": {
            "producer_score_row": score_width,
            "producer_value_matrix": value_matrix_width,
            "consumer_weights": weight_width,
            "consumer_value": result_value_width,
        },
        "arbitration": {
            "command_to_producer": "deterministic round-robin across free producers",
            "producer_to_consumer": "deterministic round-robin producer scan and enabled-free consumer scan",
            "consumer_to_result": "deterministic round-robin across valid consumers",
        },
        "stage_outputs": {
            "producer": ["payload_command_id", "payload_score_row", "payload_value_matrix"],
            "consumer": ["result_command_id", "result_score_row", "result_weights", "result_value"],
            "top": ["result_command_id", "result_score_row", "result_weights", "result_value"],
        },
        "score_contract": {
            "representation": "8 signed Q28 score lanes from exact 8-term q8*k8 dot products with fixed 1/256 dequantization scale",
            "softmax": "bucketed exp LUT with exact normalized divide",
            "value_accumulation": "8 signed q8 value dimensions accumulated with unsigned q16 weights into signed 40-bit sums",
        },
        "ppa_stimulus": {
            "mode": "seeded_internal_input_expansion",
            "purpose": "keep all QK and V lanes observable through a narrow registered macro boundary",
            "cost_caveat": "small seed-mix XOR logic is harness overhead and must be reported separately from MAC/softmax/value scaling",
        },
    }
    (out_path / "attention_separated_cluster_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_path / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = _load_json(Path(args.config))
    comp = _validate(cfg)
    _write_top(cfg=cfg, comp=comp, out_path=Path(args.out))
    print(f"attention-separated-cluster: wrote RTL to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
