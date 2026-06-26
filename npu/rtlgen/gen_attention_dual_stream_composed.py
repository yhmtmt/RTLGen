#!/usr/bin/env python3
"""Generate a composed dual-stream attention datapath harness.

The generated top keeps the external boundary narrow while composing the local
datapath pieces used by the Llama7B mixed-precision dual-stream feasibility
model: two int8 dense compute streams, a shared int8 softmax-weight generator,
two q8/v6 full-value streams, stream buffers, and simple start/done control.
By default the PPA harness exposes datapath outputs directly. Equivalence-only
hash folding can be enabled with attention_dual_stream_composed.equivalence_hash.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _as_bool(config: dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _as_str(config: dict[str, Any], key: str, default: str) -> str:
    return str(config.get(key, default)).strip()


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    comp = cfg.get("attention_dual_stream_composed")
    if not isinstance(comp, dict):
        raise SystemExit("config must contain attention_dual_stream_composed object")
    streams = _as_int(comp, "streams", 2)
    array_m = _as_int(comp, "array_m", 16)
    array_n = _as_int(comp, "array_n", 8)
    k_unroll = _as_int(comp, "k_unroll", 1)
    row_elems = _as_int(comp, "softmax_row_elems", 8)
    value_bits = _as_int(comp, "value_bits", 6)
    value_lanes = _as_int(comp, "value_lanes", 16)
    partials = _as_int(comp, "partials", 8)
    partials_per_cycle = _as_int(comp, "partials_per_cycle", 2)
    stream_buffer_bits = _as_int(comp, "stream_buffer_bits", 1024)
    softmax_pipeline_stages = _as_int(comp, "softmax_pipeline_stages", 0)
    softmax_internal_pipeline_stages = _as_int(comp, "softmax_internal_pipeline_stages", 0)
    softmax_impl = _as_str(comp, "softmax_impl", "exact_div")
    mac_accum_bits = _as_int(comp, "mac_accum_bits", 24)
    softmax_score_bits = _as_int(comp, "softmax_score_bits", 8)
    softmax_weight_bits = _as_int(comp, "softmax_weight_bits", 8)
    softmax_input_frac_bits = _as_int(comp, "softmax_input_frac_bits", 0)
    softmax_reciprocal_lut_bucket_shift = _as_int(comp, "softmax_reciprocal_lut_bucket_shift", 0)
    if streams != 2:
        raise SystemExit("attention_dual_stream_composed.streams must be 2 for the current dual-stream harness")
    if array_m < 1 or array_m > 16:
        raise SystemExit("attention_dual_stream_composed.array_m must be in [1, 16]")
    if array_n < 1 or array_n > 16:
        raise SystemExit("attention_dual_stream_composed.array_n must be in [1, 16]")
    if k_unroll < 1 or k_unroll > 4:
        raise SystemExit("attention_dual_stream_composed.k_unroll must be in [1, 4]")
    if row_elems < 1 or row_elems > 16:
        raise SystemExit("attention_dual_stream_composed.softmax_row_elems must be in [1, 16]")
    if value_bits < 2 or value_bits > 16:
        raise SystemExit("attention_dual_stream_composed.value_bits must be in [2, 16]")
    if value_lanes < 1 or value_lanes > 32:
        raise SystemExit("attention_dual_stream_composed.value_lanes must be in [1, 32]")
    if partials < 1 or partials > 16:
        raise SystemExit("attention_dual_stream_composed.partials must be in [1, 16]")
    if partials_per_cycle < 1 or partials_per_cycle > partials:
        raise SystemExit("attention_dual_stream_composed.partials_per_cycle must be in [1, partials]")
    if stream_buffer_bits < 128 or stream_buffer_bits > 4096:
        raise SystemExit("attention_dual_stream_composed.stream_buffer_bits must be in [128, 4096]")
    if softmax_pipeline_stages < 0 or softmax_pipeline_stages > 1:
        raise SystemExit("attention_dual_stream_composed.softmax_pipeline_stages must be in [0, 1]")
    if softmax_internal_pipeline_stages < 0 or softmax_internal_pipeline_stages > 1:
        raise SystemExit("attention_dual_stream_composed.softmax_internal_pipeline_stages must be in [0, 1]")
    if mac_accum_bits < 24 or mac_accum_bits > 32:
        raise SystemExit("attention_dual_stream_composed.mac_accum_bits must be in [24, 32]")
    if softmax_score_bits < 2 or softmax_score_bits > 32:
        raise SystemExit("attention_dual_stream_composed.softmax_score_bits must be in [2, 32]")
    if softmax_score_bits == 32 and mac_accum_bits != 32:
        raise SystemExit(
            "attention_dual_stream_composed.softmax_score_bits=32 requires mac_accum_bits=32"
        )
    if softmax_score_bits > mac_accum_bits:
        raise SystemExit(
            "attention_dual_stream_composed.softmax_score_bits must be in [2, mac_accum_bits]"
        )
    if softmax_score_bits == 32 and softmax_weight_bits != 16:
        raise SystemExit(
            "attention_dual_stream_composed.softmax_score_bits=32 requires softmax_weight_bits=16 in the current prototype"
        )
    if softmax_weight_bits < 2 or softmax_weight_bits > 24:
        raise SystemExit("attention_dual_stream_composed.softmax_weight_bits must be in [2, 24]")
    if softmax_input_frac_bits < 0 or softmax_input_frac_bits > 16:
        raise SystemExit("attention_dual_stream_composed.softmax_input_frac_bits must be in [0, 16]")
    if softmax_reciprocal_lut_bucket_shift < 0 or softmax_reciprocal_lut_bucket_shift > 12:
        raise SystemExit("attention_dual_stream_composed.softmax_reciprocal_lut_bucket_shift must be in [0, 12]")
    if softmax_impl not in {"exact_div", "pow2sum", "recip_lut", "pwl_recip_lut"}:
        raise SystemExit(
            "attention_dual_stream_composed.softmax_impl must be exact_div, pow2sum, recip_lut, or pwl_recip_lut"
        )
    if softmax_internal_pipeline_stages and softmax_impl != "exact_div":
        raise SystemExit("attention_dual_stream_composed.softmax_internal_pipeline_stages requires exact_div")
    if softmax_impl == "pwl_recip_lut" and softmax_internal_pipeline_stages:
        raise SystemExit("attention_dual_stream_composed.softmax_internal_pipeline_stages is not supported for pwl_recip_lut")
    return comp


def _int8_mac_module(*, accum_bits: int) -> str:
    sign_ext_bits = accum_bits - 16
    return f"""module int8_mac_s8s8_acc{accum_bits} (
    input  wire signed [7:0]  A,
    input  wire signed [7:0]  B,
    input  wire signed [{accum_bits - 1}:0] C,
    output wire signed [{accum_bits - 1}:0] R
);
  wire signed [15:0] product = A * B;
  assign R = {{{{{sign_ext_bits}{{product[15]}}}}, product}} + C;
endmodule
"""


def _hex_literal(*, bits: int, value: int) -> str:
    hex_digits = max(1, (bits + 3) // 4)
    return f"{bits}'h{value & ((1 << bits) - 1):0{hex_digits}x}"


def _zero_extend_cycle_ctr(*, bits: int) -> str:
    if bits == 16:
        return "cycle_ctr"
    return f"{{{bits - 16}'h0, cycle_ctr}}"


def _softmax_module(
    *,
    module_name: str,
    row_elems: int,
    accum_bits: int,
    reciprocal_bits: int,
    score_bits: int,
    weight_bits: int,
    input_frac_bits: int,
    reciprocal_lut_bucket_shift: int,
    equivalence_hash: bool,
    implementation: str,
    internal_pipeline_stages: int,
) -> str:
    score_row_width = row_elems * score_bits
    weight_row_width = row_elems * weight_bits
    output_scale = (1 << weight_bits) - 1
    shift_exp_max_weight = 128
    pwl_max_weight = output_scale
    max_weight = pwl_max_weight if implementation == "pwl_recip_lut" else shift_exp_max_weight
    product_bits = accum_bits + weight_bits
    hash_port = ",\n    output reg  [31:0]          weight_hash" if equivalence_hash else ""
    hash_reg = "  reg [31:0] next_hash;\n" if equivalence_hash else ""
    hash_init = f"    next_hash = 32'h5a5a_0101 ^ 32'h{reciprocal_bits & 0xFFFF:04x};\n" if equivalence_hash else ""
    hash_update = (
        f"      next_hash = {{next_hash[23:0], next_hash[31:24]}} ^ "
        f"{{{{{max(0, 32 - weight_bits)}{{1'b0}}}}, lane_out[{min(weight_bits, 32) - 1}:0]}};\n"
        if equivalence_hash
        else ""
    )
    hash_seq = "    weight_hash <= next_hash;\n" if equivalence_hash else ""
    max_sum_weight = row_elems * max_weight
    recip_lut_cases = "\n".join(
        f"      {accum_bits}'d{denom}: reciprocal_lut = {reciprocal_bits + weight_bits}'d{((output_scale << reciprocal_bits) + (denom >> 1)) // denom};"
        for denom in range(1, max_sum_weight + 1)
    )
    if implementation == "pwl_recip_lut":
        reciprocal_bucket_step = 1 << reciprocal_lut_bucket_shift
        max_bucket = (max_sum_weight + reciprocal_bucket_step - 1) >> reciprocal_lut_bucket_shift
        recip_lut_cases = "\n".join(
            f"      {accum_bits}'d{bucket}: reciprocal_lut = {reciprocal_bits + weight_bits}'d{((output_scale << reciprocal_bits) + ((bucket << reciprocal_lut_bucket_shift) >> 1)) // (bucket << reciprocal_lut_bucket_shift)};"
            for bucket in range(1, max_bucket + 1)
        )
        input_scale = 1 << input_frac_bits
        x2 = 2 * input_scale
        x4 = 4 * input_scale
        x8 = 8 * input_scale
        y0 = output_scale
        # Rounded exp anchors match src/rtlgen/rtl_operations.cpp.
        y2 = int(math.exp(-2.0) * output_scale + 0.5)
        y4 = int(math.exp(-4.0) * output_scale + 0.5)
        y8 = int(math.exp(-8.0) * output_scale + 0.5)
        return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{score_row_width - 1}:0] scores,
    output reg  [{weight_row_width - 1}:0] weights{hash_port}
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer SCORE_BITS = {score_bits};
  localparam integer WEIGHT_BITS = {weight_bits};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer OUTPUT_SCALE = {output_scale};
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};
  localparam integer RECIPROCAL_WIDTH = {reciprocal_bits + weight_bits};
  localparam integer RECIP_BUCKET_SHIFT = {reciprocal_lut_bucket_shift};
  localparam integer PWL_X2 = {x2};
  localparam integer PWL_X4 = {x4};
  localparam integer PWL_X8 = {x8};
  localparam integer PWL_Y0 = {y0};
  localparam integer PWL_Y2 = {y2};
  localparam integer PWL_Y4 = {y4};
  localparam integer PWL_Y8 = {y8};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [ACCUM_BITS-1:0] reciprocal_bucket;
  reg [RECIPROCAL_WIDTH-1:0] reciprocal_q;
  reg [PRODUCT_BITS+RECIPROCAL_WIDTH-1:0] lane_scaled;
  reg [WEIGHT_BITS-1:0] lane_out;
  reg [{weight_row_width - 1}:0] next_weights;
{hash_reg.rstrip()}

  function [ACCUM_BITS-1:0] pwl_weight;
    input integer delta_in;
    integer clamped_delta;
    integer seg_x0;
    integer seg_width;
    integer y0_seg;
    integer y1_seg;
    integer ydiff;
    reg [63:0] interp_num;
    begin
      clamped_delta = delta_in;
      if (clamped_delta < 0)
        clamped_delta = 0;
      if (clamped_delta > PWL_X8) begin
        pwl_weight = {{ACCUM_BITS{{1'b0}}}};
      end else if (clamped_delta == PWL_X8) begin
        pwl_weight = PWL_Y8;
      end else begin
        if (clamped_delta <= PWL_X2) begin
          seg_x0 = 0;
          seg_width = PWL_X2;
          y0_seg = PWL_Y0;
          y1_seg = PWL_Y2;
        end else if (clamped_delta <= PWL_X4) begin
          seg_x0 = PWL_X2;
          seg_width = PWL_X4 - PWL_X2;
          y0_seg = PWL_Y2;
          y1_seg = PWL_Y4;
        end else begin
          seg_x0 = PWL_X4;
          seg_width = PWL_X8 - PWL_X4;
          y0_seg = PWL_Y4;
          y1_seg = PWL_Y8;
        end
        ydiff = y0_seg - y1_seg;
        interp_num = ((clamped_delta - seg_x0) * ydiff) + (seg_width >> 1);
        pwl_weight = y0_seg - (interp_num / seg_width);
      end
    end
  endfunction

  function [RECIPROCAL_WIDTH-1:0] reciprocal_lut;
    input [ACCUM_BITS-1:0] bucket;
    begin
      case (bucket)
      {accum_bits}'d0: reciprocal_lut = {{RECIPROCAL_WIDTH{{1'b0}}}};
{recip_lut_cases}
      default: reciprocal_lut = {{RECIPROCAL_WIDTH{{1'b0}}}};
      endcase
    end
  endfunction

  always @(*) begin
    row_max = -(1 << (SCORE_BITS - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      exp_weight[i] = pwl_weight(delta);
      sum_weight = sum_weight + exp_weight[i];
    end

    reciprocal_bucket = (sum_weight + {accum_bits}'d{reciprocal_bucket_step - 1}) >> RECIP_BUCKET_SHIFT;
    reciprocal_q = reciprocal_lut(reciprocal_bucket);
    next_weights = {{{weight_row_width}{{1'b0}}}};
{hash_init.rstrip()}
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_scaled = (exp_weight[i] * reciprocal_q) + ({{{{(PRODUCT_BITS+RECIPROCAL_WIDTH-1){{1'b0}}}}, 1'b1}} << (RECIPROCAL_BITS - 1));
      lane_scaled = lane_scaled >> RECIPROCAL_BITS;
      if (lane_scaled > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      else
        lane_out = lane_scaled[WEIGHT_BITS-1:0];
      next_weights[(i*WEIGHT_BITS) +: WEIGHT_BITS] = lane_out;
{hash_update.rstrip()}
    end
  end

  always @(posedge clk) begin
    weights <= next_weights;
{hash_seq.rstrip()}
  end
endmodule
"""
    if internal_pipeline_stages:
        return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{score_row_width - 1}:0] scores,
    output reg  [{weight_row_width - 1}:0] weights{hash_port}
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer SCORE_BITS = {score_bits};
  localparam integer WEIGHT_BITS = {weight_bits};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = {output_scale};
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [ACCUM_BITS-1:0] exp_weight_q [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight_q;
  reg [PRODUCT_BITS-1:0] numer;
  reg [WEIGHT_BITS-1:0] lane_out;
  reg [{weight_row_width - 1}:0] next_weights;
{hash_reg.rstrip()}

  always @(*) begin
    row_max = -(1 << (SCORE_BITS - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      exp_weight[i] = ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << (MAX_SHIFT - delta));
      sum_weight = sum_weight + exp_weight[i];
    end
  end

  always @(*) begin
    next_weights = {{{weight_row_width}{{1'b0}}}};
{hash_init.rstrip()}
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      numer = (exp_weight_q[i] * OUTPUT_SCALE) + (sum_weight_q >> 1);
      if (sum_weight_q != 0)
        lane_out = numer / sum_weight_q;
      else
        lane_out = {{WEIGHT_BITS{{1'b0}}}};
      if (lane_out > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      next_weights[(i*WEIGHT_BITS) +: WEIGHT_BITS] = lane_out;
{hash_update.rstrip()}
    end
  end

  always @(posedge clk) begin
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      exp_weight_q[i] <= exp_weight[i];
    end
    sum_weight_q <= sum_weight;
    weights <= next_weights;
{hash_seq.rstrip()}
  end
endmodule
"""
    if implementation == "pow2sum":
        return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{score_row_width - 1}:0] scores,
    output reg  [{weight_row_width - 1}:0] weights{hash_port}
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer SCORE_BITS = {score_bits};
  localparam integer WEIGHT_BITS = {weight_bits};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = {output_scale};
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  integer denom_shift;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [PRODUCT_BITS-1:0] lane_scaled;
  reg [WEIGHT_BITS-1:0] lane_out;
  reg [{weight_row_width - 1}:0] next_weights;
{hash_reg.rstrip()}

  always @(*) begin
    row_max = -(1 << (SCORE_BITS - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      exp_weight[i] = ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << (MAX_SHIFT - delta));
      sum_weight = sum_weight + exp_weight[i];
    end

    denom_shift = 0;
    for (i = 0; i < ACCUM_BITS; i = i + 1) begin
      if (sum_weight > ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << i))
        denom_shift = i + 1;
    end

    next_weights = {{{weight_row_width}{{1'b0}}}};
{hash_init.rstrip()}
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_scaled = (exp_weight[i] * OUTPUT_SCALE) >> denom_shift;
      if (lane_scaled > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      else
        lane_out = lane_scaled[WEIGHT_BITS-1:0];
      next_weights[(i*WEIGHT_BITS) +: WEIGHT_BITS] = lane_out;
{hash_update.rstrip()}
    end
  end

  always @(posedge clk) begin
    weights <= next_weights;
{hash_seq.rstrip()}
  end
endmodule
"""
    if implementation == "recip_lut":
        return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{score_row_width - 1}:0] scores,
    output reg  [{weight_row_width - 1}:0] weights{hash_port}
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer SCORE_BITS = {score_bits};
  localparam integer WEIGHT_BITS = {weight_bits};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = {output_scale};
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};
  localparam integer RECIPROCAL_WIDTH = {reciprocal_bits + weight_bits};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [RECIPROCAL_WIDTH-1:0] reciprocal_q;
  reg [PRODUCT_BITS+RECIPROCAL_WIDTH-1:0] lane_scaled;
  reg [WEIGHT_BITS-1:0] lane_out;
  reg [{weight_row_width - 1}:0] next_weights;
{hash_reg.rstrip()}

  function [RECIPROCAL_WIDTH-1:0] reciprocal_lut;
    input [ACCUM_BITS-1:0] denom;
    begin
      case (denom)
{recip_lut_cases}
      default: reciprocal_lut = {{RECIPROCAL_WIDTH{{1'b0}}}};
      endcase
    end
  endfunction

  always @(*) begin
    row_max = -(1 << (SCORE_BITS - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      exp_weight[i] = ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << (MAX_SHIFT - delta));
      sum_weight = sum_weight + exp_weight[i];
    end

    reciprocal_q = reciprocal_lut(sum_weight);
    next_weights = {{{weight_row_width}{{1'b0}}}};
{hash_init.rstrip()}
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_scaled = (exp_weight[i] * reciprocal_q) + ({{{{(PRODUCT_BITS+RECIPROCAL_WIDTH-1){{1'b0}}}}, 1'b1}} << (RECIPROCAL_BITS - 1));
      lane_scaled = lane_scaled >> RECIPROCAL_BITS;
      if (lane_scaled > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      else
        lane_out = lane_scaled[WEIGHT_BITS-1:0];
      next_weights[(i*WEIGHT_BITS) +: WEIGHT_BITS] = lane_out;
{hash_update.rstrip()}
    end
  end

  always @(posedge clk) begin
    weights <= next_weights;
{hash_seq.rstrip()}
  end
endmodule
"""
    return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{score_row_width - 1}:0] scores,
    output reg  [{weight_row_width - 1}:0] weights{hash_port}
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer SCORE_BITS = {score_bits};
  localparam integer WEIGHT_BITS = {weight_bits};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = {output_scale};
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [PRODUCT_BITS-1:0] numer;
  reg [WEIGHT_BITS-1:0] lane_out;
  reg [{weight_row_width - 1}:0] next_weights;
{hash_reg.rstrip()}

  always @(*) begin
    row_max = -(1 << (SCORE_BITS - 1));
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*SCORE_BITS) +: SCORE_BITS]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      exp_weight[i] = ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << (MAX_SHIFT - delta));
      sum_weight = sum_weight + exp_weight[i];
    end

    next_weights = {{{weight_row_width}{{1'b0}}}};
{hash_init.rstrip()}
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      numer = (exp_weight[i] * OUTPUT_SCALE) + (sum_weight >> 1);
      if (sum_weight != 0)
        lane_out = numer / sum_weight;
      else
        lane_out = {{WEIGHT_BITS{{1'b0}}}};
      if (lane_out > OUTPUT_SCALE)
        lane_out = OUTPUT_SCALE;
      next_weights[(i*WEIGHT_BITS) +: WEIGHT_BITS] = lane_out;
{hash_update.rstrip()}
    end
  end

  always @(posedge clk) begin
    weights <= next_weights;
{hash_seq.rstrip()}
  end
endmodule
"""


def _value_stream_module(
    *,
    module_name: str,
    row_elems: int,
    weight_bits: int,
    value_bits: int,
    value_lanes: int,
    stream_buffer_bits: int,
    score_mix_bits: int,
    equivalence_hash: bool,
) -> str:
    acc_bits = 40
    product_bits = value_bits + weight_bits + 1
    fold_terms = ["32'h0000_0000"]
    product_lines: list[str] = []
    fold_pad_bits = max(0, 32 - product_bits)
    for lane in range(value_lanes):
        product_lines.extend(
            [
                f"  wire signed [{value_bits - 1}:0] value_{lane:02d} = stream_data[{(lane * value_bits) % (stream_buffer_bits - value_bits + 1)} +: {value_bits}];",
                f"  wire [{weight_bits - 1}:0] weight_{lane:02d} = weights[{(lane % row_elems) * weight_bits} +: {weight_bits}];",
                f"  wire signed [{weight_bits}:0] weight_{lane:02d}_signed = {{1'b0, weight_{lane:02d}}};",
                f"  wire signed [{product_bits - 1}:0] product_{lane:02d} = value_{lane:02d} * weight_{lane:02d}_signed;",
            ]
        )
        fold_terms.append(f"{{{{{fold_pad_bits}{{1'b0}}}}, product_{lane:02d}}}")
    sum_terms = [
        f"{{{{{acc_bits - product_bits}{{product_{lane:02d}[{product_bits - 1}]}}}}, product_{lane:02d}}}"
        for lane in range(value_lanes)
    ]
    sum_expr = " +\n      ".join(sum_terms)
    fold_expr = " ^\n      ".join(fold_terms)
    score_ext = f"{{{{{acc_bits - score_mix_bits}{{score_mix[{score_mix_bits - 1}]}}}}, score_mix}}"
    score_hash_mix = (
        "score_mix[31:0]" if score_mix_bits >= 32 else f"{{{{{32 - score_mix_bits}{{1'b0}}}}, score_mix}}"
    )
    hash_port = ",\n    output reg  [31:0]           value_hash" if equivalence_hash else ""
    fold_wire = f"""  wire [31:0] product_fold =
      {fold_expr};
""" if equivalence_hash else ""
    hash_seq = f"    value_hash <= product_fold ^ value_accum[31:0] ^ {score_hash_mix};\n" if equivalence_hash else ""
    return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{stream_buffer_bits - 1}:0] stream_data,
    input  wire [{row_elems * weight_bits - 1}:0] weights,
    input  wire [{score_mix_bits - 1}:0] score_mix,
    output reg  [{acc_bits - 1}:0] value_accum{hash_port}
);
{chr(10).join(product_lines)}
  wire signed [{acc_bits - 1}:0] product_sum =
      {sum_expr};
{fold_wire.rstrip()}

  always @(posedge clk) begin
    value_accum <= product_sum + {score_ext};
{hash_seq.rstrip()}
  end
endmodule
"""


def _write_top(*, cfg: dict[str, Any], comp: dict[str, Any], out_path: Path) -> None:
    top_name = str(cfg.get("top_name", "attention_dual_stream_composed_top")).strip()
    array_m = _as_int(comp, "array_m", 16)
    array_n = _as_int(comp, "array_n", 8)
    k_unroll = _as_int(comp, "k_unroll", 1)
    row_elems = _as_int(comp, "softmax_row_elems", 8)
    value_bits = _as_int(comp, "value_bits", 6)
    value_lanes = _as_int(comp, "value_lanes", 16)
    partials = _as_int(comp, "partials", 8)
    partials_per_cycle = _as_int(comp, "partials_per_cycle", 2)
    reciprocal_bits = _as_int(comp, "reciprocal_bits", 10)
    accum_bits = _as_int(comp, "softmax_accum_bits", 24)
    mac_accum_bits = _as_int(comp, "mac_accum_bits", 24)
    softmax_score_bits = _as_int(comp, "softmax_score_bits", 8)
    softmax_weight_bits = _as_int(comp, "softmax_weight_bits", 8)
    softmax_input_frac_bits = _as_int(comp, "softmax_input_frac_bits", 0)
    softmax_reciprocal_lut_bucket_shift = _as_int(comp, "softmax_reciprocal_lut_bucket_shift", 0)
    stream_buffer_bits = _as_int(comp, "stream_buffer_bits", 1024)
    equivalence_hash = _as_bool(comp, "equivalence_hash", False)
    softmax_pipeline_stages = _as_int(comp, "softmax_pipeline_stages", 0)
    softmax_internal_pipeline_stages = _as_int(comp, "softmax_internal_pipeline_stages", 0)
    softmax_impl = _as_str(comp, "softmax_impl", "exact_div")
    score_mix_bits = mac_accum_bits
    softmax_latency_stages = 1 + softmax_internal_pipeline_stages
    value_delay_stages = softmax_pipeline_stages + softmax_latency_stages if softmax_pipeline_stages else 0
    macs_per_stream = array_m * array_n * k_unroll
    streams = 2
    total_macs = streams * macs_per_stream
    softmax_score_row_width = row_elems * softmax_score_bits
    softmax_weight_row_width = row_elems * softmax_weight_bits
    softmax_name = (
        "attention_softmax_weight_q12_pwl_recip_like"
        if softmax_impl == "pwl_recip_lut"
        else (
            "attention_softmax_weight_score32_w16_exact_div_like"
            if softmax_score_bits == 32 and softmax_weight_bits == 16 and softmax_impl == "exact_div"
            else "attention_softmax_weight_int8_r8_acc24_recip_q10_like"
        )
    )
    value_name = f"attention_full_value_stream_q8v{value_bits}_p8_ppc2"

    stream_regs = [f"  reg [{stream_buffer_bits - 1}:0] stream_buf_{stream};" for stream in range(streams)]
    stream_reset = [f"      stream_buf_{stream} <= {{{stream_buffer_bits}{{1'b0}}}};" for stream in range(streams)]
    stream_update = [
        (
            f"      stream_buf_{stream} <= {{stream_buf_{stream}[{stream_buffer_bits - 33}:0], "
            f"seed_state ^ {{16'h0, cycle_ctr}} ^ 32'h{0x13572468 ^ stream:08x}}};"
        )
        for stream in range(streams)
    ]
    softmax_pipe_regs = ""
    softmax_pipe_reset = ""
    softmax_pipe_update = ""
    softmax_scores_for_softmax = "softmax_scores"
    if softmax_pipeline_stages:
        softmax_pipe_regs = f"  reg [{softmax_score_row_width - 1}:0] softmax_scores_pipe_0;\n"
        softmax_pipe_reset = f"      softmax_scores_pipe_0 <= {{{softmax_score_row_width}{{1'b0}}}};\n"
        softmax_pipe_update = "      softmax_scores_pipe_0 <= softmax_scores;\n"
        softmax_scores_for_softmax = "softmax_scores_pipe_0"

    value_pipe_regs: list[str] = []
    value_pipe_reset: list[str] = []
    value_pipe_update: list[str] = []
    value_stream_data_for_value = [f"stream_buf_{stream}" for stream in range(streams)]
    score_mix_for_value = [f"score_mix_{stream}" for stream in range(streams)]
    if value_delay_stages:
        for stream in range(streams):
            for stage in range(value_delay_stages):
                value_pipe_regs.append(f"  reg [{stream_buffer_bits - 1}:0] stream_buf_{stream}_pipe_{stage};")
                value_pipe_regs.append(f"  reg [{score_mix_bits - 1}:0] score_mix_{stream}_pipe_{stage};")
                value_pipe_reset.append(f"      stream_buf_{stream}_pipe_{stage} <= {{{stream_buffer_bits}{{1'b0}}}};")
                value_pipe_reset.append(f"      score_mix_{stream}_pipe_{stage} <= {{{score_mix_bits}{{1'b0}}}};")
                source_stream = f"stream_buf_{stream}" if stage == 0 else f"stream_buf_{stream}_pipe_{stage - 1}"
                source_score = f"score_mix_{stream}" if stage == 0 else f"score_mix_{stream}_pipe_{stage - 1}"
                value_pipe_update.append(f"      stream_buf_{stream}_pipe_{stage} <= {source_stream};")
                value_pipe_update.append(f"      score_mix_{stream}_pipe_{stage} <= {source_score};")
            value_stream_data_for_value[stream] = f"stream_buf_{stream}_pipe_{value_delay_stages - 1}"
            score_mix_for_value[stream] = f"score_mix_{stream}_pipe_{value_delay_stages - 1}"

    mac_wires: list[str] = []
    mac_insts: list[str] = []
    score_lane_terms: list[list[str]] = [[] for _ in range(row_elems)]
    score_mix_terms = [[f"{score_mix_bits}'h0"] for _ in range(streams)]
    compute_fold_terms = ["32'h0000_0000"]
    for stream in range(streams):
        for idx in range(macs_per_stream):
            row = idx // (array_n * k_unroll)
            col = (idx // k_unroll) % array_n
            ku = idx % k_unroll
            flat = stream * macs_per_stream + idx
            const_a = (0x3D ^ ((stream + 1) * 0x17) ^ ((row + 1) * 0x13) ^ ((col + 1) * 0x27) ^ (ku * 0x41)) & 0xFF
            const_b = (0x21 ^ ((stream + 1) * 0x2B) ^ ((row + 1) * 0x1D) ^ ((col + 1) * 0xA3) ^ (ku * 0x55)) & 0xFF
            const_c = (
                0x001011
                ^ ((stream + 1) * 0x0101)
                ^ ((row + 1) * 0x0007)
                ^ ((col + 1) * 0x000B)
                ^ (ku * 0x0013)
            ) & ((1 << mac_accum_bits) - 1)
            mac_wires.extend(
                [
                    f"  wire signed [7:0] mac_a_{flat:04d} = seed_state[7:0] ^ stream_buf_{stream}[{(idx * 7) % (stream_buffer_bits - 7)} +: 8] ^ 8'h{const_a:02x} ^ cycle_ctr[7:0];",
                    f"  wire signed [7:0] mac_b_{flat:04d} = seed_state[15:8] ^ stream_buf_{stream}[{(idx * 11) % (stream_buffer_bits - 7)} +: 8] ^ 8'h{const_b:02x} ^ cycle_ctr[15:8];",
                    f"  wire signed [{mac_accum_bits - 1}:0] mac_c_{flat:04d} = {_zero_extend_cycle_ctr(bits=mac_accum_bits)} ^ stream_buf_{stream}[{(idx * 13) % (stream_buffer_bits - mac_accum_bits + 1)} +: {mac_accum_bits}] ^ {_hex_literal(bits=mac_accum_bits, value=const_c)};",
                    f"  wire signed [{mac_accum_bits - 1}:0] mac_r_{flat:04d};",
                ]
            )
            mac_insts.append(
                f"""  int8_mac_s8s8_acc{mac_accum_bits} u_mac_{flat:04d} (
    .A(mac_a_{flat:04d}),
    .B(mac_b_{flat:04d}),
    .C(mac_c_{flat:04d}),
    .R(mac_r_{flat:04d})
  );"""
            )
            score_mix_term = f"mac_r_{flat:04d}[{softmax_score_bits - 1}:0]"
            score_lane_terms[idx % row_elems].append(score_mix_term)
            score_mix_terms[stream].append(f"mac_r_{flat:04d}")
            compute_fold_terms.append(
                f"mac_r_{flat:04d}[31:0]" if mac_accum_bits >= 32 else f"{{{{{32 - mac_accum_bits}{{1'b0}}}}, mac_r_{flat:04d}}}"
            )

    score_assigns = []
    for lane, terms in enumerate(score_lane_terms):
        expr = " ^ ".join(terms or [f"{softmax_score_bits}'h0"])
        score_assigns.append(f"  wire [{softmax_score_bits - 1}:0] score_lane_{lane:02d} = {expr};")
    score_row_concat = ", ".join(f"score_lane_{lane:02d}" for lane in reversed(range(row_elems)))
    compute_fold_expr = " ^\n      ".join(compute_fold_terms)
    score_mix_exprs = [" ^\n      ".join(terms) for terms in score_mix_terms]
    top_ports = [
        "    input  wire        clk",
        "    input  wire        rst_n",
        "    input  wire        start",
        "    input  wire [31:0] seed",
        "    output reg         done",
    ]
    if equivalence_hash:
        top_ports.append("    output reg  [31:0] result_hash")
    else:
        top_ports.extend(
            [
                f"    output reg  [{softmax_weight_row_width - 1}:0] softmax_weights_out",
                "    output reg  [39:0] value_accum_0_out",
                "    output reg  [39:0] value_accum_1_out",
                f"    output reg  [{score_mix_bits - 1}:0] score_mix_0_out",
                f"    output reg  [{score_mix_bits - 1}:0] score_mix_1_out",
            ]
        )
    softmax_hash_wire = "  wire [31:0] softmax_weight_hash;\n" if equivalence_hash else ""
    value_hash_wires = "  wire [31:0] value_hash_0;\n  wire [31:0] value_hash_1;\n" if equivalence_hash else ""
    compute_fold_wire = f"""  wire [31:0] compute_fold =
      {compute_fold_expr};
""" if equivalence_hash else ""
    softmax_hash_conn = ",\n    .weight_hash(softmax_weight_hash)" if equivalence_hash else ""
    value_hash_conn_0 = ",\n    .value_hash(value_hash_0)" if equivalence_hash else ""
    value_hash_conn_1 = ",\n    .value_hash(value_hash_1)" if equivalence_hash else ""
    reset_hash = "      result_hash <= 32'h0;\n" if equivalence_hash else ""
    reset_ppa_outputs = "" if equivalence_hash else f"""      softmax_weights_out <= {{{softmax_weight_row_width}{{1'b0}}}};
      value_accum_0_out <= 40'h0;
      value_accum_1_out <= 40'h0;
      score_mix_0_out <= {{{score_mix_bits}{{1'b0}}}};
      score_mix_1_out <= {{{score_mix_bits}{{1'b0}}}};
"""
    update_outputs = (
        """        result_hash <= result_hash ^ compute_fold ^ softmax_weight_hash ^ value_hash_0 ^ value_hash_1 ^
                       value_accum_0[31:0] ^ value_accum_1[31:0] ^ {16'h0, cycle_ctr};
"""
        if equivalence_hash
        else """        softmax_weights_out <= softmax_weights;
        value_accum_0_out <= value_accum_0;
        value_accum_1_out <= value_accum_1;
        score_mix_0_out <= score_mix_0;
        score_mix_1_out <= score_mix_1;
"""
    )
    top_port_text = ",\n".join(top_ports)

    top_text = f"""// Auto-generated by npu/rtlgen/gen_attention_dual_stream_composed.py
(* keep_hierarchy = 1 *)
module {top_name} (
{top_port_text}
);
  localparam integer STREAMS = {streams};
  localparam integer ARRAY_M = {array_m};
  localparam integer ARRAY_N = {array_n};
  localparam integer K_UNROLL = {k_unroll};
  localparam integer MACS_PER_STREAM = {macs_per_stream};
  localparam integer TOTAL_MACS = {total_macs};
  localparam integer SOFTMAX_ROW_ELEMS = {row_elems};
  localparam integer VALUE_LANES = {value_lanes};
  localparam integer PARTIALS = {partials};
  localparam integer PARTIALS_PER_CYCLE = {partials_per_cycle};
  localparam integer STREAM_BUFFER_BITS = {stream_buffer_bits};

  reg [31:0] seed_state;
  reg [15:0] cycle_ctr;
{chr(10).join(stream_regs)}
{softmax_pipe_regs.rstrip()}
{chr(10).join(value_pipe_regs)}

{chr(10).join(mac_wires)}

{chr(10).join(mac_insts)}

{chr(10).join(score_assigns)}
  wire [{softmax_score_row_width - 1}:0] softmax_scores = {{{score_row_concat}}};
  wire [{softmax_weight_row_width - 1}:0] softmax_weights;
{softmax_hash_wire.rstrip()}
{compute_fold_wire.rstrip()}
  wire [{score_mix_bits - 1}:0] score_mix_0 =
      {score_mix_exprs[0]};
  wire [{score_mix_bits - 1}:0] score_mix_1 =
      {score_mix_exprs[1]};
  wire [39:0] value_accum_0;
  wire [39:0] value_accum_1;
{value_hash_wires.rstrip()}

  {softmax_name} u_softmax (
    .clk(clk),
    .scores({softmax_scores_for_softmax}),
    .weights(softmax_weights){softmax_hash_conn}
  );

  {value_name} u_value_stream_0 (
    .clk(clk),
    .stream_data({value_stream_data_for_value[0]}),
    .weights(softmax_weights),
    .score_mix({score_mix_for_value[0]}),
    .value_accum(value_accum_0){value_hash_conn_0}
  );

  {value_name} u_value_stream_1 (
    .clk(clk),
    .stream_data({value_stream_data_for_value[1]}),
    .weights(softmax_weights),
    .score_mix({score_mix_for_value[1]}),
    .value_accum(value_accum_1){value_hash_conn_1}
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      seed_state <= 32'h0000_0001;
      cycle_ctr <= 16'h0;
{reset_hash.rstrip()}
      done <= 1'b0;
{reset_ppa_outputs.rstrip()}
{chr(10).join(stream_reset)}
{softmax_pipe_reset.rstrip()}
{chr(10).join(value_pipe_reset)}
    end else begin
      seed_state <= {{seed_state[30:0], seed_state[31] ^ seed_state[21] ^ seed_state[1] ^ seed_state[0]}} ^ seed;
      cycle_ctr <= cycle_ctr + 16'h1;
      done <= start;
{chr(10).join(stream_update)}
{softmax_pipe_update.rstrip()}
{chr(10).join(value_pipe_update)}
      if (start) begin
{update_outputs.rstrip()}
      end
    end
  end
endmodule
"""

    out_path.mkdir(parents=True, exist_ok=True)
    rtl = "\n\n".join(
        [
            _int8_mac_module(accum_bits=mac_accum_bits),
            _softmax_module(
                module_name=softmax_name,
                row_elems=row_elems,
                accum_bits=accum_bits,
                reciprocal_bits=reciprocal_bits,
                score_bits=softmax_score_bits,
                weight_bits=softmax_weight_bits,
                input_frac_bits=softmax_input_frac_bits,
                reciprocal_lut_bucket_shift=softmax_reciprocal_lut_bucket_shift,
                equivalence_hash=equivalence_hash,
                implementation=softmax_impl,
                internal_pipeline_stages=softmax_internal_pipeline_stages,
            ),
            _value_stream_module(
                module_name=value_name,
                row_elems=row_elems,
                weight_bits=softmax_weight_bits,
                value_bits=value_bits,
                value_lanes=value_lanes,
                stream_buffer_bits=stream_buffer_bits,
                score_mix_bits=score_mix_bits,
                equivalence_hash=equivalence_hash,
            ),
            top_text,
        ]
    )
    (out_path / "top.v").write_text(rtl, encoding="utf-8")
    manifest = {
        "version": 0.1,
        "generator": "npu/rtlgen/gen_attention_dual_stream_composed.py",
        "top_name": top_name,
        "streams": streams,
        "array_m": array_m,
        "array_n": array_n,
        "k_unroll": k_unroll,
        "macs_per_stream": macs_per_stream,
        "total_macs": total_macs,
        "softmax_row_elems": row_elems,
        "mac_accum_bits": mac_accum_bits,
        "mac_module": f"int8_mac_s8s8_acc{mac_accum_bits}",
        "softmax_accum_bits": accum_bits,
        "softmax_score_bits": softmax_score_bits,
        "softmax_weight_bits": softmax_weight_bits,
        "softmax_input_frac_bits": softmax_input_frac_bits,
        "softmax_reciprocal_lut_bucket_shift": softmax_reciprocal_lut_bucket_shift,
        "reciprocal_bits": reciprocal_bits,
        "value_bits": value_bits,
        "value_lanes_per_stream": value_lanes,
        "partials": partials,
        "partials_per_cycle": partials_per_cycle,
        "stream_buffer_bits_per_stream": stream_buffer_bits,
        "equivalence_hash": equivalence_hash,
        "softmax_impl": softmax_impl,
        "softmax_pipeline_stages": softmax_pipeline_stages,
        "softmax_internal_pipeline_stages": softmax_internal_pipeline_stages,
        "softmax_latency_stages": softmax_latency_stages,
        "value_alignment_delay_stages": value_delay_stages,
        "score_mix_bits": score_mix_bits,
        "score_bits_source": f"mac_acc{mac_accum_bits}_native",
        "components": {
            "compute": "two signed-int8 dense GEMM streams",
            "softmax_weight": (
                "one shared q12 PWL reciprocal-normalized generator"
                if softmax_impl == "pwl_recip_lut"
                else "one shared rowwise int8 shift-exp reciprocal-normalized generator"
            ),
            "full_value": "two q8/v6 weighted-value streams",
            "control": "start/done, seed LFSR, per-stream buffer registers",
        },
        "datapath_guard": (
            "all MAC, softmax, and value stream outputs fold into result_hash"
            if equivalence_hash
            else "PPA mode exposes softmax weights, value accumulators, and score mixes directly; equivalence hash disabled"
        ),
    }
    (out_path / "attention_dual_stream_composed_manifest.json").write_text(
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
    print(f"attention-dual-stream-composed: wrote RTL to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
