#!/usr/bin/env python3
"""Generate standalone ordered bank-dispatch control for exact root finalizers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from npu.sim.perf.attention_exact_partial import (
    FINALIZER_CONTROL_TRANSACTION_ID_BITS,
    HEAD_ID_BITS,
    VALUE_SLICES,
    exact_finalizer_bank_control_service_manifest,
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
    body = config.get("attention_score32_exact_finalizer_bank_control")
    if not top_name or not isinstance(body, dict):
        raise SystemExit("config requires top_name and attention_score32_exact_finalizer_bank_control")
    value_slices = int(body.get("value_slices", VALUE_SLICES))
    head_id_bits = int(body.get("head_id_bits", HEAD_ID_BITS))
    divider_lanes = int(body.get("divider_lanes", 8))
    finalizer_banks = int(body.get("finalizer_banks", 1))
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
        "value_slices": value_slices,
        "head_id_bits": head_id_bits,
        "divider_lanes": divider_lanes,
        "finalizer_banks": finalizer_banks,
    }


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
    lines = ["  always @* begin", "    dispatch_bank_in_ready_r = 1'b0;", "    case (dispatch_bank_q)"]
    for bank in range(banks):
        lines.append(
            f"      {bank_id_bits}'d{bank}: begin dispatch_bank_in_ready_r = bank_in_ready[{bank}]; end"
        )
    lines.append("      default: begin dispatch_bank_in_ready_r = 1'b0; end")
    lines.append("    endcase")
    lines.append("  end")
    return "\n".join(lines)


def _head_return_case(*, banks: int, bank_id_bits: int) -> str:
    lines = [
        "  always @* begin",
        "    head_return_valid_r = 1'b0;",
        "    head_return_transaction_id_r = {TRANSACTION_ID_BITS{1'b0}};",
        "    case (order_fifo_head_bank_id_w)",
    ]
    for bank in range(banks):
        lines.extend(
            [
                f"      {bank_id_bits}'d{bank}: begin",
                f"        head_return_valid_r = bank_out_valid[{bank}];",
                f"        head_return_transaction_id_r = bank_out_transaction_id[({bank} * TRANSACTION_ID_BITS) +: TRANSACTION_ID_BITS];",
                "      end",
            ]
        )
    lines.append("      default: begin end")
    lines.append("    endcase")
    lines.append("  end")
    return "\n".join(lines)


def _bank_issue_assigns(*, banks: int, bank_id_bits: int) -> str:
    lines: list[str] = []
    for bank in range(banks):
        lines.append(
            f"  assign bank_in_valid[{bank}] = tree_issue_w && (dispatch_bank_q == {bank_id_bits}'d{bank});"
        )
        lines.append(
            f"  assign bank_out_ready[{bank}] = root_ready && order_fifo_has_entry_w && (order_fifo_head_bank_id_w == {bank_id_bits}'d{bank});"
        )
        lines.append(
            f"  assign bank_in_transaction_id[({bank} * TRANSACTION_ID_BITS) +: TRANSACTION_ID_BITS] = tree_transaction_id;"
        )
        lines.append(
            f"  assign bank_outstanding[{bank}] = bank_outstanding_q[{bank}];"
        )
    return "\n".join(lines)


def _bank_valid_error_checks(*, banks: int) -> str:
    lines: list[str] = []
    for bank in range(banks):
        lines.append(
            f"      if (bank_out_valid[{bank}] && !bank_outstanding_q[{bank}]) begin\n"
            f"        order_protocol_error_q <= 1'b1;\n"
            f"      end"
        )
    return "\n".join(lines)


def _top_pin_estimate_bits(*, banks: int) -> int:
    transaction_link_bits = 1 + 1 + FINALIZER_CONTROL_TRANSACTION_ID_BITS
    monitor_bits = (10 * 32) + banks + 2
    return 2 + transaction_link_bits + (banks * transaction_link_bits) + (banks * transaction_link_bits) + transaction_link_bits + monitor_bits


def _top(
    *,
    top_name: str,
    value_slices: int,
    head_id_bits: int,
    finalizer_banks: int,
) -> str:
    _ = value_slices
    _ = head_id_bits
    bank_id_bits = _clog2(finalizer_banks)
    fifo_count_bits = _clog2(finalizer_banks + 1)
    dispatch_case = _dispatch_case(banks=finalizer_banks, bank_id_bits=bank_id_bits)
    head_return_case = _head_return_case(banks=finalizer_banks, bank_id_bits=bank_id_bits)
    bank_assigns = _bank_issue_assigns(banks=finalizer_banks, bank_id_bits=bank_id_bits)
    bank_valid_error_checks = _bank_valid_error_checks(banks=finalizer_banks)
    order_fifo_count_zext = _zext_expr(pad_expr="32-ORDER_FIFO_COUNT_BITS", signal_expr="order_fifo_count_q")
    dispatch_bank_zext = _zext_expr(pad_expr="32-BANK_ID_BITS", signal_expr="dispatch_bank_q")
    head_bank_zext = _zext_expr(pad_expr="32-BANK_ID_BITS", signal_expr="order_fifo_head_bank_id_w")
    fifo_zero_literal = f"{fifo_count_bits}'d0"
    fifo_one_literal = f"{fifo_count_bits}'d1"
    fifo_full_literal = f"{fifo_count_bits}'d{finalizer_banks}"
    return f"""// Auto-generated by npu/rtlgen/gen_attention_score32_exact_finalizer_bank_control.py
module {top_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         tree_valid,
    output wire         tree_ready,
    input  wire [{FINALIZER_CONTROL_TRANSACTION_ID_BITS - 1}:0] tree_transaction_id,
    output wire [{finalizer_banks - 1}:0] bank_in_valid,
    input  wire [{finalizer_banks - 1}:0] bank_in_ready,
    output wire [{finalizer_banks * FINALIZER_CONTROL_TRANSACTION_ID_BITS - 1}:0] bank_in_transaction_id,
    input  wire [{finalizer_banks - 1}:0] bank_out_valid,
    output wire [{finalizer_banks - 1}:0] bank_out_ready,
    input  wire [{finalizer_banks * FINALIZER_CONTROL_TRANSACTION_ID_BITS - 1}:0] bank_out_transaction_id,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [{FINALIZER_CONTROL_TRANSACTION_ID_BITS - 1}:0] root_transaction_id,
    output wire [31:0]  cycle_count,
    output wire [31:0]  tree_accepted_count,
    output wire [31:0]  root_completed_count,
    output wire [31:0]  order_fifo_occupancy,
    output wire [31:0]  order_fifo_high_watermark,
    output wire [31:0]  order_enqueued_count,
    output wire [31:0]  order_dequeued_count,
    output wire [31:0]  dispatch_stall_cycles,
    output wire [31:0]  dispatch_bank_id,
    output wire [31:0]  head_bank_id,
    output wire [{finalizer_banks - 1}:0] bank_outstanding,
    output wire         order_protocol_error,
    output wire         protocol_error
);
  localparam integer TRANSACTION_ID_BITS = {FINALIZER_CONTROL_TRANSACTION_ID_BITS};
  localparam integer FINALIZER_BANKS = {finalizer_banks};
  localparam integer BANK_ID_BITS = {bank_id_bits};
  localparam integer ORDER_FIFO_COUNT_BITS = {fifo_count_bits};

  {_wrap_increment_fn(name="next_bank_id", width=bank_id_bits, limit=finalizer_banks)}

  reg [BANK_ID_BITS-1:0] dispatch_bank_q;
  reg [BANK_ID_BITS-1:0] order_fifo_bank_mem [0:FINALIZER_BANKS-1];
  reg [TRANSACTION_ID_BITS-1:0] order_fifo_tid_mem [0:FINALIZER_BANKS-1];
  reg [BANK_ID_BITS-1:0] order_fifo_head_q;
  reg [BANK_ID_BITS-1:0] order_fifo_tail_q;
  reg [ORDER_FIFO_COUNT_BITS-1:0] order_fifo_count_q;
  reg [31:0] cycle_count_q;
  reg [31:0] tree_accepted_count_q;
  reg [31:0] root_completed_count_q;
  reg [31:0] order_fifo_high_watermark_q;
  reg [31:0] order_enqueued_count_q;
  reg [31:0] order_dequeued_count_q;
  reg [31:0] dispatch_stall_cycles_q;
  reg order_protocol_error_q;
  reg [FINALIZER_BANKS-1:0] bank_outstanding_q;
  reg dispatch_bank_in_ready_r;
  reg head_return_valid_r;
  reg [TRANSACTION_ID_BITS-1:0] head_return_transaction_id_r;
  reg [31:0] order_fifo_count_next_r;
  wire order_fifo_has_entry_w = order_fifo_count_q != {fifo_zero_literal};
  wire order_fifo_full_w = order_fifo_count_q == {fifo_full_literal};
  wire [BANK_ID_BITS-1:0] order_fifo_head_bank_id_w =
      order_fifo_has_entry_w ? order_fifo_bank_mem[order_fifo_head_q] : {{BANK_ID_BITS{{1'b0}}}};
  wire [TRANSACTION_ID_BITS-1:0] order_fifo_head_transaction_id_w =
      order_fifo_has_entry_w ? order_fifo_tid_mem[order_fifo_head_q] : {{TRANSACTION_ID_BITS{{1'b0}}}};
  wire order_fifo_dequeue_fire_w = root_valid && root_ready;
  wire order_fifo_enqueue_ready_w = !order_fifo_full_w || order_fifo_dequeue_fire_w;
  wire tree_ready_w = dispatch_bank_in_ready_r && order_fifo_enqueue_ready_w;
  wire tree_issue_w = tree_valid && tree_ready_w;
  wire same_bank_replace_w =
      tree_issue_w && order_fifo_dequeue_fire_w && (dispatch_bank_q == order_fifo_head_bank_id_w);

  assign tree_ready = tree_ready_w;
  assign root_valid = order_fifo_has_entry_w && head_return_valid_r;
  assign root_transaction_id = order_fifo_head_transaction_id_w;
  assign cycle_count = cycle_count_q;
  assign tree_accepted_count = tree_accepted_count_q;
  assign root_completed_count = root_completed_count_q;
  assign order_fifo_occupancy = {order_fifo_count_zext};
  assign order_fifo_high_watermark = order_fifo_high_watermark_q;
  assign order_enqueued_count = order_enqueued_count_q;
  assign order_dequeued_count = order_dequeued_count_q;
  assign dispatch_stall_cycles = dispatch_stall_cycles_q;
  assign dispatch_bank_id = {dispatch_bank_zext};
  assign head_bank_id = order_fifo_has_entry_w ? {head_bank_zext} : 32'd0;
  assign order_protocol_error = order_protocol_error_q;
  assign protocol_error = order_protocol_error_q;

{dispatch_case}

{head_return_case}

{bank_assigns}

  integer init_index;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      dispatch_bank_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_head_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_tail_q <= {{BANK_ID_BITS{{1'b0}}}};
      order_fifo_count_q <= {fifo_zero_literal};
      cycle_count_q <= 32'd0;
      tree_accepted_count_q <= 32'd0;
      root_completed_count_q <= 32'd0;
      order_fifo_high_watermark_q <= 32'd0;
      order_enqueued_count_q <= 32'd0;
      order_dequeued_count_q <= 32'd0;
      dispatch_stall_cycles_q <= 32'd0;
      order_protocol_error_q <= 1'b0;
      bank_outstanding_q <= {{FINALIZER_BANKS{{1'b0}}}};
      for (init_index = 0; init_index < FINALIZER_BANKS; init_index = init_index + 1) begin
        order_fifo_bank_mem[init_index] <= {{BANK_ID_BITS{{1'b0}}}};
        order_fifo_tid_mem[init_index] <= {{TRANSACTION_ID_BITS{{1'b0}}}};
      end
    end else begin
      cycle_count_q <= cycle_count_q + 1'b1;
{bank_valid_error_checks}
      if (tree_valid && !tree_ready_w) begin
        dispatch_stall_cycles_q <= dispatch_stall_cycles_q + 1'b1;
      end
      if (tree_issue_w) begin
        order_fifo_bank_mem[order_fifo_tail_q] <= dispatch_bank_q;
        order_fifo_tid_mem[order_fifo_tail_q] <= tree_transaction_id;
        bank_outstanding_q[dispatch_bank_q] <= 1'b1;
        tree_accepted_count_q <= tree_accepted_count_q + 1'b1;
        order_enqueued_count_q <= order_enqueued_count_q + 1'b1;
        if (bank_outstanding_q[dispatch_bank_q] && !same_bank_replace_w) begin
          order_protocol_error_q <= 1'b1;
        end
      end
      if (order_fifo_dequeue_fire_w) begin
        if (!order_fifo_has_entry_w) begin
          order_protocol_error_q <= 1'b1;
        end
        if (head_return_transaction_id_r != order_fifo_head_transaction_id_w) begin
          order_protocol_error_q <= 1'b1;
        end
        if (!same_bank_replace_w) begin
          bank_outstanding_q[order_fifo_head_bank_id_w] <= 1'b0;
        end
        root_completed_count_q <= root_completed_count_q + 1'b1;
        order_dequeued_count_q <= order_dequeued_count_q + 1'b1;
      end

      case ({{tree_issue_w, order_fifo_dequeue_fire_w}})
        2'b00: begin
          order_fifo_count_next_r = {order_fifo_count_zext};
        end
        2'b01: begin
          order_fifo_head_q <= next_bank_id(order_fifo_head_q);
          order_fifo_count_q <= order_fifo_count_q - {fifo_one_literal};
          order_fifo_count_next_r = {order_fifo_count_zext} - 32'd1;
        end
        2'b10: begin
          order_fifo_tail_q <= next_bank_id(order_fifo_tail_q);
          order_fifo_count_q <= order_fifo_count_q + {fifo_one_literal};
          order_fifo_count_next_r = {order_fifo_count_zext} + 32'd1;
        end
        default: begin
          order_fifo_head_q <= next_bank_id(order_fifo_head_q);
          order_fifo_tail_q <= next_bank_id(order_fifo_tail_q);
          order_fifo_count_next_r = {order_fifo_count_zext};
        end
      endcase
      if (tree_issue_w) begin
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
    top_text = _top(
        top_name=str(params["top_name"]),
        value_slices=int(params["value_slices"]),
        head_id_bits=int(params["head_id_bits"]),
        finalizer_banks=int(params["finalizer_banks"]),
    )
    (out_dir / "top.v").write_text(top_text, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    banks = int(params["finalizer_banks"])
    bank_id_bits = _clog2(banks)
    service_manifest = exact_finalizer_bank_control_service_manifest(
        heads=32,
        divider_lanes=int(params["divider_lanes"]),
        finalizer_banks=banks,
    )
    manifest = {
        "version": 1,
        "top_name": params["top_name"],
        "generator": "npu/rtlgen/gen_attention_score32_exact_finalizer_bank_control.py",
        "semantic_profile": "score32_online_exact_finalizer_bank_control_v1",
        "value_slices": int(params["value_slices"]),
        "head_id_bits": int(params["head_id_bits"]),
        "divider_lanes": int(params["divider_lanes"]),
        "finalizer_banks": banks,
        "result_interface": "tree_transaction_issue_to_ordered_banked_transaction_retire_stream",
        "transaction_id_bits": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "order_fifo_depth": banks,
        "order_fifo_entry_bits": bank_id_bits,
        "order_fifo_storage_bits": banks * bank_id_bits,
        "dispatch_policy": "round_robin_no_alternate_ready_scan",
        "ordering_contract": "single_bank_id_fifo_exact_issue_order_one_transaction_per_entry",
        "control_only_embodied": True,
        "bank_arithmetic_embodied": False,
        "tree_payload_fanout_embodied": False,
        "root_payload_mux_embodied": False,
        "equivalence_hash": False,
        "macro_eval_excludes_io_pads": True,
        "exact_service_model_cycle_equivalence": True,
        "service_model": service_manifest,
        "top_pin_estimate_bits": _top_pin_estimate_bits(banks=banks),
    }
    (out_dir / "attention_score32_exact_finalizer_bank_control_manifest.json").write_text(
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
