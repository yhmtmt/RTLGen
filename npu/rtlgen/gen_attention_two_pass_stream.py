#!/usr/bin/env python3
"""Generate a scalable two-pass attention engine with external score SRAM ports."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(config: dict[str, Any]) -> dict[str, int | str]:
    if not str(config.get("top_name") or "").strip():
        raise SystemExit("config top_name must not be empty")
    body = config.get("attention_two_pass_stream")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_two_pass_stream object")
    max_blocks = int(body.get("max_blocks", 16384))
    div_lanes = int(body.get("div_lanes_per_cycle", 1))
    divider_impl = str(body.get("divider_impl", "combinational")).strip()
    if max_blocks < 8 or max_blocks > 16384 or max_blocks & (max_blocks - 1):
        raise SystemExit("attention_two_pass_stream.max_blocks must be a power of two in [8, 16384]")
    if div_lanes not in {1, 2, 4, 8}:
        raise SystemExit("attention_two_pass_stream.div_lanes_per_cycle must be one of 1,2,4,8")
    if divider_impl not in {"combinational", "iterative_restoring"}:
        raise SystemExit(
            "attention_two_pass_stream.divider_impl must be combinational or iterative_restoring"
        )
    if divider_impl == "iterative_restoring" and div_lanes != 1:
        raise SystemExit("iterative_restoring uses one shared divider; div_lanes_per_cycle must be 1")
    params: dict[str, int | str] = {
        "max_blocks": max_blocks,
        "div_lanes_per_cycle": div_lanes,
        "divider_impl": divider_impl,
    }
    body.update(params)
    return params


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _exp_cases() -> str:
    return "\n".join(
        f"      32'd{bucket}: exp_lut = 16'd{max(1, int(math.exp(-(bucket / 256.0)) * 65535 + 0.5))};"
        for bucket in range(2049)
    )


def _top(*, top_name: str, params: dict[str, int | str]) -> str:
    max_blocks = int(params["max_blocks"])
    addr_bits = _clog2(max_blocks)
    count_bits = _clog2(max_blocks + 1)
    div_lanes = int(params["div_lanes_per_cycle"])
    divider_impl = str(params["divider_impl"])
    reset_num = "\n".join(f"      numerator_accum[{lane}] <= 41'sd0;" for lane in range(8))
    clear_num = "\n".join(f"        numerator_accum[{lane}] <= 41'sd0;" for lane in range(8))
    init_block = "\n".join(f"        block_numerator[{lane}] = 41'sd0;" for lane in range(8))
    next_num = "\n".join(
        f"        numerator_next[{lane}] = numerator_accum[{lane}] + block_numerator[{lane}];" for lane in range(8)
    )
    store_num = "\n".join(f"        numerator_accum[{lane}] <= numerator_next[{lane}];" for lane in range(8))
    if divider_impl == "iterative_restoring":
        state_params = (
            "  localparam [2:0] IDLE = 3'd0, FILL = 3'd1, READ_REQ = 3'd2,\n"
            "      READ_DATA = 3'd3, DIVIDE = 3'd4, DIV_LOAD = 3'd5,\n"
            "      DIV_ITER = 3'd6, HOLD = 3'd7;"
        )
        divider_regs = """
  reg div_negative;
  reg [6:0] div_bit_count;
  reg [57:0] div_quotient;
  reg [33:0] div_remainder;
  reg [33:0] div_trial_remainder;
  reg [57:0] div_next_quotient;
"""
        divider_reset = """
      div_negative <= 1'b0;
      div_bit_count <= 7'd0;
      div_quotient <= 58'd0;
      div_remainder <= 34'd0;
"""
        divider_logic = """
      if (state == DIVIDE) begin
        div_negative <= numerator_accum[div_index] < 0;
        if (numerator_accum[div_index] < 0)
          numerator_magnitude <= (~numerator_accum[div_index]) + 1'b1;
        else
          numerator_magnitude <= numerator_accum[div_index];
        state <= DIV_LOAD;
      end

      if (state == DIV_LOAD) begin
        final_magnitude <= ({17'd0, numerator_magnitude} << 16)
            - {17'd0, numerator_magnitude} + (exp_sum_accum >> 1);
        div_quotient <= 58'd0;
        div_remainder <= 34'd0;
        div_bit_count <= 7'd58;
        state <= DIV_ITER;
      end

      if (state == DIV_ITER) begin
        div_trial_remainder = {div_remainder[32:0], final_magnitude[57]};
        div_next_quotient = {div_quotient[56:0], 1'b0};
        if (div_trial_remainder >= {1'b0, exp_sum_accum}) begin
          div_remainder <= div_trial_remainder - {1'b0, exp_sum_accum};
          div_next_quotient[0] = 1'b1;
        end else begin
          div_remainder <= div_trial_remainder;
        end
        final_magnitude <= {final_magnitude[56:0], 1'b0};
        div_quotient <= div_next_quotient;
        if (div_bit_count == 1) begin
          if (div_negative)
            result_value[(div_index * 40) +: 40] <= (~div_next_quotient[39:0]) + 1'b1;
          else
            result_value[(div_index * 40) +: 40] <= div_next_quotient[39:0];
          if (div_index == 7) begin
            state <= HOLD;
            result_valid <= 1'b1;
          end else begin
            div_index <= div_index + 1'b1;
            state <= DIVIDE;
          end
        end else begin
          div_bit_count <= div_bit_count - 1'b1;
        end
      end
"""
    else:
        state_params = (
            "  localparam [2:0] IDLE = 3'd0, FILL = 3'd1, READ_REQ = 3'd2,\n"
            "      READ_DATA = 3'd3, DIVIDE = 3'd4, HOLD = 3'd5;"
        )
        divider_regs = ""
        divider_reset = ""
        divider_logic = """
      if (state == DIVIDE) begin
        for (lane_iter = 0; lane_iter < DIV_LANES; lane_iter = lane_iter + 1) begin
          lane_index = div_index + lane_iter;
          if (lane_index < 8) begin
            if (numerator_accum[lane_index] < 0) begin
              numerator_magnitude = (~numerator_accum[lane_index]) + 1'b1;
              final_magnitude = (numerator_magnitude * 17'd65535) + (exp_sum_accum >> 1);
              final_quotient = final_magnitude / exp_sum_accum;
              result_value[(lane_index * 40) +: 40] <= (~final_quotient) + 1'b1;
            end else begin
              numerator_magnitude = numerator_accum[lane_index];
              final_magnitude = (numerator_magnitude * 17'd65535) + (exp_sum_accum >> 1);
              final_quotient = final_magnitude / exp_sum_accum;
              result_value[(lane_index * 40) +: 40] <= final_quotient;
            end
          end
        end
        if (div_index + DIV_LANES >= 8) begin
          state <= HOLD;
          result_valid <= 1'b1;
        end else begin
          div_index <= div_index + DIV_LANES;
        end
      end
"""
    return f"""module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [{count_bits - 1}:0] command_block_count,

    input  wire         fill_valid,
    output wire         fill_ready,
    input  wire [255:0] fill_score_row,
    output wire         score_write_valid,
    input  wire         score_write_ready,
    output wire [{addr_bits - 1}:0] score_write_addr,
    output wire [255:0] score_write_data,

    output wire         score_read_req_valid,
    input  wire         score_read_req_ready,
    output wire [{addr_bits - 1}:0] score_read_req_addr,
    input  wire         replay_valid,
    output wire         replay_ready,
    input  wire [255:0] replay_score_row,
    input  wire [511:0] replay_value_matrix,

    output reg          result_valid,
    input  wire         result_ready,
    output reg  [15:0]  result_command_id,
    output reg signed [31:0] result_global_max,
    output reg  [32:0]  result_exp_sum,
    output reg  [319:0] result_value,
    output reg  [31:0]  accepted_count,
    output reg  [31:0]  completed_count,
    output reg  [31:0]  cycle_count
);
  localparam integer MAX_BLOCKS = {max_blocks};
  localparam integer ADDR_W = {addr_bits};
  localparam integer COUNT_W = {count_bits};
  localparam integer DIV_LANES = {div_lanes};
{state_params}

  reg [2:0] state;
  reg [15:0] active_command_id;
  reg [COUNT_W-1:0] active_block_count;
  reg [COUNT_W-1:0] fill_count;
  reg [ADDR_W-1:0] read_index;
  reg [3:0] div_index;
  reg signed [31:0] global_max;
  reg [32:0] exp_sum_accum;
  reg signed [40:0] numerator_accum [0:7];

  integer row_idx;
  integer dim_idx;
  integer lane_iter;
  integer lane_index;
  reg signed [31:0] block_max;
  reg signed [31:0] score_lane;
  reg signed [31:0] delta_score;
  reg [31:0] exp_bucket;
  reg [15:0] exp_weight;
  reg signed [7:0] value_lane;
  reg [19:0] block_sum;
  reg signed [40:0] block_numerator [0:7];
  reg [32:0] sum_next;
  reg signed [40:0] numerator_next [0:7];
  reg [40:0] numerator_magnitude;
  reg [57:0] final_magnitude;
  reg [39:0] final_quotient;
{divider_regs}

  assign command_ready = state == IDLE;
  assign fill_ready = state == FILL && score_write_ready;
  assign score_write_valid = state == FILL && fill_valid;
  assign score_write_addr = fill_count[ADDR_W-1:0];
  assign score_write_data = fill_score_row;
  assign score_read_req_valid = state == READ_REQ;
  assign score_read_req_addr = read_index;
  assign replay_ready = state == READ_DATA;

  function automatic [15:0] exp_lut;
    input [31:0] bucket;
    begin
      case (bucket)
{_exp_cases()}
      default: exp_lut = 16'd0;
      endcase
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      active_command_id <= 16'd0;
      active_block_count <= {{COUNT_W{{1'b0}}}};
      fill_count <= {{COUNT_W{{1'b0}}}};
      read_index <= {{ADDR_W{{1'b0}}}};
      div_index <= 4'd0;
      global_max <= -32'sh8000_0000;
      exp_sum_accum <= 33'd0;
      result_valid <= 1'b0;
      result_command_id <= 16'd0;
      result_global_max <= 32'sd0;
      result_exp_sum <= 33'd0;
      result_value <= 320'd0;
      accepted_count <= 32'd0;
      completed_count <= 32'd0;
      cycle_count <= 32'd0;
{divider_reset}
{reset_num}
    end else begin
      cycle_count <= cycle_count + 1'b1;
      if (state == IDLE && command_valid && command_block_count != 0) begin
        state <= FILL;
        active_command_id <= command_id;
        active_block_count <= command_block_count;
        fill_count <= {{COUNT_W{{1'b0}}}};
        global_max <= -32'sh8000_0000;
        accepted_count <= accepted_count + 1'b1;
      end

      if (state == FILL && fill_valid && fill_ready) begin
        block_max = $signed(fill_score_row[0 +: 32]);
        for (row_idx = 1; row_idx < 8; row_idx = row_idx + 1) begin
          score_lane = $signed(fill_score_row[(row_idx * 32) +: 32]);
          if (score_lane > block_max) block_max = score_lane;
        end
        if (fill_count == 0 || block_max > global_max) global_max <= block_max;
        if (fill_count + 1'b1 == active_block_count) begin
          state <= READ_REQ;
          read_index <= {{ADDR_W{{1'b0}}}};
          exp_sum_accum <= 33'd0;
{clear_num}
        end
        fill_count <= fill_count + 1'b1;
      end

      if (state == READ_REQ && score_read_req_ready) begin
        state <= READ_DATA;
      end

      if (state == READ_DATA && replay_valid && replay_ready) begin
        block_sum = 20'd0;
{init_block}
        for (row_idx = 0; row_idx < 8; row_idx = row_idx + 1) begin
          score_lane = $signed(replay_score_row[(row_idx * 32) +: 32]);
          delta_score = global_max - score_lane;
          if (delta_score < 0) delta_score = 32'sd0;
          exp_bucket = (delta_score + 32'd524288) >> 20;
          exp_weight = exp_lut(exp_bucket);
          block_sum = block_sum + exp_weight;
          for (dim_idx = 0; dim_idx < 8; dim_idx = dim_idx + 1) begin
            value_lane = $signed(replay_value_matrix[((row_idx * 8 + dim_idx) * 8) +: 8]);
            block_numerator[dim_idx] = block_numerator[dim_idx]
                + ($signed(value_lane) * $signed({{1'b0, exp_weight}}));
          end
        end
        sum_next = exp_sum_accum + block_sum;
{next_num}
        exp_sum_accum <= sum_next;
{store_num}
        if (read_index + 1'b1 == active_block_count) begin
          state <= DIVIDE;
          div_index <= 4'd0;
          result_command_id <= active_command_id;
          result_global_max <= global_max;
          result_exp_sum <= sum_next;
        end else begin
          read_index <= read_index + 1'b1;
          state <= READ_REQ;
        end
      end

{divider_logic}

      if (state == HOLD && result_valid && result_ready) begin
        result_valid <= 1'b0;
        completed_count <= completed_count + 1'b1;
        state <= IDLE;
      end
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    params = _validate(config)
    top_name = str(config["top_name"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(_top(top_name=top_name, params=params), encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "version": 1,
        "top_name": top_name,
        "semantic_profile": "q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max",
        "max_blocks": params["max_blocks"],
        "max_context_tokens": int(params["max_blocks"]) * 8,
        "div_lanes_per_cycle": params["div_lanes_per_cycle"],
        "divider_impl": params["divider_impl"],
        "divider_units": 1 if params["divider_impl"] == "iterative_restoring" else params["div_lanes_per_cycle"],
        "divider_bits_per_cycle": 1 if params["divider_impl"] == "iterative_restoring" else None,
        "divider_cycles_per_command": (
            8 * (1 + 1 + 58)
            if params["divider_impl"] == "iterative_restoring"
            else math.ceil(8 / int(params["div_lanes_per_cycle"]))
        ),
        "score_storage": "external_ready_valid_sram",
        "kv_replay": "external_ready_valid_stream",
        "read_outstanding": 1,
        "exp_sum_bits": 33,
        "weighted_numerator_bits": 41,
    }
    (out_dir / "attention_two_pass_stream_manifest.json").write_text(
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
