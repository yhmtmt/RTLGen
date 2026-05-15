#!/usr/bin/env python3
"""Probe a bounded sharded output-projection weight-store interface.

This job checks the control/interface behavior implied by the resident
weight-store feasibility result without instantiating the full resident SRAM.
The RTL model produces deterministic per-bank data from address and bank id,
and the Python perf model checks that the same sharded read stream is observed.
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
class InterfaceScenario:
    label: str
    full_required_banks: int
    representative_banks: int
    bank_read_width_bits: int
    read_ports_per_bank: int
    read_latency_cycles: int
    request_count: int
    address_stride: int


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_int_list(text: str) -> list[int]:
    values = []
    for part in str(text).split(","):
        part = part.strip()
        if part:
            values.append(int(part))
    return values


def _data_bits(bank_read_width_bits: int) -> int:
    return max(8, min(32, int(bank_read_width_bits) // 64))


def _checksum_word(*, addr: int, bank: int, data_bits: int) -> int:
    mask = (1 << data_bits) - 1
    return (addr * 131 + bank * 17 + 90) & mask


def _perf_reference(scenario: InterfaceScenario) -> JsonDict:
    data_bits = _data_bits(scenario.bank_read_width_bits)
    checksum = 0
    for req in range(scenario.request_count):
        addr = req * scenario.address_stride
        for bank in range(scenario.representative_banks):
            checksum += _checksum_word(addr=addr, bank=bank, data_bits=data_bits)
    return {
        "accepted": scenario.request_count,
        "responses": scenario.request_count,
        "checksum": checksum,
        "first_response_cycle": scenario.read_latency_cycles,
        "final_cycle_lower_bound": scenario.request_count + scenario.read_latency_cycles,
    }


def _scenario_from_shape(
    shape: JsonDict,
    *,
    max_representative_banks: int,
    latency: int,
    request_count: int,
    address_stride: int,
) -> InterfaceScenario | None:
    best = shape.get("best_area_budget_feasible")
    if not isinstance(best, dict):
        best = shape.get("best_capacity_bandwidth")
    if not isinstance(best, dict):
        return None
    required_banks = max(1, _as_int(best.get("required_banks"), 1))
    representative_banks = max(1, min(required_banks, max_representative_banks))
    return InterfaceScenario(
        label=str(shape.get("label") or best.get("label") or "shape"),
        full_required_banks=required_banks,
        representative_banks=representative_banks,
        bank_read_width_bits=max(8, _as_int(best.get("bank_read_width_bits"), 512)),
        read_ports_per_bank=max(1, _as_int(best.get("read_ports_per_bank"), 1)),
        read_latency_cycles=max(1, latency),
        request_count=max(1, request_count),
        address_stride=max(1, address_stride),
    )


def build_scenarios(
    feasibility: JsonDict,
    *,
    max_representative_banks: int,
    read_latency_cycles: list[int],
    request_count: int,
    address_stride: int,
) -> list[InterfaceScenario]:
    shape_summaries = feasibility.get("shape_summaries")
    if not isinstance(shape_summaries, list):
        return []
    scenarios: list[InterfaceScenario] = []
    for shape in shape_summaries:
        if not isinstance(shape, dict):
            continue
        for latency in read_latency_cycles:
            scenario = _scenario_from_shape(
                shape,
                max_representative_banks=max_representative_banks,
                latency=latency,
                request_count=request_count,
                address_stride=address_stride,
            )
            if scenario is not None:
                scenarios.append(scenario)
    return scenarios


def _write_rtl(path: Path, scenario: InterfaceScenario) -> None:
    data_bits = _data_bits(scenario.bank_read_width_bits)
    banks = scenario.representative_banks
    latency = scenario.read_latency_cycles
    module = "decoder_weight_store_interface_probe"
    path.write_text(
        textwrap.dedent(
            f"""\
            `timescale 1ns/1ps
            module {module} #(
              parameter integer BANKS = {banks},
              parameter integer ADDR_BITS = 16,
              parameter integer DATA_BITS = {data_bits},
              parameter integer READ_LATENCY = {latency}
            )(
              input clk,
              input rst_n,
              input req_valid,
              output req_ready,
              input [ADDR_BITS-1:0] req_addr,
              input [BANKS-1:0] req_bank_mask,
              output resp_valid,
              input resp_ready,
              output [ADDR_BITS-1:0] resp_addr,
              output [BANKS-1:0] resp_bank_mask,
              output [BANKS*DATA_BITS-1:0] resp_data
            );
              reg [READ_LATENCY:0] valid_pipe;
              reg [ADDR_BITS-1:0] addr_pipe [0:READ_LATENCY];
              reg [BANKS-1:0] mask_pipe [0:READ_LATENCY];
              integer i;
              genvar b;

              assign req_ready = 1'b1;
              assign resp_valid = valid_pipe[READ_LATENCY];
              assign resp_addr = addr_pipe[READ_LATENCY];
              assign resp_bank_mask = mask_pipe[READ_LATENCY];

              generate
                for (b = 0; b < BANKS; b = b + 1) begin : gen_data
                  wire [DATA_BITS-1:0] word;
                  assign word = (resp_addr * 131 + b * 17 + 90) & {{DATA_BITS{{1'b1}}}};
                  assign resp_data[b*DATA_BITS +: DATA_BITS] = resp_bank_mask[b] ? word : {{DATA_BITS{{1'b0}}}};
                end
              endgenerate

              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                  valid_pipe <= {{(READ_LATENCY + 1){{1'b0}}}};
                  for (i = 0; i <= READ_LATENCY; i = i + 1) begin
                    addr_pipe[i] <= {{ADDR_BITS{{1'b0}}}};
                    mask_pipe[i] <= {{BANKS{{1'b0}}}};
                  end
                end else begin
                  valid_pipe[0] <= req_valid && req_ready;
                  addr_pipe[0] <= req_addr;
                  mask_pipe[0] <= req_bank_mask;
                  for (i = 1; i <= READ_LATENCY; i = i + 1) begin
                    valid_pipe[i] <= valid_pipe[i-1];
                    addr_pipe[i] <= addr_pipe[i-1];
                    mask_pipe[i] <= mask_pipe[i-1];
                  end
                end
              end
            endmodule
            """
        ),
        encoding="utf-8",
    )


def _write_tb(path: Path, scenario: InterfaceScenario) -> None:
    banks = scenario.representative_banks
    data_bits = _data_bits(scenario.bank_read_width_bits)
    full_mask = (1 << banks) - 1
    path.write_text(
        textwrap.dedent(
            f"""\
            `timescale 1ns/1ps
            module decoder_weight_store_interface_tb;
              localparam integer BANKS = {banks};
              localparam integer DATA_BITS = {data_bits};
              localparam integer READ_LATENCY = {scenario.read_latency_cycles};
              localparam integer REQUEST_COUNT = {scenario.request_count};
              localparam integer ADDRESS_STRIDE = {scenario.address_stride};
              reg clk;
              reg rst_n;
              reg req_valid;
              wire req_ready;
              reg [15:0] req_addr;
              reg [BANKS-1:0] req_bank_mask;
              wire resp_valid;
              reg resp_ready;
              wire [15:0] resp_addr;
              wire [BANKS-1:0] resp_bank_mask;
              wire [BANKS*DATA_BITS-1:0] resp_data;
              integer cycle;
              integer sent;
              integer responses;
              integer checksum;
              integer passed;
              integer b;
              integer expected;

              decoder_weight_store_interface_probe #(
                .BANKS(BANKS),
                .ADDR_BITS(16),
                .DATA_BITS(DATA_BITS),
                .READ_LATENCY(READ_LATENCY)
              ) dut (
                .clk(clk),
                .rst_n(rst_n),
                .req_valid(req_valid),
                .req_ready(req_ready),
                .req_addr(req_addr),
                .req_bank_mask(req_bank_mask),
                .resp_valid(resp_valid),
                .resp_ready(resp_ready),
                .resp_addr(resp_addr),
                .resp_bank_mask(resp_bank_mask),
                .resp_data(resp_data)
              );

              always #5 clk = ~clk;

              initial begin
                clk = 0;
                rst_n = 0;
                req_valid = 0;
                req_addr = 0;
                req_bank_mask = {banks}'d{full_mask};
                resp_ready = 1;
                cycle = 0;
                sent = 0;
                responses = 0;
                checksum = 0;
                passed = 1;
                repeat (3) @(posedge clk);
                rst_n = 1;
              end

              always @(posedge clk) begin
                if (rst_n) begin
                  cycle = cycle + 1;
                  if (sent < REQUEST_COUNT) begin
                    req_valid <= 1'b1;
                    req_addr <= sent * ADDRESS_STRIDE;
                    req_bank_mask <= {banks}'d{full_mask};
                    if (req_ready) sent = sent + 1;
                  end else begin
                    req_valid <= 1'b0;
                  end

                  if (resp_valid && resp_ready) begin
                    responses = responses + 1;
                    if (resp_bank_mask !== {banks}'d{full_mask}) passed = 0;
                    for (b = 0; b < BANKS; b = b + 1) begin
                      expected = ((resp_addr * 131) + (b * 17) + 90) & ((1 << DATA_BITS) - 1);
                      checksum = checksum + resp_data[b*DATA_BITS +: DATA_BITS];
                      if (resp_data[b*DATA_BITS +: DATA_BITS] !== expected[DATA_BITS-1:0]) passed = 0;
                    end
                  end

                  if (responses == REQUEST_COUNT) begin
                    $display("RESULT passed=%0d accepted=%0d responses=%0d checksum=%0d final_cycle=%0d",
                      passed, sent, responses, checksum, cycle);
                    $finish;
                  end
                  if (cycle > REQUEST_COUNT + READ_LATENCY + 20) begin
                    $display("RESULT passed=0 accepted=%0d responses=%0d checksum=%0d final_cycle=%0d",
                      sent, responses, checksum, cycle);
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
        r"RESULT passed=(?P<passed>\d+) accepted=(?P<accepted>\d+) responses=(?P<responses>\d+) "
        r"checksum=(?P<checksum>\d+) final_cycle=(?P<final_cycle>\d+)",
        text,
    )
    if not match:
        return {}
    return {key: int(value) for key, value in match.groupdict().items()}


def run_rtl_scenario(scenario: InterfaceScenario, *, iverilog: str | None, vvp: str | None) -> JsonDict:
    if not iverilog or not vvp:
        return {
            "status": "simulator_missing",
            "iverilog": iverilog,
            "vvp": vvp,
        }
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        rtl = work / "decoder_weight_store_interface_probe.v"
        tb = work / "decoder_weight_store_interface_tb.v"
        simv = work / "simv"
        _write_rtl(rtl, scenario)
        _write_tb(tb, scenario)
        compile_proc = subprocess.run(
            [iverilog, "-g2012", "-o", str(simv), str(rtl), str(tb)],
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
        status = "ok" if run_proc.returncode == 0 and observed.get("passed") == 1 else "failed"
        return {
            "status": status,
            "returncode": run_proc.returncode,
            "observed": observed,
            "stdout_tail": run_proc.stdout.splitlines()[-20:],
            "stderr_tail": run_proc.stderr[-2000:],
        }


def evaluate_scenario(scenario: InterfaceScenario, *, iverilog: str | None, vvp: str | None) -> JsonDict:
    reference = _perf_reference(scenario)
    rtl = run_rtl_scenario(scenario, iverilog=iverilog, vvp=vvp)
    observed = rtl.get("observed") if isinstance(rtl.get("observed"), dict) else {}
    passed = (
        rtl.get("status") == "ok"
        and int(observed.get("accepted", -1)) == reference["accepted"]
        and int(observed.get("responses", -1)) == reference["responses"]
        and int(observed.get("checksum", -1)) == reference["checksum"]
    )
    return {
        "label": scenario.label,
        "full_required_banks": scenario.full_required_banks,
        "representative_banks": scenario.representative_banks,
        "bank_read_width_bits": scenario.bank_read_width_bits,
        "read_ports_per_bank": scenario.read_ports_per_bank,
        "read_latency_cycles": scenario.read_latency_cycles,
        "request_count": scenario.request_count,
        "address_stride": scenario.address_stride,
        "data_bits_in_probe": _data_bits(scenario.bank_read_width_bits),
        "perf_reference": reference,
        "rtl_sim": rtl,
        "passed": passed,
    }


def build_report(
    *,
    feasibility: JsonDict,
    scenarios: list[InterfaceScenario],
    iverilog: str | None,
    vvp: str | None,
) -> JsonDict:
    rows = [evaluate_scenario(scenario, iverilog=iverilog, vvp=vvp) for scenario in scenarios]
    all_passed = bool(rows) and all(bool(row.get("passed")) for row in rows)
    summary = {
        "scenario_count": len(rows),
        "passed_count": sum(1 for row in rows if row.get("passed")),
        "max_representative_banks": max((int(row["representative_banks"]) for row in rows), default=0),
        "full_required_banks": {
            str(row["label"]): int(row["full_required_banks"])
            for row in rows
        },
    }
    feasibility_decision = (
        (feasibility.get("decision") or {}).get("decision")
        if isinstance(feasibility.get("decision"), dict)
        else feasibility.get("decision")
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_weight_store_interface_contract_v1",
        "source_feasibility_decision": feasibility_decision,
        "summary": summary,
        "interface_rows": rows,
        "decision": {
            "decision": (
                "weight_store_interface_contract_passed"
                if all_passed
                else "weight_store_interface_contract_blocked"
            ),
            "next_step": (
                "Use the sharded ready/valid contract when building a measured producer-side weight fetch wrapper; keep storage PPA from the feasibility model."
                if all_passed
                else "Fix simulator availability or the sharded interface contract before adding measured producer-side logic."
            ),
        },
        "assumptions": [
            "The RTL probe scales the number of banks down to a bounded representative count; full resident capacity and area remain from the feasibility artifact.",
            "The probe models independent sharded bank reads and deterministic response ordering, not SRAM bitcell layout.",
            "Python perf reference and RTL simulation must agree on accepted requests, response count, and data checksum.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Weight-Store Interface Contract",
        "",
        f"- model: `{payload['model']}`",
        f"- source_feasibility_decision: `{payload.get('source_feasibility_decision')}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- scenario_count: `{payload['summary']['scenario_count']}`",
        f"- passed_count: `{payload['summary']['passed_count']}`",
        "",
        "## Scenarios",
        "",
        "| label | full banks | probe banks | read bits | latency | passed | checksum |",
        "|---|---:|---:|---:|---:|---|---:|",
    ]
    for row in payload["interface_rows"]:
        observed = row.get("rtl_sim", {}).get("observed", {})
        lines.append(
            "| {label} | {full} | {probe} | {bits} | {latency} | `{passed}` | {checksum} |".format(
                label=row["label"],
                full=row["full_required_banks"],
                probe=row["representative_banks"],
                bits=row["bank_read_width_bits"],
                latency=row["read_latency_cycles"],
                passed=row["passed"],
                checksum=observed.get("checksum"),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe sharded output-projection weight-store interface equivalence")
    ap.add_argument("--weight-store-feasibility", required=True)
    ap.add_argument("--max-representative-banks", type=int, default=8)
    ap.add_argument("--read-latency-cycles-list", default="1,2")
    ap.add_argument("--request-count", type=int, default=12)
    ap.add_argument("--address-stride", type=int, default=3)
    ap.add_argument("--iverilog", default="iverilog")
    ap.add_argument("--vvp", default="vvp")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    feasibility = _load_json(args.weight_store_feasibility)
    scenarios = build_scenarios(
        feasibility,
        max_representative_banks=args.max_representative_banks,
        read_latency_cycles=_parse_int_list(args.read_latency_cycles_list),
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
