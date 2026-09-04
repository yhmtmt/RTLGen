from __future__ import annotations

from dataclasses import replace

import pytest

from npu.sim.perf.attention_kv_capacity_gather_scheduler import layer_descriptors
from npu.sim.perf.attention_kv_gather_packetizer import (
    FLITS_PER_PACKET,
    full_schedule_packet_summary,
    packet_commands,
    packet_count,
)


def test_representative_span_packet_boundaries() -> None:
    rows = layer_descriptors(0)
    hbm_tail = next(
        row
        for row in rows
        if row.operation == "consume" and row.tile == 2 and row.plane == 0 and row.source == "hbm"
    )
    for descriptor, expected_count in ((rows[0], 4096), (rows[2], 64), (hbm_tail, 448)):
        packets = packet_commands(descriptor)
        assert len(packets) == expected_count
        assert packets[0].packet_index == 0
        assert packets[-1].packet_index == expected_count - 1
        assert packets[-1].descriptor_last
        assert packets[-1].canonical_byte_address + 256 == (
            descriptor.canonical_base_address + descriptor.payload_bytes
        )
        assert packets[-1].source_byte_address + 256 == (
            descriptor.source_byte_address + descriptor.payload_bytes
        )
        assert packets[-1].destination_byte_address + 256 == (
            descriptor.destination_byte_address + descriptor.payload_bytes
        )
        assert {packet.flit_count for packet in packets} == {FLITS_PER_PACKET}
        assert all(packet.tag == (packet.packet_index & 0xFF) for packet in packets)


def test_schedule_last_only_marks_last_packet() -> None:
    descriptor = replace(layer_descriptors(0)[2], last=True)
    packets = packet_commands(descriptor)
    assert sum(packet.schedule_last for packet in packets) == 1
    assert packets[-1].schedule_last


def test_full_schedule_packet_accounting() -> None:
    assert full_schedule_packet_summary() == {
        "descriptor_count": 33344,
        "packet_count": 17_055_744,
        "hbm_source_packet_count": 16_777_216,
        "canonical_consume_packet_count": 16_777_216,
        "resident_refill_packet_count": 278_528,
    }


def test_packetizer_rejects_unaligned_or_oversized_spans() -> None:
    descriptor = layer_descriptors(0)[2]
    with pytest.raises(ValueError, match="positive multiple"):
        packet_count(replace(descriptor, payload_bytes=257))
    with pytest.raises(ValueError, match="source address"):
        packet_count(replace(descriptor, source_byte_address=1))
    with pytest.raises(ValueError, match="exceed"):
        packet_count(replace(descriptor, payload_bytes=2 * 1024 * 1024))
    with pytest.raises(ValueError, match="canonical span"):
        packet_count(
            replace(
                descriptor,
                canonical_base_address=(1 << 20) - 256,
                payload_bytes=512,
            )
        )
    with pytest.raises(ValueError, match="source span"):
        packet_count(
            replace(
                descriptor,
                source_byte_address=(1 << 34) - 256,
                payload_bytes=512,
            )
        )
    with pytest.raises(ValueError, match="destination span"):
        packet_count(
            replace(
                descriptor,
                destination_byte_address=(1 << 34) - 256,
                payload_bytes=512,
            )
        )
    for field in (
        "canonical_base_address",
        "source_byte_address",
        "destination_byte_address",
    ):
        with pytest.raises(ValueError, match="non-negative"):
            packet_count(replace(descriptor, **{field: -256}))
