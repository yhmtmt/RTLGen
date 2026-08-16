from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.noc_sram_packet_mesh import (  # noqa: E402
    PacketDescriptor,
    simulate_packet_mesh,
)


def test_rx_handshakes_before_tx_release() -> None:
    result = simulate_packet_mesh(
        [
            PacketDescriptor(
                source=0,
                destination=15,
                vc=1,
                tag=0x41,
                flit_count=2,
                packet_id="ordered",
            )
        ]
    )

    rx = result.rx_descriptor_handshakes[0]
    tx = result.tx_descriptor_handshakes[0]
    assert rx.direction == "rx"
    assert tx.direction == "tx"
    assert rx.endpoint == 15
    assert tx.endpoint == 0
    assert tx.cycle > rx.cycle
    assert not result.protocol_errors
    assert result.mesh_traces == ()
    assert all(router.traces == () for router in result.router_summaries)


def test_eight_rx_contexts_throttle_a_ninth_packet() -> None:
    descriptors = [
        PacketDescriptor(
            source=index,
            destination=15,
            vc=index % 4,
            tag=index,
            flit_count=1,
            packet_id=f"packet-{index}",
        )
        for index in range(9)
    ]
    result = simulate_packet_mesh(descriptors)

    rx_by_packet = {event.packet_index: event.cycle for event in result.rx_descriptor_handshakes}
    completion_by_packet = {event.packet_index: event.cycle for event in result.completions}
    assert len(rx_by_packet) == 9
    assert max(rx_by_packet[index] for index in range(8)) < rx_by_packet[8]
    assert rx_by_packet[8] > min(completion_by_packet[index] for index in range(8))
    assert result.max_rx_context_occupancy <= 8
    assert not result.protocol_errors


def test_concrete_tags_are_preserved_across_wrap() -> None:
    descriptors = [
        PacketDescriptor(
            source=0,
            destination=15,
            vc=0,
            tag=tag,
            flit_count=1,
            schedule_order=index,
            packet_id=f"tag-{tag:02x}",
        )
        for index, tag in enumerate((0xFE, 0xFF, 0x00, 0x01))
    ]
    result = simulate_packet_mesh(descriptors)

    observed = [delivery.flit.tag for delivery in result.deliveries]
    assert observed == [0xFE, 0xFF, 0x00, 0x01]
    assert [event.descriptor.tag for event in result.tx_descriptor_handshakes] == observed
    assert not result.protocol_errors


def test_two_packet_composed_case_matches_endpoint_metadata() -> None:
    result = simulate_packet_mesh(
        [
            PacketDescriptor(
                source=0,
                destination=15,
                vc=1,
                tag=0x08,
                flit_count=8,
                tx_base_addr=0x0100,
                rx_base_addr=0x1800,
                data_seed=0,
                packet_id="source0-to-destination15",
            ),
            PacketDescriptor(
                source=3,
                destination=12,
                vc=2,
                tag=0x32,
                flit_count=3,
                tx_base_addr=0x0300,
                rx_base_addr=0x1200,
                data_seed=3,
                packet_id="source3-to-destination12",
            ),
        ],
        destination_sram_ready_schedule=lambda cycle, endpoint: not (
            (endpoint == 15 and cycle % 5 == 2)
            or (endpoint == 12 and cycle % 7 == 3)
        ),
    )

    assert len(result.source_memory_requests) == 11
    assert len(result.source_memory_responses) == 11
    assert len(result.destination_memory_writes) == 11
    assert len(result.completions) == 2
    assert not result.protocol_errors

    by_packet = {}
    for delivery in result.deliveries:
        by_packet.setdefault(delivery.packet_index, []).append(delivery.flit)
    assert [flit.fragment for flit in by_packet[0]] == list(range(8))
    assert [flit.fragment for flit in by_packet[1]] == list(range(3))
    assert all(flit.tag == 0x08 for flit in by_packet[0])
    assert all(flit.tag == 0x32 for flit in by_packet[1])
    assert [write.address for write in result.destination_memory_writes if write.packet_index == 0] == [
        0x1800 + 32 * fragment for fragment in range(8)
    ]
    assert [write.address for write in result.destination_memory_writes if write.packet_index == 1] == [
        0x1200 + 32 * fragment for fragment in range(3)
    ]
