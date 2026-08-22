#!/usr/bin/env python3
"""Exact reference model for the Phase-2 shared-SRAM stream transport.

The model is deliberately limited to the byte-preserving shared stream.  The
historical Phase-2 reduction traffic is a different VC and is not represented
here.  Addresses are logical byte addresses in two disjoint SRAM spaces:
source space first, destination space second.  The separation makes address
coverage checks unambiguous while preserving the endpoint-local layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, MutableMapping, Sequence


MESH_ENDPOINTS = 16
LOGICAL_WAVES = 8
LOCAL_ONLY_WAVE = 4
REMOTE_WAVES = tuple(wave for wave in range(LOGICAL_WAVES) if wave != LOCAL_ONLY_WAVE)
MAPPING_SHIFTS = (4, 7, 10, 13, 0, 3, 6, 9)

CONTEXT_COUNT = len(REMOTE_WAVES) * MESH_ENDPOINTS
CONTEXT_BYTES = 17_408
PACKETS_PER_CONTEXT = 68
PACKET_BYTES = 256
FLITS_PER_PACKET = 8
FLIT_BYTES = 32
SHARED_VC = 0
MAX_IN_FLIGHT_PACKET_CONTEXTS = 8

assert CONTEXT_BYTES == PACKETS_PER_CONTEXT * PACKET_BYTES
assert PACKET_BYTES == FLITS_PER_PACKET * FLIT_BYTES

CONTEXTS_PER_ENDPOINT = len(REMOTE_WAVES)
ENDPOINT_WINDOW_BYTES = CONTEXTS_PER_ENDPOINT * CONTEXT_BYTES
SOURCE_SPACE_BASE = 0
DESTINATION_SPACE_BASE = MESH_ENDPOINTS * ENDPOINT_WINDOW_BYTES
TOTAL_SHARED_BYTES = CONTEXT_COUNT * CONTEXT_BYTES
TOTAL_PACKETS = CONTEXT_COUNT * PACKETS_PER_CONTEXT
TOTAL_FLITS = TOTAL_PACKETS * FLITS_PER_PACKET


class TransportContractError(ValueError):
    """Raised when a transport invariant or equivalence check fails."""


@dataclass(frozen=True)
class SharedStreamContext:
    """One remote wave-to-destination transfer context."""

    context_id: int
    wave_index: int
    wave_ordinal: int
    source_endpoint: int
    destination_endpoint: int
    source_base: int
    destination_base: int
    packets_per_context: int = PACKETS_PER_CONTEXT
    payload_bytes: int | None = None
    flits_per_packet: int = FLITS_PER_PACKET
    vc: int = SHARED_VC

    def __post_init__(self) -> None:
        if self.packets_per_context <= 0:
            raise TransportContractError("packets_per_context must be positive")
        expected_bytes = self.packets_per_context * PACKET_BYTES
        if self.payload_bytes is None:
            object.__setattr__(self, "payload_bytes", expected_bytes)
        elif self.payload_bytes != expected_bytes:
            raise TransportContractError(
                "payload_bytes must equal packets_per_context * packet payload bytes"
            )

    @property
    def packet_count(self) -> int:
        """Compatibility spelling for the packet count in older callers."""

        return self.packets_per_context


@dataclass(frozen=True)
class PacketDescriptor:
    """A complete packet descriptor before its eight flits are emitted."""

    context_id: int
    wave_index: int
    source_endpoint: int
    destination_endpoint: int
    packet_index: int
    tag: int
    source_base: int
    destination_base: int
    payload_bytes: int = PACKET_BYTES
    flit_count: int = FLITS_PER_PACKET
    vc: int = SHARED_VC

    @property
    def source_packet_base(self) -> int:
        return self.source_base + self.packet_index * PACKET_BYTES

    @property
    def destination_packet_base(self) -> int:
        return self.destination_base + self.packet_index * PACKET_BYTES


@dataclass(frozen=True)
class MemoryWrite:
    """One accepted destination SRAM flit write."""

    context_id: int
    wave_index: int
    source_endpoint: int
    destination_endpoint: int
    packet_index: int
    flit_index: int
    source_address: int
    destination_address: int
    data: bytes
    vc: int = SHARED_VC
    tag: int = 0


@dataclass(frozen=True)
class PayloadEquivalenceResult:
    """Byte-level evidence; no hash is used to establish equivalence."""

    context_id: int
    byte_count: int
    write_count: int
    unique_address_count: int
    packet_count: int
    flit_count: int


@dataclass(frozen=True)
class ContextStatus:
    context_id: int
    admitted: bool
    completed_packet_count: int
    completion_valid: bool
    completion_accepted: bool
    source_owned: bool
    destination_owned: bool
    inflight_packet_count: int = 0
    next_packet_to_expose: int = 0
    next_packet_to_complete: int = 0


def _check_endpoint(endpoint: int) -> int:
    endpoint = int(endpoint)
    if not 0 <= endpoint < MESH_ENDPOINTS:
        raise TransportContractError(f"endpoint must be in [0, 15], got {endpoint}")
    return endpoint


def _check_packets_per_context(packets_per_context: int) -> int:
    packets_per_context = int(packets_per_context)
    if packets_per_context <= 0:
        raise TransportContractError("packets_per_context must be positive")
    return packets_per_context


def _check_remote_wave(wave_index: int) -> int:
    wave_index = int(wave_index)
    if not 0 <= wave_index < LOGICAL_WAVES:
        raise TransportContractError(f"wave index must be in [0, 7], got {wave_index}")
    if wave_index == LOCAL_ONLY_WAVE:
        raise TransportContractError("local-only wave 4 must not be admitted to shared transport")
    return wave_index


def wave_ordinal(wave_index: int) -> int:
    """Return the compact source/destination SRAM slot for a remote wave."""

    wave_index = _check_remote_wave(wave_index)
    return REMOTE_WAVES.index(wave_index)


def mapping_shift(wave_index: int) -> int:
    """Return the checked-in source-home rotation for a logical wave."""

    wave_index = int(wave_index)
    if not 0 <= wave_index < LOGICAL_WAVES:
        raise TransportContractError(f"wave index must be in [0, 7], got {wave_index}")
    return MAPPING_SHIFTS[wave_index]


def source_endpoint_for(*, wave_index: int, destination_endpoint: int) -> int:
    """Map a destination cluster to its source SRAM home."""

    destination_endpoint = _check_endpoint(destination_endpoint)
    return (destination_endpoint + mapping_shift(wave_index)) % MESH_ENDPOINTS


def endpoint_window_bytes(*, packets_per_context: int = PACKETS_PER_CONTEXT) -> int:
    """Return the per-endpoint SRAM window span for a packetized context."""

    return CONTEXTS_PER_ENDPOINT * _check_packets_per_context(packets_per_context) * PACKET_BYTES


def destination_space_base_for(*, packets_per_context: int = PACKETS_PER_CONTEXT) -> int:
    """Return the first byte of the disjoint destination address space."""

    return MESH_ENDPOINTS * endpoint_window_bytes(packets_per_context=packets_per_context)


def source_base_for(
    *, endpoint: int, wave_index: int, packets_per_context: int = PACKETS_PER_CONTEXT
) -> int:
    """Address formula for a source endpoint's remote-wave window."""

    endpoint = _check_endpoint(endpoint)
    packets_per_context = _check_packets_per_context(packets_per_context)
    window_bytes = packets_per_context * PACKET_BYTES
    return (
        SOURCE_SPACE_BASE
        + endpoint * endpoint_window_bytes(packets_per_context=packets_per_context)
        + wave_ordinal(wave_index) * window_bytes
    )


def destination_base_for(
    *, endpoint: int, wave_index: int, packets_per_context: int = PACKETS_PER_CONTEXT
) -> int:
    """Address formula for a destination endpoint's remote-wave window."""

    endpoint = _check_endpoint(endpoint)
    packets_per_context = _check_packets_per_context(packets_per_context)
    window_bytes = packets_per_context * PACKET_BYTES
    return (
        destination_space_base_for(packets_per_context=packets_per_context)
        + endpoint * endpoint_window_bytes(packets_per_context=packets_per_context)
        + wave_ordinal(wave_index) * window_bytes
    )


def context_id_for(*, wave_index: int, destination_endpoint: int) -> int:
    """Use the stable wave-major endpoint identity, leaving wave 4 unused."""

    wave_index = _check_remote_wave(wave_index)
    destination_endpoint = _check_endpoint(destination_endpoint)
    return wave_index * MESH_ENDPOINTS + destination_endpoint


def build_context(
    *, wave_index: int, destination_endpoint: int, packets_per_context: int = PACKETS_PER_CONTEXT
) -> SharedStreamContext:
    """Build one exact remote context from the contract mapping."""

    wave_index = _check_remote_wave(wave_index)
    packets_per_context = _check_packets_per_context(packets_per_context)
    destination_endpoint = _check_endpoint(destination_endpoint)
    source_endpoint = source_endpoint_for(
        wave_index=wave_index,
        destination_endpoint=destination_endpoint,
    )
    return SharedStreamContext(
        context_id=context_id_for(wave_index=wave_index, destination_endpoint=destination_endpoint),
        wave_index=wave_index,
        wave_ordinal=wave_ordinal(wave_index),
        source_endpoint=source_endpoint,
        destination_endpoint=destination_endpoint,
        source_base=source_base_for(
            endpoint=source_endpoint,
            wave_index=wave_index,
            packets_per_context=packets_per_context,
        ),
        destination_base=destination_base_for(
            endpoint=destination_endpoint,
            wave_index=wave_index,
            packets_per_context=packets_per_context,
        ),
        packets_per_context=packets_per_context,
    )


def build_contexts(
    *, packets_per_context: int = PACKETS_PER_CONTEXT
) -> tuple[SharedStreamContext, ...]:
    """Return all contexts in deterministic wave-major order."""

    return tuple(
        build_context(
            wave_index=wave,
            destination_endpoint=destination,
            packets_per_context=packets_per_context,
        )
        for wave in REMOTE_WAVES
        for destination in range(MESH_ENDPOINTS)
    )


def packet_descriptors(context: SharedStreamContext) -> tuple[PacketDescriptor, ...]:
    """Return ordered packet descriptors for one context."""

    if context.payload_bytes != context.packet_count * PACKET_BYTES:
        raise TransportContractError("context payload does not match its packet count")
    if context.flits_per_packet != FLITS_PER_PACKET:
        raise TransportContractError("shared context flit count must be exactly 8")
    return tuple(
        PacketDescriptor(
            context_id=context.context_id,
            wave_index=context.wave_index,
            source_endpoint=context.source_endpoint,
            destination_endpoint=context.destination_endpoint,
            packet_index=packet_index,
            tag=packet_index % 256,
            source_base=context.source_base,
            destination_base=context.destination_base,
        )
        for packet_index in range(context.packet_count)
    )


def _coerce_window(
    source_window: bytes | bytearray | memoryview,
    *,
    expected_bytes: int,
) -> bytes:
    payload = bytes(source_window)
    if len(payload) != expected_bytes:
        raise TransportContractError(
            f"source window must contain exactly {expected_bytes} bytes, got {len(payload)}"
        )
    return payload


def canonical_memory_writes(
    context: SharedStreamContext,
    source_window: bytes | bytearray | memoryview,
) -> tuple[MemoryWrite, ...]:
    """Create the exact ordered writes expected at the destination SRAM."""

    payload = _coerce_window(source_window, expected_bytes=context.payload_bytes)
    writes: list[MemoryWrite] = []
    for descriptor in packet_descriptors(context):
        for flit_index in range(FLITS_PER_PACKET):
            offset = descriptor.packet_index * PACKET_BYTES + flit_index * FLIT_BYTES
            writes.append(
                MemoryWrite(
                    context_id=context.context_id,
                    wave_index=context.wave_index,
                    source_endpoint=context.source_endpoint,
                    destination_endpoint=context.destination_endpoint,
                    packet_index=descriptor.packet_index,
                    flit_index=flit_index,
                    source_address=context.source_base + offset,
                    destination_address=context.destination_base + offset,
                    data=payload[offset : offset + FLIT_BYTES],
                    tag=descriptor.tag,
                )
            )
    return tuple(writes)


def validate_payload_equivalence(
    context: SharedStreamContext,
    source_window: bytes | bytearray | memoryview,
    writes: Sequence[MemoryWrite] | Iterable[MemoryWrite],
) -> PayloadEquivalenceResult:
    """Prove exact byte/address equivalence for one complete context.

    The check is intentionally independent of any digest.  It validates the
    ordered packet/flit identity, both address formulas, every byte payload,
    and uniqueness of every destination byte address.
    """

    payload = _coerce_window(source_window, expected_bytes=context.payload_bytes)
    observed = tuple(writes)
    expected_count = context.packet_count * FLITS_PER_PACKET
    if len(observed) != expected_count:
        raise TransportContractError(
            f"context {context.context_id} requires {expected_count} flit writes, got {len(observed)}"
        )

    destination_addresses: set[int] = set()
    source_addresses: set[int] = set()
    for ordinal, write in enumerate(observed):
        packet_index, flit_index = divmod(ordinal, FLITS_PER_PACKET)
        offset = packet_index * PACKET_BYTES + flit_index * FLIT_BYTES
        expected_source_address = context.source_base + offset
        expected_destination_address = context.destination_base + offset
        expected_data = payload[offset : offset + FLIT_BYTES]
        expected = {
            "context_id": context.context_id,
            "wave_index": context.wave_index,
            "source_endpoint": context.source_endpoint,
            "destination_endpoint": context.destination_endpoint,
            "packet_index": packet_index,
            "flit_index": flit_index,
            "source_address": expected_source_address,
            "destination_address": expected_destination_address,
            "vc": SHARED_VC,
            "tag": packet_index % 256,
        }
        for field, value in expected.items():
            if getattr(write, field) != value:
                raise TransportContractError(
                    f"context {context.context_id} write {ordinal} has {field}={getattr(write, field)!r}; "
                    f"expected {value!r}"
                )
        if bytes(write.data) != expected_data:
            raise TransportContractError(f"context {context.context_id} write {ordinal} payload mismatch")
        if len(write.data) != FLIT_BYTES:
            raise TransportContractError(f"context {context.context_id} write {ordinal} is not one flit")
        if expected_source_address in source_addresses:
            raise TransportContractError(f"duplicate source byte address at {expected_source_address}")
        if expected_destination_address in destination_addresses:
            raise TransportContractError(
                f"duplicate destination byte address at {expected_destination_address}"
            )
        source_addresses.update(range(expected_source_address, expected_source_address + FLIT_BYTES))
        destination_addresses.update(
            range(expected_destination_address, expected_destination_address + FLIT_BYTES)
        )

    expected_bytes = context.payload_bytes
    if len(source_addresses) != expected_bytes or len(destination_addresses) != expected_bytes:
        raise TransportContractError("payload write coverage is not exactly one complete context window")
    return PayloadEquivalenceResult(
        context_id=context.context_id,
        byte_count=expected_bytes,
        write_count=len(observed),
        unique_address_count=len(destination_addresses),
        packet_count=context.packet_count,
        flit_count=context.packet_count * FLITS_PER_PACKET,
    )


def copy_payload_and_validate(
    context: SharedStreamContext,
    source_window: bytes | bytearray | memoryview,
    destination_memory: MutableMapping[int, int],
    writes: Sequence[MemoryWrite] | Iterable[MemoryWrite] | None = None,
) -> PayloadEquivalenceResult:
    """Validate first, then copy every accepted flit into destination SRAM.

    The destination window must be unused before the copy.  Consequently an
    attempted overwrite is reported instead of silently replacing a byte.
    Invalid transfers never mutate ``destination_memory``.
    """

    payload = _coerce_window(source_window, expected_bytes=context.payload_bytes)
    observed = tuple(canonical_memory_writes(context, payload) if writes is None else writes)
    result = validate_payload_equivalence(context, payload, observed)
    destination_range = range(context.destination_base, context.destination_base + context.payload_bytes)
    if any(address in destination_memory for address in destination_range):
        raise TransportContractError(f"destination window for context {context.context_id} is already occupied")
    for write in observed:
        for offset, value in enumerate(write.data):
            destination_memory[write.destination_address + offset] = int(value)
    return result


def packet_tag(packet_index: int) -> int:
    """Return the wire tag; packet indices may exceed the eight-bit tag space."""

    packet_index = int(packet_index)
    if packet_index < 0:
        raise TransportContractError("packet index must be non-negative")
    return packet_index % 256


class PacketTagLifetimeTracker:
    """Track bounded packet exposure and ordered completion for one context."""

    def __init__(self, packet_count: int, *, max_in_flight: int = MAX_IN_FLIGHT_PACKET_CONTEXTS) -> None:
        self.packet_count = _check_packets_per_context(packet_count)
        self.max_in_flight = int(max_in_flight)
        if self.max_in_flight <= 0:
            raise TransportContractError("max_in_flight must be positive")
        self.next_packet_to_expose = 0
        self.next_packet_to_complete = 0
        self._inflight_by_tag: dict[int, int] = {}

    @property
    def inflight_packet_count(self) -> int:
        return len(self._inflight_by_tag)

    def expose(self, packet_index: int) -> int:
        packet_index = int(packet_index)
        if packet_index != self.next_packet_to_expose:
            raise TransportContractError(
                f"packet exposure must be ordered: expected {self.next_packet_to_expose}, got {packet_index}"
            )
        if packet_index >= self.packet_count:
            raise TransportContractError(f"packet index {packet_index} is out of range")
        if self.inflight_packet_count >= self.max_in_flight:
            raise TransportContractError("packet context table is full")
        tag = packet_tag(packet_index)
        prior = self._inflight_by_tag.get(tag)
        if prior is not None:
            raise TransportContractError(
                f"tag {tag} cannot be reused before packet {prior} completes"
            )
        self._inflight_by_tag[tag] = packet_index
        self.next_packet_to_expose += 1
        return tag

    def complete(self, packet_index: int) -> None:
        packet_index = int(packet_index)
        if packet_index != self.next_packet_to_complete:
            raise TransportContractError(
                f"packet completion must be ordered: expected {self.next_packet_to_complete}, got {packet_index}"
            )
        if packet_index >= self.packet_count:
            raise TransportContractError(f"packet index {packet_index} is out of range")
        tag = packet_tag(packet_index)
        if self._inflight_by_tag.get(tag) != packet_index:
            raise TransportContractError(f"packet {packet_index} was not exposed or tag ownership changed")
        del self._inflight_by_tag[tag]
        self.next_packet_to_complete += 1


class ContextCompletionTracker:
    """Model admission, ordered packet completion, and consumer-owned release."""

    def __init__(
        self,
        contexts: Sequence[SharedStreamContext] | None = None,
        *,
        max_inflight_packet_contexts: int = MAX_IN_FLIGHT_PACKET_CONTEXTS,
    ) -> None:
        selected = tuple(build_contexts() if contexts is None else contexts)
        self._contexts = {context.context_id: context for context in selected}
        if len(self._contexts) != len(selected):
            raise TransportContractError("context IDs must be unique")
        self._admitted: set[int] = set()
        self._completed_packets: dict[int, int] = {context_id: 0 for context_id in self._contexts}
        self._completion_valid: set[int] = set()
        self._completion_accepted: set[int] = set()
        self._source_owners: dict[int, int] = {}
        self._destination_owners: dict[int, int] = {}
        self._packet_trackers = {
            context_id: PacketTagLifetimeTracker(
                context.packet_count,
                max_in_flight=max_inflight_packet_contexts,
            )
            for context_id, context in self._contexts.items()
        }

    def admit(self, context_id: int) -> None:
        context = self._context(context_id)
        if context_id in self._admitted:
            raise TransportContractError(f"context {context_id} is already admitted")
        if context.source_endpoint in self._source_owners:
            raise TransportContractError(f"source endpoint {context.source_endpoint} is still owned")
        if context.destination_endpoint in self._destination_owners:
            raise TransportContractError(f"destination endpoint {context.destination_endpoint} is still owned")
        self._admitted.add(context_id)
        self._source_owners[context.source_endpoint] = context_id
        self._destination_owners[context.destination_endpoint] = context_id

    def expose_packet(self, context_id: int, packet_index: int) -> int:
        self._context(context_id)
        if context_id not in self._admitted:
            raise TransportContractError(f"context {context_id} is not admitted")
        return self._packet_trackers[context_id].expose(packet_index)

    def complete_packet(self, context_id: int, packet_index: int) -> None:
        context = self._context(context_id)
        if context_id not in self._admitted:
            raise TransportContractError(f"context {context_id} is not admitted")
        tracker = self._packet_trackers[context_id]
        expected = tracker.next_packet_to_complete
        if packet_index != expected:
            raise TransportContractError(
                f"context {context_id} packet completion must be ordered: expected {expected}, got {packet_index}"
            )
        # Direct completion remains a useful shorthand for the reference
        # model; explicit users can call expose_packet first.
        if tracker.next_packet_to_expose == packet_index:
            tracker.expose(packet_index)
        tracker.complete(packet_index)
        self._completed_packets[context_id] = tracker.next_packet_to_complete
        if self._completed_packets[context_id] == context.packet_count:
            self._completion_valid.add(context_id)

    def accept_completion(self, context_id: int) -> None:
        context = self._context(context_id)
        if context_id not in self._completion_valid:
            raise TransportContractError(f"context {context_id} completion is not valid")
        if context_id in self._completion_accepted:
            raise TransportContractError(f"context {context_id} completion was already accepted")
        self._completion_accepted.add(context_id)
        self._admitted.remove(context_id)
        self._source_owners.pop(context.source_endpoint, None)
        self._destination_owners.pop(context.destination_endpoint, None)

    def status(self, context_id: int) -> ContextStatus:
        context = self._context(context_id)
        return ContextStatus(
            context_id=context_id,
            admitted=context_id in self._admitted,
            completed_packet_count=self._completed_packets[context_id],
            completion_valid=context_id in self._completion_valid,
            completion_accepted=context_id in self._completion_accepted,
            source_owned=self._source_owners.get(context.source_endpoint) == context_id,
            destination_owned=self._destination_owners.get(context.destination_endpoint) == context_id,
            inflight_packet_count=self._packet_trackers[context_id].inflight_packet_count,
            next_packet_to_expose=self._packet_trackers[context_id].next_packet_to_expose,
            next_packet_to_complete=self._packet_trackers[context_id].next_packet_to_complete,
        )

    def _context(self, context_id: int) -> SharedStreamContext:
        try:
            return self._contexts[int(context_id)]
        except KeyError as exc:
            raise TransportContractError(f"unknown context {context_id}") from exc


# Compatibility aliases for callers that use the contract's shorter terms.
contexts = build_contexts
packets_for_context = packet_descriptors
copy_and_validate_payload = copy_payload_and_validate
