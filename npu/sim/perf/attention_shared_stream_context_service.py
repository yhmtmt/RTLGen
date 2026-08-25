"""Cycle model for the complete shared-stream context service.

The service model composes context admission and endpoint ownership with the
descriptor-driven packet mesh.  Packet release times are solved to a fixed
point because a later context cannot acquire its source and destination until
the prior owners' final packets and context-completion handshakes retire.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from npu.sim.perf.noc_sram_packet_mesh import (
    ENDPOINTS,
    PacketDescriptor,
    PacketMeshResult,
    simulate_packet_mesh,
)


ReadyFunction = Callable[[int, int], bool]
CompletionReadyFunction = Callable[[int], bool]


@dataclass(frozen=True)
class ServiceContext:
    wave: int
    source: int
    destination: int
    source_base: int
    destination_base: int
    packet_count: int = 68


@dataclass(frozen=True)
class ContextHandshake:
    cycle: int
    context_index: int
    wave: int
    source: int
    destination: int


@dataclass(frozen=True)
class ContextServiceResult:
    cycles: int
    iterations: int
    contexts: tuple[ServiceContext, ...]
    admissions: tuple[ContextHandshake, ...]
    completions: tuple[ContextHandshake, ...]
    packet_mesh: PacketMeshResult
    write_fold: int


def build_activity_contexts() -> tuple[ServiceContext, ...]:
    """Return the canonical 112 contexts driven by the physical harness."""

    wave_shifts = ((0, 4), (1, 7), (2, 10), (3, 13), (5, 3), (6, 6), (7, 9))
    return tuple(
        ServiceContext(
            wave=wave,
            source=(destination + shift) % ENDPOINTS,
            destination=destination,
            source_base=0x0100_0000 + wave * 0x0010_0000 + destination * 0x0001_0000,
            destination_base=0x0200_0000 + wave * 0x0010_0000 + destination * 0x0001_0000,
        )
        for wave, shift in wave_shifts
        for destination in range(ENDPOINTS)
    )


def _packet_descriptors(
    contexts: tuple[ServiceContext, ...],
    admission_cycles: tuple[int, ...],
) -> tuple[tuple[PacketDescriptor, ...], tuple[int, ...]]:
    descriptors: list[PacketDescriptor] = []
    descriptor_contexts: list[int] = []
    for context_index, (context, admission_cycle) in enumerate(zip(contexts, admission_cycles)):
        for packet_index in range(context.packet_count):
            descriptors.append(
                PacketDescriptor(
                    source=context.source,
                    destination=context.destination,
                    vc=0,
                    tag=packet_index & 0xFF,
                    flit_count=8,
                    tx_base_addr=context.source_base + packet_index * 256,
                    rx_base_addr=context.destination_base + packet_index * 256,
                    release_cycle=admission_cycle + 1,
                    schedule_order=len(descriptors),
                    packet_id=f"context-{context_index}-packet-{packet_index}",
                )
            )
            descriptor_contexts.append(context_index)
    return tuple(descriptors), tuple(descriptor_contexts)


def _schedule_contexts(
    contexts: tuple[ServiceContext, ...],
    event_candidate_cycles: tuple[int, ...],
    final_packet_cycles: tuple[int, ...],
    completion_ready: CompletionReadyFunction,
    *,
    max_cycles: int,
) -> tuple[tuple[int, ...], tuple[ContextHandshake, ...]]:
    slots: list[int | None] = [None] * 16
    source_owner: list[int | None] = [None] * ENDPOINTS
    destination_owner: list[int | None] = [None] * ENDPOINTS
    admission_cycles = [-1] * len(contexts)
    completions: list[ContextHandshake] = []
    next_context = 0
    completion_hold_context: int | None = None

    for cycle in range(max_cycles):
        completion_slot = None
        completion_context = completion_hold_context
        if completion_context is not None:
            completion_slot = slots.index(completion_context)
        else:
            completion_slot = next(
                (
                    slot
                    for slot, context_index in enumerate(slots)
                    if context_index is not None
                    and final_packet_cycles[context_index] + 1 < cycle
                ),
                None,
            )
            completion_context = slots[completion_slot] if completion_slot is not None else None

        admission_slot = next((slot for slot, owner in enumerate(slots) if owner is None), None)
        admission_context = None
        if next_context < len(contexts) and admission_slot is not None:
            context = contexts[next_context]
            if (
                event_candidate_cycles[next_context] <= cycle
                and source_owner[context.source] is None
                and destination_owner[context.destination] is None
            ):
                admission_context = next_context

        if completion_context is not None and completion_ready(cycle):
            context = contexts[completion_context]
            completions.append(
                ContextHandshake(
                    cycle=cycle,
                    context_index=completion_context,
                    wave=context.wave,
                    source=context.source,
                    destination=context.destination,
                )
            )
            slots[completion_slot] = None
            source_owner[context.source] = None
            destination_owner[context.destination] = None
            completion_hold_context = None
        elif completion_context is not None:
            completion_hold_context = completion_context

        # Ready and the free-slot index are sampled before this edge, so a
        # context cannot consume resources released by the completion above.
        if admission_context is not None:
            context = contexts[admission_context]
            slots[admission_slot] = admission_context
            source_owner[context.source] = admission_context
            destination_owner[context.destination] = admission_context
            admission_cycles[admission_context] = cycle
            next_context += 1

        if len(completions) == len(contexts):
            return tuple(admission_cycles), tuple(completions)

    raise RuntimeError("context-service schedule did not complete")


def _response_word(endpoint: int, address: int, salt: int) -> int:
    endpoint_pattern = int(f"{endpoint:x}" * 8, 16)
    repeated = salt ^ (endpoint << 4)
    return (
        ((address ^ salt) & 0xFFFF_FFFF) << 224
        | sum((repeated & 0xFFFF_FFFF) << (96 + lane * 32) for lane in range(4))
        | (address & 0xFFFF_FFFF) << 64
        | (salt & 0xFFFF_FFFF) << 32
        | endpoint_pattern
    )


def _activity_write_fold(packet_mesh: PacketMeshResult) -> int:
    responses = {
        (request.packet_index, request.fragment): _response_word(
            request.endpoint,
            request.address,
            request.cycle,
        )
        for request in packet_mesh.source_memory_requests
    }
    fold = 0
    mask = (1 << 128) - 1
    for write in packet_mesh.destination_memory_writes:
        word = responses[write.packet_index, write.fragment]
        fold ^= (word & mask) ^ (word >> 128) ^ write.address
    return fold


def simulate_context_service(
    contexts: Iterable[ServiceContext],
    *,
    event_candidate_cycles: Iterable[int],
    source_sram_request_ready: ReadyFunction,
    destination_sram_write_ready: ReadyFunction,
    context_completion_ready: CompletionReadyFunction,
    source_outstanding: int = 1,
    max_iterations: int = 32,
    max_cycles: int = 250_000,
) -> ContextServiceResult:
    """Solve and replay a complete context-service workload."""

    context_rows = tuple(contexts)
    event_cycles = tuple(int(cycle) for cycle in event_candidate_cycles)
    if len(event_cycles) != len(context_rows):
        raise ValueError("event_candidate_cycles must have one entry per context")
    if any(next_cycle < cycle for cycle, next_cycle in zip(event_cycles, event_cycles[1:])):
        raise ValueError("event_candidate_cycles must preserve producer order")
    if source_outstanding < 1:
        raise ValueError("source_outstanding must be positive")
    if not context_rows:
        raise ValueError("at least one context is required")

    admission_cycles = event_cycles
    final_packet_cycles = tuple(0 for _ in context_rows)
    completion_handshakes: tuple[ContextHandshake, ...] = ()
    packet_mesh: PacketMeshResult | None = None

    for iteration in range(1, max_iterations + 1):
        descriptors, descriptor_contexts = _packet_descriptors(context_rows, admission_cycles)
        packet_mesh = simulate_packet_mesh(
            descriptors,
            descriptor_scheduler="endpoint_parallel",
            tx_outstanding_limits={endpoint: source_outstanding for endpoint in range(ENDPOINTS)},
            source_sram_request_ready_schedule=source_sram_request_ready,
            destination_sram_ready_schedule=destination_sram_write_ready,
            max_cycles=max_cycles,
        )
        final = [0] * len(context_rows)
        for completion in packet_mesh.completions:
            context_index = descriptor_contexts[completion.packet_index]
            final[context_index] = max(final[context_index], completion.cycle)
        final_packet_cycles = tuple(final)
        next_admissions, next_completions = _schedule_contexts(
            context_rows,
            event_cycles,
            final_packet_cycles,
            context_completion_ready,
            max_cycles=max_cycles,
        )
        completion_handshakes = next_completions
        if next_admissions == admission_cycles:
            admissions = tuple(
                ContextHandshake(
                    cycle=cycle,
                    context_index=index,
                    wave=context.wave,
                    source=context.source,
                    destination=context.destination,
                )
                for index, (context, cycle) in enumerate(zip(context_rows, admission_cycles))
            )
            return ContextServiceResult(
                cycles=completion_handshakes[-1].cycle,
                iterations=iteration,
                contexts=context_rows,
                admissions=admissions,
                completions=completion_handshakes,
                packet_mesh=packet_mesh,
                write_fold=_activity_write_fold(packet_mesh),
            )
        admission_cycles = next_admissions

    raise RuntimeError("context-service fixed point did not converge")
