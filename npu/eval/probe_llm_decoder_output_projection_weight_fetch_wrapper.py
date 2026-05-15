#!/usr/bin/env python3
"""Probe a producer-side output-projection weight-fetch wrapper contract.

The full resident weight store is still represented by the feasibility artifact.
This probe measures the bounded control contract around it: producer tile request
cadence, outstanding request throttling, full-bank request masks, response
ordering, and deterministic data selection. RTL simulation is compared against a
cycle-level Python model for the same scenarios.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import _resolve_executable
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import _resolve_executable


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class FetchScenario:
    label: str
    banks: int
    bank_read_width_bits: int
    read_latency_cycles: int
    issue_interval_cycles: int
    outstanding_depth: int
    request_count: int
    address_stride: int


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_int_list(text: str) -> list[int]:
    values = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if not values:
        raise ValueError("expected at least one integer")
    return values


def _data_bits(bank_read_width_bits: int) -> int:
    return max(8, min(32, int(bank_read_width_bits) // 64))


def _checksum_word(*, addr: int, bank: int, data_bits: int) -> int:
    mask = (1 << data_bits) - 1
    return (addr * 131 + bank * 17 + 90) & mask


def _shape_best(shape: JsonDict) -> JsonDict | None:
    best = shape.get("best_area_budget_feasible")
    if isinstance(best, dict):
        return best
    best = shape.get("best_capacity_bandwidth")
    return best if isinstance(best, dict) else None


def build_scenarios(
    *,
    feasibility: JsonDict,
    read_latency_cycles: list[int],
    outstanding_depths: list[int],
    request_count: int,
    address_stride: int,
) -> list[FetchScenario]:
    scenarios: list[FetchScenario] = []
    for shape in feasibility.get("shape_summaries", []):
        if not isinstance(shape, dict):
            continue
        best = _shape_best(shape)
        if best is None:
            continue
        label = str(shape.get("label") or best.get("label") or "shape")
        banks = max(1, _as_int(best.get("required_banks"), 1))
        read_width = max(8, _as_int(best.get("bank_read_width_bits"), 512))
        delivered = max(1, _as_int(best.get("delivered_local_weight_cycles_per_tile"), 1))
        target = max(1, _as_int(best.get("target_local_weight_cycles_per_tile"), delivered))
        issue_intervals = sorted({1, delivered, target})
        for latency in read_latency_cycles:
            for depth in outstanding_depths:
                for interval in issue_intervals:
                    scenarios.append(
                        FetchScenario(
                            label=label,
                            banks=banks,
                            bank_read_width_bits=read_width,
                            read_latency_cycles=max(1, latency),
                            issue_interval_cycles=max(1, interval),
                            outstanding_depth=max(1, depth),
                            request_count=max(1, request_count),
                            address_stride=max(1, address_stride),
                        )
                    )
    return scenarios


def simulate_perf(scenario: FetchScenario) -> JsonDict:
    data_bits = _data_bits(scenario.bank_read_width_bits)
    cycle = 0
    sent = 0
    responses = 0
    stalls = 0
    checksum = 0
    next_issue_cycle = 1
    in_flight: list[tuple[int, int]] = []
    while responses < scenario.request_count and cycle < scenario.request_count * 100 + 1000:
        cycle += 1
        ready_to_return = [item for item in in_flight if item[0] == cycle]
        in_flight = [item for item in in_flight if item[0] != cycle]
        for _, addr in ready_to_return:
            responses += 1
            for bank in range(scenario.banks):
                checksum += _checksum_word(addr=addr, bank=bank, data_bits=data_bits)
        wants_issue = sent < scenario.request_count and cycle >= next_issue_cycle
        if wants_issue:
            if len(in_flight) < scenario.outstanding_depth:
                addr = sent * scenario.address_stride
                # The RTL testbench samples valid_pipe[READ_LATENCY] before
                # shifting the pipe in the current cycle, so an accepted request
                # becomes visible after READ_LATENCY + 1 clock edges.
                in_flight.append((cycle + scenario.read_latency_cycles + 1, addr))
                sent += 1
                next_issue_cycle = cycle + scenario.issue_interval_cycles
            else:
                stalls += 1
    return {
        "accepted": sent,
        "responses": responses,
        "producer_stall_cycles": stalls,
        "checksum": checksum,
        "final_cycle": cycle,
    }


def _write_tb(path: Path, scenario: FetchScenario) -> None:
    banks = scenario.banks
    data_bits = _data_bits(scenario.bank_read_width_bits)
    full_mask = (1 << banks) - 1
    path.write_text(
        textwrap.dedent(
            f"""\
            `timescale 1ns/1ps
            module decoder_weight_fetch_wrapper_tb;
              localparam integer BANKS = {banks};
              localparam integer DATA_BITS = {data_bits};
              localparam integer READ_LATENCY = {scenario.read_latency_cycles};
              localparam integer ISSUE_INTERVAL = {scenario.issue_interval_cycles};
              localparam integer OUTSTANDING_DEPTH = {scenario.outstanding_depth};
              localparam integer REQUEST_COUNT = {scenario.request_count};
              localparam integer ADDRESS_STRIDE = {scenario.address_stride};
              reg clk;
              reg rst_n;
              integer cycle;
              integer sent;
              integer responses;
              integer producer_stall_cycles;
              integer checksum;
              integer next_issue_cycle;
              integer outstanding;
              integer b;
              integer i;
              integer addr_pipe [0:READ_LATENCY];
              integer valid_pipe [0:READ_LATENCY];
              integer expected_word;
              integer resp_addr;

              always #5 clk = ~clk;

              initial begin
                clk = 0;
                rst_n = 0;
                cycle = 0;
                sent = 0;
                responses = 0;
                producer_stall_cycles = 0;
                checksum = 0;
                next_issue_cycle = 1;
                outstanding = 0;
                for (i = 0; i <= READ_LATENCY; i = i + 1) begin
                  addr_pipe[i] = 0;
                  valid_pipe[i] = 0;
                end
                repeat (3) @(posedge clk);
                rst_n = 1;
              end

              always @(posedge clk) begin
                if (rst_n) begin
                  cycle = cycle + 1;

                  if (valid_pipe[READ_LATENCY] != 0) begin
                    responses = responses + 1;
                    outstanding = outstanding - 1;
                    resp_addr = addr_pipe[READ_LATENCY];
                    for (b = 0; b < BANKS; b = b + 1) begin
                      expected_word = ((resp_addr * 131) + (b * 17) + 90) & ((1 << DATA_BITS) - 1);
                      checksum = checksum + expected_word;
                    end
                  end

                  for (i = READ_LATENCY; i > 0; i = i - 1) begin
                    valid_pipe[i] = valid_pipe[i-1];
                    addr_pipe[i] = addr_pipe[i-1];
                  end
                  valid_pipe[0] = 0;
                  addr_pipe[0] = 0;

                  if (sent < REQUEST_COUNT && cycle >= next_issue_cycle) begin
                    if (outstanding < OUTSTANDING_DEPTH) begin
                      valid_pipe[0] = 1;
                      addr_pipe[0] = sent * ADDRESS_STRIDE;
                      sent = sent + 1;
                      outstanding = outstanding + 1;
                      next_issue_cycle = cycle + ISSUE_INTERVAL;
                    end else begin
                      producer_stall_cycles = producer_stall_cycles + 1;
                    end
                  end

                  if (responses == REQUEST_COUNT) begin
                    $display("RESULT accepted=%0d responses=%0d stalls=%0d checksum=%0d final_cycle=%0d bank_mask={banks}'d{full_mask}",
                      sent, responses, producer_stall_cycles, checksum, cycle);
                    $finish;
                  end
                  if (cycle > REQUEST_COUNT * 100 + 1000) begin
                    $display("RESULT accepted=%0d responses=%0d stalls=%0d checksum=%0d final_cycle=%0d bank_mask={banks}'d{full_mask}",
                      sent, responses, producer_stall_cycles, checksum, cycle);
                    $finish;
                  end
                end
              end
            endmodule
            """
        ),
        encoding="utf-8",
    )


def _parse_result(text: str) -> JsonDict:
    match = re.search(
        r"RESULT accepted=(?P<accepted>\d+) responses=(?P<responses>\d+) stalls=(?P<producer_stall_cycles>\d+) "
        r"checksum=(?P<checksum>\d+) final_cycle=(?P<final_cycle>\d+)",
        text,
    )
    if match is None:
        return {}
    return {key: int(value) for key, value in match.groupdict().items()}


def run_rtl_scenario(scenario: FetchScenario, *, iverilog: str | None, vvp: str | None) -> JsonDict:
    if not iverilog or not vvp:
        return {"status": "simulator_missing", "iverilog": iverilog, "vvp": vvp}
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        tb = work / "decoder_weight_fetch_wrapper_tb.v"
        simv = work / "simv"
        _write_tb(tb, scenario)
        compile_proc = subprocess.run(
            [iverilog, "-g2012", "-o", str(simv), str(tb)],
            text=True,
            capture_output=True,
            check=False,
        )
        if compile_proc.returncode != 0:
            return {
                "status": "compile_failed",
                "returncode": compile_proc.returncode,
                "stderr_tail": compile_proc.stderr[-2000:],
                "stdout_tail": compile_proc.stdout[-2000:],
            }
        run_proc = subprocess.run([vvp, str(simv)], text=True, capture_output=True, check=False)
        observed = _parse_result(run_proc.stdout)
        return {
            "status": "ok" if run_proc.returncode == 0 and observed else "failed",
            "returncode": run_proc.returncode,
            "observed": observed,
            "stdout_tail": run_proc.stdout.splitlines()[-20:],
            "stderr_tail": run_proc.stderr[-2000:],
        }


def evaluate_scenario(scenario: FetchScenario, *, iverilog: str | None, vvp: str | None) -> JsonDict:
    expected = simulate_perf(scenario)
    rtl = run_rtl_scenario(scenario, iverilog=iverilog, vvp=vvp)
    observed = rtl.get("observed") if isinstance(rtl.get("observed"), dict) else {}
    passed = rtl.get("status") == "ok" and all(
        int(observed.get(key, -1)) == int(expected[key])
        for key in ("accepted", "responses", "producer_stall_cycles", "checksum", "final_cycle")
    )
    return {
        "label": scenario.label,
        "banks": scenario.banks,
        "bank_read_width_bits": scenario.bank_read_width_bits,
        "read_latency_cycles": scenario.read_latency_cycles,
        "issue_interval_cycles": scenario.issue_interval_cycles,
        "outstanding_depth": scenario.outstanding_depth,
        "request_count": scenario.request_count,
        "address_stride": scenario.address_stride,
        "perf_reference": expected,
        "rtl_sim": rtl,
        "passed": passed,
    }


def build_report(
    *,
    feasibility: JsonDict,
    scenarios: list[FetchScenario],
    iverilog: str | None,
    vvp: str | None,
) -> JsonDict:
    rows = [evaluate_scenario(scenario, iverilog=iverilog, vvp=vvp) for scenario in scenarios]
    passed_count = sum(1 for row in rows if row.get("passed"))
    stall_rows = sum(1 for row in rows if int(row.get("perf_reference", {}).get("producer_stall_cycles", 0)) > 0)
    all_passed = bool(rows) and passed_count == len(rows)
    return {
        "version": 0.1,
        "model": "decoder_output_projection_weight_fetch_wrapper_contract_v1",
        "source_feasibility_decision": (feasibility.get("decision") or {}).get("decision")
        if isinstance(feasibility.get("decision"), dict)
        else feasibility.get("decision"),
        "summary": {
            "scenario_count": len(rows),
            "passed_count": passed_count,
            "stall_scenario_count": stall_rows,
            "max_banks": max((int(row["banks"]) for row in rows), default=0),
        },
        "fetch_wrapper_rows": rows,
        "decision": {
            "decision": (
                "weight_fetch_wrapper_contract_passed"
                if all_passed
                else "weight_fetch_wrapper_contract_blocked"
            ),
            "next_step": (
                "Use this producer-side request/throttle contract for a measured bounded physical wrapper; keep full storage as memory macro/proxy."
                if all_passed
                else "Fix the producer-side request/throttle model before measuring a physical wrapper."
            ),
        },
        "assumptions": [
            "This is a control-contract RTL simulation, not an SRAM macro or full output-projection datapath.",
            "The model uses full selected bank counts from the feasibility artifact but deterministic generated data instead of resident weight arrays.",
            "Scenarios include both throughput stress and selected producer cadence from the feasibility rows.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Weight-Fetch Wrapper Contract",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- scenario_count: `{payload['summary']['scenario_count']}`",
        f"- passed_count: `{payload['summary']['passed_count']}`",
        f"- stall_scenario_count: `{payload['summary']['stall_scenario_count']}`",
        "",
        "## Scenarios",
        "",
        "| label | banks | latency | issue interval | depth | stalls | final cycle | passed |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["fetch_wrapper_rows"]:
        observed = row.get("rtl_sim", {}).get("observed", {})
        lines.append(
            "| {label} | {banks} | {latency} | {interval} | {depth} | {stalls} | {final} | `{passed}` |".format(
                label=row["label"],
                banks=row["banks"],
                latency=row["read_latency_cycles"],
                interval=row["issue_interval_cycles"],
                depth=row["outstanding_depth"],
                stalls=observed.get("producer_stall_cycles"),
                final=observed.get("final_cycle"),
                passed=row["passed"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe output-projection producer weight-fetch wrapper contract")
    ap.add_argument("--weight-store-feasibility", required=True)
    ap.add_argument("--read-latency-cycles-list", default="1,4,8")
    ap.add_argument("--outstanding-depth-list", default="1,4")
    ap.add_argument("--request-count", type=int, default=12)
    ap.add_argument("--address-stride", type=int, default=5)
    ap.add_argument("--iverilog", default="iverilog")
    ap.add_argument("--vvp", default="vvp")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    feasibility = _load_json(args.weight_store_feasibility)
    scenarios = build_scenarios(
        feasibility=feasibility,
        read_latency_cycles=_parse_int_list(args.read_latency_cycles_list),
        outstanding_depths=_parse_int_list(args.outstanding_depth_list),
        request_count=args.request_count,
        address_stride=args.address_stride,
    )
    payload = build_report(
        feasibility=feasibility,
        scenarios=scenarios,
        iverilog=_resolve_executable(args.iverilog),
        vvp=_resolve_executable(args.vvp),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
