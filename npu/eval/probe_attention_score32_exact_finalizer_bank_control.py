#!/usr/bin/env python3
"""Probe standalone exact finalizer bank-control RTL against the banked service model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_finalizer_bank_control import generate as generate_control
from npu.sim.perf.attention_exact_partial import (
    ExactFinalizedBeat,
    ExactPartialBeat,
    HEAD_ID_BITS,
    PARTIAL_PAYLOAD_BITS,
    VALUE_SLICES,
    exact_finalizer_bank_control_service_manifest,
    finalize_partial_beats,
    merge_balanced_partial_streams,
    pack_final_values,
    pack_numerators,
    partial_stream_from_blocks,
    simulate_exact_banked_finalizer,
)

JsonDict = dict[str, Any]

_ROOT_RE = re.compile(
    r"ROOT_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) root_completed=(\d+) stalls=(\d+) fifo_high_watermark=(\d+) protocol_error=(\d+) cycle=(\d+)"
)


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _commands(heads: int) -> tuple[dict[str, int], ...]:
    return tuple({"command_id": 0x5A00 + head_index, "head_id": head_index} for head_index in range(heads))


def _score_rows(cluster: int, command_index: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            ((cluster * 43 + command_index * 29 + block * 17 + lane * 11) % 255) - 127 + (14 if lane == block else 0)
            for lane in range(8)
        )
        for block in range(3)
    )


def _value_blocks(cluster: int, command_index: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    ((cluster * 59 + command_index * 31 + block * 23 + value_slice * 13 + row * 7 + lane * 5) % 255)
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block in range(3)
    )


def _leaf_stream(cluster: int, *, heads: int) -> tuple[ExactPartialBeat, ...]:
    beats: list[ExactPartialBeat] = []
    for command_index, command in enumerate(_commands(heads)):
        beats.extend(
            partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=_score_rows(cluster, command_index),
                value_blocks=_value_blocks(cluster, command_index),
            )
        )
    return tuple(beats)


def _merged_root_stream(clusters: int, *, heads: int) -> tuple[ExactPartialBeat, ...]:
    return merge_balanced_partial_streams([_leaf_stream(cluster, heads=heads) for cluster in range(clusters)])


def _expected(
    *,
    clusters: int,
    heads: int,
    divider_lanes: int,
    finalizer_banks: int,
    output_ready_pattern: tuple[bool, ...],
) -> dict[str, object]:
    merged = _merged_root_stream(clusters, heads=heads)
    finalized = finalize_partial_beats(merged)
    service = simulate_exact_banked_finalizer(
        merged,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
        output_ready_pattern=output_ready_pattern,
    )
    root_rows = [
        {
            "command_id": beat.command_id,
            "head_id": beat.head_id,
            "slice": beat.slice_index,
            "last": beat.last,
            "value": list(beat.values),
        }
        for beat in finalized
    ]
    return {
        "merged": merged,
        "finalized": finalized,
        "root_rows": root_rows,
        "root_hash": _hash(root_rows),
        "service": service,
    }


def _config(*, divider_lanes: int, finalizer_banks: int) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_finalizer_bank_control_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_finalizer_bank_control": {
            "value_slices": VALUE_SLICES,
            "head_id_bits": HEAD_ID_BITS,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


def _ready_mem_init(pattern: tuple[bool, ...]) -> str:
    return "\n".join(
        f"    root_ready_mem[{index}] = 1'b{1 if ready else 0};" for index, ready in enumerate(pattern)
    )


def _tree_mem_init(stream: tuple[ExactPartialBeat, ...]) -> str:
    lines: list[str] = []
    for index, beat in enumerate(stream):
        lines.append(
            f"    tree_cmd_mem[{index}] = 16'h{beat.command_id:04x}; "
            f"tree_head_mem[{index}] = 5'd{beat.head_id}; "
            f"tree_sum_mem[{index}] = 33'd{beat.exp_sum}; "
            f"tree_slice_mem[{index}] = 4'd{beat.slice_index}; "
            f"tree_last_mem[{index}] = 1'b{1 if beat.last else 0}; "
            f"tree_value_mem[{index}] = 328'h{pack_numerators(beat.numerators):082x};"
        )
    return "\n".join(lines)


def _final_mem_init(finalized: tuple[ExactFinalizedBeat, ...]) -> str:
    lines: list[str] = []
    for index, beat in enumerate(finalized):
        lines.append(
            f"    final_cmd_mem[{index}] = 16'h{beat.command_id:04x}; "
            f"final_head_mem[{index}] = 5'd{beat.head_id}; "
            f"final_slice_mem[{index}] = 4'd{beat.slice_index}; "
            f"final_last_mem[{index}] = 1'b{1 if beat.last else 0}; "
            f"final_value_mem[{index}] = 320'h{pack_final_values(beat.values):080x};"
        )
    return "\n".join(lines)


def _bank_service_logic(banks: int) -> str:
    blocks: list[str] = []
    for bank in range(banks):
        blocks.extend(
            [
                f"      if (bank_busy_cycles[{bank}] != 32'd0) begin",
                f"        bank_busy_cycles[{bank}] <= bank_busy_cycles[{bank}] - 32'd1;",
                f"        if (bank_busy_cycles[{bank}] == 32'd2) begin",
                f"          bank_output_pending[{bank}] <= 1'b1;",
                "        end",
                "      end",
                f"      if (bank_in_valid[{bank}] && bank_in_ready[{bank}]) begin",
                f"        bank_busy_cycles[{bank}] <= 32'd58;",
                f"        bank_output_pending[{bank}] <= 1'b0;",
                f"        bank_output_index[{bank}] <= accepted_index;",
                "      end",
                f"      if (bank_out_valid[{bank}] && bank_out_ready[{bank}]) begin",
                f"        bank_output_pending[{bank}] <= 1'b0;",
                "      end",
            ]
        )
    return "\n".join(blocks)


def _bank_comb_logic(banks: int) -> str:
    blocks: list[str] = []
    for bank in range(banks):
        blocks.extend(
            [
                f"    bank_in_ready[{bank}] = (bank_busy_cycles[{bank}] == 32'd0) && !bank_output_pending[{bank}];",
                f"    bank_out_valid[{bank}] = bank_output_pending[{bank}];",
                f"    bank_out_command_id[({bank} * 16) +: 16] = final_cmd_mem[bank_output_index[{bank}]];",
                f"    bank_out_head_id[({bank} * 5) +: 5] = final_head_mem[bank_output_index[{bank}]];",
                f"    bank_out_slice[({bank} * 4) +: 4] = final_slice_mem[bank_output_index[{bank}]];",
                f"    bank_out_last[{bank}] = final_last_mem[bank_output_index[{bank}]];",
                f"    bank_out_value[({bank} * 320) +: 320] = final_value_mem[bank_output_index[{bank}]];",
            ]
        )
    return "\n".join(blocks)


def _testbench(
    *,
    top_name: str,
    finalizer_banks: int,
    stream: tuple[ExactPartialBeat, ...],
    finalized: tuple[ExactFinalizedBeat, ...],
    output_ready_pattern: tuple[bool, ...],
) -> str:
    total_results = len(stream)
    timeout_cycles = max(4000, (total_results * 70) + 200)
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer BANKS = {finalizer_banks};
  localparam integer TOTAL_RESULTS = {total_results};
  localparam integer ROOT_READY_PATTERN_LEN = {len(output_ready_pattern)};
  reg clk = 0, rst_n = 0;
  reg tree_valid;
  wire tree_ready;
  reg [15:0] tree_command_id;
  reg [4:0] tree_head_id;
  reg [32:0] tree_exp_sum;
  reg [3:0] tree_slice;
  reg tree_last;
  reg [327:0] tree_value;
  wire [BANKS-1:0] bank_in_valid;
  reg [BANKS-1:0] bank_in_ready;
  wire [(BANKS*16)-1:0] bank_in_command_id;
  wire [(BANKS*5)-1:0] bank_in_head_id;
  wire [(BANKS*33)-1:0] bank_in_exp_sum;
  wire [(BANKS*4)-1:0] bank_in_slice;
  wire [BANKS-1:0] bank_in_last;
  wire [(BANKS*328)-1:0] bank_in_value;
  reg [BANKS-1:0] bank_out_valid;
  wire [BANKS-1:0] bank_out_ready;
  reg [(BANKS*16)-1:0] bank_out_command_id;
  reg [(BANKS*5)-1:0] bank_out_head_id;
  reg [(BANKS*4)-1:0] bank_out_slice;
  reg [BANKS-1:0] bank_out_last;
  reg [(BANKS*320)-1:0] bank_out_value;
  wire root_valid;
  reg root_ready;
  reg root_ready_mem [0:ROOT_READY_PATTERN_LEN-1];
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [31:0] cycle_count;
  wire [31:0] tree_accepted_count;
  wire [31:0] root_completed_count;
  wire [31:0] order_fifo_occupancy;
  wire [31:0] order_fifo_high_watermark;
  wire [31:0] order_enqueued_count;
  wire [31:0] order_dequeued_count;
  wire [31:0] dispatch_stall_cycles;
  wire [31:0] dispatch_bank_id;
  wire [31:0] head_bank_id;
  wire [BANKS-1:0] bank_outstanding;
  wire order_protocol_error;
  wire protocol_error;
  reg [15:0] tree_cmd_mem [0:TOTAL_RESULTS-1];
  reg [4:0] tree_head_mem [0:TOTAL_RESULTS-1];
  reg [32:0] tree_sum_mem [0:TOTAL_RESULTS-1];
  reg [3:0] tree_slice_mem [0:TOTAL_RESULTS-1];
  reg tree_last_mem [0:TOTAL_RESULTS-1];
  reg [327:0] tree_value_mem [0:TOTAL_RESULTS-1];
  reg [15:0] final_cmd_mem [0:TOTAL_RESULTS-1];
  reg [4:0] final_head_mem [0:TOTAL_RESULTS-1];
  reg [3:0] final_slice_mem [0:TOTAL_RESULTS-1];
  reg final_last_mem [0:TOTAL_RESULTS-1];
  reg [319:0] final_value_mem [0:TOTAL_RESULTS-1];
  reg [31:0] bank_busy_cycles [0:BANKS-1];
  reg bank_output_pending [0:BANKS-1];
  reg [31:0] bank_output_index [0:BANKS-1];
  integer init_index;
  integer bank_index;
  integer cycle = 0;
  integer issued_index = 0;
  integer accepted_index = 0;
  integer root_seen = 0;

  always #5 clk = ~clk;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .tree_valid(tree_valid),
      .tree_ready(tree_ready),
      .tree_command_id(tree_command_id),
      .tree_head_id(tree_head_id),
      .tree_exp_sum(tree_exp_sum),
      .tree_slice(tree_slice),
      .tree_last(tree_last),
      .tree_value(tree_value),
      .bank_in_valid(bank_in_valid),
      .bank_in_ready(bank_in_ready),
      .bank_in_command_id(bank_in_command_id),
      .bank_in_head_id(bank_in_head_id),
      .bank_in_exp_sum(bank_in_exp_sum),
      .bank_in_slice(bank_in_slice),
      .bank_in_last(bank_in_last),
      .bank_in_value(bank_in_value),
      .bank_out_valid(bank_out_valid),
      .bank_out_ready(bank_out_ready),
      .bank_out_command_id(bank_out_command_id),
      .bank_out_head_id(bank_out_head_id),
      .bank_out_slice(bank_out_slice),
      .bank_out_last(bank_out_last),
      .bank_out_value(bank_out_value),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(cycle_count),
      .tree_accepted_count(tree_accepted_count),
      .root_completed_count(root_completed_count),
      .order_fifo_occupancy(order_fifo_occupancy),
      .order_fifo_high_watermark(order_fifo_high_watermark),
      .order_enqueued_count(order_enqueued_count),
      .order_dequeued_count(order_dequeued_count),
      .dispatch_stall_cycles(dispatch_stall_cycles),
      .dispatch_bank_id(dispatch_bank_id),
      .head_bank_id(head_bank_id),
      .bank_outstanding(bank_outstanding),
      .order_protocol_error(order_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    tree_valid = 1'b0;
    tree_command_id = 16'd0;
    tree_head_id = 5'd0;
    tree_exp_sum = 33'd0;
    tree_slice = 4'd0;
    tree_last = 1'b0;
    tree_value = 328'd0;
    root_ready = root_ready_mem[cycle % ROOT_READY_PATTERN_LEN];
    bank_in_ready = {{BANKS{{1'b0}}}};
    bank_out_valid = {{BANKS{{1'b0}}}};
    bank_out_command_id = {{(BANKS*16){{1'b0}}}};
    bank_out_head_id = {{(BANKS*5){{1'b0}}}};
    bank_out_slice = {{(BANKS*4){{1'b0}}}};
    bank_out_last = {{BANKS{{1'b0}}}};
    bank_out_value = {{(BANKS*320){{1'b0}}}};
    if (issued_index < TOTAL_RESULTS) begin
      tree_valid = 1'b1;
      tree_command_id = tree_cmd_mem[issued_index];
      tree_head_id = tree_head_mem[issued_index];
      tree_exp_sum = tree_sum_mem[issued_index];
      tree_slice = tree_slice_mem[issued_index];
      tree_last = tree_last_mem[issued_index];
      tree_value = tree_value_mem[issued_index];
    end
{_bank_comb_logic(finalizer_banks)}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issued_index <= 0;
      accepted_index <= 0;
      root_seen <= 0;
      for (bank_index = 0; bank_index < BANKS; bank_index = bank_index + 1) begin
        bank_busy_cycles[bank_index] <= 32'd0;
        bank_output_pending[bank_index] <= 1'b0;
        bank_output_index[bank_index] <= 32'd0;
      end
    end else begin
      cycle <= cycle + 1;
      if (tree_valid && tree_ready) begin
        issued_index <= issued_index + 1;
        accepted_index <= accepted_index + 1;
      end
{_bank_service_logic(finalizer_banks)}
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        root_seen <= root_seen + 1;
        if (root_seen + 1 == TOTAL_RESULTS) begin
          $display("SUMMARY outputs=%0d root_completed=%0d stalls=%0d fifo_high_watermark=%0d protocol_error=%0d cycle=%0d",
                   root_seen + 1, root_completed_count + 1, dispatch_stall_cycles, order_fifo_high_watermark, protocol_error, cycle);
          #1 $finish;
        end
      end
      if (cycle > {timeout_cycles}) $fatal(1, "timeout");
    end
  end

  initial begin
    for (init_index = 0; init_index < TOTAL_RESULTS; init_index = init_index + 1) begin
      tree_cmd_mem[init_index] = 16'd0;
      tree_head_mem[init_index] = 5'd0;
      tree_sum_mem[init_index] = 33'd0;
      tree_slice_mem[init_index] = 4'd0;
      tree_last_mem[init_index] = 1'b0;
      tree_value_mem[init_index] = 328'd0;
      final_cmd_mem[init_index] = 16'd0;
      final_head_mem[init_index] = 5'd0;
      final_slice_mem[init_index] = 4'd0;
      final_last_mem[init_index] = 1'b0;
      final_value_mem[init_index] = 320'd0;
    end
{_ready_mem_init(output_ready_pattern)}
{_tree_mem_init(stream)}
{_final_mem_init(finalized)}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def build_report(
    *,
    clusters: int = 16,
    heads: int = 32,
    divider_lanes: int = 8,
    finalizer_banks: int = 59,
    output_ready_pattern: tuple[bool, ...] = (True,),
) -> JsonDict:
    expected = _expected(
        clusters=clusters,
        heads=heads,
        divider_lanes=divider_lanes,
        finalizer_banks=finalizer_banks,
        output_ready_pattern=output_ready_pattern,
    )
    config = _config(divider_lanes=divider_lanes, finalizer_banks=finalizer_banks)
    with tempfile.TemporaryDirectory(prefix="score32_exact_finalizer_bank_control_probe_") as td:
        temp_dir = Path(td)
        rtl_dir = temp_dir / "rtl"
        tb_path = temp_dir / "tb.v"
        sim_path = temp_dir / "sim.out"
        generate_control(config, rtl_dir)
        tb_path.write_text(
            _testbench(
                top_name=str(config["top_name"]),
                finalizer_banks=finalizer_banks,
                stream=expected["merged"],
                finalized=expected["finalized"],
                output_ready_pattern=output_ready_pattern,
            ),
            encoding="utf-8",
        )
        compile_result = subprocess.run(
            [_tool("iverilog"), "-g2012", "-o", str(sim_path), str(rtl_dir / "top.v"), str(tb_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if compile_result.returncode != 0:
            raise RuntimeError(compile_result.stderr)
        sim_result = subprocess.run(
            [_tool("vvp"), str(sim_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if sim_result.returncode != 0:
            raise RuntimeError(sim_result.stderr)

    observed_rows: list[dict[str, int | list[int] | bool]] = []
    summary: dict[str, int] | None = None
    for line in sim_result.stdout.splitlines():
        root_match = _ROOT_RE.search(line)
        if root_match is not None:
            packed = int(root_match.group(5), 16)
            values: list[int] = []
            for lane in range(8):
                raw = (packed >> (lane * 40)) & ((1 << 40) - 1)
                if raw & (1 << 39):
                    raw -= 1 << 40
                values.append(raw)
            observed_rows.append(
                {
                    "command_id": int(root_match.group(1)),
                    "head_id": int(root_match.group(2)),
                    "slice": int(root_match.group(3)),
                    "last": bool(int(root_match.group(4))),
                    "value": values,
                }
            )
            continue
        summary_match = _SUMMARY_RE.search(line)
        if summary_match is not None:
            summary = {
                "outputs": int(summary_match.group(1)),
                "root_completed": int(summary_match.group(2)),
                "dispatch_stall_cycles": int(summary_match.group(3)),
                "order_fifo_high_watermark": int(summary_match.group(4)),
                "protocol_error": int(summary_match.group(5)),
                "cycle": int(summary_match.group(6)),
            }

    if summary is None:
        raise RuntimeError("standalone bank-control probe did not emit SUMMARY")
    observed_hash = _hash(observed_rows)
    expected_hash = str(expected["root_hash"])
    service = dict(expected["service"])
    report: JsonDict = {
        "config": config,
        "service_contract": exact_finalizer_bank_control_service_manifest(
            heads=heads,
            divider_lanes=divider_lanes,
            finalizer_banks=finalizer_banks,
        ),
        "expected_service": service,
        "observed_root_hash": observed_hash,
        "expected_root_hash": expected_hash,
        "outputs": summary["outputs"],
        "root_completed_count": summary["root_completed"],
        "dispatch_stall_cycles": summary["dispatch_stall_cycles"],
        "order_fifo_high_watermark": summary["order_fifo_high_watermark"],
        "protocol_error": bool(summary["protocol_error"]),
        "cycle": summary["cycle"],
        "passed": observed_hash == expected_hash
        and summary["dispatch_stall_cycles"] == int(service["dispatch_stall_cycles"])
        and not bool(summary["protocol_error"]),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clusters", type=int, default=16)
    parser.add_argument("--heads", type=int, default=32)
    parser.add_argument("--divider-lanes", type=int, default=8)
    parser.add_argument("--finalizer-banks", type=int, default=59)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        clusters=args.clusters,
        heads=args.heads,
        divider_lanes=args.divider_lanes,
        finalizer_banks=args.finalizer_banks,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
