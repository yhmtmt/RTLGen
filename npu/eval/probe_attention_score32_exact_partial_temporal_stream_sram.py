#!/usr/bin/env python3
"""Probe macro-backed exact-partial temporal state against the reference model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import probe_attention_score32_exact_partial_temporal_stream as base_probe
from npu.rtlgen.gen_attention_score32_exact_partial_temporal_stream_sram import (
    generate,
)

JsonDict = dict[str, Any]
_MANIFEST = "attention_score32_exact_partial_temporal_stream_sram_manifest.json"
_MEM_RE = re.compile(
    r"MEM requests=(\d+) reads=(\d+) responses=(\d+) writes=(\d+) "
    r"req_stalls=(\d+) resp_stalls=(\d+) error=(\d+)"
)


def _config(top_name: str) -> JsonDict:
    return {
        "top_name": top_name,
        "attention_score32_exact_partial_temporal_stream_sram": {
            "heads": 32,
            "value_slices": 16,
            "head_id_bits": 5,
            "fifo_depth": 4,
            "exp_scale_impl": "factored_h33_l64_mul_exact",
            "keep_hierarchy": True,
        },
        "probe_defaults": {"heads": 2, "windows": 3, "sequence_id": 9},
    }


def _testbench(
    *,
    top_name: str,
    rows: list[dict[str, int]],
    expected_outputs: int,
    stress: bool,
    expect_error: bool,
) -> str:
    tb = base_probe._tb(
        top_name=top_name,
        rows=rows,
        expected_outputs=expected_outputs,
        stress=stress,
        expect_error=expect_error,
    )
    memory_line = (
        '        $display("MEM requests=%0d reads=%0d responses=%0d writes=%0d '
        'req_stalls=%0d resp_stalls=%0d error=%0d", '
        "dut.state_memory_request_count, dut.state_memory_read_request_count, "
        "dut.state_memory_read_response_count, dut.state_memory_write_count, "
        "dut.state_memory_request_stall_cycles, "
        "dut.state_memory_response_stall_cycles, "
        "dut.state_memory_protocol_error);\n"
    )
    tb = tb.replace('        $display("SUMMARY cycles=', memory_line + '        $display("SUMMARY cycles=')
    return tb.replace("tb_cycle > 5000", "tb_cycle > 20000")


def _parse_memory(stdout: str) -> JsonDict:
    matches = [
        match
        for line in stdout.splitlines()
        if (match := _MEM_RE.fullmatch(line.strip()))
    ]
    if not matches:
        raise RuntimeError(f"simulation did not print MEM counters\n{stdout}")
    keys = (
        "requests",
        "reads",
        "responses",
        "writes",
        "request_stalls",
        "response_stalls",
        "protocol_error",
    )
    return {
        key: int(value)
        for key, value in zip(keys, matches[-1].groups(), strict=True)
    }


def build_report(
    *,
    stress_interfaces: bool = False,
    order_violation: bool = False,
    protocol_violation: bool = False,
) -> JsonDict:
    if order_violation and protocol_violation:
        raise ValueError("select only one fail-closed mutation")
    top_name = "attention_score32_exact_partial_temporal_stream_sram_probe"
    config = _config(top_name)
    records = base_probe._records(heads=2, windows=3, sequence_id=9)
    rows = base_probe._rows_from_records(records)
    expected = base_probe._expected_rows(records)
    if order_violation:
        rows[1] = dict(rows[1])
        rows[1]["slice"] = 2
    if protocol_violation:
        rows[0] = dict(rows[0])
        rows[0]["last"] = 1

    with tempfile.TemporaryDirectory(prefix="exact-partial-temporal-sram-probe-") as name:
        temp = Path(name)
        rtl_dir = temp / "rtl"
        generate(config, rtl_dir)
        tb_path = temp / "tb.sv"
        tb_path.write_text(
            _testbench(
                top_name=top_name,
                rows=rows,
                expected_outputs=len(expected),
                stress=stress_interfaces,
                expect_error=order_violation or protocol_violation,
            ),
            encoding="utf-8",
        )
        simv = temp / "simv"
        compile_run = subprocess.run(
            [
                base_probe._tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(simv),
                str(rtl_dir / "top.v"),
                str(REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"),
                str(tb_path),
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if compile_run.returncode:
            raise RuntimeError(f"iverilog failed:\n{compile_run.stderr}")
        sim_run = subprocess.run(
            [base_probe._tool("vvp"), str(simv)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if sim_run.returncode:
            raise RuntimeError(
                f"simulation failed:\n{sim_run.stdout}\n{sim_run.stderr}"
            )
        observed, summary = base_probe._parse_stdout(sim_run.stdout)
        memory = _parse_memory(sim_run.stdout)
        manifest = json.loads(
            (rtl_dir / _MANIFEST).read_text(encoding="utf-8")
        )
        macro_manifest = json.loads(
            (rtl_dir / "macro_manifest.json").read_text(encoding="utf-8")
        )

    if order_violation or protocol_violation:
        passed = (
            summary["protocol_error"] == 1
            and summary["emitted"] == 0
            and not observed
            and memory["protocol_error"] == 0
        )
    else:
        passed = (
            observed == expected
            and len(observed) == 32
            and summary["protocol_error"] == 0
            and summary["input_accepted"] == 96
            and summary["merge_completed"] == 64
            and summary["emitted"] == 32
            and summary["completed_heads"] == 2
            and memory["requests"] == 192
            and memory["reads"] == 96
            and memory["responses"] == 96
            and memory["writes"] == 96
            and memory["protocol_error"] == 0
        )
    return {
        "model": "attention_score32_exact_partial_temporal_stream_sram_probe_v1",
        "passed": passed,
        "stress_interfaces": stress_interfaces,
        "order_violation": order_violation,
        "protocol_violation": protocol_violation,
        "observed_rows": [] if order_violation else observed,
        "expected_rows": [] if order_violation else expected,
        "summary": summary,
        "state_memory": memory,
        "manifest": manifest,
        "macro_manifest": macro_manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stress-interfaces", action="store_true")
    parser.add_argument("--order-violation", action="store_true")
    parser.add_argument("--protocol-violation", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(
        stress_interfaces=args.stress_interfaces,
        order_violation=args.order_violation,
        protocol_violation=args.protocol_violation,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
