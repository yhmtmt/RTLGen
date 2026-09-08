"""Exact packet expansion and full-K block pairing for Llama7B gather spans."""

from __future__ import annotations

from dataclasses import dataclass

from npu.sim.perf.attention_kv_capacity_gather_scheduler import (
    CONSUME,
    HBM,
    PLANE_BYTES,
    REFILL,
    KvGatherDescriptor,
    llama7b_descriptors,
)


PACKET_BYTES = 256
FLIT_BYTES = 32
FLITS_PER_PACKET = PACKET_BYTES // FLIT_BYTES


def _packet_offset(descriptor: KvGatherDescriptor, index: int) -> int:
    if (
        descriptor.operation == CONSUME
        and descriptor.plane < 4
        and descriptor.payload_bytes == PLANE_BYTES
    ):
        block = index >> 3
        stream = (index >> 2) & 1
        packet_in_block = index & 3
        return block * 1024 + stream * 64 * 1024 + packet_in_block * PACKET_BYTES
    return index * PACKET_BYTES


@dataclass(frozen=True)
class KvGatherPacketCommand:
    layer: int
    tile: int
    segment: int
    operation: str
    source: str
    source_endpoint: int
    destination_cluster: int
    plane: int
    canonical_byte_address: int
    source_byte_address: int
    destination_is_resident_cache: bool
    destination_byte_address: int
    packet_index: int
    tag: int
    flit_count: int
    descriptor_last: bool
    schedule_last: bool


def packet_count(descriptor: KvGatherDescriptor) -> int:
    if descriptor.payload_bytes <= 0 or descriptor.payload_bytes % PACKET_BYTES:
        raise ValueError("gather payload must be a positive multiple of 256 bytes")
    for name, address in (
        ("canonical", descriptor.canonical_base_address),
        ("source", descriptor.source_byte_address),
        ("destination", descriptor.destination_byte_address),
    ):
        if address < 0:
            raise ValueError(f"{name} address must be non-negative")
        if address % PACKET_BYTES:
            raise ValueError(f"{name} address must be 256-byte aligned")
    for name, address, limit in (
        ("canonical", descriptor.canonical_base_address, 1 << 20),
        ("source", descriptor.source_byte_address, 1 << 34),
        ("destination", descriptor.destination_byte_address, 1 << 34),
    ):
        if address + descriptor.payload_bytes > limit:
            raise ValueError(f"{name} span exceeds its address width")
    count = descriptor.payload_bytes // PACKET_BYTES
    if count > 4096:
        raise ValueError("one gather span cannot exceed 4096 packets")
    return count


def packet_commands(
    descriptor: KvGatherDescriptor,
) -> tuple[KvGatherPacketCommand, ...]:
    count = packet_count(descriptor)
    rows = []
    for index in range(count):
        offset = _packet_offset(descriptor, index)
        descriptor_last = index + 1 == count
        rows.append(
            KvGatherPacketCommand(
                layer=descriptor.layer,
                tile=descriptor.tile,
                segment=descriptor.segment,
                operation=descriptor.operation,
                source=descriptor.source,
                source_endpoint=descriptor.source_endpoint,
                destination_cluster=descriptor.destination_cluster,
                plane=descriptor.plane,
                canonical_byte_address=descriptor.canonical_base_address + offset,
                source_byte_address=descriptor.source_byte_address + offset,
                destination_is_resident_cache=descriptor.operation == REFILL,
                destination_byte_address=descriptor.destination_byte_address + offset,
                packet_index=index,
                tag=index & 0xFF,
                flit_count=FLITS_PER_PACKET,
                descriptor_last=descriptor_last,
                schedule_last=descriptor.last and descriptor_last,
            )
        )
    return tuple(rows)


def full_schedule_packet_summary() -> dict[str, int]:
    descriptors = llama7b_descriptors()
    return {
        "descriptor_count": len(descriptors),
        "packet_count": sum(packet_count(row) for row in descriptors),
        "hbm_source_packet_count": sum(
            packet_count(row) for row in descriptors if row.source == HBM
        ),
        "canonical_consume_packet_count": sum(
            packet_count(row) for row in descriptors if row.operation != REFILL
        ),
        "resident_refill_packet_count": sum(
            packet_count(row) for row in descriptors if row.operation == REFILL
        ),
    }


__all__ = [
    "FLITS_PER_PACKET",
    "KvGatherPacketCommand",
    "PACKET_BYTES",
    "full_schedule_packet_summary",
    "packet_commands",
    "packet_count",
]
