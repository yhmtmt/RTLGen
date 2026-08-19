"""Physical-bank replay model for the exact stats-once shared root.

The logical endpoint owns two packet slots per remote source.  This model maps
those slots onto a selectable number of single-port physical SRAM banks and
feeds delayed slot retirement back into packet release before re-running the
registered-credit mesh.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

from npu.sim.perf.noc_sram_packet_mesh import PacketDescriptor, PacketMeshResult, simulate_packet_mesh
from npu.sim.perf.stats_once_shared_root import (
    GROUP_FLITS,
    PACKET_ROUND_RELEASE_INTERVAL_CYCLES,
    PACKETS_PER_GROUP,
    REMOTE_SOURCES,
    ROOT_ENDPOINT,
    build_shared_root_descriptors,
    packet_flit_count,
)

MACRO_DEPTH = 64
MACRO_WIDTH = 32
PACKET_WORDS = 8
WORDS_PER_SOURCE = 16
ROOT_WORD_WIDTH = 256


@dataclass(frozen=True)
class BankedPacketReplay:
    source: int
    packet: int
    bank: int
    first_output_cycle: int
    final_output_cycle: int


@dataclass(frozen=True)
class BankedRootResult:
    physical_banks: int
    macro_count: int
    mesh: PacketMeshResult
    replays: tuple[BankedPacketReplay, ...]
    release_cycles: tuple[tuple[int, ...], ...]
    root_delivery_span_cycles: int
    final_replay_cycle: int
    replay_drain_cycles: int
    max_slots_per_source: int
    iteration_count: int


def packet_sram_macro_count(physical_banks: int) -> int:
    if not 1 <= physical_banks <= REMOTE_SOURCES:
        raise ValueError("physical_banks must be in [1, 15]")
    sources_per_bank = (REMOTE_SOURCES + physical_banks - 1) // physical_banks
    depth = sources_per_bank * WORDS_PER_SOURCE
    depth_macros = (depth + MACRO_DEPTH - 1) // MACRO_DEPTH
    width_macros = ROOT_WORD_WIDTH // MACRO_WIDTH
    return physical_banks * depth_macros * width_macros


def _schedule_banked_replays(
    mesh: PacketMeshResult,
    descriptors: tuple[PacketDescriptor, ...],
    *,
    physical_banks: int,
) -> tuple[tuple[BankedPacketReplay, ...], int]:
    completion_cycle = {event.packet_index: event.cycle for event in mesh.completions}
    writes_by_cycle_bank: set[tuple[int, int]] = set()
    for write in mesh.destination_memory_writes:
        descriptor = descriptors[write.packet_index]
        writes_by_cycle_bank.add((write.cycle, descriptor.source % physical_banks))

    next_packet = [0] * REMOTE_SOURCES
    active_packet: list[int | None] = [None] * REMOTE_SOURCES
    issued_words = [0] * REMOTE_SOURCES
    first_output: dict[tuple[int, int], int] = {}
    final_output: dict[tuple[int, int], int] = {}
    responses: dict[int, list[tuple[int, int]]] = defaultdict(list)
    round_robin = [0] * physical_banks
    completed_packets = 0
    cycle = min(completion_cycle.values())
    max_cycle = mesh.cycles + REMOTE_SOURCES * PACKETS_PER_GROUP * PACKET_WORDS * 4

    while completed_packets < REMOTE_SOURCES * PACKETS_PER_GROUP:
        if cycle > max_cycle:
            raise RuntimeError("banked replay scheduling did not converge")

        for source, packet in responses.pop(cycle, []):
            first_output.setdefault((source, packet), cycle)
            if issued_words[source] == packet_flit_count(packet):
                final_output[(source, packet)] = cycle
                completed_packets += 1
                next_packet[source] += 1
                active_packet[source] = None
                issued_words[source] = 0

        for source in range(REMOTE_SOURCES):
            packet = next_packet[source]
            if packet >= PACKETS_PER_GROUP or active_packet[source] is not None:
                continue
            index = packet * REMOTE_SOURCES + source
            if completion_cycle[index] <= cycle:
                active_packet[source] = packet

        for bank in range(physical_banks):
            if (cycle, bank) in writes_by_cycle_bank:
                continue
            candidates = [
                source
                for source in range(REMOTE_SOURCES)
                if source % physical_banks == bank
                and active_packet[source] is not None
                and issued_words[source] < packet_flit_count(active_packet[source])
            ]
            if not candidates:
                continue
            start = round_robin[bank]
            source = min(candidates, key=lambda value: (value - start) % REMOTE_SOURCES)
            packet = active_packet[source]
            assert packet is not None
            issued_words[source] += 1
            responses[cycle + 1].append((source, packet))
            round_robin[bank] = (source + 1) % REMOTE_SOURCES
        cycle += 1

    replays = tuple(
        BankedPacketReplay(
            source=source,
            packet=packet,
            bank=source % physical_banks,
            first_output_cycle=first_output[(source, packet)],
            final_output_cycle=final_output[(source, packet)],
        )
        for packet in range(PACKETS_PER_GROUP)
        for source in range(REMOTE_SOURCES)
    )
    return replays, max(final_output.values())


def _max_slot_occupancy(
    mesh: PacketMeshResult,
    replays: tuple[BankedPacketReplay, ...],
) -> int:
    descriptor_cycles = {
        event.packet_index: event.cycle for event in mesh.rx_descriptor_handshakes
    }
    events: list[list[tuple[int, int]]] = [[] for _ in range(REMOTE_SOURCES)]
    for replay in replays:
        index = replay.packet * REMOTE_SOURCES + replay.source
        events[replay.source].append((descriptor_cycles[index], 1))
        events[replay.source].append((replay.final_output_cycle + 1, -1))
    maximum = 0
    for source_events in events:
        occupancy = 0
        for _cycle, delta in sorted(source_events, key=lambda item: (item[0], item[1])):
            occupancy += delta
            maximum = max(maximum, occupancy)
    return maximum


@lru_cache(maxsize=None)
def simulate_banked_stats_once_shared_root(
    *,
    physical_banks: int,
    max_iterations: int = 32,
) -> BankedRootResult:
    packet_sram_macro_count(physical_banks)
    if physical_banks == 1:
        raise ValueError(
            "one physical bank is dominated by four banks: both require 32 "
            "64x32 macros, while one single-port bank serializes every write "
            "and replay read"
        )
    releases = [
        [packet * PACKET_ROUND_RELEASE_INTERVAL_CYCLES for packet in range(PACKETS_PER_GROUP)]
        for _source in range(REMOTE_SOURCES)
    ]

    for iteration in range(1, max_iterations + 1):
        release_map = {
            (source, packet): releases[source][packet]
            for source in range(REMOTE_SOURCES)
            for packet in range(PACKETS_PER_GROUP)
        }
        descriptors = build_shared_root_descriptors(release_cycles=release_map)
        mesh = simulate_packet_mesh(
            descriptors,
            rx_context_limits={ROOT_ENDPOINT: REMOTE_SOURCES},
            descriptor_scheduler="endpoint_parallel",
        )
        replays, final_replay = _schedule_banked_replays(
            mesh,
            descriptors,
            physical_banks=physical_banks,
        )
        replay_by_key = {(row.source, row.packet): row for row in replays}
        updated = [row[:] for row in releases]
        for source in range(REMOTE_SOURCES):
            for packet in range(2, PACKETS_PER_GROUP):
                slot_predecessor = replay_by_key[(source, packet - 2)]
                updated[source][packet] = max(
                    packet * PACKET_ROUND_RELEASE_INTERVAL_CYCLES,
                    slot_predecessor.final_output_cycle + 2,
                )
        if updated == releases:
            root_cycles = [delivery.cycle for delivery in mesh.deliveries]
            root_last = max(root_cycles)
            return BankedRootResult(
                physical_banks=physical_banks,
                macro_count=packet_sram_macro_count(physical_banks),
                mesh=mesh,
                replays=replays,
                release_cycles=tuple(tuple(row) for row in releases),
                root_delivery_span_cycles=root_last - min(root_cycles) + 1,
                final_replay_cycle=final_replay,
                replay_drain_cycles=final_replay - root_last,
                max_slots_per_source=_max_slot_occupancy(mesh, replays),
                iteration_count=iteration,
            )
        releases = updated
    raise RuntimeError("banked shared-root release schedule did not converge")


__all__ = [
    "BankedRootResult",
    "packet_sram_macro_count",
    "simulate_banked_stats_once_shared_root",
]
