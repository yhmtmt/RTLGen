#!/usr/bin/env python3
"""Prove exact functional and schedule equivalence for separated attention RTL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

from npu.rtlgen.gen_attention_separated_cluster import _validate, _write_top
from npu.sim.perf.attention_separated import (
    AttentionSeparatedCommand,
    default_commands,
    scenario_names,
    simulate,
    unpack_signed,
    unpack_unsigned,
)

JsonDict = dict[str, Any]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required RTL simulation tool is unavailable: {name}")


def _config(*, top_name: str, producer_count: int, consumer_count: int) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_separated_cluster": {
            "producer_count": producer_count,
            "consumer_count": consumer_count,
            "row_elems": 8,
            "head_dim": 8,
            "value_dim": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "input_frac_bits": 28,
            "exp_bucket_shift": 20,
        },
    }


def _testbench(
    *, top_name: str, producer_count: int, consumer_count: int, commands: list[AttentionSeparatedCommand], scenario: str
) -> str:
    command_init = "\n".join(
        f"    command_ids[{index}] = 16'h{command.command_id & 0xFFFF:04x};\n"
        f"    command_seeds[{index}] = 32'h{command.seed & 0xFFFFFFFF:08x};"
        for index, command in enumerate(commands)
    )
    dispatch_id_cases = "\n".join(
        f"      {index}: dispatch_command_id = dut.producer_{index}_payload_command_id;"
        for index in range(producer_count)
    )
    full_mask = (1 << consumer_count) - 1
    enable_logic = {
        "always_ready": f"consumer_enable = {consumer_count}'h{full_mask:x};",
        "result_backpressure": f"consumer_enable = {consumer_count}'h{full_mask:x};",
        "all_consumers_blocked_temporarily": (
            f"consumer_enable = ((cycle >= 6) && (cycle < 10)) ? {consumer_count}'h0 : "
            f"{consumer_count}'h{full_mask:x};"
        ),
        "intermittent_consumer_stall": "\n".join(
            [f"consumer_enable = {consumer_count}'h0;"]
            + [f"if (((cycle + {index}) % 4) != 1) consumer_enable[{index}] = 1'b1;" for index in range(consumer_count)]
        ),
    }[scenario]
    ready_logic = (
        "result_ready = !(((cycle >= 9) && (cycle < 13)) || ((cycle % 6) == 4));"
        if scenario == "result_backpressure"
        else "result_ready = 1'b1;"
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMAND_COUNT = {len(commands)};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [31:0] command_seed;
  reg [{consumer_count - 1}:0] consumer_enable;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire [255:0] result_score_row;
  wire [127:0] result_weights;
  wire [319:0] result_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  reg [15:0] command_ids [0:COMMAND_COUNT-1];
  reg [31:0] command_seeds [0:COMMAND_COUNT-1];
  integer send_index;
  integer cycle;
  reg [15:0] dispatch_command_id;

  always #5 clk = ~clk;

  {top_name} dut (
    .clk(clk), .rst_n(rst_n),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_id(command_id), .command_seed(command_seed),
    .consumer_enable(consumer_enable),
    .result_valid(result_valid), .result_ready(result_ready),
    .result_command_id(result_command_id), .result_score_row(result_score_row),
    .result_weights(result_weights), .result_value(result_value),
    .accepted_count(accepted_count), .completed_count(completed_count)
  );

  always @* begin
    command_valid = rst_n && (send_index < COMMAND_COUNT);
    command_id = 16'h0;
    command_seed = 32'h0;
    if (send_index < COMMAND_COUNT) begin
      command_id = command_ids[send_index];
      command_seed = command_seeds[send_index];
    end
    {enable_logic}
    {ready_logic}
    dispatch_command_id = 16'h0;
    case (dut.dispatch_producer_idx)
{dispatch_id_cases}
      default: dispatch_command_id = 16'h0;
    endcase
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      send_index <= 0;
      cycle <= 0;
    end else begin
      if (command_valid && command_ready) begin
        $display("ACCEPT cycle=%0d producer=%0d id=%0d seed=%08x", cycle, dut.issue_target_idx, command_id, command_seed);
        send_index <= send_index + 1;
      end
      if (dut.dispatch_fire) begin
        $display("DISPATCH cycle=%0d producer=%0d consumer=%0d id=%0d", cycle, dut.dispatch_producer_idx, dut.dispatch_consumer_idx, dispatch_command_id);
      end
      if (result_valid && result_ready) begin
        $display("RESULT cycle=%0d id=%0d score=%064x weights=%032x value=%080x", cycle, result_command_id, result_score_row, result_weights, result_value);
        if (completed_count + 1 == COMMAND_COUNT) begin
          $display("SUMMARY accepted=%0d completed=%0d final_cycle=%0d", accepted_count, completed_count + 1, cycle);
          #1 $finish;
        end
      end
      cycle <= cycle + 1;
      if (cycle > 500) $fatal(1, "timeout");
    end
  end

  initial begin
{command_init}
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


_ACCEPT_RE = re.compile(r"ACCEPT cycle=(\d+) producer=(\d+) id=(\d+) seed=([0-9a-fA-F]+)")
_DISPATCH_RE = re.compile(r"DISPATCH cycle=(\d+) producer=(\d+) consumer=(\d+) id=(\d+)")
_RESULT_RE = re.compile(
    r"RESULT cycle=(\d+) id=(\d+) score=([0-9a-fA-F]+) weights=([0-9a-fA-F]+) value=([0-9a-fA-F]+)"
)
_SUMMARY_RE = re.compile(r"SUMMARY accepted=(\d+) completed=(\d+) final_cycle=(\d+)")


def _parse_log(text: str) -> JsonDict:
    accepts: list[JsonDict] = []
    dispatches: list[JsonDict] = []
    results: list[JsonDict] = []
    summary: JsonDict | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _ACCEPT_RE.fullmatch(line)
        if match:
            accepts.append(
                {
                    "cycle": int(match.group(1)),
                    "producer": int(match.group(2)),
                    "command_id": int(match.group(3)),
                    "seed": int(match.group(4), 16),
                }
            )
            continue
        match = _DISPATCH_RE.fullmatch(line)
        if match:
            dispatches.append(
                {
                    "cycle": int(match.group(1)),
                    "producer": int(match.group(2)),
                    "consumer": int(match.group(3)),
                    "command_id": int(match.group(4)),
                }
            )
            continue
        match = _RESULT_RE.fullmatch(line)
        if match:
            results.append(
                {
                    "cycle": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "score_row": unpack_signed(int(match.group(3), 16), lanes=8, bits=32),
                    "weights": unpack_unsigned(int(match.group(4), 16), lanes=8, bits=16),
                    "value": unpack_signed(int(match.group(5), 16), lanes=8, bits=40),
                }
            )
            continue
        match = _SUMMARY_RE.fullmatch(line)
        if match:
            summary = {
                "accepted_count": int(match.group(1)),
                "completed_count": int(match.group(2)),
                "final_cycle": int(match.group(3)),
            }
    if summary is None:
        raise RuntimeError(f"RTL simulation did not emit SUMMARY:\n{text[-4000:]}")
    return {"accept_events": accepts, "dispatch_events": dispatches, "result_events": results, **summary}


def _run_rtl(
    *, producer_count: int, consumer_count: int, commands: list[AttentionSeparatedCommand], scenario: str
) -> JsonDict:
    top_name = f"attention_separated_cluster_p{producer_count}_c{consumer_count}"
    with tempfile.TemporaryDirectory(prefix="attention-separated-equivalence-") as tmp_text:
        tmp = Path(tmp_text)
        cfg = _config(top_name=top_name, producer_count=producer_count, consumer_count=consumer_count)
        params = _validate(cfg)
        rtl_dir = tmp / "rtl"
        _write_top(cfg=cfg, comp=params, out_path=rtl_dir)
        tb_path = tmp / "tb.sv"
        tb_path.write_text(
            _testbench(
                top_name=top_name,
                producer_count=producer_count,
                consumer_count=consumer_count,
                commands=commands,
                scenario=scenario,
            ),
            encoding="utf-8",
        )
        sim_path = tmp / "simv"
        subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(sim_path), str(rtl_dir / "top.v"), str(tb_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        completed = subprocess.run([_tool("vvp"), str(sim_path)], check=True, capture_output=True, text=True)
        return _parse_log(completed.stdout)


def _compare(perf: JsonDict, rtl: JsonDict) -> JsonDict:
    schedule_failures: list[str] = []
    functional_failures: list[str] = []
    for key in ("accept_events", "dispatch_events"):
        if perf[key] != rtl[key]:
            schedule_failures.append(f"{key} mismatch: perf={perf[key]} rtl={rtl[key]}")
    perf_results = perf["result_events"]
    rtl_results = rtl["result_events"]
    if len(perf_results) != len(rtl_results):
        functional_failures.append(f"result count mismatch: perf={len(perf_results)} rtl={len(rtl_results)}")
    for index, (expected, actual) in enumerate(zip(perf_results, rtl_results)):
        expected_functional = {
            "command_id": expected["command_id"],
            "score_row": expected["score_row"],
            "weights": expected["weights"],
            "value": expected["value"],
        }
        actual_functional = {key: actual[key] for key in expected_functional}
        if expected_functional != actual_functional:
            functional_failures.append(
                f"result[{index}] mismatch: perf={expected_functional} rtl={actual_functional}"
            )
        if expected["cycle"] != actual["cycle"]:
            schedule_failures.append(
                f"result[{index}] cycle mismatch: perf={expected['cycle']} rtl={actual['cycle']}"
            )
    for key in ("accepted_count", "completed_count", "final_cycle"):
        if perf[key] != rtl[key]:
            schedule_failures.append(f"{key} mismatch: perf={perf[key]} rtl={rtl[key]}")
    return {
        "functional_failures": functional_failures,
        "schedule_failures": schedule_failures,
        "functional_pass": not functional_failures,
        "schedule_pass": not schedule_failures,
    }


def build_report(*, ratios: list[tuple[int, int]], command_count: int) -> JsonDict:
    commands = default_commands(command_count)
    rows: list[JsonDict] = []
    for producer_count, consumer_count in ratios:
        for scenario in scenario_names():
            perf = simulate(
                commands,
                producer_count=producer_count,
                consumer_count=consumer_count,
                scenario=scenario,
            )
            rtl = _run_rtl(
                producer_count=producer_count,
                consumer_count=consumer_count,
                commands=commands,
                scenario=scenario,
            )
            comparison = _compare(perf, rtl)
            expected_ids = sorted(command.command_id for command in commands)
            actual_ids = sorted(row["command_id"] for row in rtl["result_events"])
            loss_or_duplication = (
                rtl["accepted_count"] != len(commands)
                or rtl["completed_count"] != len(commands)
                or actual_ids != expected_ids
            )
            rows.append(
                {
                    "producer_count": producer_count,
                    "consumer_count": consumer_count,
                    "ratio": f"{producer_count}:{consumer_count}",
                    "scenario": scenario,
                    "equivalence_pass": bool(
                        comparison["functional_pass"] and comparison["schedule_pass"] and not loss_or_duplication
                    ),
                    **comparison,
                    "loss_or_duplication": loss_or_duplication,
                    "accepted_count": rtl["accepted_count"],
                    "completed_count": rtl["completed_count"],
                    "final_cycle": rtl["final_cycle"],
                    "completed_order": [row["command_id"] for row in rtl["result_events"]],
                    "perf_sha256": perf["sha256"],
                }
            )
    passed = bool(rows) and all(row["equivalence_pass"] for row in rows)
    functional_pass = bool(rows) and all(row["functional_pass"] for row in rows)
    schedule_pass = bool(rows) and all(row["schedule_pass"] for row in rows)
    loss_or_duplication = any(row["loss_or_duplication"] for row in rows)
    return {
        "version": 1,
        "model": "attention_separated_cluster_perf_rtl_equivalence_v1",
        "decision": "attention_separated_cluster_equivalence_pass" if passed else "attention_separated_cluster_equivalence_fail",
        "equivalence_pass": passed,
        "semantic_profile": "q8_k8_v8_a32_s32_w16_exp_lut_div_b20",
        "ratios": [f"{producer_count}:{consumer_count}" for producer_count, consumer_count in ratios],
        "command_count": command_count,
        "scenarios": list(scenario_names()),
        "rows": rows,
        "gates": {
            "exact_score_rows": functional_pass,
            "exact_softmax_weights": functional_pass,
            "exact_weighted_value_vectors": functional_pass,
            "exact_ready_valid_schedule": schedule_pass,
            "loss_or_duplication": loss_or_duplication,
        },
        "remaining_abstractions": [
            "the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions",
            "PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe",
        ],
        "next_step": (
            "Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios."
            if passed
            else "Fix exact stage or schedule mismatches before physical evaluation."
        ),
    }


def _ratios(text: str) -> list[tuple[int, int]]:
    values: list[tuple[int, int]] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            producer_text, consumer_text = item.split(":", 1)
            producer_count = int(producer_text)
            consumer_count = int(consumer_text)
        except (TypeError, ValueError) as exc:
            raise argparse.ArgumentTypeError(f"invalid producer:consumer ratio: {item}") from exc
        if not 1 <= consumer_count <= producer_count <= 8:
            raise argparse.ArgumentTypeError(f"ratio must satisfy 1 <= consumer <= producer <= 8: {item}")
        values.append((producer_count, consumer_count))
    if not values:
        raise argparse.ArgumentTypeError("expected at least one producer:consumer ratio")
    return values


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Separated Attention Perf/RTL Equivalence",
        "",
        f"- decision: `{payload['decision']}`",
        f"- equivalence pass: `{payload['equivalence_pass']}`",
        f"- semantic profile: `{payload['semantic_profile']}`",
        "",
        "| ratio | scenario | pass | completed | final cycle |",
        "|---|---|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['ratio']} | {row['scenario']} | {row['equivalence_pass']} | "
            f"{row['completed_count']} | {row['final_cycle']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ratios",
        type=_ratios,
        default=[(1, 1), (2, 1), (4, 1), (8, 1), (4, 2), (8, 2)],
    )
    parser.add_argument("--command-count", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        ratios=args.ratios,
        command_count=args.command_count,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": payload["equivalence_pass"], "decision": payload["decision"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
