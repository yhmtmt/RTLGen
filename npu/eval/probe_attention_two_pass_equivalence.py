#!/usr/bin/env python3
"""Prove bounded two-pass attention perf/RTL equivalence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.rtlgen.gen_attention_two_pass import generate
from npu.sim.perf.attention_online import simulate_two_pass
from npu.sim.perf.attention_separated import default_commands, unpack_signed

JsonDict = dict[str, Any]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool is unavailable: {name}")


def _config(*, top_name: str, block_count: int) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_two_pass": {
            "block_count": block_count,
            "row_elems": 8,
            "head_dim": 8,
            "value_dim": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "input_frac_bits": 28,
            "exp_bucket_shift": 20,
        },
    }


def _testbench(*, top_name: str, command_count: int, scenario: str) -> str:
    commands = default_commands(command_count)
    init = "\n".join(
        f"    command_ids[{index}] = 16'h{command.command_id:04x}; command_seeds[{index}] = 32'h{command.seed:08x};"
        for index, command in enumerate(commands)
    )
    ready = (
        "result_ready = !(((cycle >= 9) && (cycle < 13)) || ((cycle % 6) == 4));"
        if scenario == "result_backpressure"
        else "result_ready = 1'b1;"
    )
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMAND_COUNT = {command_count};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [31:0] command_seed;
  wire result_valid;
  reg result_ready;
  wire [15:0] result_command_id;
  wire signed [31:0] result_global_max;
  wire [32:0] result_exp_sum;
  wire [319:0] result_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  wire [31:0] cycle_count;
  reg [15:0] command_ids [0:COMMAND_COUNT-1];
  reg [31:0] command_seeds [0:COMMAND_COUNT-1];
  integer send_index;
  integer cycle;

  always #5 clk = ~clk;
  {top_name} dut (
    .clk(clk), .rst_n(rst_n),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_id(command_id), .command_seed(command_seed),
    .result_valid(result_valid), .result_ready(result_ready),
    .result_command_id(result_command_id), .result_global_max(result_global_max),
    .result_exp_sum(result_exp_sum), .result_value(result_value),
    .accepted_count(accepted_count), .completed_count(completed_count), .cycle_count(cycle_count)
  );

  always @* begin
    command_valid = rst_n && send_index < COMMAND_COUNT;
    command_id = send_index < COMMAND_COUNT ? command_ids[send_index] : 16'd0;
    command_seed = send_index < COMMAND_COUNT ? command_seeds[send_index] : 32'd0;
    {ready}
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      send_index <= 0;
      cycle <= 0;
    end else begin
      if (command_valid && command_ready) begin
        $display("ACCEPT cycle=%0d id=%0d seed=%08x", cycle, command_id, command_seed);
        send_index <= send_index + 1;
      end
      if (result_valid && result_ready) begin
        $display("RESULT cycle=%0d id=%0d max=%0d sum=%0d value=%080x", cycle, result_command_id, $signed(result_global_max), result_exp_sum, result_value);
        if (completed_count + 1 == COMMAND_COUNT) begin
          $display("SUMMARY accepted=%0d completed=%0d final_cycle=%0d", accepted_count, completed_count + 1, cycle);
          #1 $finish;
        end
      end
      cycle <= cycle + 1;
      if (cycle > 1000) $fatal(1, "timeout");
    end
  end

  initial begin
{init}
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


_ACCEPT = re.compile(r"ACCEPT cycle=(\d+) id=(\d+) seed=([0-9a-fA-F]+)")
_RESULT = re.compile(r"RESULT cycle=(\d+) id=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)")
_SUMMARY = re.compile(r"SUMMARY accepted=(\d+) completed=(\d+) final_cycle=(\d+)")


def _parse(text: str) -> JsonDict:
    accepts: list[JsonDict] = []
    results: list[JsonDict] = []
    summary: JsonDict | None = None
    for line in text.splitlines():
        match = _ACCEPT.fullmatch(line.strip())
        if match:
            accepts.append(
                {"cycle": int(match.group(1)), "command_id": int(match.group(2)), "seed": int(match.group(3), 16)}
            )
            continue
        match = _RESULT.fullmatch(line.strip())
        if match:
            results.append(
                {
                    "cycle": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "global_max": int(match.group(3)),
                    "exp_sum": int(match.group(4)),
                    "value": unpack_signed(int(match.group(5), 16), lanes=8, bits=40),
                    "block_count": 4,
                    "seed": 0,
                }
            )
            continue
        match = _SUMMARY.fullmatch(line.strip())
        if match:
            summary = {
                "accepted_count": int(match.group(1)),
                "completed_count": int(match.group(2)),
                "final_cycle": int(match.group(3)),
            }
    if summary is None:
        raise RuntimeError(f"missing RTL summary:\n{text[-4000:]}")
    return {"accept_events": accepts, "result_events": results, **summary}


def _run_rtl(*, block_count: int, command_count: int, scenario: str) -> JsonDict:
    top_name = f"attention_two_pass_b{block_count}"
    with tempfile.TemporaryDirectory(prefix="attention-two-pass-") as tmp_text:
        tmp = Path(tmp_text)
        rtl = tmp / "rtl"
        generate(_config(top_name=top_name, block_count=block_count), rtl)
        tb = tmp / "tb.sv"
        tb.write_text(_testbench(top_name=top_name, command_count=command_count, scenario=scenario), encoding="utf-8")
        sim = tmp / "simv"
        subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(sim), str(rtl / "top.v"), str(tb)],
            check=True,
            capture_output=True,
            text=True,
        )
        completed = subprocess.run([_tool("vvp"), str(sim)], check=True, capture_output=True, text=True)
        return _parse(completed.stdout)


def build_report(*, block_counts: list[int], command_count: int) -> JsonDict:
    commands = default_commands(command_count)
    rows: list[JsonDict] = []
    for block_count in block_counts:
        for scenario in ("always_ready", "result_backpressure"):
            perf = simulate_two_pass(commands, block_count=block_count, scenario=scenario)
            rtl = _run_rtl(block_count=block_count, command_count=command_count, scenario=scenario)
            functional_failures: list[str] = []
            schedule_failures: list[str] = []
            for index, (expected, actual) in enumerate(zip(perf["result_events"], rtl["result_events"])):
                for key in ("command_id", "global_max", "exp_sum", "value"):
                    if expected[key] != actual[key]:
                        functional_failures.append(f"result[{index}].{key}: perf={expected[key]} rtl={actual[key]}")
                if expected["cycle"] != actual["cycle"]:
                    schedule_failures.append(
                        f"result[{index}].cycle: perf={expected['cycle']} rtl={actual['cycle']}"
                    )
            if len(perf["result_events"]) != len(rtl["result_events"]):
                functional_failures.append("result count mismatch")
            if perf["accept_events"] != rtl["accept_events"]:
                schedule_failures.append("accept event mismatch")
            for key in ("accepted_count", "completed_count", "final_cycle"):
                if perf[key] != rtl[key]:
                    schedule_failures.append(f"{key} mismatch: perf={perf[key]} rtl={rtl[key]}")
            rows.append(
                {
                    "block_count": block_count,
                    "context_tokens": block_count * 8,
                    "scenario": scenario,
                    "functional_pass": not functional_failures,
                    "schedule_pass": not schedule_failures,
                    "equivalence_pass": not functional_failures and not schedule_failures,
                    "functional_failures": functional_failures,
                    "schedule_failures": schedule_failures,
                    "final_cycle": rtl["final_cycle"],
                }
            )
    passed = bool(rows) and all(row["equivalence_pass"] for row in rows)
    return {
        "version": 1,
        "model": "attention_two_pass_perf_rtl_equivalence_v1",
        "decision": "attention_two_pass_equivalence_pass" if passed else "attention_two_pass_equivalence_fail",
        "equivalence_pass": passed,
        "semantic_profile": "q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max",
        "block_counts": block_counts,
        "command_count": command_count,
        "scenarios": ["always_ready", "result_backpressure"],
        "rows": rows,
        "gates": {
            "exact_global_max": all(row["functional_pass"] for row in rows),
            "exact_exp_sum": all(row["functional_pass"] for row in rows),
            "exact_weighted_value": all(row["functional_pass"] for row in rows),
            "exact_ready_valid_schedule": all(row["schedule_pass"] for row in rows),
        },
        "remaining_abstractions": [
            "bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports",
            "final divider lane folding and full 16384-block scheduling require physical exploration",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-counts", default="4")
    parser.add_argument("--command-count", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        block_counts=[int(value) for value in args.block_counts.split(",") if value],
        command_count=args.command_count,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(
        "# Two-Pass Attention Equivalence\n\n"
        f"- decision: `{payload['decision']}`\n"
        f"- equivalence pass: `{payload['equivalence_pass']}`\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": payload["decision"], "ok": payload["equivalence_pass"]}, sort_keys=True))
    return 0 if payload["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
