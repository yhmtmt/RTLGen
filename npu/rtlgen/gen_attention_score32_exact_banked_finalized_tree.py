#!/usr/bin/env python3
"""Generate a radix-2 exact-reduction tree with ordered banked root finalizers."""

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

from npu.rtlgen.gen_attention_score32_exact_partial_tree import generate as generate_tree
from npu.rtlgen.gen_attention_score32_online_state_merge import (
    FACTORED_H33_L64_MUL_EXACT,
    LEGACY_MONOLITHIC_LUT_EXACT,
)
from npu.rtlgen.gen_attention_score32_exact_root_finalizer import generate as generate_finalizer
from npu.sim.perf.attention_exact_partial import (
    FINAL_LINK_BITS,
    FINAL_PAYLOAD_BITS,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_banked_finalized_tree_service_manifest,
)

JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get("attention_score32_exact_banked_finalized_tree")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_exact_banked_finalized_tree")

    clusters = int(body.get("clusters", 16))
    radix = int(body.get("radix", 2))
    value_slices = int(body.get("value_slices", 16))
    head_id_bits = int(body.get("head_id_bits", 5))
    divider_lanes = int(body.get("divider_lanes", 8))
    finalizer_banks = int(body.get("finalizer_banks", 1))
    exp_scale_impl = str(body.get("exp_scale_impl", LEGACY_MONOLITHIC_LUT_EXACT)).strip()
    if clusters < 2 or clusters > 16 or (clusters & (clusters - 1)):
        raise SystemExit("clusters must be a power of two in [2, 16]")
    if radix != 2:
        raise SystemExit("banked exact finalized tree only implements radix=2")
    if value_slices < 1 or value_slices > 16 or (value_slices & (value_slices - 1)):
        raise SystemExit("value_slices must be a power of two in [1, 16]")
    if head_id_bits < 1 or head_id_bits > 8:
        raise SystemExit("head_id_bits must be in [1, 8]")
    if divider_lanes not in {1, 2, 4, 8}:
        raise SystemExit("divider_lanes must be one of 1, 2, 4, 8")
    if finalizer_banks < 1 or finalizer_banks > 64:
        raise SystemExit("finalizer_banks must be in [1, 64]")
    return {
        "top_name": top_name,
        "clusters": clusters,
        "radix": radix,
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
        "exp_scale_impl": exp_scale_impl,
    }


def _bank_literal(index: int, width: int) -> str:
    return f"{width}'d{index}"


def _wrap_increment_fn(*, name: str, width: int, limit: int) -> str:
    return f"""  function automatic [{width - 1}:0] {name};
    input [{width - 1}:0] value;
    begin
      if (value == {width}'d{limit - 1}) begin
        {name} = {width}'d0;
      end else begin
        {name} = value + {width}'d1;
      end
    end
  endfunction
"""


def _zext_expr(*, pad_expr: str, signal_expr: str) -> str:
    return "{{(" + pad_expr + "){1'b0}}, " + signal_expr + "}"


def _dispatch_case(*, banks: int, bank_id_bits: int) -> str:
    lines = ["  always @* begin", "    dispatch_bank_in_ready_r = 1'b0;"]
    lines.append("    case (dispatch_bank_q)")
    for bank in range(banks):
        lines.append(
            f"      {_bank_literal(bank, bank_id_bits)}: begin "
            f"dispatch_bank_in_ready_r = bank_in_ready_w[{bank}]; end"
        )
    lines.append("      default: begin dispatch_bank_in_ready_r = 1'b0; end")
    lines.append("    endcase")
    lines.append("  end")
    return "\n".join(lines)


def _root_mux_case(*, banks: int, bank_id_bits: int, head_id_bits: int, slice_bits: int) -> str:
    lines = [
        "  always @* begin",
        "    root_valid_r = 1'b0;",
        "    root_command_id_r = 16'd0;",
        f"    root_head_id_r = {{{head_id_bits}{{1'b0}}}};",
        f"    root_slice_r = {{{slice_bits}{{1'b0}}}};",
        "    root_last_r = 1'b0;",
        "    root_value_r = 320'd0;",
        "    head_bank_outstanding_r = 1'b0;",
        "    case (order_fifo_head_bank_id_w)",
    ]
    for bank in range(banks):
        lines.extend(
            [
                f"      {_bank_literal(bank, bank_id_bits)}: begin",
                f"        root_valid_r = bank_out_valid_w[{bank}];",
                f"        root_command_id_r = bank_out_command_id_w[{bank}];",
                f"        root_head_id_r = bank_out_head_id_w[{bank}];",
                f"        root_slice_r = bank_out_slice_w[{bank}];",
                f"        root_last_r = bank_out_last_w[{bank}];",
                f"        root_value_r = bank_out_value_w[{bank}];",
                f"        head_bank_outstanding_r = bank_outstanding_q[{bank}];",
                "      end",
            ]
        )
    lines.append("      default: begin end")
    lines.append("    endcase")
    lines.append("  end")
    return "\n".join(lines)


def _bank_assigns(*, banks: int, bank_id_bits: int) -> str:
    lines: list[str] = []
    for bank in range(banks):
        lines.append(
            f"  assign bank_issue_w[{bank}] = tree_root_valid && tree_root_ready_w && (dispatch_bank_q == {_bank_literal(bank, bank_id_bits)});"
        )
        lines.append(
            f"  assign bank_out_ready_w[{bank}] = root_ready && order_fifo_has_entry_w && (order_fifo_head_bank_id_w == {_bank_literal(bank, bank_id_bits)});"
        )
    return "\n".join(lines)


def _bank_instances(*, finalizer_top_name: str, banks: int, head_id_bits: int, slice_bits: int) -> str:
    blocks: list[str] = []
    for bank in range(banks):
        blocks.append(
            f"""  {finalizer_top_name} u_finalizer_bank_{bank} (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(bank_issue_w[{bank}]),
      .in_ready(bank_in_ready_w[{bank}]),
      .in_command_id(tree_root_command_id),
      .in_head_id(tree_root_head_id),
      .in_exp_sum(tree_root_exp_sum),
      .in_slice(tree_root_slice),
      .in_last(tree_root_last),
      .in_value(tree_root_value),
      .out_valid(bank_out_valid_w[{bank}]),
      .out_ready(bank_out_ready_w[{bank}]),
      .out_command_id(bank_out_command_id_w[{bank}]),
      .out_head_id(bank_out_head_id_w[{bank}]),
      .out_slice(bank_out_slice_w[{bank}]),
      .out_last(bank_out_last_w[{bank}]),
      .out_value(bank_out_value_w[{bank}]),
      .accepted_count(bank_accepted_count_w[{bank}]),
      .completed_count(bank_completed_count_w[{bank}]),
      .cycle_count(bank_cycle_count_w[{bank}]),
      .protocol_error(bank_protocol_error_w[{bank}])
  );"""
        )
    return "\n\n".join(blocks)


def _bank_output_assigns(*, banks: int) -> str:
    return "\n".join(f"  assign bank_protocol_error[{bank}] = bank_protocol_error_w[{bank}];" for bank in range(banks))


def _bank_valid_error_checks(*, banks: int) -> str:
    lines: list[str] = []
    for bank in range(banks):
        lines.append(
            f"      if (bank_out_valid_w[{bank}] && !bank_outstanding_q[{bank}]) begin\n"
            f"        order_protocol_error_q <= 1'b1;\n"
            f"      end"
        )
    return "\n".join(lines)


def _top_pin_bits(
    *,
    clusters: int,
    head_id_bits: int,
    stages: int,
    nodes: int,
    slice_bits: int,
    banks: int,
) -> int:
    leaf_bits = clusters * (1 + 16 + head_id_bits + 32 + 33 + slice_bits + 1 + PARTIAL_PAYLOAD_BITS + 1)
    root_bits = 1 + 1 + 16 + head_id_bits + slice_bits + 1 + FINAL_PAYLOAD_BITS
    monitor_bits = (
        32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + 32
        + (nodes * 32)
        + (stages * 32)
        + nodes
        + stages
        + banks
        + banks
        + 4
    )
    return 2 + leaf_bits + root_bits + monitor_bits


def _top(
    *,
    top_name: str,
    tree_top_name: str,
    finalizer_top_name: str,
    clusters: int,
    value_slices: int,
    head_id_bits: int,
    divider_lanes: int,
    finalizer_banks: int,
) -> str:
    slice_bits = _clog2(value_slices)
    node_count = clusters - 1
    stage_count = int(math.log2(clusters))
    bank_id_bits = _clog2(finalizer_banks)
    fifo_count_bits = _clog2(finalizer_banks + 1)
    dispatch_case = _dispatch_case(banks=finalizer_banks, bank_id_bits=bank_id_bits)
    root_mux_case = _root_mux_case(
        banks=finalizer_banks,
        bank_id_bits=bank_id_bits,
        head_id_bits=head_id_bits,
        slice_bits=slice_bits,
    )
    bank_assigns = _bank_assigns(banks=finalizer_banks, bank_id_bits=bank_id_bits)
    bank_instances = _bank_instances(
        finalizer_top_name=finalizer_top_name,
        banks=finalizer_banks,
        head_id_bits=head_id_bits,
        slice_bits=slice_bits,
    )
    bank_output_assigns = _bank_output_assigns(banks=finalizer_banks)
    bank_valid_error_checks = _bank_valid_error_checks(banks=finalizer_banks)
    order_fifo_count_zext = _zext_expr(pad_expr="32-ORDER_FIFO_COUNT_BITS", signal_expr="order_fifo_count_q")
    dispatch_bank_zext = _zext_expr(pad_expr="32-BANK_ID_BITS", signal_expr="dispatch_bank_q")
    head_bank_zext = _zext_expr(pad_expr="32-BANK_ID_BITS", signal_expr="order_fifo_head_bank_id_w")
    fifo_zero_literal = f"{fifo_count_bits}'d0"
    fifo_one_literal = f"{fifo_count_bits}'d1"
    fifo_full_literal = f"{fifo_count_bits}'d{finalizer_banks}"
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{clusters - 1}:0] leaf_valid,
    output wire [{clusters - 1}:0] leaf_ready,
    input  wire [{clusters * 16 - 1}:0] leaf_command_id,
    input  wire [{clusters * head_id_bits - 1}:0] leaf_head_id,
    input  wire [{clusters * 32 - 1}:0] leaf_global_max,
    input  wire [{clusters * 33 - 1}:0] leaf_exp_sum,
    input  wire [{clusters * slice_bits - 1}:0] leaf_slice,
    input  wire [{clusters - 1}:0] leaf_last,
    input  wire [{clusters * PARTIAL_PAYLOAD_BITS - 1}:0] leaf_value,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [15:0]  root_command_id,
    output wire [{head_id_bits - 1}:0] root_head_id,
    output wire [{slice_bits - 1}:0] root_slice,
    output wire         root_last,
    output wire [319:0] root_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  root_completed_count,
    output wire [31:0]  finalizer_accepted_count,
    output wire [31:0]  tree_root_completed_count,
    output wire [31:0]  order_fifo_occupancy,
    output wire [31:0]  order_fifo_high_watermark,
    output wire [31:0]  order_enqueued_count,
    output wire [31:0]  order_dequeued_count,
    output wire [31:0]  dispatch_stall_cycles,
    output wire [31:0]  dispatch_bank_id,
    output wire [31:0]  head_bank_id,
    output wire [{node_count * 32 - 1}:0] node_completed_count,
    output wire [{stage_count * 32 - 1}:0] stage_completed_count,
    output wire [{node_count - 1}:0] node_protocol_error,
    output wire [{stage_count - 1}:0] stage_protocol_error,
    output wire [{finalizer_banks - 1}:0] bank_protocol_error,
    output wire [{finalizer_banks - 1}:0] bank_outstanding,
    output wire         tree_protocol_error,
    output wire         order_protocol_error,
    output wire         finalizer_protocol_error,
    output wire         protocol_error
);
  localparam integer PARTIAL_PAYLOAD_BITS = {PARTIAL_PAYLOAD_BITS};
  localparam integer FINALIZER_BANKS = {finalizer_banks};
  localparam integer BANK_ID_BITS = {bank_id_bits};
  localparam integer ORDER_FIFO_DEPTH = {finalizer_banks};
  localparam integer ORDER_FIFO_COUNT_BITS = {fifo_count_bits};

  wire tree_root_valid;
  wire tree_root_ready;
  wire [15:0] tree_root_command_id;
  wire [{head_id_bits - 1}:0] tree_root_head_id;
  wire signed [31:0] tree_root_global_max;
  wire [32:0] tree_root_exp_sum;
  wire [{slice_bits - 1}:0] tree_root_slice;
  wire tree_root_last;
  wire [327:0] tree_root_value;
  wire [31:0] tree_cycle_count;
  wire [31:0] tree_root_completed_count_w;

  wire bank_issue_w [0:FINALIZER_BANKS-1];
  wire bank_in_ready_w [0:FINALIZER_BANKS-1];
  wire bank_out_valid_w [0:FINALIZER_BANKS-1];
  wire bank_out_ready_w [0:FINALIZER_BANKS-1];
  wire [15:0] bank_out_command_id_w [0:FINALIZER_BANKS-1];
  wire [{head_id_bits - 1}:0] bank_out_head_id_w [0:FINALIZER_BANKS-1];
  wire [{slice_bits - 1}:0] bank_out_slice_w [0:FINALIZER_BANKS-1];
  wire bank_out_last_w [0:FINALIZER_BANKS-1];
  wire [319:0] bank_out_value_w [0:FINALIZER_BANKS-1];
  wire [31:0] bank_accepted_count_w [0:FINALIZER_BANKS-1];
  wire [31:0] bank_completed_count_w [0:FINALIZER_BANKS-1];
  wire [31:0] bank_cycle_count_w [0:FINALIZER_BANKS-1];
  wire bank_protocol_error_w [0:FINALIZER_BANKS-1];

  reg [BANK_ID_BITS-1:0] dispatch_bank_q;
  reg [BANK_ID_BITS-1:0] order_fifo_head_q;
  reg [BANK_ID_BITS-1:0] order_fifo_tail_q;
  reg [BANK_ID_BITS-1:0] order_fifo_mem [0:ORDER_FIFO_DEPTH-1];
  reg [ORDER_FIFO_COUNT_BITS-1:0] order_fifo_count_q;
  reg [FINALIZER_BANKS-1:0] bank_outstanding_q;
  reg [31:0] cycle_count_q;
  reg [31:0] root_completed_count_q;
  reg [31:0] finalizer_accepted_count_q;
  reg [31:0] order_fifo_high_watermark_q;
  reg [31:0] order_enqueued_count_q;
  reg [31:0] order_dequeued_count_q;
  reg [31:0] dispatch_stall_cycles_q;
  reg order_protocol_error_q;
  reg dispatch_bank_in_ready_r;
  reg root_valid_r;
  reg [15:0] root_command_id_r;
  reg [{head_id_bits - 1}:0] root_head_id_r;
  reg [{slice_bits - 1}:0] root_slice_r;
  reg root_last_r;
  reg [319:0] root_value_r;
  reg head_bank_outstanding_r;
  reg [31:0] order_fifo_count_next_r;
  integer bank_index;

{_wrap_increment_fn(name="next_bank_id", width=bank_id_bits, limit=finalizer_banks)}
  wire order_fifo_has_entry_w = (order_fifo_count_q != {fifo_zero_literal});
  wire order_fifo_full_w = (order_fifo_count_q == {fifo_full_literal});
  wire [BANK_ID_BITS-1:0] order_fifo_head_bank_id_w = order_fifo_mem[order_fifo_head_q];
  wire order_fifo_dequeue_fire_w = root_valid_r && root_ready;
  wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;
  wire tree_root_ready_w = dispatch_bank_in_ready_r && order_fifo_enqueue_ready_w;
  wire tree_root_issue_w = tree_root_valid && tree_root_ready_w;
  wire any_bank_protocol_error_w = |bank_protocol_error;
  wire finalizer_protocol_error_w = any_bank_protocol_error_w | order_protocol_error_q;

  assign root_valid = root_valid_r;
  assign root_command_id = root_command_id_r;
  assign root_head_id = root_head_id_r;
  assign root_slice = root_slice_r;
  assign root_last = root_last_r;
  assign root_value = root_value_r;
  assign tree_root_ready = tree_root_ready_w;
  assign cycle_count = cycle_count_q;
  assign root_completed_count = root_completed_count_q;
  assign finalizer_accepted_count = finalizer_accepted_count_q;
  assign tree_root_completed_count = tree_root_completed_count_w;
  assign order_fifo_occupancy = {order_fifo_count_zext};
  assign order_fifo_high_watermark = order_fifo_high_watermark_q;
  assign order_enqueued_count = order_enqueued_count_q;
  assign order_dequeued_count = order_dequeued_count_q;
  assign dispatch_stall_cycles = dispatch_stall_cycles_q;
  assign dispatch_bank_id = {dispatch_bank_zext};
  assign head_bank_id =
      order_fifo_has_entry_w ? {head_bank_zext} : 32'd0;
  assign bank_outstanding = bank_outstanding_q;
  assign order_protocol_error = order_protocol_error_q;
  assign finalizer_protocol_error = finalizer_protocol_error_w;
  assign protocol_error = tree_protocol_error | finalizer_protocol_error_w;

{bank_output_assigns}

{dispatch_case}

{root_mux_case}

{bank_assigns}

  {tree_top_name} u_tree (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid),
      .leaf_ready(leaf_ready),
      .leaf_command_id(leaf_command_id),
      .leaf_head_id(leaf_head_id),
      .leaf_global_max(leaf_global_max),
      .leaf_exp_sum(leaf_exp_sum),
      .leaf_slice(leaf_slice),
      .leaf_last(leaf_last),
      .leaf_value(leaf_value),
      .root_valid(tree_root_valid),
      .root_ready(tree_root_ready),
      .root_command_id(tree_root_command_id),
      .root_head_id(tree_root_head_id),
      .root_global_max(tree_root_global_max),
      .root_exp_sum(tree_root_exp_sum),
      .root_slice(tree_root_slice),
      .root_last(tree_root_last),
      .root_value(tree_root_value),
      .cycle_count(tree_cycle_count),
      .root_completed_count(tree_root_completed_count_w),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .protocol_error(tree_protocol_error)
  );

{bank_instances}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      dispatch_bank_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_head_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_tail_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_count_q <= {{ORDER_FIFO_COUNT_BITS{{1'b0}}}};
      bank_outstanding_q <= {{FINALIZER_BANKS{{1'b0}}}};
      cycle_count_q <= 32'd0;
      root_completed_count_q <= 32'd0;
      finalizer_accepted_count_q <= 32'd0;
      order_fifo_high_watermark_q <= 32'd0;
      order_enqueued_count_q <= 32'd0;
      order_dequeued_count_q <= 32'd0;
      dispatch_stall_cycles_q <= 32'd0;
      order_protocol_error_q <= 1'b0;
      for (bank_index = 0; bank_index < ORDER_FIFO_DEPTH; bank_index = bank_index + 1) begin
        order_fifo_mem[bank_index] <= {{BANK_ID_BITS{{1'b0}}}};
      end
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
      if (tree_root_valid && !tree_root_ready_w) begin
        dispatch_stall_cycles_q <= dispatch_stall_cycles_q + 1'b1;
      end
      if (!order_fifo_has_entry_w && (|bank_outstanding_q)) begin
        order_protocol_error_q <= 1'b1;
      end
{bank_valid_error_checks}
      if (tree_root_issue_w) begin
        finalizer_accepted_count_q <= finalizer_accepted_count_q + 1'b1;
        order_enqueued_count_q <= order_enqueued_count_q + 1'b1;
        if (bank_outstanding_q[dispatch_bank_q]) begin
          order_protocol_error_q <= 1'b1;
        end
        bank_outstanding_q[dispatch_bank_q] <= 1'b1;
        order_fifo_mem[order_fifo_tail_q] <= dispatch_bank_q;
      end
      if (order_fifo_dequeue_fire_w) begin
        root_completed_count_q <= root_completed_count_q + 1'b1;
        order_dequeued_count_q <= order_dequeued_count_q + 1'b1;
        if (!order_fifo_has_entry_w) begin
          order_protocol_error_q <= 1'b1;
        end
        if (!head_bank_outstanding_r) begin
          order_protocol_error_q <= 1'b1;
        end
        bank_outstanding_q[order_fifo_head_bank_id_w] <= 1'b0;
      end

      order_fifo_count_next_r = {order_fifo_count_zext};
      case ({{tree_root_issue_w, order_fifo_dequeue_fire_w}})
        2'b10: begin
          order_fifo_tail_q <= next_bank_id(order_fifo_tail_q);
          order_fifo_count_q <= order_fifo_count_q + {fifo_one_literal};
          order_fifo_count_next_r = {order_fifo_count_zext} + 32'd1;
        end
        2'b01: begin
          order_fifo_head_q <= next_bank_id(order_fifo_head_q);
          order_fifo_count_q <= order_fifo_count_q - {fifo_one_literal};
          order_fifo_count_next_r = {order_fifo_count_zext} - 32'd1;
        end
        2'b11: begin
          order_fifo_head_q <= next_bank_id(order_fifo_head_q);
          order_fifo_tail_q <= next_bank_id(order_fifo_tail_q);
          order_fifo_count_next_r = {order_fifo_count_zext};
        end
        default: begin
          order_fifo_count_next_r = {order_fifo_count_zext};
        end
      endcase
      if (tree_root_issue_w) begin
        dispatch_bank_q <= next_bank_id(dispatch_bank_q);
      end
      if (order_fifo_count_next_r > order_fifo_high_watermark_q) begin
        order_fifo_high_watermark_q <= order_fifo_count_next_r;
      end
    end
  end
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    out_dir.mkdir(parents=True, exist_ok=True)

    tree_top_name = f"{params['top_name']}__partial_tree"
    finalizer_top_name = f"{params['top_name']}__root_finalizer"
    with tempfile.TemporaryDirectory(prefix="score32_exact_banked_finalized_tree_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate_tree(
            {
                "top_name": tree_top_name,
                "attention_score32_exact_partial_tree": {
                    "clusters": int(params["clusters"]),
                    "radix": int(params["radix"]),
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "exp_scale_impl": str(params["exp_scale_impl"]),
                },
            },
            temp_dir / "tree",
        )
        generate_finalizer(
            {
                "top_name": finalizer_top_name,
                "attention_score32_exact_root_finalizer": {
                    "value_slices": int(params["value_slices"]),
                    "head_id_bits": int(params["head_id_bits"]),
                    "divider_lanes": int(params["divider_lanes"]),
                },
            },
            temp_dir / "finalizer",
        )
        tree_rtl = (temp_dir / "tree" / "top.v").read_text(encoding="utf-8")
        finalizer_rtl = (temp_dir / "finalizer" / "top.v").read_text(encoding="utf-8")
        tree_manifest = json.loads(
            (temp_dir / "tree" / "attention_score32_exact_partial_tree_manifest.json").read_text(encoding="utf-8")
        )
        finalizer_manifest = json.loads(
            (temp_dir / "finalizer" / "attention_score32_exact_root_finalizer_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    top_text = _top(
        top_name=str(params["top_name"]),
        tree_top_name=tree_top_name,
        finalizer_top_name=finalizer_top_name,
        clusters=int(params["clusters"]),
        value_slices=int(params["value_slices"]),
        head_id_bits=int(params["head_id_bits"]),
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    (out_dir / "top.v").write_text(tree_rtl + "\n\n" + finalizer_rtl + "\n\n" + top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    clusters = int(params["clusters"])
    banks = int(params["finalizer_banks"])
    node_count = clusters - 1
    stage_count = int(math.log2(clusters))
    slice_bits = _clog2(int(params["value_slices"]))
    bank_id_bits = _clog2(banks)
    service_manifest = exact_banked_finalized_tree_service_manifest(
        clusters=clusters,
        heads=32,
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=banks,
    )
    manifest = {
        "version": 1,
        "top_name": params["top_name"],
        "generator": "npu/rtlgen/gen_attention_score32_exact_banked_finalized_tree.py",
        "semantic_profile": "score32_online_exact_banked_finalized_radix2_tree_v1",
        "clusters": clusters,
        "radix": int(params["radix"]),
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "divider_lanes": int(params["divider_lanes"]),
        "finalizer_banks": banks,
        "exp_scale_impl": str(params["exp_scale_impl"]),
        "tree_stages": stage_count,
        "tree_nodes": node_count,
        "result_interface": "clusters_ready_valid_exact_partial_leaf_streams_to_ordered_banked_exact_finalized_root_stream",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "order_fifo_depth": banks,
        "order_fifo_entry_bits": bank_id_bits,
        "order_fifo_storage_bits": banks * bank_id_bits,
        "order_fifo_count_bits": _clog2(banks + 1),
        "ordering_contract": "single_bank_id_fifo_exact_issue_order_one_beat_per_entry",
        "actual_finalizer_accept_interval_cycles": service_manifest["per_bank_accept_interval_cycles"],
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": True,
        "noc_closure": False,
        "sram_closure": False,
        "macro_eval_excludes_io_pads": True,
        "equivalence_hash": False,
        "service_model": service_manifest,
        "top_pin_estimate_bits": _top_pin_bits(
            clusters=clusters,
            head_id_bits=int(params["head_id_bits"]),
            stages=stage_count,
            nodes=node_count,
            slice_bits=slice_bits,
            banks=banks,
        ),
        "submodule_manifests": {
            "partial_tree": tree_manifest,
            "root_finalizer": finalizer_manifest,
        },
    }
    (out_dir / "attention_score32_exact_banked_finalized_tree_manifest.json").write_text(
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
