#!/usr/bin/env python3
"""Generate exact VC0/VC1 Llama7B router RTL activity phases."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.generate_llm_decoder_attention_score32_noc_router_rtl_activity import (  # noqa: E402
    _sha256_file,
    run_rtl_activity,
)
from npu.sim.perf.attention_shared_stream_context_service import (  # noqa: E402
    build_activity_contexts,
    simulate_context_service,
)
from npu.sim.perf.noc_segmented_mesh import MeshSimulationResult  # noqa: E402
from npu.sim.perf.noc_sram_packet_mesh import PacketMeshResult  # noqa: E402
from npu.sim.perf.stats_once_shared_root import (  # noqa: E402
    GROUP_FLITS,
    PACKETS_PER_GROUP,
    simulate_exact_stats_once_shared_root,
)

JsonDict = dict[str, Any]
SHARED_CONTEXTS = 112
SHARED_PACKETS = 7_616
SHARED_FLITS = 60_928
SHARED_CYCLES = 7_783
SHARED_WRITE_FOLD = 0x0000000000000D100000000000000D10
REDUCTION_GROUPS = 4
REDUCTION_SOURCES = 15


@dataclass(frozen=True)
class ExactRouterPhase:
    name: str
    transport_class: str
    mesh_result: MeshSimulationResult
    packet_count: int
    flit_count: int
    context_count: int
    service_cycles: int | None = None
    group: int | None = None


def _router_view(packet_mesh: PacketMeshResult) -> MeshSimulationResult:
    """Expose packet-mesh router traces through the generic replay contract."""
    return MeshSimulationResult(
        cycles=packet_mesh.cycles,
        traces=packet_mesh.mesh_traces,
        deliveries=(),
        link_transfers=packet_mesh.link_transfers,
        router_summaries=packet_mesh.router_summaries,
        endpoint_injected_flit_count=len(packet_mesh.deliveries),
        endpoint_input_stall_cycles=(0,) * 16,
    )


def build_exact_phase_models() -> tuple[ExactRouterPhase, ...]:
    contexts = build_activity_contexts()
    shared = simulate_context_service(
        contexts,
        event_candidate_cycles=range(3, 3 + len(contexts)),
        source_sram_request_ready=lambda cycle, endpoint: (
            ((cycle & 0x7) ^ (endpoint & 0x7)) != 0
        ),
        destination_sram_write_ready=lambda cycle, endpoint: (
            ((cycle + endpoint) & 0xF) != 0
        ),
        context_completion_ready=lambda cycle: (cycle & 0x1F) != 0,
        record_mesh_trace=True,
    )
    if (
        len(shared.contexts) != SHARED_CONTEXTS
        or len(shared.packet_mesh.descriptors) != SHARED_PACKETS
        or len(shared.packet_mesh.deliveries) != SHARED_FLITS
        or shared.cycles != SHARED_CYCLES
        or shared.write_fold != SHARED_WRITE_FOLD
    ):
        raise ValueError("VC0 shared-context service differs from its checked full-workload contract")

    phases = [
        ExactRouterPhase(
            name="shared_vc0_full_context_service",
            transport_class="shared_sram_context_vc0",
            mesh_result=_router_view(shared.packet_mesh),
            packet_count=SHARED_PACKETS,
            flit_count=SHARED_FLITS,
            context_count=SHARED_CONTEXTS,
            service_cycles=shared.cycles,
        )
    ]
    for group in range(REDUCTION_GROUPS):
        reduction = simulate_exact_stats_once_shared_root(
            epoch=group,
            vc=1,
            record_mesh_trace=True,
        )
        packet_count = len(reduction.mesh.descriptors)
        flit_count = len(reduction.mesh.deliveries)
        if packet_count != REDUCTION_SOURCES * PACKETS_PER_GROUP:
            raise ValueError(f"VC1 group {group} packet count differs from exact transport")
        if flit_count != REDUCTION_SOURCES * GROUP_FLITS:
            raise ValueError(f"VC1 group {group} flit count differs from exact transport")
        if reduction.slot_reuse_violations:
            raise ValueError(f"VC1 group {group} violates exact two-slot source storage")
        phases.append(
            ExactRouterPhase(
                name=f"reduction_vc1_group_{group}",
                transport_class="stats_once_exact_reduction_vc1",
                mesh_result=_router_view(reduction.mesh),
                packet_count=packet_count,
                flit_count=flit_count,
                context_count=REDUCTION_SOURCES,
                service_cycles=max(row.final_output_cycle for row in reduction.replays) + 1,
                group=group,
            )
        )
    return tuple(phases)


def _source_hashes(repo_root: Path) -> JsonDict:
    paths = (
        Path("npu/sim/perf/attention_shared_stream_context_service.py"),
        Path("npu/sim/perf/stats_once_shared_root.py"),
        Path("npu/sim/perf/noc_sram_packet_mesh.py"),
        Path("npu/sim/perf/noc_segmented_mesh.py"),
        Path("npu/sim/rtl/attention_shared_stream_context_service.sv"),
        Path("npu/sim/rtl/local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper.sv"),
        Path("npu/sim/rtl/local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv"),
        Path("npu/sim/rtl/noc_sram_packet_endpoint.sv"),
        Path("npu/sim/rtl/noc_segmented_mesh4x4.sv"),
        Path("npu/sim/rtl/noc_segmented_mesh_router.sv"),
        Path("npu/sim/rtl/noc_ready_valid_fifo.sv"),
    )
    return {path.as_posix(): _sha256_file(repo_root / path) for path in paths}


def build_manifest(
    *,
    repo_root: Path,
    node: int,
    out_dir: Path,
    timeout_seconds: int,
    clock_period_ns: float,
) -> JsonDict:
    if clock_period_ns <= 0.0:
        raise ValueError("activity clock period must be positive")
    phases = build_exact_phase_models()
    out_dir.mkdir(parents=True, exist_ok=True)
    phase_rows: list[JsonDict] = []
    for phase in phases:
        phase_dir = out_dir / phase.name
        rtl = run_rtl_activity(
            phase.mesh_result,
            node=node,
            clock_period_ns=clock_period_ns,
            out_dir=phase_dir,
            timeout_seconds=timeout_seconds,
        )
        if rtl.get("equivalence_status") != "pass":
            raise ValueError(f"router RTL replay did not pass for {phase.name}")
        phase_rows.append(
            {
                "phase": phase.name,
                "transport_class": phase.transport_class,
                "group": phase.group,
                "vcd": f"{phase.name}/{rtl['vcd']}",
                "vcd_sha256": rtl["vcd_sha256"],
                "sequential_register_activity": (
                    f"{phase.name}/{rtl['sequential_register_activity']}"
                ),
                "sequential_register_activity_sha256": rtl[
                    "sequential_register_activity_sha256"
                ],
                "measured_cycles": phase.mesh_result.cycles,
                "full_context_cycles": phase.mesh_result.cycles,
                "service_cycles": (
                    phase.mesh_result.cycles
                    if phase.service_cycles is None
                    else phase.service_cycles
                ),
                "packet_count": phase.packet_count,
                "flit_count": phase.flit_count,
                "context_count": phase.context_count,
                "requires_macro_activity": False,
                "rtl_equivalence": rtl,
            }
        )

    return {
        "version": 2,
        "model": "llama7b_score32_noc_exact_transport_router_rtl_activity_v2",
        "clock_period_ns": clock_period_ns,
        "node": node,
        "coordinates": {"x": node % 4, "y": node // 4},
        "source_contract": {
            "precision": "exact_score32_stats_once",
            "partial_link_bits_per_beat": 419,
            "partial_payload_bits_per_beat": 328,
            "release_contract": "group_major_actual_valid_ready",
            "shared_contexts": SHARED_CONTEXTS,
            "shared_packets": SHARED_PACKETS,
            "shared_flits": SHARED_FLITS,
            "reduction_groups": REDUCTION_GROUPS,
            "reduction_packets": REDUCTION_GROUPS * REDUCTION_SOURCES * PACKETS_PER_GROUP,
            "reduction_flits": REDUCTION_GROUPS * REDUCTION_SOURCES * GROUP_FLITS,
            "total_flits": SHARED_FLITS + REDUCTION_GROUPS * REDUCTION_SOURCES * GROUP_FLITS,
        },
        "source_hashes": _source_hashes(repo_root),
        "equivalence": {
            "status": "pass",
            "scope": "all cycle ready values, forwarded flit fields/data, and final router counters for every exact phase",
            "phase_count": len(phase_rows),
        },
        "phases": phase_rows,
        "remaining_abstractions": [
            "The five isolated phases preserve exact per-phase traffic but do not measure shared-mesh arbitration between simultaneously eligible VC0 and VC1 traffic.",
            "Bare-router annotation excludes aggregate links and mesh clock-tree power.",
            "HBM/DRAM control and PHY remain external by design.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--node", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--clock-period-ns", type=float, required=True)
    args = parser.parse_args()
    payload = build_manifest(
        repo_root=args.repo_root.resolve(),
        node=args.node,
        out_dir=args.out_dir.resolve(),
        timeout_seconds=args.timeout_seconds,
        clock_period_ns=args.clock_period_ns,
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
