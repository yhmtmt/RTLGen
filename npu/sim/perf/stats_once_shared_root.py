"""Finite shared-root transport model for exact stats-once reduction groups.

Fifteen remote clusters send one 167-flit group each to root endpoint 15.
The model uses the cycle-accurate registered-credit mesh and descriptor-driven
endpoint model.  It also schedules the two destination packet slots per source
through a conservative synchronous-SRAM replay timeline.

The mesh result is a NoC/control lower bound: downstream exact decoders and the
global reduction tree may add backpressure.  Those consumers must be compared
against this trace rather than hidden in an aggregate bandwidth assumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from npu.sim.perf.noc_sram_packet_mesh import (
    FLIT_BYTES,
    PacketDescriptor,
    PacketMeshResult,
    simulate_packet_mesh,
)

REMOTE_SOURCES = 15
ROOT_ENDPOINT = 15
PACKETS_PER_GROUP = 21
GROUP_FLITS = 167
FULL_PACKET_FLITS = 8
FINAL_PACKET_FLITS = 7
PACKET_SLOT_BYTES = FULL_PACKET_FLITS * FLIT_BYTES
SLOTS_PER_SOURCE = 2
SOURCE_SLOT_STRIDE_BYTES = SLOTS_PER_SOURCE * PACKET_SLOT_BYTES
PACKET_ROUND_RELEASE_INTERVAL_CYCLES = REMOTE_SOURCES * FULL_PACKET_FLITS


@dataclass(frozen=True)
class PacketReplay:
    source: int
    packet: int
    slot: int
    descriptor_cycle: int
    completion_cycle: int
    first_output_cycle: int
    final_output_cycle: int


@dataclass(frozen=True)
class SharedRootResult:
    mesh: PacketMeshResult
    replays: tuple[PacketReplay, ...]
    root_delivery_span_cycles: int
    serialization_lower_bound_cycles: int
    max_slots_per_source: int
    slot_reuse_violations: tuple[tuple[int, int, int], ...]
    packet_round_release_interval_cycles: int


def packet_flit_count(packet: int) -> int:
    if not 0 <= packet < PACKETS_PER_GROUP:
        raise ValueError("packet must be in [0, 20]")
    return FINAL_PACKET_FLITS if packet == PACKETS_PER_GROUP - 1 else FULL_PACKET_FLITS


def build_shared_root_descriptors(
    *,
    epoch: int = 0,
    vc: int = 1,
    release_cycles: Mapping[tuple[int, int], int] | None = None,
) -> tuple[PacketDescriptor, ...]:
    if not 0 <= epoch < 8:
        raise ValueError("epoch must be a 3-bit value")
    if not 0 <= vc < 4:
        raise ValueError("vc must be in [0, 3]")

    releases = dict(release_cycles or {})
    if any(cycle < 0 for cycle in releases.values()):
        raise ValueError("release cycles must be non-negative")
    descriptors = []
    schedule_order = 0
    # Packet-major order installs at most one live context per source and lets
    # all sources contend fairly for the single root ejection port.
    for packet in range(PACKETS_PER_GROUP):
        slot = packet % SLOTS_PER_SOURCE
        for source in range(REMOTE_SOURCES):
            descriptors.append(
                PacketDescriptor(
                    source=source,
                    destination=ROOT_ENDPOINT,
                    vc=vc,
                    tag=(epoch << 5) | packet,
                    flit_count=packet_flit_count(packet),
                    tx_base_addr=slot * PACKET_SLOT_BYTES,
                    rx_base_addr=(source * SOURCE_SLOT_STRIDE_BYTES)
                    + (slot * PACKET_SLOT_BYTES),
                    release_cycle=int(releases.get((source, packet), 0)),
                    schedule_order=schedule_order,
                    data_seed=(source << 8) | packet,
                    packet_id=f"source-{source}-packet-{packet}",
                )
            )
            schedule_order += 1
    return tuple(descriptors)


def _schedule_replays(
    mesh: PacketMeshResult,
    descriptors: tuple[PacketDescriptor, ...],
) -> tuple[tuple[PacketReplay, ...], int, tuple[tuple[int, int, int], ...]]:
    descriptor_cycles = {
        event.packet_index: event.cycle for event in mesh.rx_descriptor_handshakes
    }
    completion_cycles = {event.packet_index: event.cycle for event in mesh.completions}
    replays = []
    previous_final = [-1] * REMOTE_SOURCES
    intervals: list[list[list[tuple[int, int, int]]]] = [
        [[] for _ in range(SLOTS_PER_SOURCE)] for _ in range(REMOTE_SOURCES)
    ]

    for index, descriptor in enumerate(descriptors):
        packet = int(descriptor.tag & 0x1F)
        source = descriptor.source
        slot = packet % SLOTS_PER_SOURCE
        completion = completion_cycles[index]
        # Completion is registered after the final write. The adapter then
        # selects the ordered packet and performs a synchronous SRAM read.
        first_output = max(completion + 4, previous_final[source] + 1)
        final_output = first_output + descriptor.flit_count - 1
        previous_final[source] = final_output
        replay = PacketReplay(
            source=source,
            packet=packet,
            slot=slot,
            descriptor_cycle=descriptor_cycles[index],
            completion_cycle=completion,
            first_output_cycle=first_output,
            final_output_cycle=final_output,
        )
        replays.append(replay)
        intervals[source][slot].append(
            (replay.descriptor_cycle, replay.final_output_cycle, packet)
        )

    violations = []
    max_slots = 0
    for source in range(REMOTE_SOURCES):
        events = []
        for slot in range(SLOTS_PER_SOURCE):
            ordered = sorted(intervals[source][slot])
            for previous, current in zip(ordered, ordered[1:]):
                if current[0] <= previous[1]:
                    violations.append((source, previous[2], current[2]))
            for start, end, _packet in ordered:
                events.append((start, 1))
                events.append((end + 1, -1))
        occupancy = 0
        for _cycle, delta in sorted(events, key=lambda item: (item[0], item[1])):
            occupancy += delta
            max_slots = max(max_slots, occupancy)
    return tuple(replays), max_slots, tuple(violations)


def simulate_exact_stats_once_shared_root(
    *,
    epoch: int = 0,
    vc: int = 1,
    record_mesh_trace: bool = False,
) -> SharedRootResult:
    release_cycles = {
        (source, packet): packet * PACKET_ROUND_RELEASE_INTERVAL_CYCLES
        for packet in range(PACKETS_PER_GROUP)
        for source in range(REMOTE_SOURCES)
    }
    descriptors = build_shared_root_descriptors(
        epoch=epoch,
        vc=vc,
        release_cycles=release_cycles,
    )
    mesh = simulate_packet_mesh(
        descriptors,
        rx_context_limits={ROOT_ENDPOINT: REMOTE_SOURCES},
        descriptor_scheduler="endpoint_parallel",
        record_mesh_trace=record_mesh_trace,
    )
    replays, max_slots, violations = _schedule_replays(mesh, descriptors)

    root_cycles = [delivery.cycle for delivery in mesh.deliveries]
    span = max(root_cycles) - min(root_cycles) + 1
    return SharedRootResult(
        mesh=mesh,
        replays=replays,
        root_delivery_span_cycles=span,
        serialization_lower_bound_cycles=REMOTE_SOURCES * GROUP_FLITS,
        max_slots_per_source=max_slots,
        slot_reuse_violations=violations,
        packet_round_release_interval_cycles=
        PACKET_ROUND_RELEASE_INTERVAL_CYCLES,
    )


__all__ = [
    "GROUP_FLITS",
    "PACKETS_PER_GROUP",
    "PACKET_ROUND_RELEASE_INTERVAL_CYCLES",
    "REMOTE_SOURCES",
    "ROOT_ENDPOINT",
    "SharedRootResult",
    "build_shared_root_descriptors",
    "packet_flit_count",
    "simulate_exact_stats_once_shared_root",
]
