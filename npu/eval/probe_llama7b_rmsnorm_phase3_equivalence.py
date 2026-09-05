#!/usr/bin/env python3
"""Prove deterministic Phase-3 Llama-7B RMSNorm perf/RTL equivalence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.llama7b_rmsnorm_phase2 import (  # noqa: E402
    CANONICAL_PROTOCOL_ERROR_BF16,
    HIDDEN_SIZE,
    RMSNormPhase2Metadata,
    operation_metadata,
    rmsnorm_bf16_phase2,
)
from npu.rtlgen.gen_llama7b_rmsnorm import generate  # noqa: E402

JsonDict = dict[str, Any]

LANES = 16
BEATS = HIDDEN_SIZE // LANES
_SEMANTIC_PROFILE = "llama7b_bf16_rmsnorm_phase3_bounded_ready_valid_v1"
_MACRO_SEMANTIC_PROFILE = "llama7b_bf16_rmsnorm_phase3_macro_banked_ready_valid_v1"
_PIPELINED_MACRO_SEMANTIC_PROFILE = "llama7b_bf16_rmsnorm_phase3_macro_banked_pipelined_ready_valid_v1"


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config(*, top_name: str, storage_backend: str = "register_arrays") -> JsonDict:
    return {
        "top_name": top_name,
        "llama7b_rmsnorm": {
            "lanes": LANES,
            "storage_backend": storage_backend,
        },
    }


def _write_memh(path: Path, words: list[int] | tuple[int, ...]) -> None:
    path.write_text("".join(f"{word:04x}\n" for word in words), encoding="ascii")


def _unity_case() -> JsonDict:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    return {"case_id": "unity_identity", "row": row, "gamma": gamma, "wrong_last": False}


def _signed_pattern_case() -> JsonDict:
    pattern = [0x0001, 0x807F, 0x2F80, 0xBF80, 0x4F00, 0xDF00, 0x7F7F]
    row = [pattern[index % len(pattern)] for index in range(HIDDEN_SIZE)]
    gamma = [0x3F00 + (index % 5) * 0x20 for index in range(HIDDEN_SIZE)]
    return {"case_id": "signed_pattern", "row": row, "gamma": gamma, "wrong_last": False}


def _framing_error_case() -> JsonDict:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    return {"case_id": "framing_error", "row": row, "gamma": gamma, "wrong_last": True}


def _row_exponent_255_case() -> JsonDict:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    row[-1] = 0x7F80
    return {"case_id": "row_exponent_255", "row": row, "gamma": gamma, "wrong_last": False}


def _gamma_exponent_255_case() -> JsonDict:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    gamma[-1] = 0x7F80
    return {"case_id": "gamma_exponent_255", "row": row, "gamma": gamma, "wrong_last": False}


def _case_catalog() -> dict[str, Callable[[], JsonDict]]:
    return {
        "unity_identity": _unity_case,
        "signed_pattern": _signed_pattern_case,
        "framing_error": _framing_error_case,
        "row_exponent_255": _row_exponent_255_case,
        "gamma_exponent_255": _gamma_exponent_255_case,
    }


def _expected_case(case_id: str) -> JsonDict:
    factory = _case_catalog().get(case_id)
    if factory is None:
        raise ValueError(f"unknown RMSNorm phase3 case: {case_id}")
    case = factory()
    row = list(int(word) for word in case["row"])
    gamma = list(int(word) for word in case["gamma"])
    if bool(case["wrong_last"]):
        return {
            "case_id": case_id,
            "row": row,
            "gamma": gamma,
            "wrong_last": True,
            "protocol_error": True,
            "output": (CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE,
            "metadata": operation_metadata(LANES),
        }
    result = rmsnorm_bf16_phase2(row, gamma, lanes=LANES)
    return {
        "case_id": case_id,
        "row": row,
        "gamma": gamma,
        "wrong_last": False,
        "protocol_error": bool(result.protocol_error),
        "output": tuple(int(word) for word in result.output),
        "metadata": result.metadata,
    }


def _ready_expr(scenario: str) -> str:
    if scenario == "always_ready":
        return "1'b1"
    if scenario == "periodic_backpressure":
        return "((cycle % 4) != 2)"
    raise ValueError(f"unknown scenario: {scenario}")


def _testbench(
    *,
    top_name: str,
    row_path: Path,
    gamma_path: Path,
    scenario: str,
    wrong_last: bool,
) -> str:
    last_expr = "(beat == BEATS-2)" if wrong_last else "(beat == BEATS-1)"
    return f"""module tb;
  localparam integer LANES = {LANES};
  localparam integer HIDDEN_SIZE = {HIDDEN_SIZE};
  localparam integer BEATS = {BEATS};

  reg clk = 0;
  always #5 clk = ~clk;

  reg rst_n = 0;
  reg in_valid = 0;
  wire in_ready;
  reg [{LANES * 16 - 1}:0] in_row = 0;
  reg [{LANES * 16 - 1}:0] in_gamma = 0;
  reg in_last = 0;

  wire out_valid;
  reg out_ready = 1;
  wire [{LANES * 16 - 1}:0] out_row;
  wire out_last;
  wire out_protocol_error;
  wire [31:0] accepted_row_count;
  wire [31:0] completed_row_count;

  reg [15:0] row_mem [0:HIDDEN_SIZE-1];
  reg [15:0] gamma_mem [0:HIDDEN_SIZE-1];

  integer beat;
  integer lane;
  integer index;
  integer cycle;
  integer outputs_seen;
  integer last_output_cycle;
  reg summary_pending;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(in_valid),
      .in_ready(in_ready),
      .in_row(in_row),
      .in_gamma(in_gamma),
      .in_last(in_last),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_row(out_row),
      .out_last(out_last),
      .out_protocol_error(out_protocol_error),
      .accepted_row_count(accepted_row_count),
      .completed_row_count(completed_row_count)
  );

  initial begin
    $readmemh("{row_path}", row_mem);
    $readmemh("{gamma_path}", gamma_mem);

    beat = 0;
    cycle = 0;
    outputs_seen = 0;
    last_output_cycle = -1;
    summary_pending = 1'b0;

    repeat (3) @(posedge clk);
    rst_n = 1'b1;

    while (beat < BEATS) begin
      @(posedge clk);
      if (in_ready) begin
        in_valid <= 1'b1;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
          index = beat * LANES + lane;
          in_row[(lane * 16) +: 16] <= row_mem[index];
          in_gamma[(lane * 16) +: 16] <= gamma_mem[index];
        end
        in_last <= {last_expr};
        beat = beat + 1;
      end
      cycle = cycle + 1;
    end

    @(posedge clk);
    in_valid <= 1'b0;
    in_last <= 1'b0;
    cycle = cycle + 1;

    while (!summary_pending && cycle < 5000) begin
      @(negedge clk);
      out_ready = {_ready_expr(scenario)};
      @(posedge clk);
      if (out_valid && out_ready) begin
        $display(
            "OUTPUT cycle=%0d beat=%0d last=%0d error=%0d row=%064x",
            cycle,
            outputs_seen,
            out_last,
            out_protocol_error,
            out_row
        );
        last_output_cycle = cycle;
        outputs_seen = outputs_seen + 1;
        if (out_last) summary_pending = 1'b1;
      end
      cycle = cycle + 1;
    end

    @(posedge clk);
    $display(
        "SUMMARY accepted=%0d completed=%0d outputs=%0d last_output_cycle=%0d completed_cycle=%0d",
        accepted_row_count,
        completed_row_count,
        outputs_seen,
        last_output_cycle,
        cycle
    );
    $finish;
  end
endmodule
"""


_OUTPUT_RE = re.compile(
    r"OUTPUT cycle=(\d+) beat=(\d+) last=(\d+) error=(\d+) row=([0-9a-fA-F]+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY accepted=(\d+) completed=(\d+) outputs=(\d+) last_output_cycle=(-?\d+) completed_cycle=(\d+)"
)


def _decode_packed_row(hex_text: str) -> tuple[int, ...]:
    value = int(hex_text, 16)
    return tuple((value >> (lane * 16)) & 0xFFFF for lane in range(LANES))


def _expected_output_beats(words: tuple[int, ...]) -> list[tuple[int, ...]]:
    return [
        tuple(int(words[beat * LANES + lane]) for lane in range(LANES))
        for beat in range(BEATS)
    ]


def _simulate_output_cycles(
    *,
    metadata: RMSNormPhase2Metadata,
    scenario: str,
) -> list[int]:
    issue_start_cycle = (
        metadata.input_accept_cycles
        + metadata.accumulation_replay_cycles
        + metadata.finalize_cycles
        + 1
    )
    pipeline: list[int | None] = [None, None, None]
    issue_beat = 0
    cycle = 0
    outputs: list[int] = []

    def out_ready_at(sim_cycle: int) -> bool:
        if scenario == "always_ready":
            return True
        if scenario == "periodic_backpressure":
            return (sim_cycle % 4) != 2
        raise ValueError(f"unknown scenario: {scenario}")

    while len(outputs) < metadata.beats_per_row:
        out_ready = out_ready_at(cycle)
        s2_ready = pipeline[2] is None or out_ready
        s1_ready = pipeline[1] is None or s2_ready
        s0_ready = pipeline[0] is None or s1_ready
        issue_valid = cycle >= issue_start_cycle and issue_beat < metadata.beats_per_row

        if pipeline[2] is not None and out_ready:
            outputs.append(cycle)

        next_pipeline = list(pipeline)
        if s2_ready:
            next_pipeline[2] = pipeline[1]
        if s1_ready:
            next_pipeline[1] = pipeline[0]
        if s0_ready:
            next_pipeline[0] = issue_beat if issue_valid else None
            if issue_valid:
                issue_beat += 1
        pipeline = next_pipeline
        cycle += 1

        if cycle > 20000:
            raise RuntimeError("phase3 schedule model timed out")

    return outputs


def _simulate_macro_banked_output_cycles(
    *, metadata: RMSNormPhase2Metadata, scenario: str
) -> list[int]:
    """Independent schedule for one-outstanding, two-cycle macro reads."""
    first_raw_output = (
        metadata.input_accept_cycles
        + 3 * metadata.accumulation_replay_cycles
        + metadata.finalize_cycles
        + 6
    )

    def ready(cycle: int) -> bool:
        if scenario == "always_ready":
            return True
        if scenario == "periodic_backpressure":
            return (cycle % 4) != 2
        raise ValueError(f"unknown scenario: {scenario}")

    outputs: list[int] = []
    for beat in range(metadata.beats_per_row):
        cycle = first_raw_output + 3 * beat
        while not ready(cycle):
            cycle += 1
        outputs.append(cycle)
    return outputs


def _simulate_pipelined_macro_output_cycles(
    *, metadata: RMSNormPhase2Metadata, scenario: str
) -> list[int]:
    """Independent closed form for the three-credit pipelined macro controller."""
    first_output = (
        metadata.input_accept_cycles
        + metadata.accumulation_replay_cycles
        + metadata.finalize_cycles
        + 8
    )
    if scenario == "always_ready":
        return [first_output + 6 * (beat // 3) + (beat % 3) for beat in range(metadata.beats_per_row)]
    if scenario == "periodic_backpressure":
        return [
            (
                first_output
                if beat == 0
                else (first_output + 2 if beat == 1 else (first_output + 3 if beat == 2 else first_output + 2 * beat))
            )
            for beat in range(metadata.beats_per_row)
        ]
    raise ValueError(f"unknown scenario: {scenario}")


def _run_rtl(
    *,
    work_dir: Path,
    top_name: str,
    case: JsonDict,
    scenario: str,
    storage_backend: str = "register_arrays",
) -> JsonDict:
    row_path = work_dir / f"{case['case_id']}_{scenario}_row.mem"
    gamma_path = work_dir / f"{case['case_id']}_{scenario}_gamma.mem"
    tb_path = work_dir / f"{case['case_id']}_{scenario}_tb.v"
    sim_path = work_dir / f"{case['case_id']}_{scenario}.vvp"

    _write_memh(row_path, case["row"])
    _write_memh(gamma_path, case["gamma"])
    tb_path.write_text(
        _testbench(
            top_name=top_name,
            row_path=row_path,
            gamma_path=gamma_path,
            scenario=scenario,
            wrong_last=bool(case["wrong_last"]),
        ),
        encoding="ascii",
    )

    rtl_inputs = [str(work_dir / "rtl" / "top.v")]
    if storage_backend.startswith("fakeram45_64x32_banked"):
        rtl_inputs = [
            str(_REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"),
            str(work_dir / "rtl" / "llama7b_rmsnorm_banked_row_gamma_store.v"),
            *rtl_inputs,
        ]
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(sim_path),
            *rtl_inputs,
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    run = subprocess.run(
        [_tool("vvp"), str(sim_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    outputs: list[JsonDict] = []
    summary: JsonDict | None = None
    for line in run.stdout.splitlines():
        match = _OUTPUT_RE.fullmatch(line.strip())
        if match:
            outputs.append(
                {
                    "cycle": int(match.group(1)),
                    "beat": int(match.group(2)),
                    "last": bool(int(match.group(3))),
                    "error": bool(int(match.group(4))),
                    "row": _decode_packed_row(match.group(5)),
                }
            )
            continue
        match = _SUMMARY_RE.fullmatch(line.strip())
        if match:
            summary = {
                "accepted_count": int(match.group(1)),
                "completed_count": int(match.group(2)),
                "output_count": int(match.group(3)),
                "last_output_cycle": int(match.group(4)),
                "completed_cycle": int(match.group(5)),
            }
    if summary is None:
        raise RuntimeError(f"missing RMSNorm phase3 summary:\n{run.stdout[-4000:]}")
    return {"outputs": outputs, "summary": summary}


def build_report(
    *,
    cases: list[str] | None = None,
    scenarios: list[str] | None = None,
    storage_backend: str = "register_arrays",
) -> JsonDict:
    if storage_backend not in {
        "register_arrays",
        "fakeram45_64x32_banked",
        "fakeram45_64x32_banked_pipelined",
    }:
        raise ValueError(f"unsupported storage backend: {storage_backend}")
    selected_cases = (
        ["unity_identity", "signed_pattern", "framing_error", "row_exponent_255", "gamma_exponent_255"]
        if cases is None
        else cases
    )
    selected_scenarios = ["always_ready", "periodic_backpressure"] if scenarios is None else scenarios
    metadata = operation_metadata(LANES)

    rows: list[JsonDict] = []
    top_name = "llama7b_rmsnorm_bf16_l16"
    with tempfile.TemporaryDirectory(prefix="llama7b-rmsnorm-phase3-equivalence-") as tmp_text:
        tmp = Path(tmp_text)
        generate(_config(top_name=top_name, storage_backend=storage_backend), tmp / "rtl")

        for case_id in selected_cases:
            case = _expected_case(case_id)
            expected_beats = _expected_output_beats(case["output"])
            scenario_list = (
                ["always_ready"]
                if case_id in {"framing_error", "row_exponent_255", "gamma_exponent_255"}
                else list(selected_scenarios)
            )
            for scenario in scenario_list:
                rtl = _run_rtl(
                    work_dir=tmp,
                    top_name=top_name,
                    case=case,
                    scenario=scenario,
                    storage_backend=storage_backend,
                )
                if storage_backend == "fakeram45_64x32_banked_pipelined":
                    expected_cycles = _simulate_pipelined_macro_output_cycles(
                        metadata=case["metadata"], scenario=scenario
                    )
                elif storage_backend == "fakeram45_64x32_banked":
                    expected_cycles = _simulate_macro_banked_output_cycles(
                        metadata=case["metadata"], scenario=scenario
                    )
                else:
                    expected_cycles = _simulate_output_cycles(metadata=case["metadata"], scenario=scenario)
                failures: list[str] = []

                actual_outputs = rtl["outputs"]
                if len(actual_outputs) != BEATS:
                    failures.append(f"output beat count mismatch: expected {BEATS}, got {len(actual_outputs)}")
                else:
                    for beat_index, actual in enumerate(actual_outputs):
                        if actual["beat"] != beat_index:
                            failures.append(
                                f"beat index mismatch at output[{beat_index}]: rtl={actual['beat']} expected={beat_index}"
                            )
                        if actual["row"] != expected_beats[beat_index]:
                            failures.append(f"data mismatch at beat {beat_index}")
                            break
                        if actual["cycle"] != expected_cycles[beat_index]:
                            failures.append(
                                f"cycle mismatch at beat {beat_index}: rtl={actual['cycle']} expected={expected_cycles[beat_index]}"
                            )
                            break
                        expected_last = beat_index == BEATS - 1
                        if actual["last"] != expected_last:
                            failures.append(
                                f"last mismatch at beat {beat_index}: rtl={actual['last']} expected={expected_last}"
                            )
                            break
                        if actual["error"] != bool(case["protocol_error"]):
                            failures.append(
                                f"protocol_error mismatch at beat {beat_index}: rtl={actual['error']} expected={case['protocol_error']}"
                            )
                            break

                summary = rtl["summary"]
                if summary["accepted_count"] != 1:
                    failures.append(f"accepted_count mismatch: rtl={summary['accepted_count']} expected=1")
                if summary["completed_count"] != 1:
                    failures.append(f"completed_count mismatch: rtl={summary['completed_count']} expected=1")
                if summary["output_count"] != BEATS:
                    failures.append(f"summary output_count mismatch: rtl={summary['output_count']} expected={BEATS}")
                if summary["last_output_cycle"] != expected_cycles[-1]:
                    failures.append(
                        f"last_output_cycle mismatch: rtl={summary['last_output_cycle']} expected={expected_cycles[-1]}"
                    )
                expected_completed_cycle = expected_cycles[-1] + 1
                if summary["completed_cycle"] != expected_completed_cycle:
                    failures.append(
                        f"completed_cycle mismatch: rtl={summary['completed_cycle']} expected={expected_completed_cycle}"
                    )

                rows.append(
                    {
                        "case_id": case_id,
                        "scenario": scenario,
                        "protocol_error_expected": bool(case["protocol_error"]),
                        "equivalence_pass": not failures,
                        "failures": failures,
                        "last_output_cycle": summary["last_output_cycle"],
                        "completed_cycle": summary["completed_cycle"],
                    }
                )

    passed = bool(rows) and all(row["equivalence_pass"] for row in rows)
    return {
        "version": 1,
        "model": "llama7b_rmsnorm_phase3_perf_rtl_equivalence_v1",
        "decision": "llama7b_rmsnorm_phase3_equivalence_pass" if passed else "llama7b_rmsnorm_phase3_equivalence_fail",
        "equivalence_pass": passed,
        "semantic_profile": (
            _PIPELINED_MACRO_SEMANTIC_PROFILE
            if storage_backend == "fakeram45_64x32_banked_pipelined"
            else (_MACRO_SEMANTIC_PROFILE if storage_backend == "fakeram45_64x32_banked" else _SEMANTIC_PROFILE)
        ),
        "storage_backend": storage_backend,
        "lanes": LANES,
        "beats_per_row": BEATS,
        "cases": selected_cases,
        "scenarios": selected_scenarios,
        "rows": rows,
        "gates": {
            "exact_bf16_output_beats": all(not row["failures"] for row in rows),
            "exact_protocol_error_row_replay": all(
                row["equivalence_pass"]
                for row in rows
                if row["case_id"] in {"framing_error", "row_exponent_255", "gamma_exponent_255"}
            ),
            "exact_ready_valid_row_schedule": all(
                row["equivalence_pass"] for row in rows if row["scenario"] in {"always_ready", "periodic_backpressure"}
            ),
            "exact_row_accounting": all(row["equivalence_pass"] for row in rows),
        },
        "remaining_abstractions": [
            *(
                ["row_mem and gamma_mem are internal register arrays, not SRAM-macro evidence"]
                if storage_backend == "register_arrays"
                else ["FakeRAM is a characterized proxy macro, not foundry SRAM signoff"]
            ),
            "no DRAM or external-memory controller behavior is claimed by this equivalence gate",
            "clock-gating and physical overlap policy remain outside this functional/workload proof",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="", help="comma-separated case ids; empty uses the built-in catalog")
    parser.add_argument(
        "--scenarios",
        default="",
        help="comma-separated scenario ids; empty uses always_ready and periodic_backpressure",
    )
    parser.add_argument("--out", type=Path, help="optional JSON report output path")
    parser.add_argument(
        "--storage-backend",
        choices=("register_arrays", "fakeram45_64x32_banked", "fakeram45_64x32_banked_pipelined"),
        default="register_arrays",
    )
    args = parser.parse_args()

    cases = [part.strip() for part in args.cases.split(",") if part.strip()] or None
    scenarios = [part.strip() for part in args.scenarios.split(",") if part.strip()] or None
    report = build_report(cases=cases, scenarios=scenarios, storage_backend=args.storage_backend)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if report["equivalence_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
