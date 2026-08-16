#!/usr/bin/env python3
"""Replay the Llama7B Phase-2 packet schedule through endpoint plus mesh RTL."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (  # noqa: E402
    DEFAULT_MEASURED_L1_COSTS,
    DEFAULT_SOURCE_JSON,
    PacketSpec,
    _packetize_specs_with_concrete_tags,
    build_report,
)
from npu.sim.perf.noc_sram_packet_mesh import (  # noqa: E402
    PacketDescriptor,
    simulate_packet_mesh,
)

JsonDict = dict[str, Any]
MAX_PACKETS = 12000
RTL_SOURCES = (
    Path("npu/sim/rtl/noc_ready_valid_fifo.sv"),
    Path("npu/sim/rtl/noc_segmented_mesh_router.sv"),
    Path("npu/sim/rtl/noc_segmented_mesh4x4.sv"),
    Path("npu/sim/rtl/noc_sram_packet_endpoint.sv"),
    Path("npu/sim/rtl/noc_sram_packet_mesh4x4.sv"),
)
RTL_TB = Path("tests/noc_sram_packet_mesh4x4_workload_tb.sv")
PASS_RE = re.compile(
    r"PASS workload packets=(?P<packets>\d+) flits=(?P<flits>\d+) "
    r"cycles=(?P<cycles>\d+) contention=(?P<contention>\d+) "
    r"input_stalls=(?P<input_stalls>\d+) max_occupancy=(?P<max_occupancy>\d+)"
)


@dataclass(frozen=True)
class WorkloadPacket:
    packet_id: int
    schedule_order: int
    release_cycle: int
    source: int
    destination: int
    vc: int
    tag: int
    flit_count: int
    label: str


@dataclass(frozen=True)
class WorkloadMemoryPaths:
    descriptors: Path
    source_order: Path
    destination_order: Path
    source_meta: Path
    destination_meta: Path


def _tool(name: str) -> str:
    candidate = shutil.which(name)
    if candidate:
        return candidate
    bundled = Path("/oss-cad-suite/bin") / name
    if bundled.exists():
        return str(bundled)
    raise RuntimeError(f"required RTL simulation tool is unavailable: {name}")


def _flit_count(payload_bytes: int) -> int:
    return (payload_bytes + 31) // 32


def descriptors_from_packet_specs(packet_specs: list[PacketSpec]) -> list[WorkloadPacket]:
    flows = _packetize_specs_with_concrete_tags(packet_specs)
    if len(flows) != len(packet_specs):
        raise ValueError("packet specification and concrete-tag flow counts differ")
    if len(flows) > MAX_PACKETS:
        raise ValueError(f"workload has {len(flows)} packets; RTL replay limit is {MAX_PACKETS}")
    packets: list[WorkloadPacket] = []
    for packet_id, (spec, flow) in enumerate(zip(packet_specs, flows, strict=True)):
        flit_count = _flit_count(spec.payload_bytes)
        if not 1 <= flit_count <= 8:
            raise ValueError(f"packet {spec.label} has unsupported flit count {flit_count}")
        packets.append(
            WorkloadPacket(
                packet_id=packet_id,
                schedule_order=flow.schedule_order,
                release_cycle=spec.release_cycle,
                source=spec.source,
                destination=spec.destination,
                vc=spec.vc,
                tag=flow.tag_base & 0xFF,
                flit_count=flit_count,
                label=spec.label,
            )
        )
    return packets


def _write_hex_lines(path: Path, values: Iterable[int], width: int) -> None:
    path.write_text(
        "".join(f"{value:0{width}x}\n" for value in values),
        encoding="ascii",
    )


def _queue_order_and_meta(
    packets: list[WorkloadPacket],
    *,
    endpoint_field: str,
) -> tuple[list[int], list[int]]:
    order: list[int] = []
    meta: list[int] = []
    for endpoint in range(16):
        endpoint_packets = sorted(
            (
                packet
                for packet in packets
                if int(getattr(packet, endpoint_field)) == endpoint
            ),
            key=lambda packet: (packet.release_cycle, packet.schedule_order),
        )
        offset = len(order)
        count = len(endpoint_packets)
        if offset > 0xFFFF or count > 0xFFFF:
            raise ValueError("workload queue metadata exceeds 16-bit fields")
        order.extend(packet.packet_id for packet in endpoint_packets)
        meta.append((count << 16) | offset)
    if len(order) != len(packets) or sorted(order) != list(range(len(packets))):
        raise ValueError(f"{endpoint_field} queue order is not a packet permutation")
    return order, meta


def write_workload_memories(
    packets: list[WorkloadPacket],
    output_dir: Path,
) -> WorkloadMemoryPaths:
    if not packets:
        raise ValueError("RTL workload must contain at least one packet")
    output_dir.mkdir(parents=True, exist_ok=True)
    descriptors = output_dir / "descriptors.mem"
    source_order_path = output_dir / "source_order.mem"
    destination_order_path = output_dir / "destination_order.mem"
    source_meta_path = output_dir / "source_meta.mem"
    destination_meta_path = output_dir / "destination_meta.mem"

    words: list[int] = []
    for expected_id, packet in enumerate(packets):
        if packet.packet_id != expected_id:
            raise ValueError("packet IDs must be dense and array ordered")
        if not 0 <= packet.release_cycle <= 0xFFFFFFFF:
            raise ValueError(f"packet {packet.label} release cycle exceeds 32 bits")
        if not 0 <= packet.source < 16 or not 0 <= packet.destination < 16:
            raise ValueError(f"packet {packet.label} endpoint is outside the 4x4 mesh")
        if not 0 <= packet.vc < 4 or not 0 <= packet.tag < 256:
            raise ValueError(f"packet {packet.label} VC/tag is outside the wire contract")
        word = packet.release_cycle
        word |= packet.source << 32
        word |= packet.destination << 36
        word |= packet.vc << 40
        word |= packet.tag << 42
        word |= packet.flit_count << 50
        words.append(word)
    _write_hex_lines(descriptors, words, 24)

    source_order, source_meta = _queue_order_and_meta(packets, endpoint_field="source")
    destination_order, destination_meta = _queue_order_and_meta(
        packets, endpoint_field="destination"
    )
    _write_hex_lines(source_order_path, source_order, 4)
    _write_hex_lines(destination_order_path, destination_order, 4)
    _write_hex_lines(source_meta_path, source_meta, 8)
    _write_hex_lines(destination_meta_path, destination_meta, 8)
    return WorkloadMemoryPaths(
        descriptors=descriptors,
        source_order=source_order_path,
        destination_order=destination_order_path,
        source_meta=source_meta_path,
        destination_meta=destination_meta_path,
    )


def run_rtl_replay(
    *,
    repo_root: Path,
    packets: list[WorkloadPacket],
    work_dir: Path,
    timeout_cycles: int,
    wall_timeout_seconds: int,
) -> JsonDict:
    memories = write_workload_memories(packets, work_dir)
    simulator = work_dir / "phase2_endpoint_mesh.vvp"
    compile_result = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "noc_sram_packet_mesh4x4_workload_tb",
            "-o",
            str(simulator),
            *[str(repo_root / path) for path in RTL_SOURCES],
            str(repo_root / RTL_TB),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if compile_result.returncode != 0:
        raise RuntimeError(
            "endpoint mesh RTL compilation failed\n"
            f"stdout:\n{compile_result.stdout}\n"
            f"stderr:\n{compile_result.stderr}"
        )
    expected_flits = sum(packet.flit_count for packet in packets)
    command = [
        _tool("vvp"),
        str(simulator),
        f"+PACKET_COUNT={len(packets)}",
        f"+EXPECTED_FLITS={expected_flits}",
        f"+TIMEOUT_CYCLES={timeout_cycles}",
        f"+DESC_MEM={memories.descriptors}",
        f"+SRC_ORDER_MEM={memories.source_order}",
        f"+DST_ORDER_MEM={memories.destination_order}",
        f"+SRC_META_MEM={memories.source_meta}",
        f"+DST_META_MEM={memories.destination_meta}",
    ]
    process = subprocess.Popen(
        command,
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def _drain(stream: Any, lines: list[str], *, destination: Any) -> None:
        for line in stream:
            lines.append(line)
            print(line, end="", file=destination, flush=True)

    stdout_thread = threading.Thread(
        target=_drain,
        args=(process.stdout, stdout_lines),
        kwargs={"destination": sys.stdout},
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_drain,
        args=(process.stderr, stderr_lines),
        kwargs={"destination": sys.stderr},
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    try:
        return_code = process.wait(timeout=wall_timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise
    finally:
        stdout_thread.join(timeout=10)
        stderr_thread.join(timeout=10)
    simulation_stdout = "".join(stdout_lines)
    simulation_stderr = "".join(stderr_lines)
    if return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            command,
            output=simulation_stdout,
            stderr=simulation_stderr,
        )
    match = PASS_RE.search(simulation_stdout)
    if match is None:
        raise ValueError(f"RTL replay did not emit its PASS record:\n{simulation_stdout}")
    counters = {key: int(value) for key, value in match.groupdict().items()}
    if counters["packets"] != len(packets) or counters["flits"] != expected_flits:
        raise ValueError(f"RTL replay count mismatch: {counters}")
    return {
        "counters": counters,
        "compile_stdout": compile_result.stdout,
        "compile_stderr": compile_result.stderr,
        "simulation_stdout": simulation_stdout,
        "simulation_stderr": simulation_stderr,
    }


def run_performance_replay(
    packets: list[WorkloadPacket],
    *,
    max_cycles: int,
) -> JsonDict:
    result = simulate_packet_mesh(
        [
            PacketDescriptor(
                source=packet.source,
                destination=packet.destination,
                vc=packet.vc,
                tag=packet.tag,
                flit_count=packet.flit_count,
                tx_base_addr=packet.packet_id << 8,
                rx_base_addr=packet.packet_id << 8,
                release_cycle=packet.release_cycle,
                schedule_order=packet.schedule_order,
                data_seed=packet.packet_id,
                packet_id=packet.label,
            )
            for packet in packets
        ],
        max_cycles=max_cycles,
    )
    counters = {
        "packets": len(result.completions),
        "flits": len(result.destination_memory_writes),
        "cycles": result.cycles,
        "contention": sum(
            router.arbitration_contention_cycles for router in result.router_summaries
        ),
        "input_stalls": sum(router.input_stall_cycles for router in result.router_summaries),
        "max_occupancy": max(
            (router.max_input_occupancy for router in result.router_summaries),
            default=0,
        ),
        "max_rx_context_occupancy_per_endpoint": result.max_rx_context_occupancy,
        "rx_descriptor_handshakes": len(result.rx_descriptor_handshakes),
        "tx_descriptor_handshakes": len(result.tx_descriptor_handshakes),
        "source_memory_requests": len(result.source_memory_requests),
        "source_memory_responses": len(result.source_memory_responses),
        "protocol_errors": list(result.protocol_errors),
    }
    expected_flits = sum(packet.flit_count for packet in packets)
    required_counts = {
        "packets": len(packets),
        "flits": expected_flits,
        "rx_descriptor_handshakes": len(packets),
        "tx_descriptor_handshakes": len(packets),
        "source_memory_requests": expected_flits,
        "source_memory_responses": expected_flits,
    }
    mismatches = {
        key: {"expected": expected, "observed": counters[key]}
        for key, expected in required_counts.items()
        if counters[key] != expected
    }
    if mismatches or counters["protocol_errors"]:
        raise ValueError(
            "endpoint-aware performance replay failed: "
            f"count_mismatches={mismatches}, protocol_errors={counters['protocol_errors']}"
        )
    return counters


def _schedule_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=args.repo_root,
        source_json=args.source_json,
        measured_l1_costs=args.measured_l1_costs,
        wave_limit=args.wave_limit,
        packet_payload_bytes=256,
        cluster_endpoints=None,
        root_endpoint=15,
        shared_vc=0,
        reduction_vc=1,
        compute_clock_ns=None,
        noc_clock_ns=args.noc_clock_ns,
        max_cycles=args.schedule_max_cycles,
    )


def build_and_run(args: argparse.Namespace) -> JsonDict:
    packet_specs: list[PacketSpec] = []
    schedule = build_report(_schedule_args(args), packet_spec_output=packet_specs)
    packets = descriptors_from_packet_specs(packet_specs)
    performance = run_performance_replay(packets, max_cycles=args.rtl_timeout_cycles)
    with tempfile.TemporaryDirectory(prefix="rtlgen-phase2-endpoint-rtl-") as temporary:
        replay = run_rtl_replay(
            repo_root=args.repo_root.resolve(),
            packets=packets,
            work_dir=Path(temporary),
            timeout_cycles=args.rtl_timeout_cycles,
            wall_timeout_seconds=args.wall_timeout_seconds,
        )
    counters = replay["counters"]
    compared_fields = ("packets", "flits", "cycles", "contention", "input_stalls", "max_occupancy")
    mismatches = {
        field: {"performance": performance[field], "rtl": counters[field]}
        for field in compared_fields
        if performance[field] != counters[field]
    }
    if mismatches:
        raise ValueError(f"endpoint-aware performance/RTL mismatch: {mismatches}")
    return {
        "profile": "decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence",
        "version": 1,
        "coverage": schedule["source_contract"]["coverage"],
        "source_schedule": {
            "packet_count": schedule["simulation"]["scheduled_packet_count"],
            "flit_count": schedule["simulation"]["scheduled_flit_count"],
            "logical_release_queue_cycles_to_drain": schedule["simulation"]["cycles_to_drain"],
        },
        "rtl_replay": counters,
        "endpoint_aware_performance_replay": performance,
        "endpoint_cadence_delta_cycles": (
            counters["cycles"] - schedule["simulation"]["cycles_to_drain"]
        ),
        "equivalence": {
            "all_packets_completed": counters["packets"] == len(packets),
            "all_flits_written": counters["flits"] == sum(packet.flit_count for packet in packets),
            "rx_descriptor_precedes_tx_enforced": True,
            "source_sram_response_latency_cycles": 1,
            "rx_contexts_per_endpoint": 8,
            "tx_descriptor_depth": 4,
            "tx_outstanding_limit": 8,
            "wire_tag_width_bits": 8,
            "cycle_and_router_counter_match": True,
        },
        "remaining_abstractions": [
            "SRAM arrays are transaction-accurate one-cycle ports; bitcells and macro placement remain external.",
            "The command scheduler is embodied by the deterministic paired-descriptor testbench driver, not yet synthesized RTL.",
            "HBM/DRAM and its controller remain intentionally outside the design boundary.",
            "Workload-matched switching power requires a separate activity-capture run.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    source = payload["source_schedule"]
    rtl = payload["rtl_replay"]
    performance = payload["endpoint_aware_performance_replay"]
    lines = [
        "# Llama7B Phase-2 Endpoint/RTL Equivalence",
        "",
        f"- coverage: `{payload['coverage']}`",
        f"- packets/flits: `{rtl['packets']}` / `{rtl['flits']}`",
        f"- logical release-queue drain: `{source['logical_release_queue_cycles_to_drain']}` cycles",
        f"- finite endpoint/RTL drain: `{rtl['cycles']}` cycles",
        f"- endpoint cadence delta: `{payload['endpoint_cadence_delta_cycles']}` cycles",
        f"- router contention/input stalls: `{rtl['contention']}` / `{rtl['input_stalls']}`",
        f"- maximum router occupancy: `{rtl['max_occupancy']}`",
        f"- maximum RX contexts used per endpoint: `{performance['max_rx_context_occupancy_per_endpoint']}`",
        "- cycle and router counter equivalence: `true`",
        "",
        "## Remaining Abstractions",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-json", type=Path, default=DEFAULT_SOURCE_JSON)
    parser.add_argument("--measured-l1-costs", type=Path, default=DEFAULT_MEASURED_L1_COSTS)
    parser.add_argument("--wave-limit", type=int, default=None)
    parser.add_argument("--noc-clock-ns", type=float, default=1.0)
    parser.add_argument("--schedule-max-cycles", type=int, default=1000000)
    parser.add_argument("--rtl-timeout-cycles", type=int, default=2000000)
    parser.add_argument("--wall-timeout-seconds", type=int, default=1800)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = build_and_run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    print(json.dumps(payload["rtl_replay"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
