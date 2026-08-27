#!/usr/bin/env python3
"""Replay one exact Llama7B NoC router trace through RTL and emit a verified VCD."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.extract_sequential_register_vcd_activity import (  # noqa: E402
    extract_sequential_register_vcd_activity,
)
from npu.eval.generate_llm_decoder_attention_score32_noc_router_activity import (  # noqa: E402
    DEFAULT_SCHEDULE_JSON,
    _canonical_sha256,
    _sha256_file,
    build_router_activity_manifest,
    reproduce_schedule_mesh,
)
from npu.sim.perf.noc_segmented_mesh import (  # noqa: E402
    PORTS,
    MeshSimulationResult,
    iter_router_replay_cycles,
    verify_router_replay,
)

JsonDict = dict[str, Any]
_RTL_SOURCES = (
    Path("npu/sim/rtl/noc_ready_valid_fifo.sv"),
    Path("npu/sim/rtl/noc_segmented_mesh_router.sv"),
    Path("npu/sim/rtl/noc_segmented_mesh_router_node5.sv"),
)
_FORWARDED_RE = re.compile(
    r"^(?P<cycle>\d+) (?P<port>\d+) (?P<source>[0-9a-f]+) (?P<destination>[0-9a-f]+) "
    r"(?P<tag>[0-9a-f]+) (?P<fragment>[0-9a-f]+) (?P<last>[01]) (?P<vc>[0-9a-f]+) "
    r"(?P<data>[0-9a-f]+)$"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY accepted=(?P<accepted>\d+) forwarded=(?P<forwarded>\d+) "
    r"istall=(?P<istall>\d+) ostall=(?P<ostall>\d+) contention=(?P<contention>\d+) "
    r"occ=(?P<occ>\d+) maxocc=(?P<maxocc>\d+) routes="
    r"(?P<route0>\d+),(?P<route1>\d+),(?P<route2>\d+),(?P<route3>\d+),(?P<route4>\d+)"
)


def _tool(name: str) -> str:
    candidate = shutil.which(name)
    if candidate:
        return candidate
    bundled = Path("/oss-cad-suite/bin") / name
    if bundled.is_file():
        return str(bundled)
    raise RuntimeError(f"required RTL simulation tool is unavailable: {name}")


def _pack(values: list[int], width: int) -> int:
    packed = 0
    for index, value in enumerate(values):
        packed |= int(value) << (index * width)
    return packed


def _write_replay_events(mesh_result: MeshSimulationResult, *, node: int, path: Path) -> int:
    lines: list[str] = []
    for cycle, inputs, out_ready, expected_trace in iter_router_replay_cycles(
        mesh_result,
        node=node,
    ):
        valid = [int(slot.valid) for slot in inputs]
        expected_ready = (
            list(expected_trace.ready) if expected_trace is not None else [True] * PORTS
        )
        if not any(valid) and all(out_ready) and all(expected_ready):
            continue
        flits = [slot.flit if slot.valid else None for slot in inputs]
        destination = [flit.destination if flit is not None else 0 for flit in flits]
        source = [flit.source if flit is not None else 0 for flit in flits]
        tag = [flit.tag if flit is not None else 0 for flit in flits]
        fragment = [flit.fragment if flit is not None else 0 for flit in flits]
        last = [int(flit.last) if flit is not None else 0 for flit in flits]
        vc = [flit.vc if flit is not None else 0 for flit in flits]
        data = [flit.data if flit is not None else 0 for flit in flits]
        lines.append(
            " ".join(
                (
                    str(cycle),
                    f"{_pack(valid, 1):02x}",
                    f"{_pack(destination, 4):05x}",
                    f"{_pack(source, 4):05x}",
                    f"{_pack(tag, 8):010x}",
                    f"{_pack(fragment, 3):04x}",
                    f"{_pack(last, 1):02x}",
                    f"{_pack(vc, 2):03x}",
                    f"{_pack(data, 256):0320x}",
                    f"{_pack([int(value) for value in out_ready], 1):02x}",
                    f"{_pack([int(value) for value in expected_ready], 1):02x}",
                )
            )
            + "\n"
        )
    path.write_text("".join(lines), encoding="ascii")
    return len(lines)


def _expected_forwarded(mesh_result: MeshSimulationResult, *, node: int) -> list[tuple[int, ...]]:
    expected: list[tuple[int, ...]] = []
    for mesh_trace in mesh_result.traces:
        trace = mesh_trace.router_traces[node]
        for port, flit in trace.forwarded:
            expected.append(
                (
                    trace.cycle,
                    port,
                    flit.source,
                    flit.destination,
                    flit.tag,
                    flit.fragment,
                    int(flit.last),
                    flit.vc,
                    flit.data,
                )
            )
    return expected


def _testbench(
    *,
    node: int,
    cycles: int,
    clock_period_ns: float,
    replay_path: Path,
    forwarded_path: Path,
    vcd_path: Path,
) -> str:
    x_coord = node % 4
    y_coord = node // 4
    return f"""`timescale 1ns/1ps
module tb;
  localparam real HALF_PERIOD = {clock_period_ns:.17g} / 2.0;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg [4:0] in_valid = 5'b0;
  wire [4:0] in_ready;
  reg [19:0] in_dest = 20'b0;
  reg [19:0] in_source = 20'b0;
  reg [39:0] in_tag = 40'b0;
  reg [14:0] in_fragment = 15'b0;
  reg [4:0] in_last = 5'b0;
  reg [9:0] in_vc = 10'b0;
  reg [1279:0] in_data = 1280'b0;
  wire [4:0] out_valid;
  reg [4:0] out_ready = 5'b11111;
  wire [19:0] out_dest;
  wire [19:0] out_source;
  wire [39:0] out_tag;
  wire [14:0] out_fragment;
  wire [4:0] out_last;
  wire [9:0] out_vc;
  wire [1279:0] out_data;
  wire [31:0] accepted_flit_count;
  wire [31:0] forwarded_flit_count;
  wire [31:0] input_stall_cycles;
  wire [31:0] output_stall_cycles;
  wire [31:0] arbitration_contention_cycles;
  wire [31:0] current_input_occupancy;
  wire [31:0] max_input_occupancy;
  wire [159:0] route_flit_count;
  integer replay_file;
  integer forwarded_file;
  integer scan_status;
  integer next_cycle;
  integer cycle_i;
  integer port_i;
  reg [4:0] next_in_valid;
  reg [19:0] next_in_dest;
  reg [19:0] next_in_source;
  reg [39:0] next_in_tag;
  reg [14:0] next_in_fragment;
  reg [4:0] next_in_last;
  reg [9:0] next_in_vc;
  reg [1279:0] next_in_data;
  reg [4:0] next_out_ready;
  reg [4:0] next_expected_ready;
  reg [4:0] expected_ready;

  noc_segmented_mesh_router_node5 #(.X_COORD({x_coord}), .Y_COORD({y_coord})) dut (
    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready),
    .in_dest(in_dest), .in_source(in_source), .in_tag(in_tag),
    .in_fragment(in_fragment), .in_last(in_last), .in_vc(in_vc), .in_data(in_data),
    .out_valid(out_valid), .out_ready(out_ready), .out_dest(out_dest),
    .out_source(out_source), .out_tag(out_tag), .out_fragment(out_fragment),
    .out_last(out_last), .out_vc(out_vc), .out_data(out_data),
    .accepted_flit_count(accepted_flit_count), .forwarded_flit_count(forwarded_flit_count),
    .input_stall_cycles(input_stall_cycles), .output_stall_cycles(output_stall_cycles),
    .arbitration_contention_cycles(arbitration_contention_cycles),
    .current_input_occupancy(current_input_occupancy),
    .max_input_occupancy(max_input_occupancy), .route_flit_count(route_flit_count)
  );

  always #(HALF_PERIOD) clk = ~clk;

  task load_next_event;
    begin
      scan_status = $fscanf(replay_file, "%d %h %h %h %h %h %h %h %h %h %h\\n",
        next_cycle, next_in_valid, next_in_dest, next_in_source, next_in_tag,
        next_in_fragment, next_in_last, next_in_vc, next_in_data,
        next_out_ready, next_expected_ready);
      if (scan_status != 11)
        next_cycle = -1;
    end
  endtask

  task drive_cycle(input integer cycle);
    begin
      in_valid = 5'b0;
      in_dest = 20'b0;
      in_source = 20'b0;
      in_tag = 40'b0;
      in_fragment = 15'b0;
      in_last = 5'b0;
      in_vc = 10'b0;
      in_data = 1280'b0;
      out_ready = 5'b11111;
      expected_ready = 5'b11111;
      if (next_cycle == cycle) begin
        in_valid = next_in_valid;
        in_dest = next_in_dest;
        in_source = next_in_source;
        in_tag = next_in_tag;
        in_fragment = next_in_fragment;
        in_last = next_in_last;
        in_vc = next_in_vc;
        in_data = next_in_data;
        out_ready = next_out_ready;
        expected_ready = next_expected_ready;
        load_next_event();
      end
      if (next_cycle >= 0 && next_cycle < cycle)
        $fatal(1, "replay event order failure at cycle %0d", cycle);
    end
  endtask

  initial begin
    replay_file = $fopen("{replay_path}", "r");
    forwarded_file = $fopen("{forwarded_path}", "w");
    if (replay_file == 0 || forwarded_file == 0)
      $fatal(1, "failed to open router replay files");
    $dumpfile("{vcd_path}");
    $dumpvars(0, dut);
    $dumpoff;
    load_next_event();
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    $dumpon;
    for (cycle_i = 0; cycle_i < {cycles}; cycle_i = cycle_i + 1) begin
      drive_cycle(cycle_i);
      #0.001;
      if (in_ready !== expected_ready)
        $fatal(1, "in_ready mismatch cycle=%0d expected=%h observed=%h",
          cycle_i, expected_ready, in_ready);
      @(posedge clk);
      for (port_i = 0; port_i < 5; port_i = port_i + 1) begin
        if (out_valid[port_i] && out_ready[port_i])
          $fdisplay(forwarded_file, "%0d %0d %h %h %h %h %h %h %h",
            cycle_i, port_i,
            out_source[(port_i*4)+:4], out_dest[(port_i*4)+:4],
            out_tag[(port_i*8)+:8], out_fragment[(port_i*3)+:3],
            out_last[port_i], out_vc[(port_i*2)+:2], out_data[(port_i*256)+:256]);
      end
      @(negedge clk);
    end
    if (next_cycle >= 0)
      $fatal(1, "unconsumed replay event at cycle %0d", next_cycle);
    $dumpoff;
    $display({{"SUMMARY accepted=%0d forwarded=%0d istall=%0d ostall=%0d contention=%0d ",
      "occ=%0d maxocc=%0d routes=%0d,%0d,%0d,%0d,%0d"}},
      accepted_flit_count, forwarded_flit_count, input_stall_cycles, output_stall_cycles,
      arbitration_contention_cycles, current_input_occupancy, max_input_occupancy,
      route_flit_count[31:0], route_flit_count[63:32], route_flit_count[95:64],
      route_flit_count[127:96], route_flit_count[159:128]);
    $fclose(replay_file);
    $fclose(forwarded_file);
    $finish;
  end
endmodule
"""


def _normalize_vcd(path: Path) -> None:
    normalized_path = path.with_suffix(path.suffix + ".normalized")
    in_date = False
    with path.open("r", encoding="utf-8", errors="replace") as source, normalized_path.open(
        "w",
        encoding="utf-8",
    ) as destination:
        for line in source:
            if line.strip() == "$date":
                destination.write("$date\n  deterministic_router_activity_v1\n")
                in_date = True
                continue
            if in_date:
                if line.strip() == "$end":
                    destination.write("$end\n")
                    in_date = False
                continue
            destination.write(line)
    normalized_path.replace(path)


def _parse_forwarded(path: Path) -> list[tuple[int, ...]]:
    observed: list[tuple[int, ...]] = []
    for line in path.read_text(encoding="ascii").splitlines():
        match = _FORWARDED_RE.fullmatch(line.strip())
        if match is None:
            raise ValueError(f"malformed RTL forwarded event: {line}")
        values = match.groupdict()
        observed.append(
            (
                int(values["cycle"]),
                int(values["port"]),
                int(values["source"], 16),
                int(values["destination"], 16),
                int(values["tag"], 16),
                int(values["fragment"], 16),
                int(values["last"], 16),
                int(values["vc"], 16),
                int(values["data"], 16),
            )
        )
    return observed


def run_rtl_activity(
    mesh_result: MeshSimulationResult,
    *,
    node: int,
    clock_period_ns: float,
    out_dir: Path,
    timeout_seconds: int,
) -> JsonDict:
    out_dir.mkdir(parents=True, exist_ok=True)
    replay_path = out_dir / f"router_node{node}_replay.txt"
    forwarded_path = out_dir / f"router_node{node}_rtl_forwarded.txt"
    vcd_path = out_dir / f"router_node{node}_activity.vcd"
    tb_path = out_dir / f"router_node{node}_activity_tb.sv"
    simv_path = out_dir / f"router_node{node}_activity_simv"
    event_count = _write_replay_events(mesh_result, node=node, path=replay_path)
    tb_path.write_text(
        _testbench(
            node=node,
            cycles=mesh_result.cycles,
            clock_period_ns=clock_period_ns,
            replay_path=replay_path.resolve(),
            forwarded_path=forwarded_path.resolve(),
            vcd_path=vcd_path.resolve(),
        ),
        encoding="utf-8",
    )
    compile_result = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv_path),
            *(str(_REPO_ROOT / source) for source in _RTL_SOURCES),
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if compile_result.returncode:
        raise RuntimeError(f"iverilog failed:\n{compile_result.stderr}")
    simulation = subprocess.run(
        [_tool("vvp"), str(simv_path)],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if simulation.returncode:
        raise RuntimeError(f"router RTL replay failed:\n{simulation.stdout}\n{simulation.stderr}")
    summary_match = _SUMMARY_RE.search(simulation.stdout)
    if summary_match is None:
        raise RuntimeError(f"router RTL replay did not emit a summary:\n{simulation.stdout}")
    expected_forwarded = _expected_forwarded(mesh_result, node=node)
    observed_forwarded = _parse_forwarded(forwarded_path)
    if observed_forwarded != expected_forwarded:
        raise ValueError("RTL forwarded-flit stream differs from the performance model")
    verification = asdict(verify_router_replay(mesh_result, node=node))
    summary = {key: int(value) for key, value in summary_match.groupdict().items()}
    expected_summary = {
        "accepted": verification["accepted_flit_count"],
        "forwarded": verification["forwarded_flit_count"],
        "istall": verification["input_stall_cycles"],
        "ostall": verification["output_stall_cycles"],
        "contention": verification["arbitration_contention_cycles"],
        "occ": verification["current_input_occupancy"],
        "maxocc": verification["max_input_occupancy"],
        **{
            f"route{index}": verification["route_flit_count"][index]
            for index in range(PORTS)
        },
    }
    if summary != expected_summary:
        raise ValueError(f"RTL counter summary differs: expected {expected_summary}, got {summary}")
    _normalize_vcd(vcd_path)
    vcd_sha256 = _sha256_file(vcd_path)
    sequential_path = out_dir / f"router_node{node}_sequential_register_activity.json"
    sequential = extract_sequential_register_vcd_activity(
        vcd_path,
        source_vcd_sha256=vcd_sha256,
        scope="tb/dut",
    )
    sequential_path.write_text(
        json.dumps(sequential, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "replay_event_count": event_count,
        "forwarded_event_count": len(observed_forwarded),
        "forwarded_event_sha256": _canonical_sha256(observed_forwarded),
        "vcd": vcd_path.name,
        "vcd_sha256": vcd_sha256,
        "sequential_register_activity": sequential_path.name,
        "sequential_register_activity_sha256": _sha256_file(sequential_path),
        "rtl_summary": summary,
        "equivalence_status": "pass",
        "equivalence_scope": "all cycle in_ready values, forwarded flit fields/data, and final counters",
    }


def build_manifest(
    *,
    repo_root: Path,
    schedule_json: Path,
    node: int,
    out_dir: Path,
    timeout_seconds: int,
) -> JsonDict:
    absolute_schedule = schedule_json if schedule_json.is_absolute() else repo_root / schedule_json
    schedule, reproduced_semantics, mesh_result = reproduce_schedule_mesh(
        repo_root=repo_root,
        schedule_json=schedule_json,
        node=node,
    )
    clock_period_ns = float(schedule["source_contract"]["noc_clock_ns"])
    payload = build_router_activity_manifest(
        mesh_result,
        node=node,
        source_schedule_path=str(schedule_json),
        source_schedule_sha256=_sha256_file(absolute_schedule),
        source_schedule_semantic_sha256=_canonical_sha256(reproduced_semantics),
        clock_period_ns=clock_period_ns,
    )
    rtl = run_rtl_activity(
        mesh_result,
        node=node,
        clock_period_ns=clock_period_ns,
        out_dir=out_dir,
        timeout_seconds=timeout_seconds,
    )
    payload["model"] = "llama7b_score32_noc_router_exact_rtl_activity"
    payload["rtl_activity"] = rtl
    payload["phases"] = [
        {
            "phase": "full_phase2_router_replay",
            "vcd": rtl["vcd"],
            "vcd_sha256": rtl["vcd_sha256"],
            "sequential_register_activity": rtl["sequential_register_activity"],
            "sequential_register_activity_sha256": rtl[
                "sequential_register_activity_sha256"
            ],
            "measured_cycles": mesh_result.cycles,
            "full_context_cycles": mesh_result.cycles,
            "requires_macro_activity": False,
        }
    ]
    payload["remaining_abstractions"] = [
        "The VCD covers the logic-free node-5 specialization of the bare source router RTL; the "
        "matching bare-router physical result is required before post-route power can be accepted.",
        "Inter-router wires and composed clock-tree power require the routed 4x4 mesh measurement.",
        "HBM/DRAM controller and PHY power remain outside the on-chip router scope.",
    ]
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--schedule-json", type=Path, default=DEFAULT_SCHEDULE_JSON)
    parser.add_argument("--node", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    payload = build_manifest(
        repo_root=args.repo_root.resolve(),
        schedule_json=args.schedule_json,
        node=args.node,
        out_dir=args.out_dir.resolve(),
        timeout_seconds=args.timeout_seconds,
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
