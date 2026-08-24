#!/usr/bin/env python3
"""Verify shared-SRAM adapter RTL cycles and recost its physical frontier."""

from __future__ import annotations

import argparse
import csv
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

from npu.rtlgen.gen_attention_shared_sram_read_group_adapter_ppa_harness import generate
from npu.sim.perf.attention_shared_sram_read_group_adapter import (
    simulate_shared_sram_read_group_adapter,
)


VARIANTS = ((256, 1), (256, 2), (512, 1), (512, 2))
RESULT_RE = re.compile(
    r"RESULT cycles=(\d+) req=(\d+) macro=(\d+) rsp=(\d+) "
    r"req_stall=(\d+) rsp_stall=(\d+) macro_req_stall=(\d+) macro_rsp_stall=(\d+) "
    r"fold=([0-9a-fA-F]+) err=(\d+) proven=(\d+)"
)


def _tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _testbench(top_name: str) -> str:
    return f"""`timescale 1ns/1ps
module tb;
  reg clk = 0, rst_n = 0, start = 0;
  wire done, protocol_error, access_reduction_proven;
  wire [31:0] folded_result, cycle_count, beat_request_count, macro_read_count, beat_response_count;
  {top_name} dut(
    .clk(clk), .rst_n(rst_n), .start(start), .seed(32'h12345678),
    .done(done), .folded_result(folded_result), .cycle_count(cycle_count),
    .beat_request_count(beat_request_count), .macro_read_count(macro_read_count),
    .beat_response_count(beat_response_count), .protocol_error(protocol_error),
    .access_reduction_proven(access_reduction_proven));
  always #5 clk = ~clk;
  initial begin
    repeat (3) @(negedge clk); rst_n = 1; start = 1;
    @(negedge clk); start = 0;
    wait(done); @(posedge clk);
    $display("RESULT cycles=%0d req=%0d macro=%0d rsp=%0d req_stall=%0d rsp_stall=%0d macro_req_stall=%0d macro_rsp_stall=%0d fold=%08x err=%0d proven=%0d",
      cycle_count, beat_request_count, macro_read_count, beat_response_count,
      dut.unused_stalls_0, dut.unused_stalls_1, dut.unused_stalls_2, dut.unused_stalls_3,
      folded_result, protocol_error, access_reduction_proven);
    $finish;
  end
  initial begin #200000; $fatal(1, "timeout"); end
endmodule
"""


def run_rtl(*, config: dict[str, Any]) -> dict[str, int | bool]:
    top_name = str(config["top_name"])
    with tempfile.TemporaryDirectory(prefix="shared_sram_adapter_equivalence_") as temp_name:
        temp_dir = Path(temp_name)
        generate(config, temp_dir)
        tb_path = temp_dir / "tb.sv"
        sim_path = temp_dir / "sim.vvp"
        tb_path.write_text(_testbench(top_name), encoding="ascii")
        subprocess.run(
            [
                _tool("iverilog"),
                "-g2012",
                "-s",
                "tb",
                "-o",
                str(sim_path),
                str(temp_dir / "top.v"),
                str(tb_path),
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = subprocess.run(
            [_tool("vvp"), str(sim_path)],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    match = RESULT_RE.search(result.stdout)
    if match is None:
        raise RuntimeError(f"missing RTL result for {top_name}: {result.stdout[-1000:]}")
    values = [int(value, 16) if index == 8 else int(value) for index, value in enumerate(match.groups())]
    return {
        "cycle_count": values[0],
        "beat_request_count": values[1],
        "macro_read_count": values[2],
        "beat_response_count": values[3],
        "beat_request_stall_count": values[4],
        "beat_response_stall_count": values[5],
        "macro_request_stall_count": values[6],
        "macro_response_stall_count": values[7],
        "folded_result": values[8],
        "protocol_error": bool(values[9]),
        "access_reduction_proven": bool(values[10]),
    }


def _physical_row(metrics_path: Path, *, clock_period_ns: float) -> dict[str, Any]:
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    matches = []
    for row in rows:
        if row.get("status") != "ok" or None in row:
            continue
        params = json.loads(row.get("params_json") or "{}")
        if float(params.get("CLOCK_PERIOD", -1)) == float(clock_period_ns):
            matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one {clock_period_ns} ns physical row in {metrics_path}, found {len(matches)}")
    row = matches[0]
    return {
        "clock_period_ns": float(clock_period_ns),
        "critical_path_ns": float(row["critical_path_ns"]),
        "instance_area_um2": float(row["instance_area_um2"]),
        "stdcell_count": int(float(row["stdcell_count"])),
        "total_power_mw": float(row["total_power_mw"]),
        "param_hash": row["param_hash"],
        "metrics_csv": metrics_path.relative_to(REPO_ROOT).as_posix(),
        "sram_bitcell_area_included": False,
    }


def build_report(*, clock_period_ns: float = 2.0) -> dict[str, Any]:
    variants = []
    for beat_width, group_slots in VARIANTS:
        design = f"attention_shared_sram_read_group_adapter_w{beat_width}_s{group_slots}"
        design_dir = REPO_ROOT / "runs" / "designs" / "npu_blocks" / design
        config = json.loads((design_dir / "config.json").read_text(encoding="utf-8"))
        model = simulate_shared_sram_read_group_adapter(
            beat_width=beat_width,
            group_slots=group_slots,
        ).to_dict()
        rtl = run_rtl(config=config)
        compared_fields = tuple(rtl)
        mismatches = {
            field: {"model": model[field], "rtl": rtl[field]}
            for field in compared_fields
            if model[field] != rtl[field]
        }
        physical = _physical_row(design_dir / "metrics.csv", clock_period_ns=clock_period_ns)
        service_latency_ns = int(model["cycle_count"]) * clock_period_ns
        groups = int(model["groups"])
        energy_pj = float(physical["total_power_mw"]) * service_latency_ns
        variants.append(
            {
                "design": design,
                "beat_width": beat_width,
                "group_slots": group_slots,
                "precision_status": "exact_lossless_no_precision_change",
                "equivalence_passed": not mismatches,
                "equivalence_mismatches": mismatches,
                "model": model,
                "rtl": rtl,
                "physical": physical,
                "service": {
                    "groups": groups,
                    "cycles": int(model["cycle_count"]),
                    "latency_ns": service_latency_ns,
                    "groups_per_cycle": groups / int(model["cycle_count"]),
                    "group_throughput_per_s": groups / (service_latency_ns * 1e-9),
                    "energy_pj": energy_pj,
                    "energy_per_group_pj": energy_pj / groups,
                },
            }
        )

    passed = all(bool(row["equivalence_passed"]) for row in variants)
    best_throughput = min(variants, key=lambda row: float(row["service"]["latency_ns"]))["design"]
    best_energy = min(variants, key=lambda row: float(row["service"]["energy_per_group_pj"]))["design"]
    best_area = min(variants, key=lambda row: float(row["physical"]["instance_area_um2"]))["design"]
    return {
        "version": 1,
        "model": "llm_decoder_attention_shared_sram_adapter_frontier_llama7b_v1",
        "profile": "decoder_attention_shared_sram_read_group_adapter_frontier",
        "decision": "adapter_frontier_measured_exact",
        "passed": passed,
        "classification": "passed" if passed else "rtl_perf_mismatch",
        "clock_period_ns": clock_period_ns,
        "workload": {
            "groups": 64,
            "shared_macro_width_bits": 1024,
            "response_ready_pattern": [1, 1, 1, 1, 1, 0, 1, 1],
        },
        "variants": variants,
        "dimension_winners": {
            "adapter_group_service_throughput": best_throughput,
            "adapter_vectorless_total_energy_proxy": best_energy,
            "adapter_instance_area": best_area,
            "precision": "all_variants_exact",
        },
        "interpretation": {
            "adapter_only": True,
            "sram_bitcell_area_included": False,
            "power_kind": "vectorless_openroad_at_common_clock",
            "system_selection_requires_composed_scheduler_and_transport_recost": True,
        },
        "diagnosis": {
            "decision": "adapter_frontier_measured_exact" if passed else "adapter_rtl_perf_mismatch",
            "recommended_next_step": (
                "compose the selected adapter with measured scheduler, endpoint, NoC, and SRAM macro service"
                if passed
                else "resolve RTL/performance-model mismatch before system recost"
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Shared-SRAM Adapter RTL/Perf Frontier",
        "",
        f"- passed: `{str(report['passed']).lower()}`",
        f"- common_clock_period_ns: `{report['clock_period_ns']}`",
        "- precision: `exact_lossless_no_precision_change`",
        "",
        "| Design | Cycles | Latency (ns) | Area (um2) | Power (mW) | Energy/group (pJ) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["variants"]:
        lines.append(
            f"| {row['design']} | {row['service']['cycles']} | {row['service']['latency_ns']:.3f} | "
            f"{row['physical']['instance_area_um2']:.2f} | {row['physical']['total_power_mw']:.6f} | "
            f"{row['service']['energy_per_group_pj']:.6f} |"
        )
    lines.extend(
        [
            "",
            f"- adapter group-service throughput winner: `{report['dimension_winners']['adapter_group_service_throughput']}`",
            f"- adapter vectorless total-energy proxy winner: `{report['dimension_winners']['adapter_vectorless_total_energy_proxy']}`",
            f"- area winner: `{report['dimension_winners']['adapter_instance_area']}`",
            "- SRAM bitcell area is excluded; this report closes adapter logic and scheduling only.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clock-period-ns", type=float, default=2.0)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(clock_period_ns=args.clock_period_ns)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(markdown, encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else markdown, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
