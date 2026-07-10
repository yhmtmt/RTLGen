#!/usr/bin/env python3
"""Generate a bounded exact two-pass score32 attention engine."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.rtlgen.gen_attention_separated_cluster import _producer_module


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(config: dict[str, Any]) -> dict[str, int]:
    if not str(config.get("top_name") or "").strip():
        raise SystemExit("config top_name must not be empty")
    body = config.get("attention_two_pass")
    if not isinstance(body, dict):
        raise SystemExit("config must contain attention_two_pass object")
    expected = {
        "row_elems": 8,
        "head_dim": 8,
        "value_dim": 8,
        "score_bits": 32,
        "weight_bits": 16,
        "input_frac_bits": 28,
        "exp_bucket_shift": 20,
    }
    params = {key: int(body.get(key, value)) for key, value in expected.items()}
    for key, value in expected.items():
        if params[key] != value:
            raise SystemExit(f"attention_two_pass.{key} must be {value}")
    block_count = int(body.get("block_count", 4))
    if block_count < 2 or block_count > 16 or block_count & (block_count - 1):
        raise SystemExit("attention_two_pass.block_count must be a power of two in [2, 16]")
    params["block_count"] = block_count
    body.update(params)
    return params


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _top(*, top_name: str, params: dict[str, int]) -> str:
    block_count = params["block_count"]
    index_bits = _clog2(block_count + 1)
    max_bucket = 8 << (params["input_frac_bits"] - params["exp_bucket_shift"])
    bucket_scale = float(1 << params["exp_bucket_shift"]) / float(1 << params["input_frac_bits"])
    exp_cases = "\n".join(
        f"      32'd{bucket}: exp_lut = 16'd{max(1, int(math.exp(-(bucket * bucket_scale)) * 65535 + 0.5))};"
        for bucket in range(max_bucket + 1)
    )
    producer_name = f"{top_name}_producer"
    producer = _producer_module(
        module_name=producer_name,
        row_elems=8,
        head_dim=8,
        value_dim=8,
        score_bits=32,
        score_frac_bits=20,
    )
    reset_numerators = "\n".join(f"      numerator_accum[{lane}] <= 41'sd0;" for lane in range(8))
    clear_numerators = "\n".join(f"          numerator_accum[{lane}] <= 41'sd0;" for lane in range(8))
    replay_lane_init = "\n".join(f"        block_numerator[{lane}] = 41'sd0;" for lane in range(8))
    numerator_next = "\n".join(
        f"        numerator_next[{lane}] = numerator_accum[{lane}] + block_numerator[{lane}];" for lane in range(8)
    )
    numerator_store = "\n".join(f"          numerator_accum[{lane}] <= numerator_next[{lane}];" for lane in range(8))
    final_values = "\n".join(
        f"""          if (numerator_next[{lane}] < 0) begin
            numerator_magnitude = (~numerator_next[{lane}]) + 1'b1;
            final_magnitude = (numerator_magnitude * 17'd65535) + (sum_next >> 1);
            final_quotient = final_magnitude / sum_next;
            result_value[({lane} * 40) +: 40] <= (~final_quotient) + 1'b1;
          end else begin
            numerator_magnitude = numerator_next[{lane}];
            final_magnitude = (numerator_magnitude * 17'd65535) + (sum_next >> 1);
            final_quotient = final_magnitude / sum_next;
            result_value[({lane} * 40) +: 40] <= final_quotient;
          end"""
        for lane in range(8)
    )
    return producer + f"""
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         command_valid,
    output wire         command_ready,
    input  wire [15:0]  command_id,
    input  wire [31:0]  command_seed,
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
  localparam integer BLOCK_COUNT = {block_count};
  localparam integer INDEX_W = {index_bits};
  localparam [1:0] IDLE = 2'd0, FILL = 2'd1, REPLAY = 2'd2, HOLD = 2'd3;

  reg [1:0] state;
  reg [15:0] active_command_id;
  reg [31:0] active_seed;
  reg [INDEX_W-1:0] issue_index;
  reg [INDEX_W-1:0] stored_count;
  reg [INDEX_W-1:0] replay_index;
  reg signed [31:0] global_max;
  reg [32:0] exp_sum_accum;
  reg signed [40:0] numerator_accum [0:7];
  reg signed [31:0] score_mem [0:(BLOCK_COUNT*8)-1];
  reg signed [7:0] value_mem [0:(BLOCK_COUNT*64)-1];

  wire producer_payload_valid;
  wire [15:0] producer_payload_command_id;
  wire [255:0] producer_payload_score_row;
  wire [511:0] producer_payload_value_matrix;
  wire producer_load = state == FILL && issue_index < BLOCK_COUNT && !producer_payload_valid;
  wire producer_pop = state == FILL && producer_payload_valid;
  wire [15:0] producer_command_id = active_command_id + issue_index;
  wire [31:0] producer_seed = active_seed ^ (issue_index * 32'h9e37_79b9);

  integer row_idx;
  integer dim_idx;
  integer mem_idx;
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

  assign command_ready = state == IDLE;

  function automatic [15:0] exp_lut;
    input [31:0] bucket;
    begin
      case (bucket)
{exp_cases}
      default: exp_lut = 16'd0;
      endcase
    end
  endfunction

  {producer_name} u_producer (
    .clk(clk), .rst_n(rst_n),
    .load_valid(producer_load),
    .load_command_id(producer_command_id),
    .load_seed(producer_seed),
    .pop_valid(producer_pop),
    .payload_valid(producer_payload_valid),
    .payload_command_id(producer_payload_command_id),
    .payload_score_row(producer_payload_score_row),
    .payload_value_matrix(producer_payload_value_matrix)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      active_command_id <= 16'd0;
      active_seed <= 32'd0;
      issue_index <= {{INDEX_W{{1'b0}}}};
      stored_count <= {{INDEX_W{{1'b0}}}};
      replay_index <= {{INDEX_W{{1'b0}}}};
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
{reset_numerators}
    end else begin
      cycle_count <= cycle_count + 1'b1;
      if (state == IDLE && command_valid) begin
        state <= FILL;
        active_command_id <= command_id;
        active_seed <= command_seed;
        issue_index <= {{INDEX_W{{1'b0}}}};
        stored_count <= {{INDEX_W{{1'b0}}}};
        global_max <= -32'sh8000_0000;
        accepted_count <= accepted_count + 1'b1;
      end

      if (producer_load) begin
        issue_index <= issue_index + 1'b1;
      end

      if (producer_pop) begin
        block_max = $signed(producer_payload_score_row[0 +: 32]);
        for (row_idx = 0; row_idx < 8; row_idx = row_idx + 1) begin
          score_lane = $signed(producer_payload_score_row[(row_idx * 32) +: 32]);
          score_mem[(stored_count * 8) + row_idx] <= score_lane;
          if (score_lane > block_max) block_max = score_lane;
          for (dim_idx = 0; dim_idx < 8; dim_idx = dim_idx + 1) begin
            value_mem[(stored_count * 64) + (row_idx * 8) + dim_idx]
                <= $signed(producer_payload_value_matrix[((row_idx * 8 + dim_idx) * 8) +: 8]);
          end
        end
        if (stored_count == 0 || block_max > global_max) global_max <= block_max;
        if (stored_count + 1'b1 == BLOCK_COUNT) begin
          state <= REPLAY;
          replay_index <= {{INDEX_W{{1'b0}}}};
          exp_sum_accum <= 33'd0;
{clear_numerators}
        end
        stored_count <= stored_count + 1'b1;
      end

      if (state == REPLAY) begin
        block_sum = 20'd0;
{replay_lane_init}
        for (row_idx = 0; row_idx < 8; row_idx = row_idx + 1) begin
          score_lane = score_mem[(replay_index * 8) + row_idx];
          delta_score = global_max - score_lane;
          if (delta_score < 0) delta_score = 32'sd0;
          exp_bucket = (delta_score + 32'd524288) >> 20;
          exp_weight = exp_lut(exp_bucket);
          block_sum = block_sum + exp_weight;
          for (dim_idx = 0; dim_idx < 8; dim_idx = dim_idx + 1) begin
            value_lane = value_mem[(replay_index * 64) + (row_idx * 8) + dim_idx];
            block_numerator[dim_idx] = block_numerator[dim_idx]
                + ($signed(value_lane) * $signed({{1'b0, exp_weight}}));
          end
        end
        sum_next = exp_sum_accum + block_sum;
{numerator_next}
        if (replay_index + 1'b1 == BLOCK_COUNT) begin
          state <= HOLD;
          result_valid <= 1'b1;
          result_command_id <= active_command_id;
          result_global_max <= global_max;
          result_exp_sum <= sum_next;
{final_values}
        end else begin
          replay_index <= replay_index + 1'b1;
          exp_sum_accum <= sum_next;
{numerator_store}
        end
      end

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
        "block_count": params["block_count"],
        "row_elems": 8,
        "context_tokens_bounded": params["block_count"] * 8,
        "exp_sum_bits": 33,
        "weighted_numerator_bits": 41,
        "result_value_bits": 40,
        "score_store": "bounded_internal_register_reference",
        "passes": ["qk_score_store_global_max", "score_value_replay_exp_sum_weighted_numerator_final_divide"],
        "remaining_physical_abstraction": "replace bounded register store with measured score-SRAM ports",
    }
    (out_dir / "attention_two_pass_manifest.json").write_text(
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
