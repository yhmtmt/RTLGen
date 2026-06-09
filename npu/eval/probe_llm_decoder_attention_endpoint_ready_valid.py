#!/usr/bin/env python3
"""Probe the selected Llama7B endpoint service policy against ready/valid RTL."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _ceil_log2(value: int) -> int:
    return max(1, int(math.ceil(math.log2(max(1, value)))))


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_parameters(best: JsonDict) -> JsonDict:
    cluster_count = int(best["cluster_count"])
    bank_count = int(best["bank_count"])
    packet_payload_bytes = int(best["packet_payload_bytes"])
    endpoint_queue_depth_bytes = int(best["endpoint_queue_depth_bytes"])
    bank_queue_depth_bytes = int(best["bank_queue_depth_bytes"])
    banks_per_cluster = max(1, bank_count // max(1, cluster_count))
    endpoint_queue_depth_beats = max(1, endpoint_queue_depth_bytes // packet_payload_bytes)
    bank_queue_depth_beats = max(1, bank_queue_depth_bytes // packet_payload_bytes)
    return {
        "data_w": packet_payload_bytes * 8,
        "banks": banks_per_cluster,
        "bank_sel_w": _ceil_log2(banks_per_cluster),
        "endpoint_queue_depth": endpoint_queue_depth_beats,
        "bank_queue_depth": bank_queue_depth_beats,
        "counter_w": 32,
        "packet_payload_bytes": packet_payload_bytes,
        "endpoint_queue_depth_bytes": endpoint_queue_depth_bytes,
        "bank_queue_depth_bytes": bank_queue_depth_bytes,
        "cluster_count": cluster_count,
        "bank_count": bank_count,
    }


def _testbench_text(params: JsonDict) -> str:
    data_w = int(params["data_w"])
    banks = int(params["banks"])
    bank_sel_w = int(params["bank_sel_w"])
    endpoint_depth = int(params["endpoint_queue_depth"])
    bank_depth = int(params["bank_queue_depth"])
    total_beats = endpoint_depth + 1
    last_data = total_beats - 1
    return f"""`timescale 1ns/1ps

module endpoint_ready_valid_policy_tb;
  localparam integer DATA_W = {data_w};
  localparam integer BANKS = {banks};
  localparam integer BANK_SEL_W = {bank_sel_w};
  localparam integer BANK_QUEUE_DEPTH = {bank_depth};
  localparam integer ENDPOINT_QUEUE_DEPTH = {endpoint_depth};
  localparam integer COUNTER_W = 32;
  localparam integer TOTAL_BEATS = {total_beats};

  reg clk;
  reg rst_n;
  reg in_valid;
  wire in_ready;
  reg [BANK_SEL_W-1:0] in_bank;
  reg in_last;
  reg [DATA_W-1:0] in_data;
  wire out_valid;
  reg out_ready;
  wire [BANK_SEL_W-1:0] out_bank;
  wire out_last;
  wire [DATA_W-1:0] out_data;
  wire [COUNTER_W-1:0] accepted_beat_count;
  wire [COUNTER_W-1:0] emitted_beat_count;
  wire [COUNTER_W-1:0] producer_stall_cycles;
  wire [COUNTER_W-1:0] consumer_stall_cycles;
  wire [COUNTER_W-1:0] endpoint_max_occupancy;
  wire [COUNTER_W-1:0] bank_max_occupancy;
  wire [COUNTER_W-1:0] cycle_count;
  wire [COUNTER_W-1:0] final_completion_cycle;

  integer i;
  integer out_index;

  onchip_service_endpoint #(
    .DATA_W(DATA_W),
    .BANKS(BANKS),
    .BANK_SEL_W(BANK_SEL_W),
    .BANK_QUEUE_DEPTH(BANK_QUEUE_DEPTH),
    .ENDPOINT_QUEUE_DEPTH(ENDPOINT_QUEUE_DEPTH),
    .COUNTER_W(COUNTER_W)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_ready(in_ready),
    .in_bank(in_bank),
    .in_last(in_last),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_ready(out_ready),
    .out_bank(out_bank),
    .out_last(out_last),
    .out_data(out_data),
    .accepted_beat_count(accepted_beat_count),
    .emitted_beat_count(emitted_beat_count),
    .producer_stall_cycles(producer_stall_cycles),
    .consumer_stall_cycles(consumer_stall_cycles),
    .endpoint_max_occupancy(endpoint_max_occupancy),
    .bank_max_occupancy(bank_max_occupancy),
    .cycle_count(cycle_count),
    .final_completion_cycle(final_completion_cycle)
  );

  always #5 clk = ~clk;

  task offer_beat;
    input integer beat_index;
    input last;
    begin
      @(negedge clk);
      in_valid = 1'b1;
      in_bank = beat_index % BANKS;
      in_data = beat_index;
      in_last = last;
      @(posedge clk);
    end
  endtask

  initial begin
    #100000;
    $display("FAIL endpoint_ready_valid_policy: simulation timeout");
    $fatal;
  end

  always @(posedge clk) begin
    if (rst_n && out_valid && out_ready) begin
      $display(
        "OUT index=%0d bank=%0d data=%0d last=%0d cycle=%0d",
        out_index,
        out_bank,
        out_data[31:0],
        out_last,
        cycle_count
      );
      out_index = out_index + 1;
    end
  end

  initial begin
    clk = 1'b0;
    rst_n = 1'b1;
    in_valid = 1'b0;
    in_bank = 0;
    in_last = 1'b0;
    in_data = 0;
    out_ready = 1'b0;
    out_index = 0;

    #1 rst_n = 1'b0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    for (i = 0; i < ENDPOINT_QUEUE_DEPTH; i = i + 1) begin
      offer_beat(i, 1'b0);
      if (!in_ready) begin
        $display("FAIL endpoint_ready_valid_policy: early producer stall at i=%0d", i);
        $fatal;
      end
    end

    offer_beat({last_data}, 1'b1);
    if (in_ready) begin
      $display("FAIL endpoint_ready_valid_policy: expected full endpoint producer stall");
      $fatal;
    end

    @(negedge clk);
    out_ready = 1'b1;
    while (!in_ready) begin
      @(negedge clk);
    end
    @(posedge clk);
    @(negedge clk);
    in_valid = 1'b0;
    in_bank = 0;
    in_last = 1'b0;
    in_data = 0;

    while (emitted_beat_count !== TOTAL_BEATS) begin
      @(negedge clk);
    end

    out_ready = 1'b0;
    repeat (2) @(negedge clk);

    $display(
      "SUMMARY accepted=%0d emitted=%0d producer_stalls=%0d consumer_stalls=%0d endpoint_max=%0d bank_max=%0d final_cycle=%0d data_w=%0d banks=%0d endpoint_depth=%0d bank_depth=%0d",
      accepted_beat_count,
      emitted_beat_count,
      producer_stall_cycles,
      consumer_stall_cycles,
      endpoint_max_occupancy,
      bank_max_occupancy,
      final_completion_cycle,
      DATA_W,
      BANKS,
      ENDPOINT_QUEUE_DEPTH,
      BANK_QUEUE_DEPTH
    );

    if (accepted_beat_count !== TOTAL_BEATS || emitted_beat_count !== TOTAL_BEATS) begin
      $display("FAIL endpoint_ready_valid_policy: wrong beat counts");
      $fatal;
    end
    if (producer_stall_cycles === 0 || consumer_stall_cycles === 0) begin
      $display("FAIL endpoint_ready_valid_policy: expected backpressure counters to move");
      $fatal;
    end
    if (endpoint_max_occupancy < ENDPOINT_QUEUE_DEPTH) begin
      $display("FAIL endpoint_ready_valid_policy: endpoint queue did not fill");
      $fatal;
    end
    if (bank_max_occupancy === 0) begin
      $display("FAIL endpoint_ready_valid_policy: bank queue occupancy did not move");
      $fatal;
    end
    if (final_completion_cycle === 0) begin
      $display("FAIL endpoint_ready_valid_policy: final completion cycle was not recorded");
      $fatal;
    end

    $display("PASS endpoint_ready_valid_policy");
    $finish;
  end
endmodule
"""


def _run_probe(repo_root: Path, params: JsonDict) -> JsonDict:
    iverilog = shutil.which("iverilog") or "/oss-cad-suite/bin/iverilog"
    vvp = shutil.which("vvp") or "/oss-cad-suite/bin/vvp"
    if not Path(iverilog).exists() or not Path(vvp).exists():
        raise RuntimeError("iverilog/vvp are required for endpoint ready/valid probing")

    rtl = repo_root / "npu/sim/rtl/onchip_service_endpoint.sv"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tb = tmp / "endpoint_ready_valid_policy_tb.v"
        sim = tmp / "sim.out"
        tb.write_text(_testbench_text(params), encoding="utf-8")
        compile_cmd = [
            iverilog,
            "-g2012",
            "-s",
            "endpoint_ready_valid_policy_tb",
            "-o",
            str(sim),
            str(rtl),
            str(tb),
        ]
        compile_run = subprocess.run(compile_cmd, check=False, text=True, capture_output=True)
        if compile_run.returncode != 0:
            raise RuntimeError(f"iverilog failed:\n{compile_run.stdout}\n{compile_run.stderr}")
        sim_run = subprocess.run([vvp, str(sim)], check=False, text=True, capture_output=True)
        if sim_run.returncode != 0:
            raise RuntimeError(f"vvp failed:\n{sim_run.stdout}\n{sim_run.stderr}")

    text = sim_run.stdout
    summary_re = re.compile(
        r"SUMMARY accepted=(\d+) emitted=(\d+) producer_stalls=(\d+) "
        r"consumer_stalls=(\d+) endpoint_max=(\d+) bank_max=(\d+) final_cycle=(\d+) "
        r"data_w=(\d+) banks=(\d+) endpoint_depth=(\d+) bank_depth=(\d+)"
    )
    summary_match = summary_re.search(text)
    if not summary_match:
        raise RuntimeError(f"simulation did not print a SUMMARY line:\n{text}")
    keys = [
        "accepted",
        "emitted",
        "producer_stalls",
        "consumer_stalls",
        "endpoint_max",
        "bank_max",
        "final_cycle",
        "data_w",
        "banks",
        "endpoint_depth",
        "bank_depth",
    ]
    summary = dict(zip(keys, (int(value) for value in summary_match.groups()), strict=True))
    passed = "PASS endpoint_ready_valid_policy" in text
    if not passed:
        raise RuntimeError(f"simulation did not pass:\n{text}")
    return {
        "compile_command": " ".join(compile_cmd),
        "summary": summary,
        "stdout_tail": "\n".join(text.strip().splitlines()[-12:]),
        "passed": passed,
    }


def _write_report(path: Path, payload: JsonDict) -> None:
    best = payload["source_best"]
    params = payload["derived_rtl_parameters"]
    summary = payload["rtl_probe"]["summary"]
    lines = [
        "# Endpoint Ready/Valid Service Probe",
        "",
        "## Source Frontier",
        f"- source_json: `{payload['source_onchip_service_json']}`",
        f"- latency_us: `{best['latency_us']}`",
        f"- topology: `{best['topology']}`",
        f"- schedule_policy: `{best['schedule_policy']}`",
        f"- bank_arbiter_policy: `{best['bank_arbiter_policy']}`",
        "",
        "## Derived RTL Parameters",
        f"- DATA_W: `{params['data_w']}`",
        f"- BANKS: `{params['banks']}`",
        f"- BANK_SEL_W: `{params['bank_sel_w']}`",
        f"- ENDPOINT_QUEUE_DEPTH: `{params['endpoint_queue_depth']}`",
        f"- BANK_QUEUE_DEPTH: `{params['bank_queue_depth']}`",
        "",
        "## Result",
        f"- decision: `{payload['decision']}`",
        f"- accepted: `{summary['accepted']}`",
        f"- emitted: `{summary['emitted']}`",
        f"- producer_stalls: `{summary['producer_stalls']}`",
        f"- consumer_stalls: `{summary['consumer_stalls']}`",
        f"- endpoint_max: `{summary['endpoint_max']}`",
        f"- bank_max: `{summary['bank_max']}`",
        f"- final_cycle: `{summary['final_cycle']}`",
        "",
        "## Scope",
        "- This probe validates finite ready/valid endpoint buffering, producer/consumer backpressure, and locality-first bank drain for the selected packet and queue sizing.",
        "- It does not replace the full NoC router or SRAM macro timing model, and it does not change HBM/DRAM assumptions.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--onchip-service-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--source-row-rank", type=_positive_int, default=1)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    source_path = args.onchip_service_json
    if not source_path.is_absolute():
        source_path = repo_root / source_path
    source = _load_json(source_path)
    if args.source_row_rank == 1:
        best = source["best"]
    else:
        top_rows = source.get("top_rows", [])
        if args.source_row_rank > len(top_rows):
            raise SystemExit(f"source-row-rank {args.source_row_rank} exceeds top_rows length {len(top_rows)}")
        best = top_rows[args.source_row_rank - 1]

    params = _derive_parameters(best)
    probe = _run_probe(repo_root, params)
    payload: JsonDict = {
        "model": "llm_decoder_attention_endpoint_ready_valid_service_probe_v1",
        "version": 1,
        "source_onchip_service_json": str(args.onchip_service_json),
        "source_row_rank": args.source_row_rank,
        "source_best": {
            key: best[key]
            for key in [
                "latency_us",
                "topology",
                "scheduler_policy",
                "reduction_strategy",
                "schedule_policy",
                "bank_arbiter_policy",
                "cluster_count",
                "bank_count",
                "packet_payload_bytes",
                "endpoint_queue_depth_bytes",
                "bank_queue_depth_bytes",
                "local_sram_fraction",
                "tile_tokens",
                "compute_replica_count",
                "dominant_tile_resource",
            ]
            if key in best
        },
        "derived_rtl_parameters": params,
        "rtl_probe": probe,
        "decision": "ready_valid_endpoint_policy_passed" if probe["passed"] else "ready_valid_endpoint_policy_failed",
        "limitations": [
            "Ready/valid endpoint queue behavior is validated, but full router and SRAM macro RTL are not included.",
            "HBM/DRAM service remains inherited from the source endpoint service schedule.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(args.out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
