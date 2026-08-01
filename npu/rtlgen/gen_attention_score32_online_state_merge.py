#!/usr/bin/env python3
"""Generate a folded pairwise ready/valid merge stage for exact score32 partial state."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FACTORED_H33_L64_MUL_EXACT = "factored_h33_l64_mul_exact"
LEGACY_MONOLITHIC_LUT_EXACT = "legacy_monolithic_lut_exact"
SEGMENTED_LUT_9X256_EXACT = "segmented_lut_9x256_exact"

MERGE_SCALE_BITS = 24
MERGE_SCALE = (1 << MERGE_SCALE_BITS) - 1
EXP_BUCKET_SHIFT = 20
PARTIAL_VALUE_BITS = 328
NUMERATOR_BITS = 41
EXP_SUM_BITS = 33
LANE_COUNT = 8
MAX_EXP_BUCKET = 8 << (28 - EXP_BUCKET_SHIFT)
EXP_SCALE_SEGMENT_SHIFT = 8
EXP_SCALE_SEGMENT_SIZE = 1 << EXP_SCALE_SEGMENT_SHIFT
EXP_SCALE_SEGMENT_COUNT = (MAX_EXP_BUCKET // EXP_SCALE_SEGMENT_SIZE) + 1
PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES = 19
PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES = 18
PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES = 20
PAIR_EXP_SUM_SCALE_CYCLES = 2
PAIR_NUMERATOR_SCALE_CYCLES = 16
_SUPPORTED_EXP_SCALE_IMPLS = {
    LEGACY_MONOLITHIC_LUT_EXACT,
    SEGMENTED_LUT_9X256_EXACT,
    FACTORED_H33_L64_MUL_EXACT,
}
EXP_FACTOR_STEP = 64
EXP_FACTOR_HIGH_BITS = 13
EXP_FACTOR_LOW_BITS = 30
EXP_FACTOR_ROUND_SHIFT = EXP_FACTOR_HIGH_BITS + EXP_FACTOR_LOW_BITS
EXP_FACTOR_ROUND_BIAS = 1 << (EXP_FACTOR_ROUND_SHIFT - 1)
EXP_FACTOR_HIGH_ENTRIES = (MAX_EXP_BUCKET // EXP_FACTOR_STEP) + 1
EXP_FACTOR_LOW_ENTRIES = EXP_FACTOR_STEP


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(config: dict[str, Any]) -> dict[str, int | str]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_online_state_merge")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_online_state_merge")
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    exp_scale_impl = str(body.get("exp_scale_impl", FACTORED_H33_L64_MUL_EXACT)).strip()
    lane_parallelism = int(body.get("lane_parallelism", 1))
    if value_slices < 1 or value_slices > 16 or value_slices & (value_slices - 1):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if exp_scale_impl not in _SUPPORTED_EXP_SCALE_IMPLS:
        supported = ", ".join(sorted(_SUPPORTED_EXP_SCALE_IMPLS))
        raise SystemExit(f"exp_scale_impl must be one of: {supported}")
    if lane_parallelism != 1:
        raise SystemExit("lane_parallelism must be 1 for the shared single-scale exact pair merge")
    body.update(
        {
            "value_slices": value_slices,
            "head_id_bits": head_id_bits,
            "exp_scale_impl": exp_scale_impl,
            "lane_parallelism": lane_parallelism,
        }
    )
    return {
        "top_name": top_name,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "exp_scale_impl": exp_scale_impl,
        "lane_parallelism": lane_parallelism,
    }


def exact_exp_scale_value(bucket: int) -> int:
    if bucket < 0 or bucket > MAX_EXP_BUCKET:
        return 0
    return max(1, int(math.exp(-(bucket / 256.0)) * MERGE_SCALE + 0.5))


def _merge_scale_cases(*, start: int, stop: int, assign_target: str) -> str:
    return "\n".join(
        f"      8'd{bucket - start}: {assign_target} = 24'd{exact_exp_scale_value(bucket)};" for bucket in range(start, stop)
    )


def _exp_lut_functions() -> str:
    if EXP_SCALE_SEGMENT_COUNT != 9:
        raise AssertionError("segmented exact exp-scale implementation assumes 9 segments")
    blocks: list[str] = []
    for segment in range(EXP_SCALE_SEGMENT_COUNT):
        start = segment * EXP_SCALE_SEGMENT_SIZE
        stop = min(MAX_EXP_BUCKET + 1, start + EXP_SCALE_SEGMENT_SIZE)
        blocks.append(
            f"""  function automatic [23:0] exp_lut_segment_{segment};
    input [7:0] offset;
    begin
      case (offset)
{_merge_scale_cases(start=start, stop=stop, assign_target=f"exp_lut_segment_{segment}")}
      default: exp_lut_segment_{segment} = 24'd0;
      endcase
    end
  endfunction"""
        )
    return "\n\n".join(blocks)


def _factored_high_value(index: int) -> int:
    return int(math.exp(-((index * EXP_FACTOR_STEP) / 256.0)) * MERGE_SCALE * (1 << EXP_FACTOR_HIGH_BITS) + 0.5)


def _factored_low_value(index: int) -> int:
    return int(math.exp(-(index / 256.0)) * (1 << EXP_FACTOR_LOW_BITS) + 0.5)


def _factored_high_cases() -> str:
    return "\n".join(
        f"      6'd{index}: exp_lut_high = 37'd{_factored_high_value(index)};" for index in range(EXP_FACTOR_HIGH_ENTRIES)
    )


def _factored_low_cases() -> str:
    return "\n".join(
        f"      6'd{index}: exp_lut_low = 31'd{_factored_low_value(index)};" for index in range(EXP_FACTOR_LOW_ENTRIES)
    )


def _exp_lut_function(*, exp_scale_impl: str) -> str:
    if exp_scale_impl == LEGACY_MONOLITHIC_LUT_EXACT:
        cases = "\n".join(
            f"      33'd{bucket}: exp_lut = 24'd{exact_exp_scale_value(bucket)};" for bucket in range(MAX_EXP_BUCKET + 1)
        )
        return f"""  function automatic [23:0] exp_lut;
    input [32:0] bucket;
    begin
      case (bucket)
{cases}
      default: exp_lut = 24'd0;
      endcase
    end
  endfunction"""
    if exp_scale_impl == FACTORED_H33_L64_MUL_EXACT:
        return f"""  function automatic [36:0] exp_lut_high;
    input [5:0] bucket_hi;
    begin
      case (bucket_hi)
{_factored_high_cases()}
      default: exp_lut_high = 37'd0;
      endcase
    end
  endfunction

  function automatic [30:0] exp_lut_low;
    input [5:0] bucket_lo;
    begin
      case (bucket_lo)
{_factored_low_cases()}
      default: exp_lut_low = 31'd0;
      endcase
    end
  endfunction

  function automatic [23:0] exp_lut;
    input [32:0] bucket;
    reg [36:0] high_scale;
    reg [30:0] low_scale;
    reg [67:0] product;
    reg [67:0] rounded_product;
    begin
      if (bucket > 33'd{MAX_EXP_BUCKET}) begin
        exp_lut = 24'd0;
      end else begin
        if (bucket == 33'd{MAX_EXP_BUCKET}) begin
          high_scale = exp_lut_high(6'd32);
          low_scale = exp_lut_low(6'd0);
        end else begin
          high_scale = exp_lut_high(bucket[10:6]);
          low_scale = exp_lut_low(bucket[5:0]);
        end
        product = high_scale * low_scale;
        rounded_product = product + 68'd{EXP_FACTOR_ROUND_BIAS};
        exp_lut = rounded_product >> {EXP_FACTOR_ROUND_SHIFT};
      end
    end
  endfunction"""
    if exp_scale_impl != SEGMENTED_LUT_9X256_EXACT:
        raise AssertionError(f"unsupported exp_scale_impl: {exp_scale_impl}")
    return (
        _exp_lut_functions()
        + f"""

  function automatic [23:0] exp_lut;
    input [32:0] bucket;
    begin
      if (bucket > 33'd{MAX_EXP_BUCKET}) begin
        exp_lut = 24'd0;
      end else if (bucket == 33'd{MAX_EXP_BUCKET}) begin
        exp_lut = exp_lut_segment_8(8'd0);
      end else begin
        case (bucket[10:8])
          3'd0: exp_lut = exp_lut_segment_0(bucket[7:0]);
          3'd1: exp_lut = exp_lut_segment_1(bucket[7:0]);
          3'd2: exp_lut = exp_lut_segment_2(bucket[7:0]);
          3'd3: exp_lut = exp_lut_segment_3(bucket[7:0]);
          3'd4: exp_lut = exp_lut_segment_4(bucket[7:0]);
          3'd5: exp_lut = exp_lut_segment_5(bucket[7:0]);
          3'd6: exp_lut = exp_lut_segment_6(bucket[7:0]);
          3'd7: exp_lut = exp_lut_segment_7(bucket[7:0]);
          default: exp_lut = 24'd0;
        endcase
      end
    end
  endfunction"""
    )


def _lane_read_cases() -> str:
    return "\n".join(
        f"      3'd{lane}: lane_read41 = $signed(word_in[{lane * NUMERATOR_BITS} +: {NUMERATOR_BITS}]);"
        for lane in range(LANE_COUNT)
    )


def _lane_write_cases() -> str:
    lines = []
    for lane in range(LANE_COUNT):
        lines.append(f"      3'd{lane}: begin")
        lines.append(f"        lane_write41[{lane * NUMERATOR_BITS} +: {NUMERATOR_BITS}] = lane_value;")
        lines.append("      end")
    return "\n".join(lines)


def _top(*, top_name: str, value_slices: int, head_id_bits: int, exp_scale_impl: str) -> str:
    slice_bits = _clog2(value_slices)
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_online_state_merge.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         left_valid,
    output wire         left_ready,
    input  wire [15:0]  left_command_id,
    input  wire [{head_id_bits - 1}:0] left_head_id,
    input  wire signed [31:0] left_global_max,
    input  wire [32:0]  left_exp_sum,
    input  wire [{slice_bits - 1}:0] left_slice,
    input  wire         left_last,
    input  wire [327:0] left_value,
    input  wire         right_valid,
    output wire         right_ready,
    input  wire [15:0]  right_command_id,
    input  wire [{head_id_bits - 1}:0] right_head_id,
    input  wire signed [31:0] right_global_max,
    input  wire [32:0]  right_exp_sum,
    input  wire [{slice_bits - 1}:0] right_slice,
    input  wire         right_last,
    input  wire [327:0] right_value,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_command_id,
    output wire [{head_id_bits - 1}:0] out_head_id,
    output wire signed [31:0] out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [{slice_bits - 1}:0] out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output reg  [31:0]  completed_count,
    output reg  [31:0]  cycle_count,
    output wire         protocol_error
);
  localparam integer VALUE_SLICES = {value_slices};
  localparam integer HEAD_ID_BITS = {head_id_bits};
  localparam integer LANE_COUNT = {LANE_COUNT};
  localparam [{slice_bits - 1}:0] LAST_SLICE = {slice_bits}'d{value_slices - 1};
  localparam integer EXP_SCALE_BUCKET_MAX = {MAX_EXP_BUCKET};
  localparam integer EXP_SCALE_SEGMENT_SHIFT = {EXP_SCALE_SEGMENT_SHIFT};
  localparam integer EXP_SCALE_SEGMENT_SIZE = {EXP_SCALE_SEGMENT_SIZE};
  localparam integer EXP_SCALE_SEGMENT_COUNT = {EXP_SCALE_SEGMENT_COUNT};
  localparam [2:0] PHASE_IDLE = 3'd0;
  localparam [2:0] PHASE_EXP_SUM_LEFT = 3'd1;
  localparam [2:0] PHASE_EXP_SUM_RIGHT = 3'd2;
  localparam [2:0] PHASE_LANE_LEFT = 3'd3;
  localparam [2:0] PHASE_LANE_RIGHT = 3'd4;

  reg left_hold_valid_q;
  reg [15:0] left_command_id_hold_q;
  reg [HEAD_ID_BITS-1:0] left_head_id_hold_q;
  reg signed [31:0] left_global_max_hold_q;
  reg [32:0] left_exp_sum_hold_q;
  reg [{slice_bits - 1}:0] left_slice_hold_q;
  reg left_last_hold_q;
  reg [327:0] left_value_hold_q;

  reg right_hold_valid_q;
  reg [15:0] right_command_id_hold_q;
  reg [HEAD_ID_BITS-1:0] right_head_id_hold_q;
  reg signed [31:0] right_global_max_hold_q;
  reg [32:0] right_exp_sum_hold_q;
  reg [{slice_bits - 1}:0] right_slice_hold_q;
  reg right_last_hold_q;
  reg [327:0] right_value_hold_q;

  reg [2:0] phase_q;
  reg [15:0] active_command_id_q;
  reg [HEAD_ID_BITS-1:0] active_head_id_q;
  reg [{slice_bits - 1}:0] active_slice_q;
  reg active_last_q;
  reg signed [31:0] active_global_max_q;
  reg [23:0] active_left_scale_q;
  reg [23:0] active_right_scale_q;
  reg [32:0] active_left_exp_sum_q;
  reg [32:0] active_right_exp_sum_q;
  reg [32:0] active_scaled_left_exp_sum_q;
  reg [32:0] active_merged_exp_sum_q;
  reg [327:0] active_left_value_q;
  reg [327:0] active_right_value_q;
  reg [327:0] active_merged_value_q;
  reg [2:0] active_lane_index_q;
  reg signed [40:0] active_scaled_left_lane_q;

  reg out_valid_q;
  reg [15:0] out_command_id_q;
  reg [HEAD_ID_BITS-1:0] out_head_id_q;
  reg signed [31:0] out_global_max_q;
  reg [32:0] out_exp_sum_q;
  reg [{slice_bits - 1}:0] out_slice_q;
  reg out_last_q;
  reg [327:0] out_value_q;

  reg protocol_error_q;
  reg signed [32:0] left_delta_r;
  reg signed [32:0] right_delta_r;
  reg [32:0] left_delta_clamped_r;
  reg [32:0] right_delta_clamped_r;
  reg [32:0] left_bucket_r;
  reg [32:0] right_bucket_r;
  reg [23:0] left_scale_r;
  reg [23:0] right_scale_r;
  reg signed [31:0] merged_global_max_r;
  reg signed [40:0] lane_right_r;
  reg signed [40:0] lane_merged_r;
  reg [327:0] merged_value_next_r;

  wire left_last_semantic_error = left_last_hold_q != (left_slice_hold_q == LAST_SLICE);
  wire right_last_semantic_error = right_last_hold_q != (right_slice_hold_q == LAST_SLICE);
  wire pair_protocol_error =
      left_command_id_hold_q != right_command_id_hold_q
      || left_head_id_hold_q != right_head_id_hold_q
      || left_slice_hold_q != right_slice_hold_q
      || left_last_hold_q != right_last_hold_q
      || left_last_semantic_error
      || right_last_semantic_error;
  wire start_pair = (phase_q == PHASE_IDLE) && !out_valid_q && left_hold_valid_q && right_hold_valid_q;
  wire out_fire = out_valid_q && out_ready;

  assign left_ready = !left_hold_valid_q;
  assign right_ready = !right_hold_valid_q;
  assign out_valid = out_valid_q;
  assign out_command_id = out_command_id_q;
  assign out_head_id = out_head_id_q;
  assign out_global_max = out_global_max_q;
  assign out_exp_sum = out_exp_sum_q;
  assign out_slice = out_slice_q;
  assign out_last = out_last_q;
  assign out_value = out_value_q;
  assign protocol_error = protocol_error_q;

{_exp_lut_function(exp_scale_impl=exp_scale_impl)}

  function automatic [32:0] scale_unsigned33;
    input [32:0] value_in;
    input [23:0] scale_in;
    reg [56:0] product;
    reg [56:0] quotient;
    begin
      if (scale_in == 0 || value_in == 0) begin
        scale_unsigned33 = 33'd0;
      end else begin
        product = (value_in * scale_in) + 57'd{MERGE_SCALE // 2};
        quotient = product / 57'd{MERGE_SCALE};
        if (quotient > 57'd8589934591) scale_unsigned33 = 33'h1ffff_ffff;
        else scale_unsigned33 = quotient[32:0];
      end
    end
  endfunction

  function automatic signed [40:0] scale_signed41;
    input signed [40:0] value_in;
    input [23:0] scale_in;
    reg [40:0] magnitude;
    reg [64:0] product;
    reg [64:0] quotient;
    begin
      if (scale_in == 0 || value_in == 0) begin
        scale_signed41 = 41'sd0;
      end else begin
        magnitude = value_in < 0 ? (~value_in) + 1'b1 : value_in[40:0];
        product = (magnitude * scale_in) + 65'd{MERGE_SCALE // 2};
        quotient = product / 65'd{MERGE_SCALE};
        if (value_in < 0) begin
          if (quotient >= 65'd1099511627776) scale_signed41 = -41'sd1099511627776;
          else scale_signed41 = -$signed(quotient[40:0]);
        end else begin
          if (quotient > 65'd1099511627775) scale_signed41 = 41'sd1099511627775;
          else scale_signed41 = $signed(quotient[40:0]);
        end
      end
    end
  endfunction

  function automatic signed [40:0] sat_add_signed41;
    input signed [40:0] lhs;
    input signed [40:0] rhs;
    reg signed [41:0] sum;
    begin
      sum = lhs + rhs;
      if (sum > 42'sd1099511627775) sat_add_signed41 = 41'sd1099511627775;
      else if (sum < -42'sd1099511627776) sat_add_signed41 = -41'sd1099511627776;
      else sat_add_signed41 = sum[40:0];
    end
  endfunction

  function automatic [32:0] sat_add_unsigned33;
    input [32:0] lhs;
    input [32:0] rhs;
    reg [33:0] sum;
    begin
      sum = lhs + rhs;
      if (sum > 34'd8589934591) sat_add_unsigned33 = 33'h1ffff_ffff;
      else sat_add_unsigned33 = sum[32:0];
    end
  endfunction

  function automatic signed [40:0] lane_read41;
    input [327:0] word_in;
    input [2:0] lane_index;
    begin
      case (lane_index)
{_lane_read_cases()}
      default: lane_read41 = 41'sd0;
      endcase
    end
  endfunction

  function automatic [327:0] lane_write41;
    input [327:0] word_in;
    input [2:0] lane_index;
    input signed [40:0] lane_value;
    begin
      lane_write41 = word_in;
      case (lane_index)
{_lane_write_cases()}
      default: begin
      end
      endcase
    end
  endfunction

  always @(*) begin
    merged_global_max_r = left_global_max_hold_q >= right_global_max_hold_q
        ? left_global_max_hold_q
        : right_global_max_hold_q;
    left_delta_r = $signed({{merged_global_max_r[31], merged_global_max_r}})
        - $signed({{left_global_max_hold_q[31], left_global_max_hold_q}});
    right_delta_r = $signed({{merged_global_max_r[31], merged_global_max_r}})
        - $signed({{right_global_max_hold_q[31], right_global_max_hold_q}});
    left_delta_clamped_r = left_delta_r < 0 ? 33'd0 : left_delta_r[32:0];
    right_delta_clamped_r = right_delta_r < 0 ? 33'd0 : right_delta_r[32:0];
    left_bucket_r = (left_delta_clamped_r + 33'd524288) >> 20;
    right_bucket_r = (right_delta_clamped_r + 33'd524288) >> 20;
    left_scale_r = exp_lut(left_bucket_r);
    right_scale_r = exp_lut(right_bucket_r);
    lane_right_r = lane_read41(active_right_value_q, active_lane_index_q);
    lane_merged_r = sat_add_signed41(active_scaled_left_lane_q, scale_signed41(lane_right_r, active_right_scale_q));
    merged_value_next_r = lane_write41(active_merged_value_q, active_lane_index_q, lane_merged_r);
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      left_hold_valid_q <= 1'b0;
      left_command_id_hold_q <= 16'd0;
      left_head_id_hold_q <= {{HEAD_ID_BITS{{1'b0}}}};
      left_global_max_hold_q <= 32'sd0;
      left_exp_sum_hold_q <= 33'd0;
      left_slice_hold_q <= {slice_bits}'d0;
      left_last_hold_q <= 1'b0;
      left_value_hold_q <= 328'd0;
      right_hold_valid_q <= 1'b0;
      right_command_id_hold_q <= 16'd0;
      right_head_id_hold_q <= {{HEAD_ID_BITS{{1'b0}}}};
      right_global_max_hold_q <= 32'sd0;
      right_exp_sum_hold_q <= 33'd0;
      right_slice_hold_q <= {slice_bits}'d0;
      right_last_hold_q <= 1'b0;
      right_value_hold_q <= 328'd0;
      phase_q <= PHASE_IDLE;
      active_command_id_q <= 16'd0;
      active_head_id_q <= {{HEAD_ID_BITS{{1'b0}}}};
      active_slice_q <= {slice_bits}'d0;
      active_last_q <= 1'b0;
      active_global_max_q <= 32'sd0;
      active_left_scale_q <= 24'd0;
      active_right_scale_q <= 24'd0;
      active_left_exp_sum_q <= 33'd0;
      active_right_exp_sum_q <= 33'd0;
      active_scaled_left_exp_sum_q <= 33'd0;
      active_merged_exp_sum_q <= 33'd0;
      active_left_value_q <= 328'd0;
      active_right_value_q <= 328'd0;
      active_merged_value_q <= 328'd0;
      active_lane_index_q <= 3'd0;
      active_scaled_left_lane_q <= 41'sd0;
      out_valid_q <= 1'b0;
      out_command_id_q <= 16'd0;
      out_head_id_q <= {{HEAD_ID_BITS{{1'b0}}}};
      out_global_max_q <= 32'sd0;
      out_exp_sum_q <= 33'd0;
      out_slice_q <= {slice_bits}'d0;
      out_last_q <= 1'b0;
      out_value_q <= 328'd0;
      protocol_error_q <= 1'b0;
      completed_count <= 32'd0;
      cycle_count <= 32'd0;
    end else begin
      cycle_count <= cycle_count + 1'b1;

      if (out_fire) begin
        out_valid_q <= 1'b0;
        completed_count <= completed_count + 1'b1;
      end

      if (left_valid && left_ready) begin
        left_hold_valid_q <= 1'b1;
        left_command_id_hold_q <= left_command_id;
        left_head_id_hold_q <= left_head_id;
        left_global_max_hold_q <= left_global_max;
        left_exp_sum_hold_q <= left_exp_sum;
        left_slice_hold_q <= left_slice;
        left_last_hold_q <= left_last;
        left_value_hold_q <= left_value;
      end

      if (right_valid && right_ready) begin
        right_hold_valid_q <= 1'b1;
        right_command_id_hold_q <= right_command_id;
        right_head_id_hold_q <= right_head_id;
        right_global_max_hold_q <= right_global_max;
        right_exp_sum_hold_q <= right_exp_sum;
        right_slice_hold_q <= right_slice;
        right_last_hold_q <= right_last;
        right_value_hold_q <= right_value;
      end

      if (start_pair) begin
        if (pair_protocol_error) protocol_error_q <= 1'b1;
        left_hold_valid_q <= 1'b0;
        right_hold_valid_q <= 1'b0;
        phase_q <= PHASE_EXP_SUM_LEFT;
        active_command_id_q <= left_command_id_hold_q;
        active_head_id_q <= left_head_id_hold_q;
        active_slice_q <= left_slice_hold_q;
        active_last_q <= left_last_hold_q;
        active_global_max_q <= merged_global_max_r;
        active_left_scale_q <= left_scale_r;
        active_right_scale_q <= right_scale_r;
        active_left_exp_sum_q <= left_exp_sum_hold_q;
        active_right_exp_sum_q <= right_exp_sum_hold_q;
        active_scaled_left_exp_sum_q <= 33'd0;
        active_merged_exp_sum_q <= 33'd0;
        active_left_value_q <= left_value_hold_q;
        active_right_value_q <= right_value_hold_q;
        active_merged_value_q <= 328'd0;
        active_lane_index_q <= 3'd0;
        active_scaled_left_lane_q <= 41'sd0;
      end else begin
        case (phase_q)
          PHASE_IDLE: begin
          end
          PHASE_EXP_SUM_LEFT: begin
            active_scaled_left_exp_sum_q <= scale_unsigned33(active_left_exp_sum_q, active_left_scale_q);
            phase_q <= PHASE_EXP_SUM_RIGHT;
          end
          PHASE_EXP_SUM_RIGHT: begin
            active_merged_exp_sum_q <= sat_add_unsigned33(
                active_scaled_left_exp_sum_q,
                scale_unsigned33(active_right_exp_sum_q, active_right_scale_q)
            );
            active_lane_index_q <= 3'd0;
            phase_q <= PHASE_LANE_LEFT;
          end
          PHASE_LANE_LEFT: begin
            active_scaled_left_lane_q <= scale_signed41(
                lane_read41(active_left_value_q, active_lane_index_q),
                active_left_scale_q
            );
            phase_q <= PHASE_LANE_RIGHT;
          end
          PHASE_LANE_RIGHT: begin
            active_merged_value_q <= merged_value_next_r;
            if (active_lane_index_q == 3'd7) begin
              out_valid_q <= 1'b1;
              out_command_id_q <= active_command_id_q;
              out_head_id_q <= active_head_id_q;
              out_global_max_q <= active_global_max_q;
              out_exp_sum_q <= active_merged_exp_sum_q;
              out_slice_q <= active_slice_q;
              out_last_q <= active_last_q;
              out_value_q <= merged_value_next_r;
              phase_q <= PHASE_IDLE;
            end else begin
              active_lane_index_q <= active_lane_index_q + 1'b1;
              phase_q <= PHASE_LANE_LEFT;
            end
          end
          default: begin
            phase_q <= PHASE_IDLE;
          end
        endcase
      end
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(
        _top(
            top_name=str(params["top_name"]),
            value_slices=int(params["value_slices"]),
            head_id_bits=int(params["head_id_bits"]),
            exp_scale_impl=str(params["exp_scale_impl"]),
        ),
        encoding="utf-8",
    )
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "version": 1,
        "top_name": params["top_name"],
        "generator": "npu/rtlgen/gen_attention_score32_online_state_merge.py",
        "semantic_profile": "score32_online_exact_partial_pair_merge_v1",
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "partial_payload_bits_per_beat": PARTIAL_VALUE_BITS,
        "result_interface": "ready_valid_exact_partial_slice_stream",
        "equivalence_hash": False,
        "merge_scale_bits": MERGE_SCALE_BITS,
        "exp_scale_impl": str(params["exp_scale_impl"]),
        "exp_scale_bucket_max": MAX_EXP_BUCKET,
        "lane_parallelism": 1,
        "implementation_style": "shared_single_scale_folded_exact_v1",
        "shared_signed_scale_datapaths": 1,
        "shared_unsigned_scale_datapaths": 1,
        "exp_sum_scale_cycles": PAIR_EXP_SUM_SCALE_CYCLES,
        "numerator_scale_cycles": PAIR_NUMERATOR_SCALE_CYCLES,
        "pair_capture_to_output_latency_cycles": PAIR_CAPTURE_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_to_output_latency_cycles": PAIR_COMPUTE_LAUNCH_TO_OUTPUT_LATENCY_CYCLES,
        "pair_compute_launch_interval_cycles": PAIR_COMPUTE_LAUNCH_INTERVAL_CYCLES,
        "input_prefetch_pairs_per_side": 1,
    }
    if str(params["exp_scale_impl"]) == SEGMENTED_LUT_9X256_EXACT:
        manifest.update(
            {
                "exp_scale_segment_shift": EXP_SCALE_SEGMENT_SHIFT,
                "exp_scale_segment_size": EXP_SCALE_SEGMENT_SIZE,
                "exp_scale_segment_count": EXP_SCALE_SEGMENT_COUNT,
            }
        )
    if str(params["exp_scale_impl"]) == FACTORED_H33_L64_MUL_EXACT:
        manifest.update(
            {
                "exp_factor_step": EXP_FACTOR_STEP,
                "exp_factor_high_entries": EXP_FACTOR_HIGH_ENTRIES,
                "exp_factor_low_entries": EXP_FACTOR_LOW_ENTRIES,
                "exp_factor_high_bits": EXP_FACTOR_HIGH_BITS,
                "exp_factor_low_bits": EXP_FACTOR_LOW_BITS,
                "exp_factor_round_shift": EXP_FACTOR_ROUND_SHIFT,
            }
        )
    (out_dir / "attention_score32_online_state_merge_manifest.json").write_text(
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
